# Delivery-model restructure assessment — 2026-07-31

Requested by the owner: reorganize Ranex into an architecture-first but
**incremental** process — a system-wide map, then small validated vertical
slices, with ADRs written only for decisions that block the next slice.

This is an assessment and a proposal. It accepts no decision, grants no
authority, and authorizes no code.

Every claim is labelled. **FACT (executed)** means a command was run in this
working tree today and its output is quoted. **FACT (read)** means it was read
at a cited `path:line`. **INFERENCE** means concluded, not proven.

---

## 1. Current-state assessment

### Measured

| | | source |
|---|---|---|
| Accepted ADRs | 20 | FACT (executed) `ls docs/architecture/decisions/ADR-*.md \| wc -l` |
| RFCs | 9 (5 `ACCEPTED`, 4 `DRAFT`) | FACT (executed); statuses FACT (read) `docs/architecture/rfcs/README.md` |
| ADR prose | 9,455 lines | FACT (executed) |
| Architecture docs | 11,906 lines | FACT (executed) |
| Generated JSON Schemas | 157 | FACT (executed) |
| Generated contract registries | 46 | FACT (executed) |
| Generator + validator | **54,663 lines of Python** | FACT (executed) `wc -l scripts/architecture/{generate,validate}_contracts.py` |
| Product code on `bootstrap/pre-upstream` | **none** | FACT (executed) |
| R&D tracer (`.claude/worktrees/kernel-tracer`) | 4,859 lines src+tests, **82 tests pass in 0.42s** | FACT (executed) `uv run pytest -q` |
| Readiness | neither tier declared | FACT (read) `docs/HANDOFF.md:54-55` |

### The central finding

**Ranex has already done Big Design Up Front.** The thing the owner now wants to
avoid is not a risk ahead — it is the current state.

Fifty-four thousand lines of executable checking code exist, and every line of
it checks *documents*. The validator's own declared scope says so:
`EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`. The compiler compiles the map. It has
never touched the territory.

This is not a criticism of the corpus's quality. The domain model, the state
axes, the schemas and the operating model are unusually careful work. It is a
criticism of **sequencing**: 20 accepted architectural decisions have been made
about a system of which zero lines exist, and the only evidence any of them are
right is that they are internally consistent with each other.

### Why it happened — the structural cause, not a discipline failure

This did not happen because anyone chose to over-design. It happened because
**the gate topology selects for it.**

`ADR-0012` makes `IMPLEMENTATION_START_READY` the precondition for product code.
Its Tier-1 gate set (FACT (read), `ADR-0012:522-533`) is **11** gates, including
`READY-TDD-CYCLE-001`, `READY-LANDING-001`, `READY-SEALING-001`,
`READY-HY3-REVIEW-001` and `READY-DEEPSEEK-REVIEW-001`.

**Corrected after independent review.** An earlier revision of this section read
"you must have completed a real TDD cycle, a landing record, a sealing validation
and two independent model reviews *before you are permitted to start
implementing*." **That was wrong.** `ADR-0012:67` explicitly permits "one real
current-subject `ADR-0008` cycle and its separately produced `SUCCEEDED`
`LandingRecord` and sealing evidence" **inside** the tooling lane. `ADR-0012`
already cut that circularity for tooling subjects. Nothing in the Tier-1 gate set
requires a shipped product capability. The prohibition is specifically on
*product* capability, not on producing readiness evidence — and the remaining
frictions (model-reviewer availability, human decision artifacts) are real but
are not circular.

`ADR-0012` anticipated the circularity and opened one bounded escape hatch, the
`PRE_READINESS_TOOLING_TRACER` lane (`ADR-0012:57-76`). Read what that lane may
build: "compiler, generator, validator, schema, fixture, manifest, and
deterministic review-harness changes." Read what it may not (`ADR-0012:72`):
"The lane cannot implement a product capability."

**So the only work the process authorizes is more governance tooling.** That is
precisely the work that exists. 54,663 lines of it. The bootstrap lane is not a
neutral escape hatch; it is a funnel, and it has been pointing at the same wall
for the whole project.

**Demoted after independent adversarial review — read before relying on this.**
The reviewer ruled this causal claim **partly sound only**, and that ruling is
correct.

What survives execution: product capability is forbidden before the tier, in
prose *and* in the machine contract (`ADR-0012:648-657`, and the generated
`architecture/contracts/readiness-tiers.json`); neither tier is declared; the
root tree holds no product code; the compiled maps have no runtime consumer.

