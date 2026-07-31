# RFC-0010: Authorize Bounded Vertical Product Slices Before `IMPLEMENTATION_START_READY`

| Field | Value |
|---|---|
| Status | DRAFT |
| Owner | Human owner |
| Authors | Assistant, at owner direction 2026-07-31 |
| Created | 2026-07-31 |
| Version | `2.2.0` — `1.0.0` rejected by review; `2.0.0` amended and rejected again; `2.1.0` recorded those findings; `2.2.0` replaces the amendment surface with a measured, cheaper one and drafts the quarantine mechanism. **Still not promotable** — one blocker is infrastructural and cannot be cleared by drafting |
| Review by | Owner decision; promotion to `ADR-0021` is the owner's action, not the author's |
| Affected contexts | `process_assurance`, `assurance`, `policy`, `work_management`, `governed_execution` |
| Supersedes | Nothing. **`1.0.0` of this RFC claimed acceptance would narrow "only" `ADR-0012:72`. That was false.** The exact amendment surface is now enumerated in `Amendment surface` below, byte by byte. The tooling lane's own definition is **not** modified; a second, separately constrained lane is added beside it |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted (`rfcs/README.md` Status) |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md:57-76` |

## Decision question

`ADR-0012:72` states that the pre-readiness tracer lane "cannot implement a
product capability." `IMPLEMENTATION_START_READY` is the gate that would lift
that restriction, and it is not declared.

May Ranex build one small end-to-end product capability — governing only this
repository, claiming no readiness tier — before `IMPLEMENTATION_START_READY` is
declared?

## Context and evidence

### Facts

Measured in this repository on 2026-07-31 and recorded in
[`reviews/2026-07-31-delivery-model-restructure-assessment.md`](../reviews/2026-07-31-delivery-model-restructure-assessment.md):

- 20 accepted ADRs, 10 RFCs, 9,455 lines of ADR prose, 157 generated schemas,
  46 contract registries.
- **54,823 lines** of generator + validator Python. Its declared validation
  scope is `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`
  (`docs/architecture/assessments/validation-report.json:226`).
- **Zero lines of product code** on `bootstrap/pre-upstream`.
- The R&D tracer at `.claude/worktrees/kernel-tracer` has 4,859 lines of
  source and tests; **82 tests pass in 0.42s** (`uv run pytest -q`, executed).
- `grep -rn "architecture/contracts" src/ tests/` across the tracer returns
  **zero matches** — the document → registry → running-check path has never
  been closed.

### The structural argument

**Corrected in `2.0.0` after independent review.** `1.0.0` argued that Tier-1
requires TDD, landing and sealing evidence "before you are permitted to start
implementing," and that the topology is therefore *why* 54,823 lines of validator
and zero product exist. Both were overstated.

`ADR-0012:67` explicitly permits "one real current-subject `ADR-0008` cycle and
its separately produced `SUCCEEDED` `LandingRecord` and sealing evidence"
**inside** the tooling lane. `ADR-0012` already cut that circularity for tooling
subjects. Nothing in the Tier-1 gate set requires a shipped product capability.

What survives execution, and is all this RFC needs:

- Product capability is forbidden before the tier — in prose (`ADR-0012:72`) and
  in the machine contract (`:656-657`, and the generated `readiness-tiers.json`).
- Neither readiness tier is declared; the root tree holds no product code.
- The compiled maps have no runtime consumer: the tracer contains **zero**
  references to `architecture/contracts`.

The causal claim — that the topology *caused* the imbalance — is **INFERENCE**
and is not relied upon here. `ADR-0012:60-61` scopes the tooling lane to "only
the evidence needed to evaluate that tier," so growing the validator to 31,807
lines was a choice inside the funnel, not a compulsion. This RFC rests on the
prohibition being real and the product tree being empty. It does not need, and
does not assert, that the prohibition is the sole cause.

### Assumptions

- That a bounded product lane will not become a general bypass. `2.0.0` addresses
  this by construction — registry-backed admission (`SLICE-LANE-002`), mechanical
  drift detection (`-005`), and a succession cap (`-009`) — not by trust.
- **Withdrawn in `2.0.0`:** `1.0.0` assumed a slice would produce evidence usable
  by the Tier-1 gates. `SLICE-LANE-008` now makes slice evidence explicitly
  **inadmissible** for any `READY-*` gate. This removes the stated upside, and
  that is deliberate: an untested pathway from product-subject evidence into the
  readiness system is authority creep, and the review was right to flag it.

### Unknowns

- Whether the generated contract registries are loadable at runtime.
  **UNRESOLVED** — a bounded spike is required before the first slice is
  designed, not before this decision is made.
- Whether the three restatements at `ADR-0008:1718`, `SOURCE_OF_TRUTH.md:686`
  and `AI_ARTIFACT_CONTRACTS.md:672` require substantive or merely clarifying
  amendment. `2.0.0` argues clarifying, and states the residual risk openly in
  `Amendment surface` section D. **This is an owner call.**

### Conflicts

`ADR-0012:72` as written forbids what this RFC proposes, **and so does the
machine contract at `:656-657`, which `ADR-0012:79-82` declares the sole semantic
source.** `1.0.0` claimed acceptance would narrow one prose clause and nothing
else; that was false and is corrected. The full surface — prose, marked YAML,
regeneration cascade, and three clarifying notes — is enumerated in
`Amendment surface`.

This RFC does **not** weaken any gate, tier, evidence rule, authority boundary or
the noncompensating property. The tooling lane's own scope is byte-identical
after promotion.

