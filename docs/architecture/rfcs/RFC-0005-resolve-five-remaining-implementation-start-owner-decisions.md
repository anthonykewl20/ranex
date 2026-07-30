# RFC-0005: Resolve the Five Remaining Implementation-Start Owner Decisions

| Field | Value |
|---|---|
| Status | ACCEPTED |
| Owner | Human owner |
| Authors | Assistant, from Codex research, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; resolves `HERMES-OWNER-DECISION-003`, `-013`, `-017`, `-019`, `-020` |
| Affected contexts | `governed_execution`, `work_management`, `assurance`, `policy`, `module_governance`, `compatibility`, `migration`, `delivery` |
| Supersedes | Nothing. Fills five registered gaps that block `IMPLEMENTATION_START` |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md` owner-decision rows |

## Decision question

Six owner decisions block `IMPLEMENTATION_START`. `RFC-0004` resolves
`HERMES-OWNER-DECISION-001`. This RFC recommends an answer to the other five.
Each has no default, an absence outcome of `BLOCK`, and requires an accepted ADR
with predeclared acceptance tests.

They are grouped in one document deliberately: four of the five are the same
question asked about different subjects — **what is authoritative, and what is a
rebuildable view of it?** — and answering them separately would obscure that.

---

## 1. `HERMES-OWNER-DECISION-003` — transaction ownership

**In plain terms:** which writes must succeed or fail together as one unit?

### Recommendation

**One Governed Execution SQLite transaction atomically writes the Execution
aggregate's current state and version, its ordered transition/audit journal
entry, and the outbox intent.** Evidence, permits, and work projections are
*not* inside that boundary; they are bound by immutable reference and
reconciled, never co-written.

### Why

This is already the accepted obligation — `HERMES-PROMOTION-061` requires the
journal and outbox to be persisted with canonical state and version through one
SQLite unit of work, and the kernel implements it. The decision confirms the
boundary rather than inventing one, and confirms what sits *outside* it, which was
the genuinely undecided part.

### Cost

Cross-context consistency becomes eventual and reconciliation becomes mandatory
rather than optional. A crash between the unit of work and a downstream
projection leaves the projection stale until reconciled — which is why
`OUTCOME_UNKNOWN` must remain a first-class result.

### Acceptance tests

A transition writes state, journal, and outbox atomically or not at all — already
covered by the process-kill crash tests added 2026-07-30. Evidence or permit
records written inside the execution transaction fail review.

---

## 2. `HERMES-OWNER-DECISION-013` — Kanban authority

**In plain terms:** is your board the truth, or a picture of the truth?

### Recommendation

**Kanban is a disposable, rebuildable projection of canonical `WorkItemStatus`,
owned by `work_management`.** Selected Kanban tables must not be adapted into a
second authority. A drag or board action is a *command request*; it succeeds only
if the canonical legal transition succeeds.

### Why

The Core SDLC already states that boards and dashboards are projections, never
completion authorities. Adapting tables behind work management would create two
places where "done" lives, and the first disagreement between them would be
unresolvable. This also settles the same question for the owner's run-graph
visualization, which is a projection by the same rule.

### Cost

The board cannot be edited offline or used as a scratchpad. Every board action
must round-trip through the transition rules and can be rejected — which will
sometimes feel slower than dragging a card.

### Acceptance tests

Deleting the entire Kanban projection and rebuilding it from canonical state
produces an identical board. A board action that would violate a legal transition
is rejected rather than applied optimistically.

---

## 3. `HERMES-OWNER-DECISION-017` — Electron and desktop applications

**In plain terms:** does the desktop app survive?

### Recommendation

**No. Remove and keep excluded all Electron and desktop bootstrap, packaging,
updater, and desktop-only surfaces. Retain the local web and TUI paths only.**

### Why

Verified: `DEC-RANEX-020` in `ADR-0006` already records `name: "desktop-app"`,
`selected: "excluded"`, owned by the product owner. **The substantive decision was
already made.** The remaining work is administrative — binding this owner-decision
row to `ADR-0006` and the exclusion fitness function so the registry stops
reporting an open question that is in fact closed.

This is the cheapest of the six: no new choice, only bookkeeping.

### Cost

None beyond what `ADR-0006` already accepted. Note that a Tauri desktop bootstrap
installer currently exists in an ignored worktree
(`.claude/worktrees/phase-1-adopt-upstream`), which is inherited material on an
excluded surface. It is quarantined and violates no rule, but it should not
migrate into the tracked tree.

### Acceptance tests

No tracked path contains an Electron or desktop packaging surface. The exclusion
fitness function reports `DEC-RANEX-020` as satisfied, and the owner-decision row
resolves to the existing ADR rather than remaining `null`.

---

## 4. `HERMES-OWNER-DECISION-019` — one execution context or several

**In plain terms:** are execution, gates, permits, and effects one system or four?

### Recommendation

**One strong-consistency Governed Execution bounded context, with execution, gate
binding, grant/permit handling, and effect intent/reconciliation as separate
submodules sharing one persistence authority.** They may have separate domain
files and types; they may not be independently persistent authority contexts.
`assurance` and `policy` remain external contexts whose immutable results
Governed Execution binds by reference.

### Why

Splitting them into independently persistent contexts would put a network or
transaction boundary between deciding that something is permitted and recording
that it happened — precisely where atomicity is required. Decision 003's single
unit of work is only expressible if these share one persistence authority.

### Cost

Governed Execution becomes the largest context and cannot be scaled or deployed
piecewise. That is acceptable while Ranex is a single-host system; it would need
revisiting if that ever changes.

### Acceptance tests

No submodule persists authority independently of the shared boundary. Import
tests confirm `assurance` and `policy` remain external and are consumed only by
immutable reference.

---

## 5. `HERMES-OWNER-DECISION-020` — activate event sourcing?

**In plain terms:** should the event journal become the single source of truth?

### Recommendation

**No — do not activate event sourcing for the Execution aggregate now.** Retain
the accepted hybrid: relational current state and version as the operational read
source, the append-only ordered journal as the replay and audit oracle, atomic
journal/state/outbox writes, and mandatory snapshot-journal agreement checks.

### Why, and a correction to my own earlier framing

I said earlier today that the rewritten replay and crash tests might *unblock*
activating event sourcing. Codex's assessment, which I accept, is that they
strengthen the **hybrid** rather than justify a switch. The row conditions
activation on tests that *justify that choice*; tests proving the journal is a
faithful oracle demonstrate the hybrid works — they do not demonstrate that
making the journal the sole write model would be better.

The journal remains required. It is simply not yet the sole authoritative write
model, and nothing in the corpus argues it should be.

### Cost

Ranex keeps two representations of state and must keep proving they agree — which
is exactly what §8.3 and the mismatch gate now enforce. The purity of a
single-write-model design is forgone.

### Acceptance tests

The snapshot-journal agreement gate blocks on any mismatch — implemented and
tested 2026-07-30. Replay from persisted journal bytes reproduces the snapshot.
No module other than `Execution` gains event-sourcing behaviour, and this decision
authorizes none.

---

## The through-line

Four of these five say the same thing about different subjects: **one thing is
authoritative, everything else is a rebuildable view, and the two must be provably
in agreement.** Kanban is a view of work state. The run-graph is a view of
execution state. The snapshot is a view the journal can rebuild. Gates and permits
share one authority rather than holding their own.

That is already your architecture's central idea. These decisions record it in the
places where it was left open.

## Human decision requested

Five answers. Each can be accepted, amended, or rejected independently.

1. **`-003`** — accept the single execution transaction boundary, with evidence,
   permits, and projections outside it and reconciled?
2. **`-013`** — accept Kanban as a rebuildable projection, never a second
   authority?
3. **`-017`** — confirm desktop stays excluded and bind this row to `DEC-RANEX-020`?
   *(Recommended first: it is already decided and costs nothing.)*
4. **`-019`** — accept one strong-consistency Governed Execution context with
   submodules?
5. **`-020`** — accept keeping the hybrid and **not** activating event sourcing?

Accepting all five, plus `RFC-0004`, clears every owner decision blocking
`IMPLEMENTATION_START`. The remaining blockers after that are not decisions but
work: closing the review-schema defects, and configuring the type checker
`ADR-0014` requires.
