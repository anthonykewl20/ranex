Reading additional input from stdin...
OpenAI Codex v0.146.0
--------
workdir: /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: max
reasoning summaries: none
session id: 019fb1ca-a9f2-7552-8ac3-9cac801c0eed
--------
user
# Independent code review — kernel R&D tracer

You are reviewing code adversarially. Findings without `path:line` citations will be
discarded. Do not modify, create, or delete any file — read-only analysis; you may run
the existing tests (`uv run pytest`) read-only.

## Subject

This working tree, branch `feature/kernel-tracer`: `src/ranex/` and `tests/`
(untracked files — read from the filesystem). Python, SQLite, no external services.
R&D tracer code; correctness of the core mechanics is the review target.

## Review targets, in priority order

1. `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py` —
   transaction boundaries, isolation, the compare-and-swap on `version`, crash windows
   between journal append / outbox write / snapshot update, connection handling,
   error paths that can commit partial state.
2. `src/ranex/governed_execution/domain/execution.py` — reducer determinism, input
   mutation, exception safety, exhaustiveness over event types.
3. `src/ranex/governed_execution/application/application_control_pep.py` and
   `src/ranex/governed_execution/application/gate_controller.py` — every path that
   returns an allow/deny; whether any exception, missing input, or unknown value
   reaches allow.
4. `src/ranex/foundation/canonical.py` and `src/ranex/foundation/identity.py` —
   canonicalization stability (dict ordering, float/unicode edge cases), digest use.
5. `tests/` — do the replay, crash-boundary, and migration tests exercise real
   boundaries or mocks; missing failure-path coverage.

## Report format

For each finding: severity (BLOCKER/MAJOR/MINOR), one-sentence claim, `path:line`,
and a concrete failure scenario (inputs/state → wrong outcome). List separately any
inference you made that the code does not literally state. If a target area is clean,
list the files and line ranges you examined.

Print the full report to stdout as your final answer.
codex
I’ll trace the persistence transaction and failure paths first, then the reducer and policy decisions, and finally validate test coverage against the real boundaries. I’ll keep the workspace strictly read-only.
  → Inspect repository guidance, subject files, and related schemas/types
  • Analyze persistence transactions, CAS, crash windows, and connection/error handling
  • Analyze reducer, policy allow/deny paths, and canonical identity mechanics
  • Run existing tests and audit boundary/failure-path coverage
  • Produce cited adversarial review with findings, inferences, and clean ranges
exec
/bin/bash -lc 'git status --short --branch' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc pwd in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer

 succeeded in 0ms:
## feature/kernel-tracer
 M .gitignore
?? pyproject.toml
?? src/
?? tests/
?? uv.lock

exec
/bin/bash -lc 'rg --files src/ranex tests | sort' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
src/ranex/__init__.py
src/ranex/assurance/__init__.py
src/ranex/assurance/adapters/__init__.py
src/ranex/assurance/adapters/filesystem/__init__.py
src/ranex/assurance/adapters/filesystem/artifact_verifier.py
src/ranex/assurance/adapters/persistence/__init__.py
src/ranex/assurance/adapters/persistence/jsonl/__init__.py
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py
src/ranex/assurance/api/__init__.py
src/ranex/assurance/api/contracts.py
src/ranex/assurance/domain/__init__.py
src/ranex/assurance/domain/gates.py
src/ranex/foundation/__init__.py
src/ranex/foundation/canonical.py
src/ranex/foundation/identity.py
src/ranex/governed_execution/__init__.py
src/ranex/governed_execution/adapters/__init__.py
src/ranex/governed_execution/adapters/persistence/__init__.py
src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
src/ranex/governed_execution/adapters/policy/__init__.py
src/ranex/governed_execution/adapters/policy/deterministic.py
src/ranex/governed_execution/application/__init__.py
src/ranex/governed_execution/application/application_control_pep.py
src/ranex/governed_execution/application/gate_controller.py
src/ranex/governed_execution/application/ports/__init__.py
src/ranex/governed_execution/application/ports/application_control_policy.py
src/ranex/governed_execution/application/ports/execution_repository.py
src/ranex/governed_execution/domain/__init__.py
src/ranex/governed_execution/domain/application_control.py
src/ranex/governed_execution/domain/events.py
src/ranex/governed_execution/domain/execution.py
src/ranex/governed_execution/domain/status.py
src/ranex/policy/__init__.py
src/ranex/policy/adapters/__init__.py
src/ranex/policy/adapters/configuration/__init__.py
src/ranex/policy/adapters/configuration/yaml/__init__.py
src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py
src/ranex/policy/api/__init__.py
src/ranex/policy/api/contracts.py
src/ranex/policy/domain/__init__.py
src/ranex/policy/domain/gates.py
src/ranex/work_management/__init__.py
src/ranex/work_management/api/__init__.py
src/ranex/work_management/api/contracts.py
src/ranex/work_management/domain/__init__.py
src/ranex/work_management/domain/transitions.py
tests/architecture/test_kernel_imports.py
tests/contract/policy/test_gate_policy_loader.py
tests/integration/assurance/test_evidence_artifact_verifier.py
tests/integration/assurance/test_hash_chain_ledger.py
tests/integration/governed_execution/test_sqlite_execution_store.py
tests/migration/governed_execution/test_execution_store_migration.py
tests/replay/governed_execution/test_execution_replay.py
tests/resilience/test_execution_sqlite_crash_boundary.py
tests/security/test_application_control_pep.py
tests/unit/foundation/domain/test_canonical.py
tests/unit/foundation/domain/test_identity.py
tests/unit/governed_execution/application/test_gate_controller.py
tests/unit/governed_execution/domain/test_application_control.py
tests/unit/governed_execution/domain/test_execution.py
tests/unit/work_management/domain/test_transitions.py

exec
/bin/bash -lc 'find .. -name AGENTS.md -print' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 41ms:
../phase-2-runtime-bootstrap/apps/desktop/AGENTS.md
../phase-2-runtime-bootstrap/node_modules/cytoscape/AGENTS.md
../phase-2-runtime-bootstrap/AGENTS.md
../phase-1-adopt-upstream/apps/desktop/AGENTS.md
../phase-1-adopt-upstream/AGENTS.md
../gate-controller-mvp/apps/desktop/AGENTS.md
../gate-controller-mvp/AGENTS.md
../architecture-validated-baseline/apps/desktop/AGENTS.md
../architecture-validated-baseline/AGENTS.md

exec
/bin/bash -lc 'find /home/soultransit/devtony/ranex -maxdepth 1 -name AGENTS.md -print' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/domain/execution.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/domain/events.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/domain/application_control.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/domain/status.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/application/application_control_pep.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
420 src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py

 succeeded in 0ms:
73 src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql

 succeeded in 0ms:
237 src/ranex/governed_execution/domain/execution.py

 succeeded in 0ms:
197 src/ranex/governed_execution/domain/events.py

 succeeded in 0ms:
77 src/ranex/governed_execution/domain/application_control.py

 succeeded in 0ms:
23 src/ranex/governed_execution/domain/status.py

 succeeded in 0ms:
53 src/ranex/governed_execution/application/application_control_pep.py

exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/application/gate_controller.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
222 src/ranex/governed_execution/application/gate_controller.py

exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/application/ports/execution_repository.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
17 src/ranex/governed_execution/application/ports/execution_repository.py

exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/application/ports/application_control_policy.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
19 src/ranex/governed_execution/application/ports/application_control_policy.py

exec
/bin/bash -lc 'wc -l src/ranex/governed_execution/adapters/policy/deterministic.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
47 src/ranex/governed_execution/adapters/policy/deterministic.py

exec
/bin/bash -lc 'wc -l src/ranex/foundation/canonical.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
26 src/ranex/foundation/canonical.py

exec
/bin/bash -lc 'wc -l src/ranex/foundation/identity.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
53 src/ranex/foundation/identity.py

exec
/bin/bash -lc "nl -ba src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '1,220p'" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import json
     4	import sqlite3
     5	from collections.abc import Mapping
     6	from contextlib import closing
     7	from pathlib import Path
     8	
     9	from ranex.foundation.canonical import canonical_json, canonical_sha256
    10	from ranex.foundation.identity import Identity
    11	from ranex.governed_execution.application.ports.execution_repository import (
    12	    ExecutionRepository,
    13	)
    14	from ranex.governed_execution.domain.events import (
    15	    ExecutionBlocked,
    16	    ExecutionCancelled,
    17	    ExecutionCreated,
    18	    ExecutionEvent,
    19	    ExecutionFailed,
    20	    ExecutionMarkedReady,
    21	    ExecutionResumed,
    22	    ExecutionStarted,
    23	    ExecutionSucceeded,
    24	    ExecutionUnblocked,
    25	    ExecutionWaited,
    26	)
    27	from ranex.governed_execution.domain.execution import (
    28	    Execution,
    29	    reduce_execution,
    30	)
    31	from ranex.governed_execution.domain.status import ExecutionStatus
    32	
    33	_MIGRATION = Path(__file__).with_name("migrations") / "001_execution_kernel.sql"
    34	_STATE_FIELDS = frozenset(
    35	    {
    36	        "schema_version",
    37	        "execution_id",
    38	        "work_item_id",
    39	        "created_by_principal_id",
    40	        "workflow_request_ref",
    41	        "status",
    42	        "version",
    43	        "last_event_id",
    44	        "updated_at",
    45	        "blocked_from_status",
    46	    }
    47	)
    48	
    49	
    50	class ExecutionPersistenceIntegrityError(RuntimeError):
    51	    """Stored execution bytes disagree with their relational metadata."""
    52	
    53	
    54	class ConcurrentExecutionWriteError(RuntimeError):
    55	    """The expected canonical execution version changed before commit."""
    56	
    57	
    58	def _execution_to_document(execution: Execution) -> dict[str, object]:
    59	    return {
    60	        "schema_version": "execution-state/v1",
    61	        "execution_id": str(execution.execution_id),
    62	        "work_item_id": str(execution.work_item_id),
    63	        "created_by_principal_id": str(execution.created_by_principal_id),
    64	        "workflow_request_ref": execution.workflow_request_ref,
    65	        "status": execution.status.value,
    66	        "version": execution.version,
    67	        "last_event_id": str(execution.last_event_id),
    68	        "updated_at": execution.updated_at,
    69	        "blocked_from_status": (
    70	            execution.blocked_from_status.value
    71	            if execution.blocked_from_status is not None
    72	            else None
    73	        ),
    74	    }
    75	
    76	
    77	def _require_string(value: object, field: str) -> str:
    78	    if not isinstance(value, str) or not value:
    79	        raise ValueError(f"{field} must be a non-empty string")
    80	    return value
    81	
    82	
    83	def _execution_from_document(document: Mapping[str, object]) -> Execution:
    84	    if set(document) != _STATE_FIELDS:
    85	        raise ValueError("canonical execution state has unexpected fields")
    86	    if document["schema_version"] != "execution-state/v1":
    87	        raise ValueError("unsupported execution state schema version")
    88	    version = document["version"]
    89	    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
    90	        raise ValueError("execution state version must be a positive integer")
    91	    blocked_from_value = document["blocked_from_status"]
    92	    blocked_from = (
    93	        None
    94	        if blocked_from_value is None
    95	        else ExecutionStatus(_require_string(blocked_from_value, "blocked_from_status"))
    96	    )
    97	    return Execution(
    98	        execution_id=Identity.parse(
    99	            _require_string(document["execution_id"], "execution_id"),
   100	            expected_prefix="run",
   101	        ),
   102	        work_item_id=Identity.parse(
   103	            _require_string(document["work_item_id"], "work_item_id"),
   104	            expected_prefix="work",
   105	        ),
   106	        created_by_principal_id=Identity.parse(
   107	            _require_string(
   108	                document["created_by_principal_id"],
   109	                "created_by_principal_id",
   110	            ),
   111	            expected_prefix="principal",
   112	        ),
   113	        workflow_request_ref=_require_string(
   114	            document["workflow_request_ref"],
   115	            "workflow_request_ref",
   116	        ),
   117	        status=ExecutionStatus(_require_string(document["status"], "status")),
   118	        version=version,
   119	        last_event_id=Identity.parse(
   120	            _require_string(document["last_event_id"], "last_event_id"),
   121	            expected_prefix="transition",
   122	        ),
   123	        updated_at=_require_string(document["updated_at"], "updated_at"),
   124	        blocked_from_status=blocked_from,
   125	    )
   126	
   127	
   128	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   129	    document: dict[str, object] = {
   130	        "schema_version": "execution-event/v1",
   131	        "event_type": type(event).__name__,
   132	        "event_id": str(event.event_id),
   133	        "execution_id": str(event.execution_id),
   134	        "expected_version": event.expected_version,
   135	        "occurred_at": event.occurred_at,
   136	    }
   137	    if isinstance(event, ExecutionCreated):
   138	        document.update(
   139	            {
   140	                "work_item_id": str(event.work_item_id),
   141	                "created_by_principal_id": str(event.created_by_principal_id),
   142	                "workflow_request_ref": event.workflow_request_ref,
   143	            }
   144	        )
   145	    elif isinstance(event, ExecutionMarkedReady):
   146	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
   147	    elif isinstance(event, ExecutionStarted):
   148	        document["authorization_ref"] = event.authorization_ref
   149	    elif isinstance(event, ExecutionWaited):
   150	        document["wait_reason_code"] = event.wait_reason_code
   151	    elif isinstance(event, ExecutionResumed):
   152	        document["signal_ref"] = event.signal_ref
   153	    elif isinstance(event, ExecutionBlocked):
   154	        document.update(
   155	            {
   156	                "block_reason_code": event.block_reason_code,
   157	                "blocking_refs": list(event.blocking_refs),
   158	            }
   159	        )
   160	    elif isinstance(event, ExecutionUnblocked):
   161	        document.update(
   162	            {
   163	                "target_status": event.target_status.value,
   164	                "refreshed_evidence_ref": event.refreshed_evidence_ref,
   165	            }
   166	        )
   167	    elif isinstance(event, ExecutionSucceeded):
   168	        document["outcome_ref"] = event.outcome_ref
   169	    elif isinstance(event, ExecutionFailed):
   170	        document.update(
   171	            {
   172	                "failure_reason_code": event.failure_reason_code,
   173	                "evidence_ref": event.evidence_ref,
   174	            }
   175	        )
   176	    elif isinstance(event, ExecutionCancelled):
   177	        document["decision_ref"] = event.decision_ref
   178	    else:
   179	        raise TypeError(f"unsupported execution event: {type(event).__name__}")
   180	    return document
   181	
   182	
   183	class SQLiteExecutionStore(ExecutionRepository):
   184	    """State, audit journal, and outbox committed in one SQLite transaction."""
   185	
   186	    def __init__(self, path: Path) -> None:
   187	        self._path = path
   188	
   189	    def _connect(self) -> sqlite3.Connection:
   190	        connection = sqlite3.connect(
   191	            self._path,
   192	            isolation_level=None,
   193	            timeout=5.0,
   194	        )
   195	        connection.row_factory = sqlite3.Row
   196	        connection.execute("PRAGMA foreign_keys = ON")
   197	        connection.execute("PRAGMA synchronous = FULL")
   198	        return connection
   199	
   200	    def initialize(self) -> None:
   201	        self._path.parent.mkdir(parents=True, exist_ok=True)
   202	        migration = _MIGRATION.read_text(encoding="utf-8")
   203	        connection = self._connect()
   204	        try:
   205	            connection.executescript(migration)
   206	        finally:
   207	            connection.close()
   208	        self._path.chmod(0o600)
   209	
   210	    def load(self, execution_id: Identity) -> Execution | None:
   211	        self._require_run_id(execution_id)
   212	        with closing(self._connect()) as connection:
   213	            row = connection.execute(
   214	                """
   215	                SELECT execution_id, canonical_state_json, version, last_event_id
   216	                FROM execution_state
   217	                WHERE execution_id = ?
   218	                """,
   219	                (str(execution_id),),
   220	            ).fetchone()

