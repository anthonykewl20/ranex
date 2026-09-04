"""Security arms for the receiver: every sad path is a named outcome.

The receiver's promise is negative: it cannot be talked into processing an
unproven delivery, and it cannot be talked out of saying what happened.
Each refusal is journaled with its code; the webhook secret appears in no
journal entry and no refusal.
"""

from __future__ import annotations

import json
from pathlib import Path

import _github_fake

from ranex.github_app.receiver import process_delivery


def journal_text(tmp_path: Path) -> str:
    return (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_an_unfetchable_head_answers_retry_and_publishes_nothing(
    tmp_path: Path,
) -> None:
    with _github_fake.receiver_environment(tmp_path) as env:
        # A head no remote holds: the fetch refuses, and the delivery
        # answers 5xx so GitHub retries — a missing object may be a
        # replication race on their side, not a permanent fact.
        status = process_delivery(
            env.config,
            env.state,
            _github_fake.pull_request_event_body("9" * 40),
            "d-fetch",
            "pull_request",
        )

        assert status == 500
        assert env.fake.check_requests == []
        assert "E-GITHUB-UNFETCHABLE-HEAD" in journal_text(tmp_path)


def test_no_verdict_for_the_head_publishes_action_required_never_green(
    tmp_path: Path,
) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        status = process_delivery(
            env.config,
            env.state,
            _github_fake.pull_request_event_body(env.head),
            "d-absent",
            "pull_request",
        )

        assert status == 200
        assert len(env.fake.check_requests) == 1
        body = env.fake.check_requests[0]["body"]
        assert body["conclusion"] == "action_required"
        assert body["head_sha"] == env.head


def test_a_signed_but_shapeless_event_is_a_named_permanent_refusal(
    tmp_path: Path,
) -> None:
    with _github_fake.receiver_environment(tmp_path) as env:
        broken = json.dumps({"action": "opened", "installation": {"id": 1}}).encode(
            "utf-8"
        )
        status = process_delivery(env.config, env.state, broken, "d-shape", "pull_request")

        assert status == 200
        assert env.fake.check_requests == []
        assert "E-GITHUB-BAD-EVENT" in journal_text(tmp_path)


def test_a_non_pull_request_event_is_acknowledged_and_skipped(
    tmp_path: Path,
) -> None:
    with _github_fake.receiver_environment(tmp_path) as env:
        body = json.dumps({"zen": "Design for failure."}).encode("utf-8")
        status = process_delivery(env.config, env.state, body, "d-zen", "ping")

        assert status == 200
        assert env.fake.check_requests == []
        entry = json.loads(journal_text(tmp_path).splitlines()[-1])
        assert entry == {"delivery": "d-zen", "event": "ping", "outcome": "ignored"}


def test_the_webhook_secret_never_reaches_the_journal(tmp_path: Path) -> None:
    with _github_fake.receiver_environment(tmp_path) as env:
        process_delivery(
            env.config,
            env.state,
            _github_fake.pull_request_event_body(env.head),
            "d-secret",
            "pull_request",
        )
        process_delivery(
            env.config,
            env.state,
            _github_fake.pull_request_event_body("9" * 40),
            "d-secret-2",
            "pull_request",
        )

        assert _github_fake.WEBHOOK_SECRET not in journal_text(tmp_path)
