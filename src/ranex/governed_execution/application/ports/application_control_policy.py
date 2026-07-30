from __future__ import annotations

from typing import Protocol

from ranex.assurance.api.contracts import EvidenceRecord, GateEvaluation
from ranex.governed_execution.domain.application_control import (
    ApplicationControlRequest,
)


class ApplicationControlPolicy(Protocol):
    def evaluate(
        self,
        *,
        request: ApplicationControlRequest,
        evidence: tuple[EvidenceRecord, ...],
    ) -> GateEvaluation:
        """Return a deterministic, exact-subject gate evaluation."""
        ...