What overreaches: "forbids product" does not entail "authorizes unlimited tooling
and nothing else, forever." `ADR-0012:60-61` scopes the lane to "**only** the
evidence needed to evaluate that tier." Growing `validate_contracts.py` to 31,807
lines was therefore a sequencing choice *inside* the funnel, not something the
topology compelled. An earlier revision of this section said the outcome was "not
any failure of discipline"; that under-assigned the choice and has been removed.

The claim stands as **INFERENCE**. The topology is a real constraint and a real
funnel, but exclusive causation is not measured, and no decision should rest on
it as though it were fact.

### Second finding: the decision backlog has turned self-referential

The six most recent ADRs, by subject:

| ADR | subject |
|---|---|
| 0015 | canonical event/workflow schema and upcaster policy |
| 0016 | resolve five owner decisions |
| 0017 | **how to record that an owner decision was resolved** |
| 0018 | static type checker |
| 0019 | Python toolchain manager |
| 0020 | the record-freshness **self-check** |

`ADR-0017`'s entire subject is the machinery for recording decisions. Its
measured implementation cost (FACT (read), `HANDOFF.md:99-107`) is a digest
cascade across 102 occurrences in four tracked files. **The cost of deciding
something has become high enough to distort what gets decided** — which is the
exact opposite of the owner's rule 10, "optimize for small reversible decisions."

Not one of these six moved a user-visible capability. INFERENCE, and a firm one:
with nothing above the architecture to pull from, "what should we decide next?"
has no answer except "whatever the machinery demands next."

### Third finding: the top of the hierarchy is missing

The owner's proposed hierarchy begins with **Product requirements**. That layer
**does not exist in this repository.** FACT (executed) — there is no
requirements document, no user-outcome register, no acceptance-criteria corpus.
`README.md`'s "What Ranex is being built to do" is persuasive prose, not
requirements.

Every ADR is therefore anchored to an architecture that is anchored to nothing.
This is the root cause of finding two, and it is fixable cheaply.

### Fourth finding, verified today: the freshness gate has a live false negative

**FACT (executed).** `README.md:241` states "14 accepted ADRs". Twenty exist.
The record-freshness gate declares a `stated_count_stale` check
(`ADR-0020` `RECORD-SELFCHECK-003`). Run today:

```
$ uv run --project scripts/architecture python scripts/architecture/check_record_freshness.py
records fresh: 20 ADRs, 9 RFCs, no stale claims
EXIT=0
```

The gate passes while the repository's front page is six ADRs stale. Cause
(FACT (read), `scripts/architecture/check_record_freshness.py:27-33`): the
scanned set is `docs/architecture/decisions/`, `docs/architecture/rfcs/` and
`docs/README.md`. The **root `README.md` is not in the declared set.**

**It is worse than a scoping gap.** The check is this regex
(`check_record_freshness.py:142-144`):

```
\|\s*Accepted ADRs\s*\|\s*\*\*(\d+)\*\*
```

Run against the corpus (FACT (executed)), it matches **one row in one file** —
`docs/HANDOFF.md`. It returns **zero** matches in `docs/README.md`, which is
inside its own declared scan set, and could never match `README.md:241`
(`| Architecture | 14 accepted ADRs · …`) on two independent counts: the label
is not "Accepted ADRs" and the number is not bold.

So the check is not merely scoped narrowly — it is shaped to one hand-written
sentence in one file, and cannot detect the same class of defect anywhere else.

It also **infers a claim from prose with a regex**, which is exactly what
`RFC-0009`'s own `RECORD-FRESH-002` says must never happen: "claims are
declared, never inferred from prose." The capability proposed for sale to other
projects violates its own second principle in its only existing implementation.

This is a working demonstration of the blind spot in the very capability the
current in-flight decision proposes to generalise — before that capability has
been made correct at n=1.

### Fifth finding: the type-check gate is unwired, and its number is invocation-dependent

All **FACT (executed)** in this working tree.

**The gate does not run.** `ADR-0018` `TYPECHECK-STRICT-001` states "Strict mode
is the gate; a non-zero exit blocks." At `HEAD`, `architecture-contracts.yml`
runs regenerate → prove-no-drift → validate → record-freshness → concurrency →
upload. There is **no `pyrefly` step**. The gate is declared and never executed.

**The count depends on the working directory:**

