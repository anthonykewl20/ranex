# Hermes Initial Runtime Acceptance

| Field | Value |
|---|---|
| Review ID | `HERMES-INITIAL-RUNTIME-ACCEPTANCE-2026-07-28` |
| Status | `ACCEPTED_FOR_BOUNDED_LOCAL_USE` |
| Decision date | 2026-07-28 |
| Runtime | Hermes Agent `0.19.0` |
| Runtime source | `.claude/worktrees/phase-2-runtime-bootstrap` |
| Source base | `0533e1eaf50ace0eb84435a5c3de05e939fd4daa` |
| Initial accepted runtime patch snapshot | `sha256:897a35a1e21ea89a6b7372ac4f46a356776c286b7e05f1c21ea5e888df45b986` |
| Current editable worktree diff | 26 dirty paths; `sha256:e6d0a6f1c126b367feac641394ed190343416b19042d308f9e3b9981a94cf1b8` |
| Current bound first-party Python tree | 979 files, 31,142,489 bytes; `sha256:e00aac44b2f6d727cdbde217b896555dccc23be2c497679d5be78f78fd7d8969` |
| Root configuration | `sha256:d43c184bf245cc662b31cf2d95ca1bc7701740340526069492a8a04515d8c9b4` |
| Installed service subject | user systemd service, current PID `2517788` |
| Evidence roots | initial acceptance: `/home/soultransit/.local/share/ranex/evidence/2026-07-28-initial-runtime-acceptance`; thin automatic-routing delta: `/home/soultransit/.local/share/ranex/evidence/2026-07-28-thin-auto-routing-acceptance` |
| Initial evidence manifest | `sha256:0106063278a4668e6828abd24c19fbbc8867c3edbc41e0d6cb5bdec32cfd9716` |
| Thin-delta evidence manifest | 115 files; `SHA256SUMS` `sha256:33cba0dce59fab70fe4a06814b64a8c5b110473a06e1863f733346667eb12279` |
| Authority accepted | Local proposal-producing coordination only |
| Authority not accepted | Gate decisions, permits, state transitions, waivers, merge, deployment, release, or production readiness |

## 1. Decision

The installed Hermes runtime is accepted as Ranex's bounded, user-level local
office and proposal-producing coordinator.

It is not accepted as deterministic workflow authority. The separate
[gate-controller MVP audit](./2026-07-28-gate-controller-mvp-user-level-audit.md)
remains `PASS_WITH_BLOCKERS` for an R&D tracer and `REJECT` for live
authority. The human owner remains the only decision authority.

The initial evidence is bound to its patch snapshot. The thin-routing delta is
separately bound to the current first-party runtime tree, root configuration,
profile files, helper, lock manifest, systemd process, and evidence digests
named here. Neither acceptance transfers automatically to a later source edit,
configuration change, untested process restart, provider change, or network
exposure.

## 2. Accepted installed posture

### 2.1 Default and role routes

The ordinary user command `/home/soultransit/.local/bin/hermes` sets
`HERMES_HOME=/home/soultransit/.local/share/ranex` when the caller has not
already selected a home. Its mode is `0700`; the root configuration mode is
`0600`.

| Route class | Provider/model | Accepted use |
|---|---|---|
| Default office | `openai-codex/gpt-5.6-sol`, reasoning `max` | User-facing Hermes default |
| Sol roles | `openai-codex/gpt-5.6-sol`, reasoning `max` | Complex planning, office, customer testing, and temporary executive route |
| Routine roles | `zai/glm-5.2` | Supervisor, routine planning, operations, and release evidence |
| Inexpensive independent reviewer | `openrouter/tencent/hy3` | `reviewer-hy3`; HY3 is explicitly routed through OpenRouter |
| Challenger | `deepseek/deepseek-v4-flash` | Adversarial review |
| Escalation specialist | `deepseek/deepseek-v4-pro` | Bounded specialist review |
| Connected direct route | `opencode-go/glm-5.2` | Proved available; no standing worker profile is activated yet |

