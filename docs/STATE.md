# State

**Updated:** 2026-09-06
**Active slice:** none

Version v0.1.005 follows dogfood fix e99cecf525e3e85c443930213daca50a14708e8a.
Issue #89 / F-033, F-034 repair dogfood harness faults: storage_stress
replays an actual evaluation from mixed journals, and two_arm initializes its
nested repository before applying gold patches so the gold arm can no longer
silently ship the empty stub inside a worktree (a harness false rejection,
caught with the kernel verdict honest on its inputs).

Publication requires the frozen suite on this commit and a real wheel/sdist build.
The release workflow retains the validation logs. Source findings and their
end-to-end receipts remain in tools/dogfood/FINDINGS.md and audits/.
Hosted releases use GITHUB_TOKEN and explicitly dispatch CI on the published tag.
GitHub Releases carry the wheel, sdist and verified SHA256SUMS for that tag.
External services and host capabilities absent on the runner are UNVERIFIED.
