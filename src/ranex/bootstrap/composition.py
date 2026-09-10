"""The composition root.

`ADR-0007` `ORG-COMPOSE-001`: only this module selects and wires concrete
product implementations. Every other module depends on ports and domain types
and never on a concrete adapter.

`ORG-IMPORT-001`: importing this module performs no effect, no registration and
no configuration decision. Wiring happens when `build_gate_evaluator` is called,
not at import time.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ranex.foundation.scan_results import claim_expectations
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.api import (
    Claim,
    Evaluation,
    Evidence,
    Gate,
    evaluate,
)
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import (
    SliceClaimDefinition,
    load_gate_text,
    reject_pytest_xfail_blindness,
)


def catalog_digest_for(gate_catalog: bytes) -> str:
    return "sha256:" + hashlib.sha256(gate_catalog).hexdigest()


def claim_definition_for(
    gate_catalog: bytes, gate_id: str, claim_id: str
) -> SliceClaimDefinition | None:
    """Expose adapter-only claim carriers without extending the kernel Claim."""

    definition = load_gate_text(gate_catalog.decode("utf-8"), gate_id)
    return next(
        (claim for claim in definition.required_claims if claim.claim_id == claim_id),
        None,
    )


@dataclass(frozen=True, slots=True)
class GateEvaluator:
    """One wired evaluation path: catalog -> gate -> verdict -> journal.

    The catalog arrives as **bytes**, not as a path. Which bytes are the policy
    is a trust decision, and it belongs to the caller that can make it — the CLI
    takes them out of the commit. Holding a path here would mean re-reading the
    working tree at evaluation time, after the trust root was checked, which is
    exactly the window that made the check decorative.
    """

    gate_catalog: bytes
    journal_path: Path | None
    suite_manifest: bytes | None
    scan_manifests: Mapping[str, bytes] = field(default_factory=dict)
    """Committed scan-manifest bytes, keyed by the claim's `results_manifest`.

    Bytes and not paths, for the reason `committed_trust_root` exists: what was
    checked and what decides must be one read. A scan claim names its own
    manifest, so this is a mapping rather than the single suite manifest above.
    """

    def evaluate(
        self,
        gate_id: str,
        evidence: tuple[Evidence, ...],
        *,
        subject_digest: str,
        approver_id: str,
    ) -> Evaluation:
        """The verdict alone, for the callers that do not publish one."""

        evaluation, _head = self.evaluate_anchored(
            gate_id,
            evidence,
            subject_digest=subject_digest,
            approver_id=approver_id,
        )
        return evaluation

    def evaluate_anchored(
        self,
        gate_id: str,
        evidence: tuple[Evidence, ...],
        *,
        subject_digest: str,
        approver_id: str,
    ) -> tuple[Evaluation, str | None]:
        """Evaluate, and return the journal chain link this evaluation created.

        ADR-057. `Journal.append` already computes and returns that link; it was
        simply discarded here. The link is what a published verdict signs as its
        anchor, so rewriting the journal afterwards means forging a head that a
        retained, separately signed record already fixed.

        `None` when no journal is configured — there is genuinely nothing to
        anchor to, and the published record says so explicitly rather than
        omitting the field.
        """
        catalog_digest = catalog_digest_for(self.gate_catalog)
        definition = load_gate_text(self.gate_catalog.decode("utf-8"), gate_id)
        expectations: dict[str, tuple[str, tuple[str, ...], dict[str, str]]] = {}
        for claim in definition.required_claims:
            if claim.results_artifact is None:
                continue
            if claim.results_manifest is not None:
                raw = self.scan_manifests.get(claim.results_manifest)
                if raw is None:
                    raise ValueError(
                        f"claim {claim.claim_id!r} requires the committed bytes of "
                        f"{claim.results_manifest}"
                    )
            elif self.suite_manifest is None:
                raise ValueError("suite-results claim requires a committed suite manifest")
            else:
                raw = self.suite_manifest
            expectations[claim.claim_id] = claim_expectations(raw, claim.results_reporter)
        for claim in definition.required_claims:
            if claim.results_artifact is not None and claim.results_reporter == "pytest-junit":
                # ADR-056. A suite claim whose argv cannot report an XPASS is a
                # gate that cannot block one of its own declared sad paths, so
                # it is refused where the Gate is built rather than where the
                # catalog is parsed — see the loader's note on historical base
                # commits.
                reject_pytest_xfail_blindness(
                    definition.gate_id, claim.claim_id, list(claim.command)
                )
        gate = Gate(
            gate_id=definition.gate_id,
            rule_id=definition.rule_id,
            required_claims=tuple(
                Claim(
                    claim_id=claim.claim_id,
                    command_digest=claim.command_digest,
                    results_required=claim.results_artifact is not None,
                    manifest_digest=expectations[claim.claim_id][0]
                    if claim.claim_id in expectations
                    else None,
                    expected_ids=expectations[claim.claim_id][1]
                    if claim.claim_id in expectations
                    else None,
                    expected_skips=expectations[claim.claim_id][2]
                    if claim.claim_id in expectations
                    else None,
                )
                for claim in definition.required_claims
            ),
            blocking=definition.blocking,
        )
        result = evaluate(
            gate,
            evidence,
            subject_digest=subject_digest,
            catalog_digest=catalog_digest,
            approver_id=approver_id,
        )
        head = (
            Journal(self.journal_path).append(result)
            if self.journal_path is not None
            else None
        )
        return result, head




def build_gate_evaluator(
    gate_catalog: bytes,
    journal_path: Path | None = None,
    suite_manifest: bytes | None = None,
    scan_manifests: Mapping[str, bytes] | None = None,
) -> GateEvaluator:
    """Select and wire the concrete implementations. The only place that may.

    `gate_catalog` is the catalog's bytes. The digest recorded in the journal is
    taken over exactly these, so what the journal attests to is the policy that
    actually ran and not whatever the path held when the journal was written.
    """

    return GateEvaluator(
        gate_catalog=bytes(gate_catalog),
        journal_path=Path(journal_path) if journal_path is not None else None,
        suite_manifest=(bytes(suite_manifest) if suite_manifest is not None else None),
        scan_manifests={
            name: bytes(raw) for name, raw in (scan_manifests or {}).items()
        },
    )
