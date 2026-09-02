# ADR-046 — serializing the qualification cgroup-probe topology under the host-probe lock

**Status:** accepted
**Date:** 2026-09-02
**Decision-makers:** repo owner
**Issue:** #73 (parallel child qualification refuses E-C18-GATE in a freshly delegated scope)

*Panel record: two adversarial seats returned CHANGES-REQUIRED on the T0
package (partial-wrap red hole, session-race framing, false SIGKILL
recovery claims, dpkg/latency wording); every finding was addressed —
the drain-before-gate driver, the residual-risk rewording with #74, the
at-fork fd guard, the pids-delegation gate — and a fresh confirmation
seat returned ACCEPT.*

## Context and Problem Statement

Issue #73, observed during the #65 live-owner acceptance run: with
`--pool 2`, two child `qualify` provisions run concurrently in one freshly
delegated cgroup scope and one refuses
`E-C18-GATE: qualification verifier lacks the pids controller`.
`qualify`'s local host probe holds `_host_probe_lock()` while
`_real_cgroup_probe` drains every scope member into a transient leaf,
enables controllers, and restores (host_confinement.py:1925-2009). But
`_runtime_v3_verifier_isolation_probe` (:3221-3322) performs the same
drain/enable/restore dance with no lock, so a sibling's locked reads — or
the probe's own — can observe a transient leaf whose `cgroup.controllers`
is still empty, and refuse fail-closed against a healthy host.

## Decision Drivers

- ADR-044's delegated-scope lane must support the signed `maximum_pool: 2`.
- Fail-closed is correct only against real degradation, not self-inflicted
  interleaving.
