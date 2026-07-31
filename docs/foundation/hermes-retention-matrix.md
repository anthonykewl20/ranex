# Hermes retention matrix

**Date:** 2026-07-31 · **HEAD:** `f2c04c167` · Companion to
[`hermes-inventory.md`](hermes-inventory.md), which carries the measurements
this matrix classifies.

---

## How to read the classifications

The commissioning brief assumed Hermes code is present and must be pruned.
[`hermes-inventory.md` §0](hermes-inventory.md) establishes by executed
provenance that it is not: **zero Hermes runtime directories exist at `HEAD`**,
and the Hermes baseline is **not an ancestor** of this lineage.

The six classifications are therefore applied to a forward-looking question —
*should this capability enter the Ranex tree, and on what terms?* — with a
status column recording where the artifact stands today.

| Classification | Meaning in this repository |
|---|---|
| **KEEP** | Present in the Ranex tree and retained as-is. |
| **KEEP TEMPORARILY** | Present and retained, with a named expiry or trigger that closes it. |
| **ADAPT** | Ranex needs the capability; the Hermes design or interface is a useful input; the implementation is written fresh. |
| **REPLACE** | Ranex needs the capability; the Hermes implementation is structurally unfit and must not be a starting point. |
| **REMOVE** | Ranex does not want the capability. Where it is already absent, this reads **"confirm absent — do not import."** |
| **UNKNOWN — REQUIRES SPIKE** | Cannot be classified without executed evidence. |

**"Removal risk" for an absent subsystem is re-import risk, not deletion risk.**
Nothing listed `REMOVE` requires a deletion commit; the risk being managed is
that a future slice pulls it in for expedience.

---

## Matrix — the 21 named subsystems

### 1. CLI and entrypoints — **REMOVE** (absent) / Ranex CLI **KEEP**

| Field | Value |
|---|---|
| **Current responsibility** | Hermes: one 17,241-line `cli.py` plus `hermes_cli/` (224 files, 188,972 LOC) fronting sessions, billing, auth, dashboards, checkpoints, container boot. Ranex: `src/ranex/cli/main.py`, one subcommand. |
| **Dependencies** | Hermes CLI depends on effectively the whole tree. Ranex CLI depends on `argparse`, `json`, `subprocess`, `sys`, `pathlib`, and `ranex.*`. |
| **Slice 1 depends on it?** | **Yes — on the Ranex CLI.** `ranex gate evaluate` is the slice's entire operator surface. **No** dependency on anything Hermes. |
| **Ranex replacement** | Already built and executing. Verified: `PASS`/`FAIL`, correct exit codes ([inventory §5](hermes-inventory.md)). |
| **Removal risk** | **None** for Hermes (absent). For the Ranex CLI the risk is the opposite — scope creep. `cli.py` at 17,241 lines is the demonstrated end state of an entrypoint nobody bounded. |
| **Removal trigger** | n/a. Guard trigger: any PR adding a second subcommand before Slice 1 is accepted **ends the slice** (walking skeleton §5). |
| **Evidence** | `git ls-tree -r HEAD --name-only -- hermes_cli` → 0. `git show phase/2-runtime-bootstrap:cli.py \| wc -l` → 17,241. `src/ranex/cli/main.py:1-8`. |

### 2. Model-provider abstraction — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | Multi-provider routing with adapter/model/auxiliary fallback, credit accounting, Nous Portal entitlement. 9 transports + 6 adapters. |
| **Dependencies** | Credential pool, billing, rate-limit tracker, Portal. |
| **Slice 1 depends on it?** | **No — and must not.** `BC-5` requires that removing model access changes no verdict. `src/ranex/cli/main.py:1-8` asserts no model is reachable. |
| **Ranex replacement** | `ADR-0011`: one explicit provider/model/transport/adapter/auth/route per assignment; **adapter, provider, model and auxiliary fallback all disabled**; failure is a typed result returned to Ranex. Initial boundaries named: Claude Agent SDK, Codex app-server. |
| **Removal risk** | **Low.** The replacement authority is already accepted. Risk is inverse: importing the Hermes abstraction would import routing flexibility that `ADR-0011` then has to disable. |
| **Removal trigger** | The slice that first dispatches a model worker. Not Slice 1. |
| **Evidence** | `ADR-0011:118-130` (route lock, no fallback); `ADR-0006:226-236` `DEC-RANEX-025`/`026`; walking skeleton `BC-5`. |

