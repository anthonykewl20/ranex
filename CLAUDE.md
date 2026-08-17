# Ranex

Deterministic governance for AI agents that build software.

**Thesis:** rules an agent can read are suggestions; rules compiled into code are
constraints. Ranex judges work by evidence and executable checks, never by model
confidence.

## The problem, stated plainly

An AI writing software is a blindfolded dart thrower with a guide shouting
coordinates. Three failures, and they are separate problems:

1. **The thrower is blind.** It cannot see whether its own dart landed, so it
   reports success either way. Ranex discards the self-report and reads the
   diff on disk.
2. **The guide is bad.** The coordinates were wrong or vague before the throw.
   Ranex fixes them first, approved by whoever owns the target.
3. **The bullseye moves.** Most tools let the thrower paint the target around
   the dart after it lands — one actor writes the code, writes the test, and
   declares success. Ranex freezes tests before the throw, read-only to
   implementers, red-then-green enforced.

Three misses stops the game and asks the target's owner. "Cannot hit this" is a
legal outcome, not a failure to route around.

**Ranex does not improve aim.** Not by one degree. It makes misses visible and
cheap, and hits provable. Never claim more than that — not in docs, not in
program output, not to a user.

## Read these first, every session

1. `docs/STATE.md` — where we stopped and what is next. Single source of truth
   for the kernel lane.
2. The active slice named there, in `docs/slices/`.

`docs/MAP.md` is the map — problem, thesis, parts, risks. Read it when the
question is *why* or *what should exist at all*, not every session.

## Two lanes — parallel by construction

Work runs in two lanes that may progress **in parallel**, because their trees
and refs are disjoint:

- **Kernel lane** — this repo. Python: the judge. Verdicts, evidence, journal,
  provisioning, CLI. State: `docs/STATE.md`.
- **Harness lane** — `../ranex-harness`
  (github.com/anthonykewl20/ranex-harness), out of tree on purpose.
  TypeScript: the trimmed opencode fork, the loop, the TUI/board, the bridge.
  State: its own repo — `specs/`, the BOARD issues, milestone #1.

Lane rules:

- **One mutation writer per repo at a time**; every delegated agent gets its
  own worktree (two writers in one tree has destroyed finished work). A
  running harness is itself a writer — it auto-commits its tree on idle — so
  never edit or gate a tree a harness process is using.
- **Within one repo nothing changes:** one open slice, finished before another
  opens. Read-only research/review fanout is allowed anywhere; mutation fanout
  stays unauthorized until SLICE-044's concurrent-attack exit passes.
  (SLICE-036/044 are planned IDs from ADR-017 — no slice files exist yet. The
  planned governed fanout grammar is recorded in README and ADR-017.)
- **The cross-lane contract serializes.** The bridge emission and the verdict
  read channel (ADR-019) are owned by kernel ADRs; the harness consumes them.
  A contract change lands kernel-side first — ADR, implementation, contract
  tests — and only then does the harness lane consume it. Parallel lanes are
  for non-contract work.
- Lane separation is a process rule, **not a security boundary**. The harness
  runs unsandboxed as this uid (ADR-019 sad path 12; RISK-06).

## The pipeline

Every unit of work moves through six stages. One skill per stage lives in
`.claude/skills/`; the set is enumerated in
`tests/contract/test_docs_discipline.py`, so adding or renaming one is a
deliberate contract-test edit.

`idea-refine → spec-prd → code-impl → test-debug → qa-gate → go-live`

| Stage | What ends it |
|---|---|
| IDEA REFINE | the owner's explicit yes to a stated intent with an out-of-scope line |
| SPEC PRD | ADR + slice written, the slice's tests committed red and frozen; docs suite green |
| CODE IMPL | the diff on disk does what the slice says, inside its scope |
| TEST DEBUG | red-then-green proven; three misses stops and asks the owner |
| QA GATE | full frozen suite green on the exact commit; non-author review of the whole publish range |
| GO LIVE | the tested commit is on `main`, remote tip verified |

**GO LIVE is automatic** (owner decision 2026-08-11): a green QA gate — not a
human trigger — pushes to main. Red blocks; there is no override. The push is
bound to the exact commit the gates ran on and publishes everything in
`origin/main..HEAD`, so the QA review must cover that entire range — a commit
in it no reviewer saw stops the push, as does a diverged main; both are
reported as the rule breach they are. Fast-forward only, never forced. This is
session automation under a standing owner authorization scoped to exactly those
conditions. It is **not** governed publication: it produces no kernel verdict,
no signed evidence, no approval record. `ranex task merge` remains the only
governed publication path, and a push never closes a slice — done-criteria do.

