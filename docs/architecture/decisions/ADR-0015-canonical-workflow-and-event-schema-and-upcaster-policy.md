# ADR-0015: Canonical Workflow and Event Schema, and Upcaster Policy

| Field | Value |
|---|---|
| ADR ID | `ADR-0015` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-30 |
| Effective revision | Working tree based on `97c4c5ecf`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `governed_execution`, `work_management`, `assurance`, `policy`, `compatibility`, `migration`, `module_governance` |
| RFC | [`RFC-0004`](../rfcs/RFC-0004-canonical-workflow-and-event-schema-and-upcaster-policy.md), accepted by the human owner on 2026-07-30 |
| Supersedes | Nothing. Resolves `HERMES-OWNER-DECISION-001`, previously unresolved and blocking |
| Review/expiry date | Review on any change to the event envelope, interpreter contract, retention policy, or the §8.3 state/journal model |
| Compatibility/migration class | Additive definition contract; no existing artifact changes meaning; no runtime is enacted |
| Security/data class | Public architecture decision; recorded histories retain their own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-30 | Initial accepted decision, promoted from `RFC-0004`. Resolves the workflow/event schema and upcaster policy reserved to the owner by `HERMES-OWNER-DECISION-001`. |

## Context

`HERMES-OWNER-DECISION-001` (`ADR-0013:823-834`) reserved to the owner the
canonical Ranex workflow and event schema and upcaster policy, with no default,
absence outcome `BLOCK`, and activation without decision `DENIED`, blocking
`IMPLEMENTATION_START`.

The kernel had no workflow definition of any kind: `Execution` carries
`workflow_request_ref: str`, an opaque string, with no node identity, interpreter
pin, or event-schema pin. The corpus already classified the problem as "MATURE
PATTERN / R&D schema" and named the five required properties — immutable
definitions, interpreter version, event-schema version, upcaster compatibility,
and replay checks. Only the concrete form was undecided.

## Decision

### `WF-DEFINITION-001` — Immutable, content-addressed workflow definitions

`WorkflowDefinitionV1` is a closed RFC 8785 canonical JSON document carrying a
stable logical identifier, an integer version, an interpreter version pinned by
digest, an event contract naming envelope schema and schema-registry versions by
digest, input and output schema references by digest, an entry node key, and a run
policy. Node identity derives from the definition digest, so an identifier cannot
come to mean something else. Any edit produces a new version and digest;
definitions are never mutated in place.

### `WF-PIN-001` — Runs pin definition, interpreter, and schema registry

Each run records the exact definition version and digest, interpreter version, and
schema-registry version under which it executed. An active run may not acquire a
changed topology, node meaning, or interpreter fix by alias movement; it drains,
blocks, or is cancelled and re-requested.

### `WF-EVENT-001` — Reuse the existing envelope

Persisted events use `schemas/events/domain-event-envelope-v1.schema.json`
unchanged, with `event_version` carrying the payload schema version. No competing
envelope and no second serializer is introduced.

### `WF-UPCAST-001` — Upcasting on read, bytes never rewritten

Stored event bytes are never rewritten. One-to-one adjacent pure functions
normalize an older payload version to the current one before the reducer sees it,
so the reducer consumes only current normalized events and remains pure. A missing
or unknown upcaster is a blocking integrity failure; there is no fallback to
"latest."

Rejected, each with the failure it would introduce: **tolerant reader** (defaults
or ignored fields can silently change authority or terminality); **versioned event
types alone** (permanent per-version handlers accumulate inside the reducer whose
purity is load-bearing); **lazy in-place migration** (rewriting a stored event
invalidates its envelope digest and the append-only audit meaning, contradicting
§8.3); **copy-and-transform** (creates two histories and a cutover problem;
reserved for a future breaking decision).

Temporal's patch markers are deliberately not adopted: they suit code-defined
workflows, whereas Ranex already treats workflow definitions as immutable approved
data, so pinning plus upcasting achieves the same guarantee without version
branches in code.

## Accepted costs

Definitions, interpreter builds, upcasters, and frozen fixtures are retained for
the lifetime of dependent histories. A producer may not emit version `N+1` until
every reader has the registered upcaster. Old streams pay upcasting cost on full
replay. Historical facts cannot be edited; correction requires a compensating
event or a new run. Active runs cannot pick up fixes. One-to-one upcasters cannot
split, merge, delete, or reorder events — needing that means a new event type, not
a new version. Loss of an old interpreter or upcaster is a blocking integrity
incident.

## Predeclared acceptance tests

1. A history recorded under an older payload version replays through registered
   upcasters and reproduces the recorded snapshot digest exactly.
2. Removing a registered upcaster makes replay of an affected history raise an
   integrity error rather than proceeding.
3. Editing an approved definition without a version increment fails generation or
   validation.
4. A node identifier derived from one definition digest does not resolve against a
   different digest.
5. A run whose recorded interpreter or schema-registry version does not match the
   executing one blocks rather than adapting.
6. The reducer contains no version branching; existing architecture import tests
   confirm no upcaster logic enters the domain.
7. Acceptance changes no existing check's strictness and declares no readiness
   tier.

## Consequences and evidence standing

None of these tests is satisfied today, because no workflow definition, upcaster
registry, or interpreter exists. That is a stated gap, not a claim of compliance,
and it blocks at `IMPLEMENTATION_START` rather than now.

`schemas/events/domain-event-envelope-v1.schema.json` exists and already carries
`event_version`; this decision commits to reusing it rather than replacing it.

The §8.3 obligation that snapshots never replace the journal, enforced in the
kernel since 2026-07-30, is preserved: upcasting normalizes on read and never
mutates the journal.

`IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`.

## Human approval

The human owner accepted `RFC-0004` on 2026-07-30, stating acceptance of all six
recommended owner decisions. The acceptance covers `WF-DEFINITION-001`,
`WF-PIN-001`, `WF-EVENT-001`, and `WF-UPCAST-001` together with the costs recorded
above. It authorizes no product code and declares no readiness tier.
