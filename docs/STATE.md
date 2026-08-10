# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-10
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — qualify strict-local host/build/launcher; single open slice.

## Where we stopped

ADR-006 confinement is the active chain: SLICE-017 qualifies host/launcher, then
SLICE-018 owns lifecycle and SLICE-019 alone wires `cmd_run`. Two of ADR-015's
five durability claims are in production (harness tip `9eeda0bf5d21`): provider
watchdog, and reconciler hoist with startup sweep. Durable retry, blockers and
Session-ID fencing remain, parked behind P0.

**The UI redesign is a separate track.** ADR-018 (`proposed`) decides the harness
front door; BOARD-01..BOARD-22 live on the harness repo under milestone "TUI
redesign — the board is the front door", design record in `specs/tui-redesign/`.
They are **not slices**: they neither consume the open slice nor queue behind P0.

## Decisions

- The board replaces opencode's chat landing, added as a new route plus
  feature-plugin slots, never a rewrite of `routes/session`. `packages/tui` is
  ~163 insertions from fork base `012c2f57`; a rewrite would end mergeability.
- Verdict content must not vary with TTY; only styling may. Enforced by
  `tests/contract/test_verdict_presentation.py`. Python 3.14 argparse colours
  `--help` on a terminal — accepted, because help is not evidence.
- Seven causes of an unsatisfied claim exist and are **unordered**. `Evaluation`
  exposes them only as prose in `reason`; renderers must never parse it — that
  defect reopened SLICE-002. BOARD-02 adds a structured field and is the one
  board package touching the kernel, so it needs its own slice.
- The reconcile sweep ships DB-global and is **unsafe under concurrent
  processes**. Accepted because one daemon runs (ADR-014); fencing must gate it
  on a durable owner claim. Recorded in `reconcile.ts`.
- Read-only research/review fanout is allowed; `task fanout` is prototype-only.
  SLICE-044 alone authorizes production mutation. Until then, one writer.

## Next

1. Close SLICE-017 / issue #10; it qualifies only and cannot accept ADR-006.
2. Then SLICE-018 (issue #21), then SLICE-019 (issue #22); only 019 binds
   `cmd_run`, accepts ADR-006 and closes RISK-06.
3. On the UI track, alongside: accept or reject ADR-018, then BOARD-03 (degraded
   rendering) or BOARD-01 (data contract) — the only two with no prerequisites.

## Known limits

- A provider that connects and never sends a first chunk is bounded only by the
  absolute budget — up to 30 minutes. The fix is a third first-chunk budget.
