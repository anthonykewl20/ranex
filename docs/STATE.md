# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** none — SLICE-002 closed, next one not yet opened

## Where we stopped

**SLICE-002 is done, on the second attempt.** Closed at `7f6cd3779`, reopened
when audits found 12 defects and two ticked criteria that were false; fixing
those surfaced 5 more. 17 across four audits, 156 green. The first close was
honest about process and wrong about facts: the tests were narrower than reality.

**One blocker is mitigated, not closed.** The observed command no longer inherits
`$RANEX_SIGNING_KEY`, but a same-uid child reads `/proc/$PPID/environ` and the
key file regardless. While the signer runs as the user it watches, a worker can
sign its own verdict. Architecture, not a patch — and the next thing to fix.

**Fresh clone hits a wall, correctly.** No `governance/producers.yaml` here, so
`run` and `gate evaluate` exit 2 until an operator runs `keygen` and commits the
public key.

## Next

1. **SLICE-003 — journal hardening.** `Journal.append` races: two writers read
   the same `prev_link` and fork the chain. Needs `BEGIN IMMEDIATE` and a
   `journal verify` subcommand — `verify()` exists and is never called. Harvest
   the SIGKILL crash and persisted-replay tests from `feature/kernel-tracer`
   (`acf155aee`; do not merge — see `git log --grep=kernel-tracer`).

## Known debts

- **`run` false claims** — `skip-worktree` and edit-then-revert are closed in
  `60b7e1ec1`; ignored files can still influence a command while being in no tree.
- **`run` robustness** — evidence write is not atomic, no command timeout,
  concurrent runs can lose an update.
- `contracts-validated` is required by `gates.yaml` with no producer. Write one
  or amend the gate; do not fake the claim.
- `test_gate_catalog_loader.py` is misnamed; it tests `slice_gate_loader`.
- No CI. `main` blocks force-push/deletion but requires no checks — five stale
  ones outlived their workflow and blocked every non-admin merge. Agents share
  owner credentials, so it is not yet a trust boundary.
- Delegation works: direct OpenRouter, one narrow prompt per call. `tencent/hy3`
  at effort `high` stalls on ~25KB prompts; effort is a % of `max_tokens`.
- Approver identity is still an unauthenticated string, so no-self-approval is a
  convention and not a control. Now the weakest link. Own slice.
- `subject_lane` is a hardcoded default reaching journal records.
- `.git` is 665M — `upstream-sync` and `archive/*` tags hold the old objects.