```
$ cd scripts/architecture && uv run --group typecheck pyrefly check
  INFO Checking project configured at .../scripts/architecture/pyproject.toml
  INFO 245 errors                          (138 validate / 107 generate)

$ uv run --project scripts/architecture --group typecheck pyrefly check   # from root
  INFO Checking current directory with auto configuration
  No `pyrefly.toml` found — using preset `basic`
  6 errors, exit 1
```

Same pinned tool, same code, **245 vs 6** — a 40× swing, because the `--project`
form silently discards `preset = "strict"`. **Both exit non-zero**, so both look
like the gate blocking. `ADR-0018:79-81` records the command **without a working
directory**, and that omission is what determines the answer.

**A fourth stale figure, inside the file `ADR-0018` governs.**
`scripts/architecture/pyproject.toml:23` reads "the **265** errors currently
reported here are a recorded finding." `ADR-0018` was corrected twice on this
number — 256, then 245. The config says 265, which matches neither.

This reframes a recorded assistant error. `HANDOFF.md` logs "wrote a stale figure
into an accepted ADR" as carelessness. It is not: **the tool reports different
truths depending on how it is called, and the figure was recorded without the
invocation that produces it.** The fix is a rule this project already believes
in — record the command *and its working directory* beside every number, and wire
that exact invocation into CI so the gate cannot be satisfied by the weaker one.

### What is genuinely valuable and must be preserved

Being critical is not the same as being dismissive. These hold up:

- The **34 bounded contexts, state axes, transitions and path contracts.** This
  is a real domain model and re-deriving it would be expensive.
- The **157 schemas** — mostly correct-shaped, and directly reusable.
- The **kernel tracer.** 82 passing tests, a gate controller, an append-only
  SQLite execution store with crash-boundary and journal-replay tests, an
  evidence verifier and a hash-chain ledger. This is the single strongest asset
  in the repository and it is sitting in an untracked worktree, unable to be
  promoted because the process forbids product capability.
- The **epistemic discipline** — FACT/INFERENCE/UNVERIFIED labelling, evidence
  bound to subject digests, absence blocks, no self-approval. Keep all of it.
- The **evidence in RFC-0009** — eight measured false claims. That is real data.

---

## 2. Purpose and scope of the ADR currently being written

The in-flight decision is **`RFC-0009`: Record freshness as a shipped Ranex
capability** — `DRAFT`, authored 2026-07-31 at owner direction, not yet promoted
to an ADR. FACT (read),
`docs/architecture/rfcs/RFC-0009-record-freshness-as-a-shipped-capability.md:5-8`.

**What it is actually trying to settle**, stated plainly:

> Should Ranex ship, *to other people's projects*, a mechanical check that their
> written records still agree with observable facts — and on what terms: what
> triggers the obligation, which records are covered, how a project declares
> them, and whether staleness blocks?

The scope boundary is explicit and is the crux of the whole assessment. RFC-0009
states (`:46-49`) that the self-check already running in this repository is
**deliberately not its subject**, because it is "hardcoded to this repository's
paths and record types, and a capability customers run cannot be."

So RFC-0009 is a **product decision about behaviour toward governed projects
that do not exist yet.**

---

## 3. Is that decision required for the next executable vertical slice?

**No. Verdict: `CAN BE DEFERRED`.**

The reasoning is not stylistic. It is that RFC-0009 has no possible consumer:

1. Ranex cannot run against an external repository. No CLI, no entry point, no
   project-loading code exists. FACT (executed) — zero product code.
2. There are no governed projects, and there cannot be until (1).
3. All five provisions constrain behaviour toward a third-party project.
   **Zero of them constrain the next slice.**
4. `RECORD-FRESH-004` binds staleness to "the readiness gate" — machinery that
   has never executed once.

It is generalizing from n=1 before the n=1 case is correct. Section 1's fourth
finding proves the n=1 case is *not* correct: the existing self-check passes
today while the front page is stale.

**The sharper point:** RFC-0009 is a well-argued document that would have been a
good decision to make later. Writing it now was not a mistake of reasoning — it
was the process working exactly as designed, because the process had nothing
else to offer. That is the thing being fixed.

---

## 4. Parts that are premature or speculative

