# State

**Updated:** 2026-09-05 (issue #82 release follow-up)
**Active slice:** none

v0.1.001 is immutable at 6582acff9be6c7ce6dd957c769de1b02289a18ed.
Its release helper ran the frozen suite: 1786 passed, 9 skipped, 1973.22 seconds.
Wheel and sdist built; main and tag pushed atomically and verified remotely.
Installed wheel and existing-tag, repeated-run and stale-source guards passed.

## Hosted failures and follow-up

Main CI 33971550685 failed the instrumented eight-writer burst in schema setup.
Tag CI 33971550287 passed that regression but the receiver driver raced its probe.
F-018: inspect schema; initialize missing objects in an immediate transaction.
F-028: observe the actual Git child before sending the busy-delivery probe.
At 7e559bfbc on hosted-matched Python 3.14.7 / SQLite 3.53.1:
- 100,000 real gate-record appends, 25 rounds, eight writers, one CPU: all verified.
- 1000 damaged-header opens: six descriptors throughout; both triggers recovered.
- Ten CAS races: ten winners, 70 named stale refusals; all chains verified.
- Two real PR/TCP/process receiver repeats: 41/41 controls each, one/two CPUs.
- Existing journal regression: 22 passed in 15.72 seconds.
Fresh hosted CI and final-commit frozen validation are pending for v0.1.002.
The original hosted failures and diagnostic source provenance remain archived.

## Retained evidence and limits

Prior Six collection/signature/executable journeys, qualified-host runs, real
receiver/storage stress and installed-package receipts remain in the archive.
The owner's RANEX_RELEASE_TOKEN secret is absent; unattended publication and
live installed-App publication remain UNVERIFIED. Kogg qualification is
UNVERIFIED under its pinned npm environment. Reporter truth, JUnit-lost non-strict
XPASS and unanchored history/evidence reuse remain documented boundaries.
Finite stress does not prove SQLite fairness or establish the old failure's cause.
Evidence: tools/dogfood/audits/2026-09-05-remediation/ and tools/dogfood/FINDINGS.md.
