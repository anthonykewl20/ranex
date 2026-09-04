"""SLICE-080 — the principal catalog is a trust root, so every path fails closed.

Written before the implementation and required to fail first.

API pinned by these tests, in
`ranex.policy.adapters.configuration.yaml.principal_catalog`:

    class PrincipalCatalogError(KeyringError): ...
    ROLES: frozenset[str]
    KEY_STATUSES: frozenset[str]
    load_principals(path) -> PrincipalCatalog
    load_principals_text(text, source) -> PrincipalCatalog

    PrincipalKey:      .public_key .status
    Principal:         .principal_id .role .keys .active_keys .has_active(key)
    PrincipalCatalog:  .principals .resolve(key) .require(key, role=...)
                       .may_sign(key) .same_principal(a, b)

The catalog answers what the old keyring cannot: not "is this key ours" but
"what is this principal permitted to be". A catalog that cannot be read, or
that reads empty, must be a loud failure and never an empty mapping — an empty
catalog resolves nothing, which would read as honest absence rather than as a
broken trust root. Same doctrine as `producer_keyring`, same reason.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def pc():
    """Deferred import — see the note in test_producer_keyring.py."""

    from ranex.foundation import signing
    from ranex.policy.adapters.configuration.yaml import principal_catalog

    class Bundle:
        PrincipalCatalogError = principal_catalog.PrincipalCatalogError
        ROLES = principal_catalog.ROLES
        KEY_STATUSES = principal_catalog.KEY_STATUSES
        load_principals = staticmethod(principal_catalog.load_principals)
        load_principals_text = staticmethod(principal_catalog.load_principals_text)
        generate_keypair = staticmethod(signing.generate_keypair)

    return Bundle


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def catalog_text(**principals: tuple[str, list[tuple[str, str]]]) -> str:
    """Render a `principals:` document. Values are (role, [(key, status)])."""

    lines = ["principals:"]
    for principal_id, (role, keys) in principals.items():
        lines.append(f"  {principal_id}:")
        lines.append(f"    role: {role}")
        lines.append("    keys:")
        for key, status in keys:
            lines.append(f"      - key: {key}")
            lines.append(f"        status: {status}")
    return "\n".join(lines) + "\n"


# --- the happy path, and the shape it pins ----------------------------------


def test_loads_a_well_formed_catalog(pc, tmp_path: Path) -> None:
    _, worker = pc.generate_keypair()
    _, approver = pc.generate_keypair()
    path = write(
        tmp_path / "producers.yaml",
        catalog_text(
            anthony=("worker", [(worker, "active")]),
            reviewer_b=("approver", [(approver, "active")]),
        ),
    )

    catalog = pc.load_principals(path)

    assert set(catalog.principals) == {"anthony", "reviewer_b"}
    assert catalog.principals["anthony"].role == "worker"
    assert catalog.principals["anthony"].active_keys == (worker,)
    assert catalog.resolve(worker).principal_id == "anthony"
    assert catalog.resolve(approver).role == "approver"
    assert catalog.may_sign(worker) is True


def test_the_role_vocabulary_is_closed_and_is_adr_030s_plus_service(pc) -> None:
    """One vocabulary of roles in this repository, not two.

    `specification_approval._ROLES` already names four. A second, different
    list here would be a second answer to the same question, and the drift
    between them would be invisible.
    """

    from ranex.governed_execution.domain import specification_approval

    assert pc.ROLES == specification_approval._ROLES | {"service"}
    assert pc.KEY_STATUSES == {"active", "retired"}


def test_an_unknown_key_resolves_to_nothing_rather_than_raising(pc, tmp_path) -> None:
    _, worker = pc.generate_keypair()
    _, stranger = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(a=("worker", [(worker, "active")])))

    assert pc.load_principals(path).resolve(stranger) is None


# --- rotation: many keys, one identity --------------------------------------


def test_a_retired_key_still_names_its_principal_but_may_not_sign(pc, tmp_path) -> None:
    """Rotation must not rewrite history.

    Evidence signed last month by a key retired today is still that
    principal's evidence, or every rotation would orphan the record it was
    meant to protect. What retirement removes is the authority to sign
    something new.
    """

    _, old = pc.generate_keypair()
    _, new = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(anthony=("worker", [(old, "retired"), (new, "active")])),
    )

    catalog = pc.load_principals(path)

    assert catalog.resolve(old).principal_id == "anthony"
    assert catalog.may_sign(old) is False
    assert catalog.may_sign(new) is True
    assert catalog.principals["anthony"].active_keys == (new,)
    assert catalog.principals["anthony"].has_active(old) is False


def test_a_fully_retired_principal_is_a_legitimate_state(pc, tmp_path) -> None:
    """Someone leaving is not a broken trust root. Their evidence stays theirs."""

    _, gone = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(alumnus=("worker", [(gone, "retired")])))

    catalog = pc.load_principals(path)

    assert catalog.resolve(gone).principal_id == "alumnus"
    assert catalog.may_sign(gone) is False
    assert catalog.principals["alumnus"].active_keys == ()


def test_same_principal_compares_identities_not_key_strings(pc, tmp_path) -> None:
    """What no-self-approval will ask, once it asks it of keys.

    Two keys of one rotating identity are one principal. Comparing key
    strings would call them two, and a producer could approve their own work
    by rotating first.
    """

    _, old = pc.generate_keypair()
    _, new = pc.generate_keypair()
    _, other = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(
            anthony=("worker", [(old, "retired"), (new, "active")]),
            reviewer=("approver", [(other, "active")]),
        ),
    )

    catalog = pc.load_principals(path)

    assert catalog.same_principal(old, new) is True
    assert catalog.same_principal(new, other) is False


def test_same_principal_refuses_to_answer_for_an_unknown_key(pc, tmp_path) -> None:
    """An unresolvable key must not compare equal or unequal — it must refuse.

    Returning False for "unknown vs unknown" would let two forged identities
    look disjoint, which is exactly the answer no-self-approval must not get.
    """

    _, worker = pc.generate_keypair()
    _, stranger = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(a=("worker", [(worker, "active")])))
    catalog = pc.load_principals(path)

    with pytest.raises(pc.PrincipalCatalogError, match="not in the catalog"):
        catalog.same_principal(worker, stranger)


# --- require(): the check a later slice makes against a signature -----------


def test_require_returns_the_principal_for_an_active_key_in_the_named_role(pc, tmp_path):
    _, approver = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(rev=("approver", [(approver, "active")])))

    assert pc.load_principals(path).require(approver, role="approver").principal_id == "rev"


def test_require_refuses_a_key_the_catalog_does_not_carry(pc, tmp_path) -> None:
    _, approver = pc.generate_keypair()
    _, stranger = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(rev=("approver", [(approver, "active")])))

    with pytest.raises(pc.PrincipalCatalogError, match="not in the catalog"):
        pc.load_principals(path).require(stranger, role="approver")


def test_require_refuses_a_key_whose_principal_holds_another_role(pc, tmp_path) -> None:
    """The whole point: a worker's key cannot be presented as an approver's."""

    _, worker = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(anthony=("worker", [(worker, "active")])))

    with pytest.raises(pc.PrincipalCatalogError, match="role"):
        pc.load_principals(path).require(worker, role="approver")


def test_require_refuses_a_retired_key(pc, tmp_path) -> None:
    _, old = pc.generate_keypair()
    _, new = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(rev=("approver", [(old, "retired"), (new, "active")])),
    )

    with pytest.raises(pc.PrincipalCatalogError, match="retired"):
        pc.load_principals(path).require(old, role="approver")


def test_require_refuses_an_unknown_role_rather_than_never_matching(pc, tmp_path) -> None:
    """A typo in the caller must refuse, not quietly match nothing forever."""

    _, approver = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(rev=("approver", [(approver, "active")])))

    with pytest.raises(pc.PrincipalCatalogError, match="unknown role"):
        pc.load_principals(path).require(approver, role="aproverr")


# --- failing closed ---------------------------------------------------------


def test_a_missing_principals_block_is_refused(pc, tmp_path: Path) -> None:
    """Absence of the catalog is not an empty catalog."""

    _, worker = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", f"producers:\n  anthony: {worker}\n")

    with pytest.raises(pc.PrincipalCatalogError, match="no 'principals'"):
        pc.load_principals(path)


def test_an_empty_principals_block_is_refused(pc, tmp_path: Path) -> None:
    """Deleting the contents of a trust root must be as loud as deleting it."""

    path = write(tmp_path / "p.yaml", "principals: {}\n")

    with pytest.raises(pc.PrincipalCatalogError, match="empty"):
        pc.load_principals(path)


def test_an_absent_file_is_refused(pc, tmp_path: Path) -> None:
    with pytest.raises(pc.PrincipalCatalogError):
        pc.load_principals(tmp_path / "absent.yaml")


def test_a_directory_in_place_of_the_file_is_refused(pc, tmp_path: Path) -> None:
    with pytest.raises(pc.PrincipalCatalogError):
        pc.load_principals(tmp_path)


def test_invalid_yaml_is_refused(pc, tmp_path: Path) -> None:
    path = write(tmp_path / "p.yaml", "principals:\n  a: [unclosed\n")

    with pytest.raises(pc.PrincipalCatalogError):
        pc.load_principals(path)


@pytest.mark.parametrize(
    "document",
    [
        "[]\n",
        "principals: []\n",
        "principals: 3\n",
        "principals:\n  a: 3\n",
        "principals:\n  a:\n    role: worker\n",
        "principals:\n  a:\n    keys: []\n",
    ],
)
def test_a_catalog_of_the_wrong_shape_is_refused(pc, tmp_path: Path, document: str) -> None:
    path = write(tmp_path / "p.yaml", document)

    with pytest.raises(pc.PrincipalCatalogError):
        pc.load_principals(path)


def test_a_duplicate_yaml_key_is_refused(pc, tmp_path: Path) -> None:
    """YAML keeps the last of a repeated key.

    Left alone, appending four lines to this file replaces a principal with no
    diff conflict and no error — a trust-root change disguised as an addition.
    """

    _, first = pc.generate_keypair()
    _, second = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(a=("worker", [(first, "active")]))
        + catalog_text(a=("approver", [(second, "active")])).removeprefix("principals:\n"),
    )

    with pytest.raises(pc.PrincipalCatalogError, match="duplicate"):
        pc.load_principals(path)


def test_a_principal_with_no_keys_is_refused(pc, tmp_path: Path) -> None:
    path = write(tmp_path / "p.yaml", "principals:\n  a:\n    role: worker\n    keys: []\n")

    with pytest.raises(pc.PrincipalCatalogError, match="at least one key"):
        pc.load_principals(path)


def test_an_unknown_role_in_the_catalog_is_refused(pc, tmp_path: Path) -> None:
    _, key = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(a=("overlord", [(key, "active")])))

    with pytest.raises(pc.PrincipalCatalogError, match="role"):
        pc.load_principals(path)


def test_an_unknown_key_status_is_refused(pc, tmp_path: Path) -> None:
    _, key = pc.generate_keypair()
    path = write(tmp_path / "p.yaml", catalog_text(a=("worker", [(key, "probationary")])))

    with pytest.raises(pc.PrincipalCatalogError, match="status"):
        pc.load_principals(path)


@pytest.mark.parametrize("key", ["", "not-a-key", "ed25519:!!!", "ed25519:c2hvcnQ="])
def test_a_malformed_public_key_is_refused(pc, tmp_path: Path, key: str) -> None:
    path = write(tmp_path / "p.yaml", catalog_text(a=("worker", [(key or "''", "active")])))

    with pytest.raises(pc.PrincipalCatalogError, match="public key"):
        pc.load_principals(path)


def test_an_empty_principal_id_is_refused(pc, tmp_path: Path) -> None:
    _, key = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        f"principals:\n  '':\n    role: worker\n    keys:\n      - key: {key}\n        status: active\n",
    )

    with pytest.raises(pc.PrincipalCatalogError, match="principal id"):
        pc.load_principals(path)


def test_an_unexpected_field_on_a_principal_is_refused(pc, tmp_path: Path) -> None:
    """The shape is closed. A field the loader ignores is a field an attacker
    chooses, and a reviewer reads as though it did something."""

    _, key = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(a=("worker", [(key, "active")])) + "    may_self_approve: true\n",
    )

    with pytest.raises(pc.PrincipalCatalogError, match="unexpected"):
        pc.load_principals(path)


def test_an_unexpected_field_on_a_key_entry_is_refused(pc, tmp_path: Path) -> None:
    _, key = pc.generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        catalog_text(a=("worker", [(key, "active")])) + "        role: approver\n",
    )

    with pytest.raises(pc.PrincipalCatalogError, match="unexpected"):
        pc.load_principals(path)


def test_the_error_is_a_keyring_error_so_existing_handlers_still_catch_it(pc) -> None:
    """Callers already write `except KeyringError` around trust-root loads."""

    from ranex.policy.adapters.configuration.yaml.producer_keyring import KeyringError

    assert issubclass(pc.PrincipalCatalogError, KeyringError)


def test_load_principals_text_reports_the_source_it_was_given(pc) -> None:
    """The caller decides which bytes are trustworthy; the loader cannot go
    behind that decision, and says only where they came from."""

    with pytest.raises(pc.PrincipalCatalogError, match="HEAD:governance/producers.yaml"):
        pc.load_principals_text("principals: {}\n", "HEAD:governance/producers.yaml")
