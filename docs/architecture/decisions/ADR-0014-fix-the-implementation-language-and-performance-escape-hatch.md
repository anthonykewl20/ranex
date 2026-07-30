# ADR-0014: Fix the Implementation Language and Its Performance Escape Hatch

| Field | Value |
|---|---|
| ADR ID | `ADR-0014` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-30 |
| Effective revision | Working tree based on `a573502a8`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `configuration_management`, `governed_execution`, `assurance`, `policy`, `module_governance`, `compatibility`, `migration`, `release_management`, and `process_assurance` |
| RFC | [`RFC-0001`](../rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md), accepted by the human owner on 2026-07-30 |
| Supersedes | No fixed decision; converts an undeclared inherited assumption into a stated decision with a bounded exception path |
| Review/expiry date | Review on any measured budget breach admitted under `LANG-EXCEPTION-001`, any change of runtime host or storage engine, any type-checker selection, or the expiry of a declared version ceiling |
| Compatibility/migration class | Additive declaration of the existing state plus one new gated exception path; no existing artifact changes meaning |
| Security/data class | Public architecture decision; dependency, supply-chain, and build evidence retain their own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-30 | Initial accepted decision, promoted from `RFC-0001`. Records the implementation language, which the first thirteen accepted ADRs assume and none states, and answers the owner's raw-performance concern with a measured baseline and a bounded exception path rather than a language change. |

## Context

Ranex is written in Python. Until this decision, nothing decided that.

The choice is load-bearing and was undeclared. `ADR-0007:220` writes packaging
and module-boundary rules around Python package discovery under `src/ranex`; the
contract compiler and validator are approximately 50,000 lines of Python; the
kernel R&D tracer is Python. No accepted ADR named the language.

This is the same defect class as the kernel audit finding of 2026-07-30, in
which the load-bearing inference *"the relational snapshot, not journal replay,
is canonical state authority"* was enacted by code and declared nowhere. Under
this project's own standard an unreported inference is a defect regardless of
whether it is correct. This ADR does not change the language; it declares it and
bounds the case in which departing from it is legitimate.

### Evidence

Each item is measured in this repository or verified against an external source
on 2026-07-30, and labelled accordingly. Unverified recall is not admitted as
evidence here.

1. **Measured.** `scripts/architecture/pyproject.toml` requires `>=3.12` and
   pins `jsonschema==4.25.1`, `PyYAML==6.0.2`, `rfc8785==0.1.4`. The kernel
   tracer pins `>=3.11,<3.15` with `PyYAML` only.
2. **Measured.** `validate_contracts.py` — the heaviest workload in the
   repository, covering 157 schemas, 1,021 architecture elements, and more than
   40,000 assertion cases — completes in 2.29 seconds at 82 MB peak resident set.
3. **Measured.** That speed is not attributable to compiled dependencies.
   Inspection of the installed environment shows `jsonschema` 4.25.1 and
   `rfc8785` 0.1.4 contain zero compiled extension modules and execute as pure
   Python; only `PyYAML` 6.0.2 ships one. `sqlite3` and `hashlib` are
   standard-library C. Interpreted Python performs the bulk of the work and still
   completes in 2.29 seconds.
4. **Measured.** Python's annotations are not enforced at runtime, and this has
   already produced defects here: the kernel audits found a controller accepting
   values whose declared types are `EvidenceRecord` and `bool` with no runtime
   check, reaching a security-relevant decision.
5. **Verified externally.** Pyright reports the highest typing-specification
   conformance (approximately 97.8%); Meta's Pyrefly reached stable 1.0 in May
   2026 with substantially faster execution; Astral's `ty` is alpha; `mypy`
   trails at approximately 58% conformance. No type checker is configured in any
   Ranex package; `ruff` is a linter and does not discharge this.
6. **Verified externally.** Python `3.12` has security support to approximately
   October 2028. `3.15` is scheduled for 2026-10-01, so the kernel's `<3.15`
   ceiling expires roughly three months after this decision.

### The owner's concern, and what it resolves to