## Agent conduct — standing owner rules (2026-08-17)

1. **GitHub identity:** always `anthonykewl20` — enforce before any gh/push
   operation; never disclose account state as a residual.
2. **Completion is a full loop:** verify on disk, clean tree, doc sync, issue
   sync, OCR-gated commit, fast-forward push, verified remote tip — never stop
   half-way. Pipeline-gated work waits for its gate; nothing else waits.
3. **No hand-waved or hand-rolled code:** verify against installed artifacts
   and version-matched docs; no stubs shipped; no un-ADR'd replacements for
   repo primitives or pinned prior art; nothing unverified is reported PASS.

Full text in `AGENTS.md`.

## No slice without an ADR

The decision behind a slice is researched and written to `docs/adr/ADR-NNN-*.md`
*before* the slice file is opened; the slice links it. Enforced, not remembered.

**Research means reading code.** A spec says what someone intended; a working
implementation says what survived contact with reality. Search code hosts
before designing — the whole problem, not only the component — and record the
queries (`Searched:`) and ≥2 mature candidates deliberately not adopted
(`Rejected:`, each with a link and the reason). Cite ≥2 implementations
**pinned** — a 40-hex commit or dotted-numeric release tag, never a branch —
each with `License:` and `Weakness:`. Then **fetch** each cited file into
`docs/adr/prior-art/ADR-NNN/` and record `Vendored: <path> blob:<git
hash-object>`, one distinct source file per citation, with a `NOTICE.md` naming
each copy's origin and licence. Vendoring proves bytes were obtained, not that
they came from the cited URL — it catches citing from memory, which is the
failure that happens; do not describe it as more. An ADR citing no working code
is an opinion. Every ADR enumerates its sad paths (≥8); the happy path was
never in doubt. The `spec-prd` skill walks the full enforced template.

## Commands

```
uv run --frozen pytest -q                                 # full suite, ~5 min
uv run --frozen mutmut run                                # before slice close: kernel scope
                                                          # only ([tool.mutmut]); survivors are
                                                          # review input, never a blocker
PYTHONPATH=src uv run --frozen python -m ranex.cli.main --help
```

CLI surface today: `gate evaluate · journal verify · run · suite freeze ·
deps fetch|approve · keygen · task dispatch|judge|merge|delegate|fanout`
(`fanout` is the free-prompt JSONL prototype, not approved mutation authority).

**Always `--frozen`.** Plain `uv run` re-locks and rewrites `uv.lock` —
measured: it silently dropped the `[options]` epoch block, after which `ranex
deps fetch` refused the lock. The committed lock is a trust root, not a cache.

`pyproject.toml` sets `[tool.uv] package = false`, so the `ranex` console
script is **not** installed (the `[project.scripts]` entry exists but nothing
installs it). Always invoke through the module path; `uv run ranex` fails.

## Docs discipline — enforced by `tests/contract/test_docs_discipline.py`

This project previously accumulated 561 architecture files and zero product
code. The docs layer is capped so that cannot happen again.

**These are the only documents that may exist:**

| Path | Purpose | Lifecycle |
|---|---|---|
| `CLAUDE.md` | this file — orientation and rules | edited rarely |
| `AGENTS.md` | agent conduct — standing owner rules (identity, completion loop, code discipline) | edited by owner-directed commit |
| `README.md` | public overview and status | updated when public status changes |
| `docs/MAP.md` | the map — problem, thesis, parts, risks | revised when evidence changes a claim |
| `docs/STATE.md` | where we stopped, what is next | **rewritten** each session, ≤50 lines |
| `docs/adr/ADR-NNN-*.md` | one researched decision per slice | append-only — supersede, never rewrite |
| `docs/adr/prior-art/ADR-NNN/` | vendored cited sources + `NOTICE.md` | admitted only via an ADR's `Vendored:` line |
| `docs/slices/SLICE-NNN-*.md` | the one open slice | at most **one** open |
| `docs/slices/done/` | finished slices | archived, not read by default |
| `.claude/skills/<name>/SKILL.md` | the six pipeline skills | set fixed by the contract test; ≤150 lines each |
| `.claude/skills/LICENSE-agent-skills.txt` | upstream MIT notice for the adapted skills | bytes pinned by the contract test |

