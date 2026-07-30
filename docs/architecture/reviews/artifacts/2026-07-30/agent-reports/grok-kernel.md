[0m
> build · x-ai/grok-4.5
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
[0m→ [0mRead docs/research/hermes-core-architecture-research-2026-07-27.md[90m [offset=1899, limit=50][0m
[0m✱ [0mGlob "src/ranex/**/*"[90m 95 matches[0m
[0m✱ [0mGlob "tests/**/*"[90m 30 matches[0m
I'll audit the kernel tracer against the Hermes promotion obligations—starting with the governing docs and the four attack surfaces.
[0m→ [0mRead src/ranex/governed_execution/domain/execution.py
[0m→ [0mRead src/ranex/governed_execution/application/application_control_pep.py
[0m→ [0mRead src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
[0m→ [0mRead src/ranex/governed_execution/domain/application_control.py
[0m→ [0mRead src/ranex/governed_execution/adapters/policy/deterministic.py
[0m→ [0mRead tests/replay/governed_execution/test_execution_replay.py
[0m→ [0mRead tests/resilience/test_execution_sqlite_crash_boundary.py
[0m→ [0mRead src/ranex/governed_execution/domain/events.py
[0m→ [0mRead src/ranex/governed_execution/domain/status.py
[0m→ [0mRead src/ranex/foundation/canonical.py
[0m→ [0mRead src/ranex/foundation/identity.py
Reading the attacker-surface sources and related tests.
[0m→ [0mRead src/ranex/governed_execution/application/gate_controller.py
[0m→ [0mRead src/ranex/governed_execution/application/ports/application_control_policy.py
[0m→ [0mRead src/ranex/governed_execution/application/ports/execution_repository.py
[0m→ [0mRead src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
[0m→ [0mRead tests/security/test_application_control_pep.py
[0m→ [0mRead tests/integration/governed_execution/test_sqlite_execution_store.py
[0m→ [0mRead tests/unit/governed_execution/domain/test_execution.py
[0m→ [0mRead tests/architecture/test_kernel_imports.py
[0m✱ [0mGrep "relational snapshot|canonical state authority|journal replay|state authority"[90m in . · 2 matches[0m
[0m✱ [0mGrep "IMPLEMENTATION_START_READY|event.?sourc|replay_execution|list_journal|load_journal|read.*journal"[90m in . · 90 matches[0m
Continuing with ports, gate controller, SQL schema, and remaining tests.
[0m→ [0mRead src/ranex/policy/api/contracts.py
[0m→ [0mRead src/ranex/assurance/api/contracts.py
[0m→ [0mRead tests/migration/governed_execution/test_execution_store_migration.py
[0m→ [0mRead tests/unit/governed_execution/domain/test_application_control.py
[0m✱ [0mGrep "canonical snapshot|relational.*canonical|snapshot.*author|journal.*author|current.*?row|canonical execution state"[90m in docs · 71 matches[0m
[0m
[0m$ [0muv run pytest tests/replay tests/resilience tests/security/test_application_control_pep.py tests/unit/governed_execution tests/integration/governed_execution -q --tb=no 2>&1 | tail -40
......................................                                   [100%]
38 passed in 0.10s
[0m
[0m→ [0mRead src/ranex/assurance/domain/gates.py
[0m→ [0mRead src/ranex/policy/domain/gates.py
[0m→ [0mRead docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md[90m [offset=440, limit=50][0m
[0m✱ [0mGrep "load_journal|read_journal|list_events|journal.*replay|replay.*journal|resulting_state"[90m in src · 5 matches[0m
[0m✱ [0mGrep "isolation_level|BEGIN IMMEDIATE|in_transaction|autocommit"[90m in src/ranex · 4 matches[0m
[0m→ [0mRead src/ranex/governed_execution/domain/__init__.py
[0m
[0m$ [0m# Attack: can snapshot diverge from journal while load still succeeds?
python3 << 'PY'
from pathlib import Path
import tempfile, sqlite3, json
from ranex.foundation.identity import Identity
from ranex.foundation.canonical import canonical_json
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import SQLiteExecutionStore
from ranex.governed_execution.domain.events import ExecutionCreated, ExecutionMarkedReady
from ranex.governed_execution.domain.status import ExecutionStatus

td = Path(tempfile.mkdtemp())
db = td / "t.sqlite3"
store = SQLiteExecutionStore(db)
store.initialize()
run = Identity.parse("run_01890f47-25a1-7a11-98b3-5f5f6bb25af7", expected_prefix="run")
work = Identity.parse("work_01890f47-25a1-7a12-98b3-5f5f6bb25af7", expected_prefix="work")
prin = Identity.parse("principal_01890f47-25a1-7a13-98b3-5f5f6bb25af7", expected_prefix="principal")
t1 = Identity.parse("transition_01890f47-25a1-7a14-98b3-5f5f6bb25af7", expected_prefix="transition")
t2 = Identity.parse("transition_01890f47-25a1-7a15-98b3-5f5f6bb25af7", expected_prefix="transition")
store.append(ExecutionCreated(event_id=t1, execution_id=run, expected_version=0, occurred_at="2026-07-29T00:00:00Z", work_item_id=work, created_by_principal_id=prin, workflow_request_ref="wr:1"))
store.append(ExecutionMarkedReady(event_id=t2, execution_id=run, expected_version=1, occurred_at="2026-07-29T00:00:01Z", readiness_snapshot_ref="snap:1"))
# Forge snapshot only: roll status back to PROPOSED but keep version=2 and last_event_id=t2 for consistency of columns
conn = sqlite3.connect(db)
row = conn.execute("SELECT canonical_state_json FROM execution_state").fetchone()[0]
doc = json.loads(row)
print("before status", doc["status"], "ver", doc["version"])
doc["status"] = "PROPOSED"  # disagree with journal resulting_state at v2 which is READY
forged = canonical_json(doc)
conn.execute("UPDATE execution_state SET canonical_state_json=? WHERE execution_id=?", (forged, str(run)))
conn.commit()
j = conn.execute("SELECT resulting_state_json FROM execution_journal WHERE resulting_version=2").fetchone()[0]
print("journal v2 status", json.loads(j)["status"])
conn.close()
loaded = store.load(run)
print("load succeeded:", loaded is not None, "status", loaded.status if loaded else None, "version", loaded.version if loaded else None)
print("journal count", store.count_journal_entries(run))
# CAS bypass? corrupt version column to match but...菊花
# Try append with expected_version from forged — document version is still 2
from ranex.governed_execution.domain.events import ExecutionStarted
t3 = Identity.parse("transition_01890f47-25a1-7a16-98b3-5f5f6bb25af7", expected_prefix="transition")
try:
    s = store.append(ExecutionStarted(event_id=t3, execution_id=run, expected_version=2, occurred_at="2026-07-29T00:00:02Z", authorization_ref="auth:1"))
    print("append after forge succeeded", s.status, s.version)
except Exception as e:
    print("append after forge failed", type(e), e)
PY
Traceback (most recent call last):
  File "<stdin>", line 3, in <module>
ModuleNotFoundError: No module named 'ranex'
[0m
[0m$ [0mPYTHONPATH=src python3 << 'PY'
from pathlib import Path
import tempfile, sqlite3, json
from ranex.foundation.identity import Identity
from ranex.foundation.canonical import canonical_json
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import SQLiteExecutionStore
from ranex.governed_execution.domain.events import ExecutionCreated, ExecutionMarkedReady, ExecutionStarted

td = Path(tempfile.mkdtemp())
db = td / "t.sqlite3"
store = SQLiteExecutionStore(db)
store.initialize()
run = Identity.parse("run_01890f47-25a1-7a11-98b3-5f5f6bb25af7", expected_prefix="run")
work = Identity.parse("work_01890f47-25a1-7a12-98b3-5f5f6bb25af7", expected_prefix="work")
prin = Identity.parse("principal_01890f47-25a1-7a13-98b3-5f5f6bb25af7", expected_prefix="principal")
t1 = Identity.parse("transition_01890f47-25a1-7a14-98b3-5f5f6bb25af7", expected_prefix="transition")
t2 = Identity.parse("transition_01890f47-25a1-7a15-98b3-5f5f6bb25af7", expected_prefix="transition")
t3 = Identity.parse("transition_01890f47-25a1-7a16-98b3-5f5f6bb25af7", expected_prefix="transition")
store.append(ExecutionCreated(event_id=t1, execution_id=run, expected_version=0, occurred_at="2026-07-29T00:00:00Z", work_item_id=work, created_by_principal_id=prin, workflow_request_ref="wr:1"))
store.append(ExecutionMarkedReady(event_id=t2, execution_id=run, expected_version=1, occurred_at="2026-07-29T00:00:01Z", readiness_snapshot_ref="snap:1"))

conn = sqlite3.connect(db)
row = conn.execute("SELECT canonical_state_json FROM execution_state").fetchone()[0]
doc = json.loads(row)
print("before status", doc["status"], "ver", doc["version"])
doc["status"] = "PROPOSED"  # journal last is READY
forged = canonical_json(doc)
conn.execute("UPDATE execution_state SET canonical_state_json=? WHERE execution_id=?", (forged, str(run)))
conn.commit()
j = conn.execute("SELECT resulting_state_json FROM execution_journal WHERE resulting_version=2").fetchone()[0]
print("journal v2 status", json.loads(j)["status"])
conn.close()
loaded = store.load(run)
print("load ok", loaded.status, loaded.version)

try:
    s = store.append(ExecutionStarted(event_id=t3, execution_id=run, expected_version=2, occurred_at="2026-07-29T00:00:02Z", authorization_ref="auth:1"))
    print("append after forge", s.status, s.version)
except Exception as e:
    print("append after forge failed", type(e).__name__, e)

# Direct forge version bypass: bump version without journal
conn = sqlite3.connect(db)
row = conn.execute("SELECT canonical_state_json, version FROM execution_state").fetchone()
doc = json.loads(row[0])
print("mid status", doc["status"], doc["version"])
doc["status"] = "SUCCEEDED"
doc["version"] = 99
t99 = Identity.parse("transition_01890f47-25a1-7a99-98b3-5f5f6bb25af7", expected_prefix="transition")
doc["last_event_id"] = str(t99)
forged = canonical_json(doc)
conn.execute("UPDATE execution_state SET canonical_state_json=?, version=?, last_event_id=? WHERE execution_id=?",
             (forged, 99, str(t99), str(run)))
conn.commit()
conn.close()
loaded = store.load(run)
print("forged terminal load", loaded.status, loaded.version, loaded.last_event_id)
print("journal still", store.count_journal_entries(run))

# subclass GateEvaluation exploit via PEP?
from ranex.assurance.api.contracts import GateEvaluation, GateOutcome
from ranex.governed_execution.application.application_control_pep import ApplicationControlPEP
from ranex.governed_execution.domain.application_control import ApplicationControlRequest

class Rogue:
    def evaluate(self, **kw):
        return GateEvaluation(
            gate_id=Identity.parse("gate_01890f47-25a1-7b01-98b3-5f5f6bb25af7", expected_prefix="gate"),
            request_id=Identity.parse("transition_01890f47-25a1-7b02-98b3-5f5f6bb25af7", expected_prefix="transition"),
            outcome=GateOutcome.PASS,
            authorized=True,
            missing_claim_ids=(),
            reason_codes=(),
            catalog_id="X",
            catalog_digest="sha256:"+"a"*64,
            policy_digest="sha256:"+"b"*64,
            evidence_digest="sha256:"+"c"*64,
        )

req = ApplicationControlRequest(
    request_id=Identity.parse("transition_01890f47-25a1-7b02-98b3-5f5f6bb25af7", expected_prefix="transition"),
    project_id=Identity.parse("prj_01890f47-25a1-7b03-98b3-5f5f6bb25af7", expected_prefix="prj"),
    execution_id=run,
    action="ANYTHING",
    expected_version=0,
    requested_by=prin,
)
d = ApplicationControlPEP(Rogue()).decide(request=req, evidence=())
print("rogue allow", d.permitted, d.reason_codes)

# mismatched request_id
class Mismatch:
    def evaluate(self, **kw):
        return GateEvaluation(
            gate_id=Identity.parse("gate_01890f47-25a1-7b01-98b3-5f5f6bb25af7", expected_prefix="gate"),
            request_id=Identity.parse("transition_01890f47-25a1-7b09-98b3-5f5f6bb25af7", expected_prefix="transition"),
            outcome=GateOutcome.PASS,
            authorized=True,
            missing_claim_ids=(),
            reason_codes=(),
            catalog_id="X",
            catalog_digest="sha256:"+"a"*64,
            policy_digest="sha256:"+"b"*64,
            evidence_digest="sha256:"+"c"*64,
        )
d2 = ApplicationControlPEP(Mismatch()).decide(request=req, evidence=())
print("mismatch deny", d2.permitted, d2.reason_codes)

# Pass with missing_claim_ids non-empty - GateEvaluation forbids... check VALIDATOR
try:
    GateEvaluation(
        gate_id=Identity.parse("gate_01890f47-25a1-7b01-98b3-5f5f6bb25af7", expected_prefix="gate"),
        request_id=Identity.parse("transition_01890f47-25a1-7b02-98b3-5f5f6bb25af7", expected_prefix="transition"),
        outcome=GateOutcome.PASS,
        authorized=True,
        missing_claim_ids=("CLAIM-X",),
        reason_codes=(),
        catalog_id="X",
        catalog_digest="sha256:"+"a"*64,
        policy_digest="sha256:"+"b"*64,
        evidence_digest="sha256:"+"c"*64,
    )
    print("PASS with missing claims constructed OK")
except Exception as e:
    print("PASS with missing claims rejected", e)

# Subclass that bypasses isinstance
class FakeEval(GateEvaluation):
    def __init__(self):
        object.__setattr__(self, 'request_id', req.request_id)
        object.__setattr__(self, 'outcome', GateOutcome.PASS)
        object.__setattr__(self, 'authorized', True)
        object.__setattr__(self, 'reason_codes', ())
        # skip rest

# frozen dataclass hard to fake without calling __init__

# Can object() with GateEvaluation MRO? isinstance needs inheritance

# Isolation_level and multi-connection partial write - reinforce unit of work: OK

# Canappend construct Execution without reduce by writing state alone?
print("DONE")
PY
before status READY ver 2
journal v2 status READY
load ok PROPOSED 2
append after forge failed InvalidExecutionTransition PROPOSED cannot apply ExecutionStarted
mid status PROPOSED 2
forged terminal load SUCCEEDED 99 transition_01890f47-25a1-7a99-98b3-5f5f6bb25af7
journal still 2
rogue allow True ()
mismatch deny False ('POLICY_DECISION_SUBJECT_MISMATCH',)
PASS with missing claims constructed OK
DONE
[0m
[0m$ [0mPYTHONPATH=src python3 << 'PY'
from ranex.foundation.identity import Identity
from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.adapters.policy.deterministic import DeterministicPolicyAdapter
from ranex.governed_execution.application.application_control_pep import ApplicationControlPEP
from ranex.governed_execution.domain.application_control import ApplicationControlRequest
from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
from ranex.policy.api.contracts import GateCatalog, GateDefinition, RuleDefinition, RuleEnforcementClass, RuleResolution

def idp(p,s):
    return Identity.parse(f"{p}_01890f47-25a1-7{s}-98b3-5f5f6bb25af7", expected_prefix=p)

prj=idp("prj","201"); run=idp("run","202"); prin=idp("principal","203"); chk=idp("principal","204")
# Empty-rules path can't - need BLOCKING. Catalog with no claims required on rule still needs required_claim_ids non-empty.
# Adapter accepts arbitrary digest not matching catalog:
cat=GateCatalog(catalog_id="C", project_id=prj, status="R_AND_D", owner="o", gates=(
 GateDefinition(gate_id=idp("gate","207"), action="A", rules=(
  RuleDefinition(rule_id="R", enforcement=RuleEnforcementClass.BLOCKING, resolution=RuleResolution.DETERMINISTIC, required_claim_ids=("C1",)),
 ),),
))
ad=DeterministicPolicyAdapter(catalog=cat, catalog_digest="sha256:"+"0"*64)  # not bound to content
print("unbound digest accepted")

# GateEvaluation PASS+missing via PEP determining allow
from ranex.assurance.domain.gates import GateEvaluation
class Ad:
  def evaluate(self, **k):
    return GateEvaluation(
      gate_id=idp("gate","207"),
      request_id=idp("transition","205"),
      outcome=GateOutcome.PASS,
      authorized=True,
      missing_claim_ids=("C1",),
      reason_codes=(),
      catalog_id="C",
      catalog_digest="sha256:"+"0"*64,
      policy_digest="sha256:"+"1"*64,
      evidence_digest="sha256:"+"2"*64,
    )
req=ApplicationControlRequest(request_id=idp("transition","205"), project_id=prj, execution_id=run, action="A", expected_version=1, requested_by=prin)
d=ApplicationControlPEP(Ad()).decide(request=req, evidence=())
print("allow despite missing claims", d)

# Can construct Execution with illegal pair PROTOSED v99 excluding reducer?
from ranex.governed_execution.domain.execution import Execution
from ranex.governed_execution.domain.status import ExecutionStatus
e=Execution(execution_id=run, work_item_id=idp("work","208"), created_by_principal_id=prin, workflow_request_ref="x", status=ExecutionStatus.SUCCEEDED, version=1, last_event_id=idp("transition","205"), updated_at="2026-07-29T00:00:00Z")
print("direct Execution construction without reducer", e.status, e.version)
PY
unbound digest accepted
allow despite missing claims ApplicationControlDecision(permitted=True, reason_codes=())
direct Execution construction without reducer SUCCEEDED 1
[0m
[0m✱ [0mGrep "catalog_digest|canonical_sha256\(.*catalog|_catalog_digest"[90m in src/ranex · 9 matches[0m
[0m→ [0mRead docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md[90m [offset=468, limit=12][0m
[0m✱ [0mGrep "mismatch is corruption|never replace the journal|operational read source"[90m in docs · 5 matches[0m
Checking catalog_digest binding and a few remaining edges.
## Findings

### F-001 — BLOCKER
**Claim:** `SQLiteExecutionStore.load` treats the relational snapshot as sole readable authority and never detects current-row/journal mismatch, so corrupted or forged snapshot state is returned (including terminal statuses that never appear in the journal).

**Evidence:**
- `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:210-221` — `load` SELECTs only `execution_state`.
- `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390-420` — integrity checks compare columns ↔ JSON inside the snapshot row only; no journal join, no `resulting_state_json` / sha256 reconcile, no version chain check.
- `src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3-9` — `execution_state` is a mutable UPDATE target; no reject-update trigger (contrast journal/outbox triggers at `:47-69`).
- Architecture obligation that mismatch is corruption and must block: `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:475-476`; research `docs/research/hermes-core-architecture-research-2026-07-27.md:2025`.
- Runtime demonstration (PYTHONPATH=src): after two honest appends (READY@v2), direct SQL rewrote `canonical_state_json` status to `PROPOSED` while version/last_event_id stayed consistent with columns; `load` returned `PROPOSED` v2. Further forge to `SUCCEEDED` v99/`last_event_id` invented; `load` returned forged terminal; `count_journal_entries` stayed 2.

**Counter-argument:** R&D tracer with trusted filesystem; external SQL rewrite is out of scope; CAS at `execution_store.py:267-291` protects concurrent honest writers.
**Does counter win?** No. Obligation is absolute (“mismatch is corruption and blocks”); loader is the authority read path and silently serves mismatched snapshot. Cas does not run on `load`.

---

### F-002 — BLOCKER
**Claim:** Version/fencing authority is bypassable for any party that can UPDATE `execution_state`: fence exists only inside `append` CAS, not as durable integrity of stored authority.

**Evidence:**
- CAS only on UPDATE path: `execution_store.py:267-291` (`WHERE … version = ? AND canonical_state_json = ?`).
- Create path has no prior-version fence (insert-only): `execution_store.py:242-260`.
- After F-001 forge to v99 SUCCEEDED, store treats that version as current base for any future reduce/CAS attempt that loads it first (`append` decodes snapshot at `:235-238` then `reduce_execution`).
- No trigger prevents `UPDATE execution_state` (`001_execution_kernel.sql:3-9` vs `:47-69`).

**Counter-argument:** Fence is an optimistic concurrency control for multi-writer races, not an anti-tamper seal; SQLite file ACL (`chmod 0o600` at `execution_store.py:208`) is the boundary.
**Does counter win?** No against HERMES-PROMOTION-060/061 + Ground Zero 8.3. Integrity failure mode required by architecture is block-on-mismatch; only concurrent honest CAS is implemented.

---

### F-003 — MAJOR
**Claim:** Session inference “relational snapshot, not journal replay, is canonical state authority” is **not** declared in those terms; nearest proclaimed model is dual: current row = operational read, journal = replay/audit oracle that snapshots must not replace; mismatch blocks.

**Evidence:**
- Declared model: `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:472-476`; research `docs/research/hermes-core-architecture-research-2026-07-27.md:2025`; review echo `docs/architecture/reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md:172`.
- Repo grep for the session phrase / “state authority” and the exact “snapshot…canonical state authority” wording: no match in code or binding promotions ADR-0013 (search concentrated on docs + src).
- Code implements snapshot-only reads (`execution_store.py:210-221`, port docstring `execution_repository.py:11-12`) and never uses journal as load oracle or mismatch detector — a one-sided amputation of 8.3, not a declared decision artifact.

**Counter-argument:** HERMES-PROMOTION-060 literally requires relational canonical state; dual-write journal is audit; ADR-0006 prefers selective journal not full ES.
**Does counter win?** Partial for “relational state exists.” Does not dissolve undeclared inference nor dissolve missing mismatch gate in 8.3.

---

### F-004 — MAJOR
**Claim:** Application-control PEP fails open on syntactically valid but subtively incoherent `GateEvaluation` objects: `PASS` + `authorized=True` + non-empty `missing_claim_ids` yields `permitted=True`.

**Evidence:**
- `GateEvaluation.__post_init__` forbids PASS with reasons (`assurance/domain/gates.py:99-100`) and ties authorized↔PASS (`:97-98`) but **never** requires `missing_claim_ids == ()` on PASS.
- PEP maps only well-formed/request_bound/outcome/authorized/reasons (`application_control_pep.py:42-52`); never inspects `missing_claim_ids`.
- Domain allow arm: `application_control.py:73-77` — allow when pass∧authorized∧no reasons.
- Demo: constructed `GateEvaluation(..., outcome=PASS, authorized=True, missing_claim_ids=("C1",), reason_codes=())` → `ApplicationControlPEP.decide` → `permitted=True`.

**Counter-argument:** Honest `GateController` only returns PASS with empty missing (`gate_controller.py:222`); `GateEvaluation` package validation is the intended choke; PEP trusts PDP type.
**Does counter win?** No for fail-closed PEP (HERMES-PROMOTION-063 / research:1907-1908 / HERMES-PROMOTION-025 style). Fail-closed means untrustworthy or inconsistent decisions deny; isinstance is not semantic closure.

---

### F-005 — MAJOR
**Claim:** `DeterministicPolicyAdapter` does not bind `catalog_digest` to catalog bytes — any `sha256:[0-9a-f]{64}` is accepted and later emitted as if it authenticated the catalog (breaks exact policy-binding intent used by evidence/gate stack).

**Evidence:**
- `deterministic.py:27-30` — format check only; stores caller digest separately from `catalog`.
- Digest forwarded unchanged into evaluation: `deterministic.py:41-46` → `gate_controller.py:94`.
- Demo: `DeterministicPolicyAdapter(catalog=cat, catalog_digest="sha256:"+"0"*64)` constructs without hashing `cat`.

**Counter-argument:** Digest is composition-root responsibility; adapter is pure evaluator over already-bound inputs.
**Does counter win?** Weak. Port claims “deterministic, exact-subject” (`application_control_policy.py:18`); lying digest is non-determinism of attestation. Without binding, PEP decisions carry unfalsifiable policy identity.

---

### F-006 — MAJOR
**Claim:** Named replay test does not validate replay of pinned history against stores/journal or full state authority; it only checks that `replay_execution` is a thin loop over the same `reduce_execution` (tautology relative to HERMES-PROMOTION-032/065).

**Evidence:**
- `tests/replay/governed_execution/test_execution_replay.py:59-66` — builds `direct` by calling `reduce_execution` repeatedly, `replayed = replay_execution(events)`, asserts `replayed == direct` and status/version.
- `replay_execution` definition: `execution.py:226-237` — solely `reduce_execution` in a for-loop plus duplicate-id set.
- No path reads `execution_journal.event_json`, no deserialize→replay→compare-to-`load`, no blocked/wait/fail families, no"same commands"/outbox equality (HERMES-PROMOTION-032 text in ADR-0013 ~lines 412-418).
- Single happy path Created→Ready→Started→Succeeded only.

**Counter-argument:** HERMES-PROMOTION-065 asks for “reducer replay tests”; unit equality of reducer vs wrapper is a reducer test.
**Does counter win?** No against “same definition, version, and history → same state and commands” and against exit criterion “reducer replay … pass” as a gate for kernel durability. History authority is the journal; test never touches it.

---

### F-007 — MAJOR
**Claim:** Named crash-boundary test does not exercise a crash after durable partial write; it exercises SQLite `RAISE(ABORT)` mid-transaction, which rolls the whole UoW back — vacuously proving BEGIN/COMMIT error handling, not crash-boundary durability.

**Evidence:**
- Trigger ABORT before outbox insert: `tests/resilience/test_execution_sqlite_crash_boundary.py:49-58`.
- Assert prior state remains CORPORATION proposed@1 and failed event absent: `:72-98`.
- Production write order single transaction: `execution_store.py:225-357` (`BEGIN IMMEDIATE` … state … journal … outbox … `COMMIT`); exception path ROLLBACK `:359-362`.
- No process kill, no SIGKILL, no injection between COMMIT of one relation and another under autocommit, no power-loss/fault-injection, no separate connections splitting writes.
- Name: `test_failure_between_journal_and_outbox_leaves_no_partial_state` (`:31`) — between journal and outbox inside one open tx, ABORT undoes journal write too; there is no “between” durable state.

**Counter-argument:** For SQLite X transaction semantics, ABORT is a legitimate atomicity probe; FULL synchronous (`execution_store.py:197`) covers durability class.
**Does counter win?** No for claim “crash-boundary.” Atomic rollback on error ⊆ crash testing; HERMES-PROMOTION-065 couples crash-boundary with replay as exit gate.

---

### F-008 — MAJOR
**Claim:** `Execution` aggregate state is constructible and loadable without ever passing through the pure reducer, including illegal (status, version) pairs the reducer cannot emit.

**Evidence:**
- Public frozen dataclass: `execution.py:52-62` — no private constructor / factory-only discipline.
- Document hydration path: `execution_store.py:83-125` + `:390-420` — builds `Execution(...)` from JSON; no transition legality check, no force that version==1⇔PROPOSED, SUCCEEDED only from RUNNING, etc.
- Demo: `Execution(..., status=SUCCEEDED, version=1, ...)` constructs; after SQL forge `load` returns SUCCEEDED@99 without journal history.
- Store write path does use reducer (`execution_store.py:238`) — for branches retinuded through `append` only.

**Counter-argument:** Production writers always go through `append`→`reduce_execution`; tests/helpers constructing `Execution` are an irrelevance.
**Does counter win?** No as system property. Readable authority (`load`) + type surface admits state the reducer cannot reach → HERMES-PROMOTION-059/022 spirit (“only execution kernel chooses legal next state”) fails for reconstructed state.

---

### F-009 — MINOR
**Claim:** PEP path enumeration leaves a RT hole for allow without explicit policy grant when a custom `ApplicationControlPolicy` returns a well-formed PASS `GateEvaluation` (adapter is fully trusted beyond exception wrapping).

**Evidence:**
- Exception → deny: `application_control_pep.py:39-40`.
- Non-`GateEvaluation` → deny: `:42-43`.
- Allow only after domain facts: `:45-52` / `application_control.py:65-77`.
- Demo Rogue adapter returning fresh PASS tied to request_id → `permitted=True` with zero evidence and blank catalog action vocabulary.

**Counter-argument:** By hexagonal design the PDP is the grantor; PEP fail-closed class is error/unavailable/malformed, not “re-implement policy.” Tests inject Raising/Malformed adapters (`tests/security/test_application_control_pep.py:93-120`).
**Does counter win?** Mostly for “malicious PDP” class (policy adapter is TCB). Retained as MINOR residual: PEP is marketed fail-closed application-control but is a thin boolean projector; any bug in adapter is automatically an allow orifice if it emits PASS. Complements F-004.

---

### F-010 — MINOR  
**Claim:** Append-only journal holds full `resulting_state_json` per event (`execution_store.py:301-327`, schema `001_execution_kernel.sql:21`), so any SQL/reader of the DB observes journal-derived state parallel to the snapshot — with no API or test ensuring agreement (feeds F-001 observer model).

**Evidence:** columns written `:325`; no public repository method exposes journal, but raw DB and simple `SELECT` are available (integration tests already query journal: `tests/integration/governed_execution/test_sqlite_execution_store.py:102-108`).

**Counter-argument:** Journal is audit oracle by design (Ground Zero:473); presence of `resulting_state_json` is intentional, not a bug.
**Does counter win?** On presence, yes. Retained only as contributing evidence that dual records can diverge undetected (paired with F-001).

---

### F-011 — MINOR
**Claim:** HERMES-OWNER-DECISION-020 remains `owner_decision_ref: null` / `activation_without_decision: DENIED` while the tree ships Execution event journal + `replay_execution` + migration tests — i.e. event-log machinery exists without the accepted owner decision artifact that qualifies ES activation.

**Evidence:**
- ADR-0013 owner row: `docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:979-990`.
- Journal write path: `execution_store.py:301-327`.
- Replay helper:.require_execution.py{:226-237}.
- No ADR accepting OWNER-020 located in this audit pass.

**Counter-argument:** This is dual-write snapshot+audit (research “mature default”), not activated ES, because `load` never replays; OWNER-020 blocks activation only. Tracer declares no `IMPLEMENTATION_START_READY`.
**Does counter win?** Yes for runtime ES-activation claim. Residual MINOR: look-alike ES surface without the predeclared acceptance test named by the owner decision row — documentation hygiene / audit risk, not proven illicit activation.

---

## Dissolved

### D-001 — Reducer purity of `reduce_execution` (HERMES-PROMOTION-059/031)
**Examined:** `execution.py:99-223`, transitions via `dataclasses.replace` (`:80-87`); imports only identity/events/status; no time/random/I/O/globals. `replay_execution` local `set` only (`:229-234`). Event timestamp validation in `events.py:20-29` parses supplied strings; does not call wall clock. Unit proof non-mutation: `tests/unit/governed_execution/domain/test_execution.py:88-100`.
**Attack failed:** no path demonstrated hidden I/O, wall-clock dependence, input mutation, or nondeterminism across equal inputs.
**Exception partial-state:** invalid transitions raise before replace (`:78-79`); frozen inputs unchanged (`test_execution.py:140-159`).
**Notekept out of Findings:** purity of reducer holds; reachable state outside reducer (F-008) is a different surface.

### D-002 — PEP exception / malformed / subject-mismatch fail-closed paths
**Examined:** adapter exception `:39-40`; malformed type `:42-43`; subject mismatch via `request_bound` `:48` + `application_control.py:71-72`; fail outcomes `:73-74`; PASS with reasons denied `:75-76`.
**Unknown action / missing project:** `GateCatalog.gate_for` / `require_project` raise (`policy/domain/gates.py:91-100`) → adapter exception → deny.
**Tests:** `tests/security/test_application_control_pep.py:103-150`.
**Dissolved as blanket “PEP never fails closed.”** Residual gaps remain F-004/F-005/F-009.


### D-003 — One-SQLite-unit-of-work for honest `append` happy path
**Examined:** single connection, `BEGIN IMMEDIATE`…state+journal+outbox…`COMMIT` (`execution_store.py:223-364`); FK outbox→journal (`001_execution_kernel.sql:42-43`); integration test commits all three (`test_sqlite_execution_store.py:79-145`).
**Honest concurrent CAS:** one winner (`test_sqlite_execution_store.py:230-250`).
**Dissolved** as structural multi-statement split under normal `appкend`. Crash-naming defect remains F-007; mismatch remain F-001.

### D-004 — isolation_level=None autocommit “implicit multi-tx fingers”
**Examined:** `execution_store.py:190-198` uses explicit `BEGIN IMMEDIATE` on append; writers not relying on sqlite3 implicit DML begin. Mid-functionality autocommit windows not shown for `append`.
**Dissolveded** for append UoW. `load`/`count_*` are separate read connections (by design).

---

## Inferences

1. **Inference:** The session quote about snapshot-as-canonical-authority is a lab/process gloss, not a line-bound decision. **Evidence prompting:** search miss + Ground Zero 8.3 dual model (F-003).
2. **Inference:** BINARY authors intended snapshot load for latency and journal for audit/replay later; mismatch detection was deferred. **Evidence:** load-only snapshot, journal stores `resulting_state_json`/`sha256` prepared for future check unused (F-001/F-010).
3. **Inference:** Crash test was written to satisfy HERMES-PROMOTION-065 naming without OS-level fault injection harness. **Evidence:** RAISE(ABORT) pattern vs name (F-007).
4. **Inference:** Replay test was written to seal the pure-function loop quickly, not journal equivalence. **Evidence委員 tautological structure (F-006).
5. **Inference:** `catalog_digest` is a forward-compat field for composition roots that do notyet exist in this tree. **Evidence:** no caller hashing catalog; only format guard (F-005).
6. **Inference:** `GateEvaluation` PASS+missing_claim_ids is an oversight in `__post_init__`,Not intentional allow. **Evidence:**  controller never emits it; post_init locks other PASS invariants but ignores missing (F-004).
7.남의**Inference:** Direct `Execution(...)` construction surviving load is accepted R&D pragmatism, not intended alternate authority pathival. **Evidence:** only store writers call reducer (F-008).
8. **Inference:** OWNER-020 remains deliberately open; journal is dual-write audit, not activated ES load path. **Evidence:** D-003/F-011 counter material; ADR status null.

---

## Coverage

| Surface | Examined (files; lines or ranges) | Result |
|---|---|---|
| Reducer purity | entity`execution.py` 1-237; `events.py` 1-197; `status.py` 1-23; unit `test_execution.py` 1-318 | No purity defect; Related F-008 |
| PEP fail-closed |t `application_control_pep.py` 1-53; `application_control.py` 1-77; `deterministic.py` 1-47; `gate_controller.py` 1-222; `assurance/domain/gates.py` 1-114; `policy/domain/gates.py` 1-101; `test_application_control_pep.py` 1-158; `test_application_control.py` 1-64 | F-004, F-005, F-009; D-002 |
| State authority | `execution_store.py` 1-420;, migration SQL 1-case73; `execution_repository.py` 1-17; docs Ground Zero 470-476; research ~2025; ADR-0013 670-749 & 979-990; review 172; integration/migration/resilience tests as cited | F-001, F-002, F-003, F-008, F-010, F-011; D-003, D-004傾斜 |
| Replayitele tests | `testऽ_execution_replay.py` 1-66; `replay_execution` 226-237 | F-006 |
| Crash-boundary tests | `test_execution_sqlite_crash_boundary.py` 1-98; append_tx 223-364 | F-007 |
| HERMES-PROMOTION-058 | `foundation/identity.py`, `foundation/canonical.py` + unit tests | Present; no separate finding |
| HERMES-PROMOTION-064 | `tests/architecture/test_kernel_imports.py` 1-483 | Present; no hermes import in kernel graph test |
| HERMES-PROMOTION-065 exit couple |replay+预 crash+import | Forms incomplete: F-006+F-007 weaken exit proof; import side holds |
| Suite run | `uv run pytest tests/replay tests/resilience tests/security/test_application_control_pep.py tests/unit/governed_execution tests/integration/governed_execution` → 38 passed | Passing suite does not refute F-* (tests skip the defects) |
