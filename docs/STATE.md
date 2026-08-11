# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-11
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — 47/47 in a checkout, absent under the gate.

## Where we stopped

SLICE-017's 47 gates pass in a checkout (`ee3470de8`). Two host drifts were fixed:
a `systemd` upgrade broke the `systemd-run` pin (`9d4e4a9b9`), and a reboot reset
the userns sysctl (now `/etc/sysctl.d/60-ranex-userns.conf`).

**ADR-019, ADR-020 and ADR-021 are written and `proposed`**, all passing the
docs gate; none paneled. OpenRouter MCP works (~$4); the opencode CLI stalls.

## Decisions

- **The verdict read channel is one signed file per subject digest** (ADR-019),
  published by atomic rename. A socket cannot serve a board that opens after a
  short-lived kernel exits; an append-only spool keeps the torn record.
- **Cause is structure, computed once** (ADR-020). `_diagnosis()` returns the
  partition; the sentence renders from it. Moving `verdict.py` reddens
  `test_kernel_unchanged.py` by design — new digest in the same commit.
- Signing does not defend the screen: the harness is unsandboxed and can draw
  anything (ADR-019 sad path 12; RISK-06 is why the channel is signed).
- **The red gate is structural.** `_deny_network` (`main.py:1411`) runs the bound
  command in an unmapped userns, so `create_user_ns()` returns EPERM. Mapping it
  hands untrusted code nested userns — two reviewers agree, not the fix.
- **ADR-021: qualification is evidence the gate consumes, not a test it runs.**
  Its integration is SLICE-019's — the claim needs `gates.yaml`, the rule needs
  the kernel, and neither is 017's to touch.
- The board is a plugin route, never a rewrite of `routes/session`.

## Next

1. **Owner call: how does 017 close?** Four routes are closed by evidence — skip
   (its gate 9), `--ignore` (weakens the gate), close-red (QA GATE), scope
   addition (owned paths + gate 10). The one left inside its owned paths: its
   two test files assert the correct *refusal* where qualification cannot run,
   keeping gate 9's frozen counts. That edits frozen tests — yours to approve.
2. ADR-021's integration belongs to SLICE-019, not to 017 and not to a slice of
   its own. Then the ADR-019 + ADR-020 kernel slice (BOARD-01, BOARD-05..14).
3. Panel ADR-019/020/021 through the OpenRouter MCP before any is accepted.

## Known limits

- **A passing count is not evidence.** 37/47 was once green against a launcher
  parking with secrets readable; 47/47 was green while the gate ran none of them.
- **Running the harness commits your working tree** (`plugin/ranex.ts`, on idle).
