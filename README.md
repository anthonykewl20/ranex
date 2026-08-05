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

There is a third failure, and it is the most common:

> **Most tools let the thrower paint the bullseye around the dart after it
> lands.**

One actor writes the code, writes the test, and declares success. That is why
"all tests pass" from an AI means so little — the target moved to wherever the
dart went.

## What Ranex is

Ranex is building **its own harness** — a trimmed fork of opencode, molded so
that every step is judged by a kernel that stays outside the loop (decided
2026-08-03; the kernel described below is what exists today). The kernel never
asks a model what to do next.

> Ranex is `make` for a nondeterministic compiler. `make` invokes gcc; nobody
> asks gcc what to build next.

Tools like Replit, Lovable, and Base44 optimize **the throw** — better model,
better prompt, faster loop. Ranex optimizes **the scoring**.

**Ranex does not improve aim.** Not by one degree. It makes misses visible and
cheap, and hits provable. Nothing here claims more than that.

### Why this needs to exist at all

A person hiring an architect relies on licensure, liability insurance, building
codes, and inspectors — an accountability apparatus that exists outside the
architect. AI labor has none of that. Ranex is an attempt to build the missing
apparatus: the code, the inspector, and the record.

---

## How it works

### Topology

```
                       ┌────────────────────────────────────┐
  the person who ─────▶│   RANEX KERNEL  —  code only       │
  owns the target      │   state machine · gates · journal  │
                       │   budget · merge · escalation      │
                       └───┬──────────────┬─────────────┬───┘
                           │              │             │
                    ┌──────▼─────┐  ┌─────▼──────┐ ┌────▼───────┐
                    │ Model port │  │Worker port │ │ Check port │
                    │ one call,  │  │ an agent   │ │ pytest,tsc,│
                    │ schema-    │  │ in its own │ │ Gherkin,   │
                    │ constrained│  │ worktree   │ │ scanners   │
                    └──────┬─────┘  └─────┬──────┘ └────┬───────┘
                           │              │             │
                      proposals,      diff + evidence  VERDICTS
                     translations                   (the only ones)
```

Three ports, and only one of them produces a verdict.

- **Model port** — one completion, forced structured output. Intake, review,
  translating machine state into plain language. Stateless.
- **Worker port** — an agent with its own loop and tools, running in an isolated
  git worktree. Returns a diff. Replaceable by design.
- **Check port** — the only thing on the diagram whose output counts.

Models appear at leaf nodes in exactly three roles, and **none of them can pass
a gate**:

| Role | Produces | Can it decide? |
|---|---|---|
| Proposer | a proposal | never |
| Critic | a finding | never |
| Translator | text | never |

### The chain

```
idea → flow graph → covering paths → scenarios → contract tests → gates → verdict
         ▲                                                                   │
         │                                                                   ▼
   human approves this                                            evidence + journal
```

The **approved flow graph is the root of trust.** Everything to its right is
derived mechanically; everything to its left is a conversation.

### The build loop

```
  take the next ready task
     → create an isolated git worktree
     → spawn a worker with the task envelope
     → wait for it to exit
     → read the DIFF ON DISK  (the worker's own summary is discarded)
     → run the checks         (code, not a model)
     ├─ pass → THE KERNEL merges                    (workers never merge)
     └─ fail → retry ×3 with the failure output
                 → still failing → escalate to the human in plain language
```

**Ranex never trusts the worker.** It does not need to control what happens
inside the loop, only what is allowed out of it. Containment beats control, and
costs a tenth as much.

---

## A complete run, end to end

Maria owns a dog-grooming shop and wants online booking. She cannot read code.

