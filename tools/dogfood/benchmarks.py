"""Public benchmark metrics for ranex.

Two honest classes of data, never mixed:

  PROOF BOARD  — deterministic (no clocks): scenario counts per capability
                 area, facts digests, pass/fail. These are claims of FACT.
  TIMINGS      — wall-clock measurements with full statistics (median,
                 min, max, repeats) and the environment they were taken in.
                 These are claims about ONE machine, labeled as such, and
                 are never compared as if they were deterministic.

Timings cover the capacities a follower of a governance kernel actually
cares about: what does it COST to verify trust (admission, signatures,
journal) and how does that cost SCALE (verify is linear, append is flat).
"""

from __future__ import annotations

import os
import platform
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ranex.foundation.canonical import canonical_json
from ranex.foundation.signing import generate_keypair, sign_evidence, verify_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    evaluate,
)
from ranex.provisioning.lockfile import parse_lock, select_wheels
from ranex.provisioning.target import probe_target

REPO_ROOT = Path(__file__).resolve().parents[2]
DIGEST_A = "sha256:" + "a" * 64
DIGEST_C = "sha256:" + "c" * 64


@dataclass
class Metric:
    id: str
    area: str
    label: str
    unit: str
    samples: list[float] = field(default_factory=list)

    @property
    def median(self) -> float:
        return statistics.median(self.samples)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "area": self.area, "label": self.label,
            "unit": self.unit, "repeats": len(self.samples),
            "median": round(self.median, 3),
            "min": round(min(self.samples), 3),
            "max": round(max(self.samples), 3),
            "samples": [round(s, 3) for s in self.samples],
        }


def _timed(repeats: int, fn: Callable[[], Any]) -> list[float]:
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - started) * 1000)
    return samples


def _evaluation_claims(n_claims: int) -> tuple[Gate, tuple[Evidence, ...]]:
    claims = tuple(
        Claim(claim_id=f"claim-{i:03d}", command_digest=DIGEST_C)
        for i in range(n_claims)
    )
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=claims, blocking=True)
    evidence = tuple(
        Evidence(claim_id=f"claim-{i:03d}", subject_digest=DIGEST_A,
                 producer_id=f"producer-{i:03d}", command="pytest -q",
                 command_digest=DIGEST_C, executable_path="/usr/bin/pytest",
                 exit_code=0)
        for i in range(n_claims)
    )
    return gate, evidence


def _make_journal(path: Path, rows: int) -> Journal:
    journal = Journal(path)
    gate, evidence = _evaluation_claims(1)
    subject = DIGEST_A
    for item in evidence:
        journal.append(evaluate(gate, (item,), subject_digest=subject,
                                approver_id="bench-approver"))
    for _ in range(rows - 1):
        journal.append(evaluate(gate, (), subject_digest=subject,
                                approver_id="bench-approver"))
    return journal


def environment() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "system": f"{platform.system()} {platform.release()}",
        "cpu_count": str(os.cpu_count() or 1),
        "note": "single machine, single run environment; timings are not "
                "deterministic and must not be compared as if they were",
    }