The owner raised that some parts of Ranex may need raw execution speed. The
concern is registered rather than dismissed, and it resolves to a measurement:
the dominant cost in Ranex is correctness enforcement over documents, not
throughput over data, and no workload in the corpus is compute-bound. The kernel
is a single-host SQLite monolith serialized by `BEGIN IMMEDIATE`; worker
orchestration under `ADR-0005` and `ADR-0011` is dominated by provider
round-trip latency measured in seconds, against which interpreter overhead is not
observable.

Evidence item 3 also identifies where the headroom is. Because schema validation
is presently pure Python, a future budget breach in that workload has cheaper
remedies than a language change — precompiling validators for reuse, or
substituting a faster validator implementation — which `LANG-EXCEPTION-001`
requires be attempted and recorded before any compiled component is authorized.

## Decision

### `LANG-PRIMARY-001` — Python is the implementation language

Every Ranex component — architecture tooling, kernel, adapters, and tests — is
written in Python, minimum version `3.12`, with an upper bound declared per
package and re-verified against the official release schedule whenever changed.
The reasons, each independently checkable:

1. **The obligations are document and schema obligations.** Ranex compiles
   architecture documents into deterministic checks over JSON, YAML, and schemas.
   Python's standard library and the three pinned dependencies cover that domain.
2. **The dominant cost is not compute.** Evidence items 2 and 3.
3. **The existing verified asset is Python.** The compiler and validator are the
   only components in the repository that execute and pass. A language change
   discards the sole working artifact and reintroduces defects already repaired.
4. **The workforce is AI workers** under `ADR-0001` and `ADR-0011`. Python is the
   language those workers generate most reliably. Where the labour force is
   generative models, generation reliability is an engineering property of the
   language choice, not a stylistic preference.
5. **The dependency surface stays small and auditable** — three pinned tooling
   dependencies and one for the kernel, each carrying a licensing-manifest entry,
   consistent with the supply-chain obligations promoted in `ADR-0013`.

### `LANG-TYPECHECK-001` — Static type checking is a required gate

Because `LANG-PRIMARY-001` selects a language whose annotations are not enforced
at runtime, a static type checker in strict mode is a required check for every
Ranex package, and its failure blocks at `IMPLEMENTATION_START`.

**Which checker is a separate decision**, made against evidence current at
selection time rather than named here, because the field moves quickly and a tool
chosen from stale knowledge is itself a defect. Selection must record the
conformance and performance figures observed at that time, must prefer
specification conformance over execution speed where they conflict — Ranex's
interest is enforcement strength, not developer latency — and must pin the tool
and its version. Evidence item 5 is the starting point, not the answer.

This provision does not substitute for runtime validation at trust boundaries.
Both are required: static checking for code Ranex owns, runtime validation for
values crossing into it. Deserialized, duck-typed, or externally supplied values
are validated at the boundary that consumes them, and a boundary that accepts an
unvalidated value fails closed.

### `LANG-EXCEPTION-001` — Compiled components require a measured budget breach

A component may be implemented in a compiled language, or a Python inner loop
replaced by a compiled extension, only when every condition below holds. This is
the owner's raw-performance path, deliberately narrow rather than closed.

1. **A stated budget exists first.** A quality-attribute budget for the workload
   is registered under `ADR-0004` before any exception is sought. "Faster" is not
   a budget; a latency, throughput, or resource target is.
2. **A measurement shows the Python path fails that budget**, naming the
   workload, revision, method, and observed figures, and reproducible. An
   unmeasured or projected claim is not grounds for an exception.
3. **A cheaper mitigation was attempted and recorded** — algorithmic change,
   caching, incremental or parallel execution, precompiling validators for reuse,
   or substituting a faster implementation of an existing dependency. Compiled
   components are the last option, not the first.
4. **The component sits behind an existing port boundary** under `ADR-0007`
   module rules, and its removal or replacement requires no caller change.
5. **Determinism and fail-closed behaviour are preserved and proven.** The
   compiled path produces byte-identical results to the Python path it replaces,
   demonstrated by a differential test over the same inputs, and fails closed on
   error. A compiled component may not become a second source of truth, may not
   hold canonical state, and may not make or short-circuit an authority decision.