| Phase | What happens | Who decides |
|---|---|---|
| **INTAKE** | She describes it. Ranex asks ~12 non-technical questions: *when someone books, who gets notified? can two people take the same slot?* | — |
| | A **flow graph** appears — screens as boxes, transitions as arrows, rules as diamonds. She drags things, deletes the payment step, approves. | **Maria** ⏸ |
| **COMPILE** | Pure code, no model. Graph → covering paths → scenarios in plain English: *"when a customer picks a slot someone already took, they are shown the next three openings."* | — |
| | 34 scenarios, and a cost and time estimate. | **Maria** ⏸ |
| **PLAN** | One worker turns scenarios into a task DAG with file ownership and interface contracts.<br>*Gate: every scenario maps to ≥1 task; no file owned twice.* | code |
| **BUILD** | N workers, one worktree each, running the loop above.<br>*Gates: tests pass · types check · owns only its files · no new dependencies.* | code |
| **INTEGRATE** | One worker on the merged tree.<br>*Gate: full suite green; all 34 scenarios pass together.* | code |
| **SHIP** | Deploy, smoke test, live URL. She clicks through her own flow graph in a real app. | **Maria** ⏸ |

Three human gates. Everything between them is the loop turning.

When a gate fails three times, she gets a **product** question, not a stack
trace: *"Two customers hit the same slot at the same instant. Tell the second one
immediately, or offer a waitlist?"* That she can answer.

Underneath, invisible to her: every file traces to a scenario, traces to a node
she approved, with evidence and a verdict pinned to an exact content digest. She
will never look at it. Her acquirer's diligence team will.

---

## What makes a verdict trustworthy

An agent that can edit its own tests will always pass. Four rules prevent it:

1. **Tests are frozen before BUILD.** Generated in COMPILE, digested, read-only.
   Any diff touching a test file fails the gate instantly.
2. **Red-then-green, enforced.** Every generated test must fail against the
   pre-implementation tree. A test that passes before the code exists is not a
   target — it is a circle painted around a dart.
3. **Edge coverage as a gate, not a metric.** Not "80% of lines" but *"every edge
   in the approved graph has ≥1 passing test."*
4. **No self-approval.** Whoever produced the evidence cannot approve it, and the
   task that implements a scenario never authors or judges its test.

This project applies those rules to itself. The SLICE-001 tests were committed
red at `b495e3635`, before any implementation existed — red-then-green as a fact
in the git history rather than a claim in a document.

## The determinism ledger

| Deterministic | Not, and never will be |
|---|---|
| graph → covering paths | the code an agent writes |
| paths → scenario text | whether it passes on the first try |
| test + code → result | how long it takes, or what it costs |
| results + rules → verdict | |
| journal → full replay | |

Every row on the left is a pure function. Nondeterminism is quarantined inside a
single step whose output faces the left column.

**"Deterministic" describes the process and the verdict — never the generated
code.** Anyone claiming an LLM produces identical software twice is selling
something.

## What a passing build actually proves

> Every behavior on the graph the owner approved has at least one executable
> test. Every test ran. Every test passed. Here is the evidence, pinned to this
> exact code digest.

That is the claim. These are **not** claims Ranex makes:

- **That the graph was right.** Only the person who owns the target can judge
  that, and only by using the thing. Hence the preview gate.
- **Anything off the graph.** Unspecified behavior is unconstrained. Absence of a
  requirement is absence of a guarantee.
- **Non-functional properties** — performance, accessibility, security — unless
  you add gates for them. Those are separate checkers, not free.

"Conformant to an approved specification" is real, defensible, and deliverable.
"Correct" is not a claim anybody can make.

---

## Status

**Pre-release. This is not a usable product yet.** It is a kernel with a working
verdict path and very little else. The full picture above is designed; the list
below is what is actually built.

**Works today**

- `evaluate()` — a pure function of (gate, evidence, subject, approver). Same
  inputs, same verdict, always.
- **Subject-bound evidence** — the same command run against a different *commit*
  proves nothing about this one. Stale evidence stops counting automatically.
  The runner materialises that committed tree from verified blobs before it runs
  the command.
- **Absence blocks** — a required claim with no satisfying evidence is FAIL,
  never a default and never a skip.
- **No self-approval** — whoever produced the evidence cannot approve it.
- **Append-only hash-chained journal** — SQLite triggers prohibit ordinary updates
  and deletes; the hash chain detects out-of-band row edits. `ranex journal
  verify` recomputes that chain for an operator.
