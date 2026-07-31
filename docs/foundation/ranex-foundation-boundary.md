# The Ranex foundation boundary

**Date:** 2026-07-31 · **HEAD:** `f2c04c167`

What is inside the Ranex foundation, what is outside it, and what rule decides.
Companion to [`hermes-inventory.md`](hermes-inventory.md) (measurements) and
[`hermes-retention-matrix.md`](hermes-retention-matrix.md) (classifications).

---

## The boundary rule

> **A component is inside the Ranex foundation if removing it would change a
> verdict, or if a verdict cannot be produced without it. Everything else is
> outside, regardless of how useful it is.**

This rule is derivable from contracts already accepted, not invented here:

- `BC-5` — *removing model access changes no verdict*. Anything reachable only
  from a model call is therefore outside by construction.
- `BC-4` — *identical inputs, byte-identical output*. Anything contributing a
  hidden or ambient input is outside, or must be made an explicit input.
- Walking skeleton §12 — *never recorded as fact: anything the evaluated party
  asserts about its own work*. Anything that lets the evaluated party influence
  its own verdict is outside.

The rule is deliberately narrow. It does not ask whether a component is good,
maintained, or already written. Hermes contains 656,809 lines of Python that are
all three, and none of it passes this rule.

---

## Inside the boundary

Everything below is present at `HEAD`, Ranex-original, and executing. **FACT** —
sizes from `wc -l`, test result from `pytest -q`.

### The evidence kernel — Slice 0, preserve untouched

| Component | Path | Size |
|---|---|---:|
| Contract generator | `scripts/architecture/generate_contracts.py` | 23,224 |
| Contract validator | `scripts/architecture/validate_contracts.py` | 32,860 |
| Record-freshness check | `scripts/architecture/check_record_freshness.py` | 231 |
| Contract tree lock | `scripts/architecture/contract_tree_lock.py` | 67 |
| Kernel tests | `test_adr17_owner_resolution.py`, `test_contract_concurrency.py` | 377 |
| Schemas | `schemas/` | 196 JSON |
| Generated contracts | `architecture/contracts/` | 47 registries |
| Accepted decisions | `docs/architecture/decisions/` | 21 ADRs |

State: contract validation `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`,
generator idempotent, CI green across five required checks.

**This is the working Slice 0 governance and evidence kernel the brief requires
preserved. No foundation work touches it.** It has no Hermes lineage —
`generate_contracts.py` and `validate_contracts.py` were both first added in
`032adf368` as Ranex-authored work.

### The product core — Slice 1's subject

| Component | Path | LOC | Responsibility |
|---|---|---:|---|
| Canonicalisation | `src/ranex/foundation/canonical.py` | 26 | "Stable compact JSON suitable for hashing kernel records" — RFC 8785 + SHA-256 |
| Identity | `src/ranex/foundation/identity.py` | 53 | Producer / approver identity |
| Gate domain | `src/ranex/policy/domain/gates.py` | 101 | Gate and rule types |
| Verdict domain | `src/ranex/governed_execution/domain/verdict.py` | 207 | "Deterministic gate evaluation" — absence blocks, subject binding, self-approval refusal |
| Journal | `…/adapters/persistence/sqlite/journal.py` | 94 | "Append-only evaluation journal, hash-chained" |
| Catalog loader | `…/policy/adapters/configuration/yaml/slice_gate_loader.py` | 99 | "Load one gate definition from a YAML catalog" |
| Gate catalog loader | `…/yaml/gate_catalog_loader.py` | — | Catalog parsing, duplicate-rule refusal |
| Policy contracts | `src/ranex/policy/api/contracts.py` | 15 | Port definitions |
| Composition root | `src/ranex/bootstrap/composition.py` | 73 | "The composition root" — the only place wiring happens |
| Confinement | `src/ranex/cli/confinement.py` | 44 | "Repository confinement" — implements refusal of absolute paths, traversal, remote targets. ⚠ **Not imported by `cli/main.py`; not in force.** See readiness assessment **G6** |
| CLI | `src/ranex/cli/main.py` | — | One subcommand; no model reachable |
| **Total product source** | `src/ranex/` | **1,050** | 30 files |
| **Tests** | `tests/` | **573** | 5 files, **36 passing in 0.18 s** |

Layered per `ADR-0007`: `domain` → `api` → `application` → `adapters`, with
`bootstrap/composition.py` as the sole composition root.

### The dependency surface

**FACT**, `grep -rh '^import \|^from ' src/ranex` and `pyproject.toml`:

```
stdlib       argparse · dataclasses · enum · hashlib · json · pathlib
             re · sqlite3 · subprocess · sys · typing · uuid
third-party  yaml (PyYAML >=6.0.2,<7)          ← the only one
first-party  ranex.*
```

**One third-party runtime dependency.** This is the foundation's single most
valuable property and the easiest to lose. Every capability discussed in this
audit — provider routing, credential brokerage, gateways, plugins — arrives with
a dependency tree attached.

---

## Outside the boundary

### Outside and absent — nothing to do but keep it out

All 656,809 lines of Hermes Python and the ~4,400 non-Python code files. Not in
the tree, not an ancestor, not import-reachable. Enumerated per subsystem in
[`hermes-inventory.md` §2](hermes-inventory.md).

