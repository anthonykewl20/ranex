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
  Report rewrites tracked artifacts (`tools/dogfood/site/*`, the README
  dogfood-status block): commit them (`tools: dogfood artifacts —
  iteration N`) and push, or the NEXT run starts on a dirty tree and
  self-disables. Never commit unrelated dirty files with them.
- Append the iteration ledger record (iterate does this).
- Run summary: findings opened/fixed/blocked, commits pushed (SHAs),
  anything UNVERIFIED named as UNVERIFIED. Never report PASS for anything
  not actually run.
- If push is rejected (non-fast-forward — e.g. another agent pushed first),
  STOP pushing: report the divergence and finish the run locally.

## Automated versioning (after successful fixes)

A fix that lands through the cycle above is a release-worthy change. The
loop cuts it following the repo's OWN release convention (see the v0.1.0
commit 02b637815 for the reference shape):

- Bump `pyproject.toml` version: PATCH for fixes (`0.1.0 -> 0.1.1`), MINOR
  for added capability (`0.1.x -> 0.2.0`). Never jump MAJOR unattended.
- Re-derive the lock surgically and epoch-preserving:
  `uv lock --exclude-newer <governance/deps.yaml exclude_newer>` — the only
  acceptable delta is the ranex version entry.
- Update `docs/STATE.md` (rewrite, <=50 lines) to record the release.
- Commit format: `release: vX.Y.Z — close the #N gate` when a release-gate
  issue is open, else `release: vX.Y.Z` with a one-line summary of what the
  release fixes/adds. Push fast-forward; verify remote tip.
- A release is only cut when the final commit has `uv run --frozen pytest
  -q` green AND no frozen-suite test-ID changes are pending owner action.
  If either fails, ship the fix without a version bump and note why.

## Release-triggered OSS benchmark (two-arm VulcanBench)

After any release (and only then), the loop checks
`tools/dogfood/oss_bench/state.json` (`last_benched_version`) against the
current pyproject version. On advance, and ONLY if the provider API key is
present in the environment and a budget cap is configured:

- run the two-arm study (bare vs ranex-governed) per
  `tools/dogfood/oss_bench/README.md`, with `--no-judges` and `--max-cost`
  hard-enforced; never exceed the configured cap;
- write results ONLY from real run artifacts (runs/*/summary.json); no
  number is ever typed, interpolated, or estimated;
- commit results + refreshed site data, push, and report.

If the key is absent, the cap is unset, or the harness is not installed,
record SKIPPED with the reason — never fabricate or reuse stale results as
new. The ranex.dev section for these results renders only when real data
exists; an empty placeholder section is a bug.

## Nightly real-world proof accumulation (the proof pile)

The public proof page renders from the append-only archive
`tools/dogfood/oss_bench/proofs/` — one dated JSON per proof, never edited,
never deleted. Every unattended run grows it:

- Run the nightly COMPARISON BATCH: up to `nightly_batch` (default 3) fresh
  real agent runs per night — one from each pool in `state.json`'s
  `task_rotation` (control / medium / veryhard), all at `--effort minimal`,
  together bounded by `nightly_proof_budget_usd` (default $1.50
  metered-equivalent). Multiple runs per night is the point: the page's
  graphs (verdict matrix, tokens, growth line) fill with real points every
  cycle, and iteration-over-iteration comparison becomes visible. Process
  the whole batch through one `run_divergence.py` invocation and append
  with `proofs.py append <divergence.json> <date> <git head>`.
- After a RELEASE, re-run the two fault demonstrations (deleted-tests,
  stale-proof) against the new kernel and append them — a new kernel
  re-catching every attack is a new proof, and the archive dedupes per
  (attack, kernel_head), never per night.
- Regenerate the page (`oss_report_site.py`), commit proofs + page +
  ledger as `tools: proof pile — <date>`, push fast-forward.
- Skip rules: no key, no budget, harness missing, or plan-window errors
  (1302/1308) → record SKIPPED with the reason in the run summary; never
  pad the pile with fabricated or rerun-numbered entries. A thin night is
  honest; a fake proof is the one unforgivable output here.

## Protected-branch fallback

If the working tree was dirty at loop start (someone left work uncommitted),
do not fix anything: run iterate/report only and say so in the summary.
