# Ranex Master Architecture Specification

**The map. Not a decision, not a gate, not authority.**

This document shows the whole intended system while separating what is known
from what is hypothesis. It is the top of the delivery hierarchy: product
requirements → **this map** → architecturally significant requirements →
current-slice ADRs → contracts → acceptance criteria → one small slice →
evidence → back into this map.

| | |
|---|---|
| Version | `1.1.0` |
| Created | 2026-07-31 |
| Last evidence update | 2026-07-31, Slice 1 Phase 5 |
| Status | Working document. **Not digest-pinned**, deliberately — see §0.3 |
| Structure | [arc42](https://arc42.org/overview) §1–12, plus §13. See §0.4 for licensing |
| Authority | **None.** This document grants nothing, gates nothing, and supersedes no ADR |

---

## §0 How to read this

### 0.1 Status vocabulary

Every section header and every material claim carries one label. A claim with
no label inherits its section's.

| Label | Means |
|---|---|
| `CONFIRMED` | Supported by a stated requirement **or by executed implementation evidence** |
| `PROVISIONAL` | Current direction. Written down, reasoned, **not validated by anything running** |
| `UNRESOLVED` | A real decision is still required. Names what would settle it |
| `OUT-OF-SCOPE` | Not needed for the current delivery horizon |

**An accepted ADR does not make a thing `CONFIRMED`.** Twenty-one ADRs are accepted
here; almost nothing is `CONFIRMED`. Acceptance means the decision was made, not
that it was proven. Confusing the two is the failure this document exists to
prevent.

### 0.1a Governance — owner decision, 2026-07-31

**Architecture is no longer the bottleneck. Implementation evidence is.**

This map is **frozen as the working map**. It is not perfect and does not need to
be. It needs to be internally consistent, navigable, and sufficient to guide
implementation. Unknowns stay marked rather than eliminated.

**ADR expansion is frozen.** An ADR may be created only if **all four** hold:

1. the current implementation slice depends on the decision;
2. delaying it **blocks** implementation;
3. it is architecturally significant;
4. enough evidence exists to justify accepting it.

If any is false, **do not create the ADR**. Instead record the uncertainty here,
why it is deferred, and the trigger that reopens it — as §11.1 already does.

**The engineering loop:**

```
this map → smallest meaningful slice → only the blocking ADRs
  → behavioural contracts → acceptance criteria → implementation
  → automated verification → evidence → update this map
  → supersede or create ADRs only if evidence requires → repeat
```

**Eight standing rules:**

| # | Rule |
|---|---|
| 1 | This map is the complete system map. ADRs are decision records. **ADRs are not the architecture** |
| 2 | No ADR unless it directly blocks the current slice |
| 3 | Implementation slices outrank speculative architectural expansion |
| 4 | Every slice validates **at least one** architectural assumption. None → too small. Many unrelated → too large |
| 5 | Every completed slice produces evidence. **Evidence is the only valid reason to modify accepted architecture** |
| 6 | Never claim verification without execution. Implementation, static review, reasoning and executed verification are **not equivalent** |
| 7 | No infrastructure because it might be useful — no plugins, orchestration, queues, event buses, caches or generalized abstractions until a slice demonstrates need |
| 8 | When evidence invalidates an ADR, **supersede it with the evidence referenced**. Never silently rewrite |

### 0.2 What this document is not

- Not a specification you can implement from. It is deliberately shallow in
  places, because depth without evidence is the thing being avoided.
- Not authority. `ADR-0012` still governs what may be built.
- Not a replacement for the ADRs. It is the map they attach to.

### 0.3 Why it is not digest-pinned

An ADR here is compiled into 46 registries; `ADR-0013`'s digest alone appears
102 times. Every correction therefore costs a full contract-tree cascade. That
tax is correct for a *decision*, which should be expensive to change, and wrong
for a *map*, which must stay current cheaply. Keeping this document outside the
digest chain is what makes rule 9 — keep the map current — affordable.

### 0.4 On arc42

The twelve section headings follow arc42 (Starke & Hruschka), used here as a
**conformance checklist** to avoid omitting a section, not republished as an
adaptation. arc42 is licensed CC BY-SA 4.0; whether to adopt-and-attribute
instead is an open owner decision recorded in §11 as `RISK-08`.

---

## §1 Introduction and Goals

### 1.1 What Ranex is — `PROVISIONAL`; one bounded mechanism `CONFIRMED`

A governance harness that makes unreliable AI agents produce reliable software.
Rules live in architecture documents, compile into registries, schemas and
executable checks, and are enforced by code the agent never reads and cannot
argue with.

**The product thesis, stated so it can be falsified:**

> Rules compiled into code change what an agent produces. Rules written in a
> prompt do not.

`UNRESOLVED` as a product thesis. Slice 1 executed one narrower proposition:
the advisory YAML action gate returned `FAIL` for absent evidence, still
returned `FAIL` for a present record whose command exit was nonzero, and
returned `PASS` only when both required records carried exit zero for the exact
subject field. A Phase 5 integrity check then showed that `HEAD` contains zero
Slice 1/project files while the commands ran against their untracked working
tree versions. This confirms only the bounded field-to-verdict mechanism, **not
evidence support for the exact execution subject**. It did **not** compare an
agent governed by code with an agent governed by a prompt, change an observed
agent output, authenticate the evidence producer, or install a merge blocker.
The thesis therefore remains open; see §13 and the Slice 1 evidence record.

### 1.2 Product requirements — `PROVISIONAL`, and newly authored

**This layer did not exist before 2026-07-31.** Every ADR was anchored to an
architecture anchored to nothing above it. The following is derived from
`README.md` and owner statements and **requires owner confirmation**; until
then, treat each as a hypothesis about what Ranex owes a user.

| ID | Requirement | Status |
|---|---|---|
| `PR-01` | A non-technical owner can state intent in plain language and receive work that matches it, or an explicit refusal saying what is missing | `PROVISIONAL` |
| `PR-02` | No model output is ever an authorization. A gate passes on evidence or does not pass | `CONFIRMED` only for the Slice 1 advisory gate: it ran with no recognized model credential variables and derived the verdict from evidence fields; authority and evidence authenticity remain `PROVISIONAL` |
| `PR-03` | Absence blocks. An unresolved decision stops work rather than defaulting | `CONFIRMED` only for the two claims in the Slice 1 action gate; not generalized to readiness or the rest of the system |
| `PR-04` | The identity that produces work cannot approve it | `PROVISIONAL` |
| `PR-05` | Every landed change carries its authority, its evidence, and the digest of the exact subject reviewed | `PROVISIONAL` |
| `PR-06` | Every assumption an agent made is recorded, whether or not it was correct | `PROVISIONAL` |
| `PR-07` | An agent never needs to read an enforced rule, so the rulebook costs no context | `PROVISIONAL` |
| `PR-08` | A governed project's written records cannot silently drift from observable fact | `PROVISIONAL` — deferred, `RFC-0009` |

### 1.3 Major system capabilities

| Capability | What it does | Status |
|---|---|---|
| Contract compilation | Architecture documents → registries, schemas, executable checks | **`CONFIRMED`** — 54,823 lines (`wc -l scripts/architecture/{generate,validate}_contracts.py`, 2026-07-31); validator `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`; generator proven idempotent by diffing consecutive generations |
| Deterministic gate evaluation | Evidence + gate definition → verdict, no model consulted | **`CONFIRMED` for the Slice 1 YAML action gate's field-to-verdict function only** — executed absent/nonzero/zero sequence and byte-identical repeat; the commands ran on dirty bytes absent from the named `HEAD` tree, and the gate is **not wired to the compiled tree** |
| Governed execution | Exact grants, fenced leases, isolated writes | `PROVISIONAL` — partially in the tracer |
| Append-only evidence journal | Immutable records, replayable, crash-safe | `PROVISIONAL` — Slice 1 has a SQLite hash-chain journal and identical-record execution, but no executed mid-append failure test and no genuinely concurrent evaluation test |
| Readiness assessment | Two noncompensating tiers, 21 gates | `PROVISIONAL` — fully specified (`ADR-0012`), **never executed once** |
| Work lifecycle | 10 work classes, 44 state axes, 376 transitions | `PROVISIONAL` — specified, no runtime |
| Capability levelling | 41 capabilities, 0–4, earned by recorded work | `PROVISIONAL` — all 41 `NOT_ASSESSED` |
| Fleet orchestration | Multi-worker dispatch, runtime adapters | `PROVISIONAL` — `ADR-0011`, no runtime |
| Intent capture | Plain-language intent → specification | `UNRESOLVED` — `RFC-0002` undecided |
| Record freshness as a product | Staleness detection for governed projects | `OUT-OF-SCOPE` this horizon — `RFC-0009` deferred |

---

## §2 Constraints

### 2.1 Binding — `CONFIRMED`

| Constraint | Source |
|---|---|
| Python is the implementation language; performance escape hatch defined | `ADR-0014` |
| `pyrefly` 1.1.1, strict preset, no baseline permitted | `ADR-0018` |
| `uv` is the toolchain manager | `ADR-0019` |
| TDD is the default discipline on production paths | `ADR-0008` |
| Modular DDD repository organization | `ADR-0007` |
| Upstream authorship, copyright and history preserved permanently | `NOTICE.md` |
| `LICENSE-RANEX.md` is personal-use, all rights reserved | commercial optionality preserved |

### 2.2 Process constraints — `CONFIRMED`

- **No product code may be written** before `IMPLEMENTATION_START_READY`
  (`ADR-0012:72`, and the machine contract at `:656-657`). Neither tier is
  declared. This is the binding constraint on all delivery.
- One bounded `PRE_READINESS_TOOLING_TRACER` lane may build tooling and may
  produce readiness evidence on tooling subjects (`ADR-0012:57-76`).
- A second `PRE_READINESS_PRODUCT_SLICE` lane is **proposed** (`RFC-0010`
  v2.2.0) and **not accepted**.
- `BOOTSTRAP-AUTH-001` is a bounded prose exception for Slice 1 only. As of the
  Phase 5 audit it remains `ACTIVE`: not every declared failure mode has an
  executed test, the source tree exceeds its size bound, and the runtime
  readiness-quarantine claim is not implemented. It authorizes no second slice.

### 2.3 Environmental — `CONFIRMED`

- Local-first. No hosted service exists.
- Two readiness gates require named external model reviewers (HY3, DeepSeek).
  Availability is unreliable and has already blocked work.
- The `origin` remote is a **public** GitHub repository.

---

## §3 Context and Scope

### 3.1 System context — `PROVISIONAL`

```
   ┌────────────┐        intent, decisions        ┌──────────────────┐
   │   Owner    │────────────────────────────────▶│                  │
   │(non-tech.) │◀────── plain-language state ────│                  │
   └────────────┘                                 │      RANEX       │
                                                  │                  │
   ┌────────────┐   proposals + evidence          │  compile · gate  │
   │ AI workers │────────────────────────────────▶│  record · refuse │
   │  (fleet)   │◀────── task-minimal context ────│                  │
   └────────────┘         and verdicts            └────────┬─────────┘
                                                           │
   ┌────────────┐                                          │
   │  Reviewers │◀──── read-only review requests ──────────┤
   │  (models)  │───── verdicts as evidence, never ────────┤
   └────────────┘      as authority                        │
                                                           ▼
                                            ┌──────────────────────────┐
                                            │ git · CI · model providers│
                                            └──────────────────────────┘
```

### 3.2 Scope boundary — `CONFIRMED`

**In scope:** governance of software work; deterministic enforcement; evidence
custody; the work lifecycle.

**Explicitly not:** a general-purpose assistant; an autonomy experiment; a
prompt library; an inference-margin business (`ADR-0011` forecloses it).

### 3.3 External integrations

| Integration | Purpose | Status |
|---|---|---|
| `git` | Subject identity, provenance, worktree isolation | `PROVISIONAL` |
| CI (GitHub Actions) | The only enforcement layer an agent cannot bypass today | `PROVISIONAL` — the workflow file exists and its steps run locally. **Its remote status is not verifiable from this machine**: `gh run list` returns runs from an unrelated repository, so "green" is an inherited claim, not an executed one |
| Model providers | Workers and reviewers | `PROVISIONAL` — availability unreliable |
| OSCAL / FedRAMP | Machine-readable authorization packages | `OUT-OF-SCOPE` this horizon; see `RISK-07` |

---

## §4 Solution Strategy

### 4.1 The central mechanism — `PROVISIONAL`

```
Architecture documents  ──generate──▶  Registries · Schemas · Checks
   (humans decide)                          (machines read)
                                                  │
                                                  │ enforce
                                                  ▼
Agents work ──proposal + evidence──▶  Deterministic gate ──▶ Landed
                                       (evidence, not confidence)
```

**The critical unproven link is `generate → enforce`.** `CONFIRMED`: the
generator produces the registries. `UNRESOLVED`: the Slice 1 runtime does not
read them. The only `architecture/contracts/` match under `src/`, `tests/` and
`governance/` is the Slice 1 loader's docstring stating that it deliberately
loads authored YAML instead. This scoped search was executed during Phase 5;
it does not claim absence outside those runtime paths.

`SPIKE-01` then showed this link cannot be closed by wiring at all — see §11.1
`RISK-02`.

### 4.2 Strategy decisions — `CONFIRMED` as decisions, `PROVISIONAL` as designs

Deterministic-over-probabilistic enforcement; fail-closed (`NOT_ASSESSED` is
never a pass); evidence bound to exact subject digests; separation of producer
and approver; local-first before distributed.

---

## §5 Building Block View

### 5.1 Containers — `PROVISIONAL` unless noted

| Container | Responsibility | Status |
|---|---|---|
| Contract compiler (`scripts/architecture/`) | Generates registries, schemas, fixtures; validates the tree | **`CONFIRMED`** — 54,823 lines, executed |
| Ranex kernel (`src/ranex/`) | Domain, application, adapters per `ADR-0007` | Existence and the bounded gate path are **`CONFIRMED`** on this branch; broader kernel design remains `PROVISIONAL`. Physical size is 1,050 lines, exceeding Slice 1's 1,000-line bound |
| CLI | Owner and operator entry point | **`CONFIRMED` advisory only** — `PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner` executed; no CI job invokes it and it is not a required merge blocker |
| Evidence store | Append-only journal | `PROVISIONAL` — SQLite implementation exists and identical appends replayed, but required failure-mode evidence is incomplete |
| Fleet control plane | Worker dispatch, adapters | `OUT-OF-SCOPE` this horizon |
| Desktop / web surface | Owner interaction | `OUT-OF-SCOPE` this horizon |

### 5.2 Bounded contexts — `PROVISIONAL`

Thirty-four, registered in `architecture/contracts/contexts.json` and fixed by
`ADR-0003`/`ADR-0009`. Grouped by role:

| Group | Contexts |
|---|---|
| **Execution core** | `governed_execution`, `policy`, `assurance`, `work_management` |
| **Identity & authority** | `identity_access`, `module_governance`, `qualification` |
| **Product & delivery** | `product_definition`, `delivery`, `release_management`, `service_management` |
| **Configuration & provenance** | `configuration_management`, `provenance_compliance`, `artifact_management`, `upstream_sync`, `migration`, `compatibility` |
| **Process & assurance** | `process_assurance`, `analytical_review`, `effectiveness` |
| **Agent operations** | `agent_collaboration`, `routing`, `context_compilation`, `instruction_registry`, `workspace`, `repository_intelligence` |
| **Supporting** | `knowledge`, `interaction_history`, `scheduling`, `resource_governance`, `supplier_governance`, `operations`, `backup_restore`, `extension_host` |

**Honest note:** 34 contexts for a system with one incomplete product slice is a
large surface. On this branch, Slice 1 contains substantive implementation in
`governed_execution` and `policy`; `assurance` is namespace scaffolding and
`work_management` is absent. The remaining registered contexts are
`PROVISIONAL` in the strongest sense: named and bounded, never built here.

### 5.3 Slice 1 components with executed evidence — bounded `CONFIRMED`

The branch now contains an executed path through CLI, composition root, YAML
slice-gate loader, pure verdict function and optional SQLite journal. The live
four-step evidence sequence and identical-input replay are the implementation
evidence; the 36 passing tests are verification, not the sole basis for this
status. The richer `gate_catalog_loader.py`, `policy/domain/gates.py`, and
identity model are present but are not on the Slice 1 CLI path.

| Component | Path under `src/ranex/` | Phase 5 status |
|---|---|---|
| CLI and exact Git-tree subject digest | `cli/main.py` | Executed |
| Composition root | `bootstrap/composition.py` | Executed through CLI |
| Action-gate YAML loader | `policy/adapters/configuration/yaml/slice_gate_loader.py` | Executed; deliberately separate from compiled readiness gates |
| Deterministic verdict | `governed_execution/domain/verdict.py` | Executed for absent, nonzero and passing evidence |
| SQLite hash-chain journal | `governed_execution/adapters/persistence/sqlite/journal.py` | Identical records and chain verification executed; failure coverage incomplete |
| Canonical JSON/SHA-256 | `foundation/canonical.py` | Executed through subject and record digests |

### 5.4 Data ownership — `PROVISIONAL`

Each of the 34 contexts owns a disjoint data set; registered in
`architecture/contracts/data-ownership.json` (34 rows). Load-bearing examples:

| Context | Owns |
|---|---|
| `governed_execution` | Runs, pinned workflows, gate bindings, authority grants, permit issuance, effect intents and outcomes |
| `policy` | Roles, authorization-eligibility rules, risk lanes, policy packages, waivers |
| `assurance` | Claims, evidence envelopes, checker results, evidence snapshots, `GateEvaluation` |
| `identity_access` | Identities, authentication, sessions, nonces, data classification |
| `work_management` | Projects, `WorkItemStatus`, work class, queues, dependencies, debt records |
| `configuration_management` | CI registry, content-addressed baselines, traceability graph |

---

## §6 Runtime View

### 6.1 Principal flow — one change from intent to landed — `PROVISIONAL`

```
Intent ─▶ Clarify ──unknowns──▶ Ask owner ─┐
            │                              │
          clear                            └─▶ recorded as owner's answer
            ▼
      Specification ─▶ Gate: evidence sufficient?
                          │              │
                    insufficient      sufficient
                          ▼              ▼
                      BLOCKED     Governed execution
                     (records          (isolated)
                      what is             ▼
                      missing)     Work + typed evidence
                                          ▼
                                  Independent review
                                   (different identity)
                                          ▼
                              Gate: findings resolved?
                                     │        │
                                  no │        │ yes
                                     ▼        ▼
                                 BLOCKED   Human decision
                                              ▼
                                           LANDED
```

`UNRESOLVED` as an end-to-end product flow. Slice 1 executed only the narrow
middle step: an operator invoked an advisory gate over `HEAD`, received an
accurate refusal, supplied evidence records, and received a pass. No intent
capture, governed execution, independent review, human authority, landing, or
required enforcement step executed.

### 6.2 Compilation flow — **`CONFIRMED`**

```
ADRs + operating model ──parse marked blocks──▶ generate_contracts.py
   ──▶ 46 registries + 158 schemas + fixtures ──▶ validate_contracts.py
   ──▶ validation-report.json  status=PASS
       scope=EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY
       runtime_validation=NOT_ASSESSED
```

Deterministic and idempotent: same inputs, same tree digest. Verified by
execution.

### 6.3 The missing flow — `UNRESOLVED`

```
46 registries ──────▶ ??? ──────▶ running enforcement
                       ▲
              never built, never tested
```

This is the single most important gap in the system. Everything in §6.1 assumes
it. See `SPIKE-01` (§11.3).

---

## §7 Deployment View

### 7.1 Today — `CONFIRMED`

| Node | Runs | Status |
|---|---|---|
| Developer machine | Generator, validator, freshness check, tracer tests | Working |
| GitHub Actions | Regenerate → prove no drift → validate → freshness → concurrency | Workflow present; remote run and required-check status not assessed in Slice 1 Phase 5 |
| Slice 1 CLI | Advisory `gate evaluate` over one repository/ref | Working locally; not invoked by CI and not required |

**There is no deployed Ranex.** No service or daemon exists. The CLI runs from
the source tree through `uv`; it is not an installed enforcement boundary.

### 7.2 Intended — `PROVISIONAL`

Local-first single-machine (`ADR-0005`). Hosted or multi-tenant operation is
`OUT-OF-SCOPE` and would require re-deciding `ADR-0005` and `ADR-0011`.

---

## §8 Crosscutting Concepts

### 8.1 Trust and security boundaries — `PROVISIONAL`

| Boundary | Rule | Status |
|---|---|---|
| Agent ↔ checker | An agent never reads an enforced rule and cannot alter a verdict | `PROVISIONAL` — CI is the only real instance today |
| Producer ↔ approver | The identity producing work cannot approve it | `PROVISIONAL` — a unit test covers the pure verdict, but no independent real producer/approver workflow executed |
| Model ↔ authority | A model verdict is evidence, never authority | `PROVISIONAL` |
| Party ↔ own obligation | A party may not discharge an obligation that constrains it (`ADR-0017:65`) | `PROVISIONAL` |
| Enforcement ↔ inference | **No enforcement check invokes a model.** Removing model access must change no verdict | `CONFIRMED` for the Slice 1 path only: it passed with zero recognized model credential variables present and has no model/network client import |
| Repository confinement | Work governs only the repository it is scoped to | `UNRESOLVED`, with executed counter-evidence — the helper rejects absolute/traversal/remote strings, but the CLI never calls it and a second-repository evaluation returned `PASS` |

**`CONFIRMED` counterexample worth keeping visible:** the existing record-freshness
check *infers a claim from prose with a regex*, violating the
enforcement-not-inference boundary in its only implementation. Principles are
not self-enforcing.

### 8.2 Observability boundaries — `PROVISIONAL`

Recorded: every transition with its guard, authority, evidence and subject
digest; every gate evaluation with the rule that failed; every assumption an
agent made.

Never recorded as fact: anything a model asserted about its own work; any
verdict not derived from observable evidence.

`UNRESOLVED` for the intended system. Slice 1 emits a verdict and reason to
stdout and can append an evaluation to SQLite. Its default command does not
enable the journal, its record does not carry `subject_lane`, and no readiness
runtime consumes it.

### 8.3 Determinism — `PROVISIONAL`

Canonicalization is intended to be RFC 8785; digests are SHA-256. Identical
inputs must yield identical outputs, byte for byte. **`CONFIRMED`** for the
generator and for the bounded Slice 1 CLI/evaluation record: two executed runs
had identical stdout, stderr and journal records, and the journal chain
verified. This does not generalize to unbuilt runtime flows.

---

## §9 Architectural Decisions

Twenty-one accepted ADRs. Full text in `decisions/`. This is the map's index of
which decisions constrain which section.

| ADR | Decides | Constrains |
|---|---|---|
| `ADR-0001` | Established SDLC governs AI work | §4 |
| `ADR-0002` | Retire the legacy implementation guide | §0 |
| `ADR-0003` | Accept target architecture and authority kernel | §5.2 |
| `ADR-0004` | Initial quality-attribute baselines | §10 |
| `ADR-0005` | Local/static orchestration defaults | §7 |
| `ADR-0006` | Fixed decisions and fitness crosswalk | §9 |
| `ADR-0007` | Modular DDD repository organization | §5.1 |
| `ADR-0008` | TDD as default discipline | §2.1 |
| `ADR-0009` | Boundary fit, dependency edges, feedback fitness | §5.2 |
| `ADR-0010` | Bound inherited Hermes test layout migration | §11 |
| `ADR-0011` | Centralize worker orchestration and runtime adapters | §5.1 |
| `ADR-0012` | Separate implementation-start and production readiness | §2.2 |
| `ADR-0013` | Promote Hermes research obligations | §11 |
| `ADR-0014` | Implementation language and performance escape hatch | §2.1 |
| `ADR-0015` | Canonical workflow/event schema and upcaster policy | §6 |
| `ADR-0016` | Resolve five implementation-start owner decisions | §2 |
| `ADR-0017` | Record resolved owner decisions | §8.1 |
| `ADR-0018` | Select the static type checker | §2.1 |
| `ADR-0019` | `uv` as the Python toolchain manager | §2.1 |
| `ADR-0020` | Record-freshness self-check | §8.1 |
| `ADR-0021` | Limit ADR-0010 to inherited lineage | §11 |

**Open proposals (no authority):** `RFC-0002` Spec Kit adaptation, `RFC-0003`
session continuity, `RFC-0007` local-only corpus, `RFC-0009` record freshness as
product, `RFC-0010` product-slice lane (`2.2.0`; `1.0.0` and `2.0.0` both rejected by
independent review; blocked on authentication issuance).

**Migration note:** map content currently living inside `ADR-0003`, `ADR-0004`,
`ADR-0007`, `ADR-0009`, `ADR-0011` and `ADR-0012` belongs in §5, §7 and §10 of
this document. Those ADRs should shrink to their actual decisions. Not yet done;
tracked as `RISK-09`.

---

## §10 Quality Requirements

### 10.1 Architecturally Significant Requirements — `PROVISIONAL`, newly authored

The requirements that actually constrain structure. Newly written; **require
owner confirmation**.

| ID | ASR | Drives |
|---|---|---|
| `ASR-01` | A verdict must be reproducible: identical inputs yield identical verdicts, with no model invoked | Determinism (§8.3); rules out model-in-the-loop enforcement |
| `ASR-02` | Absence of evidence must block, never default | Fail-closed everywhere; forbids optional fields with permissive defaults |
| `ASR-03` | Evidence must bind to an exact subject digest, so stale evidence is not evidence | Content-addressed storage; digest cascade |
| `ASR-04` | The enforcement path must be unreachable by the governed agent | CI-or-equivalent boundary; forbids in-process trust |
| `ASR-05` | An agent must not need to read an enforced rule | Rules compile to checks, not prompts; caps context cost |
| `ASR-06` | Records must be append-only and replayable | Journal + hash chain; forbids destructive update |
| `ASR-07` | A non-technical owner must be able to act without reading the corpus | Plain-language surfaces; a single routing entry point |

### 10.2 Quality attributes — `PROVISIONAL`

Targets in `ADR-0004`. **None measured.** Any number quoted from `ADR-0004`
today is a target, not an observation.

### 10.3 Scalability assumptions — `PROVISIONAL`, none measured

| Assumption | Evidence |
|---|---|
| The full corpus exceeds ten million tokens and can never fit a context window | Asserted, not measured |
| Task-minimal context keeps worker cost bounded | No runtime; unmeasured |
| A single machine suffices for the current horizon | `ADR-0005`; untested under load |
| Compilation scales with corpus growth | **Counter-evidence:** 54,823 lines of generator for 46 registries |

---

## §11 Risks and Technical Debt

### 11.1 Unresolved architectural risks

| ID | Risk | Status | Settled by |
|---|---|---|---|
| `RISK-01` | **The broad product thesis remains untested.** Slice 1 confirmed that one authored YAML action gate changes its verdict when evidence is absent, nonzero or successful. It did not test compiled-tree rules, a prompt comparator, or changed agent output | `UNRESOLVED`, narrowed | A required enforcement experiment observing agent output, after authorization |
| `RISK-02` | **The compiled tree has no runtime consumer** — and `SPIKE-01` shows wiring cannot fix it. The registry holds *readiness* gates (`evidence_role` → tier); the kernel needs *action* gates (`action` → rules). Five fields would have to be invented. Someone must decide what the action gates **are** | `UNRESOLVED`, **sharpened** | An authored decision, when a slice needs it |
| `RISK-03` | ~~Strict typing may be unsatisfiable~~ | **CLOSED by `SPIKE-02`** | Satisfiable incrementally with a valid proof: 245 → 243, old-script tree diffed against new-script tree, identical. 243 remain as ordinary debt |
| `RISK-04` | **Compilation may not scale.** 54,823 lines to produce 46 registries | `UNRESOLVED` | Growth measurement over the next slices |
| `RISK-05` | **Readiness may be unreachable in practice.** Two gates require named external reviewers with known availability failures | `UNRESOLVED` | Owner decision on reviewer substitution |
| `RISK-06` | **Copyrighted PDFs remain reachable** in the object database via `refs/codex/**` (15 refs, 11 PDF blobs). `origin` is public. `git push --all/--mirror` would publish them | `UNRESOLVED` | Owner decision; **never use those flags** |
| `RISK-07` | Monetization undecided; FedRAMP requires machine-readable packages by 2026-09-30 and OSCAL is the format | `UNRESOLVED` | Owner decision |
| `RISK-08` | arc42 is CC BY-SA 4.0; adopting the template as an adaptation in a public repo carries ShareAlike | `UNRESOLVED` | Owner decision (§0.4) |
| `RISK-09` | Map content is trapped inside digest-pinned ADRs, making the map expensive to correct | `UNRESOLVED` | Migration into §5/§7/§10 |
| `RISK-10` | **Slice 1 evidence is unauthenticated JSON and not bound to the executed bytes.** The gate checks claim ID, caller-supplied subject digest and recorded exit code, but does not execute the named command, authenticate its producer, require a clean worktree, or isolate the command at the named Git tree. Phase 5 commands ran on untracked files absent from `HEAD` | `CONFIRMED` defect exposed by Slice 1 | Correct the existing slice's evidence-production/subject-binding path |
| `RISK-11` | **The first slice is not dischargeable as implemented.** Its actual change was outside the gate subject; duplicate rule IDs are accepted; mid-append and real concurrency tests are absent; confinement is not wired; runtime readiness quarantine is absent; and 1,050 source lines exceed the 1,000-line bound | `CONFIRMED` by Phase 5 audit | Correct the existing Slice 1 under its still-active authorization, then repeat Phase 5 |

### 11.2 Technical debt — all `CONFIRMED` by execution

| Debt | Measured |
|---|---|
| **243** strict type errors in architecture tooling | Measured by `uv run --group typecheck pyrefly check` from `/home/soultransit/devtony/ranex/scripts/architecture`; exit 1. The requested product invocation, `uv run --with pyrefly==1.1.1 pyrefly check` from the repository root, reports **0 errors** and exits 0 |
| The type-check gate has **no CI step** | `ADR-0018` declares it; no `pyrefly` step exists at `HEAD` |
| The count is invocation-dependent | **243** for architecture tooling from `scripts/architecture/`; **0** for product code from the repository root with `--with pyrefly==1.1.1`. They are different configured projects and scopes, not competing measurements of one tree |
| Three stale figures | `README.md:241` says 14 ADRs (20 exist); `pyproject.toml:23` says 265 errors (245); `ADR-0018:79-81` records the command with no working directory |
| The freshness check is regex-over-prose | Matches exactly one row in one file; violates the enforcement-not-inference boundary |
| 173 unconstrained schema arrays | Across 121 field names, each marked `UNDECIDED` |
| 20 owner decisions still unresolved | **The machinery now exists** (`ADR-0017`, implemented 2026-07-31). The count reads 20 because nothing is resolved, and it is now *derived* rather than pinned. Resolving a row requires minting a `HumanDecisionV1` into `architecture/records/owner-decisions/` and accepting the `ADR-0013` digest cascade |

### 11.3 Bounded spikes

**`SPIKE-01` — can the kernel load a gate definition from the compiled tree?**
Settles `RISK-02`. Options: load the registry directly / add a runtime
projection / keep two catalogs. Success: one gate loads from the committed tree
with no hand-editing, and a test asserts the loaded definition equals the
document's declared content. Failure: loading requires editing a generated file,
or the registry cannot express the gate without a schema change. Max scope: one
gate, one loader, ≤150 lines, in a worktree. Timebox: one session.

**`SPIKE-02` — is `ADR-0018`'s obligation satisfiable?** Settles `RISK-03`.
Success: two owners cleared with a **valid** neutrality proof — generate a tree
with the OLD script and one with the NEW, and diff *those two*, never a tree
against itself. Evidence: `pyrefly --output-format json` at named commits, with
the working directory recorded. Max scope: two owners, not the largest.

Neither may be closed on preference, familiarity, or model reasoning.

---

## §12 Glossary

| Term | Meaning |
|---|---|
| **ADR** | Accepted decision record. Compiled into the contract tree; expensive to change, by design |
| **RFC** | Proposal. Carries no authority until promoted to an ADR |
| **Contract tree** | `architecture/contracts/` — 46 generated registries. Derived, never hand-edited |
| **Exact subject** | The precise bytes a piece of evidence refers to, identified by digest |
| **Gate** | A deterministic check yielding `PASS`/`FAIL`/`UNKNOWN`/`CONFLICT`/`NOT_APPLICABLE` |
| **Noncompensating** | A passing gate cannot make up for a failing one |
| **`NOT_ASSESSED`** | No attempt was made. Never a pass |
| **Readiness tier** | `IMPLEMENTATION_START_READY` (may begin staged implementation) or `PRODUCTION_READY` (may request release authority). Neither declared |
| **Lane** | A bounded pre-readiness work channel with explicit allowed and forbidden scope |
| **Slice** | One small end-to-end capability crossing all layers; a walking skeleton |
| **Tracer** | The R&D kernel in a worktree, claiming no authority |
| **FACT / INFERENCE / UNVERIFIED** | Epistemic labels. `FACT` requires an executed command or a cited source |

---

## §13 Slice Ledger

Every delivered or verification-attempted slice, what it validated, and **what
it disproved**. A row marked incomplete is evidence, not a delivery claim.

| Work | Delivered | Validated | Disproved | Map sections changed |
|---|---|---|---|---|
| `SPIKE-01` | Executed load attempt, registry → kernel | — | **Option "load the registry directly"**. Registry and kernel gates are different concepts sharing a word | §11.1 `RISK-02` restated |
| `SPIKE-02` | 2 type errors cleared with a valid neutrality proof | Incremental typing is feasible; `ADR-0018` needs no amendment | **The bulk method**, again — and the invalid self-comparison proof | §11.1 `RISK-03` closed |
| `ADR-0017` machinery | Typed digest-bound owner-decision resolution; derived unresolved count; empty canonical record root; 11 acceptance cases | Fail-closed generalisation without relaxation (`OWNER-RESOLVE-007` case retained) | — | §11.2 debt row |
| `Slice 1` — Phase 5, **not closed** | Walking-skeleton source, one advisory CLI action gate, evidence records and SQLite journal; 36 tests pass; bootstrap authorization remains `ACTIVE` | The gate distinguishes absent, nonzero and zero-exit fields; identical inputs produce identical output/records; the live validator now activates test and source topology checks | The successful records were bound to `HEAD`, which contains zero Slice 1/project files, while commands ran on untracked working-tree bytes. ADR-0008/ADR-0010 were jointly unsatisfiable before ADR-0021; empty directories hid governance contracts; `NOT_ASSESSED` flowed into `PASS`; compiled readiness gates cannot supply action-gate fields. Completion claims were also disproved by missing failure-mode tests, unwired confinement, no executable quarantine, and 1,050 > 1,000 source lines | §1.1, §4.1, §5.1–5.3, §6.1, §8.1–8.3, §11.1–11.2 |

No product slice has been discharged. Slice 1 implementation exists under the
still-active bounded bootstrap exception; the other rows are tooling-lane work.

### Slice 1 — implemented, Phase 5 **not closed**

**"One governed change, gated by evidence, in this repository."** A walking
skeleton (Cockburn, 2000; the *tracer bullet* of this project's own reference
corpus).

```
change proposed → CLI → gate controller loads ONE authored YAML gate definition
  → domain rule: absence blocks → append-only evaluation record
  → PASS/FAIL naming the failing rule → automated tests
```

Validates only the bounded verdict mechanism inside `RISK-01`; it confirms
`RISK-02` remains open because this gate is YAML-authored and reads no compiled
registry. It may **not** become a required merge blocker under this slice.

**Closure blockers found by execution and inspection:** the gate subject omits
the entire untracked Slice 1 change and its verification files; duplicate rule IDs are
accepted; no mid-append-failure test exists; the concurrency test is sequential;
the confinement helper is not wired and a second repository passed; the record
has no `subject_lane` and `QUARANTINE-001` remains only in rejected draft
`RFC-0010`; and `src/ranex/` contains 1,050 physical/net-new lines against the
1,000-line bound. `BOOTSTRAP-AUTH-001` therefore remains `ACTIVE`.

Term 5 still controls the future: the permanent authorization issuance
mechanism is a **required prerequisite before any second implementation slice**.

---

## Maintenance

Update this document when a slice lands, when an ADR is accepted or superseded,
or when a `PROVISIONAL` claim gains or loses evidence. Promote to `CONFIRMED`
**only** on executed evidence; demote whatever a slice contradicts. Record the
command and its working directory beside every number.
