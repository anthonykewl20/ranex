"""Public task lifecycle tests; live workflow is separately qualified on Docker."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from test_http_observer_cli import PG, git, profile, setup

from ranex.foundation.signing import generate_keypair
from ranex.foundation.specification_abc import canonical_payload_bytes

REPO = Path(__file__).resolve().parents[2]


def invoke(*args, key=None):
    env = {k: v for k, v in os.environ.items() if k != "RANEX_SIGNING_KEY"}
    env["PYTHONPATH"] = str(REPO / "src")
    if key:
        env["RANEX_SIGNING_KEY"] = str(key)
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *map(str, args)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )


def prepared(tmp_path):
    root, _, _ = setup(tmp_path, profile())
    worker = dict(
        version="docker-worker-v1",
        image=PG,
        argv=["/bin/sh", "-c", 'printf "SELECT 2;\\n" > product/schema.sql'],
        product_roots=["product"],
        timeout_seconds=30,
        network=False,
        environment=[],
    )
    (root / "acceptance/worker.json").write_bytes(canonical_payload_bytes(worker))
    git(root, "add", ".")
    git(root, "commit", "-qm", "worker contract")
    frozen = tmp_path / "task-bundle"
    result = invoke(
        "specification",
        "freeze-probes",
        "--external-repository",
        root,
        "--spec-packet",
        tmp_path / "A.json",
        "--invocation",
        tmp_path / "argv.json",
        "--root",
        "acceptance",
        "--output",
        frozen,
    )
    assert result.returncode == 0, result.stderr
    private, _ = generate_keypair()
    key = tmp_path / "owner.key"
    key.write_text(private)
    key.chmod(0o600)
    return root, frozen, json.loads(result.stdout)["manifest_digest"], key


def test_task_requires_operator_signature_and_independent_bundle_pin(tmp_path):
    root, bundle, pin, key = prepared(tmp_path)
    state = tmp_path / "task-state"
    args = [
        "specification",
        "approve-task",
        "--external-repository",
        root,
        "--bundle",
        bundle,
        "--manifest-digest",
        pin,
        "--worker-profile",
        "acceptance/worker.json",
        "--state",
        state,
    ]
    unsigned = invoke(*args)
    assert unsigned.returncode == 2 and "E-TASK-" in unsigned.stderr
    assert not state.exists()
    wrong = args.copy()
    wrong[wrong.index(pin)] = "sha256:" + "0" * 64
    rejected = invoke(*wrong, key=key)
    assert rejected.returncode == 2 and "E-PROBE-PIN" in rejected.stderr
    assert not state.exists()
    approved = invoke(*args, key=key)
    assert approved.returncode == 0, approved.stdout + approved.stderr
    assert json.loads(approved.stdout)["status"] == "APPROVED"
    again = invoke(*args, key=key)
    assert again.returncode == 2
    assert "E-TASK-EXISTS" in again.stderr


def test_prove_refuses_missing_task_without_accepting_external_reports(tmp_path):
    result = invoke("prove", "--task", tmp_path / "absent")
    assert result.returncode == 2 and "E-TASK-" in result.stderr
    assert not (tmp_path / "absent").exists()


def test_build_refuses_missing_task_before_starting_worker(tmp_path):
    result = invoke("specification", "build-task", "--task", tmp_path / "absent")
    assert result.returncode == 2 and "E-TASK-" in result.stderr
    assert not (tmp_path / "absent").exists()


def test_land_refuses_missing_task_before_writing_target(tmp_path):
    result = invoke("specification", "land-task", "--task", tmp_path / "absent")
    assert result.returncode == 2 and "E-TASK-" in result.stderr


@pytest.mark.skipif(
    os.environ.get("RANEX_LIVE_TASK_EXPERIMENT") != "1",
    reason=(
        "ranex-context:live-task-experiment: requires RANEX_LIVE_TASK_EXPERIMENT=1 "
        "and local Docker images"
    ),
)
def test_real_task_build_misses_reapproval_and_exact_integration(tmp_path):
    output = tmp_path / "experiment"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO / "tools/dogfood/acceptance_task_proof.py"),
            "--output",
            str(output),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((output / "summary.json").read_bytes())
    assert summary["status"] == "EXPERIMENT-MATCH"
    assert summary["misses"] == [1, 2, 3]
    assert summary["fourth_attempt"] == "REFUSED"
    assert summary["reapproved_misses"] == 0


def test_reapproval_requires_new_revision_and_preserves_existing_authority(tmp_path):
    root, bundle, pin, key = prepared(tmp_path)
    state = tmp_path / "state"
    common = [
        "--external-repository",
        root,
        "--bundle",
        bundle,
        "--manifest-digest",
        pin,
        "--worker-profile",
        "acceptance/worker.json",
    ]
    approved = invoke("specification", "approve-task", *common, "--state", state, key=key)
    assert approved.returncode == 0, approved.stderr
    before = (state / "verdict.json").read_bytes()
    refused = invoke("specification", "reapprove-task", *common, "--task", state, key=key)
    assert refused.returncode == 2 and "E-TASK-REVISION" in refused.stderr
    assert (state / "verdict.json").read_bytes() == before
    assert not list(state.glob("revision-*"))


def test_modified_signed_anchor_refuses_before_observation(tmp_path):
    root, bundle, pin, key = prepared(tmp_path)
    state = tmp_path / "state"
    approved = invoke(
        "specification",
        "approve-task",
        "--external-repository",
        root,
        "--bundle",
        bundle,
        "--manifest-digest",
        pin,
        "--worker-profile",
        "acceptance/worker.json",
        "--state",
        state,
        key=key,
    )
    assert approved.returncode == 0, approved.stderr
    anchor = state / "verdict.json"
    value = json.loads(anchor.read_bytes())
    value["record"]["verdict"] = "PASS"
    anchor.chmod(0o600)
    anchor.write_bytes(canonical_payload_bytes(value))
    rejected = invoke("prove", "--task", state)
    assert rejected.returncode == 2 and "E-TASK-ANCHOR" in rejected.stderr
    assert not list(state.glob("observation-*"))


def test_worker_profile_refuses_mutable_image_and_scope_overlap():
    from ranex.cli.acceptance_task import module_digest, worker_profile

    digest = module_digest()
    assert digest.startswith("sha256:") and len(digest) == 71
    good = dict(
        version="docker-worker-v1",
        image=PG,
        argv=["/bin/true"],
        product_roots=["product"],
        timeout_seconds=30,
        network=False,
        environment=[],
    )
    assert worker_profile(good, ["acceptance"])["image"] == PG
    with pytest.raises(ValueError, match="E-TASK-WORKER"):
        worker_profile({**good, "image": "postgres:latest"}, ["acceptance"])
    with pytest.raises(ValueError, match="E-TASK-SCOPE"):
        worker_profile({**good, "product_roots": ["acceptance"]}, ["acceptance"])
    assert hashlib.sha256(digest.encode()).digest()


def approved_task_state(tmp_path):
    root, bundle, pin, key = prepared(tmp_path)
    state = tmp_path / "approved-state"
    result = invoke(
        "specification", "approve-task", "--external-repository", root,
        "--bundle", bundle, "--manifest-digest", pin,
        "--worker-profile", "acceptance/worker.json", "--state", state, key=key,
    )
    assert result.returncode == 0, result.stderr
    return state


@pytest.mark.parametrize("reevaluate", [False, True])
def test_task_journal_receipts_never_claim_repository_history(tmp_path, reevaluate):
    from ranex.cli.acceptance_task import Record, Task
    from ranex.foundation.specification_abc import payload_digest
    from ranex.foundation.verdict_signing import PAYLOAD_TYPE
    from ranex.governed_execution.domain.verdict import evaluate
    from ranex.governed_execution.verdict_reader import ReadState, read_verdict

    state = approved_task_state(tmp_path)
    task = Task(state)
    evaluation = evaluate(
        task.gate, (), subject_digest=task.last_verdict["subject_digest"],
        catalog_digest=payload_digest(task.context["b"]), approver_id=task.payload["principal"],
    ) if reevaluate else None
    task.append(Record({"type": "controller-check", "c_digest": task.c_digest}), evaluation)
    reopened = Task(state)
    publication = json.loads((state / "verdict.json").read_bytes())
    content = publication["record"]
    assert publication["payload_type"] == PAYLOAD_TYPE
    assert content["journal_head"] == reopened.journal.head()
    assert content["observation_checkpoint"] is None
    assert content["history_verified"] is False
    result = read_verdict(
        state / "verdict.json", {"task-publisher": reopened.context["identities"]["publisher"]},
        subject_digest=content["subject_digest"], gate_id=content["gate_id"],
        catalog_digest=content["catalog_digest"], approver_id=content["approver_id"],
        repository_root=reopened.candidate,
    )
    assert result.state == ReadState.UNANCHORED


def test_task_refuses_journal_append_without_new_signed_anchor(tmp_path):
    from ranex.cli.acceptance_task import Record, Task

    state = approved_task_state(tmp_path)
    task = Task(state)
    task.journal.append(Record({"type": "unanchored-row"}))
    with pytest.raises(ValueError, match="E-TASK-ANCHOR: journal changed"):
        Task(state)


def test_task_refuses_signed_claim_of_repository_history(tmp_path):
    from ranex.cli.acceptance_task import Task
    from ranex.foundation.canonical import canonical_sha256
    from ranex.governed_execution.adapters.persistence.sqlite.observations import GENESIS
    from ranex.governed_execution.verdict_publication import publish_verdict

    state = approved_task_state(tmp_path)
    task = Task(state)
    content = {**task.last_verdict, "history_verified": True,
               "observation_checkpoint": {"log_id": str(task.candidate / "observations.sqlite3"),
                                          "head": GENESIS, "position": 0}}
    publish_verdict(
        state / "verdict.json", {**content, "record_digest": "sha256:" + canonical_sha256(content)},
        root=state, signer_id="task-publisher", private_key=(state / "publisher.key").read_text(),
    )
    with pytest.raises(ValueError, match="E-TASK-ANCHOR: task journal receipt cannot certify"):
        Task(state)
