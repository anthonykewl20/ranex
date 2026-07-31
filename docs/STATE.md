# State

<!-- Rewrite this file. Do not append to it. Keep it under 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — closing the evidence loop
**Active slice:** `docs/slices/SLICE-001-evidence-production.md` (not started)

## Where we stopped

Clean slate landed. Removed `hermes-agent/` (212M), `HERMES-STRIP-LIST.md`, the
`upstream` remote, and the unwired gate model (`gate_catalog_loader.py`,
`policy/api/`, `policy/domain/`, `foundation/identity.py`, `assurance/`).
`src/` went 1096 → 748 lines with all 41 tests still passing, which confirmed the
removed code was dead. License is now MIT © 2026 Anthony Garces.

What exists and works: a pure `evaluate()` verdict function, subject-bound
evidence, a hash-chained append-only journal, path confinement, and a
`gate evaluate` CLI.

## Next

1. **SLICE-001 — evidence production.** `ranex run` executes a command and emits
   an evidence record. Nothing produces evidence today; the loop is open.
2. **SLICE-002 — evidence authenticity.** Sign records, verify at evaluate time.
   Today `governance/evidence.json` is hand-editable, so a pass can be forged
   with a text editor.
3. **SLICE-003 — journal hardening.** `BEGIN IMMEDIATE` in `Journal.append` (it
   races under concurrent writers) and a `journal verify` subcommand, since
   `verify()` exists but is never called.

## Known debts

- `governance/evidence.json` is stale: it cites
  `scripts/architecture/validate_contracts.py`, which is not in the repo, and is
  bound to a tree digest that no longer exists. `gate evaluate` correctly FAILs.
  SLICE-001 replaces it.
- `tests/contract/test_gate_catalog_loader.py` is misnamed — it tests
  `slice_gate_loader`. Rename when next touched.
- `.git` is 665M. `upstream-sync` holds 18,256 commits of Hermes history.
  Reclaimable via `git branch -D upstream-sync phase/1-adopt-upstream develop &&
  git gc --prune=now`. Deferred — history decision, not cleanup.
- `subject_lane` is a hardcoded default string that reaches the journal record.
