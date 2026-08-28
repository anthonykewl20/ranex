# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-28 (SLICE-073 implementation verification)
**Active slice:** `docs/slices/SLICE-073-provider-neutral-real-world-e2e.md`

## Where we stopped
The provider-specific delegation credential was removed. Unit, integration,
security, and a real pinned Ranex red/green adapter journey are green. Historical
batch qualification now proves exact build-input refusal on foreign hosts, and
suite freeze provisions disposable dependency state. Canonical freeze/full-suite
verification remains before close.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-054
SLICE-073 next action: suite-manifest ceremony, canonical e2e/stress rerun,
docs close, issue proof, commit, and push.

## Governance
Kernel-only initial release; SLICE-073 is the sole active implementation slice.
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
