# Claude Runtime, Hermes, and OpenCode HY3 Reconciliation

| Field | Value |
|---|---|
| Record ID | `REVIEW-RUNTIME-RECONCILIATION-2026-07-29` |
| Version | `1.0.0` |
| Status | `COMPLETE_ADVISORY_RECONCILIATION`; runtime and performance remain `NOT_ASSESSED` |
| Date | 2026-07-29 |
| Owner | Human owner |
| Architecture decision | [ADR-0011](../decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md) |
| Hermes source subject | `NousResearch/hermes-agent@f228e145ba35cbbf785eded2021ae6682285b91b` (2026-07-28) |
| OpenCode reviewer | OpenCode `1.18.8`, `openrouter/tencent/hy3`, high variant, plan agent |
| Input note digests | Web-GPT note A `sha256:8c2960b8fdd1ca7a7e646d2724b1b599618a52d83e6432cff8884623182b8495`; Web-GPT note B `sha256:0da8e78c53ae780c1641893369b95390924d1bf18296a0697b09d00afc8c9905` |
| Mutations | This reconciliation and the linked normative architecture/ADR updates; no product runtime or provider configuration was changed |
| Security/data class | Public synthesis; prompts, local configuration, auth state, and reviewer transcripts remain separately classified |

## Question and method

The user asked whether Hermes normally uses official Claude Code for Claude
Pro/Max, whether that matches the proposed Ranex adapter, whether Hermes has a
separate native Anthropic/OAuth route, and how the result should change a
performance-focused architecture where Ranex retains all orchestration.

The review:

1. read both user-supplied Web-GPT notes;
2. fetched the current Hermes upstream and pinned every source claim to commit
   `f228e145ba35cbbf785eded2021ae6682285b91b`;
3. checked current Anthropic and OpenAI primary documentation;
4. ran a two-round adversarial review through OpenCode HY3: initial critique,
   primary-source rebuttal, then revised verdict;
5. separated source fact, vendor policy, inference, owner decision, and unknown;
   and
6. converted the accepted owner decision into ADR-0011 rather than treating a
   model verdict as authority.

No reviewer was trusted as a fact source. Each material technical correction
below resolves to current official documentation or pinned source. Performance
recommendations remain hypotheses until Ranex benchmarks them.

## Verdict

The original statement is **substantially correct only when narrowed to the
Hermes Claude Code skill**:

> When Hermes' optional Claude Code skill is selected, its preferred
> one-shot path asks the parent Hermes model to issue a terminal call to the
> official `claude -p` runtime. This uses the same official Claude execution
> boundary proposed for Ranex, but not the same orchestration or enforcement
> quality.

The unqualified statement “For Claude Pro/Max, Hermes normally calls Claude
Code” is false or at least materially misleading:

- Hermes documentation calls Nous Portal the recommended general Hermes
  inference path, not Claude Code.
- The Claude Code behavior is an optional Markdown skill executed by a parent
  Hermes `AIAgent`.
- Hermes also has a native Anthropic Messages API adapter that can resolve
  Claude Code-derived credentials; that path does not run the official Claude
  Code harness.
- CLI authentication is not exclusively Pro/Max: the skill also documents API
  key, Console, and Enterprise SSO routes.

The owner-selected Ranex target is therefore not “copy the Hermes skill.” It is:

```text
Ranex sole cross-worker/control-plane orchestrator
  -> typed role-scoped WorkerRuntime adapter
  -> official Agent SDK/runtime
  -> one bounded leaf worker
  -> correlated structured events/result
```

## Pinned Hermes source facts

### Claude Code skill

