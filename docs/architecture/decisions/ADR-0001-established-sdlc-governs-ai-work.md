# ADR-0001: Established Software-Development Lifecycle Governs AI Work

| Field | Value |
|---|---|
| ADR ID | `ADR-0001` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-27 |
| Effective revision | Working tree based on `fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4` |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | All Ranex product, architecture, development, release, operations, and upstream-sync work |
| RFC | Not required; direct owner requirement |
| Supersedes | None |
| Review/expiry date | After two end-to-end tracers, then quarterly |
| Compatibility/migration class | New governing decision; existing Hermes/Ranex process records require mappings |
| Security/data class | Public architecture decision |

## Decision

Ranex uses established, human-developed software-engineering lifecycle practice
as its primary development operating model:

```text
govern
  -> shape
  -> discover
  -> specify
  -> design
  -> plan
  -> build
  -> verify
  -> release
  -> operate
  -> improve
  -> govern
```

The normative process is
[Ranex Core SDLC Operating Model](../CORE_SDLC_OPERATING_MODEL.md). The
[full-system architecture](../HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)
defines the system that this process builds. The
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md)
makes the frozen SWEBOK and saved-book corpus a major practice base for closing
unclear engineering details without transferring lifecycle authority. The
[AI-Agent Development Lifecycle](../AI_AGENT_DEVELOPMENT_LIFECYCLE.md) is a
subordinate execution protocol inside the core SDLC.

AI agents are workers and bounded automation. They may assist research,
requirements analysis, design, planning, implementation, testing, review,
release operation, and evidence preparation only under the applicable
human-owned SDLC state, role, packet, policy, and authority. They do not replace
software-engineering practice and may not create a parallel lifecycle, redefine
required evidence, lower risk, waive controls, approve their own work, or
authorize architecture, merge, release, operation, or closure.

Hermes remains the inherited fork substrate and a replaceable reasoning/worker
boundary. Hermes behavior does not define Ranex's development method or
canonical product state.

## Context

Ranex will use AI agents heavily, but increased execution capacity does not
remove the need for product discovery, requirements engineering, architecture,
configuration management, independent verification, secure development,
release engineering, operations, incident response, measurement, or
improvement. Those disciplines predate generative AI and have a broad standards
and empirical basis.

The owner explicitly directed that Ranex architecture be organized around the
researched software-development process and drive AI agents through that
process—not allow agent orchestration to organize or redefine software
development.

## Alternatives considered

1. **AI-native autonomous lifecycle.** Rejected because model behavior is
   probabilistic, provider-dependent, and not an authority system.
2. **Ticket-to-code pipeline.** Rejected because a ticket does not establish a
   validated problem, requirements, architecture, security, operability,
   release readiness, or product outcome.
3. **Model consensus as process authority.** Rejected because correlated
   opinions are neither deterministic proof nor accountable human judgment.
4. **One branded framework as the entire SDLC.** Rejected because no single
   planning framework covers the complete product, engineering, security,
   release, operations, incident, and fork-synchronization lifecycle.

## Consequences

### Positive

- Human accountability, engineering evidence, and lifecycle semantics remain
  stable when models or harnesses change.
- Hermes capabilities and AI-agent work attach to known software-engineering
  stages instead of creating agent-specific process islands.
- Product validation and implementation verification remain distinct.
- Security, reliability, provenance, release, operation, and learning are
  designed into work rather than appended after generation.

### Negative

- Agents cannot begin from an underspecified request merely because they can
  generate code.
- High-risk changes require more human judgment, independent review, and
  recovery evidence.
- Ranex must implement durable work-state, traceability, contract, and evidence
  infrastructure in addition to worker orchestration.

### Risks and remaining unknowns

- Initial thresholds, WIP limits, service objectives, and review depth require
  calibration from real Ranex evidence.
- Poorly designed automation could turn valid controls into performative
  ceremony; tracer trials must measure burden and defect detection.
- Process terminology can drift across work-item, run, agent-lifecycle, and
  adoption gates unless the machine registries enforce namespaces and
  crosswalks.

## State and effect ownership

- `work_management` owns the canonical core-SDLC `WorkItem` lifecycle.
- `governed_execution` owns child `Run`, activity, gate-binding, permit, and
  effect state.
- `policy` derives the risk lane and required assurance.
- Product, technical, service, security/data, release, and human-governor
  decisions retain their named human authority.
- Boards, chat transcripts, model verdicts, and Hermes session state are
  projections or evidence, never lifecycle authority.

## Dependency and source-layout changes

- `CORE_SDLC_OPERATING_MODEL.md` is the parent process policy.
- `AI_AGENT_DEVELOPMENT_LIFECYCLE.md` must map each `L0`–`L12` activity to core
  SDLC states and may not define a second work-item state machine.
- Machine contract registries must separately define `WorkItemStatus`,
  `RunStatus`, risk lanes, work classes, gate namespaces, roles, and their
  mappings.
- Agent adapters remain below application ports and never import or mutate
  process-policy state directly.

## Security and data classification

This decision adds no runtime data egress. It requires risk-proportionate secure
development, least-privilege worker grants, exact-subject evidence, separation
of duties, and authenticated human authority.

## Compatibility and migration

Existing Hermes behavior and Ranex implementation-guide phases are mapped into
the core SDLC without becoming canonical lifecycle authorities. Historical
records retain their vocabulary and receive versioned mappings. New work uses
the core state model.

## Rollback

This decision can be changed only by a superseding human-accepted ADR backed by
evidence. Disabling an AI harness or reverting an automation does not roll back
the core SDLC.

## Acceptance tests and evidence

1. A work item traces from problem signal through operated outcome.
2. Every AI run references one canonical work item, accepted inputs, risk lane,
   and current SDLC state.
3. No AI lifecycle stage can transition a work item, issue a permit, accept
   architecture/risk, merge, release, or close work without the named
   authority.
4. A requirements, design, subject, policy, or risk change invalidates the
   dependent packet and evidence.
5. Hermes, model, route, or harness replacement does not change core process
   semantics.
6. The same state and gate namespaces are represented in prose and machine
   contracts without collision.

## Human approval

The human owner explicitly approved this direction in the authenticated project
conversation on 2026-07-27: established software-development practice is the
main base for Ranex, and AI agents are workers required to follow it. This ADR
is the durable repository record of that owner decision; it does not claim a
cryptographic signature or runtime permit.

## Supersession rule

This ADR is not edited to reverse its decision. A replacement ADR names and
supersedes it.