**Do not create any other document.** No session reports, summaries, analyses,
handoffs, plans, notes, retrospectives, or `*-REPORT.md`. Instead:

- Something a future session must know → `docs/STATE.md` (rewrite, don't append)
- Something about the current work → the slice file
- Something about a change → the commit message
- Everything else → say it in chat and let it go

The docs/governance layer itself — this file, the contract tests, the skills —
changes by owner-directed commit with the reasoning in the commit message;
slices govern product code.

**This file loads into every session — the most expensive real estate in the
repo.** Only what prevents an expensive mistake belongs here. Evidence and
history belong in commit messages: permanent, greppable, free at load time.

## Delegating to an outside model

Use the OpenRouter MCP (`mcp__openrouter__send-message`) with a concrete model
slug — `~`-aliases are rejected for chat. It has no file access: inline every
fact, set `timeout_ms` explicitly. Score results against frozen tests, never
against the model's own report. The opencode CLI is **not** a delegation path —
its free tier stalls after ~2 calls; evidence:
`git log --grep=opencode-delegation`. Do not re-derive.

## Invariants

Breaking one of these is a bug, not a tradeoff. If a change requires breaking
one, stop and raise it.

- **The kernel is code.** No model decides what happens next. `evaluate()` is a
  pure function of (gate, evidence, subject, approver).
- **Absence blocks.** A required claim with no satisfying evidence is FAIL —
  never a default, never a skip.
- **Evidence is bound to a subject digest.** The same command against a
  different tree proves nothing about this one.
- **No self-approval.** Whoever produced the evidence cannot approve it.
- **A gate that cannot block is refused at construction.**
- **The journal is append-only and hash-chained.** Nothing rewrites it.
- **Removing every model credential from the machine must not change a verdict.**

## Decisions already made — do not relitigate

- Ranex builds **its own harness**: a trimmed opencode fork (MIT), every
  workflow step calling the kernel. Decided 2026-08-03. The wall stands:
  harness and kernel are separate processes — hooks collect, the kernel
  judges; the loop is confined from the keys and the journal.
- Delegation is foreman → supervisors → workers, written clean-room.
  oh-my-openagent is pattern-quarry only; its SUL-1.0 code never enters this
  tree. Hermes and OpenClaw are feature quarry, never a base.
- **Ranex never trusts worker output — including its own loop's.** Read the
  diff on disk, run the checks, discard the summary.
- **The kernel merges; the harness never does.** One worktree per task.
- Intake produces a **flow graph the non-technical owner approves**. Chain:
  graph → paths → scenarios → contract tests → gates. The approved graph is
  the root of trust.
- Tests are **frozen before BUILD and read-only to implementers**;
  red-then-green is enforced. Known open limit: the suite manifest freezes
  test IDs, not bodies (README, review 2026-08-06).
- "Deterministic" describes the **process and the verdict**, never the
  generated code.
- **Two lanes, one pipeline, automatic GO LIVE** (owner, 2026-08-11): kernel
  and harness lanes run in parallel as bounded above; a green QA gate — never
  a human trigger — pushes the tested commit to main.
- License is MIT. Monetization comes from private features on top, never from
  restricting the kernel.

## Repo shape

```
src/ranex/
  foundation/          canonical JSON, digests, signing, approval, suite results
  governed_execution/  verdict.py (the kernel), admission/task/deps domain,
                       sqlite hash-chained journal
  provisioning/        deliberate dependency provisioning (deps fetch/approve):
                       pinned resolver, lock derivation, SHA-256 wheel store
  policy/              gate catalog + producer keyring loading
  cli/                 main.py (operator entry), confinement, delegation,
                       fanout, repository/subject/toolchain;
                       host_confinement.py: imported by no src/ module, run
                       by the SLICE-017 suites via python -m
  bootstrap/           composition root — the only place concretes are wired
native/                ranex-worker-launcher (C, SLICE-017 deliverable)
governance/            gates.yaml, deps.yaml, bom.yaml, producers.yaml,
                       suite_manifest.json, confinement/ profiles;
                       evidence.json + journal.sqlite3 are gitignored
tests/                 contract/ e2e/ integration/ security/ unit/
docs/                  STATE.md, MAP.md, adr/ (+ prior-art/), slices/
.claude/skills/        the six pipeline skills
../ranex-harness       the harness lane — separate repo, deliberately out of tree
```
