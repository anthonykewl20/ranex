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
