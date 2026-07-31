# Ranex

**Deterministic governance for AI agents that build software.**

> Rules an agent can read are suggestions. Rules compiled into code are
> constraints.

Ranex judges work by evidence and executable checks, never by model confidence.
Removing every model credential from the machine must not change a single
verdict.

---

## The problem

An AI writing software is a blindfolded dart thrower with a guide shouting
coordinates. Two things go wrong, and they are separate problems:

1. **The thrower is blind.** It cannot perceive whether its own dart landed, so
   it reports success either way.
2. **The guide is bad.** The coordinates were wrong or vague before the throw.

There is a third failure, and it is the most common: most tools let the thrower
**paint the bullseye around the dart after it lands**. One actor writes the code,
writes the test, and declares success. That is why "all tests pass" from an AI
means so little.

## What Ranex does — and does not

Ranex attacks exactly those three:

- The thrower's self-report is **discarded**. Checks are the eyes: read the diff
  on disk, never the agent's summary.
- The coordinates are fixed **before any throw** and approved by whoever owns the
  target.
- The target is drawn before the throw. Tests are frozen, read-only to
  implementers, and red-then-green is enforced.
- Three misses stops the game and asks the target's owner. *"Cannot hit this"* is
  a legal outcome.

Tools like Replit, Lovable, and Base44 optimize **the throw** — better model,
better prompt, faster loop. Ranex optimizes **the scoring**.

**Ranex does not improve aim.** Not by one degree. It makes misses visible and
cheap, and hits provable. Nothing here claims more than that.

## Status

**Pre-release. This is not a usable product yet.** It is a kernel with a working
verdict path and very little else.

**Works today**

- `evaluate()` — a pure function of (gate, evidence, subject, approver). Same
  inputs, same verdict, always.
- **Subject-bound evidence** — the same command run against a different tree
  proves nothing about this one. Stale evidence stops counting automatically.
- **Absence blocks** — a required claim with no satisfying evidence is FAIL,
  never a default and never a skip.
- **No self-approval** — whoever produced the evidence cannot approve it.
- **Append-only hash-chained journal** — SQLite triggers plus a chain, so an
  out-of-band edit is detectable rather than merely discouraged.
- `ranex gate evaluate` and repository path confinement.

**Known gaps — stated plainly**

- **Nothing produces evidence.** `governance/evidence.json` is hand-written. The
  loop is open at both ends. *(SLICE-001)*
- **Evidence is unsigned.** A PASS can be forged with a text editor. Subject
  binding stops *stale* evidence; nothing yet stops *fabricated* evidence.
  *(SLICE-002)*
- **The journal append races** under concurrent writers — two appenders can read
  the same previous link and fork the chain. *(SLICE-003)*
- No worker dispatch, no flow graph, no scenario compilation, no budget or
  escalation. Those are designed, not built.

## Current work

<!-- Kept in sync with docs/STATE.md by tests/contract/test_docs_discipline.py -->

**Active slice:** `SLICE-001-evidence-production` — `ranex run` executes a
command, observes it, and emits evidence the gate will accept.

## Completed slices

_None yet._

## The intended chain

```
idea → flow graph → covering paths → scenarios → contract tests → gates → verdict
        ^                                                                    |
        |                                                                    v
   human approves                                                   evidence + journal
```

Everything from *flow graph* rightward is deterministic: the same graph yields
the same paths, the same scenarios, and the same verdict. The generated code is
never deterministic and is never claimed to be.

## Running it

```sh
uv run pytest -q

PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD \
    --approver reviewer_alice
```

`pyproject.toml` sets `[tool.uv] package = false`, so the `ranex` console script
is **not** installed. Invoke through the module path above.

## Development

One slice at a time; finish it before starting another. The rule is enforced by
a test, not left as a convention.

- `CLAUDE.md` — invariants, settled decisions, working rules
- `docs/STATE.md` — where work stopped and what is next
- `docs/slices/` — the one open slice

## License

MIT © 2026 Anthony Garces
