"""F-005 — a signed verdict anchors the journal head it was produced at.

`Journal.verify()` recomputes the hash chain, and its own docstring concedes
the limit: "Without an external head this detects inconsistent edits, not a
complete replacement or truncation of a self-consistent chain." An attacker who
rewrites the whole journal — recomputing every link from genesis — produces a
chain that verifies clean. Every "tamper-evident" claim about the journal was
therefore really "partial-edit-evident".

`--expected-head` closed half of that by letting an operator supply a head they
retained. It relies on the operator having kept one, out of band, by hand.

ADR-057 supplies the anchor automatically. `Journal.append` already returns the
chain link it created; the published verdict now signs that link as
`journal_head`. The anchor therefore lives outside the journal, in a record
signed by the *verdict signer* — a different key from the one that writes the
journal — so rewriting history means forging a head that a retained, separately
signed record already fixed.

What this does NOT establish, stated plainly: an operator holding both the
journal and the verdict signing key can still rewrite consistently. There is no
external witness here. That is the residual gap, and it is where a transparency
log would attach.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.verdict_signing import (
    PAYLOAD_TYPE,
    SIGNED_FIELDS,
    VERDICT_DOMAIN,
    sign_verdict,
    verify_verdict,
)
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.verdict_reader import ReadState, read_verdict_unbound

GENESIS = "sha256:" + "0" * 64


class _Evaluation:
    """The one thing `Journal.append` asks of what it is given."""

    def __init__(self, record: dict[str, object]) -> None:
        self._record = record

    def as_record(self) -> dict[str, object]:
        return self._record


def _chain(journal: Path, count: int) -> list[str]:
    return [
        Journal(journal).append(_Evaluation({"type": "evaluation", "n": index}))
        for index in range(count)
    ]


def _rewrite_consistently(journal: Path, records: list[dict[str, object]]) -> None:
    """Replace the whole history with a freshly, correctly rehashed chain.

    This is the attack: not an edited row, which the links already catch, but a
    complete replacement in which every link is genuinely correct.
    """

    connection = sqlite3.connect(journal)
    try:
        connection.execute("DELETE FROM evaluations")
        previous = GENESIS
        for record in records:
            link = "sha256:" + canonical_sha256(
                {"prev_link": previous, "record": record}
            )
            connection.execute(
                "INSERT INTO evaluations (record, prev_link, link) VALUES (?, ?, ?)",
                (json.dumps(record, sort_keys=True, separators=(",", ":")), previous, link),
            )
            previous = link
        connection.commit()
    finally:
        connection.close()


def _drop_triggers(journal: Path) -> None:
    """The journal is append-only in SQL; the attack presumes that is bypassed."""

    connection = sqlite3.connect(journal)
    try:
        for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        ).fetchall():
            connection.execute(f"DROP TRIGGER IF EXISTS {name}")
        connection.commit()
    finally:
        connection.close()


# --- the finding, restated as a test ------------------------------------------


def test_a_complete_rewrite_still_passes_plain_chain_verification(
    tmp_path: Path,
) -> None:
    """F-005's open half, pinned rather than argued.

    If this ever fails, the chain gained a property it does not claim, and the
    anchor below may no longer be the only thing standing between a rewrite and
    a clean bill of health.
    """

    journal = tmp_path / "journal.sqlite3"
    _chain(journal, 4)
    assert Journal(journal).verify() is True

    _drop_triggers(journal)
    _rewrite_consistently(
        journal, [{"type": "evaluation", "n": index} for index in range(2)]
    )

    assert Journal(journal).verify() is True, (
        "a fully rehashed replacement history verifies clean — this is the "
        "finding, not a regression"
    )


def test_the_anchor_refuses_the_rewrite_the_chain_accepts(tmp_path: Path) -> None:
    """The same rewrite, judged against the head a verdict fixed."""

    journal = tmp_path / "journal.sqlite3"
    links = _chain(journal, 4)
    head = links[-1]

    assert Journal(journal).verify(expected_head=head) is True

    _drop_triggers(journal)
    _rewrite_consistently(
        journal, [{"type": "evaluation", "n": index} for index in range(2)]
    )

    assert Journal(journal).verify() is True
    assert Journal(journal).verify(expected_head=head) is False, (
        "the retained head is what distinguishes the rewrite from the history "
        "that actually happened"
    )


def test_truncation_from_a_fresh_head_is_caught_only_by_the_anchor(
    tmp_path: Path,
) -> None:
    """Dropping the tail leaves a prefix whose links are all still correct."""

    journal = tmp_path / "journal.sqlite3"
    links = _chain(journal, 5)

    _drop_triggers(journal)
    connection = sqlite3.connect(journal)
    try:
        connection.execute(
            "DELETE FROM evaluations WHERE seq > (SELECT MIN(seq) + 1 FROM evaluations)"
        )
        connection.commit()
    finally:
        connection.close()

    assert Journal(journal).verify() is True, "a truncated prefix is self-consistent"
    assert Journal(journal).verify(expected_head=links[-1]) is False


# --- the anchor is signed, so forging it costs the verdict key -----------------


def _record(journal_head: str | None) -> dict[str, object]:
    content: dict[str, object] = {
        "verdict": "PASS",
        "gate_id": "landing",
        "subject_digest": "sha256:" + "a" * 64,
        "subject_lane": None,
        "catalog_digest": "sha256:" + "b" * 64,
        "approver_id": "reviewer",
        "failing_rule": None,
        "missing_claims": [],
        "considered": [],
        "causes": [],
        "rejections": [],
        "self_approval": False,
        "reason": "ok",
        "journal_head": journal_head,
    }
    assert set(content) == set(SIGNED_FIELDS)
    return content


def test_journal_head_is_inside_the_signed_bytes(tmp_path: Path) -> None:
    """Not merely published beside the signature — covered by it."""

    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    content = _record("sha256:" + "c" * 64)
    signature = sign_verdict(content, private)
    assert verify_verdict(content, signature, public, payload_type=PAYLOAD_TYPE)

    tampered = {**content, "journal_head": "sha256:" + "d" * 64}
    assert not verify_verdict(tampered, signature, public, payload_type=PAYLOAD_TYPE), (
        "the head must be signed; an anchor an attacker can edit anchors nothing"
    )


def test_the_signing_domain_moved_so_a_v1_verifier_refuses_a_v2_record() -> None:
    """Old readers must refuse, not silently read a record missing the anchor."""

    assert VERDICT_DOMAIN == b"ranex-verdict-v2\n"
    assert PAYLOAD_TYPE == "application/vnd.ranex.verdict.v2+json"
    assert "journal_head" in SIGNED_FIELDS


def test_an_unanchored_verdict_is_explicit_rather_than_absent() -> None:
    """`None` is a value the record carries, not a field it omits.

    A missing field would make an unanchored verdict indistinguishable from an
    anchored one to anything reading the key set, and `signed_payload` refuses
    a record whose fields are not exactly SIGNED_FIELDS anyway.
    """

    from ranex.foundation.signing import generate_keypair
    from ranex.foundation.verdict_signing import signed_payload

    private, public = generate_keypair()
    content = _record(None)
    assert "journal_head" in content
    payload = signed_payload(content)
    assert payload.startswith(VERDICT_DOMAIN)
    assert b'"journal_head":null' in canonical_json_bytes(content)
    assert verify_verdict(content, sign_verdict(content, private), public,
                          payload_type=PAYLOAD_TYPE)


# --- the anchor is read only from a verdict that verified ----------------------


def _envelope(path: Path, content: dict[str, object], private: str,
              signer_id: str = "kernel-verdict-signer") -> None:
    record = {**content, "record_digest": "sha256:" + canonical_sha256(content)}
    path.write_bytes(canonical_json_bytes({
        "payload_type": PAYLOAD_TYPE,
        "record": record,
        "signatures": [{"signer_id": signer_id, "signature": sign_verdict(content, private)}],
    }))


def test_the_anchor_comes_from_a_verified_verdict_not_from_its_bytes(
    tmp_path: Path,
) -> None:
    """The circularity this must not have.

    An attacker who can rewrite the journal can edit a file beside it. If the
    head were read from unverified bytes, they would simply write the rewritten
    chain's head into the verdict and the anchor would confirm the forgery.
    """

    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    other_private, _other_public = generate_keypair()
    keyring = {"kernel-verdict-signer": public}

    honest = tmp_path / "honest.json"
    _envelope(honest, _record("sha256:" + "e" * 64), private)
    result = read_verdict_unbound(honest, keyring)
    assert result.state is ReadState.VERIFIED
    assert result.record is not None
    assert result.record["journal_head"] == "sha256:" + "e" * 64

    forged = tmp_path / "forged.json"
    _envelope(forged, _record("sha256:" + "f" * 64), other_private)
    assert read_verdict_unbound(forged, keyring).state is ReadState.BAD_SIGNATURE

    edited = tmp_path / "edited.json"
    _envelope(edited, _record("sha256:" + "e" * 64), private)
    payload = json.loads(edited.read_bytes())
    payload["record"]["journal_head"] = "sha256:" + "f" * 64
    edited.write_bytes(canonical_json_bytes(payload))
    assert read_verdict_unbound(edited, keyring).state is ReadState.BAD_SIGNATURE, (
        "editing the head in place must break the record digest or the "
        "signature; if it does not, the anchor is decorative"
    )


def test_context_binding_is_absent_only_where_it_cannot_be_supplied(
    tmp_path: Path,
) -> None:
    """`read_verdict_unbound` drops the judgment-context match and nothing else.

    `journal verify` knows no subject, gate, catalog or approver, so those four
    comparisons cannot run — but every check that establishes authenticity
    still does, and the two readers share one implementation so they cannot
    drift apart.
    """

    from ranex.foundation.signing import generate_keypair
    from ranex.governed_execution.verdict_reader import read_verdict

    private, public = generate_keypair()
    keyring = {"kernel-verdict-signer": public}
    path = tmp_path / "verdict.json"
    content = _record("sha256:" + "e" * 64)
    _envelope(path, content, private)

    assert read_verdict_unbound(path, keyring).state is ReadState.VERIFIED
    assert read_verdict(
        path, keyring,
        subject_digest="sha256:" + "9" * 64,
        gate_id="landing",
        catalog_digest=content["catalog_digest"],  # type: ignore[arg-type]
        approver_id="reviewer",
    ).state is ReadState.CONTEXT_MISMATCH

    unsigned = tmp_path / "unsigned.json"
    unsigned.write_bytes(canonical_json_bytes({
        "payload_type": PAYLOAD_TYPE,
        "record": {**content, "record_digest": "sha256:" + canonical_sha256(content)},
        "signatures": [],
    }))
    assert read_verdict_unbound(unsigned, keyring).state is ReadState.UNSIGNED


@pytest.mark.parametrize("missing", ["journal_head", "verdict"])
def test_a_record_missing_a_signed_field_is_refused(missing: str) -> None:
    from ranex.foundation.verdict_signing import signed_payload

    content = _record("sha256:" + "e" * 64)
    del content[missing]
    with pytest.raises(ValueError, match="must contain exactly"):
        signed_payload(content)


# --- the bug the v2 bump introduced, and its fix, against real archived data ---

ARCHIVE = Path(__file__).resolve().parents[1].parent / "tools/dogfood/audits/2026-09-06-external"


@pytest.mark.parametrize("pilot", ["leitir-verification", "arxic-verification"])
def test_a_real_archived_v1_verdict_still_verifies_and_carries_no_anchor(
    pilot: str,
) -> None:
    """Regression for a defect the anchor work introduced and then repaired.

    The first cut of ADR-057 bumped the signing domain and refused every older
    payload type outright, citing ADR-011's evidence v2 -> v3 precedent. That
    precedent does not transfer. Evidence is produced fresh each run and never
    re-read; verdicts ARE re-read, by `tools/dogfood/verify_repository_pilot.py`,
    whose entire purpose is to show that archived audits still verify. Those
    receipts are signed history and cannot honestly be re-signed, so the bump
    would have destroyed the audit trail it was meant to protect.

    These are the real committed receipts with their real signatures. They must
    verify, and they must report no anchor — reading is allowed, deciding is
    not.
    """

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        load_trust_keyring_text,
    )

    material = ARCHIVE / pilot
    if not (material / "verdict.json").is_file():
        pytest.skip(f"archived pilot receipt absent: {material}")

    keyring = load_trust_keyring_text(
        (material / "producers.yaml").read_text(encoding="utf-8"),
        material / "producers.yaml",
    )
    result = read_verdict_unbound(
        material / "verdict.json",
        {keyring.verdict_signer_id: keyring.verdict_signer_public_key},
    )

    assert result.state is ReadState.VERIFIED, (
        f"archived verdict no longer verifies ({result.state}); a version bump "
        "that invalidates retained evidence destroys the audit trail"
    )
    assert result.payload_type == "application/vnd.ranex.verdict.v1+json"
    assert result.journal_head is None, "a v1 record predates the anchor"


def test_an_unanchored_verdict_cannot_be_used_as_an_anchor(tmp_path: Path) -> None:
    """Verifiable is not the same permission as usable-for-gating."""

    from ranex.foundation.signing import generate_keypair
    from ranex.foundation.verdict_signing import (
        PAYLOAD_TYPE_V1,
        SIGNED_FIELDS_V1,
        sign_verdict,
    )

    private, public = generate_keypair()
    content = {field: _record(None)[field] for field in SIGNED_FIELDS_V1}
    record = {**content, "record_digest": "sha256:" + canonical_sha256(content)}
    path = tmp_path / "v1.json"
    path.write_bytes(canonical_json_bytes({
        "payload_type": PAYLOAD_TYPE_V1,
        "record": record,
        "signatures": [{
            "signer_id": "kernel-verdict-signer",
            "signature": sign_verdict(content, private, payload_type=PAYLOAD_TYPE_V1),
        }],
    }))

    result = read_verdict_unbound(path, {"kernel-verdict-signer": public})
    assert result.state is ReadState.VERIFIED
    assert result.journal_head is None, (
        "a v1 record must not offer an anchor; if it did, downgrading to v1 "
        "would be a way to supply one an attacker chose"
    )
