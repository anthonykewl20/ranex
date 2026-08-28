# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-28 (SLICE-073 closed)
**Active slice:** none

## Where we stopped
SLICE-073 removed provider-specific delegation credentials and made the adapter
boundary opaque and host-neutral. Real pinned Ranex Git journeys, disposable
freeze, historical-host refusal, 10/10 fanout stress, policy/journal stress, and
the canonical 1,503-pass suite are green. The eight-writer stress also found and
closed a SQLite busy-timeout defect; the 4,000-row hash chain verifies.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-054

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
