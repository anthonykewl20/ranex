# ADR-0013: Promote Hermes Research Obligations into a Closed Audit Contract

| Field | Value |
|---|---|
| ADR ID | `ADR-0013` |
| Version | `1.1.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-29 |
| Effective revision | Working tree based on `a66267776c`; executable documentation projection generated and runtime evidence pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `configuration_management`, `governed_execution`, `policy`, `assurance`, `module_governance`, `compatibility`, `migration`, `provenance_compliance`, `release_management`, and `process_assurance` |
| RFC | Not required; direct owner requirement to make already accepted Hermes-research obligations line-auditable and fail closed |
| Supersedes | No fixed decision; adds a closed, line-bound projection of obligations already accepted through ADR-0003, ADR-0005, ADR-0006, and ADR-0011 |
| Review/expiry date | On any source-research correction, promoted-provision change, owner-choice resolution, or de-commercialization/legal-control change |
| Compatibility/migration class | Additive executable documentation contract; runtime implementation remains unassessed |
| Security/data class | Public architecture decision; legal, credential, package, runtime, and release evidence retain their own classification |

## Revision history

### 1.1.0 — 2026-07-29

The owner rejects the prior classification of all migration phases as
“implementation sequencing, not fixed authority” for Phase 1. Research lines
1899–1912 define the clean kernel's binding structural inventory and behavior,
not a delivery schedule.

This revision adds eight promoted provisions,
`HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`:

1. shared identity and canonical serialization;
2. the `Execution` aggregate and pure reducer;
3. canonical relational execution state and version;
4. the append-only transition/audit journal and outbox in one SQLite unit of
   work;
5. the evidence-gated, `Execution`-only event-sourcing boundary;
6. the fail-closed application-control PEP, pure domain decisions, and
   deterministic policy adapter;
7. architecture import tests before feature code; and
8. the replay, crash-boundary, and no-Hermes-import exit gate.

It also adds `HERMES-OWNER-DECISION-020` as an
`OWNER_DECISION_REQUIRED` row for whether qualified `Execution` event sourcing
is activated, narrows `HERMES-RESEARCH-ONLY-008` to Phases 0/0A, and
adds `HERMES-RESEARCH-ONLY-013` for Phases 2–6.
Phase 1 is no longer included in a research-only sequencing disposition.

### 1.0.0 — 2026-07-29

Established the initial line-bound Hermes-research promotion catalog,
owner-decision register, and research-only dispositions.

## Decision

The Hermes architecture research is advisory evidence, not authority by itself.
This ADR promotes only the closed set below into an accepted documentation
contract. Each promoted provision names one exact research line, one
underscore-only guard, a deterministic check class, and the stage that must
block when the check does not pass.

The licensing, copyright, provenance, attribution, and history-preservation
provision is an external-obligation boundary. No owner, model, waiver, feature
flag, profile, or passing unrelated check may compensate for it.

Phase 1 is a binding clean-kernel inventory. Its heading is phased migration
context, but lines 1901–1911 define required parts, required behavior,
construction precedence, and a falsifiable gate. They are not treated as a
calendar, delivery estimate, or optional schedule.

`OWNER_DECISION_REQUIRED` has one precise meaning here: the choice is registered
but not selected by this ADR. Its `owner_decision_ref` and `default` remain
null, absence yields `BLOCK`, and activation without the exact accepted
decision is `DENIED`. The documentation-contract validator passes when that
fail-closed definition is intact; it does not convert an unresolved owner
choice into a runtime or release pass.

Later architecture material may discuss the same subject, but topical overlap
is not treated as an exact owner-decision binding. Satisfying one of these rows
requires a catalog revision that names the accepted decision and its
predeclared acceptance test; until then the reference remains null and the
named stage blocks.

The following YAML block is the one canonical source for the generated
promotion registry. The compiler and validator require the exact denominators,
field sets, source lines, source-excerpt digests, guard syntax, guard
uniqueness, and fail-closed outcomes. Runtime evidence begins
`NOT_ASSESSED`.

```yaml
schema_version: "hermes-research-promotion-catalog/v1"
catalog_id: "RANEX-HERMES-RESEARCH-PROMOTIONS"
catalog_version: "1.1.0"
catalog_status: "DEFINITION_ONLY"
governing_adr: "ADR-0013"
research_source: "docs/research/hermes-core-architecture-research-2026-07-27.md"
promoted_provision_count: 65
owner_decision_count: 20
research_only_count: 13
promoted_provisions:
  - provision_id: "HERMES-PROMOTION-001"
    status: "PROMOTED"
    guard_id: "GOVERNED_EXECUTION_IS_CORE_DOMAIN"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2264"
    source_end_line: 2265
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Ranex defines its core domain as governed deterministic execution rather than the agent loop."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-002"
    status: "PROMOTED"
    guard_id: "DEPENDENCY_CLEAN_KERNEL_EXISTS_BESIDE_HERMES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2266"
    source_end_line: 2266
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "The Ranex authority kernel is dependency-clean and built beside, not inward through, Hermes."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-003"
    status: "PROMOTED"
    guard_id: "WORKFLOW_REDUCER_IS_KERNEL_RESPONSIBILITY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2267"
    source_end_line: 2268
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Workflow semantics and the execution reducer are first-class kernel responsibilities."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-004"
    status: "PROMOTED"
    guard_id: "HERMES_IS_REPLACEABLE_PROPOSAL_DRIVER"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2269"
    source_end_line: 2270
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Hermes is contained as a replaceable worker and evolves only into a typed action-proposal driver."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-005"
    status: "PROMOTED"
    guard_id: "FAIL_CLOSED_CAPABILITY_BUS_MEDIATES_EVERY_EFFECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2271"
    source_end_line: 2271
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "One fail-closed capability bus mediates every governed effect."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-006"
    status: "PROMOTED"
    guard_id: "AUTHORITY_EVIDENCE_PERMITS_MODULES_AND_ATOMIC_STATE_ARE_KERNEL_OWNED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2272"
    source_end_line: 2273
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Policy enforcement, evidence and gate semantics, permit authority, module governance, and atomic event/outbox state remain kernel-owned."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-007"
    status: "PROMOTED"
    guard_id: "REQUIRED_CAPABILITIES_ARE_QUALIFIED_FIRST_PARTY_MODULES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2274"
    source_end_line: 2275
    check_class: "MODULE_FITNESS"
    blocking_stage: "MODULE_ACTIVATION"
    provision: "Required capabilities ship as qualified first-party modules in one product release."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-008"
    status: "PROMOTED"
    guard_id: "LEGACY_PLUGINS_STAY_BEHIND_CONSTRAINED_COMPATIBILITY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2276"
    source_end_line: 2276
    check_class: "MODULE_FITNESS"
    blocking_stage: "MODULE_ACTIVATION"
    provision: "Legacy Hermes plugins execute only behind a constrained compatibility boundary."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-009"
    status: "PROMOTED"
    guard_id: "LOCAL_TRACER_RETAINS_WORKFLOW_RUNTIME_PORT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2277"
    source_end_line: 2277
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "The first SQLite-backed tracer retains a replaceable workflow-runtime port."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-010"
    status: "PROMOTED"
    guard_id: "IMPORT_AND_RUNTIME_FITNESS_TESTS_ENFORCE_ARCHITECTURE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2278"
    source_end_line: 2278
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Import and runtime fitness tests enforce the accepted architecture."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-011"
    status: "PROMOTED"
    guard_id: "NOUS_COMMERCIAL_SUBSYSTEM_ABSENT_PROVIDER_NEUTRAL_COST_RETAINED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2279"
    source_end_line: 2281
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "The Nous commercial provider and account, credit, subscription, payment, entitlement, Portal, and promotional infrastructure are absent while provider-neutral cost and budget measurement remains."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-012"
    status: "PROMOTED"
    guard_id: "DOMAIN_IMPORTS_EXCLUDE_TECHNICAL_AND_HERMES_PACKAGES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1811"
    source_end_line: 1812
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Domain packages cannot import Hermes, CLI, gateway, database, provider, filesystem, HTTP, or tool packages."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-013"
    status: "PROMOTED"
    guard_id: "CROSS_CONTEXT_IMPORTS_USE_PUBLIC_API_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1813"
    source_end_line: 1813
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "A bounded context imports another context only through its public API."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-014"
    status: "PROMOTED"
    guard_id: "KERNEL_NEVER_DEPENDS_ON_FIRST_PARTY_MODULES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1814"
    source_end_line: 1815
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "First-party modules may depend on kernel public APIs, but the kernel cannot depend on modules."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-015"
    status: "PROMOTED"
    guard_id: "ADAPTERS_ARE_CONSTRUCTED_ONLY_AT_COMPOSITION_ROOT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1816"
    source_end_line: 1817
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Domain and application code do not import adapters; the composition root alone constructs them."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-016"
    status: "PROMOTED"
    guard_id: "MODULE_DEPENDENCY_GRAPH_IS_ACYCLIC_AND_MANIFEST_BOUND"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1818"
    source_end_line: 1818
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "The module dependency graph is acyclic and equals a checked-in manifest."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-017"
    status: "PROMOTED"
    guard_id: "MODULE_IMPORT_HAS_NO_SIDE_EFFECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1819"
    source_end_line: 1819
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Importing a module causes no registration, I/O, migration, thread, or other side effect."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-018"
    status: "PROMOTED"
    guard_id: "CANONICAL_WRITES_OCCUR_ONLY_IN_AUTHORITY_UNIT_OF_WORK"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1820"
    source_end_line: 1820
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "Canonical state writes occur only through the authority unit of work."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-019"
    status: "PROMOTED"
    guard_id: "EFFECT_REQUIRES_GRANT_AND_RECORDED_ACTIVITY_IDENTITY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1821"
    source_end_line: 1822
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "No external effect occurs without a capability grant and recorded activity identity."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-020"
    status: "PROMOTED"
    guard_id: "MODULE_CATALOG_CANNOT_OVERRIDE_PERMIT_ISSUER_OR_POLICY_PEP"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1823"
    source_end_line: 1823
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "MODULE_ACTIVATION"
    provision: "The module catalog cannot override a permit issuer or policy enforcement point."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-021"
    status: "PROMOTED"
    guard_id: "INELIGIBLE_MODULE_CANNOT_REGISTER_MIGRATE_RECEIVE_TRAFFIC_OR_EFFECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1824"
    source_end_line: 1825
    check_class: "MODULE_FITNESS"
    blocking_stage: "MODULE_ACTIVATION"
    provision: "A disabled, incompatible, unqualified, or quarantined module cannot register, migrate, receive traffic, or perform an effect."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-022"
    status: "PROMOTED"
    guard_id: "EXECUTION_KERNEL_ALONE_SELECTS_CANONICAL_NEXT_STATE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1839"
    source_end_line: 1839
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Only the execution kernel chooses a legal next canonical state."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-023"
    status: "PROMOTED"
    guard_id: "NONREPLACEABLE_PEP_ALONE_AUTHORIZES_AND_DISPATCHES_EFFECTS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1840"
    source_end_line: 1841
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "Only nonreplaceable application control authorizes and dispatches capabilities and effects using domain authorization decisions."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-024"
    status: "PROMOTED"
    guard_id: "EVERY_EFFECT_IS_COMPLETELY_MEDIATED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1842"
    source_end_line: 1842
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Every target-mode effect is completely mediated and no special agent-tool bypass exists."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-025"
    status: "PROMOTED"
    guard_id: "POLICY_OR_CHECKER_FAILURE_DENIES_BLOCKING_ACTION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1843"
    source_end_line: 1843
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "Policy or checker unavailability and error deny a blocking action."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-026"
    status: "PROMOTED"
    guard_id: "MAKER_CANNOT_APPROVE_OWN_SUBJECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1844"
    source_end_line: 1844
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "A maker cannot approve its own subject."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-027"
    status: "PROMOTED"
    guard_id: "EVIDENCE_AND_APPROVAL_BIND_EXACT_EXECUTION_SUBJECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1845"
    source_end_line: 1846
    check_class: "EVIDENCE_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "Evidence and approval bind the exact project, run, packet, commits, workflow version, and policy activation."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-028"
    status: "PROMOTED"
    guard_id: "PERMIT_IS_SINGLE_USE_SCOPED_EXPIRING_AND_CHANGE_INVALIDATED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1847"
    source_end_line: 1848
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "An approval or permit is single-use, scoped, expiring, and invalidated by material change."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-029"
    status: "PROMOTED"
    guard_id: "STATE_AUDIT_PERMIT_AND_OUTBOX_COMMIT_ATOMICALLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1849"
    source_end_line: 1850
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Canonical state and version, audit or domain record, permit consumption, and outbox intent commit atomically."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-030"
    status: "PROMOTED"
    guard_id: "RETRY_REUSES_LOGICAL_IDEMPOTENCY_IDENTITY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1851"
    source_end_line: 1851
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Every retry uses the same logical idempotency identity."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-031"
    status: "PROMOTED"
    guard_id: "REDUCER_HAS_NO_HIDDEN_NONDETERMINISM"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1852"
    source_end_line: 1852
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "The reducer has no hidden nondeterministic dependency."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-032"
    status: "PROMOTED"
    guard_id: "REPLAY_IS_DETERMINISTIC_FOR_PINNED_DEFINITION_VERSION_AND_HISTORY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1853"
    source_end_line: 1854
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Replay of the same definition, version, and history yields the same state and commands."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-033"
    status: "PROMOTED"
    guard_id: "HISTORY_REMAINS_EXPLAINABLE_AND_NEW_EFFECTS_USE_FRESH_AUTHORITY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1855"
    source_end_line: 1855
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "Historical decisions remain explainable and new effects use fresh authority."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-034"
    status: "PROMOTED"
    guard_id: "MODULE_CANNOT_WRITE_CANONICAL_STATE_OR_SELF_GRANT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1856"
    source_end_line: 1856
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "MODULE_ACTIVATION"
    provision: "Module code cannot write canonical state or grant itself capability."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-035"
    status: "PROMOTED"
    guard_id: "PLUGIN_FAILURE_CANNOT_WEAKEN_GATE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1857"
    source_end_line: 1857
    check_class: "MODULE_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "External plugin failure cannot weaken a gate."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-036"
    status: "PROMOTED"
    guard_id: "HUMAN_WAIVER_NEVER_BECOMES_MACHINE_PASS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1858"
    source_end_line: 1858
    check_class: "EVIDENCE_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "A human waiver remains visible as a waiver and never becomes machine PASS."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-037"
    status: "PROMOTED"
    guard_id: "LEGACY_COMMERCIAL_READER_IS_OFFLINE_AND_NONACTIVATING"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1604"
    source_end_line: 1607
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "MIGRATION"
    provision: "Any time-bounded legacy commercial reader is absent from normal startup and can only warn, redact, or translate to explicit BYOK without refreshing credentials or contacting Portal."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-038"
    status: "PROMOTED"
    guard_id: "LEGACY_NOUS_AUTH_IS_QUARANTINED_AND_NEVER_SILENTLY_TRANSFERRED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1608"
    source_end_line: 1613
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "MIGRATION"
    provision: "Legacy Nous auth and catalog data stays quarantined, reports an unsupported provider, and never silently transfers OAuth credentials into Ranex."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-039"
    status: "PROMOTED"
    guard_id: "COMMERCIAL_ACCOUNT_AND_PAYMENT_DATA_IS_NEVER_MIGRATED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1614"
    source_end_line: 1615
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "MIGRATION"
    provision: "Payment methods, subscriptions, balances, entitlements, and billing authorization data are never copied into Ranex."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-040"
    status: "PROMOTED"
    guard_id: "LICENSE_COPYRIGHT_PROVENANCE_ATTRIBUTION_AND_HISTORY_ARE_PRESERVED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1616"
    source_end_line: 1617
    check_class: "LEGAL_COMPLIANCE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "License, copyright, provenance, required upstream attribution, legal notices, and Git history are preserved."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-041"
    status: "PROMOTED"
    guard_id: "PRODUCT_SURFACES_ARE_REBRANDED_WITH_LEGAL_AND_RESEARCH_EXCEPTIONS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1618"
    source_end_line: 1621
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Hermes and Nous branding is absent from Ranex product surfaces except historical research citations and legally required attribution."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-042"
    status: "PROMOTED"
    guard_id: "CLEAN_HOST_MAKES_NO_NOUS_NETWORK_REQUEST"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1670"
    source_end_line: 1671
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "A clean-host Ranex run makes no DNS or HTTP request to a Nous, Portal, or Nous inference host."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-043"
    status: "PROMOTED"
    guard_id: "NOUS_IDENTIFIERS_DO_NOT_RESOLVE_AS_RUNTIME_PROVIDER_OR_CATALOG_OWNER"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1672"
    source_end_line: 1673
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "nous, nous-portal, and nousresearch do not resolve as a runtime provider or model-catalog owner."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-044"
    status: "PROMOTED"
    guard_id: "COMMERCIAL_COMMANDS_RPCS_SCHEMAS_AND_PROXY_ROUTES_ARE_UNREGISTERED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1674"
    source_end_line: 1675
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Top-up, subscription, billing RPC, checkout, card, auto-reload, and Portal proxy commands, schemas, and routes are unregistered."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-045"
    status: "PROMOTED"
    guard_id: "RUNTIME_PACKAGES_EXCLUDE_NOUS_CREDIT_OAUTH_ENTITLEMENT_AND_PRODUCT_TAGS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1676"
    source_end_line: 1678
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Runtime packages exclude Nous credit headers, billing scopes, providers.nous state, Portal OAuth scopes, managed-tool entitlements, and product=hermes-agent tags."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-046"
    status: "PROMOTED"
    guard_id: "REMOTE_CATALOG_CANNOT_ADD_OR_ACTIVATE_UNPINNED_MODEL"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1679"
    source_end_line: 1680
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "A remote model catalog cannot introduce or activate a model outside the release-pinned Ranex catalog and qualification record."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-047"
    status: "PROMOTED"
    guard_id: "CANONICAL_DATA_AND_BACKUPS_EXCLUDE_COMMERCIAL_AND_NOUS_AUTH_STATE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1681"
    source_end_line: 1682
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Sessions, canonical databases, exports, and backups contain no payment method, subscription, commercial balance, Portal entitlement, or Nous auth token."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-048"
    status: "PROMOTED"
    guard_id: "DISTRIBUTION_AND_SBOM_EXCLUDE_COMMERCIAL_IMPLEMENTATION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1683"
    source_end_line: 1685
    check_class: "SUPPLY_CHAIN_FITNESS"
    blocking_stage: "RELEASE"
    provision: "The wheel, container, and SBOM exclude dedicated billing UI, purchase clients, Nous provider plugins, generated billing bundles, and monetization-only dependencies."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-049"
    status: "PROMOTED"
    guard_id: "ROUTE_CENSUS_FINDS_NO_REACTIVATION_PATH"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1686"
    source_end_line: 1688
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Static and runtime route-census tests find no hidden import, command, hook, RPC, environment variable, URL, or feature flag that can reactivate the commercial subsystem."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-050"
    status: "PROMOTED"
    guard_id: "MISSING_DIRECT_TOOL_CREDENTIAL_NEVER_FALLS_BACK_TO_NOUS_GATEWAY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1689"
    source_end_line: 1691
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "A tool without direct credentials becomes unavailable and never tries a Nous managed gateway or commercial-subscription check."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-051"
    status: "PROMOTED"
    guard_id: "MODEL_FAILURE_NEVER_FALLS_BACK_TO_NOUS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1692"
    source_end_line: 1693
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "EFFECT_DISPATCH"
    provision: "Missing or failed model configuration fails closed and never selects Nous as an auxiliary or fallback model."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-052"
    status: "PROMOTED"
    guard_id: "LEGACY_AUTH_LOAD_HAS_NO_LOGIN_REFRESH_KEY_MINT_OR_NETWORK_EFFECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1694"
    source_end_line: 1695
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "MIGRATION"
    provision: "Legacy auth and config loading remains quarantined and cannot load a token, refresh credentials, log in, mint a key, or send network traffic."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-053"
    status: "PROMOTED"
    guard_id: "FUZZED_NOUS_HEADERS_HAVE_NO_STATE_OR_POLICY_EFFECT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1696"
    source_end_line: 1697
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Fuzzed x-nous headers cannot create state, notices, prompt content, tier selection, or tool gating."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-054"
    status: "PROMOTED"
    guard_id: "BUILT_ARTIFACTS_EXCLUDE_COMMERCIAL_FILES_BUNDLES_PLUGINS_AND_UI_PACKAGE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1698"
    source_end_line: 1699
    check_class: "SUPPLY_CHAIN_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Built wheel, npm bundle, and container scans find no dedicated commercial file, billing bundle, provider plugin, or @nous-research/ui package."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-055"
    status: "PROMOTED"
    guard_id: "PROVIDER_NEUTRAL_COST_AND_BUDGET_TELEMETRY_SURVIVES_REMOVAL"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1700"
    source_end_line: 1701
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "PRODUCTION_READY"
    provision: "Provider-neutral token, cost, and budget telemetry continues to work after commercial deletion."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-056"
    status: "PROMOTED"
    guard_id: "LICENSE_AND_ATTRIBUTION_VERIFICATION_PASSES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1702"
    source_end_line: 1702
    check_class: "LEGAL_COMPLIANCE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "License and attribution verification passes."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-057"
    status: "PROMOTED"
    guard_id: "PRODUCT_IDENTITY_EXCLUDES_HERMES_AND_NOUS_BRANDING"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1703"
    source_end_line: 1706
    check_class: "RELEASE_FITNESS"
    blocking_stage: "RELEASE"
    provision: "Product-facing packages, commands, configuration roots, headers, telemetry, help, screenshots, assets, and defaults do not present Hermes or Nous branding outside migration warnings or legally required attribution."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-058"
    status: "PROMOTED"
    guard_id: "SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION_DEFINE_KERNEL_RECORDS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1901"
    source_end_line: 1901
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "The clean kernel contains implemented shared-identity and canonical-serialization contracts that supply shared identities and canonical serialized representations for kernel records."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-059"
    status: "PROMOTED"
    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1902"
    source_end_line: 1902
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an Execution aggregate whose state evolution is computed by a pure reducer without observable side effects."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-060"
    status: "PROMOTED"
    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
    source_end_line: 1903
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel persists canonical execution state and its associated version in relational storage."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-061"
    status: "PROMOTED"
    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
    source_end_line: 1904
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-062"
    status: "PROMOTED"
    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
    source_end_line: 1906
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-063"
    status: "PROMOTED"
    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1907"
    source_end_line: 1908
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-064"
    status: "PROMOTED"
    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1909"
    source_end_line: 1909
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-065"
    status: "PROMOTED"
    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1911"
    source_end_line: 1911
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
    required_result: "PASS"
    failure_outcome: "BLOCK"
