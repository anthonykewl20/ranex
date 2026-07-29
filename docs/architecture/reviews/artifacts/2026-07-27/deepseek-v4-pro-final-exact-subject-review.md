# Independent Advisory Architecture & File-Structure Review — DeepSeek V4 Pro (Final Exact-Subject Audit)

## 1. VERDICT

**ACCEPTABLE_FOR_FORMAL_CONTRACTING**

The documented target architecture satisfies the owner’s mandatory requirements: a full-system map subordinate to a human-governed Core SDLC, clear authority boundaries, exact-subject integrity, proper fork/strangler migration, explicit exclusions, and a rational AI‑worker fleet control envelope. No blocker prevents entry into the machine-contract and formal ADR phase. The items listed below must be resolved before the first governed runtime tracer, but they do not invalidate the architecture as the contractual target.

## 2. P0 FINDINGS

**NONE**

No violation of a non-negotiable invariant, authority breach, irreconcilable contradiction, or missing required exclusion was found in the attached exact subject.

## 3. P1 FINDINGS

These must be addressed before the architecturally‑governed code tracer (Route 4: “First governed tracer route”) is accepted as valid; they are not architecture‑map blockers but execution‑readiness prerequisites.

1. **`SDLC‑FORK‑000` pending‑status pre‑condition**  
   *Files:* `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §1.2, `SDLC_CONTROL_CATALOG.md` §8.  
   The fork‑ancestry preflight is correctly recorded as `PENDING` and blocks all runtime implementation commits. The architecture’s honest `“fork target / ancestry adoption pending”` label is appropriate, but a tracer cannot begin until this gate passes. The project must execute the preflight (immutable safety‑ref, upstream tree/ license/notices, human‑chosen adoption strategy, and merge‑base proof) **before** any governed runtime activity touches the product branch. This is a process requirement, not an architecture defect; it remains a documented blocker.

2. **`RANEX_IMPLEMENTATION_GUIDE.md` outside review scope**  
   *Files:* `SOURCE_OF_TRUTH.md` §3.1, source‑manifest only.  
   The architecture correctly states the guide must not override the target map, but its content was not included in this exact subject. Before the first tracer, an explicit reconciliation must verify that no residual plugin‑first layout, conflicting phase ordering, or model‑based authority language remains. The guide must be regenerated or formally amended to align with the architecture before it is referenced as a construction input.

3. **Public release gate for `LOCAL_ONLY`/`PROHIBITED_PENDING_RIGHTS` artifacts**  
   *Files:* `legal/licensing‑manifest.json`, `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §29, §33.3.  
   The licensing manifest classifies the twelve foundational‑reference files and the entire Kimi corpus as `LOCAL_ONLY` with `release_blocker: true`. The architecture describes a release‑gate that rejects these paths, but the gate itself is not yet implemented (Gate `AI-G2` and schema‑validation are not yet done). The first runtime tracer that exercises the full built artifact must verify that no `LOCAL_ONLY` or uncleared path can leak into a public package, mirror, or deployment input. This is a build‑release control requirement, not a map change.

4. **AI‑worker fleet adoption gates `SDLC‑ADOPT‑FLEET‑A` through `F` unproven**  
   *Files:* `AI_AGENT_FLEET_CONTROL_PLANE.md` §21, `CORE_SDLC_OPERATING_MODEL.md` §18.  
   The fleet control plane is mapped but runtime enforcement and measured scaling remain `R_AND_D`. The default of one worker is safe. Before any multi‑worker configuration is attempted, `SDLC‑ADOPT‑FLEET‑B` (single‑worker packet‑to‑cleanup tracer) and the subsequent safety gates must pass. This is an adoption‑gate requirement, not an architecture contradiction.

5. **Formal schema and contract validation (`AI‑G2`) not yet executed**  
   *Files:* `AI_ARTIFACT_CONTRACTS.md` §1, §12.  
   All templates are provisional example shapes; the executable schemas, registries, canonical‑digest golden tests, and fail‑closed fixtures do not exist. The architecture cannot claim contract seam sealing until `AI‑G2` passes. This must be completed before the runtime tracer can bind exact‑subject contracts.

## 4. P2 FINDINGS

Documentation, provenance, or clarity improvements that do not block formal contracting but would strengthen the architecture before implementation.

1. **`foundation` package size‑budget left undefined**  
   *File:* `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §13.  
   Rule 1 states the foundation package has “a strict size and consumer review budget” but no numeric ceiling is set. This is acceptable for a target map but should be quantified (e.g., maximum line count or rule count) before the authority Route begins.

2. **`compatibility` context classification borderline**  
   *Files:* `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §9.3, §12.1, §11.1.  
   The architecture calls it “exceptional boundary package, not an authority context” and does not assign it a standard `contract.yaml` or the full API/domain/application/ ports skeleton. The decision is explained, but the text could be misinterpreted. A clarifying note in the file catalog that it expressly owns no canonical state and must never evolve into an authority context is advisable.

