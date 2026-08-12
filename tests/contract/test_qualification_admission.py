"""SLICE-019 — frozen revised host-qualification admission contract."""

from __future__ import annotations

import copy
import argparse
import json
import subprocess
from pathlib import Path

import pytest

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.foundation import approval, signing
from ranex.foundation.canonical import command_digest
from ranex.cli.main import EXIT_FAIL, cmd_task_judge, subject_digest_for
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain import admission
from ranex.governed_execution.domain.task import TaskDispatch
from ranex.governed_execution.domain.verdict import Claim, Gate, Verdict, evaluate

SUBJECT = "sha256:" + "a" * 64
QUALIFY_ARGV = (
    "python", "-m", "ranex.cli.host_confinement", "qualify",
    "--profile", "governance/confinement/strict-local-host-v1.json",
    "--artifact", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
    "--manifest", "governance/confinement/native-launcher-build-v1.json",
    "--report", ".local/ranex/qualification/strict-local-v1.json",
)
HOST_STATE = {
    "lsm": {
        "securityfs_lsm": "landlock,apparmor",
        "apparmor_policy_identity": {"status": "inactive"},
        "selinux_policy_identity": {"status": "inactive"},
    },
    "unprivileged_userns_sysctls": {
        "kernel.unprivileged_userns_clone": "1",
        "user.max_user_namespaces": "15000",
    },
    "boot_id": "11111111-2222-3333-4444-555555555555",
    "machine_id": "0123456789abcdef0123456789abcdef",
    "delegation_identity": {
        "uid": 1000,
        "gid": 1000,
        "cgroup_root": "/sys/fs/cgroup",
        "cgroup_relative_path": "/session.scope",
        "source": "direct",
        "userns_state_source": "qualification-host-probe",
    },
}
REPORT = {
    "schema": "ranex-strict-local-qualification-v1",
    "qualified": True,
    "refusal": None,
    "kernel": {"release": "6.12.0", "architecture": "x86_64"},
    "primitives": {
        "landlock": {"available": True, "abi": 6},
        "seccomp_filter": True,
        "no_new_privs": True,
        "namespaces": {"user": True},
        "openat2": True,
    },
    "cgroup": {"version": 2},
    "open_objects": {"bubblewrap": {}, "launcher": {}},
    "digests": {
        "profile": "sha256:" + "1" * 64,
        "build_manifest": "sha256:" + "2" * 64,
        "artifact": "sha256:" + "3" * 64,
    },
    "delegation": {"broker": None, "existing_root": None, "source": "direct"},
    "host_state": HOST_STATE,
}


@pytest.fixture()
def identity() -> tuple[str, str]:
    return signing.generate_keypair()


def raw_record(
    private: str,
    report: object = REPORT,
    *,
    producer: str = "qualifier",
    subject: str = SUBJECT,
) -> dict[str, object]:
    content: dict[str, object] = {
        "claim_id": "host-qualification",
        "command": " ".join(QUALIFY_ARGV),
        "command_digest": command_digest(QUALIFY_ARGV),
        "executable_path": "/usr/bin/python",
        "exit_code": 0,
        "producer_id": producer,
        "subject_digest": subject,
        "suite_results": report,
    }
    return {**content, "signature": signing.sign_evidence(content, private)}


def admit_with_live(monkeypatch: pytest.MonkeyPatch, records, public: str, live=HOST_STATE):
    monkeypatch.setattr(admission, "_read_live_durable_host_state", lambda: live)
    return admission.admit(records, {"qualifier": public})


def test_absent_report_leaves_host_qualification_missing_and_blocks() -> None:
    # Red independently of the autouse freeze: the real catalog does not carry
    # host-qualification until the implementer adds it.
    root = Path(__file__).resolve().parents[2]
    evaluator = build_gate_evaluator(
        (root / "governance/gates.yaml").read_bytes(),
        suite_manifest=(root / "governance/suite_manifest.json").read_bytes(),
    )
    result = evaluator.evaluate("landing", (), subject_digest=SUBJECT, approver_id="reviewer")
    assert result.verdict is Verdict.FAIL
    assert "host-qualification" in result.missing_claims


