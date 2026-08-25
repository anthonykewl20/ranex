# SLICE-036 — approved-batch qualification

**Status:** open
**Opened:** 2026-08-25
**Priority:** P0 — kernel-only qualification; publication blocked
**ADRs:** `docs/adr/ADR-017-approved-specification-before-implementation-authority.md`, `docs/adr/ADR-025-abc-contract-freeze.md`, `docs/adr/ADR-030-approval-and-intersected-grants.md`

## Contract

Preserve legacy `task fanout` byte-for-byte and add the separate
`ranex task batch qualify` grammar. Existing A/B/C canonicalization and DSSE
plus `ranex-evidence-v4` Ed25519 evidence are the only approval/signing
primitives. B protects both normative schemas,
closed batch descriptor, fork/join child rows, every signed negative child
input, both normalized goldens, and four distinct canonical oracle artifacts:
pseudocode flow, expected values, baseline, and negative controls. The
descriptor carries a separate path/digest reference to each populated oracle;
it is not reused as a placeholder for any class. C therefore binds those
bytes, maximum pool two, exact base/subject identity, policy, and roles.

The frozen `5586d68b0936f554759022caabe847087f1d03ef` commit and
`sha256:34fa645d616fc0b0383d424573d60a447ddd829e8891b7f992b809be9a783953`
subject are the deterministic E2E fixture only. Production qualification must
accept any separately approved exact 40-hex base and its existing ADR-012
`sha256(canonical_json({"tree": git rev-parse <base>^{tree}}))` identity; it
must never replace either with a mutable ref or caller assertion.

Children execute only through the existing `ranex run --confinement
strict-local` boundary in disposable worktrees. Signed rows bind claim/check
names, exact child argv/runtime-control inputs, and relative evidence/outcome
paths, not unknowable pre-execution output digests. The B-bound public-CLI
negative inputs plant an unapproved D row, sibling scope overlap, a real
loopback attempt, a named survivor process, and an oracle-result mismatch.
Both A/B completion orders are observed, canonical results stay
A/B/C-ordered, and C is released only after the join. One clean disposable
governed repository and its `refs/heads/main` identity span qualification,
the `batch-qualified` journal row and signed artifact, dispatch, judge, merge,
and publication refusal. Qualification may append one continuity fact; judge,
merge, CAS, target-ref mutation, production fanout, and every publication path
are refused before journal or publication effects. Every independent ref,
journal, worktree, and filesystem observer reads that same repository. There is
no second target repository.

Staged development code remains outside the governed repository. Every CLI
subprocess has the governed checkout as cwd/repository root and executes through
the explicit absolute `PYTHONPATH=<development-worktree>/src`; no source patch,
copy, overlay, or generated source file enters the governed checkout. Before
qualification, the E2E independently resolves `ranex.cli.main.__file__`, hashes
a canonical path/raw-SHA-256 manifest of every executed `src/ranex` file, and
compares the exact module path and manifest digest through the normalized
qualification transcript oracle. It also proves the imported module is outside
the governed repository and the governed source manifest remains unchanged.

After its one ADR-030 `append_if_head` succeeds, qualification writes a
canonical `batch-qualification-v1` outcome. Its evidence-v4 attestation signs
the canonical payload digest and therefore binds A/B/C, descriptor, child
requests/results, exact base commit/digest, producer, and the exact
`batch-qualified` journal sequence/predecessor/head. The payload is permanently
`publication_allowed:false`. Batch-aware judge and merge accept the additive
`--batch-qualification <actual-outcome>` flag, verify that signature and every
digest through the existing keyring/admission path, match the exact journal
row, then emit `E-BATCH-PUBLICATION-REFUSED` before legacy judge, merge-intent,
check, outcome, CAS, or ref writes. Calls without the flag retain their legacy
grammar and behavior.

## Owned paths

- `governance/schemas/specification/approved-batch-v1.schema.json`
- `governance/schemas/specification/batch-qualification-v1.schema.json`
- `src/ranex/governed_execution/domain/specification_batch.py`
- `src/ranex/governed_execution/application/specification_batch.py`
- `src/ranex/governed_execution/adapters/persistence/sqlite/journal.py`
- `src/ranex/cli/main.py`
- `tests/contract/fixtures/specification/approved-batch-v1.json`
- `tests/contract/fixtures/specification/approved-batch-v1-vectors.json`
- `tests/contract/fixtures/specification/approved-batch-child-requests-v1.jsonl`
- `tests/contract/fixtures/specification/approved-batch-pseudocode-flow-v1.json`
- `tests/contract/fixtures/specification/approved-batch-expected-values-v1.json`
- `tests/contract/fixtures/specification/approved-batch-baseline-v1.json`
- `tests/contract/fixtures/specification/approved-batch-negative-controls-v1.json`
- `tests/contract/fixtures/specification/approved-batch-unapproved-row-v1.jsonl`
- `tests/contract/fixtures/specification/approved-batch-scope-overlap-v1.jsonl`
- `tests/contract/fixtures/specification/approved-batch-network-escape-v1.jsonl`
- `tests/contract/fixtures/specification/approved-batch-child-survivor-v1.jsonl`
- `tests/contract/fixtures/specification/approved-batch-oracle-mismatch-v1.jsonl`
- `tests/integration/test_approved_batch_qualification_contract.py`
- `tests/e2e/test_specification_batch_qualification.py`
- `tests/e2e/expected/slice036-approved-batch-qualification.out`
- `tests/e2e/expected/slice036-approved-batch-publication-refusal.out`
- `README.md`, `docs/STATE.md`, and this slice

