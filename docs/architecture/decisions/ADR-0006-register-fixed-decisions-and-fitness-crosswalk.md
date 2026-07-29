# ADR-0006: Register the Fixed Decisions and Fitness Crosswalk

| Field | Value |
|---|---|
| ADR ID | `ADR-0006` |
| Version | `1.1.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a758f70d39af6a21e73488c61db5f82f32` |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | Complete Ranex target and all implementation packets |
| RFC | Not required; normalizes decisions already selected by the architecture/owner ADRs |
| Supersedes | No decision ID; ADR-0011 supersedes the selected meaning and governing ADR for rows `DEC-RANEX-017`, `025`, `026`, and `027` |
| Review/expiry date | On any fixed-decision change or architecture graph diff |
| Compatibility/migration class | Machine-readable decision register |
| Security/data class | Public architecture decision |

## Decision

The following fenced YAML block is the canonical, machine-checkable crosswalk
for the 29 fixed architecture decisions. The denominator remains 29 after
ADR-0011: that ADR strengthens four existing product dimensions rather than
creating overlapping new ones. A contract compiler must parse this block,
require exactly 29 unique `decision_id` values in the contiguous range
`DEC-RANEX-001` through `DEC-RANEX-029`, resolve every named ADR and fitness
function, and reject unknown fields or a non-`ACCEPTED` item.

