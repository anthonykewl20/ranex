# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-14
**Active slice:** none.

## Where we stopped

SLICE-018 closed and shipped — the confinement-session lifecycle: cgroup-v2
controller/worker leaves with exact readbacks, bwrap plus a stdio-gated launcher
namespaces, NNP→Landlock→seccomp, cumulative enforcement with exhaustion-first
refusals, kill/drain/populated-0 teardown, bounded `openat2` collection, and a
validated unsigned result. Delegated-unit runs on this host verified an honest
session, output-writing session, path-alias refusal, and real OOM kill refusing
E-C18-LIMIT; the full suite passed 1012 with 7 declared host-gated skips.

## Next

Kernel P0 sequence: SLICE-029..044 per `docs/MAP.md` and the open issues.
Opening the next slice is an owner/governance selection.

## Known limits

- Frozen gate-1/3 real-session tests remain host-gated expected-skips without a
  directly writable cgroup root; delegated-unit evidence attached to issue #21
  proves real sessions, and gate-3 passes for real inside a delegated unit.
- The runtime profile's mounts grammar under-claims the host read-only binds
  (`/usr`, `/bin`, `/lib`, `/lib64`) the implementation needs; fold it into the
  grammar when tests next unfreeze.
- The cgroup-observer `OSError(19)` flake under load remains open.
- Mutmut advisory status for this slice: not yet run.
