"""Credential-free, controller-only bootstrap helpers for pinned subjects."""

from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

PROCESS_LOCAL_HELPER = "credential.helper=!/usr/bin/gh auth git-credential"
RANEX_REPOSITORY = "https://github.com/anthonykewl20/ranex.git"
KOGG_REPOSITORY = "https://github.com/anthonykewl20/kogg.git"
KOGG_CREDENTIAL_REF = "env:RANEX_SUBJECT_KOGG_CREDENTIAL_REF"
KOGG_CREDENTIAL_ENV = "RANEX_SUBJECT_KOGG_CREDENTIAL_REF"
KOGG_MAILPIT_ENV = ("KOGG_MAILPIT_SMTP", "KOGG_MAILPIT_API")
KOGG_PIN = "dc3763d9517eda5919dfce8bac7f251517b82c7d"
BLOCKED_LINE = "SLICE-035 BLOCKED: credential-ref-unavailable"
BLOCKED_RECORD = '{"outcome":"BLOCKED","reason":"credential-ref-unavailable"}\n'
_HEX = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CREDENTIAL_COPY = re.compile(
    r"(?:https?://[^/\s:@]+:[^@/\s]+@|(?:authorization|password|token)\s*[:=]\s*(?:Bearer\s+)?[A-Za-z0-9_~.-]{16,}|credential\.helper)",
    re.IGNORECASE,
)

LAST_KOGG_RUN: dict[str, object] = {}

_EXPECTED: dict[str, dict[str, object]] = {
    "ranex": {
        "repository": RANEX_REPOSITORY,
        "commit": "3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce",
        "issue": 10,
        "license": "MIT",
        "lockfile": ("uv.lock", "dadf979ec0c984e2ee0aa2f1f46804c63ea8c4eebf9519cfb423d4b66be3b5c2"),
        "package_manager": ("uv", "sync", "--frozen"),
        "process_commands": (
            ("uv", "run", "--frozen", "pytest", "-q", "tests/contract/test_docs_discipline.py"),
            ("uv", "run", "--frozen", "pytest", "-q"),
        ),
    },
    "kogg": {
        "repository": KOGG_REPOSITORY,
        "commit": KOGG_PIN,
        "issue": 40,
        "license": "Apache-2.0",
        "lockfile": ("package-lock.json", "282ab64ad33d0e2e28b6e91ed4d43a373b84e783102e9800672951caedd9b413"),
        "package_manager": ("npm", "11.6.0"),
        "process_commands": (("npm", "test"),),
        "credential_ref": KOGG_CREDENTIAL_REF,
        "metadata": {
            "lockfile_bytes": 1192252,
            "lockfile_sha256": "282ab64ad33d0e2e28b6e91ed4d43a373b84e783102e9800672951caedd9b413",
            "lockfile_blob": "7dcfe14ccbf5660f11e585650b71fb0c5b275ab8",
            "license_bytes": 11361,
            "license_sha256": "55367b61ccd2a016a0159ad886bd66a3ee6cb5e873d0c75c803c897dd245b075",
            "license_blob": "2d4f1fee82272cbad5f22394dc064e621f668aac",
            "package_json_bytes": 9003,
            "package_json_sha256": "391993bc493dda411cb5c5d5bc93b7a34731f9ee1d2b9c36ade77829858b204d",
            "package_json_blob": "20048b9758ad3fc696ffb5a4b1208003e5eabca3",
        },
    },
}


class SubjectBlocked(RuntimeError):
    """Legacy base for the stable subject refusal assertions."""


class SubjectDrift(SubjectBlocked):
    """A frozen subject fact mismatch; this is not the credential oracle."""


class _CredentialProfileUnavailable(RuntimeError):
    """The ordered controller-only profile check found no usable profile."""


def _drift(reason: str) -> None:
    """Raise a subject mismatch without selecting the BLOCKED oracle."""
    raise SubjectDrift(f"SLICE-035 subject drift: {reason}")