owner_decisions:
  - provision_id: "HERMES-OWNER-DECISION-001"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2125"
    source_end_line: 2125
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Canonical Ranex workflow and event schema and upcaster policy."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-002"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_LOCAL_RUNNER_OR_MATURE_DURABLE_RUNTIME"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2126"
    source_end_line: 2127
    blocking_stage: "PRODUCTION_READY"
    decision_subject: "Whether the local runner passes the required crash and recovery tests or a mature durable runtime is justified."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-003"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_EXACT_AUTHORITY_TRANSACTION_OWNERSHIP"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2128"
    source_end_line: 2129
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Exact transaction ownership across execution, evidence, permit, and work projections."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-004"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_ATLAS_COVERAGE_AND_UNKNOWN_BOUNDARY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2130"
    source_end_line: 2130
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Atlas supported-language coverage and the conditions that produce UNKNOWN."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-005"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_PARALLELISM_MAP_AND_COMPENSATION_SEMANTICS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2131"
    source_end_line: 2131
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Dynamic parallelism, map or fan-out, and compensation semantics."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-006"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_HOT_ACTIVATION_DURING_ACTIVE_EXECUTIONS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2132"
    source_end_line: 2132
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Whether and how hot module activation is allowed while executions are running."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-007"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_ACTIVE_MODULE_STATE_MIGRATION_AND_ROLLBACK"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2133"
    source_end_line: 2133
    blocking_stage: "MIGRATION"
    decision_subject: "State migration and rollback for active module versions."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-008"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_EXTERNAL_EXTENSION_PROTOCOL_AND_CAPABILITIES"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2134"
    source_end_line: 2134
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Secure external-extension protocol and capability vocabulary."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-009"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_POLICY_AUTHORING_LANGUAGE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2135"
    source_end_line: 2135
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Policy authoring language, including typed Python or JSON rules versus OPA or Cedar."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-010"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_REVIEWER_INDEPENDENCE_AND_JUDGE_THRESHOLDS"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2136"
    source_end_line: 2136
    blocking_stage: "GATE_ADVANCE"
    decision_subject: "Reviewer independence and calibrated model-judge thresholds."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-011"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_HOST_ISOLATION_PROFILE_AND_PERFORMANCE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2137"
    source_end_line: 2137
    blocking_stage: "PRODUCTION_READY"
    decision_subject: "Host isolation profile and acceptable performance."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-012"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_RETAINED_HERMES_SESSION_AND_SEARCH_SCOPE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2138"
    source_end_line: 2138
    blocking_stage: "MIGRATION"
    decision_subject: "How much inherited Hermes session and search behavior Ranex retains."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-013"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_KANBAN_PROJECTION_OR_TABLE_ADAPTER"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:758"
    source_end_line: 761
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Whether Kanban is a projection of canonical state or selected tables are adapted behind work management."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-014"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_FUTURE_PROVIDER_NEUTRAL_OPEN_WEIGHT_MODEL"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1568"
    source_end_line: 1572
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Whether a future release qualifies an independently hosted open-weight model originally published by Nous through a provider-neutral catalog."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-015"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_UNRELATED_PAYMENT_TOOL_SCOPE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1597"
    source_end_line: 1600
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Whether an unrelated third-party payment-system tool belongs in Ranex product scope and risk policy."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-016"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_VOICE_REQUIREMENT_BEFORE_MEDIA_ACTIVATION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1753"
    source_end_line: 1755
    blocking_stage: "MODULE_ACTIVATION"
    decision_subject: "Whether voice becomes an explicit requirement and therefore permits a separately qualified TTS or STT delivery adapter."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-017"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_DESKTOP_OR_LOCAL_WEB_TUI_PRODUCT_PATH"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1771"
    source_end_line: 1772
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Whether Electron and desktop bootstrap applications remain after selection of the local web or TUI product path."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-018"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_TIME_BOUNDED_HERMES_CLI_MIGRATION_SHIM"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1787"
    source_end_line: 1789
    blocking_stage: "MIGRATION"
    decision_subject: "Whether an existing-user transition requires a time-bounded hermes CLI migration shim."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-019"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_STRONG_CONSISTENCY_CONTEXT_GROUPING"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:865"
    source_end_line: 870
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Whether execution, gate, permit, and effect intent are submodules of one strong-consistency Governed Execution context or independently persistent contexts."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-020"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_EXECUTION_EVENT_SOURCING_AFTER_QUALIFICATION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
    source_end_line: 1906
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Whether to activate event sourcing for the Execution aggregate after its replay and migration tests justify that choice; the decision cannot authorize event sourcing for any other module."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
research_only:
  - provision_id: "HERMES-RESEARCH-ONLY-001"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:226"
    source_end_line: 341
    reason_code: "FACT_NOT_NORMATIVE"
    reason: "The pinned-source audit and scorecard are historical evidence about Hermes 0.19.0, not Ranex runtime obligations."
  - provision_id: "HERMES-RESEARCH-ONLY-002"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:343"
    source_end_line: 358
    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
    reason: "The reusable-seam assessments guide characterization and extraction, but each retained asset still needs exact-version qualification."
  - provision_id: "HERMES-RESEARCH-ONLY-003"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1129"
    source_end_line: 1154
    reason_code: "ILLUSTRATIVE_NONCANONICAL"
    reason: "The research explicitly labels the execution-state sketch illustrative and not the canonical enum."
  - provision_id: "HERMES-RESEARCH-ONLY-004"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1218"
    source_end_line: 1279
    reason_code: "SUPERSEDED_LAYOUT"
    reason: "The suggested layout is a research map; ADR-0007 now owns the exact canonical repository topology."
  - provision_id: "HERMES-RESEARCH-ONLY-005"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1551"
    source_end_line: 1590
    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
    reason: "Exact upstream file deletion and salvage rows are pinned-revision migration inputs; the promoted release gates check outcomes without assuming those paths still exist."
  - provision_id: "HERMES-RESEARCH-ONLY-006"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1729"
    source_end_line: 1758
    reason_code: "OWNER_SCOPE_NOT_SELECTED"
    reason: "The broad first-release profile list mixes accepted exclusions with conditional product-scope candidates and cannot be promoted as one blanket rule."
  - provision_id: "HERMES-RESEARCH-ONLY-007"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1760"
    source_end_line: 1783
    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
    reason: "Archive and source-removal candidates depend on compatibility windows and parity evidence that do not yet exist."
  - provision_id: "HERMES-RESEARCH-ONLY-008"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1860"
    source_end_line: 1898
    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
    reason: "The Phase 0 and Phase 0A freeze, characterization, and commercial-removal activities remain migration planning; the owner explicitly removed Phase 1 lines 1899-1912 from this disposition."
  - provision_id: "HERMES-RESEARCH-ONLY-009"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2006"
    source_end_line: 2090
    reason_code: "NONQUANTIFIED_RECOMMENDATION"
    reason: "The validation inventory is a test-design source; exact executable fixtures require an enacted runtime subject and are not fabricated by the documentation validator."
  - provision_id: "HERMES-RESEARCH-ONLY-010"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2092"
    source_end_line: 2155
    reason_code: "MATURITY_ASSESSMENT_NOT_CONTROL"
    reason: "Maturity labels and rejected foundations are advisory assessment; the genuine choices are separately registered as OWNER_DECISION_REQUIRED."
  - provision_id: "HERMES-RESEARCH-ONLY-011"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2157"
    source_end_line: 2258
    reason_code: "ADVISORY_MODEL_EVIDENCE"
    reason: "Limitations, HY3 execution facts, and reviewer-model maturity are provenance and evidence, not deterministic Ranex authority."
  - provision_id: "HERMES-RESEARCH-ONLY-012"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2283"
    source_end_line: 2310
    reason_code: "OWNER_SCOPE_NOT_SELECTED"
    reason: "Deferred capabilities and remove-from-core guidance do not authorize source deletion or activation; later scope ADRs and module contracts govern them."
  - provision_id: "HERMES-RESEARCH-ONLY-013"
    status: "RESEARCH_ONLY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1913"
    source_end_line: 2004
    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
    reason: "Phases 2 through 6 remain implementation planning in this revision; the owner decision promoting Phase 1 does not silently promote their sequencing or exit schedules."
