from __future__ import annotations

import re

from ranex.assurance.api.contracts import EvidenceRecord, GateEvaluation
from ranex.governed_execution.application.gate_controller import GateController
from ranex.governed_execution.application.ports.application_control_policy import (
    ApplicationControlPolicy,
)
from ranex.governed_execution.domain.application_control import (
    ApplicationControlRequest,
)
from ranex.policy.api.contracts import GateCatalog

_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class DeterministicPolicyAdapter(ApplicationControlPolicy):
    """Evaluate one immutable in-memory R&D catalog without external effects."""

    def __init__(
        self,
        *,
        catalog: GateCatalog,
        catalog_digest: str,
    ) -> None:
        if _SHA256_PATTERN.fullmatch(catalog_digest) is None:
            raise ValueError("catalog_digest must be canonical SHA-256")
        self._catalog = catalog
        self._catalog_digest = catalog_digest
        self._controller = GateController()

    def evaluate(
        self,
        *,
        request: ApplicationControlRequest,
        evidence: tuple[EvidenceRecord, ...],
    ) -> GateEvaluation:
        self._catalog.require_project(request.project_id)
        gate = self._catalog.gate_for(request.action)
        return self._controller.evaluate(
            gate=gate,
            request=request,
            evidence=evidence,
            catalog_id=self._catalog.catalog_id,
            catalog_digest=self._catalog_digest,
        )