| Element | Verdict | Why |
|---|---|---|
| `RECORD-FRESH-001` closed-set manifest | **Premature** | Designs a customer-facing declaration format with no consumer, no runtime to read it, and no second project to test generality against |
| `RECORD-FRESH-002` declared-not-inferred claims | **Keep as a principle, drop as a provision** | The principle is durable and belongs in the map. The provision presumes the manifest above |
| `RECORD-FRESH-003` mechanical and reproducible | **Not a per-capability rule** | This is a system-wide architectural constraint. It belongs in the Master Architecture Specification, binding every check Ranex ever ships |
| `RECORD-FRESH-004` blocks at the readiness gate | **Speculative** | Couples an unbuilt capability to unexecuted machinery. Two unknowns multiplied |
| `RECORD-FRESH-005` cannot self-discharge | **Already decided** | `ADR-0017:65` `OWNER-RESOLVE-003` — "resolution requires an authenticated human decision" — already establishes it. Restating an invariant per capability is how invariants drift. **Note:** `RFC-0009:57` cites `ADR-0013:1175-1176` as forbidding "the exact self-assertion." Checked: those lines read *"An unresolved owner choice cannot be activated by configuration, convention, model output, or a generator default"* — that governs decision **activation**, not self-discharge, and `grep` finds no self-approval or self-assertion language anywhere in `ADR-0013`. The RFC **overstates its own source** |
| The nine predeclared acceptance tests | **Preserve verbatim** | Good tests. Park them with the deferred decision; they become the acceptance criteria when it reopens |
| The eight-false-claims evidence table | **Preserve, promote** | The strongest empirical result in the corpus. It belongs where it can be cited by more than one decision |

Also premature, outside RFC-0009, and worth saying while we are here: the
**121 undecided array element types** (`HANDOFF.md:110-112`). Deciding 121 field
types for records that nothing produces is 121 speculative decisions. Decide
only the fields the current slice actually writes.

---

## 5. What belongs in the Master Architecture Specification instead

Two categories. The first is small; the second is not.

### From RFC-0009

- **Record Freshness** as a named system capability, status `PROVISIONAL`, with
  its one line of scope and a pointer to the deferred decision.
- **"No enforcement check invokes a model"** — promoted from a provision of one
  capability to a system-wide architectural constraint.
- **"A party may not discharge an obligation that constrains it"** — a trust
  boundary, stated once, in the map.

### From the existing ADR corpus — the larger move

A substantial fraction of the 9,455 lines of ADR prose is **map, not decision**:

| Currently in | Content that is map | Should become |
|---|---|---|
| `ADR-0003` | The target architecture, 34 contexts, authority kernel | MAS §domain boundaries, §containers, §data ownership — labelled `CONFIRMED`/`PROVISIONAL`. ADR-0003 shrinks to its one real decision: the target tree is authoritative over the legacy guide |
| `ADR-0007` | Modular DDD layout | MAS §component structure `CONFIRMED` (the tracer proves it works). ADR retained as the decision record |
| `ADR-0011` | Worker orchestration, runtime adapters | MAS §containers `PROVISIONAL` — decided on paper, never run |
| `ADR-0012` | Readiness tiers, 21 gates, state axis | MAS §deployment topology + §major failure modes. The tier *vocabulary* is `CONFIRMED`; the *gate set* is `PROVISIONAL` and, per §1, actively harmful in its current form |
| `ADR-0004` | Quality-attribute baselines | MAS §scalability assumptions, all `PROVISIONAL` — no measurement exists |
| `ADR-0009` | Boundary fit, dependency edges | MAS §domain boundaries `PROVISIONAL` |

**Why this move matters mechanically, not just tidily:** an ADR here is
digest-pinned into 46 registries. `ADR-0013`'s digest appears 102 times
(`HANDOFF.md:100-101`). Every correction to the map therefore costs a full
contract-tree cascade. Putting the *map* in a document that is **not**
digest-pinned makes it cheap to keep current — which is rule 9 — while ADRs stay
pinned, because a *decision* should be expensive to change. Right now both are
expensive, so neither gets updated, which is how `README.md` reached six ADRs
stale under a passing freshness gate.

---

## 6. Unresolved assumptions requiring evidence before acceptance

Ranked by how much rests on them.

**A. The product thesis itself is untested.** "Rules compiled into code change
what an agent produces, where rules in a prompt do not." This is the bet
(`README.md:39`). Nothing in the repository tests it end to end. Twenty ADRs
rest on an assumption with zero experimental support. This is not a criticism of
the bet — it is a statement that the first slice must be the one that tests it.

**B. That the compile-from-documents pipeline scales.** 54,663 lines of
generator+validator to produce 46 registries is early evidence against. INFERENCE.

**C. That strict typing is achievable on that generator.** 245 pyrefly errors
outstanding; a bulk attempt was made, produced a false neutrality proof, and was
reverted (`HANDOFF.md:82-97`). `ADR-0018` `TYPECHECK-DEBT-001` forbids a
baseline. That combination may be unsatisfiable as written.