The coordinator now selects these role classes from the work's semantics. A
user does not need to name GLM, HY3, DeepSeek, a provider, a profile, or a
route. The main assistant prepares a bounded task packet and invokes the fixed
role helper. The helper, rather than the assistant, owns the locked
purpose-to-profile/provider/model/endpoint mapping.

The 12 named profiles are:

```text
challenger-v4-flash
customer-taster-sol
executive-opus
head-chef-glm
head-chef-sol
office-sol
ops-glm
release-clerk-glm
reviewer-hy3
specialist-v4-pro
supervisor-glm
supervisor-ranex
```

`executive-opus` is a retained historical profile name. Its effective route is
Sol, not Claude or Anthropic.

All 18 auxiliary provider/model assignments in every configuration scope are
explicitly pinned to Sol. The 16 ordinary auxiliary reasoning fields are
`max`. No nonempty fallback chain exists in the root or any named profile.

### 2.2 Conservative defaults

- MoA is dormant: the active preset is empty and the default preset is
  explicitly disabled.
- Its dormant references are OpenRouter HY3 and direct DeepSeek V4 Flash; its
  dormant aggregator is Sol. No Claude route exists.
- Missing, null, empty, malformed, and false preset activation values fail
  closed. Only a recognized explicit true value activates a preset.
- Explicit provider/model selection remains authoritative for vision;
  availability or execution failure cannot silently cross to another provider.
- Memory and user-profile persistence are off.
- Curator learning is off.
- Skill writes require approval and agent-created skills are guarded.
- Lazy installs are off.
- Plugins are empty.
- Named-profile delegation is off.
- Root delegation is a temporary, proposal-only harness limited to one child,
  depth one, no inherited MCP toolsets, and no automatic approval.
- Kanban auto-decomposition is off; work in progress and cron concurrency are
  bounded.
- Approvals are manual and cron approval is denied.
- Tirith is enabled at an exact path, times out after five seconds, and fails
  closed.

### 2.3 Copilot and GitHub

Hermes `copilot` and `copilot-acp` authentication both report `logged out`.
Credential-suppression tombstones are retained, and corrupt or unreadable
Hermes auth state fails closed instead of consulting GitHub CLI credentials.
Final explicit Copilot selections exited nonzero before any provider API call.

Ordinary GitHub CLI authentication remains intact. Disconnecting Hermes
Copilot did not remove the user's normal `gh` access.

The provider picker may still display the built-in, unconnected Copilot
capability with zero models. That metadata is not an authenticated or selected
route.

### 2.4 User service

`ranex-hermes-dashboard.service` is enabled and active as a user systemd
service. The current accepted process is PID `2517788`, with zero restarts
after the final service restart. It listens only on `127.0.0.1:9119`.
`HERMES_DASHBOARD_SESSION_TOKEN` is explicitly removed from the inherited
service environment so every process start generates fresh session state.

The health endpoint returns HTTP 200. The health payload currently reports
`auth_required:false`, but the raw Config API returns HTTP 401 without the
ephemeral dashboard session token and HTTP 200 with the authenticated SPA
session. This posture is accepted only for loopback use. Authentication and
threat modeling must be revisited before any non-loopback exposure.

## 3. Rules, skills, and foundational engineering practices

The root SOUL and every named role SOUL apply:

1. the accepted Core SDLC;
2. the full-system architecture and accepted ADRs;
3. the [Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md);
4. evidence-bound verification, negative cases, explicit contracts,
   readable/cohesive construction, reversible slices, and professional
   escalation; and
5. the rule that model output is a proposal, never gate authority.

The six saved reference works were confirmed present, ignored, and untracked:

```text
docs/research/books/clean-code.md
docs/research/books/code-complete.md
docs/research/books/swebok-v4.md
docs/research/books/system-design-interview.md
docs/research/books/The Clean Coder-A Code of Conduct for Professional Programmers.md
docs/research/books/the-pragmatic-programmer.md
```

