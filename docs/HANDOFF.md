# Session handoff — 2026-07-30

For the next agent. Read this before doing anything else, then read
[`docs/README.md`](README.md).

## The one rule that matters most here

**Do not declare anything missing until you have searched every location.** The previous agent
declared six things absent that were present in files it had not opened — a clarify tool in the
Hermes source, an RFC home in the target tree, a success measure in ADR-0004, a bloat-and-removal
plan in research, a modular-DDD spec in ADR-0007, and a capability-level system in the Core SDLC.

Search all of these before concluding absence:

```
docs/architecture/            docs/architecture/reviews/       docs/architecture/reviews/artifacts/
docs/research/                architecture/contracts/          schemas/
.claude/worktrees/phase-2-runtime-bootstrap/     ← the inherited Hermes source
```

The corpus exceeds ten million tokens. "I searched and found nothing" is not evidence of absence.

## What Ranex is

A governance harness that makes unreliable AI agents produce reliable enterprise software.
Deterministic contracts compiled from architecture documents into checking code — not prompts.
A **non-technical owner** describes intent; an assistant translates it; a fleet of AI workers
executes under enforced constraints. Derived from Hermes Agent, stripped of its general-assistant
and commercial surface.

The owner is not technical. Explain in plain language, lead with the answer, keep it short. They
have asked for this repeatedly.

## State at handoff

| | |
|---|---|
| Public `main` | Clean — 11 entries, zero Hermes source, root README live |
| Working branch | `bootstrap/pre-upstream` |
| Accepted ADRs | 13 |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |
| Runtime | `NOT_ASSESSED` — nothing runs |
| Readiness | Neither tier declared |
| Kernel | R&D tracer only, branch `feature/kernel-tracer`, **unaudited** |

## Immediate next steps, in order

**1. Fix `HERMES-PROMOTION-059`.** One word. The provision says *"every Execution state
transition"*; research line 1902 says only *"Implement an Execution aggregate and pure reducer."*
The qualifier `every` is unsupported. Found by MiMo after three repair rounds missed it. Bump
ADR-0013 to 1.4.0.

**2. Re-dispatch three audits that were killed.** They produced zero bytes because three
concurrent HY3 runs on one provider deadlocked — see *Operational notes*. Run them **one at a
time**:
   - Verification of ADR-0013 v1.3.0 — brief at `scratchpad/verify-13.md`
   - Adversarial audit of the kernel tracer — brief at `scratchpad/audit-kernel.md`
   - Review-schema rigour questions — brief at `scratchpad/finding-rigor.md`

   The kernel audit is the important one. It asks whether the reducer is genuinely pure, whether
   the policy enforcement point actually fails closed, and whether the declared inference
   *"the relational snapshot, not journal replay, is canonical state authority"* holds. Everything
   in the engine sits on that.

**3. `evidence_refs` has no `minItems`.** `schemas/review/review-observation-v1.schema.json`
requires `evidence_refs` on every finding, but an empty array satisfies it — so a finding can
cite nothing and still validate. Also `epistemic_status` is an unconstrained string where an enum
is probably intended. Both are generated; fix at source in `generate_contracts.py`, never in the
output. **Do not invent the enum vocabulary** — that is an owner decision.

**4. Owner decisions outstanding.** Four intake parameters (question cap, session cap, materiality
thresholds, consequence-confirmation triggers) and 20 registered `OWNER_DECISION_REQUIRED` entries
in ADR-0013. All correctly block rather than default. Nothing consults them yet because no runtime
exists — that is a known limitation, not a defect.

## Open threads

- **Monetization.** The owner raised it and it was not finished. Relevant facts: `LICENSE-RANEX.md`
  is a personal-use source-available licence, all rights reserved, no commercial use without
  written permission — commercial optionality is preserved. ADR-0011 forecloses the Hermes model
  (inference margin) by committing to provider-neutral, fallback-free routing. Do not restate what
  they already decided; help them think about what the architecture still permits.
- **Documentation indexes** were added at `docs/`, `docs/research/`, `docs/architecture/reviews/`.
  Keep them current — they exist because finished work was invisible, which caused the six false
  "missing" findings.
- **Copyrighted PDFs remain reachable** in the git object database via `refs/codex/*`. A normal
  `git push` will not carry them; `--all` or `--mirror` would, to a public repo. Unresolved by
  owner choice.
- **`~/.codex/logs_2.sqlite` is ~3.6 GB, 88% dead space.** A compaction job is armed and fires when
  no Codex process is running. It has never fired because Codex has run continuously.

## Operational notes

**Model routing, from measured behaviour** (see
[`research/reviewer-model-capability-probe-2026-07-30.md`](research/reviewer-model-capability-probe-2026-07-30.md)):

- **HY3** (`openrouter/tencent/hy3`, high) — deep adversarial reading. Found the two hardest
  defects of the session. Slow, verbose, worth it where a subtle miss is expensive.
- **MiMo** (`openrouter/xiaomi/mimo-v2.5-pro`) — systematic full-corpus passes. Fast, concise,
  verifies claims structurally. Found the drift three rounds had missed.
- **DeepSeek** (`opencode-go/deepseek-v4-pro`) — third opinion for tiebreaks. Weakest on this
  corpus: mangled a path, hung five hours, sampled where a systematic pass was required, and
  inverted a check mechanism.

**Concurrency has a cliff, not a slope.** Three concurrent HY3 runs produced zero output for
24–52 minutes while a run on another provider finished in seven. Dispatch one per provider at a
time.

**A silent hang is indistinguishable from deep reasoning.** One run produced zero bytes for five
hours before anyone noticed. Check output size, not just liveness.

**Codex can be driven directly:** `codex exec --cd <dir> "<prompt>"`. Config is
`danger-full-access` with `approval_policy = never`. Use an isolated worktree for anything that
writes.

## Prompt discipline that produced results

- **State findings as attacks, not confirmations.** Verification prompts framed as "confirm X"
  returned the framing back as a finding. Adversarial prompts caught real defects.
- **Never put your own assumption in the brief.** An assertion that a tree was "unrecoverable"
  came back cited as a finding. It was false.
- **Require `path:line` for every claim.** Every finding that survived was checkable. Every
  finding that dissolved was framing.
- **Require reporting of inferences.** An unreported inference is a defect here regardless of
  whether it was correct. ADR-0012 omitted a property, an agent inferred it correctly, said
  nothing, and silently weakened a global invariant to express it.

## Standing constraint

`IMPLEMENTATION_START_READY` is not declared. Product code is authorised only as an R&D tracer in
an isolated worktree, claiming no authority — the precedent is
`reviews/2026-07-28-gate-controller-mvp-user-level-audit.md`. Do not relax a check to make code
pass; if code cannot satisfy a provision, that is a finding.
