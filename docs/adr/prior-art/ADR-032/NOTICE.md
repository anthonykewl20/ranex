# Vendored prior art for ADR-032

Copied verbatim for review. No file here is imported, executed, adapted, or
relicenced as Ranex product code; these files are evidence that the cited
implementations were read.

| File | Origin | Licence |
|---|---|---|
| `git-test-lib.sh` | <https://raw.githubusercontent.com/git/git/v2.45.2/t/test-lib.sh> (tag `v2.45.2`, commit `79d3e0e7d9b32dd2938e635dc94acc6b49000569` is this file's blob, verified against git/git's blob store) | **GPL-2.0** (git `COPYING` at `v2.45.2`: "the only valid version of the GPL ... is _this_ particular version (v2)") |
| `git-test-lib-functions.sh` | <https://raw.githubusercontent.com/git/git/v2.45.2/t/test-lib-functions.sh> (tag `v2.45.2`, blob `862d80c9748c7f9d6234c6b47d68ed7854f3de03`) | **GPL-2.0** (same `COPYING`) |
| `postgres-pg_regress.c` | <https://raw.githubusercontent.com/postgres/postgres/REL_16_2/src/test/regress/pg_regress.c> (lightweight tag `REL_16_2` = commit `b78fa8547d02fc72ace679fb4d5289dccdbfc781`, fetched at that ref; blob `57aa0de3b7adf6a41f8423cbcfd86a4bedeb3fd8`) | **PostgreSQL Licence** — permissive, BSD-style (SPDX: PostgreSQL; repo `COPYRIGHT` at `REL_16_2`) |
| `curl-sws.c` | <https://raw.githubusercontent.com/curl/curl/curl-8_8_0/tests/server/sws.c> (annotated tag `curl-8_8_0` dereferenced to commit `fd567d4f06857f4fc8e2f64ea727b1318f76ad33`, fetched at that ref; blob `53add587d6c8b44d47140d1c3a0bc3db37f29564`) | **curl licence** — MIT-style derivative (SPDX: curl; repo `COPYING` at `curl-8_8_0`) |
| `moby-requirement.go` | <https://raw.githubusercontent.com/moby/moby/v26.1.4/integration/internal/requirement/requirement.go> (tag `v26.1.4`, blob `0e4ee0c4cd6303810caa02dafc6986ab0ecc172b`) | **Apache-2.0** (repo `LICENSE` at `v26.1.4`) |
| `coveragepy-control.py` | <https://raw.githubusercontent.com/nedbat/coveragepy/7.6.1/coverage/control.py> (tag `7.6.1`, blob `ca757e9e133b02b8010f7229b817662672b14eba`) | **Apache-2.0** (repo `LICENSE.txt` at `7.6.1`) |

**GPL WARNING:** the two `git` files remain GPL-2.0. They are pattern
evidence only — no code from them enters `src/` (ADR-012 precedent for
vendored git sources, ADR-031 for the t/ suite specifically). They are not
covered by Ranex's MIT licence and must not be copied, adapted, linked, or
incorporated into MIT product code without a separate licensing review. They
are retained here solely as unexecuted research evidence.

The PostgreSQL and curl files are permissive-licensed but are likewise
vendored as read evidence only, not as code to adapt; the Apache-2.0 files
likewise carry this notice rather than their full licence text — their
licence texts are available at the origin URLs above.

Vendoring proves these bytes were obtained; it does not prove they came from
the stated URLs. Confirming provenance requires a second, independent fetch
of each cited URL, which the offline suite cannot perform. During this
session each file's git blob hash was additionally confirmed to exist in the
cited repository's own blob store at that hash, which is consistency, not
provenance.
