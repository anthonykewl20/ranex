# ADR-0016: Resolve Five Implementation-Start Owner Decisions

| Field | Value |
|---|---|
| ADR ID | `ADR-0016` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-30 |
| Effective revision | Working tree based on `97c4c5ecf`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `governed_execution`, `work_management`, `assurance`, `policy`, `module_governance`, `compatibility`, `migration`, `delivery` |
| RFC | [`RFC-0005`](../rfcs/RFC-0005-resolve-five-remaining-implementation-start-owner-decisions.md), accepted by the human owner on 2026-07-30 |
| Supersedes | Nothing. Resolves `HERMES-OWNER-DECISION-003`, `-013`, `-017`, `-019`, and `-020`, previously unresolved and blocking |
| Review/expiry date | Review on any change to the single-host assumption, the state/journal model, or the excluded desktop surface |
| Compatibility/migration class | Additive authority and boundary declarations; no existing artifact changes meaning |
| Security/data class | Public architecture decision |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-30 | Initial accepted decision, promoted from `RFC-0005`. Resolves five owner decisions that blocked `IMPLEMENTATION_START`. |

## Context

Five `OWNER_DECISION_REQUIRED` rows in `ADR-0013` blocked `IMPLEMENTATION_START`,
each with no default and an absence outcome of `BLOCK`. Four of the five are the
same question about different subjects: **what is authoritative, and what is a
rebuildable view of it?**

## Decision

### `EXEC-TXN-001` — resolves `HERMES-OWNER-DECISION-003`

One Governed Execution SQLite transaction atomically writes the Execution
aggregate's current state and version, its ordered transition and audit journal
entry, and the outbox intent. Evidence records, permits, and work projections are
outside that boundary; they are bound by immutable reference and reconciled, never
co-written.

This confirms the boundary `HERMES-PROMOTION-061` already requires and settles
what sits outside it, which was the undecided part. Cross-context consistency is
therefore eventual and reconciliation is mandatory, which is why `OUTCOME_UNKNOWN`
remains a first-class result.

### `KANBAN-PROJECTION-001` — resolves `HERMES-OWNER-DECISION-013`

Kanban is a disposable, rebuildable projection of canonical `WorkItemStatus` owned
by `work_management`. Selected Kanban tables are not adapted into a second
authority. A board action is a command request that succeeds only if the canonical
legal transition succeeds.

The Core SDLC already holds that boards and dashboards are projections, never
completion authorities. Two places recording "done" would make the first
disagreement unresolvable. The same rule governs the run-graph visualization.

The board cannot be edited offline or used as a scratchpad; every action
round-trips through the transition rules and may be rejected.

### `DESKTOP-EXCLUDED-001` — resolves `HERMES-OWNER-DECISION-017`

Electron and desktop bootstrap, packaging, updater, and desktop-only surfaces are
removed and remain excluded. Only the local web and TUI paths are retained.

The substantive decision was already made: `DEC-RANEX-020` in `ADR-0006` records
`name: "desktop-app"`, `selected: "excluded"`, owned by the product owner. This
row was administrative rather than a new choice, and binds to that decision.

A Tauri desktop bootstrap installer exists in the ignored worktree
`.claude/worktrees/phase-1-adopt-upstream`. It is inherited material on an excluded
surface, quarantined by `.gitignore` and `ADR-0007`, violating no rule. It must not
migrate into the tracked tree.

### `EXEC-CONTEXT-001` — resolves `HERMES-OWNER-DECISION-019`

Execution, gate binding, grant and permit handling, and effect intent and
reconciliation are separate submodules of one strong-consistency Governed
Execution bounded context sharing one persistence authority. They may have
separate domain files and types; they are not independently persistent authority
contexts. `assurance` and `policy` remain external contexts whose immutable
results Governed Execution binds by reference.

Independently persistent contexts would place a boundary between deciding that
something is permitted and recording that it happened — exactly where atomicity is
required. `EXEC-TXN-001` is only expressible if these share one persistence
authority.

Governed Execution therefore cannot be scaled or deployed piecewise. That is
accepted while Ranex is single-host and must be revisited if that changes.

### `EXEC-HYBRID-001` — resolves `HERMES-OWNER-DECISION-020`

Event sourcing is **not** activated for the Execution aggregate. The accepted
hybrid is retained: relational current state and version as the operational read
source, the append-only ordered journal as the replay and audit oracle, atomic
journal, state, and outbox writes, and mandatory snapshot-journal agreement
checks.

The row conditions activation on replay and migration tests that *justify that
choice*. The tests rewritten on 2026-07-30 — replaying persisted journal bytes and
killing a real process at three commit points — demonstrate that the journal is a
faithful oracle and therefore that the hybrid works. They do not demonstrate that
making the journal the sole write model would be better. An earlier assistant
claim that these tests unblocked *activation* was incorrect and is recorded as
such in `RFC-0005`.

Ranex consequently keeps two representations of state and must keep proving they
agree, which §8.3 and the mismatch gate now enforce. The simplicity of a single
write model is forgone. This decision authorizes event sourcing for no other
module.

## Predeclared acceptance tests

1. A transition writes state, journal, and outbox atomically or not at all —
   already exercised by the process-kill crash tests.
2. An evidence or permit record written inside the execution transaction fails
   review.
3. Deleting the entire Kanban projection and rebuilding it from canonical state
   produces an identical board.
4. A board action that would violate a legal transition is rejected rather than
   applied optimistically.
5. No tracked path contains an Electron or desktop packaging surface, and the
   exclusion fitness function reports `DEC-RANEX-020` satisfied.
6. No Governed Execution submodule persists authority independently of the shared
   boundary; import tests confirm `assurance` and `policy` remain external and are
   consumed only by immutable reference.
7. The snapshot-journal agreement gate blocks on any mismatch, and replay from
   persisted journal bytes reproduces the snapshot.
8. No module other than `Execution` gains event-sourcing behaviour.

## Consequences and evidence standing

Tests 1 and 7 are satisfied today by the kernel R&D tracer, which claims no
authority. Tests 3, 4, and 6 cannot be satisfied yet because no Kanban projection
and no composition root exist. Test 5 is satisfiable now and is the cheapest
remaining action. That distribution is a stated gap, not a claim of compliance.

`IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`.

## Human approval

The human owner accepted `RFC-0005` on 2026-07-30, stating acceptance of all six
recommended owner decisions. The acceptance covers `EXEC-TXN-001`,
`KANBAN-PROJECTION-001`, `DESKTOP-EXCLUDED-001`, `EXEC-CONTEXT-001`, and
`EXEC-HYBRID-001` together with the costs recorded above. It authorizes no product
code and declares no readiness tier.
