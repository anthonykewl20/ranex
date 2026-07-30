# RFC-0008: Select the Static Type Checker Required by `LANG-TYPECHECK-001`

| Field | Value |
|---|---|
| Status | ACCEPTED |
| Owner | Human owner |
| Authors | Assistant, from local measurement and a Grok-4.5 refutation pass, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; discharges the deferred selection in `ADR-0014` `LANG-TYPECHECK-001` |
| Affected contexts | `configuration_management`, `assurance`, `process_assurance`, `module_governance` |
| Supersedes | Nothing. Fills a selection `ADR-0014` deliberately deferred |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:122` |

## Decision question

`ADR-0014` `LANG-TYPECHECK-001` requires a strict-mode static type checker as a
blocking gate, and explicitly defers **which** checker to a separate decision
made "against evidence current at selection time," recording "the conformance and
performance figures observed at that time," preferring "specification conformance
over execution speed where they conflict," and pinning "the tool and its version."

This RFC recommends **`pyrefly`, pinned at `1.1.1`**.

## Evidence

All figures below were measured on 2026-07-30. Nothing is cited from memory.

### Specification conformance

Parsed directly from the official `python/typing` conformance suite results
(`python/typing`, `conformance/results/results.html`), 141 test cases:

| checker | version tested | full Pass | Partial | Unsupported |
|---|---|---|---|---|
| basilisk | 0.27.0 | 141 (100.0%) | 0 | 0 |
| zuban | 0.8.2 | 140 (99.3%) | 1 | 0 |
| **pyrefly** | **1.1.0** | **135 (95.7%)** | 6 | 0 |
| pyright | 1.1.410 | 134 (95.0%) | 5 | 2 |
| pycroscope | 0.4.0 | 120 (85.1%) | 20 | 1 |
| ty | 0.0.50 | 101 (71.6%) | 30 | 10 |
| mypy | 2.1.0 | 83 (58.9%) | 52 | 6 |

### Conformance rank does not predict defect detection

This is the decisive finding and it inverts the naive reading of the table above.

A six-case smoke test was written against defect classes that have actually
harmed this repository, then run against every candidate. Full harness, cases and
raw results accompany this RFC.

| case | basilisk | pyrefly | ty | zuban |
|---|---|---|---|---|
| empty container with no element type | caught | **caught** | missed | missed |
| unvalidated `json.load()` value crossing a boundary | missed | missed | missed | missed |
| `Optional` dereferenced without narrowing | missed | **caught** | caught | caught |
| wrong argument type | caught | **caught** | caught | caught |
| attribute that cannot exist | missed | **caught** | caught | caught |
| correct code — must stay silent | silent | **silent** | silent | silent |
| **detection** | 2/5 | **4/5** | 3/5 | 3/5 |
| **false positives** | 0/1 | **0/1** | 0/1 | 0/1 |

`basilisk`, the only checker at 100% conformance, does not detect
`len(name)` where `name: str | None`, nor an access to an attribute that does not
exist. Both are detected by `pyrefly`, `ty`, `zuban`, `mypy --strict`, and
`pyright` — six independent checkers. **FACT**, reproduced.

Fairness controls applied before drawing that conclusion:

- `basilisk` splits rules across `check` (PEP-tagged rules only) and `analyze`
  ("every rule *not* tagged `pep`"). Both were run, with every documented rule
  tag set to `error` in `[tool.basilisk.rule-tags]`. The configuration was
  confirmed live — enabling it changed output on a different case.
- The version splice was eliminated. `basilisk` **0.27.0**, the exact version
  measured at 141/141, misses both cases as well. The gap is not a regression
  introduced after the conformance run.

**INFERENCE:** the conformance suite measures agreement with specified typing
behaviour, not defect-finding power over ordinary code. A perfect score is
therefore compatible with missing elementary errors. `ADR-0014` instructs that
conformance be preferred over *speed*; it does not instruct that conformance be
preferred over *detecting defects*, which is the provision's actual purpose.

### Performance

Measured against this repository's `scripts/architecture/`, 54,840 lines:

| checker | version | wall | max RSS |
|---|---|---|---|
| basilisk | 0.38.0 | 0.24 s | 41 MB |
| **pyrefly** | **1.1.1** | **0.51 s** | 154 MB |
| ty | 0.0.65 | 0.62 s | 130 MB |
| zuban | 0.9.0 | 0.66 s | 63 MB |

Every candidate is fast enough that speed is not a discriminator. Under
`ADR-0014` this axis yields to conformance and, as argued above, to detection.

### Version drift between the measured and the installable

`ADR-0014` requires citing conformance figures *and* pinning a version. For some
candidates those two obligations cannot both be met honestly:

| package | conformance figure describes | installable today | releases between |
|---|---|---|---|
| basilisk-python | 0.27.0 (2026-07-05) | 0.38.0 (2026-07-29) | **11** |
| **pyrefly** | **1.1.0 (2026-06-17)** | **1.1.1 (2026-06-18)** | **0** |
| ty | 0.0.50 | 0.0.65 (2026-07-29) | 14 |
| zuban | 0.8.2 | 0.9.0 (2026-06-23) | 0 |

`pyrefly`'s published conformance figure describes software one day and zero
releases from the artifact that would be pinned.

### Licensing and the right to continue the tool

| candidate | repository licence | package metadata licence |
|---|---|---|
| **pyrefly** | **MIT** (`facebook/pyrefly`) | **MIT** |
| ty | MIT (`astral-sh/ty`) | MIT |
| basilisk | MIT (`Nimblesite/Basilisk`) | **none declared on PyPI** |
| zuban | `NOASSERTION` (`zubanls/zuban`) | **Other/Proprietary** |
| pyright | `NOASSERTION` | PyPI package is a third-party wrapper, "not affiliated with Microsoft," which fetches Node at run time |

This repository carries an open, recorded failing gap: dependency licences are
unregistered (`ADR-0014` v1.1.0). A tool with absent or contradictory licence
metadata worsens a known deficiency. `zuban`'s terms additionally foreclose the
continuation right described below.

### Reproducibility of the standard-library stubs

A checker whose stub source can move will return different verdicts on identical
code. This was tested rather than assumed.

- **FACT:** `pyrefly` returns identical results with all network egress directed
  at a dead proxy, and creates no stub or cache store on disk, while still
  resolving `len` and the `Sized` protocol from the standard library.
  **INFERENCE:** its stubs are embedded in the released binary, so pinning the
  package version pins the stubs. A true network-namespace test was attempted and
  denied by the sandbox; this is recorded rather than claimed as proven.
- **FACT:** `basilisk`'s own CycloneDX SBOM declares a `basilisk-typeshed-fetch`
  component; it ships a `typeshed` subcommand documented as the only place
  downloading happens; and it emits `typeshed_source_unpinned` until
  `typeshed-commit` is set to a full 40-character SHA. Its stub source is a
  second moving part requiring a second pin.

One pinnable artifact is preferable to two under this project's reproducibility
requirement.

### Supply-chain evidence

`pyrefly` ships a **CycloneDX 1.5 SBOM** inside its distribution, declaring 317
components with SPDX licence expressions. `ty` (300 components) and `basilisk`
(338) do the same. Adopting a candidate that ships an SBOM adds machine-readable
licence evidence rather than adding unregistered dependencies. This does not
close the existing `jsonschema` / `PyYAML` / `rfc8785` gap.

### Continuation right

`ADR-0014` requires the tool be pinnable; the owner additionally requires that
Ranex be able to continue a tool that is abandoned. An MIT licence plus a
self-contained binary and a public source repository satisfies this: the artifact
is complete and the licence permits a fork. This is the reason licence ambiguity
is treated as disqualifying rather than cosmetic.

## Recommended provisions

### `TYPECHECK-TOOL-001` — `pyrefly` is the selected checker, pinned

The checker is `pyrefly`, pinned to an exact version, currently `1.1.1`. The pin
is a declared tool choice and is registered in the licensing manifest. Changing
it requires a new decision recording conformance and performance figures current
at that time.

### `TYPECHECK-STRICT-001` — strict mode, failing closed

`pyrefly` runs with `preset = "strict"` in a committed configuration file. A
non-zero exit blocks. Verified: the tool exits non-zero on a defect and is
deterministic across repeated runs.

### `TYPECHECK-DEBT-001` — existing errors are a recorded finding, not a waiver

Strict mode currently reports **265 errors** across `scripts/architecture/`, of
which **133 are `implicit-any-empty-container`** — the same defect class as the
329 unconstrained arrays in the generated schema tree. These are recorded as a
finding. The gate is not weakened, no baseline is adopted, and no rule is demoted
to make existing code pass.

### `TYPECHECK-BOUNDARY-001` — static checking does not discharge boundary validation

No candidate detected the `json.load()` value returned as a declared `int`. This
empirically confirms `ADR-0014`'s requirement that runtime validation at trust
boundaries is separately required. Selecting a checker does not satisfy it.

### `TYPECHECK-BENCH-001` — the selection harness is retained and owned

The six-case harness is kept in the repository as the reproducible basis of this
decision and the means of evaluating any future replacement. A candidate
replacing `pyrefly` must be run through it and must not regress detection or
false-positive counts.

## Predeclared acceptance tests

1. A committed `pyrefly` configuration exists, sets strict mode, and pins an
   exact version; validation reports `LANG-TYPECHECK-001` satisfied only when all
   three hold.
2. Introducing `len(x)` where `x: str | None` fails the gate.
3. Introducing an access to a non-existent attribute fails the gate.
4. Correct, fully annotated code produces zero diagnostics.
5. The gate exits non-zero whenever any error is reported.
6. Two consecutive runs over identical input produce byte-identical output.
7. Running with network egress blocked produces identical results.
8. The recorded 265-error debt is visible as a finding; no configuration demotes
   those rules to warnings to obtain a pass.
9. A proposed replacement checker is evaluated by the retained harness, and its
   detection and false-positive results are recorded in the superseding decision.

## Consequences and evidence standing

- `LANG-TYPECHECK-001` becomes satisfiable, but is **not satisfied on acceptance**:
  265 existing errors must be resolved before the gate can pass. That is a stated
  gap, not a compliance claim.
- One development dependency is added. It ships an SBOM; its licence is MIT in
  both the repository and the package metadata.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`. This
  decision declares no readiness tier and authorizes no product code.
- The rejected candidates are recorded with reasons so the decision can be
  attacked later on its evidence rather than re-argued from preference.

## Human approval

The human owner directed that the conformance-versus-detection question be tested
rather than assumed, that the Basilisk finding be subjected to an explicit
refutation attempt before it was relied upon, and that the continuation right be
treated as a selection criterion. This RFC records those directions and awaits
acceptance of the provisions above.
