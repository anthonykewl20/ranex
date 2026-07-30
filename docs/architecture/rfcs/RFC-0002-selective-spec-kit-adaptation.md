# RFC-0002: Selectively Adapt Spec Kit Interaction and Artifact Patterns

| Field | Value |
|---|---|
| Status | DRAFT |
| Owner | Human owner / `human-governor` |
| Authors | Codex synthesis from owner request and independent HY3/DeepSeek review |
| Created | 2026-07-30 |
| Review by | Unassigned |
| Affected contexts | Candidate: `product_definition`, `work_management`, `analytical_review`, `assurance`, `governed_execution`; future-only: `instruction_registry`, `routing`, `extension_host`, `process_assurance` |
| Supersedes | None |
| Architecture subject digest | `git-tree-sha1:cb99ae954b7536ab91762bc8cac7cc0df46c1b43` at commit `a573502a87e0599cf6e5f9456c348bf1a7686382` |
| Subject-manifest digest | [`sha256:43b4213f7895b5ba9e63de4ac9e7d4e4b5390439d6fd722f1e7e0b51837a8697`](../reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/source-manifest.json) |
| Core SDLC trace ref/digest | Not assigned; no governed work item or trace was supplied for this prose proposal |

This RFC is a proposal, not a decision. It creates no authority, artifact
contract, permit, implementation work, runtime conformance, or readiness
claim.

## Decision question

Should Ranex adopt a familiar specification-driven interaction façade—drawing
selectively from pinned GitHub Spec Kit patterns—while compiling every
authoritative action into existing Ranex artifacts, state owners, gates,
effects, and human decisions?

If yes, which subset should enter a bounded experiment, and which mechanisms
must remain permanently excluded?

## Full-map impact

- Contexts: no new context is proposed. Initial candidates attach to
  `product_definition`, `work_management`, `analytical_review`, `assurance`,
  and existing `governed_execution`.
- Public APIs: possible future owner-facing intake, clarification,
  requirements-quality, analysis, and convergence views; exact API shape is
  undecided.
- State owners: unchanged. `work_management` retains `WorkItemStatus`;
  `product_definition` retains requirement/outcome ownership;
  `governed_execution` retains run/workflow/effect authority; `assurance`
  retains gate evaluation; humans retain decisions and landing.
- Effect owners: unchanged. Any issue creation or external mutation is an
  explicit effect through `CapabilityBus`.
- Lifecycles: unchanged by this RFC. Proposed revisions must use existing
  immutable/supersession/invalidation semantics unless a later ADR changes
  them.
- Trust/security boundaries: owner dialogue and model analysis remain
  untrusted/advisory inputs. No prompt, external issue, downloaded workflow, or
  package gains authority.
- Attachment points preserved: work intake and product definition; workflow
  definitions; instruction registry; runtime routing; issue-tracker port;
  extension-host quarantine/qualification; review/checker/gate path.
- Product inclusions/exclusions changed: none until an ADR is accepted.
  Prompt enforcement, self-approval, remote catalog activation, ambient
  plugins, unsandboxed shell, and model-controlled workers remain excluded.

## Context and evidence

The complete advisory reconciliation is
[`REVIEW-SPEC-KIT-SELECTIVE-ADAPTATION-2026-07-30`](../reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md).
Its evidence bundle pins the Ranex and Spec Kit subjects, common prompt, raw
independent HY3/DeepSeek outputs, and session metadata.

### Facts

- Current Spec Kit provides a coherent
  `specify -> clarify -> plan -> tasks -> analyze/checklist -> implement ->
  converge` experience, issue conversion, artifact-evolution guidance, agent
  integrations, and an extension/preset/workflow/bundle ecosystem.
- Spec Kit's requirements checklist explicitly assesses requirements writing,
  not implementation behavior; `analyze` is read-only.
- Spec Kit's workflow runner supports human gates and rich control flow, but
  its shell step runs with user privileges, has no capability sandbox, and
  performs plain string interpolation.
- The same agent may author, implement, self-validate, and mark Markdown tasks
  complete in the Spec Kit flow.
- Ranex already maps governed workflows, issue projections, an instruction
  registry, qualified runtime adapters, and a quarantined extension host.
