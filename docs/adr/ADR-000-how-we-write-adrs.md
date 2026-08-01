# ADR-000 — how we write ADRs

**Status:** accepted
**Date:** 2026-08-01
**Decision-makers:** repo owner
**Slice:** n/a — this ADR governs the others

## Context and Problem Statement

CLAUDE.md now requires an ADR before any slice is opened. It did not say what an
ADR is. An unspecified format is a format each session reinvents, and the agents
writing these documents are the specific failure mode this repo already survived
once: 561 architecture files, zero product code.

Two failure modes have to be prevented at the same time, and they pull in
opposite directions. Under-specify and an agent fills the gaps by assuming —
prose that sounds like a decision and records none. Over-specify and the
document becomes the work. The format must be complete enough that nothing is
left to invention, and capped tightly enough that it cannot become the product.

## Decision Drivers

- An agent with an ambiguous instruction will assume rather than ask.
- Anything checkable must be checked, or it will drift within three sessions.
- The docs cap is not negotiable — this repo has failed this exact way before.
- Whatever is required must be *researchable*, not a matter of taste.
- Reviewers need the same shape every time to read these quickly.

## Prior art

- **MADR 4.0.0** (2024-09-17), the maintained standard — four templates: full,
  minimal, bare, bare-minimal. Frontmatter keys `status`, `date`,
  `decision-makers`, `consulted`, `informed`, all optional:
  <https://github.com/adr/madr/blob/4.0.0/template/adr-template.md>
- **Michael Nygard, "Documenting Architecture Decisions"** (2011) — the
  Context/Decision/Consequences skeleton, and the superseding rule verbatim: "If
  a decision is reversed, we will keep the old one around, but mark it as
  superseded":
  <https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
- **Y-statements** (Zdun, Capilla, Musil et al.) — the one-sentence decision
  form: <https://www.infoq.com/articles/sustainable-architectural-design-decisions/>
- **Kent Beck, *TDD By Example*** — "Run all tests and see the new one fail" as a
  numbered step; and his own list of TDD deviations (tests without assertions,
  expected values copied from computed output):
  <https://newsletter.kentbeck.com/p/canon-tdd>
- **Martin Fowler** — coverage is a signal not a target, and assertion-free
  suites reach 100%: <https://martinfowler.com/bliki/TestCoverage.html>,
  <https://martinfowler.com/bliki/AssertionFreeTesting.html>,
  <https://martinfowler.com/articles/practical-test-pyramid.html>
