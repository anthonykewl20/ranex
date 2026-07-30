Reading additional input from stdin...
OpenAI Codex v0.146.0
--------
workdir: /home/soultransit/devtony/ranex
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: high
reasoning summaries: none
session id: 019fb2a4-9b0c-7ac3-8075-9d408b0dfc97
--------
user
# Prior-art sweep A — findings, controls, and provenance

Ranex is a governance harness that compiles architecture documents into
deterministic checking code, so that unreliable AI agents produce auditable
software. The working premise of this task: **Ranex is not novel. Established
standards and production implementations already cover most of what it does.**
Your job is to find them and report precisely what Ranex should adopt, adapt, or
deliberately diverge from — and where it is genuinely without prior art.

Do not design anything. Do not propose original schemas. Find what exists.

## Your assigned layers

1. **Review findings interchange** — how tools represent a finding: rule
   violated, severity, source location, evidence, provenance, suggested fix,
   and confidence/epistemic status.
2. **Controls, assessments, and compliance evidence** — machine-readable
   representation of obligations, assessments, observations, findings, and
   evidence of compliance.
3. **Provenance and attestation** — proving an artifact was produced by a
   declared process from declared inputs, and binding evidence to claims.
4. **Tamper-evident evidence storage** — append-only logs, hash chains,
   transparency logs, and what production systems use to make audit trails
   verifiable.

Known starting points, to verify and go beyond rather than accept from me:
SARIF (OASIS), NIST OSCAL, in-toto, SLSA, W3C PROV, Sigstore, Certificate
Transparency / Trillian. Find others. Where a standard has competitors, say so
and compare.

## What Ranex currently does — read it, cite it

- `schemas/review/` — six schemas: `review-observation-v1`, `review-verdict-v1`,
  `review-request-v1`, `analysis-attempt-v1`, `independence-evaluation-v1`,
  `review-record-projection-v1`.
- `docs/architecture/AI_ARTIFACT_CONTRACTS.md` — the prose contract for these
  artifacts, including the finding lifecycle and verdict vocabulary.
- `docs/architecture/templates/REVIEW_OBSERVATION.yaml` and siblings — the
  authoring templates the schemas are generated from.
- `schemas/common/evidence-ref.schema.json` — the evidence reference type.
- `src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py` in the
  separate worktree `.claude/worktrees/kernel-tracer` (branch
  `feature/kernel-tracer`, untracked `src/`) — the current evidence ledger.
- All schemas are **generated** by `scripts/architecture/generate_contracts.py`
  from the templates; never propose editing generated output.

## Required output — one row per layer or sub-layer

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |

`Verdict` is exactly one of:
- **ADOPT** — use the standard directly; Ranex's version adds nothing.
- **ADAPT** — the standard is right but needs a stated modification; say which
  and why.
- **DIVERGE** — Ranex's approach is deliberately different and defensible; give
  the reason it must differ.
- **NOVEL** — you searched and found no prior art. Say what you searched.

`Specific delta` must be actionable: which field, which construct, what changes.
"Consider aligning with SARIF" is useless. "SARIF `result.level` replaces the
free-string `severity` field at `review-observation-v1.schema.json:63`" is useful.

## Non-negotiables

- **Verify externally.** Use web search/fetch for every external claim; if those
  tools are unavailable to you, use `curl`. Cite a URL for each. Where you could
  not verify something, mark it `UNVERIFIED` explicitly rather than asserting it.
  Recalled knowledge stated as fact is a failure of this task.
- **Licence check.** For anything you recommend adopting, report its licence and
  whether it is compatible with a source-available, all-rights-reserved product
  that preserves future commercial optionality (see `LICENSE-RANEX.md`). Flag
  anything copyleft or commercially encumbered.
- **Read-only.** Do not modify, create, or delete any file in the repository.
- **Report inferences.** Any conclusion not directly supported by a cited source
  or a repository line goes in an `Inferences` section, marked as inference.
- **Maturity matters.** Prefer a ratified standard or a production system with
  named adopters over a promising project. State adoption evidence.

## Output sections

`Mapping table`, `Adopt shortlist` (ranked, with licence), `Genuinely novel`,
`Inferences`, `Search coverage` (what you searched and what you could not verify).
codex
I’ll trace Ranex’s current fields and lifecycle to exact repository lines, then verify each comparison against primary standards or production documentation. I’ll keep the repository read-only and separate directly supported facts from inference.
  → Inspect Ranex schemas, templates, architecture contract, licence, and hash-chain ledger with exact lines
  • Verify prior-art specifications, maturity/adoption, and licences from primary sources
  • Map Ranex elements to standards with ADOPT/ADAPT/DIVERGE/NOVEL verdicts and actionable deltas
  • Audit citations, inferences, search coverage, and produce the required report
exec
/bin/bash -lc 'pwd && rg --files schemas/review schemas/common docs/architecture scripts/architecture | sort && git status --short && git worktree list --porcelain' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
/home/soultransit/devtony/ranex
docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md
docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md
docs/architecture/AI_ARTIFACT_CONTRACTS.md
docs/architecture/CORE_SDLC_OPERATING_MODEL.md
docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
docs/architecture/README.md
docs/architecture/SDLC_CONTROL_CATALOG.md
docs/architecture/SOURCE_OF_TRUTH.md
docs/architecture/assessments/COMPLETENESS_REPORT.md
docs/architecture/assessments/assessment-source-manifest.json
docs/architecture/assessments/assessment-subject.json
docs/architecture/assessments/completeness-report.json
docs/architecture/assessments/controls/SDLC-AIW-001.json
docs/architecture/assessments/controls/SDLC-AIW-002.json
docs/architecture/assessments/controls/SDLC-AIW-003.json
docs/architecture/assessments/controls/SDLC-AIW-004.json
docs/architecture/assessments/controls/SDLC-AIW-005.json
docs/architecture/assessments/controls/SDLC-AIW-006.json
docs/architecture/assessments/controls/SDLC-AIW-007.json
docs/architecture/assessments/controls/SDLC-BLD-001.json
docs/architecture/assessments/controls/SDLC-BLK-001.json
docs/architecture/assessments/controls/SDLC-CAN-001.json
docs/architecture/assessments/controls/SDLC-CLS-001.json
docs/architecture/assessments/controls/SDLC-CM-001.json
docs/architecture/assessments/controls/SDLC-DEF-001.json
docs/architecture/assessments/controls/SDLC-DES-001.json
docs/architecture/assessments/controls/SDLC-DIS-001.json
docs/architecture/assessments/controls/SDLC-EST-001.json
docs/architecture/assessments/controls/SDLC-FORK-000.json
docs/architecture/assessments/controls/SDLC-FORK-001.json
docs/architecture/assessments/controls/SDLC-FORK-002.json
docs/architecture/assessments/controls/SDLC-FORK-003.json
docs/architecture/assessments/controls/SDLC-FORK-004.json
docs/architecture/assessments/controls/SDLC-FORK-005.json
docs/architecture/assessments/controls/SDLC-FORK-006.json
docs/architecture/assessments/controls/SDLC-FORK-007.json
docs/architecture/assessments/controls/SDLC-INT-001.json
docs/architecture/assessments/controls/SDLC-MEA-001.json
docs/architecture/assessments/controls/SDLC-MEA-002.json
docs/architecture/assessments/controls/SDLC-MNT-001.json
docs/architecture/assessments/controls/SDLC-OPS-001.json
docs/architecture/assessments/controls/SDLC-OUT-001.json
docs/architecture/assessments/controls/SDLC-PA-001.json
docs/architecture/assessments/controls/SDLC-PLN-001.json
docs/architecture/assessments/controls/SDLC-RBK-001.json
docs/architecture/assessments/controls/SDLC-RDY-001.json
docs/architecture/assessments/controls/SDLC-REL-001.json
docs/architecture/assessments/controls/SDLC-RET-001.json
docs/architecture/assessments/controls/SDLC-TAIL-001.json
docs/architecture/assessments/controls/SDLC-TR-001.json
docs/architecture/assessments/controls/SDLC-TRI-001.json
docs/architecture/assessments/controls/SDLC-VER-001.json
docs/architecture/assessments/controls/SDLC-VV-001.json
docs/architecture/assessments/domains/CAP-BUILD-FLOW.json
docs/architecture/assessments/domains/CAP-DESIGN-READINESS.json
docs/architecture/assessments/domains/CAP-DISCOVERY-DEFINITION.json
docs/architecture/assessments/domains/CAP-GOVERN-EVIDENCE.json
docs/architecture/assessments/domains/CAP-HERMES-AI-HEALTH.json
docs/architecture/assessments/domains/CAP-INTAKE-TRIAGE.json
docs/architecture/assessments/domains/CAP-OPERATE-MAINTAIN.json
docs/architecture/assessments/domains/CAP-OUTCOME-CLOSE-RETIRE.json
docs/architecture/assessments/domains/CAP-RELEASE-RECOVERY.json
docs/architecture/assessments/domains/CAP-VERIFY-VALIDATE.json
docs/architecture/assessments/validation-report.json
docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md
docs/architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md
docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md
docs/architecture/decisions/ADR-0004-establish-initial-quality-attribute-baselines.md
docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md
docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md
docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md
docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
docs/architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md
docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
docs/architecture/reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md
docs/architecture/reviews/2026-07-27-foundational-reference-corpus-reconciliation.md
docs/architecture/reviews/2026-07-27-kimi-agent-fleet-research-reconciliation.md
docs/architecture/reviews/2026-07-28-aposd-agent-rules-skills-reconciliation.md
docs/architecture/reviews/2026-07-28-gate-controller-mvp-user-level-audit.md
docs/architecture/reviews/2026-07-28-hermes-initial-runtime-acceptance.md
docs/architecture/reviews/2026-07-28-implementation-worktree-subject-binding-audit.md
docs/architecture/reviews/2026-07-28-live-foundational-reference-corpus-reconciliation.md
docs/architecture/reviews/2026-07-28-modular-ddd-tdd-adversarial-review.md
docs/architecture/reviews/2026-07-28-sdlc-fork-000-preflight.md
docs/architecture/reviews/2026-07-29-claude-runtime-hermes-opencode-reconciliation.md
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md
docs/architecture/reviews/README.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-exact-subject-review.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-exact-subject-review.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-1.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-1.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-2.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-2.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-post-reconciliation-review.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-post-reconciliation-review.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/final-exact-subject-review-bundle-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/final-exact-subject-review-prompt.md
docs/architecture/reviews/artifacts/2026-07-27/final-exact-subject-source-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/final-full-map-review-prompt.md
docs/architecture/reviews/artifacts/2026-07-27/foundational-reference-corpus-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/hy3-final-exact-subject-review.md
docs/architecture/reviews/artifacts/2026-07-27/hy3-final-exact-subject-review.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/hy3-final-review.md
docs/architecture/reviews/artifacts/2026-07-27/hy3-final-review.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.md
docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.metadata.json
docs/architecture/reviews/artifacts/2026-07-27/kimi-research-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/post-reconciliation-full-map-review-prompt.md
docs/architecture/reviews/artifacts/2026-07-27/post-reconciliation-review-bundle-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/post-reconciliation-review-bundle.tar.gz
docs/architecture/reviews/artifacts/2026-07-27/post-reconciliation-source-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/post-review-resulting-source-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-27/source-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/fleet-experiment.json
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-addendum-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-packet.json
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-subject.json
docs/architecture/reviews/artifacts/2026-07-28/aposd-agent-rules-skills/task-population.json
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/artifact-manifest.sha256
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/deepseek-v4-pro-review.md
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/hy3-review-part-1.md
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/hy3-review-part-2.md
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/review-metadata.json
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/review-prompt.md
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/source-manifest.json
docs/architecture/reviews/artifacts/enterprise-build-readiness/sdlc-fork-000-evidence.json
docs/architecture/reviews/artifacts/enterprise-build-readiness/worktree-subject-bindings.json
docs/architecture/reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus-index.json
docs/architecture/reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256
docs/architecture/rfcs/README.md
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md
docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md
docs/architecture/templates/ADR.md
docs/architecture/templates/AGENT_ASSIGNMENT.yaml
docs/architecture/templates/AI_HANDOFF.yaml
docs/architecture/templates/AI_TASK_PACKET.yaml
docs/architecture/templates/ANALYSIS_ATTEMPT.yaml
docs/architecture/templates/ARCHITECTURE_PROPOSAL.yaml
docs/architecture/templates/ARCHITECTURE_RECONCILIATION.yaml
docs/architecture/templates/ARCHITECTURE_REVIEW_PACKET.yaml
docs/architecture/templates/AUTHORITY_GRANT.yaml
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml
docs/architecture/templates/CAPABILITY_DOMAIN_PROJECTION.yaml
docs/architecture/templates/CHECKER_RESULT.yaml
docs/architecture/templates/CORE_SDLC_TRACE.yaml
docs/architecture/templates/DIRECT_SOURCE_CLASSIFICATION_AUTHORITY.yaml
docs/architecture/templates/DISPATCH_OFFER.yaml
docs/architecture/templates/EVIDENCE_SNAPSHOT.yaml
docs/architecture/templates/FLEET_EXPERIMENT.yaml
docs/architecture/templates/GATE_EVALUATION.yaml
docs/architecture/templates/HUMAN_DECISION.yaml
docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml
docs/architecture/templates/LANDING_RECORD.yaml
docs/architecture/templates/MAILBOX_ENVELOPE.yaml
docs/architecture/templates/OPERATION_EVIDENCE.yaml
docs/architecture/templates/OUTCOME_REVIEW.yaml
docs/architecture/templates/PERMIT.yaml
docs/architecture/templates/POST_LANDING_VERIFICATION.yaml
docs/architecture/templates/RELEASE_EVIDENCE.yaml
docs/architecture/templates/RESEARCH_PACKET.yaml
docs/architecture/templates/RESOURCE_RESERVATION.yaml
docs/architecture/templates/REVIEW_OBSERVATION.yaml
docs/architecture/templates/REVIEW_RECORD.yaml
docs/architecture/templates/REVIEW_REQUEST.yaml
docs/architecture/templates/REVIEW_VERDICT.yaml
docs/architecture/templates/RFC.md
docs/architecture/templates/RUN_RESULT.yaml
docs/architecture/templates/TEST_BEHAVIOR_AUTHORITY.yaml
docs/architecture/templates/TRANSITION_EVENT.yaml
docs/architecture/templates/WORKER_ATTEMPT.yaml
docs/architecture/templates/WORKER_LEASE.yaml
docs/architecture/templates/WORK_INTAKE.yaml
schemas/common/architecture-element-assessment-v1.schema.json
schemas/common/architecture-practice-application-profile-v1.schema.json
schemas/common/architecture-rule-assessment-v1.schema.json
schemas/common/architecture-subject-v1.schema.json
schemas/common/canonical-digest.schema.json
schemas/common/context-boundary-fit-v1.schema.json
schemas/common/context-coupling-policy-v1.schema.json
schemas/common/context-dependency-edge-v1.schema.json
schemas/common/core-sdlc-trace-v1.schema.json
schemas/common/direct-source-classification-authority-v1.schema.json
schemas/common/engineering-practice-profile-v1.schema.json
schemas/common/evidence-ref.schema.json
schemas/common/exact-subject-v1.schema.json
schemas/common/feedback-fitness-policy-v1.schema.json
schemas/common/hermes-research-provision-v1.schema.json
schemas/common/identifiers.schema.json
schemas/common/legacy-test-change-exception-v1.schema.json
schemas/common/legacy-test-change-exception-v2.schema.json
schemas/common/legacy-test-cutover-removal-record-v1.schema.json
schemas/common/legacy-test-cutover-removal-record-v2.schema.json
schemas/common/legacy-test-layout-policy-v1.schema.json
schemas/common/legacy-test-layout-policy-v2.schema.json
schemas/common/legacy-test-migration-record-v1.schema.json
schemas/common/legacy-test-migration-record-v2.schema.json
schemas/common/path-contract-v1.schema.json
schemas/common/research-subject-v1.schema.json
schemas/common/resource-subject-v1.schema.json
schemas/common/runtime-adapter-v1.schema.json
schemas/common/subject-binding-v1.schema.json
schemas/common/tdd-cycle-record-v1.schema.json
schemas/common/tdd-cycle-subject-v1.schema.json
schemas/common/tdd-exception-record-v1.schema.json
schemas/common/tdd-exception-subject-v1.schema.json
schemas/common/test-behavior-authority-v1.schema.json
schemas/common/test-deletion-record-v1.schema.json
schemas/common/test-deletion-subject-v1.schema.json
schemas/common/test-practice-profile-v1.schema.json
schemas/common/test-quarantine-record-v1.schema.json
schemas/common/test-quarantine-subject-v1.schema.json
schemas/common/topology-exception-v1.schema.json
schemas/common/work-subject-v1.schema.json
schemas/common/worker-role-profile-v1.schema.json
schemas/review/analysis-attempt-v1.schema.json
schemas/review/independence-evaluation-v1.schema.json
schemas/review/review-observation-v1.schema.json
schemas/review/review-record-projection-v1.schema.json
schemas/review/review-request-v1.schema.json
schemas/review/review-verdict-v1.schema.json
scripts/architecture/README.md
scripts/architecture/contract_tree_lock.py
scripts/architecture/generate_contracts.py
scripts/architecture/pyproject.toml
scripts/architecture/test_contract_concurrency.py
scripts/architecture/uv.lock
scripts/architecture/validate_contracts.py
 M docs/README.md
 M docs/architecture/README.md
 M docs/architecture/reviews/README.md
 M docs/architecture/rfcs/README.md
 M docs/research/README.md
?? docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md
?? docs/architecture/reviews/artifacts/2026-07-30/
?? docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md
?? docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
worktree /home/soultransit/devtony/ranex
HEAD fd00aa06f3dfa2677553076852521841b6e58fa7
branch refs/heads/bootstrap/pre-upstream

worktree /home/soultransit/devtony/ranex/.claude/worktrees/architecture-validated-baseline
HEAD d1fc30b4f74fd67db9baf2356c395ae7d501b4c7
branch refs/heads/architecture/validated-baseline-20260728

worktree /home/soultransit/devtony/ranex/.claude/worktrees/gate-controller-mvp
HEAD 0533e1eaf50ace0eb84435a5c3de05e939fd4daa
branch refs/heads/feature/deterministic-gate-controller-mvp

worktree /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
HEAD 780299025dceb0c215cb05aaeb8fb6b234a94939
branch refs/heads/feature/kernel-tracer

worktree /home/soultransit/devtony/ranex/.claude/worktrees/phase-0-preflight
HEAD fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4
branch refs/heads/phase/0-preflight

worktree /home/soultransit/devtony/ranex/.claude/worktrees/phase-1-adopt-upstream
HEAD 9be6bd9443e447b205ad265d44238436910dfbce
branch refs/heads/phase/1-adopt-upstream

worktree /home/soultransit/devtony/ranex/.claude/worktrees/phase-2-runtime-bootstrap
HEAD 0533e1eaf50ace0eb84435a5c3de05e939fd4daa
branch refs/heads/develop


exec
/bin/bash -lc 'for f in schemas/review/*.json schemas/common/evidence-ref.schema.json docs/architecture/templates/REVIEW_OBSERVATION.yaml docs/architecture/templates/REVIEW_VERDICT.yaml docs/architecture/templates/REVIEW_REQUEST.yaml docs/architecture/templates/ANALYSIS_ATTEMPT.yaml docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml docs/architecture/templates/REVIEW_RECORD.yaml LICENSE-RANEX.md; do echo "FILE $f"; nl -ba "$f"; done' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
FILE schemas/review/analysis-attempt-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/analysis-attempt-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "absolute_deadline": {
     7	      "type": "string",
     8	      "x-ranex-runtime-format": "date-time"
     9	    },
    10	    "artifact_type": {
    11	      "const": "analysis_attempt"
    12	    },
    13	    "attempt_id": {
    14	      "type": "string"
    15	    },
    16	    "core_sdlc_trace_ref": {
    17	      "type": "string"
    18	    },
    19	    "digest": {
    20	      "type": "string",
    21	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    22	    },
    23	    "failure_domain": {
    24	      "type": [
    25	        "string",
    26	        "null"
    27	      ]
    28	    },
    29	    "finished_at": {
    30	      "type": "string",
    31	      "x-ranex-runtime-format": "date-time"
    32	    },
    33	    "granted_capabilities": {
    34	      "items": {},
    35	      "type": "array"
    36	    },
    37	    "input_artifact_refs": {
    38	      "items": {},
    39	      "type": "array"
    40	    },
    41	    "input_manifest_digest": {
    42	      "type": "string",
    43	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    44	    },
    45	    "previous_attempt_id": {
    46	      "type": [
    47	        "string",
    48	        "null"
    49	      ]
    50	    },
    51	    "raw_output_artifact_ref": {
    52	      "type": "string"
    53	    },
    54	    "raw_output_digest": {
    55	      "type": "string",
    56	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    57	    },
    58	    "retry_class": {
    59	      "type": [
    60	        "string",
    61	        "null"
    62	      ]
    63	    },
    64	    "review_request_id": {
    65	      "type": "string"
    66	    },
    67	    "reviewer": {
    68	      "additionalProperties": false,
    69	      "properties": {
    70	        "principal_id": {
    71	          "type": "string"
    72	        },
    73	        "role_id": {
    74	          "type": "string"
    75	        },
    76	        "session_id": {
    77	          "type": "string"
    78	        }
    79	      },
    80	      "required": [
    81	        "principal_id",
    82	        "role_id",
    83	        "session_id"
    84	      ],
    85	      "type": "object"
    86	    },
    87	    "route": {
    88	      "additionalProperties": false,
    89	      "properties": {
    90	        "actual_model_id": {
    91	          "type": "string"
    92	        },
    93	        "actual_model_snapshot": {
    94	          "type": [
    95	            "string",
    96	            "null"
    97	          ]
    98	        },
    99	        "actual_provider_id": {
   100	          "type": "string"
   101	        },
   102	        "executable_digest": {
   103	          "type": "string",
   104	          "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   105	        },
   106	        "isolation_profile_id": {
   107	          "type": "string"
   108	        },
   109	        "parser_version": {
   110	          "type": "string"
   111	        },
   112	        "route_lock_id": {
   113	          "type": "string"
   114	        },
   115	        "transport_digest": {
   116	          "type": "string",
   117	          "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   118	        },
   119	        "transport_id": {
   120	          "type": "string"
   121	        }
   122	      },
   123	      "required": [
   124	        "route_lock_id",
   125	        "actual_provider_id",
   126	        "actual_model_id",
   127	        "actual_model_snapshot",
   128	        "transport_id",
   129	        "transport_digest",
   130	        "executable_digest",
   131	        "parser_version",
   132	        "isolation_profile_id"
   133	      ],
   134	      "type": "object"
   135	    },
   136	    "schema_version": {
   137	      "const": "1"
   138	    },
   139	    "started_at": {
   140	      "type": "string",
   141	      "x-ranex-runtime-format": "date-time"
   142	    },
   143	    "status": {
   144	      "type": [
   145	        "string",
   146	        "null"
   147	      ]
   148	    },
   149	    "subject_digest": {
   150	      "type": "string",
   151	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   152	    },
   153	    "subject_manifest_digest": {
   154	      "type": [
   155	        "string",
   156	        "null"
   157	      ]
   158	    },
   159	    "subject_ref": {
   160	      "type": "string"
   161	    },
   162	    "subject_schema": {
   163	      "type": [
   164	        "string",
   165	        "null"
   166	      ]
   167	    },
   168	    "usage": {
   169	      "additionalProperties": false,
   170	      "properties": {},
   171	      "required": [],
   172	      "type": "object"
   173	    },
   174	    "write_attempt_evidence_refs": {
   175	      "items": {},
   176	      "type": "array"
   177	    }
   178	  },
   179	  "required": [
   180	    "schema_version",
   181	    "artifact_type",
   182	    "attempt_id",
   183	    "review_request_id",
   184	    "previous_attempt_id",
   185	    "subject_schema",
   186	    "subject_ref",
   187	    "subject_digest",
   188	    "subject_manifest_digest",
   189	    "core_sdlc_trace_ref",
   190	    "reviewer",
   191	    "route",
   192	    "input_artifact_refs",
   193	    "input_manifest_digest",
   194	    "granted_capabilities",
   195	    "write_attempt_evidence_refs",
   196	    "started_at",
   197	    "finished_at",
   198	    "absolute_deadline",
   199	    "status",
   200	    "failure_domain",
   201	    "retry_class",
   202	    "usage",
   203	    "raw_output_artifact_ref",
   204	    "raw_output_digest",
   205	    "digest"
   206	  ],
   207	  "title": "analysis_attempt",
   208	  "type": "object",
   209	  "x-ranex-canonical-producer": "analytical_review",
   210	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   211	  "x-ranex-template": "docs/architecture/templates/ANALYSIS_ATTEMPT.yaml"
   212	}
FILE schemas/review/independence-evaluation-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/independence-evaluation-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "analysis_attempt_ids": {
     7	      "items": {},
     8	      "type": "array"
     9	    },
    10	    "artifact_type": {
    11	      "const": "independence_evaluation"
    12	    },
    13	    "blocking_reasons": {
    14	      "items": {},
    15	      "type": "array"
    16	    },
    17	    "checks": {
    18	      "additionalProperties": false,
    19	      "properties": {
    20	        "blind_context_satisfied": {
    21	          "additionalProperties": false,
    22	          "properties": {
    23	            "evidence_refs": {
    24	              "items": {},
    25	              "type": "array"
    26	            },
    27	            "outcome": {
    28	              "type": "string"
    29	            }
    30	          },
    31	          "required": [
    32	            "outcome",
    33	            "evidence_refs"
    34	          ],
    35	          "type": "object"
    36	        },
    37	        "hidden_verification_withheld": {
    38	          "additionalProperties": false,
    39	          "properties": {
    40	            "evidence_refs": {
    41	              "items": {},
    42	              "type": "array"
    43	            },
    44	            "outcome": {
    45	              "type": "string"
    46	            }
    47	          },
    48	          "required": [
    49	            "outcome",
    50	            "evidence_refs"
    51	          ],
    52	          "type": "object"
    53	        },
    54	        "maker_reviewer_identity_separated": {
    55	          "additionalProperties": false,
    56	          "properties": {
    57	            "evidence_refs": {
    58	              "items": {},
    59	              "type": "array"
    60	            },
    61	            "outcome": {
    62	              "type": "string"
    63	            }
    64	          },
    65	          "required": [
    66	            "outcome",
    67	            "evidence_refs"
    68	          ],
    69	          "type": "object"
    70	        },
    71	        "maker_reviewer_session_separated": {
    72	          "additionalProperties": false,
    73	          "properties": {
    74	            "evidence_refs": {
    75	              "items": {},
    76	              "type": "array"
    77	            },
    78	            "outcome": {
    79	              "type": "string"
    80	            }
    81	          },
    82	          "required": [
    83	            "outcome",
    84	            "evidence_refs"
    85	          ],
    86	          "type": "object"
    87	        },
    88	        "reviewer_did_not_mutate_subject": {
    89	          "additionalProperties": false,
    90	          "properties": {
    91	            "evidence_refs": {
    92	              "items": {},
    93	              "type": "array"
    94	            },
    95	            "outcome": {
    96	              "type": "string"
    97	            }
    98	          },
    99	          "required": [
   100	            "outcome",
   101	            "evidence_refs"
   102	          ],
   103	          "type": "object"
   104	        },
   105	        "reviewer_had_no_write_or_authority_capability": {
   106	          "additionalProperties": false,
   107	          "properties": {
   108	            "evidence_refs": {
   109	              "items": {},
   110	              "type": "array"
   111	            },
   112	            "outcome": {
   113	              "type": "string"
   114	            }
   115	          },
   116	          "required": [
   117	            "outcome",
   118	            "evidence_refs"
   119	          ],
   120	          "type": "object"
   121	        },
   122	        "route_fact_diversity_satisfied": {
   123	          "additionalProperties": false,
   124	          "properties": {
   125	            "evidence_refs": {
   126	              "items": {},
   127	              "type": "array"
   128	            },
   129	            "outcome": {
   130	              "type": "string"
   131	            }
   132	          },
   133	          "required": [
   134	            "outcome",
   135	            "evidence_refs"
   136	          ],
   137	          "type": "object"
   138	        },
   139	        "subject_exact": {
   140	          "additionalProperties": false,
   141	          "properties": {
   142	            "evidence_refs": {
   143	              "items": {},
   144	              "type": "array"
   145	            },
   146	            "outcome": {
   147	              "type": "string"
   148	            }
   149	          },
   150	          "required": [
   151	            "outcome",
   152	            "evidence_refs"
   153	          ],
   154	          "type": "object"
   155	        }
   156	      },
   157	      "required": [
   158	        "maker_reviewer_identity_separated",
   159	        "maker_reviewer_session_separated",
   160	        "subject_exact",
   161	        "reviewer_did_not_mutate_subject",
   162	        "reviewer_had_no_write_or_authority_capability",
   163	        "blind_context_satisfied",
   164	        "route_fact_diversity_satisfied",
   165	        "hidden_verification_withheld"
   166	      ],
   167	      "type": "object"
   168	    },
   169	    "core_sdlc_trace_ref": {
   170	      "type": "string"
   171	    },
   172	    "digest": {
   173	      "type": "string",
   174	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   175	    },
   176	    "eligible": {
   177	      "type": "boolean"
   178	    },
   179	    "evaluated_at": {
   180	      "type": "string",
   181	      "x-ranex-runtime-format": "date-time"
   182	    },
   183	    "evaluation_id": {
   184	      "type": "string"
   185	    },
   186	    "review_request_id": {
   187	      "type": "string"
   188	    },
   189	    "schema_version": {
   190	      "const": "1"
   191	    },
   192	    "subject_digest": {
   193	      "type": "string",
   194	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   195	    },
   196	    "subject_manifest_digest": {
   197	      "type": [
   198	        "string",
   199	        "null"
   200	      ]
   201	    },
   202	    "subject_ref": {
   203	      "type": "string"
   204	    },
   205	    "subject_schema": {
   206	      "type": [
   207	        "string",
   208	        "null"
   209	      ]
   210	    },
   211	    "validator_code_digest": {
   212	      "type": "string",
   213	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   214	    },
   215	    "validator_id": {
   216	      "type": "string"
   217	    },
   218	    "validator_version": {
   219	      "type": "string"
   220	    }
   221	  },
   222	  "required": [
   223	    "schema_version",
   224	    "artifact_type",
   225	    "evaluation_id",
   226	    "review_request_id",
   227	    "analysis_attempt_ids",
   228	    "subject_schema",
   229	    "subject_ref",
   230	    "subject_digest",
   231	    "subject_manifest_digest",
   232	    "core_sdlc_trace_ref",
   233	    "checks",
   234	    "eligible",
   235	    "blocking_reasons",
   236	    "validator_id",
   237	    "validator_version",
   238	    "validator_code_digest",
   239	    "evaluated_at",
   240	    "digest"
   241	  ],
   242	  "title": "independence_evaluation",
   243	  "type": "object",
   244	  "x-ranex-canonical-producer": "analytical_review",
   245	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   246	  "x-ranex-template": "docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml"
   247	}
FILE schemas/review/review-observation-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-observation-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "analysis_attempt_id": {
     7	      "type": "string"
     8	    },
     9	    "artifact_type": {
    10	      "const": "review_observation"
    11	    },
    12	    "core_sdlc_trace_ref": {
    13	      "type": "string"
    14	    },
    15	    "digest": {
    16	      "type": "string",
    17	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    18	    },
    19	    "findings": {
    20	      "items": {
    21	        "additionalProperties": false,
    22	        "allOf": [
    23	          {
    24	            "if": {
    25	              "properties": {
    26	                "epistemic_status": {
    27	                  "const": "FACT"
    28	                }
    29	              },
    30	              "required": [
    31	                "epistemic_status"
    32	              ]
    33	            },
    34	            "then": {
    35	              "properties": {
    36	                "evidence_refs": {
    37	                  "items": {
    38	                    "minLength": 1,
    39	                    "type": "string"
    40	                  },
    41	                  "minItems": 1
    42	                }
    43	              }
    44	            }
    45	          }
    46	        ],
    47	        "properties": {
    48	          "category": {
    49	            "type": "string"
    50	          },
    51	          "claim": {
    52	            "type": "string"
    53	          },
    54	          "confidence": {
    55	            "type": "string"
    56	          },
    57	          "epistemic_status": {
    58	            "enum": [
    59	              "FACT",
    60	              "INFERENCE",
    61	              "OWNER_REQUIREMENT",
    62	              "PROPOSAL",
    63	              "REPORTED_ADVISORY_RESULT"
    64	            ]
    65	          },
    66	          "evidence_refs": {
    67	            "items": {},
    68	            "type": "array"
    69	          },
    70	          "finding_id": {
    71	            "type": "string"
    72	          },
    73	          "impact": {
    74	            "type": "string"
    75	          },
    76	          "location": {
    77	            "type": "string"
    78	          },
    79	          "owner_ref": {
    80	            "type": [
    81	              "string",
    82	              "null"
    83	            ]
    84	          },
    85	          "reconciliation_ref": {
    86	            "type": [
    87	              "string",
    88	              "null"
    89	            ]
    90	          },
    91	          "required_action": {
    92	            "type": "string"
    93	          },
    94	          "severity": {
    95	            "type": "string"
    96	          },
    97	          "state": {
    98	            "type": "string"
    99	          }
   100	        },
   101	        "required": [
   102	          "finding_id",
   103	          "category",
   104	          "severity",
   105	          "confidence",
   106	          "epistemic_status",
   107	          "location",
   108	          "claim",
   109	          "impact",
   110	          "evidence_refs",
   111	          "required_action",
   112	          "owner_ref",
   113	          "state",
   114	          "reconciliation_ref"
   115	        ],
   116	        "type": "object"
   117	      },
   118	      "type": "array"
   119	    },
   120	    "limitations": {
   121	      "items": {},
   122	      "type": "array"
   123	    },
   124	    "observation_id": {
   125	      "type": "string"
   126	    },
   127	    "proposed_actions": {
   128	      "items": {},
   129	      "type": "array"
   130	    },
   131	    "review_request_id": {
   132	      "type": "string"
   133	    },
   134	    "schema_version": {
   135	      "const": "1"
   136	    },
   137	    "state": {
   138	      "type": "string"
   139	    },
   140	    "subject_digest": {
   141	      "type": "string",
   142	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   143	    },
   144	    "subject_manifest_digest": {
   145	      "type": [
   146	        "string",
   147	        "null"
   148	      ]
   149	    },
   150	    "subject_ref": {
   151	      "type": "string"
   152	    },
   153	    "subject_schema": {
   154	      "type": [
   155	        "string",
   156	        "null"
   157	      ]
   158	    },
   159	    "summary": {
   160	      "type": "string"
   161	    },
   162	    "uncertainties": {
   163	      "items": {},
   164	      "type": "array"
   165	    }
   166	  },
   167	  "required": [
   168	    "schema_version",
   169	    "artifact_type",
   170	    "observation_id",
   171	    "review_request_id",
   172	    "analysis_attempt_id",
   173	    "subject_schema",
   174	    "subject_ref",
   175	    "subject_digest",
   176	    "subject_manifest_digest",
   177	    "core_sdlc_trace_ref",
   178	    "state",
   179	    "summary",
   180	    "findings",
   181	    "uncertainties",
   182	    "limitations",
   183	    "proposed_actions",
   184	    "digest"
   185	  ],
   186	  "title": "review_observation",
   187	  "type": "object",
   188	  "x-ranex-canonical-producer": "analytical_review",
   189	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   190	  "x-ranex-template": "docs/architecture/templates/REVIEW_OBSERVATION.yaml"
   191	}
