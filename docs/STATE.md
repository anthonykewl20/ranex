# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-14 (late session)
**Active slice:** none.

## Where we stopped

SLICE-045 (#31) closed on the repository side and pushed (ef473d1be): the
2026-08-10 retrofit (56aa110e6) had already backfilled ADR-001/002 with
pinned citations, License/Weakness, vendored bytes and NOTICE; that commit
retires the two lapsed grandfather rows so the discipline tables reflect
compliant text. All #31 done criteria verified: 5/5 Vendored blob hashes
match git ls-files, no branch citations, NOTICE complete, >=2 Rejected per
ADR, full frozen suite 1015 passed / 7 skipped with the change present.
GitHub closure of #31 with this proof is still pending (no gh access from
the agent session).

A concurrent writer is active in this tree: an in-flight CI-hardening
change (weekly osv-scan job, contract-test enforcement, cryptography <51
re-lock; .github/workflows/ci.yml, pyproject.toml,
tests/contract/test_ci_workflow.py, uv.lock) — uncommitted, untouched by
this session, unreviewed here.

SLICE-029 (#12) remains blocked on its stated prerequisites: ADR-006 is
still `proposed`, RISK-06 still open (MAP 11.5), ADR-017 still
`proposed`; #10/#21/#22 are closed but nothing accepted ADR-006 — the
cmd_run confinement binding moved to SLICE-018, whose frozen scope
excluded acceptance. The owner must decide the acceptance path (or amend
the prerequisites) before SLICE-029 opens.

## Next

Owner: post #31 closure proof (SHA ef473d1be, suite 1015/7) and the drafted
#32 reply from this session's report; decide the SLICE-029 prerequisite
path; the concurrent CI-hardening writer finishes or is reviewed on its own.

## Known limits

- Frozen gate-1/3 real-session tests stay host-gated expected-skips without a
  directly-writable cgroup root (delegated-unit evidence on issue #21; gate-3
  passes for real under delegation).
- The readiness phase is unbounded if the controller itself is suspended
  (availability only, not confinement).
- Gated loader/libc Landlock rules hardcode Debian multiarch paths (fails closed
  elsewhere).
- The cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
