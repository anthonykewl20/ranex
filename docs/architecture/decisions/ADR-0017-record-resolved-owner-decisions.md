# ADR-0017: Record a Resolved Owner Decision

| Field | Value |
|---|---|
| ADR ID | `ADR-0017` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-31 |
| Effective revision | Working tree based on `79d568914`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `assurance`, `policy`, `module_governance`, `compatibility` |
| RFC | [`RFC-0006`](../rfcs/RFC-0006-record-resolved-owner-decisions.md), accepted by the human owner on 2026-07-31 |
| Supersedes | Nothing. Amends `ADR-0013` so its own stated resolution procedure becomes executable |
| Review/expiry date | On any change to the owner-decision row shape, the authority-reference contract, or the resolution procedure in `ADR-0013` |
| Compatibility/migration class | Additive definition contract; no existing artifact changes meaning; no runtime is enacted |
| Security/data class | Public architecture decision; referenced human decisions retain their own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-31 | Initial accepted decision, promoted from `RFC-0006`. Makes the resolution procedure `ADR-0013:149-153` already prescribes representable in the compiled contract. |

## Context

`ADR-0013` registers twenty rows with status `OWNER_DECISION_REQUIRED`. Six now
have accepted decision records: `ADR-0015` resolves `HERMES-OWNER-DECISION-001`,
and `ADR-0016` resolves `-003`, `-013`, `-017`, `-019` and `-020`.

`ADR-0013:149-153` already states the procedure: satisfying one of these rows
"requires a catalog revision that names the accepted decision and its predeclared
acceptance test; until then the reference remains null and the named stage
blocks." The prose is coherent. The compiled machinery cannot express the
outcome it prescribes — the generator rejects a non-null reference, the row
schema pins the reference to `null` and the status to a single constant, and the
unresolved count is pinned to twenty.

The prior session handoff recorded that `ADR-0013` "encodes no path to
resolution." That was **incorrect** and is corrected here.

This decision introduces no new mechanism. Every element it adopts already exists
in this repository under `ADR-0010`, or in the canonical status vocabulary.

## Decision

### `OWNER-RESOLVE-001` — a resolved row is `ACCEPTED`

A satisfied row changes `status` from `OWNER_DECISION_REQUIRED` to `ACCEPTED`,
the existing canonical value meaning "human-approved and currently normative"
(`SOURCE_OF_TRUTH.md:184`), already used as a record status value at
`ADR-0010:1059`. No new status vocabulary is introduced. The row is retained in
the register, so `owner_decision_count` remains twenty.

### `OWNER-RESOLVE-002` — the reference is typed and digest-bound

`owner_decision_ref` becomes `TypedArtifactRefV1|null` exactly as at
`ADR-0010:856`: `{artifact_type, artifact_ref, artifact_digest}` with
`artifact_type` fixed to `human_decision`. A paired `owner_decision_digest` is
added. Both are null or both are non-null; when non-null, `owner_decision_digest`
equals `owner_decision_ref.artifact_digest`, mirroring `ADR-0010:872`. The
validator recomputes the digest from the referenced bytes rather than trusting
the recorded value, mirroring `validate_contracts.py:17947-17951`.

### `OWNER-RESOLVE-003` — resolution requires an authenticated human decision

A non-null reference must resolve to a `HumanDecisionV1` record validating
against `schemas/authority/human-decision-v1.schema.json`, authenticated, not
revoked, not expired, and authorized for the exact role, action and scope of the
named row, with `active_cardinality` 1, mirroring `ADR-0010:1236`.

The alternative considered was a digest-bound citation of the ADR file alone. It
was rejected because it does not close self-assertion: any party able to write
the generator input could record a resolution the owner never made. Ranex already
requires an authenticated decision to register a test behaviour; requiring less
for the gates that unblock `IMPLEMENTATION_START` would be incoherent.

### `OWNER-RESOLVE-004` — resolution lifts the block, it creates no runtime evidence

A resolved row's `runtime_validation_status` becomes `NOT_ASSESSED`, the value
already used for promoted provisions at `generate_contracts.py:6938` — never a
pass. `ADR-0013:158-159` requires runtime evidence to begin `NOT_ASSESSED`, and
resolving a decision executes nothing.