- Ranex has no product runtime yet; neither readiness tier is declared.
- The reviewed repository contained four ignored, byte-identical Spec Kit
  consultation files and no tracked declared adaptation.
- Spec Kit is MIT-licensed at the pinned subject.

### Assumptions

- Owners benefit from a lower-friction way to express and refine intent.
- Familiar SDD concepts can be presented as views without weakening canonical
  Ranex authority.
- Existing artifact families may cover the first experiment without a new
  `Spec` or `ClarificationSession` schema.
- A single-worker, low-risk experiment can reveal projection loss and workflow
  friction before broader ecosystem work.

These are proposal assumptions, not established facts.

### Unknowns

- User demand, willingness to pay, onboarding improvement, and retention.
- Whether the UX reduces rework or merely adds ceremony.
- Which analysis rules are deterministic enough to qualify.
- Whether existing artifacts can record clarification and convergence without
  semantic overload.
- Exact CLI/UI terminology and whether Spec Kit-compatible names create value.
- Performance, safety, false-positive, false-negative, and operating cost.
- Distribution/license disposition if exact upstream material is copied.
- Whether issue trackers, workflow authoring, or an extension ecosystem are
  priorities for Ranex users.

### Conflicts

- A prompt constitution conflicts with Ranex's compiled-control model.
- Markdown tasks as status authority conflict with `work_management`.
- Same-maker validation and completion conflict with independence and no
  self-approval.
- Spec Kit shell/workflow execution conflicts with deny-by-default capability
  control and effect authorization.
- Direct integration or remote extension activation conflicts with qualified,
  pinned routes and the extension lifecycle.
- In-place mutation of a sealed living spec conflicts with exact-subject
  immutability and downstream invalidation.
- Stars and model agreement conflict with Ranex evidence policy if treated as
  correctness or effectiveness proof.

## Requirements and non-goals

Any accepted adaptation must:

1. preserve current state and effect owners;
2. use Ranex-native semantics and exact-subject bindings;
3. treat friendly Markdown, command names, queues, boards, and external issues
   as views or proposals only;
4. record owner answers with provenance and retain unresolved `UNKNOWN` states;
5. create immutable revisions/supersession and invalidate dependent artifacts
   when intent changes;
6. separate maker, independent reviewer/checker, gate evaluation, human
   decision, and landing;
7. distinguish deterministic qualified checks from advisory model findings;
8. route every external effect through exact destination binding,
   least-privilege authority, idempotency, evidence, and reconciliation;
9. preserve qualified route locks and the existing extension
   quarantine/qualification/human-activation lifecycle;
10. predeclare experiment measures, comparison, and stopping rules; and
11. record attribution and license obligations before incorporating exact
    upstream source or templates; and
12. bind the `checklist`/`analyze` and `converge` steps to the **enforced**
    finding contract, not to advisory prose.

**On requirement 12 — added 2026-07-30 after independent review.** Spec Kit is
designed for a technical developer driving an AI, who can judge for themselves
whether a returned specification is sound. Ranex's owner is explicitly
non-technical and, by design, should not have to make that judgement. That
inverts where the risk sits: `analyze` and `converge` are not conveniences here,
they are the owner's only defence against a specification that reads plausibly
and is wrong.

The mapping table routes `checklist`/`analyze` to `ReviewObservation` for
advisory reasoning. Advisory prose alone would let "analyze passed" mean nothing
more than "a model said it looked fine" — the exact failure this architecture
exists to prevent. `review-observation-v1` now enforces, as of the same date:

- `severity` is closed to SARIF 2.1.0 `result.level` (`none|note|warning|error`);
- a finding at the blocking level (`error`) must carry
  `epistemic_status: FACT`; and
- a `FACT` finding must cite at least one non-empty `evidence_ref`.

So a `converge` step may not report a blocking problem it merely inferred, and
may not claim verification while citing nothing. Non-blocking observations remain
freely expressible — an agent may still say "I think this is wrong" — it simply
cannot halt the owner's work on a hunch, or present a hunch as a finding of fact.

