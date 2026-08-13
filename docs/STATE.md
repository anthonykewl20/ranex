# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-13
**Active slice:** none.

## Where we stopped

SLICE-017 is closed. ADR-021 was accepted after consensus. SLICE-019 implemented
host qualification as signed, subject-bound landing-gate evidence, passed its
qa-gate after five consensus rounds (consensus QA-PASS ×2), and is now closed.

## Preserved for SLICE-020 (ready when SLICE-019 closes)

SLICE-020 (judgment identity and verdict-read channel under ADR-019/020) is
preserved on branch `agent/slice020-impl`. It is the next slice.

## Next

1. Resume SLICE-020 from `agent/slice020-impl`.
2. Then SLICE-018/029; SLICE-029..044 strictly one at a time (ADR-017; MAP §0.26).

## Known limits

- The materialised suite is not fully deterministic — a SLICE-017 cgroup-inotify
  test flaked once under load and remains unfixed.
- The cgroup-observer test has a known unresolved flake.
- Running the harness commits its tree on idle (`plugin/ranex.ts`).
- The real qualification e2e honestly skips on hosts without delegated cgroup
  `cpu`; `cmd_run` confinement and RISK-06 remain open.
