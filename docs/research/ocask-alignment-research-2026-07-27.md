# OCAsk-to-Ranex alignment research

**Research date:** 2026-07-27<br>
**Decision status:** design-time adoption study; no OCAsk or Ranex runtime integration was implemented<br>
**Ranex revision reviewed:** `3844673b0bfa743de3c351566b6ffa9ffd67e0b8`<br>
**OCAsk product revision reviewed:** default branch `main` at `340151fc6ef43958adaf15776cee93147c42aeda`<br>
**OCAsk experimental revision reviewed separately:** divergent branch `master` at `4e2778d1b0a72b527b5674e56ac5ef02183d8fef`<br>
**Upstream repository:** <https://github.com/anthonykewl20/ocask><br>
**Primary Ranex authority:** `RANEX_IMPLEMENTATION_GUIDE.md` plus the owner-fixed architecture boundary recorded in `docs/research/cookbook-alignment-research-2026-07-27.md`<br>
**Internal review status:** parallel source, Ranex-gap, and report-structure reviews were completed in this research session; these are not organizationally or model-family independent, and no external security audit, legal opinion, or live-provider qualification was performed<br>
**Validation performed:** pinned-source inspection, Git and GitHub state inspection, the complete `main` offline Node test command, the repository sync check, and the documented experimental Intent Assurance test command

## Executive answer

**Decision: do not adapt OCAsk wholesale into Ranex, do not make it a required
or core Ranex dependency or gate, and do not copy its current OpenCode execution
boundary.**

OCAsk is valuable to Ranex as:

1. a compact catalogue of provider-routing, deadline, parsing, abstention,
   failure-taxonomy, and evaluation mechanisms;
2. a possible future **sandboxed comparative adapter** for an analytical reviewer
   lane; and
3. a source of unusually candid negative evaluation and operations evidence.

It is not suitable as:

- Ranex's control kernel;
- Ranex's review authority;
- Ranex's canonical model registry;
- Ranex's evidence ledger;
- Ranex's risk classifier;
- Ranex's default panel or lens system;
- an in-process concurrency-safe library; or
- a production-ready read-only OpenCode reviewer.

The recommended posture is therefore:

| Decision | What it means for Ranex |
|---|---|
| **REUSE** | Carry forward the abstract mechanisms that are already coherent: judgment versus no-judgment, abstention distinct from dissent, failure-origin unwrapping, shared product/evaluation parsing, explicit evaluation budgets, and the provider-factory attempt-history shape. |
| **MODIFY** | Re-express provider identity, retries, risk, telemetry, cost, and review outputs in Ranex-owned schemas and policy. Models remain evidence producers; deterministic code and humans remain the only transition authorities. |
| **REJECT** | Reject the current prompt-only read-only boundary, OpenCode `--auto` plus allow-all permissions, ambient caller environment, unbounded child output, model verdicts as gate results, opaque cross-model fallback, raw rationale logging, process-global run context, and local JSONL as a ledger. |
| **DEFER** | Defer an OCAsk subprocess adapter, panels, lenses, auto-risk, persistent OpenCode server use, and experimental `master` code until Ranex has a runtime, canonical contracts, a safe sandbox, and a provenance-backed qualification suite. |

The immediate adaptation is **documentation and contract design**, not source
import. Before implementation, Ranex should add:

- a candidate `AnalyticalReviewRequest` mapped to the guide's canonical IDs;
- a distinct `AnalysisAttempt`;
- a model-produced `ReviewObservation`;
- validation into the guide's existing `ReviewVerdict`; and
- deterministic reduction into the guide's existing `GateDecision`;
- an exact model-and-transport lock;
- one end-to-end deadline and spend budget;
- explicit retry ownership;
- a privacy-minimized telemetry contract; and
- a qualification protocol for the complete execution tuple.

The complete tuple matters:

```text
subject revision
+ task packet and policy revision
+ reviewer role
+ requested model identity
+ actual wire model identity
+ transport and transport version
+ tool/capability profile
+ prompt/evaluation specification
+ parser version
+ isolation profile
= the system that was actually qualified
```

OCAsk's current `--no-fallback` table cannot establish that tuple. It contains
human declarations over mutable aliases, has no immutable provider snapshot, and
does not capture the major capability difference between a native API call and an
OpenCode process with tools.

The strongest reason not to promote OCAsk's review strategies is its own frozen
evaluation. On a small 20-case JavaScript corpus, its control/lens/panel recall was
`0.60 / 0.70 / 0.10`, false-positive rate was `0.10 / 0.40 / 0.90`, and raw
no-verdict rate was `15% / 32% / 83%`. The report concluded that neither the lens
nor panel qualified over the control. Those figures are not general effectiveness
estimates: all 20 cases are placeholders and the frozen system-under-test commit is
unresolved. They are still sufficient negative evidence to reject panel or lens
promotion without a new Ranex-shaped trial.

## How to read this report

### Epistemic status

- **FACT** — directly observed in pinned source, Git state, test output, or an
  authoritative source.
- **INFERENCE** — a conclusion that follows from facts but was not directly
  exercised in the target Ranex runtime.
- **PROPOSAL** — a recommended Ranex design or delivery choice.
- **UNKNOWN** — evidence is missing, contradictory, stale, or too weak.
- **OWNER REQUIREMENT** — a product or architecture boundary already fixed by the
  owner; it is not presented as implemented behavior.

Inline labels are used for decision-critical claims whose status could otherwise
be mistaken. Unlabelled source summaries remain bounded by their adjacent
citations and the evidence hierarchy below; they should not be read as
implementation or qualification claims.

### Adaptation status

- **REUSE** — preserve the mechanism or principle.
- **MODIFY** — preserve the intent but redesign the contract or implementation.
- **REJECT** — do not carry the behavior into Ranex.
- **DEFER** — keep as an experiment until named evidence exists.

### What “mature” means here

“Mature” does not mean that a repository contains code or tests. A mechanism is
treated as mature enough to carry forward only when:

1. the contract is explicit;
2. the implementation and documentation agree;
3. tests exercise consequential sad paths;
4. the mechanism fails visibly;
5. its security and authority boundary fits Ranex; and
6. empirical outcome claims are separated from mechanism correctness.

OCAsk has several mature mechanisms. It does not have mature evidence that its
panels, lenses, or model verdicts improve Ranex outcomes.

## Scope and method

### Question asked

This report answers:

> If Ranex studies OCAsk deeply before implementation, which parts should be
> adapted into Ranex, which need redesign, which should be rejected, and what must
> be proven before any OCAsk code or executable is integrated?

It does not answer:

- how to install OCAsk for personal use;
- whether OCAsk is useful in its author's current workflow;
- whether the upstream owner should change OCAsk;
- whether any named model is generally “better”;
- whether Ranex should immediately implement the proposed integration; or
- whether an Apache-2.0 source import is legally advisable.

### Snapshot boundary

