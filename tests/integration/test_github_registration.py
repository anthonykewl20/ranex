"""Integration arms for App registration, status and the App-pinned ruleset.

Fake GitHub only. Live App creation, HTTPS delivery and merge refusal stay
UNVERIFIED until a real conversion and installation are observed.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

import _github_fake

from ranex.github_app.client import AppCredentials, GitHubClient
from ranex.github_app.publisher import CHECK_NAME
from ranex.github_app.registration import (
    app_manifest,
    convert_and_store,
    credentials_paths,
    manifest_form_html,
    serve_manifest_redirect,
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


def test_the_frozen_manifest_names_the_documented_permissions_and_https_hook() -> None:
    manifest = app_manifest(
        name="ranex",
        homepage="https://ranex.dev",
        webhook_url="https://receiver.example/webhook",
        redirect_url="http://127.0.0.1:8081/redirect",
    )
    assert manifest["default_permissions"] == {
        "checks": "write", "contents": "read", "pull_requests": "read",
    }
    assert manifest["default_events"] == ["pull_request"]
    assert manifest["hook_attributes"]["url"].startswith("https://")
    assert manifest["public"] is False
    html = manifest_form_html(manifest, state="abc", web_root="https://github.com")
    assert "settings/apps/new?state=abc" in html
    assert "name=\"manifest\"" in html


def test_convert_and_store_writes_0600_credentials_outside_the_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        stored = convert_and_store(
            fake.conversion_code, keys, repository_root=repo, api_root=fake.url,
        )
    key_path, secret_path, identity_path = credentials_paths(stored)
    identity = json.loads(identity_path.read_bytes())
    assert identity["app_id"] == _github_fake.APP_ID_INT
    assert identity["slug"] == "ranex"
    pem = key_path.read_text(encoding="ascii")
    assert pem.startswith("-----BEGIN")
    assert pem.endswith("\n")
    assert secret_path.read_text(encoding="utf-8").strip() == _github_fake.WEBHOOK_SECRET_CONVERTED
    for path in (key_path, secret_path, identity_path):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_github_register_cli_converts_a_code_and_prints_no_secret(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        result = invoke(
            "github", "register",
            "--code", fake.conversion_code,
            "--credentials-dir", str(keys),
            "--webhook-url", "https://receiver.example/webhook",
            "--repository", str(repo),
            env=clean_env(RANEX_GITHUB_API_ROOT=fake.url),
        )
    assert result.returncode == 0, result.stderr
    assert f"app_id={_github_fake.APP_ID_INT}" in result.stdout
    assert "REGISTERED" in result.stdout
    assert _github_fake.WEBHOOK_SECRET_CONVERTED not in result.stdout
    assert _github_fake.WEBHOOK_SECRET_CONVERTED not in result.stderr
    assert "BEGIN" not in result.stdout
    assert (keys / "app.pem").is_file()


def test_github_status_and_ruleset_against_the_fake_api(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    key_path, public = _github_fake.write_app_key(tmp_path / "app-keys")
    with _github_fake.FakeGitHub(public) as fake:
        env = clean_env(
            RANEX_GITHUB_API_ROOT=fake.url,
            RANEX_GITHUB_APP_ID=_github_fake.APP_ID,
            RANEX_GITHUB_APP_PRIVATE_KEY=str(key_path),
            RANEX_GITHUB_WEBHOOK_SECRET="secret",
            RANEX_GITHUB_OPERATOR_TOKEN=_github_fake.OPERATOR_TOKEN,
        )
        status = invoke(
            "github", "status", "--repo", "owner/name", "--repository", str(repo), env=env,
        )
        assert status.returncode == 1, status.stdout + status.stderr
        assert "APP  id=123456" in status.stdout
        assert "installation=99" in status.stdout
        assert "ranex/acceptance not required" in status.stdout

        created = invoke(
            "github", "ruleset", "--repo", "owner/name", "--branch", "main",
            "--repository", str(repo), env=env,
        )
        assert created.returncode == 0, created.stderr
        assert "created" in created.stdout
        assert fake.rulesets[0]["rules"][0]["parameters"]["required_status_checks"][0] == {
            "context": CHECK_NAME, "integration_id": _github_fake.APP_ID_INT,
        }

        again = invoke(
            "github", "ruleset", "--repo", "owner/name", "--branch", "main",
            "--repository", str(repo), env=env,
        )
        assert again.returncode == 0, again.stderr
        assert "existing" in again.stdout
        assert len(fake.rulesets) == 1
        fake.rulesets[0]["enforcement"] = "disabled"
        disabled = invoke(
            "github", "status", "--repo", "owner/name", "--repository", str(repo), env=env,
        )
        assert disabled.returncode == 1, disabled.stdout + disabled.stderr
        assert "not required" in disabled.stdout
        fake.rulesets[0]["enforcement"] = "active"


        pinned = invoke(
            "github", "status", "--repo", "owner/name", "--repository", str(repo), env=env,
        )
        assert pinned.returncode == 0, pinned.stderr
        assert "pinned to this App" in pinned.stdout


def test_a_mismatched_redirect_state_does_not_convert() -> None:
    import threading
    from urllib.error import HTTPError

    form = manifest_form_html(
        app_manifest(
            name="ranex", homepage="https://ranex.dev",
            webhook_url="https://receiver.example/webhook",
        ),
        state="expected-state",
        web_root="https://github.com",
    )
    ready = threading.Event()
    captured: dict[str, object] = {}

    def on_listen(server):
        captured["port"] = server.server_address[1]
        ready.set()

    worker = threading.Thread(
        target=lambda: captured.update(
            server=serve_manifest_redirect(
                ("127.0.0.1", 0), state="expected-state", form_html=form, on_listen=on_listen,
            )
        ),
        daemon=True,
    )
    worker.start()
    assert ready.wait(5)
    url = f"http://127.0.0.1:{captured['port']}/redirect?code=abc&state=wrong"
    try:
        urlopen(Request(url), timeout=5)
    except HTTPError as error:
        captured["status"] = error.code
    else:
        raise AssertionError("a mismatched state must refuse")
    worker.join(5)
    server = captured["server"]
    assert server.code is None
    assert server.error == "state-mismatch"
    assert captured["status"] == 403


def test_status_authenticates_as_the_app_with_a_stored_key(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    key_path, public = _github_fake.write_app_key(tmp_path / "mint")
    with _github_fake.FakeGitHub(public) as fake:
        # Store a conversion PEM that will not mint; status uses env credentials.
        convert_and_store(fake.conversion_code, keys, repository_root=repo, api_root=fake.url)
        client = GitHubClient(
            AppCredentials(_github_fake.APP_ID, key_path, "secret"), api_root=fake.url,
        )
        identity = client.app_identity()
        assert identity["id"] == _github_fake.APP_ID_INT
        assert client.list_installations()[0]["id"] == 99
    assert fake.app_requests


def test_ruleset_pin_does_not_credit_disabled_or_wrong_scope_rules(tmp_path: Path) -> None:
    from copy import deepcopy

    from ranex.github_app.registration import pin_acceptance_ruleset, ruleset_body

    desired = ruleset_body(_github_fake.APP_ID_INT, "main")
    weak = []
    for field, value in (("enforcement", "disabled"), ("enforcement", "evaluate"),
                         ("target", "tag"), ("bypass_actors", [{"actor_id": 1, "actor_type": "Integration", "bypass_mode": "always"}])):
        item = deepcopy(desired)
        item[field] = value
        weak.append(item)
    item = deepcopy(desired)
    item["conditions"]["ref_name"]["include"] = ["refs/heads/other"]
    weak.append(item)
    item = deepcopy(desired)
    item["conditions"]["ref_name"]["exclude"] = ["refs/heads/main"]
    weak.append(item)
    item = deepcopy(desired)
    item["rules"][0]["parameters"]["strict_required_status_checks_policy"] = False
    weak.append(item)
    item = deepcopy(desired)
    item["rules"][0]["parameters"]["do_not_enforce_on_create"] = True
    weak.append(item)
    with _github_fake.FakeGitHub(b"") as fake:
        for existing in weak:
            fake.rulesets = [existing]
            assert pin_acceptance_ruleset("operator", "owner/name", _github_fake.APP_ID_INT,
                                          branch="main", api_root=fake.url) == "created"
            assert fake.rulesets == [existing, {**desired, "id": 7}]
            # GitHub adds this default to the GET response; preserve idempotency.
            fake.rulesets[-1]["rules"][0]["parameters"]["do_not_enforce_on_create"] = False
            # Other valid requirements must not prevent reuse of this rule.
            fake.rulesets[-1]["rules"].insert(0, {"type": "required_linear_history"})
            assert pin_acceptance_ruleset("operator", "owner/name", _github_fake.APP_ID_INT,
                                          branch="main", api_root=fake.url) == "existing"
