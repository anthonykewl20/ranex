# Independent Architecture & Product-Fit Review
**Subject:** Selective adaptation of proven patterns from `github/spec-kit` @ `f36634b5c1463d3592382e863cd5e7b8a94d9c9a`
**Method:** Read-only. Sources = attached Ranex architecture/policy docs + attached Spec Kit tree. No other reviewer's verdict consulted. GitHub stars/popularity treated as adoption signal only, never as fitness proof.

---

## 1. Verdict on selective adoption

**Conditionally adopt the *workflow shape and artifact vocabulary*; reject the *enforcement mechanism*.**

Spec Kit is a well-built *prompt-and-template* scaffolding toolkit for spec-driven development. Its value is in shaping agent discipline (clarify → plan → tasks → implement → converge) and in treating requirements quality as a first-class concern (the "unit tests for English" checklist idea). Those shapes are genuinely useful and map cleanly onto Ranex's Core-SDLC stages and AI-agent lifecycle.

However, Spec Kit's *governance mechanism* is precisely the thing Ranex was built to forbid:

- Rules live in markdown the agent **reads** (`constitution.md`), which Ranex's README calls "suggestions, not constraints" (README.md:35–39).
- Workers **mark their own work done** (`implement` steps 8, 9, 166; `converge` append-and-complete), which violates CORE_SDLC §2 invariant 10 and AI_LIFECYCLE §9.2 ("the human lands the change").
- `workflows.md:481` states plainly there is **"no capability sandbox"** and **"no `requires.permissions` capability gate"** — the opposite of FLEET §11.2 and §15.1.
- Community `extensions`/`presets`/`bundles`/`catalogs` let unvetted third parties add commands and mutate templates, conflicting with SOURCE_OF_TRUTH §9 (RFC/ADR required for process/architecture change) and the LICENSE-RANEX personal-use constraint.

The defensible path is **Ranex-native re-implementation of the useful shapes** (specify→clarify→plan→tasks→analyze→converge) that *emits Ranex artifact schemas with exact-subject digests and gated landing*, rather than installing Spec Kit files. Favor semantics over names.

---

## 2. ADOPT / MODIFY / REJECT / DEFER matrix

Citations use `ranex:<file>` and `spec:<file>` from the attached trees.

