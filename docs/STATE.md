# State

<!-- Rewrite this file. Do not append to it. Keep it under 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** none — SLICE-001 closed, next one not yet opened

## Where we stopped

**SLICE-001 is done.** `ranex run` executes a command, observes it, and emits
evidence that `gate evaluate` accepts. 65 tests green. The target was committed
red at `b495e3635` before any implementation existed and is byte-identical since
(`5e0dc922d2dd06c5`), so red-then-green is checkable in this history rather than
asserted.

The loop closes end to end on this repo: `run` records `tests-executed` bound to
the live tree digest, and the gate reads it. The gate still FAILs — on
`contracts-validated` alone, because nothing can produce that claim. That is
absence-blocks working correctly, not a regression.

Earlier: clean slate (Hermes and the dead gate model removed, 1096 → 748 lines),
a docs cap and README↔STATE sync enforced by tests, and a public README.

## Next

1. **SLICE-002 — evidence authenticity.** Records are unsigned; a PASS is
   forgeable with a text editor. Subject binding stops stale evidence, nothing
   stops fabricated evidence. Needs a decision on signing scheme and key custody.
2. **SLICE-003 — journal hardening.** `Journal.append` races: two writers read
   the same `prev_link` and fork the chain. Needs `BEGIN IMMEDIATE`, plus a
   `journal verify` subcommand — `verify()` exists and is never called.
3. **SLICE-004 — a reliable delegation channel.** Every later slice depends on
   dispatching work to a worker, and today none is proven.

## Known debts

- `contracts-validated` is required by `governance/gates.yaml` but has no
  producer — its script left with the clean slate. Write one or amend the gate;
  do not fake the claim.
- `tests/contract/test_gate_catalog_loader.py` is misnamed; it tests
  `slice_gate_loader`. Rename when next touched.
- Branch protection requires 5 status checks and there is no `.github/workflows`
  to satisfy any of them.
- opencode delegation is unreliable; codex works interactively but its
  non-interactive invocation was never made to run shell commands. Evidence:
  `git log --grep=opencode-delegation`.
- `subject_lane` is a hardcoded default that reaches journal records.
- `.git` is 665M — `upstream-sync` holds 18,256 commits of Hermes history.
