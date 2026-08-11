# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-11
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — 47/47 in a checkout, absent under the gate.

## Where we stopped

SLICE-017's 47 gates pass in a checkout (`ee3470de8`). Two host drifts were fixed:
a `systemd` upgrade broke the `systemd-run` pin (`9d4e4a9b9`), and a reboot reset
the userns sysctl (now `/etc/sysctl.d/60-ranex-userns.conf`).

**ADR-019 and ADR-020 are written and `proposed`**, both passing the docs gate.
They are the whole design for the kernel slice the UI track waits on; neither has
been paneled. The OpenRouter MCP works (~$4 left); the opencode CLI stalls.

## Decisions

- **The verdict read channel is one signed file per subject digest** (ADR-019),
  published by atomic rename. A socket cannot serve a board that opens after a
  short-lived kernel exits; an append-only spool keeps the torn record.
- **Cause is structure, computed once** (ADR-020). `_diagnosis()` returns the
  partition; the sentence renders from it. Moving `verdict.py` turns
  `test_kernel_unchanged.py` red by design — new digest in the same commit.
- Signing does not defend the screen. `host_confinement.py` is imported nowhere
  in `src/`, so the harness is unsandboxed and can draw anything. Recorded as
  ADR-019 sad path 12; RISK-06 is why the channel is signed at all.
- **The red gate is structural.** `_deny_network` (`main.py:1411`) runs the bound
  command in a userns with no uid map, so `create_user_ns()` returns EPERM.
  Mapping it hands untrusted code nested userns — two reviewers agree, not the fix.
- The board is a plugin route, never a rewrite of `routes/session`.

## Next

1. Two routes are closed — do not retry. A skip in the SLICE-017 files trips
   their own frozen gate 9 (no skip/mock tokens, and conftest would evade it).
   `--ignore` in gates.yaml weakens the landing gate: TESTS_EXECUTED also fails
   by the bound command's exit code, which is what covers those 47 on the host.
   Left: qualification as evidence the gate consumes (needs an ADR), or red.
2. Close 017. Only then may the ADR-019 + ADR-020 kernel slice open — it is one
   slice, not two, and it unblocks BOARD-01 and BOARD-05..BOARD-14.
3. Panel both ADRs through the OpenRouter MCP before either is accepted.

## Known limits

- **A passing count is not evidence.** 37/47 was once green against a launcher
  that parked with secrets readable; 47/47 was green while the governed run ran
  none of these tests at all (`ee3470de8` fixes half: 38 errors → 18).
- **Running the harness commits your working tree** (`plugin/ranex.ts`, on idle).
