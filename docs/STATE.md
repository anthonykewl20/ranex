# State

**Updated:** 2026-09-05 (remediation, issue #82)
**Active slice:** none

Receiver retries failed attempts, retains durable completion across restart,
bounds connections and reads, and refuses damaged receipts without crashing.
Producer/signing admission now enforces existing principal retirement rules.
Actual collection errors retain their observed module identity.
Journal connections close; corrupt JSON returns false. --expected-head checks
an independently retained head against deletion, truncation and rewrites.
Real benchmark execution now sets pytest rootdir consistently.

## Measured evidence

Two real storage stress runs: 20,000 appends each; all chains verified.
Real public PR replay: 1,000 concurrent requests, restart and saturation;
two receivers shared 200 deliveries; corrupt receipt recovery succeeded.
Cold start: 9 passed with actual host evidence. Direct host checks:
29 passed, zero skipped. Historical bootstrap rerun is still running.
Original config-parse and semver agent patches: bare GREEN, gate PASS.
Wheel installed outside checkout reports ranex v0.1.001; package version 0.1.1.
Receipts: tools/dogfood/audits/2026-09-05-remediation/.

## Remaining before completion

Complete current external audit, real subject bootstraps and final frozen CI.
Reconcile findings and archive final evidence. No release has been pushed.
Automatic tags use vMAJOR.MINOR.PPP after explicit dogfood fix trailers.
The release workflow needs the owner's RANEX_RELEASE_TOKEN secret.
Live installed GitHub App publication remains UNVERIFIED without setup.
Hostile reporter truth, non-strict XPASS lost by JUnit and unchanged-evidence
reuse remain explicit boundaries. Journal anchors must be independently kept.