The measured basis for this requirement is on record: during the session that
produced this amendment, three separate claims by the assistant and by reviewing
models were plausible, well-formed, and false, each caught only by verification
at `path:line`. See
[`reviews/2026-07-30-kernel-tracer-adversarial-audit.md`](../reviews/2026-07-30-kernel-tracer-adversarial-audit.md).

Non-goals:

- installing or wrapping Spec Kit as Ranex's authority layer;
- feature parity with Spec Kit;
- reserving an ADR number or accepting a design;
- creating a new workflow, pipeline, spec, or extension bounded context;
- building a public marketplace or broad integration matrix now;
- making Markdown canonical;
- enabling remote catalogs, agent-local prompt authority, hooks, or shell
  workflows;
- allowing self-approval, auto-landing, auto-merge, or model gates;
- weakening any risk, readiness, lineage, migration, license, or upstream-sync
  control; and
- claiming product readiness or commercial value.

## Alternatives

### Option A — Selective Ranex-native façade (proposed)

Adapt the interaction patterns and selected taxonomies, compile them into
existing Ranex artifacts and state owners, and test the smallest slice before
adding infrastructure.

Advantages:

- captures the strongest usability ideas;
- preserves Ranex's differentiated assurance model;
- reuses existing full-map attachment points;
- permits measured, reversible learning; and
- avoids a second authority hierarchy.

Costs and risks:

- translation may lose some of Spec Kit's simplicity;
- friendly views must be proven lossless;
- requirements analysis can create noisy model findings;
- the workflow may add ceremony without validated user demand; and
- exact upstream reuse still needs provenance/legal handling.

### Option B — Install, fork, or wrap the Spec Kit CLI

Run Spec Kit directly or behind a Ranex adapter, then attempt to gate its
outputs.

Advantages:

- fastest route to visible commands and broad integrations;
- closer compatibility with the existing Spec Kit ecosystem.

Reasons not proposed:

- creates competing artifact and authority semantics;
- retains self-validation and Markdown completion behavior;
- exposes unsafe workflow/hook/shell and activation surfaces;
- makes exact subject, grant, effect, invalidation, and review boundaries hard
  to prove; and
- creates larger upgrade, provenance, and compatibility obligations.

### Status quo — No adaptation

Keep the current architecture and build only Ranex-original interaction
surfaces.

Advantages:

- lowest immediate scope and integration risk;
- no third-party terminology or provenance dependency.

Costs:

- may repeat mature interaction-design work;
- misses a recognizable onboarding path and useful requirements-quality
  vocabulary;
- provides no evidence about whether a familiar façade improves adoption.

## Proposed design

### 1. Owner-facing projection

Provide a friendly sequence whose labels are a UI decision, not canonical
artifact types:

```text
express intent
  -> clarify material unknowns
  -> inspect requirements-quality findings
  -> propose design and work breakdown
  -> independently analyze consistency
  -> perform governed execution
  -> independently assess convergence
  -> gate and human decision
```

The projection shows source, revision, unresolved unknowns, subject digest,
owner, and whether each result is advisory, deterministic, or authoritative.

### 2. Candidate artifact mapping

The mapping is deliberately provisional:

| Interaction | Existing candidate | Rule |
|---|---|---|
| Express intent / `specify` | `WorkIntake` plus owned outcome, requirement, and acceptance-criterion references | Prose is a generated view; canonical state remains typed and subject-bound. |
| Clarify | New `WorkIntake`/requirement revision and, where research is involved, `ResearchPacket` claims/unknowns | Owner answers are attributed; model suggestions are not owner facts. |
| Plan | `ArchitectureProposal`, ADR/RFC where required, and normal traceability | No prompt-level constitution gate. |
| Tasks | `TaskPacket` and later assignment compilation | A task view owns no status, grant, lease, or permit. |
| Checklist / analyze | `ReviewObservation` for advisory reasoning; `CheckerResult` only for qualified deterministic checks | Independent identity and exact subject required. |
| Implement | Existing governed run/assignment/attempt/lease/result/evidence chain | No canonical `[X]` self-mark. |
| Converge | Independent `ReviewObservation`, checker evidence where qualified, and proposed remediation work | A clean model report is not a pass. |
| External issues | `work_management` projection plus governed effect records | External state never becomes canonical. |

