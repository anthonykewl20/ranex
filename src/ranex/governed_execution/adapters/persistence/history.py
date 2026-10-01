"""Service-signed history checkpoints retained outside the observed repository."""
from __future__ import annotations

import fcntl
import json
import os
import sqlite3
import stat
import threading
from collections.abc import Iterator
from contextlib import closing, contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ranex.foundation.atomic_writer import _open_created_directory, write_atomic
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.dsse import sign_envelope, verify_envelope
from ranex.foundation.history_checkpoint import validate_checkpoint
from ranex.foundation.signing import public_key_for
from ranex.foundation.suite_results import read_results_artifact
from ranex.governed_execution.adapters.persistence.sqlite.observations import (
    GENESIS,
    ObservationLog,
    Reconciliation,
    observations_path_for,
    reconcile,
)

CHECKPOINT_VARIABLE = "RANEX_HISTORY_CHECKPOINT"
CHECKPOINT_TYPE = "application/vnd.ranex.observation-checkpoint.v1+json"
ERROR = "E-OBSERVATION-ANCHOR"
MAX_CHECKPOINT_BYTES = 64 * 1024


@dataclass(eq=False, frozen=True)
class HistoryLock:
    """A live, process/thread-local capability for a retained checkpoint lock."""
    path: Path
    descriptor: int
    process: int
    thread: int

    def validate(self, path: Path) -> None:
        if (self.path != path or self.process != os.getpid()
                or self.thread != threading.get_ident()
                or _ACTIVE_LOCKS.get(self.descriptor) is not self):
            raise ValueError(f"{ERROR}: history lock is not held for this checkpoint")


_ACTIVE_LOCKS: dict[int, HistoryLock] = {}


def _drop_inherited_history_locks() -> None:
    # Fork duplicates flock's open file description. A writer child must not
    # retain its parent's publication lock while waiting for the same lock.
    for descriptor in tuple(_ACTIVE_LOCKS):
        try:
            os.close(descriptor)
        except OSError:
            pass
    _ACTIVE_LOCKS.clear()


os.register_at_fork(after_in_child=_drop_inherited_history_locks)


def checkpoint_path(value: Path | str | None, repository: Path) -> Path:
    raw = value if value is not None else os.environ.get(CHECKPOINT_VARIABLE)
    if raw is None or not str(raw).strip():
        raise ValueError(f"{ERROR}: configure an independently retained {CHECKPOINT_VARIABLE}")
    path = Path(raw).absolute()
    if not Path(raw).is_absolute():
        raise ValueError(f"{ERROR}: checkpoint must have an absolute external path")
    # Resolve ancestors for containment only; never follow a checkpoint symlink.
    if path.resolve().is_relative_to(repository.resolve()):
        raise ValueError(f"{ERROR}: checkpoint must be retained outside the candidate repository")
    if path.is_symlink():
        raise ValueError(f"{ERROR}: checkpoint symlinks are refused")
    return path


def log_id(evidence: Path) -> str:
    return str(observations_path_for(evidence).absolute())


def checkpoint_record(evidence: Path, head: str, position: int) -> dict[str, Any]:
    return {"log_id": log_id(evidence), "head": head, "position": position}




@contextmanager
def history_lock(path: Path) -> Iterator[HistoryLock]:
    """One external lock serializes bootstrap, writers and snapshot readers."""
    # Directory traversal uses the same descriptor-relative nofollow discipline
    # as durable publication; the external directory is the operator trust root.
    directory = _open_created_directory(Path(path.anchor), path.parent)
    descriptor = -1
    token: HistoryLock | None = None
    try:
        descriptor = os.open(path.name + ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
                             | os.O_CLOEXEC | os.O_NONBLOCK, 0o600, dir_fd=directory)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"{ERROR}: history lock must be a regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        token = HistoryLock(path, descriptor, os.getpid(), threading.get_ident())
        _ACTIVE_LOCKS[descriptor] = token
        yield token
    finally:
        if descriptor >= 0 and (token is None or _ACTIVE_LOCKS.get(descriptor) is token):
            _ACTIVE_LOCKS.pop(descriptor, None)
            os.close(descriptor)
        os.close(directory)


