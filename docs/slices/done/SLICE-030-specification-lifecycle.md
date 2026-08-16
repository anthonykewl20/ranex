# SLICE-030 — kernel lifecycle and human clarification

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — A/B/C needs a deterministic pre-implementation lifecycle.
**ADRs:** `docs/adr/ADR-027-specification-lifecycle.md`.

## Contract

Given SLICE-029 A/B/C ports, canonical human clarification inputs, and an
actor, the kernel returns a durable lifecycle result across `DRAFT`,
`SPEC_VALIDATED`, `TESTS_MAPPED`, and `APPROVAL_PENDING`. It never returns a
capability or reaches implementation authority.

## Exact owned paths

- `src/ranex/governed_execution/domain/specification.py`
- `src/ranex/governed_execution/application/specification.py`
- `src/ranex/governed_execution/application/__init__.py`
- `src/ranex/cli/specification.py`
- `tests/unit/test_specification_lifecycle.py`
- `tests/integration/test_specification_cli.py`
- this slice and ADR-027 prior art only.

## Deterministic acceptance gates

1. Every permitted and refused transition has a closed-table result with actor,
   answer, ambiguity, contradiction, stale-base, and retry guards.
   `test_transition_table_and_refusals_are_closed` and
   `test_actor_base_and_answer_guards_are_distinct`.
2. Pre-IMPLEMENTABLE lifecycle cannot construct capability authority, call a
   producer, mutate a subject, or advance from prose. `test_no_preapproval_authority_is_exposed`.
3. Reapplying a request returns the identical durable result.
   `test_retry_returns_the_recorded_result_without_an_effect`.
4. Identical A input renders byte-identical blocking questions and semantic
   digest. `test_questions_and_semantic_digest_are_stable`.
5. Observed facts remain characterization only.
   `test_observed_only_facts_cannot_promote_intent`.
6. The isolated CLI parser drives draft/advance/questions/status and prints
    refusal code to stderr with a nonzero exit. `test_specification_parser_drafts_a_valid_session`
    and `test_specification_parser_refusal_is_nonzero_and_stable`.

## Not owned

- `main.py`, journal/persistence, approval signing, generators, grants, harness,
  judge, merge, providers, E2E, and any SLICE-029-owned contract file.

## Stop conditions

Stop if the A/B/C port cannot express a required guard, frozen contract tests
need alteration, or a change requires an implementation capability, persistence,
or a SLICE-029-owned file.

## Verification commands

```text
PYTHONPATH=src uv run --frozen pytest -q tests/unit/test_specification_lifecycle.py tests/integration/test_specification_cli.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen ruff check src/ranex/governed_execution/domain/specification.py src/ranex/governed_execution/application/specification.py src/ranex/cli/specification.py tests/unit/test_specification_lifecycle.py tests/integration/test_specification_cli.py
uv run --frozen pytest -q
```

## Closure

Focused verification: 14 passed. Full suite: 1048 passed / 33 skipped / 1
known flake; the flake is the documented cgroup-observer `OSError(19)` under
load and passed in isolation. Independent review resolved all P2 findings;
remediation landed in `2c6b7510c`. Follow-ups: SLICE-032 owns wiring lifecycle
facts and nonce tracking.
