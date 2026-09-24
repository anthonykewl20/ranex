# SLICE-088 — deliberate-shortcut markers as deterministic evidence

**Status:** done

Issue #110 (+ Correction 2 on the issue, arm 8). A deliberate simplification
may be taken, but it may not be silent: a cut corner leaves a greppable
`ranex:` marker naming the ceiling it accepts and the trigger that should
revisit it. A tiny stdlib scanner greps the tree and emits SARIF 2.1.0
(#97); trigger-less or malformed markers are `error` findings a gate can
refuse, well-formed ones are `note`. Grep is pure — no model, no network, no
judgment near a verdict. `evaluate()` and `verdict.py` are untouched.

## Shape

- Scanner: `src/ranex/foundation/markers.py`, shipped as the installed
  kernel's own entry points — `ranex markers` (a subcommand; what a governed
  run binds, because the console script carries its shebang and therefore its
  kernel, where a venv `python -m` resolves through the symlink to a bare
  interpreter with no ranex in site-packages) and
  `python -P -m ranex.foundation.markers` for direct operator use. Never an
  in-tree script (Correction 2).
- Marker line protocol: `(#|//) ?ranex:` then `<ceiling>; <trigger>`.
  - no `;` → `ranex/marker-no-trigger` at `error` (upstream's "no-trigger,
    those rot silently")
  - empty ceiling or trigger half → `ranex/marker-malformed` at `error`
  - well-formed → `ranex/marker-shortcut` at `note`
- Like ruff's `--exit-zero`, the scanner exits 0 however many findings it
  reports and decides through its artifact: a bound `accepted` must stay
  reachable through a zero exit.
- A marker whose comment prefix sits inside a quoted span on its line is a
  string literal, not a comment → not a finding (arm 6). Line-level quote
  tracking only; multi-line literals are a recorded boundary.
- Skipped directories: `.git`, `node_modules`, `build`, `dist`, `target`,
  `__pycache__` (upstream's exclusion set, made deterministic). Non-UTF-8
  files are skipped (binary).
- SARIF carries the #97 fingerprint (imported from `scan_results`, so the
  emitted and recomputed IDs agree by construction), an
  `invocations[].executionSuccessful` witness, and an `artifacts[]` witness
  for every scanned file, so a scope path the scanner never saw is `missing`
  and blocks.
- Acceptance lives in the claim's frozen scan manifest `accepted` map
  (already #97's shape); removing a declaration flips the run to FAIL.

## Arm 8 — the scanner is not the tree's to choose

Correction 2 measured a claim bound to a system interpreter plus an in-tree
script being admitted and passing: containment inspected `argv[0]` only, and
the record's command digest matched the catalog that declared the neuter
argv. The binding is authored in the gate catalog, so the catalog is where it
is refused: a `sarif-2.1.0` claim may resolve its scanner from `argv[0]`
(ruff) or an interpreter's own program options (`-m mod`, `-c code`), never
from a script operand — a file whose bytes the loader cannot see, wherever it
lives. `scripted_interpreter_operand` locates that operand with a closed,
per-interpreter option grammar (python's `-m` names a module, not a path;
`-c` code is not a path; operands after the program belong to the program);
the loader refuses what it finds, `run` and `gate evaluate` cannot load such
a catalog at all, and a neuter argv executed under an honest catalog produces
a real, signed, exit-0 record that still cannot satisfy the bound claim —
the digest is the catalog's, not the operator's whim.

The interpreter set is closed and named (python family, pypy, node, ruby,
perl, php, lua, the shells). Suite (JUnit) claims are untouched: a check
script committed with the suite is SLICE-003's separately recorded stance,
not reversed here by accident.

## Proof (#95 protocol)

Real `ranex` subprocesses on the pinned `benjaminp/six` subject, no mocks,
positive+negative controls, 3× repeats, statuses VERIFIED / GAP / FALSE-PASS
/ NON-DETERMINISTIC / UNVERIFIED. Arms 1–8 per the issue. Receipts under
`tools/dogfood/audits/2026-09-23-markers/`.

## Out of scope

Dogfood `--selftest` wiring (#113), handbook injection (#100), this repo's
own landing gate, dependency and CI changes.
