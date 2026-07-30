# Kernel R&D tracer — adversarial audit, three independent models

| Field | Value |
|---|---|
| Review ID | `REV-KERNEL-TRACER-001` |
| Date | 2026-07-30 |
| Subject | Branch `feature/kernel-tracer`, worktree `.claude/worktrees/kernel-tracer`, untracked `src/` and `tests/` |
| Evidence status | Advisory cross-model review; no transition authority, no readiness claim |
| Reviewers | `openrouter/tencent/hy3` (variant high), Codex `gpt-5.6-sol`, `openrouter/x-ai/grok-4.5` (default effort) |
| Briefs | Identical brief to HY3 and Grok; a code-review-framed brief to Codex |
| Raw artifacts | [`artifacts/2026-07-30/agent-reports/`](artifacts/2026-07-30/agent-reports/) — `kernel-hy3.md`, `kernel-codex.md`, `grok-kernel.md` |
| Repository mutations by reviewers | None; all runs read-only |
| Standing constraint | `IMPLEMENTATION_START_READY` is not declared. This code is an R&D tracer claiming no authority. Findings are against the code, never grounds to relax a check |

## Why three models

The prior capability probe recorded that reviewer disagreement is more
informative than reviewer consensus, provided it is resolvable. That held here:
the most consequential result of this audit is a **correction of one reviewer by
another**, and it changes what the fix is.

## The correction that matters most

**HY3's blocking finding was wrong, and Codex and the orchestrator shared its
error.**

HY3 reported as a BLOCKER that the state-authority principle — *"the relational
snapshot, not journal replay, is canonical state authority"* — is declared nowhere
in the corpus, and therefore an undeclared inference enacted silently by code.
Codex did not contradict it. The orchestrator searched independently and also
found nothing. Three readers, plus the prior session that produced the phrase,
all concluded absence.

Grok found it. `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md`
§8.3, verified verbatim:

> - The current row is the operational read source.
> - The ordered journal is the replay and audit oracle.
> - Snapshots may accelerate replay but never replace the journal.
> - A current-row/journal mismatch is corruption and blocks advancement; code
>   does not choose whichever source is convenient.

Three consequences:

1. **The architecture declares a dual model, not snapshot supremacy.** The
   session phrase is not merely undeclared — its "snapshot is canonical
   authority" reading is *contrary* to a declared obligation that snapshots never
   replace the journal.
2. **The defect is a violation, not an omission.** The kernel implements the
   first bullet and omits the fourth entirely. There is no mismatch detection
   anywhere in the read path.
3. **The fix changes completely.** "Write the principle down" was the wrong
   remedy. The right one is to implement the blocking mismatch gate §8.3 already
   requires.

The four earlier searches failed because their terms matched the session phrasing
("canonical state authority", "journal replay") rather than §8.3's own wording
("current row", "operational read source"). A negative search result is evidence
about the search, not about the corpus.

## Confirmed findings

Each reproduced by the orchestrator at the cited lines before being recorded.

### 1. No mismatch detection in the authority read path — violates §8.3

`load()` selects only from `execution_state`
(`execution_store.py:210-221`). `_decode_state_row` checks row-internal
consistency only — canonical form, and the `version`/`last_event_id`/`execution_id`
columns against the JSON document (`:398-419`). Journal chain continuity is
enforced by no Python code and no SQL constraint: the migration checks
`resulting_version = previous_version + 1` and digest *lengths*
(`001_execution_kernel.sql:11-33`), and `UNIQUE (execution_id, resulting_version)`
does not require a new `previous_version` to equal the current chain head. The
only journal readers in `src/` are row counters (`:366-382`); no event decoder
exists anywhere.

**Grok executed the exploit rather than inferring it.** After two honest appends
reaching `READY` at version 2, direct SQL rewrote `canonical_state_json` to
`PROPOSED` while keeping version and `last_event_id` internally consistent;
`load()` returned `PROPOSED`. A further forge to `SUCCEEDED` at version 99 with an
invented event ID was likewise returned. The store's advertised tamper detection
catches only internally *inconsistent* forgeries, which is the half its tests
cover (`test_sqlite_execution_store.py:174-189`, `:192-227`).

### 2. Authorization is bound to the request by identifier alone

`ApplicationControlPEP.decide` consumes only `well_formed`, `request_bound`,
`gate_passed`, `gate_authorized`, and `reason_codes`
(`application_control_pep.py:42-52`), where `request_bound` is
`evaluation.request_id == request.request_id` (`:48`). It never cross-checks
`gate_id`, action, `policy_digest`, `catalog_digest`, or `evidence_digest`, though
it holds the evidence tuple it forwarded and could recompute the digest exactly as
`gate_controller.py:73-77` does.

**Codex sharpened this decisively:** `GateEvaluation.__post_init__` forbids PASS
with reason codes and ties `authorized` to PASS (`assurance/domain/gates.py:97-100`)
but **never requires `missing_claim_ids` to be empty on PASS**. So a `PASS` that
simultaneously reports missing critical claims is constructible, and the PEP
discards that field — yielding `permitted=True`. Verified: the field exists at
`gates.py:85` and appears nowhere in the PEP's fact construction.

