"""A verdict that lands after the event was answered still reaches GitHub.

The receiver publishes what verified verdicts say; when none exists yet it
publishes `action_required` and remembers the head. The periodic pass then
re-reads the verdict store and publishes once the record is there — no
redelivery, no second `action_required`, and never a second success.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import _github_fake

from ranex.github_app import receiver
from ranex.github_app.receiver import process_delivery, refresh_awaiting

event_body = _github_fake.pull_request_event_body


def _land_verdicts(tmp_path: Path, env) -> None:
    env.config.verdicts_dir.mkdir(parents=True, exist_ok=True)
    for path in (tmp_path / "source" / "governance" / "verdicts").iterdir():
        (env.config.verdicts_dir / path.name).write_bytes(path.read_bytes())


def _conclusions(env) -> list[str]:
    return [r["body"]["conclusion"] for r in env.fake.check_requests]


def test_an_absent_verdict_is_remembered_and_published_when_it_lands(tmp_path: Path) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        assert process_delivery(env.config, env.state, event_body(env.head), "d-early", "pull_request") == 200
        assert _conclusions(env) == ["action_required"]
        awaiting = tmp_path / "state" / "awaiting" / f"{env.head}.json"
        assert json.loads(awaiting.read_bytes()) == {
            "delivery": "d-early", "installation_id": 1, "repository": "owner/name",
        }

        # Nothing landed yet: the pass publishes nothing and keeps waiting.
        assert refresh_awaiting(env.config, env.state) == {}
        assert _conclusions(env) == ["action_required"]
        assert awaiting.exists()

        _land_verdicts(tmp_path, env)
        assert refresh_awaiting(env.config, env.state) == {env.head: "success"}
        assert _conclusions(env) == ["action_required", "success"]
        assert env.fake.check_requests[-1]["body"]["external_id"] == f"refresh:{env.head}"
        assert not awaiting.exists()
        journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
        assert f'"head_sha": "{env.head}", "delivery": "d-early", "outcome": "refreshed:success"' in journal

        # Satisfied heads are forgotten; a further pass is a no-op.
        assert refresh_awaiting(env.config, env.state) == {}
        assert _conclusions(env) == ["action_required", "success"]


def test_a_fresh_event_that_publishes_a_verdict_forgets_the_wait(tmp_path: Path) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        process_delivery(env.config, env.state, event_body(env.head), "d-1", "pull_request")
        awaiting = tmp_path / "state" / "awaiting" / f"{env.head}.json"
        assert awaiting.exists()
        _land_verdicts(tmp_path, env)
        process_delivery(env.config, env.state, event_body(env.head), "d-2", "pull_request")
        assert _conclusions(env) == ["action_required", "success"]
        assert not awaiting.exists()
        assert refresh_awaiting(env.config, env.state) == {}


def test_a_refresh_interrupted_after_publication_reconciles_on_the_next_pass(
    tmp_path: Path,
) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        process_delivery(env.config, env.state, event_body(env.head), "d-1", "pull_request")
        _land_verdicts(tmp_path, env)
        awaiting = tmp_path / "state" / "awaiting" / f"{env.head}.json"
        record = awaiting.read_bytes()

        def keep(path, *args, **kwargs):
            raise OSError("injected failure removing the wait record")

        with patch.object(receiver, "_forget_awaiting", keep):
            assert refresh_awaiting(env.config, env.state) == {env.head: 500}
        assert _conclusions(env) == ["action_required", "success"]
        assert awaiting.exists() and awaiting.read_bytes() == record

        # The failed pass backs off; after the window it reconciles.
        assert refresh_awaiting(env.config, env.state) == {}
        with patch.object(receiver, "SPOOL_RETRY_SECONDS", 0):
            assert refresh_awaiting(env.config, env.state) == {env.head: "success"}
        assert not awaiting.with_suffix(".failed").exists()
        assert _conclusions(env) == ["action_required", "success"]
        assert not awaiting.exists()
        assert "reconciled-refresh:success" in (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_a_busy_pipeline_and_damaged_records_leave_the_wait_in_place(tmp_path: Path) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        assert refresh_awaiting(env.config, env.state) == {}
        process_delivery(env.config, env.state, event_body(env.head), "d-1", "pull_request")
        _land_verdicts(tmp_path, env)
        assert env.state.lock.acquire(blocking=False)
        try:
            assert refresh_awaiting(env.config, env.state) == {env.head: 503}
        finally:
            env.state.lock.release()
        assert _conclusions(env) == ["action_required"]

        damaged = tmp_path / "state" / "awaiting" / f"{'9' * 40}.json"
        damaged.write_bytes(b'{"delivery": 1}')
        assert env.state.lock.acquire(blocking=False)
        try:
            # 503 is not a failure of the entry: no backoff marker is written.
            assert refresh_awaiting(env.config, env.state) == {"9" * 40: 500, env.head: 503}
        finally:
            env.state.lock.release()
        assert not (tmp_path / "state" / "awaiting" / f"{env.head}.failed").exists()
        (tmp_path / "state" / "awaiting" / f"{'9' * 40}.failed").unlink()
        env.state.demand = 1
        assert refresh_awaiting(env.config, env.state) == {}
        assert env.state.yielded is True
        env.state.demand = 0
        env.state.yielded = False
        misnamed = tmp_path / "state" / "awaiting" / "not-a-head.json"
        misnamed.write_bytes(
            b'{"delivery": "d-x", "installation_id": 1, "repository": "owner/name"}'
        )
        statuses = refresh_awaiting(env.config, env.state)
        assert statuses == {"9" * 40: 500, "not-a-head": 500, env.head: "success"}
        assert damaged.exists() and misnamed.exists()
        rows = (tmp_path / "state" / "deliveries.jsonl").read_text()
        assert '"outcome": "awaiting-unreadable"' in rows


def test_refresh_does_not_publish_after_repository_is_removed_from_allowlist(tmp_path: Path) -> None:
    from dataclasses import replace

    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        process_delivery(env.config, env.state, event_body(env.head), "d-revoked", "pull_request")
        _land_verdicts(tmp_path, env)
        before = len(env.fake.requests)
        revoked = replace(env.config, allowlist=frozenset())
        assert refresh_awaiting(revoked, env.state) == {env.head: "not-allowlisted"}
        assert len(env.fake.requests) == before
        assert not (env.config.state_dir / "awaiting" / f"{env.head}.json").exists()
