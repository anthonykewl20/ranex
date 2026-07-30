# Session handoff — 2026-07-30 (evening)

For the next agent. Read this, then [`docs/README.md`](README.md).

Every claim below is labelled. **FACT** means measured in this repository or
verified against a cited external source. **INFERENCE** means concluded but not
directly proven. **UNVERIFIED** means neither. Do not promote a label without
doing the work.

## The two rules that matter most here

**1. Nobody holds true answers — verify everything.** Not the owner, not you, not
any model. Your training knowledge is stale. HY3, Codex, Grok, MiMo and DeepSeek
are all susceptible to assumption. Every claim needs proof at `path:line` or a
cited source. This is the owner's standing mandate, restated three times.

**2. Ranex is not novel — find the working piece before designing anything.**
Others have already built what you are about to invent, and their version is
public and maintained. Search first, adopt, then improve. See
[`architecture/rfcs/RFC-0003`](architecture/rfcs/RFC-0003-deterministic-session-continuity-and-drift-tripwires.md)
for what happens when you skip this: three of its four provisions were rewritten
as adoptions of `cog`, `AGENTS.md`, and `pre-commit` after a sweep found them.

**Corollary — a negative search result is evidence about your search, not about
the corpus.** Do not declare anything missing until you have searched every
location, including these:

```
docs/architecture/            docs/architecture/reviews/   docs/architecture/reviews/artifacts/
docs/architecture/rfcs/       docs/research/               architecture/contracts/   schemas/
.claude/worktrees/kernel-tracer/            ← the R&D tracer, untracked src/ and tests/
.claude/worktrees/phase-2-runtime-bootstrap/ ← inherited Hermes source
```

## What Ranex is

A governance harness that makes unreliable AI agents produce reliable enterprise
software. Deterministic contracts compiled from architecture documents into
checking code — not prompts. A **non-technical owner** describes intent; an
assistant translates it; a fleet of AI workers executes under enforced
constraints. Derived from Hermes Agent, stripped of its general-assistant and
commercial surface.

The owner is not technical. Explain in plain language, lead with the answer, keep
it short. Do not ask trivial questions that do not need their input.

## State at handoff — all FACT

| | |
|---|---|
| Working branch | `bootstrap/pre-upstream` |
| Accepted ADRs | **20** (ADR-0017 … ADR-0020 accepted 2026-07-31) |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |
| Runtime | `NOT_ASSESSED` — nothing runs |
| Readiness | Neither tier declared |
| Owner decisions | 20 rows; **six resolved today** by ADR-0015/0016. The registry still reports 20 — see Open threads |
| Kernel | R&D tracer, branch `feature/kernel-tracer`. Audited by three models; §8.3 gate, journal replay and real crash tests added. 82 tests pass |

## Corrections to the previous handoff — read before acting

The handoff you are replacing contained a **false** instruction. Both corrections
are FACT.

1. **Agent stalls were NOT provider concurrency.** The previous handoff said three
   concurrent runs on one provider produce zero output for 24–52 minutes, and told
   you to serialize. Measured today: the causes were (a) **unclosed stdin** —
   identical model, brief and provider gave 0 bytes in 2h47m with stdin open and
   3,275 bytes in 90 seconds with `< /dev/null`; and (b) an **exhausted
   opencode-go quota**. Cross-provider parallelism works fine. Always pass
   `< /dev/null` and a hard `timeout`.
2. **Check accumulated CPU time, not output size,** to tell working from hung. A
   real hang shows `00:00:00` CPU over hours; a working model can legitimately go
   quiet. The previous advice to watch file size produced a false alarm on a model
   that was simply slow.

## Immediate next steps, in order

All six owner decisions that blocked `IMPLEMENTATION_START` were resolved on
2026-07-30 by `ADR-0015` and `ADR-0016`. What remains is work, not decisions.

