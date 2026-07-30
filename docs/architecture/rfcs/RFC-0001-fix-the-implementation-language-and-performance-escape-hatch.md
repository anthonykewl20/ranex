# RFC-0001: Fix the Implementation Language and Its Performance Escape Hatch

| Field | Value |
|---|---|
| Status | ACCEPTED |
| Owner | Human owner |
| Authors | Assistant, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; no expiry claimed |
| Affected contexts | `configuration_management`, `governed_execution`, `assurance`, `policy`, `module_governance`, `compatibility`, `migration`, `release_management`, `process_assurance` |
| Supersedes | Nothing. Converts an undeclared inherited assumption into a stated proposal |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted (`rfcs/README.md` Status) |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/CORE_SDLC_OPERATING_MODEL.md:577` (changes route through RFC/ADR policy) |

## Decision question

Ranex is written in Python and no accepted decision says so. Should Python be
fixed as the implementation language, and under what conditions may a
performance-critical component depart from it?

## Full-map impact

- **Contexts:** all listed above; no context gains or loses ownership.
- **Public APIs:** none change.
- **State owners:** unchanged.
- **Effect owners:** unchanged.
- **Lifecycles:** none added. A compiled component admitted under
  `LANG-EXCEPTION-001` would be an implementation detail behind an existing port.
- **Trust/security boundaries:** unchanged, with one addition — this RFC requires
  runtime validation at boundaries that accept externally supplied values, which
  today is inconsistently applied.
- **Attachment points preserved:** `ADR-0007` module boundaries and port
  direction are preserved; no new dependency direction is introduced.
- **Product inclusions/exclusions changed:** none.

## Context and evidence

### Facts

Each item is measured in this repository or verified against an external source
on 2026-07-30, and labelled accordingly.

1. **No accepted ADR states the implementation language.** Verified by reading
   all thirteen accepted ADRs. `ADR-0007:220` writes packaging rules around
   Python package discovery under `src/ranex` without deciding on Python.
2. **The tooling is Python and pins three dependencies.** Measured:
   `scripts/architecture/pyproject.toml` requires `>=3.12` and pins
   `jsonschema==4.25.1`, `PyYAML==6.0.2`, `rfc8785==0.1.4`. The kernel tracer
   pins `>=3.11,<3.15` with `PyYAML` only.
3. **The heaviest workload completes in 2.29 seconds at 82 MB peak RSS.**
   Measured: `validate_contracts.py` over 157 schemas, 1,021 architecture
   elements, and more than 40,000 assertion cases.
4. **That speed is not attributable to compiled dependencies.** Measured by
   inspecting the installed environment: `jsonschema` 4.25.1 and `rfc8785` 0.1.4
   contain zero compiled extension modules and run as pure Python; only
   `PyYAML` 6.0.2 ships one. `sqlite3` and `hashlib` are standard-library C.
   Interpreted Python does the bulk of the work and still finishes in 2.29 s.
5. **Python's annotations are not enforced at runtime, and this has already
   produced defects here.** The kernel audits of 2026-07-30 found a controller
   accepting values whose declared types are `EvidenceRecord` and `bool` with no
   runtime check, reaching a security-relevant decision.
6. **Type-checker landscape, verified externally 2026-07-30.** Pyright reports
   the highest typing-specification conformance (~97.8%); Meta's Pyrefly reached
   stable 1.0 in May 2026 with substantially faster execution; Astral's `ty` is
   alpha; `mypy` trails at ~58% conformance. No type checker is configured in
   any Ranex package today; `ruff` is a linter and does not discharge this.
7. **Version horizon, verified externally 2026-07-30.** Python `3.12` has
   security support to approximately October 2028. `3.15` is scheduled for
   2026-10-01, so the kernel's `<3.15` ceiling expires roughly three months from
   this RFC.

### Assumptions

1. Ranex remains a single-host system with SQLite as its transactional
   authority. If that changes, fact 3 must be re-measured.
2. AI workers remain the primary labour force under `ADR-0001` and `ADR-0011`.
3. The corpus continues to grow at a rate where fact 3 stays comfortably inside
   any plausible budget. This is an assumption, not a measurement — the 2.29 s
   figure is a point observation at one revision, not a trend.

### Unknowns

1. **No quality-attribute budget exists for any performance-critical workload**
   under `ADR-0004`. Without one, "fast enough" is undefined and no exception can
   be evaluated. This is the principal unknown.
2. Which type checker will be selected, and its conformance and performance
   figures at selection time.
3. Whether any Ranex workload will ever be compute-bound. No evidence either way.

### Conflicts

1. **Against the product's own purpose.** Ranex compiles contracts into
   checking code and fails closed; selecting a language whose type declarations
   are advisory means Ranex must implement by hand what other languages
   guarantee. This RFC does not dissolve that tension — it bounds it with
   `LANG-TYPECHECK-001` and boundary validation.
2. **No conflict with `ADR-0005`/`ADR-0011`.** Provider-neutral, fallback-free
   routing constrains model routing, not implementation language.

## Requirements and non-goals

**Requirements.** State the language; keep the reasoning checkable; require the
mitigation for the property the language lacks; and leave a legitimate,
evidence-gated path for a performance-critical component so that a future
measured need has a remedy other than reversing this decision.

**Non-goals.** Selecting a type checker; authorizing any compiled component;
declaring readiness; authorizing product code; registering a performance budget.

## Alternatives

### Option A — Rewrite in a compiled language (Rust, Go)

Buys enforced types at compile time and removes an entire defect class.
Rejected: it discards the only components in the repository that execute and
pass, restarts a defect-repair history already paid for, forfeits AI-worker
generation reliability, and is proposed against a measured hot path of 2.29
seconds. Reconsider only if a registered budget is breached and
`LANG-EXCEPTION-001` proves insufficient in aggregate rather than per component.

### Option B — Two first-class languages: Python harness, compiled kernel

Rejected at this time. It doubles toolchain, review, and supply-chain surface
while `IMPLEMENTATION_START_READY` is undeclared and the kernel is an unaudited
R&D tracer with open BLOCKER-class findings. `LANG-EXCEPTION-001` reaches the
same end state incrementally and under measurement.

### Status quo — leave the language undeclared

Rejected. It is the defect this RFC exists to close: a load-bearing assumption
enacted everywhere and declared nowhere, which is the same class as the kernel
audit's blocking finding on undeclared state authority.

## Proposed design

### `LANG-PRIMARY-001` — Python is the implementation language

Every Ranex component is written in Python, minimum `3.12`, with an upper bound
declared per package and re-verified against the official release schedule
whenever changed. Reasons, each independently checkable: the obligations are
document and schema obligations that Python's standard library and three pinned
dependencies cover directly; the dominant cost is not compute (fact 3); the only
components that execute and pass are already Python; the labour force is AI
workers, for which generation reliability is an engineering property rather than
a preference; and the dependency surface stays small and licence-auditable.

### `LANG-TYPECHECK-001` — Static type checking is a required gate

A static type checker in strict mode is required for every Ranex package and
blocks at `IMPLEMENTATION_START`. **Which checker is a separate decision**, made
against evidence current at selection time, weighting specification conformance
over speed, with the tool and version pinned and the observed figures recorded.
Naming one from stale knowledge would itself be a defect.

This does not substitute for runtime validation. Both are required: static
checking for code Ranex owns, runtime validation for values crossing into it. A
boundary that accepts an unvalidated externally supplied value fails closed.

### `LANG-EXCEPTION-001` — Compiled components require a measured budget breach

A component may be compiled, or a Python inner loop replaced by a compiled
extension, only when all of the following hold:

1. A quality-attribute budget for the workload is registered under `ADR-0004`
   first. "Faster" is not a budget; a latency, throughput, or resource target is.
2. A reproducible measurement shows the Python path fails that budget, naming
   workload, revision, method, and figures. Unmeasured or projected claims do
   not qualify.
3. Cheaper mitigations were attempted and recorded — algorithmic change,
   caching, incremental or parallel execution, precompiling validators for
   reuse, or substituting a faster implementation of an existing dependency.
   Compiled components are the last option.
4. The component sits behind a declared port under `ADR-0007`, and its removal
   requires no caller change.
5. Determinism and fail-closed behaviour are preserved and proven: byte-identical
   results to the Python path over the same inputs, demonstrated by a
   differential test, and closed failure on error. A compiled component may not
   hold canonical state, become a second source of truth, or make or
   short-circuit an authority decision.
6. Toolchain and target platforms are pinned, the build is reproducible, and
   every added artifact carries a licensing-manifest entry.
7. The owner authorizes the specific component. This provision authorizes a
   path, not any particular component.

An exception does not alter `LANG-PRIMARY-001`.

## Dependency and file-structure impact

No new runtime dependency. `LANG-TYPECHECK-001` adds one development dependency
when the checker is selected. No module moves. Promotion to an ADR changes the
accepted-ADR count from thirteen to fourteen, which is pinned in both
`generate_contracts.py` and `validate_contracts.py` and must be updated at
source, never in generated output.

## Data, state, event, and transaction impact

None. No schema, state axis, transition, or event changes.

## Security, privacy, and secrets

Positive: `LANG-TYPECHECK-001` and the boundary-validation requirement address a
defect class already observed reaching a security-relevant decision. A compiled
component would add native-code and supply-chain review surface, which is why
condition 6 pins the toolchain and requires licence registration.

## Compatibility, migration, rollback, and upstream sync

Additive and declarative; no existing artifact changes meaning. Rollback is
deletion of the ADR and its registration. Upstream sync is unaffected — the
inherited Hermes tree is already Python.

## Operations, backup, and recovery

No operational impact. No runtime exists.

## Predeclared acceptance tests

Stated before acceptance, as `ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST`
requires.

1. **Registration.** After promotion, the accepted-ADR registry contains
   fourteen entries and validation returns `PASS`; the count is changed in
   generator and validator source, and no generated file is hand-edited.
2. **Language conformance.** No Ranex package declares a language other than
   Python, and every package declares a minimum of at least `3.12` and an
   explicit upper bound.
3. **Type-checking gate is registered and failing-closed.** Before a checker is
   selected, `LANG-TYPECHECK-001` is recorded as unsatisfied and blocking at
   `IMPLEMENTATION_START` — not as satisfied, and not as absent. A run that
   reports it satisfied without a configured, pinned checker fails this test.
4. **Exception path is inert until used.** With no registered budget and no
   authorized exception, no compiled artifact exists in any Ranex package. A
   compiled artifact present without a recorded owner authorization fails.
5. **Negative test for condition 2.** An exception request citing no
   reproducible measurement, or a projected future breach, is rejected.
6. **No relaxation.** Acceptance changes no existing check's strictness and
   declares no readiness tier; `IMPLEMENTATION_START_READY` and
   `PRODUCTION_READY` remain `NOT_ASSESSED`.

## Specialist review

Not performed. A security and supply-chain review is owed before any exception
under `LANG-EXCEPTION-001` is granted, not before this RFC is accepted.

## Independent challenge

Not yet performed on this RFC. Relevant history: a first draft asserted from
recall that the tooling dependencies were C-backed; local inspection disproved
it (fact 4). The corrected finding strengthens rather than weakens the
conclusion, but the episode is recorded because an unverified external claim in
a governance artifact is a defect regardless of whether the conclusion survives.
An independent adversarial review of this RFC is recommended before promotion.

## Reconciliation

Open items, none of which block acceptance and all of which are stated rather
than defaulted: the type checker is unselected (`LANG-TYPECHECK-001`); no
performance budget is registered under `ADR-0004`; and the kernel's `<3.15`
ceiling expires around 2026-10-01.

## Human decision requested

Accept, amend, or reject. Specifically:

1. Fix Python as the implementation language per `LANG-PRIMARY-001`.
2. Make strict static type checking a required gate per `LANG-TYPECHECK-001`,
   with the tool chosen separately against current evidence.
3. Adopt `LANG-EXCEPTION-001` as the route for performance-critical components,
   or amend its seven conditions — the owner raised raw performance as a concern,
   and the threshold should be one the owner considers reachable when genuinely
   needed rather than one that forecloses the case in practice.
