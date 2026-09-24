# State

**Updated:** 2026-09-24
**Active slice:** none — milestone 8 continues with #113; task authority (#119)
is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the whole program, required exits and trust boundaries.
Do not stop at artifact integrity or describe it as product acceptance.

SLICE-089 / #118: calibrated live HTTP observer. `ranex specification
observe-http` binds an independently pinned probe bundle, materialises the
exact Git candidate, starts real PostgreSQL/PostgREST containers by immutable
image ID, runs frozen HTTP journeys with process controls, and refuses
surviving, unrelated or failing known-bad calibration. Installed-CLI
qualification 2026-09-23, re-qualified after lint hardening 2026-09-24
(receipts bind the delivered observer bytes): 16/16 VERIFIED — three good
runs byte-identical on journey observations, three known-bad rejections at
tenant isolation, three each of the surviving-control, compile-error and
wrong-assertion refusals. Receipts: audits/2026-09-23-live-observer/.
Startup readiness can surface transient 503 probes until the PostgREST pool
warms; the observer retries under its frozen deadline. Not a verdict.

SLICE-088 / #110: deliberate-shortcut markers as deterministic evidence.
`ranex markers` greps `ranex:` markers into SARIF 2.1.0 through #97's
reducer; `evaluate()` and verdict.py are untouched. Well-formed marker =
note, trigger-less and half-empty markers = error. Acceptance rides the scan
manifest's committed `accepted` map; a scan claim bound to a scripted
interpreter's script operand is refused at load. All 8 arms VERIFIED on real
subprocesses over pinned `benjaminp/six`, 3x byte-identical repeats:
audits/2026-09-23-markers/.

Suite status, measured 2026-09-23: the host glibc moved past the owner's
pinned native build inputs (libc, libm, libz, ld-linux, ld.so.cache, libc.a),
so the drift family (slice036 selectors, approved-batch contract,
specification-batch qualification) and every nested-green ceremony test
(gating stage_08b/slice009, suite-freeze golden's run_exit=0) are red on a
pristine base checkout too — the owner re-pin HEAD already records is still
needed. Manifest refreezes remain mechanical (IDs only; outcome-blind) and
load_manifest-verified; the drift-family detail is retained at
audits/2026-09-23-live-observer/base-failures.log. The treehouse pool path
also sits deep enough that host_result_dir's `../../../etc/passwd` probe
resolves inside writable `$HOME`; those five pass from `/tmp`-depth trees.

SLICE-087 / #116: external executable probe bundles stand as recorded in
MAP §6.4. Next: #113 (self-test wiring), #111, #112, #114, #115, then
milestone 7 (#107, #108, #109), then #100 (handbook injection — where agents
are told to leave markers in the first place), #102, #105, #106.

#117: the host lane check/write race reproduced with real concurrent
processes; a persistent directory flock now serializes registry transactions.
Two-slot baseline admitted 5/5/5; fixed runs 2/2/2, one-slot 1 each.

Parallel work and overlapping verification are owner-authorized (2026-09-12);
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