## Done criteria

1. `test_signed_authority_closes_schema_descriptor_children_and_every_oracle_fixture`
   recomputes every B-protected digest and the existing A/B/C/DSSE chain; no
   empty oracle class or fabricated child-evidence digest remains.
2. `test_fixture_uses_exact_base_subject_and_provenanced_runtime_evidence_contract`
   recomputes the fixture subject, freezes strict-local invocations, disjoint
   child scopes, required claim/check names, and relative evidence paths.
3. `test_b_bound_negative_inputs_plant_each_public_cli_control_in_child_rows`
   proves every negative input is independently populated, B-protected, and
   carries the exact row/argv/runtime plant the E2E supplies through `--tasks`.
4. `test_separate_batch_qualify_parser_preserves_the_exact_legacy_fanout_surface`
   proves the new three-token grammar is separate and legacy fanout still owns
   its current parser/function without A/B/C flags.
5. `test_signed_plan_has_both_completion_orders_canonical_results_and_c_join`
   proves A/B and B/A completion, canonical result ordering, and the C join
   from signed inputs without public test knobs.
6. `test_append_if_head_is_one_begin_immediate_cas_and_stale_reentry_is_stable`
   races two real SQLite callers: one `Journal.append_if_head(expected_head,
   evaluation)` returns position/head, one gets `E-BATCH-STALE-BASE`, and no
   blind replay appends. The adapter owns `BEGIN IMMEDIATE`; callers never use
   raw SQLite to append.
7. `test_real_cli_qualifies_both_orders_and_independently_proves_no_publication`
   invokes staged development code through the exact absolute
   `PYTHONPATH=<development-worktree>/src` and `uv run --frozen python -m
   ranex.cli.main task batch qualify`, while cwd and the repository root remain
   one clean disposable governed checkout. The test independently resolves the
   exact imported `ranex.cli.main` path, hashes a deterministic canonical
   path/raw-SHA-256 manifest of every executed `src/ranex` file, records both in
   the normalized transcript oracle, and proves no patch, copy, overlay, or
   generated source entered the governed repository. That same repository and
   `refs/heads/main` span qualification, its actual SQLite journal row and
   signed artifact, dispatch, judge, merge, and refusal. The journey
   independently queries that ref, SQLite row/head, `git worktree list`,
   filesystem residue, SHA-256 of child evidence, a `/proc` survivor scan, and
   a calibrated real loopback listener. Five B-bound fixtures drive public CLI
   refusal arms for unapproved row, scope overlap, network attempt, survivor,
   and oracle mismatch. It also plants golden, journal, ref, worktree, pool,
   and protected-byte controls. It independently verifies the actual canonical
   qualification artifact using the existing keyring loader/admission verifier,
   passes that artifact to real judge/merge, and compares normalized goldens.

## Stable refusal order

`E-BATCH-SCHEMA` → `E-BATCH-PROTECTED-ARTIFACT` →
`E-BATCH-STALE-BASE` → `E-BATCH-UNAPPROVED-ROW` →
`E-BATCH-POOL-EXCEEDS` → `E-BATCH-SCOPE-OVERLAP` →
`E-BATCH-NETWORK-ESCAPE` → `E-BATCH-CHILD-SURVIVOR` →
`E-BATCH-WORKTREE-RESIDUE` → `E-BATCH-ORACLE-MISMATCH` →
`E-BATCH-PUBLICATION-REFUSED`. All input, authority, liveness, negative-oracle,
and publication refusals precede `append_if_head`, ref mutation, CAS, or
publication. A successful qualification appends exactly once.

## Not owned

No edit to `src/ranex/cli/fanout.py`, `tests/e2e/test_task_real.py`, harness,
broker, dependency, signing domain, production fanout, judge acceptance,
merge/CAS authority, target-ref update, or publication. No suite-manifest edit
or hand-captured implementation output belongs in this frozen-red commit.

## Verification

```text
uv run --frozen pytest --collect-only -q
uv run --frozen pytest -q tests/integration/test_approved_batch_qualification_contract.py
uv run --frozen pytest -q tests/e2e/test_specification_batch_qualification.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
```

The focused integration and E2E commands must remain honestly RED only at the
absent public batch application/CLI, qualification-artifact linkage, and
`Journal.append_if_head` surfaces. Docs and fixture closure must be green.
Implementation starts only after independent review, owner CCR acceptance,
and `status:ready`; this slice never self-approves.