def _read_checkpoint(path: Path, expected_log_id: str, public_key: str) -> dict[str, Any]:
    try:
        envelope = json.loads(read_results_artifact(path, maximum_bytes=MAX_CHECKPOINT_BYTES))
        if not isinstance(envelope, dict) or set(envelope) != {"payloadType", "payload", "signatures"}:
            raise ValueError("invalid envelope fields")
        signatures = envelope["signatures"]
        if (not isinstance(signatures, list) or len(signatures) != 1
                or not isinstance(signatures[0], dict) or set(signatures[0]) != {"sig"}):
            raise ValueError("invalid checkpoint signatures")
        payload = verify_envelope(envelope, public_key=public_key, expected_payload_type=CHECKPOINT_TYPE)
        if payload is None:
            raise ValueError("invalid checkpoint signature")
        record = json.loads(payload)
        if not validate_checkpoint(record) or canonical_json_bytes(record) != payload:
            raise ValueError("invalid checkpoint record")
        if record["log_id"] != expected_log_id:
            raise ValueError("checkpoint belongs to another observation log")
        return record
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise ValueError(f"{ERROR}: cannot verify retained checkpoint: {exc}") from exc


def _read(path: Path, evidence: Path, public_key: str) -> dict[str, Any]:
    return _read_checkpoint(path, log_id(evidence), public_key)


def verify_bound_history(anchor: Any, public_key: str, repository: Path,
                         checkpoint: Path | None = None) -> bool:
    """A receipt may authorize only the currently certified history snapshot."""
    if not validate_checkpoint(anchor):
        return False
    try:
        path = checkpoint_path(checkpoint, repository)
        log = ObservationLog(Path(anchor["log_id"]))
        if not log.path.absolute().is_relative_to(repository.absolute()):
            return False
        with history_lock(path):
            retained = _read_checkpoint(path, anchor["log_id"], public_key)
            if retained != anchor:
                return False
            snapshot = log.snapshot(expected_head=retained["head"])
            return (snapshot.head, snapshot.position) == (retained["head"], retained["position"])
    except (OSError, ValueError, sqlite3.Error):
        return False


def _write(path: Path, record: dict[str, Any], private_key: str, *, exclusive=False) -> None:
    envelope = sign_envelope(payload_type=CHECKPOINT_TYPE, payload=canonical_json_bytes(record), private_key=private_key)
    write_atomic(path, canonical_json_bytes(envelope) + b"\n", root=Path(path.anchor), exclusive=exclusive)


def _key(private_key: str, public_key: str) -> None:
    if public_key_for(private_key) != public_key:
        raise ValueError(f"{ERROR}: history signing key does not match the trusted verdict signer")


def _snapshot(evidence: Path, retained: dict[str, Any]):
    log = ObservationLog(observations_path_for(evidence))
    snapshot = log.snapshot(expected_head=retained["head"])
    # Every durable observation is certified before success is reported. An
    # unsigned suffix is incomplete storage, not evidence eligible for judgment.
    if (snapshot.head, snapshot.position) != (retained["head"], retained["position"]):
        raise ValueError(f"{ERROR}: history differs from the current signed checkpoint")
    return log, snapshot


def _evidence(path: Path) -> list[Any]:
    try:
        records = json.loads(path.read_bytes())
    except FileNotFoundError:
        return []
    if not isinstance(records, list):
        raise ValueError("evidence file must contain a JSON array")
    return records


def bootstrap_history(evidence: Path, checkpoint: Path, private_key: str,
                      public_key: str, repository: Path) -> None:
    """Explicit initial ceremony. Never reset a checkpoint or migrate implicitly."""
    checkpoint = checkpoint_path(checkpoint, repository)
    _key(private_key, public_key)
    with history_lock(checkpoint):
        if checkpoint.exists():
            raise ValueError(f"{ERROR}: bootstrap refuses an existing checkpoint")
        log = ObservationLog(observations_path_for(evidence))
        if _evidence(evidence) or log.snapshot().position != 0:
            raise ValueError(f"{ERROR}: bootstrap requires empty history; retained history cannot be reset")
        with closing(log._connect()):
            pass
        _write(checkpoint, checkpoint_record(evidence, GENESIS, 0), private_key, exclusive=True)


