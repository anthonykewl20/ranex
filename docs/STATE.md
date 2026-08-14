# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-14
**Active slice:** none.

## Where we stopped

SLICE-018 is closed and shipped: the confinement-session lifecycle now ENFORCES
NNP → strict full-mask Landlock (ruleset+add+restrict) → default-deny seccomp
→ `execveat` behind a closed `--ranex-worker-exec` path. A real
capability-gated session owns controller/worker cgroup-v2 lifecycle, enrollment
readback before gate release, a readiness witness, readback-bound honest facts,
kill → drain → remove, and unsigned `ranex-confinement-result-v1`. The launcher
uses an `openat2` resolve-beneath collector, environment allowlist `{LC_ALL,TZ}`
with inherited-FD closure, and enters six namespaces: user, mount, pid, ipc,
net, and cgroup.

## Next

Next kernel slice: SLICE-029 — A/B/C contract schemas; ADR-017 is written with
prior-art vendored.

## Known limits

- Integrated real-cgroup session, cgroup attack gates, and device-node attack
  are HOST-UNVERIFIED on this machine (delegated cgroup-v2 / `CAP_MKNOD`
  required; skip-declared).
- The unprivileged-userns gap in governed contexts is skip-declared.
- `mutmut` does not complete on this host (SLICE-017 copy-repo environment
  crash); advisory/non-blocking.
- The gate8 concurrent-session collision is FIXED (pid-matched rendezvous and
  unique blocker names; 4-way concurrent proof).
- The cgroup-observer gate5 flake class remains possible under extreme load.
- ADR-006 remains proposed and RISK-06 remains open. SLICE-019 retains the
  exclusive right to close them; SLICE-018 did not.
