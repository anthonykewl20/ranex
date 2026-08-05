# Vendored prior art for ADR-012

Copied verbatim for review. No file here is imported, executed, adapted, or
relicensed as Ranex product code; these files are evidence that the cited
implementations were read.

| File | Origin | Licence |
|---|---|---|
| `prow-tide.go` | <https://raw.githubusercontent.com/kubernetes-sigs/prow/7f8580d8da573bcb9e4fe716358d4c0ee1d24b38/pkg/tide/tide.go> | Apache-2.0 |
| `gerrit-merge-op.java` | <https://raw.githubusercontent.com/GerritCodeReview/gerrit/017823543c322cd1b3500bdc91d8b5a62baf5caf/java/com/google/gerrit/server/submit/MergeOp.java> | Apache-2.0 |
| `zuul-merger.py` | <https://raw.githubusercontent.com/openstack-infra/zuul/dc9347c1223e3c7eb0399889d03c5de9e854a836/zuul/merger/merger.py> (`3.8.0`) | Apache-2.0 |
| `git-merge-tree.c` | <https://raw.githubusercontent.com/git/git/c44beea485f0f2feaf460e2ac87fdd5608d63cf0/builtin/merge-tree.c> (`v2.51.0`) | **GPL-2.0-only** |
| `git-refs-files-backend.c` | <https://raw.githubusercontent.com/git/git/c44beea485f0f2feaf460e2ac87fdd5608d63cf0/refs/files-backend.c> (`v2.51.0`) | **GPL-2.0-only** |
| `in-toto-verifylib.py` | <https://raw.githubusercontent.com/in-toto/in-toto/c82fe5d21aaa61c7f1a213db20a46f10bb3f411a/in_toto/verifylib.py> (`3.1.0`) | Apache-2.0 |

**GPL WARNING:** `git-merge-tree.c` and `git-refs-files-backend.c` remain
GPL-2.0-only. They are not covered by Ranex's MIT licence and must not be copied,
adapted, linked, or incorporated into MIT product code without a separate
licensing review. They are retained here solely as unexecuted research evidence.

The Apache-2.0 files remain under Apache-2.0 and retain their upstream
attribution and notice obligations. Nothing in this directory is relicensed by
the repository's MIT licence.

Leitir exact-pin materialisation was attempted for Prow, Gerrit, Git, and Zuul,
but the configured corpus is read-only in this session. The exact in-toto 3.1.0
tree was already present in Leitir and supplied `in-toto-verifylib.py`. The
other five files were fetched from the immutable 40-hex raw URLs above. An
opensrc fallback attempt for Git also failed because its cache is read-only; in
any case opensrc fetches the default branch rather than the cited pin.

Vendoring proves these bytes were obtained; it does not prove they came from
the stated URLs. Confirming provenance requires a second, independent fetch of
each cited URL, which the offline suite cannot perform.