```yaml
schema_version: "1.0.0"
register_id: "RANEX-FIXED-DECISIONS"
required_count: 29
decisions:
  - decision_id: "DEC-RANEX-001"
    name: "product-form"
    selected: "release-pinned modular monolith with bounded-context packages"
    owner: "human-owner"
    governing_adr: "ADR-0003"
    alternatives: ["microservices", "shared unbounded monolith"]
    fitness_functions: ["FF-BOUNDARY-001", "FF-PATH-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-002"
    name: "development-process"
    selected: "Core SDLC governs; AI L0-L12 is subordinate execution"
    owner: "human-owner"
    governing_adr: "ADR-0001"
    alternatives: ["AI-native lifecycle", "ticket-to-code pipeline"]
    fitness_functions: ["FF-SDLC-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-003"
    name: "engineering-references"
    selected: "frozen registered references are advisory practice inputs under Core SDLC"
    owner: "human-owner"
    governing_adr: "ADR-0001"
    alternatives: ["model intuition", "books as authority"]
    fitness_functions: ["FF-REF-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-004"
    name: "engineering-practice-application"
    selected: "each packet binds applicability, behavior, deviations, and verification"
    owner: "human-owner"
    governing_adr: "ADR-0002"
    alternatives: ["citation-only compliance", "unregistered convention"]
    fitness_functions: ["FF-REF-001", "FF-PACKET-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-005"
    name: "legacy-implementation-guide"
    selected: "retired and non-authoritative"
    owner: "human-owner"
    governing_adr: "ADR-0002"
    alternatives: ["retain as implementation authority", "silently archive"]
    fitness_functions: ["FF-GUIDE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-006"
    name: "upstream-relationship"
    selected: "Hermes-derived fork with blocking ancestry, history, license, and provenance preflight"
    owner: "human-owner"
    governing_adr: "ADR-0003"
    alternatives: ["unrelated clean-room repository", "unverified source copy"]
    fitness_functions: ["FF-FORK-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-007"
    name: "new-core"
    selected: "new authority/domain/application core has no inherited-Hermes dependency"
    owner: "architecture-owner"
    governing_adr: "ADR-0003"
    alternatives: ["extend inherited agent core", "implicit compatibility imports"]
    fitness_functions: ["FF-BOUNDARY-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-008"
    name: "migration"
    selected: "strangler migration inside the attributed fork"
    owner: "architecture-owner"
    governing_adr: "ADR-0003"
    alternatives: ["big-bang rewrite", "permanent dual authority"]
    fitness_functions: ["FF-MIG-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-009"
    name: "work-lifecycle-authority"
    selected: "work_management alone owns WorkItemStatus"
    owner: "work-management"
    governing_adr: "ADR-0003"
    alternatives: ["board authority", "run-derived work state"]
    fitness_functions: ["FF-AUTH-001", "FF-LIFE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-010"
    name: "canonical-authority"
    selected: "governed_execution authority cell owns run, gate binding, permit, and effect intent"
    owner: "governed-execution"
    governing_adr: "ADR-0003"
    alternatives: ["distributed writers", "worker-local authority"]
    fitness_functions: ["FF-AUTH-001", "FF-AUTH-002", "FF-PERMIT-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-011"
    name: "state-storage"
    selected: "single local SQLite authority database with logical ownership, journal, and outbox"
    owner: "governed-execution"
    governing_adr: "ADR-0003"
    alternatives: ["database per context", "remote distributed database"]
    fitness_functions: ["FF-CRASH-001", "FF-RESTORE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-012"
    name: "event-sourcing"
    selected: "selective governed-execution replay journal; product is not wholly event sourced"
    owner: "governed-execution"
    governing_adr: "ADR-0003"
    alternatives: ["full event sourcing", "mutable state without journal"]
    fitness_functions: ["FF-CRASH-001", "FF-ORCH-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-013"
    name: "workflow-runtime"
    selected: "local durable runner behind a stable runtime port"
    owner: "governed-execution"
    governing_adr: "ADR-0005"
    alternatives: ["Temporal initially", "in-memory callback chain"]
    fitness_functions: ["FF-ORCH-001", "FF-ORCH-002"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-014"
    name: "effects"
    selected: "declared at-least-once or at-most-once attempts with idempotency and reconciliation"
    owner: "governed-execution"
    governing_adr: "ADR-0003"
    alternatives: ["exactly-once claim", "untracked adapter effects"]
    fitness_functions: ["FF-CRASH-001", "FF-EFFECT-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-015"
    name: "policy-failure"
    selected: "blocking proof failure denies visibly"
    owner: "policy"
    governing_adr: "ADR-0003"
    alternatives: ["fail open", "model-decided fallback"]
    fitness_functions: ["FF-PDP-001", "FF-SAFE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-016"
    name: "model-authority"
    selected: "models produce proposals and observations only"
    owner: "human-owner"
    governing_adr: "ADR-0001"
    alternatives: ["model gate authority", "model-issued permits"]
    fitness_functions: ["FF-EVID-001", "FF-SAFE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-017"
    name: "AI-worker-fleet"
    selected: "Ranex control services alone orchestrate deterministic bounded fan-out/join; all model and harness workers are leaf-only; each assignment receives a task-minimal proper subset of its role capability ceiling; isolated writes and human-controlled landing"
    owner: "process-owner"
    governing_adr: "ADR-0011"
    alternatives: ["worker-controlled subagents", "unbounded fan-out", "always-parallel writers", "generic full-tool workers"]
    fitness_functions: ["FF-FLEET-001", "FF-FLEET-LEAF-001", "FF-ROLE-TOOLS-001", "FF-SESSION-001", "FF-DISPATCH-PERF-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-018"
    name: "first-party-capabilities"
    selected: "shipped behind stable internal interfaces"
    owner: "architecture-owner"
    governing_adr: "ADR-0003"
    alternatives: ["user-installed prerequisite", "direct vendor binding"]
    fitness_functions: ["FF-BOUNDARY-001", "FF-SUPPLY-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-019"
    name: "external-extensions"
    selected: "lower-trust out-of-process capability-scoped protocol outside authority"
    owner: "extension-host"
    governing_adr: "ADR-0005"
    alternatives: ["in-process plugins", "extension authority writes"]
    fitness_functions: ["FF-EXT-001", "FF-SBX-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-020"
    name: "desktop-app"
    selected: "excluded"
    owner: "product-owner"
    governing_adr: "ADR-0006"
    alternatives: ["Electron desktop", "desktop updater"]
    fitness_functions: ["FF-EXCL-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-021"
    name: "local-UX"
    selected: "CLI, TUI, loopback web, GitHub edge, and text-phone delivery port"
    owner: "product-owner"
    governing_adr: "ADR-0006"
    alternatives: ["desktop-only", "public web service"]
    fitness_functions: ["FF-DELIVERY-001", "FF-SEC-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-022"
    name: "phone-implementation"
    selected: "Telegram first adapter behind channel-neutral contracts"
    owner: "product-owner"
    governing_adr: "ADR-0006"
    alternatives: ["phone-specific authority", "no mobile delivery"]
    fitness_functions: ["FF-DELIVERY-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-023"
    name: "voice"
    selected: "mapped optional adapter, inactive"
    owner: "product-owner"
    governing_adr: "ADR-0005"
    alternatives: ["activate by default", "put media in authority kernel"]
    fitness_functions: ["FF-EXCL-001", "FF-PRIV-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-024"
    name: "public-dashboard"
    selected: "excluded; web binds to loopback"
    owner: "product-owner"
    governing_adr: "ADR-0006"
    alternatives: ["public binding", "unauthenticated LAN binding"]
    fitness_functions: ["FF-SEC-001", "FF-EXCL-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-025"
    name: "providers"
    selected: "one explicit qualified route/model/runtime per assignment through a Ranex-owned official typed runtime adapter; eligible local individual subscription or product API/BYOK/cloud route classes remain separate"
    owner: "routing"
    governing_adr: "ADR-0011"
    alternatives: ["Hermes parent-model dispatch", "terminal-skill dispatch", "credential-file impersonation", "unqualified dynamic provider"]
    fitness_functions: ["FF-ROUTE-001", "FF-RUNTIME-001", "FF-AUTH-ROUTE-001", "FF-SUPPLY-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-026"
    name: "Nous-commercial-product"
    selected: "Hermes/Nous is provenance, compatibility, and reference only: no live inference, parent-agent model loop, Portal/model route, credential/entitlement, billing, credits, subscription, managed tool pool, purchase, promotion, or fallback"
    owner: "product-owner"
    governing_adr: "ADR-0011"
    alternatives: ["hide commercial UI", "retain dormant commercial runtime", "reuse Hermes native OAuth adapter"]
    fitness_functions: ["FF-DECOMM-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-027"
    name: "remote-model-catalog"
    selected: "release-pinned catalog cannot activate or mutate a route; model/provider/adapter fallback, provider subagents, and auxiliary model calls are disabled"
    owner: "routing"
    governing_adr: "ADR-0011"
    alternatives: ["remote auto-activation", "model-selected route", "provider fallback chain", "worker-selected auxiliary model"]
    fitness_functions: ["FF-ROUTE-001", "FF-NO-FALLBACK-001", "FF-SAFE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-028"
    name: "risk"
    selected: "deterministic policy derives risk; worker input is untrusted observation"
    owner: "policy"
    governing_adr: "ADR-0003"
    alternatives: ["worker-declared risk", "model consensus"]
    fitness_functions: ["FF-PDP-001", "FF-SAFE-001"]
    status: "ACCEPTED"
  - decision_id: "DEC-RANEX-029"
    name: "merge"
    selected: "human-controlled landing"
    owner: "release-owner"
    governing_adr: "ADR-0001"
    alternatives: ["worker self-merge", "gate-only auto-merge"]
    fitness_functions: ["FF-LANDING-001"]
    status: "ACCEPTED"
```