3. **Missing `unit_of_work.py` / `integration_event_outbox.py` port description**  
   *File:* `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §12.1.  
   The table says “every stateful context also has a narrowly typed local …” but only some entries list them. This is harmless, but a cross‑reference to a common pattern (e.g., `foundation`‑provided base) would reduce ambiguity.

4. **Visual diagrams and alternative text for SVG/HTML**  
   *Files:* `ranex‑sdlc‑full‑spec.svg`, `ranex‑sdlc‑visual‑guide.html`.  
   The SVG is referenced but its accessibility (screen‑reader) and non‑visual audit trail are not described. This is a minor inclusion standard; the architecture already states it is a non‑normative projection.

5. **Date references in the fork preflight**  
   *File:* `HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §1.2.  
   The preflight facts use a documentation commit hash as a historical anchor; the text could clarify that this is frozen history and not a live pointer.

## 5. APP ARCHITECTURE AND FILE‑TREE AUDIT

The full‑system tree is consistent with the bounded‑context ownership map. All capability zones have a unique owner, an explicit file home, and dependency‑direction rules that forbid reverse coupling.

- **No orphan capability** was found; even inactive capabilities (e.g., voice, microVMs) have a mapped attachment point and require a future product‑scope ADR before activation.
- The `governed_execution` authority cell’s internal file partition (reducer, UoW, journal, outbox, permit) is explicit and correctly isolated.
- The `web‑dashboard` application is properly segregated under `apps/` and contains no authority‑transition logic.
- The `legacy/` and `compatibility/` trees maintain separation; no Ranex domain imports legacy Hermes roots except through the compatibility adapter.
- The `adapters/` directory includes harness, platform, and process‑assurance implementations, respecting inward‑only dependency from adapters to ports.
- The `architecture/contracts/` set (identities, states, roles, lifecycles, etc.) can be compiled into machine‑validatable schemas without ambiguity once the generation toolchain exists.

**Actionable suggestions:**
- Clarify whether `foundation` may ever contain a `typing`‑only utility that imports from `domain`—the current rule forbids it.
- In transition, the `src/ranex/compatibility/hermes_legacy/` sub‑tree should be explicitly listed in the path‑ownership registry to prevent accidental new dependency insertion.

## 6. STATE, CONTRACT, AND AUTHORITY AUDIT

- **Typed namespaces** are correctly separated: `WorkItemStatus` ≠ `RunStatus` ≠ `AssignmentStatus` ≠ `GateOutcome` etc. No aggregate owns another’s transition.
- **Exact‑subject binding** is consistent across artifacts: every evidence, permit, and gate requires project/ work/ run/ workspace/ packet/ workflow/ policy digests. The subject models (work, exact, architecture, research, resource) use discriminated schemas.
- **Gateway ordering** (evidence → gate evaluation → optional human decision → authority grant → permit → effect) is irreversible and never allows a model to emit a transition.
- The `governed_execution` transaction atomically updates the run version, journal, consumed grant/permit, and outbox intents; no external effect runs inside the transaction.
- `CoreSDLCTrace` is correctly required for every run, review, gate, and release evidence; it is nullable only for project/release root reservations.
- The `CapabilityAssessment` and `CapabilityDomainProjection` templates correctly enforce no arithmetic aggregation, lowest‑member‑level derivation, and priority‑rule tiering.

**Potential future edge:** The `Policy` and `HumanDecisionRecord` are owned by `policy` while the `ConsumableAuthorityGrant` is owned by `governed_execution`. The architecture cross‑references them; no data‑race exists because the grant is issued from a snapshot and consumed within the authority cell. This is sound for a one‑host monolith, but the snapshot digest must be validated before use—this invariant is stated but could be made a machine‑checkable assertion in the contract schemas.

## 7. HERMES‑FORK AUDIT

- The fork preflight `SDLC‑FORK‑000` is genuinely fail‑closed; the architecture does not claim ancestry until proven. This is faithful to owner requirements.
- Upstream‑sync lifecycle (`OBSERVED → … → BASELINE_RECORDED`) includes `BLOCKED` and `ROLLED_BACK` branches and requires per‑commit/path disposition.
- Desktop exclusion is executable: sync and release gates reject any Electron or desktop‑bootstrap content.
- De‑commercialization is explicit: Nous Portal/billing/credits paths are on the denylist and rejected by classification gate.
- Compatibility surfaces have a lifecycle `SUPPORTED → DEPRECATED → READ_ONLY → REMOVED`, preventing indefinite legacy support.
- The strangler migration (physical coexistence, compatibility adapter, selective extraction) is described in §11.1 and respects shared‑history constraints.

