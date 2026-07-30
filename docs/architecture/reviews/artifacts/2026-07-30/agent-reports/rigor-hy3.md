[0m
> build · tencent/hy3
[0m
[0m$ [0mls schemas/review/ && pwd
analysis-attempt-v1.schema.json
independence-evaluation-v1.schema.json
review-observation-v1.schema.json
review-record-projection-v1.schema.json
review-request-v1.schema.json
review-verdict-v1.schema.json
/home/soultransit/devtony/ranex
[0m
[0m✱ [0mGlob "scripts/architecture/generate_contracts.py"[90m 1 match[0m
[0m→ [0mRead schemas/review/review-observation-v1.schema.json
[0m→ [0mRead schemas/review/review-verdict-v1.schema.json
[0m→ [0mRead schemas/review/review-request-v1.schema.json
[0m→ [0mRead schemas/review/independence-evaluation-v1.schema.json
[0m→ [0mRead schemas/review/review-record-projection-v1.schema.json
[0m→ [0mRead schemas/review/analysis-attempt-v1.schema.json
[0m→ [0mRead scripts/architecture/generate_contracts.py
[0m
[0m$ [0mrg -n "def .*schema|infer|template" scripts/architecture/generate_contracts.py | head -60
5:documents and authoring templates, then writes only generated contract,
36:TEMPLATES = ROOT / "docs" / "architecture" / "templates"
2079:def event_nonempty_string_schema(*, max_length: int = 1024) -> dict[str, Any]:
2088:def event_id_schema(id_type: str) -> dict[str, Any]:
2099:def event_ref_schema(ref_type: str) -> dict[str, Any]:
2115:def event_payload_base_type_schema(
2145:def event_payload_field_schema(
2214:def state_initial_binding_schema(
2267:def state_edge_binding_ref_schema(
2318:def event_payload_schema(
2386:def domain_event_envelope_schema(
2533:def event_contract_schemas(
3449:    checker_template = load_yaml_text_strict(
3453:        list(checker_template)
3455:        or list(checker_template["subject"])
3459:            "CHECKER_RESULT template does not project the exact "
3920:        "authoring_templates",
4408:    templates = classification_authority["authoring_templates"]
4410:        templates
4413:                "docs/architecture/templates/"
4417:                "docs/architecture/templates/"
4421:        or sha256_file(ROOT / templates["behavior"])
4423:        or sha256_file(ROOT / templates["classification"])
4426:        raise ValueError("ADR-0010 authority template drift")
6235:            "Portal, or Nous inference host."
7781:def transition_event_schema(
7787:    template = load_yaml_text_strict(
7791:    if list(template) != field_names:
7793:            "TRANSITION_EVENT template does not project the exact "
7975:        "x-ranex-template": (
7976:            "docs/architecture/templates/TRANSITION_EVENT.yaml"
7985:def artifact_legal_hold_fact_schema() -> dict[str, Any]:
8988:def fixture_schema_sample(schema: dict[str, Any]) -> Any:
9036:def closed_schema_fixture_value(
10381:def scalar_schema(key: str, value: Any, artifact_type: str) -> dict[str, Any]:
10408:def infer_schema(value: Any, key: str, artifact_type: str) -> dict[str, Any]:
10412:            "properties": {name: infer_schema(child, name, artifact_type) for name, child in value.items()},
10417:        return {"type": "array", "items": infer_schema(value[0], key, artifact_type) if value else {}}
10421:def common_schemas() -> dict[str, dict[str, Any]]:
10458:def hermes_research_provision_schema() -> dict[str, Any]:
10644:def tdd_primitive_schema(type_name: str) -> dict[str, Any]:
10708:def tdd_inline_schema(spec: dict[str, Any]) -> dict[str, Any]:
10774:def tdd_type_schema(
10862:def tdd_health_contract_schemas() -> dict[str, dict[str, Any]]:
11005:def checker_execution_subject_schema() -> dict[str, Any]:
11008:    template = load_yaml_text_strict(
11012:    if list(template) != fields:
11014:            "Checker execution subject template field drift"
12898:def subject_schema(name: str, required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
12910:def build_subject_schemas() -> dict[str, dict[str, Any]]:
12949:        **{key: digest for key in ["architecture_document_digest", "architecture_subject_manifest_digest", "contract_and_template_manifest_digest", "accepted_adr_registry_digest", "review_prompt_digest"]},
13011:def test_practice_profile_schema() -> dict[str, Any]:
13705:def architecture_rule_assessment_schema() -> dict[str, Any]:
13802:def architecture_element_assessment_schema() -> dict[str, Any]:
14164:def architecture_practice_application_profile_schema() -> dict[str, Any]:
14552:def path_contract_schema() -> dict[str, Any]:
14654:def context_dependency_edge_schema() -> dict[str, Any]:
14711:def context_boundary_fit_schema() -> dict[str, Any]:
14760:def context_coupling_policy_schema() -> dict[str, Any]:
14868:def feedback_fitness_policy_schema() -> dict[str, Any]:
[0m
[0m→ [0mRead scripts/architecture/generate_contracts.py[90m [offset=10370, limit=100][0m
[0m✱ [0mGrep "ARTIFACT_SCHEMAS"[90m in scripts/architecture/generate_contracts.py · 11 matches[0m
[0m✱ [0mGrep "x-ranex-template|x-ranex-canonical-producer"[90m in scripts/architecture/generate_contracts.py · 6 matches[0m
[0m→ [0mRead scripts/architecture/generate_contracts.py[90m [limit=130, offset=19490][0m
[0m
[0m$ [0mls docs/architecture/templates/ | grep -iE "review|analysis|independ"
ANALYSIS_ATTEMPT.yaml
ARCHITECTURE_REVIEW_PACKET.yaml
INDEPENDENCE_EVALUATION.yaml
OUTCOME_REVIEW.yaml
REVIEW_OBSERVATION.yaml
REVIEW_RECORD.yaml
REVIEW_REQUEST.yaml
REVIEW_VERDICT.yaml
[0m
[0m→ [0mRead docs/architecture/templates/REVIEW_OBSERVATION.yaml
[0m→ [0mRead docs/architecture/templates/REVIEW_VERDICT.yaml
[0m→ [0mRead docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml
[0m→ [0mRead docs/architecture/templates/REVIEW_REQUEST.yaml
[0m→ [0mRead docs/architecture/templates/REVIEW_RECORD.yaml
[0m
[0m$ [0mrg -n "review_observation|review_verdict|independence|blind_context|epistemic" scripts/architecture/validate_contracts.py | head -50
1613:            "Reviewer independence and calibrated model-judge thresholds."
4204:            "review_verdict",
18928:        == "review_verdict"
26882:                "review_verdict",
27199:                "review_verdict",
[0m
[0m$ [0mrg -n -B4 -A12 "review_verdict" scripts/architecture/validate_contracts.py
4200-            "checker_result",
4201-            "evidence_snapshot",
4202-            "gate_evaluation",
4203-            "human_decision",
4204:            "review_verdict",
4205-        },
4206-        "TDD_ARTIFACT_RESOLVER_SET",
4207-        "",
4208-    )
4209-    record_types = set(adr8_test_health_contracts())
4210-    require(
4211-        len(catalog["reference_subject_roles"]) == 7,
4212-        "TDD_REFERENCE_SUBJECT_ROLE_DENOMINATOR",
4213-        str(len(catalog["reference_subject_roles"])),
4214-    )
4215-    for role in catalog["reference_subject_roles"]:
4216-        require(
--
18924-    require(
18925-        exception["independent_migration_review_ref"][
18926-            "artifact_type"
18927-        ]
18928:        == "review_verdict"
18929-        and exception["change_owner_acceptance_ref"][
18930-            "artifact_type"
18931-        ]
18932-        == "human_decision",
18933-        "LEGACY_TEST_CHANGE_EXCEPTION_INDEPENDENCE",
18934-        path,
18935-    )
18936-    exception_expiry = datetime.fromisoformat(
18937-        exception.get("expires_at", "").replace("Z", "+00:00")
18938-    )
18939-    require(
18940-        exception_expiry > now and exception_expiry <= policy_expiry,
--
26878-            case["fixture_id"] + "-change-owner",
26879-        ),
26880-        "independent_migration_review_ref": (
26881-            fixture_typed_artifact_ref(
26882:                "review_verdict",
26883-                case["fixture_id"] + "-change-review",
26884-            )
26885-        ),
26886-        "exact_subject_ref": (
26887-            "urn:ranex:legacy-test-change:" + record_id
26888-        ),
26889-        "exact_subject_digest": "",
26890-        "accepted_at": "2026-07-28T00:00:00Z",
26891-        "recorded_at": "2026-07-28T00:00:02Z",
26892-        "result": "PASS",
26893-        "status": "ACTIVE",
26894-    }
--
27195-            )
27196-        ),
27197-        "independent_migration_review_ref": (
27198-            fixture_typed_artifact_ref(
27199:                "review_verdict",
27200-                case["fixture_id"] + "-migration-review",
27201-            )
27202-        ),
27203-        "exact_subject_ref": (
27204-            "urn:ranex:legacy-test-migration-member:" + proof_id
27205-        ),
27206-        "exact_subject_digest": "",
27207-        "accepted_at": "2026-07-28T00:00:00Z",
27208-        "recorded_at": "2026-07-28T00:00:02Z",
27209-        "result": "PASS",
27210-        "status": "ACCEPTED",
27211-    }
[0m
[0m$ [0mrg -n "x-ranex-runtime-pattern|x-ranex-runtime-format" scripts/architecture/validate_contracts.py scripts/architecture/generate_contracts.py | head -30
scripts/architecture/generate_contracts.py:10402:        result["x-ranex-runtime-pattern"] = "^sha256:[0-9a-f]{64}$"
scripts/architecture/generate_contracts.py:10404:        result["x-ranex-runtime-format"] = "date-time"
[0m
[0m$ [0mrg -rln "x-ranex-runtime-pattern" --glob '!schemas/**' | head -20; echo ---; rg -c "x-ranex-runtime-pattern" -g '*.py' scripts/ 2>/dev/null
scripts/architecture/generate_contracts.py:        result["ln"] = "^sha256:[0-9a-f]{64}$"
---
scripts/architecture/generate_contracts.py:1
[0m
[0m$ [0mrg -ln "runtime-pattern|runtime_pattern" --glob '!schemas/**' --glob '!*.json'; echo ---; rg -ln "review-observation-v1|review_observation" src/ 2>/dev/null | head; ls src 2>/dev/null | head
scripts/architecture/generate_contracts.py
---
[0m
[0m$ [0mls; echo ---; rg -ln "review-observation-v1" -g '!schemas/**' | head
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
legal/licensing-manifest.json
scripts/architecture/generate_contracts.py
docs/HANDOFF.md
docs/architecture/AI_ARTIFACT_CONTRACTS.md
docs/research/reviewer-model-capability-probe-2026-07-30.md
docs/architecture/reviews/artifacts/enterprise-build-readiness/worktree-subject-bindings.json
architecture/contracts/generated-output-authority.json
architecture/contracts/schema-registry.json
architecture/contracts/artifact-types.json
[0m
[0m$ [0mrg -n "epistemic" docs/ architecture/ schemas/ -g '!*.lock' | head -40
schemas/research/research-packet-v1.schema.json:19:          "epistemic_status": {
schemas/research/research-packet-v1.schema.json:37:          "epistemic_status",
schemas/review/review-observation-v1.schema.json:32:          "epistemic_status": {
schemas/review/review-observation-v1.schema.json:75:          "epistemic_status",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:99:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:112:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:125:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:138:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:152:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:165:      "epistemic_status": "INFERENCE",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:178:      "epistemic_status": "INFERENCE",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:192:      "epistemic_status": "PROPOSAL",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:205:      "epistemic_status": "OWNER_REQUIREMENT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:216:      "epistemic_status": "FACT",
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:231:      "epistemic_status": "REPORTED_ADVISORY_RESULT",
docs/architecture/templates/REVIEW_OBSERVATION.yaml:19:    epistemic_status: INFERENCE
docs/architecture/templates/RESEARCH_PACKET.yaml:37:    epistemic_status: "UNKNOWN"
docs/HANDOFF.md:67:cite nothing and still validate. Also `epistemic_status` is an unconstrained string where an enum
docs/architecture/AI_ARTIFACT_CONTRACTS.md:59:required unknown facts use the typed epistemic state.
docs/architecture/AI_ARTIFACT_CONTRACTS.md:424:Every finding has category, severity, confidence/epistemic status, exact
docs/research/cookbook-alignment-research-2026-07-27.md:151:| `RANEX_IMPLEMENTATION_GUIDE.md:3882-4812` | Context packets, epistemic state, gates, artifacts, and ledger. | Closest part to a deterministic kernel; the atomic storage boundary remains incomplete. |
docs/research/kimi-research/agent_fleet_control_sec08.md:23:MAST's trace corpus predates the 2026 swarm harnesses, and the highest-velocity fleet on record fails in ways the taxonomy does not name. Cursor's engineering report on rebuilding SQLite in Rust with four agent teams (from the 835-page specification, without source, tests, or internet; all configurations reached 100% on sqllogictest at costs from $1,339 (Opus 4.8 + Composer 2.5 mix) to $20,057 (Fable 5 alone, informal calibration) across model mixes — a ~15× spread, with the GPT 5.5 single-model configuration at the $10,565 point) catalogs five velocity failure modes, each paired with an engineered fix — vendor-reported, MEDIUM confidence, no per-fix ablations published [^92^][^116^]. **Split-brain design** — two planners implementing the same concept differently — was fixed by making planners decide design questions themselves, with no two subtrees deciding the same question. **Planner contention** over shared files received a design document with compile-checked references. **Merge conflicts** at commit velocity received a neutral reconciler agent with arbitration rules. **Megafiles** received a flagging mechanism in which an outside agent decomposes the bloated file. **Ossification** — agents learning not to touch core code — received "licensed intentional breakage": an agent that judges a core change worthwhile makes a focused patch, and the compiler propagates it through every dependent work item [^92^][^116^]. Two supporting mechanisms generalize: decorrelated review lenses (the field-report counterpart of Chapter 7's cross-family judging) and a line-budgeted "Field Guide" injected into every agent at start as institutional memory against FM-1.4 and FM-2.4 [^92^]. The caveat is epistemic as much as technical: these are unablated field reports, and licensed intentional breakage — an agent authorized to destabilize core code — belongs behind a rollback mechanism.
docs/research/kimi-research/agent_fleet_control.docx_input.converted.md:915:MAST's trace corpus predates the 2026 swarm harnesses, and the highest-velocity fleet on record fails in ways the taxonomy does not name. Cursor's engineering report on rebuilding SQLite in Rust with four agent teams (from the 835-page specification, without source, tests, or internet; all configurations reached 100% on sqllogictest at costs from $1,339 (Opus 4.8 + Composer 2.5 mix) to $20,057 (Fable 5 alone, informal calibration) across model mixes — a ~15× spread, with the GPT 5.5 single-model configuration at the $10,565 point) catalogs five velocity failure modes, each paired with an engineered fix — vendor-reported, MEDIUM confidence, no per-fix ablations published ^31^ ^144^. **Split-brain design** — two planners implementing the same concept differently — was fixed by making planners decide design questions themselves, with no two subtrees deciding the same question. **Planner contention** over shared files received a design document with compile-checked references. **Merge conflicts** at commit velocity received a neutral reconciler agent with arbitration rules. **Megafiles** received a flagging mechanism in which an outside agent decomposes the bloated file. **Ossification** — agents learning not to touch core code — received "licensed intentional breakage": an agent that judges a core change worthwhile makes a focused patch, and the compiler propagates it through every dependent work item ^31^ ^144^. Two supporting mechanisms generalize: decorrelated review lenses (the field-report counterpart of Chapter 7's cross-family judging) and a line-budgeted "Field Guide" injected into every agent at start as institutional memory against FM-1.4 and FM-2.4 ^31^. The caveat is epistemic as much as technical: these are unablated field reports, and licensed intentional breakage — an agent authorized to destabilize core code — belongs behind a rollback mechanism.
docs/research/kimi-research/agent_fleet_control.docx_input.converted.md:1370:Every experiment cell reports the same block, modeled on the minimum protocol of the noise-floor study and the grader doctrine for agentic evals ^8^ ^135^: $n$ tasks, $k$ trials, seeds, model and version string, temperature, infrastructure configuration as resource floor/ceiling, token budget requested *and consumed* (the two diverge — under equal nominal budgets, different architectures surface different amounts of visible computation ^4^), infrastructure-error rate, pass@1 with Wilson interval, pass@k and pass^k bracketing the optimistic bound and per-task consistency, pass^k_active conditioned on trials where coordination was actually exercised — with pass^k and pass^k_active consistency claims estimated from E1's dedicated high-$k$ subsample (30 tasks × $k=32$), not from the $k=5$ experiment cells, whose per-task standard error cannot support them — tokens per resolved task, paired win/loss/tie for every contrast, and the E1 noise-floor line. The primary contrast — protocols, seed, temperature, correction family (Bonferroni $m$ = number of contrasts) — is frozen before the run, and effects are reported with max–min spread across runs rather than single numbers, since even temperature-zero decoding is not deterministic (80 distinct completions from 1,000 identical greedy requests) ^8^ ^43^ ^44^. Accuracy figures are reported alongside intraclass correlation and within-query variance, because a component swap that raises mean accuracy while degrading ICC has traded capability for stability ^47^. Two habits guard the epistemics: aggregate across cells before concluding (the honest template for underpowered cells ^24^), and treat any leaderboard-style difference below 3 pp as noise until the evaluation configuration is documented and matched ^40^.
docs/research/kimi-research/agent_fleet_control.docx_input.md:915:MAST's trace corpus predates the 2026 swarm harnesses, and the highest-velocity fleet on record fails in ways the taxonomy does not name. Cursor's engineering report on rebuilding SQLite in Rust with four agent teams (from the 835-page specification, without source, tests, or internet; all configurations reached 100% on sqllogictest at costs from $1,339 (Opus 4.8 + Composer 2.5 mix) to $20,057 (Fable 5 alone, informal calibration) across model mixes — a ~15× spread, with the GPT 5.5 single-model configuration at the $10,565 point) catalogs five velocity failure modes, each paired with an engineered fix — vendor-reported, MEDIUM confidence, no per-fix ablations published [^31^][^144^]. **Split-brain design** — two planners implementing the same concept differently — was fixed by making planners decide design questions themselves, with no two subtrees deciding the same question. **Planner contention** over shared files received a design document with compile-checked references. **Merge conflicts** at commit velocity received a neutral reconciler agent with arbitration rules. **Megafiles** received a flagging mechanism in which an outside agent decomposes the bloated file. **Ossification** — agents learning not to touch core code — received "licensed intentional breakage": an agent that judges a core change worthwhile makes a focused patch, and the compiler propagates it through every dependent work item [^31^][^144^]. Two supporting mechanisms generalize: decorrelated review lenses (the field-report counterpart of Chapter 7's cross-family judging) and a line-budgeted "Field Guide" injected into every agent at start as institutional memory against FM-1.4 and FM-2.4 [^31^]. The caveat is epistemic as much as technical: these are unablated field reports, and licensed intentional breakage — an agent authorized to destabilize core code — belongs behind a rollback mechanism.
docs/research/kimi-research/agent_fleet_control.docx_input.md:1370:Every experiment cell reports the same block, modeled on the minimum protocol of the noise-floor study and the grader doctrine for agentic evals [^8^][^135^]: $n$ tasks, $k$ trials, seeds, model and version string, temperature, infrastructure configuration as resource floor/ceiling, token budget requested *and consumed* (the two diverge — under equal nominal budgets, different architectures surface different amounts of visible computation [^4^]), infrastructure-error rate, pass@1 with Wilson interval, pass@k and pass^k bracketing the optimistic bound and per-task consistency, pass^k_active conditioned on trials where coordination was actually exercised — with pass^k and pass^k_active consistency claims estimated from E1's dedicated high-$k$ subsample (30 tasks × $k=32$), not from the $k=5$ experiment cells, whose per-task standard error cannot support them — tokens per resolved task, paired win/loss/tie for every contrast, and the E1 noise-floor line. The primary contrast — protocols, seed, temperature, correction family (Bonferroni $m$ = number of contrasts) — is frozen before the run, and effects are reported with max–min spread across runs rather than single numbers, since even temperature-zero decoding is not deterministic (80 distinct completions from 1,000 identical greedy requests) [^8^][^43^][^44^]. Accuracy figures are reported alongside intraclass correlation and within-query variance, because a component swap that raises mean accuracy while degrading ICC has traded capability for stability [^47^]. Two habits guard the epistemics: aggregate across cells before concluding (the honest template for underpowered cells [^24^]), and treat any leaderboard-style difference below 3 pp as noise until the evaluation configuration is documented and matched [^40^].
docs/research/kimi-research/agent_fleet_control_sec13.md:83:Every experiment cell reports the same block, modeled on the minimum protocol of the noise-floor study and the grader doctrine for agentic evals [^121^][^83^]: $n$ tasks, $k$ trials, seeds, model and version string, temperature, infrastructure configuration as resource floor/ceiling, token budget requested *and consumed* (the two diverge — under equal nominal budgets, different architectures surface different amounts of visible computation [^245^]), infrastructure-error rate, pass@1 with Wilson interval, pass@k and pass^k bracketing the optimistic bound and per-task consistency, pass^k_active conditioned on trials where coordination was actually exercised — with pass^k and pass^k_active consistency claims estimated from E1's dedicated high-$k$ subsample (30 tasks × $k=32$), not from the $k=5$ experiment cells, whose per-task standard error cannot support them — tokens per resolved task, paired win/loss/tie for every contrast, and the E1 noise-floor line. The primary contrast — protocols, seed, temperature, correction family (Bonferroni $m$ = number of contrasts) — is frozen before the run, and effects are reported with max–min spread across runs rather than single numbers, since even temperature-zero decoding is not deterministic (80 distinct completions from 1,000 identical greedy requests) [^121^][^243^][^242^]. Accuracy figures are reported alongside intraclass correlation and within-query variance, because a component swap that raises mean accuracy while degrading ICC has traded capability for stability [^241^]. Two habits guard the epistemics: aggregate across cells before concluding (the honest template for underpowered cells [^246^]), and treat any leaderboard-style difference below 3 pp as noise until the evaluation configuration is documented and matched [^244^].
docs/research/kimi-research/research/agentfleet_insight.md:31:- **Rationale:** Independent measurement-focused dimensions all show the same epistemic fragility; the practitioner corollary (build E0–E3 before any topology bet) is non-obvious and contradicts the build-first instinct.
docs/research/kimi-research/agent_fleet_control.agent.final.md:976:MAST's trace corpus predates the 2026 swarm harnesses, and the highest-velocity fleet on record fails in ways the taxonomy does not name. Cursor's engineering report on rebuilding SQLite in Rust with four agent teams (from the 835-page specification, without source, tests, or internet; all configurations reached 100% on sqllogictest at costs from $1,339 (Opus 4.8 + Composer 2.5 mix) to $20,057 (Fable 5 alone, informal calibration) across model mixes — a ~15× spread, with the GPT 5.5 single-model configuration at the $10,565 point) catalogs five velocity failure modes, each paired with an engineered fix — vendor-reported, MEDIUM confidence, no per-fix ablations published [^92^][^116^]. **Split-brain design** — two planners implementing the same concept differently — was fixed by making planners decide design questions themselves, with no two subtrees deciding the same question. **Planner contention** over shared files received a design document with compile-checked references. **Merge conflicts** at commit velocity received a neutral reconciler agent with arbitration rules. **Megafiles** received a flagging mechanism in which an outside agent decomposes the bloated file. **Ossification** — agents learning not to touch core code — received "licensed intentional breakage": an agent that judges a core change worthwhile makes a focused patch, and the compiler propagates it through every dependent work item [^92^][^116^]. Two supporting mechanisms generalize: decorrelated review lenses (the field-report counterpart of Chapter 7's cross-family judging) and a line-budgeted "Field Guide" injected into every agent at start as institutional memory against FM-1.4 and FM-2.4 [^92^]. The caveat is epistemic as much as technical: these are unablated field reports, and licensed intentional breakage — an agent authorized to destabilize core code — belongs behind a rollback mechanism.
docs/research/kimi-research/agent_fleet_control.agent.final.md:1488:Every experiment cell reports the same block, modeled on the minimum protocol of the noise-floor study and the grader doctrine for agentic evals [^121^][^83^]: $n$ tasks, $k$ trials, seeds, model and version string, temperature, infrastructure configuration as resource floor/ceiling, token budget requested *and consumed* (the two diverge — under equal nominal budgets, different architectures surface different amounts of visible computation [^245^]), infrastructure-error rate, pass@1 with Wilson interval, pass@k and pass^k bracketing the optimistic bound and per-task consistency, pass^k_active conditioned on trials where coordination was actually exercised — with pass^k and pass^k_active consistency claims estimated from E1's dedicated high-$k$ subsample (30 tasks × $k=32$), not from the $k=5$ experiment cells, whose per-task standard error cannot support them — tokens per resolved task, paired win/loss/tie for every contrast, and the E1 noise-floor line. The primary contrast — protocols, seed, temperature, correction family (Bonferroni $m$ = number of contrasts) — is frozen before the run, and effects are reported with max–min spread across runs rather than single numbers, since even temperature-zero decoding is not deterministic (80 distinct completions from 1,000 identical greedy requests) [^121^][^243^][^242^]. Accuracy figures are reported alongside intraclass correlation and within-query variance, because a component swap that raises mean accuracy while degrading ICC has traded capability for stability [^241^]. Two habits guard the epistemics: aggregate across cells before concluding (the honest template for underpowered cells [^246^]), and treat any leaderboard-style difference below 3 pp as noise until the evaluation configuration is documented and matched [^244^].
[0m
[0m$ [0msed -n 40,110p docs/HANDOFF.md
| Accepted ADRs | 13 |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |
| Runtime | `NOT_ASSESSED` — nothing runs |
| Readiness | Neither tier declared |
| Kernel | R&D tracer only, branch `feature/kernel-tracer`, **unaudited** |

## Immediate next steps, in order

**1. Fix `HERMES-PROMOTION-059`.** One word. The provision says *"every Execution state
transition"*; research line 1902 says only *"Implement an Execution aggregate and pure reducer."*
The qualifier `every` is unsupported. Found by MiMo after three repair rounds missed it. Bump
ADR-0013 to 1.4.0.

**2. Re-dispatch three audits that were killed.** They produced zero bytes because three
concurrent HY3 runs on one provider deadlocked — see *Operational notes*. Run them **one at a
time**:
   - Verification of ADR-0013 v1.3.0 — brief at `scratchpad/verify-13.md`
   - Adversarial audit of the kernel tracer — brief at `scratchpad/audit-kernel.md`
   - Review-schema rigour questions — brief at `scratchpad/finding-rigor.md`

   The kernel audit is the important one. It asks whether the reducer is genuinely pure, whether
   the policy enforcement point actually fails closed, and whether the declared inference
   *"the relational snapshot, not journal replay, is canonical state authority"* holds. Everything
   in the engine sits on that.

**3. `evidence_refs` has no `minItems`.** `schemas/review/review-observation-v1.schema.json`
requires `evidence_refs` on every finding, but an empty array satisfies it — so a finding can
cite nothing and still validate. Also `epistemic_status` is an unconstrained string where an enum
is probably intended. Both are generated; fix at source in `generate_contracts.py`, never in the
output. **Do not invent the enum vocabulary** — that is an owner decision.

**4. Owner decisions outstanding.** Four intake parameters (question cap, session cap, materiality
thresholds, consequence-confirmation triggers) and 20 registered `OWNER_DECISION_REQUIRED` entries
in ADR-0013. All correctly block rather than default. Nothing consults them yet because no runtime
exists — that is a known limitation, not a defect.

## Open threads

- **Monetization.** The owner raised it and it was not finished. Relevant facts: `LICENSE-RANEX.md`
  is a personal-use source-available licence, all rights reserved, no commercial use without
  written permission — commercial optionality is preserved. ADR-0011 forecloses the Hermes model
  (inference margin) by committing to provider-neutral, fallback-free routing. Do not restate what
  they already decided; help them think about what the architecture still permits.
- **Documentation indexes** were added at `docs/`, `docs/research/`, `docs/architecture/reviews/`.
  Keep them current — they exist because finished work was invisible, which caused the six false
  "missing" findings.
- **Copyrighted PDFs remain reachable** in the git object database via `refs/codex/*`. A normal
  `git push` will not carry them; `--all` or `--mirror` would, to a public repo. Unresolved by
  owner choice.
- **`~/.codex/logs_2.sqlite` is ~3.6 GB, 88% dead space.** A compaction job is armed and fires when
  no Codex process is running. It has never fired because Codex has run continuously.

## Operational notes

**Model routing, from measured behaviour** (see
[`research/reviewer-model-capability-probe-2026-07-30.md`](research/reviewer-model-capability-probe-2026-07-30.md)):

- **HY3** (`openrouter/tencent/hy3`, high) — deep adversarial reading. Found the two hardest
  defects of the session. Slow, verbose, worth it where a subtle miss is expensive.
- **MiMo** (`openrouter/xiaomi/mimo-v2.5-pro`) — systematic full-corpus passes. Fast, concise,
  verifies claims structurally. Found the drift three rounds had missed.
- **DeepSeek** (`opencode-go/deepseek-v4-pro`) — third opinion for tiebreaks. Weakest on this
  corpus: mangled a path, hung five hours, sampled where a systematic pass was required, and
  inverted a check mechanism.

**Concurrency has a cliff, not a slope.** Three concurrent HY3 runs produced zero output for
24–52 minutes while a run on another provider finished in seven. Dispatch one per provider at a
time.

**A silent hang is indistinguishable from deep reasoning.** One run produced zero bytes for five
hours before anyone noticed. Check output size, not just liveness.
[0m
[0m$ [0mrg -n "PLAUSIBLE|CONFIRMED|REFUTED|confirmed/|refuted" docs/research/reviewer-model-capability-probe-2026-07-30.md docs/architecture/AI_ARTIFACT_CONTRACTS.md | head -30
(no output)
[0m
[0m$ [0mrg -n "Applicability to Ranex" -A60 docs/research/reviewer-model-capability-probe-2026-07-30.md | head -90
107:## Applicability to Ranex
108-
109-Three properties of this probe are reusable inside the product rather than merely about it:
110-
111-1. **A finding must be checkable or it is an opinion.** Every claim that survived was verifiable
112-   at `path:line`. Every claim that dissolved was framing. This is already partially enforced —
113-   `review-observation-v1.schema.json` requires `evidence_refs` per finding — but `minItems` is
114-   unset, so an empty array satisfies the requirement.
115-2. **Reviewer disagreement is more informative than reviewer consensus, provided it is
116-   resolvable.** Two reviewers contradicted each other on the pin mechanism; three lines of code
117-   settled it. A gate that collects agreeing signatures proves less than one that surfaces a
118-   disagreement with a test attached.
119-3. **Prompt contamination defeats independent review.** An assumption placed in a brief was
120-   returned as a finding with a citation. `review-request-v1.schema.json` already carries
121-   `blind_context_manifest_digest` and `independence-evaluation-v1.schema.json` carries
122-   `blind_context_satisfied` — the mechanism exists; this probe is evidence for why it matters.
123-
124-## Addendum — session-warmth latency probe
125-
126-A separate probe on the same day asked whether Hermes' Nous keepalive removes a capability Ranex
127-must rebuild. Four conditions, 20 runs each, interleaved, on `openai-codex`:
128-
129-| Condition | n | median | p95 | runs > 6s |
130-|---|---:|---:|---:|---:|
131-| `safe-mode` (all customisation off) | 20 | 4.01 s | 5.22 s | **0** |
132-| `--ignore-rules` | 20 | 4.13 s | 5.60 s | 1 |
133-| warm | 20 | 4.21 s | 7.16 s | 5 |
134-| cold (caches cleared) | 20 | 4.62 s | 9.70 s | 3 |
135-
136-**Robust finding:** customisation, not cache state, drives the latency tail. Medians differ by
137-0.6 s across all four conditions, but `safe-mode` never exceeded 6 s in 20 runs while warm
138-sessions with full skills and persona loaded did so five times, peaking at 10.7 s. The ~11.6 k
139-tokens of skills injection is a latency-variance cost, not only a token cost.
140-
141-**Implication for de-commercialization:** session warmth was not the mechanism. Cold and warm
142-medians differ by 0.4 s. Deleting the Nous keepalive does not remove a capability worth
143-rebuilding.
144-
145-**Discarded finding:** the harness printed a verdict on a `cold − warm` gap of `+2.54 s` at p95.
146-That is not trustworthy. At n=20, p95 is effectively the second-slowest observation, and warm's
147-own p95 (7.16 s) sits far above its median (4.21 s) — the tail is fat in both conditions. The
148-decision rule was applied to a statistic that is unstable at this sample size. Recorded as a
149-design error in the harness, not as a result.
150-
151-The p95 question remains `EFFECTIVENESS_UNKNOWN`. Settling it needs n≈100 and time-to-first-token
152-instrumentation rather than wall-clock timing.
153-
154-## Limitations
155-
156-- One to three samples per model. No repetition, no holdout, no hidden evaluation.
157-- Conditions were not held constant: one model ran without provider contention while others
158-  queued.
159-- All briefs were authored by the orchestrator, whose framing demonstrably contaminated at least
160-  one result.
161-- The orchestrator also verified the results. There was no independent check of the verification.
162-- Ground truth came from prior audit rounds, not from an authored answer key.
163-- No cost or token accounting was captured.
[0m
[0m$ [0mrg -rn "PLAUSIBLE" docs/ architecture/ schemas/ | head -20; echo ===; rg -rn "EFFECTIVENESS_UNKNOWN" docs/ architecture/ schemas/ scripts/ | head -10
===
scripts/architecture/generate_contracts.py:    "P2_IMPROVE_DELIBERATELY": ["LEVEL_2", "n", "EFFECTIVENESS_REGRESSING", "EFFECTIVENESS_MIXED", "MATERIAL_FLOW_QUALITY_OUTCOME_HARM", "P3_CRITERIA_UNPROVEN"],
architecture/contracts/priority-rules.json:        "n",
docs/architecture/SDLC_CONTROL_CATALOG.md:| `P2` | `LEVEL_2`, `n`, `EFFECTIVENESS_REGRESSING`, `EFFECTIVENESS_MIXED`, `MATERIAL_FLOW_QUALITY_OUTCOME_HARM`, `P3_CRITERIA_UNPROVEN` |
docs/architecture/assessments/controls/SDLC-AIW-004.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-DIS-001.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-AIW-001.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-AIW-002.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-TRI-001.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-CAN-001.json:        "trigger_code": "n"
docs/architecture/assessments/controls/SDLC-FORK-004.json:        "trigger_code": "n"
[0m
[0m$ [0mrg -n "PLAUSIBLE" docs/ architecture/ schemas/ scripts/ | head -20; echo ===; rg -n "EFFECTIVENESS_UNKNOWN" docs/ architecture/ schemas/ scripts/ | head -15; echo ===; rg -n "UNKNOWN|CONFIRMED|REFUTED" docs/research/reviewer-model-capability-probe-2026-07-30.md | head -20
===
scripts/architecture/generate_contracts.py:508:    "P2_IMPROVE_DELIBERATELY": ["LEVEL_2", "EFFECTIVENESS_UNKNOWN", "EFFECTIVENESS_REGRESSING", "EFFECTIVENESS_MIXED", "MATERIAL_FLOW_QUALITY_OUTCOME_HARM", "P3_CRITERIA_UNPROVEN"],
architecture/contracts/priority-rules.json:34:        "EFFECTIVENESS_UNKNOWN",
docs/architecture/assessments/controls/SDLC-PA-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-CM-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-DES-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-AIW-004.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/SDLC_CONTROL_CATALOG.md:1755:| `P2` | `LEVEL_2`, `EFFECTIVENESS_UNKNOWN`, `EFFECTIVENESS_REGRESSING`, `EFFECTIVENESS_MIXED`, `MATERIAL_FLOW_QUALITY_OUTCOME_HARM`, `P3_CRITERIA_UNPROVEN` |
docs/architecture/assessments/controls/SDLC-CAN-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-FORK-007.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-PLN-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-AIW-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-OUT-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-DIS-001.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-FORK-004.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
docs/architecture/assessments/controls/SDLC-FORK-002.json:709:        "trigger_code": "EFFECTIVENESS_UNKNOWN"
===
151:The p95 question remains `EFFECTIVENESS_UNKNOWN`. Settling it needs n≈100 and time-to-first-token
[0m
[0m$ [0mrg -n "epistemic" docs/architecture/AI_ARTIFACT_CONTRACTS.md; echo ===; sed -n '40,70p;410,440p' docs/architecture/AI_ARTIFACT_CONTRACTS.md
59:required unknown facts use the typed epistemic state.
424:Every finding has category, severity, confidence/epistemic status, exact
===

The contract registry declares one canonical wire representation:

1. accept JSON or YAML only at an ingress adapter;
2. parse with duplicate-key rejection and schema-selected scalar types;
3. normalize to the versioned JSON data model;
4. reject unknown fields unless that schema version explicitly reserves them;
5. encode using RFC 8785 JSON Canonicalization Scheme;
6. compute SHA-256 over the UTF-8 canonical bytes with the top-level `digest`
   field absent;
7. serialize `digest` as `sha256:<64 lowercase hex>`;
8. preserve the original submitted bytes as a separate artifact when required;
   and
9. never use display YAML bytes, map insertion order, local paths, timestamps,
   or a redacted projection to recompute the canonical digest.

Times are RFC 3339 UTC with explicit `Z`. Durations and budgets are integer
base units declared by schema. Floating-point values are forbidden in authority
and evidence identity. Empty string is not a substitute for absent/unknown;
required unknown facts use the typed epistemic state.

## 3. Shared identifiers and vocabulary

All generated identifiers use the prefixes registered in `identities.yaml`.
Minimum prefixes include:

| Type | Prefix |
|---|---|
| Repository | `repo_` |
| Project / work / run / activity / effect | `prj_`, `work_`, `run_`, `act_`, `eff_` |
| Workspace / packet / intake / research | `wsp_`, `pkt_`, `intake_`, `research_` |
In draft templates, `null` means **not established**. It never means unlimited.
A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
reservation cannot become `ACTIVE` while a policy-required deadline or budget
dimension is null. Zero denies consumption of that dimension. A dimension may
be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
reason, accountable owner, and evidence reference.

Every activated execution/review reservation has an absolute deadline and all
transitive dimensions required by its risk/work-class policy. Child limits are
no later/larger than every ancestor. Canonical validation rejects negative,
ambiguous, unitless, floating-point, or “unlimited” sentinel values.

## 8. Finding lifecycle

Every finding has category, severity, confidence/epistemic status, exact
location, claim, impact, evidence, required action, owner, and state:

```text
OPEN
  -> ACCEPTED
  -> FIXED_PENDING_VERIFICATION
  -> VERIFIED

OPEN
  -> DISPUTED
  -> SPECIALIST_REVIEW
  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
```

Only the review/finding application service changes finding state. A maker may
submit a resolution proposal but cannot mark its finding verified.
[0m
[0m$ [0mrg -ln "epistemic_status" docs/architecture/reviews/ | head; echo ===; rg -n "\"epistemic_status\"|\"confidence\"|\"state\":" docs/architecture/reviews/artifacts/enterprise-build-readiness/*.json 2>/dev/null | head -30
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json
===
[0m
[0m$ [0mrg -n "verdict|independence|blind_context|disagree|reconcil" docs/architecture/AI_ARTIFACT_CONTRACTS.md | head -40
74:| Architecture review packet / proposal / reconciliation | `archpkt_`, `proposal_`, `archreconcile_` |
75:| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
77:| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
96:- observation, finding, review-verdict, checker, gate, decision, grant, permit,
240:artifact declared in scope. The reconciliation records both the reviewed
355:| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
356:| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
358:| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
405:`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
540:│   └── reconciliation-v1.schema.json
550:│   ├── independence-evaluation-v1.schema.json
551:│   ├── review-verdict-v1.schema.json
634:  imported from the public-safe reconciled registry, while applicability and
682:- hidden-fixture isolation and review independence through a real harness;
[0m
[0m$ [0msed -n '350,415p' docs/architecture/AI_ARTIFACT_CONTRACTS.md
| `ResourceReservation` | `resource_governance` | Bind hierarchical admitted limits and settled usage to an exact subject | Authorize an effect, exceed an ancestor, or declare work complete |
| `CapabilityAssessment` | `process_assurance` under accountable assessor/approver roles | Diagnose one exact capability/control scope with separate level, effectiveness, coverage, confidence, and improvement priority | Authorize a transition, average away a vital-control failure, or rank people |
| `CapabilityDomainProjection` | `process_assurance` deterministic projection service under accountable assessor/approver roles | Bind the exact registered control-tuple set for one domain/scope/window and derive result, lowest supported level, and highest-precedence priority | Author a member assessment, omit/duplicate/remap a registry tuple, arithmetically aggregate levels, or authorize a transition |
| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
| `ReviewObservation` | Reviewer/model normalization | Findings, uncertainty, limitations | Gate outcome |
| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
| `ReviewRecordProjection` | Projection builder | Read model joining immutable review records for navigation | Replace or mutate its source records |
| `CheckerResult` | Qualified deterministic checker wrapper | One reproducible check outcome | Aggregate gate alone |
| `EvidenceSnapshot` | Assurance service | Freeze exact eligible evidence set | Decision by itself |
| `GateEvaluation` | Qualified gate evaluator | Produce runtime `GateOutcome` | Human decision |
| `HumanDecisionRecord` | Policy after IAM authentication | Record accountable human choice | Direct effect execution |
| `ConsumableAuthorityGrant` | Governed execution | One-shot eligible decision snapshot | Broader/different action |
| `Permit` | Governed execution after gate/decision | One-shot exact effect/transition capability | Another subject/action |
| `LandingRecord` | Workspace/Git adapter normalization | Prove candidate-to-landed relation | Release/closure |
| `PostLandingVerification` | Assurance service | Verify landed subject | Product outcome |
| `ReleaseEvidence` | Release management | Build/promotion/rollback facts | Service/product acceptance |
| `OperationEvidence` | Operations/service evidence ingestion | Health/support/recovery facts | Product outcome |
| `OutcomeReview` | Product definition under product owner | Compare outcome and decide keep/change/remove | Rewrite engineering facts |
| `TransitionEvent` | Owning aggregate UoW | Durable accepted state fact | State owned by another aggregate |

## 7. Review separation

Review is five immutable records, not one mutable model response:

```text
ReviewRequest
  -> AnalysisAttempt[1..N]
  -> ReviewObservation[0..N]
  -> IndependenceEvaluation
  -> ReviewVerdict
  -> EvidenceSnapshot
  -> GateEvaluation
```

`ReviewRequest` records maker principal/run/session/role, exact subject,
separate review packet, required reviewer role, prohibited capabilities, blind
context manifest, diversity requirements expressed as actual route facts, and
qualification policy.

Each `AnalysisAttempt` records reviewer principal/role/session, actual
provider/model/transport/executable/parser/isolation identities, route lock,
input/output artifact digests, start/end/deadline/budget, granted capabilities,
write attempts, failures, usage, and relation to previous attempts.

`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
self-assertion and a model-family label are insufficient. It compares maker and
reviewer identities/sessions, packet construction, write capability/activity,
blindness manifest, route/provider/transport facts, qualification, hidden
fixture isolation, and candidate identity.

`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
not `GateOutcome`.

### 7.1 Deadline and budget null semantics

In draft templates, `null` means **not established**. It never means unlimited.
A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
reservation cannot become `ACTIVE` while a policy-required deadline or budget
dimension is null. Zero denies consumption of that dimension. A dimension may
be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
reason, accountable owner, and evidence reference.
[0m
Now let me verify the degenerate instances actually validate, using a scratch script in `/tmp/opencode` (repo stays untouched):
[0m$ [0mmkdir -p /tmp/opencode && cat > /tmp/opencode/vacuous_test.py <<'EOF'
import json, jsonschema
root="/home/soultransit/devtony/ranex/schemas/review/"

obs=json.load(open(root+"review-observation-v1.schema.json"))
vacuous_finding={
 "finding_id":"","category":"","severity":"","confidence":"",
 "epistemic_status":"","location":"","claim":"","impact":"",
 "evidence_refs":[],"required_action":"","owner_ref":None,
 "state":"","reconciliation_ref":None}
vacuous_obs={
 "schema_version":"1","artifact_type":"review_observation",
 "observation_id":"","review_request_id":"","analysis_attempt_id":"",
 "subject_schema":None,"subject_ref":"","subject_digest":"",
 "subject_manifest_digest":None,"core_sdlc_trace_ref":"","state":"",
 "summary":"","findings":[vacuous_finding],"uncertainties":[],
 "limitations":[],"proposed_actions":[],"digest":""}
jsonschema.validate(vacuous_obs, obs)
print("VACUOUS OBSERVATION: VALIDATES")

# uncheckable evidence refs: any JSON type accepted?
f2=dict(vacuous_finding, evidence_refs=[None, 42, {}, "", "not a path", []])
o2=dict(vacuous_obs, findings=[f2])
jsonschema.validate(o2, obs)
print("GARBAGE evidence_refs [null,42,{},'','not a path',[]]: VALIDATES")

ver=json.load(open(root+"review-verdict-v1.schema.json"))
vacuous_verdict={
 "schema_version":"1","artifact_type":"review_verdict","verdict_id":"",
 "review_request_id":"","observation_ids":[],"independence_evaluation_id":"",
 "subject_schema":None,"subject_ref":"","subject_digest":"",
 "subject_manifest_digest":None,"core_sdlc_trace_ref":"",
 "verdict":"LGTM_SHIP_IT","open_finding_refs":[],"resolved_finding_refs":[],
 "reconciliation_refs":[],"evidence_refs":[],"limitations":[],
 "producer_service_id":"","produced_at":"not a date","digest":"sha256:nope"}
jsonschema.validate(vacuous_verdict, ver)
print("VERDICT verdict='LGTM_SHIP_IT', digest='sha256:nope', produced_at='not a date': VALIDATES")

ind=json.load(open(root+"independence-evaluation-v1.schema.json"))
check={"outcome":"","evidence_refs":[]}
vac_ind={
 "schema_version":"1","artifact_type":"independence_evaluation",
 "evaluation_id":"","review_request_id":"","analysis_attempt_ids":[],
 "subject_schema":None,"subject_ref":"","subject_digest":"",
 "subject_manifest_digest":None,"core_sdlc_trace_ref":"",
 "checks":{k:dict(check) for k in ["maker_reviewer_identity_separated",
   "maker_reviewer_session_separated","subject_exact",
   "reviewer_did_not_mutate_subject",
   "reviewer_had_no_write_or_authority_capability",
   "blind_context_satisfied","route_fact_diversity_satisfied",
   "hidden_verification_withheld"]},
 "eligible":True,"blocking_reasons":[],"validator_id":"",
 "validator_version":"","validator_code_digest":"","evaluated_at":"",
 "digest":""}
vac_ind["checks"]["blind_context_satisfied"]={"outcome":"SATISFIED_TRUST_ME","evidence_refs":[]}
jsonschema.validate(vac_ind, ind)
print("INDEPENDENCE eligible=true, blind outcome='SATISFIED_TRUST_ME', all evidence []: VALIDATES")

req=json.load(open(root+"review-request-v1.schema.json"))
vac_req={
 "schema_version":"1","artifact_type":"review_request","request_id":"",
 "review_spec_id":"","review_spec_version":"","packet_id":"",
 "packet_digest":"","subject_schema":None,"subject_ref":"",
 "subject_digest":"","subject_manifest_digest":None,"core_sdlc_trace_ref":"",
 "maker":{"principal_id":"","role_id":"","run_id":"","session_id":""},
 "required_reviewer_role_id":"","required_independence":[],
 "prohibited_capabilities":[],"blind_context_manifest_digest":"",
 "required_route_fact_diversity":[],"qualification_policy_id":"",
 "absolute_deadline":"","digest":""}
jsonschema.validate(vac_req, req)
print("REQUEST blind_context_manifest_digest='' , prohibited_capabilities=[]: VALIDATES")

proj=json.load(open(root+"review-record-projection-v1.schema.json"))
vac_proj={
 "schema_version":"1","artifact_type":"review_record_projection",
 "projection_id":"","subject_schema":None,"subject_ref":"",
 "subject_digest":"","subject_manifest_digest":None,
 "core_sdlc_trace_ref":"","review_request_id":"","review_request_digest":"",
 "analysis_attempt_refs":[],"review_observation_refs":[],
 "independence_evaluation_id":"","independence_evaluation_digest":"",
 "review_verdict_id":"","review_verdict_digest":"","gate_evaluation_ref":None,
 "generated_at":"","source_registry_version":"","digest":""}
jsonschema.validate(vac_proj, proj)
print("PROJECTION zero attempts, zero observations, empty digests: VALIDATES")

att=json.load(open(root+"analysis-attempt-v1.schema.json"))
vac_att={
 "schema_version":"1","artifact_type":"analysis_attempt","attempt_id":"",
 "review_request_id":"","previous_attempt_id":None,"subject_schema":None,
 "subject_ref":"","subject_digest":"","subject_manifest_digest":None,
 "core_sdlc_trace_ref":"",
 "reviewer":{"principal_id":"","role_id":"","session_id":""},
 "route":{"route_lock_id":"","actual_provider_id":"","actual_model_id":"",
   "actual_model_snapshot":None,"transport_id":"","transport_digest":"",
   "executable_digest":"","parser_version":"","isolation_profile_id":""},
 "input_artifact_refs":[],"input_manifest_digest":"",
 "granted_capabilities":[],"write_attempt_evidence_refs":[],
 "started_at":"","finished_at":"","absolute_deadline":"","status":None,
 "failure_domain":None,"retry_class":None,"usage":{"anything":"goes"},
 "raw_output_artifact_ref":"","raw_output_digest":"","digest":""}
try:
    jsonschema.validate(vac_att, att)
    print("ATTEMPT all-empty + usage extra key: VALIDATES")
except jsonschema.ValidationError as e:
    print("ATTEMPT rejected:", e.message)
    vac_att["usage"]={}
    jsonschema.validate(vac_att, att)
    print("ATTEMPT all-empty with usage={}: VALIDATES")
EOF
python3 /tmp/opencode/vacuous_test.py
Traceback (most recent call last):
  File "/tmp/opencode/vacuous_test.py", line 1, in <module>
    import json, jsonschema
ModuleNotFoundError: No module named 'jsonschema'
[0m
[0m$ [0mls scripts/architecture/ | head; python3 -c "import sys; print(sys.version)"; pip list 2>/dev/null | grep -i -E "jsonschema|yaml|rfc" ; ls .venv venv 2>/dev/null
contract_tree_lock.py
generate_contracts.py
__pycache__
pyproject.toml
README.md
test_contract_concurrency.py
uv.lock
validate_contracts.py
3.14.6 (main, Jun 23 2026, 15:18:23) [Clang 22.1.3 ]
[0m
[0m$ [0mcd /tmp/opencode && uv venv -q v 2>/dev/null; . v/bin/activate && uv pip install -q jsonschema 2>&1 | tail -1; python /tmp/opencode/vacuous_test.py
VACUOUS OBSERVATION: VALIDATES
GARBAGE evidence_refs [null,42,{},'','not a path',[]]: VALIDATES
VERDICT verdict='LGTM_SHIP_IT', digest='sha256:nope', produced_at='not a date': VALIDATES
INDEPENDENCE eligible=true, blind outcome='SATISFIED_TRUST_ME', all evidence []: VALIDATES
REQUEST blind_context_manifest_digest='' , prohibited_capabilities=[]: VALIDATES
PROJECTION zero attempts, zero observations, empty digests: VALIDATES
ATTEMPT rejected: Additional properties are not allowed ('anything' was unexpected)
ATTEMPT all-empty with usage={}: VALIDATES
[0m
[0m$ [0mrg -n "blind" schemas/ scripts/architecture/validate_contracts.py docs/architecture/AI_ARTIFACT_CONTRACTS.md | head; echo ===; rg -n "minItems" scripts/architecture/generate_contracts.py | head -20; echo ===; rg -c "minItems" schemas/review/*.json 2>/dev/null; echo ===; rg -n "blind_context" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head
docs/architecture/AI_ARTIFACT_CONTRACTS.md:389:separate review packet, required reviewer role, prohibited capabilities, blind
docs/architecture/AI_ARTIFACT_CONTRACTS.md:401:blindness manifest, route/provider/transport facts, qualification, hidden
schemas/architecture/review-packet-v1.schema.json:282:            "blind_to_primary_initially": {
schemas/architecture/review-packet-v1.schema.json:296:            "blind_to_primary_initially",
schemas/review/review-request-v1.schema.json:13:    "blind_context_manifest_digest": {
schemas/review/review-request-v1.schema.json:124:    "blind_context_manifest_digest",
schemas/review/independence-evaluation-v1.schema.json:20:        "blind_context_satisfied": {
schemas/review/independence-evaluation-v1.schema.json:163:        "blind_context_satisfied",
===
2160:            "minItems": 0 if field["allow_empty_set"] else 1,
2335:            "minItems": 1,
2343:            "minItems": 1,
7918:            "minItems": 1,
7925:            "minItems": 0,
7932:            "minItems": 0,
9009:        count = max(schema.get("minItems", 0), 1)
9065:        count = schema.get("minItems", 0)
10756:            "minItems": len(values),
10856:            result["minItems"] = minimum
10975:                        "minItems": 1,
12987:                    "minItems": 10,
13053:                "minItems": 1,
13079:                "minItems": 1,
13096:                        "minItems": 1,
13116:                "minItems": 1,
13120:                "minItems": 1,
13124:                "minItems": 1,
13136:                "minItems": 1,
13143:                "minItems": 1,
===
===
[0m
[0m$ [0mrg -l "review_observation" docs/architecture/reviews/artifacts/ | head; echo ===; rg -n "reviews/artifacts" scripts/architecture/validate_contracts.py | head -5; echo ===; rg -n "evidence-ref.schema|evidence_ref" scripts/architecture/validate_contracts.py | head -10
===
===
5796:            "evidence_ref": "evidence:" + case["case_id"],
5863:        and evidence.get("evidence_ref")
6306:            item.get("evidence_ref")
8335:        "evidence_ref": "urn:ranex:evidence:estimate-basis",
8476:        "evidence_refs": [],
8551:                "evidence_ref": evidence["evidence_ref"],
8955:                binding["evidence_ref"],
8977:                if row.get("evidence_ref")
8978:                == evidence_binding["evidence_ref"]
8983:                evidence_binding["evidence_ref"],
[0m
[0m$ [0mrg -n "runtime" scripts/architecture/validate_contracts.py | head -20; echo ===; rg -n "schemas/review|review/" scripts/architecture/validate_contracts.py | head -20
124:    / "ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md"
1280:            "Import and runtime fitness tests enforce the architecture."
1390:            "workflow-runtime port."
1489:            "nous, nous-portal, and nousresearch do not resolve as a runtime "
1508:            "Static and runtime route-census tests find no hidden import, "
1585:            "tests or a mature durable runtime is justified."
1681:            "about Hermes 0.19.0, not Ranex runtime obligations."
1718:            "executable fixtures require an enacted runtime subject and are "
2147:                runtime_status = "NOT_ASSESSED"
2165:                runtime_status = (
2175:                runtime_status = "NOT_APPLICABLE"
2194:                "runtime_validation_status": runtime_status,
2247:        "runtime_validation_status",
2278:        "runtime_validation_status": "NOT_ASSESSED",
2391:            if row.get("runtime_validation_status") != "NOT_ASSESSED":
2426:                row.get("runtime_validation_status")
2437:                row.get("runtime_validation_status")
2714:    forged_runtime_pass = copy.deepcopy(actual)
2715:    forged_runtime_pass["entries"][promoted_index][
2716:        "runtime_validation_status"
===
[0m
[0m$ [0msed -n '2130,2200p' scripts/architecture/validate_contracts.py
in allowed_blocking_stages
                    and row["required_result"] == "PASS"
                    and row["failure_outcome"] == "BLOCK",
                    "HERMES_RESEARCH_PROMOTION_FAIL_CLOSED",
                    provision_id,
                )
                if provision_id in {
                    "HERMES-PROMOTION-040",
                    "HERMES-PROMOTION-056",
                }:
                    require(
                        row["check_class"]
                        == "LEGAL_COMPLIANCE_FITNESS"
                        and row["blocking_stage"] == "RELEASE",
                        "HERMES_RESEARCH_LEGAL_OBLIGATION",
                        provision_id,
                    )
                runtime_status = "NOT_ASSESSED"
            elif collection == "owner_decisions":
                guard_ids.append(row["guard_id"])
                require(
                    row["blocking_stage"]
                    in allowed_blocking_stages
                    and row["required_decision_artifact"]
                    == (
                        "ACCEPTED_ADR_WITH_PREDECLARED_"
                        "ACCEPTANCE_TEST"
                    )
                    and row["owner_decision_ref"] is None
                    and row["default"] is None
                    and row["absence_outcome"] == "BLOCK"
                    and row["activation_without_decision"] == "DENIED",
                    "HERMES_RESEARCH_OWNER_DECISION_FAIL_CLOSED",
                    provision_id,
                )
                runtime_status = (
                    "BLOCKED_OWNER_DECISION_REQUIRED"
                )
            else:
                require(
                    row["reason_code"]
                    in allowed_research_reason_codes,
                    "HERMES_RESEARCH_ONLY_REASON",
                    provision_id,
                )
                runtime_status = "NOT_APPLICABLE"

            excerpt = "".join(
                research_lines[start_line - 1 : end_line]
            ).encode("utf-8")
            projected = {
                **row,
                "source_path": research_relative,
                "source_start_line": start_line,
                "source_excerpt_digest": (
                    "sha256:"
                    + hashlib.sha256(excerpt).hexdigest()
                ),
                "research_source_digest": research_digest,
                "catalog_id": catalog["catalog_id"],
                "catalog_version": catalog["catalog_version"],
                "governing_adr": catalog["governing_adr"],
                "governing_adr_source": adr_relative,
                "governing_adr_digest": adr_digest,
                "runtime_validation_status": runtime_status,
            }
            projected["digest"] = digest(projected)
            projected_entries.append(projected)

    require(
        len(guard_ids) == 85
[0m
[0m$ [0mrg -n "fixture_schema_sample|closed_schema_fixture_value" scripts/architecture/generate_contracts.py | head; sed -n '8988,9100p' scripts/architecture/generate_contracts.py
8988:def fixture_schema_sample(schema: dict[str, Any]) -> Any:
8999:        return fixture_schema_sample(
9005:            key: fixture_schema_sample(schema["properties"][key])
9011:            fixture_schema_sample(schema["items"])
9036:def closed_schema_fixture_value(
9050:        return closed_schema_fixture_value(schema["oneOf"][0], seed)
9058:            field_name: closed_schema_fixture_value(
9067:            closed_schema_fixture_value(
9162:    payload = fixture_schema_sample(payload_schema)
11179:        type_id: closed_schema_fixture_value(
def fixture_schema_sample(schema: dict[str, Any]) -> Any:
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "oneOf" in schema:
        non_null = [
            choice
            for choice in schema["oneOf"]
            if choice.get("type") != "null"
        ]
        return fixture_schema_sample(
            non_null[0] if non_null else schema["oneOf"][0]
        )
    schema_type = schema.get("type")
    if schema_type == "object":
        return {
            key: fixture_schema_sample(schema["properties"][key])
            for key in schema.get("required", [])
        }
    if schema_type == "array":
        count = max(schema.get("minItems", 0), 1)
        values = [
            fixture_schema_sample(schema["items"])
            for _ in range(count)
        ]
        return sorted(values, key=canonical_bytes)
    if schema_type == "integer":
        return max(schema.get("minimum", 0), 1)
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        pattern = schema.get("pattern", "")
        if "sha256:" in pattern:
            return "sha256:" + "1" * 64
        if "\\d{4}-\\d{2}" in pattern:
            return FIXED_TIME
        if "-7[0-9a-f]" in pattern:
            return deterministic_uuid7("fixture-schema-sample")
        if schema.get("x-ranex-id-type"):
            return "id_sample"
        return "sample"
    raise ValueError(
        "Cannot construct fixture sample for schema: "
        + json.dumps(schema, sort_keys=True)
    )


def closed_schema_fixture_value(
    schema: dict[str, Any],
    seed: str,
) -> Any:
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "oneOf" in schema:
        if any(
            choice.get("type") == "null"
            for choice in schema["oneOf"]
        ):
            return None
        return closed_schema_fixture_value(schema["oneOf"][0], seed)
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if "null" in schema_type:
            return None
        schema_type = schema_type[0]
    if schema_type == "object":
        return {
            field_name: closed_schema_fixture_value(
                schema["properties"][field_name],
                seed + "-" + field_name,
            )
            for field_name in schema.get("required", [])
        }
    if schema_type == "array":
        count = schema.get("minItems", 0)
        values = [
            closed_schema_fixture_value(
                schema["items"],
                seed + f"-{index}",
            )
            for index in range(count)
        ]
        if schema.get("x-ranex-bytewise-sorted"):
            values.sort(key=canonical_bytes)
        return values
    if schema_type == "integer":
        return schema.get("minimum", 0)
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        pattern = schema.get("pattern", "")
        seed_digest = hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()
        if "sha256:" in pattern:
            return "sha256:" + seed_digest
        if "{64}" in pattern:
            return seed_digest
        if "{40}" in pattern:
            return seed_digest[:40]
        if "[0-9]+" in pattern and r"\." in pattern:
            return "1.0.0"
        if "/v[1-9]" in pattern:
            return "fixture/v1"
        if "urn:" in pattern:
            return "urn:ranex:fixture:" + seed_digest[:16]
        if (
            schema.get("format") == "date-time"
            or r"\d{4}" in pattern
        ):
[0m
[0m$ [0mrg -n "PLAUSIBLE" . 2>/dev/null | head; echo === ; rg -n "confirmed|refuted|dissolved|Dissolved" docs/research/reviewer-model-capability-probe-2026-07-30.md | head; echo ===; rg -n "\"confidence\"" docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json | head -3; rg -n "confidence" docs/architecture/templates/RESEARCH_PACKET.yaml docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml 2>/dev/null | head
===
112:   at `path:line`. Every claim that dissolved was framing. This is already partially enforced —
===
104:      "confidence": "HIGH_FOR_BYTES_LOW_FOR_PROVENANCE",
117:      "confidence": "HIGH",
130:      "confidence": "HIGH_FOR_PUBLIC_SELF_REPORT",
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:256:confidence:
docs/architecture/templates/RESEARCH_PACKET.yaml:39:    confidence: ""
[0m
[0m$ [0msed -n '250,270p' docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml; echo ===; rg -n "VERIFIED_LOCAL|REPORTED|VERIFIED" docs/architecture/templates/RESEARCH_PACKET.yaml | head; echo ===; sed -n '30,45p' docs/architecture/templates/RESEARCH_PACKET.yaml; echo ===; rg -n "RESULT_UNKNOWN|RESULT_NOT_ASSESSED" docs/architecture/SDLC_CONTROL_CATALOG.md | head -4
unresolved_material_gap_refs: []
    scored_eligibility_result: NOT_CHECKED
    result: NOT_CHECKED

# Confidence is rule-derived. HIGH requires all seven tests PASS and independent
# sign-off. Any material unresolved gap forces LOW.
confidence:
  adequacy_rule:
    rule_id: ""
    rule_version: ""
    rule_digest: ""
    approval_ref: ""
  tests:
    sample:
      result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
      evidence_refs: []
    duration:
      result: NOT_CHECKED
      evidence_refs: []
    representativeness:
      result: NOT_CHECKED
===
===
    authority: ""
    observed_at: ""
    freshness: ""

claims:
  - claim_id: ""
    statement: ""
    epistemic_status: "UNKNOWN"
    evidence_refs: []
    confidence: ""
    limitations: []

contradictions: []
negative_results: []
unknowns:
  - unknown: ""
===
1754:| `P1` | `RESULT_NOT_ASSESSED`, `RESULT_UNKNOWN`, `LEVEL_0`, `LEVEL_1`, `OVERDUE_CRITICAL_OBLIGATION`, `REPEATED_ESCAPE`, `HIGH_EXPOSURE_DOWNSTREAM_BLOCKAGE`, `LOW_CONFIDENCE_INSTRUMENTATION` |
[0m
[0m$ [0mrg -n "^\*\*|finding\b" docs/research/reviewer-model-capability-probe-2026-07-30.md | head -20; echo ===; rg -n "state: EVALUATION_INCOMPLETE|EVALUATION_" docs/ schemas/ scripts/ -g '!kimi*' | head; echo ===; rg -n "\"state\"" docs/architecture/reviews/ -g '*.json' | head
3:**Date:** 2026-07-30
4:**Decision status:** observational evidence; no routing decision is made or implied
5:**Ranex revision probed:** ADR-0013 `v1.3.0` on `bootstrap/pre-upstream`
6:**Models probed:** `openrouter/tencent/hy3` (high variant), `opencode-go/deepseek-v4-pro`,
8:**Independent review of this document:** none yet
37:**This is a probe, not an evaluation.** Sample sizes are one to three per model, conditions were
61:| The generated tree was unrecoverable | DeepSeek | **Refuted.** The publisher is transactional with rollback. The claim originated in the orchestrator's own prompt and was returned as a finding |
66:**HY3 (high variant).** Produced the two findings nothing else approached — the reclaim/fencing
72:**MiMo-V2.5-Pro.** Performed a full 65-row systematic pass unprompted and found the one remaining
78:**DeepSeek-V4-Pro.** Found real defects in round one, including two that materially weakened
86:**Concurrency has a cliff, not a slope.** Three concurrent high-variant runs against one provider
91:**Silent hangs are indistinguishable from slow work.** One run produced zero bytes for five hours
96:**Suggests** — different reviewer work has different requirements. Deep adversarial reading of an
100:**Does not suggest** any model is better. One to three samples under unequal conditions cannot
103:**Does not authorize** a routing change. `SUB-ROUTING-001` requires repeated equal-budget
111:1. **A finding must be checkable or it is an opinion.** Every claim that survived was verifiable
113:   `review-observation-v1.schema.json` requires `evidence_refs` per finding — but `minItems` is
120:   returned as a finding with a citation. `review-request-v1.schema.json` already carries
136:**Robust finding:** customisation, not cache state, drives the latency tail. Medians differ by
141:**Implication for de-commercialization:** session warmth was not the mechanism. Cold and warm
===
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1476:| `ObservationState` | `OPINION_PRODUCED`, `NO_OPINION`, `OPINION_UNUSABLE`, `EVALUATION_INCOMPLETE` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1989:    values: ["OPINION_PRODUCED", "NO_OPINION", "OPINION_UNUSABLE", "EVALUATION_INCOMPLETE"]
schemas/fixtures/semantic/adr0008-synthetic-definition-contract.json:1410:      "fixture_id": "TDD-CYCLE-PROPOSED-NONNULL-CYCLE_GATE_EVALUATION_REF",
docs/research/ocask-alignment-research-2026-07-27.md:1666:EVALUATION_INCOMPLETE
docs/architecture/templates/REVIEW_OBSERVATION.yaml:12:state: EVALUATION_INCOMPLETE
docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md:555:    - {gate_id: "READY-SOURCE-MANIFEST-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_COMMITTED_SOURCE_MANIFEST", freshness_rule: "PINNED_CLEAN_EVALUATION_COMMIT_AND_UNCHANGED_GOVERNED_PATHS_ON_CLEAN_DESCENDANT_HEAD", bridge_rule_id: "BRIDGE-READY-SOURCE-MANIFEST-001", noncompensating: true}
docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md:558:    - {gate_id: "READY-FORK-PREFLIGHT-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "SDLC_FORK_000_GATE_EVALUATION", freshness_rule: "EVALUATION_COMMIT_CLEAN_UPSTREAM_DERIVED_AND_CURRENT_HEAD_CLEAN_DESCENDANT", bridge_rule_id: "BRIDGE-READY-FORK-PREFLIGHT-001", noncompensating: true}
docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md:561:    - {gate_id: "READY-SEALING-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "POST_LANDING_SEALING_VALIDATION", freshness_rule: "LANDED_EVALUATION_COMMIT_TREE_AND_ALL_GOVERNED_INPUT_DIGESTS_CURRENT", bridge_rule_id: "BRIDGE-READY-SEALING-001", noncompensating: true}
===
[0m
[0m$ [0mrg -n "FindingState|VerdictState|ACCEPTABLE|CHANGES_REQUIRED|INELIGIBLE" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -12; echo ===; sed -n '1470,1485p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
===
| `RuleStage` | Derived policy classifier `STATE-RULE-STAGE-1.0`, owned by `policy`: `GOVERNANCE`, `DISCOVERY`, `REQUIREMENTS`, `DESIGN`, `PLANNING`, `IMPLEMENTATION`, `VERIFICATION`, `RELEASE`, `OPERATIONS`, `OUTCOME_REVIEW`, `MAINTENANCE`, `RETIREMENT` |
| `IncidentStatus` | `DETECTED`, `ACKNOWLEDGED`, `MITIGATING`, `MITIGATED`, `RECOVERY_VERIFIED`, `REVIEWED`, `ACTIONS_TRACKED`, `CLOSED` |
| `ReleaseStatus` | `PLANNED`, `BUILT`, `VERIFIED`, `RELEASE_READY`, `RELEASING`, `OPERATING`, `ROLLED_BACK`, `WITHDRAWN` |
| `CapabilityStatus` | `PROPOSED`, `SUPPORTED`, `DEPRECATED`, `RETIRE_READY`, `RETIRING`, `RETIRED` |
| `ActivityStatus` | `REQUESTED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
| `GateOutcome` | `PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, `CHECKER_FAULT` |
| `ObservationState` | `OPINION_PRODUCED`, `NO_OPINION`, `OPINION_UNUSABLE`, `EVALUATION_INCOMPLETE` |
| `PermitStatus` | `ISSUED`, `CONSUMED`, `EXPIRED`, `REVOKED` |
| `HumanDecisionRecordStatus` | `PENDING`, `APPROVED`, `DENIED`, `EXPIRED`, `REVOKED` |
| `AuthorityGrantStatus` | `ISSUED`, `CONSUMED`, `EXPIRED`, `REVOKED` |
| `EffectStatus` | `INTENDED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`, `OUTCOME_UNKNOWN` |
| `ReconciliationStatus` | `NOT_REQUIRED`, `PENDING`, `RUNNING`, `RESOLVED`, `UNRESOLVED` with preserved discovered effect disposition |
| `ModuleStatus` | `PACKAGED`, `DISABLED`, `QUALIFIED`, `CANARY`, `ACTIVE`, `RESTRICTED`, `QUARANTINED`, `RETIRED` |
| `RouteStatus` | `UNCONFIGURED`, `AUTHENTICATED`, `SMOKE_TESTED`, `PROBATION`, `APPROVED`, `RESTRICTED`, `SUSPENDED`, `RETIRED` |
| `ExtensionStatus` | `DISCOVERED`, `QUARANTINED`, `REVIEWED`, `QUALIFIED`, `PINNED`, `ENABLED`, `SUSPENDED`, `RETIRED` |
| `CompatibilityStatus` | `SUPPORTED`, `DEPRECATED`, `READ_ONLY`, `REMOVED`; owned by `service_management` for each registered legacy surface |
[0m
[0m$ [0mrg -n "jsonschema" scripts/architecture/generate_contracts.py | head; echo ===; rg -n "jsonschema.validate|Draft202012|validator" scripts/architecture/validate_contracts.py | head -20
27:import jsonschema
5428:            jsonschema.Draft202012Validator(
5430:                format_checker=jsonschema.FormatChecker(),
5465:            jsonschema.Draft202012Validator(
5467:                format_checker=jsonschema.FormatChecker(),
===
1719:            "not fabricated by the documentation validator."
2307:    validator = jsonschema.Draft202012Validator(row_schema)
2313:        if list(validator.iter_errors(row)):
4076:            "validator_requirement",
6528:    validator = jsonschema.Draft202012Validator(
6546:        errors = list(validator.iter_errors(fact))
7025:    transition_validator = jsonschema.Draft202012Validator(
7038:                transition_validator.iter_errors(fact)
7168:        not list(transition_validator.iter_errors(acceptance_fact)),
7249:    envelope_validator = jsonschema.Draft202012Validator(
7290:                    envelope_validator.iter_errors(event)
7550:    validator = jsonschema.Draft202012Validator(
7576:            and not list(validator.iter_errors(case["fact"]))
7619:                error.validator == "required"
7620:                for error in validator.iter_errors(fact)
7646:        errors = list(validator.iter_errors(fact))
7689:        validator.iter_errors(additional["fact"])
7697:            error.validator == "additionalProperties"
7722:        schema_errors = list(validator.iter_errors(case["fact"]))
8760:            jsonschema.Draft202012Validator(
[0m
[0m$ [0msed -n '5400,5480p' scripts/architecture/generate_contracts.py
source_schema = legacy_test_record_schema(
            (
                "test_behavior_authorities"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else "direct_source_classification_authorities"
            ),
            (
                "test-behavior-authority-v1.schema.json"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else (
                    "direct-source-classification-"
                    "authority-v1.schema.json"
                )
            ),
            spec["record_type"],
        )
        row_schema = adr10_closed_object_schema(
            nested_by_type[spec["row_type"]],
            nested_by_type,
            {
                row["type_id"]: row
                for row in parse_tdd_nested_type_catalog()["types"]
            },
        )
        rows: list[dict[str, Any]] = []
        seen_ids: set[tuple[str, ...]] = set()
        for source_path in source_paths:
            source = load_json_strict(source_path)
            jsonschema.Draft202012Validator(
                source_schema,
                format_checker=jsonschema.FormatChecker(),
            ).validate(source)
            identity = tuple(source[field] for field in spec["id_fields"])
            if identity in seen_ids:
                raise ValueError(
                    "ADR-0010 duplicate authority identity: "
                    + ":".join(identity)
                )
            seen_ids.add(identity)
            expected_name = (
                source["behavior_id"]
                + "@"
                + source["behavior_version"]
                + ".json"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else source["classification_id"] + ".json"
            )
            if source_path.name != expected_name:
                raise ValueError(
                    "ADR-0010 authority filename identity drift: "
                    + str(source_path.relative_to(ROOT))
                )
            source_relative = str(source_path.relative_to(ROOT))
            row = {
                field: (
                    source_relative
                    if field == "source_path"
                    else (
                        "sha256:" + sha256_file(source_path)
                        if field == "source_digest"
                        else source[field]
                    )
                )
                for field in nested_by_type[spec["row_type"]]["fields"]
            }
            jsonschema.Draft202012Validator(
                row_schema,
                format_checker=jsonschema.FormatChecker(),
            ).validate(row)
            rows.append(row)
        catalogs[spec["registry_filename"]] = registry(
            spec["registry_id"],
            "1.0.0",
            rows,
            source_pattern=next(
                row["source_pattern"]
                for row in contract["record_catalog"]
                if row["type_id"] == spec["record_type"]
            ),
            source_count=len(source_paths),
            entry_count=len(rows),
[0m
[0m$ [0mrg -n "REVIEW_OBSERVATION|TEMPLATES|templates/" scripts/architecture/validate_contracts.py | head -15
31:TEMPLATES = ROOT / "docs" / "architecture" / "templates"
4133:        ROOT / "docs/architecture/templates/CHECKER_RESULT.yaml"
11307:                "docs/architecture/templates/"
11311:                "docs/architecture/templates/"
21114:        for path in TEMPLATES.glob("*.yaml")
[0m
[0m$ [0msed -n '21100,21230p' scripts/architecture/validate_contracts.py
artifact_registry = load_json(CONTRACTS / "artifact-types.json")
    entries = artifact_registry["entries"]
    authored_entries = [
        entry
        for entry in entries
        if entry["projection_kind"] == "AUTHORING_TEMPLATE"
    ]
    generated_entries = [
        entry
        for entry in entries
        if entry["projection_kind"] == "GENERATED_PROJECTION"
    ]
    governed_template_paths = {
        str(path.relative_to(ROOT))
        for path in TEMPLATES.glob("*.yaml")
        if isinstance(load_yaml(path), dict)
        and "artifact_type" in load_yaml(path)
    }
    require(
        set(artifact_registry)
        == {
            "registry_id",
            "version",
            "status",
            "generated_by",
            "entries",
            "artifact_type_count",
            "authoring_template_count",
            "generated_projection_count",
        }
        and artifact_registry["artifact_type_count"] == len(entries)
        and artifact_registry["authoring_template_count"]
        == len(authored_entries)
        == len(governed_template_paths)
        and artifact_registry["generated_projection_count"]
        == len(generated_entries)
        == len(EXPECTED_GENERATED_ARTIFACT_SCHEMAS)
        and len(entries)
        == len(authored_entries) + len(generated_entries),
        "ARTIFACT_TYPE_DENOMINATOR",
        str(len(entries)),
    )
    unique(entries, "artifact_type", "ARTIFACT_TYPE_DUPLICATE")
    unique(entries, "schema_path", "ARTIFACT_SCHEMA_DUPLICATE")
    require(
        len(
            {
                entry["template_path"]
                for entry in authored_entries
            }
        )
        == len(authored_entries),
        "ARTIFACT_TEMPLATE_DUPLICATE",
        "",
    )
    seen: dict[str, str] = {}
    expected_entry_fields = {
        "artifact_type",
        "template_path",
        "schema_path",
        "canonical_producer",
        "owner_context",
        "projection_kind",
        "generation_contract_ref",
        "authority_status",
        "runtime_producer_validation_status",
    }
    for entry in authored_entries:
        require(
            set(entry) == expected_entry_fields
            and entry["template_path"] in governed_template_paths
            and entry["generation_contract_ref"] is None
            and entry["authority_status"] == "DEFINED"
            and entry["runtime_producer_validation_status"]
            == "NOT_ASSESSED",
            "ARTIFACT_TEMPLATE_REGISTRY_ROW",
            entry["artifact_type"],
        )
        template_path = ROOT / entry["template_path"]
        schema_path = entry["schema_path"]
        require(template_path.exists(), "TEMPLATE_MISSING", entry["template_path"])
        require(schema_path in schemas, "ARTIFACT_SCHEMA_MISSING", schema_path)
        instance = load_yaml(template_path)
        if entry["artifact_type"] == "transition_event":
            source_fields = [
                field["name"]
                for field in hermes_transition_fact_contract()[
                    "required_fields"
                ]
            ]
            require(
                list(instance) == source_fields,
                "TRANSITION_TEMPLATE_SOURCE_PROJECTION",
                entry["template_path"],
            )
        else:
            jsonschema.Draft202012Validator(
                schemas[schema_path]
            ).validate(instance)
        require(instance["artifact_type"] == entry["artifact_type"], "ARTIFACT_TYPE_MISMATCH", entry["template_path"])
        require(entry["canonical_producer"] != "", "PRODUCER_MISSING", entry["artifact_type"])
        require(
            entry["owner_context"],
            "ARTIFACT_OWNER_MISSING",
            entry["artifact_type"],
        )
        seen[entry["artifact_type"]] = schema_path
        checks["governed_templates"] += 1

    expected_generated = {
        artifact_type: {
            "artifact_type": artifact_type,
            **expected,
            "template_path": None,
            "projection_kind": "GENERATED_PROJECTION",
            "authority_status": "DEFINED",
            "runtime_producer_validation_status": "NOT_ASSESSED",
        }
        for artifact_type, expected
        in EXPECTED_GENERATED_ARTIFACT_SCHEMAS.items()
    }
    actual_generated = {
        entry["artifact_type"]: entry for entry in generated_entries
    }
    require(
        actual_generated == expected_generated,
        "GENERATED_ARTIFACT_PROJECTION_SET",
        (
            "missing="
            + ",".join(
                sorted(set(expected_generated) - set(actual_generated))
[0m
[0m$ [0mrg -n "disagree|dissent|conflict" docs/architecture/AI_ARTIFACT_CONTRACTS.md docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -15; echo ===; rg -n "route_fact_diversity|diversity" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -8
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:226:| Policy failure | Deny visibly. Missing, stale, malformed, unavailable, or conflicting blocking proof cannot pass. |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:517:| `context_compilation` | Resolved source manifests, packet compilation, context budget, conflicts, provenance | Deterministic and recorded stochastic retrieval |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1131:| `context_compilation` | `api/{commands,queries,views}.py`; `domain/{source_records,precedence,freshness,conflicts,budgets,manifests,packets,invariants}.py` | `application/{source_resolver,packet_compiler,rendering_service}.py`; `application/ports/{source_provider,retrieval_activity}.py` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2685:| `idempotency_key` | nonempty stable logical-operation key; same key plus different subject/payload is a conflict |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2795:| `EVENT-OUTCOMEREQUIREMENTREFSBOUND` / `OutcomeRequirementRefsBound` | `work_management` / `traceability_service`; `product_definition`, `assurance` | `WorkItem`; owned outcomes/requirements/criteria resolve without conflict | `work_item_id:Id<WorkItem>`, `outcome_refs:Set<ArtifactRef>`, `requirement_refs:Set<ArtifactRef>`, `acceptance_criterion_refs:Set<ArtifactRef>`, `trace_manifest_digest:Sha256` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2800:| `EVENT-RUNREQUESTEDFORWORKITEM` / `RunRequestedForWorkItem` | `work_management` / `run_request_service`; `governed_execution` | `WorkItem`; item ready, no conflicting active run, exact subject/profile bound | `work_item_id:Id<WorkItem>`, `run_request_id:Id<RunRequest>`, `requested_subject_ref:ArtifactRef`, `requested_subject_digest:Sha256`, `workflow_request_ref:Ref<WorkflowRequest>`, `requested_at:Utc` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3226:dependencies and conflicts
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3321:- conflict status.
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4078:    Their adopted and rejected uses, edition/extraction limits, conflicts, and
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4137:- blocking disagreements have human decisions; and
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4164:- the canonical contract set is generated and conflict-free;
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4166:  evidence with no material `UNKNOWN`, conflict, stale result, or unexpired
docs/architecture/AI_ARTIFACT_CONTRACTS.md:118:the selected subject has no separate manifest. Missing, conflicting, or
docs/architecture/AI_ARTIFACT_CONTRACTS.md:185:rule set, instruction-registry version, applicability evidence, conflicts,
docs/architecture/AI_ARTIFACT_CONTRACTS.md:458:coverage, conflicting/missing evidence, exact subject, evaluator code digest,
===
[0m
[0m$ [0mgrep -n "OPEN\|ACCEPTED\|FIXED_PENDING\|VERIFIED\|DISPUTED\|SPECIALIST_REVIEW\|REJECTED_WITH_EVIDENCE\|HUMAN_ACCEPTED_RISK" docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n 1,12p; echo ===; grep -n "NOT_CHECKED" docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml | head -3; echo ===; sed -n '15,40p' schemas/research/research-packet-v1.schema.json; echo ===; grep -n "Refuted\|Robust finding\|Discarded finding\|dissolved" docs/research/reviewer-model-capability-probe-2026-07-30.md
411:A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
428:OPEN
429:  -> ACCEPTED
430:  -> FIXED_PENDING_VERIFICATION
431:  -> VERIFIED
433:OPEN
434:  -> DISPUTED
435:  -> SPECIALIST_REVIEW
436:  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
===
83:    totals_identity_result: NOT_CHECKED # eligible = included + excluded
84:    strata_complete_result: NOT_CHECKED
85:    strata_sum_to_totals_result: NOT_CHECKED
===
          },
          "confidence": {
            "type": "string"
          },
          "epistemic_status": {
            "type": "string"
          },
          "evidence_refs": {
            "items": {},
            "type": "array"
          },
          "limitations": {
            "items": {},
            "type": "array"
          },
          "statement": {
            "type": "string"
          }
        },
        "required": [
          "claim_id",
          "statement",
          "epistemic_status",
          "evidence_refs",
          "confidence",
          "limitations"
===
60:| The fidelity pin is an exact-string blacklist and therefore weak | DeepSeek | **Refuted.** It is an equality allowlist against corrected text; a paraphrase fails closed. Settled by reading `validate_contracts.py:1356-1361` |
61:| The generated tree was unrecoverable | DeepSeek | **Refuted.** The publisher is transactional with rollback. The claim originated in the orchestrator's own prompt and was returned as a finding |
62:| The prototype tree could not be safely regenerated | DeepSeek | **Refuted** by the same mechanism |
112:   at `path:line`. Every claim that dissolved was framing. This is already partially enforced —
136:**Robust finding:** customisation, not cache state, drives the latency tail. Medians differ by
145:**Discarded finding:** the harness printed a verdict on a `cold − warm` gap of `+2.54 s` at p95.
[0m
[0m$ [0mgrep -n "Draft202012Validator" scripts/architecture/validate_contracts.py | sed -n '1,30p' | grep -n "" | tail -5; grep -n "schemas\[schema_path\]" scripts/architecture/validate_contracts.py
26:22159:    jsonschema.Draft202012Validator(
27:22294:            if jsonschema.Draft202012Validator(
28:22365:        validator = jsonschema.Draft202012Validator(
29:22427:        validator = jsonschema.Draft202012Validator(
30:22638:        validator = jsonschema.Draft202012Validator(schema)
7484:        and schemas[schema_path]
7551:        schemas[schema_path],
13947:                schemas[schema_path]
21066:        schema = schemas[schema_path]
21197:                schemas[schema_path]
21245:        schema = schemas[schema_path]
21854:        record_schema = schemas[schema_path]
22160:        schemas[schema_path],
22417:        schema = schemas[schema_path]
[0m
[0m$ [0msed -n '21193,21200p' scripts/architecture/validate_contracts.py; sed -n '21170,21178p' scripts/architecture/validate_contracts.py
entry["template_path"],
            )
        else:
            jsonschema.Draft202012Validator(
                schemas[schema_path]
            ).validate(instance)
        require(instance["artifact_type"] == entry["artifact_type"], "ARTIFACT_TYPE_MISMATCH", entry["template_path"])
        require(entry["canonical_producer"] != "", "PRODUCER_MISSING", entry["artifact_type"])
            and entry["template_path"] in governed_template_paths
            and entry["generation_contract_ref"] is None
            and entry["authority_status"] == "DEFINED"
            and entry["runtime_producer_validation_status"]
            == "NOT_ASSESSED",
            "ARTIFACT_TEMPLATE_REGISTRY_ROW",
            entry["artifact_type"],
        )
        template_path = ROOT / entry["template_path"]
[0m
[0m$ [0mgrep -n "usage" docs/architecture/templates/ANALYSIS_ATTEMPT.yaml; sed -n '1,60p' docs/architecture/templates/ANALYSIS_ATTEMPT.yaml | grep -n "usage" ; sed -n "$(grep -n 'usage' docs/architecture/templates/ANALYSIS_ATTEMPT.yaml | head -1 | cut -d: -f1),+2p" docs/architecture/templates/ANALYSIS_ATTEMPT.yaml
39:usage: {}
39:usage: {}
usage: {}
raw_output_artifact_ref: ""
raw_output_digest: ""
[0m
[0m$ [0mgrep -n "ReviewVerdict\` values\|Empty string is not a substitute\|inspectable evidence" docs/architecture/AI_ARTIFACT_CONTRACTS.md; grep -n "blind_context_satisfied\|deterministic independence" docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml
58:and evidence identity. Empty string is not a substitute for absent/unknown;
398:`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
404:`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
2:# Produced by deterministic independence validation, never by the reviewer.
30:  blind_context_satisfied:
[0m
# Findings

---

**F1 — BLOCKER — A finding citing nothing, claiming nothing, located nowhere validates against `review-observation-v1`.**

- Schema: `schemas/review/review-observation-v1.schema.json:35-38` (`evidence_refs` = `{"items": {}, "type": "array"}` — presence required at line 79, no `minItems`); every other finding field is a bare `{"type": "string"}` (`category`:23-25, `severity`:63-65, `confidence`:29-31, `location`:45-47, `claim`:26-28, `impact`:42-44, `required_action`:60-62, `state`:66-68). Both suspected instances from the brief are **confirmed at source**, and the defect is wider than the brief: *every* finding field is degenerate-satisfiable.
- Generator: `scripts/architecture/generate_contracts.py:10417` — `{"type": "array", "items": infer_schema(value[0], ...) if value else {}}`: an empty template list yields untyped items and no `minItems`. `scripts/architecture/generate_contracts.py:10400` — string default with no `minLength`/`enum`. `scripts/architecture/generate_contracts.py:10413` — `required` is just template key presence, never content. Template input that drives this: `docs/architecture/templates/REVIEW_OBSERVATION.yaml:23` (`evidence_refs: []`) and `:16-24` (empty-string placeholders).
- Empirically verified (jsonschema Draft 2020-12): this instance validates:

```json
{"schema_version":"1","artifact_type":"review_observation","observation_id":"","review_request_id":"","analysis_attempt_id":"","subject_schema":null,"subject_ref":"","subject_digest":"","subject_manifest_digest":null,"core_sdlc_trace_ref":"","state":"","summary":"","findings":[{"finding_id":"","category":"","severity":"","confidence":"","epistemic_status":"","location":"","claim":"","impact":"","evidence_refs":[],"required_action":"","owner_ref":null,"state":"","reconciliation_ref":null}],"uncertainties":[],"limitations":[],"proposed_actions":[],"digest":""}
```

- Contradicts the owning contract's own text: `docs/architecture/AI_ARTIFACT_CONTRACTS.md:58-59` ("Empty string is not a substitute for absent/unknown") and the probe's requirement (`docs/research/reviewer-model-capability-probe-2026-07-30.md:111-114`).
- Strongest counter-argument: the schema declares `x-ranex-runtime-semantics: scripts/architecture/validate_contracts.py` (`review-observation-v1.schema.json:158`), so rigour lives in the runtime validator, not the schema. Counter fails: `validate_contracts.py` contains **zero** semantic checks for review observations — `rg "review_observation|epistemic|blind_context" scripts/architecture/validate_contracts.py` matches nothing relevant (only `review_verdict` as an artifact-type token at :4204, :18928, :26882, :27199 in unrelated legacy-test contexts).

---

**F2 — BLOCKER — `evidence_refs` entries constrain nothing: `[null, 42, {}, "", "not a path", []]` validates.**

- Schema: `schemas/review/review-observation-v1.schema.json:36` (`"items": {}` — the empty schema accepts any JSON value). Same defect in `review-verdict-v1.schema.json:16-19` and every `checks.*.evidence_refs` in `independence-evaluation-v1.schema.json:23-26,40-43,57-60,74-77,91-94,108-111,125-128,142-145`.
- Empirically verified: a finding with `evidence_refs: [null, 42, {}, "", "not a path", []]` validates.
- The generator already builds a typed evidence ref — `common/evidence-ref.schema.json` with `evidence_ref` `minLength: 1` and a real digest `pattern` (`scripts/architecture/generate_contracts.py:10447-10454`) — but `infer_schema` (`generate_contracts.py:10408-10418`) has no `$ref` mechanism, so review schemas never reference it. Fix belongs at the generator: teach the review-family branch of the loop at `generate_contracts.py:19506-19523` to bind `evidence_refs.items` to the existing common schema.
- Strongest counter-argument: refs may legitimately be heterogeneous (URNs, paths, artifact ids), so `items: {}` is intentional latitude. Counter fails: latitude between *string forms* would be `{"type":"string","minLength":1}`; accepting `null` and `42` serves no representational purpose and directly defeats "a finding must be checkable" (`docs/research/reviewer-model-capability-probe-2026-07-30.md:111-114`).

---

**F3 — MAJOR — Digest and timestamp constraints are dead annotations; `"digest": "sha256:nope"` and `"produced_at": "not a date"` validate.**

- Generator: `scripts/architecture/generate_contracts.py:10401-10404` emits `x-ranex-runtime-pattern` / `x-ranex-runtime-format` instead of the enforceable `pattern` / `format` keywords. `rg "x-ranex-runtime-pattern"` across the repo shows exactly one producer (`generate_contracts.py:10402`) and **zero consumers** — not `validate_contracts.py`, nothing.
- Contrast inside the same generator: `common_schemas()` uses the real `pattern` keyword (`generate_contracts.py:10422,10426`), so the enforceable form was available.
- Effect verified empirically on `review-verdict-v1` (schema `:12-15,35-38`): `digest: "sha256:nope"`, `produced_at: "not a date"` validate; on `review-request-v1` (`:13-16`): `blind_context_manifest_digest: ""` validates.
- Every schema in the family claims `"x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py"` (e.g., `review-verdict-v1.schema.json:107`), and that script enforces none of these patterns for review artifacts — the annotation over-claims an enforcement that does not exist.
- Strongest counter-argument: JSON Schema 2020-12 `format` is annotation-only by default anyway, and the annotations are reserved for a future runtime validator (runtime is declared `NOT_ASSESSED`, `docs/HANDOFF.md:43`). Partially survives for `format`; fails for `pattern`, which *is* assertive in every mainstream validator and was deliberately renamed into inertness. See F4 for the structural reason.

---

**F4 — BLOCKER — The vacuous instance is load-bearing: the pipeline *requires* the degenerate artifact to validate, so any generator-side fix breaks the build unless templates change with it.**

- `scripts/architecture/validate_contracts.py:21196-21198` validates each authoring template against its generated schema (`jsonschema.Draft202012Validator(schemas[schema_path]).validate(instance)`). The review templates are all-empty placeholder skeletons (`docs/architecture/templates/REVIEW_OBSERVATION.yaml:8-9,13,16-24`; `REVIEW_VERDICT.yaml:10-22`; `REVIEW_REQUEST.yaml:6-14,25`; `INDEPENDENCE_EVALUATION.yaml:42-46`).
- Consequence: adding `minItems: 1` to `evidence_refs`, `minLength: 1` to ids, or a real digest `pattern` in the generator makes `validate_contracts.py` fail on the templates themselves. The vacuity of F1–F3 is not an oversight in one function; it is structurally pinned by the template-validates-against-schema invariant. This plausibly explains the `x-ranex-runtime-pattern` renaming (see Inferences I1).
- The templates' own escape hatch — "Empty placeholders are invalid for SEALED or runtime artifacts" (`REVIEW_OBSERVATION.yaml:1`) — is enforced by nothing: `validate_contracts.py:21173-21174` *requires* `runtime_producer_validation_status == "NOT_ASSESSED"` for every authored artifact type.
- Fix framing (generator, per constraints): either (a) generate two projections per artifact — a permissive AUTHORING profile and a strict SEALED profile — or (b) exempt template instances from strict keywords via a placeholder-aware validation path; both live in `generate_contracts.py:19506-19577` plus `validate_contracts.py:21196-21198`, never in the emitted JSON.
- Strongest counter-argument: this is a deliberate two-phase design; the schema family only promises structural shape now. Counter fails: the schemas advertise runtime semantics *today* (F3), and the probe context says an unenforceable finding contract produces opinions, not findings — the design promise has no owner-visible marker distinguishing "shape-only" from "checkable".

---

**F5 — MAJOR — `epistemic_status` is an unconstrained free string (confirmed), and the generator structurally cannot emit any enum for it.**

- Schema: `schemas/review/review-observation-v1.schema.json:32-34`. Generator: `scripts/architecture/generate_contracts.py:10400` (string fallthrough); only `artifact_type` and `schema_version` are lifted to `const` (`:10396-10399`). The template's `epistemic_status: INFERENCE` (`docs/architecture/templates/REVIEW_OBSERVATION.yaml:19`) is silently downgraded from a vocabulary sample to an arbitrary-string example. Same defect in `schemas/research/research-packet-v1.schema.json:19-21`.
- Minimal instance: `"epistemic_status": ""` — validates (verified, F1 instance).
- Per the brief, I do **not** propose the vocabulary; candidates are inventoried below for owner decision.
- Strongest counter-argument: the vocabulary is an unresolved owner decision (`docs/HANDOFF.md:70`), so an unconstrained string is the correct fail-open placeholder until decided. Counter partially survives on *which* enum, but fails on shape: an owner-pending enum could still be `{"type":"string","minLength":1}` today without prejudging vocabulary; empty string is already outlawed by `AI_ARTIFACT_CONTRACTS.md:58-59`.

---

**F6 — MAJOR — Consensus laundering is representable and cheap: an `ACCEPTABLE` (or `"LGTM_SHIP_IT"`) verdict over zero observations, zero attempts, and zero reconciliations validates; reviewer-vs-reviewer disagreement resolution has no typed representation anywhere in the family.**

- `schemas/review/review-verdict-v1.schema.json:75-77`: `verdict` is a free string — the documented closed set `ACCEPTABLE | CHANGES_REQUIRED | INCOMPLETE | INELIGIBLE` (`docs/architecture/AI_ARTIFACT_CONTRACTS.md:404-405`) is not carried into the schema (generator cause: `generate_contracts.py:10400`; template sample `REVIEW_VERDICT.yaml:14` downgraded, as in F5). Verified: `"verdict": "LGTM_SHIP_IT"` validates.
- `review-verdict-v1.schema.json:27-30` (`observation_ids`), `:42-45` (`reconciliation_refs`), `:16-19` (`evidence_refs`) are all untyped arrays with no `minItems`; `review-record-projection-v1.schema.json:6-9` (`analysis_attempt_refs`) and `:40-43` (`review_observation_refs`) likewise. Verified: a projection with zero attempts and zero observations validates.
- Nothing conditions a verdict on agreement structure: N agreeing observations with `reconciliation_refs: []` is indistinguishable, at schema level, from one adversarially checked observation.
- "Reviewers disagreed; here is what settled it" is representable **only** as opaque strings: `reconciliation_refs` items are `{}` (`review-verdict-v1.schema.json:42-45`) and per-finding `reconciliation_ref` is a nullable free string (`review-observation-v1.schema.json:54-59`). No schema in `schemas/review/` types a resolution record (what claim conflicted, which evidence settled it). The documented finding lifecycle `DISPUTED -> SPECIALIST_REVIEW` (`AI_ARTIFACT_CONTRACTS.md:428-436`) covers maker-vs-reviewer disputes over a single finding, not cross-reviewer contradiction. Per the brief's rule, non-representability is itself the finding — the measured behaviour this family must serve says resolvable disagreement is worth more than consensus (`docs/research/reviewer-model-capability-probe-2026-07-30.md:115-118`), and the schema family cannot record it checkably.
- Strongest counter-argument: `required_route_fact_diversity` (`review-request-v1.schema.json:74-77`) plus `route_fact_diversity_satisfied` (`independence-evaluation-v1.schema.json:122-138`) already force decorrelated reviewers, which is the anti-consensus mechanism. Counter fails: both are untyped arrays / free-string outcomes (`required_route_fact_diversity` items `{}`, may be empty — verified), and diversity of *routes* records nothing about disagreement *content* or its resolution.

---

**F7 — BLOCKER — Blindness is self-assertable: an independence evaluation can claim `blind_context_satisfied` with an invented outcome string, empty evidence, and no reference to any manifest digest; nothing in the family or the validator is obligated to check the digest.**

- Attack chain, all cited:
  1. `review-request-v1.schema.json:13-16` — `blind_context_manifest_digest` is `type: string` with annotation-only pattern (F3); `""` validates (verified).
  2. No schema anywhere defines the blind context manifest artifact itself — `rg "blind" schemas/` yields only the request field and the check name; the digest has nothing registered to match against.
  3. `independence-evaluation-v1.schema.json:20-36` — `blind_context_satisfied` is `{outcome: <free string>, evidence_refs: <untyped array>}`. It carries no field echoing the manifest digest it evaluated; linkage to the request is a free-string `review_request_id` (`:186-188`). Verified: `{"outcome": "SATISFIED_TRUST_ME", "evidence_refs": []}` with top-level `"eligible": true` validates.
  4. `validator_id`/`validator_version`/`validator_code_digest` (`:211-220`) — the fields meant to prove "deterministic validation, never the reviewer" (`docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml:2`) — are free strings; all-`""` validates (verified).
  5. `rg "blind_context" scripts/architecture/validate_contracts.py` — zero hits. The obligation "based on inspectable evidence references. Reviewer self-assertion … insufficient" (`docs/architecture/AI_ARTIFACT_CONTRACTS.md:398-399`) has no executable counterpart.
- Generator cause: same `infer_schema`/`scalar_schema` path (`generate_contracts.py:10400,10408-10418`); fix belongs there (typed check object: outcome from an owner-decided set, `evidence_refs` → `common/evidence-ref.schema.json`, and an `evaluated_manifest_digest` echo field would require template change per F4).
- Strongest counter-argument: digest matching is inherently a runtime join (fetch request, compare bytes) and cannot be expressed in a single-document JSON Schema. Survives for the *comparison*, fails for the *representation*: the evaluation cannot even record which digest it compared, so no downstream auditor can perform the join from the records alone. The mechanism the probe credits as existing (`probe doc:119-122`) is presently a pair of unlinked, unverified free strings.

---

**F8 — MAJOR — `analysis_attempt.usage` is a mandatory closed empty object: recording any usage datum is schema-invalid.**

- `schemas/review/analysis-attempt-v1.schema.json:168-173` — `"usage": {"additionalProperties": false, "properties": {}, "required": [], "type": "object"}`. Verified: `"usage": {"anything": "goes"}` is **rejected**; only `{}` validates. The documented content — "start/end/deadline/budget, … failures, usage" (`docs/architecture/AI_ARTIFACT_CONTRACTS.md:395-398`) — is unrepresentable.
- Generator cause: `docs/architecture/templates/ANALYSIS_ATTEMPT.yaml:39` (`usage: {}`) fed through `infer_schema`'s dict branch (`generate_contracts.py:10409-10415`), which closes the object over zero keys. An empty-dict template plus `additionalProperties: false` is a contradiction the generator should reject or special-case, not emit.
- Strongest counter-argument: intentionally deferred until usage dimensions are decided; `{}` keeps the slot reserved. Counter fails: a reserved-but-open slot would omit `additionalProperties: false` or the field; the emitted schema actively forbids ever writing usage under `schema_version: "1"` while the prose contract promises it.

---

**F9 — MINOR — A review request that grants the reviewer every capability validates: `prohibited_capabilities: []` and `required_independence: []` are accepted.**

- `review-request-v1.schema.json:55-60` (`prohibited_capabilities`, no `minItems`; template default `[write, merge, release, permit_issue]` at `REVIEW_REQUEST.yaml:24` is only a sample), `:67-70` (`required_independence` items `{}`). Verified empirically.
- Counter-argument: policy, not schema, should set the floor; a request with no prohibitions may be legitimate for some review classes. Partially survives — hence MINOR — but note there is no policy check either (`validate_contracts.py`: no hits).

---

**F10 — MINOR — `review_observation.state` is a free string although a closed `ObservationState` axis is already normative and already parsed by the generator.**

- Schema `review-observation-v1.schema.json:106-108` vs. `ObservationState = OPINION_PRODUCED | NO_OPINION | OPINION_UNUSABLE | EVALUATION_INCOMPLETE` (`docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1476` and axis catalog `:1989`). The generator parses this exact catalog into `STATE_AXES` (`generate_contracts.py:1256-1267`) and binds it for `transition_event` (`:19516-19519`) but never binds `state` fields of other artifacts to their axes. Vocabulary exists and is owner-accepted; only the binding is missing — this one is not an owner-decision blocker, unlike F5.
- Counter-argument: axis enforcement is the transition-event's job, artifact `state` is a denormalized echo. Fails: an unconstrained echo can contradict the axis with no detection anywhere.

# Dissolved

**D1 — "Maker==reviewer is unrepresentable/undetectable in the family."** Refuted at source: the request records maker principal/role/run/session (`review-request-v1.schema.json:24-47`) and each attempt records reviewer principal/role/session (`analysis-attempt-v1.schema.json:67-86`); `maker_reviewer_identity_separated` / `maker_reviewer_session_separated` checks exist (`independence-evaluation-v1.schema.json:54-87`). The data for the comparison is fully representable; the absence of an *obligated* comparison is already covered by F7's pattern and is not a separate representability defect.

**D2 — "Digests are unverifiable because canonicalization is unspecified."** Refuted: RFC 8785 + SHA-256 over digest-absent canonical bytes is exactly specified (`docs/architecture/AI_ARTIFACT_CONTRACTS.md:44-52`) and implemented (`generate_contracts.py:885-891`). The defect is enforcement (F3), not specification.

**D3 — "`produced_at` lacking `format: date-time` is an independent defect."** Mostly dissolved: in Draft 2020-12, `format` is non-assertive by default, so even the "correct" keyword would not reject `"not a date"` without a format-assertion vocabulary or `FormatChecker` (which `validate_contracts.py` does apply elsewhere, e.g. `:5428-5431`, but never to review artifacts). Folded into F3 as the enforcement gap; the keyword-renaming itself remains found only for `pattern`.

# Inferences

**I1 — The `x-ranex-runtime-pattern` renaming exists to let placeholder templates pass the template-against-schema check.** Prompting evidence: templates carry `digest: ""` (`REVIEW_OBSERVATION.yaml:31`) yet must validate at `validate_contracts.py:21196-21198`; a real `pattern` would fail them; the same generator uses real `pattern` in `common_schemas()` (`generate_contracts.py:10422,10426`) where no template is validated against it. Not documented anywhere I found; inference, not fact.

**I2 — All six review schemas are pure `infer_schema` output with zero review-specific hardening.** Evidence: `ARTIFACT_SCHEMAS` rows (`generate_contracts.py:273,287,297-300`), the generation loop (`:19506-19523`), and the only special-cased templates being `CHECKER_RESULT.yaml` (`:19524`), `LANDING_RECORD.yaml` (`:19536`), and `TRANSITION_EVENT.yaml` (`:19516`). Inferred from control flow; I did not execute the generator.

**I3 — Contamination risk in this audit itself:** the two "suspected instances" in my brief also appear verbatim in `docs/HANDOFF.md:66-70` and `docs/research/reviewer-model-capability-probe-2026-07-30.md:113-114` — the assumption-returned-as-finding failure mode the probe documents (`:119-120`). Mitigation applied: both were confirmed against schema bytes (`review-observation-v1.schema.json:32-38,70-84`) and by executing a Draft 2020-12 validator on constructed instances, not by trusting the brief. Findings F2–F4, F6–F10 are outside the brief's seeded claims.

**I4 — Severity ratings assume verdicts feed gates.** Evidence for the premise: the review chain terminates in `GateEvaluation` (`AI_ARTIFACT_CONTRACTS.md:377-386`), though the verdict itself is explicitly "not GateOutcome" (`REVIEW_VERDICT.yaml:23`). If verdicts never gate anything, BLOCKERs degrade to MAJOR.

**I5 — No runtime producer exists yet** (nothing writes these artifacts in anger): `docs/HANDOFF.md:43` ("Runtime `NOT_ASSESSED` — nothing runs") and `validate_contracts.py:21173-21174`. This is why every finding is framed as generator defect + template co-change, not as observed exploitation.

# Epistemic vocabulary inventory

Reported for owner decision; no recommendation made or implied.

| # | Vocabulary (verbatim values) | Where used | Citations |
|---|---|---|---|
| V1 | `FACT`, `INFERENCE`, `PROPOSAL`, `OWNER_REQUIREMENT`, `REPORTED_ADVISORY_RESULT` | `epistemic_status` in the only real research-packet instance | `docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:99,165,192,205,231` |
| V2 | `INFERENCE` (template default for review findings) | `epistemic_status` placeholder | `docs/architecture/templates/REVIEW_OBSERVATION.yaml:19` |
| V3 | `UNKNOWN` (template default for research claims) | `epistemic_status` placeholder | `docs/architecture/templates/RESEARCH_PACKET.yaml:37` |
| V4 | `OPINION_PRODUCED`, `NO_OPINION`, `OPINION_UNUSABLE`, `EVALUATION_INCOMPLETE` | normative `ObservationState` axis (observation-level, not finding-level) | `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1476,1989`; template default `REVIEW_OBSERVATION.yaml:12` |
| V5 | `OPEN`, `ACCEPTED`, `FIXED_PENDING_VERIFICATION`, `VERIFIED`, `DISPUTED`, `SPECIALIST_REVIEW`, `REJECTED_WITH_EVIDENCE`, `HUMAN_ACCEPTED_RISK` | finding lifecycle `state` | `docs/architecture/AI_ARTIFACT_CONTRACTS.md:428-436`; template default `OPEN` at `REVIEW_OBSERVATION.yaml:26` |
| V6 | `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, `INELIGIBLE` | `review_verdict.verdict` documented closed set | `docs/architecture/AI_ARTIFACT_CONTRACTS.md:404-405`; template default `INCOMPLETE` at `REVIEW_VERDICT.yaml:14` |
| V7 | `PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, `CHECKER_FAULT` | `GateOutcome` (downstream of verdict) | `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1475` |
| V8 | `UNKNOWN` (only value in evidence) | independence check `outcome` placeholder; full outcome set defined nowhere | `docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml:16,19,22,25,28,31,34,37`; no closed set in `AI_ARTIFACT_CONTRACTS.md` §7 or schema |
| V9 | `EFFECTIVENESS_UNKNOWN`, `EFFECTIVENESS_REGRESSING`, `EFFECTIVENESS_MIXED`; `RESULT_NOT_ASSESSED`, `RESULT_UNKNOWN` | capability/priority trigger codes; also used epistemically in the probe | `scripts/architecture/generate_contracts.py:507-508`; `docs/architecture/SDLC_CONTROL_CATALOG.md:1754-1755`; `docs/research/reviewer-model-capability-probe-2026-07-30.md:151` |
| V10 | `NOT_CHECKED`, `PASS`, `FAIL` | capability-assessment confidence tests | `docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:264` (comment: `NOT_CHECKED \| PASS \| FAIL`), `:83-85` |
| V11 | `NOT_ASSESSED`, `NOT_APPLICABLE`, `BLOCKED_OWNER_DECISION_REQUIRED` | `runtime_validation_status` epistemic markers | `scripts/architecture/validate_contracts.py:2147,2165-2167,2175` |
| V12 | Prose statuses: **Refuted**, *dissolved*, **Robust finding**, **Discarded finding** | probe document's own finding dispositions (confirmed/refuted/unknown family) | `docs/research/reviewer-model-capability-probe-2026-07-30.md:60-62,112,136,145` |
| V13 | Free-form compound confidence strings in the wild: `HIGH`, `HIGH_FOR_BYTES_LOW_FOR_PROVENANCE`, `HIGH_FOR_PUBLIC_SELF_REPORT` | demonstrates vocabulary drift already occurring under unconstrained strings | `docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json:104,117,130` |
| V14 | `PLAUSIBLE` | **zero occurrences in the corpus** (`rg PLAUSIBLE` over docs/, schemas/, architecture/, scripts/: no matches) — if the owner has seen it, it is external to this tree | — |

# Coverage

- **Read in full:** all six `schemas/review/*.schema.json`; all five review templates plus `ANALYSIS_ATTEMPT.yaml`; `docs/architecture/AI_ARTIFACT_CONTRACTS.md` §§2,6,7,7.1,8; probe doc "Applicability to Ranex" + addendum + limitations; `docs/HANDOFF.md` relevant sections.
- **Read in relevant part:** `generate_contracts.py` (22,710 lines) — `scalar_schema`/`infer_schema` (10381-10418), `common_schemas` (10421-10455), the schema-emission loop (19506-19595), fixture samplers (8988-9100), state-axis parsing (952-1271), digest/canonicalization (877-901); `validate_contracts.py` (≈27k lines) — artifact-registry/template validation (21100-21230) plus keyword sweeps.
- **Verified empirically:** every "validates" claim above was executed against the actual schema files with `jsonschema` Draft 2020-12 in `/tmp/opencode`; repository untouched (read-only constraint held; scratch work confined to the pre-approved temp directory).
- **Keyword sweeps (negative results are load-bearing):** `x-ranex-runtime-pattern` consumers (none), `blind_context` in validator (none), `epistemic` in validator (none), `minItems` in any review schema (none), `PLAUSIBLE` anywhere (none).
- **Not done / residual risk:** did not execute the generator (missing deps; read-only intent); did not exhaustively read all 27k lines of `validate_contracts.py`, so a semantic review-family check reachable under a name my sweeps missed is possible — probability low given zero hits on `review_observation`, `independence`, `blind`, `epistemic`; did not audit the five non-review schema families except where used for contrast (`common/evidence-ref`, `transition-event`); did not assess the `git` history for when the `pattern`→annotation rename occurred.
