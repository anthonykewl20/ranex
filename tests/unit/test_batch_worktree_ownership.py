"""Batch cleanup releases acquired worktrees, preserving all other state."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes, command_digest
from ranex.foundation.signing import CATALOG_ABSENT, ENVELOPE_TYPE, GATE_ABSENT, sign_evidence
from ranex.foundation.specification_abc import payload_digest, sign_approval_payload
from ranex.governed_execution.application import specification_batch as batch


def repository(tmp_path: Path) -> Path:
    root = tmp_path / "target"
    root.mkdir()
    for argv in (
        ("init", "-q"),
        ("-c", "user.name=Test", "-c", "user.email=test@ranex.invalid", "commit", "--allow-empty", "-qm", "base"),
    ):
        result = batch.git(root, *argv)
        assert result.returncode == 0, result.stderr
    return root


def test_cleanup_preserves_preexisting_flow_and_never_prunes(tmp_path, monkeypatch):
    root = repository(tmp_path)
    flow = tmp_path / "existing-flow"
    child = flow / "children" / "unrelated" / "attempt-0"
    child.mkdir(parents=True)
    sentinel = flow / "keep.txt"
    sentinel.write_text("preserved")
    calls = []
    monkeypatch.setattr(batch, "git", lambda *argv: calls.append(argv))

    # Predicted destinations do not confer ownership over existing state.
    with pytest.raises(batch.BatchRefusal, match="ownership"):
        batch._remove_children(root, [child])

    assert sentinel.read_text() == "preserved"
    assert child.is_dir()
    assert calls == []


def test_reserving_existing_flow_refuses_without_removing_it(tmp_path):
    root = repository(tmp_path)
    flow = tmp_path / "existing-flow"
    flow.mkdir()
    sentinel = flow / "keep.txt"
    sentinel.write_text("preserved")
    resources = batch._BatchResources()

    with pytest.raises(batch.BatchRefusal, match="E-BATCH-WORKTREE-RESIDUE"):
        resources.reserve(flow)
    batch._remove_children(root, resources)

    assert sentinel.read_text() == "preserved"


def test_partial_concurrent_provisioning_releases_both_acquisitions(tmp_path, monkeypatch):
    root = repository(tmp_path)
    resources = batch._BatchResources()
    resources.reserve(tmp_path / "owned-flow")
    # Run tiny real child processes instead of host provisioning services.
    monkeypatch.setattr(batch, "_uv_executable", lambda: sys.executable)
    monkeypatch.setattr(batch, "_HOST_ARGUMENTS", ())
    monkeypatch.setattr(batch, "_PROVISIONING", (("-c", "import pathlib; raise SystemExit(7 if pathlib.Path.cwd().parent.name == 'A' else 0)"),))
    unrelated = tmp_path / "unrelated-worktree"
    assert batch.git(root, "worktree", "add", "--quiet", "--detach", str(unrelated), "HEAD").returncode == 0
    sentinel = unrelated / "keep.txt"
    sentinel.write_text("preserved")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(batch._provision_child, root, "HEAD", "owned-flow", {"task_id": name, "attempt": 0}, resources=resources) for name in ("A", "B")]
        with pytest.raises(batch.BatchRefusal, match="E-BATCH-ORACLE-MISMATCH"):
            futures[0].result()
        assert futures[1].result().task_id == "B"
    assert batch._worktree_count(root) == 4

    batch._remove_children(root, resources)

    assert batch._worktree_count(root) == 2
    assert not (tmp_path / "owned-flow").exists()
    assert sentinel.read_text() == "preserved"


def test_cleanup_failure_reports_residue_and_preserves_recoverable_tree(tmp_path, monkeypatch):
    root = repository(tmp_path)
    resources = batch._BatchResources()
    resources.reserve(tmp_path / "owned-flow")
    monkeypatch.setattr(batch, "_uv_executable", lambda: sys.executable)
    monkeypatch.setattr(batch, "_HOST_ARGUMENTS", ())
    monkeypatch.setattr(batch, "_PROVISIONING", (("-c", "pass"),))
    prepared = batch._provision_child(root, "HEAD", "owned-flow", {"task_id": "A", "attempt": 0}, resources=resources)
    sentinel = prepared.worktree / "keep.txt"
    sentinel.write_text("recoverable")
    original_git = batch.git
    calls = []

    def failing_remove(repository, *argv, **kwargs):
        calls.append(argv)
        if argv[:2] == ("worktree", "remove"):
            return subprocess.CompletedProcess(argv, 1, "", "injected removal failure")
        return original_git(repository, *argv, **kwargs)

    monkeypatch.setattr(batch, "git", failing_remove)
    with pytest.raises(batch.BatchRefusal, match="E-BATCH-WORKTREE-RESIDUE"):
        batch._remove_children(root, resources)

    assert sentinel.read_text() == "recoverable"
    assert batch._worktree_count(root) == 2
    assert not any(argv[:2] == ("worktree", "prune") for argv in calls)


def qualification_case(tmp_path, monkeypatch, *, dependencies=None):
    """Real signed preflight; only committed snapshot and child commands are supplied."""
    root = repository(tmp_path)
    fixtures = Path(__file__).parents[1] / "contract/fixtures/specification"
    vectors = json.loads((fixtures / "approved-batch-v1-vectors.json").read_bytes())
    descriptor = json.loads((fixtures / "approved-batch-v1.json").read_bytes())
    rows = tuple(json.loads(line) for line in (fixtures / "approved-batch-child-requests-v1.jsonl").read_text().splitlines())
    if dependencies is not None:
        for row in rows:
            row["depends_on"] = dependencies[row["task_id"]]
    descriptor_path = tmp_path / "descriptor.json"
    tasks_path = tmp_path / "tasks.jsonl"
    descriptor_path.write_bytes(canonical_json_bytes(descriptor))
    tasks_path.write_bytes(b"\n".join(canonical_json_bytes(row) for row in rows) + b"\n")
    a = copy.deepcopy(vectors["triple"]["a"])
    b = copy.deepcopy(vectors["triple"]["b"])
    b["artifacts"]["protected"] = [{"path": path.name, "digest": batch._sha256(path.read_bytes())} for path in (descriptor_path, tasks_path)]
    payload = copy.deepcopy(vectors["triple"]["c_payload"])
    payload["b_digest"] = payload_digest(b)
    c = {"version": "approval-envelope-v1", "payload_type": "application/vnd.ranex.approval-envelope.v1+json", "payload": payload, "key_id": vectors["triple"]["key_id"], "signature": sign_approval_payload(payload, vectors["fixture_private_key"])}
    authority = []
    for name, value in (("a", a), ("b", b), ("c", c)):
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical_json_bytes(value))
        authority.append(path)
    original_git_text = batch._git_text
    monkeypatch.setattr(batch, "_git_text", lambda root, *argv, **kwargs: original_git_text(root, *argv, **kwargs) if argv[:2] == ("worktree", "list") else descriptor["base_commit"])
    keyring = f"producers:\n  owner: {vectors['triple']['key_id']}\n".encode()
    monkeypatch.setattr(batch, "_git_blob", lambda *args, **kwargs: keyring)
    monkeypatch.setattr(batch, "_protected_path", lambda relative: tmp_path / relative)
    monkeypatch.setattr(batch, "_validate_inputs", lambda *args: None)
    monkeypatch.setattr(batch, "_uv_executable", lambda: sys.executable)
    monkeypatch.setattr(batch, "_HOST_ARGUMENTS", ())
    monkeypatch.setattr(batch, "_PROVISIONING", (("-c", "pass"),))
    original_provision = batch._provision_child
    monkeypatch.setattr(batch, "_provision_child", lambda root, base, flow, row, **kwargs: original_provision(root, "HEAD", flow, row, **kwargs))

    def execute(prepared):
        content = {"envelope_type": ENVELOPE_TYPE, "gate_id": GATE_ABSENT, "catalog_digest": CATALOG_ABSENT, "claim_id": prepared.task_id, "command": "python", "command_digest": command_digest(("python",)), "executable_path": sys.executable, "exit_code": 0, "producer_id": "owner", "subject_digest": descriptor["subject_digest"], "suite_results": None, "confinement_profile_digest": "sha256:" + "a" * 64, "confinement_result_digest": "sha256:" + "b" * 64}
        record = {**content, "signature": sign_evidence(content, vectors["fixture_private_key"])}
        return batch._ChildOutcome(prepared.task_id, canonical_json_bytes([record]), record)

    monkeypatch.setattr(batch, "_execute_child", execute)
    return dict(spec_packet=authority[0], artifact_manifest=authority[1], approval_envelope=authority[2], descriptor_path=descriptor_path, tasks_path=tasks_path, target=root, journal_path=tmp_path / "journal.sqlite3", outcome_dir=tmp_path / "outcome", pool=2, signed_command=("qualification",), private_key=vectors["fixture_private_key"], subject_digest=descriptor["subject_digest"])


def test_qualification_preserves_primary_refusal_when_cleanup_also_fails(tmp_path, monkeypatch):
    arguments = qualification_case(tmp_path, monkeypatch)

    def fail_provision(*args, **kwargs):
        raise batch.BatchRefusal("E-BATCH-ORACLE-MISMATCH", "primary provisioning failure")

    def fail_cleanup(*args, **kwargs):
        raise batch.BatchRefusal("E-BATCH-WORKTREE-RESIDUE", "cleanup failure")

    monkeypatch.setattr(batch, "_provision_child", fail_provision)
    monkeypatch.setattr(batch, "_remove_children", fail_cleanup)
    with pytest.raises(batch.BatchRefusal) as refusal:
        batch.qualify_batch(**arguments)
    assert refusal.value.code == "E-BATCH-ORACLE-MISMATCH"
    assert "primary provisioning failure" in str(refusal.value)
    assert "cleanup failure" in str(refusal.value)


def test_qualification_accepts_and_preserves_unrelated_worktree(tmp_path, monkeypatch):
    arguments = qualification_case(tmp_path, monkeypatch)
    unrelated = tmp_path / "unrelated"
    assert batch.git(arguments["target"], "worktree", "add", "--quiet", "--detach", str(unrelated), "HEAD").returncode == 0
    sentinel = unrelated / "keep.txt"
    sentinel.write_text("preserved")

    result = batch.qualify_batch(**arguments)

    assert result.lines
    assert batch._worktree_count(arguments["target"]) == 2
    assert sentinel.read_text() == "preserved"


@pytest.mark.parametrize("topology", ["three-waves", "no-join", "partial-join"])
def test_unsupported_topology_refuses_before_allocating_or_writing(tmp_path, monkeypatch, topology):
    first, second, joined = ("SLICE-036-child-A", "SLICE-036-child-B", "SLICE-036-child-C")
    dependencies = {
        "three-waves": {first: [], second: [first], joined: [second]},
        "no-join": {first: [], second: [], joined: []},
        "partial-join": {first: [], second: [], joined: [first]},
    }[topology]
    arguments = qualification_case(tmp_path, monkeypatch, dependencies=dependencies)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    acquisitions = []
    original_reserve = batch._BatchResources.reserve

    def reserve(resources, path):
        acquisitions.append(path)
        return original_reserve(resources, path)

    monkeypatch.setattr(batch._BatchResources, "reserve", reserve)
    with pytest.raises(batch.BatchRefusal, match="E-BATCH-SCHEMA"):
        batch.qualify_batch(**arguments)

    assert acquisitions == []
    assert batch._worktree_count(arguments["target"]) == 1
    assert not arguments["journal_path"].exists()
    assert not arguments["outcome_dir"].exists()
    assert before == {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}


def test_child_refusal_preserves_original_runtime_failure(tmp_path, monkeypatch):
    row = {"invocation": {"argv": ["python", "-m", "ranex.cli.main", "run"]},
           "runtime_input": {"mode": "normal", "flow_id": "flow"}}
    prepared = batch._PreparedChild("child", tmp_path, row)
    monkeypatch.setattr(batch, "_uv_executable", lambda: "uv")
    monkeypatch.setattr(batch.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args, 2, "", "ERROR E-C18-RUNTIME-PROFILE-DRIFT"))
    with pytest.raises(batch.BatchRefusal, match="exited 2.*E-C18-RUNTIME-PROFILE-DRIFT"):
        batch._execute_child(prepared)


def test_child_missing_result_diagnostic_is_redacted_and_bounded(tmp_path, monkeypatch):
    row = {"invocation": {"argv": ["python", "-m", "ranex.cli.main", "run"]},
           "runtime_input": {"mode": "normal", "flow_id": "flow"}}
    prepared = batch._PreparedChild("child", tmp_path, row)
    secret = "fixture-diagnostic-token-0123456789"
    monkeypatch.setenv("RANEX_API_TOKEN", secret)
    stderr = "x" * 8192 + "\nERROR E-C18-RUNTIME-PROFILE-DRIFT " + secret
    monkeypatch.setattr(batch, "_uv_executable", lambda: "uv")
    monkeypatch.setattr(batch.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args, 2, "", stderr))
    with pytest.raises(batch.BatchRefusal) as refusal:
        batch._execute_child(prepared)
    detail = str(refusal.value)
    assert "E-C18-RUNTIME-PROFILE-DRIFT" in detail
    assert "[REDACTED:env:RANEX_API_TOKEN]" in detail
    assert secret not in detail
    assert "[ranex truncated:" in detail
    assert len(detail.encode()) < 4300
