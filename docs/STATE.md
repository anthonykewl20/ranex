# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-26 (trace-schema CCR #50 complete)
**Active slice:** none

## Where we stopped
SLICE-071/#49 completes the retained approved-batch qualification task from
superseded #19. The public v2 source selectors, separate `task batch qualify`
surface, protected A/B/C admission, sequential joined execution, atomic
qualification journal append, signed non-publishable outcome, and batch-aware
judge/merge refusal are implemented. Host-probe mutations serialize across
processes without weakening the existing strict-local v1/v2 boundaries.
Follow-up #50 advances the trace schema to v2 and registers and emits the
`cli.task.batch.qualify.start/end` boundary for that nested command.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: none selected. Dynamic v2 runtime closure remains deferred to #48.

## Governance
Kernel-only initial release; no open slice after SLICE-071.
Build order: milestone 4 → milestone 3 → milestone 2

## Known limits

- The strict-local controller remains same-UID trusted infrastructure; hosted
  confinement requires user namespaces and delegated cgroup controllers.
- Dynamic v2 runtime closure is unsupported/refused; #48 owns it and there is
  no host-root fallback.
- About 125 legacy test IDs remain unregistered; trace fd targets retain O_NONBLOCK on the operator descriptor after exit (disclosed).
- mutmut statistics remain unavailable for subprocess-heavy surfaces; default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- The approver remains an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
