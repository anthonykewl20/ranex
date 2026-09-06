# State

**Updated:** 2026-09-06
**Active slice:** none

Version v0.1.003 follows dogfood fix ae9e3e3d6de7e2ef9bb83024cf5d041bb2c9c3c4.
Issues: #83. Findings: F-029.

Publication requires the frozen suite on this commit and a real wheel/sdist build.
The release workflow retains the validation logs. Source findings and their
end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.
Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published tag.
External services and host capabilities absent on the runner are UNVERIFIED.