- No new resident trusted infrastructure; same-UID systemd primitives only.
- Deterministic tests — no sleep-based flakes (issue #73 criterion 1).
- The v3 probe's existing teardown (release in `finally`) stays untouched.

## Prior art

Searched: GitHub code search 'cgroup subtree_control internal processes
flock', 'cgroups v2 enable controllers concurrently', 'dpkg database lock
flock', and pinned-source inspection of the vendored files below.

- https://github.com/opencontainers/cgroups/blob/v0.1.0/fs2/create.go
  grounds: `CreateCgroupPath` walks the path creating each level and
  enabling controllers parent-first, and treats an internal process as
  `domain invalid` — an error or a threaded-mode degradation, never a
  silent shared mutation. This is the create-before-enable ordering the
  probe keeps; the citation pins that ordering against real code.
  License: Apache-2.0 (opencontainers contributors).
  Weakness: assumes the caller owns the whole path; two peer writers get
  no serialization answer from it, and its degraded threaded mode would
  forfeit the domain controllers the batch children need.
  Vendored: `docs/adr/prior-art/ADR-046/opencontainers-cgroups-v0.1.0-fs2-create.go` blob:6be11c24739ace3e0ff46c0eabf01b94040d3b4a

- https://github.com/guillemj/dpkg/blob/1.23.7/lib/dpkg/dbmodify.c
  grounds: every dpkg database mutation runs under one cross-process
  flock (`modstatdb_lock`), acquired before the read-modify-write and
  released only after — peers queue rather than interleave. That is the
  exact serialization pattern `_host_probe_lock` already gives the local
  probe and this decision extends to the v3 probe.
  License: GPL-2.0-or-later (Ian Jackson, Wichert Akkerman, Guillem Jover).
  Weakness: it is a database-file lock (an fcntl-based advisory lock,
  not flock), not cgroup topology, and it fails fast (`FILE_LOCK_NOWAIT`)
  with a user-facing error where qualification peers must wait their
  turn; vendored as evidence only, not linked.
  Vendored: `docs/adr/prior-art/ADR-046/dpkg-1.23.7-lib-dpkg-dbmodify.c` blob:deac375bb1fafdfd7113047c3de255a2f1bb7e09

- Rejected: https://github.com/containers/crun — its cgroupfs path
  (`libcrun_cgroup_enter_finalize`) moves the container's own process and
  enables controllers on a subtree the runtime exclusively owns; it offers
  no answer for peer CLI processes sharing one delegated scope root, which
  is precisely the topology ADR-044 creates.
- Rejected: https://github.com/systemd/systemd — delegating all mutation
  to a resident single-writer manager (the D-Bus model) would add
  same-UID trusted infrastructure beyond the frozen systemd-run primitive
  ADR-044 already admits, for a concurrency problem a file lock solves.

## Considered Options

1. Acquire `_host_probe_lock()` inside
   `_runtime_v3_verifier_isolation_probe` — chosen.
2. Reorder `_real_cgroup_probe`'s drain/enable. Rejected: the kernel's
   no-internal-process rule fixes that order; leaves are created before
   controllers can be enabled.
3. Tolerate/retry transient empty controller reads. Rejected: masks a
   real interleaving and could admit a genuinely degraded host.
4. A single-writer broker process owning scope mutation. Rejected:
   new resident trusted infrastructure (see systemd above).

## Decision Outcome

In the context of issue #73's self-inflicted refusal, facing two probe
dances sharing one mutable scope, we chose to make the v3 verifier
isolation probe acquire the existing `_host_probe_lock()` for its whole
body — drain, enable, fork/verify, and teardown — so every cgroup-topology
mutation a qualification performs is serialized against every other.

- `src/ranex/cli/host_confinement.py`: the body of
  `_runtime_v3_verifier_isolation_probe` runs inside
  `with _host_probe_lock():` — reads included (the :3233 refusal fires
  from a read). The lock's directory fd gains an `os.register_at_fork`
  guard so forked children do not inherit the flock. No other behavior
  changes; report shape and refusal codes are untouched.
- The function is now non-reentrant (self-deadlock if called while this
  process holds the lock); its only caller is `qualify`'s report
  assembly, which holds none there (checklist carries the invariant).

### Consequences

- `--pool 2` in a freshly delegated scope serializes its two
  provisioning probes instead of refusing; pool 1 is unaffected.
- Every qualify-path cgroup mutation (local probe + v3 probe) is now
  under one per-user flock; a queued peer waits behind at most that
  peer's two probe dances.
- Residual risk, accepted and named: the session path still mutates
  topology unlocked and can race a qualification in the same scope
  (the #73 refusal class, either direction); the supported batch flow
  never overlaps them, and #74 owns the follow-up — never fixed by
  locking the shared helpers (self-deadlock; see Sad paths).
- The broker path (no local controllers) is unchanged: the v3 probe
  still runs locally and now queues behind any concurrent holder.

### Confirmation

`tests/e2e/test_delegated_probe_serialization.py::test_v3_verifier_probe_blocks_while_the_host_probe_lock_is_held`
is the deterministic red proof: the driver holds the lock *and* the
drained topology (every scope member in a fresh controller-less leaf),
so an unlocked probe — or a partial wrap that locks only the mutations
while reading controllers outside — completes or refuses while the lock
is held and fails red; with the fix the child blocks on the flock,
completes only after release, restores the caller's cgroup, and leaves
no `ranex-*` residue in the scope. The parallel-qualify arm pins the
user-visible symptom green (it is a regression pin, not the red proof).

## Improvements on the prior art

1. dpkg fails fast on a held lock; qualification peers block and queue,
   because a concurrent provisioning probe is expected, not an error.
2. opencontainers/cgroups degrades to threaded mode or errors on
   internal processes; the probe instead drains members into a leaf,
   enables domain controllers, and reverses both — under the lock,
   reads included.
3. dpkg locks one database file by path; `_host_probe_lock` flocks a
   verified, owner-checked, no-follow directory descriptor under
   `/run/user/<uid>`, refusing symlinked or re-owned lock directories.

## Architecture surface

- `src/ranex/cli/host_confinement.py` — `_runtime_v3_verifier_isolation_probe`
  wrapped in `_host_probe_lock()`; the lock's directory fd registered
  with an `os.register_at_fork` guard so forked children drop it.
- `tests/e2e/test_delegated_probe_serialization.py` — new: the frozen
  red/green serialization proof and the parallel-qualify regression arm.

## Scope and threat delta

Serialization only: no new trust root, no new primitive, no authority or
attestation change, no CLI surface change. STRIDE letters moved: none —
the lock narrows a denial-of-service window (self-refusal), widens
nothing; the probe's refusal vocabulary and fail-closed order are
unchanged. Explicit non-goal: session-path serialization (#74 records
the residual race and the call-site warning) and cross-batch locking
(single-operator journal discipline covers it today).

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | report bytes and refusal codes unchanged; no new surface |
| Compatibility | pool 1, broker path, and session path byte-identical |
| Consistency | same lock, same discipline, as the local host probe |
| Simplicity | one context manager around one existing function body |
| Reversibility | remove the `with` line; behavior returns exactly |
| Testability | deterministic lock-blocking proof, no sleep-based flake |

## Reversibility

Door: two-way

Deleting the `with _host_probe_lock():` wrapper and the at-fork guard
restores today's behavior exactly; no schema, report, manifest, or
journal shape records the lock's existence.

## Sad paths

- `/run/user/<uid>` absent, symlinked, or re-owned → the lock refuses
  `E-DELEGATION` before any topology change (existing behavior).
- A hung process holds the lock → peers block without timeout; killing
  the holder releases it because forked children no longer inherit the
  lock fd (the at-fork guard) — the paused children linger until
  reaped, but cannot wedge the lock.
- The probe is called while this process already holds the lock →
  self-deadlock; prevented by the single caller invariant (checklist).
- Locking the shared helpers `_create_worker_cgroup` /
  `_release_controller_leaf` instead of this call site → self-deadlock
  with the v3 probe; session serialization goes at session call sites
  (#74).
- The scope lacks `pids` → the probe still refuses `E-C18-GATE`, now
  after queueing for the lock — fail-closed order preserved.
- Fork, pipe, or cgroup write fails mid-dance → the existing `finally`
  releases the controller leaf; the lock then releases with it.
- SIGKILL between drain and restore → members stay in the leaf (the
  next probe refuses `E-FACT missing controllers` — pre-existing
  hazard) but the lock itself frees with the killed process.
- A forked verifier child is never reaped → the at-fork guard keeps the
  lock releasable; the orphan itself remains until killed.
- Host without a creatable delegated user scope, or one whose fresh
  scopes lack `pids` → the new e2e module skips with a live-probe
  reason, never reports PASS.
- Parallel qualifies on a no-delegation host → broker path, isolated
  transient services; the local v3 probe queues briefly, no refusal.
- A second v3-probe caller is added inside a held-lock section → the
  checklist line catches it in review; no runtime guard by design.

## Test strategy

- `tests/e2e/test_delegated_probe_serialization.py` (new, frozen red
  first): the lock-blocking proof (forked child must not complete the
  probe while the parent holds `_host_probe_lock`; after release it
  completes, restores the caller's cgroup, leaves no `ranex-*` leaves)
  and the parallel-qualify arm (two `host_confinement qualify` in one
  fresh delegated scope both exit 0, `qualified=true`).
- `tests/e2e/test_specification_batch_qualification.py` — the existing
  journey proves single-pool qualification is unchanged by the fix.
- `tests/contract/test_docs_discipline.py` — governs this ADR's shape,
  citations, licences, weaknesses, and vendored blob digests.
- Issue #73 acceptance (not a suite test): the real owner-authority
  batch re-qualified `--pool 2` inside a delegated scope, evidence
  attached to the issue.

## Code review checklist

- [ ] The diff wraps the whole `_runtime_v3_verifier_isolation_probe`
      body — reads included — in `_host_probe_lock()`, and adds only the
      at-fork fd guard beyond it.
- [ ] No new caller of `_runtime_v3_verifier_isolation_probe` sits
      inside a held-lock section, and nothing locks the shared
      `_create_worker_cgroup`/`_release_controller_leaf` helpers
      (self-deadlock; #74).
- [ ] The red commit precedes the fix commit; the frozen test file is
      byte-identical between them.
- [ ] Vendored blob digests recomputed on the review commit; NOTICE
      names both files with origin tag and licence.
- [ ] pool=2 acceptance transcript on #73 shows both concurrent
      provisions green in one delegated scope.

## More Information

- Issue #73 — the blocker and its acceptance criteria; issue #65 — the
  acceptance run that exposed it; ADR-044 — the delegated-scope lane
  and the same-UID primitive stance this preserves.
- `docs/adr/prior-art/ADR-046/NOTICE.md` — provenance and licences.
- `src/ranex/cli/host_confinement.py` (`_host_probe_lock`,
  `_real_cgroup_probe`, `_runtime_v3_verifier_isolation_probe`,
  `qualify`).