## Requirements and non-goals

**Requirements.** A lane in which one small end-to-end capability may be built;
bounded by an accepted slice definition; producing real execution evidence;
governing only this repository; ending cleanly.

**Non-goals.** Declaring either readiness tier. Relaxing any gate. Granting
release, deployment, permit or grant authority. Authorizing work on any
repository other than this one. Authorizing more than one slice at a time, or
more than three in succession without fresh authorization. Producing any evidence
admissible to a readiness gate.

## Alternatives

### Option A — Add a second bounded lane beside the tooling tracer *(proposed)*

Adds `PRE_READINESS_PRODUCT_SLICE` with its own allowed and forbidden scope,
leaving the tooling lane byte-identical. Reversible: withdrawing it returns the
project to the status quo, and any slice built under it remains
non-authoritative and produces no readiness evidence.

### Option B — Declare `IMPLEMENTATION_START_READY` first

**Reassessed in `2.0.0`.** `1.0.0` called this "the circularity, not a way out."
That overstated it, and the independent review was right to say so. Tier-1 is
reachable *by design* without any product capability: its 11 gates are
architecture, tooling, review and human-decision shaped, and `ADR-0012:67` allows
the tracer to produce the TDD, landing and sealing evidence they need.

The real obstacles are dependency-laden rather than circular: two named external
model reviewers as noncompensating gates, with known availability problems
(`HANDOFF.md:179-182`), plus authenticated human-decision artifacts that do not
exist. **This remains a legitimate alternative** and the owner may prefer it. It
is slower and depends on third parties; it is not impossible.

### Option C — Continue building governance tooling until the gates can be met

Rejected on evidence, not preference: this has been the operating mode and has
produced 54,823 lines of validator and zero lines of product. It is a legitimate
choice, but it should be made knowingly rather than by default.

### Status quo

`ADR-0012:72` stands; no product code may be written; the project continues under
Option C by omission.

## Amendment surface — exactly what promotion changes

*Addresses review item 1. `1.0.0` claimed this was one prose line. It is not.*

**Design choice that bounds the blast radius.** The tooling lane is **not**
widened. Its `allowed_scope` and `forbidden_scope` stay byte-identical, so it
remains unable to implement product capability. Promotion adds a **second,
separately constrained lane object** beside it. "The tooling tracer cannot
implement a product capability" stays true after promotion, which is what makes
the restatements below survive.

### A. `ADR-0012` prose, `:57-76`

Add one paragraph after `:75` introducing `PRE_READINESS_PRODUCT_SLICE` and
pointing at the new YAML object. **No existing sentence is edited or deleted.**

### B. `ADR-0012` marked YAML, insert after `:663`

A sibling key to `bootstrap_lane`, inside the same
`<!-- BEGIN ADR12 READINESS TIER CONTRACT -->` block that `ADR-0012:79-82`
declares "the sole semantic source":

```yaml
  product_slice_lane:
    lane_id: "PRE_READINESS_PRODUCT_SLICE"
    current_authorization: "NOT_GRANTED_BY_THIS_DEFINITION"
    governed_repository_only: true
    max_open_slices: 1
    max_sequential_slices_per_authorization: 3
    allowed_scope:
      - "PRODUCT_CAPABILITY_IMPLEMENTATION_ON_GOVERNED_REPOSITORY"
      - "PRODUCT_RUNTIME_ACTIVATION_ON_GOVERNED_REPOSITORY"
    forbidden_scope:
      - "PRODUCTION_OR_USER_DATA"
      - "RELEASE_OR_DEPLOYMENT"
      - "READINESS_SELF_APPROVAL"
      - "GATE_OR_AUTHORITY_BYPASS"
      - "READINESS_EVIDENCE_PRODUCTION"
      - "REQUIRED_MERGE_BLOCKER_INSTALLATION"
      - "OPERATION_ON_ANY_OTHER_REPOSITORY"
    termination: "SUCCESS_FAILURE_EXPIRY_SCOPE_DRIFT_UNREGISTERED_PATH_OR_AUTHORIZATION_EXHAUSTION_ENDS_THE_SLICE"
```

Note `READINESS_EVIDENCE_PRODUCTION` in **forbidden** scope. That single token
implements the evidence quarantine (`SLICE-LANE-008`) and is what keeps the three
restatements in section D true.

### B.0 SUPERSEDED BY MEASUREMENT — do not amend `ADR-0012` at all

*`2.2.0`. Sections B and B.1 below are retained as history. Both proposed
editing `ADR-0012`. **Executed evidence says do not.***

**Measured, in a disposable copy:**

```
# edit ONE PROSE LINE of ADR-0012, outside the marked YAML block
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
ValueError: ADR-0012 source digest drift          EXIT=1
```

`generate_contracts.py:4480` pins `sha256_file(READINESS_ADR)` — the **entire
file** — against `ADR12_SOURCE_SHA256`. A second pin,
`ADR12_MACHINE_BLOCK_SHA256`, covers the marked block. **Any** byte changed
anywhere in `ADR-0012` fails generation until the constant is recomputed.

I had reasoned that prose at `:72` sat outside the marked block (lines 84–777)
and would therefore be free. **That reasoning was wrong and executing it is what
caught it.** The whole-file pin makes prose and YAML equally expensive.

**The alternative, also measured.** A new ADR carrying its own marked block,
with `ADR-0012` untouched:

```
$ # add docs/architecture/decisions/ADR-0021-<canonical-name>.md, ADR-0012 unmodified
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
ValueError: Accepted ADR header field cardinality drift: ADR-0021:ADR ID
```