### `OWNER-RESOLVE-005` — the unresolved count is derived, never pinned

`unresolved_owner_decision_count` is computed from row state rather than asserted
as a literal. Its pinned form is redundant with `owner_decision_count` precisely
because no row can currently resolve. This is the only deletion this decision
accepts.

### `OWNER-RESOLVE-006` — a canonical source root, empty by default

Owner-decision records live in a canonical source root under
`architecture/records/`, governed as
`architecture/records/test-governance/behavior-authorities/` already is: only
canonical JSON files are eligible, each validates against its schema, each has
exactly one byte-bound catalog row, and the initial live population is empty and
therefore grants nothing.

### `OWNER-RESOLVE-007` — no existing fail-closed check is relaxed

No check is deleted to make a resolution representable. The negative case at
`validate_contracts.py:2670-2675`, which sets `owner_decision_ref` to the bare
string `"ADR-9999"` and requires `OWNER_FAIL_CLOSED`, is **retained**: a bare
unverifiable string is not a `TypedArtifactRefV1` and must continue to fail. The
`HERMES-OWNER-DECISION-020` exact-equality assertions are updated to their
resolved expected value, not removed.

Both research models consulted recommended deleting fail-closed checks to make
this change possible. Those recommendations are rejected. `ADR-0014` condition 6
states that a decision changes no existing check's strictness.

## Predeclared acceptance tests

1. A row with `status: ACCEPTED`, a well-formed `TypedArtifactRefV1`, a matching
   `owner_decision_digest` and a valid backing `HumanDecisionV1` validates, and
   the registry reports nineteen unresolved rather than twenty.
2. The same row with `owner_decision_digest` altered by one character fails.
3. The same row whose backing decision file is modified after citation fails on
   recomputation, with no change to the row itself.
4. A row citing a `HumanDecisionV1` that is expired, revoked, or authorized for a
   different role, action or scope fails.
5. A row citing a bare string such as `"ADR-9999"` fails — the existing negative
   case, unchanged.
6. A row with `status: ACCEPTED` and a null reference fails, and a row with a
   non-null reference and `status: OWNER_DECISION_REQUIRED` fails.
7. A resolved row reports `runtime_validation_status: NOT_ASSESSED`, never a
   pass, and neither readiness tier changes.
8. `unresolved_owner_decision_count` is recomputed from row state; forging it to
   any literal, including the current literal twenty, fails.
9. `owner_decision_count` remains twenty and the total entry count remains 98.
10. With the live record root empty, all twenty rows remain unresolved and
    blocking — the mechanism grants nothing by existing.

## Consequences and evidence standing

**This decision is not implemented on acceptance.** The registry continues to
report twenty unresolved owner decisions until the machinery is changed. That is
a stated gap, not a compliance claim, and it is the honest reading of the current
contract rather than a number edited to look better.

- Implementation requires a catalog revision taking `ADR-0013` to `1.5.0`. The
  `ADR-0013` source digest appears **102 times across four tracked files** —
  ninety-nine in the promotion registry alone — so a single byte changes all 98
  row digests and cascades to the registry manifest, schema registry and
  validation report. **FACT**, measured 2026-07-30.
- The catalog version `1.4.0` is separately pinned at `generate_contracts.py:5921`,
  `:10519`, `:18724` and `validate_contracts.py:1141`.
- `HERMES-OWNER-DECISION-020` trips three exact-equality assertions no other row
  trips: `generate_contracts.py:6716-6722`, `validate_contracts.py:1935-1940`,
  `validate_contracts.py:2492-2496`.
- Six `HumanDecisionV1` records must be created, one per already-accepted
  decision. This records decisions the owner has already made; it reopens none.
- `architecture/records/` currently holds only README files. This establishes the
  first live authority records in the repository.
- Fourteen rows remain unresolved and continue to block `IMPLEMENTATION_START`.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`. This
  decision authorizes no product code and declares no readiness tier.

## Human approval

The human owner accepted `RFC-0006` on 2026-07-31, having been shown both the
authenticated-decision option and the weaker digest-bound-citation alternative,
and selected the authenticated option. The acceptance covers `OWNER-RESOLVE-001`
through `OWNER-RESOLVE-007` together with the implementation cost recorded above.
