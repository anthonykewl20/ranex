# State

**Updated:** 2026-09-24
**Active slice:** none — #111 (instruction digest) is next; task authority (#119) under ADR-061 follows the milestone-8 queue.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge;
ADR-061 defines the whole program, required exits and trust boundaries. Do
not stop at artifact integrity or describe it as product acceptance.

SLICE-091 / #118: calibrated live HTTP observer. `ranex specification
observe-http` binds an independently pinned probe bundle, materialises the
exact Git candidate, starts real PostgreSQL/PostgREST containers by immutable
image ID, runs frozen HTTP journeys with process controls, and refuses
surviving, unrelated or failing known-bad calibration. Qualification and the
lint-hardening re-run: 16/16 VERIFIED, receipts bind the delivered observer
bytes (audits/2026-09-23-live-observer/). Transient 503 readiness probes
retry under the frozen deadline. Not a verdict.

SLICE-090 / #113: instrument self-test. tools/dogfood/selftest.py
pre-flights every dogfood gauge on a committed good/bad reference pair
before any measurement; calibration.py writes no calibration.json without a
passing self-test in the same run; --blunt must read FALSE-PASS. Nine arms
as-expected ×3 (audits/2026-09-24-selftest/); verdict.py untouched.

SLICE-089 / #100 and SLICE-088 / #110 stand as recorded (path-scoped
handbook injection ADR-062; markers SARIF evidence). Queue: #111
(instruction digest), #112 (minimization ladder), #114, #115, milestone 7
(#107-#109), then #102, #105, #106, #119.

Suite status, measured 2026-09-23/24: host glibc moved past the owner's
pinned native build inputs, so the drift family (slice036 selectors,
approved-batch contract, specification-batch qualification) and every
nested-green ceremony test (gating stage_08b/slice009, suite-freeze golden's
run_exit=0) are red on a pristine base checkout too — the owner re-pin main
already records is still needed; detail at
audits/2026-09-23-live-observer/base-failures.log. Refreezes stay
mechanical (IDs only, outcome-blind). host_result_dir's traversal probe is
root-clamped (2026-09-24), so its refusal fires from any checkout depth.

Parallel work and overlapping verification are owner-authorized (2026-09-12);
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Harness mediation, observer scheduling, merge-group checks
and production hosting are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
