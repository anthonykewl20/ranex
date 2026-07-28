# DeepSeek V4 Pro and HY3 Full-Map Architecture Reconciliation

| Field | Value |
|---|---|
| Review ID | `REVIEW-ARCH-RANEX-001` |
| Version | `1.3.0` |
| Date | 2026-07-27 |
| Status | Advisory architecture evidence; final exact-subject round recorded |
| Ranex HEAD at source capture | `fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4` |
| Historical OpenCode version | `1.18.7` |
| Historical execution mode | `plan`, read-only, `--pure` |
| Primary collaborator | `deepseek/deepseek-v4-pro`, variant `high` |
| Independent challenger | `openrouter/tencent/hy3`, variant `high` |
| Independence standing | Historical passes were procedurally separate but not mechanically attested; advisory only |
| Final-round independence | Concurrent provider-separated requests, identical user payload, neither response shared with the other request, retained provider metadata |
| Repository mutations by reviewers | None |
| Decision authority | Human owner |

## 1. Purpose

The owner requested architecture and file-structure collaboration with HY3 and,
especially, DeepSeek V4 Pro. Two parallel review passes were performed:

1. a ground-zero architecture and file-structure pass; and
2. a corrected full-map completeness pass after the owner rejected MVP/v1-only
   documentation.

DeepSeek V4 Pro acted as the primary specialist. HY3 received the same
historical research corpus independently and challenged boundaries, authority,
completeness, and testing. A later direct-API, exact-route round retained raw
responses and provider metadata. The architecture was then synthesized against
local research and repository evidence by the human-governed documentation
process; neither model became a decision authority.

## 2. Frozen evidence corpus

The historical initial corpus consisted of the following five files—the
research files present and selected at that capture. Later research and visual
artifacts are not retroactively claimed as inputs to these first two passes.

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

The OCAsk digest in this table is the historical pre-format-normalization
subject. The reduced direct-review manifest later bound the same path at
`1856b91765bcb7b95533738ff37ba13c7b04d8af447a16a728c9b1e96a0fad43`.
They are different revisions, not two names for one byte sequence. The later
manifest is retained at
[`source-manifest.sha256`](./artifacts/2026-07-27/source-manifest.sha256).

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
2. The historical reviewers read the five-file corpus named in section 2.
   Later visual, SDLC, Kimi, book, and other research is not retroactively
   claimed as an input to those passes. No review performed a fresh exhaustive
   audit of every upstream Hermes source file.
3. The current Ranex repository still contains documentation rather than the
   target runtime.
4. The architecture remains unvalidated until its P0 tests pass.
5. Provider behavior and model identities may change; the recorded routes apply
   to this review date and access path.
6. Raw outputs from the first historical OpenCode passes were not retained as
   canonical artifacts. Raw response bytes and provider metadata from the
   later direct-API review were retained, but provider metadata remains
   provider-supplied evidence rather than an independently witnessed billing or
   identity attestation.
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

## 10. Retained direct-API pre-reconciliation review

A later review used the exact requested routes directly and retained the
provider responses byte-for-byte. It reviewed the reduced bundle frozen in
[`source-manifest.sha256`](./artifacts/2026-07-27/source-manifest.sha256) with
[`final-full-map-review-prompt.md`](./artifacts/2026-07-27/final-full-map-review-prompt.md).
That bundle included the then-current normative architecture documents and nine
top-level research/visual artifacts. It did not include the subsequently
arriving Kimi corpus, book corpus, new fleet specification, or the complete
template set, so it is a pre-reconciliation review rather than the final exact
subject.

