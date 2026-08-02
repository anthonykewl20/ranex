# Third-party source vendored for ADR-003

These files are copies of upstream implementations, kept so that what ADR-003
claims to have read is on disk and checkable. They are evidence, not
dependencies: nothing imports, executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub reports for that path at that revision —
so these copies agree with upstream, not merely with each other.

- `pip-hashes.py` — MIT — pip `src/pip/_internal/utils/hashes.py` at release 24.2, blob `535e94fca0cc8b049673ee0d02dba259c68af76c`, from <https://github.com/pypa/pip/blob/24.2/src/pip/_internal/utils/hashes.py> — Copyright (c) 2008-present The pip developers.
- `go-modfetch-fetch.go` — BSD-3-Clause — Go `src/cmd/go/internal/modfetch/fetch.go` at commit 6885bad7dd86880be6929c02085e5c7a67ff2887 (release go1.23.0), blob `ad4eb8ecd25b483a79264624fa58a5471c14cd61`, from <https://github.com/golang/go/blob/6885bad7dd86880be6929c02085e5c7a67ff2887/src/cmd/go/internal/modfetch/fetch.go> — Copyright (c) 2009 The Go Authors. All rights reserved.

Both licences are permissive and compatible with this repository's MIT licence,
and both require the copyright notice to travel with the copy — which is what
this file is for.
