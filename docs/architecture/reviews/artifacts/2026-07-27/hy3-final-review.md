1. `VERDICT`: `CHANGES_REQUIRED`

2. `P0 FINDINGS`:
   1. **File/section**: `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §1.2 “Fork-lineage reality and required preflight” (and `legal/licensing-manifest.json` per `source-manifest.sha256`).
      **Violated invariant**: Owner requirement 4 (ground zero = dependency-clean Ranex core built by strangler migration *inside a governed, attributed fork* of `nousresearch/hermes-agent`); architecture explicitly states `bootstrap/pre-upstream` has *no merge base* with upstream baseline and `github_network_fork: false`.
      **Consequence**: The claimed “attributed fork” is unproven; implementation starting under this target would either be a clean-room rebuild (violating req 4) or an undocumented fork; ancestry/license provenance gates (`SDLC-FORK-001/002`) cannot pass.
      **Precise correction**: Complete `FORK-PREFLIGHT` steps 1–7 before any code migration: preserve current Ranex commits under immutable ref, verify pinned upstream tree `129a4419…`, record human-selected adoption strategy (replay vs import), set `upstream` fetch-only, update `legal/licensing-manifest.json` `github_network_fork` to actual hosting fact, and relabel architecture status from “conditionally accepted” to “fork‑proof pending” until gate passes.

3. `P1 FINDINGS`:
   1. **File/section**: `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §11 and §12.1 vs `source-manifest.sha256` – `architecture/contracts/*.yaml` not present in manifest (only planned). **Violated**: `AI-G2` contract readiness (`AI_AGENT_DEVELOPMENT_LIFECYCLE.md` §6) not met. **Consequence**: Machine contract registry (identities, states, lifecycles) is prose-only; packet determinism and namespace enforcement unenforceable pre-tracer. **Correction**: Generate `architecture/contracts/` from accepted ADRs before first governed tracer; validate against `AI_ARTIFACT_CONTRACTS.md` §12.
   2. **File/section**: `docs/research/ranex-sdlc-visual-hy3-review-2026-07-27.md` cites SHA-256 for `CORE_SDLC_OPERATING_MODEL.md` as `b2171f67…` whereas `source-manifest.sha256` binds `56c6151e…`. **Violated**: Provenance/traceability (`SOURCE_OF_TRUTH.md` §6). **Consequence**: Visual review reconciled against a different policy snapshot; adoption-gate evidence may be stale. **Correction**: Re-run visual reconciliation against manifest-bound digests or record explicit supersession.
   3. **File/section**: `HERMES_GROUND_ZERO…` §33.3 behavioral P0 gates list “real Hermes/Codex/Claude/OpenCode bypass matrix” but `adapters/harnesses/` tree lacks explicit bypass-test fixtures. **Violated**: HY3 correction #5 (real bypass matrix) adopted in reconciliation but not yet mapped to file home. **Correction**: Add `tests/security/bypass_matrix/` with per-adapter denial fixtures before tracer route 5.

4. `P2 FINDINGS`:
   1. `docs/architecture/reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md` §2 lists `ocask-alignment-research` SHA `f3a57e48…` but manifest binds `1856b917…` for `ocask-alignment-research-2026-07-27.md` (different file name/date). Provenance labeling ambiguous; clarify mapping.
   2. `HERMES_GROUND_ZERO…` §36 cites `ranex-sdlc-full-spec.svg` as generated projection; manifest includes digest `2ac6625d…` but SVG content not provided in review packet – audit relies on Mermaid block per rules, acceptable but note in evidence log.
   3. `AI_AGENT_DEVELOPMENT_LIFECYCLE.md` §10 references `templates/` dir not present in source tree (only spec). Documentation should state templates are provisional until `AI-G2`.

5. `OWNERSHIP AND FILE-TREE AUDIT`:
   - **Missing**: `process_assurance` context (§9.2) has no dedicated adapter under `src/ranex/adapters/` (e.g., `qualification/fixture_runner` exists but no `process_assurance` port). Correction: add `adapters/process_assurance/audit_reader/` or confirm it uses `qualification` adapters; assign explicit port in §12.1 catalog.
   - **Duplicated**: None identified; `policy` vs `governed_execution` grant separation clean.
   - **Misplaced**: `compatibility/hermes_legacy` correctly isolated; `legacy/hermes` frozen subset per §11.1 step 7 not yet populated (expected). No misplacement in target tree.

