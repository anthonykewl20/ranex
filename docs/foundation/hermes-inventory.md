# Hermes subsystem inventory

**Date:** 2026-07-31 · **Branch:** `bootstrap/pre-upstream` · **HEAD:** `f2c04c167`

Every claim here is labelled. **FACT** = measured in this repository by the
command shown. **INFERENCE** = concluded but not directly proven.
**UNVERIFIED** = neither.

---

## 0. The finding that reframes this audit

**The working tree contains no Hermes runtime code. FACT.**

The audit was commissioned on the premise that "Ranex is being built from a
Hermes codebase." At `HEAD` that premise does not hold. Measured:

```console
$ cd /home/soultransit/devtony/ranex
$ for d in agent hermes_cli tools gateway cron plugins skills apps web \
           ui-tui acp_adapter tui_gateway; do
    echo "$d: $(git ls-tree -r HEAD --name-only -- $d | wc -l)"; done
agent: 0        hermes_cli: 0   tools: 0        gateway: 0
cron: 0         plugins: 0      skills: 0       apps: 0
web: 0          ui-tui: 0       acp_adapter: 0  tui_gateway: 0
```

And the Hermes baseline is not in this lineage's ancestry:

```console
$ git merge-base --is-ancestor 0533e1eaf50ace0eb84435a5c3de05e939fd4daa HEAD
$ echo $?
1                                   # 1 = NOT an ancestor
$ git merge-base --is-ancestor phase/2-runtime-bootstrap HEAD; echo $?
1
$ git rev-list --max-parents=0 HEAD
4ee007fcbe40b1afa7c362767005cf2f4508fc3d
$ git rev-list --count HEAD
38
```

This lineage is 38 commits deep from an unrelated root. `ADR-0021` already
established this fact for the 2,444-file inherited **test** tree. **This audit
extends the same executed finding to the entire Hermes runtime.**

Hermes survives in this repository in exactly three forms, all of which are
inert with respect to the Python import graph:

| Form | Where | Reachable by `import`? |
|---|---|---|
| Git refs | `phase/*`, `upstream-sync`, `remotes/upstream/*` (Hermes remote at `github.com/NousResearch/hermes-agent`) | **No** |
| Filesystem archive | `/home/soultransit/devtony/ranex-worktree-archive-2026-07-31/` — outside the repository | **No** |
| Contract and document residue | 23 files under `architecture/contracts/`, 10 tracked paths matching `hermes` | **No** — data and prose, not code |

Everything below therefore inventories a corpus that must be **not imported**,
rather than one that must be dismantled. That is a materially cheaper problem,
and it is the single most consequential input to the Slice 1 readiness verdict.

---

## 1. Scale of the corpus not in the tree

Reference tree used throughout: `phase/2-runtime-bootstrap` — the Ranex fork
point with the Hermes runtime intact. **FACT**, all figures measured with
`git ls-tree -r phase/2-runtime-bootstrap` and `git show … | wc -l`.

| Subsystem | Files | Python LOC |
|---|---:|---:|
| `hermes_cli/` | 224 | 188,972 |
| `plugins/` | 190 | 116,994 |
| `agent/` | 165 | 116,701 |
| `tools/` | 119 | 103,278 |
| `gateway/` | 80 | 92,964 |
| `tui_gateway/` | 16 | 22,848 |
| `cron/` | 11 | 8,938 |
| `acp_adapter/` | 11 | 5,691 |
| `providers/` | 2 | 423 |
| **Python subtotal** | **818** | **656,809** |

Non-Python surfaces, by code-file count: `apps/` 1,201 · `ui-tui/` 423 ·
`plugins/` (JS/TS portion, counted above by file) · `web/` 139 ·
`optional-skills/` 81 · `skills/` 70 · `website/` 9 · `tests/` 2,436.
Whole tree: **7,671 files**.

Largest single modules, LOC:

