from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskCandidate

TARGET_REF = "refs/heads/main"
CATALOG = (
    b"gates:\n"
    b"  - gate_id: landing\n"
    b"    rule_id: TESTS_EXECUTED\n"
    b"    blocking: true\n"
    b"    required_claims:\n"
    b"      - claim_id: tests-executed\n"
    b"        command: [pytest, -q]\n"
)


def git(repo: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def invoke(repo: Path, argv: list[str]) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        return main(argv)


@dataclass
class MergeScenario:
    repo: Path
    tip: str
    candidate: str
    subject: str
    approval: Path
    candidate_record: dict[str, object]
    worker_private: str
    approver_private: str
    evidence_body: dict[str, object]

    @classmethod
    def create(
        cls,
        root: Path,
        *,
        history: str = "linear",
        commits: int = 1,
        missing_claims: tuple[str, ...] = (),
        append_candidate: bool = True,
        catalog_change: bool = False,
        keyring_change: bool = False,
    ) -> MergeScenario:
        repo = root / "governed"
        git(root, "init", "-q", str(repo))
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test")
        worker_private, worker_public = generate_keypair()
        approver_private, approver_public = generate_keypair()
        governance = repo / "governance"
        governance.mkdir()
        (governance / "gates.yaml").write_bytes(CATALOG)
        (governance / "producers.yaml").write_text(
            f"producers:\n  worker: {worker_public}\n  owner: {approver_public}\n",
            encoding="utf-8",
        )
        (repo / ".gitignore").write_text(
            "governance/evidence.json\ngovernance/journal.sqlite3\n",
            encoding="utf-8",
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        git(repo, "branch", "-M", "main")
        tip = git(repo, "rev-parse", TARGET_REF)

        if history in {"linear", "orphan"}:
            for number in range(commits):
                (repo / f"candidate-{number}.txt").write_text(
                    f"candidate {number}\n", encoding="utf-8"
                )
                git(repo, "add", f"candidate-{number}.txt")
                git(repo, "commit", "-q", "-m", f"candidate {number}")
            candidate = git(repo, "rev-parse", "HEAD")
            if history == "orphan":
                candidate = git(
                    repo,
                    "commit-tree",
                    git(repo, "rev-parse", f"{candidate}^{{tree}}"),
                    "-m",
                    "orphan",
                )
        elif history == "merge":
            (repo / "left.txt").write_text("left\n", encoding="utf-8")
            git(repo, "add", "left.txt")
            git(repo, "commit", "-q", "-m", "left")
            git(repo, "checkout", "-q", "-b", "side", tip)
            (repo / "right.txt").write_text("right\n", encoding="utf-8")
            git(repo, "add", "right.txt")
            git(repo, "commit", "-q", "-m", "right")
            git(repo, "checkout", "-q", "main")
            git(repo, "merge", "-q", "--no-ff", "side", "-m", "merge")
            candidate = git(repo, "rev-parse", "HEAD")
        elif history == "equal":
            candidate = tip
        elif history == "same-tree":
            candidate = git(
                repo,
                "commit-tree",
                git(repo, "rev-parse", f"{tip}^{{tree}}"),
                "-p",
                tip,
                "-m",
                "same tree",
            )
        elif history == "orphan-merge":
            (repo / "orphan.txt").write_text("orphan\n", encoding="utf-8")
            git(repo, "add", "orphan.txt")
            tree = git(repo, "write-tree")
            left = git(repo, "commit-tree", tree, "-m", "orphan left")
            right = git(repo, "commit-tree", tree, "-m", "orphan right")
            candidate = git(
                repo,
                "commit-tree",
                tree,
                "-p",
                left,
                "-p",
                right,
                "-m",
                "orphan merge",
            )
        else:
            raise ValueError(f"unknown history: {history}")

        if catalog_change or keyring_change:
            git(repo, "update-ref", TARGET_REF, candidate)
            git(repo, "reset", "--hard", "-q", candidate)
            if catalog_change:
                (governance / "gates.yaml").write_bytes(CATALOG + b"\n")
            if keyring_change:
                _, extra_public = generate_keypair()
                with (governance / "producers.yaml").open("a", encoding="utf-8") as stream:
                    stream.write(f"  extra: {extra_public}\n")
            git(repo, "add", "governance")
            git(repo, "commit", "-q", "-m", "candidate policy change")
            candidate = git(repo, "rev-parse", "HEAD")

        git(repo, "update-ref", TARGET_REF, tip)
        subject = subject_digest_for(repo, candidate)
        evidence_body: dict[str, object] = {
            "claim_id": "tests-executed",
            "command": "pytest -q",
            "command_digest": command_digest(["pytest", "-q"]),
            "executable_path": "/usr/bin/pytest",
            "exit_code": 0,
            "producer_id": "worker",
            "subject_digest": subject,
            "suite_results": None,
            "confinement_result_digest": "sha256:" + "c" * 64,
            "confinement_profile_digest": "sha256:" + "d" * 64,
        }
        (governance / "evidence.json").write_text(
            json.dumps(
                [
                    {
                        **evidence_body,
                        "signature": sign_evidence(evidence_body, worker_private),
                    }
                ]
            ),
            encoding="utf-8",
        )
        journal = Journal(governance / "journal.sqlite3")
        candidate_value = TaskCandidate(
            "task-1", "landing", subject, missing_claims
        )
        candidate_record = candidate_value.as_record()
        if append_candidate:
            journal.append(candidate_value)
        else:
            journal.entries()
        envelope = {
            "candidate": candidate,
            "subject": subject,
            "target_ref": TARGET_REF,
            "tip": tip,
            "catalog_digest": catalog_digest_for(CATALOG),
            "candidate_row_hash": candidate_row_hash(candidate_record),
            "approver_id": "owner",
        }
        approval = repo / "approval.json"
        approval.write_text(
            json.dumps(
                {
                    **envelope,
                    "signature": sign_approval(envelope, approver_private),
                }
            ),
            encoding="utf-8",
        )
        return cls(
            repo,
            tip,
            candidate,
            subject,
            approval,
            candidate_record,
            worker_private,
            approver_private,
            evidence_body,
        )

    def args(self, *, candidate: str | None = None) -> list[str]:
        return [
            "task",
            "merge",
            "--task-id",
            "task-1",
            "--target-ref",
            TARGET_REF,
            "--candidate",
            candidate or self.candidate,
            "--approval",
            str(self.approval),
        ]

    def approval_document(self) -> dict[str, object]:
        value = json.loads(self.approval.read_text(encoding="utf-8"))
        assert isinstance(value, dict)
        return value

    def write_approval(
        self,
        envelope: dict[str, object],
        *,
        private_key: str | None = None,
        signature: str | None = None,
    ) -> None:
        if signature is None:
            signature = sign_approval(envelope, private_key or self.approver_private)
        self.approval.write_text(
            json.dumps({**envelope, "signature": signature}), encoding="utf-8"
        )


def assert_refused(
    scenario: MergeScenario,
    expected_check: str,
    *,
    expected_ref: str | None = None,
    candidate: str | None = None,
    expected_detail: str | None = None,
) -> list[dict[str, object]]:
    assert invoke(scenario.repo, scenario.args(candidate=candidate)) != 0
    if expected_ref is None:
        assert git(scenario.repo, "rev-parse", "--verify", TARGET_REF, check=False) == ""
    else:
        assert git(scenario.repo, "rev-parse", TARGET_REF) == expected_ref
    entries = Journal(scenario.repo / "governance" / "journal.sqlite3").entries()
    outcomes = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") == "task-1"
        and entry.get("outcome") == "REFUSED"
    ]
    assert outcomes
    refused = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == "task-1"
        and entry.get("status") == "refused"
    ]
    assert refused[-1]["check"] == expected_check
    if expected_detail is not None:
        assert refused[-1]["detail"] == expected_detail
    return entries


