# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-11
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — 47/47 gates pass; still open, see Next.

## Where we stopped

SLICE-017 is implemented and all 47 frozen gates pass (`718b4aaa4`). Full suite
887 passed / 3 failed / 2 skipped, from an 838 baseline. The 3 failures are the
e2e repository-gate tests: SLICE-017's tests ERROR at fixture setup inside the
hermetic clone, which cannot build a binary, spawn systemd units and cgroups,
and run `uv run` in a copy. UNVERIFIED cause; run the clone before fixing.

**The UI redesign is a separate track**, not a slice: ADR-018 `accepted`,
BOARD-01..BOARD-22 on the harness repo. Landed there: BOARD-03 (degraded
rendering), BOARD-04 (board route), BOARD-01's contract. Blocked: the bridge is
emit-only, so no verdict can reach the harness.

## Decisions

- **The host needs `kernel.apparmor_restrict_unprivileged_userns=0`.** It took
  the gates 21 → 30 and **resets on reboot**; refusing there is ADR-006 sad path 2.
- Host-state bound on owner approval: LSM state, userns sysctls, boot id, machine
  id, delegation identity. SLICE-019 needs these to re-qualify.
- Launcher hygiene completes **before** the gate wait, and a clean environment
  needs re-exec: `/proc/<pid>/environ` keeps the original envp past `clearenv()`.
- ADR-006 stays `proposed`, RISK-06 stays open. 017 qualifies only.
- The board is a plugin route, never a rewrite of `routes/session`: `packages/tui`
  is ~163 insertions from fork base `012c2f57`, and a rewrite ends mergeability.

## Next

1. Decide the governed-clone collision: exclude SLICE-017's heavyweight tests
   (bumps "a skip is absence"), equip the clone, or accept red until SLICE-019.
2. Then close 017 and open SLICE-018 (issue #21), then SLICE-019 (#22); only 019
   binds `cmd_run` and closes RISK-06.
3. UI track, alongside: one kernel slice for the verdict read channel plus
   BOARD-02's structured cause. It unblocks nine board issues.

## Known limits

- **Running the harness commits your working tree.** `plugin/ranex.ts` does
  `git add -A && git commit` on idle; it swept the fencing work into `98130460a0`.
- Measurements from this machine were frozen as acceptance values **seven times**
  in these tests. Assert relations and roles, never measurements.
- 37/47 was once green against a launcher that parked with secrets readable.
  Review caught it; no test did. A passing count is not evidence.
