"""SLICE-001 — `ranex run` observes a command and emits evidence.

The target for this slice. Written before the implementation and required to
fail first: a test that passes before the code exists is not a target, it is a
circle painted around wherever the dart landed.

Contract under test:

    ranex run --claim <id> --producer <id> -- <command...>

- exits with the wrapped command's exit code, so `run && gate evaluate` composes
- records the exit code verbatim, success or failure — a failing command is
  honest evidence, not an error
- refuses a dirty working tree, because a digest of HEAD does not describe an
  uncommitted tree
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import cmd_run, main
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256, command_digest

# SLICE-003: `tests-executed` names one command. `check.sh` reads the committed
# tree and succeeds only against it, so a claim satisfied by it is a claim about
# this tree — unlike `sh -c 'exit 0'`, which most of this file runs and which is
# therefore no longer satisfying evidence for anything.
CHECK_SCRIPT = "grep -qx content file.txt\n"
BOUND = ["sh", "check.sh"]

GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["sh", "check.sh"]
"""


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    """A real git repository whose working tree is clean."""

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    # The keyring is committed with the tree, as it is in production: it is the
    # trust root, and review of this file is the control on it.
    signing.write_keyring(repository)
    attach(repository, signing)
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    return repository


def subject_of(repo: Path) -> str:
    """The digest `gate evaluate` will compute for HEAD."""

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def invoke(repo: Path, argv: list[str], producer: str | None = None) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        if producer is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv(
                "RANEX_SIGNING_KEY", str(signing_for(repo).key_path(producer))
            )
        return main(argv)


def run_cmd(repo: Path, *command: str, claim: str = "tests-executed",
            producer: str = "worker", evidence: str = "evidence.json") -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", claim,
            "--producer", producer,
            "--repository", ".",
            "--evidence", evidence,
            "--producers", "producers.yaml",
            "--", *command,
        ],
        producer=producer,
    )


def evaluate(repo: Path, approver: str = "reviewer") -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--suite-manifest", "suite_manifest.json",
            "--approver", approver,
        ],
    )


def records(repo: Path, name: str = "evidence.json") -> list[dict]:
    return json.loads((repo / name).read_text(encoding="utf-8"))


# --- observation -----------------------------------------------------------


def test_records_a_successful_command_that_satisfies_nothing(repo: Path) -> None:
    """SLICE-003 inverted the second half of this test, deliberately.

    Everything SLICE-001 proved is still asserted: `run` records the claim, the
    producer, the exit code verbatim, the subject digest, and a readable command.
    What it no longer does is bless the result. `sh -c 'exit 0'` succeeds against
    any tree, so a record of it is honest observation and not evidence for
    `tests-executed` — the claim names a different command, and `gate evaluate`
    now says so.
    """

    assert run_cmd(repo, "sh", "-c", "exit 0") == 0

    (record,) = records(repo)
    assert record["claim_id"] == "tests-executed"
    assert record["producer_id"] == "worker"
    assert record["exit_code"] == 0
    assert record["subject_digest"] == subject_of(repo)
    assert "exit 0" in record["command"]
    assert record["command_digest"] == command_digest(["sh", "-c", "exit 0"])

    assert evaluate(repo) == 1, (
        "a command that exits 0 against any tree was accepted as evidence that "
        "this tree's tests ran"
    )


def test_records_a_failing_command_and_exits_with_its_code(repo: Path) -> None:
    """A failing command is evidence of failure, not a usage error."""

    assert run_cmd(repo, "sh", "-c", "exit 3") == 3

    (record,) = records(repo)
    assert record["exit_code"] == 3


def test_records_a_command_that_exits_two_and_returns_two(repo: Path) -> None:
    """Exit 2 can be the observed command's status after recording succeeds."""

    assert run_cmd(repo, "sh", "-c", "exit 2") == 2

    (record,) = records(repo)
    assert record["exit_code"] == 2
    assert cmd_run.__doc__ is not None
    assert "Exit 2 can therefore mean either" in cmd_run.__doc__
    assert "inspect the evidence file" in " ".join(cmd_run.__doc__.split())


def test_subject_matches_what_gate_evaluate_computes(repo: Path) -> None:
    """One digest implementation, not two."""

    run_cmd(repo, "sh", "-c", "exit 0")
    assert records(repo)[0]["subject_digest"] == subject_of(repo)


def test_suite_freeze_command_writes_canonical_outcome_blind_manifest(
    repo: Path,
) -> None:
    (repo / "freeze-report.sh").write_text(
        "printf '%s' '<testsuites><testsuite><testcase "
        "classname=\"tests.test_sample\" name=\"test_skip\"><failure />"
        "</testcase></testsuite></testsuites>' > report.xml\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(repo), "add", "freeze-report.sh"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "freeze command"],
        check=True,
    )

    assert invoke(
        repo,
        [
            "suite",
            "freeze",
            "--artifact",
            "report.xml",
            "--output",
            "suite_manifest.json",
            "--expected-skip",
            "tests/test_sample.py::test_skip=credential-gated",
            "--",
            "sh",
            "freeze-report.sh",
        ],
    ) == 0
    expected = {
        "suite": ["tests/test_sample.py::test_skip"],
        "expected_skips": {
            "tests/test_sample.py::test_skip": "credential-gated",
        },
    }
    assert (repo / "suite_manifest.json").read_bytes() == canonical_json_bytes(expected)


