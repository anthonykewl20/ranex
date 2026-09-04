"""Security arms for the publisher: fail closed, leak nothing, retry never.

The load-bearing property is one line: no input outside a VERIFIED record
saying PASS can produce a `success` check. Everything else here guards the
operational edges — credentials, key placement, API refusal, and the
promise that no secret value ever reaches a log line.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import _github_fake

from ranex.foundation.canonical import canonical_sha256
from ranex.github_app.acceptance import (
    ABSENT_CODE,
    ACCEPTED,
    REJECTED_PREFIX,
    Acceptance,
    code_for_state,
)
from ranex.github_app.binding import PrHeadBinding, subject_digest_for_tree
from ranex.github_app.client import AppCredentials, ClientRefusal
from ranex.github_app.publisher import (
    CONCLUSION_SUCCESS,
    decide_check,
)
from ranex.governed_execution.verdict_reader import ReadState


def binding() -> PrHeadBinding:
    tree = "c" * 40
    return PrHeadBinding(
        head_sha="d" * 40, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )


def verified(verdict: str) -> Acceptance:
    return Acceptance(
        ACCEPTED,
        ReadState.VERIFIED,
        {"verdict": verdict, "gate_id": "landing", "failing_rule": None,
         "missing_claims": [], "record_digest": "sha256:" + canonical_sha256({})},
    )


def test_only_a_verified_pass_reaches_success() -> None:
    assert decide_check(binding(), verified("PASS")).conclusion == CONCLUSION_SUCCESS


def test_a_verified_fail_is_failure_not_success() -> None:
    decision = decide_check(binding(), verified("FAIL"))
    assert decision.conclusion == "failure"
    assert decision.summary.startswith("FAIL")


def test_every_rejected_reader_state_is_failure_naming_its_state() -> None:
    rejected = [
        state for state in ReadState if state not in (ReadState.VERIFIED, ReadState.ABSENT)
    ]
    assert rejected, "the closed reader set must have rejection states"
    for state in rejected:
        acceptance = Acceptance(f"{REJECTED_PREFIX}{state.value}", state)
        decision = decide_check(binding(), acceptance)
        assert decision.conclusion == "failure", state
        assert state.value in decision.summary, state


def test_absence_is_action_required_never_success() -> None:
    decision = decide_check(binding(), Acceptance(ABSENT_CODE, ReadState.ABSENT))
    assert decision.conclusion == "action_required"


def test_success_is_unreachable_from_every_non_verified_state() -> None:
    # The fail-closed sweep: each state's mapped acceptance, plus a
    # hypothetical unmapped state string, can never yield success.
    for state in ReadState:
        if state is ReadState.VERIFIED:
            continue
        acceptance = Acceptance(code_for_state(state), state)
        assert decide_check(binding(), acceptance).conclusion != CONCLUSION_SUCCESS
    unknown = Acceptance(f"{REJECTED_PREFIX}never-heard-of", ReadState.MALFORMED)
    assert decide_check(binding(), unknown).conclusion != CONCLUSION_SUCCESS


def test_credentials_refuse_when_any_variable_is_unset(tmp_path: Path) -> None:
    environment = {
        "RANEX_GITHUB_APP_ID": "1",
        "RANEX_GITHUB_APP_PRIVATE_KEY": str(tmp_path / "app.pem"),
        "RANEX_GITHUB_WEBHOOK_SECRET": "s",
    }
    for missing in environment:
        partial = {key: value for key, value in environment.items() if key != missing}
        os.environ.update(partial)
        try:
            try:
                AppCredentials.from_environment(tmp_path)
            except ClientRefusal as refusal:
                assert refusal.code == "E-GITHUB-CREDENTIALS-ABSENT"
                assert missing in refusal.detail
            else:
                raise AssertionError(f"{missing} unset must refuse")
        finally:
            for key in partial:
                os.environ.pop(key, None)


def test_a_key_inside_the_repository_is_refused(tmp_path: Path) -> None:
    os.environ.update(
        {
            "RANEX_GITHUB_APP_ID": "1",
            "RANEX_GITHUB_APP_PRIVATE_KEY": str(tmp_path / "inside.pem"),
            "RANEX_GITHUB_WEBHOOK_SECRET": "s",
        }
    )
    try:
        try:
            AppCredentials.from_environment(tmp_path)
        except ClientRefusal as refusal:
            assert refusal.code == "E-GITHUB-KEY-INSIDE-REPO"
        else:
            raise AssertionError("a key inside the repository must refuse")
    finally:
        for key in (
            "RANEX_GITHUB_APP_ID",
            "RANEX_GITHUB_APP_PRIVATE_KEY",
            "RANEX_GITHUB_WEBHOOK_SECRET",
        ):
            os.environ.pop(key, None)


def cli_env(fake_url: str, key_path: Path) -> dict[str, str]:
    return {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
        "RANEX_GITHUB_APP_ID": _github_fake.APP_ID,
        "RANEX_GITHUB_APP_PRIVATE_KEY": str(key_path),
        "RANEX_GITHUB_WEBHOOK_SECRET": "webhook-secret-value",
        "RANEX_GITHUB_API_ROOT": fake_url,
    }


def test_the_cli_refuses_an_api_error_without_retrying(tmp_path: Path) -> None:
    clone, head = _github_fake.seeded_governed_clone(tmp_path / "clone")
    key_path, public = _github_fake.write_app_key(tmp_path / "keys")
    with _github_fake.FakeGitHub(public) as fake:
        fake.fail_check_runs_with = 502
        result = subprocess.run(
            [
                "python", "-m", "ranex.cli.main",
                "github", "check", "publish",
                "--head-sha", head, "--installation", "1", "--repo", "owner/name",
                "--repository", str(clone), "--approver", "operator",
            ],
            capture_output=True, text=True, check=False,
            env=cli_env(fake.url, key_path),
        )

    assert result.returncode == 2
    assert "E-GITHUB-API-REFUSED" in result.stderr
    assert "502" in result.stderr
    # Exactly one check-run POST: a refusal is loud, never a quiet retry.
    assert len(fake.check_requests) == 1


def test_no_secret_value_reaches_the_output(tmp_path: Path) -> None:
    clone, head = _github_fake.seeded_governed_clone(tmp_path / "clone")
    key_path, public = _github_fake.write_app_key(tmp_path / "keys")
    with _github_fake.FakeGitHub(public) as fake:
        result = subprocess.run(
            [
                "python", "-m", "ranex.cli.main",
                "github", "check", "publish",
                "--head-sha", head, "--installation", "1", "--repo", "owner/name",
                "--repository", str(clone), "--approver", "operator",
            ],
            capture_output=True, text=True, check=False,
            env=cli_env(fake.url, key_path),
        )

    assert result.returncode == 0, result.stderr
    emitted = result.stdout + result.stderr
    assert "PRIVATE KEY" not in emitted
    assert key_path.read_text(encoding="ascii") not in emitted
    assert _github_fake.INSTALLATION_TOKEN not in emitted
    assert "webhook-secret-value" not in emitted


def test_a_malformed_key_file_refuses_cleanly(tmp_path: Path) -> None:
    clone, head = _github_fake.seeded_governed_clone(tmp_path / "clone")
    key_path = tmp_path / "not-a-key.pem"
    key_path.write_text("this is not a PEM key\n", encoding="ascii")
    with _github_fake.FakeGitHub(b"unused") as fake:
        result = subprocess.run(
            [
                "python", "-m", "ranex.cli.main",
                "github", "check", "publish",
                "--head-sha", head, "--installation", "1", "--repo", "owner/name",
                "--repository", str(clone), "--approver", "operator",
            ],
            capture_output=True, text=True, check=False,
            env=cli_env(fake.url, key_path),
        )

    assert result.returncode == 2
    assert "E-GITHUB-KEY-UNREADABLE" in result.stderr
    assert "Traceback" not in result.stderr