### 3. The two Phase 1 exit-criterion tests do not test what their names claim

**Replay.** `test_execution_replay.py:59-66` builds `direct` by folding
`reduce_execution` over in-memory events and compares it to
`replay_execution(events)` — which is that same fold (`execution.py:226-237`). The
production reducer is compared with itself. No path reads
`execution_journal.event_json`; no serialization round-trip; only the happy path
`PROPOSED→READY→RUNNING→SUCCEEDED`; and no "same commands" comparison though
`HERMES-PROMOTION-032` requires it.

**Crash boundary.** `test_execution_sqlite_crash_boundary.py:50-59` installs a
SQLite `RAISE(ABORT)` trigger. The resulting exception is caught and rolled back
by the store's own handler (`execution_store.py:359-362`) — the path a real crash
would never execute. No process dies, no fsync or torn-write scenario, and no
`PRAGMA journal_mode` is ever set, so recovery behaviour depends on an unpinned
SQLite default.

### 4. Confirmed sound: the reducer is pure

Attacked by all three reviewers and dissolved with evidence by two.
`execution.py` imports only `dataclasses`, `collections.abc`, and sibling domain
modules; timestamps come exclusively from `event.occurred_at`; new state is built
by `replace()` on frozen inputs so an exception can leave no partial state;
`frozenset`s are used for membership only, never iterated into output. The
architecture test independently bans effectful imports and calls in domain code
(`test_kernel_imports.py:18-52`). **No reviewer invented a defect here**, which was
one of the graded expectations of this audit.

### 5. Lesser confirmed findings

- `catalog_digest` is accepted on format alone and never bound to catalog bytes
  (`policy/adapters/configuration/.../deterministic.py:27-30`), then forwarded into
  every evaluation. Tests normalize a digest of nothing.
- `_execution_from_document` reconstructs state without cross-field invariants
  (`execution_store.py:83-125`), so a persisted `BLOCKED` with a null
  `blocked_from_status` loads cleanly and steers which `ExecutionUnblocked` the
  reducer will later accept.
- `int(row["version"])` silently coerces (`:408`): a relational `1.5` reads as
  version 1; `'abc'` leaks a raw `ValueError` rather than the store's own
  integrity error.
- The database is world-readable for a window at creation — `chmod(0o600)` runs
  after migration and close (`:200-208`) — while `hash_chain_ledger.py:145-146`
  demonstrates the correct `touch(mode=0o600)`-first pattern.
- The evidence ledger derives both its starting point and expected history from
  the local file (`hash_chain_ledger.py:65-80`), so wholesale replacement or
  truncation recomputes as valid. It detects edits, not substitution.

## Claims that did not survive

- **HY3 F1 (BLOCKER)** — "declared nowhere." Disproved above.
- **Codex finding 9 (BLOCKER)** — malformed evidence reaching a decision via
  `exit_code=False` and `artifact_verified="yes"`. `EvidenceRecord.__post_init__`
  already rejects both by type (`gates.py:66-76`). Survives only for duck-typed
  impostors bypassing the dataclass; real, but not blocking.
- Six further claims were self-dissolved by HY3 with evidence, including
  snapshot-column normalization and outbox dispatch state, both correctly
  identified as out of Phase 1 scope.

## What production practice says the fix is

From the prior-art sweep (`artifacts/2026-07-30/agent-reports/priorart-B.md`),
four controls make a snapshot and a journal provably agree. **Ranex has one.**

| Control | Present |
|---|---|
| The journal is the recovery authority; the snapshot is a rebuildable cache | No |
| The snapshot names the exact journal position it represents — Temporal stores the latest history event ID and treats mutable state as valid only when reflected in history | No |
| Events and the synchronous projection commit atomically | **Yes** |
| Verify-or-rebuild: replay from original event bytes must reproduce the snapshot | No |

And the load-bearing caution: atomicity is not integrity. One transaction proves
all three writes committed or none did; it cannot prove the snapshot was computed
from the journal event it names. A shared implementation bug can atomically commit
mutually inconsistent data.

For crash testing, SQLite's own documented methodology applies: a parent creates a
durable database, a separate **child process** performs the transition, the parent
kills the child at systematically varied write and commit points, a fresh process
reopens the real file, runs `PRAGMA integrity_check`, and accepts only
complete-old or complete-new state — never a mixture.

## Disposition

No code is changed by this review. The confirmed findings become work items:
implement the §8.3 mismatch gate, bind authorization to more than a reusable
identifier, and replace both exit-criterion tests with ones that can fail. None of
this authorizes product code, and `IMPLEMENTATION_START_READY` remains
`NOT_ASSESSED`.

## Method notes

- Grok ran at **default** reasoning effort while every HY3 run used `high`, so the
  comparison was tilted against the model that performed best.
- Briefs deliberately withheld the orchestrator's own hypotheses. Of three
  withheld, one was independently found, one was found in a different and more
  serious form, and one was not surfaced.
- Report length did not track quality: the shortest report (36 KB) missed none of
  the longest report's (93 KB) findings and added the §8.3 discovery plus an
  executed exploit.