def migrate_history(evidence: Path, checkpoint: Path, private_key: str,
                    public_key: str, repository: Path) -> None:
    """Explicitly trust a legacy verified history, creating its first anchor.

    This is an operator ceremony with service-key possession, never a normal
    admission fallback. No pre-migration authenticity of the chain is claimed.
    """
    checkpoint = checkpoint_path(checkpoint, repository)
    _key(private_key, public_key)
    with history_lock(checkpoint):
        if checkpoint.exists():
            raise ValueError(f"{ERROR}: migration refuses an existing checkpoint")
        log = ObservationLog(observations_path_for(evidence))
        if not log.path.is_file():
            raise ValueError(f"{ERROR}: migration requires an existing observation log")
        snapshot = log.snapshot()
        projection = _evidence(evidence)
        result = reconcile(log, projection, snapshot=snapshot)
        if any(not result.in_chain(item) for item in projection):
            raise ValueError("E-OBSERVATION-CHAIN: projection includes unchained records")
        _write(checkpoint, checkpoint_record(evidence, snapshot.head, snapshot.position),
               private_key, exclusive=True)
        write_atomic(evidence, canonical_json_bytes(result.records) + b"\n", root=repository)


def reconcile_anchored(evidence: Path, checkpoint: Path | None, public_key: str,
                       repository: Path, *, held_lock: HistoryLock | None = None) -> Reconciliation:
    checkpoint = checkpoint_path(checkpoint, repository)
    if held_lock is not None:
        held_lock.validate(checkpoint)
    with nullcontext(held_lock) if held_lock is not None else history_lock(checkpoint):
        retained = _read(checkpoint, evidence, public_key)
        log, snapshot = _snapshot(evidence, retained)
        records = _evidence(evidence)
        result = reconcile(log, records, snapshot=snapshot)
        if any(not result.in_chain(record) for record in records):
            raise ValueError("E-OBSERVATION-CHAIN: projection includes unchained records")
        return result


def record_anchored(evidence: Path, record: dict[str, Any], checkpoint: Path | None,
                    private_key: str, public_key: str, repository: Path) -> None:
    checkpoint = checkpoint_path(checkpoint, repository)
    _key(private_key, public_key)
    with history_lock(checkpoint):
        retained = _read(checkpoint, evidence, public_key)
        log, snapshot = _snapshot(evidence, retained)
        projection = _evidence(evidence)
        existing = reconcile(log, projection, snapshot=snapshot)
        if any(not existing.in_chain(item) for item in projection):
            raise ValueError("E-OBSERVATION-CHAIN: projection includes unchained records")
        # Durable history precedes its rebuildable projection. A projection
        # failure leaves a signed observation that reconciliation can restore.
        appended = log.append_record_if_head(snapshot.head if snapshot.position else None, record)
        _write(checkpoint, checkpoint_record(evidence, appended.head, appended.position), private_key)
        kept = [item for item in existing.records if not (
            isinstance(item, dict) and item.get("claim_id") == record["claim_id"]
            and item.get("producer_id") == record["producer_id"])]
        kept.append(record)
        write_atomic(evidence, canonical_json_bytes(kept) + b"\n", root=repository)


def recover_history(evidence: Path, checkpoint: Path, private_key: str,
                    public_key: str, repository: Path) -> None:
    """Explicit service-key ceremony after an interrupted checkpoint write.

    The old signed checkpoint must still exist in the verified chain at its
    original position. Recovery may certify its extension; it cannot reset,
    truncate, transplant or bootstrap a lost retained checkpoint.
    """
    checkpoint = checkpoint_path(checkpoint, repository)
    _key(private_key, public_key)
    with history_lock(checkpoint):
        retained = _read(checkpoint, evidence, public_key)
        log = ObservationLog(observations_path_for(evidence))
        snapshot = log.snapshot(expected_head=retained["head"])
        if retained["position"]:
            # Bind the retained head's position too, not just its membership.
            from ranex.foundation.canonical import canonical_sha256
            head = GENESIS
            found = False
            for position, record in snapshot.records:
                head = "sha256:" + canonical_sha256({"prev_link": head, "record": record})
                if head == retained["head"]:
                    found = position == retained["position"]
                    break
            if not found:
                raise ValueError(f"{ERROR}: retained checkpoint position changed")
        projection = _evidence(evidence)
        result = reconcile(log, projection, snapshot=snapshot)
        if any(not result.in_chain(item) for item in projection):
            raise ValueError("E-OBSERVATION-CHAIN: projection includes unchained records")
        _write(checkpoint, checkpoint_record(evidence, snapshot.head, snapshot.position), private_key)
        write_atomic(evidence, canonical_json_bytes(result.records) + b"\n", root=repository)
