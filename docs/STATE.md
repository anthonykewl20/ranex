# State

**Updated:** 2026-09-23
**Active slice:** none — task authority (#119) is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the whole program, required exits and trust boundaries.
Do not stop at artifact integrity or describe it as product acceptance.

SLICE-088 / #118: calibrated live HTTP observer. `ranex specification
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

SLICE-087 / #116: freeze-probes/check-probes preserve artifact integrity, not
product PASS; verdict.py is unchanged. Live journal experiment: three baseline
matches, three named mutant failures, 499 green unit tests on a known-bad
commit rejected by the live probe. Output: audits/2026-09-12-probe-bundles/.

Host drift, second occurrence: /etc/ld.so.cache drifted again 2026-09-10, so
reproducible-build digests (slice036 worker, batch-qualification static
worker, suite-freeze golden round-trip) mismatch on this host. The 24
affected tests fail identically on the pristine base commit 0de369b62
(retained log: audits/2026-09-23-live-observer/base-failures.log); owner
re-pin still needed. A refreeze on this host carries run_exit=1 from that
drift; the golden records the real output.

SLICE-085 / #88 production registration is parked under the owner pivot.
Prior queue is retained: milestone 8 (#113, #110, #111, #112, #114, #115),
then milestone 7 (#107, #108, #109), then #100, #102, #105, #106.
No production sign-off, zero-bug claim or universal deterministic-runtime claim.

Parallel work and overlapping verification are owner-authorized (2026-09-12).
Use separate writer worktrees and pinned verification worktrees. Refreeze on a
committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, independent observer scheduling, merge-group checks and production
hosting/rotation/backup are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
