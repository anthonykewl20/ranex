"""The receiver: one endpoint, one event type, one delivery at a time.

The repo's first long-running process, bounded on purpose (ADR-051): a
stdlib `http.server` listener on localhost — TLS is the terminator's job —
that turns each validated delivery into at most one check publication. It
never evaluates; it publishes what verified verdicts already say.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
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
MAX_CONNECTIONS = 16
READ_DEADLINE_SECONDS = 5.0
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
    """Serialize the Git/publication pipeline; receipt state lives on disk."""

    lock: Any = field(default_factory=threading.Lock)


def _migrate_legacy_spool(config: ReceiverConfig) -> None:
    """Retain terminal acknowledgements recorded by the pre-repair listener.

    Old receipts had no body fingerprint. They may suppress a completed ID,
    but a failed attempt or the old erroneous `replayed` row is never success.
    Run under the receiver file lock; the atomic marker makes this restartable.
    """
    marker = config.state_dir / "spool-v2.json"
    if marker.exists():
        return
    legacy = config.state_dir / _DELIVERY_JOURNAL
    if legacy.exists():
        with legacy.open(encoding="utf-8") as handle:
            for line in handle:
                entry = json.loads(line)
                if not isinstance(entry, dict) or not isinstance(entry.get("outcome"), str):
                    raise ValueError("invalid legacy delivery receipt")
                delivery, outcome = entry.get("delivery"), entry["outcome"]
                terminal = (outcome in {"ignored", "not-allowlisted", "E-GITHUB-BAD-EVENT"}
                            or outcome.startswith("published:"))
                if terminal and isinstance(delivery, str) and _DELIVERY_ID_PATTERN.fullmatch(delivery):
                    target = config.state_dir / "completed" / f"{delivery}.json"
                    if not target.exists():
                        write_atomic(target, canonical_json_bytes({"fingerprint": None}), root=config.state_dir)
    write_atomic(marker, b"{}", root=config.state_dir)


def _journal(config: ReceiverConfig, entry: Mapping[str, Any]) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)
    with (config.state_dir / _DELIVERY_JOURNAL).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def process_delivery(
    config: ReceiverConfig,
    state: _ReceiverState,
    body: bytes,
    delivery_id: str,
    event_name: str,
) -> int:
    """Persist completed deliveries; failed attempts remain retryable.

    A 5xx requires operator/API redelivery: GitHub does not retry automatically.
    Completion cannot be atomic with GitHub's remote check creation. A crash
    after publication but before local completion can still duplicate a check.
    """
    if not _DELIVERY_ID_PATTERN.fullmatch(delivery_id) or len(delivery_id) > 128:
        return 400
    if not state.lock.acquire(blocking=False):
        return 503
    try:
        config.state_dir.mkdir(parents=True, exist_ok=True)
        # Also serialize distinct receiver processes sharing a state directory.
        with (config.state_dir / "receiver.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 503
            _migrate_legacy_spool(config)
            target = config.state_dir / "completed" / f"{delivery_id}.json"
            fingerprint = canonical_sha256({"body": body.hex(), "event": event_name})
            if target.exists():
                stored = json.loads(target.read_bytes())
                if not isinstance(stored, dict) or set(stored) != {"fingerprint"}:
                    raise ValueError("invalid completion receipt")
                previous = stored["fingerprint"]
                if previous is not None and (
                    not isinstance(previous, str)
                    or re.fullmatch(r"[0-9a-f]{64}", previous) is None
                ):
                    raise ValueError("invalid completion fingerprint")
                if previous is not None and previous != fingerprint:
                    _journal(config, {"delivery": delivery_id, "outcome": "delivery-conflict"})
                    return 409
                _journal(config, {"delivery": delivery_id, "outcome": "replayed"})
                return 200
            status = _process_delivery(config, body, delivery_id, event_name)
            if status == 200:
                write_atomic(target, canonical_json_bytes({"fingerprint": fingerprint}),
                             root=config.state_dir)
            return status
    finally:
        state.lock.release()


def _process_delivery(
    config: ReceiverConfig, body: bytes, delivery_id: str, event_name: str,
) -> int:
    """One validated delivery end to end. Returns the HTTP status to answer.

    Transient failures answer 5xx so an operator can retry the delivery; anything
    the pipeline understood and acted on — including a published refusal
    check — answers 200, because redelivering it changes nothing.
    """

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
        if isinstance(refusal, ClientRefusal) or refusal.code == "E-GITHUB-UNFETCHABLE-HEAD":
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
        timeout = READ_DEADLINE_SECONDS

        def handle(self) -> None:
            # A wall-clock deadline also bounds clients that trickle bytes
            # often enough to defeat a socket's inactivity timeout.
            self._deadline = threading.Timer(READ_DEADLINE_SECONDS, self._expire)
            self._deadline.daemon = True
            self._deadline.start()
            try:
                super().handle()
            except (ConnectionError, OSError):
                self.close_connection = True
            finally:
                self._deadline.cancel()
                self._deadline.join()

        def _expire(self) -> None:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

        def do_POST(self) -> None:  # noqa: N802 — stdlib naming
            if self.path != "/webhook":
                self._answer(404, "no such endpoint")
                return
            lengths = self.headers.get_all("Content-Length", [])
            if (self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1
                    or not re.fullmatch(r"[0-9]{1,10}", lengths[0])):
                self._answer(400, "malformed Content-Length")
                return
            length = int(lengths[0])
            if length > MAX_BODY_BYTES:
                self._answer(413, "delivery too large")
                return
            body = self.rfile.read(length) if length else b""
            if len(body) != length:
                self._answer(400, "incomplete body")
                return
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
            if not _DELIVERY_ID_PATTERN.fullmatch(delivery_id) or len(delivery_id) > 128:
                self._answer(400, "malformed delivery id")
                return
            self._deadline.cancel()
            self._deadline.join()
            try:
                status = process_delivery(
                    config, state, body, delivery_id,
                    self.headers.get(webhook.EVENT_HEADER, ""),
                )
            except (OSError, ValueError):
                self._answer(500, "delivery state unavailable")
                return
            self._answer(status, "accepted" if status == 200 else "retry later")

        def _answer(self, status: int, message: str) -> None:
            self.close_connection = True
            payload = message.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:
            # The delivery journal is the record; the default stderr chatter
            # can echo header values, and headers carry signatures.
            return

    return _DeliveryHandler


class _BoundedServer(ThreadingMixIn, HTTPServer):
    """At most sixteen accepted sockets and one active delivery pipeline."""

    daemon_threads = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        super().__init__(*args, **kwargs)

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self._slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._slots.release()


def serve(config: ReceiverConfig, bind: tuple[str, int]) -> None:
    """Listen with bounded connections and a serialized delivery pipeline."""

    state = _ReceiverState()
    server = _BoundedServer(bind, build_handler(config, state))
    try:
        server.serve_forever()
    finally:
        server.server_close()