@pytest.mark.parametrize(
    ("report", "specific_detail"),
    (
        ({**REPORT, "schema": "ranex-strict-local-qualification-v2"}, "unknown host-qualification schema"),
        (
            {**REPORT, "host_state": {k: v for k, v in HOST_STATE.items() if k != "boot_id"}},
            "host_state does not match its closed schema",
        ),
    ),
    ids=("unknown-schema", "missing-required-host-fact"),
)
def test_unknown_schema_or_missing_host_fact_refuses(
    monkeypatch, identity, report, specific_detail: str
) -> None:
    private, public = identity
    result = admit_with_live(monkeypatch, [raw_record(private, report)], public)
    assert result.evidence == ()
    assert len(result.rejections) == 1
    assert result.rejections[0].reason is admission.RejectionReason.MALFORMED_RECORD
    # Red now: generic JUnit parsing refuses these bytes for the wrong reason.
    assert specific_detail in result.rejections[0].detail


def test_disagreeing_reports_refuse_as_ambiguity_not_newest_wins(monkeypatch, identity) -> None:
    private, public = identity
    changed_state = copy.deepcopy(HOST_STATE)
    changed_state["boot_id"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    changed = {**REPORT, "host_state": changed_state}
    result = admit_with_live(
        monkeypatch, [raw_record(private), raw_record(private, changed)], public
    )
    assert result.evidence == ()
    assert len(result.rejections) == 2
    assert all(
        rejection.reason is admission.RejectionReason.STALE_HOST_STATE
        for rejection in result.rejections
    )
    assert all("ambigu" in rejection.detail.lower() for rejection in result.rejections)


@pytest.mark.parametrize(
    "field", ("boot_id", "machine_id", "lsm", "unprivileged_userns_sysctls", "uid", "gid")
)
def test_genuine_report_refuses_when_a_live_durable_anchor_differs(
    monkeypatch, identity, field: str
) -> None:
    private, public = identity
    live = copy.deepcopy(HOST_STATE)
    if field in ("uid", "gid"):
        live["delegation_identity"][field] += 1
    elif field == "lsm":
        live[field]["securityfs_lsm"] = "selinux"
    elif field == "unprivileged_userns_sysctls":
        live[field]["user.max_user_namespaces"] = "0"
    else:
        live[field] = "live-host-has-different-bytes"
    result = admit_with_live(monkeypatch, [raw_record(private)], public, live)
    assert result.evidence == ()
    assert result.rejections[0].reason is admission.RejectionReason.STALE_HOST_STATE
    assert field in result.rejections[0].detail


def test_transient_host_state_differences_do_not_stale_evidence(monkeypatch, identity) -> None:
    private, public = identity
    live = copy.deepcopy(HOST_STATE)
    live["delegation_identity"].update(
        cgroup_root="/different", cgroup_relative_path="/different.scope",
        source="broker", userns_state_source="different-probe",
    )
    result = admit_with_live(monkeypatch, [raw_record(private)], public, live)
    assert result.rejections == ()
    assert result.evidence[0].suite_results is None


def test_producer_cannot_approve_its_own_qualification(monkeypatch, identity) -> None:
    private, public = identity
    admitted = admit_with_live(monkeypatch, [raw_record(private)], public)
    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(
            Claim(
                claim_id="host-qualification",
                command_digest=command_digest(QUALIFY_ARGV),
                results_required=False,
            ),
        ),
        blocking=True,
    )
    result = evaluate(
        gate, admitted.evidence, subject_digest=SUBJECT, approver_id="qualifier"
    )
    assert result.verdict is Verdict.FAIL
    assert result.reason == (
        "self-approval refused: qualifier produced evidence and approved it"
    )


