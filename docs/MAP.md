# Ranex Map

**The map. Not a decision, not a gate, not authority.**

This document shows the whole intended system while separating what is known
from what is hypothesis. It is the top of the delivery hierarchy: problem →
product requirements → **this map** → architecturally significant requirements →
bill of materials → current-slice ADRs → one small slice → evidence → back into
this map.

| | |
|---|---|
| Version | `2.1.0` |
| Created | 2026-07-31, as `MASTER_ARCHITECTURE_SPECIFICATION.md` in the pre-reset tree |
| Last revised | 2026-08-03 — **thesis change** (`2.0.0`) and **bounded TOGAF adoption** (`2.1.0`), see §0.5, §0.6 |
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

**An accepted ADR does not make a thing `CONFIRMED`.** Acceptance means the
decision was made, not that it was proven. Confusing the two is the failure this
document exists to prevent.

### 0.2 What this document is not

- Not a specification you can implement from. It is deliberately shallow in
  places, because depth without evidence is the thing being avoided.
- Not authority. The ADRs in `docs/adr/` govern what may be built.
- Not a work plan. §5.5 names the bill of materials that will carry that load.
- Not a log. `docs/STATE.md` says where work stopped; this says where it is going.
- **Not conformant to ISO/IEC/IEEE 42010**, the standard for architecture
  descriptions, and knowingly so. It has an entity of interest (§3.1), views
  (§5, §6, §7) and partial rationale (§0.5, §4.2, §4.3). It has **no enumerated
  stakeholders, no concerns traced to them, no declared viewpoints governing its
  views, and no correspondences** — the relations between AD elements that a
  correspondence rule could check. Those four absences are the difference between
  a document that reads well and one that can **fail**. Recorded as `RISK-18`
  rather than quietly carried.
- **Not finished.** The owner's assessment as of 2026-08-03 is that this map is
  "still cloudy and needs much more refinement." Treat every §1 claim as a first
  articulation rather than a settled position.

### 0.3 Why it is not digest-pinned

A map must stay current cheaply. A decision should be expensive to change.
Pinning this document's digest into anything taxes every correction and produces
a map that is stale because updating it is costly. Keeping it outside the digest
chain is what makes it affordable to keep true.

### 0.4 On arc42

The twelve section headings follow arc42 (Starke & Hruschka), used here as a
**conformance checklist** to avoid omitting a section, not republished as an
adaptation. arc42 is licensed CC BY-SA 4.0; whether to adopt-and-attribute
instead is an open owner decision recorded in §11 as `RISK-16`.

### 0.5 What changed in `2.0.0`, and why — `CONFIRMED` as a change of position

Version `1.1.0` stated the product thesis as:

> A governance harness that makes unreliable AI agents produce reliable software.
> Rules compiled into code change what an agent produces.

That is a claim about **output quality**. It was never tested, it is expensive to
test, and `1.1.0` recorded that the experiment which would settle it had not been
run.

The repository moved away from it independently. `CLAUDE.md` and `README.md` now
state the opposite in the strongest available language:

> **Ranex does not improve aim.** Not by one degree. It makes misses visible and
> cheap, and hits provable.

`2.0.0` resolves the contradiction in favour of the repository. Every product
requirement, ASR and risk in `1.1.0` was written against the discarded thesis and
has been re-derived. The change is not cosmetic: **the old thesis is a claim
about aim, the new one is a claim about scoring**, and they imply different
products, different proof burdens and different buyers.

The substantive additions in `2.0.0` — the problem statement (§1.1), the factory
doctrine (§4), calibration as a first-class concern (§8.4), and the measurement
problem (§11.3) — come from an owner working session on 2026-08-03. They are
recorded as `PROVISIONAL` because they are newly articulated and nothing has been
built against them.

### 0.6 What changed in `2.1.0` — bounded adoption of TOGAF

`2.1.0` adopts **four** parts of the TOGAF ADM and explicitly refuses the rest
(§4.5), and records the map's own non-conformance to ISO/IEC/IEEE 42010 (§0.2,
`RISK-18`).

Two standards, two different questions, and Ranex needs both:

- **ISO/IEC/IEEE 42010** — *architecture description*. Answers "is the map
  complete?" Completeness is not "every section is filled"; it is **every
  identified stakeholder concern is framed by a viewpoint and addressed by a
  view, with correspondences stated between them.** That is a checkable
  criterion; the one used to call `2.0.0` "fully written" was a formatting check.
- **TOGAF** — *architecture process*. Answers "how do we get from here to there,
  and how do we know the builders complied?"

**Source discipline:** the TOGAF material consulted was 9.1/9.2, which is
**superseded**. The current standard is the *TOGAF Standard, 10th Edition*
(The Open Group, April 2022, Technical Corrigendum 1 in 2025), free for
non-commercial use. Anything entering an ADR must cite the 10th Edition
directly — the 9.x copies read were an unlicensed third-party dump including
copyrighted commercial books, and ADR-003 would reject them on origin and
licence alone.

---

## §1 Introduction and Goals

### 1.1 The problem — `PROVISIONAL`, newly articulated 2026-08-03

Stated at four depths, because the shallow versions are true but do not justify a
product.

**Level one — agents misreport.** An agent says the tests pass when they do not.
Real, and merely annoying.

**Level two — bad code ships.** Also real, also not new. Software has shipped
broken since it existed.

**Level three — no one has held the code in their head.** Every line of
production software was historically, at some moment, reasoned about by a human
who could later be asked. That is no longer true. Organisations now own, ship and
carry liability for code no living person has ever thought about. Not *the author
left* — **there was no author.**

**Level four — the load-bearing one.** Every artefact by which an organisation
demonstrates that it was careful — tests, documentation, decision records, review
comments, commit messages, changelogs, postmortems, compliance narratives — can
now be generated by the same system that did the work, more cheaply than the care
those artefacts are supposed to evidence.

> **AI has made the evidence of care cheaper than care itself, and every
> institution that governs software runs on that evidence.**

Any signal that costs less to produce than the thing it signals stops being a
signal. This requires no one to act in bad faith: an honest team using AI honestly
produces artefacts indistinguishable from a dishonest team's. The result is a
market for lemons — the careful organisation can no longer signal its care, and is
therefore priced as though it were careless.

