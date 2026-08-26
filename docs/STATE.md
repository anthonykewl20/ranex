# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-26 (SLICE-072 specification freeze)
**Active slice:** docs/slices/SLICE-072-digest-bound-dynamic-runtime-closure.md (#48)

## Where we stopped
The owner approved ADR-035 Option B: one complete digest-bound dynamic runtime
tree supporting a top-level interpreter, transitive libraries, native
extensions, and runtime data. The existing static v2 profile stays immutable;
SLICE-072 seals every exact runtime file, assembles fixed `/ranex/runtime`, and
compares pyelftools with a confined held-loader probe before releasing the same
private snapshot. The claim is native dependency closure, not interpreted/JIT
code policy. ADR, slice, and RED tests are the active specification checkpoint.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next: implement SLICE-072 only after its RED specification commit is published.

## Governance
Kernel-only initial release; SLICE-072 is the sole open slice.
Build order: milestone 4 → milestone 3 → milestone 2

## Known limits

- The strict-local controller remains same-UID trusted infrastructure; hosted
  confinement requires user namespaces and delegated cgroup controllers.
- Dynamic execution remains unsupported until SLICE-072 turns its frozen tests
  green; static v2 continues to refuse and there is no host-root fallback.
- About 125 legacy test IDs remain unregistered; trace fd targets retain O_NONBLOCK on the operator descriptor after exit (disclosed).
- mutmut statistics remain unavailable for subprocess-heavy surfaces; default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- The approver remains an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