### 3. Agent execution loop — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | Model-driven turn loop, 6,763 LOC. The model decides what to call, when to stop, when to retry. |
| **Dependencies** | Transports, tool executor, context engine, memory, prompt builder. |
| **Slice 1 depends on it?** | **No.** Slice 1 has no loop. It evaluates one gate against recorded evidence and exits. |
| **Ranex replacement** | `ADR-0011` runtime boundary: `governed_execution` → typed `WorkerRuntime` port → Ranex-owned pinned adapter → official provider runtime → one **leaf** worker. |
| **Removal risk** | **Low**, deferred. |
| **Removal trigger** | Same as row 2. |
| **Evidence** | `ADR-0011:66-72` — *"The target does not put a Hermes `AIAgent`, Nous model, Markdown skill, model-authored shell command, PTY, terminal scraper, or `tmux` keystroke loop between the Ranex scheduler and a worker."* |

### 4. Prompt handling — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | Assembles system prompt, skills, memory, coding context into the model call — 2,090 + 614 LOC plus caching, sanitisation, scrubbing. |
| **Dependencies** | Skills, memory manager, context engine. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | **None, deliberately.** The product thesis is that rules belong in checking code, not prompts. A prompt-assembly subsystem in the foundation would be an invitation to encode a rule in the place the thesis says does not work. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. Re-import trigger: any prompt template entering `src/ranex/` before a slice explicitly authorises worker dispatch. |
| **Evidence** | Walking skeleton §2, quoting the thesis under test: *"rules compiled into code change what an agent produces; rules in a prompt do not."* |

### 5. Tool execution — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | Dispatches model-requested tool calls under a runtime-configurable approval mode and guardrails. |
| **Dependencies** | Toolsets, approval, permissions, plugins. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | `ADR-0011` capability envelope: each role has an immutable maximum; each assignment compiles a task-minimal subset; **empty is the default**; every effectful call crosses policy and `CapabilityBus`. |
| **Removal risk** | **Low.** |
| **Removal trigger** | Same as row 2. |
| **Evidence** | `ADR-0011:48-56` — *"a prompt, provider allow-list, prior session, ambient user configuration, or worker request cannot broaden the effective set."* |

### 6. Terminal and filesystem access — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | Model-authored shell, PTY, `tmux` scraping, full desktop and browser control (`tools/computer_use/`, `tools/browser_*`, `tools/desktop_ui.py`). |
| **Dependencies** | Tool executor, approval, computer-use permissions. |
| **Slice 1 depends on it?** | **No — the opposite is intended.** `src/ranex/cli/confinement.py` (44 lines) implements refusal of absolute paths, traversal above the repository root, and remote targets — but ⚠ **it is not wired into `cli/main.py`**; see readiness assessment **G6**. |
| **Ranex replacement** | Repository confinement, **written but not in force**. Walking skeleton §9 says the three path failure modes "are the enforcement of 'governs only this repository,' which is otherwise only prose" — at present the enforcement is *also* only prose, because the helper those tests exercise is never called by the CLI. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. |
| **Evidence** | `ADR-0011:70-72` — shell/PTY/tmux "may appear only in diagnostic or compatibility evidence outside the qualified product hot path; they cannot be an active runtime adapter." `tests/security/test_repository_confinement.py`. |

### 7. Task lifecycle — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | Session/subagent lifecycle keyed to conversation turns; completion asserted by the agent. |
| **Dependencies** | Conversation loop, checkpoints, kanban watchers. |
| **Slice 1 depends on it?** | **No.** Slice 1's unit of work is one evaluation; there is no lifecycle. |
| **Ranex replacement** | `DEC-RANEX-009` — `work_management` alone owns `WorkItemStatus`. `KANBAN-PROJECTION-001` (`ADR-0016`) — boards are disposable rebuildable projections, never completion authorities; every board action round-trips through transition rules and may be rejected. |
| **Removal risk** | **Low.** |
| **Removal trigger** | The slice that introduces a work item outliving one command. |
| **Evidence** | `ADR-0016` `KANBAN-PROJECTION-001`; `ADR-0006:98-104`. |

