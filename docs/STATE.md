# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.

SLICE-088 / #100: path-scoped kernel handbook injection shipped (ADR-062).
Two layers — governance/handbook.json (project) over
${XDG_CONFIG_HOME:-$HOME/.config}/ranex/handbook.json (system), one operator —
resolve purely per path: project wins, merge_system keeps system first, a
data-driven sniff_marker decorates the system layer only, unmatched paths are
recorded rows. task delegate injects chapters plus the table into the brief
and lands {digest, chapters, matched, unmatched} as the additive ADR-043
manifest field. No handbook anywhere is byte-identical to before; run/gate
evaluate never read a handbook; verdict.py unchanged (digest-pinned). #95
proof: six control pairs over six@1.17.0 (ebd9b3af9…48d07) and this repo,
all VERIFIED ×3 — tools/dogfood/audits/2026-09-24-handbook-injection/.
#102 delegated review and #112 minimization compose this later.

Next: independent live HTTP/database observer (#118 in flight), approved
known-bad calibration, persisted task authority/three misses/reapproval,
exact integration candidate, then real application and browser release
journeys. No ranex prove exists yet. SLICE-087/#116 closing evidence lives
in that slice and its audit.

SLICE-085 / #88 production registration is parked under the owner pivot.
Queue: milestone 8 (#113, #110, #111, #112, #114, #115), milestone 7
(#107, #108, #109), then #102, #105, #106 — no production sign-off,
zero-bug claim or universal deterministic-runtime claim.

#117: lane check/write race fixed with a persistent directory flock over
registry transactions; hermetic refreeze 1856/160 with a golden from that
run (tools/dogfood/audits/2026-09-12-leitir-lane-race/).
Host fact: /etc/ld.so.cache drifted again 2026-09-10; reproducible-build
goldens and launcher host-fact tests refuse E-C17-BUILD-INPUT-DRIFT until
the owner re-pins. The 2026-09-24 runs show exactly that class (slice036
selectors, batch qualification, gating-real stage 08b, host-result-dir
confinement, and the suite-freeze golden's run_exit=0 seal) — all reproduce
on pristine main 3edad33af, not this slice's change.

Parallel work and overlapping verification are owner-authorized (2026-09-12):
separate writer worktrees, pinned verification worktrees, two-lane helper.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, independent observer scheduling, merge-group checks and production
hosting/rotation/backup are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