def test_suite_freeze_refuses_a_second_repository_target(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (repo / "nested").mkdir()

    result = invoke(
        repo,
        [
            "suite", "freeze",
            "--repository", "nested",
            "--artifact", "report.xml",
            "--", "sh", "-c", "exit 0",
        ],
    )

    assert result == 2
    assert "second-repository targets are refused" in capsys.readouterr().err


def test_suite_freeze_refuses_a_missing_command(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke(
        repo,
        ["suite", "freeze", "--artifact", "report.xml"],
    )

    assert result == 2
    assert "a freeze command is required after --" in capsys.readouterr().err


def test_suite_freeze_refuses_a_malformed_expected_skip(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = invoke(
        repo,
        [
            "suite", "freeze",
            "--artifact", "report.xml",
            "--expected-skip", "tests/test_sample.py::test_skip=   ",
            "--", "sh", "-c", "exit 0",
        ],
    )

    assert result == 2
    assert "TEST_ID=REASON with a non-empty reason" in capsys.readouterr().err


def test_suite_freeze_refuses_duplicate_expected_skip_declarations(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    declaration = "tests/test_sample.py::test_skip=credential-gated"
    result = invoke(
        repo,
        [
            "suite", "freeze",
            "--artifact", "report.xml",
            "--expected-skip", declaration,
            "--expected-skip", declaration,
            "--", "sh", "-c", "exit 0",
        ],
    )

    assert result == 2
    assert "duplicate --expected-skip declaration" in capsys.readouterr().err


def test_suite_freeze_refuses_a_dirty_working_tree(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (repo / "file.txt").write_text("dirty\n", encoding="utf-8")

    result = invoke(
        repo,
        [
            "suite", "freeze",
            "--artifact", "report.xml",
            "--", "sh", "-c", "exit 0",
        ],
    )

    assert result == 2
    assert "refusing to freeze against a dirty working tree" in capsys.readouterr().err


def test_suite_freeze_refuses_when_execution_returns_no_artifact(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    completed = subprocess.CompletedProcess(["sh", "-c", "exit 0"], 0)
    monkeypatch.setattr(
        "ranex.cli.main._execute_hermetically",
        lambda *_args, **_kwargs: SimpleNamespace(
            completed=completed,
            executable=Path("/usr/bin/sh"),
            artifact=None,
        ),
    )

    result = invoke(
        repo,
        [
            "suite", "freeze",
            "--artifact", "report.xml",
            "--", "sh", "-c", "exit 0",
        ],
    )

    assert result == 2
    assert "freeze run produced no readable results artifact" in capsys.readouterr().err


def test_run_reads_suite_results_before_materialisation_teardown(repo: Path) -> None:
    test_id = "tests/test_sample.py::test_pass"
    command = ["sh", "write-results.sh", "--junitxml=artifacts/junit.xml"]
    (repo / "write-results.sh").write_text(
        "mkdir -p artifacts\n"
        "printf '%s' '<testsuites><testsuite><testcase "
        "classname=\"tests.test_sample\" name=\"test_pass\" />"
        "</testsuite></testsuites>' > artifacts/junit.xml\n",
        encoding="utf-8",
    )
    (repo / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: tests-executed\n"
        f"        command: {json.dumps(command)}\n"
        "        results_artifact: artifacts/junit.xml\n",
        encoding="utf-8",
    )
    manifest = {"suite": [test_id], "expected_skips": {}}
    (repo / "suite_manifest.json").write_bytes(canonical_json_bytes(manifest))
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "bind suite results"],
        check=True,
    )

    assert invoke(
        repo,
        [
            "run",
            "--claim",
            "tests-executed",
            "--producer",
            "worker",
            "--evidence",
            "evidence.json",
            "--producers",
            "producers.yaml",
            "--gate-catalog",
            "gates.yaml",
            "--suite-manifest",
            "suite_manifest.json",
            "--",
            *command,
        ],
        producer="worker",
    ) == 0
    (record,) = records(repo)
    assert record["suite_results"]["missing"] == []
    assert record["suite_results"]["counts"]["passed"] == 1
    assert not (repo / "artifacts" / "junit.xml").exists()
    assert evaluate(repo) == 0


def test_run_refuses_a_suite_results_claim_without_a_loaded_manifest(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    command = ["sh", "-c", "exit 0", "--junitxml=artifacts/junit.xml"]
    (repo / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: tests-executed\n"
        f"        command: {json.dumps(command)}\n"
        "        results_artifact: artifacts/junit.xml\n",
        encoding="utf-8",
    )
    (repo / "suite_manifest.json").write_bytes(
        canonical_json_bytes({"suite": [], "expected_skips": {}})
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "suite claim"],
        check=True,
    )
    monkeypatch.setattr("ranex.cli.main.load_manifest_bytes", lambda _source: None)

    result = invoke(
        repo,
        [
            "run",
            "--claim", "tests-executed",
            "--producer", "worker",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--gate-catalog", "gates.yaml",
            "--suite-manifest", "suite_manifest.json",
            "--", *command,
        ],
        producer="worker",
    )

    assert result == 2
    assert "suite-results claim has no loaded manifest" in capsys.readouterr().err
    assert not (repo / "evidence.json").exists()


# --- refusing to make a false claim ----------------------------------------


def test_refuses_a_dirty_working_tree(repo: Path) -> None:
    """HEAD's digest does not describe an uncommitted tree."""

    (repo / "file.txt").write_text("modified\n", encoding="utf-8")

    assert run_cmd(repo, "sh", "-c", "exit 0") == 2
    assert not (repo / "evidence.json").exists(), "nothing may be written"


def test_refuses_an_untracked_file(repo: Path) -> None:
    """An untracked file is absent from HEAD's tree but present when the
    command runs, so the digest would not describe what was observed."""

    (repo / "stray.py").write_text("x = 1\n", encoding="utf-8")

    assert run_cmd(repo, "sh", "-c", "exit 0") == 2
    assert not (repo / "evidence.json").exists()


def test_existing_evidence_file_does_not_count_as_dirty(repo: Path) -> None:
    """Ranex's own output is written after the command ran and cannot have
    influenced it. Without this exemption the second run always refuses."""

    assert run_cmd(repo, "sh", "-c", "exit 0") == 0
    assert run_cmd(repo, "sh", "-c", "exit 0", claim="contracts-validated") == 0

    assert {r["claim_id"] for r in records(repo)} == {
        "tests-executed",
        "contracts-validated",
    }


def test_refuses_absolute_evidence_path(repo: Path) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 0", evidence=str(repo / "out.json")) == 2


# --- the evidence file -----------------------------------------------------


def test_creates_the_evidence_file_when_absent(repo: Path) -> None:
    assert not (repo / "evidence.json").exists()
    run_cmd(repo, "sh", "-c", "exit 0")
    assert (repo / "evidence.json").is_file()


def test_preserves_unrelated_records(repo: Path) -> None:
    (repo / "evidence.json").write_text(
        json.dumps(
            [
                signing_for(repo).sign(
                    {
                        "claim_id": "contracts-validated",
                        "subject_digest": subject_of(repo),
                        "producer_id": "auditor",
                        "command": "validate",
                        "command_digest": command_digest(["validate"]),
                        "executable_path": "/usr/bin/validate",
                        "exit_code": 0,
                    },
                    "auditor",
                )
            ]
        ),
        encoding="utf-8",
    )

    run_cmd(repo, "sh", "-c", "exit 0")

    assert {r["claim_id"] for r in records(repo)} == {
        "contracts-validated",
        "tests-executed",
    }


def test_replaces_the_same_claim_and_producer(repo: Path) -> None:
    run_cmd(repo, "sh", "-c", "exit 0")
    run_cmd(repo, "sh", "-c", "exit 0")

    assert len(records(repo)) == 1


def test_keeps_the_same_claim_from_a_different_producer(repo: Path) -> None:
    run_cmd(repo, "sh", "-c", "exit 0", producer="worker-a")
    run_cmd(repo, "sh", "-c", "exit 0", producer="worker-b")

    assert {r["producer_id"] for r in records(repo)} == {"worker-a", "worker-b"}


def test_output_round_trips_through_admission(repo: Path) -> None:
    """`load_evidence` became `admitted_evidence` in SLICE-002: records are read
    raw and admission decides which are evidence. The round trip still has to
    hold, and now it also has to verify."""

    from ranex.cli.main import admitted_evidence

    run_cmd(repo, "sh", "-c", "exit 0")

    admission = admitted_evidence(repo / "evidence.json", repo / "producers.yaml")
    assert admission.rejections == ()
    (evidence,) = admission.evidence
    assert evidence.claim_id == "tests-executed"
    assert evidence.exit_code == 0
    assert evidence.subject_digest == subject_of(repo)


# --- the closed loop -------------------------------------------------------


def test_run_then_gate_evaluate_passes(repo: Path, capsys) -> None:
    """The whole point of the slice: produced evidence satisfies the gate.

    SLICE-003 changed which command that is — the one the catalog binds to the
    claim — and nothing else about what this test proves.
    """

    assert run_cmd(repo, *BOUND) == 0
    capsys.readouterr()

    assert evaluate(repo) == 0
    assert "PASS" in capsys.readouterr().out


def test_failed_command_produces_evidence_that_blocks(repo: Path, capsys) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 1") == 1
    capsys.readouterr()

    assert evaluate(repo) == 1
    assert "FAIL" in capsys.readouterr().out


def test_self_approval_still_refused_end_to_end(repo: Path, capsys) -> None:
    """The bound command, so self-approval is the only reason this can fail."""

    assert run_cmd(repo, *BOUND, producer="alice") == 0
    capsys.readouterr()

    assert evaluate(repo, approver="alice") == 1
    assert "self-approval" in capsys.readouterr().out