It progressed past **every** `ADR-0012` check and failed only on the ordinary
new-ADR requirements — canonical filename, complete header, `SOURCE_OF_TRUTH`
declaration. **Neither digest pin was touched. `expected_keys` was never
reached.**

### Revised amendment surface — `PROPOSED`

1. **Do not edit `ADR-0012`.** Not the prose, not the YAML.
2. `ADR-0021` carries `product_slice_lane` in **its own** marked block, and
   records in its `Supersedes` header that it narrows `ADR-0012:72` for the
   product-slice lane only.
3. Add the projection for the new block; regenerate.
4. The three restatements keep their clarifying notes.

This is what rule 8 — *"preserve architectural history; supersede accepted ADRs
instead of silently rewriting them"* — already required. The corpus's own rule
pointed at the cheaper mechanism, and `2.0.0` proposed the expensive one.

**Residual, stated plainly:** `ADR-0012:72` still *reads* as an unqualified
prohibition. A reader who does not follow the supersession chain will conclude
the lane is illegitimate. That is inherent to supersede-don't-rewrite and is the
price of not re-pinning digests. The `Amendment surface` D notes remain
necessary.

### B.1 Surface B is NOT a drop-in — three hard failures, found by re-review

`2.0.0` presented the sibling key as an insertion. **It would break the
generator in three places.** All verified by opening the code:

| Blocker | Location | Effect |
|---|---|---|
| `set(contract) != expected_keys` — **exact set equality**, 37 members, `product_slice_lane` absent | `generate_contracts.py:4512-4533` | Adding the key raises "readiness contract identity drift". Not a warning; a hard stop |
| `ADR12_MACHINE_BLOCK_SHA256 = 90690d00…` pins the marked block's exact bytes | `generate_contracts.py:137-139`, checked at `:4475-4479` | **Any** edit to the block fails until the pin is recomputed |
| No projection exists for a second lane object | — | The registry would not carry it even if the first two passed |

So promotion requires, in order: extend `expected_keys`; write the second-lane
projection; regenerate; recompute and re-pin `ADR12_MACHINE_BLOCK_SHA256`;
regenerate again. Each step is generator code, not documentation.

**Alternative worth considering before committing to the sibling key:** put the
product-slice lane in a **separate contract file** that the current code accepts
without touching `ADR-0012`'s pinned block at all. That trades one amendment to
digest-pinned law for one new artifact, and it may be strictly cheaper. Not yet
evaluated. `UNRESOLVED`.

### C. Regeneration — the measured cost

Promotion requires `generate_contracts.py` to project the new object, then
regeneration of at least `architecture/contracts/readiness-tiers.json`, the
registry manifest, the schema registry and the validation report. `ADR-0012`'s
source digest is an input to the readiness projection, so **this is a
digest-cascading change**, comparable to the `ADR-0017` cost recorded at
`HANDOFF.md:99-107`. It is not a documentation edit and must not be scheduled as
one. The generator does not currently project a second lane object; that
projection is new code and is itself the first thing the amendment obliges.

### D. Restatements — clarifying, not substantive

| Location | Text | Status after promotion |
|---|---|---|
| `ADR-0008:1717-1719` | "only ADR-0012's bounded `PRE_READINESS_TOOLING_TRACER` may produce readiness evidence; **it** cannot implement a product capability" | **Remains true.** The slice lane produces no readiness evidence (forbidden scope), and the clause's "it" is the tracer |
| `SOURCE_OF_TRUTH.md:684-686` | "only ADR-0012's bounded `PRE_READINESS_TOOLING_TRACER` may produce the evidence needed to assess that tier" | **Remains true**, same reason |
| `AI_ARTIFACT_CONTRACTS.md:670-672` | "only the bounded `PRE_READINESS_TOOLING_TRACER` may produce its architecture/tooling evidence" | **Remains true**, same reason |

Each nonetheless takes a one-sentence clarifying note that a separate lane exists
which produces no readiness evidence — so no reader infers from "only X may
produce readiness evidence" that "only X may exist." That inference is not in the
text, but it is available, and an available misreading in a governance corpus is
a defect.

**Honest statement of residual risk:** this reading turns on the word "readiness"
in all three sentences. If the owner reads them as a blanket prohibition on any
pre-readiness product work, they require substantive amendment, not clarification,
and the cost rises. That call belongs to the owner.

## Proposed design

### `SLICE-LANE-001` — definitions, operationally testable

*Addresses review item 2. `1.0.0` used `product capability` and `slice` without
defining either, permitting laundering in both directions.*

**`product capability`** — code that satisfies **all four**:

1. reachable by a user or operator through an entry point (CLI, API, service),
   not solely by a test or a developer script;
2. produces an outcome consumed outside the process that produced it;
3. lives under a product path class (`src/ranex/**`), not under
   `scripts/architecture/**`, `schemas/**` or `architecture/**`;
4. is not exclusively a compiler, generator, validator, schema, fixture,
   manifest or review-harness artifact — the tooling lane's `allowed_scope`.

Failing any of the four, the work is **not** a product capability and belongs in
the tooling lane. Satisfying all four, it is, and may not be relabelled tooling.

**Known gaps, found by re-review and not yet closed:**

