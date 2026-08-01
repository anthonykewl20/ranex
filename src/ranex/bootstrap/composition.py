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

from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.api import (
    Claim,
    Evaluation,
    Evidence,
    Gate,
    evaluate,
)
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate


@dataclass(frozen=True, slots=True)
class GateEvaluator:
    """One wired evaluation path: catalog -> gate -> verdict -> journal."""

    gate_catalog_path: Path
    journal_path: Path | None

    def evaluate(
        self,
        gate_id: str,
        evidence: tuple[Evidence, ...],
        *,
        subject_digest: str,
        approver_id: str,
    ) -> Evaluation:
        content = self.gate_catalog_path.read_bytes()
        catalog_digest = "sha256:" + hashlib.sha256(content).hexdigest()
        definition = load_gate(self.gate_catalog_path, gate_id)
        gate = Gate(
            gate_id=definition.gate_id,
            rule_id=definition.rule_id,
            required_claims=tuple(
                Claim(
                    claim_id=claim.claim_id,
                    command_digest=claim.command_digest,
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
    gate_catalog_path: Path,
    journal_path: Path | None = None,
) -> GateEvaluator:
    """Select and wire the concrete implementations. The only place that may."""

    return GateEvaluator(
        gate_catalog_path=Path(gate_catalog_path),
        journal_path=Path(journal_path) if journal_path is not None else None,
    )
