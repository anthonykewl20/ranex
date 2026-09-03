# Two-arm OSS benchmark (VulcanBench) — ranex-governed vs bare

Compares, on REAL merged OSS pull-request tasks, an agent whose "done" is a
self-reported claim (bare arm) against the same agent whose "done" must be
signed evidence passing a ranex gate (governed arm). Grading in both arms
is VulcanBench's own deterministic hidden tests — ranex is never graded by
its own opinion, and ranex is NOT claimed to raise pass@1. The claims under
test are:

1. FALSE-CLAIM RATE — bare self-reports vs hidden-test reality can diverge;
   the governed arm's verified-pass must never diverge (a gate that verified
   a failing task would be a kernel bug worth an F-finding).
2. GOVERNANCE OVERHEAD — wall-clock and $ delta of wrapping verification in
   ranex (VulcanBench already tracks $/task and minutes/task).
3. EVIDENCE — every governed completion ships a signed evidence record and
   a tamper-evident journal chain; the bare arm ships a claim.

## Status — HONEST

- Adapter VALIDATED end-to-end on real task data at $0 (2026-09-03):
  - plumbing: vendored kernel + signed evidence + gate verdicts both
    directions on a real task repo (git-bound claims);
  - real task tests: py-txn-kvstore's own 9 hidden tests under governance —
    gold -> gate PASS, empty -> gate FAIL, journals verified;
  - bare ground truth: gold 9/9, empty 0/9.
- LIVE-FIRE PROVEN: `zai:glm-5.3` through the real VulcanBench harness on
  the GLM Coding Plan endpoint (`ZAI_BASE_URL=https://api.z.ai/api/coding/
  paas/v4`, key at ~/.secrets/GLM-API-KEY line 2): hello-world
  functional=1.0 total=0.9949 at $0.003 metered-equivalent.
- The plan bills USAGE WINDOWS (codes 1302/1308), not metered credits; the
  $ cap is metered-equivalent. An alternative plan path exists as the
  `zcode:<model>` harness mode (drives the ZCode CLI on the same plan) —
  deliberately NOT used for the two-arm study: it measures model+product,
  the raw `zai:` provider keeps both arms the same model.
- Integration lessons are recorded as F-003 (vendoring pattern, evidence
  gitignore, pinned toolchain prerequisite — now satisfied).

## Pipeline (when built)

1. TRIGGER — nightly loop calls `check_release.py`; a version advance since
   `state.json`'s `last_benched_version` arms the benchmark.
2. GOVERNED-REPO CONSTRUCTION — per task: copy `repo/` to scratch, commit
   governance files (producer keyring with a bench producer, gates.yaml
   binding the task's own `fail_to_pass`/`pass_to_pass` commands, suite
   manifest frozen from the hidden tests), keygen outside the repo.
3. ARMS — same model, same tasks:
   - bare: agent solves; harness grades (VulcanBench standard flow).
   - governed: the agent's verification step runs under
     `ranex run --producer bench --claim tests-executed -- <task's test
     command>`; completion counts only if `gate evaluate` returns PASS on
     the signed evidence. Network-off is preserved by provisioning wheels
     into the content-addressed store host-side and mounting it read-only.
4. REPORT — `results.json` (schema below) written ONLY from
   `runs/*/summary.json` artifacts; per-task digests recorded; site data
   regenerated; `state.json` updated to the benched version.

## The proof pile (append-only archive contract)

Every entry in `proofs/` is `ranex-oss-proof-entry-v1`. Two producers:

- the divergence experiment (agent runs, `kind: run`, with model/tokens/
  cost/self-report, and `kind: attack` demos: `deleted-tests`,
  `stale-proof`);
- `tools/dogfood/external_proof.py` (`kind: run` with `agentless: true`
  and an `external` identity block — released tag, external URL/commit/
  license, vendored-vs-tag tree digests; and `kind: attack`
  `stale-proof-external` with before/after gate outputs on the external
  repository). External entries carry no model; the site renders them in
  their own section, never in the agent matrix.

Files are never edited or deleted; every page number derives from the
archive. Re-publishing the same proof is idempotent per kernel commit.

## results.json schema (site contract)

    {
      "schema": "ranex-oss-bench-v1",
      "kernel_git_head": "<40hex>",
      "kernel_version": "X.Y.Z",
      "vulcan_suite": "v1",
      "model": "provider:model",
      "budget_cap_usd": <number>,
      "tasks": [
        {
          "task_id": "...",
          "bare":   {"claimed_pass": bool, "grader_pass": bool,
                     "cost_usd": n, "minutes": n},
          "governed": {"gate_pass": bool, "grader_pass": bool,
                       "cost_usd": n, "minutes": n,
                       "evidence_digest": "sha256:...",
                       "journal_verified": bool}
        }
      ],
      "summary": {
        "bare_false_claims": n, "governed_false_verifications": n,
        "overhead_median_ms": n, "tasks": n
      }
    }

The ranex.dev /dogfood section for this data renders ONLY when a real
results.json exists (AUTOFIX.md forbids placeholder sections).
`governed_false_verifications > 0` is a kernel bug, not a benchmark result —
file it as an F-finding.

## Budget rules

`--no-judges` always; `--max-cost` hard cap from state.json config; absent
key/cap/harness => record SKIPPED with reason. Never reuse stale results.
