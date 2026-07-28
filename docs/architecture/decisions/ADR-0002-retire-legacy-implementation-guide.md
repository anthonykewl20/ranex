# ADR-0002: Retire the Legacy Implementation Guide and Require Engineering-Practice Profiles

| Field | Value |
|---|---|
| ADR ID | `ADR-0002` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a67843b02d5970f442fb54aed8d6525dda` |
| Content binding | Exact digest is recorded externally in the next immutable review/release source manifest |
| Affected contexts | Architecture, source precedence, work management, context compilation, configuration management, process assurance, provenance/compliance, and every Ranex construction activity |
| RFC | Not required; direct owner requirement |
| Supersedes | Every active construction, capability-checklist, bootstrap-playbook, and operational-requirement use of the deleted root implementation guide |
| Does not supersede | Immutable historical research, review output, source manifests, or execution records that truthfully record the guide as a past input |
| Review/expiry date | First manual tracer, first runtime tracer, then quarterly |
| Compatibility/migration class | Removal of a conflicting planning source; historical records remain readable through an archival-only mapping |
| Security/data class | Public architecture decision; saved full-text engineering references remain `LOCAL_ONLY` |

## Decision

The root legacy implementation guide is deleted and permanently retired as an
active Ranex source. It must not be restored, regenerated, quoted into a task,
or used from Git history, another branch, a review bundle, a research report,
or model memory to direct new work.

New Ranex work is derived only from:

1. the accepted Core SDLC and control catalog;
2. the full-system architecture and source-of-truth policy;
3. accepted ADRs and RFC decisions;
4. executable architecture registries and schemas;
5. exact requirements, evidence, and task packets; and
6. the Engineering Reference Application Map's governed application of
   SWEBOK V4.0a, *Code Complete*, *Clean Code*, *The Pragmatic Programmer*,
   *System Design Interview*, and *The Clean Coder*.

The six works are practice inputs, not decorative citations. At contract
readiness, `engineering-practices.yaml` registers each adopted practice with
its source, scope, limitation, required behavior, and verification method.
Every architecture or implementation packet binds an exact engineering-practice
profile that:

- evaluates all six source families for applicability;
- identifies the practices actually required by the work;
- states how each applicable practice changes design, construction,
  verification, operation, or professional conduct;
- records evidence for `NOT_APPLICABLE`;
- blocks on a material `UNKNOWN`;
- records any deliberate deviation and its decision authority; and
- never embeds or republishes unauthorized full-text source material.

A book heuristic cannot override law, rights, an owner decision, the Core SDLC,
security, recovery, or measured Ranex evidence.

## Context

The retired guide accumulated useful observations alongside a plugin-first
office core, duplicate lifecycle and role vocabularies, conflicting path and
storage proposals, and an implementation order that could build branding or
worker orchestration before the authority and contract seams. Retaining it at
lower precedence still allowed future workers to select convenient stale
instructions and contaminate the dependency-clean target.

The foundational works have already been read, reconciled, and mapped to named
engineering responsibilities. The remaining need is operational adoption:
packet-level practice selection, observable application, independent
verification, and outcome evidence.

## Alternatives considered

1. **Keep the guide at lower precedence.** Rejected because duplicated
   prescriptions remain an attractive but conflicting construction source.
2. **Rewrite the guide in place.** Rejected because it would duplicate the
   Core SDLC, architecture, contracts, and route plan and would obscure which
   source owns a decision.
3. **Delete it without a decision record.** Rejected because historical
   manifests and research would leave ambiguous references that a future agent
   might treat as recoverable authority.
4. **Treat every book statement as a mandatory rule.** Rejected because the
   works contain contextual, dated, opinionated, incomplete, or mutually
   conflicting advice. Applicability, limitations, and evidence remain
   mandatory.

## Consequences

### Positive

- One coherent authority chain drives construction.
- Plugin-first, duplicate-state, and stale phase-order assumptions cannot
  silently re-enter the product.
- The six foundational works affect actual task behavior and verification
  through explicit, inspectable profiles.
- Future implementation routes start from the complete architecture rather
  than from a legacy itinerary.

### Negative

- Useful host or upstream observations formerly recorded only in the guide
  must be re-observed and accepted in their proper runbook, requirement, or
  contract home.
- Historical guide-derived phase records need an archival mapping to the Core
  SDLC when they are queried.
- Practice-profile compilation and verification add bounded work to packet
  preparation.

### Risks and remaining unknowns

- A performative profile could cite principles without changing behavior.
  Verification must therefore bind required behavior to tests, review, code,
  operational evidence, or an explicit decision.
- Over-application can become ceremony. Profiles select practices by work
  class, lifecycle stage, risk, and subject rather than copying every maxim
  into every packet.
- Exact practice IDs and conditional schema validation remain part of
  `AI-G2`; no current YAML example proves runtime enforcement.

## State and effect ownership

This decision creates no runtime transition or external effect.
`instruction_registry` owns the future registered practice definitions,
`context_compilation` owns exact practice-profile compilation,
`configuration_management` binds the profile into traceability, and
`process_assurance` measures whether practice application is real and useful.
The accountable Core-SDLC roles retain all acceptance authority.

## Dependency and source-layout changes

- Delete the root legacy implementation guide.
- Add `architecture/contracts/engineering-practices.yaml` to the target
  contract registry.
- Add `engineering-practice-profile-v1` to the task-packet contract family.
- Keep the public-safe synthesis in
  `docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md`.
- Keep full-text book artifacts local-only under `docs/research/books/`.
- Derive future implementation sequencing from architecture routes and
  accepted work items; do not create another monolithic guide.

## Security and data classification

No runtime permission or egress is added. Full-text book files and derivatives
remain `CURATED_RESEARCH`, `NOASSERTION`, `LOCAL_ONLY`, and
`PROHIBITED_PENDING_RIGHTS`. Practice profiles use stable IDs and original
Ranex synthesis, not reconstructive excerpts.

## Compatibility and migration

Historical source manifests retain the deleted path and digest because they
bind an earlier exact subject. Research and review prose remains immutable
historical evidence. Those references do not make the file part of the live
tree or a current source.

The guide's old phase vocabulary may be mapped only to interpret already
recorded historical work. It cannot generate a new work item, state
transition, task packet, implementation order, or acceptance criterion.

## Rollback

Reintroducing the old guide is prohibited. A future need for consolidated
operator instructions must create a narrowly scoped, tested runbook from
current authoritative sources. A future implementation roadmap must be a
generated or versioned projection of accepted work and architecture contracts.
Either change requires a superseding human-accepted ADR.

## Acceptance tests and evidence

1. The root legacy guide is absent from the live tree.
2. No active normative document treats it as a construction or operational
   source.
3. Historical manifests and review outputs remain byte-preserved and are
   clearly classified as historical evidence.
4. The licensing manifest no longer classifies the deleted file as a live
   repository file.
5. The machine-contract target includes `engineering-practices.yaml`.
6. The task-packet target includes an exact engineering-practice profile with
   applicability, behavior, deviation, and verification fields.
7. The six full-text Markdown files remain ignored/local-only and cannot enter
   a public package or release.
8. The first manual and runtime tracers demonstrate at least one applicable
   practice through behavioral evidence rather than citation alone.

## Human approval

The human owner explicitly directed in the authenticated project conversation
on 2026-07-28 that the six foundational works be practiced and used in
developing Ranex and that the legacy root implementation guide be removed so
it cannot pollute the build. This ADR records that decision; it does not claim
a cryptographic signature or runtime permit.

## Supersession rule

This ADR is not edited to reverse its decision. A replacement ADR names and
supersedes it.
