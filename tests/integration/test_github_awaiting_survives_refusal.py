"""A head answered `action_required` must stay refreshable even when the
publication of that very `action_required` check is refused by the API.

The live probe on 2026-09-07 (issue #88, `live-absent-verdict-1`) showed the
gap against the real API: `publish_check` raised, the refusal was journaled,
and `_remember_awaiting` never ran — so a transient outage at event time
silently loses the head and ADR-054's refresh can never pick it up. The
marker must be written before the publication attempt.
"""

from __future__ import annotations

from unittest.mock import patch

import _github_fake

from ranex.github_app.client import ClientRefusal
from ranex.github_app.receiver import process_delivery, refresh_awaiting

event_body = _github_fake.pull_request_event_body


def _land_verdicts(tmp_path, env) -> None:
    env.config.verdicts_dir.mkdir(parents=True, exist_ok=True)
    for path in (tmp_path / "source" / "governance" / "verdicts").iterdir():
        (env.config.verdicts_dir / path.name).write_bytes(path.read_bytes())


def test_an_absent_verdict_head_is_remembered_even_when_publication_refuses(
    tmp_path,
) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        def refused(*args, **kwargs):
            raise ClientRefusal("E-GITHUB-API-REFUSED", "injected outage")

        with patch.object(env.config.client, "create_check_run", refused):
            status = process_delivery(
                env.config, env.state, event_body(env.head), "d-outage", "pull_request",
            )
        assert status == 500
        assert env.fake.check_requests == []
        # The head must already be remembered: the outage must not lose it.
        awaiting = tmp_path / "state" / "awaiting" / f"{env.head}.json"
        assert awaiting.exists(), (
            "a head whose action_required publication was refused must still be "
            "remembered for the periodic refresh (ADR-054)"
        )

        _land_verdicts(tmp_path, env)
        refreshed = refresh_awaiting(env.config, env.state)
        assert refreshed == {env.head: "success"}
        assert [r["body"]["conclusion"] for r in env.fake.check_requests] == ["success"]


def test_a_refused_refresh_keeps_the_head_for_the_next_pass(tmp_path) -> None:
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        process_delivery(env.config, env.state, event_body(env.head), "d-1", "pull_request")
        _land_verdicts(tmp_path, env)
        awaiting = tmp_path / "state" / "awaiting" / f"{env.head}.json"

        def refused(*args, **kwargs):
            raise ClientRefusal("E-GITHUB-API-REFUSED", "injected outage")

        with patch.object(env.config.client, "create_check_run", refused):
            statuses = refresh_awaiting(env.config, env.state)
        assert statuses == {env.head: 500}
        assert awaiting.exists()