def test_sad_path_2_unrelated_history_refuses_at_ancestry(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path, history="orphan")

    assert_refused(scenario, "ancestry", expected_ref=scenario.tip)


def test_sad_path_3_merge_commit_in_range_refuses_at_merge_range(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path, history="merge")

    assert git(scenario.repo, "rev-list", "--merges", f"{scenario.tip}..{scenario.candidate}")
    assert_refused(scenario, "merge_range", expected_ref=scenario.tip)


def test_sad_path_5_missing_satisfying_claim_refuses_at_digest_evidence(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path, missing_claims=("tests-executed",))

    assert_refused(
        scenario,
        "digest_evidence",
        expected_ref=scenario.tip,
        expected_detail="sad-path-5 satisfying-evidence-missing",
    )


def test_sad_path_5_subject_differs_from_candidate_refuses_at_digest_evidence(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path)
    wrong_subject = "sha256:" + "0" * 64
    candidate = TaskCandidate("task-1", "landing", wrong_subject, ())
    Journal(scenario.repo / "governance" / "journal.sqlite3").append(candidate)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    envelope["subject"] = wrong_subject
    envelope["candidate_row_hash"] = candidate_row_hash(candidate.as_record())
    scenario.write_approval(envelope)

    assert_refused(
        scenario,
        "digest_evidence",
        expected_ref=scenario.tip,
        expected_detail="sad-path-5 subject-digest-mismatch",
    )