### 8. Context and memory — **REPLACE** (deferred), one open question

| Field | Value |
|---|---|
| **Current responsibility** | Lossy conversation compression plus a mutating cross-session learning graph — ~2,500 LOC across 12 modules. |
| **Dependencies** | Conversation loop, memory provider, curator. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | Not designed. What Ranex needs is not "memory" — it is a **replayable journal**, already built: `src/ranex/…/sqlite/journal.py`, 94 lines, "append-only evaluation journal, hash-chained." |
| **Removal risk** | **None** now. Later risk is a **category error**: a future slice asks for "agent memory," someone reaches for a compressor, and a hidden non-deterministic input enters the verdict path. |
| **Removal trigger** | Any slice proposing to carry state between agent invocations must first state whether that state is an input to a verdict. If it is, it must be journalled, not summarised. |
| **Evidence** | `BC-4` requires byte-identical output from identical inputs — measured `IDENTICAL` at [inventory §5](hermes-inventory.md). A lossy compressor keyed on accumulated history is a hidden input by construction (**INFERENCE**; structural, not measured against running Hermes). |

### 9. Scheduling — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | `cron/` — 8,938 LOC of recurring personal-automation jobs, including model-suggested and model-classified ones. |
| **Dependencies** | Chronos plugin, gateway, tools. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | `ADR-0011`: "Ranex control services are the sole orchestrator, dispatcher, **scheduler**, coordinator, fan-out owner, and join owner." A control-plane scheduler, not a cron. |
| **Removal risk** | **Low.** Naming risk is real — the two subsystems share a word and share nothing else. |
| **Removal trigger** | The slice introducing dispatch. |
| **Evidence** | `ADR-0011:45-47`; `cron/suggestions.py`, `cron/scripts/classify_items.py` (model-driven job selection). |

### 10. Communication channels — **REMOVE** (all but one narrow port)

| Field | Value |
|---|---|
| **Current responsibility** | `gateway/` — 92,964 LOC; 28 platform files (Signal, WhatsApp Cloud, QQ Bot, WeChat, Yuanbao, BlueBubbles/iMessage, MS Graph, webhooks, API server) plus Discord. |
| **Dependencies** | Delivery ledger, pairing, mirror, authz, kanban watchers. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | `DEC-RANEX-021` retains "CLI, TUI, loopback web, GitHub edge, and text-phone delivery port"; `DEC-RANEX-022` names Telegram as the **first adapter behind channel-neutral contracts**. One port, not a gateway. `DEC-RANEX-024` excludes the public dashboard. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. The delivery port is authorised but unbuilt; it needs its own slice. |
| **Evidence** | `ADR-0006:194-224`; `git ls-tree -r phase/2-runtime-bootstrap -- gateway/platforms` → 28 files. |

### 11. Remote-control features — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | Remote drive of the agent from phone, browser, dashboard or external editor: `tui_gateway/` (22,848 LOC), `acp_adapter/` (5,691), `web/` (139 files), `ui-tui/` (423), `dashboard_auth/` (12), `api_server.py`. |
| **Dependencies** | Websockets, HTTP, dashboard auth, cookies, ws tickets. |
| **Slice 1 depends on it?** | **No — and it is directly adverse.** |
| **Ranex replacement** | **None.** Each of these is an authority path into the agent from outside the repository. `SLICE-LANE-007` requires the opposite and enforces it with three failure-mode tests. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. Re-import trigger: any network listener in `src/ranex/`. |
| **Evidence** | Walking skeleton §9; `tests/security/test_repository_confinement.py`; `DEC-RANEX-024` (web binds to loopback). |

### 12. Personal-assistant functionality — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | `skills/` (70) + `optional-skills/` (81) across Apple, email, smart-home, social-media, media, note-taking, productivity, creative; `agent/pet/` (a virtual pet with image generation); voice, TTS, transcription, image/video generation registries. |
| **Dependencies** | Skill bundles, prompt preprocessing, provider registries. |
| **Slice 1 depends on it?** | **No.** |
| **Ranex replacement** | **None. This is Hermes-the-product, and Ranex is explicitly not it.** |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. |
| **Evidence** | `docs/HANDOFF.md:41-42` — Ranex is "derived from Hermes Agent, **stripped of its general-assistant and commercial surface**." `ADR-0011` excludes "Markdown skill" from the runtime boundary. |

