"""A hand-rolled fake GitHub: the repo's stdlib-HTTPServer test pattern.

Serves exactly the two endpoints the client speaks to, records every
request for byte-exact assertions, and verifies the RS256 JWT with the
test's own public key — so the minting code is judged by the same
arithmetic GitHub will apply, not by what the code under test says about
itself. Also grows the governed clone a verified verdict publication is
written into, so publisher journeys run against real git stores.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

INSTALLATION_TOKEN = "ghs_integration-fake"
APP_ID = "123456"


def write_app_key(directory: Path) -> tuple[Path, bytes]:
    """A fresh RSA keypair on disk: (private PEM path, public PEM bytes)."""

    directory.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    path = directory / "app.pem"
    path.write_text(private, encoding="ascii")
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return path, public


def verify_jwt(token: str, public_pem: bytes) -> dict[str, object]:
    """Verify the JWT the way GitHub does: RS256 over the signing input."""

    header, claims, signature = token.split(".")
    signing_input = f"{header}.{claims}".encode("ascii")
    public = serialization.load_pem_public_key(public_pem)
    public.verify(
        _b64url_decode(signature),
        signing_input,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    assert json.loads(_b64url_decode(header))["alg"] == "RS256"
    return json.loads(_b64url_decode(claims))


def _b64url_decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))


class FakeGitHub:
    """The API surface the publisher uses, with judgment recorded per request."""

    def __init__(self, public_pem: bytes) -> None:
        self.public_pem = public_pem
        self.requests: list[dict[str, object]] = []
        self.jwt_claims: list[dict[str, object]] = []
        self.token_requests = 0
        self.check_requests: list[dict[str, object]] = []
        self.fail_check_runs_with: int | None = None
        outer = self

        class _Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self) -> None:  # noqa: N802 — stdlib naming
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                outer.requests.append(
                    {
                        "path": self.path,
                        "authorization": self.headers.get("Authorization", ""),
                        "accept": self.headers.get("Accept", ""),
                        "api_version": self.headers.get("X-GitHub-Api-Version", ""),
                        "content_type": self.headers.get("Content-Type", ""),
                        "body": json.loads(body) if body else None,
                    }
                )
                if self.path.endswith("/access_tokens"):
                    outer.token_requests += 1
                    outer.jwt_claims.append(
                        verify_jwt(
                            self.headers.get("Authorization", "").removeprefix(
                                "Bearer "
                            ),
                            outer.public_pem,
                        )
                    )
                    self._json(
                        {
                            "token": INSTALLATION_TOKEN,
                            "expires_at": time.strftime(
                                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 3600)
                            ),
                        }
                    )
                    return
                if self.path.endswith("/check-runs"):
                    outer.check_requests.append(outer.requests[-1])
                    if outer.fail_check_runs_with is not None:
                        self._json(
                            {"message": "faked failure"},
                            status=outer.fail_check_runs_with,
                        )
                        return
                    self._json({"id": 424242, "html_url": "https://example.invalid"},
                               status=201)
                    return
                self._json({"message": "not found"}, status=404)

            def _json(self, payload: dict[str, object], status: int = 200) -> None:
                raw = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def __enter__(self) -> FakeGitHub:
        self.thread.start()
        return self

    def __exit__(self, *exception: object) -> None:
        self._server.shutdown()
        self._server.server_close()


def _git_env() -> dict[str, str]:
    return {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "LC_ALL": "C",
    }


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True, text=True, check=True, env=_git_env(),
    )
    return result.stdout.strip()


def seeded_governed_clone(path: Path) -> tuple[Path, str]:
    """A clone whose committed trust root can verify one verdict publication.

    Commits a minimal gates catalog and producer keyring (verdict signer
    included), then writes a signed PASS verdict for HEAD's tree under the
    publisher's convention. Returns (clone, head_sha).
    """

    from ranex.bootstrap.composition import catalog_digest_for
    from ranex.foundation.canonical import canonical_sha256
    from ranex.foundation.signing import generate_keypair
    from ranex.foundation.verdict_signing import PAYLOAD_TYPE, sign_verdict
    from ranex.github_app.binding import PrHeadBinding, subject_digest_for_tree

    subprocess.run(["git", "init", "-q", str(path)], check=True, env=_git_env())
    _git(path, "config", "user.email", "publisher-test@example.invalid")
    _git(path, "config", "user.name", "Publisher Test")
    signer_private, signer_public = generate_keypair()
    producer_private, producer_public = generate_keypair()
    governance = path / "governance"
    governance.mkdir(parents=True)
    gates = governance / "gates.yaml"
    gates.write_text("gates: {}\n", encoding="utf-8")
    (governance / "producers.yaml").write_text(
        "producers:\n"
        f"  worker: {producer_public}\n"
        "verdict_signer:\n"
        "  id: kernel-verdict-signer\n"
        f"  public_key: {signer_public}\n",
        encoding="utf-8",
    )
    (path / "work.txt").write_text("pull request content\n", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "the PR head and its trust root")
    head = _git(path, "rev-parse", "HEAD")
    tree = _git(path, "rev-parse", "HEAD^{tree}")
    binding = PrHeadBinding(
        head_sha=head, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )
    content = {
        "verdict": "PASS",
        "gate_id": "landing",
        "subject_digest": binding.subject_digest,
        "subject_lane": "PRE_READINESS_PRODUCT_SLICE",
        "catalog_digest": catalog_digest_for(gates.read_bytes()),
        "approver_id": "operator",
        "failing_rule": None,
        "missing_claims": [],
        "considered": [],
        "causes": [],
        "rejections": [],
        "self_approval": False,
        "reason": "publisher integration",
    }
    record = {**content, "record_digest": "sha256:" + canonical_sha256(content)}
    verdicts = governance / "verdicts"
    verdicts.mkdir(parents=True)
    (verdicts / f"{binding.subject_digest.removeprefix('sha256:')}.json").write_text(
        json.dumps(
            {
                "payload_type": PAYLOAD_TYPE,
                "record": record,
                "signatures": [
                    {
                        "signer_id": "kernel-verdict-signer",
                        "signature": sign_verdict(content, signer_private),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path, head


WEBHOOK_SECRET = "webhook-secret-value"


def pull_request_event_body(
    head: str, *, action: str = "opened", repository: str = "owner/name"
) -> bytes:
    """A pull_request delivery body in the shape GitHub sends."""

    return json.dumps(
        {
            "action": action,
            "pull_request": {"number": 7, "head": {"sha": head}},
            "repository": {"full_name": repository},
            "installation": {"id": 1},
        }
    ).encode("utf-8")


@contextmanager
def receiver_environment(tmp_path, *, with_verdict: bool = True):
    """A receiver wired end to end: real git stores, fake GitHub API.

    Yields a config with its own per-call state, the live fake, the
    operator clone, and the PR head SHA everything is bound to.
    """

    from dataclasses import dataclass

    import yaml

    from ranex.bootstrap.composition import catalog_digest_for
    from ranex.github_app.client import AppCredentials, GitHubClient
    from ranex.github_app.receiver import ReceiverConfig, _ReceiverState

    key_path, public = write_app_key(tmp_path / "keys")
    with FakeGitHub(public) as fake:
        source, head = seeded_governed_clone(tmp_path / "source")
        clone = tmp_path / "clone"
        subprocess.run(
            ["git", "clone", "-q", str(source), str(clone)],
            check=True,
            env={"PATH": os.environ["PATH"], "LC_ALL": "C"},
        )
        if with_verdict:
            verdicts = clone / "governance" / "verdicts"
            verdicts.mkdir(parents=True)
            for publication in (source / "governance" / "verdicts").iterdir():
                (verdicts / publication.name).write_bytes(publication.read_bytes())
        document = yaml.safe_load((clone / "governance" / "producers.yaml").read_text())
        config = ReceiverConfig(
            repo_root=clone,
            remote=str(source),
            verdicts_dir=clone / "governance" / "verdicts",
            keyring={"kernel-verdict-signer": document["verdict_signer"]["public_key"]},
            gate_id="landing",
            catalog_digest=catalog_digest_for(
                (clone / "governance" / "gates.yaml").read_bytes()
            ),
            approver_id="operator",
            webhook_secret=WEBHOOK_SECRET,
            allowlist=frozenset({(1, "owner/name")}),
            client=GitHubClient(
                AppCredentials(APP_ID, key_path, WEBHOOK_SECRET), api_root=fake.url
            ),
            state_dir=tmp_path / "state",
        )

        @dataclass
        class _Environment:
            config: object
            state: object
            fake: object
            clone: Path
            head: str

        yield _Environment(
            config=config, state=_ReceiverState(), fake=fake, clone=clone, head=head
        )
