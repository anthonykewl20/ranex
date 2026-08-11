---
name: code-impl
description: Implements an open slice inside its scope, in the right lane, without touching frozen tests. Use when an ADR and open slice exist and tests are frozen red. Use for any mutation of product code.
---

# Code implementation — stage 3 of 6

Pipeline: idea-refine → spec-prd → **code-impl** → test-debug → qa-gate → go-live.

## Overview

Implementation happens only inside an open slice, only in one lane, only under
frozen tests. The diff on disk is the deliverable; narrated progress counts
for nothing.

## When to use

- An open slice names the work and its ADR; its tests exist and are red.

When NOT to use: no slice is open (go back to `spec-prd`); the change is a
docs/governance edit; you are tempted to "quickly fix" something outside the
slice's scope.

## Process

1. **Take the lane.** Kernel → this repo; harness → `../ranex-harness`. One
   mutation writer per repo at a time; every delegated agent gets its own
   worktree. Never edit a tree a running harness is using — it auto-commits
   on idle.
2. **Red first.** Confirm the slice's tests fail against the pre-change tree.
   A test that passes before the code exists is a circle painted around a
   dart — stop and raise it.
3. **Slice vertically, riskiest first.** Each increment is one complete
   behavior, leaves the tree compiling, and is independently revertable. The
   part most likely to sink the design gets built first, so a miss is cheap.
4. **Scope discipline.** Touch only what the slice requires. Adjacent problems
   go in a `NOTICED, NOT TOUCHING:` note in chat — never a drive-by fix, never
   a new document.
5. **Frozen tests are read-only.** If a frozen test seems wrong, stop and
   raise it — changing it is a decision for the test's owner, not the
   implementer. Never weaken a test, auth, validation, or security control to
   make work pass.
6. **Commit in coherent units** with messages that carry the reasoning — the
   commit message is this repo's only legal place for history.

## Red flags

- "While I was in there…" — scope creep is how one writer becomes two.
- Editing anything under `tests/` that the slice froze.
- Working in a tree another writer (agent or harness) is using.
- Implementing against the agent's summary of the spec instead of the ADR
  itself.

## Gate

The slice's own frozen tests go green (`test-debug` owns getting there), the
diff stays inside the slice's scope, and nothing outside the slice changed.
The evidence is the diff and the test run — on disk, not in a report.

---
Adapted from `incremental-implementation` and `planning-and-task-breakdown` in
addyosmani/agent-skills @7676817c12a1317454ae3898a0c5c1eacf5dd3d5;
self-verification replaced by frozen-test gates and lane rules.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
