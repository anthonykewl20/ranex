"""Frozen SLICE-035 controller-side subject bootstrap contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
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
    arxic = subjects.load_subject(SPECIFICATION / "arxic-subject-v1.json")
    assert ranex["commit"] == "3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce"
    assert ranex["issue"] == 10
    assert arxic["commit"] == "135991d9b1a07c2ffa08e38f8e261543ec5ab980"
    assert arxic["issue"] == 109
    assert arxic["credential_ref"] == "github:anthonykewl20/arxic-read"
    subjects.validate_manifest(ranex)
    subjects.validate_manifest(arxic)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"commit": "0" * 40}, "subject-commit-drift"),
        ({"issue": 110}, "subject-issue-drift"),
        ({"license": "Apache-2.0"}, "subject-license-drift"),
        ({"lockfile": {"path": "pnpm-lock.yaml", "sha256": "0" * 64}}, "lock-drift"),
        ({"package_manager": {"command": ["pnpm", "install"]}}, "package-manager-unpinned"),
    ],
)
def test_checkout_fact_refusals_are_stable(change: dict[str, object], reason: str) -> None:
    subject = json.loads((SPECIFICATION / "arxic-subject-v1.json").read_text())
    subject.update(change)
    with pytest.raises(subjects.SubjectBlocked, match=reason):
        subjects.validate_manifest(subject)


def test_checkout_fact_refusals_are_stable_for_source_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    subject = json.loads((SPECIFICATION / "arxic-subject-v1.json").read_text())
    checkout = tmp_path / "subject"
    checkout.mkdir()
    (checkout / "LICENSE").write_text("MIT License\n")
    (checkout / "package.json").write_text('{"packageManager": "pnpm@11.17.0"}')
    lock = checkout / "pnpm-lock.yaml"
    lock.write_text("locked\n")
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    subject["lockfile"]["sha256"] = digest
    monkeypatch.setitem(subjects._EXPECTED["arxic"], "lockfile", ("pnpm-lock.yaml", digest))
    subjects.validate_checkout(subject, checkout, subject["commit"], subject["issue"])
    lock.write_text("drift\n")
    with pytest.raises(subjects.SubjectBlocked, match="lock-drift"):
        subjects.validate_checkout(subject, checkout, subject["commit"], subject["issue"])
    lock.write_text("locked\n")
    (checkout / "LICENSE").unlink()
    with pytest.raises(subjects.SubjectBlocked, match="subject-license-drift"):
        subjects.validate_checkout(subject, checkout, subject["commit"], subject["issue"])


def test_credential_reference_refusal_is_stable() -> None:
    with pytest.raises(subjects.SubjectBlocked, match="credential-ref-unavailable"):
        subjects.resolve_credential_reference("github:wrong/profile", lambda *_a, **_k: None)


def test_broker_uses_only_identical_local_helper() -> None:
    preflight, clone = subjects.arxic_network_commands(Path("/tmp/private/repo"))
    assert preflight[0:3] == ("git", "-c", subjects.PROCESS_LOCAL_HELPER)
    assert clone[0:3] == preflight[0:3]
    assert "repo" not in preflight and "repo" not in clone[:3]
    assert "https://github.com/anthonykewl20/arxic.git" in preflight
    assert "--no-checkout" in clone


@pytest.mark.parametrize(
    "unsafe",
    [
        "https://x-access-token:0000000000000000@example.invalid/repo.git",
        "credential.helper=!helper password=0000000000000000",
        "Authorization: Bearer 0000000000000000",
    ],
)
def test_credential_hygiene_refusals_are_stable(unsafe: str, tmp_path: Path) -> None:
    unsafe_path = tmp_path / "unsafe"
    unsafe_path.write_text(unsafe)
    with pytest.raises(subjects.SubjectBlocked, match="credential-copy-detected"):
        subjects.assert_credential_free((unsafe_path,))
    environment = subjects.broker_environment({"GH_TOKEN": "secret", "GITHUB_TOKEN": "secret"})
    assert "GH_TOKEN" not in environment and "GITHUB_TOKEN" not in environment


def test_real_ranex_bootstrap_or_host_skip(tmp_path: Path) -> None:
    if os.environ.get("RANEX_SLICE035_REAL") != "1":
        pytest.skip("SLICE-035 Ranex real bootstrap host-gated: set RANEX_SLICE035_REAL=1")
    subject = subjects.load_subject(SPECIFICATION / "ranex-subject-v1.json")
    destination = tmp_path / "ranex"
    destination.mkdir(mode=0o700)
    try:
        commands = subjects.run_ranex_subject(subject, destination)
        assert commands[2] == ("uv", "sync", "--frozen")
    finally:
        shutil.rmtree(destination)


def test_broker_cleanup_leaves_no_survivor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    subject = subjects.load_subject(SPECIFICATION / "arxic-subject-v1.json")
    empty_digest = hashlib.sha256(b"").hexdigest()
    subject["lockfile"]["sha256"] = empty_digest
    monkeypatch.setitem(subjects._EXPECTED["arxic"], "lockfile", ("pnpm-lock.yaml", empty_digest))
    calls: list[tuple[str, ...]] = []

    def runner(command: tuple[str, ...], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[:3] == ("gh", "auth", "status"):
            return subprocess.CompletedProcess(command, 0, "anthonykewl20 keyring", "")
        if command[:3] == ("gh", "repo", "view"):
            return subprocess.CompletedProcess(command, 0, '{"nameWithOwner":"anthonykewl20/arxic","isPrivate":false}', "")
        if command[:3] == ("gh", "issue", "view"):
            return subprocess.CompletedProcess(command, 0, '{"number":109}', "")
        if "clone" in command:
            destination = Path(command[-1])
            (destination / ".git").mkdir(parents=True)
            (destination / ".git" / "config").write_text(
                "[remote \"origin\"]\n\turl = https://github.com/anthonykewl20/arxic.git\n"
            )
        if "show" in command and command[-1].endswith(":LICENSE"):
            return subprocess.CompletedProcess(command, 0, "MIT License\n", "")
        if "show" in command and command[-1].endswith(":pnpm-lock.yaml"):
            return subprocess.CompletedProcess(command, 0, "", "")
        if "show" in command and command[-1].endswith(":package.json"):
            return subprocess.CompletedProcess(command, 0, '{"packageManager": "pnpm@11.17.0"}', "")
        if command[-4:] == ("remote", "get-url", "--all", "origin"):
            return subprocess.CompletedProcess(command, 0, "https://github.com/anthonykewl20/arxic.git\n", "")
        return subprocess.CompletedProcess(command, 0, "", "")

    with subjects.arxic_object_store(subject, runner=runner, temp_parent=tmp_path, helper_available=lambda: True) as store:
        assert store.path.is_dir()
        assert store.credential_ref == "github:anthonykewl20/arxic-read"
        assert "secret" not in repr(store)
        assert all("secret" not in entry for entry in store.audit)
    assert list(tmp_path.iterdir()) == []
    _preflight, clone = subjects.arxic_network_commands(Path("/tmp/private/repo"))
    assert any(command[:3] == clone[:3] and "--no-checkout" in command for command in calls)