| Reviewer call | Actual route/model | Response ID | UTC interval | Response SHA-256 |
|---|---|---|---|---|
| DeepSeek part 1 | `deepseek` / `deepseek-v4-pro` | `3336015f-da40-4011-ba4a-6dba62e47f9c` | `13:13:26.873Z`–`13:15:16.562Z` | `2349bbe616ee574b6b90b3451addcaf59c11fa252526c4a0ea77af067b12f150` |
| DeepSeek continuation | `deepseek` / `deepseek-v4-pro` | `151058f3-ab09-48bf-9789-7e1e2474edfb` | `13:23:29.407Z`–`13:24:09.494Z` | `7e8479853baa5d8ae3e921a31e04516f262427d88ca16c2acb76f28f5268ba0f` |
| HY3 independent challenge | `openrouter` / `tencent/hy3` | `gen-1785158547-NJy3i1xLtrxTsafCulgG` | `13:22:27.018Z`–`13:24:22.906Z` | `1029d1b98ecf3e1b7c9fa654814f4716dcdf0d3c174d5e520b728db093583481` |

DeepSeek part 1 ended mid-section because the response reached its output
limit. The continuation was a second authenticated request bound to the first
response digest; it is not represented as one atomic provider response. The
first DeepSeek request used bundle digest
`8ffa853f1e8499387fd154dc4bfc4cf51e3e24e5f862b6857b254646363ac066`.
The reconstructed continuation and independent HY3 requests used bundle digest
`3d0ec7bbb66ac23c1aa882611017d15ab7893c767266bb03ae6083f52e192b98`.
The frozen prompt digest was
`e20b481c027105c2b16f66299664a854d4db2aabba6f64851b4358f1cad2eab4`.

Retained evidence:

- [DeepSeek V4 Pro part 1](./artifacts/2026-07-27/deepseek-v4-pro-final-review-part-1.md)
  and [metadata](./artifacts/2026-07-27/deepseek-v4-pro-final-review-part-1.metadata.json);
- [DeepSeek V4 Pro continuation](./artifacts/2026-07-27/deepseek-v4-pro-final-review-part-2.md)
  and [metadata](./artifacts/2026-07-27/deepseek-v4-pro-final-review-part-2.metadata.json); and
- [HY3 independent challenge](./artifacts/2026-07-27/hy3-final-review.md)
  and [metadata](./artifacts/2026-07-27/hy3-final-review.metadata.json).

DeepSeek found the map acceptable for formal contracting with no P0 finding.
HY3 returned `CHANGES_REQUIRED`, principally because the repository still
lacked fork-lineage proof and executable contracts. That is a valid
implementation blocker, but not permission to collapse the documented map.

## 11. Direct-review finding reconciliation

| Finding | Disposition and exact correction |
|---|---|
| Signed-maintenance key ownership was ambiguous | Accepted. `release_management` owns signing policy, allowed key IDs, manifests, and signed records; `identity_access` and its secret backend custody raw private material; bootstrap pins public trust roots; the human release authority owns ceremony, rotation, and revocation. No application service stores raw keys. |
| Architecture review did not bind the exact architecture subject | Accepted. `ArchitectureSubjectV1`, exact architecture-document and manifest digests, `CoreSDLCTrace`, and corresponding architecture packet/proposal/reconciliation fields were added to the artifact contract and templates. |
| Fork preflight was prose-only | Accepted. `SDLC-FORK-000` is registered in the control catalog with required evidence and is blocking before any runtime implementation commit enters the product branch. The actual GitHub network-fork fact may remain `false`; it is not fabricated to imply Git ancestry. |
| Sixteen work-item states were not listed clearly enough | Accepted. The Core SDLC lists the normal thirteen-state path plus `BLOCKED`, `CANCELLED`, and `ROLLED_BACK`; the semantic HTML contains sixteen state cards. |
| Raw direct-review outputs were absent | Accepted for the later round. Exact response bytes, digests, request/route metadata, timestamps, and usage are retained above. Historical output absence remains disclosed. |
| Visual-review hashes were stale | Accepted. The visual review retains historical hashes as history and adds a current exact-subject supersession section. |
| Real-harness bypass tests lacked a file home | Accepted. The target tree includes `tests/security/bypass_matrix/` and per-harness, helper, subprocess, filesystem, process, network, plugin, MCP, subagent, background, and alternate-tool denial coverage. |
| `process_assurance` lacked an explicit adapter | Accepted. The target tree and responsibility catalog include the `process_assurance` adapter package and measurement/conformance ports. |
| Templates and machine schemas are not runtime-implemented | Confirmed, not hidden. Templates are provisional examples until `AI-G2`; future `architecture/contracts/` schemas and registries must pass contract generation and validation before the first governed runtime tracer. |
| Fork ancestry remains unproven | Confirmed, not waived. The map is conditionally accepted while `SDLC-FORK-000 = PENDING`; runtime implementation is blocked. |