The licensing manifest classifies them as `CURATED_RESEARCH`, `NOASSERTION`,
`LOCAL_ONLY`, and `PROHIBITED_PENDING_RIGHTS`. They guide original Ranex
practice synthesis but cannot enter a public package or release.

The former `RANEX_IMPLEMENTATION_GUIDE.md` is physically absent and recorded
as a deletion in all five worktrees. [ADR-0002](../decisions/ADR-0002-retire-legacy-implementation-guide.md)
prohibits restoring, reconstructing, or using it as implementation input.
Historical manifests and reviews retain truthful provenance only.

This does **not** claim that the complete rules-and-skills system is already
machine enforced. Current role guidance is correctly installed for bounded
coordination, while automatic learning and unreviewed skill promotion are
disabled. `AI-G2` must still implement and validate:

- `engineering-practices.yaml`;
- `EngineeringPracticeProfileV1`;
- role/stage/project/technology/risk/trigger activation manifests;
- executable schemas and semantic validators; and
- deterministic transition gates outside agent reasoning.

Until then, book-derived practices and SOUL rules are guidance with observable
tests, not hard authority.

## 4. User-level and independent evidence

| Check | Result | Bound evidence |
|---|---|---|
| Exact hardening regression suite | 1,049 passed, 0 failed; Ruff and diff checks clean | Runtime patch `897a35a1…df45b986` |
| Independent adversarial patch audit | 49 passed, 0 failed; all seven prior bypass classes closed; no HIGH/MEDIUM finding | `runtime/independent-patch-audit-final.json`, `sha256:8aff13a1319a60345ae6f8d3fc7f61ad576ee32b42b891df1fa3f055e0b46fc5` |
| Malformed MoA activation through installed CLI | Missing/null/empty/garbage/false denied, exit 1, zero API calls; true observed enabled without inference | `runtime/moa-enabled-user-probe-final.jsonl`, `sha256:f3cbd9f6856ee582d9336ec0b377fa792cc6c527114af090aa2894515eeaaab5` |
| Plain `hermes` with `HERMES_HOME` unset | Exact marker returned through `openai-codex/gpt-5.6-sol`; one real API call | response `sha256:d2bab1b794a45f8ff533597030959fe46c70be780ad866195e26daa2cf55571a`; usage `sha256:102eb40a320ef174e81df532ec3ab6f2532407feb537ba1db9b8300a0a738392` |
| Frozen real route matrix | 14/14 accepted routes, 14 API calls, 14/14 ended sessions, zero tool calls/events, all proposed `DENY`, all denied self-issued permits | `routes-frozen-897a35a1/validation.json`, `sha256:61474fbb265ba3e0020333c52166d09d75f20fad861590be0c8a9613b917ccc1` |
| Browser acceptance | 24/24 assertions; 59/59 browser responses HTTP 200; zero console/page/request/application errors; protected raw API 401 | `browser/final-pid-2201252/acceptance.json`, `sha256:40e399d98d9928a7a21c269640059a33acfca36953911c7dadfd4d0378ec819e` |
| Configuration and auth | 13/13 config checks; 13/13 empty fallback chains; both Copilot routes logged out | `runtime/final-config-auth-status.txt`, `sha256:9da3b3d1ede88027480ce2e8c5deb9a8cc2dfee0af159d0087d41329b6fba96f` |
| Explicit disabled MoA | Nonzero exit with typed disabled error and zero API calls | `runtime/moa-disabled-explicit-final.*` |
| Explicit Copilot routes | Both nonzero before inference; no API call; ordinary `gh` retained | `runtime/copilot-explicit-final.*`, `runtime/copilot-acp-explicit-final.*` |
| Tirith | Safe command accepted; `curl | bash` rejected with HIGH finding | `runtime/tirith-safe-final.json`, `runtime/tirith-block-final.json` |
| Final systemd runtime | PID `2201252`, active/running, enabled, zero restarts, loopback listener, health 200, protected Config 401 | `runtime/final-live-status.txt`, `sha256:ca8e6d0122dab56be59be80ebeaad98195e0b454442d55c9cbccdb2ba73f0ae1` |
| Independent model review | HY3 via OpenRouter and DeepSeek V4 Flash both `ACCEPT_WITH_FINDINGS`; no actionable HIGH/MEDIUM finding or hidden route; zero tools | `reviews/final-advisory/reconciled-verdict.md`, `sha256:6767aafd1c9bba897770aec92d22cceb63f0a8898ed308c885e3c5aa2b440533` |
| Evidence credential scan | 492 manifest entries; five credential-pattern families; zero matches | `SECRET_SCAN.json`, `sha256:861c0b21e0cc9719c807790a440e665d1abaa8557d6646dacab6dbaf551a1523` |