**D. That the generated contract registries are loadable at runtime.**
**FACT (executed):** `grep -rn "architecture/contracts" src/ tests/` across the
tracer returns **zero matches**. It loads gate definitions from its own YAML via
`policy/adapters/configuration/yaml/gate_catalog_loader.py`, a generic loader
with no binding to the generated tree. The document → registry → running check
path has **never been closed.** That path is the pipeline's whole premise, and
it is unproven.

**E. That the `ADR-0012` gate set is achievable at all.** It requires two named
external model reviewers as noncompensating gates. Model availability is already
known to be unreliable (`HANDOFF.md:179-182`, opencode-go quota exhausted).

---

## 7. Proposed Master Architecture Specification structure

**Correction to this section.** My first draft invented a bespoke 19-section
structure. That violates the owner's standing rule — *Ranex is not novel; find
the working piece before designing anything.* An established, maintained
standard exists and covers every element the owner listed. Verified against
official sources rather than recall:

- **arc42** — twelve sections, in use since 2005, explicitly tailorable.
  Section list confirmed at <https://arc42.org/overview>.
- **ISO/IEC/IEEE 42010:2022** — Edition 2, published 2022-11, the current
  standard for the structure and expression of an architecture description.
  Confirmed at <https://www.iso.org/standard/74393.html>.

**Every element the owner asked for maps onto arc42 with nothing left over:**

| Owner's requirement | arc42 section |
|---|---|
| Product requirements | 1. Introduction & Goals |
| Major system capabilities | 1. Introduction & Goals |
| System context; external integrations | 3. Context & Scope |
| Domain boundaries; containers; components; data ownership | 5. Building Block View |
| Principal data flows; major failure modes | 6. Runtime View |
| Deployment topology | 7. Deployment View |
| Trust and security boundaries; observability boundaries | 8. Crosscutting Concepts |
| — (the ADR index) | 9. Architectural Decisions |
| ASRs; scalability assumptions | 10. Quality Requirements |
| Unresolved architectural risks | 11. Risks & Technical Debt |

**Proposal:** `docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md`, arc42's
twelve sections in order, plus one tailoring — **§13 Slice Ledger**, recording
every delivered slice, what it validated, and what it disproved. Target
≤ 800 lines. **Not** digest-pinned. Every section and every material claim
carries a status label.

| label | meaning |
|---|---|
| `CONFIRMED` | supported by a stated requirement or executed implementation evidence |
| `PROVISIONAL` | current direction, not validated |
| `UNRESOLVED` | a real decision is still required; names the trigger |
| `OUT-OF-SCOPE` | not needed for the current delivery horizon |

### An owner decision this raises — licensing

**FACT**, confirmed at <https://arc42.org/license>: arc42 is published under the
**Creative Commons Attribution-ShareAlike 4.0 International License**. Using it
requires giving credit and linking the licence; **publishing an adaptation of
the template requires releasing that adaptation under the same licence.**

This repository is **public**, and `LICENSE-RANEX.md` is personal-use, all
rights reserved, with commercial optionality deliberately preserved. So this is
not a neutral choice and I am not treating it as one. Two paths:

1. **Adopt and attribute.** Credit Starke and Hruschka, link CC BY-SA 4.0, and
   accept ShareAlike on that one document's structure. Note arc42 states that
   *your own content* within the template remains yours — only the template
   structure carries the licence.
2. **Use arc42 as a conformance checklist only.** Author our own section list,
   then check it against arc42 and 42010 for gaps, and cite them as the
   standards checked against rather than republishing an adaptation.

I recommend **(2)** for the first pass — it captures the entire benefit, which
is *not missing a section*, without introducing a licence obligation into a
public repository whose commercial position is still open. This is the owner's
call, not mine, and it is not a legal opinion.

Honest prediction, INFERENCE: on first authoring, arc42 §4–§11 will be
overwhelmingly `PROVISIONAL`, with `CONFIRMED` appearing only where the tracer's
82 tests reach. That is the correct and useful outcome. A map that admits it is
mostly hypothesis is worth more than 20 ADRs that do not.

arc42 §1 (product requirements) and §10 (ASRs) are the only genuinely missing
content. They should be short — an afternoon, not a phase.

---

## 8. Proposed first vertical slice

### Slice 1 — "One governed change, gated by evidence, in this repository"

**Operational outcome, in the owner's terms:** *I can ask Ranex whether a change
is allowed to land, and it answers from recorded evidence rather than from a
model's opinion, and it writes down why.*