6. `STATE AND AUTHORITY AUDIT`:
   - Namespaces: `WorkItemStatus`, `RunStatus`, `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, `ModuleStatus`, `RouteStatus`, `ExtensionStatus`, `CompatibilityStatus` each owned by distinct context (§16, `CORE_SDLC` §3.2). No collision.
   - Transition order: §8.2 atomic authority transaction binds run row + journal + permit + outbox; `work_management` consumes events idempotently. Compliant.
   - Authorization order: §20 one-way flow evidence→snapshot→gate→human decision→grant→permit→effect. No violation found.
   - Conflict: `SDLC-FORK-003` update states vs `ReleaseStatus` in §16 – both exist; mapped via `SDLC-FORK-003` not as `WorkItemStatus`. Acceptable.

7. `HERMES-FORK AUDIT`:
   - Lineage: Unproven per P0.
   - Upstream-sync: `upstream_sync` context + `SDLC-FORK-002` lifecycle defined; anti-recontamination gate in §29.2. Adequate.
   - Compatibility: `compatibility` boundary package + `service_management` owns `CompatibilityStatus`; `SDLC-FORK-004` lifecycle present.
   - Desktop: Explicitly excluded (`apps/desktop/` absent, §31). Confirmed.
   - De-commercialization: `provenance_compliance` context + denylist.yaml; §29.2 sync gate rejects Portal/billing. Good.
   - Cutover: `SDLC-FORK-006` one-writer cutover states mapped. Gap: preflight blocks start.

8. `SDLC/AI BOUNDARY AUDIT`:
   - No place where AI becomes method/authority. `AI_AGENT_DEVELOPMENT_LIFECYCLE.md` §2 roles prohibit model from owning transition; L0–L12 mapped to Core SDLC states (§5.0). `ADR-0001` governs.
   - Minor: `HERMES_GROUND_ZERO…` §36 describes DeepSeek V4 Pro as “primary architecture/file-structure collaborator” – advisory only, not authority; flagged as evidence not decision.

9. `TOP ACCEPTANCE TESTS` (ten highest-value falsifiers):
   1. Reducer purity + replay: same inputs → same state (§18, §33.3).
   2. Atomic authority transaction: simulate failure mid-commit leaves no partial effect (§8.2).
   3. Real harness bypass matrix: Hermes/Codex/Claude/OpenCode cannot write authority DB or escape sandbox (§27, HY3 corr #5).
   4. Exact-subject permit CAS: replayed permit consumed twice rejected (§8.1, §21).
   5. Evidence vs observation isolation: model `ReviewObservation` cannot set `GateOutcome=PASS` (§20).
   6. Packet digest stability: changed source → different `pkt_` digest (§15, L3).
   7. Backup/restore external reconciliation: restored state reconciles GitHub/provider/outbox (§28).
   8. Upstream-sync anti-recontamination: candidate restoring Nous billing blocked (§29.2).
   9. De-commercialization runtime+SBOM: zero monetization artifacts in package/network (§31, §33.3).
   10. First governed tracer denial: missing policy → effect denied visibly (§20, route 4).

10. `OPEN CONFLICTS OR UNKNOWNS`:
   - Fork ancestry proof pending human decision on adoption strategy (replay vs import) – requires human.
   - `legal/licensing-manifest.json` `github_network_fork` value vs attributed-fork claim needs human/hosting fact.
   - `ranex-sdlc-full-spec.svg` content not directly inspected (digest bound only) – runtime research not needed but visual parity unverified.
   - Provider/route identity behavior may change post-review; `RouteStatus` probation logic needs runtime evidence.
   - `AI-G2` schema validation unimplemented; contract registry maturity unknown.

*HY3 advisory challenge complete; no human authority claimed; evidence distinguished from claims per manifest.*