| File | LOC | Role |
|---|---:|---|
| `cli.py` | 17,241 | Monolithic entrypoint |
| `run_agent.py` | 7,106 | Agent bootstrap and run |
| `agent/conversation_loop.py` | 6,763 | The agent loop |
| `tools/delegate_tool.py` | 3,939 | Model-initiated delegation |
| `agent/moa_loop.py` | 2,126 | Mixture-of-agents loop |
| `agent/prompt_builder.py` | 2,090 | Prompt assembly |
| `agent/tool_executor.py` | 1,852 | Tool dispatch |
| `agent/memory_manager.py` | 1,241 | Cross-session memory |
| `toolsets.py` | 975 | Tool surface composition |

For comparison, the entire Ranex product source at `HEAD` is **1,050 lines**
across 30 files (most of them `__init__.py`), with **573 lines** of tests.
**FACT**, `find src tests -name '*.py' -not -path '*__pycache__*' | xargs wc -l`.

The ratio is roughly **625 : 1**. Any decision framed as "trim Hermes down to
Ranex" is the wrong shape; the tree already reflects the opposite decision,
taken earlier and never written down as an inventory. This document is that
missing record.

---

## 2. Subsystem-by-subsystem inventory

Each entry states the subsystem's responsibility **in Hermes**, its
dependencies, and the evidence located. Classification, Slice 1 dependency,
replacement, removal risk and trigger are carried in
[`hermes-retention-matrix.md`](hermes-retention-matrix.md) so that each fact
appears once.

### 2.1 CLI and entrypoints

`cli.py` (17,241 LOC) · `hermes_cli/` (224 files, 188,972 LOC) ·
`run_agent.py` · `batch_runner.py` · `mini_swe_runner.py` ·
`hermes_bootstrap.py` (239) · `setup.py` · `setup-hermes.sh`

A single monolithic argument parser fronting the whole product: sessions,
billing, auth, dashboards, checkpoints, backups, container boot, shell
completion, clipboard, banners. `hermes_cli/` carries mixins
(`cli_agent_setup_mixin.py`, `cli_billing_mixin.py`, `cli_commands_mixin.py`)
that couple the entrypoint to inference, billing and orchestration in the same
call graph.

**Dependencies:** effectively everything. `agent/`, `tools/`, `gateway/`,
`cron/`, `plugins/`, credential and billing subsystems.

**Ranex equivalent at HEAD:** `src/ranex/cli/main.py`, 1 subcommand, no model
reachable. Its module docstring states the property directly: *"No model is
reachable from here. Removing every credential on the machine changes no
verdict."*

### 2.2 Model-provider abstraction

`agent/transports/` (anthropic, bedrock, chat_completions, codex,
codex_app_server, codex_event_projector, `hermes_tools_mcp_server`, base,
types) · `agent/anthropic_adapter.py`, `bedrock_adapter.py`, `vertex_adapter.py`,
`gemini_native_adapter.py`, `codex_responses_adapter.py`,
`azure_identity_adapter.py` · `providers/base.py` · `model_tools.py` ·
`models_dev.py` · `agent/model_metadata.py` · `agent/usage_pricing.py` ·
`agent/credits_tracker.py` · `agent/rate_limit_tracker.py` ·
`agent/nous_rate_guard.py`

Multi-provider routing with fallback, auxiliary-model calls, credit accounting
and commercial entitlement checks against the Nous Portal.

**Governing Ranex decision already accepted:** `ADR-0011` requires *one*
explicit provider/model/transport/adapter/route per assignment, with **adapter,
provider, model and auxiliary fallback all disabled** — a typed failure returned
to Ranex instead. `DEC-RANEX-026` (`ADR-0006:234`) records Hermes/Nous as
"provenance, compatibility, and reference only: no live inference, parent-agent
model loop, Portal/model route, credential/entitlement, billing, credits,
subscription, managed tool pool, purchase, promotion, or fallback."

The Hermes abstraction's central feature — routing flexibility — is the exact
property Ranex has decided to forbid. **INFERENCE:** adopting it would require
removing more of it than remains.

### 2.3 Agent execution loop

`agent/conversation_loop.py` (6,763) · `run_agent.py` (7,106) ·
`agent/oneshot.py` · `agent/moa_loop.py` (2,126) · `agent/turn_context.py` ·
`agent/turn_finalizer.py` · `agent/turn_retry_state.py` ·
`agent/iteration_budget.py` · `agent/bounded_response.py`

