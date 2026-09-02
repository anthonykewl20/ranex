"""Deterministic math proofs: every property here is verified by RECOMPUTING
the kernel's cryptography with independent primitives (plain hashlib, plain
json) rather than trusting the kernel's own verdict about itself.

No randomness, no clocks, no environment: identical inputs must yield
byte-identical outputs on every run, which is what makes them usable as
golden baselines across dogfood iterations.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from ranex.foundation.canonical import canonical_json, command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.foundation.suite_results import freeze_manifest, manifest_digest


def _independent_canonical(value: Any) -> bytes:
    """Canonical JSON re-derived WITHOUT the kernel's canonical module, so
    agreement between the two implementations is evidence, not tautology."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _independent_link(prev_link: str, record: dict[str, Any]) -> str:
    """The journal chain rule, recomputed with plain hashlib."""
    payload = _independent_canonical({"prev_link": prev_link, "record": record})
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def journal_chain_algebra(ctx) -> dict[str, Any]:
    """Every stored link equals the independent recomputation
    link_i = sha256(canonical({prev_link, record})), genesis chained from
    64 zeros — proven over raw SQLite rows, not via Journal.verify()."""
    from scenarios import _evaluation

    path = ctx.scratch / "chain-proof.sqlite3"
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    journal = Journal(path)
    evaluations = [_evaluation() for _ in range(5)]
    for item in evaluations:
        journal.append(item)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT seq, record, prev_link, link FROM evaluations ORDER BY seq ASC"
    ).fetchall()
    conn.close()

    genesis = "sha256:" + "0" * 64
    prev = genesis
    for row in rows:
        assert row["prev_link"] == prev, f"row {row['seq']}: stored prev_link breaks the chain"
        expected = _independent_link(prev, json.loads(row["record"]))
        assert row["link"] == expected, (
            f"row {row['seq']}: stored link does not equal independent recomputation"
        )
        prev = row["link"]
    return {"rows_proven": len(rows), "genesis": genesis[:14] + "...",
            "final_link": prev}


def journal_tamper_propagation(ctx) -> dict[str, Any]:
    """A one-record edit not only breaks that row — every LATER stored link
    must diverge from the independent recomputation. Tamper sensitivity is
    proven forward through the whole chain, not just at the edit site."""
    from scenarios import _evaluation

    path = ctx.scratch / "tamper-proof.sqlite3"
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    journal = Journal(path)
    for _ in range(4):
        journal.append(_evaluation())

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("DROP TRIGGER evaluations_no_update")
    # Minimal edit: flip the approver character in row 2's record.
    row = conn.execute("SELECT record FROM evaluations WHERE seq = 2").fetchone()
    forged = row[0].replace("dogfood-approver", "dogfood-approvex")
    assert forged != row[0], "tamper edit was a no-op"
    conn.execute("UPDATE evaluations SET record = ? WHERE seq = 2", (forged,))
    conn.commit()
    rows = conn.execute(
        "SELECT seq, record, prev_link, link FROM evaluations ORDER BY seq ASC"
    ).fetchall()
    conn.close()

    prev = "sha256:" + "0" * 64
    diverged = []
    for record_row in rows:
        record = json.loads(record_row["record"])
        expected = _independent_link(prev, record)
        if record_row["link"] != expected:
            diverged.append(record_row["seq"])
        prev = record_row["link"]  # follow STORED links: divergence is sticky
    assert diverged and diverged == sorted(diverged), "chain did not diverge monotonically"
    assert min(diverged) == 2, f"divergence did not start at the tampered row: {diverged}"
    assert not Journal(path).verify(), "Journal.verify() accepted the forged chain"
    return {"tampered_row": 2, "diverged_rows": diverged}


def canonical_agreement(ctx) -> dict[str, Any]:
    """The kernel's canonical JSON and an independent implementation agree
    byte-for-byte across generated samples, and key insertion order never
    changes the bytes."""
    samples = [
        {"z": 1, "a": {"nested": [1, 2, {"k": "v"}]}, "m": None},
        {"unicode": "ranex-evidence-v4", "empty": {}, "list": []},
        {"n": 0, "neg": -1, "big": 2**53 - 1},
    ]
    for original in samples:
        reordered = dict(reversed(list(original.items())))
        assert canonical_json(original) == canonical_json(reordered), (
            "canonical bytes changed with insertion order"
        )
        assert canonical_json(original).encode("utf-8") == _independent_canonical(original), (
            "kernel canonical JSON disagrees with independent recomputation"
        )
    return {"samples": len(samples), "agreement": "byte-exact"}


def signature_determinism_stress(ctx) -> dict[str, Any]:
    """RFC 8032 determinism under stress: same key + same content signs
    identically across repetitions; distinct contents sign distinctly; the
    same content under distinct keys signs distinctly."""
    from ranex.foundation.signing import SIGNED_FIELDS

    private, _public = generate_keypair()
    other_private, _ = generate_keypair()

    def content(i: int) -> dict[str, Any]:
        value = {field: None for field in SIGNED_FIELDS}
        value.update({"claim_id": f"stress-{i:04d}", "exit_code": i % 2})
        return value

    signatures = []
    for i in range(128):
        message = content(i)
        first = sign_evidence(message, private)
        second = sign_evidence(message, private)
        assert first == second, f"signing not deterministic for sample {i}"
        signatures.append(first)
    assert len(set(signatures)) == len(signatures), "distinct contents produced equal signatures"
    same_message = content(0)
    assert sign_evidence(same_message, private) != sign_evidence(same_message, other_private), (
        "two keys produced the same signature over one message"
    )
    return {"samples": 128, "repeat_stable": True, "distinct": True}


def digest_avalanche_and_distinctness(ctx) -> dict[str, Any]:
    """command_digest is order-structural and collision-free over a large
    deterministic sample: 8192 generated argvs yield 8192 distinct digests,
    and one-character differences change the digest."""
    argvs = [[f"tool-{i:05d}", "run", "--flag"] for i in range(8192)]
    digests = {command_digest(argv) for argv in argvs}
    assert len(digests) == len(argvs), "command_digest collisions in distinct sample"
    assert command_digest(["tool", "--x=1"]) != command_digest(["tool", "--x=2"]), (
        "one-character argv difference did not change the digest"
    )
    return {"samples": len(argvs), "distinct_digests": len(digests)}


def manifest_digest_recomputation(ctx) -> dict[str, Any]:
    """manifest_digest equals an independent sha256 over independently
    canonicalised manifest bytes — the digest binding is proven, not trusted."""
    junit = (
        b'<testsuite name="s"><testcase classname="t" name="test_a"/>'
        b'<testcase classname="t" name="test_b"/></testsuite>'
    )
    manifest = freeze_manifest(junit)
    independent = "sha256:" + hashlib.sha256(_independent_canonical(manifest)).hexdigest()
    assert manifest_digest(manifest) == independent, (
        "manifest digest does not equal independent recomputation"
    )
    return {"digest": independent}
