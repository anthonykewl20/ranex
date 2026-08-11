---
name: qa-gate
description: Judges finished work by evidence on disk — fresh suite run, diff review by a non-author, adversarial review for non-trivial decisions. Use when work claims to be done and before anything moves toward main.
---

# QA gate — stage 5 of 6

Pipeline: idea-refine → spec-prd → code-impl → test-debug → **qa-gate** → go-live.

## Overview

The worker's report is discarded; the checks are the eyes. This stage decides
whether work is done, and its verdict comes from commands whose exit codes
decide — never from anyone's summary, including your own.

## When to use

- `test-debug` reports green and the slice claims completion.
- Any non-trivial decision needs an adversarial check before it stands.

When NOT to use: mid-implementation (that is `test-debug`'s loop); trivial
mechanical edits.

## Process

1. **Re-run, never re-tell.** `uv run --frozen pytest -q` fresh, on the exact
   tree being judged. A remembered green or a narrated "tests pass" is not
   evidence. Record which commit the run judged.
2. **Read the diff on disk** — the full range go-live would publish
   (`git log origin/main..HEAD`), tests first, then implementation. The
   verdict names that range; a commit in it no reviewer saw makes the range
   unreviewed. Findings get severities: BLOCKER (wrong, must fix), MAJOR
   (fix before go-live), MINOR (note it). Lead with the one structural
   problem, not ten nits.
3. **No self-approval.** The review verdict comes from someone other than the
   diff's author — a fresh-context agent or an outside model. The author may
   run checks; the author's approval counts for nothing.
4. **Adversarial review for non-trivial decisions.** Hand the reviewer the
   artifact and its contract, **never your conclusion** — handing over your
   reasoning buys validation of your reasoning. Instruct: "find what is
   wrong; do not validate." Classify findings honestly; two review cycles
   with substantive findings and zero accepted is validation theater. Three
   unresolved cycles is information: escalate to the owner.
5. **Mutation input, kernel scope.** Before a kernel-lane slice closes:
   `uv run --frozen mutmut run`. Survivors are review input, never a blocker.
6. **State limits plainly.** Green means these tests passed on this commit —
   the manifest freezes test IDs, not bodies, and declared expected-skips did
   not run. Never report more than the evidence shows; anything unverified is
   reported UNVERIFIED, never PASS.

## Red flags

- Approving a diff you authored.
- A verdict quoting a test run older than the latest commit.
- Findings classified "noise" by the person they inconvenience.
- A review that ends in agreement on the first pass with zero findings.

## Gate

Full suite green on the exact commit, a non-author review verdict naming the
whole `origin/main..HEAD` range with no open BLOCKER/MAJOR, mutation run done
for kernel-scope slice closes. Only then is `go-live` allowed to see the
commit.

---
Adapted from `code-review-and-quality` and `doubt-driven-development` in
addyosmani/agent-skills @7676817c12a1317454ae3898a0c5c1eacf5dd3d5; its
self-review allowance and narrated-verification step deliberately not copied.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
