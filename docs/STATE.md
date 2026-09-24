# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
SLICE-089 / #100: path-scoped kernel handbook injection (ADR-062).
Two layers — governance/handbook.json (project) over
${XDG_CONFIG_HOME:-$HOME/.config}/ranex/handbook.json (system), one operator —
resolve purely per path: project wins, merge_system keeps system first, a
data-driven sniff_marker decorates the system layer only, unmatched paths are
recorded rows. task delegate injects chapters plus the table into the brief
and lands {digest, chapters, matched, unmatched} as the additive ADR-043
manifest field. No handbook anywhere is byte-identical to before; run/gate
evaluate never read a handbook; verdict.py unchanged (digest-pinned). #95
proof: six control pairs over six@1.17.0 (ebd9b3af9…48d07) and this repo, all
VERIFIED ×3 — tools/dogfood/audits/2026-09-24-handbook-injection/. #102
delegated review and #112 minimization compose this later.

SLICE-088 / #110: deliberate-shortcut markers as deterministic evidence —
`ranex markers` greps `(#|//) ?ranex:` markers into SARIF 2.1.0; trigger-less
and half-empty markers are errors; acceptance rides the scan manifest's
committed `accepted` map; a scan claim bound to a script operand is refused
at load. All 8 arms VERIFIED ×3 over pinned benjaminp/six, byte-identical
(tools/dogfood/audits/2026-09-23-markers/).
Next: #113 (self-test wiring), #111, #112, #114, #115, then milestone 7
(#107, #108, #109), then #102, #105, #106. Live observer under ADR-061
remains the program's next exit; no ranex prove exists yet.

Suite status, measured 2026-09-23/24: host glibc moved past the owner's
pinned native build inputs, so the drift family (slice036 selectors,
approved-batch contract, specification-batch qualification) and every
nested-green ceremony test (gating stage_08b/slice009, suite-freeze golden's
run_exit=0) are red on a pristine base checkout too — the owner re-pin main
already records is still needed. Refreezes stay mechanical (IDs only).
host_result_dir's traversal probe is root-clamped (2026-09-24), so its
refusal fires from any checkout depth; the short form hit writable `$HOME`.

SLICE-087 / #116 and #117 stand as recorded in their slices and audits
(probe bundles; lane-flock registry serialization, refreeze 1856/160).
Parallel work and overlapping verification are owner-authorized (2026-09-12):
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