The accepted route set used 59,661 tokens. One release-clerk attempt
conservatively refused to express `transition: DENY` because it interpreted
that field as authoritative. A fresh prompt clarified that the response was
only a non-authoritative recommendation and passed. Both attempts are retained;
the complete 15-call total was 63,353 tokens with estimated cost
`$0.002134531`.

The final advisory reviews used the same packet and made one real call each:

| Reviewer | Actual route | Session | Total tokens | Estimated cost |
|---|---|---|---:|---:|
| HY3 | `openrouter/tencent/hy3` | `20260728_030524_d122d3` | 5,155 | `$0.0014993880` |
| Challenger | `deepseek/deepseek-v4-flash` | `20260728_030524_3316cf` | 5,373 | `$0.0010136952` |

Both explicitly stated that their reviews grant no permit, transition, waiver,
merge, deployment, release, or other authority.

## 5. Backup and recovery evidence

The supported full backup command produced:

```text
/home/soultransit/.local/share/ranex-backups/post-initial-hermes-config-2026-07-28.zip
sha256:a9f06d5757d7e583be1eed18cb18d6b190963ea03664b725b5421c462738eec4
mode: 0600
members: 1341
compressed size: 107345071 bytes
```

All ZIP members passed CRC validation. A real `hermes import --force` into an
isolated temporary `HERMES_HOME` restored 1,339 files, after the importer
correctly preserved two machine-runtime state files. The restored root config
was byte-identical, all 12 profile config/SOUL hash sets matched, the runtime
patch matched, Sol/`max` remained selected, both Copilot routes remained logged
out, and `hermes config check` passed. The temporary restore was then removed.

Restore transcript:
`runtime/post-backup-restore-test.txt`,
`sha256:baf460c54ab2165787f3287c744fb7746b347c7848028e4868ac68de17abf222`.

Hermes backup intentionally excludes the codebase. The user launcher and
systemd unit also live outside `HERMES_HOME`. A full machine recovery therefore
still requires:

1. an installed compatible Hermes codebase;
2. the saved runtime patch or a future commit containing it;
3. the user launcher;
4. the user systemd unit; and
5. the Hermes backup archive.

The thin automatic-routing delta also produced:

```text
/home/soultransit/.local/share/ranex-backups/post-thin-auto-routing-2026-07-28.zip
sha256:37838676f43a39f19c97e772bd6ad50183fc218eec25e731f1b1fe1f321a7009
mode: 0600
members: 1517
compressed size: 110734089 bytes
```

An empty-directory import with isolated temporary `HOME` and `HERMES_HOME`
passed ZIP path, symlink, CRC, required-file, hash, sensitive-mode,
configuration, and 22 SQLite integrity checks. The 55 required thin
configuration and role files were byte-identical before and after import.

Two restore qualifications are explicit. Hermes import restores the role
helper as `0600`, so recovery must restore its `0700` executable mode. The
helper also contains active-install absolute paths; its `--check` therefore
cannot be counted as restored-state proof. The archive is a private
configuration/state snapshot, not a standalone Hermes runtime.

## 6. Known limitations and non-claims

