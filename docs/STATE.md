# State

**Updated:** 2026-09-05 (issue #82 reopened after release validation)
**Active slice:** none

v0.1.001 is immutable at 6582acff9be6c7ce6dd957c769de1b02289a18ed.
Its release helper ran the frozen suite: 1786 passed, 9 skipped, 1973.22 seconds.
Wheel and sdist built; main and tag pushed atomically and verified remotely.
Installed wheel: ranex v0.1.001, Python metadata 0.1.1. Existing-tag, repeated-run
and stale-source release guards passed against the actual published history.

## Hosted failures and follow-up

Main CI 33971550685 failed the instrumented eight-writer journal burst in schema
initialization. Tag CI 33971550287 passed that regression but the paused-Git
stress driver raced its own probe. Neither hosted failure is called PASS.
F-018: inspect existing schema; create missing objects in an immediate transaction.
F-028: observe the actual Git child before sending the busy-delivery probe.
An initial 20,000-append journal diagnostic passed; its source override is retained.
Python now matched to hosted 3.14.7 (SQLite 3.53.1) for follow-up validation.
Missing-trigger recovery, increased real contention, repeated receiver journeys
and fresh hosted CI are pending. Any release of these fixes must be v0.1.002.

## Retained evidence and limits

Prior real PR/process stress, Six collection/signature/executable journeys,
qualified-host runs and package receipts remain in the remediation archive.
The 293-file archive before this follow-up was fully tracked and digest-verified.
Source commit f8c73b35b had successful hosted CI; later release failures are retained.
The owner's RANEX_RELEASE_TOKEN secret is still absent; unattended publication
and live installed-App publication remain UNVERIFIED. Kogg qualification is
UNVERIFIED under its pinned npm environment. Reporter truth, JUnit-lost non-strict
XPASS and unanchored history/evidence reuse remain documented boundaries.
Evidence: tools/dogfood/audits/2026-09-05-remediation/ and tools/dogfood/FINDINGS.md.
