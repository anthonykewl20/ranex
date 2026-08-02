# Third-party source vendored for ADR-005

Copies of upstream implementations, kept so that what ADR-005 claims to have read
is on disk and checkable. They are evidence, not dependencies: nothing imports,
executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub's contents API reports for that path at
that revision — both matched, so these copies agree with upstream and not merely
with each other.

- `bazel-SymlinkedSandboxedSpawn.java` — Apache-2.0 — Bazel `src/main/java/com/google/devtools/build/lib/sandbox/SymlinkedSandboxedSpawn.java` at commit c8217fdd2f20e4a061122c0af0417380d09e9480 (release 8.0.0), blob `770f3caf7197575ce49f6308d6efc0c9b100030f`, from <https://github.com/bazelbuild/bazel/blob/c8217fdd2f20e4a061122c0af0417380d09e9480/src/main/java/com/google/devtools/build/lib/sandbox/SymlinkedSandboxedSpawn.java> — Copyright 2016 The Bazel Authors, under the Apache License 2.0 carried in the file header.
- `containerd-content-writer.go` — Apache-2.0 — containerd `content/local/writer.go` at commit 88bf19b2105c8b17560993bee28a01ddc2f97182 (release v1.7.24), blob `0cd8f2d04bbd9e3d2bfbac1973d25a9ccaafba5f`, from <https://github.com/containerd/containerd/blob/88bf19b2105c8b17560993bee28a01ddc2f97182/content/local/writer.go> — Copyright The containerd Authors, under the Apache License 2.0 carried in the file header.

Both are Apache-2.0: permissive, compatible with this repository's MIT licence,
and requiring the copyright notice and licence attribution to travel with the
copy — which is what this file is for.

Deliberately absent, and each for a reason worth recording:

- **git's own `checkout-index` and `archive`** materialise a tree far better than
  anything written here will. git is GPL-2.0-only, so it is read and discussed in
  ADR-005 and not vendored — the same call ADR-004 made about `local_repo_env`.
- **bubblewrap and systemd's `nspawn`** are the mature unprivileged-sandbox
  implementations. Both are copyleft (LGPL-2.0-or-later and LGPL-2.1-or-later),
  so neither is vendorable here.
- **JGit's `UnpackedObject.java`** was fetched and read as a candidate for the
  object-verification citation and then dropped, because reading it refuted the
  reason for citing it: it raises `CorruptObjectException` for a bad header, a
  negative size, trailing garbage and a short inflate, and it never recomputes
  the object id. It inherits the same weakness as git's C implementation rather
  than fixing it, so containerd's content store is cited instead. Recorded here
  because a negative result that changed the decision is part of the research.