**Two concrete failures this predicts** — `PROVISIONAL`, and the legal and
regulatory mechanics below require verification against primary sources before
either is repeated publicly:

- **Diligence.** An acquirer reviews 400,000 lines, 94% coverage, a complete test
  suite passing, thorough decision records. The question *what does passing prove?*
  has no answer, because no one at the company wrote any of it. The company is
  repriced or the deal dies — not because the software is bad, but because it is
  **unprovable**, and to a buyer those are the same condition.
- **Liability.** After a loss, discovery asks who approved a change. A name
  appears in the log. That person approved forty thousand lines that week and
  could not have read them. The organisation's defence is that it had a process,
  and the opposing exhibit is the organisation's own documentation of a process it
  demonstrably did not follow. **Thorough governance documentation becomes
  evidence against its author.**

**Why this worsens as models improve — `PROVISIONAL`, and strategically load-bearing.**
Confidence is the proxy humans use for knowledge. A more capable model is more
confident and more persuasive, so it degrades that proxy faster. An organisation's
certainty rises while its correctness does not. Most AI development tooling is a
bet that current models are weak and is obsoleted by the next release. **Ranex is
a bet that models get strong**, and becomes more necessary with each capability
increase. If a single claim in this document is worth defending, it is this one.

### 1.2 What Ranex is — `PROVISIONAL`; the bounded mechanism `CONFIRMED`

Ranex is **the gauge**.

The age has an abundance of ways to produce software — models, harnesses, skills,
tool servers, frameworks, agents — multiplying weekly, each shipping with its own
self-assessment. What does not exist is any fixed external standard that says
whether the output is good and that the producer cannot reach. Self-assessment is
precisely what a gauge exists to replace.

> **The age has infinite ways to produce software and no way to gauge it.**

**The thesis, stated so it can be falsified:**

> A verdict produced by a fixed target, set before the work, and scored by
> something the producer cannot alter, is worth more than any quantity of evidence
> the producer generates about itself.

`PROVISIONAL` as a product thesis. It is substantially true by construction rather
than by experiment, which is a strength relative to `1.1.0`'s thesis — but "true"
and "someone will pay for it" are different claims, and only the first is
addressed here. See `RISK-01`.

**What Ranex explicitly does not claim — `CONFIRMED` as policy, `CLAUDE.md`:**
it does not improve the quality of generated code, by any margin. Program output,
documentation and sales material must never suggest otherwise.

### 1.3 Product requirements — `PROVISIONAL`, re-derived 2026-08-03

Re-derived against §1.2. `1.1.0`'s `PR-01` and `PR-07` were claims about aim and
efficiency and do not survive the thesis change. `PR-06`, `PR-07` and `PR-09`
below are new and come directly from the 2026-08-03 session.

| ID | Requirement | Status |
|---|---|---|
| `PR-01` | A verdict can be re-derived by someone who did not produce the work, offline, from the record alone | `PROVISIONAL` — the record exists; no external re-derivation has been performed |
| `PR-02` | No model output is ever an authorization. A gate passes on evidence or does not pass | `CONFIRMED` for the kernel path: `evaluate()` imports no model client, and the suite passes with no model credential present |
| `PR-03` | Absence blocks. A required claim with no satisfying evidence is `FAIL`, never a default and never a skip | `CONFIRMED` for the kernel |
| `PR-04` | The identity that produces evidence cannot approve it | `CONFIRMED` as a string comparison in the kernel; `UNRESOLVED` as a control, because `approver_id` is unauthenticated — see `RISK-07` |
| `PR-05` | Every verdict binds the exact subject digest it was measured against, so stale evidence stops counting automatically | `CONFIRMED` — SLICE-001 and SLICE-004 |
| `PR-06` | **Every gauge carries a calibration result. An uncalibrated gauge yields no information and must not be reported as though it did** | `PROVISIONAL` — `mutmut` is a calibration procedure and runs; nothing consumes its result as a gate, and 880 mutants survive |
| `PR-07` | **The record binds the full production configuration — model, harness version, skill and tool manifest, prompt digest — not the code alone** | `UNRESOLVED` — not designed, not built. §5.5 |
| `PR-08` | A governed project's written records cannot silently drift from observable fact | `PROVISIONAL` — the mechanism exists in `tests/contract/test_docs_discipline.py`; not generalised |
| `PR-09` | **A run that cannot succeed stops within a bounded budget and asks the owner a product question, rather than continuing to spend** | `UNRESOLVED` — designed in `README.md`, no budget, no escalation, no worker to bound |
| `PR-10` | Removing every model credential from the machine must not change a verdict | `CONFIRMED` for the kernel path |

**`PR-09` is the commercial wedge and `PR-01` is the moat.** See §11.2.

### 1.4 Major system capabilities — status as of 2026-08-03

| Capability | What it does | Status |
|---|---|---|
| Deterministic verdict | Gate + evidence + subject + approver → verdict, no model consulted | **`CONFIRMED`** — `evaluate()` is a pure function |
| Subject-bound evidence | Evidence binds the digest of the committed tree it was measured against | **`CONFIRMED`** — SLICE-001 |
| Evidence authenticity | Ed25519 signature verified against a committed keyring before admission | **`CONFIRMED`** — SLICE-002 |
| Claim↔command binding | The committed catalog declares the argv that satisfies a claim | **`CONFIRMED`** — SLICE-003; six independent audits failed to break it |
| Hermetic observation | The bound command runs against a materialisation of the subject commit, in an environment built from empty, with a pinned toolchain | **`CONFIRMED`** — SLICE-004, closed twice |
| Append-only journal | Hash-chained SQLite, serialised appends | **`CONFIRMED`** for append and chain verification; **no reader** — `Journal.verify()` has no caller and there is no `journal` command |
| Confinement of the measured party | The bound command cannot reach the key that signs its own measurement | `PROVISIONAL` — ADR-006 decided; its slice was withdrawn 2026-08-03 and re-sequenced behind SLICE-006. Nothing built |
| Calibration of the gauges | Demonstrating that a gate detects a known defect | `PROVISIONAL` — `mutmut` and `diff-cover` run; no negative control, no gate consumes a calibration result |
| Worker dispatch | Spawn a harness in an isolated worktree, read the diff, discard the summary | `UNRESOLVED` — designed, never built. **The single largest untested assumption in the system** |
| Budget and escalation | Bounded spend, three misses, plain-language question to the owner | `UNRESOLVED` — designed, never built |
| Intake and flow graph | Plain-language intent → a graph the owner approves → scenarios → tests | `UNRESOLVED` — designed, never built |
| Configuration comparison | Which model, harness and skill set actually finishes work, measured | `UNRESOLVED` — §11.3 argues this is the most valuable byproduct and the hardest to get right |

