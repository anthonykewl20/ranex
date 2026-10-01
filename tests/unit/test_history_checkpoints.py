
import pytest

from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.history import (
    bootstrap_history,
    reconcile_anchored,
    record_anchored,
)
from ranex.governed_execution.adapters.persistence.sqlite.observations import (
    ObservationLog,
    observations_path_for,
)


def observation(code):
    return {"claim_id": "tests", "producer_id": "worker", "exit_code": code}


def setup_history(tmp_path):
    repository = tmp_path / "candidate"
    repository.mkdir()
    evidence = repository / "evidence.json"
    checkpoint = tmp_path / "retained" / "history.dsse.json"
    private, public = generate_keypair()
    bootstrap_history(evidence, checkpoint, private, public, repository)
    return evidence, checkpoint, private, public, repository


def test_explicit_empty_bootstrap_then_record_advances_signed_checkpoint(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    record_anchored(evidence, observation(0), checkpoint, private, public, repository)
    result = reconcile_anchored(evidence, checkpoint, public, repository)
    assert result.records == [observation(0)]
    assert result.position == 1
    assert result.head == ObservationLog(observations_path_for(evidence)).head()


@pytest.mark.parametrize("attack", ["truncate", "rewrite", "delete-log", "delete-checkpoint"])
def test_signed_checkpoint_refuses_all_history_rollback_modes(tmp_path, attack):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    record_anchored(evidence, observation(0), checkpoint, private, public, repository)
    record_anchored(evidence, observation(1), checkpoint, private, public, repository)
    log = ObservationLog(observations_path_for(evidence))
    if attack == "delete-checkpoint":
        checkpoint.unlink()
    else:
        log.path.unlink()
        if attack != "delete-log":
            log.append_record(observation(0))
            if attack == "rewrite":
                log.append_record(observation(0))
            assert log.verify()
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile_anchored(evidence, checkpoint, public, repository)


def test_bootstrap_cannot_reset_existing_checkpoint_or_nonempty_history(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    old = checkpoint.read_bytes()
    with pytest.raises((ValueError, FileExistsError)):
        bootstrap_history(evidence, checkpoint, private, public, repository)
    assert checkpoint.read_bytes() == old
    record_anchored(evidence, observation(1), checkpoint, private, public, repository)
    checkpoint.unlink()
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        bootstrap_history(evidence, checkpoint, private, public, repository)


def test_producer_key_cannot_advance_service_checkpoint(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    producer_private, _ = generate_keypair()
    old = checkpoint.read_bytes()
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        record_anchored(evidence, observation(1), checkpoint, producer_private, public, repository)
    assert checkpoint.read_bytes() == old
    assert ObservationLog(observations_path_for(evidence)).snapshot().position == 0


def test_checkpoint_inside_candidate_is_refused(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        bootstrap_history(evidence, repository / "checkpoint.json", private, public, repository)


def test_projection_publication_failure_preserves_certified_failure(tmp_path, monkeypatch):
    from ranex.governed_execution.adapters.persistence import history
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    record_anchored(evidence, observation(0), checkpoint, private, public, repository)
    original = history.write_atomic
    def fail_projection(target, *args, **kwargs):
        if target == evidence:
            raise OSError("injected projection publication failure")
        return original(target, *args, **kwargs)
    monkeypatch.setattr(history, "write_atomic", fail_projection)
    with pytest.raises(OSError, match="injected"):
        record_anchored(evidence, observation(1), checkpoint, private, public, repository)
    result = reconcile_anchored(evidence, checkpoint, public, repository)
    assert result.records == [observation(1)]
    assert result.removed[0].claim_id == "tests"


def test_sqlite_failure_never_poison_projection_or_checkpoint(tmp_path, monkeypatch):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    record_anchored(evidence, observation(0), checkpoint, private, public, repository)
    projection, retained = evidence.read_bytes(), checkpoint.read_bytes()
    def fail_append(*args, **kwargs):
        import sqlite3
        raise sqlite3.OperationalError("database is locked")
    monkeypatch.setattr(ObservationLog, "append_record_if_head", fail_append)
    with pytest.raises(Exception, match="locked"):
        record_anchored(evidence, observation(1), checkpoint, private, public, repository)
    assert evidence.read_bytes() == projection
    assert checkpoint.read_bytes() == retained
    assert reconcile_anchored(evidence, checkpoint, public, repository).records == [observation(0)]


def test_concurrent_writers_preserve_all_different_claims(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    records = [{"claim_id": f"claim-{i}", "producer_id": "worker", "exit_code": 0}
               for i in range(6)]
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(lambda record: record_anchored(
            evidence, record, checkpoint, private, public, repository), records))
    result = reconcile_anchored(evidence, checkpoint, public, repository)
    assert result.position == 6
    assert sorted(result.records, key=lambda r: r["claim_id"]) == records
    assert not result.removed


def test_interrupted_checkpoint_publication_requires_explicit_trusted_extension(tmp_path, monkeypatch):
    from ranex.governed_execution.adapters.persistence import history
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    record_anchored(evidence, observation(0), checkpoint, private, public, repository)
    original = history.write_atomic
    def fail_checkpoint(target, *args, **kwargs):
        if target == checkpoint:
            raise OSError("injected checkpoint failure")
        return original(target, *args, **kwargs)
    monkeypatch.setattr(history, "write_atomic", fail_checkpoint)
    with pytest.raises(OSError, match="injected"):
        record_anchored(evidence, observation(1), checkpoint, private, public, repository)
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile_anchored(evidence, checkpoint, public, repository)
    monkeypatch.setattr(history, "write_atomic", original)
    history.recover_history(evidence, checkpoint, private, public, repository)
    result = reconcile_anchored(evidence, checkpoint, public, repository)
    assert result.records == [observation(1)]
    assert result.position == 2


def test_checkpoint_cannot_be_transplanted_to_another_projection(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    foreign = repository / "foreign.json"
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile_anchored(foreign, checkpoint, public, repository)


def test_legacy_migration_is_explicit_exclusive_and_service_authorized(tmp_path):
    from ranex.governed_execution.adapters.persistence import history
    repository = tmp_path / "candidate"
    repository.mkdir()
    evidence = repository / "evidence.json"
    checkpoint = tmp_path / "retained" / "history.json"
    private, public = generate_keypair()
    record = observation(1)
    ObservationLog(observations_path_for(evidence)).append_record(record)
    evidence.write_text("[]")
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile_anchored(evidence, checkpoint, public, repository)
    history.migrate_history(evidence, checkpoint, private, public, repository)
    assert reconcile_anchored(evidence, checkpoint, public, repository).records == [record]
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        history.migrate_history(evidence, checkpoint, private, public, repository)


def _verify_in_process(anchor, public, repository, checkpoint, queue):
    from ranex.governed_execution.adapters.persistence.history import verify_bound_history
    queue.put(verify_bound_history(anchor, public, repository, checkpoint))


def test_checkpoint_fifo_is_refused_without_waiting_for_a_writer(tmp_path):
    import multiprocessing
    import os

    from ranex.governed_execution.adapters.persistence.history import checkpoint_record
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    anchor = checkpoint_record(evidence, ObservationLog(observations_path_for(evidence)).snapshot().head, 0)
    checkpoint.unlink()
    os.mkfifo(checkpoint)
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    child = context.Process(target=_verify_in_process, args=(anchor, public, repository, checkpoint, queue))
    child.start()
    try:
        child.join(timeout=1)
        assert not child.is_alive(), "checkpoint FIFO read blocked without a writer"
        assert queue.get(timeout=1) is False
    finally:
        if child.is_alive():
            child.terminate()
        child.join(timeout=2)
        queue.close()


def test_oversized_but_valid_signed_checkpoint_is_refused(tmp_path):
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    checkpoint.chmod(0o600)
    checkpoint.write_bytes(checkpoint.read_bytes() + b" " * (128 * 1024))
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile_anchored(evidence, checkpoint, public, repository)


def test_nonregular_external_lock_is_refused(tmp_path):
    import os

    from ranex.governed_execution.adapters.persistence.history import history_lock
    evidence, checkpoint, private, public, repository = setup_history(tmp_path)
    lock = checkpoint.with_name(checkpoint.name + ".lock")
    lock.unlink()
    os.mkfifo(lock)
    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        with history_lock(checkpoint):
            pass


def test_live_history_lock_reuses_snapshot_and_expired_token_refuses(tmp_path):
    from ranex.governed_execution.adapters.persistence.history import history_lock

    evidence, checkpoint, _, public, repository = setup_history(tmp_path)
    with history_lock(checkpoint) as token:
        result = reconcile_anchored(evidence, checkpoint, public, repository, held_lock=token)
        assert result.position == 0
    with pytest.raises(ValueError, match='history lock is not held'):
        reconcile_anchored(evidence, checkpoint, public, repository, held_lock=token)


def test_history_lock_token_cannot_authorize_another_checkpoint_or_thread(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    from ranex.governed_execution.adapters.persistence.history import history_lock

    evidence, checkpoint, _, public, repository = setup_history(tmp_path)
    with history_lock(checkpoint) as token:
        with pytest.raises(ValueError, match='history lock is not held'):
            reconcile_anchored(evidence, tmp_path / 'other.json', public, repository, held_lock=token)
        with ThreadPoolExecutor(max_workers=1) as workers:
            future = workers.submit(reconcile_anchored, evidence, checkpoint, public, repository,
                                    held_lock=token)
            with pytest.raises(ValueError, match='history lock is not held'):
                future.result(timeout=5)
