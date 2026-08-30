# ADR-041 — task authority contract

**Status:** accepted
**Date:** 2026-08-30
**Decision-makers:** repo owner
**Issue:** #62 (composed task flow; observed failure recorded in the #55 audit)

## Context and Problem Statement

`task dispatch` and `task judge` require caller-chosen path flags
(`--journal` required with no default, main.py:3711-3716 and 3718-3736;
`--evidence` required and resolved worktree-relative at main.py:1183-1185),
while `task merge` accepts no path flags at all and hardcodes the governed
root's `governance/journal.sqlite3` (main.py:1368, DEFAULT_JOURNAL at :148)
and `governance/evidence.json` (:1450, DEFAULT_EVIDENCE at :156). The
composed flow therefore needed manual bridging: the e2e test hand-plants
the candidate row into the target journal
(tests/e2e/test_task_real.py:437-440) and re-runs `run` at the target to
grow evidence there (:551-576). Merge refused sad-path-5 until evidence
was manually copied — issue #62's observed failure.

## Decision Drivers

- One vocabulary of authority across dispatch, judge, and merge.
- The composed Ranex-gates-Ranex flow works with zero flags, zero copies.
- `run` remains the only writer of evidence bytes; the kernel never moves them.
- Explicit flags keep working for external-target flows (additive defaults).
- Journal record shapes stay unchanged (they feed hash chains and approvals).
- Refusal vocabulary (sad-path-1..22) keys off content, not paths — unchanged.

## Prior art

Searched: GitHub code search 'git worktree GIT_COMMON_DIR documentation',
'argparse add_argument default optional flag'; consulted docs.python.org
library/argparse (3.14) `default` semantics before choosing evidence.

- https://github.com/git/git/blob/v2.43.0/Documentation/git-worktree.txt —
  the linked-worktree topology this decision derives defaults from: a
  linked worktree's `.git` file points back at the main worktree's
  `$GIT_DIR`, and `$GIT_COMMON_DIR` names it, so the worktree a dispatch
  created resolves to the repository that is the dispatch target.
  License: GPL-2.0 — copyleft documentation, vendored as design evidence
  only; no product code is derived from it, and the NOTICE records the
  licence honestly rather than relabelling it permissive.
  Weakness: the same doc says administrative files for a deleted worktree
  are pruned automatically (`gc.worktreePruneExpire`), so the worktree a
  journal row names can vanish under the record — default resolution must
  refuse, never invent; it also warns against assuming which dir owns a
  path, which this decision answers by deriving, not assuming.
  Vendored: `docs/adr/prior-art/ADR-041/git-2.43.0-git-worktree.txt` blob:a9c636a9c7a8eb51b8f8bac89dcdb53951c371a1

- https://github.com/python/cpython/blob/v3.14.0/Doc/library/argparse.rst —
  the `default` section: the value produced when the option string was not
  present, "for optional arguments … used when the option string was not
  present at the command line" — exactly the required→optional change
  dispatch/judge/merge make, and the same library the CLI is built on.
  License: PSF-2.0, BSD-style Python Software Foundation License Version 2
  (documentation code examples additionally 0-Clause BSD per the v3.14.0
  LICENSE).
  Weakness: it documents that a string `default` is parsed as if it came
  from the command line (type conversion applied) — a hazard for
  path-valued defaults this decision avoids by defaulting to `None` and
  deriving the path in the command; and "required options are generally
  considered bad form" is advice argparse never enforces. The vendored
  copy is the `default`-section excerpt, not the whole 2,287-line file.
  Vendored: `docs/adr/prior-art/ADR-041/cpython-3.14.0-argparse-default.rst` blob:56c0648003f6bbb33a1067437e79e40b0c26207f

- Rejected: https://github.com/git/git — its `builtin/worktree.c` at tag
  v2.43.0 is the C behind `git worktree add`; GPL-2.0 code, and it answers
  how worktrees are built rather than the contract this decision needs
  (which repository a worktree belongs to), which the doc states directly.
- Rejected: https://github.com/pypa/pip — its
  `src/pip/_internal/cli/cmdoptions.py` at tag 25.2 shows mature
  `default=` usage, but the defaults read mutable configuration at parse
  time; this decision's defaults derive from git topology the kernel
  itself established, so the pattern does not transfer.

