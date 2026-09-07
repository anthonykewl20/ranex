"""Durability arms for the receiver: acknowledge in time, publish once.

GitHub abandons a delivery it has not heard back from within ten seconds, so
the listener spools every proven delivery before it works on it and answers
202 when the pipeline outlasts the acknowledgement deadline. A retry after a
publication that reached GitHub but not the local completion receipt must
reconcile against the check GitHub already holds instead of publishing twice.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

import _github_fake
import pytest

from ranex.github_app import receiver
from ranex.github_app.receiver import build_handler, drain_spool, process_delivery
from ranex.github_app.webhook import delivery_signature

SECRET = _github_fake.WEBHOOK_SECRET
event_body = _github_fake.pull_request_event_body
receiver_environment = _github_fake.receiver_environment


def _signed(port: int, body: bytes, delivery: str) -> Request:
    return Request(
        f"http://127.0.0.1:{port}/webhook",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": delivery_signature(SECRET, body),
            "X-GitHub-Delivery": delivery,
            "X-GitHub-Event": "pull_request",
        },
    )


def _wait_for(predicate, *, seconds: float = 10.0) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("condition did not hold in time")
        time.sleep(0.05)


def test_a_slow_publication_is_acknowledged_before_the_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(receiver, "ACK_DEADLINE_SECONDS", 0.5)
    with receiver_environment(tmp_path) as env:
        server = HTTPServer(("127.0.0.1", 0), build_handler(env.config, env.state))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        original = env.config.client.create_check_run

        def slow(*args, **kwargs):
            time.sleep(1.5)
            return original(*args, **kwargs)

        try:
            body = event_body(env.head)
            with patch.object(env.config.client, "create_check_run", slow):
                started = time.monotonic()
                with urlopen(_signed(server.server_address[1], body, "d-slow"), timeout=10) as response:
                    status = response.status
                elapsed = time.monotonic() - started
                assert status == 202
                assert elapsed < 1.5
                spooled = tmp_path / "state" / "spool" / "d-slow.json"
                assert spooled.exists()
                _wait_for(lambda: (tmp_path / "state" / "completed" / "d-slow.json").exists())
                _wait_for(lambda: not spooled.exists())
            assert len(env.fake.check_requests) == 1
            journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
            assert "published:success" in journal
        finally:
            server.shutdown()
            server.server_close()


def test_a_fast_delivery_still_answers_its_real_status_and_leaves_no_spool(
    tmp_path: Path,
) -> None:
    with receiver_environment(tmp_path) as env:
        server = HTTPServer(("127.0.0.1", 0), build_handler(env.config, env.state))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with urlopen(_signed(server.server_address[1], event_body(env.head), "d-fast"), timeout=10) as response:
                assert response.status == 200
            assert not (tmp_path / "state" / "spool" / "d-fast.json").exists()
            assert len(env.fake.check_requests) == 1
        finally:
            server.shutdown()
            server.server_close()


def test_a_spooled_delivery_survives_a_restart_and_drains_once(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)
        receiver.spool_delivery(env.config, body, "d-crash", "pull_request")
        assert (tmp_path / "state" / "spool" / "d-crash.json").exists()

        drained = drain_spool(env.config, env.state)

        assert drained == {"d-crash": 200}
        assert not (tmp_path / "state" / "spool" / "d-crash.json").exists()
        assert (tmp_path / "state" / "completed" / "d-crash.json").exists()
        assert len(env.fake.check_requests) == 1
        # A second pass finds nothing; the completed receipt guards a replay.
        assert drain_spool(env.config, env.state) == {}
        assert len(env.fake.check_requests) == 1


def test_a_spooled_delivery_that_cannot_complete_stays_spooled(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        receiver.spool_delivery(
            env.config, event_body("9" * 40), "d-unfetchable", "pull_request"
        )
        assert drain_spool(env.config, env.state) == {"d-unfetchable": 500}
        spool = tmp_path / "state" / "spool"
        assert (spool / "d-unfetchable.json").exists()
        assert env.fake.check_requests == []
        # A failed attempt backs off: the next pass (and a restart's startup
        # pass) leaves it alone until SPOOL_RETRY_SECONDS have elapsed, so a
        # stuck entry cannot hold the pipeline against live deliveries.
        assert (spool / "d-unfetchable.failed").exists()
        assert drain_spool(env.config, env.state) == {}
        with patch.object(receiver, "SPOOL_RETRY_SECONDS", 0):
            assert drain_spool(env.config, env.state) == {"d-unfetchable": 500}


def test_a_damaged_spool_entry_is_journaled_and_left_for_the_operator(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        spool = tmp_path / "state" / "spool"
        spool.mkdir(parents=True)
        (spool / "d-damaged.json").write_bytes(b"{not json")
        assert drain_spool(env.config, env.state) == {"d-damaged": 500}
        assert (spool / "d-damaged.json").exists()
        # Journaled once per backoff window, not once per pass.
        assert drain_spool(env.config, env.state) == {}
        rows = [json.loads(line) for line in (tmp_path / "state" / "deliveries.jsonl").read_text().splitlines()]
        assert rows[-1] == {"delivery": "d-damaged", "outcome": "spool-unreadable"}
        assert env.fake.check_requests == []


def test_a_retry_after_a_lost_completion_reconciles_instead_of_republishing(
    tmp_path: Path,
) -> None:
    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)
        original = receiver.write_atomic

        def fail_completion(path, *args, **kwargs):
            if Path(path).parent.name == "completed":
                raise OSError("injected completion persistence failure")
            return original(path, *args, **kwargs)

        with patch.object(receiver, "write_atomic", fail_completion), pytest.raises(OSError):
            process_delivery(env.config, env.state, body, "d-lost", "pull_request")
        assert len(env.fake.check_requests) == 1
        assert env.fake.check_requests[0]["body"]["external_id"] == "d-lost"

        status = process_delivery(env.config, env.state, body, "d-lost", "pull_request")

        assert status == 200
        assert len(env.fake.check_requests) == 1
        assert (tmp_path / "state" / "completed" / "d-lost.json").exists()
        journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
        assert "reconciled:success" in journal


def test_a_retry_after_a_crash_before_publication_publishes_exactly_once(
    tmp_path: Path,
) -> None:
    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)

        def crash(*args, **kwargs):
            raise OSError("injected crash before the API call")

        with patch.object(env.config.client, "create_check_run", crash), pytest.raises(OSError):
            process_delivery(env.config, env.state, body, "d-early", "pull_request")
        assert (tmp_path / "state" / "attempted" / "d-early.json").exists()
        assert env.fake.check_requests == []

        assert process_delivery(env.config, env.state, body, "d-early", "pull_request") == 200
        assert len(env.fake.check_requests) == 1
        assert "published:success" in (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_reconciliation_never_trusts_a_check_for_another_head(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)
        attempted = tmp_path / "state" / "attempted"
        attempted.mkdir(parents=True)
        # A stale attempt record naming a different head cannot satisfy this
        # delivery: the pipeline runs and publishes for the real head.
        receiver.write_atomic(
            attempted / "d-stale.json",
            json.dumps({"head_sha": "9" * 40}).encode(),
            root=tmp_path / "state",
        )
        assert process_delivery(env.config, env.state, body, "d-stale", "pull_request") == 200
        assert len(env.fake.check_requests) == 1
        assert env.fake.check_requests[0]["body"]["head_sha"] == env.head


def test_the_listener_drains_its_spool_at_start_and_then_serves(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        for index in range(3):
            receiver.spool_delivery(
                env.config, event_body(env.head), f"d-before-start-{index}", "pull_request",
            )
        servers: list = []
        listening = threading.Event()
        original = env.config.client.create_check_run

        def slow(*args, **kwargs):
            time.sleep(0.6)
            return original(*args, **kwargs)

        def on_listen(server) -> None:
            servers.append(server)
            listening.set()

        thread = threading.Thread(
            target=receiver.serve, args=(env.config, ("127.0.0.1", 0)),
            kwargs={"on_listen": on_listen}, daemon=True,
        )
        with patch.object(env.config.client, "create_check_run", slow):
            thread.start()
            assert listening.wait(10)
            try:
                # The startup pass holds the pipeline; a live delivery waits
                # for it instead of being refused 503, and the pass yields to
                # it after the entry in flight.
                port = servers[0].server_address[1]
                started = time.monotonic()
                with urlopen(_signed(port, event_body(env.head), "d-live"), timeout=10) as response:
                    assert response.status == 200
                assert time.monotonic() - started < receiver.ACK_DEADLINE_SECONDS
                journal = (tmp_path / "state" / "deliveries.jsonl").read_text()
                assert journal.count("published:success") < 4
                try:
                    # The drain's observable end state is receipts present AND
                    # the spool released: a receipt is written inside the
                    # pipeline while _unspool runs after it returns, so under
                    # load the two lag each other by a real window.
                    _wait_for(lambda: all(
                        (tmp_path / "state" / "completed" / f"d-before-start-{i}.json").exists()
                        for i in range(3)
                    ) and not any((tmp_path / "state" / "spool").glob("*.json")),
                        seconds=30)
                except AssertionError as error:
                    raise AssertionError(
                        (tmp_path / "state" / "deliveries.jsonl").read_text()
                        + str(sorted(p.name for p in (tmp_path / "state" / "spool").iterdir()))
                    ) from error
            finally:
                servers[0].shutdown()
                thread.join(10)
        assert not thread.is_alive()
        assert len(env.fake.check_requests) == 4


def test_the_handler_names_state_failures_and_bad_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with receiver_environment(tmp_path) as env:
        server = HTTPServer(("127.0.0.1", 0), build_handler(env.config, env.state))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = server.server_address[1]
        body = event_body(env.head)
        try:
            with pytest.raises(Exception) as bad_id:
                urlopen(_signed(port, body, "../outside"), timeout=10)
            assert bad_id.value.code == 400

            def unwritable(*args, **kwargs):
                raise OSError("injected spool failure")

            monkeypatch.setattr(receiver, "spool_delivery", unwritable)
            with pytest.raises(Exception) as no_state:
                urlopen(_signed(port, body, "d-nospool"), timeout=10)
            assert no_state.value.code == 500
            monkeypatch.undo()

            def damaged(*args, **kwargs):
                raise ValueError("injected damaged receipt")

            monkeypatch.setattr(receiver, "process_delivery", damaged)
            with pytest.raises(Exception) as damaged_state:
                urlopen(_signed(port, body, "d-damaged"), timeout=10)
            assert damaged_state.value.code == 500
            # Answered synchronously, the spool has nothing left to say.
            assert not (tmp_path / "state" / "spool" / "d-damaged.json").exists()
            assert env.fake.check_requests == []
        finally:
            server.shutdown()
            server.server_close()


def test_spool_bookkeeping_refuses_bad_ids_shapes_and_absent_state(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        assert receiver.spool_delivery(env.config, b"{}", "../x", "ping") == 400
        assert drain_spool(env.config, env.state) == {}
        spool = tmp_path / "state" / "spool"
        spool.mkdir(parents=True)
        (spool / "d-shape.json").write_bytes(b'{"body": "00"}')
        # A live delivery waiting for the pipeline stops the pass before it
        # touches an entry; the pass resumes right after that delivery.
        env.state.demand = 1
        assert drain_spool(env.config, env.state) == {}
        assert env.state.yielded is True
        env.state.demand = 0
        env.state.yielded = False
        assert drain_spool(env.config, env.state) == {"d-shape": 500}
        assert (spool / "d-shape.json").exists()


def test_a_drain_that_hits_damaged_state_keeps_the_entry(tmp_path: Path) -> None:
    with receiver_environment(tmp_path) as env:
        receiver.spool_delivery(env.config, event_body(env.head), "d-keep", "pull_request")
        original = receiver.write_atomic

        def fail_completion(path, *args, **kwargs):
            if Path(path).parent.name == "completed":
                raise OSError("injected completion persistence failure")
            return original(path, *args, **kwargs)

        with patch.object(receiver, "write_atomic", fail_completion):
            assert drain_spool(env.config, env.state) == {"d-keep": 500}
        assert (tmp_path / "state" / "spool" / "d-keep.json").exists()
        # Once the backoff has elapsed, the next pass reconciles the check
        # that already reached GitHub, and the failure marker goes with it.
        with patch.object(receiver, "SPOOL_RETRY_SECONDS", 0):
            assert drain_spool(env.config, env.state) == {"d-keep": 200}
        assert not (tmp_path / "state" / "spool" / "d-keep.failed").exists()
        assert len(env.fake.check_requests) == 1
        assert "reconciled:success" in (tmp_path / "state" / "deliveries.jsonl").read_text()


def test_completion_receipts_guard_replays_conflicts_and_damage(tmp_path: Path) -> None:
    import fcntl

    with receiver_environment(tmp_path) as env:
        body = event_body(env.head)
        assert process_delivery(env.config, env.state, body, "d-1", "pull_request") == 200
        assert process_delivery(env.config, env.state, body + b" ", "d-1", "pull_request") == 409
        assert len(env.fake.check_requests) == 1

        # The in-process pipeline lock and the cross-process file lock each
        # answer 503 without touching the receipt store.
        assert env.state.lock.acquire(blocking=False)
        try:
            assert process_delivery(env.config, env.state, body, "d-2", "pull_request") == 503
        finally:
            env.state.lock.release()
        with (tmp_path / "state" / "receiver.lock").open("a") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            assert process_delivery(env.config, env.state, body, "d-2", "pull_request") == 503
        assert len(env.fake.check_requests) == 1

        completed = tmp_path / "state" / "completed"
        for name, damage in (("d-shape", b"[]"), ("d-digest", b'{"fingerprint": "nope"}')):
            path = completed / f"{name}.json"
            path.write_bytes(damage)
            with pytest.raises(ValueError):
                process_delivery(env.config, env.state, body, name, "pull_request")
        assert len(env.fake.check_requests) == 1
