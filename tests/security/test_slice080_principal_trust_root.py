"""SLICE-080 — attacks on the principal catalog.

The catalog exists so that a later slice can prove an approver by signature
instead of accepting a typed name. Every attack here is an attempt to make one
holder of one private key occupy two identities, or to make a key claim
authority the committed trust root never granted it. Each must be
unrepresentable, not merely discouraged by review.
"""

from __future__ import annotations

import base64
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from ranex.foundation.signing import generate_keypair
from ranex.policy.adapters.configuration.yaml.principal_catalog import (
    ROLES,
    PrincipalCatalogError,
    load_principals,
    load_principals_text,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_KEYRING = REPO_ROOT / "governance" / "producers.yaml"

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def entry(principal_id: str, role: str, *keys: tuple[str, str]) -> str:
    lines = [f"  {principal_id}:", f"    role: {role}", "    keys:"]
    for key, status in keys:
        lines += [f"      - key: {key}", f"        status: {status}"]
    return "\n".join(lines) + "\n"


def document(*entries: str) -> str:
    return "principals:\n" + "".join(entries)


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def respelled(public_key: str) -> str:
    """The same 32 bytes, spelled with different unread padding bits.

    A 32-byte key does not divide into 3-byte base64 groups, so its final
    character carries two bits no decoder reads: four strings decode to one
    key. If the catalog accepted them, one key would be four identities and
    the one-key-one-principal rule would buy nothing.
    """

    body = public_key.removeprefix("ed25519:")
    index = _ALPHABET.index(body[-2])
    variant = _ALPHABET[index ^ 0b01]
    assert variant != body[-2]
    alias = "ed25519:" + body[:-2] + variant + body[-1]
    assert base64.b64decode(alias.removeprefix("ed25519:")) == base64.b64decode(body)
    assert alias != public_key
    return alias


# --- one key must never be two identities -----------------------------------


def test_one_key_may_not_serve_two_principals(tmp_path: Path) -> None:
    """The alias attack, refused at the trust root.

    If `anthony` and `reviewer` share a public key, whoever holds the private
    half signs as either identity: they produce evidence as one and approve it
    as the other, and no-self-approval compares two different principals and
    permits it. `producer_keyring` already refuses this for producers; the
    catalog is a second trust root and must refuse it too, or the rule is only
    enforced on the half of the file nobody is attacking.
    """

    _, shared = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        document(entry("anthony", "worker", (shared, "active")),
                 entry("reviewer", "approver", (shared, "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="share a public key"):
        load_principals(path)


def test_the_alias_rule_holds_across_active_and_retired(tmp_path: Path) -> None:
    """Retiring the second copy does not launder the alias.

    A retired key still resolves to a principal. Two principals resolving from
    one key is ambiguous attribution however the second copy is labelled.
    """

    _, shared = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        document(entry("anthony", "worker", (shared, "active")),
                 entry("reviewer", "approver", (shared, "retired"))),
    )

    with pytest.raises(PrincipalCatalogError, match="share a public key"):
        load_principals(path)


def test_one_key_may_not_be_listed_twice_inside_one_principal(tmp_path: Path) -> None:
    """Not an attack on identity, but on the record: two entries for one key
    can disagree about its status, and then whether it may sign depends on
    which one the loader happened to read last."""

    _, key = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        document(entry("anthony", "worker", (key, "retired"), (key, "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="twice"):
        load_principals(path)


def test_a_respelled_key_cannot_smuggle_a_second_identity(tmp_path: Path) -> None:
    """Four base64 strings decode to one Ed25519 key.

    Accepting a non-canonical spelling would let the same private key hold two
    principal ids that the alias check cannot see are the same, which is the
    one-key-one-principal rule defeated for the price of one character.
    """

    _, key = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        document(entry("anthony", "worker", (key, "active")),
                 entry("reviewer", "approver", (respelled(key), "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="public key"):
        load_principals(path)


def test_a_yaml_anchor_does_not_hide_a_shared_key(tmp_path: Path) -> None:
    """The alias check must see resolved values, not the text that produced them."""

    _, shared = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        "principals:\n"
        "  anthony:\n"
        "    role: worker\n"
        "    keys:\n"
        f"      - &shared\n        key: {shared}\n        status: active\n"
        "  reviewer:\n"
        "    role: approver\n"
        "    keys:\n"
        "      - *shared\n",
    )

    with pytest.raises(PrincipalCatalogError, match="share a public key"):
        load_principals(path)


# --- a principal may not claim authority the catalog does not grant ---------


def test_a_principal_may_not_hold_two_roles(tmp_path: Path) -> None:
    """One principal, one role.

    Per-principal role lists are the shape that lets one key be a worker for
    the evidence and an approver for the verdict, which is self-approval with
    extra steps. ADR-030's incompatibility matrix is subsumed by refusing the
    shape rather than by policing pairs inside it.
    """

    _, key = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        "principals:\n"
        "  anthony:\n"
        "    role:\n      - worker\n      - approver\n"
        "    keys:\n"
        f"      - key: {key}\n        status: active\n",
    )

    with pytest.raises(PrincipalCatalogError, match="role"):
        load_principals(path)


def test_a_worker_key_cannot_be_required_as_an_approver(tmp_path: Path) -> None:
    _, worker = generate_keypair()
    path = write(tmp_path / "p.yaml", document(entry("anthony", "worker", (worker, "active"))))

    catalog = load_principals(path)

    assert catalog.resolve(worker).role == "worker"
    with pytest.raises(PrincipalCatalogError, match="role"):
        catalog.require(worker, role="approver")


def test_a_retired_key_cannot_sign_new_work(tmp_path: Path) -> None:
    """Rotation is only a control if the old key stops being able to act."""

    _, old = generate_keypair()
    _, new = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        document(entry("reviewer", "approver", (old, "retired"), (new, "active"))),
    )

    catalog = load_principals(path)

    assert catalog.resolve(old).principal_id == "reviewer"
    assert catalog.may_sign(old) is False
    with pytest.raises(PrincipalCatalogError, match="retired"):
        catalog.require(old, role="approver")


# --- the two blocks may not give two answers --------------------------------


def test_a_producer_missing_from_the_catalog_is_refused(tmp_path: Path) -> None:
    """Every key the old trust root admits must be attributable in the new one,
    or evidence admitted by one is unattributable by the other."""

    _, worker = generate_keypair()
    _, other = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        f"producers:\n  anthony: {worker}\n"
        + document(entry("reviewer", "approver", (other, "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="anthony"):
        load_principals(path)


def test_the_two_blocks_may_not_disagree_about_who_owns_a_key(tmp_path: Path) -> None:
    """The attack this closes: leave `producers:` naming the key as `anthony`,
    add a `principals:` entry naming it `reviewer`, and whichever loader a
    caller reaches for decides who signed."""

    _, key = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        f"producers:\n  anthony: {key}\n"
        + document(entry("reviewer", "approver", (key, "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="share a public key|anthony"):
        load_principals(path)


def test_a_producer_whose_catalog_key_is_retired_is_refused(tmp_path: Path) -> None:
    """A key the old loader still admits, retired in the new one, is a trust
    root that says both yes and no."""

    _, key = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        f"producers:\n  anthony: {key}\n"
        + document(entry("anthony", "worker", (key, "retired"))),
    )

    with pytest.raises(PrincipalCatalogError, match="retired"):
        load_principals(path)


def test_a_producer_carrying_a_different_key_than_the_catalog_is_refused(tmp_path) -> None:
    _, old = generate_keypair()
    _, new = generate_keypair()
    path = write(
        tmp_path / "p.yaml",
        f"producers:\n  anthony: {old}\n"
        + document(entry("anthony", "worker", (new, "active"))),
    )

    with pytest.raises(PrincipalCatalogError, match="anthony"):
        load_principals(path)


def test_a_catalog_only_document_needs_no_producers_block(tmp_path: Path) -> None:
    """Consistency is a check between two present blocks, not a requirement
    that both exist. An external repository may adopt the catalog alone."""

    _, key = generate_keypair()
    path = write(tmp_path / "p.yaml", document(entry("anthony", "worker", (key, "active"))))

    assert set(load_principals(path).principals) == {"anthony"}


# --- the trust root of whatever repository this suite runs in ---------------
#
# These arms deliberately do NOT assert "the ranex repository has a catalog".
# Several e2e journeys (test_gating_real_suite, test_cold_start_journey) clone
# this repository, REPLACE `governance/producers.yaml` with a two-block fixture
# keyring, and re-run the whole suite inside the clone. An arm that demanded a
# `principals:` block there would fail for a reason that is not a defect: the
# block is optional by ADR-047 precisely so a repository that adopted only the
# older blocks keeps working.
#
# So the property asserted is the universal one, and it is the one that
# protects this repository: *if* a trust root carries a catalog, that catalog
# must be valid and must agree with the keyring beside it. The real file has a
# catalog, so any corruption of it fails here. The branch that finds none
# asserts what it found instead of skipping — a skip would hide the difference
# between "this fixture has no catalog" and "the catalog stopped loading".


def live_document() -> dict:
    """The committed trust root of the repository this suite is running in."""

    loaded = yaml.safe_load(LIVE_KEYRING.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), f"{LIVE_KEYRING} is not a mapping"
    return loaded


def test_a_committed_catalog_loads_and_agrees_with_the_keyring_beside_it() -> None:
    trust_root = live_document()
    if "principals" not in trust_root:
        assert "producers" in trust_root, (
            f"{LIVE_KEYRING} carries neither a catalog nor a producer keyring; "
            "it is not a trust root at all"
        )
        return

    catalog = load_principals(LIVE_KEYRING)

    assert catalog.principals, "a loaded catalog is never empty"
    for principal in catalog.principals.values():
        assert principal.role in ROLES
        assert principal.keys, f"{principal.principal_id} has no keys"


def test_a_committed_catalog_and_keyring_name_the_same_keys() -> None:
    """Belt and braces: load each block with its own loader and compare.

    `load_principals` already refuses a disagreement. This asserts the same
    thing from outside, so a future relaxation of the internal check cannot
    pass unnoticed.
    """

    from ranex.policy.adapters.configuration.yaml.producer_keyring import load_keyring

    trust_root = live_document()
    if "principals" not in trust_root:
        return

    catalog = load_principals(LIVE_KEYRING)
    for producer_id, public_key in load_keyring(LIVE_KEYRING).items():
        principal = catalog.resolve(public_key)
        assert principal is not None, f"{producer_id} has no principal"
        assert principal.principal_id == producer_id
        assert catalog.may_sign(public_key) is True


def test_a_committed_verdict_signer_is_a_service_principal_not_a_producer() -> None:
    """`verdict_signer` may not alias a producer — the existing rule, restated
    in the catalog's vocabulary so both trust roots enforce it."""

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        load_trust_keyring,
    )

    trust_root = live_document()
    if "principals" not in trust_root or "verdict_signer" not in trust_root:
        return

    trust = load_trust_keyring(LIVE_KEYRING)
    catalog = load_principals(LIVE_KEYRING)
    signer = catalog.resolve(trust.verdict_signer_public_key)

    assert signer is not None
    assert signer.principal_id == trust.verdict_signer_id
    assert signer.role == "service"
    assert signer.principal_id not in trust.producers


def test_the_older_loaders_still_read_the_committed_trust_root() -> None:
    """Extended, not replaced: the original loaders still work on the real file,
    catalog present or not."""

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        load_keyring,
        load_trust_keyring,
    )

    trust_root = live_document()
    assert load_keyring(LIVE_KEYRING), "the producer keyring still loads"
    if "verdict_signer" in trust_root:
        assert load_trust_keyring(LIVE_KEYRING).verdict_signer_id


def test_this_checkouts_catalog_is_the_one_slice_080_committed() -> None:
    """The done criterion, asserted where a fixture cannot silently replace it.

    Journeys overwrite the working-tree keyring; none of them rewrites git
    history, so HEAD in any clone of this repository still carries the catalog
    SLICE-080 committed. Read the bytes git records rather than the file on
    disk — the same discipline `cmd_gate_evaluate` uses for the keyring that
    decides a verdict.
    """

    blob = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "cat-file", "-p", "HEAD:governance/producers.yaml"],
        capture_output=True,
        text=True,
        check=False,
        # An ambient GIT_DIR names a different repository, and the question here
        # is about this one — the same reason `git()` in cli/main.py strips it.
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )
    if blob.returncode != 0 or "principals:" not in blob.stdout:
        # Not this repository's history: a journey that commits a two-block
        # fixture keyring into its clone has no catalog at HEAD either, and
        # that is the same legitimate absence the arms above branch on.
        return

    catalog = load_principals_text(blob.stdout, "HEAD:governance/producers.yaml")

    assert catalog.principals["anthony"].role == "worker"
    assert catalog.principals["kernel-verdict-signer"].role == "service"
    assert catalog.principals["kernel-verdict-signer"].active_keys


# --- failing closed, from bytes already in hand -----------------------------


def test_a_truncated_catalog_is_refused_rather_than_read_empty() -> None:
    with pytest.raises(PrincipalCatalogError):
        load_principals_text("", "HEAD:governance/producers.yaml")


def test_a_catalog_emptied_in_place_is_refused() -> None:
    """Deleting every principal must be as loud as deleting the file: an empty
    catalog resolves no key, so every signature becomes an unknown principal
    and the output reads as work never done."""

    with pytest.raises(PrincipalCatalogError, match="empty"):
        load_principals_text("principals: {}\n", "HEAD:governance/producers.yaml")


# --- the older loader's closed block set stays closed ------------------------


def _trust_document(extra: str = "") -> str:
    _, producer = generate_keypair()
    _, signer = generate_keypair()
    return (
        f"producers:\n  anthony: {producer}\n"
        "verdict_signer:\n"
        "  id: kernel-verdict-signer\n"
        f"  public_key: {signer}\n" + extra
    )


def test_the_trust_keyring_still_refuses_a_block_it_does_not_name() -> None:
    """SLICE-080 admits `principals` to that loader's closed set and nothing else.

    The set is closed so that a block a loader silently ignores cannot sit in a
    trust root looking as though it did something. Admitting one name
    deliberately must not turn the document into an open one.
    """

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        KeyringError,
        load_trust_keyring_text,
    )

    with pytest.raises(KeyringError, match="producers and verdict_signer"):
        load_trust_keyring_text(_trust_document("shadow_signer:\n  id: x\n"), "fixture")


def test_the_trust_keyring_loads_a_document_that_carries_the_catalog() -> None:
    """The block is admitted, not parsed here — `principal_catalog` owns it."""

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        load_trust_keyring_text,
    )

    _, other = generate_keypair()
    text = _trust_document(document(entry("reviewer", "approver", (other, "active"))))

    assert load_trust_keyring_text(text, "fixture").verdict_signer_id == (
        "kernel-verdict-signer"
    )

