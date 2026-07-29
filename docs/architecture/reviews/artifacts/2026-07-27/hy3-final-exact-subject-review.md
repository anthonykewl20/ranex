1. `VERDICT`: `CHANGES_REQUIRED`

2. `P0 FINDINGS`:
`NONE` — No blocker violates a non-negotiable invariant in the frozen payload that would prevent formal contracting once the machine registries exist. The documents consistently enforce human authority, AI-worker subordination, fail-closed fork preflight, and local-only rights exclusion.

3. `P1 FINDINGS`:
   1. **File**: `docs/architecture/AI_ARTIFACT_CONTRACTS.md` §12 and `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §11 / `architecture/contracts/` list. **Violated invariant**: `AI-G2` requires executable schemas and registries; the frozen payload contains only provisional `templates/` and no `architecture/contracts/*.yaml` or `schemas/` tree. **Consequence**: `AI-G2` cannot be claimed; any tracer must report schema validation as `UNKNOWN`/not implemented. **Precise correction**: Before the first governed runtime tracer, generate the exact registry files (`identities.yaml`, `states.yaml`, `roles.yaml`, etc.) and the `schemas/` subset from `AI_ARTIFACT_CONTRACTS.md` §12, validate them in CI, and bind their digests in the release manifest.
   2. **File**: `legal/licensing-manifest.json` (file entries for `docs/research/books/...` and `docs/research/kimi-research/...`). **Violated invariant**: `SDLC-FORK-000` and rights-safety rule require `LOCAL_ONLY`/`PROHIBITED_PENDING_RIGHTS` paths to never enter Git index/package. The `.gitignore` excludes `docs/research/books/` and `docs/research/kimi-research/`, but the manifest itself is committed and references those hashes; a future `git add` of the manifest does not add the files, yet the release gate must mechanically scan the index. **Consequence**: If any ignored file is force-added or a mirror includes the raw directory, release blocker fails. **Precise correction**: Add a CI check that parses `legal/licensing-manifest.json`, enumerates every `repository_inclusion: LOCAL_ONLY` path, and verifies it is absent from `git ls-files` and from any release tarball, failing with `PROHIBITED_PENDING_RIGHTS` if present.
   3. **File**: `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §1.2 / `SDLC_CONTROL_CATALOG.md` §8 (`SDLC-FORK-000`). **Violated invariant**: No runtime implementation commit may be accepted until fork ancestry preflight passes; current label is "fork target / ancestry adoption pending". **Consequence**: The architecture is conditionally accepted but not runtime-validated. **Precise correction**: Implement the deterministic gate `SDLC-FORK-000` as code (immutable safety ref, upstream tree verification, human decision record, merge-base proof) and run it against the pinned upstream before any product-branch code commit; until then keep `MAP`/`AI-G` gates at `UNKNOWN`.

4. `P2 FINDINGS`:
   1. **File**: `docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml` and `CAPABILITY_DOMAIN_PROJECTION.yaml`. **Correction**: Template fields mix `null` and `UNKNOWN` (e.g., `level: null` vs `result: NOT_ASSESSED`); the spec in `SDLC_CONTROL_CATALOG.md` §3 (`SDLC-MEA-002`) defines ordinal labels and `UNKNOWN` as a status, not a value for `level`. Clarify in template comments that `level` must be omitted (not `null`) when `result != SCORED` to avoid JSON Schema confusion.
   2. **File**: `docs/architecture/SOURCE_OF_TRUTH.md` §3.1 references `RANEX_IMPLEMENTATION_GUIDE.md` as not overriding architecture, but that file is not in the frozen payload (only in manifests). **Correction**: Either include the guide in the frozen subject or explicitly mark it as `OUT_OF_SCOPE` for this review to prevent stale assumptions.
   3. **File**: `docs/architecture/README.md` read-order lists `reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md` but that file is not in the frozen payload (only referenced in licensing manifest as CURATED_RESEARCH). **Correction**: Note that the review reconciliation file is not part of the exact-subject source manifest and is historical advisory only.

5. `APP ARCHITECTURE AND FILE-TREE AUDIT`:
   - **Missing responsibility**: `src/ranex/adapters/process_assurance/fleet_measurement_reader.py` and `experiment_runner.py` are specified in architecture §11 but no corresponding interface contract or port is shown in `AI_ARTIFACT_CONTRACTS.md`. **Correction**: Add `process_assurance` port definitions to `schemas/` (or `architecture/contracts/`) mapping `fleet_measurement_reader` and `experiment_runner` to `process_assurance/ports/` as prescribed.
   - **Misplaced**: `docs/architecture/templates/` holds `RFC.md` and `ADR.md` as governance forms; the architecture §11 target tree places ADRs under `docs/architecture/decisions/` and RFCs under `docs/architecture/rfc/`. **Correction**: Keep templates as examples but note the real ADR/RFC homes are `decisions/` and `rfc/` to avoid confusion.
   - **Duplicated**: `CORE_SDLC_TRACE.yaml` is both a shared embedded block and listed as a template; the artifact contract §5 says it can be embedded or referenced. No code-level duplication, but the template should explicitly state it is the single canonical shape for all contexts.

6. `STATE, CONTRACT, AND AUTHORITY AUDIT`:
   - **Namespace separation**: `WorkItemStatus`, `RunStatus`, `AssignmentStatus`, `LeaseStatus`, `MailboxDeliveryStatus`, `ReservationStatus`, `FleetExperimentStatus`, `CapabilityAssessmentStatus`, `IntakeStatus`, `PacketStatus`, `DispatchOfferStatus`, `PermitStatus`, `HumanDecisionRecordStatus`, `AuthorityGrantStatus`, `EffectStatus`, `ReconciliationStatus`, `ModuleStatus`, `RouteStatus`, `ExtensionStatus`, `CompatibilityStatus`, `SyncCandidateStatus`, `UpdateStatus`, `CutoverStatus` are all defined with distinct owners in architecture §16. No collision found.
   - **Authorization order**: `EvidenceSnapshot -> GateEvaluation -> HumanDecisionRecord -> ConsumableAuthorityGrant -> Permit -> effect` is enforced in `AI_ARTIFACT_CONTRACTS.md` §9 and templates. No model or maker can short-circuit.
   - **Subject binding**: `ExactSubjectV1` and other subject schemas are consistent across templates; `AI_TASK_PACKET.yaml` embeds the subject without recursive packet digest. Good.
   - **Registry conflict**: `architecture/contracts/` (full-system) vs `schemas/` (artifact subset) is explicitly a superset/subsets relation; no conflict if generator respects one canonical path per schema.

7. `HERMES-FORK AUDIT`:
   - **Ancestry preflight**: `SDLC-FORK-000 = PENDING`; blocked until machine gate runs. Required evidence items listed in architecture §1.2 and control catalog §8 are complete as spec, not as executed code.
   - **Upstream sync**: `SDLC-FORK-002` lifecycle defined; `BLOCKED`/`ROLLED_BACK` branches deterministic. No broad auto-merge.
   - **Compatibility**: `SDLC-FORK-004` status enum `SUPPORTED -> DEPRECATED -> READ_ONLY -> REMOVED` mapped to `CompatibilityStatus`. Legacy home isolated.
   - **Desktop exclusion**: Explicitly excluded in architecture §3, §31, and sync gate rejects Electron. Verified.
   - **De-commercialization**: Provenance denylist and SBOM checks required; `Nous` commercial paths removed.
   - **Migration/cutover**: `SDLC-FORK-006` cutover modes; strangler plan §11.1. All mapped, but unvalidated at runtime.

8. `SDLC, BOOK, AND AI BOUNDARY AUDIT`:
   - No document lets a book heuristic (Clean Code, SWEBOK, etc.) override policy. `ENGINEERING_REFERENCE_APPLICATION_MAP.md` §10 rejects "Code is the only truth", fixed coverage, etc.
   - AI workers are uniformly "bounded workers"; DeepSeek/HY3 are route data, not authority (`HERMES_GROUND_ZERO...` §23, `AI_AGENT_DEVELOPMENT_LIFECYCLE.md` §2.1). Model consensus is explicitly not a gate.
   - `ADR-0001` and `SOURCE_OF_TRUTH.md` keep Core SDLC as parent; L0–L12 are activity protocol, not work-item states.

9. `RIGHTS AND RELEASE AUDIT`:
   - `.gitignore` ignores `docs/research/books/` and `docs/research/kimi-research/`, matching `LOCAL_ONLY`/`PROHIBITED_PENDING_RIGHTS` in `legal/licensing-manifest.json`.
   - `legal/licensing-manifest.json` itself is `RANEX_ORIGINAL` and committable; it correctly classifies all frozen architecture docs as `RANEX_ORIGINAL` (Personal-Use-1.0) and research as `CURATED_RESEARCH`/`NOASSERTION`.
   - **Risk**: The `docs/research/books/PDFs/*.pdf` and `*.md` are ignored, but the manifest lists them with `release_blocker: true`. A packaging script must fail if any such path appears in the index or tarball. The frozen payload does not include a CI script; this is a process gap to close before release (P1 item 2 above).
   - `final-exact-subject-source-manifest.sha256` includes those local-only hashes, but the bundle manifest excludes them, complying with the review prompt's rule.

10. `TOP ACCEPTANCE TESTS` (ten highest-value falsifiers):
    1. Two workers race for one assignment; exactly one active lease exists (fleet control §23.1).
    2. Reclaimed stale worker attempts every write/tool/result path; old fencing epoch denied everywhere (§23.2).
    3. Child spawns nested work and evades budget; every charge reaches ancestors and hard cap stops tree (§23.3).
    4. Worker writes outside canonical path via symlink/subprocess/generated path; denied (§23.4, architecture §33.3).
    5. Model repeats syntactically varied failed actions; result-aware loop detection suspends (§23.5).
    6. Maker attempts to read/overwrite/predict hidden verification; candidate invalidated (§23.6).
    7. Planner proposes overlapping writers; deterministic scheduler rejects (§23.7).
    8. Reconciler produces conflict patch and attempts self-landing; only proposal + human landing allowed (§23.8).
    9. Coordinator crashes at claim/heartbeat/completion/outbox; recovery yields no double assignment or blind replay (§23.9).
    10. Verifier/human capacity exhausted; admission backpressure stops new work without reducing assurance (§23.10).

11. `OPEN CONFLICTS OR UNKNOWNS`:
    - Exact lease durations, heartbeat cadence, concurrency limits, task populations, model mix, verification margins: require Ranex runtime evidence (fleet control §24, Kimi reconciliation §10).
    - `SDLC-FORK-000` actual Git ancestry proof not yet executed; current branch `bootstrap/pre-upstream` has no merge base with upstream (architecture §1.2) — must be resolved by human decision + code.
    - Local noise floor for level-4 claims cannot default to zero; needs method evidence and independent approval (`SDLC_CONTROL_CATALOG.md` §3).
    - Kimi corpus provenance (author/model/license) unknown; not reusable as verified research without corrected derivative (Kimi reconciliation §8).
    - Whether `RANEX_IMPLEMENTATION_GUIDE.md` (not in frozen set) conflicts with current architecture on older plugin-first layout — needs explicit reconciliation before any implementation.
    - ISO/IEC/IEEE 12207:2026 crosswalk vs SWEBOK V4.0a 2017 mapping is historical; needs versioned 2026 mapping (ENGINEERING REFERENCE MAP §1, foundational reconciliation §7.1).
