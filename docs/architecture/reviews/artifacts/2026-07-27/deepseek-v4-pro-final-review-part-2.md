## 7. HERMES‑FORK AUDIT

**Lineage, upstream‑sync, compatibility, desktop, de‑commercialization, and cutover gaps**

- Lineage proof remains a pending preflight (FORK‑PREFLIGHT). The architecture does not claim completed ancestry; it correctly states “fork target / derived relationship, upstream fetched, ancestry adoption pending”.  
- Upstream‑sync lifecycle (`OBSERVED` → … → `BASELINE_RECORDED`) is fully specified with per‑commit/path disposition, anti‑recontamination gates, and selective porting.  
- The disposition ledger for inherited Hermes behavior (RETAIN / WRAP / EXTRACT / REIMPLEMENT / REMOVE / QUARANTINE / DEFER) is mandatory; its execution is a precondition for extraction but does not block the map.  
- De‑commercialization is enforced by release, sync, and provenance gates that explicitly reject Nous Portal/billing/credit paths, desktop binaries, and bundled commercial dependencies. Desktop exclusion is executable: any selected port set, build graph, or manifest containing desktop code is rejected.  
- Compatibility surface lifecycle (`SUPPORTED` → `DEPRECATED` → `READ_ONLY` → `REMOVED`) is owned by `service_management`; the architecture correctly forbids indefinite compatibility without a renewed human decision.  
- The one‑writer cutover states (`BOOTSTRAP` → … → `LEGACY_REMOVED`) guarantee exactly one canonical writer in every mode. “Dual run” means dual execution surfaces, not dual authority.  

**Gap:** The FORK‑PREFLIGHT gate is described procedurally but not yet assigned a machine‑checkable gate ID in the `GateOutcome` registries. It should be added as `FORK‑PREFLIGHT‑001` with a concrete evidence checklist before any implementation commit is accepted.

## 8. SDLC/AI BOUNDARY AUDIT

The architecture consistently treats AI agents as workers inside the core SDLC. Every potential boundary violation is prevented by explicit countermeasures:

- **No AI‑owned lifecycle state:** `WorkItemStatus` and `RunStatus` are owned exclusively by `work_management` and `governed_execution`, respectively. AI‑worked runs produce proposals and evidence; they never directly transition those aggregates.  
- **No agent‑issued permits:** Only `governed_execution` can issue a `ConsumableAuthorityGrant` and a `Permit`, and that issuance occurs only after an exact‑subject `GateEvaluation` and, where required, a human `HumanDecisionRecord`.  
- **No model‑generated gate outcome:** Models produce `ReviewObservations`; these are validated by the `assurance` context into `EvidenceSnapshots` and then evaluated by a qualified deterministic gate evaluator. No model emits a `GateOutcome`.  
- **No bypass of the capability bus:** All target‑mode effects cross the `CapabilityBus`. No special tool or agent path exists.  
- **No model‑lowered risk:** Risk lanes are derived by the `policy` engine from configuration items, data classification, and other objective inputs. A worker’s risk proposal is advisory only.  
- **No self‑approval:** Independence evaluation is deterministic, comparing maker and reviewer identities, sessions, and route facts. The AI‑agent lifecycle (L6) explicitly forbids both the maker and reviewer from being the same execution principal for enhanced/critical work.  
- **No hidden agent authority:** Every agent collaboration result is a typed worker proposal. The architecture prohibits any Hermes session, Codex/Claude output, or Kanban projection from being an authority source.  

The only open question—not a gap—is whether real‑world packet compilation and gate evaluation will be fast enough for practical development; this is an implementation‑calibration issue, not an architecture boundary violation.

## 9. TOP ACCEPTANCE TESTS

The ten highest‑value falsification tests for the architecture:

1. **No agent can transition a work item** – Attempt to set `WorkItemStatus` from an AI‑worked run without an intervening human decision. Expect: the `work_management` transition service rejects the request.  
2. **Atomic authority transaction survives mid‑crash** – Kill the process after writing the journal record but before committing the effect outbox row. After recovery, verify no orphan permit or outbox entry exists and the current run state is consistent.  
3. **Pure reducer replays identically** – Feed the same deterministic input log to the `governed_execution.domain.reducer` twice; confirm bit‑identical output and no external I/O.  
4. **Exact‑subject mismatch blocks permit** – Change the candidate commit in the `ExactSubject` after the gate evaluation but before the permit request; the permit issuance must fail.  
5. **Hermes worker cannot write the authority database** – Execute a compromised legacy `run_agent.py` that tries to open `$RANEX_HOME/db/ranex.db`. Verify OS‑level denial (file permissions/sandbox) and a recorded denial in the telemetry.  
6. **Anti‑recontamination gate blocks commercial paths** – Attempt to upstream‑sync a candidate that restores a Nous billing endpoint; the sync classification service must reject it with reason `COMMERCIAL_RE‑CONTAMINATION`.  
7. **Backup/restore reconciliation** – Make an external effect (e.g., a GitHub issue comment), take a backup, delete the effect record, then restore. Run the reconciliation service and verify it discovers the missing effect and marks it `OUTCOME_UNKNOWN` → `SUCCEEDED` with the actual GitHub comment ID without re‑execution.  
8. **Route identity change forces re‑probation** – Modify the tool‑permission profile of an active route lock; verify the route transitions to `PROBATION` and that no run can use it until requalification completes.  
9. **Sandbox denial of network egress** – Launch a tool‑bearing harness with an explicit network‑enabled profile that attempts to connect to `https://example.com`. The egress adapter must deny the connection and record the destination and reason.  
10. **De‑commercialized release has zero monetization paths** – Perform a release build of the full target; an automated SBOM and source scan must find no references to Nous Portal, billing endpoints, credit systems, or desktop binaries.  

## 10. OPEN CONFLICTS OR UNKNOWNS

Only genuine unresolved questions that require a human decision or runtime data:

1. **FORK‑PREFLIGHT execution** – The specific Git history‑rewriting strategy (rebase‑vs‑import) and the exact ancestry proof method need human selection; the architecture shows the requirements but not the final Git recipe.  
2. **Local runner vs. Temporal** – The architecture ports a local durable runner but leaves the final selection behind the runtime port to a future experiment. That choice will be determined by the replay, cancellation, and upgrade‑crash matrix of the local implementation.  
3. **Policy engine (built‑in vs. OPA)** – Both are kept as ports; the built‑in engine must be proven adequate for offline decisioning and rapid evaluation before the OPA adapter is abandoned or promoted.  
4. **Sandbox profile selection (Bubblewrap vs. Docker)** – The isolation matrix is defined; real denial, escape, and performance tests will determine which profile layers fulfill the trust‑tier requirements.  
5. **Artifact trust anchoring** – The architecture assumes local tamper‑evident baselines; if an external witness or transparency log is required later, a new threat‑model ADR must be accepted.  
6. **Voice activation** – The adapter is mapped but marked inactive; any activation would require a new product‑scope ADR and privacy/security qualification.  
7. **Multi‑host control** – Explicitly excluded from the current product; a new human‑driven architecture decision (and a separate map) would be needed if this ever becomes a product goal.  
8. **Performance envelope of atomic authority transaction** – The design shows one SQLite transaction per run transition; real‑world throughput under concurrent projects and effect outbox dispatch is unknown and will be measured during the concurrency‑recovery implementation route.  

No remaining conflict: all previously noted document‑level inconsistencies (lifecycle namespaces, rollback re‑entry, maturity language) were reconciled in the final architecture pass and the supporting visual review.