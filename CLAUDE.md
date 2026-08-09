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

`docs/MAP.md` is the map — problem, thesis, parts, risks. Read it when the
question is *why* or *what should exist at all*. **Not** every session: it is long,
and `STATE.md` stays the entry point.

## The working rule

**One slice at a time. Finish it before starting anything else.**

"Finished" means every done-criterion in the slice file is met and a test proves
it. If you believe something else is more urgent, say so and stop — do not start
it. Opening a second slice is the failure mode this rule exists to prevent.

Slices are small on purpose. If one cannot be finished in a session, it is too
big — split it rather than carrying it.

Parallelism has two different rules:

- **Read-only fanout is allowed now.** Bounded research and independent review
  jobs may run concurrently when they cannot change repository files/refs or
  external state, receive no secret, and return only evidence or advice for the
  supervisor to verify. Their reports never authorize implementation.
- **Mutation fanout is not authorized yet.** The existing `task fanout` is a
  convenience/prototype over free-prompt JSONL, not a capability boundary.
  Until SLICE-044's real concurrent attack exit passes, keep one open slice and
  one mutation writer. SLICE-036 may qualify mutation only in disposable child
  worktrees with every publication path blocked.

After that exit, parallel jobs are children of one approved batch inside the
open slice, not extra slices. The batch binds the approved parent/C digest and
base digest, a dependency-ready task set, pairwise-disjoint exact path+action
scopes, isolated worktrees, frozen per-child tests/evidence, and an approved
maximum pool. Each child receives only parent ∩ request; it receives no secret,
approval, integration, merge, or publication power. A retry keeps the same
scope and tests; widening means a new approval. Results are reported in
canonical task/attempt order regardless of finish order. One key-exclusive
integrator consumes accepted children in that order and the kernel alone
publishes by stale-base CAS.

The planned governed shape is:
`PYTHONPATH=src uv run --frozen python -m ranex.cli.main task fanout
--spec-packet A.json --artifact-manifest B.json --approval-envelope C.json
--tasks child-requests.jsonl --target <repo> --journal <external>
--outcome-dir <dir> --pool N`. B/C, not caller flags, own harness, model,
timeout, and suite. Child rows reference approved `scope_id` and
`capability_request_id`, never a free-form prompt as an oracle. `--pool` may
only narrow the signed maximum. This grammar is planned, not present today.

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
uv run --frozen pytest -q                               # full suite, about five minutes
uv run --frozen mutmut run                              # before close: kernel scope only (see
                                                        # [tool.mutmut]); survivors are review
                                                        # input, never a blocker; keep mutants/
PYTHONPATH=src uv run python -m ranex.cli.main --help
```

**Always `--frozen`.** Plain `uv run` re-locks and rewrites `uv.lock` — measured:
it silently dropped the `[options]` epoch block, after which `ranex deps fetch`
refused the lock against its own clean derivation. The committed lock is a trust
root here, not a cache.

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
| `docs/MAP.md` | the map — problem, thesis, parts, risks | revised when evidence changes a claim |
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

## Delegating to an outside model

Use the OpenRouter MCP (`mcp__openrouter__send-message`) with a concrete model
slug — `~`-prefixed aliases are rejected for chat. It has no file access: inline
every fact the model needs, and set `timeout_ms` explicitly. Score every result
against frozen tests, never against the model's own report.

The opencode CLI is **not** the delegation path — its free tier stalls after
roughly two calls. Ruled-out causes and evidence:
`git log --grep=opencode-delegation`. Do not re-derive.

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

- Ranex builds **its own harness**: a trimmed fork of opencode (MIT), molded so
  every workflow step calls the kernel. Decided 2026-08-03, overturning the
  control-plane doctrine. The wall stands: harness and kernel are separate
  processes — hooks collect, the kernel judges; the loop is confined from the
  keys and the journal.
- Delegation is foreman → department supervisors → workers, written clean-room.
  Orchestration patterns are learned from oh-my-openagent; its code is SUL-1.0
  and never enters this tree, converted or not.
- **Ranex never trusts worker output — including its own loop's.** It reads the
  diff on disk and runs checks. The agent's own summary is discarded.
- **The kernel merges; the harness never does.** One git worktree per task.
- Intake produces a **flow graph the non-technical user approves**. Chain is
  graph → paths → scenarios → contract tests → gates. The approved graph is the
  root of trust.
- Tests are **frozen before BUILD and read-only to implementers**; red-then-green
  is enforced.
- "Deterministic" describes the **process and the verdict**, never the generated
  code. Never claim otherwise in docs or output.
- Hermes is **not** a base; removed 2026-08-01 after an audit measured zero
  contribution. It and OpenClaw are feature quarry under the adoption rule,
  never a base.
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
