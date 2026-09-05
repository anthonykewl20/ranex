# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (owner-requested release audit, issue #81)
**Active slice:** none

## Where we stopped

Auditing v0.1.0 and HEAD with real external tests and TCP/process probes.
Reproducers: tools/dogfood/release_audit.py and receiver_audit.py.
Findings: tools/dogfood/FINDINGS.md, F-007 through F-013.
The audit is in progress; a final clean-commit full-suite run is pending.

## Next

Finish clean-checkout validation and retain results before closing #81.
Remediation priorities: receiver liveness/durable delivery state, principal
enforcement, XPASS/collection diagnostics, and honest verifier boundaries.
Anti-replay and trusted journal-head anchoring remain deferred owner work.

## Governance

No frozen suite, dependency lock, signing domain, or verdict kernel change.
One runtime correction: guardian argv[0] names its resolved interpreter;
execution still uses the verified fd. Python 3.11 regression check pending.
Initial full run: 1757 passed, 34 skipped, 4 setup errors caused by the
audit's dirty tree; those errors are not reported as a product regression.

## Known limits

UNVERIFIED: live GitHub App/PR/ruleset journey and unexecuted host branches.
A hostile pytest reporter can receive signed PASS for broken code.
Journal truncation/full rewrite still verifies; retired principal metadata
does not govern producer admission; non-strict XPASS still receives PASS.