**1. Teach the contract system to record a resolved owner decision.** This is the
sharpest remaining defect. `generate_contracts.py:6946` raises if
`owner_decision_ref` is not `None`, the emitted row schema pins it to
`{"type": "null"}`, and the validator pins `unresolved_owner_decision_count` to
20. `ADR-0013` modelled these rows as permanently unresolved and encodes no path
to resolution, so validation reports 20 unresolved decisions although six now have
accepted ADRs. **FACT**, verified at those lines. Do not simply edit the number —
it is a normative change to an accepted ADR and needs its own decision.

**2. Close the review-schema defects.** The rigour audit
(`reviews/artifacts/2026-07-30/agent-reports/rigor-hy3.md`) found four
blocking-class defects. Two were fixed on 2026-07-30: `epistemic_status` is a
closed enum, and `severity` now uses SARIF `result.level` with a blocking finding
required to be `FACT` with cited evidence. Still open: `evidence_refs` items are
untyped so `[null, 42, {}]` validates, and blindness is self-assertable in
`independence-evaluation-v1`. Fix at the generator, never in generated output.

**3. Configure the static type checker.** `LANG-TYPECHECK-001` (`ADR-0014`) is
recorded as unsatisfied and blocking at `IMPLEMENTATION_START`. No checker is
configured; `ruff` is a linter and does not discharge it. Choose against evidence
current at selection time and weight specification conformance over speed.

**4. `uv` is an undeclared load-bearing tool choice.** Same defect class
`ADR-0014` closed for the language. Needs its own decision record.

**5. `RFC-0002` and `RFC-0003` await owner decision.** RFC-0002 (Spec Kit
adaptation, amended with requirement 12 binding analyze/converge to the enforced
finding contract) and RFC-0003 (session continuity, rewritten as adoption of
`cog`, `AGENTS.md`, `pre-commit`, with an all-Python CI layer).

## Open threads

- **Monetization**, still unfinished. New relevant FACT: FedRAMP requires
  machine-readable authorization packages by **2026-09-30**, and NIST OSCAL is the
  format. Ranex produces exactly that class of artifact. `LICENSE-RANEX.md` is
  personal-use, all rights reserved, so commercial optionality is preserved.
  ADR-0011 forecloses the Hermes inference-margin model.
- **`uv` is an undeclared load-bearing tool choice** — every executable
  verification path runs through it, `uv.lock` is tracked and licence-classified,
  and no decision record selects it. Same defect class ADR-0014 just closed for
  the language. **FACT**, found by HY3.
- **Dependency licences are unregistered.** `legal/licensing-manifest.json` has no
  entry for `jsonschema`, `PyYAML`, or the `rfc8785` package. Recorded as a failing
  gap in ADR-0014 v1.1.0. **FACT**, verified by full-text scan.
- **Copyrighted PDFs remain reachable** in the git object database via
  `refs/codex/*` — **15 such refs confirmed present on 2026-07-30**. The `origin`
  remote is a **PUBLIC** GitHub repository. A normal `git push <remote> <branch>`
  does not carry them; **`git push --all` or `--mirror` would publish them**.
  Never use those flags on this repository. Unresolved by owner choice. **FACT**.
- **`~/.codex/logs_2.sqlite` is ~3.6 GB, 88% dead space.** A compaction job is
  armed and fires when no Codex process runs. It has never fired. **UNVERIFIED**
  today — inherited claim, not re-checked.

## Operational notes — model routing

Verified prices, OpenRouter, 2026-07-30. **FACT.**

| Model | In | Out | Role |
|---|---|---|---|
| `tencent/hy3` (variant high) | $0.13/M | $0.53/M | **Workhorse.** Exhaustive reads, adversarial audits, full-corpus sweeps |
| `tencent/hy3-preview` | $0.06/M | $0.21/M | Cheaper still; untested here |
| `xiaomi/mimo-v2.5-pro` | $0.43/M | $0.87/M | Systematic full-row passes; verifies claims structurally |
| `x-ai/grok-4.5` | $2.00/M | $6.00/M | **Final validator and tiebreaker only** — owner decision |
| Codex `gpt-5.6-sol` | **free** | **free** | **Default for heavy research.** Owner has an x20 Pro account. Fastest measured, ~27 KB/min |