The model-driven turn loop: the model decides what to call, when to stop, when
to retry, when to compress. `agent/kanban_stop.py` and
`agent/verification_stop.py` are *nudges* into that loop, not gates on it.

**Ranex position:** `ADR-0011` states the target explicitly — *"The target does
not put a Hermes `AIAgent`, Nous model, Markdown skill, model-authored shell
command, PTY, terminal scraper, or `tmux` keystroke loop between the Ranex
scheduler and a worker."*

### 2.4 Prompt handling

`agent/prompt_builder.py` (2,090) · `agent/system_prompt.py` (614) ·
`agent/prompt_caching.py` · `agent/skill_preprocessing.py` ·
`agent/learn_prompt.py` · `agent/message_content.py` ·
`agent/message_sanitization.py` · `agent/think_scrubber.py` ·
`agent/redact.py`

Assembles system prompt, skills, memory, coding context and subdirectory hints
into the model call. This is where Hermes encodes behaviour that Ranex has
decided must live in checking code instead — the product thesis at
`docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md:20`:
*"rules compiled into code change what an agent produces; rules in a prompt do
not."*

### 2.5 Tool execution

`agent/tool_executor.py` (1,852) · `agent/tool_dispatch_helpers.py` ·
`agent/tool_guardrails.py` · `agent/tool_result_classification.py` ·
`toolsets.py` (975) · `toolset_distributions.py` · `tools/approval.py` ·
`tools/permissions*`

Dispatches model-requested tool calls with an approval mode and guardrails.
Approval is interactive/advisory and configurable at runtime by the user or by a
plugin.

**Contrast with `ADR-0011`:** each role owns an immutable maximum capability
envelope; each assignment compiles a *task-minimal subset*; **empty is the
default**; and "a prompt, provider allow-list, prior session, ambient user
configuration, or worker request cannot broaden the effective set."

### 2.6 Terminal and filesystem access

`tools/` terminal, PTY and `tmux` surfaces · `tools/close_terminal_tool.py` ·
`tools/code_execution_tool.py` · `agent/file_safety.py` ·
`agent/runtime_cwd.py` · `agent/shell_hooks.py` ·
`tools/computer_use/` (8 files) · `tools/desktop_ui.py` ·
`tools/browser_*.py` (6 files)

Model-authored shell, screen scraping and full desktop/browser control.

**Explicitly excluded by `ADR-0011`:** shell/PTY/tmux "may appear only in
diagnostic or compatibility evidence outside the qualified product hot path;
they cannot be an active runtime adapter."

**Ranex equivalent at HEAD:** `src/ranex/cli/confinement.py` (44 lines) — ⚠ **written but not wired into `cli/main.py`; see readiness assessment G6.** In intent, the
*opposite* discipline. It refuses absolute paths, traversal above the repository
root, and remote targets.

### 2.7 Task lifecycle

`agent/subagent_lifecycle.py` (533) · `agent/turn_finalizer.py` ·
`agent/turn_summary.py` · `agent/kanban_stop.py` ·
`hermes_cli/checkpoints.py` · `hermes_cli/active_sessions.py` ·
`tools/checkpoint_manager.py`

Session and subagent lifecycle keyed to conversation turns. Completion is
asserted by the agent and recorded; there is no independent authority that can
refuse the assertion.

**Ranex position:** `DEC-RANEX-009` — `work_management` alone owns
`WorkItemStatus`; `KANBAN-PROJECTION-001` (`ADR-0016`) makes boards a
*disposable, rebuildable projection*, never a completion authority.

### 2.8 Context and memory

`agent/context_engine.py` (489) · `agent/context_compressor.py` ·
`agent/context_breakdown.py` · `agent/context_references.py` ·
`agent/conversation_compression.py` · `agent/manual_compression_feedback.py` ·
`trajectory_compressor.py` · `agent/memory_manager.py` (1,241) ·
`agent/memory_provider.py` · `agent/learning_graph.py` ·
`agent/learning_mutations.py` · `agent/curator.py`

