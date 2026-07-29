# Final Ranex Full-Map Architecture Review Prompt

You are reviewing the complete target architecture for Ranex. This is an
advisory architecture/file-structure review. Do not edit files and do not claim
decision, gate, merge, or release authority.

Non-negotiable owner requirements:

1. Established human software-development practice is the governing parent:
   product discovery, requirements, architecture, planning, construction,
   independent verification and validation, configuration management,
   security, release, operations, incident response, maintenance, retirement,
   measurement, and improvement.
2. AI agents are workers inside that process. Agent orchestration must not
   redefine the SDLC, own `WorkItemStatus`, lower risk, manufacture evidence,
   approve its own work, or authorize an effect.
3. This is a full-system/full-lifecycle map—not an MVP, v1, prototype, or
   near-term itinerary. Safe implementation slices are routes through the map;
   they do not define its extent.
4. “Ground zero” means a dependency-clean Ranex authority/domain core built by
   strangler migration inside a governed, attributed fork of
   `nousresearch/hermes-agent`. It does not mean an unrelated clean-room
   product or erased upstream history.
5. The desktop/Electron product is excluded. CLI, TUI, loopback web, text-phone
   delivery, GitHub, and authenticated triggers share the same application
   authority.
6. DeepSeek V4 Pro is the primary architecture/file-structure specialist. HY3
   is the separate cross-family challenger. Neither is a human decision
   authority and DeepSeek cannot independently approve architecture it helped
   design.

Evidence rules:

- Read every attached text artifact and use `source-manifest.sha256` as the
  exact subject inventory.
- The generated SVG is bound by digest in the manifest. Its authoritative
  source is the Mermaid block in the real-world SDLC research; the semantic
  HTML is its accessible projection. Do not treat the SVG as a separate
  normative source.
- The original five research reports were read during the historical model
  passes. Re-audit them where attached; do not assume an old reconciliation is
  still valid for the current architecture.
- Distinguish normative requirement, current repository fact, target design,
  advisory evidence, R&D choice, and runtime-unvalidated claim.
- A model consensus is not proof. Missing evidence stays `UNKNOWN`; conflict
  stays `CONFLICT`.

Audit the full map:

- bounded contexts, aggregates, ownership, public APIs, local transactions and
  integration outboxes;
- domain/application/port/adapter dependency direction and composition;
- exact source tree and whether every responsibility has one plausible file
  home;
- Core-SDLC `WorkItem` versus governed `Run`, incident, release, capability,
  compatibility, extension, module, route, update, cutover, and migration
  lifecycles;
- gate/evidence/human-decision/authority-grant/permit/effect ordering;
- exact-subject identity, invalidation, replay, retry, idempotency,
  reconciliation, artifact purge, backup/restore, and safe-mode semantics;
- IAM, policy, secrets, egress, sandbox, provider/harness/tool, extension, and
  legacy trust boundaries;
- product definition, service management, configuration/traceability,
  supplier/dependency, resource budget, interaction history, process
  assurance, delivery, operations, release, migration, provenance, and
  upstream-sync coverage;
- Hermes lineage/adoption, selective porting, de-commercialization,
  compatibility, one-writer cutover, and desktop exclusion;
- schema/contract generation, tests, architecture fitness gates, and the
  development lifecycle needed for changing this architecture safely.

Return a concise but concrete report in this exact structure:

1. `VERDICT`: `ACCEPTABLE_FOR_FORMAL_CONTRACTING`,
   `CHANGES_REQUIRED`, or `INCOMPLETE`.
2. `P0 FINDINGS`: numbered blockers with exact file/section, violated
   invariant, consequence, and precise correction. Write `NONE` if none.
3. `P1 FINDINGS`: same structure for pre-tracer corrections.
4. `P2 FINDINGS`: documentation/provenance/clarity corrections.
5. `OWNERSHIP AND FILE-TREE AUDIT`: missing, duplicated, or misplaced
   responsibility and the exact target path/API/port/adapter correction.
6. `STATE AND AUTHORITY AUDIT`: namespace, transition, transaction, and
   authorization-order conflicts.
7. `HERMES-FORK AUDIT`: lineage, upstream-sync, compatibility, desktop,
   de-commercialization, and cutover gaps.
8. `SDLC/AI BOUNDARY AUDIT`: any place where AI becomes the method or authority
   instead of a worker.
9. `TOP ACCEPTANCE TESTS`: the ten highest-value tests that would falsify the
   architecture.
10. `OPEN CONFLICTS OR UNKNOWNS`: only items that genuinely require human
    decision or runtime research.

Do not reward length, rename ordinary concepts for novelty, or propose
microservices merely to separate responsibilities. Prefer the smallest
coherent correction that preserves one-host modular-monolith deployment and
the full map.