def test_existing_evidence_domain_exact_fields_and_identity_bindings(identity) -> None:
    # Regression-only: the reused EVIDENCE_DOMAIN and exact fields already exist;
    # this freezes the owner-approved no-new-envelope constraint, not new behavior.
    private, public = identity
    record = raw_record(private)
    content = {k: v for k, v in record.items() if k != "signature"}
    assert signing.EVIDENCE_DOMAIN == b"ranex-evidence-v3\n"
    assert tuple(content) == signing.SIGNED_FIELDS
    assert signing.verify_evidence(content, record["signature"], public)
    for field in ("subject_digest", "producer_id"):
        altered = {**content, field: "altered"}
        assert not signing.verify_evidence(altered, record["signature"], public)
    with pytest.raises(ValueError):
        signing.signed_payload({**content, "extra": True})
    missing = dict(content)
    missing.pop("suite_results")
    with pytest.raises(ValueError):
        signing.signed_payload(missing)


def test_host_qualification_signature_does_not_verify_as_approval(identity) -> None:
    # Regression-only: approval-domain separation already exists and must survive
    # adding claim-specific admission.
    _, public = identity
    record = raw_record(identity[0])
    approval_content = {
        "candidate": "a" * 40, "subject": SUBJECT, "target_ref": "refs/heads/main",
        "tip": "b" * 40, "catalog_digest": "sha256:" + "c" * 64,
        "candidate_row_hash": "sha256:" + "d" * 64, "approver_id": "reviewer",
    }
    assert not approval.verify_approval(approval_content, record["signature"], public)


def test_cmd_task_judge_uses_shared_qualification_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The merge-candidate path preserves absence/refusal as a judged missing claim."""

    # Red now on the pinned shared-admission API before exercising both cases.
    assert admission.RejectionReason.STALE_HOST_STATE == "stale-host-state"

    qualification = "stale"
    repository = tmp_path / qualification
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "slice019@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "SLICE-019"],
        check=True,
    )
    private, public = signing.generate_keypair()
    governance = repository / "governance"
    governance.mkdir()
    (governance / "gates.yaml").write_text(
        """gates:
  - gate_id: landing
    rule_id: HOST_QUALIFIED
    blocking: true
    required_claims:
      - claim_id: host-qualification
        command: ["python", "-m", "ranex.cli.host_confinement", "qualify", "--profile", "governance/confinement/strict-local-host-v1.json", "--artifact", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher", "--manifest", "governance/confinement/native-launcher-build-v1.json", "--report", ".local/ranex/qualification/strict-local-v1.json"]
""",
        encoding="utf-8",
    )
    (governance / "producers.yaml").write_text(
        f"producers:\n  qualifier: {public}\n", encoding="utf-8"
    )
    (repository / "candidate.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "base"], check=True
    )
    base = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (repository / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "candidate.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "candidate"], check=True
    )
    candidate = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subject = subject_digest_for(repository, candidate)

    records: list[dict[str, object]] = []
    if qualification == "stale":
        records.append(raw_record(private, subject=subject))
        live = copy.deepcopy(HOST_STATE)
        live["boot_id"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        monkeypatch.setattr(admission, "_read_live_durable_host_state", lambda: live)
    evidence_path = governance / "evidence.json"
    evidence_path.write_text(json.dumps(records), encoding="utf-8")

    journal_path = tmp_path / f"{qualification}.sqlite3"
    Journal(journal_path).append(TaskDispatch("T-19", str(repository), base))
    result = cmd_task_judge(
        argparse.Namespace(
            task_id="T-19",
            emitted_worktree=str(repository),
            emitted_commit=candidate,
            gate="landing",
            gate_catalog="governance/gates.yaml",
            evidence="governance/evidence.json",
            producers="governance/producers.yaml",
            suite_manifest="governance/suite_manifest.json",
            journal=str(journal_path),
        )
    )
    candidates = [
        row for row in Journal(journal_path).entries() if row.get("type") == "task-candidate"
    ]
    assert result == EXIT_FAIL  # judged FAIL, not EXIT_USAGE
    assert candidates[-1]["missing_claims"] == ["host-qualification"]
