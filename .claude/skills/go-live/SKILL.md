---
name: go-live
description: Pushes the exact QA-judged commit to main automatically when the gate is green. Use when qa-gate has passed on the current commit. Red blocks the push; there is no override and no human trigger.
---

# Go live — stage 6 of 6

Pipeline: idea-refine → spec-prd → code-impl → test-debug → qa-gate → **go-live**.

## Overview

A green QA gate — not a human — triggers the push to main (owner decision,
2026-08-11). This is session automation under that standing authorization,
scoped to exactly the conditions below. It is **not** governed publication: no
kernel verdict, no signed evidence, no approval record. `ranex task merge`
remains the only governed path, and a push never closes a slice.

## When to use

- `qa-gate` just passed on the commit at HEAD.

When NOT to use: anything is red; the tree is dirty; qa-gate ran on an older
commit; the repo is mid-rebase or mid-merge.

## Process — every step checked, in order; any failure stops with the output

1. **Identity.** `gh auth status` shows **anthonykewl20** active (TonyGarces
   breaks pushes silently), and `git remote get-url origin` names the repo you
   intend to publish.
2. **Bind the subject.** Working tree clean — all work already committed.
   `SUBJECT=$(git rev-parse HEAD)`. Everything below refers to this digest;
   nothing may be committed after it.
3. **No divergence.** `git fetch origin`, then `git merge-base --is-ancestor
   origin/main $SUBJECT` must hold. If main moved: **stop and report** — a
   diverged main means a second writer, which is a rule breach to surface.
   Never merge it in, never rebase onto it, never force.
4. **The range is reviewed.** The push publishes every commit in
   `origin/main..$SUBJECT`, so the qa-gate verdict must name exactly that
   range. A commit in it the reviewer never saw — another writer's, or one
   landed after the review — stops the push; re-run qa-gate on the full
   range first.
5. **The gate, on the subject.** `uv run --frozen pytest -q` — fresh, full,
   green. Then confirm `git rev-parse HEAD` still equals `$SUBJECT` and the
   tree is still clean; a moved HEAD or a dirtied tree voids the run.
6. **Push the digest, fast-forward only.**
   `git push origin $SUBJECT:refs/heads/main` — never `--force`.
7. **Verify the remote.** `git ls-remote origin refs/heads/main` equals
   `$SUBJECT`. On a network error or timeout the outcome is *ambiguous*:
   re-check the remote tip before concluding anything, and never retry the
   push until the tip has been read. Report the verified tip either way.

## Red flags

- Any commit created between the gate run and the push.
- A publish range containing commits the QA verdict never named.
- A push retried after a timeout without reading the remote tip first.
- "It was green earlier" — the gate binds to `$SUBJECT`, not to memory.
- Reporting the push as governed, approved, or kernel-judged. It is none of
  those; say what it is.

## Gate

`refs/heads/main` on the remote equals the commit the full suite passed on,
verified by reading the remote tip — or the push did not happen and the reason
is reported with its output. Both are correct outcomes.

---
Adapted from `shipping-and-launch` and `git-workflow-and-versioning` in
addyosmani/agent-skills @7676817c12a1317454ae3898a0c5c1eacf5dd3d5; the
human ship decision replaced by a digest-bound automatic gate per owner policy.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
