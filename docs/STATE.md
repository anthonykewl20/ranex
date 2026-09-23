# State

**Updated:** 2026-09-23
**Active slice:** none — SLICE-088 closed on #110; milestone 8 continues
with #113 next.

SLICE-088 / #110: deliberate-shortcut markers as deterministic evidence.
`ranex markers` (and `python -P -m ranex.foundation.markers`) greps
`(#|//) ?ranex:` markers and emits SARIF 2.1.0 through #97's reducer;
`evaluate()` and verdict.py are untouched. Well-formed marker = note,
trigger-less (`no-trigger`) and half-empty markers = error. Acceptance rides
the scan manifest's committed `accepted` map. Correction 2 closed at the
catalog: a scan claim bound to a scripted interpreter's script operand is
refused at load (the #97 forger tests ride inline `-c` bytes now). All 8
arms VERIFIED on real subprocesses over pinned `benjaminp/six`, 3x repeats,
byte-identical: tools/dogfood/audits/2026-09-23-markers/.

Suite status, measured 2026-09-23: the host glibc moved past the owner's
pinned native build inputs (libc, libm, libz, ld-linux, ld.so.cache, libc.a),
so the drift family (slice036 selectors, approved-batch contract,
specification-batch qualification) and every nested-green ceremony test
(gating stage_08b/slice009, suite-freeze golden's run_exit=0) are red on a
pristine base checkout too — the owner re-pin HEAD already records is still
needed. #110's manifest refreeze was still performed mechanically (IDs only;
outcome-blind by contract) and verified a superset. The treehouse pool path
also sits deep enough that host_result_dir's `../../../etc/passwd` probe
resolves inside writable `$HOME`; those five pass from `/tmp`-depth trees.

SLICE-087 / #116: external executable probe bundles stand as recorded in
MAP §6.4. Next: #113 (self-test wiring), #111, #112, #114, #115, then
milestone 7 (#107, #108, #109), then #100 (handbook injection — where agents
are told to leave markers in the first place), #102, #105, #106.

Live journal experiment: three baseline matches and three named mutant
failures; 499 unit tests pass on that same known-bad commit; live probe
rejects it (tools/dogfood/audits/2026-09-12-probe-bundles/).

#117: the host lane check/write race reproduced with real concurrent
processes; a persistent directory flock now serializes registry transactions.
Two-slot baseline admitted 5/5/5; fixed runs admitted 2/2/2, one-slot 1 each.

Parallel work and overlapping verification are owner-authorized (2026-09-12);
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
