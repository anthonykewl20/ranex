"""Integration arms for the webhook receiver: prove, dedupe, publish.

The HMAC arithmetic is pinned against the test vector GitHub itself
publishes; the journeys run a real receiver handler against real git
stores with a fake GitHub behind the client — the full pipeline a live
delivery would walk.
"""

from __future__ import annotations

import http.client
import threading
from http.server import HTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import _github_fake

from ranex.github_app.receiver import MAX_BODY_BYTES, build_handler, process_delivery
from ranex.github_app.webhook import (
    DOCUMENTED_VECTOR_BODY,
    DOCUMENTED_VECTOR_SECRET,
    DOCUMENTED_VECTOR_SIGNATURE,
    delivery_signature,
    parse_pull_request_event,
    validate_delivery,
)

SECRET = _github_fake.WEBHOOK_SECRET
event_body = _github_fake.pull_request_event_body
receiver_environment = _github_fake.receiver_environment


def test_the_signature_arithmetic_matches_the_documented_vector() -> None:
    assert (
        delivery_signature(DOCUMENTED_VECTOR_SECRET, DOCUMENTED_VECTOR_BODY)
        == DOCUMENTED_VECTOR_SIGNATURE
    )


def test_an_unsigned_delivery_refuses_before_any_parsing() -> None:
    try:
        validate_delivery(SECRET, b"{}", None)
    except Exception as exc:  # noqa: BLE001 — the code is the assertion
        assert getattr(exc, "code", "") == "E-GITHUB-UNSIGNED-DELIVERY"
    else:
        raise AssertionError("an unsigned delivery must refuse")


def test_a_tampered_delivery_refuses() -> None:
    signature = delivery_signature(SECRET, b"{}")
    try:
        validate_delivery(SECRET, b'{"tampered": true}', signature)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "code", "") == "E-GITHUB-BAD-SIGNATURE"
    else:
        raise AssertionError("a tampered delivery must refuse")


def test_the_event_grammar_is_closed_at_parse_time() -> None:
    event = parse_pull_request_event(event_body("a" * 40))
    assert event is not None
    assert (event.action, event.head_sha, event.repository, event.installation_id) == (
        "opened",
        "a" * 40,
        "owner/name",
        1,
    )
    # An action the receiver does not handle is acknowledged, not parsed.
    assert parse_pull_request_event(event_body("a" * 40, action="closed")) is None


def test_a_signed_delivery_publishes_the_check(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        status = process_delivery(
            env.config, env.state, event_body(env.head), "d-1", "pull_request"
        )

        assert status == 200
        assert len(env.fake.check_requests) == 1
        assert env.fake.check_requests[0]["body"]["head_sha"] == env.head
        assert env.fake.check_requests[0]["body"]["conclusion"] == "success"
        journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
        assert "published:success" in journal


def test_a_replayed_delivery_id_is_a_no_op(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)
        first = process_delivery(env.config, env.state, body, "d-1", "pull_request")
        second = process_delivery(env.config, env.state, body, "d-1", "pull_request")

        assert first == second == 200
        assert len(env.fake.check_requests) == 1
        journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
        assert journal.count("replayed") == 1


def test_a_foreign_repository_is_journaled_and_skipped(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        status = process_delivery(
            env.config,
            env.state,
            event_body(env.head, repository="someone/else"),
            "d-2",
            "pull_request",
        )

        assert status == 200
        assert env.fake.check_requests == []
        assert "not-allowlisted" in (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_an_unhandled_action_is_journaled_and_skipped(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        status = process_delivery(
            env.config,
            env.state,
            event_body(env.head, action="closed"),
            "d-3",
            "pull_request",
        )

        assert status == 200
        assert env.fake.check_requests == []
        assert '"ignored"' in (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_the_http_endpoint_validates_before_it_processes(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        server = HTTPServer(("127.0.0.1", 0), build_handler(env.config, env.state))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            host, port = server.server_address[:2]
            body = event_body(env.head)
            signed = Request(
                f"http://{host}:{port}/webhook",
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": delivery_signature(SECRET, body),
                    "X-GitHub-Delivery": "d-http-1",
                    "X-GitHub-Event": "pull_request",
                },
            )
            with urlopen(signed, timeout=10) as response:
                assert response.status == 200

            unsigned = Request(
                f"http://{host}:{port}/webhook",
                data=body,
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Delivery": "d-http-2",
                    "X-GitHub-Event": "pull_request",
                },
            )
            try:
                urlopen(unsigned, timeout=10)
            except Exception as exc:  # noqa: BLE001
                assert getattr(exc, "code", None) == 401
            else:
                raise AssertionError("an unsigned POST must be refused with 401")

            assert len(env.fake.check_requests) == 1
            journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
            assert "d-http-2" not in journal
        finally:
            server.shutdown()
            server.server_close()


def test_an_oversized_delivery_is_refused_without_parsing(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        server = HTTPServer(("127.0.0.1", 0), build_handler(env.config, env.state))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            host, port = server.server_address[:2]
            connection = http.client.HTTPConnection(host, port, timeout=10)
            connection.request(
                "POST",
                "/webhook",
                body=b"",
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(MAX_BODY_BYTES + 1),
                    "X-Hub-Signature-256": "sha256=" + "0" * 64,
                    "X-GitHub-Delivery": "d-big",
                    "X-GitHub-Event": "pull_request",
                },
            )
            response = connection.getresponse()
            assert response.status == 413
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
