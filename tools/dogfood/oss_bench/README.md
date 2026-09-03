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

- DESIGNED, adapter NOT YET BUILT. Nothing here has been run; there are no
  results yet, and none may be published until real runs exist.
- Built and working today: `check_release.py` (release-trigger detection
  consumed by the nightly loop) and the site data schema below.
- To build the adapter: clone https://github.com/morganlinton/VulcanBench,
  `make setup && make sandbox-image`, then validate the pipeline at $0 with
  their `mock` provider on the hello task + 2-3 real `tasks/v1` tasks.

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
