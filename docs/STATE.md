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
Cold start: 9 passed. Direct qualified host: 29 passed, zero skipped.
Live historical Ranex bootstrap: 1 passed in 2161.84s, including full child suite.
Original config/semver patches: bare GREEN, gate PASS. OSV: 34 packages, zero findings.
Real installed wheel: ranex v0.1.001, normalized metadata 0.1.1.
Evidence: tools/dogfood/audits/2026-09-05-remediation/.

## Completion gates still running

Final frozen regression/coverage and actual versioned publication remain pending.
Automatic releases use vMAJOR.MINOR.PPP after explicit dogfood-fix trailers.
The GitHub workflow needs the owner's RANEX_RELEASE_TOKEN secret.
Live installed-App publication and Kogg qualification remain UNVERIFIED.
Kogg's pinned npm build failed; a newer npm diagnostic reached 17 failing tests.
Reporter truth, JUnit's lost non-strict XPASS and unchanged-evidence reuse remain
explicit boundaries. The GitHub publisher host/App credentials are trusted.
Chock's real onboarding comparison is archived; MAP names Ranex's adoption gaps.
