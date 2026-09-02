# Self-fix protocol for unattended runs

Unattended scheduled runs (02:00, 06:00, 10:00) may fix what they find, under this protocol. The 13:30 run is read-only (digest before the owner returns). It follows the
repo's standing owner rules (AGENTS.md): one issue at a time, green suite,
one comment, fast-forward push, stop after 3 failed attempts.

## When to fix, when to stop

FIX (autonomously) when ALL hold:
- the finding is a deterministic failure, baseline drift, or scenario bug
  with a reproducing case;
- root cause is in `src/ranex/**` or `tools/dogfood/**` and understood
  (named file:line, not a guess);
- the fix is minimal and `uv run --frozen pytest -q` is GREEN on the final
  commit (always `--frozen`);
- fixing it does not require changing the frozen suite manifest's test-ID
  set. (If a fix genuinely needs new/changed test IDs, STOP: re-freezing the
  suite golden is a deliberate owner act — diagnose and leave it.)

DO NOT TOUCH while unattended (diagnose only, leave for the owner):
- `src/ranex/foundation/signing.py`, `verdict_signing.py`, `approval.py`,
  `domain/admission.py`, `native/**` (launcher.c), `provisioning/pins.py`,
  `derivation.py`, `store.py` — the trust chain and confinement surface.
  A wrong unattended "fix" there is worse than a red run.
- `governance/**` (committed trust roots), `docs/adr/**`.
- Never "fix" by weakening a scenario assertion to match broken kernel
  behavior, and never edit `baselines.json`, `FINDINGS.md`, or ledger files
  to make a finding disappear.

## The fix cycle (per issue, max 3 issues per run, 3 attempts per issue)

1. Diagnose from source + the failing scenario's error. Write the root cause
   down before editing anything.
2. Apply the minimal fix. Run `uv run --frozen pytest -q` — must be green.
3. Re-run `uv run --frozen python tools/dogfood/dogfood.py iterate`:
   the pinning scenario must now drift (proof the kernel changed) or pass.
   Review that drift matches the intended fix — then deliberately re-record
   with `dogfood.py baseline`, and close the entry in `FINDINGS.md`
   (anchor + how closed).
4. Commit message names the finding id (e.g. "fix: F-001 — journal verify
   returns False on non-JSON rows"). Push FAST-FORWARD ONLY, after
   confirming `gh auth status` active account is `anthonykewl20` (switch if
   not), and verify the remote tip is your commit. Leave the tree clean.
5. After 3 failed attempts on one issue: stop, leave ONE comment on the
   finding in `FINDINGS.md` naming the blocker and what was tried, move on
   (or end the run if budget exhausted).

## Always, at the end of each run

- Run `dogfood.py report` so the public page reflects the post-fix state.
- Append the iteration ledger record (iterate does this).
- Run summary: findings opened/fixed/blocked, commits pushed (SHAs),
  anything UNVERIFIED named as UNVERIFIED. Never report PASS for anything
  not actually run.
- If push is rejected (non-fast-forward — e.g. another agent pushed first),
  STOP pushing: report the divergence and finish the run locally.

## Protected-branch fallback

If the working tree was dirty at loop start (someone left work uncommitted),
do not fix anything: run iterate/report only and say so in the summary.