def test_sad_path_5_evidence_for_other_subject_refuses_at_digest_evidence(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path)
    evidence_body = {
        **scenario.evidence_body,
        "subject_digest": "sha256:" + "0" * 64,
    }
    (scenario.repo / "governance" / "evidence.json").write_text(
        json.dumps(
            [
                {
                    **evidence_body,
                    "signature": sign_evidence(evidence_body, scenario.worker_private),
                }
            ]
        ),
        encoding="utf-8",
    )

    assert_refused(
        scenario,
        "digest_evidence",
        expected_ref=scenario.tip,
        expected_detail="sad-path-5 satisfying-evidence-missing",
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("candidate", lambda scenario: scenario.tip),
        ("subject", lambda _scenario: "sha256:" + "0" * 64),
        ("target_ref", lambda _scenario: "refs/heads/other"),
        ("tip", lambda scenario: scenario.candidate),
        ("catalog_digest", lambda _scenario: "sha256:" + "0" * 64),
        ("candidate_row_hash", lambda _scenario: "sha256:" + "0" * 64),
    ],
)
def test_sad_path_22_tampered_signed_binding_refuses_at_policy_approval(
    tmp_path: Path, field: str, replacement: object
) -> None:
    scenario = MergeScenario.create(tmp_path)
    document = scenario.approval_document()
    document[field] = replacement(scenario)
    scenario.approval.write_text(json.dumps(document), encoding="utf-8")

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


@pytest.mark.parametrize(
    ("field", "replacement", "reason"),
    [
        ("candidate", lambda scenario: scenario.tip, "sad-path-6 candidate-mismatch"),
        ("subject", lambda _scenario: "sha256:" + "0" * 64, "sad-path-7 subject-mismatch"),
        ("target_ref", lambda _scenario: "refs/heads/other", "sad-path-8 target-ref-mismatch"),
        (
            "catalog_digest",
            lambda _scenario: "sha256:" + "0" * 64,
            "sad-path-10 catalog-digest-mismatch",
        ),
    ],
)
def test_sad_paths_6_7_8_and_10_resigned_binding_refuses_at_policy_approval(
    tmp_path: Path, field: str, replacement: object, reason: str
) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    envelope[field] = replacement(scenario)
    scenario.write_approval(envelope)

    assert_refused(
        scenario,
        "policy_approval",
        expected_ref=scenario.tip,
        expected_detail=reason,
    )