| Surface | Decision | Evidence | Ranex fit | User value | Differentiation / moat | Effort | Governance / security risk |
|---|---|---|---|---|---|---|---|
| `specify` (NL → spec.md) | **MODIFY** | spec:templates/commands/specify.md:115 reads `/memory/constitution.md`; ranex:README.md:35–39 | Good *shape* (intake + requirements + acceptance scenarios). Must project to `WorkIntake` + requirement artifacts with subject binding (AI_ARTIFACT_CONTRACTS §4) | Faster, structured intake for owners | Ranex keeps authority in `work_management`, not prose | Low | Low if output is an artifact, not markdown the agent trusts |
| `clarify` (≤5 Q&A) | **MODIFY** | spec:templates/commands/clarify.md:129–179; ranex:AI_LIFECYCLE §5.1 (L1 research) | Fits L0/L1 refinement; needs recorded claims as FACT/INFERENCE/UNKNOWN (AI_LIFECYCLE §5.1) | Reduces ambiguous scope | Ranex traces assumptions as first-class | Low | Medium: answers must bind to subject, not silently edit spec |
| `plan` (research/data-model/contracts/quickstart + constitution gate) | **MODIFY** | spec:templates/commands/plan.md:66–72; ranex:CORE_SDLC §7.2 design record | Decomposition maps to DESIGN/PLAN; "constitution check" gate must become deterministic AI-G2 (SOURCE_OF_TRUTH §7) | Reusable planning discipline | Ranex gates are fail-closed, not prompt gates | Med | Med: markdown plan must not override machine contract (AI_LIFECYCLE §7.2) |
| `tasks` (task list, `[P]` parallel) | **MODIFY** | spec:templates/commands/tasks.md:143–213; ranex:FLEET §8.2 topologies | `TaskPacket` + `WorkerAssignment` with task-minimal grant (FLEET §6.1) | Clear work breakdown, parallel hints | Ranex enforces parallel safety (atomic claim, fencing) | Med | Low if projected to packet; high if used as raw markdown authority |
| `checklist` ("unit tests for English") | **ADOPT** (concept) | spec:templates/commands/checklist.md:9–28,159–247; ranex:CORE_SDLC §10 verification strategy | Strong fit: requirements-quality checks = evidence culture. Must emit machine-registered check items w/ subject digest | Catches vague requirements pre-build | Ranex adds non-compensating scoring honesty | Low | Low; keep advisory, never a gate by itself |
| `analyze` (read-only cross-artifact) | **ADOPT** (concept) | spec:templates/commands/analyze.md:52–61; ranex:AI_LIFECYCLE §5.7 review | Maps to independent review / post-landing verification; read-only is safe | Finds inconsistencies early | Ranex requires independent identity (§3) | Low | Low; advisory only, no authority |
| `implement` (execute + self-mark `[X]`) | **REJECT** mechanism / **MODIFY** shape | spec:templates/commands/implement.md:146–166; ranex:CORE_SDLC §2.10, AI_LIFECYCLE §9.2 | Self-approval is forbidden. Keep phase execution, replace self-mark with `RunResult`+gate+human landing | — | Moat = no maker self-approval | — | **High**: self-approval violates core invariant |
| `converge` (assess code, append tasks) | **MODIFY** | spec:templates/commands/converge.md:57–83; ranex:AI_ARTIFACT_CONTRACTS §5 (immutable trace) | Append-only rework detection fits; but must not mutate spec/plan and must bind findings to subject | Surfaces unfinished work | Append-only matches Ranex immutable records | Med | Med: LLM self-assessment of "done" is not evidence (SOURCE_OF_TRUTH §2.2) |
| `taskstoissues` (GitHub MCP) | **REJECT** / **DEFER** | spec:templates/commands/taskstoissues.md:58–73; ranex:SOURCE_OF_TRUTH §2.1 (`work_management` owns `WorkItemStatus`) | External issues as source of truth conflicts with "agent queues are projections" | Convenience for GitHub users | Ranex keeps work item as canonical | — | Med: CAUTION about remote URL shows no sandbox; provenance not Ranex-bound |
| Artifact evolution (living/flow-back spec) | **REJECT** (living) / **DEFER** (flow-forward) | spec:docs/guides/evolving-specs.md:35–80; ranex:AI_ARTIFACT_CONTRACTS §4–§5 | "living spec" mutating `spec.md` breaks exact-subject immutability + CoreSDLCTrace | — | Moat = immutable subject binding | — | **High**: edits spec = breaks digest chain |
| `integrations` (30+ agents) | **REJECT** | spec:docs/reference/integrations.md:7–45 (incl. `hermes`, `opencode`); ranex:FLEET (ADR-0011 catalog = Claude SDK / Codex only) | Breadth violates "only cataloged providers" (FLEET §6.1, ADR-0011) | — | Ranex's fixed adapter catalog is the authority | — | **High**: arbitrary runtime = route drift (FLEET §20) |
| `extensions` (community commands) | **REJECT** | spec:docs/reference/extensions.md:233–261; ranex:SOURCE_OF_TRUTH §9, FLEET §15.1 | Unvetted command addition = worker capability expansion = forbidden | — | Moat = no ambient/auxiliary tool surface | — | **High**: supply-chain + capability escape |
| `presets` (template override stack) | **DEFER** | spec:docs/reference/presets.md:138–205; ranex:SOURCE_OF_TRUTH §4 (document classes) | Could override Ranex policy projection; mechanism is prompt-level | Minor | — | Low | Med: must not override normative ADR/policy |
| `workflows` (shell/fan-out/gate) | **REJECT** (shell) / **MODIFY** (gate chain) | spec:docs/reference/workflows.md:481 (no sandbox), :465–481; ranex:FLEET §11.2, §15.1 | Gate+chain shape is fine; **shell step has no sandbox** | Automation | Moat = governed execution w/ tool-boundary enforcement | — | **Critical**: unsandboxed shell = unrestricted effect |
| `bundles` (compose ext/preset/wf) | **DEFER** | spec:docs/reference/bundles.md:1–46; ranex:legal/LICENSE-RANEX (personal-use, no redistribution) | Distribution layer needs provenance model first | — | Ranex legal manifest requires provenance | Low | Med: community bundle = unvetted provenance |
| Catalog/provenance | **REJECT** (unvetted) | spec:docs/reference/* `catalog list` env var > project > user > built-in; ranex:legal/licensing-manifest.json, NOTICE.md | Community catalogs lack Ranex's provenance obligations (`NOASSERTION`, CURATED_RESEARCH) | — | Moat = auditable provenance | — | **High**: provenance gap |

---

## 3. Smallest first end-to-end slice (Ranex-native, Spec-Kit-shaped)

Pick **one internal Ranex tooling/documentation work item** (e.g., enhance `scripts/architecture/generate_contracts.py`, or add one missing template) and run it through a Ranex-native "specify" projection:

1. **specify** → owner intent becomes `WorkIntake` + a `spec` artifact; requirement rows get `subject_schema`/`subject_digest` (AI_ARTIFACT_CONTRACTS §4). Borrow Spec Kit's *prompt structure* (user stories, FRs, acceptance scenarios, `[NEEDS CLARIFICATION]`), but write Ranex schemas, not `spec.md`.
2. **clarify** → L1 research packet; unknowns tagged FACT/INFERENCE/UNKNOWN (AI_LIFECYCLE §5.1).
3. **plan** → `TaskPacket` compiler emits one packet with task-minimal proper-subset grant + single route lock (FLEET §6.1, §11.2). No markdown constitution read by the agent.
4. **tasks** → one `WorkerAssignment`/`WorkerAttempt`/`WorkerLease` (fenced) for a single leaf worker (FLEET §6, §8.1 default = one worker).
5. **implement** → `RunResult` with evidence refs; **no self-mark** (CORE_SDLC §2.10).
6. **analyze/checklist** → independent review observations (advisory).
7. **gate + human landing** → `GateEvaluation` → `HumanDecisionRecord` → `Permit` → `LandingRecord` (AI_ARTIFACT_CONTRACTS §9).

This proves the pattern fits *without* installing Spec Kit, copying its files, or trusting any prompt-level governance. It also exercises exactly the one real ADR-0008 TDD cycle + landing + review that `IMPLEMENTATION_START_READY` already requires (AI_ARTIFACT_CONTRACTS §13).

---

## 4. Patterns that conflict with Ranex invariants

1. **Constitution-as-markdown-the-agent-reads** (spec:spec-driven.md:46–49; spec:templates/commands/specify.md:115) vs Ranex README.md:35–39 ("rules an agent can read are suggestions… rules compiled into code are constraints") and SOURCE_OF_TRUTH §7 (machine contract registry is authority).
2. **Maker self-approval** (spec:implement.md:166; converge self-assess) vs CORE_SDLC §2 invariant 10 + AI_LIFECYCLE §9.2 ("human lands the change"). "The human governor accepts" is non-delegable.
3. **Unsandboxed shell** (spec:workflows.md:481) vs FLEET §11.2 permission gateway + §15.1 default worker posture (deny-by-default, no ambient capability).
4. **Community extensions/presets/bundles mutate commands/templates** (spec:extensions.md, presets.md, bundles.md) vs SOURCE_OF_TRUTH §9 (RFC/ADR for process/architecture/capability change) and FLEET §15.2 (worker cannot widen tools).
5. **Living/flow-back spec mutation** (spec:evolving-specs.md:35–80) vs AI_ARTIFACT_CONTRACTS §4–§5 exact-subject + immutable `CoreSDLCTrace`; Ranex requires new subject on change, not in-place edit.
6. **Broad integrations incl. `hermes`** (spec:integrations.md:26) vs ADR-0011 (Hermes/Nous inference decommissioned; only Claude Agent SDK + Codex app-server are qualified runtime adapters).
7. **Popularity as fitness** — explicitly excluded by your brief and by Ranex SOURCE_OF_TRUTH §2.2 (model review is the *weakest* empirical-evidence tier; stars are below that).

---

## 5. Commercial-value hypotheses (clearly separated from facts)

**Facts (from the attached docs):**
- Ranex's contract generator+validator currently reports `PASS` on `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` (README.md:190); runtime remains `NOT_ASSESSED`.
- Spec Kit is MIT-licensed, actively maintained, multi-agent integrated; its checklist/analyze ideas are sound requirement-engineering practice.
- Ranex is LICENSE-RANEX **personal-use** (NOTICE.md:19–26): no redistribution/business use without owner permission.

**Hypotheses (unproven, to be tested — not claimed as value):**
- *H1:* Offering a Ranex-native "specify-style" intake command lowers owner onboarding friction and increases admissible work-item quality. (Testable via SDLC-ADOPT-E capability profile + owner-satisfaction measure.)
- *H2:* Borrowing Spec Kit's *requirement-quality checklist* vocabulary improves Ranex `DEFINED` (level 1) assessments without changing enforcement. (Testable via false-accept rate in review.)
- *H3:* A governed "converge"-like rework detector reduces landed-but-incomplete work. (Testable via escaped-defect / rework measure.)
- *H4:* There is commercial differentiation in marketing "governed, not just disciplined" agents — i.e., Ranex's moat is *deterministic governance that cannot be talked out of a verdict*, whereas Spec Kit makes agents *disciplined*. (Commercial positioning hypothesis; not a technical fact.)
- *H5:* Integrating Spec Kit's broad agent list would widen Ranex's addressable market. (Contradicted by ADR-0011; treating as rejected, not a live hypothesis.)

None of H1–H4 are established by this review
