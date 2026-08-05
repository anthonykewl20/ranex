# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-06
**Phase:** ADR-012 accepted; harness fully rebranded. Implementation not started.
**Active slice:** none

## Where we stopped

ADR-012 is accepted: `ranex task merge` is the only governed publication path —
fast-forward ancestry checked, merge commits excluded, judged digest and
immutable policy blobs re-checked, approval bound to candidate/tip/policy/
CANDIDATE-row identity, then one expected-old ref update. Prior art vendored,
re-fetched, byte-matched; REFUTE panel and its substitutions are in the ADR.

The harness is fully rebranded (owner's decision): `ranex.json` config,
`RANEX_*` env, ranex directories and username. `packages/opencode` and
`@opencode-ai/*` stay — pinned by the frozen tests here, invisible to
operators. Pushed to anthonykewl20/ranex-harness (`origin`; `upstream` =
anomalyco/opencode). Suite baseline at `1079faa4f5`: 2896 pass / 68 fail —
byte-identical failures at pre-rebrand `fb650d29b0`, so all pre-existing
(bridge/trim era: subprocess, acp, tui clusters; ~20 flaky between runs).

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
