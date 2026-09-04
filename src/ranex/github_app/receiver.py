"""The receiver: one endpoint, one event type, one delivery at a time.

The repo's first long-running process, bounded on purpose (ADR-051): a
stdlib `http.server` listener on localhost — TLS is the terminator's job —
that turns each validated delivery into at most one check publication. It
never evaluates; it publishes what verified verdicts already say.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from ranex.github_app import webhook
from ranex.github_app.acceptance import resolve_acceptance
from ranex.github_app.binding import (
    BindingRefusal,
    bind_pr_head,
    fetch_pr_head,
    revalidate_pr_head,
)
from ranex.github_app.client import ClientRefusal, GitHubClient
from ranex.github_app.publisher import publish_check

MAX_BODY_BYTES = 1_048_576
_DELIVERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
_DELIVERY_JOURNAL = "deliveries.jsonl"


@dataclass(frozen=True, slots=True)
class ReceiverConfig:
    """Everything the pipeline needs, frozen at listener start."""

    repo_root: Path
    remote: str
    verdicts_dir: Path
    keyring: Mapping[str, str]
    gate_id: str
    catalog_digest: str | None
    approver_id: str
    webhook_secret: str
    allowlist: frozenset[tuple[int, str]]
    client: GitHubClient
    state_dir: Path


@dataclass(slots=True)
class _ReceiverState:
    """Seen-delivery ids, grown only by `process_delivery`."""

    seen: set[str] = field(default_factory=set)


def _journal(config: ReceiverConfig, entry: Mapping[str, Any]) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    with (config.state_dir / _DELIVERY_JOURNAL).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def process_delivery(
    config: ReceiverConfig,
    state: _ReceiverState,
    body: bytes,
    delivery_id: str,
    event_name: str,
) -> int:
    """One validated delivery end to end. Returns the HTTP status to answer.

    Transient failures answer 5xx so GitHub retries the delivery; anything
    the pipeline understood and acted on — including a published refusal
    check — answers 200, because redelivering it changes nothing.
    """

    if delivery_id in state.seen:
        _journal(config, {"delivery": delivery_id, "outcome": "replayed"})
        return 200
    state.seen.add(delivery_id)
    try:
        event = None
        if event_name == webhook.HANDLED_EVENT:
            event = webhook.parse_pull_request_event(body)
    except webhook.WebhookRefusal as refusal:
        # A signed body with an unexpected shape is permanent; retrying the
        # same bytes cannot change the answer.
        _journal(config, {"delivery": delivery_id, "outcome": refusal.code})
        return 200
    if event is None:
        _journal(
            config, {"delivery": delivery_id, "event": event_name, "outcome": "ignored"}
        )
        return 200
    if (event.installation_id, event.repository) not in config.allowlist:
        _journal(
            config,
            {
                "delivery": delivery_id,
                "event": event_name,
                "outcome": "not-allowlisted",
                "repository": event.repository,
            },
        )
        return 200
    try:
        fetch_pr_head(config.repo_root, config.remote, event.head_sha)
        binding = bind_pr_head(config.repo_root, event.head_sha)
        acceptance = resolve_acceptance(
            config.verdicts_dir,
            binding,
            config.keyring,
            gate_id=config.gate_id,
            catalog_digest=config.catalog_digest,
            approver_id=config.approver_id,
        )
        revalidate_pr_head(config.repo_root, binding)
        moment = time.time()
        decision, _ = publish_check(
            config.client,
            event.installation_id,
            event.repository,
            binding,
            acceptance,
            started_at=moment,
            completed_at=moment,
        )
        outcome = f"published:{decision.conclusion}"
    except (BindingRefusal, ClientRefusal) as refusal:
        _journal(
            config,
            {
                "delivery": delivery_id,
                "event": event_name,
                "outcome": refusal.code,
                "head_sha": event.head_sha,
            },
        )
        # A fetch that could not reach the remote may succeed on redelivery;
        # everything else is a local, permanent answer.
        if refusal.code == "E-GITHUB-UNFETCHABLE-HEAD":
            return 500
        return 200
    _journal(
        config,
        {
            "delivery": delivery_id,
            "event": event_name,
            "outcome": outcome,
            "head_sha": event.head_sha,
        },
    )
    return 200


def build_handler(config: ReceiverConfig, state: _ReceiverState):
    """The request handler, closed over one config and one state."""

    class _DeliveryHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_POST(self) -> None:  # noqa: N802 — stdlib naming
            if self.path != "/webhook":
                self._answer(404, "no such endpoint")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._answer(400, "malformed Content-Length")
                return
            if length > MAX_BODY_BYTES:
                self._answer(413, "delivery too large")
                return
            body = self.rfile.read(length) if length else b""
            try:
                webhook.validate_delivery(
                    config.webhook_secret,
                    body,
                    self.headers.get(webhook.SIGNATURE_HEADER),
                )
            except webhook.WebhookRefusal:
                # 401 before a byte of the body is parsed or journaled.
                self._answer(401, "delivery did not prove itself")
                return
            delivery_id = self.headers.get(webhook.DELIVERY_HEADER, "")
            if not _DELIVERY_ID_PATTERN.fullmatch(delivery_id):
                self._answer(400, "malformed delivery id")
                return
            status = process_delivery(
                config,
                state,
                body,
                delivery_id,
                self.headers.get(webhook.EVENT_HEADER, ""),
            )
            self._answer(status, "accepted" if status == 200 else "retry later")

        def _answer(self, status: int, message: str) -> None:
            payload = message.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:
            # The delivery journal is the record; the default stderr chatter
            # can echo header values, and headers carry signatures.
            return

    return _DeliveryHandler


def serve(config: ReceiverConfig, bind: tuple[str, int]) -> None:
    """Listen until interrupted. One delivery at a time, by construction."""

    state = _ReceiverState()
    server = HTTPServer(bind, build_handler(config, state))
    try:
        server.serve_forever()
    finally:
        server.server_close()
