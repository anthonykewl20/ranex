# State

<!-- Rewrite this file. Do not append to it. Keep it under 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** none — SLICE-001 closed, next one not yet opened

## Where we stopped

**SLICE-001 is done.** `ranex run` executes a command, observes it, and emits
evidence that `gate evaluate` accepts. 78 tests green. The target was committed
red at `b495e3635` before any implementation existed and is byte-identical since
(file digest `5e0dc922d2dd06c5`), so red-then-green is checkable in this history
rather than asserted.

The loop closes end to end on this repo: `run` records `tests-executed` bound to
the live tree digest, and the gate reads it. It never reaches PASS: nothing
produces `contracts-validated`, and once the tree moves past the recorded digest
`tests-executed` fails first on subject binding. Both are the design working.

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

- **`run` false claims still open** — `assume-unchanged`/`skip-worktree` hide
  changes from `git status` itself; ignored files can influence a command while
  being in no tree. Four others fixed in `10eb09586`.
- **`run` robustness** — evidence write is not atomic, no command timeout,
  concurrent runs can lose an update.
- `contracts-validated` is required by `gates.yaml` with no producer. Write one
  or amend the gate; do not fake the claim.
- `test_gate_catalog_loader.py` is misnamed; it tests `slice_gate_loader`.
- Branch protection requires 5 checks; no `.github/workflows` exists.
- Delegation: only a direct OpenRouter completion works; that spike was never
  committed. opencode non-interactive never ran. `git log --grep=opencode-delegation`.
- `subject_lane` is a hardcoded default reaching journal records.
- `.git` is 665M — `upstream-sync` holds 18,256 Hermes commits.