| Gap | Attack |
|---|---|
| Clause 3 names only `src/ranex/**` | Product logic placed under `scripts/**` or `.claude/worktrees/**` escapes the product label entirely. The tracer already has a `src/ranex` **inside a worktree** |
| Clause 3, inverse | Real product work kept under `scripts/architecture/**` passes as tooling and skips the slice registry altogether. **This is the more likely abuse**, because it is also the path of least friction |
| Clause 4 is editorial | "Not exclusively a review harness" — a gate-controller CLI is arguable either way, by design |
| Clause 2 does not discriminate | "Outcome consumed outside the producing process" is also true of a generator writing schemas. The conjunction leans entirely on clauses 3 and 4 |
| No checker | The whole test is prose. Nothing evaluates it |

The test is therefore a **usable definition for a human reviewer** and **not** an
enforcement mechanism. Stated plainly so it is not mistaken for one.

**`slice`** — one unit of product capability bounded by **all** of:

- exactly one user-or-operator-visible outcome, stated in one sentence;
- one entry point added or changed;
- a declared path allowlist, enumerated at acceptance;
- a **non-empty** exclusion list;
- ≤ 1,000 net added lines of product source excluding tests. Exceeding the
  bound does not fail the build — it **ends the slice** under `SLICE-LANE-005`
  and requires re-acceptance.

### `SLICE-LANE-002` — registry-backed admission

*Addresses review item 3. `1.0.0` made an owner-accepted prose definition the
entire admissions control, with no schema, no registry and no detection.*

A slice is admitted only by a record in
`architecture/records/product-slices/` validating against a new
`schemas/process/product-slice-definition-v1.schema.json`, carrying: `slice_id`,
`outcome` (one sentence), `entry_point`, `path_allowlist` (non-empty),
`excluded_behaviour` (non-empty), `acceptance_criteria`, `net_line_bound`,
`authorization_ref` and `authorization_digest` (see `SLICE-LANE-011`),
`opened_at`, `status`.

The registry is a **closed set**, following the pattern
`generate_contracts.py:5563` already uses for accepted decisions: a declared
slice with no record, and a product commit with no `slice_id`, are both findings.
A checker script rejects a product-path change carrying no open `slice_id`.

Until that schema and checker exist, acceptance tests 1, 2 and 5 are **not**
acceptance tests. They are stated intentions and are labelled as such below.

### `SLICE-LANE-003` — authority boundary

A slice governs **only this repository**. It declares no readiness tier, grants
no authority, issues no permit, produces no release or deployment, processes no
production or user data, and makes no availability or fitness claim to any third
party. It may not relax, waive or reinterpret any gate. Output is
non-authoritative, exactly as the R&D tracer's is — the precedent is
[`reviews/2026-07-28-gate-controller-mvp-user-level-audit.md`](../reviews/2026-07-28-gate-controller-mvp-user-level-audit.md).

### `SLICE-LANE-004` — evidence obligations are not reduced

Every slice change needs an exact work item, ordinary path and effect authority,
`ADR-0008` TDD, executed tests with recorded output, review, and human-controlled
landing. A claim that a check works requires evidence that it **actually failed
and blocked** at least once — a check only ever observed passing is not evidence.
Every recorded measurement carries the command **and its working directory**;
`ADR-0018`'s figure was wrong three times for exactly that omission.

### `SLICE-LANE-005` — the lane cannot widen itself, and drift is detected

*Addresses review item 3's second half. `1.0.0`'s equivalent provision specified
no detection, making it retrospective scolding.*

Scope growth ends the slice. Detection is mechanical, not editorial: a change
touching a path outside the slice's `path_allowlist`, or carrying the net-line
bound past its declared value, is a finding at the same checker that enforces
`SLICE-LANE-002`. A capability not named in the definition is a new slice
requiring new acceptance. No abstraction may be introduced for a capability
outside the current slice.

### `SLICE-LANE-006` — no de facto gate

*Addresses review item 4.*

A slice artifact **may not become a required merge blocker**. It runs advisory
by default. Promotion of any slice-produced check to required status requires a
separate explicit owner decision recorded as its own ADR, because a required
check is normative control over landing — gate-like authority — whether or not it
carries a `READY-*` identifier. `REQUIRED_MERGE_BLOCKER_INSTALLATION` is in the
lane's forbidden scope so this is machine-visible, not prose-only.

### `SLICE-LANE-007` — enforced repository confinement

*Addresses review item 5. `1.0.0` asserted "this repository only" with no
enforcement.*

A slice's entry point resolves every path against the governed repository root
and **rejects** an absolute path, a traversal outside that root, or any remote
or second-repository target. This is a behavioural contract with a sad-path test,
not a statement of intent. `OPERATION_ON_ANY_OTHER_REPOSITORY` is in the lane's
forbidden scope.

### `SLICE-LANE-008` — quarantine: slice evidence is not readiness evidence

*Addresses review item 5 of the review list — the one with the sharpest teeth.*

TDD cycles, landing records and sealing evidence produced under this lane are
**inadmissible** for any `READY-*` gate. They may not be bound by any
`BRIDGE-READY-*` rule. `ADR-0012`'s permitted bootstrap evidence remains
`ONE_REAL_CURRENT_SUBJECT_TDD_LANDING_AND_SEALING_TRACER` on tooling subjects
and is unchanged.

Admitting slice evidence to a readiness gate requires a named bridge amendment in
a future ADR. Default is inadmissible, and absence of an explicit admission is a
denial, not a gap.

This provision is what preserves the three restatements in `Amendment surface`
section D, and it is why `READINESS_EVIDENCE_PRODUCTION` sits in the lane's
forbidden scope.

**Corrected after re-review — the token is not a mechanism.** Three collisions
make the quarantine intent-only as drafted:

1. `SLICE-LANE-004` **obliges** the slice to produce TDD, landing and sealing
   artifacts, while `allowed_scope` permits `PRODUCT_RUNTIME_ACTIVATION`. So the
   artifacts get produced and sit on disk. Quarantine is a binding ban, not
   non-existence.
2. The bridge rules do not discriminate by subject path.
   `BRIDGE-READY-TDD-CYCLE-001` and `BRIDGE-READY-LANDING-001` accept
   `TDD_EXACT_SUBJECT`; `BRIDGE-READY-SEALING-001` accepts
   `ARCHITECTURE_SUBJECT`. **No tooling-path-exclusive subject class exists.** A
   product-subject `TddCycleRecordV1` can satisfy the relation rule as written.
3. `SLICE-LANE-010` says termination "invalidates no prior evidence," so the
   pile is sticky and a later bridge amendment can re-admit it wholesale.

**The mechanism, drafted in `2.2.0`.** A token enforces nothing; this does.

Add one field to the TDD, landing and sealing record types, and one validator
rule that reads it:

```yaml
# on TddCycleRecordV1, LandingRecordV1, and the sealing evidence record
subject_lane:
  type: enum
  values: ["PRE_READINESS_TOOLING_TRACER", "PRE_READINESS_PRODUCT_SLICE"]
  required: true          # absence is a finding, not a default
```

```
QUARANTINE-001 (validator rule)
  A ReadinessEvidenceBindingV1 whose evidence resolves a record with
  subject_lane == "PRE_READINESS_PRODUCT_SLICE" FAILS, for every gate_id
  in the Tier-1 and Tier-2 gate sets, regardless of bridge_rule_id.
  Absence of subject_lane FAILS. There is no waiver flag; admitting
  product-lane evidence requires a named bridge amendment in a future ADR.
```

Why this closes the three collisions:

| Collision | Closed by |
|---|---|
| Artifacts are produced and sit on disk | They may exist; `QUARANTINE-001` makes them **unbindable**. Quarantine is enforced at the binding, not by non-existence |
| Bridges do not discriminate by subject path | `subject_lane` is carried on the record, so no path heuristic is needed and no new native subject class is required |
| "Invalidates no prior evidence" makes the pile sticky | Stickiness is now harmless: the records persist and remain permanently unbindable unless a future ADR names an exception |

**Why a field rather than a path rule:** path-based discrimination would inherit
every laundering gap in `SLICE-LANE-001` — code under `scripts/architecture/**`
would produce tooling-lane evidence by location alone. A declared field is
checkable and cannot be changed by moving a file.

**Cost, honestly:** three record types change, so their schemas regenerate and
their digests cascade. `ADR-0015`'s upcaster policy governs the version bump.
This is real work and is **not yet done**. `PROPOSED`, not implemented.

### `SLICE-LANE-009` — bounded succession, not a standing lane

*Addresses review item 6. `1.0.0` allowed one slice at a time with unlimited
succession, which is a reusable bypass against `ADR-0012:74` — time-sliced.*

One authorization permits **at most three** sequential slices
(`max_sequential_slices_per_authorization: 3`). Exhaustion ends the lane and
requires fresh owner authorization to reopen.

**Corrected after re-review — the cap alone was theatre.** A fresh
`HumanDecisionV1` resets the counter, so three is a *batch size*, not a career
cap, and lifetime slice count stays unbounded. The bypass survived the fix meant
to close it.

Two additional bounds, either of which closes it:

| Option | Bound | Trade |
|---|---|---|
| **(a) Lifetime cap** | `max_total_slices_before_readiness: N` across all authorizations. Exhaustion ends the lane permanently until a readiness tier is declared | Hard and mechanical. Requires guessing N now |
| **(b) Sunset** | Each authorization carries `expires_at` (already required by `HumanDecisionV1`) and the lane admits no slice after the **first** authorization's expiry, regardless of reissue | No number to guess; bounded by wall-clock. Weaker if expiries are set long |

**Author's selection: both, conjunctively.** `2.2.0` adopts

```yaml
    max_sequential_slices_per_authorization: 3
    max_total_slices_before_readiness: 6
    lane_sunset: "FIRST_AUTHORIZATION_EXPIRES_AT"
```

Reasoning, so the owner can overturn it on the reasoning rather than on taste:
(a) alone requires guessing N with no evidence, but 6 is defensible as "two
authorizations' worth" — enough to learn whether slices work, too few to rebuild
the system through the side door. (b) alone is weak because an expiry can simply
be set long. Together, the lane ends on **whichever comes first**, so neither
weakness is load-bearing. Both are cheap to widen later with evidence and
expensive to narrow after abuse, which is the correct asymmetry for a bypass.

**This is an author recommendation, not an owner decision.** It is recorded here
so the RFC is complete and reviewable; the owner may set different values or
reject the approach. Without (a) *and* (b), `SLICE-LANE-009` does not satisfy
`ADR-0012:74` and this RFC must not claim that it does.

### `SLICE-LANE-010` — termination

The lane ends on: declaration of `IMPLEMENTATION_START_READY`; owner withdrawal;
scope growth under `SLICE-LANE-005`; or authorization exhaustion under
`SLICE-LANE-009`. Termination produces no readiness transition and invalidates no
prior evidence — which is safe **only** because `SLICE-LANE-008` kept that
evidence out of the readiness system in the first place.

### `SLICE-LANE-011` — authenticated authorization, no narrative consent

*Addresses review item 7.*