The Kimi addendum arrived after this round and was separately audited in
[Kimi Agent-Fleet Research Reconciliation](./2026-07-27-kimi-agent-fleet-research-reconciliation.md).
That round therefore cannot inherit a later exact-subject verdict
automatically.

## 12. First post-reconciliation direct round

The first all-research reconciliation attempt used:

| Evidence | Count / bytes | SHA-256 |
|---|---:|---|
| `post-reconciliation-source-manifest.sha256` | 178 files / 61,458,128 bytes | `619fe0bee1fd68e67211de87b7d12741d97cfb82f91cca0f70ec1663c9df6528` |
| `post-reconciliation-review-bundle-manifest.sha256` | 54 files / 558,221 bytes | `36777e3cd55ee1356b6af698d43811ee27f646276e4046932618f74b9138e75e` |
| `post-reconciliation-full-map-review-prompt.md` | 8,072 bytes | `040461e190492328daa1fea81bc93d3e0ba9cdf492607954f142804124ae0503` |
| Identical user payload | 573,748 bytes | `0a67ed37b90eb702421d68e3baad45d8862560a8fbf6f6bd76724fb395db4210` |

The two requests were independent and neither included the other response:

| Reviewer | Actual route/model | Response ID | UTC interval | Finish | Response SHA-256 | Tokens |
|---|---|---|---|---|---|---:|
| DeepSeek V4 Pro | `deepseek` / `deepseek-v4-pro` | `7d7ea097-7d93-4dfe-8675-688f3a5818f2` | `14:56:46.410Z`–`14:58:46.289Z` | `stop` | `8be87ba82feb6af75b61e9400444c48693d396004ecaeac51c077c8cf43c67c5` | 149,075 |
| HY3 | `openrouter` / `tencent/hy3` | `gen-1785164206-nwPvdzwHCuzbKAUUe7sN` | `14:56:46.437Z`–`14:59:31.390Z` | `stop` | `092402523e3ee1ada88b50ae10af2d563350f7fb4948c734cfcf777e78e85775` | 146,445 |

Both responses said `ACCEPTABLE_FOR_FORMAL_CONTRACTING` and reported no P0.
Their useful nonblocking corrections were applied:

- the full-system `schemas/` tree is now explicitly the superset of the exact
  AI-artifact schema subset;
- the 36 YAML examples are explicitly mapped to 36 artifact/value-object
  producer rows, with ADR/RFC forms kept separate; and
- the `process_assurance` adapter-to-port relationship is explicit.

The following findings were confirmed without being disguised as document
completion:

- `SDLC-FORK-000`, executable registries/schemas/codegen, runtime validation,
  and release leakage checks remain implementation blockers;
- the implementation guide already has a fail-closed lower-precedence
  relationship in `SOURCE_OF_TRUTH.md` §3.1; and
- provenance/denylist paths shown in the target tree remain target
  implementation files, not fabricated current files.

DeepSeek's raw response contains one internally inconsistent sentence claiming
the review-bundle manifest included book files. It did not. The
**source** manifest inventoried the twelve local-only book artifacts; the
54-file attachment bundle excluded their contents. That sentence is rejected,
while the response is retained byte-for-byte.

A concurrent scoring-review update later changed
`docs/research/ranex-sdlc-visual-hy3-review-2026-07-27.md`. The live tree
therefore no longer verifies all 178 entries in that source manifest. The
54/54 attachment set remains exact and is preserved with its manifest in
`post-reconciliation-review-bundle.tar.gz`:

- 55 archive members: 54 listed files plus the non-self-listed manifest;
- 171,566 bytes; and
- SHA-256
  `f7246ad0c9e90ba2b5560021a01199d470d628d52b6705b500140d82bf3032ae`.

This race is why the round is retained as historical advisory evidence and not
represented as the current final exact subject.

Retained evidence:

- [DeepSeek V4 Pro response](./artifacts/2026-07-27/deepseek-v4-pro-post-reconciliation-review.md)
  and [metadata](./artifacts/2026-07-27/deepseek-v4-pro-post-reconciliation-review.metadata.json);
- [HY3 response](./artifacts/2026-07-27/hy3-post-reconciliation-review.md)
  and [metadata](./artifacts/2026-07-27/hy3-post-reconciliation-review.metadata.json);
- [source manifest](./artifacts/2026-07-27/post-reconciliation-source-manifest.sha256);
- [attachment manifest](./artifacts/2026-07-27/post-reconciliation-review-bundle-manifest.sha256);
  and
- [frozen attachment archive](./artifacts/2026-07-27/post-reconciliation-review-bundle.tar.gz).

## 13. Final exact-subject direct round

After the accepted clarity corrections, a new non-circular subject was frozen.
The final model responses and this reconciliation record are deliberately not
inputs to their own review. Every normative architecture, lifecycle, contract,
template, current research reconciliation, visual/research artifact, and
rights-control source remains in the source inventory.

| Evidence | Count / bytes | SHA-256 |
|---|---:|---|
| `final-exact-subject-source-manifest.sha256` | 168 files / 61,406,149 bytes | `c96e9bce674d393422f7d1158dd22f1f39adfd69dd3e74b6eb85c5fa4cf79ef0` |
| `final-exact-subject-review-bundle-manifest.sha256` | 54 files / 549,951 bytes | `46073c9b90b9a1527b373b2de42851d9b8c6405ac65b4262faacf6c3fc78cf44` |
| `final-exact-subject-review-prompt.md` | frozen instruction file | `067ef657847ed8eabc32b1ca6df4cf9aa5544d918e0d9c0970acb946cbdfbfa9` |
| Identical user payload | 565,440 bytes | `f50236da45aa8ab4b2c487f2a37cad275ebe4021c9310a7dd472204beaad4606` |

Both manifests verified in full immediately before submission and remained
unchanged through both calls:

| Reviewer | Actual route/model | Response ID | UTC interval | Finish | Response SHA-256 | Tokens | Verdict |
|---|---|---|---|---|---|---:|---|
| DeepSeek V4 Pro | `deepseek` / `deepseek-v4-pro` | `a1f15625-2e7a-4862-8b45-dcbc3b9a7a3e` | `15:13:40.494Z`–`15:16:53.669Z` | `stop` | `cb9a5abdfd72ade69576faf5c01ccf291d41101d6690e953dc305107f2e4f5a4` | 151,036 | `ACCEPTABLE_FOR_FORMAL_CONTRACTING`; no P0 |
| HY3 | `openrouter` / `tencent/hy3` | `gen-1785165220-p1R8LlPGA80rcCqO8asH` | `15:13:40.518Z`–`15:17:12.820Z` | `stop` | `62c107925de9020d2f63037bcd35a87b42f68ae06e36cdaeee34f3f74c591b85` | 145,241 | `CHANGES_REQUIRED`; no P0 |

### 13.1 Final finding dispositions

