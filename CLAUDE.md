# Ranex

Deterministic governance for AI agents that build software.

**Thesis:** rules an agent can read are suggestions; rules compiled into code are
constraints. Ranex judges work by evidence and executable checks, never by model
confidence.

---

## Read these first, every session

1. `docs/STATE.md` — where we stopped and what is next. Single source of truth.
2. The active slice named there, in `docs/slices/`. That is the only thing to
   work on.

## The working rule

**One slice at a time. Finish it before starting anything else.**

"Finished" means every done-criterion in the slice file is met and a test proves
it. If you believe something else is more urgent, say so and stop — do not start
it. Opening a second slice is the failure mode this rule exists to prevent.

Slices are small on purpose. If one cannot be finished in a session, it is too
big — split it rather than carrying it.

## Commands

```
uv run pytest -q                                        # currently 41 tests, ~0.4s
PYTHONPATH=src uv run python -m ranex.cli.main --help
```

`pyproject.toml` sets `[tool.uv] package = false`, so the `ranex` console script
is **not** installed. Always invoke through the module path above. `uv run ranex`
will fail.

## Docs discipline — enforced by `tests/contract/test_docs_discipline.py`

This project previously accumulated 561 architecture files and zero product
code. The docs layer is deliberately capped so that cannot happen again.

**These are the only documents that may exist:**

| Path | Purpose | Lifecycle |
|---|---|---|
| `CLAUDE.md` | this file — orientation and rules | edited rarely |
| `docs/STATE.md` | where we stopped, what is next | **rewritten** each session |
| `docs/slices/SLICE-NNN-*.md` | the one open slice | at most **one** open |
| `docs/slices/done/` | finished slices | archived, not read by default |

**Do not create any other document.** No session reports, summaries, analyses,
handoffs, plans, notes, retrospectives, or `*-REPORT.md`. The instinct to write
one is exactly what produced the 561 files. Instead:

- Something a future session must know → `docs/STATE.md` (rewrite it, don't append)
- Something about the current work → the slice file
- Something about a change → the commit message
- Everything else → say it in chat and let it go

`STATE.md` is a **pointer, not a log.** It has a fixed shape and stays under 50
lines forever. Git already holds the history; do not duplicate it here.

## Invariants

Breaking one of these is a bug, not a tradeoff. If a change requires breaking
one, stop and raise it.

- **The kernel is code.** No model decides what happens next. `evaluate()` is a
  pure function of (gate, evidence, subject, approver).
- **Absence blocks.** A required claim with no satisfying evidence is FAIL —
  never a default, never a skip.
- **Evidence is bound to a subject digest.** The same command run against a
  different tree proves nothing about this one.
- **No self-approval.** Whoever produced the evidence cannot approve it.
- **A gate that cannot block is refused at construction.** A non-blocking gate is
  decoration.
- **The journal is append-only and hash-chained.** Nothing rewrites it.
- **Removing every model credential from the machine must not change a verdict.**

## Decisions already made — do not relitigate

- Ranex is a **control plane**, not an agent harness. It never implements an
  agent loop.
- The worker is **Claude Code** (Agent SDK / headless), because Max plan
  entitlement is bound to that harness. Workers stay behind a port and are
  replaceable.
- **Ranex never trusts worker output.** It reads the diff on disk and runs
  checks. The agent's own summary is discarded.
- **The kernel merges; workers never do.** One git worktree per task.
- Intake produces a **flow graph the non-technical user approves**. Chain is
  graph → paths → scenarios → contract tests → gates. The approved graph is the
  root of trust.
- Tests are **frozen before BUILD and read-only to implementers**; red-then-green
  is enforced.
- "Deterministic" describes the **process and the verdict**, never the generated
  code. Never claim otherwise in docs or output.
- Hermes is **not** a base. Removed 2026-08-01. Do not reintroduce it.
- License is MIT. Monetization will come from private features layered on top,
  not from restricting the kernel.

## Repo shape

```
src/ranex/
  foundation/          canonical JSON + digests
  governed_execution/  verdict.py (the kernel) + sqlite journal
  policy/              gate catalog loading
  cli/                 operator entry point + path confinement
  bootstrap/           composition root — the only place concretes are wired
governance/            gates.yaml, evidence.json, journal.sqlite3 (gitignored)
docs/                  STATE.md + slices/
```
