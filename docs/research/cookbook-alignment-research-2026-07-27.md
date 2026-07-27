# Cookbook-to-Ranex alignment research

**Date:** 2026-07-27
**Decision status:** design-time recommendation; no Ranex runtime exists yet
**Ranex revision reviewed:** `7f1e2ac91e6a7eeb601f1ef64901a858b8ce8819`
**Cookbook revision reviewed:** `7cbdb7e5fdcf48c4cef4067d9f78e17e6283e2de`
**Current upstream Hermes revision checked:** `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`
**Primary Ranex authority:** `RANEX_IMPLEMENTATION_GUIDE.md`
**Supporting research reviewed:** `docs/research/gemini-research.md`
**Independent design review:** blocked; the configured reviewer route was unavailable

## Executive answer

Cookbook is aligned with Ranex at the **operating-principle level**, but not at the
**implementation level**.

Ranex should reuse these Cookbook ideas:

1. variable agents require a stable process;
2. work must be written for a stranger before assignment;
3. makers must not approve their own work;
4. evidence and verdicts are different records;
5. state-changing decisions need an auditable path;
6. missing or conflicting proof must stop high-risk transitions;
7. evaluations need predeclared tests, independent checking, and visible limitations.

Ranex should modify Cookbook's literal roles, static manual, one-owner change door, and
restaurant vocabulary into typed, versioned, project-scoped policies and authorities.
It should reject Cookbook's current scripts as a production foundation. Those scripts
are experiments around prompts and prose checks, not an isolated, durable, typed
multi-agent control plane.

The owner has also fixed an important product boundary: Cookbook's reviewed delivery
path is tied to Claude Code, and this limitation is part of the move to Hermes. Ranex
must own its handbook and enforcement outside any worker harness. It should compile
governed, current context into whichever worker or model is selected, then measure
both instruction-level compliance and whole-workflow effectiveness.

Ranex also owns the Hermes fork. Therefore, “modular” means a batteries-included
Ranex core whose first-party components ship together behind stable internal
interfaces. It does **not** mean implementing scoring or other required capabilities
as optional plugins that users install into an independent Hermes application.

The current Ranex guide is the stronger architecture. It already separates control,
execution, and evidence; makes model output advisory; and proposes typed gates,
project isolation, context packets, and exact-commit completion permits
(`RANEX_IMPLEMENTATION_GUIDE.md:236-258`, `:340-445`, `:3882-4810`,
`:4814-5123`).

However, implementation should not begin from the guide exactly as written. Its state
model is now canonical in prose, and its branch and repository decisions are clearer.
Nine internal contracts still conflict: governance-state versus rule-stage typing,
role IDs, configuration/state paths, worktree execution, run-ID types, transactional
authority, gate sequencing, profile creation, and qualification protocol. The owner
has separately superseded its plugin-first contained-package architecture with
baked-in internal modules. Those are specification defects, not editorial details.
The first build step should therefore be a **contract-normalization slice**, followed
by one thin end-to-end workflow. The nineteen numbered phases should remain a
capability checklist; implementation order should follow a corrected dependency graph
derived from the guide's 22-entry PR sequence.

## How to read this report

Every material statement has one of five statuses:

| Status | Meaning |
|---|---|
| **FACT** | Directly observed in a cited local file, repository state, or primary source. |
| **INFERENCE** | The stated conclusion follows from facts, but is not directly asserted by a source. |
| **PROPOSAL** | A recommended design or test. It is not yet implemented or proven in Ranex. |
| **UNKNOWN** | Evidence is missing, conflicting, or too weak to decide safely. |
| **OWNER REQUIREMENT** | Product direction supplied by the owner; implementation still requires proof. |

The reuse labels mean:

| Label | Meaning |
|---|---|
| **REUSE** | Carry the principle into Ranex with only domain-neutral wording. |
| **MODIFY** | Preserve the intent, but change the mechanism or scope. |
| **REJECT** | Do not make this part of the Ranex baseline. |
| **DEFER** | Keep as a research option until a named test justifies it. |

For this report, **mature** does not mean “proven effective in Ranex.” A process is
mature enough to adopt as a baseline only when its mechanism is explicit, its
failure behavior is known, its result is inspectable, and it has either a stable
standard/production implementation or support from more than one independent primary
source. A Cookbook-only script is local evidence, not mature infrastructure. A
plausible design with no Ranex trial remains a **PROPOSAL**. Missing or conflicting
evidence stays in the fog register until its named acceptance test passes.

## Scope and method

### Questions asked

This review asked:

1. What problem is Cookbook actually trying to solve?
2. Which of its theories have concrete supporting evidence?
3. Which of its processes are mature enough to carry into Ranex?
4. Which parts are metaphor, local convention, experiment, or unfinished work?
5. Where do Cookbook, the Ranex guide, and the Gemini research agree or conflict?
6. What must be proven before implementation choices become hard to reverse?

### Evidence reviewed

**FACT — Ranex.** The full 7,338-line implementation guide and the full 302-line
Gemini research note were read. At the reviewed revision, Ranex has no runtime
source, schemas, tests, or configuration; its tracked files are design, research,
licensing, and metadata. This report therefore evaluates internal coherence and
prior art; it does not claim runtime effectiveness.

**FACT — Cookbook.** All 51 chapters, the main status and hole registers, evaluation
reports, relevant research notes, plugin files, and `press/` scripts were inspected.
The Cookbook checkout is on `main`, one local commit ahead of `origin/main`, and was
clean when inspected.

**FACT — external evidence.** Primary specifications, official documentation, and
original research papers were used where available. External sources were accessed
on 2026-07-27 and are linked directly in the source register.

### Evidence hierarchy used

For a claim about what the local systems contain:

1. executable code or repository state;
2. the authoritative local design document;
3. a status or research note;
4. prose claims without a matching implementation.

For a claim about a general technique:

1. standard or official specification;
2. original research;
3. official engineering guidance;
4. a secondary summary.

This hierarchy matters because Cookbook sometimes has two current-looking files that
disagree. For example, `cookbook/CONTENTS.md:3-5` says nothing has been written,
while `cookbook/README.md:3-5` says all 51 chapters are written and bound.
A Ranex worker must not guess which is fresher. The context compiler must expose
source precedence, revision, and a conflict state.

## Evidence inventory

| Evidence | What it establishes | Strength and limitation |
|---|---|---|
| `RANEX_IMPLEMENTATION_GUIDE.md:183-303` | Ranex's objective, operating principle, definition of done, and non-goals. | Primary design authority; not implemented evidence. |
| `RANEX_IMPLEMENTATION_GUIDE.md:340-445` | Control, execution, and evidence planes; typed roles and authority. | Strong architectural separation; later role IDs drift. |
| `RANEX_IMPLEMENTATION_GUIDE.md:2174-2777` | Plugin-first package, schemas, canonical state, model, and route configuration. | Detailed proposal; its plugin-first packaging boundary is superseded by the owner and its paths conflict with later canonical paths. |
| `RANEX_IMPLEMENTATION_GUIDE.md:3107-3880` | Adapter execution, sandboxing, Kanban state, and completion permits. | Good enforcement intent; the numbered phases introduce permit use before the gate engine. |
| `RANEX_IMPLEMENTATION_GUIDE.md:3882-4812` | Context packets, epistemic state, gates, artifacts, and ledger. | Closest part to a deterministic kernel; the atomic storage boundary remains incomplete. |
| `RANEX_IMPLEMENTATION_GUIDE.md:4814-5533` | Project isolation and agent profiles. | Strong isolation objective; four profiles are created in two phases. |
| `RANEX_IMPLEMENTATION_GUIDE.md:5838-6253` | Model qualification and probation. | Useful lane; evaluation design is not yet strong enough for promotion claims. |
| `RANEX_IMPLEMENTATION_GUIDE.md:6255-7202` | Operations, upstream sync, canonical configuration, implementation sequence, and unresolved decisions. | Good operational breadth; repository and branch intent are now clearer, but remain unexecuted. |
| `docs/research/gemini-research.md` | Candidate approaches for routing, context, MCP, and isolation. | No bibliography or inline citations. Useful discovery map, not decision proof. |
| `cookbook/README.md:3-28` | Cookbook purpose, review claims, and plugin boundary. | Clear scope; explicitly says the plugin contains one smoke rule only. |
| `cookbook/CONTENTS.md:14-60` | Variable workers, stable process, one change path, and three portability piles. | Strong conceptual framing; literal static-manual claim needs modification. |
| `cookbook/CONTENTS.md:118-138` | Instructions versus current snapshot versus append-only history. | Valuable distinctions; discarding old snapshots is unsafe for Ranex audit needs. |
| `cookbook/CONTENTS.md:216-267` | Roles justified by failed promises; maker/checker separation; fail closed. | Reusable invariants; seven roles and three people are metaphor-specific. |
| `cookbook/CONTENTS.md:287-304` | Method and outcome are checked separately. | Useful matrix; “taster's word is final” conflicts with Ranex authority. |
| `cookbook/book/12-the-operations-log.md:5-53` | Append-only corrections, seven stamps, decisions, and evidence/verdict separation. | Strong record model; still prose rather than a durable implementation. |
| `cookbook/book/29-when-one-cook-is-not-enough.md:11-49` | Write a stranger-ready job; coordinator does not become worker. | Directly aligned with scoped context packets and role boundaries. |
| `cookbook/book/30-two-people-working-at-once-without-colliding.md:26-56` | Separate workspaces, one responsible worker, independent checks. | Aligned with worktrees; does not itself prove collision safety. |
| `cookbook/book/37-knowing-which-restaurant-you-are-standing-in.md:11-25` | Shared instructions and isolated local records. | Correct isolation intent; policy travel needs explicit scope, not an absolute ban. |
| `cookbook/press/brief_contract.py:1-28` | One eight-field work packet shared by producer and consumers. | A useful contract prototype; too small for Ranex's full provenance needs. |
| `cookbook/research/proof-over-authority.md:118-196` | Predeclared acceptance tests, independent checks, measured runs, expertise as evidence. | Strong method; the note admits thin adversarial and source-quality evidence. |
| `cookbook/research/skill-eval-framework-evidence-audit.md:215-240`, `:253-307`, `:334-362` | Matched baselines, deterministic-first grading, isolated repeated trials, holdout protection, evaluator qualification, and `INCONCLUSIVE`. | Stronger than the current Ranex probation design; still design guidance, not a completed Ranex evaluation. |
| `cookbook/showdown2/RESULTS.md:41-58`, `:82-109`, `:176-184` | Hidden answer key, recomputable scoring, adversarial checks, and limitations. | Useful evaluation mechanics; only one run per model/level and one level absent. |
| `cookbook/KNOWN-HOLES.md` | Open gaps in override, serving, rejection, locks, drift, logging, and staffing. | Honest fog register; confirms the method is unfinished. |
| `cookbook/WHERE-WE-ARE.md` | Dated narrative status, issue graph, sandbox, and evaluation work. | Useful snapshot with explicitly superseded sections; it is not a generated current-state view. |
| `cookbook/plugins/chain-standards/hooks-handlers/session-start.sh:3-15` | Plugin behavior is prompt injection of a smoke rule. | Proves delivery, not enforcement or installation of the full book. |
| `cookbook/press/print.py:265-305` | Current outside-model runner behavior. | Persistent process, broad access, and no enforced runtime isolation visible here. |
| `cookbook/press/test_printer_reach.py` | A real CLI seam with independently authored baseline and sad-path tests. | Strongest executable testing pattern in Cookbook; narrow in scope. |