- **`ranex run`** — after an operator-facing dirty-tree check, materialises HEAD
  from verified blobs, executes the command there with an environment built from
  empty and a pinned toolchain, then records its exit code and subject digest.
  `run` then `gate evaluate` is a closed loop for self-contained commands.
- **Signed evidence** — Ed25519, verified against a committed keyring before a
  record is admitted. The verifier holds only public keys and cannot forge.
- **Claim↔command binding** — the committed catalog declares the argv that
  satisfies a claim, and the kernel compares its digest, so a record of `true`
  no longer satisfies `tests-executed`. Read the next section for what it does
  *not* buy.
- `ranex gate evaluate`, `ranex keygen`, and repository path confinement.

**Known gaps — stated plainly**

- **SLICE-004 shut the six frozen false-PASS routes.** The command runs against a
  materialisation of verified committed blobs, not the working tree; its
  environment is built from empty; and Ranex resolves its own tools from pinned
  directories. The tests cover an inherited environment, an ignored file, an
  untracked empty directory, a clean-filter-hidden edit, a substituted Git blob,
  and a `git` shim on `$PATH`. They are passing regression tests, not expected
  failures. **Do not point Ranex at a real agent yet.** SLICE-006 must first make
  dependency-backed commands runnable without trusting the observed party's
  `.venv`, `node_modules`, or `uv`; same-UID key theft, unauthenticated approvals,
  and journal rollback remain open after that.
- **Approver identity is unauthenticated.** `--approver` is a plain string, so a
  producer can name anyone as their approver. Evidence signing proves only that
  the holder of the registered private key signed the record; it proves nothing
  about who approved it. No-self-approval compares those unauthenticated strings.
- **The journal does not detect rollback or truncation.** Concurrent appenders
  are serialised before they read the previous link, and `ranex journal verify`
  recomputes the chain. But an internally consistent earlier prefix still
  verifies after later rows are removed. *(unassigned)*
- **No worker dispatch, no flow graph, no scenario compilation**, no budget, no
  escalation. Those are designed, not built.

Roughly speaking: the hardest part to get conceptually right exists, and almost
none of the surface around it does.

## Current work

<!-- Kept in sync with docs/STATE.md by tests/contract/test_docs_discipline.py -->

**Active slice:** none. SLICE-009 closed 2026-08-05. Next: the owner decides
whether to merge and push `slice009-build`; then diagnose the unrelated CI red
on `origin/main`; then decide mutation-testing policy.

**Ranex gates Ranex.** With SLICE-009 closed, `ranex run` executes this
repository's own suite — provisioned, sealed and offline — against a
materialisation of the real current commit, and `gate evaluate` judges signed
structured outcomes against the manifest diff — 736 IDs, with 67
ceremony-declared expected-skips — not the exit code alone. The materialisation
is a fresh single-commit repository carrying the verified tree (ADR-009), so a
committed suite that asks git about itself is told the truth, while the sample
shares nothing with the governed object store.

Ranex observes a **materialisation of the subject commit**, built from bytes
checked against the object ids the commit's tree carries, with an environment
constructed from empty and a toolchain pinned to directories the observed party
cannot write. The six frozen false-PASS paths were two root causes, not six: the
tree observed was not the tree HEAD names, and the toolchain and its inputs were
chosen by the party being measured. Both are closed.

## Completed slices

- **SLICE-009-a-skip-is-absence** — exit-code satisfaction let a skipped or
  vanished test read as success; the measured failure destroyed 27 tests while
  the remainder stayed green. Junitxml is bound in the digest-bound argv;
  signed structured outcomes use evidence v3; an outcome-blind manifest is
  frozen from the suite; and its diff blocks undeclared skip, xfail, xpass,
  error, or missing IDs. Delegated judging reads trust roots from the base tree.
  A hostile tree can forge the artifact; criterion 10's passing test states
  that boundary. Ranex's own gate now PASSes honestly and flips to FAIL when a
  frozen test's file is deleted.
