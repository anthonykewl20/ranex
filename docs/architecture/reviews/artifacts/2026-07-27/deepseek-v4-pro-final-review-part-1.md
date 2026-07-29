# Full-Map Architecture Review Report

## 1. VERDICT: `ACCEPTABLE_FOR_FORMAL_CONTRACTING`

The target architecture is complete, internally consistent, and satisfies every non-negotiable owner invariant. The map has no missing ownership, authority collisions, or unknown capability zones. All capability zones have explicit owners, bounded contexts, public API surfaces, trust tiers, lifecycles, attachment points, and file-tree homes. The AI-agent development lifecycle, core SDLC, artifact contracts, and source-of-truth policy form a coherent hierarchy. The Hermes fork lineage, de‑commercialization, migration, and upstream‑sync boundaries are fully defined. The implementation preflight (FORK-PREFLIGHT) and several implementation‑time research gates remain open, but they do not shrink the map; they are acknowledged conditions for runtime validation.

The advisory review therefore finds the architecture ready for formal contracting, with the preconditions explicitly noted.

## 2. P0 FINDINGS: NONE

No blocker was identified that would prevent the architecture from serving as the normative target. Every owner requirement, fixed decision, and non‑negotiable invariant is respected, and no structural contradiction exists among the normative documents.

## 3. P1 FINDINGS

These are pre‑tracer corrections that would sharpen the architecture without changing its commitments.

1. **Signed maintenance controller authority**  
   **File/section:** `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md`, sec. 14.1 “Signed maintenance controller”  
   **Observation:** The architecture requires a signed maintenance controller but does not assign ownership of the signing key, ceremony, or revocation.  
   **Consequence:** Without that ownership, the controller’s integrity proof could become ambiguous.  
   **Correction:** Explicitly state that `release_management` owns the binary signing key and policy for the maintenance controller, and that the controller’s signature is verified by the bootstrapper using a pinned public key embedded in the release manifest.

2. **Exact‑subject for architecture review**  
   **File/section:** `AI_AGENT_DEVELOPMENT_LIFECYCLE.md`, sec. 5.3 “L2 – Architecture and decision” and `AI_ARTIFACT_CONTRACTS.md`, sec. 6 “ArchitectureReconciliation”  
   **Observation:** The `ArchitectureReconciliation` artifact should bind an exact subject (e.g., the architecture document’s digest at a point‑in‑time). The specification currently describes the packet and proposal but not the subject’s own digest.  
   **Consequence:** Full exact‑subject traceability is required for the architecture gate, yet the artifact contract does not define the subject field.  
   **Correction:** Add an `arch_subject_digest` field to the `ArchitectureReconciliation` schema (or to the `ArchitectureReviewPacket`) that freezes the exact revision/digest of the architecture documents being evaluated.

3. **Upstream‑fork preflight as a gated precondition**  
   **File/section:** `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md`, sec. 1.2 “Fork‑lineage reality and required preflight”  
   **Observation:** The architecture lists the FORK-PREFLIGHT steps but does not assign an explicit gate ID (e.g., `SDLC‑FORK‑P0`) or define the evidence required to mark it passed.  
   **Consequence:** The preflight remains a prose requirement without a machine‑checkable status.  
   **Correction:** Register a gate `SDLC‑FORK‑P0` in the gate‑namespace registry and define the exact evidence checklist (preserved safety ref, pristine‑upstream tree verification, adopted‑ancestry proof, license restoration). The gate must be `PASS` before any implementation commit is accepted into the product branch.

## 4. P2 FINDINGS

Documentation, provenance, or clarity improvements that do not affect architectural soundness.

1. **Licensing‑manifest state**  
   `legal/licensing-manifest.json` currently records `github_network_fork: false`. The architecture (sec. 1.2) notes that this will become true after the preflight; a forward reference in the manifest or a note in the architecture that links to the preflight gate would be clearer.

2. **Explicit listing of the sixteen canonical WorkItemStatus values**  
   The current visual HTML guide was updated to display all sixteen states, but the SDLC operating model’s ASCII diagram (sec. 4.2) mentions only the normal path. Adding the exceptional states (BLOCKED, CANCELLED, ROLLED_BACK) to the inline state list would avoid confusion.

3. **DeepSeek V4 Pro / HY3 provenance**  
   `reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md` notes that raw model responses were not retained as content‑addressed artifacts. While fidelity is not mandatory for advisory evidence, a future best‑practice could capture the provider response digests for reproducibility.

## 5. OWNERSHIP AND FILE‑TREE AUDIT

**Missing, duplicated, or misplaced responsibilities:** None.

Every bounded context listed in section 9 has a corresponding top‑level directory under `src/ranex/`, and the target tree (section 11) contains all required `api/`, `domain/`, and `application/` packages. The `governed_execution` context is the only one whose internal detailed files are enumerated; the others follow the standard package contract (section 12) and the canonical file‑responsibility catalog (section 12.1). The web dashboard, generated contracts, adapters, tests, and configuration directories are all present and correctly placed. The `compatibility` boundary is a special package, not an authority context, and it appears correctly under `src/ranex/compatibility/`. No responsibility appears in two places, and no required adapter is omitted.

## 6. STATE AND AUTHORITY AUDIT

**Namespace, transition, and authorization‑order conflicts:** None.

- `WorkItemStatus`, `RunStatus`, `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, and `ActivityStatus` are clearly separated namespaces with distinct owners.  
- The gate/decision/permit order (evidence → gate → human decision → authority grant → permit) is enforced; a permit cannot be created without a preceding gate evaluation and, when required, an authenticated human decision.  
- The atomic authority transaction in `governed_execution` (section 8.2) includes run version compare‑and‑swap, evidence snapshot binding, and effect outbox insertion—all within one SQLite write. No other context can write canonical run state.  
- The `policy` context’s `HumanDecisionRecord` is append‑only and never consumed; the derived `ConsumableAuthorityGrant` is single‑use and subject to CAS.  
- The only “cross‑context” updates use typed integration events and idempotent commands, which are acknowledged as at‑least‑once and subject to reconciliation. There is no distributed transaction illusion.  
- All lifecycle crosswalks, invalidation rules, and state‑ownership registries are documented and will ultimately live in the machine contract registries (`architecture/contracts/`), preventing accidental resumption of a wrong owner.

## 7. HERMES‑FORK AUDIT

**Lineage, upstream‑sync, compatibility, desktop, de‑commercialization, and cutover gaps:** The fork map is complete but has one unresolved condition.

- The architecture mandates a preflight (FORK‑PREFLIGHT) before any code change, and documentation correctly states “fork target / derived relationship, upstream fetched, ancestry adoption pending.”  
- Upstream sync is defined as a specialized SDLC work class with its own lifecycle (`OBSERVED → FETCHED → … → BASELINE_RECORDED`).  
- Every inherited Hermes surface requires a disposition ledger (RETAIN / WRAP / EXTRACT / REIMPLEMENT / REMOVE / QUARANTINE / DEFER).  
- The anti‑recontamination gate (section 29.2) explicitly blocks reintroduction of Nous commercial paths, desktop code, or authority bypass.  
- Legacy compatibility surfaces use `SUPPORTED → DEPRECATED → READ_ONLY → REMOVED`, owned by `service_management`.  
- The one‑writer cutover (`BOOTSTRAP → … → LEG