**Shape:**

```
A change is proposed (a commit on this repository)
  → CLI:          PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate <ref> --approver <identity>
  → application:  gate controller loads ONE gate definition
                  from the generated contract tree
  → domain rule:  absence blocks — a required claim with no evidence is FAIL,
                  never a pass, never a default
  → persistence:  append-only evaluation record, subject-digest bound
  → observable:   PASS/FAIL on stdout naming the failing rule and the missing
                  evidence; non-zero exit
  → verification: unit + integration + replay tests, and the command runs as a
                  required check on this repository's own CI
```

**This shape is not novel either, and should not be presented as such.** It is a
**walking skeleton** — Alistair Cockburn, *Writing Effective Use Cases* (2000):
"a tiny implementation of the system that performs a small end-to-end function…
it need not use the final architecture, but it should link together the main
architectural components." The same idea appears in this project's **own
reference corpus** as *The Pragmatic Programmer*'s **tracer bullet** — which is
what the existing worktree is already named. The concept was in the building
already; it just was not being applied.

**Why this slice and not another:**

- It is the **only** slice whose user exists today. Ranex's first customer is
  Ranex. Any other slice requires inventing a user.
- It **directly tests assumption A** — the product thesis — because from the day
  it lands, changes to this repository are gated by compiled code rather than by
  prose an agent can reinterpret.
- It **closes assumption D** — the document → registry → running check path.
  That path is the premise of the entire architecture and has never been closed.
- **~70% already exists and is proven.** The tracer has the gate controller,
  the execution store, journal replay, the evidence verifier and the hash-chain
  ledger, with 82 tests I executed today. The slice is largely *promotion plus a
  registry loader plus a CLI*, not new invention.
- It is **not horizontal infrastructure.** It produces a verdict a person reads.
- It **produces the first runtime evidence in the project's history**, which is
  what every `NOT_ASSESSED` in the corpus is waiting on — including
  `READY-TDD-CYCLE-001` and `READY-LANDING-001`. It walks toward the readiness
  gates instead of waiting for them.

**Explicitly excluded** — and none of this may be added mid-slice (rule 6):
fleet or multi-worker anything; worktree isolation; leases; queues, event buses
or upcasters; the readiness resolver; authenticated human-decision records; the
other 20 gates; capability scoring; the record-freshness product capability;
plugins; caching; any second gate; any generalization to a second repository.

**Rejected alternatives, briefly.** *Record-freshness as product* — no user,
§3. *Intent capture / plain-language spec* — user-visible but crosses no
architecture layer and tests no assumption. *Finish the 245 type errors* — pure
horizontal infrastructure, delivers no capability, and per §6C may be
unsatisfiable as specified.

---

## 9. ADRs required for this slice

### `REQUIRED NOW` — exactly one

**`ADR-0021`: Authorize bounded vertical product slices before
`IMPLEMENTATION_START_READY`.**

This is the only genuinely blocking decision, and it is genuinely
architecturally significant. Slice 1 *is* a product capability, and
`ADR-0012:73` forbids the tracer lane from implementing one. Without this ADR,
no vertical slice may be written at all — and per §1, the project repeats its
history.

It must settle, and nothing more:

1. That a bounded **product-slice lane** exists alongside the tooling tracer.
2. Its authority boundary: governs **only this repository**; claims no readiness
   tier; produces no release, deployment, grant or permit; does not relax any
   gate; makes no availability claim to any third party.
3. Its per-slice obligations: an accepted slice definition, TDD per `ADR-0008`,
   tests executed and recorded, and evidence that a check **actually failed and
   blocked** before it is claimed to work.
4. What ends the lane: scope growth beyond the accepted slice, or the declaration
   of `IMPLEMENTATION_START_READY`.
5. That it **supersedes** `ADR-0012`'s bootstrap-lane scope clause and nothing
   else. The tier definitions, the state axis and the 21 gates are untouched
   (rule 8).

Suggested provision IDs: `SLICE-LANE-001` … `-005`.

### `ALREADY DECIDED` — no new ADR, cite and move

| Decision | Record |
|---|---|
| Implementation language + escape hatch | `ADR-0014` |
| Static type checker (`pyrefly` 1.1.1) | `ADR-0018` |
| Toolchain manager (`uv`) | `ADR-0019` |
| TDD as default discipline | `ADR-0008` |
| Modular DDD repository layout | `ADR-0007` |
| Canonical workflow/event schema | `ADR-0015` |
| No self-approval / no self-assertion | `ADR-0013`, `ADR-0017` |
| Readiness tier vocabulary and states | `ADR-0012` |
| Finding severity uses SARIF `result.level` | commit `637eb3148` |