The lane opens only against a `HumanDecisionV1` record validating against
`schemas/authority/human-decision-v1.schema.json`, whose 22 required fields
include `principal_id`, `authentication_context_id`,
`presentation_challenge_digest`, `nonce`, `issued_at`, `expires_at`, `subject`,
`action`, `scope` and `digest`.

Each slice definition binds that record by `authorization_ref` and
`authorization_digest`. A conversational "yes" recorded in prose — including the
one currently in this RFC's `Human decision requested` section — **does not
satisfy this provision** and is explicitly insufficient. `ADR-0017:65`
`OWNER-RESOLVE-003` requires an authenticated decision, and an agent may not
discharge an obligation that constrains it.

## Predeclared acceptance tests

**Honest labelling, per review item 3.** Tests marked `EXECUTABLE ONLY AFTER` are
**not** acceptance tests today. They become acceptance tests when the named
artifact exists. Calling an unimplementable check an acceptance test is the
defect this RFC's own `SLICE-LANE-004` forbids.

| # | Test | Status |
|---|---|---|
| 1 | A product-path change carrying no open `slice_id` is refused | `EXECUTABLE ONLY AFTER` the `SLICE-LANE-002` checker exists |
| 2 | A change touching a path outside the slice's `path_allowlist` is a finding | `EXECUTABLE ONLY AFTER` the same checker |
| 3 | A slice definition with an empty `excluded_behaviour` fails schema validation | `EXECUTABLE ONLY AFTER` the slice-definition schema exists |
| 4 | A second open slice is refused while one is open | `EXECUTABLE ONLY AFTER` the slice registry exists |
| 5 | A fourth sequential slice under one authorization is refused | `EXECUTABLE ONLY AFTER` the slice registry exists |
| 6 | A slice cannot declare, or cause the declaration of, any readiness tier | Executable now against the readiness resolver contract |
| 7 | A slice cannot cause any gate to be relaxed, waived or reinterpreted | Executable now |
| 8 | Slice-produced TDD/landing/sealing evidence is rejected by every `BRIDGE-READY-*` rule | `EXECUTABLE ONLY AFTER` regeneration lands the quarantine token |
| 9 | A slice entry point rejects an absolute path, a traversal above the repository root, and a remote target | Executable as a sad-path test **within** the first slice |
| 10 | A slice-produced check installed as a required merge blocker is a finding | `EXECUTABLE ONLY AFTER` the `SLICE-LANE-002` checker exists |
| 11 | Opening the lane without a validating `HumanDecisionV1` is refused | `EXECUTABLE ONLY AFTER` an authorization record exists |
| 12 | Termination leaves prior evidence valid and produces no readiness transition | Executable now |

**Nine of twelve are not executable today** — eight `EXECUTABLE ONLY AFTER` plus
test 9, which is deferred into the first slice. Three are executable now, and
even those have no slice runner to execute against, so in practice the honest
figure is **three of twelve, all unexercised**.

`2.0.0` originally claimed "six of twelve." That was false, produced by
estimating rather than counting, in a document whose own `SLICE-LANE-004`
forbids exactly that. Counted this session with a script over the table rows.
That is a statement about this RFC's readiness, not a reason to soften the tests.

## Independent challenge

This RFC and its source assessment were submitted to independent adversarial
review, briefed to attack rather than confirm.

**Result: REJECTED AS DRAFTED.** Eligible for promotion only after the named
amendments below. Every finding cited here was independently re-verified by the
author against this repository before being recorded; none is relayed on the
reviewer's word.

### Verified defects in this RFC

| # | Finding | Verification |
|---|---|---|
| 1 | **The "narrows only `:72`" claim was false.** The ban also lives in `ADR-0012:648-657`'s marked YAML — which `ADR-0012:79-82` declares "the sole semantic source" — in the generated `readiness-tiers.json`, and at `ADR-0008:1718`, `SOURCE_OF_TRUTH.md:686`, `AI_ARTIFACT_CONTRACTS.md:672`. Amending prose alone would leave the lane authorised in prose and illegal in contract | `grep` on all five, executed |
| 2 | **`product capability` is nowhere defined operationally.** Neither `ADR-0012` nor this RFC gives a path class, artifact type or test. An authority boundary that cannot classify work is not airtight, and permits laundering in both directions | `ADR-0012` carries only the bare token |
| 3 | **Slice admission is prose-only.** No slice-definition schema, no open-slice registry, no mechanical check that the excluded list is non-empty. `1.0.0`'s scope-growth provision specifies no detection, making it retrospective | inspection of this RFC |
| 4 | **A required CI check is gate-like authority.** The plan's own step — promote the slice's check to required — creates a blocking control without amending any `READY-*` gate, so acceptance tests 3 and 4 cannot see it | inspection |
| 5 | **"Governs only this repository" has no enforcement.** No path allowlist, no remote check. A CLI taking an arbitrary path satisfies the prose while operating elsewhere | inspection |
| 6 | **Slice evidence could pollute Tier-1.** `ADR-0012`'s allowed bootstrap TDD is `ONE_REAL_CURRENT_SUBJECT_TDD_LANDING_AND_SEALING_TRACER` on tooling subjects. Product-subject evidence would either fail the bridges or silently widen what counts as readiness evidence — and `1.0.0`'s termination provision says "invalidates no prior evidence," so it cannot be withdrawn | `ADR-0012` bootstrap_lane `allowed_scope` |
| 7 | **The recorded owner "yes" is unauthenticated prose.** No `HumanDecisionV1` artifact exists for it. Citing `OWNER-RESOLVE-003` beside a narrative yes does not satisfy it | no populated record found |
| 8 | **Serial slices are a standing bypass.** `ADR-0012:74` forbids the tracer becoming "a reusable bypass." "At most one slice at a time" permits unlimited succession — a bypass class, time-sliced | `ADR-0012:74` |
| 9 | **Dangling precedent link.** Corrected in this revision | `ls`, executed |
| 10 | **This RFC broke `ADR-0020`'s freshness gate on arrival** — added unindexed, so `check_record_freshness.py` went red with `record_not_indexed` and `stated_range_stale`. Corrected in this revision | gate executed, was `EXIT=1` |

