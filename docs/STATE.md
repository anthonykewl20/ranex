# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** SLICE-008 closed. No slice open.
**Active slice:** none — next slice needs its ADR first.

## Where we stopped

SLICE-008 closed: there is a front door. `ranex task delegate` runs a harness
headless in a stripped environment that refuses to hold the signing key, kills
the whole process group at the wall-clock bound, cross-checks the emission
against its own dispatch record, measures the frozen suite sealed, and leaves
judgement to a separate keyless invocation. `task fanout` runs a bounded pool,
one worktree each; a duplicate task id refuses at dispatch. Proven end to end
against a real free model (`openrouter/cohere/north-mini-code:free`): real
diff, suite green only because the model's file reached the materialised tree,
journalled CANDIDATE naming its missing claims, chain verifying after five
concurrent runs. The fork now presents as `ranex` (`bin/ranex`, wordmark,
help), opencode's MIT attribution untouched. All uncommitted — one commit
covering kernel + harness trees is the next act.

## Next

1. **Commit SLICE-008** in both trees (kernel and `ranex-harness`), then pick
   the next ADR. Strongest candidates: **merge** (kernel-side, with the
   merge-time digest re-check ADR-010 names) or **MAP §4.6 as a gate rule**
   (start with "a skip is absence, not success").
2. Backlog: verifiable separation (signing identity that makes a violated
   execute/attest split detectable); egress confinement for the model
   credential; ADR-006/Landlock still proposed and deferred; handbooks.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` — measured.
- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (recorded, not mitigated — ADR-010 s.p. 13).
- `RISK-06` closed for the delegated path only; `ranex run` still reads the
  key before spawning. `approver_id` unauthenticated (`RISK-07`).
- Concurrent same-task-id dispatch has a TOCTOU window; the earlier racer
  dies at cross-check (latest dispatch wins). Sequential duplicates refuse.
- Mutmut is blind to subprocess-driven tests: the slice-008 security file is
  excluded (pyproject documents why), so delegation/fanout survivors overstate
  weakness — their proof is the live tests. Treat mutmut as weak evidence.
- The credential-gated e2e skips loudly without `OPENROUTER_API_KEY`; the
  operator key lives outside the repo and must never enter it.
- Dependencies are trusted computing base (ADR-007). The journal detects an
  edited row, not a removed one.
