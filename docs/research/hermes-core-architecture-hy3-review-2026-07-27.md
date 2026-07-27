# HY3 advisory review of the Ranex Hermes-core architecture

- **Date:** 2026-07-27
- **Execution window:** 2026-07-27T19:16:03+08:00 to
  2026-07-27T19:19:29+08:00
- **Evidence status:** cross-family advisory review; no transition authority
- **OpenCode version:** `1.18.7`
- **OpenCode agent:** `plan` (read-only)
- **Provider:** `openrouter`
- **Model:** `tencent/hy3`
- **Variant:** `high`
- **OpenCode session:** `ses_05cb5ff07ffezZAPVFoKVdAhch`
- **Ranex revision:** `3844673b0bfa743de3c351566b6ffa9ffd67e0b8`
- **Hermes revision under review:**
  `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`
- **Alignment-input SHA-256:**
  `344c14f6e5a475af2eebdd5ff444079188b5bf78c44c65fafbada662d352b4c7`
- **Architecture-input SHA-256:**
  `af1c1f59338a66a6732ea601ee723513488ea61e2fb44816daba5cdf933551ca`
- **Review-prompt SHA-256:**
  `119dff1ce2a40493ddd40b89b1e7523d08771d1a98d88fc3e9b7403baba74bfe`
- **Final-response SHA-256:**
  `c02b6d871f3653707cf3dc55837468de7714ecc06545f9d292cf0288703de6a6`
- **Session usage reported by OpenCode:** 60,805 input tokens; 3,706
  output tokens; 12,540 reasoning tokens; 35,712 cache-read tokens; no
  cache-write tokens
- **Session cost reported by OpenCode:** USD `0.017782644`
- **Repository mutations reported by OpenCode:** zero files, additions, or
  deletions

## Evidence limitations

HY3 read both attached research documents in full. It did not directly clone or
exhaustively inspect the pinned Hermes checkout during this run. Consequently,
claims it labels `[OBS]` are corroborations of observations and citations in
the supplied reports, not a second independent source-code audit.

The model's hidden reasoning trace is intentionally not reproduced. The final
response is stored below exactly as returned. Model output remains advisory
evidence: it cannot authorize a Ranex transition, settle an ADR, or overrule a
primary source or deterministic test.

The input architecture report still said HY3 was unavailable. HY3 therefore
repeated that statement in its `UNKNOWN` section. That observation became stale
when this very review completed.

## Reconciliation against the audited evidence

### Accepted corrections

1. **Scope complete mediation by migration mode.** Per-effect mediation is a
   target-driver invariant. A transitional Hermes/Codex/OpenCode subprocess is
   mediated at the activity and OS-isolation boundary; it is not proof that
   every internal harness call crossed `CapabilityBus`.
2. **Test real adapters, not only a fake driver.** The migration exit gate must
   exercise actual sequential, parallel, terminal, file, browser, MCP,
   app-server, subagent, plugin, network, and background paths.
3. **Do not create a `control_plane` god package.** Nonreplaceable application
   control is a trust layer, not one source-code module. Application services
   should live with their owning bounded contexts, with one explicitly owned
   cross-context process manager.
4. **Keep the local workflow composition tagged R&D.** SQLite, transactions,
   reducers, and outboxes are mature components. Ranex replay, signal, timer,
   cancellation, migration, and crash behavior are not mature until the P0
   matrix passes.
5. **Bind packet determinism to its resolved inputs.** A frozen task plus frozen
   source/retrieval revisions must produce the same manifest and digest.
   Stochastic retrieval must be recorded as an activity result, not hidden
   inside compilation.
6. **Preserve evaluation value before archiving runners.** Extract reusable
   paired-run fixtures and harness behavior from `batch_runner.py` and
   `mini_swe_runner.py`; archive the inherited entry points only after the
   Ranex evaluation module proves parity.
7. **Prevent `ExecutionContext` from becoming ambient state.** Version the
   envelope and give each context the smallest immutable subject view it
   requires.

