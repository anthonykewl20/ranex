# ADR-0018: Select the Static Type Checker Required by LANG-TYPECHECK-001

| Field | Value |
|---|---|
| ADR ID | `ADR-0018` |
| Version | `1.1.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-31 |
| Effective revision | Working tree based on `79d568914`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `configuration_management`, `assurance`, `process_assurance`, `module_governance` |
| RFC | [`RFC-0008`](../rfcs/RFC-0008-select-the-static-type-checker.md), accepted by the human owner on 2026-07-31 |
| Supersedes | Nothing. Discharges the selection `ADR-0014` `LANG-TYPECHECK-001` deliberately deferred |
| Review/expiry date | On any change to the pinned version, or on evidence that the selected tool is unmaintained or relicensed |
| Compatibility/migration class | Additive tooling selection; adds one development dependency; no runtime is enacted |
| Security/data class | Public architecture decision |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-31 | Initial accepted decision, promoted from `RFC-0008`. Selects `pyrefly` pinned at `1.1.1` against evidence measured 2026-07-30. |
| `1.1.0` | 2026-07-31 | Recorded the debt figure produced by the committed configuration (256, with per-rule breakdown) in place of the 265 measured against an uncommitted standalone config, and recorded why the two differ. No provision changed. |

## Context

`ADR-0014` `LANG-TYPECHECK-001` (`ADR-0014:122`) makes a strict-mode static type
checker a blocking gate and explicitly defers **which** checker to a separate
decision, made "against evidence current at selection time," recording "the
conformance and performance figures observed at that time," preferring
"specification conformance over execution speed where they conflict," and pinning
"the tool and its version."

All evidence below was measured on 2026-07-30. None is cited from memory. Seven
candidates were evaluated; three were unknown to the assistant beforehand, which
is itself evidence that the deferral in `ADR-0014` was correct.

## Decision

### `TYPECHECK-TOOL-001` — `pyrefly` is the selected checker, pinned

The checker is `pyrefly`, pinned to an exact version, initially `1.1.1`. The pin
is a declared tool choice and is registered in the licensing manifest. Changing
it requires a superseding decision that records conformance and performance
figures current at that time.

### `TYPECHECK-STRICT-001` — strict mode, failing closed

`pyrefly` runs with `preset = "strict"` in a committed configuration file. A
non-zero exit blocks. Verified by execution: the tool exits non-zero on a defect,
and two consecutive runs over identical input produce byte-identical output.

### `TYPECHECK-DEBT-001` — existing errors are a finding, not a waiver

Under the committed configuration (`scripts/architecture/pyproject.toml`,
`[tool.pyrefly] preset = "strict"`), strict mode reports **256 errors** across
the four files in `scripts/architecture/`, reproducibly:

| count | rule |
|---|---|
| 133 | `implicit-any-empty-container` |
| 45 | `missing-attribute` |
| 40 | `bad-argument-type` |
| 18 | `unsupported-operation` |
| 9 | `bad-index` |
| 3 | `bad-assignment` |
| 3 | `not-iterable` |
| 2 | `no-matching-overload` |
| 1 each | `bad-argument-count`, `bad-return` |

The largest class, `implicit-any-empty-container`, is the same defect as the 329
unconstrained arrays in the generated schema tree: a container whose element type
cannot be derived from its initialiser. Two independent tools therefore identify
one root cause.

These are recorded as a finding. The gate is not weakened, no baseline is
adopted, and no rule is demoted to obtain a pass.

**Figure provenance.** `RFC-0008` cited 265 errors, measured 2026-07-30 against a
standalone strict configuration. The count is now 256 because
`contract_tree_lock.py` and `test_contract_concurrency.py` were subsequently
corrected, removing some. The figure binding this decision is the one produced by
the **committed** configuration, which is the artefact CI executes; a count
measured against a configuration that is not committed is not reproducible
evidence.

### `TYPECHECK-BOUNDARY-001` — static checking does not discharge boundary validation

No candidate detected a `json.load()` value returned as a declared `int`. This
empirically confirms `ADR-0014`'s requirement that runtime validation at trust
boundaries is separately required. Selecting a checker does not satisfy it.

### `TYPECHECK-BENCH-001` — the selection harness is retained

The six-case harness that produced this decision is retained as its reproducible
basis and as the means of evaluating any replacement. A candidate replacing
`pyrefly` must be run through it and must not regress detection or
false-positive counts.

## Evidence

### Conformance rank does not predict defect detection

Parsed from the official `python/typing` conformance suite, 141 cases:
`basilisk` 0.27.0 scored **141/141 (100%)**, `zuban` 0.8.2 140, **`pyrefly` 1.1.0
135 (95.7%)**, `pyright` 1.1.410 134, `pycroscope` 0.4.0 120, `ty` 0.0.50 101,
`mypy` 2.1.0 83 (58.9%).

Against six defect cases drawn from classes that have actually harmed this
repository, detection inverted that ranking:

| case | basilisk | pyrefly | ty | zuban |
|---|---|---|---|---|
| empty container with no element type | caught | **caught** | missed | missed |
| unvalidated `json.load()` crossing a boundary | missed | missed | missed | missed |
| `Optional` dereferenced without narrowing | missed | **caught** | caught | caught |
| wrong argument type | caught | **caught** | caught | caught |
| attribute that cannot exist | missed | **caught** | caught | caught |
| correct code — must stay silent | silent | **silent** | silent | silent |
| detection | 2/5 | **4/5** | 3/5 | 3/5 |
| false positives | 0/1 | **0/1** | 0/1 | 0/1 |

`basilisk`, the only checker at 100% conformance, detects neither `len(name)`
where `name: str | None` nor access to a non-existent attribute. Both are
detected by `pyrefly`, `ty`, `zuban`, `mypy --strict` and `pyright` — six
independent checkers. **FACT**, reproduced.

Fairness controls applied before relying on that finding:

- `basilisk` splits rules across `check` (PEP-tagged only) and `analyze`. Both
  were run with every documented rule tag set to `error`; the configuration was
  confirmed live because enabling it changed output on another case.
- The version splice was eliminated: `basilisk` **0.27.0**, the exact version
  measured at 141/141, misses both cases too. It is not a later regression.
- The finding was submitted to an adversarial refutation pass whose instruction
  was to break it. It returned `VERDICT: SURVIVES`, having identified the version
  splice as the strongest attack; executing that attack closed it.

**INFERENCE:** the conformance suite measures agreement with specified typing
behaviour, not defect-finding power over ordinary code. `ADR-0014` directs that
conformance be preferred over *speed*; it does not direct that conformance be
preferred over detecting defects, which is the provision's purpose.

### Version drift between measured and installable

`ADR-0014` requires citing conformance figures *and* pinning a version. For some
candidates both cannot be satisfied honestly: `basilisk`'s figure describes
0.27.0 (2026-07-05) while 0.38.0 (2026-07-29) is installable — **11 releases**
apart. `ty` is 14 apart. **`pyrefly`'s 1.1.0 and 1.1.1 are one day and zero
releases apart**, so its published figure describes the artifact being pinned.

### Performance

Against `scripts/architecture/`, 54,840 lines: `basilisk` 0.24 s / 41 MB,
**`pyrefly` 0.51 s / 154 MB**, `ty` 0.62 s / 130 MB, `zuban` 0.66 s / 63 MB.
Every candidate is fast enough that speed does not discriminate, so this axis
yields to conformance and detection as `ADR-0014` requires.

### Licensing and the continuation right

`pyrefly` is MIT in both the repository (`facebook/pyrefly`) and the package
metadata. `ty` likewise. `basilisk` is MIT on GitHub but **declares no licence on
PyPI**. `zuban` is `NOASSERTION` on GitHub and **Other/Proprietary** on PyPI. The
PyPI `pyright` package is a third-party wrapper, "not affiliated with Microsoft,"
that fetches Node at run time and therefore cannot be pinned.

This repository carries an open failing gap for unregistered dependency licences
(`ADR-0014` v1.1.0); a tool with absent or contradictory licence metadata worsens
a known deficiency. An MIT licence with a public source repository also preserves
the owner's stated requirement that Ranex be able to continue a tool that is
abandoned — the licence grants the right to fork, at no cost while upstream
remains maintained.

### Stub reproducibility

A checker whose standard-library stub source can move returns different verdicts
on identical code. **FACT:** `pyrefly` returns identical results with all network
egress directed at a dead proxy, creates no stub or cache store on disk, and
still resolves `len` and the `Sized` protocol. **INFERENCE:** its stubs are
embedded in the released binary, so pinning the package pins the stubs. A
network-namespace test was attempted and denied by the sandbox; this is recorded
rather than claimed as proven.

By contrast `basilisk`'s own SBOM declares a `basilisk-typeshed-fetch` component,
it ships a `typeshed` subcommand documented as the only place downloading
happens, and it emits `typeshed_source_unpinned` until `typeshed-commit` is set
to a full 40-character SHA. Its stub source is a second moving part requiring a
second pin.

### Supply-chain evidence

`pyrefly` ships a **CycloneDX 1.5 SBOM** declaring 317 components with SPDX
licence expressions. Adopting it adds machine-readable licence evidence rather
than further unregistered dependencies. This does not close the existing
`jsonschema` / `PyYAML` / `rfc8785` gap.

## Predeclared acceptance tests

1. A committed `pyrefly` configuration exists, sets strict mode, and pins an
   exact version; `LANG-TYPECHECK-001` reports satisfied only when all three hold.
2. Introducing `len(x)` where `x: str | None` fails the gate.
3. Introducing access to a non-existent attribute fails the gate.
4. Correct, fully annotated code produces zero diagnostics.
5. The gate exits non-zero whenever any error is reported.
6. Two consecutive runs over identical input produce byte-identical output.
7. Running with network egress blocked produces identical results.
8. The 256-error debt is visible as a finding; no configuration demotes those
   rules to warnings to obtain a pass.
9. A proposed replacement is evaluated by the retained harness, and its detection
   and false-positive results are recorded in the superseding decision.

## Consequences and evidence standing

- `LANG-TYPECHECK-001` becomes satisfiable but is **not satisfied on acceptance**:
  256 existing errors must be resolved before the gate can pass. That is a stated
  gap, not a compliance claim.
- One development dependency is added, MIT in both repository and package
  metadata, shipping an SBOM.
- Rejected candidates are recorded with reasons so this decision can be attacked
  on its evidence rather than re-argued from preference.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`. This
  decision authorizes no product code and declares no readiness tier.

## Human approval

The human owner accepted `RFC-0008` on 2026-07-31, having directed that the
conformance-versus-detection question be tested rather than assumed, that the
`basilisk` finding be subjected to an explicit refutation attempt before being
relied upon, and that the right to continue an abandoned tool be treated as a
selection criterion.
