# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-29 (installed operator CLI, issue #63)
**Active slice:** docs/slices/SLICE-075-installed-operator-cli.md

## Where we stopped

T0 of SLICE-075 is complete: ADR-038 (hatchling under the frozen epoch) is
accepted with vendored prior art, and tests/contract/test_packaging.py is
frozen red at 3 failed / 2 passed — red for the right reasons (build-system,
non-virtual lock + epoch, sdist). No product bytes have changed yet.

The repository remains a pre-release, source-run Python kernel (see issue #55
for the real-data acceptance baseline); its public CLI covers gate, journal,
run, suite, deps, keygen, and task commands.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-075 T1 packaging enablement (hatchling bytes + deliberate
epoch-preserving re-lock), then T2 installed-CLI evidence, T3 operator docs
and slice close, T4 coverage-floor re-derivation.

## Governance

ADR-038 decides the installed operator CLI: hatchling build system, drop
`package = false`, keep `[project.scripts]`. Never run bare `uv lock` or
epoch-less `uv build` — a bare lock silently drops the `[options]`
exclude-newer epoch (probe-verified; now contract-enforced in
test_packaging.py). Build backends are not pinned by uv.lock; hatchling is
bounded only by pyproject requires plus the epoch discipline.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
(superseded by the 2026-08-25 kernel-only scope reset).

## Known limits

- The source CLI needs `PYTHONPATH=src`; no installed command is available
  yet (SLICE-075 open; removed in T3).
- `task delegate` records a nonzero suite exit but returns orchestration success.
- Free-prompt fanout has no A/B/C child admission; batch qualification cannot publish.
- Journal verification cannot detect an internally consistent older snapshot.
- Strict-local requires an operator-retained delegated cgroup and trusts a same-UID controller.
