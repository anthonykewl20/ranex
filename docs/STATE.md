# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-03
**Phase:** kernel — evidence loop
**Active slice:** none. ADR-006 is written; SLICE-005 opens against it.

## Where we stopped

SLICE-004 was reopened and closed again. It had been closed on a cleanup control
broken on every supported Python, covered by a test that monkeypatched out the
function it was named for, and on a mutation check run by hand by the actor who
wrote the code. Measuring the general form found **59 refusals no test executed**.

Now enforced by tools, not habit: `diff-cover` fails any change adding a line no
test runs, and `mutmut` replaces the hand-run claim. 15 of the 59 closed. The
journal's concurrent-append corruption — honest races forging tamper evidence —
is fixed with `BEGIN IMMEDIATE`.

**Not a clean bill of health, and the numbers are in the slice:** 44 refusals
still unreached, and 880 surviving mutants. `verdict.py`'s 47 matter most —
inverting `item.exit_code == 0` in the kernel's contradiction check survives, so
no test detects the kernel's success comparison being flipped.

## Next

1. **SLICE-005 — Landlock confinement.** ADR-006 written. Closes the measured
   forge-anything path: the bound command reads `/proc/<ranex>/environ`, gets
   `RANEX_SIGNING_KEY`, reads the key, and signs any verdict.
2. **ADR-007 then the journal.** Verify before append, never auto-create, and a
   checkpoint committing to log **size** — Trillian and Rekor both do this, and
   size is what catches truncation and rollback. Sources cached via `opensrc`.
3. **Make Ranex gate itself.** `gates.yaml` demands a command a hermetic tree
   cannot run, so nothing gates this repo. That is why the defect got through.
4. Then: kernel mutation survivors; in-toto export (decided — keep our kernel,
   emit their format, never let their advisory command check reach a verdict);
   the remaining 44; ADR-000's template, which now teaches a failing format.

## Known limits, stated not fixed

- **Same uid** — worst open hole, ADR-006 closes it. **No timeout on the bound
  command**, and a background process outlives the run (ADR-006 s.p. 12, 13).
- **A hermetic tree has no installed dependencies**, so only self-contained
  commands can be gated — in every language, not just Python.
- **`mutmut` says nothing about `cli/main.py`**: its selection excludes the e2e
  tests that exercise it. A green run there is not evidence.
- `evidence.json` is not append-only; approver identity unauthenticated; `HOME`
  still inherited by Ranex's own git queries; symlink/submodule trees unobservable.