No new artifact type is accepted by this table. The experiment must first show
where existing types are insufficient.

### 3. Revision and invalidation

Flow-forward is the default: a changed requirement creates a new immutable
revision linked to the prior subject. A living or flow-back experience is
allowed only as a UI over:

1. an authenticated owner change;
2. a new immutable subject/revision;
3. explicit supersession/relation;
4. downstream dependency invalidation;
5. renewed plan/task/check/evidence bindings; and
6. the normal gate/human-decision path.

Implementation discoveries may propose a requirement change. They cannot enact
one.

### 4. Analysis and convergence

The first experiment should separate:

- deterministic joins: missing IDs, stale digests, uncovered requirement
  references, duplicate identifiers, illegal dependency direction;
- qualified semantic rules, if any can be specified and fixture-tested; and
- model observations: ambiguity, contradiction, missing edge cases, partial
  coverage, or unrequested behavior.

Model observations remain advisory and preserve confidence, evidence,
limitations, and unresolved uncertainty. A separate reviewer/checker identity
must assess the maker's exact subject.

### 5. Deferred ecosystem projection

If later evidence supports it:

- agent integrations become qualified `routing`/`WorkerRuntime` descriptors;
- presets become exact-digest instruction/tailoring/presentation profiles;
- workflow authoring compiles to existing approved workflow definitions;
- bundles compose only already qualified references; and
- extensions/catalog entries enter the existing `extension_host` lifecycle.

Discovery never implies installation, qualification, pinning, or activation.

## Dependency and file-structure impact

This DRAFT changes no target dependency edge or file map.

A bounded experiment should prefer existing homes and projections. Any new
public API, schema, registry, bounded context, dependency edge, CLI package, or
canonical file home requires a separate accepted design decision and regenerated
contracts. UI compatibility files, if any, must be generated projections, not
parallel semantic sources.

## Data, state, event, and transaction impact

No state or event change is accepted.

The experiment must demonstrate:

- owner-attributed, immutable revision records;
- exact links among intent, requirement, plan, task, result, finding, and
  remediation subjects;
- invalidation when any upstream digest changes;
- idempotent creation/reconciliation of any external projection;
- no distributed transaction assumption; and
- no external or UI projection writing canonical status.

If these cannot be represented with current artifacts, the gap must be reported
before proposing a schema or event.

## Security, privacy, and secrets

- Treat prompts, owner text, repository content, external tickets, downloaded
  packages, and model output as untrusted inputs.
- Do not execute Spec Kit hooks or workflow shell steps in the experiment.
- Do not interpolate untrusted text into shell commands.
- Do not expose raw standing credentials to a worker or model.
- Bind any external destination exactly and route the effect through
  `CapabilityBus`.
- Preserve data classification, egress policy, redaction, audit, lease,
  fencing, workspace, route, and task-minimal grant controls.
- Prevent models and packages from activating workflows, instructions, routes,
  presets, bundles, or extensions.

## Compatibility, migration, rollback, and upstream sync

The first experiment should copy no Spec Kit implementation/template into
tracked product paths. It may use original Ranex prompts/views informed by the
reviewed semantics.

If exact MIT-licensed material is later selected:

1. pin repository, commit, path, and digest;
2. identify copied versus modified material;
3. preserve the required copyright/license notice;
4. update `NOTICE.md` and `legal/licensing-manifest.json` as applicable;
5. obtain the repository's required owner/legal decision for distribution; and
6. define upstream update, compatibility, removal, and rollback policy.

The façade must be removable without losing canonical Ranex artifacts. A
rollback disables the view/adapter and preserves all underlying state and
evidence.

## Operations, backup, and recovery

The DRAFT adds no operation.

Any accepted implementation must include:

- durable interruption/resume for owner dialogue without replaying an answer;
- recovery from partial view generation;
- idempotent external effects and reconciliation;
- immutable evidence and audit retention under current policy;
- metrics that do not store raw sensitive prompts by default; and
- a safe disable path that leaves canonical Ranex work usable.

