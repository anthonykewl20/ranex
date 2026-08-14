# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-14
**Active slice:** none.

## Where we stopped

SLICE-018 shipped and host-verified — the confinement-session lifecycle
(cgroup-v2 controller/worker leaves with exact readbacks, pinned bwrap
namespaces, gated launcher enforcing NNP → Landlock → seccomp before exec,
cumulative cpu/memory/pids/wall/output enforcement, kill → drain → populated-0
teardown, bounded openat2 collection, validated unsigned
`ranex-confinement-result-v1`). After closure, a delegated-systemd-unit battery
on this host caught and fixed (0caa1090f) a Landlock ABI equality-vs-minimum bug
that refused every real session on ABI≠6 hosts, plus symlinked-executable
support, an initially-empty subtree_control start, and a pre-exec readiness-ack
so membership/namespace/enforcement readbacks happen while the worker exists.
Real sessions are now VERIFIED on this host (honest /bin/true, output-writing,
path-alias refusal, static-hog OOM refusing E-C18-LIMIT with events); full suite
1015 passed / 7 declared skips at the pushed commit.

## Next

SLICE-029 (ADR-017 written, prior art vendored) pending owner selection;
SLICE-045 prior-art backfill also open; harness lane progresses in its own repo.

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
