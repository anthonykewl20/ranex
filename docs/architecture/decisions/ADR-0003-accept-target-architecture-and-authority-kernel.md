# ADR-0003: Accept the Ranex Target Architecture and Authority Kernel

| Field | Value |
|---|---|
| ADR ID | `ADR-0003` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a758f70d39af6a21e73488c61db5f82f32` |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | All Ranex bounded contexts, authority records, evidence records, repository layout, adapters, and migration work |
| RFC | Not required; closes the owner-directed architecture contract |
| Supersedes | None |
| Review/expiry date | First target-mode tracer, then on any authority-boundary change |
| Compatibility/migration class | New target architecture with strangler migration from the pinned Hermes-derived substrate |
| Security/data class | Public architecture decision |

## Decision

The
[full-system architecture](../HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)
is accepted as Ranex's normative target architecture. Acceptance means that the
paper contract is the construction destination. It does **not** mean that the
current branch has passed fork preflight, executable-contract validation,
security qualification, recovery drills, performance objectives, or a
target-mode runtime tracer.

Ranex is one release-pinned modular monolith with explicit bounded-context
packages. The only canonical context source path is:

```text
src/ranex/<context>/
```

`src/ranex/contexts/<context>/` is rejected. Compatibility code lives below
`src/ranex/compatibility/`; adapters live below the owning context or the
explicit composition boundary. A second context-root convention may not be
introduced by a route plan, generator, example, or migration.

The authority kernel is single-valued:

| Authoritative record or decision | Sole owner | Explicit non-owners |
|---|---|---|
| `WorkItemStatus` and legal work-item transition | `work_management` | Runs, boards, models, agent assignments, review, assurance |
| `RunStatus`, run reducer, workflow node, gate binding, authority unit of work | `governed_execution` | Worker fleet, policy, assurance, models |
| `ConsumableAuthorityGrant`, `Permit`, permit consumption, effect intent/outcome/reconciliation | `governed_execution` | Policy, identity, adapters, workers |
| Rules, risk derivation, authorization snapshot, `HumanDecisionRecord` policy requirements | `policy` | Models, workers, delivery channels |
| Principal authentication, challenges, session/device binding, secret handles | `identity_access` | Policy, workers, delivery channels |
| Claims, `EvidenceEnvelope`, qualified `CheckerResult`, `EvidenceSnapshot`, `GateEvaluation` | `assurance` | Reviewers, governed execution, process assurance |
| `ReviewSpecification`, `ReviewRequest`, `AnalysisAttempt`, `ReviewObservation`, `ReviewVerdict`, `IndependenceEvaluation` | `analytical_review` | Assurance, governed execution, process assurance |
| SDLC conformance audits, capability assessments, corrective actions, fleet experiments | `process_assurance` | Runtime gate evaluator, workers |

`analytical_review` may publish immutable references to observations.
`assurance` may ingest those references as candidate evidence, qualify them,
and create an exact-subject evidence snapshot and `GateEvaluation`; it may not
rewrite or co-own the underlying `ReviewObservation`. `governed_execution` may
atomically bind a fresh passing `GateEvaluation` to a run and consume a valid
permit; it may not author the evaluation.

An authenticated human decision is an input to policy and assurance where the
governing rule requires judgment. It is never represented as a machine
`GateOutcome=PASS`. Policy may establish eligibility for an authority grant,
but only `governed_execution` issues and consumes the grant/permit inside the
authority transaction.

## Architectural standing

The target has three independently reported maturity states:

1. **Paper contract:** accepted by this ADR.
2. **Executable contract:** pending until canonical registries, schemas,
   generators, and drift checks pass `AI-G2`.
3. **Runtime qualification:** pending until fork preflight and the applicable
   structural, behavioral, security, recovery, and operating gates pass against
   an immutable exact subject.

A pass in one state cannot be inferred from another. In particular, a
`MAP-*` result cannot substitute for `AI-G2`, and neither can authorize an
implementation commit while `SDLC-FORK-000` is pending.

## Alternatives considered

1. **Keep the architecture conditionally selected until runtime exists.**
   Rejected because it leaves constructors without one accepted destination;
   implementation maturity is tracked separately instead.
2. **Use `src/ranex/contexts/<context>`.** Rejected because it conflicts with
   the complete target repository map and adds a redundant physical layer.
3. **Let each workflow component own its local gate or permit.** Rejected
   because duplicated authority permits disagreement and bypass.
4. **Let assurance own review observations.** Rejected because evidence
   qualification and independent analytical judgment are distinct lifecycles.
5. **Make every context a service.** Rejected because the local-first product
   does not justify distributed failure, consistency, deployment, and
   operations cost.
6. **Use one shared domain package.** Rejected because it erases ownership and
   makes authority writes difficult to constrain mechanically.

## Fitness functions and acceptance evidence

| ID | Required result |
|---|---|
| `FF-PATH-001` | The path registry, architecture tree, generated packages, import rules, and source tree contain only `src/ranex/<context>/` for context packages. |
| `FF-AUTH-001` | The lifecycle/data-ownership registries assign every authority-bearing type to exactly one owner and reject duplicate or missing owners. |
| `FF-AUTH-002` | Static imports plus integration tests prove that only `governed_execution` writes its authority tables and only `work_management` transitions work items. |
| `FF-EVID-001` | A review observation cannot directly produce `PASS`; only an `assurance` evaluator can create a subject-bound `GateEvaluation`. |
| `FF-PERMIT-001` | Stale, reused, wrong-subject, revoked, expired, or concurrently consumed grants/permits fail atomically. |
| `FF-LIFE-001` | Model/property tests cover every legal and illegal work/run transition, including block/resume, terminality, retry, and cancellation. |
| `FF-FORK-001` | `SDLC-FORK-000` binds ancestry, license, provenance, selected adoption strategy, and immutable baseline before runtime implementation. |
| `FF-BOUNDARY-001` | Dependency-graph checks report no forbidden edge, cycle, compatibility leak, or adapter-to-domain authority mutation. |

These are obligations, not claims that the current implementation passes.

## Engineering-reference application

This decision applies the frozen advisory corpus through the
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md),
especially §3 (ambiguity closure), §5.2 (decomposition), §5.3 (authority
seams), §5.4 (alternatives and fitness functions), §6 (file structure), §8
(verification), and §10 (guardrails). The references support practices; they
do not transfer decision authority. Corpus age, excerpt scope, transcription
quality, opinionated examples, and incomplete standards coverage remain the
limitations recorded in that map. No book text is copied into this ADR.

## Consequences

- Construction has one target path, context granularity, and record owner.
- The architecture can be accepted without overstating current runtime
  maturity.
- Cross-context writes require commands/events or the named atomic authority
  transaction, not shared-table convenience.
- Contract registries and tests are mandatory before implementation readiness
  can be claimed.

## Migration and rollback

Migration uses the strangler route from the pinned Hermes-derived baseline.
Historical paths remain readable through compatibility mappings but cannot
become new target paths. Any path or owner change requires a superseding ADR,
registry migration, compatibility plan, and proof that no two authorities are
live concurrently.

Rollback of an implementation restores the last qualified implementation; it
does not silently revoke this architecture decision. Reversal requires a
superseding owner-accepted ADR.

## Human approval

The human owner directed the team to close architectural ambiguity, use mature
engineering practice, and establish an enterprise-build-ready paper contract.
This accepted ADR records that architectural closure. It is not a
cryptographic signature, runtime permit, fork-preflight result, or production
approval.

