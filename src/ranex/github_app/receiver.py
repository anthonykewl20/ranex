"""The receiver: one endpoint, one event type, one delivery at a time.

The repo's first long-running process, bounded on purpose (ADR-051): a
stdlib `http.server` listener on localhost — TLS is the terminator's job —
that turns each validated delivery into at most one check publication. It
never evaluates; it publishes what verified verdicts already say.

Two durability arms sit around the pipeline. Every proven delivery is spooled
to disk before it is worked on, and the HTTP answer waits at most
`ACK_DEADLINE_SECONDS` for the pipeline: past that it answers 202 and the
spool carries the delivery to completion or to a restart. And a publication
is stamped with its delivery id, so a retry after a lost completion receipt
reconciles against the check GitHub already holds instead of publishing twice.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any

from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.github_app import webhook
from ranex.github_app.acceptance import ABSENT_CODE, resolve_acceptance
from ranex.github_app.binding import (
    BindingRefusal,
    bind_pr_head,
    fetch_pr_head,
    revalidate_pr_head,
)
from ranex.github_app.client import ClientRefusal, GitHubClient
from ranex.github_app.publisher import CHECK_NAME, publish_check

MAX_BODY_BYTES = 1_048_576
MAX_CONNECTIONS = 16
READ_DEADLINE_SECONDS = 5.0
# GitHub abandons a delivery it has not heard back from in ten seconds; the
# answer goes out before that, whatever the pipeline is still doing.
ACK_DEADLINE_SECONDS = 8.0
# How often a running listener re-drains deliveries it acknowledged with 202
# but could not complete (a remote that was unreachable, an API refusal).
SPOOL_RETRY_SECONDS = 300.0
_DELIVERY_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
_DELIVERY_JOURNAL = "deliveries.jsonl"
_SPOOL_DIR = "spool"
_ATTEMPTED_DIR = "attempted"
_AWAITING_DIR = "awaiting"
_HEAD_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


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


def _valid_delivery_id(delivery_id: str) -> bool:
    return bool(_DELIVERY_ID_PATTERN.fullmatch(delivery_id)) and len(delivery_id) <= 128


def spool_delivery(
    config: ReceiverConfig, body: bytes, delivery_id: str, event_name: str,
) -> int:
    """Durably retain one proven delivery before any work is done on it.

    Returns 400 for an id that cannot name a file; 202 once the entry is on
    disk. An entry already present for the id is left as it was: the first
    body spooled is the one the pipeline judges, and a conflicting redelivery
    is answered by the completion receipt when it is processed.
    """
    if not _valid_delivery_id(delivery_id):
        return 400
    target = config.state_dir / _SPOOL_DIR / f"{delivery_id}.json"
    if not target.exists():
        config.state_dir.mkdir(parents=True, exist_ok=True)
        write_atomic(
            target,
            canonical_json_bytes({"body": body.hex(), "event": event_name}),
            root=config.state_dir,
        )
    return 202


def _unspool(config: ReceiverConfig, delivery_id: str) -> None:
    with suppress(FileNotFoundError):
        (config.state_dir / _SPOOL_DIR / f"{delivery_id}.json").unlink()


def _read_spool_entry(path: Path) -> tuple[bytes, str]:
    entry = json.loads(path.read_bytes())
    if (
        not isinstance(entry, dict)
        or set(entry) != {"body", "event"}
        or not isinstance(entry["body"], str)
        or not isinstance(entry["event"], str)
    ):
        raise ValueError("invalid spool entry")
    return bytes.fromhex(entry["body"]), entry["event"]


def drain_spool(config: ReceiverConfig, state: _ReceiverState) -> dict[str, int]:
    """Run every spooled delivery through the pipeline; return each status.

    Called at listener start (crash recovery) and on a timer. A delivery that
    completes — accepted, refused as malformed, or in conflict — leaves the
    spool; one that cannot (5xx) stays for the next pass. A damaged entry is
    journaled and left for the operator: the receiver never guesses at bytes.
    """
    statuses: dict[str, int] = {}
    spool = config.state_dir / _SPOOL_DIR
    if not spool.is_dir():
        return statuses
    for path in sorted(spool.glob("*.json"), key=lambda p: (p.stat().st_mtime, p.name)):
        delivery_id = path.stem
        try:
            body, event_name = _read_spool_entry(path)
        except (OSError, ValueError):
            _journal(config, {"delivery": delivery_id, "outcome": "spool-unreadable"})
            statuses[delivery_id] = 500
            continue
        try:
            status = process_delivery(config, state, body, delivery_id, event_name)
        except (OSError, ValueError):
            status = 500
        if status < 500:
            _unspool(config, delivery_id)
        statuses[delivery_id] = status
    return statuses


def process_delivery(
    config: ReceiverConfig,
    state: _ReceiverState,
    body: bytes,
    delivery_id: str,
    event_name: str,
) -> int:
    """Persist completed deliveries; failed attempts remain retryable.

    A 5xx answered synchronously requires operator/API redelivery: GitHub does
    not retry automatically. Completion cannot be atomic with GitHub's remote
    check creation, so publication is at-least-once by construction; the
    attempt record and the check's `external_id` let a retry reconcile against
    what GitHub already holds instead of publishing a second check.
    """
    if not _valid_delivery_id(delivery_id):
        return 400
    with _pipeline(config, state) as held:
        if not held:
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


@contextmanager
def _pipeline(config: ReceiverConfig, state: _ReceiverState) -> Iterator[bool]:
    """Hold the one delivery pipeline, in-process and across processes.

    Yields False without waiting when either lock is taken: the caller
    answers 503 (or, on a periodic pass, tries again next time).
    """
    if not state.lock.acquire(blocking=False):
        yield False
        return
    try:
        config.state_dir.mkdir(parents=True, exist_ok=True)
        # Also serialize distinct receiver processes sharing a state directory.
        with (config.state_dir / "receiver.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            yield True
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
        reconciled = _reconcile_attempt(config, event, delivery_id)
        if reconciled is not None:
            _journal(
                config,
                {
                    "delivery": delivery_id,
                    "event": event_name,
                    "outcome": f"reconciled:{reconciled}",
                    "head_sha": event.head_sha,
                },
            )
            return 200
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
        # The attempt record goes down before the API call: a crash between
        # the two leaves a retry able to ask GitHub what it already holds.
        write_atomic(
            config.state_dir / _ATTEMPTED_DIR / f"{delivery_id}.json",
            canonical_json_bytes({"head_sha": event.head_sha}),
            root=config.state_dir,
        )
        moment = time.time()
        decision, _ = publish_check(
            config.client,
            event.installation_id,
            event.repository,
            binding,
            acceptance,
            started_at=moment,
            completed_at=moment,
            external_id=delivery_id,
        )
        outcome = f"published:{decision.conclusion}"
        if acceptance.code == ABSENT_CODE:
            _remember_awaiting(config, event, delivery_id)
        else:
            _forget_awaiting(config, event.head_sha)
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


def _reconcile_attempt(
    config: ReceiverConfig, event: webhook.PullRequestEvent, delivery_id: str,
) -> str | None:
    """The conclusion GitHub already holds for this delivery, if any.

    Only an attempt record naming this event's head counts; a record for
    another head is a stale artefact, not evidence. GitHub is asked for this
    App's `ranex/acceptance` runs on the head and the one stamped with this
    delivery id is the earlier publication. Nothing is republished.
    """
    record_path = config.state_dir / _ATTEMPTED_DIR / f"{delivery_id}.json"
    if not record_path.exists():
        return None
    record = json.loads(record_path.read_bytes())
    if not isinstance(record, dict) or record.get("head_sha") != event.head_sha:
        return None
    for run in config.client.list_check_runs(
        event.installation_id, event.repository, event.head_sha, check_name=CHECK_NAME,
    ):
        if run.get("external_id") == delivery_id and isinstance(run.get("conclusion"), str):
            return run["conclusion"]
    return None


def _remember_awaiting(
    config: ReceiverConfig, event: webhook.PullRequestEvent, delivery_id: str,
) -> None:
    """The head has no verdict yet; the periodic pass will look again."""
    write_atomic(
        config.state_dir / _AWAITING_DIR / f"{event.head_sha}.json",
        canonical_json_bytes({
            "delivery": delivery_id,
            "installation_id": event.installation_id,
            "repository": event.repository,
        }),
        root=config.state_dir,
    )


def _forget_awaiting(config: ReceiverConfig, head_sha: str) -> None:
    with suppress(FileNotFoundError):
        (config.state_dir / _AWAITING_DIR / f"{head_sha}.json").unlink()


def _read_awaiting(path: Path) -> tuple[str, int, str]:
    record = json.loads(path.read_bytes())
    if (
        not isinstance(record, dict)
        or set(record) != {"delivery", "installation_id", "repository"}
        or not isinstance(record["delivery"], str)
        or not isinstance(record["installation_id"], int)
        or not isinstance(record["repository"], str)
    ):
        raise ValueError("invalid awaiting record")
    return record["delivery"], record["installation_id"], record["repository"]


def refresh_awaiting(config: ReceiverConfig, state: _ReceiverState) -> dict[str, str | int]:
    """Publish for heads answered `action_required` whose verdict has since landed.

    Runs on the listener's periodic pass under the same pipeline lock a
    delivery holds. Per head: the conclusion published, 503 when the pipeline
    was busy, 500 when the record or publication failed. A head whose verdict
    is still absent is left waiting and does not appear. The refresh check is
    stamped `refresh:<head>` so an interrupted pass reconciles instead of
    publishing twice; nothing here evaluates anything.
    """
    statuses: dict[str, str | int] = {}
    awaiting = config.state_dir / _AWAITING_DIR
    if not awaiting.is_dir():
        return statuses
    for path in sorted(awaiting.glob("*.json")):
        head_sha = path.stem
        try:
            delivery_id, installation_id, repository = _read_awaiting(path)
            if not _HEAD_SHA_PATTERN.fullmatch(head_sha):
                raise ValueError("invalid awaiting head")
        except (OSError, ValueError):
            _journal(config, {"head_sha": head_sha, "outcome": "awaiting-unreadable"})
            statuses[head_sha] = 500
            continue
        with _pipeline(config, state) as held:
            if not held:
                statuses[head_sha] = 503
                continue
            try:
                conclusion = _refresh_head(config, head_sha, delivery_id, installation_id, repository)
            except (BindingRefusal, ClientRefusal, OSError, ValueError) as error:
                _journal(config, {"head_sha": head_sha, "outcome": "refresh-failed",
                                  "detail": type(error).__name__})
                statuses[head_sha] = 500
                continue
        if conclusion is not None:
            statuses[head_sha] = conclusion
    return statuses


def _refresh_head(
    config: ReceiverConfig, head_sha: str, delivery_id: str, installation_id: int, repository: str,
) -> str | None:
    external_id = f"refresh:{head_sha}"
    for run in config.client.list_check_runs(
        installation_id, repository, head_sha, check_name=CHECK_NAME,
    ):
        if run.get("external_id") == external_id and isinstance(run.get("conclusion"), str):
            # A previous pass published and was interrupted before forgetting.
            _forget_awaiting(config, head_sha)
            _journal(config, {"head_sha": head_sha, "delivery": delivery_id,
                              "outcome": f"reconciled-refresh:{run['conclusion']}"})
            return run["conclusion"]
    binding = bind_pr_head(config.repo_root, head_sha)
    acceptance = resolve_acceptance(
        config.verdicts_dir, binding, config.keyring, gate_id=config.gate_id,
        catalog_digest=config.catalog_digest, approver_id=config.approver_id,
    )
    if acceptance.code == ABSENT_CODE:
        return None
    revalidate_pr_head(config.repo_root, binding)
    moment = time.time()
    decision, _ = publish_check(
        config.client, installation_id, repository, binding, acceptance,
        started_at=moment, completed_at=moment, external_id=external_id,
    )
    _forget_awaiting(config, head_sha)
    _journal(config, {"head_sha": head_sha, "delivery": delivery_id,
                      "outcome": f"refreshed:{decision.conclusion}"})
    return decision.conclusion


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
            with suppress(OSError):
                self.connection.shutdown(socket.SHUT_RDWR)

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
            event_name = self.headers.get(webhook.EVENT_HEADER, "")
            self._deadline.cancel()
            self._deadline.join()
            try:
                spooled = spool_delivery(config, body, delivery_id, event_name)
            except OSError:
                self._answer(500, "delivery state unavailable")
                return
            if spooled == 400:
                self._answer(400, "malformed delivery id")
                return
            outcome: dict[str, int] = {}
            answer_lock = threading.Lock()

            def run() -> None:
                try:
                    status = process_delivery(config, state, body, delivery_id, event_name)
                except (OSError, ValueError):
                    status = 500
                with answer_lock:
                    outcome["status"] = status
                    answered = outcome.get("answered")
                # Answered 202 already: the spool keeps anything that did not
                # complete for the drain, and releases what did.
                if answered == 202 and status < 500:
                    _unspool(config, delivery_id)

            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            worker.join(ACK_DEADLINE_SECONDS)
            with answer_lock:
                status = outcome.get("status")
                outcome["answered"] = 202 if status is None else status
            if status is None:
                self._answer(202, "queued")
                return
            # Answered synchronously, the answer is the truth GitHub holds and
            # the spool has nothing left to say about this delivery.
            _unspool(config, delivery_id)
            self._answer(status, "accepted" if status == 200 else
                         "malformed delivery id" if status == 400 else "retry later")

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


def serve(
    config: ReceiverConfig,
    bind: tuple[str, int],
    *,
    on_listen: Callable[[HTTPServer], None] | None = None,
) -> None:
    """Listen with bounded connections and a serialized delivery pipeline.

    `on_listen` receives the bound server before it serves: a test's handle
    on the ephemeral port and on `shutdown()`. Production passes nothing.
    """

    state = _ReceiverState()
    stop = threading.Event()

    def redrain() -> None:
        # Crash recovery first, then the periodic pass for what 202'd and
        # could not complete. Damaged state is journaled, never fatal here.
        while not stop.is_set():
            with suppress(OSError, ValueError):
                drain_spool(config, state)
            with suppress(OSError, ValueError):
                refresh_awaiting(config, state)
            stop.wait(SPOOL_RETRY_SECONDS)

    drainer = threading.Thread(target=redrain, daemon=True)
    drainer.start()
    server = _BoundedServer(bind, build_handler(config, state))
    if on_listen is not None:
        on_listen(server)
    try:
        server.serve_forever()
    finally:
        stop.set()
        server.server_close()
