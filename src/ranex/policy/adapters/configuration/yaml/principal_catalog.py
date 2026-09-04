"""Load the committed catalog that says what a principal is permitted to be.

`producer_keyring` answers one question: is this public key one of ours. That
is enough to admit evidence and not enough to admit an *approver*, because an
approver is not a key the kernel already holds — it is a role someone claims.
Today that claim is a command-line string (`--approver <name>`), checked
against nothing. This module is the place a signature can be checked instead.

The catalog is the second trust root and is committed for the same reason as
the first: review is the control on it. Every failure path here is loud rather
than empty, because an empty catalog resolves no key, rejects every signature
as an unknown principal, and produces output indistinguishable from a project
that simply has not done the work. A broken trust root must never be mistakable
for honest absence.

Three rules carry the weight, and each is a refusal rather than a convention:

1. **One key, one principal.** Generalised from `producer_keyring`'s producer
   alias rule. If two principals share a key, whoever holds the private half
   signs as either of them, produces evidence as one and approves it as the
   other, and no-self-approval compares two different names and permits it.
2. **One principal, one role.** Per-key or per-principal role *lists* are the
   shape that lets one identity be the worker for the evidence and the approver
   for the verdict. Refusing the shape subsumes ADR-030's role incompatibility
   matrix inside this catalog: a key cannot hold two roles because it cannot
   hold two principals.
3. **A retired key resolves but cannot sign.** Rotation must not orphan the
   evidence a key produced before it was replaced, and must not leave the
   replaced key able to authorise anything new.

What this cannot do, stated where the next reader will look: the catalog binds
keys to principals, never principals to humans. One operator can add a second
principal with a second key and approve their own work. No test can see that
the two are one person. What changes is that the lie must now be a committed
diff to a trust root rather than an unrecorded argument — reviewable,
attributable, permanent. ADR-047 records that limit and why review is the
control on it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ranex.foundation.signing import is_public_key

# The role vocabulary is imported, never restated. `specification_approval`
# already owns the four roles an approval envelope may claim (ADR-030); a
# second list written out here would be a second answer to the same question,
# and the drift between them would be a defect with no test to catch it.
# `service` is added for actors that are not people — the verdict signer, and
# any future broker or operator identity.
from ranex.governed_execution.domain.specification_approval import _ROLES
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    KeyringError,
    _NoDuplicateKeys,
    load_keyring_text,
)

ROLES: frozenset[str] = frozenset(_ROLES | {"service"})

ACTIVE = "active"
RETIRED = "retired"
KEY_STATUSES: frozenset[str] = frozenset({ACTIVE, RETIRED})

_PRINCIPAL_FIELDS = ("role", "keys")
_KEY_FIELDS = ("key", "status")


class PrincipalCatalogError(KeyringError):
    """The catalog cannot be trusted, so no identity may be resolved from it.

    A subclass of `KeyringError` on purpose: callers already write
    `except KeyringError` around trust-root loads, and a new sibling exception
    would walk straight past every one of those handlers.
    """


def _closed_shape(value: object, fields: tuple[str, ...], subject: str) -> dict[str, Any]:
    """Return `value` as a mapping of exactly `fields`, or refuse.

    A field the loader ignores is a field the writer chooses and a reviewer
    reads as though it did something. `may_self_approve: true` sitting inert in
    a trust root is worse than an error.
    """

    if not isinstance(value, dict):
        raise PrincipalCatalogError(f"{subject} must be a mapping of {', '.join(fields)}")
    present = set(value)
    expected = set(fields)
    if present != expected:
        detail = []
        if unexpected := sorted(present - expected):
            detail.append(f"unexpected {', '.join(unexpected)}")
        if missing := sorted(expected - present):
            detail.append(f"missing {', '.join(missing)}")
        raise PrincipalCatalogError(
            f"{subject} must have exactly {', '.join(fields)}: " + "; ".join(detail)
        )
    return value


@dataclass(frozen=True, slots=True)
class PrincipalKey:
    """One key a principal signs with, and whether it still may."""

    public_key: str
    status: str


@dataclass(frozen=True, slots=True)
class Principal:
    """An identity, the one role it holds, and the keys that have spoken for it."""

    principal_id: str
    role: str
    keys: tuple[PrincipalKey, ...]

    @property
    def active_keys(self) -> tuple[str, ...]:
        return tuple(key.public_key for key in self.keys if key.status == ACTIVE)

    def has_active(self, public_key: str) -> bool:
        return public_key in self.active_keys


@dataclass(frozen=True, slots=True)
class PrincipalCatalog:
    """Resolved principals, plus the key index every check here goes through."""

    principals: Mapping[str, Principal]
    _by_key: Mapping[str, Principal] = field(repr=False)

    def resolve(self, public_key: object) -> Principal | None:
        """The principal this key speaks for, retired keys included, or None.

        Retired keys resolve because evidence signed before a rotation is still
        that principal's evidence. Whether the key may still *act* is
        `may_sign`, which is a different question and must not be answered by
        making the old key anonymous.
        """

        if not isinstance(public_key, str):
            return None
        return self._by_key.get(public_key)

    def may_sign(self, public_key: object) -> bool:
        """Whether this key may authorise new work. Retired keys may not."""

        principal = self.resolve(public_key)
        return principal is not None and principal.has_active(str(public_key))

    def require(self, public_key: object, *, role: str) -> Principal:
        """The principal for an active key in `role`, or refuse saying which
        of the three ways it failed."""

        if role not in ROLES:
            raise PrincipalCatalogError(
                f"unknown role {role!r}; the vocabulary is {sorted(ROLES)}"
            )
        principal = self.resolve(public_key)
        if principal is None:
            raise PrincipalCatalogError(
                f"the key presented as {role!r} is not in the catalog"
            )
        if principal.role != role:
            raise PrincipalCatalogError(
                f"principal {principal.principal_id!r} holds role "
                f"{principal.role!r}, not {role!r}"
            )
        if not principal.has_active(str(public_key)):
            raise PrincipalCatalogError(
                f"principal {principal.principal_id!r} retired that key; a "
                "retired key attributes past work and authorises none"
            )
        return principal

    def same_principal(self, public_key: object, other: object) -> bool:
        """Whether two keys are one identity — what no-self-approval must ask.

        Refuses an unresolvable key rather than answering. "Unknown versus
        unknown" answered False would let two forged identities look disjoint,
        which is precisely the answer no-self-approval must never receive.
        """

        return self._named(public_key).principal_id == self._named(other).principal_id

    def _named(self, public_key: object) -> Principal:
        """Resolve or refuse. Never `assert` — `python -O` strips those, and
        this narrowing is the check itself, not a developer's note."""

        principal = self.resolve(public_key)
        if principal is None:
            raise PrincipalCatalogError(
                f"cannot compare identities: {public_key!r} is not in the catalog"
            )
        return principal