**Honest summary:** the hardest part to get conceptually right exists and is
tested. Almost none of the surface around it does, and the loop has never closed
around a real agent even once.

---

## §2 Constraints

### 2.1 Binding — `CONFIRMED`

| Constraint | Source |
|---|---|
| Python is the implementation language | repository |
| `uv` is the toolchain manager; `[tool.uv] package = false`, so no console script is installed | `pyproject.toml` |
| One slice at a time; no slice without a researched ADR | `CLAUDE.md`, enforced by contract test |
| Research must vendor pinned third-party source with origin and licence | ADR-003, enforced by contract test |
| The docs layer is capped to a fixed set of allowed documents | `CLAUDE.md`, enforced by `tests/contract/test_docs_discipline.py` |
| `diff-cover` at 100% on changed lines; `mutmut` before a slice closes | SLICE-004 |
| Licence is MIT | `README.md` |
| Hermes is not a base and must not be reintroduced. Removed 2026-08-01 | `CLAUDE.md` |

### 2.2 Process constraints — `CONFIRMED`

- **One slice open at a time.** Opening a second is the named failure mode.
- **No slice without an ADR**, written before the slice file exists.
- An ADR citing no working code is an opinion, and this is enforced by test.
- Never weaken a test, checker, baseline or policy to make work pass.

### 2.3 Environmental — `CONFIRMED`

- Local-first. No hosted service exists and none is planned this horizon.
- Ranex becomes **Linux-only in fact** once confinement lands, and will refuse
  below Landlock ABI 6. Taken deliberately; ADR-006 records it as a cost.
- A hermetic tree has no installed dependencies, so only self-contained commands
  can be gated — in every language, not only Python.
- Single developer, no second implementer. See `RISK-15`.

---

## §3 Context and Scope

### 3.1 System context — `PROVISIONAL`

```
   ┌────────────┐        intent, decisions        ┌──────────────────┐
   │   Owner    │────────────────────────────────▶│                  │
   │(non-tech.) │◀────── plain-language state ────│                  │
   └────────────┘                                 │      RANEX       │
                                                  │   the gauge      │
   ┌────────────┐   diff on disk + evidence       │                  │
   │  Harnesses │────────────────────────────────▶│  freeze · run    │
   │ (bought,   │◀──── frozen target, bounded ────│  measure · record│
   │  not built)│      budget, no summary read    │  refuse          │
   └────────────┘                                 └────────┬─────────┘
                                                           │
   ┌────────────┐                                          │
   │  Outsiders │◀──── a record they can check without ────┘
   │ acquirer,  │      trusting the party that produced it
   │ insurer,   │
   │ regulator  │
   └────────────┘
```

The third box is new in `2.0.0` and follows from §1.1. A record only the producer
can read is a diary. See `RISK-03`.

### 3.2 Scope boundary — `CONFIRMED` as policy

**In scope:** fixing the target before the work; measuring the result with code;
binding the measurement to an exact subject; recording it so an outsider can check
it; calibrating the instruments that do the measuring; refusing when any of these
cannot be done honestly.

**Explicitly not:**

- **An agent harness.** `CLAUDE.md` — Ranex never implements an agent loop and
  never asks a model what to do next. See §4.3 for why this is load-bearing rather
  than stylistic.
- A general-purpose assistant, a prompt library, or a model-inference business.
- A claim about the quality of generated code (§1.2).

---

## §4 Solution Strategy

### 4.1 The doctrine — `PROVISIONAL`, articulated 2026-08-03

Ranex imports a solved discipline rather than inventing one. The industrial
factory's innovation was not mass production; it was **interchangeable parts**,
and interchangeable parts required something that had to exist before any part was
made: **the gauge**.

Before it, every musket was hand-fitted and a broken part meant finding a
gunsmith. The armory system stopped asking whether the craftsman was skilled and
started asking whether the part passes a fixed standard the maker cannot alter.

| Factory concept | Meaning | Ranex | Status |
|---|---|---|---|
| **Go/no-go gauge** | Fixed tolerance, mechanical check, precedes production | Frozen tests + gates | **built** |
| **Interchangeable parts** | Any supplier's part fits | Model and harness swappable behind a port | designed |
| **Poka-yoke** | The defect is made impossible, not caught later | Tests read-only to implementers; no self-approval | **built** |
| **Jidoka / andon** | The machine stops itself on a defect; anyone may halt the line, and halting is correct | Three misses → escalate a product question to the owner | designed |
| **The traveler** | The card that rides with the part, stamped at every station. **An unstamped part does not ship** | The journal plus signed evidence | **built** |
| **Incoming inspection** | Check what suppliers send before it enters the line | Digest the model, harness and skill manifest | **missing** — `PR-07` |
| **Calibration lab** | The gauges are themselves measured, on a schedule, against a reference | `mutmut` as calibration; negative controls | partial |
| **Statistical process control** | Measure the process, catch drift before it makes scrap | Cross-run comparison of configurations | **missing** |
| **Bill of materials** | Every part, its provenance, its spec | §5.5 | **missing** |

The traveler is the most useful reframing available for the journal: it carries
its own rule, and a non-technical buyer understands *an unstamped part does not
ship* instantly, where *hash-chained append-only log* means nothing.

### 4.2 Why every prior software factory failed, and why that failure does not transfer — `PROVISIONAL`

"Software factory" is a burned term. It has been attempted publicly and failed —
CASE tooling, model-driven architecture, and the 2004 *Software Factories*
programme, among others. *(These specifics are recalled, not verified. They must
be checked against primary sources before use in any public material.)* To an
experienced engineer the phrase reads as a discredited idea, which is a real cost
of adopting it.