## Predeclared acceptance tests

Before a first experiment is authorized, bind exact fixtures and thresholds for:

1. **Projection fidelity:** every displayed requirement, owner answer, unknown,
   plan link, task link, and finding resolves to the exact canonical subject;
   no UI-only field gains authority.
2. **Owner attribution:** suggested answers remain proposals until explicitly
   accepted; unanswered material questions remain `UNKNOWN`.
3. **Revision/invalidation:** changing an accepted answer creates a new
   revision and invalidates every dependent stale artifact.
4. **Independence:** the maker cannot produce the authoritative review/gate or
   mutate the review subject.
5. **Determinism:** deterministic checks replay identically for the same exact
   subject and qualified checker version.
6. **Advisory honesty:** model findings retain evidence, confidence,
   limitations, and no-pass standing.
7. **Convergence anchors:** a hidden labeled set covers missing, partial,
   contradictory, unrequested, and clean cases; report false positives and
   false negatives.
8. **No self-completion:** maker progress cannot transition canonical
   `WorkItemStatus`, land, merge, release, or issue a permit.
9. **Effect safety:** if an issue projection is included later, replay creates
   no duplicate, remote mismatch denies, and external closure cannot change
   Ranex work state.
10. **Capability safety:** no prompt, hook, shell, catalog, package, or detected
    integration broadens the effective grant or becomes active.
11. **Outcome experiment:** compare against a declared baseline using owner
    time, ambiguity closure, confirmed/false findings, invalidation/rework, and
    cycle time; one tracer establishes technical fit only.
12. **Provenance:** shipped bytes contain no unregistered third-party source,
    template, notice, or dependency.

Exact thresholds and stopping rules remain owner decisions and must not be
invented by this RFC.

## Specialist review

HY3 and DeepSeek V4 Pro independently recommended selective, heavily modified
adoption and rejected prompt-level authority, self-approval, and unsandboxed
execution. Their raw responses are preserved in the evidence bundle.

Both offered useful product hypotheses. Both also made unsupported effort and
artifact-mapping assumptions. DeepSeek incorrectly described governed
workflow, extension, and issue-projection attachment points as missing; HY3
over-rejected integrations/extensions and over-narrowed artifact evolution.
The advisory reconciliation corrects these claims against the accepted full
map.

## Independent challenge

The principal challenge is that a compatibility façade could become a second
authority system by convenience:

- users may trust `spec.md` or an external issue over canonical state;
- a five-question flow may suppress rather than expose important unknowns;
- model-generated checklist/convergence findings may look deterministic;
- generated views may drift or become editable inputs;
- “workflow compatibility” may reintroduce shell, hooks, or implicit
  activation;
- ecosystem breadth may pressure Ranex to weaken route and extension
  qualification; and
- familiar commands may add ceremony without improving outcomes.

The proposal survives this challenge only if projection fidelity,
authority labeling, exact binding, independence, invalidation, and measured
outcomes are treated as acceptance criteria—not documentation promises.

## Reconciliation

Option A is the current recommendation because it captures useful interaction
design while preserving Ranex state/effect ownership. It is narrower than
either raw reviewer proposal:

- no new workflow engine or bounded context;
- no `ranex init` commitment;
- no new artifact schema by default;
- no broad adapter or extension program;
- one manual/bounded intake-to-convergence experiment first; and
- later surfaces require their own evidence and decisions.

The recommendation remains reversible. A failed experiment returns to the
status quo without migrating canonical state.

## Human decision requested

The owner is asked to decide only:

1. whether to accept selective Ranex-native adaptation as a direction for a
   bounded experiment;
2. whether the first experiment should be the proposed
   intake/clarify/check/analyze/converge slice;
3. which exact work item, subject, owner, measures, baseline, thresholds, and
   stopping rule bind that experiment;
4. whether familiar Spec Kit command names may appear in non-authoritative UI
   projections; and
5. whether any exact upstream material may be considered later, subject to
   provenance/legal review.

Acceptance of this RFC would still require a separately numbered ADR and
contract changes for any normative architecture, workflow, policy, state,
runtime, extension, or effect change. Rejection leaves the current architecture
unchanged.
