# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-11
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — 47/47 gates pass; still open, see Next.

## Where we stopped

SLICE-017 is implemented and all 47 frozen gates pass (`718b4aaa4`). Full suite
887 passed / 3 failed / 2 skipped, from an 838 baseline. The 3 failures are the
e2e repository-gate tests: the gate clones HEAD and runs the suite hermetically,
and SLICE-017's tests ERROR at fixture setup there — they build a real binary,
spawn systemd units, cgroups and namespaces, and run `uv run` inside a copied
repo, which the isolated materialisation cannot complete. UNVERIFIED cause;
confirm by running the governed clone before designing a fix.

## Decisions

- **The host needs `kernel.apparmor_restrict_unprivileged_userns=0`.** Ubuntu
  defaults it to 1, blocking unprivileged user namespaces; setting it took the
  gates 21 → 30. It **resets on reboot**. Ranex refusing on such a host is
  correct (ADR-006 sad path 2), not a bug.
- Host-state binding added on owner approval: LSM state, unprivileged-userns
  sysctls, boot id, machine id, delegation identity. ADR-006 sad path 21 was the
  only row assigned to no slice; SLICE-019 cannot build a re-qualification
  trigger without these recorded.
- Launcher hygiene completes **before** the gate wait, and a clean environment
  requires re-exec: `/proc/<pid>/environ` exposes the original execve envp
  region, which `clearenv()` does not alter.
- ADR-006 stays `proposed`, RISK-06 stays open. 017 qualifies only.

## Next

1. Decide the governed-clone collision: exclude SLICE-017's heavyweight tests
   from the hermetic run (bumps "a skip is absence"), give the clone what they
   need, or accept a red gate until SLICE-019. Owner's call; do not pick alone.
2. Then close 017 and open SLICE-018 (issue #21), then SLICE-019 (#22); only 019
   binds `cmd_run` and closes RISK-06.
3. Parked durability stays subordinate to P0; harness fencing is uncommitted there.

## Known limits

- Measurements from this machine were frozen as acceptance values **seven times**
  in these tests. Assert relations and roles, never measurements.
- Codex's sandbox denies ptrace, user D-Bus and namespaces, so it cannot run
  these tests; its counts are noise. Re-run locally, always.
- 37/47 was once green against a launcher that parked with secrets readable and
  proved its environment by grepping for the test's own magic string. Adversarial
  review caught it; no test did. A passing count is not evidence.
