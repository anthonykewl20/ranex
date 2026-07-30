BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS execution_state (
    execution_id TEXT PRIMARY KEY,
    canonical_state_json TEXT NOT NULL,
    version INTEGER NOT NULL CHECK (version >= 1),
    last_event_id TEXT NOT NULL UNIQUE,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_journal (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    execution_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_version INTEGER NOT NULL CHECK (previous_version >= 0),
    resulting_version INTEGER NOT NULL,
    event_json TEXT NOT NULL,
    previous_state_sha256 TEXT,
    resulting_state_sha256 TEXT NOT NULL,
    resulting_state_json TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (execution_id)
        REFERENCES execution_state(execution_id),
    UNIQUE (execution_id, resulting_version),
    CHECK (resulting_version = previous_version + 1),
    CHECK (
        (previous_version = 0 AND previous_state_sha256 IS NULL)
        OR
        (previous_version > 0 AND length(previous_state_sha256) = 64)
    ),
    CHECK (length(resulting_state_sha256) = 64)
);

CREATE TABLE IF NOT EXISTS execution_outbox (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    execution_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 1),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (event_id)
        REFERENCES execution_journal(event_id),
    UNIQUE (execution_id, aggregate_version)
);

CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
BEFORE UPDATE ON execution_journal
BEGIN
    SELECT RAISE(ABORT, 'execution_journal is append-only');
END;

CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
BEFORE DELETE ON execution_journal
BEGIN
    SELECT RAISE(ABORT, 'execution_journal is append-only');
END;

CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
BEFORE UPDATE ON execution_outbox
BEGIN
    SELECT RAISE(ABORT, 'execution_outbox is append-only');
END;

CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
BEFORE DELETE ON execution_outbox
BEGIN
    SELECT RAISE(ABORT, 'execution_outbox is append-only');
END;

PRAGMA user_version = 1;

COMMIT;
