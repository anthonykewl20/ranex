# State

**Updated:** 2026-09-06
**Active slice:** none

Version v0.1.005 follows dogfood fix e99cecf525e3e85c443930213daca50a14708e8a.
Issues: #85. Findings: F-031, F-032.

Publication requires the frozen suite on this commit and a real wheel/sdist build.
The release workflow retains the validation logs. Source findings and their
end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.
Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published tag.
GitHub Releases carry the wheel, sdist and verified SHA256SUMS for that tag.
External services and host capabilities absent on the runner are UNVERIFIED.
