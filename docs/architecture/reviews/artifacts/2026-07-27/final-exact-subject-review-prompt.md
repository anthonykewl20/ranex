# Ranex Final Exact-Subject Full-Map Architecture Review

You are reviewing the complete target architecture and file structure for
Ranex. This is an advisory architecture review. Do not edit files and do not
claim decision, gate, merge, implementation, or release authority.

## Non-negotiable owner requirements

1. Established human software-development practice is the governing parent:
   governance, product discovery, requirements, architecture, planning,
   construction, independent verification and validation, configuration
   management, security, release, operations, incident response, maintenance,
   retirement, measurement, and improvement.
2. AI agents are workers inside that process. Agent orchestration must not
   redefine the SDLC, own `WorkItemStatus`, lower risk, manufacture evidence,
   approve its own work, consume a human decision, or authorize an effect.
3. This is a full-system/full-lifecycle map—not an MVP, v1, prototype, or
   near-term itinerary. Bounded implementation slices are routes through the
   already-complete map; they do not define its extent.
4. “Ground zero” means a dependency-clean Ranex authority/domain core built by
   strangler migration inside a governed and attributed derivative of
   `nousresearch/hermes-agent`. It does not mean an unrelated clean-room
   product or erased upstream history.
5. The repository does not yet prove Git ancestry to the pinned Hermes
   upstream. `SDLC-FORK-000 = PENDING` is therefore a real, fail-closed
   preflight that blocks runtime implementation commits. Do not repair that
   fact in prose or mistake a target architecture for completed adoption.
6. The desktop/Electron product is excluded. CLI, TUI, loopback web,
   text-phone delivery, GitHub, and authenticated triggers share the same
   application authority.
7. The six saved software-engineering works are major practice references
   inside the established SDLC hierarchy. They close underspecified
   requirements, architecture, file structure, construction, verification,
   professional-practice, operations, and improvement choices. They are not
   executable authority or universal numeric mandates.
8. The twelve saved full-text book artifacts are local-only and blocked from
   public Git, packaging, mirroring, and release pending documented rights.
   Their lawful bibliographic links, original reconciliation, and
   non-reconstructive digests are the public-safe substitute.
9. The Kimi corpus is advisory secondary research about worker-fleet control.
   Ranex adopts typed/fenced assignment, liveness, governors, transitive
   budgets, tool-boundary enforcement, artifact handoff, verifier capacity,
   recovery, and measured topology. It rejects generic competing task/status
   authority, full-permission workers, direct operator-to-gateway approval,
   self-merge, removal of human review, and unverified numeric thresholds.
10. DeepSeek V4 Pro is the primary architecture/file-structure specialist. HY3
    is a separate cross-family challenger. Neither is human authority, and
    model agreement is not proof.

## Exact-subject and evidence rules

- `final-exact-subject-source-manifest.sha256` inventories the frozen
  architecture, templates, research, reconciliation, visual, and legal source
  subject. It is the authoritative source-subject list for this round.
- `final-exact-subject-review-bundle-manifest.sha256` identifies every file
  whose text is attached to the request. Both independent reviewers receive
  the same attachment bytes and neither receives the other reviewer's output.
  The manifest itself is attached as a non-self-listed transport envelope
  because placing its own digest inside itself would be circular.
- Raw Kimi stages, saved full-text books, binary/rendered projections, and raw
  prior model responses are intentionally not placed in model context. Audit
  their treatment through their content-addressed manifests, the current
  normative synthesis, reconciliation records, `.gitignore`, and licensing
  manifest. Do not claim to have directly read an unattached artifact.
- This round's response files and the reconciliation record that will cite
  them are necessarily excluded from the source subject: review outputs cannot
  be inputs to their own review. That exclusion does not remove any normative
  architecture, lifecycle, contract, template, research reconciliation, or
  rights-control source from the subject.
- The earlier post-reconciliation round is historical advisory evidence. One
  broader source-inventory file changed during that round, so its verdict must
  not be inherited as a current exact-subject verdict.
