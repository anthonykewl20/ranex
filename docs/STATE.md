# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the program, exits and trust boundaries; no ranex prove
exists; do not stop at artifact integrity or call it acceptance.

SLICE-089 / #100: path-scoped kernel handbook injection (ADR-062): project
layer governance/handbook.json over the system layer (one operator),
resolved purely per path. task delegate injects the chapters into the brief
and lands {digest, chapters, matched, unmatched} as the additive ADR-043
manifest field. No handbook anywhere is byte-identical to before; run/gate
evaluate never read a handbook; verdict.py unchanged. Six #95 control pairs
VERIFIED ×3 (tools/dogfood/audits/2026-09-24-handbook-injection/).

SLICE-088 / #110: deliberate-shortcut markers as deterministic evidence —
`ranex markers` into SARIF 2.1.0, trigger-less/half-empty markers are
errors, acceptance rides the committed `accepted` map; 8 arms VERIFIED ×3
over pinned benjaminp/six (2026-09-23-markers/).

#111 shipped: `task delegate` records what shaped the work. Outcome and
ADR-043 manifest carry `instruction_digest` — sha256 over the canonical
composed instruction (since ADR-062, the prompt with injected chapters in
it) — and the instruction is retained as a redacted `instruction` stream
under the unchanged ADR-043 rules; signed envelope untouched (v6 is
PR-07/ADR-016). Evidence: 2026-09-24-issue111-instruction-digest/.

Next: #113 (self-test wiring), #112, #114, #115, milestone 7 (#107, #108,
#109), then #102, #105, #106; #102 review and #112 minimization compose the
handbook and digest records later.

Suite status 2026-09-23/24: host glibc moved past the owner's pinned native
build inputs, so the drift family (slice036, approved-batch, spec-batch) and
every nested-green ceremony test (gating, suite-freeze golden) are red on a
pristine base too — the owner re-pin main already records is still needed.
Refreezes stay mechanical (IDs only). The treehouse pool path sits deep
enough that host_result_dir's `../../../etc/passwd` probe resolves inside
writable $HOME; those five pass from /tmp.

SLICE-087 / #116 and #117 stand as recorded in their slices and audits.
Parallel work and overlapping verification are owner-authorized (2026-09-12);
refreeze on a committed tree and load_manifest before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined; harness mediation, observer
scheduling, merge-group checks and production hosting are UNVERIFIED (MAP).
