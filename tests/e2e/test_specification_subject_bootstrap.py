"""Frozen SLICE-035 controller-side subject bootstrap contract."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

SPECIFICATION = Path(__file__).with_name("specification")
SUBJECTS_PATH = SPECIFICATION / "subjects.py"
_spec = importlib.util.spec_from_file_location("slice035_subjects", SUBJECTS_PATH)
assert _spec is not None and _spec.loader is not None
subjects = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(subjects)


def test_subject_manifests_bind_real_subject_facts() -> None:
    ranex = subjects.load_subject(SPECIFICATION / "ranex-subject-v1.json")
    kogg = subjects.load_subject(SPECIFICATION / "kogg-subject-v1.json")
    assert ranex["commit"] == "3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce"
    assert ranex["issue"] == 10
    assert kogg["commit"] == subjects.KOGG_PIN
    assert kogg["issue"] == 40
    assert kogg["license"] == "Apache-2.0"
    assert kogg["lockfile"]["bytes"] == 1192252
    assert kogg["lockfile"]["blob"] == "7dcfe14ccbf5660f11e585650b71fb0c5b275ab8"
    assert kogg["license_metadata"]["bytes"] == 11361
    assert kogg["license_metadata"]["sha256"] == "55367b61ccd2a016a0159ad886bd66a3ee6cb5e873d0c75c803c897dd245b075"
    assert kogg["license_metadata"]["blob"] == "2d4f1fee82272cbad5f22394dc064e621f668aac"
    assert kogg["package_json"]["bytes"] == 9003
    assert kogg["package_manager"]["command"] == ["npm", "11.6.0"]
    subjects.validate_manifest(ranex)
    subjects.validate_manifest(kogg)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"commit": "0" * 40}, "subject-commit-drift"),
        ({"issue": 41}, "subject-issue-drift"),
        ({"license": "MIT"}, "subject-license-drift"),
        ({"lockfile": {"path": "package-lock.json", "sha256": "0" * 64}}, "lock-drift"),
        ({"package_manager": {"command": ["npm", "install"]}}, "package-manager-unpinned"),
        ({"process_commands": [["echo", "drift"]]}, "process-command-drift"),
    ],
)
def test_manifest_refusals_are_stable(change: dict[str, object], reason: str) -> None:
    subject = json.loads((SPECIFICATION / "kogg-subject-v1.json").read_text())
    subject.update(change)
    with pytest.raises(subjects.SubjectBlocked, match=reason):
        subjects.validate_manifest(subject)


def test_broker_uses_only_identical_local_helper() -> None:
    preflight, clone = subjects.kogg_network_commands(Path("/tmp/private/repo"))
    assert preflight[:3] == ("git", "-c", subjects.PROCESS_LOCAL_HELPER)
    assert clone[:3] == preflight[:3]
    assert "https://github.com/anthonykewl20/kogg.git" in preflight
    assert "--no-checkout" in clone
    subjects.assert_identical_local_helper(preflight, clone)
    with pytest.raises(subjects.SubjectBlocked, match="helper-mismatch"):
        subjects.assert_identical_local_helper(preflight, ("git", "-c", "credential.helper=!different", *clone[3:]))


def test_credential_hygiene_and_environment_boundary() -> None:
    environment = subjects.broker_environment({"GH_TOKEN": "secret", "GITHUB_TOKEN": "secret", "GIT_CONFIG": "x", "SSH_AUTH_SOCK": "x", subjects.KOGG_CREDENTIAL_ENV: "ref", "KOGG_MAILPIT_SMTP": "1025"})
    assert not any(key.startswith(("GH_", "GITHUB_", "SSH_", "RANEX_SUBJECT_")) or key == "GIT_CONFIG" for key in environment)
    assert "KOGG_MAILPIT_SMTP" not in environment
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1"
    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
    assert environment["GIT_TERMINAL_PROMPT"] == "0"


def test_credential_reference_refusal_is_stable() -> None:
    with pytest.raises(RuntimeError, match="credential-ref-unavailable"):
        subjects.resolve_credential_reference(subjects.KOGG_CREDENTIAL_REF, lambda *_a, **_k: None, source={})


def test_missing_credential_helper_refusal_is_stable() -> None:
    with pytest.raises(RuntimeError, match="helper-unavailable"):
        subjects.resolve_credential_reference(subjects.KOGG_CREDENTIAL_REF, helper_available=lambda: False,
                                              source={subjects.KOGG_CREDENTIAL_ENV: "present"})


@pytest.mark.parametrize("content", [
    "https://user:0000000000000000@example.invalid/repo.git",
    "credential.helper=store\n",
    "Authorization: Bearer 0000000000000000",
])
def test_credential_copy_refusal_is_stable(tmp_path: Path, content: str) -> None:
    unsafe = tmp_path / "unsafe"
    unsafe.write_text(content)
    with pytest.raises(subjects.SubjectBlocked, match="credential-copy-detected"):
        subjects.assert_credential_free((unsafe,))


def test_blocked_oracle_is_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    subject = subjects.load_subject(SPECIFICATION / "kogg-subject-v1.json")
    journal = tmp_path / "outcome.journal"
    monkeypatch.delenv(subjects.KOGG_CREDENTIAL_ENV, raising=False)
    assert subjects.run_kogg_subject(subject, tmp_path, outcome_journal=journal,
                                     runner=lambda *_a, **_k: None) == "BLOCKED"
    assert capsys.readouterr().out == subjects.BLOCKED_LINE + "\n"
    assert journal.read_bytes() == subjects.BLOCKED_RECORD.encode()


def test_real_ranex_bootstrap_or_host_skip(tmp_path: Path) -> None:
    if os.environ.get("RANEX_SLICE035_REAL") != "1":
        pytest.skip("SLICE-035 Ranex real bootstrap: set RANEX_SLICE035_REAL=1")
    subject = subjects.load_subject(SPECIFICATION / "ranex-subject-v1.json")
    commands = subjects.run_ranex_subject(subject, tmp_path)
    assert commands[2] == ("uv", "sync", "--frozen")


def test_real_kogg_bootstrap_or_blocked(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    if os.environ.get("RANEX_SLICE035_REAL") != "1":
        pytest.skip("SLICE-035 kogg real bootstrap: set RANEX_SLICE035_REAL=1")
    subject = subjects.load_subject(SPECIFICATION / "kogg-subject-v1.json")
    journal = tmp_path / "outcome.journal"
    outcome = subjects.run_kogg_subject(subject, tmp_path, outcome_journal=journal)
    if outcome == "BLOCKED":
        assert capsys.readouterr().out == subjects.BLOCKED_LINE + "\n"
        assert journal.read_text(encoding="utf-8") == subjects.BLOCKED_RECORD
    else:
        assert outcome == "AVAILABLE"
        assert not journal.exists()
        assert subjects.LAST_KOGG_RUN["checkout_head"] == subjects.KOGG_PIN
        assert subjects.LAST_KOGG_RUN["metadata"] == {
            "license_sha256": subject["license_metadata"]["sha256"],
            "license_blob": subject["license_metadata"]["blob"],
            "lockfile_sha256": subject["lockfile"]["sha256"],
            "lockfile_blob": subject["lockfile"]["blob"],
            "package_json_sha256": subject["package_json"]["sha256"],
            "package_json_blob": subject["package_json"]["blob"],
        }
        assert subjects.LAST_KOGG_RUN["commands"] == (("npm", "ci"), ("npm", "test"))
        assert "credential.helper" not in subjects.LAST_KOGG_RUN["config_content"]
        assert not any(key.startswith(("GH_", "GITHUB_", "GIT_", "SSH_", "RANEX_SUBJECT_"))
                       and key not in {"GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_TERMINAL_PROMPT"}
                       for key in subjects.LAST_KOGG_RUN["environment"])
        assert subjects.LAST_KOGG_RUN["environment"]["GIT_CONFIG_NOSYSTEM"] == "1"
        assert subjects.LAST_KOGG_RUN["environment"]["GIT_TERMINAL_PROMPT"] == "0"


@pytest.mark.parametrize(
    ("actual_commit", "actual_issue", "reason"),
    [("0" * 40, 10, "subject-commit-drift"), ("3d0924c9c8f0c5483c0dc62558fdd23c51e9ce", 11, "subject-issue-drift")],
)
def test_ranex_subject_refuses_actual_checkout_facts(tmp_path: Path, actual_commit: str, actual_issue: int, reason: str) -> None:
    subject = subjects.load_subject(SPECIFICATION / "ranex-subject-v1.json")
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[-2:] == ("rev-parse", "HEAD"):
            return subprocess.CompletedProcess(command, 0, actual_commit, "")
        if command[:3] == ("gh", "issue", "view"):
            return subprocess.CompletedProcess(command, 0, json.dumps({"number": actual_issue}), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(subjects.SubjectBlocked, match=reason):
        subjects.run_ranex_subject(subject, tmp_path, runner=runner)
