# RFC-0004: Canonical Workflow and Event Schema, and Upcaster Policy

| Field | Value |
|---|---|
| Status | ACCEPTED |
| Owner | Human owner |
| Authors | Assistant, from Codex research, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; resolves `HERMES-OWNER-DECISION-001` |
| Affected contexts | `governed_execution`, `work_management`, `assurance`, `policy`, `compatibility`, `migration`, `module_governance` |
| Supersedes | Nothing. Fills a registered gap that currently blocks `IMPLEMENTATION_START` |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:823-834` |

## Decision question

`HERMES-OWNER-DECISION-001` reserves to the owner: *"Canonical Ranex workflow and
event schema and upcaster policy."* It has **no default**, its absence outcome is
`BLOCK`, activation without decision is `DENIED`, and it blocks
`IMPLEMENTATION_START`. It requires an accepted ADR with predeclared acceptance
tests.

In plain terms: **what is a workflow made of, what does a recorded event look
like, and how may either change without breaking runs already recorded in the old
format?**

## Why this is answerable now rather than an open research question

The corpus already classifies this as **"MATURE PATTERN / R&D schema"**
(`docs/research/hermes-core-architecture-research-2026-07-27.md:786`) and names
the five required properties: immutable definitions, interpreter version,
event-schema version, upcaster compatibility, and replay checks. Line 2023-2024
adds "pin interpreter/event versions; test upcasters against frozen old
histories." The pattern is settled in production systems; only the concrete form
was undecided. This RFC therefore recommends one form rather than surveying
options.

## Context and evidence

### Facts

1. **Measured, this repository.** The kernel has no workflow definition at all.
   `Execution` carries `workflow_request_ref: str` — an opaque string
   (`.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:57`).
   There is no node identity, no interpreter pin, and no event-schema pin.
2. **Measured, this repository.** A domain event envelope schema already exists,
   `schemas/events/domain-event-envelope-v1.schema.json`, and already carries
   `event_version`, `event_name`, `aggregate_version`,
   `aggregate_event_sequence`, `correlation_id`, `causation_id`, `digest`, and
   `data_classification`. The recommendation reuses it unchanged rather than
   introducing a competing envelope.
3. **Measured, this repository.** §8.3 of
   `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:474` states "Snapshots may
   accelerate replay but never replace the journal," and `:475` that a
   current-row/journal mismatch is corruption that blocks advancement. As of
   2026-07-30 the kernel enforces this on every read.
4. **Measured, this repository.** Replay now decodes persisted journal bytes and
   verifies each step's digest, and crash recovery is exercised by `SIGKILL`ing a
   real child process at three commit points
   (`.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_journal_replay.py`,
   `tests/resilience/test_execution_crash_recovery.py`). This matters because
   `HERMES-OWNER-DECISION-020` conditions event sourcing on exactly such tests.
5. **Verified externally.** Temporal pins workflow versioning and replay safety;
   Axon uses upcasters for event schema evolution; Marten commits events and
   inline projections in one transaction; Argo restricts changes to submitted
   workflows. Full citations are preserved in the research artifact.

### Assumptions

1. Runs remain replayable for the lifetime of any dependent history. If histories
   were ever discardable, cheaper policies would become available.
2. Ranex continues to treat workflow definitions as immutable approved data that
   a model may draft but not activate. This is already accepted architecture.

### Unknowns

1. How long histories must be retained. This bounds the retention cost below and
   is not decided here.
2. Whether any future aggregate besides `Execution` will need event sourcing.
   `HERMES-OWNER-DECISION-020` governs that separately and this RFC does not
   touch it.

### Conflicts

None found. The conflict audit against `HERMES-PROMOTION-058` through `-065` and
§8.3 is recorded in the research artifact and reports no contradiction: hashing
uses the existing shared-identity and canonical-serialization facilities, the
reducer stays pure because upcasting is a separate pre-reducer stage, the
one-SQLite-unit-of-work boundary is untouched, and unknown or missing
compatibility fails closed.

## Proposed design

### `WF-DEFINITION-001` — A workflow definition is an immutable, content-addressed document

`WorkflowDefinitionV1` is a closed RFC 8785 canonical JSON document carrying: a
stable logical `workflow_definition_id`; an integer `workflow_definition_version`;
a `workflow_interpreter_version` pinned by digest; an `event_contract` naming the
envelope schema version and schema-registry version by digest; input and output
schema references by digest; an entry node key; and a run policy.

Node identity is **derived from the definition digest**, so a node identifier
cannot silently come to mean something else. Any edit — including a cosmetic one —
produces a new version and a new digest. Definitions are never mutated in place.

### `WF-PIN-001` — Every run pins its definition, interpreter, and schema registry

A run records the exact definition version and digest, the interpreter version,
and the schema-registry version it executed under. An active run cannot acquire a
changed topology, a new node meaning, or an interpreter fix by alias movement; it
must drain, block, or be cancelled and re-requested. This is what makes replay
deterministic years later.

### `WF-EVENT-001` — Reuse the existing envelope; version the payload

Persisted events use the existing `domain-event-envelope-v1` unchanged (fact 2),
with `event_version` carrying payload schema version. No competing envelope, no
second serializer.

### `WF-UPCAST-001` — Upcasting on read, with immutable bytes

Compatibility is handled by **upcasting on read**: stored bytes are never
rewritten, and one-to-one adjacent pure functions normalize an old payload version
to the current one *before* the reducer sees it. The reducer therefore consumes
only current normalized events and stays pure. A missing or unknown upcaster is a
blocking integrity failure, never a fallback to "latest."

**Rejected, with the failure each would introduce:**

| Alternative | Why rejected |
|---|---|
| Weak schema / tolerant reader | Ignoring unknown fields or inserting defaults can silently change authority or terminality. A governance kernel cannot guess. |
| Versioned event types only | Permanent `ApplyV1`, `ApplyV2`, … handlers accumulate in the reducer, polluting the one component whose purity is proven and load-bearing. |
| Lazy in-place migration | Rewriting a stored event invalidates its envelope digest, the append-only audit meaning, and every frozen fixture. Directly contradicts §8.3. |
| Copy-and-transform | Produces two histories and a cutover problem. Reserved for a future breaking decision, not ordinary evolution. |

**A deliberate divergence from Temporal:** its patch markers suit code-defined
long-running workflows. Ranex already treats workflows as immutable approved data,
so pinning plus upcasting achieves the same guarantee without embedding version
branches in code.

## Costs — stated, not glossed

- **Retention:** every definition, interpreter build, upcaster, and frozen fixture
  must remain available for the lifetime of dependent histories.
- **Deployment ordering:** a producer cannot emit version `N+1` until every reader
  that might receive it has the registered upcaster.
- **Performance:** old streams pay upcasting cost on every full replay. Snapshots
  reduce frequency but may not replace the journal.
- **No historical corrections:** a wrong fact stays in history; correction means a
  compensating event or a new run.
- **No live change:** an active run cannot pick up a fix. It drains or is
  cancelled.
- **Limited upcasters:** one-to-one functions cannot split, merge, delete, or
  reorder events. Needing that means it is a new event type, not a new version.
- **Operational failure mode:** losing an old interpreter or upcaster is a
  blocking integrity incident, not something recoverable by defaulting.

## Predeclared acceptance tests

1. **Frozen-history replay.** A history recorded under an older payload version
   replays through registered upcasters and reproduces the recorded snapshot
   digest exactly.
2. **Missing upcaster fails closed.** Removing a registered upcaster makes replay
   of an affected history raise an integrity error; it never silently proceeds.
3. **Definition immutability.** Editing an approved definition without a version
   increment fails generation or validation.
4. **Node identity stability.** A node identifier derived from one definition
   digest cannot resolve against a different digest.
5. **Run pin enforcement.** A run whose recorded interpreter or schema-registry
   version does not match the executing one blocks rather than adapting.
6. **Reducer purity preserved.** The reducer contains no version-branching; the
   architecture tests that already ban effectful imports also confirm no upcaster
   logic leaks into the domain.
7. **No relaxation.** Acceptance changes no existing check and declares no
   readiness tier.

## Human decision requested

Codex's assessment, which I verified: **there is no technical selector left inside
this recommendation.** Every element is forced by obligations already accepted.
What genuinely remains yours is whether to accept the operational cost.

> **Do you accept immutable content-addressed workflow definitions with
> digest-derived node identifiers, exact per-run definition/interpreter/schema
> pins, the existing event envelope unchanged, and upcasting-on-read with
> never-rewritten bytes — together with the costs listed above, chiefly that
> histories and their upcasters must be retained indefinitely, running work
> cannot pick up fixes, and history can never be edited?**

A "yes," recorded in an accepted ADR with the tests above, resolves
`HERMES-OWNER-DECISION-001` and removes one of the six blockers to
`IMPLEMENTATION_START`.

A "no" must name a replacement for each rejected element and accept the failure
mode recorded against it, because leaving it unresolved keeps the gate closed.
