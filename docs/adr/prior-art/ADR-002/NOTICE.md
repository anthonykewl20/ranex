# Third-party source vendored for ADR-002

These files are copies of upstream implementations, kept so that what ADR-002
claims to have read is on disk and checkable. They are evidence, not
dependencies: nothing imports, executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub reports for that path at that revision —
so these copies agree with upstream, not merely with each other.

- `python-tuf-trusted-metadata-set.py` — MIT OR Apache-2.0 — python-tuf `tuf/ngclient/_internal/trusted_metadata_set.py` at tag v7.0.0, blob `689eef01de665280434e4c3d8ccdc63f4431b67b`, from <https://github.com/theupdateframework/python-tuf/blob/v7.0.0/tuf/ngclient/_internal/trusted_metadata_set.py> — Copyright the TUF contributors.
- `go-tuf-trustedmetadata.go` — Apache-2.0 — go-tuf `metadata/trustedmetadata/trustedmetadata.go` at tag v2.4.2, blob `3ae32781cdf83d84bacdd4276ae868cc7b6ef0ed`, from <https://github.com/theupdateframework/go-tuf/blob/v2.4.2/metadata/trustedmetadata/trustedmetadata.go> — Copyright 2024 The Update Framework Authors.

Both licences are permissive and compatible with this repository's MIT licence,
and both require the copyright notice to travel with the copy — which is what
this file is for.
