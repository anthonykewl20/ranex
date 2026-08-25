# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-26 (SLICE-070 strict-local I/O prerequisite)
**Active slice:** `docs/slices/SLICE-070-stable-strict-local-io-namespace.md`

## Where we stopped
Milestone 4 remains closed with partial kernel delivery; harness, broker,
task-family real-provider proof, and production mutation fanout are withdrawn.
SLICE-036/#19 is not done: its frozen approved-batch command cannot truthfully
read committed inputs from strict-local v1's scratch cwd without hidden checkout
geometry. It is now `blocked` on SLICE-070/#47.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-070
SLICE-070 is the sole open slice. ADR-034 freezes an additive strict-local v2
ABI: exact descriptor-held input/toolchain are recursive read-only at
`/ranex/input` and `/ranex/toolchain`; exact bounded output/scratch are writable
at `/ranex/output` and `/ranex/scratch`; cwd is `/ranex/input`. Descriptors carry
sources only. The launcher creates fixed targets in a private root and uses
held-FD `open_tree`, `mount_setattr`, and `move_mount` with no legacy fallback.
Worker env stays `{LC_ALL,TZ}`; stdin/data FDs stay closed. Initial v2 admits
only genuinely self-contained static executables; dynamic runtime closure is
unsupported/refused and tracked separately in #48.
The frozen real journey uses existing public build/install/qualify/session
commands sequentially inside one delegated systemd unit. Self-contained static code
reads committed input, observes input write refusal, creates explicit output,
and is checked against ordinary-result bytes plus canonical collected hashes.
SLICE-036 C consumes no predecessor bytes, so no predecessor namespace is added.
Implementation waits for independent review, OCR, publication, and #47 ready.

## Governance
Kernel-only initial release; one open slice and one mutation writer. `blocked`
is distinct from `done` and does not consume the one-open slot.
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
