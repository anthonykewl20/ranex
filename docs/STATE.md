# State

**Updated:** 2026-09-06
**Active slice:** none

Version v0.1.004 follows dogfood fix 3deb74459bd62d8475bc73d1b3c69610d0810288.
Issues: #84. Findings: F-030.

Publication requires the frozen suite on this commit and a real wheel/sdist build.
The release workflow retains the validation logs. Source findings and their
end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.
Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published tag.
GitHub Releases carry the wheel, sdist and verified SHA256SUMS for that tag.
External services and host capabilities absent on the runner are UNVERIFIED.
