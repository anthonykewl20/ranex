import argparse
import json
import subprocess
from unittest.mock import patch

import pytest

import ranex.cli.main as cli
from ranex.bootstrap.composition import catalog_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskDispatch
from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate


@pytest.mark.parametrize("scenario", ["clean", "contradiction", "foreign-policy", "late-failure"])
def test_task_publication_obeys_current_kernel_verdict(
    tmp_path, monkeypatch, scenario, *, concurrent_writer=False,
):
    r = tmp_path
    repo = r / "subject"
    repo.mkdir()
    (repo / "governance").mkdir()

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Audit fixture")
    git("config", "user.email", "audit@example.invalid")
    keys = {n: generate_keypair() for n in ["worker1", "worker2", "reviewer"]}
    service_private, service_public = generate_keypair()
    checkpoint = r / "external-history.json"
    monkeypatch.setenv("RANEX_HISTORY_CHECKPOINT", str(checkpoint))
    cat = "gates:\n  - gate_id: landing\n    rule_id: RULE\n    blocking: true\n    required_claims:\n      - claim_id: tests\n        command: [/usr/bin/true]\n"
    (repo / "governance/gates.yaml").write_text(cat)
    (repo / "governance/producers.yaml").write_text(
        "producers:\n" + "".join(f"  {n}: {pub}\n" for n, (_, pub) in keys.items())
        + f"verdict_signer:\n  id: kernel-verdict-signer\n  public_key: {service_public}\n"
    )
    (repo / ".gitignore").write_text("governance/*.sqlite3\ngovernance/evidence.json\n")
    (repo / "work.txt").write_text("base\n")
    git("add", ".")
    git("commit", "-qm", "base fixture")
    base = git("rev-parse", "HEAD")
    git("switch", "-qc", "candidate")
    (repo / "work.txt").write_text("candidate\n")
    git("add", "work.txt")
    git("commit", "-qm", "candidate fixture")
    candidate = git("rev-parse", "HEAD")
    subject = cli.subject_digest_for(repo, candidate)
    cd = command_digest(["/usr/bin/true"])
    catalog = catalog_digest_for(cat.encode())
    evidence = repo / "governance/evidence.json"
    cli.bootstrap_history(evidence, checkpoint, service_private, service_public, repo)
    history = dict(repository_root=repo, history_public_key=service_public,
                   history_private_key=service_private, history_checkpoint_path=checkpoint)
    journal = Journal(repo / "governance/journal.sqlite3")
    journal.append(TaskDispatch(scenario, str(repo), base))
    for producer, code in (
        [("worker1", 0), ("worker2", 1)] if scenario == "contradiction" else [("worker1", 0)]
    ):
        content = {
            "claim_id": "tests",
            "command": "/usr/bin/true",
            "command_digest": cd,
            "executable_path": "/usr/bin/true",
            "exit_code": code,
            "producer_id": producer,
            "subject_digest": subject,
            "suite_results": None,
            "confinement_result_digest": "sha256:" + "a" * 64,
            "confinement_profile_digest": "sha256:" + "a" * 64,
            "envelope_type": "ranex-evidence-envelope-v1",
            "gate_id": "foreign" if scenario == "foreign-policy" else "landing",
            "catalog_digest": "sha256:" + "b" * 64 if scenario == "foreign-policy" else catalog,
        }
        cli.record_evidence(
            evidence, {**content, "signature": sign_evidence(content, keys[producer][0])}, **history
        )
    args = argparse.Namespace(
        batch_qualification=None,
        emitted_worktree=str(repo),
        journal=str(journal._path),
        task_id=scenario,
        emitted_commit=candidate,
        gate_catalog="governance/gates.yaml",
        producers="governance/producers.yaml",
        evidence="governance/evidence.json",
        gate="landing",
        suite_manifest="governance/suite_manifest.json",
    )
    code = cli.cmd_task_judge(args)
    row = next(x for x in reversed(journal.entries()) if x.get("type") == "task-candidate")
    if scenario == "late-failure":
        content["exit_code"] = 1
        cli.record_evidence(
            evidence, {**content, "signature": sign_evidence(content, keys["worker1"][0])}, **history
        )
    ad = cli.admit_records(
        evidence,
        {n: pub for n, (_, pub) in keys.items()},
        repo,
        gate_id="landing",
        catalog_digest=catalog,
        history_public_key=service_public,
    )
    result = evaluate(
        Gate("landing", "RULE", (Claim("tests", cd),), True),
        ad.evidence,
        subject_digest=subject,
        approver_id="reviewer",
    )
    assert result.verdict == ("PASS" if scenario == "clean" else "FAIL")
    assert code == (0 if scenario in ("clean", "late-failure") else 1)
    assert bool(row["missing_claims"]) == (scenario not in ("clean", "late-failure"))
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": base,
        "catalog_digest": catalog,
        "candidate_row_hash": candidate_row_hash(row),
        "approver_id": "reviewer",
    }
    approval = r / "approval.json"
    approval.write_text(
        json.dumps({**envelope, "signature": sign_approval(envelope, keys["reviewer"][0])})
    )
    merge = argparse.Namespace(
        batch_qualification=None,
        journal=str(journal._path),
        approval=str(approval),
        task_id=scenario,
        candidate=candidate,
        target_ref="refs/heads/main",
        evidence="governance/evidence.json",
    )
    child = None
    if concurrent_writer:
        import multiprocessing

        ctx = multiprocessing.get_context("fork")
        started, finished = ctx.Event(), ctx.Event()
        outcome = ctx.Queue()
        failure = {**content, "exit_code": 1}
        failure["signature"] = sign_evidence(failure, keys["worker1"][0])

        def append_failure():
            started.set()
            cli.record_evidence(evidence, failure, **history)
            outcome.put(git("rev-parse", "main"))
            finished.set()

        original_git = cli.git

        def interleaved_git(root, *argv, **kwargs):
            nonlocal child
            if argv and argv[0] == "update-ref" and child is None:
                child = ctx.Process(target=append_failure)
                child.start()
                assert started.wait(timeout=5)
                assert not finished.wait(timeout=0.2), "signed FAIL committed before publication CAS"
            return original_git(root, *argv, **kwargs)

        monkeypatch.setattr(cli, "git", interleaved_git)
    try:
        with patch.object(cli, "governed_repository_root", return_value=repo):
            merge_code = cli.cmd_task_merge(merge)
        if concurrent_writer:
            assert child is not None
            child.join(timeout=5)
            assert child.exitcode == 0
            assert finished.is_set()
            assert outcome.get(timeout=2) == candidate
            current = cli.admit_records(evidence, {n: pub for n, (_, pub) in keys.items()},
                                        repo, gate_id="landing", catalog_digest=catalog,
                                        history_public_key=service_public)
            assert evaluate(Gate("landing", "RULE", (Claim("tests", cd),), True),
                            current.evidence, subject_digest=subject,
                            approver_id="reviewer").verdict == "FAIL"
    finally:
        if child is not None and child.is_alive():
            child.terminate()
            child.join(timeout=5)
        if concurrent_writer:
            outcome.close()
            outcome.join_thread()
    assert merge_code == (0 if scenario == "clean" else 1)
    assert git("rev-parse", "main") == (candidate if scenario == "clean" else base)


def test_task_merge_serializes_signed_history_through_ref_cas(tmp_path, monkeypatch):
    test_task_publication_obeys_current_kernel_verdict(
        tmp_path, monkeypatch, "clean", concurrent_writer=True,
    )