Lossy summarisation of conversation history, plus a mutating cross-session
learning graph.

**Direct conflict with Slice 1's determinism contract.** `BC-4` requires
byte-identical output from identical inputs. A lossy compressor whose behaviour
depends on accumulated history is, by construction, a hidden input. **INFERENCE**
— stated as a structural property, not measured against a running Hermes.

### 2.9 Scheduling

`cron/` — 11 files, 8,938 LOC: `scheduler.py`, `scheduler_provider.py`,
`jobs.py`, `executions.py`, `lifecycle_guard.py`, `blueprint_catalog.py`,
`suggestions.py`, `suggestion_catalog.py`, `scripts/classify_items.py` ·
`tools/cronjob_tools.py` · `plugins/cron_providers/chronos/`

Recurring background jobs, including model-suggested and model-classified ones
(`suggestions.py`, `classify_items.py`).

Ranex's scheduler is a **control-plane** component under `ADR-0011` ("Ranex
control services are the sole orchestrator, dispatcher, scheduler, coordinator,
fan-out owner, and join owner"). Hermes's is a personal-automation cron. Same
word, different responsibility.

### 2.10 Communication channels

`gateway/` — 80 files, 92,964 LOC. `gateway/platforms/` carries 28 files:
Signal (3), WhatsApp Cloud (2), QQ Bot (7), WeChat (`weixin.py`), Yuanbao (4),
BlueBubbles/iMessage, MS Graph webhook, generic webhook + filters, API server.
Plus `delivery.py`, `delivery_ledger.py`, `pairing.py`, `mirror.py`,
`channel_directory.py`, `kanban_watchers.py`, `drain_control.py`,
`authz_mixin.py` · `tools/discord_tool.py`

Inbound and outbound consumer messaging — the personal-assistant surface.

`DEC-RANEX-021` retains "CLI, TUI, loopback web, GitHub edge, and text-phone
delivery port"; `DEC-RANEX-022` names Telegram as first adapter behind
channel-neutral contracts. So Ranex keeps **one narrow delivery port**, not a
28-platform gateway. `DEC-RANEX-024` excludes the public dashboard; web binds to
loopback.

### 2.11 Remote-control features

`tui_gateway/` (16 files, 22,848 LOC) · `acp_adapter/` (11 files, 5,691 LOC) ·
`web/` (139 code files) · `ui-tui/` (423) · `website/` (9) ·
`hermes_cli/dashboard_auth/` (12 files) ·
`gateway/platforms/api_server.py` · `hermes_cli/browser_connect.py` ·
`hermes_cli/claw.py`

Remote drive of the agent from a phone, browser, dashboard or external editor
over websockets and an HTTP API.

Every one of these is an authority path into the agent from outside the
repository. Slice 1's `SLICE-LANE-007` requires the opposite property — that the
tool governs *only this repository* — and enforces it with three tests
(absolute path, traversal, remote target).

### 2.12 Personal-assistant functionality

`skills/` (70 code files) across `apple`, `email`, `smart-home`,
`social-media`, `media`, `note-taking`, `productivity`, `creative`,
`github`, `research`, `mlops`, `software-development`,
`autonomous-ai-agents`, `index-cache` · `optional-skills/` (81) ·
`agent/pet/` (11 files — a virtual pet with image generation) ·
`tools/voice_mode.py`, `tts_tool.py`, `tts_streaming.py`,
`neutts_synth.py` · `agent/tts_*`, `transcription_*`, `image_gen_*`,
`video_gen_*`, `web_search_*` registries · `agent/reactions.py` ·
`agent/insights.py` · `plugins/google_meet/`

This is Hermes-the-product: a general personal assistant. `docs/HANDOFF.md:41`
already records the intent — Ranex is "derived from Hermes Agent, stripped of
its general-assistant and commercial surface."

None of it is in the tree. Nothing needs stripping; it needs **not importing**.

### 2.13 Observability