The argument that the failure does not transfer:

> Every previous attempt industrialised **production** — generating the
> implementation, assembling from components — but production was never the
> constraint. Knowing what to write, and knowing whether it was right, were.
> **AI has moved the constraint.** Writing code is now nearly free; specification
> and verification are what remain scarce. A factory is, at its core, a machine
> for verification at scale.

**Prior software factories industrialised the wrong step. Ranex industrialises
inspection, which is the step that just became scarce.** `PROVISIONAL`, but it
survives the obvious objection, which is more than the `1.1.0` thesis managed.

### 4.3 Ranex is the quality system, not the factory — `CONFIRMED` as policy

This reconciles the factory framing with §3.2's refusal to be a harness.

A factory contains machine tools **and** a quality system — gauges, inspection
stations, travelers, the andon cord, incoming inspection, process control. Nobody
builds their own machine tools; they are bought, and replaced when better ones
ship.

**The models and harnesses are the machine tools. Ranex is the quality system.**

Three consequences:

1. A quality system that also operates the machine is not a quality system. It is
   a machine with an opinion about itself — which is the failure §1.1 describes.
2. The proliferation of models and harnesses is **not Ranex's problem to solve.**
   A factory does not agonise over which lathe to buy, because the gauge reads the
   same either way. Ranex's answer to *which model should I use* is **stop asking;
   the choice is now cheap to get wrong and measurable when it is.**
3. Being outside the harness is what makes the verdict worth anything, and it is
   also what lets Ranex outlive any particular harness. A harness is a bet on
   today's tooling; a gauge is not.

### 4.4 Strategy decisions — `CONFIRMED` as decisions, `PROVISIONAL` as designs

Deterministic over probabilistic enforcement; fail-closed, where `NOT_ASSESSED`
is never a pass; evidence bound to exact subject digests; separation of producer
and approver; containment over control — Ranex does not need to govern what
happens inside the worker's loop, only what is allowed out of it; local-first
before anything distributed.

### 4.5 What we take from TOGAF, and what we refuse — `PROVISIONAL`, new in `2.1.0`

**The positioning claim: Ranex is ADM Phase G, executed by code instead of a
review board.**

TOGAF's Phase G — Implementation Governance — exists to ensure conformance with
the Target Architecture by the projects implementing it. Its instrument is the
**Architecture Contract (signed)**; its output is a **Compliance Assessment**.
Every enterprise runs that phase with an architecture board, review meetings and
spreadsheets, rated by people who cannot have read everything. It is the phase
where §1.1's problem lands hardest, and the phase most cheaply faked.

TOGAF named the loop and left the checking to humans. Ranex does the checking
with code. This is the most credible sentence available to an enterprise buyer,
because it names an acknowledged weak point rather than inventing a category.
`UNRESOLVED` as market positioning — never tested on a buyer (`RISK-04`).

**Adopted — four parts, and nothing else:**

| TOGAF part | What it gives Ranex |
|---|---|
| **Architecture Contract** | The frozen, signed task envelope. Half-built already: signed evidence and claim↔command binding are its mechanics |
| **Baseline / Target / Gap / Roadmap / Transition Architectures** | The vocabulary for §5.5. Where we are, the finish line, the parts, the order, and intermediate states that each deliver value |
| **ABB vs SBB** — Architecture Building Block (capability needed) vs Solution Building Block (what implements it) | The buy/build column, made rigorous. An ABB with no SBB is an unfilled part |
| **Requirements Management as the hub, not a phase** | It sits at the centre of the ADM and every phase touches it. This is the layer §0.2 records as missing |

**Refused, and one of them actively:**

Discarded as enterprise-scale overhead with no second consumer here: the four
architecture domains, the Enterprise Continuum, TRM and III-RM, the Skills
Framework, and the Architecture Board / Chief Architect / Domain Architect
hierarchy.

**Refused on principle: TOGAF's Compliance Levels.** The scale — Irrelevant,
Consistent, Compliant, Conformant, Fully Conformant, Non-Conformant — is
**incompatible with this project's invariants.** Absence blocks, and a gate that
cannot block is refused at construction. A graded scale is exactly how "mostly
compliant" becomes a pass, and it is the mechanism by which enterprise governance
became the theatre §1.1 describes. Take the contract; refuse the grading that
softens it.

**Why the adoption is this narrow — evidence, not preference.** The pre-reset
tree already contained a faithful TOGAF-shaped apparatus: a core SDLC operating
model, a 2,172-line control catalog, 34 bounded contexts, 21 readiness gates in
two non-compensating tiers, 41 capabilities levelled 0–4 and every one
`NOT_ASSESSED`, compliance assessments and a governance log. It produced **561
files and zero product code.** The failure was structural, not a lapse of
discipline: **TOGAF's overhead is amortised across an enterprise, and there is
one implementer here.** Every ADM artifact assumes a different person consumes
it; when author and audience are the same person, the artifact is pure cost.
Tracked as `RISK-17`.

---

## §5 Building Block View

### 5.1 Containers — status 2026-08-03

| Container | Responsibility | Status |
|---|---|---|
| `foundation/` | Canonical JSON, SHA-256 digests | **`CONFIRMED`** |
| `governed_execution/` | `verdict.py` — the kernel — and the SQLite hash-chained journal | **`CONFIRMED`** for evaluate and append; journal has no reader |
| `policy/` | Gate catalog loading from the committed tree | **`CONFIRMED`** |
| `cli/` | Operator entry point, path confinement, subject materialisation, toolchain pinning | **`CONFIRMED`**; **`mutmut` says nothing about `cli/main.py`** — see `RISK-10` |
| `bootstrap/` | Composition root, the only place concretes are wired | **`CONFIRMED`** |
| Worker port | Dispatch a harness into an isolated worktree | **absent** |
| Budget / escalation | Bounded spend, three-miss escalation | **absent** |
| Intake / compile | Flow graph, covering paths, scenarios, frozen tests | **absent** |
| Outward record | Something an outsider can verify | **absent** — see `RISK-03` |

`1.1.0` registered 34 bounded contexts. Five directories exist. The other 29 were
named and never built, and are removed from this map rather than carried as
aspiration. This is the single largest correction in `2.0.0`.

