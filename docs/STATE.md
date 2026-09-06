# State

**Updated:** 2026-09-06
**Active slice:** none

Current release: v0.1.004 at 85037d1d901a205298deb1778503bb118ab88000.
Issue #85 / F-031, F-032 repair the frozen suite on a qualified operator
host: the docs cap no longer sweeps gitignored `.local` receipts, and the
cold-start journey follows README plus the linked operator guide. Release CI
stayed green throughout; only the qualified host ran the affected tests.

Publication requires the frozen suite on this commit and a real wheel/sdist
build. The release workflow retains the validation logs. Source findings and
their end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.
Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published
tag. GitHub Releases carry the wheel, sdist and verified SHA256SUMS for that
tag. External services and host capabilities absent on the runner are
UNVERIFIED.