- **Grok earns the validator role on evidence:** it found §8.3 that four other
  readers missed, and it **executed** an exploit (forged the SQLite snapshot, then
  called `load()`) rather than reasoning about one. It did this at **default**
  effort while HY3 ran at `high`.
- **Cost is dominated by what a model READS, not by output length or reasoning
  effort.** FACT: a 36 KB kernel audit cost $0.0868; four tiny single-file probes
  across all four effort levels cost $0.0798 combined; one whole-repo-plus-web
  sweep cost **$1.88**. Constrain the brief's reading scope to control cost.
  Reasoning effort is close to free on narrow questions — all four variants
  answered a targeted question correctly.
- **GLM 5.2 — verdict CONFOUNDED, not established.** It measured ~1.4 KB/min
  against Codex's ~27 KB/min, but it ran on opencode-go while that gateway's quota
  was exhausted. Out of the roster by owner decision; the slowness measurement is
  not trustworthy evidence about the model.
- **opencode-go quota is exhausted.** `hy3` and `grok-4.5` are listed there but
  will not respond. Use OpenRouter. **Probe any model with a one-token prompt
  before dispatching real work** — a model appearing in a list does not mean it
  answers.
- **Costs are queryable** at the provider's credits endpoint. Expect settlement lag
  of more than 20 seconds, so do not attribute per-run costs from a short window.
  Check the remaining balance before dispatching paid work.
- **Codex is drivable directly:** `codex exec --cd <dir> "<prompt>" < /dev/null`.
  Config is `danger-full-access` with `approval_policy = never`. Use an isolated
  worktree for anything that writes.

## Prompt discipline that produced results

- **State findings as attacks, not confirmations.** "Confirm X" returns the
  framing back as a finding.
- **Never put your own assumption in the brief.** Of three hypotheses withheld
  today, one was independently found, one was found in a more serious form, and
  one was not surfaced — which is itself information about that hypothesis.
- **Require `path:line` for every claim,** and verify before relaying. Today: one
  agent claim verified true, one overstated, one file-list grep that turned out to
  be a false positive matching `429` inside a SHA-256 hash. Relaying any unchecked
  would have misled the owner.
- **Require reporting of inferences.** An unreported inference is a defect
  regardless of correctness.
- **Ask a sweep what to DELETE**, not only what to add. That instruction is what
  demolished RFC-0003's first draft.

## Assistant errors this session — do not repeat

Recorded because the pattern matters more than the individual mistakes. All were
caught by the owner or by another model, never by self-review.

1. Asserted from recall that the tooling dependencies were C-backed. **False** —
   `jsonschema` and `rfc8785` contain no compiled extensions.
2. Wrote "each dependency carries a licensing-manifest entry" into an **accepted
   ADR**. **False** — zero entries exist. Fixed in v1.1.0.
3. Diagnosed stalls as provider concurrency and serialized the whole queue on that
   basis, after having already disproved it.
4. Designed four mechanisms in RFC-0003 before searching; three already existed as
   maintained tools.
5. Queued two jobs on a model without probing it; the model never answered.
6. Ran a grep, reported five files as containing rate-limit evidence, and nearly
   confirmed the owner's hypothesis on a match that was `429` inside a hash.

The common thread: **stating a checkable claim without checking it.**

## Standing constraint

`IMPLEMENTATION_START_READY` is not declared. Product code is authorised only as
an R&D tracer in an isolated worktree, claiming no authority — the precedent is
`reviews/2026-07-28-gate-controller-mvp-user-level-audit.md`. Do not relax a check
to make code pass; if code cannot satisfy a provision, that is a finding.
