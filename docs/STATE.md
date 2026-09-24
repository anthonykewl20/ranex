# State

**Updated:** 2026-09-25
**Active slice:** none — #111 closed on PR #124; #112/#114/#115 then task authority (#119) follow.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge;
ADR-061 defines the whole program, required exits and trust boundaries. Do
not stop at artifact integrity or describe it as product acceptance.

SLICE-091 / #118: calibrated live HTTP observer — `ranex specification
observe-http` binds a pinned probe bundle, materialises the exact candidate,
starts real PostgreSQL/PostgREST containers by immutable image ID, runs
frozen HTTP journeys, refuses surviving/unrelated/failing known-bad
calibration. 16/16 VERIFIED (audits/2026-09-23-live-observer/). Not a verdict.

SLICE-090 / #113: instrument self-test — tools/dogfood/selftest.py
pre-flights every gauge on a committed good/bad pair before any measurement;
calibration writes nothing without a passing self-test. Nine arms ×3
(audits/2026-09-24-selftest/); verdict.py untouched.

SLICE-089 / #100 and SLICE-088 / #110 stand as recorded (path-scoped handbook
injection ADR-062; markers SARIF evidence).

#111 shipped: `task delegate` records what shaped the work. Outcome and
ADR-043 manifest carry `instruction_digest` — sha256 over the canonical
composed instruction (the prompt with injected chapters in it) — and the
instruction is retained as a redacted `instruction` stream under the
unchanged ADR-043 rules; signed envelope untouched (v6 is PR-07/ADR-016).
Evidence: 2026-09-24-issue111-instruction-digest/.

Queue: #112 (minimization ladder), #114, #115, milestone 7 (#107-#109),
then #102, #105, #106, #119; #102 review and #112 compose the digest and
handbook records later.

Suite status 2026-09-23/24: host glibc moved past the owner's pinned native
build inputs, so the drift family (slice036, approved-batch, spec-batch) and
every nested-green ceremony test (gating, suite-freeze golden) are red on a
pristine base too — the owner re-pin main already records is still needed
(audits/2026-09-23-live-observer/base-failures.log). Refreezes stay
mechanical (IDs only). host_result_dir's traversal probe is root-clamped
(2026-09-24); its refusal fires from any checkout depth.

Parallel work and overlapping verification are owner-authorized (2026-09-12);
refreeze on a committed tree and load_manifest before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Harness mediation, observer scheduling, merge-group checks
and production hosting are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
