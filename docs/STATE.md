# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (owner-requested remediation, issue #82)
**Active slice:** none

## Work in progress

Issue #82 follows the preserved release audit in tools/dogfood/audits/2026-09-05/.
Owner requests remediation of all findings, real-data end-to-end stress runs,
and automated padded patch releases. No finding is closed by this checkpoint.

Receiver now bounds connections and request reads, durably records completion,
and permits retry after failed fetch/API attempts; signed malformed events refuse.
Principal catalog retirement/conflicts are checked by admission loaders.
Collection-error records retain actual observed module IDs.
Journal connections close deterministically; corrupt JSON verifies false.
Optional journal --expected-head compares against an independently retained head.
Benchmark collection fixes rootdir; old fault receipts remain unchanged.
Real bootstrap pin advances to the clean audited be228ca revision and its lock.

## Evidence so far

Both receiver probe reruns: 16 verified receiving-boundary controls each.
Original config-parse and semver agent patches: real bare suites GREEN and
governed gates PASS after the rootdir correction. Receipts currently in
.local/remediation-82/; archive final evidence before completing this issue.
These runs do not establish live GitHub App publication or exhaustive correctness.

## Remaining

Stress real sockets, Git recovery, storage concurrency, signed external execution;
run sequential qualified-host/nested journeys and the updated real bootstrap.
Validate release preparation/build/publication and complete frozen regression CI.
Reconcile every finding with its actual evidence; keep residual limits explicit.
Release workflow requires the owner's RANEX_RELEASE_TOKEN repository secret.
Live installed App target/credentials have been requested from the owner.
Reporter truth, non-strict XPASS lost by JUnit, and replay of unchanged evidence
remain limitations; external-head verification requires a separately trusted anchor.