`hermes_logging.py` · `agent/moa_trace.py` · `agent/trace_upload.py` ·
`agent/stream_diag.py` · `agent/insights.py` · `agent/display.py` ·
`agent/thread_scoped_output.py` · `agent/lsp/eventlog.py` ·
`gateway/memory_monitor.py` · `agent/battery.py`

Human-facing operator telemetry and diagnostics, with an upload path.
`trace_upload.py` sends trajectories off-machine.

**Ranex's observability requirement is different in kind.** Walking skeleton
§12: every evaluation appends one record carrying subject digest, gate id, rule
id, verdict, evidence considered, failure reason and `subject_lane` — and
*"Never recorded as fact: anything the evaluated party asserts about its own
work."* That is an audit record, not a log. `src/ranex/…/sqlite/journal.py`
(94 lines) implements it as a hash-chained append-only journal.

### 2.14 Configuration

`hermes_cli/config.py` · `hermes_cli/fallback_config.py` ·
`cli-config.yaml.example` · `.env.example` · `agent/agent_init.py` ·
`agent/process_bootstrap.py` · `tools/budget_config.py`

Layered ambient configuration — env, dotfiles, user config, per-session
overrides — read at many points in the call graph.

`ADR-0011` forbids exactly this influence path: "ambient user configuration …
cannot broaden the effective set," and requires "isolated assignment
configuration/home and working directory, no setting/skill/plugin/auto-memory
sources."

### 2.15 Authentication and secrets

`agent/secret_sources/` — `bitwarden.py`, `onepassword.py`, `command.py`,
`registry.py`, `base.py`, `_cache.py` · `agent/secret_scope.py` ·
`agent/credential_persistence.py`, `credential_pool.py`,
`credential_sources.py` · `tools/credential_files.py` ·
`hermes_cli/auth.py`, `auth_commands.py`, `copilot_auth.py`,
`credential_lifecycle.py`, `dingtalk_auth.py`, `azure_detect.py` ·
`hermes_cli/dashboard_auth/` (12 files) · `agent/ssl_guard.py`,
`ssl_verify.py`

Broad credential brokerage: external password managers, arbitrary shell command
sources, pooled credentials, dashboard sessions, cookies, websocket tickets.

**Slice 1 needs none of it.** The verdict must not change when every credential
on the machine is removed (`BC-5`). Importing a credential broker into the
foundation would make that contract harder to prove, not easier.

**Standing hazard, unrelated to Hermes but in the same object database:**
`refs/codex/**` — **15 refs re-measured 2026-07-31**, two carrying 11
copyrighted PDF blobs. `origin` is a **public** GitHub repository.
`git push --all` or `--mirror` would publish them. **FACT.** Count with
`git for-each-ref 'refs/codex/**'` — the single-star glob returns 0 and reads as
a false all-clear.

### 2.16 Plugin and extension mechanisms

`plugins/` — 190 code files, 116,994 LOC: `browser/` (browser_use,
browserbase, firecrawl), `cron_providers/chronos/`, `dashboard_auth/` (4),
`google_meet/`, `disk-cleanup/`, `context_engine/` · `optional-mcps/` ·
`mcp_serve.py` · `agent/plugin_llm.py` · `agent/skill_bundles.py`,
`skill_commands.py`, `skill_utils.py` · `hermes_cli/plugins`

In-process extension: a plugin can supply an LLM, a cron provider, a dashboard
auth backend, or intercept the verify loop (`verify_hooks.py` resolves
directives via `hermes_cli.plugins.get_pre_verify_continue_message`).

**In-process extension of a gate is the gate's own bypass.** `DEC-RANEX-019`
already decided the shape: external extensions are "lower-trust **out-of-process**
capability-scoped protocol **outside authority**." The walking skeleton §5 lists
plugins under explicit exclusions.

### 2.17 Governance

Hermes has approval modes (`hermes_cli/approval_mode.py`,
`approvals_suggest.py`), tool guardrails, and computer-use permissions
(`tools/computer_use/permissions.py`).

All are **advisory and interactive**: they prompt a human, or apply a
configurable allow-list, in a loop the model drives. None is a deterministic
authority that can refuse an outcome on recorded evidence.