```

## Noncompensating fitness functions

| ID | Required result |
|---|---|
| `FF-HERMES-PROMOTION-001` | The generated registry exactly projects all 65 promoted provisions, 20 owner-decision gates, and 13 research-only dispositions; every cited line and excerpt digest resolves to the immutable research source. |
| `FF-HERMES-GUARD-001` | Every promoted or owner-decision guard is unique and matches `^[A-Z][A-Z0-9_]*$`; a missing, malformed, duplicated, or hyphenated guard fails validation. |
| `FF-HERMES-OWNER-DECISION-001` | Every genuine owner choice is `OWNER_DECISION_REQUIRED`, has no default or synthetic decision reference, and blocks activation or progression while the exact accepted owner decision is absent. |
| `FF-HERMES-LEGAL-001` | License, copyright, provenance, required-attribution, legal-notice, and Git-history preservation are non-waivable release obligations; separate de-commercialization, package, network, credential, data, and branding checks remain noncompensating owner requirements rather than being mislabeled as law. |
| `FF-HERMES-KERNEL-001` | The clean-kernel inventory contains all eight Phase 1 provisions, binds only research lines 1901–1911, retains the one-SQLite-unit-of-work and Execution-only event-sourcing boundaries, requires import-test precedence, and cannot advance its gate without replay, crash-boundary, and no-Hermes-import proof. |

## What remains research

The thirteen `RESEARCH_ONLY` rows retain historical facts, advisory assessments,
illustrative shapes, conditional migration guidance, and unselected product
scope. They are not silently discarded. Promotion later requires a new accepted
ADR, an exact line binding, a deterministic checker contract, and migration or
compatibility treatment where applicable.

Those rows are a closed denominator of material disposition classes, not a
claim that every explanatory or bibliographic line is itself a provision.
Research text not named by a promoted or owner-decision row remains advisory
under the Source of Truth policy; omission from this catalog cannot promote it
by implication.

## Consequences

- Missing or reordered catalog rows, drifted citations, and malformed guards
  fail architecture validation.
- Phase 1 cannot be reclassified as mere sequencing or removed from the
  clean-kernel inventory without a superseding owner-accepted ADR and catalog
  revision.
- An unresolved owner choice cannot be activated by configuration, convention,
  model output, or a generator default.
- `PASS` from `validate_contracts.py` means the documentation contract is
  closed and faithful; all runtime and release evidence remains
  `NOT_ASSESSED`.
- Legal and attribution obligations remain outside owner waiver authority.

## Human approval

The human owner required these research-backed obligations to become
line-auditable and fail closed. This ADR records that direction. It is not
runtime evidence, a release permit, or a substitute for counsel where a legal
question requires legal advice.
