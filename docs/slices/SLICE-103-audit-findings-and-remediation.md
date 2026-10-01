# SLICE-103 — Audit findings and remediation

**Status:** open

## Why this slice exists

The owner asked for an exhaustive, code-only audit: the real status of every
feature and initial plan, unfinished seams, critical issues, bugs, and whether
all processes carry logs under one centralized logging. The audit ran on
2026-09-30 against the settled tip `f42f03fed`. Docs and issue text were
treated as claims; code is truth. This slice captures the findings and the
remediation queue so the work survives the session.

## Method

- Six independent audit lanes run in parallel: unfinished/stub/dead code and
  CLI surface; logging and observability; test-vs-feature gaps; critical bug
  hunt; recent-feature claims versus code; full issue-history versus code.
- Every lane finding was independently re-verified against source before
  acceptance (each claim below carries its anchor).
- One clean full-suite run on the settled tip; representative red tests
  root-caused individually instead of accepted as "standing failures".
- Worktree integrity audited first: all uncommitted and unpushed work was
  rescued to pushed `rescue/` branches before any cleanup; no work was lost.

## Verdict

The kernel is real and well tested. Eight of the eleven recent features are
genuinely shipped end to end. But the initial plans are NOT finished, the
CRITICAL policy-context fail-open is now remediated (C1 below), the suite was
red on the settled tip for reasons that are not only host drift, and the owner's
logging requirement is unmet at every level.

## Findings

### CRITICAL

- C1 — SLICE-081 policy-context binding fails open. `admit()` appends
  qualification records after all regular evidence
  (`src/ranex/governed_execution/domain/admission.py:577`), but
  `refuse_foreign_policy_context` and `refuse_executables_inside`
  (`src/ranex/cli/main.py:472`, `:560`) zip evidence against record positions
  under an explicitly documented order assumption that this reordering breaks.
  A `host-qualification` record placed before a foreign-policy record shifts
  every pairing: the foreign record is admitted under the wrong gate and
  catalog, and the honest record is rejected. Reproduced through the
  production chain. No test mixed both record kinds at audit time.
  **Remediated:** `f01d42a` (2026-10-01). Admission preserves original record
  order even after deferred host-state checks; both executable containment and
  policy filtering check equal lengths and every evidence field against its
  signed source, refusing duplicate envelopes and broken/missing identity.
  `tests/security/test_c1_policy_context_pairing.py` covers both production-chain
  orderings and malformed, missing, duplicate, unmatched and length-mismatched
  identity. Origin/main `c3ac86a85710dc615902e72d473d218d880e5af6`:
  16 failed / 3 passed; fixed branch: 19 passed (63 with existing qualification,
  policy-context and kernel-byte contracts). The reverse-order counterfactual
  was already green on main; qualification-first was red. Kernel bytes remain
  `2969aa74adc8ac40393fb4f782e05be8f29f34d2ab0f594051906f4e6a5b5ed6`.
  `MAIN_PY_SHA256` re-pinned in the implementation commit. Production refreeze
  on that committed tree: 2469 tests / 157 expected skips, `load_manifest`
  accepted; sealed run 2268 passed / 146 skipped / 22 failed / 33 errors.
  That nonzero run is not PASS; direct final-suite drift comparison is reported
  separately in the C1 review PR.

### HIGH

- H1 — the observation log has no externally anchored head. `reconcile`
  verifies with no expected head
  (`src/ranex/governed_execution/adapters/persistence/sqlite/observations.py`),
  so deleting a FAIL from both `evidence.json` and `observations.sqlite3` and
  rewriting a self-consistent chain defeats the removed-observation
  protection. The evaluation journal closes this class with its signed
  `journal_head`; no signed field carries the observation-chain head
  (`src/ranex/foundation/signing.py:79-93`).

### MEDIUM

- M1 — the promotion gate admits `NaN`/`Infinity` delta triples (the
  arithmetic reconciliation at
  `src/ranex/governed_execution/promotion_gate.py:513-516` compares with `>`,
  which is always false for NaN; claims load via plain `json.loads` at
  `src/ranex/cli/main.py:1577`) and silently skips a malformed `tau`
  (`promotion_gate.py:532-533`). Reproduced: `nan`, `inf`, malformed tau all
  ADMITTED.
- M2 — structurally broken promotion claims raise `ValueError` and surface as
  `ERROR`/exit 2 (`src/ranex/cli/main.py:1597-1599`) instead of the promised
  REFUSED decision record with a named cause.
- M3 — `record_evidence` is a non-atomic, unsynchronized read-modify-write of
  the shared `evidence.json`, with the observation-log append after the
  projection write (`src/ranex/cli/main.py:977-995`). Concurrent runs can lose
  updates; a crash between the writes wedges every later `gate evaluate` on
  `E-OBSERVATION-CHAIN`.
- M4 — the bubblewrap probe subprocess has no timeout
  (`src/ranex/cli/process_supervisor.py:301-309`); every other subprocess in
  that module is bounded. A hung probe hangs every guarded execution.