**Ranex's governance is the product.** It is original: `ADR-0001`–`ADR-0021`,
`architecture/contracts/` (47 generated registries), `schemas/` (196 JSON
schemas), and `scripts/architecture/` (56,759 LOC). **No part of it is
Hermes-derived** — `generate_contracts.py` and `validate_contracts.py` were
added in `032adf368` as Ranex-authored work.

### 2.18 Evidence collection

`agent/verification_evidence.py` — a SQLite ledger of what the agent proved
while working.

**This is the most instructive entry in the inventory, and the clearest
"contaminating" component.** Its own module docstring states its design:

> "This module records what the agent actually proved while working in a code
> workspace. **It is deliberately passive: it never decides to run a suite,
> never blocks completion,** and never upgrades targeted checks into 'repo
> green'."

Ranex's foundational rule is the exact negation. `PR-03`/`ASR-02`: **absence
blocks**. `BC-2`: a required claim with no evidence is `FAIL` — *"Never a
default, never a skip."*

The two share a name and a storage engine and disagree on the only thing that
matters. Adopting the Hermes ledger would give Slice 1 something that looks like
an evidence store, passes casual review, and cannot refuse anything. **FACT**
(the docstring is quoted verbatim from
`phase/2-runtime-bootstrap:agent/verification_evidence.py:1-6`).

### 2.19 Deterministic validation

**Hermes has no counterpart.** Searched `agent/`, `hermes_cli/`, `tools/`,
`gateway/` for canonicalisation, RFC 8785, content-addressed subject binding and
reproducible verdicts; found none. Nearest neighbours are
`agent/error_classifier.py` and `tool_result_classification.py`, which classify
model output heuristically.

Ranex's is original and present at `HEAD`:
`src/ranex/foundation/canonical.py` (26 lines, "stable compact JSON suitable for
hashing kernel records"), `governed_execution/domain/verdict.py` (207 lines,
"Deterministic gate evaluation"), and the 56,759-line contract validator.

**This is the one capability Ranex must have and Hermes never had. It cannot be
inherited, adapted or extracted. It exists only because it was written here.**

### 2.20 Repair loops

`agent/verify_hooks.py` · `agent/verification_stop.py` ·
`agent/retry_utils.py` · `agent/turn_retry_state.py` ·
`agent/error_classifier.py` · `agent/reasoning_timeouts.py` ·
`agent/thinking_timeout_guidance.py`

`verify_hooks.py` documents its mechanism: a `pre_verify` hook fires at round
end and a directive "keeps the agent going one more turn," bounded by
`DEFAULT_MAX_VERIFY_NUDGES = 3`. It is a **nudge**: guidance appended to a prompt.

The same category error as §2.18 — a prompt-level persuasion mechanism where
Ranex requires a control-plane one. Slice 1 has no repair loop and needs none.

### 2.21 Multi-agent orchestration

`tools/delegate_tool.py` (3,939) · `tools/async_delegation.py` ·
`tools/delegation_live_log.py` · `agent/delegation_context.py` ·
`agent/subagent_lifecycle.py` (533) · `agent/moa_loop.py` (2,126) ·
`agent/background_review.py` · `agent/auxiliary_client.py` ·
`tools/daemon_pool.py`

**The model decides to delegate.** `delegate_tool.py` is a tool the model calls;
`moa_loop.py` fans out to several models and merges. Topology is model-authored
at runtime.

`ADR-0011` inverts every load-bearing property: Ranex "compiles a deterministic,
bounded fan-out/join graph **before dispatch**"; "model-generated decomposition
is an **untrusted proposal**"; a worker "cannot create assignments, spawn or
delegate to another model worker, coordinate a fleet, choose a successor, widen
its role or tools, switch its model/route, approve its own output, or land a
change"; and "a provider's built-in subagent, team, delegation, advisor,
fallback, or auxiliary-model facility is **disabled**."

`ADR-0011` is, in effect, the already-accepted decision to replace this
subsystem in full. It is not on Slice 1's path — the walking skeleton §5
excludes "fleet, workers or dispatch."

---

