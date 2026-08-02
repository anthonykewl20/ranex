# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** none. The next slice cannot open until its ADR is written.

## Where we stopped

SLICE-004 closed: 298 green, **0 xfail** — the six frozen false-PASS paths are
shut. Ranex now observes a **materialisation of the subject commit**, not the
tree the worker stands in: every blob checked against the object id the tree
carries, the child's environment built from empty, the toolchain pinned to
directories the observed party cannot write.

Verified locally, not assumed: git recomputes an object's hash when it parses a
**tree** and never when it streams a **blob**. `cat-file` served substituted
bytes while `ls-tree` still reported the honest id — that disagreement is the
defect and, compared rather than ignored, the fix.

**Mutation testing found a control nothing tested.** The pinned `git` could be
removed with the suite green: D17 uses a replace ref, which blob verification
refuses whichever `git` answered — one control stood in front of another and hid
it. Now covered by shimming `git status`, which no object id can check.

## Next

1. **Landlock confinement for the bound command.** Needs an ADR first. Same uid
   means absolute paths still reach the governed repo, the operator's home and
   the journal. ABI 8, unprivileged, ~75 rules at ~1.7 ms, inode-bound — so
   assert `st_nlink == 1` or a hard link re-grants read under an allowed path.
2. **Open: should `gate evaluate` verify the chain before appending?** It
   appends to a tampered journal without complaint. Recommended yes, refusing
   with exit 2 — an operational refusal, never exit 1, which means the gate was
   judged unsatisfied. What it does not buy: the chain is tamper-*evident*, not
   tamper-proof — anyone who can write the file can rebuild it. Its own slice.

## Known limits, stated not fixed

- **A hermetic tree has no installed dependencies.** `.venv`/`node_modules` are
  ignored, so Ranex gates only self-contained commands — not this repo's own
  `uv run pytest`. Withdrawn on purpose; digest-bound inputs restore it.
- **A tree carrying a symlink or submodule cannot be observed at all.** Only
  `100644`/`100755` are implemented, everything else fails closed (ADR-005
  s.p. 16). This repo carries neither, so the suite never feels it.
- **Same uid** (Next 1); **`HOME` still inherited by Ranex's own git queries**;
  **vendoring proves bytes were obtained, not where from** (ADR-003 s.p. 13);
  **`evidence.json` is not append-only** (ADR-001 s.p. 27); approver identity
  unauthenticated; this repo cannot yet gate itself.
