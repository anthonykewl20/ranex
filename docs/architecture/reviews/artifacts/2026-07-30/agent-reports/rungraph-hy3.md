[0m
> build · tencent/hy3
[0m
[0m$ [0mls docs/architecture/decisions/ docs/architecture/ 2>&1 | head -60
docs/architecture/:
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

docs/architecture/decisions/:
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
[0m
[0m$ [0mpwd && ls && git status --short | head -50 && git log --oneline -5
/home/soultransit/devtony/ranex
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
 M architecture/contracts/accepted-adrs.json
 M architecture/contracts/architecture-element-assessments.json
 M architecture/contracts/architecture-elements.json
 M architecture/contracts/registry-manifest.json
 M architecture/contracts/schema-registry.json
 M docs/README.md
 M docs/architecture/README.md
 M docs/architecture/SOURCE_OF_TRUTH.md
 M docs/architecture/assessments/COMPLETENESS_REPORT.md
 M docs/architecture/assessments/completeness-report.json
 M docs/architecture/assessments/validation-report.json
 M docs/architecture/reviews/README.md
 M docs/architecture/rfcs/README.md
 M docs/research/README.md
 M docs/research/ranex-architecture-practice-application-profile.json
 M schemas/review/review-observation-v1.schema.json
 M scripts/architecture/generate_contracts.py
 M scripts/architecture/validate_contracts.py
?? docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
?? docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md
?? docs/architecture/reviews/artifacts/2026-07-30/
?? docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md
?? docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md
?? docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
a573502a8 fix: remove unsupported qualifier from HERMES-PROMOTION-059, ADR-0013 v1.4.0
c15678dc2 docs: ADR-0013 v1.3.0, reviewer probe research, and session handoff
780299025 docs: add root README, documentation indexes, and upstream licence
a66267776 fix: fail closed on nonterminal lifecycle axes
b14e0af29 chore: reconcile ADR-0012 readiness axis with transition conventions
[0m
I'll start by reading the subject document and surveying the governing corpus.
[0m→ [0mRead docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
[0m
[0m$ [0mwc -l docs/architecture/decisions/*.md docs/architecture/*.md architecture/contracts/* schemas/**/*.json 2>/dev/null | tail -60; echo ---; ls -R architecture schemas | head -80
125 schemas/execution/agent-handoff-v1.schema.json
     150 schemas/execution/landing-record-v1.schema.json
     105 schemas/execution/post-landing-verification-v1.schema.json
     641 schemas/execution/run-result-v1.schema.json
     481 schemas/fleet/assignment-v1.schema.json
     148 schemas/fleet/dispatch-offer-v1.schema.json
     209 schemas/fleet/fleet-experiment-v1.schema.json
     157 schemas/fleet/lease-v1.schema.json
     141 schemas/fleet/mailbox-envelope-v1.schema.json
     694 schemas/fleet/worker-attempt-v1.schema.json
     129 schemas/lifecycle/operation-evidence-v1.schema.json
     122 schemas/lifecycle/outcome-review-v1.schema.json
     142 schemas/lifecycle/release-evidence-v1.schema.json
     204 schemas/planning/acceptance-authority-registry-v1.schema.json
     121 schemas/planning/acceptance-basis-authority-row-v1.schema.json
     105 schemas/planning/accountable-delivery-owner-assignment-v1.schema.json
     188 schemas/planning/accountable-owner-authority-registry-v1.schema.json
     206 schemas/planning/capacity-authority-registry-v1.schema.json
     123 schemas/planning/capacity-snapshot-authority-row-v1.schema.json
     446 schemas/planning/commitment-decision-authority-registry-v1.schema.json
      87 schemas/planning/core-sdlc-trace-authority-binding-v1.schema.json
     374 schemas/planning/core-sdlc-trace-authority-registry-v1.schema.json
      80 schemas/planning/decision-artifact-registry-row-v1.schema.json
     103 schemas/planning/decision-authentication-binding-v1.schema.json
     205 schemas/planning/delivery-commitment-subject-v1.schema.json
     215 schemas/planning/dependency-authority-registry-v1.schema.json
     132 schemas/planning/dependency-snapshot-authority-row-v1.schema.json
     761 schemas/planning/estimate-authority-registry-v2.schema.json
    3491 schemas/planning/estimate-commitment-source-envelope-v2.schema.json
      96 schemas/planning/estimate-evidence-authority-row-v1.schema.json
      85 schemas/planning/estimate-id-reservation-history-generation-v1.schema.json
     198 schemas/planning/estimate-id-reservation-history-v1.schema.json
      76 schemas/planning/estimate-id-reservation-v1.schema.json
      89 schemas/planning/estimate-method-authority-row-v1.schema.json
     213 schemas/planning/estimate-observation-v1.schema.json
      83 schemas/planning/estimate-preparer-provenance-v1.schema.json
     185 schemas/planning/estimate-source-replay-authority-registry-v1.schema.json
      99 schemas/planning/estimate-source-replay-reservation-v1.schema.json
     257 schemas/planning/integrated-plan-authority-registry-v1.schema.json
     174 schemas/planning/integrated-plan-authority-row-v1.schema.json
     198 schemas/planning/risk-authority-registry-v1.schema.json
     115 schemas/planning/risk-snapshot-authority-row-v1.schema.json
     249 schemas/planning/scope-authority-registry-v1.schema.json
     166 schemas/planning/scope-authority-row-v1.schema.json
     177 schemas/planning/trusted-time-authority-registry-v1.schema.json
      94 schemas/planning/trusted-time-observation-v1.schema.json
    1334 schemas/process/capability-assessment-v1.schema.json
     418 schemas/process/capability-domain-projection-v1.schema.json
     249 schemas/research/research-packet-v1.schema.json
     239 schemas/resources/resource-reservation-v1.schema.json
     212 schemas/review/analysis-attempt-v1.schema.json
     247 schemas/review/independence-evaluation-v1.schema.json
     191 schemas/review/review-observation-v1.schema.json
     111 schemas/review/review-record-projection-v1.schema.json
     135 schemas/review/review-request-v1.schema.json
     109 schemas/review/review-verdict-v1.schema.json
     897 schemas/work/task-packet-v1.schema.json
     695 schemas/work/transition-event-v1.schema.json
     192 schemas/work/work-intake-v1.schema.json
  255727 total
---
architecture:
contracts
records

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

architecture/records/legacy-test-layout:
direct-source-classifications
README.md

architecture/records/legacy-test-layout/direct-source-classifications:
README.md

architecture/records/test-governance:
behavior-authorities
README.md

architecture/records/test-governance/behavior-authorities:
README.md

architecture/records/test-health:
README.md

schemas:
architecture
artifacts
assurance
authority
common
[0m
[0m$ [0mcat LICENSE-RANEX.md
# Ranex Personal-Use Source License 1.0

Copyright (c) 2026 Anthony Garces. All rights reserved.

This is a source-available license. It is not an open-source license.

## 1. Scope

This license applies only to original Ranex code, documentation, configuration,
artwork, and modifications owned by Anthony Garces (the "Ranex Material").

It does not apply to Hermes Agent material or any other third-party material.
Those portions remain governed by their own licenses. When Hermes Agent
material is adopted in Phase 1, its MIT License is retained in `LICENSE`.

## 2. Personal-use permission

Subject to every condition below, an individual may view, copy, run, study, and
privately modify the Ranex Material solely for personal learning,
experimentation, or evaluation.

This permission is personal, limited, non-exclusive, and non-transferable. All
copyright, license, attribution, and source notices must remain intact.

## 3. Restrictions

Except for the limited GitHub-platform rights in section 4, and unless Anthony
Garces gives prior written permission, you may not:

1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
   or otherwise provide the Ranex Material or a modified version to anyone;
2. make the Ranex Material available through a public or shared repository,
   download, package, service, hosted application, network endpoint, or device;
3. use the Ranex Material for any commercial, business, employment,
   professional, institutional, revenue-generating, or client purpose;
4. use the Ranex Material to operate, support, develop, or improve a product,
   service, organization, or business process;
5. remove, hide, or alter a copyright, license, provenance, or attribution
   notice;
6. claim authorship or ownership of Ranex Material created by Anthony Garces,
   or present that material as your own work;
7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
   ownership; or
8. grant another person rights that this license does not grant to you.

You may identify original changes that you created privately, but that does not
give you ownership of the underlying Ranex Material or permission to
redistribute the combined work.

## 4. Public GitHub repository

While the repository is public, GitHub's Terms of Service grant GitHub users
limited permission to use, display, perform, and reproduce repository content
through GitHub's service as its features allow, including by forking it. This
license does not restrict those platform rights.

Those platform permissions do not grant permission to redistribute the Ranex
Material outside GitHub's service, use it for business, remove its notices, or
claim it as your own.

## 5. Ownership and third-party rights

The Ranex Material is licensed, not sold. Anthony Garces retains all rights
not expressly granted here.

No term in this license reduces a right granted directly by the MIT License or
another applicable third-party license. When a file contains both upstream
material and original Ranex modifications, each portion remains governed by
its applicable license.

## 6. Termination

Your permission under this license ends automatically when you violate it.
After termination, you must stop using the Ranex Material and delete copies in
your possession or control, except copies GitHub retains under its Terms of
Service or copies the law requires you to preserve.

## 7. No warranty

THE RANEX MATERIAL IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE, TITLE, AND NON-INFRINGEMENT.

TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE RANEX MATERIAL OR
ITS USE.

## 8. Other rights

This license does not limit fair use, fair dealing, or another right that
applicable law does not allow a license to restrict.

For redistribution, business use, sublicensing, or another exception, obtain
prior written permission from Anthony Garces through the `anthonykewl20`
GitHub account.
[0m
[0m$ [0mwc -l docs/architecture/decisions/*.md docs/architecture/*.md
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
[0m
[0m$ [0mls .claude/worktrees/ 2>&1; ls .claude/worktrees/kernel-tracer 2>&1 | head
architecture-validated-baseline
docs
gate-controller-mvp
kernel-tracer
phase-0-preflight
phase-1-adopt-upstream
phase-2-runtime-bootstrap
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
[0m
[0m$ [0mls -la .claude/worktrees/kernel-tracer; echo ---; cd .claude/worktrees/kernel-tracer && git status --short | head -40 && git log --oneline -5 && git branch --show-current
total 120
drwxrwxr-x 13 soultransit soultransit  4096 Jul 30 00:04 .
drwxrwxr-x  9 soultransit soultransit  4096 Jul 29 23:56 ..
drwxrwxr-x  4 soultransit soultransit  4096 Jul 29 23:56 architecture
drwxrwxr-x  2 soultransit soultransit  4096 Jul 29 23:56 decisions
drwxrwxr-x  4 soultransit soultransit  4096 Jul 29 23:56 docs
-rw-rw-r--  1 soultransit soultransit    69 Jul 29 23:56 .git
-rw-rw-r--  1 soultransit soultransit   940 Jul 30 00:35 .gitignore
drwxrwxr-x  2 soultransit soultransit  4096 Jul 29 23:56 legal
-rw-rw-r--  1 soultransit soultransit  1070 Jul 29 23:56 LICENSE
-rw-rw-r--  1 soultransit soultransit  4105 Jul 29 23:56 LICENSE-RANEX.md
-rw-rw-r--  1 soultransit soultransit  2280 Jul 29 23:56 NOTICE.md
-rw-rw-r--  1 soultransit soultransit   572 Jul 30 00:01 pyproject.toml
drwxrwxr-x  3 soultransit soultransit  4096 Jul 30 00:01 .pytest_cache
-rw-rw-r--  1 soultransit soultransit 11931 Jul 29 23:56 README.md
drwxrwxr-x  3 soultransit soultransit  4096 Jul 30 00:04 .ruff_cache
drwxrwxr-x 18 soultransit soultransit  4096 Jul 29 23:56 schemas
drwxrwxr-x  3 soultransit soultransit  4096 Jul 29 23:56 scripts
drwxrwxr-x  3 soultransit soultransit  4096 Jul 30 00:01 src
drwxrwxr-x 10 soultransit soultransit  4096 Jul 30 00:19 tests
-rw-rw-r--  1 soultransit soultransit 26249 Jul 30 00:01 uv.lock
drwxrwxr-x  4 soultransit soultransit  4096 Jul 30 00:01 .venv
---
 M .gitignore
?? pyproject.toml
?? src/
?? tests/
?? uv.lock
780299025 docs: add root README, documentation indexes, and upstream licence
a66267776 fix: fail closed on nonterminal lifecycle axes
b14e0af29 chore: reconcile ADR-0012 readiness axis with transition conventions
099ac438d chore: capture passing architecture contract validation
032adf368 chore: snapshot architecture contracts, schemas, and tooling
feature/kernel-tracer
[0m
[0m$ [0mgrep -n "governed_execution" -r docs/architecture/ architecture/ schemas/ --include=* -l | head -30
docs/architecture/CORE_SDLC_OPERATING_MODEL.md
docs/architecture/README.md
docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md
docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md
docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md
docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md
docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md
docs/architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md
docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md
docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md
docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md
docs/architecture/templates/AUTHORITY_GRANT.yaml
docs/architecture/reviews/2026-07-28-gate-controller-mvp-user-level-audit.md
docs/architecture/reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md
docs/architecture/reviews/2026-07-28-modular-ddd-tdd-adversarial-review.md
docs/architecture/reviews/2026-07-28-hermes-initial-runtime-acceptance.md
docs/architecture/reviews/2026-07-27-kimi-agent-fleet-research-reconciliation.md
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/deepseek-v4-pro-review.md
docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-1.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-post-reconciliation-review.md
docs/architecture/reviews/artifacts/2026-07-27/hy3-final-review.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-review-part-2.md
docs/architecture/reviews/artifacts/2026-07-27/deepseek-v4-pro-final-exact-subject-review.md
docs/architecture/SOURCE_OF_TRUTH.md
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
[0m
[0m$ [0mfind src tests -type f | sort; echo ---; wc -l $(find src tests -name '*.py') | tail -5
src/ranex/assurance/adapters/filesystem/artifact_verifier.py
src/ranex/assurance/adapters/filesystem/__init__.py
src/ranex/assurance/adapters/filesystem/__pycache__/artifact_verifier.cpython-314.pyc
src/ranex/assurance/adapters/filesystem/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/adapters/__init__.py
src/ranex/assurance/adapters/persistence/__init__.py
src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py
src/ranex/assurance/adapters/persistence/jsonl/__init__.py
src/ranex/assurance/adapters/persistence/jsonl/__pycache__/hash_chain_ledger.cpython-314.pyc
src/ranex/assurance/adapters/persistence/jsonl/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/adapters/persistence/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/adapters/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/api/contracts.py
src/ranex/assurance/api/__init__.py
src/ranex/assurance/api/__pycache__/contracts.cpython-314.pyc
src/ranex/assurance/api/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/domain/gates.py
src/ranex/assurance/domain/__init__.py
src/ranex/assurance/domain/__pycache__/gates.cpython-314.pyc
src/ranex/assurance/domain/__pycache__/__init__.cpython-314.pyc
src/ranex/assurance/__init__.py
src/ranex/assurance/__pycache__/__init__.cpython-314.pyc
src/ranex/foundation/canonical.py
src/ranex/foundation/identity.py
src/ranex/foundation/__init__.py
src/ranex/foundation/__pycache__/canonical.cpython-314.pyc
src/ranex/foundation/__pycache__/identity.cpython-314.pyc
src/ranex/foundation/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/adapters/__init__.py
src/ranex/governed_execution/adapters/persistence/__init__.py
src/ranex/governed_execution/adapters/persistence/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
src/ranex/governed_execution/adapters/persistence/sqlite/__pycache__/execution_store.cpython-314.pyc
src/ranex/governed_execution/adapters/persistence/sqlite/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/adapters/policy/deterministic.py
src/ranex/governed_execution/adapters/policy/__init__.py
src/ranex/governed_execution/adapters/policy/__pycache__/deterministic.cpython-314.pyc
src/ranex/governed_execution/adapters/policy/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/adapters/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/application/application_control_pep.py
src/ranex/governed_execution/application/gate_controller.py
src/ranex/governed_execution/application/__init__.py
src/ranex/governed_execution/application/ports/application_control_policy.py
src/ranex/governed_execution/application/ports/execution_repository.py
src/ranex/governed_execution/application/ports/__init__.py
src/ranex/governed_execution/application/ports/__pycache__/application_control_policy.cpython-314.pyc
src/ranex/governed_execution/application/ports/__pycache__/execution_repository.cpython-314.pyc
src/ranex/governed_execution/application/ports/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/application/__pycache__/application_control_pep.cpython-314.pyc
src/ranex/governed_execution/application/__pycache__/gate_controller.cpython-314.pyc
src/ranex/governed_execution/application/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/domain/application_control.py
src/ranex/governed_execution/domain/events.py
src/ranex/governed_execution/domain/execution.py
src/ranex/governed_execution/domain/__init__.py
src/ranex/governed_execution/domain/__pycache__/application_control.cpython-314.pyc
src/ranex/governed_execution/domain/__pycache__/events.cpython-314.pyc
src/ranex/governed_execution/domain/__pycache__/execution.cpython-314.pyc
src/ranex/governed_execution/domain/__pycache__/__init__.cpython-314.pyc
src/ranex/governed_execution/domain/__pycache__/status.cpython-314.pyc
src/ranex/governed_execution/domain/status.py
src/ranex/governed_execution/__init__.py
src/ranex/governed_execution/__pycache__/__init__.cpython-314.pyc
src/ranex/__init__.py
src/ranex/policy/adapters/configuration/__init__.py
src/ranex/policy/adapters/configuration/__pycache__/__init__.cpython-314.pyc
src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py
src/ranex/policy/adapters/configuration/yaml/__init__.py
src/ranex/policy/adapters/configuration/yaml/__pycache__/gate_catalog_loader.cpython-314.pyc
src/ranex/policy/adapters/configuration/yaml/__pycache__/__init__.cpython-314.pyc
src/ranex/policy/adapters/__init__.py
src/ranex/policy/adapters/__pycache__/__init__.cpython-314.pyc
src/ranex/policy/api/contracts.py
src/ranex/policy/api/__init__.py
src/ranex/policy/api/__pycache__/contracts.cpython-314.pyc
src/ranex/policy/api/__pycache__/__init__.cpython-314.pyc
src/ranex/policy/domain/gates.py
src/ranex/policy/domain/__init__.py
src/ranex/policy/domain/__pycache__/gates.cpython-314.pyc
src/ranex/policy/domain/__pycache__/__init__.cpython-314.pyc
src/ranex/policy/__init__.py
src/ranex/policy/__pycache__/__init__.cpython-314.pyc
src/ranex/__pycache__/__init__.cpython-314.pyc
src/ranex/work_management/api/contracts.py
src/ranex/work_management/api/__init__.py
src/ranex/work_management/api/__pycache__/contracts.cpython-314.pyc
src/ranex/work_management/api/__pycache__/__init__.cpython-314.pyc
src/ranex/work_management/domain/__init__.py
src/ranex/work_management/domain/__pycache__/__init__.cpython-314.pyc
src/ranex/work_management/domain/__pycache__/transitions.cpython-314.pyc
src/ranex/work_management/domain/transitions.py
src/ranex/work_management/__init__.py
src/ranex/work_management/__pycache__/__init__.cpython-314.pyc
tests/architecture/__pycache__/test_kernel_imports.cpython-314-pytest-9.1.1.pyc
tests/architecture/test_kernel_imports.py
tests/contract/policy/__pycache__/test_gate_policy_loader.cpython-314-pytest-9.1.1.pyc
tests/contract/policy/test_gate_policy_loader.py
tests/integration/assurance/__pycache__/test_evidence_artifact_verifier.cpython-314-pytest-9.1.1.pyc
tests/integration/assurance/__pycache__/test_hash_chain_ledger.cpython-314-pytest-9.1.1.pyc
tests/integration/assurance/test_evidence_artifact_verifier.py
tests/integration/assurance/test_hash_chain_ledger.py
tests/integration/governed_execution/__pycache__/test_sqlite_execution_store.cpython-314-pytest-9.1.1.pyc
tests/integration/governed_execution/test_sqlite_execution_store.py
tests/migration/governed_execution/__pycache__/test_execution_store_migration.cpython-314-pytest-9.1.1.pyc
tests/migration/governed_execution/test_execution_store_migration.py
tests/replay/governed_execution/__pycache__/test_execution_replay.cpython-314-pytest-9.1.1.pyc
tests/replay/governed_execution/test_execution_replay.py
tests/resilience/__pycache__/test_execution_sqlite_crash_boundary.cpython-314-pytest-9.1.1.pyc
tests/resilience/test_execution_sqlite_crash_boundary.py
tests/security/__pycache__/test_application_control_pep.cpython-314-pytest-9.1.1.pyc
tests/security/test_application_control_pep.py
tests/unit/foundation/domain/__pycache__/test_canonical.cpython-314-pytest-9.1.1.pyc
tests/unit/foundation/domain/__pycache__/test_identity.cpython-314-pytest-9.1.1.pyc
tests/unit/foundation/domain/test_canonical.py
tests/unit/foundation/domain/test_identity.py
tests/unit/governed_execution/application/__pycache__/test_gate_controller.cpython-314-pytest-9.1.1.pyc
tests/unit/governed_execution/application/test_gate_controller.py
tests/unit/governed_execution/domain/__pycache__/test_application_control.cpython-314-pytest-9.1.1.pyc
tests/unit/governed_execution/domain/__pycache__/test_execution.cpython-314-pytest-9.1.1.pyc
tests/unit/governed_execution/domain/test_application_control.py
tests/unit/governed_execution/domain/test_execution.py
tests/unit/work_management/domain/__pycache__/test_transitions.cpython-314-pytest-9.1.1.pyc
tests/unit/work_management/domain/test_transitions.py
---
    66 tests/replay/governed_execution/test_execution_replay.py
    38 tests/migration/governed_execution/test_execution_store_migration.py
   483 tests/architecture/test_kernel_imports.py
    76 tests/contract/policy/test_gate_policy_loader.py
  4205 total
[0m
[0m$ [0mgrep -rn "governed_execution" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -40
221:| Canonical authority | One `governed_execution` consistency cell owns run transitions, gate bindings, permit consumption, and effect intent. |
244:1. Only `governed_execution` chooses and commits a legal canonical run state.
409:`governed_execution` is one bounded consistency cell with four cohesive
429:`governed_execution` integration events and submits idempotent commands through
434:`governed_execution` owns the exact-subject `ConsumableAuthorityGrant` created
497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
548:| Workflow and run control | `governed_execution` | workflow runtime | `governed_execution` | Run events and state |
552:| Permits and effects | `governed_execution` | capability bus/outbox | `governed_execution` | Consumed permit + effect intent/result |
606:│       ├── governed_execution/
1022:The expanded `governed_execution` adapter illustrates a context-exclusive
1151:`governed_execution` remains the only expanded authority cell in the physical
1215:17. `governed_execution.application.process_manager` is orchestration-only. It
1242:25. Only Ranex `governed_execution` and `agent_collaboration` services create,
1288:  -> governed_execution Run + deterministic governor
1660:    owner_context: "governed_execution"
1954:    owner_context: "governed_execution"
2005:    owner_context: "governed_execution"
2046:    owner_context: "governed_execution"
2066:    owner_context: "governed_execution"
2086:    owner_context: "governed_execution"
2628:- one work item may have many `Run` attempts; `governed_execution` alone
2649:| `AI-G0`–`AI-G10` | Exact-subject evidence gates for one agent-assisted execution | `assurance` creates `GateEvaluation`; `governed_execution` only binds a fresh pass |
2711:| `ActivityResolution` | reuse `states.json#ActivityStatus@1.0.0`; `governed_execution` | restricted to `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
2714:| `EffectKnownOutcome` | reuse `states.json#EffectStatus@1.0.0`; `governed_execution` | restricted to known attempt dispositions `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`; `FAILED_RETRYABLE` is nonterminal for the effect lifecycle |
2767:| `EVENT-RUNCREATED` / `RunCreated` | `governed_execution` / `run_service`; `work_management`, `process_assurance` | `Run`; accepted unique run request, work item not terminal | `run_id:Id<Run>`, `work_item_id:Id<WorkItem>`, `initial_status:Enum<RunStatus>=PROPOSED`, `created_by_principal_id:Id<Principal>`, `workflow_request_ref:Ref<WorkflowRequest>` |
2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
2769:| `EVENT-PACKETBOUND` / `PacketBound` | `governed_execution` / `packet_binding_service`; `agent_collaboration`, `assurance` | `Run`; workflow pinned, packet sealed for same work/subject | `run_id:Id<Run>`, `task_packet_ref:Ref<TaskPacket>`, `test_practice_profile_ref:Ref<TestPracticeProfile>`, `engineering_practice_profile_ref:Ref<EngineeringPracticeProfile>` |
2770:| `EVENT-RUNMARKEDREADY` / `RunMarkedReady` | `governed_execution` / `run_lifecycle_service`; `agent_collaboration`, `work_management` | `Run`; workflow/packet/profiles bound, reservation and policy current | `run_id:Id<Run>`, `from_status:Enum<RunStatus>`, `to_status:Enum<RunStatus>=READY`, `readiness_snapshot_ref:Ref<EvidenceSnapshot>` |
2771:| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
2772:| `EVENT-AUTHORIZATIONEVALUATED` / `AuthorizationEvaluated` | `governed_execution` / `authorization_service`; `policy`, `assurance` | `Activity`; requested activity has current identity/policy/subject | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `authorization_snapshot_ref:Ref<AuthorizationSnapshot>`, `decision:Enum<AuthorizationOutcome>`, `reason_codes:Set<String>` |
2773:| `EVENT-ACTIVITYDISPATCHED` / `ActivityDispatched` | `governed_execution` / `dispatch_service`; `agent_collaboration`, `resource_governance` | `Activity`; authorization allowed, assignment/lease/reservation current | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `assignment_ref:Ref<AgentAssignment>`, `worker_attempt_id:Id<WorkerAttempt>`, `lease_ref:Ref<WorkerLease>`, `dispatch_attempt:UInt` |
2774:| `EVENT-ACTIVITYRESOLVED` / `ActivityResolved` | `governed_execution` / `activity_resolution_service`; `assurance`, `work_management` | `Activity`; typed result normalized and every required effect has the attempt disposition/reconciliation required by the selected activity edge | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `run_result_ref:Ref<RunResult>`, `resolution:Enum<ActivityStatus>` restricted by `ActivityResolution`, `required_effect_ids:Set<EffectId>[0..N]` (empty exactly for a declared pure zero-effect activity), `resolved_at:Utc` |
2775:| `EVENT-EVIDENCESNAPSHOTBOUND` / `EvidenceSnapshotBound` | `governed_execution` / `evidence_binding_service`; `assurance` | `Run`; eligible fresh snapshot resolves to exact run subject | `run_id:Id<Run>`, `gate_id:Id<Gate>`, `evidence_snapshot_ref:Ref<EvidenceSnapshot>`, `required_claim_ids:Set<ClaimId>`, `freshness_cutoff:Utc` |
2776:| `EVENT-GATEEVALUATED` / `GateEvaluated` | `governed_execution` / `gate_binding_service`; `assurance`, `work_management` | `Run`; qualified gate evaluation matches bound snapshot/subject | `run_id:Id<Run>`, `gate_evaluation_ref:Ref<GateEvaluation>`, `gate_id:Id<Gate>`, `outcome:Enum<GateOutcome>`, `reason_codes:Set<String>[0..N]` (empty only for a qualified warning-free `PASS`; every other outcome has at least one reason) |
2777:| `EVENT-HUMANDECISIONSNAPSHOTBOUND` / `HumanDecisionSnapshotBound` | `governed_execution` / `decision_binding_service`; `policy`, `assurance` | `Run`; policy requires human choice and authenticated decision is current/exact | `run_id:Id<Run>`, `decision_ref:Ref<HumanDecisionRecord>`, `decision_kind:Enum<HumanDecisionKind>`, `decision_status:Enum<HumanDecisionRecordStatus>=APPROVED`, `decision_snapshot_digest:Sha256` |
2778:| `EVENT-PERMITISSUED` / `PermitIssued` | `governed_execution` / `permit_service`; `policy`, `operations` | `Run`; fresh gate pass and required decision produce eligible one-shot grant | `run_id:Id<Run>`, `permit_ref:Ref<Permit>`, `authority_grant_ref:Ref<ConsumableAuthorityGrant>`, `action_type:String`, `expires_at:Utc` |
2779:| `EVENT-PERMITCONSUMED` / `PermitConsumed` | `governed_execution` / `permit_service`; `operations`, `process_assurance` | `Run`; atomic compare-and-swap consumes unused current permit once | `run_id:Id<Run>`, `permit_id:Id<Permit>`, `consumed_for_effect_id:Id<Effect>`, `consumption_version:UInt`, `consumed_at:Utc` |
2780:| `EVENT-EFFECTINTENTRECORDED` / `EffectIntentRecorded` | `governed_execution` / `effect_service`; `operations`, `artifact_management` | `Effect`; permit consumption and durable intent occur in one UoW | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `effect_id:Id<Effect>`, `permit_id:Id<Permit>`, `effect_type:String`, `destination_fact_ref:Ref<DestinationFact>`, `argument_digest:Sha256` |
2781:| `EVENT-EFFECTDISPATCHED` / `EffectDispatched` | `governed_execution` / `effect_dispatch_service`; `operations` | `Effect`; committed intent leased, deadline/retry policy allows attempt | `effect_id:Id<Effect>`, `dispatch_attempt:UInt`, `adapter_id:String`, `adapter_version:String`, `provider_request_id:String`, `dispatched_at:Utc` |
2782:| `EVENT-EFFECTRESOLVED` / `EffectResolved` | `governed_execution` / `effect_resolution_service`; `operations`, `assurance` | `Effect`; typed provider result proves a known disposition for the completed attempt | `effect_id:Id<Effect>`, `outcome:Enum<EffectStatus>` restricted by `EffectKnownOutcome`, `provider_receipt_ref:Ref<ProviderReceipt>`, `result_artifact_ref:Ref<Artifact>`, `resolved_at:Utc` |
[0m
[0m$ [0mgrep -n "HERMES-OWNER-DECISION" docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | head -60
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
[0m$ [0mgrep -rn "HERMES-OWNER-DECISION" --include=*.md --include=*.json . | grep -v "ADR-0013" | head -40
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1515:      "provision_id": "HERMES-OWNER-DECISION-001",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1540:      "provision_id": "HERMES-OWNER-DECISION-002",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1565:      "provision_id": "HERMES-OWNER-DECISION-003",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1590:      "provision_id": "HERMES-OWNER-DECISION-004",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1615:      "provision_id": "HERMES-OWNER-DECISION-005",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1640:      "provision_id": "HERMES-OWNER-DECISION-006",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1665:      "provision_id": "HERMES-OWNER-DECISION-007",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1690:      "provision_id": "HERMES-OWNER-DECISION-008",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1715:      "provision_id": "HERMES-OWNER-DECISION-009",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1740:      "provision_id": "HERMES-OWNER-DECISION-010",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1765:      "provision_id": "HERMES-OWNER-DECISION-011",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1790:      "provision_id": "HERMES-OWNER-DECISION-012",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1815:      "provision_id": "HERMES-OWNER-DECISION-013",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1840:      "provision_id": "HERMES-OWNER-DECISION-014",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1865:      "provision_id": "HERMES-OWNER-DECISION-015",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1890:      "provision_id": "HERMES-OWNER-DECISION-016",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1915:      "provision_id": "HERMES-OWNER-DECISION-017",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1940:      "provision_id": "HERMES-OWNER-DECISION-018",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1965:      "provision_id": "HERMES-OWNER-DECISION-019",
./.claude/worktrees/kernel-tracer/architecture/contracts/hermes-research-promotions.json:1990:      "provision_id": "HERMES-OWNER-DECISION-020",
./.claude/worktrees/kernel-tracer/schemas/common/hermes-research-provision-v1.schema.json:183:          "pattern": "^HERMES-OWNER-DECISION-[0-9]{3}$",
./architecture/contracts/hermes-research-promotions.json:1515:      "provision_id": "HERMES-OWNER-DECISION-001",
./architecture/contracts/hermes-research-promotions.json:1540:      "provision_id": "HERMES-OWNER-DECISION-002",
./architecture/contracts/hermes-research-promotions.json:1565:      "provision_id": "HERMES-OWNER-DECISION-003",
./architecture/contracts/hermes-research-promotions.json:1590:      "provision_id": "HERMES-OWNER-DECISION-004",
./architecture/contracts/hermes-research-promotions.json:1615:      "provision_id": "HERMES-OWNER-DECISION-005",
./architecture/contracts/hermes-research-promotions.json:1640:      "provision_id": "HERMES-OWNER-DECISION-006",
./architecture/contracts/hermes-research-promotions.json:1665:      "provision_id": "HERMES-OWNER-DECISION-007",
./architecture/contracts/hermes-research-promotions.json:1690:      "provision_id": "HERMES-OWNER-DECISION-008",
./architecture/contracts/hermes-research-promotions.json:1715:      "provision_id": "HERMES-OWNER-DECISION-009",
./architecture/contracts/hermes-research-promotions.json:1740:      "provision_id": "HERMES-OWNER-DECISION-010",
./architecture/contracts/hermes-research-promotions.json:1765:      "provision_id": "HERMES-OWNER-DECISION-011",
./architecture/contracts/hermes-research-promotions.json:1790:      "provision_id": "HERMES-OWNER-DECISION-012",
./architecture/contracts/hermes-research-promotions.json:1815:      "provision_id": "HERMES-OWNER-DECISION-013",
./architecture/contracts/hermes-research-promotions.json:1840:      "provision_id": "HERMES-OWNER-DECISION-014",
./architecture/contracts/hermes-research-promotions.json:1865:      "provision_id": "HERMES-OWNER-DECISION-015",
./architecture/contracts/hermes-research-promotions.json:1890:      "provision_id": "HERMES-OWNER-DECISION-016",
./architecture/contracts/hermes-research-promotions.json:1915:      "provision_id": "HERMES-OWNER-DECISION-017",
./architecture/contracts/hermes-research-promotions.json:1940:      "provision_id": "HERMES-OWNER-DECISION-018",
./architecture/contracts/hermes-research-promotions.json:1965:      "provision_id": "HERMES-OWNER-DECISION-019",
[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md[90m [offset=800, limit=200][0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md[90m [offset=1000, limit=190][0m
[0m
[0m$ [0mgrep -n "IMPLEMENTATION_START\|readiness tier\|Tier\|NOT_ASSESSED\|PRODUCTION_READY" docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md | head -80
15:| Review/expiry date | Review on any readiness tier, gate, evidence role, reviewer route, architecture-rule denominator, production-admission, or authority-boundary change |
23:| `1.1.0` | 2026-07-29 | Reconciled the readiness lifecycle with the shared state/transition conventions: registered `READINESS-STATE-1.0` in the main state catalog, changed guard identifiers to underscore form, and bound transition facts to the standard `architecture/contracts/states.json` catalog. This corrects the prior cross-contract incompatibility without changing or versioning `TransitionEventV1` and declares no readiness tier. |
28:Ranex has two noncompensating readiness tiers with different authority and
33:| `IMPLEMENTATION_START_READY` | `DESIGN_DEFINITION_READY` | Admission of staged product implementation under the normal per-work-item packet, gate, grant, permit, TDD, review, and landing controls | Enacted product runtime, production safety, operational effectiveness, mature capability scores, release, deployment, or user impact |
34:| `PRODUCTION_READY` | `ENTERPRISE_RUNTIME_READY` | Eligibility to request the normal exact-subject release/deployment authority chain after runtime and operational readiness passes | A deployment effect, release permit, waiver, permanent qualification, or proof of healthy operation after change |
41:`IMPLEMENTATION_START_READY` is deliberately attainable before full runtime
43:`NOT_ASSESSED`, but that fact must be explicit, cannot be represented as
48:`PRODUCTION_READY` requires enacted runtime producers, complete current rule
59:Before `IMPLEMENTATION_START_READY`, one bounded
93:  catalog_status: "DEFINITION_ONLY_NOT_ASSESSED"
131:      - "NOT_ASSESSED"
137:      NOT_ASSESSED: "no runtime-assurance attempt exists; paired runtime assessment ref/digest are null"
154:    initial_state: "NOT_ASSESSED"
156:      - "NOT_ASSESSED"
157:      - "IMPLEMENTATION_START_EVALUATING"
158:      - "IMPLEMENTATION_START_BLOCKED"
159:      - "IMPLEMENTATION_START_READY"
162:      - "PRODUCTION_READY"
165:      - "NOT_ASSESSED>IMPLEMENTATION_START_EVALUATING@READINESS_ASSESSMENT_OPENED"
166:      - "IMPLEMENTATION_START_EVALUATING>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_NOT_PASS"
167:      - "IMPLEMENTATION_START_EVALUATING>IMPLEMENTATION_START_READY@IMPLEMENTATION_START_EXACT_PASS_AND_HUMAN_DECISION"
168:      - "IMPLEMENTATION_START_BLOCKED>IMPLEMENTATION_START_EVALUATING@FRESH_EXACT_SUBJECT_REASSESSMENT"
169:      - "IMPLEMENTATION_START_READY>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_EVIDENCE_INVALIDATED"
170:      - "IMPLEMENTATION_START_READY>PRODUCTION_EVALUATING@PRODUCTION_ASSESSMENT_OPENED"
172:      - "PRODUCTION_EVALUATING>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
173:      - "PRODUCTION_EVALUATING>PRODUCTION_READY@PRODUCTION_EXACT_PASS_AND_HUMAN_DECISION"
175:      - "PRODUCTION_BLOCKED>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
176:      - "PRODUCTION_READY>PRODUCTION_BLOCKED@PRODUCTION_EVIDENCE_INVALIDATED"
177:      - "PRODUCTION_READY>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
179:      - "NOT_ASSESSED>IMPLEMENTATION_START_READY"
180:      - "NOT_ASSESSED>PRODUCTION_READY"
181:      - "IMPLEMENTATION_START_BLOCKED>IMPLEMENTATION_START_READY"
182:      - "IMPLEMENTATION_START_READY>PRODUCTION_READY"
183:      - "PRODUCTION_BLOCKED>PRODUCTION_READY"
184:      - "PRODUCTION_READY>IMPLEMENTATION_START_READY"
257:      source_commit_sha1: "the clean committed upstream-derived evaluation baseline from which Tier 1 admits staged implementation"
260:      tier_evidence_subject: "all four tier_evidence_subject_* fields are null for Tier 1; for Tier 2 schema/ref/digest bind one exact built-once runtime release subject and its manifest field follows that native schema's nullability rule"
265:    descendant_validity_rule: "After Tier 1 admission, an ordinary authorized product implementation commit does not change this frozen evaluation subject. Future reliance requires a clean current head descended from source_commit_sha1 and byte-identical governed source-manifest paths; a non-descendant, dirty head, or governed-path change invalidates Tier 1."
303:      entries: "exactly 7 for Tier 1; exactly 8 for Tier 2"
332:      TIER_EVIDENCE_SUBJECT: "present only for Tier 2; schema/ref/digest/manifest binding equals the exact_subject tier_evidence_subject_* tuple"
466:      prior_state: {enum: ["NOT_ASSESSED", "IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_BLOCKED", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"]}
467:      proposed_state: {enum: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_BLOCKED", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"]}
502:      - "gate_results is the exact gate set for tier_id with no duplicate, omission, extra, or reordered row; the production tier resolves its prerequisite through READY-IMPLEMENTATION-PREREQUISITE-001, whose exact current assessment independently contains the complete Tier 1 gate set"
507:      - "Tier 1 READY permits runtime_assessment_status only NOT_ASSESSED or ASSESSED_PASS; Tier 2 READY requires ASSESSED_PASS; UNKNOWN, ASSESSED_FAIL, or CONFLICT forbids any READY proposed_state"
508:      - "runtime_assessment_ref and runtime_assessment_digest are paired; NOT_ASSESSED requires both null, while every other status requires both to resolve one exact immutable runtime-assurance reconciliation whose derived status equals runtime_assessment_status"
509:      - "A production assessment resolves one CURRENT IMPLEMENTATION_START_READY assessment with the identical readiness_basis_digest; the two tier-specific subject refs and digests necessarily differ because tier_id differs"
515:      canonical_state: "IMPLEMENTATION_START_READY"
518:      runtime_assessment_policy: "NOT_ASSESSED_OR_ASSESSED_PASS_ALLOWED; UNKNOWN_ASSESSED_FAIL_OR_CONFLICT_BLOCK; ASSESSED_PASS_CANNOT_COMPENSATE"
519:      capability_score_policy: "NULL_OR_NOT_ASSESSED_ALLOWED_AND_NONAUTHORITATIVE"
535:      canonical_state: "PRODUCTION_READY"
538:      runtime_assessment_policy: "ONLY_ASSESSED_PASS_ALLOWED; NOT_ASSESSED_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT_BLOCK"
565:    - {gate_id: "READY-HUMAN-START-DECISION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "AUTHENTICATED_IMPLEMENTATION_START_DECISION", freshness_rule: "ISSUED_AFTER_ALL_NON_DECISION_TIER_EVIDENCE_AND_NOT_REVOKED_OR_SUPERSEDED", bridge_rule_id: "BRIDGE-READY-HUMAN-START-DECISION-001", noncompensating: true}
566:    - {gate_id: "READY-IMPLEMENTATION-PREREQUISITE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "CURRENT_IMPLEMENTATION_START_READINESS_ASSESSMENT", freshness_rule: "CURRENT_TIER1_ASSESSMENT_WITH_IDENTICAL_READINESS_BASIS_DIGEST", bridge_rule_id: "BRIDGE-READY-IMPLEMENTATION-PREREQUISITE-001", noncompensating: true}
583:      TIER1_READINESS_SUBJECT: "native schema is readiness-subject/v1; native ref/digest/manifest resolve an independently valid Tier 1 subject and manifest"
584:      TIER2_READINESS_SUBJECT: "native schema is readiness-subject/v1; native ref/digest/manifest equal the containing Tier 2 readiness subject exactly"
585:      TIER2_RUNTIME_RELEASE_SUBJECT: "native schema is exact-subject/v1; native ref/digest/manifest equal all containing Tier 2 tier_evidence_subject_* fields and the closed manifest TIER_EVIDENCE_SUBJECT entry"
587:      READY-ADOPTION-GATES-001: {bridge_rule_id: "BRIDGE-READY-ADOPTION-GATES-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals all Tier 2 tier_evidence_subject_* fields; evidence is the complete exact adoption-gate reconciliation for that release subject"}
588:      READY-AUTHORITY-CHAIN-001: {bridge_rule_id: "BRIDGE-READY-AUTHORITY-CHAIN-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds only authority qualification, not a release grant or permit"}
589:      READY-CAPABILITY-ASSESSMENTS-001: {bridge_rule_id: "BRIDGE-READY-CAPABILITY-ASSESSMENTS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence is a complete population reconciliation whose members bind the same scope, window, service, and value stream"}
595:      READY-HUMAN-PRODUCTION-DECISION-001: {bridge_rule_id: "BRIDGE-READY-HUMAN-PRODUCTION-DECISION-001", native_subject_class: "TIER2_READINESS_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals the containing Tier 2 readiness subject exactly; evidence_digest equals the assessment human_decision_digest"}
596:      READY-HUMAN-START-DECISION-001: {bridge_rule_id: "BRIDGE-READY-HUMAN-START-DECISION-001", native_subject_class: "TIER1_READINESS_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals the containing Tier 1 readiness subject exactly; evidence_digest equals the assessment human_decision_digest"}
598:      READY-IMPLEMENTATION-PREREQUISITE-001: {bridge_rule_id: "BRIDGE-READY-IMPLEMENTATION-PREREQUISITE-001", native_subject_class: "TIER1_READINESS_SUBJECT", relation_rule: "native subject is Tier 1 with all tier_evidence_subject_* fields null; its readiness_basis_digest equals the containing Tier 2 basis, its subject ref/digest necessarily differ, and evidence_digest equals the unique current Tier 1 PASS assessment digest"}
600:      READY-OPERATING-EVIDENCE-001: {bridge_rule_id: "BRIDGE-READY-OPERATING-EVIDENCE-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds the built-once artifact, intended destination, qualified target-equivalent environment, and declared observation window"}
601:      READY-RECOVERY-EVIDENCE-001: {bridge_rule_id: "BRIDGE-READY-RECOVERY-EVIDENCE-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds backup, restore, rollback, incident, and reconciliation results for that release subject"}
602:      READY-RULE-RESULTS-001: {bridge_rule_id: "BRIDGE-READY-RULE-RESULTS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence contains exactly 18 ORG, 26 TDD, 10 ADR-0009, and 10 ADR-0010 current nonblocking rows"}
603:      READY-RUNTIME-PRODUCERS-001: {bridge_rule_id: "BRIDGE-READY-RUNTIME-PRODUCERS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence covers every active registered producer and proves cross-producer forgery denial"}
605:      READY-SECURITY-ISOLATION-001: {bridge_rule_id: "BRIDGE-READY-SECURITY-ISOLATION-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds target host, route, model, tools, sandbox, bypass matrix, privacy, and data class"}
618:      READINESS-TIER-IMPLEMENTATION-START-001: "AUTHORIZE_STAGED_IMPLEMENTATION_START"
702:      - "runtime UNKNOWN, ASSESSED_FAIL, or CONFLICT for Tier 1; runtime anything except ASSESSED_PASS for Tier 2"
708:    - {condition: "TIER1_REQUIRED_INPUT_NOT_PASS", from_states: ["IMPLEMENTATION_START_EVALUATING"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
709:    - {condition: "DIRTY_UNCOMMITTED_OR_WRONG_ANCESTRY", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
710:    - {condition: "SYNTHETIC_TDD_OR_MISSING_SEPARATE_SUCCEEDED_LANDING_OR_SEAL", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
711:    - {condition: "MISSING_STALE_OR_NONINDEPENDENT_REQUIRED_REVIEW", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
712:    - {condition: "UNRESOLVED_P0_OR_P1", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
713:    - {condition: "RUNTIME_NOT_ASSESSED_AT_TIER1", from_states: ["IMPLEMENTATION_START_EVALUATING"], to_state: "IMPLEMENTATION_START_EVALUATING", effect: "EXPLICIT_NONPASS_RUNTIME_FACT_RETAINED"}
714:    - {condition: "TIER1_RUNTIME_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
715:    - {condition: "TIER2_RUNTIME_NOT_ASSESSED_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
716:    - {condition: "RULE_RESULT_DENOMINATOR_NOT_EXACTLY_64_OR_ANY_BLOCKING_RESULT", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
717:    - {condition: "RUNTIME_PRODUCER_MISSING_WRONG_OWNER_OR_CROSS_PRODUCER_FORGERY", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
718:    - {condition: "OPERATIONAL_RECOVERY_SECURITY_SCORE_OR_AUTHORITY_EVIDENCE_INCOMPLETE", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
[0m
[0m$ [0msed -n '1,120p' docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md
# ADR-0012: Separate Implementation-Start and Production Readiness

| Field | Value |
|---|---|
| ADR ID | `ADR-0012` |
| Version | `1.1.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-29 |
| Effective revision | Definition-only working tree; no readiness assessment or authorization is claimed |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `process_assurance`, `assurance`, `policy`, `work_management`, `governed_execution`, `configuration_management`, `provenance_compliance`, `migration`, `release_management`, `operations`, and every context supplying readiness evidence |
| RFC | Not required; resolves the human owner's readiness-language and bootstrap-authority decision |
| Supersedes | Ambiguous uses of “build ready,” “enterprise build ready,” and “runtime ready” in earlier documents; it does not weaken any evidence, authority, security, recovery, or production gate |
| Review/expiry date | Review on any readiness tier, gate, evidence role, reviewer route, architecture-rule denominator, production-admission, or authority-boundary change |
| Compatibility/migration class | New typed readiness namespace; historical unqualified readiness statements become nonauthoritative prose until mapped to this contract |
| Security/data class | Public decision and gate metadata; referenced source, review, security, operational, and production evidence retains its own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.1.0` | 2026-07-29 | Reconciled the readiness lifecycle with the shared state/transition conventions: registered `READINESS-STATE-1.0` in the main state catalog, changed guard identifiers to underscore form, and bound transition facts to the standard `architecture/contracts/states.json` catalog. This corrects the prior cross-contract incompatibility without changing or versioning `TransitionEventV1` and declares no readiness tier. |
| `1.0.0` | 2026-07-29 | Initial accepted definition-only readiness contract. |

## Decision

Ranex has two noncompensating readiness tiers with different authority and
evidence boundaries:

| Canonical machine state | Documentation label | What it permits | What it does not claim |
|---|---|---|---|
| `IMPLEMENTATION_START_READY` | `DESIGN_DEFINITION_READY` | Admission of staged product implementation under the normal per-work-item packet, gate, grant, permit, TDD, review, and landing controls | Enacted product runtime, production safety, operational effectiveness, mature capability scores, release, deployment, or user impact |
| `PRODUCTION_READY` | `ENTERPRISE_RUNTIME_READY` | Eligibility to request the normal exact-subject release/deployment authority chain after runtime and operational readiness passes | A deployment effect, release permit, waiver, permanent qualification, or proof of healthy operation after change |

The documentation labels are explanatory labels, not additional states or
accepted aliases. Machine records use only the canonical states. A document
that says only “build ready,” “enterprise ready,” or “runtime ready” grants no
authority.

`IMPLEMENTATION_START_READY` is deliberately attainable before full runtime
enactment. Runtime rule results and capability effectiveness may remain
`NOT_ASSESSED`, but that fact must be explicit, cannot be represented as
`PASS`, and cannot be omitted from the assessment. This prevents absent runtime
evidence from circularly blocking the start of staged implementation while
also preventing a paper contract from masquerading as a production system.

`PRODUCTION_READY` requires enacted runtime producers, complete current rule
results, operational and recovery evidence, applicable evidence-bound
capability assessments, and the normal human authority chain. An
implementation-start result cannot compensate for any missing production
evidence.

Neither tier is currently declared. This ADR accepts the vocabulary,
state machine, gate contracts, and authority boundary only.

## Bootstrap without circular authority

Before `IMPLEMENTATION_START_READY`, one bounded
`PRE_READINESS_TOOLING_TRACER` lane may create only the evidence needed to
evaluate that tier:

- compiler, generator, validator, schema, fixture, manifest, and deterministic
  review-harness changes on registered architecture/tooling paths;
- fork-preservation, provenance, clean-worktree, and source-manifest work;
- one real current-subject ADR-0008 cycle and its separately produced
  `SUCCEEDED` `LandingRecord` and sealing evidence; and
- read-only review and finding-reconciliation artifacts.

Every tracer change still needs an exact work item, bounded task packet,
ordinary path/effect authority, tests, review, and human-controlled landing.
The lane cannot implement a product capability, activate a product runtime,
process production/user data, deploy, release, grant itself readiness, relax a
gate, or become a reusable bypass. Failure, expiry, scope growth, or an
unregistered path ends the tracer without a readiness transition.

## Exact machine contract

The following marked YAML block is the sole semantic source for the readiness
tier catalog, state axis, assessment schema, resolver, and synthetic fixture
denominators. Generated projections preserve the complete mapping without
semantic edits.

<!-- BEGIN ADR12 READINESS TIER CONTRACT -->

```yaml
readiness_tier_contract:
  contract_id: "RANEX-READINESS-TIER-CONTROL-1.0"
  contract_version: "1.0.0"
  schema_version: "readiness-tier-contract/v1"
  catalog_id: "RANEX-READINESS-TIERS-001"
  catalog_version: "1.0.0"
  catalog_status: "DEFINITION_ONLY_NOT_ASSESSED"
  governing_adr: "ADR-0012"
  canonicalization: "RFC8785"
  digest_algorithm: "SHA-256"
  digest_encoding: "sha256:<64 lowercase hex>"
  additional_properties: false
  noncompensating: true
  source_projection_ref: "architecture/contracts/readiness-tiers.json"
  assessment_registry_ref: "architecture/contracts/readiness-assessments.json"
  subject_schema_ref: "schemas/assurance/readiness-subject-v1.schema.json"
  subject_manifest_schema_ref: "schemas/assurance/readiness-subject-manifest-v1.schema.json"
  evidence_binding_schema_ref: "schemas/assurance/readiness-evidence-binding-v1.schema.json"
  assessment_schema_ref: "schemas/assurance/readiness-assessment-v1.schema.json"
  inherited_type_authority:
    source: "ADR-0008, AI_ARTIFACT_CONTRACTS.md, and their generated schemas"
    types:
      - "ArchitectureSubject"
      - "TddCycleRecordV1"
      - "LandingRecordV1"
      - "HumanDecisionRecord"
      - "ReviewVerdict"
      - "GateEvaluation"
      - "CapabilityAssessment"
      - "TransitionEventV1"
  scalar_types:
    safe_id: "nonempty registered identifier with no path traversal"
    safe_ref: "safe_id or registered urn:ranex identifier"
    sha1: "40 lowercase hexadecimal characters"
[0m
[0m$ [0mgrep -n "WorkItemStatus" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -30; echo ===; grep -rn "WorkItemStatus" architecture/contracts/data-ownership.json architecture/contracts/states.json | head -20
220:| Work lifecycle authority | `work_management` owns `WorkItemStatus`; boards, runs, models, and Hermes sessions do not. |
508:| `work_management` | Projects, canonical `WorkItemStatus`, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections | Core-SDLC transition API, GitHub intake, product/requirement links, governed-run/evidence integration |
1455:| `WorkItemStatus` | `FUNNEL`, `TRIAGE`, `DISCOVERY`, `DEFINITION`, `DESIGN`, `READY`, `IN_PROGRESS`, `VERIFICATION`, `RELEASE_READY`, `RELEASING`, `OPERATING`, `OUTCOME_REVIEW`, `CLOSED`, `BLOCKED`, `CANCELLED`, `ROLLED_BACK` |
1464:| `IntakeStatus` | `PROPOSED`, `ACCEPTED`, `REJECTED`, `DUPLICATE`, `WITHDRAWN`; owned by `work_management`; it does not alias `WorkItemStatus` |
1635:  - axis_id: "WorkItemStatus"
1638:    contract_ref: "states.json#WorkItemStatus@1.0.0"
1644:    emitted_fact: "TransitionEventV1(axis_id=WorkItemStatus)"
1830:    revocation_semantics: "NOT_APPLICABLE:accepted work is governed by WorkItemStatus"
2627:- `work_management` alone transitions `WorkItemStatus`.
2634:  `WorkItemStatus`.
2792:| `EVENT-WORKITEMCREATED` / `WorkItemCreated` | `work_management` / `work_intake_service`; `product_definition`, `process_assurance` | `WorkItem`; accepted nonduplicate intake with owner and initial scope | `work_item_id:Id<WorkItem>`, `intake_ref:Ref<WorkIntake>`, `initial_status:Enum<WorkItemStatus>=FUNNEL`, `owner_id:Id<PrincipalOrTeam>`, `scope_digest:Sha256` |
2796:| `EVENT-WORKITEMTRANSITIONED` / `WorkItemTransitioned` | `work_management` / `work_lifecycle_service`; `governed_execution`, `product_definition`, `process_assurance` | `WorkItem`; registered legal transition passes gate/decision/version checks | `work_item_id:Id<WorkItem>`, `from_status:Enum<WorkItemStatus>`, `to_status:Enum<WorkItemStatus>`, `transition_rule_id:String`, `gate_evaluation_ref:Ref<GateEvaluation>`, `decision_ref:Ref<HumanDecisionRecord>?` |
2797:| `EVENT-WORKITEMBLOCKED` / `WorkItemBlocked` | `work_management` / `work_lifecycle_service`; `governed_execution`, `product_definition` | `WorkItem`; named material blocker prevents legal progression | `work_item_id:Id<WorkItem>`, `from_status:Enum<WorkItemStatus>`, `block_reason_code:String`, `blocking_refs:Set<ArtifactRef>`, `blocked_at:Utc` |
2798:| `EVENT-WORKITEMUNBLOCKED` / `WorkItemUnblocked` | `work_management` / `work_lifecycle_service`; `governed_execution`, `product_definition` | `WorkItem`; every named blocker has fresh resolution | `work_item_id:Id<WorkItem>`, `from_status:Enum<WorkItemStatus>=BLOCKED`, `to_status:Enum<WorkItemStatus>`, `resolution_refs:Set<ArtifactRef>`, `unblocked_at:Utc` |
2799:| `EVENT-WORKITEMCANCELLED` / `WorkItemCancelled` | `work_management` / `work_lifecycle_service`; `governed_execution`, `product_definition` | `WorkItem`; authenticated cancellation accepted; active runs dispositioned | `work_item_id:Id<WorkItem>`, `from_status:Enum<WorkItemStatus>`, `decision_ref:Ref<HumanDecisionRecord>`, `active_run_disposition_refs:Set<ArtifactRef>[0..N]` (empty only when the exact pre-cancellation snapshot proves no active run), `cancelled_at:Utc` |
2806:| `EVENT-WORKITEMCLOSED` / `WorkItemClosed` | `work_management` / `work_lifecycle_service`; `product_definition`, `process_assurance`, `release_management` | `WorkItem`; required run/release/operation/outcome evidence linked, no blocker | `work_item_id:Id<WorkItem>`, `from_status:Enum<WorkItemStatus>`, `to_status:Enum<WorkItemStatus>=CLOSED`, `closure_snapshot_ref:Ref<EvidenceSnapshot>`, `closure_decision_ref:Ref<HumanDecisionRecord>`, `closed_at:Utc` |
2997:    initial_bindings: [{axis_id: "WorkItemStatus", axis_version: "1.0.0", initial_value: "FUNNEL"}]
3010:      - axis_id: "WorkItemStatus"
3017:      - axis_id: "WorkItemStatus"
3024:      - axis_id: "WorkItemStatus"
3031:      - axis_id: "WorkItemStatus"
3056:      - axis_id: "WorkItemStatus"
===
architecture/contracts/data-ownership.json:40:      "owned_data": "Projects, canonical WorkItemStatus, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections",
architecture/contracts/states.json:9:      "axis_id": "WorkItemStatus",
architecture/contracts/states.json:14:      "contract_ref": "states.json#WorkItemStatus@1.0.0",
architecture/contracts/states.json:16:      "emitted_fact": "TransitionEventV1(axis_id=WorkItemStatus)",
architecture/contracts/states.json:978:      "revocation_semantics": "NOT_APPLICABLE:accepted work is governed by WorkItemStatus",
[0m
[0m$ [0mgrep -n "loopback\|web dashboard\|web-dashboard\|dashboard" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -40
232:| Local UX | CLI, TUI, loopback-only web dashboard, GitHub edge, and a text-phone delivery port. |
235:| Public dashboard | Excluded. The web dashboard binds to loopback; private tailnet publication is an explicit delivery adapter and policy decision. |
253:6. Kanban, dashboards, Hermes session state, and external systems are projections
813:│   └── web-dashboard/
1160:### 12.2 Web dashboard structure
1162:The web dashboard is a presentation application, not another control plane:
1165:apps/web-dashboard/src/
3437:scheme/host/port and resolved IP set, denies loopback/link-local/private/cloud
3617:- a public internet dashboard;
[0m
[0m$ [0msed -n '215,270p;405,440p;490,560p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
| Engineering-practice application | Every architecture and implementation packet binds a machine-registered applicability profile, required behavior, deviations, and verification evidence; citation without demonstrated application is insufficient. |
| Legacy implementation guide | Deleted and retired by `ADR-0002`; historical references grant no construction authority and new route plans derive from this architecture. |
| Upstream relationship | Ranex is a Hermes-derived software fork; lineage/history/license proof is a blocking preflight, and GitHub network-fork status is tracked separately. |
| New core | Authority, domain, and application code outside the named compatibility adapter has no dependency on inherited Hermes internals. |
| Migration | Strangler migration inside the fork; no big-bang rewrite. |
| Work lifecycle authority | `work_management` owns `WorkItemStatus`; boards, runs, models, and Hermes sessions do not. |
| Canonical authority | One `governed_execution` consistency cell owns run transitions, gate bindings, permit consumption, and effect intent. |
| State storage | One physical SQLite authority database for the local target, with logical context ownership, an append-only journal, and a transactional outbox. |
| Event sourcing | Selective replay journal for governed execution; the whole product is not event sourced. |
| Workflow runtime | A runtime port with a local durable runner as the product default; another engine may implement the same port after an ADR and parity tests. |
| Effects | At-least-once or at-most-once attempt semantics with idempotency and reconciliation; never claim exactly once. |
| Policy failure | Deny visibly. Missing, stale, malformed, unavailable, or conflicting blocking proof cannot pass. |
| Model authority | Models produce proposals and observations. They cannot emit an accepted transition, gate decision, permit, waiver, or human decision. |
| AI-worker fleet | Ranex control services alone orchestrate deterministic bounded fan-out/join; every model/harness is a leaf worker; each assignment receives a task-minimal proper subset of its role ceiling; writes are isolated and landing is human-controlled. |
| First-party capabilities | Shipped with Ranex behind stable internal interfaces; not user-installed prerequisites. |
| External extensions | Lower-trust, out-of-process, capability-scoped, and permanently outside the authority path. |
| Desktop app | Excluded from the Ranex target. No Electron desktop, desktop bootstrap, or desktop updater. |
| Local UX | CLI, TUI, loopback-only web dashboard, GitHub edge, and a text-phone delivery port. |
| Phone implementation | Telegram is the first mapped text-phone adapter; other channels implement the same delivery/auth contracts. |
| Voice | Mapped as an optional media/transcription adapter, inactive unless a future accepted decision requires it. It never enters the kernel. |
| Public dashboard | Excluded. The web dashboard binds to loopback; private tailnet publication is an explicit delivery adapter and policy decision. |
| Providers | One explicit provider/model/official-runtime route per assignment; eligible local individual subscription and product API/BYOK/cloud routes are distinct. No adapter/provider/model fallback or auxiliary model call. |
| Nous commercial product | Hermes/Nous is provenance, reference, and non-inference compatibility only: no live inference, parent-agent loop, Portal/model route, credential/entitlement, billing, credits, subscriptions, managed tool pool, purchase, promotion, or fallback. |
| Remote model catalog | Cannot activate or mutate routes. The qualified catalog is release-pinned and cannot introduce provider subagents, fallback, or auxiliary calls. |
| Risk | Deterministic policy derives risk; worker-supplied risk can only be an untrusted observation. |
| Merge | Human-controlled landing until a later accepted decision changes the policy. |

## 4. Non-negotiable invariants

1. Only `governed_execution` chooses and commits a legal canonical run state.
2. Only the nonreplaceable application policy-enforcement point authorizes an
   effect.
3. Every target-mode effect crosses `CapabilityBus`; no special tool or agent
   path bypasses it.
4. Transitional inherited harnesses are described honestly as activity-boundary
   plus OS-sandbox mediated until their real tool paths pass the bypass matrix.
5. One transaction commits the run version/current row, ordered journal record,
   consumed permit or decision, and outbound effect intent.
6. Kanban, dashboards, Hermes session state, and external systems are projections
   or adapter state, never alternative completion authorities.
7. Every authority and evidence record binds to the exact project, work item,
   run, activity, workspace, base commit, candidate commit, packet digest,
   workflow version, policy snapshot, module profile, and aggregate version
   required by its contract.
8. A maker cannot approve its own subject.
9. A human waiver remains a waiver and never becomes machine `PASS`.
10. Unknown action, role, capability, route, schema, state, or dependency is
    denied by default.
11. A module cannot qualify, grant, activate, promote, quarantine, or retire
    itself.
12. A route cannot establish its own identity, capability profile, independence,
    or qualification.
13. The reducer performs no I/O and reads no wall clock, randomness, environment,
    process global, database, filesystem, network, provider, or Hermes state.
14. The same workflow/interpreter versions and ordered recorded inputs replay to
    the same state and commands.
## 8. Canonical consistency boundary

### 8.1 The Governed Execution Authority Cell

`governed_execution` is one bounded consistency cell with four cohesive
subdomains:

1. run/workflow lifecycle;
2. exact authorization and gate-decision snapshots;
3. permits and human-decision consumption; and
4. activity/effect intent, result, retry, and reconciliation.

These responsibilities are separate domain files and types, but they participate
in one invariant and one SQLite transaction. They are not persisted as four
independent authorities.

Policy definitions, evidence artifacts, checker qualification, and module/route
catalogs are owned by other contexts. Before a transition, their immutable
decisions and digests are copied or bound into the authority transaction. A
later change cannot rewrite the historical snapshot, while every new effect
still requires current-policy re-evaluation.

`work_management` owns the separate `WorkItem` aggregate and Core-SDLC
transition history. It does not join the run transaction. It consumes
`governed_execution` integration events and submits idempotent commands through
public APIs; failure is retried/reconciled and never simulated as
cross-context atomicity.

`policy` owns the authenticated, append-only `HumanDecisionRecord`.
`governed_execution` owns the exact-subject `ConsumableAuthorityGrant` created
from an eligible decision snapshot. The policy table is never mutated by the
run transaction; grant issuance/consumption and permit issuance/consumption
inside the authority cell are compare-and-swap protected.

### 8.2 Atomic authority transaction


## 9. Complete bounded-context ownership map

### 9.1 Nonreplaceable authority contexts

| Context | Owns | Public API | Persistence authority |
|---|---|---|---|
| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
| `policy` | Roles, authorization-eligibility rules, risk-lane derivation, policy packages, activation, authorization snapshots, waivers and authenticated human-decision records | Authorization request/decision, active-policy and human-decision snapshots | Policy definitions and append-only decision history; never issues or consumes execution grants/permits |
| `assurance` | Claims, evidence envelopes, qualified checker results, exact-subject evidence snapshots, and `GateEvaluation` | Evidence ingestion/query, checker result, snapshot and gate-evaluation APIs | Sole evidence/gate-evaluation record owner; does not own review observations, qualify components, bind a run gate, or commit run state |
| `module_governance` | Module catalog, descriptors, capability vocabulary, grants, compatibility, activation lifecycle | Module/grant/profile snapshots | Module and grant authority |
| `identity_access` | Human/service identities, authentication, sessions, nonces, remote decision authentication, data classification, destination facts, secret references | Principal/session/secret-handle and destination-fact APIs | Identity and access authority; policy decides and the egress adapter enforces |

### 9.2 Product and development contexts

| Context | Owns | Attachment points |
|---|---|---|
| `product_definition` | Actors, problems/needs, hypotheses, product capabilities, requirements, acceptance examples, outcome measures, validation decisions, `CapabilityStatus` | Discovery/user research, product decisions, work intake, outcome review |
| `work_management` | Projects, canonical `WorkItemStatus`, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections | Core-SDLC transition API, GitHub intake, product/requirement links, governed-run/evidence integration |
| `service_management` | Service catalog, service/capability ownership, supported versions, SLIs/SLOs/error budgets, support/escalation, maintenance and retirement triggers | Operations evidence, release catalog, product capability lifecycle |
| `configuration_management` | Configuration-item registry, content-addressed baselines, status accounting, bidirectional traceability graph, functional/physical configuration audits | Product requirements, source/build/test/docs, release manifests, assurance evidence |
| `supplier_governance` | Supplier/dependency adoption and reuse decisions, shared responsibility, version/support/vulnerability monitoring, concentration/exit plans | Packages, toolchains, providers, APIs, extensions, hosted services, Hermes upstream |
| `resource_governance` | Local capacity, hierarchical cost/token/tool/output/network budgets, parent/child reservations, quotas, transitive usage attribution and provider-limit facts | Policy, routing, scheduling, agent runs, operations; never commercial billing |
| `interaction_history` | User conversation/thread/message identity, continuity, search lifecycle, classification, retention, export and deletion | Delivery channels, context compilation, legacy session import |
| `process_assurance` | SDLC policy conformance, tailoring profiles, human-role competence, process audits/nonconformance/corrective action, process improvement evidence, fleet experiment and calibration records | Core SDLC, work records, metrics, training/qualification and measurement-harness evidence |
| `workspace` | Repository identity, worktree plans, branch/head validation, landing and cleanup | Git adapter, sandbox mounts |
| `instruction_registry` | Atomic versioned instructions, precedence, applicability, checker bindings | Policy and packet compilation |
| `context_compilation` | Resolved source manifests, packet compilation, context budget, conflicts, provenance | Deterministic and recorded stochastic retrieval |
| `analytical_review` | Review specifications, requests, attempts, observations, verdicts, parsing and independence evaluations | Native and tool-bearing review transports; publishes immutable review references to assurance |
| `routing` | Provider/model/transport/runtime/auth identities, one-route assignment locks, health, failure and governed-redispatch facts | Official runtime and provider adapters; no fallback chain |
| `qualification` | Checker, module, route, and isolation-profile qualification | Frozen fixtures, canaries, holdouts |
| `effectiveness` | Whole-workflow paired evaluation, causal ablations, owner-facing scorecards | Evaluation runners and artifacts |
| `agent_collaboration` | Typed worker assignments/offers, atomic claims, fenced leases, heartbeats/liveness, mailboxes, Ranex-owned dispatch graphs and fan-out/join, role separation, worker attempts, results and handoffs | Official leaf runtime adapters; workers cannot delegate or coordinate and the context never owns `RunStatus`, work state, gate, permit, effect, merge, or release |
| `repository_intelligence` | Source graph/index, language coverage, freshness, unsupported-analysis states | Atlas/tree-sitter or simpler index strategies |
| `knowledge` | Skills, project memory, learned records, quarantine, sanitization, transfer approvals | Packet sources and explicitly scoped worker reads |
| `scheduling` | Schedules, authenticated triggers, catch-up rules, trigger lifecycle | Cron, webhooks, external timers |
| `delivery` | Channel-neutral messages, commands, decision challenges, rendering, delivery receipts | CLI, TUI, web, phone, GitHub adapters |
| `artifact_management` | Content-addressed blobs, classification, access, retention, legal hold, expiry, purge | Filesystem/object-store adapters |

### 9.3 Operations, evolution, and boundary contexts

| Context | Owns | Attachment points |
|---|---|---|
| `operations` | Observed health, alerts, `IncidentStatus`, response/recovery evidence, reconciliation scheduling and operator runbooks | Telemetry, delivery, service objectives, external-system probes |
| `backup_restore` | Backup sets, encryption, RPO/RTO policy, restore drills, reconciliation | SQLite, artifacts, configuration, remote stores |
| `release_management` | Build manifest, release profile, install/update/rollback, package/SBOM verification | Installer and updater adapters |
| `upstream_sync` | Upstream baseline, diff classification, anti-recontamination gates, selective porting, sync evidence | Git worktrees and upstream remote |
| `migration` | Schema ordering, upcasters, module migrations, legacy readers, verification, rollback/tombstones | Persistence and compatibility readers |
| `extension_host` | Lower-trust extension protocol, capability grants, lifecycle, quarantine | Out-of-process RPC/MCP-like bridge |
| `compatibility` boundary package | Hermes anti-corruption facade, legacy state/CLI/tool-name translation, contained non-inference characterization; no canonical lifecycle state, provider route, credential, network, or worker dispatch | Frozen inherited Hermes subset; `service_management` owns the legacy-surface compatibility lifecycle |
| `provenance_compliance` | File classification, licenses, notices, de-commercialization denylist, SBOM policy | CI, release, upstream sync |

## 10. Full capability attachment matrix

Every target capability must resolve all columns before implementation.

| Capability zone | Owner | Effect/adapter family | Lifecycle owner | Canonical output |
|---|---|---|---|---|
| Workflow and run control | `governed_execution` | workflow runtime | `governed_execution` | Run events and state |
| Policy and risk | `policy` | built-in/OPA PDP | `policy` | Authorization decision snapshot |
| Human decisions | `policy` + `identity_access` | CLI/web/phone/GitHub challenge | `policy` | Authenticated exact-subject decision |
| Evidence and checks | `assurance` | deterministic/model/human checker modules | checker module state in `module_governance`; qualification evidence in `qualification` | Evidence/checker result |
| Permits and effects | `governed_execution` | capability bus/outbox | `governed_execution` | Consumed permit + effect intent/result |
| Modules and capabilities | `module_governance` | composition catalog | `module_governance` | Qualified module profile |
| Routes/providers | `routing` | release-pinned official runtime or API/BYOK adapters | route state in `routing`; qualification evidence in `qualification` | One explicit no-fallback route lock and attempt |
| Product discovery/requirements/outcomes | `product_definition` | research, decision and analytics adapters | `product_definition` | Versioned need, requirement, measure and validation decision |
| Core-SDLC projects/work/traceability | `work_management` | transition, portfolio, GitHub and projection adapters | `work_management` | Canonical work item, requirements/outcome links, and projections |
| Services/SLOs/support/lifecycle | `service_management` | service catalog and operational projections | `service_management` | Service objective and capability/support state |
| Configuration/baselines/traceability | `configuration_management` | repository/build/test/release scanners | `configuration_management` | Audited baseline and trace graph |
| Suppliers/dependencies | `supplier_governance` | package/provider/upstream monitors | `supplier_governance` | Adoption/monitoring/exit decision |
| Resource budgets/usage | `resource_governance` | provider/tool/host usage meters | `resource_governance` | Reservation, quota and attributed usage |
[0m
[0m$ [0msed -n '1155,1230p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
Every stateful context also has a narrowly typed local `unit_of_work.py` and
`integration_event_outbox.py` port even when omitted from the compact table.
Their adapters atomically persist that context's aggregate and integration
events; they do not share the governed-execution effect outbox.

### 12.2 Web dashboard structure

The web dashboard is a presentation application, not another control plane:

```text
apps/web-dashboard/src/
├── app/
├── features/
│   ├── runs/
│   ├── work/
│   ├── evidence/
│   ├── decisions/
│   ├── modules/
│   ├── routes/
│   ├── operations/
│   └── recovery/
├── generated-contracts/
├── transport/
└── security/
```

It imports generated TypeScript contracts, calls authenticated application
APIs, and renders returned authority state. It contains no transition table,
gate rule, permit rule, risk rule, or provider credential.

## 13. Enforced source dependency rules

1. `foundation` imports the Python standard library only and has a strict size
   and consumer review budget.
2. Any `domain/` imports only its own context domain and `foundation`.
3. A context crosses another context only through `<other>.api`.
4. Application code imports ports, never adapter implementations.
5. Adapters implement ports and may import public APIs.
6. No adapter imports another adapter; shared host mechanics become a narrowly
   named port or platform adapter.
7. Only `bootstrap/composition.py` constructs concrete implementations, reads
   runtime environment configuration, and binds factories.
8. Nonreplaceable contexts never import `modules`, `adapters`,
   `compatibility`, or `legacy`.
9. First-party modules submit commands, proposals, and evidence; they cannot
   write authority tables.
10. `compatibility` may call Ranex public APIs; no Ranex context imports
    compatibility.
11. Only the Hermes compatibility adapter may import the inherited Hermes root
    during migration.
12. External extensions cannot import the host package; they communicate
    through the versioned process protocol.
13. The declared module graph is acyclic and is checked against actual imports.
14. `ExecutionContext` is forbidden as a domain-method parameter. Domain methods
    receive the smallest immutable subject view.
15. `scripts/` contains thin authenticated clients of public application APIs;
    no script imports repositories/adapters or performs an unrecorded
    install/update/migration/restore effect.
16. Only `compatibility.hermes_legacy` may import inherited Hermes roots during
    the strangler; no authority, domain, or other application package may.
17. `governed_execution.application.process_manager` is orchestration-only. It
    may call registered public application services and ports, but contains no
    policy, gate, permit, transition, risk, evidence-eligibility, or product
    business rule; those remain in their named domain/application owners.
18. Ports exist only below
    `src/ranex/<context>/application/ports/`; a sibling `<context>/ports/`
    package is invalid.
19. Cross-context imports target the other context's public `api` package.
    Imports of another context's `domain`, `application`, `ports`, `adapters`,
    or private modules fail even if Python can resolve them.
20. Importing a module performs no network/database/filesystem mutation,
    process spawn, migration, discovery registration, environment-dependent
    decision, or other effect.
21. A context-exclusive implementation lives below
    `src/ranex/<context>/adapters/<technology>/`. A central
    `src/ranex/adapters/<boundary>/<technology>/` implementation is valid only
[0m
[0m$ [0mgrep -n "deterministic choice\|fan-out\|fan out\|durable wait\|compensation\|dynamic graph\|workflow semantics\|extension point" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -40
228:| AI-worker fleet | Ranex control services alone orchestrate deterministic bounded fan-out/join; every model/harness is a leaf worker; each assignment receives a task-minimal proper subset of its role ceiling; writes are isolated and landing is human-controlled. |
353:      COLLAB["Ranex worker dispatch · leases · fan-out/join"]
522:| `agent_collaboration` | Typed worker assignments/offers, atomic claims, fenced leases, heartbeats/liveness, mailboxes, Ranex-owned dispatch graphs and fan-out/join, role separation, worker attempts, results and handoffs | Official leaf runtime adapters; workers cannot delegate or coordinate and the context never owns `RunStatus`, work state, gate, permit, effect, merge, or release |
1243:    dispatch, cancel, fan out, or join worker assignments. No runtime adapter or
1295:- read-only work may fan out, but writing work uses validated isolated
1297:- only Ranex control services create deterministic bounded fan-out/join; a
1671:    cancellation_semantics: "Any nonterminal state may cancel with authenticated authority and compensation disposition"
2787:| `EVENT-RUNCANCELLED` / `RunCancelled` | `governed_execution` / `run_lifecycle_service`; `work_management`, `operations` | `Run`; authenticated cancellation accepted from cancellable state | `run_id:Id<Run>`, `from_status:Enum<RunStatus>`, `cancellation_decision_ref:Ref<HumanDecisionRecord>`, `reason_code:String`, `compensation_refs:Set<ArtifactRef>[0..N]` (empty only when the workflow's exact compensation contract declares none applicable) |
3088:- deterministic choice;
3095:- compensation request;
3099:Parallel/fan-out, map, dynamic graph mutation, and richer authoring remain mapped
3100:extension points under `governed_execution.domain.workflow`, but cannot gain
3101:authority until their ordering, cancellation, retry, compensation, and replay
3113:have acceptable terminal facts; optional effects and compensation are declared
3127:- compensation/reconciliation contract.
3228:idempotency/retry/timeout/compensation contract
3784:Its complete machine obligations are grouped without compensation:
3841:- governed-execution responsibility/fan-in/fan-out/interaction/change/
3847:- no compensation across any of them: `ARCH9-NONCOMP-001`.
3850:`governed_execution` fan-out/fan-in of 10/3. Those are paper definitions, not
4112:  noncompensation rules;
[0m
[0m$ [0mgrep -n "OUTCOME_UNKNOWN" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -30; echo ===; grep -n "WorkflowDefinition\|workflow definition" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -40
273:16. `OUTCOME_UNKNOWN` is a first-class result and must enter reconciliation.
1474:| `ActivityStatus` | `REQUESTED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
1480:| `EffectStatus` | `INTENDED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`, `OUTCOME_UNKNOWN` |
1953:    values: ["REQUESTED", "DISPATCHED", "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_PERMANENT", "TIMED_OUT", "CANCELLED", "DENIED", "OUTCOME_UNKNOWN"]
1966:    recovery_semantics: "OUTCOME_UNKNOWN reaches known state only through qualified reconciliation"
1967:    transitions: ["REQUESTED>DISPATCHED@AUTHORIZATION_ASSIGNMENT_LEASE_AND_BUDGET_CURRENT", "REQUESTED>DENIED@AUTHORIZATION_TERMINALLY_DENIED", "REQUESTED>CANCELLED@AUTHORIZED_ACTIVITY_CANCELLATION", "REQUESTED>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED", "DISPATCHED>SUCCEEDED@TYPED_RESULT_AND_REQUIRED_EFFECTS_SUCCEEDED", "DISPATCHED>FAILED_RETRYABLE@CLASSIFIED_RETRYABLE_FAILURE", "DISPATCHED>FAILED_PERMANENT@CLASSIFIED_TERMINAL_FAILURE", "DISPATCHED>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED_AND_EFFECTS_RECONCILED", "DISPATCHED>CANCELLED@AUTHORIZED_CANCELLATION_AND_EFFECTS_RECONCILED", "DISPATCHED>DENIED@PROVIDER_OR_POLICY_TERMINAL_DENIAL_PROVEN", "DISPATCHED>OUTCOME_UNKNOWN@RESULT_OR_EFFECT_OUTCOME_AMBIGUOUS", "FAILED_RETRYABLE>DISPATCHED@RETRY_POLICY_BUDGET_AND_DEADLINE_ALLOW", "FAILED_RETRYABLE>FAILED_PERMANENT@RETRY_BUDGET_EXHAUSTED", "FAILED_RETRYABLE>CANCELLED@AUTHORIZED_ACTIVITY_CANCELLATION_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "FAILED_RETRYABLE>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "FAILED_RETRYABLE>DENIED@RETRY_AUTHORIZATION_OR_POLICY_REVOKED_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "OUTCOME_UNKNOWN>SUCCEEDED@QUALIFIED_RECONCILIATION_PROVES_SUCCESS", "OUTCOME_UNKNOWN>FAILED_RETRYABLE@QUALIFIED_RECONCILIATION_PROVES_RETRYABLE_FAILURE", "OUTCOME_UNKNOWN>FAILED_PERMANENT@QUALIFIED_RECONCILIATION_PROVES_TERMINAL_FAILURE", "OUTCOME_UNKNOWN>DENIED@QUALIFIED_RECONCILIATION_PROVES_DENIAL"]
2065:    values: ["INTENDED", "DISPATCHED", "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_PERMANENT", "DENIED", "OUTCOME_UNKNOWN"]
2075:    expiry_semantics: "Exhaustion converts known retryable failure to FAILED_PERMANENT; ambiguity stays OUTCOME_UNKNOWN"
2078:    recovery_semantics: "OUTCOME_UNKNOWN changes only when qualified reconciliation proves a listed result"
2079:    transitions: ["INTENDED>DISPATCHED@COMMITTED_INTENT_CURRENT_PERMIT_AND_ADAPTER_LEASE", "INTENDED>DENIED@PRE_DISPATCH_POLICY_OR_DESTINATION_DENIAL", "INTENDED>FAILED_PERMANENT@INTENT_OR_ADAPTER_VALIDATION_TERMINALLY_FAILED", "DISPATCHED>SUCCEEDED@PROVIDER_RECEIPT_PROVES_SUCCESS", "DISPATCHED>FAILED_RETRYABLE@PROVIDER_RECEIPT_PROVES_RETRYABLE_FAILURE", "DISPATCHED>FAILED_PERMANENT@PROVIDER_RECEIPT_PROVES_TERMINAL_FAILURE", "DISPATCHED>DENIED@PROVIDER_RECEIPT_PROVES_DENIAL", "DISPATCHED>OUTCOME_UNKNOWN@ACKNOWLEDGEMENT_LOST_OR_AMBIGUOUS", "FAILED_RETRYABLE>DISPATCHED@RETRY_POLICY_BUDGET_AND_DEADLINE_ALLOW", "FAILED_RETRYABLE>FAILED_PERMANENT@RETRY_BUDGET_OR_DEADLINE_EXHAUSTED", "FAILED_RETRYABLE>DENIED@POLICY_OR_DESTINATION_DENIES_RETRY", "OUTCOME_UNKNOWN>SUCCEEDED@QUALIFIED_RECONCILIATION_PROVES_SUCCESS", "OUTCOME_UNKNOWN>FAILED_RETRYABLE@QUALIFIED_RECONCILIATION_PROVES_RETRYABLE_FAILURE", "OUTCOME_UNKNOWN>FAILED_PERMANENT@QUALIFIED_RECONCILIATION_PROVES_TERMINAL_FAILURE", "OUTCOME_UNKNOWN>DENIED@QUALIFIED_RECONCILIATION_PROVES_DENIAL"]
2711:| `ActivityResolution` | reuse `states.json#ActivityStatus@1.0.0`; `governed_execution` | restricted to `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
2784:| `EVENT-EFFECTRECONCILED` / `EffectReconciled` | `governed_execution` / `reconciliation_service`; `operations`, `assurance` | `Effect`; qualified reconciler proves disposition of prior unknown outcome | `effect_id:Id<Effect>`, `reconciliation_ref:Ref<ReconciliationRecord>`, `prior_status:Enum<EffectStatus>=OUTCOME_UNKNOWN`, `proven_outcome:Enum<EffectStatus>` restricted by `EffectKnownOutcome`, `reconciled_at:Utc` |
2899:        allowed_edges: ["REQUESTED>DENIED@AUTHORIZATION_TERMINALLY_DENIED", "REQUESTED>CANCELLED@AUTHORIZED_ACTIVITY_CANCELLATION", "REQUESTED>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED", "DISPATCHED>SUCCEEDED@TYPED_RESULT_AND_REQUIRED_EFFECTS_SUCCEEDED", "DISPATCHED>FAILED_RETRYABLE@CLASSIFIED_RETRYABLE_FAILURE", "DISPATCHED>FAILED_PERMANENT@CLASSIFIED_TERMINAL_FAILURE", "DISPATCHED>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED_AND_EFFECTS_RECONCILED", "DISPATCHED>CANCELLED@AUTHORIZED_CANCELLATION_AND_EFFECTS_RECONCILED", "DISPATCHED>DENIED@PROVIDER_OR_POLICY_TERMINAL_DENIAL_PROVEN", "DISPATCHED>OUTCOME_UNKNOWN@RESULT_OR_EFFECT_OUTCOME_AMBIGUOUS", "FAILED_RETRYABLE>FAILED_PERMANENT@RETRY_BUDGET_EXHAUSTED", "FAILED_RETRYABLE>CANCELLED@AUTHORIZED_ACTIVITY_CANCELLATION_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "FAILED_RETRYABLE>TIMED_OUT@ABSOLUTE_DEADLINE_ELAPSED_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "FAILED_RETRYABLE>DENIED@RETRY_AUTHORIZATION_OR_POLICY_REVOKED_AND_NO_DISPATCHED_EFFECT_OR_EFFECTS_RECONCILED", "OUTCOME_UNKNOWN>SUCCEEDED@QUALIFIED_RECONCILIATION_PROVES_SUCCESS", "OUTCOME_UNKNOWN>FAILED_RETRYABLE@QUALIFIED_RECONCILIATION_PROVES_RETRYABLE_FAILURE", "OUTCOME_UNKNOWN>FAILED_PERMANENT@QUALIFIED_RECONCILIATION_PROVES_TERMINAL_FAILURE", "OUTCOME_UNKNOWN>DENIED@QUALIFIED_RECONCILIATION_PROVES_DENIAL"]
2942:        allowed_edges: ["DISPATCHED>OUTCOME_UNKNOWN@ACKNOWLEDGEMENT_LOST_OR_AMBIGUOUS"]
2949:        allowed_edges: ["OUTCOME_UNKNOWN>SUCCEEDED@QUALIFIED_RECONCILIATION_PROVES_SUCCESS", "OUTCOME_UNKNOWN>FAILED_RETRYABLE@QUALIFIED_RECONCILIATION_PROVES_RETRYABLE_FAILURE", "OUTCOME_UNKNOWN>FAILED_PERMANENT@QUALIFIED_RECONCILIATION_PROVES_TERMINAL_FAILURE", "OUTCOME_UNKNOWN>DENIED@QUALIFIED_RECONCILIATION_PROVES_DENIAL"]
3135:5. marks success, classified failure, denial, or `OUTCOME_UNKNOWN`;
3142:discovered effect disposition and moves `EffectStatus` from `OUTCOME_UNKNOWN`
===
1442:workflow definition + interpreter version
1494:`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
3114:in the workflow definition.
[0m
[0m$ [0msed -n '3075,3160p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
compatibility/replay contracts, canonical row digest, and source-file digest.
Runtime emission, delivery, consumer handling, upcast, and replay evidence all
remain `NOT_ASSESSED`. Product, service, configuration, supplier, resource,
interaction, process, incident, release, migration, and upstream-sync contexts
may add events only through the same catalog decision; generic
`StatusChanged`, `Updated`, untyped payloads, or name-only additions are
blocking.

## 18. Workflow semantics

The target interpreter supports:

- sequence;
- deterministic choice;
- activity request/result;
- evidence gate;
- durable signal wait;
- durable timer;
- classified retry;
- cancellation;
- compensation request;
- reconciliation wait; and
- terminal success/failure.

Parallel/fan-out, map, dynamic graph mutation, and richer authoring remain mapped
extension points under `governed_execution.domain.workflow`, but cannot gain
authority until their ordering, cancellation, retry, compensation, and replay
semantics are specified and tested.

Workflow definitions are immutable release- or project-approved data. Models may
draft definitions, never activate them.

## 19. Effects, idempotency, and reconciliation

An `Activity` is one logical unit of workflow work. It may be pure, invoke a
worker, or request `0..N` external `Effect` records. Each effect has its own
identity, destination, authority, idempotency/retry policy, result, and
reconciliation history. An activity resolves only when its required effects
have acceptable terminal facts; optional effects and compensation are declared
in the workflow definition.

Every `ActivityRequest` declares:

- exact subject;
- activity/effect type;
- canonical argument digest;
- required capabilities and declared effects;
- route/module/isolation profile;
- one absolute deadline and remaining budgets;
- idempotency key;
- timeout and retry policy;
- expected result/evidence schemas; and
- compensation/reconciliation contract.

The outbox relay:

1. leases a committed intent;
2. dispatches with the same logical idempotency key;
3. validates the typed result;
4. records provider/external receipts as artifacts;
5. marks success, classified failure, denial, or `OUTCOME_UNKNOWN`;
6. retries only when policy permits;
7. sends ambiguous outcomes to an adapter-specific reconciler; and
8. records the reconciled fact before the run advances.

Reconciliation is an orthogonal record, not a terminal effect outcome. It
transitions `PENDING -> RUNNING -> RESOLVED | UNRESOLVED`; `RESOLVED` stores the
discovered effect disposition and moves `EffectStatus` from `OUTCOME_UNKNOWN`
to the proven `SUCCEEDED`, `FAILED_*`, or `DENIED` value. History never erases
that the original acknowledgement was unknown.

GitHub, Git, messaging, provider, filesystem, and database effects each define
how to query or prove outcome after a lost acknowledgement. “Probably happened”
is never a terminal state.

## 20. Evidence, review, gates, and human authority

The data flow is deliberately one-way:

```text
raw artifact
  -> EvidenceEnvelope
  -> immutable ReviewObservation reference or qualified CheckerResult
  -> validated exact-subject evidence snapshot
  -> GateEvaluation
  -> optional authenticated HumanDecision
[0m
[0m$ [0msed -n '1430,1510p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
The minimum exact-subject tuple is:

```text
project_id
work_item_id
run_id
activity/effect identity when applicable
workspace_id
repository identity
base commit
candidate commit or artifact digest
task-packet digest
workflow definition + interpreter version
policy/rule activation manifest + decision digest
module profile + grant digest
schema registry version
expected run aggregate version
```

## 16. Canonical state axes

One overloaded “office stage” is prohibited.

| Axis | Canonical values |
|---|---|
| `WorkItemStatus` | `FUNNEL`, `TRIAGE`, `DISCOVERY`, `DEFINITION`, `DESIGN`, `READY`, `IN_PROGRESS`, `VERIFICATION`, `RELEASE_READY`, `RELEASING`, `OPERATING`, `OUTCOME_REVIEW`, `CLOSED`, `BLOCKED`, `CANCELLED`, `ROLLED_BACK` |
| `WorkClass` | `PRODUCT`, `DEFECT`, `RELIABILITY`, `SECURITY_PRIVACY`, `ARCHITECTURE_PLATFORM`, `COMPLIANCE_PROVENANCE`, `UPSTREAM_SYNC`, `MAINTENANCE`, `RETIREMENT`, `INCIDENT_RESPONSE` |
| `RiskLane` | `STANDARD`, `ENHANCED`, `CRITICAL`, `EMERGENCY` |
| `RunStatus` | `PROPOSED`, `READY`, `RUNNING`, `WAITING`, `BLOCKED`, `SUCCEEDED`, `FAILED`, `CANCELLED` |
| `AssignmentStatus` | `PENDING`, `OFFERED`, `CLAIMED`, `RUNNING`, `HANDOFF_READY`, `COMPLETED`, `FAILED`, `EXPIRED`, `CANCELLED`; owned by `agent_collaboration` and never a work/run completion alias |
| `DispatchOfferStatus` | `OPEN`, `CLAIMED`, `EXPIRED`, `REVOKED`; owned by `agent_collaboration`; invitation currency only |
| `LeaseStatus` | `ACTIVE`, `RELEASED`, `EXPIRED`, `REVOKED`; owned by `agent_collaboration` with a monotonically increasing fencing epoch |
| `MailboxDeliveryStatus` | `QUEUED`, `DELIVERED`, `ACKNOWLEDGED`, `DEAD_LETTERED`, `EXPIRED`; coordination delivery only, never authority |
| `ReservationStatus` | `PENDING`, `ACTIVE`, `EXHAUSTED`, `RELEASED`, `EXPIRED`, `REVOKED`, `SETTLED`; owned by `resource_governance`; never work completion or authority beyond its ancestor tree |
| `IntakeStatus` | `PROPOSED`, `ACCEPTED`, `REJECTED`, `DUPLICATE`, `WITHDRAWN`; owned by `work_management`; it does not alias `WorkItemStatus` |
| `PacketStatus` | `DRAFT`, `SEALED`, `SUPERSEDED`, `INVALIDATED`; owned by each packet producer under the shared schema; only `SEALED` is dispatch/review eligible |
| `FleetExperimentStatus` | `DRAFT`, `REGISTERED`, `RUNNING`, `COMPLETED`, `STOPPED`, `INVALIDATED`; owned by `process_assurance`; completion cannot activate policy |
| `CapabilityAssessmentStatus` | `NOT_ASSESSED`, `IN_PROGRESS`, `COMPLETE`, `SUPERSEDED`; owned by `process_assurance` and shared by immutable control assessments and domain projections; neither acts as a gate |
| `READINESS-STATE-1.0` | `NOT_ASSESSED`, `IMPLEMENTATION_START_EVALUATING`, `IMPLEMENTATION_START_BLOCKED`, `IMPLEMENTATION_START_READY`, `PRODUCTION_EVALUATING`, `PRODUCTION_BLOCKED`, `PRODUCTION_READY`; owned by `process_assurance`; definition-only and governed by ADR-0012 |
| `RuleEnforcementClass` | `ADVISORY`, `REQUIRED`, `BLOCKING`, `EXPERIMENTAL`; `STATE-RULE-ENFORCEMENT-CLASS-1.0`, owned by `policy`; separate `DETERMINISTIC` or `HUMAN_DECISION_REQUIRED` resolution metadata prevents human authority from being overloaded as severity |
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
| `InstructionStatus` | `DRAFT`, `ACTIVE`, `DEPRECATED`, `RETIRED` |
| `ArtifactStatus` | `INGESTED`, `QUARANTINED`, `AVAILABLE`, `EXPIRED`, `PURGED`; legal hold is an orthogonal append-only fact, never an availability state |
| `MigrationStatus` | `PLANNED`, `TESTED`, `APPLIED`, `VERIFIED`, `ROLLED_BACK`, `FAILED` |
| `SyncCandidateStatus` | `OBSERVED`, `FETCHED`, `PINNED`, `CLASSIFIED`, `DISPOSITIONED`, `PORTING`, `PORT_CANDIDATE`, `VERIFIED`, `RELEASED`, `BASELINE_RECORDED`, `REJECTED`, `DEFERRED`, `BLOCKED`, `ROLLED_BACK` |
| `SyncDisposition` | `REJECT`, `DEFER`, `PORT`; `STATE-SYNC-DISPOSITION-1.0`, owned by `upstream_sync`; a decision value recorded at `DISPOSITIONED`, never an overloaded status |
| `UpdateStatus` | `CHECKED`, `DOWNLOADED`, `VERIFIED`, `SNAPSHOTTED`, `STAGED`, `MIGRATED`, `ACTIVATED`, `HEALTH_VERIFIED`, `COMPLETED`, `ROLLED_BACK`, `RECOVERY_VERIFIED` |
| `CutoverStatus` | `BOOTSTRAP`, `LEGACY_BASELINE`, `TRANSITIONAL_DUAL_RUN`, `TARGET_SHADOW`, `TARGET_LIMITED`, `TARGET_DEFAULT`, `LEGACY_FROZEN`, `LEGACY_REMOVED`, `ABANDONED` |

`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
not another run-status enum. A waiver is a `HumanDecision`, not a gate outcome.

`RunStatus` has one legal transition graph:

```text
PROPOSED -> READY | CANCELLED
READY -> RUNNING | BLOCKED | CANCELLED
RUNNING -> WAITING | BLOCKED | SUCCEEDED | FAILED | CANCELLED
WAITING -> RUNNING | BLOCKED | FAILED | CANCELLED
BLOCKED -> <recorded blocked_from_status> | FAILED | CANCELLED
```

Entering `BLOCKED` records the prior nonterminal state, reason, owner, time,
blocking evidence/dependency, invalidated inputs, and review deadline. Resume
is permitted only to that recorded state after fresh policy/evidence confirms
the blocker is resolved; it is not a generic jump. `SUCCEEDED`, `FAILED`, and
[0m
[0m$ [0mfor f in src/ranex/governed_execution/domain/execution.py src/ranex/governed_execution/domain/status.py src/ranex/governed_execution/domain/events.py; do echo "=== $f"; cat -n $f; done
=== src/ranex/governed_execution/domain/execution.py
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	from dataclasses import dataclass, replace
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.events import (
     8	    ExecutionBlocked,
     9	    ExecutionCancelled,
    10	    ExecutionCreated,
    11	    ExecutionEvent,
    12	    ExecutionFailed,
    13	    ExecutionMarkedReady,
    14	    ExecutionResumed,
    15	    ExecutionStarted,
    16	    ExecutionSucceeded,
    17	    ExecutionUnblocked,
    18	    ExecutionWaited,
    19	)
    20	from ranex.governed_execution.domain.status import ExecutionStatus
    21	
    22	
    23	class InvalidExecutionTransition(ValueError):
    24	    """An event cannot evolve the supplied execution state."""
    25	
    26	
    27	LEGAL_STATUS_TRANSITIONS = frozenset(
    28	    {
    29	        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
    30	        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
    31	        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
    32	        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
    33	        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
    34	        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
    35	        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
    36	        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
    37	        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
    38	        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    39	        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
    40	        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
    41	        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
    42	        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
    43	        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
    44	        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
    45	        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
    46	        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
    47	        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    48	    }
    49	)
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class Execution:
    54	    execution_id: Identity
    55	    work_item_id: Identity
    56	    created_by_principal_id: Identity
    57	    workflow_request_ref: str
    58	    status: ExecutionStatus
    59	    version: int
    60	    last_event_id: Identity
    61	    updated_at: str
    62	    blocked_from_status: ExecutionStatus | None = None
    63	
    64	
    65	def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    66	    return InvalidExecutionTransition(
    67	        f"{state.status.value} cannot apply {type(event).__name__}"
    68	    )
    69	
    70	
    71	def _advance(
    72	    state: Execution,
    73	    event: ExecutionEvent,
    74	    target_status: ExecutionStatus,
    75	    *,
    76	    blocked_from_status: ExecutionStatus | None = None,
    77	) -> Execution:
    78	    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
    79	        raise _invalid(state, event)
    80	    return replace(
    81	        state,
    82	        status=target_status,
    83	        version=state.version + 1,
    84	        last_event_id=event.event_id,
    85	        updated_at=event.occurred_at,
    86	        blocked_from_status=blocked_from_status,
    87	    )
    88	
    89	
    90	def _require_source(
    91	    state: Execution,
    92	    event: ExecutionEvent,
    93	    allowed: frozenset[ExecutionStatus],
    94	) -> None:
    95	    if state.status not in allowed:
    96	        raise _invalid(state, event)
    97	
    98	
    99	def reduce_execution(
   100	    current: Execution | None,
   101	    event: ExecutionEvent,
   102	) -> Execution:
   103	    """Purely compute the next immutable Execution from one event."""
   104	    if current is None:
   105	        if not isinstance(event, ExecutionCreated):
   106	            raise InvalidExecutionTransition(
   107	                f"no execution can apply {type(event).__name__}"
   108	            )
   109	        if event.expected_version != 0:
   110	            raise InvalidExecutionTransition(
   111	                "ExecutionCreated expected version must be zero"
   112	            )
   113	        return Execution(
   114	            execution_id=event.execution_id,
   115	            work_item_id=event.work_item_id,
   116	            created_by_principal_id=event.created_by_principal_id,
   117	            workflow_request_ref=event.workflow_request_ref,
   118	            status=ExecutionStatus.PROPOSED,
   119	            version=1,
   120	            last_event_id=event.event_id,
   121	            updated_at=event.occurred_at,
   122	        )
   123	
   124	    if isinstance(event, ExecutionCreated):
   125	        raise _invalid(current, event)
   126	    if event.execution_id != current.execution_id:
   127	        raise InvalidExecutionTransition("event targets a different execution")
   128	    if event.expected_version != current.version:
   129	        raise InvalidExecutionTransition(
   130	            "event expected version does not match execution version"
   131	        )
   132	    if event.event_id == current.last_event_id:
   133	        raise InvalidExecutionTransition("last event cannot be applied twice")
   134	
   135	    if isinstance(event, ExecutionMarkedReady):
   136	        _require_source(
   137	            current,
   138	            event,
   139	            frozenset({ExecutionStatus.PROPOSED}),
   140	        )
   141	        return _advance(current, event, ExecutionStatus.READY)
   142	    if isinstance(event, ExecutionStarted):
   143	        _require_source(
   144	            current,
   145	            event,
   146	            frozenset({ExecutionStatus.READY}),
   147	        )
   148	        return _advance(current, event, ExecutionStatus.RUNNING)
   149	    if isinstance(event, ExecutionWaited):
   150	        _require_source(
   151	            current,
   152	            event,
   153	            frozenset({ExecutionStatus.RUNNING}),
   154	        )
   155	        return _advance(current, event, ExecutionStatus.WAITING)
   156	    if isinstance(event, ExecutionResumed):
   157	        _require_source(
   158	            current,
   159	            event,
   160	            frozenset({ExecutionStatus.WAITING}),
   161	        )
   162	        return _advance(current, event, ExecutionStatus.RUNNING)
   163	    if isinstance(event, ExecutionBlocked):
   164	        _require_source(
   165	            current,
   166	            event,
   167	            frozenset(
   168	                {
   169	                    ExecutionStatus.READY,
   170	                    ExecutionStatus.RUNNING,
   171	                    ExecutionStatus.WAITING,
   172	                }
   173	            ),
   174	        )
   175	        return _advance(
   176	            current,
   177	            event,
   178	            ExecutionStatus.BLOCKED,
   179	            blocked_from_status=current.status,
   180	        )
   181	    if isinstance(event, ExecutionUnblocked):
   182	        if (
   183	            current.status is not ExecutionStatus.BLOCKED
   184	            or current.blocked_from_status is not event.target_status
   185	        ):
   186	            raise _invalid(current, event)
   187	        return _advance(current, event, event.target_status)
   188	    if isinstance(event, ExecutionSucceeded):
   189	        _require_source(
   190	            current,
   191	            event,
   192	            frozenset({ExecutionStatus.RUNNING}),
   193	        )
   194	        return _advance(current, event, ExecutionStatus.SUCCEEDED)
   195	    if isinstance(event, ExecutionFailed):
   196	        _require_source(
   197	            current,
   198	            event,
   199	            frozenset(
   200	                {
   201	                    ExecutionStatus.RUNNING,
   202	                    ExecutionStatus.WAITING,
   203	                    ExecutionStatus.BLOCKED,
   204	                }
   205	            ),
   206	        )
   207	        return _advance(current, event, ExecutionStatus.FAILED)
   208	    if isinstance(event, ExecutionCancelled):
   209	        _require_source(
   210	            current,
   211	            event,
   212	            frozenset(
   213	                {
   214	                    ExecutionStatus.PROPOSED,
   215	                    ExecutionStatus.READY,
   216	                    ExecutionStatus.RUNNING,
   217	                    ExecutionStatus.WAITING,
   218	                    ExecutionStatus.BLOCKED,
   219	                }
   220	            ),
   221	        )
   222	        return _advance(current, event, ExecutionStatus.CANCELLED)
   223	    raise TypeError(f"unsupported execution event: {type(event).__name__}")
   224	
   225	
   226	def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
   227	    """Replay an ordered history through the same production reducer."""
   228	    state: Execution | None = None
   229	    seen_event_ids: set[Identity] = set()
   230	    for event in events:
   231	        if event.event_id in seen_event_ids:
   232	            raise InvalidExecutionTransition("event identity is duplicated in history")
   233	        seen_event_ids.add(event.event_id)
   234	        state = reduce_execution(state, event)
   235	    if state is None:
   236	        raise InvalidExecutionTransition("execution history must not be empty")
   237	    return state
=== src/ranex/governed_execution/domain/status.py
     1	from __future__ import annotations
     2	
     3	from enum import StrEnum
     4	
     5	
     6	class ExecutionStatus(StrEnum):
     7	    PROPOSED = "PROPOSED"
     8	    READY = "READY"
     9	    RUNNING = "RUNNING"
    10	    WAITING = "WAITING"
    11	    BLOCKED = "BLOCKED"
    12	    SUCCEEDED = "SUCCEEDED"
    13	    FAILED = "FAILED"
    14	    CANCELLED = "CANCELLED"
    15	
    16	
    17	TERMINAL_EXECUTION_STATUSES = frozenset(
    18	    {
    19	        ExecutionStatus.SUCCEEDED,
    20	        ExecutionStatus.FAILED,
    21	        ExecutionStatus.CANCELLED,
    22	    }
    23	)
=== src/ranex/governed_execution/domain/events.py
     1	from __future__ import annotations
     2	
     3	from dataclasses import dataclass
     4	from datetime import UTC, datetime
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.status import ExecutionStatus
     8	
     9	
    10	def _require_text(value: str, *, field: str) -> None:
    11	    if not isinstance(value, str) or not value.strip():
    12	        raise ValueError(f"{field} must be a non-empty string")
    13	
    14	
    15	def _require_identity(value: Identity, *, prefix: str, field: str) -> None:
    16	    if not isinstance(value, Identity) or value.prefix != prefix:
    17	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    18	
    19	
    20	def _require_utc_timestamp(value: str) -> None:
    21	    _require_text(value, field="occurred_at")
    22	    if not value.endswith("Z"):
    23	        raise ValueError("occurred_at must use canonical UTC Z notation")
    24	    try:
    25	        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    26	    except ValueError as exc:
    27	        raise ValueError("occurred_at must be a valid UTC timestamp") from exc
    28	    if parsed.tzinfo != UTC:
    29	        raise ValueError("occurred_at must be UTC")
    30	
    31	
    32	@dataclass(frozen=True, slots=True, kw_only=True)
    33	class ExecutionEventMetadata:
    34	    event_id: Identity
    35	    execution_id: Identity
    36	    expected_version: int
    37	    occurred_at: str
    38	
    39	    def __post_init__(self) -> None:
    40	        _require_identity(
    41	            self.event_id,
    42	            prefix="transition",
    43	            field="event_id",
    44	        )
    45	        _require_identity(
    46	            self.execution_id,
    47	            prefix="run",
    48	            field="execution_id",
    49	        )
    50	        if (
    51	            isinstance(self.expected_version, bool)
    52	            or not isinstance(self.expected_version, int)
    53	            or self.expected_version < 0
    54	        ):
    55	            raise ValueError("expected_version must be a non-negative integer")
    56	        _require_utc_timestamp(self.occurred_at)
    57	
    58	
    59	@dataclass(frozen=True, slots=True, kw_only=True)
    60	class ExecutionCreated(ExecutionEventMetadata):
    61	    work_item_id: Identity
    62	    created_by_principal_id: Identity
    63	    workflow_request_ref: str
    64	
    65	    def __post_init__(self) -> None:
    66	        super().__post_init__()
    67	        _require_identity(
    68	            self.work_item_id,
    69	            prefix="work",
    70	            field="work_item_id",
    71	        )
    72	        _require_identity(
    73	            self.created_by_principal_id,
    74	            prefix="principal",
    75	            field="created_by_principal_id",
    76	        )
    77	        _require_text(self.workflow_request_ref, field="workflow_request_ref")
    78	
    79	
    80	@dataclass(frozen=True, slots=True, kw_only=True)
    81	class ExecutionMarkedReady(ExecutionEventMetadata):
    82	    readiness_snapshot_ref: str
    83	
    84	    def __post_init__(self) -> None:
    85	        super().__post_init__()
    86	        _require_text(
    87	            self.readiness_snapshot_ref,
    88	            field="readiness_snapshot_ref",
    89	        )
    90	
    91	
    92	@dataclass(frozen=True, slots=True, kw_only=True)
    93	class ExecutionStarted(ExecutionEventMetadata):
    94	    authorization_ref: str
    95	
    96	    def __post_init__(self) -> None:
    97	        super().__post_init__()
    98	        _require_text(self.authorization_ref, field="authorization_ref")
    99	
   100	
   101	@dataclass(frozen=True, slots=True, kw_only=True)
   102	class ExecutionWaited(ExecutionEventMetadata):
   103	    wait_reason_code: str
   104	
   105	    def __post_init__(self) -> None:
   106	        super().__post_init__()
   107	        _require_text(self.wait_reason_code, field="wait_reason_code")
   108	
   109	
   110	@dataclass(frozen=True, slots=True, kw_only=True)
   111	class ExecutionResumed(ExecutionEventMetadata):
   112	    signal_ref: str
   113	
   114	    def __post_init__(self) -> None:
   115	        super().__post_init__()
   116	        _require_text(self.signal_ref, field="signal_ref")
   117	
   118	
   119	@dataclass(frozen=True, slots=True, kw_only=True)
   120	class ExecutionBlocked(ExecutionEventMetadata):
   121	    block_reason_code: str
   122	    blocking_refs: tuple[str, ...]
   123	
   124	    def __post_init__(self) -> None:
   125	        super().__post_init__()
   126	        _require_text(self.block_reason_code, field="block_reason_code")
   127	        if not self.blocking_refs:
   128	            raise ValueError("blocking_refs must not be empty")
   129	        if any(not reference.strip() for reference in self.blocking_refs):
   130	            raise ValueError("blocking_refs must contain non-empty references")
   131	        if self.blocking_refs != tuple(sorted(set(self.blocking_refs))):
   132	            raise ValueError("blocking_refs must be unique and canonically sorted")
   133	
   134	
   135	@dataclass(frozen=True, slots=True, kw_only=True)
   136	class ExecutionUnblocked(ExecutionEventMetadata):
   137	    target_status: ExecutionStatus
   138	    refreshed_evidence_ref: str
   139	
   140	    def __post_init__(self) -> None:
   141	        super().__post_init__()
   142	        if self.target_status not in {
   143	            ExecutionStatus.READY,
   144	            ExecutionStatus.RUNNING,
   145	            ExecutionStatus.WAITING,
   146	        }:
   147	            raise ValueError("unblock target must be READY, RUNNING, or WAITING")
   148	        _require_text(
   149	            self.refreshed_evidence_ref,
   150	            field="refreshed_evidence_ref",
   151	        )
   152	
   153	
   154	@dataclass(frozen=True, slots=True, kw_only=True)
   155	class ExecutionSucceeded(ExecutionEventMetadata):
   156	    outcome_ref: str
   157	
   158	    def __post_init__(self) -> None:
   159	        super().__post_init__()
   160	        _require_text(self.outcome_ref, field="outcome_ref")
   161	
   162	
   163	@dataclass(frozen=True, slots=True, kw_only=True)
   164	class ExecutionFailed(ExecutionEventMetadata):
   165	    failure_reason_code: str
   166	    evidence_ref: str
   167	
   168	    def __post_init__(self) -> None:
   169	        super().__post_init__()
   170	        _require_text(
   171	            self.failure_reason_code,
   172	            field="failure_reason_code",
   173	        )
   174	        _require_text(self.evidence_ref, field="evidence_ref")
   175	
   176	
   177	@dataclass(frozen=True, slots=True, kw_only=True)
   178	class ExecutionCancelled(ExecutionEventMetadata):
   179	    decision_ref: str
   180	
   181	    def __post_init__(self) -> None:
   182	        super().__post_init__()
   183	        _require_text(self.decision_ref, field="decision_ref")
   184	
   185	
   186	ExecutionEvent = (
   187	    ExecutionCreated
   188	    | ExecutionMarkedReady
   189	    | ExecutionStarted
   190	    | ExecutionWaited
   191	    | ExecutionResumed
   192	    | ExecutionBlocked
   193	    | ExecutionUnblocked
   194	    | ExecutionSucceeded
   195	    | ExecutionFailed
   196	    | ExecutionCancelled
   197	)
[0m
[0m$ [0mcat -n src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py; echo "=== MIGRATION"; cat -n src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql; echo "=== PORT"; cat -n src/ranex/governed_execution/application/ports/execution_repository.py
1	from __future__ import annotations
     2	
     3	import json
     4	import sqlite3
     5	from collections.abc import Mapping
     6	from contextlib import closing
     7	from pathlib import Path
     8	
     9	from ranex.foundation.canonical import canonical_json, canonical_sha256
    10	from ranex.foundation.identity import Identity
    11	from ranex.governed_execution.application.ports.execution_repository import (
    12	    ExecutionRepository,
    13	)
    14	from ranex.governed_execution.domain.events import (
    15	    ExecutionBlocked,
    16	    ExecutionCancelled,
    17	    ExecutionCreated,
    18	    ExecutionEvent,
    19	    ExecutionFailed,
    20	    ExecutionMarkedReady,
    21	    ExecutionResumed,
    22	    ExecutionStarted,
    23	    ExecutionSucceeded,
    24	    ExecutionUnblocked,
    25	    ExecutionWaited,
    26	)
    27	from ranex.governed_execution.domain.execution import (
    28	    Execution,
    29	    reduce_execution,
    30	)
    31	from ranex.governed_execution.domain.status import ExecutionStatus
    32	
    33	_MIGRATION = Path(__file__).with_name("migrations") / "001_execution_kernel.sql"
    34	_STATE_FIELDS = frozenset(
    35	    {
    36	        "schema_version",
    37	        "execution_id",
    38	        "work_item_id",
    39	        "created_by_principal_id",
    40	        "workflow_request_ref",
    41	        "status",
    42	        "version",
    43	        "last_event_id",
    44	        "updated_at",
    45	        "blocked_from_status",
    46	    }
    47	)
    48	
    49	
    50	class ExecutionPersistenceIntegrityError(RuntimeError):
    51	    """Stored execution bytes disagree with their relational metadata."""
    52	
    53	
    54	class ConcurrentExecutionWriteError(RuntimeError):
    55	    """The expected canonical execution version changed before commit."""
    56	
    57	
    58	def _execution_to_document(execution: Execution) -> dict[str, object]:
    59	    return {
    60	        "schema_version": "execution-state/v1",
    61	        "execution_id": str(execution.execution_id),
    62	        "work_item_id": str(execution.work_item_id),
    63	        "created_by_principal_id": str(execution.created_by_principal_id),
    64	        "workflow_request_ref": execution.workflow_request_ref,
    65	        "status": execution.status.value,
    66	        "version": execution.version,
    67	        "last_event_id": str(execution.last_event_id),
    68	        "updated_at": execution.updated_at,
    69	        "blocked_from_status": (
    70	            execution.blocked_from_status.value
    71	            if execution.blocked_from_status is not None
    72	            else None
    73	        ),
    74	    }
    75	
    76	
    77	def _require_string(value: object, field: str) -> str:
    78	    if not isinstance(value, str) or not value:
    79	        raise ValueError(f"{field} must be a non-empty string")
    80	    return value
    81	
    82	
    83	def _execution_from_document(document: Mapping[str, object]) -> Execution:
    84	    if set(document) != _STATE_FIELDS:
    85	        raise ValueError("canonical execution state has unexpected fields")
    86	    if document["schema_version"] != "execution-state/v1":
    87	        raise ValueError("unsupported execution state schema version")
    88	    version = document["version"]
    89	    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
    90	        raise ValueError("execution state version must be a positive integer")
    91	    blocked_from_value = document["blocked_from_status"]
    92	    blocked_from = (
    93	        None
    94	        if blocked_from_value is None
    95	        else ExecutionStatus(_require_string(blocked_from_value, "blocked_from_status"))
    96	    )
    97	    return Execution(
    98	        execution_id=Identity.parse(
    99	            _require_string(document["execution_id"], "execution_id"),
   100	            expected_prefix="run",
   101	        ),
   102	        work_item_id=Identity.parse(
   103	            _require_string(document["work_item_id"], "work_item_id"),
   104	            expected_prefix="work",
   105	        ),
   106	        created_by_principal_id=Identity.parse(
   107	            _require_string(
   108	                document["created_by_principal_id"],
   109	                "created_by_principal_id",
   110	            ),
   111	            expected_prefix="principal",
   112	        ),
   113	        workflow_request_ref=_require_string(
   114	            document["workflow_request_ref"],
   115	            "workflow_request_ref",
   116	        ),
   117	        status=ExecutionStatus(_require_string(document["status"], "status")),
   118	        version=version,
   119	        last_event_id=Identity.parse(
   120	            _require_string(document["last_event_id"], "last_event_id"),
   121	            expected_prefix="transition",
   122	        ),
   123	        updated_at=_require_string(document["updated_at"], "updated_at"),
   124	        blocked_from_status=blocked_from,
   125	    )
   126	
   127	
   128	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   129	    document: dict[str, object] = {
   130	        "schema_version": "execution-event/v1",
   131	        "event_type": type(event).__name__,
   132	        "event_id": str(event.event_id),
   133	        "execution_id": str(event.execution_id),
   134	        "expected_version": event.expected_version,
   135	        "occurred_at": event.occurred_at,
   136	    }
   137	    if isinstance(event, ExecutionCreated):
   138	        document.update(
   139	            {
   140	                "work_item_id": str(event.work_item_id),
   141	                "created_by_principal_id": str(event.created_by_principal_id),
   142	                "workflow_request_ref": event.workflow_request_ref,
   143	            }
   144	        )
   145	    elif isinstance(event, ExecutionMarkedReady):
   146	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
   147	    elif isinstance(event, ExecutionStarted):
   148	        document["authorization_ref"] = event.authorization_ref
   149	    elif isinstance(event, ExecutionWaited):
   150	        document["wait_reason_code"] = event.wait_reason_code
   151	    elif isinstance(event, ExecutionResumed):
   152	        document["signal_ref"] = event.signal_ref
   153	    elif isinstance(event, ExecutionBlocked):
   154	        document.update(
   155	            {
   156	                "block_reason_code": event.block_reason_code,
   157	                "blocking_refs": list(event.blocking_refs),
   158	            }
   159	        )
   160	    elif isinstance(event, ExecutionUnblocked):
   161	        document.update(
   162	            {
   163	                "target_status": event.target_status.value,
   164	                "refreshed_evidence_ref": event.refreshed_evidence_ref,
   165	            }
   166	        )
   167	    elif isinstance(event, ExecutionSucceeded):
   168	        document["outcome_ref"] = event.outcome_ref
   169	    elif isinstance(event, ExecutionFailed):
   170	        document.update(
   171	            {
   172	                "failure_reason_code": event.failure_reason_code,
   173	                "evidence_ref": event.evidence_ref,
   174	            }
   175	        )
   176	    elif isinstance(event, ExecutionCancelled):
   177	        document["decision_ref"] = event.decision_ref
   178	    else:
   179	        raise TypeError(f"unsupported execution event: {type(event).__name__}")
   180	    return document
   181	
   182	
   183	class SQLiteExecutionStore(ExecutionRepository):
   184	    """State, audit journal, and outbox committed in one SQLite transaction."""
   185	
   186	    def __init__(self, path: Path) -> None:
   187	        self._path = path
   188	
   189	    def _connect(self) -> sqlite3.Connection:
   190	        connection = sqlite3.connect(
   191	            self._path,
   192	            isolation_level=None,
   193	            timeout=5.0,
   194	        )
   195	        connection.row_factory = sqlite3.Row
   196	        connection.execute("PRAGMA foreign_keys = ON")
   197	        connection.execute("PRAGMA synchronous = FULL")
   198	        return connection
   199	
   200	    def initialize(self) -> None:
   201	        self._path.parent.mkdir(parents=True, exist_ok=True)
   202	        migration = _MIGRATION.read_text(encoding="utf-8")
   203	        connection = self._connect()
   204	        try:
   205	            connection.executescript(migration)
   206	        finally:
   207	            connection.close()
   208	        self._path.chmod(0o600)
   209	
   210	    def load(self, execution_id: Identity) -> Execution | None:
   211	        self._require_run_id(execution_id)
   212	        with closing(self._connect()) as connection:
   213	            row = connection.execute(
   214	                """
   215	                SELECT execution_id, canonical_state_json, version, last_event_id
   216	                FROM execution_state
   217	                WHERE execution_id = ?
   218	                """,
   219	                (str(execution_id),),
   220	            ).fetchone()
   221	        return None if row is None else self._decode_state_row(row)
   222	
   223	    def append(self, event: ExecutionEvent) -> Execution:
   224	        connection = self._connect()
   225	        connection.execute("BEGIN IMMEDIATE")
   226	        try:
   227	            current_row = connection.execute(
   228	                """
   229	                SELECT execution_id, canonical_state_json, version, last_event_id
   230	                FROM execution_state
   231	                WHERE execution_id = ?
   232	                """,
   233	                (str(event.execution_id),),
   234	            ).fetchone()
   235	            current = (
   236	                None if current_row is None else self._decode_state_row(current_row)
   237	            )
   238	            next_state = reduce_execution(current, event)
   239	            next_document = _execution_to_document(next_state)
   240	            next_json = canonical_json(next_document)
   241	
   242	            if current is None:
   243	                connection.execute(
   244	                    """
   245	                    INSERT INTO execution_state(
   246	                        execution_id,
   247	                        canonical_state_json,
   248	                        version,
   249	                        last_event_id,
   250	                        updated_at
   251	                    ) VALUES (?, ?, ?, ?, ?)
   252	                    """,
   253	                    (
   254	                        str(next_state.execution_id),
   255	                        next_json,
   256	                        next_state.version,
   257	                        str(next_state.last_event_id),
   258	                        next_state.updated_at,
   259	                    ),
   260	                )
   261	                previous_json = None
   262	                previous_version = 0
   263	            else:
   264	                assert current_row is not None
   265	                previous_json = str(current_row["canonical_state_json"])
   266	                previous_version = current.version
   267	                cursor = connection.execute(
   268	                    """
   269	                    UPDATE execution_state
   270	                    SET canonical_state_json = ?,
   271	                        version = ?,
   272	                        last_event_id = ?,
   273	                        updated_at = ?
   274	                    WHERE execution_id = ?
   275	                      AND version = ?
   276	                      AND canonical_state_json = ?
   277	                    """,
   278	                    (
   279	                        next_json,
   280	                        next_state.version,
   281	                        str(next_state.last_event_id),
   282	                        next_state.updated_at,
   283	                        str(next_state.execution_id),
   284	                        current.version,
   285	                        previous_json,
   286	                    ),
   287	                )
   288	                if cursor.rowcount != 1:
   289	                    raise ConcurrentExecutionWriteError(
   290	                        "canonical execution compare-and-swap failed"
   291	                    )
   292	
   293	            event_document = _event_to_document(event)
   294	            event_json = canonical_json(event_document)
   295	            resulting_digest = canonical_sha256(next_document)
   296	            previous_digest = (
   297	                None
   298	                if previous_json is None
   299	                else canonical_sha256(json.loads(previous_json))
   300	            )
   301	            connection.execute(
   302	                """
   303	                INSERT INTO execution_journal(
   304	                    event_id,
   305	                    execution_id,
   306	                    event_type,
   307	                    previous_version,
   308	                    resulting_version,
   309	                    event_json,
   310	                    previous_state_sha256,
   311	                    resulting_state_sha256,
   312	                    resulting_state_json,
   313	                    recorded_at
   314	                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   315	                """,
   316	                (
   317	                    str(event.event_id),
   318	                    str(event.execution_id),
   319	                    type(event).__name__,
   320	                    previous_version,
   321	                    next_state.version,
   322	                    event_json,
   323	                    previous_digest,
   324	                    resulting_digest,
   325	                    next_json,
   326	                    event.occurred_at,
   327	                ),
   328	            )
   329	
   330	            outbox_document = {
   331	                "schema_version": "execution-outbox/v1",
   332	                "event_id": str(event.event_id),
   333	                "event_type": type(event).__name__,
   334	                "execution_id": str(event.execution_id),
   335	                "aggregate_version": next_state.version,
   336	                "occurred_at": event.occurred_at,
   337	                "event": event_document,
   338	            }
   339	            connection.execute(
   340	                """
   341	                INSERT INTO execution_outbox(
   342	                    event_id,
   343	                    execution_id,
   344	                    aggregate_version,
   345	                    payload_json,
   346	                    created_at
   347	                ) VALUES (?, ?, ?, ?, ?)
   348	                """,
   349	                (
   350	                    str(event.event_id),
   351	                    str(event.execution_id),
   352	                    next_state.version,
   353	                    canonical_json(outbox_document),
   354	                    event.occurred_at,
   355	                ),
   356	            )
   357	            connection.execute("COMMIT")
   358	            return next_state
   359	        except BaseException:
   360	            if connection.in_transaction:
   361	                connection.execute("ROLLBACK")
   362	            raise
   363	        finally:
   364	            connection.close()
   365	
   366	    def count_journal_entries(self, execution_id: Identity) -> int:
   367	        return self._count_rows("execution_journal", execution_id)
   368	
   369	    def count_outbox_entries(self, execution_id: Identity) -> int:
   370	        return self._count_rows("execution_outbox", execution_id)
   371	
   372	    def _count_rows(self, table: str, execution_id: Identity) -> int:
   373	        self._require_run_id(execution_id)
   374	        if table not in {"execution_journal", "execution_outbox"}:
   375	            raise ValueError("unsupported execution table")
   376	        with closing(self._connect()) as connection:
   377	            row = connection.execute(
   378	                f"SELECT COUNT(*) AS count FROM {table} WHERE execution_id = ?",
   379	                (str(execution_id),),
   380	            ).fetchone()
   381	        assert row is not None
   382	        return int(row["count"])
   383	
   384	    @staticmethod
   385	    def _require_run_id(execution_id: Identity) -> None:
   386	        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
   387	            raise ValueError("execution_id must be a canonical run identity")
   388	
   389	    @staticmethod
   390	    def _decode_state_row(row: sqlite3.Row) -> Execution:
   391	        raw = str(row["canonical_state_json"])
   392	        try:
   393	            document = json.loads(raw)
   394	        except json.JSONDecodeError as exc:
   395	            raise ExecutionPersistenceIntegrityError(
   396	                "canonical execution state is not JSON"
   397	            ) from exc
   398	        if not isinstance(document, dict) or canonical_json(document) != raw:
   399	            raise ExecutionPersistenceIntegrityError(
   400	                "execution state is not canonically serialized"
   401	            )
   402	        try:
   403	            state = _execution_from_document(document)
   404	        except (TypeError, ValueError) as exc:
   405	            raise ExecutionPersistenceIntegrityError(
   406	                "canonical execution state is invalid"
   407	            ) from exc
   408	        if int(row["version"]) != state.version:
   409	            raise ExecutionPersistenceIntegrityError(
   410	                "relational version disagrees with canonical state version"
   411	            )
   412	        if str(row["last_event_id"]) != str(state.last_event_id):
   413	            raise ExecutionPersistenceIntegrityError(
   414	                "relational last event disagrees with canonical state"
   415	            )
   416	        if str(row["execution_id"]) != str(state.execution_id):
   417	            raise ExecutionPersistenceIntegrityError(
   418	                "relational identity disagrees with canonical state identity"
   419	            )
   420	        return state
=== MIGRATION
     1	BEGIN IMMEDIATE;
     2	
     3	CREATE TABLE IF NOT EXISTS execution_state (
     4	    execution_id TEXT PRIMARY KEY,
     5	    canonical_state_json TEXT NOT NULL,
     6	    version INTEGER NOT NULL CHECK (version >= 1),
     7	    last_event_id TEXT NOT NULL UNIQUE,
     8	    updated_at TEXT NOT NULL
     9	);
    10	
    11	CREATE TABLE IF NOT EXISTS execution_journal (
    12	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    13	    event_id TEXT NOT NULL UNIQUE,
    14	    execution_id TEXT NOT NULL,
    15	    event_type TEXT NOT NULL,
    16	    previous_version INTEGER NOT NULL CHECK (previous_version >= 0),
    17	    resulting_version INTEGER NOT NULL,
    18	    event_json TEXT NOT NULL,
    19	    previous_state_sha256 TEXT,
    20	    resulting_state_sha256 TEXT NOT NULL,
    21	    resulting_state_json TEXT NOT NULL,
    22	    recorded_at TEXT NOT NULL,
    23	    FOREIGN KEY (execution_id)
    24	        REFERENCES execution_state(execution_id),
    25	    UNIQUE (execution_id, resulting_version),
    26	    CHECK (resulting_version = previous_version + 1),
    27	    CHECK (
    28	        (previous_version = 0 AND previous_state_sha256 IS NULL)
    29	        OR
    30	        (previous_version > 0 AND length(previous_state_sha256) = 64)
    31	    ),
    32	    CHECK (length(resulting_state_sha256) = 64)
    33	);
    34	
    35	CREATE TABLE IF NOT EXISTS execution_outbox (
    36	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    37	    event_id TEXT NOT NULL UNIQUE,
    38	    execution_id TEXT NOT NULL,
    39	    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 1),
    40	    payload_json TEXT NOT NULL,
    41	    created_at TEXT NOT NULL,
    42	    FOREIGN KEY (event_id)
    43	        REFERENCES execution_journal(event_id),
    44	    UNIQUE (execution_id, aggregate_version)
    45	);
    46	
    47	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
    48	BEFORE UPDATE ON execution_journal
    49	BEGIN
    50	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    51	END;
    52	
    53	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
    54	BEFORE DELETE ON execution_journal
    55	BEGIN
    56	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    57	END;
    58	
    59	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
    60	BEFORE UPDATE ON execution_outbox
    61	BEGIN
    62	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    63	END;
    64	
    65	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
    66	BEFORE DELETE ON execution_outbox
    67	BEGIN
    68	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    69	END;
    70	
    71	PRAGMA user_version = 1;
    72	
    73	COMMIT;
=== PORT
     1	from __future__ import annotations
     2	
     3	from typing import Protocol
     4	
     5	from ranex.foundation.identity import Identity
     6	from ranex.governed_execution.domain.events import ExecutionEvent
     7	from ranex.governed_execution.domain.execution import Execution
     8	
     9	
    10	class ExecutionRepository(Protocol):
    11	    def load(self, execution_id: Identity) -> Execution | None:
    12	        """Load the current canonical execution snapshot."""
    13	        ...
    14	
    15	    def append(self, event: ExecutionEvent) -> Execution:
    16	        """Reduce and atomically persist one execution transition."""
    17	        ...
[0m
[0m$ [0mcat -n src/ranex/governed_execution/application/gate_controller.py src/ranex/governed_execution/application/application_control_pep.py | head -220
1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	
     5	from ranex.assurance.api.contracts import (
     6	    EvidenceRecord,
     7	    GateEvaluation,
     8	    GateOutcome,
     9	)
    10	from ranex.foundation.canonical import canonical_json, canonical_sha256
    11	from ranex.governed_execution.domain.application_control import (
    12	    ApplicationControlRequest,
    13	)
    14	from ranex.policy.api.contracts import (
    15	    GateDefinition,
    16	    RuleEnforcementClass,
    17	    RuleResolution,
    18	)
    19	
    20	
    21	def _digest(value: object) -> str:
    22	    return f"sha256:{canonical_sha256(value)}"
    23	
    24	
    25	def _gate_document(gate: GateDefinition) -> dict[str, object]:
    26	    return {
    27	        "gate_id": str(gate.gate_id),
    28	        "action": gate.action,
    29	        "rules": [
    30	            {
    31	                "rule_id": rule.rule_id,
    32	                "enforcement": rule.enforcement.value,
    33	                "resolution": rule.resolution.value,
    34	                "required_claim_ids": list(rule.required_claim_ids),
    35	                "independent_producer_required": (rule.independent_producer_required),
    36	            }
    37	            for rule in gate.rules
    38	        ],
    39	    }
    40	
    41	
    42	def _evidence_document(record: EvidenceRecord) -> dict[str, object]:
    43	    return {
    44	        "evidence_id": str(record.evidence_id),
    45	        "claim_id": record.claim_id,
    46	        "outcome": record.outcome.value,
    47	        "project_id": str(record.project_id),
    48	        "execution_id": str(record.execution_id),
    49	        "action": record.action,
    50	        "subject_version": record.subject_version,
    51	        "producer_id": str(record.producer_id),
    52	        "producer_role": record.producer_role,
    53	        "command": record.command,
    54	        "exit_code": record.exit_code,
    55	        "observed_at": record.observed_at,
    56	        "artifact_sha256": record.artifact_sha256,
    57	        "artifact_verified": record.artifact_verified,
    58	    }
    59	
    60	
    61	class GateController:
    62	    """Pure fail-closed evaluator; it is not an Execution reducer."""
    63	
    64	    def evaluate(
    65	        self,
    66	        *,
    67	        gate: GateDefinition,
    68	        request: ApplicationControlRequest,
    69	        evidence: Iterable[EvidenceRecord],
    70	        catalog_id: str,
    71	        catalog_digest: str,
    72	    ) -> GateEvaluation:
    73	        records = tuple(evidence)
    74	        policy_digest = _digest(_gate_document(gate))
    75	        documents = [_evidence_document(record) for record in records]
    76	        documents.sort(key=canonical_json)
    77	        evidence_digest = _digest(documents)
    78	
    79	        def result(
    80	            outcome: GateOutcome,
    81	            *,
    82	            authorized: bool = False,
    83	            missing: tuple[str, ...] = (),
    84	            reasons: tuple[str, ...],
    85	        ) -> GateEvaluation:
    86	            return GateEvaluation(
    87	                gate_id=gate.gate_id,
    88	                request_id=request.request_id,
    89	                outcome=outcome,
    90	                authorized=authorized,
    91	                missing_claim_ids=tuple(sorted(set(missing))),
    92	                reason_codes=tuple(sorted(set(reasons))),
    93	                catalog_id=catalog_id,
    94	                catalog_digest=catalog_digest,
    95	                policy_digest=policy_digest,
    96	                evidence_digest=evidence_digest,
    97	            )
    98	
    99	        if request.action != gate.action:
   100	            return result(
   101	                GateOutcome.FAIL,
   102	                reasons=("ACTION_DOES_NOT_MATCH_GATE",),
   103	            )
   104	
   105	        authority_rules = tuple(
   106	            rule
   107	            for rule in gate.rules
   108	            if rule.enforcement
   109	            in {
   110	                RuleEnforcementClass.REQUIRED,
   111	                RuleEnforcementClass.BLOCKING,
   112	            }
   113	        )
   114	        if not authority_rules:
   115	            return result(
   116	                GateOutcome.UNKNOWN,
   117	                reasons=("NO_AUTHORITY_RULES",),
   118	            )
   119	        if any(
   120	            rule.resolution is RuleResolution.HUMAN_DECISION_REQUIRED
   121	            for rule in authority_rules
   122	        ):
   123	            return result(
   124	                GateOutcome.UNKNOWN,
   125	                reasons=("HUMAN_DECISION_NOT_VERIFIED",),
   126	            )
   127	
   128	        actor_ids = {request.requested_by, *request.subject_actor_ids}
   129	        conflicts: list[str] = []
   130	        checker_faults: list[str] = []
   131	        unverified: list[str] = []
   132	        independence_violations: list[str] = []
   133	        failed: list[str] = []
   134	        missing: list[str] = []
   135	        wrong_subject: list[str] = []
   136	
   137	        for rule in authority_rules:
   138	            for claim_id in rule.required_claim_ids:
   139	                claim_records = tuple(
   140	                    record for record in records if record.claim_id == claim_id
   141	                )
   142	                candidates = tuple(
   143	                    record
   144	                    for record in claim_records
   145	                    if record.project_id == request.project_id
   146	                    and record.execution_id == request.execution_id
   147	                    and record.action == request.action
   148	                    and record.subject_version == request.expected_version
   149	                )
   150	                if claim_records and not candidates:
   151	                    wrong_subject.append(claim_id)
   152	                    missing.append(claim_id)
   153	                    continue
   154	
   155	                outcomes = {record.outcome for record in candidates}
   156	                if GateOutcome.CHECKER_FAULT in outcomes:
   157	                    checker_faults.append(claim_id)
   158	                    continue
   159	                if GateOutcome.CONFLICT in outcomes or (
   160	                    GateOutcome.PASS in outcomes and GateOutcome.FAIL in outcomes
   161	                ):
   162	                    conflicts.append(claim_id)
   163	                    continue
   164	                passing = tuple(
   165	                    record
   166	                    for record in candidates
   167	                    if record.outcome is GateOutcome.PASS and record.exit_code == 0
   168	                )
   169	                if passing and not any(record.artifact_verified for record in passing):
   170	                    unverified.append(claim_id)
   171	                    continue
   172	                if rule.independent_producer_required and any(
   173	                    record.producer_id in actor_ids for record in passing
   174	                ):
   175	                    independence_violations.append(claim_id)
   176	                    continue
   177	                if any(
   178	                    record.outcome is GateOutcome.FAIL or record.exit_code != 0
   179	                    for record in candidates
   180	                ):
   181	                    failed.append(claim_id)
   182	                    continue
   183	                if not passing:
   184	                    missing.append(claim_id)
   185	
   186	        if checker_faults:
   187	            return result(
   188	                GateOutcome.CHECKER_FAULT,
   189	                reasons=("CHECKER_FAULT",),
   190	            )
   191	        if conflicts:
   192	            return result(
   193	                GateOutcome.CONFLICT,
   194	                reasons=("CONFLICTING_EXACT_SUBJECT_EVIDENCE",),
   195	            )
   196	        if unverified:
   197	            return result(
   198	                GateOutcome.UNKNOWN,
   199	                missing=tuple(unverified),
   200	                reasons=("UNVERIFIED_EVIDENCE_ARTIFACT",),
   201	            )
   202	        if independence_violations:
   203	            return result(
   204	                GateOutcome.FAIL,
   205	                reasons=("INDEPENDENCE_VIOLATION",),
   206	            )
   207	        if failed:
   208	            return result(
   209	                GateOutcome.FAIL,
   210	                reasons=("BLOCKING_EVIDENCE_FAILED",),
   211	            )
   212	        if missing:
   213	            return result(
   214	                GateOutcome.UNKNOWN,
   215	                missing=tuple(missing),
   216	                reasons=(
   217	                    ("WRONG_SUBJECT_EVIDENCE",)
   218	                    if wrong_subject
   219	                    else ("MISSING_BLOCKING_EVIDENCE",)
   220	                ),
[0m
[0m$ [0mcat -n src/ranex/work_management/api/contracts.py src/ranex/work_management/domain/transitions.py | head -160
1	from ranex.work_management.domain.transitions import (
     2	    WorkItemStatus,
     3	    WorkTransitionRequest,
     4	)
     5	
     6	__all__ = ["WorkItemStatus", "WorkTransitionRequest"]
     7	from __future__ import annotations
     8	
     9	import re
    10	from dataclasses import dataclass
    11	from enum import StrEnum
    12	
    13	from ranex.foundation.identity import Identity
    14	
    15	_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
    16	
    17	
    18	class WorkItemStatus(StrEnum):
    19	    FUNNEL = "FUNNEL"
    20	    TRIAGE = "TRIAGE"
    21	    DISCOVERY = "DISCOVERY"
    22	    DEFINITION = "DEFINITION"
    23	    DESIGN = "DESIGN"
    24	    READY = "READY"
    25	    IN_PROGRESS = "IN_PROGRESS"
    26	    VERIFICATION = "VERIFICATION"
    27	    RELEASE_READY = "RELEASE_READY"
    28	    RELEASING = "RELEASING"
    29	    OPERATING = "OPERATING"
    30	    OUTCOME_REVIEW = "OUTCOME_REVIEW"
    31	    CLOSED = "CLOSED"
    32	    BLOCKED = "BLOCKED"
    33	    CANCELLED = "CANCELLED"
    34	    ROLLED_BACK = "ROLLED_BACK"
    35	
    36	
    37	def _require_identity(value: Identity, prefix: str, field: str) -> None:
    38	    if not isinstance(value, Identity) or value.prefix != prefix:
    39	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    40	
    41	
    42	@dataclass(frozen=True, slots=True)
    43	class WorkTransitionRequest:
    44	    request_id: Identity
    45	    project_id: Identity
    46	    work_item_id: Identity
    47	    repository_id: Identity
    48	    candidate_commit: str
    49	    from_status: WorkItemStatus
    50	    to_status: WorkItemStatus
    51	    expected_version: int
    52	    requested_by: Identity
    53	    subject_actor_ids: tuple[Identity, ...] = ()
    54	
    55	    def __post_init__(self) -> None:
    56	        _require_identity(self.request_id, "transition", "request_id")
    57	        _require_identity(self.project_id, "prj", "project_id")
    58	        _require_identity(self.work_item_id, "work", "work_item_id")
    59	        _require_identity(self.repository_id, "repo", "repository_id")
    60	        _require_identity(self.requested_by, "principal", "requested_by")
    61	        if _COMMIT_PATTERN.fullmatch(self.candidate_commit) is None:
    62	            raise ValueError("candidate_commit must be lowercase Git commit hex")
    63	        if not isinstance(self.from_status, WorkItemStatus) or not isinstance(
    64	            self.to_status,
    65	            WorkItemStatus,
    66	        ):
    67	            raise ValueError("work transition statuses must be canonical")
    68	        if self.from_status is self.to_status:
    69	            raise ValueError("from_status and to_status must differ")
    70	        if (
    71	            isinstance(self.expected_version, bool)
    72	            or not isinstance(self.expected_version, int)
    73	            or self.expected_version < 0
    74	        ):
    75	            raise ValueError("expected_version must be a non-negative integer")
    76	        canonical_actor_ids = tuple(sorted(set(self.subject_actor_ids), key=str))
    77	        if self.subject_actor_ids != canonical_actor_ids:
    78	            raise ValueError("subject_actor_ids must be unique and sorted")
    79	        for actor_id in self.subject_actor_ids:
    80	            _require_identity(actor_id, "principal", "subject_actor_ids")
[0m
[0m$ [0mcat -n src/ranex/assurance/api/contracts.py | head -80; echo "=== ledger"; sed -n '1,60p' src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py; echo "=== pep"; cat -n src/ranex/governed_execution/application/application_control_pep.py
1	from ranex.assurance.domain.gates import (
     2	    EvidenceRecord,
     3	    GateEvaluation,
     4	    GateOutcome,
     5	)
     6	
     7	__all__ = ["EvidenceRecord", "GateEvaluation", "GateOutcome"]
=== ledger
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_json

_GENESIS_DIGEST = "0" * 64


class LedgerIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    previous_digest: str
    record_digest: str
    entry_digest: str
    record: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LedgerVerification:
    valid: bool
    entry_count: int
    broken_sequence: int | None
    head_digest: str
    reason: str | None = None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _entry_digest(
    *,
    sequence: int,
    previous_digest: str,
    record_digest: str,
) -> str:
    return _sha256_text(
        canonical_json(
            {
                "previous_digest": previous_digest,
                "record_digest": record_digest,
                "sequence": sequence,
            }
        )
    )


class HashChainLedger:
    """Append-only API over a tamper-evident canonical JSONL hash chain."""
=== pep
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	
     5	from ranex.assurance.api.contracts import (
     6	    EvidenceRecord,
     7	    GateEvaluation,
     8	    GateOutcome,
     9	)
    10	from ranex.governed_execution.application.ports.application_control_policy import (
    11	    ApplicationControlPolicy,
    12	)
    13	from ranex.governed_execution.domain.application_control import (
    14	    ApplicationControlDecision,
    15	    ApplicationControlFacts,
    16	    ApplicationControlRequest,
    17	    decide_application_control,
    18	    deny_application_control,
    19	)
    20	
    21	
    22	class ApplicationControlPEP:
    23	    """Fail-closed policy-enforcement point with no dispatch capability."""
    24	
    25	    def __init__(self, policy: ApplicationControlPolicy) -> None:
    26	        self._policy = policy
    27	
    28	    def decide(
    29	        self,
    30	        *,
    31	        request: ApplicationControlRequest,
    32	        evidence: Iterable[EvidenceRecord],
    33	    ) -> ApplicationControlDecision:
    34	        try:
    35	            evaluation = self._policy.evaluate(
    36	                request=request,
    37	                evidence=tuple(evidence),
    38	            )
    39	        except Exception:
    40	            return deny_application_control("POLICY_ADAPTER_EXCEPTION")
    41	
    42	        if not isinstance(evaluation, GateEvaluation):
    43	            return deny_application_control("MALFORMED_POLICY_DECISION")
    44	
    45	        return decide_application_control(
    46	            ApplicationControlFacts(
    47	                decision_well_formed=True,
    48	                request_bound=evaluation.request_id == request.request_id,
    49	                gate_passed=evaluation.outcome is GateOutcome.PASS,
    50	                gate_authorized=evaluation.authorized,
    51	                reason_codes=evaluation.reason_codes,
    52	            )
    53	        )
[0m
[0m$ [0msed -n '1,80p' docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md
# ADR-0014: Fix the Implementation Language and Its Performance Escape Hatch

| Field | Value |
|---|---|
| ADR ID | `ADR-0014` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-30 |
| Effective revision | Working tree based on `a573502a8`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `configuration_management`, `governed_execution`, `assurance`, `policy`, `module_governance`, `compatibility`, `migration`, `release_management`, and `process_assurance` |
| RFC | [`RFC-0001`](../rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md), accepted by the human owner on 2026-07-30 |
| Supersedes | No fixed decision; converts an undeclared inherited assumption into a stated decision with a bounded exception path |
| Review/expiry date | Review on any measured budget breach admitted under `LANG-EXCEPTION-001`, any change of runtime host or storage engine, any type-checker selection, or the expiry of a declared version ceiling |
| Compatibility/migration class | Additive declaration of the existing state plus one new gated exception path; no existing artifact changes meaning |
| Security/data class | Public architecture decision; dependency, supply-chain, and build evidence retain their own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-30 | Initial accepted decision, promoted from `RFC-0001`. Records the implementation language, which the first thirteen accepted ADRs assume and none states, and answers the owner's raw-performance concern with a measured baseline and a bounded exception path rather than a language change. |

## Context

Ranex is written in Python. Until this decision, nothing decided that.

The choice is load-bearing and was undeclared. `ADR-0007:220` writes packaging
and module-boundary rules around Python package discovery under `src/ranex`; the
contract compiler and validator are approximately 50,000 lines of Python; the
kernel R&D tracer is Python. No accepted ADR named the language.

This is the same defect class as the kernel audit finding of 2026-07-30, in
which the load-bearing inference *"the relational snapshot, not journal replay,
is canonical state authority"* was enacted by code and declared nowhere. Under
this project's own standard an unreported inference is a defect regardless of
whether it is correct. This ADR does not change the language; it declares it and
bounds the case in which departing from it is legitimate.

### Evidence

Each item is measured in this repository or verified against an external source
on 2026-07-30, and labelled accordingly. Unverified recall is not admitted as
evidence here.

1. **Measured.** `scripts/architecture/pyproject.toml` requires `>=3.12` and
   pins `jsonschema==4.25.1`, `PyYAML==6.0.2`, `rfc8785==0.1.4`. The kernel
   tracer pins `>=3.11,<3.15` with `PyYAML` only.
2. **Measured.** `validate_contracts.py` — the heaviest workload in the
   repository, covering 157 schemas, 1,021 architecture elements, and more than
   40,000 assertion cases — completes in 2.29 seconds at 82 MB peak resident set.
3. **Measured.** That speed is not attributable to compiled dependencies.
   Inspection of the installed environment shows `jsonschema` 4.25.1 and
   `rfc8785` 0.1.4 contain zero compiled extension modules and execute as pure
   Python; only `PyYAML` 6.0.2 ships one. `sqlite3` and `hashlib` are
   standard-library C. Interpreted Python performs the bulk of the work and still
   completes in 2.29 seconds.
4. **Measured.** Python's annotations are not enforced at runtime, and this has
   already produced defects here: the kernel audits found a controller accepting
   values whose declared types are `EvidenceRecord` and `bool` with no runtime
   check, reaching a security-relevant decision.
5. **Verified externally.** Pyright reports the highest typing-specification
   conformance (approximately 97.8%); Meta's Pyrefly reached stable 1.0 in May
   2026 with substantially faster execution; Astral's `ty` is alpha; `mypy`
   trails at approximately 58% conformance. No type checker is configured in any
   Ranex package; `ruff` is a linter and does not discharge this.
6. **Verified externally.** Python `3.12` has security support to approximately
   October 2028. `3.15` is scheduled for 2026-10-01, so the kernel's `<3.15`
   ceiling expires roughly three months after this decision.

### The owner's concern, and what it resolves to

The owner raised that some parts of Ranex may need raw execution speed. The
concern is registered rather than dismissed, and it resolves to a measurement:
the dominant cost in Ranex is correctness enforcement over documents, not
throughput over data, and no workload in the corpus is compute-bound. The kernel
is a single-host SQLite monolith serialized by `BEGIN IMMEDIATE`; worker
orchestration under `ADR-0005` and `ADR-0011` is dominated by provider
round-trip latency measured in seconds, against which interpreter overhead is not
[0m
[0m$ [0mgrep -rn "TypeScript\|typescript" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md docs/architecture/decisions/*.md | head -20
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:583:| Contract/schema generation | `configuration_management` orchestrates from accepted source-owner registries | deterministic contract compiler and language generators | source context owns semantics; `configuration_management` owns baseline/reproducibility | Registry digest, generated Python/TypeScript packages, drift/audit result |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:819:│       └── typescript/
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1181:It imports generated TypeScript contracts, calls authenticated application
docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md:43:| Repository intelligence | Initial qualification targets Python, TypeScript/JavaScript, Markdown, YAML/JSON, and POSIX shell; unqualified language/construct returns `UNKNOWN` | `SUB-LANG-001`: add a language only after versioned fixtures, freshness, unsupported-construct, and fallback tests |
docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md:221:docs, tools, `legacy`, worktrees, and generated TypeScript are excluded.
[0m
[0m$ [0mpython3 -c "
import json
d=json.load(open('architecture/contracts/accepted-adrs.json'))
print(json.dumps(d,indent=1)[:3000])
"
{
 "entries": [
  {
   "adr_id": "ADR-0001",
   "source_digest": "sha256:a1eec2c60576f0c5c6b7117555b6ec9abf949e983f129a402089a61affbe49b4",
   "source_path": "docs/architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md",
   "status": "ACCEPTED",
   "version": "1.1.0"
  },
  {
   "adr_id": "ADR-0002",
   "source_digest": "sha256:da71597ef601024873e0c1bf846bece30268d2d0501d5f8cd1caba6d5db9005b",
   "source_path": "docs/architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md",
   "status": "ACCEPTED",
   "version": "1.1.0"
  },
  {
   "adr_id": "ADR-0003",
   "source_digest": "sha256:83b63af6cf221d07bfeb4cd4179c33ce821132bf8e1fcc057b3958b34bff1d5d",
   "source_path": "docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md",
   "status": "ACCEPTED",
   "version": "1.0.0"
  },
  {
   "adr_id": "ADR-0004",
   "source_digest": "sha256:3e08978d1a43eb70ee6d1d06174deab82c93429242a5c85e8d4a4a1f06c09667",
   "source_path": "docs/architecture/decisions/ADR-0004-establish-initial-quality-attribute-baselines.md",
   "status": "ACCEPTED",
   "version": "1.0.0"
  },
  {
   "adr_id": "ADR-0005",
   "source_digest": "sha256:4905cbfe547a5bf04607a227aa92283ba6d304a4bdef2d08ed7387fc68edab78",
   "source_path": "docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md",
   "status": "ACCEPTED",
   "version": "1.1.0"
  },
  {
   "adr_id": "ADR-0006",
   "source_digest": "sha256:afe2757659e217c3761895e2f66874eef18408210b97c0bdbf2f8c90e377d2c4",
   "source_path": "docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md",
   "status": "ACCEPTED",
   "version": "1.1.0"
  },
  {
   "adr_id": "ADR-0007",
   "source_digest": "sha256:c0d66e868113d1a612d0ea6f48227b0fd9b2ca8aae9143f6d4da49caf454211f",
   "source_path": "docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md",
   "status": "ACCEPTED",
   "version": "1.0.0"
  },
  {
   "adr_id": "ADR-0008",
   "source_digest": "sha256:f2391238817bdda9303dbfd82b440399a162448463a850e35733c76bbe09612f",
   "source_path": "docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md",
   "status": "ACCEPTED",
   "version": "1.6.0"
  },
  {
   "adr_id": "ADR-0009",
   "source_digest": "sha256:16837df0d8647e7abaf0ecf630a52625aeb4d643763e15dd393ba2e53cb21b2b",
   "source_path": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md",
   "status": "ACCEPTED",
   "version": "1.0.0"
  },
  {
   "adr_id": "ADR-0010",
   "source_digest": "sha256:45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb",
   "source_path": "docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md",
   "status": "ACCEPTED",
   "version": "2.0.1"
  },
  {
   "adr_id": "ADR-0011",
   "source_digest": "sha256:d475f8d665295eabfcb622edfd3605e21b3fadab966886afa29990d090d7d492",
   "source_path": "docs/architecture/decisions/
[0m
[0m$ [0mgrep -n "PROPOSED\|Status" docs/architecture/rfcs/RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md | head; echo ===; git diff --stat; echo ===; git diff architecture/contracts/accepted-adrs.json | head -40
5:| Status | DRAFT |
12:| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted (`rfcs/README.md` Status) |
129:### Status quo — leave the language undeclared
===
 architecture/contracts/accepted-adrs.json          |   11 +-
 .../architecture-element-assessments.json          | 4147 ++++++++++----------
 architecture/contracts/architecture-elements.json  | 2066 +++++-----
 architecture/contracts/registry-manifest.json      |    8 +-
 architecture/contracts/schema-registry.json        |    2 +-
 docs/README.md                                     |    2 +-
 docs/architecture/README.md                        |   11 +
 docs/architecture/SOURCE_OF_TRUTH.md               |    2 +-
 .../assessments/COMPLETENESS_REPORT.md             |    2 +-
 .../assessments/completeness-report.json           |    2 +-
 .../assessments/validation-report.json             |   22 +-
 docs/architecture/reviews/README.md                |    4 +
 docs/architecture/rfcs/README.md                   |   11 +-
 docs/research/README.md                            |   14 +-
 ...-architecture-practice-application-profile.json |    3 +-
 schemas/review/review-observation-v1.schema.json   |   33 +-
 scripts/architecture/generate_contracts.py         |   52 +-
 scripts/architecture/validate_contracts.py         |    2 +-
 18 files changed, 3295 insertions(+), 3099 deletions(-)
===
diff --git a/architecture/contracts/accepted-adrs.json b/architecture/contracts/accepted-adrs.json
index 108a3d7c2..2f88a598c 100644
--- a/architecture/contracts/accepted-adrs.json
+++ b/architecture/contracts/accepted-adrs.json
@@ -90,13 +90,20 @@
       "source_path": "docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md",
       "status": "ACCEPTED",
       "version": "1.4.0"
+    },
+    {
+      "adr_id": "ADR-0014",
+      "source_digest": "sha256:823a12d237ea8549ba693ffa3353e2fd17013c6425e7c1021d79bd70274d5ea2",
+      "source_path": "docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md",
+      "status": "ACCEPTED",
+      "version": "1.0.0"
     }
   ],
   "generated_by": "scripts/architecture/generate_contracts.py",
   "registry_id": "REG-ACCEPTED-ADRS-001",
-  "required_count": 13,
+  "required_count": 14,
   "source": "docs/architecture/SOURCE_OF_TRUTH.md",
-  "source_digest": "sha256:136c9f34376217b8ace5aca4c6e3410f98e95c5276fdf953dc448448ef74b33e",
+  "source_digest": "sha256:0f2de943951c3232d221cff96689a04712d24822709fb142ccf2f710ada6604f",
   "status": "ACTIVE_DOCUMENTATION_CONTRACT",
   "version": "1.0.0"
 }
[0m
[0m$ [0mpython3 - <<'EOF'
import json,glob
for p in ['architecture/contracts/paths.json','architecture/contracts/runtime-adapters.json','architecture/contracts/identities.json']:
    d=json.load(open(p))
    print('==',p, list(d.keys())[:12])
    e=d.get('entries') or d.get('paths') or []
    print(len(e))
    print(json.dumps(e[:4],indent=1)[:1500])
EOF
== architecture/contracts/paths.json ['entries', 'generated_by', 'path_contract_schema', 'path_enactment_status', 'registry_id', 'status', 'tdd_decision_binding', 'tdd_rule_set_id', 'topology_decision_binding', 'topology_rule_set_id', 'version']
236
[
 {
  "accountable_human_role": "HUMAN_CONTEXT_OWNER",
  "allowed_dependency_targets": [
   "DECLARED_CONTEXT_LAYER_RULES"
  ],
  "applicability": "REQUIRED_BY_REGISTERED_SCOPE",
  "content_status": "MIXED",
  "data_classification": "INHERITS_SUBJECT_CLASSIFICATION",
  "data_ownership_refs": [
   "architecture/contracts/contexts.json#governed_execution",
   "architecture/contracts/data-ownership.json#governed_execution"
  ],
  "definition_status": "DEFINED",
  "dependency_direction": "INWARD_ONLY_AND_CROSS_CONTEXT_API_ONLY",
  "exception_metadata": {
   "allowed_classes": [],
   "current_exception_ids": [],
   "required": false
  },
  "governance_owner_context": "governed_execution",
  "owner_context": "governed_execution",
  "path_id": "PATH-CONTEXT-GOVERNED-EXECUTION",
  "path_pattern": "src/ranex/governed_execution/**",
  "required_reviewer_role": "INDEPENDENT_ARCHITECTURE_REVIEWER",
  "responsibility_class": "BOUNDED_CONTEXT_ROOT",
  "runtime_validation_status": "NOT_ASSESSED",
  "semantic_owner_context": "governed_execution",
  "semantic_owner_kind": "EXACT_CONTEXT",
  "semantic_owner_resolution": "The exact registered context is both governance and semantic leaf owner.",
  "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#91-nonreplaceable-authority-contexts",
  "tdd_rule_ids": [],
  "topology_rule_ids": [
   "ORG-EXEMPTION-001",
   "ORG-OWNERSHIP-001",
   "ORG-PATH-001"
  ]
 },
 {
  "accountable_human_role": "HUMAN_CONTEXT_OWNER",
  "allowed_
== architecture/contracts/runtime-adapters.json ['assignment_defaults', 'assignment_defaults_digest', 'catalog_digest', 'catalog_id', 'catalog_status', 'catalog_version', 'entries', 'fixed_decision_count', 'generated_by', 'governing_adr', 'registry_id', 'runtime_adapter_count']
2
[
 {
  "adapter_fallback": "DISABLED",
  "allowed_tools_semantics": "AUTO_APPROVAL_ONLY_NOT_RESTRICTION",
  "ambient_configuration": "DISABLED",
  "auth_policy": {
   "credential_file_extraction": "DENIED",
   "environment_precedence": "SANITIZE_AND_ATTEST_BEFORE_DISPATCH",
   "local_individual_subscription": "OFFICIAL_SUBSCRIPTION_WHEN_TERMS_AND_EFFECTIVE_AUTH_ALLOW",
   "product_api_or_cloud": "API_BYOK_SUPPORTED_CLOUD_OR_WRITTEN_VENDOR_APPROVAL"
  },
  "auxiliary_model_calls": "DISABLED",
  "cancellation": "INTERRUPT_THEN_DRAIN_TO_DEADLINE_THEN_SDK_DISCONNECT_THEN_OUTER_SUPERVISOR_CLEANUP_VERIFICATION",
  "catalog_id": "RANEX-WORKER-RUNTIME-CATALOG",
  "catalog_status": "DEFINITION_ONLY",
  "catalog_version": "1.0.0",
  "digest": "sha256:d43fab93bfc918c0c7471109423aa548ce5843dfabd9163dd7bf5bd1782fa71b",
  "event_correlation": "ASSIGNMENT_ATTEMPT_LEASE_EPOCH_SESSION_REQUEST_AND_TOOL_IDS",
  "exact_full_model_id_required": true,
  "exact_model_required": true,
  "forbidden_runtime_tool_names": [
   "Agent",
   "Task",
   "Workflow",
   "SendMessage",
   "ToolSearch",
   "Cron",
   "RemoteTrigger",
   "EnterWorktree"
  ],
  "leaf_worker_only": true,
  "lifecycle": "DEFINED_NOT_QUALIFIED",
  "model_fallback": "DISABLED",
  "nested_parent_tool_use_id": "CONTAINMENT_VIOLATION",
  "official_runtime": "CLAUDE_AGENT_SDK_CLAUDE_SDK_CLIENT",
  "official_source": "https://code.claude.com/docs/en/agent-sdk/overview",
  "preconnect": "ONLY_AFTER_COMPLETE_ASSIGNMENT_LEASE_AFFINITY_KEY_EX
== architecture/contracts/identities.json ['entries', 'generated_by', 'registry_id', 'status', 'version']
50
[
 {
  "generation": "UUIDV7",
  "prefix": "repo_",
  "type": "repository"
 },
 {
  "generation": "UUIDV7",
  "prefix": "prj_",
  "type": "project"
 },
 {
  "generation": "UUIDV7",
  "prefix": "work_",
  "type": "work_item"
 },
 {
  "generation": "UUIDV7",
  "prefix": "run_",
  "type": "run"
 }
]
[0m
[0m$ [0mgrep -n "apps/web-dashboard\|web-dashboard\|delivery\|transport" architecture/contracts/paths.json | head -20; echo ===; grep -c . architecture/contracts/paths.json
900:        "architecture/contracts/contexts.json#delivery",
901:        "architecture/contracts/data-ownership.json#delivery"
910:      "governance_owner_context": "delivery",
911:      "owner_context": "delivery",
913:      "path_pattern": "src/ranex/delivery/**",
917:      "semantic_owner_context": "delivery",
6185:        "ranex.delivery.api",
6186:        "ranex.delivery.domain"
6192:        "architecture/contracts/contexts.json#delivery",
6193:        "architecture/contracts/data-ownership.json#delivery"
6202:      "governance_owner_context": "delivery",
6203:      "owner_context": "delivery",
6205:      "path_pattern": "src/ranex/delivery/api/**",
6209:      "semantic_owner_context": "delivery",
6226:        "ranex.delivery.domain"
6232:        "architecture/contracts/contexts.json#delivery",
6233:        "architecture/contracts/data-ownership.json#delivery"
6242:      "governance_owner_context": "delivery",
6243:      "owner_context": "delivery",
6245:      "path_pattern": "src/ranex/delivery/domain/**",
===
9503
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('architecture/contracts/paths.json'))
pats=[e['path_pattern'] for e in d['entries']]
print(len(pats))
print([p for p in pats if 'apps' in p or 'web' in p or 'dashboard' in p or not p.startswith('src/')])
EOF
echo "=== identities"
python3 -c "
import json;d=json.load(open('architecture/contracts/identities.json'))
print([e['type'] for e in d['entries']])"
236
['tests/unit/**', 'tests/contract/**', 'tests/integration/**', 'tests/architecture/**', 'tests/acceptance/**', 'tests/system/**', 'tests/e2e/**', 'tests/security/**', 'tests/performance/**', 'tests/resilience/**', 'tests/migration/**', 'tests/replay/**', 'tests/operations/**', 'tests/qualification/**', 'tests/effectiveness/**', 'tests/evaluation/**', 'tests/fixtures/**', 'tests/builders/**', 'architecture/generated/**', 'packages/generated-contracts/**', 'legacy/hermes/**', 'architecture/contracts/readiness-tiers.json', 'architecture/contracts/readiness-assessments.json', 'architecture/records/readiness/**', 'schemas/assurance/readiness-*.schema.json', 'architecture/contracts/**', 'schemas/**', 'docs/architecture/assessments/**']
=== identities
['repository', 'project', 'work_item', 'run', 'activity', 'effect', 'workspace', 'packet', 'intake', 'research', 'requirement', 'criterion', 'measure', 'core_sdlc_trace', 'evidence', 'snapshot', 'artifact', 'checker_result', 'architecture_review_packet', 'architecture_proposal', 'architecture_reconciliation', 'review_request', 'analysis_attempt', 'review_observation', 'review_verdict', 'review_projection', 'independence_evaluation', 'finding', 'reconciliation', 'decision', 'authority_grant', 'permit', 'gate', 'handoff', 'result', 'landing', 'transition', 'release', 'incident', 'service', 'capability', 'assignment', 'offer', 'worker_attempt', 'lease', 'mailbox', 'reservation', 'fleet_experiment', 'capability_assessment', 'capability_domain_projection']
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('architecture/contracts/schema-registry.json'))
print(list(d.keys()))
es=d['entries'] if 'entries' in d else d
print(len(es))
import re
names=[e.get('schema_id') or e.get('path') or e for e in es]
print([n for n in names if 'execution' in str(n) or 'graph' in str(n) or 'projection' in str(n)])
EOF
['entries', 'generated_by', 'registry_id', 'schema_count', 'status', 'version']
153
['https://schemas.ranex.dev/assurance/checker-execution-subject-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/activity-dispatched-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/activity-requested-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/activity-resolved-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/authorization-evaluated-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/effect-dispatched-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/effect-intent-recorded-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/effect-outcome-marked-unknown-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/effect-reconciled-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/effect-resolved-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/evidence-snapshot-bound-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/gate-evaluated-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/human-decision-snapshot-bound-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/packet-bound-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/permit-consumed-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/permit-issued-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/policy-change-blocked-run-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-blocked-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-cancelled-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-created-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-failed-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-marked-ready-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-succeeded-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/run-unblocked-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/source-divergence-detected-v1.schema.json', 'https://schemas.ranex.dev/events/governed_execution/workflow-pinned-v1.schema.json', 'https://schemas.ranex.dev/execution/agent-handoff-v1.schema.json', 'https://schemas.ranex.dev/execution/landing-record-v1.schema.json', 'https://schemas.ranex.dev/execution/post-landing-verification-v1.schema.json', 'https://schemas.ranex.dev/execution/run-result-v1.schema.json', 'https://schemas.ranex.dev/process/capability-domain-projection-v1.schema.json', 'https://schemas.ranex.dev/review/review-record-projection-v1.schema.json']
[0m
[0m$ [0mls schemas/; echo ===; ls schemas/events 2>&1 | head; echo ===; ls schemas/execution schemas/architecture 2>&1|head -30
architecture
artifacts
assurance
authority
common
events
execution
fixtures
fleet
lifecycle
planning
process
research
resources
review
work
===
domain-event-envelope-v1.schema.json
governed_execution
work_management
===
schemas/architecture:
proposal-v1.schema.json
reconciliation-v1.schema.json
review-packet-v1.schema.json

schemas/execution:
agent-handoff-v1.schema.json
landing-record-v1.schema.json
post-landing-verification-v1.schema.json
run-result-v1.schema.json
[0m
[0m$ [0mgrep -rn "apps/\|packages/generated-contracts" docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md | head -20; echo ===; sed -n '795,830p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
45:├── apps/                           # delivery applications; no authority rules
49:├── packages/generated-contracts/   # generated language bindings
178:  `packages/generated-contracts`; generated documentation lives under
===
│       │   │   ├── updater/
│       │   │   └── rollback/
│       │   └── extensions/
│       │       └── rpc_bridge/
│       ├── compatibility/
│       │   ├── hermes_legacy/
│       │   ├── legacy_plugins/
│       │   ├── legacy_state/
│       │   ├── legacy_cli/
│       │   └── old_tool_names/
│       └── bootstrap/
│           ├── catalog.py
│           ├── profiles.py
│           ├── composition.py
│           ├── maintenance_controller.py
│           ├── lifecycle.py
│           └── main.py
├── apps/
│   └── web-dashboard/
│       ├── src/
│       └── tests/
├── packages/
│   └── generated-contracts/
│       ├── python/
│       └── typescript/
├── config/
│   ├── release-profiles/
│   ├── workflows/
│   ├── policies/
│   ├── instructions/
│   ├── roles/
│   ├── capabilities/
│   ├── routes/
│   ├── isolation/
│   ├── retention/
│   ├── services/
[0m
[0m$ [0mls schemas/events/governed_execution/; echo ===; sed -n '40,60p;170,200p' docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
activity-dispatched-v1.schema.json
activity-requested-v1.schema.json
activity-resolved-v1.schema.json
authorization-evaluated-v1.schema.json
effect-dispatched-v1.schema.json
effect-intent-recorded-v1.schema.json
effect-outcome-marked-unknown-v1.schema.json
effect-reconciled-v1.schema.json
effect-resolved-v1.schema.json
evidence-snapshot-bound-v1.schema.json
gate-evaluated-v1.schema.json
human-decision-snapshot-bound-v1.schema.json
packet-bound-v1.schema.json
permit-consumed-v1.schema.json
permit-issued-v1.schema.json
policy-change-blocked-run-v1.schema.json
run-blocked-v1.schema.json
run-cancelled-v1.schema.json
run-created-v1.schema.json
run-failed-v1.schema.json
run-marked-ready-v1.schema.json
run-succeeded-v1.schema.json
run-unblocked-v1.schema.json
source-divergence-detected-v1.schema.json
workflow-pinned-v1.schema.json
===
│   ├── modules/                    # first-party capability modules
│   ├── adapters/                   # multi-context/host-edge adapters only
│   ├── compatibility/              # anti-corruption boundary only
│   ├── bootstrap/                  # composition root and startup
│   └── migration/                  # cross-context migration ordering
├── apps/                           # delivery applications; no authority rules
├── architecture/contracts/         # owner-authored semantic registries
├── architecture/generated/         # generated projections; never hand edited
├── schemas/<owning-area>/           # canonical wire/artifact schemas
├── packages/generated-contracts/   # generated language bindings
├── tests/                           # ADR-0008 taxonomy, mirroring owners
├── config/                          # release-pinned declarative profiles
├── deploy/                          # declarative packaging/install/host assets
├── docs/
│   ├── architecture/               # normative architecture and specifications
│   │   ├── decisions/              # ADRs
│   │   └── rfcs/                   # non-accepted proposals
│   ├── research/                   # evidence/advice, never authority
│   └── operations/                 # tested runbooks
├── scripts/                        # thin public-API operator/CI clients
├── tools/                          # build, contract generation, validation
## Tests, schemas, generated artifacts, and migrations

- Tests mirror source ownership under the ADR-0008 roots. Unit paths include
  `tests/unit/<context>/domain/` and
  `tests/unit/<context>/application/`; contract/integration paths name the
  owning context and port/adapter.
- Canonical semantic registries live in `architecture/contracts`; JSON Schema
  lives once under `schemas/<owning-area>`; generated bindings live under
  `packages/generated-contracts`; generated documentation lives under
  `architecture/generated` or an explicitly generated docs subtree.
- Generated outputs carry generator/input digests and are not hand edited.
  Drift, duplicate definitions, missing owner, and schema/API incompatibility
  fail validation.
- Context-owned SQLite migrations live with the owning persistence adapter,
  normally
  `src/ranex/<context>/adapters/persistence/sqlite/migrations/`.
  `src/ranex/migration` owns only ordering, compatibility, application,
  verification, and rollback across those manifests.
- Shared SQLite connection/transaction mechanics may live in a named platform
  adapter; they cannot own context table definitions or silently coordinate
  cross-context writes.

## Operations, deployment, tooling, and documentation

- `deploy/` contains declarative package/install/service/host-profile assets.
  Runtime behavior remains in production adapters and release management.
- `docs/operations/` contains versioned runbooks linked to tested commands and
  recovery evidence.
- `scripts/` contains thin authenticated clients of public APIs; no repository,
  adapter, secret, migration, or authority shortcut is permitted.
- `tools/` contains developer/build/codegen/validation programs and fixtures;
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('schemas/events/governed_execution/workflow-pinned-v1.schema.json'));print(json.dumps(d,indent=1))" | head -60
{
 "$id": "https://schemas.ranex.dev/events/governed_execution/workflow-pinned-v1.schema.json",
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "additionalProperties": false,
 "properties": {
  "run_id": {
   "maxLength": 255,
   "minLength": 1,
   "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
   "type": "string",
   "x-ranex-id-type": "Run",
   "x-ranex-registered-opaque-id": true
  },
  "workflow_definition_ref": {
   "additionalProperties": false,
   "properties": {
    "digest": {
     "pattern": "^sha256:[0-9a-f]{64}$",
     "type": "string"
    },
    "id": {
     "maxLength": 255,
     "minLength": 1,
     "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
     "type": "string",
     "x-ranex-id-type": "WorkflowDefinition",
     "x-ranex-registered-opaque-id": true
    }
   },
   "required": [
    "id",
    "digest"
   ],
   "type": "object",
   "x-ranex-ref-type": "WorkflowDefinition"
  },
  "workflow_interpreter_version": {
   "maxLength": 1024,
   "minLength": 1,
   "pattern": ".*\\S.*",
   "type": "string"
  },
  "workflow_policy_ref": {
   "additionalProperties": false,
   "properties": {
    "digest": {
     "pattern": "^sha256:[0-9a-f]{64}$",
     "type": "string"
    },
    "id": {
     "maxLength": 255,
     "minLength": 1,
     "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
     "type": "string",
     "x-ranex-id-type": "PolicyActivation",
     "x-ranex-registered-opaque-id": true
    }
   },
   "required": [
    "id",
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('schemas/events/governed_execution/source-divergence-detected-v1.schema.json'));print(json.dumps(d,indent=1))" | head -70; echo "=== arch mention"; grep -n "SOURCEDIVERGENCE\|SourceDivergence\|divergen" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -20
{
 "$id": "https://schemas.ranex.dev/events/governed_execution/source-divergence-detected-v1.schema.json",
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "additionalProperties": false,
 "properties": {
  "divergence_class": {
   "enum": [
    "BASE_COMMIT_CHANGED",
    "CANDIDATE_COMMIT_CHANGED",
    "WORKTREE_CHANGED",
    "ARTIFACT_DIGEST_CHANGED",
    "POLICY_OR_PROFILE_CHANGED",
    "SCHEMA_OR_REGISTRY_CHANGED",
    "SUBJECT_MISSING"
   ],
   "type": "string",
   "x-ranex-enum-binding": "ENUM-SOURCE-DIVERGENCE-CLASS-1.0"
  },
  "expected_subject_digest": {
   "pattern": "^sha256:[0-9a-f]{64}$",
   "type": "string"
  },
  "expected_subject_ref": {
   "additionalProperties": false,
   "properties": {
    "digest": {
     "pattern": "^sha256:[0-9a-f]{64}$",
     "type": "string"
    },
    "id": {
     "maxLength": 255,
     "minLength": 1,
     "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
     "type": "string",
     "x-ranex-id-type": "Artifact",
     "x-ranex-registered-opaque-id": true
    }
   },
   "required": [
    "id",
    "digest"
   ],
   "type": "object",
   "x-ranex-ref-type": "Artifact"
  },
  "observed_subject_digest": {
   "pattern": "^sha256:[0-9a-f]{64}$",
   "type": "string"
  },
  "observed_subject_ref": {
   "additionalProperties": false,
   "properties": {
    "digest": {
     "pattern": "^sha256:[0-9a-f]{64}$",
     "type": "string"
    },
    "id": {
     "maxLength": 255,
     "minLength": 1,
     "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
     "type": "string",
     "x-ranex-id-type": "Artifact",
     "x-ranex-registered-opaque-id": true
    }
   },
   "required": [
    "id",
    "digest"
   ],
   "type": "object",
=== arch mention
2421:  - axis_id: "SourceDivergenceClass"
2432:    referencing_events: ["SourceDivergenceDetected"]
2434:    transition_semantics: "NOT_APPLICABLE:immutable divergence observation classification"
2715:| `SourceDivergenceClass` | `ENUM-SOURCE-DIVERGENCE-CLASS-1.0`; `configuration_management` | `BASE_COMMIT_CHANGED`, `CANDIDATE_COMMIT_CHANGED`, `WORKTREE_CHANGED`, `ARTIFACT_DIGEST_CHANGED`, `POLICY_OR_PROFILE_CHANGED`, `SCHEMA_OR_REGISTRY_CHANGED`, `SUBJECT_MISSING` |
2791:| `EVENT-SOURCEDIVERGENCEDETECTED` / `SourceDivergenceDetected` | `governed_execution` / `source_divergence_service`; `configuration_management`, `work_management`, `assurance` | `Run`; observed source/subject differs from pinned exact digest | `run_id:Id<Run>`, `expected_subject_ref:ArtifactRef`, `expected_subject_digest:Sha256`, `observed_subject_ref:ArtifactRef`, `observed_subject_digest:Sha256`, `divergence_class:Enum<SourceDivergenceClass>` |
2992:  - event_name: "SourceDivergenceDetected"
2994:    referenced_axis_ids: ["SourceDivergenceClass"]
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('architecture/contracts/context-dependency-edges.json'))
print(list(d.keys()))
es=d['entries']
print(len(es))
for e in es:
    s=json.dumps(e)
    if 'delivery' in s or 'dashboard' in s:
        print(json.dumps(e)[:400])
EOF
['actual_cycle_result', 'actual_import_pairs', 'actual_import_scan_status', 'actual_subset_result', 'decision_binding', 'declared_cycle_result', 'default_policy', 'dependency_graph_id', 'entries', 'expected_edge_count', 'generated_by', 'record_schema_path', 'registry_id', 'runtime_validation_status', 'status', 'version']
67
{"callee": "identity_access", "callee_owner": "identity_access", "caller": "delivery", "caller_owner": "delivery", "consistency": "READ_ONLY_SNAPSHOT", "definition_status": "DEFINED", "edge_id": "EDGE-DELIVERY-IDENTITY", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_QUERY", "rationale": "Authenticate channel principals and destinations.", "recovery": "REFRESH_REEVALUATE", "runtime_valida
{"callee": "work_management", "callee_owner": "work_management", "caller": "delivery", "caller_owner": "delivery", "consistency": "CALLEE_TRANSACTION_ONLY", "definition_status": "DEFINED", "edge_id": "EDGE-DELIVERY-WORK", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_COMMAND", "rationale": "Submit/query canonical work through channel-neutral commands.", "recovery": "IDEMPOTENT_RETRY_RECO
{"callee": "governed_execution", "callee_owner": "governed_execution", "caller": "delivery", "caller_owner": "delivery", "consistency": "CALLEE_TRANSACTION_ONLY", "definition_status": "DEFINED", "edge_id": "EDGE-DELIVERY-GE", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_COMMAND", "rationale": "Submit run commands and render immutable run views.", "recovery": "IDEMPOTENT_RETRY_RECONCILE"
{"callee": "interaction_history", "callee_owner": "interaction_history", "caller": "delivery", "caller_owner": "delivery", "consistency": "CALLEE_TRANSACTION_ONLY", "definition_status": "DEFINED", "edge_id": "EDGE-DELIVERY-HISTORY", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_COMMAND", "rationale": "Append classified channel messages and continuity facts.", "recovery": "IDEMPOTENT_RETR
{"callee": "delivery", "callee_owner": "delivery", "caller": "scheduling", "caller_owner": "scheduling", "consistency": "CALLEE_TRANSACTION_ONLY", "definition_status": "DEFINED", "edge_id": "EDGE-SCHEDULE-DELIVERY", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_COMMAND", "rationale": "Deliver trigger receipts and operator challenges.", "recovery": "IDEMPOTENT_RETRY_RECONCILE", "runtime_v
{"callee": "delivery", "callee_owner": "delivery", "caller": "compatibility", "caller_owner": "compatibility", "consistency": "CALLEE_TRANSACTION_ONLY", "definition_status": "DEFINED", "edge_id": "EDGE-COMPAT-DELIVERY", "failure": "FAIL_CLOSED_REQUIRED", "interaction": "SYNC_COMMAND", "rationale": "Translate legacy CLI/channel requests through canonical delivery commands.", "recovery": "IDEMPOTENT
[0m
[0m$ [0mgrep -rn "Server-Sent\|SSE\|WebSocket\|websocket\|streaming\|long-poll\|polling" docs/architecture/*.md docs/architecture/decisions/*.md | head -20; echo "=== interaction values"; python3 -c "
import json;d=json.load(open('architecture/contracts/context-dependency-edges.json'))
print(sorted({e['interaction'] for e in d['entries']}))
print(sorted({e['consistency'] for e in d['entries']}))
print(json.dumps(d['default_policy'],indent=1)[:800])
print(d['expected_edge_count'], d['runtime_validation_status'], d['actual_import_scan_status'])"
docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md:699:- [Capability assessment](./templates/CAPABILITY_ASSESSMENT.yaml);
docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md:411:- mailbox polling without new sequence;
docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md:563:ancestry. Retry, review, polling, and generated output consume the same parent
docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md:685:- mailbox delay, dead-letter, polling, and duplicate-delivery rate;
docs/architecture/AI_ARTIFACT_CONTRACTS.md:7:| Status | Normative executable documentation-contract baseline; runtime producer enforcement is `NOT_ASSESSED` and human `AI-G2` acceptance is pending |
docs/architecture/AI_ARTIFACT_CONTRACTS.md:631:  `NOT_ASSESSED`, with no numeric score, because no runtime/source subject or
docs/architecture/AI_ARTIFACT_CONTRACTS.md:635:  behavioral evidence remain `UNKNOWN`/`NOT_ASSESSED`;
docs/architecture/AI_ARTIFACT_CONTRACTS.md:670:remain explicitly `NOT_ASSESSED`/null at this tier. Before it passes, only the
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:627:1. **Capability rating:** `result` is `NOT_ASSESSED`, `UNKNOWN`,
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:634:When `result` is not `SCORED`, `level` is absent. `NOT_ASSESSED` and `UNKNOWN`
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:666:evidence, the honest result is `NOT_ASSESSED` (or `UNKNOWN` where evidence was
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:678:member ratings `NOT_ASSESSED` produces `NOT_ASSESSED`; after any begins, one
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:679:applicable `UNKNOWN`/`NOT_ASSESSED` member produces `UNKNOWN`; and a domain is
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:728:| `P1 — IMPROVE_NEXT` | Result `NOT_ASSESSED`/`UNKNOWN`; level `0`/`1`; overdue critical obligation; repeated escape; high-exposure downstream blockage; or `LOW`-confidence instrumentation need | Assign an accountable owner and begin bounded corrective or instrumentation work |
docs/architecture/CORE_SDLC_OPERATING_MODEL.md:844:  `NOT_ASSESSED` or `UNKNOWN` into zero/pass.
docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md:20:| Rights class | `CURATED_RESEARCH`, `NOASSERTION`; local possession does not establish redistribution rights |
docs/architecture/ENGINEERING_REFERENCE_APPLICATION_MAP.md:90:and `NOASSERTION` classify uncertainty; they do not create a license.
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:66:`PRODUCTION_READY` tiers. Both currently remain `NOT_ASSESSED` and
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1269:feedback-latency objectives. All observations remain `NOT_ASSESSED`.
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1467:| `CapabilityAssessmentStatus` | `NOT_ASSESSED`, `IN_PROGRESS`, `COMPLETE`, `SUPERSEDED`; owned by `process_assurance` and shared by immutable control assessments and domain projections; neither acts as a gate |
=== interaction values
['ASYNC_EVENT', 'SYNC_COMMAND', 'SYNC_QUERY']
['CALLEE_TRANSACTION_ONLY', 'EVENTUAL_OUTBOX', 'READ_ONLY_SNAPSHOT']
"DENY_UNLESS_EXACT_EDGE_REGISTERED"
67 NOT_ASSESSED NOT_ASSESSED
[0m
[0m$ [0mgrep -rn "quality attribute\|latency\|p95\|budget" docs/architecture/decisions/ADR-0004-establish-initial-quality-attribute-baselines.md | head -30
47:| Local read/query latency | `p95 <= 500 ms`, `p99 <= 1 s` | Warm local process, supported dataset, excludes explicitly identified external-provider work |
48:| Authority command commit latency | `p95 <= 2 s`, `p99 <= 5 s` | Receipt through durable SQLite commit/outbox record; excludes downstream effect completion |
[0m
[0m% [0mWebFetch https://registry.npmjs.org/@xyflow/react/latest
[0m% [0mWebFetch https://reactflow.dev/learn/troubleshooting/remove-attribution
[0m% [0mWebFetch https://registry.npmjs.org/@dagrejs/dagre/latest
[0m% [0mWebFetch https://registry.npmjs.org/elkjs/latest
[0m
[0m$ [0mfor r in kestra-io/kestra dagu-org/dagu dagster-io/dagster go-gitea/gitea apache/airflow argoproj/argo-workflows xyflow/xyflow dagrejs/dagre kieler/elkjs; do
  echo "--- $r"
  curl -s "https://api.github.com/repos/$r" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('license'), '| archived:',d.get('archived'),'| pushed:',d.get('pushed_at'),'| stars:',d.get('stargazers_count'))" 2>&1
done
--- kestra-io/kestra
{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:30:24Z | stars: 27509
--- dagu-org/dagu
None | archived: None | pushed: None | stars: None
--- dagster-io/dagster
{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-29T21:22:50Z | stars: 15916
--- go-gitea/gitea
{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-07-30T09:13:48Z | stars: 57120
--- apache/airflow
{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:26:46Z | stars: 46323
--- argoproj/argo-workflows
{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:25:58Z | stars: 16858
--- xyflow/xyflow
{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-07-30T09:59:22Z | stars: 37856
--- dagrejs/dagre
{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-03-22T16:17:24Z | stars: 5737
--- kieler/elkjs
{'key': 'other', 'name': 'Other', 'spdx_id': 'NOASSERTION', 'url': None, 'node_id': 'MDc6TGljZW5zZTA='} | archived: False | pushed: 2026-07-25T21:46:47Z | stars: 2680
[0m
[0m$ [0mcurl -s -o /tmp/opencode/dagu.json -w "%{http_code}\n" "https://api.github.com/repos/dagu-org/dagu"; head -c 400 /tmp/opencode/dagu.json; echo; echo "=== kestra license file check"; curl -s -o /dev/null -w "%{http_code}\n" "https://raw.githubusercontent.com/kestra-io/kestra/develop/LICENSE"; echo "=== kestra EE dir"; curl -s "https://api.github.com/repos/kestra-io/kestra/contents/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print([x['name'] for x in d])"
301
{
  "message": "Moved Permanently",
  "url": "https://api.github.com/repositories/484434975",
  "documentation_url": "https://docs.github.com/rest/guides/best-practices-for-using-the-rest-api#follow-redirects"
}

=== kestra license file check
200
=== kestra EE dir
['.codespellrc', '.devcontainer', '.editorconfig', '.gitattributes', '.github', '.gitignore', '.gitpod.yml', '.prettierignore', 'AGENTS.md', 'CLAUDE.md', 'Dockerfile', 'Dockerfile.base', 'Dockerfile.pr', 'LICENSE', 'Makefile', 'README.md', 'SECURITY.md', 'build-and-start-e2e-tests.sh', 'build.gradle', 'charts', 'cli', 'codecov.yml', 'core', 'dev-tools', 'docker-compose-ci.yml', 'docker-compose-dind.yml', 'docker-compose.yml', 'docker', 'docs', 'executor', 'gradle.properties', 'gradle', 'gradlew', 'gradlew.bat', 'indexer', 'jdbc-h2', 'jdbc-mysql', 'jdbc-postgres', 'jdbc', 'jmh-benchmarks', 'lombok.config', 'model', 'owasp-dependency-suppressions.xml', 'platform', 'plugins', 'processor', 'queue-jdbc', 'queue', 'repository-memory', 'runner-memory', 'scheduler', 'script', 'settings.gradle', 'storage-local', 'tests', 'ui', 'webserver', 'worker-controller', 'worker']
[0m
[0m$ [0mcurl -sL "https://api.github.com/repositories/484434975" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('full_name'), d.get('license'), '| archived:',d.get('archived'),'| pushed:',d.get('pushed_at'))"
dagucloud/dagu {'key': 'gpl-3.0', 'name': 'GNU General Public License v3.0', 'spdx_id': 'GPL-3.0', 'url': 'https://api.github.com/licenses/gpl-3.0', 'node_id': 'MDc6TGljZW5zZTk='} | archived: False | pushed: 2026-07-30T03:25:53Z
[0m
[0m$ [0mfor u in \
 "https://api.github.com/repos/go-gitea/gitea/contents/web_src/js/components/WorkflowGraph.vue?ref=e80a62f5552cad07bf79b2f31687cf5a9b93f1fc" \
 "https://api.github.com/repos/apache/airflow/contents/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx?ref=f781f8b8785496d68c9d9ae725a004764bbc9f1d" \
 "https://api.github.com/repos/argoproj/argo-workflows/contents/ui/src/widgets/workflow-graph.tsx?ref=d98d7b7d73d1b24dd7258153453ea612dbb70092" \
 "https://api.github.com/repos/argoproj/argo-workflows/contents/ui/src/shared/components/graph/pretty-layout.ts?ref=d98d7b7d73d1b24dd7258153453ea612dbb70092" \
 "https://api.github.com/repos/dagster-io/dagster/contents/js_modules/dagster-ui/packages/ui-core/src/graph/layout.ts?ref=014641bc1bdb71ea2c7f40371691103bbff5c9c7" \
 "https://api.github.com/repos/kestra-io/kestra/contents/ui/packages/topology?ref=e03a4f351328f294e67f62be60af0553401fad7a" \
 ; do printf "%s -> " "${u:30:80}"; curl -s -o /dev/null -w "%{http_code}\n" "$u"; done
o-gitea/gitea/contents/web_src/js/components/WorkflowGraph.vue?ref=e80a62f5552ca -> 200
pache/airflow/contents/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Gra -> 200
rgoproj/argo-workflows/contents/ui/src/widgets/workflow-graph.tsx?ref=d98d7b7d73 -> 200
rgoproj/argo-workflows/contents/ui/src/shared/components/graph/pretty-layout.ts? -> 200
agster-io/dagster/contents/js_modules/dagster-ui/packages/ui-core/src/graph/layo -> 404
estra-io/kestra/contents/ui/packages/topology?ref=e03a4f351328f294e67f62be60af05 -> 200
[0m
[0m$ [0mecho -n "commit 014641b: "; curl -s -o /dev/null -w "%{http_code}\n" "https://api.github.com/repos/dagster-io/dagster/commits/014641bc1bdb71ea2c7f40371691103bbff5c9c7"
echo -n "dir graph at that ref: "; curl -s "https://api.github.com/repos/dagster-io/dagster/contents/js_modules/dagster-ui/packages/ui-core/src/graph?ref=014641bc1bdb71ea2c7f40371691103bbff5c9c7" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d if isinstance(d,dict) else [x['name'] for x in d])" 2>&1 | head -20
echo -n "layout.ts on master: "; curl -s -o /dev/null -w "%{http_code}\n" "https://api.github.com/repos/dagster-io/dagster/contents/js_modules/dagster-ui/packages/ui-core/src/graph/layout.ts"
commit 014641b: 200
dir graph at that ref: {'message': 'Not Found', 'documentation_url': 'https://docs.github.com/rest/repos/contents#get-repository-content', 'status': '404'}
layout.ts on master: 404
[0m
[0m$ [0mcurl -s "https://api.github.com/search/code?q=repo:dagster-io/dagster+filename:layout.ts+path:js_modules" -H "Accept: application/vnd.github+json" | head -c 600; echo; echo "=== tree probe"; for p in js_modules js_modules/dagster-ui js_modules/dagster-ui/packages js_modules/dagster-ui/packages/ui-core/src; do printf "%s -> " "$p"; curl -s "https://api.github.com/repos/dagster-io/dagster/contents/$p" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('message') if isinstance(d,dict) else [x['name'] for x in d][:25])"; done
{
  "message": "Requires authentication",
  "documentation_url": "https://docs.github.com/rest",
  "status": "401"
}
=== tree probe
js_modules -> ['.gitignore', '.yarn', '.yarnrc.yml', 'Makefile', 'README.md', 'app-oss', 'claude.md', 'dg-docs-components', 'eslint-config', 'package.json', 'pyproject.toml', 'tox.ini', 'ui-components', 'ui-core', 'uv.lock', 'yarn.lock']
js_modules/dagster-ui -> Not Found
js_modules/dagster-ui/packages -> Not Found
js_modules/dagster-ui/packages/ui-core/src -> Not Found
[0m
[0m$ [0mprintf "js_modules@014641b -> "; curl -s "https://api.github.com/repos/dagster-io/dagster/contents/js_modules?ref=014641bc1bdb71ea2c7f40371691103bbff5c9c7" | python3 -c "
import sys,json;d=json.load(sys.stdin);print(d.get('message') if isinstance(d,dict) else [x['name'] for x in d])"
printf "ui-core/src/graph@014641b -> "; curl -s "https://api.github.com/repos/dagster-io/dagster/contents/js_modules/ui-core/src/graph?ref=014641bc1bdb71ea2c7f40371691103bbff5c9c7" | python3 -c "
import sys,json;d=json.load(sys.stdin);print(d.get('message') if isinstance(d,dict) else [x['name'] for x in d][:30])"
printf "commit date -> "; curl -s "https://api.github.com/repos/dagster-io/dagster/commits/014641bc1bdb71ea2c7f40371691103bbff5c9c7" | python3 -c "
import sys,json;d=json.load(sys.stdin);print(d['commit']['author']['date'], d['commit']['message'][:80])"
js_modules@014641b -> ['.gitignore', '.yarn', '.yarnrc.yml', 'Makefile', 'README.md', 'app-oss', 'claude.md', 'dg-docs-components', 'eslint-config', 'package.json', 'pyproject.toml', 'tox.ini', 'ui-components', 'ui-core', 'uv.lock', 'yarn.lock']
ui-core/src/graph@014641b -> ['ExternalConnectionNode.tsx', 'KindTags.tsx', 'MappingLine.tsx', 'OpEdges.tsx', 'OpGraph.tsx', 'OpIOBox.tsx', 'OpNode.tsx', 'OpTags.tsx', 'ParentOpNode.tsx', 'SVGComponents.tsx', 'SVGConsts.ts', 'SVGExporter.tsx', 'SVGViewport.tsx', 'SVGViewportContext.tsx', '__fixtures__', '__stories__', '__tests__', 'asyncGraphLayout.ts', 'common.ts', 'css', 'kindtag-images', 'layout.ts', 'makeSVGPortable.tsx', 'optag-images', 'ray.svg', 'types']
commit date -> 2026-07-29T21:20:05Z [dagster-tableau] make loading more resilient (#25279)

## Summary & Motivation
[0m
[0m$ [0mfor f in WorkflowGraph.utils.ts WorkflowGraph.utils.test.ts; do printf "%s -> " $f; curl -s -o /dev/null -w "%{http_code}\n" "https://api.github.com/repos/go-gitea/gitea/contents/web_src/js/components/$f?ref=e80a62f5552cad07bf79b2f31687cf5a9b93f1fc"; done
echo "=== airflow Graph.tsx head"
curl -s "https://raw.githubusercontent.com/apache/airflow/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx" | head -60
WorkflowGraph.utils.ts -> 200
WorkflowGraph.utils.test.ts -> 200
=== airflow Graph.tsx head
/*!
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
import { Box, Spinner, useToken } from "@chakra-ui/react";
import { ReactFlow, Background, MiniMap, type Node as ReactFlowNode } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useLocalStorage } from "usehooks-ts";

import { useDagRunServiceGetDagRun, useStructureServiceStructureData } from "openapi/queries";
import type { Direction } from "src/components/Graph/DirectionDropdown";
import { DownloadButton } from "src/components/Graph/DownloadButton";
import { edgeTypes, nodeTypes } from "src/components/Graph/graphTypes";
import { getGatePathEdgeIdsForSelection, type CustomNodeProps } from "src/components/Graph/reactflowUtils";
import { useGraphLayout } from "src/components/Graph/useGraphLayout";
import { SHOW_ALL_DEPENDENCIES_KEY, directionKey } from "src/constants/localStorage";
import { useColorMode } from "src/context/colorMode";
import { useGroups } from "src/context/groups";
import useSelectedVersion from "src/hooks/useSelectedVersion";
import { flattenGraphNodes } from "src/layouts/Details/Grid/utils.ts";
import { useDependencyGraph } from "src/queries/useDependencyGraph";
import { useGridTiSummariesStream } from "src/queries/useGridTISummaries.ts";
import { getReactFlowThemeStyle } from "src/theme";

import { FitViewOnLayout } from "./components/FitViewOnLayout";
import { GraphControls } from "./components/GraphControls";
import { useFilteredNodesAndEdges } from "./hooks/useFilteredNodesAndEdges";
import { useGraphSearchParams } from "./hooks/useGraphSearchParams";
import { useGraphFilteredNodes } from "./useGraphFilteredNodes";
import { nodeColor } from "./utils/nodeColor";

// Hoisted to module scope so ReactFlow receives a stable reference and skips
// its internal shallow-equality check on every render.
const defaultEdgeOptions = { zIndex: 1 };

export const Graph = () => {
  const { colorMode = "light" } = useColorMode();
  const { dagId = "", groupId, runId = "", taskId } = useParams();

  const selectedVersion = useSelectedVersion();

  const { depth, filterRoot, graphFilters, hasActiveFilter, includeDownstream, includeUpstream } =
    useGraphSearchParams();
[0m
[0m$ [0mcurl -s "https://raw.githubusercontent.com/argoproj/argo-workflows/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/shared/components/graph/pretty-layout.ts" | head -40; echo "=== kestra topology pkg.json"; curl -s "https://raw.githubusercontent.com/kestra-io/kestra/e03a4f351328f294e67f62be60af0553401fad7a/ui/packages/topology/package.json" | head -40
import * as dagre from 'dagre';

import {Graph, Node} from './types';

const minSize = 1;
export function layoutGraphPretty(graph: Graph, nodeSize: number, horizontal: boolean, hidden: (id: Node) => boolean) {
    const gap = nodeSize * 1.25;
    const g = new dagre.graphlib.Graph();
    g.setGraph({rankdir: horizontal ? 'LR' : 'TB', ranksep: gap, nodesep: gap, edgesep: gap});
    g.setDefaultEdgeLabel(() => ({}));
    graph.nodes.forEach((label, id) =>
        g.setNode(id, {
            width: hidden(id) ? minSize : nodeSize,
            height: hidden(id) ? minSize : nodeSize
        })
    );
    graph.edges.forEach((label, e) => {
        if (graph.nodes.has(e.v) && graph.nodes.has(e.w)) {
            g.setEdge(e.v, e.w);
        }
    });

    dagre.layout(g);

    graph.width = 0;
    graph.height = 0;
    graph.nodes.forEach((label, id) => {
        graph.nodes.get(id).x = g.node(id).x;
        graph.nodes.get(id).y = g.node(id).y;
        graph.width = Math.max(graph.width, label.x + nodeSize);
        graph.height = Math.max(graph.height, label.y + nodeSize);
    });
    graph.edges.forEach((label, e) => {
        if (graph.nodes.has(e.v) && graph.nodes.has(e.w)) {
            const points = g.edge(e).points;
            graph.edges.get(e).points = points;
            points.forEach(p => {
                graph.width = Math.max(graph.width, p.x + nodeSize);
                graph.height = Math.max(graph.height, p.y + nodeSize);
            });
=== kestra topology pkg.json
{
    "name": "@kestra-io/topology",
    "version": "0.0.0-dev",
    "description": "Kestra flow topology graph component – powered by Vue Flow",
    "type": "module",
    "homepage": "https://github.com/kestra-io/kestra#readme",
    "repository": {
        "type": "git",
        "url": "git+https://github.com/kestra-io/kestra.git"
    },
    "bugs": {
        "url": "https://github.com/kestra-io/kestra/issues"
    },
    "exports": {
        ".": "./src/index.ts",
        "./vue-flow-utils": "./src/vue-flow-utils.ts"
    },
    "main": "./dist/index.js",
    "types": "./dist/index.d.ts",
    "files": [
        "dist"
    ],
    "sideEffects": [
        "**/*.css",
        "**/*.scss",
        "./dist/style.css",
        "./src/index.ts"
    ],
    "publishConfig": {
        "access": "public"
    },
    "scripts": {
        "build": "tsdown",
        "dev": "tsdown --watch",
        "typecheck": "vue-tsc --noEmit",
        "test": "npm run unit:test",
        "unit:test": "vitest run --config vitest.unit.config.ts",
        "unit:watch": "vitest --config vitest.unit.config.ts",
        "lint:fix": "eslint --fix",
        "lint:test": "eslint",
[0m
[0m$ [0mecho "=== airflow useGraphLayout"; curl -s "https://raw.githubusercontent.com/apache/airflow/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/components/Graph/useGraphLayout.ts" | grep -n "elk\|ELK\|dagre" | head -20
echo "=== argo package.json dagre"; curl -s "https://raw.githubusercontent.com/argoproj/argo-workflows/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/package.json" | grep -n "dagre"
echo "=== dagster layout.ts dagre"; curl -s "https://raw.githubusercontent.com/dagster-io/dagster/014641bc1bdb71ea2c7f40371691103bbff5c9c7/js_modules/ui-core/src/graph/layout.ts" | grep -n "dagre" | head
=== airflow useGraphLayout
20:import ELK, { type ElkNode } from "elkjs";
27:import ElkWorkerSource from "elkjs/lib/elk-worker.min.js?raw";
32:import { generateElkGraph } from "./elkGraphUtils";
36:// original CJS environment detection in elk-worker: as a classic script
39:const elkWorkerBlobUrl = URL.createObjectURL(new Blob([ElkWorkerSource], { type: "application/javascript" }));
41:const elk = new ELK({
42:  workerFactory: () => new Worker(elkWorkerBlobUrl, { type: "classic" }),
64:      // 1. Format graph data to pass for elk to process
73:      // 2. use elk to generate the size and position of nodes and edges
74:      const data = (await elk.layout(graph)) as LayoutNode;
82:      // O(n²) findIndex. Root-level edges from ELK come first; child edges from
=== argo package.json dagre
28:        "dagre": "^0.8.5",
61:        "@types/dagre": "^0.7.52",
=== dagster layout.ts dagre
1:import * as dagre from 'dagre';
120:  const g = new dagre.graphlib.Graph();
123:  // parent op AROUND it. We pass this padding in to dagre, and then we have enough
179:  dagre.layout(g);
182:  const dagreNodes: {[opName: string]: dagre.Node} = {};
188:    dagreNodes[opName] = node;
199:  Object.entries(dagreNodes).forEach(([opName, node]) => {
[0m
[0m$ [0mecho "=== airflow ui package.json elk"; curl -s "https://raw.githubusercontent.com/apache/airflow/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/package.json" | grep -n "elk\|xyflow"
echo "=== kestra topology dagre"; curl -s "https://raw.githubusercontent.com/kestra-io/kestra/e03a4f351328f294e67f62be60af0553401fad7a/ui/packages/topology/package.json" | grep -n "dagre\|vue-flow"
=== airflow ui package.json elk
39:    "@xyflow/react": "^12.11.1",
48:    "elkjs": "^0.11.1",
=== kestra topology dagre
16:        "./vue-flow-utils": "./src/vue-flow-utils.ts"
44:        "dagre": "^0.8.5",
52:        "@vue-flow/background": "^1.3.2",
53:        "@vue-flow/controls": "^1.1.3",
54:        "@vue-flow/core": "^1.48.2",
67:        "@types/dagre": "^0.7.52",
[0m
[0m$ [0mcurl -s "https://registry.npmjs.org/dagre" | python3 -c "
import sys,json;d=json.load(sys.stdin)
t=d['time']; print('latest',d['dist-tags']); print('0.8.5 published', t.get('0.8.5')); print('modified',t.get('modified'))"
echo "=== dagrejs releases"
curl -s "https://api.github.com/repos/dagrejs/dagre/releases?per_page=6" | python3 -c "
import sys,json
for r in json.load(sys.stdin): print(r['tag_name'], r['published_at'])"
echo "=== @dagrejs/dagre versions"
curl -s "https://registry.npmjs.org/@dagrejs/dagre" | python3 -c "
import sys,json;d=json.load(sys.stdin);t=d['time']
for k,v in sorted(t.items(), key=lambda x:x[1]):
  if k not in ('created','modified'): print(k,v)" | tail -12
latest {'latest': '0.8.5'}
0.8.5 published 2019-12-03T17:04:44.979Z
modified 2022-06-14T08:16:47.942Z
=== dagrejs releases
v2.0.0 2025-11-23T09:12:13Z
v1.0.4 2023-11-17T09:34:47Z
v0.7.3 2015-07-08T14:00:58Z
v0.7.1 2014-12-17T02:29:44Z
v0.7.0 2014-12-15T03:07:08Z
v0.6.4 2014-11-02T04:38:59Z
=== @dagrejs/dagre versions
1.1.0 2024-03-13T14:57:54.479Z
1.1.1 2024-03-15T14:59:42.562Z
1.1.2 2024-04-11T11:11:40.103Z
1.1.3 2024-06-28T11:10:06.508Z
1.1.4 2024-08-15T11:11:25.778Z
1.1.5 2025-06-17T08:33:16.679Z
1.1.8 2025-11-03T21:12:11.347Z
2.0.0 2025-11-20T13:20:17.188Z
2.0.1 2025-12-01T10:31:14.674Z
2.0.3 2026-01-23T13:36:49.367Z
2.0.4 2026-02-09T19:58:41.500Z
3.0.0 2026-03-22T16:11:26.902Z
[0m
[0m$ [0mfor u in "https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui" "https://docs.gitlab.com/ci/pipelines/" "https://www.w3.org/TR/WCAG22/" "https://reactflow.dev/learn/layouting/layouting" "https://reactflow.dev/learn/advanced-use/accessibility" "https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html" "https://github.com/dagrejs/dagre/releases/tag/v2.0.0" "https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows?learn=getting_started&learnproduct=actions"; do printf "%s -> " "$u"; curl -s -o /dev/null -w "%{http_code}\n" -L "$u"; done
https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui -> 200
https://docs.gitlab.com/ci/pipelines/ -> 200
https://www.w3.org/TR/WCAG22/ -> 200
https://reactflow.dev/learn/layouting/layouting -> 200
https://reactflow.dev/learn/advanced-use/accessibility -> 200
https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html -> 200
https://github.com/dagrejs/dagre/releases/tag/v2.0.0 -> 200
https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows?learn=getting_started&learnproduct=actions -> 200
[0m
[0m$ [0mcurl -sL "https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui" | python3 -c "
import sys,re,html
t=sys.stdin.read()
t=re.sub(r'<script.*?</script>','',t,flags=re.S)
t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\s+',' ',t)
import re as r
for m in r.finditer(r'.{200}(?:visualiz|graph|real-time|real time).{200}', t, r.I):
    print(m.group(0)[:420]); print('---')
" | head -40
unners Control access Use larger runners Use custom images Actions Runner Controller Authenticate to the API Deploy runner scale sets Use ARC in a workflow Use proxy servers Monitor workflows Use the visualization graph View workflow run history View job execution time Add a status badge Use workflow run logs View job condition logs Enable debug logging Troubleshoot workflows Administer View metrics Get s
---
ate from GitLab CI/CD Migrate from Jenkins Migrate from Travis CI Actions Runner Controller Get started Troubleshoot Monitor workflows You can monitor GitHub Actions workflows by using tools like the visualization graph and run logs. Using the visualization graph Every workflow run generates a real-time graph that illustrates the run progress. You can use this graph to monitor and debug workflows. Viewing
---
[0m
[0m$ [0mcurl -sL "https://docs.gitlab.com/ci/pipelines/" | python3 -c "
import sys,re,html
t=sys.stdin.read(); t=re.sub(r'<script.*?</script>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=html.unescape(t); t=re.sub(r'\s+',' ',t)
for m in re.finditer(r'.{150}(?:graph|visualiz|group).{150}', t, re.I):
    print(m.group(0)[:330]); print('---')
" | head -40
ger a pipeline External commit statuses Customize pipeline configuration Pipeline architectures Pipeline efficiency Compute minutes Pipeline resource groups Downstream pipelines Jobs CI/CD components CI/CD inputs CI/CD variables Pipeline security GitLab Secrets Manager External secrets Debugging Auto Dev
---
example, a job could compile, test, or deploy code. Jobs run independently from each other, and are executed by runners . Stages, which define how to group jobs together. Stages run in sequence, while the jobs in a stage run in parallel. For example, an early stage could have jobs that lint and compile c
---
your pipeline Manual jobs , allow you to require manual interaction before moving forward in the pipeline. You can do this straight from the pipeline graph. Select Run ( play ) to execute that particular job. For example, your pipeline can start automatically, but require a manual action to deploy to pro
---
job in the pipeline. From this page you can cancel a running pipeline, retry failed jobs, or delete a pipeline . The pipeline details page displays a graph of all the jobs in the pipeline: You can use a standard URL to access the details for specific pipelines: gitlab.example.com/my-group/my-project/-/pi
---
group/my-project/-/pipelines/<branch>/latest : The details page for the latest pipeline for the most recent commit on branch <branch> in the project. Group jobs by stage or needs configuration When you configure jobs with the needs keyword, you have two options for how to group the jobs in the pipeline d
---
n optionally select Show dependencies to render lines between dependent jobs. Jobs in the leftmost column run first, and jobs that depend on them are grouped in the next columns. In this example: lint-job is configured with needs: [] and depends on no jobs, so it displays in the first column, despite bei
---
e third column. When you hover over a job in the Job dependencies view, every job that must run before the selected job is highlighted: Pipeline mini graphs Pipeline mini graphs take less space and can tell you at a quick glance if all jobs passed or something failed. They show all related jobs for a sin
---
The pipeline mini graph always group jobs by stage, and display throughout GitLab when displaying pipeline or commit details. Stages in pipeline mini graphs are expandable. Hover your mouse over each stage to see the name and status, and select a stage to expand its jobs list. Downstream pipeline graphs 
---
line details view and mini graphs. In the pipeline details view, a card displays for every triggered downstream pipeline on the right of the pipeline graph. Hover over a card to see which job triggered the downstream pipeline. Select a card to display the downstream pipeline to the right of the pipeline 
---
[0m
[0m$ [0mcat docs/research/README.md
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
[0m$ [0mpython3 -c "
import json;d=json.load(open('schemas/review/review-verdict-v1.schema.json'));print(json.dumps(d,indent=1))" | head -60; echo "=== ARCH version"; grep -n "ARCH-RANEX-001\|^| Version\|2.10.0" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -10
{
 "$id": "https://schemas.ranex.dev/review/review-verdict-v1.schema.json",
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "additionalProperties": false,
 "properties": {
  "artifact_type": {
   "const": "review_verdict"
  },
  "core_sdlc_trace_ref": {
   "type": "string"
  },
  "digest": {
   "type": "string",
   "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
  },
  "evidence_refs": {
   "items": {},
   "type": "array"
  },
  "independence_evaluation_id": {
   "type": "string"
  },
  "limitations": {
   "items": {},
   "type": "array"
  },
  "observation_ids": {
   "items": {},
   "type": "array"
  },
  "open_finding_refs": {
   "items": {},
   "type": "array"
  },
  "produced_at": {
   "type": "string",
   "x-ranex-runtime-format": "date-time"
  },
  "producer_service_id": {
   "type": "string"
  },
  "reconciliation_refs": {
   "items": {},
   "type": "array"
  },
  "resolved_finding_refs": {
   "items": {},
   "type": "array"
  },
  "review_request_id": {
   "type": "string"
  },
  "schema_version": {
   "const": "1"
  },
  "subject_digest": {
   "type": "string",
   "x-ranex-runtime-pattern": "^sha256:[0-9a-f]{64}$"
  },
  "subject_manifest_digest": {
=== ARCH version
5:| Architecture ID | `ARCH-RANEX-001` |
6:| Version | `2.10.0` |
[0m
[0m$ [0msed -n '25,120p' docs/architecture/decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md
current branch has passed fork preflight, executable-contract validation,
security qualification, recovery drills, performance objectives, or a
target-mode runtime tracer.

Ranex is one release-pinned modular monolith with explicit bounded-context
packages. The only canonical context source path is:

```text
src/ranex/<context>/
```

`src/ranex/contexts/<context>/` is rejected. Compatibility code lives below
`src/ranex/compatibility/`; adapters live below the owning context or the
explicit composition boundary. A second context-root convention may not be
introduced by a route plan, generator, example, or migration.

The authority kernel is single-valued:

| Authoritative record or decision | Sole owner | Explicit non-owners |
|---|---|---|
| `WorkItemStatus` and legal work-item transition | `work_management` | Runs, boards, models, agent assignments, review, assurance |
| `RunStatus`, run reducer, workflow node, gate binding, authority unit of work | `governed_execution` | Worker fleet, policy, assurance, models |
| `ConsumableAuthorityGrant`, `Permit`, permit consumption, effect intent/outcome/reconciliation | `governed_execution` | Policy, identity, adapters, workers |
| Rules, risk derivation, authorization snapshot, `HumanDecisionRecord` policy requirements | `policy` | Models, workers, delivery channels |
| Principal authentication, challenges, session/device binding, secret handles | `identity_access` | Policy, workers, delivery channels |
| Claims, `EvidenceEnvelope`, qualified `CheckerResult`, `EvidenceSnapshot`, `GateEvaluation` | `assurance` | Reviewers, governed execution, process assurance |
| `ReviewSpecification`, `ReviewRequest`, `AnalysisAttempt`, `ReviewObservation`, `ReviewVerdict`, `IndependenceEvaluation` | `analytical_review` | Assurance, governed execution, process assurance |
| SDLC conformance audits, capability assessments, corrective actions, fleet experiments | `process_assurance` | Runtime gate evaluator, workers |

`analytical_review` may publish immutable references to observations.
`assurance` may ingest those references as candidate evidence, qualify them,
and create an exact-subject evidence snapshot and `GateEvaluation`; it may not
rewrite or co-own the underlying `ReviewObservation`. `governed_execution` may
atomically bind a fresh passing `GateEvaluation` to a run and consume a valid
permit; it may not author the evaluation.

An authenticated human decision is an input to policy and assurance where the
governing rule requires judgment. It is never represented as a machine
`GateOutcome=PASS`. Policy may establish eligibility for an authority grant,
but only `governed_execution` issues and consumes the grant/permit inside the
authority transaction.

## Architectural standing

The target has three independently reported maturity states:

1. **Paper contract:** accepted by this ADR.
2. **Executable contract:** pending until canonical registries, schemas,
   generators, and drift checks pass `AI-G2`.
3. **Runtime qualification:** pending until fork preflight and the applicable
   structural, behavioral, security, recovery, and operating gates pass against
   an immutable exact subject.

A pass in one state cannot be inferred from another. In particular, a
`MAP-*` result cannot substitute for `AI-G2`, and neither can authorize an
implementation commit while `SDLC-FORK-000` is pending.

## Alternatives considered

1. **Keep the architecture conditionally selected until runtime exists.**
   Rejected because it leaves constructors without one accepted destination;
   implementation maturity is tracked separately instead.
2. **Use `src/ranex/contexts/<context>`.** Rejected because it conflicts with
   the complete target repository map and adds a redundant physical layer.
3. **Let each workflow component own its local gate or permit.** Rejected
   because duplicated authority permits disagreement and bypass.
4. **Let assurance own review observations.** Rejected because evidence
   qualification and independent analytical judgment are distinct lifecycles.
5. **Make every context a service.** Rejected because the local-first product
   does not justify distributed failure, consistency, deployment, and
   operations cost.
6. **Use one shared domain package.** Rejected because it erases ownership and
   makes authority writes difficult to constrain mechanically.

## Fitness functions and acceptance evidence

| ID | Required result |
|---|---|
| `FF-PATH-001` | The path registry, architecture tree, generated packages, import rules, and source tree contain only `src/ranex/<context>/` for context packages. |
| `FF-AUTH-001` | The lifecycle/data-ownership registries assign every authority-bearing type to exactly one owner and reject duplicate or missing owners. |
| `FF-AUTH-002` | Static imports plus integration tests prove that only `governed_execution` writes its authority tables and only `work_management` transitions work items. |
| `FF-EVID-001` | A review observation cannot directly produce `PASS`; only an `assurance` evaluator can create a subject-bound `GateEvaluation`. |
| `FF-PERMIT-001` | Stale, reused, wrong-subject, revoked, expired, or concurrently consumed grants/permits fail atomically. |
| `FF-LIFE-001` | Model/property tests cover every legal and illegal work/run transition, including block/resume, terminality, retry, and cancellation. |
| `FF-FORK-001` | `SDLC-FORK-000` binds ancestry, license, provenance, selected adoption strategy, and immutable baseline before runtime implementation. |
| `FF-BOUNDARY-001` | Dependency-graph checks report no forbidden edge, cycle, compatibility leak, or adapter-to-domain authority mutation. |

These are obligations, not claims that the current implementation passes.

## Engineering-reference application

This decision applies the frozen advisory corpus through the
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md),
especially §3 (ambiguity closure), §5.2 (decomposition), §5.3 (authority
seams), §5.4 (alternatives and fitness functions), §6 (file structure), §8
(verification), and §10 (guardrails). The references support practices; they
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('architecture/contracts/generated-output-authority.json'));print(json.dumps(d,indent=1))" | head -80
{
 "entries": [
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/accepted-adrs.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/applicability-rules.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/architecture-element-assessments.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_CURATED_RESEARCH_NOASSERTION",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/architecture-elements.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/architecture-rule-assessments.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/artifact-types.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/context-boundary-fitness.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/context-coupling-policy.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/context-dependency-edges.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/contexts.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
   "licensing_policy_id": "GENERATED_RANEX_ORIGINAL",
   "licensing_projection_required": true,
   "output_class": "CONTRACT_REGISTRY",
   "path": "architecture/contracts/data-ownership.json",
   "writer": "scripts/architecture/generate_contracts.py"
  },
  {
Exception ignored while flushing sys.stdout:
BrokenPipeError: [Errno 32] Broken pipe
[0m
[0m$ [0mgrep -rn "SDLC-FORK-000" docs/architecture/*.md docs/architecture/decisions/*.md | head -8; echo "=== new axis registration"; sed -n '1600,1660p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
docs/architecture/AI_ARTIFACT_CONTRACTS.md:662:- a clean, committed, upstream-derived `SDLC-FORK-000: PASS` subject;
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:13:| Fork preflight | [`SDLC-FORK-000 = BLOCKED`](./reviews/2026-07-28-sdlc-fork-000-preflight.md); blocking for every runtime implementation commit |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:62:`SDLC-FORK-000`, `AI-G2`, applicable behavioral/security/recovery gates, and a
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:132:gate `SDLC-FORK-000` (**fork ancestry and provenance preflight**) must:
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2648:| `SDLC-*` | Core-SDLC stage/cross-lifecycle controls, including `SDLC-FORK-000` preflight | Owning SDLC roles plus deterministic requirements |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4000:- [SDLC-FORK-000 deterministic preflight](./reviews/2026-07-28-sdlc-fork-000-preflight.md);
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4146:source and generated contracts validate without drift, `SDLC-FORK-000` passes
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:4163:- `SDLC-FORK-000` passes on the exact upstream-derived construction subject;
=== new axis registration
  - "on entry to BLOCKED, recorded_prior_state == from_state; on exact resume it equals to_state"
  - "an abandonment or rollback edge from BLOCKED must satisfy its row-specific recorded-prior and reconciliation guard"
  - "digest is RFC8785 SHA-256 of the complete fact excluding digest"
  - "any failed invariant yields STATE-REJECTION-FAIL-CLOSED-1.0 with no aggregate mutation, fact, or outbox row"
idempotency_and_replay:
  identity: "transition_id is globally unique; same ID and identical canonical bytes is idempotent, same ID with different bytes is CONFLICT"
  uniqueness: "at most one transition fact exists for (owner_context, aggregate_type, aggregate_id, aggregate_version_after)"
  replay_order: ["owner_context", "aggregate_type", "aggregate_id", "aggregate_version_after", "transition_id"]
  version_rule: "aggregate_version_before must equal the persisted aggregate version and aggregate_version_after must equal before + 1"
  gap_policy: "transition-only streams need not be gap-free because non-transition aggregate writes may consume versions; gaps are checked against the complete aggregate event log"
  forbidden_field: "transition_sequence is not part of TRANSITION-EVENT-V1 and must not be synthesized"
```
<!-- TRANSITION_FACT_CONTRACT_END -->

The catalog below is normative and machine-parseable. Each transition string
uses exact grammar `FROM>TO@GUARD_ID`; absence is denial.
`NOT_APPLICABLE:<reason>` is an exact non-applicability result, not a pass or a
missing assessment. A lifecycle may use `terminal_values: []` only when the
same row declares `nonterminal: true`; that declaration is invalid on a
classifier or on a lifecycle with any terminal value.

```yaml
schema_version: "state-axis-contract/v1"
catalog_id: "STATE-AXIS-CONTRACT-1.0"
axis_count: 44
lifecycle_axis_count: 31
classifier_axis_count: 13
value_count: 285
transition_notation: "FROM>TO@GUARD_ID"
transition_fact_ref: "schemas/work/transition-event-v1.schema.json"
rejection_policy:
  policy_id: "STATE-REJECTION-FAIL-CLOSED-1.0"
  result: "REJECT_NO_MUTATION_NO_TRANSITION_FACT_NO_OUTBOX_EVENT"
  causes: ["UNKNOWN_AXIS_OR_VALUE", "WRONG_OWNER_OR_AUTHORITY", "STALE_AGGREGATE_VERSION", "ILLEGAL_EDGE", "UNSATISFIED_GUARD", "WRONG_RECORDED_PRIOR_STATE", "MISSING_OR_STALE_EVIDENCE"]
axes:
  - axis_id: "WorkItemStatus"
    axis_kind: "LIFECYCLE"
    axis_version: "1.0.0"
    contract_ref: "states.json#WorkItemStatus@1.0.0"
    values: ["FUNNEL", "TRIAGE", "DISCOVERY", "DEFINITION", "DESIGN", "READY", "IN_PROGRESS", "VERIFICATION", "RELEASE_READY", "RELEASING", "OPERATING", "OUTCOME_REVIEW", "CLOSED", "BLOCKED", "CANCELLED", "ROLLED_BACK"]
    owner_context: "work_management"
    transition_authority: "work_lifecycle_service under accountable Core-SDLC transition authority"
    initial_values: ["FUNNEL"]
    terminal_values: ["CLOSED", "CANCELLED"]
    emitted_fact: "TransitionEventV1(axis_id=WorkItemStatus)"
    integration_events: ["WorkItemCreated", "WorkItemTransitioned", "WorkItemBlocked", "WorkItemUnblocked", "WorkItemCancelled", "WorkItemClosed"]
    rejection_policy_ref: "STATE-REJECTION-FAIL-CLOSED-1.0"
    retry_semantics: "ROLLED_BACK may re-enter TRIAGE; a terminal item requires a new linked WorkItemId"
    backward_semantics: "Only listed verification rejection, outcome falsification, rollback, and recorded BLOCKED-resume edges"
    expiry_semantics: "NOT_APPLICABLE:no wall-clock expiry state"
    cancellation_semantics: "Authenticated pre-release cancellation only through listed edges"
    revocation_semantics: "NOT_APPLICABLE:authority revocation blocks a transition but is not work-item state"
    recovery_semantics: "BLOCKED resumes only blocked_from_status after fresh evidence; ROLLED_BACK re-enters TRIAGE"
    transitions: ["FUNNEL>TRIAGE@NORMAL_EVIDENCE_AND_AUTHORITY", "TRIAGE>DISCOVERY@NORMAL_EVIDENCE_AND_AUTHORITY", "DISCOVERY>DEFINITION@NORMAL_EVIDENCE_AND_AUTHORITY", "DEFINITION>DESIGN@NORMAL_EVIDENCE_AND_AUTHORITY", "DESIGN>READY@NORMAL_EVIDENCE_AND_AUTHORITY", "READY>IN_PROGRESS@NORMAL_EVIDENCE_AND_AUTHORITY", "IN_PROGRESS>VERIFICATION@NORMAL_EVIDENCE_AND_AUTHORITY", "VERIFICATION>RELEASE_READY@NORMAL_EVIDENCE_AND_AUTHORITY", "RELEASE_READY>RELEASING@NORMAL_EVIDENCE_AND_AUTHORITY", "RELEASING>OPERATING@NORMAL_EVIDENCE_AND_AUTHORITY", "OPERATING>OUTCOME_REVIEW@NORMAL_EVIDENCE_AND_AUTHORITY", "OUTCOME_REVIEW>CLOSED@NORMAL_EVIDENCE_AND_AUTHORITY", "VERIFICATION>DEFINITION@VERIFICATION_REJECTION", "VERIFICATION>DESIGN@VERIFICATION_REJECTION", "VERIFICATION>IN_PROGRESS@VERIFICATION_REJECTION", "RELEASING>ROLLED_BACK@ROLLOUT_HEALTH_BREACH", "ROLLED_BACK>TRIAGE@SAFE_STATE_VERIFIED_AND_RETRIAGE_LINKED", "OUTCOME_REVIEW>DISCOVERY@OUTCOME_FALSIFIED", "OUTCOME_REVIEW>DEFINITION@OUTCOME_REQUIRES_REDEFINITION", "FUNNEL>BLOCKED@TYPED_BLOCKER_RECORDED", "TRIAGE>BLOCKED@TYPED_BLOCKER_RECORDED", "DISCOVERY>BLOCKED@TYPED_BLOCKER_RECORDED", "DEFINITION>BLOCKED@TYPED_BLOCKER_RECORDED", "DESIGN>BLOCKED@TYPED_BLOCKER_RECORDED", "READY>BLOCKED@TYPED_BLOCKER_RECORDED", "IN_PROGRESS>BLOCKED@TYPED_BLOCKER_RECORDED", "VERIFICATION>BLOCKED@TYPED_BLOCKER_RECORDED", "RELEASE_READY>BLOCKED@TYPED_BLOCKER_RECORDED", "RELEASING>BLOCKED@TYPED_BLOCKER_RECORDED", "OPERATING>BLOCKED@TYPED_BLOCKER_RECORDED", "OUTCOME_REVIEW>BLOCKED@TYPED_BLOCKER_RECORDED", "BLOCKED>FUNNEL@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>TRIAGE@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>DISCOVERY@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>DEFINITION@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>DESIGN@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>READY@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>IN_PROGRESS@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>VERIFICATION@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>RELEASE_READY@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>RELEASING@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>OPERATING@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "BLOCKED>OUTCOME_REVIEW@RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE", "FUNNEL>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "TRIAGE>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "DISCOVERY>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "DEFINITION>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "DESIGN>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "READY>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "IN_PROGRESS>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "VERIFICATION>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "RELEASE_READY>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION", "BLOCKED>CANCELLED@AUTHORIZED_PRE_RELEASE_CANCELLATION"]

  - axis_id: "RunStatus"
    axis_kind: "LIFECYCLE"
    axis_version: "1.0.0"
    contract_ref: "states.json#RunStatus@1.0.0"
    values: ["PROPOSED", "READY", "RUNNING", "WAITING", "BLOCKED", "SUCCEEDED", "FAILED", "CANCELLED"]
    owner_context: "governed_execution"
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('architecture/contracts/context-coupling-policy.json'));print(json.dumps(d,indent=1)[:2500])"
{
 "coupling_policy_id": "RANEX-GE-COUPLING-1.0",
 "decision_binding": {
  "decision_id": "ADR-0009",
  "digest": "sha256:16837df0d8647e7abaf0ecf630a52625aeb4d643763e15dd393ba2e53cb21b2b",
  "path": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md",
  "runtime_enactment_status": "NOT_ASSESSED",
  "status": "ACCEPTED_PAPER_DECISION"
 },
 "decision_owner": "human_governor",
 "declared_static_fan_in": 3,
 "declared_static_fan_out": 10,
 "fitness_ids": [
  "FF-COUPLING-001",
  "FF-COUPLING-002",
  "FF-ARCH9-NONCOMP-001"
 ],
 "measurement_owner": "process_assurance",
 "measures": [
  {
   "cadence": "each architecture change",
   "definition": "Count distinct registered governed_execution responsibility clauses.",
   "evidence_refs": [],
   "measure_id": "GE-RESPONSIBILITY-COUNT",
   "owner_id": "process_assurance",
   "rationale": "This falsification measure triggers review; it is not a maturity score or automatic split decision.",
   "result": "NOT_ASSESSED",
   "review_trigger": "> 12 or +2 in one rolling 20-change window"
  },
  {
   "cadence": "each edge/architecture change",
   "definition": "Count approved outgoing source-dependency edges.",
   "evidence_refs": [],
   "measure_id": "GE-STATIC-FAN-OUT",
   "owner_id": "process_assurance",
   "rationale": "This falsification measure triggers review; it is not a maturity score or automatic split decision.",
   "result": "NOT_ASSESSED",
   "review_trigger": "> 10"
  },
  {
   "cadence": "each edge/architecture change",
   "definition": "Count approved incoming source-dependency edges.",
   "evidence_refs": [],
   "measure_id": "GE-STATIC-FAN-IN",
   "owner_id": "process_assurance",
   "rationale": "This falsification measure triggers review; it is not a maturity score or automatic split decision.",
   "result": "NOT_ASSESSED",
   "review_trigger": "> 8"
  },
  {
   "cadence": "each tracer/release; rolling 30 transitions",
   "definition": "Distribution of distinct synchronous context calls per authority transition.",
   "evidence_refs": [],
   "measure_id": "GE-INTERACTION-COUPLING",
   "owner_id": "process_assurance",
   "rationale": "This falsification measure triggers review; it is not a maturity score or automatic split decision.",
   "result": "NOT_ASSESSED",
   "review_trigger": "p95 > 8 or > 25% of transitions call more than 4 contexts"
  },
  {
   "cadence": "rolling 20 accepted changes",
   "definition": "Distribution of other contexts changed with gov
[0m
[0m$ [0mpython3 - <<'EOF'
import json
d=json.load(open('architecture/contracts/context-dependency-edges.json'))
out=[e for e in d['entries'] if e['caller']=='governed_execution']
inn=[e for e in d['entries'] if e['callee']=='governed_execution']
print('GE fan-out',len(out),[ (e['callee'],e['interaction']) for e in out])
print('GE fan-in',len(inn),[ (e['caller'],e['interaction']) for e in inn])
EOF
GE fan-out 10 [('policy', 'SYNC_QUERY'), ('assurance', 'SYNC_QUERY'), ('module_governance', 'SYNC_QUERY'), ('identity_access', 'SYNC_QUERY'), ('resource_governance', 'SYNC_COMMAND'), ('workspace', 'SYNC_QUERY'), ('context_compilation', 'SYNC_COMMAND'), ('routing', 'SYNC_QUERY'), ('agent_collaboration', 'SYNC_COMMAND'), ('artifact_management', 'SYNC_COMMAND')]
GE fan-in 3 [('delivery', 'SYNC_COMMAND'), ('scheduling', 'SYNC_COMMAND'), ('compatibility', 'SYNC_COMMAND')]
[0m
[0m$ [0msed -n '3830,3860p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo ===; grep -n "FF-COUPLING-001\|FF-COUPLING-002\|fan-out\|fan-in" docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md | head -20
seal any of them.

### 33.5 Boundary-fit, dependency, coupling, and feedback gates

[ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md)
adds ten noncompensating rules:

- exact owned dependency semantics, actual-import subset, and acyclicity:
  `ARCH-EDGE-001`, `ARCH-EDGE-002`, and `ARCH-EDGE-003`;
- exact 34-context boundary hypotheses and falsifier disposition:
  `ARCH-BOUNDARY-001` and `ARCH-BOUNDARY-002`;
- governed-execution responsibility/fan-in/fan-out/interaction/change/
  ownership-concentration measurement and trigger response:
  `ARCH-COUPLING-001` and `ARCH-COUPLING-002`;
- exact-host/artifact feedback distributions plus deterministic selection,
  sharding, and risk escalation: `TDD-FEEDBACK-001` and
  `TDD-FEEDBACK-002`; and
- no compensation across any of them: `ARCH9-NONCOMP-001`.

The approved source graph has 67 unique caller/callee edges, no cycle, and
`governed_execution` fan-out/fan-in of 10/3. Those are paper definitions, not
observed source facts. Each boundary row has a keep/merge/split alternative
and tracer falsifier. A coupling threshold starts an independent review; it
does not automatically mandate a split or microservice. Feedback objectives
never authorize omitted tests or a different candidate artifact.

### 33.6 Inherited Hermes test-layout migration gates

[ADR-0010](./decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md)
adds ten noncompensating `LEGACYTEST-*` rules and nine `FF-LEGACYTEST-*`
fitness checks. They reproduce the immutable 2,444-file baseline, require
===
28:waiver from coupling control: responsibility, fan-in, fan-out, interaction
287:  - {id: "ARCH-COUPLING-001", enforcement: "BLOCK", invariant: "governed_execution responsibility, fan-in, fan-out, interaction, change, and ownership-concentration distributions are exact-subject measured at the declared cadence."}
300:| `FF-COUPLING-001` | Exact-subject static and rolling runtime/change distributions compute all six governed-execution measures. |
301:| `FF-COUPLING-002` | Threshold fixtures prove every trigger creates a blocking review record and no average suppresses it. |
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('architecture/contracts/readiness-assessments.json'));print(json.dumps(d,indent=1)[:1500])"; echo ===; python3 -c "
import json;d=json.load(open('architecture/contracts/readiness-tiers.json'));print(d.get('catalog_status'), d.get('declared_tier'), list(d.keys()))"
{
 "contract_id": "RANEX-READINESS-TIER-CONTROL-1.0",
 "contract_version": "1.0.0",
 "current_standing": {
  "assessment_record_count": 0,
  "capability_score": null,
  "evidence_binding_count": 0,
  "implementation_start_authorized": false,
  "implementation_start_state": "NOT_ASSESSED",
  "production_authorized": false,
  "production_state": "NOT_ASSESSED",
  "runtime_validation_status": "NOT_ASSESSED",
  "subject_manifest_count": 0,
  "transition_fact_count": 0
 },
 "entries": [],
 "evidence_binding_schema_ref": "schemas/assurance/readiness-evidence-binding-v1.schema.json",
 "generated_by": "scripts/architecture/generate_contracts.py",
 "governing_adr": "ADR-0012",
 "record_count": 0,
 "record_schema_ref": "schemas/assurance/readiness-assessment-v1.schema.json",
 "registry_id": "REG-READINESS-ASSESSMENTS-001",
 "source_contract_digest": "sha256:81f295e5a28fb67784c4dd93650ee8b020da0098aa22e5d09414df8993ad3277",
 "source_digest": "sha256:2707cfe0b1b4111f5b9ec1e41f9c71f0fbf75ac7f438c6df2d0829ea2ff54d02",
 "source_path": "docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md",
 "status": "DEFINITION_ONLY_NOT_ASSESSED",
 "subject_manifest_schema_ref": "schemas/assurance/readiness-subject-manifest-v1.schema.json",
 "subject_schema_ref": "schemas/assurance/readiness-subject-v1.schema.json",
 "tier_catalog_ref": "architecture/contracts/readiness-tiers.json",
 "version": "1.0.0"
}
===
DEFINITION_ONLY_NOT_ASSESSED None ['additional_properties', 'assessment_record', 'assessment_registry_ref', 'assessment_schema_ref', 'bootstrap_lane', 'canonicalization', 'catalog_id', 'catalog_status', 'catalog_version', 'contract_id', 'contract_version', 'current_standing', 'digest_algorithm', 'digest_encoding', 'evidence_binding_schema_ref', 'evidence_bridge_contract', 'exact_subject_projection', 'fixture_contract', 'gates', 'generated_by', 'governing_adr', 'human_decision_contract', 'inherited_type_authority', 'nested_types', 'noncompensating', 'readiness_subject_manifest_projection', 'resolver_contract', 'reviewer_contract', 'runtime_assessment_status_contract', 'sad_path_transitions', 'scalar_types', 'schema_version', 'source_contract_digest', 'source_digest', 'source_path', 'source_projection_ref', 'state_axis', 'subject_manifest_schema_ref', 'subject_schema_ref', 'tiers', 'transition_fact_contract']
[0m
[0m$ [0msed -n '55,80p;125,150p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
- deleting all inherited behavior before a replacement is characterized;
- a big-bang production cutover; or
- allowing upstream layout or implementation details to define the new domain.

The architecture is accepted as the paper target by
[ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md).
That decision does not claim executable-contract or runtime validation.
`SDLC-FORK-000`, `AI-G2`, applicable behavioral/security/recovery gates, and a
complete exact-subject tracer remain separately reportable proof obligations.
[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md)
maps those obligations into separate `IMPLEMENTATION_START_READY` and
`PRODUCTION_READY` tiers. Both currently remain `NOT_ASSESSED` and
unauthorized.
Model review, including DeepSeek V4 Pro and HY3 review, is advisory evidence
and is never an architecture decision by itself.

### 1.1 Software-development process foundation

The architecture is subordinate to the owner-accepted, human-established
software-development lifecycle. Core SDLC owns the product-to-production
process: governance, discovery, requirements, design, planning, build,
independent verification and validation, release, operation, maintenance,
retirement, and improvement.

Ranex does not invent a parallel “AI-native SDLC.” AI agents are bounded leaf
workers used inside named lifecycle activities. Retained inherited Hermes
  manifest was proven; and
- GitHub reports a separately hosted repository (`fork=false`, with no
  parent/source relationship), which is a hosting fact rather than Git
  ancestry evidence.

A software-derived fork, shared Git ancestry, and GitHub's network-fork flag
are separate facts. Before implementation begins, the machine-registerable
gate `SDLC-FORK-000` (**fork ancestry and provenance preflight**) must:

1. preserve the current Ranex commits under an immutable safety ref;
2. retain the exact audited upstream commit in a pristine mirror/worktree and
   verify its tree, license, notices, tags, and source manifest;
3. record the human-selected adoption strategy—prefer replaying the Ranex
   documentation commits on the pinned upstream base when it preserves both
   histories cleanly; otherwise use a provenance-complete history import;
4. keep `upstream` fetch-only and define the final Ranex branch/worktree
   topology;
5. distinguish the observed, audited, incorporated, and latest-seen upstream
   baselines;
6. restore the unchanged upstream license and classify every retained,
   modified, removed, or original file; and
7. prove ancestry/baseline/provenance and record the manifest's network-fork
   field as the actual hosting fact, which may legitimately remain `false`.

The gate's required evidence is:
[0m
[0m$ [0mgrep -n "FORBIDDEN\|ALLOWED\|def test_\|api\b" tests/architecture/test_kernel_imports.py | head -50
17:_LAYERS = frozenset({"api", "domain", "application", "adapters"})
18:_DOMAIN_FORBIDDEN_IMPORTS = frozenset(
36:_DOMAIN_FORBIDDEN_CALLS = frozenset(
171:    if source_layer == "api":
172:        return target_layer in {"api", "domain", "application"}
174:        return target_layer in {"api", "domain", "application"}
232:                if root_module in _DOMAIN_FORBIDDEN_IMPORTS:
271:                if target_layer != "api":
311:                    and name in _DOMAIN_FORBIDDEN_CALLS
379:def test_kernel_imports_follow_layering_and_have_no_hermes_reachability() -> None:
384:def test_kernel_import_graph_is_acyclic() -> None:
389:def test_checker_rejects_private_cross_context_import(tmp_path: Path) -> None:
405:def test_checker_rejects_relative_private_cross_context_import(
423:def test_checker_rejects_hermes_import(tmp_path: Path) -> None:
434:def test_checker_rejects_dynamic_hermes_import(tmp_path: Path) -> None:
448:def test_checker_rejects_domain_environment_dependency(tmp_path: Path) -> None:
462:def test_checker_allows_api_to_expose_immutable_domain_types(
466:    source = root / "assurance" / "api" / "contracts.py"
476:def test_importing_entire_kernel_graph_loads_no_hermes_dependency() -> None:
[0m
[0m$ [0mcd /tmp/opencode && python3 - <<'EOF'
import sqlite3, os
p='/tmp/opencode/seqtest.db'
if os.path.exists(p): os.remove(p)
c=sqlite3.connect(p, isolation_level=None)
c.execute("CREATE TABLE j(sequence INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
c.execute("BEGIN IMMEDIATE"); c.execute("INSERT INTO j(v) VALUES('a')"); c.execute("COMMIT")
c.execute("BEGIN IMMEDIATE"); c.execute("INSERT INTO j(v) VALUES('b')"); c.execute("ROLLBACK")
c.execute("BEGIN IMMEDIATE"); c.execute("INSERT INTO j(v) VALUES('c')"); c.execute("COMMIT")
print("rows:", c.execute("SELECT sequence,v FROM j").fetchall())
print("sqlite_sequence:", c.execute("SELECT * FROM sqlite_sequence").fetchall())
print("journal_mode:", c.execute("PRAGMA journal_mode").fetchone())
EOF
rows: [(1, 'a'), (2, 'c')]
sqlite_sequence: [('j', 2)]
journal_mode: ('delete',)
[0m
[0m$ [0mcd /tmp/opencode && python3 - <<'EOF'
import sqlite3, os
p='/tmp/opencode/lock.db'
if os.path.exists(p): os.remove(p)
a=sqlite3.connect(p, isolation_level=None); a.execute("PRAGMA synchronous=FULL")
a.execute("CREATE TABLE t(x INTEGER)"); a.execute("INSERT INTO t VALUES(1)")
print("journal_mode:", a.execute("PRAGMA journal_mode").fetchone())
r=sqlite3.connect(p, isolation_level=None, timeout=1.0)
r.execute("BEGIN")           # deferred
r.execute("SELECT * FROM t").fetchall()   # now holds SHARED lock
w=sqlite3.connect(p, isolation_level=None, timeout=1.0)
try:
    w.execute("BEGIN IMMEDIATE"); print("writer acquired RESERVED (ok)")
    try:
        w.execute("INSERT INTO t VALUES(2)"); w.execute("COMMIT"); print("writer COMMITTED while reader open")
    except Exception as e: print("writer COMMIT failed:", type(e).__name__, e)
except Exception as e:
    print("writer BEGIN IMMEDIATE failed:", type(e).__name__, e)
EOF
journal_mode: ('delete',)
writer acquired RESERVED (ok)
writer COMMIT failed: OperationalError database is locked
[0m
[0m$ [0mgrep -rniE "http|fastapi|starlette|uvicorn|flask|redact|classificat|principal_auth|session|authenticat" --include=*.py --include=*.toml src tests pyproject.toml | grep -v "\.pyc" | head -20; echo "--- deps"; cat pyproject.toml
tests/architecture/test_kernel_imports.py:21:        "httpx",
--- deps
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
[0m
[0m$ [0mgrep -rn "work_item_id" --include=*.py .claude/worktrees/kernel-tracer/src | head -20; echo "=== 12.1 ports table / query"; grep -n "query\|read model\|projection" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '1,40p'
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:40:    work_item_id: Identity
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:52:        _require_identity(self.work_item_id, "work", "work_item_id")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:55:    work_item_id: Identity
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:115:            work_item_id=event.work_item_id,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:61:    work_item_id: Identity
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:68:            self.work_item_id,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:70:            field="work_item_id",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:38:        "work_item_id",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:62:        "work_item_id": str(execution.work_item_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:102:        work_item_id=Identity.parse(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:103:            _require_string(document["work_item_id"], "work_item_id"),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:140:                "work_item_id": str(event.work_item_id),
=== 12.1 ports table / query
208:This prose table is the readable projection; a mismatch is `CONFLICT`.
253:6. Kanban, dashboards, Hermes session state, and external systems are projections
477:- Other context projections are rebuilt or reconciled from canonical events.
499:| `assurance` | Claims, evidence envelopes, qualified checker results, exact-subject evidence snapshots, and `GateEvaluation` | Evidence ingestion/query, checker result, snapshot and gate-evaluation APIs | Sole evidence/gate-evaluation record owner; does not own review observations, qualify components, bind a run gate, or commit run state |
508:| `work_management` | Projects, canonical `WorkItemStatus`, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections | Core-SDLC transition API, GitHub intake, product/requirement links, governed-run/evidence integration |
556:| Core-SDLC projects/work/traceability | `work_management` | transition, portfolio, GitHub and projection adapters | `work_management` | Canonical work item, requirements/outcome links, and projections |
557:| Services/SLOs/support/lifecycle | `service_management` | service catalog and operational projections | `service_management` | Service objective and capability/support state |
786:│       │   │   └── environment_projection/
1008:runtime-domain projections; they may not become competing semantic sources.
1068:├── contract.yaml             # generated/validated registry projection
1113:projection, or experiment state and requires `HOST_EDGE_ADAPTER` evidence.
1120:| `identity_access` | `api/{commands,queries,views}.py`; `domain/{principals,authentication,sessions,nonces,data_classification,destination_facts,secret_refs,invariants}.py` | `application/{authentication_service,session_service,destination_fact_service,secret_projection_service}.py`; `application/ports/{authenticator,secret_backend,destination_resolver}.py` |
1122:| `work_management` | `api/{commands,queries,events,views}.py`; `domain/{projects,work_items,work_item_status,work_classes,outcome_refs,requirement_refs,configuration_refs,accountable_roles,queues,external_refs,projections,invariants}.py` | `application/{intake_service,transition_service,link_service,queue_service,projection_service}.py`; `application/ports/{issue_tracker,work_repository}.py` |
1128:| `process_assurance` | `api/{commands,queries,events,views}.py`; `domain/{tailoring_profiles,competence_profiles,audits,nonconformances,corrective_actions,process_measures,capability_assessments,capability_domain_projections,fleet_experiments,calibration_records,improvement_proposals,invariants}.py` | `application/{tailoring_service,audit_service,competence_service,corrective_action_service,capability_assessment_service,capability_projection_service,fleet_experiment_service}.py`; `application/ports/{process_evidence,training_registry,measurement_runner}.py` |
1137:| `repository_intelligence` | `api/{commands,queries,views}.py`; `domain/{repository_snapshot,symbols,dependencies,coverage,unsupported,freshness,findings}.py` | `application/{index_service,query_service,evidence_service}.py`; `application/ports/{parser,index_store}.py` |
1142:| `operations` | `api/{commands,queries,events,views}.py`; `domain/{health,alerts,incidents,capacity,reconciliation,service_levels,runbooks,lifecycle}.py` | `application/{health_service,alert_service,incident_service,reconciliation_service}.py`; `application/ports/{telemetry_query,notification}.py` |
1234:    the generated CODEOWNERS projection and actual package discovery must agree
1467:| `CapabilityAssessmentStatus` | `NOT_ASSESSED`, `IN_PROGRESS`, `COMPLETE`, `SUPERSEDED`; owned by `process_assurance` and shared by immutable control assessments and domain projections; neither acts as a gate |
2748:projection; it is never skipped into success. Retry reuses the same event ID
3147:how to query or prove outcome after a lost acknowledgement. “Probably happened”
3196:- credential projection records under policy-defined rules.
3199:smallest read-only projection for one bounded operation. Tool-bearing processes
3426:- no secret mounts except operation-specific projections;
3477:and tested. Restore is not complete until external effects, projections,
3764:- split-source reconciliation with Hermes/Kanban/projections;
3821:`TestPracticeProfile` carries ID projections only, and the validator reconciles
3909:  projection;
3923:or a lossy selected-field projection is `CONFLICT`.
4021:citation data, Mermaid sources and PNG projections, and three DOCX renderings.
4023:directory glob. HTML/SVG/PNG/DOCX renderings are non-normative projections;
4057:   projection of the selected lifecycle.
4058:9. `ranex-sdlc-full-spec.svg` is the generated diagram projection inspected
4142:registries/projections, deterministic evaluation records, and the named owner
[0m
[0m$ [0msed -n '1114,1125p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; echo "=== 3900-3930"; sed -n '3898,3930p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
| Context | Domain/API files | Application/port files |
|---|---|---|
| `policy` | `api/{commands,queries,views}.py`; `domain/{principals,roles,eligibility_rules,risk,policy_packages,activation,authorization_snapshots,human_decisions,waivers,invariants}.py` | `application/{authorization_service,risk_service,human_decision_service}.py`; `application/ports/{policy_engine,decision_store}.py` |
| `assurance` | `api/{commands,queries,views}.py`; `domain/{claims,evidence,checker_results,coverage,freshness,evidence_snapshots,gate_evaluations,invariants}.py` | `application/{ingestion_service,checker_service,snapshot_service,gate_evaluation_service}.py`; `application/ports/{checker_transport,evidence_repository}.py` |
| `module_governance` | `api/{commands,queries,views}.py`; `domain/{descriptors,interfaces,capabilities,grants,profiles,lifecycle,qualification_refs,invariants}.py` | `application/{catalog_service,activation_service,grant_service,profile_service}.py`; `application/ports/{module_factory,module_state_store}.py` |
| `identity_access` | `api/{commands,queries,views}.py`; `domain/{principals,authentication,sessions,nonces,data_classification,destination_facts,secret_refs,invariants}.py` | `application/{authentication_service,session_service,destination_fact_service,secret_projection_service}.py`; `application/ports/{authenticator,secret_backend,destination_resolver}.py` |
| `product_definition` | `api/{commands,queries,events,views}.py`; `domain/{actors,needs,hypotheses,capabilities,requirements,acceptance_examples,outcome_measures,validation_decisions,capability_status,invariants}.py` | `application/{discovery_service,requirements_service,validation_service,capability_lifecycle_service}.py`; `application/ports/{research_source,outcome_analytics}.py` |
| `work_management` | `api/{commands,queries,events,views}.py`; `domain/{projects,work_items,work_item_status,work_classes,outcome_refs,requirement_refs,configuration_refs,accountable_roles,queues,external_refs,projections,invariants}.py` | `application/{intake_service,transition_service,link_service,queue_service,projection_service}.py`; `application/ports/{issue_tracker,work_repository}.py` |
| `service_management` | `api/{commands,queries,events,views}.py`; `domain/{services,owners,supported_versions,slis,slos,error_budgets,support,maintenance_triggers,retirement_triggers,invariants}.py` | `application/{catalog_service,objective_service,support_service,lifecycle_trigger_service}.py`; `application/ports/{service_catalog,operational_evidence}.py` |
| `configuration_management` | `api/{commands,queries,events,views}.py`; `domain/{configuration_items,baselines,status_accounting,trace_links,audits,drift,generation_manifests,invariants}.py` | `application/{baseline_service,traceability_service,audit_service,drift_service,contract_generation_service}.py`; `application/ports/{configuration_scanner,baseline_store,contract_registry,code_generator}.py` |
| `supplier_governance` | `api/{commands,queries,events,views}.py`; `domain/{suppliers,dependencies,adoption_decisions,shared_responsibility,monitoring,concentration,exit_plans,invariants}.py` | `application/{adoption_service,monitoring_service,reassessment_service,exit_service}.py`; `application/ports/{dependency_inventory,supplier_probe}.py` |
=== 3900-3930

### 33.7 Exact architecture-element inventory and assessment subjects

`architecture-elements.json` is not a name/owner index. Every element in the
current 1,008-row architecture inventory is a closed, content-bound definition
subject with these required fields:

- `definition_contract_ref`: the exact canonical registry/schema row or
  normative decision fragment that owns the complete definition;
- `canonical_definition_row_digest`: RFC 8785 SHA-256 of that complete row,
  including all kind-specific semantics rather than a selected name/owner
  projection;
- `source_ref` and `source_file_digest`: repository-relative normative source
  and SHA-256 of its complete bytes; and
- bytewise-sorted unique `parent_element_refs` for every subordinate or
  generated element, empty only for a true root.

Kind-specific closure is mandatory. A state value names its parent state axis
and content-binds the complete value/transition row. An artifact type binds its
registered artifact/schema row. A path, dependency edge, boundary, rule,
fitness function, event, decision, capability, context, and practice element
binds its complete canonical registry/decision row and every semantic parent.
Generated children bind both their source definition and generating parent.
The 40 event elements bind the §17 envelope/payload catalog rows, not merely
their names. Duplicate parents, an unresolved parent, row/source digest drift,
or a lossy selected-field projection is `CONFLICT`.

`definition_status: DEFINED` is permitted only after those bindings validate.
`DEFINED_NAME_ONLY` is blocking. Each
`architecture-element-assessments.json` subject includes the complete element
object and digest, canonical row and source-file digests, and resolved parent
digests. A changed row, source byte, or parent makes the prior assessment
`STALE`; no score or neighboring element can compensate. Definition binding
[0m
[0m$ [0mgrep -n "^| \`governed_execution\` |" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
[0m
[0m$ [0msed -n '600,700p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -60; echo "=== find GE expanded tree"; grep -n "process_manager\|run_service\|workflow_service\|views.py" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -20
│       ├── foundation/
│       │   ├── ids.py
│       │   ├── canonical.py
│       │   ├── versions.py
│       │   ├── errors.py
│       │   └── time_types.py
│       ├── governed_execution/
│       │   ├── README.md
│       │   ├── contract.yaml
│       │   ├── api/
│       │   │   ├── commands.py
│       │   │   ├── queries.py
│       │   │   ├── integration_events.py
│       │   │   └── views.py
│       │   ├── domain/
│       │   │   ├── run.py
│       │   │   ├── workflow.py
│       │   │   ├── state.py
│       │   │   ├── commands.py
│       │   │   ├── events.py
│       │   │   ├── activities.py
│       │   │   ├── gates.py
│       │   │   ├── permits.py
│       │   │   ├── effects.py
│       │   │   ├── decisions.py
│       │   │   ├── governor.py
│       │   │   ├── termination.py
│       │   │   ├── progress_window.py
│       │   │   ├── invariants.py
│       │   │   └── reducer.py
│       │   ├── application/
│       │   │   ├── handlers/
│       │   │   ├── authorized_transition.py
│       │   │   ├── process_manager.py
│       │   │   ├── cancellation_service.py
│       │   │   ├── capability_bus.py
│       │   │   ├── reconciliation.py
│       │   │   ├── outbox_relay.py
│       │   │   └── ports/
│       │   │       ├── unit_of_work.py
│       │   │       ├── workflow_runtime.py
│       │   │       ├── worker_runtime.py
│       │   │       ├── activity_transport.py
│       │   │       ├── effect_dispatch.py
│       │   │       ├── policy_decision.py
│       │   │       ├── evidence_catalog.py
│       │   │       ├── artifact_store.py
│       │   │       ├── clock.py
│       │   │       ├── id_source.py
│       │   │       ├── secret_resolver.py
│       │   │       └── telemetry.py
│       │   └── adapters/
│       │       └── persistence/
│       │           └── sqlite/
│       │               ├── repository.py
│       │               ├── integration_event_outbox.py
│       │               └── migrations/
│       ├── policy/
│       ├── assurance/
│       ├── module_governance/
=== find GE expanded tree
613:│       │   │   └── views.py
633:│       │   │   ├── process_manager.py
1215:17. `governed_execution.application.process_manager` is orchestration-only. It
2767:| `EVENT-RUNCREATED` / `RunCreated` | `governed_execution` / `run_service`; `work_management`, `process_assurance` | `Run`; accepted unique run request, work item not terminal | `run_id:Id<Run>`, `work_item_id:Id<WorkItem>`, `initial_status:Enum<RunStatus>=PROPOSED`, `created_by_principal_id:Id<Principal>`, `workflow_request_ref:Ref<WorkflowRequest>` |
2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
2771:| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('schemas/events/governed_execution/activity-requested-v1.schema.json'));print(json.dumps(d['properties'].get('workflow_node_id'),indent=1))"
echo "=== workflow edge search"
grep -rn "workflow.*edge\|edge.*workflow\|WorkflowEdge\|workflow_edge" docs/architecture/ architecture/ schemas/ 2>/dev/null | head
echo "=== 'activity edge'"
grep -n "activity edge\|selected activity edge" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head
{
 "maxLength": 1024,
 "minLength": 1,
 "pattern": ".*\\S.*",
 "type": "string"
}
=== workflow edge search
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/deepseek-v4-pro-review.md:160:| Q2 | Should the workflow engine be a new bounded context (`pipeline_execution`) or a capability of the existing `governed_execution` context? | Affects ownership, dependency edges, and the atomic authority boundary. `governed_execution` already owns `RunStatus`, gate binding, grants, and permits. | Workflow engine implementation. |
=== 'activity edge'
2774:| `EVENT-ACTIVITYRESOLVED` / `ActivityResolved` | `governed_execution` / `activity_resolution_service`; `assurance`, `work_management` | `Activity`; typed result normalized and every required effect has the attempt disposition/reconciliation required by the selected activity edge | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `run_result_ref:Ref<RunResult>`, `resolution:Enum<ActivityStatus>` restricted by `ActivityResolution`, `required_effect_ids:Set<EffectId>[0..N]` (empty exactly for a declared pure zero-effect activity), `resolved_at:Utc` |
[0m
[0m$ [0mls config 2>&1; echo ===; ls schemas/* -d; echo ===; grep -rln "workflow" schemas/ | head; echo "=== invariant 14 line"; grep -n "The same workflow/interpreter versions and ordered recorded inputs" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md; grep -n "OUTCOME_UNKNOWN\` is a first-class" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
ls: cannot access 'config': No such file or directory
===
schemas/architecture
schemas/artifacts
schemas/assurance
schemas/authority
schemas/common
schemas/events
schemas/execution
schemas/fixtures
schemas/fleet
schemas/lifecycle
schemas/planning
schemas/process
schemas/research
schemas/resources
schemas/review
schemas/work
===
schemas/authority/permit-v1.schema.json
schemas/execution/run-result-v1.schema.json
schemas/fixtures/negative/state-transition-contract-cases.json
schemas/fixtures/semantic/adr0008-synthetic-definition-contract.json
schemas/common/exact-subject-v1.schema.json
schemas/work/task-packet-v1.schema.json
schemas/events/work_management/run-requested-for-work-item-v1.schema.json
schemas/events/governed_execution/activity-requested-v1.schema.json
schemas/events/governed_execution/workflow-pinned-v1.schema.json
schemas/events/governed_execution/run-created-v1.schema.json
=== invariant 14 line
269:14. The same workflow/interpreter versions and ordered recorded inputs replay to
273:16. `OUTCOME_UNKNOWN` is a first-class result and must enter reconciliation.
[0m
[0m$ [0mgrep -n "attempt\|dispatch" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | grep -in "run\b" | head -10; echo "=== worker attempt owner"; grep -n "WorkerAttempt" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -5
14:565:| Agent collaboration | `agent_collaboration` | role-scoped official leaf runtimes; Hermes is excluded from live dispatch | assignment/run handoff state in `agent_collaboration`; worker-module activation in `module_governance` | Worker result/proposal |
29:1511:`CANCELLED` are terminal for one run attempt. Retry creates a new `RunId`
30:1512:linked to the prior attempt. A terminal run remains only input to the
47:2628:- one work item may have many `Run` attempts; `governed_execution` alone
52:2773:| `EVENT-ACTIVITYDISPATCHED` / `ActivityDispatched` | `governed_execution` / `dispatch_service`; `agent_collaboration`, `resource_governance` | `Activity`; authorization allowed, assignment/lease/reservation current | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `assignment_ref:Ref<AgentAssignment>`, `worker_attempt_id:Id<WorkerAttempt>`, `lease_ref:Ref<WorkerLease>`, `dispatch_attempt:UInt` |
53:2774:| `EVENT-ACTIVITYRESOLVED` / `ActivityResolved` | `governed_execution` / `activity_resolution_service`; `assurance`, `work_management` | `Activity`; typed result normalized and every required effect has the attempt disposition/reconciliation required by the selected activity edge | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `run_result_ref:Ref<RunResult>`, `resolution:Enum<ActivityStatus>` restricted by `ActivityResolution`, `required_effect_ids:Set<EffectId>[0..N]` (empty exactly for a declared pure zero-effect activity), `resolved_at:Utc` |
=== worker attempt owner
1721:    retry_semantics: "Retry creates new linked AssignmentId and WorkerAttemptId with a higher fencing epoch"
1961:    retry_semantics: "FAILED_RETRYABLE redispatches same ActivityId with new WorkerAttemptId and incremented attempt; exhaustion proves FAILED_PERMANENT"
2773:| `EVENT-ACTIVITYDISPATCHED` / `ActivityDispatched` | `governed_execution` / `dispatch_service`; `agent_collaboration`, `resource_governance` | `Activity`; authorization allowed, assignment/lease/reservation current | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `assignment_ref:Ref<AgentAssignment>`, `worker_attempt_id:Id<WorkerAttempt>`, `lease_ref:Ref<WorkerLease>`, `dispatch_attempt:UInt` |
[0m
[0m$ [0mls schemas/events/work_management/; echo ===; python3 -c "
import json;d=json.load(open('schemas/events/work_management/run-requested-for-work-item-v1.schema.json'));print(list(d['properties'].keys()), d.get('required'))"; echo ===; grep -n "RUNREQUESTEDFORWORKITEM\|RunRequestedForWorkItem" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
follow-up-work-linked-v1.schema.json
operational-evidence-linked-v1.schema.json
outcome-decision-linked-v1.schema.json
outcome-requirement-refs-bound-v1.schema.json
release-evidence-linked-v1.schema.json
risk-lane-bound-v1.schema.json
run-evidence-linked-v1.schema.json
run-requested-for-work-item-v1.schema.json
work-item-blocked-v1.schema.json
work-item-cancelled-v1.schema.json
work-item-classified-v1.schema.json
work-item-closed-v1.schema.json
work-item-created-v1.schema.json
work-item-transitioned-v1.schema.json
work-item-unblocked-v1.schema.json
===
['requested_at', 'requested_subject_digest', 'requested_subject_ref', 'run_request_id', 'work_item_id', 'workflow_request_ref'] ['work_item_id', 'run_request_id', 'requested_subject_ref', 'requested_subject_digest', 'workflow_request_ref', 'requested_at']
===
2800:| `EVENT-RUNREQUESTEDFORWORKITEM` / `RunRequestedForWorkItem` | `work_management` / `run_request_service`; `governed_execution` | `WorkItem`; item ready, no conflicting active run, exact subject/profile bound | `work_item_id:Id<WorkItem>`, `run_request_id:Id<RunRequest>`, `requested_subject_ref:ArtifactRef`, `requested_subject_digest:Sha256`, `workflow_request_ref:Ref<WorkflowRequest>`, `requested_at:Utc` |
3035:  - event_name: "RunRequestedForWorkItem"
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('architecture/contracts/test-behaviors.json'));print(list(d.keys())); print(len(d.get('entries',[])))"; echo ===; grep -n "^| \`FIX-\|fixed_decision\|FIX-" docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md | head -40
['active_entry_count', 'entries', 'entry_count', 'generated_by', 'registry_id', 'runtime_authority_resolution_status', 'source_bijection_status', 'source_count', 'source_pattern', 'status', 'version']
0
===
[0m
[0m$ [0mgrep -n "decision_id\|DEC-" docs/architecture/decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md | head -40; echo ===; python3 -c "
import json;d=json.load(open('architecture/contracts/decisions.json'));e=d['entries'];print(len(e));print([x.get('decision_id') or x.get('id') for x in e][:60])"
14:| Supersedes | No decision ID; ADR-0011 supersedes the selected meaning and governing ADR for rows `DEC-RANEX-017`, `025`, `026`, and `027` |
25:require exactly 29 unique `decision_id` values in the contiguous range
26:`DEC-RANEX-001` through `DEC-RANEX-029`, resolve every named ADR and fitness
34:  - decision_id: "DEC-RANEX-001"
42:  - decision_id: "DEC-RANEX-002"
50:  - decision_id: "DEC-RANEX-003"
58:  - decision_id: "DEC-RANEX-004"
66:  - decision_id: "DEC-RANEX-005"
74:  - decision_id: "DEC-RANEX-006"
82:  - decision_id: "DEC-RANEX-007"
90:  - decision_id: "DEC-RANEX-008"
98:  - decision_id: "DEC-RANEX-009"
106:  - decision_id: "DEC-RANEX-010"
114:  - decision_id: "DEC-RANEX-011"
122:  - decision_id: "DEC-RANEX-012"
130:  - decision_id: "DEC-RANEX-013"
138:  - decision_id: "DEC-RANEX-014"
146:  - decision_id: "DEC-RANEX-015"
154:  - decision_id: "DEC-RANEX-016"
162:  - decision_id: "DEC-RANEX-017"
170:  - decision_id: "DEC-RANEX-018"
178:  - decision_id: "DEC-RANEX-019"
186:  - decision_id: "DEC-RANEX-020"
194:  - decision_id: "DEC-RANEX-021"
202:  - decision_id: "DEC-RANEX-022"
210:  - decision_id: "DEC-RANEX-023"
218:  - decision_id: "DEC-RANEX-024"
226:  - decision_id: "DEC-RANEX-025"
234:  - decision_id: "DEC-RANEX-026"
242:  - decision_id: "DEC-RANEX-027"
250:  - decision_id: "DEC-RANEX-028"
258:  - decision_id: "DEC-RANEX-029"
===
29
['DEC-RANEX-001', 'DEC-RANEX-002', 'DEC-RANEX-003', 'DEC-RANEX-004', 'DEC-RANEX-005', 'DEC-RANEX-006', 'DEC-RANEX-007', 'DEC-RANEX-008', 'DEC-RANEX-009', 'DEC-RANEX-010', 'DEC-RANEX-011', 'DEC-RANEX-012', 'DEC-RANEX-013', 'DEC-RANEX-014', 'DEC-RANEX-015', 'DEC-RANEX-016', 'DEC-RANEX-017', 'DEC-RANEX-018', 'DEC-RANEX-019', 'DEC-RANEX-020', 'DEC-RANEX-021', 'DEC-RANEX-022', 'DEC-RANEX-023', 'DEC-RANEX-024', 'DEC-RANEX-025', 'DEC-RANEX-026', 'DEC-RANEX-027', 'DEC-RANEX-028', 'DEC-RANEX-029']
[0m
[0m$ [0mpython3 -c "
import json;d=json.load(open('architecture/contracts/decisions.json'))
for e in d['entries']:
    print(e['decision_id'],'|', e.get('selected','')[:150])"
DEC-RANEX-001 | release-pinned modular monolith with bounded-context packages
DEC-RANEX-002 | Core SDLC governs; AI L0-L12 is subordinate execution
DEC-RANEX-003 | frozen registered references are advisory practice inputs under Core SDLC
DEC-RANEX-004 | each packet binds applicability, behavior, deviations, and verification
DEC-RANEX-005 | retired and non-authoritative
DEC-RANEX-006 | Hermes-derived fork with blocking ancestry, history, license, and provenance preflight
DEC-RANEX-007 | new authority/domain/application core has no inherited-Hermes dependency
DEC-RANEX-008 | strangler migration inside the attributed fork
DEC-RANEX-009 | work_management alone owns WorkItemStatus
DEC-RANEX-010 | governed_execution authority cell owns run, gate binding, permit, and effect intent
DEC-RANEX-011 | single local SQLite authority database with logical ownership, journal, and outbox
DEC-RANEX-012 | selective governed-execution replay journal; product is not wholly event sourced
DEC-RANEX-013 | local durable runner behind a stable runtime port
DEC-RANEX-014 | declared at-least-once or at-most-once attempts with idempotency and reconciliation
DEC-RANEX-015 | blocking proof failure denies visibly
DEC-RANEX-016 | models produce proposals and observations only
DEC-RANEX-017 | Ranex control services alone orchestrate deterministic bounded fan-out/join; all model and harness workers are leaf-only; each assignment receives a t
DEC-RANEX-018 | shipped behind stable internal interfaces
DEC-RANEX-019 | lower-trust out-of-process capability-scoped protocol outside authority
DEC-RANEX-020 | excluded
DEC-RANEX-021 | CLI, TUI, loopback web, GitHub edge, and text-phone delivery port
DEC-RANEX-022 | Telegram first adapter behind channel-neutral contracts
DEC-RANEX-023 | mapped optional adapter, inactive
DEC-RANEX-024 | excluded; web binds to loopback
DEC-RANEX-025 | one explicit qualified route/model/runtime per assignment through a Ranex-owned official typed runtime adapter; eligible local individual subscription
DEC-RANEX-026 | Hermes/Nous is provenance, compatibility, and reference only: no live inference, parent-agent model loop, Portal/model route, credential/entitlement, 
DEC-RANEX-027 | release-pinned catalog cannot activate or mutate a route; model/provider/adapter fallback, provider subagents, and auxiliary model calls are disabled
DEC-RANEX-028 | deterministic policy derives risk; worker input is untrusted observation
DEC-RANEX-029 | human-controlled landing
[0m
[0m$ [0msed -n '2620,2645p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
The orthogonal legal-hold contract adds its separately enumerated 51 cases, so
the combined §16.1 state/event/hold denominator is exactly `10,027`.

### 16.2 Core-SDLC and execution boundary

- `product_definition` owns capabilities, needs, requirements, outcomes, and
  product validation.
- `work_management` alone transitions `WorkItemStatus`.
- one work item may have many `Run` attempts; `governed_execution` alone
  transitions each `RunStatus`.
- `operations` owns incidents; `release_management` owns release/update state;
  `service_management` owns service commitments and lifecycle triggers.
- maintenance, retirement, and incident response create linked work items with
  the applicable `WorkClass`; they do not smuggle new values into
  `WorkItemStatus`.
- a run success, merge, release, model verdict, board move, incident mitigation,
  or capability state change is evidence/input to a work transition, never the
  transition itself.
- cross-aggregate mappings and invalidation rules live in
  `lifecycle-crosswalks.yaml` and `invalidation-graph.yaml`.

`RuleStage` is derived from the owning lifecycle state solely to select
applicable policy. It is not independently writable.

### 16.3 Gate namespaces
[0m
[0m$ [0mgit branch --show-current; git rev-parse HEAD; echo "=== crosswalk files"; ls docs/architecture/*.yaml architecture/*.yaml 2>&1 | head; find . -name "lifecycle-crosswalks.yaml" -o -name "invalidation-graph.yaml" 2>/dev/null | head
bootstrap/pre-upstream
a573502a87e0599cf6e5f9456c348bf1a7686382
=== crosswalk files
ls: cannot access 'docs/architecture/*.yaml': No such file or directory
ls: cannot access 'architecture/*.yaml': No such file or directory
[0m
[0m$ [0mfind . -name package.json -not -path "*/node_modules/*" -not -path "./.git/*" 2>/dev/null | head; echo "--- ls root of main"; ls -a | head -20; echo "--- schema-registry execution-graph"; grep -c "execution-graph\|graph-projection" architecture/contracts/schema-registry.json; echo "--- packages dir"; ls packages 2>&1
./.claude/worktrees/phase-2-runtime-bootstrap/plugins/platforms/photon/sidecar/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/web/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/website/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/apps/desktop/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/apps/shared/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/apps/bootstrap-installer/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/scripts/whatsapp-bridge/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/tests-js/package.json
./.claude/worktrees/phase-2-runtime-bootstrap/ui-tui/package.json
--- ls root of main
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
--- schema-registry execution-graph
0
--- packages dir
ls: cannot access 'packages': No such file or directory
[0m
## Objective
- Act as adversarial reviewer to break (not endorse) the proposal `docs/research/deterministic-run-graph-visualization-research-2026-07-30.md` (read-only deterministic run-graph visualization for governed Ranex runs launched from a Kanban work item).
- Final deliverable is raw findings data with sections: `Findings`, `Dissolved`, `Assumed-capability ledger`, `External verification`, `Inferences`, `Coverage` — not prose.

## Important Details
- Governing corpus: 14 ADRs in `docs/architecture/decisions/`; architecture docs in `docs/architecture/`; generated contracts in `architecture/contracts/`; `schemas/`.
- Prompt stated ADR-0014 is "PROPOSED, non-authoritative" — **actual state contradicts this**: `ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md` header says `Status: ACCEPTED`, and `architecture/contracts/accepted-adrs.json` was modified to include ADR-0014 as ACCEPTED (digist `sha256:823a12d2...`). Treat as factual discrepancy.
- Read-only constraint: do not modify/create/delete any file.
- `IMPLEMENTATION_START_READY` not declared: `architecture/contracts/readiness-assessments.json` → `implementation_start_authorized: false`, `implementation_start_state: NOT_ASSESSED`, `production_state: NOT_ASSESSED`.
- Three claim types must be distinguished: measured/verified in repo (`path:line`), verified external (URL), unverified.
- Each finding: severity (BLOCKER/MAJOR/MINOR), one-sentence claim, evidence (`path:line` or URL), strongest counter-argument.
- Kernel tracer lives in separate worktree `.claude/worktrees/kernel-tracer` on branch `feature/kernel-tracer` (untracked `src/`, `tests/`); inspected there.
- Proposal header: `Status: REVIEWED DRAFT RESEARCH PROPOSAL — NON-NORMATIVE; NOT IMPLEMENTATION AUTHORITY`; `Decision effect: None`; cites `ARCH-RANEX-001 v2.10.0`; names `@xyflow/react` + `@dagrejs/dagre` as leading candidates (lines 27-28).

## Work State
### Completed
- Read proposal header/§1 only (file truncated: omitted 40312 chars beyond line ~28; full body NOT yet read).
- Surveyed authority kernel: `governed_execution` sole run/execution-transition authority (`HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:221,244,497,2627-2634`); `work_management` sole `WorkItemStatus` owner (`:220,508,1455,2627`); web-dashboard is read-only presentation, loopback-only, no public dashboard (`:235,1160-1181`, §12.2).
- Workflow semantics: only sequence/deterministic-choice/activity/evidence-gate/durable-wait/timer/retry/cancel/compensation/reconciliation/terminal are supported; parallel/fan-out/map/dynamic-graph-mutation are extension points with NO authority until specified+tested (`:3088-3101`).
- `OUTCOME_UNKNOWN` is first-class, must enter reconciliation (`:273,1474,1966`).
- `source-divergence-detected-v1.schema.json` exists (divergence event). `run-requested-for-work-item-v1.schema.json` links `work_item_id`↔`run_id` (arch `:2800`).
- Kernel-tracer read path: `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py` reads SQLite; `domain/execution.py` has `work_item_id` (`:55`), `events.py` (`:61`); `work_management/domain/transitions.py` has `WorkItemStatus` enum. `reduce_execution` replays events.
- `context-dependency-edges.json`: `EDGE-DELIVERY-GE` (delivery→governed_execution, SYNC_COMMAND, CALLEE_TRANSACTION_ONLY) exists; GE fan-out 10 / fan-in 3 (paper, `NOT_ASSESSED`). Projection read would be query-only.
- `paths.json` has NO `apps/web-dashboard/**` path (only `src/ranex/**`, `tests/**`, `packages/generated-contracts/**`, `architecture/generated/**`). `schema-registry.json` has NO execution-graph/projection schema. `identities.json` has NO graph/projection identity type.
- ADR-0013 `HERMES-OWNER-DECISION-001`..`020` all `OWNER_DECISION_REQUIRED`, `absence_outcome: BLOCK`, none resolved (incl. `HERMES-OWNER-DECISION-001` canonical workflow/event schema + upcaster policy, blocking `IMPLEMENTATION_START`).
- Verified external libraries (npm registry + GitHub API, 2026-07-30):
  - `@xyflow/react` 12.11.2, **MIT** (registry.npmjs.org). React Flow attribution removal requires paid Pro (reactflow.dev/remove-attribution).
  - `@dagrejs/dagre` 3.0.0, **MIT** (npm). Note old `dagre` 0.8.5 (2019) still `latest` on npm — version-confusion risk.
  - `elkjs` 0.12.0, **`EPL-2.0 OR GPL-3.0-or-later`** (npm `license` field; GitHub API `NOASSERTION`) — dual copyleft; potential commercial encumbrance under `LICENSE-RANEX.md` (source-available, all-rights-reserved, commercial use restricted).
  - Prior-art repos verified live: GitHub Actions visualization graph (docs.github.com/en/actions/how-tos/monitor-workflows 200), GitLab pipeline graph (docs.gitlab.com/ci/pipelines 200), go-gitea/gitea (MIT, `WorkflowGraph.vue` at commit e80a62f… 200), apache/airflow (Apache-2.0, uses `@xyflow/react`+`elkjs` 200), argoproj/argo-workflows (Apache-2.0, uses `dagre` 200), dagster-io/dagster (Apache-2.0, uses `dagre` at commit 014641b… 200), kestra-io/kestra (Apache-2.0, uses Vue Flow+`dagre` 200). `dagu-org/dagu` redirected to `dagucloud/dagu` **GPL-3.0**.
- `LICENSE-RANEX.md`: source-available, all-rights-reserved; commercial/business use prohibited without written permission.
- SQLite concurrency verified: writer `BEGIN IMMEDIATE` + COMMIT fails with `OperationalError database is locked` while reader holds SHARED lock; ROLLBACK does not reuse AUTOINCREMENT sequence (supports reader/projection integrity but sequence gaps possible).

### Active
- Investigation/evidence-gathering complete for most attack surfaces; final findings output NOT yet emitted.
- Proposal body (§4 fidelity claims, §13 MVP boundary, §14 acceptance/falsification tests, purpose/inferential-chain wording, full external-library list) NOT yet read — needed to complete attack surfaces 1, 4, 5, 7.

### Blocked
- Subject proposal file truncated at read time; full text (sections 4, 13, 14, etc.) never retrieved. Must re-read remainder before finalizing.
- (none other)

## Next Move
1. Re-read `docs/research/deterministic-run-graph-visualization-research-2026-07-30.md` from line ~29 onward to capture §4 assertions, §13 MVP, §14 tests, inferential-chain/purpose wording, and complete external-library/prior-art list.
2. Emit the final adversarial review raw findings: `Findings`, `Dissolved`, `Assumed-capability ledger` (capability/status/citation), `External verification` (claim/verdict/URL), `Inferences`, `Coverage`.

## Relevant Files
- `docs/research/deterministic-run-graph-visualization-research-2026-07-30.md` — subject proposal (must read remainder)
- `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` — authority kernel, dashboard rules, workflow semantics, OUTCOME_UNKNOWN, divergence
- `docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md` — readiness tiers NOT_ASSESSED
- `docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md` — HERMES-OWNER-DECISION-001..020 unresolved
- `docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md` — ACCEPTED (contradicts prompt premise)
- `architecture/contracts/accepted-adrs.json` — ADR-0014 now ACCEPTED
- `architecture/contracts/readiness-assessments.json` — implementation_start_authorized=false
- `architecture/contracts/context-dependency-edges.json` — EDGE-DELIVERY-GE; GE fan-out/fan-in paper counts
- `architecture/contracts/paths.json` — no apps/web-dashboard path
- `architecture/contracts/schema-registry.json` — no graph-projection schema
- `architecture/contracts/identities.json` — no graph/projection identity
- `schemas/events/governed_execution/source-divergence-detected-v1.schema.json` — divergence event
- `schemas/events/work_management/run-requested-for-work-item-v1.schema.json` — work_item↔run link
- `.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py` — read path
- `.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py`, `events.py` — work_item_id, status
- `.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py` — WorkItemStatus enum
- `LICENSE-RANEX.md` — commercial-use restriction
- External: registry.npmjs.org/@xyflow/react, @dagrejs/dagre, elkjs; github.com/xyflow/xyflow, dagrejs/dagre, kieler/elkjs, go-gitea/gitea, apache/airflow, argoproj/argo-workflows, dagster-io/dagster, kestra-io/kestra, dagucloud/dagu; docs.github.com/en/actions/how-tos/monitor-workflows; docs.gitlab.com/ci/pipelines; reactflow.dev/remove-attribution
Continue if you have next steps, or stop and ask for clarification if you are unsure how to proceed.
[0m→ [0mRead docs/research/deterministic-run-graph-visualization-research-2026-07-30.md[90m [offset=29][0m
[0m
[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && grep -rIl "workflow_definition\|WorkflowDefinition" src/ranex/governed_execution 2>/dev/null; echo "---STATUS ENUMS---"; grep -rIn "class RunStatus\|class ActivityStatus\|class GateOutcome\|class EffectStatus\|RunStatus\b" src/ranex/governed_execution 2>/dev/null | head -40
---STATUS ENUMS---
[0m
[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && ls src/ranex/governed_execution/domain 2>/dev/null; echo "---"; find src/ranex/governed_execution -iname "*workflow*" 2>/dev/null; echo "---PINNED/INTERPRETER---"; grep -rIn "interpreter_version\|pinned\|workflow_definition_digest" src/ranex/governed_execution 2>/dev/null | head
application_control.py
events.py
execution.py
__init__.py
__pycache__
status.py
---
---PINNED/INTERPRETER---
[0m
I now have the full proposal. Let me ground a few critical claims in the kernel before finalizing the adversarial findings.
[0m→ [0mRead .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/status.py
[0m
[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && grep -rIn "workflow\|Workflow\|interpreter\|pinned\|WorkflowDefinition" src/ranex 2>/dev/null | head -30; echo "===EXECUTION.PY head==="; sed -n '1,80p' src/ranex/governed_execution/domain/execution.py 2>/dev/null
src/ranex/governed_execution/domain/execution.py:57:    workflow_request_ref: str
src/ranex/governed_execution/domain/execution.py:117:            workflow_request_ref=event.workflow_request_ref,
src/ranex/governed_execution/domain/events.py:63:    workflow_request_ref: str
src/ranex/governed_execution/domain/events.py:77:        _require_text(self.workflow_request_ref, field="workflow_request_ref")
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:40:        "workflow_request_ref",
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:64:        "workflow_request_ref": execution.workflow_request_ref,
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:113:        workflow_request_ref=_require_string(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:114:            document["workflow_request_ref"],
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:115:            "workflow_request_ref",
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:142:                "workflow_request_ref": event.workflow_request_ref,
===EXECUTION.PY head===
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import (
    ExecutionBlocked,
    ExecutionCancelled,
    ExecutionCreated,
    ExecutionEvent,
    ExecutionFailed,
    ExecutionMarkedReady,
    ExecutionResumed,
    ExecutionStarted,
    ExecutionSucceeded,
    ExecutionUnblocked,
    ExecutionWaited,
)
from ranex.governed_execution.domain.status import ExecutionStatus


class InvalidExecutionTransition(ValueError):
    """An event cannot evolve the supplied execution state."""


LEGAL_STATUS_TRANSITIONS = frozenset(
    {
        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    }
)


@dataclass(frozen=True, slots=True)
class Execution:
    execution_id: Identity
    work_item_id: Identity
    created_by_principal_id: Identity
    workflow_request_ref: str
    status: ExecutionStatus
    version: int
    last_event_id: Identity
    updated_at: str
    blocked_from_status: ExecutionStatus | None = None


def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    return InvalidExecutionTransition(
        f"{state.status.value} cannot apply {type(event).__name__}"
    )


def _advance(
    state: Execution,
    event: ExecutionEvent,
    target_status: ExecutionStatus,
    *,
    blocked_from_status: ExecutionStatus | None = None,
) -> Execution:
    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
        raise _invalid(state, event)
    return replace(
[0m
# Adversarial Review — `deterministic-run-graph-visualization-research-2026-07-30.md`

Read-only review. Breaks the proposal; does not endorse it.

## Findings

**F-01 — BLOCKER — Projection's closed inputs do not exist in the implemented kernel.**
The `feature/kernel-tracer` worktree models execution as one flat aggregate (`Execution`, `execution.py:46-66`) holding only `workflow_request_ref: str` and `ExecutionStatus` (`status.py:6`). There is no `WorkflowDefinition`, no Activity/Gate/Permit/Effect/reconciliation sub-records, no stable node IDs, no digest, no interpreter version. §7.1/§7.2 assume all of these as join inputs.
*Counter:* the architecture narration (HERMES_GROUND_ZERO) describes these concepts as designed; the worktree is mid-implementation. Against the only buildable canonical state, the projection cannot be derived.

**F-02 — BLOCKER — An unresolved owner decision gates the dependency.**
ADR-0013 `HERMES-OWNER-DECISION-001` (canonical workflow/event schema + upcaster policy) is `OWNER_DECISION_REQUIRED` with `absence_outcome: BLOCK`, which blocks `IMPLEMENTATION_START` (`readiness-assessments.json`: `implementation_start_authorized=false`). The `topology_digest` closed input (definition digest, interpreter version, stable node IDs, choice conditions) *is* that canonical workflow/event schema. The proposal never cites ADR-0013.
*Counter:* §18 says "record an RFC/ADR" — but an RFC cannot override an owner BLOCK; the decision must resolve first.

**F-03 — MAJOR — Canonical status types referenced by the visual-state mapping do not exist.**
§9 maps from `RunStatus`, `ActivityStatus`, `GateOutcome`, `EffectStatus`; the kernel has only `ExecutionStatus`. `ActivityStatus`/`GateOutcome`/`EffectStatus` are absent from `governed_execution`. `OUTCOME_UNKNOWN` is a first-class *effect*-level result per architecture (HERMES_GROUND_ZERO:273,1474,1966), not an `ExecutionStatus` (kernel omits it: `status.py`). The "total, server-owned mapping" maps from types with no upstream.
*Counter:* these are research sketches; target types will be defined by the same RFC/ADR.

**F-04 — MAJOR — ELK license understated.**
§11/§19 name only `EPL-2.0` for ELK/elkjs, but npm `license` is `EPL-2.0 OR GPL-3.0-or-later` (dual; GitHub API `NOASSERTION`). `LICENSE-RANEX.md` is source-available/all-rights-reserved with commercial-use restriction; distributing elkjs under the GPL-3.0 alternative would be incompatible. "EPL-2.0 qualification" omits the GPL alternative and an explicit EPL-only election.
*Counter:* elkjs is only an upgrade candidate; the OR lets one elect EPL-2.0 — but the proposal never records that election.

**F-05 — MAJOR — Dagre refutation is partially wrong; legacy `latest` trap remains.**
§17.3 cites `@dagrejs/dagre v2.0.0 (2025)`; npm current latest is **3.0.0 (2026)** — stale citation. More importantly the legacy `dagre` package still holds npm `latest` at **0.8.5 (2019)**, so DeepSeek's "stale 2019" premise is TRUE for that package. The proposal warns about this exact confusion in §11 yet its refutation points to a *different* package without noting the legacy `latest` trap.
*Counter:* a maintained `@dagrejs/dagre` exists — the refutation's core point holds; version drift is minor.

**F-06 — MINOR — React Flow attribution removal is paid.**
§11 calls React Flow "MIT" beside Dagre; React Flow's MIT license permits removing on-screen attribution only via a paid Pro subscription (reactflow.dev/remove-attribution). "Both MIT" understates the clean-UI cost.
*Counter:* attribution can stay; cost is opt-in.

**F-07 — MINOR — Frozen-revision file paths may have drifted.**
§19 cites `tree/<rev>/<path>` for Airflow/Argo/Kestra/Dagster/Gitea; Airflow recently reorganized its UI under `airflow-core/`, so the cited path may not resolve at that revision (root repos verified 200; specific UI blob path unverified). Weakens "proven implementation" precision.
*Counter:* the projects demonstrably exist and use the named libraries.

**F-08 — MINOR — No transport exists in the kernel at all.**
§10 concedes SSE is unregistered, but the kernel-tracer `pyproject` deps are only `PyYAML` — no HTTP/transport/auth server. The "compatible first tracer" (authenticated polling) also requires building transport from scratch; the framing understates that zero transport exists.
*Counter:* §10 does say an adapter must be registered.

**F-09 — MINOR — §4 "accepted architecture already establishes" overclaims vs contracts.**
Authority boundaries are described in HERMES_GROUND_ZERO, but the concrete artifacts the proposal itself says must be registered (schema under `schemas/execution/`, generated contracts, `paths.json` entry, identity type) do NOT exist (`schema-registry.json`, `paths.json`, `identities.json` checked). Self-aware in §7.1; §4 framing can mislead.

## Dissolved
- "Invent a graph framework / import a workflow engine" — dissolved: prior art (Airflow, Argo, Gitea, Kestra, Dagster) confirms React Flow + Dagre suffices (repos verified live). §5/§6.
- "Layout must recompute every status update" — dissolved: topology separable from status; layout keyed by `topology_digest` (§7.2/§10).
- "Loopback deployment unestablished" — dissolved: ARCH-RANEX-001 fixes web-dashboard loopback-only (HERMES_GROUND_ZERO:235); §17.3 correctly refutes.
- "Stale Dagre (2019) = no maintained layout lib" — partially dissolved: `@dagrejs/dagre` is maintained, but the legacy `dagre@0.8.5` `latest` trap (F-05) is real.

## Assumed-capability ledger
| Capability | Status | Citation |
|---|---|---|
| Canonical `WorkflowDefinition` w/ stable node IDs, kinds, choice conditions | NOT IMPLEMENTED | `execution.py:46-66`; no workflow_definition module |
| `workflow_definition_digest` / `workflow_interpreter_version` pins | NOT IMPLEMENTED (opaque `workflow_request_ref: str`) | `execution.py:57`; `status.py` |
| Activity / Gate / Permit / Effect / reconciliation sub-records | NOT IMPLEMENTED | `events.py` execution-level only |
| `ActivityStatus` / `GateOutcome` / `EffectStatus` enums | NOT FOUND | `status.py` has only `ExecutionStatus` |
| `OUTCOME_UNKNOWN` at execution level | NOT in kernel; effect-level only per arch | `status.py`; HERMES_GROUND_ZERO:273,1474,1966 |
| HTTP/transport/auth server in kernel | ABSENT (deps: PyYAML only) | kernel-tracer `pyproject` |
| Projection schema under `schemas/execution/` | NOT REGISTERED | `schema-registry.json` |
| `apps/web-dashboard` path / graph identity type | NOT REGISTERED | `paths.json`; `identities.json` |
| `HERMES-OWNER-DECISION-001` (canonical workflow/event schema) | OWNER_DECISION_REQUIRED, BLOCK | ADR-0013; `readiness-assessments.json` |
| `IMPLEMENTATION_START_READY` | NOT declared (`implementation_start_authorized=false`) | `readiness-assessments.json` |
| ADR-0014 (Python/perf) | ACCEPTED — contradicts prompt's "PROPOSED" | `ADR-0014`; `accepted-adrs.json` |

## External verification
| Claim | Verdict | Source |
|---|---|---|
| @xyflow/react 12.11.2, MIT | VERIFIED | registry.npmjs.org/@xyflow/react |
| @dagrejs/dagre latest 3.0.0, MIT (proposal cites v2.0.0) | VERIFIED w/ drift | registry.npmjs.org/@dagrejs/dagre |
| legacy `dagre` 0.8.5 (2019) `latest` | VERIFIED (supports F-05) | registry.npmjs.org/dagre |
| elkjs 0.12.0 `EPL-2.0 OR GPL-3.0-or-later` | VERIFIED (proposal names only EPL-2.0) | registry.npmjs.org/elkjs; github kieler/elkjs (NOASSERTION) |
| React Flow attribution removal = paid Pro | VERIFIED | reactflow.dev/remove-attribution |
| Gitea WorkflowGraph.vue @ e80a62f | VERIFIED 200 | github go-gitea/gitea |
| Apache Airflow (uses @xyflow/react + elkjs) | VERIFIED 200 (specific UI path unverified) | github apache/airflow |
| Argo / Kestra / Dagster (Apache-2.0, dagre) | VERIFIED 200 | github argoproj/argo-workflows, kestra-io/kestra, dagster-io/dagster |
| Dagu GPL-3.0 | VERIFIED | github dagucloud/dagu (redirect from dagu-org/dagu) |
| GitHub Actions / GitLab CI graph docs | VERIFIED 200 | docs.github.com; docs.gitlab.com |

## Inferences
- The proposal is internally consistent and well self-gated as *research* ("register via RFC/ADR before implementation"; "do not claim conformance until readiness passes"). The break is not in its logic but in its **unstated dependency on a canonical workflow/activity/gate/effect model that is neither implemented nor decision-closed.**
- Because `workflow_request_ref` is an opaque string with no digest, the integrity anchor (`topology_digest` over definition digest) has no upstream source of truth today; the determinism guarantees in §7.2/§14.1 are ungrounded against buildable state.
- License posture in §11/§19 is careless on ELK (dual copyleft) and silent on React Flow attribution cost — both material for `supplier_governance` under a source-available license.
- Net: architecturally sound and the authority-preserving rules (§4 "cannot", §9 fail-closed) are correct. It is **not buildable from this research alone** — the blocking gap is an unresolved owner decision (HERMES-OWNER-DECISION-001) plus an unimplemented workflow/activity model, not merely "missing contracts."

## Coverage
- **Attacked:** determinism grounding (F-01/F-02/F-03), fidelity to corpus (F-03/F-08/F-09), external-library/license claims (F-04/F-05/F-06/F-07 + verification), divergent-authority risk (§4 "cannot" list is sound — no new authority claimed).
- **Not requiring a break (proposal-correct):** authority boundary (§7.1), fail-closed visual-state design (§9), snapshot/cursor atomicity (§10/§14.1), MVP scope (§13), prior-art existence, loopback posture, "don't import an engine," accessibility baseline proposal.