def load_subject(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise RuntimeError(f"subject manifest unreadable: path={str(path)!r}") from None
    if not isinstance(value, dict):
        raise RuntimeError(f"subject manifest unreadable: path={str(path)!r}")
    return value


def validate_manifest(subject: Mapping[str, object]) -> None:
    name = subject.get("name")
    if not isinstance(name, str) or name not in _EXPECTED:
        _drift("subject-name-invalid")
    expected = _EXPECTED[name]
    if subject.get("schema") != "ranex-provider-subject-v1":
        _drift("subject-schema-invalid")
    for field, reason in (("repository", "subject-repository-drift"), ("commit", "subject-commit-drift"),
                          ("issue", "subject-issue-drift"), ("license", "subject-license-drift")):
        if subject.get(field) != expected[field]:
            _drift(reason)
    commit = subject["commit"]
    if not isinstance(commit, str) or not _HEX.fullmatch(commit):
        _drift("subject-commit-drift")
    lockfile = subject.get("lockfile")
    if not isinstance(lockfile, dict) or (lockfile.get("path"), lockfile.get("sha256")) != expected["lockfile"]:
        _drift("lock-drift")
    if not isinstance(lockfile.get("sha256"), str) or not _SHA256.fullmatch(lockfile["sha256"]):
        _drift("lock-drift")
    manager = subject.get("package_manager")
    if not isinstance(manager, dict) or tuple(manager.get("command", ())) != expected["package_manager"]:
        _drift("package-manager-unpinned")
    commands = subject.get("process_commands")
    if not isinstance(commands, list) or not all(isinstance(command, list) and command for command in commands):
        _drift("process-command-invalid")
    if tuple(tuple(command) for command in commands) != expected["process_commands"]:
        _drift("process-command-drift")
    if name == "kogg" and subject.get("credential_ref") != KOGG_CREDENTIAL_REF:
        _drift("credential-ref-unavailable")
    if name == "kogg":
        license_metadata = subject.get("license_metadata")
        package_json = subject.get("package_json")
        if not isinstance(license_metadata, dict) or not isinstance(package_json, dict):
            _drift("subject-metadata-drift")
        for key, expected_value in expected["metadata"].items():
            actual = {
                "license_bytes": license_metadata.get("bytes"),
                "license_sha256": license_metadata.get("sha256"),
                "license_blob": license_metadata.get("blob"),
                "lockfile_bytes": lockfile.get("bytes"),
                "lockfile_sha256": lockfile.get("sha256"),
                "lockfile_blob": lockfile.get("blob"),
                "package_json_bytes": package_json.get("bytes"),
                "package_json_sha256": package_json.get("sha256"),
                "package_json_blob": package_json.get("blob"),
            }.get(key)
            if actual != expected_value:
                _drift("subject-metadata-drift")


def broker_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Construct the only environment passed to Git or subject subprocesses."""

    source = os.environ if source is None else source
    environment = {
        key: value
        for key, value in source.items()
        if not key.startswith(("GH_", "GITHUB_", "GIT_", "SSH_", "RANEX_SUBJECT_"))
        and key not in KOGG_MAILPIT_ENV
    }
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"})
    return environment


def controller_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Preserve controller authority while making its GH config explicit.

    The G-4 isolation wrapper replaces HOME/XDG_CONFIG_HOME, but does not
    provision a GH profile. Resolve the real passwd home rather than the
    brokered HOME; this environment is never passed to subject processes.
    """
    source = os.environ if source is None else source
    environment = dict(source)
    if not environment.get("GH_CONFIG_DIR"):
        real_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
        environment["GH_CONFIG_DIR"] = str(real_home / ".config" / "gh")
    return environment


def kogg_network_commands(destination: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    prefix = ("git", "-c", PROCESS_LOCAL_HELPER)
    return (*prefix, "ls-remote", KOGG_REPOSITORY, "HEAD"), (*prefix, "clone", "--no-checkout", KOGG_REPOSITORY, str(destination))


def assert_identical_local_helper(*commands: Sequence[str]) -> None:
    expected = ("git", "-c", PROCESS_LOCAL_HELPER)
    if any(tuple(command[:3]) != expected for command in commands):
        _drift("helper-mismatch")


def resolve_credential_reference(
    reference: str,
    runner: Callable[..., subprocess.CompletedProcess[str] | None] = subprocess.run,
    helper_available: Callable[[], bool] | None = None,
    source: Mapping[str, str] | None = None,
) -> None:
    """Resolve only the named controller profile, never its credential bytes."""

    if reference != KOGG_CREDENTIAL_REF:
        raise ValueError("credential reference is not the controller-only kogg profile")
    source = os.environ if source is None else source
    helper_available = helper_available or (lambda: Path("/usr/bin/gh").is_file() and os.access("/usr/bin/gh", os.X_OK))
    if not helper_available():
        raise RuntimeError("helper-unavailable")
    try:
        completed = runner(("gh", "auth", "status"), capture_output=True, text=True, check=False,
                            env=controller_environment(source), stdin=subprocess.DEVNULL, close_fds=True, timeout=5)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("credential profile command timed out: argv=('gh', 'auth', 'status')") from error
    if completed is None:
        raise _CredentialProfileUnavailable("credential-ref-unavailable")
    status = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        if re.search(r"not logged in|not authenticated|no authentication", status, re.IGNORECASE):
            raise _CredentialProfileUnavailable("credential-ref-unavailable")
        raise RuntimeError(
            f"credential profile command failed: argv=('gh', 'auth', 'status') returncode={completed.returncode} "
            f"stdout_tail={(completed.stdout or '')[-2000:]!r} stderr_tail={(completed.stderr or '')[-2000:]!r}"
        )
    profiles = re.findall(r"account\s+([A-Za-z0-9_-]+)", status)
    if profiles != ["anthonykewl20"] or "keyring" not in status.lower() or "Active account: true" not in status:
        raise _CredentialProfileUnavailable("credential-ref-unavailable")


def _run(runner: Callable[..., subprocess.CompletedProcess[str]], command: Sequence[str], *, cwd: Path | None = None,
         environment: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = runner(tuple(command), cwd=cwd, capture_output=True, text=True, check=False,
                       env=dict(controller_environment() if environment is None else environment),
                       stdin=subprocess.DEVNULL, close_fds=True)
    if completed is None or completed.returncode != 0:
        stdout = (completed.stdout if completed is not None else "") or ""
        stderr = (completed.stderr if completed is not None else "") or ""
        raise RuntimeError(
            f"controller command failed: argv={tuple(command)!r} returncode={completed.returncode if completed is not None else 'unknown'} "
            f"stdout_tail={stdout[-2000:]!r} stderr_tail={stderr[-2000:]!r}"
        )
    return completed


def _run_lifecycle(runner: Callable[..., subprocess.CompletedProcess[str]], command: Sequence[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = runner(tuple(command), cwd=cwd, capture_output=True, text=True, check=False, env=broker_environment(),
                       stdin=subprocess.DEVNULL, close_fds=True)
    if completed is None or completed.returncode != 0:
        stdout = (completed.stdout if completed is not None else "") or ""
        stderr = (completed.stderr if completed is not None else "") or ""
        raise RuntimeError(
            f"lifecycle command failed: argv={tuple(command)!r} returncode={completed.returncode if completed is not None else 'unknown'} "
            f"stdout_tail={stdout[-2000:]!r} stderr_tail={stderr[-2000:]!r}"
        )
    return completed


def assert_credential_free(paths: Sequence[Path], environment: Mapping[str, str] | None = None) -> None:
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            raise RuntimeError(f"credential hygiene unreadable: path={str(path)!r}") from None
        if _CREDENTIAL_COPY.search(content):
            raise SubjectDrift("SLICE-035 subject hygiene failure: credential-copy-detected")
    safe_git_controls = {"GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL", "GIT_TERMINAL_PROMPT"}
    if environment is not None and any(key.startswith(("GH_", "GITHUB_", "GIT_", "SSH_", "RANEX_SUBJECT_"))
                                      and key not in safe_git_controls for key in environment):
        raise SubjectDrift("SLICE-035 subject hygiene failure: credential-copy-detected")


def validate_checkout(subject: Mapping[str, object], checkout: Path, actual_commit: str, issue: int) -> None:
    validate_manifest(subject)
    if actual_commit != subject["commit"]:
        _drift("subject-commit-drift")
    if issue != subject["issue"]:
        _drift("subject-issue-drift")
    license_path = checkout / "LICENSE"
    if not license_path.is_file() or (subject["license"] == "MIT" and "MIT License" not in license_path.read_text(encoding="utf-8")):
        _drift("subject-license-drift")
    if subject["license"] == "Apache-2.0" and "Apache License" not in license_path.read_text(encoding="utf-8"):
        _drift("subject-license-drift")
    lock = subject["lockfile"]
    assert isinstance(lock, dict)
    lock_path = checkout / str(lock["path"])
    if not lock_path.is_file() or hashlib.sha256(lock_path.read_bytes()).hexdigest() != lock["sha256"]:
        _drift("lock-drift")


def validate_kogg_metadata(subject: Mapping[str, object], checkout: Path) -> dict[str, str]:
    metadata = subject.get("license_metadata")
    package_json = subject.get("package_json")
    lock = subject.get("lockfile")
    if not isinstance(metadata, dict) or not isinstance(package_json, dict) or not isinstance(lock, dict):
        _drift("subject-metadata-drift")
    expected = {
        "LICENSE": (checkout / "LICENSE", metadata, "license"),
        str(lock["path"]): (checkout / str(lock["path"]), lock, "lockfile"),
        "package.json": (checkout / "package.json", package_json, "package_json"),
    }
    verified: dict[str, str] = {}
    for _name, (path, facts, prefix) in expected.items():
        if not path.is_file():
            _drift("subject-metadata-drift")
        content = path.read_bytes()
        blob = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        if (len(content) != facts.get("bytes") or hashlib.sha256(content).hexdigest() != facts.get("sha256")
                or blob != facts.get("blob")):
            _drift("subject-metadata-drift")
        verified[f"{prefix}_sha256"] = hashlib.sha256(content).hexdigest()
        verified[f"{prefix}_blob"] = blob
    return verified


def write_blocked_outcome(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as journal:
        journal.write(BLOCKED_RECORD)


def run_kogg_subject(subject: Mapping[str, object], destination: Path, *, outcome_journal: Path,
                     runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> str:
    """Run the credential gate; only its unavailable branch is accepted as BLOCKED."""

    try:
        resolve_credential_reference(str(subject.get("credential_ref", "")), runner)
    except _CredentialProfileUnavailable:
        write_blocked_outcome(outcome_journal)
        print(BLOCKED_LINE)
        return "BLOCKED"
    root = destination / "repo"
    try:
        preflight, clone = kogg_network_commands(root)
        assert_identical_local_helper(preflight, clone)
        _run(runner, preflight)
        _run(runner, clone)
        _run(runner, ("git", "-C", str(root), "checkout", "--detach", KOGG_PIN))
        validate_checkout(subject, root, KOGG_PIN, int(subject["issue"]))
        verified = validate_kogg_metadata(subject, root)
        environment = broker_environment()
        assert_credential_free((root / ".git" / "config",), environment)
        lifecycle_commands = (("npm", "ci"), ("npm", "test"))
        for command in lifecycle_commands:
            _run_lifecycle(runner, command, cwd=root)
        LAST_KOGG_RUN.clear()
        LAST_KOGG_RUN.update(checkout_head=KOGG_PIN, metadata=verified, commands=lifecycle_commands,
                             environment=environment, config_content=(root / ".git" / "config").read_text(encoding="utf-8"))
        return "AVAILABLE"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def run_ranex_subject(subject: Mapping[str, object], destination: Path, *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> list[tuple[str, ...]]:
    validate_manifest(subject)
    checkout = destination / "repo"
    commands: list[tuple[str, ...]] = [("git", "clone", "--no-checkout", str(subject["repository"]), str(checkout)),
                                      ("git", "-C", str(checkout), "checkout", "--detach", str(subject["commit"]))]
    for command in commands:
        _run(runner, command)
    actual_commit = _run(runner, ("git", "-C", str(checkout), "rev-parse", "HEAD")).stdout.strip()
    issue = _run(runner, ("gh", "issue", "view", str(subject["issue"]), "-R", "anthonykewl20/ranex", "--json", "number"))
    issue_command = ("gh", "issue", "view", str(subject["issue"]), "-R", "anthonykewl20/ranex", "--json", "number")
    try:
        actual_issue = json.loads(issue.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"controller command returned invalid JSON: argv={issue_command!r} "
            f"stdout_tail={issue.stdout[-2000:]!r} stderr_tail={issue.stderr[-2000:]!r}"
        ) from None
    if not isinstance(actual_issue, dict) or actual_issue.get("number") != subject["issue"]:
        _drift("subject-issue-drift")
    validate_checkout(subject, checkout, actual_commit, actual_issue["number"])
    manager = subject["package_manager"]
    assert isinstance(manager, dict)
    all_commands = [tuple(manager["command"]), *(tuple(command) for command in subject["process_commands"])]
    for command in all_commands:
        _run_lifecycle(runner, command, cwd=checkout)
    return [*commands, *all_commands]