### Correction to the source assessment

The assessment framed `ADR-0012` as requiring "a real TDD cycle, a landing record
and a sealing validation **before you are permitted to start implementing**."
That overstates it. `ADR-0012:67` explicitly permits "one real current-subject
`ADR-0008` cycle and its separately produced `SUCCEEDED` `LandingRecord` and
sealing evidence" **inside** the tooling lane. `ADR-0012` already cut that
circularity for tooling subjects. The prohibition is on *product* capability
specifically, not on producing readiness evidence.

The reviewer ruled the assessment's central causal claim — that the gate topology
is *why* 54,823 lines of validator and zero product exist — **partly sound only**.
Product is forbidden, readiness is undeclared, and the maps have no runtime
consumer: all verified. But "forbids product" does not entail "authorises
unlimited tooling forever," and growing the validator past the evidence Tier-1
needs remains a choice inside the funnel. The causal claim is demoted to
`INFERENCE` and must not be relied on as fact.

### Amendments — disposition in `2.0.0`

| # | Amendment | Disposition |
|---|---|---|
| 1 | Amend the real law, not only `ADR-0012:72` | **DRAFTED.** `Amendment surface` A–D specifies the prose insertion, the exact YAML object, the regeneration cascade and the three clarifying notes. Blast radius reduced by adding a lane rather than widening the tooling lane, which stays byte-identical |
| 2 | Define `product capability` and `slice` operationally | **DRAFTED.** `SLICE-LANE-001` — a four-part conjunctive test for `product capability` that runs in both directions, and five bounds on `slice` including a non-empty exclusion list and a net-line cap |
| 3 | Registry-backed slice admission | **PARTIAL — design only.** `SLICE-LANE-002` names the record location, a schema and a checker. **None exist on disk**: `architecture/records/product-slices/` and `schemas/process/product-slice-definition-v1.schema.json` are both absent, and `generate_contracts.py:5563` is the *ADR* catalog parser, not a slice parser. Nine of twelve acceptance tests are consequently not executable |
| 4 | Bar de facto gate smuggling | **DRAFTED.** `SLICE-LANE-006`, backed by `REQUIRED_MERGE_BLOCKER_INSTALLATION` in the machine-visible forbidden scope |
| 5 | Quarantine slice evidence | **DRAFTED.** `SLICE-LANE-008`, backed by `READINESS_EVIDENCE_PRODUCTION` in forbidden scope. This also withdraws `1.0.0`'s stated upside — see `Assumptions` |
| 6 | Cap serial slices | **DRAFTED.** `SLICE-LANE-009`, `max_sequential_slices_per_authorization: 3` |
| 7 | Authenticated owner decision artifact | **SPECIFIED, NOT SATISFIED.** `SLICE-LANE-011` names the schema and the binding fields. **No such record exists.** This RFC cannot be promoted until one does |
| 8 | Incorporate the review | **DONE** in this revision |
| 9 | Housekeeping to green | **DONE** — RFC indexed, `docs/README.md` range corrected, dangling link fixed, `check_record_freshness.py` back to `EXIT=0` |
| 10 | Drop the over-strong causal story | **DONE** — demoted to `INFERENCE` in `The structural argument`, and `Option B` reassessed as dependency-laden rather than circular |

### Second independent review — `2.0.0` REJECTED

`2.0.0` was re-reviewed and **rejected again**. Ruling: amendments 1–6 and 8 are
**partially closed** (design only, no mechanism on disk); 7 is honestly open; 10
is closed; **9 was falsely claimed closed in the reviewer's environment**.

Every finding below was re-verified by the author against this repository.

