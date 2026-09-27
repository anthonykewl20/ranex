# ADR-070 — minimization ladder as the handbook system layer

**Status:** accepted
**Date:** 2026-09-27
**Decision-makers:** repo owner
**Issue:** #112

## Context and Problem Statement

Issue #100 shipped path-scoped handbook injection (ADR-062): two layers,
project over system, digest-bound into the delegate packet. The catalog was
empty. Delegated workers still had no standing craft rule for "build less".

Upstream ponytail (MIT) publishes a minimization ladder. Copying it verbatim
breaks this repository on three points the issue names: rung 5 must mean
already-**approved** dependencies (not merely installed); the testing clause
must be a red-first suite-manifest test (not an invisible `__main__` assert);
and a headless worker must not stall to "ask the user". MAP §17.6 also
refuses lite/full/ultra/off gauges.

## Decision Drivers

- MAP §15.3: vendor prior art with NOTICE; adapt, do not grow runtime deps.
- MAP §17.6: one level, always on — no recalibratable gauge.
- ADR-062: system/project layers already exist; land the ladder as data.
- AGENTS.md: tests written red, then green, in the frozen manifest.

## Prior art

- Vendored: `docs/adr/prior-art/ADR-070/ponytail.md` blob:0af61d583fbd42e8900fce9183d68167eb3d93e6
  — DietrichGebert/ponytail@356918eba965ee1eac64bd3a7f0dd02108350de5
  `.agents/rules/ponytail.md`, MIT (see NOTICE).

## Decision

1. Land the **adapted** ladder text in `governance/handbook.json` as a
   single `**/*` entry — the kernel handbook catalog #100 left empty. For
   foreign subjects the same bytes are installed as the operator system
   layer (`$XDG_CONFIG_HOME/ranex/handbook.json`) so the ladder is always
   on without a per-repo project file.
2. Amendments (binding): rung 5 = already-approved via `deps fetch/approve`;
   testing = new red-first test in the suite manifest; no ask-the-user rule
   (record the question in the outcome); one level always on.
3. Guardrails never simplified away: trust-boundary validation, data-loss
   error handling, security, accessibility, anything explicitly requested.
4. No new runtime dependency. `verdict.py` untouched. Handbook remains
   guidance — never read by `run` / `gate evaluate`.

## Consequences

- Every delegate that resolves the handbook receives the ladder.
- Measured build-size deltas on a seeded subject are receipts, not
  marketing percentages from upstream.
- Operators who want the ladder on foreign repos copy/install the system
  layer; project rules still outrank it per ADR-062.

## Evidence

`tools/dogfood/audits/2026-09-27-minimization-ladder/` via
`tools/dogfood/minimization_ladder_proof.py` on
`fastapi/full-stack-fastapi-template@cd83fc1` (seeded-subject, anti-flake ×3).
