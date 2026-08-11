---
name: spec-prd
description: Compiles a confirmed intent into the researched ADR and slice file this repo's contract tests enforce. Use when intent is confirmed and no ADR exists for it yet, or when opening a slice. Use before any implementation.
---

# Spec / PRD — stage 2 of 6

Pipeline: idea-refine → **spec-prd** → code-impl → test-debug → qa-gate → go-live.

## Overview

The spec unit of this repo is the ADR; the work unit is the slice. Both have
compiled shapes — `tests/contract/test_docs_discipline.py` is the authority,
and this skill is a walkthrough of what it enforces, so you satisfy it by
construction instead of by failure.

## When to use

- A confirmed intent exists (from `idea-refine`) and needs its decision
  researched and recorded.
- A slice is being opened (requires the ADR to exist first).

When NOT to use: the work is a docs/governance edit (those go by owner-directed
commit), or an ADR already covers the decision.

## Process

1. **Search before designing.** Code hosts, the whole problem, not only the
   component. Keep the queries — the ADR records them.
2. **Read the working implementations.** ≥2 mature candidates adopted-from,
   ≥2 deliberately rejected. A spec says what someone intended; working code
   says what survived.
3. **Write the ADR** to `docs/adr/ADR-NNN-*.md` with every enforced element:
   - all sections, canonical order, within per-section line budgets (≤300
     lines total); `**Status:** proposed`; `Door: one-way|two-way`.
   - Prior art: ≥2 citations **pinned** to a 40-hex commit or dotted-numeric
     tag (never a branch); per citation `License:`, `Weakness:`, and
     `Vendored: docs/adr/prior-art/ADR-NNN/<file> blob:<git hash-object>` —
     nothing after the blob hash on that line, one distinct source file per
     citation, never a NOTICE.
   - `Searched:` lines and ≥2 `Rejected:` entries, each with a code-host URL
     plus ≥30 characters of reasoning.
   - `NOTICE.md` beside the vendored files: each file's origin (URL/commit)
     and licence.
   - ≥8 sad paths; a test strategy naming real `tests/` paths.
4. **Panel it.** Two independent fresh-context adversarial reviews before the
   ADR is accepted (see `qa-gate` for the review contract). Consensus first,
   then acceptance.
5. **Open the slice** in `docs/slices/SLICE-NNN-*.md`: `**Status:** open`, a
   link to the ADR, and done-criteria each provable by a named test. At most
   one open slice per repo — if one is open, finish it first.
6. **Freeze the target.** The slice's done-criteria tests are written now —
   before any implementation — and committed red in their own commit, so
   red-then-green is provable from git history, not memory. From that commit
   they are read-only to the implementer. Where a second author is available
   (a delegated agent, another session), the implementer does not write them.
7. **Choose the lane.** Kernel work → this repo. Harness work →
   `../ranex-harness`. A cross-lane contract change starts kernel-side, always.

## Red flags

- Citing from memory: a URL you never fetched, a plausible SHA. Vendoring
  exists because this happens; the test compares real blob hashes.
- An ADR whose sad paths are variations of one failure.
- Writing the slice before the ADR, or a second open slice.

## Gate

`uv run --frozen pytest -q tests/contract/test_docs_discipline.py` green, the
panel's divergences reconciled, and the slice's tests committed red. Then —
and only then — `code-impl`.

---
Adapted from `spec-driven-development` and `documentation-and-adrs` in
addyosmani/agent-skills @7676817c12a1317454ae3898a0c5c1eacf5dd3d5;
self-ticked checklists replaced by this repo's compiled docs gates.
Copyright (c) 2025 Addy Osmani; MIT licensed — the copyright and
permission notice travels with the shelf: .claude/skills/LICENSE-agent-skills.txt