| Finding | Disposition |
|---|---|
| `SDLC-FORK-000` has not passed | Confirmed and not waived. It blocks runtime implementation commits; it is not an omitted architecture region. |
| Executable registries, schemas, codegen, CI validation, and fleet adoption gates are not implemented | Confirmed and not relabeled. These are `AI-G2`/runtime prerequisites before the first governed tracer, not evidence that the full target map is absent. |
| A release/index/package scan must mechanically reject every `LOCAL_ONLY` path | Confirmed. The legal manifest already makes every such path a fail-closed release blocker; implementation and runtime proof remain required. |
| Capability templates use `null` where executable records omit an inapplicable level | No contradiction. `AI_ARTIFACT_CONTRACTS.md` §7.1 explicitly defines `null` in provisional draft templates as “not established,” while the Core SDLC requires omission in the executable record. The future conditional schema must enforce that distinction at `AI-G2`. |
| `RANEX_IMPLEMENTATION_GUIDE.md` was not attached | Correct observation, wrong scope conclusion. It is in the 168-file source inventory, and the prompt forbids claiming direct inspection of unattached text. `SOURCE_OF_TRUTH.md` §3.1 already blocks conflicts; a guide reconciliation remains required before it is a construction input. |
| This reconciliation record was outside the review subject | Intentional non-circularity, disclosed in the prompt. Review outputs and the record citing them cannot be inputs to their own review. |
| `process_assurance` measurement adapters lack a port/schema home | Already satisfied. Architecture §12.1 names `process_evidence`, `training_registry`, and `measurement_runner` ports and explains the adapter split. Internal application ports are not AI-work artifact schemas. |
| ADR/RFC examples might be mistaken for runtime schemas or accepted-document homes | Already satisfied. The lifecycle calls them governance-document forms, and the target tree provides the accepted ADR/RFC homes. |
| `CoreSDLCTrace` might be duplicated | Already satisfied. The lifecycle and artifact contract identify one shared embedded trace schema, not a second artifact authority. |
| Compatibility state ownership is ambiguous | Already satisfied. Architecture §12.1 calls it an exceptional boundary package, says it owns no canonical state, and limits it to typed results/proposals. |
| Local UoW/outbox homes are missing from compact rows | Already satisfied immediately below the §12.1 table: every stateful context has narrow local `unit_of_work.py` and `integration_event_outbox.py` ports even when omitted from the compact row. |
| Foundation size budget should receive an arbitrary number now | Deferred to measured architecture fitness work. An invented line ceiling would violate the evidence/calibration rule; the strict consumer and responsibility budget remains mandatory. |

The raw outputs are retained without silently editing model mistakes:

- [DeepSeek V4 Pro final response](./artifacts/2026-07-27/deepseek-v4-pro-final-exact-subject-review.md)
  and [metadata](./artifacts/2026-07-27/deepseek-v4-pro-final-exact-subject-review.metadata.json);
- [HY3 final response](./artifacts/2026-07-27/hy3-final-exact-subject-review.md)
  and [metadata](./artifacts/2026-07-27/hy3-final-exact-subject-review.metadata.json);
- [final source manifest](./artifacts/2026-07-27/final-exact-subject-source-manifest.sha256);
- [final attachment manifest](./artifacts/2026-07-27/final-exact-subject-review-bundle-manifest.sha256);
  and
- [final review prompt](./artifacts/2026-07-27/final-exact-subject-review-prompt.md).

### 13.2 Final status

The evidence supports:

> **Complete full-system target map; independently reviewed exact subject; no
> P0 architecture finding; no runtime proof.**

It does **not** support:

- a claim that fork ancestry is established;
- a claim that executable contracts, release leakage gates, codegen, or the
  target runtime exist;
- a claim that HY3 returned unconditional acceptance; or
- a model-issued architecture decision.

DeepSeek considers the target suitable for formal contracting. HY3 requires
the already registered fail-closed implementation prerequisites before the
first governed tracer. The human owner remains the architecture decision
authority.

## 14. Post-review owner disposition — 2026-07-28

After the frozen review, the human owner deleted the former root implementation
guide and accepted
[ADR-0002](../decisions/ADR-0002-retire-legacy-implementation-guide.md).
The guide-reconciliation prerequisite in section 13.1 is therefore closed by
retirement, not by accepting or regenerating that guide.

Historical research, raw model responses, and source manifests continue to
name and hash the file because it was part of their earlier exact subjects.
They are not rewritten, and their references do not restore present
construction authority. New review subjects and manifests exclude the deleted
file and include `ADR-0002` plus the engineering-practice-profile changes.
