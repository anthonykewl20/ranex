# State

**Updated:** 2026-09-12
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the whole program, required exits and trust boundaries.
Do not stop at artifact integrity or describe it as product acceptance.

SLICE-087 / #116: external executable probe bundles, reusing A/B identity,
canonical bytes and verified Git object readers. New CLI freeze-probes and
check-probes preserve artifact integrity, not product PASS. Closing full-suite
evidence is on #116; verdict.py is unchanged.
Live journal experiment: three baseline matches and three named mutant failures;
499 unit tests pass on that same known-bad commit; live probe rejects it.
Raw output: tools/dogfood/audits/2026-09-12-probe-bundles/.

Next: independent live HTTP/database observer, approved known-bad calibration,
persisted task authority/three misses/reapproval, exact integration candidate,
then real application and browser release journeys. No ranex prove exists yet.
Existing SLICE-031 placeholder projections are refused by executable freeze.
Operator-supplied probes still require review; integrity cannot prove adequacy.

SLICE-085 / #88 production registration is parked under the owner pivot.
Prior queue is retained: milestone 8 (#113, #110, #111, #112, #114, #115),
then milestone 7 (#107, #108, #109), then #100, #102, #105, #106.
No production sign-off, zero-bug claim or universal deterministic-runtime claim.

#117: the host lane check/write race reproduced with real concurrent processes.
A persistent directory flock now serializes registry transactions, not workloads.
Leitir supplied pinned filelock source evidence; existing Ranex locking was reused.
Current two-slot baseline admitted 5/5/5 contenders; fixed runs admitted 2/2/2
and refused 14 each. One-slot runs admitted 1 each. All 49 focused checks pass.
Loaded manifest: 2016 IDs, 168 expected-skip declarations. Hermetic refreeze:
1856 passed / 160 skipped, run_exit=0. Golden captured from that real output.
Final host-suite evidence is bound to its commit in #117. No dependency added.
Evidence: tools/dogfood/audits/2026-09-12-leitir-lane-race/.

Parallel work and overlapping verification are owner-authorized (2026-09-12).
Use separate writer worktrees and pinned verification worktrees. The lane helper
admits two verification runs with memory checks. Refreeze on a committed tree;
load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, independent observer scheduling, merge-group checks and production
hosting/rotation/backup are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
