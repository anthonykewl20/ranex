# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** SLICE-008 committed in both trees. ADR-011 proposed, staged.
**Active slice:** none — ADR-011 awaits acceptance; SLICE-009 opens then.

## Where we stopped

SLICE-008 is committed (kernel d3f5967ce, harness fb650d29b0). ADR-011 —
a skip is absence, not success (MAP §4.6's first control) — is researched,
panelled, authored, and staged with four vendored citations under
docs/adr/prior-art/ADR-011/. Suite green: 624 passed, 2 skipped (the
credential-gated e2e). The decision: suite claims carry --junitxml inside
the digest-bound argv; observation signs a structured outcome summary into
evidence (domain v2→v3); a freeze-time, outcome-blind manifest of test IDs
is the reference set; every manifest ID must pass except declared
expected-skips; anything else is absence and blocks. A REFUTE panel
(tencent/hy3, qwen/qwen3-max) forced two fixes now in the design: delegated
judging reads every trust root from the dispatch-time base tree, never the
candidate commit; and the manifest ID set is taken outcome-blind, because
newly frozen tests are red under red-then-green.

## Next

1. Commit the staged proposal: `docs: propose ADR-011 — a skip is absence`.
2. Accept ADR-011, open SLICE-009, implement: the loader's junitxml claim
   key, artifact read-out before teardown, evidence v3, manifest
   generation, the satisfies/diagnosis extension. FT-07 (red-then-green)
   rides on the same freeze-time artifact later.
3. Then the merge ADR (kernel-side, with ADR-010's digest re-check) —
   deferred behind the gauge fix on purpose: merge must consume verdicts a
   skip cannot hollow out.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` — measured.
- Full suite is ~3 min now (delegation e2e spawns real processes);
  CLAUDE.md's "about a second" predates SLICE-008.
- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (recorded, not mitigated — ADR-010 s.p. 13).
- RISK-06 closed for the delegated path only; `ranex run` still reads the
  key before spawning. `approver_id` unauthenticated (RISK-07).
- Same-task-id dispatch has a TOCTOU window (earlier racer dies at
  cross-check). Mutmut is blind to subprocess-driven tests — weak evidence.
- The credential-gated e2e skips loudly without OPENROUTER_API_KEY —
  ADR-011's manifest must declare exactly this skip, never invent it.
- Dependencies are trusted computing base (ADR-007). The journal detects an
  edited row, not a removed one.
