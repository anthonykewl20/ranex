"""Identical Git content in separate installations/repositories publishes separately."""

from __future__ import annotations

import json
from dataclasses import replace

import _github_fake

from ranex.github_app import receiver


def event(head, installation, repository):
    value = json.loads(_github_fake.pull_request_event_body(head, repository=repository))
    value["installation"]["id"] = installation
    return json.dumps(value).encode()


def test_pending_same_head_is_retained_for_each_repository_and_installation(tmp_path):
    identities = ((1, "owner/one"), (1, "owner/two"), (2, "owner/two"))
    with _github_fake.receiver_environment(tmp_path, with_verdict=False) as env:
        config = replace(env.config, allowlist=frozenset(identities))
        for index, (installation, repository) in enumerate(identities):
            assert receiver.process_delivery(config, env.state, event(env.head, installation, repository), f"delivery-{index}", "pull_request") == 200
        pending = list((config.state_dir / "awaiting").rglob("*.json"))
        assert len(pending) == 3
        assert {(row["installation_id"], row["repository"]) for row in (json.loads(path.read_bytes()) for path in pending)} == set(identities)
        config.verdicts_dir.mkdir(parents=True, exist_ok=True)
        for path in (tmp_path / "source" / "governance" / "verdicts").iterdir():
            (config.verdicts_dir / path.name).write_bytes(path.read_bytes())

        receiver.refresh_awaiting(config, env.state)

        success = [request for request in env.fake.check_requests if request["body"]["conclusion"] == "success"]
        assert len(success) == 3
        assert len({request["body"]["external_id"] for request in success}) == 3
        assert not list((config.state_dir / "awaiting").rglob("*.json"))


def test_evaluation_receipt_for_same_verdict_never_suppresses_another_identity(tmp_path):
    identities = ((1, "owner/one"), (1, "owner/two"), (2, "owner/two"))
    with _github_fake.receiver_environment(tmp_path) as env:
        config = replace(env.config, allowlist=frozenset(identities), evaluator=lambda binding: None)
        config.state_dir.mkdir()
        for index, (installation, repository) in enumerate(identities):
            result = receiver._refresh_evaluated_head(config, env.head, f"delivery-{index}", installation, repository)
            assert result == "success"
        assert len(env.fake.check_requests) == 3
        assert len(list((config.state_dir / "evaluations").glob("*.json"))) == 3
        for index, (installation, repository) in enumerate(identities):
            assert receiver._refresh_evaluated_head(config, env.head, f"delivery-{index}", installation, repository) is None
        assert len(env.fake.check_requests) == 3