exec
/bin/bash -lc "nl -ba src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '221,460p'" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
   221	        return None if row is None else self._decode_state_row(row)
   222	
   223	    def append(self, event: ExecutionEvent) -> Execution:
   224	        connection = self._connect()
   225	        connection.execute("BEGIN IMMEDIATE")
   226	        try:
   227	            current_row = connection.execute(
   228	                """
   229	                SELECT execution_id, canonical_state_json, version, last_event_id
   230	                FROM execution_state
   231	                WHERE execution_id = ?
   232	                """,
   233	                (str(event.execution_id),),
   234	            ).fetchone()
   235	            current = (
   236	                None if current_row is None else self._decode_state_row(current_row)
   237	            )
   238	            next_state = reduce_execution(current, event)
   239	            next_document = _execution_to_document(next_state)
   240	            next_json = canonical_json(next_document)
   241	
   242	            if current is None:
   243	                connection.execute(
   244	                    """
   245	                    INSERT INTO execution_state(
   246	                        execution_id,
   247	                        canonical_state_json,
   248	                        version,
   249	                        last_event_id,
   250	                        updated_at
   251	                    ) VALUES (?, ?, ?, ?, ?)
   252	                    """,
   253	                    (
   254	                        str(next_state.execution_id),
   255	                        next_json,
   256	                        next_state.version,
   257	                        str(next_state.last_event_id),
   258	                        next_state.updated_at,
   259	                    ),
   260	                )
   261	                previous_json = None
   262	                previous_version = 0
   263	            else:
   264	                assert current_row is not None
   265	                previous_json = str(current_row["canonical_state_json"])
   266	                previous_version = current.version
   267	                cursor = connection.execute(
   268	                    """
   269	                    UPDATE execution_state
   270	                    SET canonical_state_json = ?,
   271	                        version = ?,
   272	                        last_event_id = ?,
   273	                        updated_at = ?
   274	                    WHERE execution_id = ?
   275	                      AND version = ?
   276	                      AND canonical_state_json = ?
   277	                    """,
   278	                    (
   279	                        next_json,
   280	                        next_state.version,
   281	                        str(next_state.last_event_id),
   282	                        next_state.updated_at,
   283	                        str(next_state.execution_id),
   284	                        current.version,
   285	                        previous_json,
   286	                    ),
   287	                )
   288	                if cursor.rowcount != 1:
   289	                    raise ConcurrentExecutionWriteError(
   290	                        "canonical execution compare-and-swap failed"
   291	                    )
   292	
   293	            event_document = _event_to_document(event)
   294	            event_json = canonical_json(event_document)
   295	            resulting_digest = canonical_sha256(next_document)
   296	            previous_digest = (
   297	                None
   298	                if previous_json is None
   299	                else canonical_sha256(json.loads(previous_json))
   300	            )
   301	            connection.execute(
   302	                """
   303	                INSERT INTO execution_journal(
   304	                    event_id,
   305	                    execution_id,
   306	                    event_type,
   307	                    previous_version,
   308	                    resulting_version,
   309	                    event_json,
   310	                    previous_state_sha256,
   311	                    resulting_state_sha256,
   312	                    resulting_state_json,
   313	                    recorded_at
   314	                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   315	                """,
   316	                (
   317	                    str(event.event_id),
   318	                    str(event.execution_id),
   319	                    type(event).__name__,
   320	                    previous_version,
   321	                    next_state.version,
   322	                    event_json,
   323	                    previous_digest,
   324	                    resulting_digest,
   325	                    next_json,
   326	                    event.occurred_at,
   327	                ),
   328	            )
   329	
   330	            outbox_document = {
   331	                "schema_version": "execution-outbox/v1",
   332	                "event_id": str(event.event_id),
   333	                "event_type": type(event).__name__,
   334	                "execution_id": str(event.execution_id),
   335	                "aggregate_version": next_state.version,
   336	                "occurred_at": event.occurred_at,
   337	                "event": event_document,
   338	            }
   339	            connection.execute(
   340	                """
   341	                INSERT INTO execution_outbox(
   342	                    event_id,
   343	                    execution_id,
   344	                    aggregate_version,
   345	                    payload_json,
   346	                    created_at
   347	                ) VALUES (?, ?, ?, ?, ?)
   348	                """,
   349	                (
   350	                    str(event.event_id),
   351	                    str(event.execution_id),
   352	                    next_state.version,
   353	                    canonical_json(outbox_document),
   354	                    event.occurred_at,
   355	                ),
   356	            )
   357	            connection.execute("COMMIT")
   358	            return next_state
   359	        except BaseException:
   360	            if connection.in_transaction:
   361	                connection.execute("ROLLBACK")
   362	            raise
   363	        finally:
   364	            connection.close()
   365	
   366	    def count_journal_entries(self, execution_id: Identity) -> int:
   367	        return self._count_rows("execution_journal", execution_id)
   368	
   369	    def count_outbox_entries(self, execution_id: Identity) -> int:
   370	        return self._count_rows("execution_outbox", execution_id)
   371	
   372	    def _count_rows(self, table: str, execution_id: Identity) -> int:
   373	        self._require_run_id(execution_id)
   374	        if table not in {"execution_journal", "execution_outbox"}:
   375	            raise ValueError("unsupported execution table")
   376	        with closing(self._connect()) as connection:
   377	            row = connection.execute(
   378	                f"SELECT COUNT(*) AS count FROM {table} WHERE execution_id = ?",
   379	                (str(execution_id),),
   380	            ).fetchone()
   381	        assert row is not None
   382	        return int(row["count"])
   383	
   384	    @staticmethod
   385	    def _require_run_id(execution_id: Identity) -> None:
   386	        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
   387	            raise ValueError("execution_id must be a canonical run identity")
   388	
   389	    @staticmethod
   390	    def _decode_state_row(row: sqlite3.Row) -> Execution:
   391	        raw = str(row["canonical_state_json"])
   392	        try:
   393	            document = json.loads(raw)
   394	        except json.JSONDecodeError as exc:
   395	            raise ExecutionPersistenceIntegrityError(
   396	                "canonical execution state is not JSON"
   397	            ) from exc
   398	        if not isinstance(document, dict) or canonical_json(document) != raw:
   399	            raise ExecutionPersistenceIntegrityError(
   400	                "execution state is not canonically serialized"
   401	            )
   402	        try:
   403	            state = _execution_from_document(document)
   404	        except (TypeError, ValueError) as exc:
   405	            raise ExecutionPersistenceIntegrityError(
   406	                "canonical execution state is invalid"
   407	            ) from exc
   408	        if int(row["version"]) != state.version:
   409	            raise ExecutionPersistenceIntegrityError(
   410	                "relational version disagrees with canonical state version"
   411	            )
   412	        if str(row["last_event_id"]) != str(state.last_event_id):
   413	            raise ExecutionPersistenceIntegrityError(
   414	                "relational last event disagrees with canonical state"
   415	            )
   416	        if str(row["execution_id"]) != str(state.execution_id):
   417	            raise ExecutionPersistenceIntegrityError(
   418	                "relational identity disagrees with canonical state identity"
   419	            )
   420	        return state

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	BEGIN IMMEDIATE;
     2	
     3	CREATE TABLE IF NOT EXISTS execution_state (
     4	    execution_id TEXT PRIMARY KEY,
     5	    canonical_state_json TEXT NOT NULL,
     6	    version INTEGER NOT NULL CHECK (version >= 1),
     7	    last_event_id TEXT NOT NULL UNIQUE,
     8	    updated_at TEXT NOT NULL
     9	);
    10	
    11	CREATE TABLE IF NOT EXISTS execution_journal (
    12	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    13	    event_id TEXT NOT NULL UNIQUE,
    14	    execution_id TEXT NOT NULL,
    15	    event_type TEXT NOT NULL,
    16	    previous_version INTEGER NOT NULL CHECK (previous_version >= 0),
    17	    resulting_version INTEGER NOT NULL,
    18	    event_json TEXT NOT NULL,
    19	    previous_state_sha256 TEXT,
    20	    resulting_state_sha256 TEXT NOT NULL,
    21	    resulting_state_json TEXT NOT NULL,
    22	    recorded_at TEXT NOT NULL,
    23	    FOREIGN KEY (execution_id)
    24	        REFERENCES execution_state(execution_id),
    25	    UNIQUE (execution_id, resulting_version),
    26	    CHECK (resulting_version = previous_version + 1),
    27	    CHECK (
    28	        (previous_version = 0 AND previous_state_sha256 IS NULL)
    29	        OR
    30	        (previous_version > 0 AND length(previous_state_sha256) = 64)
    31	    ),
    32	    CHECK (length(resulting_state_sha256) = 64)
    33	);
    34	
    35	CREATE TABLE IF NOT EXISTS execution_outbox (
    36	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    37	    event_id TEXT NOT NULL UNIQUE,
    38	    execution_id TEXT NOT NULL,
    39	    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 1),
    40	    payload_json TEXT NOT NULL,
    41	    created_at TEXT NOT NULL,
    42	    FOREIGN KEY (event_id)
    43	        REFERENCES execution_journal(event_id),
    44	    UNIQUE (execution_id, aggregate_version)
    45	);
    46	
    47	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
    48	BEFORE UPDATE ON execution_journal
    49	BEGIN
    50	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    51	END;
    52	
    53	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
    54	BEFORE DELETE ON execution_journal
    55	BEGIN
    56	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    57	END;
    58	
    59	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
    60	BEFORE UPDATE ON execution_outbox
    61	BEGIN
    62	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    63	END;
    64	
    65	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
    66	BEFORE DELETE ON execution_outbox
    67	BEGIN
    68	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    69	END;
    70	
    71	PRAGMA user_version = 1;
    72	
    73	COMMIT;

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/domain/application_control.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from dataclasses import dataclass
     4	
     5	from ranex.foundation.identity import Identity
     6	
     7	
     8	def _require_identity(value: Identity, prefix: str, field: str) -> None:
     9	    if not isinstance(value, Identity) or value.prefix != prefix:
    10	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    11	
    12	
    13	@dataclass(frozen=True, slots=True)
    14	class ApplicationControlRequest:
    15	    request_id: Identity
    16	    project_id: Identity
    17	    execution_id: Identity
    18	    action: str
    19	    expected_version: int
    20	    requested_by: Identity
    21	    subject_actor_ids: tuple[Identity, ...] = ()
    22	
    23	    def __post_init__(self) -> None:
    24	        _require_identity(self.request_id, "transition", "request_id")
    25	        _require_identity(self.project_id, "prj", "project_id")
    26	        _require_identity(self.execution_id, "run", "execution_id")
    27	        _require_identity(self.requested_by, "principal", "requested_by")
    28	        if not isinstance(self.action, str) or not self.action.strip():
    29	            raise ValueError("action must be a non-empty string")
    30	        if (
    31	            isinstance(self.expected_version, bool)
    32	            or not isinstance(self.expected_version, int)
    33	            or self.expected_version < 0
    34	        ):
    35	            raise ValueError("expected_version must be a non-negative integer")
    36	        canonical_actor_ids = tuple(sorted(set(self.subject_actor_ids), key=str))
    37	        if self.subject_actor_ids != canonical_actor_ids:
    38	            raise ValueError("subject_actor_ids must be unique and sorted")
    39	        for actor_id in self.subject_actor_ids:
    40	            _require_identity(actor_id, "principal", "subject_actor_ids")
    41	
    42	
    43	@dataclass(frozen=True, slots=True)
    44	class ApplicationControlFacts:
    45	    decision_well_formed: bool
    46	    request_bound: bool
    47	    gate_passed: bool
    48	    gate_authorized: bool
    49	    reason_codes: tuple[str, ...]
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class ApplicationControlDecision:
    54	    permitted: bool
    55	    reason_codes: tuple[str, ...]
    56	
    57	
    58	def deny_application_control(*reason_codes: str) -> ApplicationControlDecision:
    59	    reasons = tuple(sorted(set(reason_codes)))
    60	    if not reasons or any(not reason for reason in reasons):
    61	        raise ValueError("denial requires non-empty reason codes")
    62	    return ApplicationControlDecision(permitted=False, reason_codes=reasons)
    63	
    64	
    65	def decide_application_control(
    66	    facts: ApplicationControlFacts,
    67	) -> ApplicationControlDecision:
    68	    """Pure fail-closed application-control decision."""
    69	    if not facts.decision_well_formed:
    70	        return deny_application_control("MALFORMED_POLICY_DECISION")
    71	    if not facts.request_bound:
    72	        return deny_application_control("POLICY_DECISION_SUBJECT_MISMATCH")
    73	    if not facts.gate_passed or not facts.gate_authorized:
    74	        return deny_application_control(*(facts.reason_codes or ("POLICY_DENIED",)))
    75	    if facts.reason_codes:
    76	        return deny_application_control("PASS_DECISION_CONTAINS_REASONS")
    77	    return ApplicationControlDecision(permitted=True, reason_codes=())

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/domain/execution.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	from dataclasses import dataclass, replace
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.events import (
     8	    ExecutionBlocked,
     9	    ExecutionCancelled,
    10	    ExecutionCreated,
    11	    ExecutionEvent,
    12	    ExecutionFailed,
    13	    ExecutionMarkedReady,
    14	    ExecutionResumed,
    15	    ExecutionStarted,
    16	    ExecutionSucceeded,
    17	    ExecutionUnblocked,
    18	    ExecutionWaited,
    19	)
    20	from ranex.governed_execution.domain.status import ExecutionStatus
    21	
    22	
    23	class InvalidExecutionTransition(ValueError):
    24	    """An event cannot evolve the supplied execution state."""
    25	
    26	
    27	LEGAL_STATUS_TRANSITIONS = frozenset(
    28	    {
    29	        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
    30	        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
    31	        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
    32	        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
    33	        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
    34	        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
    35	        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
    36	        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
    37	        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
    38	        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    39	        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
    40	        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
    41	        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
    42	        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
    43	        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
    44	        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
    45	        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
    46	        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
    47	        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    48	    }
    49	)
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class Execution:
    54	    execution_id: Identity
    55	    work_item_id: Identity
    56	    created_by_principal_id: Identity
    57	    workflow_request_ref: str
    58	    status: ExecutionStatus
    59	    version: int
    60	    last_event_id: Identity
    61	    updated_at: str
    62	    blocked_from_status: ExecutionStatus | None = None
    63	
    64	
    65	def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    66	    return InvalidExecutionTransition(
    67	        f"{state.status.value} cannot apply {type(event).__name__}"
    68	    )
    69	
    70	
    71	def _advance(
    72	    state: Execution,
    73	    event: ExecutionEvent,
    74	    target_status: ExecutionStatus,
    75	    *,
    76	    blocked_from_status: ExecutionStatus | None = None,
    77	) -> Execution:
    78	    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
    79	        raise _invalid(state, event)
    80	    return replace(
    81	        state,
    82	        status=target_status,
    83	        version=state.version + 1,
    84	        last_event_id=event.event_id,
    85	        updated_at=event.occurred_at,
    86	        blocked_from_status=blocked_from_status,
    87	    )
    88	
    89	
    90	def _require_source(
    91	    state: Execution,
    92	    event: ExecutionEvent,
    93	    allowed: frozenset[ExecutionStatus],
    94	) -> None:
    95	    if state.status not in allowed:
    96	        raise _invalid(state, event)
    97	
    98	
    99	def reduce_execution(
   100	    current: Execution | None,
   101	    event: ExecutionEvent,
   102	) -> Execution:
   103	    """Purely compute the next immutable Execution from one event."""
   104	    if current is None:
   105	        if not isinstance(event, ExecutionCreated):
   106	            raise InvalidExecutionTransition(
   107	                f"no execution can apply {type(event).__name__}"
   108	            )
   109	        if event.expected_version != 0:
   110	            raise InvalidExecutionTransition(
   111	                "ExecutionCreated expected version must be zero"
   112	            )
   113	        return Execution(
   114	            execution_id=event.execution_id,
   115	            work_item_id=event.work_item_id,
   116	            created_by_principal_id=event.created_by_principal_id,
   117	            workflow_request_ref=event.workflow_request_ref,
   118	            status=ExecutionStatus.PROPOSED,
   119	            version=1,
   120	            last_event_id=event.event_id,
   121	            updated_at=event.occurred_at,
   122	        )
   123	
   124	    if isinstance(event, ExecutionCreated):
   125	        raise _invalid(current, event)
   126	    if event.execution_id != current.execution_id:
   127	        raise InvalidExecutionTransition("event targets a different execution")
   128	    if event.expected_version != current.version:
   129	        raise InvalidExecutionTransition(
   130	            "event expected version does not match execution version"
   131	        )
   132	    if event.event_id == current.last_event_id:
   133	        raise InvalidExecutionTransition("last event cannot be applied twice")
   134	
   135	    if isinstance(event, ExecutionMarkedReady):
   136	        _require_source(
   137	            current,
   138	            event,
   139	            frozenset({ExecutionStatus.PROPOSED}),
   140	        )
   141	        return _advance(current, event, ExecutionStatus.READY)
   142	    if isinstance(event, ExecutionStarted):
   143	        _require_source(
   144	            current,
   145	            event,
   146	            frozenset({ExecutionStatus.READY}),
   147	        )
   148	        return _advance(current, event, ExecutionStatus.RUNNING)
   149	    if isinstance(event, ExecutionWaited):
   150	        _require_source(
   151	            current,
   152	            event,
   153	            frozenset({ExecutionStatus.RUNNING}),
   154	        )
   155	        return _advance(current, event, ExecutionStatus.WAITING)
   156	    if isinstance(event, ExecutionResumed):
   157	        _require_source(
   158	            current,
   159	            event,
   160	            frozenset({ExecutionStatus.WAITING}),
   161	        )
   162	        return _advance(current, event, ExecutionStatus.RUNNING)
   163	    if isinstance(event, ExecutionBlocked):
   164	        _require_source(
   165	            current,
   166	            event,
   167	            frozenset(
   168	                {
   169	                    ExecutionStatus.READY,
   170	                    ExecutionStatus.RUNNING,
   171	                    ExecutionStatus.WAITING,
   172	                }
   173	            ),
   174	        )
   175	        return _advance(
   176	            current,
   177	            event,
   178	            ExecutionStatus.BLOCKED,
   179	            blocked_from_status=current.status,
   180	        )
   181	    if isinstance(event, ExecutionUnblocked):
   182	        if (
   183	            current.status is not ExecutionStatus.BLOCKED
   184	            or current.blocked_from_status is not event.target_status
   185	        ):
   186	            raise _invalid(current, event)
   187	        return _advance(current, event, event.target_status)
   188	    if isinstance(event, ExecutionSucceeded):
   189	        _require_source(
   190	            current,
   191	            event,
   192	            frozenset({ExecutionStatus.RUNNING}),
   193	        )
   194	        return _advance(current, event, ExecutionStatus.SUCCEEDED)
   195	    if isinstance(event, ExecutionFailed):
   196	        _require_source(
   197	            current,
   198	            event,
   199	            frozenset(
   200	                {
   201	                    ExecutionStatus.RUNNING,
   202	                    ExecutionStatus.WAITING,
   203	                    ExecutionStatus.BLOCKED,
   204	                }
   205	            ),
   206	        )
   207	        return _advance(current, event, ExecutionStatus.FAILED)
   208	    if isinstance(event, ExecutionCancelled):
   209	        _require_source(
   210	            current,
   211	            event,
   212	            frozenset(
   213	                {
   214	                    ExecutionStatus.PROPOSED,
   215	                    ExecutionStatus.READY,
   216	                    ExecutionStatus.RUNNING,
   217	                    ExecutionStatus.WAITING,
   218	                    ExecutionStatus.BLOCKED,
   219	                }
   220	            ),
   221	        )
   222	        return _advance(current, event, ExecutionStatus.CANCELLED)
   223	    raise TypeError(f"unsupported execution event: {type(event).__name__}")
   224	
   225	
   226	def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
   227	    """Replay an ordered history through the same production reducer."""
   228	    state: Execution | None = None
   229	    seen_event_ids: set[Identity] = set()
   230	    for event in events:
   231	        if event.event_id in seen_event_ids:
   232	            raise InvalidExecutionTransition("event identity is duplicated in history")
   233	        seen_event_ids.add(event.event_id)
   234	        state = reduce_execution(state, event)
   235	    if state is None:
   236	        raise InvalidExecutionTransition("execution history must not be empty")
   237	    return state

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/domain/events.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from dataclasses import dataclass
     4	from datetime import UTC, datetime
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.status import ExecutionStatus
     8	
     9	
    10	def _require_text(value: str, *, field: str) -> None:
    11	    if not isinstance(value, str) or not value.strip():
    12	        raise ValueError(f"{field} must be a non-empty string")
    13	
    14	
    15	def _require_identity(value: Identity, *, prefix: str, field: str) -> None:
    16	    if not isinstance(value, Identity) or value.prefix != prefix:
    17	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    18	
    19	
    20	def _require_utc_timestamp(value: str) -> None:
    21	    _require_text(value, field="occurred_at")
    22	    if not value.endswith("Z"):
    23	        raise ValueError("occurred_at must use canonical UTC Z notation")
    24	    try:
    25	        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    26	    except ValueError as exc:
    27	        raise ValueError("occurred_at must be a valid UTC timestamp") from exc
    28	    if parsed.tzinfo != UTC:
    29	        raise ValueError("occurred_at must be UTC")
    30	
    31	
    32	@dataclass(frozen=True, slots=True, kw_only=True)
    33	class ExecutionEventMetadata:
    34	    event_id: Identity
    35	    execution_id: Identity
    36	    expected_version: int
    37	    occurred_at: str
    38	
    39	    def __post_init__(self) -> None:
    40	        _require_identity(
    41	            self.event_id,
    42	            prefix="transition",
    43	            field="event_id",
    44	        )
    45	        _require_identity(
    46	            self.execution_id,
    47	            prefix="run",
    48	            field="execution_id",
    49	        )
    50	        if (
    51	            isinstance(self.expected_version, bool)
    52	            or not isinstance(self.expected_version, int)
    53	            or self.expected_version < 0
    54	        ):
    55	            raise ValueError("expected_version must be a non-negative integer")
    56	        _require_utc_timestamp(self.occurred_at)
    57	
    58	
    59	@dataclass(frozen=True, slots=True, kw_only=True)
    60	class ExecutionCreated(ExecutionEventMetadata):
    61	    work_item_id: Identity
    62	    created_by_principal_id: Identity
    63	    workflow_request_ref: str
    64	
    65	    def __post_init__(self) -> None:
    66	        super().__post_init__()
    67	        _require_identity(
    68	            self.work_item_id,
    69	            prefix="work",
    70	            field="work_item_id",
    71	        )
    72	        _require_identity(
    73	            self.created_by_principal_id,
    74	            prefix="principal",
    75	            field="created_by_principal_id",
    76	        )
    77	        _require_text(self.workflow_request_ref, field="workflow_request_ref")
    78	
    79	
    80	@dataclass(frozen=True, slots=True, kw_only=True)
    81	class ExecutionMarkedReady(ExecutionEventMetadata):
    82	    readiness_snapshot_ref: str
    83	
    84	    def __post_init__(self) -> None:
    85	        super().__post_init__()
    86	        _require_text(
    87	            self.readiness_snapshot_ref,
    88	            field="readiness_snapshot_ref",
    89	        )
    90	
    91	
    92	@dataclass(frozen=True, slots=True, kw_only=True)
    93	class ExecutionStarted(ExecutionEventMetadata):
    94	    authorization_ref: str
    95	
    96	    def __post_init__(self) -> None:
    97	        super().__post_init__()
    98	        _require_text(self.authorization_ref, field="authorization_ref")
    99	
   100	
   101	@dataclass(frozen=True, slots=True, kw_only=True)
   102	class ExecutionWaited(ExecutionEventMetadata):
   103	    wait_reason_code: str
   104	
   105	    def __post_init__(self) -> None:
   106	        super().__post_init__()
   107	        _require_text(self.wait_reason_code, field="wait_reason_code")
   108	
   109	
   110	@dataclass(frozen=True, slots=True, kw_only=True)
   111	class ExecutionResumed(ExecutionEventMetadata):
   112	    signal_ref: str
   113	
   114	    def __post_init__(self) -> None:
   115	        super().__post_init__()
   116	        _require_text(self.signal_ref, field="signal_ref")
   117	
   118	
   119	@dataclass(frozen=True, slots=True, kw_only=True)
   120	class ExecutionBlocked(ExecutionEventMetadata):
   121	    block_reason_code: str
   122	    blocking_refs: tuple[str, ...]
   123	
   124	    def __post_init__(self) -> None:
   125	        super().__post_init__()
   126	        _require_text(self.block_reason_code, field="block_reason_code")
   127	        if not self.blocking_refs:
   128	            raise ValueError("blocking_refs must not be empty")
   129	        if any(not reference.strip() for reference in self.blocking_refs):
   130	            raise ValueError("blocking_refs must contain non-empty references")
   131	        if self.blocking_refs != tuple(sorted(set(self.blocking_refs))):
   132	            raise ValueError("blocking_refs must be unique and canonically sorted")
   133	
   134	
   135	@dataclass(frozen=True, slots=True, kw_only=True)
   136	class ExecutionUnblocked(ExecutionEventMetadata):
   137	    target_status: ExecutionStatus
   138	    refreshed_evidence_ref: str
   139	
   140	    def __post_init__(self) -> None:
   141	        super().__post_init__()
   142	        if self.target_status not in {
   143	            ExecutionStatus.READY,
   144	            ExecutionStatus.RUNNING,
   145	            ExecutionStatus.WAITING,
   146	        }:
   147	            raise ValueError("unblock target must be READY, RUNNING, or WAITING")
   148	        _require_text(
   149	            self.refreshed_evidence_ref,
   150	            field="refreshed_evidence_ref",
   151	        )
   152	
   153	
   154	@dataclass(frozen=True, slots=True, kw_only=True)
   155	class ExecutionSucceeded(ExecutionEventMetadata):
   156	    outcome_ref: str
   157	
   158	    def __post_init__(self) -> None:
   159	        super().__post_init__()
   160	        _require_text(self.outcome_ref, field="outcome_ref")
   161	
   162	
   163	@dataclass(frozen=True, slots=True, kw_only=True)
   164	class ExecutionFailed(ExecutionEventMetadata):
   165	    failure_reason_code: str
   166	    evidence_ref: str
   167	
   168	    def __post_init__(self) -> None:
   169	        super().__post_init__()
   170	        _require_text(
   171	            self.failure_reason_code,
   172	            field="failure_reason_code",
   173	        )
   174	        _require_text(self.evidence_ref, field="evidence_ref")
   175	
   176	
   177	@dataclass(frozen=True, slots=True, kw_only=True)
   178	class ExecutionCancelled(ExecutionEventMetadata):
   179	    decision_ref: str
   180	
   181	    def __post_init__(self) -> None:
   182	        super().__post_init__()
   183	        _require_text(self.decision_ref, field="decision_ref")
   184	
   185	
   186	ExecutionEvent = (
   187	    ExecutionCreated
   188	    | ExecutionMarkedReady
   189	    | ExecutionStarted
   190	    | ExecutionWaited
   191	    | ExecutionResumed
   192	    | ExecutionBlocked
   193	    | ExecutionUnblocked
   194	    | ExecutionSucceeded
   195	    | ExecutionFailed
   196	    | ExecutionCancelled
   197	)

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/domain/status.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from enum import StrEnum
     4	
     5	
     6	class ExecutionStatus(StrEnum):
     7	    PROPOSED = "PROPOSED"
     8	    READY = "READY"
     9	    RUNNING = "RUNNING"
    10	    WAITING = "WAITING"
    11	    BLOCKED = "BLOCKED"
    12	    SUCCEEDED = "SUCCEEDED"
    13	    FAILED = "FAILED"
    14	    CANCELLED = "CANCELLED"
    15	
    16	
    17	TERMINAL_EXECUTION_STATUSES = frozenset(
    18	    {
    19	        ExecutionStatus.SUCCEEDED,
    20	        ExecutionStatus.FAILED,
    21	        ExecutionStatus.CANCELLED,
    22	    }
    23	)

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/application/application_control_pep.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	
     5	from ranex.assurance.api.contracts import (
     6	    EvidenceRecord,
     7	    GateEvaluation,
     8	    GateOutcome,
     9	)
    10	from ranex.governed_execution.application.ports.application_control_policy import (
    11	    ApplicationControlPolicy,
    12	)
    13	from ranex.governed_execution.domain.application_control import (
    14	    ApplicationControlDecision,
    15	    ApplicationControlFacts,
    16	    ApplicationControlRequest,
    17	    decide_application_control,
    18	    deny_application_control,
    19	)
    20	
    21	
    22	class ApplicationControlPEP:
    23	    """Fail-closed policy-enforcement point with no dispatch capability."""
    24	
    25	    def __init__(self, policy: ApplicationControlPolicy) -> None:
    26	        self._policy = policy
    27	
    28	    def decide(
    29	        self,
    30	        *,
    31	        request: ApplicationControlRequest,
    32	        evidence: Iterable[EvidenceRecord],
    33	    ) -> ApplicationControlDecision:
    34	        try:
    35	            evaluation = self._policy.evaluate(
    36	                request=request,
    37	                evidence=tuple(evidence),
    38	            )
    39	        except Exception:
    40	            return deny_application_control("POLICY_ADAPTER_EXCEPTION")
    41	
    42	        if not isinstance(evaluation, GateEvaluation):
    43	            return deny_application_control("MALFORMED_POLICY_DECISION")
    44	
    45	        return decide_application_control(
    46	            ApplicationControlFacts(
    47	                decision_well_formed=True,
    48	                request_bound=evaluation.request_id == request.request_id,
    49	                gate_passed=evaluation.outcome is GateOutcome.PASS,
    50	                gate_authorized=evaluation.authorized,
    51	                reason_codes=evaluation.reason_codes,
    52	            )
    53	        )

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/application/ports/execution_repository.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from typing import Protocol
     4	
     5	from ranex.foundation.identity import Identity
     6	from ranex.governed_execution.domain.events import ExecutionEvent
     7	from ranex.governed_execution.domain.execution import Execution
     8	
     9	
    10	class ExecutionRepository(Protocol):
    11	    def load(self, execution_id: Identity) -> Execution | None:
    12	        """Load the current canonical execution snapshot."""
    13	        ...
    14	
    15	    def append(self, event: ExecutionEvent) -> Execution:
    16	        """Reduce and atomically persist one execution transition."""
    17	        ...

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/application/gate_controller.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	
     5	from ranex.assurance.api.contracts import (
     6	    EvidenceRecord,
     7	    GateEvaluation,
     8	    GateOutcome,
     9	)
    10	from ranex.foundation.canonical import canonical_json, canonical_sha256
    11	from ranex.governed_execution.domain.application_control import (
    12	    ApplicationControlRequest,
    13	)
    14	from ranex.policy.api.contracts import (
    15	    GateDefinition,
    16	    RuleEnforcementClass,
    17	    RuleResolution,
    18	)
    19	
    20	
    21	def _digest(value: object) -> str:
    22	    return f"sha256:{canonical_sha256(value)}"
    23	
    24	
    25	def _gate_document(gate: GateDefinition) -> dict[str, object]:
    26	    return {
    27	        "gate_id": str(gate.gate_id),
    28	        "action": gate.action,
    29	        "rules": [
    30	            {
    31	                "rule_id": rule.rule_id,
    32	                "enforcement": rule.enforcement.value,
    33	                "resolution": rule.resolution.value,
    34	                "required_claim_ids": list(rule.required_claim_ids),
    35	                "independent_producer_required": (rule.independent_producer_required),
    36	            }
    37	            for rule in gate.rules
    38	        ],
    39	    }
    40	
    41	
    42	def _evidence_document(record: EvidenceRecord) -> dict[str, object]:
    43	    return {
    44	        "evidence_id": str(record.evidence_id),
    45	        "claim_id": record.claim_id,
    46	        "outcome": record.outcome.value,
    47	        "project_id": str(record.project_id),
    48	        "execution_id": str(record.execution_id),
    49	        "action": record.action,
    50	        "subject_version": record.subject_version,
    51	        "producer_id": str(record.producer_id),
    52	        "producer_role": record.producer_role,
    53	        "command": record.command,
    54	        "exit_code": record.exit_code,
    55	        "observed_at": record.observed_at,
    56	        "artifact_sha256": record.artifact_sha256,
    57	        "artifact_verified": record.artifact_verified,
    58	    }
    59	
    60	
    61	class GateController:
    62	    """Pure fail-closed evaluator; it is not an Execution reducer."""
    63	
    64	    def evaluate(
    65	        self,
    66	        *,
    67	        gate: GateDefinition,
    68	        request: ApplicationControlRequest,
    69	        evidence: Iterable[EvidenceRecord],
    70	        catalog_id: str,
    71	        catalog_digest: str,
    72	    ) -> GateEvaluation:
    73	        records = tuple(evidence)
    74	        policy_digest = _digest(_gate_document(gate))
    75	        documents = [_evidence_document(record) for record in records]
    76	        documents.sort(key=canonical_json)
    77	        evidence_digest = _digest(documents)
    78	
    79	        def result(
    80	            outcome: GateOutcome,
    81	            *,
    82	            authorized: bool = False,
    83	            missing: tuple[str, ...] = (),
    84	            reasons: tuple[str, ...],
    85	        ) -> GateEvaluation:
    86	            return GateEvaluation(
    87	                gate_id=gate.gate_id,
    88	                request_id=request.request_id,
    89	                outcome=outcome,
    90	                authorized=authorized,
    91	                missing_claim_ids=tuple(sorted(set(missing))),
    92	                reason_codes=tuple(sorted(set(reasons))),
    93	                catalog_id=catalog_id,
    94	                catalog_digest=catalog_digest,
    95	                policy_digest=policy_digest,
    96	                evidence_digest=evidence_digest,
    97	            )
    98	
    99	        if request.action != gate.action:
   100	            return result(
   101	                GateOutcome.FAIL,
   102	                reasons=("ACTION_DOES_NOT_MATCH_GATE",),
   103	            )
   104	
   105	        authority_rules = tuple(
   106	            rule
   107	            for rule in gate.rules
   108	            if rule.enforcement
   109	            in {
   110	                RuleEnforcementClass.REQUIRED,
   111	                RuleEnforcementClass.BLOCKING,
   112	            }
   113	        )
   114	        if not authority_rules:
   115	            return result(
   116	                GateOutcome.UNKNOWN,
   117	                reasons=("NO_AUTHORITY_RULES",),
   118	            )
   119	        if any(
   120	            rule.resolution is RuleResolution.HUMAN_DECISION_REQUIRED
   121	            for rule in authority_rules
   122	        ):
   123	            return result(
   124	                GateOutcome.UNKNOWN,
   125	                reasons=("HUMAN_DECISION_NOT_VERIFIED",),
   126	            )
   127	
   128	        actor_ids = {request.requested_by, *request.subject_actor_ids}
   129	        conflicts: list[str] = []
   130	        checker_faults: list[str] = []
   131	        unverified: list[str] = []
   132	        independence_violations: list[str] = []
   133	        failed: list[str] = []
   134	        missing: list[str] = []
   135	        wrong_subject: list[str] = []
   136	
   137	        for rule in authority_rules:
   138	            for claim_id in rule.required_claim_ids:
   139	                claim_records = tuple(
   140	                    record for record in records if record.claim_id == claim_id
   141	                )
   142	                candidates = tuple(
   143	                    record
   144	                    for record in claim_records
   145	                    if record.project_id == request.project_id
   146	                    and record.execution_id == request.execution_id
   147	                    and record.action == request.action
   148	                    and record.subject_version == request.expected_version
   149	                )
   150	                if claim_records and not candidates:
   151	                    wrong_subject.append(claim_id)
   152	                    missing.append(claim_id)
   153	                    continue
   154	
   155	                outcomes = {record.outcome for record in candidates}
   156	                if GateOutcome.CHECKER_FAULT in outcomes:
   157	                    checker_faults.append(claim_id)
   158	                    continue
   159	                if GateOutcome.CONFLICT in outcomes or (
   160	                    GateOutcome.PASS in outcomes and GateOutcome.FAIL in outcomes
   161	                ):
   162	                    conflicts.append(claim_id)
   163	                    continue
   164	                passing = tuple(
   165	                    record
   166	                    for record in candidates
   167	                    if record.outcome is GateOutcome.PASS and record.exit_code == 0
   168	                )
   169	                if passing and not any(record.artifact_verified for record in passing):
   170	                    unverified.append(claim_id)
   171	                    continue
   172	                if rule.independent_producer_required and any(
   173	                    record.producer_id in actor_ids for record in passing
   174	                ):
   175	                    independence_violations.append(claim_id)
   176	                    continue
   177	                if any(
   178	                    record.outcome is GateOutcome.FAIL or record.exit_code != 0
   179	                    for record in candidates
   180	                ):
   181	                    failed.append(claim_id)
   182	                    continue
   183	                if not passing:
   184	                    missing.append(claim_id)
   185	
   186	        if checker_faults:
   187	            return result(
   188	                GateOutcome.CHECKER_FAULT,
   189	                reasons=("CHECKER_FAULT",),
   190	            )
   191	        if conflicts:
   192	            return result(
   193	                GateOutcome.CONFLICT,
   194	                reasons=("CONFLICTING_EXACT_SUBJECT_EVIDENCE",),
   195	            )
   196	        if unverified:
   197	            return result(
   198	                GateOutcome.UNKNOWN,
   199	                missing=tuple(unverified),
   200	                reasons=("UNVERIFIED_EVIDENCE_ARTIFACT",),
   201	            )
   202	        if independence_violations:
   203	            return result(
   204	                GateOutcome.FAIL,
   205	                reasons=("INDEPENDENCE_VIOLATION",),
   206	            )
   207	        if failed:
   208	            return result(
   209	                GateOutcome.FAIL,
   210	                reasons=("BLOCKING_EVIDENCE_FAILED",),
   211	            )
   212	        if missing:
   213	            return result(
   214	                GateOutcome.UNKNOWN,
   215	                missing=tuple(missing),
   216	                reasons=(
   217	                    ("WRONG_SUBJECT_EVIDENCE",)
   218	                    if wrong_subject
   219	                    else ("MISSING_BLOCKING_EVIDENCE",)
   220	                ),
   221	            )
   222	        return result(GateOutcome.PASS, authorized=True, reasons=())

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/adapters/policy/deterministic.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import re
     4	
     5	from ranex.assurance.api.contracts import EvidenceRecord, GateEvaluation
     6	from ranex.governed_execution.application.gate_controller import GateController
     7	from ranex.governed_execution.application.ports.application_control_policy import (
     8	    ApplicationControlPolicy,
     9	)
    10	from ranex.governed_execution.domain.application_control import (
    11	    ApplicationControlRequest,
    12	)
    13	from ranex.policy.api.contracts import GateCatalog
    14	
    15	_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
    16	
    17	
    18	class DeterministicPolicyAdapter(ApplicationControlPolicy):
    19	    """Evaluate one immutable in-memory R&D catalog without external effects."""
    20	
    21	    def __init__(
    22	        self,
    23	        *,
    24	        catalog: GateCatalog,
    25	        catalog_digest: str,
    26	    ) -> None:
    27	        if _SHA256_PATTERN.fullmatch(catalog_digest) is None:
    28	            raise ValueError("catalog_digest must be canonical SHA-256")
    29	        self._catalog = catalog
    30	        self._catalog_digest = catalog_digest
    31	        self._controller = GateController()
    32	
    33	    def evaluate(
    34	        self,
    35	        *,
    36	        request: ApplicationControlRequest,
    37	        evidence: tuple[EvidenceRecord, ...],
    38	    ) -> GateEvaluation:
    39	        self._catalog.require_project(request.project_id)
    40	        gate = self._catalog.gate_for(request.action)
    41	        return self._controller.evaluate(
    42	            gate=gate,
    43	            request=request,
    44	            evidence=evidence,
    45	            catalog_id=self._catalog.catalog_id,
    46	            catalog_digest=self._catalog_digest,
    47	        )