**FACT.** GitHub identifies `main` as the default branch. The pinned product
revision is
[`340151fc6ef43958adaf15776cee93147c42aeda`](https://github.com/anthonykewl20/ocask/tree/340151fc6ef43958adaf15776cee93147c42aeda),
dated 2026-07-22.

**FACT.** Remote `master` points at
[`4e2778d1b0a72b527b5674e56ac5ef02183d8fef`](https://github.com/anthonykewl20/ocask/tree/4e2778d1b0a72b527b5674e56ac5ef02183d8fef),
dated 2026-07-25. `git merge-base origin/main origin/master` found no common
ancestor. A left/right revision count reported `54 / 250`.

The report therefore uses:

- `main` as evidence about the OCAsk product; and
- `master` only as evidence about a separate experimental Intent Assurance and
  drift-guard research lineage.

Nothing found only on `master` is described as shipped OCAsk behavior.

**FACT.** Open
[PR #103](https://github.com/anthonykewl20/ocask/pull/103) proposes retiring the
Qwen family and promoting Tencent `hy3`. It is based on the pinned `main` revision
and remained open at review time. Its proposed state is not used as current product
fact.

### Evidence reviewed

The audit covered:

- the full OCAsk `main` source tree;
- `README.md`, `ARCHITECTURE.md`, governance, security, release, skill, command,
  installer, and CI files;
- `ocask.mjs`, `logging.mjs`, `ocverify.mjs`, pricing, version, and system code;
- all three provider implementations and their factory;
- the offline evaluation harness, corpus status, goldens, reports, and frozen
  baseline;
- all committed OCAsk decision records under `docs/research/`;
- open issues with direct bearing on provider output, OpenCode state, evaluation,
  routing, documentation drift, and installation;
- PR #103 as proposed future direction;
- the divergent `master` experimental architecture, evidence model, results
  ledger, and selected prototypes;
- the current Ranex implementation guide and Cookbook alignment report; and
- relevant official OpenCode, DeepSeek, gRPC, OpenTelemetry, OWASP, Temporal,
  GitHub, MITRE, and evaluation guidance.

### Evidence hierarchy

When sources disagree, this report uses:

1. observed behavior from the pinned executable tests;
2. executable source at the pinned revision;
3. committed machine-readable result artifacts;
4. committed design and research records;
5. current GitHub issues and pull requests;
6. README and architecture prose;
7. proposed future work;
8. inference.

An open issue can prove that a concern is documented; it cannot prove that its
proposed fix is implemented. A passing unit test can prove a tested mechanism; it
cannot prove real-provider behavior or review efficacy.

### Reproduced checks

At pinned `main`:

```text
node --test ocask.test.mjs eval/*.test.mjs
  tests 236
  pass 236
  fail 0

./check.sh
  94 passed
  3 failed

node --test experimental/prototype-1/intent-assurance.test.mjs
  tests 147
  pass 81
  fail 66
```

The three sync-check failures were local installation expectations: the temporary
checkout was intentionally not installed as the operator's `ocask` command, Claude
skill, or OpenCode command.

No paid model call was made. No provider credential was inspected. No OCAsk
installer was run. No Ranex runtime file was changed.

The `master` prototype command is not a clean release gate. Its suite includes
red/adversarial fixtures and at least one direct Intent Assurance report correctly
exited `2` on violated evidence, so 66 failed tests must not be relabelled as 66
independent product defects. The observed command is still concrete evidence
against treating the experimental implementation as production-ready.

## Evidence inventory

| Source | What it establishes | Limitation |
|---|---|---|
| Current Ranex repository at `3844673...` | Ranex is still a clean, seven-file, design-only bootstrap with no Hermes runtime, package manifest, schemas, tests, configuration, or remote. | There is no implementation against which interoperability can be demonstrated. |
| `RANEX_IMPLEMENTATION_GUIDE.md` | Intended domain records, routing, adapters, sandbox, evidence ledger, reviewer roles, gates, and qualification. | It is a plan with known internal conflicts, not runtime fact. |
| Cookbook alignment research | Owner-fixed modular-monolith and deterministic-kernel boundaries; nine unresolved guide conflicts; evidence standards. | It reviewed Ranex before this new report and does not analyze OCAsk. |
| OCAsk `main` source | Actual CLI, parser, provider, retry, panel, telemetry, security, and process behavior. | Provider and OS behavior was not exercised live in this study. |
| OCAsk offline tests | 236 tests pass at the pinned product revision, including real local CLI seams with fake provider executables. | Predominantly offline/mocked; not proof of account entitlements, provider identity, network behavior, sandboxing, or review quality. |
| `check.sh` | 94 substring/file/install checks pass in the temporary checkout. | It does not semantically compare docs and code and is not run by CI. |
| OCAsk frozen evaluation | A 20-case, 3-arm, 3-repeat JSON-mode result and candid negative panel/lens metrics. | Corpus cases are placeholders; exact SUT commit is unresolved; no text-mode baseline; small synthetic scope. |
| OCAsk decision records | Rationale for deadlines, panels, parsing, logging isolation, redaction, and provider behavior. | Some claims depend on private local telemetry or absent evidence; decisions can predate later code. |
| Open issues #78, #80, #92–#95, #104, #123, #124 | Known provider, storage, evaluation, routing, and documentation gaps. | Issues are reports/proposals, not completed fixes. |
| Open PR #103 | Concrete evidence of routing churn and hard-coded family assumptions. | Open and unmerged; its test counts and live probes describe the PR, not pinned `main`. |
| Divergent `master` research | Intent Assurance, exact evidence bindings, anti-erosion, staleness, static/dynamic completeness, and an honest results ledger. | Unrelated history, experimental scope, significant unbuilt design, and a documented test invocation that is not a clean release suite; no basis for treating it as OCAsk product code. |
| Official external sources | Current semantics for OpenCode auto permissions, DeepSeek response/model fields, deadlines, context, logging, retries, and evals. | General prior art; none proves Ranex-specific transferability. |

## What OCAsk actually is

### Implemented product boundary

**FACT.** OCAsk `main` is a Node.js 20+ command-line application with no npm
runtime dependencies. It is not packaged as an npm library or service. Its public
surface is:

- the `ocask` CLI;
- direct DeepSeek and Qwen HTTP adapters;
- an OpenCode CLI adapter;
- `doctor`, `diagnose`, `cost`, `pricing`, and `upgrade` subcommands;
- a Claude Code skill;
- an OpenCode slash command; and
- an installer that creates a symlink and copies user-level command files.

See the pinned
[README](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/README.md#L1-L51)
and
[installer](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/install.sh#L7-L83).

The source exports many functions for testing, but it does not declare a stable
library API, concurrency contract, compatibility policy, or package version
boundary for in-process consumers.

### Input and outbound-data boundary

`--task`, `--system`, and `--context` each accept:

- `-` for stdin;
- an existing regular file; or
- an inline string.

The reader treats a directory path as literal text rather than recursively loading
it
([`ocask.mjs:488-501`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L488-L501)).
The README's `--task ./src/` example therefore does not supply that directory's
contents.

There is no input byte cap for stdin or regular files before prompt assembly.
Task, system, context, lens, and response instructions are combined and sent to
the selected remote provider or OpenCode process
([`ocask.mjs:265-312`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L265-L312)).

**FACT.** Provider keys are not deliberately placed in that prompt. This is not
equivalent to “secrets never go to a model”: user-provided task/context may itself
contain secrets, proprietary code, credentials, or personal data. OCAsk has no
classification or egress-approval step for that content.

### Review output boundary

OCAsk can return free-form analysis or require one of:

- `APPROVED`;
- `WARNING`;
- `BLOCKED`; or
- no judgment when no valid verdict is produced.

This is a useful caller distinction. It remains a model opinion over supplied or
tool-discovered evidence, not a deterministic proof that a Ranex requirement is
satisfied.

### Product and release maturity

The project describes itself as `v0.1` and pre-1.0. At the research snapshot:

- `git ls-remote --tags` returned no tags;
- the changelog linked a `v0.1.0` release URL;
- that URL returned 404; and
- GitHub's releases page said there were no releases.

See the pinned
[changelog](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/CHANGELOG.md#L76-L82)
and the current
[GitHub releases page](https://github.com/anthonykewl20/ocask/releases).

This does not make the code unusable. It means Ranex cannot rely on a release tag,
immutable package artifact, support window, or conventional dependency update
channel.

## What Ranex needs from analytical review

Ranex does not merely need a model to print a verdict. It needs an analytical
effect whose observations can be bound to:

- one project;
- one task;
- one task-packet revision;
- one base commit;
- one candidate commit or artifact digest;
- one reviewer role;
- one actual execution identity;
- one actual model and transport;
- one isolation/capability profile;
- one evidence set;
- one parser and policy version; and
- explicit limitations.

The current guide already sketches separate `Run evidence`, `Review verdict`, and
`Gate decision` records (`RANEX_IMPLEMENTATION_GUIDE.md:2336-2401`). That
separation is directionally correct.

OCAsk exposes five design gaps that Ranex should resolve before implementation:

1. **A direct analytical model transport is not a code-writing worker.**<br>
   The guide's `WorkerAdapter` is broad enough to execute CLIs, but a direct HTTP
   reviewer needs a narrower, non-tool-bearing `AnalyticalTransport` contract.

2. **A provider attempt is not a review verdict.**<br>
   Requested route, actual route, retry chain, usage, failure, parse result, and
   model observation need separate records before normalization.

3. **Timeout is not the whole budget.**<br>
   The caller must own wall-clock, attempt, token, dollar, output-byte, and
   tool/side-effect budgets across all nested work.

4. **Model identity and execution capability are independent.**<br>
   A native API and an OpenCode process may claim the same model while exposing
   radically different context and tool surfaces.

5. **Operational diagnosis needs a typed causal record.**<br>
   Ranex's current guide does not yet define a complete attempt/failure taxonomy,
   censored latency handling, or route-health aggregation.

## Fixed Ranex boundaries governing adaptation

### Models produce evidence, not authority

**OWNER REQUIREMENT.** Ranex treats every LLM result as an untrusted proposal
until deterministic evidence or independent review supports it
(`RANEX_IMPLEMENTATION_GUIDE.md:91-102`).

The deterministic gate phase states that workflow advancement depends on
machine-verifiable evidence and explicit human decisions, not an agent saying work
is complete (`RANEX_IMPLEMENTATION_GUIDE.md:4369-4380`).

A review record is one input. A `Gate decision` and single-use permit remain
Ranex-owned (`RANEX_IMPLEMENTATION_GUIDE.md:4665-4766`).

This boundary overrides OCAsk documentation calling itself an “analytical gate.”

### Ranex is an owned modular monolith

**OWNER REQUIREMENT.** Required capabilities belong in first-party modules in
the owned Hermes fork. Users must not need to install optional plugins for Ranex
to be complete. External compatibility surfaces remain lower-authority adapters
(`docs/research/cookbook-alignment-research-2026-07-27.md:199-290`).

Therefore:

- OCAsk should not become a required end-user-installed plugin;
- its installer should not be part of Ranex bootstrap;
- any adapted mechanism should live behind a Ranex-owned internal port; and
- a future OCAsk executable integration should be optional, pinned, and
  replaceable.

### Ranex owns route and fallback policy

The guide requires:

- an explicit model registry;
- exact provider/access-path verification;
- a model lock;
- explainable risk routes; and
- rejection of unverified or role-weakening fallback
  (`RANEX_IMPLEMENTATION_GUIDE.md:2590-2778`).

OCAsk's internal model swap cannot silently substitute for that policy.

### Ranex requires enforced isolation

The guide requires argv execution, a minimal environment, bounded output,
real-path and symlink checks, an OS sandbox, a read-only review mount, and no
fallback to an unsandboxed lane
(`RANEX_IMPLEMENTATION_GUIDE.md:3136-3267`).

Prompt text such as “do not modify files” is not an isolation control.

### Existing Ranex contract conflicts remain prerequisites

The Cookbook alignment report identifies nine unresolved guide conflicts:

- governance state versus rule stage;
- role identifiers;
- configuration and state roots;
- worktree procedure;
- permit/gate sequencing;
- transactional system of record;
- profile creation;
- run-ID type; and
- qualification protocol
  (`docs/research/cookbook-alignment-research-2026-07-27.md:779-807`).

An OCAsk integration would add another run ID, state root, model vocabulary, and
qualification surface. Those existing conflicts must be normalized first.

## OCAsk architecture and behavior

### CLI and request contract

The CLI exposes model, provider, task, system, context, JSON mode, verdict
requirement, fallback, cross-verification, panel, risk, lens, metadata, timeout,
and an advisory response-length value
([`ocask.mjs:22-41`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L22-L41)).

Positive properties:

- unknown arguments fail;
- one stdin source is enforced;
- numeric timeout and token values are validated;
- a hard timeout ceiling exists;
- provider/model compatibility is checked before a preferred route runs; and
- output can be machine-readable.

Missing Ranex bindings:

- project ID;
- work-item ID;
- canonical Ranex run ID;
- base and candidate revisions;
- task-packet digest;
- active policy digest;
- evidence IDs;
- allowed source paths;
- isolation profile;
- route-lock revision;
- adapter executable digest; and
- idempotency key.

**FACT.** `--max-tokens` is not an enforced token limit. It adds an advisory
sentence to the prompt. The direct DeepSeek and Qwen adapters each send a fixed
`max_tokens: 65536`, and the OpenCode adapter receives no output-token limit
([`ocask.mjs:265-290`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L265-L290),
[`deepseek.mjs:12-73`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/deepseek.mjs#L12-L73),
[`qwen.mjs:13-90`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/qwen.mjs#L13-L90)).
Ranex must enforce cost, response-byte, and provider-supported token limits outside
the prompt.

**MODIFY.** Treat the CLI as a possible adapter protocol, not a canonical Ranex
request contract.

### Prompt assembly and review lenses

OCAsk assembles:

1. task text;
2. optional system and context text;
3. an optional review lens;
4. execution guidance; and
5. a response contract.

The review prompt explicitly says the task is read-only. The same prompt also asks
the model to “show your reasoning”
([`ocask.mjs:274-310`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L274-L310)).

**REJECT.**

- Do not copy a chain-of-thought disclosure request into Ranex.
- Do not treat a prompt lens as policy enforcement.
- Do not treat prompt text as a capability restriction.

**MODIFY.** If Ranex retains review lenses, define them as versioned
`ReviewSpecification` records containing:

- stable ID and version;
- intended role and task strata;
- rubric dimensions;
- response schema;
- source and approval;
- qualification results;
- known failure modes; and
- retirement state.

A lens is a review aid. It does not acquire authority because it is detailed.

### Provider abstraction

OCAsk's provider factory has several sound implementation properties:

- providers are lazy-loaded;
- each transport accepts a common request shape;
- successful results include actual provider/model information and token usage;
- errors have stable codes;
- the configured provider chain is filtered by serving compatibility; and
- the provider factory attaches prior transport attempts and an originating cause
  to its result or terminal wrapper
  ([`factory.mjs:18-31`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L18-L31),
  [`:128-201`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L128-L201),
  [`:237-304`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L237-L304)).

**REUSE** the factory's typed transport-result and attempt-history shape.

**FACT.** The higher-level `runAsk` path does not promote the factory's nested
`result.attempts` or wrapper `.attempts` into its CLI metadata. It records one
model-level attempt attributed to the final or originating provider
([`factory.mjs:255-302`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L255-L302),
[`ocask.mjs:800-849`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L800-L849)).
Ranex must promote every nested transport attempt into canonical records rather
than assuming the current CLI metadata is complete.

**MODIFY** the error model. Ranex needs at least:

```text
failure domain
  request | policy | capability | credential | transport | provider
  model-output | parser | evidence | cancellation | budget | internal

retry class
  never | same-attempt-safe | new-attempt-idempotent | human-decision

observation state
  reply-received | reply-absent | reply-unusable | result-incomplete

attribution confidence
  entailed | inferred | unknown
```

The OCAsk labels `our-side` and `their-side` are useful for a small CLI, but too
coarse once Ranex has a kernel, broker, adapter, sandbox, provider, and external
system.

### Model identity and transport trust

The identity table explicitly calls each entry a human-asserted declaration. All
snapshot IDs are null, and the declared routes include:

- `deepseek-v4-pro` via native `deepseek-chat`;
- `deepseek-v4-pro` via `deepseek/deepseek-v4-pro`;
- `qwen3.7-plus` via native `qwen-plus`; and
- `qwen3.7-plus` via `alibaba/qwen3.7-plus`.

See
[`factory.mjs:42-88`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L42-L88).

The recorded provenance path,
`.evidence/issue5-nofallback-decision.md`, is absent from pinned `main`.

`--no-fallback` therefore means:

- do not switch model family;
- permit transport fallback through a declared equivalent route; and
- report `identity_preserved` from that declaration.

It does **not** prove:

- immutable weights;
- an exact provider snapshot;
- identical inference configuration;
- identical tool availability;
- identical system prompts;
- identical context assembly;
- identical provider preprocessing; or
- identical observable behavior.

This matters because the native DeepSeek transport sends one user message with no
repository tools, while the OpenCode transport runs a tool-capable agent. “Same
weights” would still not mean “same reviewer system.”

**REJECT** the current table as Ranex identity evidence.

**MODIFY** it into distinct records:

```text
ModelIdentity
  provider model ID
  immutable snapshot/version when available
  provider response model ID
  reasoning mode and effort
  context/output limits
  observation timestamp

TransportIdentity
  adapter ID/version/digest
  API or CLI version
  wire route
  credential path class
  tool and permission profile
  prompt/system-envelope version

Qualification
  exact model + transport + capability + parser tuple
  tested strata
  result and limitations
  probation/retirement state
```

### Current DeepSeek route drift

Pinned `main` maps `deepseek-v4-pro` to `deepseek-chat` and only accepts
`choice.message.content`
([`deepseek.mjs:27-35`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/deepseek.mjs#L27-L35),
[`110-124`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/deepseek.mjs#L110-L124)).

Open
[issue #94](https://github.com/anthonykewl20/ocask/issues/94) records
reasoning-only responses being discarded and a requested-versus-served tier
mismatch.

Current official
[DeepSeek Chat Completion documentation](https://api-docs.deepseek.com/api/create-chat-completion)
lists `deepseek-v4-pro` and `deepseek-v4-flash` as model IDs and defines nullable
`reasoning_content`.

**FACT.** The external model contract is moving faster than the pinned adapter.

**PROPOSAL.** Ranex must discover and smoke-test the actual wire contract at
qualification time. Never copy the current aliases into a static kernel enum.

### Transport fallback, model retry, and partial deadline

OCAsk has two different fallback layers.

Provider fallback:

- starts with the model's native family provider;
- can continue to OpenCode;
- removes cross-family native providers through the compatibility gate; and
- retries selected transport/auth/rate/connection/model-not-found failures.

Model-output retry:

- occurs only after `MODEL_OUTPUT`;
- retries the same model up to two times;
- may then switch to the configured opposite-family model; and
- does not switch family under `--no-fallback`.

See
[`factory.mjs:118-207`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L118-L207)
and
[`ocask.mjs:789-903`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L789-L903).

**FACT.** OCAsk computes one model-level absolute deadline and recomputes the
remaining budget before each same-model/model-family retry and before each panel
member starts
([`ocask.mjs:70-89`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L70-L89),
[`719-803`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L719-L803)).

It does **not** enforce one deadline across every nested provider attempt.
`invokeWithFallback` passes the same `timeoutMs` independently to each sequential
provider in its chain rather than deducting the first provider's elapsed time
([`factory.mjs:258-290`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs#L258-L290)).
A native failure followed by OpenCode can therefore exceed the nominal deadline;
panel members inherit the same nested-provider defect.

**MODIFY.** Preserve the caller-owned absolute-deadline design, not the current
implementation. Every transport invocation must receive only the remaining
budget. This matches the established deadline-propagation principle of deducting
elapsed time from downstream work in the
[gRPC deadline guide](https://grpc.io/docs/guides/deadlines/).

**MODIFY.** Ranex should own all retry decisions. An opposite-family retry should
be a new `AnalysisAttempt` with:

- a new attempt ID;
- an explicit reason;
- the route policy that authorized it;
- remaining wall-clock and cost reservation;
- actual identity;
- subject binding;
- idempotency classification; and
- a visible relationship to the prior attempt.

OCAsk currently performs that model substitution inside one command. That makes
the high-level caller's policy and evidence graph harder to audit.

`--no-fallback` only prevents a cross-family substitution. It does not disable
the two same-model `MODEL_OUTPUT` retries, and it may still traverse declared
same-identity transports. A future adapter cannot claim kernel-owned retries
unless OCAsk exposes a true one-attempt mode or Ranex receives and governs every
nested attempt.

**REJECT.** Do not copy the claim that a verdict task is “read-only, safe to
replay.” Native API calls are externally billed; OpenCode can use tools; version
checks and logs mutate local state; and a timed-out operation may have partially
executed. Retried effects require explicit idempotency analysis. Temporal's
[Activity guidance](https://docs.temporal.io/activity-definition#idempotency)
explains why a timed-out or lost acknowledgment can cause repeated execution and
why idempotency keys belong at the called service.

### Four-way caller and verdict contract

The strongest OCAsk product contract is its distinction among:

```text
APPROVED     process 0
WARNING      process 0
BLOCKED      process 20
no-judgment  process 30
```

The JSON representation includes `outcome`, `verdict`, `reason`, `locus`,
`mechanism`, `exit_code`, and output
([`ocask.mjs:1007-1073`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L1007-L1073)).

**REUSE** these distinctions:

- positive opinion;
- cautionary opinion;
- negative opinion; and
- inability to form a valid opinion.

**MODIFY** their meaning:

- call them model `ReviewObservation` outcomes, not gate outcomes;
- represent missing/invalid/incomplete evidence separately;
- retain parser diagnostics;
- bind every observation to an exact subject;
- keep `WARNING` distinct from `APPROVED` in every projection; and
- make the CLI exit code a projection of typed data, not the domain source.

**FACT.** Standard single-model `runAsk` metadata sets `exit_code = 0` before
`runMain` maps `BLOCKED` to 20
([`ocask.mjs:904-910`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L904-L910),
[`1136-1157`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L1136-L1157)).
Failure metadata can similarly contain `1` while the final process contract uses
30.

**REJECT** `metadata.exit_code` as authoritative evidence.

### Verdict parsing

OCAsk's current parser has several sound properties:

- text verdicts must occupy a canonical whole line;
- repeated agreeing verdicts are accepted;
- conflicting verdicts are rejected;
- JSON mode validates a top-level verdict and rationale field;
- a bare text verdict needs some Unicode letter content outside verdict lines; and
- the evaluator imports the product verdict extractor.

See
[`ocask.mjs:383-478`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L383-L478)
and the
[parser-agreement decision](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/docs/research/issue87-parser-agreement.md).

**REUSE** one parser implementation across product and evaluation.

**MODIFY** the output schema. Ranex's planned review verdict includes evidence
IDs, reviewed commit, findings, severity, required actions, uncertainties, and an
independence attestation (`RANEX_IMPLEMENTATION_GUIDE.md:2367-2381`). OCAsk's
`verdict + rationale` cannot populate those fields safely.

The parser correctly documents that a letter-bearing line is a hygiene floor, not
semantic proof. Ranex must not invent missing findings or evidence references
during normalization.

### Panel consensus and abstention

The panel mechanism:

- selects two model families;
- launches members in parallel;
- shares one outer model-level deadline, subject to the nested-provider timeout
  defect described above;
- counts only members classified as real judgments;
- treats failures as abstentions;
- requires a strict majority;
- returns no judgment below quorum; and
- uses `BLOCKED`, otherwise `WARNING`, as a split-vote tiebreaker.

See
[`ocask.mjs:515-716`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L515-L716).

**FACT.** Current panel aggregation does not preserve full member findings or
rationales. Each successful member is reduced to a 200-character
`output_preview`, and formatted panel output contains the vote rather than the
full review
([`ocask.mjs:574-585`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L574-L585),
[`640-650`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L640-L650)).
That evidence loss prevents Ranex from auditing how consensus was formed.

**REUSE** the ontology:

- abstention is not dissent;
- insufficient judgment is not consensus;
- disagreement is not infrastructure failure; and
- a degraded panel must remain visible.

**REJECT** the authority inference. A vote reducer does not establish correctness.
The conservative tiebreaker is a policy choice, not evidence that the blocking
member is right.

**DEFER** all Ranex panel use until:

- each member gets an independently compiled evidence packet;
- the second reviewer does not see the first review;
- family/transport independence is qualified rather than named;
- member rationales and findings are preserved;
- the panel is compared against its best single member;
- abstention and cost are guardrails; and
- the complete panel tuple beats a simpler baseline.

### Cross-verification is not independent

The older `--cross-verify` path sends the buddy:

- the primary model name;
- the primary verdict; and
- up to 800 characters of the primary rationale.

It then asks for an “independent” opinion. If the buddy fails, OCAsk records
unavailability and returns the primary result
([`ocask.mjs:913-989`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L913-L989)).

**FACT.** This is a critique/confirmation pass, not blind independent evidence.

**REJECT** the independence label and silent degradation for any Ranex-mandatory
review.

### Risk selection

`--risk auto` inspects a unified diff:

- sensitive path regex;
- changed-line count;
- touched-file count; and
- small-change thresholds.

Non-diff input defaults to `default`
([`ocask.mjs:116-170`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L116-L170)).

**REUSE** explainability: a route selector should name the signals that affected
its choice.

**REJECT** this heuristic as authoritative Ranex risk. A tiny diff can alter a
generated policy, dependency lock, migration, permission default, or call path
whose risk is not visible in file count. An attacker or mistaken packet can omit
the relevant context.

**MODIFY.** Ranex risk should be derived from:

- owner/project policy;
- task kind;
- declared affected capabilities;
- changed dependency and permission surfaces;
- data classification;
- deployment/reversibility;
- static change analysis;
- prior incidents and uncertainty; and
- human override.

The diff heuristic may remain a non-authoritative signal with a reason code.

### Logging and diagnostics

OCAsk's logging has useful mechanisms:

- JSONL events;
- per-model-level attempt provider/model/duration/outcome;
- token observations;
- a typed failure taxonomy;
- originating-cause unwrapping;
- right-censored timeout marking;
- a doctor rule that names a cause only when evidence entails it;
- log rotation;
- mode-limited files;
- redaction of known secret variants; and
- a test-only guard against writing fixtures to the real operator log.

See
[`logging.mjs:188-275`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs#L188-L275),
[`387-405`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs#L387-L405),
and the
[test-telemetry decision](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/docs/research/issue79-test-telemetry-isolation.md).

**REUSE**:

- attempt-level records;
- explicit censored observations;
- originating failure alongside wrapper failure;
- “undetermined” rather than unsupported diagnosis;
- test telemetry isolation; and
- local private metadata writes.

**REJECT** the storage and context model:

- JSONL rotation discards old history;
- malformed lines are silently skipped;
- there is no content addressing or ledger relationship;
- `_currentRunId` is process-global mutable state
  ([`logging.mjs:413-521`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs#L413-L521));
- concurrent in-process runs can cross-attribute later events;
- prompt hashes are truncated, unkeyed, stable correlation identifiers; and
- the log is operator observability, not tamper evidence.

OpenTelemetry defines `Context` as immutable, execution-scoped state propagated
across logically associated units
([OpenTelemetry Context specification](https://opentelemetry.io/docs/specs/otel/context/)).
Ranex should pass a `RunContext` explicitly or through a concurrency-safe scoped
mechanism, never through one mutable module global.

### Logging privacy contradiction

The architecture says logs never contain raw prompt, output, credentials, paths,
or session IDs
([`ARCHITECTURE.md:304-320`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ARCHITECTURE.md#L304-L320)).

The implementation passes the first 200 characters of model output to
`logVerdict`, which stores it as `brief` without the secret scrubber
([`ocask.mjs:906-910`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L906-L910),
[`logging.mjs:474-483`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs#L474-L483)).

**FACT.** The documentation's “no raw output” claim is false at the pinned
revision.

The
[OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
recommends excluding or transforming source code, session identifiers, tokens,
passwords, keys, and other sensitive data.

**PROPOSAL.** Ranex telemetry should default to:

- IDs and digests;
- sizes and counts;
- normalized status;
- timings and cost;
- provider response IDs;
- artifact references;
- redaction outcome; and
- explicit sampling/classification.

Raw prompts, model output, source, and paths belong in separately classified
artifacts with retention and access policy, not routine telemetry.

### Historical telemetry contamination

The OCAsk test-isolation decision records that 7,627 of 10,800 log records were
quarantined as likely test contamination. It also records that a reported provider
health number changed materially after partitioning
([`issue79-test-telemetry-isolation.md:54-89`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/docs/research/issue79-test-telemetry-isolation.md#L54-L89)).

The fix is a positive engineering response. The incident means earlier
log-derived latency, failure, and health claims cannot be transferred without
provenance and isolation.

**REUSE** the lesson: synthetic, evaluation, probe, and production observations
need explicit origin and separate storage/queries.

### Metadata writing

OCAsk writes metadata via a new mode-0600 temporary file, fsync, atomic rename,
and chmod
([`ocask.mjs:995-1005`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L995-L1005)).

**REUSE** the atomic private-write pattern for local projections.

**MODIFY.** Ranex's canonical evidence still needs:

- schema validation;
- content digest;
- exact subject;
- event/ledger relationship;
- append-only history;
- transaction/outbox rules; and
- recovery tests.

An atomic file is not automatically trustworthy evidence.

### OpenCode execution boundary

This is the most important rejection.

Pinned `main`:

- sets `MAX_OUTPUT_BYTES = 0`;
- sets `OPENCODE_PERMISSION` to `{"*":"allow"}`;
- invokes `opencode run --auto --pure`;
- spreads the complete caller-provided environment into the child;
- gives the child the caller's working directory;
- buffers stdout and stderr completely in memory; and
- uses no OS-enforced read-only sandbox.

See
[`opencode.mjs:14-25`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/opencode.mjs#L14-L25),
[`261-305`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/opencode.mjs#L261-L305),
and
[`334-379`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/opencode.mjs#L334-L379).

Current official
[OpenCode permission documentation](https://opencode.ai/docs/permissions)
states that `--auto` automatically approves requests not explicitly denied and
that global permission may be set to allow. OCAsk supplies both auto mode and a
global allow.

The prompt's “do not modify files” statement does not constrain a mistaken,
compromised, or instruction-injected tool call. The child can also see ambient
credentials and unrelated environment values.

This directly conflicts with Ranex requirements for:

- deny-by-default tools;
- no `--auto` until forbidden operations are proven denied;
- a minimal environment;
- a read-only review mount;
- bounded output;
- no whole-home exposure; and
- kernel-enforced isolation
  (`RANEX_IMPLEMENTATION_GUIDE.md:3193-3267`, `:3337-3354`).

**REJECT** the current OCAsk OpenCode transport for any Ranex production lane.

If a later experiment uses it, the outer Ranex adapter must enforce the boundary
regardless of OCAsk internals. Promotion additionally requires OCAsk to stop
re-enabling tools itself.

### Persistent OpenCode server

`providers/opencode.mjs` contains substantial persistent-server state, lock,
health, and startup machinery. The active `invoke` path calculates
`disableServer` but always uses direct `opencode run`; it never calls the server
machinery.

Open
[issue #93](https://github.com/anthonykewl20/ocask/issues/93) proposes routing
through the server to avoid shared database lock collisions.
[Issue #92](https://github.com/anthonykewl20/ocask/issues/92) records probe/bench
pollution of the shared OpenCode database.

**FACT.** Persistent-server code existence does not establish persistent-server
product behavior.

**DEFER.** Ranex should not inherit this state management. If a future OpenCode
adapter needs a daemon, define ownership, readiness, auth, database isolation,
concurrency, shutdown, recovery, and evidence as Ranex contracts.

### Version-check side effect

Every normal CLI entry starts a fire-and-forget GitHub release check unless
`OCASK_NO_VERSION_CHECK=1`
([`ocask.mjs:1177-1179`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs#L1177-L1179),
[`version.mjs:51-92`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/version.mjs#L51-L92)).

That can perform network and local cache writes unrelated to the requested review.

**REJECT** unsolicited update checks inside a Ranex effect adapter. Version
discovery belongs in an explicit probe or operator-controlled maintenance task.

### Credential handling

Positive properties:

- credentials are not put in argv;
- direct providers accept caller-owned environment objects;
- missing `HOME` prevents the direct DeepSeek/Qwen provider resolvers from
  silently falling back to the process home;
- known secret values and several encodings are scrubbed from failure messages; and
- metadata excludes mechanism text.

Limitations:

- provider invocation reads `$HOME/.deepseek-key` or `$HOME/.qwen-key` without
  checking ownership, symlink state, or mode;
- the full environment reaches OpenCode;
- redaction knows only secrets it can enumerate;
- task/context can contain unknown secrets;
- a remote model receives user content by design; and
- secret redaction is not egress control.

**FACT.** Logging's `gatherSecretValues(env)` separately calls `os.homedir()` and
reads `.deepseek-key`, `.qwen-key`, and `.opencode-go-key` from the real process
home, ignoring the caller-provided `env.HOME`
([`logging.mjs:79-104`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs#L79-L104)).
Clearing `HOME` or pointing it at an isolated directory therefore does not by
itself prevent OCAsk from reading operator-home key files.

**MODIFY.** Ranex should provide adapter-specific secret handles/projections,
mount only required credential material read-only, clear the rest of the
environment, hide the real operator home through the filesystem sandbox, and
record capability identity without recording secret values.

### `ocverify.mjs`

`ocverify.mjs` is a second verifier with:

- a different model allowlist;
- a separate Zen Go API client;
- `confirm/reject/error` output;
- hard blockers, soft flags, and evidence;
- optional grep/read/git-show tools; and
- its own retry/parser behavior.

See
[`ocverify.mjs:10-105`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocverify.mjs#L10-L105)
and
[`516-607`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocverify.mjs#L516-L607).

Its model allowlist includes identities the main provider factory cannot serve.
PR #103 explicitly reports that models listable through one API are not
necessarily servable through it.

The tool path check uses lexical `path.resolve` containment and then reads or
greps the resulting path
([`ocverify.mjs:264-370`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocverify.mjs#L264-L370)).
A symlink located inside the repository can target material outside it.
[CWE-61](https://cwe.mitre.org/data/definitions/61.html) covers the class of
security failure caused by following an attacker-influenced symbolic link.

**REJECT**:

- duplicate verdict taxonomies;
- duplicate model allowlists;
- lexical-only containment; and
- a verifier that combines route registry, provider client, tool broker, parser,
  and verdict policy.

**REUSE** only the idea of separating hard reproducible findings from softer
observations, after expressing both in canonical Ranex records.

## Evaluation evidence

### Evaluation design

The committed harness defines:

- control: `deepseek-v4-pro`, general lens;
- lens: the same model, code-review lens;
- panel: the same requested model with panel mode;
- 3 arms × 3 iterations per case;
- an offline injectable seam;
- a live-run opt-in;
- a default USD cap;
- an explicit baseline-freeze flag;
- an 80% completion threshold;
- JSON or text output mode;
- system-under-test identity capture; and
- one product/evaluation verdict parser.

See
[`eval/README.md`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/README.md).

**REUSE**:

- explicit control and treatment arms;
- repeated trials;
- abstention and flip-rate measurement;
- separate normal result and frozen baseline;
- spend gating;
- exact SUT identity fields;
- shared parsing; and
- publication of negative results.

### Frozen result

The T08 run reports:

| Arm | Recall | False-positive rate | Reported abstention | Flip rate | Raw no-verdict |
|---|---:|---:|---:|---:|---:|
| Control | 0.60 | 0.10 | 0.15 | 0.33 | 9/60 |
| Lens | 0.70 | 0.40 | 0.32 | 0.57 | 19/60 |
| Panel | 0.10 | 0.90 | 0.00* | 0.20 | 50/60 |

`*` Panel no-verdicts were conservatively mapped to misses/false positives, so
the raw 83% quorum-failure rate is the informative availability measure.

The report states:

- the lens added only one caught buggy case and failed its significance rule;
- lens false positives and instability regressed;
- panel recall collapsed and false positives rose;
- panel cost more while performing worse; and
- verdict adherence should be improved before adding review structure.

See
[`T08-baseline-where-ocask-fails.md`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/reports/T08-baseline-where-ocask-fails.md).

**FACT.** These results are strong evidence against promoting the tested lens or
panel configuration.

### Evaluation limitations

The result cannot support a general OCAsk or Ranex effectiveness claim because:

- all 20 corpus entries are explicitly placeholders
  ([`eval/corpus/VERIFIED.md`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/corpus/VERIFIED.md));
- golden outputs are synthetic
  ([`eval/golden/README.md`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/golden/README.md));
- the frozen baseline records the exact SUT ref and commit as unresolved
  ([`frozen-baseline.json:1-25`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/baseline/frozen-baseline.json#L1-L25));
- it is JSON-mode only;
- open [issue #95](https://github.com/anthonykewl20/ocask/issues/95)
  says no text-mode baseline exists;
- the corpus is only small JavaScript snippets;
- no hidden holdout is established;
- no exact current provider/model snapshot is bound; and
- the evaluation does not measure Ranex workflow completion or customer outcome.

Two measurement details also prevent direct reuse of the current promotion
rules:

- missing token aggregates remain `null`, but the token-budget guardrail defaults
  to pass when token data is unavailable; and
- the live cost snapshot returns `0` when the expected `per_model` array is
  absent
  ([`eval/metrics.mjs:573-599`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/metrics.mjs#L573-L599),
  [`eval/run-live.mjs:262-270`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/run-live.mjs#L262-L270)).

The significance helper also uses alpha `0.15` and automatically accepts any
recall increase once baseline recall is at least `0.8`
([`eval/metrics.mjs:6-10`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/metrics.mjs#L6-L10),
[`181-199`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/metrics.mjs#L181-L199)).
Those are repository policy choices, not general statistical evidence and not
Ranex defaults.

Anthropic's
[agent-evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
recommends repeated trials, balanced positive/negative cases, multiple grader
types, human calibration, transcript inspection, and product-shaped tasks. Those
principles support a broader Ranex qualification suite; they do not validate
OCAsk's current corpus.

### Required Ranex qualification

**PROPOSAL.** Any future OCAsk adapter must be compared against:

1. no model reviewer;
2. the simplest single-model Ranex-native reviewer;
3. the same model without an OCAsk lens;
4. OCAsk single-model;
5. any proposed panel; and
6. deterministic checks alone and combined with model review.

Predeclare:

- task strata and risk;
- provenance-backed buggy and clean cases;
- hidden holdout;
- exact SUT tuple;
- randomization/counterbalancing;
- repetitions;
- grader calibration;
- recall and false-positive costs;
- abstention;
- flip/consistency;
- latency;
- tokens and dollars;
- security/policy violations;
- workflow completion;
- promotion thresholds; and
- an explicit inconclusive outcome.

Do not use the T08 thresholds as Ranex policy.

## Testing, CI, governance, and documentation

### Tests

**FACT.** The pinned full offline command passed 236/236 tests in this research
environment.

This establishes meaningful coverage of:

- argument parsing;
- risk selection;
- model guards;
- identity-table behavior;
- provider-chain filtering;
- direct-provider caller-owned environment behavior;
- outer model-level deadline calculations;
- output parsing;
- panels and abstentions;
- exit codes;
- redaction;
- logging isolation;
- real local CLI/symlink seams;
- evaluation parsing and metrics; and
- baseline persistence.

It does not establish:

- real DeepSeek or Qwen availability;
- actual model identity;
- OpenCode permissions or filesystem confinement;
- safe live retry;
- provider pricing;
- account or quota behavior;
- production concurrency;
- review accuracy outside the placeholder corpus; or
- Ranex integration.

### Test-count and command drift

The README says “45 unit tests”; the architecture says “23 unit tests.” The
observed full run has 236 tests
([`README.md:282-290`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/README.md#L282-L290),
[`ARCHITECTURE.md:342-359`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ARCHITECTURE.md#L342-L359)).

CI runs:

```text
node --test ocask.test.mjs eval/*.test.mjs
```

The contributing guide calls the narrower `node --test ocask.test.mjs` command
“exactly what CI runs.” Open
[issue #104](https://github.com/anthonykewl20/ocask/issues/104) records that
drift.

CI does not run `check.sh`, even though the contributor guide requires installed
command verification for consequential changes
([CI workflow](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/.github/workflows/ci.yml),
[`CONTRIBUTING.md:29-65`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/CONTRIBUTING.md#L29-L65)).

**REUSE** real-seam installed-command tests.

**REJECT** test-count claims and duplicated commands as synchronization
mechanisms. Generate documentation fragments or make one command the executable
source of truth.

### Sync check limitation

`check.sh` primarily checks whether selected substrings occur in code and docs.
It did not detect:

- false raw-output privacy prose;
- the stale test counts;
- the narrower contributor test command;
- the README fallback graph mismatch;
- the inactive persistent server path; or
- the personal absolute path in the skill.

Open [issue #123](https://github.com/anthonykewl20/ocask/issues/123) explicitly
records documentation/tracker drift. Open
[issue #124](https://github.com/anthonykewl20/ocask/issues/124) records that the
installed skill ships a stale personal path
([`skill/SKILL.md:9-17`](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/skill/SKILL.md#L9-L17)).

**REUSE** the intent that derived surfaces remain synchronized.

**MODIFY** it into structural generation, schema validation, executable examples,
and behavior tests. Presence of a word is not proof that two contracts agree.

### CI supply-chain note

The workflow references `actions/checkout@v7` and `actions/setup-node@v7`, not
immutable commit SHAs. GitHub's
[secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
recommends pinning third-party actions to full-length commit SHAs as the only
immutable release form.

This is not central to the OCAsk-to-Ranex decision. Ranex should nevertheless
apply its own supply-chain policy rather than copying the workflow verbatim.

### Governance unknowns

README and contributing prose say `main` is protected. This review did not have
administrative settings access and does not treat prose as proof of branch
protection.

**UNKNOWN.** Required checks, dismissal rules, force-push policy, signed commits,
and private vulnerability-reporting enablement were not independently verified.

These are project-governance concerns, not prerequisites for reusing an
algorithmic idea. They are prerequisites for trusting an upstream branch or
release as a pinned production dependency.

## Licensing and provenance

OCAsk `main` contains an Apache License 2.0 file and a NOTICE that says
redistributions or derivative works must retain the notice
([LICENSE](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/LICENSE),
[NOTICE](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/NOTICE)).

Ranex's current licensing manifest distinguishes:

- MIT upstream Hermes material;
- original Ranex personal-use material;
- mixed modified material; and
- curated research
  (`legal/licensing-manifest.json:9-37`).

It does not currently classify imported Apache-2.0 OCAsk material.

**PROPOSAL.**

- Pattern-level research belongs under `CURATED_RESEARCH`.
- If source is copied or vendored, add an explicit Apache-2.0 material class,
  source revision, file-level provenance, license text, NOTICE handling, and
  modification record before the copy lands.
- Do not relabel OCAsk source as original Ranex material.
- A separately invoked executable reduces source mixing but does not remove
  version, provenance, distribution, or notice questions.

This report is not a legal opinion. The owner should obtain a rights review before
public distribution of copied or modified OCAsk source.

## Divergent `master`: experimental research, not product behavior

### Why it is included

The remote `master` lineage contains an experimental Intent Assurance engine and
drift-guard research with several ideas that align strongly with Ranex. Excluding
it would miss useful research; merging it conceptually with `main` would be
incorrect.

**FACT.** It is an unrelated Git history and must be versioned, qualified, and
licensed as a separate source lineage.

**FACT.** The documented prototype command
`node --test experimental/prototype-1/intent-assurance.test.mjs` was not green at
the pinned revision: 81 of 147 tests passed and 66 failed in this environment. A
direct report in the output exited `2` on a violated fixture. Some failures may
represent intentionally red adversarial fixtures, so this is not a count of
independent defects. It does mean the documented invocation cannot be used as a
release-grade qualification signal.

### Useful experimental patterns

#### 1. Model output is explicitly soft

The experimental specification says model outputs may be `AI_INFERRED` or
`LINK_PROPOSED` but may not emit executable-evidence statuses. Real commands and
deterministic executors determine enforcement
([`experimental/SPEC.md:29-49`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/SPEC.md#L29-L49)).

**REUSE.** This directly matches Ranex's kernel boundary.

#### 2. Evidence has orthogonal axes

The experimental decisions separate:

- `oracle_strength`;
- `argument_state`; and
- `provenance`
  ([`experimental/DECISIONS.md:66-88`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/DECISIONS.md#L66-L88)).

**REUSE the separation, MODIFY the vocabulary.** Ranex should not collapse:

- how strong a check is;
- whether the current claim is satisfied, violated, conflicting, stale, waived,
  or uncovered; and
- who or what produced the observation.

A single green/red label loses essential information.

#### 3. Exact evidence binding

The experimental architecture uses an in-toto Statement-like envelope, exact
subject digests, SLSA-style dependencies/byproducts/builder identity, and a nested
test result
([`experimental/architecture.md:362-499`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/architecture.md#L362-L499)).

**MODIFY.** Ranex already proposes similar shapes in the Cookbook alignment report.
Use current official schemas and Ranex-owned types; do not copy the experimental
schema unquestioned or claim SLSA compliance.

#### 4. `must_now_pass` and `must_stay_green`

The experiment distinguishes new required behavior from established guarantees
that may not erode. It checks whether named guard tests still exist, execute, and
retain a bounded assertion shape.

**REUSE** the anti-erosion concept. Ranex should represent monotonic regression
obligations explicitly and add non-vacuity probes: inject a known violation and
confirm the bound evidence turns red.

**MODIFY.** A test name or lexical assertion shape is only a bounded oracle. The
record must state its scope and limitations.

#### 5. Staleness schedules reevaluation

The experiment marks affected evidence stale using reverse reachability, reruns
it, and blocks on an actual violation or uncovered requirement rather than stale
state alone
([`experimental/architecture.md:170-207`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/architecture.md#L170-L207)).

**REUSE.** Staleness, violation, absence, and conflict are different states.

**MODIFY.** Critical policy may still decide that unresolved stale evidence blocks
a transition. The kernel should make that policy explicit rather than treating
staleness as pass or failure by definition.

#### 6. Static and dynamic evidence are complementary

The drift-guard ledger reports:

- static enumeration can be precise but misses indirection and catalogue gaps;
- dynamic observation catches exercised effects but misses unexercised paths and
  unmonitored operations; and
- absence of observed effects is not proof that no effect exists
  ([`experimental/drift-guard/LEDGER.md:25-52`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/drift-guard/LEDGER.md#L25-L52)).

**REUSE.** Ranex schemas should preserve:

- `ABSENT`;
- `NOT_READ`;
- `NOT_EXERCISED`;
- `UNSUPPORTED`;
- `UNKNOWN`;
- `INCOMPLETE`; and
- `OBSERVED`.

Never convert “the instrument saw nothing” directly to “the behavior does not
exist.”

#### 7. Honest negative results

The ledger records:

- a model reclassified a reworded promise as background in 10/10 reads;
- a writing template preserved shape but not meaning;
- demanding a proof led authors to invent or select inadequate proofs;
- document chopping reversed polarity while structural checks remained green; and
- local records are forgeable without an external trust anchor.

These are unusually useful negative findings
([`experimental/drift-guard/LEDGER.md:37-47`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/drift-guard/LEDGER.md#L37-L47),
[`96-108`](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/drift-guard/LEDGER.md#L96-L108)).

**REUSE** the research discipline.

**REJECT** any inference that tags, hashes, signatures, templates, panels, or
model review establish semantic correctness by themselves.

### What not to import from `master`

- the experimental implementation as a production Ranex module;
- exact status names before Ranex contract normalization;
- JavaScript-specific scanners as language-general policy;
- local unsigned attestations as an external root of trust;
- hand-maintained sink catalogues as complete;
- exit codes as the only authority interface; or
- unbuilt drift-guard designs as established mechanisms.

**DEFER** a separate Intent Assurance/drift-guard alignment report if Ranex plans
to implement that feature. It is materially larger than an OCAsk reviewer adapter
and deserves its own decision boundary.

## Alignment matrix

| Area | OCAsk position | Ranex position | Decision | Reason |
|---|---|---|---|---|
| Product form | Standalone CLI plus user-installed skill/command | Owned first-party modular monolith | **REJECT** as core form | Ranex must not depend on user installation or duplicate command state. |
| Analytical reviewer | Model produces review and verdict | Reviewer produces evidence | **MODIFY** | Preserve analysis, remove transition authority. |
| Provider interface | Lazy common `invoke` adapters | Planned worker adapters and model registry | **MODIFY** | Reuse the typed-result intent inside a narrower Ranex analytical transport port. |
| Current identity table | Human-declared alias/transport equivalence | Exact model/access lock and qualification | **REJECT** | Mutable aliases and missing provenance cannot prove identity. |
| Identity contract | Requested/served/provider fields | Full model, transport, capability, and qualification tuple | **MODIFY** | Preserve observations but replace the trust semantics and schema. |
| Transport identity | Provider name plus route | Full adapter/capability/version tuple | **MODIFY** | Native API and OpenCode are not equivalent reviewer systems. |
| Provider fallback | Internal compatible transport chain | Kernel-owned explicit route policy | **MODIFY** | Each attempt must be visible and policy-authorized. |
| Model fallback | Internal opposite-family retry | Role/risk policy and new governed attempt | **REJECT** as opaque behavior | A model substitution changes the qualified system. |
| Deadline | Outer model-level deadline; nested provider attempts reuse the same timeout | One actual end-to-end deadline | **MODIFY** | Preserve the design goal and fix nested transport accounting. |
| Spend budget | Eval cap and token/cost logs | Planned quota/cost governance | **MODIFY** | Add reservation, exact price source, and concurrency-safe cap. |
| Retry safety | Review described as safe to replay | Effects require idempotency classification | **REJECT** | Tool use, billing, logs, and partial execution break the blanket claim. |
| Output parser | Whole-line/JSON verdict parser | Canonical typed review schema | **MODIFY** | Reuse one-parser discipline; normalize into richer records without inventing data. |
| Judgment states | Approved/warning/blocked/no-judgment | Review evidence plus deterministic gate | **MODIFY** | Keep the distinctions but rename and scope them as observations. |
| CLI exit codes | Warning and approval both zero | Typed kernel state | **REJECT** as authority | Shell success cannot distinguish caution from approval. |
| Panel abstention | No-judgment is excluded from votes | Unknown must not pass | **REUSE** | Correct distinction. |
| Current panel reducer | Model vote becomes consensus verdict and member rationale is truncated | Evidence reducer and policy gate | **REJECT** | Voting does not establish truth and discards review evidence. |
| Any future panel feature | Parallel analytical observations | Optional qualified reviewer strategy | **DEFER** | Local eval is negative; promotion requires best-member comparison and preserved findings. |
| Cross-verify | Buddy sees primary opinion; failure degrades | Independent evidence required when claimed | **REJECT** | It is critique, not independent review. |
| Risk auto-detection | Diff-size/path heuristic | Project/policy/capability risk | **MODIFY** | Keep as advisory signal only. |
| Current review lens | Prompt checklist | No default before qualification | **DEFER** | The tested lens failed local guardrails. |
| Review specification contract | Unversioned built-in prompt lens | Versioned, approved, retired specification | **MODIFY** | Preserve rubric intent only through a Ranex-owned lifecycle. |
| Read-only claim | Prompt instruction | OS-enforced read-only mount/capabilities | **REJECT** | Prompt is not enforcement. |
| OpenCode permissions | Global allow plus `--auto` | Deny by default | **REJECT** | Direct conflict with Ranex safety boundary. |
| Child environment | Complete caller env | Minimal allowlist and secret projection | **REJECT** | Ambient authority and secret exposure. |
| Child output | No byte limit, full buffering | Streamed bounded artifacts and memory cap | **REJECT** | Availability and evidence-size risk. |
| Workspace containment | CWD plus prompt | Real-path, Git identity, read-only sandbox | **REJECT** | Current adapter does not enforce subject/workspace isolation. |
| Tool path containment | Lexical path check in verifier | Real-path and symlink rejection | **REJECT** | Symlink escape remains possible. |
| Failure taxonomy | Typed origin/locus/mechanism/censoring | Not yet fully specified | **MODIFY** | Reuse the distinctions but add Ranex domains and retry semantics. |
| Diagnosis | Cause only when entailed | Evidence-linked operational diagnosis | **REUSE** | Avoid confident unsupported root cause. |
| Run context | Process-global mutable run ID | Per-run execution context | **REJECT** | Unsafe for concurrent in-process use. |
| Telemetry event concepts | Attempt, failure, usage, and verdict events | Canonical execution-scoped event schema | **MODIFY** | Preserve useful fields and remove global context/raw previews. |
| JSONL storage as ledger | Rotating local file with skipped malformed lines | Append-only events/artifacts/projections | **REJECT** | Operator logs are not canonical evidence. |
| Prompt hash | Stable truncated SHA-256 | Artifact IDs and privacy policy | **REJECT** as identity | Correlation is not provenance and can leak equality. |
| Metadata write | Atomic private file | Durable evidence plane | **MODIFY** | Retain the write technique only for a non-authoritative projection. |
| Version check | Implicit startup network/cache effect | Explicit operator probe | **REJECT** | Unrelated side effect during review. |
| Eval parser | Imports product parser | One canonical classification seam | **REUSE** | Prevents measurement/product drift. |
| Eval matrix | Three arms, repeats, budgets, negative report | Product-shaped qualification | **MODIFY** | Preserve experimental mechanics; replace corpus, binding, missing-data, and promotion rules. |
| Eval result | Panel/lens fail local guardrails | No defaults before qualification | **REJECT** promotion | Direct negative evidence. |
| Documentation sync | Substring checks and copied commands | Generated/validated contracts | **MODIFY** | Preserve synchronization intent through structural generation and behavior tests. |
| Installation | Writes user home and symlinks | Reproducible Ranex distribution | **REJECT** | Do not run upstream installer inside product bootstrap. |
| License | Apache-2.0 plus NOTICE | Mixed MIT/personal-use manifest | **MODIFY** | New material class and provenance are required before copying. |
| Experimental evidence axes | Separate strength/state/provenance on `master` | Evidence plane needs honest status | **DEFER** | Strong research proposal, but the experimental implementation is not qualified. |
| Experimental drift guard | Separate unrelated prototype lineage | Possible future Ranex capability | **DEFER** | Too large and unproven to smuggle through reviewer integration. |

## Patterns worth carrying forward or completing

### 1. One caller-owned absolute deadline

**MODIFY.** Adopt this as a Ranex invariant, but do not reuse OCAsk's current
nested-provider implementation. Every nested attempt must consume the same
remaining time. Add:

- monotonic-clock measurement;
- cancellation propagation;
- attempt count;
- token/dollar reservations;
- output limits;
- tool-call limits; and
- a typed budget-exhausted result.

### 2. Judgment is distinct from no judgment

**REUSE.** Provider failure, malformed reply, timeout, and lack of evidence may
not be converted into approval or rejection.

**MODIFY.** Preserve at least:

```text
OPINION_PRODUCED
NO_OPINION
OPINION_UNUSABLE
EVALUATION_INCOMPLETE
```

The final gate separately uses the guide's existing outcomes: `PASS`, `FAIL`,
`UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, or `WAIVED`. The Stage 0 normalization
may amend that contract explicitly; this report does not introduce another gate
enum.

### 3. Abstention is distinct from dissent

**REUSE.** A reviewer unable to judge has not voted either way. This applies even
without panels: an unavailable challenger is missing evidence, not concurrence.

### 4. Typed attempt history and originating cause

**REUSE** the factory's typed attempt and originating-cause distinctions.

**MODIFY** their exposure: promote every nested transport and model attempt into
Ranex records with duration, result, actual model/transport, and origin failure.
The current CLI metadata is incomplete. Do not let an aggregate “providers
exhausted” wrapper erase the cause.

### 5. Entailment-based operational diagnosis

**REUSE.** Name a cause only when the record supports it. Otherwise preserve the
symptom and say `UNKNOWN` or `UNDETERMINED`.

### 6. One product/evaluation parser

**REUSE.** The same parser version must classify production and evaluation
outputs. Store raw artifact digest, parser version, normalized result, and
diagnostics so reprocessing is possible.

### 7. Test telemetry isolation

**REUSE.** Tests, probes, evals, and production must have separate origin labels
and storage. Add a hard guard so test mode cannot write to production evidence or
operator health state.

### 8. Atomic private projections

**REUSE.** Write sensitive local projections through exclusive temp creation,
fsync, rename, and restrictive mode. Keep canonical event/evidence semantics
separate.

### 9. Explicit live-eval spend gate

**REUSE.** Live calls require an explicit opt-in and a budget cap.

**MODIFY.** Reserve cost before concurrent batches and stop scheduling before the
cap can be exceeded. Temporal's
[fixed-count retry guidance](https://docs.temporal.io/design-patterns/fixed-count-retries)
is useful prior art for capping attempts when each call consumes paid or scarce
resources.

### 10. Transparent negative reporting

**REUSE.** OCAsk's T07/T08 reports describe abstention, broken metrics, negative
panel value, and cost instead of hiding them. Ranex should preserve this
decision-record style.

### 11. Real-seam command tests

**REUSE.** Test the installed/packaged invocation, exit status, stdout, stderr,
signals, symlinks, and environment—not only imported functions.

### 12. Orthogonal evidence status

**PROPOSAL — DEFER pending qualification.** The experimental lineage suggests
keeping strength, current claim state, provenance, freshness, completeness, and
authority as separate fields. The concept aligns with Ranex, but it does not meet
this report's maturity test at the pinned experimental revision.

### 13. Anti-erosion obligations

**PROPOSAL — DEFER pending qualification.** Record what must newly pass and what
must remain green, then test the proposal with mutation/non-vacuity probes so an
erased guard cannot remain green by construction. Do not describe the current
experimental implementation as an adopted Ranex mechanism.

## What must not be inherited unchanged

### Authority

- model verdicts as gate outcomes;
- majority vote as proof;
- shell exit zero as approval;
- warning and approval collapsed in a caller's only signal;
- a prompt-assigned role as authority;
- a local log or metadata file as a permit; or
- model-declared completion.

### Isolation and capabilities

- `OPENCODE_PERMISSION={"*":"allow"}`;
- `opencode run --auto`;
- prompt-only read-only policy;
- full caller environment;
- ambient real home;
- unrestricted network beyond provider need;
- no OS sandbox;
- unbounded stdout/stderr;
- lexical path containment;
- cross-project readable state; or
- fallback from a failed sandbox to none.

### Identity and routing

- mutable aliases as exact model identity;
- human declarations labeled “preserved” without present provenance;
- model-only identity without transport/tool profile;
- hard-coded “opposite family” tables;
- unknown model families defaulted to another family;
- opaque internal model fallback;
- copied provider names/prices/timeouts; or
- unverified fallback for a critical role.

### Evidence and observability

- process-global run IDs;
- raw model-output previews in routine logs;
- prompt hashes as artifact identity;
- silently skipped malformed audit records;
- rotating logs as the evidence ledger;
- test and production observations in one health dataset;
- generated summaries that cannot link to raw artifacts; or
- exact-subject fields omitted from review records.

### Evaluation

- the placeholder corpus as a promotion suite;
- the unresolved frozen SUT identity;
- JSON-mode results generalized to text mode;
- panel or lens defaults based on the current result;
- thresholds selected after seeing a baseline;
- one ad hoc “significance” rule as statistical proof;
- missing token data allowed to pass the token guardrail;
- an absent live `per_model` cost array interpreted as zero;
- model-family labels as independence proof; or
- efficacy claims derived from offline mechanism tests.

### Distribution and governance

- running `install.sh` inside Ranex bootstrap;
- copied user-home skills as first-party module state;
- duplicated hand-maintained commands/counts;
- unpinned upstream source;
- absent release artifacts treated as a version;
- copying Apache source without manifest/NOTICE treatment; or
- relying on unverified branch-protection prose.

## Contradictions and drift found

### Inside OCAsk `main`

| Contradiction or drift | Evidence | Consequence |
|---|---|---|
| README provider graph says `deepseek → qwen → opencode`; code filters incompatible native providers and architecture says `deepseek → opencode`. | `README.md:169-180`; `ARCHITECTURE.md:118-137`; `factory.mjs:118-201` | A caller cannot derive actual routing from the quick documentation. |
| README calls verdict retries read-only and safe to replay; OpenCode runs with auto-approved allow-all tools. | `README.md:177-186`; `opencode.mjs:22-25,345-365` | Safety claim is not enforced. |
| Architecture says no raw output is logged; `logVerdict` stores the first 200 output characters. | `ARCHITECTURE.md:304-320`; `ocask.mjs:906-910`; `logging.mjs:474-483` | Privacy documentation is false. |
| Architecture documents optional persistent server mode; active invocation always runs direct. | `ARCHITECTURE.md:111-116`; `opencode.mjs:334-379` | Documented state/concurrency behavior is not active behavior. |
| README says 45 tests, Architecture says 23, observed suite has 236. | README and architecture test sections; reproduced test run | Counts are stale and cannot support maturity claims. |
| Contributing says its narrower test command is exactly CI. | `CONTRIBUTING.md:29-65`; CI line 26; issue #104 | Contributors can miss all eval tests while believing they ran the gate. |
| `check.sh` claims synchronization but misses semantic contradictions and the stale personal skill path. | `check.sh`; issues #123/#124 | Substring presence is not contract synchronization. |
| Changelog describes v0.1.0, but no tag or release exists. | `CHANGELOG.md:76-82`; remote tags; GitHub releases | There is no immutable release boundary. |
| `--metadata` single-run exit code can disagree with final process/JSON outcome. | `ocask.mjs:874-904,1007-1073,1136-1157` | Metadata consumers can misclassify a blocked/failed run. |
| “Identity preserved” can span native no-tools and OpenCode allow-all-tools transports. | trust table and provider code | Identity field overstates equivalence of the reviewed system. |
| Trust-table provenance points to a missing file. | `factory.mjs:42-88`; repository file inventory | Declaration cannot be audited from its named evidence. |
| Native DeepSeek parser ignores reasoning-only content; current issue records field failure. | `deepseek.mjs:110-124`; issue #94 | Valid replies can become malformed/no-judgment. |
| Main allowlist and `ocverify` allowlist/serving surface differ. | `factory.mjs:35-40`; `ocverify.mjs:10-22`; PR #103 | “Allowed,” “known,” and “servable” are conflated. |
| The outer deadline is recomputed for model retries, but each nested provider receives the full same timeout. | `ocask.mjs:789-803`; `factory.mjs:258-290` | Sequential transport fallback can exceed the nominal deadline. |
| `--max-tokens` sounds like a budget but is prompt advice; native providers request 65,536 and OpenCode receives no token cap. | `ocask.mjs:265-290`; native provider request bodies | Caller cost/output assumptions can be false. |
| Direct provider credential lookup honors caller `HOME`; logging's scrubber reads keys through real `os.homedir()`. | provider resolvers; `logging.mjs:79-104` | Environment-only home isolation still reads operator-home secrets. |
| Factory results retain nested provider attempts; `runAsk` does not copy them into CLI metadata. | `factory.mjs:255-302`; `ocask.mjs:800-849` | High-level evidence can omit actual transport attempts. |
| Panel aggregation asks members for analysis but keeps only a 200-character preview and emits votes. | `ocask.mjs:574-585,640-650` | Consensus evidence cannot be reconstructed from the result. |
| Panel results use `panel.result`; doctor only counts `verdict` as successful run completion. | `logging.mjs:474-498,553-568,645-650` | **INFERENCE:** panel runs can appear as partial crashes in doctor aggregation. This was not separately executed in this study. |

### Inside Ranex

The nine guide conflicts already listed in the Cookbook alignment report remain.
This report adds the following design gaps:

| Gap | Why OCAsk makes it visible | Required resolution |
|---|---|---|
| No narrow analytical transport port | Direct APIs do not fit a code-writing worker cleanly. | Define `AnalyticalTransport` and capability-free direct-provider semantics. |
| No analysis-attempt record distinct from verdict | OCAsk mixes request, retries, provider outcome, parser, and verdict. | Add `AnalysisAttempt` and `ReviewObservation` before `ReviewVerdict`. |
| Nested deadline/spend semantics incomplete | OCAsk shows primary, retry, fallback, panel, and buddy compete for one budget. | Define one caller-owned budget object and reservation rules. |
| Model identity lacks capability tuple | OCAsk's same model can run through native API or a tool-bearing CLI. | Qualify model, transport, prompt, parser, tools, and sandbox together. |
| Operational failure taxonomy incomplete | OCAsk has useful origin/censoring distinctions. | Define Ranex failure domains, retry safety, and attribution confidence. |
| Review specification lifecycle absent | Lenses can drift or regress without a versioned qualification. | Add version, source, approval, evaluation, and retirement. |
| Live analytical egress is not yet authorized | A native reviewer sends selected task evidence to a remote destination. | Resolve data classification, destination policy, credentials, quota/cost, and HUMAN GATE 9 before a live call. |
| Transaction/recovery semantics remain unresolved | Provider return, evidence commit, gate evaluation, and permit issuance cross crash boundaries. | Resolve canonical authority/outbox/permit atomicity in Stage 0 and prove it with the fake adapter. |
| Reimplemented analytical capabilities need the fixed module contract | A copied mechanism can otherwise become an unregistered second subsystem. | Require composition-root registration, descriptors/digests, capabilities, schemas, activation, canarying, and qualification. |
| This new report is not yet in the licensing manifest | Ranex requires every new file to be classified. | Add this file as `CURATED_RESEARCH` before landing it. |
| Licensing manifest lacks Apache imported-material class | Copying OCAsk would create a third source regime. | Resolve before any source import. |

### OCAsk versus Ranex

| Tension | Ranex decision |
|---|---|
| OCAsk describes itself as the analytical gate. | OCAsk output can only be analytical evidence. |
| OCAsk model verdict determines exit semantics. | Deterministic policy and human authority determine state transitions. |
| OCAsk `--no-fallback` trusts declared aliases. | Ranex records actual model/route and qualifies the full tuple. |
| OCAsk can retry/switch models internally. | Ranex kernel owns retries and records each attempt. |
| OCAsk review-only is prompt text. | Ranex read-only is an OS and capability property. |
| OCAsk logs locally under user state. | Ranex owns evidence events, artifacts, projections, retention, and access. |
| OCAsk auto-risk inspects diff shape. | Ranex risk is project/policy/capability data; heuristic is advisory. |
| OCAsk installer writes user-level commands. | Required Ranex modules ship built in. |
| OCAsk panel vote emits consensus. | Ranex may combine observations, but a vote does not issue a permit. |
| OCAsk cross-verify sees the first verdict. | Call it critique; reserve independence for hidden prior output and separated context. |

## Reappraisal of external claims

### OpenCode permissions

Official OpenCode documentation says:

- `allow` runs without approval;
- `ask` prompts;
- `deny` blocks; and
- `--auto` automatically approves requests not explicitly denied.

OCAsk sets global allow and auto mode. The strongest defensible statement is not
“review-only”; it is “the prompt requests no mutation while the runtime grants
tools.”

### DeepSeek model identity and output

Current official API documentation exposes different model names and a thinking
response field from those assumed by pinned OCAsk. This is direct evidence that
provider aliases and response shapes are volatile.

Ranex must:

- record the actual response model ID;
- record thinking/reasoning configuration;
- probe both content fields;
- reject silent tier changes;
- freeze the adapter version; and
- requalify on provider contract change.

### Deadlines

OCAsk's outer absolute-deadline design is supported by mature
deadline-propagation practice, but its nested provider fallback does not fully
implement that design. Ranex should implement and test one actual end-to-end
deadline, not copy either the defect or OCAsk's specific 170/300/900-second
constants. Those constants came from a small local sample and must not become
Ranex defaults.

### Logging

Mode-0600 local files and known-secret redaction are useful defense in depth. They
do not make raw model output safe to log and do not create tamper resistance.

### Evaluation

Multiple trials and layered graders are good practice. A small, public,
hand-authored placeholder corpus with an unresolved SUT revision is not a
promotion-grade effectiveness proof.

### Local attestations

Hashes and local signatures can detect accidental drift when their anchor is
preserved. A process with authority to rewrite the evidence store and anchor can
rewrite both. Ranex should call such records tamper-evident only within a stated
threat model.

## Recommended Ranex architecture

### Boundary: analytical effect below deterministic authority

```text
human / issue / task
          |
          v
  deterministic intake
  project + task + risk
          |
          v
  task-packet compiler
  exact subject manifest
          |
          v
  route and capability policy
  model/transport lock + budget
          |
          v
  AnalyticalReviewPort
          |
          +------------------------------+
          |                              |
          v                              v
  native provider adapter       sandboxed CLI adapter
  no tools by construction      read-only capabilities
          |                              |
          +--------------+---------------+
                         v
                 AnalysisAttempt
                 raw artifact refs
                 actual identity
                 failure/usage
                         |
                         v
                 ReviewObservation
                 findings + uncertainty
                 no transition authority
                         |
                         v
                 kernel validation
                 subject + independence checks
                         |
                         v
                 ReviewVerdict
                 existing guide contract
                         |
                         v
                 deterministic checks
                 policy reduction
                         |
                         v
                 GateDecision
                 existing guide outcomes
                         |
                  human decision when required
                         |
                         v
                 single-use permit / transition
```

### Candidate additive contracts and canonical mappings

These are **candidate** contracts for Stage 0, not a new canonical vocabulary.
Field names that overlap the implementation guide use its current forms:
`task_id`, `risk_class`, `base_commit_sha`, and `subject_commit_sha`. Stage 0 must
resolve the guide's pre-existing ID/schema conflicts before code or generated
schemas adopt them.

#### `AnalyticalReviewRequest`

```text
request_id
schema_version
project_id
task_id
run_id (after the canonical run-ID normalization)
review_role_id
task_packet_id
task_packet_digest
policy_activation_id
policy_digest
base_commit_sha
subject_commit_sha
subject_manifest_digest
evidence_refs
review_spec_id
review_spec_version
risk_class
requested_route_lock_id
capability_profile_id
isolation_profile_id
absolute_deadline
attempt_limit
token_budget
cost_budget
output_byte_budget
idempotency_key
created_at
```

#### `RouteLock`

```text
route_lock_id
provider_id
requested_model_id
wire_model_id
snapshot_or_version
transport_id
transport_version
transport_digest
api_or_cli_version
reasoning_mode
reasoning_effort
tool_profile_digest
permission_profile_digest
prompt_envelope_version
parser_version
verified_at
qualification_id
known_limitations
```

#### `AnalysisAttempt`

```text
attempt_id
request_id
attempt_index
retry_of
retry_reason
retry_policy_version
requested_route_lock_id
actual_provider_id
actual_model_id
provider_response_id
actual_transport_id
executable_path
executable_digest
cwd_identity
isolation_identity
capability_identity
started_at
finished_at
deadline_at_start
remaining_cost_at_start
status
failure_domain
failure_mechanism
failure_origin
retry_class
duration_censored
http_status
token_usage
estimated_cost
stdout_artifact
stderr_artifact
raw_response_artifact
limitations
```

#### `ReviewObservation`

```text
observation_id
request_id
attempt_id
subject_commit_sha
subject_manifest_digest
review_spec_id
review_spec_version
parser_version
opinion_state
opinion
findings
evidence_refs
uncertainties
required_actions_proposed
completeness
raw_artifact_ref
```

`ReviewObservation` is raw normalized analytical evidence. The model does not
supply `independence_class`. The kernel derives independence from run, session,
worker, task-packet role, subject timing, capability, and modification evidence.

The kernel then validates eligible observations into the implementation guide's
existing `ReviewVerdict` contract, including `task_id`, `subject_commit_sha`,
reviewer identity, findings, evidence references, and limitations. Deterministic
gate reduction emits the guide's existing `GateDecision` outcomes:
`PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, or `WAIVED`.

If Stage 0 changes those guide contracts, it must provide an explicit migration
and regenerate all examples. This report does not silently replace
`ReviewVerdict` or `GateDecision`. No field from `ReviewObservation` directly
grants a state change.

### Provider and capability boundary

Define two implementation categories:

1. **Native analytical transport**
   - no filesystem/tool capability;
   - prompt and selected evidence only;
   - minimal secret handle;
   - response byte cap;
   - actual response identity;
   - explicit egress classification.

2. **Tool-bearing analytical adapter**
   - OS sandbox;
   - read-only exact subject;
   - minimal environment and credentials;
   - deny-by-default tool policy;
   - bounded processes/output;
   - provider-only network where feasible;
   - complete tool/effect evidence;
   - no access to office authority or unrelated projects.

Never silently substitute one category for the other.

### Subject binding and evidence provenance

The packet compiler should produce a deterministic subject manifest containing:

- repository identity;
- base and candidate commit;
- dirty state;
- diff digest;
- selected file digests;
- dependency/context source digests;
- active acceptance criteria;
- active review specification;
- omissions and budget truncation;
- observation time; and
- compiler version.

The reviewer must echo only IDs/digests supplied by the host. The host validates
them; the model cannot establish them by assertion.

### Retry, timeout, and idempotency

One kernel-owned budget object should cover all attempts:

```text
deadline
max_attempts
max_same_route_attempts
max_route_changes
token reservation
cost reservation
output bytes
tool calls
side effects
```

Retry rules:

- parser/output repair can retry only under a declared count and remaining budget;
- a transport retry records potential duplicate submission;
- a model/transport change is a new attempt;
- a sandbox/policy violation is never retried through a weaker capability profile;
- a critical role cannot silently downgrade;
- tool-bearing retries require replay safety or a new isolated snapshot; and
- cancellation must terminate the whole process group and record uncertain
  completion where acknowledgment is missing.

### Observability

Use explicit execution-scoped context and emit:

- request and attempt IDs;
- actual route;
- status/failure taxonomy;
- duration and censoring;
- token/cost observations;
- artifact references;
- parser version;
- sampling/privacy classification; and
- trace relationships.

Observability is not the evidence ledger. Evidence artifacts are content-addressed
and retained under policy. Current-state health tables are rebuildable
projections.

### Qualification, canarying, and retirement

Qualification attaches to the complete tuple, not a friendly model name.

Use the implementation guide's existing route lifecycle:

```text
UNCONFIGURED
AUTHENTICATED
SMOKE_TESTED
PROBATION
APPROVED
RESTRICTED
SUSPENDED
RETIRED
```

`APPROVED` is scoped by the exact model, provider, adapter, reasoning setting,
role, task risk classes, toolset, office policy, parser, and isolation profile.
Qualification strata and health degradation are scoped fields/evidence that may
move a route to `RESTRICTED` or `SUSPENDED`; they are not a competing lifecycle.
This route lifecycle also remains distinct from the Cookbook report's module
activation lifecycle.

Re-probation, restriction, suspension, or explicit retirement triggers:

- provider model ID changes;
- transport or CLI version changes;
- tool/permission profile changes;
- prompt/review specification changes;
- parser changes;
- sandbox changes;
- provider response-shape changes;
- material abstention/FP/latency/cost drift; or
- a security incident.

Every reimplemented reviewer, provider, parser, or scoring capability must also
follow the owner-fixed module contract: composition-root registration,
descriptor and digest, explicit capability grants, configuration/state schemas,
activation scope, canarying, and independent qualification. A route being
`APPROVED` does not by itself activate or authorize its module.

## Integration options

| Option | Decision | Why |
|---|---|---|
| Copy OCAsk source into Ranex core | **REJECT** | Wrong authority, state, concurrency, security, distribution, and license seam. |
| Vendor OCAsk and modify it in place | **REJECT for v1** | Creates a second product/kernel and ongoing upstream divergence before Ranex has contracts. |
| Import `ocask.mjs` in process | **REJECT for initial integration** | No stable library API; process-global run ID; user-state logging; implicit version check; provider globals; harder isolation. |
| Require users to install OCAsk | **REJECT** | Conflicts with the baked-in first-party module requirement. |
| Invoke a pinned OCAsk executable as a sandboxed adapter | **DEFER, candidate experiment** | Replaceable and isolatable, but current OpenCode path and review evidence still need restrictions and qualification. |
| Re-express selected mechanisms in Ranex-owned modules | **PROCEED at design level** | Keeps one authority model and canonical contracts; implementation still follows the staged gates. |
| Use OCAsk only as a comparative eval arm | **DEFER until qualification harness exists** | Useful benchmark without product dependency. |
| Import divergent `master` Intent Assurance engine | **DEFER to separate study** | Valuable research, unrelated and not production ready. |

## Recommended delivery process

### Design amendments before code

Update the implementation guide or a generated canonical contract set to:

1. define the modular-monolith boundary as authoritative;
2. resolve the existing nine guide conflicts;
3. add `AnalyticalReviewPort`;
4. add the four candidate analytical contracts above and map them explicitly to
   the existing `ReviewVerdict` and `GateDecision`;
5. separate model identity from transport/capability identity;
6. assign retry and fallback ownership to the kernel;
7. define one end-to-end budget;
8. define review-specification lifecycle;
9. define telemetry privacy and execution context; and
10. classify Apache-2.0 imported material before any source copy.

### Build the native seam before an OCAsk adapter

Design work may proceed now. Runtime work must first complete the implementation
guide's Phases 0–3: preflight, owned-Hermes history adoption, isolated
environment, and an unmodified upstream baseline. Before creating a provider/auth
stack, inspect the inherited Hermes provider seams and wrap or refactor them
behind the Ranex port where possible.

The first analytical runtime tracer should then use a fake adapter, followed by
the smallest native provider adapter or inherited-Hermes wrapper that satisfies
the port. This proves Ranex's:

- request schema;
- exact subject;
- no-judgment handling;
- parser;
- evidence ingestion;
- deterministic gate boundary;
- budget; and
- sandbox-independent direct transport.

Only after that seam is stable should OCAsk be added as one replaceable adapter.

### Candidate OCAsk experiment

If authorized after the prerequisites, the first experiment should:

- pin exact OCAsk commit and executable digest;
- use a Ranex-built stdin packet;
- select an explicit provider and locked model;
- use `--json --require-verdict --no-fallback`;
- disable panel, cross-verify, and auto-risk;
- require a verified one-attempt/zero-retry OCAsk mode or audited patch before
  product integration—pinned `main` has no such option, and `--no-fallback` still
  permits two same-model output retries and declared transport fallback;
- set `OCASK_NO_VERSION_CHECK=1`;
- use a per-run `XDG_DATA_HOME`;
- use a filesystem namespace that hides the real operator home; clearing `HOME`
  alone is insufficient because logging calls `os.homedir()`;
- provide a minimal credential projection;
- initially prohibit the OCAsk OpenCode transport;
- enforce the real deadline, response bytes, token/cost reservation, and process
  limits outside OCAsk;
- capture actual process status and JSON, not metadata exit code alone;
- ingest every provider and model attempt; the current CLI metadata is
  insufficient for this;
- ingest output only as `ReviewObservation`; and
- compare against the Ranex-native baseline.

Unmodified pinned `main` may still be used as an opaque comparative evaluation
arm, but it cannot pass the product-adapter stage while its nested retries and
attempts remain outside kernel control. This is an experiment plan, not
authorization to implement it now.

## Prioritized fog register

### P0 — blocks a coherent and safe tracer

| Unknown | Risk | Required evidence | Acceptance test |
|---|---|---|---|
| Canonical authority boundary | A model opinion could advance state. | Final schema and reducer showing observation cannot issue permit. | `AT-AUTH-001 model observation cannot transition` |
| Canonical IDs and roots | OCAsk adds conflicting run IDs and state directories. | One generated registry and path ownership map. | `AT-ID-001 cross-record join` |
| Analytical port versus worker adapter | Direct API gets overprivileged or forced into wrong lifecycle. | Separate interfaces and fake adapters. | `AT-PORT-001 direct transport has no tools` |
| Exact subject contract | Reviewer can judge stale/wrong code. | Commit/digest-bound packet and validation. | `AT-SUBJECT-001 swapped commit rejected` |
| Full route identity | Mutable alias is mistaken for qualified identity. | Actual response ID, CLI/API version, capability tuple. | `AT-ROUTE-001 alias/transport mismatch` |
| Read-only enforcement | Reviewer mutates code or reads unrelated secrets. | OS sandbox and capability profile. | `AT-SBX-001 outside write denied`; `AT-SBX-002 sibling read denied` |
| Output and process bounds | Child exhausts memory/disk or survives timeout. | Outer runner with streamed limits and process groups. | `AT-PROC-001 output bomb`; `AT-PROC-002 child tree killed` |
| Retry ownership | Hidden model/transport switch weakens evidence. | Kernel retry state machine and attempt records. | `AT-RETRY-001 every switch is new attempt` |
| Budget atomicity | Parallel attempts overspend. | Reservation and release protocol. | `AT-BUDGET-001 concurrent cap` |
| Egress classification and authorization | Private task data goes to the wrong provider before any live tracer. | Data classification, destination policy, minimal credentials, and HUMAN GATE 9 approval. | `AT-EGRESS-001 restricted packet blocked` |
| Review normalization | Missing findings/evidence are invented. | Lossless parser/normalizer rules. | `AT-NORM-001 absent field stays absent` |
| Evidence versus telemetry | Local log is treated as ledger. | Separate schemas/storage/retention. | `AT-EVID-001 rebuild projection` |
| Transaction and recovery boundary | Crash loses provider result, evidence, or permit relationship. | Canonical authority, transaction/outbox, reconciliation, and fake-adapter crash tests. | `AT-RECOVERY-001 crash after provider return` |
| Licensing/provenance class | This research is unclassified for landing; copied Apache material would add another source regime. | `CURATED_RESEARCH` entry for this report and an owner/legal decision before source import. | `AT-LIC-001 new-file classification` |

### P1 — blocks unattended or multi-project operation

| Unknown | Risk | Required evidence | Acceptance test |
|---|---|---|---|
| Concurrent run context | Events cross between runs. | Explicit/async-safe run context. | `AT-CTX-001 interleaved runs` |
| Provider credential projection | Adapter sees unrelated home secrets. | Minimal read-only credential projection. | `AT-SECRET-001 enumerate-home denied` |
| Cancellation acknowledgment | Timed-out effect may still run. | Process/provider cancellation semantics and uncertain state. | `AT-CANCEL-001 late completion` |
| Cost truth | Missing tokens/pricing appear as zero cost. | Usage source, price revision, unknown-cost state. | `AT-COST-001 missing usage is unknown` |
| Provider response drift | Valid reasoning output becomes malformed. | Contract fixtures and live canary. | `AT-PROVIDER-001 content/reasoning variants` |
| Multi-project log isolation | One project leaks paths/output to another. | Project-scoped artifacts and access tests. | `AT-ISO-001 cross-project query denied` |
| Route degradation | Critical review silently uses weaker route. | Route-state and human escalation policy. | `AT-ROUTE-002 critical fallback blocks` |
| Upstream pin/update | Moving branch changes executable silently. | Digest lock and explicit update workflow. | `AT-PIN-001 branch movement detected` |

### P2 — optional optimization

| Unknown | Decision now | Promotion evidence |
|---|---|---|
| Do OCAsk lenses help Ranex? | **DEFER** | Paired, provenance-backed holdout with FP/abstention/consistency guardrails. |
| Does a panel beat one reviewer? | **DEFER** | Best-member comparison, independent packets, material net lift. |
| Is auto-risk useful? | **DEFER** | Recall of policy-defined high-risk tasks with bounded false escalation. |
| Does persistent OpenCode server help? | **DEFER** | Isolated DB, concurrency, lifecycle, recovery, and security proof. |
| Is two-step verdict extraction worth another call? | **DEFER** | Head-to-head against current parser under cost/latency guardrails; see issue #80. |
| Should OCAsk doctor concepts become a UI? | **DEFER** | Stable canonical telemetry and calibrated diagnosis first. |
| Should Ranex implement drift guard/Intent Assurance? | **SEPARATE STUDY** | Product scope, threat model, language matrix, external trust anchor, and efficacy trial. |

## Staged validation plan

### Stage 0 — contract and documentation consistency

Deliver:

- canonical IDs and state roots;
- module/adapter authority diagram;
- analysis/review/gate schemas;
- route lock;
- budget/retry state machine;
- review-specification schema;
- canonical transactional authority, outbox, permit atomicity, and reconciliation;
- module descriptors, capability grants, activation, and qualification rules;
- licensing decision and manifest classification for this report; and
- generated examples.

Pass when:

- every guide example validates;
- no model field can authorize a transition;
- role/model/transport names come from one registry;
- the Cookbook owner boundary and implementation guide agree;
- crash points have one specified recovery outcome before a live effect is added;
- all documented test commands are generated from executable configuration; and
- this report has a manifest classification before landing.

### Stage 1 — parser, taxonomy, and fake adapter

Build a no-network fake adapter that produces:

- valid approval/warning/block observations;
- no judgment;
- conflicting verdicts;
- malformed JSON/text;
- oversized output;
- timeout;
- cancellation;
- provider wrapper plus origin error; and
- missing/unknown usage.

Inject crashes:

- before provider dispatch;
- after a fake provider returns but before evidence commit;
- after evidence commit but before projection update; and
- between gate evaluation and permit issuance/consumption.

Pass:

- normalized records are deterministic;
- production and evaluation use the same parser;
- missing data remains missing;
- invalid observations cannot become gate passes;
- wrapper and origin are both retained;
- all failure states have typed retry policy;
- recovery never duplicates authority or loses a completed effect; and
- projections rebuild from canonical state.

### Stage 2A — common egress and native-provider boundary

Required before the first live provider call:

- data classification and provider/destination policy;
- explicit egress authorization;
- HUMAN GATE 9 cost, quota, credential-location, and adapter authorization;
- inherited-Hermes provider-seam inspection;
- minimal credential projection;
- no filesystem/tools by construction for the native adapter;
- provider-only network destination;
- response-byte and provider token limits;
- external deadline/cost reservation; and
- unknown usage/cost handling.

Test restricted packets, wrong destinations, missing approval, credential
enumeration, response bombs, identity mismatch, timeout, and unknown usage. Stage
3 cannot begin until this boundary passes.

### Stage 2B — tool-bearing CLI sandbox boundary

Test:

- minimal environment;
- credential projection;
- a filesystem namespace that hides the real home;
- read-only subject;
- outside/sibling/secret reads;
- symlink escapes;
- child processes;
- network policy;
- output and file-size caps;
- signal escalation; and
- no fallback to `none`.

Pass only when the kernel, not prompt compliance, enforces the boundary. This
stage is mandatory before Stage 4 or any other tool-bearing CLI adapter; it does
not block the tool-free native tracer once Stage 2A passes.

### Stage 3 — exact-subject native reviewer

After implementation-guide Phases 0–3, Stage 2A, and HUMAN GATE 9, use one locked
native provider without tools through an inherited-Hermes seam or justified
minimal adapter.

Pass:

- request and response bind to exact subject;
- actual response identity is captured;
- provider response variants are parsed;
- no implicit model change occurs;
- one deadline and cost budget bind;
- raw artifacts are retained under policy;
- observation cannot transition state; and
- deterministic gate/human flow works end to end.

### Stage 4 — optional pinned OCAsk adapter

Only after Stages 0–3:

- pin commit and executable digest;
- disable version check;
- isolate data home and hide the real home at the filesystem layer;
- disable panel and cross-verify;
- require a verified zero-retry/one-transport mode and complete attempt export;
  stock `--no-fallback` is insufficient;
- prohibit OpenCode transport initially;
- compare process exit, JSON descriptor, and metadata;
- enforce token/cost, output, and actual end-to-end deadline outside OCAsk;
- inject malformed/provider failure variants; and
- verify source/license provenance.

Pass when OCAsk is demonstrably replaceable and cannot bypass Ranex policy.

### Stage 5 — adversarial retry and concurrency

Exercise:

- simultaneous runs;
- provider timeout after submission;
- cancellation race;
- output bomb;
- log/artifact write failure;
- budget exhaustion;
- parser retry;
- route change;
- provider response identity mismatch;
- crash after provider response but before evidence commit; and
- recovery/reconciliation.

Pass when no hidden attempt, duplicate authority, cross-run event, or silent
degradation occurs.

### Stage 6 — repeated efficacy qualification

Use a frozen, provenance-backed, balanced, partly hidden corpus representing
Ranex task strata. Compare the arms listed earlier.

Require:

- predeclared thresholds;
- repeated paired trials;
- calibrated deterministic/model/human grading;
- FP, recall, abstention, consistency, latency, cost, and policy violations;
- transcript/artifact review;
- holdout protection;
- exact tuple identity; and
- an inconclusive result when power or completeness is inadequate.

Panel/lens promotion requires material net benefit over the best simpler arm.

### Stage 7 — operations and retirement

Prove:

- canarying;
- route health without test contamination;
- cost reconciliation;
- artifact retention;
- backup/restore;
- drift detection;
- model/provider change requalification;
- degraded-route alerting;
- explicit retirement; and
- rollback to the prior qualified tuple.

## Decision-ready recommendation

### Adopt now

At the design/research level:

- judgment/no-judgment distinction;
- abstention distinct from dissent;
- a Ranex-owned actual end-to-end deadline requirement, not OCAsk's partial
  implementation;
- the provider-factory typed outcome/attempt shape, promoted into complete Ranex
  records;
- originating failure preservation;
- entailment-based diagnosis;
- one product/eval parser;
- explicit test telemetry isolation;
- private atomic projection writes;
- explicit live-eval budgets;
- transparent negative evaluation;
- real-seam tests.

Also adopt the rule:

> A model may produce findings and propose evidence. It may not establish its own
> identity, capabilities, independence, qualification, or authority.

### Modify before implementation

- analytical transport interface;
- exact route identity;
- review and observation schemas;
- risk derivation;
- retry/fallback;
- budgets;
- cost accounting;
- telemetry;
- evidence storage;
- review-specification lifecycle;
- credentials;
- subject binding;
- evaluation harness;
- documentation generation; and
- license manifest.

### Defer

- any OCAsk executable integration;
- OCAsk OpenCode transport;
- panels;
- cross-verification;
- auto-risk;
- code-review and other lenses as defaults;
- two-step model verdict extraction;
- persistent OpenCode server;
- doctor/cost UI adaptation;
- PR #103 model-family changes;
- live provider claims;
- experimental orthogonal evidence axes;
- experimental anti-erosion obligations;
- `master` Intent Assurance implementation; and
- a Ranex drift guard.

### Reject

- wholesale source import;
- a required OCAsk plugin/installation;
- in-process OCAsk library use for the initial seam;
- model verdict as gate authority;
- exit zero as approval authority;
- current identity trust declarations as proof;
- prompt-only read-only policy;
- OpenCode allow-all and `--auto`;
- ambient full environment/home access;
- unbounded output;
- advisory `--max-tokens` treated as an enforced budget;
- current nested-provider timeout reuse treated as one end-to-end deadline;
- hidden same-model retries inside a Ranex product adapter;
- lexical-only path containment;
- opaque cross-family fallback;
- non-blind “independent” cross-verification;
- current panel/lens promotion;
- process-global run context;
- raw rationale logging;
- prompt hashes as provenance;
- rotating JSONL as a ledger;
- malformed-record skipping in canonical evidence;
- placeholder eval as qualification; and
- copied provider/model/pricing/timeout constants as kernel policy.

## Limitations

1. Ranex has no runtime. Every integration conclusion is architectural, not an
   interoperability result.
2. No paid provider call was made; current account, latency, model behavior,
   pricing, and entitlements were not tested.
3. OpenCode itself was not run under OCAsk in this study. The security conclusion
   follows source and official permission semantics, not a hostile runtime probe.
4. The source audit was deep but not a formal security audit.
5. GitHub administrative settings were unavailable.
6. Provider documentation and model contracts can change after the research date.
7. Open issues can contain accurate field evidence, stale evidence, or proposals;
   this report uses them only within those limits.
8. `master` is a separate history. Its documented Intent Assurance command was
   run, but the many red/adversarial fixtures were not individually adjudicated
   and the broader experimental lineage was not qualified as a product suite.
9. The experimental research contains private/local measurement references that
   cannot all be independently reproduced from the public repository.
10. The legal section is an engineering provenance recommendation, not legal
    advice.
11. Parallel reviewers in this session share the same working environment and do
    not constitute organizational or model-family independence.
12. This report does not update the implementation guide or licensing manifest.
    It remains unclassified for landing until a `CURATED_RESEARCH` manifest entry
    is added; the report records the other changes that should precede
    implementation.

## Local source register

### Ranex

- `RANEX_IMPLEMENTATION_GUIDE.md`
- `docs/research/cookbook-alignment-research-2026-07-27.md`
- `docs/research/gemini-research.md`
- `legal/licensing-manifest.json`
- Git revision `3844673b0bfa743de3c351566b6ffa9ffd67e0b8`

### OCAsk product source

- [Pinned repository tree](https://github.com/anthonykewl20/ocask/tree/340151fc6ef43958adaf15776cee93147c42aeda)
- [README](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/README.md)
- [Architecture](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ARCHITECTURE.md)
- [CLI and review engine](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.mjs)
- [Logging and diagnostics](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/logging.mjs)
- [Provider factory](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/factory.mjs)
- [DeepSeek provider](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/deepseek.mjs)
- [Qwen provider](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/qwen.mjs)
- [OpenCode provider](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/providers/opencode.mjs)
- [Paid verifier](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocverify.mjs)
- [Version check](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/version.mjs)
- [Installer](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/install.sh)
- [Sync check](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/check.sh)

### OCAsk tests and evaluation

- [Core tests](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/ocask.test.mjs)
- [Evaluation README](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/README.md)
- [Frozen baseline](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/baseline/frozen-baseline.json)
- [T07 micro-run report](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/reports/T07-microrun.md)
- [T08 baseline report](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/reports/T08-baseline-where-ocask-fails.md)
- [Corpus provenance status](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/corpus/VERIFIED.md)
- [Golden-fixture status](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/eval/golden/README.md)

### OCAsk research and governance

- [Committed research directory](https://github.com/anthonykewl20/ocask/tree/340151fc6ef43958adaf15776cee93147c42aeda/docs/research)
- [Contributing guide](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/CONTRIBUTING.md)
- [Security policy](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/SECURITY.md)
- [Changelog](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/CHANGELOG.md)
- [CI workflow](https://github.com/anthonykewl20/ocask/blob/340151fc6ef43958adaf15776cee93147c42aeda/.github/workflows/ci.yml)
- [Issue #78 — tiered routing and soft-output boundary](https://github.com/anthonykewl20/ocask/issues/78)
- [Issue #80 — two-step verdict extraction](https://github.com/anthonykewl20/ocask/issues/80)
- [Issue #92 — OpenCode DB pollution](https://github.com/anthonykewl20/ocask/issues/92)
- [Issue #93 — persistent server routing](https://github.com/anthonykewl20/ocask/issues/93)
- [Issue #94 — DeepSeek provider/output failures](https://github.com/anthonykewl20/ocask/issues/94)
- [Issue #95 — missing text baseline](https://github.com/anthonykewl20/ocask/issues/95)
- [Issue #104 — contributor/CI drift](https://github.com/anthonykewl20/ocask/issues/104)
- [Issue #123 — docs/tracker drift](https://github.com/anthonykewl20/ocask/issues/123)
- [Issue #124 — stale personal skill path](https://github.com/anthonykewl20/ocask/issues/124)
- [PR #103 — proposed Qwen retirement and hy3 promotion](https://github.com/anthonykewl20/ocask/pull/103)

### Divergent experimental lineage

- [Pinned `master` tree](https://github.com/anthonykewl20/ocask/tree/4e2778d1b0a72b527b5674e56ac5ef02183d8fef)
- [Intent Assurance specification](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/SPEC.md)
- [Experimental architecture](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/architecture.md)
- [Experimental decisions](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/DECISIONS.md)
- [T07 findings](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/T07-findings.md)
- [Drift-guard evidence ledger](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/drift-guard/LEDGER.md)
- [Prior-art and standards research](https://github.com/anthonykewl20/ocask/blob/4e2778d1b0a72b527b5674e56ac5ef02183d8fef/experimental/research/prior-art-and-standards.md)

## External primary and official sources

### Execution, security, and observability

- [OpenCode permissions](https://opencode.ai/docs/permissions)
- [DeepSeek Chat Completion API](https://api-docs.deepseek.com/api/create-chat-completion)
- [gRPC deadlines](https://grpc.io/docs/guides/deadlines/)
- [OpenTelemetry Context specification](https://opentelemetry.io/docs/specs/otel/context/)
- [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [MITRE CWE-61: UNIX symbolic link following](https://cwe.mitre.org/data/definitions/61.html)
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)

### Retry, evidence, and evaluation

- [Temporal Activity definition and idempotency](https://docs.temporal.io/activity-definition)
- [Temporal fixed-count retries](https://docs.temporal.io/design-patterns/fixed-count-retries)
- [in-toto Attestation Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
- [in-toto Test Result predicate](https://github.com/in-toto/attestation/blob/main/spec/predicates/test-result.md)
- [SLSA provenance v1.2](https://slsa.dev/spec/v1.2/provenance)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
