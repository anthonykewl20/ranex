# RFC-0003: Deterministic Session Continuity and Drift Tripwires

| Field | Value |
|---|---|
| Status | DRAFT |
| Owner | Human owner |
| Authors | Assistant, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; no expiry claimed |
| Affected contexts | `process_assurance`, `agent_collaboration`, `configuration_management`, `assurance`, `provenance_compliance` |
| Supersedes | The hand-written `docs/HANDOFF.md` practice, retained as prose but no longer the continuity mechanism |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted (`rfcs/README.md` Status) |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/CORE_SDLC_OPERATING_MODEL.md:323` (Definition of Closed requires docs and decision status current) |

## Revision note

The first draft of this RFC designed four mechanisms from scratch. An adversarial
prior-art sweep found that three of them already exist as maintained public
tools, and the fourth is a settled open convention used by more than sixty
thousand repositories. That draft is superseded by this one, which adopts rather
than invents. The episode is recorded because authoring a design before searching
for the existing implementation is a method defect, not merely wasted effort.

## Decision question

Every AI agent begins a session with no memory of the project, and documentation
currency depends on an agent choosing to update it. Both facts are known and
neither is enforced. Which existing tools should Ranex adopt to make continuity
and documentation currency deterministic, and what genuine residue must Ranex
build itself?

## Full-map impact

- **Contexts:** as listed; no context gains or loses state ownership.
- **Public APIs:** none change.
- **State owners:** unchanged. The continuity artifact is a projection of state
  owned elsewhere, plus an authored narrative.
- **Effect owners:** unchanged. No check here issues a permit or performs an
  effect; each either passes or blocks.
- **Lifecycles:** none added.
- **Trust/security boundaries:** enforcement moves outside the agent being
  governed, and two new third-party tools enter the build path.
- **Attachment points preserved:** `ADR-0007` boundaries, `ADR-0012` readiness
  separation, and generated-output authority rules are untouched.
- **Product inclusions/exclusions changed:** none.

## Context and evidence

### Facts

1. **Measured, this repository.** `docs/HANDOFF.md` is the current continuity
   mechanism and it transmits a false instruction: it tells the next agent that
   concurrent runs on one provider cause multi-hour stalls. The measured causes
   were an unclosed stdin (identical model, brief and provider: 0 bytes in 2h47m
   with stdin open, 3,275 bytes in 90 seconds with it closed) and, separately, an
   exhausted gateway quota. A hand-written handoff became a false instruction
   within one session.
2. **Measured, this repository.** Documentation drift appeared within hours and
   was invisible until an adversarial audit: root `README.md` claimed 13 accepted
   ADRs against a registry of 14; `docs/research/README.md` claimed 57 promoted
   provisions against a catalog of 65.
3. **Measured, this repository.** The stale count propagated into work — the
   reviewing agent recorded that the misstated ADR set "propagated into this
   task's intake premise."
4. **Measured, this repository.** Deterministic fail-closed checking already
   works here: `generate_contracts.py` refused an ADR three consecutive times —
   wrong status, unregistered ID, stale digest pin — until registration was
   consistent.
5. **Verified externally, by execution.** `cog` (`cogapp`) provides exactly the
   mechanism the first draft specified: `-c` checksums generated output against
   accidental change, `--check` fails when a file would change if regenerated,
   `--diff` shows what failed, `--check-fail-msg` supplies a custom message.
   Confirmed by running `cog --help` on 2026-07-30. Version 3.6.0, **MIT**
   licence ([PyPI](https://pypi.org/project/cogapp/),
   [repository](https://github.com/nedbat/cog)).
6. **Verified externally.** `AGENTS.md` is an open convention for handing project
   context to a fresh agent session: used by more than 60,000 open-source
   projects, supported by 20+ tools including Claude Code, Codex, Cursor, Aider,
   Gemini CLI, Copilot's coding agent, Devin, Zed and Windsurf, and now stewarded
   by the Agentic AI Foundation under the Linux Foundation
   ([agents.md](https://agents.md/)). An open convention, not a formal standard.
7. **Verified externally.** `danger-js` exists for precisely the "nag on rules
   the contributor forgot" role, with the stated purpose *"Stop saying 'you
   forgot to …' in code review."* It runs in CI across GitHub Actions and many
   other systems ([danger.systems/js](https://danger.systems/js/),
   [danger/danger-js](https://github.com/danger/danger-js)).
8. **Verified externally.** Structured handoff protocols have measured effect:
   I-PASS produced a 47% reduction in adverse events across 32 hospitals and a
   23% reduction in medical error in a prospective multi-centre study, and is
   assessed as the structured handoff tool with the strongest certainty of
   evidence ([AHRQ review](https://www.ncbi.nlm.nih.gov/books/NBK613742/),
   [I-PASS outcomes](https://answers.childrenshospital.org/i-pass-handoffs/)). The
   mechanism is a fixed required format, not exhortation.
9. **Measured, this repository.** No enforcement infrastructure exists: no active
   git hook, no `core.hooksPath`, no harness hook configuration, no CI workflow.
10. **Measured, this repository.** A worker-to-worker handoff artifact already
    exists — `docs/architecture/templates/AI_HANDOFF.yaml` and
    `schemas/execution/agent-handoff-v1.schema.json` — scoped to one task packet
    within a run, not to project state across sessions.

### Assumptions

1. Agents will not reliably self-report. Treated as certain: the owner's position
   is that humans with notes and handbooks forget and bypass, and an agent with
   no persistent memory is strictly worse.
2. Any file an agent can write, an agent can also neutralize. This bounds what
   "cannot be bypassed" may honestly mean.
3. Enough documentation claims are machine-recomputable for generation to be
   worthwhile. Supported by fact 2: both drifted claims were plain counts.

### Unknowns

1. Whether a remote CI service will exist. Without one, no layer is fully
   non-bypassable by a local agent.
2. Whether the harness hook mechanism can be made non-editable by the agent it
   governs in this environment.
3. How many documentation claims are machine-recomputable in practice; a census
   is required before coverage can be stated.
4. Whether `AGENTS.md` semantics, being a convention rather than a specification,
   are stable enough to carry a blocking obligation. It currently governs agent
   *instructions*; using it to carry *state* is an extension, not conformance.

### Conflicts

1. **"Invincible to AI" is not achievable locally and this RFC does not claim
   it.** An agent with repository write access can delete a hook, pass
   `--no-verify`, or edit a settings file. Only a check running where the agent
   cannot write is genuinely non-bypassable. Each layer below states its real
   strength; overstating this would be the defect class the harness exists to
   catch.
2. **Two third-party tools enter the build path.** Both are MIT or permissive and
   neither is copyleft, but they are new supply-chain surface — see Security.
3. **Against `ADR-0012`.** Nothing here declares readiness or authorizes product
   code.
4. **Against `ADR-0014`.** `danger-js` is a Node tool, and `LANG-PRIMARY-001`
   fixes Python as the implementation language. Development-time CI tooling is
   not a Ranex component, but this must be stated rather than assumed — see
   `CONT-NAG-001`.

## Requirements and non-goals

**Requirements.** Continuity must survive total loss of agent memory. Currency of
machine-checkable documentation must not depend on an agent remembering.
Detection must be deterministic, with no model judgment in the check. Marginal
token cost per session must be zero. A violation must block where an authority
boundary is crossed.

**Non-goals.** Judging whether prose is good. Enforcing currency of claims no
machine can recompute. Replacing the existing worker-to-worker handoff artifact.
Declaring readiness. Preventing a determined operator with write access from
disabling local checks. **Building any mechanism a maintained tool already
provides.**

## Alternatives

### Option A — Better instructions to the agent

Write the obligation into memory and the handoff document and rely on compliance.
Rejected: this is the status quo, and facts 1–3 are its measured failure within a
single session.

### Option B — Build the four mechanisms (the superseded first draft)

Rejected. Facts 5–7 show three are maintained tools and one is a 60,000-repository
convention. Building them would cost implementation and maintenance to obtain a
worse version of something free, and would violate the owner's standing rule that
Ranex is not novel and the working piece already exists publicly.

### Option C — An AI reviewer checking documentation currency

Rejected as the primary mechanism: it costs tokens per session, adds a second
fallible agent, and produces findings rather than blocks. Retained for the
non-checkable prose residue as a non-blocking role.

### Status quo — hand-written `HANDOFF.md`

Rejected. Fact 1 is the status quo actively transmitting a false instruction.

## Proposed design

Four provisions. Three are adoptions; one is the genuine residue.

### `CONT-GENERATE-001` — Adopt `cog` for generated spans in documentation

Volatile documentation facts derivable from generated contracts — counts of
accepted ADRs, promoted provisions, schemas, registries, state axes, readiness
status, validation outcome — are emitted into `cog` spans inside the documents
that state them, checksummed with `cog -c`.

Ranex writes only the small functions that compute each value from existing
registries. `cog` owns marker syntax, emission, checksumming, and change
detection. Drift becomes structurally impossible for every claim inside a span:
both defects in fact 2 were plain counts and would not have been expressible.

Adopted, not built: MIT, no copyleft, one development dependency, and the
`--check` mode required for enforcement is verified to exist (fact 5).

### `CONT-DRIFT-001` — Drift is a validation failure, via `cog --check`

`validate_contracts.py` invokes `cog --check --diff` over the documentation set
and fails on any divergence. Its report already gates everything and already
refuses inconsistency (fact 4), so documentation currency becomes the same class
of failure as a wrong digest pin.

Claims that cannot be placed in a generated span are, in order of preference:
moved into one; or left as prose and excluded from blocking. Building a bespoke
prose-claim extractor is **dropped** — the sweep found no maintained tool for
general numeric claim verification, and inventing one contradicts Option B's
reasoning.

**No waiver.** No environment variable, flag, or configuration key may skip the
drift check. An unfixable drift is a finding; relaxing a check so the tree passes
is already forbidden by standing constraint. This is policy, not a tool feature.

### `CONT-SESSION-001` — Adopt `AGENTS.md` as the location; the residue is the field list

`AGENTS.md` is the conventional, tool-recognised place a fresh agent looks
(fact 6). Ranex adopts it as the continuity location rather than defining a new
artifact type.

Its **generated section** is a `cog` span projecting state that already exists:
the commit it describes, accepted decision set, open `OWNER_DECISION_REQUIRED`
entries, readiness tier status, validation result and scope, and uncommitted paths
at generation time.

Its **authored section** is the genuine residue — the one thing no tool provides.
A fixed field list, following I-PASS's proven mechanism of a required format
rather than an instruction to communicate (fact 8), with field names aligned to
established handoff vocabularies rather than invented. Every authored claim
carries an `epistemic_status` from the closed vocabulary already enforced in
`review-observation-v1`:

- what was attempted, and its outcome;
- **what was disproved, with evidence** — the field that would have caught fact 1,
  where "concurrency causes the stalls" was an `INFERENCE` recorded as a `FACT`;
- what must not be retried, and why;
- blocked items and the exact blocker;
- the next action, and the evidence that would settle it.

**Stale by construction.** The generated span records the commit it describes.
When `HEAD` moves it is stale by definition — a `git rev-parse HEAD` comparison,
no freshness heuristic and no judgment.

Unknown 4 applies: using `AGENTS.md` to carry state extends a convention meant
for instructions. If that proves unstable, the fallback is a sibling generated
file referenced from `AGENTS.md`, not a bespoke artifact type.

### `CONT-NAG-001` — Adopt existing enforcement; state each layer's real strength

Four layers, none built here.

1. **`cog --check` inside validation** — runs wherever validation runs.
   *Stops:* any workflow consuming the validation report. *Bypass:* editing the
   validator, itself a tracked and reviewed change.
2. **Harness session-end hook** — a deterministic script executed by the harness
   rather than the model, failing when the continuity artifact is absent or
   stale. This is the nag: unconditional, unsuppressible by the model, zero
   tokens because it is code. *Stops:* an agent ending a session silently.
   *Bypass:* editing the settings file (Unknown 2).
3. **`pre-commit` framework** — runs the drift check before a commit exists.
   *Stops:* honest omission at the point of change. *Bypass:* `--no-verify` or
   removing the hook. Useful; not a control, and must not be described as one.
4. **CI required status check, all-Python** — the only layer an agent with local
   write access cannot defeat, because it does not run on the agent's machine.
   Blocked on Unknown 1 (whether a CI service will exist).

   **`danger-js` is rejected.** The owner fixed Python as the implementation
   language and does not want a second toolchain. Two independent models were
   asked to find the Python equivalent and prove it; the resulting stack, with
   licences verified against PyPI on 2026-07-30:

   1. **Enforcement:** a workflow step running `python -m cogapp --check -c --diff`
      over the documentation set, plus the staleness script. A non-zero exit fails
      the job; the job made a **required status check** blocks the merge. Pure
      Python, no added dependency.
   2. **Visible report:** write the result, including the `--diff` output on
      failure, to `$GITHUB_STEP_SUMMARY`. Zero dependencies.
   3. **The nag:** on failure only, post or update one comment via the `gh` CLI,
      which is preinstalled on GitHub-hosted runners, so no package is added.

   Rejected with reasons: `reviewdog` is a Go binary — a third toolchain, the
   exact objection that removed `danger-js`. `danger-python` last released v0.1 in
   2020 and its own README requires installing Node's `danger` first, so it does
   not avoid Node at all. **`PyGithub` is LGPL** (classifier confirmed on PyPI for
   2.9.1) — copyleft, and wrong for a source-available, all-rights-reserved
   product preserving commercial optionality.

   If comment logic ever outgrows the `gh` CLI, use **`ghapi` 2.0.4, Apache-2.0**
   (verified on PyPI). One reviewer recommended `githubkit` as MIT; PyPI publishes
   **no licence field or classifier** for it, so that claim is `UNVERIFIED` and
   `ghapi` is preferred until it is checked.

**What is lost versus `danger-js`, stated rather than glossed:** ready-made
pull-request inspection helpers, its plugin ecosystem, and its established
message-formatting conventions. Each becomes Python we write and maintain. The
trade is accepted deliberately: one toolchain, verified licences, and every check
computed by the language `LANG-PRIMARY-001` fixes.

Layer 4 is the only honest "cannot be bypassed." Layers 1–3 raise cost and catch
omission; they do not defeat intent.

Per Conflict 4, `danger-js` is development-time CI tooling and not a Ranex
component under `LANG-PRIMARY-001`. If the owner prefers to avoid a Node
toolchain entirely, the same role is achievable with a Python CI step at some loss
of ready-made pull-request integration; that is an owner choice, not a technical
blocker.

**Tokenomics.** Every layer is a script or an existing tool. Marginal token cost
per session is zero. The only token-consuming mechanism, Option C, is confined to
non-blocking prose review — inverting today's arrangement, where the expensive
fallible mechanism is the only one there is.

## Dependency and file-structure impact

New development dependencies: `cogapp` (MIT), `pre-commit`, and `danger-js` only
if layer 4 proceeds with Node. New files: `AGENTS.md` with `cog` spans,
`.pre-commit-config.yaml`, a CI workflow, and small value-computing functions
beside the existing generator. No module boundary changes; hook scripts must not
import product code.

## Data, state, event, and transaction impact

None. No state axis, transition, or event changes. The continuity artifact holds
no canonical state and confers no authority.

## Security, privacy, and secrets

The continuity artifact records paths, decision identifiers, and validation status
— never credentials or evidence contents; the uncommitted-paths list records paths
only. Hook scripts and `cog` spans execute code automatically and are therefore
supply-chain surface: pin both tools, register their licences in the licensing
manifest — an obligation `ADR-0014` v1.1.0 records as currently unmet for
existing dependencies — and forbid network access at generation time.

## Compatibility, migration, rollback, and upstream sync

Additive. `docs/HANDOFF.md` is retained as prose history, demoted from mechanism,
and its false stall claim corrected on acceptance rather than carried forward.
Rollback is removal of the spans, the check invocation, and the hooks. No upstream
interaction.

## Operations, backup, and recovery

No runtime. A hook failing for infrastructure reasons must be distinguishable
from a genuine drift failure; an infrastructure fault reported as a subject
failure is the defect class capability assessment separates at level 4.

## Predeclared acceptance tests

1. **Generated spans cannot drift.** Hand-edit a `cog` span; `cog --check` and
   validation fail. Restore; both pass.
2. **The two real defects are caught.** Reintroduce "13 accepted ADRs" and "57
   provisions" inside spans; both fail. A regression test against measured
   history, not a hypothetical.
3. **Stale continuity artifact blocks.** Generate it, commit anything, re-run:
   stale by construction, session-end check fails.
4. **Absent artifact blocks.** With no continuity artifact, the check fails
   rather than passing silently.
5. **No escape hatches.** No variable, flag, or config key skips the drift check;
   a search for a waiver mechanism finds none.
6. **A disproved claim is representable and labelled.** The disproved-claims field
   accepts the stall correction with `epistemic_status: FACT` and its evidence,
   and rejects an empty evidence set for a `FACT`, inheriting the rule already
   enforced in `review-observation-v1`.
7. **Zero token cost.** The session-end and pre-commit paths invoke no model.
8. **Honest strength stated.** Each layer's documentation states what it stops and
   how it can be bypassed. A layer described as unbypassable while running on the
   agent's own machine fails this test.
9. **Nothing was built that a tool provides.** For each provision, the tool or
   convention adopted is named with its licence and version. A provision
   implementing behaviour available in a maintained tool fails this test.

## Specialist review

A security review of automatically-executing hook scripts and `cog` spans is owed
before layers 2–4 are enabled, and a licence review is owed for each added
dependency. Neither is owed before acceptance.

## Independent challenge

The first draft was challenged and largely demolished: three of four provisions
became adoptions and one bespoke sub-mechanism was dropped. This revision has not
yet been challenged. Attention is invited to whether `AGENTS.md` can carry state
without abusing the convention (Unknown 4), and whether layer 2 is as
unsuppressible as claimed. The author's record this session includes three
unverified claims caught by others, one inside an accepted ADR, which is why this
section is not a formality.

## Reconciliation

Open, none blocking acceptance: Unknown 1 blocks layer 4; Unknown 2 bounds layer
2; a census of machine-recomputable claims is required before coverage can be
stated; and Unknown 4 may redirect the continuity artifact to a sibling file.

## Human decision requested

Accept, amend, or reject:

1. **`CONT-GENERATE-001`** — adopt `cog` for generated documentation spans.
2. **`CONT-DRIFT-001`** — drift becomes a validation failure via `cog --check`,
   with no waiver; the bespoke prose-claim extractor is dropped.
3. **`CONT-SESSION-001`** — adopt `AGENTS.md` as the continuity location, with a
   generated span plus a fixed authored field list carrying epistemic status.
4. **`CONT-NAG-001`** — adopt existing enforcement in four layers, each
   documented with its real strength.

The owner should specifically confirm: whether a Node toolchain is acceptable for
`danger-js` in CI or a Python equivalent is preferred; and whether layer 3 is
wanted despite being trivially bypassable.