exec
/bin/bash -lc 'nl -ba src/ranex/governed_execution/application/ports/application_control_policy.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from typing import Protocol
     4	
     5	from ranex.assurance.api.contracts import EvidenceRecord, GateEvaluation
     6	from ranex.governed_execution.domain.application_control import (
     7	    ApplicationControlRequest,
     8	)
     9	
    10	
    11	class ApplicationControlPolicy(Protocol):
    12	    def evaluate(
    13	        self,
    14	        *,
    15	        request: ApplicationControlRequest,
    16	        evidence: tuple[EvidenceRecord, ...],
    17	    ) -> GateEvaluation:
    18	        """Return a deterministic, exact-subject gate evaluation."""
    19	        ...

exec
/bin/bash -lc 'nl -ba src/ranex/assurance/api/contracts.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from ranex.assurance.domain.gates import (
     2	    EvidenceRecord,
     3	    GateEvaluation,
     4	    GateOutcome,
     5	)
     6	
     7	__all__ = ["EvidenceRecord", "GateEvaluation", "GateOutcome"]

exec
/bin/bash -lc 'nl -ba src/ranex/assurance/domain/gates.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import re
     4	from dataclasses import dataclass
     5	from enum import StrEnum
     6	
     7	from ranex.foundation.identity import Identity
     8	
     9	_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
    10	
    11	
    12	class GateOutcome(StrEnum):
    13	    PASS = "PASS"
    14	    FAIL = "FAIL"
    15	    UNKNOWN = "UNKNOWN"
    16	    CONFLICT = "CONFLICT"
    17	    NOT_APPLICABLE = "NOT_APPLICABLE"
    18	    CHECKER_FAULT = "CHECKER_FAULT"
    19	
    20	
    21	def _require_identity(value: Identity, prefix: str, field: str) -> None:
    22	    if not isinstance(value, Identity) or value.prefix != prefix:
    23	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    24	
    25	
    26	def _require_text(value: str, field: str) -> None:
    27	    if not isinstance(value, str) or not value.strip():
    28	        raise ValueError(f"{field} must be a non-empty string")
    29	
    30	
    31	def _require_digest(value: str, field: str) -> None:
    32	    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
    33	        raise ValueError(f"{field} must be canonical sha256 lowercase hex")
    34	
    35	
    36	@dataclass(frozen=True, slots=True)
    37	class EvidenceRecord:
    38	    evidence_id: Identity
    39	    claim_id: str
    40	    outcome: GateOutcome
    41	    project_id: Identity
    42	    execution_id: Identity
    43	    action: str
    44	    subject_version: int
    45	    producer_id: Identity
    46	    producer_role: str
    47	    command: str
    48	    exit_code: int
    49	    observed_at: str
    50	    artifact_sha256: str
    51	    artifact_verified: bool = False
    52	
    53	    def __post_init__(self) -> None:
    54	        _require_identity(self.evidence_id, "evd", "evidence_id")
    55	        _require_identity(self.project_id, "prj", "project_id")
    56	        _require_identity(self.execution_id, "run", "execution_id")
    57	        _require_identity(self.producer_id, "principal", "producer_id")
    58	        for field, value in (
    59	            ("claim_id", self.claim_id),
    60	            ("action", self.action),
    61	            ("producer_role", self.producer_role),
    62	            ("command", self.command),
    63	            ("observed_at", self.observed_at),
    64	        ):
    65	            _require_text(value, field)
    66	        if (
    67	            isinstance(self.subject_version, bool)
    68	            or not isinstance(self.subject_version, int)
    69	            or self.subject_version < 0
    70	        ):
    71	            raise ValueError("subject_version must be a non-negative integer")
    72	        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
    73	            raise ValueError("exit_code must be an integer")
    74	        _require_digest(self.artifact_sha256, "artifact_sha256")
    75	        if not isinstance(self.artifact_verified, bool):
    76	            raise ValueError("artifact_verified must be a boolean")
    77	
    78	
    79	@dataclass(frozen=True, slots=True)
    80	class GateEvaluation:
    81	    gate_id: Identity
    82	    request_id: Identity
    83	    outcome: GateOutcome
    84	    authorized: bool
    85	    missing_claim_ids: tuple[str, ...]
    86	    reason_codes: tuple[str, ...]
    87	    catalog_id: str
    88	    catalog_digest: str
    89	    policy_digest: str
    90	    evidence_digest: str
    91	
    92	    def __post_init__(self) -> None:
    93	        _require_identity(self.gate_id, "gate", "gate_id")
    94	        _require_identity(self.request_id, "transition", "request_id")
    95	        if not isinstance(self.authorized, bool):
    96	            raise ValueError("authorized must be a boolean")
    97	        if self.authorized != (self.outcome is GateOutcome.PASS):
    98	            raise ValueError("only PASS may be authorized and PASS must be authorized")
    99	        if self.outcome is GateOutcome.PASS and self.reason_codes:
   100	            raise ValueError("PASS evaluation must not contain reason codes")
   101	        if self.outcome is not GateOutcome.PASS and not self.reason_codes:
   102	            raise ValueError("non-PASS evaluation must contain a reason code")
   103	        for field, values in (
   104	            ("missing_claim_ids", self.missing_claim_ids),
   105	            ("reason_codes", self.reason_codes),
   106	        ):
   107	            if values != tuple(sorted(set(values))):
   108	                raise ValueError(f"{field} must be unique and sorted")
   109	            if any(not value for value in values):
   110	                raise ValueError(f"{field} must contain non-empty values")
   111	        _require_text(self.catalog_id, "catalog_id")
   112	        _require_digest(self.catalog_digest, "catalog_digest")
   113	        _require_digest(self.policy_digest, "policy_digest")
   114	        _require_digest(self.evidence_digest, "evidence_digest")

exec
/bin/bash -lc 'nl -ba src/ranex/foundation/canonical.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import hashlib
     4	import json
     5	from typing import Any
     6	
     7	
     8	def canonical_json(value: Any) -> str:
     9	    """Return stable compact JSON suitable for hashing kernel records."""
    10	    return json.dumps(
    11	        value,
    12	        allow_nan=False,
    13	        ensure_ascii=False,
    14	        separators=(",", ":"),
    15	        sort_keys=True,
    16	    )
    17	
    18	
    19	def canonical_json_bytes(value: Any) -> bytes:
    20	    """Return the UTF-8 bytes of the canonical JSON representation."""
    21	    return canonical_json(value).encode("utf-8")
    22	
    23	
    24	def canonical_sha256(value: Any) -> str:
    25	    """Return lowercase SHA-256 hex over the canonical JSON bytes."""
    26	    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()

exec
/bin/bash -lc 'nl -ba src/ranex/policy/api/contracts.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from ranex.policy.domain.gates import (
     2	    GateCatalog,
     3	    GateDefinition,
     4	    RuleDefinition,
     5	    RuleEnforcementClass,
     6	    RuleResolution,
     7	)
     8	
     9	__all__ = [
    10	    "GateCatalog",
    11	    "GateDefinition",
    12	    "RuleDefinition",
    13	    "RuleEnforcementClass",
    14	    "RuleResolution",
    15	]

exec
/bin/bash -lc 'nl -ba src/ranex/policy/domain/gates.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from dataclasses import dataclass
     4	from enum import StrEnum
     5	
     6	from ranex.foundation.identity import Identity
     7	
     8	
     9	class RuleEnforcementClass(StrEnum):
    10	    ADVISORY = "ADVISORY"
    11	    REQUIRED = "REQUIRED"
    12	    BLOCKING = "BLOCKING"
    13	    EXPERIMENTAL = "EXPERIMENTAL"
    14	
    15	
    16	class RuleResolution(StrEnum):
    17	    DETERMINISTIC = "DETERMINISTIC"
    18	    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"
    19	
    20	
    21	def _require_text(value: str, field: str) -> None:
    22	    if not isinstance(value, str) or not value.strip():
    23	        raise ValueError(f"{field} must be a non-empty string")
    24	
    25	
    26	@dataclass(frozen=True, slots=True)
    27	class RuleDefinition:
    28	    rule_id: str
    29	    enforcement: RuleEnforcementClass
    30	    resolution: RuleResolution
    31	    required_claim_ids: tuple[str, ...]
    32	    independent_producer_required: bool = False
    33	
    34	    def __post_init__(self) -> None:
    35	        _require_text(self.rule_id, "rule_id")
    36	        if not self.required_claim_ids:
    37	            raise ValueError("required_claim_ids must not be empty")
    38	        if self.required_claim_ids != tuple(sorted(set(self.required_claim_ids))):
    39	            raise ValueError("required_claim_ids must be unique and sorted")
    40	        if any(not claim_id for claim_id in self.required_claim_ids):
    41	            raise ValueError("required_claim_ids must contain non-empty values")
    42	        if not isinstance(self.independent_producer_required, bool):
    43	            raise ValueError("independent_producer_required must be a boolean")
    44	
    45	
    46	@dataclass(frozen=True, slots=True)
    47	class GateDefinition:
    48	    gate_id: Identity
    49	    action: str
    50	    rules: tuple[RuleDefinition, ...]
    51	
    52	    def __post_init__(self) -> None:
    53	        if not isinstance(self.gate_id, Identity) or self.gate_id.prefix != "gate":
    54	            raise ValueError("gate_id must be a canonical gate identity")
    55	        _require_text(self.action, "action")
    56	        if not self.rules:
    57	            raise ValueError("gate rules must not be empty")
    58	        rule_ids = tuple(rule.rule_id for rule in self.rules)
    59	        if len(rule_ids) != len(set(rule_ids)):
    60	            raise ValueError("gate rule IDs must be unique")
    61	        if not any(
    62	            rule.enforcement is RuleEnforcementClass.BLOCKING for rule in self.rules
    63	        ):
    64	            raise ValueError("gate must contain a BLOCKING rule")
    65	
    66	
    67	@dataclass(frozen=True, slots=True)
    68	class GateCatalog:
    69	    catalog_id: str
    70	    project_id: Identity
    71	    status: str
    72	    owner: str
    73	    gates: tuple[GateDefinition, ...]
    74	
    75	    def __post_init__(self) -> None:
    76	        _require_text(self.catalog_id, "catalog_id")
    77	        if not isinstance(self.project_id, Identity) or self.project_id.prefix != "prj":
    78	            raise ValueError("project_id must be a canonical project identity")
    79	        if self.status != "R_AND_D":
    80	            raise ValueError("tracer policy status must be R_AND_D")
    81	        _require_text(self.owner, "owner")
    82	        if not self.gates:
    83	            raise ValueError("gate catalog must not be empty")
    84	        gate_ids = tuple(gate.gate_id for gate in self.gates)
    85	        actions = tuple(gate.action for gate in self.gates)
    86	        if len(gate_ids) != len(set(gate_ids)):
    87	            raise ValueError("gate IDs must be unique")
    88	        if len(actions) != len(set(actions)):
    89	            raise ValueError("gate actions must be unique")
    90	
    91	    def require_project(self, project_id: Identity) -> None:
    92	        if project_id != self.project_id:
    93	            raise ValueError("policy project does not match control request")
    94	
    95	    def gate_for(self, action: str) -> GateDefinition:
    96	        matches = tuple(gate for gate in self.gates if gate.action == action)
    97	        if len(matches) != 1:
    98	            raise ValueError(
    99	                f"expected exactly one gate for {action!r}; found {len(matches)}"
   100	            )
   101	        return matches[0]

exec
/bin/bash -lc 'nl -ba src/ranex/foundation/identity.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import re
     4	import uuid
     5	from dataclasses import dataclass
     6	
     7	_PREFIX = r"[a-z][a-z0-9_]*"
     8	_UUID7 = (
     9	    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
    10	    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
    11	)
    12	_IDENTITY_PATTERN = re.compile(rf"^(?P<prefix>{_PREFIX})_(?P<uuid>{_UUID7})$")
    13	_PREFIX_PATTERN = re.compile(rf"^{_PREFIX}$")
    14	
    15	
    16	@dataclass(frozen=True, slots=True)
    17	class Identity:
    18	    """An opaque canonical Ranex prefix plus UUIDv7 identity."""
    19	
    20	    value: str
    21	    prefix: str
    22	    uuid: uuid.UUID
    23	
    24	    def __post_init__(self) -> None:
    25	        if not _PREFIX_PATTERN.fullmatch(self.prefix):
    26	            raise ValueError("identity prefix is not canonical")
    27	        if self.uuid.version != 7 or self.uuid.variant != uuid.RFC_4122:
    28	            raise ValueError("identity UUID must be RFC 4122 variant UUIDv7")
    29	        if self.value != f"{self.prefix}_{self.uuid}":
    30	            raise ValueError("identity value does not match its canonical parts")
    31	
    32	    @classmethod
    33	    def parse(
    34	        cls,
    35	        value: str,
    36	        *,
    37	        expected_prefix: str | None = None,
    38	    ) -> Identity:
    39	        if not isinstance(value, str):
    40	            raise TypeError("identity must be a string")
    41	        match = _IDENTITY_PATTERN.fullmatch(value)
    42	        if match is None:
    43	            raise ValueError("identity must be a lowercase prefix plus UUIDv7")
    44	        prefix = match.group("prefix")
    45	        if expected_prefix is not None and prefix != expected_prefix:
    46	            raise ValueError(
    47	                f"identity prefix {prefix!r} does not match {expected_prefix!r}"
    48	            )
    49	        parsed_uuid = uuid.UUID(match.group("uuid"))
    50	        return cls(value=value, prefix=prefix, uuid=parsed_uuid)
    51	
    52	    def __str__(self) -> str:
    53	        return self.value

codex
The store does use one explicit `BEGIN IMMEDIATE` transaction for snapshot, journal, and outbox, so I’m now probing the less obvious cases: malformed persisted rows, commit/rollback failures, replay divergence, and policy inputs that are valid Python objects but semantically hostile.
exec
/bin/bash -lc 'wc -l tests/integration/governed_execution/test_sqlite_execution_store.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
250 tests/integration/governed_execution/test_sqlite_execution_store.py

