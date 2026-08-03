# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-03
**Phase:** map — v3.0.0 complete, ready to direct; awaiting owner's go
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`

## Where we stopped

**The map carries the full thesis and is ready to direct the build.** Owner
decided the full harness — Ranex owns the restaurant: harness = trimmed opencode
fork (MIT, pinned commit) molded to the kernel; kernel stays a separate process
(hooks collect, kernel stamps); delegation = foreman → supervisors → workers,
clean-room patterns from oh-my-openagent (its code is SUL-1.0 — never copied,
converted or not); governance/ = handbook library; Web UI parked. MAP §17 is the
trim spec: keep/cut/assess, horsepower-vs-fuel-economy measures, customization
policy (few knobs, deep customization blocked). CLAUDE.md and README aligned.

**Awaiting the owner:** declare the map done, then pick the first step — the
fork ADR (recorded order, MAP §0.14) or SLICE-006. **Do not start either until
told.**

## Next

1. **The fork ADR** — researched per ADR-003: pinned opencode commit, trim list
   confirmed against code (§17.3), kernel-bridge protocol, vendored prior art,
   sad paths. Then: trimmed fork → first delegation → handbooks.
2. SLICE-006, then confinement — only once the owner unblocks them. Confinement
   is now load-bearing for the harness wall.
3. Map gaps kept on purpose: VP-05/VP-06 govern no view until the harness and
   SLICE-006 give them one; §17 numbers are measured at fork time.

## Known limits

- `docs/MAP.html` is a projection of v2.8.0 — stale against 3.0.0; regenerate or
  delete once the map settles.
- Fork debt recorded, not solved: the trim must stay rebaseable.
- Clean-room is a discipline, not yet a check.
- The journal detects an edited row but not a removed one.
- `approver_id` unauthenticated; same-uid key theft open; Ranex does not gate
  its own repo yet.