## 3. Hermes residue that *is* in the tracked tree

These are the only Hermes-derived artifacts Slice 1 could actually collide with.
**FACT**, `git ls-files | grep -i hermes` and a per-file scan of
`architecture/contracts/`.

| Path | Nature | Size |
|---|---|---|
| `architecture/contracts/hermes-research-promotions.json` | 65 `HERMES-PROMOTION-*` obligation rows | 514 `hermes` matches |
| `architecture/contracts/legacy-test-layout-policy{,-v1,-v2}.json` | `ADR-0010` projection — 2,444 inherited test paths | 545 matches each |
| `architecture/contracts/architecture-element{s,-assessments}.json` | Elements tagged with Hermes provenance | 1,088 / 1,094 |
| `architecture/contracts/contexts.json`, `states.json`, `events.json`, `data-ownership.json`, `paths.json`, `vital-profile.json`, `effects.json`, `decisions.json` | Scattered provenance references | 76 / 45 / 49 / 35 / 36 / 30 / 6 / 5 |
| `architecture/contracts/legacy-test-lineage-applicability-v1.json` | `ADR-0021` lineage narrowing | 1 |
| `schemas/common/hermes-research-provision-v1.schema.json` | Schema for the 65 rows | — |
| `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` | Reference architecture map | — |
| `docs/research/hermes-core-architecture-{research,hy3-review}-2026-07-27.md` | Research inputs | — |
| `docs/architecture/decisions/ADR-0010`, `ADR-0013` | Accepted decisions about Hermes | 1,804 / 1,152 lines |
| `docs/architecture/reviews/2026-07-{28,29}-*.md` | Runtime acceptance and reconciliation reviews | — |

**None is executable. None is on Slice 1's import path.** The 2,444-path
`ADR-0010` projection describes files that do not exist in the working tree —
`ADR-0021` measured **zero of 2,444** present.

---

## 4. What the Ranex foundation actually consists of

**FACT**, measured at `HEAD`.

| Layer | Location | Size | Origin |
|---|---|---:|---|
| Product source | `src/ranex/` | 1,050 LOC, 30 files | Ranex-original |
| Product tests | `tests/` | 573 LOC, 5 files, **36 passing in 0.18 s** | Ranex-original |
| Contract generator | `scripts/architecture/generate_contracts.py` | 23,224 LOC | Ranex-original |
| Contract validator | `scripts/architecture/validate_contracts.py` | 32,860 LOC | Ranex-original |
| Freshness / lock / tests | `scripts/architecture/*.py` | 675 LOC | Ranex-original |
| Schemas | `schemas/` | 196 JSON | Ranex-original |
| Generated contracts | `architecture/contracts/` | 47 registries | Generated |
| Decisions | `docs/architecture/decisions/` | 21 accepted ADRs | Ranex-original |
| Third-party runtime deps | `pyproject.toml` | **1** — `PyYAML>=6.0.2,<7` | — |

The complete import surface of the Ranex product source, **FACT**
(`grep -rh '^import \|^from ' src/ranex`):

```
stdlib:  argparse, dataclasses, enum, hashlib, json, pathlib, re,
         sqlite3, subprocess, sys, typing, uuid
third-party: yaml (PyYAML)
first-party: ranex.*
```

**Zero Hermes imports. Zero Hermes packages. One third-party dependency.**

---

## 5. Executed behaviour of the current foundation

Run from `/home/soultransit/devtony/ranex` on 2026-07-31 at `f2c04c167`.
**FACT.**

```console
$ .venv/bin/python -m pytest -q
36 passed in 0.18s

$ PYTHONPATH=src .venv/bin/python -m ranex.cli.main gate evaluate HEAD \
    --repository . --gate-catalog governance/gates.yaml \
    --evidence governance/evidence.json --approver owner
PASS  gate=landing  subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
exit=0

# absence blocks — BC-2
$ echo '[]' > /tmp/empty-evidence.json
$ PYTHONPATH=src .venv/bin/python -m ranex.cli.main gate evaluate HEAD \
    --repository . --gate-catalog governance/gates.yaml \
    --evidence /tmp/empty-evidence.json --approver owner
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: contracts-validated, tests-executed
      subject=sha256:9edd77be…
exit=1

# self-approval refused — BC-6
$ … --approver <the producer_id from evidence.json>
FAIL  gate=landing  rule=TESTS_EXECUTED
      self-approval refused: worker produced evidence and approved it
exit=1

# determinism — BC-4
$ … > r1.txt ; … > r2.txt ; cmp r1.txt r2.txt
IDENTICAL
```

