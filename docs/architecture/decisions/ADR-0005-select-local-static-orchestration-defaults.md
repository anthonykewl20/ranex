# ADR-0005: Select Local Static Orchestration Defaults and Substitution Gates

| Field | Value |
|---|---|
| ADR ID | `ADR-0005` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a758f70d39af6a21e73488c61db5f82f32` |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | Governed execution, policy, agent collaboration, context compilation, routing, repository intelligence, extension host, artifacts, delivery |
| RFC | Not required; closes construction defaults while retaining evidence-triggered substitution |
| Supersedes | None |
| Review/expiry date | After two representative target-mode tracers or on a substitution proposal |
| Compatibility/migration class | Initial local single-host profile |
| Security/data class | Public architecture decision |

## Decision

Ranex begins with the smallest deterministic topology that satisfies the full
architecture. Defaults are binding construction decisions, not open questions:

| Area | Selected default | Evidence-triggered substitution gate |
|---|---|---|
| Product/process topology | One release-pinned modular monolith; bounded contexts are packages, not services | `SUB-TOPOLOGY-001`: measured independent scaling/failure/deployment need, consistency analysis, operations ownership, migration/rollback proof |
| Workflow runtime | Ranex local durable runner behind the runtime port | `SUB-RUNNER-001`: candidate passes replay, timer, signal, cancellation, upgrade, crash, determinism, operability, and migration parity |
| Policy decision point | Built-in deterministic, versioned local PDP behind the policy port | `SUB-PDP-001`: candidate passes offline-deny, semantic parity, versioning, latency, authoring, audit, rollback, and supply-chain qualification |
| Linux worker isolation | Qualified `bubblewrap` profile for standard local lanes; deny execution when unavailable/unqualified | `SUB-SANDBOX-001`: alternative proves equal or stronger real file/process/network/secret/escape denial and acceptable operability/performance |
| Context selection | Deterministic manifest/filter/ranking rules with recorded inputs | `SUB-CONTEXT-001`: graph/learned candidate wins repeated equal-budget holdouts without freshness, provenance, latency, or failure regression |
| Model/provider routing | Static explainable release-pinned routes and explicit fallbacks | `SUB-ROUTING-001`: candidate wins repeated holdouts, remains policy bounded, supports hidden evaluation/drift/rollback, and cannot self-activate |
| Worker topology | One writer/implementer by default; parallel read-only research/review fan-out when declared; isolated write branches; serialized human-controlled landing | `SUB-FLEET-001`: repeated equal-budget experiment exceeds the registered effect threshold and passes claim/lease/fencing/backpressure/landing safety |
| Lease profile | 60-second lease, heartbeat every 15 seconds, renewal no later than 30 seconds remaining, 15-second post-expiry reclaim grace; values release-pinned | `SUB-LEASE-001`: false-expiry, detection latency, overhead, fencing, suspend/resume, and recovery measurements justify a new profile |
| Orchestration policy | Static typed workflows and topology rules | `SUB-ORCH-001`: measurement maturity, hidden evaluation, tamper resistance, bounded exploration, drift alarms, rollback, human activation, and accepted superseding ADR |
| Repository intelligence | Initial qualification targets Python, TypeScript/JavaScript, Markdown, YAML/JSON, and POSIX shell; unqualified language/construct returns `UNKNOWN` | `SUB-LANG-001`: add a language only after versioned fixtures, freshness, unsupported-construct, and fallback tests |
| Extension wire protocol | Versioned JSON-RPC 2.0 messages over local stdio behind the extension port; capability grants and schema negotiation required | `SUB-EXT-001`: candidate passes capability, identity, crash, quarantine, migration, compatibility, backpressure, and framing tests |
| Artifact integrity | Content digests plus an append-only local journal and daily separately protected signed/witnessed anchor before live authority | `SUB-ANCHOR-001`: replacement threat model and tamper tests show equal or stronger detection, availability, key separation, and recovery |
| Voice/media | Mapped but inactive | `SUB-VOICE-001`: accepted product need plus privacy, consent, retention, authentication, and media-adapter qualification |
| Multi-host control | Excluded from the current product | `SUB-MULTIHOST-001`: new product-scope ADR covers consistency, identity, transport, partition, scheduler, operations, backup, security, and migration |

The selected sandbox is a supported-profile choice, not permission to claim
isolation by process convention. If a supported host cannot enforce the
qualified profile, write-capable worker execution fails closed. A future
container profile may coexist only as a separately named and qualified lane.

Learned routing/orchestration is inactive code and configuration, if present.
It cannot observe secrets/hidden holdouts, write its own policy, promote a
route, weaken evidence, raise a budget, or activate itself.

## Substitution procedure

A substitution requires all of:

1. a registered problem and baseline on the same immutable subjects;
2. an explicit alternative and expected effect size;
3. repeated equal-budget tests including failure and adversarial cases;
4. raw evidence plus uncertainty, cost, latency, safety, operability, and
   rollback results;
5. no regression of authority, exact-subject, denial, recovery, or human
   control invariants;
6. independent review and deterministic verification;
7. an owner-accepted ADR naming migration, compatibility, and rollback; and
8. a release profile that pins the selected implementation/version.

Meeting a numeric experiment threshold does not activate a substitute.

## Alternatives considered

1. **Start with Temporal, OPA, Kubernetes, and a multi-service worker fleet.**
   Rejected because present scale and single-host scope do not justify their
   distributed operational and failure surface.
2. **Allow every implementation packet to choose.** Rejected because the same
   architecture would compile into incompatible systems.
3. **Select learned orchestration immediately.** Rejected because evaluation,
   drift, tamper, and rollback infrastructure must precede delegated control.
4. **Never permit substitution.** Rejected because measured workload or risk
   could invalidate an initial local choice.
5. **Treat all languages and hosts as supported.** Rejected because honest
   `UNKNOWN` is safer than analysis that silently misses constructs.

## Fitness functions

| ID | Required result |
|---|---|
| `FF-ORCH-001` | Deterministic replay produces the same next-node/decision sequence for the same definition, state, inputs, clock facts, and policy version. |
| `FF-ORCH-002` | Crash/signal/timer/cancellation/upgrade matrices preserve one legal run state and reconciled effects. |
| `FF-PDP-001` | Missing, stale, conflicting, malformed, timed-out, or unavailable blocking policy input denies visibly. |
| `FF-SBX-001` | Real worker processes fail file, authority-DB, home, secret, process, argument, output, and network bypass attempts. |
| `FF-FLEET-001` | Double claim, stale epoch, expiry/reclaim, orphan worker, child-budget escape, mailbox loss, and verifier saturation do not create authority or unsafe landing. |
| `FF-ROUTE-001` | Route identity, fallback, outage, drift, re-probation, cost, and output limits are deterministic and auditable. |
| `FF-EXT-001` | Malformed, oversized, slow, crashing, over-capability, and incompatible extensions are contained and quarantined. |
| `FF-RI-001` | Unsupported languages/constructs return `UNKNOWN`; stale indexes cannot produce a passing claim. |
| `FF-EXP-001` | Substitution experiments preserve raw paired results, uncertainty, subject digests, budgets, and non-activation proof. |

No current runtime pass is asserted.

## Engineering-reference application

This decision uses the advisory practice mapping in
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md)
§3, §5.1–§5.4, §6, §8, and §10: make the quality attributes explicit, compare
alternatives, assign boundaries, and encode falsifiable fitness functions.
The saved books are not standards, contain edition/excerpt and transcription
limitations, and do not select these technologies. These are Ranex decisions;
no book text is copied.

## Consequences, migration, and rollback

The defaults reduce the initial state space while preserving ports for evidence-
justified replacement. They impose real work for a durable runner, denial
testing, recovery, contract registries, and measurement. A substitution ships
through dual-read/shadow or other ADR-defined migration as appropriate and
must retain a rollback path until parity evidence is accepted.

## Human approval

The human owner requested closure of shallow architectural holes using mature,
proven practices. This ADR records construction defaults and explicit evidence
gates for replacing them. It does not claim the implementations exist or are
qualified.

