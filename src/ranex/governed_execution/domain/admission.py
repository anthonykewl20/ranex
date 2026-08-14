"""Which records become evidence, and why the rest did not.

`evaluate()` is a pure function of (gate, evidence, subject, approver) and stays
one. Verification happens here instead, so a record that does not verify is
never admitted and reaches the kernel as *absence* — which already blocks.

That reduction is only safe because rejections leave here as **structured data**.
Both forged and absent produce FAIL, but they are not the same event: absence is
work not done, forgery is an attack. If the difference lived only in printed
prose, an automated consumer would read an attack as a missing task.

The trust chain, stated once:

    raw records + keyring  ──admit──▶  admitted evidence  ──evaluate()──▶  verdict
                                       + rejections

The keyring is an input to admission and never to the kernel. Keys are ambient
machine state, and a kernel whose judgement depended on them would break the
principle behind "removing every credential from the machine must not change a
verdict".

`admit` takes a plain mapping of producer id to public key, never a path and
never a loader: the domain does not reach for adapters.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ranex.foundation.signing import (
    SIGNED_FIELDS,
    is_signature,
    signed_payload,
    verify_evidence,
)
from ranex.foundation.suite_results import validate_suite_results
from ranex.governed_execution.domain.verdict import Evidence


class RejectionReason(StrEnum):
    """Why a record is not evidence.

    Deliberately none of these reads as "no evidence for required claim". That
    is the kernel's phrasing for honest absence, and a rejection must never be
    mistakable for it.
    """

    MALFORMED_RECORD = "malformed-record"
    MISSING_SIGNATURE = "missing-signature"
    MALFORMED_SIGNATURE = "malformed-signature"
    UNKNOWN_PRODUCER = "unknown-producer"
    BAD_SIGNATURE = "bad-signature"
    STALE_HOST_STATE = "stale-host-state"
    # SLICE-003. Decided outside this module, because containment is a question
    # about a repository and the domain does not reach for one; named here so a
    # refusal for it is reported as structured data like every other.
    EXECUTABLE_INSIDE_SUBJECT = "executable-inside-subject"


@dataclass(frozen=True, slots=True)
class Rejection:
    """One record that did not become evidence, locatable by a human."""

    index: int
    reason: RejectionReason
    detail: str
    producer_id: str | None
    claim_id: str | None


@dataclass(frozen=True, slots=True)
class Admission:
    evidence: tuple[Evidence, ...]
    rejections: tuple[Rejection, ...]


_SIGNATURE = "signature"
_QUALIFICATION_CLAIM = "host-qualification"
_QUALIFICATION_SCHEMA = "ranex-strict-local-qualification-v1"
_SHA256 = re.compile(r"(?:sha256:)?[0-9a-f]{64}\Z")


def _required_host_text(path: Path, field: str, *, limit: int = 65_536) -> str:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        raw = os.read(descriptor, limit + 1)
    finally:
        os.close(descriptor)
    if len(raw) > limit:
        raise ValueError(f"live host-state {field} exceeds {limit} bytes")
    value = raw.decode("utf-8").strip()
    if not value:
        raise ValueError(f"live host-state {field} is empty")
    return value


def _parent_namespace_id(value: int, *, kind: str) -> int:
    lines = Path(f"/proc/self/{kind}_map").read_text(encoding="utf-8").splitlines()
    ranges = [tuple(int(field) for field in line.split()) for line in lines]
    if any(len(fields) != 3 for fields in ranges):
        raise ValueError(f"live parent {kind} identity map is malformed")
    for inside, outside, length in ranges:
        if inside <= value < inside + length:
            return outside + value - inside
    raise ValueError(f"live {kind} has no parent-namespace identity")


def _policy_identity(active_lsms: set[str], name: str) -> Mapping[str, str]:
    if name not in active_lsms:
        return {"status": "inactive"}
    if name == "apparmor":
        return {
            "status": "active",
            "enabled": _required_host_text(
                Path("/sys/module/apparmor/parameters/enabled"), "AppArmor enabled state"
            ),
            "namespace": _required_host_text(
                Path("/sys/kernel/security/apparmor/.ns_name"), "AppArmor policy namespace"
            ),
            "revision": _required_host_text(
                Path("/sys/kernel/security/apparmor/revision"), "AppArmor policy revision"
            ),
            "current_profile": _required_host_text(
                Path("/proc/self/attr/apparmor/current"), "AppArmor current profile"
            ),
        }
    policy = Path("/sys/fs/selinux/policy")
    policy_sha256 = "sha256:" + hashlib.sha256(policy.read_bytes()).hexdigest()
    return {
        "status": "active",
        "policy_sha256": policy_sha256,
        "policy_version": _required_host_text(
            Path("/sys/fs/selinux/policyvers"), "SELinux policy version"
        ),
        "enforcing": _required_host_text(
            Path("/sys/fs/selinux/enforce"), "SELinux enforcing state"
        ),
        "current_context": _required_host_text(
            Path("/proc/self/attr/selinux/current"), "SELinux current context"
        ),
    }


def _read_live_durable_host_state() -> Mapping[str, Any]:
    """Read freshness anchors; tests replace this exact seam with masked state."""

    lsm_text = _required_host_text(Path("/sys/kernel/security/lsm"), "active LSM list")
    active_lsms = {name.strip() for name in lsm_text.split(",") if name.strip()}
    sysctls: dict[str, str] = {}
    for name, path in (
        ("kernel.unprivileged_userns_clone", Path("/proc/sys/kernel/unprivileged_userns_clone")),
        ("user.max_user_namespaces", Path("/proc/sys/user/max_user_namespaces")),
    ):
        if path.exists():
            sysctls[name] = _required_host_text(path, name)
    if "user.max_user_namespaces" not in sysctls:
        raise ValueError("live mandatory user.max_user_namespaces host state is unavailable")
    return {
        "lsm": {
            "securityfs_lsm": lsm_text,
            "apparmor_policy_identity": _policy_identity(active_lsms, "apparmor"),
            "selinux_policy_identity": _policy_identity(active_lsms, "selinux"),
        },
        "unprivileged_userns_sysctls": sysctls,
        "boot_id": _required_host_text(
            Path("/proc/sys/kernel/random/boot_id"), "boot ID"
        ),
        "machine_id": _required_host_text(Path("/etc/machine-id"), "machine ID"),
        "delegation_identity": {
            "uid": _parent_namespace_id(os.geteuid(), kind="uid"),
            "gid": _parent_namespace_id(os.getegid(), kind="gid"),
        },
    }


def _mapping_with_keys(value: Any, keys: set[str], field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"{field} does not match its closed schema")
    return value


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} is not a non-empty string")
    return value


def _required_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} is not an integer")
    return value


def _required_boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} is not a boolean")
    return value


def _required_sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field} is not a sha256 digest")
    return value


def _required_text_list(value: Any, field: str) -> Sequence[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{field} is not a non-empty list of non-empty strings")
    return value


def _validate_open_object(value: Any, field: str) -> None:
    opened = _mapping_with_keys(
        value,
        {
            "path", "realpath", "sha256", "device", "inode", "uid", "gid",
            "mode", "mount_id", "security_capability", "filesystem",
        },
        field,
    )
    for name in ("path", "realpath"):
        _required_text(opened[name], f"{field}.{name}")
    _required_sha256(opened["sha256"], f"{field}.sha256")
    for name in ("device", "inode", "uid", "gid", "mode", "mount_id"):
        _required_integer(opened[name], f"{field}.{name}")
    _required_boolean(opened["security_capability"], f"{field}.security_capability")
    filesystem = _mapping_with_keys(
        opened["filesystem"],
        {"device", "filesystem", "mount_id", "mount_point", "options", "source"},
        f"{field}.filesystem",
    )
    for name in ("device", "filesystem", "mount_point", "source"):
        _required_text(filesystem[name], f"{field}.filesystem.{name}")
    _required_integer(filesystem["mount_id"], f"{field}.filesystem.mount_id")
    _required_text_list(filesystem["options"], f"{field}.filesystem.options")


def _validate_qualification_report(value: Any) -> Mapping[str, Any]:
    report = _mapping_with_keys(
        value,
        {
            "schema", "qualified", "refusal", "kernel", "primitives", "cgroup",
            "open_objects", "digests", "delegation", "host_state",
        },
        "host-qualification report",
    )
    if report["schema"] != _QUALIFICATION_SCHEMA:
        raise ValueError(f"unknown host-qualification schema: {report['schema']!r}")
    if report["qualified"] is not True or report["refusal"] is not None:
        raise ValueError("host-qualification report is not a successful qualification")
    kernel = _mapping_with_keys(report["kernel"], {"release", "architecture"}, "kernel")
    _required_text(kernel["release"], "kernel.release")
    _required_text(kernel["architecture"], "kernel.architecture")
    primitives = _mapping_with_keys(
        report["primitives"],
        {"landlock", "seccomp_filter", "no_new_privs", "namespaces", "openat2"},
        "primitives",
    )
    landlock = _mapping_with_keys(
        primitives["landlock"], {"available", "abi"}, "primitives.landlock"
    )
    _required_boolean(landlock["available"], "primitives.landlock.available")
    _required_integer(landlock["abi"], "primitives.landlock.abi")
    for name in ("seccomp_filter", "no_new_privs", "openat2"):
        _required_boolean(primitives[name], f"primitives.{name}")
    namespaces = _mapping_with_keys(
        primitives["namespaces"],
        {"user", "mount", "pid", "ipc", "network"},
        "primitives.namespaces",
    )
    for name, namespace_available in namespaces.items():
        _required_boolean(namespace_available, f"primitives.namespaces.{name}")
    cgroup = _mapping_with_keys(
        report["cgroup"],
        {"cgroup_kill", "mount", "root", "relative_path", "controllers", "probe_transcript"},
        "cgroup",
    )
    _required_boolean(cgroup["cgroup_kill"], "cgroup.cgroup_kill")
    mount = _mapping_with_keys(cgroup["mount"], {"path", "filesystem"}, "cgroup.mount")
    _required_text(mount["path"], "cgroup.mount.path")
    _required_text(mount["filesystem"], "cgroup.mount.filesystem")
    _required_text(cgroup["root"], "cgroup.root")
    _required_text(cgroup["relative_path"], "cgroup.relative_path")
    _required_text_list(cgroup["controllers"], "cgroup.controllers")
    if not isinstance(cgroup["probe_transcript"], Mapping) or not cgroup["probe_transcript"]:
        raise ValueError("cgroup.probe_transcript is not a non-empty object")
    open_objects = _mapping_with_keys(
        report["open_objects"], {"bubblewrap", "launcher"}, "open_objects"
    )
    for name, opened in open_objects.items():
        _validate_open_object(opened, f"open_objects.{name}")
    digests = _mapping_with_keys(
        report["digests"], {"profile", "build_manifest", "artifact"}, "digests"
    )
    for name, digest in digests.items():
        _required_sha256(digest, f"digests.{name}")
    _mapping_with_keys(report["delegation"], {"broker", "existing_root", "source"}, "delegation")
    host_state = _mapping_with_keys(
        report["host_state"],
        {"lsm", "unprivileged_userns_sysctls", "boot_id", "machine_id", "delegation_identity"},
        "host_state",
    )
    _mapping_with_keys(
        host_state["lsm"],
        {"securityfs_lsm", "apparmor_policy_identity", "selinux_policy_identity"},
        "host_state.lsm",
    )
    sysctls = host_state["unprivileged_userns_sysctls"]
    if not isinstance(sysctls, Mapping) or set(sysctls) not in (
        {"user.max_user_namespaces"},
        {"kernel.unprivileged_userns_clone", "user.max_user_namespaces"},
    ):
        raise ValueError("host_state.unprivileged_userns_sysctls does not match its closed schema")
    delegation_identity = _mapping_with_keys(
        host_state["delegation_identity"],
        {"uid", "gid", "cgroup_root", "cgroup_relative_path", "source", "userns_state_source"},
        "host_state.delegation_identity",
    )
    for name in ("uid", "gid"):
        _required_integer(
            delegation_identity[name], f"host_state.delegation_identity.{name}"
        )
    return report


def _normalized_anchor(value: Any) -> Any:
    """Canonicalize only the schema-accepted SHA-256 representation."""

    if isinstance(value, str) and _SHA256.fullmatch(value) is not None:
        return value.removeprefix("sha256:")
    if isinstance(value, Mapping):
        return {key: _normalized_anchor(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalized_anchor(item) for item in value]
    return value


def _stale_anchor(report_state: Mapping[str, Any], live_state: Mapping[str, Any]) -> str | None:
    for field in ("boot_id", "machine_id", "lsm", "unprivileged_userns_sysctls"):
        if _normalized_anchor(report_state[field]) != _normalized_anchor(live_state[field]):
            return field
    report_identity = report_state["delegation_identity"]
    live_identity = live_state["delegation_identity"]
    for field in ("uid", "gid"):
        if report_identity[field] != live_identity[field]:
            return field
    return None


def _text_or_none(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    return value if isinstance(value, str) else None


def admit(
    records: Sequence[Any],
    keyring: Mapping[str, str],
) -> Admission:
    """Split records into evidence and rejections. Never raises on bad input."""

    evidence: list[Evidence] = []
    rejections: list[Rejection] = []
    qualifications: list[tuple[int, Evidence, Mapping[str, Any], Any]] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            rejections.append(
                Rejection(
                    index=index,
                    reason=RejectionReason.MALFORMED_RECORD,
                    detail="record is not a JSON object",
                    producer_id=None,
                    claim_id=None,
                )
            )
            continue

        producer_id = _text_or_none(record, "producer_id")
        claim_id = _text_or_none(record, "claim_id")

        def reject(reason: RejectionReason, detail: str, *, _index=index, _producer_id=producer_id, _claim_id=claim_id) -> None:
            rejections.append(
                Rejection(
                    index=_index,
                    reason=reason,
                    detail=detail,
                    producer_id=_producer_id,
                    claim_id=_claim_id,
                )
            )

        content = {k: v for k, v in record.items() if k != _SIGNATURE}
        if set(content) != set(SIGNED_FIELDS):
            unexpected = sorted(set(content) - set(SIGNED_FIELDS))
            missing = sorted(set(SIGNED_FIELDS) - set(content))
            parts = []
            if unexpected:
                parts.append(f"unexpected field(s): {', '.join(unexpected)}")
            if missing:
                parts.append(f"missing field(s): {', '.join(missing)}")
            # Checked before the signature: an extra field is outside the signed
            # bytes by construction, so verifying first would pass a record
            # carrying content nobody attested to.
            reject(RejectionReason.MALFORMED_RECORD, "; ".join(parts))
            continue

        qualification_report: Mapping[str, Any] | None = None
        try:
            if claim_id == _QUALIFICATION_CLAIM:
                qualification_report = _validate_qualification_report(content["suite_results"])
            elif content["suite_results"] is not None:
                validate_suite_results(content["suite_results"])
        except (ValueError, TypeError) as exc:
            reject(RejectionReason.MALFORMED_RECORD, str(exc))
            continue

        # Whether these fields can be encoded at all is a question about the
        # record's shape, so it is answered here rather than inferred from a
        # verify failure. `json.loads` accepts a lone surrogate and a bare NaN;
        # the canonical encoder accepts neither, and `verify_evidence` reports
        # every ValueError as False. Left to that path the record is accused of
        # BAD_SIGNATURE — "altered or signed by another key" — though no
        # verification ever took place: a false accusation against a named
        # producer, manufacturable by anyone who can write six characters into
        # the evidence file. Only a real verification failure may say that.
        try:
            signed_payload(content)
        except (ValueError, TypeError) as exc:
            reject(
                RejectionReason.MALFORMED_RECORD,
                f"record cannot be canonically encoded, so no signature over it "
                f"could be checked: {exc}",
            )
            continue

        if _SIGNATURE not in record:
            reject(
                RejectionReason.MISSING_SIGNATURE,
                "record carries no signature; unsigned records are not evidence",
            )
            continue

        if producer_id is None:
            reject(RejectionReason.MALFORMED_RECORD, "producer_id is not a string")
            continue

        public_key = keyring.get(producer_id)
        if public_key is None:
            # Never trusted by default. An unregistered producer is not a
            # producer.
            reject(
                RejectionReason.UNKNOWN_PRODUCER,
                f"no public key registered for producer {producer_id!r}",
            )
            continue

        signature = record[_SIGNATURE]
        if not is_signature(signature):
            reject(
                RejectionReason.MALFORMED_SIGNATURE,
                "signature is not an ed25519:<base64> value of the right length",
            )
            continue

        # Verified against the key registered for the producer the record
        # CLAIMS to be. Without that binding, a holder of any trusted key could
        # produce evidence under another identity and walk past no-self-approval.
        if not verify_evidence(content, signature, public_key):
            reject(
                RejectionReason.BAD_SIGNATURE,
                f"signature does not verify against the registered key for "
                f"{producer_id!r}; the record was altered or signed by another key",
            )
            continue

        try:
            admitted = Evidence(
                claim_id=content["claim_id"],
                subject_digest=content["subject_digest"],
                producer_id=content["producer_id"],
                command=content["command"],
                command_digest=content["command_digest"],
                executable_path=content["executable_path"],
                exit_code=content["exit_code"],
                suite_results=(
                    None if claim_id == _QUALIFICATION_CLAIM else content["suite_results"]
                ),
            )
        except (ValueError, TypeError) as exc:
            # A signature proves who wrote it, never that what they wrote is
            # well-formed.
            reject(RejectionReason.MALFORMED_RECORD, str(exc))
            continue

        if qualification_report is None:
            evidence.append(admitted)
        else:
            qualifications.append(
                (index, admitted, qualification_report["host_state"], reject)
            )

    if qualifications:
        host_states = [host_state for _, _, host_state, _ in qualifications]
        if any(host_state != host_states[0] for host_state in host_states[1:]):
            for _, _, _, reject in qualifications:
                reject(
                    RejectionReason.STALE_HOST_STATE,
                    "ambiguous host-qualification records disagree on host_state",
                )
        else:
            try:
                live_state = _read_live_durable_host_state()
                stale = _stale_anchor(host_states[0], live_state)
            except (KeyError, TypeError, ValueError, OSError, UnicodeError) as exc:
                for _, _, _, reject in qualifications:
                    reject(
                        RejectionReason.MALFORMED_RECORD,
                        f"cannot read live durable host state: {exc}",
                    )
            else:
                if stale is not None:
                    for _, _, _, reject in qualifications:
                        reject(
                            RejectionReason.STALE_HOST_STATE,
                            f"live durable host-state anchor differs: {stale}",
                        )
                else:
                    evidence.extend(admitted for _, admitted, _, _ in qualifications)

    return Admission(evidence=tuple(evidence), rejections=tuple(rejections))
