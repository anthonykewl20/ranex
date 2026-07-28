# Kimi Agent-Fleet Research Reconciliation

| Field | Value |
|---|---|
| Review ID | `REVIEW-KIMI-FLEET-001` |
| Version | `1.0.0` |
| Status | Advisory corpus audit and architecture reconciliation |
| Date | 2026-07-27 |
| Owner | Human governor |
| Corpus | Every file in `docs/research/kimi-research/` at the frozen addendum snapshot |
| Corpus count/size | 89 files; 12,058,857 bytes |
| Corpus manifest | [`kimi-research-manifest.sha256`](./artifacts/2026-07-27/kimi-research-manifest.sha256) |
| Manifest SHA-256 | `9f9ef29fa7a7046a3724b9d64e1904f25a925be86a111b6697648debba0607a6` |
| Governing process | [Ranex Core SDLC Operating Model](../CORE_SDLC_OPERATING_MODEL.md) |
| Resulting control spec | [AI-Worker Fleet Control-Plane Specification](../AI_AGENT_FLEET_CONTROL_PLANE.md) |
| Decision authority | Human owner; this review and the Kimi material are not authority |
| Provenance class | `CURATED_RESEARCH`, `NOASSERTION`; source, author, model, provider, tool, and third-party rights remain unproven unless separately recorded |
| Compatibility/migration class | Advisory addendum translated into existing Ranex contexts; no Kimi status, path, or lifecycle becomes canonical |
| Security/data class | Consultation-only `LOCAL_ONLY` artifacts as observed; public inclusion is prohibited pending source, license, and privacy clearance |

## 1. Verdict

The Kimi corpus is useful advisory research about controlling concurrent AI
workers, but it is not a coherent normative base for Ranex by itself.

Its strongest engineering contribution is the distributed-systems framing:
atomic assignment claims, expiring leases, fencing, liveness, dead letters,
deterministic governors, transitive budgets, tool-boundary enforcement,
artifact handoffs, verifier backpressure, and crash recovery. Those controls
fit Ranex after they are assigned to existing bounded contexts and kept
subordinate to the accepted Core SDLC.

Several recommendations conflict with owner requirements and are rejected:

- a measurement/fleet harness as the root system before governance and
  authority exist;
- generic task/status schemas and a `.fleet/` directory as a parallel source
  of truth;
- direct operator approval flowing into a budget/permission gateway;
- “full permissions” workers;
- worker self-merge or reconciler merge authority;
- removal of accountable human review under the current policy; and
- external numeric thresholds treated as universal production gates.

The resulting disposition is:

> **Accept the control mechanisms as translated worker infrastructure; reject
> the parallel process and authority model; keep numerical scaling and learned
> orchestration as locally measured R&D.**

## 2. Exact corpus and audit method

The corpus arrived after the original full-map review freeze. It was therefore
audited as a separate immutable addendum, not silently appended to an older
“all research” claim.

### 2.1 Inventory

| Type | Count | Treatment |
|---|---:|---|
| DOCX | 3 | Archive structure checked; document XML/text, relationships, metadata, notes, and embedded media inspected |
| PNG | 13 | Dimensions/format inspected; diagrams/charts visually or through their authoritative source inspected |
| JSON | 1 | Parsed and citation-registry structure inspected |
| JSONL | 1 | Parsed line-by-line and final citation set inspected |
| Markdown | 45 | Read and classified, including final report, sections, research dimensions, wide searches, validation, plan, and conversion artifacts |
| Mermaid | 6 | Read and compared with the six generated diagram projections/final-report blocks |
| Text | 20 | Read as research prompt/“cheat” lineage inputs |
| **Total** | **89** | Bound by exact SHA-256 manifest |

The audit:

1. created the sorted `<sha256><two spaces><path>` manifest;
2. verified all 89 current files against it;
3. read every textual artifact and extracted DOCX text/metadata;
4. parsed JSON and JSONL;
5. compared Mermaid sources, generated diagrams, report sections, and DOCX
   embedded media;
6. inspected the architecture-relevant visuals;
7. checked internal citation lineage and rendering behavior;
8. spot-checked the most decision-critical primary-source anchors; and
9. compared every recommendation against ADR-0001, Core SDLC, source-of-truth,
   authority ordering, target file ownership, and product exclusions.

Later changes to `docs/research/kimi-research/` are a new subject and require a
new manifest/reconciliation. A live directory glob is not this audit.

## 3. Corpus lineage and limitations

The 89 artifacts are a production lineage around one report, not 89
independent reports.