- **SLICE-008-first-delegation** — the front door. `ranex task delegate` runs
  a real agent headless in a dispatched worktree, in an environment built from
  empty that **refuses to start holding the signing key**; the wall-clock bound
  kills the whole process group; the kernel cross-checks the emission against
  its own dispatch record, measures the frozen suite sealed, and a separate
  keyless invocation judges — a CANDIDATE naming its missing claims, never a
  PASS. `task fanout` runs a bounded pool, one worktree each; the journal
  chain verifies after concurrent runs. Proven end to end against a real free
  model, and the harness fork now presents as `ranex` with opencode's MIT
  attribution retained. Recorded, not mitigated: the model credential sits in
  a network-open loop (use a scoped, spend-limited key), and `ranex run`'s own
  path still reads the key before spawning (`RISK-06` stays open there).
- **SLICE-001-evidence-production** — `ranex run` executes a command, observes
  it, and emits evidence the gate accepts. Target committed red at `b495e3635`,
  before any implementation existed.
- **SLICE-002-evidence-authenticity** — evidence carries an Ed25519 signature
  bound to a producer in a committed keyring, and the keyring and gate catalog
  are read from the commit rather than the working tree. Closed once, reopened
  when audits found the tests were narrower than reality, and closed again after
  17 defects across four audits. **Reopened a second time on 2026-08-02**: the
  trust-root check was skipped entirely for a path the commit did not carry, so
  a catalog or keyring the attacker named was read unchecked. Closed by
  `docs/adr/ADR-002-committed-trust-root.md`.
- **SLICE-003-claim-command-binding** — the committed catalog declares the argv
  that satisfies a claim, and the kernel compares its digest, so a signed record
  of `true` no longer satisfies `tests-executed`. Six independent audits failed
  to break that binding, and criteria 1–9 were re-proven by mutation — each
  safeguard deleted from `src/` in turn, the covering test watched to go red.
  Closed on its own promise, not on a clean bill of health: the same audits
  reproduced six ways to get a false PASS *around* the binding, all one root
  cause, all recorded and frozen as strict expected-failure tests, all assigned
  to the next slice.
- **SLICE-007-trimmed-fork-to-the-kernel** — Ranex owns its harness: `opencode`
  forked at `v1.18.11` (`012c2f57`), trimmed to the keep-set, plugin surface
  locked to compiled-in built-ins, and startup fails closed unbridged. The
  kernel gained `task dispatch|judge`: the dispatcher records task→worktree in
  the hash-chained journal, the harness commits and emits references, and the
  kernel cross-checks against its own record, materialises the commit, and
  journals `CANDIDATE` — never a PASS; the stamp stays a human's, out-of-band.
  Proven end-to-end by the gear-mesh e2e running the loop on a deterministic
  in-fork model with zero credentials. Closed by
  `docs/adr/ADR-008-fork-opencode-and-bridge-to-the-kernel.md`.
- **SLICE-004-hermetic-observation** — the six frozen false-PASS paths are shut.
  The bound command runs against a **materialisation of the subject commit**
  whose every blob was checked against the object id the tree carries, in an
  environment built from empty, with a toolchain pinned to directories the
  observed party cannot write. Closed by
  `docs/adr/ADR-005-hermetic-observation.md`. Two capabilities were
  **deliberately withdrawn**: a tree needing installed dependencies, and a tree
  carrying a symlink or submodule, can no longer be observed at all.
  **Closed, reopened, and closed again.** The first close rested on a cleanup
  control that had never worked on any supported Python, covered by a test that
  monkeypatched out the very function it was named for — and on a mutation check
  run by hand by the same actor who wrote the code. Measuring the general form of
  that found **59 refusals no test executed at all**. The reopening replaced the
  hand-run claim with `mutmut`, added `diff-cover` so no future change can add an
  unreached line, and closed 15 of the 59. The remaining 44, and 880 surviving
  mutants including some in the kernel, are recorded in the slice rather than
  smoothed over.
- **SLICE-006-gating-a-real-test-suite** — Ranex gates Ranex. Dependencies are
  provisioned deliberately: `deps fetch` derives the lock clean under pinned
  inputs and byte-compares it, only SHA-256-addressed wheels enter the store,
  `deps approve` records the named package delta, and the run executes sealed
  and offline. The materialisation became a fresh single-commit repository
  carrying the verified tree (ADR-009), which let the five git-dependent
  controls pass unweakened, and the self-gate ran for real with the operator's
  own registered key. Nine defects found by driving the CLI as a person does;
  none by a unit test. What is **not** caught is recorded in the slice: an
  approved, hash-correct wheel still chooses its own exit code.

