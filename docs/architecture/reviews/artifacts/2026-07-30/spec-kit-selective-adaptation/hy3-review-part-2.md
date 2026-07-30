## 6. Unresolved questions and required RFC/ADR decisions

**Unresolved questions (must be closed before any adaptation):**

1. **Build vs. wrap.** Should Ranex (a) implement a native "specify-shaped" command that emits Ranex artifact schemas, (b) wrap the Spec Kit CLI behind a Ranex runtime adapter, or (c) reject? This is undecided in the attached docs.
2. **Authority for the "constitution" analog.** Which Ranex artifact owns the principle set — an existing ADR/policy, or a new registry? It must not become markdown an agent reads (README.md:35–39). Undecided.
3. **Registry gap.** `SOURCE_OF_TRUTH.md §7` enumerates contract registries but lists no `requirements`/`spec` projection. Is one required to bind Spec-Kit-style specs to exact subjects (AI_ARTIFACT_CONTRACTS §4)? Undecided.
4. **Subject schema for spec artifacts.** Should a spec bind as `work-subject/v1` or require a new discriminated subject? The attached schemas define work/exact/architecture/research/resource subjects but no "spec" subject.
5. **Topology fit.** Is `SINGLE_WORKER` (FLEET §8.1) sufficient for the recommend slice, or does a new decomposition need a `STAGED_CHAIN` assignment (FLEET §8.2)? Undecided.
6. **Licensing/provenance of borrowed templates.** Whether incorporating Spec Kit's MIT-licensed prompt templates into Ranex original material is permitted under LICENSE-RANEX personal-use, and how to record it in `legal/licensing-manifest.json` / NOTICE.md. Undecided and legally load-bearing.
7. **Tooling-tracer scope.** Any automation around specify→converge must stay inside ADR-0012's bounded `PRE_READINESS_TOOLING_TRACER`; its exact permissible surface is undefined.

**Exact RFC/ADR decisions required (each is a governed change under SOURCE_OF_TRUTH §9):**

- **RFC + new ADR (e.g. ADR-0014):** Adopt, modify, or reject a "specification-decomposition workflow" as a Ranex-native process. This changes workflow semantics → RFC/ADR mandatory.
- **ADR:** Runtime-adapter decision for any wrapper. ADR-0011 fixes the qualified adapters to Claude Agent SDK + Codex app-server (SOURCE_OF_TRUTH §7.5); invoking the Spec Kit CLI would need a route-lock/adapter decision, not an ambient shell.
- **RFC + ADR (compliance):** Provenance/licensing disposition of any borrowed MIT template → record in `legal/licensing-manifest.json`; likely a `COMPLIANCE_PROVENANCE` work item.
- **ADR:** Define the authoritative home of the principle set and forbid a readable-markdown constitution (resolves Q2); bind it to the machine-contract registry, not a prompt file.
- **RFC:** Add (or explicitly decline) a `requirements`/`spec` projection to `architecture/contracts/` (resolves Q3); if added, the generator+validator must change.
- **ADR:** Confirm the self-approval boundary — mandate that any "implement/converge" mapping emits `RunResult` + `GateEvaluation` + human landing with **no maker self-mark** (CORE_SDLC §2 invariant 10; AI_LIFECYCLE §9.2).
- **ADR:** Sandbox/permission ruling for any workflow automation, given Spec Kit `workflows.md:481` states "no capability sandbox" — Ranex must not inherit that gap.

---

## Claims in my earlier answer I now regard as uncertain (not directly supported by the attached subject)

These are analytical inferences or judgments, not statements found in the attached Ranex/Spec Kit docs. Listed for honesty; they do not change the §1 verdict, which rested on directly cited conflicts.

1. **Effort ratings (Low/Med/High) in the ADOPT/MODIFY/REJECT/DEFER matrix.** Pure analyst judgment; the attached docs contain no implementation-effort data for any Ranex-native reimplementation. Treat as estimates, not facts.
2. **The specific artifact-mapping projections** (e.g., "specify → `WorkIntake`", "plan → `TaskPacket`", "tasks → `WorkerAssignment`"). The attached docs *define* those Ranex artifact types and the Spec Kit surfaces, but **nowhere state they correspond to one another**. The mappings are my recommended interpretation, not subject-stated equivalences.
3. **Legal claim that incorporating Spec Kit's MIT templates into Ranex is permitted.** The attached NOTICE.md and LICENSE-RANEX.md address Hermes *upstream* MIT vs. Ranex original material only; they do **not** explicitly cover incorporation of a *third-party* MIT project (Spec Kit) into Ranex original material. This needs the legal review named in Q6 above; I should not have implied it was settled.
4. **Qualitative praise of Spec Kit** ("well-built", "genuinely useful", "sound requirement-engineering practice"). Subjective assessment, not a fitness fact; consistent with your instruction to ignore popularity, but still opinion rather than subject-supported evidence.
5. **The disposition recommendations** (e.g., DEFER living-spec/flow-back, MODIFY converge) are recommendations I supplied, not mandates in the attached Ranex docs. The docs forbid living-spec-style mutation via their immutability rules, but the *specific* Defer/Modify labeling is my call.
6. **H1–H5 were correctly labeled hypotheses**, but the framing of the §3 slice *assumes* a Ranex-native specify command should be built — that assumption is itself open decision Q1, not a concluded position.

No file was edited.
