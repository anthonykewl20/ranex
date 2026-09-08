"""Security arms for App registration: HTTPS, overwrite, secrets, pin conflict."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import _github_fake
import pytest

from ranex.github_app.client import ClientRefusal
from ranex.github_app.registration import (
    app_manifest,
    convert_and_store,
    pin_acceptance_ruleset,
    store_credentials,
)


def clean_env(**extra: str) -> dict[str, str]:
    env = {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }
    # CI measures the real CLI journeys through the documented subprocess
    # hook; forward it so these children count toward changed-line coverage.
    for name in ("COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG", "COVERAGE_FILE"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    if env.get("COVERAGE_PROCESS_START") or env.get("COVERAGE_PROCESS_CONFIG"):
        env["PYTHONPATH"] = os.pathsep.join(["src", os.path.join("tests", "e2e", "coverage")])
    env.update(extra)
    return env


def invoke(*arguments: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "-m", "ranex.cli.main", *arguments],
        capture_output=True, text=True, check=False, env=env,
    )


def test_an_http_webhook_url_is_refused() -> None:
    with pytest.raises(ClientRefusal) as raised:
        app_manifest(
            name="ranex",
            homepage="https://ranex.dev",
            webhook_url="http://receiver.example/webhook",
        )
    assert raised.value.code == "E-GITHUB-WEBHOOK-NOT-HTTPS"


def test_credentials_inside_the_repository_are_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ClientRefusal) as raised:
        store_credentials(
            repo / "keys",
            {"id": 1, "pem": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n",
             "webhook_secret": "s"},
            repository_root=repo,
        )
    assert raised.value.code == "E-GITHUB-KEY-INSIDE-REPO"
    assert not (repo / "keys" / "app.pem").exists()


def test_an_existing_credential_file_is_not_overwritten(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        convert_and_store(fake.conversion_code, keys, repository_root=repo, api_root=fake.url)
        with pytest.raises(ClientRefusal) as raised:
            convert_and_store(
                fake.conversion_code, keys, repository_root=repo, api_root=fake.url,
            )
    assert raised.value.code == "E-GITHUB-CREDENTIALS-EXIST"


def test_a_failed_conversion_writes_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        fake.fail_conversion_with = 422
        with pytest.raises(ClientRefusal) as raised:
            convert_and_store(
                fake.conversion_code, keys, repository_root=repo, api_root=fake.url,
            )
    assert raised.value.code == "E-GITHUB-API-REFUSED"
    assert not keys.exists() or not (keys / "app.pem").exists()


def test_a_malformed_conversion_code_is_refused_without_network(tmp_path: Path) -> None:
    with pytest.raises(ClientRefusal) as raised:
        convert_and_store("../x", tmp_path / "keys", repository_root=tmp_path / "repo")
    assert raised.value.code == "E-GITHUB-BAD-MANIFEST-CODE"


def test_register_cli_refuses_http_webhook(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    result = invoke(
        "github", "register", "--print-form",
        "--credentials-dir", str(tmp_path / "keys"),
        "--webhook-url", "http://127.0.0.1/webhook",
        "--repository", str(repo),
        env=clean_env(),
    )
    assert result.returncode == 2
    assert "E-GITHUB-WEBHOOK-NOT-HTTPS" in result.stderr


def test_ruleset_without_operator_token_is_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    key_path, _ = _github_fake.write_app_key(tmp_path / "keys")
    env = clean_env(
        RANEX_GITHUB_APP_ID=_github_fake.APP_ID,
        RANEX_GITHUB_APP_PRIVATE_KEY=str(key_path),
        RANEX_GITHUB_WEBHOOK_SECRET="secret",
    )
    env.pop("GITHUB_TOKEN", None)
    result = invoke(
        "github", "ruleset", "--repo", "owner/name", "--repository", str(repo), env=env,
    )
    assert result.returncode == 2
    assert "E-GITHUB-OPERATOR-TOKEN-ABSENT" in result.stderr


def test_a_foreign_integration_id_is_a_conflict_not_a_replacement(tmp_path: Path) -> None:
    key_path, public = _github_fake.write_app_key(tmp_path / "keys")
    with _github_fake.FakeGitHub(public) as fake:
        fake.rulesets = [{
            "id": 1,
            "name": "other",
            "rules": [{
                "type": "required_status_checks",
                "parameters": {
                    "required_status_checks": [
                        {"context": "ranex/acceptance", "integration_id": 999},
                    ],
                },
            }],
        }]
        with pytest.raises(ClientRefusal) as raised:
            pin_acceptance_ruleset(
                "token", "owner/name", _github_fake.APP_ID_INT,
                branch="main", api_root=fake.url,
            )
    assert raised.value.code == "E-GITHUB-RULESET-CONFLICT"
    assert len(fake.rulesets) == 1


def test_stored_key_mode_is_owner_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        convert_and_store(fake.conversion_code, keys, repository_root=repo, api_root=fake.url)
    mode = stat.S_IMODE((keys / "app.pem").stat().st_mode)
    assert mode & 0o077 == 0


def test_matching_rule_does_not_hide_a_later_foreign_pin(tmp_path: Path) -> None:
    from ranex.github_app.registration import ruleset_body

    with _github_fake.FakeGitHub(b"") as fake:
        fake.rulesets = [ruleset_body(123, "main"), ruleset_body(999, "main")]
        with pytest.raises(ClientRefusal, match="E-GITHUB-RULESET-CONFLICT"):
            pin_acceptance_ruleset("token", "owner/name", 123, branch="main", api_root=fake.url)
        assert len(fake.rulesets) == 2
