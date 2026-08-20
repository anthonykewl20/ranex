"""Closed approval authority records and least-authority capability algebra."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import NoReturn, cast

from ranex.foundation.specification_abc import canonical_payload_bytes, payload_digest


class ApprovalRefusal(ValueError):
    """A stable, domain-local refusal; ABC errors retain their ABC codes."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _refuse(code: str, detail: str) -> NoReturn:
    raise ApprovalRefusal(code, detail)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _refuse("E-APPROVAL-SHAPE", f"{field} must be a non-empty string")
    return value


def _capability_strings(
    value: object, field: str, *, container: type[list[object]] | type[tuple[object, ...]], ordered: bool,
) -> tuple[str, ...]:
    """Validate one capability collection at both untrusted construction boundaries."""

    if not isinstance(value, container) or any(not isinstance(item, str) or not item for item in value):
        label = "list" if container is list else "tuple"
        _refuse("E-APPROVAL-SHAPE", f"{field} must be a string {label}")
    values = cast(tuple[str, ...], tuple(value))
    if len(set(values)) != len(values):
        _refuse("E-APPROVAL-SHAPE", f"{field} must not repeat values")
    if any("*" in item for item in values):
        _refuse("E-APPROVAL-WILDCARD", field)
    if container is tuple and not ordered and tuple(sorted(values)) != values:
        _refuse("E-APPROVAL-SHAPE", f"{field} must be sorted and unique")
    return values if ordered else tuple(sorted(values))


def _tuple_strings(value: object, field: str) -> tuple[str, ...]:
    return _capability_strings(value, field, container=tuple, ordered=field == "argv")


def _record_strings(value: object, field: str) -> tuple[str, ...]:
    return _capability_strings(value, field, container=list, ordered=field == "argv")