def test_sad_path_22_forged_signature_refuses_at_policy_approval(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    forged_private, _ = generate_keypair()
    scenario.write_approval(envelope, private_key=forged_private)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_22_cross_domain_signature_refuses_at_policy_approval(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    evidence_signature = sign_evidence(scenario.evidence_body, scenario.approver_private)
    scenario.write_approval(envelope, signature=evidence_signature)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_11_pre_signed_approval_without_candidate_row_refuses(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path, append_candidate=False)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_12_stale_candidate_row_hash_refuses_at_policy_approval(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    envelope["candidate_row_hash"] = "sha256:" + "1" * 64
    scenario.write_approval(envelope)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_13_approver_absent_from_tip_keyring_refuses(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    absent_private, _ = generate_keypair()
    envelope["approver_id"] = "absent"
    scenario.write_approval(envelope, private_key=absent_private)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_14_evidence_producer_cannot_approve(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path)
    envelope = scenario.approval_document()
    envelope.pop("signature")
    envelope["approver_id"] = "worker"
    scenario.write_approval(envelope, private_key=scenario.worker_private)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_15_candidate_catalog_change_refuses_at_policy_approval(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path, catalog_change=True)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_16_candidate_keyring_change_refuses_at_policy_approval(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path, keyring_change=True)

    assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)


def test_sad_path_9_advanced_target_invalidates_tip_binding_before_cas(
    tmp_path: Path,
) -> None:
    scenario = MergeScenario.create(tmp_path)
    git(scenario.repo, "update-ref", TARGET_REF, scenario.candidate, scenario.tip)
    (scenario.repo / "advanced.txt").write_text("advanced\n", encoding="utf-8")
    git(scenario.repo, "add", "advanced.txt")
    git(scenario.repo, "commit", "-q", "-m", "advanced target")
    advanced = git(scenario.repo, "rev-parse", "HEAD")

    assert_refused(scenario, "policy_approval", expected_ref=advanced)


def test_criterion_11_linear_multi_commit_candidate_publishes(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path, commits=4)

    assert git(scenario.repo, "rev-list", "--count", f"{scenario.tip}..{scenario.candidate}") == "4"
    assert invoke(scenario.repo, scenario.args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_REF) == scenario.candidate
    outcomes = [
        entry
        for entry in Journal(
            scenario.repo / "governance" / "journal.sqlite3"
        ).entries()
        if entry.get("type") == "task-merge-outcome"
    ]
    assert outcomes[-1]["outcome"] == "PUBLISHED"


def test_criterion_12_policy_approval_refuses_before_ancestry(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path, history="orphan")
    document = scenario.approval_document()
    document["subject"] = "sha256:" + "0" * 64
    scenario.approval.write_text(json.dumps(document), encoding="utf-8")

    entries = assert_refused(scenario, "policy_approval", expected_ref=scenario.tip)
    checks = [entry["check"] for entry in entries if entry.get("type") == "task-merge-check"]
    assert checks == ["policy_approval"]
    assert "ancestry" not in checks


def test_criterion_12_ancestry_refuses_before_merge_range(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path, history="orphan-merge")

    entries = assert_refused(scenario, "ancestry", expected_ref=scenario.tip)
    checks = [entry["check"] for entry in entries if entry.get("type") == "task-merge-check"]
    assert checks == ["policy_approval", "ancestry"]
    assert "merge_range" not in checks


def test_criterion_14_mutable_working_tree_policy_is_not_read(tmp_path: Path) -> None:
    scenario = MergeScenario.create(tmp_path)
    (scenario.repo / "governance" / "gates.yaml").write_bytes(b"malicious")
    (scenario.repo / "governance" / "producers.yaml").write_bytes(b"malicious")

    assert invoke(scenario.repo, scenario.args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_REF) == scenario.candidate
    outcomes = [
        entry
        for entry in Journal(
            scenario.repo / "governance" / "journal.sqlite3"
        ).entries()
        if entry.get("type") == "task-merge-outcome"
    ]
    assert outcomes[-1]["outcome"] == "PUBLISHED"
