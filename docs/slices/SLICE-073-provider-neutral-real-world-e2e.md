# SLICE-073 — provider-neutral real-world e2e portability

**Status:** open
**Opened:** 2026-08-28
**Priority:** P0 — restore portable real-e2e truth
**Issue:** #52
**ADR:** `docs/adr/ADR-036-provider-neutral-real-world-e2e.md`

## Contract

Implement ADR-036. The kernel invokes an opaque executable adapter with no
provider credential requirement or injection. Real task-family tests apply a
pinned existing Git commit to its real parent and independently observe the
red/green suite, diff, candidate, and journal. Freeze owns disposable real
dependency state. Historical qualification either completes on its exact host
or proves the exact fail-closed refusal elsewhere.

## Owned paths

- ADR-036, its prior-art directory, this slice, README, and `docs/STATE.md`
- `src/ranex/cli/delegation.py`
- delegation unit/integration/security and real task-family e2e tests
- `tests/e2e/test_provider_neutral_adapter_real.py`
- `tests/e2e/test_suite_freeze_real.py`
- `tests/e2e/test_specification_batch_qualification.py`
- real-e2e prerequisite/manifest contracts only where OpenRouter declarations cease

## Done criteria

1. Frozen unit/integration tests prove no provider credential constant or
   requirement exists, ambient API keys are dropped, and the child environment
   contains only pinned PATH, scratch HOME, task ID, and emission path.
2. Existing signing-key, emission, timeout, worktree, commit, suite, candidate,
   and journal refusal tests remain unchanged in strength and green.
3. Real delegation e2e applies pinned commit
   `cebc06a33ba1f28fd21815bb21edbdc768b4a669` to its real parent, proves the
   focused suite red before and green after, and records a non-empty diff plus
   evidence-absent CANDIDATE without any provider credential.
4. Real freeze operates in a disposable clone, derives and test-approves the
   exact lock there, reproduces the committed manifest, and leaves the operator
   checkout/journal untouched.
5. Historical batch qualification completes only on matching build bytes; on
   this foreign host it must assert `E-C17-BUILD-INPUT-DRIFT`, no artifact, no
   publication, and clean repositories rather than fail setup.
6. The bounded-pool fanout control passes ten consecutive focused iterations
   and the canonical nested run without relaxing overlap, timeout, emission,
   or journal assertions.
7. The canonical full real-e2e entrypoint passes coverage and honest skip-ledger
   checks on the exact final commit; any unavailable host-only feature remains
   explicitly unverified rather than green by absence.

## Stable refusal order

Signing-key exclusion → harness admission → dispatch → adapter timeout/emission
binding → real diff → independent suite → candidate/journal → merge authority.

## Not owned

No provider SDK/router, credential broker, desktop integration, harness-lane
mutation, new network authority, production fanout, SWE-bench score claim, or
rewrite of published historical authority bytes.

## Verification

```text
uv run --frozen pytest -q tests/unit/test_delegation.py tests/integration/test_delegation_command.py
uv run --frozen pytest -q tests/e2e/test_first_delegation.py tests/e2e/test_delegation_real.py
uv run --frozen pytest -q tests/e2e/test_suite_freeze_real.py tests/e2e/test_specification_batch_qualification.py
uv run --frozen pytest -q tests/security/test_slice008_execute_attest_separation.py::test_fanout_respects_bounded_pool_and_does_not_tick_queue_time
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

The five provider-neutral tests were frozen RED before production changes. The
three existing real-e2e failures from the baseline are already frozen regression
tests; implementation may not weaken or delete them.
