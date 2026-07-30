from __future__ import annotations

from typing import Protocol

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import ExecutionEvent
from ranex.governed_execution.domain.execution import Execution


class ExecutionRepository(Protocol):
    def load(self, execution_id: Identity) -> Execution | None:
        """Load the current canonical execution snapshot."""
        ...

    def append(self, event: ExecutionEvent) -> Execution:
        """Reduce and atomically persist one execution transition."""
        ...
