"""Observe production gaps using real Git/HTTP and a local fake GitHub API.

No live GitHub calls or production credentials are used. Fault injection is
explicit; the output records observed behavior, not a production PASS.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import hmac
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
import _github_fake  # noqa: E402

from ranex.github_app import receiver  # noqa: E402
from ranex.github_app.client import AppCredentials, ClientRefusal, mint_app_jwt  # noqa: E402


def delayed_publication(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root) as env:
        server = receiver._BoundedServer(
            ("127.0.0.1", 0), receiver.build_handler(env.config, env.state),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        original = env.config.client.create_check_run

        def slow(*args, **kwargs):
            time.sleep(11)
            return original(*args, **kwargs)

        body = _github_fake.pull_request_event_body(env.head)
        signature = "sha256=" + hmac.new(
            _github_fake.WEBHOOK_SECRET.encode(), body, hashlib.sha256,
        ).hexdigest()
        request = Request(
            f"http://127.0.0.1:{server.server_address[1]}/webhook", data=body,
            headers={"X-Hub-Signature-256": signature,
                     "X-GitHub-Delivery": "slow-publication",
                     "X-GitHub-Event": "pull_request"},
        )
        try:
            with patch.object(env.config.client, "create_check_run", slow):
                started = time.monotonic()
                with urlopen(request, timeout=25) as response:
                    status = response.status
                    response.read()
                elapsed = time.monotonic() - started
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
        deadline = time.monotonic() + 30
        while len(env.fake.check_requests) < 1 and time.monotonic() < deadline:
            time.sleep(0.1)
        return {"injection": "11-second check-publication delay",
                "http_status": status, "response_seconds": elapsed,
                "within_github_10_second_deadline": elapsed < 10,
                "published_checks": len(env.fake.check_requests),
                "completed_after_acknowledgement": (
                    env.config.state_dir / "completed" / "slow-publication.json").exists()}


def late_verdict(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root, with_verdict=False) as env:
        body = _github_fake.pull_request_event_body(env.head)

        def deliver(identifier):
            return receiver.process_delivery(
                env.config, env.state, body, identifier, "pull_request",
            )

        first = deliver("late-verdict")
        before = [r["body"]["conclusion"] for r in env.fake.check_requests]
        env.config.verdicts_dir.mkdir(parents=True, exist_ok=True)
        for path in (root / "source/governance/verdicts").iterdir():
            (env.config.verdicts_dir / path.name).write_bytes(path.read_bytes())
        replay = deliver("late-verdict")
        after_replay = [r["body"]["conclusion"] for r in env.fake.check_requests]
        fresh = deliver("late-verdict-fresh-event")
        return {"initial_status": first, "initial_conclusions": before,
                "same_delivery_status": replay, "after_same_delivery": after_replay,
                "fresh_event_status": fresh,
                "after_fresh_event": [r["body"]["conclusion"] for r in env.fake.check_requests],
                "automatic_refresh": False}


def completion_failure(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root) as env:
        body = _github_fake.pull_request_event_body(env.head)
        original = receiver.write_atomic

        def fail_completion(path, *args, **kwargs):
            if Path(path).parent.name == "completed":
                raise OSError("injected completion persistence failure")
            return original(path, *args, **kwargs)

        failure = None
        with patch.object(receiver, "write_atomic", fail_completion):
            try:
                receiver.process_delivery(env.config, env.state, body, "crash-window", "pull_request")
            except OSError as error:
                failure = str(error)
        before = len(env.fake.check_requests)
        status = receiver.process_delivery(env.config, env.state, body, "crash-window", "pull_request")
        return {"injection": failure, "checks_before_retry": before,
                "retry_status": status, "checks_after_retry": len(env.fake.check_requests),
                "conclusions": [r["body"]["conclusion"] for r in env.fake.check_requests]}


def persisted_state(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root) as env:
        body = _github_fake.pull_request_event_body(env.head)
        env.config.state_dir.mkdir(parents=True)
        with (env.config.state_dir / "receiver.lock").open("a") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            busy = receiver.process_delivery(env.config, env.state, body, "busy", "pull_request")
        recovered = receiver.process_delivery(env.config, env.state, body, "busy", "pull_request")
        conflict = receiver.process_delivery(
            env.config, env.state, body + b" ", "busy", "pull_request",
        )
        restarted = receiver.process_delivery(
            env.config, receiver._ReceiverState(), body, "busy", "pull_request",
        )
        return {"busy_status": busy, "after_lock_release": recovered,
                "conflicting_body_status": conflict, "restart_replay_status": restarted,
                "published_checks": len(env.fake.check_requests),
                "control_passed": (busy, recovered, conflict, restarted,
                                   len(env.fake.check_requests)) == (503, 200, 409, 200, 1)}


def http_refusals(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root) as env:
        server = receiver._BoundedServer(
            ("127.0.0.1", 0), receiver.build_handler(env.config, env.state),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        body = _github_fake.pull_request_event_body(env.head)
        signature = "sha256=" + hmac.new(
            _github_fake.WEBHOOK_SECRET.encode(), body, hashlib.sha256,
        ).hexdigest()
        cases = [
            ("unsigned", body, {}, "/webhook", 401),
            ("tampered", body + b" ", {"X-Hub-Signature-256": signature}, "/webhook", 401),
            ("invalid-id", body, {"X-Hub-Signature-256": signature,
                                  "X-GitHub-Delivery": "../escape"}, "/webhook", 400),
            ("wrong-endpoint", body, {}, "/other", 404),
            ("oversized", b"", {"Content-Length": str(receiver.MAX_BODY_BYTES + 1)}, "/webhook", 413),
        ]
        rows = []
        try:
            for name, payload, headers, path, expected in cases:
                request = Request(f"http://127.0.0.1:{server.server_address[1]}{path}",
                                  data=payload, headers=headers)
                try:
                    with urlopen(request, timeout=10) as response:
                        actual = response.status
                except HTTPError as error:
                    actual = error.code
                    error.close()
                rows.append({"case": name, "expected": expected, "actual": actual,
                             "control_passed": actual == expected})
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
        return {"cases": rows, "published_checks": len(env.fake.check_requests),
                "control_passed": all(r["control_passed"] for r in rows)
                and not env.fake.check_requests}


def connection_bound(root: Path) -> dict[str, object]:
    with _github_fake.receiver_environment(root) as env:
        server = receiver._BoundedServer(
            ("127.0.0.1", 0), receiver.build_handler(env.config, env.state),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        sockets = []
        try:
            for _ in range(receiver.MAX_CONNECTIONS):
                connection = socket.create_connection(server.server_address, timeout=2)
                connection.sendall(b"POST /webhook HTTP/1.1\r\nHost: localhost\r\n")
                sockets.append(connection)
            deadline = time.monotonic() + 2
            while server._slots._value and time.monotonic() < deadline:
                time.sleep(0.01)
            occupied = receiver.MAX_CONNECTIONS - server._slots._value
            with socket.create_connection(server.server_address, timeout=2) as overflow:
                overflow.settimeout(2)
                try:
                    rejected = overflow.recv(1) == b""
                except ConnectionResetError:
                    rejected = True
            deadline = time.monotonic() + receiver.READ_DEADLINE_SECONDS + 2
            while server._slots._value != receiver.MAX_CONNECTIONS and time.monotonic() < deadline:
                time.sleep(0.02)
            recovered = server._slots._value
        finally:
            for connection in sockets:
                connection.close()
            server.shutdown()
            thread.join()
            server.server_close()
        return {"held_incomplete_requests": occupied, "overflow_connection_rejected": rejected,
                "available_slots_after_read_deadlines": recovered,
                "published_checks": len(env.fake.check_requests),
                "control_passed": occupied == recovered == receiver.MAX_CONNECTIONS
                and rejected and not env.fake.check_requests}


def credential_file_mode(root: Path) -> dict[str, object]:
    path, public = _github_fake.write_app_key(root / "keys")
    path.chmod(0o644)
    repository = root / "repository"
    repository.mkdir()
    with patch.dict(os.environ, {
        "RANEX_GITHUB_APP_ID": _github_fake.APP_ID,
        "RANEX_GITHUB_APP_PRIVATE_KEY": str(path),
        "RANEX_GITHUB_WEBHOOK_SECRET": _github_fake.WEBHOOK_SECRET,
    }):
        credentials = AppCredentials.from_environment(repository)
        refusal = None
        claims = None
        try:
            token = mint_app_jwt(credentials)
            claims = _github_fake.verify_jwt(token, public)
        except ClientRefusal as error:
            refusal = error.code
    return {"key_mode": oct(path.stat().st_mode & 0o777),
            "jwt_signature_verified": bool(claims),
            "group_or_other_readable_key_refused": refusal == "E-GITHUB-KEY-EXPOSED",
            "refusal": refusal,
            "scope": "Temporary fixture key only; no production credentials"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="ranex-production-probes-") as temporary:
        root = Path(temporary)
        report = {
            "source_commit": subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True,
            ).strip(),
            "scope": "Real local Git/HTTP, fake GitHub API; NOT live production verification",
            "slow_publication": delayed_publication(root / "slow"),
            "late_verdict": late_verdict(root / "late"),
            "completion_failure": completion_failure(root / "crash"),
            "persisted_state": persisted_state(root / "state"),
            "http_refusals": http_refusals(root / "http"),
            "connection_bound": connection_bound(root / "connections"),
            "credential_file_mode": credential_file_mode(root / "credentials"),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