### 13. Observability — **ADAPT** (interface only), Ranex journal **KEEP**

| Field | Value |
|---|---|
| **Current responsibility** | Operator telemetry, diagnostics, insights, and `trace_upload.py` — an off-machine upload path. |
| **Dependencies** | Logging, display, stream diagnostics. |
| **Slice 1 depends on it?** | **Yes — on the Ranex journal, not on Hermes.** Walking skeleton §12 requires one record per evaluation carrying subject digest, gate id, rule id, verdict, evidence considered, failure reason and `subject_lane`. |
| **Ranex replacement** | `src/ranex/…/sqlite/journal.py` (94 LOC), hash-chained and append-only. Built and executing. |
| **Removal risk** | **None** (Hermes absent). |
| **Removal trigger** | n/a. **Hard constraint:** no telemetry with an off-machine upload path may enter the foundation without an explicit decision — `trace_upload.py` shows how quietly that arrives. |
| **Evidence** | Walking skeleton §12 — *"Never recorded as fact: anything the evaluated party asserts about its own work."* That single sentence is why a log is not a substitute for a journal. |

### 14. Configuration — **REPLACE** (deferred)

| Field | Value |
|---|---|
| **Current responsibility** | Layered ambient configuration — env, dotfiles, user config, per-session overrides — read at many points in the call graph. |
| **Dependencies** | Everything that reads config, which is most of Hermes. |
| **Slice 1 depends on it?** | **No.** Slice 1 takes explicit CLI arguments: `--repository`, `--gate-catalog`, `--evidence`, `--approver`, `--journal`. No ambient source. |
| **Ranex replacement** | `ADR-0011`: "isolated assignment configuration/home and working directory, **no setting/skill/plugin/auto-memory sources**." |
| **Removal risk** | **Low**, but the *re-import* risk is the highest on this matrix. Configuration arrives one convenience default at a time and each addition is individually defensible. |
| **Removal trigger** | Any environment variable or config-file read in `src/ranex/` requires an explicit decision, because an ambient input to a verdict breaks `BC-4` reproducibility across machines. |
| **Evidence** | `ADR-0011:48-56` — ambient user configuration "cannot broaden the effective set." `src/ranex/cli/main.py` argument list. |

### 15. Authentication and secrets — **REMOVE** (confirm absent); repo hazard **KEEP TEMPORARILY**

| Field | Value |
|---|---|
| **Current responsibility** | Credential brokerage across Bitwarden, 1Password, arbitrary shell commands, pooled credentials, dashboard sessions, cookies, websocket tickets — ~20 modules. |
| **Dependencies** | External password managers, HTTP, SSL guards. |
| **Slice 1 depends on it?** | **No.** `BC-5`: removing model access changes no verdict. There is nothing to authenticate to. |
| **Ranex replacement** | Deferred to whichever slice first needs a provider credential. Until then, **absence is a proof asset**: it is what makes `BC-5` cheap to demonstrate. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | First worker-dispatch slice. |
| **Evidence** | `src/ranex/cli/main.py:1-8`; single declared dependency `PyYAML` in `pyproject.toml`. |
| **Separate live hazard — KEEP TEMPORARILY** | `refs/codex/**` — **15 refs**, two carrying **11 copyrighted PDF blobs**, in the object database of a repository whose `origin` is **public**. `git push --all` or `--mirror` publishes them. Not Hermes-derived; recorded here because it is the only unresolved secrets-class exposure. **Trigger:** owner decision; unresolved by choice. **Count with `git for-each-ref 'refs/codex/**'`** — the single-star glob returns 0 and reads as a false all-clear. **FACT**, re-measured 2026-07-31. |

