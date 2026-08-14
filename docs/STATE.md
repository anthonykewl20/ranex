# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-14
**Active slice:** none.

## Where we stopped

SLICE-018 shipped (c31baab32) and was hardened (0caa1090f): the
confinement-session lifecycle ENFORCES NNP → strict full-mask Landlock
(ruleset+add+restrict) → default-deny seccomp → `execveat` behind a closed
`--ranex-worker-exec` path. A capability-gated session owns controller/worker
cgroup-v2 lifecycle, enrollment readback before gate release, a readiness
witness, readback-bound honest facts, kill → drain → remove, and unsigned
`ranex-confinement-result-v1`. The launcher uses an `openat2` resolve-beneath
collector, environment allowlist `{LC_ALL,TZ}` with inherited-FD closure, and
enters six namespaces: user, mount, pid, ipc, net, and cgroup.

The delegated-unit battery verified on this host: an honest `/bin/true`
session with six distinct namespace readbacks; an output-writing session;
path-alias refusal; and static-hog OOM refusing E-C18-LIMIT with observed
events. Full suite: 1015 passed / 0 failed + 7 declared skips at 0caa1090f.

## Next

Next kernel slice: SLICE-029 — A/B/C contract schemas; ADR-017 is written with
prior-art vendored.

## Known limits

- The readiness phase is unbounded if the controller itself is suspended
  (availability, not confinement).
- Loader/libc Landlock rules hardcode Debian multiarch paths and fail closed on
  other distributions.
- The device-node attack still needs `CAP_MKNOD` and is skip-declared.
- `mutmut` does not complete on this host (SLICE-017 copy-repo environment
  crash); advisory/non-blocking.
- The cgroup-observer gate5 flake class remains possible under extreme load.
- ADR-006 remains proposed and RISK-06 remains open. SLICE-019 retains the
  exclusive right to close them; SLICE-018 did not.