### 5.2 The kernel invariants — `CONFIRMED`, `CLAUDE.md`

Breaking one is a bug, not a tradeoff.

- The kernel is code. No model decides what happens next.
- Absence blocks.
- Evidence is bound to a subject digest.
- No self-approval.
- A gate that cannot block is refused at construction.
- The journal is append-only and hash-chained.
- Removing every model credential must not change a verdict.

### 5.3 What exists with executed evidence

Four slices closed, one withdrawn before implementation, one open. As of
2026-08-03 the suite is `323` passing, `0` failing.

### 5.4 Data ownership — `PROVISIONAL`

`governance/` holds `gates.yaml` (the committed catalog), `producers.yaml` (the
keyring and trust root), `evidence.json` (records, **not append-only**) and
`journal.sqlite3` (append-only, hash-chained, gitignored).

### 5.5 Bill of materials — `UNRESOLVED`, and the next artefact to build

This map describes the system. It does not enumerate the parts, and the owner
identified that absence on 2026-08-03 as the reason there is no finish line and no
way to tell whether the current path is correct.

The gap is real and this document should not try to fill it, because prose is what
produced 561 architecture files and zero product code. The parts list must be
**structured data, not prose** — a table has a natural size limit and an essay does
not.

Required shape, in TOGAF's vocabulary rather than invented terms (§4.5):

| Column | TOGAF name | Discipline it enforces |
|---|---|---|
| Part | **ABB** — Architecture Building Block | The capability required, stated independently of what implements it |
| **BUY or BUILD** | **SBB** — Solution Building Block | What actually implements the ABB. Forces the never-hand-roll question at every node, structurally. **An ABB with no SBB is an unfilled part**, which is the honest name for most of this system today |
| **Gauge** | — | How this part is proven good. **A part with no gauge is a wish, not a part** |
| Status | — | `missing` → `specified` → `built` → `calibrated`. Built and calibrated are separate on purpose (§8.4) |
| Depends on | **Architecture Roadmap** | Assembly order, derived rather than authored |

And the frame the rows sit in: **Baseline** is what exists today (§1.4's
`CONFIRMED` rows), **Target** is the finish line, the **Gap** between them is the
parts list, and **Transition Architectures** are the intermediate states that each
have to deliver something rather than merely being closer to done. A slice is a
work package moving one transition to the next.

And the mechanism `1.1.0` lacked: **a test reads the bill of materials.** Every
row marked `built` must name a test that exists and passes; every row marked
`calibrated` must name a mutation or negative-control result; no row may exist
without a gauge. The plan then cannot drift from the code, because drift breaks
the build. A plan an agent can read is a suggestion; a plan compiled into a check
is a constraint — which is the project's own thesis applied to its own map.

**What can and cannot be complete** — recorded so the next session does not
attempt the impossible: the finish line can be complete; the parts list can be
complete; the routing can be complete in *order*. **Detailed steps can only ever
be complete for the next two or three parts**, because parts built earlier change
what the later steps should be. The slice files already are those detailed steps.
The missing layer is the parts list they hang from, not more step detail.

---

## §6 Runtime View

### 6.1 The intended flow — `UNRESOLVED` end to end

```
idea → flow graph → covering paths → scenarios → contract tests → gates → verdict
         ▲                                                                   │
         │                                                                   ▼
   owner approves this                                          evidence + journal
```

The approved graph is the root of trust. Everything to its right is derived
mechanically; everything to its left is a conversation. Only the rightmost two
steps exist.

### 6.2 The build loop — `UNRESOLVED`, never executed

```
  take the next ready task
     → create an isolated git worktree
     → spawn a harness with the task envelope
     → wait for it to exit
     → read the DIFF ON DISK  (the harness's own summary is discarded)
     → run the checks         (code, not a model)
     ├─ pass → THE KERNEL merges          (workers never merge)
     └─ fail → retry ×3 with the failure output
                 → still failing → escalate to the owner in plain language
```

**This has never run.** Five slices have hardened the measurement path; nothing
has ever been measured that an agent produced. That is the largest untested
assumption in the system and it is named again in `RISK-14`.

### 6.3 The verdict path — **`CONFIRMED`**

```
ranex run --claim C --producer P -- <argv>
  → refuse if the worktree differs from HEAD
  → materialise the subject commit, each blob checked against the tree's object id
  → build the environment from empty, pin the toolchain
  → execute, record exit code + subject digest, sign Ed25519
ranex gate evaluate HEAD --approver A
  → verify signature against the committed keyring
  → compare the claim's declared argv digest
  → absence blocks; contradiction blocks; self-approval blocks
  → verdict + reason + journal append
```

---

## §7 Deployment View

### 7.1 Today — `CONFIRMED`

There is no deployed Ranex. No service, no daemon, no installed package. The CLI
runs from the source tree through `uv` and is not an enforcement boundary for
anything but this repository — and **not even for this one**: `gates.yaml` demands
a command a hermetic tree cannot run, so nothing currently gates this project.
See `RISK-08`.

### 7.2 Intended — `PROVISIONAL`

Local-first, single machine. A hosted surface is `OUT-OF-SCOPE` this horizon and
would be required by two things named later in this document — an outward-facing
record (`RISK-03`) and the fleet scale the measurement flywheel needs (§11.4).
Those are the two forces that would eventually overturn local-first.

---

## §8 Crosscutting Concepts

### 8.1 Trust boundaries

| Boundary | Rule | Status |
|---|---|---|
| Producer ↔ gauge | The gauge is external to the producer and unalterable by it | `UNRESOLVED` — ADR-006 decides the measured route to the signing key; unbuilt and re-sequenced |
| Producer ↔ approver | The identity producing evidence cannot approve it | `CONFIRMED` as a comparison; `UNRESOLVED` as a control (`RISK-07`) |
| Model ↔ authority | A model verdict is evidence, never authority | `CONFIRMED` for the kernel |
| Enforcement ↔ inference | No enforcement check invokes a model. Removing model access changes no verdict | `CONFIRMED` for the kernel path |
| Ranex ↔ its own confinement | Ranex writes the journal, so it cannot be confined by the domain it applies to the worker | `CONFIRMED` as a limit; ADR-006 s.p. 20 |

