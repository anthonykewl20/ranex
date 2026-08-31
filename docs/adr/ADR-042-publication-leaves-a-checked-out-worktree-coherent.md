# ADR-042 — publication leaves a checked-out worktree coherent

**Status:** accepted
**Date:** 2026-08-31
**Decision-makers:** repo owner
**Issue:** #56 (checked-out-worktree coherence; production failure recorded in the #55 audit)

## Context and Problem Statement

`task merge` publishes a candidate by moving the target ref with a compare-and-swap (`git update-ref TARGET CANDIDATE OBSERVED-TIP`, main.py:1738). Issue #56 recorded a production failure where the target branch was checked out in a worktree: the CAS succeeded, the command printed `PUBLISHED`, and the checked-out worktree stayed stale — `git status` in that checkout showed `D production_published_candidate_4.txt`, a file the governed ref no longer had but the working tree still did.

A ref that says one commit while a checked-out tree shows another is exactly the gap the kernel exists to close, and it opened during publication itself.

The problem: what must `task merge` do, and refuse to do, when its target branch is checked out, so that `PUBLISHED` is never printed over a stale or conflicted worktree, and a crash mid-publication never hides that fact.

## Decision Drivers

- Never print `PUBLISHED` when the checked-out worktree does not match the published ref.
- Never destroy uncommitted operator work in the checked-out worktree.
- Preserve the no-overwrite guarantee `git merge --ff-only` already gives, without silently discarding ignored files git would overwrite.
- Recovery after a crash must stay honest: no `PUBLISHED` after the fact, journal must state the real state.
- Keep the fix inside the existing CAS+journal architecture (ADR-012), not a new subsystem.

## Prior art

Searched: git merge and git status documentation (v2.43.0) for the semantics of uncommitted changes across a fast-forward and what status does and does not report; GitHub code search for an existing checkout-coherence library before writing bespoke dirty-scan/repair code.

