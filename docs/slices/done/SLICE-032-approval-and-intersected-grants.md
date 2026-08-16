# SLICE-032 — approval, revocation and intersected child grants

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — issue a bounded, revocable implementation authority.
**ADRs:** `docs/adr/ADR-030-approval-and-intersected-grants.md`.

## Contract

Validate A/B/C with the frozen 029 contract, bind a closed policy record to C,
project approval lifecycle facts, and issue only deterministic least-authority
grants. Events are pure, chained domain records; use reduction observes an
ordered prefix. Persistence and CAS wiring remain SLICE-036.

## Exact owned paths

- `src/ranex/governed_execution/domain/specification_approval.py`
- `src/ranex/governed_execution/domain/specification_events.py`
- `src/ranex/governed_execution/application/specification_approval.py`
- `tests/unit/test_specification_approval.py`
- `tests/unit/test_specification_child_grants.py`
- `tests/integration/test_specification_revocation.py`
- `docs/adr/ADR-030-approval-and-intersected-grants.md` and `docs/adr/prior-art/ADR-030/`
- `docs/slices/SLICE-032-approval-and-intersected-grants.md`

## Deterministic acceptance gates

1. C replay, nonce, audience/session/base, signer and role failures refuse:
   `test_approval_binds_policy_roles_head_nonce_and_window`.
2. Exact policy/parent/request intersection never expands a child:
   `test_child_intersection_is_closed_and_never_expands`.
3. Wildcards, empty-list allow-all, bool counts and path escapes refuse:
   `test_capability_grammar_refuses_ambiguous_authority`.
4. Child siblings cannot share an overlapping path-prefix+action scope:
   `test_sibling_path_action_scopes_are_disjoint`.
5. Ancestor revoke/expiry and deterministic race order govern use:
   `test_revoke_and_expiry_propagate_through_descendants`.
6. Equal inputs produce equal grant/event/use facts:
   `test_event_and_use_facts_are_canonical_and_deterministic`.

## Not owned

- SLICE-029 ABC contract or error registry; SLICE-030 session wiring.
- Journal persistence, atomic append, batch liveness, adapters, CLI, harness,
  judge, merge, generator, and publication integration.

## Stop conditions

Stop for a required change to frozen ABC semantics, an inability to express the
CAS boundary as a pure contract, or a full-suite failure outside owned paths.

## Verification commands

```text
uv run --frozen pytest -q tests/unit/test_specification_approval.py tests/unit/test_specification_child_grants.py tests/integration/test_specification_revocation.py tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

## Closure

Consensus-hardened design: a consensus review reshaped it before implementation.
Independent adversarial review found three P1s — argv ordering, use-time window,
and sibling prefix overlap — remediated in `4068d953b` and `81fb410fa`.
Focused verification: 13 passed. SLICE-036 owns CAS/persistence and the
`SpecificationEvent` atomicity contract. Nonce tracking is wired here per
SLICE-030's handoff.