**The walking skeleton runs.** `BC-2` (absence blocks), `BC-4` (byte-identical
across runs) and `BC-6` (self-approval refused) are demonstrated at the CLI
boundary, not merely unit-tested.

**Caveat on completeness — do not read this as slice acceptance.** These four
commands demonstrate three of seven behavioural contracts end-to-end. `BC-1`,
`BC-3`, `BC-5` and `BC-7` and the twelve failure modes are covered by the 36
tests but were not separately re-executed at the CLI boundary in this audit, and
acceptance criterion 2 — *blocking a real change, recorded* — has not been
demonstrated against a change anyone actually wanted to land. Slice 1 is
**working**, not **accepted**.

**Side effects of this audit: none.** An earlier draft of this document stated
that the runs above appended rows to `governance/journal.sqlite3`. **That was
wrong, and the correction is itself a finding.** `--journal` defaults to `None`
(`src/ranex/cli/main.py:69,115`) and was not passed, so **nothing was written**.
Verified: the journal holds **2 rows**, both pre-existing `FAIL` records, and its
mtime is `2026-07-31 17:42:37` — hours before these runs.

Which exposes a gap against the slice's own requirement. Walking skeleton §12:
*"Each evaluation appends one record."* The code appends a record **only when
`--journal` is supplied**. Four evaluations were executed above and the audit
trail records none of them.

Three further gaps, measured while checking that one:

| Requirement | State | Evidence |
|---|---|---|
| §12 — every evaluation appends a record | **Opt-in, not automatic** | `--journal` defaults to `None` |
| §13 — every record carries `subject_lane: PRE_READINESS_PRODUCT_SLICE` | **Field absent** | Record keys are exactly `approver_id, considered, failing_rule, gate_id, missing_claims, reason, subject_digest, verdict` |
| Reproducible verdict | **Policy not bound** | No catalog or gate digest in the record. The subject is digest-bound; the *rules that judged it* are not |
| Gate catalog under version control | **Untracked** | `git ls-files governance/` → **0**; `git status --porcelain governance/` → `?? governance/` |

Together these mean: `governance/gates.yaml` can be edited invisibly to git, the
same subject can then yield a different verdict, and the journal — if written at
all — records `gate_id: landing` in both cases with no way to tell them apart.

**This is a Slice 1 completion gap, not a Hermes contamination issue.** It is
carried into
[`slice-1-readiness-assessment.md`](slice-1-readiness-assessment.md) §4 as
required work, and it does not change the verdict on whether the *foundation* is
safe.

---

## 6. What this inventory did not examine

Stated so that a later reader does not mistake silence for absence — the
handoff's own corollary, that a negative result is evidence about the search.

- **Hermes runtime behaviour was not executed.** All Hermes claims are read from
  source at `phase/2-runtime-bootstrap`. Where a claim concerns behaviour rather
  than structure it is marked **INFERENCE**.
- **`tests/` (2,436 code files) was counted, not read.** `ADR-0010` and
  `ADR-0021` already govern it and it is absent from this lineage.
- **`apps/`, `ui-tui/`, `web/`, `website/` were counted, not read.** All fall
  under `DEC-RANEX-020` (desktop excluded) and `DEC-RANEX-024` (public dashboard
  excluded), both already accepted.
- **The 65 `HERMES-PROMOTION-*` rows were counted, not individually
  re-adjudicated** against their research sources. `ADR-0013` v1.4.0 records
  four prior fidelity-audit rounds; a fifth was out of scope here.
- **`remotes/upstream/*` was not swept.** The Hermes upstream carries many
  branches; only the fork point was inventoried.
