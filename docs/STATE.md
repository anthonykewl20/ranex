# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** ADR-011 accepted. SLICE-009 open, implementation not started.
**Active slice:** `docs/slices/SLICE-009-a-skip-is-absence.md`

## Where we stopped

ADR-011 (a skip is absence, not success) was proposed, panelled, and
accepted by the owner the same day; SLICE-009 is open to build it. Nothing
of the slice is implemented yet. The design, in one breath: suite claims
carry --junitxml inside the digest-bound argv; observation signs a
structured outcome summary into evidence (domain v2→v3, admission refuses
any other shape); a freeze-time, outcome-blind manifest of test IDs is the
committed reference set; every manifest ID must pass except declared
expected-skips; anything else — undeclared skip, xfail, xpass, error,
missing ID, bad artifact — is absence and blocks. Delegated judging reads
every trust root from the dispatch-time base tree, never the candidate.
Forgery via conftest/wheel is stated open (same trust level as the exit
code); criterion 10 proves the boundary with a passing test.

## Next

1. Implement SLICE-009 red-then-green: freeze the new tests first
   (tests/unit/test_suite_results.py,
   tests/security/test_slice009_skip_is_absence.py), observe red, then
   build: loader claim key → junitxml read-out before teardown → evidence
   v3 → manifest freeze command → the satisfies/diagnosis diff →
   base-tree manifest read for delegation. Criterion 11 last: our own
   gates.yaml + manifest, Ranex gating Ranex through the new rule.
2. Close the slice only with diff-cover 100% on the change and mutmut run.
3. Then the merge ADR (kernel-side, ADR-010's digest re-check) — deferred
   behind this gauge fix on purpose.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` — measured.
- Full suite is ~3 min (delegation e2e spawns real processes); CLAUDE.md's
  "about a second" predates SLICE-008.
- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (ADR-010 s.p. 13). RISK-06 open for `ranex run`;
  `approver_id` unauthenticated (RISK-07).
- Same-task-id dispatch has a TOCTOU window (earlier racer dies at
  cross-check). Mutmut is blind to subprocess-driven tests — weak evidence.
- The credential-gated e2e skips loudly without OPENROUTER_API_KEY —
  SLICE-009's manifest must declare exactly this skip, never invent it.
- Dependencies are trusted computing base (ADR-007). The journal detects an
  edited row, not a removed one.