- Treat the foundational-reference and Kimi reconciliation records as
  traceable summaries, not substitutes for runtime proof or primary-source
  verification.
- Distinguish normative requirement, current repository fact, target design,
  advisory evidence, unresolved research choice, and runtime-unvalidated
  claim.
- Missing evidence stays `UNKNOWN`; conflict stays `CONFLICT`; a model
  observation cannot become an accepted verdict.
- Find contradictions across documents, not just omissions within one file.
  Prefer a precise correction to a new abstraction.

## Audit the full map

- product/system context, capability coverage, exclusions, quality attributes,
  bounded contexts, aggregates, owners, public APIs, local transactions, and
  integration outboxes;
- domain/application/port/adapter dependency direction, composition root, and
  whether the modular-monolith boundaries avoid god packages and split
  authority;
- exact target/transitional source trees, one plausible file home per
  responsibility, canonical schema ownership, tests, operations, migrations,
  legal/provenance records, and architecture fitness rules;
- Core-SDLC `WorkItem` versus governed `Run`, worker assignment/attempt/lease,
  resource reservation, incident, release, capability, compatibility,
  extension, module, route, update, cutover, and migration lifecycles;
- gate/evidence/checker/review/human-decision/authority-grant/permit/effect
  ordering and atomicity;
- exact-subject identity, invalidation, replay, retry, idempotency, fencing,
  reconciliation, artifact purge, backup/restore, safe mode, and recovery;
- IAM, policy, secrets, egress, sandbox, provider/harness/tool, plugin,
  extension, legacy, release-signing, and maintenance trust boundaries;
- configuration/traceability, supplier/dependency, budget, interaction
  history, process assurance, delivery, operations, release, migration,
  provenance, de-commercialization, and upstream-sync coverage;
- Hermes lineage/adoption, selective porting, compatibility, one-writer
  cutover, upstream recontamination defenses, and desktop exclusion;
- contract/template fail-closed defaults, subject-binding consistency,
  canonical schema/tree agreement, registry completeness, and no circular
  digest identity;
- the established SDLC/book-practice/AI-worker authority hierarchy;
- public-repository licensing/rights controls and whether local-only artifacts
  can leak through Git, a package, a mirror, or a release;
- the development, verification, deployment, operations, maintenance, and
  retirement lifecycle needed to change this architecture safely.

## Required response

Return a concise but concrete report in exactly this structure:

1. `VERDICT`: `ACCEPTABLE_FOR_FORMAL_CONTRACTING`,
   `CHANGES_REQUIRED`, or `INCOMPLETE`.
2. `P0 FINDINGS`: numbered blockers with exact file/section, violated
   invariant, consequence, and precise correction. Write `NONE` if none.
3. `P1 FINDINGS`: same structure for corrections required before the first
   governed runtime tracer.
4. `P2 FINDINGS`: documentation, provenance, or clarity corrections.
5. `APP ARCHITECTURE AND FILE-TREE AUDIT`: missing, duplicated, cyclic, or
   misplaced responsibility and the exact target path/API/port/adapter
   correction.
6. `STATE, CONTRACT, AND AUTHORITY AUDIT`: namespace, subject, transition,
   transaction, registry, and authorization-order conflicts.
7. `HERMES-FORK AUDIT`: ancestry preflight, upstream sync, compatibility,
   desktop, de-commercialization, migration, and cutover gaps.
8. `SDLC, BOOK, AND AI BOUNDARY AUDIT`: any place where a book heuristic or AI
   worker becomes the lifecycle method or authority.
9. `RIGHTS AND RELEASE AUDIT`: paths or rules that could publish local-only,
   unlicensed, private, or provenance-defective material.
10. `TOP ACCEPTANCE TESTS`: the ten highest-value tests that would falsify the
    architecture.
11. `OPEN CONFLICTS OR UNKNOWNS`: only items that genuinely require human
    decision, upstream evidence, primary-source verification, or runtime
    research.

Do not reward length, rename ordinary concepts for novelty, or propose
microservices merely to separate responsibilities. Preserve a one-host
modular-monolith deployment unless evidence requires otherwise.