- The final Markdown, per-section Markdown, reference expansion, DOCX-input
  Markdown, converted Markdown, outlines, research dimensions, broad-search
  notes, and validation files are stages or evidence inputs for the same
  report.
- The three DOCX files are render/conversion variants. They embed the same 13
  PNG payloads byte-for-byte and must not be counted as independent visual
  evidence.
- Six PNG diagrams have corresponding Mermaid sources. Seven other PNGs are
  raster charts without retained generation code or data.
- The large citation registry contains 550 unique URL strings but 523
  canonicalized targets. The final citation JSONL contains 245 URL strings but
  241 canonicalized targets. URL count is not independent-source count.

The corpus does not record:

- generating model, provider, model version/snapshot, route, prompt, prompt
  hash, run/session ID, tool/command log, or output-response hash;
- a source snapshot/content manifest for every cited page;
- named human author/editor/reviewer;
- license, copyright holder, or reuse grant for the report, charts, or
  generated renderings; or
- a reproducible chart/export toolchain and renderer versions.

Accordingly, the corpus is preserved as flawed advisory lineage with
`NOASSERTION`, not relabeled as Ranex-owned or mechanically reproducible
research.

## 4. Evidence-quality findings

### 4.1 Citation and document defects

- The final Markdown has 245 cited identifiers and 245 definitions, but uses
  nonstandard `[^n^]`/`[n]` conventions. Many citations do not render as
  ordinary Markdown footnotes.
- Twenty-one citation-looking tokens occur literally inside code blocks and
  cannot behave as document references.
- The final DOCX has seven shifted/misbound footnotes:
  `181→186`, `182→187`, `183→181`, `184→182`, `185→183`, `186→184`,
  and `187→185`.
- The DOCX files have blank creator/title metadata, no hyperlink relationships,
  and stale internal “83 words/1 page” counters despite roughly 44,726
  extracted report words.
- Raster charts contain stale citation identifiers. Examples include MAST
  `113/114` where the final registry uses `1/142`, three-forces `14/187/534`
  where the final registry uses `7/5/21` and `534` is outside the final
  1–245 range, and model-mix `92` where the final registry uses `31`.
- The six Mermaid sources match their corresponding final-report diagram
  blocks, but the renderer/version is absent. One diagram is unusually tall
  for normal pages; several wide diagrams are likely unreadable when scaled to
  document width. Alternative text is not systematically retained.

These are provenance/export defects. The source files remain unchanged so the
review does not rewrite historical evidence.

### 4.2 Claim and version defects

Decision-critical primary-source spot checks broadly support the need for
strong fleet controls, but not every headline universal or exact number.

- The report overstates the Data Processing Inequality as a general guarantee.
  The cited argument is conditional on budget/context assumptions that the
  report restores only later.
- The MAST discussion mixes sample/version statistics. The final version's
  per-mode category totals and first-210-trace figure do not support binding
  the older `41.8/36.9/21.3` percentages to all 1,642 traces as written.
- The report mixes April preprint statistics with the 24 July 2026 version of
  record for the multi-agent scaling study. The later paper treats roughly 45%
  as a practical selection rule rather than a universal law and reports weak
  leave-one-domain-out generalization. “Veto the whole build” and
  HIGH-confidence universality are therefore not accepted Ranex claims.

The architecture uses the direction—measure locally and default to the
smallest effective topology—without importing the disputed constants.

### 4.3 Experiment-design defects

The report's E0/E2/E4/E10 gates are useful experiment prompts, not
decision-grade Ranex acceptance contracts:

- E0's noise floor from `30×3` trials and a five-percentage-point cutoff is not
  justified as a universal margin.
- E2 proposes `FAR < 10%` using `n=30`; even zero observed false accepts leaves
  a 95% upper bound above ten percent.
- E4 proposes a Wilson interval excluding zero for a paired difference; paired
  data require a paired-difference/Newcombe or exact McNemar method plus a
  predeclared decision margin.
- E10's four-week production parity lacks minimum traffic, an equivalence/
  non-inferiority margin, power, and explicit failure treatment.

Ranex therefore predeclares the population, controls, pairing, uncertainty
method, decision margin, sample-size basis, failure treatment, and stop rule for
each `FleetExperiment`. All Kimi thresholds remain `R_AND_D`.

## 5. Claim-level architecture disposition

