# State

**Updated:** 2026-09-06
**Active slice:** none

Issue #86 adds explicit external-repository selection to run, suite freeze,
gate evaluate, journal verify, deps fetch/approve and keygen (ADR-052).
Existing default authority selection and path/key confinement remain intact.
Vitest JUnit has explicit reporter/output binding and preserves its test IDs;
pytest remains the default reporter and ID convention.
The real freeze ceremony records 1,813 tests, adding 18 IDs with unchanged
expected-skip declarations; the captured freeze transcript is refreshed.

Real local pilots: Leitir's 79 treehash tests and Arxic's two version-policy
Vitest tests passed under observation. Both signed verdicts verified; source
changes and actual collection failures were rejected, followed by fresh
passing recovery and verified journal chains. Public verification material,
source patches and receipts: tools/dogfood/audits/2026-09-06-external/.
A separate wheel installation evaluated Leitir evidence and verified its journal.
These bounded modules do not establish full application acceptance.

Live App authentication, webhook delivery and App-pinned merge enforcement
remain UNVERIFIED. App credentials and a connected browser are unavailable.
Automatic PR evaluation/refresh, merge-candidate handling and distributed
shard aggregation remain unimplemented. Arxic's full suite is UNVERIFIED.
Includes issue #85's operator documentation repair.