1. The hardened runtime source is an uncommitted patch over the named base
   commit. It is installed and tested, but not yet durable repository history.
2. The dashboard is accepted only on loopback. Its health metadata says
   `auth_required:false` even though protected routes enforce an ephemeral
   session.
3. Root's one-child/depth-one delegation is inherited transitional machinery,
   not qualified Ranex fleet control.
4. The provider picker can show unselected built-in Anthropic or Copilot
   metadata. Selected and configured routes contain neither.
5. `executive-opus` is a misleading historical name whose actual route is
   Sol.
6. OpenCode Go was real-call tested but has no standing role profile; activating
   another worker before deterministic authority would violate least
   authority.
7. The dashboard schema view omits one auxiliary
   `memory_query_rewrite` effort field even though authenticated configuration
   inspection proves it is `max`.
8. Historical session cards may describe earlier automatic routes. They are
   history, not the current configuration.
9. External provider availability, pricing, and behavior can change. A later
   acceptance must execute fresh route evidence.
10. No broad claim such as secure, production-ready, fully tested, or complete
    is made.
11. Automatic semantic selection is accepted for the representative GLM
    planning and HY3-plus-DeepSeek review paths executed below. It is not proof
    that every future natural-language request will be classified correctly.
12. Role receipts are local, unsigned, and same-user mutable. They bind local
    effective configuration and persisted response accounting, not remote
    provider-account identity.
13. One-shot parent CLI sessions persist a final assistant `stop` and complete
    usage but remain resumable, with null session-level `ended_at` and
    `end_reason`. Child role sessions close normally.
14. The dashboard requests Google Fonts. The final browser acceptance blocked
    those stylesheet requests before transmission and proved the UI works
    without them; removing the external dependency remains future product
    hardening.
15. Backup/import does not preserve the role helper's executable bit and is not
    a standalone runtime recovery mechanism.

## 7. Thin automatic-routing acceptance delta

The thin configuration is accepted for bounded Ranex development. It does not
require the user to remind the main assistant which connected model should
perform a role.

| Semantic work class | Fixed purpose | Effective role |
|---|---|---|
| Routine bounded planning | `ROUTINE_PLAN` | GLM through `zai/glm-5.2` |
| Material technical review | `TECH_REVIEW` | HY3 through `openrouter/tencent/hy3` |
| Independent adversarial challenge | `ADVERSARIAL_CHALLENGE` | DeepSeek through `deepseek/deepseek-v4-flash` |
| Deep specialist escalation | `SPECIALIST_ESCALATION` | DeepSeek through `deepseek/deepseek-v4-pro` |

The installed catalog contains 11 fixed purposes. The main assistant may choose
a purpose from task semantics, but it cannot choose a provider/model override.
The private lock manifest pins every profile config, role SOUL, credential
identity, endpoint, helper/runtime identity, and selected first-party runtime
tree. A changed lock, profile, credential identity, endpoint, runtime file, or
transport override fails closed before a child call.

Two clean main-assistant conversations supplied no model, provider, profile,
purpose, or helper reminder:

1. Parent `20260727_211436_c9e8bb`, running
   `openai-codex/gpt-5.6-sol` at `max`, selected `ROUTINE_PLAN` and obtained one
   GLM response.
2. Parent `20260727_211710_f7c5b6`, running the same Sol route, selected
   `TECH_REVIEW` followed by `ADVERSARIAL_CHALLENGE` and obtained independent
   HY3/OpenRouter and DeepSeek responses in that order.

The validator reconstructed every parent tool call/result ID and name, required
the terminal calls to use only the fixed helper, matched the exact persisted
user prompts and final assistant responses, and reconciled each child packet,
response, usage record, session, endpoint, helper hash, manifest hash, and
before/after integrity snapshot.

