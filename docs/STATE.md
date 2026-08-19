# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 mid-flight, BLOCKER 3 ruling pending)
**Active slice:** docs/slices/SLICE-057-real-e2e-execution-family.md

## Where we stopped

SLICE-057 (#37) mid-implementation, STOPPED at the survivor arm —
BLOCKER 3 on #37 (comment 5347838349) awaits the amendment ruling.
Landed this range (main, not pushed): 0013bf427 enrollment drain fix
(BLOCKER 1), f4b09b264 re-qualification (ld.so.cache), 128d13552
default-deny-v1 admits `clock_nanosleep` + tracked re-pin (BLOCKER 2
ruling applied; `nanosleep` not issued by the pinned artifact — not
admitted), d2881a2e0 the run + confinement goldens. State at d2881a2e0:
run family 5 passed plain AND delegated; confinement delegated 6
passed / 1 failed (survivor: dash "Cannot fork" — the allowlist also
omits clone/execve/wait4 + id-probes; census in the BLOCKER), plain
2 passed + 5 declared `qualified_host` skips; freeze 2 passed / 4 red
as designed (manifest stale +18 IDs, golden lands at the ceremony).
Frozen suites over the re-pin: slice017 47 passed; slice046/047/018 +
confinement-result/trace-invariance/kernel-unchanged 52 passed / 3
pre-existing skips; no test pins the shifted digests.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-057 (open, implementation lane, ruling pending)
Worker B resumes on the BLOCKER 3 ruling: (a/a′) process-creation
allowlist completion → same rebuild/re-qualify/re-pin mechanics →
survivor arm green → full suite green (5 skips declared) → ceremony
(+18 IDs, 5 context-tier declarations) → freeze golden → AC2 trace
stream + AC3 sabotage red posted → close per the issue's bar. Open
follow-ups stand: the P3 mirror-pin test for `_journal_first_broken_row`,
and the SLICE-055 follow-ups queued in its done slice file.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
