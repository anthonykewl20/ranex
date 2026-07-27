# DeepSeek V4 Pro and HY3 Full-Map Architecture Reconciliation

| Field | Value |
|---|---|
| Date | 2026-07-27 |
| Status | Advisory architecture evidence |
| Ranex HEAD at source capture | `fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4` |
| OpenCode version | `1.18.7` |
| Execution mode | `plan`, read-only, `--pure` |
| Primary collaborator | `deepseek/deepseek-v4-pro`, variant `high` |
| Independent challenger | `openrouter/tencent/hy3`, variant `high` |
| Repository mutations by reviewers | None |
| Decision authority | Human owner |

## 1. Purpose

The owner requested architecture and file-structure collaboration with HY3 and,
especially, DeepSeek V4 Pro. Two parallel review passes were performed:

1. a ground-zero architecture and file-structure pass; and
2. a corrected full-map completeness pass after the owner rejected MVP/v1-only
   documentation.

DeepSeek V4 Pro acted as the primary co-designer. HY3 received the same research
corpus independently and challenged boundaries, authority, completeness, and
testing. The final architecture was synthesized against local research and
repository evidence.

## 2. Frozen evidence corpus

All five files under `docs/research/` were attached and read in full.

| File | Lines | SHA-256 |
|---|---:|---|
| `cookbook-alignment-research-2026-07-27.md` | 1,496 | `344c14f6e5a475af2eebdd5ff444079188b5bf78c44c65fafbada662d352b4c7` |
| `gemini-research.md` | 302 | `db92a0c3dd9b51d3fbaa5b5072c00e79b81f6fcb853e552c02257eee8ec82a8a` |
| `hermes-core-architecture-hy3-review-2026-07-27.md` | 237 | `7d8e90898b0506a3ea32f6e4af3ed43eb34ef2049c129126dbdf9b4c3fccc0e7` |
| `hermes-core-architecture-research-2026-07-27.md` | 2,450 | `4c3e642ad245a62cdea14cdd508e5ec4a30314781127efa46ba6c06bafe5d29b` |
| `ocask-alignment-research-2026-07-27.md` | 2,779 | `f3a57e48b3081203922210081bfb22e19b0feeaabf5fea8ca8aa7a82d680e41f` |

Total: 7,264 lines.

`RANEX_IMPLEMENTATION_GUIDE.md` and the repository structure were also inspected
for context. The reviewers were not asked to modify files.

## 3. Review prompts and roles

### 3.1 DeepSeek V4 Pro — primary architecture collaborator

The first pass requested:

- system context and modular-monolith bounded contexts;
- domain/application/ports/adapters boundaries;
- deterministic workflow and state authority;
- evidence/gate and capability/sandbox semantics;
- model/provider adapter boundary;
- exact repository/package/file tree;
- dependency/public-API rules;
- data and transaction ownership;
- event/outbox strategy;
- configuration, schema, testing, observability, migration, and cutover;
- AI-agent development lifecycle; and
- challenges to potential god objects.

The corrected pass explicitly required the entire target-system map, including
every final attachment point for inactive or later-implemented capability zones.
It also fixed these owner inputs:

- Ranex remains a fork of `nousresearch/hermes-agent`;
- ground zero is a dependency-clean core inside the fork;
- the desktop app is excluded;
- CLI, TUI, local web, phone, and GitHub surfaces remain mapped; and
- implementation routes cannot define the map's extent.

### 3.2 HY3 — independent challenger

The first pass challenged:

- hidden coupling and god packages;
- authority bypass;
- workflow/replay correctness;
- split sources of truth;
- evidence versus verdict;
- provider identity;
- untrusted model output;
- process isolation;
- migration hazards; and
- enforceable source modularity.

The corrected pass audited the architecture for unseen territory and demanded
owners, lifecycles, trust/security boundaries, and source locations for every
capability zone.

## 4. DeepSeek V4 Pro contributions adopted

DeepSeek V4 Pro materially shaped:

- the product inversion from an agent-centered runtime to governed execution;
- the trust-tier model;
- the explicit domain/application/port/adapter split;
- the first-party module descriptor and lifecycle;
- the detailed repository and test tree;
- route-lock identity for provider/model/transport/tool/parser tuples;
- two distinct analytical transports: native tool-free and tool-bearing
  sandboxed;
- deterministic workflow, effect, permit, and policy-freshness semantics;
- explicit context/instruction/packet and skills/memory boundaries;
- de-commercialization and upstream compatibility treatment;
- full target surface decisions, including removal of desktop;
- the principle that delivery phases are routes through the full map; and
- explicit product exclusions rather than blank deferred territory.

## 5. HY3 corrections adopted

HY3 materially strengthened:

1. **Authority atomicity.** Run state, exact gate bindings, permit/decision
   consumption, journal event, and effect intent must share one strong
   transaction.
2. **Application decomposition.** “Control plane” is a trust layer, not one god
   package. Application services remain beside their owning context.