- **Google Code Review Developer Guide** — the twelve-point review list and the
  standard ("definitely improves the overall code health… even if the CL isn't
  perfect"): <https://google.github.io/eng-practices/review/reviewer/looking-for.html>
- **Bacchelli & Bird, ICSE'13** — modern code review is "less about defects than
  expected", which is why anything compilable into a check must be:
  <https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/>
- **Yuan et al., OSDI'14** — 92% of catastrophic failures come from incorrect
  handling of non-fatal errors; most were reachable by simple error-path tests:
  <http://petertsehsun.github.io/soen691/current/papers/osdi14-paper-yuan.pdf>
- **arc42 §10** (measurable quality scenarios, never adjectives),
  **C4 model** (use only the levels that add value), **ISO/IEC/IEEE 42010 §6.10**
  (recording decisions and rationale), **Cockburn** (ports and adapters),
  **ISO 25010:2023** (nine quality characteristics), **STRIDE**,
  **Dan North** (Given-When-Then), **ISTQB** (equivalence partitioning, boundary
  values, decision tables, state transitions), **Bezos 2015 letter** (Type 1 /
  Type 2 doors): <https://arc42.org/overview>, <https://c4model.com/>,
  <https://alistair.cockburn.us/hexagonal-architecture/>,
  <https://dannorth.net/blog/introducing-bdd/>,
  <https://s2.q4cdn.com/299287126/files/doc_financials/annual/2015-Letter-to-Shareholders.PDF>
- **Ahmeti et al., ECSA'24** — review gates and standardised tags counter ADR
  rot; undefined thresholds ("major" decisions) are a primary cause of it:
  <https://rebekkaa.github.io/files/2024_ECSA.pdf>
- Books, cited as works and not as any mirror of them: **Khorikov, *Unit
  Testing*** — "resistance to refactoring": implementation-coupled tests block
  correct implementations, which is the standing hazard of this repo's
  freeze-tests-before-BUILD rule. **Feathers, *Working Effectively with Legacy
  Code*** — characterization tests pin behaviour that no spec records.
  **Ousterhout, *A Philosophy of Software Design*** — prefer defining errors out
  of existence to enumerating them. **Tornhill, *Your Code as a Crime Scene***
  — review hotspots and temporal coupling mined from VCS history.
  **Forsgren, Humble & Kim, *Accelerate*** — external approval boards do not
  improve stability and do slow delivery; peer review does. **Saltzer &
  Schroeder (1975)**, separation of privilege — the principle behind this
  project's no-self-approval invariant:
  <https://web.mit.edu/Saltzer/www/publications/protection/>

## Considered Options

1. **Nygard's five-part skeleton.** Smallest, best-adopted. Rejected alone: says
   nothing about tests, threats, or reversibility, so agents fill those by
   assumption — the exact failure being prevented.
2. **MADR 4.0.0 full template, unmodified.** Rejected as the enforcement target:
   its option headings are variable strings (`### {title of option 1}`) and
   cannot be compiled into a fixed check. Its `bare` variant is worse — the H1 is
   an HTML comment, so an untouched scaffold passes a naive check.
3. **MADR minimal + `### Confirmation` + project sections.** Chosen.
4. **Branch by decision weight** — full template for one-way doors, short form
   for two-way. Rejected: an agent that may choose the light path will argue
   itself onto it. One shape, always.

## Decision Outcome

In the context of AI agents authoring design records, facing their tendency to
assume where a format is silent, we chose **MADR 4.0.0's minimal template plus
`### Confirmation`, plus nine project sections, all mandatory and all line
budgeted**, to make every ADR complete, uniform and checkable, accepting that
this is heavier than MADR intends and that heavier templates are adopted less
readily.

Sixteen sections, fixed order, enforced. MADR-verbatim headings are kept
verbatim so the format stays recognisable and re-adoptable.

### Consequences

- Every ADR answers the same questions in the same order; a reviewer learns the
  shape once.
- Nothing checkable is left to good intentions: order, budgets, citations, sad
  path count, reversibility, and named tests are all asserted.
- Requiring every section and closing the status set **exceeds MADR**. That is
  our choice and must not be attributed to the standard.
- The cost is real. ECSA'24 and adoption studies both find lighter templates get
  used more. Budgets are the counterweight; if ADRs start going unwritten rather
  than being written badly, that is the signal to revisit.
- ADR-001 predates this and needs backfilling to conform.

### Confirmation

`tests/contract/test_docs_discipline.py` is the check. It asserts the section
set, canonical order, per-section line budgets, the total cap, a URL in
`## Prior art`, at least three enumerated sad paths, a `Door:` line, and that
`## Test strategy` names test files that actually exist. An ADR that satisfies
the prose but not the test is not accepted — the test is the authority.

## Improvements on the prior art

1. **Enforced, not encouraged.** MADR ships templates and no checker; ECSA'24
   names review gates as what actually stops rot. Here the format is a test.
2. **Order is fixed.** MADR does not require one. Fixed order is what lets a
   reader — human or agent — find a section without reading the whole file.
3. **Budgets per section.** Neither MADR nor Nygard bounds length. Bounding it is
   what makes "require more sections" safe in a repo with a hard docs cap.
4. **Sad paths are counted.** Prior art asks for consequences; none asks the
   author to enumerate failure modes. Given OSDI'14's 92%, this is the section
   most likely to prevent a real defect.
5. **The test strategy must name tests that exist.** A strategy naming no file is
   a plan to write one later; the check resolves each path on disk.
6. **Placeholders are rejected.** MADR's own `bare` template would pass an
   unfilled scaffold. Ours fails it.

## Architecture surface

No port, no adapter, no runtime code. This ADR governs `docs/adr/` and is
enforced by a contract test. The only coupling to the kernel is that
`tests/contract/test_docs_discipline.py` reads the repo tree; it imports nothing
from `src/ranex/`. No diagram — C4 says use only the levels that add value, and
at this size none do.

## Scope and threat delta

Governs how decisions are recorded, not what they decide. STRIDE letters moved:
**none** — this changes no trust boundary, no signing path, no verdict.

Explicit non-goal: this does not make a recorded decision *correct*. A
well-formatted ADR with a wrong decision passes every check here. Out of scope:
an author who deliberately writes a plausible falsehood — the citation
requirement raises the cost of that, and review is the control, not this test.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Maintainability | a reader locates any section in an unfamiliar ADR | fixed order, ≤300 lines |
| Functional correctness | a non-conforming ADR reaches `main` | suite fails before merge |
| Usability | an agent writes a conforming ADR from the template alone | zero ambiguity per section |

## Reversibility

Door: two-way

The template can be revised by superseding this ADR. Existing ADRs are
append-only — per Nygard, a reversed decision is marked superseded, not edited —
but the *format* is not load-bearing on any runtime behaviour, so changing it
costs a backfill and nothing else.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | ADR missing a required section | suite fails, names the section |
| 2 | sections present but reordered | suite fails, prints got vs expected |
| 3 | section over its line budget | suite fails, names section and count |
| 4 | ADR over the total cap | suite fails |
| 5 | `## Prior art` with no URL | suite fails — an ADR with no citation is an opinion |
| 6 | fewer than three enumerated sad paths | suite fails |
| 7 | no `Door: one-way\|two-way` line | suite fails |
| 8 | `## Test strategy` names no test file | suite fails |
| 9 | test strategy names a file that does not exist | suite fails, lists the absent paths |
| 10 | unfilled `{placeholder}` left in the document | suite fails, names file and line |
| 11 | slice opened with no ADR link | suite fails |
| 12 | slice links an ADR that does not exist | suite fails |
| 13 | status outside the closed set | suite fails |
| 14 | ADR is well-formed and the decision is wrong | **not caught** — review's job, stated plainly |

## Test strategy

All enforcement lives in `tests/contract/test_docs_discipline.py`, at the
contract level: these are rules about the repo, not about a unit, and there is
nothing to mock. Red-then-green was followed — every check above was observed
failing against the non-conforming ADR-001 before ADR-000 existed.

Levels: contract only. No unit tests (no unit), no e2e (no runtime path). The
ordinal pyramid invariant does not apply to a suite with one level.

Coverage: **no percentage is required, here or in any ADR.** Assertion-free
suites reach 100% (Fowler), and coverage is a review-time signal, not a
threshold. Where a slice needs a coverage statement it states delta coverage on
changed lines and full coverage of error branches, nothing global.

Sad paths 1–13 above each map to a named test in that file; sad path 14 is
declared uncatchable rather than tested, which is the honest outcome.

## Code review checklist

Adapted from Google's reviewer guide; the standard is "definitely improves
overall health", not perfection.

- Does the decision answer the problem actually stated in Context?
- Is every claim in `## Prior art` traceable to the cited URL, and read closely
  enough to surface that source's *known weakness*?
- Does `## Improvements on the prior art` say what we changed and why, or does it
  restate the prior art?
- Are the sad paths real failure modes, or restatements of the happy path?
- Does `### Confirmation` name a check that would actually fail if violated?
- Do the frozen tests assert **behaviour** rather than internal shape? Tests
  coupled to a signature block correct implementations (Khorikov), and this repo
  freezes tests before BUILD — so the hazard is structural, not hypothetical.
- Does the file's git history show it as a hotspot or temporally coupled to
  something this ADR does not mention (Tornhill)?
- Is anything here that belongs in code, a commit message, or the slice file?

## More Information

Supersede this ADR rather than editing it. The fill-in template follows; copy it
verbatim and replace every `{...}` placeholder. Section budgets are in
`_SECTION_BUDGET` in the contract test — that dict is authoritative, not this
prose.

```markdown
# ADR-NNN — {short title naming problem and chosen solution}

**Status:** proposed
**Date:** {YYYY-MM-DD}
**Decision-makers:** {who decided}
**Slice:** `docs/slices/SLICE-NNN-{name}.md`

## Context and Problem Statement
{What is broken or undecided, in prose. Cite file:line for the defect. 14 lines.}

## Decision Drivers
{Bulleted forces that constrain the choice. 10 lines.}

## Prior art
{How this is already solved elsewhere. At least one URL — required. Name each
source's known weakness, not only its design. 32 lines.}

## Considered Options
{Numbered options, each with one line on why it was rejected or chosen. 14 lines.}

## Decision Outcome
{A Y-statement: in the context of X, facing Y, we chose Z, to achieve W,
accepting V. Then the concrete change. 14 lines.}

### Consequences
{What becomes true, good and bad. Include what this does NOT close. 14 lines.}

### Confirmation
{The executable check that fails if this decision is violated. 12 lines.}

## Improvements on the prior art
{Numbered. What we changed from the cited design and why. 22 lines.}

## Architecture surface
{Port and adapter touched, or "no port — direct domain call". No diagrams. 10 lines.}

## Scope and threat delta
{What this governs; the STRIDE letters it moves or "none"; one explicit non-goal
and the attacker deliberately out of scope. 10 lines.}

## Quality attributes
{Table: characteristic | scenario | measure. ISO 25010 vocabulary. Measurable,
never adjectives. 10 lines.}

## Reversibility
Door: {one-way | two-way}
{What undoes this: rollback, format compatibility, migration. 8 lines.}

## Sad paths
{Numbered table: input/failure -> required behaviour. At least 3; aim for every
boundary and error branch. Derive them by a named technique (equivalence
partitions, boundary values, decision table, state transitions). Mark anything
deliberately not caught. 34 lines.}

## Test strategy
{Which levels and why. Every sad path maps to a named test. Name real files
under tests/ — they are resolved on disk. Red-then-green evidence. No global
coverage percentage. 32 lines.}

## Code review checklist
{What a reviewer must check that no test can. 14 lines.}

## More Information
{Links, superseded ADRs, open questions. 12 lines.}
```
