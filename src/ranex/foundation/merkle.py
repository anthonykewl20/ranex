"""RFC 6962 / RFC 9162 Merkle inclusion proofs.

Owned verifier for transparency-log inclusion proofs. The leaf and internal
node prefixes follow Certificate Transparency (RFC 6962 §2.1): leaves are
``SHA-256(0x00 || data)``, interior nodes ``SHA-256(0x01 || left || right)``.
Side selection while walking the audit path follows RFC 9162 §2.1.3.2.

Nothing here reaches a network or a model. The root this function checks is
authenticated elsewhere (the log's signed checkpoint).
"""

from __future__ import annotations

import hashlib


def leaf_hash(data: bytes) -> bytes:
    """RFC 6962 leaf hash of one log entry's canonical body."""

    return hashlib.sha256(b"\x00" + data).digest()


def verify_inclusion(
    *,
    index: int,
    size: int,
    leaf: bytes,
    hashes: list[bytes],
    root: bytes,
) -> bool:
    """True iff ``leaf`` at ``index`` in a tree of ``size`` recomputes ``root``.

    ``hashes`` is the audit path bottom-up (the order Rekor returns). Returns
    False for every malformed shape rather than raising — a hand-mangled
    witness must fail verification, not crash the operator's CLI.
    """

    if (
        index < 0
        or size <= 0
        or index >= size
        or len(leaf) != 32
        or len(root) != 32
        or any(len(item) != 32 for item in hashes)
    ):
        return False
    fn = index
    sn = size - 1
    r = leaf
    for sibling in hashes:
        if fn % 2 == 1 or fn == sn:
            r = hashlib.sha256(b"\x01" + sibling + r).digest()
            while fn % 2 == 0 and fn != 0:
                fn >>= 1
                sn >>= 1
        else:
            r = hashlib.sha256(b"\x01" + r + sibling).digest()
        fn >>= 1
        sn >>= 1
    return r == root and fn == 0