### 16. Plugin and extension mechanisms — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | `plugins/` — 190 code files, 116,994 LOC. In-process extension supplying LLMs, cron providers, dashboard auth backends, and **verify-loop interception**. |
| **Dependencies** | Plugin loader, MCP, skill bundles. |
| **Slice 1 depends on it?** | **No.** Walking skeleton §5 lists plugins under explicit exclusions. |
| **Ranex replacement** | `DEC-RANEX-019` already fixed the shape: external extensions are "lower-trust **out-of-process** capability-scoped protocol **outside authority**." |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. **In-process extension of a gate is the gate's own bypass** — `verify_hooks.py` resolves directives through `hermes_cli.plugins.get_pre_verify_continue_message`, i.e. a plugin can steer the verification loop. |
| **Evidence** | `ADR-0006:178-184`; `phase/2-runtime-bootstrap:agent/verify_hooks.py:3-5`. |

### 17. Governance — **KEEP** (Ranex-original), Hermes approval modes **REMOVE**

| Field | Value |
|---|---|
| **Current responsibility** | Hermes: interactive approval modes, tool guardrails, computer-use permissions — advisory, configurable at runtime, inside a loop the model drives. Ranex: 21 ADRs, 47 generated contract registries, 196 schemas, 56,759 LOC of generator + validator. |
| **Dependencies** | Ranex governance depends on `jsonschema`, `PyYAML`, `rfc8785` (declared in `legal/licensing-manifest.json`) and git. |
| **Slice 1 depends on it?** | **Yes, heavily** — `ADR-0007` (layout), `ADR-0008` (TDD), `ADR-0014` (Python), `ADR-0015` (event schema), `ADR-0018` (pyrefly), `ADR-0019` (uv), and `ADR-0012` (which currently **blocks** it). |
| **Ranex replacement** | n/a — this **is** the product. |
| **Removal risk** | **High if disturbed.** This is the working Slice 0 kernel the brief requires preserved. Contract validation is `PASS` and the generator is idempotent. |
| **Removal trigger** | **None. Do not touch as part of foundation work.** |
| **Evidence** | `generate_contracts.py` + `validate_contracts.py` first added in `032adf368` as Ranex-authored work — **no Hermes lineage**. `docs/HANDOFF.md:53`. |

### 18. Evidence collection — **REPLACE** ⚠ **contaminating if adopted**

| Field | Value |
|---|---|
| **Current responsibility** | `agent/verification_evidence.py` — a SQLite ledger of what the agent proved while working. |
| **Dependencies** | `hermes_constants.get_hermes_home`, SQLite. |
| **Slice 1 depends on it?** | **No — and adopting it would silently defeat the slice.** |
| **Ranex replacement** | `src/ranex/governed_execution/domain/verdict.py` (207 LOC) + the hash-chained journal. `PR-03`/`ASR-02`/`BC-2`: **absence blocks**. |
| **Removal risk** | **None** (absent). **Adoption risk is the highest on this matrix** — see below. |
| **Removal trigger** | n/a. |
| **Evidence** | Module docstring, verbatim from `phase/2-runtime-bootstrap:agent/verification_evidence.py:1-6`: *"It is **deliberately passive: it never decides to run a suite, never blocks completion**, and never upgrades targeted checks into 'repo green'."* Ranex `BC-2`: a required claim with no evidence is `FAIL` — *"Never a default, never a skip."* |

> **Why this is the sharpest contamination risk in the audit.** The Hermes module
> and the Ranex requirement share a name (*evidence*), a storage engine
> (SQLite), and a record shape (command, exit code, output summary). They
> disagree on the only property that matters: whether absence blocks. A future
> agent looking for "the evidence ledger we already have" would find something
> that passes review, imports cleanly, and **cannot refuse anything**. It would
> not fail loudly; Slice 1 would simply always pass.

### 19. Deterministic validation — **KEEP** (Ranex-original; no Hermes counterpart)

