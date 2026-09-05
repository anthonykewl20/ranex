"""Probe the real receiver over TCP and process restarts, without a fake API.

All deliveries and credentials are local audit fixtures. No check is published
to GitHub. Retry tests use a real, unavailable local Git remote. These probes
cover the receiving boundary; live GitHub authentication remains UNVERIFIED.
Exit 1 reports reproduced gaps, exit 2 an incomplete audit.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import http.client
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

REPO = Path(__file__).resolve().parents[2]
SECRET = "local-audit-fixture-not-a-github-credential"
SERVER = """
import sys
from pathlib import Path
from ranex.github_app.client import AppCredentials, GitHubClient
from ranex.github_app.receiver import ReceiverConfig, serve
root = Path(sys.argv[1])
config = ReceiverConfig(
    repo_root=root / 'repo', remote=str(root / 'missing-remote'),
    verdicts_dir=root / 'verdicts', keyring={}, gate_id='landing',
    catalog_digest=None, approver_id='audit', webhook_secret=sys.argv[3],
    allowlist=frozenset({(1, 'audit/local')}),
    client=GitHubClient(AppCredentials('1', root / 'app.pem', sys.argv[3])),
    state_dir=root / 'state')
serve(config, ('127.0.0.1', int(sys.argv[2])))
"""


def request(port: int, delivery: str, body: bytes = b"{}", *, event: str = "ping",
            signed: bool = True) -> dict:
    headers = {"X-GitHub-Delivery": delivery, "X-GitHub-Event": event}
    if signed:
        headers["X-Hub-Signature-256"] = "sha256=" + hmac.new(
            SECRET.encode(), body, hashlib.sha256).hexdigest()
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("POST", "/webhook", body, headers)
        response = connection.getresponse()
        return {"status": response.status, "body": response.read().decode()}
    except (OSError, http.client.HTTPException) as error:
        return {"error": type(error).__name__, "detail": str(error)}
    finally:
        connection.close()


@contextmanager
def server(root: Path, log: Path):
    with socket.socket() as selector:
        selector.bind(("127.0.0.1", 0))
        port = selector.getsockname()[1]
    env = dict(os.environ, PYTHONPATH=str(REPO / "src"))
    with log.open("a") as output:
        process = subprocess.Popen([sys.executable, "-c", SERVER, str(root), str(port), SECRET],
                                   cwd=root, env=env, stdout=output, stderr=output)
        try:
            deadline = time.monotonic() + 10
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"receiver exited {process.returncode}; see {log}")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=.2):
                        break
                except OSError as error:
                    if time.monotonic() > deadline:
                        raise TimeoutError("receiver did not start") from error
                    time.sleep(.02)
            yield port
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def execute(out: Path) -> list[dict]:
    cases = []

    def record(name: str, verified: bool, observed: object, expectation: str) -> None:
        cases.append({"case": name, "status": "VERIFIED" if verified else "GAP",
                      "expected": expectation, "observed": observed})
        (out / "receipt.json").write_text(json.dumps(cases, indent=2) + "\n")
        print(f"{cases[-1]['status']} {name}", flush=True)

    with tempfile.TemporaryDirectory(prefix="ranex-receiver-audit-") as directory:
        root = Path(directory)
        (root / "repo").mkdir()
        subprocess.run(["git", "init", "-q", str(root / "repo")], check=True)
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        (root / "app.pem").write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
        (root / "app.pem").chmod(0o600)
        log = out / "receiver.log"
        with server(root, log) as port:
            healthy = request(port, "ping-1")
            record("signed-http", healthy.get("status") == 200, healthy, "signed ping returns 200")
            unsigned = request(port, "unsigned", signed=False)
            record("unsigned-http", unsigned.get("status") == 401, unsigned, "unsigned body returns 401")
            request(port, "ping-1")
            journal = root / "state/deliveries.jsonl"
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
            record("dedupe-in-process", rows[-1]["outcome"] == "replayed", rows[-1],
                   "same delivery is a no-op")
            body = json.dumps({"action": "opened", "installation": {"id": 1},
                               "repository": {"full_name": "audit/local"},
                               "pull_request": {"number": 1, "head": {"sha": "9" * 40}}}).encode()
            first = request(port, "fetch-retry", body, event="pull_request")
            second = request(port, "fetch-retry", body, event="pull_request")
            record("retry-after-real-fetch-failure", first.get("status") == second.get("status") == 500,
                   [first, second], "unchanged unavailable Git remote remains retryable on redelivery")
            for name, payload in (("malformed-json", b"{"),
                                  ("malformed-number", body.replace(b'"number": 1', b'"number": "oops"'))):
                result = request(port, name, payload, event="pull_request")
                record(name, result.get("status") == 200, result,
                       "authenticated malformed event is a journaled, named permanent refusal")

        with server(root, log) as port:
            restarted = request(port, "ping-1")
            rows = [json.loads(line) for line in journal.read_text().splitlines()]
            record("dedupe-after-restart", rows[-1]["outcome"] == "replayed",
                   {"response": restarted, "entry": rows[-1]}, "delivery spool survives process restart")

        # Keep the blocking socket alive while a healthy second client tries
        # the listener. Release it and prove the listener recovers. Timeouts
        # are observations over a two-second window, not claims of eternity.
        for name, prefix in (
            ("negative-content-length", b"POST /webhook HTTP/1.1\r\nHost: localhost\r\nContent-Length: -1\r\n\r\n"),
            ("incomplete-body", b"POST /webhook HTTP/1.1\r\nHost: localhost\r\nContent-Length: 20\r\n\r\n{"),
            ("idle-client", b""),
        ):
            with server(root, log) as port:
                blocker = socket.create_connection(("127.0.0.1", port), timeout=2)
                try:
                    if prefix:
                        blocker.sendall(prefix)
                    time.sleep(.1)
                    healthy = request(port, name + "-control")
                finally:
                    blocker.close()
                recovery = request(port, name + "-recovery")
                record(name, healthy.get("status") == 200,
                       {"concurrent_healthy": healthy, "after_release": recovery,
                        "raw_request": prefix.decode()},
                       "one unproven client does not monopolize the single listener")
        (out / "deliveries.jsonl").write_bytes(journal.read_bytes())
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    try:
        cases = execute(out)
    except Exception as error:
        (out / "incomplete.json").write_text(json.dumps({
            "status": "UNVERIFIED", "error": f"{type(error).__name__}: {error}"}) + "\n")
        return 2
    return 1 if any(c["status"] == "GAP" for c in cases) else 0


if __name__ == "__main__":
    raise SystemExit(main())