- M5 — `run` then `suite freeze` self-conflicts in a fresh subject repo.
  `cmd_run` exempts its own artifacts (evidence, journal, observation log)
  from the dirty-tree check (`src/ranex/cli/main.py:4082-4091`), but
  `suite freeze` exempts only its own `--output` (`cli/main.py:4319-4322`).
  After #109 added `observations.sqlite3`, a run-then-freeze flow refuses
  ("HEAD does not describe: observations.sqlite3") on the files `run` itself
  wrote. Observed in the red suite (gating/manifest families). The freeze
  exemption list was never updated to match `run`'s.

### Suite status on the settled tip

`uv run --frozen pytest -q` at `f42f03fed` produced 2330 passed / 65 skipped /
13 failed / 26 errors, exit 1. Root causes established by focused reruns:

- `test_slice017` gate10 freeze: stale `MAIN_PY_SHA256` pin — `cli/main.py`
  changed without re-pinning in the same commit. A discipline violation, not
  drift.
- `test_slice003` command binding: pre-observation-log contract — hand-edited
  evidence is now hard-refused with `E-OBSERVATION-CHAIN` (exit 2) before the
  kernel can judge it as a refusal (exit 1). Feature landed; test not updated.
- Golden e2e family (`test_run_real`, `test_suite_freeze_real`,
  `test_task_real`): tests delete `evidence.json` expecting absence, but the
  observation log restores chain-held records for judgment by design. Stale
  tests, not broken absence-blocking (kernel is digest-pinned and green).
- `test_slice036` selector family: compiled worker artifact digest drift
  (rebuilt binary does not match the pinned manifest digest). Environmental
  and a reproducible-build weakness, not a logic bug.
- `test_slice046` strict-local: the known E-046 host-gate.

Conclusion: the "standing host drift" label used at issue closures is
incomplete. The red suite hides a broken contract pin, stale tests versus the
observation-log semantics, and a reproducible-build weakness. Issues #105,
#110, #115 and #119 were all closed against this red suite.

