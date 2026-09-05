# State

**Updated:** 2026-09-05 (remediation, issue #82)
**Active slice:** none

Receiver failures retry, completion survives restart, connections/reads are
bounded, and corrupt receipts return named refusals. Producer/signing admission
enforces principal retirement. Collection-error reports retain actual failures.
Journal connections close; malformed JSON returns false. --expected-head detects
rewrites, truncation and deletion with an independently retained history head.
Benchmark execution fixes pytest rootdir. Positive host evidence is executed.

## Measured evidence

Storage: two 20,000-append stress runs; all chains verified and tamper controls block.
Receiver: real PR replay, 1,000 concurrent requests, repeated saturation,
SIGKILL restart, two-process shared state, damaged receipts and thread exhaustion.
External six: collection errors and retired keys now refuse correctly.
Cold start at fd13edbc0: 9 passed; governed child 1657 passed, 138 skipped.
Direct qualified host: 29 passed, zero skipped.
Live historical Ranex bootstrap: 1 passed in 2161.84s, including full child suite.
Original config/semver patches: bare GREEN, gate PASS. OSV: 34 packages, zero findings.
Real installed wheel: ranex v0.1.001, normalized metadata 0.1.1.
Evidence: tools/dogfood/audits/2026-09-05-remediation/.

## Completion gates still running

Qualified regression: 1782 passed, 9 skipped, 4 setup errors. In-session tool
edits made the freeze journey correctly refuse a dirty tree. Corrections
preserve the onboarding catalog, revalidate existing launchers, and remove
shared Git-config writes from the concurrent harness. Cold rerun is green.
Relative journal verification now accepts actual archive paths; full rerun pending.
Expanded receiver admission: 38 controls passed; earlier incomplete burst retained.
Failed database initialization now closes connections; 1,000 corrupt opens held 4 FDs.
Automatic releases use vMAJOR.MINOR.PPP after explicit dogfood-fix trailers.
The GitHub workflow needs the owner's RANEX_RELEASE_TOKEN secret.
Live installed-App publication and Kogg qualification remain UNVERIFIED.
Kogg's pinned npm build failed on Node 22 and 24; newer npm reached 17 failing tests.
Reporter truth, JUnit's lost non-strict XPASS and unchanged-evidence reuse remain
explicit boundaries. The GitHub publisher host/App credentials are trusted.
Chock's real onboarding comparison is archived; MAP names Ranex's adoption gaps.
