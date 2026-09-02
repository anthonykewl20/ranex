---
name: idea-refine
description: Turns a rough product idea into a confirmed intent the owner has explicitly approved, one question at a time. Use when the owner describes a new feature, capability, or change and no ADR or slice exists for it yet. Use before any spec, ADR, or code.
---

# Idea refine

## Overview

Extract what the owner actually wants, not what they think they should want.
The output is a confirmed intent statement **in chat** — nothing is written to
disk at this stage.

## When to use

- The owner describes new work in product terms.
- A request is ambiguous enough that two reasonable readings diverge.

When NOT to use: the intent is already confirmed, or the work is a mechanical
fix with one reading. Never in a non-interactive run — if the owner cannot
answer, stop before this stage, not inside it.

## Process

1. **Hypothesis.** One sentence stating what you believe they want.
2. **One question at a time, with your guess attached.** The owner reacts to a
   wrong guess faster than they generate an answer. Batching three questions is
   a red flag.
3. **Probe want-vs-should-want.** Buzzword answers trigger: *"If you didn't
   have to justify this to anyone, what would you actually want?"*
4. **Restate in the owner's words**: Outcome / Who it serves / Why now / What
   success looks like / **Out of scope**. The out-of-scope line is mandatory.
5. **Gate on an explicit yes.** "Sounds good", "sure", "whatever you think",
   and silence are not yes.

## Gate

The stage ends when the owner has said an explicit yes to the restated intent,
including its out-of-scope line.

---
Adapted from `interview-me` and `idea-refine` in addyosmani/agent-skills
@7676817c12a1317454ae3898a0c5c1eacf5dd3d5, rebuilt for Ranex gating.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