| Kimi claim/recommendation | Disposition | Ranex translation or reason |
|---|---|---|
| Fleet control is a distributed-systems problem, not a prompt convention | **ACCEPT** | Use durable typed state, concurrency control, fencing, outboxes, recovery, and tool-boundary enforcement |
| Verification capacity bounds useful worker scaling | **ACCEPT WITH LIMITS** | Verifier/human capacity creates backpressure; no imported universal agent count or threshold |
| Parallelize reads and isolate/serialize writes | **ACCEPT** | `STAR_READ` and `PARTITIONED_WRITE`; isolated worktrees; one writer per shared file; serialized landing |
| Artifact handoff is safer than transcript relay | **ACCEPT** | Content-addressed packets/results/evidence/handoffs; summaries are navigation only |
| Atomic claim plus TTL/heartbeat/watchdog | **ADAPT** | `agent_collaboration` CAS claim, coordinator-time lease, grace/recheck, monotonically increasing fencing epoch, typed reclaim |
| Restart and replay the last message | **REJECT AS GENERIC RULE** | Only workflow-node-specific replay is permitted; never blindly replay a prompt, tool call, or external effect |
| Execution governor and loop detector | **ACCEPT** | `governed_execution` owns deterministic deadlines, ceilings, result-aware loops, cancellation, and termination cause |
| Transitive spend metering | **ACCEPT** | `resource_governance` reservation tree charges every descendant to all ancestors |
| Hook layer enforces permission | **ADAPT** | Hooks are policy-enforcement adapters; current lease/subject/workspace/capability/route/sandbox/budget all validate |
| Operator approval enters gateway directly | **REJECT** | Authentication → policy decision → exact-subject grant → permit → `CapabilityBus` remains mandatory |
| Generic task registry is source of truth | **REJECT** | `work_management`, `agent_collaboration`, and `governed_execution` own distinct typed aggregates |
| Generic `deferred` task/status value | **REJECT** | Scheduling metadata cannot become architecture status or collide with typed lifecycle state |
| `.fleet/` handoff/decision/task layout | **REJECT AS CANONICAL** | Map concepts to context APIs, content-addressed artifacts, configuration management, workspaces, and contract registries |
| Planner is sole design owner | **REJECT AS AUTHORITY** | Planner produces decomposition proposal; architecture/product/human decision rights remain unchanged |
| Worker uses disposable devbox with “full permissions” | **REJECT** | Ephemeral least privilege, exact capabilities, no operator home/authority DB/standing secret, sandbox and egress controls |
| Self-merge up to a worker threshold | **REJECT** | No worker self-merges at any count; human-controlled landing remains policy |
| Reconciler queue owns merge above a threshold | **REJECT AS AUTHORITY** | Reconciler may propose conflict patch; semantic selection/review/landing use normal authority |
| Remove human review behind strong holdouts | **REJECT UNDER CURRENT ADR** | Holdouts strengthen evidence but do not silently transfer accountable merge/release/closure rights |
| Measurement harness is the first build artifact | **RESEQUENCE** | First fleet-scaling instrument after Core-SDLC contract, identity, authority, evidence, and isolation foundations |
| Fixed 3→10→30 worker roadmap | **R_AND_D** | Topology/size derives from local paired evidence, verifier capacity, shared-state risk, and human burden |
| Model-mix routing is the largest savings lever | **R_AND_D** | Static qualified routes first; exact local cost/outcome/drift evidence required |
| Learned topology/router/conductor | **DEFER AS MAPPED R&D** | Offline hidden evaluation, tamper resistance, drift/rollback, non-self-activation, and human ADR required |

## 6. Visual-specific reconciliation

Three manifest-bound Mermaid sources make the conflicts especially concrete.
The paths below identify local evidence; they are not public links and the
files must not be distributed pending rights clearance:

1. `docs/research/kimi-research/mermaid_png/diagram_1.mmd`
   sends operator approval directly to the budget/permission gateway. Ranex
   retains authentication → `HumanDecisionRecord` → eligible decision snapshot
   → one-shot `ConsumableAuthorityGrant` → `Permit` → effect intent/dispatch.
2. `docs/research/kimi-research/mermaid_png/diagram_5.mmd`
   labels a worker “full permissions, no prompts” and permits “self-merge
   ≤10 writers / reconciler queue >10.” Both are rejected. Prompt presence is
   irrelevant to least privilege, and no worker/reconciler receives landing
   authority.
3. `docs/research/kimi-research/mermaid_png/diagram_6.mmd`
   places the measurement harness in weeks 1–2 before the control plane. Ranex
   treats this as an experiment itinerary, not the full architecture, and
   resequences the harness after constitutional and authority foundations.

