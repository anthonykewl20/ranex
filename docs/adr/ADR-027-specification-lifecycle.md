# ADR-027 — specification lifecycle

**Status:** accepted
**Date:** 2026-08-16
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-030-specification-lifecycle.md`

## Context and Problem Statement

ADR-017 defines a pre-implementation lifecycle but A/B/C bytes alone do not
record which human answered which blocking question or prevent an out-of-order
advance. This slice needs a replayable, typed decision record from `DRAFT`
through `APPROVAL_PENDING`, without granting implementation authority.

## Decision Drivers

- Equal state and machine-checkable input must yield equal records.
- A recorded actor and base digest must guard every transition.
- Human questions must be stable and their answers cannot be inferred from prose.
- A/B/C validation must remain owned by SLICE-029's foundation port.
- Refusal must be durable data, not an exception escaping a workflow.

## Prior art

- Searched: GitHub code search for immutable state transition tables, workflow
  replay nondeterminism, and human approval state machines.
- [XState adjacency traversal at c25dba07a2b68565edbe83d83c5d679dd85e00b2](https://github.com/statelyai/xstate/blob/c25dba07a2b68565edbe83d83c5d679dd85e00b2/packages/core/src/graph/adjacency.ts)
  traverses a bounded serialized state/event graph.
  License: MIT.
  Weakness: traversal discovers possible states; it does not authenticate an
  actor, bind a base digest, or make a refusal a durable record.
  Vendored: `docs/adr/prior-art/ADR-027/xstate-adjacency.ts` blob:fc9f4b077dfbc7bcdcf0a2e5d077bf3109616b82
- [Temporal Python workflow exceptions at 84b519e0ff407b049da88ac7d1711f110494ff4d](https://github.com/temporalio/sdk-python/blob/84b519e0ff407b049da88ac7d1711f110494ff4d/temporalio/workflow/_exceptions.py)
  distinguishes deterministic replay failure from calls in a read-only context.
  License: MIT.
  Weakness: its runtime and event history are a much broader external-effect
  system than this pure kernel decision function requires.
  Vendored: `docs/adr/prior-art/ADR-027/temporal-exceptions.py` blob:2d34c2fedda59bc9c457d633da3ee1138299efc4
- Rejected: https://github.com/pytransitions/transitions Its runtime-mutable
  callbacks and dynamically added transitions make the frozen transition table
  unverifiable and would add a dependency to a four-state pure function.
- Rejected: https://github.com/temporalio/sdk-python Its worker/runtime history
  solves distributed durable effects, but this slice deliberately has no effect
  to replay and may not introduce a journal or persistence adapter.

## Considered Options

1. Closed pure transition table with result records: chosen.
2. Mutable state-machine framework: rejected; transition authority can drift.
3. Throw validation exceptions to the CLI: rejected; callers lose durable cause.
4. Grant a preapproval read capability: rejected; no capability exists here.

## Decision Outcome

Use frozen dataclasses for sessions, questions, inputs, and results. The
application validates A/B/C through the foundation ports and returns either an
advanced session or a stable refusal. It records the input digest, actor, and
semantic digest with every result, so identical retry returns the same record.

### Consequences

- Only `DRAFT → SPEC_VALIDATED → TESTS_MAPPED → APPROVAL_PENDING` is reachable.
- Questions and answer IDs are canonical and machine-checkable.
- Observed-only facts remain characterization records, never approval inputs.
- No capability, producer invocation, subject write, journal write, or CLI-main
  registration is introduced.
- Sad paths 4 and 5 remain distinct in the closed vocabulary:
  `MISSING_ANSWER` is an omitted required answer and `UNKNOWN_ANSWER` names an
  answer for a question that was never asked. Sad path 8 records
  `INVALID_APPROVAL` when C's envelope is invalid, while sad path 9 records
  `CHAIN_MISMATCH` after a valid envelope fails A/B/C binding. The outer
  lifecycle code stays closed and the underlying `E-ABC-*` code is retained as
  the result cause.

### Confirmation

`test_specification_lifecycle.py` freezes transition/refusal, replay, question,
and no-authority cases. `test_specification_cli.py` drives the isolated parser
and checks stable refusal stderr. Main CLI integration is deferred by ADR-017.

## Improvements on the prior art

XState's bounded graph idea becomes a literal closed table rather than a
runtime-configurable machine. Temporal's replay distinction becomes a pure
input-digest retry result: there is no external effect to replay. Both are
references for mechanics only; neither becomes authority for human intent.

## Architecture surface

Add domain and application specification modules plus an unregistered CLI
module. The application consumes only `specification_abc` validators; it does
not select adapters, write the journal, or wire `main.py`.

## Scope and threat delta

This prevents prose-led or stale/out-of-order preapproval progress. It does not
approve, issue, revoke, persist, execute, generate tests, or protect effect
leaves; those remain later slices.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Determinism | retry after crash | byte-identical result record |
| Integrity | changed actor/base | stable typed refusal |
| Clarity | same A input | byte-identical question rendering |

## Reversibility

Door: two-way

The transition table and records can be superseded before any grant issuer is
added. Historical result records remain evidence, but cannot become a grant.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | blank actor | typed identity refusal |
| 2 | actor changes | typed identity refusal |
| 3 | out-of-order advance | typed order refusal |
| 4 | missing question answer | typed missing-answer refusal |
| 5 | unknown answer ID | typed contradiction refusal |
| 6 | ambiguous choice | typed ambiguity refusal |
| 7 | stale base digest | typed stale-base refusal |
| 8 | malformed A/B/C | typed contract refusal |
| 9 | A/B/C relation differs | typed chain refusal |
| 10 | observed-only fact offered as intent | refuse promotion |
| 11 | repeated identical request | return recorded result |
| 12 | model prose supplied | no public input field can advance it |

## Test strategy

Frozen `tests/unit/test_specification_lifecycle.py` enumerates every table row
and refusal code, then proves stable rendering, digest, retry, and absence of a
capability path. `tests/integration/test_specification_cli.py` invokes the
module-local argparse parser for draft, advance, questions, and refusal stderr.
Full suite remains the composition check.

## Code review checklist

- Is the state table closed and free of implementation states?
- Does every result carry actor, base, semantic, and input identities?
- Are all validation failures converted to stable records?
- Is `observed-only` unable to satisfy intended semantics?
- Does no public type or function issue a capability or invoke a producer?
- Is `main.py`, journal, signing, and generator code untouched?

## More Information

Vendored bytes prove bytes were obtained, not their upstream origin. The XState
source was also read in ADR-017, but is re-vendored here because this ADR makes
its own claim.
