"""The registration surface, branch by branch, through the real CLI and API shapes.

Complements test_github_registration.py: stored credentials drive `status`
and `ruleset`; the redirect catcher completes a handshake end to end; a
foreign pin is reported, not replaced; and every shapeless API answer, bad
manifest field and damaged credential store is a named refusal.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import _github_fake
import pytest

from ranex.github_app import client as client_module
from ranex.github_app import registration
from ranex.github_app.client import (
    AppCredentials,
    ClientRefusal,
    GitHubClient,
    complete_repository_rulesets,
    convert_app_manifest,
    create_repository_ruleset,
    get_repository_ruleset,
    list_repository_rulesets,
    operator_token_from_environment,
)
from ranex.github_app.publisher import CHECK_NAME
from ranex.github_app.registration import (
    acceptance_pin,
    app_manifest,
    convert_and_store,
    load_stored_identity,
    manifest_form_html,
    pin_acceptance_ruleset,
    ruleset_body,
    serve_manifest_redirect,
    store_credentials,
    web_root_from_environment,
)


def clean_env(**extra: str) -> dict[str, str]:
    env = {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }
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
        capture_output=True, text=True, check=False, env=env, timeout=120,
    )


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _conversion(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": 7, "slug": "ranex", "html_url": "https://github.com/apps/ranex",
        "pem": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        "webhook_secret": "s",
    }
    base.update(overrides)
    return base


def test_stored_credentials_drive_status_and_ruleset(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        fake.public_pem = fake.conversion_public_pem
        convert_and_store(fake.conversion_code, keys, repository_root=repo, api_root=fake.url)
        env = clean_env(
            RANEX_GITHUB_API_ROOT=fake.url, RANEX_GITHUB_OPERATOR_TOKEN=_github_fake.OPERATOR_TOKEN,
        )
        # A ruleset without the check is walked past; a foreign pin is reported.
        fake.rulesets.append({"id": 1, "name": "other", "rules": []})
        fake.rulesets.append({"id": 2, "name": "foreign", "rules": [{
            "type": "required_status_checks",
            "parameters": {"required_status_checks": [{"context": CHECK_NAME, "integration_id": 4242}]},
        }]})
        status = invoke(
            "github", "status", "--credentials-dir", str(keys), "--repo", "owner/name",
            "--repository", str(repo), env=env,
        )
        assert status.returncode == 1, status.stdout + status.stderr
        assert f"APP  id={_github_fake.APP_ID_INT}" in status.stdout
        assert "installation=99" in status.stdout
        assert "pinned to integration_id=4242" in status.stdout

        fake.installation_list = []
        uninstalled = invoke(
            "github", "status", "--credentials-dir", str(keys), "--repository", str(repo), env=env,
        )
        assert uninstalled.returncode == 0, uninstalled.stderr
        assert "installations=none" in uninstalled.stdout

        conflict = invoke(
            "github", "ruleset", "--credentials-dir", str(keys), "--repo", "owner/name",
            "--branch", "main", "--repository", str(repo), env=env,
        )
        assert conflict.returncode == 2
        assert "E-GITHUB-RULESET-CONFLICT" in conflict.stderr
        assert len(fake.rulesets) == 2

        fake.rulesets.pop()
        created = invoke(
            "github", "ruleset", "--credentials-dir", str(keys), "--repo", "owner/name",
            "--branch", "main", "--repository", str(repo), env=env,
        )
        assert created.returncode == 0, created.stderr
        assert f"created  app_id={_github_fake.APP_ID_INT}" in created.stdout

        # A credentials store inside the governed repository is refused even
        # when its identity file is perfectly readable.
        inside = repo / "keys"
        inside.mkdir()
        for name in ("app.pem", "webhook-secret", "identity.json"):
            (inside / name).write_bytes((keys / name).read_bytes())
        refused = invoke(
            "github", "status", "--credentials-dir", str(inside), "--repository", str(repo), env=env,
        )
        assert refused.returncode == 2
        assert "E-GITHUB-KEY-INSIDE-REPO" in refused.stderr


def test_register_prints_the_form_and_completes_a_served_handshake(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        env = clean_env(RANEX_GITHUB_API_ROOT=fake.url)
        common = [
            "github", "register", "--credentials-dir", str(keys),
            "--webhook-url", "https://receiver.example/webhook", "--repository", str(repo),
        ]
        printed = invoke(*common, "--print-form", env=env)
        assert printed.returncode == 0, printed.stderr
        assert "REGISTER  open http://127.0.0.1:" in printed.stdout
        assert 'name="manifest"' in printed.stdout
        assert not keys.exists()

        bad_bind = invoke(*common, "--bind", "nowhere", env=env)
        assert bad_bind.returncode == 2
        assert "--bind expects host:port" in bad_bind.stderr

        no_hook = invoke(
            "github", "register", "--credentials-dir", str(keys), "--repository", str(repo), env=env,
        )
        assert no_hook.returncode == 2
        assert "E-GITHUB-WEBHOOK-NOT-HTTPS" in no_hook.stderr

        port = _free_port()
        process = subprocess.Popen(
            ["python", "-m", "ranex.cli.main", *common, "--bind", f"127.0.0.1:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )
        try:
            form = None
            for _ in range(100):
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                        form = response.read().decode()
                    break
                except OSError:
                    time.sleep(0.1)
            assert form is not None, "the redirect catcher never listened"
            state = re.search(r"new\?state=([A-Za-z0-9_.~%-]+)", form).group(1)
            with urlopen(
                f"http://127.0.0.1:{port}/redirect?code={fake.conversion_code}&state={state}",
                timeout=5,
            ) as response:
                assert response.status == 200
            stdout, stderr = process.communicate(timeout=60)
        finally:
            if process.poll() is None:
                process.kill()
        assert process.returncode == 0, stderr
        assert "REGISTERED" in stdout
        assert _github_fake.WEBHOOK_SECRET_CONVERTED not in stdout + stderr
        assert (keys / "identity.json").is_file()


def test_the_redirect_catcher_serves_the_form_and_refuses_other_paths() -> None:
    form = manifest_form_html(
        app_manifest(name="ranex", homepage="https://ranex.dev",
                     webhook_url="https://receiver.example/webhook"),
        state="s", web_root="https://github.example",
    )
    ready = threading.Event()
    captured: dict[str, object] = {}

    def on_listen(server):
        captured["port"] = server.server_address[1]
        ready.set()

    worker = threading.Thread(
        target=lambda: captured.update(server=serve_manifest_redirect(
            ("127.0.0.1", 0), state="s", form_html=form, on_listen=on_listen)),
        daemon=True,
    )
    worker.start()
    assert ready.wait(5)
    base = f"http://127.0.0.1:{captured['port']}"
    with urlopen(f"{base}/", timeout=5) as response:
        assert "https://github.example/settings/apps/new?state=s" in response.read().decode()
    with pytest.raises(HTTPError) as missing:
        urlopen(Request(f"{base}/nope"), timeout=5)
    assert missing.value.code == 404
    with urlopen(f"{base}/redirect?code=good-code&state=s", timeout=5) as response:
        assert response.status == 200
    worker.join(5)
    assert captured["server"].code == "good-code"


def test_manifest_fields_and_web_root_are_validated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(registration.WEB_ROOT_VARIABLE, "https://ghe.example/")
    assert web_root_from_environment() == "https://ghe.example"
    with pytest.raises(ClientRefusal, match="invalid App name"):
        app_manifest(name="bad name", homepage="https://r.dev", webhook_url="https://h/x")
    with pytest.raises(ClientRefusal, match="redirect must be an absolute URL"):
        app_manifest(name="ranex", homepage="https://r.dev", webhook_url="https://h/x",
                     redirect_url="/relative")
    with pytest.raises(ClientRefusal, match="invalid branch name"):
        ruleset_body(1, "../main")


def test_the_credential_store_refuses_every_malformed_conversion(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with pytest.raises(ClientRefusal, match="absolute path"):
        store_credentials(Path("relative/keys"), _conversion(), repository_root=repo)
    cases = [
        ({"id": None}, "conversion response lacked" if False else "not a positive integer"),
        ({"pem": "nope"}, "not a PEM"),
        ({"webhook_secret": ""}, "webhook_secret is empty"),
    ]
    for override, message in cases:
        with pytest.raises(ClientRefusal, match=message):
            store_credentials(keys, _conversion(**override), repository_root=repo)
    lacking = _conversion()
    del lacking["pem"]
    with pytest.raises(ClientRefusal, match="conversion response lacked"):
        store_credentials(keys, lacking, repository_root=repo)
    assert not keys.exists() or not any(keys.iterdir())

    with patch.object(registration.os, "readlink", side_effect=OSError("no proc")):
        with pytest.raises(ClientRefusal, match="E-GITHUB-KEY-UNREADABLE"):
            store_credentials(keys, _conversion(), repository_root=repo)

    # A PEM and secret without trailing newlines are stored newline-terminated.
    stored = store_credentials(keys, _conversion(slug=None, html_url=None), repository_root=repo)
    assert (stored / "app.pem").read_bytes().endswith(b"-----END PRIVATE KEY-----\n")
    assert (stored / "webhook-secret").read_bytes() == b"s\n"
    assert load_stored_identity(stored) == {"app_id": 7, "slug": "", "html_url": ""}

    with pytest.raises(ClientRefusal, match="E-GITHUB-CREDENTIALS-ABSENT"):
        load_stored_identity(tmp_path / "absent")
    (stored / "identity.json").write_bytes(b'{"app_id": "7"}')
    with pytest.raises(ClientRefusal, match="missing app_id"):
        load_stored_identity(stored)


def test_acceptance_pin_reads_only_well_formed_rulesets() -> None:
    assert acceptance_pin({"rules": "no"}) is None
    assert acceptance_pin({"rules": ["x", {"type": "other"}]}) is None
    assert acceptance_pin({"rules": [{"type": "required_status_checks", "parameters": []}]}) is None
    assert acceptance_pin({"rules": [{"type": "required_status_checks",
                                      "parameters": {"required_status_checks": {}}}]}) is None
    assert acceptance_pin({"rules": [{"type": "required_status_checks", "parameters": {
        "required_status_checks": ["x", {"context": CHECK_NAME, "integration_id": "1"},
                                   {"context": CHECK_NAME, "integration_id": 5}]}}]}) == 5


def test_every_shapeless_api_answer_is_a_named_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(client_module.OPERATOR_TOKEN_VARIABLE, raising=False)
    monkeypatch.delenv(client_module.OPERATOR_TOKEN_FALLBACK, raising=False)
    with pytest.raises(ClientRefusal, match="E-GITHUB-OPERATOR-TOKEN-ABSENT"):
        operator_token_from_environment()
    monkeypatch.setenv(client_module.OPERATOR_TOKEN_FALLBACK, "fallback")
    assert operator_token_from_environment() == "fallback"

    # A closed port is a transport refusal, not a traceback.
    with pytest.raises(ClientRefusal, match="E-GITHUB-API-REFUSED"):
        convert_app_manifest("code", api_root=f"http://127.0.0.1:{_free_port()}")

    shapeless = [
        (lambda: convert_app_manifest("code"), []),
        (lambda: list_repository_rulesets("t", "o/n"), {}),
        (lambda: create_repository_ruleset("t", "o/n", {}), []),
        (lambda: get_repository_ruleset("t", "o/n", 1), []),
    ]
    for call, answer in shapeless:
        with patch.object(client_module, "_api_request", return_value=answer):
            with pytest.raises(ClientRefusal, match="E-GITHUB-API-REFUSED"):
                call()

    key_path, public = _github_fake.write_app_key(tmp_path / "keys")
    client = GitHubClient(AppCredentials("1", key_path, "s"), api_root="http://127.0.0.1:9")
    for method, answer in (("app_identity", {"id": "x"}), ("list_installations", {})):
        with patch.object(client, "_request", return_value=answer):
            with pytest.raises(ClientRefusal, match="E-GITHUB-API-REFUSED"):
                getattr(client, method)()

    # Summaries without rules are completed by id; an id-less one is kept as is.
    with _github_fake.FakeGitHub(public) as fake:
        fake.rulesets.append({"id": 3, "name": "full", "rules": []})
        completed = complete_repository_rulesets(
            "t", "owner/name",
            [{"id": 3}, {"name": "no-id"}, {"id": 4, "rules": []}],
            api_root=fake.url,
        )
        assert completed == [{"id": 3, "name": "full", "rules": []}, {"name": "no-id"},
                             {"id": 4, "rules": []}]
        assert pin_acceptance_ruleset("t", "owner/name", 9, branch="main", api_root=fake.url) == "created"
        assert json.loads(json.dumps(fake.rulesets[-1]))["rules"][0]["type"] == "required_status_checks"


def test_a_served_handshake_with_a_wrong_state_converts_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    keys = tmp_path / "keys"
    with _github_fake.FakeGitHub(b"") as fake:
        port = _free_port()
        process = subprocess.Popen(
            ["python", "-m", "ranex.cli.main", "github", "register", "--credentials-dir", str(keys),
             "--webhook-url", "https://receiver.example/webhook", "--repository", str(repo),
             "--bind", f"127.0.0.1:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=clean_env(RANEX_GITHUB_API_ROOT=fake.url),
        )
        try:
            for _ in range(100):
                try:
                    with urlopen(f"http://127.0.0.1:{port}/", timeout=2):
                        break
                except OSError:
                    time.sleep(0.1)
            with pytest.raises(HTTPError) as refused:
                urlopen(f"http://127.0.0.1:{port}/redirect?code={fake.conversion_code}&state=wrong",
                        timeout=5)
            assert refused.value.code == 403
            stdout, stderr = process.communicate(timeout=60)
        finally:
            if process.poll() is None:
                process.kill()
        assert process.returncode == 2
        assert "E-GITHUB-BAD-MANIFEST-CODE state-mismatch" in stderr
        assert fake.conversion_requests == []
        assert not keys.exists()


def test_the_store_refuses_a_stalled_write_and_a_directory_that_turns_out_committable(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    with patch.object(registration.os, "write", return_value=0):
        with pytest.raises(OSError, match="made no progress"):
            store_credentials(tmp_path / "stalled", _conversion(), repository_root=repo)
    # The exclusive create happened; the stalled write left it empty, and a
    # rerun refuses to overwrite it (the operator removes it deliberately).
    assert (tmp_path / "stalled" / "app.pem").read_bytes() == b""
    with pytest.raises(ClientRefusal, match="E-GITHUB-CREDENTIALS-EXIST"):
        store_credentials(tmp_path / "stalled", _conversion(), repository_root=repo)
    # The path check passed, but the opened directory resolves into the
    # repository (a swap between the two): still refused, nothing written.
    with patch.object(registration, "committable_into", side_effect=[False, True]):
        with pytest.raises(ClientRefusal, match="E-GITHUB-KEY-INSIDE-REPO"):
            store_credentials(tmp_path / "swapped", _conversion(), repository_root=repo)
    assert not (tmp_path / "swapped" / "app.pem").exists()