def _portable_relative(value: str, field: str, *, cwd: bool = False) -> str:
    if cwd and value == ".":
        return value
    if (
        not value
        or value.startswith("/")
        or "\\" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        _refuse("E-APPROVAL-PATH", field)
    return value


def _record(value: object, fields: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        _refuse("E-APPROVAL-SHAPE", f"{field} is not a closed record")
    return value


@dataclass(frozen=True)
class PolicyCapabilities:
    """The closed v1 policy/capability grammar; empty collections grant nothing."""

    executable: str
    argv: tuple[str, ...]
    cwd: str
    roots: tuple[str, ...]
    actions: tuple[str, ...]
    environment_allow: tuple[str, ...]
    network_allow: bool
    network_hosts: tuple[str, ...]
    secret_allow: bool
    secret_names: tuple[str, ...]
    commit_allow: bool
    subagent_allow: bool
    subagent_max_children: int
    version: str = "policy-capabilities-v1"

    def __post_init__(self) -> None:
        """Direct construction is also an untrusted boundary, not an escape hatch."""

        if self.version != "policy-capabilities-v1":
            _refuse("E-APPROVAL-SHAPE", "capability version is unsupported")
        _string(self.executable, "executable")
        _tuple_strings(self.argv, "argv")
        _portable_relative(_string(self.cwd, "cwd"), "cwd", cwd=True)
        for root in _tuple_strings(self.roots, "roots"):
            _portable_relative(root, "roots")
        for field, values in (
            ("actions", self.actions), ("environment.allow", self.environment_allow),
            ("network.hosts", self.network_hosts), ("secret.names", self.secret_names),
        ):
            _tuple_strings(values, field)
        if any(type(flag) is not bool for flag in (self.network_allow, self.secret_allow, self.commit_allow, self.subagent_allow)):
            _refuse("E-APPROVAL-SHAPE", "capability flags must be booleans")
        if type(self.subagent_max_children) is not int or self.subagent_max_children < 0:
            _refuse("E-APPROVAL-SHAPE", "max_children must be a non-negative integer")

    @classmethod
    def from_record(cls, value: object) -> PolicyCapabilities:
        expected = {"version", "executable", "argv", "cwd", "roots", "actions", "environment", "network", "secret", "commit", "subagent"}
        if not isinstance(value, dict) or set(value) not in (expected, expected - {"version"}):
            _refuse("E-APPROVAL-SHAPE", "capability is not a closed record")
        record = value
        environment = _record(record["environment"], {"allow"}, "environment")
        network = _record(record["network"], {"allow", "hosts"}, "network")
        secret = _record(record["secret"], {"allow", "names"}, "secret")
        commit = _record(record["commit"], {"allow"}, "commit")
        subagent = _record(record["subagent"], {"allow", "max_children"}, "subagent")
        roots = _record_strings(record["roots"], "roots")
        for root in roots:
            _portable_relative(root, "roots")
        cwd = _portable_relative(_string(record["cwd"], "cwd"), "cwd", cwd=True)
        flags = (network["allow"], secret["allow"], commit["allow"], subagent["allow"])
        if any(type(flag) is not bool for flag in flags):
            _refuse("E-APPROVAL-SHAPE", "capability flags must be booleans")
        maximum = subagent["max_children"]
        if type(maximum) is not int or maximum < 0:
            _refuse("E-APPROVAL-SHAPE", "max_children must be a non-negative integer")
        return cls(
            _string(record["executable"], "executable"),
            _record_strings(record["argv"], "argv"), cwd, roots, _record_strings(record["actions"], "actions"),
            _record_strings(environment["allow"], "environment.allow"), cast(bool, network["allow"]),
            _record_strings(network["hosts"], "network.hosts"), cast(bool, secret["allow"]),
            _record_strings(secret["names"], "secret.names"), cast(bool, commit["allow"]),
            cast(bool, subagent["allow"]), maximum, record.get("version", "policy-capabilities-v1"),
        )

    def as_record(self) -> dict[str, object]:
        return {
            "version": self.version, "executable": self.executable, "argv": list(self.argv), "cwd": self.cwd,
            "roots": list(self.roots), "actions": list(self.actions),
            "environment": {"allow": list(self.environment_allow)},
            "network": {"allow": self.network_allow, "hosts": list(self.network_hosts)},
            "secret": {"allow": self.secret_allow, "names": list(self.secret_names)},
            "commit": {"allow": self.commit_allow},
            "subagent": {"allow": self.subagent_allow, "max_children": self.subagent_max_children},
        }

    @property
    def digest(self) -> str:
        # Policy is not an ABC payload type, so v029 canonical JSON SHA-256 applies directly.
        return payload_digest(self.as_record())


@dataclass(frozen=True)
class ApprovalPendingContext:
    a_digest: str
    subject_digest: str
    actor: str

    def as_record(self) -> dict[str, str]:
        return {"a_digest": self.a_digest, "subject_digest": self.subject_digest, "actor": self.actor}


@dataclass(frozen=True)
class RoleAssignment:
    assignment_id: str
    principal_id: str
    public_key: str
    role: str
    scope_c_digest: str

    def as_record(self) -> dict[str, str]:
        return {
            "assignment_id": self.assignment_id, "principal_id": self.principal_id,
            "public_key": self.public_key, "role": self.role, "scope_c_digest": self.scope_c_digest,
        }


_INCOMPATIBLE_ROLES = frozenset({
    frozenset(("approver", "worker")), frozenset(("approver", "evaluator")),
    frozenset(("worker", "evaluator")), frozenset(("evaluator", "publisher")),
    frozenset(("worker", "publisher")),
})
_ROLES = frozenset({"approver", "worker", "evaluator", "publisher"})


@dataclass(frozen=True)
class RoleAssignments:
    assignments: tuple[RoleAssignment, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.assignments, (tuple, list)):
            _refuse("E-APPROVAL-SHAPE", "role assignments must be a sequence")
        object.__setattr__(self, "assignments", tuple(self.assignments))
        seen_ids: set[str] = set()
        by_key: dict[str, set[str]] = {}
        for assignment in self.assignments:
            if not isinstance(assignment, RoleAssignment):
                _refuse("E-APPROVAL-SHAPE", "role assignments must contain role assignments")
            if not all(isinstance(value, str) and value for value in assignment.as_record().values()):
                _refuse("E-APPROVAL-SHAPE", "role assignment fields must be non-empty strings")
            if assignment.role not in _ROLES or assignment.assignment_id in seen_ids:
                _refuse("E-APPROVAL-ROLE", "unknown role or duplicate assignment")
            seen_ids.add(assignment.assignment_id)
            roles = by_key.setdefault(assignment.public_key, set())
            for role in roles:
                if frozenset((role, assignment.role)) in _INCOMPATIBLE_ROLES:
                    _refuse("E-APPROVAL-ROLE", "public key has incompatible roles")
            roles.add(assignment.role)

    def require(self, principal: str, key: str, role: str, c_digest: str) -> None:
        if not any(
            assignment.principal_id == principal and assignment.public_key == key
            and assignment.role == role and assignment.scope_c_digest == c_digest
            for assignment in self.assignments
        ):
            _refuse("E-APPROVAL-ROLE", "principal/key/role is absent from C-bound snapshot")

    def key_for(self, role: str, c_digest: str) -> str:
        matches = sorted({a.public_key for a in self.assignments if a.role == role and a.scope_c_digest == c_digest})
        if len(matches) != 1:
            _refuse("E-APPROVAL-ROLE", f"exactly one {role} key is required")
        return matches[0]


@dataclass(frozen=True)
class CapabilityGrant:
    grant_id: str
    c_digest: str
    parent_grant_id: str | None
    capabilities: PolicyCapabilities
    worker_key: str
    evaluator_key: str
    publisher_key: str | None
    not_before: int
    not_after: int

    def __post_init__(self) -> None:
        for value, field in (
            (self.grant_id, "grant_id"), (self.c_digest, "c_digest"),
            (self.worker_key, "worker_key"), (self.evaluator_key, "evaluator_key"),
        ):
            _string(value, field)
        if self.parent_grant_id is not None:
            _string(self.parent_grant_id, "parent_grant_id")
        if self.publisher_key is not None:
            _string(self.publisher_key, "publisher_key")
        if (
            type(self.not_before) is not int or type(self.not_after) is not int
            or self.not_before < 0 or self.not_after < self.not_before
        ):
            _refuse("E-APPROVAL-WINDOW", "grant window is invalid")

    def as_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "grant_id": self.grant_id, "c_digest": self.c_digest,
            "parent_grant_id": self.parent_grant_id, "capabilities": self.capabilities.as_record(),
            "worker_key": self.worker_key, "evaluator_key": self.evaluator_key,
            "time_window": {"not_before": self.not_before, "not_after": self.not_after},
        }
        if self.publisher_key is not None:
            record["publisher_key"] = self.publisher_key
        return record


def _intersection(values: Iterable[tuple[str, ...]]) -> tuple[str, ...]:
    iterator = iter(values)
    try:
        common = set(next(iterator))
    except StopIteration:
        return ()
    for value in iterator:
        common.intersection_update(value)
    return tuple(sorted(common))


def _root_intersection(values: Iterable[tuple[str, ...]]) -> tuple[str, ...]:
    """Return requested roots contained by a root in every authority source."""

    collections = tuple(values)
    candidates = {root for roots in collections for root in roots}
    return tuple(sorted(
        candidate for candidate in candidates
        if all(any(_path_prefix(root, candidate) for root in roots) for roots in collections)
    ))


def intersect_capabilities(*values: PolicyCapabilities, child: bool) -> PolicyCapabilities:
    """Return only common authority; child-only structural prohibitions are explicit."""

    if not values:
        _refuse("E-APPROVAL-SHAPE", "at least one capability record is required")
    if (
        len({value.executable for value in values}) != 1
        or len({value.argv for value in values}) != 1
        or len({value.cwd for value in values}) != 1
    ):
        _refuse("E-APPROVAL-EXPANSION", "executable, argv, and cwd require exact equality")
    scopes = {
        (root, action)
        for root in _root_intersection(value.roots for value in values)
        for action in _intersection(value.actions for value in values)
    }
    network_hosts = _intersection(value.network_hosts for value in values)
    network_allow = all(value.network_allow for value in values) and bool(network_hosts)
    return PolicyCapabilities(
        values[0].executable, values[0].argv, values[0].cwd,
        tuple(sorted({root for root, _ in scopes})), tuple(sorted({action for _, action in scopes})),
        _intersection(value.environment_allow for value in values), network_allow,
        network_hosts if network_allow else (),
        False if child else all(value.secret_allow for value in values),
        () if child else _intersection(value.secret_names for value in values),
        False if child else all(value.commit_allow for value in values),
        all(value.subagent_allow for value in values),
        min(value.subagent_max_children for value in values),
    )


def _path_prefix(left: str, right: str) -> bool:
    return left == right or right.startswith(left + "/")


def issue_child_grant(
    grant_id: str,
    request: PolicyCapabilities,
    parent: CapabilityGrant,
    policy: PolicyCapabilities,
    *,
    siblings: tuple[CapabilityGrant, ...] = (),
    journal_position: int,
    journal_head_link: str | None,
    prior_events: tuple[object, ...],
    principal_id: str,
    key_id: str,
) -> tuple[CapabilityGrant, object]:
    """Issue the closed intersection and its typed event; callers supply the observed prefix."""

    _string(grant_id, "grant_id")
    if not isinstance(prior_events, tuple):
        _refuse("E-APPROVAL-EVENT", "prior events must be an ordered tuple")
    if parent.c_digest == "":
        _refuse("E-APPROVAL-SHAPE", "parent C digest is absent")
    values = (request, parent.capabilities, policy)
    capabilities = intersect_capabilities(*values, child=True)
    for sibling in siblings:
        if sibling.parent_grant_id != parent.grant_id:
            continue
        shared_actions = set(capabilities.actions) & set(sibling.capabilities.actions)
        if shared_actions and any(
            _path_prefix(root, other) or _path_prefix(other, root)
            for root in capabilities.roots for other in sibling.capabilities.roots
        ):
            _refuse("E-APPROVAL-OVERLAP", "siblings share a path-prefix+action scope")
    grant = CapabilityGrant(
        grant_id, parent.c_digest, parent.grant_id, capabilities,
        parent.worker_key, parent.evaluator_key, None, parent.not_before, parent.not_after,
    )
    from ranex.governed_execution.domain.specification_events import (
        SpecificationEvent,
        grant_issued_event,
    )

    if any(not isinstance(event, SpecificationEvent) for event in prior_events):
        _refuse("E-APPROVAL-EVENT", "prior events must be specification events")
    events = cast(tuple[SpecificationEvent, ...], prior_events)
    previous_event_digest = events[-1].digest if events else None
    return grant, grant_issued_event(
        grant, seq=journal_position, journal_head_link=journal_head_link,
        principal_id=principal_id, key_id=key_id, previous_event_digest=previous_event_digest,
    )


def refuse_batch_issuance() -> None:
    """Batches need SLICE-036's compare-head/append liveness contract."""

    _refuse("E-APPROVAL-BATCH-UNSUPPORTED", "batch issuance is reserved for SLICE-036")


def canonical_record_bytes(value: object) -> bytes:
    """Public testable bridge to the v029 canonical serializer."""

    return canonical_payload_bytes(value)