| Field | Value |
|---|---|
| **Current responsibility** | Canonical JSON (RFC 8785) + SHA-256 subject binding, reproducible verdicts, contract validation. |
| **Dependencies** | `PyYAML` (product), `jsonschema`/`rfc8785` (validator), stdlib `hashlib`/`json`. |
| **Slice 1 depends on it?** | **Yes. It is the slice.** `BC-3` (exact-subject binding) and `BC-4` (byte-identical) are both this capability. |
| **Ranex replacement** | n/a — already the replacement. |
| **Removal risk** | **Total.** Remove it and there is no product. |
| **Removal trigger** | **None.** |
| **Evidence** | Searched `agent/`, `hermes_cli/`, `tools/`, `gateway/` for canonicalisation, RFC 8785, content-addressed subject binding and reproducible verdicts — **none found**. Nearest neighbours (`error_classifier.py`, `tool_result_classification.py`) classify model output heuristically. **This capability cannot be inherited or extracted. It exists only because it was written here.** |

### 20. Repair loops — **REMOVE** (confirm absent)

| Field | Value |
|---|---|
| **Current responsibility** | `verify_hooks.py` fires a `pre_verify` hook at round end; a directive "keeps the agent going one more turn," bounded by `DEFAULT_MAX_VERIFY_NUDGES = 3`. Plus retry utilities and reasoning-timeout guidance. |
| **Dependencies** | Conversation loop, plugins. |
| **Slice 1 depends on it?** | **No.** Slice 1 evaluates and exits. |
| **Ranex replacement** | **None, and none is wanted at this stage.** A repair loop belongs on the control plane, if anywhere. |
| **Removal risk** | **None** (absent). |
| **Removal trigger** | n/a. |
| **Evidence** | `phase/2-runtime-bootstrap:agent/verify_hooks.py:1-25` — the mechanism is guidance appended to a prompt. Same category error as row 18: prompt-level persuasion where the thesis requires control-plane enforcement. |

### 21. Multi-agent orchestration — **REPLACE** (deferred; authority already accepted)

| Field | Value |
|---|---|
| **Current responsibility** | Model-initiated delegation — `tools/delegate_tool.py` (3,939 LOC) is a **tool the model calls**; `moa_loop.py` (2,126) fans out and merges. Topology is model-authored at runtime. |
| **Dependencies** | Subagent lifecycle, auxiliary client, daemon pool, transports. |
| **Slice 1 depends on it?** | **No.** Walking skeleton §5 excludes "fleet, workers or dispatch." |
| **Ranex replacement** | `ADR-0011`, already `ACCEPTED`: Ranex compiles a deterministic bounded fan-out/join graph **before dispatch**; "model-generated decomposition is an **untrusted proposal**"; a worker "cannot create assignments, spawn or delegate to another model worker, coordinate a fleet, choose a successor, widen its role or tools, switch its model/route, approve its own output, or land a change." |
| **Removal risk** | **Low**, fully deferred. |
| **Removal trigger** | The slice that first dispatches more than one worker. `ADR-0011`'s qualification requirements (cold one-shot vs cold managed-client vs warm reuse, with named metrics and "no threshold invented before measurement") are that slice's acceptance criteria. |
| **Evidence** | `ADR-0011:31-44`. |

---

## Matrix — Hermes residue actually present in the tracked tree

These are the only rows requiring action or a watch. **FACT**, per-file scan of
`architecture/contracts/` and `git ls-files | grep -i hermes`.

