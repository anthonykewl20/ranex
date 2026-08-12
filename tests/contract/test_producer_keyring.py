"""SLICE-002 — the keyring is the trust root, so every path fails closed.

Written before the implementation and required to fail first.

API pinned by these tests, in
`ranex.policy.adapters.configuration.yaml.producer_keyring`:

    class KeyringError(ValueError): ...
    load_keyring(path) -> dict[str, str]      # producer_id -> "ed25519:<b64>"

A keyring that cannot be read must be a loud failure, never an empty mapping.
An empty mapping would reject every record and read as "no evidence", turning a
broken trust root into what looks like honest absence.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def kr():
    """Deferred import — see the note in test_evidence_signing.py."""

    from ranex.foundation import signing
    from ranex.policy.adapters.configuration.yaml import producer_keyring

    class Bundle:
        KeyringError = producer_keyring.KeyringError
        load_keyring = staticmethod(producer_keyring.load_keyring)
        generate_keypair = staticmethod(signing.generate_keypair)

    return Bundle


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_a_well_formed_keyring(kr, tmp_path: Path) -> None:
    _, worker = kr.generate_keypair()
    _, alice = kr.generate_keypair()
    path = write(
        tmp_path / "producers.yaml",
        f"producers:\n  worker: {worker}\n  reviewer_alice: {alice}\n",
    )

    assert kr.load_keyring(path) == {"worker": worker, "reviewer_alice": alice}


def test_one_key_may_not_serve_two_producers(kr, tmp_path: Path) -> None:
    """The alias attack, refused at the trust root.

    If `alice` and `worker` share a public key, whoever holds the private key
    signs as either identity. They then produce evidence as `worker` and approve
    as `alice`, and no-self-approval sees two different strings and permits it.
    The keyring must make this unrepresentable rather than rely on review.
    """

    _, shared = kr.generate_keypair()
    path = write(
        tmp_path / "producers.yaml",
        f"producers:\n  worker: {shared}\n  reviewer_alice: {shared}\n",
    )

    with pytest.raises(kr.KeyringError, match="(?i)key"):
        kr.load_keyring(path)


def test_duplicate_producer_entries_are_refused(kr, tmp_path: Path) -> None:
    """YAML permits a repeated key and silently keeps the last. Resolving that
    by last-wins would let an appended line quietly replace a producer's key."""

    _, first = kr.generate_keypair()
    _, second = kr.generate_keypair()
    path = write(
        tmp_path / "producers.yaml",
        f"producers:\n  worker: {first}\n  worker: {second}\n",
    )

    with pytest.raises(kr.KeyringError):
        kr.load_keyring(path)


def test_missing_file_is_an_error_not_an_empty_keyring(kr, tmp_path: Path) -> None:
    with pytest.raises(kr.KeyringError):
        kr.load_keyring(tmp_path / "absent.yaml")


def test_invalid_yaml_is_an_error(kr, tmp_path: Path) -> None:
    path = write(tmp_path / "producers.yaml", "producers:\n  worker: [unclosed\n")
    with pytest.raises(kr.KeyringError):
        kr.load_keyring(path)


def test_wrong_shape_is_an_error(kr, tmp_path: Path) -> None:
    for text in ("[]\n", "producers: []\n", "producers: worker\n", "{}\n"):
        path = write(tmp_path / "producers.yaml", text)
        with pytest.raises(kr.KeyringError):
            kr.load_keyring(path)


@pytest.mark.parametrize(
    "key",
    [
        "",
        "not-a-key",
        "ed25519:",
        "ed25519:!!!not-base64!!!",
        "ed25519:c2hvcnQ=",  # valid base64, wrong length for Ed25519
        "rsa:AAAA",
    ],
)
def test_malformed_public_key_is_an_error(kr, tmp_path: Path, key: str) -> None:
    path = write(tmp_path / "producers.yaml", f"producers:\n  worker: {key!r}\n")
    with pytest.raises(kr.KeyringError):
        kr.load_keyring(path)


def test_empty_producer_id_is_an_error(kr, tmp_path: Path) -> None:
    _, public = kr.generate_keypair()
    path = write(tmp_path / "producers.yaml", f"producers:\n  '': {public}\n")
    with pytest.raises(kr.KeyringError):
        kr.load_keyring(path)


def test_loads_dedicated_verdict_signer_separately(kr, tmp_path: Path) -> None:
    from ranex.policy.adapters.configuration.yaml.producer_keyring import load_trust_keyring

    _, worker = kr.generate_keypair()
    _, signer = kr.generate_keypair()
    path = write(tmp_path / "producers.yaml", (
        f"producers:\n  worker: {worker}\n"
        "verdict_signer:\n  id: kernel-verdict-signer\n"
        f"  public_key: {signer}\n"
    ))
    loaded = load_trust_keyring(path)
    assert loaded.producers == {"worker": worker}
    assert loaded.verdict_signer_id == "kernel-verdict-signer"
    assert loaded.verdict_signer_public_key == signer


def test_verdict_signer_must_exist_and_may_not_alias_a_producer(kr, tmp_path: Path) -> None:
    from ranex.policy.adapters.configuration.yaml.producer_keyring import load_trust_keyring

    _, shared = kr.generate_keypair()
    missing = write(tmp_path / "missing.yaml", f"producers:\n  worker: {shared}\n")
    with pytest.raises(kr.KeyringError, match="verdict_signer"):
        load_trust_keyring(missing)
    aliased = write(tmp_path / "aliased.yaml", (
        f"producers:\n  worker: {shared}\nverdict_signer:\n"
        f"  id: kernel-verdict-signer\n  public_key: {shared}\n"
    ))
    with pytest.raises(kr.KeyringError, match="(?i)key|alias"):
        load_trust_keyring(aliased)
