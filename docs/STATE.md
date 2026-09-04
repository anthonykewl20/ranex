# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (dogfood page copy honesty fix, #75)
**Active slice:** none

## Where we stopped

Benchmark-page copy fix (#75): PLAIN_FINDINGS for F-001/F-002 said
"we're polishing" / "we're making the skip list explicit" — present-tense
claims of work in progress. FINDINGS.md records both fixes as candidate
directions, not attempted. The page now says the candidate fixes are
written down, not yet started; site regenerated via `dogfood.py report`
(43/43, fingerprint verified, git_head 2f220e622 stamped per
site/INTEGRATION.md freshness rule); README status block refreshed by
the tool. No kernel, contract, or artifact numbers changed.

Before that (0d2bd655e): harness-audit fix on the dogfood/oss_bench loop
(node-id parsing, absolute key/PYTHONPATH resolution, harness_fault
classification, per-function coverage, isolated bench/iterate scratch).

## Next

Re-run a nightly divergence with an absolute `--out` so new pile rows are
task-local. Close F-005 remaining items (journal head anchor; interval-
honest wording). Owner decision on F-004. Attempt the F-001/F-002
candidate fixes (then update the page wording to match). More
permissively-licensed external repos.

## Governance

ADR-038/009 unchanged. No kernel, contract, or suite-manifest ID changes.
Dogfood harness guards live at `tools/dogfood/test_harness_guards.py`
(not the frozen suite).

## Known limits

Same as before: trainer labels are host-relative; no journal head anchor;
mutmut UNVERIFIED; the 18-mutant battery is the control.