The pinned
[Claude Code skill prerequisites and two modes](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/skills/autonomous-ai-agents/claude-code/SKILL.md#L18-L79)
establish:

- Claude Code must be installed.
- Auth may be Pro/Max browser OAuth, `ANTHROPIC_API_KEY`, Console login, or
  Enterprise SSO.
- `claude -p` is labeled preferred for most one-shot tasks.
- The example is a Hermes `terminal(...)` invocation with
  `--allowedTools Read,Edit` and `--max-turns 10`.
- Print mode needs no PTY and returns/exits.
- The interactive alternative uses `tmux`, sleeps, keystrokes, and pane
  capture.

The same pinned skill documents
[JSON/stream-JSON and session continuation](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/skills/autonomous-ai-agents/claude-code/SKILL.md#L143-L221).
`stream-json` is an available deeper recipe; it is not present in the basic
preferred command. Calling tmux “cruder” is a reasonable engineering inference
from terminal scraping and fixed sleeps. Calling it slower is not a measured
Ranex result.

Hermes' own
[provider documentation](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/website/docs/integrations/providers.md#L65-L75)
describes Nous Portal as its recommended general path. This disproves “normally”
when the word is applied to Hermes as a whole.

### Native Anthropic adapter

The pinned adapter identifies itself as an
[Anthropic Messages API adapter with API-key, setup-token, and Claude Code
credential support](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/agent/anthropic_adapter.py#L1-L11).
Its OAuth branch adds Claude Code-specific beta headers and identity behavior,
including a Claude Code system prefix and detected client version
([source](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/agent/anthropic_adapter.py#L345-L383)),
and builds an Anthropic SDK client with Claude Code user-agent/`x-app` headers
([source](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/agent/anthropic_adapter.py#L765-L886)).

Hermes' pinned provider documentation says this native OAuth route
[requires Max plus extra-usage credits, does not use included base Max
allowance, and does not support Pro](https://github.com/NousResearch/hermes-agent/blob/f228e145ba35cbbf785eded2021ae6682285b91b/website/docs/integrations/providers.md#L108-L116).
That is not the official Claude Code harness boundary selected for Ranex.

An
[open Hermes PR proposing a first-class `claude -p` inference backend](https://github.com/NousResearch/hermes-agent/pull/67335)
corroborates, but by itself does not prove, that the pinned mainline skill is
not yet a first-class runtime adapter. The pinned mainline files above are the
primary proof for the current structure.

## Current official Claude facts

### Runtime and lifecycle

Anthropic's current
[CLI reference](https://code.claude.com/docs/en/cli-usage) defines `claude -p`
as noninteractive print mode and documents structured output, explicit model,
turn limits, resume/continue, tools, deny rules, and interrupt-related scripting
surfaces.

The current
[Agent SDK hosting documentation](https://code.claude.com/docs/en/agent-sdk/hosting)
states that `query()` spawns a separate `claude` subprocess over stdio and that
one agent session maps to one subprocess. The
[Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python)
distinguishes one-shot `query()` from `ClaudeSDKClient`: the client reuses the
same session, supports multiple exchanges, and supports interrupt. This supports
a managed client boundary; it does not prove a zero-startup or prewarmed path.

Ranex will use the pinned SDK lifecycle rather than manipulate undocumented
private PIDs. Its cancellation contract is interrupt, drain correlated terminal
events to a deadline, call SDK disconnect, then have the outer sandbox/
supervisor verify cleanup. Exact close/terminate/kill behavior remains a
release-pinned qualification fact, not a timeless API promise.

### Tool and configuration enforcement

The original `--allowedTools Read,Edit` example is not a least-privilege tool
surface. Anthropic's
[permissions documentation](https://code.claude.com/docs/en/agent-sdk/permissions)
states that allow rules only pre-approve calls; unlisted tools remain available
and fall through to permission mode. It also states that `canUseTool` can be
shadowed by permission mode or allow rules, while a `PreToolUse` hook is the
mechanism for gating every call.

The current
[Python options reference](https://code.claude.com/docs/en/agent-sdk/python)
exposes the actual `tools` set, `disallowed_tools`, `model`, `fallback_model`,
`cwd`, environment, setting sources, strict MCP configuration, hooks, custom
tools, session IDs, and sandbox controls. The strict Ranex profile therefore
requires:

- exact actual `tools`, startup-attested and deny-complemented;
- no Agent/Task alias, Workflow, SendMessage, ToolSearch, Cron/RemoteTrigger,
  EnterWorktree, provider team/delegation, or background-capable surface;
- `dontAsk`, never model-classified `auto`, plus catch-all `PreToolUse` or an
  SDK custom-tool gateway for every observed attempt;
- `can_use_tool` only as the ask-path fallback;
- empty setting/agent/skill/plugin sources, strict explicit MCP, auto-memory
  disabled, and a per-lease config directory and working directory;
- explicit full model ID and no fallback model;
- sanitized environment and separate filesystem/network/process controls when
  Bash is granted; and
- `CapabilityBus` for every effect.

An official harness may still execute a bounded model/tool loop inside the
assignment. “Leaf” prohibits cross-worker/control-plane orchestration, not the
in-role loop required to do the assigned job.

### Authentication and terms

Anthropic's current
[authentication precedence](https://code.claude.com/docs/en/authentication)
places cloud credentials, auth tokens, and API keys ahead of subscription
OAuth; `ANTHROPIC_API_KEY` is always used in `-p` when present. The adapter must
sanitize the environment and record configured intent separately from observed
effective auth.

The June 16
[Claude plan/Agent SDK notice](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
says the proposed June 15 monthly-credit change is paused. For now, Agent SDK,
`claude -p`, and third-party Agent SDK app use continue to draw from
subscription usage limits. The older credit table remains on the page only as
preserved, non-effective reference.

Anthropic's current
[legal and compliance documentation](https://code.claude.com/docs/en/legal-and-compliance)
distinguishes ordinary individual OAuth use from products/services. It directs
third-party product developers to API-key or supported-cloud authentication and
forbids offering Claude.ai login or routing Free/Pro/Max credentials on behalf
of users. Therefore:

- eligible local individual use may select the official subscription route;
- a distributed Ranex product uses API/BYOK or a supported cloud unless
  Anthropic gives written approval; and
- Hermes-style credential extraction/identity imitation is not a Ranex route.

Vendor-internal entitlement routing that the adapter cannot observe remains
`UNKNOWN`. An account label is not proof of which quota or billing path was
used.

## Current official Codex facts

OpenAI's current
[Codex app-server documentation](https://learn.chatgpt.com/docs/app-server.md)
defines the structured integration surface used by rich clients: JSON-RPC 2.0
semantics, JSONL stdio, thread start/resume, streamed turn/item events,
approvals, and turn interruption. The implementation is published under
[openai/codex](https://github.com/openai/codex/tree/main/codex-rs/app-server).

The current
[Codex SDK documentation](https://learn.chatgpt.com/docs/codex-sdk.md) describes
thread start, continued turns, resume, streaming, and sandbox control; current
Python SDK builds include a pinned Codex runtime dependency. These facts support
the ADR-0011 typed adapter boundary. They do not prove a particular Pro
entitlement, latency, stable experimental surface, or the adequacy of Ranex's
future tool containment. The adapter stays on stable app-server APIs unless an
experimental surface receives its own qualification.

## OpenCode HY3 adversarial disposition

The first HY3 round judged the broad claim “mostly true on execution boundary,
materially overclaimed on mechanism, terminology, and terms scope.” The
primary-source rebuttal supplied the pinned skill, native adapter, official SDK,
permissions, auth, and legal facts above. The revised HY3 position converged on:

- Hermes' skill-prescribed print and tmux paths are real;
- subscription use is conditional on effective auth and current vendor terms;
- the official Claude runtime boundary is the shared foundation;
- a managed SDK client is a better typed substrate than terminal-skill
  orchestration;
- one-shot calls are not automatically persistent/warm;
- role-scoped actual tools and no ambient surfaces matter more than prompt
  allow-lists; and
- latency, process spawn, call amplification, memory, model pinning, and
  fallback absence require measurement.

HY3 initially underweighted the pinned tmux source and overgeneralized terms.
Those points were corrected in the rebuttal. The reviewer agreement is
advisory corroboration, not a source fact or owner decision.

## Owner decision applied

ADR-0011 applies the verified evidence as one integrated decision:

- Ranex alone orchestrates across workers.
- All model/harness runtimes are leaf workers with bounded in-role loops.
- Roles define immutable maximum envelopes; assignments compile exact proper
  subsets.
- One explicit model/route/runtime exists per assignment, with no fallback,
  auxiliary model, or provider-native worker delegation.
- Claude and Codex use official typed runtimes, not a parent Hermes inference
  layer or terminal/PTY/tmux hot path.
- Connected runtime reuse is assignment/lease/session/profile/auth/workspace
  affine and never crosses unrelated tasks.
- Hermes/Nous has provenance/reference/compatibility standing only and no live
  model, credential, entitlement, or monetization route.

## Inferences and unknowns

The following are explicitly not established facts:

- “tmux is slower” is plausible but unmeasured on Ranex.
- “SDK is blazing fast” is not established; one-shot SDK paths can still spawn
  a subprocess.
- Safe preconnect is supported as a design option but its latency/memory benefit
  is unmeasured.
- No source proves that a generic stateful client can be scrubbed safely for an
  unrelated assignment; ADR-0011 prohibits that reuse.
- Future Claude subscription policy, quota routing, and product authorization
  may change and must be rechecked at release/route qualification time.
- No OpenCode, DeepSeek, HY3, or direct-provider adapter is qualified merely
  because it was used as an advisory reviewer.
- Runtime enforcement, sandbox containment, exact tool closure, cancellation,
  event correlation, performance, and absence of hidden calls all remain
  `NOT_ASSESSED` until exact-host tests pass.

## Evidence limitation

Official documentation is current web material observed on 2026-07-29 and can
change. Hermes claims are pinned to an immutable Git commit. The two Web-GPT
notes and HY3 review are secondary/advisory material. This record paraphrases
sources and does not treat search snippets, issue assertions, reviewer
confidence, or architecture prose as runtime proof.
