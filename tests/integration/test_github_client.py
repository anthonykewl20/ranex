"""Integration arms for the GitHub App client and check publisher.

Everything speaks to a local fake GitHub — the repo's stdlib HTTPServer
pattern — so no test ever touches the real API, and the fake verifies the
RS256 JWT with the test's own key: the minting is judged by GitHub's
arithmetic, not the minter's self-report.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import _github_fake

from ranex.foundation.canonical import canonical_sha256
from ranex.github_app.acceptance import ACCEPTED, Acceptance
from ranex.github_app.binding import PrHeadBinding, subject_digest_for_tree
from ranex.github_app.client import AppCredentials, GitHubClient, mint_app_jwt
from ranex.github_app.publisher import check_run_body, decide_check, publish_check
from ranex.governed_execution.verdict_reader import ReadState


def clean_env() -> dict[str, str]:
    return {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }


def binding_for(tree: str) -> PrHeadBinding:
    return PrHeadBinding(
        head_sha="f" * 40, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )


def verified_acceptance(binding: PrHeadBinding, *, verdict: str = "PASS") -> Acceptance:
    record = {
        "verdict": verdict,
        "gate_id": "landing",
        "subject_digest": binding.subject_digest,
        "record_digest": "sha256:" + canonical_sha256({"subject": binding.subject_digest}),
    }
    return Acceptance(ACCEPTED, ReadState.VERIFIED, record)


def test_minted_jwt_carries_the_documented_claims_window(tmp_path: Path) -> None:
    key_path, public = _github_fake.write_app_key(tmp_path)
    credentials = AppCredentials(
        app_id=_github_fake.APP_ID,
        private_key_path=key_path,
        webhook_secret="secret",
    )

    before = time.time()
    token = mint_app_jwt(credentials)
    claims = _github_fake.verify_jwt(token, public)
    after = time.time()

    assert claims["iss"] == _github_fake.APP_ID
    assert claims["iat"] <= after - 59
    assert claims["iat"] >= before - 61
    assert claims["exp"] <= after + 600
    assert claims["exp"] >= before + 599


def test_installation_token_is_exchanged_once_and_cached(tmp_path: Path) -> None:
    key_path, public = _github_fake.write_app_key(tmp_path)
    with _github_fake.FakeGitHub(public) as fake:
        client = GitHubClient(
            AppCredentials(_github_fake.APP_ID, key_path, "secret"),
            api_root=fake.url,
        )
        first = client.installation_token(1)
        second = client.installation_token(1)

    assert first == second == _github_fake.INSTALLATION_TOKEN
    assert fake.token_requests == 1
    assert fake.jwt_claims[0]["iss"] == _github_fake.APP_ID


def test_an_expired_token_re_exchanges_on_the_next_call(tmp_path: Path) -> None:
    key_path, public = _github_fake.write_app_key(tmp_path)
    clock = {"now": time.time()}
    with _github_fake.FakeGitHub(public) as fake:
        client = GitHubClient(
            AppCredentials(_github_fake.APP_ID, key_path, "secret"),
            api_root=fake.url,
            now=lambda: clock["now"],
        )
        client.installation_token(1)
        # An hour passes; the cached token is past its refresh margin.
        clock["now"] += 3600
        client.installation_token(1)

    assert fake.token_requests == 2


def test_the_check_run_body_is_exactly_what_the_docs_promise(tmp_path: Path) -> None:
    binding = binding_for("a" * 40)
    decision = decide_check(binding, verified_acceptance(binding))
    body = check_run_body(
        binding, decision, started_at=1_700_000_000.0, completed_at=1_700_000_060.0
    )

    assert body["name"] == "ranex/acceptance"
    assert body["head_sha"] == binding.head_sha
    assert body["status"] == "completed"
    assert body["conclusion"] == "success"
    assert set(body["output"]) == {"title", "summary", "text"}
    assert body["started_at"] == "2023-11-14T22:13:20Z"
    assert body["completed_at"] == "2023-11-14T22:14:20Z"


def test_publish_check_sends_the_bearer_installation_token(tmp_path: Path) -> None:
    key_path, public = _github_fake.write_app_key(tmp_path)
    binding = binding_for("b" * 40)
    with _github_fake.FakeGitHub(public) as fake:
        client = GitHubClient(
            AppCredentials(_github_fake.APP_ID, key_path, "secret"),
            api_root=fake.url,
        )
        decision, response = publish_check(
            client,
            1,
            "owner/name",
            binding,
            verified_acceptance(binding),
            started_at=time.time(),
            completed_at=time.time(),
        )

        assert decision.conclusion == "success"
        assert response["id"] == 424242
        assert len(fake.check_requests) == 1
        request = fake.check_requests[0]
        assert str(request["path"]).endswith("/repos/owner/name/check-runs")
        # The check run is authorized by the installation token, never the
        # app JWT — one token, one audience, no substitution.
        assert request["authorization"] == f"Bearer {_github_fake.INSTALLATION_TOKEN}"
        assert request["accept"] == "application/vnd.github+json"
        assert request["api_version"] == "2026-03-10"
        assert request["body"]["name"] == "ranex/acceptance"


def test_the_cli_publishes_from_a_verified_verdict(tmp_path: Path) -> None:
    clone, head = _github_fake.seeded_governed_clone(tmp_path / "clone")
    key_path, public = _github_fake.write_app_key(tmp_path / "keys")
    with _github_fake.FakeGitHub(public) as fake:
        environment = dict(clean_env())
        environment.update(
            {
                "RANEX_GITHUB_APP_ID": _github_fake.APP_ID,
                "RANEX_GITHUB_APP_PRIVATE_KEY": str(key_path),
                "RANEX_GITHUB_WEBHOOK_SECRET": "webhook-secret",
                "RANEX_GITHUB_API_ROOT": fake.url,
            }
        )
        result = subprocess.run(
            [
                "python", "-m", "ranex.cli.main",
                "github", "check", "publish",
                "--head-sha", head,
                "--installation", "1",
                "--repo", "owner/name",
                "--repository", str(clone),
                "--approver", "operator",
            ],
            capture_output=True, text=True, check=False, env=environment,
        )

    assert result.returncode == 0, result.stderr
    assert "PUBLISHED  ranex/acceptance" in result.stdout
    assert "conclusion=success" in result.stdout
    assert len(fake.check_requests) == 1
    assert fake.check_requests[0]["body"]["conclusion"] == "success"
    assert fake.check_requests[0]["body"]["head_sha"] == head


def test_lists_include_later_pages_and_reconciliation_requests_all_runs(tmp_path: Path) -> None:
    from urllib.parse import parse_qs, urlsplit

    from ranex.github_app.client import list_repository_rulesets

    key_path, public = _github_fake.write_app_key(tmp_path)
    with _github_fake.FakeGitHub(public) as fake:
        client = GitHubClient(AppCredentials(_github_fake.APP_ID, key_path, "secret"), api_root=fake.url)
        fake.installation_list = [{"id": i} for i in range(105)]
        fake.rulesets = [{"id": i, "rules": []} for i in range(105)]
        assert client.list_installations() == fake.installation_list
        assert list_repository_rulesets("operator", "owner/name", api_root=fake.url) == fake.rulesets
        binding = binding_for("b" * 40)
        for i in range(105):
            client.create_check_run(1, "owner/name", check_run_body(
                binding, decide_check(binding, verified_acceptance(binding)),
                started_at=time.time(), completed_at=time.time(), external_id=f"delivery-{i}",
            ))
        runs = client.list_check_runs(1, "owner/name", binding.head_sha, check_name="ranex/acceptance")
        assert [run["external_id"] for run in runs] == [f"delivery-{i}" for i in range(105)]
        listings = [parse_qs(urlsplit(r["path"]).query) for r in fake.requests if "/commits/" in r["path"]]
        assert [q["page"] for q in listings] == [["1"], ["2"]]
        assert all(q["filter"] == ["all"] for q in listings)


def test_non_rsa_private_key_is_a_named_refusal(tmp_path: Path) -> None:
    import pytest
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    from ranex.github_app.client import ClientRefusal

    path = tmp_path / "wrong-key.pem"
    path.write_bytes(ed25519.Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption(),
    ))
    path.chmod(0o600)
    with pytest.raises(ClientRefusal, match="RSA private key"):
        mint_app_jwt(AppCredentials("123", path, "secret"))


def test_invalid_api_json_is_a_named_refusal() -> None:
    import io
    from unittest.mock import patch

    import pytest

    from ranex.github_app.client import ClientRefusal, _api_request

    for body in (b'<html>upstream unavailable</html>', b'\xff', b'[' * 2000):
        with patch('urllib.request.urlopen', return_value=io.BytesIO(body)):
            with pytest.raises(ClientRefusal, match='response was not valid JSON'):
                _api_request('GET', 'https://api.github.com/app', token='private')


def test_pagination_refuses_malformed_later_pages_and_missing_envelopes() -> None:
    from unittest.mock import Mock

    import pytest

    from ranex.github_app.client import ClientRefusal, _paged_objects

    for bad in ([], {"check_runs": None}, {"check_runs": ["invalid"]}):
        with pytest.raises(ClientRefusal):
            _paged_objects(Mock(return_value=bad), field="check_runs")
    with pytest.raises(ClientRefusal):
        _paged_objects(Mock(side_effect=[[{"id": i} for i in range(100)], {}]))
    with pytest.raises(ClientRefusal, match="exceeded 1000 pages"):
        _paged_objects(Mock(return_value=[{"id": i} for i in range(100)]))


def test_truncated_http_response_is_a_retryable_client_refusal() -> None:
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    import pytest

    from ranex.github_app.client import ClientRefusal, _api_request

    class Truncated(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Length", "100")
            self.end_headers()
            self.wfile.write(b"{}")
            self.close_connection = True

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Truncated)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        with pytest.raises(ClientRefusal, match="E-GITHUB-API-REFUSED"):
            _api_request("GET", f"http://127.0.0.1:{server.server_port}/app", token="test-only")
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_error_response_with_reset_body_preserves_http_status() -> None:
    import io
    from unittest.mock import patch
    from urllib.error import HTTPError

    import pytest

    from ranex.github_app.client import ClientRefusal, _api_request

    class ResetBody(io.BytesIO):
        def read(self, *args, **kwargs):
            raise ConnectionResetError("peer reset the error body")

    error = HTTPError("https://api.github.com/app", 503, "unavailable", {}, ResetBody())
    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(ClientRefusal, match="HTTP 503 response body unavailable"):
            _api_request("GET", "https://api.github.com/app", token="test-only")
