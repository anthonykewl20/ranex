"""Closed approval authority records and least-authority capability algebra."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ranex.foundation.specification_abc import canonical_payload_bytes, payload_digest


class ApprovalRefusal(ValueError):
    """A stable, domain-local refusal; ABC errors retain their ABC codes."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _refuse(code: str, detail: str) -> None:
    raise ApprovalRefusal(code, detail)


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _refuse("E-APPROVAL-SHAPE", f"{field} must be a non-empty string")
    return value


def _strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        _refuse("E-APPROVAL-SHAPE", f"{field} must be a string list")
    if len(set(value)) != len(value):
        _refuse("E-APPROVAL-SHAPE", f"{field} must not repeat values")
    if any("*" in item for item in value):
        _refuse("E-APPROVAL-WILDCARD", field)
    return tuple(sorted(value))


def _tuple_strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or any(not isinstance(item, str) or not item for item in value):
        _refuse("E-APPROVAL-SHAPE", f"{field} must be a string tuple")
    if tuple(sorted(value)) != value or len(set(value)) != len(value):
        _refuse("E-APPROVAL-SHAPE", f"{field} must be sorted and unique")
    if any("*" in item for item in value):
        _refuse("E-APPROVAL-WILDCARD", field)
    return value


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

    def __post_init__(self) -> None:
        """Direct construction is also an untrusted boundary, not an escape hatch."""

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
        record = _record(value, {"executable", "argv", "cwd", "roots", "actions", "environment", "network", "secret", "commit", "subagent"}, "capability")
        environment = _record(record["environment"], {"allow"}, "environment")
        network = _record(record["network"], {"allow", "hosts"}, "network")
        secret = _record(record["secret"], {"allow", "names"}, "secret")
        commit = _record(record["commit"], {"allow"}, "commit")
        subagent = _record(record["subagent"], {"allow", "max_children"}, "subagent")
        roots = _strings(record["roots"], "roots")
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
            _strings(record["argv"], "argv"), cwd, roots, _strings(record["actions"], "actions"),
            _strings(environment["allow"], "environment.allow"), network["allow"],
            _strings(network["hosts"], "network.hosts"), secret["allow"],
            _strings(secret["names"], "secret.names"), commit["allow"],
            subagent["allow"], maximum,
        )

    def as_record(self) -> dict[str, object]:
        return {
            "executable": self.executable, "argv": list(self.argv), "cwd": self.cwd,
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
    semantic_digest: str
    actor: str

    def as_record(self) -> dict[str, str]:
        return {"semantic_digest": self.semantic_digest, "actor": self.actor}


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
        seen_ids: set[str] = set()
        by_key: dict[str, set[str]] = {}
        for assignment in self.assignments:
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

    def as_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "grant_id": self.grant_id, "c_digest": self.c_digest,
            "parent_grant_id": self.parent_grant_id, "capabilities": self.capabilities.as_record(),
            "worker_key": self.worker_key, "evaluator_key": self.evaluator_key,
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


def issue_child_grant(
    grant_id: str,
    request: PolicyCapabilities,
    parent: CapabilityGrant,
    policy: PolicyCapabilities,
    *,
    siblings: tuple[CapabilityGrant, ...] = (),
) -> CapabilityGrant:
    """Issue the closed intersection; no field has an implicit allow-all meaning."""

    _string(grant_id, "grant_id")
    if parent.c_digest == "":
        _refuse("E-APPROVAL-SHAPE", "parent C digest is absent")
    values = (request, parent.capabilities, policy)
    if len({value.executable for value in values}) != 1 or len({value.argv for value in values}) != 1 or len({value.cwd for value in values}) != 1:
        _refuse("E-APPROVAL-EXPANSION", "executable, argv, and cwd require exact equality")
    scopes = {(root, action) for root in _intersection(v.roots for v in values) for action in _intersection(v.actions for v in values)}
    for sibling in siblings:
        if sibling.parent_grant_id != parent.grant_id:
            continue
        sibling_scopes = {(root, action) for root in sibling.capabilities.roots for action in sibling.capabilities.actions}
        if scopes & sibling_scopes:
            _refuse("E-APPROVAL-OVERLAP", "siblings share a path+action scope")
    network_allow = all(value.network_allow for value in values)
    network_hosts = _intersection(value.network_hosts for value in values) if network_allow else ()
    capabilities = PolicyCapabilities(
        request.executable, request.argv, request.cwd,
        tuple(sorted({root for root, _ in scopes})), tuple(sorted({action for _, action in scopes})),
        _intersection(value.environment_allow for value in values), network_allow, network_hosts,
        False, (), False, all(value.subagent_allow for value in values),
        min(value.subagent_max_children for value in values),
    )
    return CapabilityGrant(
        grant_id, parent.c_digest, parent.grant_id, capabilities,
        parent.worker_key, parent.evaluator_key, None,
    )


def refuse_batch_issuance() -> None:
    """Batches need SLICE-036's compare-head/append liveness contract."""

    _refuse("E-APPROVAL-BATCH-UNSUPPORTED", "batch issuance is reserved for SLICE-036")


def canonical_record_bytes(value: object) -> bytes:
    """Public testable bridge to the v029 canonical serializer."""

    return canonical_payload_bytes(value)
