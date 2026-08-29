# SLICE-075 — installed operator CLI

**Status:** open
**Opened:** 2026-08-29
**Priority:** P0 — milestone v0.1.0 installed operator command (issue #63)
**Issue:** #63
**ADR:** `docs/adr/ADR-038-installed-operator-cli.md`

## Contract

Implement ADR-038. An installed `ranex` console command works without
`PYTHONPATH=src`: `pyproject.toml` declares the hatchling build system and
keeps `[project.scripts] ranex = "ranex.cli.main:main"`; `uv.lock` records
ranex as non-virtual (editable) with the `[options]` exclude-newer epoch
preserved; the wheel ships exactly the ranex package plus dist-info; the
sdist carries the VCS-tracked repo essentials.

## Owned paths

- `pyproject.toml` and `uv.lock`
- `tests/contract/test_packaging.py` — frozen red at open; not modified by this slice's implementers
- README operator docs, `docs/STATE.md`, this slice, ADR-038 and its prior-art directory
- `CLAUDE.md` command block — edits land as a separate owner-directed commit

## Done criteria

1. `tests/contract/test_packaging.py` passes 5/5.
2. `uv run --frozen ranex --help` exits 0 with the full command tree
   {gate, journal, run, suite, deps, keygen, task}, no `PYTHONPATH`.
3. The wheel's top level is exactly `ranex/` + `ranex-0.0.0.dist-info/`, with
   `entry_points.txt` carrying `[console_scripts] ranex = ranex.cli.main:main`.
4. The sdist is re-verified with `.git` present (VCS selection, not the
   `.git`-less fallback) and contains pyproject, src, README, LICENSE,
   uv.lock, and no `.venv/` or `dist/`.
5. `tests/contract/test_trace_schema.py` stays green via installed-metadata
   resolution; the `exe` literal changes only inside the #66 release slice.
6. Docs-discipline, ci-workflow, and real-suite-entrypoint contracts stay
   green after the re-lock.
7. README operator docs describe the installed invocation and drop the
   `PYTHONPATH=src` instruction.
8. No version bump: 0.0.0 until umbrella #66's release slice.

## Tranche plan

- T0 (this tranche, done): ADR-038 accepted with vendored prior art;
  `tests/contract/test_packaging.py` frozen red — 3 failed / 2 passed, red
  for the right reasons (build-system, non-virtual lock + epoch, sdist).
- T1: pyproject bytes + deliberate epoch-preserving re-lock. T1 evidence is
  real-repo evidence with `.git` present — the contract test asserts member
  floors + ignored-path absence, and the `.git`-present VCS-selection member
  set is verified in T1 from the real repo and attached to issue #63. A cold
  uv cache is preferred for at least one full `uv run --frozen` gate run.
- T2: installed-CLI real-data evidence.
- T3: operator docs + slice close. T3 also lands the CLAUDE.md command-block
  and packaging paragraphs (CLAUDE.md lines ~138, ~150-152) as a separate
  owner-directed commit.
- T4: coverage-floor re-derivation.

## Not owned

Issue #60 specification registration; the version bump to 0.1.0 (umbrella
#66 release slice); CI workflow change (expected none).

## Evidence

GitHub issue #63 carries the observed `ModuleNotFoundError` failure and the
acceptance criteria. Frozen-red reference: `tests/contract/test_packaging.py`
— 3 failed / 2 passed at open. ADR-038's Confirmation records the probe
commands and exit codes backing the backend decision.
