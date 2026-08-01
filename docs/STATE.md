# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** none — SLICE-001 closed, next one not yet opened

## Where we stopped

**SLICE-001 is done.** `ranex run` executes a command, observes it, and emits
evidence that `gate evaluate` accepts. 78 tests green. The target was committed
red at `b495e3635` before any implementation existed and is byte-identical since
(file digest `5e0dc922d2dd06c5`), so red-then-green is checkable in this history.

The loop closes on this repo: `run` records `tests-executed` bound to the live
tree digest, and the gate reads it. It never reaches PASS: nothing produces
`contracts-validated`, and once the tree moves past the recorded digest
`tests-executed` fails first on subject binding. Both are the design working.

**`main` is now the kernel tree**, replacing a disjoint 446-file architecture
tree that shared no ancestor with it. Six retired branches deleted, tips kept as
`archive/*` tags. `bootstrap/pre-upstream` duplicates `main`; retire it.

## Next

1. **SLICE-002 — evidence authenticity.** Records are unsigned; a PASS is
   forgeable with a text editor. Blocked on: signing scheme and key custody.
2. **SLICE-003 — journal hardening.** `Journal.append` races: two writers read
   the same `prev_link` and fork the chain. Needs `BEGIN IMMEDIATE` and a
   `journal verify` subcommand — `verify()` exists and is never called. Harvest
   the SIGKILL crash and persisted-replay tests from `feature/kernel-tracer`
   (`acf155aee`; do not merge — see `git log --grep=kernel-tracer`).

## Known debts

- **`run` false claims still open** — `assume-unchanged`/`skip-worktree` hide
  changes from `git status`; ignored files can influence a command while being
  in no tree. Four others fixed in `10eb09586`.
- **`run` robustness** — evidence write is not atomic, no command timeout,
  concurrent runs can lose an update.
- `contracts-validated` is required by `gates.yaml` with no producer. Write one
  or amend the gate; do not fake the claim.
- `test_gate_catalog_loader.py` is misnamed; it tests `slice_gate_loader`.
- No CI exists. `main` blocks force-push and deletion; its 5 required checks
  named workflows that never existed and were removed. Add real ones.
- Delegation works: direct OpenRouter, one narrow prompt per call. `tencent/hy3`
  at effort `high` stalls on ~25KB prompts; effort is a % of `max_tokens`.
- `subject_lane` is a hardcoded default reaching journal records.
- `.git` is 665M — `upstream-sync` and `archive/*` tags hold the old objects.