- https://github.com/git/git/blob/v2.43.0/Documentation/git-merge.txt —
  grounds: PRE-MERGE CHECKS (local uncommitted changes overlap refusal),
  the FAST-FORWARD MERGE section, and `--overwrite-ignore` ("Silently
  overwrite ignored files from the merge result. This is the default
  behavior.") — the exact hazard the dirty scan exists to refuse.
  License: GPL-2.0 — copyleft documentation vendored as design evidence
  only; no product code is derived from it, recorded honestly rather
  than relabelled.
  Weakness: the same page documents that merge stops only for changes
  it may need to update, and silently overwrites ignored files by
  default — it protects the merge operation, not the uncommitted intent
  of the operator, and says nothing about a branch advanced underneath
  a linked worktree.
  Vendored: `docs/adr/prior-art/ADR-042/git-2.43.0-git-merge.txt` blob:e8ab34031919fa4d2ac920e1cd706c77c7c65138

- https://github.com/git/git/blob/v2.43.0/Documentation/git-status.txt —
  grounds: `--untracked-files=all` ("Also shows individual files in
  untracked directories"), the porcelain `-z` rename field order
  (post-image then pre-image), and "Ignored files are not listed unless
  `--ignored` is used" — the three facts the dirty scan is built on.
  License: GPL-2.0 — copyleft documentation vendored as design evidence
  only; same honesty terms as the entry above.
  Weakness: it documents that status reports what the index knows, so
  skip-worktree/assume-unchanged bits make modified files invisible —
  the documented residual this ADR carries rather than fixes.
  Vendored: `docs/adr/prior-art/ADR-042/git-2.43.0-git-status.txt` blob:10fecc51a75d4783c68565d25302c50480d626ce

- Rejected: https://github.com/libgit2/libgit2 — mature C checkout/merge APIs, but the kernel already executes a pinned git CLI toolchain; linking a library for one coherence guarantee adds a build dependency and duplicates semantics the pin already provides.
- Rejected: https://github.com/jj-vcs/jj — colocated repos keep a working-copy commit synced automatically, but adopting a different VCS model is out of proportion: kernel subjects, digests, and approvals bind git tree OIDs.

## Considered Options

1. Status quo — CAS moves the ref, worktree untouched. This is the issue #56 failure itself.
2. Refuse to publish whenever the target branch is checked out, clean or not. Refuses the common clean-checkout case for no protective gain.
3. Refuse only when checked-out worktree dirty state intersects the candidate diff; otherwise synchronize the worktree after the CAS. Chosen.
4. Best-effort background sync detached from the merge command, `git worktree repair`-style. Not durable, races the operator, gives the journal no honest vocabulary for "still syncing".

## Decision Outcome

Chosen option 3: refuse before the ref moves when checked-out worktree dirty state intersects the candidate diff; otherwise synchronize the worktree after the CAS.
Dirty state comes from `_worktree_dirty_paths` (main.py:1345-1400): `git status --porcelain -z --untracked-files=all` (untracked directories not collapsed), rename/copy records counted at both post-image and pre-image paths, plus a targeted `git ls-files --others --ignored --exclude-standard -z -- CANDIDATE-PATHS` query, because `git merge --ff-only` silently overwrites ignored files in its way (`--overwrite-ignore` is the documented default) — documented residual: files marked skip-worktree/assume-unchanged are reported clean by git even when modified on disk, so the scan misses them.
Intersecting dirty state refuses via `_worktree_conflict_reason` (main.py:1421-1428) before the CAS runs: `sad-path-23 worktree-conflict` naming up to three paths plus a `", ... (+N more)"` suffix.
Clean, or dirty only in paths disjoint from the candidate diff: the CAS moves the ref, then the worktree is synchronized in order (main.py:1747-1767) — `checkout --detach OBSERVED-TIP`, `merge --ff-only CANDIDATE`, `symbolic-ref HEAD TARGET-REF`.
The detach step exists because the CAS changes the symbolic branch before git updates the checkout's index and files; a direct post-CAS merge would resolve HEAD-through-branch to the candidate already and report "Already up to date" without touching the worktree.
`PUBLISHED` prints only after synchronization succeeds (main.py:1795-1803, 1826); sync failure and crash recovery are covered under Sad paths.

### Consequences

- Accepted tradeoff: intersecting dirty state refuses publication even though `git merge --ff-only` could in principle have preserved some of it — the no-destructive-overwrite guarantee wins over permissiveness.
- Disjoint dirty state (uncommitted operator changes untouched by the candidate diff) is preserved across the CAS and the sync, so publication does not require an empty worktree.
- A sync failure after the CAS is never silent: it is journaled as ABORTED with the exact repair command, and `PUBLISHED` is never printed for that outcome.
- The skip-worktree/assume-unchanged residual is accepted, not fixed: a rare configuration an operator would need to have deliberately set on the target checkout.
- Every checked-out-target merge now costs one extra `git diff`, one extra `git status`, and (on success) three extra git subprocess calls versus the prior unchecked path.

### Confirmation

`tests/integration/test_task_merge_worktree_coherence.py` pins the full postcondition: HEAD, index, target ref, and working tree all at the candidate after a clean or disjoint-dirty publish; `git status --porcelain` empty apart from preserved disjoint operator changes.
The same suite pins refusal on intersecting dirty state (ref does not move, `sad-path-23 worktree-conflict` reason, worktree untouched — including rename pre-image, untracked-at-candidate-path, and ignored-at-candidate-path cases) and pins the ABORTED-plus-repair-command outcome on a forced post-CAS sync failure.
`tests/integration/test_journal.py` pins the recovery arms: INFERRED with the stale-worktree fact and repair appended, INFERRED with the detail unchanged when the worktree is coherent, and INFERRED degrading to the ref-only detail when worktree inspection fails.
Issue #56's closing evidence reports the full suite at 1579 tests with 157 expected skips.
Honesty caveat: the recovery stale-worktree arm is pinned via an injected-state
test; through real git states that branch is currently hard to reach (an
on-branch stale HEAD reads coherent, and the post-detach window is invisible
to branch matching). Recovery never fabricates `PUBLISHED`, but live detection
of the mid-sync crash window is thin and tracked as a follow-up issue.

## Improvements on the prior art

- git-merge.txt's PRE-MERGE CHECKS refuse a merge for "changes it may need to update" but say nothing about a ref moved by a separate CAS call underneath a linked worktree — this decision closes that gap by treating the checked-out worktree as a first-class postcondition of `task merge`.
- git-merge.txt documents `--overwrite-ignore` as the default; this decision adds a pre-flight ignored-file check scoped to the candidate's changed paths so a checked-out worktree's ignored files are never silently clobbered by the eventual `merge --ff-only`.
- git-status.txt documents the format but offers no dirty-set API; the scan reads both NUL-terminated fields of each rename/copy record and intersects the whole set with the candidate diff, so a rename touching either name still counts.
- Where prior art stops at "the merge refused" or "the status is clean/dirty", this decision adds honest states the git plumbing has no vocabulary for: ABORTED-after-CAS, journaled with the operator-runnable repair command, and INFERRED-after-crash with the same repair appended.
- The residual (skip-worktree/assume-unchanged invisibility) is inherited unfixed from git-status.txt's own documented behavior; this decision is explicit that it is a known gap, not a silent one.

## Architecture surface

- New: `_worktree_dirty_paths`, `_worktree_conflict_reason`, `_worktree_sync_repair` (main.py:1345-1428) and the post-CAS sync block (main.py:1747-1767) inside `cmd_task_merge`.
- Changed: `_recover_task_merges` (main.py:1431-1498) gains the stale-worktree detail branch on the existing INFERRED/ABORTED resolution path.
- No new module, no new CLI flag, no new journal field — the repair command and stale-worktree fact ride the existing free-text `detail` of `TaskMergeOutcome`.
- Consumes the pinned git CLI toolchain only; no new dependency.

## Scope and threat delta

- In scope: the target branch is checked out in a worktree of the repository the kernel is operating in.
- Out of scope: bare-repo targets with no checkout — `_checked_out_target_worktree` returns None and the prior unchecked path runs unchanged.
- Threat delta: none adversarial — a coherence fix for the operator's own checkout; no new credential, network call, or privilege.
- No concurrent writer to the checked-out worktree is assumed; the CAS still guards the ref itself.

## Quality attributes

| Attribute | Effect |
|---|---|
| Safety | no destructive overwrite of intersecting dirty state; refuses instead |
| Honesty | `PUBLISHED` only after full sync; ABORTED/INFERRED name the exact repair |
| Availability | disjoint dirty state publishes instead of blocking; the operator's changes ride through |
| Cost | +1 diff, +1 status, +up to 3 git subprocesses per checked-out-target merge |
| Residual risk | skip-worktree/assume-unchanged files remain undetected |

## Reversibility

Door: two-way

Reverting the sync block restores the pre-#56 behavior (CAS-only, no worktree touch); no schema or ref format changed, so no migration is needed either direction.
The added `detail` text in `TaskMergeOutcome` is additive and free-text; older journal entries without it remain valid, and no reader depends on its absence.
A revert would need `tests/integration/test_task_merge_worktree_coherence.py` deleted or relaxed, which is itself the signal that #56 has reopened.

## Sad paths

- Target branch checked out, clean worktree, candidate publishes — worktree synchronized, `PUBLISHED` printed, no residual dirt.
- Target branch checked out, dirty state disjoint from the candidate diff — synchronized and preserved; publication proceeds.
- Target branch checked out, dirty state intersects the candidate diff — refuses before the CAS with `sad-path-23 worktree-conflict`, naming up to three paths plus `", ... (+N more)"`; ref never moves.
- Ignored file at a path the candidate changes — the pre-flight ignored-file check counts it as dirty even though plain `git status` would not show it, because `merge --ff-only` would silently overwrite it.
- Rename/copy in the working tree touching a candidate path via its pre-image name only — still counted dirty because the scan reads both NUL-terminated fields of the rename record.
- Untracked file inside an untracked directory at a candidate path — still counted, because the scan forces `--untracked-files=all` rather than the default directory-collapsing behavior.
- File hidden by skip-worktree/assume-unchanged and modified on disk at a candidate path — NOT detected (documented residual); publication can proceed and the sync's `merge --ff-only` may then fail or silently diverge from that file.
- CAS succeeds, `checkout --detach` or `merge --ff-only` or `symbolic-ref` fails mid-sync — journaled ABORTED with `ref moved to CANDIDATE but worktree PATH sync failed: GIT-ERROR; repair with REPAIR`; `REPAIR` is the shlex-quoted three-command chain from `_worktree_sync_repair`; stderr gets `ERROR`, nonzero exit, `PUBLISHED` never printed.
- Process crashes between the CAS and the end of sync — `_recover_task_merges` resolves the unmatched intent by inspecting the target ref: candidate landed means INFERRED, else ABORTED; if the checked-out worktree's HEAD is stale, the journaled detail gets `worktree PATH is stale at HEAD; repair with REPAIR` appended; `PUBLISHED` is never printed by recovery.
- Recovery's own inspection raises OSError/ToolchainError/UnicodeDecodeError/ValueError — swallowed, so recovery still returns its ref-only outcome instead of crashing; the stale-worktree detail is simply not appended that run.
- Operator retries `task merge` after an ABORTED sync failure instead of running the printed repair — refused as `sad-path-9 tip-mismatch`, because the retry's expected-old ref no longer matches the already-moved target; the repair command is the only supported path back to a synced worktree.
- The repair command itself is run against a worktree an operator has since made dirty again — `merge --ff-only` in the repair refuses exactly like any other non-fast-forward merge would, rather than overwriting the new changes.

## Test strategy

`tests/integration/test_task_merge_worktree_coherence.py` is the primary contract: clean-checkout publish, disjoint-dirty publish, intersecting-dirty refusal (plain, rename pre-image, untracked-at-path, ignored-at-path), ignored-disjoint publish, unchecked-out target, sync-failure ABORTED+repair with the retry refusing as sad-path-9, each against a real git worktree.
`tests/integration/test_journal.py` pins the recovery arms: INFERRED with stale-worktree detail and repair text, coherent-worktree detail unchanged, and inspection-failure degradation to the ref-only detail.
`tests/contract/test_docs_discipline.py` governs this ADR itself (budgets, citations, vendored digests, NOTICE).
`governance/suite_manifest.json` freezes the test IDs and allowed skip reasons touched by this work.

## Code review checklist

- [ ] `_checked_out_target_worktree` identifies the worktree for the exact target ref, not a same-named branch elsewhere.
- [ ] Dirty scan and candidate diff both compute against the same OBSERVED/CANDIDATE pair the CAS itself uses — no window for a third commit to land between them.
- [ ] Refusal path performs zero git mutation — the target ref is byte-identical before and after a refused attempt.
- [ ] Sync block's three-command order is never reordered — reordering reintroduces the "Already up to date" hazard the detach avoids.
- [ ] Every repair string is copy-pasteable and shlex-quoted, including against paths containing spaces.
- [ ] `PUBLISHED` never appears on stdout on any path that does not reach the end of the sync block.
- [ ] Is recovery's swallowed-exception branch exercised for each of the four caught exception types, not just asserted by reading the code?

## More Information

- `docs/adr/ADR-012-the-kernel-merges.md` — the CAS publication model this decision extends; `docs/adr/ADR-041-task-authority-contract.md` — the kernel-anchored journal/evidence defaults the composed dispatch → judge → merge flow relies on.
- Issue #56 is the production failure this decision closes; the #55 audit is where it was first recorded.
- Implementing history: c433360f7 (original worktree-coherence work), 541134538, 593a1cb5c, plus further hardening uncommitted on disk at the time of writing.
- Vendored prior art and licensing: `docs/adr/prior-art/ADR-042/NOTICE.md`.
