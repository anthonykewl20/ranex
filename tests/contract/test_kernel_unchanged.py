"""SLICE-002 — the kernel does not move.

`evaluate()` is a pure function of (gate, evidence, subject, approver). SLICE-002
adds signing *around* it: verification happens at admission, and a record that
does not verify is never passed in. Nothing about that requires the kernel to
change, and the slice says so in its notes — if it seems to, the slice is wrong,
not the kernel.

"Do not change verdict.py" is a rule an agent can read, which makes it a
suggestion. This is the constraint. It is deliberately a whole-file digest
rather than a signature check: adding a keyring parameter, threading a rejection
through, or "just" widening a type would each pass a looser test and each would
be the thing this slice must not do.

If the digest fails, that is not automatically a bug — but changing it is a
decision to be made deliberately and argued in a commit message, never a side
effect of implementing signing.

**SLICE-003 moves the kernel on purpose.** `Claim` gains `command_digest`,
`Evidence` gains `command_digest`, and `satisfies()` compares them — the whole
point of that slice is that satisfaction must ask what ran, and there is nowhere
else for that comparison to live. So this test is expected to be RED until the
implementer sets `KERNEL_DIGEST` to the new bytes **in the same commit** and says
why in the message. That is the one line of this file the implementation is
meant to touch; nothing else here may be relaxed to accommodate it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

KERNEL = (
    Path(__file__).resolve().parents[2]
    / "src/ranex/governed_execution/domain/verdict.py"
)

# Digest as of SLICE-020, which moved the kernel deliberately under ADR-020:
# Evaluation now carries and serializes the structured five-kind diagnosis and
# self-approval marker from the same partition that renders the byte-identical
# reason, so journal records preserve both rather than only the prose.
KERNEL_DIGEST = "2969aa74adc8ac40393fb4f782e05be8f29f34d2ab0f594051906f4e6a5b5ed6"


def test_verdict_module_is_byte_for_byte_unchanged() -> None:
    actual = hashlib.sha256(KERNEL.read_bytes()).hexdigest()
    assert actual == KERNEL_DIGEST, (
        "src/ranex/governed_execution/domain/verdict.py changed during "
        "SLICE-002. Signing is an admission concern and must not reach the "
        "kernel. If this change is deliberate, update KERNEL_DIGEST in the same "
        "commit and say why in the message."
    )
