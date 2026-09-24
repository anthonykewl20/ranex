# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
SLICE-090 / #113: instrument self-test. `tools/dogfood/selftest.py`
pre-flights every dogfood gauge on a committed good/bad reference pair
(markers/release/receiver under tools/dogfood/selftest/references/) before
any measurement or spend; exit 0/1/2, #95 vocabulary, timing-free receipts
that are byte-identical across repeats. All three drivers pre-flight their
own instrument; the #95 driver (calibration.py) writes no calibration.json
without a passing self-test in the same run — --skip-selftest is refused,
--blunt breaks one gauge on purpose and must read FALSE-PASS. Nine arms
as-expected ×3 (tools/dogfood/audits/2026-09-24-selftest/), including the
added lock arms proven against lane.py (refusal, SIGKILL self-heal, all
three spellings admitted through the lane, forged boot-id staleness).
verdict.py untouched. calibration's subject python now defaults to
sys.executable (a bare "python3" could not import ranex in the scrubbed
subject env).

SLICE-088 / #110 and SLICE-089 / #100 stand as recorded (markers SARIF
evidence; path-scoped handbook injection, ADR-062).
Next: #111 (instruction digest), #112 (minimization ladder), #114, #115,
then milestone 7 (#107, #108, #109), then #102, #105, #106, #119. Live
observer under ADR-061 remains the program's next exit; no ranex prove
exists yet.

Suite status, measured 2026-09-23/24: host glibc moved past the owner's
pinned native build inputs, so the drift family (slice036 selectors,
approved-batch contract, specification-batch qualification) and every
nested-green ceremony test (gating stage_08b/slice009, suite-freeze golden's
run_exit=0) are red on a pristine base checkout too — the owner re-pin main
already records is still needed. Refreezes stay mechanical (IDs only).
host_result_dir's traversal probe is root-clamped (2026-09-24), so its
refusal fires from any checkout depth; the short form hit writable `$HOME`.

Parallel work and overlapping verification are owner-authorized
(2026-09-12): use separate writer worktrees and pinned verification
worktrees. Refreeze on a committed tree; load_manifest must accept the
result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