3. **`ExecutionContext` containment.** The full envelope is forbidden in domain
   method signatures; contexts receive minimal immutable subject views.
4. **Transitional honesty.** Inherited Hermes/Codex/Claude/OpenCode loops have
   only activity/OS mediation until real tool paths are rewired and tested.
5. **Real bypass matrix.** Sequential, parallel, terminal, file, browser, MCP,
   app-server, subagent, background, plugin, process, and network routes need
   real denial tests.
6. **Evidence/verdict separation.** Model `ReviewObservation` and accepted
   `GateOutcome` are distinct schemas and flows; a model-only observation cannot
   create `PASS`.
7. **Split-source reconciliation.** Hermes session state and Kanban are
   projections/private module state; divergence is typed and blocks instead of
   creating another authority.
8. **Packet determinism.** Digests bind resolved source/retrieval revisions;
   stochastic retrieval is a recorded activity.
9. **Provider identity.** Any route-lock field change forces probation.
10. **Knowledge quarantine.** Memory, skills, and learning need a mapped,
    project-scoped quarantine/sanitization/approval boundary.
11. **Missing full-map owners.** Identity/access/secrets, artifacts,
    operations, backup/restore, release/update, upstream sync, migration, and
    external extensions needed explicit contexts.
12. **Anti-recontamination.** De-commercialization and architecture gates must
    run on upstream-sync candidates as well as releases.

## 6. Reconciled decisions

| Question | DeepSeek direction | HY3 challenge | Reconciled architecture |
|---|---|---|---|
| Four core contexts or one? | Four semantic core contexts | Separate persistence can split authority | Keep semantic contexts, but place run/gate/permit/effect mutation in one `governed_execution` authority cell and transaction |
| Application control location | Cross-context process manager | New god-object risk | Per-context application services; one orchestration-only process manager; one narrow PEP/UoW |
| Legacy layout | Compatibility facade | Full fork co-location was not drawn | Transitional inherited root plus sole facade import; target frozen subset under `legacy/hermes` after parity |
| Review authority | Models provide structured reviews | Evidence may collapse into verdict | Separate request, attempt, observation, checker result, gate outcome, human decision, and permit |
| Desktop | Generic delivery module | Must be explicit | No desktop package; local web provides visual UX |
| Phone | Text-phone adapter | Transport/auth unclear | Channel-neutral delivery port, Telegram first adapter, shared decision/auth contract |
| Deferred areas | Attachment points listed selectively | Full-map omissions remain | Every capability receives a final owner and attachment point or explicit exclusion |
| State/event design | Replayable journal and current state | Which one wins on divergence? | Current row is operational; journal is replay oracle; mismatch is corruption and blocks |
| Workflow engine | Local runner first | Home-grown durability is R&D | Runtime port is permanent; local runner must pass the same matrix as any mature alternative |
| Upstream fork | Strangler and compatibility | Upstream may reintroduce removed surfaces | Dedicated governed upstream-sync context and anti-recontamination gate |

## 7. Full-map omissions closed

The corrected architecture adds named boundaries for:

- identity, authentication, remote decisions, data classification, and secrets;
- content-addressed artifacts, access, retention, hold, expiry, and purge;
- operations, health, incidents, reconciliation, and telemetry;
- encrypted backup/restore and external-state reconciliation;
- explicit install, update, release, rollback, and SBOM handling;
- governed upstream fetch/classification/challenge/port/verification;
- schema, module, workflow, and legacy migration coordination;
- quarantined knowledge/skills/memory/learning;
- separate route qualification and whole-system effectiveness evaluation;
- external extension lifecycle and out-of-process protocol;
- tool/MCP/search/browser attachment families;
- full delivery surfaces and shared human-decision contract;
- compliance/provenance and de-commercialization ownership; and
- transitional and target physical repository layouts.

## 8. Limitations

1. The model outputs are advisory and were not runtime acceptance tests.
2. The reviewers read the complete local research corpus but did not perform a
   fresh exhaustive audit of every upstream Hermes source file.
3. The current Ranex repository still contains documentation rather than the
   target runtime.
4. The architecture remains unvalidated until its P0 tests pass.
5. Provider behavior and model identities may change; the recorded routes apply
   to this review date and access path.
6. The raw responses were not retained as canonical content-addressed
   artifacts in this repository. This record preserves the input corpus,
   review roles, limitations, and reconciled material findings, but it is not a
   provider billing or transcript attestation.
7. No credential value was printed or copied into the repository.

## 9. Outcome

The collaboration produced:

- a complete target-system architecture rather than a narrow v1/MVP map;
- a concrete end-state repository and package structure;
- a separate AI-agent development lifecycle;
- a source-of-truth and decision policy; and
- explicit validation gates that must pass before the architecture is called
  runtime-validated.

The correct current status is:

> **Complete target map; conditionally accepted architecture; no runtime proof
> yet.**
