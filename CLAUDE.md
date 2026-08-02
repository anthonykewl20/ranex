# Ranex

Deterministic governance for AI agents that build software.

**Thesis:** rules an agent can read are suggestions; rules compiled into code are
constraints. Ranex judges work by evidence and executable checks, never by model
confidence.

## The problem, stated plainly

An AI writing software is a blindfolded dart thrower with a guide shouting
coordinates. Two things go wrong, and they are separate problems:

1. **The thrower is blind.** It cannot perceive whether its own dart landed, so
   it reports success either way.
2. **The guide is bad.** The coordinates were wrong or vague before the throw.

There is a third failure the metaphor exposes, and it is the most common: most
tools let the thrower **paint the bullseye around the dart after it lands**. One
actor writes the code, writes the test, and declares success.

Ranex attacks exactly these, and nothing else:

- The thrower's self-report is **discarded**. Checks are the eyes — read the diff
  on disk, never the agent's summary.
- The coordinates are fixed **before any throw** and approved by whoever owns the
  target.
- The target is drawn before the throw: tests are frozen, read-only to
  implementers, and red-then-green is enforced.
- Three misses stops the game and asks the target's owner. "Cannot hit this" is a
  legal outcome, not a failure to route around.

Tools like Replit, Lovable, and Base44 optimize **the throw** — better model,
better prompt, faster loop. Ranex optimizes **the scoring**.

**Ranex does not improve aim.** Not by one degree. It makes misses visible and
cheap, and hits provable. Never claim more than that — not in docs, not in
program output, not to a user.

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

**No slice without an ADR.** The decision behind a slice is researched and
written to `docs/adr/ADR-NNN-*.md` *before* the slice file is opened. The slice
links it. Enforced, not remembered.

**Research means reading code.** We are not the first here and not the smartest.
A specification says what someone intended; a working implementation says what
survived contact with reality, and mature open source has already solved most of
this. Search code hosts *before designing* — for the whole problem, not only the
component — and record the queries and the tool used. Record at least two mature
candidates you deliberately did not adopt, each with a link and the reason. Then
find the implementation that works, read it, copy what holds, and say what you
deliberately did not copy.

Cite it **pinned** — a 40-hex commit, or a dotted-numeric release tag. Never a
branch: `2.x` and `24-feature` are branches, and a branch starting with a digit
is no more fixed than one starting with a letter.

Then **actually fetch it**: copy the file into `docs/adr/prior-art/ADR-NNN/` —
your own ADR's directory — and record `Vendored: <path> blob:<git hash-object>`.
A citation is a shape an agent can invent; a file with a matching hash is one it
had to obtain. **One distinct source file per citation**, never the `NOTICE.md`:
a review reproduced two citations both vendoring the notice itself, and every
check passed with nothing fetched. Alongside, a `NOTICE.md` naming each copied
file with its **origin** (URL or commit) and its **licence** — a bare filename
records neither, and we are copying into an MIT repo where a GPL file changes
what may be distributed. Also state each citation's **License:** and its
**Weakness:** (adopting a design without its caveats is how you ship
decoration). Two implementations minimum — a floor on rigour, not a reading
quota; research that sprawls has stopped being useful.

Vendoring proves bytes were obtained, **not** that they came from that URL. It
catches citing from memory, which is the failure that happens. Verifying
provenance needs a second fetch of the cited URL, which the offline suite cannot
do — do not describe it as more than it is.

**An ADR citing no working code is an opinion**, and this is enforced, not
remembered. Every ADR enumerates its sad paths; the happy path is the part that
was never in doubt.

## Commands

```
uv run pytest -q                                        # full suite, about a second
uv run mutmut run                                       # required before a slice closes
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
| `README.md` | public project overview and status | updated when public status changes |
| `docs/STATE.md` | where we stopped, what is next | **rewritten** each session |
| `docs/adr/ADR-NNN-*.md` | one researched decision per slice | append-only — supersede, never rewrite |
| `docs/slices/SLICE-NNN-*.md` | the one open slice | at most **one** open |
| `docs/slices/done/` | finished slices | archived, not read by default |

**Do not create any other document.** No session reports, summaries, analyses,
handoffs, plans, notes, retrospectives, or `*-REPORT.md`. The instinct to write
one is exactly what produced the 561 files. Instead:

- Something a future session must know → `docs/STATE.md` (rewrite it, don't append)
- Something about the current work → the slice file
- Something about a change → the commit message
- Everything else → say it in chat and let it go

`STATE.md` is a **pointer, not a log.** It has a fixed shape and stays at most 50
lines forever — the cap the test enforces is `<= 50`, and the file sits at it.
Git already holds the history; do not duplicate it here.

**This file loads into every session, so it is the most expensive real estate in
the repo.** Put here only what prevents an expensive mistake. Evidence, history,
and how a conclusion was reached belong in commit messages — permanent,
greppable, and free at load time. If you are about to add more than a few lines
here, that is the signal it belongs somewhere else.

## Delegating to opencode

```sh
opencode run --print-logs -m opencode/deepseek-v4-flash-free --dir "$PWD" "<prompt>"
```

`--print-logs` is required — without it nothing is emitted when stdout is piped.

**The free tier is burst-throttled: roughly two calls succeed, then it stalls for
minutes.** Use it for spaced review or audit; it cannot sustain an implementation
loop. Six free models exist, so prefer three *different* models voting over one
model asked three times. Score every result against frozen tests, never against
the agent's own report.

Already ruled out as causes of the stall — do not re-derive: prompt length,
`--variant max`, `--auto` (redundant — `build` already allows `*`), and GitHub
issue #13851. Evidence: `git log --grep=opencode-delegation`.

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
