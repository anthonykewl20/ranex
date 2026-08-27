# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-28 (SLICE-072 delivered)
**Active slice:** none

## Where we stopped
SLICE-072 delivered the ADR-035 dynamic runtime closure. Qualified hosts now
execute strict-local dynamic inputs; the captured qualified-host journey and
the full focused closure are complete. The approved-batch specification vectors,
Gate 10 pin, and prerequisite reconciliation are refreshed for the delivered
runtime.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next: harness-lane continuation per MAP and milestone order.

## Governance
Kernel-only initial release; no implementation slice is active.
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
