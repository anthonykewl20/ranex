[0m
> build · tencent/hy3
[0m
[0m✱ [0mGlob "**/*"[90m 100 matches[0m
[0m
[0m$ [0mls; echo ---; ls docs; echo ---; ls docs/architecture/decisions docs/research 2>/dev/null
architecture
decisions
docs
legal
LICENSE
LICENSE-RANEX.md
NOTICE.md
README.md
schemas
scripts
---
architecture
HANDOFF.md
README.md
research
---
docs/architecture/decisions:
ADR-0001-established-sdlc-governs-ai-work.md
ADR-0002-retire-legacy-implementation-guide.md
ADR-0003-accept-target-architecture-and-authority-kernel.md
ADR-0004-establish-initial-quality-attribute-baselines.md
ADR-0005-select-local-static-orchestration-defaults.md
ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md
ADR-0007-establish-modular-ddd-repository-organization.md
ADR-0008-make-tdd-the-default-development-discipline.md
ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md
ADR-0010-bound-inherited-hermes-test-layout-migration.md
ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md
ADR-0012-separate-implementation-start-and-production-readiness.md
ADR-0013-promote-hermes-research-obligations.md
ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md

docs/research:
aposd-agent-rules-codebase-design-assessment-2026-07-28.md
books
cookbook-alignment-research-2026-07-27.md
deterministic-run-graph-visualization-research-2026-07-30.md
engineering-reference-practice-registry.json
gemini-research.md
hermes-core-architecture-hy3-review-2026-07-27.md
hermes-core-architecture-research-2026-07-27.md
kimi-research
ocask-alignment-research-2026-07-27.md
ranex-architecture-practice-application-profile.json
ranex-sdlc-full-spec.svg
ranex-sdlc-visual-guide.html
ranex-sdlc-visual-hy3-review-2026-07-27.md
README.md
real-world-sdlc-operating-model-research-2026-07-27.md
reviewer-model-capability-probe-2026-07-30.md
[0m
[0m→ [0mRead README.md
[0m→ [0mRead docs/README.md
[0m
[0m$ [0mls architecture decisions scripts scripts/architecture 2>/dev/null; echo ---; ls docs/architecture
architecture:
contracts
records

decisions:
local-values.env
local-values.env.example

scripts:
architecture

scripts/architecture:
contract_tree_lock.py
generate_contracts.py
__pycache__
pyproject.toml
README.md
test_contract_concurrency.py
uv.lock
validate_contracts.py
---
AI_AGENT_DEVELOPMENT_LIFECYCLE.md
AI_AGENT_FLEET_CONTROL_PLANE.md
AI_ARTIFACT_CONTRACTS.md
assessments
CORE_SDLC_OPERATING_MODEL.md
decisions
ENGINEERING_REFERENCE_APPLICATION_MAP.md
HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
README.md
reviews
rfcs
SDLC_CONTROL_CATALOG.md
SOURCE_OF_TRUTH.md
templates
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
[0m
[0m$ [0mwc -l docs/architecture/decisions/*.md docs/architecture/*.md; echo ---; ls architecture/contracts architecture/records; echo ---; cat decisions/local-values.env.example; echo ---; cat decisions/local-values.env 2>/dev/null | head -50
195 docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md
    196 docs/architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md
    157 docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md
    166 docs/architecture/decisions/ADR-0004-establish-initial-quality-attribute-baselines.md
    132 docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md
    327 docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md
    387 docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
   1798 docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md
    355 docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md
   1917 docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
    543 docs/architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md
    900 docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md
   1187 docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
    236 docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
    723 docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md
   1264 docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md
    689 docs/architecture/AI_ARTIFACT_CONTRACTS.md
    899 docs/architecture/CORE_SDLC_OPERATING_MODEL.md
    671 docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md
   4198 docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
    409 docs/architecture/README.md
   2172 docs/architecture/SDLC_CONTROL_CATALOG.md
    878 docs/architecture/SOURCE_OF_TRUTH.md
  20399 total
---
architecture/contracts:
accepted-adrs.json
applicability-rules.json
architecture-element-assessments.json
architecture-elements.json
architecture-rule-assessments.json
artifact-types.json
context-boundary-fitness.json
context-coupling-policy.json
context-dependency-edges.json
contexts.json
data-ownership.json
decisions.json
effects.json
engineering-practice-profiles.json
engineering-practices.json
estimate-commitment-control.json
events.json
feedback-fitness.json
generated-output-authority.json
hermes-research-promotions.json
identities.json
legacy-test-direct-source-classifications.json
legacy-test-layout-policy.json
legacy-test-layout-policy-v1.json
legacy-test-layout-policy-v2.json
legacy-test-layout-records.json
legacy-test-layout-records-v1.json
legacy-test-layout-records-v2.json
paths.json
priority-rules.json
readiness-assessments.json
readiness-tiers.json
registry-manifest.json
runtime-adapters.json
schema-registry.json
states.json
tdd-cycle-records.json
tdd-exception-records.json
test-behaviors.json
test-deletion-records.json
test-practice-profiles.json
test-practices.json
test-quarantine-records.json
topology-rules.json
vital-profile.json
worker-role-profiles.json

architecture/records:
legacy-test-layout
test-governance
test-health
---
# Copy this file to decisions/local-values.env and validate every value before
# running repository-adoption or local-environment commands. Never commit the
# local copy.

BRAND_NAME="Ranex"
BRAND_SHORT_NAME="Ranex"
BRAND_SLUG="ranex"
BRAND_CLI="ranex"
BRAND_ENV_PREFIX="RANEX"

GITHUB_OWNER="anthonykewl20"
ORIGIN_REPO_NAME="ranex"
GITHUB_VISIBILITY="public"
GITHUB_NETWORK_FORK="false"

SOURCE_PARENT="$HOME/devtony"
SOURCE_DIR="$SOURCE_PARENT/$BRAND_SLUG"
PROJECTS_ROOT="$HOME/devtony"
EVALUATION_REPO="$PROJECTS_ROOT/ranex-evaluation"
APP_HOME="$HOME/.local/share/$BRAND_SLUG"
STATE_HOME="$HOME/.local/state/$BRAND_SLUG"
CACHE_HOME="$HOME/.cache/$BRAND_SLUG"
DEV_VENV="$HOME/.local/share/$BRAND_SLUG/venvs/dev"

UPSTREAM_REPO="https://github.com/NousResearch/hermes-agent.git"
ORIGIN_REPO="https://github.com/$GITHUB_OWNER/$ORIGIN_REPO_NAME.git"

DEFAULT_BRANCH="main"
DEVELOP_BRANCH="develop"
UPSTREAM_SYNC_BRANCH="upstream-sync"

OWNER_TIMEZONE="Asia/Manila"
---
# Local, noncommitted values validated for this host on 2026-07-27.

BRAND_NAME="Ranex"
BRAND_SHORT_NAME="Ranex"
BRAND_SLUG="ranex"
BRAND_CLI="ranex"
BRAND_ENV_PREFIX="RANEX"

GITHUB_OWNER="anthonykewl20"
ORIGIN_REPO_NAME="ranex"
GITHUB_VISIBILITY="public"
GITHUB_NETWORK_FORK="false"

SOURCE_PARENT="/home/soultransit/devtony"
SOURCE_DIR="/home/soultransit/devtony/ranex"
PROJECTS_ROOT="/home/soultransit/devtony"
EVALUATION_REPO="/home/soultransit/devtony/ranex-evaluation"
APP_HOME="/home/soultransit/.local/share/ranex"
STATE_HOME="/home/soultransit/.local/state/ranex"
CACHE_HOME="/home/soultransit/.cache/ranex"
DEV_VENV="/home/soultransit/.local/share/ranex/venvs/dev"

UPSTREAM_REPO="https://github.com/NousResearch/hermes-agent.git"
ORIGIN_REPO="https://github.com/anthonykewl20/ranex.git"

DEFAULT_BRANCH="main"
DEVELOP_BRANCH="develop"
UPSTREAM_SYNC_BRANCH="upstream-sync"

OWNER_TIMEZONE="Asia/Manila"
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md
[0m→ [0mRead docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md
[0m→ [0mRead docs/architecture/decisions/ADR-0004-establish-initial-quality-attribute-baselines.md
[0m→ [0mRead docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
[0m→ [0mRead docs/architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md
[0m→ [0mRead docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md
[0m
[0m$ [0mrg -n "HERMES-OWNER-DECISION" docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | head -40
114:It also adds `HERMES-OWNER-DECISION-020` as an
823:  - provision_id: "HERMES-OWNER-DECISION-001"
835:  - provision_id: "HERMES-OWNER-DECISION-002"
847:  - provision_id: "HERMES-OWNER-DECISION-003"
859:  - provision_id: "HERMES-OWNER-DECISION-004"
871:  - provision_id: "HERMES-OWNER-DECISION-005"
883:  - provision_id: "HERMES-OWNER-DECISION-006"
895:  - provision_id: "HERMES-OWNER-DECISION-007"
907:  - provision_id: "HERMES-OWNER-DECISION-008"
919:  - provision_id: "HERMES-OWNER-DECISION-009"
931:  - provision_id: "HERMES-OWNER-DECISION-010"
943:  - provision_id: "HERMES-OWNER-DECISION-011"
955:  - provision_id: "HERMES-OWNER-DECISION-012"
967:  - provision_id: "HERMES-OWNER-DECISION-013"
979:  - provision_id: "HERMES-OWNER-DECISION-014"
991:  - provision_id: "HERMES-OWNER-DECISION-015"
1003:  - provision_id: "HERMES-OWNER-DECISION-016"
1015:  - provision_id: "HERMES-OWNER-DECISION-017"
1027:  - provision_id: "HERMES-OWNER-DECISION-018"
1039:  - provision_id: "HERMES-OWNER-DECISION-019"
1051:  - provision_id: "HERMES-OWNER-DECISION-020"
1150:| `FF-HERMES-OWNER-DECISION-001` | Every genuine owner choice is `OWNER_DECISION_REQUIRED`, has no default or synthetic decision reference, and blocks activation or progression while the exact accepted owner decision is absent. |
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md[90m [offset=760, limit=330][0m
[0m
[0m$ [0mrg -n -i "pytest|hypothesis\b|unittest" docs/architecture scripts --include-zero -g '!*reviews*' | head -30; echo ===; rg -n -i "\buv\b|pyproject|pip\b" docs/architecture -g '!*reviews*' | head -30; echo ===; rg -n -i "ruff|mypy|pyright|pyrefly|type check" docs/architecture -g '!*reviews*' | head -30
docs/architecture/SDLC_CONTROL_CATALOG.md:1779:A linked improvement record names causal stage/control, hypothesis, bounded
docs/architecture/SDLC_CONTROL_CATALOG.md:1890:| `SDLC-DIS-001` `DISCOVERY` | Validate problem/value; triaged item | Signal, users/actors, current behavior, research access | Research current behavior/users, baseline, alternatives, hypothesis, unknowns and falsifier | Discovery packet and evidence register | Research/product / product owner / technical, service, data / stakeholders | Evidence/source/unknown checks + product decision | Weak evidence → Discovery/Funnel/Cancelled | Standard fixes may use reproduction as discovery; measure learning time/hypothesis yield | `PRAC`,`OBS`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1899:| `SDLC-OUT-001` `OUTCOME_REVIEW` | Decide whether change helped; observation due | Hypothesis/baseline, product and ops evidence | Compare expected/actual, side effects and segments; decide keep/change/remove | Outcome decision and follow-up work | Product analytics / product owner / technical, service, users / portfolio | Data-quality check + human product decision | Falsified → `DISCOVERY` or linked `MAINTENANCE`/`RETIREMENT` work | Sampled only for standard lane; outcome/side-effect measures | `OBS`,`PRAC`,`OWNER` |
scripts/architecture/generate_contracts.py:14732:        "title": "Ranex context boundary-fit hypothesis",
scripts/architecture/generate_contracts.py:14738:            "consistency_hypothesis": nonempty,
scripts/architecture/generate_contracts.py:14739:            "failure_hypothesis": nonempty,
scripts/architecture/generate_contracts.py:14740:            "ownership_hypothesis": nonempty,
scripts/architecture/generate_contracts.py:14741:            "change_locality_hypothesis": nonempty,
scripts/architecture/generate_contracts.py:14757:            "consistency_hypothesis",
scripts/architecture/generate_contracts.py:14758:            "failure_hypothesis",
scripts/architecture/generate_contracts.py:14759:            "ownership_hypothesis",
scripts/architecture/generate_contracts.py:14760:            "change_locality_hypothesis",
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:20:Ranex records boundary quality as a falsifiable hypothesis, not as a conclusion
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:164:Each row is a design hypothesis. `merge_candidate` and `split_candidate` are
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:177:  - {context_id: "governed_execution", owner: "governed_execution", consistency_hypothesis: "One atomic run/transition/grant/permit/effect-intent transaction.", failure_hypothesis: "Failure halts privileged continuation and preserves replayable intent.", ownership_hypothesis: "Only this context owns run and execution authority.", change_locality_hypothesis: "Authority semantics change here; policy/evidence semantics remain in their owners.", merge_candidate: "none unless authority and policy become one consistency boundary", split_candidate: "effect ledger or process manager after a coupling trigger", tracer_falsifier: "crash/replay/permit reuse or a change requiring private knowledge from three owners"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:178:  - {context_id: "policy", owner: "policy", consistency_hypothesis: "One versioned policy/risk/decision snapshot.", failure_hypothesis: "Unavailable or malformed policy denies privileged continuation.", ownership_hypothesis: "Only policy owns eligibility/risk/waiver meaning.", change_locality_hypothesis: "Rule changes avoid execution-state edits.", merge_candidate: "identity_access only if policy and identity lifecycle prove inseparable", split_candidate: "policy package evaluation from human-decision records", tracer_falsifier: "one rule change repeatedly modifies governed_execution internals"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:179:  - {context_id: "assurance", owner: "assurance", consistency_hypothesis: "One exact-subject evidence snapshot and GateEvaluation.", failure_hypothesis: "Stale/missing/conflicting proof remains UNKNOWN and blocks.", ownership_hypothesis: "Only assurance converts eligible evidence into gate evaluation.", change_locality_hypothesis: "Checker/evidence changes avoid run-state edits.", merge_candidate: "qualification only if evidence and qualification lifecycle cannot be separated", split_candidate: "evidence catalog from gate evaluation after independent scaling pressure", tracer_falsifier: "wrong-subject or stale evidence can authorize a transition"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:180:  - {context_id: "module_governance", owner: "module_governance", consistency_hypothesis: "One module descriptor/grant/activation version.", failure_hypothesis: "Unknown or incompatible module remains inactive.", ownership_hypothesis: "Only this context owns module catalog and activation.", change_locality_hypothesis: "Module lifecycle changes avoid worker/run authority edits.", merge_candidate: "extension_host only if first- and third-party lifecycle converge", split_candidate: "catalog from activation after lifecycle divergence", tracer_falsifier: "import registration activates an undeclared module"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:181:  - {context_id: "identity_access", owner: "identity_access", consistency_hypothesis: "One authenticated principal/session/destination-fact snapshot.", failure_hypothesis: "Authentication or secret resolution failure denies access/effect.", ownership_hypothesis: "Only this context owns identity/session/secret handles.", change_locality_hypothesis: "Authentication changes do not alter policy rules.", merge_candidate: "policy only if lifecycle evidence demands it", split_candidate: "secret projection from authentication after security/isolation trigger", tracer_falsifier: "a stale session or raw secret crosses a public boundary"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:182:  - {context_id: "product_definition", owner: "product_definition", consistency_hypothesis: "One requirement/acceptance/outcome baseline.", failure_hypothesis: "Conflicting or unapproved need remains unresolved work input.", ownership_hypothesis: "Only this context owns product intent and acceptance meaning.", change_locality_hypothesis: "Requirement changes propagate by trace rather than private imports.", merge_candidate: "work_management only if intent and execution status cannot vary independently", split_candidate: "outcome validation from requirements after ownership divergence", tracer_falsifier: "work status silently changes product acceptance"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:183:  - {context_id: "work_management", owner: "work_management", consistency_hypothesis: "One canonical work item/status/queue transaction.", failure_hypothesis: "Invalid transition leaves work unchanged and auditable.", ownership_hypothesis: "Only this context owns WorkItemStatus and work queues.", change_locality_hypothesis: "Workflow changes avoid product/run state mutation.", merge_candidate: "product_definition only if discovery and delivery lifecycle collapse", split_candidate: "portfolio/queue projection from transactional work state", tracer_falsifier: "another context writes work status or a board becomes authority"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:184:  - {context_id: "service_management", owner: "service_management", consistency_hypothesis: "One service/objective/support lifecycle record.", failure_hypothesis: "Missing owner/SLO/support fact blocks release/operation decision.", ownership_hypothesis: "Only this context owns service catalog and objectives.", change_locality_hypothesis: "SLO/support changes avoid incident/release implementation edits.", merge_candidate: "operations only if service definition and incident state cannot diverge", split_candidate: "objective/error-budget policy from service catalog", tracer_falsifier: "release or operations invents its own service owner/SLO"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:185:  - {context_id: "configuration_management", owner: "configuration_management", consistency_hypothesis: "One content-addressed baseline/status-accounting transaction.", failure_hypothesis: "Digest/trace/audit mismatch blocks use.", ownership_hypothesis: "Only this context owns configuration baselines and trace graph.", change_locality_hypothesis: "New configuration item types avoid consumer-specific rules.", merge_candidate: "none; cross-cutting baseline authority remains explicit", split_candidate: "contract generation from baseline/audit after independent change pressure", tracer_falsifier: "two canonical paths or mutable baseline identity appear"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:186:  - {context_id: "supplier_governance", owner: "supplier_governance", consistency_hypothesis: "One supplier adoption/support/exit decision.", failure_hypothesis: "Unknown support/vulnerability/concentration blocks adoption or release.", ownership_hypothesis: "Only this context owns supplier acceptance and exit policy.", change_locality_hypothesis: "Supplier changes avoid route/release private rules.", merge_candidate: "provenance_compliance only if adoption and legal decisions share lifecycle", split_candidate: "monitoring from adoption decisions after cadence divergence", tracer_falsifier: "routing activates an unapproved supplier"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:187:  - {context_id: "resource_governance", owner: "resource_governance", consistency_hypothesis: "One hierarchical reservation/usage settlement transaction.", failure_hypothesis: "Capacity/budget ambiguity denies new allocation and reconciles usage.", ownership_hypothesis: "Only this context owns budgets, quotas, and usage attribution.", change_locality_hypothesis: "Budget rules change without worker/run state rewrites.", merge_candidate: "agent_collaboration only if leases and resource reservations prove one aggregate", split_candidate: "rate/usage catalog from reservations", tracer_falsifier: "child work exceeds parent reservation or usage lacks attribution"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:188:  - {context_id: "interaction_history", owner: "interaction_history", consistency_hypothesis: "One classified thread/message/retention append.", failure_hypothesis: "Failed append/access/delete remains explicit and retryable.", ownership_hypothesis: "Only this context owns conversation continuity and deletion.", change_locality_hypothesis: "Channel changes do not redefine history lifecycle.", merge_candidate: "delivery only if channel receipt and durable history cannot diverge", split_candidate: "search index projection from canonical history", tracer_falsifier: "delivery stores an authoritative parallel transcript"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:189:  - {context_id: "process_assurance", owner: "process_assurance", consistency_hypothesis: "One process assessment/audit/corrective-action record.", failure_hypothesis: "Missing/biased evidence remains UNKNOWN and cannot raise maturity.", ownership_hypothesis: "Only this context owns process conformance and improvement evidence.", change_locality_hypothesis: "Process metrics do not alter product gate authority.", merge_candidate: "assurance only if process/product evidence lifecycles converge", split_candidate: "fleet experiments from audits after independent cadence", tracer_falsifier: "an aggregate score hides one failed control"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:190:  - {context_id: "workspace", owner: "workspace", consistency_hypothesis: "One repository/worktree/head/landing identity plan.", failure_hypothesis: "Path/head/ancestry mismatch blocks writing or landing.", ownership_hypothesis: "Only this context owns workspace lifecycle and landing plan.", change_locality_hypothesis: "Git topology changes avoid domain state edits.", merge_candidate: "upstream_sync only if all workspace use becomes sync-specific", split_candidate: "landing from workspace allocation after concurrency pressure", tracer_falsifier: "a write lands outside the bound worktree/head"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:191:  - {context_id: "instruction_registry", owner: "instruction_registry", consistency_hypothesis: "One immutable instruction/version/precedence activation.", failure_hypothesis: "Conflict or missing applicability blocks packet sealing.", ownership_hypothesis: "Only this context owns instruction semantics and precedence.", change_locality_hypothesis: "Instruction edits avoid compiler/run authority changes.", merge_candidate: "context_compilation only if instructions have no independent lifecycle", split_candidate: "activation from immutable registry after cadence divergence", tracer_falsifier: "packet output depends on unregistered ambient instructions"}
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:192:  - {context_id: "context_compilation", owner: "context_compilation", consistency_hypothesis: "One exact resolved-source packet manifest/digest.", failure_hypothesis: "Conflict, missing source, budget overflow, or freshness failure blocks sealing.", ownership_hypothesis: "Only this context owns packet compilation and source resolution.", change_locality_hypothesis: "Source-provider changes stay behind ports.", merge_candidate: "instruction_registry only if compilation and instruction lifecycle collapse", split_candidate: "retrieval orchestration from canonical packet compiler", tracer_falsifier: "same resolved inputs produce different packet digest"}
===
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:592:├── pyproject.toml
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:593:├── uv.lock
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:48:   `scripts/architecture/pyproject.toml` requires `>=3.12` and pins
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:47:1. **Measured.** `scripts/architecture/pyproject.toml` requires `>=3.12` and
docs/architecture/assessments/COMPLETENESS_REPORT.md:34:Run `uv run --project scripts/architecture python
===
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:133:The licensing, copyright, provenance, attribution, and history-preservation
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:564:    guard_id: "LICENSE_COPYRIGHT_PROVENANCE_ATTRIBUTION_AND_HISTORY_ARE_PRESERVED"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:569:    provision: "Preserve license, copyright, provenance, and required upstream attribution. Rebranding does not authorize erasing legal notices or Git history."
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1151:| `FF-HERMES-LEGAL-001` | License, copyright, provenance, required-attribution, legal-notice, and Git-history preservation are non-waivable release obligations; separate de-commercialization, package, network, credential, data, and branding checks remain noncompensating owner requirements rather than being mislabeled as law. |
docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:875:      - "every evidence_ref has artifact_type checker_result, is unique, resolves to subject, and the complete ordered set hashes to attempt_manifest_digest"
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:63:5. **Verified externally.** Pyright reports the highest typing-specification
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:64:   conformance (approximately 97.8%); Meta's Pyrefly reached stable 1.0 in May
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:65:   2026 with substantially faster execution; Astral's `ty` is alpha; `mypy`
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:66:   trails at approximately 58% conformance. No type checker is configured in any
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:67:   Ranex package; `ruff` is a linter and does not discharge this.
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:113:### `LANG-TYPECHECK-001` — Static type checking is a required gate
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:116:at runtime, a static type checker in strict mode is a required check for every
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:235:select a type checker, register a performance budget, authorize any compiled
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:63:6. **Type-checker landscape, verified externally 2026-07-30.** Pyright reports
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:64:   the highest typing-specification conformance (~97.8%); Meta's Pyrefly reached
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:66:   alpha; `mypy` trails at ~58% conformance. No type checker is configured in
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:67:   any Ranex package today; `ruff` is a linter and does not discharge this.
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:87:2. Which type checker will be selected, and its conformance and performance
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:108:**Non-goals.** Selecting a type checker; authorizing any compiled component;
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:148:### `LANG-TYPECHECK-001` — Static type checking is a required gate
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:150:A static type checker in strict mode is required for every Ranex package and
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:258:than defaulted: the type checker is unselected (`LANG-TYPECHECK-001`); no
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md:267:2. Make strict static type checking a required gate per `LANG-TYPECHECK-001`,
docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md:353:3. preserve the required copyright/license notice;
docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md:101:- no human ADR or model review can waive copyright, contract, privacy, or
[0m
[0m$ [0mrg -n -i "github actions|continuous integration|\bCI\b" docs/architecture -g '!*reviews*' | head -30; echo ===; rg -n -i "license|AGPL|MIT|Apache|commercial" LICENSE-RANEX.md NOTICE.md legal/licensing-manifest.json | head -40
docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md:59:├── scripts/                        # thin public-API operator/CI clients
docs/architecture/SDLC_CONTROL_CATALOG.md:1894:| `SDLC-BLD-001` `IN_PROGRESS` | Produce bounded candidate; Ready item and exact base | Task packet, baselines, workspace, grants | Implement with tests/docs/telemetry; integrate small; manage config/dependencies; record truthfully | Exact candidate, run result, handoff, updated trace/config status | Maker / technical owner / reviewer, V&V, config / delivery | Path/dependency/schema/CI checks + maker handoff (not approval) | Failure → In Progress/Blocked/Design/Definition | One conceptual change; WIP, cycle time, build/rework | `STD`,`OBS`,`PRAC`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1957:| Small batches, WIP, CI/CD, tests, observability and measures | [DORA capabilities](https://dora.dev/capabilities/) and [metrics](https://dora.dev/guides/dora-metrics/) |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:540:| `provenance_compliance` | File classification, licenses, notices, de-commercialization denylist, SBOM policy | CI, release, upstream sync |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:582:| Legal/de-commercialization | `provenance_compliance` | CI scanners/SBOM | release and sync gates | Compliance decision |
docs/architecture/AI_ARTIFACT_CONTRACTS.md:595:from these schemas and registries. Hand editing generated files fails CI.
docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:1720:  - {exception_id: "LEGACY-TEST-ROOT-004", legacy_root: "tests/ci", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 8, subtree_oid_sha1: "1db247587d6bd6772c2d92c498d3737e90aefb20", ls_tree_listing_sha256: "871807a9eeb28b79e1e9bdbb67a428a508712f1e12704b65f3972cd4b9ae0aaf", destination_root: "tests/qualification/release_management/ci", row_policy_ref: "row_policy"}
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:790:- continuous intake, CI, security and incident response;
docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md:397:projections. Hand-edited duplication fails CI.
===
NOTICE.md:1:# Ranex Copyright and License Notice
NOTICE.md:13:remains licensed under the MIT License retained in `LICENSE`. That license
NOTICE.md:14:permits use, modification, publication, distribution, sublicensing, and sale
NOTICE.md:21:Original Ranex additions and modifications are licensed under the
NOTICE.md:22:Ranex Personal-Use Source License 1.0 in `LICENSE-RANEX.md`. That license allows
NOTICE.md:30:An unchanged file inherited from Hermes Agent remains MIT licensed. A modified
NOTICE.md:31:upstream file can contain both MIT-licensed upstream material and separately
NOTICE.md:32:licensed original Ranex modifications.
NOTICE.md:35:history must identify the applicable portions. The Ranex license does not
NOTICE.md:36:remove or narrow rights granted directly under the MIT License for upstream
NOTICE.md:52:The repository is public. GitHub's Terms of Service grant limited use,
LICENSE-RANEX.md:1:# Ranex Personal-Use Source License 1.0
LICENSE-RANEX.md:5:This is a source-available license. It is not an open-source license.
LICENSE-RANEX.md:9:This license applies only to original Ranex code, documentation, configuration,
LICENSE-RANEX.md:13:Those portions remain governed by their own licenses. When Hermes Agent
LICENSE-RANEX.md:14:material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
LICENSE-RANEX.md:22:This permission is personal, limited, non-exclusive, and non-transferable. All
LICENSE-RANEX.md:23:copyright, license, attribution, and source notices must remain intact.
LICENSE-RANEX.md:27:Except for the limited GitHub-platform rights in section 4, and unless Anthony
LICENSE-RANEX.md:30:1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
LICENSE-RANEX.md:34:3. use the Ranex Material for any commercial, business, employment,
LICENSE-RANEX.md:38:5. remove, hide, or alter a copyright, license, provenance, or attribution
LICENSE-RANEX.md:44:8. grant another person rights that this license does not grant to you.
LICENSE-RANEX.md:53:limited permission to use, display, perform, and reproduce repository content
LICENSE-RANEX.md:55:license does not restrict those platform rights.
LICENSE-RANEX.md:63:The Ranex Material is licensed, not sold. Anthony Garces retains all rights
LICENSE-RANEX.md:66:No term in this license reduces a right granted directly by the MIT License or
LICENSE-RANEX.md:67:another applicable third-party license. When a file contains both upstream
LICENSE-RANEX.md:69:its applicable license.
LICENSE-RANEX.md:73:Your permission under this license ends automatically when you violate it.
LICENSE-RANEX.md:84:TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
LICENSE-RANEX.md:90:This license does not limit fair use, fair dealing, or another right that
LICENSE-RANEX.md:91:applicable law does not allow a license to restrict.
legal/licensing-manifest.json:9:  "licenses": {
legal/licensing-manifest.json:11:      "id": "MIT",
legal/licensing-manifest.json:12:      "file": "LICENSE",
legal/licensing-manifest.json:14:      "applies_to": "Hermes Agent and other material received under the MIT License"
legal/licensing-manifest.json:17:      "id": "LicenseRef-Ranex-Personal-Use-1.0",
legal/licensing-manifest.json:18:      "file": "LICENSE-RANEX.md",
legal/licensing-manifest.json:22:      "personal_learning_use": "permitted",
[0m
[0m$ [0mrg -n -i "framework|test runner|tool" docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md | head -25; echo ===; cat scripts/architecture/pyproject.toml; echo ===; python3 -c "
import json
d=json.load(open('architecture/contracts/accepted-adrs.json'))
print(type(d));
import sys
s=json.dumps(d)[:400]; print(s)
"
121:additionally binds the image, toolchain, network policy, filesystem policy,
157:randomness, ID generation, network, filesystem, provider/tool transport, and
196:9. network/provider/tool failure, route/identity mismatch, malformed/oversized
719:    fields: ["tier", "seed_manifest_digest", "input_manifest_digest", "rule_version_manifest_digest", "journal_capture_policy_digest", "image_digest", "toolchain_manifest_digest", "network_policy_digest", "filesystem_policy_digest", "dependency_lock_digest", "execution_capability_profile_digest"]
727:      toolchain_manifest_digest: "sha256|null"
732:    cardinality: {tier: "1", seed_manifest_digest: "1", input_manifest_digest: "1", rule_version_manifest_digest: "1", journal_capture_policy_digest: "1", image_digest: "0..1", toolchain_manifest_digest: "0..1", network_policy_digest: "0..1", filesystem_policy_digest: "0..1", dependency_lock_digest: "0..1", execution_capability_profile_digest: "0..1"}
1701:5. one bounded readiness tooling tracer produces a real, nonsynthetic,
1717:the tier passes, only ADR-0012's bounded `PRE_READINESS_TOOLING_TRACER` may
1762:evidence is retained Ch.5 only; Pragmatic tooling is dated; SWEBOK is a
===
[project]
name = "ranex-architecture-contracts"
version = "0.1.0"
description = "Deterministic generation and validation for Ranex architecture contracts"
requires-python = ">=3.12"
dependencies = [
  "jsonschema==4.25.1",
  "PyYAML==6.0.2",
  "rfc8785==0.1.4",
]

[tool.uv]
package = false

===
<class 'dict'>
{"entries": [{"adr_id": "ADR-0001", "source_digest": "sha256:a1eec2c60576f0c5c6b7117555b6ec9abf949e983f129a402089a61affbe49b4", "source_path": "docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md", "status": "ACCEPTED", "version": "1.1.0"}, {"adr_id": "ADR-0002", "source_digest": "sha256:da71597ef601024873e0c1bf846bece30268d2d0501d5f8cd1caba6d5db9005b", "source_path": "docs/ar
[0m
[0m$ [0mrg -n "ADR-0014|ADR-0013" architecture/contracts/*.json | head; echo ===; rg -n -i "secret|credential" docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md | head; echo ===; rg -n -i "IMPLEMENTATION_START_READY|gate" docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md | head -30
architecture/contracts/hermes-research-promotions.json:13:      "governing_adr": "ADR-0013",
architecture/contracts/hermes-research-promotions.json:15:      "governing_adr_source": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
architecture/contracts/hermes-research-promotions.json:36:      "governing_adr": "ADR-0013",
architecture/contracts/hermes-research-promotions.json:38:      "governing_adr_source": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
architecture/contracts/hermes-research-promotions.json:59:      "governing_adr": "ADR-0013",
architecture/contracts/hermes-research-promotions.json:61:      "governing_adr_source": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
architecture/contracts/hermes-research-promotions.json:82:      "governing_adr": "ADR-0013",
architecture/contracts/hermes-research-promotions.json:84:      "governing_adr_source": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
architecture/contracts/hermes-research-promotions.json:105:      "governing_adr": "ADR-0013",
architecture/contracts/hermes-research-promotions.json:107:      "governing_adr_source": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
===
===
14:| Supersedes | Ambiguous uses of “build ready,” “enterprise build ready,” and “runtime ready” in earlier documents; it does not weaken any evidence, authority, security, recovery, or production gate |
15:| Review/expiry date | Review on any readiness tier, gate, evidence role, reviewer route, architecture-rule denominator, production-admission, or authority-boundary change |
17:| Security/data class | Public decision and gate metadata; referenced source, review, security, operational, and production evidence retains its own classification |
33:| `IMPLEMENTATION_START_READY` | `DESIGN_DEFINITION_READY` | Admission of staged product implementation under the normal per-work-item packet, gate, grant, permit, TDD, review, and landing controls | Enacted product runtime, production safety, operational effectiveness, mature capability scores, release, deployment, or user impact |
41:`IMPLEMENTATION_START_READY` is deliberately attainable before full runtime
55:state machine, gate contracts, and authority boundary only.
59:Before `IMPLEMENTATION_START_READY`, one bounded
74:gate, or become a reusable bypass. Failure, expiry, scope growth, or an
114:      - "GateEvaluation"
149:    aggregate_type: "RepositoryReadiness"
150:    aggregate_id_rule: "aggregate_id equals repository_id"
159:      - "IMPLEMENTATION_START_READY"
167:      - "IMPLEMENTATION_START_EVALUATING>IMPLEMENTATION_START_READY@IMPLEMENTATION_START_EXACT_PASS_AND_HUMAN_DECISION"
169:      - "IMPLEMENTATION_START_READY>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_EVIDENCE_INVALIDATED"
170:      - "IMPLEMENTATION_START_READY>PRODUCTION_EVALUATING@PRODUCTION_ASSESSMENT_OPENED"
179:      - "NOT_ASSESSED>IMPLEMENTATION_START_READY"
181:      - "IMPLEMENTATION_START_BLOCKED>IMPLEMENTATION_START_READY"
182:      - "IMPLEMENTATION_START_READY>PRODUCTION_READY"
184:      - "PRODUCTION_READY>IMPLEMENTATION_START_READY"
191:      - "state_catalog_ref, axis_id, axis_version, owner_context, aggregate_type, and aggregate_id equal the state_axis contract and repository_id"
192:      - "from_state equals the prior current state; to_state and guard_id name one exact allowed transition; aggregate_version_after equals aggregate_version_before plus one"
193:      - "subject schema/ref/digest/manifest digest equal the assessment exact readiness subject; evidence_refs include that immutable assessment and its gate bindings"
196:    uniqueness: "at most one immutable transition fact exists for repository_id and aggregate_version_after"
360:        - "gate_id"
377:        gate_id: "safe_id"
398:        - "bridge_rule_id is the one registered rule for gate_id; the resolver independently proves its relation and rejects caller-selected relabeling"
399:    - type_id: "ReadinessGateResultV1"
402:        - "gate_id"
408:        gate_id: "safe_id"
417:        - "evidence_binding.gate_id equals gate_id and resolves the exact per-gate native-subject bridge"
[0m
[0m$ [0mpython3 -c "
import json
d=json.load(open('architecture/contracts/accepted-adrs.json'))
for e in d['entries']:
    print(e['adr_id'], e['status'], e['version'])
"
ADR-0001 ACCEPTED 1.1.0
ADR-0002 ACCEPTED 1.1.0
ADR-0003 ACCEPTED 1.0.0
ADR-0004 ACCEPTED 1.0.0
ADR-0005 ACCEPTED 1.1.0
ADR-0006 ACCEPTED 1.1.0
ADR-0007 ACCEPTED 1.0.0
ADR-0008 ACCEPTED 1.6.0
ADR-0009 ACCEPTED 1.0.0
ADR-0010 ACCEPTED 2.0.1
ADR-0011 ACCEPTED 1.0.0
ADR-0012 ACCEPTED 1.1.0
ADR-0013 ACCEPTED 1.4.0
ADR-0014 ACCEPTED 1.0.0
[0m
[0m$ [0mrg -n -i "secrets|keyring|keychain|env var|environment variable" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -20; echo ===; rg -n "TUI|CLI|loopback|Telegram|owner" docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md | head; echo ===; rg -n -i "plain.language|non.technical|owner interface|intent" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -20
277:19. Secrets are opaque handles until resolved at the authorized adapter edge.
328:| Security | Identity, authentication, grants, data classification, egress, secrets, isolation profiles | Business workflow state |
345:      IAM["Identity, Access & Secrets"]
572:| Authentication/secrets | `identity_access` | keyring/file/vault/OAuth adapters | identity/session/secret lifecycle | Principal or secret handle |
783:│       │   ├── secrets/
784:│       │   │   ├── keyring/
2754:instead of secrets/raw personal content, and applies
3185:## 21. Policy, identity, secrets, and human decisions
3379:compatibility data. Files containing secrets or classified content use `0600`
3440:limits, and records the destination/receipt without secrets. Direct socket,
3475:reconciliation. Secrets are backed up only through their secret backend's
===
8:| Decision owner | Human owner |
13:| RFC | Not required; direct owner requirement |
75:The owner explicitly directed that Ranex architecture be organized around the
124:## State and effect ownership
186:The human owner explicitly approved this direction in the authenticated project
189:is the durable repository record of that owner decision; it does not claim a
===
221:| Canonical authority | One `governed_execution` consistency cell owns run transitions, gate bindings, permit consumption, and effect intent. |
252:   consumed permit or decision, and outbound effect intent.
383:    GE -- "authorized activity/effect intents" --> Effects
415:4. activity/effect intent, result, retry, and reconciliation.
450:  -> insert zero or more outbound effect intents in the effect outbox
460:`0..N` effect intents, each with its own identity, arguments, destination,
468:the stale intent's authority.
497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
552:| Permits and effects | `governed_execution` | capability bus/outbox | `governed_execution` | Consumed permit + effect intent/result |
2071:    integration_events: ["EffectIntentRecorded", "EffectDispatched", "EffectResolved", "EffectOutcomeMarkedUnknown", "EffectReconciled"]
2076:    cancellation_semantics: "Unexecuted revoked intent is DENIED; dispatched effect must resolve or reconcile"
2079:    transitions: ["INTENDED>DISPATCHED@COMMITTED_INTENT_CURRENT_PERMIT_AND_ADAPTER_LEASE", "INTENDED>DENIED@PRE_DISPATCH_POLICY_OR_DESTINATION_DENIAL", "INTENDED>FAILED_PERMANENT@INTENT_OR_ADAPTER_VALIDATION_TERMINALLY_FAILED", "DISPATCHED>SUCCEEDED@PROVIDER_RECEIPT_PROVES_SUCCESS", "DISPATCHED>FAILED_RETRYABLE@PROVIDER_RECEIPT_PROVES_RETRYABLE_FAILURE", "DISPATCHED>FAILED_PERMANENT@PROVIDER_RECEIPT_PROVES_TERMINAL_FAILURE", "DISPATCHED>DENIED@PROVIDER_RECEIPT_PROVES_DENIAL", "DISPATCHED>OUTCOME_UNKNOWN@ACKNOWLEDGEMENT_LOST_OR_AMBIGUOUS", "FAILED_RETRYABLE>DISPATCHED@RETRY_POLICY_BUDGET_AND_DEADLINE_ALLOW", "FAILED_RETRYABLE>FAILED_PERMANENT@RETRY_BUDGET_OR_DEADLINE_EXHAUSTED", "FAILED_RETRYABLE>DENIED@POLICY_OR_DESTINATION_DENIES_RETRY", "OUTCOME_UNKNOWN>SUCCEEDED@QUALIFIED_RECONCILIATION_PROVES_SUCCESS", "OUTCOME_UNKNOWN>FAILED_RETRYABLE@QUALIFIED_RECONCILIATION_PROVES_RETRYABLE_FAILURE", "OUTCOME_UNKNOWN>FAILED_PERMANENT@QUALIFIED_RECONCILIATION_PROVES_TERMINAL_FAILURE", "OUTCOME_UNKNOWN>DENIED@QUALIFIED_RECONCILIATION_PROVES_DENIAL"]
2617:the one dimension intentionally falsified by that negative. Reusing a partial
2750:effect; effect dispatch requires its separate permit/intent path.
2780:| `EVENT-EFFECTINTENTRECORDED` / `EffectIntentRecorded` | `governed_execution` / `effect_service`; `operations`, `artifact_management` | `Effect`; permit consumption and durable intent occur in one UoW | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `effect_id:Id<Effect>`, `permit_id:Id<Permit>`, `effect_type:String`, `destination_fact_ref:Ref<DestinationFact>`, `argument_digest:Sha256` |
2781:| `EVENT-EFFECTDISPATCHED` / `EffectDispatched` | `governed_execution` / `effect_dispatch_service`; `operations` | `Effect`; committed intent leased, deadline/retry policy allows attempt | `effect_id:Id<Effect>`, `dispatch_attempt:UInt`, `adapter_id:String`, `adapter_version:String`, `provider_request_id:String`, `dispatched_at:Utc` |
2919:  - event_name: "EffectIntentRecorded"
2928:        allowed_edges: ["INTENDED>DISPATCHED@COMMITTED_INTENT_CURRENT_PERMIT_AND_ADAPTER_LEASE", "FAILED_RETRYABLE>DISPATCHED@RETRY_POLICY_BUDGET_AND_DEADLINE_ALLOW"]
3131:1. leases a committed intent;
3245:configured auth intent, observed effective auth source/subject, and vendor-unobservable UNKNOWN facts
[0m
[0m$ [0mrg -n -i "telemetry|observab|OpenTelemetry|metrics|audit" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -25; echo ===; rg -n -i "plain.language|intent capture|nontechnical|non-technical" docs/architecture/*.md docs/architecture/decisions/*.md | head -20
111:- the audited Hermes baseline
118:  either the audited baseline or phase-1 line;
120:  separately recorded observations, not silently substituted audited or
135:2. retain the exact audited upstream commit in a pristine mirror/worktree and
142:5. distinguish the observed, audited, incorporated, and latest-seen upstream
157:- observed, audited, incorporated, and latest-seen baseline records;
168:audited license/provenance, record strategy and topology, bind the resulting
279:    telemetry.
366:      OBS["telemetry exporters"]
446:  -> append ordered run/domain/audit event
473:- The ordered journal is the replay and audit oracle.
481:Every stateful context commits its aggregate update, local audit event, and
510:| `configuration_management` | Configuration-item registry, content-addressed baselines, status accounting, bidirectional traceability graph, functional/physical configuration audits | Product requirements, source/build/test/docs, release manifests, assurance evidence |
514:| `process_assurance` | SDLC policy conformance, tailoring profiles, human-role competence, process audits/nonconformance/corrective action, process improvement evidence, fleet experiment and calibration records | Core SDLC, work records, metrics, training/qualification and measurement-harness evidence |
533:| `operations` | Observed health, alerts, `IncidentStatus`, response/recovery evidence, reconciliation scheduling and operator runbooks | Telemetry, delivery, service objectives, external-system probes |
558:| Configuration/baselines/traceability | `configuration_management` | repository/build/test/release scanners | `configuration_management` | Audited baseline and trace graph |
562:| Process assurance | `process_assurance` | conformance/audit/competence adapters | `process_assurance` | Tailoring, nonconformance and corrective-action record |
575:| Observability/operations | `operations` | OTLP/log/metric exporters | incident/health lifecycle | Noncanonical telemetry |
583:| Contract/schema generation | `configuration_management` orchestrates from accepted source-owner registries | deterministic contract compiler and language generators | source context owns semantics; `configuration_management` owns baseline/reproducibility | Registry digest, generated Python/TypeScript packages, drift/audit result |
650:│       │   │       └── telemetry.py
787:│       │   ├── observability/
1124:| `configuration_management` | `api/{commands,queries,events,views}.py`; `domain/{configuration_items,baselines,status_accounting,trace_links,audits,drift,generation_manifests,invariants}.py` | `application/{baseline_service,traceability_service,audit_service,drift_service,contract_generation_service}.py`; `application/ports/{configuration_scanner,baseline_store,contract_registry,code_generator}.py` |
1128:| `process_assurance` | `api/{commands,queries,events,views}.py`; `domain/{tailoring_profiles,competence_profiles,audits,nonconformances,corrective_actions,process_measures,capability_assessments,capability_domain_projections,fleet_experiments,calibration_records,improvement_proposals,invariants}.py` | `application/{tailoring_service,audit_service,competence_service,corrective_action_service,capability_assessment_service,capability_projection_service,fleet_experiment_service}.py`; `application/ports/{process_evidence,training_registry,measurement_runner}.py` |
1135:| `effectiveness` | `api/{commands,queries,views}.py`; `domain/{experiments,arms,trials,metrics,uncertainty,scorecards,ablation,invariants}.py` | `application/{experiment_service,analysis_service,report_service}.py`; `application/ports/{workflow_runner,effectiveness_grader}.py` |
1142:| `operations` | `api/{commands,queries,events,views}.py`; `domain/{health,alerts,incidents,capacity,reconciliation,service_levels,runbooks,lifecycle}.py` | `application/{health_service,alert_service,incident_service,reconciliation_service}.py`; `application/ports/{telemetry_query,notification}.py` |
===
[0m
[0m$ [0mls -a; ls .github 2>/dev/null; echo ===; glob() { :; }; find . -name "pyrightconfig*" -o -name "mypy.ini" -o -name ".pre-commit*" -o -name "*.toml" -not -path "./.git/*" 2>/dev/null | head; echo ===; find . -path ./.git -prune -o -name "*.py" -print | head -20; echo ===; rg -n -i "kernel" scripts/architecture/README.md | head; echo ===; rg -l "BEGIN IMMEDIATE" -g '!.git' . 2>/dev/null | head
.
..
architecture
.claude
decisions
docs
.git
.gitignore
legal
LICENSE
LICENSE-RANEX.md
.local
NOTICE.md
README.md
schemas
scripts
===
./.claude/worktrees/phase-2-runtime-bootstrap/apps/bootstrap-installer/src-tauri/Cargo.toml
./.claude/worktrees/phase-2-runtime-bootstrap/node_modules/node-gyp/gyp/pyproject.toml
./.claude/worktrees/phase-2-runtime-bootstrap/pyproject.toml
./.claude/worktrees/phase-1-adopt-upstream/apps/bootstrap-installer/src-tauri/Cargo.toml
./.claude/worktrees/phase-1-adopt-upstream/pyproject.toml
./.claude/worktrees/kernel-tracer/scripts/architecture/pyproject.toml
./.claude/worktrees/kernel-tracer/pyproject.toml
./.claude/worktrees/gate-controller-mvp/apps/bootstrap-installer/src-tauri/Cargo.toml
./.claude/worktrees/gate-controller-mvp/pyproject.toml
./.claude/worktrees/architecture-validated-baseline/apps/bootstrap-installer/src-tauri/Cargo.toml
===
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/curses_ui.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/browser_connect.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/console.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/slack.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/model.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/tools.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/approvals.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/mcp.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/dump.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/gateway.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/plugins.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/import_cmd.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/version.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/profile.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/claw.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/debug.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/logs.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/skills.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/config.py
./.claude/worktrees/phase-2-runtime-bootstrap/hermes_cli/subcommands/hooks.py
===
===
./docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
[0m
[0m$ [0mcat .gitignore; echo ===; git -C . ls-files | rg "^\.claude|^\.local" | head; echo ===; git ls-files | awk -F/ '{print $1}' | sort | uniq -c | sort -rn | head -20
.claude/worktrees/

# Local helpers, runtime evidence, credentials, and machine-specific decisions.
.local/*
!.local/*.example
evidence/runtime/
*.secret
decisions/local-values.env
.env
.env.local
.env.*
!.env.example
!*.env.example

# Full-text reference books are consultation-only local artifacts. Their
# bibliographic citations, original reconciliation, and non-reconstructive
# digest manifest remain publishable; the source files do not.
docs/research/books/

# The raw Kimi corpus has no retained license/provider/source lineage. Keep the
# exact digest manifest and original reconciliation public; keep the opaque
# source/rendering bundle local until rights and privacy clearance exists.
docs/research/kimi-research/

# Local configuration for the running Hermes agent; not a Ranex research or
# architecture input.
RULES-THERY.md
===
===
    200 schemas
    184 docs
     51 architecture
      8 scripts
      1 README.md
      1 NOTICE.md
      1 LICENSE-RANEX.md
      1 LICENSE
      1 legal
      1 .gitignore
      1 decisions
[0m
[0m$ [0mcat .claude/worktrees/kernel-tracer/pyproject.toml 2>/dev/null; echo ===; ls .claude/worktrees; echo ===; rg -n "BEGIN IMMEDIATE" .claude/worktrees/kernel-tracer -l 2>/dev/null | head; echo; ls .claude/worktrees/kernel-tracer 2>/dev/null | head -30
[project]
name = "ranex-kernel-tracer"
version = "0.0.0"
description = "Non-authoritative R&D tracer for the proposed Ranex kernel"
requires-python = ">=3.11,<3.15"
dependencies = [
    "PyYAML>=6.0.2,<7",
]

[dependency-groups]
dev = [
    "pytest>=9.0.2,<10",
    "ruff>=0.15.10,<0.16",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
addopts = [
    "--strict-config",
    "--strict-markers",
]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
===
architecture-validated-baseline
docs
gate-controller-mvp
kernel-tracer
phase-0-preflight
phase-1-adopt-upstream
phase-2-runtime-bootstrap
===
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py

architecture
decisions
docs
legal
LICENSE
LICENSE-RANEX.md
NOTICE.md
pyproject.toml
README.md
schemas
scripts
src
tests
uv.lock
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md[90m [limit=110][0m
[0m
[0m$ [0mrg -n "IMPLEMENTATION_START gate|gate_id:|gates:" docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md | head -40
377:        gate_id: "safe_id"
408:        gate_id: "safe_id"
554:  gates:
555:    - {gate_id: "READY-SOURCE-MANIFEST-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_COMMITTED_SOURCE_MANIFEST", freshness_rule: "PINNED_CLEAN_EVALUATION_COMMIT_AND_UNCHANGED_GOVERNED_PATHS_ON_CLEAN_DESCENDANT_HEAD", bridge_rule_id: "BRIDGE-READY-SOURCE-MANIFEST-001", noncompensating: true}
556:    - {gate_id: "READY-GENERATED-MANIFEST-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_GENERATED_OUTPUT_MANIFEST", freshness_rule: "DERIVED_FROM_CURRENT_GOVERNED_SOURCE_MANIFEST", bridge_rule_id: "BRIDGE-READY-GENERATED-MANIFEST-001", noncompensating: true}
557:    - {gate_id: "READY-CONTRACT-VALIDATION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "DETERMINISTIC_COMPILER_VALIDATOR_REPORT", freshness_rule: "ZERO_VIOLATIONS_NO_STALE_OUTPUT_OR_DENOMINATOR", bridge_rule_id: "BRIDGE-READY-CONTRACT-VALIDATION-001", noncompensating: true}
558:    - {gate_id: "READY-FORK-PREFLIGHT-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "SDLC_FORK_000_GATE_EVALUATION", freshness_rule: "EVALUATION_COMMIT_CLEAN_UPSTREAM_DERIVED_AND_CURRENT_HEAD_CLEAN_DESCENDANT", bridge_rule_id: "BRIDGE-READY-FORK-PREFLIGHT-001", noncompensating: true}
559:    - {gate_id: "READY-TDD-CYCLE-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "REAL_TDD_CYCLE_RECORD_V1", freshness_rule: "CURRENT_NON_SYNTHETIC_GATED_PASS", bridge_rule_id: "BRIDGE-READY-TDD-CYCLE-001", noncompensating: true}
560:    - {gate_id: "READY-LANDING-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "SEPARATE_LANDING_RECORD_V1", freshness_rule: "EXACTLY_ONE_SUCCEEDED_FOR_TDD_CANDIDATE", bridge_rule_id: "BRIDGE-READY-LANDING-001", noncompensating: true}
561:    - {gate_id: "READY-SEALING-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "POST_LANDING_SEALING_VALIDATION", freshness_rule: "LANDED_EVALUATION_COMMIT_TREE_AND_ALL_GOVERNED_INPUT_DIGESTS_CURRENT", bridge_rule_id: "BRIDGE-READY-SEALING-001", noncompensating: true}
562:    - {gate_id: "READY-HY3-REVIEW-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "OPENCODE_HY3_FINAL_STRUCTURAL_REVIEW", freshness_rule: "POST_SEAL_READ_ONLY_CURRENT_ROUTE_AND_MODEL", bridge_rule_id: "BRIDGE-READY-HY3-REVIEW-001", noncompensating: true}
563:    - {gate_id: "READY-DEEPSEEK-REVIEW-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "OPENCODE_DEEPSEEK_V4_PRO_STRUCTURAL_REVIEW", freshness_rule: "POST_SEAL_READ_ONLY_CURRENT_ROUTE_AND_MODEL", bridge_rule_id: "BRIDGE-READY-DEEPSEEK-REVIEW-001", noncompensating: true}
564:    - {gate_id: "READY-FINDING-RECONCILIATION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_REVIEW_FINDING_RECONCILIATION", freshness_rule: "NO_UNRESOLVED_P0_OR_P1_AND_ALL_P2_P3_RETAINED", bridge_rule_id: "BRIDGE-READY-FINDING-RECONCILIATION-001", noncompensating: true}
565:    - {gate_id: "READY-HUMAN-START-DECISION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "AUTHENTICATED_IMPLEMENTATION_START_DECISION", freshness_rule: "ISSUED_AFTER_ALL_NON_DECISION_TIER_EVIDENCE_AND_NOT_REVOKED_OR_SUPERSEDED", bridge_rule_id: "BRIDGE-READY-HUMAN-START-DECISION-001", noncompensating: true}
566:    - {gate_id: "READY-IMPLEMENTATION-PREREQUISITE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "CURRENT_IMPLEMENTATION_START_READINESS_ASSESSMENT", freshness_rule: "CURRENT_TIER1_ASSESSMENT_WITH_IDENTICAL_READINESS_BASIS_DIGEST", bridge_rule_id: "BRIDGE-READY-IMPLEMENTATION-PREREQUISITE-001", noncompensating: true}
567:    - {gate_id: "READY-RUNTIME-PRODUCERS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "ENACTED_RUNTIME_PRODUCER_AND_OWNERSHIP_EVIDENCE", freshness_rule: "ALL_ACTIVE_PRODUCERS_CURRENT_AND_CROSS_PRODUCER_FORGERY_DENIED", bridge_rule_id: "BRIDGE-READY-RUNTIME-PRODUCERS-001", noncompensating: true}
568:    - {gate_id: "READY-RULE-RESULTS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "ARCHITECTURE_RULE_RESULT_RECONCILIATION", freshness_rule: "EXACT_64_ROWS_CURRENT_COMPLETE_AND_NO_BLOCKING_RESULT", bridge_rule_id: "BRIDGE-READY-RULE-RESULTS-001", noncompensating: true}
569:    - {gate_id: "READY-ADOPTION-GATES-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "PROCESS_AND_APPLICABLE_FLEET_ADOPTION_GATE_SET", freshness_rule: "SDLC_ADOPT_A_THROUGH_E_AND_EVERY_APPLICABLE_SPECIALIZED_GATE_PASS", bridge_rule_id: "BRIDGE-READY-ADOPTION-GATES-001", noncompensating: true}
570:    - {gate_id: "READY-SECURITY-ISOLATION-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "SECURITY_PRIVACY_SANDBOX_BYPASS_AND_INDEPENDENCE_EVIDENCE", freshness_rule: "TARGET_HOST_ROUTE_MODEL_TOOL_SANDBOX_AND_DATA_CLASS_CURRENT", bridge_rule_id: "BRIDGE-READY-SECURITY-ISOLATION-001", noncompensating: true}
571:    - {gate_id: "READY-OPERATING-EVIDENCE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "RELEASE_CANDIDATE_REHEARSAL_OBSERVATION_AND_SERVICE_ACCEPTANCE_EVIDENCE", freshness_rule: "QUALIFIED_TARGET_EQUIVALENT_ENVIRONMENT_AND_DECLARED_WINDOW", bridge_rule_id: "BRIDGE-READY-OPERATING-EVIDENCE-001", noncompensating: true}
572:    - {gate_id: "READY-RECOVERY-EVIDENCE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "BACKUP_RESTORE_ROLLBACK_INCIDENT_AND_RECONCILIATION_EVIDENCE", freshness_rule: "QUALIFIED_TARGET_ENVIRONMENT_AND_CURRENT_RUNBOOKS", bridge_rule_id: "BRIDGE-READY-RECOVERY-EVIDENCE-001", noncompensating: true}
573:    - {gate_id: "READY-CAPABILITY-ASSESSMENTS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "APPLICABLE_VITAL_CONTROL_AND_DOMAIN_ASSESSMENT_SET", freshness_rule: "EVERY_APPLICABLE_TUPLE_CURRENT_SCORED_OR_APPROVED_NOT_APPLICABLE_NO_UNKNOWN", bridge_rule_id: "BRIDGE-READY-CAPABILITY-ASSESSMENTS-001", noncompensating: true}
574:    - {gate_id: "READY-AUTHORITY-CHAIN-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "AUTHENTICATED_GOVERNANCE_DECISION_AND_AUTHORITY_QUALIFICATION_EVIDENCE", freshness_rule: "CURRENT_EXACT_SUBJECT_NO_SELF_APPROVAL_OR_BYPASS", bridge_rule_id: "BRIDGE-READY-AUTHORITY-CHAIN-001", noncompensating: true}
575:    - {gate_id: "READY-HUMAN-PRODUCTION-DECISION-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "AUTHENTICATED_PRODUCTION_READINESS_DECISION", freshness_rule: "ISSUED_AFTER_ALL_NON_DECISION_PRODUCTION_EVIDENCE_AND_NOT_REVOKED_OR_SUPERSEDED", bridge_rule_id: "BRIDGE-READY-HUMAN-PRODUCTION-DECISION-001", noncompensating: true}
[0m
[0m$ [0mrg -n "guard_id:" docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | sed -n '1,80p'
174:    guard_id: "GOVERNED_EXECUTION_IS_CORE_DOMAIN"
184:    guard_id: "DEPENDENCY_CLEAN_KERNEL_EXISTS_BESIDE_HERMES"
194:    guard_id: "WORKFLOW_REDUCER_IS_KERNEL_RESPONSIBILITY"
204:    guard_id: "HERMES_IS_REPLACEABLE_PROPOSAL_DRIVER"
214:    guard_id: "FAIL_CLOSED_CAPABILITY_BUS_MEDIATES_EVERY_EFFECT"
224:    guard_id: "AUTHORITY_EVIDENCE_PERMITS_MODULES_AND_ATOMIC_STATE_ARE_KERNEL_OWNED"
234:    guard_id: "REQUIRED_CAPABILITIES_ARE_QUALIFIED_FIRST_PARTY_MODULES"
244:    guard_id: "LEGACY_PLUGINS_STAY_BEHIND_CONSTRAINED_COMPATIBILITY"
254:    guard_id: "LOCAL_TRACER_RETAINS_WORKFLOW_RUNTIME_PORT"
264:    guard_id: "IMPORT_AND_RUNTIME_FITNESS_TESTS_ENFORCE_ARCHITECTURE"
274:    guard_id: "NOUS_COMMERCIAL_SUBSYSTEM_ABSENT_PROVIDER_NEUTRAL_COST_RETAINED"
284:    guard_id: "DOMAIN_IMPORTS_EXCLUDE_TECHNICAL_AND_HERMES_PACKAGES"
294:    guard_id: "CROSS_CONTEXT_IMPORTS_USE_PUBLIC_API_ONLY"
304:    guard_id: "KERNEL_NEVER_DEPENDS_ON_FIRST_PARTY_MODULES"
314:    guard_id: "ADAPTERS_ARE_CONSTRUCTED_ONLY_AT_COMPOSITION_ROOT"
324:    guard_id: "MODULE_DEPENDENCY_GRAPH_IS_ACYCLIC_AND_MANIFEST_BOUND"
334:    guard_id: "MODULE_IMPORT_HAS_NO_SIDE_EFFECT"
344:    guard_id: "CANONICAL_WRITES_OCCUR_ONLY_IN_AUTHORITY_UNIT_OF_WORK"
354:    guard_id: "EFFECT_REQUIRES_GRANT_AND_RECORDED_ACTIVITY_IDENTITY"
364:    guard_id: "MODULE_CATALOG_CANNOT_OVERRIDE_PERMIT_ISSUER_OR_POLICY_PEP"
374:    guard_id: "INELIGIBLE_MODULE_CANNOT_REGISTER_MIGRATE_RECEIVE_TRAFFIC_OR_EFFECT"
384:    guard_id: "EXECUTION_KERNEL_ALONE_SELECTS_CANONICAL_NEXT_STATE"
394:    guard_id: "NONREPLACEABLE_PEP_ALONE_AUTHORIZES_AND_DISPATCHES_EFFECTS"
404:    guard_id: "EVERY_EFFECT_IS_COMPLETELY_MEDIATED"
414:    guard_id: "POLICY_OR_CHECKER_FAILURE_DENIES_BLOCKING_ACTION"
424:    guard_id: "MAKER_CANNOT_APPROVE_OWN_SUBJECT"
434:    guard_id: "EVIDENCE_AND_APPROVAL_BIND_EXACT_EXECUTION_SUBJECT"
444:    guard_id: "PERMIT_IS_SINGLE_USE_SCOPED_EXPIRING_AND_CHANGE_INVALIDATED"
454:    guard_id: "STATE_AUDIT_PERMIT_AND_OUTBOX_COMMIT_ATOMICALLY"
464:    guard_id: "RETRY_REUSES_LOGICAL_IDEMPOTENCY_IDENTITY"
474:    guard_id: "REDUCER_HAS_NO_HIDDEN_NONDETERMINISM"
484:    guard_id: "REPLAY_IS_DETERMINISTIC_FOR_PINNED_DEFINITION_VERSION_AND_HISTORY"
494:    guard_id: "HISTORY_REMAINS_EXPLAINABLE_AND_NEW_EFFECTS_USE_FRESH_AUTHORITY"
504:    guard_id: "MODULE_CANNOT_WRITE_CANONICAL_STATE_OR_SELF_GRANT"
514:    guard_id: "PLUGIN_FAILURE_CANNOT_WEAKEN_GATE"
524:    guard_id: "HUMAN_WAIVER_NEVER_BECOMES_MACHINE_PASS"
534:    guard_id: "LEGACY_COMMERCIAL_READER_IS_OFFLINE_AND_NONACTIVATING"
544:    guard_id: "LEGACY_NOUS_AUTH_IS_QUARANTINED_AND_NEVER_SILENTLY_TRANSFERRED"
554:    guard_id: "COMMERCIAL_ACCOUNT_AND_PAYMENT_DATA_IS_NEVER_MIGRATED"
564:    guard_id: "LICENSE_COPYRIGHT_PROVENANCE_ATTRIBUTION_AND_HISTORY_ARE_PRESERVED"
574:    guard_id: "PRODUCT_SURFACES_ARE_REBRANDED_WITH_LEGAL_AND_RESEARCH_EXCEPTIONS"
584:    guard_id: "CLEAN_HOST_MAKES_NO_NOUS_NETWORK_REQUEST"
594:    guard_id: "NOUS_IDENTIFIERS_DO_NOT_RESOLVE_AS_RUNTIME_PROVIDER_OR_CATALOG_OWNER"
604:    guard_id: "COMMERCIAL_COMMANDS_RPCS_SCHEMAS_AND_PROXY_ROUTES_ARE_UNREGISTERED"
614:    guard_id: "RUNTIME_PACKAGES_EXCLUDE_NOUS_CREDIT_OAUTH_ENTITLEMENT_AND_PRODUCT_TAGS"
624:    guard_id: "REMOTE_CATALOG_CANNOT_ADD_OR_ACTIVATE_UNPINNED_MODEL"
634:    guard_id: "CANONICAL_DATA_AND_BACKUPS_EXCLUDE_COMMERCIAL_AND_NOUS_AUTH_STATE"
644:    guard_id: "DISTRIBUTION_AND_SBOM_EXCLUDE_COMMERCIAL_IMPLEMENTATION"
654:    guard_id: "ROUTE_CENSUS_FINDS_NO_REACTIVATION_PATH"
664:    guard_id: "MISSING_DIRECT_TOOL_CREDENTIAL_NEVER_FALLS_BACK_TO_NOUS_GATEWAY"
674:    guard_id: "MODEL_FAILURE_NEVER_FALLS_BACK_TO_NOUS"
684:    guard_id: "LEGACY_AUTH_LOAD_HAS_NO_LOGIN_REFRESH_KEY_MINT_OR_NETWORK_EFFECT"
694:    guard_id: "FUZZED_NOUS_HEADERS_HAVE_NO_STATE_OR_POLICY_EFFECT"
704:    guard_id: "BUILT_ARTIFACTS_EXCLUDE_COMMERCIAL_FILES_BUNDLES_PLUGINS_AND_UI_PACKAGE"
714:    guard_id: "PROVIDER_NEUTRAL_COST_AND_BUDGET_TELEMETRY_SURVIVES_REMOVAL"
724:    guard_id: "LICENSE_AND_ATTRIBUTION_VERIFICATION_PASSES"
734:    guard_id: "PRODUCT_IDENTITY_EXCLUDES_HERMES_AND_NOUS_BRANDING"
744:    guard_id: "CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION"
754:    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
764:    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
774:    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
784:    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
794:    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
804:    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
814:    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
825:    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
837:    guard_id: "OWNER_DECIDES_LOCAL_RUNNER_OR_MATURE_DURABLE_RUNTIME"
849:    guard_id: "OWNER_DECIDES_EXACT_AUTHORITY_TRANSACTION_OWNERSHIP"
861:    guard_id: "OWNER_DECIDES_ATLAS_COVERAGE_AND_UNKNOWN_BOUNDARY"
873:    guard_id: "OWNER_DECIDES_PARALLELISM_MAP_AND_COMPENSATION_SEMANTICS"
885:    guard_id: "OWNER_DECIDES_HOT_ACTIVATION_DURING_ACTIVE_EXECUTIONS"
897:    guard_id: "OWNER_DECIDES_ACTIVE_MODULE_STATE_MIGRATION_AND_ROLLBACK"
909:    guard_id: "OWNER_DECIDES_EXTERNAL_EXTENSION_PROTOCOL_AND_CAPABILITIES"
921:    guard_id: "OWNER_DECIDES_POLICY_AUTHORING_LANGUAGE"
933:    guard_id: "OWNER_DECIDES_REVIEWER_INDEPENDENCE_AND_JUDGE_THRESHOLDS"
945:    guard_id: "OWNER_DECIDES_HOST_ISOLATION_PROFILE_AND_PERFORMANCE"
957:    guard_id: "OWNER_DECIDES_RETAINED_HERMES_SESSION_AND_SEARCH_SCOPE"
969:    guard_id: "OWNER_DECIDES_KANBAN_PROJECTION_OR_TABLE_ADAPTER"
981:    guard_id: "OWNER_DECIDES_FUTURE_PROVIDER_NEUTRAL_OPEN_WEIGHT_MODEL"
993:    guard_id: "OWNER_DECIDES_UNRELATED_PAYMENT_TOOL_SCOPE"
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md[90m [limit=230][0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md[90m [limit=170][0m
[0m
[0m$ [0mrg -n "ADR-001[34]|thirteen|fourteen|13 accepted|14 accepted" docs/architecture/README.md README.md docs/README.md | head; echo ===; rg -n -i "linux|macos|windows|host" docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md | head; echo ===; rg -n -i "single-host|local-first|linux" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -10
README.md:189:| Architecture | 13 accepted ADRs · 34 bounded contexts · accepted **on paper** (ADR-0003) |
docs/architecture/README.md:70:   [ADR-0013](./decisions/ADR-0013-promote-hermes-research-obligations.md).
===
12:| Affected contexts | Governed execution, policy, agent collaboration, context compilation, routing, repository intelligence, extension host, artifacts, delivery |
16:| Compatibility/migration class | Initial local single-host profile |
37:| Linux worker isolation | Qualified `bubblewrap` profile for standard local lanes; deny execution when unavailable/unqualified | `SUB-SANDBOX-001`: alternative proves equal or stronger real file/process/network/secret/escape denial and acceptable operability/performance |
47:| Multi-host control | Excluded from the current product | `SUB-MULTIHOST-001`: new product-scope ADR covers consistency, identity, transport, partition, scheduler, operations, backup, security, and migration |
50:isolation by process convention. If a supported host cannot enforce the
80:   Rejected because present scale and single-host scope do not justify their
88:5. **Treat all languages and hosts as supported.** Rejected because honest
===
176:The product is a local-first, one-host, batteries-included modular monolith.
3953:selects the local durable runner, built-in deterministic PDP, qualified Linux
[0m
[0m$ [0mrg -n "ADR-0014|ADR-0013" docs/architecture/README.md; echo ===; sed -n '1,80p' docs/architecture/README.md
70:   [ADR-0013](./decisions/ADR-0013-promote-hermes-research-obligations.md).
===
# Ranex Architecture Documentation

This directory is the normative architecture base for rebuilding Hermes into
Ranex.

The target architecture is accepted as a paper construction contract by
[ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md).
That is neither of the readiness claims defined by
[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md).
`IMPLEMENTATION_START_READY` still requires the exact source/generated
contract, clean committed fork, real cycle/landing/seal, current independent
reviews, finding closure, and human decision. `PRODUCTION_READY` additionally
requires enacted runtime, rule, security, recovery, operational, score, and
authority evidence. Neither tier is currently declared.
After a Tier 1 pass, ordinary authorized product commits may advance on a
clean descendant without circularly revoking admission only while the governed
design/control manifest remains byte-identical; every such commit still uses
the normal per-work controls.

## Read in this order

1. [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md)<br>
   The core product-to-production process: governance, discovery,
   requirements, design, planning, implementation, verification, release,
   operation, improvement, risk lanes, decision rights, measurable flow, and
   evidence-bound capability assessment and improvement priority.
   Its executable stage contracts and stable controls are in the
   [SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md).
   The owner decision making this established SDLC primary and AI work
   subordinate is [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md).

2. [Ranex Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md)<br>
   Makes SWEBOK and every frozen saved engineering book a major, named input to
   requirements, architecture, file structure, construction, verification,
   operation, and improvement while preserving the Core-SDLC authority
   hierarchy. Applicable practices must change the work and its verification,
   not merely appear in a citation list.

3. [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)<br>
   The complete target map: product boundaries, bounded contexts, ownership,
   source tree, dependencies, state, effects, security, operations, migration,
   upstream sync, exclusions, and acceptance gates.
   Its accepted closure is recorded by
   [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md);
   initial quality/SLO/RPO/RTO/security/retention targets by
   [ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md);
   local/static defaults and substitution gates by
   [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md);
   and the machine-checkable 29-decision crosswalk by
   [ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md).
   The canonical modular-DDD repository organization is fixed by
   [ADR-0007](./decisions/ADR-0007-establish-modular-ddd-repository-organization.md),
   and production-path TDD is the default through
   [ADR-0008](./decisions/ADR-0008-make-tdd-the-default-development-discipline.md).
   Exact dependency edges, per-context boundary fit, governed-execution
   coupling triggers, and feedback fitness are fixed by
   [ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md).
   The exact inherited Hermes test baseline, its no-expansion compatibility
   boundary, file-by-file migration proof, expiry, and cutover gate are fixed by
   [ADR-0010](./decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md).
   Ranex-only cross-worker orchestration, role-scoped task-minimal grants,
   leaf-only official runtime adapters, one explicit no-fallback route, strict
   session affinity, and Hermes/Nous inference decommissioning are fixed by
   [ADR-0011](./decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md).
   The noncompensating separation between implementation-start and production
   readiness, including the bounded pre-readiness tooling tracer, is fixed by
   [ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md).
   The exact line-bound promotion of Hermes architecture research obligations,
   blocking owner-choice records, and research-only dispositions is fixed by
   [ADR-0013](./decisions/ADR-0013-promote-hermes-research-obligations.md).

4. [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md)<br>
   Defines authority, evidence, machine contracts, conflicts, RFC/ADR changes,
   and how sliced delivery preserves the full map.

5. [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md)<br>
   Defines roles, packets, handoffs, independent review, verification, permits,
   landing, post-landing checks, and definition of done. It is the governed
   execution subprocess inside the core SDLC.
[0m
[0m$ [0mpython3 -c "
import json
d=json.load(open('legal/licensing-manifest.json'))
print(list(d.keys()))
import re,sys
s=json.dumps(d,indent=0)
" ; rg -n "jsonschema|PyYAML|rfc8785|uv" legal/licensing-manifest.json | head; echo ===; sed -n '1,60p' docs/research/README.md
['schema_version', 'policy_version', 'repository', 'licenses', 'public_platform_exception', 'classification_rules', 'rights_safety', 'files', 'phase_1_requirements']
4259:      "path": "schemas/fixtures/canonical/rfc8785-golden.json",
5397:      "path": "scripts/architecture/uv.lock",
===
# Research inputs

Research informs the architecture but never overrides it
(`../architecture/README.md`, "Research inputs"). Files registered below as
immutable evidence are frozen in content-addressed manifests; **renaming or
moving one of those files breaks digest evidence.** A new draft remains
non-authoritative until it is explicitly reviewed, digest-bound, and promoted
through the architecture process. Files dated 2026-07-27 that cite the retired
`RANEX_IMPLEMENTATION_GUIDE.md` are historical under
[ADR-0002](../architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md).

## Active proposals (not yet architecture decisions)

| File | ID / status | Standing |
|---|---|---|
| [deterministic-run-graph-visualization-research-2026-07-30.md](deterministic-run-graph-visualization-research-2026-07-30.md) | `RES-EXEC-GRAPH-001` v0.2.0 — reviewed draft research proposal | DeepSeek V4 Pro and HY3 both returned `FIT_WITH_CHANGES`; recommends a read-only deterministic run graph and requires an accepted RFC/ADR before any dependency or product implementation |

## Current inputs (accepted decisions or tooling depend on these)

| File | ID / status | Depended on by |
|---|---|---|
| [real-world-sdlc-operating-model-research-2026-07-27.md](real-world-sdlc-operating-model-research-2026-07-27.md) | `RES-SDLC-001` — adopted evidence basis, not normative | [Core SDLC Operating Model](../architecture/CORE_SDLC_OPERATING_MODEL.md) ("Research basis" header row); context for ADR-0001 |
| [ranex-architecture-practice-application-profile.json](ranex-architecture-practice-application-profile.json) | `ENGPROFILE-RANEX-ARCHITECTURE-DESIGN-001` v1.7.0 — design application defined, runtime `NOT_ASSESSED` | SHA-256-pinned inside `scripts/architecture/validate_contracts.py`; cited by `../architecture/README.md` ("Engineering-practice rule"). Do not edit without updating the validator constant |
| [engineering-reference-practice-registry.json](engineering-reference-practice-registry.json) | `ENGREF-PRACTICE-SOURCES-001` v1.1.0 — `SOURCE_RECONCILED_NOT_APPLIED` | Read by `scripts/architecture/generate_contracts.py`; digest-bound inside the profile above |
| [aposd-agent-rules-codebase-design-assessment-2026-07-28.md](aposd-agent-rules-codebase-design-assessment-2026-07-28.md) | `RESEARCH-APOSD-SKILLS-001` v1.2.0 — `RESEARCH_ONLY` | Advisory only; reconciled in [the APOSD review](../architecture/reviews/2026-07-28-aposd-agent-rules-skills-reconciliation.md); registered APOSD as the tenth source family |
| [hermes-core-architecture-research-2026-07-27.md](hermes-core-architecture-research-2026-07-27.md) | Historical study, **and now a promotion source** | [ADR-0013](../architecture/decisions/) promotes 57 provisions from it with per-row line citations and excerpt digests. Editing any promoted line breaks those bindings. The unpromoted material remains advisory — see the ADR for exactly which line ranges were deliberately left in research |

## Historical studies (immutable evidence; no accepted decision depends on their recommendations)

| File | Status | Note |
|---|---|---|
| [gemini-research.md](gemini-research.md) | UNKNOWN (no ID, date, or status header in file) | Added 2026-07-27; frozen in four `.sha256` manifests and `legal/licensing-manifest.json` — must not be renamed |
| [cookbook-alignment-research-2026-07-27.md](cookbook-alignment-research-2026-07-27.md) | Historical | Names the retired implementation guide as primary authority |
| [ocask-alignment-research-2026-07-27.md](ocask-alignment-research-2026-07-27.md) | Historical | Same retired-guide framing |
| [hermes-core-architecture-research-2026-07-27.md](hermes-core-architecture-research-2026-07-27.md) | **Moved to Current inputs above** — ADR-0013 promotes from it | Paired with the HY3 review below |
| [hermes-core-architecture-hy3-review-2026-07-27.md](hermes-core-architecture-hy3-review-2026-07-27.md) | Historical advisory review; no transition authority | Cross-family review of the file above |
| [ranex-sdlc-full-spec.svg](ranex-sdlc-full-spec.svg), [ranex-sdlc-visual-guide.html](ranex-sdlc-visual-guide.html) | Historical visuals | Whether they still match `POL-SDLC-001` v1.5.0 is UNKNOWN; reviewed by the file below |
| [ranex-sdlc-visual-hy3-review-2026-07-27.md](ranex-sdlc-visual-hy3-review-2026-07-27.md) | `REV-SDLC-VISUAL-HY3-001` — advisory | Review of the two visuals |

## Local-only (git-ignored; not in the repository you cloned)

- `books/` — full-text reference works; represented publicly by the
  [live-corpus manifest](../architecture/reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256).
- `kimi-research/` — raw Kimi corpus; represented publicly by the
  [Kimi manifest](../architecture/reviews/artifacts/2026-07-27/kimi-research-manifest.sha256).
[0m
[0m$ [0mrg -n "jsonschema|pyyaml|PyYAML|rfc8785" legal/licensing-manifest.json | head -10; echo ===; git grep -n -i "mypy\|pyright\|pyrefly" -- ':!docs' | head; echo ===; rg -n "context_dependency_edges|dependency_edges:|edges:" docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md | head; echo ===; sed -n '70,80p;180,195p' docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md
4259:      "path": "schemas/fixtures/canonical/rfc8785-golden.json",
===
LICENSE:3:Copyright (c) 2025 Nous Research
LICENSE:12:The above copyright notice and this permission notice shall be included in all
LICENSE:18:AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LICENSE-RANEX.md:3:Copyright (c) 2026 Anthony Garces. All rights reserved.
LICENSE-RANEX.md:23:copyright, license, attribution, and source notices must remain intact.
LICENSE-RANEX.md:38:5. remove, hide, or alter a copyright, license, provenance, or attribution
LICENSE-RANEX.md:84:TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
NOTICE.md:1:# Ranex Copyright and License Notice
NOTICE.md:10:Copyright (c) 2025 Nous Research.
NOTICE.md:19:Copyright (c) 2026 Anthony Garces. All rights reserved.
===
88:edges:
===
configuration management, independent verification, secure development,
release engineering, operations, incident response, measurement, or
improvement. Those disciplines predate generative AI and have a broad standards
and empirical basis.

The owner explicitly directed that Ranex architecture be organized around the
researched software-development process and drive AI agents through that
process—not allow agent orchestration to organize or redefine software
development.

## Alternatives considered
   estimate binding, capacity, dependency, risk, acceptance basis, or expired
   window rejects reliance on the old commitment until a fresh exact-subject
   human decision resolves.

## Human approval

The human owner explicitly approved this direction in the authenticated project
conversation on 2026-07-27: established software-development practice is the
main base for Ranex, and AI agents are workers required to follow it. This ADR
is the durable repository record of that owner decision; it does not claim a
cryptographic signature or runtime permit.

## Supersession rule

This ADR is not edited to reverse its decision. A replacement ADR names and
supersedes it.
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('legal/licensing-manifest.json'))
s=json.dumps(d).lower()
for t in ['jsonschema','pyyaml','yaml','rfc8785','dependency','dependencies','third']:
    print(t, s.count(t))
print(list(d.get('phase_1_requirements',{}))[:10] if isinstance(d.get('phase_1_requirements'),dict) else str(d.get('phase_1_requirements'))[:300])
EOF
jsonschema 0
pyyaml 0
yaml 37
rfc8785 1
dependency 7
dependencies 1
third 356
['Retain upstream LICENSE unchanged.', 'Classify every new Ranex file.', 'Add an explicit entry for every modified upstream file.', 'Never claim ownership of upstream material.', 'Reject any LOCAL_ONLY or PROHIBITED_PENDING_RIGHTS path present in the Git index, public release, package, mirror, or de
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('legal/licensing-manifest.json'))
# find mentions of dependency
def walk(o,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            walk(v,path+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o):
            walk(v,f'{path}[{i}]')
    else:
        if isinstance(o,str) and 'depend' in o.lower():
            print(path,'=>',o[:200])
walk(d)
EOF
/files[13]/path => architecture/contracts/context-dependency-edges.json
/files[127]/path => docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md
/files[194]/path => docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml
/files[364]/path => schemas/common/context-dependency-edge-v1.schema.json
/files[508]/path => schemas/planning/dependency-authority-registry-v1.schema.json
/files[509]/path => schemas/planning/dependency-snapshot-authority-row-v1.schema.json
/files[534]/path => schemas/review/independence-evaluation-v1.schema.json
/files[548]/provenance_kind => GENERATED_DEPENDENCY_LOCK
/files[548]/redistribution => SUBJECT_TO_RANEX_LICENSE_AND_DEPENDENCY_METADATA_RIGHTS
/files[548]/notes => Generated resolution metadata only; it does not vendor dependency source or replace the licenses applicable to resolved packages.
[0m
[0m$ [0msed -n '585,600p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo ===; sed -n '3945,3960p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo ===; sed -n '270,285p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo ===; sed -n '18,40p' docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
## 11. Complete target repository map

The tree is the end-state destination map. Directories may be populated in safe
slices, but their ownership and dependency positions are fixed now.

```text
ranex/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE
├── LICENSE-RANEX.md
├── NOTICE.md
├── src/
│   └── ranex/
│       ├── foundation/
===
compiler. The generated `architecture-elements.json` registry, its
`counts_by_kind`, and the exact matching assessment registry are authoritative
for the resulting current denominator; an accepted additive row inherits the
same closed-definition, parent-resolution, and `NOT_ASSESSED` runtime rules.

## 34. Selected defaults and evidence-triggered substitution gates

[ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md)
selects the local durable runner, built-in deterministic PDP, qualified Linux
`bubblewrap` lane, deterministic context/routing/workflow rules, single-worker
default, release-pinned lease profile, versioned stdio extension protocol,
separately protected artifact anchor, inactive voice, and exclusion of
multi-host control. Those are construction defaults, not open implementation
choices.

Each named `SUB-*` gate in ADR-0005 is a substitution gate: evidence may
===
    the same state and commands.
15. Every retry preserves the same logical idempotency identity or becomes a new
    explicitly related attempt.
16. `OUTCOME_UNKNOWN` is a first-class result and must enter reconciliation.
17. Importing a module causes no registration, environment read, file access,
    network access, thread creation, migration, or other side effect.
18. No external Python plugin runs inside the authority process.
19. Secrets are opaque handles until resolved at the authorized adapter edge.
20. Raw prompts, source, and model output are classified artifacts, not routine
    telemetry.
21. Cross-project data does not enter packets, prompts, workspaces, artifacts,
    logs, learned knowledge, or route-training data without explicit sanitized
    transfer authority.
22. Every upstream synchronization reruns the same de-commercialization,
    architecture, provenance, security, and release gates as a product release.
23. A worker run, merge, deployment, incident, or model observation cannot
===
## Decision

ADR-0008 remains the sole target test-layout policy. The accepted Hermes
upstream-derived source, however, contains inherited tests outside that target.
Deleting, moving, or relabeling them merely to make a topology check green
would destroy regression evidence and increase upstream-sync risk.

Ranex therefore accepts one bounded, immutable compatibility baseline:

- unchanged baseline files may continue to execute as inherited regression
  evidence;
- they do not establish Ranex TDD enactment, architecture conformance, gate
  `PASS`, or migration completion;
- no new Ranex test may be created in an inherited root or directly under
  `tests/`;
- any added file in a legacy or direct-top-level scope is a blocking
  recontamination finding; a change exception cannot enlarge the baseline;
- an in-place content change to an existing baseline path requires a
  registered, expiring change exception and migration review before landing;
- a move or rename is a migration: its new path must be canonical under
  ADR-0008 and it requires complete migration proof, never a change exception;
- intentional retirement is authorized only by ADR-0008's canonical
  `TestDeletionRecordV1`, for either the exact legacy source or a later stable
[0m
[0m$ [0msed -n '1,30p' scripts/architecture/test_contract_concurrency.py; echo ===; rg -n "pytest" scripts/architecture/*.py scripts/architecture/uv.lock | head; echo ===; sed -n '1,40p' scripts/architecture/README.md
#!/usr/bin/env python3
"""Deterministic concurrency regression for contract generation/validation.

The test runs only in a disposable repository copy.  It proves that:

* a validator cannot observe the generator's empty-denominator cleanup window;
* a second generator cannot enter while another publisher owns the lock; and
* publication followed by validation reproduces the same complete tree.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from contract_tree_lock import contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOTS = (
    Path("architecture/contracts"),
    Path("schemas"),
    Path("docs/architecture/assessments"),
===
===
# Architecture contract tooling

Run from the repository root:

```sh
uv run --project scripts/architecture \
  python scripts/architecture/generate_contracts.py
uv run --project scripts/architecture \
  python scripts/architecture/validate_contracts.py
uv run --project scripts/architecture \
  python scripts/architecture/test_contract_concurrency.py
```

`generate_contracts.py` deterministically derives registries, JSON Schemas,
architecture-element inventory, capability-assessment baselines, domain
projections, fixtures, and completeness reports from the accepted normative
documents and authoring templates.

`validate_contracts.py` rejects duplicate YAML keys, schema drift, registry
referential-integrity defects, manifest drift, forged digests, permit reuse,
subject mismatches, stale subjects, incomplete VITAL profiles, arithmetic
capability aggregation, and dishonest runtime scoring.

Generation and validation both hold the same repository-scoped interprocess
lock from their first read through their final write. The lock is outside all
generator-owned trees, so a validator or second writer waits rather than
observing a partial cleanup/publication. `test_contract_concurrency.py` verifies
that behavior in a disposable repository copy by staging an empty assessment
denominator, contending with both a validator and second generator, and
requiring the post-release tree digest to equal its baseline.

The validation report binds the exact generator, validator, lock module, and
concurrency-regression script digests alongside the registry, schema, practice
profile, and assessment-subject digests.

Full validation has two prerequisites that are intentionally outside a normal
working-tree file snapshot:

- the repository must retain its Git history and object database because
  inherited-layout validation resolves committed ancestry and the bound legacy
[0m
[0m$ [0mrg -n "No external Python plugin|generated Python/TypeScript|OTLP|keyring/file/vault|local-first, one-host" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo ===; rg -n "packages/generated-contracts|generated language bindings|TypeScript" docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
176:The product is a local-first, one-host, batteries-included modular monolith.
276:18. No external Python plugin runs inside the authority process.
572:| Authentication/secrets | `identity_access` | keyring/file/vault/OAuth adapters | identity/session/secret lifecycle | Principal or secret handle |
575:| Observability/operations | `operations` | OTLP/log/metric exporters | incident/health lifecycle | Noncanonical telemetry |
583:| Contract/schema generation | `configuration_management` orchestrates from accepted source-owner registries | deterministic contract compiler and language generators | source context owns semantics; `configuration_management` owns baseline/reproducibility | Registry digest, generated Python/TypeScript packages, drift/audit result |
===
49:├── packages/generated-contracts/   # generated language bindings
178:  `packages/generated-contracts`; generated documentation lives under
221:docs, tools, `legacy`, worktrees, and generated TypeScript are excluded.
[0m
# Ranex technology-stack derivation

Preliminary correction to the intake premise: the corpus contains **fourteen** accepted ADRs, not thirteen. `architecture/contracts/accepted-adrs.json` registers ADR-0001…ADR-0014 all `ACCEPTED` (verified by parsing the registry), and `docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:7` is `Status: ACCEPTED`, decision date 2026-07-30. The intake's "thirteen" matches the stale `README.md:189` ("13 accepted ADRs") and `docs/README.md:21` ("ADR-0001 … ADR-0012, all ACCEPTED"), both of which lag the registry. This changes the answer to test-question 1 materially.

---

## Stack table

| Layer | Classification | Choice | Citation | Binding obligations |
|---|---|---|---|---|
| Implementation language + version | **DECIDED** | Python, min `3.12`, per-package declared upper bound, for every component (tooling, kernel, adapters, tests) | `LANG-PRIMARY-001`, docs/architecture/decisions/ADR-0014-...md:91–96 | AI-worker generation reliability named as engineering property (ADR-0014:105–108); dep surface auditable (ADR-0014:109–111); supersession only via `LANG-EXCEPTION-001` (ADR-0014:133–164) which requires ADR-0004 budget, measured breach, cheaper-mitigation record, port boundary per ADR-0007, byte-identical differential proof + fail-closed, reproducible licence-clean build, owner authorization |
| Compiled-language escape hatch | **DECIDED** (path only, inert) | Narrow gated path; no compiled artifact may exist without recorded owner authorization | ADR-0014:133–164, acceptance test 4 at ADR-0014:201–203 | Compiled path may not hold canonical state or make authority decisions (ADR-0014:153–155) |
| Runtime/execution topology | **DECIDED** | Release-pinned modular monolith, local-first, one host; contexts are packages not services; multi-host excluded | ADR-0003:29–34; HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:176; DEC-RANEX-001 ADR-0006:34–41; ADR-0005:47 | `SUB-TOPOLOGY-001`/`SUB-MULTIHOST-001` substitution gates (ADR-0005:34,47); FF-BOUNDARY-001 (ADR-0003:110) |
| Workflow runtime | **DECIDED** default + **OWNER_DECISION_REQUIRED** later | Ranex local durable runner behind runtime port (Temporal explicitly rejected initially) | ADR-0005:35, ADR-0005:79–81; DEC-RANEX-013 ADR-0006:130–137 | `HERMES-OWNER-DECISION-002` (ADR-0013:835–846) reserves "local runner vs mature durable runtime" to owner, blocking at `PRODUCTION_READY`; `SUB-RUNNER-001` parity gate ADR-0005:35 |
| Worker isolation host | **DECIDED** (Linux lane) / **OWNER_DECISION_REQUIRED** (final profile) | Qualified `bubblewrap` profile; write-capable execution fails closed on unsupported host | ADR-0005:37, ADR-0005:49–52 | `HERMES-OWNER-DECISION-011` (ADR-0013:943–954) reserves host isolation profile + acceptable performance, blocking `PRODUCTION_READY`; FF-SBX-001 ADR-0005:98. Non-Linux hosts: OPEN — corpus only defines the Linux lane |
| Durable storage + transaction model | **DECIDED** | Single local SQLite authority DB; logical per-context ownership; journal + outbox; state+audit+outbox in one SQLite unit of work; selective (Execution-only) event sourcing | DEC-RANEX-011 ADR-0006:114–121; DEC-RANEX-012 ADR-0006:122–129; HERMES-PROMOTION-061 ADR-0013:772–781; ADR-0007:157–158; ADR-0004:48,62 | RPO=0 committed authority transactions (ADR-0004:49); atomic commit guard ADR-0013:454; ephemeral **real** SQLite in test lanes, no in-memory substitutes (ADR-0008:163–166). Reserved: exact transaction ownership `HERMES-OWNER-DECISION-003` (ADR-0013:847–858, blocks `IMPLEMENTATION_START`); consistency grouping `-019` (ADR-0013:1039–1050); event-sourcing activation `-020` (ADR-0013:1051–1062). `BEGIN IMMEDIATE` serialization is measured tracer evidence only (ADR-0014:78–79), not a decided provision |
| Schema definition + validation | **DECIDED** | JSON Schema, one canonical copy per owning area; generated projections with digests; RFC 8785 canonicalization + SHA-256 | ADR-0007:176–181; ORG-GENERATED-001 ADR-0007:261; ADR-0012:95–97; `schemas/common/canonical-digest.schema.json` | Validator library `jsonschema==4.25.1` + `rfc8785==0.1.4` are pinned tooling facts cited as ADR-0014 evidence (ADR-0014:47–49), substitutable as a pre-compiled-component mitigation (ADR-0014:82–87) — pin level DECIDED-by-evidence, library identity not contractually fixed |
| Policy definition + evaluation | **DECIDED** pattern / **OWNER_DECISION_REQUIRED** language | Built-in deterministic, versioned, local PDP behind policy port; offline-deny; fail-closed PEP with pure domain decisions | ADR-0005:36; DEC-RANEX-015 ADR-0006:146–153; HERMES-PROMOTION-063 ADR-0013:792–801; FF-PDP-001 ADR-0005:97 | Policy **authoring language** ("typed Python or JSON rules versus OPA or Cedar") is `HERMES-OWNER-DECISION-009` (ADR-0013:919–930), blocking `MODULE_ACTIVATION`, no default, absence = BLOCK. OPA-first rejected at ADR-0005:79–81 |
| AI provider integration + routing | **DECIDED** | Sole Ranex orchestrator, leaf-only workers; one explicit release-pinned provider/model/adapter/auth route per assignment; all fallback + auxiliary model calls disabled; initial adapters = official Claude Agent SDK and Codex SDK/app-server (JSON-RPC/JSONL stdio); no Hermes/Nous inference route ever | ADR-0011:21–62, 85–116, 184–191; catalog ADR-0011:203–445; DEC-RANEX-025/026/027 ADR-0006:226–249 | FF-NO-FALLBACK-001 ADR-0011:471; FF-AUTH-ROUTE-001 ADR-0011:474; new providers only via accepted catalog revision + qualification (ADR-0011:117–121); review gates pin OpenCode HY3 + DeepSeek reviewer routes (ADR-0012:562–563) as evidence sources, never authority (README.md:159–161) |
| Dependency + package management | Split: pinning **DECIDED**; `pyproject` layout **IMPLIED**; `uv` **INHERITED_UNDECIDED** | Pins/locks mandatory; target root carries `pyproject.toml` + `uv.lock` in the accepted architecture tree; but no decision names uv | Pinning: FF-SUPPLY-001 ADR-0006:284; ADR-0008 Tier-2 `dependency_lock_digest` ADR-0008:719–732. Layout: HERMES_GROUND_ZERO...md:592–593 (accepted via ADR-0003:21–23). uv usage: README.md:202–203; scripts/architecture/pyproject.toml:12–13 (`[tool.uv]`); uv.lock classified `GENERATED_DEPENDENCY_LOCK` legal/licensing-manifest.json:5397 | No ADR selects uv. It is load-bearing for the only executable verification path (README.md:201–204). See Finding F4 |
| Test discipline | **DECIDED** (exhaustively) | TDD default with typed cycle records, change profiles, Tier-1/2 reproducibility envelopes, production-path/build-once invariant, canonical `tests/` taxonomy | ADR-0008:22–58, 119–126, 137–166, 218–230; ORG-TEST-MIRROR-001 ADR-0007:260; inherited-layout quarantine ADR-0010:18–40 | READY-TDD-CYCLE-001 / READY-LANDING-001 gate `IMPLEMENTATION_START` (ADR-0012:559–560) |
| Test framework (runner) | **IMPLIED** family / **OPEN** tool | Must be Python (all tests are Python per LANG-PRIMARY-001, ADR-0014:92–93) and must emit typed, deterministic, machine-checkable step results (ADR-0008:65–73). No accepted artifact names a runner. `pytest>=9` exists only in the git-ignored kernel-tracer worktree (`.claude/worktrees/kernel-tracer/pyproject.toml`, dev group; ignored per .gitignore:1) — INHERITED_UNDECIDED in practice | | Tracked tooling test is a plain script, no framework (scripts/architecture/test_contract_concurrency.py:1–20) |
| Static type checking | **DECIDED** obligation / deliberately **OPEN** tool | Strict-mode checker required per package; failure blocks at `IMPLEMENTATION_START`; checker selection deferred to evidence-at-selection-time, conformance preferred over speed; currently recorded **unsatisfied**, fail-closed | LANG-TYPECHECK-001 ADR-0014:113–131; ADR-0014:197–199, 215–217 | Runtime boundary validation additionally required; unvalidated boundary value fails closed (ADR-0014:127–131) |
| Linter | **INHERITED_UNDECIDED** | `ruff` pinned only in ignored kernel-tracer worktree; ADR-0014:67 states ruff "does not discharge" the type-check obligation; no decision adopts a linter | `.claude/worktrees/kernel-tracer/pyproject.toml` (`ruff>=0.15.10`); ADR-0014:66–67 | |
| Build/CI enforcement | **DECIDED** obligations / **OPEN** CI system | Deterministic generator+validator with interprocess lock and tree digest (README.md:206–209; scripts/architecture/README.md:14–31); hand-editing generated files "fails CI" (docs/architecture/AI_ARTIFACT_CONTRACTS.md:595); build-once content-digested candidate (ADR-0008:147–149); 21 noncompensating readiness gates, 11+10 (ADR-0012:554–575) | | No CI configuration exists in the tracked tree (no `.github/`; root listing). CI vendor undecided; GitHub is the origin host and a delivery edge (decisions/local-values.env.example:11–13; DEC-RANEX-021 ADR-0006:196) |
| Observability, audit, evidence storage | **DECIDED** pattern / **OPEN** backend | Append-only journal as replay/audit oracle (HGZ:473); daily separately protected signed/witnessed anchor (ADR-0005:45; ADR-0004:70–73); structured allowlist logging + redaction (ADR-0004:91–92); OTLP/log/metric exporters as noncanonical telemetry (HGZ:575); retention schedule ADR-0004:98–106; evidence digest-bound to exact subjects (ADR-0003:50–59) | | Anchor substitution gated by `SUB-ANCHOR-001` ADR-0005:45; FF-ANCHOR-001 ADR-0004:136. Concrete exporter/collector: nothing decided beyond the protocol-family word "OTLP" |
| Secrets + credentials | **DECIDED** pattern / **OPEN** backend | Opaque handles resolved only at authorized adapter edge (HGZ:276–277 item 19; ADR-0004:86–88); keyring/file/vault/OAuth adapters under `identity_access` (HGZ:572, 783–784); workers start secret-value-denied (ADR-0004:84–85); credential file extraction DENIED (ADR-0011:370, 429); backups exclude raw secrets, secret backend backs itself up (HGZ:3475) | | Which keyring/vault implementation: undecided |
| Owner interface surface | **DECIDED** classes / reserved item / **OPEN** toolkits | CLI, TUI, loopback web, GitHub edge, text-phone (Telegram first) (DEC-RANEX-021/022 ADR-0006:194–209); desktop excluded (DEC-RANEX-020 ADR-0006:186–193); public binding excluded (DEC-RANEX-024 ADR-0006:218–225); loopback + authenticated expiring sessions (ADR-0004:81–83); channel-neutral contracts FF-DELIVERY-001 ADR-0006:286 | | Electron/desktop-bootstrap retention reserved: `HERMES-OWNER-DECISION-017` ADR-0013:1015–1026, blocks `IMPLEMENTATION_START`. Web/TUI frameworks: nothing decided |
| Packaging + distribution | Constrained, partly **OPEN** | Declarative `deploy/` assets (ADR-0007:52, 194–195); release manifest pins dependencies/providers (FF-SUPPLY-001 ADR-0006:284); built artifacts exclude all commercial/Nous surfaces (ADR-0013 guards :644, :704); licence: upstream MIT + Ranex Personal-Use 1.0 — source-available, **no redistribution or commercial use** absent separate grant (LICENSE-RANEX.md:5, 27–44; NOTICE.md:13–32); a "distributed Ranex product" is contemplated but must use customer-owned credentials/vendor-approved routes (ADR-0011:151–157) | | Channel/registry/installer: undecided. Any distribution beyond personal use requires an owner licensing act outside current terms (LICENSE-RANEX.md:27–29) |
| Migration tooling | **DECIDED** pattern / **OPEN** tool | Context-owned SQLite migrations at `src/ranex/<context>/adapters/persistence/sqlite/migrations/`; `src/ranex/migration` owns only cross-context ordering/verification/rollback (ADR-0007:183–190); ORG-MIGRATION-001 ADR-0007:262; FF-ORG-006 ADR-0007:312; strangler migration from Hermes (DEC-RANEX-008 ADR-0006:90–97; ADR-0003:141–145) | | Raw-SQL file exists only in ignored tracer worktree (`.../migrations/001_execution_kernel.sql`). No migration framework named |
| Extension surface (corpus-implied layer) | **DECIDED** | Versioned JSON-RPC 2.0 over local stdio, out-of-process, capability-scoped, outside authority | ADR-0005:44; DEC-RANEX-019 ADR-0006:178–185 | Protocol/capability vocabulary detail reserved: `HERMES-OWNER-DECISION-008` ADR-0013:907–918 |
| Repository-intelligence language coverage (corpus-implied layer) | **DECIDED** initial set | Python, TypeScript/JavaScript, Markdown, YAML/JSON, POSIX shell; everything else returns `UNKNOWN` | ADR-0005:43; `SUB-LANG-001` same row | Atlas coverage/UNKNOWN boundary reserved: `HERMES-OWNER-DECISION-004` ADR-0013:859–870 |
| Generated language bindings (corpus-implied layer) | **DECIDED** existence, **OPEN** toolchain | `packages/generated-contracts/` generated bindings incl. TypeScript (ADR-0007:49, 178; HGZ:583); generated TS excluded from Python discovery (ADR-0007:220–221) | | A TS generation toolchain is eventually implied; nothing selects it |

## Findings

**F1 — Stale decision inventory in the routing documents. Severity: MEDIUM.**
`README.md:189` claims "13 accepted ADRs"; `docs/README.md:21` claims "ADR-0001 … ADR-0012, all ACCEPTED"; `docs/architecture/README.md` reading order ends at ADR-0013 (line 70) and never mentions ADR-0014. The registry (`architecture/contracts/accepted-adrs.json`) carries 14 `ACCEPTED` entries including ADR-0013 v1.4.0 and ADR-0014 v1.0.0. By the corpus's own standard — "an unreported inference is a defect regardless of whether it is correct" (ADR-0014:37–39) — the entry-point documents misstating the accepted decision set is a defect. It also propagated into this task's intake premise.

**F2 — ADR-0014 factual reason 5 not corroborated by the licensing manifest. Severity: MEDIUM.**
ADR-0014:109–111 states the three pinned tooling dependencies and the kernel dependency "each carr[y] a licensing-manifest entry." `legal/licensing-manifest.json` contains zero occurrences of `jsonschema`, `PyYAML`/`pyyaml`-as-package, or `rfc8785`-as-package (verified by full-text scan); the only related entry is `scripts/architecture/uv.lock` classified `GENERATED_DEPENDENCY_LOCK` (legal/licensing-manifest.json:5397, files[548]), whose own note says it "does not vendor dependency source or replace the licenses applicable to resolved packages." Either the ADR's evidence claim is inaccurate or "entry" was meant loosely as the lock-file entry; under FF-SUPPLY-001 (ADR-0006:284) and `LICENSE_AND_ATTRIBUTION_VERIFICATION_PASSES` (ADR-0013:724) this ambiguity is checkable and currently unfavourable.

**F3 — Version-ceiling timebomb, self-flagged. Severity: LOW-MEDIUM.**
Kernel tracer pins `>=3.11,<3.15` (ADR-0014:48–49; confirmed in the ignored worktree `pyproject.toml`); Python 3.15 releases ~2026-10-01, ~3 months post-decision (ADR-0014:69–70). ADR-0014:223–224 requires deliberate revisit. Tracked, but no work item is visible in the tree that owns the revisit.

**F4 — `uv` is an undeclared load-bearing tool choice — the same defect class ADR-0014 just closed for the language. Severity: MEDIUM.**
The only executable verification path the corpus offers runs through `uv` (`README.md:202–203`, `scripts/architecture/README.md:5–12`), `uv.lock` is tracked and licence-classified, and `pyproject.toml`+`uv.lock` sit in the **accepted** target repository map (HGZ:592–593, accepted by ADR-0003:21–23). No decision record selects uv. ADR-0014:34–39 defines exactly this pattern ("load-bearing and undeclared") as a defect class. Not currently a rule violation — no rule governs it — which is the finding.

**F5 — Local ignored worktrees contain excluded-surface and off-language material. Severity: LOW (contained by .gitignore and ADR-0007 quarantine).**
`.claude/worktrees/*` (ignored, .gitignore:1) contain inherited Hermes source, Node `node_modules`, and a Tauri desktop `bootstrap-installer` (`.claude/worktrees/phase-1-adopt-upstream/apps/bootstrap-installer/src-tauri/Cargo.toml` — Rust/compiled, general engineering knowledge, not a corpus fact). Desktop is excluded by DEC-RANEX-020 (ADR-0006:186–193), the desktop-bootstrap question is reserved by HERMES-OWNER-DECISION-017 (ADR-0013:1015–1026), and compiled artifacts in "Ranex packages" would fail ADR-0014 acceptance test 4 (ADR-0014:201–203). ADR-0007:220–221 excludes worktrees from discovery, so no accepted rule is violated by the tracked tree; the material is a recontamination risk consistent with ADR-0010's concern class (ADR-0010:30–33).

**F6 — Research README count drift. Severity: LOW.**
`docs/research/README.md:29` says ADR-0013 "promotes 57 provisions"; ADR-0013:168 declares `promoted_provision_count: 65` (v1.4.0). Stale by two revisions of a digest-sensitive catalog.

**F7 — Declared, compliant gap (not a conflict): type checking.**
`LANG-TYPECHECK-001` is recorded unsatisfied and blocking at `IMPLEMENTATION_START` (ADR-0014:215–217); no checker config exists in the tracked tree (searched: no pyrightconfig/mypy config). This is the fail-closed behaviour the corpus requires (ADR-0014:197–199) — reported to confirm the tree matches its own declaration.

## Open layers

Per instruction, no winners are picked; options + Ranex-specific tradeoff + settling evidence only.

1. **Type checker (selection deliberately open).** Options named by the corpus itself: Pyright (~97.8% conformance), Pyrefly (stable, faster), ty (alpha), mypy (~58%) — ADR-0014:63–67. Ranex-specific tradeoff is pre-resolved by rule: conformance beats speed (ADR-0014:122–124). Settling evidence: conformance/performance figures **current at selection time**, recorded, pinned (ADR-0014:119–125).
2. **Test runner.** Constraint chain: Python-only (ADR-0014:92–93) + per-step typed checker references and immutable step snapshots (ADR-0008:65–73) + Tier-2 toolchain digests (ADR-0008:719–732). Options: pytest (already in the tracer's dev deps), unittest (stdlib, smaller supply-chain surface per ADR-0014:109–111 logic), a bespoke deterministic harness (the tracked tooling already runs framework-free — scripts/architecture/test_contract_concurrency.py). Tradeoff that matters here: machine-parseable, forgery-resistant result artifacts vs. ecosystem convenience for AI workers. Settling evidence: whether a candidate can emit the `TddCycleRecordV1`/`ExpectedFailureFingerprintV1` shapes (ADR-0008:65–73) without a wrapper that itself becomes untyped glue.
3. **CI system.** No config exists; obligations are host-agnostic (deterministic scripts + digests, ADR-0008:147–149, README.md:206–209). GitHub is origin host and delivery edge (decisions/local-values.env.example:11–13; ADR-0006:196), which weakly points at GitHub Actions, but local-first posture (HGZ:176) and human-controlled landing (DEC-RANEX-029 ADR-0006:258–265) permit a purely local enforcement runner. Settling evidence: where `READY-*` gate evaluations are produced and how their evidence is digest-bound off-host (ADR-0004:70–73 anchor requirement).
4. **Policy authoring language.** Reserved, not open to implementers: `HERMES-OWNER-DECISION-009` (ADR-0013:919–930). Options the corpus itself names: typed Python rules, JSON rules, OPA, Cedar. Ranex-specific tradeoff: a non-Python evaluator adds a second language runtime against LANG-PRIMARY-001's single-language rationale (ADR-0014:98–111) and the supply-chain surface FF-SUPPLY-001 polices; a Python DSL keeps the fail-closed PEP (ADR-0013:792–801) in one type-checked codebase but forfeits an externally audited engine. Settling artifact: an accepted ADR with predeclared acceptance test (ADR-0013:830).
5. **Secrets backend, telemetry backend, web/TUI frameworks, migration framework, packaging channel.** All pattern-decided, tool-undecided (citations in table). Settling evidence in each case is the corpus's uniform mechanism: qualification against the named fitness functions (FF-SEC-001 ADR-0004:134, FF-RET-001 ADR-0004:135, FF-DELIVERY-001 ADR-0006:286, FF-ORG-006 ADR-0007:312) plus release-profile pinning (ADR-0005:73).
6. **Non-Linux runtime hosts.** Only a Linux bubblewrap lane exists; unsupported host = fail-closed denial of write-capable work (ADR-0005:49–52). Settling evidence: a separately named, qualified sandbox lane per `SUB-SANDBOX-001` (ADR-0005:37) and the owner's `-011` decision.

**Test-question 2 (does the governance model favour a language property?), argued from cited obligations:**
- *Against the chosen family:* the product's premise is enforcement the worker cannot negotiate; Python's annotations enforce nothing at runtime, and this concretely produced a security-relevant defect (ADR-0014:59–62). Determinism obligations (FF-ORCH-001 ADR-0005:95; reducer purity ADR-0013:754,474) and fail-closed boundaries (ADR-0013:794–801) are exactly where an unenforced type crossing is most expensive.
- *For it:* the enforced obligations are document/schema checks, measured non-compute-bound (ADR-0014:98–104, 50–58, 74–81); the labour force is AI workers and generation reliability is declared an engineering property of the language choice (ADR-0014:105–108 under ADR-0001/ADR-0011); the only components that execute and pass are Python (ADR-0014:102–104); the dependency surface stays small (ADR-0014:109–111).
- *Which argument the corpus's priorities support:* the corpus resolved this itself rather than leaving it to inference — it takes the second argument **conditional on** neutralizing the first: mandatory strict static checking blocking at `IMPLEMENTATION_START` plus mandatory runtime validation at every trust boundary, fail-closed (ADR-0014:113–131), plus a measured, owner-authorized compiled escape hatch that can never touch authority decisions (ADR-0014:133–164). Rejected alternative 4 (ADR-0014:181–183) states the trade explicitly.

## Inferences

Every non-quoted conclusion above, with prompting evidence:

1. **The corpus has 14 accepted ADRs; the intake's "thirteen" is stale.** Prompted by `accepted-adrs.json` parse + ADR-0014:7. (Basis: registry is the corpus's own machine authority, README.md:206–209.)
2. **Test runner must be a Python-family tool.** Inference from LANG-PRIMARY-001 covering "tests" (ADR-0014:92–93); no artifact states a runner.
3. **GitHub-hosted CI is weakly implied, not decided.** Inference from decisions/local-values.env.example:11–13 + ADR-0006:196. Marked weak; local-first posture cuts the other way.
4. **`pyproject`-based packaging is "IMPLIED-accepted."** Inference from the accepted target tree containing `pyproject.toml`/`uv.lock` (HGZ:592–593) under ADR-0003's acceptance of that document (ADR-0003:21–23). The tree is a "destination map" (HGZ:587), so file-level entries carry less decisional force than ADR provisions — that discount is itself an inference.
5. **The uv.lock manifest entry does not satisfy "each carrying a licensing-manifest entry."** Interpretive inference behind Finding F2; the charitable alternative reading is stated there.
6. **Worktrees fall outside "any Ranex package" for ADR-0014 acceptance test 4.** Inference from ADR-0007:220–221 (worktrees excluded from discovery) + .gitignore:1.
7. **"OTLP" names a protocol family, not an implementation decision.** Inference from the single occurrence HGZ:575 in an adapter-boundary table.
8. **Tauri = Rust/compiled; bubblewrap = Linux-only mechanism.** General engineering knowledge, not corpus facts (the corpus does independently label the lane "Linux worker isolation," ADR-0005:37).
9. **pytest/ruff versions in the kernel tracer are practice, not decision.** Inference from their absence in any ADR + ADR-0014:66–67 explicitly declining to let ruff discharge an obligation.
10. **`BEGIN IMMEDIATE` is evidence, not a decided provision.** Inference from its appearance only in ADR-0014's evidence narrative (ADR-0014:78–79) and the tracer's non-authoritative self-description (`.claude/worktrees/kernel-tracer/pyproject.toml` description: "Non-authoritative R&D tracer").
11. **Severity assignments** throughout are my judgment calibrated to the corpus's own defect standard (ADR-0014:36–39) — general engineering judgment, not corpus rules.

## Coverage

- Read in full: README.md, docs/README.md, ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0011, ADR-0014; ADR-0008 lines 1–230 + targeted sections (719–732); ADR-0012 lines 1–110 + gate catalog 554–575; ADR-0013 lines 1–170 and 760–1089 + guard index; ADR-0001, ADR-0002, ADR-0009, ADR-0010 by targeted excerpt/grep only. LICENSE-RANEX.md, NOTICE.md, legal/licensing-manifest.json (parsed), decisions/local-values.env(.example), .gitignore, scripts/architecture/{pyproject.toml,README.md,test_contract_concurrency.py head}.
- Targeted grep only: HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md (4,198 lines), SDLC_CONTROL_CATALOG.md, AI_ARTIFACT_CONTRACTS.md, CORE_SDLC_OPERATING_MODEL.md, SOURCE_OF_TRUTH.md, RFC-0001/0002, docs/research/README.md. The research corpus bodies (hermes-core-architecture-research etc.) were not read beyond lines ADR-0013 pins; ADR-0013's line-bound promotion contract makes the ADR the authoritative projection.
- Generated projections spot-checked: accepted-adrs.json (full parse), contracts directory listing, hermes-research-promotions.json references. Generator/validator **not executed** (they hold a write lock and publish trees — scripts/architecture/README.md:24–31 — which conflicts with the read-only constraint).
- Not covered: `docs/architecture/reviews/`, `assessments/`, `templates/` contents; git-ignored `docs/research/books/`, `kimi-research/`; the ignored worktrees beyond the file names and two pyproject files cited. No file was modified, created, or deleted.