## Considered Options

1. Defaults everywhere: optional `--journal`/`--evidence` on dispatch,
   judge, and merge, each defaulting from the authority the command
   already holds; explicit flags always win.
2. Judge exports/copies evidence into the governed root so merge keeps
   reading only governed paths.
3. Merge's journal defaults to the dispatch target instead of the
   governed root.
4. Record journal/evidence paths inside journal records.
5. Status quo: required flags plus manual bridging.

## Decision Outcome

Adopt option 1; reject 2-4 (see below); 5 is issue #62's failure.

- **dispatch**: `--journal` becomes OPTIONAL, default
  `<target>/governance/journal.sqlite3`, resolved within the target
  (dispatch holds `--target`).
- **judge**: `--journal` OPTIONAL, default derived from
  `--emitted-worktree`'s git common dir → `<common-dir>/governance/journal.sqlite3`
  (the worktree's main repo is the dispatch target); `--evidence`
  OPTIONAL, default `governance/evidence.json` resolved within the
  worktree (existing `resolve_within_repository` semantics, main.py:1183).
- **merge**: gains OPTIONAL `--journal` (default governed `DEFAULT_JOURNAL`, unchanged) and OPTIONAL `--evidence`. Default evidence: when the governed journal carries a `task-dispatch` row for the task, resolve `governance/evidence.json` within the row's recorded `worktree` (task.py:28) — the kernel reads it, never copies it; with no dispatch row (legacy hand-planted candidates), fall back to governed `DEFAULT_EVIDENCE`. Explicit `--evidence` always wins.
- **The kernel never moves evidence bytes**; `run` stays evidence's only
  writer. Record shapes in task.py are unchanged — no journal or evidence
  path is added to any record.

### Consequences

- The composed no-flag flow (Ranex-gates-Ranex, target == governed root)
  runs dispatch → run → judge → merge and publishes with zero copies and
  zero path flags.
- External-target flows work by passing explicit `--journal` (and
  `--evidence` where the layout differs).
- Every existing test keeps passing: required→optional is additive
  (explicit paths still accepted), and merge's legacy fallback preserves
  the hand-planted-row tests (tests/integration/test_task_merge.py:92-93).
- All five sad-path families keyed on journal/evidence CONTENT —
  sad-path-5, 11, 12, 14 among them (main.py:1428-1453) — are unchanged;
  no refusal keys off a path.

### Confirmation

Verified on 2026-08-30: six integration contracts in
`tests/integration/test_task_authority_contract.py` pin default resolution,
explicit overrides, legacy governed-root fallback, and deleted-worktree
sad-path-5 refusal. Issue #62's executed evidence run demonstrates the
no-flag composed flow — dispatch → real `run` → judge → merge →
`PUBLISHED` — with zero artifact movement and both refusal paths captured.
The full suite was green: 1537 tests passed.

## Improvements on the prior art

- git documents the worktree↔common-dir topology but leaves path choices
  to the caller; this decision closes the loop by making the topology
  itself the default authority, so the caller cannot name a different
  repository than the one dispatch recorded.
- git prunes stale worktree metadata silently; here a vanished worktree
  is a refusal in the established vocabulary, never a silent fallback to
  stale governed evidence.
- argparse's `default` is a static value parsed like a command-line
  string; these defaults are `None` plus in-command derivation, so no
  path is type-converted or frozen at parser-build time, and explicit
  flags win by construction (a passed value is never overwritten by a
  default — the documented namespace behaviour the vendored section
  shows).

## Architecture surface

- `src/ranex/cli/main.py` — `build_parser()` task group: three flags
  move required→optional with defaults; `cmd_task_dispatch`,
  `cmd_task_judge`, `cmd_task_merge` gain default resolution (target,
  common-dir, dispatch-row respectively).
- `src/ranex/governed_execution/domain/task.py` — untouched; record
  shapes unchanged.

## Scope and threat delta

- No new authority: defaults resolve to paths the kernel itself
  established (dispatch's target, the worktree's common dir, the row the
  kernel journaled); explicit flags cannot widen containment
  (`resolve_within_repository` still applies).
- Threat model unchanged: no evidence bytes move, no signature covers a
  copy, no record hash changes. Merge remains a governed-root operation
  (update-ref, blob-OID equality at the tip, main.py:1397-1414).

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | the journal's own dispatch row names the worktree evidence is read from |
| Compatibility | required→optional is additive; explicit paths behave identically |
| Consistency | one authority vocabulary across dispatch, judge, merge |
| Simplicity | the composed flow needs zero flags and zero copies |
| Reversibility | restore `required=True`; the defaults disappear |
| Testability | no-flag e2e plus unmodified explicit-path suites |

## Reversibility

Door: two-way

Re-pin `required=True` on the three flags and delete the default
resolution branches; explicit-flag behaviour never changed, no record,
journal, or golden depends on the defaults existing.

## Sad paths

- Dispatch and judge defaults derive from different roots (target vs
  worktree common dir) and drift: both come from the same git topology —
  dispatch creates the worktree from the target, so the common dir IS
  the target; a mismatch means the worktree was not ours, and the
  candidate row will not be found (sad-path-11).
- The worktree is deleted before merge: default-evidence resolution
  fails and merge refuses with the established
  sad-path-5 satisfying-evidence-missing vocabulary — it never invents
  evidence and never silently falls back.
- Explicit `--evidence` points outside the candidate worktree:
  `resolve_within_repository` containment (main.py:1183) still refuses.
- Two dispatches into two journals: merge reads one journal; the other's
  rows are simply absent — candidate-row-missing (sad-path-11), not a
  path error.
- Legacy governed-root evidence shadows worktree evidence when both
  exist: dispatch-row precedence is deterministic — row present means
  worktree evidence wins; no row means the governed default.
- `--journal` on merge points at a non-task journal: candidate-row
  lookup misses and sad-path-11 refuses, unchanged.
- argparse default churn breaks in-process callers passing explicit
  kwargs: defaults are additive; a passed value is never overwritten by
  a default (the vendored `default` section documents exactly this
  namespace behaviour).
- Evidence is rewritten by `run` after judge read it (post-judge tamper):
  merge re-admits signatures and re-checks the subject digest, so
  staleness still refuses — defaulting the path changed nothing about
  the content checks.

## Test strategy

- `tests/integration/test_task_authority_contract.py` — six integration
  contracts pin defaults, explicit overrides, legacy fallback, and the
  deleted-worktree sad-path-5 refusal.
- Issue #62's executed evidence run is the end-to-end proof: no-flag
  dispatch → real `run` → judge → merge → `PUBLISHED`, with zero artifact
  movement and both refusal paths captured. It is evidence, not a new arm
  in `tests/e2e/test_task_real.py`.
- `tests/contract/test_docs_discipline.py` — governs this ADR itself
  (budgets, citations, vendored digests, NOTICE).
- Full suite: `uv run --frozen pytest -q` — 1537 tests passed.

## Code review checklist

- [ ] `build_parser()` task group: `--journal` (dispatch, judge) and
      `--journal`/`--evidence` (merge) optional with documented defaults.
- [ ] No default is a static path string passed through argparse typing;
      resolution happens in the command from the kernel's own anchors.
- [ ] `task.py` diff is empty; no record carries a journal or evidence path.
- [ ] Merge's dispatch-row precedence: row present → worktree evidence;
      absent → governed `DEFAULT_EVIDENCE`; explicit `--evidence` wins.
- [ ] Deleted-worktree refusal proven in the sad-path-5 vocabulary.
- [ ] `tests/integration/test_task_merge.py` and existing e2e arms: diffs
      empty, suites green.
- [ ] Full suite (`uv run --frozen pytest -q`) green on the exact commit.

## More Information

- Issue #62 — this decision; the #55 audit's observed sad-path-5 failure.
- `docs/adr/ADR-012-the-kernel-merges.md` — merge as a governed-root
  operation; `docs/adr/ADR-003-research-is-fetched-evidence.md` — vendored
  evidence discipline.
- `src/ranex/cli/main.py:148,156,1183-1185,1368,1428-1453,3711-3747` —
  constants, resolution, refusals, parser shapes.
- `docs/adr/prior-art/ADR-041/NOTICE.md` — provenance, licences, and the
  excerpt disclosure for the vendored evidence.