| Artifact | Class | Slice 1 dep? | Trigger to close | Evidence |
|---|---|---|---|---|
| `architecture/contracts/hermes-research-promotions.json` — 65 `HERMES-PROMOTION-*` rows | **KEEP TEMPORARILY** | No | Each row closes when its obligation is either implemented or superseded by an accepted decision. `ADR-0013` v1.4.0 records four fidelity-audit rounds already. | 514 `hermes` matches; `ADR-0013` |
| `schemas/common/hermes-research-provision-v1.schema.json` | **KEEP TEMPORARILY** | No | Closes with the last promotion row. | Schema registry |
| `architecture/contracts/legacy-test-layout-policy{,-v1,-v2}.json` — 2,444 inherited test paths | **KEEP TEMPORARILY** | No | `ADR-0021` already narrowed `ADR-0010` to inherited lineage; **zero of 2,444 paths exist** in the working tree. Closes at `ADR-0010` expiry, **2026-10-31T23:59:59Z**. | `ADR-0010` header; `ADR-0021`; `LEGACY-TEST-RESOLUTION.md` |
| `architecture/contracts/legacy-test-lineage-applicability-v1.json` | **KEEP** | No | n/a — it is the narrowing record. | `ADR-0021` |
| Hermes provenance tags in `architecture-element{s,-assessments}.json`, `contexts.json`, `events.json`, `states.json`, `data-ownership.json`, `paths.json`, `vital-profile.json`, `effects.json`, `decisions.json` | **KEEP** | No | n/a — provenance is a fact about origin and stays true. | 1,088 / 1,094 / 76 / 49 / 45 / 35 / 36 / 30 / 6 / 5 matches |
| `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md`, `docs/research/hermes-core-architecture-*.md` | **KEEP** | No | n/a — reference material, correctly labelled. | Tracked docs |
| Git refs: `phase/*`, `upstream-sync`, `remotes/upstream/*` (`github.com/NousResearch/hermes-agent`) | **KEEP TEMPORARILY** | No | Retain while `DEC-RANEX-006` provenance obligations and `ADR-0013` rows are open. Not import-reachable. | `git remote -v`; `git branch -a` |
| `develop` branch — commit `0533e1eaf` reachable from **4 refs**, not one | **KEEP** ⚠ **load-bearing** | Indirectly — CI | **Never delete or force-push.** Both the `drift` and `validate` CI jobs read git objects from it. | `generate_contracts.py:4938,5140`; `validate_contracts.py:13841`; `docs/HANDOFF.md:144-147` |
| `/home/soultransit/devtony/ranex-worktree-archive-2026-07-31/` | **KEEP TEMPORARILY** | No | Outside the repository; retain until the last `HERMES-PROMOTION` row closes. | Filesystem, outside git |

---

## ADR review — classification of all 21 accepted ADRs

Classes as specified in the brief. **No accepted ADR is rewritten by this
document**; recommendations are recorded and nothing is enacted.

| ADR | Title (short) | Class | Slice 1 | Note |
|---|---|---|---|---|
| `ADR-0001` | Established SDLC governs AI work | **GOVERNANCE** | Indirect | — |
| `ADR-0002` | Retire legacy implementation guide | **GOVERNANCE** | No | Retirement record |
| `ADR-0003` | Target architecture and authority kernel | **RANEX FOUNDATION** | Indirect | ⚠ flagged below |
| `ADR-0004` | Quality-attribute baselines | **GOVERNANCE** | Indirect | — |
| `ADR-0005` | Local static orchestration defaults | **REQUIRES REVIEW** | No | Partly superseded by `ADR-0011` |
| `ADR-0006` | Fixed decisions + fitness crosswalk (29 `DEC-RANEX` rows) | **RANEX FOUNDATION** | Indirect | ⚠ flagged below |
| `ADR-0007` | Modular DDD repository organization | **RANEX FOUNDATION** | **Yes** | Governs `src/ranex/` layout |
| `ADR-0008` | TDD as default discipline | **GOVERNANCE** | **Yes** | Failing test first |
| `ADR-0009` | Boundary-fit deps and feedback fitness | **GOVERNANCE** | Indirect | — |
| `ADR-0010` | Bound inherited Hermes test layout | **HERMES-INHERITED** | No | ⚠ flagged below |
| `ADR-0011` | Centralize worker orchestration + runtime adapters | **PRODUCT / FUTURE-DEFERRED** | No | The replacement authority for rows 2,3,5,7,9,21 |
| `ADR-0012` | Separate implementation start / production readiness | **GOVERNANCE** | **Yes — blocking** | `:72` forbids product capability pre-`IMPLEMENTATION_START_READY` |
| `ADR-0013` | Promote Hermes research obligations (65 rows) | **HERMES-INHERITED** | No | ⚠ flagged below |
| `ADR-0014` | Implementation language + escape hatch | **RANEX FOUNDATION** | **Yes** | Python |
| `ADR-0015` | Canonical workflow/event schema + upcaster policy | **RANEX FOUNDATION** | **Partly** | ⚠ scope note below |
| `ADR-0016` | Resolve five implementation-start owner decisions | **GOVERNANCE** | Indirect | Carries `DESKTOP-EXCLUDED-001` |
| `ADR-0017` | Record resolved owner decisions | **GOVERNANCE** | Indirect | Implemented 2026-07-31, 11 cases pass |
| `ADR-0018` | Select the static type checker | **GOVERNANCE** | **Yes** | 243-error baseline; run from `scripts/architecture` |
| `ADR-0019` | Declare `uv` as toolchain manager | **GOVERNANCE** | **Yes** | — |
| `ADR-0020` | Record-freshness self-check | **GOVERNANCE** | No | Product form excluded from slice |
| `ADR-0021` | Limit `ADR-0010` to inherited lineage | **GOVERNANCE** | No | Did half this audit's work already |