### 8.2 Determinism — `CONFIRMED` for the kernel

Canonical JSON, SHA-256 digests, identical inputs to identical verdicts byte for
byte. **"Deterministic" describes the process and the verdict, never the generated
code.** Anyone claiming an LLM produces identical software twice is selling
something.

### 8.3 Observability

Recorded: every verdict with the rule that failed, the subject digest, the
producer and the approver. Never recorded as fact: anything a model asserted about
its own work.

Not recorded and required by `PR-07`: the production configuration — model,
harness version, skill and tool manifest, prompt digest.

### 8.4 Calibration — `PROVISIONAL`, new in `2.0.0`

The deepest part of the doctrine, and the part `1.1.0` had no concept of.

In a factory, **the gauges are themselves calibrated** against a reference, on a
schedule, with a certificate and a due date. The rule that gives it force:

> When a gauge is found out of calibration, **every part it passed** since its
> last good check is suspect and is recalled.

Not the parts it rejected. The ones it approved — because a bad gauge does not
produce visible errors, it produces confident approvals.

The surrounding discipline is **Measurement System Analysis**, whose core tool is
**Gauge R&R**: measuring the variance of *the measurement system* rather than the
part. Repeatability — same gauge, same part, same answer? Reproducibility —
different operators, same answer? Published guidance places roughly under 10% of
tolerance as good and over 30% as unusable. *(Thresholds recalled from AIAG
practice and not verified; check before quoting.)* Most shops never measure this,
and therefore do not know their pass/fail data is largely noise.

The same discipline exists in pharmaceutical work as **method validation** — an
assay must be validated for specificity, accuracy, precision and robustness
*before* any result from it is trusted. The test is tested before the drug is.

**Four consequences for Ranex, none of them currently satisfied:**

1. **`mutmut` is not a code-quality tool. It is gauge calibration** — deliberately
   introducing known defects and checking whether the instrument notices. The 880
   surviving mutants are not a backlog; they are a **calibration report** stating
   that this instrument fails to detect 880 known defects, 47 of them in
   `verdict.py`, which is the master gauge every other measurement passes through.
2. **A gate that has never fired is unproven, not good.** It is either protecting
   against something that does not occur or it is broken, and from outside those
   are indistinguishable. Firing rate must be a recorded property of every gate.
   `gates.yaml` today is a gauge reading `PASS` because it is disconnected from the
   part (`RISK-08`).
3. **Negative controls.** Periodically inject a change known to be bad and confirm
   the gates block it. Every serious assay runs one. If it ever passes, every
   verdict since the last good control is suspect — calibration recall, applied.
   This is the smallest shippable piece of §8.4 and should be built first.
4. **Built and calibrated are different states**, which is why §5.5's bill of
   materials separates them.

---

## §9 Architectural Decisions

Seven ADRs exist. `1.1.0` indexed twenty-one belonging to an architecture that was
deleted; they are not carried forward.

| ADR | Decides |
|---|---|
| `ADR-000` | How ADRs are written — prior art must be fetched, pinned and vendored |
| `ADR-001` | Claim↔command binding |
| `ADR-002` | Committed trust root |
| `ADR-003` | Research is fetched evidence, not citation |
| `ADR-004` | Environment boundary for git queries |
| `ADR-005` | Hermetic observation |
| `ADR-006` | Landlock confinement of the bound command |
| `ADR-007` | Provision dependencies without pretending they are evidence — `proposed` |

**ADR-007 is not the journal ADR.** ADR-005 removed `.venv` and `node_modules`
from the materialisation because ignored state is not in the commit, so only
self-contained commands can run — and this repository's own `uv run pytest -q`
is not one. ADR-007 exists to reconnect the gauge to the part (`RISK-08`), which
is why it displaced confinement in the ordering (§13).

The journal ADR — verify before append, never auto-create, and a checkpoint
committing to log **size**, because size is what catches truncation and
rollback — is deferred and unnumbered.

---

## §10 Quality Requirements

### 10.1 Architecturally significant requirements — `PROVISIONAL`, re-derived

| ID | ASR | Drives |
|---|---|---|
| `ASR-01` | A verdict must be reproducible: identical inputs, identical verdict, no model invoked | Rules out model-in-the-loop enforcement entirely |
| `ASR-02` | Absence of evidence must block, never default | Fail-closed; forbids permissive defaults |
| `ASR-03` | Evidence must bind an exact subject digest | Content addressing; stale evidence self-invalidates |
| `ASR-04` | **The gauge must be unreachable by the party it measures** | Confinement; forbids in-process trust. ADR-006, unbuilt |
| `ASR-05` | **Every gauge must be demonstrably able to detect a known defect** | Mutation testing and negative controls become gates, not habits (§8.4) |
| `ASR-06` | Records must be append-only and replayable | Journal + hash chain; forbids destructive update |
| `ASR-07` | **A verdict must be checkable by someone who distrusts its producer** | Signatures, public keyring, offline re-derivation. Currently unsatisfied (`RISK-03`) |
| `ASR-08` | **Configurations must be comparable: the same frozen target, scored identically across different producers** | This is what makes measurement possible at all (§11.3) |
| `ASR-09` | **Every run must be bounded in wall clock and spend, and exceeding the bound is a recorded refusal, never silent continuation** | `PR-09`, the wedge |
| `ASR-10` | A non-technical owner must be able to act without reading code | Plain-language escalation; the flow-graph gate |

### 10.2 Quality attributes — `UNRESOLVED`

**None measured.** No performance, latency or cost target has been observed. Any
number quoted today is a target, not an observation.

---

## §11 Risks and Open Questions

### 11.1 Product and market — all `UNRESOLVED`, all new in `2.0.0`

