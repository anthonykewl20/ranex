# Spec Kit Selective-Adaptation Reconciliation

| Field | Value |
|---|---|
| Record ID | `REVIEW-SPEC-KIT-SELECTIVE-ADAPTATION-2026-07-30` |
| Version | `1.0.0` |
| Status | `COMPLETE_ADVISORY_RECONCILIATION`; no adaptation, runtime claim, gate result, or readiness claim |
| Date | 2026-07-30 |
| Owner | Human owner |
| Ranex source subject | commit `a573502a87e0599cf6e5f9456c348bf1a7686382`; tree `cb99ae954b7536ab91762bc8cac7cc0df46c1b43` |
| Spec Kit source subject | [`github/spec-kit@f36634b5c1463d3592382e863cd5e7b8a94d9c9a`](https://github.com/github/spec-kit/tree/f36634b5c1463d3592382e863cd5e7b8a94d9c9a); declared version `0.14.5.dev0`; MIT license |
| Independent reviewers | OpenCode `1.18.8`; `openrouter/tencent/hy3` high/plan and `opencode-go/deepseek-v4-pro` default/plan |
| Evidence bundle | [`artifacts/2026-07-30/spec-kit-selective-adaptation/`](artifacts/2026-07-30/spec-kit-selective-adaptation/) |
| Proposal | [RFC-0002](../rfcs/RFC-0002-selective-spec-kit-adaptation.md), `DRAFT`; not a decision |
| Mutations | This advisory record, its immutable evidence bundle, the draft RFC, and documentation indexes only |

## Executive verdict

There is useful product value in selectively adapting Spec Kit, but not in
installing it as Ranex's governance layer or copying its authority model.

The strongest product thesis is:

> A familiar, Spec-Kit-shaped interaction path over the Ranex assurance kernel:
> easy for an owner to express and refine intent; impossible for an agent,
> prompt, external issue, or downloaded workflow to turn that intent into
> authority by itself.

The valuable patterns are the owner-facing progression from intent through
clarification, plan and task decomposition; requirements-quality checklists;
read-only cross-artifact analysis; convergence/gap classification; and,
later, familiar projections into issue trackers and qualified ecosystem
packages. These should reuse Ranex state owners, artifacts, gates, effects, and
extension lifecycle.

The rejected mechanisms are prompt text as enforcement, Markdown as canonical
authority, maker self-completion, model verdicts as gates, unqualified
integration or extension activation, and unsandboxed shell execution with
plain interpolation.

This is a product-direction recommendation, not proof of market demand or
permission to implement. Ranex remains pre-implementation, with runtime
conformance and effectiveness `NOT_ASSESSED`.

## Question and method

The review answered three separate questions:

1. What does current Spec Kit actually provide?
2. Which semantics fit the already accepted Ranex full map?
3. Which adaptations might create user or commercial value, and what evidence
   would be needed to establish that value?

The pinned upstream command templates, guides, and ecosystem references were
compared with the pinned Ranex architecture. HY3 and DeepSeek V4 Pro then
received the same source bytes and prompt, independently, without either
reviewer's answer. The complete raw prompt, source manifest, outputs, and
session metadata are in the
[evidence bundle](artifacts/2026-07-30/spec-kit-selective-adaptation/).

Two earlier attempts were excluded: one HY3 run could not read its attachments,
and one DeepSeek run did not receive four core command files. Exclusion details
are recorded in
[`review-metadata.json`](artifacts/2026-07-30/spec-kit-selective-adaptation/review-metadata.json).

No reviewer verdict was used as a fact source. Material recommendations were
reconciled against pinned primary sources. Popularity was deliberately treated
as an adoption signal, not correctness, security, production-fitness, or
effectiveness evidence.

## Verified baseline facts

### What is already present in Ranex

At the reviewed subject, tracked Ranex files contained no Spec Kit attribution
or declared adoption. Four files under ignored `.local/speckit-ref/` were
byte-identical consultation copies of the pinned upstream constitution
template, specification template, `clarify` command, and `analyze` command.
They are not Git-tracked, machine contracts, product code, or evidence of an
implemented feature. Their paths and digests are recorded in the
[source manifest](artifacts/2026-07-30/spec-kit-selective-adaptation/source-manifest.json).

Ranex already maps the attachment points that several reviewer recommendations
mistook for missing:

- `work_management` owns external references and projections and has an
  `issue_tracker` port
  ([full-system architecture, context map and file map](../HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md));
- `instruction_registry` already owns versioned instructions, precedence,
  applicability, and activation;
- `governed_execution` already defines deterministic workflow primitives,
  immutable approved workflow definitions, human/evidence gates, retry,
  cancellation, compensation, and reconciliation; models may draft but never
  activate workflow definitions;
- `routing` and release-pinned `WorkerRuntime` adapters already own qualified
  runtime integration;
- `extension_host` already defines a version-negotiated, out-of-process typed
  protocol whose effects return through `CapabilityBus`; and
- `ExtensionStatus` already progresses through
  `DISCOVERED -> QUARANTINED -> REVIEWED -> QUALIFIED -> PINNED -> ENABLED`,
  with source, dependency, manifest, capability, egress, secret, data-class,
  crash-isolation, quarantine, and human-activation controls
  ([`SDLC-FORK-005`](../SDLC_CONTROL_CATALOG.md)).

Agent queues, boards, and external systems are projections. They cannot own
`WorkItemStatus` or authorize transitions
([fleet context ownership](../AI_AGENT_FLEET_CONTROL_PLANE.md)).

These are accepted target-architecture facts, not implemented-runtime facts.
The repository still says no product code exists and neither readiness tier is
declared.

### What current Spec Kit provides

The pinned Spec Kit workflow exposes `constitution`, `specify`, `plan`, `tasks`,
`implement`, `converge`, `taskstoissues`, `clarify`, `analyze`, and `checklist`
commands
([pinned README](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/README.md#L162-L188)).

The useful source-level details are more specific than the command names:

- `clarify` applies a broad ambiguity taxonomy, prioritizes at most five
  material questions, asks exactly one at a time, explains why each matters,
  and proposes an answer
  ([pinned command](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/commands/clarify.md#L90-L188));
- `checklist` checks whether requirements are complete, clear, consistent, and
  testable rather than checking whether implementation works
  ([pinned command](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/commands/checklist.md#L9-L28));
- `analyze` is expressly read-only and compares the spec, plan, and tasks
  ([pinned command](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/commands/analyze.md#L52-L72));
- `converge` appends remediation work after comparing present code with the
  requested artifact set
  ([pinned command](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/commands/converge.md#L57-L88));
- `taskstoissues` checks the destination and existing issues before creating
  missing GitHub issues
  ([pinned command](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/commands/taskstoissues.md#L53-L73)); and
- the artifact-evolution guide distinguishes flow-forward history, a revised
  living spec, and flow-back reconciliation
  ([pinned guide](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/docs/guides/evolving-specs.md#L17-L80)).

Spec Kit also has an actual workflow runner, not merely prompt files. Its step
types include commands, prompts, shell, gates, branches, loops, fan-out, and
fan-in. Its own security note says a shell step runs with the user's privileges,
`requires` is advisory rather than a capability gate, and no capability sandbox
exists
([pinned workflow reference](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/docs/reference/workflows.md#L465-L481)).
Plain string substitution into `/bin/sh -c` creates an additional injection
boundary
([same reference](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/docs/reference/workflows.md#L505-L514)).

The current constitution template is project-defined; example principles are
not a mandatory fixed nine-article constitution
([pinned template](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/templates/constitution-template.md)).
The nine articles described in `spec-driven.md` are useful historical
methodology context, not an accurate description of the current template's
fixed shape.

The official Spec Kit site reported 121K+ stars, 240+ contributors,
35 integrations, 138 extensions, and 25 presets on 2026-07-16
([official overview](https://github.github.io/spec-kit/index.html)). That is
strong evidence of reach, discoverability, and ecosystem activity. The reviewed
sources contain no controlled outcome study, defect-rate comparison, security
qualification, or Ranex-fit benchmark; “battle-tested” therefore remains
`UNKNOWN` as a reliability/effectiveness claim.

The pinned upstream license is MIT. This review copies no Spec Kit template or
implementation into the tracked Ranex product. If exact upstream material is
later incorporated, its notice/provenance and compatibility with Ranex
distribution terms require an explicit legal/compliance disposition.

## Independent-review result and corrections

Both complete reviewers reached the same high-level conclusion:

- selectively adapt useful workflow and requirements-engineering semantics;
- translate them into Ranex-native artifacts and enforcement;
- do not use prompt constitutions, self-validation, or unsandboxed execution as
  authority; and
- treat commercial value as a hypothesis that requires measurement.

Their prioritization differed. HY3 favored the
`specify -> clarify -> plan -> tasks -> implement -> analyze/checklist ->
converge` experience. DeepSeek prioritized a workflow engine, project-init CLI,
and issue-tracker bridge.

Primary-source reconciliation changes several model recommendations:

1. **No new workflow authority is established here.** DeepSeek's claim that
   Ranex has no executable sequencing primitive is false at target-design
   scope: the accepted architecture already specifies one. Runtime remains
   absent. A future adaptation can improve authoring and interaction UX, but
   must not add a competing `pipeline_execution` owner.
2. **Extensions are not a missing architecture.** Ranex already has
   `extension_host` and a fail-closed qualification/activation lifecycle.
   Spec Kit's discovery and packaging UX may inform that surface later; its
   remote or ambient activation semantics remain excluded.
3. **Issue integration is already an attachment point.** A
   `taskstoissues`-like feature is an effectful, idempotent outbound projection
   through `work_management.issue_tracker`, not a new tracker authority and not
   a “read-only adapter.”
4. **Integrations are not categorically rejected.** Agent-neutral onboarding is
   valuable, but each runtime still requires a release-pinned qualified route
   and typed `WorkerRuntime`; agent-directory prompt installation cannot grant
   authority or widen a route.
5. **Artifact evolution is not categorically rejected.** Flow-forward history
   fits Ranex directly. Living and flow-back semantics can fit only as new,
   immutable, owner-attributed revisions with supersession, dependency
   invalidation, and re-evaluation—not silent in-place mutation of a sealed
   subject.
6. **Model-suggested artifact mappings are proposals.** Existing `WorkIntake`,
   `ResearchPacket`, `ArchitectureProposal`, `TaskPacket`,
   `ReviewObservation`, `CheckerResult`, `RunResult`, and outcome artifacts are
   candidates. This review does not create a `Spec`, `ClarificationSession`,
   `CrossArtifactAnalysis`, or `ConvergenceAssessment` contract.
7. **Effort, risk, and market confidence ratings in both raw reviews are
   analyst estimates.** No implementation estimate or market study was in the
   attached subject.

The raw reviews remain preserved as advisory evidence even where this
reconciliation corrects them.

## Corrected disposition matrix

`ADOPT` below means adopt a bounded method or taxonomy, not copy a file.
`MODIFY` means translate the user experience into existing Ranex authority.
`DEFER` means retain an attachment point but make no current product
commitment. `REJECT` applies to the unsafe mechanism, not necessarily the user
need.

| Spec Kit surface | Disposition | Ranex-native treatment | Non-negotiable boundary |
|---|---|---|---|
| Constitution | **REJECT enforcement; MODIFY authoring aid** | A friendly editor may help owners propose principles or policy changes through RFC/ADR and registries. | No Markdown constitution, prompt, or model interpretation becomes enforcement or outranks accepted authority. |
| `specify` | **MODIFY** | Project owner intent into `WorkIntake`, product outcomes, requirements, acceptance criteria, and readable generated views. | A prose spec is a view/proposal, not canonical work state or permission to implement. |
| `clarify` | **ADOPT method; MODIFY recording** | Use the ambiguity taxonomy, prioritized bounded dialogue, one question at a time, “why it matters,” and an optional recommendation. Record owner answers, unresolved unknowns, and a new subject revision. | The model cannot silently answer for the owner, erase an unknown, or mutate a sealed subject. Five questions is a UX default, not universal policy. |
| `plan` | **MODIFY** | Guide research, alternatives, architecture proposal, traceability, and packet compilation using current artifact candidates. | Planning output cannot activate policy, choose an unqualified route, or approve itself. |
| `tasks` | **MODIFY** | Render dependency-aware tasks from governed work and compile exact `TaskPacket`/assignment inputs; parallel hints are advisory until fleet rules prove safety. | Markdown checkboxes and `[P]` markers never own status, grants, leases, or fan-out. |
| Requirements checklist | **ADOPT concept** | Apply requirements-writing quality categories. Deterministic qualified rules may emit `CheckerResult`; model judgments emit advisory `ReviewObservation`. | It does not test implementation, satisfy a gate by itself, or let the author self-approve. |
| Cross-artifact `analyze` | **ADOPT concept** | Compare exact requirement, design, task, and evidence subjects; use deterministic joins where possible and independent analytical review elsewhere. | Read-only; findings are advisory until a qualified checker/gate and human decision consume them. |
| `implement` | **MODIFY UX; REJECT self-completion** | Present governed execution progress backed by assignments, attempts, leases, `RunResult`, evidence, and landing records. | A maker cannot mark canonical work complete, validate its own result, land, merge, release, or mint a permit. |
| `converge` | **MODIFY** | Reuse the useful `MISSING`, `PARTIAL`, `CONTRADICTS`, and `UNREQUESTED` gap taxonomy; independently generate governed remediation proposals/work. | Current artifacts are not the “sole source of intent”; a model's clean verdict is not proof, and it cannot append authoritative work directly. |
| `taskstoissues` | **MODIFY, later slice** | Create or reconcile external issues as idempotent outbound projections with exact destination binding, effect permit, replay key, and evidence. | External issue state never transitions `WorkItemStatus`; remote mismatch or unqualified credentials deny the effect. |
| Flow-forward evolution | **ADOPT concept** | Preserve immutable history and explicit supersedes/continues/remediates links. | Historical subjects stay addressable; no evidence is silently rewritten. |
| Living/flow-back evolution | **MODIFY** | Express accepted change as a new owner-attributed revision, invalidate dependent artifacts, then re-plan/re-check. | No in-place mutation of a sealed canonical subject and no code-level discovery silently changes product intent. |
| Agent integrations | **DEFER distribution UX** | Later expose qualified adapter descriptors and agent-neutral onboarding through `routing` and the runtime catalog. | No agent-directory prompt, detected binary, environment variable, or popularity signal activates a route. |
| Extensions and catalogs | **DEFER packaging UX** | Build, if demanded, on existing `extension_host`, content digests, provenance, quarantine, qualification, pinning, grants, and human activation. | No remote catalog activation, ambient plugin, same-process hostile code, or extension access to authority stores. |
| Presets | **DEFER** | Candidate projections into `instruction_registry`, process-tailoring, terminology, and presentation profiles. | A preset cannot override an ADR, policy, gate, risk floor, state owner, or route lock. |
| Workflows | **MODIFY authoring UX; REJECT runtime mechanics** | A friendly authoring view may compile into existing immutable approved workflow definitions and governed activities/effects. | No competing workflow owner, raw shell step, plain untrusted interpolation, advisory “permission,” or model activation. |
| Bundles | **DEFER** | Potentially compose already qualified role, instruction, tailoring, adapter, and workflow references by exact digest. | A bundle cannot transitively install or enable unqualified content or change precedence implicitly. |
| `init` / project bootstrap | **DEFER pending product decision** | A guided bootstrap may later generate a valid Ranex workspace and run contract validation. | It cannot copy unreviewed templates, create authority by scaffolding, overwrite project material, or imply readiness. |
| Greenfield/brownfield recipes | **MODIFY vocabulary only** | Tailor the same Core SDLC and full-map rules to new or existing systems, retaining lineage, migration, and invalidation evidence. | “Generate from scratch” and “modernize” never bypass full-map, upstream, migration, or readiness controls. |
| Popularity / “battle-tested” claim | **REJECT as proof** | Use ecosystem scale only to prioritize user research and compatibility questions. | Stars, contributors, integrations, or model agreement cannot establish correctness, security, effectiveness, or Ranex fit. |

## Where the commercial value may be

### Facts

- Spec Kit exposes a recognizable end-to-end vocabulary and a large current
  ecosystem.
- Ranex has a differentiated assurance architecture but no implemented product
  runtime.
- The Spec Kit interaction patterns and Ranex enforcement mechanisms can be
  conceptually separated.
- A template or command name is easy for competitors to reproduce; it is not a
  durable moat by itself.

### Inference

The most plausible differentiation is not “Ranex also has slash commands.” It
is the combination of low-friction specification UX with subject binding,
independent review, least privilege, effect control, and human authority. In
short: Spec Kit can inform the front door; Ranex remains the vault.

### Unproven hypotheses

| Hypothesis | Potential value | Required evidence |
|---|---|---|
| Guided `specify` + bounded `clarify` reduces owner effort and downstream rework. | Faster onboarding and fewer misunderstood work items. | Compare owner minutes, unresolved unknowns, invalidations, clarification churn, and rework against a baseline. |
| Requirements-quality checklist + cross-artifact analysis catches defects earlier. | Lower review and implementation waste. | Measure confirmed findings, false positives/negatives, escaped requirement defects, and time-to-correction on exact subjects. |
| Independent convergence analysis finds missing, contradictory, or unrequested implementation. | Better trust and less landed-but-incomplete work. | Blind evaluation against human-labeled anchors; track remediation yield and escaped gaps. |
| Familiar command/view terminology improves adoption without weakening authority. | Lower learning cost for teams already familiar with SDD tools. | Usability tests and activation/retention measures; do not substitute repository stars. |
| Governed issue projections fit teams' existing GitHub/Jira process. | Lower switching cost. | Trace idempotency/reconciliation failures and interview teams using an existing tracker. |
| A quarantined, qualified extension ecosystem becomes a trust differentiator. | Long-term network effects without an unsafe plugin market. | Validate demand first; later measure qualified packages, active use, incidents, revocations, and upgrade cost. |

One tracer can test technical fit. It cannot establish commercial value. Market
claims require several representative users and a predeclared comparison.

## Smallest responsible first slice

If the owner accepts the draft RFC and current readiness/preflight rules permit
it, the first slice should be a manual or explicitly bounded pre-readiness
tooling experiment, not a new workflow engine or marketplace:

1. Select one low-risk Ranex documentation/tooling work item and freeze its exact
   subject.
2. Present a friendly intake view that populates existing `WorkIntake` and
   requirement/outcome candidates.
3. Run a maximum-five clarification dialogue as a default. Record each owner
   answer, preserve every unresolved `UNKNOWN`, and create an attributed
   revision rather than editing a sealed subject.
4. Produce the normal design/plan/task artifacts through existing governance.
   Use one leaf worker only if implementation is separately authorized.
5. Run requirements-quality and cross-artifact checks through an independent
   identity. Separate deterministic `CheckerResult` candidates from advisory
   `ReviewObservation` findings.
6. Compare the exact accepted intent with the exact result using the
   convergence taxonomy. Create remediation proposals; do not self-pass or
   directly alter canonical work state.
7. Retain the normal gate, human landing, post-landing, outcome, and trace
   requirements.
8. Record owner effort, ambiguity closure, confirmed/false findings,
   invalidation/rework, cycle time, and any authority-boundary violation.

The experiment should first prove that the friendly layer is a lossless
projection of current Ranex semantics. Issue projection, bootstrap CLI,
workflow authoring, integration packaging, extensions, presets, and bundles
should follow only if evidence justifies them.

## Decisions still required

The linked draft RFC deliberately leaves these owner decisions open:

1. whether the friendly specification/decomposition experience is an accepted
   Ranex product direction;
2. which existing artifact types are sufficient and whether any new schema is
   justified;
3. how owner answers create revision/supersession and downstream invalidation;
4. which checklist/analyze/converge checks can be deterministic and qualified,
   and which must remain model-advisory;
5. whether familiar Spec Kit names are used in UI projections or replaced with
   Ranex terminology;
6. the exact pre-readiness tracer scope, success measures, comparison, and
   stopping rule;
7. the one-way/reconciliation semantics of external issue projections;
8. whether workflow, integration, preset, bundle, and extension authoring
   surfaces merit later proposals; and
9. the legal/provenance treatment if exact MIT-licensed source or templates are
   ever incorporated.

If the RFC is accepted, any change to state ownership, workflow semantics,
contracts, policy, runtime adapters, extension activation, or effect authority
requires the normal governed ADR/contract path. No ADR number is reserved by
this review.

## Standing and limitations

This record is advisory evidence. It does not:

- adopt Spec Kit;
- install, copy, or enable an integration, extension, preset, workflow, bundle,
  or catalog;
- create a Ranex artifact schema, state transition, context, gate, permit, or
  runtime route;
- resolve licensing compatibility for a future derivative;
- demonstrate security, performance, outcome improvement, market demand, or
  commercial value; or
- change the current pre-implementation/readiness state.

Its current conclusion is narrower: selective adaptation is worth a governed,
measured experiment, and the highest-value patterns fit only when their UX is
separated from Spec Kit's prompt-level authority and reattached to existing
Ranex controls.