## What Ranex is building

**FACT.** Ranex is not a cookbook application. It is a local, one-host
multi-agent software-engineering operating system built around Hermes. Its intended
workflow covers intake, research, planning, implementation, independent review,
testing, human decisions, evidence, remote control, project isolation, recovery, and
upstream maintenance (`RANEX_IMPLEMENTATION_GUIDE.md:183-215`, `:260-303`,
`:6255-6650`).

**FACT.** The guide already states the essential safety boundary:
model output is a proposal; deterministic gates and human decisions authorize state
transitions (`RANEX_IMPLEMENTATION_GUIDE.md:236-258`, `:430-445`).

**INFERENCE.** “Deterministic multi-agent system” should therefore mean:

- deterministic validation of inputs, authority, state transitions, artifacts, and
  side effects;
- reproducible assembly of the same versioned context for the same task state;
- explicit handling of stochastic or conflicting agent output;
- never a claim that the agents themselves return identical answers.

That distinction should appear in every Ranex architecture summary. It prevents an
unprovable product promise.

## Owner-fixed boundary: harness-independent rules and measurable effectiveness

**OWNER REQUIREMENT.** Ranex must not depend on Claude Code to store, deliver, or
enforce its operating rules. The reviewed Cookbook plugin is a Claude Code
session-start prompt hook, and Cookbook states that it currently carries only one
smoke rule (`cookbook/README.md:21-28`;
`cookbook/plugins/chain-standards/hooks-handlers/session-start.sh:3-15`).

**PROPOSAL.** The Ranex control plane built on Hermes should own a versioned
instruction registry and compile applicable instructions into a worker-neutral
packet. Claude Code, Codex, another model CLI, or a future harness becomes an
execution adapter. No adapter becomes the source of truth.

**FACT.** The current guide now identifies Ranex as the owned software fork that
adopts and evolves Hermes in place (`RANEX_IMPLEMENTATION_GUIDE.md:44-74`,
`:183-196`, `:913-932`).

**OWNER REQUIREMENT — architecture boundary.** Deterministic scoring is a Ranex
first-party internal module built into the Hermes-derived product. It is not an
optional plugin that a user installs into an independent Hermes application, and it
is not logic embedded in a model prompt or worker harness.

**PROPOSAL.** The scoring implementation can evolve behind an internal interface;
the kernel owns its result contract and authority boundary.

**OWNER REQUIREMENT — modular core.** Ranex must keep its inherited Hermes core
modular by default because Ranex owns the fork. Major capabilities ship together as
first-party internal modules in the Ranex distribution. Context selection,
instructions, scoring, routing, providers, harnesses, sandboxes, reviewers, and
remote surfaces must be replaceable behind stable internal contracts so Ranex can
experiment without rewriting the agent loop.

This target is a **batteries-included modular monolith**, not a marketplace of
required plugins and not a fleet of microservices. A composition root selects and
wires only modules already shipped and reviewed with the Ranex release. Runtime
activation and canarying are experiment controls; they are not arbitrary code
installation.

**OWNER REQUIREMENT — guide amendment required.** Phase 7 still directs implementers
to build the office as a plugin and move into core only if the extension surface is
insufficient (`RANEX_IMPLEMENTATION_GUIDE.md:2174-2267`, `:2510-2533`). That
instruction conflicts with the owned-core direction and must be amended before Phase
7 or its matching implementation PR begins.

| Boundary | Responsibility |
|---|---|
| Ranex composition root | Builds a validated graph from the baked-in module catalog; binds configuration, implementations, and lifecycle without business logic. |
| Non-replaceable Ranex kernel | Canonical identity, capability broker, authority, legal state transitions, atomic event/outbox writes, and permit consumption. |
| First-party internal modules | Instructions, packet compilation, evidence normalization, scoring, routing, providers, reviewers, remotes, and projections shipped with Ranex. |
| Effect adapters | Harnesses, sandboxes, files, databases, and remote APIs accessed through typed kernel ports without owning policy or score semantics. |
| Upstream compatibility facade | Contains inherited Hermes interfaces and migration shims so upstream sync does not leak through every Ranex module. |
| Optional external extension bridge | A separate, lower-trust edge that may expose selected Ranex APIs later; never the composition mechanism for required core features. |

The scorer may be replaceable. The result schema, evidence binding, hard-gate
semantics, and authority to promote or release are kernel contracts. A candidate
scorer cannot qualify itself, activate itself, write its own passing evidence, or
issue a permit.

### Why the existing Hermes plugin loader is not the target

**FACT.** Current upstream Hermes already describes its core as a narrow waist and
states that capability should live at the edges. Its official plugin system discovers
bundled, user, project, and Python entry-point plugins; general third-party plugins
are opt-in; and its context API registers tools, hooks, commands, skills, platforms,
and several provider types. This is visible in the upstream
[development rules](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/AGENTS.md),
[plugin guide](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/website/docs/user-guide/features/plugins.md),
and [plugin manager](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/hermes_cli/plugins.py).

**FACT.** That plugin system is designed to load user, project, and pip-installed
extensions. Its ordinary hooks are non-blocking: errors are logged instead of
stopping the agent. Those are reasonable external-extension semantics. They are not
sufficient for required internal state, authority, scoring, or gate components.

**OWNER REQUIREMENT — architecture interpretation.** Ranex will not make its internal
architecture depend on users installing plugins. It will refactor the fork into
stable internal ports and first-party modules, then keep any inherited external
plugin system behind a separate compatibility bridge.

Two mature examples support this distinction:

- [VS Code's extension API](https://code.visualstudio.com/api/) states that many core
  product features are built as extensions while still shipping as one product.
- [OpenTelemetry Collector distributions](https://opentelemetry.io/docs/collector/distributions/)
  bake a declared set of components into a distribution. Its
  [configuration model](https://opentelemetry.io/docs/collector/configuration/)
  separates “available in the distribution” from “enabled in this service pipeline.”

They are prior art for a built-in component architecture. They do not prove Ranex's
specific module boundaries, safety, or runtime behavior.

### Internal module contract

Every first-party Ranex module should have a validated, content-addressed descriptor:

| Field | Purpose |
|---|---|
| `module_id`, `code_revision`, `digest` | Stable identity and exact Ranex-shipped implementation. |
| `interface` and `interface_version` | Narrow internal port implemented by the module. |
| `factory` | Side-effect-free construction entry used only by the composition root. |
| `required_capabilities` | Kernel ports required for files, network, models, secret handles, commands, events, or state; absence means denial. |
| `config_schema` and `config_digest` | Typed configuration bound to the evaluated module condition. |
| `state_schema` and `migrations` | Versioned module-owned state with forward, recovery, rollback, and retirement rules. |
| `consumes` and `emits` | Versioned event and command schemas; undeclared traffic is rejected. |
| `dependencies` and `conflicts` | Explicit module graph and deterministic resolution. |
| `lifecycle` and `health` | Initialize, start, ready, drain, stop, recover, and retire behavior. |
| `side_effect_contract` | Idempotency, retry, timeout, compensation, and evidence requirements. |
| `qualification` | Fixture-suite digest, allowed project/risk lanes, scorecard, expiry, and reviewer decision. |
| `owner` and `activation_scope` | Human governor and the projects, roles, tasks, or canary percentage where activation is legal. |

Minimum release and activation lifecycle:

```text
PACKAGED
  -> DISABLED
  -> QUALIFIED
  -> CANARY
  -> ACTIVE | RESTRICTED
  -> QUARANTINED
  -> RETIRED
```

Packaging a module in Ranex does not silently activate it. The default release profile
explicitly names which baked-in modules are active. A module version moves forward
only through a recorded kernel transition. A new digest returns to qualification.
Retirement happens through a Ranex release and preserves evidence, decisions,
state-migration records, and historical replay metadata.

For cheap experiments:

- choose another baked-in implementation through a versioned composition profile;
- activate it only for a declared project, task stratum, or canary percentage;
- compare the exact module digest and config against a frozen disabled baseline;
- broker state changes and side effects through kernel commands;
- keep pure first-party modules in the modular monolith where practical;
- place effectful worker, harness, or sandbox adapters behind process isolation when
  their threat and failure model requires it;
- quarantine a failed module or restore the prior release profile without corrupting
  workflow state;
- promote only after its scorecard passes; never let the module consume its own
  evaluation.

Internal modularity is about ownership, boundaries, and replaceability. It does not
require every component to be dynamically loaded or placed in another process.

### Atomic instruction registry

Each enforceable instruction should be one addressable record, not only a paragraph
inside a handbook:

| Field | Purpose |
|---|---|
| `instruction_id` | Stable, domain-neutral identity that survives wording changes. |
| `revision` and `digest` | Exact text and semantics evaluated in a run. |
| `status` | Draft, active, deprecated, or retired. |
| `scope` | Global, project, technology, risk, role, task, or emergency. |
| `applicability` | Deterministic predicate and required inputs. |
| `precedence` | How conflicts are detected and which authority may resolve them. |
| `instruction_text` | Human- and model-readable requirement. |
| `rationale` and `source_refs` | Why the instruction exists and the evidence or decision that introduced it. |
| `enforcement` | Prompt guidance, deterministic guard, or both. |
| `checker` | ID, kind, version, code digest, fixture-suite digest, and qualification state. |
| `required_evidence` | Artifact or event needed to score the instruction. |
| `subject_binding` | Project, work item, run, base/head commit, workspace, and packet identity to which evidence applies. |
| `severity` and `failure_code` | Advisory, blocking, or catastrophic classification with a stable failed outcome. |
| `coverage_state` | `QUALIFIED`, `UNCALIBRATED`, or `UNCHECKED`; uncovered rules never appear enforced. |
| `owner` | Human authority responsible for changing it. |
| `effective_at` / `expires_at` / `review_at` | Activation, temporary-rule, and mandatory review bounds. |
| `supersedes` | Traceable instruction history without ID reuse. |

**PROPOSAL.** A handbook page should be generated from these records, or refer to
them by stable ID. A deterministic registry check should reject:

- duplicate active IDs;
- missing checkers for blocking observable rules;
- overlapping applicability with unresolved precedence;
- active references to retired records;
- changed instruction text without a revision and digest change;
- a packet that cannot account for every applicable blocking instruction.

### Effectiveness has two phases

#### Phase 1 — instruction reach and compliance

Before asking whether Ranex improves software outcomes, prove that each activated
instruction reached the intended worker and that observable requirements were
followed.

For every instruction/run pair, record:

- applicable or not applicable, with the predicate result;
- delivered or missing, with packet digest;
- followed, violated, unknown, or conflicted;
- checker version and frozen evidence;
- whether a deterministic guard prevented a violation;
- whether a human waiver applied.

A packet digest and delivery receipt prove that Ranex delivered exact bytes into the
harness. They do not prove model attention, understanding, or causation. Observable
behavior and outcome evaluation score those separate claims.

Deterministic graders should operate on frozen artifacts wherever the claim is
mechanical: paths, commits, schemas, transitions, test exit status, actor identity,
packet contents, permit subject, and side-effect count. An agent grader may assess
semantic quality, but its result remains a versioned evaluation with calibration and
uncertainty.

#### Phase 2 — outcome lift against a baseline

Instruction compliance does not prove the process is useful. Compare the same task
distribution under:

- a frozen baseline workflow without the Ranex component being tested; and
- the frozen Ranex workflow.

Use repeated, paired trials and a holdout not used to tune prompts, instructions,
routes, or thresholds. Randomize ordering where carry-over could matter. Report the
distribution and uncertainty because agent outputs remain stochastic even when the
measurement procedure is deterministic.

This follows Cookbook's strongest evaluation audit, which requires external evaluator
separation, matched task-level comparisons, deterministic-first grading, isolated
environments, locked holdouts, repeated task-clustered trials, and separate correctness,
safety, cost, and latency gates
(`cookbook/research/skill-eval-framework-evidence-audit.md:215-240`).
[Anthropic's agent-evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
likewise distinguishes tasks from repeated trials, recommends reproducible code graders
where possible, and requires calibration for model graders.

The scorecard must retain separate dimensions:

| Dimension | Example measures |
|---|---|
| Quality | acceptance-test pass, defect escape, reviewer-confirmed correctness |
| Safety and governance | unauthorized transitions, secret leakage, invalid permit use |
| Cost | model, tool, compute, and human-review cost |
| Latency | queue, execution, gate, and end-to-end tail latency |
| Rework | retries, rejected submissions, reopened work, correction cycles |
| Owner intervention | decisions, recoveries, clarifications, and manual repairs |
| Context freshness | stale, missing, conflicting, or wrong-project inputs |

Catastrophic outcomes are hard gates, not weights. Zero secret exfiltration cannot be
averaged with lower cost. Zero unauthorized irreversible transitions cannot be
hidden by a higher quality score. For non-catastrophic dimensions, show the vector
and trade-offs; do not collapse everything into one weighted number.

#### Deterministic measurement contract

The word **score** covers three different things. Ranex must keep them separate:

| Plane | Evaluation unit | Deterministic output | Authority |
|---|---|---|---|
| Instrument soundness | checker version × frozen fixture-suite digest | `QUALIFIED` or `QUARANTINED` | Decides whether the checker may be used; never approves work. |
| Run conformance | instruction revision × frozen subject/evidence snapshot | `PASS`, registered `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, or `CHECKER_FAULT` | Only qualified deterministic checks or an explicit human decision may satisfy a blocking gate. |
| Workflow effectiveness | end-to-end task × frozen condition × trial | metric vector, paired difference, and uncertainty | Informs human approval or restriction of an exact workflow/route configuration. |

**PROPOSAL.** The same normalized evidence, registry revisions, fixture-suite digest,
and checker binaries must produce byte-identical conformance results. This makes the
measurement instrument reproducible. It does not make the agent outcome reproducible.

Report counts beside every rate. Minimum instruction-level measures are:

```text
reach_i =
  exact-revision deliveries for applicable instruction i
  / applicable trials for instruction i

conformance_i =
  PASS results for instruction i
  / applicable trials for instruction i

unresolved_i =
  (UNKNOWN + CONFLICT + CHECKER_FAULT + missing evidence)
  / applicable trials for instruction i

violation_recall_i =
  seeded violations correctly blocked
  / seeded violation attempts

false_positive_rate_i =
  valid clean fixtures incorrectly blocked
  / valid clean fixtures

paired_outcome_lift =
  task-level result with frozen Ranex condition
  - task-level result with matched frozen baseline

cost_per_accepted_task =
  total model + tool + compute + human-review cost
  / accepted end-to-end tasks
```

For a blocking instruction, `UNKNOWN`, `CONFLICT`, `CHECKER_FAULT`, or missing
evidence is not a pass. `NOT_APPLICABLE` requires the recorded applicability proof.
Compliance correlation alone does not prove an instruction caused a better result;
causal claims require a controlled revision comparison, safe ablation, or other
predeclared intervention.

The owner-facing result should be a decision plus the full vector:

- `FAIL` when any predeclared catastrophic gate fires;
- `INCONCLUSIVE` when the instrument, sample, holdout, or evidence is inadequate;
- `RESTRICTED` when hard gates pass only for declared task, project, or risk lanes;
- `PASS` only when all predeclared hard gates and dimension-specific thresholds pass.

No aggregate number may turn `FAIL` or `INCONCLUSIVE` into `PASS`.

#### Component ablations

Change one component at a time after the baseline and whole path are stable:

- one module digest/config enabled versus disabled;
- packet compiler on/off;
- one instruction revision versus another;
- deterministic guard versus prompt-only instruction;
- independent review versus no independent review;
- static route versus candidate router;
- simple file selection versus symbol graph;
- one sandbox profile versus another.

Freeze every other material input. An ablation is safe only if catastrophic gates
remain active in both arms. A component is promoted when its predeclared improvement
survives repeated paired holdout trials without a critical regression in another
scorecard dimension.

## Alignment matrix

| Area | Cookbook position | Ranex position | Decision | Reason |
|---|---|---|---|---|
| Core problem | Variable, memoryless workers; stable result requires stable process (`cookbook/CONTENTS.md:14-27`). | Variable agents operate inside deterministic controls (`RANEX_IMPLEMENTATION_GUIDE.md:236-258`). | **REUSE** | Same central problem and compatible answer. |
| Metaphor | Restaurant = software project; dish = work unit (`cookbook/README.md:3`). | Guide maps “restaurant chain” to one software project and assigns product roles restaurant names (`RANEX_IMPLEMENTATION_GUIDE.md:217-234`). | **MODIFY** | Keep metaphor in owner-facing explanations only. Canonical schemas need domain-neutral terms. |
| Stable manual | Owner changes one static manual through one door (`cookbook/CONTENTS.md:24-38`). | Layered constitutional, role, stage, project, technology, risk, and task rules (`RANEX_IMPLEMENTATION_GUIDE.md:3882-4156`). | **MODIFY** | Stability comes from versioning, scope, precedence, review, and tests, not one monolithic file. |
| Role count | Seven role promises, three essential separations (`cookbook/CONTENTS.md:216-236`). | A larger typed roster and authority matrix (`RANEX_IMPLEMENTATION_GUIDE.md:387-445`). | **MODIFY** | Reuse separation-of-duty constraints, not seven names or a fixed body count. |
| Worker assignment | Write the job for a stranger before choosing the worker (`cookbook/book/29-when-one-cook-is-not-enough.md:11-17`). | Compile a bounded role- and task-specific context packet before dispatch (`RANEX_IMPLEMENTATION_GUIDE.md:4158-4233`). | **REUSE** | This is the strongest direct alignment. |
| Coordinator boundary | Manager reads open work and log but never becomes a worker (`cookbook/book/29-when-one-cook-is-not-enough.md:25-49`). | Duty orchestrator and project supervisor dispatch disposable workers. | **REUSE** | Prevents hidden work and self-review. Emergency human override remains separate. |
| Work isolation | Separate workspaces and one responsible worker (`cookbook/book/30-two-people-working-at-once-without-colliding.md:26-56`). | Per-task worktrees and cross-project canaries (`RANEX_IMPLEMENTATION_GUIDE.md:4814-5123`). | **REUSE** | Git worktrees are the concrete Ranex mechanism. |
| Prompt roles | Most Cookbook enforcement is written instruction. | Ranex proposes schemas, deny-by-default tools, sandboxing, gates, and permits. | **REJECT** as enforcement | A role prompt describes intent; it cannot authorize or technically constrain a side effect. |
| Review authority | Taster's quality verdict is final (`cookbook/CONTENTS.md:287-295`). | Agent output is advisory; deterministic and human gates control transitions. | **REJECT** | An evaluator can be wrong, compromised, stale, or unavailable. Its verdict is evidence. |
| Missing checker | No checker, no service (`cookbook/CONTENTS.md:243-258`). | Blocking unknowns and conflicts fail closed. | **MODIFY** | Fail closed for required gates. Gate depth should still be proportional to trusted risk class. |
| Evidence and verdict | Method, result, and means are separate; evidence differs from verdict. | Typed gate results, content-addressed artifacts, ledger, and permits. | **REUSE** | Ranex makes the distinction enforceable. |
| Current state/history | Rewrite a stocktake; append only to the operations log (`cookbook/CONTENTS.md:121-134`). | SQLite current state plus append-only artifacts and hash-chain ledger. | **MODIFY** | Use rebuildable projections, but retain event history and backups. Do not discard audit-relevant snapshots. |
| Change governance | Fault moves upward; owner alone amends the manual (`cookbook/CONTENTS.md:29-49`). | Typed human decisions, waivers, rule layers, and project policy. | **MODIFY** | Owner/human authority stays for governance and waivers. Routine validated transitions should not need manual action. |
| Knowledge transfer | Instructions travel; local staff and records do not (`cookbook/CONTENTS.md:51-60`; `cookbook/book/37-knowing-which-restaurant-you-are-standing-in.md:11-25`). | Shared base rules plus isolated project knowledge and quarantined learning. | **MODIFY** | Transfer only declared, reviewed, sanitized artifacts. Project policy may travel by explicit owner decision. |
| Model selection | Measured contests choose workers and checkers. | Static routes, fallback order, probation, and promotion. | **REUSE** with stronger tests | Measured selection is right; single-run model contests are insufficient. |
| Scaling trigger | Add management when work exceeds owner attention. | Duty orchestrator, supervisors, queueing, budgets, and project limits. | **MODIFY** | Replace “attention” with observable queue, latency, collision, retry, defect, and cost measures. |
| Implementation asset | Prose, prompt checks, a smoke plugin, and local scripts. | Hermes-derived modular core, built-in first-party modules, local database, adapters, sandboxes, and operational tooling. | **REJECT** as runtime | Borrow tests and language; do not make Cookbook code a Ranex dependency. |

## Mature patterns worth carrying forward

The mature part is the engineering mechanism or evaluation method, not a claim that
Ranex already implements it:

| Mature baseline | Prior art that makes it adoptable | Boundary that remains unproven |
|---|---|---|
| Baked-in modules behind stable internal interfaces | [VS Code](https://code.visualstudio.com/api/) ships many core features as extensions; [OpenTelemetry Collector distributions](https://opentelemetry.io/docs/collector/distributions/) declare their included components and enable them through explicit service configuration. | Ranex's exact kernel, module graph, internal APIs, lifecycle, state migration, and qualification. |
| Versioned, machine-validated contracts | [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) and [RFC 8785 canonical JSON](https://www.rfc-editor.org/rfc/rfc8785) | Ranex's actual schemas, compatibility rules, and canonicalization profile. |
| Content-addressed evidence and provenance | [SLSA provenance v1.2](https://slsa.dev/spec/v1.2/build-provenance) | Which Ranex events and artifacts are authoritative, retained, or derived. |
| Transactional state with replayable workflow history | [SQLite transactions](https://sqlite.org/lang_transaction.html) and [Temporal workflows](https://docs.temporal.io/workflows) | The one-host transaction boundary and whether Ranex needs Temporal. |
| Cross-component run and subject correlation | [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/) and [Trace API](https://opentelemetry.io/docs/specs/otel/trace/) | Ranex's canonical identity tuple and trust boundary. |
| Isolated work units and layered containment | [Git worktrees](https://git-scm.com/docs/git-worktree), [bubblewrap](https://github.com/containers/bubblewrap), and [Docker Engine security](https://docs.docker.com/engine/security/) | The host-specific sandbox profile and proved denial tests. |
| Predeclared, repeated, calibrated evaluation | [OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) and [Anthropic agent-evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | Ranex task corpus, thresholds, trial count, graders, and holdout protection. |
| Small vertical delivery slices with continuous verification | [DORA small-batch guidance](https://dora.dev/capabilities/working-in-small-batches/) and [continuous integration guidance](https://dora.dev/capabilities/continuous-integration/) | The first Ranex tracer and measured service targets. |

### 1. Stable process around variable agents

**FACT.** Cookbook treats different, memoryless workers as the permanent operating
condition (`cookbook/CONTENTS.md:14-27`).

**INFERENCE.** This is more realistic than trying to make one agent persona persistent.
Ranex should persist state, policy, evidence, and work contracts outside the model.
Disposable agents can then be replaced without losing governance state.

### 2. Stranger-ready work packets

**FACT.** Cookbook says to finish the written job before assigning a worker
(`cookbook/book/29-when-one-cook-is-not-enough.md:11-17`). Its
`cookbook/press/brief_contract.py:1-28` also prototypes one packet schema shared by the writer
and readers.

**PROPOSAL.** Ranex should turn this into a content-addressed `TaskPacket` that includes:

- task and project identity;
- authoritative objective and acceptance tests;
- base commit and allowed workspace;
- selected policy revisions and their precedence;
- known facts, assumptions, conflicts, and unknowns;
- allowed tools, network mode, time and cost budgets;
- required artifacts and gates;
- upstream dependencies and prior decisions;
- packet schema version and digest.

The same digest must appear in the dispatch record, agent result, gate evidence, and
completion permit. A packet is not “current context” unless its sources and freshness
rules are machine-checkable.

### 3. Separation of method, result, and system health

**FACT.** Cookbook separates process checking, outcome checking, and fitness checking
(`cookbook/CONTENTS.md:260-278`).

**PROPOSAL.** Ranex should preserve the questions without preserving the role names:

| Question | Ranex evidence |
|---|---|
| Was the authorized method followed? | policy trace, command/event log, packet digest, changed-file scope |
| Is the result correct? | tests, acceptance checks, independent review, customer/human evaluation |
| Is the operating system healthy? | queue, error, retry, isolation, budget, drift, recovery, and provider telemetry |

One agent may advise on more than one question, but the same execution identity must
not both produce work and issue its approval.

### 4. Evidence is not a verdict

**FACT.** Cookbook records both evidence and a conclusion; it also says a maker's note
does not prove completion (`cookbook/book/12-the-operations-log.md:15-35`;
`cookbook/FOR-THE-OWNER.md`).

**PROPOSAL.** Each Ranex gate record should contain:

- the claim being evaluated;
- gate and policy version;
- subject commit and packet digest;
- raw evidence references;
- evaluator identity and independence properties;
- check outcome: `PASS`, registered `FAIL`, `UNKNOWN`, `CONFLICT`,
  `NOT_APPLICABLE`, or `CHECKER_FAULT`;
- reason and any separate, scoped human-waiver reference;
- the authority allowed to consume that outcome.

The raw evidence remains available even when a later gate overturns the verdict.

### 5. Predeclared and adversarial evaluation

**FACT.** Cookbook's best evaluation work hides an answer key, uses recomputable
metrics, seeds contradictions, and reports missed detections
(`cookbook/showdown2/RESULTS.md:41-58`, `:82-109`;
`cookbook/THE-CONTRADICTION-PASS.md`).

**FACT.** Its own report also says the trial count was one per model and level, with
one intended level absent (`cookbook/showdown2/RESULTS.md:176-184`).

**INFERENCE.** The mature principle is not “this model won.” It is:
freeze the test before the result, include sad paths, keep the key away from the
subject, make the score recomputable, and disclose sample limits.

### 6. Fail visibly when proof is unavailable

**FACT.** Cookbook stops service when a required checker is absent
(`cookbook/CONTENTS.md:243-258`). Ranex proposes blocking `UNKNOWN` and `CONFLICT`
outcomes.

**PROPOSAL.** Required high-risk gates should fail closed. Lower-risk work may have a
smaller predeclared gate set, but the dispatcher must not silently downgrade a gate
because a provider, tool, or reviewer is unavailable.

### 7. Real-seam tests

**FACT.** `cookbook/press/test_printer_reach.py` tests an actual CLI boundary, includes
a baseline and a sad path, and was authored separately from the runner it checks.

**PROPOSAL.** Ranex should copy that testing shape. A “sandbox test” must attempt a
forbidden read, write, process, and network action against the real adapter. A
“completion test” must try the external CLI against a stale commit and without a
permit. Unit tests alone cannot prove those boundaries.

## What must not be inherited unchanged

### Cookbook is not currently an enforceable operating system

**FACT.** The installable plugin carries one `pineapple-check` smoke rule, not the
book (`cookbook/README.md:21-28`). Its session-start hook injects text
(`cookbook/plugins/chain-standards/hooks-handlers/session-start.sh:3-15`).

**FACT.** The current runner at `cookbook/press/print.py:265-305` launches an outside
model process. The reviewed code does not establish the isolation, bounded output,
typed result, immutable model revision, or durable workflow guarantees Ranex needs.

**INFERENCE.** Passing the smoke check proves prompt delivery. It does not prove:

- that all policies were delivered;
- that the model followed them;
- that forbidden tools were blocked;
- that the result came from the intended revision;
- that a side effect was authorized;
- that retries are idempotent;
- that evidence is complete.

Ranex should import no Cookbook execution code by default. Any later reuse must pass
the same adapter, schema, isolation, and durability tests as newly written code.

### The metaphor leaks into authority

**FACT.** Cookbook maps a restaurant to one project (`cookbook/README.md:3`).
The Ranex guide instead maps “restaurant chain” to one project, collapsing the
portfolio/project boundary (`RANEX_IMPLEMENTATION_GUIDE.md:217-234`). It also uses
`head-chef`, `implementation-chef`, and `customer-taster` as canonical-looking role IDs
(`RANEX_IMPLEMENTATION_GUIDE.md:6663-6729`).

**INFERENCE.** Two metaphor mappings will cause role and scope errors in schemas,
logs, and user interfaces.

**PROPOSAL.** Use domain-neutral canonical IDs:

- `duty-orchestrator`;
- `project-supervisor`;
- `planner`;
- `implementation-worker`;
- `process-reviewer`;
- `outcome-reviewer`;
- `adversarial-reviewer`;
- `human-governor`.

The UI may display owner-selected restaurant terms. Stored authority must use the
canonical IDs.

### A static manual is too coarse

**FACT.** Cookbook says the manual is static and changes through one owner-controlled
door (`cookbook/CONTENTS.md:24-38`).

**INFERENCE.** A single manual cannot safely represent global constraints,
project-specific policy, language-specific rules, temporary task constraints, and
emergency waivers without either constant editing or hidden exceptions.

**PROPOSAL.** Replace the literal static manual with immutable, versioned rule
packages. A packet's activation manifest should name:

- each package and digest;
- declared scope;
- precedence;
- activation reason;
- conflicts;
- waivers and expiry.

Humans control governance policy and waivers. Deterministic code may apply already
approved policy and routine state transitions.

### A fresh session is not independent evidence

**FACT.** Cookbook often uses a different or fresh agent session as a separate pair
of eyes.

**INFERENCE.** Session freshness alone does not establish independence. Two runs can
share a model family, prompt contamination, mutable source, hidden rationale, or
write access.

**PROPOSAL.** An independence record should state whether the evaluator:

- is a different execution identity;
- did not edit the subject;
- saw no maker rationale before its own verdict;
- used the exact subject commit;
- used a separate context packet;
- is a different model family when policy requires diversity;
- received a locked test or hidden key when appropriate.

## Contradictions and drift found

These conflicts are evidence for machine-checked source precedence, not criticism of
the people or agents who produced the documents.

### Inside Cookbook

| Conflict | Evidence | Ranex lesson |
|---|---|---|
| Book not written versus all chapters bound | `cookbook/CONTENTS.md:3-5` conflicts with `cookbook/README.md:3-5`. | Every source needs status, revision, precedence, and freshness. Conflicts enter packets explicitly. |
| Menu classed as instruction versus local record | `cookbook/CONTENTS.md:118-120` conflicts with `cookbook/press/core-invariants.json:9-10` and `cookbook/book/35-what-a-chain-is.md:27-37`. | Canonical entity types need schema validation, not prose consensus. |
| Eight checklist items versus seven implemented | `cookbook/TASTING-CHECKLIST.md:82-100` adds item 8; `cookbook/press/taste.py:98,110-112` still describes seven and emits `t1` through `t7`. | Policy and checker versions must be coupled and compatibility-tested. |
| Showdown “never run” versus stored results | `cookbook/SHOWDOWN.md:3` conflicts with its result artifacts. | Generated status must derive from execution records. |
| Ten invariants versus eleven registry entries | `cookbook/THE-PRINT-SHOP.md:40` conflicts with `cookbook/press/core-invariants.json`. | Human-readable counts should be generated from the registry. |
| “Working tools ship” versus smoke-rule-only plugin | `cookbook/book/49-what-ships-in-the-box.md:5-15`, `:54-66` conflicts with the implemented boundary admitted by `cookbook/README.md:19-28`. | Treat promised capability and implemented capability as separate, machine-derived states. |

**FACT.** Cookbook already records open gaps for overrides, locks, serving,
rejection, log implementation, drift detection, and staffing
(`cookbook/KNOWN-HOLES.md`). Its dated status snapshot records the registry and
sandbox build as open (`cookbook/WHERE-WE-ARE.md:45-94`).

**INFERENCE.** Cookbook should be treated as active research and a pattern library,
not a settled dependency.

### Inside the Ranex implementation guide

| Conflict | Evidence | Risk | Required resolution |
|---|---|---|---|
| Governance state versus rule stage | The guide declares one uppercase office-governance enum and requires schemas to import it (`RANEX_IMPLEMENTATION_GUIDE.md:2403-2440`, `:4411-4449`), while rule and packet examples use lowercase stages such as `implementation` (`:3938-3971`, `:4116-4173`) and the canonical packet schema accepts any nonempty stage string (`:6851-6890`). | Rule activation, packet validation, and transition gates can interpret the same `stage` field differently. | Define separate typed `governance_state` and `rule_stage` fields with an exhaustive mapping, or use the canonical enum throughout; generate schemas and examples from that choice. |
| Role IDs | The architecture roster uses `coding-worker-standard`, `chief-reviewer`, and `review-challenger` (`RANEX_IMPLEMENTATION_GUIDE.md:387-405`); packet and lane examples use `standard-chef` (`:3556-3577`, `:4116-4154`); canonical configuration uses `implementation-chef`, `chief-code-reviewer`, and `adversarial-reviewer` (`:6663-6729`). | Authority checks can bind the wrong identity or fail open. | One role registry with aliases allowed only at the presentation boundary; generate examples and schemas from it. |
| Configuration and state roots | The orchestration package embeds `config/` under a plugin (`:2184-2246`), Phase 8 writes root `config/` (`:2541-2720`), and canonical files live under `office/config/` (`:6659-6839`). The guide reserves `STATE_HOME` for Ranex-native runtime state (`:508-561`, `:655-689`, `:1374-1385`) but Phase 7 stores the new office database and evidence under compatibility `APP_HOME` (`:2467-2495`). | Different phases can read or back up different configuration and runtime state. | Freeze one config tree and one state-ownership map for database, ledger, evidence, profiles, migration, and backups; schema-test every referenced path. |
| Worktree execution procedure | The guide requires every writing phase and PR to use a pre-created named worktree and branch (`:76-82`), but later steps switch or create branches in place (`:1764-1783`, `:3438-3474`, `:6311-6331`). | An implementer can mutate the primary checkout, collide with an already checked-out branch, or work outside the declared branch. | Define one worktree creation, execution, landing, and cleanup procedure; parameterize phase commands with its validated paths instead of switching branches in place. |
| Permit before gate engine | Phase 11 requires completion guards and a gate permit (`:3712-3766`); the gate engine and permit issuer are created in Phase 13 (`:4369-4806`). The later PR sequence correctly places gates before adapters (`:6958-6990`). | Following phase numbers and following the PR sequence produce different dependency orders; early code may invent a temporary authority path or block. | Declare the PR dependency graph authoritative and implement the gate/permit seam before any external completion mutation. |
| Atomic system of record | Office state uses separate SQLite storage (`:2467-2495`); Kanban remains the durable task queue and lifecycle trail (`:3438-3460`); the evidence ledger is separate (`:4557-4600`); permit consumption and transition must be atomic (`:4738-4756`). | A crash can consume authority or expose “complete” in one plane while another remains pending. | Choose one transactional authority boundary and specify event, outbox, projection, replay, reconciliation, and orphan-permit recovery rules. |
| Duplicate profile creation | Phase 9 creates `office-sol`, `reviewer-hy3`, `challenger-v4-flash`, and `specialist-v4-pro` while verifying providers (`:2819-2849`, `:2957-3013`); Phase 15 creates all four again as blank role profiles (`:5157-5227`). | The later phase can fail, overwrite, or diverge from the earlier profiles. | Separate profile schema creation from provider binding and make profile seeding idempotent. |
| Run-ID type | The lane request and completion guard type `run_id` as an integer (`:3476-3534`, `:3712-3734`), while the result contract and canonical schemas use string IDs such as `run-456` (`:3661-3705`, `:6851-6953`). | Evidence, permits, and adapter runs can fail to join or can bind the wrong identifier. | Define separate canonical IDs if both Kanban numeric IDs and Ranex run IDs are required; generate all types and schemas from one registry. |
| Qualification proof | Phase 17 defines status, metrics, and promotion without paired baselines, repeated trials, holdout separation, confidence/power, or evaluator calibration (`:5838-6253`); it sets thresholds after an initial blind run (`:6066`). | Model promotion can encode noise, leakage, or a favorable first sample. | Predeclare evaluation protocol and thresholds; use repeated paired tasks, frozen holdout, and calibrated grading. |

**OWNER REQUIREMENT — settled interpretation.** The guide's “plugin-first” and
plugin-directory language (`RANEX_IMPLEMENTATION_GUIDE.md:2174-2259`) must not be
implemented as a set of optional packages installed by end users. Required Ranex
capabilities belong to the baked-in module catalog of the owned Hermes fork. Any
external plugin interface is a separate compatibility surface with lower authority.

**FACT.** Revision `7f1e2ac91e6a7eeb601f1ef64901a858b8ce8819` resolved three
findings present in the earlier reviewed draft: it now declares one canonical office
state vocabulary (`RANEX_IMPLEMENTATION_GUIDE.md:2403-2465`, `:4411-4449`), uses a
consistent `develop`/`upstream-sync` branch model (`:1196-1223`, `:6295-6359`), and
defines this repository as the in-place owned fork (`:44-74`, `:913-932`).

**PROPOSAL.** Resolve the nine remaining conflicts in a short canonical contract document
or generated schema set before implementing later phases. Do not allow phase-local
examples to define new state or role identifiers.

### Cookbook versus Ranex

| Tension | Decision |
|---|---|
| Cookbook says a taster's verdict is final; Ranex says models cannot authorize transitions. | Ranex rule wins. Taster/reviewer output is evidence only. |
| Cookbook makes the owner the only manual changer; Ranex needs routine machine transitions. | Humans govern policies, risk, waivers, and hard-to-reverse decisions. Deterministic code applies approved rules. |
| Cookbook says instructions travel unchanged and records never travel. | Use declared scope. Shared policy may travel; project facts remain isolated unless sanitized and explicitly approved. |
| Cookbook treats old stocktakes as disposable. | Ranex retains event history and recoverable backups; current state is a rebuildable projection. |
| Cookbook promotes a seven-role floor. | Ranex enforces promises and separation constraints; it does not encode the number seven. |
| Cookbook uses prose and prompts as the main carrier. | Ranex uses typed, versioned schemas plus prompts as one presentation layer. |

## Reappraisal of the Gemini research note

`docs/research/gemini-research.md` is useful as an idea inventory. It is not adequate
as a proof record because it contains no bibliography or inline source citations.
The following decisions use the original or official sources instead.

| Gemini theme | Primary evidence | Decision for Ranex |
|---|---|---|
| Deterministic staged workflow around agents | [Agentless](https://arxiv.org/abs/2407.01489) uses localization → repair → patch validation and reports 32% at $0.70 on SWE-bench Lite in its current abstract. | **REUSE the shape**, not its benchmark result as a Ranex forecast. Staged, inspectable control is a good baseline. |
| Hard “15–20 turns” degradation threshold and “exponential” cost growth | The Gemini note gives neither a source nor a defined experiment for these claims (`docs/research/gemini-research.md:31-35`). | **UNKNOWN.** Treat context growth, drift, cost, and failure as measurements. Do not encode these numbers or growth law into policy. |
| Repository map and curated context | [Aider's RepoMap](https://aider.chat/docs/repomap.html) uses symbols and graph ranking within a token budget. [DORA](https://dora.dev/capabilities/ai-accessible-internal-data/) recommends specific, current internal context and warns against indiscriminate context loading. | **MODIFY.** Start with deterministic file/symbol/dependency selection and provenance. Prove value against a simpler baseline before adding graph ranking. |
| MCP as universal tool bus | The [MCP architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture) defines host/client/server boundaries, while its [tool security rules](https://modelcontextprotocol.io/specification/2025-11-25/server/tools#security-considerations) still require access control, validation, confirmation, timeouts, and audit logging. | **MODIFY.** MCP may be an adapter protocol. It does not itself provide Ranex authority, isolation, durability, centralized audit, or policy enforcement. |
| Kubernetes plus warm Firecracker microVM pool | The Gemini note claims boot under 5 ms (`docs/research/gemini-research.md:187`); the [Firecracker FAQ](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md#what-is-the-difference-between-firecracker-and-qemu) states a target below 125 ms and requires KVM plus careful host configuration. | **REJECT for one-host v1.** Use bubblewrap first if the threat model and host tests support it; retain Docker only as a separately tested fallback. Revisit microVMs for a demonstrated isolation gap. |
| DeltaBox and Crab rollback as mature infrastructure | [DeltaBox](https://arxiv.org/abs/2605.22781) and [Crab](https://arxiv.org/abs/2604.28138) were first submitted in April–May 2026. Their results are promising research, not established Ranex operations evidence. | **DEFER.** Filesystem/process rollback also cannot undo GitHub, network, database, or notification effects. Use explicit compensations and idempotency keys first. |
| Learned model router | [Conductor](https://arxiv.org/abs/2512.04388), [TRINITY](https://arxiv.org/abs/2512.04695), [LEMON](https://arxiv.org/abs/2605.14483), ALMAS, and Fugu are recent research or product work across different domains. | **DEFER.** Static, explainable routes plus measured probation are the baseline. A learned router must beat them on a frozen holdout after cost and failure penalties. |
| More agent loops and recursive refinement | The recent systems cited above report gains only for their own tasks and conditions. Every added call also adds directly measurable cost and latency and creates another failure point; broader benefit is an **INFERENCE**, not a transferable result. | **DEFER by risk lane.** Add a loop only when a predeclared ablation proves material net value. |

### Corrected conclusion from the Gemini note

**PROPOSAL.** Ranex v1 should prefer:

- a deterministic, typed control kernel;
- static and explainable model routes;
- curated, revisioned context packets;
- real workspace isolation;
- append-only evidence plus rebuildable current state;
- exact-subject, single-use completion authority;
- small vertical slices and repeated production-shaped evaluation.

Kubernetes, microVM pools, learned routers, process checkpoint engines, and blanket
MCP standardization remain research options. None is required to prove the core
Ranex operating model.

## Recommended architecture

### Boundary: deterministic kernel, probabilistic workers

```text
human / GitHub / CLI / phone
             |
             v
      authenticated intake
             |
             v
  +---------------------------+
  | deterministic control     |
  | state machine             |
  | policy + authority        |
  | composition + broker      |
  | packet compiler           |
  | scheduler + budgets       |
  | gate + permit issuer      |
  +---------------------------+
       |                 |
       v                 v
 execution adapters     evidence plane
 sandboxed workspaces   events + artifacts
 agents and tools       traces + projections
       |                 |
       +------ result ---+
             |
             v
  gate evidence -> human decision when required
             |
             v
 authorized side effect / state transition
```

**PROPOSAL.** The control kernel should be the only component allowed to:

- choose a legal next state;
- validate a module and grant its scoped capabilities;
- activate a policy set;
- authorize an execution;
- issue or consume a completion permit;
- record a waiver;
- perform an external state mutation through a typed adapter.

An agent may recommend any of those actions. It may not perform them merely because
its prompt says it has that role.

### Canonical data model

At minimum, define one schema and stable ID for:

- `Project`;
- `WorkItem`;
- `Run`;
- `InternalModuleDescriptor`;
- `ModuleActivation`;
- `ModuleCapabilityGrant`;
- `ExecutionIdentity`;
- `Role`;
- `AuthorityGrant`;
- `PolicyPackage`;
- `PolicyActivation`;
- `TaskPacket`;
- `Artifact`;
- `Claim`;
- `GateEvaluation`;
- `HumanDecision`;
- `Permit`;
- `SideEffect`;
- `RouteEvaluation`;
- `Waiver`.

**PROPOSAL.** [JSON Schema 2020-12](https://json-schema.org/draft/2020-12)
can validate interchange records. [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)
canonical JSON or an equivalently specified encoding should be used before hashing.
[SLSA provenance](https://slsa.dev/spec/v1.2/provenance) is useful prior art for
naming the subject, builder, invocation, and resolved inputs. Ranex need not claim
SLSA compliance to reuse those record shapes.

### State and evidence

**PROPOSAL.**

- Keep append-only domain events and content-addressed artifacts as the audit source.
- Build current SQLite tables as projections that can be regenerated.
- Use transactions for state plus outbox records on the same database boundary.
- Assign idempotency keys to every external side effect.
- Store provider response IDs and artifact references, not secrets or raw credentials.
- Correlate a work item, run, adapter call, gate, and side effect with trace/run IDs.
- Treat [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
  as observability, not tamper resistance.
- Verify the installed SQLite release against the current
  [WAL documentation and limitations](https://sqlite.org/wal.html) before enabling WAL.
- Exercise checkpoint, crash, backup, and restore behavior on the actual host.

**INFERENCE.** A local hash chain is **tamper-evident**, not immutable. A party able
to replace the database, artifact store, and chain anchor can rewrite all three.
Ranex documentation should use “immutable” only for storage that technically enforces
it. Stronger detection requires protected or externally anchored checkpoints plus
restore and reconciliation tests.

### Execution isolation

**FACT.** [Bubblewrap](https://github.com/containers/bubblewrap) describes itself as
a low-level sandbox construction tool; its security depends on the arguments used.
It is not a complete policy by installation alone.

**PROPOSAL.** Define an isolation profile by capability, then test the profile:

- read-only base repository;
- writable task worktree only;
- no secret mounts;
- isolated temporary directory;
- denied network by default;
- explicit destination allowlist when network is required;
- process, time, memory, file-size, and output limits;
- new session and appropriate namespaces;
- immutable adapter argv lists without shell interpolation.

Bubblewrap may be the preferred local mechanism only after those sad-path tests pass
on the target host. Docker can be a fallback with its own acceptance tests.
`none` must not be a silent fallback.

### Context delivery

**PROPOSAL.** The context compiler should:

1. resolve authoritative sources by declared precedence;
2. record source commit, content digest, and observation time;
3. validate freshness rules;
4. detect contradictory facts and emit `CONFLICT`, not pick a favorite;
5. select only role- and task-relevant content;
6. enforce the packet budget visibly;
7. reject silent truncation;
8. block project-private material from another project;
9. attach unresolved unknowns and required research;
10. produce a deterministic manifest even if the final prose rendering changes.

This directly addresses the product need to compensate for stale model knowledge.
“Give the agent more files” is not sufficient context engineering.

### Durable workflow choice

**FACT.** [Temporal](https://docs.temporal.io/) is established prior art for durable,
replayable workflow histories and retryable external activities. It also introduces a
service, SDK, operational model, and deterministic workflow-code constraints.

**UNKNOWN.** It is not yet proven that Ranex's one-host v1 needs Temporal rather than
a smaller built-in Ranex workflow module plus SQLite event/outbox state.

**PROPOSAL.** Build the single-task tracer slice with the smaller design first.
Run crash and retry tests. Adopt Temporal, or another durable engine, only if the
small design fails named recovery or operability criteria that cannot be fixed
without recreating a workflow engine.

## Recommended delivery process

### Replace horizontal construction with tracer slices

The guide's phases are valuable as a completeness checklist. Building every storage,
role, profile, sandbox, gate, remote interface, and operations feature in horizontal
order postpones proof that they compose.

**PROPOSAL.** Use this sequence:

1. **Normalize contracts.** Freeze canonical state, roles, paths, authorities,
   transition table, subject identity, gate outcomes, module boundary, and branch
   topology.
2. **Build one safe modular path.** One local issue, one project, one planner, one
   worker, one reviewer, one test command, one scorer module, one human approval, and
   one completion adapter.
3. **Prove the sad paths.** Wrong project, stale commit, invalid transition,
   self-review, missing evidence, duplicate callback, provider timeout, crash, and
   forbidden sandbox action.
4. **Add a second concurrent work item.** Prove worktree isolation, collision
   handling, queue fairness, and landing order.
5. **Add one remote surface.** Apply the same authority and idempotency path rather
   than implementing a second control system.
6. **Add more roles and routes only when a failed promise requires them.**
7. **Run restore and upstream-sync drills before calling the system operational.**

This follows DORA's [small-batch](https://dora.dev/capabilities/working-in-small-batches/)
and [continuous-integration](https://dora.dev/capabilities/continuous-integration/)
guidance: independently testable slices, short-lived work, and fast feedback.

### Keep decisions separate from implementation

Before a hard-to-reverse choice, record:

- the claim;
- alternatives;
- decision owner;
- predeclared acceptance test;
- evidence;
- result;
- remaining uncertainty;
- review or expiry date.

Agent recommendations can populate the draft. A human signs governance, provider,
cost, credential, waiver, and destructive-operation decisions.

## Prioritized fog register

Priority reflects the cost of building on the wrong answer:

- **P0:** blocks a coherent or safe tracer slice;
- **P1:** required before multi-project or unattended operation;
- **P2:** can remain outside v1 until evidence justifies it.

| Priority | Fog / closure question | Risk if guessed | Evidence required to close it | Acceptance test |
|---|---|---|---|---|
| **P0** | Does the guide's canonical office state machine and any separate rule-stage taxonomy cover every path without aliases? | Components can still invent states or activate the wrong rules even though the prose now names one governance vocabulary. | Generated governance enum, typed rule-stage vocabulary and mapping, transition table, migration policy, and full path review. | Reject every undeclared transition, stage, and alias; replay normal, blocked, cancelled, superseded, and rollback workflows to the same projection and rule activations. |
| **P0** | What are canonical role IDs and authorities? | Alias drift can grant or deny the wrong power. | One role registry with domain-neutral IDs and explicit display aliases. | Exhaustive authority matrix test; every unlisted role/action pair is denied. |
| **P0** | Which configuration tree and application-state roots are authoritative? | Phases can write configuration, databases, evidence, or profiles that later code and backups never read. | One canonical config tree plus a state-ownership, migration, and backup map. | Repository and clean-host checks reject duplicate config roots, misplaced native state, or unresolved guide paths; backup/restore covers every declared owner. |
| **P0** | What is the irreducible kernel, and what must be a module? | A “modular” design either keeps a hidden monolith or lets feature modules replace root authority. | Responsibility map with one owner per state, authority, event, and side effect. | Dependency check rejects kernel-to-feature imports and modules cannot write canonical state or issue permits directly. |
| **P0** | What is the versioned internal module interface and capability model? | Easy experiments gain ambient filesystem, network, secret, or transition authority. | Descriptor schema, capability vocabulary, broker, interface compatibility policy, and denial fixtures. | An undeclared capability, incompatible interface, kernel-port override, event, state write, or side effect fails before execution and leaves an audit event. |
| **P0** | What exact subject does a gate approve? | Evidence for one commit or packet authorizes another. | Subject tuple: project, work item, base, candidate commit, packet digest, gate-policy digest. | Any one-field mismatch makes permit issuance and consumption fail. |
| **P0** | What is atomic across the office database, Kanban projection, ledger, and permit transition? | A crash can show “complete” in one plane and “pending” in another. | One transactional source-of-truth boundary, event/outbox rules, and explicit derived projections. | Inject failure before and after every write; recovery produces one legal state, one ledger history, and no usable orphan permit. |
| **P0** | Who derives `risk_class`, policy activation, and tool permissions? | An agent can self-select weak gates or broad tools. | Trusted deterministic derivation rules plus human override path. | Worker-supplied risk or permission fields are ignored; downgrade requires signed, expiring human decision. |
| **P0** | How are gate and permit phases ordered? | Completion either deadlocks or gets a temporary bypass. | Minimal gate/permit interface before completion adapter. | External completion fails without a single-use exact-subject permit and succeeds once with it. |
| **P0** | What single worktree procedure implements the declared `develop`/`upstream-sync` topology? | Current phase commands can switch branches in place despite the global named-worktree rule. | One executable creation, landing, cleanup, release, and recovery procedure against the exact fork. | Run representative phase, concurrent landing, non-fast-forward rejection, conflict recovery, release promotion, and upstream-sync rehearsals while the primary checkout branch and commit remain unchanged. |
| **P0** | Has the guide's in-place owned-fork identity been realized in Git? | The design names the correct repository, but code, remotes, and evidence can still bind to the wrong history during upstream adoption. | Verified repository root, adoption commit, origin/upstream remotes, and retained bootstrap records. | Phase 0/1 evidence resolves one root and commit; every later artifact and worktree binds to them. |
| **P0** | What does “current context” mean operationally? | Agents act on stale or contradictory material. | Source precedence, freshness, conflict, budget, and provenance contract. | Seed old, current, missing, and contradictory sources; packet labels each correctly and never silently truncates. |
| **P0** | What is the host isolation threat model? | A prompt-level rule is mistaken for containment. | Named assets, actors, allowed capabilities, and mechanisms. | Real adapter cannot read a planted secret, write outside its worktree, reach denied network, escape argv boundaries, or survive limits. |
| **P1** | Can state and side effects recover after every crash point? | Duplicate issues, comments, merges, or lost approvals. | Event/outbox design and idempotency contract. | Kill at each boundary in a test harness; restart yields one legal state and at most one external effect. |
| **P1** | Is project isolation end to end? | One client or project leaks code, facts, secrets, or derived knowledge. | Data-flow map and per-project storage/packet rules. | Cross-project canaries never appear in packets, model inputs, artifacts, search, logs, or learned-route data. |
| **P1** | Which internal module kinds remain in-process, and which effect adapters cross a process boundary? | One faulty built-in experiment crashes the host, while unnecessary isolation makes the core costly and complex. | Failure and threat model, latency baseline, trust classes, process protocol, and resource policy. | Pure module faults are contained and recoverable; an isolated effect adapter can hang, crash, allocate, emit malformed data, and attempt denied access without corrupting or escaping the host. |
| **P1** | How do release upgrade, rollback, activation, and retirement preserve module state? | A failed experiment leaves incompatible data, active registrations, or an unreplayable history. | Versioned migrations, drain protocol, recovery point, dependency graph, release profile, and tombstone rules. | Inject failure at every lifecycle step; restart yields one active version, compatible state, no ghost registration, intact history, and recovery to the prior release profile. |
| **P1** | What makes a reviewer independent? | Correlated or contaminated review gives false assurance. | Executable independence policy. | A reviewer who edited the subject, saw forbidden rationale, or uses the wrong commit cannot issue an accepted gate result. |
| **P1** | How is evaluation calibrated? | A persuasive but inconsistent grader controls promotions. | Human-labeled calibration set, disagreement handling, grader versioning. | Meet predeclared agreement/error limits; otherwise outcome remains inconclusive. |
| **P1** | What proves one route beats another? | A noisy first run becomes permanent routing policy. | Paired baseline, repeated trials, frozen holdout, cost/latency/failure measures, confidence rule. | Promotion occurs only after the predeclared effect and reliability thresholds pass on holdout. |
| **P1** | Are packet, task, run, trace, workspace, and provider IDs defined once? | Identity drift breaks correlation and can attach evidence to the wrong run. | Canonical identity schema, lifecycle, and uniqueness rules. | Every adapter and artifact validates the same identity tuple; mismatched or missing IDs fail ingestion. |
| **P1** | What are backup and restore guarantees? | Audit state or work disappears while backups look healthy. | Recovery point/time objectives chosen by owner and encrypted backup design. | Restore onto a clean environment and reconcile database, artifacts, ledger, worktrees, and external side effects. |
| **P1** | Which SQLite mode/version is safe on this host? | WAL or backup behavior fails under concurrency or crash. | Installed version check, filesystem check, concurrency and checkpoint measurements. | Host-qualified release; reader/writer, crash, checkpoint, backup, and restore suite passes. |
| **P1** | How are model/provider identities pinned and retired? | “Same model” silently changes behavior. | Provider/model revision registry with observation and qualification dates. | Unknown or changed identity enters probation and cannot inherit a prior approval. |
| **P1** | How are raw external facts separated from learned guidance? | Untrusted or private material becomes shared policy. | Provenance, quarantine, sanitization, review, expiry, and project-scope rules. | Unapproved learned artifact cannot activate or cross a project boundary. |
| **P1** | How are remote human decisions authenticated and bound to a subject? | A replayed or ambiguous phone action can approve different work. | Strong identity, nonce, expiry, subject summary, confirmation, and audit rules. | Replayed, expired, wrong-subject, or altered decisions fail; the human sees the exact subject before approval. |
| **P1** | What redaction and exfiltration boundary applies before model or remote delivery? | Secrets or project-private content can leave the machine through a permitted adapter. | Data classification, deterministic preflight, destination policy, output filtering, and incident path. | Planted credentials and cross-project canaries never reach model payloads, remote notifications, logs, or artifacts. |
| **P1** | What operational load requires another supervisor? | “Owner attention” cannot be alerted or capacity-planned. | Baseline queue latency, WIP, collision, retry, escape, cost, and tail-latency data. | Alert and scaling decision use measured thresholds with a runbook, not an agent feeling. |
| **P2** | Does a symbol graph beat simpler file/context selection? | Complexity without better task outcomes. | Paired ablation on Ranex-like tasks. | Material improvement on frozen holdout after token, latency, and failure cost. |
| **P2** | Does a learned router beat static rules? | Opaque routing adds cost and a new failure mode. | Frozen tasks, static baseline, repeated paired trials, drift monitoring. | Predeclared net benefit with no critical reliability regression. |
| **P2** | Do microVMs close a real bubblewrap/Docker gap? | High host and operations complexity. | Threat test bubblewrap and Docker cannot pass. | MicroVM lane passes that test and stays within chosen startup, resource, recovery, and maintenance budgets. |
| **P2** | Should Ranex use Temporal? | Either needless infrastructure or an accidental home-grown workflow engine. | Tracer-slice crash/retry/operability results and build-versus-adopt estimate. | Choose the smallest option that passes the same recovery and side-effect tests. |
| **P2** | Where does MCP reduce adapter cost? | Protocol adoption is mistaken for security or authority. | Two real adapters implemented with and without MCP. | Lower maintenance cost without weakening auth, isolation, provenance, schema, or idempotency. |

## Staged validation plan

The metrics below are **PROPOSALS**. They must be frozen before the evaluated run.
Where a numeric performance threshold depends on the host or provider, measure the
baseline first and have the owner accept the service target before testing.

### Stage 0 — contract consistency

Build no agent workflow yet.

Checks:

- one generated enum for governance state and gate outcomes;
- one canonical role/authority registry and exhaustive rule-stage mapping;
- one kernel/module responsibility map;
- one versioned internal module interface and descriptor schema;
- one canonical configuration tree;
- every guide example validates against current schemas;
- every transition is declared once;
- every authority is deny-by-default;
- every referenced phase dependency exists before consumption.

Ship condition:

- zero conflicting canonical IDs;
- zero undeclared transitions accepted;
- zero unowned schema fields;
- zero feature modules with direct canonical-state or permit authority;
- an independent reviewer returns a verdict, then the human owner approves the state
  and authority model.

### Stage 1 — composition root, instruction registry, and measurement kernel

Implement the minimum module contract and use the scoring path as its first reference
module. Register a small constitutional instruction set before trying to score the
whole handbook.

Checker fixtures:

- valid disabled, canary, restricted, active, quarantined, and retired module states;
- incompatible internal interface version, duplicate ID, changed digest, undeclared
  dependency, and denied capability;
- module crash, hang, malformed event, ghost hook, partial migration, and failed
  retirement or release rollback;
- known-good evidence;
- one defective mutant per registered failure;
- valid alternative implementation;
- wrong subject or commit;
- malformed, partial, or missing evidence;
- false `NOT_APPLICABLE` claim;
- bypass attempt;
- no-op, placebo, harmful-workflow, broken-checker, missing-telemetry, and leakage canaries.

Ship condition:

- a packaged but disabled internal module performs no registration, lifecycle action,
  or side effect;
- the exact module, config, capability-grant, and activation digests appear in every
  affected run and score;
- an incompatible, unqualified, disabled, or quarantined module cannot register or
  execute;
- a candidate scorer cannot qualify, promote, or activate itself, mutate canonical
  workflow state, or issue a permit;
- module crash, timeout, failed migration, failed release rollback, and retirement
  leave one legal host state, no ghost registrations, and inspectable evidence;
- every active instruction has a stable ID, revision, statement digest, scope,
  applicability rule, severity, evidence contract, and coverage state;
- every blocking observable instruction has a qualified deterministic checker or is
  visibly `UNCHECKED` and therefore unable to pass;
- identical frozen evidence and checker inputs produce byte-identical normalized
  results;
- all good, bad, alternative, malformed, and bypass fixtures receive their
  predeclared results;
- a single catastrophic failure remains visible and blocking despite strong scores
  elsewhere;
- missing evaluation cells and insufficient sample size produce `INCONCLUSIVE`,
  never zero or `PASS`;
- protected fixtures, expected results, and holdout tasks are inaccessible to the
  evaluated worker.

### Stage 2 — context packet compiler

Fixtures:

- current authoritative source;
- stale source;
- two authoritative-looking sources in conflict;
- missing required source;
- oversized but relevant source set;
- irrelevant large source;
- another project's planted canary;
- source changed after packet compilation.

Ship condition:

- all provenance fields present;
- all stale, missing, and conflicting fixtures classified correctly;
- no silent truncation;
- zero cross-project canary leakage;
- digest changes whenever any activated source or policy changes;
- identical normalized inputs produce the same manifest digest.

### Stage 3 — one end-to-end tracer

Path:

```text
local work item
  -> research/planning packet
  -> approved plan
  -> isolated worktree
  -> implementation worker
  -> tests
  -> independent review
  -> exact-subject permit
  -> external completion mutation
  -> ledger and current-state reconciliation
```

Ship condition:

- every state transition has an actor, reason, prior state, next state, and event ID;
- every run carries project, work-item, packet, workspace, commit, and policy identity;
- completion without a valid permit fails;
- permit reuse fails;
- permit use against a changed commit fails;
- maker self-approval fails;
- raw test and review evidence remains inspectable;
- one authorized run completes and can be replayed into the same current state.

### Stage 4 — adversarial sad paths

Tests:

- prompt says a worker is authorized, but the grant is absent;
- agent claims tests passed, but no artifact exists;
- wrapper reports no output while an artifact exists;
- provider returns malformed, truncated, duplicated, or delayed output;
- reviewer uses the wrong commit;
- reviewer edits the subject before verdict;
- worktree contains a secret canary;
- command contains shell metacharacters;
- network request targets a non-allowlisted destination;
- risk class is lowered in model output;
- human waiver is expired or for another subject.

Ship condition:

- zero unauthorized state changes or external mutations;
- every blocked condition is visible and attributable;
- no wrapper summary overrides inspected artifacts;
- no secret canary reaches model input, logs, artifacts, or replies.

### Stage 5 — concurrency and recovery

Run at least two work items against the same project and two projects concurrently.
Inject process termination before and after each durable boundary.

Measure:

- duplicate side effects;
- lost or split-brain state;
- worktree collisions;
- queue wait and tail latency;
- retry count and cost;
- database lock and checkpoint behavior;
- recovery time;
- cross-project leakage.

Ship condition:

- zero duplicate irreversible side effects;
- zero illegal or split-brain terminal states;
- zero cross-project leakage;
- all abandoned leases are reclaimed through a recorded rule;
- restored state reconciles with external systems.

### Stage 6 — model and route qualification

Protocol:

1. define task strata and risks;
2. create a static baseline;
3. freeze prompts, tools, budgets, grader, and thresholds;
4. reserve an unseen holdout;
5. run repeated paired trials;
6. randomize order where ordering could matter;
7. record correctness, critical failures, cost, latency, retries, and variance;
8. calibrate automated grading against human-labeled examples;
9. report confidence and inconclusive results;
10. canary a winning route before promotion.

The primary paired arms should be:

- `A — frozen current baseline`;
- `B — frozen Ranex workflow`, whose task-level difference from A is the primary
  deployment effect;
- `C — forced activation`, used only to diagnose routing or instruction-reach failure;
- `D — prior Ranex release`, once one exists;
- `P — length-matched placebo context`, required only when claiming procedural
  content caused the improvement rather than extra attention or tokens.

Keep the same task, base commit, outer sandbox, resource ceiling, network policy,
user-response script, and graders across paired arms. Randomize and interleave the
conditions. Treat trials as nested within tasks; turns and tool calls are diagnostics,
not independent samples. Report task-macro first-attempt success, harmed-task count,
critical failures with exposure counts and an upper bound, cost per assigned and
accepted task, wall-time percentiles, owner minutes, rework, collisions, routing
errors, and infrastructure/checker-fault rates as separate cards.

Do not use SWE-bench alone. It measures repository issue resolution, not Ranex's
authority, context freshness, isolation, evidence, recovery, or human-governance
workflow.

### Stage 7 — operations proof

Run:

- clean-host installation;
- provider outage and rate-limit drill;
- disk-full and database-recovery drill;
- encrypted backup and clean restore;
- credential rotation without credential output;
- worktree hygiene with secret-lock protection;
- upstream fetch, compare, conflict, and no-auto-merge rehearsal;
- remote authentication and replay attack tests;
- seven-day or owner-chosen soak with queue, cost, error, and tail-latency review.

Operational readiness is achieved only after the owner accepts measured recovery,
cost, latency, and unattended-operation limits.

## Decision-ready recommendation

### Adopt now

1. Treat Cookbook as a cited pattern library, not a code dependency.
2. Refactor the owned Hermes fork into a batteries-included modular monolith with a
   small non-replaceable kernel and baked-in first-party modules.
3. Make Ranex, not Claude Code, Codex, or another adapter, the source of truth for
   versioned instructions, activation, evidence, and authority.
4. Preserve Cookbook's separation-of-duty, stranger-ready packet, proof, log, and sad-path
   principles.
5. Build deterministic scoring as a first-party internal module beside the first
   contracts, while keeping score authority and hard gates in the kernel.
6. Make the Ranex guide's deterministic control/human authority boundary canonical.
7. Resolve the nine remaining guide conflicts before building the later phases.
8. Build one vertical tracer slice before expanding roles, providers, remotes, or
   advanced routing.
9. Keep every high-risk unknown open until its acceptance test passes.

### Defer

- learned routing;
- Kubernetes;
- warm Firecracker pools;
- process checkpoint engines;
- blanket MCP adoption;
- automatic cross-project learning;
- large permanent agent rosters.

### Reject

- prompt text as an enforcement boundary;
- a model reviewer as final transition authority;
- silent gate downgrades;
- literal reuse of Cookbook's scripts as the Ranex runtime;
- claims that stochastic agents themselves are deterministic;
- model promotion from one favorable run;
- raw cross-project context sharing.

## Limitations

1. **FACT.** Ranex has no implementation in this checkout, so this report cannot
   measure end-to-end behavior, security, performance, recovery, or cost.
2. **FACT.** Cookbook's strongest evaluation artifacts are narrow and often have
   one run per condition. They support techniques, not broad effectiveness claims.
3. **FACT.** The Cookbook checkout is one local commit ahead of its remote.
   Citations name the exact local revision reviewed.
4. **FACT.** Local status records and external software guidance can change after
   2026-07-27. They are evidence of the reviewed snapshot, not permanent facts.
5. **UNKNOWN.** The target host's exact kernel features, SQLite version, Docker
   configuration, provider contracts, budgets, and recovery targets were not
   established by the reviewed documents.
6. **UNKNOWN.** No production-shaped Ranex task corpus or human-calibrated evaluator
   exists yet. The route-qualification plan cannot close until those are created.
7. **UNKNOWN.** Independent cross-family design review did not run. The configured
   Claude reviewer route exposed no agents, and its documented `opencode` fallback
   was unavailable. The evidence and source checks ran; the design recommendations
   remain uncorroborated judgments until that review occurs.
8. **FACT.** The upstream Hermes review was targeted to its current architecture,
   plugin, hook, and loading surfaces. It was not a full audit of every upstream
   module or future compatibility risk.

## Local source register

Paths beginning `cookbook/` are relative to `/home/soultransit/devtony/`.
Ranex paths are relative to this repository.

### Ranex

- `RANEX_IMPLEMENTATION_GUIDE.md`
- `docs/research/gemini-research.md`

### Cookbook foundations

- `cookbook/README.md`
- `cookbook/CONTENTS.md`
- `cookbook/KNOWN-HOLES.md`
- `cookbook/WHERE-WE-ARE.md`
- `cookbook/TASTING-CHECKLIST.md`
- `cookbook/THE-CONTRADICTION-PASS.md`
- `cookbook/FOR-THE-OWNER.md`
- `cookbook/SHOWDOWN.md`
- `cookbook/THE-PRINT-SHOP.md`

### Cookbook chapters

- `cookbook/book/12-the-operations-log.md`
- `cookbook/book/29-when-one-cook-is-not-enough.md`
- `cookbook/book/30-two-people-working-at-once-without-colliding.md`
- `cookbook/book/35-what-a-chain-is.md`
- `cookbook/book/37-knowing-which-restaurant-you-are-standing-in.md`

### Cookbook research, evaluation, and implementation

- `cookbook/research/proof-over-authority.md`
- `cookbook/research/agent-skill-effectiveness-framework.md`
- `cookbook/research/agent-skill-effectiveness-framework-gaps.md`
- `cookbook/research/skill-eval-framework-evidence-audit.md`
- `cookbook/showdown2/RESULTS.md`
- `cookbook/press/brief_contract.py`
- `cookbook/press/core-invariants.json`
- `cookbook/press/print.py`
- `cookbook/press/taste.py`
- `cookbook/press/test_printer_reach.py`
- `cookbook/plugins/chain-standards/hooks-handlers/session-start.sh`

## External primary and official sources

All external sources were accessed on 2026-07-27.

### Architecture and modularity

- Hermes Agent, [development architecture rules](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/AGENTS.md)
- Hermes Agent, [plugin guide](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/website/docs/user-guide/features/plugins.md)
- Hermes Agent, [plugin manager source](https://github.com/NousResearch/hermes-agent/blob/d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012/hermes_cli/plugins.py)
- Visual Studio Code, [Extension API](https://code.visualstudio.com/api/)
- OpenTelemetry, [Collector distributions](https://opentelemetry.io/docs/collector/distributions/)
- OpenTelemetry, [Collector configuration](https://opentelemetry.io/docs/collector/configuration/)

### Governance, evaluation, and delivery

- NIST, [AI Risk Management Framework Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- NIST, [Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
- NIST, [Secure Software Development Framework, SP 800-218](https://csrc.nist.gov/pubs/sp/800/218/final)
- OpenAI, [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)
- OpenAI, [How to evaluate skills](https://developers.openai.com/blog/eval-skills)
- Anthropic, [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- DORA, [AI-accessible internal data](https://dora.dev/capabilities/ai-accessible-internal-data/)
- DORA, [Working in small batches](https://dora.dev/capabilities/working-in-small-batches/)
- DORA, [Continuous integration](https://dora.dev/capabilities/continuous-integration/)
- Google SRE, [Monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/)

### Schemas, provenance, state, and workflows

- JSON Schema, [Draft 2020-12](https://json-schema.org/draft/2020-12)
- IETF, [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)
- SLSA, [Build provenance v1.2](https://slsa.dev/spec/v1.2/build-provenance)
- SQLite, [Write-ahead logging](https://sqlite.org/wal.html)
- SQLite, [Transactions](https://sqlite.org/lang_transaction.html)
- Temporal, [Workflows](https://docs.temporal.io/workflows)
- Temporal, [Python error-handling best practices](https://docs.temporal.io/develop/python/best-practices/error-handling)
- OpenTelemetry, [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- OpenTelemetry, [Trace API specification](https://opentelemetry.io/docs/specs/otel/trace/)

### Execution and integration

- Bubblewrap, [official repository and sandbox construction guidance](https://github.com/containers/bubblewrap)
- Docker, [Engine security](https://docs.docker.com/engine/security/)
- Git, [`git worktree` documentation](https://git-scm.com/docs/git-worktree)
- Model Context Protocol, [Architecture](https://modelcontextprotocol.io/specification/2025-11-25/architecture)
- Model Context Protocol, [Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- Model Context Protocol, [Security best practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices)
- Firecracker, [official FAQ](https://github.com/firecracker-microvm/firecracker/blob/main/FAQ.md)

### Agent and context research

- Xia et al., [Agentless: Demystifying LLM-based Software Engineering Agents](https://arxiv.org/abs/2407.01489)
- Jimenez et al., [SWE-bench: Can Language Models Resolve Real-World GitHub Issues?](https://arxiv.org/abs/2310.06770)
- Aider, [Repository map documentation](https://aider.chat/docs/repomap.html)
- [Conductor: Learning to Route Agents](https://arxiv.org/abs/2512.04388)
- [TRINITY: Learning to Orchestrate Agents](https://arxiv.org/abs/2512.04695)
- [LEMON: Learning to Route Multi-Agent Systems](https://arxiv.org/abs/2605.14483)
- [ALMAS: An Automated Framework for Language Model Agent System Design](https://arxiv.org/abs/2510.03463)
- Sakana AI, [Fugu model routing](https://sakana.ai/fugu-release/)
- [DeltaBox: fast state management for agent sandboxes](https://arxiv.org/abs/2605.22781)
- [Crab: asynchronous checkpointing for AI agents](https://arxiv.org/abs/2604.28138)
