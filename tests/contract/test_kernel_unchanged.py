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
"""

from __future__ import annotations

import hashlib
from pathlib import Path

KERNEL = (
    Path(__file__).resolve().parents[2]
    / "src/ranex/governed_execution/domain/verdict.py"
)

# Digest as of the commit that opened SLICE-002, before any signing existed.
KERNEL_DIGEST = "0663ff6817b760cc205fe7fbc800a9e21380058ec9d850014f4374d6d88f659d"


def test_verdict_module_is_byte_for_byte_unchanged() -> None:
    actual = hashlib.sha256(KERNEL.read_bytes()).hexdigest()
    assert actual == KERNEL_DIGEST, (
        "src/ranex/governed_execution/domain/verdict.py changed during "
        "SLICE-002. Signing is an admission concern and must not reach the "
        "kernel. If this change is deliberate, update KERNEL_DIGEST in the same "
        "commit and say why in the message."
    )