### ADRs that assume a Hermes subsystem we plan to remove or replace

Four flags. Two are benign; two are substantive.

**⚠ 1 — `ADR-0010`: assumes an inherited test tree that this lineage does not
have.** Its entire subject is 2,444 tests in
`0533e1eaf50ace0eb84435a5c3de05e939fd4daa`. Executed: that commit is **not an
ancestor of `HEAD`** (`git merge-base --is-ancestor …; echo $?` → `1`), and
**zero of 2,444 baseline paths exist** in the working tree.
**Already handled — `ADR-0021` narrowed it to the inherited lineage on exactly
this evidence. No further action.**

**⚠ 2 — `ADR-0006` `DEC-RANEX-008`: "strangler migration inside the attributed
fork."** A strangler migration presumes a legacy system inside the tree to
strangle incrementally. **There is none at `HEAD`.** The same premise appears in
`DEC-RANEX-007` ("new authority/domain/application core has no inherited-Hermes
dependency" — now trivially satisfied rather than achieved through migration)
and in `ADR-0003`'s authority kernel, whose `HERMES-PROMOTION-002` describes a
kernel "built **beside** Hermes."

**This is the one genuinely stale architectural premise the audit found.** It is
not currently harmful: the decisions' *outcomes* are all satisfied, and more
cheaply than by the route they describe. It becomes harmful only if a future
slice reads "strangler migration" as an instruction to import Hermes code in
order to have something to strangle.

**Recommendation — deliberately minimal.** Do **not** write an ADR now. Record
the finding in these foundation documents (done), and if a slice ever collides
with the premise, supersede on the `ADR-0021` pattern: narrow the scope on
executed provenance evidence, without rewriting the accepted decision. Creating
a decision record for a premise nothing currently depends on would be the
speculative-ADR and BDUF behaviour the brief forbids.

**⚠ 3 — `ADR-0013`: 65 `HERMES-PROMOTION-*` obligations promoted from Hermes
research.** Some describe runtime obligations for subsystems classified
`REPLACE` above. This is **by design** — `ADR-0013`'s purpose is to make
already-accepted obligations line-auditable and fail closed, and its revision
history shows four fidelity-audit rounds removing unsupported qualifiers.
`HERMES-OWNER-DECISION-*` rows remain the real gate. **No action. Watch as rows
close.**

**⚠ 4 — `ADR-0005`: orchestration defaults.** `ADR-0011` explicitly supersedes
its "model/provider-routing fallback, worker-topology coordinator, and
model-controlled orchestration clauses." The supersession is recorded in
`ADR-0011`'s header. **Already handled. No action.**

### Scope note, not a flag

**`ADR-0015`** (canonical workflow/event schema and upcaster policy) is
`RANEX FOUNDATION` and Slice 1 depends on the canonical-schema half. The
walking skeleton §5 explicitly excludes "queues, event buses, upcasters." That
is a **slice scope boundary, not a conflict** — the ADR governs the shape of
events when they exist; Slice 1 has none yet.

### The ADR that actually blocks Slice 1

`ADR-0012:72` forbids product capability before `IMPLEMENTATION_START_READY`.
`RFC-0010` would authorise it and is not promoted, because promotion needs an
authenticated `HumanDecisionV1` and **nothing in this repository can mint one** —
the only construction of `authentication_context_id` /
`presentation_challenge_digest` is a synthetic fixture at
`validate_contracts.py:8507`.

**This is a governance block, not a foundation block, and this audit does not
lift it.** It is carried to
[`slice-1-readiness-assessment.md`](slice-1-readiness-assessment.md) §1 as the
single open condition.