## Fitness-function resolution

Fitness IDs defined in ADR-0003 through ADR-0005 and ADR-0011 resolve there.
In particular, ADR-0011 owns `FF-FLEET-LEAF-001`, `FF-ROLE-TOOLS-001`,
`FF-RUNTIME-001`, `FF-NO-FALLBACK-001`, `FF-SESSION-001`,
`FF-DISPATCH-PERF-001`, `FF-AUTH-ROUTE-001`, and the strengthened
`FF-DECOMM-001`. The remaining registry-level functions resolve as follows:

| ID | Required result |
|---|---|
| `FF-SDLC-001` | Every execution/activity maps to one Core-SDLC work item/state and no subordinate lifecycle can transition it. |
| `FF-REF-001` | Each reference/profile has an exact registered source, applicability, limitation, required behavior, deviation, and verification mapping. |
| `FF-PACKET-001` | A sealed packet is deterministic from pinned inputs and invalidates when a dependency changes. |
| `FF-GUIDE-001` | No active normative link, packet, generator, or route treats the retired guide as construction authority. |
| `FF-MIG-001` | Characterization, shadow/dual-read comparison, cutover, rollback, and no-dual-authority tests pass. |
| `FF-EFFECT-001` | Each effect declares attempt semantics, idempotency key, durable intent, outcome query, and reconciliation path. |
| `FF-SUPPLY-001` | Release manifest pins dependencies/providers and passes provenance, license, vulnerability, support, and exit checks. |
| `FF-EXCL-001` | Source, routes, packages, runtime, network, and SBOM contain no excluded surface. |
| `FF-DELIVERY-001` | Every channel uses the same command, challenge, decision, permit, authentication, replay, and audit contracts. |
| `FF-PRIV-001` | Consent, minimization, classification, retention, deletion, and egress tests pass for personal/media data. |
| `FF-LANDING-001` | Only the authenticated human landing path can integrate the exact reviewed/verified head, with rollback prepared. |

The compiler rejects a fixed decision if its referenced fitness evidence is
missing, stale, for another subject, or reports a blocking non-pass outcome.
The decision remains accepted while implementation readiness remains pending.

## Alternatives considered

1. **Keep the prose table only.** Rejected because row naming and completeness
   cannot be checked reliably across packets and generators.
2. **Create one ADR per row immediately.** Rejected as needless ceremony for
   already selected, related constraints; a row can receive a dedicated
   superseding ADR when evidence calls it into question.
3. **Treat the register as runtime proof.** Rejected because a decision and a
   passing implementation are different artifacts.

## Change and supersession

A change to one row requires a new accepted ADR naming the stable decision ID,
alternatives, evidence, migration, compatibility, security/operations impact,
fitness-function changes, and rollback. The register then points that stable ID
to the superseding ADR, as rows `017`, `025`, `026`, and `027` now point to
ADR-0011. IDs are never recycled or silently renumbered. A superseding ADR that
refines an existing dimension does not increase `required_count`; a genuinely
new, nonoverlapping fixed dimension requires an explicit denominator decision
and compatible migration of every exact-subject consumer.

## Engineering-reference application

The crosswalk operationalizes the advisory
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md)
§3, §5.1–§5.4, §6, §8, and §10. It records alternatives, ownership, decisions,
and falsifiable tests without treating any book as authority or copying its
text. The corpus limitations recorded by the map remain in force.

## Human approval

This ADR normalizes the owner-selected fixed positions already stated by the
accepted architecture and ADRs. It creates a checkable decision inventory; it
does not assert that its fitness functions currently pass.
