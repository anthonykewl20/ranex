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

**ADR-019 and ADR-020 are written and `proposed`**, both passing the docs gate.
They are the whole design for the kernel slice the UI track waits on. Neither
has been read by an outside panel: the OpenRouter credential is expired, and
both ADRs disclose that in their Confirmation sections rather than imply consensus.

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
- Host needs `kernel.apparmor_restrict_unprivileged_userns=0`; **resets on reboot**.
- The board is a plugin route, never a rewrite of `routes/session`.

## Next

1. Decide the governed-clone collision: exclude SLICE-017's heavyweight tests
   (bumps "a skip is absence"), equip the clone, or accept red until SLICE-019.
2. Close 017. Only then may the ADR-019 + ADR-020 kernel slice open — it is one
   slice, not two, and it unblocks BOARD-01 and BOARD-05..BOARD-14.
3. Re-auth OpenRouter (`/mcp`) and panel both ADRs before either is accepted.

## Known limits

- **Running the harness commits your working tree.** `plugin/ranex.ts` does
  `git add -A && git commit` on idle; it swept the fencing work into `98130460a0`.
- Measurements from this machine were frozen as acceptance values **seven times**
  in these tests. Assert relations and roles, never measurements.
- 37/47 was once green against a launcher that parked with secrets readable.
  Review caught it; no test did. A passing count is not evidence.
