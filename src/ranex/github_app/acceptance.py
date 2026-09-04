"""Closed mapping from a PR-head binding to an outward acceptance outcome.

The only path to a publishable record runs through `read_verdict` returning
`VERIFIED` under the committed verdict signer's keyring. Absence is named as
absence; every other reader state is named as a rejection with the state in
the code, so an operator reading a refused check learns which link broke
without guessing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ranex.github_app.binding import PrHeadBinding
from ranex.governed_execution.verdict_reader import ReadState, read_verdict

ACCEPTED = "OK"
ABSENT_CODE = "E-GITHUB-VERDICT-ABSENT"
REJECTED_PREFIX = "E-GITHUB-VERDICT-REJECTED:"


@dataclass(frozen=True, slots=True)
class Acceptance:
    """One binding's outward answer: publishable, or refused with a name."""

    code: str
    state: ReadState
    record: Mapping[str, Any] | None = None

    @property
    def publishable(self) -> bool:
        return self.code == ACCEPTED


def code_for_state(state: ReadState) -> str:
    """The closed outcome code for a reader state; fail-closed by shape.

    VERIFIED is the only publishable state; ABSENT is named as absence
    because the operator can fix it by running the gate; everything else is
    a rejection that names the reader state. An upstream `ReadState` this
    table never met still lands in the rejection branch — an unmapped state
    publishes nothing.
    """

    if state is ReadState.VERIFIED:
        return ACCEPTED
    if state is ReadState.ABSENT:
        return ABSENT_CODE
    return f"{REJECTED_PREFIX}{state.value}"


def verdict_path(verdicts_dir: Path, binding: PrHeadBinding) -> Path:
    """Where a verdict for this subject lives — the publisher's convention."""

    return Path(verdicts_dir) / f"{binding.subject_digest.removeprefix('sha256:')}.json"


def resolve_acceptance(
    verdicts_dir: Path,
    binding: PrHeadBinding,
    keyring: Mapping[str, str],
    *,
    gate_id: str,
    catalog_digest: str | None,
    approver_id: str,
) -> Acceptance:
    """Map the reader's closed state machine onto outward outcomes."""

    result = read_verdict(
        verdict_path(verdicts_dir, binding),
        keyring,
        subject_digest=binding.subject_digest,
        gate_id=gate_id,
        catalog_digest=catalog_digest,
        approver_id=approver_id,
    )
    return Acceptance(code_for_state(result.state), result.state, result.record)
