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
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ranex.foundation.suite_results import load_manifest_bytes, manifest_digest
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

    def evaluate(
        self,
        gate_id: str,
        evidence: tuple[Evidence, ...],
        *,
        subject_digest: str,
        approver_id: str,
    ) -> Evaluation:
        catalog_digest = catalog_digest_for(self.gate_catalog)
        definition = load_gate_text(self.gate_catalog.decode("utf-8"), gate_id)
        requires_results = any(
            claim.results_artifact is not None for claim in definition.required_claims
        )
        manifest = None
        if requires_results:
            if self.suite_manifest is None:
                raise ValueError("suite-results claim requires a committed suite manifest")
            manifest = load_manifest_bytes(self.suite_manifest)
        gate = Gate(
            gate_id=definition.gate_id,
            rule_id=definition.rule_id,
            required_claims=tuple(
                Claim(
                    claim_id=claim.claim_id,
                    command_digest=claim.command_digest,
                    results_required=claim.results_artifact is not None,
                    manifest_digest=(
                        manifest_digest(manifest)
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
                    expected_ids=(
                        tuple(cast(list[str], manifest["suite"]))
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
                    expected_skips=(
                        dict(cast(dict[str, str], manifest["expected_skips"]))
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
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
        if self.journal_path is not None:
            Journal(self.journal_path).append(result)
        return result


def build_gate_evaluator(
    gate_catalog: bytes,
    journal_path: Path | None = None,
    suite_manifest: bytes | None = None,
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
    )