exec
/bin/bash -lc 'wc -l tests/resilience/test_execution_sqlite_crash_boundary.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
98 tests/resilience/test_execution_sqlite_crash_boundary.py

exec
/bin/bash -lc 'wc -l tests/unit/governed_execution/domain/test_application_control.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
64 tests/unit/governed_execution/domain/test_application_control.py

exec
/bin/bash -lc 'wc -l tests/security/test_application_control_pep.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
158 tests/security/test_application_control_pep.py

exec
/bin/bash -lc 'wc -l tests/unit/governed_execution/domain/test_execution.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
318 tests/unit/governed_execution/domain/test_execution.py

exec
/bin/bash -lc 'wc -l tests/unit/governed_execution/application/test_gate_controller.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
132 tests/unit/governed_execution/application/test_gate_controller.py

exec
/bin/bash -lc 'wc -l tests/migration/governed_execution/test_execution_store_migration.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
38 tests/migration/governed_execution/test_execution_store_migration.py

exec
/bin/bash -lc 'wc -l tests/unit/foundation/domain/test_canonical.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
25 tests/unit/foundation/domain/test_canonical.py

exec
/bin/bash -lc 'wc -l tests/unit/foundation/domain/test_identity.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
32 tests/unit/foundation/domain/test_identity.py

exec
/bin/bash -lc 'wc -l tests/replay/governed_execution/test_execution_replay.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
66 tests/replay/governed_execution/test_execution_replay.py

exec
/bin/bash -lc 'nl -ba tests/migration/governed_execution/test_execution_store_migration.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import sqlite3
     4	from pathlib import Path
     5	
     6	from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
     7	    SQLiteExecutionStore,
     8	)
     9	
    10	
    11	def test_initial_migration_is_repeatable_and_records_schema_version(
    12	    tmp_path: Path,
    13	) -> None:
    14	    database_path = tmp_path / "migration.sqlite3"
    15	    store = SQLiteExecutionStore(database_path)
    16	
    17	    store.initialize()
    18	    store.initialize()
    19	
    20	    with sqlite3.connect(database_path) as connection:
    21	        user_version = connection.execute("PRAGMA user_version").fetchone()
    22	        tables = {
    23	            row[0]
    24	            for row in connection.execute(
    25	                """
    26	                SELECT name
    27	                FROM sqlite_schema
    28	                WHERE type = 'table' AND name LIKE 'execution_%'
    29	                """
    30	            )
    31	        }
    32	
    33	    assert user_version == (1,)
    34	    assert tables == {
    35	        "execution_state",
    36	        "execution_journal",
    37	        "execution_outbox",
    38	    }

exec
/bin/bash -lc "nl -ba tests/integration/governed_execution/test_sqlite_execution_store.py | sed -n '1,260p'" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import json
     4	import sqlite3
     5	from concurrent.futures import ThreadPoolExecutor
     6	from pathlib import Path
     7	from threading import Barrier
     8	
     9	import pytest
    10	
    11	from ranex.foundation.canonical import canonical_json
    12	from ranex.foundation.identity import Identity
    13	from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    14	    ExecutionPersistenceIntegrityError,
    15	    SQLiteExecutionStore,
    16	)
    17	from ranex.governed_execution.domain.events import (
    18	    ExecutionCreated,
    19	    ExecutionMarkedReady,
    20	)
    21	from ranex.governed_execution.domain.execution import Execution
    22	from ranex.governed_execution.domain.status import ExecutionStatus
    23	
    24	RUN_ID = Identity.parse(
    25	    "run_01890f47-25a1-7e01-98b3-5f5f6bb25af7",
    26	    expected_prefix="run",
    27	)
    28	WORK_ITEM_ID = Identity.parse(
    29	    "work_01890f47-25a1-7e02-98b3-5f5f6bb25af7",
    30	    expected_prefix="work",
    31	)
    32	PRINCIPAL_ID = Identity.parse(
    33	    "principal_01890f47-25a1-7e03-98b3-5f5f6bb25af7",
    34	    expected_prefix="principal",
    35	)
    36	
    37	
    38	def event_id(sequence: int) -> Identity:
    39	    return Identity.parse(
    40	        f"transition_01890f47-25a1-7f{sequence:02x}-98b3-5f5f6bb25af7",
    41	        expected_prefix="transition",
    42	    )
    43	
    44	
    45	def create_event() -> ExecutionCreated:
    46	    return ExecutionCreated(
    47	        event_id=event_id(1),
    48	        execution_id=RUN_ID,
    49	        expected_version=0,
    50	        occurred_at="2026-07-29T02:00:00Z",
    51	        work_item_id=WORK_ITEM_ID,
    52	        created_by_principal_id=PRINCIPAL_ID,
    53	        workflow_request_ref="workflow-request:sha256:sqlite",
    54	    )
    55	
    56	
    57	def ready_event() -> ExecutionMarkedReady:
    58	    return ExecutionMarkedReady(
    59	        event_id=event_id(2),
    60	        execution_id=RUN_ID,
    61	        expected_version=1,
    62	        occurred_at="2026-07-29T02:00:01Z",
    63	        readiness_snapshot_ref="snapshot:sha256:sqlite-ready",
    64	    )
    65	
    66	
    67	@pytest.fixture
    68	def database_path(tmp_path: Path) -> Path:
    69	    return tmp_path / "kernel.sqlite3"
    70	
    71	
    72	@pytest.fixture
    73	def store(database_path: Path) -> SQLiteExecutionStore:
    74	    execution_store = SQLiteExecutionStore(database_path)
    75	    execution_store.initialize()
    76	    return execution_store
    77	
    78	
    79	def test_transition_commits_canonical_state_version_journal_and_outbox_together(
    80	    store: SQLiteExecutionStore,
    81	    database_path: Path,
    82	) -> None:
    83	    proposed = store.append(create_event())
    84	    ready = store.append(ready_event())
    85	
    86	    assert proposed.status is ExecutionStatus.PROPOSED
    87	    assert proposed.version == 1
    88	    assert ready.status is ExecutionStatus.READY
    89	    assert ready.version == 2
    90	    assert store.load(RUN_ID) == ready
    91	
    92	    with sqlite3.connect(database_path) as connection:
    93	        connection.row_factory = sqlite3.Row
    94	        state_row = connection.execute(
    95	            """
    96	            SELECT canonical_state_json, version, last_event_id
    97	            FROM execution_state
    98	            WHERE execution_id = ?
    99	            """,
   100	            (str(RUN_ID),),
   101	        ).fetchone()
   102	        journal_rows = connection.execute(
   103	            """
   104	            SELECT event_id, previous_version, resulting_version,
   105	                   event_json, resulting_state_json
   106	            FROM execution_journal
   107	            ORDER BY sequence
   108	            """
   109	        ).fetchall()
   110	        outbox_rows = connection.execute(
   111	            """
   112	            SELECT event_id, aggregate_version, payload_json
   113	            FROM execution_outbox
   114	            ORDER BY sequence
   115	            """
   116	        ).fetchall()
   117	
   118	    assert state_row is not None
   119	    state_document = json.loads(state_row["canonical_state_json"])
   120	    assert state_row["canonical_state_json"] == canonical_json(state_document)
   121	    assert state_row["version"] == state_document["version"] == 2
   122	    assert state_row["last_event_id"] == str(event_id(2))
   123	
   124	    assert [
   125	        (row["event_id"], row["previous_version"], row["resulting_version"])
   126	        for row in journal_rows
   127	    ] == [
   128	        (str(event_id(1)), 0, 1),
   129	        (str(event_id(2)), 1, 2),
   130	    ]
   131	    assert all(
   132	        row["event_json"] == canonical_json(json.loads(row["event_json"]))
   133	        and row["resulting_state_json"]
   134	        == canonical_json(json.loads(row["resulting_state_json"]))
   135	        for row in journal_rows
   136	    )
   137	
   138	    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
   139	        (str(event_id(1)), 1),
   140	        (str(event_id(2)), 2),
   141	    ]
   142	    assert all(
   143	        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
   144	        for row in outbox_rows
   145	    )
   146	
   147	
   148	def test_journal_is_database_enforced_append_only(
   149	    store: SQLiteExecutionStore,
   150	    database_path: Path,
   151	) -> None:
   152	    store.append(create_event())
   153	
   154	    with sqlite3.connect(database_path) as connection:
   155	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   156	            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
   157	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   158	            connection.execute("DELETE FROM execution_journal")
   159	
   160	
   161	def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
   162	    store: SQLiteExecutionStore,
   163	) -> None:
   164	    store.append(create_event())
   165	    store.append(ready_event())
   166	
   167	    with pytest.raises(ValueError, match="expected version"):
   168	        store.append(ready_event())
   169	
   170	    assert store.count_journal_entries(RUN_ID) == 2
   171	    assert store.count_outbox_entries(RUN_ID) == 2
   172	
   173	
   174	def test_load_rejects_relational_and_canonical_version_disagreement(
   175	    store: SQLiteExecutionStore,
   176	    database_path: Path,
   177	) -> None:
   178	    store.append(create_event())
   179	    with sqlite3.connect(database_path) as connection:
   180	        connection.execute(
   181	            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
   182	            (str(RUN_ID),),
   183	        )
   184	
   185	    with pytest.raises(
   186	        ExecutionPersistenceIntegrityError,
   187	        match="version disagrees",
   188	    ):
   189	        store.load(RUN_ID)
   190	
   191	
   192	def test_load_rejects_relational_and_canonical_identity_disagreement(
   193	    store: SQLiteExecutionStore,
   194	    database_path: Path,
   195	) -> None:
   196	    store.append(create_event())
   197	    with sqlite3.connect(database_path) as connection:
   198	        raw = connection.execute(
   199	            """
   200	            SELECT canonical_state_json
   201	            FROM execution_state
   202	            WHERE execution_id = ?
   203	            """,
   204	            (str(RUN_ID),),
   205	        ).fetchone()
   206	        assert raw is not None
   207	        document = json.loads(raw[0])
   208	        document["execution_id"] = str(
   209	            Identity.parse(
   210	                "run_01890f47-25a1-7e09-98b3-5f5f6bb25af7",
   211	                expected_prefix="run",
   212	            )
   213	        )
   214	        connection.execute(
   215	            """
   216	            UPDATE execution_state
   217	            SET canonical_state_json = ?
   218	            WHERE execution_id = ?
   219	            """,
   220	            (canonical_json(document), str(RUN_ID)),
   221	        )
   222	
   223	    with pytest.raises(
   224	        ExecutionPersistenceIntegrityError,
   225	        match="identity disagrees",
   226	    ):
   227	        store.load(RUN_ID)
   228	
   229	
   230	def test_concurrent_same_version_transitions_have_one_cas_winner(
   231	    store: SQLiteExecutionStore,
   232	) -> None:
   233	    store.append(create_event())
   234	    barrier = Barrier(2)
   235	
   236	    def attempt() -> Execution | Exception:
   237	        barrier.wait()
   238	        try:
   239	            return store.append(ready_event())
   240	        except Exception as exc:
   241	            return exc
   242	
   243	    with ThreadPoolExecutor(max_workers=2) as executor:
   244	        results = tuple(executor.map(lambda _index: attempt(), range(2)))
   245	
   246	    assert sum(isinstance(result, Execution) for result in results) == 1
   247	    assert sum(isinstance(result, Exception) for result in results) == 1
   248	    assert store.load(RUN_ID).version == 2  # type: ignore[union-attr]
   249	    assert store.count_journal_entries(RUN_ID) == 2
   250	    assert store.count_outbox_entries(RUN_ID) == 2

exec
/bin/bash -lc 'nl -ba tests/resilience/test_execution_sqlite_crash_boundary.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import sqlite3
     4	from pathlib import Path
     5	
     6	import pytest
     7	
     8	from ranex.foundation.identity import Identity
     9	from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    10	    SQLiteExecutionStore,
    11	)
    12	from ranex.governed_execution.domain.events import (
    13	    ExecutionCreated,
    14	    ExecutionMarkedReady,
    15	)
    16	from ranex.governed_execution.domain.status import ExecutionStatus
    17	
    18	RUN_ID = Identity.parse(
    19	    "run_01890f47-25a1-7a11-98b3-5f5f6bb25af7",
    20	    expected_prefix="run",
    21	)
    22	
    23	
    24	def identity(prefix: str, suffix: str) -> Identity:
    25	    return Identity.parse(
    26	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    27	        expected_prefix=prefix,
    28	    )
    29	
    30	
    31	def test_failure_between_journal_and_outbox_leaves_no_partial_state(
    32	    tmp_path: Path,
    33	) -> None:
    34	    database_path = tmp_path / "crash-boundary.sqlite3"
    35	    store = SQLiteExecutionStore(database_path)
    36	    store.initialize()
    37	    store.append(
    38	        ExecutionCreated(
    39	            event_id=identity("transition", "a12"),
    40	            execution_id=RUN_ID,
    41	            expected_version=0,
    42	            occurred_at="2026-07-29T03:00:00Z",
    43	            work_item_id=identity("work", "a13"),
    44	            created_by_principal_id=identity("principal", "a14"),
    45	            workflow_request_ref="workflow-request:sha256:crash",
    46	        )
    47	    )
    48	
    49	    with sqlite3.connect(database_path) as connection:
    50	        connection.executescript(
    51	            """
    52	            CREATE TRIGGER simulate_crash_before_outbox
    53	            BEFORE INSERT ON execution_outbox
    54	            WHEN NEW.aggregate_version = 2
    55	            BEGIN
    56	                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
    57	            END;
    58	            """
    59	        )
    60	
    61	    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
    62	        store.append(
    63	            ExecutionMarkedReady(
    64	                event_id=identity("transition", "a15"),
    65	                execution_id=RUN_ID,
    66	                expected_version=1,
    67	                occurred_at="2026-07-29T03:00:01Z",
    68	                readiness_snapshot_ref="snapshot:sha256:crash-ready",
    69	            )
    70	        )
    71	
    72	    unchanged = store.load(RUN_ID)
    73	    assert unchanged is not None
    74	    assert unchanged.status is ExecutionStatus.PROPOSED
    75	    assert unchanged.version == 1
    76	    assert unchanged.last_event_id == identity("transition", "a12")
    77	    assert store.count_journal_entries(RUN_ID) == 1
    78	    assert store.count_outbox_entries(RUN_ID) == 1
    79	
    80	    with sqlite3.connect(database_path) as connection:
    81	        absent_everywhere = connection.execute(
    82	            """
    83	            SELECT
    84	                (SELECT COUNT(*) FROM execution_state
    85	                 WHERE last_event_id = ?) +
    86	                (SELECT COUNT(*) FROM execution_journal
    87	                 WHERE event_id = ?) +
    88	                (SELECT COUNT(*) FROM execution_outbox
    89	                 WHERE event_id = ?)
    90	            """,
    91	            (
    92	                str(identity("transition", "a15")),
    93	                str(identity("transition", "a15")),
    94	                str(identity("transition", "a15")),
    95	            ),
    96	        ).fetchone()
    97	
    98	    assert absent_everywhere == (0,)

exec
/bin/bash -lc 'nl -ba tests/replay/governed_execution/test_execution_replay.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from ranex.foundation.identity import Identity
     4	from ranex.governed_execution.domain.events import (
     5	    ExecutionCreated,
     6	    ExecutionMarkedReady,
     7	    ExecutionStarted,
     8	    ExecutionSucceeded,
     9	)
    10	from ranex.governed_execution.domain.execution import (
    11	    reduce_execution,
    12	    replay_execution,
    13	)
    14	from ranex.governed_execution.domain.status import ExecutionStatus
    15	
    16	
    17	def identity(prefix: str, suffix: str) -> Identity:
    18	    return Identity.parse(
    19	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    20	        expected_prefix=prefix,
    21	    )
    22	
    23	
    24	def test_replay_reproduces_identical_final_state_and_version() -> None:
    25	    run_id = identity("run", "a01")
    26	    events = (
    27	        ExecutionCreated(
    28	            event_id=identity("transition", "b01"),
    29	            execution_id=run_id,
    30	            expected_version=0,
    31	            occurred_at="2026-07-29T01:00:00Z",
    32	            work_item_id=identity("work", "a02"),
    33	            created_by_principal_id=identity("principal", "a03"),
    34	            workflow_request_ref="workflow-request:sha256:one",
    35	        ),
    36	        ExecutionMarkedReady(
    37	            event_id=identity("transition", "b02"),
    38	            execution_id=run_id,
    39	            expected_version=1,
    40	            occurred_at="2026-07-29T01:00:01Z",
    41	            readiness_snapshot_ref="snapshot:sha256:ready",
    42	        ),
    43	        ExecutionStarted(
    44	            event_id=identity("transition", "b03"),
    45	            execution_id=run_id,
    46	            expected_version=2,
    47	            occurred_at="2026-07-29T01:00:02Z",
    48	            authorization_ref="authorization:sha256:start",
    49	        ),
    50	        ExecutionSucceeded(
    51	            event_id=identity("transition", "b04"),
    52	            execution_id=run_id,
    53	            expected_version=3,
    54	            occurred_at="2026-07-29T01:00:03Z",
    55	            outcome_ref="outcome:sha256:success",
    56	        ),
    57	    )
    58	
    59	    direct = None
    60	    for event in events:
    61	        direct = reduce_execution(direct, event)
    62	    replayed = replay_execution(events)
    63	
    64	    assert replayed == direct
    65	    assert replayed.status is ExecutionStatus.SUCCEEDED
    66	    assert replayed.version == len(events) == 4

exec
/bin/bash -lc 'nl -ba tests/security/test_application_control_pep.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from typing import Any
     4	
     5	import pytest
     6	
     7	from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
     8	from ranex.foundation.identity import Identity
     9	from ranex.governed_execution.adapters.policy.deterministic import (
    10	    DeterministicPolicyAdapter,
    11	)
    12	from ranex.governed_execution.application.application_control_pep import (
    13	    ApplicationControlPEP,
    14	)
    15	from ranex.governed_execution.domain.application_control import (
    16	    ApplicationControlRequest,
    17	)
    18	from ranex.policy.api.contracts import (
    19	    GateCatalog,
    20	    GateDefinition,
    21	    RuleDefinition,
    22	    RuleEnforcementClass,
    23	    RuleResolution,
    24	)
    25	
    26	
    27	def identity(prefix: str, suffix: str) -> Identity:
    28	    return Identity.parse(
    29	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    30	        expected_prefix=prefix,
    31	    )
    32	
    33	
    34	PROJECT_ID = identity("prj", "201")
    35	RUN_ID = identity("run", "202")
    36	REQUESTER_ID = identity("principal", "203")
    37	CHECKER_ID = identity("principal", "204")
    38	
    39	
    40	def request() -> ApplicationControlRequest:
    41	    return ApplicationControlRequest(
    42	        request_id=identity("transition", "205"),
    43	        project_id=PROJECT_ID,
    44	        execution_id=RUN_ID,
    45	        action="EXECUTION_START",
    46	        expected_version=1,
    47	        requested_by=REQUESTER_ID,
    48	    )
    49	
    50	
    51	def evidence() -> EvidenceRecord:
    52	    return EvidenceRecord(
    53	        evidence_id=identity("evd", "206"),
    54	        claim_id="CLAIM-POLICY",
    55	        outcome=GateOutcome.PASS,
    56	        project_id=PROJECT_ID,
    57	        execution_id=RUN_ID,
    58	        action="EXECUTION_START",
    59	        subject_version=1,
    60	        producer_id=CHECKER_ID,
    61	        producer_role="qualified_checker",
    62	        command="policy-check",
    63	        exit_code=0,
    64	        observed_at="2026-07-29T05:00:00Z",
    65	        artifact_sha256="sha256:" + "c" * 64,
    66	        artifact_verified=True,
    67	    )
    68	
    69	
    70	def catalog() -> GateCatalog:
    71	    return GateCatalog(
    72	        catalog_id="RANEX-RD-CATALOG",
    73	        project_id=PROJECT_ID,
    74	        status="R_AND_D",
    75	        owner="human-owner",
    76	        gates=(
    77	            GateDefinition(
    78	                gate_id=identity("gate", "207"),
    79	                action="EXECUTION_START",
    80	                rules=(
    81	                    RuleDefinition(
    82	                        rule_id="RULE-POLICY",
    83	                        enforcement=RuleEnforcementClass.BLOCKING,
    84	                        resolution=RuleResolution.DETERMINISTIC,
    85	                        required_claim_ids=("CLAIM-POLICY",),
    86	                    ),
    87	                ),
    88	            ),
    89	        ),
    90	    )
    91	
    92	
    93	class RaisingPolicyAdapter:
    94	    def evaluate(self, **_kwargs: Any) -> Any:
    95	        raise RuntimeError("policy backend exploded")
    96	
    97	
    98	class MalformedPolicyAdapter:
    99	    def evaluate(self, **_kwargs: Any) -> object:
   100	        return object()
   101	
   102	
   103	def test_pep_fails_closed_when_policy_adapter_raises() -> None:
   104	    decision = ApplicationControlPEP(RaisingPolicyAdapter()).decide(
   105	        request=request(),
   106	        evidence=(evidence(),),
   107	    )
   108	
   109	    assert decision.permitted is False
   110	    assert decision.reason_codes == ("POLICY_ADAPTER_EXCEPTION",)
   111	
   112	
   113	def test_pep_fails_closed_on_malformed_policy_result() -> None:
   114	    decision = ApplicationControlPEP(MalformedPolicyAdapter()).decide(
   115	        request=request(),
   116	        evidence=(evidence(),),
   117	    )
   118	
   119	    assert decision.permitted is False
   120	    assert decision.reason_codes == ("MALFORMED_POLICY_DECISION",)
   121	
   122	
   123	def test_deterministic_policy_adapter_and_pep_produce_same_decision() -> None:
   124	    adapter = DeterministicPolicyAdapter(
   125	        catalog=catalog(),
   126	        catalog_digest="sha256:" + "d" * 64,
   127	    )
   128	    pep = ApplicationControlPEP(adapter)
   129	
   130	    first = pep.decide(request=request(), evidence=(evidence(),))
   131	    second = pep.decide(request=request(), evidence=(evidence(),))
   132	
   133	    assert first == second
   134	    assert first.permitted is True
   135	    assert first.reason_codes == ()
   136	
   137	
   138	def test_pep_denies_when_deterministic_policy_has_no_evidence() -> None:
   139	    adapter = DeterministicPolicyAdapter(
   140	        catalog=catalog(),
   141	        catalog_digest="sha256:" + "d" * 64,
   142	    )
   143	
   144	    decision = ApplicationControlPEP(adapter).decide(
   145	        request=request(),
   146	        evidence=(),
   147	    )
   148	
   149	    assert decision.permitted is False
   150	    assert decision.reason_codes == ("MISSING_BLOCKING_EVIDENCE",)
   151	
   152	
   153	def test_deterministic_policy_adapter_rejects_noncanonical_digest() -> None:
   154	    with pytest.raises(ValueError, match="catalog_digest"):
   155	        DeterministicPolicyAdapter(
   156	            catalog=catalog(),
   157	            catalog_digest="sha256:" + "z" * 64,
   158	        )

