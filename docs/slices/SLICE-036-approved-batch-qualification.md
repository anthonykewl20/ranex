# SLICE-036 — approved-batch qualification

**Status:** blocked
**Opened:** 2026-08-25
**Priority:** P0 — kernel-only qualification; publication blocked
**Dependency:** #47 / `SLICE-070` must land the generic strict-local stable I/O
namespace before child execution or frozen-fixture correction resumes.
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

The frozen `a0cbee4b1ac88fa143a5f4c2835c1da09989618c` commit and
`sha256:920a1588d1f9cfcc36a07c7d0b296ad319afb9b120db534b8e0237804b1df9f8`
subject are the deterministic E2E fixture only. The E2E reconstructs that
successor from public parent `5ded60d9a9c8213828dce7acc0e77acad0c25731`
using fixed author/committer identity, time, and message. The successor adds
the fixture owner's real public key to the existing producer keyring and
canonical tracked inputs for every B-bound A/B/C/D row; it changes no
production source. Production qualification must accept any separately
approved exact 40-hex base and its existing ADR-012
`sha256(canonical_json({"tree": git rev-parse <base>^{tree}}))` identity; it
must never replace either with a mutable ref or caller assertion.

Children execute only through the existing `ranex run --confinement
strict-local` boundary in disposable worktrees. Before every such run, the
controller must invoke the existing public `ranex.cli.host_confinement`
`launcher-build`, `launcher-install`, and `qualify` commands inside that child
checkout and verify the launcher, manifest, profile, report schema, host-state
binding, and qualification result. Each child starts with no built launcher,
installed launcher, or usable qualification report. A positive independent
calibration constructs all six clean child geometries, runs the exact three
public commands in each child's cwd, and verifies that child's installed
launcher digest, canonical report digest, host binding, and `qualified=true`
state. The outer observer invokes the already-resolved absolute development
Python controller directly—never `uv`—under literal `/usr/bin/strace -f
--detach-on=execve -s 8192`. It records only `execve`, process ancestry, and cwd
changes while retaining every spawned public `uv run --frozen` argv; it
requires the same exact command sequence in every actual child before that
child's `ranex run`. Its focused calibration observes both sequential and
concurrent sibling controllers. Its canonical provenance artifact is outside
the governed repository, and the B-protected manifest pins literal
`/usr/bin/strace`, its version, and installed-file SHA-256. The canonical inner
host-confinement tracer and all final launcher/report/host checks are unchanged.
Installed strace 6.8 behavior is frozen explicitly: the controller's launch-time
`execve` is recorded while the root remains traced, and each later child
`execve` is recorded before that child detaches. Losing the root necessarily
fails the closed 24-execution calibration (18 host steps plus six runs). The observer rejects any extra or duplicate
child execution and matches the complete signed `ranex run --confinement
strict-local` argv, whose existing public session owner performs the canonical
full host-state drift verification. The successor intentionally commits no
mutable dependency journal, so the calibration first uses the child base's
existing public `deps fetch`, `deps approve`, and `journal verify` path. Those
commands prepare governed admission before tracing; they are not child host
provisioning observations. The older undelegated calibration reached the
canonical verifier's `E-C18-HOST-DRIFT` refusal; that was a valid host-identity
control, never the current release boundary. With #47 unpublished, the actual
child journey now refuses earlier at the missing v2 fixed-toolchain executable
resolution. It cannot reach the absent batch parser/application seams or turn
either refusal into qualification.
The B-bound child command is byte-identical for every row:
`/ranex/toolchain/bin/slice036-worker --task`, with the validator-compatible
policy cwd literal `.` mapped by v2 to actual cwd `/ranex/input`. Its C source
and build provenance are committed in the deterministic
successor. The exact `/usr/bin/x86_64-linux-gnu-gcc-13` 13.3.0 compiler,
installed linker/static inputs, closed environment, absent build ID, source
digest, two byte-identical builds, ELF properties, and final binary digest are
B-protected. The controller verifies those bytes before placing them in the
held toolchain object; the observed subject remains non-executable authority.
The public controller remains `uv run --frozen python -m ranex.cli.main ...`;
the public CLI is unchanged.

