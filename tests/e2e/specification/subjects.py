"""Credential-free, controller-only bootstrap helpers for the pinned real subjects."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path

PROCESS_LOCAL_HELPER = "credential.helper=!/usr/bin/gh auth git-credential"
ARXIC_REPOSITORY = "https://github.com/anthonykewl20/arxic.git"
ARXIC_CREDENTIAL_REF = "github:anthonykewl20/arxic-read"
_HEX = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CREDENTIAL_COPY = re.compile(
    r"(?:https?://[^/\s:@]+:[^@/\s]+@|(?:authorization|password|token)\s*[:=]\s*(?:Bearer\s+)?[A-Za-z0-9_~.-]{16,}|credential\.helper)",
    re.IGNORECASE,
)
_EXPECTED: dict[str, dict[str, object]] = {
    "ranex": {
        "repository": "https://github.com/anthonykewl20/ranex.git",
        "commit": "3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce",
        "issue": 10,
        "license": "MIT",
        "lockfile": ("uv.lock", "dadf979ec0c984e2ee0aa2f1f46804c63ea8c4eebf9519cfb423d4b66be3b5c2"),
        "package_manager": ("uv", "sync", "--frozen"),
    },
    "arxic": {
        "repository": ARXIC_REPOSITORY,
        "commit": "135991d9b1a07c2ffa08e38f8e261543ec5ab980",
        "issue": 109,
        "license": "MIT",
        "lockfile": ("pnpm-lock.yaml", "4659eff963d149db1ee351ac8359f0af1990b201f10ab555b12c4b323cf4a482"),
        "package_manager": ("corepack", "pnpm@11.17.0", "install", "--frozen-lockfile"),
    },
}


class SubjectBlocked(RuntimeError):
    """A stable, deliberately credential-free bootstrap refusal."""


def _blocked(reason: str) -> None:
    raise SubjectBlocked(f"SLICE-035 BLOCKED: {reason}")


def load_subject(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _blocked("subject-manifest-unreadable")
    if not isinstance(value, dict):
        _blocked("subject-manifest-unreadable")
    return value


def validate_manifest(subject: Mapping[str, object]) -> None:
    """Reject all drift from the two approved immutable subject descriptions."""

    name = subject.get("name")
    if not isinstance(name, str) or name not in _EXPECTED:
        _blocked("subject-name-invalid")
    expected = _EXPECTED[name]
    if subject.get("schema") != "ranex-provider-subject-v1":
        _blocked("subject-schema-invalid")
    for field, reason in (("repository", "subject-repository-drift"), ("commit", "subject-commit-drift"),
                          ("issue", "subject-issue-drift"), ("license", "subject-license-drift")):
        if subject.get(field) != expected[field]:
            _blocked(reason)
    commit = subject["commit"]
    if not isinstance(commit, str) or not _HEX.fullmatch(commit):
        _blocked("subject-commit-drift")
    lockfile = subject.get("lockfile")
    if not isinstance(lockfile, dict) or (
        lockfile.get("path"), lockfile.get("sha256")
    ) != expected["lockfile"]:
        _blocked("lock-drift")
    if not isinstance(lockfile.get("sha256"), str) or not _SHA256.fullmatch(lockfile["sha256"]):
        _blocked("lock-drift")
    manager = subject.get("package_manager")
    if not isinstance(manager, dict) or tuple(manager.get("command", ())) != expected["package_manager"]:
        _blocked("package-manager-unpinned")
    commands = subject.get("process_commands")
    if not isinstance(commands, list) or not all(isinstance(command, list) and command for command in commands):
        _blocked("process-command-invalid")
    if name == "arxic" and subject.get("credential_ref") != ARXIC_CREDENTIAL_REF:
        _blocked("credential-ref-unavailable")


def broker_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Construct the only environment passed to Git or bootstrap subprocesses."""

    source = os.environ if source is None else source
    environment = {
        key: value
        for key, value in source.items()
        if not key.startswith(("GH_", "GITHUB_", "GIT_", "SSH_"))
    }
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"})
    return environment


