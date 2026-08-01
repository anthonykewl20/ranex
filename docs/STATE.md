# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** none — SLICE-002 closed, next one not yet opened

## Where we stopped

**SLICE-002 is done.** Evidence is signed. `run` refuses to write without a key,
admission verifies each record against the committed keyring, and a record that
does not verify never reaches `evaluate()` — forgery arrives as absence, and
absence blocks. 134 tests green. The target was committed red at `0b0512c2f` and
all five of its files are byte-identical since; `verdict.py` is unchanged, held
by a digest test.

**Signing is mandatory, and that is a wall on a fresh clone.** No
`governance/producers.yaml` exists here, so `run` and `gate evaluate` exit 2
until an operator runs `keygen` and commits the public key. Failing closed is
correct, and it is the first thing a newcomer hits.

## Next

1. **SLICE-003 — journal hardening.** `Journal.append` races: two writers read
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
- No CI or rulesets exist. `main` blocks force-push/deletion but requires no
  checks. Five required checks outlived the workflow that produced them and
  silently blocked every non-admin merge; protection must never outlast the job
  it names. Agents share owner credentials, so it is not yet a trust boundary.
- Delegation works: direct OpenRouter, one narrow prompt per call. `tencent/hy3`
  at effort `high` stalls on ~25KB prompts; effort is a % of `max_tokens`.
- Approver identity is still an unauthenticated string, so no-self-approval is a
  convention and not a control. Now the weakest link. Own slice.
- `subject_lane` is a hardcoded default reaching journal records.
- `.git` is 665M — `upstream-sync` and `archive/*` tags hold the old objects.