Full inventory of the 13 red (focused rerun, 2026-09-30): `test_docs_discipline`
(local third_party tree), `test_gating_real_suite` x2 and
`test_pytest_observer` xpass arm (M5 freeze-refusal / restore semantics),
`test_scan_claim_real` x2 (scanner exit-code arms), `test_specification_batch_qualification`
x2 + `test_approved_batch_qualification_contract` x2 (static-worker
reproducible-build drift), `test_slice017` gate10 (stale pin), `test_slice003`
(pre-#109 contract), `test_slice046` (E-046 host gate).

### Logging: FAIL against the owner requirement

- Zero Python `logging` usage in the tree. The one central facade
  (`src/ranex/observability/`) is env-gated and default-OFF
  (`RANEX_TRACE`), and records only CLI stage pairs plus exit codes.
- Only `cli/main.py` and `cli/host_confinement.py` call it. `governed_execution`,
  `policy`, `github_app`, `provisioning`, `foundation`, `bootstrap` emit
  nothing on any path: verdict decisions, gate refusals, digest failures,
  journal verify results and signature failures leave no log record.
- No debug mode exists: no flag, no env var, no debug-level events.
- Genuine silent failures: `src/ranex/cli/main.py:5822-5824` swallows
  trace-anchor failure with `except Exception: pass`;
  `src/ranex/github_app/receiver.py:701-704` answers bad-signature deliveries
  401 with zero persisted record; `:725-726` discards exception detail into a
  bare 500.
- `NotImplementedError` at `src/ranex/observability/emitter.py:218` is an
  intentional interface seam (all four sinks implement it), not unfinished.

### Unfinished or prematurely closed features

- #112 minimization ladder: the headline proof arms are hard-coded GAP stubs
  in `tools/dogfood/minimization_ladder_proof.py:196` ("live model worker not
  configured", empty digests) and GAP is treated as non-failing at `:220`.
  Committed receipts carry `status: GAP` with empty digests while the closure
  claimed a seeded-subject fastapi proof. The firstmate dispatch brief
  (`third_party/firstmate/data/ranex-112/brief.md`) explicitly demanded "the
  real-app-repo proof uses real receipts (argv/cwd/digests/exit/wall-clock),
  not prose claims" — the tasked deliverable was never produced. By the
  issue contract ("GAP is not PASS") it was closed unfinished.
- SLICE-036 thread: batch approval issuance is reserved but unimplemented
  (`refuse_batch_issuance`,
  `src/ranex/governed_execution/domain/specification_approval.py:382`, itself
  dead code), and fanout qualification assertions sit permanently skipped with
  dead bodies (`tests/e2e/test_task_real.py:957`).
- #115 gate calibration: every certificate freezes
  `reproducibility: UNVERIFIED`; the cross-operator leg was never measured.
- #105 OCR subject: 5 of 6 arms are hard-coded unverified stubs; the goal
  "govern OCR as a subject" was not achieved (terminal pre-authorized).
- #88, #98, #99, #103, #104, #90: closed with no code for part or all of
  their titled deliverables (run-manifest failure classes, provider
  classification, CLI honest labels, receiver host-header allowlist,
  automatic publication).

### Plans never written (zero matches in src/ranex)

- Merge-candidate / merge-group governance (merge queues bypass Ranex).
- Shard aggregation.
- Multi-agent policy compiler/catalog.
- Closed failure classes for the run manifest.
- The multi-agent harness milestone (durable run schema, supervisor leases,
  merge handoff, orchestrator, manager UI) — withdrawn as wontfix, but it was
  in the initial plans.
- Effect-admission family and protocol-v1 credential broker — wontfix.
- Production ops: hosting soak, credential rotation, backup/restore.

### Repo-ledger and contract defects

- `governance/bom.yaml` (honesty enforced by `test_bom_is_honest.py`): 4 of 16
  parts are `status: specified` with no implementation anchor — FT-06
  (read-only frozen spec), FT-07 (red-before/green-after enforcement), FT-10,
  FT-11. Only 1 of 16 is `calibrated`. FT-07 means "was it red first?" is
  structurally unenforced.
- `governance/suite_manifest.json` carries 107 non-collectable test IDs:
  `_test_id` in `src/ranex/foundation/suite_results.py:148-152` renders
  class-based tests as `file/Class.py::test`, which pytest can never collect.
  The freeze is byte-checked but not semantically true.
- Environmental landmine: `third_party/firstmate/` is parked inside the
  checkout (excluded via `.git/info/exclude`, invisible to git), but
  `test_docs_discipline.py` scans the working tree, so
  `test_no_document_exists_outside_the_allowed_set` fails on any machine
  carrying that tree and passes on clean CI. Part of the red suite is this
  local tree, not code.

### Dead code (lean/DRY rule) and untested seams

- Eight unreferenced symbols: `refuse_batch_issuance` and
  `canonical_record_bytes` (`domain/specification_approval.py`),
  `verify_envelope` (`foundation/dsse.py`), `scanned_test_files`
  (`foundation/antislop.py`), `parse_delegated_review_artifact` and the
  reporter constants (`foundation/delegated_review.py`),
  `_current_session_host_state` (`cli/host_confinement.py`),
  `cmd_launcher_build`/`cmd_launcher_install` (`cli/main.py`).
- Untested: `foundation/release_version.py` (zero tests), `foundation/dsse.py`
  and `foundation/merkle.py` (crypto blocks, indirect only), delegated-review
  SARIF output, roughly 30 witness refusal branches, fanout grammar refusals
  (dead under skip), 3 of 4 `static_executable` refusals, live HTTP observer
  (env-gated).
- Generated "executable" gauges are tautological placeholders tagged
  `placeholder-until-execution-slice`
  (`src/ranex/specification_generation/projection.py:110-116`); the execution
  slice that replaces them was never built.

### Clean areas (evidence-backed)

Kernel purity, absence-blocking, subject/command digest binding, no
self-approval, journal append-only chain with signed anchor, credential
removal invariance, signing and DSSE, webhook validation, no `shell=True`
anywhere, and all 29 CLI commands / 281 flags real (zero parsed-and-ignored).

## Remediation queue (priority order)

Progress: 2026-10-01 — the #105 OCR-subject gap is closed (static
entrypoint v3 admission + proof arms 0/1/2/3/5 VERIFIED; arm 4 GAP by
owner decision); see `tools/dogfood/audits/2026-09-30-ocr-subject-v2/`.

1. C1: **done**, `f01d42a`; order-preserving admission with checked identity,
   both mixed record orderings covered by production-chain security regressions.
2. H1: **next** — anchor the observation-chain head in the signed verdict. Acceptance:
   wholesale chain rewrite is refused like the journal anchor case.
3. M1/M2: promotion gate refuses non-finite and wrong-type claim fields as
   data with named causes. Acceptance: NaN/inf/malformed-tau claims produce
   REFUSED decisions, never crashes or admissions.
4. Fix the red suite honestly: re-pin `MAIN_PY_SHA256` in the same commit as
   any `cli/main.py` change; update pre-observation-log tests to the restore
   semantics (or change the semantics and say so); align `suite freeze`'s
   dirty-tree exemptions with `run`'s (M5); decide the reproducible build
   story for `test_slice036`/batch-qualification artifacts.
5. Finish or reopen #112 (run the live arms for real) and SLICE-036 (batch
   issuance, fanout qualification).
6. Centralized logging: one global logger, domain events on every critical
   path, a debug mode, and no swallowed errors without a record.
7. Delete or wire the eight dead symbols; fix `_test_id` so the frozen suite
   manifest holds only collectable IDs; give `dsse.py`/`merkle.py`/
   `release_version.py` direct tests.
8. Decide the fate of the zero-code plans (merge-group, shard aggregation,
   policy compiler, FT-06/FT-07): build, or record as rejected.

## Blind spots named (not audited)

Native launcher C review, dogfood script internals, performance at scale,
dependency supply chain, live GitHub App operations, opt-in live experiment
arms, cross-host behavior, non-Linux portability.