def arxic_network_commands(destination: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the exact paired commands; no caller supplies a helper or URL."""

    prefix = ("git", "-c", PROCESS_LOCAL_HELPER)
    return (
        (*prefix, "ls-remote", ARXIC_REPOSITORY, "HEAD"),
        (*prefix, "clone", "--no-checkout", ARXIC_REPOSITORY, str(destination)),
    )


def assert_identical_local_helper(*commands: Sequence[str]) -> None:
    """Refuse if either Arxic network command loses the exact helper argv."""

    expected = ("git", "-c", PROCESS_LOCAL_HELPER)
    if any(tuple(command[:3]) != expected for command in commands):
        _blocked("helper-mismatch")


def resolve_credential_reference(
    reference: str, runner: Callable[..., subprocess.CompletedProcess[str] | None] = subprocess.run,
    helper_available: Callable[[], bool] | None = None,
) -> None:
    """Confirm the named existing keyring profile without ever requesting its token."""

    if reference != ARXIC_CREDENTIAL_REF:
        _blocked("credential-ref-unavailable")
    helper_available = helper_available or (lambda: Path("/usr/bin/gh").is_file() and os.access("/usr/bin/gh", os.X_OK))
    if not helper_available():
        _blocked("helper-unavailable")
    completed = _run(runner, ("gh", "auth", "status"), failure_reason="credential-ref-unavailable")
    status = (completed.stdout or "") + (completed.stderr or "")
    if "anthonykewl20" not in status or "keyring" not in status.lower():
        _blocked("credential-ref-unavailable")


def _run(
    runner: Callable[..., subprocess.CompletedProcess[str]],
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    failure_reason: str = "remote-preflight-failed",
) -> subprocess.CompletedProcess[str]:
    completed = runner(
        tuple(command), cwd=cwd, capture_output=True, text=True, check=False, env=broker_environment(),
        stdin=subprocess.DEVNULL, close_fds=True,
    )
    if completed is None or completed.returncode != 0:
        _blocked(failure_reason)
    return completed


def assert_credential_free(paths: Sequence[Path]) -> None:
    """Reject source-like files containing a copy-shaped credential, never report it."""

    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            _blocked("credential-hygiene-unreadable")
        if _CREDENTIAL_COPY.search(content):
            _blocked("credential-copy-detected")


def _assert_credential_free_text(content: str) -> None:
    if _CREDENTIAL_COPY.search(content):
        _blocked("credential-copy-detected")


def validate_checkout(subject: Mapping[str, object], checkout: Path, actual_commit: str, issue: int) -> None:
    """Validate checked-out source facts before any dependency command may run."""

    validate_manifest(subject)
    if actual_commit != subject["commit"]:
        _blocked("subject-commit-drift")
    if issue != subject["issue"]:
        _blocked("subject-issue-drift")
    license_path = checkout / "LICENSE"
    if not license_path.is_file() or "MIT License" not in license_path.read_text(encoding="utf-8"):
        _blocked("subject-license-drift")
    lock = subject["lockfile"]
    assert isinstance(lock, dict)
    lock_path = checkout / str(lock["path"])
    if not lock_path.is_file() or hashlib.sha256(lock_path.read_bytes()).hexdigest() != lock["sha256"]:
        _blocked("lock-drift")
    if subject["name"] == "arxic":
        package = checkout / "package.json"
        if not package.is_file() or "\"packageManager\": \"pnpm@11.17.0\"" not in package.read_text(encoding="utf-8"):
            _blocked("package-manager-unpinned")


class CredentialFreeObjectStore:
    """The only Arxic artifact permitted to leave the controller broker."""

    def __init__(self, path: Path, credential_ref: str, audit: tuple[str, ...]) -> None:
        self.path = path
        self.credential_ref = credential_ref
        self.outcome = "credential-free-object-store"
        self.audit = audit


@contextmanager
def arxic_object_store(
    subject: Mapping[str, object],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    temp_parent: Path | None = None,
    helper_available: Callable[[], bool] | None = None,
) -> Iterator[CredentialFreeObjectStore]:
    """Provision a no-checkout clone and delete it after the controller use."""

    validate_manifest(subject)
    resolve_credential_reference(str(subject["credential_ref"]), runner, helper_available)
    root = Path(tempfile.mkdtemp(prefix="slice035-arxic-", dir=temp_parent))
    repository = root / "repo"
    completed = False
    try:
        root.chmod(0o700)
        view = _run(runner, ("gh", "repo", "view", "anthonykewl20/arxic", "--json", "nameWithOwner,isPrivate"))
        try:
            identity = json.loads(view.stdout)
        except json.JSONDecodeError:
            _blocked("repository-identity-drift")
        if identity != {"nameWithOwner": "anthonykewl20/arxic", "isPrivate": False}:
            _blocked("repository-identity-drift")
        issue = _run(runner, ("gh", "issue", "view", "109", "-R", "anthonykewl20/arxic", "--json", "number"))
        try:
            if json.loads(issue.stdout) != {"number": 109}:
                _blocked("subject-issue-drift")
        except json.JSONDecodeError:
            _blocked("subject-issue-drift")
        preflight, clone = arxic_network_commands(repository)
        assert_identical_local_helper(preflight, clone)
        _run(runner, preflight)
        _run(runner, clone)
        config = repository / ".git" / "config"
        if not repository.is_dir() or not config.is_file():
            _blocked("remote-preflight-failed")
        assert_credential_free((config,))
        remote_urls = _run(runner, ("git", "-C", str(repository), "remote", "get-url", "--all", "origin")).stdout
        _assert_credential_free_text(remote_urls)
        if remote_urls.splitlines() != [ARXIC_REPOSITORY]:
            _blocked("repository-identity-drift")
        commit = str(subject["commit"])
        _run(runner, ("git", "-C", str(repository), "cat-file", "-e", f"{commit}^{{commit}}"))
        license_text = _run(runner, ("git", "-C", str(repository), "show", f"{commit}:LICENSE")).stdout
        lock_text = _run(runner, ("git", "-C", str(repository), "show", f"{commit}:pnpm-lock.yaml")).stdout
        package_text = _run(runner, ("git", "-C", str(repository), "show", f"{commit}:package.json")).stdout
        _assert_credential_free_text(license_text + lock_text + package_text)
        if "MIT License" not in license_text:
            _blocked("subject-license-drift")
        lock = subject["lockfile"]
        assert isinstance(lock, dict)
        if hashlib.sha256(lock_text.encode()).hexdigest() != lock["sha256"]:
            _blocked("lock-drift")
        if '"packageManager": "pnpm@11.17.0"' not in package_text:
            _blocked("package-manager-unpinned")
        mode = stat.S_IMODE(root.stat().st_mode)
        if mode != 0o700:
            _blocked("temporary-directory-permissions")
        audit = (
            f"credential-ref={ARXIC_CREDENTIAL_REF}",
            "repository=anthonykewl20/arxic",
            "outcome=credential-free-object-store",
        )
        _assert_credential_free_text("\n".join(audit))
        yield CredentialFreeObjectStore(repository, ARXIC_CREDENTIAL_REF, audit)
        completed = True
    finally:
        try:
            shutil.rmtree(root)
        except OSError:
            if completed:
                _blocked("cleanup-failed")


def run_ranex_subject(
    subject: Mapping[str, object],
    destination: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[tuple[str, ...]]:
    """Clone and execute the locked public Ranex subject; callers own cleanup."""

    validate_manifest(subject)
    checkout = destination / "repo"
    commands: list[tuple[str, ...]] = [
        ("git", "clone", "--no-checkout", str(subject["repository"]), str(checkout)),
        ("git", "-C", str(checkout), "checkout", "--detach", str(subject["commit"])),
    ]
    for command in commands:
        _run(runner, command, failure_reason="ranex-bootstrap-failed")
    actual_commit = _run(
        runner,
        ("git", "-C", str(checkout), "rev-parse", "HEAD"),
        failure_reason="ranex-bootstrap-failed",
    ).stdout.strip()
    issue = _run(
        runner,
        ("gh", "issue", "view", str(subject["issue"]), "-R", "anthonykewl20/ranex", "--json", "number"),
        failure_reason="subject-issue-drift",
    )
    try:
        actual_issue = json.loads(issue.stdout)
    except json.JSONDecodeError:
        _blocked("subject-issue-drift")
    if not isinstance(actual_issue, dict) or actual_issue.get("number") != subject["issue"]:
        _blocked("subject-issue-drift")
    validate_checkout(subject, checkout, actual_commit, actual_issue["number"])
    manager = subject["package_manager"]
    assert isinstance(manager, dict)
    all_commands = [tuple(manager["command"]), *(tuple(command) for command in subject["process_commands"])]
    for command in all_commands:
        _run(runner, command, cwd=checkout, failure_reason="process-failed")
    return [*commands, *all_commands]
