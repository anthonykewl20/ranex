# State

**Updated:** 2026-09-06
**Active slice:** none

Current release: v0.1.003 at 82cacd162adf022644ce3316783491153ac0bcf6.
Issue #84 / F-030 repairs missing GitHub Release pages and the public README.
The existing v0.1.003 page is published and Latest; wheel/sdist/checksum asset
hashes match the verified fresh-clone build. Its original tag has not moved.

Automatic release now creates a matching Release page with verified assets and
change notes after the existing frozen-test/build/tag/dispatch sequence.
The README is shortened to a public introduction, real quickstart, core usage
and current architecture; detailed recipes live in docs/OPERATIONS.md.
Frozen developer entrypoint and completed-slice contracts remain enforced.
The generated dogfood snapshot is preserved and explicitly dated.

Hosted automatic publication, dispatched tag CI, fresh-clone quickstart and
public asset download checks for this change are pending. Existing real
built-in-token publication was verified in issue #83; no personal secret exists.
Evidence and remaining trust/host boundaries: tools/dogfood/FINDINGS.md.
