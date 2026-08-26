"""Approved-batch qualification planning and orchestration.

The legacy fanout path deliberately does not enter this module.  This owner
accepts only a closed, signed A/B/C batch and can produce only a
qualification-only artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, cast

from ranex.cli.repository import git, uncommitted_paths
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256, command_digest
from ranex.foundation.signing import public_key_for, sign_evidence
from ranex.foundation.specification_abc import (
    assert_abc_chain,
    payload_digest,
    validate_approval_envelope_bytes,
    validate_generated_artifact_manifest_bytes,
    validate_spec_packet_bytes,
)
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.admission import admit
from ranex.governed_execution.domain.specification_approval import (
    PolicyCapabilities,
    intersect_capabilities,
)
from ranex.policy.adapters.configuration.yaml.producer_keyring import load_keyring_text

_DEVELOPMENT_ROOT = Path(__file__).resolve().parents[4]
_KEYRING = "governance/producers.yaml"
_MAIN_REF = "refs/heads/main"
_HOST_ARGUMENTS = (
    "run",
    "--frozen",
    "python",
    "-m",
    "ranex.cli.host_confinement",
)
_PROVISIONING = (
    (
        "launcher-build",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--source",
        "native/ranex-worker-launcher/launcher.c",
        "--output",
        ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
    ),
    (
        "launcher-install",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--artifact",
        ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
        "--destination",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
    ),
    (
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report",
        ".local/ranex/qualification/strict-local-v1.json",
    ),
)
_ERROR_PRECEDENCE = (
    "E-BATCH-SCHEMA",
    "E-BATCH-PROTECTED-ARTIFACT",
    "E-BATCH-STALE-BASE",
    "E-BATCH-UNAPPROVED-ROW",
    "E-BATCH-INPUT-MISMATCH",
    "E-BATCH-POOL-EXCEEDS",
    "E-BATCH-SCOPE-OVERLAP",
    "E-BATCH-NETWORK-ESCAPE",
    "E-BATCH-CHILD-SURVIVOR",
    "E-BATCH-WORKTREE-RESIDUE",
    "E-BATCH-ORACLE-MISMATCH",
    "E-BATCH-PUBLICATION-REFUSED",
)


class BatchRefusal(ValueError):
    """Stable public refusal selected by the approved-batch contract."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _refuse(code: str, detail: str) -> NoReturn:
    raise BatchRefusal(code, detail)


def _uv_executable() -> str:
    executable = shutil.which("uv")
    if executable is None:
        _refuse("E-BATCH-ORACLE-MISMATCH", "uv executable is unavailable")
    return str(Path(executable).resolve())


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _event(value: dict[str, object]) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _git_text(root: Path, *arguments: str, code: str) -> str:
    result = git(root, *arguments)
    if result.returncode != 0:
        _refuse(code, result.stderr.strip() or "git query failed")
    return result.stdout.strip()


def _git_blob(root: Path, commit: str, relative: str, *, code: str) -> bytes:
    result = git(root, "show", f"{commit}:{relative}", text=False)
    if result.returncode != 0:
        _refuse(code, f"commit {commit} does not carry {relative}")
    return result.stdout


def _canonical_document(
    path: Path, *, code: str, require_canonical: bool = True
) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _refuse(code, f"cannot read canonical JSON at {path}: {exc}")
    if not isinstance(value, dict) or (require_canonical and raw != canonical_json_bytes(value)):
        _refuse(code, f"{path} is not a canonical JSON object")
    return raw, value


