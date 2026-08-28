# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-29 (SLICE-074 closed)
**Active slice:** none

## Where we stopped
SLICE-074 closes the real SIGKILL orphan defect in non-confined `run` and
`suite freeze`. An external guardian owns the exact root and fresh PID
namespace, transfers verified PID-1 pidfds behind an exact start gate, preserves
raw exit/signal status, and cleans before admission. Nested Ranex delegates back
to that external guardian through a PID-namespace-authenticated broker, so it
gets a fresh sibling namespace without forbidden nested user namespaces.

Real governed verification reached 1,442 passed / 105 declared skips with
signed zero-exit evidence. After adversarial repair, the final freeze reached
1,441 passed / 109 declared skips and froze 1,550 IDs / 154 declarations with
`run_exit=0`. Kernel,
guardian, and nested-controller SIGKILL arms left no owned process or root.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-054

## Governance
Kernel-only initial release; no implementation slice is active.
Build order: milestone 4 → milestone 3 → milestone 2

## Known limits

- Simultaneous kernel+guardian SIGKILL and pre-identity guardian SIGKILL remain
  unverified; strict-local controller crash remains a separate boundary.
- Host `/tmp` stays writable. A hostile same-UID host peer can attack scratch or
  replace the pathname broker; client-side server authenticity is not claimed.
- Unqualified-host skips remain; qualified-host dynamic execution is supported.
- Hosted confinement requires user namespaces and delegated cgroup controllers.
- About 125 legacy test IDs remain unregistered; trace fd targets retain O_NONBLOCK on the operator descriptor after exit (disclosed).
- mutmut statistics remain unavailable for subprocess-heavy surfaces; default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- The approver remains an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
