---
name: idea-refine
description: Turns a rough product idea into a confirmed intent the owner has explicitly approved, one question at a time. Use when the owner describes a new feature, capability, or change and no ADR or slice exists for it yet. Use before any spec, ADR, or code.
---

# Idea refine — stage 1 of 6

Pipeline: **idea-refine** → spec-prd → code-impl → test-debug → qa-gate → go-live.

## Overview

Extract what the owner actually wants, not what they think they should want.
The output is a confirmed intent statement **in chat** — nothing is written to
disk at this stage. `spec-prd` compiles the confirmed intent into an ADR.

## When to use

- The owner describes new work in product terms.
- A request is ambiguous enough that two reasonable readings diverge.

When NOT to use: the intent is already confirmed, or the work is a mechanical
fix with one reading. Never in a non-interactive run — if the owner cannot
answer, stop before this stage, not inside it.

## Process

1. **Hypothesis.** One sentence stating what you believe they want.
2. **One question at a time, with your guess attached.** The owner reacts to a
   wrong guess faster than they generate an answer, and the guess exposes your
   assumptions. Batching three questions is a red flag. The owner is
   non-technical: ask product questions only; decide technical questions
   yourself and say what you decided.
3. **Probe want-vs-should-want.** Buzzword answers ("scalable", "clean")
   trigger: *"If you didn't have to justify this to anyone, what would you
   actually want?"*
4. **Restate in the owner's words**: Outcome / Who it serves / Why now / What
   success looks like / **Out of scope**. The out-of-scope line is mandatory —
   half of misalignment is silent disagreement about what is not being built.
5. **Gate on an explicit yes.** "Sounds good", "sure", "whatever you think",
   and silence are not yes. Each gets a follow-up naming the specific thing
   you need confirmed.

## Red flags

- You asked three questions in one message.
- You are interviewing about implementation choices the owner cannot judge.
- Several rounds without convergence — something foundational is missing; say
  so instead of asking round four.
- You wrote a file. This stage produces chat, never documents
  (`tests/contract/test_docs_discipline.py` refuses new documents anyway).

## Gate

The stage ends when the owner has said an explicit yes to the restated intent,
including its out-of-scope line. That confirmed intent is the input `spec-prd`
starts from.

---
Adapted from `interview-me` and `idea-refine` in addyosmani/agent-skills
@7676817c12a1317454ae3898a0c5c1eacf5dd3d5, rebuilt for Ranex gating.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