| Delta check | Result | Bound evidence |
|---|---|---|
| Automatic no-reminder selection | `PASS`; Sol/max parent, GLM planning, HY3 technical review, DeepSeek challenge; exact order and full tool/session reconciliation | `automatic/automatic-validation-final.json`, `sha256:47818b854c2de35740d0f551daa06347bda144851bea7b94d42f6270561ae779` |
| Current helper and lock manifest | 11/11 routes `PASS`; 979-file first-party runtime tree covered; independent mutation and Python startup-hook probes passed | helper `sha256:5d9d7fc41ce401f52884c3e552015069c9b6cc06ad0bbc9fbbf0a2cb7106fb04`; manifest `sha256:81cd5e0b98b638aae400f83581ec8e16dcdc50f1751c32f0ae4506e5fa575a69` |
| Static installed posture | `PASS`; 13 configuration scopes, valid routing skill, no fallback, memory and MoA off, 12 exact profiles, both Copilot routes logged out, service loopback/active | `static/static-validation-final.json`, `sha256:893a9771ec1e3b683127f8e894fa77a782dd27e640b3cbdc3980665e1a91e090` |
| Hardened browser acceptance | 29/29; exact full profile contract; no unexpected console/page/request/HTTP error, mutation, session-token persistence, or non-loopback response | `browser/hardened-final-pid-2517788/acceptance.json`, `sha256:17459e2b809f8c43c244ee74c1a2a9c851570ce799870cb65b5b7b895e1f45b7` |
| Backup/import | `PASS`; 1,517 members, 55 required files hash-identical, 22 SQLite databases intact; explicit executable/runtime qualifications | `backup/restore-validation.json`, `sha256:bd55d2cb37af030be47d10a0f387ad6a84b75971179e515d4ccbae30be0aa6a2` |
| Independent audits | Local hardening, receipt/provenance, and forward-policy reviewers passed; live HY3 and DeepSeek observations remained non-authoritative | `INDEPENDENT_AUDITS.md`, `sha256:c7d878fea8c24ee14c23927cbb83aefd9f4d8590371039463e276d9273c7350e` |
| Final user service | PID `2517788`, enabled, active/running, zero restarts, loopback only, health 200, raw Config 401, inherited dashboard token unset | unit `sha256:b10ff8b48f889ebf6900251488f5e416400f833bc34d38bbc76d651a17c3ea84` |

This proves actual responses and locally effective routes. It does not turn an
agent or its receipt into workflow authority.

## 8. What comes next

Yes: clear the authority-bearing architectural fog before implementing more
gate code. Do not reopen every settled design choice. Run one bounded sprint:

```text
AUTHORITY-KERNEL-CONTRACT-CLOSURE
```

The ordered exit criteria are:

1. Create an exact, content-addressed `ArchitectureSubjectV1`.
2. Accept one ownership/transition ADR: `work_management` owns
   `WorkItemStatus`; `governed_execution` owns runs, gates, grants, permits,
   and effects; `process_assurance` owns evidence/checkers; policy and the
   human owner retain decisions.
3. Freeze canonical registries for identifiers, states, roles, paths,
   capabilities, owners, namespaces, enforcement levels, source precedence,
   and engineering practices. `CHECKER_FAULT` must exist; `R_AND_D` cannot
   activate authority; discarded owner metadata is prohibited.
4. Implement the `AI-G2` schemas, semantic validators, RFC 8785/SHA-256 golden
   vectors, and cross-language Python/TypeScript canonicalization parity.
5. Specify trusted, authenticated evidence collectors and claim-specific
   validators. Agent-authored evidence remains a proposal.
6. Separate privileged bootstrap/import from normal work registration and
   place the ledger integrity root outside the writer's rewrite boundary.
7. Build a black-box negative acceptance pack and one sealed task packet for
   exactly `IN_PROGRESS -> VERIFICATION`.

Only after those seven criteria pass should Ranex implement and independently
accept one truthful vertical authority tracer. More gates, deeper fleet
concurrency, release automation, or provider-interface expansion are out of
scope for that sprint.

The next truthful milestone is:

```text
Authority contracts ready for one bounded tracer.
```

It is not:

```text
Ranex workflow authority is live.
```
