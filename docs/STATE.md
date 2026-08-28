# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-28 (SLICE-074 opened)
**Active slice:** `docs/slices/SLICE-074-kill-safe-command-ownership.md`

## Where we stopped
A disposable current-main clone ran the real committed landing command after
real key generation, producer registration, and approval of all 26 locked
wheels. SIGKILL of the kernel left uv, pytest, nested Ranex, strace, GCC, and
cc1 alive under PID 1 with no evidence and a stale subject root. Issue #53
contains the process-tree proof. The pre-change canonical suite is green at
1,503 passed / 29 skipped, so existing tests do not cover this failure.

## Next
Freeze the real failure as RED, implement ADR-037's external guardian and
PID-namespace ownership, then repeat the destructive real journey.
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-054

## Governance
Kernel-only initial release; one P0 implementation slice is active.
ADR-037 is accepted after independent operability and security review.
Build order: milestone 4 → milestone 3 → milestone 2

## Known limits

- Unqualified-host skips remain; qualified-host dynamic execution is supported.
- The strict-local controller remains same-UID trusted infrastructure; hosted
  confinement requires user namespaces and delegated cgroup controllers.
- About 125 legacy test IDs remain unregistered; trace fd targets retain O_NONBLOCK on the operator descriptor after exit (disclosed).
- mutmut statistics remain unavailable for subprocess-heavy surfaces; default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- The approver remains an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