def _canonical_rows(path: Path) -> tuple[bytes, tuple[dict[str, Any], ...]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        _refuse("E-BATCH-SCHEMA", f"cannot read child rows: {exc}")
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(raw.splitlines(), start=1):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _refuse("E-BATCH-SCHEMA", f"child row {number} is invalid JSON: {exc}")
        if not isinstance(value, dict) or line != canonical_json_bytes(value):
            _refuse("E-BATCH-SCHEMA", f"child row {number} is not canonical")
        rows.append(value)
    if not rows or raw != b"\n".join(canonical_json_bytes(row) for row in rows) + b"\n":
        _refuse("E-BATCH-SCHEMA", "child request file is not canonical JSONL")
    return raw, tuple(rows)


def _protected_path(relative: str) -> Path:
    candidate = (_DEVELOPMENT_ROOT / relative).resolve()
    if not candidate.is_relative_to(_DEVELOPMENT_ROOT):
        _refuse("E-BATCH-PROTECTED-ARTIFACT", f"protected path escapes source: {relative}")
    return candidate


def _verify_protected(manifest: dict[str, Any]) -> dict[str, str]:
    try:
        protected = {row["path"]: row["digest"] for row in manifest["artifacts"]["protected"]}
    except (KeyError, TypeError) as exc:
        _refuse("E-BATCH-SCHEMA", f"manifest protected set is malformed: {exc}")
    for relative, expected in protected.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            _refuse("E-BATCH-SCHEMA", "manifest protected row is malformed")
        try:
            observed = _sha256(_protected_path(relative).read_bytes())
        except OSError as exc:
            _refuse("E-BATCH-PROTECTED-ARTIFACT", f"cannot read {relative}: {exc}")
        if observed != expected:
            _refuse("E-BATCH-PROTECTED-ARTIFACT", f"digest mismatch for {relative}")
    return protected


def _require_protected_input(path: Path, raw: bytes, protected: dict[str, str]) -> None:
    resolved = path.resolve()
    matches = [relative for relative in protected if _protected_path(relative) == resolved]
    if len(matches) != 1 or protected[matches[0]] != _sha256(raw):
        _refuse("E-BATCH-PROTECTED-ARTIFACT", f"unprotected input {path}")


def _validate_descriptor_rows(descriptor: dict[str, Any], rows: tuple[dict[str, Any], ...]) -> None:
    descriptor_fields = {
        "base_commit",
        "children",
        "domain",
        "maximum_pool",
        "oracle",
        "policy",
        "qualification_output",
        "retry_limit",
        "roles",
        "subject_digest",
        "version",
    }
    row_fields = {
        "attempt",
        "base_commit",
        "capability_request",
        "checks",
        "depends_on",
        "evidence",
        "invocation",
        "publication",
        "retry_limit",
        "runtime_input",
        "scope",
        "task_id",
        "timeout_seconds",
        "worktree",
    }
    if set(descriptor) != descriptor_fields or descriptor.get("version") != "approved-batch-v1":
        _refuse("E-BATCH-SCHEMA", "descriptor is not the closed approved-batch-v1 record")
    output = descriptor.get("qualification_output")
    oracle = descriptor.get("oracle")
    protected_oracles = oracle.get("protected_artifacts") if isinstance(oracle, dict) else None
    roles = descriptor.get("roles")
    children = descriptor.get("children")
    if (
        descriptor.get("domain") != "kernel"
        or descriptor.get("maximum_pool") != 2
        or descriptor.get("retry_limit") != 1
        or not isinstance(children, list)
        or len(children) < 3
        or len(set(children)) != len(children)
        or any(not isinstance(child, str) or not child for child in children)
        or not isinstance(output, dict)
        or set(output)
        != {
            "claim_id",
            "path",
            "producer_id",
            "publication_allowed",
            "schema",
            "signature_primitive",
        }
        or output.get("claim_id") != "approved-batch-qualified"
        or output.get("publication_allowed") is not False
        or output.get("signature_primitive") != "ranex-evidence-v4"
        or not isinstance(output.get("path"), str)
        or not isinstance(output.get("producer_id"), str)
        or not isinstance(output.get("schema"), dict)
        or set(output["schema"]) != {"digest", "path"}
        or not isinstance(oracle, dict)
        or set(oracle) != {"error_precedence", "goldens", "protected_artifacts"}
        or tuple(oracle.get("error_precedence", ())) != _ERROR_PRECEDENCE
        or not isinstance(oracle.get("goldens"), list)
        or len(oracle["goldens"]) < 2
        or not isinstance(protected_oracles, dict)
        or set(protected_oracles)
        != {"baseline", "expected_values", "negative_controls", "pseudocode_flow"}
        or not isinstance(roles, list)
        or len(roles) < 3
        or any(
            not isinstance(role, dict)
            or set(role) != {"key", "principal", "role"}
            or role.get("role") not in {"approver", "worker", "evaluator"}
            for role in roles
        )
    ):
        _refuse("E-BATCH-SCHEMA", "descriptor violates the closed approved-batch-v1 schema")
    if any(set(row) != row_fields for row in rows):
        _refuse("E-BATCH-SCHEMA", "child request is not the closed v1 record")
    try:
        parent = PolicyCapabilities.from_record(descriptor["policy"])
        for row in rows:
            child = PolicyCapabilities.from_record(row["capability_request"])
            if intersect_capabilities(parent, child, child=True) != child:
                _refuse("E-BATCH-SCHEMA", f"child capability expands policy: {row['task_id']}")
            invocation = row["invocation"]
            if (
                row["base_commit"] != descriptor["base_commit"]
                or row["worktree"] != "disposable"
                or row["publication"] is not False
                or row["retry_limit"] != descriptor["retry_limit"]
                or invocation["confinement"] != "strict-local"
                or invocation["argv"][:4] != ["python", "-m", "ranex.cli.main", "run"]
                or row["runtime_input"]["task_id"] != row["task_id"]
            ):
                _refuse("E-BATCH-SCHEMA", f"invalid child contract: {row['task_id']}")
    except BatchRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        message = str(exc)
        if message.startswith("E-BATCH-"):
            code, _, detail = message.partition(":")
            _refuse(code, detail.strip())
        _refuse("E-BATCH-SCHEMA", str(exc))


def _validate_inputs(root: Path, base: str, rows: tuple[dict[str, Any], ...]) -> None:
    for row in rows:
        task_id = row["task_id"]
        runtime = row["runtime_input"]
        expected = (
            f"governance/qualification/inputs/{task_id}/{runtime['flow_id']}/"
            f"attempt-{row['attempt']}"
        )
        relative = row["invocation"]["runtime_input_path"]
        if relative != expected:
            _refuse("E-BATCH-INPUT-MISMATCH", f"input path does not identify {task_id}")
        raw = _git_blob(root, base, relative + "/task.json", code="E-BATCH-INPUT-MISMATCH")
        try:
            record = json.loads(raw)
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            _refuse("E-BATCH-INPUT-MISMATCH", f"invalid committed input for {task_id}: {exc}")
        expected_record = {
            "attempt": row["attempt"],
            "delay_ms": runtime["delay_ms"],
            "flow_id": runtime["flow_id"],
            "mode": runtime["mode"],
            "task_id": task_id,
            "version": "slice036-child-input-v2",
        }
        if raw != canonical_json_bytes(record) or record != expected_record:
            _refuse("E-BATCH-INPUT-MISMATCH", f"committed input disagrees for {task_id}")


def _path_prefix(left: str, right: str) -> bool:
    return left == right or right.startswith(left.rstrip("/") + "/")


def _validate_sibling_scopes(rows: tuple[dict[str, Any], ...]) -> None:
    flow_ids = tuple(dict.fromkeys(row["runtime_input"]["flow_id"] for row in rows))
    for flow_id in flow_ids:
        flow_rows = [row for row in rows if row["runtime_input"]["flow_id"] == flow_id]
        for index, left_row in enumerate(flow_rows):
            left_id = left_row["task_id"]
            left = left_row["scope"]
            for right_row in flow_rows[index + 1 :]:
                if right_row["depends_on"] == left_row["depends_on"]:
                    right_id = right_row["task_id"]
                    right = right_row["scope"]
                    shared_actions = set(left["actions"]) & set(right["actions"])
                    overlaps = any(
                        _path_prefix(a, b) or _path_prefix(b, a)
                        for a in left["roots"]
                        for b in right["roots"]
                    )
                    if shared_actions and overlaps:
                        _refuse(
                            "E-BATCH-SCOPE-OVERLAP",
                            f"siblings {left_id} and {right_id} overlap",
                        )


def _worktree_count(root: Path) -> int:
    output = _git_text(root, "worktree", "list", "--porcelain", code="E-BATCH-WORKTREE-RESIDUE")
    return sum(line.startswith("worktree ") for line in output.splitlines())


@dataclass(frozen=True, slots=True)
class _ChildOutcome:
    task_id: str
    evidence: bytes
    record: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _PreparedChild:
    task_id: str
    worktree: Path
    row: dict[str, Any]


def _provision_child(root: Path, base: str, flow_id: str, row: dict[str, Any]) -> _PreparedChild:
    task_id = row["task_id"]
    child = root.parent / flow_id / "children" / task_id / f"attempt-{row['attempt']}"
    created = git(root, "worktree", "add", "--quiet", "--detach", str(child), base)
    if created.returncode != 0:
        _refuse(
            "E-BATCH-WORKTREE-RESIDUE", f"cannot create child worktree: {created.stderr.strip()}"
        )
    try:
        if uncommitted_paths(child):
            _refuse("E-BATCH-WORKTREE-RESIDUE", f"child worktree is not initially clean: {task_id}")
        environment = dict(os.environ)
        for arguments in _PROVISIONING:
            completed = subprocess.run(
                [_uv_executable(), *_HOST_ARGUMENTS, *arguments],
                cwd=child,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                _refuse(
                    "E-BATCH-ORACLE-MISMATCH",
                    "child provisioning failed: "
                    + "\n".join(
                        part
                        for part in (completed.stdout.strip(), completed.stderr.strip())
                        if part
                    ),
                )
        return _PreparedChild(task_id, child, row)
    except OSError as exc:
        _refuse("E-BATCH-ORACLE-MISMATCH", f"child provisioning failed: {exc}")


def _execute_child(prepared: _PreparedChild) -> _ChildOutcome:
    task_id = prepared.task_id
    child = prepared.worktree
    row = prepared.row
    try:
        environment = dict(os.environ)
        completed = subprocess.run(
            [_uv_executable(), "run", "--frozen", *row["invocation"]["argv"]],
            cwd=child,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        mode = row["runtime_input"]["mode"]
        flow_id = row["runtime_input"]["flow_id"]
        marker = "RANEX-BATCH-RESULT "
        result_lines = [line for line in completed.stderr.splitlines() if line.startswith(marker)]
        try:
            runtime_result = json.loads(result_lines[0][len(marker) :])
        except (IndexError, json.JSONDecodeError) as exc:
            _refuse("E-BATCH-ORACLE-MISMATCH", f"child runtime result is absent: {task_id}: {exc}")
        if completed.returncode == 91:
            _refuse("E-BATCH-NETWORK-ESCAPE", f"network control escaped for {task_id}")
        if completed.returncode != 0:
            if (
                flow_id == "oracle-mismatch-control"
                and completed.returncode == 92
                and runtime_result == {"exit_code": 92}
            ):
                _refuse(
                    "E-BATCH-ORACLE-MISMATCH",
                    f"child {task_id} exited 92 before emitting the oracle result",
                )
            detail = completed.stderr.strip() or "no stderr"
            _refuse(
                "E-BATCH-ORACLE-MISMATCH",
                f"child {task_id} exited {completed.returncode}: {detail}",
            )
        evidence = completed.stdout.encode("utf-8")
        records = json.loads(evidence)
        if not isinstance(records, list) or len(records) != 1 or not isinstance(records[0], dict):
            _refuse("E-BATCH-ORACLE-MISMATCH", f"child evidence is not singular: {task_id}")
        expected_result = {
            "attempt": row["attempt"],
            "flow_id": row["runtime_input"]["flow_id"],
            "network": "denied",
            "pid": None,
            "task_id": task_id,
            "value": "ok",
        }
        if not isinstance(runtime_result, dict) or set(runtime_result) != set(expected_result):
            _refuse("E-BATCH-ORACLE-MISMATCH", f"child runtime result is malformed: {task_id}")
        if mode == "survivor":
            without_pid = {name: value for name, value in expected_result.items() if name != "pid"}
            if (
                {name: runtime_result[name] for name in without_pid} != without_pid
                or type(runtime_result["pid"]) is not int
                or runtime_result["pid"] <= 0
            ):
                _refuse("E-BATCH-ORACLE-MISMATCH", f"survivor control was not observed: {task_id}")
            _refuse(
                "E-BATCH-CHILD-SURVIVOR",
                f"child {task_id} emitted survivor pid {runtime_result['pid']}",
            )
        if mode == "oracle-mismatch":
            if runtime_result != {**expected_result, "value": "oracle-mismatch"}:
                _refuse("E-BATCH-ORACLE-MISMATCH", f"oracle control was not observed: {task_id}")
            _refuse("E-BATCH-ORACLE-MISMATCH", f"child oracle disagreed for {task_id}")
        if runtime_result != expected_result:
            _refuse("E-BATCH-ORACLE-MISMATCH", f"child result disagreed for {task_id}")
        return _ChildOutcome(task_id, evidence, records[0])
    except OSError as exc:
        _refuse("E-BATCH-ORACLE-MISMATCH", f"child execution failed: {exc}")


def _remove_children(root: Path, paths: list[Path]) -> None:
    for child in paths:
        if child.exists():
            git(root, "worktree", "remove", "--force", str(child))
    git(root, "worktree", "prune")
    for flow in sorted({child.parents[2] for child in paths}, reverse=True):
        shutil.rmtree(flow, ignore_errors=True)


@dataclass(frozen=True, slots=True)
class BatchQualificationRecord:
    identities: dict[str, str]
    child_results_digest: str
    producer_id: str

    def as_record(self) -> dict[str, object]:
        values: dict[str, object] = {
            **self.identities,
            "batch_digest": "sha256:" + canonical_sha256(self.identities),
            "child_results_digest": self.child_results_digest,
            "producer_id": self.producer_id,
            "publication_allowed": False,
            "type": "batch-qualified",
        }
        return values


@dataclass(frozen=True, slots=True)
class QualificationResult:
    lines: tuple[str, ...]


def qualify_batch(
    *,
    spec_packet: Path,
    artifact_manifest: Path,
    approval_envelope: Path,
    descriptor_path: Path,
    tasks_path: Path,
    target: Path,
    journal_path: Path,
    outcome_dir: Path,
    pool: int,
    signed_command: tuple[str, ...],
    private_key: str,
    subject_digest: str,
) -> QualificationResult:
    """Execute both signed flows and commit one qualification-only result."""

    try:
        a_raw = spec_packet.read_bytes()
        b_raw = artifact_manifest.read_bytes()
        c_raw = approval_envelope.read_bytes()
        a = validate_spec_packet_bytes(a_raw)
        b = validate_generated_artifact_manifest_bytes(b_raw, spec_packet=a)
        c = validate_approval_envelope_bytes(c_raw)
        assert_abc_chain(a, b, c)
        descriptor_raw, descriptor = _canonical_document(
            descriptor_path, code="E-BATCH-SCHEMA", require_canonical=False
        )
        rows_raw, rows = _canonical_rows(tasks_path)
        _validate_descriptor_rows(descriptor, rows)
    except BatchRefusal:
        raise
    except (OSError, ValueError, TypeError, KeyError) as exc:
        _refuse("E-BATCH-SCHEMA", str(exc))

    protected = _verify_protected(b)
    _require_protected_input(descriptor_path, descriptor_raw, protected)
    _require_protected_input(tasks_path, rows_raw, protected)

    base = descriptor["base_commit"]
    payload = cast(dict[str, object], c["payload"])
    target = target.resolve()
    journal_path = journal_path.resolve()
    if (
        _git_text(target, "rev-parse", "--verify", _MAIN_REF, code="E-BATCH-STALE-BASE") != base
        or _git_text(target, "rev-parse", "--verify", "HEAD", code="E-BATCH-STALE-BASE") != base
        or descriptor["subject_digest"] != subject_digest
        or payload["base_digest"] != subject_digest
        or payload["subject_digest"] != subject_digest
    ):
        _refuse("E-BATCH-STALE-BASE", "signed base, subject, HEAD, or refs/heads/main moved")
    expected_head = cast(str | None, payload["journal_predecessor"])
    if journal_path.exists():
        journal = Journal(journal_path)
        if not journal.verify():
            _refuse("E-BATCH-STALE-BASE", "journal hash chain is invalid")
        if journal.head() != expected_head:
            _refuse("E-BATCH-STALE-BASE", "journal predecessor changed")
    elif expected_head is not None:
        _refuse("E-BATCH-STALE-BASE", "approved journal predecessor is absent")

    keyring_raw = _git_blob(target, base, _KEYRING, code="E-BATCH-STALE-BASE")
    keyring = load_keyring_text(keyring_raw.decode("utf-8"), f"{base}:{_KEYRING}")
    producer = descriptor["qualification_output"]["producer_id"]
    role_keys = [
        role["key"]
        for role in descriptor["roles"]
        if role["principal"] == producer and role["role"] == "approver"
    ]
    if (
        len(role_keys) != 1
        or keyring.get(producer) != role_keys[0]
        or public_key_for(private_key) != role_keys[0]
    ):
        _refuse("E-BATCH-STALE-BASE", "committed producer trust does not match approval")

    children = tuple(descriptor["children"])
    if set(row["task_id"] for row in rows) != set(children):
        _refuse("E-BATCH-UNAPPROVED-ROW", "child rows differ from approved descriptor")
    _validate_inputs(target, base, rows)
    if type(pool) is not int or pool < 1 or pool > descriptor["maximum_pool"]:
        _refuse("E-BATCH-POOL-EXCEEDS", f"pool {pool} exceeds {descriptor['maximum_pool']}")
    _validate_sibling_scopes(rows)
    try:
        plan = plan_qualification(descriptor, rows)
    except ValueError as exc:
        message = str(exc)
        if message.startswith("E-BATCH-"):
            code, _, detail = message.partition(":")
            _refuse(code, detail.strip())
        _refuse("E-BATCH-SCHEMA", message)
    if _worktree_count(target) != 1:
        _refuse("E-BATCH-WORKTREE-RESIDUE", "governed repository has an unrelated worktree")
    dirty = uncommitted_paths(target, ignoring=target / "governance/journal.sqlite3")
    if dirty:
        _refuse("E-BATCH-WORKTREE-RESIDUE", f"governed worktree is dirty: {', '.join(dirty)}")

    by_key = {(row["runtime_input"]["flow_id"], row["task_id"]): row for row in rows}
    child_paths = [
        target.parent
        / flow.flow_id
        / "children"
        / task_id
        / f"attempt-{by_key[(flow.flow_id, task_id)]['attempt']}"
        for flow in plan.flows
        for task_id in children
    ]
    outcomes: dict[str, _ChildOutcome] = {}
    lines = [
        _event(
            {
                "base_commit": base,
                "event": "batch.accepted",
                "maximum_pool": descriptor["maximum_pool"],
                "subject_digest": subject_digest,
            }
        )
    ]
    for row in sorted(
        rows,
        key=lambda item: (item["runtime_input"]["flow_id"], item["task_id"]),
    ):
        lines.append(
            _event(
                {
                    "event": "batch.child.sources",
                    "flow_id": row["runtime_input"]["flow_id"],
                    "input": "/ranex/input/task.json",
                    "runtime_input_path": row["invocation"]["runtime_input_path"],
                    "task_id": row["task_id"],
                    "toolchain": "/ranex/toolchain",
                    "toolchain_root": row["invocation"]["toolchain_root"],
                }
            )
        )
    try:
        for flow in plan.flows:
            first_ready = plan.ready_sets[0]
            lines.append(
                _event(
                    {"event": "batch.ready", "flow_id": flow.flow_id, "tasks": list(first_ready)}
                )
            )
            completion: list[str] = []
            prepared: dict[str, _PreparedChild] = {}
            with ThreadPoolExecutor(max_workers=min(pool, len(first_ready))) as executor:
                futures = {
                    executor.submit(
                        _provision_child,
                        target,
                        base,
                        flow.flow_id,
                        by_key[(flow.flow_id, task_id)],
                    ): task_id
                    for task_id in first_ready
                }
                for future in as_completed(futures):
                    child = future.result()
                    prepared[child.task_id] = child

            signed_first_order = tuple(
                task_id for task_id in flow.completion_order if task_id in first_ready
            )
            for task_id in signed_first_order:
                outcome = _execute_child(prepared[task_id])
                completion.append(outcome.task_id)
                outcomes[outcome.task_id] = outcome

            joined = plan.ready_sets[1]
            for task_id in joined:
                child = _provision_child(
                    target,
                    base,
                    flow.flow_id,
                    by_key[(flow.flow_id, task_id)],
                )
                outcome = _execute_child(child)
                completion.append(outcome.task_id)
                outcomes[outcome.task_id] = outcome
            if tuple(completion) != flow.completion_order:
                _refuse("E-BATCH-ORACLE-MISMATCH", f"completion order disagreed for {flow.flow_id}")
            lines.append(
                _event(
                    {
                        "canonical_results": list(flow.canonical_results),
                        "completion_order": completion,
                        "event": "batch.completed",
                        "flow_id": flow.flow_id,
                    }
                )
            )
            lines.append(
                _event(
                    {
                        "event": "batch.join",
                        "flow_id": flow.flow_id,
                        "released": flow.join_released,
                        "satisfied_by": list(first_ready),
                    }
                )
            )
    finally:
        _remove_children(target, child_paths)
    if _worktree_count(target) != 1:
        _refuse("E-BATCH-WORKTREE-RESIDUE", "child worktree cleanup left residue")

    admitted_records = [outcomes[task_id].record for task_id in children]
    admission = admit(admitted_records, keyring)
    if admission.rejections or len(admission.evidence) != len(children):
        _refuse("E-BATCH-ORACLE-MISMATCH", "child evidence was not admitted")

    evidence_rows: list[dict[str, str]] = []
    evidence_writes: list[tuple[Path, bytes]] = []
    for task_id in children:
        relative = by_key[(plan.flows[-1].flow_id, task_id)]["evidence"][0]["path"]
        raw = outcomes[task_id].evidence
        digest = _sha256(raw)
        evidence_rows.append({"task_id": task_id, "evidence_digest": digest})
        evidence_writes.append((outcome_dir / relative, raw))
        lines.append(
            _event(
                {"digest": digest, "event": "batch.evidence", "path": relative, "task_id": task_id}
            )
        )
    child_results_digest = "sha256:" + canonical_sha256({"results": evidence_rows})
    identities = {
        "a_digest": payload_digest(a),
        "b_digest": payload_digest(b),
        "base_commit": base,
        "base_digest": subject_digest,
        "c_digest": payload_digest(payload),
        "child_requests_digest": _sha256(rows_raw),
        "descriptor_digest": _sha256(descriptor_raw),
    }
    record = BatchQualificationRecord(identities, child_results_digest, producer)
    journal_append = Journal(journal_path).append_if_head(expected_head, record)
    record_value = record.as_record()
    qualification_payload = {
        **identities,
        "batch_digest": record_value["batch_digest"],
        "child_results_digest": child_results_digest,
        "producer_id": producer,
        "publication_allowed": False,
        "qualification_journal": {
            "head": journal_append.head,
            "previous_head": journal_append.previous_head,
            "seq": journal_append.position,
        },
        "qualification_record_digest": "sha256:" + canonical_sha256(record_value),
        "version": "batch-qualification-payload-v1",
    }
    result_digests = sorted(record["confinement_result_digest"] for record in admitted_records)
    profile_digests = sorted(record["confinement_profile_digest"] for record in admitted_records)
    content = {
        "claim_id": descriptor["qualification_output"]["claim_id"],
        "command": shlex.join(signed_command),
        "command_digest": command_digest(signed_command),
        "confinement_profile_digest": "sha256:" + canonical_sha256({"profiles": profile_digests}),
        "confinement_result_digest": "sha256:" + canonical_sha256({"results": result_digests}),
        "executable_path": str(Path(sys.executable).resolve()),
        "exit_code": 0,
        "producer_id": producer,
        "subject_digest": subject_digest,
        "suite_results": {
            "counts": {
                "errors": 0,
                "failed": 0,
                "passed": len(children),
                "skipped": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "extra_count": 0,
            "manifest_digest": identities["descriptor_digest"],
            "missing": [],
            "non_passed": [],
            "outcome_digest": _sha256(canonical_json_bytes(qualification_payload)),
        },
    }
    artifact = {
        "attestation": {**content, "signature": sign_evidence(content, private_key)},
        "payload": qualification_payload,
        "version": "batch-qualification-v1",
    }
    artifact_raw = canonical_json_bytes(artifact)
    for destination, raw in evidence_writes:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    artifact_relative = descriptor["qualification_output"]["path"]
    artifact_path = outcome_dir / artifact_relative
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact_raw)
    lines.append(
        _event(
            {
                "digest": _sha256(artifact_raw),
                "event": "batch.qualification",
                "path": artifact_relative,
                "producer_id": producer,
            }
        )
    )
    lines.append(
        _event(
            {
                "event": "batch.qualified",
                "journal_head": journal_append.head,
                "journal_position": journal_append.position,
                "network": "denied",
                "publication": False,
                "residue": [],
            }
        )
    )
    return QualificationResult(tuple(lines))


def verify_publication_refusal(
    artifact_path: Path,
    *,
    governed: Path,
    journal_path: Path,
    candidate_repository: Path,
    candidate: str,
    target_ref: str = _MAIN_REF,
) -> NoReturn:
    """Verify an actual qualification through base/candidate/tip, then refuse.

    This function is intentionally read-only and is called before either
    legacy publication path constructs an intent or candidate journal row.
    """

    raw, artifact = _canonical_document(artifact_path, code="E-BATCH-PROTECTED-ARTIFACT")
    del raw
    if (
        set(artifact) != {"attestation", "payload", "version"}
        or artifact.get("version") != "batch-qualification-v1"
    ):
        _refuse("E-BATCH-SCHEMA", "qualification artifact is not closed v1")
    payload = artifact.get("payload")
    attestation = artifact.get("attestation")
    required_payload = {
        "a_digest",
        "b_digest",
        "base_commit",
        "base_digest",
        "batch_digest",
        "c_digest",
        "child_requests_digest",
        "child_results_digest",
        "descriptor_digest",
        "producer_id",
        "publication_allowed",
        "qualification_journal",
        "qualification_record_digest",
        "version",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) != required_payload
        or payload.get("version") != "batch-qualification-payload-v1"
        or payload.get("publication_allowed") is not False
        or not isinstance(attestation, dict)
    ):
        _refuse("E-BATCH-SCHEMA", "qualification payload is not closed v1")
    identities = {
        name: payload[name]
        for name in (
            "a_digest",
            "b_digest",
            "base_commit",
            "base_digest",
            "c_digest",
            "child_requests_digest",
            "descriptor_digest",
        )
    }
    if payload["batch_digest"] != "sha256:" + canonical_sha256(identities):
        _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification batch digest disagrees")

    evidence = []
    children_root = artifact_path.parent / "children"
    if children_root.is_dir():
        for path in sorted(children_root.glob("*/evidence.json")):
            evidence.append(
                {
                    "task_id": path.parent.name,
                    "evidence_digest": _sha256(path.read_bytes()),
                }
            )
    if not evidence or payload["child_results_digest"] != "sha256:" + canonical_sha256(
        {"results": evidence}
    ):
        _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualified child evidence disagrees")

    fact = payload.get("qualification_journal")
    if not isinstance(fact, dict) or set(fact) != {"head", "previous_head", "seq"}:
        _refuse("E-BATCH-SCHEMA", "qualification journal fact is malformed")
    if not journal_path.is_file() or not Journal(journal_path).verify():
        _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification journal is absent or invalid")
    connection = sqlite3.connect(f"{journal_path.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT record, prev_link, link FROM evaluations WHERE seq = ?",
            (fact["seq"],),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification journal row is absent")
    record = json.loads(row[0])
    if (
        fact != {"seq": fact["seq"], "previous_head": row[1], "head": row[2]}
        or row[2] != "sha256:" + canonical_sha256({"prev_link": row[1], "record": record})
        or payload["qualification_record_digest"] != "sha256:" + canonical_sha256(record)
        or any(
            record.get(name) != payload.get(name)
            for name in required_payload
            - {"qualification_journal", "qualification_record_digest", "version"}
        )
        or record.get("type") != "batch-qualified"
    ):
        _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification journal binding disagrees")

    base = payload["base_commit"]
    tip = _git_text(governed, "rev-parse", "--verify", target_ref, code="E-BATCH-STALE-BASE")
    snapshots = (
        _git_blob(governed, base, _KEYRING, code="E-BATCH-STALE-BASE"),
        _git_blob(candidate_repository, candidate, _KEYRING, code="E-BATCH-STALE-BASE"),
        _git_blob(governed, tip, _KEYRING, code="E-BATCH-STALE-BASE"),
    )
    if len(set(snapshots)) != 1:
        _refuse("E-BATCH-STALE-BASE", "base/candidate/tip keyrings differ")
    for ordinal, snapshot in enumerate(snapshots):
        keyring = load_keyring_text(snapshot.decode("utf-8"), f"publication-keyring-{ordinal}")
        admission = admit([attestation], keyring)
        if admission.rejections or len(admission.evidence) != 1:
            _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification attestation is not admitted")
        admitted = admission.evidence[0]
        if (
            admitted.claim_id != "approved-batch-qualified"
            or admitted.subject_digest != payload["base_digest"]
            or admitted.producer_id != payload["producer_id"]
        ):
            _refuse("E-BATCH-PROTECTED-ARTIFACT", "qualification attestation identity disagrees")
    _refuse(
        "E-BATCH-PUBLICATION-REFUSED",
        "approved-batch child results are qualification-only",
    )


@dataclass(frozen=True, slots=True)
class QualificationFlow:
    flow_id: str
    completion_order: tuple[str, ...]
    canonical_results: tuple[str, ...]
    join_released: str


@dataclass(frozen=True, slots=True)
class QualificationPlan:
    ready_sets: tuple[tuple[str, ...], ...]
    flows: tuple[QualificationFlow, ...]


def plan_qualification(
    descriptor: dict[str, Any], rows: tuple[dict[str, Any], ...]
) -> QualificationPlan:
    """Derive deterministic ready sets and signed completion-order flows."""

    children = tuple(descriptor["children"])
    by_key = {(row["runtime_input"]["flow_id"], row["task_id"]): row for row in rows}
    flow_ids = tuple(dict.fromkeys(row["runtime_input"]["flow_id"] for row in rows))
    if (
        len(flow_ids) not in (1, 2)
        or len(by_key) != len(rows)
        or set(by_key) != {(flow_id, task_id) for flow_id in flow_ids for task_id in children}
    ):
        raise ValueError("E-BATCH-UNAPPROVED-ROW: child rows differ from descriptor")

    first_flow = flow_ids[0]
    by_task = {task_id: by_key[(first_flow, task_id)] for task_id in children}
    for flow_id in flow_ids[1:]:
        if any(
            by_key[(flow_id, task_id)]["depends_on"] != by_task[task_id]["depends_on"]
            for task_id in children
        ):
            raise ValueError("E-BATCH-SCHEMA: flow dependency graphs disagree")

    completed: set[str] = set()
    ready_sets: list[tuple[str, ...]] = []
    while len(completed) < len(children):
        ready = tuple(
            task_id
            for task_id in children
            if task_id not in completed and set(by_task[task_id]["depends_on"]).issubset(completed)
        )
        if not ready:
            raise ValueError("E-BATCH-SCHEMA: child dependency graph is cyclic")
        ready_sets.append(ready)
        completed.update(ready)

    flows: list[QualificationFlow] = []
    for flow_id in flow_ids:
        completion: list[str] = []
        for ready in ready_sets:
            completion.extend(
                sorted(
                    ready,
                    key=lambda task_id: (
                        by_key[(flow_id, task_id)]["runtime_input"]["delay_ms"],
                        children.index(task_id),
                    ),
                )
            )
        flows.append(
            QualificationFlow(
                flow_id,
                tuple(completion),
                children,
                ready_sets[-1][0],
            )
        )
    return QualificationPlan(tuple(ready_sets), tuple(flows))
