# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** SLICE-009 closed on branch `slice009-build` (worktree
`ranex-slice009`); NOT merged to main, NOT pushed — owner decision pending.
**Active slice:** none

## Where we stopped

SLICE-009 landed: the gauge measures test identity now; a skip is absence
unless ceremony-declared. The ancestor-`.venv` capture fix also landed:
provisioned runs pin `VIRTUAL_ENV` to the verified deps environment.

## Next

1. Owner decides merge/push of `slice009-build`.
2. Diagnose CI red on `origin/main`: four SLICE-004/008 tests, red since
   2026-08-04, predating this slice, cause unknown — NOT the local `.venv`
   capture.
3. Decide mutation-testing policy. Research is running; the owner questions
   mutmut's worth, and the likely scope is kernel modules plus changed code.
4. Then the merge ADR: kernel-side digest re-check, deferred behind this
   gauge on purpose.

## Known limits

- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (ADR-010 s.p. 13). RISK-06 remains open for `ranex run`.
- `approver_id` is unauthenticated (RISK-07).
- Same-task-id dispatch has a TOCTOU window; the earlier racer dies at the
  cross-check.
- Dependencies are trusted computing base (ADR-007).
- The journal detects an edited row, not a removed one.
- Mutmut evidence is weak outside the kernel.
- The 67 declared expected-skips are permission, not obligation.
- The full suite takes about five minutes.
