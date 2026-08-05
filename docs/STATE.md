# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** ADR-012 written and REFUTE-panelled; implementation has not started.
**Active slice:** none

## Where we stopped

ADR-012 is accepted: `ranex task merge` is the only governed publication path.
It checks fast-forward ancestry, excludes merge commits above the observed tip,
re-checks the exact judged tree digest and immutable policy blobs, verifies a
signed approval bound to candidate/tip/policy/CANDIDATE-row identity, then makes
one expected-old ref update. The harness never merges and the human never pushes.

The six prior-art implementations are vendored under
`docs/adr/prior-art/ADR-012/`; each was independently re-fetched from its pinned
URL on 2026-08-05 and byte-matched. The REFUTE panel accepted history-smuggling,
pre-signing, evidence-reuse and crash-recovery controls; its substitutions
and timeouts are recorded in the ADR.

## Next

1. Open SLICE-010 implementing `ranex task merge` exactly per
   `docs/adr/ADR-012-the-kernel-merges.md`, with red-first refusal tests.
2. Continue the rest of MAP §4.6: entry-point-observed spawning,
   `tests-executed` vs `product-exercised`, and assertion strength.

## Known limits

- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (ADR-010 sad path 13). RISK-06 remains open for `ranex run`.
- `approver_id` remains unauthenticated (RISK-07).
- Approval at an unmoved target tip never expires; only advancing the tip
  revokes it. No wall clock enters the kernel.
- There is no merge queue/train; under contention a slow candidate may starve.
- Ref writes bypassing the kernel are in the operator's trust domain.
- Same-task-id dispatch has a TOCTOU window; the earlier racer dies at cross-check.
- Dependencies are trusted computing base (ADR-007).
- The journal detects an edited row, not a removed one.
- A hostile tree can forge the suite artifact; the passing security test states
  that boundary.
- The 67 declared expected-skips are permission, not obligation; the manifest
  holds 737 IDs and re-freezing is the only way in.
- Submodule/LFS subject boundaries remain ADR-009's materialisation contract.
- The full suite takes about six minutes; mutation re-baselining about fifteen.