**No conflict with the architecture.** The only actionable item is the still‑pending preflight gate, captured in P1.

## 8. SDLC, BOOK, AND AI BOUNDARY AUDIT

- The architecture is strictly subordinate to the human‑owned Core SDLC; no AI‑worker lifecycle (`L0`–`L12`) can transition a `WorkItem`. All authority points are correctly mapped to named human roles.
- The Engineering Reference Application Map clearly distinguishes major practice references from authority; each saved book has explicit adopted/rejected dispositions and no book heuristic overrides a Core SDLC control.
- SWEBOK V4.0a’s outdated 12207:2017 crosswalk is flagged as needing a versioned 2026 mapping; this is a documented risk, not a hidden conflict.
- AI‑agent “orchestration” is prohibited from redefining the SDLC; the fleet control plane is a worker‑subprocess specification, not a second process authority.
- Learning quarantine rules prevent any learned routing/policy from activating without explicit human ADR and hidden‑holdout evidence.

**Conclusion: The SDLC/Book/AI boundary is correctly delineated and lawful.**

## 9. RIGHTS AND RELEASE AUDIT

- The licensing manifest classifies every file, preserves upstream MIT license for future Hermes legacy, and correctly marks foundational‑reference full‑texts as `LOCAL_ONLY` / `PROHIBITED_PENDING_RIGHTS`.
- `LICENSE‑RANEX.md` restricts redistribution but, together with the GitHub Terms of Service exception, allows the repository to exist publicly while preventing off‑platform conveyance. This is a deliberate owner decision; the architecture does not misrepresent the license as open‑source.
- Build/release gates will reject any `LOCAL_ONLY` path; this is described but not yet implemented (covered in P1 finding #3).

**No rights‑based architectural defect exists.** The architecture faithfully records its limitations.

## 10. TOP ACCEPTANCE TESTS

The ten highest‑value tests that would falsify the architecture if they failed (ordered by severity):

1. **Fork‑ancestry proof and restored upstream LICENSE** — `SDLC‑FORK‑000` must pass with a verifiable merge‑base and license restoration.
2. **Authoritative transition atomicity** — During a crash at the exact point of a gate evaluation → permit consumption, replay must leave exactly one valid journal entry and no orphan outbox intent.
3. **Reducer purity** — In a fenced sandbox with no network, the reducer must produce identical results across 10,000 replays of the same recorded inputs.
4. **Policy PEP denial** — An attempted effect without a valid, unexpired, exact‑subject permit must be denied, and the denial must be recorded without allowing a side‑effect.
5. **Stale worker fencing** — A reclaimed worker attempting to write a result or submit a mailbox acknowledgment must be blocked at every boundary (tool, model, artifact store).
6. **Artifact‑purge integrity** — After an authorized purge, replay must yield `EVIDENCE_PURGED`, not a generic missing‑artifact error or a silent fallback to pass.
7. **Hidden‑fixture isolation** — A maker’s workspace must be unable to read, list, or otherwise access the verifier‑only hidden‑anchor fixtures, even through symlinks, alternate worktrees, or sub‑processes.
8. **Upstream‑sync anti‑recontamination** — A candidate port set containing a reinstated `Portal/billing` path must fail the de‑commercialization gate with a specific, auditable reason.
9. **Transitive budget exhaustion** — A child worker that spawns a nested sub‑agent must cause its parent reservation to reach the hard cap and deny further work without circumvention.
10. **Rollback after a failed release** — Performing a full `ROLLED_BACK` transition must leave the service in the exact pre‑release state (verified by configuration audit, checksum, and external‑effect reconciliation) without manual intervention.

These tests are documented in the architecture’s behavioral‑gate section and can serve as the initial falsification suite.

## 11. OPEN CONFLICTS OR UNKNOWNS

The following items genuinely require human decision, upstream evidence, or runtime measurement before they can be resolved; none are architecture‑map gaps.

- **Fork‑adoption strategy** (human decision) — whether to replay Ranex documentation commits on top of the pinned upstream base or perform a provenance‑complete history import.
- **Public redistribution of foundational‑reference and Kimi corpus** — rights clearance is not available and may never be; the architecture’s “blocked” stance is correct, but the possibility of obtaining a license or removing the files is an owner choice.
- **Concrete lease/heartbeat durations and worker concurrency limits** — these need Ranex runtime evidence (the fleet‑adoption gates prescribe measurement).
- **Measurement harness maturity** — the process‑assurance measurement adapters do not exist; closing the calibration gate `SDLC‑ADOPT‑E` requires a functioning, qualified harness.
- **ISO/IEC/IEEE 12207:2026 crosswalk for SWEBOK** — will need a versioned mapping before any standards‑clause conformance claim is made.

**END OF REVIEW**