| ID | Risk | Settled by |
|---|---|---|
| `RISK-01` | **The thesis is now largely true by construction, which moves the risk from "is it true" to "will anyone pay."** `1.1.0` risked being wrong; `2.0.0` risks being correct and unwanted | A buyer paying for it |
| `RISK-02` | **Timing.** The provability nightmare (§1.1 level four) may be three to five years early. No one has been sued at scale over AI-written code. Founders do not buy diligence insurance in advance. Right and early is operationally identical to wrong | Evidence of present-tense pain, or a wedge that pays before the nightmare arrives |
| `RISK-03` | **Position.** A lemons market is fixed by a signal a hostile outsider can read. Ranex is a local CLI, and a certificate you issue to yourself is worth nothing. The cryptographic substrate for an outward record exists; the position does not | A decision about who the verifier is, which likely overturns local-first (§7.2) |
| `RISK-04` | **The buyer is post-disillusionment.** Someone who still believes a prompt produces an app does not want gates — they want the magic, and competitors sell it. The buyer is the person who already burned weeks and thousands and now distrusts the loop. Real, growing, and smaller than the believer market | Contact with actual buyers |
| `RISK-05` | **"Software factory" and "enterprise" both carry cost.** The first is a discredited term to experienced engineers (§4.2); the second quietly promises output quality, which §1.2 forbids claiming | An owner decision on naming |

### 11.2 The wedge and the moat — `PROVISIONAL`

Two different problems, and conflating them is how this goes wrong.

- **The wedge is cost and completion** (`PR-09`). *Stop burning money on runs that
  never finish.* Felt today, has a budget, easy to explain, and a competitor can
  copy it in a quarter.
- **The moat is provability** (`PR-01`, `ASR-07`). *The record survives someone who
  wants it to be false.* Not felt yet, and it is what remains defensible after the
  wedge is copied.

**Lead with the wedge, build for the moat.** Leading with the moat sells a lawsuit
nobody has received. Building only the wedge ships a feature anyone can clone.

### 11.3 The measurement problem — `UNRESOLVED`, and the most valuable unbuilt thing

The owner's intent is that accumulated use should grade every component — skills,
gates, rules, reviews, models — and that grading should compound into improvement.

**The plan as stated does not work, for a structural reason.** Observational data
from real runs is confounded. Hard tasks get the expensive model; careful users
load better skills; complex repositories get more gates. Regressing outcome on
components across observed runs will produce a confident, tight-error-bar
conclusion that expensive models cause failure — because they were assigned to the
hard problems. This is not a data-hygiene issue that cleaning fixes; it is
structural, and it is the standard way measurement programmes generate confident
nonsense.

Both mature disciplines solved it the same way, and neither solved it with logs:

- Manufacturing uses **Design of Experiments** — deliberately varying factors on a
  schedule so effects are separable. Taguchi's orthogonal arrays exist to test many
  factors in few runs, which is precisely the constraint here.
- Pharmacology uses the **control arm**. No efficacy claim without a comparison
  group.

**So: run data gives monitoring; causal grades require deliberate experiments.**
Different machinery, and it has to be designed in rather than retrofitted.

**Why this is an opportunity rather than an obstacle.** An honest trial needs a
fixed treatment, isolated replicates, and an outcome measured by something with no
stake in it. Ranex has all three by construction: the target is frozen before the
run, worktrees are isolated, the verdict is mechanical, and repeats are cheap.

Every existing benchmark of AI tooling either uses a fixed public test set —
contaminated and gamed within months — or an LLM judge, which is the thing under
test grading itself. **An external deterministic gauge is the precondition for
honestly measuring AI tooling, and no one has one.**

This reframes the question the whole market is guessing at. *Which model, harness
or skill is best?* is unanswered not because it is hard but because **the
instrument required to answer it does not exist.** Build the gauge and the answer
is a byproduct.

### 11.4 Limits of the grading idea — `PROVISIONAL`

| Limit | Consequence |
|---|---|
| **Not everything decomposes.** Skills, gates, rules and models are discrete and gradeable. Prompts, tasks and context are not. Some variance lives irreducibly in the whole | Do not attempt a grade for every input; the parts list must distinguish gradeable parts from unbounded ones |
| **Goodhart.** Publishing a component's grade causes components to be optimised for the grade. Manufacturing's defence is that the gauge measures a physical property that cannot be faked without making a better part | Ranex's equivalent is the frozen, producer-unalterable target. This is what keeps the metric honest under optimisation pressure — it is not fussiness |
| **Sample size.** Separating signal from variance needs many runs on comparable tasks. One repository will never produce that | The flywheel is a fleet-scale asset. This argues for a hosted product later, and is a real constraint on *when* data becomes valuable |

### 11.5 Engineering risks — current, `CONFIRMED` unless noted

| ID | Risk |
|---|---|
| `RISK-06` | **The measured party runs under the uid that signs the measurement.** Reproduced: the bound command reads `/proc/<ranex-pid>/environ`, obtains the signing key, and signs any record. ADR-006 decides the fix; its slice was **withdrawn on 2026-08-03 and re-sequenced behind SLICE-006**, so the hole is open and now unscheduled |
| `RISK-07` | **`approver_id` is an unauthenticated string.** No-self-approval is a comparison, so any caller can name an approver that is not themselves. The strongest remaining hole once confinement lands |
| `RISK-08` | **Ranex does not gate its own repository.** `gates.yaml` requires a command a hermetic tree cannot run. This is why the SLICE-004 defect got through, and it is §8.4's disconnected gauge. **SLICE-006 and ADR-007 are open against it** — the first engineering work this map's calibration argument directly motivates |
| `RISK-09` | **880 surviving mutants**, 47 in `verdict.py`, and **44 refusals no test executes**. The gauge's own calibration report, unaddressed |
| `RISK-10` | **`mutmut` says nothing about `cli/main.py`** — its selection excludes the tests that exercise it. A green run there is not evidence, and `cmd_run` lives there |
| `RISK-11` | **`evidence.json` is not append-only.** Signatures prevent forgery, but deletion turns a recorded failure into absence. Absence blocks, so this is denial rather than forgery — but it is unbounded |
| `RISK-12` | **The journal has no reader.** `Journal.verify()` has no caller and there is no `journal` command, so the chain is tamper-evident only to the test suite |
| `RISK-13` | **`HOME` is still inherited by Ranex's own git queries**; symlink and submodule trees cannot be observed at all |
| `RISK-14` | **The loop has never closed around a real agent.** No worker port, no dispatch. Five slices have hardened a measurement path that has never measured agent output. This is the largest untested assumption in the system, and hardening has no natural stopping point — every slice ends by naming the next strongest hole |
| `RISK-15` | **One implementer.** No second engineer, no redundancy, and every control in this document is enforced by tests one person wrote |
| `RISK-16` | arc42 is CC BY-SA 4.0; adopting the template as an adaptation in a public repository carries ShareAlike |
| `RISK-17` | **Adopting more of TOGAF than §4.5's four parts recreates the 561-file failure.** This is not a hypothetical: the pre-reset tree was already TOGAF-shaped and produced zero product code. The ADM's overhead is amortised across an enterprise; there is one implementer here. Any proposal to add an ADM phase, a capability level, a maturity score or a compliance grade should be read as this risk materialising |
| `RISK-18` | **This map does not conform to ISO/IEC/IEEE 42010** — no enumerated stakeholders, no concerns traced to them, no declared viewpoints, no correspondences (§0.2). Its `PR-*` rows are therefore assertions derived from conversation rather than requirements traceable to anyone who wants them. This is the same defect the pre-reset tree recorded as *"every ADR was anchored to an architecture anchored to nothing above it"* |

