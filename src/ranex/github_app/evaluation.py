"""Automatic judgment of independently produced evidence, never PR execution.

The receiver owns the policy checkout and verdict key. An independent observer
delivers signed evidence. Only the installed kernel's gate command runs here;
no command, executable, environment or working directory comes from a webhook.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.github_app.binding import PrHeadBinding


@dataclass(frozen=True)
class EvidenceEvaluator:
    repository: Path
    evidence: str
    gate: str
    gate_catalog: str
    producers: str
    suite_manifest: str
    approver: str
    verdicts_dir: Path
    signing_key: Path
    state_dir: Path
    _policy: tuple[bytes, ...] = field(init=False, repr=False)
    _policy_names: tuple[str, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        from ranex.cli.confinement import resolve_within_repository
        from ranex.cli.main import committed_trust_root
        from ranex.policy.adapters.configuration.yaml.slice_gate_loader import (
            load_gate_text,
            reject_pytest_xfail_blindness,
        )

        def trusted(name: str, ref: str = "HEAD") -> bytes:
            return committed_trust_root(
                self.repository, ref, name,
                resolve_within_repository(self.repository, name), name,
            )

        # A scan claim's manifest carries its scope and its accepted findings,
        # so it decides as much as the catalog does: a head that quietly widens
        # `accepted` has changed the policy, and the receiver must refuse it
        # exactly as it refuses a rewritten catalog.
        definition = load_gate_text(trusted(self.gate_catalog).decode("utf-8"), self.gate)
        for claim in definition.required_claims:
            if claim.results_artifact is not None and claim.results_reporter == "pytest-junit":
                # ADR-056: every consumer of `results_artifact` refuses an
                # XPASS-blind claim. The receiver became one when it started
                # reading claims to decide which manifests are policy, so it
                # takes the same refusal — and takes it at start-up, before a
                # listener is accepting deliveries it could never publish.
                reject_pytest_xfail_blindness(
                    definition.gate_id, claim.claim_id, list(claim.command)
                )
        scans = sorted({
            claim.results_manifest
            for claim in definition.required_claims
            if claim.results_manifest is not None
        })
        # The suite manifest is pinned when it decides something. A gate whose
        # only results claim is a scan is judged entirely by that scan's own
        # manifest, and demanding a suite manifest such a repository has no
        # reason to carry would refuse it for holding nothing.
        suite = (
            (self.suite_manifest,)
            if any(
                claim.results_artifact is not None and claim.results_manifest is None
                for claim in definition.required_claims
            )
            else ()
        )
        names = (self.gate_catalog, self.producers, *suite, *scans)
        object.__setattr__(self, "_policy_names", names)
        object.__setattr__(self, "_policy", tuple(trusted(name) for name in names))

    def __call__(self, binding: PrHeadBinding) -> None:
        # Use the exact same confinement and committed-policy admission as the
        # public command. Import lazily to avoid a CLI/adapter import cycle.
        from ranex.cli.confinement import resolve_within_repository
        from ranex.cli.main import committed_trust_root

        for name, trusted in zip(self._policy_names, self._policy, strict=True):
            path = resolve_within_repository(self.repository, name)
            actual = committed_trust_root(self.repository, binding.head_sha, name, path, name)
            if actual != trusted:
                raise ValueError("E-GITHUB-EVALUATION-POLICY-CHANGED")
        evidence = resolve_within_repository(self.repository, self.evidence)
        if not evidence.exists():
            return
        fingerprint = canonical_sha256({"evidence": evidence.read_bytes().hex()})
        stamp = self.state_dir / "evaluated" / f"{binding.subject_digest[7:]}.json"
        receipt = canonical_json_bytes({"evidence": fingerprint, "gate": self.gate,
                                        "approver": self.approver,
                                        "policy": [canonical_sha256(x.hex()) for x in self._policy]})
        verdict = self.verdicts_dir / f"{binding.subject_digest[7:]}.json"
        if stamp.exists() and stamp.read_bytes() == receipt and verdict.exists():
            return
        # A minimal environment excludes the App key/token, Python startup
        # hooks and Git overrides. The trusted kernel is selected absolutely.
        environment = {
            "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
            "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
            "RANEX_VERDICT_SIGNING_KEY": str(self.signing_key),
            "RANEX_VERDICT_DIR": str(self.verdicts_dir.relative_to(self.repository)),
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        }
        argv = [sys.executable, "-m", "ranex.cli.main", "gate", "evaluate",
                binding.head_sha, "--external-repository", str(self.repository),
                "--evidence", self.evidence, "--gate", self.gate,
                "--gate-catalog", self.gate_catalog, "--producers", self.producers,
                "--suite-manifest", self.suite_manifest, "--approver", self.approver]
        try:
            result = subprocess.run(argv, cwd=Path(__file__).resolve().parents[3],
                                    env=environment, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=60, check=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("E-GITHUB-EVALUATION-TIMEOUT") from exc
        if result.returncode not in (0, 1) or not verdict.exists():
            raise ValueError("E-GITHUB-EVALUATION-REFUSED")
        # If an observer published during evaluation, retry rather than mark
        # the newer evidence as judged. Publication still verifies the verdict.
        if canonical_sha256({"evidence": evidence.read_bytes().hex()}) != fingerprint:
            raise ValueError("E-GITHUB-EVIDENCE-MOVED")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(stamp, receipt, root=self.state_dir)