6. **The build stays reproducible and licence-clean.** Toolchain and target
   platforms are pinned, the build is reproducible, and every added artifact
   carries a licensing-manifest entry.
7. **The owner authorizes the specific exception**, recorded as an owner decision
   naming the component. This provision authorizes a path, not any component.

An exception granted under `LANG-EXCEPTION-001` does not alter
`LANG-PRIMARY-001`: Python remains the language of the harness, the kernel, and
every authority decision.

## Alternatives considered and rejected

1. **Rewrite in a compiled language now (Rust, Go).** Rejected. It discards the
   only working components in the repository, restarts a defect-repair history
   already paid for, forfeits AI-worker generation reliability, and is proposed
   against a measured hot path of 2.29 seconds. Reconsider only if a registered
   budget is breached and `LANG-EXCEPTION-001` proves insufficient in aggregate
   rather than for one component.
2. **Two first-class languages — Python harness, compiled kernel.** Rejected at
   this time. It doubles toolchain, review, and supply-chain surface while
   `IMPLEMENTATION_START_READY` is undeclared and the kernel is an unaudited R&D
   tracer with open blocking findings. `LANG-EXCEPTION-001` reaches the same end
   state incrementally and under measurement.
3. **Leave the language undeclared.** Rejected; it is the defect this decision
   closes.
4. **Declare Python and add no type-checking obligation.** Rejected. It accepts
   the one property Python does not provide while declining the cheap mitigation,
   in a product whose purpose is enforced correctness.
5. **Forbid compiled components entirely.** Rejected. It would answer the
   owner's concern by ruling it out of order rather than bounding it, and would
   leave a future measured budget breach with no legitimate remedy.

## Predeclared acceptance tests

Declared in `RFC-0001` before acceptance and carried forward unchanged.

1. **Registration.** The accepted-ADR registry includes this ADR and validation
   returns `PASS`; no generated file is hand-edited.
2. **Language conformance.** No Ranex package declares a language other than
   Python, and every package declares a minimum of at least `3.12` and an
   explicit upper bound.
3. **Type-checking gate fails closed while unsatisfied.** Until a checker is
   selected, `LANG-TYPECHECK-001` is recorded as unsatisfied and blocking at
   `IMPLEMENTATION_START` — not as satisfied, and not as absent. A report
   claiming it satisfied without a configured, pinned checker fails this test.
4. **Exception path inert until used.** With no registered budget and no
   authorized exception, no compiled artifact exists in any Ranex package. A
   compiled artifact present without recorded owner authorization fails.
5. **Negative test for condition 2.** An exception request citing no reproducible
   measurement, or citing a projected future breach, is rejected.
6. **No relaxation.** This decision changes no existing check's strictness and
   declares no readiness tier.

## Consequences and evidence standing

The compiler must project this ADR into the accepted-ADR registry, the
architecture-element inventory, the source-of-truth record, the practice profile,
and the licensing manifest, without implying any readiness or runtime claim.

`LANG-TYPECHECK-001` is **not satisfied** at the time of acceptance. No type
checker is configured in any package. That is a stated gap, not a claim of
compliance, and it blocks at `IMPLEMENTATION_START` rather than now.

No exception under `LANG-EXCEPTION-001` exists, and no quality-attribute budget
for a performance-critical workload is registered under `ADR-0004`. The measured
2.29-second baseline is evidence for this decision, not a registered budget.

The kernel's declared `<3.15` ceiling expires around 2026-10-01 and must be
revisited deliberately rather than allowed to block an upgrade silently.

This decision declares no readiness tier, authorizes no product code, and relaxes
no existing check. `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain
`NOT_ASSESSED`.

## Human approval

The human owner accepted `RFC-0001` on 2026-07-30 and is the decision owner of
record for this ADR. The acceptance covers `LANG-PRIMARY-001`,
`LANG-TYPECHECK-001`, and `LANG-EXCEPTION-001` as written above. It does not
select a type checker, register a performance budget, authorize any compiled
component, or declare any readiness tier.