---

## §12 Glossary

| Term | Meaning |
|---|---|
| **Gauge** | A fixed, external, mechanical standard that decides whether a part passes. Set before the work and unalterable by the producer |
| **Calibration** | Demonstrating that a gauge detects a known defect. A gauge with no calibration result yields no information |
| **Gauge R&R** | Measuring the variance of the measurement system itself — repeatability and reproducibility — rather than of the part |
| **Negative control** | A deliberately bad input run through the system to confirm it is rejected. If it passes, everything since the last good control is suspect |
| **Traveler** | The record that accompanies work through every station, stamped at each. An unstamped part does not ship |
| **Jidoka / andon** | Stopping on a detected defect rather than continuing confidently. Stopping is correct behaviour |
| **Poka-yoke** | Making the defect impossible rather than catching it later |
| **Bill of materials** | Every part needed to build the whole, with its buy/build decision, its gauge and its status |
| **Routing** | The order of assembly, derived from the parts list's dependencies |
| **ABB / SBB** | TOGAF: Architecture Building Block — the capability required — versus Solution Building Block — what implements it. An ABB with no SBB is an unfilled part |
| **Baseline / Target / Gap** | TOGAF: what exists, the finish line, and the difference between them, which is the parts list |
| **Transition Architecture** | TOGAF: an intermediate state that must deliver value on its own, not merely be closer to done |
| **Architecture Contract** | TOGAF: the signed agreement an implementer must satisfy. Ranex's frozen task envelope, and Phase G is the checking of it (§4.5) |
| **Phase G** | TOGAF ADM Implementation Governance — conformance of built work to the agreed target. The phase Ranex automates |
| **Viewpoint / view / concern / correspondence** | ISO 42010: a concern matters to a stakeholder; a viewpoint frames concerns; a view is governed by a viewpoint and addresses concerns; a correspondence is a checkable relation between description elements |
| **DOE** | Design of Experiments — deliberately varying factors so their effects are separable |
| **Worker envelope** | The full production configuration: model, harness version, skill and tool manifest, prompt digest |
| **Wedge / moat** | The problem that sells today versus the property that remains defensible after copying |
| **Subject digest** | The exact bytes a piece of evidence refers to |
| **Slice** | One small end-to-end capability, with an ADR behind it and a test proving each done-criterion |
| **`NOT_ASSESSED`** | No attempt was made. Never a pass |

---

## §13 Slice Ledger

Every slice, what it validated, and **what it disproved**. The second column is
the one that matters; a ledger recording only successes is a brochure.

| Slice | Delivered | Disproved |
|---|---|---|
| `SLICE-001` evidence production | `ranex run` executes a command, records exit code and tree digest, emits evidence the gate accepts. Target committed red at `b495e3635` before any implementation existed | — |
| `SLICE-002` evidence authenticity | Ed25519 signatures verified against a committed keyring; keyring and catalog read from the commit, not the working tree | **Closed twice, reopened twice.** Audits found the tests narrower than reality (17 defects across four audits); then the trust-root check was skipped entirely for a path the commit did not carry, so an attacker-named catalog was read unchecked |
| `SLICE-003` claim↔command binding | The committed catalog declares the argv satisfying a claim; a signed record of `true` no longer satisfies `tests-executed`. Six audits failed to break the binding | The same audits reproduced **six ways to get a false PASS around it** — one root cause, all frozen as deliberately-failing tests |
| `SLICE-004` hermetic observation | The bound command runs against a materialisation of the subject commit, every blob checked against the tree's object id, environment built from empty, toolchain pinned | **Closed, reopened, closed again.** The first close rested on a cleanup control that had never worked on any supported Python, covered by a test that monkeypatched out the function it was named for, and on a mutation check **run by hand by the actor who wrote the code**. Measuring the general form found **59 refusals no test executed**. Two capabilities were deliberately withdrawn: trees needing installed dependencies, and trees carrying symlinks or submodules, can no longer be observed |
| `SLICE-005` confinement | **Withdrawn 2026-08-03 before any implementation**, never committed. ADR-006 stands; the slice was re-sequenced behind SLICE-006 | — |
| `SLICE-006` gate a real test suite | Open. Nothing built. Closes `RISK-08` — reconnecting the gauge to the part, so that Ranex can gate Ranex | — |

**The pattern across five slices, stated because it is the most reliable
information in this document:** every slice that was closed on the implementer's
own report was later reopened. Every reopening was caused by a measurement the
implementer did not run. The project's own history is the strongest available
evidence for §1.1 — and the substitution of `mutmut` and `diff-cover` for
self-report in SLICE-004 is the only structural change that has ever stopped it.

**No slice has yet governed work produced by an agent.**

---

## Maintenance

Update when a slice closes, an ADR is accepted, or a `PROVISIONAL` claim gains or
loses evidence. Promote to `CONFIRMED` only on executed evidence; demote whatever
a slice contradicts. Record the command and its working directory beside every
number.

**The next artefact is the bill of materials (§5.5), not a longer version of this
document.** `1.1.0` was a good document that failed because it was prose, and
prose has no size limit, no mechanism forcing it to match reality, and no way to
be wrong out loud. If the response to "we need a plan" is "write more here," that
is the failure repeating.
