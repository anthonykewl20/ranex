# Third-party source vendored for ADR-006

Copies of upstream implementations, kept so that what ADR-006 claims to have read
is on disk and checkable. They are evidence, not dependencies: nothing imports,
executes or lints them.

Each was fetched at the pinned revision named below, and its git blob hash was
then compared against the hash GitHub's contents API reports for that path at
that revision — both matched, so these copies agree with upstream and not merely
with each other.

- `go-landlock-restrict.go` — MIT — go-landlock `landlock/restrict.go` at release v0.9.0, blob `34755a18d12ba505bacd1cd8b58fceb629d9c5bf`, from <https://github.com/landlock-lsm/go-landlock/blob/v0.9.0/landlock/restrict.go> — Copyright (c) 2021 Günther Noack, under the MIT License carried at <https://github.com/landlock-lsm/go-landlock/blob/v0.9.0/LICENSE>.
- `py-landlock-landlock.py` — MIT — py-landlock `py_landlock/landlock.py` at release v0.1.1, blob `0a3e98c2cfab07eacdf9cfd4a10a5142a6516f76`, from <https://github.com/SebastienWae/py-landlock/blob/v0.1.1/py_landlock/landlock.py> — Copyright (c) 2026 the py-landlock authors, under the MIT License carried at <https://github.com/SebastienWae/py-landlock/blob/v0.1.1/LICENSE>.

Both are MIT: the same licence this repository carries, requiring only that the
copyright notice and permission notice travel with the copy — which is what this
file is for.

Deliberately absent, and each for a reason worth recording:

- **bubblewrap** (<https://github.com/containers/bubblewrap>, 8.2k stars) is the
  stronger mechanism and is not vendorable: LGPL-2.0-or-later into an MIT
  repository. It is also not adoptable here yet for a second reason — it needs a
  helper binary in the measurement path and unprivileged user namespaces, which
  this host's AppArmor policy denies except through bwrap's own profile
  (`kernel.apparmor_restrict_unprivileged_userns = 1`, and `unshare -U` fails
  while `bwrap` succeeds). Read, discussed in ADR-006, not copied.
- **landrun** (<https://github.com/Zouuup/landrun>, 2.2k stars, MIT) is the most
  adopted implementation of exactly this job and *is* vendorable. It was read and
  not copied because it is a command-line tool: adopting it means an external
  executable decides the boundary, and this repository's pinned-toolchain rule
  would then have to cover a binary that is not part of any base system.
- **in-toto and witness** (<https://github.com/in-toto/in-toto>,
  <https://github.com/in-toto/witness>) were fetched as candidates for the whole
  problem, not merely this slice, and are the reason the search was worth running:
  they already implement Ranex's evidence-and-policy half, maturely and to a
  published standard. They are absent from this directory because they contribute
  no confinement code to cite — `gh api search/code` for `landlock`, `seccomp`,
  `bubblewrap` and `sandbox` returns zero hits in both repositories. A negative
  result that shaped the decision is part of the research, so it is recorded here
  rather than left as something a future session must rediscover.