exec
/bin/bash -lc 'nl -ba tests/unit/governed_execution/application/test_gate_controller.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from dataclasses import replace
     4	
     5	from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.application.gate_controller import GateController
     8	from ranex.governed_execution.domain.application_control import (
     9	    ApplicationControlRequest,
    10	)
    11	from ranex.policy.api.contracts import (
    12	    GateDefinition,
    13	    RuleDefinition,
    14	    RuleEnforcementClass,
    15	    RuleResolution,
    16	)
    17	
    18	
    19	def identity(prefix: str, suffix: str) -> Identity:
    20	    return Identity.parse(
    21	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    22	        expected_prefix=prefix,
    23	    )
    24	
    25	
    26	PROJECT_ID = identity("prj", "101")
    27	RUN_ID = identity("run", "102")
    28	REQUESTER_ID = identity("principal", "103")
    29	CHECKER_ID = identity("principal", "104")
    30	
    31	
    32	def request() -> ApplicationControlRequest:
    33	    return ApplicationControlRequest(
    34	        request_id=identity("transition", "105"),
    35	        project_id=PROJECT_ID,
    36	        execution_id=RUN_ID,
    37	        action="EXECUTION_START",
    38	        expected_version=2,
    39	        requested_by=REQUESTER_ID,
    40	        subject_actor_ids=(REQUESTER_ID,),
    41	    )
    42	
    43	
    44	def gate() -> GateDefinition:
    45	    return GateDefinition(
    46	        gate_id=identity("gate", "106"),
    47	        action="EXECUTION_START",
    48	        rules=(
    49	            RuleDefinition(
    50	                rule_id="RULE-STATIC-CHECK",
    51	                enforcement=RuleEnforcementClass.BLOCKING,
    52	                resolution=RuleResolution.DETERMINISTIC,
    53	                required_claim_ids=("CLAIM-STATIC-CHECK",),
    54	                independent_producer_required=True,
    55	            ),
    56	        ),
    57	    )
    58	
    59	
    60	def evidence() -> EvidenceRecord:
    61	    return EvidenceRecord(
    62	        evidence_id=identity("evd", "107"),
    63	        claim_id="CLAIM-STATIC-CHECK",
    64	        outcome=GateOutcome.PASS,
    65	        project_id=PROJECT_ID,
    66	        execution_id=RUN_ID,
    67	        action="EXECUTION_START",
    68	        subject_version=2,
    69	        producer_id=CHECKER_ID,
    70	        producer_role="qualified_checker",
    71	        command="ruff check",
    72	        exit_code=0,
    73	        observed_at="2026-07-29T04:00:00Z",
    74	        artifact_sha256="sha256:" + "a" * 64,
    75	        artifact_verified=True,
    76	    )
    77	
    78	
    79	def evaluate(records: tuple[EvidenceRecord, ...]):
    80	    return GateController().evaluate(
    81	        gate=gate(),
    82	        request=request(),
    83	        evidence=records,
    84	        catalog_id="RANEX-RD-CATALOG",
    85	        catalog_digest="sha256:" + "b" * 64,
    86	    )
    87	
    88	
    89	def test_gate_controller_fails_closed_when_evidence_is_missing() -> None:
    90	    decision = evaluate(())
    91	
    92	    assert decision.outcome is GateOutcome.UNKNOWN
    93	    assert decision.authorized is False
    94	    assert decision.missing_claim_ids == ("CLAIM-STATIC-CHECK",)
    95	    assert decision.reason_codes == ("MISSING_BLOCKING_EVIDENCE",)
    96	
    97	
    98	def test_gate_controller_accepts_verified_exact_subject_evidence() -> None:
    99	    decision = evaluate((evidence(),))
   100	
   101	    assert decision.outcome is GateOutcome.PASS
   102	    assert decision.authorized is True
   103	    assert decision.reason_codes == ()
   104	    assert decision.policy_digest.startswith("sha256:")
   105	    assert decision.evidence_digest.startswith("sha256:")
   106	
   107	
   108	def test_gate_controller_rejects_conflict_and_nonindependent_producer() -> None:
   109	    conflict = replace(
   110	        evidence(),
   111	        evidence_id=identity("evd", "108"),
   112	        outcome=GateOutcome.FAIL,
   113	    )
   114	    conflicting = evaluate((evidence(), conflict))
   115	    self_produced = evaluate((replace(evidence(), producer_id=REQUESTER_ID),))
   116	
   117	    assert conflicting.outcome is GateOutcome.CONFLICT
   118	    assert conflicting.authorized is False
   119	    assert self_produced.outcome is GateOutcome.FAIL
   120	    assert self_produced.reason_codes == ("INDEPENDENCE_VIOLATION",)
   121	
   122	
   123	def test_gate_controller_rejects_wrong_subject_and_unverified_artifact() -> None:
   124	    other_run = identity("run", "109")
   125	
   126	    wrong_subject = evaluate((replace(evidence(), execution_id=other_run),))
   127	    unverified = evaluate((replace(evidence(), artifact_verified=False),))
   128	
   129	    assert wrong_subject.outcome is GateOutcome.UNKNOWN
   130	    assert wrong_subject.reason_codes == ("WRONG_SUBJECT_EVIDENCE",)
   131	    assert unverified.outcome is GateOutcome.UNKNOWN
   132	    assert unverified.reason_codes == ("UNVERIFIED_EVIDENCE_ARTIFACT",)