def load_principals(path: Path | str) -> PrincipalCatalog:
    """Return the catalog at `path`, reading the working tree.

    Kept for callers that genuinely mean "the file at this path". A caller that
    has already decided which bytes it trusts — the ones git records, say —
    should hand them to `load_principals_text` instead, so the trust root that
    decides an identity is never re-read from a name the observed party can
    repoint between the check and the load.
    """

    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PrincipalCatalogError(f"cannot read the catalog at {path}: {exc}") from exc
    return load_principals_text(text, path)


def load_principals_text(text: str, source: object) -> PrincipalCatalog:
    """Return the catalog from text already in hand.

    `source` names where the text came from, for error messages only — nothing
    here reads it. That is the point: the caller has already decided which
    bytes are trustworthy, and this function cannot go behind that decision.
    """

    try:
        document = yaml.load(text, Loader=_NoDuplicateKeys)
    except KeyringError as exc:
        # `_NoDuplicateKeys` raises the base error. Re-raised as this module's
        # so a caller narrowing on PrincipalCatalogError still sees a trust-root
        # replacement that arrived disguised as an addition.
        raise PrincipalCatalogError(f"catalog at {source}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PrincipalCatalogError(f"catalog at {source} is not valid YAML: {exc}") from exc

    if not isinstance(document, dict):
        raise PrincipalCatalogError(f"catalog at {source} must be a mapping")
    if "principals" not in document:
        raise PrincipalCatalogError(f"catalog at {source} has no 'principals' mapping")

    entries = document["principals"]
    if not isinstance(entries, dict):
        raise PrincipalCatalogError(f"'principals' in {source} must be a mapping")
    # `principals: {}` is a mapping, so it passes the shape check, loops zero
    # times, and returns the empty catalog this module's docstring says must
    # never be returned. Emptying a trust root must be as loud as deleting it.
    if not entries:
        raise PrincipalCatalogError(
            f"'principals' in {source} is empty; an empty catalog resolves no "
            "key, which reads as work never done rather than as a broken root"
        )

    principals: dict[str, Principal] = {}
    by_key: dict[str, Principal] = {}
    for principal_id, entry in entries.items():
        if not isinstance(principal_id, str) or not principal_id.strip():
            raise PrincipalCatalogError(
                f"principal id {principal_id!r} must be a non-empty string"
            )
        body = _closed_shape(entry, _PRINCIPAL_FIELDS, f"principal {principal_id!r}")

        role = body["role"]
        if not isinstance(role, str) or role not in ROLES:
            raise PrincipalCatalogError(
                f"principal {principal_id!r} declares role {role!r}; one "
                f"principal holds exactly one role from {sorted(ROLES)}"
            )

        raw_keys = body["keys"]
        if not isinstance(raw_keys, list):
            raise PrincipalCatalogError(f"principal {principal_id!r} must list its keys")
        if not raw_keys:
            raise PrincipalCatalogError(
                f"principal {principal_id!r} has no keys; a principal needs at "
                "least one key or nothing can ever be attributed to it"
            )

        keys: list[PrincipalKey] = []
        seen: set[str] = set()
        for index, raw in enumerate(raw_keys):
            slot = _closed_shape(raw, _KEY_FIELDS, f"principal {principal_id!r} key {index}")
            public_key, status = slot["key"], slot["status"]
            if not is_public_key(public_key):
                raise PrincipalCatalogError(
                    f"principal {principal_id!r} key {index} is not a well-formed "
                    "public key; expected the canonical ed25519 base64 spelling"
                )
            if not isinstance(status, str) or status not in KEY_STATUSES:
                raise PrincipalCatalogError(
                    f"principal {principal_id!r} key {index} has status "
                    f"{status!r}; expected one of {sorted(KEY_STATUSES)}"
                )
            # Two entries for one key can disagree about status, and then
            # whether it may sign depends on which one was read last.
            if public_key in seen:
                raise PrincipalCatalogError(
                    f"principal {principal_id!r} lists one key twice; its status "
                    "would then depend on read order"
                )
            seen.add(public_key)
            keys.append(PrincipalKey(public_key=public_key, status=status))

        principal = Principal(
            principal_id=principal_id, role=role, keys=tuple(keys)
        )
        for key in keys:
            # One key, one identity. Whoever holds the private half of a shared
            # key produces evidence as one principal and approves it as the
            # other; no-self-approval then compares two different ids and
            # permits it. Refused here so the attack is unrepresentable.
            if (owner := by_key.get(key.public_key)) is not None:
                raise PrincipalCatalogError(
                    f"principals {owner.principal_id!r} and {principal_id!r} "
                    "share a public key; one key may serve only one principal, "
                    "or no-self-approval can be defeated by signing as either"
                )
            by_key[key.public_key] = principal
        principals[principal_id] = principal

    if "producers" in document:
        _require_blocks_agree(document["producers"], by_key, source)

    return PrincipalCatalog(principals=principals, _by_key=by_key)


def _require_blocks_agree(
    producers: object, by_key: Mapping[str, Principal], source: object
) -> None:
    """Refuse a file whose two trust-root blocks give two answers.

    The attack this closes needs no forged signature: leave `producers:` naming
    a key as one identity, add a `principals:` entry naming it another, and
    which one signed depends on which loader a caller happened to reach for.
    """

    try:
        keyring = load_keyring_text(yaml.safe_dump({"producers": producers}), source)
    except KeyringError as exc:
        raise PrincipalCatalogError(f"catalog at {source}: {exc}") from exc

    for producer_id, public_key in keyring.items():
        principal = by_key.get(public_key)
        if principal is None:
            raise PrincipalCatalogError(
                f"producer {producer_id!r} in {source} holds a key the principal "
                "catalog does not carry; evidence admitted by one trust root "
                "would be unattributable in the other"
            )
        if principal.principal_id != producer_id:
            raise PrincipalCatalogError(
                f"producer {producer_id!r} and principal "
                f"{principal.principal_id!r} in {source} claim the same key; the "
                "two blocks may not disagree about who signed"
            )
        if not principal.has_active(public_key):
            raise PrincipalCatalogError(
                f"producer {producer_id!r} in {source} is still admitted by the "
                "keyring but its catalog key is retired; the trust root would "
                "say both yes and no"
            )
