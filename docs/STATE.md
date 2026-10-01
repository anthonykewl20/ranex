# State

**Updated:** 2026-10-02
**Active slice:** docs/slices/SLICE-103-audit-findings-and-remediation.md

SLICE-104 audit remediation merged to main via PR #227 (4b9206d98);
57 audit issues closed with evidence.

Measured validation so far: C1 pairing 19 passed; focused C1 + contract
769 passed, 0 failed, 8 skipped after the slice/STATE documentation fixes.
CI Ruff: all checks passed. Pyrefly: 0 errors.
Full suite (final commit): 2865 passed, 22 failed, 41 skipped, 25 errors.
32 baseline reds fixed; 1 new red classified host-transient (passed 3/3 isolated reruns).
Manifest ceremony accepted: 2953 tests, 125 expected skips.

Settings PR-0a implemented on branch captain/settings-pr0a (ADR-071).
Adds scoped catalogs, loader, policy digest and `ranex settings show|get`;
no consumers migrated, kernel unchanged. Focused settings/architecture: 73 passed.
Mutation spot-check: 8 failed, 21 passed; restored checks pass.
Ruff passes; Pyrefly reports 0 errors. Suite/manifest results in PR/report.

Next: settings PR-0b (v6 envelope, admission binding and live path),
then PR-0c (platform table and no-literal contract test).
Remediation follow-up: C1 #223, then H1 verification.