**An author error the reviewer surfaced, recorded because it is mine.** The
reviewer was given a repository copy containing `2.0.0` of this RFC but **not**
the index updates made alongside it, so it correctly reported the freshness gate
red and the RFC unindexed. In this repository both are green — verified by
executing `check_record_freshness.py` (`EXIT=0`, "20 ADRs, 10 RFCs, no stale
claims") and by `grep`. **The reviewer reported its environment accurately; the
environment was stale because the author built it carelessly.** A review of a
stale tree is worth less than it appears, and the fault is the author's.

| Finding | Verified? | Disposition |
|---|---|---|
| **Surface B breaks the generator in three places** — `expected_keys` exact-set equality, the `ADR12_MACHINE_BLOCK_SHA256` byte pin, and the missing projection | **Yes**, code opened | `Amendment surface B.1` added. A separate contract file is now flagged as a possibly cheaper alternative |
| **"Six of twelve" acceptance tests was a false count** — it is nine | **Yes**, counted by script | Corrected to nine, with three executable-now that have nothing to execute against |
| **The succession cap is a batch size, not a career cap** — reissuing authorization resets it | **Yes**, by reading the provision | Two closing options added; **owner must pick one** |
| **The evidence quarantine is intent, not mechanism** — artifacts are still produced, bridges do not discriminate by subject path, and the pile is sticky | **Yes**, bridge rules opened | Recorded as `UNRESOLVED`; a validator rule or tooling-exclusive subject class is required and is not drafted |
| **The four-part capability test has four laundering gaps**, the most likely being real product kept under `scripts/architecture/**` | **Yes**, by inspection | Gaps table added; the test is now labelled a human definition, not enforcement |
| **Amendment 8's blanket "DONE" overreached** while other items were partial | Accepted | This section replaces it |

### Disposition in `2.2.0`

| Blocker from `2.1.0` | Status |
|---|---|
| The generator amendment, specified and costed | **CLOSED by measurement.** Do not edit `ADR-0012` at all — a whole-file digest pin makes prose as expensive as YAML. Put the lane in `ADR-0021`'s own block and supersede by reference, which is what rule 8 already required. Both paths executed; see `Amendment surface B.0` |
| The quarantine mechanism | **DRAFTED.** `subject_lane` on the three record types plus validator rule `QUARANTINE-001`, which fails every `BRIDGE-READY-*` binding for product-lane evidence. Not implemented |
| The succession-bound call | **RECOMMENDED, not decided.** Both bounds conjunctively: 3 per authorization, 6 lifetime, sunset at first expiry. Reasoning given so it can be overturned on reasoning |
| The restatement-scope call | **RECOMMENDED, not decided.** Clarifying notes, with residual risk stated. Cheaper now that `ADR-0012` is not edited at all |
| A third review against a current tree | **OPEN** |
| An authenticated `HumanDecisionV1` | **OPEN, and infrastructural — see below** |

### The blocker that drafting cannot clear

`SLICE-LANE-011` requires a `HumanDecisionV1`. **No mechanism exists to produce
one.** Verified:

- No populated `HumanDecisionV1` instance exists anywhere in `architecture/`.
- The only construction of those fields is a **synthetic fixture inside the
  validator** (`validate_contracts.py:8436`, `"authentication_context_id":
  "auth_" + decision_id`) — a test double, not an issuing authority.
- `ADR-0017`'s `OWNER-RESOLVE-*` provisions are **not projected** into
  `architecture/contracts/`; the decision is accepted, the machinery is not
  built. `HANDOFF.md` records the same.

So `RFC-0010` cannot be promoted until `ADR-0017` is implemented — there is no
authentication context, no challenge digest, no nonce issuance. **This is a
genuine deadlock and it is not the owner's fault or mine: the corpus requires an
artifact it cannot yet mint.**

Three ways out, for the owner to choose:

1. **Implement `ADR-0017` first.** Correct, and it is tooling-lane work so it is
   permitted today. Measured cost: the `ADR-0013` digest appears 102 times across
   four tracked files.
2. **Record the decision in the form the corpus can actually produce today** —
   a signed prose decision in `decisions/`, explicitly labelled as not
   satisfying `OWNER-RESOLVE-003` — and make `RFC-0010` depend on `ADR-0017`
   landing before the *first slice opens* rather than before promotion.
3. **Do not promote.** Keep the lane closed until `ADR-0017` is built.

Option 1 is cleanest and is the author's recommendation. It also means the next
work item is not a slice at all — it is `ADR-0017`'s machinery, which is
permitted, unblocked, and blocks everything else.

`2.2.0` is materially better than `2.0.0` and is still not safe to promote. The
policy goal remains legitimate; the instrument now has one dependency that no
amount of drafting removes.

Three further defects in the source assessment were found by the author's own
verification and corrected before this RFC was drafted: an off-by-one citation;
a citation relayed from `RFC-0009` without checking, which on inspection
overstated its source; and an inference stated as near-fact.

## Human decision requested

Accept, reject, or amend. On acceptance this RFC is promoted to `ADR-0021` and
the amendment surface in section A–D is executed — **including the regeneration
cascade**, which is engineering work, not a documentation edit.

### Three decisions are requested, not one

1. **The lane itself.** Permit `PRE_READINESS_PRODUCT_SLICE` as specified.
2. **The restatement question** (`Unknowns`). Are `ADR-0008:1718`,
   `SOURCE_OF_TRUTH.md:686` and `AI_ARTIFACT_CONTRACTS.md:672` satisfied by a
   clarifying note, as `2.0.0` argues, or do they require substantive amendment?
   The author's reading turns on the word "readiness" in all three sentences and
   could be wrong.
3. **The quarantine trade.** `SLICE-LANE-008` makes slice evidence inadmissible
   for readiness. This is safer, and it means the first slice contributes
   **nothing** toward `IMPLEMENTATION_START_READY`. `1.0.0` claimed that
   contribution as the upside; `2.0.0` gives it up. The owner should confirm that
   trade knowingly.

### Owner position recorded 2026-07-31 — and why it is not sufficient

Asked whether Ranex may build one small end-to-end capability, governing only
this repository and claiming no readiness, before `IMPLEMENTATION_START_READY` is
declared, the human owner answered **yes**, and subsequently directed that this
RFC be amended through review items 1–7.

**That is a genuine owner decision and it is recorded verbatim. It does not
satisfy `SLICE-LANE-011`.** No `HumanDecisionV1` record exists: there is no
`principal_id`, no `authentication_context_id`, no
`presentation_challenge_digest`, no `nonce`, no `expires_at`, no `digest`. Under
`ADR-0017:65` `OWNER-RESOLVE-003` a conversational yes is not an authenticated
decision, and an agent may not discharge an obligation that constrains it.

Recording the decision is the author's job. Authenticating it is not, and this
RFC does not pretend otherwise.
