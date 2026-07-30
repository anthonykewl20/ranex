# RFC-0006: Record a Resolved Owner Decision

| Field | Value |
|---|---|
| Status | ACCEPTED |
| Owner | Human owner |
| Authors | Assistant, from Codex and HY3 research, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; amends `ADR-0013` and unblocks recording of `ADR-0015`/`ADR-0016` |
| Affected contexts | `assurance`, `policy`, `module_governance`, `compatibility` |
| Supersedes | Nothing. Amends `ADR-0013` to make its own stated resolution procedure executable |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md` owner-decision rows |

## Decision question

`ADR-0013` registers 20 rows with status `OWNER_DECISION_REQUIRED`. Six now have
accepted decision records: `ADR-0015` resolves `HERMES-OWNER-DECISION-001`;
`ADR-0016` resolves `-003`, `-013`, `-017`, `-019`, and `-020`. The contract
system cannot record that fact. It reports 20 unresolved.

How should a resolved owner decision be represented, such that a resolution
cannot be forged, aliased, backdated, or asserted by the party the decision
constrains?

## The problem is the machinery, not the policy

**FACT.** `ADR-0013` already states the resolution procedure at lines 149–153:

> Later architecture material may discuss the same subject, but topical overlap
> is not treated as an exact owner-decision binding. Satisfying one of these rows
> requires a catalog revision that names the accepted decision and its
> predeclared acceptance test; until then the reference remains null and the
> named stage blocks.

Lines 142–147 and 1175–1176 define only the *pre-resolution* state. Two
independent model readings (Codex, HY3) reached this same conclusion. The prose
is internally coherent; the compiled machinery contradicts it.

The previous session handoff recorded that `ADR-0013` "encodes no path to
resolution." That is **incorrect** and is corrected here.

### Where the machinery blocks it

**FACT**, each read at the cited line on 2026-07-30.

| path:line | pin |
|---|---|
| `generate_contracts.py:6946` | raises if `owner_decision_ref is not None` |
| `generate_contracts.py:6955` | assigns `BLOCKED_OWNER_DECISION_REQUIRED` unconditionally for the whole collection |
| `generate_contracts.py:10598` | schema: `status` const `OWNER_DECISION_REQUIRED` |
| `generate_contracts.py:10624` | schema: `owner_decision_ref` `{"type": "null"}` |
| `generate_contracts.py:10533-10535`, `:10629` | schema: `runtime_validation_status` const `BLOCKED_OWNER_DECISION_REQUIRED` |
| `generate_contracts.py:6870-6874` | `owner_decision_ref` excluded from scalar type/nonblank validation |
| `generate_contracts.py:18746` | unresolved count set equal to total |
| `validate_contracts.py:2158`, `:2413-2423` | two independent passes assert the reference is null |
| `validate_contracts.py:2165-2167`, `:2424-2428` | derived blocked runtime status, twice |
| `validate_contracts.py:2265-2266` | `owner_decision_count: 20`, `unresolved_owner_decision_count: 20` |
| `validate_contracts.py:2464` | status histogram pins exactly 20 rows to `OWNER_DECISION_REQUIRED` |

`HERMES-OWNER-DECISION-020` additionally trips three exact-equality assertions
that no other row trips: `generate_contracts.py:6716-6722`,
`validate_contracts.py:1935-1940`, `validate_contracts.py:2492-2496`. `ADR-0016`
resolves `-020`, so this cost is unavoidable.

### The dominant cost is a digest cascade

**FACT**, measured by exact-string count on 2026-07-30. The `ADR-0013` source
digest `sha256:acd188f5833ed9a051be03cb9d631948912c6ddffcd469cac41dd988171d1df3`
appears **102 times across four tracked files**:

| file | occurrences |
|---|---|
| `architecture/contracts/hermes-research-promotions.json` | 99 — one `governing_adr_digest` per each of the 98 rows, plus the registry-level source digest |
| `architecture/contracts/accepted-adrs.json` | 1 (`:89`) |
| `architecture/contracts/architecture-elements.json` | 1 (`:25846`) |
| `architecture/contracts/architecture-element-assessments.json` | 1 (`:776`) |

Each of the 98 rows also carries its own distinct row `digest`, computed over
content that includes the embedded ADR digest. Revising one byte of `ADR-0013`
therefore changes all 98 embedded ADR digests, therefore all 98 row digests,
therefore the registry digest at `registry-manifest.json:80`, and propagates on
to `schema-registry.json:207` and `validation-report.json:216-235`. The catalog
version `1.4.0` is separately pinned at `generate_contracts.py:5921`, `:10519`,
`:18724`, and within the required revision fragments at
`validate_contracts.py:1141`.

This is the bulk of the work. The row change itself is small.

## Ranex already contains the mechanism — this RFC adopts it

Per the standing rule that Ranex is not novel, no mechanism is designed here. The
required capability exists in this repository, accepted under `ADR-0010`,
implemented, and passing validation today.

| requirement | where it already exists |
|---|---|
| typed reference `{artifact_type, artifact_ref, artifact_digest}` | `validate_contracts.py:16976-16980` |
| declared as `TypedArtifactRefV1\|null` | `ADR-0010:856` |
| both-null-or-both-nonnull; digest equality invariant | `ADR-0010:872` |
| digest recomputed rather than trusted as written | `validate_contracts.py:17947-17951` |
| status enum in which non-active states grant no authority | `ADR-0010:866`, `:874` |
| `ACCEPTED` already used as a record status enum value | `ADR-0010:1059`, `:1134` |
| binding to role, action, outcome, `active_cardinality: 1` | `ADR-0010:1236` |
| authenticated decision record — principal, authentication context, presentation challenge digest, nonce, issue/expiry, revocation, supersession | `schemas/authority/human-decision-v1.schema.json` |
| canonical source root that is empty by default and grants nothing | `architecture/records/test-governance/behavior-authorities/README.md` |
| status value for a human-approved normative artifact | `ACCEPTED`, `SOURCE_OF_TRUTH.md:184` |
| runtime status when a contract is defined but unproven | `NOT_ASSESSED`, `generate_contracts.py:6938` |

### External convergence

Two maintained public standards separate the same three concerns Ranex collapsed
into one constant — the requirement's identity, its disposition, and the artifact
authorizing that disposition.

- **NIST OSCAL** `implementation-status` carries a required `state` flag with
  values `implemented`, `partial`, `planned`, `alternative`, `not-applicable`,
  plus `remarks`. Content binding is separate: `back-matter/resource` carries
  `rlink` and `hash` (algorithm + value). Source:
  `usnistgov/OSCAL`, `src/metaschema/oscal_implementation-common_metaschema.xml`.
  **Ranex deliberately diverges on one point:** OSCAL marks that enum
  `allow-other="yes"`, leaving it open. Ranex closes it, because an open status
  enum permits a generator to invent a disposition, which `ADR-0013:1175-1176`
  forbids.
- **OASIS SARIF 2.1.0** `suppression` carries required `kind`
  (`inSource`/`external`), optional `status` (`accepted`/`underReview`/`rejected`),
  and `justification`. Source: `oasis-tcs/sarif-spec`,
  `sarif-2.1/schema/sarif-schema-2.1.0.json`. Ranex has already adopted SARIF
  `result.level` for finding severity, so this extends an existing adoption.

## Recommended provisions

### `OWNER-RESOLVE-001` — a resolved row is `ACCEPTED`, not a new status

A satisfied row changes `status` from `OWNER_DECISION_REQUIRED` to `ACCEPTED`,
the existing canonical value meaning "human-approved and currently normative"
(`SOURCE_OF_TRUTH.md:184`), already used as a record status enum value at
`ADR-0010:1059` and `:1134`. No new status vocabulary is introduced and
`SOURCE_OF_TRUTH.md` does not change. The row is retained in the register, so
`owner_decision_count` remains 20.

### `OWNER-RESOLVE-002` — the reference is a typed, digest-bound artifact reference

`owner_decision_ref` becomes `TypedArtifactRefV1|null` exactly as at
`ADR-0010:856`: `{artifact_type, artifact_ref, artifact_digest}` with
`artifact_type` fixed to `human_decision`. A paired `owner_decision_digest` is
added. Both are null or both are non-null; when non-null,
`owner_decision_digest` equals `owner_decision_ref.artifact_digest`, mirroring
`ADR-0010:872`. The validator recomputes the digest from the referenced bytes
rather than trusting the recorded value, mirroring
`validate_contracts.py:17947-17951`.

This closes the edit-after-citation and aliasing attacks: a cited decision
cannot change underneath its citation, and a reference cannot be repointed.

### `OWNER-RESOLVE-003` — resolution requires an authenticated human decision

A non-null reference must resolve to a `HumanDecisionV1` record validating
against `schemas/authority/human-decision-v1.schema.json`, authenticated, not
revoked, not expired, and authorized for the exact role, action, and scope of the
named row, with `active_cardinality` 1 — mirroring `ADR-0010:1236`.

**This is the provision the owner selected.** The alternative considered was a
digest-bound citation of the ADR file alone. That alternative was rejected
because it does not close self-assertion: any party able to write the generator
input document could record a resolution the owner never made. Ranex already
requires an authenticated decision for registering a test behaviour; requiring
less for the gates that unblock `IMPLEMENTATION_START` would be incoherent.

### `OWNER-RESOLVE-004` — resolution lifts the block; it creates no runtime evidence

A resolved row's `runtime_validation_status` becomes `NOT_ASSESSED`, the value
already used for promoted provisions at `generate_contracts.py:6938` — not a
pass. `ADR-0013:158-159` requires runtime evidence to begin `NOT_ASSESSED`, and
resolving a decision does not execute anything. `IMPLEMENTATION_START_READY` and
`PRODUCTION_READY` remain `NOT_ASSESSED`.

### `OWNER-RESOLVE-005` — the unresolved count is derived, never pinned

`unresolved_owner_decision_count` is computed from row state, not asserted as a
literal. Its current pinned form is redundant with `owner_decision_count`
precisely because no row can resolve; both are 20 for that reason. The status
histogram at `validate_contracts.py:2464` becomes a derived comparison against
row state rather than a fixed triple.

**Both** the Codex and HY3 sweeps independently identified this pin as the item
to delete rather than extend. It is the only deletion this RFC accepts.

### `OWNER-RESOLVE-006` — a new canonical source root, empty by default

Owner-decision records live in a new canonical source root under
`architecture/records/`, governed by the same rules as
`architecture/records/test-governance/behavior-authorities/`: only canonical JSON
files are eligible, each must validate against its schema, each must have exactly
one byte-bound catalog row, and the initial live population is empty and
therefore grants nothing. READMEs, templates, symlinks, and synthetic fixtures
are never authority sources.

### `OWNER-RESOLVE-007` — no existing fail-closed check is relaxed

No check is deleted to make a resolution representable. Specifically, the
negative case at `validate_contracts.py:2670-2675`, which sets
`owner_decision_ref` to the bare string `"ADR-9999"` and requires
`OWNER_FAIL_CLOSED`, is **retained**: a bare unverifiable string is not a
`TypedArtifactRefV1` and must continue to fail. The `-020` exact-equality
assertions are updated to their resolved expected value, not removed.

Both research models recommended deleting fail-closed checks to make this change
possible — HY3 the generator pre-checks at `generate_contracts.py:6941-6950`,
Codex the negative case at `:2670`, the `-020` comparisons, and the per-row
runtime status field. Those recommendations are **rejected**. `ADR-0014`
condition 6 states that a decision changes no existing check's strictness, and
the standing constraint forbids relaxing a check to make code pass.

## Predeclared acceptance tests

1. A row with `status: ACCEPTED`, a well-formed `TypedArtifactRefV1`, a matching
   `owner_decision_digest`, and a valid backing `HumanDecisionV1` validates, and
   the registry reports 19 unresolved rather than 20.
2. The same row with `owner_decision_digest` altered by one character fails.
3. The same row whose backing decision file is modified after citation fails on
   recomputation, without any change to the row itself.
4. A row citing a `HumanDecisionV1` that is expired, revoked, or authorized for a
   different role, action, or scope fails.
5. A row citing a bare string such as `"ADR-9999"` fails — the existing negative
   case at `validate_contracts.py:2670-2675`, unchanged.
6. A row with `status: ACCEPTED` and a null reference fails, and a row with a
   non-null reference and `status: OWNER_DECISION_REQUIRED` fails; the paired
   invariant holds in both directions.
7. A resolved row reports `runtime_validation_status: NOT_ASSESSED`, never a pass,
   and neither readiness tier changes.
8. `unresolved_owner_decision_count` is recomputed from row state; forging it to
   any literal value fails, including the current literal 20.
9. `owner_decision_count` remains 20 and the total entry count remains 98.
10. With the live record root empty, every one of the 20 rows remains unresolved
    and blocking — the mechanism grants nothing by existing.

## Consequences and evidence standing

- `ADR-0013` requires a catalog revision, taking it to `1.5.0`. This changes all
  98 row digests and cascades to six generated artifacts, as measured above.
- Six `HumanDecisionV1` records must be created, one per already-accepted
  decision. This records decisions the owner has already made; it re-opens none
  of them.
- `architecture/records/` currently holds only README files. **FACT** — this
  establishes the first live authority records in the repository.
- The status histogram, unresolved-count pin, and `-020` special cases all change
  shape. None is removed.
- No product code is authorized. No readiness tier is declared. Runtime evidence
  remains `NOT_ASSESSED` throughout.
- Fourteen rows remain unresolved and continue to block `IMPLEMENTATION_START`.
  This RFC records six resolutions; it does not resolve the rest.

## Human approval

The human owner selected the authenticated-decision option on 2026-07-30, in
preference to a digest-bound ADR citation, after being shown both. This RFC
records that selection and awaits acceptance of the provisions above. It
authorizes no product code and declares no readiness tier.