FILE schemas/review/review-record-projection-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-record-projection-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "analysis_attempt_refs": {
     7	      "items": {},
     8	      "type": "array"
     9	    },
    10	    "artifact_type": {
    11	      "const": "review_record_projection"
    12	    },
    13	    "core_sdlc_trace_ref": {
    14	      "type": "string"
    15	    },
    16	    "digest": {
    17	      "type": "string",
    18	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    19	    },
    20	    "gate_evaluation_ref": {
    21	      "type": [
    22	        "string",
    23	        "null"
    24	      ]
    25	    },
    26	    "generated_at": {
    27	      "type": "string",
    28	      "x-ranex-runtime-format": "date-time"
    29	    },
    30	    "independence_evaluation_digest": {
    31	      "type": "string",
    32	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    33	    },
    34	    "independence_evaluation_id": {
    35	      "type": "string"
    36	    },
    37	    "projection_id": {
    38	      "type": "string"
    39	    },
    40	    "review_observation_refs": {
    41	      "items": {},
    42	      "type": "array"
    43	    },
    44	    "review_request_digest": {
    45	      "type": "string",
    46	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    47	    },
    48	    "review_request_id": {
    49	      "type": "string"
    50	    },
    51	    "review_verdict_digest": {
    52	      "type": "string",
    53	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    54	    },
    55	    "review_verdict_id": {
    56	      "type": "string"
    57	    },
    58	    "schema_version": {
    59	      "const": "1"
    60	    },
    61	    "source_registry_version": {
    62	      "type": "string"
    63	    },
    64	    "subject_digest": {
    65	      "type": "string",
    66	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    67	    },
    68	    "subject_manifest_digest": {
    69	      "type": [
    70	        "string",
    71	        "null"
    72	      ]
    73	    },
    74	    "subject_ref": {
    75	      "type": "string"
    76	    },
    77	    "subject_schema": {
    78	      "type": [
    79	        "string",
    80	        "null"
    81	      ]
    82	    }
    83	  },
    84	  "required": [
    85	    "schema_version",
    86	    "artifact_type",
    87	    "projection_id",
    88	    "subject_schema",
    89	    "subject_ref",
    90	    "subject_digest",
    91	    "subject_manifest_digest",
    92	    "core_sdlc_trace_ref",
    93	    "review_request_id",
    94	    "review_request_digest",
    95	    "analysis_attempt_refs",
    96	    "review_observation_refs",
    97	    "independence_evaluation_id",
    98	    "independence_evaluation_digest",
    99	    "review_verdict_id",
   100	    "review_verdict_digest",
   101	    "gate_evaluation_ref",
   102	    "generated_at",
   103	    "source_registry_version",
   104	    "digest"
   105	  ],
   106	  "title": "review_record_projection",
   107	  "type": "object",
   108	  "x-ranex-canonical-producer": "analytical_review",
   109	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   110	  "x-ranex-template": "docs/architecture/templates/REVIEW_RECORD.yaml"
   111	}
FILE schemas/review/review-request-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-request-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "absolute_deadline": {
     7	      "type": "string",
     8	      "x-ranex-runtime-format": "date-time"
     9	    },
    10	    "artifact_type": {
    11	      "const": "review_request"
    12	    },
    13	    "blind_context_manifest_digest": {
    14	      "type": "string",
    15	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    16	    },
    17	    "core_sdlc_trace_ref": {
    18	      "type": "string"
    19	    },
    20	    "digest": {
    21	      "type": "string",
    22	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    23	    },
    24	    "maker": {
    25	      "additionalProperties": false,
    26	      "properties": {
    27	        "principal_id": {
    28	          "type": "string"
    29	        },
    30	        "role_id": {
    31	          "type": "string"
    32	        },
    33	        "run_id": {
    34	          "type": "string"
    35	        },
    36	        "session_id": {
    37	          "type": "string"
    38	        }
    39	      },
    40	      "required": [
    41	        "principal_id",
    42	        "role_id",
    43	        "run_id",
    44	        "session_id"
    45	      ],
    46	      "type": "object"
    47	    },
    48	    "packet_digest": {
    49	      "type": "string",
    50	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    51	    },
    52	    "packet_id": {
    53	      "type": "string"
    54	    },
    55	    "prohibited_capabilities": {
    56	      "items": {
    57	        "type": "string"
    58	      },
    59	      "type": "array"
    60	    },
    61	    "qualification_policy_id": {
    62	      "type": "string"
    63	    },
    64	    "request_id": {
    65	      "type": "string"
    66	    },
    67	    "required_independence": {
    68	      "items": {},
    69	      "type": "array"
    70	    },
    71	    "required_reviewer_role_id": {
    72	      "type": "string"
    73	    },
    74	    "required_route_fact_diversity": {
    75	      "items": {},
    76	      "type": "array"
    77	    },
    78	    "review_spec_id": {
    79	      "type": "string"
    80	    },
    81	    "review_spec_version": {
    82	      "type": "string"
    83	    },
    84	    "schema_version": {
    85	      "const": "1"
    86	    },
    87	    "subject_digest": {
    88	      "type": "string",
    89	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    90	    },
    91	    "subject_manifest_digest": {
    92	      "type": [
    93	        "string",
    94	        "null"
    95	      ]
    96	    },
    97	    "subject_ref": {
    98	      "type": "string"
    99	    },
   100	    "subject_schema": {
   101	      "type": [
   102	        "string",
   103	        "null"
   104	      ]
   105	    }
   106	  },
   107	  "required": [
   108	    "schema_version",
   109	    "artifact_type",
   110	    "request_id",
   111	    "review_spec_id",
   112	    "review_spec_version",
   113	    "packet_id",
   114	    "packet_digest",
   115	    "subject_schema",
   116	    "subject_ref",
   117	    "subject_digest",
   118	    "subject_manifest_digest",
   119	    "core_sdlc_trace_ref",
   120	    "maker",
   121	    "required_reviewer_role_id",
   122	    "required_independence",
   123	    "prohibited_capabilities",
   124	    "blind_context_manifest_digest",
   125	    "required_route_fact_diversity",
   126	    "qualification_policy_id",
   127	    "absolute_deadline",
   128	    "digest"
   129	  ],
   130	  "title": "review_request",
   131	  "type": "object",
   132	  "x-ranex-canonical-producer": "analytical_review",
   133	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   134	  "x-ranex-template": "docs/architecture/templates/REVIEW_REQUEST.yaml"
   135	}
FILE schemas/review/review-verdict-v1.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-verdict-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "artifact_type": {
     7	      "const": "review_verdict"
     8	    },
     9	    "core_sdlc_trace_ref": {
    10	      "type": "string"
    11	    },
    12	    "digest": {
    13	      "type": "string",
    14	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    15	    },
    16	    "evidence_refs": {
    17	      "items": {},
    18	      "type": "array"
    19	    },
    20	    "independence_evaluation_id": {
    21	      "type": "string"
    22	    },
    23	    "limitations": {
    24	      "items": {},
    25	      "type": "array"
    26	    },
    27	    "observation_ids": {
    28	      "items": {},
    29	      "type": "array"
    30	    },
    31	    "open_finding_refs": {
    32	      "items": {},
    33	      "type": "array"
    34	    },
    35	    "produced_at": {
    36	      "type": "string",
    37	      "x-ranex-runtime-format": "date-time"
    38	    },
    39	    "producer_service_id": {
    40	      "type": "string"
    41	    },
    42	    "reconciliation_refs": {
    43	      "items": {},
    44	      "type": "array"
    45	    },
    46	    "resolved_finding_refs": {
    47	      "items": {},
    48	      "type": "array"
    49	    },
    50	    "review_request_id": {
    51	      "type": "string"
    52	    },
    53	    "schema_version": {
    54	      "const": "1"
    55	    },
    56	    "subject_digest": {
    57	      "type": "string",
    58	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    59	    },
    60	    "subject_manifest_digest": {
    61	      "type": [
    62	        "string",
    63	        "null"
    64	      ]
    65	    },
    66	    "subject_ref": {
    67	      "type": "string"
    68	    },
    69	    "subject_schema": {
    70	      "type": [
    71	        "string",
    72	        "null"
    73	      ]
    74	    },
    75	    "verdict": {
    76	      "type": "string"
    77	    },
    78	    "verdict_id": {
    79	      "type": "string"
    80	    }
    81	  },
    82	  "required": [
    83	    "schema_version",
    84	    "artifact_type",
    85	    "verdict_id",
    86	    "review_request_id",
    87	    "observation_ids",
    88	    "independence_evaluation_id",
    89	    "subject_schema",
    90	    "subject_ref",
    91	    "subject_digest",
    92	    "subject_manifest_digest",
    93	    "core_sdlc_trace_ref",
    94	    "verdict",
    95	    "open_finding_refs",
    96	    "resolved_finding_refs",
    97	    "reconciliation_refs",
    98	    "evidence_refs",
    99	    "limitations",
   100	    "producer_service_id",
   101	    "produced_at",
   102	    "digest"
   103	  ],
   104	  "title": "review_verdict",
   105	  "type": "object",
   106	  "x-ranex-canonical-producer": "analytical_review",
   107	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   108	  "x-ranex-template": "docs/architecture/templates/REVIEW_VERDICT.yaml"
   109	}
FILE schemas/common/evidence-ref.schema.json
     1	{
     2	  "$id": "https://schemas.ranex.dev/common/evidence-ref.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "evidence_digest": {
     7	      "pattern": "^sha256:[0-9a-f]{64}$",
     8	      "type": "string"
     9	    },
    10	    "evidence_ref": {
    11	      "minLength": 1,
    12	      "type": "string"
    13	    }
    14	  },
    15	  "required": [
    16	    "evidence_ref",
    17	    "evidence_digest"
    18	  ],
    19	  "type": "object"
    20	}
FILE docs/architecture/templates/REVIEW_OBSERVATION.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	schema_version: "1"
     3	artifact_type: review_observation
     4	observation_id: "observation_<uuidv7>"
     5	review_request_id: "review_<uuidv7>"
     6	analysis_attempt_id: "attempt_<uuidv7>"
     7	subject_schema: null
     8	subject_ref: ""
     9	subject_digest: ""
    10	subject_manifest_digest: null
    11	core_sdlc_trace_ref: ""
    12	state: EVALUATION_INCOMPLETE
    13	summary: ""
    14	findings:
    15	  - finding_id: "finding_<uuidv7>"
    16	    category: ""
    17	    severity: ""
    18	    confidence: ""
    19	    epistemic_status: INFERENCE
    20	    location: ""
    21	    claim: ""
    22	    impact: ""
    23	    evidence_refs: []
    24	    required_action: ""
    25	    owner_ref: null
    26	    state: OPEN
    27	    reconciliation_ref: null
    28	uncertainties: []
    29	limitations: []
    30	proposed_actions: []
    31	digest: ""
FILE docs/architecture/templates/REVIEW_VERDICT.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	# Produced by the review application service after independence validation.
     3	schema_version: "1"
     4	artifact_type: review_verdict
     5	verdict_id: "verdict_<uuidv7>"
     6	review_request_id: "review_<uuidv7>"
     7	observation_ids: []
     8	independence_evaluation_id: "independence_<uuidv7>"
     9	subject_schema: null
    10	subject_ref: ""
    11	subject_digest: ""
    12	subject_manifest_digest: null
    13	core_sdlc_trace_ref: ""
    14	verdict: INCOMPLETE
    15	open_finding_refs: []
    16	resolved_finding_refs: []
    17	reconciliation_refs: []
    18	evidence_refs: []
    19	limitations: []
    20	producer_service_id: ""
    21	produced_at: ""
    22	digest: ""
    23	# This is not GateOutcome and cannot authorize a transition.
FILE docs/architecture/templates/REVIEW_REQUEST.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	schema_version: "1"
     3	artifact_type: review_request
     4	request_id: "review_<uuidv7>"
     5	
     6	review_spec_id: ""
     7	review_spec_version: ""
     8	packet_id: ""
     9	packet_digest: ""
    10	subject_schema: null
    11	subject_ref: ""
    12	subject_digest: ""
    13	subject_manifest_digest: null
    14	core_sdlc_trace_ref: ""
    15	
    16	maker:
    17	  principal_id: ""
    18	  role_id: implementation-worker
    19	  run_id: ""
    20	  session_id: ""
    21	
    22	required_reviewer_role_id: ""
    23	required_independence: []
    24	prohibited_capabilities: [write, merge, release, permit_issue]
    25	blind_context_manifest_digest: ""
    26	required_route_fact_diversity: []
    27	qualification_policy_id: ""
    28	absolute_deadline: ""
    29	digest: ""
FILE docs/architecture/templates/ANALYSIS_ATTEMPT.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	schema_version: "1"
     3	artifact_type: analysis_attempt
     4	attempt_id: "attempt_<uuidv7>"
     5	review_request_id: "review_<uuidv7>"
     6	previous_attempt_id: null
     7	subject_schema: null
     8	subject_ref: ""
     9	subject_digest: ""
    10	subject_manifest_digest: null
    11	core_sdlc_trace_ref: ""
    12	
    13	reviewer:
    14	  principal_id: ""
    15	  role_id: ""
    16	  session_id: ""
    17	
    18	route:
    19	  route_lock_id: ""
    20	  actual_provider_id: ""
    21	  actual_model_id: ""
    22	  actual_model_snapshot: null
    23	  transport_id: ""
    24	  transport_digest: ""
    25	  executable_digest: ""
    26	  parser_version: ""
    27	  isolation_profile_id: ""
    28	
    29	input_artifact_refs: []
    30	input_manifest_digest: ""
    31	granted_capabilities: []
    32	write_attempt_evidence_refs: []
    33	started_at: ""
    34	finished_at: ""
    35	absolute_deadline: ""
    36	status: null
    37	failure_domain: null
    38	retry_class: null
    39	usage: {}
    40	raw_output_artifact_ref: ""
    41	raw_output_digest: ""
    42	digest: ""
FILE docs/architecture/templates/INDEPENDENCE_EVALUATION.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	# Produced by deterministic independence validation, never by the reviewer.
     3	schema_version: "1"
     4	artifact_type: independence_evaluation
     5	evaluation_id: "independence_<uuidv7>"
     6	review_request_id: "review_<uuidv7>"
     7	analysis_attempt_ids: []
     8	subject_schema: null
     9	subject_ref: ""
    10	subject_digest: ""
    11	subject_manifest_digest: null
    12	core_sdlc_trace_ref: ""
    13	
    14	checks:
    15	  maker_reviewer_identity_separated:
    16	    outcome: UNKNOWN
    17	    evidence_refs: []
    18	  maker_reviewer_session_separated:
    19	    outcome: UNKNOWN
    20	    evidence_refs: []
    21	  subject_exact:
    22	    outcome: UNKNOWN
    23	    evidence_refs: []
    24	  reviewer_did_not_mutate_subject:
    25	    outcome: UNKNOWN
    26	    evidence_refs: []
    27	  reviewer_had_no_write_or_authority_capability:
    28	    outcome: UNKNOWN
    29	    evidence_refs: []
    30	  blind_context_satisfied:
    31	    outcome: UNKNOWN
    32	    evidence_refs: []
    33	  route_fact_diversity_satisfied:
    34	    outcome: UNKNOWN
    35	    evidence_refs: []
    36	  hidden_verification_withheld:
    37	    outcome: UNKNOWN
    38	    evidence_refs: []
    39	
    40	eligible: false
    41	blocking_reasons: []
    42	validator_id: ""
    43	validator_version: ""
    44	validator_code_digest: ""
    45	evaluated_at: ""
    46	digest: ""
FILE docs/architecture/templates/REVIEW_RECORD.yaml
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	# Generated read projection only. The five referenced records are immutable
     3	# authority/evidence sources and must not be replaced by this bundle.
     4	schema_version: "1"
     5	artifact_type: review_record_projection
     6	projection_id: "review_projection_<uuidv7>"
     7	subject_schema: null
     8	subject_ref: ""
     9	subject_digest: ""
    10	subject_manifest_digest: null
    11	core_sdlc_trace_ref: ""
    12	
    13	review_request_id: "review_<uuidv7>"
    14	review_request_digest: ""
    15	analysis_attempt_refs: []
    16	review_observation_refs: []
    17	independence_evaluation_id: "independence_<uuidv7>"
    18	independence_evaluation_digest: ""
    19	review_verdict_id: "verdict_<uuidv7>"
    20	review_verdict_digest: ""
    21	gate_evaluation_ref: null
    22	
    23	generated_at: ""
    24	source_registry_version: ""
    25	digest: ""
FILE LICENSE-RANEX.md
     1	# Ranex Personal-Use Source License 1.0
     2	
     3	Copyright (c) 2026 Anthony Garces. All rights reserved.
     4	
     5	This is a source-available license. It is not an open-source license.
     6	
     7	## 1. Scope
     8	
     9	This license applies only to original Ranex code, documentation, configuration,
    10	artwork, and modifications owned by Anthony Garces (the "Ranex Material").
    11	
    12	It does not apply to Hermes Agent material or any other third-party material.
    13	Those portions remain governed by their own licenses. When Hermes Agent
    14	material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
    15	
    16	## 2. Personal-use permission
    17	
    18	Subject to every condition below, an individual may view, copy, run, study, and
    19	privately modify the Ranex Material solely for personal learning,
    20	experimentation, or evaluation.
    21	
    22	This permission is personal, limited, non-exclusive, and non-transferable. All
    23	copyright, license, attribution, and source notices must remain intact.
    24	
    25	## 3. Restrictions
    26	
    27	Except for the limited GitHub-platform rights in section 4, and unless Anthony
    28	Garces gives prior written permission, you may not:
    29	
    30	1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
    31	   or otherwise provide the Ranex Material or a modified version to anyone;
    32	2. make the Ranex Material available through a public or shared repository,
    33	   download, package, service, hosted application, network endpoint, or device;
    34	3. use the Ranex Material for any commercial, business, employment,
    35	   professional, institutional, revenue-generating, or client purpose;
    36	4. use the Ranex Material to operate, support, develop, or improve a product,
    37	   service, organization, or business process;
    38	5. remove, hide, or alter a copyright, license, provenance, or attribution
    39	   notice;
    40	6. claim authorship or ownership of Ranex Material created by Anthony Garces,
    41	   or present that material as your own work;
    42	7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
    43	   ownership; or
    44	8. grant another person rights that this license does not grant to you.
    45	
    46	You may identify original changes that you created privately, but that does not
    47	give you ownership of the underlying Ranex Material or permission to
    48	redistribute the combined work.
    49	
    50	## 4. Public GitHub repository
    51	
    52	While the repository is public, GitHub's Terms of Service grant GitHub users
    53	limited permission to use, display, perform, and reproduce repository content
    54	through GitHub's service as its features allow, including by forking it. This
    55	license does not restrict those platform rights.
    56	
    57	Those platform permissions do not grant permission to redistribute the Ranex
    58	Material outside GitHub's service, use it for business, remove its notices, or
    59	claim it as your own.
    60	
    61	## 5. Ownership and third-party rights
    62	
    63	The Ranex Material is licensed, not sold. Anthony Garces retains all rights
    64	not expressly granted here.
    65	
    66	No term in this license reduces a right granted directly by the MIT License or
    67	another applicable third-party license. When a file contains both upstream
    68	material and original Ranex modifications, each portion remains governed by
    69	its applicable license.
    70	
    71	## 6. Termination
    72	
    73	Your permission under this license ends automatically when you violate it.
    74	After termination, you must stop using the Ranex Material and delete copies in
    75	your possession or control, except copies GitHub retains under its Terms of
    76	Service or copies the law requires you to preserve.
    77	
    78	## 7. No warranty
    79	
    80	THE RANEX MATERIAL IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    81	OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
    82	PURPOSE, TITLE, AND NON-INFRINGEMENT.
    83	
    84	TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
    85	FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE RANEX MATERIAL OR
    86	ITS USE.
    87	
    88	## 8. Other rights
    89	
    90	This license does not limit fair use, fair dealing, or another right that
    91	applicable law does not allow a license to restrict.
    92	
    93	For redistribution, business use, sublicensing, or another exception, obtain
    94	prior written permission from Anthony Garces through the `anthonykewl20`
    95	GitHub account.