---

## Running it

```sh
uv run --frozen pytest -q

PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD \
    --approver reviewer_alice
```

Always `--frozen`. Plain `uv run` re-locks and rewrites `uv.lock`, which is a
trust root here: it silently dropped the resolution epoch once, after which
`ranex deps fetch` refused the lock against its own clean derivation. The
gated command needs no flag — its argv stays exactly as the catalog binds it,
and `run` sets `UV_FROZEN` in the environment instead.

`pyproject.toml` sets `[tool.uv] package = false`, so the `ranex` console script
is **not** installed. Invoke through the module path above.

**On a fresh clone `gate evaluate` fails, and that is correct.** Absence
blocks: no evidence exists yet for `tests-executed`, so the verdict is FAIL
with a nonzero exit, naming the missing claim. Producing evidence needs a
signing identity of your own — the private key must live outside the
repository, and `keygen` refuses to write it anywhere inside:

```sh
export RANEX_SIGNING_KEY=~/.config/ranex/worker.key
PYTHONPATH=src uv run python -m ranex.cli.main keygen --producer worker
```

This repository commits the **public** keyring, `governance/producers.yaml` —
it is the trust root, and review of it is the control on it. It holds public
halves only; no private key is anywhere in the tree. It is a single
`producers` mapping, and `keygen` prints the exact line to add (and the whole
mapping, for a keyring being created from nothing):

```yaml
producers:
  worker: ed25519:<the key keygen printed>
```

Commit the change.

Next, provision dependencies. The bound command is `uv run pytest -q`, and the
observation is built from committed blobs only — so `.venv` is not in it and the
suite has nothing to import until its wheels are provisioned deliberately. The
resolver is pinned by path **and** digest in `governance/deps.yaml`, at a
root-owned location, because a resolver this uid can rewrite is one the observed
party chooses:

```sh
sudo install -m 0755 ~/.local/bin/uv /usr/local/bin/uv

PYTHONPATH=src uv run python -m ranex.cli.main deps fetch
PYTHONPATH=src uv run python -m ranex.cli.main deps approve --approver reviewer_alice
```

`deps fetch` is the only networked step: it re-derives the lock from the manifest
alone under those pinned inputs, refuses any byte of difference, and admits only
SHA-256-addressed wheels to the store. `deps approve` prints the package delta
and records that a human accepted exactly it. **Skipping either makes the next
command refuse, by name** — a lock nothing regenerated may be entirely authored.
Approval reduces hidden change; it cannot make third-party code truthful, and
`tests/security/test_slice006_approved_wheel_can_lie.py` demonstrates an
approved, hash-correct wheel forcing a passing verdict. Then:

```sh
PYTHONPATH=src uv run python -m ranex.cli.main run \
    --claim tests-executed --producer worker -- uv run pytest -q
```

`gate evaluate` will still FAIL today, and the reason is recorded rather than
hidden: five of this repository's own tests need a git checkout, and the
observation carries committed blobs with no `.git`, so the suite exits nonzero
inside it. That is SLICE-006 criterion 14, `ADR-009` proposes the fix, and two
strict `xfail` markers in `tests/e2e/test_gating_real_suite.py` will fail loudly
the moment it starts passing.

Once the tree moves past the digest the evidence was bound to, `tests-executed`
stops counting too. A record that fails verification is reported as *refused*,
with a reason — never as "no evidence", because an attack and an unfinished task
are not the same event.

## Development

One slice at a time; finish it before starting another. The rule is enforced by
a test, not left as a convention — as is the cap on how many documents may exist,
because this repository previously accumulated 561 architecture files and zero
product code.

- `CLAUDE.md` — invariants, settled decisions, working rules
- `docs/STATE.md` — where work stopped and what is next
- `docs/slices/` — the open slice, when one is open

## License

MIT © 2026 Anthony Garces