### Qualified challenges

- “Ranex owns control, authority, state, and proof; Hermes supplies reasoning”
  is an **OWNER REQUIREMENT + ARCHITECTURE PROPOSAL**, not an implemented fact.
  The negative case against Hermes as authority is source-backed; clean
  extraction remains a P0 feasibility test.
- TTS/STT remain outside the first text-phone release. If voice becomes a
  requirement, they return as delivery adapters, never as kernel code.
- Minimal deterministic, scoped retrieval is required for packet compilation.
  The rejected capability is broad shared mutable memory, not read-only
  revisioned source selection.
- The exact upstream batch runners need not become permanent architecture.
  Their useful evaluation fixtures and paired-baseline behavior must survive
  until a qualified replacement exists.

### Stale or already-accounted observations

- The response's statement that HY3 had not run was true in its attached input,
  but was invalidated by completion of this session.
- The nine guide conflicts were not assumed resolved by the architecture
  report; they were already explicit Phase-0 blockers. HY3 correctly reinforces
  their priority.
- One HY3 run satisfies the requested cross-family second look. It does not
  calibrate HY3 as a reliable architecture grader or constitute a second
  independent code audit.

## Verbatim final response

```text
I've read both documents in full (cookbook-alignment-research through line 1496; hermes-core-architecture-research through line 2104). Below is my independent review. I distinguish **[OBS]** observed in pinned code, **[INF]** architectural inference, and **[REC]** my recommendation.

---

# EXECUTIVE VERDICT

The two reports are well-reasoned, internally consistent, and correctly identify Hermes's structural limits and the right *target shape*: a governed deterministic kernel with contained probabilistic workers. **However, they overstate maturity and understate the single hardest risk.** The central safety claim — "every effect is completely mediated; no bypass exists" — is **proven only for a fake driver in target mode, not for the real Hermes/Codex subprocesses**, which run their own agent loops and are mediated only at the OS-sandbox/activity boundary during the transitional phase. No independent cross-family review ran. The architecture is a **strong, falsifiable hypothesis, not validated design.**

Conditional approval only: adopt the direction and the fog/acceptance-test discipline; withhold "architecture approved" until the P0 acceptance tests pass.

---

# CONFIRMED FINDINGS

**F1 — Hermes is edge-modular, not modular DDD.** **[OBS]** `AIAgent.__init__` and `init_agent` expose 72 effective parameters (`agent/agent_init.py:447–2679`); extracted modules back-import `run_agent` (`agent_init._ra()`, `conversation_loop.py`, `tool_executor.py`, `agent_runtime_helpers.py`); no repository-wide dependency rule enforces `domain → ports only`. **Confidence: HIGH.**

**F2 — Hermes's plugin/hook system is non-blocking and cannot be a mandatory PEP.** **[OBS]** `model_tools.py:L1220-1265` logs request-middleware/pre-tool-hook errors and continues; `tool_executor.py:L290-315` returns original args on middleware failure; general plugin hooks are deliberately non-fatal. **Confidence: HIGH.**

**F3 — Cookbook is principle-aligned but not an enforceable OS.** **[OBS]** Its installable plugin carries one `pineapple-check` smoke rule (`cookbook/README.md:21-28`, `session-start.sh:3-15`); `print.py:265-305` launches an outside model process with no isolation/typed-result guarantees. **Confidence: HIGH.**

**F4 — The deterministic-orchestration / nondeterministic-activity split is a mature, correct foundation.** **[OBS/INF]** Temporal/AWS/Cadence citations are apt; the reducer/step separation is the right core decision. **Confidence: HIGH (as a pattern).**

**F5 — The three-plane measurement contract is a sound methodological contribution.** **[INF]** Instrument-soundness / run-conformance / workflow-effectiveness separation (doc1:445-504) correctly prevents "FAIL→PASS" collapse and distinguishes checker qualification from work approval. **Confidence: HIGH (as method).**

**F6 — Stranger-ready packets, maker/checker separation, and fail-closed-on-missing-proof are reusable.** **[OBS]** Cookbook `book/29`, `CONTENTS.md:216-267`, `brief_contract.py` support these. **Confidence: HIGH.**

---

# CHALLENGED FINDINGS

**C1 — "Ranex owns control, authority, state, and proof; Hermes supplies reasoning" presented as a supported conclusion.**
- *Counter:* The **negative** (Hermes must not own authority) is well-evidenced (F2). The **positive** (Ranex can cleanly own all four — especially separating canonical state from `SessionDB` and achieving per-effect mediation) is a **PROPOSAL** with zero runtime. The sentence reads as a verdict but is prescriptive.
- *Correction:* Relabel as **OWNER REQUIREMENT + PROPOSAL**; state explicitly that *feasibility of clean kernel extraction* is itself a P0 acceptance test, not an assumption.
- *Confidence: HIGH.*

**C2 — Invariant 3 ("every effect is completely mediated; no special agent tool bypass exists") is achievable in the transitional design.**
- *Counter:* For **any** harness running its own agent loop (Hermes subprocess, Codex, Claude Code, OpenCode), only **activity-level** mediation + OS sandbox exist. Per-effect `CapabilityBus` mediation requires rewiring each harness's internal tool execution — `tool_executor.py` has sequential (~700 LOC) + concurrent (~700 LOC) + MCP + agent-loop paths, all different routes (doc2:440-460). The Phase 3 exit test uses a **fake driver**, which proves the *interface* exists, not that **real** Hermes/Codex tool paths are mediated. So invariant 3 is **TRUE in target-driver mode, FALSE in transitional mode and for any non-rewired harness.**
- *Correction:* Scope invariant 3 to target mode. For transitional, state the *only* mediation is OS sandbox + activity boundary, and name an acceptance test exercising **real** Hermes/Codex tool paths (forbidden read/write/network/process/argv) through the actual adapter, not a fake.
- *Confidence: MEDIUM-HIGH.*

**C3 — "Small homemade SQLite reducer is the smallest path to one atomic authority boundary; defer Temporal" understates risk.**
- *Counter:* Hand-rolled durable execution with correct replay, timers, signals, cancellation, and idempotency is itself a mature-solved hard problem. The report tags it "MATURE COMPONENTS / R&D composition" (doc2:692) yet treats the composition as low-risk. The mature pattern (Temporal/AWS) contradicts the "build your own" recommendation by omission.
- *Correction:* Keep deferring Temporal, but make **reducer replay correctness** a P0 gate (not assumed); name the build-vs-adopt decision as FOGGY until the crash/recovery matrix passes.
- *Confidence: MEDIUM.*

**C4 — Bloat/removal plan safely removes TTS/STT, broad memory, and archives `batch_runner.py` / `mini_swe_runner.py`.**
- *Counter:* (a) If the chosen phone surface uses voice, removing TTS/STT breaks a *required* module (doc2 keeps "phone surface"). (b) The packet compiler (first-party module) needs *some* scoped read-only context retrieval — "broad shared memory removal" could starve it. (c) `batch_runner.py` / `mini_swe_runner.py` are exactly the harnesses Stage 6 needs for **paired baselines** — archiving them destroys evaluation infrastructure the report itself requires.
- *Correction:* Keep a text-scoped phone surface or retain TTS/STT; retain minimal scoped retrieval for the compiler; move `batch`/`mini_swe_runner` into the evaluation/route-qualification module, **do not archive**.
- *Confidence: MEDIUM.*

**C5 — The "nonreplaceable application control" layer is thin because the pure domain is thin.**
- *Counter:* The five-part inclusion test was applied to *responsibilities*, but `control_plane/` (command_handlers + workflow_coordinator + policy_enforcement + effect_dispatcher + unit_of_work in one package, doc2:1230-1235) is a single undifferentiated blob with **no internal bounded contexts**, while the four pure-domain contexts ARE modular. This is the anemic-domain/smart-service anti-pattern; `control_plane` risks becoming the **new god object**.
- *Correction:* Decompose `control_plane` into one application service per bounded context; apply the same import/dependency fitness rules internally.
- *Confidence: MEDIUM.*

**C6 — Packet/context determinism supports byte-identical conformance (doc1:455-457).**
- *Counter:* The packet's *inputs* (authoritative-source selection, retrieval) may be **stochastic** (memory/search). Same task can yield different packet digests across runs, breaking replay and the measurement contract. The compiler rule "deterministic manifest even if prose changes" (doc1:990) addresses rendering, not input stochasticity.
- *Correction:* Add an acceptance test proving packet-digest stability for a frozen task+source set, and record the packet's input revision set inside its digest.
- *Confidence: MEDIUM.*

---

# UNKNOWN / INSUFFICIENT EVIDENCE

- **No independent cross-family (HY3) review ran** (doc1:10, doc2:6, 1879-1907). The frozen review packet exists but was not executed. Architecture is **uncorroborated**.
- **Host isolation profile unproven** (FOGGY #11): bubblewrap/Docker sad-path denial on the *target host* is untested.
- **Nine Ranex guide contract conflicts unresolved** at report time (doc1:783-791) — resolution assumed, not demonstrated.
- **Clean kernel extraction feasibility**: pure reducer "no Hermes import" + replay is only an exit criterion, not demonstrated on 170k LOC.
- **Local SQLite reducer crash/recovery matrix** — FOGGY #2.
- **Reviewer independence + calibrated model-judge thresholds** — FOGGY #10.
- **Exact transaction ownership across execution/evidence/permit/work projections** — FOGGY #3 (doc2) and P0 (doc1).
- **HY3 as architecture reviewer**: did not execute; its review value is **UNKNOWN**.

---

# TOP FIVE DESIGN RISKS (priority order)

1. **Per-effect mediation gap (transitional).** Invariant 3 is false for any harness running its own loop; only OS sandbox + activity boundary mediate. A contained worker can still exfiltrate or mutate unintentionally. Directly undermines the central safety claim.
2. **Second source of truth during strangle.** `SessionDB` (Hermes) + Ranex execution store + Kanban board + evidence ledger can diverge; the atomic boundary is FOGGY. A crash can show "complete" in one plane and "pending" in another, or orphan a permit — breaking auditability and fail-closed.
3. **Kernel extraction feasibility.** 170k-line entangled fork; "no Hermes import" pure reducer is unproven. If extraction fails, Ranex inherits the god object it set out to replace.
4. **`control_plane` god object / `ExecutionContext` coupling center.** The 20-field immutable `ExecutionContext` (doc2:1344-1380) threaded everywhere repeats `AIAgent`'s 72-param problem in a different shape; `control_plane` is monolithic.
5. **Evaluation & independence vacuum.** No paired baseline, no calibrated grader, no cross-family review, HY3 didn't run. The "measurable effectiveness" differentiator has no instrument yet; promotion/route decisions risk encoding noise.

---

# REQUIRED ACCEPTANCE TESTS BEFORE ARCHITECTURE APPROVAL

- **A. Contract normalization (P0):** one generated governance enum + rule-stage mapping + role registry + canonical config tree + identity schema; zero undeclared transitions/aliases; independent reviewer + owner sign-off (doc1 Stage 0).
- **B. Reducer purity & replay:** pure domain imports no I/O; reject undeclared transitions; replay normal/blocked/cancelled/retried/waived/recovered histories to identical state; inject time/random/network and prove absent (doc2 reducer tests).
- **C. REAL-adapter bypass (not fake):** exercise **actual** Hermes/Codex tool paths against forbidden read/write/network/process/argv; every attempt fails and is attributed. Until this passes, invariant 3 is scoped to target mode only.
- **D. Atomic authority boundary:** one transactional source of truth across execution/evidence/permit/projection; inject crash before/after every write; recovery yields one legal state, one ledger history, no usable orphan permit.
- **E. `control_plane` & `ExecutionContext` fitness:** import tests forbid cross-context business coupling; `ExecutionContext` schema versioned and change-controlled; composition deterministic.
- **F. Packet-digest stability:** same frozen task+source set → identical packet digest; stochastic retrieval inputs recorded in digest.
- **G. Isolation profile on target host:** bubblewrap/Docker sad-path denials (secret read, worktree escape, denied network, argv escape, limits) pass on the actual host.
- **H. Module mediation:** undeclared capability/interface/state-write/side-effect from any module fails pre-execution + leaves audit event.
- **I. Independent cross-family review:** execute the HY3 (or equivalent) review using the frozen packet (doc2:1909-1935); store as advisory evidence, not authority.
- **J. Evaluation instrument exists before any promotion:** paired baseline, frozen holdout, calibrated grader, repeated trials — or no route/model promotion.

---

# MATURITY-TAG CORRECTIONS

| Location | Current tag | Corrected tag | Reason |
|---|---|---|---|
| doc2:1799 "Modular monolith w/ vertical bounded contexts" | MATURE | **MATURE PATTERN / UNPROVEN IN RANEX** | Pattern mature; applying to a forked 170k-LOC god object is unproven. |
| doc2:692 vs 1816 "Local SQLite reducer" | MATURE COMPONENTS / R&D vs MATURING | **COMPONENTS MATURE; COMPOSITION + REPLAY CORRECTNESS = R&D** | Inconsistent; replay correctness is the hard, unproven part. |
| doc2:1820 "Process/container/WASM isolation" | MATURING | **TOOL MATURE; RANEX HOST PROFILE = FOGGY/R&D** (align w/ FOGGY #11) | Bubblewrap/Docker are mature software; the Ranex profile is unproven. |
| doc1:553 "Baked-in modules" | MATURE | **MATURE PATTERN / UNPROVEN IN RANEX** | VS Code/OTel analogy covers shipping, not forked-codebase modularization; dominant volume (Hermes) stays non-modular behind a facade. |
| doc1:559 evaluation guidance | MATURE | **MATURE GUIDANCE; RANEX IMPL = PROPOSAL/R&D** | Avoid implying Ranex already implements it. |
| doc2 HY3 architecture-review independence | (implied done) | **UNKNOWN — NOT EXECUTED** | Distinct from HY3 model maturity; the independence claim is weakened because the reviewer didn't run. |
| REJECT list (exactly-once, plugin-as-PEP, model self-auth, same-process hostile Python, event-source everything) | REJECT | **Keep REJECT** | Correctly tagged. |

---

# FINAL RECOMMENDATION

**[REC]** Adopt the architecture **direction** and the **fog/acceptance-test discipline** as the project's controlling method. **Do NOT treat the architecture as validated.** Grant **conditional approval** contingent on passing P0 tests A–E and I. Before any implementation beyond Stage 0:

1. Resolve the nine guide conflicts into one generated contract set (P0).
2. Build the pure reducer + fake-driver tracer first, but **immediately follow with the REAL-adapter mediation test (C)**, not only a fake.
3. Make the atomic authority boundary explicit and tested **before any completion effect exists** (D).
4. Decompose `control_plane` per bounded context; version `ExecutionContext`; prevent it becoming the new god object (E, C5).
5. Obtain the cross-family review; until then, mark all Ranex-runtime maturity claims as PROPOSAL/UNPROVEN (I).
6. Retain evaluation harnesses (`batch`/`mini_swe_runner`) and minimal scoped retrieval; do not starve the packet compiler or the route-qualification stage (C4).

This is a strong, falsifiable hypothesis. **Approve as a research/design target; withhold "architecture approved" until the P0 gates pass.**

---

*Note: I am in read-only/plan mode and have not modified any files. This review is analysis only. The two source documents contain the detailed citations; my challenges above reference their line numbers directly so the owner can verify each claim against the pinned revisions.*
```