exec
/bin/bash -lc 'rg -n "finding|verdict|observation|epistemic|evidence|review request|analysis attempt|independen|projection|lifecycle|FACT|INFERENCE|PASS|FAIL|INCOMPLETE|OPEN|RESOLVED|RECONCIL" docs/architecture/AI_ARTIFACT_CONTRACTS.md | head -n 260' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
5:| Specification ID | `SPEC-AI-ARTIFACTS-001` |
17:| Security/data class | Public specification metadata; artifact instances are classified independently |
35:`AI-G2: PASS`. That gate additionally requires the exact-revision validation
37:evidence, and authenticated human acceptance.
54:   or a redacted projection to recompute the canonical digest.
58:and evidence identity. Empty string is not a substitute for absent/unknown;
59:required unknown facts use the typed epistemic state.
75:| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
76:| Review-record projection | `review_projection_` |
77:| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
81:| Post-landing / release / operation / outcome evidence | `postlanding_`, `release_evidence_`, `operation_evidence_`, `outcome_review_` |
84:| Capability assessment / domain projection | `capability_assessment_`, `capability_domain_projection_` |
96:- observation, finding, review-verdict, checker, gate, decision, grant, permit,
134:signal_evidence_digest: sha256:<hex>
146:Every evidence, decision, gate, permit, run, review, and effect contract embeds
185:rule set, instruction-registry version, applicability evidence, conflicts,
204:- requires reason/evidence for non-applicability;
213:quotation is not verification evidence.
299:Every intake, task, run, review, gate, capability assessment/domain projection,
304:WorkItemStatus at dispatch/observation
313:Definition-of-Ready evidence snapshot
314:requirement/criterion -> checker/evidence links
342:| `ArchitectureReconciliation` | Synthesizer plus finding records | Resolve proposal/challenge against evidence | Human ADR decision |
352:| `CapabilityDomainProjection` | `process_assurance` deterministic projection service under accountable assessor/approver roles | Bind the exact registered control-tuple set for one domain/scope/window and derive result, lowest supported level, and highest-precedence priority | Author a member assessment, omit/duplicate/remap a registry tuple, arithmetically aggregate levels, or authorize a transition |
353:| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
354:| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
355:| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
356:| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
358:| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
359:| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
362:| `EvidenceSnapshot` | Assurance service | Freeze exact eligible evidence set | Decision by itself |
370:| `OperationEvidence` | Operations/service evidence ingestion | Health/support/recovery facts | Product outcome |
398:`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
404:`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
405:`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
411:A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
415:reason, accountable owner, and evidence reference.
422:## 8. Finding lifecycle
424:Every finding has category, severity, confidence/epistemic status, exact
425:location, claim, impact, evidence, required action, owner, and state:
428:OPEN
433:OPEN
439:Only the review/finding application service changes finding state. A maker may
440:submit a resolution proposal but cannot mark its finding verified.
447:eligible evidence
458:coverage, conflicting/missing evidence, exact subject, evaluator code digest,
483:## 11. Command and test evidence
499:`AgentHandoff` references immutable `RunResult`, test, evidence, finding, and
500:artifact IDs. Any human-readable duplication is a generated projection and must
526:│   ├── evidence-ref.schema.json
536:│   └── capability-domain-projection-v1.schema.json
549:│   ├── review-observation-v1.schema.json
550:│   ├── independence-evaluation-v1.schema.json
551:│   ├── review-verdict-v1.schema.json
552:│   └── review-record-projection-v1.schema.json
555:│   ├── evidence-snapshot-v1.schema.json
570:└── lifecycle/
571:    ├── release-evidence-v1.schema.json
572:    ├── operation-evidence-v1.schema.json
579:identifier, evidence-reference, engineering-practice-profile,
627:  nine ADR-0009 fitness obligations are exact-set projections;
632:  current behavioral evidence exists;
635:  behavioral evidence remain `UNKNOWN`/`NOT_ASSESSED`;
643:  retry-to-pass, incomplete deletion, and unbound production evidence.
661:  subject evidence bridge, with no stale output, denominator, or conflict;
662:- a clean, committed, upstream-derived `SDLC-FORK-000: PASS` subject;
666:  no unresolved P0/P1 finding; and
672:evidence; it cannot implement product capability or activate product runtime.
682:- hidden-fixture isolation and review independence through a real harness;
687:  capability-assessment evidence; and
689:  production-readiness evidence.

exec
/bin/bash -lc "nl -ba docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n '1,115p;120,225p;285,465p;475,515p;575,605p;650,700p'
printf '--- record schema ---\\n'
nl -ba schemas/review/review-record-projection-v1.schema.json
printf '--- templates origin generator refs ---\\n'
rg -n \"template|generated|schema\" scripts/architecture/generate_contracts.py scripts/architecture/README.md | head -n 120
printf '--- ledger ---\\n'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	# Ranex AI-Work Artifact Contract Specification
     2	
     3	| Field | Value |
     4	|---|---|
     5	| Specification ID | `SPEC-AI-ARTIFACTS-001` |
     6	| Version | `1.3.0` |
     7	| Status | Normative executable documentation-contract baseline; runtime producer enforcement is `NOT_ASSESSED` and human `AI-G2` acceptance is pending |
     8	| Owner | Human governor |
     9	| Effective date | 2026-07-27 |
    10	| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
    11	| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
    12	| Worker protocol | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
    13	| Fleet control | [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md) |
    14	| Architecture | [Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
    15	| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md); [ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md) |
    16	| Compatibility/migration class | New contract family; later breaking changes require upcasters and compatibility fixtures |
    17	| Security/data class | Public specification metadata; artifact instances are classified independently |
    18	| Review trigger | `AI-G2`, schema/canonicalization change, or any artifact-authority change |
    19	
    20	## 1. Standing
    21	
    22	This document specifies the complete artifact family used to drive and verify
    23	AI workers inside the established Core SDLC. It defines target fields,
    24	producers, authority boundaries, canonicalization, and schema locations.
    25	
    26	Files under [`templates/`](./templates/) are reviewable authoring skeletons.
    27	Their executable JSON Schemas are registered under
    28	[`../../schemas/`](../../schemas/), canonical vocabularies are registered under
    29	[`../../architecture/contracts/`](../../architecture/contracts/), and
    30	`scripts/architecture/validate_contracts.py` validates them together with
    31	canonicalization, forgery, reuse, and subject-binding fixtures. Empty authoring
    32	placeholders remain invalid for a sealed runtime artifact.
    33	
    34	This executable documentation-contract baseline does not by itself establish
    35	`AI-G2: PASS`. That gate additionally requires the exact-revision validation
    36	report, generated consumer packages, qualified runtime producers, isolation
    37	evidence, and authenticated human acceptance.
    38	
    39	## 2. Canonical encoding and digest
    40	
    41	The contract registry declares one canonical wire representation:
    42	
    43	1. accept JSON or YAML only at an ingress adapter;
    44	2. parse with duplicate-key rejection and schema-selected scalar types;
    45	3. normalize to the versioned JSON data model;
    46	4. reject unknown fields unless that schema version explicitly reserves them;
    47	5. encode using RFC 8785 JSON Canonicalization Scheme;
    48	6. compute SHA-256 over the UTF-8 canonical bytes with the top-level `digest`
    49	   field absent;
    50	7. serialize `digest` as `sha256:<64 lowercase hex>`;
    51	8. preserve the original submitted bytes as a separate artifact when required;
    52	   and
    53	9. never use display YAML bytes, map insertion order, local paths, timestamps,
    54	   or a redacted projection to recompute the canonical digest.
    55	
    56	Times are RFC 3339 UTC with explicit `Z`. Durations and budgets are integer
    57	base units declared by schema. Floating-point values are forbidden in authority
    58	and evidence identity. Empty string is not a substitute for absent/unknown;
    59	required unknown facts use the typed epistemic state.
    60	
    61	## 3. Shared identifiers and vocabulary
    62	
    63	All generated identifiers use the prefixes registered in `identities.yaml`.
    64	Minimum prefixes include:
    65	
    66	| Type | Prefix |
    67	|---|---|
    68	| Repository | `repo_` |
    69	| Project / work / run / activity / effect | `prj_`, `work_`, `run_`, `act_`, `eff_` |
    70	| Workspace / packet / intake / research | `wsp_`, `pkt_`, `intake_`, `research_` |
    71	| Requirement / criterion / outcome measure | `req_`, `criterion_`, `measure_` |
    72	| Core-SDLC trace block | `trace_` |
    73	| Evidence / snapshot / artifact / checker result | `evd_`, `snapshot_`, `art_`, `check_` |
    74	| Architecture review packet / proposal / reconciliation | `archpkt_`, `proposal_`, `archreconcile_` |
    75	| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
    76	| Review-record projection | `review_projection_` |
    77	| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
    78	| Decision / authority grant / permit / gate | `dec_`, `grant_`, `permit_`, `gate_` |
    79	| Handoff / result / landing / transition | `handoff_`, `result_`, `landing_`, `transition_` |
    80	| Release / incident / service / capability | `release_`, `incident_`, `svc_`, `cap_` |
    81	| Post-landing / release / operation / outcome evidence | `postlanding_`, `release_evidence_`, `operation_evidence_`, `outcome_review_` |
    82	| Assignment / offer / worker attempt / lease / mailbox | `assignment_`, `offer_`, `wattempt_`, `lease_`, `message_` |
    83	| Resource reservation / fleet experiment | `reservation_`, `fleetexp_` |
    84	| Capability assessment / domain projection | `capability_assessment_`, `capability_domain_projection_` |
    85	
    86	Canonical enum values are uppercase. Lowercase values in display examples are
    87	invalid after `AI-G2`. The authoritative registries own:
    88	
    89	- `WorkItemStatus`, `WorkClass`, `RiskLane`, `RunStatus`, `ActivityStatus`,
    90	  `IntakeStatus`, `PacketStatus`, `AssignmentStatus`, `DispatchOfferStatus`,
    91	  `LeaseStatus`, `MailboxDeliveryStatus`, `ReservationStatus`,
    92	  `FleetExperimentStatus`, `CapabilityAssessmentStatus`, `EffectStatus`, and
    93	  `ReconciliationStatus`;
    94	- `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, `ModuleStatus`,
    95	  `RouteStatus`, `ExtensionStatus`, and `CompatibilityStatus`;
    96	- observation, finding, review-verdict, checker, gate, decision, grant, permit,
    97	  artifact, migration, sync, update, and cutover states;
    98	- role IDs and incompatible-role combinations; and
    99	- `SDLC-*`, `AI-G*`, `MAP-*`, and `SDLC-ADOPT-*` gate namespaces.
   100	
   101	## 4. Subject binding
   102	
   103	A child artifact either embeds one full discriminated subject or references one
   104	through `SubjectBindingV1`:
   105	
   106	```yaml
   107	subject_schema: work-subject/v1 # or exact/architecture/research/resource subject
   108	subject_ref: art_<uuidv7>
   109	subject_digest: sha256:<hex>
   110	subject_manifest_digest: null
   111	```
   112	
   113	`subject_schema` selects the conditional subject contract. `subject_ref`
   114	identifies the immutable stored subject; it is never overloaded with the schema
   115	ID. `subject_digest` binds the canonical subject bytes.
   120	
   121	### 4.1 `WorkSubjectV1`
   122	
   123	Core-SDLC work exists before an execution run, workspace, or task packet.
   124	Intake, definition, and design may therefore bind:
   125	
   126	```yaml
   127	subject_schema: work-subject/v1
   128	project_id: prj_<uuidv7>
   129	work_item_id: work_<uuidv7>
   130	repository_id: repo_<uuidv7>
   131	repository_uri_digest: sha256:<hex>
   132	base_revision: <40-hex>
   133	work_baseline_manifest_digest: sha256:<hex>
   134	signal_evidence_digest: sha256:<hex>
   135	requirements_baseline_digest: null
   136	design_baseline_digest: null
   137	observed_at: <RFC3339>
   138	```
   139	
   140	The subject advances only through an owned Core-SDLC transition or baseline
   141	change. A later execution subject references the same project/work item and
   142	the accepted baselines; it does not erase this earlier work identity.
   143	
   144	### 4.2 `ExactSubjectV1`
   145	
   146	Every evidence, decision, gate, permit, run, review, and effect contract embeds
   147	or references one immutable subject:
   148	
   149	```yaml
   150	subject_schema: exact-subject/v1
   151	project_id: prj_<uuidv7>
   152	work_item_id: work_<uuidv7>
   153	run_id: run_<uuidv7>
   154	activity_id: null
   155	effect_id: null
   156	workspace_id: wsp_<uuidv7>
   157	repository_id: repo_<uuidv7>
   158	repository_uri_digest: sha256:<hex>
   159	base_commit: <40-hex>
   160	candidate_commit: <40-hex-or-null>
   161	artifact_digest: null
   162	packet_id: pkt_<uuidv7>
   163	packet_digest: sha256:<hex>
   164	workflow_definition_id: <stable-id>
   165	workflow_definition_digest: sha256:<hex>
   166	workflow_interpreter_version: <semver-or-content-id>
   167	policy_activation_id: <stable-id>
   168	policy_activation_manifest_digest: sha256:<hex>
   169	policy_decision_digest: sha256:<hex>
   170	module_profile_id: <stable-id>
   171	module_profile_digest: sha256:<hex>
   172	capability_grant_digest: sha256:<hex>
   173	route_lock_id: route_<uuidv7-or-null>
   174	schema_registry_version: <immutable-version>
   175	expected_run_aggregate_version: <nonnegative-integer>
   176	```
   177	
   178	The schema uses conditional requirements. An architecture/process decision may
   179	bind a normative artifact revision/digest instead of a run/activity/effect; an
   180	effect permit requires all effect fields. A `TaskPacket` omits its own
   181	`packet_id`/`packet_digest` from the embedded subject to avoid a recursive hash;
   182	its top-level ID and digest become required in every downstream subject.
   183	Adapters cannot silently fill an inapplicable field with an empty string.
   184	`policy_activation_manifest_digest` binds the deterministic included/excluded
   185	rule set, instruction-registry version, applicability evidence, conflicts,
   186	enforcement classes, resolution requirements, and context budget compiled for
   187	the subject. It is not a prompt receipt. The exact subject is the sole field
   188	home for activation ID/digest; a task packet embeds the manifest components in
   189	its authority block, and the semantic validator canonicalizes that block and
   190	requires its hash to equal the subject digest before `SEALED`. Any material
   191	rule, scope, project, role, stage, technology, risk, task, trigger, or budget
   192	change invalidates the packet and every downstream subject.
   193	
   194	#### 4.2.1 `EngineeringPracticeProfileV1`
   195	
   196	Every `TaskPacket` embeds one immutable engineering-practice profile compiled
   197	from the exact `engineering-practices.json` registry and
   198	Engineering Reference Application Map revision. The profile:
   199	
   200	- binds the registry version/digest and application-map revision/digest;
   201	- evaluates all ten registered source families as `APPLICABLE`,
   202	  `NOT_APPLICABLE`, or `UNKNOWN`;
   203	- binds applicable practice IDs to required behavior and verification refs;
   204	- requires reason/evidence for non-applicability;
   205	- records deliberate deviations with consequence and decision reference;
   206	- blocks sealing when a material applicability decision is `UNKNOWN`; and
   207	- has its own canonical digest included in the task-packet digest.
   208	
   209	The semantic validator requires exactly one source-coverage entry for each
   210	registered source-family ID and rejects missing, duplicate, unknown, or
   211	unregistered IDs. The profile carries public-safe Ranex synthesis and stable
   212	locators, never unauthorized full-text book content. A practice label or
   213	quotation is not verification evidence.
   214	
   215	### 4.3 `ArchitectureSubjectV1`
   216	
   217	Architecture/process review is bound to an explicit normative subject rather
   218	than overloading a runtime `Run` tuple:
   219	
   220	```yaml
   221	subject_schema: architecture-subject/v1
   222	project_id: prj_<uuidv7>
   223	work_item_id: work_<uuidv7>
   224	repository_id: repo_<uuidv7>
   225	repository_uri_digest: sha256:<hex>
   285	base_revision: <40-hex>
   286	scope_manifest_digest: sha256:<hex>
   287	parent_subject_ref: null
   288	parent_subject_digest: null
   289	```
   290	
   291	The executable schema requires the IDs implied by `scope_kind`, forbids
   292	lower-level IDs at a higher-level root, and requires the immediate parent
   293	subject for every non-root scope. A `CoreSDLCTrace` is required from
   294	`WORK_ITEM` downward and is `null` only for a legitimate `PROJECT` or
   295	`RELEASE` root. This subject carries no authority by itself.
   296	
   297	## 5. Core-SDLC trace block
   298	
   299	Every intake, task, run, review, gate, capability assessment/domain projection,
   300	landing, release, operation, and outcome record embeds or content-addresses one
   301	immutable `CoreSDLCTraceV1`:
   302	
   303	```text
   304	WorkItemStatus at dispatch/observation
   305	WorkClass
   306	RiskLane + risk decision reference/digest
   307	product, technical, service, security/data, delivery, V&V,
   308	  configuration, supplier and release owner references as applicable
   309	outcome-measure IDs
   310	requirement IDs
   311	acceptance-criterion IDs
   312	configuration baseline ID/digest
   313	Definition-of-Ready evidence snapshot
   314	requirement/criterion -> checker/evidence links
   315	invalidation dependency IDs
   316	```
   317	
   318	The trace binds a discriminated subject reference: `work-subject/v1`,
   319	`exact-subject/v1`, `architecture-subject/v1`, `research-subject/v1`, or a
   320	`resource-subject/v1` whose scope is `WORK_ITEM` or lower. Its subject digest
   321	and, when the variant has one, subject-manifest digest must match the child
   322	record. A resource trace's `WorkItemId` must match the resource subject.
   323	Project/release root reservations have no Core trace. An architecture or
   324	process trace is therefore not forced into a fake runtime run/activity tuple.
   325	
   326	These are references, not duplicate product/work authority. A changed source
   327	marks dependent artifacts stale through `invalidation-graph.yaml`.
   328	If a child artifact uses `core_sdlc_trace_ref` instead of embedding the block,
   329	the referenced trace digest is part of the child's canonical digest and must
   330	bind the same `WorkItemId` and exact subject. Empty or mismatched references
   331	fail closed.
   332	
   333	## 6. Artifact family and producer authority
   334	
   335	| Artifact | Canonical producer | Purpose | Cannot authorize |
   336	|---|---|---|---|
   337	| `CoreSDLCTrace` | `configuration_management` traceability compiler | Content-address the accepted project/work/control/requirement/criterion/baseline and exact-subject bindings reused by child artifacts | Mutate its sources, change `WorkItemStatus`, lower risk, or authorize work/effects |
   338	| `WorkIntake` | Work-intake service under duty/product owner | Capture signal and initial facts | Priority, lower risk, dispatch |
   339	| `ResearchPacket` | Research activity | Bind sources, claims, contradictions, unknowns | Architecture/product decision |
   340	| `ArchitectureReviewPacket` | Packet compiler | Freeze exact design-review subject | Acceptance |
   341	| `ArchitectureProposal` | Specialist worker | Proposed boundaries/tree/trade-offs | Its own acceptance |
   342	| `ArchitectureReconciliation` | Synthesizer plus finding records | Resolve proposal/challenge against evidence | Human ADR decision |
   343	| `TaskPacket` | Deterministic packet compiler | Authorize one bounded worker run and bind its exact engineering-practice application profile | Expanded scope, book-derived authority, or merge/release |
   344	| `AgentAssignment` | `agent_collaboration` | Bind eligible packet, role, workspace, topology, reservation, and deadline | Work/run transition or claim |
   345	| `DispatchOffer` | `agent_collaboration` offer service | Bind one expiring eligibility invitation to an assignment, optional named principal, and immutable eligibility policy | Grant authority or claim an assignment outside atomic claim |
   346	| `WorkerAttempt` | `agent_collaboration` attempt service | Bind one principal/session/route/harness/workspace/lease epoch to one assignment and immutable result lineage | Work/run transition, retry policy, or broader lease |
   347	| `WorkerLease` | `agent_collaboration` atomic claim service | Time-bound one attempt with fencing epoch | Broader scope or authority |
   348	| `MailboxEnvelope` | `agent_collaboration` mailbox service | Durable typed coordination reference | Recipient command acceptance or authority |
   349	| `FleetExperiment` | `process_assurance` | Predeclare and retain fleet/control measurement | Change active topology/policy by itself |
   350	| `ResourceReservation` | `resource_governance` | Bind hierarchical admitted limits and settled usage to an exact subject | Authorize an effect, exceed an ancestor, or declare work complete |
   351	| `CapabilityAssessment` | `process_assurance` under accountable assessor/approver roles | Diagnose one exact capability/control scope with separate level, effectiveness, coverage, confidence, and improvement priority | Authorize a transition, average away a vital-control failure, or rank people |
   352	| `CapabilityDomainProjection` | `process_assurance` deterministic projection service under accountable assessor/approver roles | Bind the exact registered control-tuple set for one domain/scope/window and derive result, lowest supported level, and highest-precedence priority | Author a member assessment, omit/duplicate/remap a registry tuple, arithmetically aggregate levels, or authorize a transition |
   353	| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
   354	| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
   355	| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
   356	| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
   357	| `ReviewObservation` | Reviewer/model normalization | Findings, uncertainty, limitations | Gate outcome |
   358	| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
   359	| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
   360	| `ReviewRecordProjection` | Projection builder | Read model joining immutable review records for navigation | Replace or mutate its source records |
   361	| `CheckerResult` | Qualified deterministic checker wrapper | One reproducible check outcome | Aggregate gate alone |
   362	| `EvidenceSnapshot` | Assurance service | Freeze exact eligible evidence set | Decision by itself |
   363	| `GateEvaluation` | Qualified gate evaluator | Produce runtime `GateOutcome` | Human decision |
   364	| `HumanDecisionRecord` | Policy after IAM authentication | Record accountable human choice | Direct effect execution |
   365	| `ConsumableAuthorityGrant` | Governed execution | One-shot eligible decision snapshot | Broader/different action |
   366	| `Permit` | Governed execution after gate/decision | One-shot exact effect/transition capability | Another subject/action |
   367	| `LandingRecord` | Workspace/Git adapter normalization | Prove candidate-to-landed relation | Release/closure |
   368	| `PostLandingVerification` | Assurance service | Verify landed subject | Product outcome |
   369	| `ReleaseEvidence` | Release management | Build/promotion/rollback facts | Service/product acceptance |
   370	| `OperationEvidence` | Operations/service evidence ingestion | Health/support/recovery facts | Product outcome |
   371	| `OutcomeReview` | Product definition under product owner | Compare outcome and decide keep/change/remove | Rewrite engineering facts |
   372	| `TransitionEvent` | Owning aggregate UoW | Durable accepted state fact | State owned by another aggregate |
   373	
   374	## 7. Review separation
   375	
   376	Review is five immutable records, not one mutable model response:
   377	
   378	```text
   379	ReviewRequest
   380	  -> AnalysisAttempt[1..N]
   381	  -> ReviewObservation[0..N]
   382	  -> IndependenceEvaluation
   383	  -> ReviewVerdict
   384	  -> EvidenceSnapshot
   385	  -> GateEvaluation
   386	```
   387	
   388	`ReviewRequest` records maker principal/run/session/role, exact subject,
   389	separate review packet, required reviewer role, prohibited capabilities, blind
   390	context manifest, diversity requirements expressed as actual route facts, and
   391	qualification policy.
   392	
   393	Each `AnalysisAttempt` records reviewer principal/role/session, actual
   394	provider/model/transport/executable/parser/isolation identities, route lock,
   395	input/output artifact digests, start/end/deadline/budget, granted capabilities,
   396	write attempts, failures, usage, and relation to previous attempts.
   397	
   398	`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
   399	self-assertion and a model-family label are insufficient. It compares maker and
   400	reviewer identities/sessions, packet construction, write capability/activity,
   401	blindness manifest, route/provider/transport facts, qualification, hidden
   402	fixture isolation, and candidate identity.
   403	
   404	`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
   405	`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
   406	not `GateOutcome`.
   407	
   408	### 7.1 Deadline and budget null semantics
   409	
   410	In draft templates, `null` means **not established**. It never means unlimited.
   411	A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
   412	reservation cannot become `ACTIVE` while a policy-required deadline or budget
   413	dimension is null. Zero denies consumption of that dimension. A dimension may
   414	be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
   415	reason, accountable owner, and evidence reference.
   416	
   417	Every activated execution/review reservation has an absolute deadline and all
   418	transitive dimensions required by its risk/work-class policy. Child limits are
   419	no later/larger than every ancestor. Canonical validation rejects negative,
   420	ambiguous, unitless, floating-point, or “unlimited” sentinel values.
   421	
   422	## 8. Finding lifecycle
   423	
   424	Every finding has category, severity, confidence/epistemic status, exact
   425	location, claim, impact, evidence, required action, owner, and state:
   426	
   427	```text
   428	OPEN
   429	  -> ACCEPTED
   430	  -> FIXED_PENDING_VERIFICATION
   431	  -> VERIFIED
   432	
   433	OPEN
   434	  -> DISPUTED
   435	  -> SPECIALIST_REVIEW
   436	  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
   437	```
   438	
   439	Only the review/finding application service changes finding state. A maker may
   440	submit a resolution proposal but cannot mark its finding verified.
   441	
   442	## 9. Gate, decision, grant, and permit order
   443	
   444	The required order is:
   445	
   446	```text
   447	eligible evidence
   448	  -> EvidenceSnapshot
   449	  -> GateEvaluation
   450	  -> authenticated HumanDecisionRecord when policy requires
   451	  -> ConsumableAuthorityGrant
   452	  -> Permit
   453	  -> atomic permit consumption + effect intent
   454	```
   455	
   456	`GateEvaluation` binds gate ID/version, namespace, policy, required and observed
   457	claims, checker qualifications/results, applicability proof, freshness,
   458	coverage, conflicting/missing evidence, exact subject, evaluator code digest,
   459	and one `GateOutcome`.
   460	
   461	`HumanDecisionRecord` discriminates:
   462	
   463	- `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`;
   464	- `RISK_ACCEPTANCE_OR_WAIVER`;
   465	- `WORK_TRANSITION`;
   475	## 10. Worker-visible versus withheld verification
   476	
   477	The worker packet contains required public test families, commands, acceptance
   478	criteria, and an opaque `withheld_verification_profile_id`. It never contains
   479	hidden fixture paths, IDs, contents, expected results, answer keys, grader
   480	internals, or secrets. Qualification/verifier packets hold those fields and are
   481	unavailable to maker identities and workspaces.
   482	
   483	## 11. Command and test evidence
   484	
   485	Commands are structured records:
   486	
   487	```text
   488	argv[]                 exact arguments, never a reconstructed shell string
   489	cwd_repository_relative
   490	environment_allowlist_digest
   491	tool/executable identity and digest
   492	subject commit/workspace
   493	start/end/deadline
   494	exit status or typed launch/timeout/cancel failure
   495	stdout/stderr artifact refs
   496	redaction/classification status
   497	```
   498	
   499	`AgentHandoff` references immutable `RunResult`, test, evidence, finding, and
   500	artifact IDs. Any human-readable duplication is a generated projection and must
   501	match its source digest.
   502	
   503	## 12. Executable schema tree
   504	
   505	```text
   506	schemas/
   507	├── common/
   508	│   ├── identifiers.schema.json
   509	│   ├── subject-binding-v1.schema.json
   510	│   ├── work-subject-v1.schema.json
   511	│   ├── exact-subject-v1.schema.json
   512	│   ├── architecture-subject-v1.schema.json
   513	│   ├── research-subject-v1.schema.json
   514	│   ├── resource-subject-v1.schema.json
   515	│   ├── core-sdlc-trace-v1.schema.json
   575	
   576	This tree now exists and is indexed by
   577	`architecture/contracts/schema-registry.json`. The 36 governed YAML artifact
   578	types have one schema and one canonical producer entry each. Common subject,
   579	identifier, evidence-reference, engineering-practice-profile,
   580	test-practice-profile, path-contract, per-rule architecture-assessment, and
   581	canonical-digest schemas are executable Draft 2020-12 contracts. Schema
   582	validation is necessary but not sufficient: the deterministic validator also
   583	enforces registry closure, exact VITAL, topology, TDD, path, and fixture
   584	denominators, digest integrity, single-use permits, subject equality,
   585	cross-context import and cycle policy, test/production-path parity, and scoring
   586	honesty.
   587	
   588	This remains the detailed artifact-contract subset of the full `schemas/`
   589	namespace map in the system architecture. The system map additionally reserves
   590	product, service, configuration, supplier, interaction, module, route,
   591	operation, and other future domain-schema namespaces. It is a superset, not a
   592	competing tree.
   593	
   594	Generated Python/TypeScript types, examples, documentation, and validators come
   595	from these schemas and registries. Hand editing generated files fails CI.
   596	
   597	Contract generation and validation are one serialized publication protocol.
   598	Both tools acquire the same repository-scoped interprocess lock before reading,
   599	cleaning, writing, or validating any generated tree. The lock lives outside
   600	all generator-owned paths. A validator or second generator therefore waits for
   601	the complete publication and can never treat the intentional cleanup window as
   602	an empty denominator. The disposable
   603	`scripts/architecture/test_contract_concurrency.py` regression stages exactly
   604	that window, proves both contenders wait, restores the prior complete tree,
   605	and requires the final generated-tree digest to equal its baseline.
   650	[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md)
   651	governs two separate readiness tiers.
   652	
   653	`IMPLEMENTATION_START_READY` still requires:
   654	
   655	- authoring placeholders to be resolved before any instance becomes `SEALED`;
   656	- generated Python and TypeScript consumer packages and cross-language
   657	  canonicalization parity;
   658	- exact-revision compatibility/upcaster fixtures for every breaking change;
   659	- deterministic validation of the exact committed source and generated
   660	  manifests plus the closed readiness subject manifest and every native-
   661	  subject evidence bridge, with no stale output, denominator, or conflict;
   662	- a clean, committed, upstream-derived `SDLC-FORK-000: PASS` subject;
   663	- one real current-subject non-synthetic ADR-0008 cycle, its separate
   664	  `SUCCEEDED` landing, and post-landing seal;
   665	- fresh same-subject OpenCode HY3 and DeepSeek V4 Pro structural reviews with
   666	  no unresolved P0/P1 finding; and
   667	- an authenticated causal human implementation-start decision.
   668	
   669	Runtime producer enforcement, runtime rule results, and capability scores may
   670	remain explicitly `NOT_ASSESSED`/null at this tier. Before it passes, only the
   671	bounded `PRE_READINESS_TOOLING_TRACER` may produce its architecture/tooling
   672	evidence; it cannot implement product capability or activate product runtime.
   673	After it passes, an ordinary authorized product commit may retain the admitted
   674	baseline only on a clean descendant with byte-identical governed
   675	design/control paths; the commit's own normal controls are never inherited
   676	from readiness.
   677	
   678	`PRODUCTION_READY` additionally requires:
   679	
   680	- every runtime producer to be its registered context and unable to forge
   681	  another producer's record;
   682	- hidden-fixture isolation and review independence through a real harness;
   683	- an enacted `src/ranex` tree plus representative test roots and exactly 64
   684	  current ADR-0007–ADR-0010 rule results before source topology, import-cycle,
   685	  production/test-path parity, or TDD conformance can pass;
   686	- qualified runtime, security, recovery, operational, adoption, and applicable
   687	  capability-assessment evidence; and
   688	- authenticated human acceptance of the resulting exact-subject `AI-G2` and
   689	  production-readiness evidence.
/bin/bash: line 2: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-record-projection-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "analysis_attempt_refs": {
     7	      "items": {},
     8	      "type": "array"
     9	    },
    10	    "artifact_type": {
    11	      "const": "review_record_projection"
    12	    },
    13	    "core_sdlc_trace_ref": {
    14	      "type": "string"
    15	    },
    16	    "digest": {
    17	      "type": "string",
    18	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    19	    },
    20	    "gate_evaluation_ref": {
    21	      "type": [
    22	        "string",
    23	        "null"
    24	      ]
    25	    },
    26	    "generated_at": {
    27	      "type": "string",
    28	      "x-ranex-runtime-format": "date-time"
    29	    },
    30	    "independence_evaluation_digest": {
    31	      "type": "string",
    32	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    33	    },
    34	    "independence_evaluation_id": {
    35	      "type": "string"
    36	    },
    37	    "projection_id": {
    38	      "type": "string"
    39	    },
    40	    "review_observation_refs": {
    41	      "items": {},
    42	      "type": "array"
    43	    },
    44	    "review_request_digest": {
    45	      "type": "string",
    46	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    47	    },
    48	    "review_request_id": {
    49	      "type": "string"
    50	    },
    51	    "review_verdict_digest": {
    52	      "type": "string",
    53	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    54	    },
    55	    "review_verdict_id": {
    56	      "type": "string"
    57	    },
    58	    "schema_version": {
    59	      "const": "1"
    60	    },
    61	    "source_registry_version": {
    62	      "type": "string"
    63	    },
    64	    "subject_digest": {
    65	      "type": "string",
    66	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    67	    },
    68	    "subject_manifest_digest": {
    69	      "type": [
    70	        "string",
    71	        "null"
    72	      ]
    73	    },
    74	    "subject_ref": {
    75	      "type": "string"
    76	    },
    77	    "subject_schema": {
    78	      "type": [
    79	        "string",
    80	        "null"
    81	      ]
    82	    }
    83	  },
    84	  "required": [
    85	    "schema_version",
    86	    "artifact_type",
    87	    "projection_id",
    88	    "subject_schema",
    89	    "subject_ref",
    90	    "subject_digest",
    91	    "subject_manifest_digest",
    92	    "core_sdlc_trace_ref",
    93	    "review_request_id",
    94	    "review_request_digest",
    95	    "analysis_attempt_refs",
    96	    "review_observation_refs",
    97	    "independence_evaluation_id",
    98	    "independence_evaluation_digest",
    99	    "review_verdict_id",
   100	    "review_verdict_digest",
   101	    "gate_evaluation_ref",
   102	    "generated_at",
   103	    "source_registry_version",
   104	    "digest"
   105	  ],
   106	  "title": "review_record_projection",
   107	  "type": "object",
   108	  "x-ranex-canonical-producer": "analytical_review",
   109	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   110	  "x-ranex-template": "docs/architecture/templates/REVIEW_RECORD.yaml"
   111	}