This release does not claim to prove the absence of every transient filesystem
copy or model every Linux write syscall. Copying that is subsequently replaced
by the independently executed public build/install/qualify sequence and passes
the final per-child hash and qualified-state checks is not a release blocker.
Application-emitted provisioning booleans remain untrusted. Signed rows bind
one byte-identical argv/cwd literal and preserve the worker environment exactly
as `{LC_ALL,TZ}`; they do not add a task-id environment channel. The controller
derives closed flow/task/attempt values from its owned geometry, cross-checks
the signed row, and opens the exact signed base-committed
`governance/qualification/inputs/<task-id>/<flow-id>/attempt-<n>/task.json`
as `/ranex/input/task.json`. Embedded flow/task/attempt identity must match,
the input must be tracked at the signed base, and the child worktree
must be clean before provisioning and execution. The B-bound public-CLI
negative inputs plant a path/task-id mismatch, an unapproved D row, sibling
scope overlap, a real loopback attempt, a named survivor process, and an
oracle-result mismatch.
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
`publication_allowed:false`. Qualification admission loads the owner's key
from the signed base commit using the existing keyring loader and `admit`;
the descriptor role is only an equality cross-check, never a trust root.
Before publication refusal the E2E independently reads immutable keyring bytes
from the base commit, actual dispatched candidate commit, and current target
tip, requires byte equality, and admits the actual qualification attestation
through every snapshot. Batch-aware judge and merge accept the additive
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
- `tests/contract/fixtures/specification/approved-batch-input-mismatch-v1.jsonl`
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
   a calibrated real loopback listener. It reconstructs the deterministic
   successor commit, verifies every committed child input is tracked and the
   checkout clean and canonically provisions strict-local in the governed
   checkout. A positive calibration begins every governed child without a
   launcher or usable qualification report, independently runs the three exact
   public host-confinement commands in that child's cwd, and verifies its final
   launcher/report digests and qualified host binding. A manifest-pinned command
   observer—not application output—targets the resolved absolute development
   Python controller directly with `-f --detach-on=execve -s 8192`, never wraps
   `uv`, and proves the same exact spawned public `uv` sequence and child cwd
   before every actual child run. Sequential and concurrent sibling
   calibrations both produce one canonical provenance artifact. Because the
   deterministic successor has no mutable dependency journal, the observer
   self-test invokes the existing child-base dependency derivation, approval,
   and journal verification commands before tracing. Its exact full signed run
   must then either pass or return only the existing canonical host-drift
   verifier refusal; actual batch qualification is asserted separately.
   The release deliberately makes no exhaustive transient-copy or Linux-syscall
   absence claim; the canonical sequence must replace any prior bytes. Six
   B-bound fixtures drive public CLI refusal arms for input/path mismatch,
   unapproved row, scope overlap, network attempt, survivor, and oracle
   mismatch. It also plants golden, journal, ref, worktree, pool,
   and protected-byte controls. It independently verifies the actual canonical
   qualification artifact using committed base, candidate, and tip keyring
   bytes through the existing keyring loader/admission verifier, passes that
   artifact to real judge/merge, and compares normalized goldens.

## Stable refusal order

`E-BATCH-SCHEMA` → `E-BATCH-PROTECTED-ARTIFACT` →
`E-BATCH-STALE-BASE` → `E-BATCH-UNAPPROVED-ROW` →
`E-BATCH-INPUT-MISMATCH` → `E-BATCH-POOL-EXCEEDS` → `E-BATCH-SCOPE-OVERLAP` →
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

While dependency #47 is unpublished, the first pre-implementation RED is the
strict-local v2 fixed toolchain executable-resolution refusal. That refusal is
the truthful current boundary, not `E-C18-HOST-DRIFT` and not a batch parser
claim. After v2 lands, the expected RED progression is the absent public batch
parser/application seams, qualification-artifact linkage, and
`Journal.append_if_head`; after those land the frozen journey succeeds. Docs,
fixture closure, and the byte-level static ELF checks must remain green.
Implementation starts only after independent review, owner CCR acceptance,
and `status:ready`; this slice never self-approves.
