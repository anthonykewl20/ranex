# ADR-039 — confinement coverage boundary

**Status:** accepted
**Date:** 2026-08-30
**Decision-makers:** repo owner
**Issue:** #67 (pyrefly gate; slice-less maintenance — no slice)

## Context and Problem Statement

`tests/contract/test_ci_workflow.py:88-105` byte-freezes the CI coverage step:
`coverage run --source=src/ranex -m pytest -q`, then `coverage xml`, then
`diff-cover --fail-under=100`. This measures in-process coverage only.
Governed confinement-controller children (`src/ranex/cli/main.py:2713-2738`)
run in a hermetic env allowing only PATH/HOME/TMPDIR/LANG/GIT_*, network
denied, and strip `COVERAGE_PROCESS_START` plus the sitecustomize hook by
design — that stripping is the confinement itself. Fixing the pyrefly
backlog (#67) added type-narrowing asserts and `OSError.errno` formatting in
those regions, adding executable lines diff-cover judges but that this
pipeline structurally cannot instrument. `diff-cover --fail-under=100`
therefore fails on lines that can never be covered without breaking the
invariant being measured.

## Decision Drivers

- Do not change byte-pinned CI text frozen by `test_ci_workflow.py`.
- Do not weaken or bypass the confinement hermetic-env invariant to gain coverage.
- Prefer an existing repo convention over inventing a second one.
- Base `fail_under` on the pipeline that actually enforces the gate.
- Keep the exclusion greppable and scoped, not a blanket opt-out.
- Preserve runtime behavior of the asserts — this is bookkeeping, not deletion.

## Prior art

Searched: GitHub code search 'coverage.py exclude_lines pragma no cover',
'diff-cover fail-under compare-branch', readthedocs config exclusions page;
both tools' docs fetched pinned 2026-08-30.

- https://github.com/coveragepy/coveragepy/blob/7.15.3/doc/config.rst —
  exclusion semantics: `exclude_lines`/`exclude_also` regexes,
  `pragma: no cover` is a DEFAULT pattern preserved by `exclude_also`;
  excluding a line introducing a block excludes the whole block; `[run]`
  patching subprocess requires `COVERAGE_PROCESS_START` copied into child
  envs — exactly what hermetic governed children strip.
  License: Apache-2.0.
  Weakness: the tag holds a docs snapshot that drifts across releases, and
  the vendored copy passed through a text-converting fetch so whitespace may
  differ from the raw upstream rst.
  Vendored: docs/adr/prior-art/ADR-039/coverage-config-exclusions.md blob:42f21fc5d1a47b68a06673d54ef1742f8fa3ba89

- https://github.com/Bachmann1234/diff_cover/blob/47bee8236167ef14201ff96204d46279a7e1dafc/README.rst —
  compares an XML coverage report against `git diff` output, judges
  new/modified lines, `--fail-under=100` returns non-zero below threshold,
  compares against `origin/main` by default.
  License: Apache-2.0.
  Weakness: it judges diff lines against statement-based coverage reports,
  so a moved multi-line statement can be misjudged unless
  `--expand-coverage-report` is used, and the README documents defaults
  rather than the installed behavior.
  Vendored: docs/adr/prior-art/ADR-039/diff-cover-readme.md blob:c130d7344c72015e4714cc35e31dc4e2dedd7326

- Rejected: https://github.com/coveragepy/coveragepy — wiring subprocess
  coverage into CI (patch subprocess + PYTHONPATH + combine) changes
  byte-pinned CI text the `test_ci_workflow` contract freezes, and the
  wiring cannot reach hermetic governed children without violating the
  confinement invariant it measures; empirically the confined lines stayed
  uncovered anyway (66%→72% total, 11 lines unchanged).
- Rejected: https://github.com/Bachmann1234/diff_cover — an `exclude_also`
  config with a new custom tag (e.g. a ranex-specific marker) introduces a
  second exclusion convention where the repo already has 10
  `# pragma: no cover - <reason>` usages; two conventions dilute
  greppability. Also rejected: driving the controllers from in-process
  tests — requires reconstructing launcher/cgroup/session contexts
  in-process; the controllers exist to own those resources hermetically,
  and forcing that would test the harness, not the invariant.

## Considered Options

1. Add `# pragma: no cover - <reason>` to the eleven confinement-only lines
   using the existing repo convention (10 precedent usages, e.g.
   `src/ranex/foundation/dynamic_runtime.py:24`).
2. Wire subprocess coverage (`COVERAGE_PROCESS_START`, combine) through the
   governed confinement path so children get instrumented.
3. Introduce a new `exclude_also` regex/tag distinct from the existing
   pragma convention.
4. Lower `fail_under` globally instead of excluding specific lines.
5. Derive `fail_under` from the higher-measuring README e2e (subprocess-wired)
   entrypoint instead of the enforcing CI pipeline.

Option 1 was adopted. Option 2 requires stripping the invariant's hermetic env and empirically still missed the lines.
Option 3 duplicates the existing convention. Option 4 hides repo-wide regressions rather than only the eleven named lines.
Option 5 bases the gate on a non-enforcing pipeline.

## Decision Outcome

Mark exactly the eleven confinement-only lines with the existing
`# pragma: no cover - <reason>` convention; add no new exclusion
convention and no `exclude_also` config. The pragma is coverage-bookkeeping
only — the asserts still execute at runtime, and their behavior is proven
by the governed journey suites, not by this unit-coverage gate. Derive
`fail_under` from the pipeline that enforces it (the CI-shaped in-process
run), not the higher-measuring subprocess-wired e2e entrypoint. Both
pipelines are documented in a `pyproject.toml` comment; the floor is the
enforcing pipeline's `floor(TOTAL) − 2`.

### Consequences

- The eleven confinement lines are permanently excluded from diff-cover
  judgment; new confinement-only lines must be pragma'd deliberately, not
  silently.
- `fail_under` no longer drifts upward on a pipeline that never enforces it.
- Anyone auditing coverage must grep `pragma: no cover` and cross-check
  against `src/ranex/cli/host_confinement.py` and
  `src/ranex/foundation/dynamic_runtime.py` line numbers named here.
- No CI workflow text changes; `test_ci_workflow.py` stays green unmodified.
- Runtime safety of the pyrefly-driven asserts is unchanged — proven by
  governed journey suites, not unit coverage.

### Confirmation

- `git grep -n "pragma: no cover" src/ranex/cli/host_confinement.py src/ranex/foundation/dynamic_runtime.py` (scoped to the two files) returns exactly 12 pragma lines:
  11 ADR-039-tagged plus the pre-existing precedent at
  `dynamic_runtime.py:24`.
- `uv run --frozen pytest -q tests/contract/test_ci_workflow.py` stays green,
  proving the byte-pinned CI text is untouched.
- `coverage run --source=src/ranex -m pytest -q && coverage xml &&
  diff-cover --fail-under=100` passes against `origin/main`.
- `pyproject.toml`'s coverage comment names both pipelines and their
  measured totals with dates.

## Improvements on the prior art

- Uses coveragepy's own default `pragma: no cover` pattern
  (`exclude_also`-preserved, per config.rst) rather than a bespoke regex —
  zero new tooling config.
- Reuses the repo's own established idiom (10 prior usages) instead of
  diff-cover's `--expand-coverage-report` workaround for moved statements,
  avoiding a second exclusion mechanism entirely.
- Anchors `fail_under` to the pipeline that actually gates merges, which
  neither vendored doc discusses — coveragepy documents exclusion syntax,
  diff-cover documents its own diffing behavior, and neither prescribes
  which of two divergent pipelines a repo should trust when they disagree.
- Keeps the exclusion count small (11 lines) and named inline in this ADR,
  so a future reviewer can diff the pragma set against this list instead of
  trusting a percentage alone.
- Documents the empirical 66%→72% experiment and its reversion so the next
  session does not re-attempt subprocess coverage under the same
  confinement invariant.

## Architecture surface

- `src/ranex/cli/host_confinement.py` — ten pragma lines in controller
  forks and session reporting (3262, 3269, 4227, 4389, 4420, 4436, 4461,
  4503, 4636, 4612).
- `src/ranex/foundation/dynamic_runtime.py` — one pragma line (485) in the
  confinement-only parse path.
- `pyproject.toml` — coverage/diff-cover config comment naming both
  pipelines and their totals.
- No change to `src/ranex/cli/main.py`'s hermetic env construction
  (2713-2738); this ADR documents it, does not alter it.

## Scope and threat delta

- No change to the confinement hermetic-env allowlist or network denial.
- No change to what CI runs or how `diff-cover` is invoked.
- Threat model unchanged: excluding lines from coverage bookkeeping cannot
  weaken the runtime asserts or the confinement invariant they check.
- Scope is exactly eleven named lines across two files; no directory-level
  or wildcard exclusion is introduced.

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | pragma reasons + this ADR make the exclusion greppable and explained |
| Determinism | gate outcome no longer depends on which pipeline happened to run last |
| Safety | runtime asserts unchanged; only coverage bookkeeping is affected |
| Maintainability | one exclusion convention, not two |
| Coupling | confinement invariant untouched; no coverage wiring added to it |

## Reversibility

Door: two-way

Removing a pragma re-includes the line in diff-cover judgment; if a future
change makes a line reachable in-process (e.g. an in-process test harness
for the controller), delete the pragma and let the line count normally. No
data migration, no journal entry, no schema implicated.

## Sad paths

- A pragma line later gains an in-process test but the pragma is not
  removed — coverage silently hides real coverage. Mitigate: greppable
  reason tag plus review discipline on any PR touching these files.
- `fail_under` gets re-derived from the higher-measuring e2e pipeline
  again — the gate breaks or lies. Mitigated by this ADR and the
  `pyproject.toml` comment naming the enforcing pipeline explicitly.
- Pragma creep — every new confinement line opts out until the percentage
  no longer reflects real coverage. Mitigate: exclusion count is greppable
  and scoped to the ADR-named regions only.
- coverage 7.15.3 auto-combines parallel data files without an explicit
  `combine` step; a future regression removing that behavior could mask a
  missing-combine bug silently.
- diff-cover judges a moved (not added) line as newly added in some diffs,
  re-triggering the gate on confined-region refactors that didn't change
  behavior.
- pyrefly later accepts a weaker fix without the narrowing assert — the
  type-narrowing guarantee is silently lost even though the pragma stays.
- CI and e2e coverage totals drift far apart over time until the
  `pyproject.toml` comment's dual numbers become confusing without dates.
  Mitigate: both totals recorded with the date measured.
- Tree hacks like `git assume-unchanged` used during coverage experiments
  can mask real diffs from review — this session's own cleanup risk.
- A pragma placed on a multi-line statement excludes the whole clause per
  coveragepy semantics, potentially hiding more lines than intended.

## Test strategy

- `tests/contract/test_ci_workflow.py` — asserts the CI coverage step text
  (lines 88-105) is byte-frozen; this ADR changes no line it checks.
- `uv run --frozen pytest -q` — full suite must stay green; the eleven
  pragma'd lines' asserts still execute under governed journey tests and
  are exercised there, just not counted by unit coverage.
- `coverage run --source=src/ranex -m pytest -q && coverage xml &&
  diff-cover --fail-under=100` — run locally against `origin/main` to
  confirm the eleven lines drop out of judgment and the gate passes.
- `git grep -c "pragma: no cover" src/ranex` before and after — count must
  grow by exactly 11 (10 prior usages → 21), scoped to the two named files.
- No new test file is added; this is a coverage-bookkeeping change, not a
  behavior change, so behavior remains proven by existing suites in
  `tests/e2e/` and `tests/security/` that exercise the confinement
  controllers end-to-end.

## Code review checklist

- [ ] Exactly eleven `# pragma: no cover - <reason>` lines added, matching
      the line numbers named in this ADR.
- [ ] No `exclude_also`/config-level exclusion added to `pyproject.toml`.
- [ ] `tests/contract/test_ci_workflow.py` diff is empty.
- [ ] `pyproject.toml` coverage comment names both pipelines, their totals,
      and the measurement date.
- [ ] No hermetic-env allowlist change in `src/ranex/cli/main.py`.
- [ ] Each pragma reason states *why* the line is confinement-only, not
      just "no cover".
- [ ] Full suite (`uv run --frozen pytest -q`) green on the exact commit.

## More Information

- Issue #67 — pyrefly backlog that introduced the narrowing asserts.
- `docs/STATE.md` — session record of the 66%→72% subprocess-coverage
  experiment and its reversion.
- `src/ranex/foundation/dynamic_runtime.py:24` — precedent pragma usage.
- `src/ranex/cli/main.py:2713-2738` — hermetic env construction for
  governed children.