/bin/bash: line 4: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
scripts/architecture/README.md:17:documents and authoring templates.
scripts/architecture/README.md:19:`validate_contracts.py` rejects duplicate YAML keys, schema drift, registry
scripts/architecture/README.md:33:concurrency-regression script digests alongside the registry, schema, practice
scripts/architecture/generate_contracts.py:5:documents and authoring templates, then writes only generated contract,
scripts/architecture/generate_contracts.py:6:schema, fixture, and assessment paths owned by Wave 1.
scripts/architecture/generate_contracts.py:27:import jsonschema
scripts/architecture/generate_contracts.py:34:SCHEMAS = ROOT / "schemas"
scripts/architecture/generate_contracts.py:36:TEMPLATES = ROOT / "docs" / "architecture" / "templates"
scripts/architecture/generate_contracts.py:175:            "schemas/common/"
scripts/architecture/generate_contracts.py:176:            "legacy-test-change-exception-v1.schema.json"
scripts/architecture/generate_contracts.py:179:            "schemas/common/"
scripts/architecture/generate_contracts.py:180:            "legacy-test-cutover-removal-record-v1.schema.json"
scripts/architecture/generate_contracts.py:182:        "schemas/common/legacy-test-layout-policy-v1.schema.json",
scripts/architecture/generate_contracts.py:184:            "schemas/common/"
scripts/architecture/generate_contracts.py:185:            "legacy-test-migration-record-v1.schema.json"
scripts/architecture/generate_contracts.py:187:        "schemas/execution/landing-record-v1.schema.json",
scripts/architecture/generate_contracts.py:217:        "schema_path": (
scripts/architecture/generate_contracts.py:218:            "schemas/common/tdd-cycle-record-v1.schema.json"
scripts/architecture/generate_contracts.py:226:        "schema_path": (
scripts/architecture/generate_contracts.py:227:            "schemas/common/tdd-exception-record-v1.schema.json"
scripts/architecture/generate_contracts.py:235:        "schema_path": (
scripts/architecture/generate_contracts.py:236:            "schemas/common/test-quarantine-record-v1.schema.json"
scripts/architecture/generate_contracts.py:244:        "schema_path": (
scripts/architecture/generate_contracts.py:245:            "schemas/common/test-deletion-record-v1.schema.json"
scripts/architecture/generate_contracts.py:274:# template default and is deliberately not bound to this set; that
scripts/architecture/generate_contracts.py:286:    "AGENT_ASSIGNMENT.yaml": ("fleet/assignment-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:287:    "AI_HANDOFF.yaml": ("execution/agent-handoff-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:288:    "AI_TASK_PACKET.yaml": ("work/task-packet-v1.schema.json", "context_compilation"),
scripts/architecture/generate_contracts.py:289:    "ANALYSIS_ATTEMPT.yaml": ("review/analysis-attempt-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:290:    "ARCHITECTURE_PROPOSAL.yaml": ("architecture/proposal-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:291:    "ARCHITECTURE_RECONCILIATION.yaml": ("architecture/reconciliation-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:292:    "ARCHITECTURE_REVIEW_PACKET.yaml": ("architecture/review-packet-v1.schema.json", "context_compilation"),
scripts/architecture/generate_contracts.py:293:    "AUTHORITY_GRANT.yaml": ("authority/authority-grant-v1.schema.json", "governed_execution"),
scripts/architecture/generate_contracts.py:294:    "CAPABILITY_ASSESSMENT.yaml": ("process/capability-assessment-v1.schema.json", "process_assurance"),
scripts/architecture/generate_contracts.py:295:    "CAPABILITY_DOMAIN_PROJECTION.yaml": ("process/capability-domain-projection-v1.schema.json", "process_assurance"),
scripts/architecture/generate_contracts.py:296:    "CHECKER_RESULT.yaml": ("assurance/checker-result-v1.schema.json", "assurance"),
scripts/architecture/generate_contracts.py:297:    "CORE_SDLC_TRACE.yaml": ("common/core-sdlc-trace-v1.schema.json", "configuration_management"),
scripts/architecture/generate_contracts.py:298:    "DISPATCH_OFFER.yaml": ("fleet/dispatch-offer-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:299:    "EVIDENCE_SNAPSHOT.yaml": ("assurance/evidence-snapshot-v1.schema.json", "assurance"),
scripts/architecture/generate_contracts.py:300:    "FLEET_EXPERIMENT.yaml": ("fleet/fleet-experiment-v1.schema.json", "process_assurance"),
scripts/architecture/generate_contracts.py:301:    "GATE_EVALUATION.yaml": ("assurance/gate-evaluation-v1.schema.json", "assurance"),
scripts/architecture/generate_contracts.py:302:    "HUMAN_DECISION.yaml": ("authority/human-decision-v1.schema.json", "policy"),
scripts/architecture/generate_contracts.py:303:    "INDEPENDENCE_EVALUATION.yaml": ("review/independence-evaluation-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:304:    "LANDING_RECORD.yaml": ("execution/landing-record-v1.schema.json", "workspace"),
scripts/architecture/generate_contracts.py:305:    "MAILBOX_ENVELOPE.yaml": ("fleet/mailbox-envelope-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:306:    "OPERATION_EVIDENCE.yaml": ("lifecycle/operation-evidence-v1.schema.json", "operations"),
scripts/architecture/generate_contracts.py:307:    "OUTCOME_REVIEW.yaml": ("lifecycle/outcome-review-v1.schema.json", "product_definition"),
scripts/architecture/generate_contracts.py:308:    "PERMIT.yaml": ("authority/permit-v1.schema.json", "governed_execution"),
scripts/architecture/generate_contracts.py:309:    "POST_LANDING_VERIFICATION.yaml": ("execution/post-landing-verification-v1.schema.json", "assurance"),
scripts/architecture/generate_contracts.py:310:    "RELEASE_EVIDENCE.yaml": ("lifecycle/release-evidence-v1.schema.json", "release_management"),
scripts/architecture/generate_contracts.py:311:    "RESEARCH_PACKET.yaml": ("research/research-packet-v1.schema.json", "product_definition"),
scripts/architecture/generate_contracts.py:312:    "RESOURCE_RESERVATION.yaml": ("resources/resource-reservation-v1.schema.json", "resource_governance"),
scripts/architecture/generate_contracts.py:313:    "REVIEW_OBSERVATION.yaml": ("review/review-observation-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:314:    "REVIEW_RECORD.yaml": ("review/review-record-projection-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:315:    "REVIEW_REQUEST.yaml": ("review/review-request-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:316:    "REVIEW_VERDICT.yaml": ("review/review-verdict-v1.schema.json", "analytical_review"),
scripts/architecture/generate_contracts.py:317:    "RUN_RESULT.yaml": ("execution/run-result-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:318:    "TRANSITION_EVENT.yaml": ("work/transition-event-v1.schema.json", "owning_aggregate_uow"),
scripts/architecture/generate_contracts.py:319:    "WORKER_ATTEMPT.yaml": ("fleet/worker-attempt-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:320:    "WORKER_LEASE.yaml": ("fleet/lease-v1.schema.json", "agent_collaboration"),
scripts/architecture/generate_contracts.py:321:    "WORK_INTAKE.yaml": ("work/work-intake-v1.schema.json", "work_management"),
scripts/architecture/generate_contracts.py:327:        "schema_path": (
scripts/architecture/generate_contracts.py:328:            "schemas/artifacts/"
scripts/architecture/generate_contracts.py:329:            "artifact-legal-hold-fact-v1.schema.json"
scripts/architecture/generate_contracts.py:341:        "schema_path": (
scripts/architecture/generate_contracts.py:342:            "schemas/assurance/"
scripts/architecture/generate_contracts.py:343:            "checker-execution-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:355:        "schema_path": (
scripts/architecture/generate_contracts.py:356:            "schemas/common/tdd-cycle-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:368:        "schema_path": (
scripts/architecture/generate_contracts.py:369:            "schemas/common/tdd-exception-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:381:        "schema_path": (
scripts/architecture/generate_contracts.py:382:            "schemas/common/test-deletion-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:394:        "schema_path": (
scripts/architecture/generate_contracts.py:395:            "schemas/common/test-quarantine-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:407:        "schema_path": (
scripts/architecture/generate_contracts.py:408:            "schemas/assurance/readiness-subject-v1.schema.json"
scripts/architecture/generate_contracts.py:420:        "schema_path": (
scripts/architecture/generate_contracts.py:421:            "schemas/assurance/"
scripts/architecture/generate_contracts.py:422:            "readiness-subject-manifest-v1.schema.json"
scripts/architecture/generate_contracts.py:434:        "schema_path": (
scripts/architecture/generate_contracts.py:435:            "schemas/assurance/"
scripts/architecture/generate_contracts.py:436:            "readiness-evidence-binding-v1.schema.json"
scripts/architecture/generate_contracts.py:448:        "schema_path": (
scripts/architecture/generate_contracts.py:449:            "schemas/assurance/readiness-assessment-v1.schema.json"
scripts/architecture/generate_contracts.py:539:        "purpose": "Public API, schema, port, fake/real-adapter parity, and compatibility.",
scripts/architecture/generate_contracts.py:549:        "purpose": "Path, ownership, import, cycle, composition, discovery, and generated-drift fitness.",
scripts/architecture/generate_contracts.py:639:        "shape_rule": "Bind public API, port, schema, fake, real-adapter, and compatibility contracts to one context.",
scripts/architecture/generate_contracts.py:653:        "shape_rule": "Bind each fitness check to exact registry, rule, path, import, or generated-projection metadata.",
scripts/architecture/generate_contracts.py:921:def write_generated_text(path: Path, value: str) -> None:
scripts/architecture/generate_contracts.py:980:            and candidate.get("schema_version") == "state-axis-contract/v1"
scripts/architecture/generate_contracts.py:989:        "schema_version",
scripts/architecture/generate_contracts.py:1008:        != "schemas/work/transition-event-v1.schema.json"
scripts/architecture/generate_contracts.py:1010:        raise ValueError("Unexpected state transition fact schema")
scripts/architecture/generate_contracts.py:1294:    schema_version: str,
scripts/architecture/generate_contracts.py:1300:            f"Missing marked YAML contract: {schema_version}"
scripts/architecture/generate_contracts.py:1314:        and candidate.get("schema_version") == schema_version
scripts/architecture/generate_contracts.py:1318:            f"Expected one marked {schema_version} contract"
scripts/architecture/generate_contracts.py:1331:        "schema_version",
scripts/architecture/generate_contracts.py:1333:        "schema_ref",
scripts/architecture/generate_contracts.py:1344:        or contract["schema_ref"]
scripts/architecture/generate_contracts.py:1345:        != "schemas/work/transition-event-v1.schema.json"
scripts/architecture/generate_contracts.py:1396:        "schema_version",
scripts/architecture/generate_contracts.py:1398:        "schema_ref",
scripts/architecture/generate_contracts.py:1409:        or contract["schema_ref"]
scripts/architecture/generate_contracts.py:1410:        != "schemas/artifacts/artifact-legal-hold-fact-v1.schema.json"
scripts/architecture/generate_contracts.py:1490:        and candidate.get("schema_version")
scripts/architecture/generate_contracts.py:1499:        "schema_version",
scripts/architecture/generate_contracts.py:1535:            "schema_valid_positive",
scripts/architecture/generate_contracts.py:1617:        "schema_version",
scripts/architecture/generate_contracts.py:2095:def event_nonempty_string_schema(*, max_length: int = 1024) -> dict[str, Any]:
scripts/architecture/generate_contracts.py:2104:def event_id_schema(id_type: str) -> dict[str, Any]:
scripts/architecture/generate_contracts.py:2115:def event_ref_schema(ref_type: str) -> dict[str, Any]:
scripts/architecture/generate_contracts.py:2119:            "id": event_id_schema(ref_type),
scripts/architecture/generate_contracts.py:2131:def event_payload_base_type_schema(
scripts/architecture/generate_contracts.py:2135:        return event_nonempty_string_schema()
scripts/architecture/generate_contracts.py:2155:        return event_ref_schema("Artifact")
scripts/architecture/generate_contracts.py:2157:        return event_id_schema(type_name[:-2])
scripts/architecture/generate_contracts.py:2161:def event_payload_field_schema(
scripts/architecture/generate_contracts.py:2168:        schema = event_id_schema(type_parameter)
/bin/bash: line 6: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
     1	from __future__ import annotations
     2	
     3	import fcntl
     4	import hashlib
     5	import json
     6	import os
     7	from dataclasses import dataclass
     8	from pathlib import Path
     9	from typing import Any
    10	
    11	from ranex.foundation.canonical import canonical_json
    12	
    13	_GENESIS_DIGEST = "0" * 64
    14	
    15	
    16	class LedgerIntegrityError(RuntimeError):
    17	    pass
    18	
    19	
    20	@dataclass(frozen=True, slots=True)
    21	class LedgerEntry:
    22	    sequence: int
    23	    previous_digest: str
    24	    record_digest: str
    25	    entry_digest: str
    26	    record: dict[str, Any]
    27	
    28	
    29	@dataclass(frozen=True, slots=True)
    30	class LedgerVerification:
    31	    valid: bool
    32	    entry_count: int
    33	    broken_sequence: int | None
    34	    head_digest: str
    35	    reason: str | None = None
    36	
    37	
    38	def _sha256_text(value: str) -> str:
    39	    return hashlib.sha256(value.encode("utf-8")).hexdigest()
    40	
    41	
    42	def _entry_digest(
    43	    *,
    44	    sequence: int,
    45	    previous_digest: str,
    46	    record_digest: str,
    47	) -> str:
    48	    return _sha256_text(
    49	        canonical_json(
    50	            {
    51	                "previous_digest": previous_digest,
    52	                "record_digest": record_digest,
    53	                "sequence": sequence,
    54	            }
    55	        )
    56	    )
    57	
    58	
    59	class HashChainLedger:
    60	    """Append-only API over a tamper-evident canonical JSONL hash chain."""
    61	
    62	    def __init__(self, path: Path) -> None:
    63	        self._path = path
    64	
    65	    def _verify_lines(self, lines: list[str]) -> LedgerVerification:
    66	        previous_digest = _GENESIS_DIGEST
    67	        for expected_sequence, line in enumerate(lines, start=1):
    68	            try:
    69	                raw = json.loads(line)
    70	                record = raw["record"]
    71	                record_digest = _sha256_text(canonical_json(record))
    72	                computed_entry_digest = _entry_digest(
    73	                    sequence=expected_sequence,
    74	                    previous_digest=previous_digest,
    75	                    record_digest=record_digest,
    76	                )
    77	                valid = (
    78	                    raw["sequence"] == expected_sequence
    79	                    and raw["previous_digest"] == previous_digest
    80	                    and raw["record_digest"] == record_digest
    81	                    and raw["entry_digest"] == computed_entry_digest
    82	                )
    83	            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
    84	                valid = False
    85	                computed_entry_digest = previous_digest
    86	            if not valid:
    87	                return LedgerVerification(
    88	                    valid=False,
    89	                    entry_count=len(lines),
    90	                    broken_sequence=expected_sequence,
    91	                    head_digest=previous_digest,
    92	                    reason="ledger hash chain is invalid",
    93	                )
    94	            previous_digest = computed_entry_digest
    95	        return LedgerVerification(
    96	            valid=True,
    97	            entry_count=len(lines),
    98	            broken_sequence=None,
    99	            head_digest=previous_digest,
   100	        )
   101	
   102	    def verify(self) -> LedgerVerification:
   103	        if not self._path.exists():
   104	            return LedgerVerification(
   105	                valid=False,
   106	                entry_count=0,
   107	                broken_sequence=None,
   108	                head_digest=_GENESIS_DIGEST,
   109	                reason="ledger file is missing",
   110	            )
   111	        with self._path.open("r", encoding="utf-8") as stream:
   112	            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
   113	            lines = [line for line in stream.read().splitlines() if line.strip()]
   114	        if not lines:
   115	            return LedgerVerification(
   116	                valid=False,
   117	                entry_count=0,
   118	                broken_sequence=None,
   119	                head_digest=_GENESIS_DIGEST,
   120	                reason="ledger file is empty",
   121	            )
   122	        return self._verify_lines(lines)
   123	
   124	    def append(self, record: dict[str, Any]) -> LedgerEntry:
   125	        return self._append(record, idempotency_key=None)
   126	
   127	    def append_once(self, record: dict[str, Any], *, key: str) -> LedgerEntry:
   128	        if not key:
   129	            raise ValueError("idempotency key must be non-empty")
   130	        return self._append(record, idempotency_key=key)
   131	
   132	    def _append(
   133	        self,
   134	        record: dict[str, Any],
   135	        *,
   136	        idempotency_key: str | None,
   137	    ) -> LedgerEntry:
   138	        if "_ledger_idempotency_key" in record:
   139	            raise ValueError("record uses a reserved ledger field")
   140	        stored_record = dict(record)
   141	        if idempotency_key is not None:
   142	            stored_record["_ledger_idempotency_key"] = idempotency_key
   143	
   144	        self._path.parent.mkdir(parents=True, exist_ok=True)
   145	        self._path.touch(mode=0o600, exist_ok=True)
   146	        self._path.chmod(0o600)
   147	        with self._path.open("a+", encoding="utf-8") as stream:
   148	            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
   149	            stream.seek(0)
   150	            lines = [line for line in stream.read().splitlines() if line.strip()]
   151	            verification = self._verify_lines(lines)
   152	            if not verification.valid:
   153	                raise LedgerIntegrityError(
   154	                    "refusing append because the ledger hash chain is invalid"
   155	                )
   156	
   157	            if idempotency_key is not None:
   158	                for line in lines:
   159	                    raw = json.loads(line)
   160	                    existing_record = raw["record"]
   161	                    if (
   162	                        existing_record.get("_ledger_idempotency_key")
   163	                        == idempotency_key
   164	                    ):
   165	                        if canonical_json(existing_record) != canonical_json(
   166	                            stored_record
   167	                        ):
   168	                            raise LedgerIntegrityError(
   169	                                "idempotency key was reused for a different record"
   170	                            )
   171	                        return LedgerEntry(
   172	                            sequence=raw["sequence"],
   173	                            previous_digest=raw["previous_digest"],
   174	                            record_digest=raw["record_digest"],
   175	                            entry_digest=raw["entry_digest"],
   176	                            record=existing_record,
   177	                        )
   178	
   179	            sequence = verification.entry_count + 1
   180	            record_digest = _sha256_text(canonical_json(stored_record))
   181	            entry_digest = _entry_digest(
   182	                sequence=sequence,
   183	                previous_digest=verification.head_digest,
   184	                record_digest=record_digest,
   185	            )
   186	            entry = LedgerEntry(
   187	                sequence=sequence,
   188	                previous_digest=verification.head_digest,
   189	                record_digest=record_digest,
   190	                entry_digest=entry_digest,
   191	                record=stored_record,
   192	            )
   193	            stream.seek(0, os.SEEK_END)
   194	            stream.write(
   195	                canonical_json(
   196	                    {
   197	                        "sequence": entry.sequence,
   198	                        "previous_digest": entry.previous_digest,
   199	                        "record_digest": entry.record_digest,
   200	                        "entry_digest": entry.entry_digest,
   201	                        "record": entry.record,
   202	                    }
   203	                )
   204	                + "\n"
   205	            )
   206	            stream.flush()
   207	            os.fsync(stream.fileno())
   208	            return entry

exec
/bin/bash -lc "nl -ba docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n '386,465p'
nl -ba schemas/review/review-record-projection-v1.schema.json
nl -ba schemas/review/review-verdict-v1.schema.json
nl -ba schemas/review/review-request-v1.schema.json | sed -n '1,140p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   386	```
   387	
   388	`ReviewRequest` records maker principal/run/session/role, exact subject,
   389	separate review packet, required reviewer role, prohibited capabilities, blind
   390	context manifest, diversity requirements expressed as actual route facts, and
   391	qualification policy.
   392	
   393	Each `AnalysisAttempt` records reviewer principal/role/session, actual
   394	provider/model/transport/executable/parser/isolation identities, route lock,
   395	input/output artifact digests, start/end/deadline/budget, granted capabilities,
   396	write attempts, failures, usage, and relation to previous attempts.
   397	
   398	`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
   399	self-assertion and a model-family label are insufficient. It compares maker and
   400	reviewer identities/sessions, packet construction, write capability/activity,
   401	blindness manifest, route/provider/transport facts, qualification, hidden
   402	fixture isolation, and candidate identity.
   403	
   404	`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
   405	`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
   406	not `GateOutcome`.
   407	
   408	### 7.1 Deadline and budget null semantics
   409	
   410	In draft templates, `null` means **not established**. It never means unlimited.
   411	A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
   412	reservation cannot become `ACTIVE` while a policy-required deadline or budget
   413	dimension is null. Zero denies consumption of that dimension. A dimension may
   414	be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
   415	reason, accountable owner, and evidence reference.
   416	
   417	Every activated execution/review reservation has an absolute deadline and all
   418	transitive dimensions required by its risk/work-class policy. Child limits are
   419	no later/larger than every ancestor. Canonical validation rejects negative,
   420	ambiguous, unitless, floating-point, or “unlimited” sentinel values.
   421	
   422	## 8. Finding lifecycle
   423	
   424	Every finding has category, severity, confidence/epistemic status, exact
   425	location, claim, impact, evidence, required action, owner, and state:
   426	
   427	```text
   428	OPEN
   429	  -> ACCEPTED
   430	  -> FIXED_PENDING_VERIFICATION
   431	  -> VERIFIED
   432	
   433	OPEN
   434	  -> DISPUTED
   435	  -> SPECIALIST_REVIEW
   436	  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
   437	```
   438	
   439	Only the review/finding application service changes finding state. A maker may
   440	submit a resolution proposal but cannot mark its finding verified.
   441	
   442	## 9. Gate, decision, grant, and permit order
   443	
   444	The required order is:
   445	
   446	```text
   447	eligible evidence
   448	  -> EvidenceSnapshot
   449	  -> GateEvaluation
   450	  -> authenticated HumanDecisionRecord when policy requires
   451	  -> ConsumableAuthorityGrant
   452	  -> Permit
   453	  -> atomic permit consumption + effect intent
   454	```
   455	
   456	`GateEvaluation` binds gate ID/version, namespace, policy, required and observed
   457	claims, checker qualifications/results, applicability proof, freshness,
   458	coverage, conflicting/missing evidence, exact subject, evaluator code digest,
   459	and one `GateOutcome`.
   460	
   461	`HumanDecisionRecord` discriminates:
   462	
   463	- `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`;
   464	- `RISK_ACCEPTANCE_OR_WAIVER`;
   465	- `WORK_TRANSITION`;
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-record-projection-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "analysis_attempt_refs": {
     7	      "items": {},
     8	      "type": "array"
     9	    },
    10	    "artifact_type": {
    11	      "const": "review_record_projection"
    12	    },
    13	    "core_sdlc_trace_ref": {
    14	      "type": "string"
    15	    },
    16	    "digest": {
    17	      "type": "string",
    18	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    19	    },
    20	    "gate_evaluation_ref": {
    21	      "type": [
    22	        "string",
    23	        "null"
    24	      ]
    25	    },
    26	    "generated_at": {
    27	      "type": "string",
    28	      "x-ranex-runtime-format": "date-time"
    29	    },
    30	    "independence_evaluation_digest": {
    31	      "type": "string",
    32	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    33	    },
    34	    "independence_evaluation_id": {
    35	      "type": "string"
    36	    },
    37	    "projection_id": {
    38	      "type": "string"
    39	    },
    40	    "review_observation_refs": {
    41	      "items": {},
    42	      "type": "array"
    43	    },
    44	    "review_request_digest": {
    45	      "type": "string",
    46	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    47	    },
    48	    "review_request_id": {
    49	      "type": "string"
    50	    },
    51	    "review_verdict_digest": {
    52	      "type": "string",
    53	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    54	    },
    55	    "review_verdict_id": {
    56	      "type": "string"
    57	    },
    58	    "schema_version": {
    59	      "const": "1"
    60	    },
    61	    "source_registry_version": {
    62	      "type": "string"
    63	    },
    64	    "subject_digest": {
    65	      "type": "string",
    66	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    67	    },
    68	    "subject_manifest_digest": {
    69	      "type": [
    70	        "string",
    71	        "null"
    72	      ]
    73	    },
    74	    "subject_ref": {
    75	      "type": "string"
    76	    },
    77	    "subject_schema": {
    78	      "type": [
    79	        "string",
    80	        "null"
    81	      ]
    82	    }
    83	  },
    84	  "required": [
    85	    "schema_version",
    86	    "artifact_type",
    87	    "projection_id",
    88	    "subject_schema",
    89	    "subject_ref",
    90	    "subject_digest",
    91	    "subject_manifest_digest",
    92	    "core_sdlc_trace_ref",
    93	    "review_request_id",
    94	    "review_request_digest",
    95	    "analysis_attempt_refs",
    96	    "review_observation_refs",
    97	    "independence_evaluation_id",
    98	    "independence_evaluation_digest",
    99	    "review_verdict_id",
   100	    "review_verdict_digest",
   101	    "gate_evaluation_ref",
   102	    "generated_at",
   103	    "source_registry_version",
   104	    "digest"
   105	  ],
   106	  "title": "review_record_projection",
   107	  "type": "object",
   108	  "x-ranex-canonical-producer": "analytical_review",
   109	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   110	  "x-ranex-template": "docs/architecture/templates/REVIEW_RECORD.yaml"
   111	}
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-verdict-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "artifact_type": {
     7	      "const": "review_verdict"
     8	    },
     9	    "core_sdlc_trace_ref": {
    10	      "type": "string"
    11	    },
    12	    "digest": {
    13	      "type": "string",
    14	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    15	    },
    16	    "evidence_refs": {
    17	      "items": {},
    18	      "type": "array"
    19	    },
    20	    "independence_evaluation_id": {
    21	      "type": "string"
    22	    },
    23	    "limitations": {
    24	      "items": {},
    25	      "type": "array"
    26	    },
    27	    "observation_ids": {
    28	      "items": {},
    29	      "type": "array"
    30	    },
    31	    "open_finding_refs": {
    32	      "items": {},
    33	      "type": "array"
    34	    },
    35	    "produced_at": {
    36	      "type": "string",
    37	      "x-ranex-runtime-format": "date-time"
    38	    },
    39	    "producer_service_id": {
    40	      "type": "string"
    41	    },
    42	    "reconciliation_refs": {
    43	      "items": {},
    44	      "type": "array"
    45	    },
    46	    "resolved_finding_refs": {
    47	      "items": {},
    48	      "type": "array"
    49	    },
    50	    "review_request_id": {
    51	      "type": "string"
    52	    },
    53	    "schema_version": {
    54	      "const": "1"
    55	    },
    56	    "subject_digest": {
    57	      "type": "string",
    58	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    59	    },
    60	    "subject_manifest_digest": {
    61	      "type": [
    62	        "string",
    63	        "null"
    64	      ]
    65	    },
    66	    "subject_ref": {
    67	      "type": "string"
    68	    },
    69	    "subject_schema": {
    70	      "type": [
    71	        "string",
    72	        "null"
    73	      ]
    74	    },
    75	    "verdict": {
    76	      "type": "string"
    77	    },
    78	    "verdict_id": {
    79	      "type": "string"
    80	    }
    81	  },
    82	  "required": [
    83	    "schema_version",
    84	    "artifact_type",
    85	    "verdict_id",
    86	    "review_request_id",
    87	    "observation_ids",
    88	    "independence_evaluation_id",
    89	    "subject_schema",
    90	    "subject_ref",
    91	    "subject_digest",
    92	    "subject_manifest_digest",
    93	    "core_sdlc_trace_ref",
    94	    "verdict",
    95	    "open_finding_refs",
    96	    "resolved_finding_refs",
    97	    "reconciliation_refs",
    98	    "evidence_refs",
    99	    "limitations",
   100	    "producer_service_id",
   101	    "produced_at",
   102	    "digest"
   103	  ],
   104	  "title": "review_verdict",
   105	  "type": "object",
   106	  "x-ranex-canonical-producer": "analytical_review",
   107	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   108	  "x-ranex-template": "docs/architecture/templates/REVIEW_VERDICT.yaml"
   109	}
     1	{
     2	  "$id": "https://schemas.ranex.dev/review/review-request-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "absolute_deadline": {
     7	      "type": "string",
     8	      "x-ranex-runtime-format": "date-time"
     9	    },
    10	    "artifact_type": {
    11	      "const": "review_request"
    12	    },
    13	    "blind_context_manifest_digest": {
    14	      "type": "string",
    15	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    16	    },
    17	    "core_sdlc_trace_ref": {
    18	      "type": "string"
    19	    },
    20	    "digest": {
    21	      "type": "string",
    22	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    23	    },
    24	    "maker": {
    25	      "additionalProperties": false,
    26	      "properties": {
    27	        "principal_id": {
    28	          "type": "string"
    29	        },
    30	        "role_id": {
    31	          "type": "string"
    32	        },
    33	        "run_id": {
    34	          "type": "string"
    35	        },
    36	        "session_id": {
    37	          "type": "string"
    38	        }
    39	      },
    40	      "required": [
    41	        "principal_id",
    42	        "role_id",
    43	        "run_id",
    44	        "session_id"
    45	      ],
    46	      "type": "object"
    47	    },
    48	    "packet_digest": {
    49	      "type": "string",
    50	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    51	    },
    52	    "packet_id": {
    53	      "type": "string"
    54	    },
    55	    "prohibited_capabilities": {
    56	      "items": {
    57	        "type": "string"
    58	      },
    59	      "type": "array"
    60	    },
    61	    "qualification_policy_id": {
    62	      "type": "string"
    63	    },
    64	    "request_id": {
    65	      "type": "string"
    66	    },
    67	    "required_independence": {
    68	      "items": {},
    69	      "type": "array"
    70	    },
    71	    "required_reviewer_role_id": {
    72	      "type": "string"
    73	    },
    74	    "required_route_fact_diversity": {
    75	      "items": {},
    76	      "type": "array"
    77	    },
    78	    "review_spec_id": {
    79	      "type": "string"
    80	    },
    81	    "review_spec_version": {
    82	      "type": "string"
    83	    },
    84	    "schema_version": {
    85	      "const": "1"
    86	    },
    87	    "subject_digest": {
    88	      "type": "string",
    89	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    90	    },
    91	    "subject_manifest_digest": {
    92	      "type": [
    93	        "string",
    94	        "null"
    95	      ]
    96	    },
    97	    "subject_ref": {
    98	      "type": "string"
    99	    },
   100	    "subject_schema": {
   101	      "type": [
   102	        "string",
   103	        "null"
   104	      ]
   105	    }
   106	  },
   107	  "required": [
   108	    "schema_version",
   109	    "artifact_type",
   110	    "request_id",
   111	    "review_spec_id",
   112	    "review_spec_version",
   113	    "packet_id",
   114	    "packet_digest",
   115	    "subject_schema",
   116	    "subject_ref",
   117	    "subject_digest",
   118	    "subject_manifest_digest",
   119	    "core_sdlc_trace_ref",
   120	    "maker",
   121	    "required_reviewer_role_id",
   122	    "required_independence",
   123	    "prohibited_capabilities",
   124	    "blind_context_manifest_digest",
   125	    "required_route_fact_diversity",
   126	    "qualification_policy_id",
   127	    "absolute_deadline",
   128	    "digest"
   129	  ],
   130	  "title": "review_request",
   131	  "type": "object",
   132	  "x-ranex-canonical-producer": "analytical_review",
   133	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   134	  "x-ranex-template": "docs/architecture/templates/REVIEW_REQUEST.yaml"
   135	}

exec
/bin/bash -lc "rg -n \"control|assessment|observation|finding|evidence|confidence|effectiveness|obligation|requirement\" docs/architecture/SDLC_CONTROL_CATALOG.md docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml schemas/process/capability-assessment-v1.schema.json schemas/assurance/evidence-snapshot-v1.schema.json 2>/dev/null | head -n 280
nl -ba docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml
nl -ba schemas/process/capability-assessment-v1.schema.json | sed -n '1,280p'
nl -ba schemas/assurance/evidence-snapshot-v1.schema.json | sed -n '1,260p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
schemas/assurance/evidence-snapshot-v1.schema.json:2:  "$id": "https://schemas.ranex.dev/assurance/evidence-snapshot-v1.schema.json",
schemas/assurance/evidence-snapshot-v1.schema.json:7:      "const": "evidence_snapshot"
schemas/assurance/evidence-snapshot-v1.schema.json:31:    "eligible_evidence_refs": {
schemas/assurance/evidence-snapshot-v1.schema.json:38:    "ineligible_evidence": {
schemas/assurance/evidence-snapshot-v1.schema.json:42:          "evidence_ref": {
schemas/assurance/evidence-snapshot-v1.schema.json:50:          "evidence_ref",
schemas/assurance/evidence-snapshot-v1.schema.json:110:    "eligible_evidence_refs",
schemas/assurance/evidence-snapshot-v1.schema.json:111:    "ineligible_evidence",
schemas/assurance/evidence-snapshot-v1.schema.json:120:  "title": "evidence_snapshot",
schemas/process/capability-assessment-v1.schema.json:2:  "$id": "https://schemas.ranex.dev/process/capability-assessment-v1.schema.json",
schemas/process/capability-assessment-v1.schema.json:65:      "const": "capability_assessment"
schemas/process/capability-assessment-v1.schema.json:67:    "assessment_authority": {
schemas/process/capability-assessment-v1.schema.json:80:        "independence_evidence_ref": {
schemas/process/capability-assessment-v1.schema.json:87:        "independence_evidence_ref",
schemas/process/capability-assessment-v1.schema.json:92:    "assessment_id": {
schemas/process/capability-assessment-v1.schema.json:101:        "criterion_evidence": {
schemas/process/capability-assessment-v1.schema.json:108:              "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:118:              "evidence_refs",
schemas/process/capability-assessment-v1.schema.json:146:        "criterion_evidence",
schemas/process/capability-assessment-v1.schema.json:152:    "confidence": {
schemas/process/capability-assessment-v1.schema.json:201:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:211:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:218:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:228:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:235:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:245:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:252:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:262:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:269:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:279:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:286:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:296:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:303:                "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:313:                "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:385:    "definition_evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:396:    "effectiveness": {
schemas/process/capability-assessment-v1.schema.json:438:    "evidence": {
schemas/process/capability-assessment-v1.schema.json:459:        "evidence_snapshot_refs": {
schemas/process/capability-assessment-v1.schema.json:483:        "evidence_snapshot_refs",
schemas/process/capability-assessment-v1.schema.json:494:    "findings": {
schemas/process/capability-assessment-v1.schema.json:537:              "disposition_evidence_ref": {
schemas/process/capability-assessment-v1.schema.json:559:              "disposition_evidence_ref"
schemas/process/capability-assessment-v1.schema.json:616:        "causal_control_id": {
schemas/process/capability-assessment-v1.schema.json:625:        "effectiveness_review_ref": {
schemas/process/capability-assessment-v1.schema.json:628:        "evidence_window_end": {
schemas/process/capability-assessment-v1.schema.json:658:        "causal_control_id",
schemas/process/capability-assessment-v1.schema.json:664:        "evidence_window_end",
schemas/process/capability-assessment-v1.schema.json:667:        "effectiveness_review_ref",
schemas/process/capability-assessment-v1.schema.json:791:            "zero_claim_evidence_ref": {
schemas/process/capability-assessment-v1.schema.json:802:            "zero_claim_evidence_ref",
schemas/process/capability-assessment-v1.schema.json:1006:            "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:1032:            "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:1086:    "prior_assessment_ref": {
schemas/process/capability-assessment-v1.schema.json:1117:              "evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:1131:              "evidence_refs"
schemas/process/capability-assessment-v1.schema.json:1172:            "validation_evidence_refs": {
schemas/process/capability-assessment-v1.schema.json:1180:            "validation_evidence_refs"
schemas/process/capability-assessment-v1.schema.json:1224:        "control_id": {
schemas/process/capability-assessment-v1.schema.json:1258:        "control_id",
schemas/process/capability-assessment-v1.schema.json:1293:    "assessment_id",
schemas/process/capability-assessment-v1.schema.json:1297:    "definition_evidence_refs",
schemas/process/capability-assessment-v1.schema.json:1308:    "assessment_authority",
schemas/process/capability-assessment-v1.schema.json:1311:    "evidence",
schemas/process/capability-assessment-v1.schema.json:1313:    "effectiveness",
schemas/process/capability-assessment-v1.schema.json:1317:    "confidence",
schemas/process/capability-assessment-v1.schema.json:1319:    "findings",
schemas/process/capability-assessment-v1.schema.json:1323:    "prior_assessment_ref",
schemas/process/capability-assessment-v1.schema.json:1329:  "title": "capability_assessment",
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:4:# One record assesses one exact control or named capability for one immutable
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:8:artifact_type: capability_assessment
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:9:assessment_id: "capability_assessment_<uuidv7>"
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:12:definition_status: DEFINED # DEFINED means the control contract exists; it is not a runtime score.
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:13:definition_evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:27:  control_id: "" # Required for a VITAL-SDLC-001 member assessment.
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:36:assessment_authority:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:39:  independence_evidence_ref: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:88:    evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:154:evidence:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:157:  evidence_snapshot_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:171:  criterion_evidence:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:173:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:178:effectiveness:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:208:    zero_claim_evidence_ref: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:235:# One register owns every evidence, population, coverage, measurement, and
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:246:      disposition_evidence_ref: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:256:confidence:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:265:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:268:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:271:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:274:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:277:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:280:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:283:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:300:      evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:304:    validation_evidence_refs: []
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:316:findings:
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:326:  causal_control_id: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:332:  evidence_window_end: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:335:  effectiveness_review_ref: ""
docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:340:prior_assessment_ref: ""
docs/architecture/SDLC_CONTROL_CATALOG.md:13:| Compatibility/migration class | New control catalog; older phases are inputs to a versioned crosswalk |
docs/architecture/SDLC_CONTROL_CATALOG.md:14:| Security/data class | Public control metadata; referenced evidence retains its own classification |
docs/architecture/SDLC_CONTROL_CATALOG.md:19:control IDs, common evidence systems, complete stage contracts, rejection
docs/architecture/SDLC_CONTROL_CATALOG.md:20:routes, tailoring rules, and source/evidence classifications.
docs/architecture/SDLC_CONTROL_CATALOG.md:24:appraisal. Adoption-gate evidence reports implementation maturity separately.
docs/architecture/SDLC_CONTROL_CATALOG.md:32:| `OBS` | Repeated observational industry research |
docs/architecture/SDLC_CONTROL_CATALOG.md:34:| `MODEL` | Capability/maturity assessment model |
docs/architecture/SDLC_CONTROL_CATALOG.md:35:| `OWNER` | Ranex owner requirement or design choice |
docs/architecture/SDLC_CONTROL_CATALOG.md:37:Major controls cite one or more classes. Evidence-informed does not mean
docs/architecture/SDLC_CONTROL_CATALOG.md:40:## 3. Cross-lifecycle control systems
docs/architecture/SDLC_CONTROL_CATALOG.md:57:capacity, cost, requirement or risk change requires human recommitment.
docs/architecture/SDLC_CONTROL_CATALOG.md:68:An estimate is an immutable uncertainty observation, never a promise. It names
docs/architecture/SDLC_CONTROL_CATALOG.md:69:one exact subject, unit, range, assumptions, method, evidence, and the capacity
docs/architecture/SDLC_CONTROL_CATALOG.md:92:other passing controls can make a missing, stale, cross-subject, expired,
docs/architecture/SDLC_CONTROL_CATALOG.md:98:estimate_commitment_control:
docs/architecture/SDLC_CONTROL_CATALOG.md:99:  control_id: "SDLC-EST-001"
docs/architecture/SDLC_CONTROL_CATALOG.md:100:  control_version: "1.1.0"
docs/architecture/SDLC_CONTROL_CATALOG.md:103:  contract_projection_ref: "architecture/contracts/estimate-commitment-control.json"
docs/architecture/SDLC_CONTROL_CATALOG.md:119:    entry_rule: "entries[0] is the complete estimate_commitment_control mapping from this marked source block, including this projection contract; source_digest is computed over the exact UTF-8 YAML payload between the markers and is therefore outside entries."
docs/architecture/SDLC_CONTROL_CATALOG.md:191:      fields: ["evidence_ref", "evidence_digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:193:        evidence_ref: "safe_id_or_registered_urn"
docs/architecture/SDLC_CONTROL_CATALOG.md:194:        evidence_digest: "sha256"
docs/architecture/SDLC_CONTROL_CATALOG.md:214:    schema_ref: "schemas/planning/estimate-observation-v1.schema.json"
docs/architecture/SDLC_CONTROL_CATALOG.md:216:    fields: ["schema_version", "record_type", "estimate_id", "work_item_id", "subject_schema", "subject_ref", "subject_digest", "estimate_kind", "unit", "lower_bound", "most_likely", "upper_bound", "confidence", "method_ref", "assumptions", "evidence_bindings", "capacity_snapshot_ref", "capacity_snapshot_digest", "dependency_snapshot_ref", "dependency_snapshot_digest", "prepared_by_principal_id", "observed_at", "valid_until", "supersedes_estimate_id", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:230:      confidence: {enum: ["UNKNOWN", "LOW", "MEDIUM", "HIGH"]}
docs/architecture/SDLC_CONTROL_CATALOG.md:233:      evidence_bindings: "EstimateEvidenceBindingV1[]"
docs/architecture/SDLC_CONTROL_CATALOG.md:246:      evidence_bindings: "1..N"
docs/architecture/SDLC_CONTROL_CATALOG.md:249:      evidence_bindings: "BYTEWISE_EVIDENCE_REF"
docs/architecture/SDLC_CONTROL_CATALOG.md:255:      - "An estimate is CURRENT at a trusted instant only when observed_at <= instant < valid_until and no later admitted estimate names it in supersedes_estimate_id. A non-null supersedes_estimate_id names exactly one earlier-admitted estimate in the same derived series and work_item; observation/admission time strictly increases and each series graph is single-predecessor, single-successor, and acyclic."
docs/architecture/SDLC_CONTROL_CATALOG.md:256:      - "assumptions and evidence_bindings are exact duplicate-free bytewise sets; their received order must already be canonical."
docs/architecture/SDLC_CONTROL_CATALOG.md:257:      - "subject, capacity, dependency, method, preparer provenance, and every evidence binding independently resolve by exact ref and digest for the same work item and observation time."
docs/architecture/SDLC_CONTROL_CATALOG.md:264:    rationale: "The former ESTIMATE role was an ungoverned list of EstimateObservationV1 rows. V2 is a closed content-addressed registry that also carries the complete reservation history and exact method, evidence, and preparer authorities. No list-to-registry coercion is permitted."
docs/architecture/SDLC_CONTROL_CATALOG.md:327:      admission_causality: "A row cannot be admitted before the observation, authentication, reservation, or external-artifact registration instants it binds. A commitment decision issued_at is strictly later than every predecision estimate/source observation, estimate admission, owner assignment, trace observation, and decision authentication instant and no later than the trusted TIME instant. Its own decision-artifact registration occurs at or after issued_at and no later than the trusted instant."
docs/architecture/SDLC_CONTROL_CATALOG.md:354:      - {type_id: "EstimateEvidenceAuthorityRowV1", pointer_field: "supersedes_evidence_row_digest", predecessor_key: "digest", partition_key: "work_item_id + evidence_id", chronology_field: "observed_at"}
docs/architecture/SDLC_CONTROL_CATALOG.md:363:      - {type_id: "TrustedTimeObservationV1", pointer_field: "previous_observation_digest", predecessor_key: "digest", partition_key: "trusted_source_id", chronology_field: "monotonic_counter and instant"}
docs/architecture/SDLC_CONTROL_CATALOG.md:371:        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "reservation_history", "method_rows", "evidence_rows", "preparer_rows", "estimate_rows", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:385:          evidence_rows: "EstimateEvidenceAuthorityRowV1[]"
docs/architecture/SDLC_CONTROL_CATALOG.md:392:          evidence_rows: "1..N"
docs/architecture/SDLC_CONTROL_CATALOG.md:397:          evidence_rows: "BYTEWISE_EVIDENCE_REF"
docs/architecture/SDLC_CONTROL_CATALOG.md:403:          - "Every EstimateObservationV1 resolves exactly one method row, one preparer row for prepared_by_principal_id, and every evidence binding from this same complete registry."
docs/architecture/SDLC_CONTROL_CATALOG.md:404:          - "The V2 object shape is mandatory. A raw EstimateObservationV1 array, a V1 wrapper, a mixed registry, or synthesized method/evidence/preparer/reservation authority fails."
docs/architecture/SDLC_CONTROL_CATALOG.md:662:        schema_ref: "schemas/planning/estimate-evidence-authority-row-v1.schema.json"
docs/architecture/SDLC_CONTROL_CATALOG.md:664:        fields: ["schema_version", "record_type", "evidence_id", "evidence_version", "evidence_ref", "work_item_id", "artifact_ref", "artifact_digest", "media_type", "observed_at", "valid_until", "supersedes_evidence_row_digest", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:668:          evidence_id: "safe_id"
docs/architecture/SDLC_CONTROL_CATALOG.md:669:          evidence_version: "positive_integer"
docs/architecture/SDLC_CONTROL_CATALOG.md:670:          evidence_ref: "safe_id_or_registered_urn"
docs/architecture/SDLC_CONTROL_CATALOG.md:677:          supersedes_evidence_row_digest: "sha256|null"
docs/architecture/SDLC_CONTROL_CATALOG.md:679:        nullable_fields: ["supersedes_evidence_row_digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:681:        self_reference_rule: "evidence_ref equals urn:ranex:estimate-evidence:<evidence_id>:<evidence_version>:<artifact_digest-without-prefix>:<digest-without-prefix>; digest excludes evidence_ref and digest."
docs/architecture/SDLC_CONTROL_CATALOG.md:682:        invariant: "EstimateEvidenceBindingV1.evidence_digest equals this row digest, not merely artifact_digest. The row and artifact must be exact and valid for the same work item at estimate observed_at. A successor keeps evidence_id, strictly increases evidence_version and observed_at, and names the immediate prior row digest."
docs/architecture/SDLC_CONTROL_CATALOG.md:752:        fields: ["schema_version", "record_type", "scope_id", "scope_version", "work_item_id", "scope_ref", "requirement_ids", "acceptance_criterion_ids", "included_configuration_item_bindings", "excluded_configuration_item_bindings", "scope_definition_ref", "scope_definition_digest", "observed_at", "valid_until", "supersedes_scope_id", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:760:          requirement_ids: "safe_id[]"
docs/architecture/SDLC_CONTROL_CATALOG.md:772:          requirement_ids: "1..N"
docs/architecture/SDLC_CONTROL_CATALOG.md:777:          requirement_ids: "BYTEWISE_ID"
docs/architecture/SDLC_CONTROL_CATALOG.md:784:          - "Included and excluded configuration-item sets are disjoint; requirement, acceptance, content-addressed configuration-item, and definition bindings are exact business scope, not descriptive shell metadata."
docs/architecture/SDLC_CONTROL_CATALOG.md:998:        schema_ref: "schemas/planning/trusted-time-observation-v1.schema.json"
docs/architecture/SDLC_CONTROL_CATALOG.md:1000:        fields: ["schema_version", "record_type", "time_observation_id", "trusted_source_id", "source_ref", "source_digest", "instant", "uncertainty_milliseconds", "maximum_age_milliseconds", "monotonic_counter", "previous_observation_digest", "attested_at", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:1004:          time_observation_id: "safe_id"
docs/architecture/SDLC_CONTROL_CATALOG.md:1012:          previous_observation_digest: "sha256|null"
docs/architecture/SDLC_CONTROL_CATALOG.md:1015:        nullable_fields: ["previous_observation_digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:1019:          - "The accepted row is the unique latest row for trusted_source_id; monotonic_counter and instant strictly increase, previous_observation_digest names the unique immediate predecessor, and the chain is complete, single-successor, and acyclic."
docs/architecture/SDLC_CONTROL_CATALOG.md:1035:          - "Obtain method, evidence, preparer, reservation-history, and every role authority row from its canonical owner. A migrator cannot infer or synthesize them from an estimate."
docs/architecture/SDLC_CONTROL_CATALOG.md:1036:          - "A preserved estimate migrates only when its existing method_ref and evidence bindings already resolve the exact new authority rows without changing a byte. Otherwise the migrator retains that row as non-authoritative history and a human-authorized producer issues a new EstimateObservationV1 with a globally new reserved estimate_id; silent ref or digest rewriting is forbidden."
docs/architecture/SDLC_CONTROL_CATALOG.md:1038:          - "After V2 publication, V1 input remains rejected and immutable migration evidence is retained."
docs/architecture/SDLC_CONTROL_CATALOG.md:1104:      - "issued_at is at or after commitment_window_start, strictly later than every predecision bound estimate observed/admitted instant and source observation, owner assignment, trace observation, and authentication instant, and no later than the accepted trusted TIME instant; its artifact registration is at or after issued_at and no later than that trusted instant. expires_at equals commitment_window_end and revoked_at is JSON null."
docs/architecture/SDLC_CONTROL_CATALOG.md:1109:      - "It cannot change a WorkItem state, manufacture gate PASS, issue an AuthorityGrant or Permit, waive evidence, land code, release, or prove delivery."
docs/architecture/SDLC_CONTROL_CATALOG.md:1119:    query_requirement_matrix:
docs/architecture/SDLC_CONTROL_CATALOG.md:1121:        registry_requirements: "All eleven closed authenticated registry objects and their complete histories are present and valid."
docs/architecture/SDLC_CONTROL_CATALOG.md:1122:        selected_row_requirements: ["CAPACITY", "DEPENDENCY", "ESTIMATE", "SCOPE", "TIME"]
docs/architecture/SDLC_CONTROL_CATALOG.md:1127:        registry_requirements: "All eleven closed authenticated registry objects and their complete histories are present and valid."
docs/architecture/SDLC_CONTROL_CATALOG.md:1128:        selected_row_requirements: ["ACCEPTANCE", "CAPACITY", "DECISION", "DEPENDENCY", "ESTIMATE", "OWNER", "PLAN", "RISK", "SCOPE", "TIME", "TRACE"]
docs/architecture/SDLC_CONTROL_CATALOG.md:1132:      rule: "The matrix prevents a circular requirement for a plan or decision before an estimate can be inspected while still validating the estimate's exact scope, capacity, dependency, method, evidence, preparer, reservation, and time authorities. Permitted absence means no selected row for this work item; it never permits a missing registry, malformed history, stale selected estimate binding, or favorable caller subset."
docs/architecture/SDLC_CONTROL_CATALOG.md:1222:      method_evidence_and_preparer:
docs/architecture/SDLC_CONTROL_CATALOG.md:1404:distinction; `STD` ISO/IEC 29110 planning and control; `GOV`
docs/architecture/SDLC_CONTROL_CATALOG.md:1405:NASA-HDBK-2203 project planning/control; `OWNER` Ranex exact-subject and
docs/architecture/SDLC_CONTROL_CATALOG.md:1412:- needs, requirements, decisions, ADRs and contracts;
docs/architecture/SDLC_CONTROL_CATALOG.md:1418:- runbooks, user/operator documentation, findings and waivers; and
docs/architecture/SDLC_CONTROL_CATALOG.md:1425:3. applies authorized change control;
docs/architecture/SDLC_CONTROL_CATALOG.md:1430:8. reconciles emergency changes into normal control.
docs/architecture/SDLC_CONTROL_CATALOG.md:1432:`RELEASE_READY` requires evidence that requirements, source, build inputs,
docs/architecture/SDLC_CONTROL_CATALOG.md:1443:need/outcome <-> software requirement
docs/architecture/SDLC_CONTROL_CATALOG.md:1444:requirement <-> risk/hazard/misuse control
docs/architecture/SDLC_CONTROL_CATALOG.md:1445:requirement <-> design component
docs/architecture/SDLC_CONTROL_CATALOG.md:1447:requirement <-> verification and validation evidence
docs/architecture/SDLC_CONTROL_CATALOG.md:1448:requirement <-> defect/nonconformance/waiver
docs/architecture/SDLC_CONTROL_CATALOG.md:1452:extra-element checks. Changing a source marks dependent links/evidence stale
docs/architecture/SDLC_CONTROL_CATALOG.md:1459:- **Verification** proves specified requirements/design were implemented
docs/architecture/SDLC_CONTROL_CATALOG.md:1463:Every record names need/requirement, exact subject, verifier, method,
docs/architecture/SDLC_CONTROL_CATALOG.md:1465:anomaly/waiver, date and durable evidence. Acceptance names the version,
docs/architecture/SDLC_CONTROL_CATALOG.md:1490:  exit requirements;
docs/architecture/SDLC_CONTROL_CATALOG.md:1496:- reassessment date and residual-risk authority.
docs/architecture/SDLC_CONTROL_CATALOG.md:1498:An SBOM is evidence, not acceptance by itself.
docs/architecture/SDLC_CONTROL_CATALOG.md:1517:omitted or modified controls, rationale, compensating controls, approver,
docs/architecture/SDLC_CONTROL_CATALOG.md:1520:Truthfulness, exact-subject evidence, traceability, evidence integrity, legal
docs/architecture/SDLC_CONTROL_CATALOG.md:1533:owner, cadence, baseline/control limit, paired guardrail, retention, triggered
docs/architecture/SDLC_CONTROL_CATALOG.md:1542:The catalog covers outcome, flow, DORA delivery measures, requirement
docs/architecture/SDLC_CONTROL_CATALOG.md:1544:effectiveness, configuration drift, dependencies/maintenance, supplier
docs/architecture/SDLC_CONTROL_CATALOG.md:1550:qualification evidence, repeatability/data-quality tests, and an
docs/architecture/SDLC_CONTROL_CATALOG.md:1556:### SDLC-MEA-002 — Capability assessment and improvement selection
docs/architecture/SDLC_CONTROL_CATALOG.md:1560:Capability assessment is diagnostic and evidence-bound. The assessment unit is
docs/architecture/SDLC_CONTROL_CATALOG.md:1561:one normative control or named capability for a declared value stream/service,
docs/architecture/SDLC_CONTROL_CATALOG.md:1571:- effectiveness: `UNKNOWN`, `REGRESSING`, `MIXED`, or `MEETS_TARGET`;
docs/architecture/SDLC_CONTROL_CATALOG.md:1574:- confidence: `LOW`, `MEDIUM`, or `HIGH`, with sample, duration,
docs/architecture/SDLC_CONTROL_CATALOG.md:1582:A numeric level requires criterion evidence for that level and every lower
docs/architecture/SDLC_CONTROL_CATALOG.md:1584:evidence includes a normal path and at least one rejection, invalidation,
docs/architecture/SDLC_CONTROL_CATALOG.md:1589:evidence. Level `4` requires a prospectively frozen improvement experiment
docs/architecture/SDLC_CONTROL_CATALOG.md:1597:Failed required tests and disabled safeguards remain non-compensating findings.
docs/architecture/SDLC_CONTROL_CATALOG.md:1611:| `APP-CROSS-001` | Cross-lifecycle control applies to every material in-scope work item |
docs/architecture/SDLC_CONTROL_CATALOG.md:1612:| `APP-STAGE-001` | Stage control applies when eligible work entered or should have entered that canonical state |
docs/architecture/SDLC_CONTROL_CATALOG.md:1613:| `APP-TRIGGER-001` | Linked maintenance, retirement, exception, rollback, supplier, or similar control applies when its declared trigger exists |
docs/architecture/SDLC_CONTROL_CATALOG.md:1614:| `APP-FORK-BASE-001` | Persistent fork ancestry, inherited-behavior, compatibility/integration-surface, and reconciliation controls apply to Ranex in every review window |
docs/architecture/SDLC_CONTROL_CATALOG.md:1615:| `APP-FORK-SYNC-001` | Upstream-sync control applies when an observation/cadence obligation, candidate, classification, disposition, port, or baseline decision is due or exists in-window |
docs/architecture/SDLC_CONTROL_CATALOG.md:1616:| `APP-FORK-UPDATE-001` | Release/update control applies when an update obligation, candidate, staged change, activation, or recovery exists in-window |
docs/architecture/SDLC_CONTROL_CATALOG.md:1617:| `APP-FORK-CUTOVER-001` | Cutover/self-development control applies when an operating-mode, canonical-writer, controller/candidate, or cutover obligation/change exists in-window |
docs/architecture/SDLC_CONTROL_CATALOG.md:1618:| `APP-AIW-001` | AI-worker fleet controls apply whenever more than one agent/worker is dispatched or fleet machinery affects evidence, selection, landing, or authority |
docs/architecture/SDLC_CONTROL_CATALOG.md:1620:Vital-control profile `VITAL-SDLC-001`, version `1.2.0`, is owned by the human
docs/architecture/SDLC_CONTROL_CATALOG.md:1625:`(domain_id, control_id, applicability_rule_id)` tuples. Each tuple has exactly
docs/architecture/SDLC_CONTROL_CATALOG.md:1626:one rule, so assessment authors never choose an `AND`/`OR` interpretation.
docs/architecture/SDLC_CONTROL_CATALOG.md:1673:A domain projection binds one immutable assessment ID, revision, and digest for
docs/architecture/SDLC_CONTROL_CATALOG.md:1686:applicable member and never enters the level floor. An applicable assessment
docs/architecture/SDLC_CONTROL_CATALOG.md:1708:assurance sign-off. Without an approved adequacy rule, confidence is at most
docs/architecture/SDLC_CONTROL_CATALOG.md:1709:`MEDIUM`; a material unresolved population/evidence gap forces `LOW`. One gap
docs/architecture/SDLC_CONTROL_CATALOG.md:1710:register inventories evidence, applicability, population, coverage and
docs/architecture/SDLC_CONTROL_CATALOG.md:1714:rating `UNKNOWN` with no level and confidence `LOW`; it cannot coexist with a
docs/architecture/SDLC_CONTROL_CATALOG.md:1726:“class” list. At minimum they distinguish failed control/execution outcomes,
docs/architecture/SDLC_CONTROL_CATALOG.md:1734:applicable assessment. Evaluate tiers in `P0 -> P1 -> P2 -> P3` order; the
docs/architecture/SDLC_CONTROL_CATALOG.md:1738:  invariant/truth/authority/evidence/recovery breach;
docs/architecture/SDLC_CONTROL_CATALOG.md:1740:  overdue critical obligation, repeated escape, high-exposure downstream
docs/architecture/SDLC_CONTROL_CATALOG.md:1741:  blockage, or `LOW`-confidence instrumentation need;
docs/architecture/SDLC_CONTROL_CATALOG.md:1743:  `UNKNOWN`/`REGRESSING`/`MIXED` effectiveness, material
docs/architecture/SDLC_CONTROL_CATALOG.md:1747:  guardrails, no adverse trend, and confidence above `LOW`.
docs/architecture/SDLC_CONTROL_CATALOG.md:1759:assessment. `P3_CRITERIA_UNPROVEN` and `P3_ALL_CRITERIA_PROVEN` are mutually
docs/architecture/SDLC_CONTROL_CATALOG.md:1764:capability gap determine order. `LOW` confidence selects P1 and requires a
docs/architecture/SDLC_CONTROL_CATALOG.md:1765:linked instrumentation/sampling action. A valid all-N/A assessment has no
docs/architecture/SDLC_CONTROL_CATALOG.md:1769:The per-control assessment record includes assessor/approver independence,
docs/architecture/SDLC_CONTROL_CATALOG.md:1772:digests and counts; N/A disposition/audit; event/evidence digest; criterion
docs/architecture/SDLC_CONTROL_CATALOG.md:1773:evidence; measures/baseline/comparator; all seven named confidence-adequacy
docs/architecture/SDLC_CONTROL_CATALOG.md:1774:tests and sign-off; invariant findings; exceptions; derived priority;
docs/architecture/SDLC_CONTROL_CATALOG.md:1779:A linked improvement record names causal stage/control, hypothesis, bounded
docs/architecture/SDLC_CONTROL_CATALOG.md:1787:improvement record carries its owner, evidence window, stop/revert criteria and
docs/architecture/SDLC_CONTROL_CATALOG.md:1792:[`capability-assessment-v1.schema.json`](../../schemas/process/capability-assessment-v1.schema.json)
docs/architecture/SDLC_CONTROL_CATALOG.md:1801:cannot default to zero. An established zero floor requires method evidence and
docs/architecture/SDLC_CONTROL_CATALOG.md:1807:permit, waive a control, lower risk, convert missing/failing evidence into
docs/architecture/SDLC_CONTROL_CATALOG.md:1833:  [`architecture-rule-assessments.json`](../../architecture/contracts/architecture-rule-assessments.json);
docs/architecture/SDLC_CONTROL_CATALOG.md:1834:- the 41 generated per-control records and ten deterministic domain projections
docs/architecture/SDLC_CONTROL_CATALOG.md:1835:  under [`assessments/`](./assessments/); and
docs/architecture/SDLC_CONTROL_CATALOG.md:1842:validator cannot observe an empty assessment denominator, that a second writer
docs/architecture/SDLC_CONTROL_CATALOG.md:1845:Every generated control record separates `definition_status: DEFINED` from the
docs/architecture/SDLC_CONTROL_CATALOG.md:1847:`UNKNOWN` while applicability and runtime evidence remain unresolved. These
docs/architecture/SDLC_CONTROL_CATALOG.md:1849:scores, operating evidence, or adoption-gate passes. Runtime producer
docs/architecture/SDLC_CONTROL_CATALOG.md:1855:Evidence basis: `OBS` DORA system measures; `MODEL` CMMI assessment lens;
docs/architecture/SDLC_CONTROL_CATALOG.md:1860:The process is itself controlled:
docs/architecture/SDLC_CONTROL_CATALOG.md:1863:proposal -> pilot -> evidence review -> human approval
docs/architecture/SDLC_CONTROL_CATALOG.md:1864:  -> versioned rollout/training -> conformance/effectiveness review
docs/architecture/SDLC_CONTROL_CATALOG.md:1871:action and verifies effectiveness. Quarterly management review examines
docs/architecture/SDLC_CONTROL_CATALOG.md:1874:Competence profiles and qualification evidence exist for maker, reviewer, V&V,
docs/architecture/SDLC_CONTROL_CATALOG.md:1886:| Control/state | Purpose and precondition | Required inputs | Mandatory activities | Required outputs/evidence | R / A / C / I | Automated + human exit gates | Rejection/recovery | Tailoring and measures | Basis |
docs/architecture/SDLC_CONTROL_CATALOG.md:1888:| `SDLC-INT-001` `FUNNEL` | Preserve a signal; source exists | User/stakeholder feedback, alert, incident, vulnerability, strategy or upstream observation | Assign ID; capture source/date/scope without inventing facts | Immutable signal record | Intake / duty owner / affected owner / reporter | Schema/duplicate/privacy scan + owner acknowledgment | Malformed/sensitive input quarantined; out-of-scope routed or cancelled | Summary may be minimal; measure intake age/source | `STD`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1890:| `SDLC-DIS-001` `DISCOVERY` | Validate problem/value; triaged item | Signal, users/actors, current behavior, research access | Research current behavior/users, baseline, alternatives, hypothesis, unknowns and falsifier | Discovery packet and evidence register | Research/product / product owner / technical, service, data / stakeholders | Evidence/source/unknown checks + product decision | Weak evidence → Discovery/Funnel/Cancelled | Standard fixes may use reproduction as discovery; measure learning time/hypothesis yield | `PRAC`,`OBS`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1891:| `SDLC-DEF-001` `DEFINITION` | State testable need; supported problem | Discovery packet, constraints, policies | Define outcome, requirements, examples, qualities, non-goals, failure/misuse/recovery, measures; validate with affected user/owner | Baselined requirements and traceability | Requirements role / product owner / technical, V&V, service, security/data / delivery | Schema/orphan/testability checks + product/affected-owner validation | Ambiguous/unverifiable → Discovery/Definition | Artifact length varies, traceability does not; volatility and validation defects | `STD`,`GOV`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1893:| `SDLC-PLN-001` `READY` | Make responsible commitment; accepted design | Integrated scope, design, estimates, capacity, dependencies/risks | Slice vertically; estimate range; forecast; resource; plan evidence/configuration/acceptance; bind tailoring | Integrated delivery plan, task/decision inputs, DoR proof | Delivery/planner / delivery owner / product, technical, V&V, service / stakeholders | Completeness/dependency/capacity checks + human commitment | Infeasible → Design/Triage; blocking dependency → Blocked | No mandatory points; lead time, forecast calibration, readiness escapes | `STD`,`MODEL`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1895:| `SDLC-VER-001` `VERIFICATION` | Verify and validate exact subject; candidate exists | Candidate, requirements/design, V&V plan, qualified environment | Independent review; test portfolio; security/data/compatibility/recovery; anomaly disposition; representative validation | Review, checker, V&V, acceptance and anomaly records | V&V/reviewers / independent V&V authority + product validator / maker, technical, service, security / release | Exact-subject deterministic gates + independent human/product acceptance by lane | Fail → Build/Design/Definition; environment invalid → re-run | Independence may only increase; effectiveness, leakage, flake, latency | `GOV`,`PRAC`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1898:| `SDLC-OPS-001` `OPERATING` | Establish supported healthy service; released subject | Release record, SLO/measurement/support/runbooks | Observe window; support; reconcile; scan; backup/restore; capacity/cost review | Operational acceptance, health/security/support evidence | Service/operations / service owner / product, security, supplier / users | Telemetry/reconciliation/backup checks + service-owner acceptance | Failure opens an incident and linked `INCIDENT_RESPONSE` work; uncertainty extends observation | SLO may be Unknown with plan; reliability/support measures | `GOV`,`PRAC`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1899:| `SDLC-OUT-001` `OUTCOME_REVIEW` | Decide whether change helped; observation due | Hypothesis/baseline, product and ops evidence | Compare expected/actual, side effects and segments; decide keep/change/remove | Outcome decision and follow-up work | Product analytics / product owner / technical, service, users / portfolio | Data-quality check + human product decision | Falsified → `DISCOVERY` or linked `MAINTENANCE`/`RETIREMENT` work | Sampled only for standard lane; outcome/side-effect measures | `OBS`,`PRAC`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1900:| `SDLC-MNT-001` maintenance control | Keep a supported capability fit; maintenance trigger creates a linked work item | Supported-version policy, defects, debt, vulnerability/dependency/ops signals | Run corrective/adaptive/perfective/preventive work through `FUNNEL`–`CLOSED`; regress; patch; update docs/config baseline; release/observe normally | Maintained baseline, linked work item, disposition and release evidence | Maintenance / maintenance+service owner / product, V&V, supplier, security / users | Normal definition/design/V&V/release gates | Unsupported/unviable → linked retirement work; impact → incident record and emergency work item | No bypass for “existing” behavior; backlog age, freshness, debt interest | `STD`,`GOV`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1901:| `SDLC-RET-001` retirement control | End capability use/data/access safely; approved trigger creates a linked work item | Consumer/dependency inventory, retention/legal/privacy, replacement/export, recovery | Run retirement work through `FUNNEL`–`CLOSED`; notify; migrate/export; archive; revoke; delete/retain; teardown; observe; audit absence and retrieval | Capability-state transition, retirement permit/events, disposition proofs, independent audit, residual owner | Retirement operator / human governor / product, service, data/security, config / users | Inventory/data/access/archive automated checks + human approval and final audit | Failure leaves capability active/deprecated and opens recovery/incident work; incomplete teardown cannot become `RETIRED` | Retirement depth not tailorable for affected data/access; completion/exceptions | `GOV`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1902:| `SDLC-CLS-001` `CLOSED` | Reconcile work and release obligations; terminal evidence exists | Outcome/retirement decision, follow-ups, baselines | Verify ownership, archive, temporary access/flags/worktrees, debt and decisions; close project plan | Closure/acceptance record and retrievable evidence | Work/delivery / work owner / product, technical, service, config / stakeholders | Orphan/expiry/archive checks + accountable closure | Missing follow-up/evidence → prior state/Blocked | Merge never qualifies; end-to-end time, closure debt | `STD`,`MODEL`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1903:| `SDLC-BLK-001` `BLOCKED` | Preserve truth when safe progress is impossible; active item has a blocker | Current state/baseline, typed blocker, affected evidence and dependencies | Record reason, owner, entered time, impact, invalidation, escalation and next-decision date; age and review the blocker | Append-only blocked transition and decision/recovery evidence | Work/delivery / work owner / dependency and affected owners / stakeholders | Schema/age/escalation checks + accountable resume/disposition decision | Resume only to an allowed state with refreshed evidence; unresolved/unsafe remains blocked or receives authorized cancellation | No hidden parked work; blocker age/share, repeat causes, missed decision dates | `STD`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1904:| `SDLC-CAN-001` `CANCELLED` | End pre-release work without fabricating completion; authorized stop decision exists | Current state, reason, impact, evidence, temporary effects and obligations | Record authority/reason; preserve evidence; clean access/flags/worktrees; assign residual follow-up and notify affected owners | Cancellation decision, cleanup proof, retained record and owned follow-ups | Work/product / product or work owner / technical, service, security/data / stakeholders | Pre-release/state/authority/cleanup checks + human cancellation decision | Missing authority/cleanup → Blocked or prior state; rediscovery creates a linked new work item | Never reported as done/released; cancellation timing/reasons, residual cleanup and repeat discarded work | `STD`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1905:| `SDLC-RBK-001` `ROLLED_BACK` | Record a release reversal and prove the prior safe state; rollback initiated | Release/permit, exact artifact/destination, rollback plan, health/impact evidence | Execute authorized rollback; verify safe state; reconcile config/data/access; bound impact; open incident when applicable; create linked re-triage | Rollback events, safe-state proof, impact/reconciliation evidence, linked `TRIAGE` item and incident/action refs | Release/service / release + service owner / incident, product, security/data, configuration / stakeholders | Destination/digest/safe-state/reconciliation checks + release/service acceptance | Unverified recovery remains incident/rollback work; never return directly to normal release without new triage and qualification | Recovery distribution, rollback recurrence, reconciliation/action age | `GOV`,`PRAC`,`OWNER` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1915:| Ambiguous/unverifiable requirement | `DISCOVERY` or `DEFINITION` |
docs/architecture/SDLC_CONTROL_CATALOG.md:1925:| Process nonconformance | Corrective action; evidence stays failed/missing |
docs/architecture/SDLC_CONTROL_CATALOG.md:1928:evidence and next owner. Risk may be accepted within policy; factual failure,
docs/architecture/SDLC_CONTROL_CATALOG.md:1929:forged/missing evidence and stale exact-subject proof cannot be overridden.
docs/architecture/SDLC_CONTROL_CATALOG.md:1935:- requirements owner/business analyst;
docs/architecture/SDLC_CONTROL_CATALOG.md:1962:## 8. Hermes-fork specialized controls
docs/architecture/SDLC_CONTROL_CATALOG.md:1979:- the actual GitHub network-fork observation as a separate hosting fact.
docs/architecture/SDLC_CONTROL_CATALOG.md:1982:software derivation, Git ancestry, or license evidence. Failure or missing
docs/architecture/SDLC_CONTROL_CATALOG.md:1983:evidence keeps the gate `FAIL`, `UNKNOWN`, or `CONFLICT` and the architecture
docs/architecture/SDLC_CONTROL_CATALOG.md:2012:reason, owner, required evidence, and review deadline; resolution returns only
     1	# Authoring skeleton; executable schema is registered under schemas/.
     2	# Empty placeholders are invalid for SEALED or runtime artifacts; human AI-G2
     3	# acceptance and runtime producer enforcement remain pending.
     4	# One record assesses one exact control or named capability for one immutable
     5	# scope, population snapshot, and review window. Domain floors are derived in
     6	# CAPABILITY_DOMAIN_PROJECTION.yaml, never authored here.
     7	schema_version: "1"
     8	artifact_type: capability_assessment
     9	assessment_id: "capability_assessment_<uuidv7>"
    10	revision: 1
    11	status: NOT_ASSESSED
    12	definition_status: DEFINED # DEFINED means the control contract exists; it is not a runtime score.
    13	definition_evidence_refs: []
    14	subject_schema: "research-subject/v1"
    15	subject_ref: ""
    16	subject_digest: ""
    17	subject_manifest_digest: ""
    18	core_sdlc_trace_ref: ""
    19	
    20	policy_id: "POL-SDLC-001"
    21	policy_version: "1.4.0"
    22	rubric_id: "SDLC-MEA-002"
    23	rubric_version: "3.0.0"
    24	
    25	scope:
    26	  capability_id: ""
    27	  control_id: "" # Required for a VITAL-SDLC-001 member assessment.
    28	  service_ids: []
    29	  value_stream_ids: []
    30	  work_classes: []
    31	  risk_lanes: []
    32	  window_start: ""
    33	  window_end: ""
    34	  scope_digest: ""
    35	
    36	assessment_authority:
    37	  assessor_id: ""
    38	  approver_id: ""
    39	  independence_evidence_ref: ""
    40	  conflicts: []
    41	
    42	applicability:
    43	  registry_id: "APPLICABILITY-SDLC-001"
    44	  registry_version: "1.1.0"
    45	  registry_digest: ""
    46	  rule_id: ""
    47	  result: UNKNOWN # APPLICABLE | NOT_APPLICABLE | UNKNOWN
    48	  population_ref: "#/population"
    49	  qualifying_trigger_query_ref: ""
    50	  qualifying_trigger_query_digest: ""
    51	  not_applicable_reason: ""
    52	  not_applicable_approval_ref: ""
    53	  not_applicable_audit_ref: ""
    54	
    55	# Counts are derived from this one snapshot. They are never independently
    56	# entered by the assessor.
    57	population:
    58	  snapshot_ref: ""
    59	  snapshot_digest: ""
    60	  eligibility_rule_ref: ""
    61	  eligibility_query_ref: ""
    62	  eligibility_query_digest: ""
    63	  totals:
    64	    eligible: 0
    65	    included: 0
    66	    excluded: 0
    67	  # Include every selected work-class/risk-lane pair, including zero-count rows.
    68	  joint_strata:
    69	    - work_class: ""
    70	      risk_lane: ""
    71	      eligible: 0
    72	      included: 0
    73	      excluded: 0
    74	  exclusions:
    75	    - subject_ref: ""
    76	      work_class: ""
    77	      risk_lane: ""
    78	      reason_code: ""
    79	      approval_ref: ""
    80	      correction_ref: ""
    81	  sampling_method: ""
    82	  reconciliation:
    83	    totals_identity_result: NOT_CHECKED # eligible = included + excluded
    84	    strata_complete_result: NOT_CHECKED
    85	    strata_sum_to_totals_result: NOT_CHECKED
    86	    exclusions_sum_to_excluded_result: NOT_CHECKED
    87	    result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
    88	    evidence_refs: []
    89	  # Typed predicates prevent status, attempt history, outcome, and risk lane
    90	  # from being collapsed into one misleading "class" list.
    91	  adverse_categories:
    92	    - category_id: CONTROL_OR_EXECUTION_OUTCOME_FAIL
    93	      dimension: CONTROL_OR_EXECUTION_OUTCOME
    94	      selector: FAIL
    95	      predicate_rule_ref: ""
    96	      query_ref: ""
    97	      query_digest: ""
    98	      eligible: 0
    99	      included: 0
   100	      excluded: 0
   101	      derived_result: NOT_CHECKED
   102	    - category_id: WORK_STATUS_BLOCKED
   103	      dimension: WORK_STATUS_HISTORY
   104	      selector: BLOCKED
   105	      predicate_rule_ref: ""
   106	      query_ref: ""
   107	      query_digest: ""
   108	      eligible: 0
   109	      included: 0
   110	      excluded: 0
   111	      derived_result: NOT_CHECKED
   112	    - category_id: WORK_STATUS_CANCELLED
   113	      dimension: WORK_STATUS_HISTORY
   114	      selector: CANCELLED
   115	      predicate_rule_ref: ""
   116	      query_ref: ""
   117	      query_digest: ""
   118	      eligible: 0
   119	      included: 0
   120	      excluded: 0
   121	      derived_result: NOT_CHECKED
   122	    - category_id: WORK_STATUS_ROLLED_BACK
   123	      dimension: WORK_STATUS_HISTORY
   124	      selector: ROLLED_BACK
   125	      predicate_rule_ref: ""
   126	      query_ref: ""
   127	      query_digest: ""
   128	      eligible: 0
   129	      included: 0
   130	      excluded: 0
   131	      derived_result: NOT_CHECKED
   132	    - category_id: REOPENED_ATTEMPT
   133	      dimension: ATTEMPT_HISTORY
   134	      selector: REOPENED
   135	      predicate_rule_ref: ""
   136	      query_ref: ""
   137	      query_digest: ""
   138	      eligible: 0
   139	      included: 0
   140	      excluded: 0
   141	      derived_result: NOT_CHECKED
   142	    - category_id: RISK_LANE_EMERGENCY
   143	      dimension: RISK_LANE
   144	      selector: EMERGENCY
   145	      predicate_rule_ref: ""
   146	      query_ref: ""
   147	      query_digest: ""
   148	      eligible: 0
   149	      included: 0
   150	      excluded: 0
   151	      derived_result: NOT_CHECKED
   152	  adverse_reconciliation_result: NOT_CHECKED
   153	
   154	evidence:
   155	  event_query_ref: ""
   156	  event_query_digest: ""
   157	  evidence_snapshot_refs: []
   158	  enacted_practice_refs: []
   159	  artifact_and_provenance_refs: []
   160	  outcome_and_guardrail_refs: []
   161	  normal_path_event_refs: []
   162	  traversed_rejection_invalidation_exception_or_backward_event_refs: []
   163	  data_quality_result_ref: ""
   164	  limitations: []
   165	
   166	capability_rating:
   167	  # SCORED also requires gap_register.reconciliation.scored_eligibility_result PASS.
   168	  result: NOT_ASSESSED # NOT_ASSESSED | UNKNOWN | NOT_APPLICABLE | SCORED
   169	  level: null # null unless SCORED; otherwise 0 | 1 | 2 | 3 | 4
   170	  label: ""
   171	  criterion_evidence:
   172	    - criterion_id: ""
   173	      evidence_refs: []
   174	      result: UNKNOWN
   175	  ordinal_label_only: true
   176	  arithmetic_aggregation_prohibited: true
   177	
   178	effectiveness:
   179	  result: UNKNOWN # UNKNOWN | REGRESSING | MIXED | MEETS_TARGET
   180	  metric_spec_ids: []
   181	  baseline_refs: []
   182	  comparator_refs: []
   183	  observed_result_refs: []
   184	  distribution_and_trend_refs: []
   185	  guardrail_result_refs: []
   186	
   187	# Level 3/4 and every experiment supporting level 4 bind this immutable design.
   188	measurement_design:
   189	  design_id: ""
   190	  design_version: ""
   191	  design_digest: ""
   192	  goal_question_decision_refs: []
   193	  metric_spec_refs: []
   194	  metric_registry_id: "METRIC-SDLC-001"
   195	  metric_registry_version: "1.0.0"
   196	  fixed_comparator_ref: ""
   197	  prospective_decision_rule_ref: ""
   198	  decision_rule_frozen_at: ""
   199	  minimum_meaningful_effect: ""
   200	  minimum_detectable_effect: ""
   201	  analysis_method_ref: ""
   202	  analysis_assumption_check_refs: []
   203	  decision_rule_evaluation_ref: ""
   204	  noise:
   205	    status: NOT_ASSESSED # NOT_ASSESSED | ESTABLISHED | NOT_APPLICABLE
   206	    floor: null
   207	    method_ref: ""
   208	    zero_claim_evidence_ref: ""
   209	    zero_claim_independent_approval_ref: ""
   210	    uncertainty_na_rule_ref: ""
   211	    uncertainty_na_approval_ref: ""
   212	  harness:
   213	    harness_id: ""
   214	    harness_version: ""
   215	    harness_digest: ""
   216	    configuration_ref: ""
   217	    configuration_digest: ""
   218	    qualification_result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
   219	    qualification_ref: ""
   220	    repeatability_test_refs: []
   221	    data_quality_test_refs: []
   222	  outcome_accounting:
   223	    subject_failure_count: 0
   224	    infrastructure_error_count: 0
   225	    infrastructure_error_ledger_ref: ""
   226	
   227	# Coverage is a view over population; it carries no duplicate count fields.
   228	coverage:
   229	  population_ref: "#/population"
   230	  percentage: null # Output-only computed field; authored input must be null.
   231	  percentage_formula: "population.totals.included / population.totals.eligible * 100; null when eligible = 0"
   232	  by_joint_strata_ref: "#/population/joint_strata"
   233	  reconciliation_result: NOT_CHECKED
   234	
   235	# One register owns every evidence, population, coverage, measurement, and
   236	# applicability gap. HIGH cannot omit a known material gap.
   237	gap_register:
   238	  inventory_query_ref: ""
   239	  inventory_query_digest: ""
   240	  entries:
   241	    - gap_id: ""
   242	      source_dimension: "" # EVIDENCE | POPULATION | COVERAGE | MEASUREMENT | APPLICABILITY
   243	      source_ref: ""
   244	      materiality: UNKNOWN # UNKNOWN | NON_MATERIAL | MATERIAL
   245	      disposition: OPEN # OPEN | ACCEPTED_LIMITATION | CORRECTED | SUPERSEDED
   246	      disposition_evidence_ref: ""
   247	  reconciliation:
   248	    source_inventory_complete_result: NOT_CHECKED
   249	    every_gap_disposed_result: NOT_CHECKED
   250	    unresolved_material_gap_refs: []
   251	    scored_eligibility_result: NOT_CHECKED
   252	    result: NOT_CHECKED
   253	
   254	# Confidence is rule-derived. HIGH requires all seven tests PASS and independent
   255	# sign-off. Any material unresolved gap forces LOW.
   256	confidence:
   257	  adequacy_rule:
   258	    rule_id: ""
   259	    rule_version: ""
   260	    rule_digest: ""
   261	    approval_ref: ""
   262	  tests:
   263	    sample:
   264	      result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
   265	      evidence_refs: []
   266	    duration:
   267	      result: NOT_CHECKED
   268	      evidence_refs: []
   269	    representativeness:
   270	      result: NOT_CHECKED
   271	      evidence_refs: []
   272	    authenticity:
   273	      result: NOT_CHECKED
   274	      evidence_refs: []
   275	    freshness:
   276	      result: NOT_CHECKED
   277	      evidence_refs: []
   278	    missingness:
   279	      result: NOT_CHECKED
   280	      evidence_refs: []
   281	    data_quality:
   282	      result: NOT_CHECKED
   283	      evidence_refs: []
   284	  gap_register_ref: "#/gap_register"
   285	  independent_assurance_signoff_ref: ""
   286	  derived_level: LOW # LOW | MEDIUM | HIGH
   287	  derivation_result: NOT_CHECKED
   288	  rationale: ""
   289	
   290	# Evaluate every registry trigger and apply P0 > P1 > P2 > P3. The first
   291	# matching tier wins. Valid NOT_APPLICABLE has no tier.
   292	priority:
   293	  priority_rule_id: "PRIORITY-SDLC-001"
   294	  priority_rule_version: "1.0.0"
   295	  priority_rule_digest: ""
   296	  result: NOT_EVALUATED # NOT_EVALUATED | NOT_APPLICABLE | ASSIGNED
   297	  evaluated_trigger_results:
   298	    - trigger_code: ""
   299	      result: NOT_CHECKED # NOT_CHECKED | MATCH | NO_MATCH
   300	      evidence_refs: []
   301	  trigger_set_validation:
   302	    exact_registry_trigger_set_result: NOT_CHECKED
   303	    no_duplicate_trigger_result: NOT_CHECKED
   304	    validation_evidence_refs: []
   305	  matched_trigger_codes: []
   306	  decisive_trigger_code: ""
   307	  derived_tier: null # null | P0_CONTROL_NOW | P1_IMPROVE_NEXT | P2_IMPROVE_DELIBERATELY | P3_SUSTAIN
   308	  instrumentation_action_ref: ""
   309	  derivation_result: NOT_CHECKED
   310	  consequence: ""
   311	  exposure: ""
   312	  recurrence: ""
   313	  downstream_blocking: ""
   314	  capability_gap: ""
   315	
   316	findings:
   317	  active_harm_refs: []
   318	  invariant_breach_refs: []
   319	  nonconformity_refs: []
   320	  exception_refs: []
   321	  gate_outcome_refs: []
   322	
   323	improvement:
   324	  linked_work_item_id: ""
   325	  causal_stage: ""
   326	  causal_control_id: ""
   327	  hypothesis: ""
   328	  bounded_change: ""
   329	  measurement_design_ref: ""
   330	  measurement_design_digest: ""
   331	  owner_id: ""
   332	  evidence_window_end: ""
   333	  stop_or_revert_criteria: []
   334	  review_date: ""
   335	  effectiveness_review_ref: ""
   336	  decision: "" # RETAIN | SCALE | SIMPLIFY | CHANGE | REVERT
   337	
   338	decision_ref: ""
   339	approved_at: ""
   340	prior_assessment_ref: ""
   341	supersedes_ref: ""
   342	correction_reason: ""
   343	created_at: ""
   344	digest: ""
     1	{
     2	  "$id": "https://schemas.ranex.dev/process/capability-assessment-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "applicability": {
     7	      "additionalProperties": false,
     8	      "properties": {
     9	        "not_applicable_approval_ref": {
    10	          "type": "string"
    11	        },
    12	        "not_applicable_audit_ref": {
    13	          "type": "string"
    14	        },
    15	        "not_applicable_reason": {
    16	          "type": "string"
    17	        },
    18	        "population_ref": {
    19	          "type": "string"
    20	        },
    21	        "qualifying_trigger_query_digest": {
    22	          "type": "string",
    23	          "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    24	        },
    25	        "qualifying_trigger_query_ref": {
    26	          "type": "string"
    27	        },
    28	        "registry_digest": {
    29	          "type": "string",
    30	          "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    31	        },
    32	        "registry_id": {
    33	          "type": "string"
    34	        },
    35	        "registry_version": {
    36	          "type": "string"
    37	        },
    38	        "result": {
    39	          "type": "string"
    40	        },
    41	        "rule_id": {
    42	          "type": "string"
    43	        }
    44	      },
    45	      "required": [
    46	        "registry_id",
    47	        "registry_version",
    48	        "registry_digest",
    49	        "rule_id",
    50	        "result",
    51	        "population_ref",
    52	        "qualifying_trigger_query_ref",
    53	        "qualifying_trigger_query_digest",
    54	        "not_applicable_reason",
    55	        "not_applicable_approval_ref",
    56	        "not_applicable_audit_ref"
    57	      ],
    58	      "type": "object"
    59	    },
    60	    "approved_at": {
    61	      "type": "string",
    62	      "x-ranex-runtime-format": "date-time"
    63	    },
    64	    "artifact_type": {
    65	      "const": "capability_assessment"
    66	    },
    67	    "assessment_authority": {
    68	      "additionalProperties": false,
    69	      "properties": {
    70	        "approver_id": {
    71	          "type": "string"
    72	        },
    73	        "assessor_id": {
    74	          "type": "string"
    75	        },
    76	        "conflicts": {
    77	          "items": {},
    78	          "type": "array"
    79	        },
    80	        "independence_evidence_ref": {
    81	          "type": "string"
    82	        }
    83	      },
    84	      "required": [
    85	        "assessor_id",
    86	        "approver_id",
    87	        "independence_evidence_ref",
    88	        "conflicts"
    89	      ],
    90	      "type": "object"
    91	    },
    92	    "assessment_id": {
    93	      "type": "string"
    94	    },
    95	    "capability_rating": {
    96	      "additionalProperties": false,
    97	      "properties": {
    98	        "arithmetic_aggregation_prohibited": {
    99	          "type": "boolean"
   100	        },
   101	        "criterion_evidence": {
   102	          "items": {
   103	            "additionalProperties": false,
   104	            "properties": {
   105	              "criterion_id": {
   106	                "type": "string"
   107	              },
   108	              "evidence_refs": {
   109	                "items": {},
   110	                "type": "array"
   111	              },
   112	              "result": {
   113	                "type": "string"
   114	              }
   115	            },
   116	            "required": [
   117	              "criterion_id",
   118	              "evidence_refs",
   119	              "result"
   120	            ],
   121	            "type": "object"
   122	          },
   123	          "type": "array"
   124	        },
   125	        "label": {
   126	          "type": "string"
   127	        },
   128	        "level": {
   129	          "minimum": 0,
   130	          "type": [
   131	            "integer",
   132	            "null"
   133	          ]
   134	        },
   135	        "ordinal_label_only": {
   136	          "type": "boolean"
   137	        },
   138	        "result": {
   139	          "type": "string"
   140	        }
   141	      },
   142	      "required": [
   143	        "result",
   144	        "level",
   145	        "label",
   146	        "criterion_evidence",
   147	        "ordinal_label_only",
   148	        "arithmetic_aggregation_prohibited"
   149	      ],
   150	      "type": "object"
   151	    },
   152	    "confidence": {
   153	      "additionalProperties": false,
   154	      "properties": {
   155	        "adequacy_rule": {
   156	          "additionalProperties": false,
   157	          "properties": {
   158	            "approval_ref": {
   159	              "type": "string"
   160	            },
   161	            "rule_digest": {
   162	              "type": "string",
   163	              "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
   164	            },
   165	            "rule_id": {
   166	              "type": "string"
   167	            },
   168	            "rule_version": {
   169	              "type": "string"
   170	            }
   171	          },
   172	          "required": [
   173	            "rule_id",
   174	            "rule_version",
   175	            "rule_digest",
   176	            "approval_ref"
   177	          ],
   178	          "type": "object"
   179	        },
   180	        "derivation_result": {
   181	          "type": "string"
   182	        },
   183	        "derived_level": {
   184	          "type": "string"
   185	        },
   186	        "gap_register_ref": {
   187	          "type": "string"
   188	        },
   189	        "independent_assurance_signoff_ref": {
   190	          "type": "string"
   191	        },
   192	        "rationale": {
   193	          "type": "string"
   194	        },
   195	        "tests": {
   196	          "additionalProperties": false,
   197	          "properties": {
   198	            "authenticity": {
   199	              "additionalProperties": false,
   200	              "properties": {
   201	                "evidence_refs": {
   202	                  "items": {},
   203	                  "type": "array"
   204	                },
   205	                "result": {
   206	                  "type": "string"
   207	                }
   208	              },
   209	              "required": [
   210	                "result",
   211	                "evidence_refs"
   212	              ],
   213	              "type": "object"
   214	            },
   215	            "data_quality": {
   216	              "additionalProperties": false,
   217	              "properties": {
   218	                "evidence_refs": {
   219	                  "items": {},
   220	                  "type": "array"
   221	                },
   222	                "result": {
   223	                  "type": "string"
   224	                }
   225	              },
   226	              "required": [
   227	                "result",
   228	                "evidence_refs"
   229	              ],
   230	              "type": "object"
   231	            },
   232	            "duration": {
   233	              "additionalProperties": false,
   234	              "properties": {
   235	                "evidence_refs": {
   236	                  "items": {},
   237	                  "type": "array"
   238	                },
   239	                "result": {
   240	                  "type": "string"
   241	                }
   242	              },
   243	              "required": [
   244	                "result",
   245	                "evidence_refs"
   246	              ],
   247	              "type": "object"
   248	            },
   249	            "freshness": {
   250	              "additionalProperties": false,
   251	              "properties": {
   252	                "evidence_refs": {
   253	                  "items": {},
   254	                  "type": "array"
   255	                },
   256	                "result": {
   257	                  "type": "string"
   258	                }
   259	              },
   260	              "required": [
   261	                "result",
   262	                "evidence_refs"
   263	              ],
   264	              "type": "object"
   265	            },
   266	            "missingness": {
   267	              "additionalProperties": false,
   268	              "properties": {
   269	                "evidence_refs": {
   270	                  "items": {},
   271	                  "type": "array"
   272	                },
   273	                "result": {
   274	                  "type": "string"
   275	                }
   276	              },
   277	              "required": [
   278	                "result",
   279	                "evidence_refs"
   280	              ],
     1	{
     2	  "$id": "https://schemas.ranex.dev/assurance/evidence-snapshot-v1.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "artifact_type": {
     7	      "const": "evidence_snapshot"
     8	    },
     9	    "conflicts": {
    10	      "items": {},
    11	      "type": "array"
    12	    },
    13	    "core_sdlc_trace_ref": {
    14	      "type": "string"
    15	    },
    16	    "coverage": {
    17	      "items": {},
    18	      "type": "array"
    19	    },
    20	    "created_at": {
    21	      "type": "string",
    22	      "x-ranex-runtime-format": "date-time"
    23	    },
    24	    "created_by_service_id": {
    25	      "type": "string"
    26	    },
    27	    "digest": {
    28	      "type": "string",
    29	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    30	    },
    31	    "eligible_evidence_refs": {
    32	      "items": {},
    33	      "type": "array"
    34	    },
    35	    "freshness_cutoff": {
    36	      "type": "string"
    37	    },
    38	    "ineligible_evidence": {
    39	      "items": {
    40	        "additionalProperties": false,
    41	        "properties": {
    42	          "evidence_ref": {
    43	            "type": "string"
    44	          },
    45	          "reason_code": {
    46	            "type": "string"
    47	          }
    48	        },
    49	        "required": [
    50	          "evidence_ref",
    51	          "reason_code"
    52	        ],
    53	        "type": "object"
    54	      },
    55	      "type": "array"
    56	    },
    57	    "missing_claim_ids": {
    58	      "items": {},
    59	      "type": "array"
    60	    },
    61	    "policy_activation_id": {
    62	      "type": "string"
    63	    },
    64	    "policy_activation_manifest_digest": {
    65	      "type": "string",
    66	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    67	    },
    68	    "required_claim_ids": {
    69	      "items": {},
    70	      "type": "array"
    71	    },
    72	    "schema_version": {
    73	      "const": "1"
    74	    },
    75	    "snapshot_id": {
    76	      "type": "string"
    77	    },
    78	    "subject_digest": {
    79	      "type": "string",
    80	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    81	    },
    82	    "subject_manifest_digest": {
    83	      "type": [
    84	        "string",
    85	        "null"
    86	      ]
    87	    },
    88	    "subject_ref": {
    89	      "type": "string"
    90	    },
    91	    "subject_schema": {
    92	      "type": [
    93	        "string",
    94	        "null"
    95	      ]
    96	    }
    97	  },
    98	  "required": [
    99	    "schema_version",
   100	    "artifact_type",
   101	    "snapshot_id",
   102	    "subject_schema",
   103	    "subject_ref",
   104	    "subject_digest",
   105	    "subject_manifest_digest",
   106	    "core_sdlc_trace_ref",
   107	    "policy_activation_id",
   108	    "policy_activation_manifest_digest",
   109	    "required_claim_ids",
   110	    "eligible_evidence_refs",
   111	    "ineligible_evidence",
   112	    "freshness_cutoff",
   113	    "coverage",
   114	    "missing_claim_ids",
   115	    "conflicts",
   116	    "created_by_service_id",
   117	    "created_at",
   118	    "digest"
   119	  ],
   120	  "title": "evidence_snapshot",
   121	  "type": "object",
   122	  "x-ranex-canonical-producer": "assurance",
   123	  "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
   124	  "x-ranex-template": "docs/architecture/templates/EVIDENCE_SNAPSHOT.yaml"
   125	}

codex
The repository trace confirms that the generated schemas are mostly permissive string/array shells, while the prose and YAML templates carry much of the real vocabulary. I’m therefore treating deltas as template/generator changes, even when the row cites the generated schema line that exposes the issue. The current JSONL ledger is a local SHA-256 hash chain with locking and `fsync`; that distinction will matter against externally witnessed transparency logs.
Repository inspection is complete enough to anchor exact current behavior. External verification is now underway across each layer and competitor set.
  ✓ Inspect Ranex schemas, templates, architecture contract, licence, and hash-chain ledger with exact lines
  → Verify prior-art specifications, maturity/adoption, and licences from primary sources
  • Map Ranex elements to standards with ADOPT/ADAPT/DIVERGE/NOVEL verdicts and actionable deltas
  • Audit citations, inferences, search coverage, and produce the required report
web search: 
web search: site:oasis-open.org sarif 2.1 result ruleId level message locations fixes provenance specification ...
web search: 
web search: 
web search: 
web search: site:pages.nist.gov/OSCAL concepts layers assessment results observations findings risks evidence OSCAL ...
web search: 
web search: site:github.com/usnistgov/OSCAL "LICENSE.md" public domain ...
web search: 
web search: site:pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/json-reference "Observation" "relevant-evidence" ...
web search: 
web search: site:csrc.nist.gov/projects/security-content-automation-protocol SCAP 1.3 XCCDF OVAL ARF standardized compliance results ...
web search: 
web search: site:schema.ocsf.io compliance finding class security finding OCSF evidence remediation status confidence ...
web search: 
web search: https://schema.ocsf.io/1.3.0/classes/compliance_finding
web search: 
web search: github ocsf ocsf-schema license Apache-2.0 ...
web search: 
web search: site:w3.org/TR/prov-dm W3C Recommendation entity activity agent generation usage derivation bundle ...
web search: 
web search: site:github.com/in-toto/attestation specification v1 statement subject predicateType resourceDescriptor digest license ...
web search: 
web search: site:github.com/in-toto/attestation/blob/main/LICENSE Apache 2.0 ...
exec
/bin/bash -lc "curl -L --max-time 20 -sS https://raw.githubusercontent.com/in-toto/attestation/main/LICENSE | sed -n '1,40p'
curl -L --max-time 20 -sS https://api.github.com/repos/in-toto/attestation/license | rg '\"spdx_id\"|\"html_url\"'
curl -L --max-time 20 -sS https://api.github.com/repos/in-toto/in-toto/license | rg '\"spdx_id\"|\"html_url\"'" in /home/soultransit/devtony/ranex
 succeeded in 1065ms:
Copyright 2021 in-toto Developers

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
  "html_url": "https://github.com/in-toto/attestation/blob/main/LICENSE",
    "spdx_id": "NOASSERTION",
  "html_url": "https://github.com/in-toto/in-toto/blob/develop/LICENSE",
    "spdx_id": "NOASSERTION",

web search: 
web search: site:slsa.dev/spec latest provenance v1.1 buildDefinition runDetails resolvedDependencies builder byproducts ...
web search: 
web search: https://slsa.dev/spec/v1.2/build-provenance
web search: 
web search: site:docs.github.com artifact attestations SLSA provenance in-toto Sigstore production ...
web search: 
web search: site:docs.sigstore.dev bundle format verification materials certificate tlog inclusion proof checkpoint ...
web search: 
web search: site:github.com/sigstore/rekor Apache-2.0 license ...
web search: 
web search: site:rfc-editor.org RFC 9162 Certificate Transparency version 2 Merkle Tree inclusion proof consistency proof signed tree head ...
web search: 
web search: 
web search: 
web search: site:github.com/transparency-dev/tessera Apache 2.0 production transparency log tile based ...
web search: 
web search: site:learn.microsoft.com Azure Confidential Ledger immutable tamper evident receipts CCF production ...
web search: 
web search: site:github.com/microsoft/CCF "Apache-2.0 license" ...
exec
/bin/bash -lc "curl -L --max-time 20 -sS https://raw.githubusercontent.com/microsoft/CCF/main/LICENSE | sed -n '1,14p'
curl -L --max-time 20 -sS https://api.github.com/repos/microsoft/CCF/license | rg '\"spdx_id\"|\"html_url\"'" in /home/soultransit/devtony/ranex
 succeeded in 655ms:

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.
  "html_url": "https://github.com/microsoft/CCF/blob/main/LICENSE",
    "spdx_id": "Apache-2.0",

web search: 
web search: site:rfc-editor.org SCITT architecture transparency services signed statements receipts RFC ...
web search: 
web search: https://www.rfc-editor.org/info/rfc9942/
web search: 
web search: RFC 9942 COSE receipts for verifiable data structures inclusion consistency proofs ...
web search: 
web search: site:c2pa.org/specifications C2PA 2.2 manifest assertions ingredients claim signature trust list adopters ...
context compacted
codex
The main standards split is now clear: SARIF covers finding interchange, OSCAL covers controls/assessment evidence, and in-toto/SLSA plus Sigstore/SCITT cover authenticated provenance and verifiable logging. I’m checking the edge cases now—especially whether Ranex’s AI-review independence and epistemic vocabulary have a genuine machine-readable predecessor.
web search: 
web search: site:nist.gov assessor independence assessment evidence NIST 800-53 CA-2 independent assessors ...
web search: 
web search: C2PA specification provenance claims content credentials official production adoption license ...
web search: 
web search: site:cyclonedx.org/docs/1.7 attestations claims evidence conformance confidence formulation ...
exec
/bin/bash -lc "git status --short && nl -ba schemas/review/review-observation-v1.schema.json | sed -n '15,120p' && nl -ba schemas/common/evidence-ref.schema.json | sed -n '1,30p' && nl -ba .claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py | sed -n '13,215p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
 M docs/README.md
 M docs/architecture/README.md
 M docs/architecture/reviews/README.md
 M docs/architecture/rfcs/README.md
 M docs/research/README.md
?? docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md
?? docs/architecture/reviews/artifacts/2026-07-30/
?? docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md
?? docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
    15	    "digest": {
    16	      "type": "string",
    17	      "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
    18	    },
    19	    "findings": {
    20	      "items": {
    21	        "additionalProperties": false,
    22	        "allOf": [
    23	          {
    24	            "if": {
    25	              "properties": {
    26	                "epistemic_status": {
    27	                  "const": "FACT"
    28	                }
    29	              },
    30	              "required": [
    31	                "epistemic_status"
    32	              ]
    33	            },
    34	            "then": {
    35	              "properties": {
    36	                "evidence_refs": {
    37	                  "items": {
    38	                    "minLength": 1,
    39	                    "type": "string"
    40	                  },
    41	                  "minItems": 1
    42	                }
    43	              }
    44	            }
    45	          }
    46	        ],
    47	        "properties": {
    48	          "category": {
    49	            "type": "string"
    50	          },
    51	          "claim": {
    52	            "type": "string"
    53	          },
    54	          "confidence": {
    55	            "type": "string"
    56	          },
    57	          "epistemic_status": {
    58	            "enum": [
    59	              "FACT",
    60	              "INFERENCE",
    61	              "OWNER_REQUIREMENT",
    62	              "PROPOSAL",
    63	              "REPORTED_ADVISORY_RESULT"
    64	            ]
    65	          },
    66	          "evidence_refs": {
    67	            "items": {},
    68	            "type": "array"
    69	          },
    70	          "finding_id": {
    71	            "type": "string"
    72	          },
    73	          "impact": {
    74	            "type": "string"
    75	          },
    76	          "location": {
    77	            "type": "string"
    78	          },
    79	          "owner_ref": {
    80	            "type": [
    81	              "string",
    82	              "null"
    83	            ]
    84	          },
    85	          "reconciliation_ref": {
    86	            "type": [
    87	              "string",
    88	              "null"
    89	            ]
    90	          },
    91	          "required_action": {
    92	            "type": "string"
    93	          },
    94	          "severity": {
    95	            "type": "string"
    96	          },
    97	          "state": {
    98	            "type": "string"
    99	          }
   100	        },
   101	        "required": [
   102	          "finding_id",
   103	          "category",
   104	          "severity",
   105	          "confidence",
   106	          "epistemic_status",
   107	          "location",
   108	          "claim",
   109	          "impact",
   110	          "evidence_refs",
   111	          "required_action",
   112	          "owner_ref",
   113	          "state",
   114	          "reconciliation_ref"
   115	        ],
   116	        "type": "object"
   117	      },
   118	      "type": "array"
   119	    },
   120	    "limitations": {
     1	{
     2	  "$id": "https://schemas.ranex.dev/common/evidence-ref.schema.json",
     3	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     4	  "additionalProperties": false,
     5	  "properties": {
     6	    "evidence_digest": {
     7	      "pattern": "^sha256:[0-9a-f]{64}$",
     8	      "type": "string"
     9	    },
    10	    "evidence_ref": {
    11	      "minLength": 1,
    12	      "type": "string"
    13	    }
    14	  },
    15	  "required": [
    16	    "evidence_ref",
    17	    "evidence_digest"
    18	  ],
    19	  "type": "object"
    20	}
    13	_GENESIS_DIGEST = "0" * 64
    14	
    15	
    16	class LedgerIntegrityError(RuntimeError):
    17	    pass
    18	
    19	
    20	@dataclass(frozen=True, slots=True)
    21	class LedgerEntry:
    22	    sequence: int
    23	    previous_digest: str
    24	    record_digest: str
    25	    entry_digest: str
    26	    record: dict[str, Any]
    27	
    28	
    29	@dataclass(frozen=True, slots=True)
    30	class LedgerVerification:
    31	    valid: bool
    32	    entry_count: int
    33	    broken_sequence: int | None
    34	    head_digest: str
    35	    reason: str | None = None
    36	
    37	
    38	def _sha256_text(value: str) -> str:
    39	    return hashlib.sha256(value.encode("utf-8")).hexdigest()
    40	
    41	
    42	def _entry_digest(
    43	    *,
    44	    sequence: int,
    45	    previous_digest: str,
    46	    record_digest: str,
    47	) -> str:
    48	    return _sha256_text(
    49	        canonical_json(
    50	            {
    51	                "previous_digest": previous_digest,
    52	                "record_digest": record_digest,
    53	                "sequence": sequence,
    54	            }
    55	        )
    56	    )
    57	
    58	
    59	class HashChainLedger:
    60	    """Append-only API over a tamper-evident canonical JSONL hash chain."""
    61	
    62	    def __init__(self, path: Path) -> None:
    63	        self._path = path
    64	
    65	    def _verify_lines(self, lines: list[str]) -> LedgerVerification:
    66	        previous_digest = _GENESIS_DIGEST
    67	        for expected_sequence, line in enumerate(lines, start=1):
    68	            try:
    69	                raw = json.loads(line)
    70	                record = raw["record"]
    71	                record_digest = _sha256_text(canonical_json(record))
    72	                computed_entry_digest = _entry_digest(
    73	                    sequence=expected_sequence,
    74	                    previous_digest=previous_digest,
    75	                    record_digest=record_digest,
    76	                )
    77	                valid = (
    78	                    raw["sequence"] == expected_sequence
    79	                    and raw["previous_digest"] == previous_digest
    80	                    and raw["record_digest"] == record_digest
    81	                    and raw["entry_digest"] == computed_entry_digest
    82	                )
    83	            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
    84	                valid = False
    85	                computed_entry_digest = previous_digest
    86	            if not valid:
    87	                return LedgerVerification(
    88	                    valid=False,
    89	                    entry_count=len(lines),
    90	                    broken_sequence=expected_sequence,
    91	                    head_digest=previous_digest,
    92	                    reason="ledger hash chain is invalid",
    93	                )
    94	            previous_digest = computed_entry_digest
    95	        return LedgerVerification(
    96	            valid=True,
    97	            entry_count=len(lines),
    98	            broken_sequence=None,
    99	            head_digest=previous_digest,
   100	        )
   101	
   102	    def verify(self) -> LedgerVerification:
   103	        if not self._path.exists():
   104	            return LedgerVerification(
   105	                valid=False,
   106	                entry_count=0,
   107	                broken_sequence=None,
   108	                head_digest=_GENESIS_DIGEST,
   109	                reason="ledger file is missing",
   110	            )
   111	        with self._path.open("r", encoding="utf-8") as stream:
   112	            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
   113	            lines = [line for line in stream.read().splitlines() if line.strip()]
   114	        if not lines:
   115	            return LedgerVerification(
   116	                valid=False,
   117	                entry_count=0,
   118	                broken_sequence=None,
   119	                head_digest=_GENESIS_DIGEST,
   120	                reason="ledger file is empty",
   121	            )
   122	        return self._verify_lines(lines)
   123	
   124	    def append(self, record: dict[str, Any]) -> LedgerEntry:
   125	        return self._append(record, idempotency_key=None)
   126	
   127	    def append_once(self, record: dict[str, Any], *, key: str) -> LedgerEntry:
   128	        if not key:
   129	            raise ValueError("idempotency key must be non-empty")
   130	        return self._append(record, idempotency_key=key)
   131	
   132	    def _append(
   133	        self,
   134	        record: dict[str, Any],
   135	        *,
   136	        idempotency_key: str | None,
   137	    ) -> LedgerEntry:
   138	        if "_ledger_idempotency_key" in record:
   139	            raise ValueError("record uses a reserved ledger field")
   140	        stored_record = dict(record)
   141	        if idempotency_key is not None:
   142	            stored_record["_ledger_idempotency_key"] = idempotency_key
   143	
   144	        self._path.parent.mkdir(parents=True, exist_ok=True)
   145	        self._path.touch(mode=0o600, exist_ok=True)
   146	        self._path.chmod(0o600)
   147	        with self._path.open("a+", encoding="utf-8") as stream:
   148	            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
   149	            stream.seek(0)
   150	            lines = [line for line in stream.read().splitlines() if line.strip()]
   151	            verification = self._verify_lines(lines)
   152	            if not verification.valid:
   153	                raise LedgerIntegrityError(
   154	                    "refusing append because the ledger hash chain is invalid"
   155	                )
   156	
   157	            if idempotency_key is not None:
   158	                for line in lines:
   159	                    raw = json.loads(line)
   160	                    existing_record = raw["record"]
   161	                    if (
   162	                        existing_record.get("_ledger_idempotency_key")
   163	                        == idempotency_key
   164	                    ):
   165	                        if canonical_json(existing_record) != canonical_json(
   166	                            stored_record
   167	                        ):
   168	                            raise LedgerIntegrityError(
   169	                                "idempotency key was reused for a different record"
   170	                            )
   171	                        return LedgerEntry(
   172	                            sequence=raw["sequence"],
   173	                            previous_digest=raw["previous_digest"],
   174	                            record_digest=raw["record_digest"],
   175	                            entry_digest=raw["entry_digest"],
   176	                            record=existing_record,
   177	                        )
   178	
   179	            sequence = verification.entry_count + 1
   180	            record_digest = _sha256_text(canonical_json(stored_record))
   181	            entry_digest = _entry_digest(
   182	                sequence=sequence,
   183	                previous_digest=verification.head_digest,
   184	                record_digest=record_digest,
   185	            )
   186	            entry = LedgerEntry(
   187	                sequence=sequence,
   188	                previous_digest=verification.head_digest,
   189	                record_digest=record_digest,
   190	                entry_digest=entry_digest,
   191	                record=stored_record,
   192	            )
   193	            stream.seek(0, os.SEEK_END)
   194	            stream.write(
   195	                canonical_json(
   196	                    {
   197	                        "sequence": entry.sequence,
   198	                        "previous_digest": entry.previous_digest,
   199	                        "record_digest": entry.record_digest,
   200	                        "entry_digest": entry.entry_digest,
   201	                        "record": entry.record,
   202	                    }
   203	                )
   204	                + "\n"
   205	            )
   206	            stream.flush()
   207	            os.fsync(stream.fileno())
   208	            return entry

exec
/bin/bash -lc "nl -ba docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n '20,110p;333,465p' && nl -ba docs/architecture/templates/REVIEW_OBSERVATION.yaml | sed -n '1,40p' && nl -ba docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml | sed -n '145,345p' && nl -ba scripts/architecture/generate_contracts.py | sed -n '280,325p' && nl -ba LICENSE-RANEX.md | sed -n '1,75p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
    20	## 1. Standing
    21	
    22	This document specifies the complete artifact family used to drive and verify
    23	AI workers inside the established Core SDLC. It defines target fields,
    24	producers, authority boundaries, canonicalization, and schema locations.
    25	
    26	Files under [`templates/`](./templates/) are reviewable authoring skeletons.
    27	Their executable JSON Schemas are registered under
    28	[`../../schemas/`](../../schemas/), canonical vocabularies are registered under
    29	[`../../architecture/contracts/`](../../architecture/contracts/), and
    30	`scripts/architecture/validate_contracts.py` validates them together with
    31	canonicalization, forgery, reuse, and subject-binding fixtures. Empty authoring
    32	placeholders remain invalid for a sealed runtime artifact.
    33	
    34	This executable documentation-contract baseline does not by itself establish
    35	`AI-G2: PASS`. That gate additionally requires the exact-revision validation
    36	report, generated consumer packages, qualified runtime producers, isolation
    37	evidence, and authenticated human acceptance.
    38	
    39	## 2. Canonical encoding and digest
    40	
    41	The contract registry declares one canonical wire representation:
    42	
    43	1. accept JSON or YAML only at an ingress adapter;
    44	2. parse with duplicate-key rejection and schema-selected scalar types;
    45	3. normalize to the versioned JSON data model;
    46	4. reject unknown fields unless that schema version explicitly reserves them;
    47	5. encode using RFC 8785 JSON Canonicalization Scheme;
    48	6. compute SHA-256 over the UTF-8 canonical bytes with the top-level `digest`
    49	   field absent;
    50	7. serialize `digest` as `sha256:<64 lowercase hex>`;
    51	8. preserve the original submitted bytes as a separate artifact when required;
    52	   and
    53	9. never use display YAML bytes, map insertion order, local paths, timestamps,
    54	   or a redacted projection to recompute the canonical digest.
    55	
    56	Times are RFC 3339 UTC with explicit `Z`. Durations and budgets are integer
    57	base units declared by schema. Floating-point values are forbidden in authority
    58	and evidence identity. Empty string is not a substitute for absent/unknown;
    59	required unknown facts use the typed epistemic state.
    60	
    61	## 3. Shared identifiers and vocabulary
    62	
    63	All generated identifiers use the prefixes registered in `identities.yaml`.
    64	Minimum prefixes include:
    65	
    66	| Type | Prefix |
    67	|---|---|
    68	| Repository | `repo_` |
    69	| Project / work / run / activity / effect | `prj_`, `work_`, `run_`, `act_`, `eff_` |
    70	| Workspace / packet / intake / research | `wsp_`, `pkt_`, `intake_`, `research_` |
    71	| Requirement / criterion / outcome measure | `req_`, `criterion_`, `measure_` |
    72	| Core-SDLC trace block | `trace_` |
    73	| Evidence / snapshot / artifact / checker result | `evd_`, `snapshot_`, `art_`, `check_` |
    74	| Architecture review packet / proposal / reconciliation | `archpkt_`, `proposal_`, `archreconcile_` |
    75	| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
    76	| Review-record projection | `review_projection_` |
    77	| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
    78	| Decision / authority grant / permit / gate | `dec_`, `grant_`, `permit_`, `gate_` |
    79	| Handoff / result / landing / transition | `handoff_`, `result_`, `landing_`, `transition_` |
    80	| Release / incident / service / capability | `release_`, `incident_`, `svc_`, `cap_` |
    81	| Post-landing / release / operation / outcome evidence | `postlanding_`, `release_evidence_`, `operation_evidence_`, `outcome_review_` |
    82	| Assignment / offer / worker attempt / lease / mailbox | `assignment_`, `offer_`, `wattempt_`, `lease_`, `message_` |
    83	| Resource reservation / fleet experiment | `reservation_`, `fleetexp_` |
    84	| Capability assessment / domain projection | `capability_assessment_`, `capability_domain_projection_` |
    85	
    86	Canonical enum values are uppercase. Lowercase values in display examples are
    87	invalid after `AI-G2`. The authoritative registries own:
    88	
    89	- `WorkItemStatus`, `WorkClass`, `RiskLane`, `RunStatus`, `ActivityStatus`,
    90	  `IntakeStatus`, `PacketStatus`, `AssignmentStatus`, `DispatchOfferStatus`,
    91	  `LeaseStatus`, `MailboxDeliveryStatus`, `ReservationStatus`,
    92	  `FleetExperimentStatus`, `CapabilityAssessmentStatus`, `EffectStatus`, and
    93	  `ReconciliationStatus`;
    94	- `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, `ModuleStatus`,
    95	  `RouteStatus`, `ExtensionStatus`, and `CompatibilityStatus`;
    96	- observation, finding, review-verdict, checker, gate, decision, grant, permit,
    97	  artifact, migration, sync, update, and cutover states;
    98	- role IDs and incompatible-role combinations; and
    99	- `SDLC-*`, `AI-G*`, `MAP-*`, and `SDLC-ADOPT-*` gate namespaces.
   100	
   101	## 4. Subject binding
   102	
   103	A child artifact either embeds one full discriminated subject or references one
   104	through `SubjectBindingV1`:
   105	
   106	```yaml
   107	subject_schema: work-subject/v1 # or exact/architecture/research/resource subject
   108	subject_ref: art_<uuidv7>
   109	subject_digest: sha256:<hex>
   110	subject_manifest_digest: null
   333	## 6. Artifact family and producer authority
   334	
   335	| Artifact | Canonical producer | Purpose | Cannot authorize |
   336	|---|---|---|---|
   337	| `CoreSDLCTrace` | `configuration_management` traceability compiler | Content-address the accepted project/work/control/requirement/criterion/baseline and exact-subject bindings reused by child artifacts | Mutate its sources, change `WorkItemStatus`, lower risk, or authorize work/effects |
   338	| `WorkIntake` | Work-intake service under duty/product owner | Capture signal and initial facts | Priority, lower risk, dispatch |
   339	| `ResearchPacket` | Research activity | Bind sources, claims, contradictions, unknowns | Architecture/product decision |
   340	| `ArchitectureReviewPacket` | Packet compiler | Freeze exact design-review subject | Acceptance |
   341	| `ArchitectureProposal` | Specialist worker | Proposed boundaries/tree/trade-offs | Its own acceptance |
   342	| `ArchitectureReconciliation` | Synthesizer plus finding records | Resolve proposal/challenge against evidence | Human ADR decision |
   343	| `TaskPacket` | Deterministic packet compiler | Authorize one bounded worker run and bind its exact engineering-practice application profile | Expanded scope, book-derived authority, or merge/release |
   344	| `AgentAssignment` | `agent_collaboration` | Bind eligible packet, role, workspace, topology, reservation, and deadline | Work/run transition or claim |
   345	| `DispatchOffer` | `agent_collaboration` offer service | Bind one expiring eligibility invitation to an assignment, optional named principal, and immutable eligibility policy | Grant authority or claim an assignment outside atomic claim |
   346	| `WorkerAttempt` | `agent_collaboration` attempt service | Bind one principal/session/route/harness/workspace/lease epoch to one assignment and immutable result lineage | Work/run transition, retry policy, or broader lease |
   347	| `WorkerLease` | `agent_collaboration` atomic claim service | Time-bound one attempt with fencing epoch | Broader scope or authority |
   348	| `MailboxEnvelope` | `agent_collaboration` mailbox service | Durable typed coordination reference | Recipient command acceptance or authority |
   349	| `FleetExperiment` | `process_assurance` | Predeclare and retain fleet/control measurement | Change active topology/policy by itself |
   350	| `ResourceReservation` | `resource_governance` | Bind hierarchical admitted limits and settled usage to an exact subject | Authorize an effect, exceed an ancestor, or declare work complete |
   351	| `CapabilityAssessment` | `process_assurance` under accountable assessor/approver roles | Diagnose one exact capability/control scope with separate level, effectiveness, coverage, confidence, and improvement priority | Authorize a transition, average away a vital-control failure, or rank people |
   352	| `CapabilityDomainProjection` | `process_assurance` deterministic projection service under accountable assessor/approver roles | Bind the exact registered control-tuple set for one domain/scope/window and derive result, lowest supported level, and highest-precedence priority | Author a member assessment, omit/duplicate/remap a registry tuple, arithmetically aggregate levels, or authorize a transition |
   353	| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
   354	| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
   355	| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
   356	| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
   357	| `ReviewObservation` | Reviewer/model normalization | Findings, uncertainty, limitations | Gate outcome |
   358	| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
   359	| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
   360	| `ReviewRecordProjection` | Projection builder | Read model joining immutable review records for navigation | Replace or mutate its source records |
   361	| `CheckerResult` | Qualified deterministic checker wrapper | One reproducible check outcome | Aggregate gate alone |
   362	| `EvidenceSnapshot` | Assurance service | Freeze exact eligible evidence set | Decision by itself |
   363	| `GateEvaluation` | Qualified gate evaluator | Produce runtime `GateOutcome` | Human decision |
   364	| `HumanDecisionRecord` | Policy after IAM authentication | Record accountable human choice | Direct effect execution |
   365	| `ConsumableAuthorityGrant` | Governed execution | One-shot eligible decision snapshot | Broader/different action |
   366	| `Permit` | Governed execution after gate/decision | One-shot exact effect/transition capability | Another subject/action |
   367	| `LandingRecord` | Workspace/Git adapter normalization | Prove candidate-to-landed relation | Release/closure |
   368	| `PostLandingVerification` | Assurance service | Verify landed subject | Product outcome |
   369	| `ReleaseEvidence` | Release management | Build/promotion/rollback facts | Service/product acceptance |
   370	| `OperationEvidence` | Operations/service evidence ingestion | Health/support/recovery facts | Product outcome |
   371	| `OutcomeReview` | Product definition under product owner | Compare outcome and decide keep/change/remove | Rewrite engineering facts |
   372	| `TransitionEvent` | Owning aggregate UoW | Durable accepted state fact | State owned by another aggregate |
   373	
   374	## 7. Review separation
   375	
   376	Review is five immutable records, not one mutable model response:
   377	
   378	```text
   379	ReviewRequest
   380	  -> AnalysisAttempt[1..N]
   381	  -> ReviewObservation[0..N]
   382	  -> IndependenceEvaluation
   383	  -> ReviewVerdict
   384	  -> EvidenceSnapshot
   385	  -> GateEvaluation
   386	```
   387	
   388	`ReviewRequest` records maker principal/run/session/role, exact subject,
   389	separate review packet, required reviewer role, prohibited capabilities, blind
   390	context manifest, diversity requirements expressed as actual route facts, and
   391	qualification policy.
   392	
   393	Each `AnalysisAttempt` records reviewer principal/role/session, actual
   394	provider/model/transport/executable/parser/isolation identities, route lock,
   395	input/output artifact digests, start/end/deadline/budget, granted capabilities,
   396	write attempts, failures, usage, and relation to previous attempts.
   397	
   398	`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
   399	self-assertion and a model-family label are insufficient. It compares maker and
   400	reviewer identities/sessions, packet construction, write capability/activity,
   401	blindness manifest, route/provider/transport facts, qualification, hidden
   402	fixture isolation, and candidate identity.
   403	
   404	`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
   405	`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
   406	not `GateOutcome`.
   407	
   408	### 7.1 Deadline and budget null semantics
   409	
   410	In draft templates, `null` means **not established**. It never means unlimited.
   411	A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
   412	reservation cannot become `ACTIVE` while a policy-required deadline or budget
   413	dimension is null. Zero denies consumption of that dimension. A dimension may
   414	be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
   415	reason, accountable owner, and evidence reference.
   416	
   417	Every activated execution/review reservation has an absolute deadline and all
   418	transitive dimensions required by its risk/work-class policy. Child limits are
   419	no later/larger than every ancestor. Canonical validation rejects negative,
   420	ambiguous, unitless, floating-point, or “unlimited” sentinel values.
   421	
   422	## 8. Finding lifecycle
   423	
   424	Every finding has category, severity, confidence/epistemic status, exact
   425	location, claim, impact, evidence, required action, owner, and state:
   426	
   427	```text
   428	OPEN
   429	  -> ACCEPTED
   430	  -> FIXED_PENDING_VERIFICATION
   431	  -> VERIFIED
   432	
   433	OPEN
   434	  -> DISPUTED
   435	  -> SPECIALIST_REVIEW
   436	  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
   437	```
   438	
   439	Only the review/finding application service changes finding state. A maker may
   440	submit a resolution proposal but cannot mark its finding verified.
   441	
   442	## 9. Gate, decision, grant, and permit order
   443	
   444	The required order is:
   445	
   446	```text
   447	eligible evidence
   448	  -> EvidenceSnapshot
   449	  -> GateEvaluation
   450	  -> authenticated HumanDecisionRecord when policy requires
   451	  -> ConsumableAuthorityGrant
   452	  -> Permit
   453	  -> atomic permit consumption + effect intent
   454	```
   455	
   456	`GateEvaluation` binds gate ID/version, namespace, policy, required and observed
   457	claims, checker qualifications/results, applicability proof, freshness,
   458	coverage, conflicting/missing evidence, exact subject, evaluator code digest,
   459	and one `GateOutcome`.
   460	
   461	`HumanDecisionRecord` discriminates:
   462	
   463	- `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`;
   464	- `RISK_ACCEPTANCE_OR_WAIVER`;
   465	- `WORK_TRANSITION`;
     1	# Authoring skeleton; executable schema is registered under schemas/. Empty placeholders are invalid for SEALED or runtime artifacts.
     2	schema_version: "1"
     3	artifact_type: review_observation
     4	observation_id: "observation_<uuidv7>"
     5	review_request_id: "review_<uuidv7>"
     6	analysis_attempt_id: "attempt_<uuidv7>"
     7	subject_schema: null
     8	subject_ref: ""
     9	subject_digest: ""
    10	subject_manifest_digest: null
    11	core_sdlc_trace_ref: ""
    12	state: EVALUATION_INCOMPLETE
    13	summary: ""
    14	findings:
    15	  - finding_id: "finding_<uuidv7>"
    16	    category: ""
    17	    severity: ""
    18	    confidence: ""
    19	    epistemic_status: INFERENCE
    20	    location: ""
    21	    claim: ""
    22	    impact: ""
    23	    evidence_refs: []
    24	    required_action: ""
    25	    owner_ref: null
    26	    state: OPEN
    27	    reconciliation_ref: null
    28	uncertainties: []
    29	limitations: []
    30	proposed_actions: []
    31	digest: ""
   145	      predicate_rule_ref: ""
   146	      query_ref: ""
   147	      query_digest: ""
   148	      eligible: 0
   149	      included: 0
   150	      excluded: 0
   151	      derived_result: NOT_CHECKED
   152	  adverse_reconciliation_result: NOT_CHECKED
   153	
   154	evidence:
   155	  event_query_ref: ""
   156	  event_query_digest: ""
   157	  evidence_snapshot_refs: []
   158	  enacted_practice_refs: []
   159	  artifact_and_provenance_refs: []
   160	  outcome_and_guardrail_refs: []
   161	  normal_path_event_refs: []
   162	  traversed_rejection_invalidation_exception_or_backward_event_refs: []
   163	  data_quality_result_ref: ""
   164	  limitations: []
   165	
   166	capability_rating:
   167	  # SCORED also requires gap_register.reconciliation.scored_eligibility_result PASS.
   168	  result: NOT_ASSESSED # NOT_ASSESSED | UNKNOWN | NOT_APPLICABLE | SCORED
   169	  level: null # null unless SCORED; otherwise 0 | 1 | 2 | 3 | 4
   170	  label: ""
   171	  criterion_evidence:
   172	    - criterion_id: ""
   173	      evidence_refs: []
   174	      result: UNKNOWN
   175	  ordinal_label_only: true
   176	  arithmetic_aggregation_prohibited: true
   177	
   178	effectiveness:
   179	  result: UNKNOWN # UNKNOWN | REGRESSING | MIXED | MEETS_TARGET
   180	  metric_spec_ids: []
   181	  baseline_refs: []
   182	  comparator_refs: []
   183	  observed_result_refs: []
   184	  distribution_and_trend_refs: []
   185	  guardrail_result_refs: []
   186	
   187	# Level 3/4 and every experiment supporting level 4 bind this immutable design.
   188	measurement_design:
   189	  design_id: ""
   190	  design_version: ""
   191	  design_digest: ""
   192	  goal_question_decision_refs: []
   193	  metric_spec_refs: []
   194	  metric_registry_id: "METRIC-SDLC-001"
   195	  metric_registry_version: "1.0.0"
   196	  fixed_comparator_ref: ""
   197	  prospective_decision_rule_ref: ""
   198	  decision_rule_frozen_at: ""
   199	  minimum_meaningful_effect: ""
   200	  minimum_detectable_effect: ""
   201	  analysis_method_ref: ""
   202	  analysis_assumption_check_refs: []
   203	  decision_rule_evaluation_ref: ""
   204	  noise:
   205	    status: NOT_ASSESSED # NOT_ASSESSED | ESTABLISHED | NOT_APPLICABLE
   206	    floor: null
   207	    method_ref: ""
   208	    zero_claim_evidence_ref: ""
   209	    zero_claim_independent_approval_ref: ""
   210	    uncertainty_na_rule_ref: ""
   211	    uncertainty_na_approval_ref: ""
   212	  harness:
   213	    harness_id: ""
   214	    harness_version: ""
   215	    harness_digest: ""
   216	    configuration_ref: ""
   217	    configuration_digest: ""
   218	    qualification_result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
   219	    qualification_ref: ""
   220	    repeatability_test_refs: []
   221	    data_quality_test_refs: []
   222	  outcome_accounting:
   223	    subject_failure_count: 0
   224	    infrastructure_error_count: 0
   225	    infrastructure_error_ledger_ref: ""
   226	
   227	# Coverage is a view over population; it carries no duplicate count fields.
   228	coverage:
   229	  population_ref: "#/population"
   230	  percentage: null # Output-only computed field; authored input must be null.
   231	  percentage_formula: "population.totals.included / population.totals.eligible * 100; null when eligible = 0"
   232	  by_joint_strata_ref: "#/population/joint_strata"
   233	  reconciliation_result: NOT_CHECKED
   234	
   235	# One register owns every evidence, population, coverage, measurement, and
   236	# applicability gap. HIGH cannot omit a known material gap.
   237	gap_register:
   238	  inventory_query_ref: ""
   239	  inventory_query_digest: ""
   240	  entries:
   241	    - gap_id: ""
   242	      source_dimension: "" # EVIDENCE | POPULATION | COVERAGE | MEASUREMENT | APPLICABILITY
   243	      source_ref: ""
   244	      materiality: UNKNOWN # UNKNOWN | NON_MATERIAL | MATERIAL
   245	      disposition: OPEN # OPEN | ACCEPTED_LIMITATION | CORRECTED | SUPERSEDED
   246	      disposition_evidence_ref: ""
   247	  reconciliation:
   248	    source_inventory_complete_result: NOT_CHECKED
   249	    every_gap_disposed_result: NOT_CHECKED
   250	    unresolved_material_gap_refs: []
   251	    scored_eligibility_result: NOT_CHECKED
   252	    result: NOT_CHECKED
   253	
   254	# Confidence is rule-derived. HIGH requires all seven tests PASS and independent
   255	# sign-off. Any material unresolved gap forces LOW.
   256	confidence:
   257	  adequacy_rule:
   258	    rule_id: ""
   259	    rule_version: ""
   260	    rule_digest: ""
   261	    approval_ref: ""
   262	  tests:
   263	    sample:
   264	      result: NOT_CHECKED # NOT_CHECKED | PASS | FAIL
   265	      evidence_refs: []
   266	    duration:
   267	      result: NOT_CHECKED
   268	      evidence_refs: []
   269	    representativeness:
   270	      result: NOT_CHECKED
   271	      evidence_refs: []
   272	    authenticity:
   273	      result: NOT_CHECKED
   274	      evidence_refs: []
   275	    freshness:
   276	      result: NOT_CHECKED
   277	      evidence_refs: []
   278	    missingness:
   279	      result: NOT_CHECKED
   280	      evidence_refs: []
   281	    data_quality:
   282	      result: NOT_CHECKED
   283	      evidence_refs: []
   284	  gap_register_ref: "#/gap_register"
   285	  independent_assurance_signoff_ref: ""
   286	  derived_level: LOW # LOW | MEDIUM | HIGH
   287	  derivation_result: NOT_CHECKED
   288	  rationale: ""
   289	
   290	# Evaluate every registry trigger and apply P0 > P1 > P2 > P3. The first
   291	# matching tier wins. Valid NOT_APPLICABLE has no tier.
   292	priority:
   293	  priority_rule_id: "PRIORITY-SDLC-001"
   294	  priority_rule_version: "1.0.0"
   295	  priority_rule_digest: ""
   296	  result: NOT_EVALUATED # NOT_EVALUATED | NOT_APPLICABLE | ASSIGNED
   297	  evaluated_trigger_results:
   298	    - trigger_code: ""
   299	      result: NOT_CHECKED # NOT_CHECKED | MATCH | NO_MATCH
   300	      evidence_refs: []
   301	  trigger_set_validation:
   302	    exact_registry_trigger_set_result: NOT_CHECKED
   303	    no_duplicate_trigger_result: NOT_CHECKED
   304	    validation_evidence_refs: []
   305	  matched_trigger_codes: []
   306	  decisive_trigger_code: ""
   307	  derived_tier: null # null | P0_CONTROL_NOW | P1_IMPROVE_NEXT | P2_IMPROVE_DELIBERATELY | P3_SUSTAIN
   308	  instrumentation_action_ref: ""
   309	  derivation_result: NOT_CHECKED
   310	  consequence: ""
   311	  exposure: ""
   312	  recurrence: ""
   313	  downstream_blocking: ""
   314	  capability_gap: ""
   315	
   316	findings:
   317	  active_harm_refs: []
   318	  invariant_breach_refs: []
   319	  nonconformity_refs: []
   320	  exception_refs: []
   321	  gate_outcome_refs: []
   322	
   323	improvement:
   324	  linked_work_item_id: ""
   325	  causal_stage: ""
   326	  causal_control_id: ""
   327	  hypothesis: ""
   328	  bounded_change: ""
   329	  measurement_design_ref: ""
   330	  measurement_design_digest: ""
   331	  owner_id: ""
   332	  evidence_window_end: ""
   333	  stop_or_revert_criteria: []
   334	  review_date: ""
   335	  effectiveness_review_ref: ""
   336	  decision: "" # RETAIN | SCALE | SIMPLIFY | CHANGE | REVERT
   337	
   338	decision_ref: ""
   339	approved_at: ""
   340	prior_assessment_ref: ""
   341	supersedes_ref: ""
   342	correction_reason: ""
   343	created_at: ""
   344	digest: ""
   280	    "PROPOSAL",
   281	    "REPORTED_ADVISORY_RESULT",
   282	)
   283	
   284	
   285	ARTIFACT_SCHEMAS: dict[str, tuple[str, str]] = {
   286	    "AGENT_ASSIGNMENT.yaml": ("fleet/assignment-v1.schema.json", "agent_collaboration"),
   287	    "AI_HANDOFF.yaml": ("execution/agent-handoff-v1.schema.json", "agent_collaboration"),
   288	    "AI_TASK_PACKET.yaml": ("work/task-packet-v1.schema.json", "context_compilation"),
   289	    "ANALYSIS_ATTEMPT.yaml": ("review/analysis-attempt-v1.schema.json", "analytical_review"),
   290	    "ARCHITECTURE_PROPOSAL.yaml": ("architecture/proposal-v1.schema.json", "analytical_review"),
   291	    "ARCHITECTURE_RECONCILIATION.yaml": ("architecture/reconciliation-v1.schema.json", "analytical_review"),
   292	    "ARCHITECTURE_REVIEW_PACKET.yaml": ("architecture/review-packet-v1.schema.json", "context_compilation"),
   293	    "AUTHORITY_GRANT.yaml": ("authority/authority-grant-v1.schema.json", "governed_execution"),
   294	    "CAPABILITY_ASSESSMENT.yaml": ("process/capability-assessment-v1.schema.json", "process_assurance"),
   295	    "CAPABILITY_DOMAIN_PROJECTION.yaml": ("process/capability-domain-projection-v1.schema.json", "process_assurance"),
   296	    "CHECKER_RESULT.yaml": ("assurance/checker-result-v1.schema.json", "assurance"),
   297	    "CORE_SDLC_TRACE.yaml": ("common/core-sdlc-trace-v1.schema.json", "configuration_management"),
   298	    "DISPATCH_OFFER.yaml": ("fleet/dispatch-offer-v1.schema.json", "agent_collaboration"),
   299	    "EVIDENCE_SNAPSHOT.yaml": ("assurance/evidence-snapshot-v1.schema.json", "assurance"),
   300	    "FLEET_EXPERIMENT.yaml": ("fleet/fleet-experiment-v1.schema.json", "process_assurance"),
   301	    "GATE_EVALUATION.yaml": ("assurance/gate-evaluation-v1.schema.json", "assurance"),
   302	    "HUMAN_DECISION.yaml": ("authority/human-decision-v1.schema.json", "policy"),
   303	    "INDEPENDENCE_EVALUATION.yaml": ("review/independence-evaluation-v1.schema.json", "analytical_review"),
   304	    "LANDING_RECORD.yaml": ("execution/landing-record-v1.schema.json", "workspace"),
   305	    "MAILBOX_ENVELOPE.yaml": ("fleet/mailbox-envelope-v1.schema.json", "agent_collaboration"),
   306	    "OPERATION_EVIDENCE.yaml": ("lifecycle/operation-evidence-v1.schema.json", "operations"),
   307	    "OUTCOME_REVIEW.yaml": ("lifecycle/outcome-review-v1.schema.json", "product_definition"),
   308	    "PERMIT.yaml": ("authority/permit-v1.schema.json", "governed_execution"),
   309	    "POST_LANDING_VERIFICATION.yaml": ("execution/post-landing-verification-v1.schema.json", "assurance"),
   310	    "RELEASE_EVIDENCE.yaml": ("lifecycle/release-evidence-v1.schema.json", "release_management"),
   311	    "RESEARCH_PACKET.yaml": ("research/research-packet-v1.schema.json", "product_definition"),
   312	    "RESOURCE_RESERVATION.yaml": ("resources/resource-reservation-v1.schema.json", "resource_governance"),
   313	    "REVIEW_OBSERVATION.yaml": ("review/review-observation-v1.schema.json", "analytical_review"),
   314	    "REVIEW_RECORD.yaml": ("review/review-record-projection-v1.schema.json", "analytical_review"),
   315	    "REVIEW_REQUEST.yaml": ("review/review-request-v1.schema.json", "analytical_review"),
   316	    "REVIEW_VERDICT.yaml": ("review/review-verdict-v1.schema.json", "analytical_review"),
   317	    "RUN_RESULT.yaml": ("execution/run-result-v1.schema.json", "agent_collaboration"),
   318	    "TRANSITION_EVENT.yaml": ("work/transition-event-v1.schema.json", "owning_aggregate_uow"),
   319	    "WORKER_ATTEMPT.yaml": ("fleet/worker-attempt-v1.schema.json", "agent_collaboration"),
   320	    "WORKER_LEASE.yaml": ("fleet/lease-v1.schema.json", "agent_collaboration"),
   321	    "WORK_INTAKE.yaml": ("work/work-intake-v1.schema.json", "work_management"),
   322	}
   323	
   324	GENERATED_ARTIFACT_SCHEMAS: tuple[dict[str, str], ...] = (
   325	    {
     1	# Ranex Personal-Use Source License 1.0
     2	
     3	Copyright (c) 2026 Anthony Garces. All rights reserved.
     4	
     5	This is a source-available license. It is not an open-source license.
     6	
     7	## 1. Scope
     8	
     9	This license applies only to original Ranex code, documentation, configuration,
    10	artwork, and modifications owned by Anthony Garces (the "Ranex Material").
    11	
    12	It does not apply to Hermes Agent material or any other third-party material.
    13	Those portions remain governed by their own licenses. When Hermes Agent
    14	material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
    15	
    16	## 2. Personal-use permission
    17	
    18	Subject to every condition below, an individual may view, copy, run, study, and
    19	privately modify the Ranex Material solely for personal learning,
    20	experimentation, or evaluation.
    21	
    22	This permission is personal, limited, non-exclusive, and non-transferable. All
    23	copyright, license, attribution, and source notices must remain intact.
    24	
    25	## 3. Restrictions
    26	
    27	Except for the limited GitHub-platform rights in section 4, and unless Anthony
    28	Garces gives prior written permission, you may not:
    29	
    30	1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
    31	   or otherwise provide the Ranex Material or a modified version to anyone;
    32	2. make the Ranex Material available through a public or shared repository,
    33	   download, package, service, hosted application, network endpoint, or device;
    34	3. use the Ranex Material for any commercial, business, employment,
    35	   professional, institutional, revenue-generating, or client purpose;
    36	4. use the Ranex Material to operate, support, develop, or improve a product,
    37	   service, organization, or business process;
    38	5. remove, hide, or alter a copyright, license, provenance, or attribution
    39	   notice;
    40	6. claim authorship or ownership of Ranex Material created by Anthony Garces,
    41	   or present that material as your own work;
    42	7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
    43	   ownership; or
    44	8. grant another person rights that this license does not grant to you.
    45	
    46	You may identify original changes that you created privately, but that does not
    47	give you ownership of the underlying Ranex Material or permission to
    48	redistribute the combined work.
    49	
    50	## 4. Public GitHub repository
    51	
    52	While the repository is public, GitHub's Terms of Service grant GitHub users
    53	limited permission to use, display, perform, and reproduce repository content
    54	through GitHub's service as its features allow, including by forking it. This
    55	license does not restrict those platform rights.
    56	
    57	Those platform permissions do not grant permission to redistribute the Ranex
    58	Material outside GitHub's service, use it for business, remove its notices, or
    59	claim it as your own.
    60	
    61	## 5. Ownership and third-party rights
    62	
    63	The Ranex Material is licensed, not sold. Anthony Garces retains all rights
    64	not expressly granted here.
    65	
    66	No term in this license reduces a right granted directly by the MIT License or
    67	another applicable third-party license. When a file contains both upstream
    68	material and original Ranex modifications, each portion remains governed by
    69	its applicable license.
    70	
    71	## 6. Termination
    72	
    73	Your permission under this license ends automatically when you violate it.
    74	After termination, you must stop using the Ranex Material and delete copies in
    75	your possession or control, except copies GitHub retains under its Terms of

web search: 
web search: https://www.rfc-editor.org/info/rfc9943/
web search: 
web search: site:learn.microsoft.com Microsoft Signing Transparency Ledger generally available SCITT COSE receipts ...
web search: 
web search: https://www.w3.org/TR/prov-o/
exec
/bin/bash -lc 'for f in schemas/review/review-request-v1.schema.json schemas/review/analysis-attempt-v1.schema.json schemas/review/independence-evaluation-v1.schema.json schemas/review/review-verdict-v1.schema.json schemas/review/review-record-projection-v1.schema.json schemas/assurance/evidence-snapshot-v1.schema.json; do echo "$f"; nl -ba "$f" | sed -n '"'1,235p' | rg -n 'blind_context|maker|packet_digest|prohibited|qualification|required_independence|route_diversity|review_spec|subject_digest|input_|output_|raw_output|provider|model|transport|executable|parser|isolation|write|checks|eligible|validator|open_finding|resolved_finding|reconciliation|observation_ids|evidence_refs|source_registry|review_request_digest|independence_evaluation_digest|review_verdict_digest|required_claim|eligible_evidence|ineligible_evidence|coverage|conflict|missing_claim|policy_activation' ; done" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
schemas/review/review-request-v1.schema.json
13:    13	    "blind_context_manifest_digest": {
24:    24	    "maker": {
48:    48	    "packet_digest": {
55:    55	    "prohibited_capabilities": {
61:    61	    "qualification_policy_id": {
67:    67	    "required_independence": {
78:    78	    "review_spec_id": {
81:    81	    "review_spec_version": {
87:    87	    "subject_digest": {
111:   111	    "review_spec_id",
112:   112	    "review_spec_version",
114:   114	    "packet_digest",
117:   117	    "subject_digest",
120:   120	    "maker",
122:   122	    "required_independence",
123:   123	    "prohibited_capabilities",
124:   124	    "blind_context_manifest_digest",
126:   126	    "qualification_policy_id",
schemas/review/analysis-attempt-v1.schema.json
37:    37	    "input_artifact_refs": {
41:    41	    "input_manifest_digest": {
51:    51	    "raw_output_artifact_ref": {
54:    54	    "raw_output_digest": {
90:    90	        "actual_model_id": {
93:    93	        "actual_model_snapshot": {
99:    99	        "actual_provider_id": {
102:   102	        "executable_digest": {
106:   106	        "isolation_profile_id": {
109:   109	        "parser_version": {
115:   115	        "transport_digest": {
119:   119	        "transport_id": {
125:   125	        "actual_provider_id",
126:   126	        "actual_model_id",
127:   127	        "actual_model_snapshot",
128:   128	        "transport_id",
129:   129	        "transport_digest",
130:   130	        "executable_digest",
131:   131	        "parser_version",
132:   132	        "isolation_profile_id"
149:   149	    "subject_digest": {
174:   174	    "write_attempt_evidence_refs": {
187:   187	    "subject_digest",
192:   192	    "input_artifact_refs",
193:   193	    "input_manifest_digest",
195:   195	    "write_attempt_evidence_refs",
203:   203	    "raw_output_artifact_ref",
204:   204	    "raw_output_digest",
schemas/review/independence-evaluation-v1.schema.json
17:    17	    "checks": {
20:    20	        "blind_context_satisfied": {
23:    23	            "evidence_refs": {
33:    33	            "evidence_refs"
40:    40	            "evidence_refs": {
50:    50	            "evidence_refs"
54:    54	        "maker_reviewer_identity_separated": {
57:    57	            "evidence_refs": {
67:    67	            "evidence_refs"
71:    71	        "maker_reviewer_session_separated": {
74:    74	            "evidence_refs": {
84:    84	            "evidence_refs"
91:    91	            "evidence_refs": {
101:   101	            "evidence_refs"
105:   105	        "reviewer_had_no_write_or_authority_capability": {
108:   108	            "evidence_refs": {
118:   118	            "evidence_refs"
125:   125	            "evidence_refs": {
135:   135	            "evidence_refs"
142:   142	            "evidence_refs": {
152:   152	            "evidence_refs"
158:   158	        "maker_reviewer_identity_separated",
159:   159	        "maker_reviewer_session_separated",
162:   162	        "reviewer_had_no_write_or_authority_capability",
163:   163	        "blind_context_satisfied",
176:   176	    "eligible": {
192:   192	    "subject_digest": {
211:   211	    "validator_code_digest": {
215:   215	    "validator_id": {
218:   218	    "validator_version": {
230:   230	    "subject_digest",
233:   233	    "checks",
234:   234	    "eligible",
schemas/review/review-verdict-v1.schema.json
16:    16	    "evidence_refs": {
27:    27	    "observation_ids": {
31:    31	    "open_finding_refs": {
42:    42	    "reconciliation_refs": {
46:    46	    "resolved_finding_refs": {
56:    56	    "subject_digest": {
87:    87	    "observation_ids",
91:    91	    "subject_digest",
95:    95	    "open_finding_refs",
96:    96	    "resolved_finding_refs",
97:    97	    "reconciliation_refs",
98:    98	    "evidence_refs",
schemas/review/review-record-projection-v1.schema.json
30:    30	    "independence_evaluation_digest": {
44:    44	    "review_request_digest": {
51:    51	    "review_verdict_digest": {
61:    61	    "source_registry_version": {
64:    64	    "subject_digest": {
90:    90	    "subject_digest",
94:    94	    "review_request_digest",
98:    98	    "independence_evaluation_digest",
100:   100	    "review_verdict_digest",
103:   103	    "source_registry_version",
schemas/assurance/evidence-snapshot-v1.schema.json
9:     9	    "conflicts": {
16:    16	    "coverage": {
31:    31	    "eligible_evidence_refs": {
38:    38	    "ineligible_evidence": {
57:    57	    "missing_claim_ids": {
61:    61	    "policy_activation_id": {
64:    64	    "policy_activation_manifest_digest": {
68:    68	    "required_claim_ids": {
78:    78	    "subject_digest": {
104:   104	    "subject_digest",
107:   107	    "policy_activation_id",
108:   108	    "policy_activation_manifest_digest",
109:   109	    "required_claim_ids",
110:   110	    "eligible_evidence_refs",
111:   111	    "ineligible_evidence",
113:   113	    "coverage",
114:   114	    "missing_claim_ids",
115:   115	    "conflicts",

web search: 
web search: Grafeas occurrence vulnerability build attestation official specification license production adopters ...
Repository tracing and external verification are complete. I mapped each Ranex sub-layer to the strongest ratified standard or deployed implementation, checked licences and adoption evidence, and isolated conclusions that are inferences.
  ✓ Inspect Ranex review schemas, architecture contracts, templates, generator, licence, and hash-chain ledger with exact line references
  ✓ Verify prior-art standards, competitors, licences, and production adoption from primary external sources
  ✓ Map each Ranex layer/sub-layer to ADOPT, ADAPT, DIVERGE, or NOVEL with actionable deltas
  ✓ Audit citations, inference labels, search coverage, and read-only compliance; deliver report
codex
Ranex mostly recomposes established standards. Its strongest unmatched element is the exact, machine-evaluable bundle of AI-review independence checks—not the underlying independence principle.

The JSON schemas are generated from templates ([contract rule](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:26), [generator registry](/home/soultransit/devtony/ranex/scripts/architecture/generate_contracts.py:285)). Therefore, every schema delta below means: change the corresponding authoring template and `generate_contracts.py`, then regenerate; do not hand-edit generated JSON.

## Mapping table

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
|---|---|---|---|---|
| [AI_ARTIFACT_CONTRACTS.md:39](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:39) | Canonicalizes JSON with RFC 8785, removes `digest`, then computes a SHA-256 identifier. | [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) | **ADOPT** | Already adopted correctly. Keep RFC 8785 normative and use its published test vectors; do not introduce a Ranex-specific canonicalization variant. |
| [review-observation-v1.schema.json:48](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:48), [template:15](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:15) | A finding has free-string `category` and `claim`, plus `finding_id`. It does not identify the violated rule separately. | [OASIS SARIF 2.1.0 `result`, `ruleId`, `message`, `guid`, and fingerprints](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) | **ADOPT** | Use SARIF `result.ruleId` for the violated rule and `result.message` for `claim`; transport `finding_id` as `result.guid`. Use `partialFingerprints` for stable matching across revisions. Do not overload `category` as a rule identifier. |
| [review-observation-v1.schema.json:94](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:94), [template:17](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:17) | `severity` is an unconstrained string. | [SARIF `result.level`](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html); security-specific competitor: [OCSF Detection Finding severity](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **ADOPT** | Replace the interchange value with SARIF `none`, `note`, `warning`, or `error`. If Ranex needs risk magnitude beyond diagnostic level, carry it separately rather than extending `result.level`. Map imported security findings from OCSF’s wider severity vocabulary at the adapter boundary. |
| [review-observation-v1.schema.json:54](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:54), [template:18](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:18) | `confidence` is a required but unconstrained string. | [CycloneDX 1.7 Attestation confidence: score and rationale](https://cyclonedx.org/docs/1.7/proto/); [OCSF confidence ID and score](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **ADAPT** | Represent interchange confidence as CycloneDX’s bounded `0..1` score plus rationale. Preserve a Ranex-derived band only as a projection. For security telemetry, define a lossless adapter to OCSF confidence rather than accepting arbitrary text. |
| [review-observation-v1.schema.json:57](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:57), [AI_ARTIFACT_CONTRACTS.md:424](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:424) | Distinguishes `FACT`, `INFERENCE`, `OWNER_REQUIREMENT`, `PROPOSAL`, and `REPORTED_ADVISORY_RESULT`; facts require evidence. | [CycloneDX Attestations claims, counterclaims, evidence, conformance and confidence](https://cyclonedx.org/use-cases/attestations/); [W3C PROV-O attribution and derivation](https://www.w3.org/TR/prov-o/) | **ADAPT** | Keep epistemic classification as a Ranex namespaced extension, but model the underlying assertion as a CycloneDX claim/counterclaim and its origin/derivation with PROV. Do not map this field to SARIF “precision”: SARIF precision measures rule quality, not the epistemic status of one claim. |
| [review-observation-v1.schema.json:66](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:66), [evidence-ref.schema.json:6](/home/soultransit/devtony/ranex/schemas/common/evidence-ref.schema.json:6) | Finding `evidence_refs.items` is unconstrained and does not reference the existing `{evidence_ref,evidence_digest}` type. | [CycloneDX declarations/evidence](https://cyclonedx.org/docs/1.7/proto/); [OSCAL observation `relevant-evidence` and hashed back-matter resources](https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/json-definitions/) | **ADOPT** | Replace opaque array items with standard evidence references: CycloneDX `bom-ref` links for claim evidence or OSCAL `relevant-evidence.href` links backed by hashed resources. Remove the parallel untyped representation. |
| [review-observation-v1.schema.json:76](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:76), [template:20](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:20) | `location` is one free string; `required_action` is prose. | [SARIF `locations`, `physicalLocation`, `logicalLocations`, `region`, `relatedLocations`, `attachments`, and `fixes`](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) | **ADOPT** | Use SARIF location objects with artifact URI plus region/logical location. Express machine-applicable corrections as SARIF `fixes`; keep prose only as rule help or message text. Use `relatedLocations`/`attachments` for supporting locations and excerpts. |
| [AI_ARTIFACT_CONTRACTS.md:427](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:427), [review-verdict-v1.schema.json:31](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:31) | Maintains a service-controlled lifecycle including dispute, specialist review, verification, and human risk acceptance; verdicts list open and resolved findings. | [SARIF `baselineState`, fingerprints and suppressions](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html); [OCSF finding status](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **DIVERGE** | Keep Ranex’s authoritative workflow because SARIF and OCSF carry snapshots, not this segregation-of-duties state machine. Export `VERIFIED` changes using SARIF fingerprints/baseline state and risk acceptance using SARIF suppression status plus justification; do not treat the SARIF file as workflow authority. |
| [review-request-v1.schema.json:13](/home/soultransit/devtony/ranex/schemas/review/review-request-v1.schema.json:13), [AI_ARTIFACT_CONTRACTS.md:388](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:388) | Binds the assessment subject, packet, maker, reviewer requirements, prohibited capabilities, blind-context digest, route diversity and qualification policy. | [NIST OSCAL Assessment Plan](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/); [NIST SP 800-53 CA-2 independent assessors](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) | **ADAPT** | Make the request an OSCAL Assessment Plan/profile: express scope through reviewed controls and subjects, procedures through assessment activities, and assessors through responsible roles/parties. Retain blind-context, prohibited-capability and route-diversity requirements as namespaced OSCAL properties. |
| [AI_ARTIFACT_CONTRACTS.md:376](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:376), [review-verdict-v1.schema.json:27](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:27) | Separates request, attempts, observations, independence evaluation, verdict and evidence snapshot into immutable records. | [OSCAL Assessment Results](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/); [CycloneDX Attestations](https://cyclonedx.org/use-cases/attestations/) | **ADAPT** | Use an OSCAL Assessment Results document for results, reviewed controls, observations, findings, risks, attestations and assessment log. Use CycloneDX declarations when exchanging software-supply-chain claims/counterclaims. Preserve Ranex record separation as event provenance, not as a competing compliance interchange family. |
| [review-verdict-v1.schema.json:75](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:75), [AI_ARTIFACT_CONTRACTS.md:404](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:404) | Uses Ranex dispositions `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, and `INELIGIBLE`; explicitly not a gate outcome. | [OSCAL findings, risks and attestations](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/); [CycloneDX affirmation/signatories](https://cyclonedx.org/use-cases/attestations/) | **ADAPT** | Publish observations and findings in OSCAL and the signed conformance assertion in CycloneDX. Keep the four Ranex dispositions as a named profile vocabulary because neither standard defines this exact eligibility-versus-acceptability distinction. |
| [CAPABILITY_ASSESSMENT.yaml:154](/home/soultransit/devtony/ranex/docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:154), [CAPABILITY_ASSESSMENT.yaml:235](/home/soultransit/devtony/ranex/docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:235) | Combines control scope, evidence, ordinal capability, effectiveness, population coverage, gaps, confidence tests, findings and improvement actions. | [OSCAL Catalog/Profile/Assessment Results/POA&M models](https://pages.nist.gov/OSCAL-Reference/models/); competitor [CycloneDX requirements-to-claims/evidence attestations](https://cyclonedx.org/use-cases/machine-readable-standards/) | **ADAPT** | Represent obligations in OSCAL Catalog/Profile, assessment execution/results in Assessment Results, and gaps/remediation in POA&M. Carry Ranex ordinal capability and deterministic aggregation constraints as namespaced properties. Use CycloneDX only for exchanging software-supply-chain conformance claims, not as the control catalog. |
| [evidence-snapshot-v1.schema.json:31](/home/soultransit/devtony/ranex/schemas/assurance/evidence-snapshot-v1.schema.json:31) | Freezes eligible and ineligible evidence, required/missing claims, conflicts, coverage and policy activation against an exact subject. | [OSCAL observations, relevant evidence, findings and back matter](https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/json-definitions/) | **ADAPT** | Express eligible evidence as OSCAL observations and hashed back-matter resources; express missing/conflicting evidence as findings or risks. Retain policy-activation digest and Ranex eligibility decision as namespaced properties because OSCAL does not determine evidence eligibility policy. |
| [analysis-attempt-v1.schema.json:37](/home/soultransit/devtony/ranex/schemas/review/analysis-attempt-v1.schema.json:37), [analysis-attempt-v1.schema.json:87](/home/soultransit/devtony/ranex/schemas/review/analysis-attempt-v1.schema.json:87) | Records inputs, output, reviewer, provider/model, transport, executable, parser, isolation, timing, capabilities and write attempts. | [W3C PROV-O](https://www.w3.org/TR/prov-o/) and its [implementation report](https://www.w3.org/TR/prov-implementations/) | **ADAPT** | Expose each attempt as `prov:Activity`; inputs/outputs as `prov:Entity`; reviewer, model wrapper and service as `prov:Agent`/`prov:SoftwareAgent`; use `prov:used`, `wasGeneratedBy`, `wasAssociatedWith`, `hadRole`, and `wasInformedBy`. Keep exact route digests as domain attributes. |
| [review-record-projection-v1.schema.json:30](/home/soultransit/devtony/ranex/schemas/review/review-record-projection-v1.schema.json:30), [AI_ARTIFACT_CONTRACTS.md:360](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:360) | Joins source-record IDs/digests into a non-authoritative navigation projection. | [W3C PROV `Bundle` and `Collection`](https://www.w3.org/TR/prov-o/) | **ADAPT** | Publish a PROV Bundle/Collection containing the source entities and their relationships. Keep the existing projection only as a UI/read-model cache; it must not be the provenance interchange or evidence authority. |
| [AI_ARTIFACT_CONTRACTS.md:47](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:47), [evidence-ref.schema.json:6](/home/soultransit/devtony/ranex/schemas/common/evidence-ref.schema.json:6) | Content-addresses artifacts and evidence but provides no standard subject/predicate envelope or issuer signature. | [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) and [DSSE envelope](https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md) | **ADOPT** | Make each sealed Ranex artifact the predicate of an in-toto Statement. Put the artifact being claimed about in `subject[]` with an algorithm-keyed digest map, assign a stable `predicateType`, and sign the Statement using DSSE. The current internal `digest` may remain an object identifier but is not an attestation. |
| [generate_contracts.py:285](/home/soultransit/devtony/ranex/scripts/architecture/generate_contracts.py:285), [AI_ARTIFACT_CONTRACTS.md:26](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:26) | Generates executable schemas from templates but does not emit standardized build provenance. | [SLSA v1.2 Build Provenance](https://slsa.dev/spec/v1.2/build-provenance) | **ADOPT** | Emit SLSA provenance for every generated schema/checker set: generated files in `subject`; templates, generator and registries in `resolvedDependencies`; generator invocation in `buildDefinition`; qualified runner in `builder`; times and by-products in `runDetails`. Do not use SLSA for semantic review verdicts. |
| [independence-evaluation-v1.schema.json:17](/home/soultransit/devtony/ranex/schemas/review/independence-evaluation-v1.schema.json:17), [AI_ARTIFACT_CONTRACTS.md:398](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:398) | Deterministically evaluates identity/session separation, no-write authority, blind context, route/provider/transport diversity, qualification, hidden-fixture isolation and exact candidate identity, each with evidence. | Principles exist in [NIST SP 800-53 CA-2(1)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) and isolation of attester from target in [IETF RATS Architecture, RFC 9334](https://www.rfc-editor.org/rfc/rfc9334.html), but no matching interchange artifact was found. | **NOVEL** | Keep this as a Ranex extension, but identify its assessors and evidence through OSCAL and attest the result through in-toto/DSSE. Search for an equivalent covered assessor-independence schemas, blind evaluation manifests, model/provider-route diversity attestations, RATS evidence and AI evaluation provenance; none exposed this combined check set. |
| [hash_chain_ledger.py:20](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:20), [hash_chain_ledger.py:65](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:65) | Stores a local JSONL sequence whose entry hash covers sequence, previous digest and record digest; verification replays the local file. | [SCITT Architecture, RFC 9943](https://www.rfc-editor.org/info/rfc9943/) and [COSE Receipts, RFC 9942](https://www.rfc-editor.org/info/rfc9942/) | **ADOPT** | Replace the private hash-chain proof format with SCITT Signed/Transparent Statements and RFC 9942 receipts. A stored record must carry an issuer signature, registration-policy identity, signed inclusion receipt and verifiable-data-structure profile—not merely `previous_digest`. |
| [hash_chain_ledger.py:144](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:144), [hash_chain_ledger.py:206](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:206) | File permissions, locking and `fsync` improve local durability, but there are no signed checkpoints, inclusion/consistency proofs, witnesses or independently held receipts. | Public option: [Sigstore Bundle](https://docs.sigstore.dev/about/bundle/) and [Rekor](https://docs.sigstore.dev/logging/overview/). General Merkle design: [RFC 9162 Certificate Transparency](https://www.rfc-editor.org/rfc/rfc9162.html). Confidential option: [Azure Confidential Ledger/CCF receipts](https://learn.microsoft.com/en-us/azure/confidential-ledger/write-transaction-receipts). [Trillian is now in maintenance mode](https://github.com/google/trillian). | **ADAPT** | Use Sigstore/Rekor for publishable attestations and an RFC 9942/CCF-compatible private transparency service for confidential evidence. Persist the returned bundle/receipt with the evidence. Do not start a new deployment on Trillian; its maintainers recommend newer log implementations. |
| [review-observation-v1.schema.json:48](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:48) | Ranex is a general review format, including non-security architecture findings. | [OCSF Detection Finding](https://schema.ocsf.io/1.3.0/classes/detection_finding), deployed by [AWS Security Lake](https://docs.aws.amazon.com/security-lake/latest/userguide/open-cybersecurity-schema-framework.html); [SCAP/ARF](https://csrc.nist.gov/Projects/security-content-automation-protocol/SCAP-Releases/scap-1-3) | **DIVERGE** | Do not make OCSF or SCAP the canonical Ranex format: both are narrower security/technical-control ecosystems. Provide import/export adapters for OCSF security findings and SCAP ARF/XCCDF/OVAL results, then normalize them into SARIF/OSCAL. |

## Adopt shortlist

Ranked by immediate value to Ranex:

1. **SARIF 2.1.0 for review-finding interchange.** It is an OASIS Standard and is consumed in production by [GitHub code scanning](https://docs.github.com/en/enterprise-cloud@latest/code-security/reference/code-scanning/sarif-files/sarif-support). OASIS permits implementation and redistribution of specification material under its notices; the work uses an RF-on-RAND IPR mode. Compatible with Ranex’s all-rights-reserved model, provided required notices are retained. No copyleft.

2. **OSCAL for controls, assessments and evidence packages.** NIST lists all seven models as released and publishes XML, JSON and YAML tooling ([models](https://pages.nist.gov/OSCAL-Reference/models/), [tools](https://pages.nist.gov/OSCAL/resources/tools/)). NIST material/software is generally usable and distributable with its notice and attribution conditions ([NIST notice](https://pages.nist.gov/oscal-tools/about/)). Compatible; no copyleft. Maturity caveat: FedRAMP reported more than 100 Rev. 5 authorizations but no OSCAL submissions during its earlier pilot, so production exchange adoption lags model maturity ([FedRAMP RFC-0024](https://www.fedramp.gov/rfcs/0024/)).

3. **CycloneDX Attestations for software-supply-chain claims, counterclaims, evidence and confidence.** CycloneDX 1.7 is ECMA-424 and its schemas are Apache-2.0 under a royalty-free patent policy ([specification repository](https://github.com/CycloneDX/specification)). Compatible with commercial/ARR code if Apache notices and any `NOTICE` content are preserved. Its wider BOM ecosystem lists roughly 300 tools ([tool center](https://cyclonedx.org/tool-center/)); production use specifically of the attestations subset remains **UNVERIFIED**.

4. **in-toto Statement v1 plus DSSE for signed Ranex artifacts.** Apache-2.0 ([in-toto licence](https://github.com/in-toto/attestation/blob/main/LICENSE)); commercially compatible with notice/patent conditions and no copyleft. Production evidence includes [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations), which use signed attestations bound to artifact digests.

5. **SLSA v1.2 for the architecture compiler and generated checking code.** Production implementations include [Google Cloud Build provenance](https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance), [npm provenance](https://docs.npmjs.com/generating-provenance-statements/) and [Tekton Chains](https://tekton.dev/docs/chains/slsa-provenance/). The current specification uses the [Community Specification License 1.0](https://github.com/slsa-framework/slsa/blob/main/LICENSE), while existing code is commonly Apache-2.0. Implementing the standard is commercially compatible; retain applicable notices and obtain legal review before copying specification text wholesale.

6. **SCITT RFC 9943 plus COSE Receipts RFC 9942 for the evidence ledger.** Both became IETF Proposed Standards in June 2026. [Microsoft’s Signing Transparency Ledger](https://learn.microsoft.com/en-us/azure/confidential-ledger/about-microsoft-signing-transparency-ledger) is a named GA implementation, currently scoped to specific Microsoft services. IETF Trust terms apply to the documents; extracted code components use Revised BSD. Compatible with commercial use, with the required notices; no copyleft.

7. **Sigstore Bundle/Rekor for public attestations.** Sigstore components use Apache-2.0; commercially compatible with notices and patent terms. [npm provenance](https://docs.npmjs.com/generating-provenance-statements/) uses Sigstore’s public services, while Sigstore documents Rekor’s public operational service and auditing model ([Rekor overview](https://docs.sigstore.dev/logging/overview/)). Public logging exposes metadata, so sensitive evidence needs a private service or hash-only statement.

8. **W3C PROV-O for provenance interchange.** It is a W3C Recommendation with an implementation report covering more than 40 implementations and cross-implementation exchange ([report](https://www.w3.org/TR/prov-implementations/)). Commercial implementation is compatible under W3C document-use and patent-policy terms, but Ranex should reference the Recommendation rather than copying or modifying its normative text.

The standards and implementations above are permissive or standards-implementation licences. None is copyleft. Cloud services such as Azure Confidential Ledger are commercially priced and create operational dependency, but the underlying [CCF project](https://github.com/microsoft/CCF) is Apache-2.0.

## Genuinely novel

- **The exact `IndependenceEvaluation` check artifact is unmatched prior art.** NIST standardizes independent assessors, OSCAL identifies assessment parties, and RATS separates an attesting environment from its target. I found no ratified schema combining maker/reviewer principal and session separation, actual model/provider/transport route diversity, blind-context digest, hidden-fixture isolation, prohibited write/authority checks and per-check evidence into one deterministic eligibility artifact.

- This is **not** a claim that independent review, blind testing, segregation of duties, or attestation isolation are novel. Only the exact machine-readable composition appears unmatched.

- The five-stage immutable review family and the epistemic vocabulary are **not sufficiently novel to claim**: OSCAL already separates plans, observations, findings, risks and attestations; CycloneDX represents claims, counterclaims, evidence, conformance and confidence; PROV represents derivation and responsibility.

Here, **NOVEL means “no direct technical interchange precedent found in this sweep,” not patent novelty or legal novelty**.

## Inferences

- **Inference — hash-chain threat model:** Because verification derives its starting point and expected history solely from the current local file ([verification code](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:65)), a party able to replace or truncate the whole file can recompute a valid chain. This follows from the implementation and the transparency-log requirement that clients retain or compare independently witnessed heads ([transparency.dev explanation](https://transparency.dev/verifiable-data-structures/)).

- **Inference — OSCAL/CycloneDX boundary:** OSCAL is the stronger canonical choice for governance controls and assessment packages; CycloneDX is the stronger exchange choice for software-supply-chain claims and counterclaims. This division is based on their published model scopes, not an explicit statement by either standards body.

- **Inference — SARIF extensions:** Mapping epistemic status and Ranex workflow state into namespaced SARIF properties is preferable to redefining SARIF fields because their meanings do not match. That mapping is a compatibility judgment.

- **Inference — licence compatibility:** Compatibility assessments mean that implementing the formats does not appear to require relicensing Ranex. They are not legal advice; all attribution, notice, trademark and patent-policy conditions still apply.

- **Inference — independence novelty:** The `NOVEL` conclusion is negative search evidence and can be overturned by a later-discovered standard or proprietary implementation.

## Search coverage

Searched and externally verified:

- Findings: SARIF 2.1.0, GitHub SARIF support, OCSF Detection Finding/AWS Security Lake, SCAP 1.3, XCCDF, OVAL and ARF.
- Controls/evidence: OSCAL Catalog, Profile, SSP, Assessment Plan, Assessment Results and POA&M; FedRAMP OSCAL adoption; CycloneDX/ECMA-424 declarations and attestations.
- Provenance/attestation: W3C PROV-O, in-toto Statement/Envelope/Bundle family, DSSE, SLSA 1.2, Sigstore Bundle, Rekor, RATS/EAT, C2PA, SPDX 3.0, Grafeas, GUAC and OCI 1.1 referrers.
- Tamper evidence: RFC 9162 Certificate Transparency, Trillian, transparency.dev audit model, SCITT RFC 9943, COSE Receipts RFC 9942, Sigstore Rekor, Microsoft Signing Transparency Ledger, Azure Confidential Ledger and CCF.
- Independence/epistemics: NIST SP 800-53 CA-2/CA-7, SP 800-53A assessment procedures, RATS attester isolation, blind evaluation manifests, AI evaluation provenance, model/provider-route diversity attestations and machine-readable fact/inference vocabularies.
- Licensing: Ranex’s [source-available, all-rights-reserved licence](/home/soultransit/devtony/ranex/LICENSE-RANEX.md:1), OASIS terms/IPR mode, NIST notices, Apache-2.0 projects, W3C document rules, SLSA Community Specification License and IETF Trust/Revised BSD terms.

Could not fully verify:

- **UNVERIFIED:** named production deployments using the CycloneDX Attestations subset specifically; the broader CycloneDX BOM ecosystem is verified.
- **UNVERIFIED:** a ratified, general-purpose machine-readable epistemic-status vocabulary matching Ranex’s five values.
- The SCITT CCF receipt profile used by Microsoft remains an Internet-Draft; the generic SCITT architecture and COSE Receipts are ratified RFCs.
- ISO material behind paywalls was not relied upon for field-level recommendations.

No repository files were created, modified or deleted.
tokens used
376,654
Ranex mostly recomposes established standards. Its strongest unmatched element is the exact, machine-evaluable bundle of AI-review independence checks—not the underlying independence principle.

The JSON schemas are generated from templates ([contract rule](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:26), [generator registry](/home/soultransit/devtony/ranex/scripts/architecture/generate_contracts.py:285)). Therefore, every schema delta below means: change the corresponding authoring template and `generate_contracts.py`, then regenerate; do not hand-edit generated JSON.

## Mapping table

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
|---|---|---|---|---|
| [AI_ARTIFACT_CONTRACTS.md:39](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:39) | Canonicalizes JSON with RFC 8785, removes `digest`, then computes a SHA-256 identifier. | [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) | **ADOPT** | Already adopted correctly. Keep RFC 8785 normative and use its published test vectors; do not introduce a Ranex-specific canonicalization variant. |
| [review-observation-v1.schema.json:48](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:48), [template:15](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:15) | A finding has free-string `category` and `claim`, plus `finding_id`. It does not identify the violated rule separately. | [OASIS SARIF 2.1.0 `result`, `ruleId`, `message`, `guid`, and fingerprints](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) | **ADOPT** | Use SARIF `result.ruleId` for the violated rule and `result.message` for `claim`; transport `finding_id` as `result.guid`. Use `partialFingerprints` for stable matching across revisions. Do not overload `category` as a rule identifier. |
| [review-observation-v1.schema.json:94](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:94), [template:17](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:17) | `severity` is an unconstrained string. | [SARIF `result.level`](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html); security-specific competitor: [OCSF Detection Finding severity](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **ADOPT** | Replace the interchange value with SARIF `none`, `note`, `warning`, or `error`. If Ranex needs risk magnitude beyond diagnostic level, carry it separately rather than extending `result.level`. Map imported security findings from OCSF’s wider severity vocabulary at the adapter boundary. |
| [review-observation-v1.schema.json:54](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:54), [template:18](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:18) | `confidence` is a required but unconstrained string. | [CycloneDX 1.7 Attestation confidence: score and rationale](https://cyclonedx.org/docs/1.7/proto/); [OCSF confidence ID and score](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **ADAPT** | Represent interchange confidence as CycloneDX’s bounded `0..1` score plus rationale. Preserve a Ranex-derived band only as a projection. For security telemetry, define a lossless adapter to OCSF confidence rather than accepting arbitrary text. |
| [review-observation-v1.schema.json:57](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:57), [AI_ARTIFACT_CONTRACTS.md:424](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:424) | Distinguishes `FACT`, `INFERENCE`, `OWNER_REQUIREMENT`, `PROPOSAL`, and `REPORTED_ADVISORY_RESULT`; facts require evidence. | [CycloneDX Attestations claims, counterclaims, evidence, conformance and confidence](https://cyclonedx.org/use-cases/attestations/); [W3C PROV-O attribution and derivation](https://www.w3.org/TR/prov-o/) | **ADAPT** | Keep epistemic classification as a Ranex namespaced extension, but model the underlying assertion as a CycloneDX claim/counterclaim and its origin/derivation with PROV. Do not map this field to SARIF “precision”: SARIF precision measures rule quality, not the epistemic status of one claim. |
| [review-observation-v1.schema.json:66](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:66), [evidence-ref.schema.json:6](/home/soultransit/devtony/ranex/schemas/common/evidence-ref.schema.json:6) | Finding `evidence_refs.items` is unconstrained and does not reference the existing `{evidence_ref,evidence_digest}` type. | [CycloneDX declarations/evidence](https://cyclonedx.org/docs/1.7/proto/); [OSCAL observation `relevant-evidence` and hashed back-matter resources](https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/json-definitions/) | **ADOPT** | Replace opaque array items with standard evidence references: CycloneDX `bom-ref` links for claim evidence or OSCAL `relevant-evidence.href` links backed by hashed resources. Remove the parallel untyped representation. |
| [review-observation-v1.schema.json:76](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:76), [template:20](/home/soultransit/devtony/ranex/docs/architecture/templates/REVIEW_OBSERVATION.yaml:20) | `location` is one free string; `required_action` is prose. | [SARIF `locations`, `physicalLocation`, `logicalLocations`, `region`, `relatedLocations`, `attachments`, and `fixes`](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) | **ADOPT** | Use SARIF location objects with artifact URI plus region/logical location. Express machine-applicable corrections as SARIF `fixes`; keep prose only as rule help or message text. Use `relatedLocations`/`attachments` for supporting locations and excerpts. |
| [AI_ARTIFACT_CONTRACTS.md:427](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:427), [review-verdict-v1.schema.json:31](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:31) | Maintains a service-controlled lifecycle including dispute, specialist review, verification, and human risk acceptance; verdicts list open and resolved findings. | [SARIF `baselineState`, fingerprints and suppressions](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html); [OCSF finding status](https://schema.ocsf.io/1.3.0/classes/detection_finding) | **DIVERGE** | Keep Ranex’s authoritative workflow because SARIF and OCSF carry snapshots, not this segregation-of-duties state machine. Export `VERIFIED` changes using SARIF fingerprints/baseline state and risk acceptance using SARIF suppression status plus justification; do not treat the SARIF file as workflow authority. |
| [review-request-v1.schema.json:13](/home/soultransit/devtony/ranex/schemas/review/review-request-v1.schema.json:13), [AI_ARTIFACT_CONTRACTS.md:388](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:388) | Binds the assessment subject, packet, maker, reviewer requirements, prohibited capabilities, blind-context digest, route diversity and qualification policy. | [NIST OSCAL Assessment Plan](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/); [NIST SP 800-53 CA-2 independent assessors](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) | **ADAPT** | Make the request an OSCAL Assessment Plan/profile: express scope through reviewed controls and subjects, procedures through assessment activities, and assessors through responsible roles/parties. Retain blind-context, prohibited-capability and route-diversity requirements as namespaced OSCAL properties. |
| [AI_ARTIFACT_CONTRACTS.md:376](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:376), [review-verdict-v1.schema.json:27](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:27) | Separates request, attempts, observations, independence evaluation, verdict and evidence snapshot into immutable records. | [OSCAL Assessment Results](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/); [CycloneDX Attestations](https://cyclonedx.org/use-cases/attestations/) | **ADAPT** | Use an OSCAL Assessment Results document for results, reviewed controls, observations, findings, risks, attestations and assessment log. Use CycloneDX declarations when exchanging software-supply-chain claims/counterclaims. Preserve Ranex record separation as event provenance, not as a competing compliance interchange family. |
| [review-verdict-v1.schema.json:75](/home/soultransit/devtony/ranex/schemas/review/review-verdict-v1.schema.json:75), [AI_ARTIFACT_CONTRACTS.md:404](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:404) | Uses Ranex dispositions `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, and `INELIGIBLE`; explicitly not a gate outcome. | [OSCAL findings, risks and attestations](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/); [CycloneDX affirmation/signatories](https://cyclonedx.org/use-cases/attestations/) | **ADAPT** | Publish observations and findings in OSCAL and the signed conformance assertion in CycloneDX. Keep the four Ranex dispositions as a named profile vocabulary because neither standard defines this exact eligibility-versus-acceptability distinction. |
| [CAPABILITY_ASSESSMENT.yaml:154](/home/soultransit/devtony/ranex/docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:154), [CAPABILITY_ASSESSMENT.yaml:235](/home/soultransit/devtony/ranex/docs/architecture/templates/CAPABILITY_ASSESSMENT.yaml:235) | Combines control scope, evidence, ordinal capability, effectiveness, population coverage, gaps, confidence tests, findings and improvement actions. | [OSCAL Catalog/Profile/Assessment Results/POA&M models](https://pages.nist.gov/OSCAL-Reference/models/); competitor [CycloneDX requirements-to-claims/evidence attestations](https://cyclonedx.org/use-cases/machine-readable-standards/) | **ADAPT** | Represent obligations in OSCAL Catalog/Profile, assessment execution/results in Assessment Results, and gaps/remediation in POA&M. Carry Ranex ordinal capability and deterministic aggregation constraints as namespaced properties. Use CycloneDX only for exchanging software-supply-chain conformance claims, not as the control catalog. |
| [evidence-snapshot-v1.schema.json:31](/home/soultransit/devtony/ranex/schemas/assurance/evidence-snapshot-v1.schema.json:31) | Freezes eligible and ineligible evidence, required/missing claims, conflicts, coverage and policy activation against an exact subject. | [OSCAL observations, relevant evidence, findings and back matter](https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/assessment-results/json-definitions/) | **ADAPT** | Express eligible evidence as OSCAL observations and hashed back-matter resources; express missing/conflicting evidence as findings or risks. Retain policy-activation digest and Ranex eligibility decision as namespaced properties because OSCAL does not determine evidence eligibility policy. |
| [analysis-attempt-v1.schema.json:37](/home/soultransit/devtony/ranex/schemas/review/analysis-attempt-v1.schema.json:37), [analysis-attempt-v1.schema.json:87](/home/soultransit/devtony/ranex/schemas/review/analysis-attempt-v1.schema.json:87) | Records inputs, output, reviewer, provider/model, transport, executable, parser, isolation, timing, capabilities and write attempts. | [W3C PROV-O](https://www.w3.org/TR/prov-o/) and its [implementation report](https://www.w3.org/TR/prov-implementations/) | **ADAPT** | Expose each attempt as `prov:Activity`; inputs/outputs as `prov:Entity`; reviewer, model wrapper and service as `prov:Agent`/`prov:SoftwareAgent`; use `prov:used`, `wasGeneratedBy`, `wasAssociatedWith`, `hadRole`, and `wasInformedBy`. Keep exact route digests as domain attributes. |
| [review-record-projection-v1.schema.json:30](/home/soultransit/devtony/ranex/schemas/review/review-record-projection-v1.schema.json:30), [AI_ARTIFACT_CONTRACTS.md:360](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:360) | Joins source-record IDs/digests into a non-authoritative navigation projection. | [W3C PROV `Bundle` and `Collection`](https://www.w3.org/TR/prov-o/) | **ADAPT** | Publish a PROV Bundle/Collection containing the source entities and their relationships. Keep the existing projection only as a UI/read-model cache; it must not be the provenance interchange or evidence authority. |
| [AI_ARTIFACT_CONTRACTS.md:47](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:47), [evidence-ref.schema.json:6](/home/soultransit/devtony/ranex/schemas/common/evidence-ref.schema.json:6) | Content-addresses artifacts and evidence but provides no standard subject/predicate envelope or issuer signature. | [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md) and [DSSE envelope](https://github.com/in-toto/attestation/blob/main/spec/v1/envelope.md) | **ADOPT** | Make each sealed Ranex artifact the predicate of an in-toto Statement. Put the artifact being claimed about in `subject[]` with an algorithm-keyed digest map, assign a stable `predicateType`, and sign the Statement using DSSE. The current internal `digest` may remain an object identifier but is not an attestation. |
| [generate_contracts.py:285](/home/soultransit/devtony/ranex/scripts/architecture/generate_contracts.py:285), [AI_ARTIFACT_CONTRACTS.md:26](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:26) | Generates executable schemas from templates but does not emit standardized build provenance. | [SLSA v1.2 Build Provenance](https://slsa.dev/spec/v1.2/build-provenance) | **ADOPT** | Emit SLSA provenance for every generated schema/checker set: generated files in `subject`; templates, generator and registries in `resolvedDependencies`; generator invocation in `buildDefinition`; qualified runner in `builder`; times and by-products in `runDetails`. Do not use SLSA for semantic review verdicts. |
| [independence-evaluation-v1.schema.json:17](/home/soultransit/devtony/ranex/schemas/review/independence-evaluation-v1.schema.json:17), [AI_ARTIFACT_CONTRACTS.md:398](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:398) | Deterministically evaluates identity/session separation, no-write authority, blind context, route/provider/transport diversity, qualification, hidden-fixture isolation and exact candidate identity, each with evidence. | Principles exist in [NIST SP 800-53 CA-2(1)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf) and isolation of attester from target in [IETF RATS Architecture, RFC 9334](https://www.rfc-editor.org/rfc/rfc9334.html), but no matching interchange artifact was found. | **NOVEL** | Keep this as a Ranex extension, but identify its assessors and evidence through OSCAL and attest the result through in-toto/DSSE. Search for an equivalent covered assessor-independence schemas, blind evaluation manifests, model/provider-route diversity attestations, RATS evidence and AI evaluation provenance; none exposed this combined check set. |
| [hash_chain_ledger.py:20](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:20), [hash_chain_ledger.py:65](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:65) | Stores a local JSONL sequence whose entry hash covers sequence, previous digest and record digest; verification replays the local file. | [SCITT Architecture, RFC 9943](https://www.rfc-editor.org/info/rfc9943/) and [COSE Receipts, RFC 9942](https://www.rfc-editor.org/info/rfc9942/) | **ADOPT** | Replace the private hash-chain proof format with SCITT Signed/Transparent Statements and RFC 9942 receipts. A stored record must carry an issuer signature, registration-policy identity, signed inclusion receipt and verifiable-data-structure profile—not merely `previous_digest`. |
| [hash_chain_ledger.py:144](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:144), [hash_chain_ledger.py:206](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:206) | File permissions, locking and `fsync` improve local durability, but there are no signed checkpoints, inclusion/consistency proofs, witnesses or independently held receipts. | Public option: [Sigstore Bundle](https://docs.sigstore.dev/about/bundle/) and [Rekor](https://docs.sigstore.dev/logging/overview/). General Merkle design: [RFC 9162 Certificate Transparency](https://www.rfc-editor.org/rfc/rfc9162.html). Confidential option: [Azure Confidential Ledger/CCF receipts](https://learn.microsoft.com/en-us/azure/confidential-ledger/write-transaction-receipts). [Trillian is now in maintenance mode](https://github.com/google/trillian). | **ADAPT** | Use Sigstore/Rekor for publishable attestations and an RFC 9942/CCF-compatible private transparency service for confidential evidence. Persist the returned bundle/receipt with the evidence. Do not start a new deployment on Trillian; its maintainers recommend newer log implementations. |
| [review-observation-v1.schema.json:48](/home/soultransit/devtony/ranex/schemas/review/review-observation-v1.schema.json:48) | Ranex is a general review format, including non-security architecture findings. | [OCSF Detection Finding](https://schema.ocsf.io/1.3.0/classes/detection_finding), deployed by [AWS Security Lake](https://docs.aws.amazon.com/security-lake/latest/userguide/open-cybersecurity-schema-framework.html); [SCAP/ARF](https://csrc.nist.gov/Projects/security-content-automation-protocol/SCAP-Releases/scap-1-3) | **DIVERGE** | Do not make OCSF or SCAP the canonical Ranex format: both are narrower security/technical-control ecosystems. Provide import/export adapters for OCSF security findings and SCAP ARF/XCCDF/OVAL results, then normalize them into SARIF/OSCAL. |

## Adopt shortlist

Ranked by immediate value to Ranex:

1. **SARIF 2.1.0 for review-finding interchange.** It is an OASIS Standard and is consumed in production by [GitHub code scanning](https://docs.github.com/en/enterprise-cloud@latest/code-security/reference/code-scanning/sarif-files/sarif-support). OASIS permits implementation and redistribution of specification material under its notices; the work uses an RF-on-RAND IPR mode. Compatible with Ranex’s all-rights-reserved model, provided required notices are retained. No copyleft.

2. **OSCAL for controls, assessments and evidence packages.** NIST lists all seven models as released and publishes XML, JSON and YAML tooling ([models](https://pages.nist.gov/OSCAL-Reference/models/), [tools](https://pages.nist.gov/OSCAL/resources/tools/)). NIST material/software is generally usable and distributable with its notice and attribution conditions ([NIST notice](https://pages.nist.gov/oscal-tools/about/)). Compatible; no copyleft. Maturity caveat: FedRAMP reported more than 100 Rev. 5 authorizations but no OSCAL submissions during its earlier pilot, so production exchange adoption lags model maturity ([FedRAMP RFC-0024](https://www.fedramp.gov/rfcs/0024/)).

3. **CycloneDX Attestations for software-supply-chain claims, counterclaims, evidence and confidence.** CycloneDX 1.7 is ECMA-424 and its schemas are Apache-2.0 under a royalty-free patent policy ([specification repository](https://github.com/CycloneDX/specification)). Compatible with commercial/ARR code if Apache notices and any `NOTICE` content are preserved. Its wider BOM ecosystem lists roughly 300 tools ([tool center](https://cyclonedx.org/tool-center/)); production use specifically of the attestations subset remains **UNVERIFIED**.

4. **in-toto Statement v1 plus DSSE for signed Ranex artifacts.** Apache-2.0 ([in-toto licence](https://github.com/in-toto/attestation/blob/main/LICENSE)); commercially compatible with notice/patent conditions and no copyleft. Production evidence includes [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations), which use signed attestations bound to artifact digests.

5. **SLSA v1.2 for the architecture compiler and generated checking code.** Production implementations include [Google Cloud Build provenance](https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance), [npm provenance](https://docs.npmjs.com/generating-provenance-statements/) and [Tekton Chains](https://tekton.dev/docs/chains/slsa-provenance/). The current specification uses the [Community Specification License 1.0](https://github.com/slsa-framework/slsa/blob/main/LICENSE), while existing code is commonly Apache-2.0. Implementing the standard is commercially compatible; retain applicable notices and obtain legal review before copying specification text wholesale.

6. **SCITT RFC 9943 plus COSE Receipts RFC 9942 for the evidence ledger.** Both became IETF Proposed Standards in June 2026. [Microsoft’s Signing Transparency Ledger](https://learn.microsoft.com/en-us/azure/confidential-ledger/about-microsoft-signing-transparency-ledger) is a named GA implementation, currently scoped to specific Microsoft services. IETF Trust terms apply to the documents; extracted code components use Revised BSD. Compatible with commercial use, with the required notices; no copyleft.

7. **Sigstore Bundle/Rekor for public attestations.** Sigstore components use Apache-2.0; commercially compatible with notices and patent terms. [npm provenance](https://docs.npmjs.com/generating-provenance-statements/) uses Sigstore’s public services, while Sigstore documents Rekor’s public operational service and auditing model ([Rekor overview](https://docs.sigstore.dev/logging/overview/)). Public logging exposes metadata, so sensitive evidence needs a private service or hash-only statement.

8. **W3C PROV-O for provenance interchange.** It is a W3C Recommendation with an implementation report covering more than 40 implementations and cross-implementation exchange ([report](https://www.w3.org/TR/prov-implementations/)). Commercial implementation is compatible under W3C document-use and patent-policy terms, but Ranex should reference the Recommendation rather than copying or modifying its normative text.

The standards and implementations above are permissive or standards-implementation licences. None is copyleft. Cloud services such as Azure Confidential Ledger are commercially priced and create operational dependency, but the underlying [CCF project](https://github.com/microsoft/CCF) is Apache-2.0.

## Genuinely novel

- **The exact `IndependenceEvaluation` check artifact is unmatched prior art.** NIST standardizes independent assessors, OSCAL identifies assessment parties, and RATS separates an attesting environment from its target. I found no ratified schema combining maker/reviewer principal and session separation, actual model/provider/transport route diversity, blind-context digest, hidden-fixture isolation, prohibited write/authority checks and per-check evidence into one deterministic eligibility artifact.

- This is **not** a claim that independent review, blind testing, segregation of duties, or attestation isolation are novel. Only the exact machine-readable composition appears unmatched.

- The five-stage immutable review family and the epistemic vocabulary are **not sufficiently novel to claim**: OSCAL already separates plans, observations, findings, risks and attestations; CycloneDX represents claims, counterclaims, evidence, conformance and confidence; PROV represents derivation and responsibility.

Here, **NOVEL means “no direct technical interchange precedent found in this sweep,” not patent novelty or legal novelty**.

## Inferences

- **Inference — hash-chain threat model:** Because verification derives its starting point and expected history solely from the current local file ([verification code](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:65)), a party able to replace or truncate the whole file can recompute a valid chain. This follows from the implementation and the transparency-log requirement that clients retain or compare independently witnessed heads ([transparency.dev explanation](https://transparency.dev/verifiable-data-structures/)).

- **Inference — OSCAL/CycloneDX boundary:** OSCAL is the stronger canonical choice for governance controls and assessment packages; CycloneDX is the stronger exchange choice for software-supply-chain claims and counterclaims. This division is based on their published model scopes, not an explicit statement by either standards body.

- **Inference — SARIF extensions:** Mapping epistemic status and Ranex workflow state into namespaced SARIF properties is preferable to redefining SARIF fields because their meanings do not match. That mapping is a compatibility judgment.

- **Inference — licence compatibility:** Compatibility assessments mean that implementing the formats does not appear to require relicensing Ranex. They are not legal advice; all attribution, notice, trademark and patent-policy conditions still apply.

- **Inference — independence novelty:** The `NOVEL` conclusion is negative search evidence and can be overturned by a later-discovered standard or proprietary implementation.

## Search coverage

Searched and externally verified:

- Findings: SARIF 2.1.0, GitHub SARIF support, OCSF Detection Finding/AWS Security Lake, SCAP 1.3, XCCDF, OVAL and ARF.
- Controls/evidence: OSCAL Catalog, Profile, SSP, Assessment Plan, Assessment Results and POA&M; FedRAMP OSCAL adoption; CycloneDX/ECMA-424 declarations and attestations.
- Provenance/attestation: W3C PROV-O, in-toto Statement/Envelope/Bundle family, DSSE, SLSA 1.2, Sigstore Bundle, Rekor, RATS/EAT, C2PA, SPDX 3.0, Grafeas, GUAC and OCI 1.1 referrers.
- Tamper evidence: RFC 9162 Certificate Transparency, Trillian, transparency.dev audit model, SCITT RFC 9943, COSE Receipts RFC 9942, Sigstore Rekor, Microsoft Signing Transparency Ledger, Azure Confidential Ledger and CCF.
- Independence/epistemics: NIST SP 800-53 CA-2/CA-7, SP 800-53A assessment procedures, RATS attester isolation, blind evaluation manifests, AI evaluation provenance, model/provider-route diversity attestations and machine-readable fact/inference vocabularies.
- Licensing: Ranex’s [source-available, all-rights-reserved licence](/home/soultransit/devtony/ranex/LICENSE-RANEX.md:1), OASIS terms/IPR mode, NIST notices, Apache-2.0 projects, W3C document rules, SLSA Community Specification License and IETF Trust/Revised BSD terms.

Could not fully verify:

- **UNVERIFIED:** named production deployments using the CycloneDX Attestations subset specifically; the broader CycloneDX BOM ecosystem is verified.
- **UNVERIFIED:** a ratified, general-purpose machine-readable epistemic-status vocabulary matching Ranex’s five values.
- The SCITT CCF receipt profile used by Microsoft remains an Internet-Draft; the generic SCITT architecture and COSE Receipts are ratified RFCs.
- ISO material behind paywalls was not relied upon for field-level recommendations.

No repository files were created, modified or deleted.