The boundary here is enforced by a fact rather than a rule: **there is no import
path.** `git ls-tree -r HEAD -- agent hermes_cli tools gateway cron plugins
skills apps web ui-tui acp_adapter tui_gateway` returns **0 files for every
one**.

### Outside but present — reference material, correctly labelled

Git refs (`phase/*`, `upstream-sync`, `remotes/upstream/*`), the filesystem
archive at `/home/soultransit/devtony/ranex-worktree-archive-2026-07-31/`, and
the tracked Hermes research and architecture documents.

These are **data and prose, never code on an import path**. They stay because
`DEC-RANEX-006` requires provenance and `ADR-0013` has 65 open obligation rows
that cite them.

### Outside and deferred — capabilities Ranex will need but does not have

Provider adapters · worker dispatch · fleet orchestration · scheduling ·
the delivery port (`DEC-RANEX-022`, Telegram-first) · loopback web/TUI ·
work-item lifecycle.

Each is authorised in principle by an accepted decision and unbuilt. Each needs
its own slice. **None is on Slice 1's path**, and the walking skeleton §5 lists
most of them under explicit exclusions whose addition "ends the slice."

---

## The three boundaries that must not be crossed

Not new policy — restatements of accepted contracts, gathered here because each
is a place where a plausible, well-intentioned change would quietly break the
product thesis.

### 1. No model may be reachable from a verdict

`BC-5`. Today this holds by construction: the entire import surface is listed
above and contains no HTTP client, no provider SDK, no credential source.

**How it breaks:** not by someone adding a model call to `verdict.py`. It breaks
by a "small" convenience — an LLM-assisted explanation of a failure, a
model-classified error message — that shares a module with the verdict path.
`agent/error_classifier.py` and `tool_result_classification.py` are what that
looks like at scale.

**Check:** the import surface above is short enough to read in full. Read it.

### 2. Absence must block, and no component may soften that

`PR-03` / `ASR-02` / `BC-2` — *"Never a default, never a skip."* Demonstrated
executing at [inventory §5](hermes-inventory.md).

**How it breaks:** by adopting something that looks like an evidence store and
is passive. Hermes ships exactly that — `agent/verification_evidence.py`, whose
own docstring says it "never decides to run a suite, never blocks completion."
Same name, same storage engine, same record shape, opposite semantics. It would
import cleanly, pass review, and make Slice 1 always pass.

**Check:** any component claiming to hold evidence must have a test that proves
it **refuses** on absence. A component only ever observed passing is not
evidence — acceptance criterion 2.

### 3. The evaluated party may not influence its own verdict

Walking skeleton §12 and `BC-6`. Demonstrated: `self-approval refused: worker
produced evidence and approved it`, exit 1.

**How it breaks:** through extension points. `verify_hooks.py` shows the shape —
a plugin resolves the directive that steers the verification loop. In-process
extension of a gate is the gate's own bypass. `DEC-RANEX-019` already requires
external extensions to be out-of-process, capability-scoped, and **outside
authority**.

**Check:** no in-process extension point in `src/ranex/` without an explicit
decision.

---

## What changed about the boundary as a result of this audit

**Nothing in the code. One thing in the understanding.**

Before: the boundary was assumed to be a line to be *cut* through an inherited
Hermes codebase, with foundation work meaning extraction and removal.

After (**FACT**, executed provenance): the cut already happened, before this
lineage began. The boundary is a line to be *held*. Foundation work therefore
means **maintaining an inventory and a set of triggers**, not performing
surgery.

That is a substantially cheaper posture, and it is the direct reason
[`removal-sequence.md`](removal-sequence.md) recommends **no removal commits at
all** before Slice 1 resumes.

---

## Where the boundary is weakest

Recorded so it is not mistaken for a solved problem.

1. **The boundary is documented, not enforced.** Nothing in CI fails if
   `src/ranex/` grows an HTTP client or a second third-party dependency. The
   short import surface is a fact about today, not a guarantee about tomorrow.
   The cheapest closure is an import-surface assertion in the test suite —
   deferred, because it is new functionality and the brief forbids building any.

2. **`ADR-0006` `DEC-RANEX-008` describes a strangler migration with nothing to
   strangle.** Stale premise, currently harmless, flagged in
   [`hermes-retention-matrix.md`](hermes-retention-matrix.md) ADR review ⚠ 2.
   Deliberately left un-superseded.

3. **`develop` is load-bearing for CI and easy to mistake for dead.** Commit
   Commit `0533e1eaf` is reachable from **four refs**, not one — `architecture/validated-baseline-20260728`, `develop`, `feature/deterministic-gate-controller-mvp` and `origin/develop` (**measured 2026-07-31**; the handoff and the workflow comment at `.github/workflows/architecture-contracts.yml:75-76` both say "no other ref" and are **wrong**). Both the `drift` and `validate` jobs read git objects from it. Deleting or force-pushing it breaks
   CI outright. It is branch-protected; the risk is a future reader concluding
   the branch is Hermes residue and removing it.

4. **`refs/codex/**` — 15 refs, 11 copyrighted PDF blobs, public `origin`.**
   Unresolved by owner choice. Not Hermes-derived, but inside the same object
   database as everything above.
