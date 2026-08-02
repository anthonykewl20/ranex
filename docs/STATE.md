# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** `docs/slices/SLICE-004-hermetic-observation.md` — reopened.

## Where we stopped

SLICE-004 was closed on a control that never worked. `_remove_materialisation`
hands `shutil.rmtree` a handler that calls `function(path)`; on Linux rmtree
calls it with `os.open`, which needs a second argument. The `TypeError` is not
`OSError`, so it is never converted, escapes **from a `finally`**, and replaces
the refusal already propagating — defect 2 of this slice, in the code that
closed it. Broken on 3.11, 3.12, 3.13 and 3.14: never a regression.

The test named for it monkeypatches `_remove_materialisation` out, so it never
calls the function, and could not have caught this anyway — the real failure is
a `TypeError` and the stub raises the one type already handled.

**ADR-006 is written and accepted-pending**: Landlock confinement for the bound
command, with `/proc/<ranex>/environ` -> `RANEX_SIGNING_KEY` -> forge-anything
measured, and io_uring verified in C *not* to bypass Landlock.

## Next

1. **Finish the reopened SLICE-004.** Version-independent cleanup, a test that
   calls the real function against a real mode-0 directory, and the new
   criterion: every error-recovery path in `src/ranex/` is executed by a test.
2. Then **SLICE-005, Landlock confinement** — ADR-006 is already written.
3. Then the journal: verify-before-append, no auto-create, and a checkpoint
   committing to log **size**, which is what catches truncation and rollback.

## Known limits, stated not fixed

- **Nothing gates Ranex itself.** `governance/gates.yaml` requires
  `uv run pytest -q`, which a hermetic tree cannot run — so every check on this
  repo is the suite plus review, and this defect passed both. The gates govern
  documents; nothing yet governs whether a test touches its subject.
- **A hermetic tree has no installed dependencies**, so only self-contained
  commands can be gated — in any language, not just Python.
- **A tree carrying a symlink or submodule cannot be observed** (ADR-005 s.p. 16).
- **Same uid** (ADR-006 closes it); **`HOME` inherited by Ranex's own git
  queries**; **`evidence.json` is not append-only** (ADR-001 s.p. 27); approver
  identity unauthenticated; no timeout on the bound command; a background
  process outlives the run.
