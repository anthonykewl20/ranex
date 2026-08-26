# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-26 (SLICE-070 complete and published)
**Active slice:** none — SLICE-036 is ready but remains dependency-gated pending
its explicit public run-source-selector CCR

## Where we stopped
SLICE-070/#47 is complete, published, remotely verified, and archived.
Strict-local v2 now gives self-contained static workers held, stable
`/ranex/input`, `/ranex/toolchain`, `/ranex/output`, `/ranex/scratch`, and
no-exec `/ranex/subject` mounts without changing the explicit v1 session API.
The qualified-host v2 journey and delegated legacy v1 regressions are green.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-036
Publish the explicit SLICE-036 public `ranex run`
source-selector/materialisation CCR, then let the next spec owner claim #19 and
remove its dependency gate. The seam for the fixed
`/ranex/toolchain/bin/slice036-worker` deliberately remains outside #47.

## Governance
Kernel-only initial release; no open slice while #19 awaits its explicit CCR.
`dependency-gated` is distinct from `done` and does not consume the one-open slot.
Build order: milestone 4 → milestone 3 → milestone 2

## Known limits

- The strict-local controller remains same-UID trusted infrastructure; hosted
  confinement requires user namespaces and delegated cgroup controllers.
- Dynamic v2 runtime closure is unsupported/refused; #48 owns it and there is
  no host-root fallback.
- The full suite remains intentionally red at SLICE-036's four absent batch
  seams and its public-run source selector; suite-freeze also lacks committed
  dependency-derivation admission. These are not SLICE-070 acceptance failures.
- About 125 legacy test IDs remain unregistered; trace fd targets retain O_NONBLOCK on the operator descriptor after exit (disclosed).
- mutmut statistics remain unavailable for subprocess-heavy surfaces; default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- The approver remains an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
