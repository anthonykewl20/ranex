# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (dogfood/oss_bench harness-audit fix)
**Active slice:** none

## Where we stopped

Harness-audit fix on the dogfood/oss_bench loop, not the kernel. oss_bench
now parses test node ids (no argv[3]), resolves RANEX_SIGNING_KEY and
PYTHONPATH absolutely before the child cwd, and classifies pile rows that
judged this kernel's journal or ran `pytest pytest pytest` as
`harness_fault`. `proofs.summary()` reports 0 false passes, 0 kernel false
blocks, 9 harness faults on the existing append-only pile (files not
edited). Independent canonical JSON matches the kernel (`ensure_ascii=False`,
non-ASCII sample). Evolution census is per-function coverage; iterate
refuses a filtered ledger write; bench uses a fresh scratch per repeat.

## Next

Re-run a nightly divergence with an absolute `--out` so new pile rows are
task-local. Close F-005 remaining items (journal head anchor; interval-
honest wording). Owner decision on F-004. More permissively-licensed
external repos.

## Governance

ADR-038/009 unchanged. No kernel, contract, or suite-manifest ID changes.
New tests live at `tools/dogfood/test_harness_guards.py` (not the frozen
suite).

## Known limits

Same as before: trainer labels are host-relative; no journal head anchor;
mutmut UNVERIFIED; the 18-mutant battery is the control.
