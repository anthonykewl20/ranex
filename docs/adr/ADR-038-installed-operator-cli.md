# ADR-038 — installed operator CLI

**Status:** accepted
**Date:** 2026-08-29
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-075-installed-operator-cli.md`

## Context and Problem Statement

Issue #63: an operator cloning Ranex gets `ModuleNotFoundError` unless they
export `PYTHONPATH=src`. The cause is structural: `pyproject.toml` declares
`[project.scripts] ranex = "ranex.cli.main:main"` but `[tool.uv] package =
false` (its only key) and no `[build-system]`, so `uv.lock` records ranex as
`source = { virtual = "." }` and nothing is ever built or installed.
Acceptance-audit baseline 420b94cef1aeb592b37a10f7a2a2927acc1b7bce; uv 0.11.26.
The kernel needs an installed console command for milestone v0.1.0.

## Decision Drivers

- An operator command must work without `PYTHONPATH=src` (issue #63).
- The frozen lock epoch `2026-08-04T00:00:00Z` is a trust root; builds must not escape it.
- The backend choice must be buildable under that epoch, verified empirically.
- Version stays 0.0.0; the 0.1.0 bump belongs to umbrella #66's release slice.
- The wheel must not ship governance or native trees (per-repo trust roots, on-host launcher).
- Frozen contracts are not weakened; no existing test changes.

## Prior art

- Searched: `site:docs.astral.sh uv build backend default`; PyPA "writing pyproject.toml" entry points console scripts; GitHub code search `hatchling src layout default file selection wheel`; `uv lock exclude-newer` lockfile epoch behavior; both candidate backends probed on this machine 2026-08-29 (uv 0.11.26).
- https://github.com/pypa/hatch/blob/4b3fd7d6d8435312b16fe8e8a317be5244a81b23/docs/plugins/builder/wheel.md — hatchling's wheel-builder documentation: its default file-selection heuristic ships `src/<NAME>/__init__.py` as the package with no extra configuration, which is exactly Ranex's `src/ranex` layout.
  License: MIT.
  Weakness: version-matched to the `hatchling-v1.31.0` tag documentation rather than a pinned release artifact, and the vendored copy passed through a text-converting fetch so its whitespace may differ from the raw upstream object.
  Vendored: `docs/adr/prior-art/ADR-038/hatch-wheel-builder.md` blob:946df8f89fd3e43d0df8809727d3db30396d37d7
- https://github.com/astral-sh/uv/blob/0.11.26/docs/concepts/projects/config.md — uv's projects/config documentation: a `[build-system]` makes uv build and install the project (editable by default), `[project.scripts]` entry points require one, and `tool.uv.package = false` suppresses installation — the exact mechanism behind issue #63's failure.
  License: MIT OR Apache-2.0.
  Weakness: it documents the frontend's current default backend (`uv-build`), which is empirically unbuildable under our frozen epoch, and page snapshots drift across uv releases.
  Vendored: `docs/adr/prior-art/ADR-038/uv-projects-config.md` blob:f4e7fa70f704e77665c0412e76766e0984d3ce64
- Rejected: https://github.com/astral-sh/uv/tree/main/crates/uv-build — uv_build, the uv-docs default backend, is empirically unbuildable under the frozen epoch: `uv build --exclude-newer 2026-08-04T00:00:00Z` with `requires = ["uv-build>=0.12.7,<0.13"]` exits 2 (only uv-build ≤ 0.12.1 predates the epoch; 0.12.7 was published 2026-08-27), and a bare epoch-less build escapes the trust root.
- Rejected: https://github.com/pypa/setuptools — setuptools' implicit `setuptools.build_meta:__legacy__` fallback, or keeping `package = false` with a hand-rolled PATH wrapper / documented `PYTHONPATH=src` invocation, leaves build behavior undeclared or the operator path hand-rolled — exactly the failure issue #63 rejects.

## Considered Options

1. uv_build, the uv-docs default. Rejected: exit 2 under the frozen epoch.
2. Keep `package = false` plus a wrapper script or documented `PYTHONPATH`. Rejected: hand-rolled operator path.
3. setuptools legacy fallback. Rejected: implicit, undeclared build behavior.
4. hatchling with a deliberate epoch-preserving re-lock. Chosen.

## Decision Outcome

Adopt hatchling: `[build-system]` with `requires = ["hatchling"]` and
`build-backend = "hatchling.build"`; drop `[tool.uv] package = false`; keep
`[project.scripts] ranex = "ranex.cli.main:main"`. Re-lock deliberately with
`uv lock --exclude-newer 2026-08-04T00:00:00Z` — the ranex lock entry becomes
`source = { editable = "." }`, the `[options]` epoch is preserved, and only
two lock hunks change — and always build with the same flag. Wheel scope is
exactly the `ranex` package plus dist-info; governance/, native/, tests/, and
docs/ are excluded. The sdist is the VCS-tracked repo, re-verified with
`.git` present in T1. Version stays 0.0.0; the 0.1.0 bump is a release-gate
edit in umbrella #66's slice, touching pyproject, the re-lock, and the frozen
exe literal in test_trace_schema.py together.

### Consequences

- Good: after T1, `uv run --frozen ranex --help` exits 0 with the full command tree, no `PYTHONPATH`.
- Good: the epoch discipline survives the T1 re-lock (`[options]` preserved).
- Good: after T1 the wheel is minimal — no governance/native fork of per-repo trust roots.
- Bad: bare `uv lock` silently drops the epoch; a contract test now guards it.
- Bad: hatchling is not lock-pinned; only pyproject `requires` plus the epoch bound it.
- Bad: after T1 every `uv run --frozen` in CI builds the project — a build break bricks all gates.

### Confirmation

Probed 2026-08-29, uv 0.11.26, in an epoch-preserved scratch copy of the tree:
- Hatchling under the epoch: `uv build --exclude-newer 2026-08-04T00:00:00Z` exit 0 (hatchling resolves to 1.31.0, pre-epoch); uv-docs default `uv-build>=0.12.7,<0.13` exit 2 (only ≤ 0.12.1 pre-epoch; 0.12.7 published 2026-08-27).
- Bare `uv lock`: "Resolving despite existing lockfile due to removal of global exclude newer" — silently drops the `[options]` epoch; contract-enforced in tests/contract/test_packaging.py.
- Probe wheel: top level exactly `ranex/` + `ranex-0.0.0.dist-info/`, `[console_scripts] ranex = ranex.cli.main:main`, Version 0.0.0, Requires-Python `<3.15,>=3.11`.
- Probe sdist (`.git`-less copy; T1 re-verifies VCS selection): pyproject, src, README, LICENSE, tests, docs, governance, native, uv.lock under `ranex-0.0.0/`.
- Editable install at `src/`: `import ranex` resolves there; `uv run --frozen ranex --help` exit 0.
- Scratch-copy contracts: test_trace_schema.py 19 passed, test_docs_discipline.py 65 passed, test_ci_workflow.py + test_real_suite_entrypoint.py 14 passed.

## Improvements on the prior art

1. Bind the backend to the repo's frozen epoch instead of accepting the
   frontend's default, which is empirically unbuildable here.
2. Keep the operator command the standard entry-point mechanism
   (`[project.scripts]`) rather than a wrapper script.
3. Exclude governance/native/tests/docs from the wheel deliberately:
   governance files are per-governed-repo cwd trust roots and the native
   launcher is built on-host.
4. Record the bare-`uv lock` epoch drop as a permanent contract test rather
   than a documented caveat.

## Architecture surface

`pyproject.toml` gains `[build-system]` and loses `package = false`;
`uv.lock`'s ranex entry moves virtual→editable. No file under `src/ranex/`
changes in T1; the CLI surface {gate, journal, run, suite, deps, keygen,
task} is unchanged.

## Scope and threat delta

No new authority enters any build or installed artifact; the wheel carries
only existing kernel code. The trust-root set is unchanged: the lock epoch
remains the resolution bound, and hatchling sits outside uv.lock — bounded
by `requires` plus the epoch, recorded as a weakness rather than hidden.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Installability | fresh clone, `uv run --frozen ranex --help` | exit 0, no PYTHONPATH |
| Epoch discipline | lock and build under the frozen epoch | `[options]` preserved, exit 0 |
| Wheel hygiene | inspect wheel members | `ranex/` + dist-info only |
| Honesty | version metadata | 0.0.0 until the #66 release slice |

## Reversibility

Door: two-way

Removing `[build-system]` and restoring `package = false` returns the tree to
the virtual state mechanically; the re-lock is two hunks.

## Sad paths

- A bare `uv lock` silently drops the `[options]` epoch ("Resolving despite existing lockfile due to removal of global exclude newer") — now a permanent contract test.
- An epoch-less `uv build` resolves post-epoch backends: the explicit `uv_build` probe (backend `uv_build`, `requires=["uv-build>=0.12.7,<0.13"]`) exited 2 under the epoch, and a bare epoch-less build escapes to post-epoch uv_build — always pass the flag. The current tree, having no `[build-system]`, instead rides uv's documented legacy fallback (`setuptools.build_meta:__legacy__`, per the vendored uv config doc), which is why the two wheel-shape tests pass red-state while the pyproject/lock/sdist tests fail (3F/2P).
- The backend version is not lock-pinned: hatchling 1.31.0 here may drift to a newer release elsewhere within `requires`.
- Build isolation needs the network or a warm uv cache — offline CI can fail at the hatchling fetch.
- Sdist member selection depends on `.git` presence (fallback vs VCS) — T1 re-verifies with `.git`.
- Every `uv run --frozen` now builds the project; a build break bricks all gates at once.
- Installed-metadata version resolution silently changes trace `exe` semantics on version bumps — the frozen test literal couples pyproject, lock, and test.
- A wheel accidentally shipping `governance/` or `native/` would fork per-repo trust roots.
- Editable vs non-editable installs diverge in coverage paths and console-script import path.

## Test strategy

`tests/contract/test_packaging.py` is the frozen-red acceptance gate (5
tests; 3 failed / 2 passed at open: build-system, non-virtual lock + epoch,
sdist). `tests/contract/test_docs_discipline.py` governs this ADR.
`tests/contract/test_trace_schema.py` keeps the `exe` literal honest through
installed-metadata resolution. `tests/contract/test_ci_workflow.py` and
`tests/contract/test_real_suite_entrypoint.py` must stay green after the
re-lock.

## Code review checklist

- Verify the build-system bytes are exactly hatchling and `package = false` is gone.
- Verify every lock/build command in docs and CI carries `--exclude-newer 2026-08-04T00:00:00Z`.
- Verify the wheel contains only `ranex/` + dist-info and the console script points at `ranex.cli.main:main`.
- Verify version metadata is 0.0.0 and no release claim is added.

## More Information

Issue #63 carries the observed `ModuleNotFoundError`/`PYTHONPATH=src`
failure and the acceptance criteria. Umbrella #66 owns the 0.1.0 release
edit. SLICE-075 executes this decision in tranches T1–T4.
