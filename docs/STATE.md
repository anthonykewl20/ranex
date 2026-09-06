# State

**Updated:** 2026-09-06
**Active slice:** none

Current release: v0.1.002 (9a7b6ca3d84e0b90a2c5d9b2af33c12c00c32337).
Issue #83 / F-029: remove the personal-token prerequisite for dogfood releases.
The owner authorized GitHub's built-in token and the Actions publisher identity.
The release job grants repository contents write, issues read and actions write.
It explicitly dispatches full CI on the verified published tag because built-in
token pushes do not trigger ordinary push workflows. Local owner checks remain.

Real eligible hosted publication and its dispatched CI are pending. A skipped
release job or successful dispatch alone is not release validation. Frozen tests
on the release commit, actual wheel/sdist builds, atomic fast-forward publication
and remote-tip verification remain mandatory. Existing tags stay immutable.
Prior evidence and boundaries: tools/dogfood/FINDINGS.md and audits/.
Live installed-App publication and absent host capabilities remain UNVERIFIED.