exec
/bin/bash -lc "nl -ba tests/unit/governed_execution/domain/test_execution.py | sed -n '1,180p'" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from dataclasses import replace
     4	
     5	import pytest
     6	
     7	from ranex.foundation.identity import Identity
     8	from ranex.governed_execution.domain.events import (
     9	    ExecutionBlocked,
    10	    ExecutionCancelled,
    11	    ExecutionCreated,
    12	    ExecutionFailed,
    13	    ExecutionMarkedReady,
    14	    ExecutionResumed,
    15	    ExecutionStarted,
    16	    ExecutionSucceeded,
    17	    ExecutionUnblocked,
    18	    ExecutionWaited,
    19	)
    20	from ranex.governed_execution.domain.execution import (
    21	    LEGAL_STATUS_TRANSITIONS,
    22	    InvalidExecutionTransition,
    23	    reduce_execution,
    24	)
    25	from ranex.governed_execution.domain.status import ExecutionStatus
    26	
    27	RUN_ID = Identity.parse(
    28	    "run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7",
    29	    expected_prefix="run",
    30	)
    31	WORK_ITEM_ID = Identity.parse(
    32	    "work_01890f47-25a1-7cc2-98b3-5f5f6bb25af7",
    33	    expected_prefix="work",
    34	)
    35	PRINCIPAL_ID = Identity.parse(
    36	    "principal_01890f47-25a1-7cc3-98b3-5f5f6bb25af7",
    37	    expected_prefix="principal",
    38	)
    39	
    40	
    41	def transition_id(sequence: int) -> Identity:
    42	    value = f"transition_01890f47-25a1-7d{sequence:02x}-98b3-5f5f6bb25af7"
    43	    return Identity.parse(value, expected_prefix="transition")
    44	
    45	
    46	def created() -> ExecutionCreated:
    47	    return ExecutionCreated(
    48	        event_id=transition_id(1),
    49	        execution_id=RUN_ID,
    50	        expected_version=0,
    51	        occurred_at="2026-07-29T00:00:00Z",
    52	        work_item_id=WORK_ITEM_ID,
    53	        created_by_principal_id=PRINCIPAL_ID,
    54	        workflow_request_ref="workflow-request:sha256:created",
    55	    )
    56	
    57	
    58	def ready(*, version: int = 1, sequence: int = 2) -> ExecutionMarkedReady:
    59	    return ExecutionMarkedReady(
    60	        event_id=transition_id(sequence),
    61	        execution_id=RUN_ID,
    62	        expected_version=version,
    63	        occurred_at=f"2026-07-29T00:00:{sequence:02d}Z",
    64	        readiness_snapshot_ref="snapshot:sha256:ready",
    65	    )
    66	
    67	
    68	def started(*, version: int = 2, sequence: int = 3) -> ExecutionStarted:
    69	    return ExecutionStarted(
    70	        event_id=transition_id(sequence),
    71	        execution_id=RUN_ID,
    72	        expected_version=version,
    73	        occurred_at=f"2026-07-29T00:00:{sequence:02d}Z",
    74	        authorization_ref="authorization:sha256:start",
    75	    )
    76	
    77	
    78	def test_creation_is_a_reducer_transition_from_no_state() -> None:
    79	    state = reduce_execution(None, created())
    80	
    81	    assert state.execution_id == RUN_ID
    82	    assert state.work_item_id == WORK_ITEM_ID
    83	    assert state.status is ExecutionStatus.PROPOSED
    84	    assert state.version == 1
    85	    assert state.last_event_id == transition_id(1)
    86	
    87	
    88	def test_reducer_is_deterministic_and_does_not_mutate_input() -> None:
    89	    proposed = reduce_execution(None, created())
    90	    original = replace(proposed)
    91	    event = ready()
    92	
    93	    first = reduce_execution(proposed, event)
    94	    second = reduce_execution(proposed, event)
    95	
    96	    assert first == second
    97	    assert proposed == original
    98	    assert proposed.status is ExecutionStatus.PROPOSED
    99	    assert first.status is ExecutionStatus.READY
   100	    assert first.version == 2
   101	
   102	
   103	def test_block_and_unblock_restore_the_recorded_prior_status() -> None:
   104	    running = reduce_execution(
   105	        reduce_execution(reduce_execution(None, created()), ready()),
   106	        started(),
   107	    )
   108	    blocked = reduce_execution(
   109	        running,
   110	        ExecutionBlocked(
   111	            event_id=transition_id(4),
   112	            execution_id=RUN_ID,
   113	            expected_version=3,
   114	            occurred_at="2026-07-29T00:00:04Z",
   115	            block_reason_code="POLICY_UNAVAILABLE",
   116	            blocking_refs=("policy:sha256:unavailable",),
   117	        ),
   118	    )
   119	
   120	    assert blocked.status is ExecutionStatus.BLOCKED
   121	    assert blocked.blocked_from_status is ExecutionStatus.RUNNING
   122	
   123	    unblocked = reduce_execution(
   124	        blocked,
   125	        ExecutionUnblocked(
   126	            event_id=transition_id(5),
   127	            execution_id=RUN_ID,
   128	            expected_version=4,
   129	            occurred_at="2026-07-29T00:00:05Z",
   130	            target_status=ExecutionStatus.RUNNING,
   131	            refreshed_evidence_ref="snapshot:sha256:refreshed",
   132	        ),
   133	    )
   134	
   135	    assert unblocked.status is ExecutionStatus.RUNNING
   136	    assert unblocked.blocked_from_status is None
   137	    assert unblocked.version == 5
   138	
   139	
   140	def test_illegal_transition_fails_without_changing_state() -> None:
   141	    proposed = reduce_execution(None, created())
   142	    original = replace(proposed)
   143	
   144	    with pytest.raises(
   145	        InvalidExecutionTransition,
   146	        match="PROPOSED cannot apply ExecutionSucceeded",
   147	    ):
   148	        reduce_execution(
   149	            proposed,
   150	            ExecutionSucceeded(
   151	                event_id=transition_id(2),
   152	                execution_id=RUN_ID,
   153	                expected_version=1,
   154	                occurred_at="2026-07-29T00:00:02Z",
   155	                outcome_ref="outcome:sha256:impossible",
   156	            ),
   157	        )
   158	
   159	    assert proposed == original
   160	
   161	
   162	def test_reducer_rejects_wrong_execution_and_stale_version() -> None:
   163	    proposed = reduce_execution(None, created())
   164	    other_run = Identity.parse(
   165	        "run_01890f47-25a1-7cc4-98b3-5f5f6bb25af7",
   166	        expected_prefix="run",
   167	    )
   168	
   169	    with pytest.raises(InvalidExecutionTransition, match="different execution"):
   170	        reduce_execution(proposed, replace(ready(), execution_id=other_run))
   171	    with pytest.raises(InvalidExecutionTransition, match="expected version"):
   172	        reduce_execution(proposed, replace(ready(), expected_version=99))
   173	
   174	
   175	def test_event_type_cannot_impersonate_a_different_legal_edge() -> None:
   176	    proposed = reduce_execution(None, created())
   177	    ready_state = reduce_execution(proposed, ready())
   178	    running = reduce_execution(ready_state, started())
   179	    blocked = reduce_execution(
   180	        running,

exec
/bin/bash -lc "nl -ba tests/unit/governed_execution/domain/test_execution.py | sed -n '181,360p'" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
   181	        ExecutionBlocked(
   182	            event_id=transition_id(4),
   183	            execution_id=RUN_ID,
   184	            expected_version=3,
   185	            occurred_at="2026-07-29T00:00:04Z",
   186	            block_reason_code="BLOCKED",
   187	            blocking_refs=("block:ref",),
   188	        ),
   189	    )
   190	
   191	    with pytest.raises(InvalidExecutionTransition):
   192	        reduce_execution(
   193	            ready_state,
   194	            ExecutionResumed(
   195	                event_id=transition_id(3),
   196	                execution_id=RUN_ID,
   197	                expected_version=2,
   198	                occurred_at="2026-07-29T00:00:03Z",
   199	                signal_ref="signal:not-a-start",
   200	            ),
   201	        )
   202	    with pytest.raises(InvalidExecutionTransition):
   203	        reduce_execution(blocked, started(version=4, sequence=5))
   204	
   205	
   206	def test_registered_execution_transition_set_is_exhaustive() -> None:
   207	    assert (
   208	        frozenset(
   209	            {
   210	                (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
   211	                (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
   212	                (ExecutionStatus.READY, ExecutionStatus.RUNNING),
   213	                (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
   214	                (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
   215	                (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
   216	                (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
   217	                (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
   218	                (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
   219	                (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
   220	                (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
   221	                (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
   222	                (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
   223	                (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
   224	                (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
   225	                (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
   226	                (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
   227	                (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
   228	                (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
   229	            }
   230	        )
   231	        == LEGAL_STATUS_TRANSITIONS
   232	    )
   233	
   234	
   235	@pytest.mark.parametrize(
   236	    ("build_state", "event_type", "target"),
   237	    [
   238	        ("proposed", ExecutionCancelled, ExecutionStatus.CANCELLED),
   239	        ("ready", ExecutionCancelled, ExecutionStatus.CANCELLED),
   240	        ("running", ExecutionWaited, ExecutionStatus.WAITING),
   241	        ("running", ExecutionSucceeded, ExecutionStatus.SUCCEEDED),
   242	        ("running", ExecutionFailed, ExecutionStatus.FAILED),
   243	        ("running", ExecutionCancelled, ExecutionStatus.CANCELLED),
   244	        ("waiting", ExecutionResumed, ExecutionStatus.RUNNING),
   245	        ("waiting", ExecutionFailed, ExecutionStatus.FAILED),
   246	        ("waiting", ExecutionCancelled, ExecutionStatus.CANCELLED),
   247	        ("blocked", ExecutionFailed, ExecutionStatus.FAILED),
   248	        ("blocked", ExecutionCancelled, ExecutionStatus.CANCELLED),
   249	    ],
   250	)
   251	def test_reducer_computes_each_non_blocking_transition_family(
   252	    build_state: str,
   253	    event_type: type,
   254	    target: ExecutionStatus,
   255	) -> None:
   256	    states = _states_for_transition_examples()
   257	    state = states[build_state]
   258	    event = _event_for(event_type, state.version)
   259	
   260	    assert reduce_execution(state, event).status is target
   261	
   262	
   263	def _states_for_transition_examples() -> dict[str, object]:
   264	    proposed = reduce_execution(None, created())
   265	    ready_state = reduce_execution(proposed, ready())
   266	    running = reduce_execution(ready_state, started())
   267	    waiting = reduce_execution(
   268	        running,
   269	        ExecutionWaited(
   270	            event_id=transition_id(4),
   271	            execution_id=RUN_ID,
   272	            expected_version=3,
   273	            occurred_at="2026-07-29T00:00:04Z",
   274	            wait_reason_code="AWAITING_SIGNAL",
   275	        ),
   276	    )
   277	    blocked = reduce_execution(
   278	        running,
   279	        ExecutionBlocked(
   280	            event_id=transition_id(4),
   281	            execution_id=RUN_ID,
   282	            expected_version=3,
   283	            occurred_at="2026-07-29T00:00:04Z",
   284	            block_reason_code="BLOCKED",
   285	            blocking_refs=("block:ref",),
   286	        ),
   287	    )
   288	    return {
   289	        "proposed": proposed,
   290	        "ready": ready_state,
   291	        "running": running,
   292	        "waiting": waiting,
   293	        "blocked": blocked,
   294	    }
   295	
   296	
   297	def _event_for(event_type: type, version: int) -> object:
   298	    common = {
   299	        "event_id": transition_id(version + 1),
   300	        "execution_id": RUN_ID,
   301	        "expected_version": version,
   302	        "occurred_at": f"2026-07-29T00:00:{version + 1:02d}Z",
   303	    }
   304	    if event_type is ExecutionCancelled:
   305	        return ExecutionCancelled(**common, decision_ref="decision:cancel")
   306	    if event_type is ExecutionWaited:
   307	        return ExecutionWaited(**common, wait_reason_code="WAIT")
   308	    if event_type is ExecutionResumed:
   309	        return ExecutionResumed(**common, signal_ref="signal:resolved")
   310	    if event_type is ExecutionSucceeded:
   311	        return ExecutionSucceeded(**common, outcome_ref="outcome:succeeded")
   312	    if event_type is ExecutionFailed:
   313	        return ExecutionFailed(
   314	            **common,
   315	            failure_reason_code="FAILED",
   316	            evidence_ref="evidence:failure",
   317	        )
   318	    raise AssertionError(f"unsupported test event type: {event_type}")

exec
/bin/bash -lc 'nl -ba tests/unit/governed_execution/domain/test_application_control.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import pytest
     4	
     5	from ranex.foundation.identity import Identity
     6	from ranex.governed_execution.domain.application_control import (
     7	    ApplicationControlFacts,
     8	    ApplicationControlRequest,
     9	    decide_application_control,
    10	)
    11	
    12	
    13	def identity(prefix: str, suffix: str) -> Identity:
    14	    return Identity.parse(
    15	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    16	        expected_prefix=prefix,
    17	    )
    18	
    19	
    20	def test_application_control_decision_is_pure_and_deterministic() -> None:
    21	    facts = ApplicationControlFacts(
    22	        decision_well_formed=True,
    23	        request_bound=True,
    24	        gate_passed=True,
    25	        gate_authorized=True,
    26	        reason_codes=(),
    27	    )
    28	
    29	    first = decide_application_control(facts)
    30	    second = decide_application_control(facts)
    31	
    32	    assert first == second
    33	    assert first.permitted is True
    34	
    35	
    36	def test_application_control_decision_denies_malformed_facts() -> None:
    37	    decision = decide_application_control(
    38	        ApplicationControlFacts(
    39	            decision_well_formed=False,
    40	            request_bound=True,
    41	            gate_passed=True,
    42	            gate_authorized=True,
    43	            reason_codes=(),
    44	        )
    45	    )
    46	
    47	    assert decision.permitted is False
    48	    assert decision.reason_codes == ("MALFORMED_POLICY_DECISION",)
    49	
    50	
    51	def test_application_control_request_rejects_noncanonical_actor_order() -> None:
    52	    later = identity("principal", "603")
    53	    earlier = identity("principal", "602")
    54	
    55	    with pytest.raises(ValueError, match="unique and sorted"):
    56	        ApplicationControlRequest(
    57	            request_id=identity("transition", "604"),
    58	            project_id=identity("prj", "605"),
    59	            execution_id=identity("run", "606"),
    60	            action="EXECUTION_START",
    61	            expected_version=0,
    62	            requested_by=identity("principal", "607"),
    63	            subject_actor_ids=(later, earlier),
    64	        )

exec
/bin/bash -lc 'nl -ba tests/unit/foundation/domain/test_canonical.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import math
     4	
     5	import pytest
     6	
     7	from ranex.foundation.canonical import canonical_json, canonical_json_bytes
     8	
     9	
    10	def test_canonical_json_is_compact_sorted_and_unicode_preserving() -> None:
    11	    value = {
    12	        "z": [3, {"β": "snowman ☃"}],
    13	        "a": True,
    14	    }
    15	
    16	    assert canonical_json(value) == '{"a":true,"z":[3,{"β":"snowman ☃"}]}'
    17	    assert canonical_json_bytes(value) == (
    18	        b'{"a":true,"z":[3,{"\xce\xb2":"snowman \xe2\x98\x83"}]}'
    19	    )
    20	
    21	
    22	@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
    23	def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
    24	    with pytest.raises(ValueError):
    25	        canonical_json({"unsafe": value})

exec
/bin/bash -lc 'nl -ba tests/unit/foundation/domain/test_identity.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import pytest
     4	
     5	from ranex.foundation.identity import Identity
     6	
     7	RUN_ID = "run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7"
     8	
     9	
    10	def test_identity_parses_canonical_prefixed_uuid7() -> None:
    11	    identity = Identity.parse(RUN_ID, expected_prefix="run")
    12	
    13	    assert str(identity) == RUN_ID
    14	    assert identity.prefix == "run"
    15	    assert identity.uuid.version == 7
    16	
    17	
    18	@pytest.mark.parametrize(
    19	    ("value", "expected_prefix"),
    20	    [
    21	        (RUN_ID, "work"),
    22	        ("run_01890f47-25a1-4cc1-98b3-5f5f6bb25af7", "run"),
    23	        ("RUN_01890f47-25a1-7cc1-98b3-5f5f6bb25af7", "run"),
    24	        ("run_not-a-uuid", "run"),
    25	    ],
    26	)
    27	def test_identity_rejects_wrong_kind_or_noncanonical_value(
    28	    value: str,
    29	    expected_prefix: str,
    30	) -> None:
    31	    with pytest.raises(ValueError):
    32	        Identity.parse(value, expected_prefix=expected_prefix)

exec
/bin/bash -lc 'nl -ba pyproject.toml' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	[project]
     2	name = "ranex-kernel-tracer"
     3	version = "0.0.0"
     4	description = "Non-authoritative R&D tracer for the proposed Ranex kernel"
     5	requires-python = ">=3.11,<3.15"
     6	dependencies = [
     7	    "PyYAML>=6.0.2,<7",
     8	]
     9	
    10	[dependency-groups]
    11	dev = [
    12	    "pytest>=9.0.2,<10",
    13	    "ruff>=0.15.10,<0.16",
    14	]
    15	
    16	[tool.uv]
    17	package = false
    18	
    19	[tool.pytest.ini_options]
    20	addopts = [
    21	    "--strict-config",
    22	    "--strict-markers",
    23	]
    24	pythonpath = ["src"]
    25	testpaths = ["tests"]
    26	
    27	[tool.ruff]
    28	target-version = "py311"
    29	line-length = 88
    30	
    31	[tool.ruff.lint]
    32	select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

exec
/bin/bash -lc 'nl -ba src/ranex/foundation/__init__.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	"""Semantics-light shared primitives for the Ranex tracer."""

exec
/bin/bash -lc "rg -n \"canonical_(json|sha256|json_bytes)|Identity\\(\" src tests" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
tests/integration/assurance/test_hash_chain_ledger.py:12:from ranex.foundation.canonical import canonical_json
tests/integration/assurance/test_hash_chain_ledger.py:40:    path.write_text(canonical_json(raw) + "\n", encoding="utf-8")
src/ranex/foundation/canonical.py:8:def canonical_json(value: Any) -> str:
src/ranex/foundation/canonical.py:19:def canonical_json_bytes(value: Any) -> bytes:
src/ranex/foundation/canonical.py:21:    return canonical_json(value).encode("utf-8")
src/ranex/foundation/canonical.py:24:def canonical_sha256(value: Any) -> str:
src/ranex/foundation/canonical.py:26:    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:11:from ranex.foundation.canonical import canonical_json
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:49:        canonical_json(
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:71:                record_digest = _sha256_text(canonical_json(record))
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:165:                        if canonical_json(existing_record) != canonical_json(
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:180:            record_digest = _sha256_text(canonical_json(stored_record))
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:195:                canonical_json(
tests/integration/governed_execution/test_sqlite_execution_store.py:11:from ranex.foundation.canonical import canonical_json
tests/integration/governed_execution/test_sqlite_execution_store.py:120:    assert state_row["canonical_state_json"] == canonical_json(state_document)
tests/integration/governed_execution/test_sqlite_execution_store.py:132:        row["event_json"] == canonical_json(json.loads(row["event_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:134:        == canonical_json(json.loads(row["resulting_state_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:143:        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:220:            (canonical_json(document), str(RUN_ID)),
tests/unit/foundation/domain/test_canonical.py:7:from ranex.foundation.canonical import canonical_json, canonical_json_bytes
tests/unit/foundation/domain/test_canonical.py:10:def test_canonical_json_is_compact_sorted_and_unicode_preserving() -> None:
tests/unit/foundation/domain/test_canonical.py:16:    assert canonical_json(value) == '{"a":true,"z":[3,{"β":"snowman ☃"}]}'
tests/unit/foundation/domain/test_canonical.py:17:    assert canonical_json_bytes(value) == (
tests/unit/foundation/domain/test_canonical.py:23:def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
tests/unit/foundation/domain/test_canonical.py:25:        canonical_json({"unsafe": value})
src/ranex/governed_execution/application/gate_controller.py:10:from ranex.foundation.canonical import canonical_json, canonical_sha256
src/ranex/governed_execution/application/gate_controller.py:22:    return f"sha256:{canonical_sha256(value)}"
src/ranex/governed_execution/application/gate_controller.py:76:        documents.sort(key=canonical_json)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:9:from ranex.foundation.canonical import canonical_json, canonical_sha256
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:240:            next_json = canonical_json(next_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:294:            event_json = canonical_json(event_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:295:            resulting_digest = canonical_sha256(next_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:299:                else canonical_sha256(json.loads(previous_json))
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:353:                    canonical_json(outbox_document),
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:398:        if not isinstance(document, dict) or canonical_json(document) != raw:

exec
/bin/bash -lc 'nl -ba src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import hashlib
     4	from pathlib import Path
     5	from typing import Any
     6	
     7	import yaml
     8	from yaml.nodes import MappingNode
     9	
    10	from ranex.foundation.identity import Identity
    11	from ranex.policy.api.contracts import (
    12	    GateCatalog,
    13	    GateDefinition,
    14	    RuleDefinition,
    15	    RuleEnforcementClass,
    16	    RuleResolution,
    17	)
    18	
    19	
    20	class _UniqueKeySafeLoader(yaml.SafeLoader):
    21	    def construct_mapping(
    22	        self,
    23	        node: MappingNode,
    24	        deep: bool = False,
    25	    ) -> dict[object, object]:
    26	        mapping: dict[object, object] = {}
    27	        for key_node, value_node in node.value:
    28	            key = self.construct_object(key_node, deep=deep)
    29	            if key in mapping:
    30	                raise ValueError(f"duplicate YAML key: {key!r}")
    31	            mapping[key] = self.construct_object(value_node, deep=deep)
    32	        return mapping
    33	
    34	
    35	def _mapping(value: Any, field: str) -> dict[str, Any]:
    36	    if not isinstance(value, dict):
    37	        raise ValueError(f"{field} must be a mapping")
    38	    return value
    39	
    40	
    41	def _closed(
    42	    value: dict[str, Any],
    43	    *,
    44	    allowed: frozenset[str],
    45	    field: str,
    46	) -> None:
    47	    unexpected = sorted(set(value) - allowed)
    48	    if unexpected:
    49	        raise ValueError(f"{field} contains unexpected fields: {unexpected}")
    50	
    51	
    52	def _text(value: Any, field: str) -> str:
    53	    if not isinstance(value, str) or not value.strip():
    54	        raise ValueError(f"{field} must be a non-empty string")
    55	    return value.strip()
    56	
    57	
    58	def _boolean(value: Any, field: str) -> bool:
    59	    if not isinstance(value, bool):
    60	        raise ValueError(f"{field} must be a boolean")
    61	    return value
    62	
    63	
    64	def _parse(raw_value: Any) -> GateCatalog:
    65	    raw = _mapping(raw_value, "catalog")
    66	    _closed(
    67	        raw,
    68	        allowed=frozenset(
    69	            {
    70	                "schema_version",
    71	                "artifact_type",
    72	                "catalog_id",
    73	                "project_id",
    74	                "status",
    75	                "owner",
    76	                "gates",
    77	            }
    78	        ),
    79	        field="catalog",
    80	    )
    81	    if raw.get("schema_version") != "1":
    82	        raise ValueError("unsupported policy schema_version")
    83	    if raw.get("artifact_type") != "application_control_policy":
    84	        raise ValueError("unsupported policy artifact_type")
    85	    raw_gates = raw.get("gates")
    86	    if not isinstance(raw_gates, list) or not raw_gates:
    87	        raise ValueError("gates must be a non-empty list")
    88	
    89	    gates: list[GateDefinition] = []
    90	    for gate_index, raw_gate_value in enumerate(raw_gates):
    91	        raw_gate = _mapping(raw_gate_value, f"gates[{gate_index}]")
    92	        _closed(
    93	            raw_gate,
    94	            allowed=frozenset({"gate_id", "action", "rules"}),
    95	            field=f"gates[{gate_index}]",
    96	        )
    97	        raw_rules = raw_gate.get("rules")
    98	        if not isinstance(raw_rules, list) or not raw_rules:
    99	            raise ValueError(f"gates[{gate_index}].rules must be non-empty")
   100	        rules: list[RuleDefinition] = []
   101	        for rule_index, raw_rule_value in enumerate(raw_rules):
   102	            raw_rule = _mapping(
   103	                raw_rule_value,
   104	                f"gates[{gate_index}].rules[{rule_index}]",
   105	            )
   106	            _closed(
   107	                raw_rule,
   108	                allowed=frozenset(
   109	                    {
   110	                        "rule_id",
   111	                        "enforcement",
   112	                        "resolution",
   113	                        "required_claim_ids",
   114	                        "independent_producer_required",
   115	                    }
   116	                ),
   117	                field=f"gates[{gate_index}].rules[{rule_index}]",
   118	            )
   119	            claims_value = raw_rule.get("required_claim_ids")
   120	            if not isinstance(claims_value, list) or not claims_value:
   121	                raise ValueError("required_claim_ids must be a non-empty list")
   122	            claims = tuple(sorted(_text(claim, "claim_id") for claim in claims_value))
   123	            rules.append(
   124	                RuleDefinition(
   125	                    rule_id=_text(raw_rule.get("rule_id"), "rule_id"),
   126	                    enforcement=RuleEnforcementClass(raw_rule.get("enforcement")),
   127	                    resolution=RuleResolution(raw_rule.get("resolution")),
   128	                    required_claim_ids=claims,
   129	                    independent_producer_required=_boolean(
   130	                        raw_rule.get("independent_producer_required", False),
   131	                        "independent_producer_required",
   132	                    ),
   133	                )
   134	            )
   135	        gates.append(
   136	            GateDefinition(
   137	                gate_id=Identity.parse(
   138	                    _text(raw_gate.get("gate_id"), "gate_id"),
   139	                    expected_prefix="gate",
   140	                ),
   141	                action=_text(raw_gate.get("action"), "action"),
   142	                rules=tuple(rules),
   143	            )
   144	        )
   145	    return GateCatalog(
   146	        catalog_id=_text(raw.get("catalog_id"), "catalog_id"),
   147	        project_id=Identity.parse(
   148	            _text(raw.get("project_id"), "project_id"),
   149	            expected_prefix="prj",
   150	        ),
   151	        status=_text(raw.get("status"), "status"),
   152	        owner=_text(raw.get("owner"), "owner"),
   153	        gates=tuple(gates),
   154	    )
   155	
   156	
   157	def load_gate_catalog_bytes(content: bytes) -> GateCatalog:
   158	    try:
   159	        raw = yaml.load(content, Loader=_UniqueKeySafeLoader)
   160	    except ValueError:
   161	        raise
   162	    except yaml.YAMLError as exc:
   163	        raise ValueError("invalid policy YAML") from exc
   164	    return _parse(raw)
   165	
   166	
   167	def load_gate_catalog(path: Path) -> GateCatalog:
   168	    return load_gate_catalog_bytes(path.read_bytes())
   169	
   170	
   171	def load_gate_catalog_with_digest(path: Path) -> tuple[GateCatalog, str]:
   172	    content = path.read_bytes()
   173	    digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
   174	    return load_gate_catalog_bytes(content), digest

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
from dataclasses import dataclass, replace
from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import ExecutionCreated, ExecutionMarkedReady
from ranex.governed_execution.domain.execution import reduce_execution

def ident(prefix, suffix):
    return Identity.parse(f'{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7', expected_prefix=prefix)

run=ident('run','001')
created=ExecutionCreated(event_id=ident('transition','002'),execution_id=run,expected_version=0,occurred_at='2026-01-01T00:00:00Z',work_item_id=ident('work','003'),created_by_principal_id=ident('principal','004'),workflow_request_ref='r')
state=reduce_execution(None, created)
@dataclass(frozen=True, slots=True, kw_only=True)
class UnknownReady(ExecutionMarkedReady):
    pass
unknown=UnknownReady(event_id=ident('transition','005'),execution_id=run,expected_version=1,occurred_at='2026-01-01T00:00:01Z',readiness_snapshot_ref='r')
print('unknown_subclass_status', reduce_execution(state, unknown).status, type(unknown).__name__)
print('key_json_equal', canonical_json({1:'x'}) == canonical_json({'1':'x'}), canonical_json({1:'x'}))
print('key_digest_equal', canonical_sha256({1:'x'}) == canonical_sha256({'1':'x'}))
print('negative_zero', canonical_json(-0.0), canonical_json(0.0))
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
unknown_subclass_status READY UnknownReady
key_json_equal True {"1":"x"}
key_digest_equal True
negative_zero -0.0 0.0

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
from ranex.assurance.api.contracts import EvidenceRecord, GateEvaluation, GateOutcome
from ranex.foundation.identity import Identity
from ranex.governed_execution.application.application_control_pep import ApplicationControlPEP
from ranex.governed_execution.application.gate_controller import GateController
from ranex.governed_execution.domain.application_control import ApplicationControlRequest
from ranex.policy.api.contracts import GateDefinition, RuleDefinition, RuleEnforcementClass, RuleResolution

def i(prefix,s): return Identity.parse(f'{prefix}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7',expected_prefix=prefix)
req_id=i('transition','101'); project=i('prj','102'); run_a=i('run','103'); run_b=i('run','104'); principal=i('principal','105'); checker=i('principal','106')
req_a=ApplicationControlRequest(req_id,project,run_a,'SAFE',1,principal)
req_b=ApplicationControlRequest(req_id,project,run_b,'DANGEROUS',99,principal)
evaluation=GateEvaluation(i('gate','107'),req_id,GateOutcome.PASS,True,(),(),'catalog','sha256:'+'a'*64,'sha256:'+'b'*64,'sha256:'+'c'*64)
class Cached:
 def evaluate(self, **kwargs): return evaluation
print('rebound_pep_permitted', ApplicationControlPEP(Cached()).decide(request=req_b,evidence=()).permitted)

gate=GateDefinition(i('gate','108'),'ACT',(
 RuleDefinition('r',RuleEnforcementClass.BLOCKING,RuleResolution.DETERMINISTIC,('A','B')),
))
req=ApplicationControlRequest(i('transition','109'),project,run_a,'ACT',1,principal)
eid=i('evd','110')
def ev(claim): return EvidenceRecord(eid,claim,GateOutcome.PASS,project,run_a,'ACT',1,checker,'checker','cmd',0,'now','sha256:'+'d'*64,True)
res=GateController().evaluate(gate=gate,request=req,evidence=(ev('A'),ev('B')),catalog_id='catalog',catalog_digest='sha256:'+'e'*64)
print('duplicate_evidence_id', res.outcome, res.authorized)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
rebound_pep_permitted True
duplicate_evidence_id PASS True

exec
/bin/bash -lc 'rg -n "TODO|FIXME|XXX|pass$|NotImplemented|crash|replay|journal|outbox|compare-and-swap|fail-closed|canonical" src/ranex tests' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
tests/migration/governed_execution/test_execution_store_migration.py:36:        "execution_journal",
tests/migration/governed_execution/test_execution_store_migration.py:37:        "execution_outbox",
tests/replay/governed_execution/test_execution_replay.py:12:    replay_execution,
tests/replay/governed_execution/test_execution_replay.py:24:def test_replay_reproduces_identical_final_state_and_version() -> None:
tests/replay/governed_execution/test_execution_replay.py:62:    replayed = replay_execution(events)
tests/replay/governed_execution/test_execution_replay.py:64:    assert replayed == direct
tests/replay/governed_execution/test_execution_replay.py:65:    assert replayed.status is ExecutionStatus.SUCCEEDED
tests/replay/governed_execution/test_execution_replay.py:66:    assert replayed.version == len(events) == 4
tests/resilience/test_execution_sqlite_crash_boundary.py:31:def test_failure_between_journal_and_outbox_leaves_no_partial_state(
tests/resilience/test_execution_sqlite_crash_boundary.py:34:    database_path = tmp_path / "crash-boundary.sqlite3"
tests/resilience/test_execution_sqlite_crash_boundary.py:45:            workflow_request_ref="workflow-request:sha256:crash",
tests/resilience/test_execution_sqlite_crash_boundary.py:52:            CREATE TRIGGER simulate_crash_before_outbox
tests/resilience/test_execution_sqlite_crash_boundary.py:53:            BEFORE INSERT ON execution_outbox
tests/resilience/test_execution_sqlite_crash_boundary.py:56:                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
tests/resilience/test_execution_sqlite_crash_boundary.py:61:    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
tests/resilience/test_execution_sqlite_crash_boundary.py:68:                readiness_snapshot_ref="snapshot:sha256:crash-ready",
tests/resilience/test_execution_sqlite_crash_boundary.py:77:    assert store.count_journal_entries(RUN_ID) == 1
tests/resilience/test_execution_sqlite_crash_boundary.py:78:    assert store.count_outbox_entries(RUN_ID) == 1
tests/resilience/test_execution_sqlite_crash_boundary.py:86:                (SELECT COUNT(*) FROM execution_journal
tests/resilience/test_execution_sqlite_crash_boundary.py:88:                (SELECT COUNT(*) FROM execution_outbox
src/ranex/policy/domain/gates.py:54:            raise ValueError("gate_id must be a canonical gate identity")
src/ranex/policy/domain/gates.py:78:            raise ValueError("project_id must be a canonical project identity")
tests/security/test_application_control_pep.py:153:def test_deterministic_policy_adapter_rejects_noncanonical_digest() -> None:
tests/unit/foundation/domain/test_canonical.py:7:from ranex.foundation.canonical import canonical_json, canonical_json_bytes
tests/unit/foundation/domain/test_canonical.py:10:def test_canonical_json_is_compact_sorted_and_unicode_preserving() -> None:
tests/unit/foundation/domain/test_canonical.py:16:    assert canonical_json(value) == '{"a":true,"z":[3,{"β":"snowman ☃"}]}'
tests/unit/foundation/domain/test_canonical.py:17:    assert canonical_json_bytes(value) == (
tests/unit/foundation/domain/test_canonical.py:23:def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
tests/unit/foundation/domain/test_canonical.py:25:        canonical_json({"unsafe": value})
tests/unit/foundation/domain/test_identity.py:10:def test_identity_parses_canonical_prefixed_uuid7() -> None:
tests/unit/foundation/domain/test_identity.py:27:def test_identity_rejects_wrong_kind_or_noncanonical_value(
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:11:from ranex.foundation.canonical import canonical_json
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:17:    pass
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:49:        canonical_json(
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:60:    """Append-only API over a tamper-evident canonical JSONL hash chain."""
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:71:                record_digest = _sha256_text(canonical_json(record))
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:165:                        if canonical_json(existing_record) != canonical_json(
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:180:            record_digest = _sha256_text(canonical_json(stored_record))
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:195:                canonical_json(
src/ranex/foundation/identity.py:18:    """An opaque canonical Ranex prefix plus UUIDv7 identity."""
src/ranex/foundation/identity.py:26:            raise ValueError("identity prefix is not canonical")
src/ranex/foundation/identity.py:30:            raise ValueError("identity value does not match its canonical parts")
src/ranex/assurance/domain/gates.py:23:        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
src/ranex/assurance/domain/gates.py:33:        raise ValueError(f"{field} must be canonical sha256 lowercase hex")
tests/unit/work_management/domain/test_transitions.py:56:def test_work_transition_request_rejects_noncanonical_actor_order() -> None:
src/ranex/foundation/canonical.py:8:def canonical_json(value: Any) -> str:
src/ranex/foundation/canonical.py:19:def canonical_json_bytes(value: Any) -> bytes:
src/ranex/foundation/canonical.py:20:    """Return the UTF-8 bytes of the canonical JSON representation."""
src/ranex/foundation/canonical.py:21:    return canonical_json(value).encode("utf-8")
src/ranex/foundation/canonical.py:24:def canonical_sha256(value: Any) -> str:
src/ranex/foundation/canonical.py:25:    """Return lowercase SHA-256 hex over the canonical JSON bytes."""
src/ranex/foundation/canonical.py:26:    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
tests/unit/governed_execution/domain/test_application_control.py:51:def test_application_control_request_rejects_noncanonical_actor_order() -> None:
tests/integration/assurance/test_hash_chain_ledger.py:12:from ranex.foundation.canonical import canonical_json
tests/integration/assurance/test_hash_chain_ledger.py:40:    path.write_text(canonical_json(raw) + "\n", encoding="utf-8")
tests/integration/assurance/test_hash_chain_ledger.py:53:    replay = ledger.append_once({"decision": "PASS"}, key="request-1")
tests/integration/assurance/test_hash_chain_ledger.py:55:    assert replay == first
tests/integration/governed_execution/test_sqlite_execution_store.py:11:from ranex.foundation.canonical import canonical_json
tests/integration/governed_execution/test_sqlite_execution_store.py:79:def test_transition_commits_canonical_state_version_journal_and_outbox_together(
tests/integration/governed_execution/test_sqlite_execution_store.py:96:            SELECT canonical_state_json, version, last_event_id
tests/integration/governed_execution/test_sqlite_execution_store.py:102:        journal_rows = connection.execute(
tests/integration/governed_execution/test_sqlite_execution_store.py:106:            FROM execution_journal
tests/integration/governed_execution/test_sqlite_execution_store.py:110:        outbox_rows = connection.execute(
tests/integration/governed_execution/test_sqlite_execution_store.py:113:            FROM execution_outbox
tests/integration/governed_execution/test_sqlite_execution_store.py:119:    state_document = json.loads(state_row["canonical_state_json"])
tests/integration/governed_execution/test_sqlite_execution_store.py:120:    assert state_row["canonical_state_json"] == canonical_json(state_document)
tests/integration/governed_execution/test_sqlite_execution_store.py:126:        for row in journal_rows
tests/integration/governed_execution/test_sqlite_execution_store.py:132:        row["event_json"] == canonical_json(json.loads(row["event_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:134:        == canonical_json(json.loads(row["resulting_state_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:135:        for row in journal_rows
tests/integration/governed_execution/test_sqlite_execution_store.py:138:    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
tests/integration/governed_execution/test_sqlite_execution_store.py:143:        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
tests/integration/governed_execution/test_sqlite_execution_store.py:144:        for row in outbox_rows
tests/integration/governed_execution/test_sqlite_execution_store.py:148:def test_journal_is_database_enforced_append_only(
tests/integration/governed_execution/test_sqlite_execution_store.py:156:            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
tests/integration/governed_execution/test_sqlite_execution_store.py:158:            connection.execute("DELETE FROM execution_journal")
tests/integration/governed_execution/test_sqlite_execution_store.py:161:def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
tests/integration/governed_execution/test_sqlite_execution_store.py:170:    assert store.count_journal_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:171:    assert store.count_outbox_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:174:def test_load_rejects_relational_and_canonical_version_disagreement(
tests/integration/governed_execution/test_sqlite_execution_store.py:192:def test_load_rejects_relational_and_canonical_identity_disagreement(
tests/integration/governed_execution/test_sqlite_execution_store.py:200:            SELECT canonical_state_json
tests/integration/governed_execution/test_sqlite_execution_store.py:217:            SET canonical_state_json = ?
tests/integration/governed_execution/test_sqlite_execution_store.py:220:            (canonical_json(document), str(RUN_ID)),
tests/integration/governed_execution/test_sqlite_execution_store.py:249:    assert store.count_journal_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:250:    assert store.count_outbox_entries(RUN_ID) == 2
src/ranex/work_management/domain/transitions.py:33:        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
src/ranex/work_management/domain/transitions.py:61:            raise ValueError("work transition statuses must be canonical")
src/ranex/work_management/domain/transitions.py:70:        canonical_actor_ids = tuple(sorted(set(self.subject_actor_ids), key=str))
src/ranex/work_management/domain/transitions.py:71:        if self.subject_actor_ids != canonical_actor_ids:
src/ranex/work_management/__init__.py:1:"""Work-management context and canonical work-item ownership."""
src/ranex/governed_execution/domain/events.py:17:        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
src/ranex/governed_execution/domain/events.py:23:        raise ValueError("occurred_at must use canonical UTC Z notation")
src/ranex/governed_execution/domain/events.py:132:            raise ValueError("blocking_refs must be unique and canonically sorted")
src/ranex/governed_execution/domain/execution.py:226:def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
src/ranex/governed_execution/domain/application_control.py:10:        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
src/ranex/governed_execution/domain/application_control.py:36:        canonical_actor_ids = tuple(sorted(set(self.subject_actor_ids), key=str))
src/ranex/governed_execution/domain/application_control.py:37:        if self.subject_actor_ids != canonical_actor_ids:
src/ranex/governed_execution/domain/application_control.py:68:    """Pure fail-closed application-control decision."""
src/ranex/governed_execution/adapters/policy/deterministic.py:28:            raise ValueError("catalog_digest must be canonical SHA-256")
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:5:    canonical_state_json TEXT NOT NULL,
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:11:CREATE TABLE IF NOT EXISTS execution_journal (
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35:CREATE TABLE IF NOT EXISTS execution_outbox (
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:43:        REFERENCES execution_journal(event_id),
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:48:BEFORE UPDATE ON execution_journal
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:50:    SELECT RAISE(ABORT, 'execution_journal is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:53:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:54:BEFORE DELETE ON execution_journal
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:56:    SELECT RAISE(ABORT, 'execution_journal is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:59:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:60:BEFORE UPDATE ON execution_outbox
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:62:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:65:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:66:BEFORE DELETE ON execution_outbox
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:68:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:9:from ranex.foundation.canonical import canonical_json, canonical_sha256
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:55:    """The expected canonical execution version changed before commit."""
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:85:        raise ValueError("canonical execution state has unexpected fields")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:184:    """State, audit journal, and outbox committed in one SQLite transaction."""
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:215:                SELECT execution_id, canonical_state_json, version, last_event_id
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:229:                SELECT execution_id, canonical_state_json, version, last_event_id
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:240:            next_json = canonical_json(next_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:247:                        canonical_state_json,
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:265:                previous_json = str(current_row["canonical_state_json"])
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:270:                    SET canonical_state_json = ?,
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:276:                      AND canonical_state_json = ?
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:290:                        "canonical execution compare-and-swap failed"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:294:            event_json = canonical_json(event_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:295:            resulting_digest = canonical_sha256(next_document)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:299:                else canonical_sha256(json.loads(previous_json))
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:303:                INSERT INTO execution_journal(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:330:            outbox_document = {
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:331:                "schema_version": "execution-outbox/v1",
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:341:                INSERT INTO execution_outbox(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:353:                    canonical_json(outbox_document),
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:366:    def count_journal_entries(self, execution_id: Identity) -> int:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:367:        return self._count_rows("execution_journal", execution_id)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:369:    def count_outbox_entries(self, execution_id: Identity) -> int:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:370:        return self._count_rows("execution_outbox", execution_id)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:374:        if table not in {"execution_journal", "execution_outbox"}:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:387:            raise ValueError("execution_id must be a canonical run identity")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:391:        raw = str(row["canonical_state_json"])
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:396:                "canonical execution state is not JSON"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:398:        if not isinstance(document, dict) or canonical_json(document) != raw:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:400:                "execution state is not canonically serialized"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:406:                "canonical execution state is invalid"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:410:                "relational version disagrees with canonical state version"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:414:                "relational last event disagrees with canonical state"
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:418:                "relational identity disagrees with canonical state identity"
src/ranex/governed_execution/application/ports/execution_repository.py:12:        """Load the current canonical execution snapshot."""
src/ranex/governed_execution/application/gate_controller.py:10:from ranex.foundation.canonical import canonical_json, canonical_sha256
src/ranex/governed_execution/application/gate_controller.py:22:    return f"sha256:{canonical_sha256(value)}"
src/ranex/governed_execution/application/gate_controller.py:62:    """Pure fail-closed evaluator; it is not an Execution reducer."""
src/ranex/governed_execution/application/gate_controller.py:76:        documents.sort(key=canonical_json)

exec
/bin/bash -lc 'rg -n "sqlite3|BEGIN|COMMIT|ROLLBACK|PRAGMA|user_version|execution_state|execution_journal|execution_outbox" src/ranex tests' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
tests/architecture/test_kernel_imports.py:29:        "sqlite3",
tests/migration/governed_execution/test_execution_store_migration.py:3:import sqlite3
tests/migration/governed_execution/test_execution_store_migration.py:14:    database_path = tmp_path / "migration.sqlite3"
tests/migration/governed_execution/test_execution_store_migration.py:20:    with sqlite3.connect(database_path) as connection:
tests/migration/governed_execution/test_execution_store_migration.py:21:        user_version = connection.execute("PRAGMA user_version").fetchone()
tests/migration/governed_execution/test_execution_store_migration.py:33:    assert user_version == (1,)
tests/migration/governed_execution/test_execution_store_migration.py:35:        "execution_state",
tests/migration/governed_execution/test_execution_store_migration.py:36:        "execution_journal",
tests/migration/governed_execution/test_execution_store_migration.py:37:        "execution_outbox",
tests/resilience/test_execution_sqlite_crash_boundary.py:3:import sqlite3
tests/resilience/test_execution_sqlite_crash_boundary.py:34:    database_path = tmp_path / "crash-boundary.sqlite3"
tests/resilience/test_execution_sqlite_crash_boundary.py:49:    with sqlite3.connect(database_path) as connection:
tests/resilience/test_execution_sqlite_crash_boundary.py:53:            BEFORE INSERT ON execution_outbox
tests/resilience/test_execution_sqlite_crash_boundary.py:55:            BEGIN
tests/resilience/test_execution_sqlite_crash_boundary.py:61:    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
tests/resilience/test_execution_sqlite_crash_boundary.py:80:    with sqlite3.connect(database_path) as connection:
tests/resilience/test_execution_sqlite_crash_boundary.py:84:                (SELECT COUNT(*) FROM execution_state
tests/resilience/test_execution_sqlite_crash_boundary.py:86:                (SELECT COUNT(*) FROM execution_journal
tests/resilience/test_execution_sqlite_crash_boundary.py:88:                (SELECT COUNT(*) FROM execution_outbox
tests/integration/governed_execution/test_sqlite_execution_store.py:4:import sqlite3
tests/integration/governed_execution/test_sqlite_execution_store.py:69:    return tmp_path / "kernel.sqlite3"
tests/integration/governed_execution/test_sqlite_execution_store.py:92:    with sqlite3.connect(database_path) as connection:
tests/integration/governed_execution/test_sqlite_execution_store.py:93:        connection.row_factory = sqlite3.Row
tests/integration/governed_execution/test_sqlite_execution_store.py:97:            FROM execution_state
tests/integration/governed_execution/test_sqlite_execution_store.py:106:            FROM execution_journal
tests/integration/governed_execution/test_sqlite_execution_store.py:113:            FROM execution_outbox
tests/integration/governed_execution/test_sqlite_execution_store.py:154:    with sqlite3.connect(database_path) as connection:
tests/integration/governed_execution/test_sqlite_execution_store.py:155:        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
tests/integration/governed_execution/test_sqlite_execution_store.py:156:            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
tests/integration/governed_execution/test_sqlite_execution_store.py:157:        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
tests/integration/governed_execution/test_sqlite_execution_store.py:158:            connection.execute("DELETE FROM execution_journal")
tests/integration/governed_execution/test_sqlite_execution_store.py:179:    with sqlite3.connect(database_path) as connection:
tests/integration/governed_execution/test_sqlite_execution_store.py:181:            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
tests/integration/governed_execution/test_sqlite_execution_store.py:197:    with sqlite3.connect(database_path) as connection:
tests/integration/governed_execution/test_sqlite_execution_store.py:201:            FROM execution_state
tests/integration/governed_execution/test_sqlite_execution_store.py:216:            UPDATE execution_state
src/ranex/work_management/domain/transitions.py:9:_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
src/ranex/work_management/domain/transitions.py:55:        if _COMMIT_PATTERN.fullmatch(self.candidate_commit) is None:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:4:import sqlite3
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:189:    def _connect(self) -> sqlite3.Connection:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:190:        connection = sqlite3.connect(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:195:        connection.row_factory = sqlite3.Row
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:196:        connection.execute("PRAGMA foreign_keys = ON")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:197:        connection.execute("PRAGMA synchronous = FULL")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:216:                FROM execution_state
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:225:        connection.execute("BEGIN IMMEDIATE")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:230:                FROM execution_state
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:245:                    INSERT INTO execution_state(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:269:                    UPDATE execution_state
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:303:                INSERT INTO execution_journal(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:341:                INSERT INTO execution_outbox(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:357:            connection.execute("COMMIT")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:361:                connection.execute("ROLLBACK")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:367:        return self._count_rows("execution_journal", execution_id)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:370:        return self._count_rows("execution_outbox", execution_id)
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:374:        if table not in {"execution_journal", "execution_outbox"}:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390:    def _decode_state_row(row: sqlite3.Row) -> Execution:
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1:BEGIN IMMEDIATE;
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3:CREATE TABLE IF NOT EXISTS execution_state (
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:11:CREATE TABLE IF NOT EXISTS execution_journal (
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:24:        REFERENCES execution_state(execution_id),
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35:CREATE TABLE IF NOT EXISTS execution_outbox (
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:43:        REFERENCES execution_journal(event_id),
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:48:BEFORE UPDATE ON execution_journal
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:49:BEGIN
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:50:    SELECT RAISE(ABORT, 'execution_journal is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:53:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:54:BEFORE DELETE ON execution_journal
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:55:BEGIN
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:56:    SELECT RAISE(ABORT, 'execution_journal is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:59:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:60:BEFORE UPDATE ON execution_outbox
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:61:BEGIN
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:62:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:65:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:66:BEFORE DELETE ON execution_outbox
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:67:BEGIN
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:68:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:71:PRAGMA user_version = 1;
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:73:COMMIT;

exec
/bin/bash -lc 'rg -n "permitted=True|authorized=True|GateOutcome.PASS|return .*PASS|return .*permit" src/ranex tests' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
tests/security/test_application_control_pep.py:55:        outcome=GateOutcome.PASS,
tests/unit/governed_execution/domain/test_application_control.py:25:        gate_authorized=True,
tests/unit/governed_execution/domain/test_application_control.py:42:            gate_authorized=True,
tests/unit/governed_execution/application/test_gate_controller.py:64:        outcome=GateOutcome.PASS,
tests/unit/governed_execution/application/test_gate_controller.py:101:    assert decision.outcome is GateOutcome.PASS
src/ranex/assurance/domain/gates.py:97:        if self.authorized != (self.outcome is GateOutcome.PASS):
src/ranex/assurance/domain/gates.py:99:        if self.outcome is GateOutcome.PASS and self.reason_codes:
src/ranex/assurance/domain/gates.py:101:        if self.outcome is not GateOutcome.PASS and not self.reason_codes:
tests/integration/assurance/test_evidence_artifact_verifier.py:28:        outcome=GateOutcome.PASS,
src/ranex/governed_execution/application/application_control_pep.py:49:                gate_passed=evaluation.outcome is GateOutcome.PASS,
src/ranex/governed_execution/application/gate_controller.py:160:                    GateOutcome.PASS in outcomes and GateOutcome.FAIL in outcomes
src/ranex/governed_execution/application/gate_controller.py:167:                    if record.outcome is GateOutcome.PASS and record.exit_code == 0
src/ranex/governed_execution/application/gate_controller.py:222:        return result(GateOutcome.PASS, authorized=True, reasons=())
src/ranex/governed_execution/domain/application_control.py:62:    return ApplicationControlDecision(permitted=False, reason_codes=reasons)
src/ranex/governed_execution/domain/application_control.py:76:        return deny_application_control("PASS_DECISION_CONTAINS_REASONS")
src/ranex/governed_execution/domain/application_control.py:77:    return ApplicationControlDecision(permitted=True, reason_codes=())

exec
/bin/bash -lc 'nl -ba src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import fcntl
     4	import hashlib
     5	import json
     6	import os
     7	from dataclasses import dataclass
     8	from pathlib import Path
     9	from typing import Any
    10	
    11	from ranex.foundation.canonical import canonical_json
    12	
    13	_GENESIS_DIGEST = "0" * 64
    14	
    15	
    16	class LedgerIntegrityError(RuntimeError):
    17	    pass
    18	
    19	
    20	@dataclass(frozen=True, slots=True)
    21	class LedgerEntry:
    22	    sequence: int
    23	    previous_digest: str
    24	    record_digest: str
    25	    entry_digest: str
    26	    record: dict[str, Any]
    27	
    28	
    29	@dataclass(frozen=True, slots=True)
    30	class LedgerVerification:
    31	    valid: bool
    32	    entry_count: int
    33	    broken_sequence: int | None
    34	    head_digest: str
    35	    reason: str | None = None
    36	
    37	
    38	def _sha256_text(value: str) -> str:
    39	    return hashlib.sha256(value.encode("utf-8")).hexdigest()
    40	
    41	
    42	def _entry_digest(
    43	    *,
    44	    sequence: int,
    45	    previous_digest: str,
    46	    record_digest: str,
    47	) -> str:
    48	    return _sha256_text(
    49	        canonical_json(
    50	            {
    51	                "previous_digest": previous_digest,
    52	                "record_digest": record_digest,
    53	                "sequence": sequence,
    54	            }
    55	        )
    56	    )
    57	
    58	
    59	class HashChainLedger:
    60	    """Append-only API over a tamper-evident canonical JSONL hash chain."""
    61	
    62	    def __init__(self, path: Path) -> None:
    63	        self._path = path
    64	
    65	    def _verify_lines(self, lines: list[str]) -> LedgerVerification:
    66	        previous_digest = _GENESIS_DIGEST
    67	        for expected_sequence, line in enumerate(lines, start=1):
    68	            try:
    69	                raw = json.loads(line)
    70	                record = raw["record"]
    71	                record_digest = _sha256_text(canonical_json(record))
    72	                computed_entry_digest = _entry_digest(
    73	                    sequence=expected_sequence,
    74	                    previous_digest=previous_digest,
    75	                    record_digest=record_digest,
    76	                )
    77	                valid = (
    78	                    raw["sequence"] == expected_sequence
    79	                    and raw["previous_digest"] == previous_digest
    80	                    and raw["record_digest"] == record_digest
    81	                    and raw["entry_digest"] == computed_entry_digest
    82	                )
    83	            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
    84	                valid = False
    85	                computed_entry_digest = previous_digest
    86	            if not valid:
    87	                return LedgerVerification(
    88	                    valid=False,
    89	                    entry_count=len(lines),
    90	                    broken_sequence=expected_sequence,
    91	                    head_digest=previous_digest,
    92	                    reason="ledger hash chain is invalid",
    93	                )
    94	            previous_digest = computed_entry_digest
    95	        return LedgerVerification(
    96	            valid=True,
    97	            entry_count=len(lines),
    98	            broken_sequence=None,
    99	            head_digest=previous_digest,
   100	        )
   101	
   102	    def verify(self) -> LedgerVerification:
   103	        if not self._path.exists():
   104	            return LedgerVerification(
   105	                valid=False,
   106	                entry_count=0,
   107	                broken_sequence=None,
   108	                head_digest=_GENESIS_DIGEST,
   109	                reason="ledger file is missing",
   110	            )
   111	        with self._path.open("r", encoding="utf-8") as stream:
   112	            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
   113	            lines = [line for line in stream.read().splitlines() if line.strip()]
   114	        if not lines:
   115	            return LedgerVerification(
   116	                valid=False,
   117	                entry_count=0,
   118	                broken_sequence=None,
   119	                head_digest=_GENESIS_DIGEST,
   120	                reason="ledger file is empty",
   121	            )
   122	        return self._verify_lines(lines)
   123	
   124	    def append(self, record: dict[str, Any]) -> LedgerEntry:
   125	        return self._append(record, idempotency_key=None)
   126	
   127	    def append_once(self, record: dict[str, Any], *, key: str) -> LedgerEntry:
   128	        if not key:
   129	            raise ValueError("idempotency key must be non-empty")
   130	        return self._append(record, idempotency_key=key)
   131	
   132	    def _append(
   133	        self,
   134	        record: dict[str, Any],
   135	        *,
   136	        idempotency_key: str | None,
   137	    ) -> LedgerEntry:
   138	        if "_ledger_idempotency_key" in record:
   139	            raise ValueError("record uses a reserved ledger field")
   140	        stored_record = dict(record)
   141	        if idempotency_key is not None:
   142	            stored_record["_ledger_idempotency_key"] = idempotency_key
   143	
   144	        self._path.parent.mkdir(parents=True, exist_ok=True)
   145	        self._path.touch(mode=0o600, exist_ok=True)
   146	        self._path.chmod(0o600)
   147	        with self._path.open("a+", encoding="utf-8") as stream:
   148	            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
   149	            stream.seek(0)
   150	            lines = [line for line in stream.read().splitlines() if line.strip()]
   151	            verification = self._verify_lines(lines)
   152	            if not verification.valid:
   153	                raise LedgerIntegrityError(
   154	                    "refusing append because the ledger hash chain is invalid"
   155	                )
   156	
   157	            if idempotency_key is not None:
   158	                for line in lines:
   159	                    raw = json.loads(line)
   160	                    existing_record = raw["record"]
   161	                    if (
   162	                        existing_record.get("_ledger_idempotency_key")
   163	                        == idempotency_key
   164	                    ):
   165	                        if canonical_json(existing_record) != canonical_json(
   166	                            stored_record
   167	                        ):
   168	                            raise LedgerIntegrityError(
   169	                                "idempotency key was reused for a different record"
   170	                            )
   171	                        return LedgerEntry(
   172	                            sequence=raw["sequence"],
   173	                            previous_digest=raw["previous_digest"],
   174	                            record_digest=raw["record_digest"],
   175	                            entry_digest=raw["entry_digest"],
   176	                            record=existing_record,
   177	                        )
   178	
   179	            sequence = verification.entry_count + 1
   180	            record_digest = _sha256_text(canonical_json(stored_record))
   181	            entry_digest = _entry_digest(
   182	                sequence=sequence,
   183	                previous_digest=verification.head_digest,
   184	                record_digest=record_digest,
   185	            )
   186	            entry = LedgerEntry(
   187	                sequence=sequence,
   188	                previous_digest=verification.head_digest,
   189	                record_digest=record_digest,
   190	                entry_digest=entry_digest,
   191	                record=stored_record,
   192	            )
   193	            stream.seek(0, os.SEEK_END)
   194	            stream.write(
   195	                canonical_json(
   196	                    {
   197	                        "sequence": entry.sequence,
   198	                        "previous_digest": entry.previous_digest,
   199	                        "record_digest": entry.record_digest,
   200	                        "entry_digest": entry.entry_digest,
   201	                        "record": entry.record,
   202	                    }
   203	                )
   204	                + "\n"
   205	            )
   206	            stream.flush()
   207	            os.fsync(stream.fileno())
   208	            return entry

Completed the source pass and identified several candidate integrity/fail-open issues; proceeding to validate behavior and coverage with the existing suite.
  ✓ Inspect repository guidance, subject files, and related schemas/types
  ✓ Analyze persistence transactions, CAS, crash windows, and connection/error handling
  ✓ Analyze reducer, policy allow/deny paths, and canonical identity mechanics
  → Run existing tests and audit boundary/failure-path coverage
  • Produce cited adversarial review with findings, inferences, and clean ranges
codex
Two allow-path defects reproduced in-memory: a cached PASS can be rebound to a different request that reuses the same request ID, and two evidence records sharing one evidence ID can satisfy two claims. I’m running the suite now, then I’ll separate implementation defects from coverage gaps and explicit assumptions.
exec
/bin/bash -lc 'PYTHONDONTWRITEBYTECODE=1 UV_NO_SYNC=1 uv run --frozen --no-sync pytest -p no:cacheprovider' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 199ms:
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
configfile: pyproject.toml
testpaths: tests
collected 72 items

tests/architecture/test_kernel_imports.py .........                      [ 12%]
tests/contract/policy/test_gate_policy_loader.py ....                    [ 18%]
tests/integration/assurance/test_evidence_artifact_verifier.py .....     [ 25%]
tests/integration/assurance/test_hash_chain_ledger.py ...                [ 29%]
tests/integration/governed_execution/test_sqlite_execution_store.py .... [ 34%]
..                                                                       [ 37%]
tests/migration/governed_execution/test_execution_store_migration.py .   [ 38%]
tests/replay/governed_execution/test_execution_replay.py .               [ 40%]
tests/resilience/test_execution_sqlite_crash_boundary.py .               [ 41%]
tests/security/test_application_control_pep.py .....                     [ 48%]
tests/unit/foundation/domain/test_canonical.py ....                      [ 54%]
tests/unit/foundation/domain/test_identity.py .....                      [ 61%]
tests/unit/governed_execution/application/test_gate_controller.py ....   [ 66%]
tests/unit/governed_execution/domain/test_application_control.py ...     [ 70%]
tests/unit/governed_execution/domain/test_execution.py ................. [ 94%]
.                                                                        [ 95%]
tests/unit/work_management/domain/test_transitions.py ...                [100%]

============================== 72 passed in 0.20s ==============================

exec
/bin/bash -lc 'git status --short --branch' in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
## feature/kernel-tracer
 M .gitignore
?? pyproject.toml
?? src/
?? tests/
?? uv.lock

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
from types import SimpleNamespace
from ranex.assurance.api.contracts import GateOutcome
from ranex.foundation.identity import Identity
from ranex.governed_execution.application.gate_controller import GateController
from ranex.governed_execution.domain.application_control import ApplicationControlRequest
from ranex.policy.api.contracts import GateDefinition, RuleDefinition, RuleEnforcementClass, RuleResolution

def i(p,s): return Identity.parse(f'{p}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7',expected_prefix=p)
p=i('prj','211'); r=i('run','212'); requester=i('principal','213'); checker=i('principal','214')
req=ApplicationControlRequest(i('transition','215'),p,r,'ACT',1,requester)
gate=GateDefinition(i('gate','216'),'ACT',(RuleDefinition('rule',RuleEnforcementClass.BLOCKING,RuleResolution.DETERMINISTIC,('claim',)),))
record=SimpleNamespace(evidence_id=i('evd','217'),claim_id='claim',outcome=GateOutcome.PASS,project_id=p,execution_id=r,action='ACT',subject_version=1,producer_id=checker,producer_role='checker',command='cmd',exit_code=False,observed_at='not-a-timestamp',artifact_sha256='not-a-digest',artifact_verified='yes')
result=GateController().evaluate(gate=gate,request=req,evidence=(record,),catalog_id='catalog',catalog_digest='sha256:'+'a'*64)
print(result.outcome,result.authorized)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
PASS True

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
import uuid
from ranex.foundation.identity import Identity
class FakeUUID:
    version=7
    variant=uuid.RFC_4122
    def __str__(self): return '01890f47-25a1-7cc1-98b3-5f5f6bb25af7'
identity=Identity('run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7','run',FakeUUID())
print(type(identity.uuid).__name__, str(identity))
try: print(hash(identity))
except Exception as e: print(type(e).__name__)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
FakeUUID run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7
-793304785521672275

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
import uuid
from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
from ranex.foundation.identity import Identity
from ranex.governed_execution.application.gate_controller import GateController
from ranex.governed_execution.domain.application_control import ApplicationControlRequest
from ranex.policy.api.contracts import GateDefinition, RuleDefinition, RuleEnforcementClass, RuleResolution
class F:
 version=7; variant=uuid.RFC_4122
 def __init__(self,s): self.s=s
 def __str__(self): return self.s
def fake(p,s):
 u=f'01890f47-25a1-7{s}-98b3-5f5f6bb25af7'; return Identity(f'{p}_{u}',p,F(u))
def real(p,s): return Identity.parse(f'{p}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7',expected_prefix=p)
requester=fake('principal','301'); same_text_producer=fake('principal','301')
print('same_text',str(requester)==str(same_text_producer),'equal',requester==same_text_producer)
p=real('prj','302'); r=real('run','303')
req=ApplicationControlRequest(real('transition','304'),p,r,'ACT',1,requester)
gate=GateDefinition(real('gate','305'),'ACT',(RuleDefinition('r',RuleEnforcementClass.BLOCKING,RuleResolution.DETERMINISTIC,('c',),True),))
ev=EvidenceRecord(real('evd','306'),'c',GateOutcome.PASS,p,r,'ACT',1,same_text_producer,'role','cmd',0,'now','sha256:'+'a'*64,True)
res=GateController().evaluate(gate=gate,request=req,evidence=(ev,),catalog_id='c',catalog_digest='sha256:'+'b'*64)
print(res.outcome,res.authorized)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
same_text True equal False
PASS True

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 python -B - <<'PY'
import sqlite3
from pathlib import Path
migration=Path('src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql').read_text()
c=sqlite3.connect(':memory:',isolation_level=None)
c.execute('CREATE TABLE execution_state (execution_id TEXT PRIMARY KEY)')
c.executescript(migration)
print(c.execute('PRAGMA user_version').fetchone()[0])
print([r[1] for r in c.execute('PRAGMA table_info(execution_state)')])
print([r[0] for r in c.execute(\"SELECT name FROM sqlite_schema WHERE type='table' AND name LIKE 'execution_%' ORDER BY name\")])
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
1
['execution_id']
['execution_journal', 'execution_outbox', 'execution_state']

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
import sqlite3
from ranex.foundation.canonical import canonical_json
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import SQLiteExecutionStore
run='run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7'; event='transition_01890f47-25a1-7cc2-98b3-5f5f6bb25af7'
doc={'schema_version':'execution-state/v1','execution_id':run,'work_item_id':'work_01890f47-25a1-7cc3-98b3-5f5f6bb25af7','created_by_principal_id':'principal_01890f47-25a1-7cc4-98b3-5f5f6bb25af7','workflow_request_ref':'r','status':'PROPOSED','version':1,'last_event_id':event,'updated_at':'x','blocked_from_status':None}
c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
row=c.execute('SELECT ? AS execution_id, ? AS canonical_state_json, 1.5 AS version, ? AS last_event_id',(run,canonical_json(doc),event)).fetchone()
print(SQLiteExecutionStore._decode_state_row(row).version)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
1

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import ExecutionMarkedReady

def i(p,s): return Identity.parse(f'{p}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7',expected_prefix=p)
for ts in ['2026-01-01T00:00:00Z','2026-01-01 00:00:00Z','2026-01-01T00:00:00.000000Z','2026-01-01T00:00Z']:
 try:
  ExecutionMarkedReady(event_id=i('transition','401'),execution_id=i('run','402'),expected_version=1,occurred_at=ts,readiness_snapshot_ref='r')
  print('accepted',repr(ts))
 except Exception as e: print('rejected',repr(ts),type(e).__name__)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
accepted '2026-01-01T00:00:00Z'
accepted '2026-01-01 00:00:00Z'
accepted '2026-01-01T00:00:00.000000Z'
accepted '2026-01-01T00:00Z'

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -B - <<'PY'
from ranex.assurance.api.contracts import GateEvaluation,GateOutcome
from ranex.foundation.identity import Identity

def i(p,s): return Identity.parse(f'{p}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7',expected_prefix=p)
e=GateEvaluation(i('gate','501'),i('transition','502'),GateOutcome.PASS,True,('MISSING',),(),'c','sha256:'+'a'*64,'sha256:'+'b'*64,'sha256:'+'c'*64)
print(e.outcome,e.authorized,e.missing_claim_ids)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
PASS True ('MISSING',)

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 python -B - <<'PY'
import sqlite3
c=sqlite3.connect(':memory:')
c.execute('CREATE TABLE t(version INTEGER NOT NULL CHECK(version >= 1))')
for v in (1.5,'abc'):
 try:
  c.execute('INSERT INTO t VALUES(?)',(v,)); print('accepted',repr(v),c.execute('SELECT version,typeof(version) FROM t ORDER BY rowid DESC LIMIT 1').fetchone())
 except Exception as e: print('rejected',repr(v),type(e).__name__)
PY" in /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
 succeeded in 0ms:
accepted 1.5 (1.5, 'real')
accepted 'abc' ('abc', 'text')

All 72 existing tests pass. The review is complete, including targeted in-memory reproductions of the fail-open, integrity, migration, canonicalization, and event-subclass cases without changing the workspace.
  ✓ Inspect repository guidance, subject files, and related schemas/types
  ✓ Analyze persistence transactions, CAS, crash windows, and connection/error handling
  ✓ Analyze reducer, policy allow/deny paths, and canonical identity mechanics
  ✓ Run existing tests and audit boundary/failure-path coverage
  ✓ Produce cited adversarial review with findings, inferences, and clean ranges
codex
# Independent code review report

Test run: `72 passed` via `uv run pytest`; the working tree remained unchanged.

## Findings

1. **MAJOR — The mutable snapshot is not anchored to the preceding append-only journal digest, allowing rewritten history to be accepted and extended.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:227-238`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:295-328`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390-420`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:25-32`  
   Scenario: after version 1 records `PROPOSED`, change only the canonical snapshot status to `READY` while retaining its version, identity, and last event; `load()` accepts it, and an `ExecutionStarted(expected_version=1)` commits version 2 whose `previous_state_sha256` does not equal version 1’s journal digest, silently producing `RUNNING` without a ready event.

2. **MAJOR — Snapshot decoding accepts semantically impossible execution states.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:91-125`, `src/ranex/governed_execution/domain/execution.py:52-62`, `src/ranex/governed_execution/domain/execution.py:181-187`  
   Scenario: persist a canonical `BLOCKED` state with `blocked_from_status=null`; `load()` returns it as valid, but every valid `ExecutionUnblocked` event is rejected because no target can match the missing source status.

3. **MAJOR — SQLite version metadata is neither type-strict nor safely decoded.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:6`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408-411`  
   Scenario: SQLite accepts relational `version=1.5`; `int(1.5)` makes `load()` silently accept it as canonical version 1, after which the next CAS cannot match `version=1`; relational `version='abc'` instead leaks a raw `ValueError` rather than `ExecutionPersistenceIntegrityError`.

4. **MAJOR — Initialization can mark an incompatible pre-existing schema as successfully migrated.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:200-208`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3-45`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47-71`, `tests/migration/governed_execution/test_execution_store_migration.py:11-38`  
   Scenario: start with `execution_state(execution_id TEXT PRIMARY KEY)` only; `CREATE TABLE IF NOT EXISTS` preserves that incompatible table, creates the remaining objects, sets `user_version=1`, and commits, but the first append fails because required state columns are absent. The migration test covers only a fresh correct schema initialized twice.

5. **MINOR — A failure in `BEGIN IMMEDIATE` bypasses the append method’s rollback and explicit connection close.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223-226`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:359-364`  
   Scenario: another writer holds the database beyond the five-second timeout; `BEGIN IMMEDIATE` raises before entering `try`, and retaining those exceptions retains unclosed connection objects until traceback cleanup or garbage collection.

6. **MINOR — Relational `updated_at` disagreement is never detected.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:213-220`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408-419`  
   Scenario: change only `execution_state.updated_at` to an obsolete timestamp; direct SQL and canonical state now disagree, but `load()` neither selects nor validates the relational value and reports a healthy execution.

7. **MAJOR — Unknown event subclasses are treated as supported base events rather than rejected exhaustively.**  
   Citations: `src/ranex/governed_execution/domain/execution.py:124-223`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-180`  
   Scenario: subclass `ExecutionMarkedReady` as `ExecutionForceReady`; `reduce_execution()` advances `PROPOSED→READY`, while persistence records the unknown event name but serializes only base-class fields, creating a history outside the declared event union.

8. **MINOR — “Canonical” event timestamps have multiple accepted spellings and therefore unstable state and journal digests.**  
   Citations: `src/ranex/governed_execution/domain/events.py:20-29`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-136`, `src/ranex/foundation/canonical.py:10-16`  
   Scenario: both `2026-01-01T00:00:00Z` and `2026-01-01T00:00:00.000000Z` represent the same instant and pass validation, but produce different `updated_at`, event JSON, and SHA-256 values.

9. **BLOCKER — `GateController` accepts unvalidated record-shaped objects and uses truthiness for security-critical evidence fields, permitting malformed evidence.**  
   Citations: `src/ranex/governed_execution/application/gate_controller.py:73-77`, `src/ranex/governed_execution/application/gate_controller.py:164-180`, `src/ranex/governed_execution/application/gate_controller.py:222`, `src/ranex/governed_execution/application/application_control_pep.py:34-52`  
   Scenario: provide an object with exact-subject `GateOutcome.PASS`, `exit_code=False`, `artifact_verified="yes"`, and invalid timestamp/digest fields; `False == 0` and `"yes"` is truthy, so the deterministic adapter returns authorized `PASS` and the PEP permits it.

10. **BLOCKER — The PEP binds a PASS only by reusable `request_id` and discards `missing_claim_ids`, so authorization is not bound to execution, action, or version.**  
    Citations: `src/ranex/governed_execution/application/application_control_pep.py:42-52`, `src/ranex/governed_execution/domain/application_control.py:14-21`, `src/ranex/assurance/domain/gates.py:79-114`  
    Scenario: obtain a valid PASS for run A, then submit run B/action B/version 99 using the same request ID and have a cached adapter return that evaluation—even with `missing_claim_ids=("CRITICAL",)`; the PEP sets `request_bound=True` and permits run B.

11. **MAJOR — Duplicate evidence identities can independently satisfy multiple required claims.**  
    Citations: `src/ranex/governed_execution/application/gate_controller.py:73-77`, `src/ranex/governed_execution/application/gate_controller.py:137-185`, `src/ranex/governed_execution/application/gate_controller.py:222`, `src/ranex/assurance/domain/gates.py:36-76`  
    Scenario: a gate requires claims A and B; submit two otherwise valid `EvidenceRecord` objects with the same `evidence_id` but different claim IDs, and the controller counts both and returns authorized `PASS` instead of rejecting the identity collision.

12. **MINOR — The final domain decision accepts arbitrary truthy values as validated facts.**  
    Citations: `src/ranex/governed_execution/domain/application_control.py:43-49`, `src/ranex/governed_execution/domain/application_control.py:65-77`  
    Scenario: `ApplicationControlFacts("yes", 1, object(), [1], ())` passes every truthiness check and returns `permitted=True`, despite containing no booleans; the normal PEP path constructs booleans, but direct or deserialized callers are fail-open.

13. **MAJOR — `Identity` does not require its `uuid` component to be a real `uuid.UUID`, allowing identical serialized identities to compare unequal.**  
    Citations: `src/ranex/foundation/identity.py:16-30`, `src/ranex/governed_execution/application/gate_controller.py:128-128`, `src/ranex/governed_execution/application/gate_controller.py:172-175`  
    Scenario: construct two principal identities with the same `value` and prefix but separate fake UUID objects exposing `version=7`, the RFC variant, and matching string output; both pass validation yet compare unequal, so self-produced evidence evades `independent_producer_required` and is authorized.

14. **MINOR — Canonical hashing is non-injective for mapping key types.**  
    Citations: `src/ranex/foundation/canonical.py:8-16`, `src/ranex/foundation/canonical.py:24-26`, `tests/unit/foundation/domain/test_canonical.py:10-25`  
    Scenario: `{1: "PASS"}` and `{"1": "PASS"}` both serialize as `{"1":"PASS"}` and receive the same digest, so an idempotency or integrity comparison can treat distinct Python records as identical; current execution documents use string keys, limiting present exposure.

15. **MAJOR — The replay test never replays persisted journal bytes and is effectively a same-reducer comparison.**  
    Citations: `tests/replay/governed_execution/test_execution_replay.py:24-66`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-180`, `src/ranex/governed_execution/application/ports/execution_repository.py:10-17`  
    Scenario: `_event_to_document()` could omit or corrupt an event field—or persisted digest continuity could be broken—and this test would still pass because both “direct” and “replayed” states consume the original in-memory event objects.

16. **MINOR — The crash-boundary test exercises ordinary exception rollback, not process-crash or commit-durability recovery.**  
    Citations: `tests/resilience/test_execution_sqlite_crash_boundary.py:31-70`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:339-364`  
    Scenario: removing full synchronous durability would not fail this test because its trigger raises `ABORT` and the live process executes the normal `ROLLBACK`; abrupt termination after journal insertion or during commit is never exercised.

17. **MINOR — The concurrency test does not exercise the failed CAS branch.**  
    Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:225-238`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:267-291`, `tests/integration/governed_execution/test_sqlite_execution_store.py:230-250`  
    Scenario: `BEGIN IMMEDIATE` serializes the threads, so the loser reads version 2 and fails in `reduce_execution()` before its `UPDATE`; deleting or breaking the `rowcount != 1` handling would leave this test green because it accepts any exception.

## Verified mechanics

- Snapshot update, journal insert, and outbox insert are inside one explicit transaction, with a single commit and rollback on post-`BEGIN` failures: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223-364`.
- For declared exact event classes, the reducer uses immutable replacement, checks aggregate identity/version, and does not mutate its input: `src/ranex/governed_execution/domain/execution.py:71-87`, `src/ranex/governed_execution/domain/execution.py:99-133`.
- Known non-PASS gate outcomes, missing ordinary evidence, policy exceptions, and non-`GateEvaluation` results deny: `src/ranex/governed_execution/application/gate_controller.py:99-221`, `src/ranex/governed_execution/application/application_control_pep.py:34-44`.
- Lowercase UUIDv7 parsing and expected-prefix enforcement are otherwise strict: `src/ranex/foundation/identity.py:32-53`.
- String-key dictionary ordering and rejection of non-finite floats are stable: `src/ranex/foundation/canonical.py:10-16`.

## Inferences used

- The state digests and append-only journal are intended to detect snapshot tampering and support persisted replay.
- `BLOCKED` must retain exactly one resumable prior status, while non-blocked states must retain none.
- Fail-closed behavior must hold for runtime values, rather than relying solely on Python annotations.
- Request and evidence identities identify one immutable logical object and must not be reused with different contents.
- `missing_claim_ids` denotes authorization-relevant missing claims; if it intentionally includes optional claims on PASS, only that portion of finding 10 drops.
- Canonicalization is expected to reject or distinguish non-string mapping keys; if a string-key-only precondition is enforced outside this tree, finding 14 is lower impact.
- A crash-boundary test is expected to cover abrupt process or power loss, not only a database statement error.
tokens used
162,598
# Independent code review report

Test run: `72 passed` via `uv run pytest`; the working tree remained unchanged.

## Findings

1. **MAJOR — The mutable snapshot is not anchored to the preceding append-only journal digest, allowing rewritten history to be accepted and extended.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:227-238`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:295-328`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390-420`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:25-32`  
   Scenario: after version 1 records `PROPOSED`, change only the canonical snapshot status to `READY` while retaining its version, identity, and last event; `load()` accepts it, and an `ExecutionStarted(expected_version=1)` commits version 2 whose `previous_state_sha256` does not equal version 1’s journal digest, silently producing `RUNNING` without a ready event.

2. **MAJOR — Snapshot decoding accepts semantically impossible execution states.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:91-125`, `src/ranex/governed_execution/domain/execution.py:52-62`, `src/ranex/governed_execution/domain/execution.py:181-187`  
   Scenario: persist a canonical `BLOCKED` state with `blocked_from_status=null`; `load()` returns it as valid, but every valid `ExecutionUnblocked` event is rejected because no target can match the missing source status.

3. **MAJOR — SQLite version metadata is neither type-strict nor safely decoded.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:6`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408-411`  
   Scenario: SQLite accepts relational `version=1.5`; `int(1.5)` makes `load()` silently accept it as canonical version 1, after which the next CAS cannot match `version=1`; relational `version='abc'` instead leaks a raw `ValueError` rather than `ExecutionPersistenceIntegrityError`.

4. **MAJOR — Initialization can mark an incompatible pre-existing schema as successfully migrated.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:200-208`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3-45`, `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47-71`, `tests/migration/governed_execution/test_execution_store_migration.py:11-38`  
   Scenario: start with `execution_state(execution_id TEXT PRIMARY KEY)` only; `CREATE TABLE IF NOT EXISTS` preserves that incompatible table, creates the remaining objects, sets `user_version=1`, and commits, but the first append fails because required state columns are absent. The migration test covers only a fresh correct schema initialized twice.

5. **MINOR — A failure in `BEGIN IMMEDIATE` bypasses the append method’s rollback and explicit connection close.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223-226`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:359-364`  
   Scenario: another writer holds the database beyond the five-second timeout; `BEGIN IMMEDIATE` raises before entering `try`, and retaining those exceptions retains unclosed connection objects until traceback cleanup or garbage collection.

6. **MINOR — Relational `updated_at` disagreement is never detected.**  
   Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:213-220`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408-419`  
   Scenario: change only `execution_state.updated_at` to an obsolete timestamp; direct SQL and canonical state now disagree, but `load()` neither selects nor validates the relational value and reports a healthy execution.

7. **MAJOR — Unknown event subclasses are treated as supported base events rather than rejected exhaustively.**  
   Citations: `src/ranex/governed_execution/domain/execution.py:124-223`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-180`  
   Scenario: subclass `ExecutionMarkedReady` as `ExecutionForceReady`; `reduce_execution()` advances `PROPOSED→READY`, while persistence records the unknown event name but serializes only base-class fields, creating a history outside the declared event union.

8. **MINOR — “Canonical” event timestamps have multiple accepted spellings and therefore unstable state and journal digests.**  
   Citations: `src/ranex/governed_execution/domain/events.py:20-29`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-136`, `src/ranex/foundation/canonical.py:10-16`  
   Scenario: both `2026-01-01T00:00:00Z` and `2026-01-01T00:00:00.000000Z` represent the same instant and pass validation, but produce different `updated_at`, event JSON, and SHA-256 values.

9. **BLOCKER — `GateController` accepts unvalidated record-shaped objects and uses truthiness for security-critical evidence fields, permitting malformed evidence.**  
   Citations: `src/ranex/governed_execution/application/gate_controller.py:73-77`, `src/ranex/governed_execution/application/gate_controller.py:164-180`, `src/ranex/governed_execution/application/gate_controller.py:222`, `src/ranex/governed_execution/application/application_control_pep.py:34-52`  
   Scenario: provide an object with exact-subject `GateOutcome.PASS`, `exit_code=False`, `artifact_verified="yes"`, and invalid timestamp/digest fields; `False == 0` and `"yes"` is truthy, so the deterministic adapter returns authorized `PASS` and the PEP permits it.

10. **BLOCKER — The PEP binds a PASS only by reusable `request_id` and discards `missing_claim_ids`, so authorization is not bound to execution, action, or version.**  
    Citations: `src/ranex/governed_execution/application/application_control_pep.py:42-52`, `src/ranex/governed_execution/domain/application_control.py:14-21`, `src/ranex/assurance/domain/gates.py:79-114`  
    Scenario: obtain a valid PASS for run A, then submit run B/action B/version 99 using the same request ID and have a cached adapter return that evaluation—even with `missing_claim_ids=("CRITICAL",)`; the PEP sets `request_bound=True` and permits run B.

11. **MAJOR — Duplicate evidence identities can independently satisfy multiple required claims.**  
    Citations: `src/ranex/governed_execution/application/gate_controller.py:73-77`, `src/ranex/governed_execution/application/gate_controller.py:137-185`, `src/ranex/governed_execution/application/gate_controller.py:222`, `src/ranex/assurance/domain/gates.py:36-76`  
    Scenario: a gate requires claims A and B; submit two otherwise valid `EvidenceRecord` objects with the same `evidence_id` but different claim IDs, and the controller counts both and returns authorized `PASS` instead of rejecting the identity collision.

12. **MINOR — The final domain decision accepts arbitrary truthy values as validated facts.**  
    Citations: `src/ranex/governed_execution/domain/application_control.py:43-49`, `src/ranex/governed_execution/domain/application_control.py:65-77`  
    Scenario: `ApplicationControlFacts("yes", 1, object(), [1], ())` passes every truthiness check and returns `permitted=True`, despite containing no booleans; the normal PEP path constructs booleans, but direct or deserialized callers are fail-open.

13. **MAJOR — `Identity` does not require its `uuid` component to be a real `uuid.UUID`, allowing identical serialized identities to compare unequal.**  
    Citations: `src/ranex/foundation/identity.py:16-30`, `src/ranex/governed_execution/application/gate_controller.py:128-128`, `src/ranex/governed_execution/application/gate_controller.py:172-175`  
    Scenario: construct two principal identities with the same `value` and prefix but separate fake UUID objects exposing `version=7`, the RFC variant, and matching string output; both pass validation yet compare unequal, so self-produced evidence evades `independent_producer_required` and is authorized.

14. **MINOR — Canonical hashing is non-injective for mapping key types.**  
    Citations: `src/ranex/foundation/canonical.py:8-16`, `src/ranex/foundation/canonical.py:24-26`, `tests/unit/foundation/domain/test_canonical.py:10-25`  
    Scenario: `{1: "PASS"}` and `{"1": "PASS"}` both serialize as `{"1":"PASS"}` and receive the same digest, so an idempotency or integrity comparison can treat distinct Python records as identical; current execution documents use string keys, limiting present exposure.

15. **MAJOR — The replay test never replays persisted journal bytes and is effectively a same-reducer comparison.**  
    Citations: `tests/replay/governed_execution/test_execution_replay.py:24-66`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128-180`, `src/ranex/governed_execution/application/ports/execution_repository.py:10-17`  
    Scenario: `_event_to_document()` could omit or corrupt an event field—or persisted digest continuity could be broken—and this test would still pass because both “direct” and “replayed” states consume the original in-memory event objects.

16. **MINOR — The crash-boundary test exercises ordinary exception rollback, not process-crash or commit-durability recovery.**  
    Citations: `tests/resilience/test_execution_sqlite_crash_boundary.py:31-70`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:339-364`  
    Scenario: removing full synchronous durability would not fail this test because its trigger raises `ABORT` and the live process executes the normal `ROLLBACK`; abrupt termination after journal insertion or during commit is never exercised.

17. **MINOR — The concurrency test does not exercise the failed CAS branch.**  
    Citations: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:225-238`, `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:267-291`, `tests/integration/governed_execution/test_sqlite_execution_store.py:230-250`  
    Scenario: `BEGIN IMMEDIATE` serializes the threads, so the loser reads version 2 and fails in `reduce_execution()` before its `UPDATE`; deleting or breaking the `rowcount != 1` handling would leave this test green because it accepts any exception.

## Verified mechanics

- Snapshot update, journal insert, and outbox insert are inside one explicit transaction, with a single commit and rollback on post-`BEGIN` failures: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223-364`.
- For declared exact event classes, the reducer uses immutable replacement, checks aggregate identity/version, and does not mutate its input: `src/ranex/governed_execution/domain/execution.py:71-87`, `src/ranex/governed_execution/domain/execution.py:99-133`.
- Known non-PASS gate outcomes, missing ordinary evidence, policy exceptions, and non-`GateEvaluation` results deny: `src/ranex/governed_execution/application/gate_controller.py:99-221`, `src/ranex/governed_execution/application/application_control_pep.py:34-44`.
- Lowercase UUIDv7 parsing and expected-prefix enforcement are otherwise strict: `src/ranex/foundation/identity.py:32-53`.
- String-key dictionary ordering and rejection of non-finite floats are stable: `src/ranex/foundation/canonical.py:10-16`.

## Inferences used

- The state digests and append-only journal are intended to detect snapshot tampering and support persisted replay.
- `BLOCKED` must retain exactly one resumable prior status, while non-blocked states must retain none.
- Fail-closed behavior must hold for runtime values, rather than relying solely on Python annotations.
- Request and evidence identities identify one immutable logical object and must not be reused with different contents.
- `missing_claim_ids` denotes authorization-relevant missing claims; if it intentionally includes optional claims on PASS, only that portion of finding 10 drops.
- Canonicalization is expected to reject or distinguish non-string mapping keys; if a string-key-only precondition is enforced outside this tree, finding 14 is lower impact.
- A crash-boundary test is expected to cover abrupt process or power loss, not only a database statement error.