The other diagrams are conceptual research illustrations. They are not Ranex
state, transaction, or file-ownership diagrams.

## 7. Resulting Ranex ownership and file map

| Control | Owner | Target home |
|---|---|---|
| Assignment/offer/claim/attempt | `agent_collaboration` | `domain/{assignments,dispatch_offers,worker_attempts}.py`; claim service |
| Lease/heartbeat/reclaim/fencing | `agent_collaboration` | `domain/{leases,heartbeats}.py`; liveness service; harness fencing guard |
| Mailbox/dead letters/handoff | `agent_collaboration` | `domain/mailboxes.py`; mailbox/handoff services |
| Run governor/termination/loop window | `governed_execution` | `domain/{governor,termination,progress_window}.py` |
| Parent/child reservations and usage | `resource_governance` | `domain/{reservation_tree,usage_settlement}.py`; budget gateway |
| Tool-boundary enforcement | Policy PEP plus adapters | `adapters/harnesses/common/{permission_hook,fencing_guard}.py` |
| Worktrees/path ownership/landing plan | `workspace` | workspace application APIs and Git/filesystem/sandbox ports |
| Verifier evidence and capacity | `assurance`, `qualification`, `process_assurance` | checker/evidence APIs, qualification fixtures, fleet calibration records |
| Fleet experiment | `process_assurance` | measurement runner/reader plus `tests/evaluation/fleet_control/` |

The complete aggregate/state/API/test map is normative in the
[AI-Worker Fleet Control-Plane Specification](../AI_AGENT_FLEET_CONTROL_PLANE.md).

## 8. Required provenance repair before stronger reuse claims

Preserve the frozen corpus, then create a corrected derivative only through a
new research work item that:

1. records author/editor, model/provider/version, prompts, runs, tools, and
   source manifests;
2. records copyright/license/holder and allowed reuse for report and visuals;
3. assigns stable canonical source IDs and keeps URL aliases separate;
4. maps each consequential claim to exact source/version/page/section and
   distinguishes quotation, paraphrase, inference, and synthesis;
5. separates preprint, version-of-record, vendor report, benchmark, and local
   hypothesis;
6. fixes footnote binding, Markdown syntax, literal code-block markers,
   hyperlink relationships, metadata, page fit, and alternative text;
7. retains chart data/code, environment, fonts, and renderer versions;
8. adds export CI for missing/misbound citations, unresolved markers, clipped
   diagrams, and unreadable scale; and
9. reruns experiment-design review before adopting any numeric gate.

Until that work exists, Ranex cites this reconciliation and the frozen manifest
for architectural input. It does not cite the DOCX variants as verified or
independent research deliverables.

## 9. Architecture impact

The Kimi audit caused these material additions:

- the complete
  [AI-Worker Fleet Control-Plane Specification](../AI_AGENT_FLEET_CONTROL_PLANE.md);
- `SDLC-AIW-001` through `SDLC-AIW-007` and
  `SDLC-ADOPT-FLEET-A` through F;
- explicit `AssignmentStatus`, `LeaseStatus`, and
  `MailboxDeliveryStatus` namespaces;
- assignment, lease, mailbox, and fleet-experiment artifact contracts;
- atomic claim, coordinator-time liveness, stale-worker fencing, transitive
  budgets, result-aware loop detection, verifier backpressure, and typed crash
  recovery;
- process-assurance measurement adapters and security/resilience/evaluation
  test homes;
- a one-worker default and locally measured topology policy; and
- explicit rejection of self-merge, unbounded workers, direct gateway approval,
  generic `.fleet/` authority, and pre-governance fleet sequencing.

The audit did **not** change:

- Core SDLC as the governing human software-development process;
- AI agents as bounded workers;
- human-controlled architecture, risk, landing, release, and closure rights;
- exact evidence → gate → decision → grant → permit → effect ordering;
- Hermes-derived fork/strangler strategy;
- the one-host modular-monolith target; or
- desktop/Electron exclusion.

## 10. Remaining unknowns

- Exact lease durations, heartbeat cadence, concurrency limits, task
  populations, model mix, and verification margins need Ranex runtime evidence.
- Kimi generation provenance and reuse rights are unknown.
- Many third-party claims need exact version/page snapshots before they can
  support a high-risk decision.
- Learned orchestration remains inactive R&D.
- The new fleet controls remain target documentation until schemas, code,
  harness enforcement, and adoption-gate evidence exist.

No model consensus resolves these unknowns. The human owner may choose a
direction, but empirical claims remain `UNKNOWN` until the named evidence
exists.