def collect_timings(scratch: Path, repeats: int = 3) -> list[Metric]:
    """One metric per capacity; each sample is a full operation of the named
    workload (documented per metric), so medians are comparable within this
    environment only."""
    metrics: list[Metric] = []

    # -- journal: append throughput and verify scaling ---------------------
    for rows in (100, 500, 2000):
        path = scratch / f"bench-journal-{rows}.sqlite3"
        samples = []
        for _ in range(repeats):
            path.unlink(missing_ok=True)
            started = time.perf_counter()
            _make_journal(path, rows)
            samples.append((time.perf_counter() - started) * 1000)
        metric = Metric(f"journal-append-{rows}", "journal",
                        f"append {rows} chained evaluation rows",
                        "ms total", samples)
        metrics.append(metric)

    for rows in (100, 500, 2000):
        path = scratch / f"bench-journal-{rows}.sqlite3"
        if not path.exists():
            _make_journal(path, rows)
        journal = Journal(path)
        samples = _timed(repeats, journal.verify)
        metrics.append(Metric(f"journal-verify-{rows}", "journal",
                              f"verify chain of {rows} rows (recompute all links)",
                              "ms", samples))

    # -- admission: full pipeline (parse + signature verify) ---------------
    from ranex.foundation.signing import SIGNED_FIELDS

    private, public = generate_keypair()
    digest = DIGEST_C

    def record(i: int) -> dict[str, Any]:
        content = {field_: None for field_ in SIGNED_FIELDS}
        content.update({
            "claim_id": f"claim-{i:04d}", "subject_digest": DIGEST_A,
            "producer_id": "bench-producer", "command": "pytest -q",
            "command_digest": digest, "executable_path": "/usr/bin/pytest",
            "exit_code": 0,
        })
        return {**content, "signature": sign_evidence(content, private)}

    from ranex.governed_execution.domain import admission

    records = [record(i) for i in range(200)]
    keyring = {"bench-producer": public}
    samples = _timed(repeats, lambda: admission.admit(records, keyring=keyring))
    metrics.append(Metric("admission-200", "admission",
                          "admit 200 signed records (Ed25519 verify each)",
                          "ms", samples))

    # -- signatures: sign and verify throughput -----------------------------
    content = record(0)
    content.pop("signature")

    def sign_200() -> None:
        for _ in range(200):
            sign_evidence(content, private)

    samples = _timed(repeats, sign_200)
    metrics.append(Metric("sign-200", "signing",
                          "Ed25519-sign 200 evidence payloads", "ms", samples))
    signature = sign_evidence(content, private)

    def verify_200() -> None:
        for _ in range(200):
            verify_evidence(content, signature, public)

    samples = _timed(repeats, verify_200)
    metrics.append(Metric("verify-200", "signing",
                          "Ed25519-verify 200 evidence payloads", "ms", samples))

    # -- verdict kernel: pure evaluate ---------------------------------------
    gate, evidence = _evaluation_claims(20)
    samples = _timed(repeats, lambda: [
        evaluate(gate, evidence, subject_digest=DIGEST_A,
                 approver_id="bench-approver") for _ in range(100)
    ])
    metrics.append(Metric("evaluate-20claims-100calls", "verdict",
                          "100 pure evaluations of a 20-claim gate",
                          "ms", samples))

    # -- provisioning: wheel selection over the real lock -------------------
    lock = parse_lock((REPO_ROOT / "uv.lock").read_bytes())
    import yaml

    pins = yaml.safe_load((REPO_ROOT / "governance" / "deps.yaml").read_text())
    target = probe_target(Path(pins["python"]["path"]))
    samples = _timed(repeats, lambda: select_wheels(lock, "ranex", target))
    metrics.append(Metric("select-wheels-real-lock", "provisioning",
                          "select wheels over the real committed uv.lock",
                          "ms", samples))

    # -- canonical JSON -------------------------------------------------------
    doc = {"suite": [f"test-{i:04d}" for i in range(100)],
           "counts": {"passed": 100, "failed": 0}, "digests": {"a": DIGEST_A}}
    samples = _timed(repeats, lambda: [canonical_json(doc) for _ in range(1000)])
    metrics.append(Metric("canonical-json-1000", "canonical",
                          "canonicalise 1000 medium documents", "ms", samples))

    # -- CLI cold start (user-facing latency) --------------------------------
    def cli_help() -> None:
        subprocess.run([sys.executable, "-m", "ranex.cli.main", "--help"],
                       capture_output=True, check=True)

    samples = _timed(repeats, cli_help)
    metrics.append(Metric("cli-cold-start", "cli",
                          "ranex --help cold start (interpreter + imports)",
                          "ms", samples))

    return metrics


def scaling_series(metrics: list[Metric]) -> dict[str, list[dict[str, Any]]]:
    """Group the sized metrics into plottable series (x = rows, y = ms)."""
    series: dict[str, list[dict[str, Any]]] = {"journal-verify": [], "journal-append": []}
    for metric in metrics:
        for prefix, key in (("journal-verify-", "journal-verify"),
                            ("journal-append-", "journal-append")):
            if metric.id.startswith(prefix):
                rows = int(metric.id.rsplit("-", 1)[1])
                series[key].append({"rows": rows, "median_ms": metric.median})
    for values in series.values():
        values.sort(key=lambda point: point["rows"])
    return series