### `CAN BE DEFERRED` — with the trigger that reopens each

| Deferred | Reopens when |
|---|---|
| `RFC-0009` record freshness as product | A second repository is actually governed by Ranex — **and** the n=1 false negative in §1.4 is fixed |
| `RFC-0002` Spec Kit adaptation | An intent-capture slice is selected |
| `ADR-0017` full implementation (102-digest cascade) | A slice needs a `HumanDecisionV1` record written at runtime |
| The 121 undecided array element types | Per field, when a slice actually writes that field |
| `ADR-0011` worker orchestration enactment | A slice needs more than one worker |
| Everything in `ADR-0012`'s Tier-2 gate set | Slice 1 is not a release |

### `NOT AN ADR`

- The self-check being repository-specific — that is implementation detail of
  `ADR-0020`, already accepted.
- The model-routing table — an operational note, correctly living in `HANDOFF.md`.
- Array element types the field name determines — a derivation rule, already
  decided by the owner (`HANDOFF.md:111-112`).
- **Fixing `README.md:241`** — a stale fact, not a decision. Fix it directly.
  Widening the freshness gate's declared set to include the root `README.md`
  *is* a change to `ADR-0020` `RECORD-SELFCHECK-003` and is a small ADR
  amendment, not a new decision.

### `REQUIRES SPIKE`

Detailed in §10. Two of them, both bounded, both blocking the slice's design but
not its authorization.

---

## 10. Required spikes

### Spike 1 — Can the running kernel load a gate definition from the generated contract tree?

| | |
|---|---|
| **Question** | Can `architecture/contracts/*.json`, as generated today, be loaded at runtime into the tracer's `GateDefinition`, or must the registry format change? |
| **Why it matters** | This is the pipeline's entire premise (assumption D), and it is currently unproven — the tracer reads its own YAML catalog, not the generated tree |
| **Options compared** | (a) load the generated registry directly; (b) add a generated projection shaped for runtime consumption; (c) keep two catalogs and reconcile |
| **Success criteria** | One gate definition loads from the committed contract tree, with no hand-editing, and a test asserts the loaded definition equals the document's declared content |
| **Failure criteria** | Loading requires editing a generated file, or the registry cannot express the gate without a schema change |
| **Maximum scope** | One gate, one loader module, ≤ 150 lines, in the tracer worktree. No CLI, no persistence changes |
| **Required evidence** | The executed test output, and the specific registry file and field path used |
| **Decision produced** | Whether Slice 1 loads from the contract tree (a), needs a runtime projection (b), or whether the compile-to-runtime premise needs an ADR of its own |
| **Timebox** | One session |

### Spike 2 — Is `ADR-0018`'s strict-typing obligation satisfiable as written?

| | |
|---|---|
| **Question** | Can the 245 outstanding `pyrefly` errors reach zero on a 54,663-line generator without a baseline, which `TYPECHECK-DEBT-001` forbids? |
| **Why it matters** | It gates CI, blocks any clean slice landing, and one bulk attempt has already been made and reverted on an invalid proof |
| **Options compared** | (a) per-owner incremental clearing (33 owners); (b) narrow the strict scope to product code, leaving the generator at a lower tier; (c) amend `ADR-0018` |
| **Success criteria** | Two owners cleared with a **valid** neutrality proof — generate one tree with the OLD script, one with the NEW, and diff **those two**, never a tree against itself |
| **Failure criteria** | Any tree difference, or effort per owner that extrapolates to an unacceptable total |
| **Maximum scope** | Two owners. Do **not** start with the largest |
| **Required evidence** | `pyrefly check --output-format json` before and after at named commits — never a count derived from prose output |
| **Decision produced** | Continue incrementally, or amend `ADR-0018`'s scope with measured justification |
| **Timebox** | One session |

Neither spike may be closed on preference, familiarity, or model reasoning. Both
require executed output (rule 4, rule 7).

---

## 11. Slice implementation and verification plan

To be written in full **after** `ADR-0021` is accepted and both spikes close.
The skeleton, so the shape is agreed now:

| Element | Content |
|---|---|
| **Slice goal** | One gate evaluation, driven by a compiled definition, against a real change in this repository |
| **Operational outcome** | A person or agent runs one command and receives an evidence-based verdict with a reason |
| **In scope** | CLI entry point; registry loader (per Spike 1); one gate, one rule; evidence record; append-only evaluation record; PASS/FAIL with reason; non-zero exit; CI wiring |
| **Explicitly excluded** | §8's exclusion list, unchanged. Any addition is a new slice |
| **Applicable requirements** | MAS §1 and §3, authored in Phase 1 |
| **Applicable ADRs** | `ADR-0021` (authorization), `-0007` (layout), `-0008` (TDD), `-0014`/`-0018`/`-0019` (toolchain), `-0015` (event schema) |
| **Behavioural contracts** | Required claim with satisfying evidence → `PASS`. Required claim with **no** evidence → `FAIL`, never a default. Evidence bound to a different subject digest → `FAIL`, not ignored. Verdict is a pure function of (definition, evidence) — no model is consulted |
| **Sad paths** | Missing evidence; stale evidence; wrong-subject evidence; malformed registry; unreadable store; store write fails mid-append; producer identity equals approver identity; two concurrent evaluations |
| **Acceptance criteria** | Every behavioural contract and every sad path has an executed, passing test. The command blocks a **real** change on this repository — demonstrated, not described. Two runs over identical inputs produce byte-identical records. Removing model access changes no verdict |
| **Test strategy** | `ADR-0008` TDD: failing test first, recorded. Unit (domain rules), integration (store), contract (registry loading), replay (journal determinism), plus one end-to-end run against a real commit |
| **Observability** | Every evaluation writes an append-only record carrying subject digest, gate id, rule id, verdict, and the evidence considered. Nothing inferred; nothing asserted by the party being evaluated |
| **Rollback / containment** | The lane governs only this repository and grants no authority. Rollback is reverting the commit; the gate is advisory in CI for its first N runs, then required — **and the promotion to required is itself the evidence that it works** |

**Phase 5 feedback, predeclared** — so it cannot be quietly skipped:

1. Run the tests; record the exact commands and their output.
2. Separate what was **executed** from what was **statically reviewed**. The
   project has been burned by this distinction three times (`HANDOFF.md:206-239`).
3. Document every failure and limitation, including anything the slice proved
   *wrong* about the architecture.
4. Update the MAS: promote sections from `PROVISIONAL` to `CONFIRMED` **only**
   where the slice produced evidence, and demote anything it contradicted.
5. Record the slice in the MAS §17 ledger.
6. Accept, reject or supersede `ADR-0021` and any ADR the slice disproved —
   superseding, never rewriting (rule 8).
7. Name the next smallest slice.

---

## 12. Recommended next action

**One decision from the owner, and nothing else is blocked by anything else.**

> **Authorize the bounded product-slice lane** — that is, accept in principle
> that Ranex may build one small end-to-end capability, governing only this
> repository, claiming no readiness, before `IMPLEMENTATION_START_READY` is
> declared.

Everything in this assessment follows from that one answer. If it is yes, the
work order is:

1. Draft `ADR-0021` from §9 for owner acceptance. *(no code)*
2. Author the Master Architecture Specification from §7, honestly labelled.
   *(no code)*
3. Run Spike 1, then Spike 2. *(bounded code, in a worktree, claiming nothing)*
4. Write the full Slice 1 plan from §11.
5. Implement Slice 1.

If it is no, say so plainly — and the honest consequence is that the project
continues producing governance tooling, because that is the only work its own
gates authorize. That is a legitimate choice; it should just be made knowingly
rather than by default.

Two small things worth doing regardless of the answer, because they are true
today and cost minutes:

- ~~Fix `README.md:241`~~ — **DONE 2026-07-31.** It now reads 20.
- ~~Record §1.4 as a finding against `ADR-0020`~~ — **DONE.** Recorded in the
  Master Architecture Specification §11.2 technical-debt table: the gate's
  declared set omits the root `README.md`, and its `stated_count_stale` check is
  a regex matching exactly one row in one file.

**Status of this document, 2026-07-31.** Its eleven sections are delivered and
its recommendations are executed or superseded. The map it proposed now exists
at [`../MASTER_ARCHITECTURE_SPECIFICATION.md`](../MASTER_ARCHITECTURE_SPECIFICATION.md);
the slice it proposed is defined at
[`2026-07-31-walking-skeleton-definition.md`](2026-07-31-walking-skeleton-definition.md);
both spikes are executed at
[`2026-07-31-spike-01-and-02-results.md`](2026-07-31-spike-01-and-02-results.md).
This file is retained as the assessment of record, **not** as a live plan.
