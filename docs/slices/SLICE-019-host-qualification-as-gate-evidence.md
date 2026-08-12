# SLICE-019 — host qualification as gate evidence

**Status:** open
**Opened:** 2026-08-12
**Priority:** P0 — closes ADR-021's absence gap: the landing gate requires only
`tests-executed` today, so an unqualified host can pass (`governance/gates.yaml:10-17`).
**ADR:** `docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md`
(accepted). By owner direction 2026-08-12, this slice narrows ADR-006's original
“SLICE-019 = `cmd_run` integration” grant to ADR-021 integration only. General
`cmd_run` confinement binding and cgroup/output lifecycle remain deferred.
**Next:** revise and freeze this slice's tests red; implement and close this
slice; then the ADR-019/020 kernel slice (judgment identity + `self_approval`
wire); then SLICE-018/029.

## Session-sized result

The landing gate gains one required `host-qualification` claim. It is satisfied
by the same ordinary signed `Evidence` record used for `tests-executed`: the
operator runs `ranex run --claim host-qualification --producer <id> -- <qualify
argv>`, the command exits zero and writes its unsigned report, and the report's
canonical JSON rides in the record's `suite_results`. The existing
`EVIDENCE_DOMAIN = b"ranex-evidence-v3\n"` and exact fields sign the complete
report together with `claim_id`, command, producer and subject
(`src/ranex/foundation/signing.py:44,52-61`). There is no new signing domain,
sidecar, foundation module, claim-loader field or kernel field.

Freshness and ambiguity are the only new admission decisions. Before constructing kernel evidence,
shared admission recognizes `host-qualification`, validates the report instead
of interpreting it as JUnit, re-reads every durable host anchor, and refuses
malformed, stale, mismatched or ambiguous records. A rejected or absent record
reaches the kernel as absence (`src/ranex/governed_execution/domain/admission.py:1-24`),
and existing `missing_claims` blocks (`src/ranex/governed_execution/domain/verdict.py:390-397`).
The kernel remains byte-exact and pure (`verdict.py:1-10,338-347`).

## Exact owned paths

Only these paths may change in code-impl:

- `governance/gates.yaml` (add the `host-qualification` claim: `claim_id`,
  `command` = the qualify argv, NO `results_artifact`)
- `src/ranex/governed_execution/domain/admission.py` (new `RejectionReason` +
  the live-anchor freshness check + row-11 ambiguity refusal + report extraction
  from `suite_results`)
- `src/ranex/cli/main.py` (the shared admission wiring consumed by both
  `cmd_gate_evaluate` and `cmd_task_judge`; fix the early-error path so a
  missing/malformed report reaches evaluation as absence/rejection, never
  `EXIT_USAGE`)
- `governance/suite_manifest.json` (freeze the new test IDs so they are
  gate-blocking)
- `tests/contract/test_qualification_admission.py` (new — rows 1, 9, 11, 13 +
  freshness + self-approval + domain-separation)
- `tests/e2e/test_gating_real_suite.py` (UPDATE existing one-claim preconditions
  AND add the qualify→approve→gate PASS → change-one-fact → FAIL journey)
- `docs/slices/SLICE-019-host-qualification-as-gate-evidence.md`
- `docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md`
- `docs/STATE.md`
- `README.md`

Explicitly **NOT** owned (one-way doors / other slices):

- `src/ranex/foundation/qualification.py` (not created — no new domain)
- `src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py`
- `src/ranex/bootstrap/composition.py`
- `src/ranex/governed_execution/domain/verdict.py` (kernel byte-exact —
  `KERNEL_DIGEST` unchanged; absence falls out of existing `missing_claims`)
- `src/ranex/cli/host_confinement.py` (SLICE-017-owned; the report writer and
  launch-time re-read stay there)
- `cmd_run` confinement binding
- cgroup lifecycle
- SLICE-018/029 work

## Frozen qualification-evidence contract

### Existing Evidence envelope and claim source

`host-qualification` uses no qualification-specific envelope. The signed record
has exactly the existing `Evidence` fields — `claim_id`, `command`,
`command_digest`, `executable_path`, `exit_code`, `producer_id`,
`subject_digest`, and `suite_results` (`src/ranex/governed_execution/domain/verdict.py:90-113`) —
and verifies only under `EVIDENCE_DOMAIN` using the exact `SIGNED_FIELDS`
(`src/ranex/foundation/signing.py:44,52-61`). The full canonical qualification
report is the `suite_results` value, so the existing signature binds the whole
report, producer and subject. There is NO new signing domain, NO sidecar, NO
`src/ranex/foundation/qualification.py`, NO loader extension and NO composition
change.

The catalog claim binds this existing qualify argv and deliberately omits
`results_artifact`:

```text
python -m ranex.cli.host_confinement qualify --profile governance/confinement/strict-local-host-v1.json --artifact .local/ranex/libexec/strict-local-v1/ranex-worker-launcher --manifest governance/confinement/native-launcher-build-v1.json --report .local/ranex/qualification/strict-local-v1.json
```

Its option names and ordering are the existing parser's
(`src/ranex/cli/host_confinement.py:2635-2660`). `results_artifact` is optional
and only enables the JUnit token rule when present
(`src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py:75,133-151`);
omitting it makes `results_required=False` in current composition
(`src/ranex/bootstrap/composition.py:68-95`). Therefore no suite-manifest/JUnit
validation may run for this claim: `cmd_run` captures the named report as the
raw record's `suite_results`, and shared admission intercepts, extracts and
validates that signed value before the existing generic JUnit validator
(`src/ranex/governed_execution/domain/admission.py:123-143`) or `Evidence`
constructor (`src/ranex/governed_execution/domain/verdict.py:103-113`) sees it.
After successful qualification admission, it constructs the ordinary
exit-code-only kernel `Evidence` with `suite_results=None`; this normalization is
necessary to keep `verdict.py` byte-exact, while the raw signed record remains
the audit carrier for the complete report. The unsigned source report remains
`.local/ranex/qualification/strict-local-v1.json`, emitted by the unchanged
writer (`src/ranex/cli/host_confinement.py:2568-2617`).

### Refusal rule

Shared admission extracts `suite_results` from every `host-qualification`
record, validates the known report schema, and re-reads live `boot_id`,
`machine_id`, LSM state, unprivileged-userns sysctls, and only the durable
parent-namespace `delegation_identity.uid`/`gid`; unreadable, missing, stale or
mismatched durable anchors reject under `MALFORMED_RECORD` or the new structured
host-state reason `STALE_HOST_STATE`, never default. It does not compare transient
`cgroup_root`, `cgroup_relative_path`, `source`, or `userns_state_source`
(`docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md:147-152,189-190`;
the source report contains both halves at `src/ranex/cli/host_confinement.py:1502-1521`).
Two otherwise admissible qualification records whose `host_state` differs are
both refused as ambiguity, never collapsed or ordered by recency. Missing or
rejected evidence still reaches `evaluate()` as absence and FAILs
`host-qualification`; malformed or missing reports must not be swallowed by
`cmd_gate_evaluate`'s current early `ValueError`/`OSError` → `EXIT_USAGE` path
(`src/ranex/cli/main.py:782-797`). The check belongs to shared admission used by
both `cmd_gate_evaluate` (`main.py:767-780`) and the second landing-gate path in
`cmd_task_judge` (`main.py:1027-1087`). Existing
`producer_id == approver_id` kernel refusal supplies self-approval protection
(`verdict.py:356-376`); `--approver` remains an unauthenticated string, a known
pre-existing risk explicitly outside this slice.

For both CLI paths, “missing report” means no `host-qualification` record was
recorded, so evaluation proceeds normally with that claim absent. “Malformed
report” means malformed JSON carried in a raw signed record's `suite_results`,
which admission converts to a structured rejection before generic suite parsing.
An unreadable evidence file, gate catalog, keyring, suite manifest or journal
remains an operational `EXIT_USAGE`; this slice does not turn general I/O failure
into a verdict.

## Deterministic acceptance gates

1. Absent report → `host-qualification` unsatisfied → gate FAIL, never skip
   (ADR-021 row 1). `tests/contract/test_qualification_admission.py`.
2. Unknown schema / missing host fact → admission refusal (ADR-021 rows 9, 13).
   `tests/contract/test_qualification_admission.py`.
3. Two admitted records disagreeing on `host_state` → refuse ambiguity, never
   prefer newer (ADR-021 row 11). `tests/contract/test_qualification_admission.py`.
4. A genuine report whose durable anchor (boot/machine/LSM/sysctl/uid/gid)
   differs from the live host → admission refusal; the test masks the live
   re-read, never deletes a report key. `tests/contract/test_qualification_admission.py`.
5. `producer_id == approver_id` → self-approval refusal through the existing
   mechanism. `tests/contract/test_qualification_admission.py`.
6. `verdict.py` byte-exact: `reason` bytes and `KERNEL_DIGEST` unchanged;
   `tests/contract/test_kernel_unchanged.py` green without touching the kernel.
7. E2E qualify→approve→gate PASS, then change one bound durable fact → FAIL
   naming `host-qualification`. `tests/e2e/test_gating_real_suite.py`.
8. A `host-qualification` Evidence verifies only under `ranex-evidence-v3` (not
   under `ranex-approval-v1`); exact-`SIGNED_FIELDS` refusal holds and
    `subject_digest`/`producer_id` binding is proven.
    `tests/contract/test_qualification_admission.py`.
9. `cmd_task_judge` (the merge-candidate landing-gate path at
   `src/ranex/cli/main.py:1027-1087`) honors `host-qualification` via the SAME
   shared admission as `cmd_gate_evaluate`: an absent or `STALE_HOST_STATE`
   qualification leaves `host-qualification` missing / rejected, never silently
   admitted or turned into a usage error.
   `tests/contract/test_qualification_admission.py::test_cmd_task_judge_uses_shared_qualification_admission`.

ADR-021 sad-path rows 3–7 — real boot/machine-ID/LSM/sysctl/PRINCIPAL
transitions — require a disposable-VM harness. Per ADR-021's test strategy
(`docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md:202-210`),
they remain MANUAL evidence. Gate 4 is a simulated reader-comparator test, not
proof of those transitions.

## Verification commands

```text
uv sync --frozen
uv run --frozen pytest -q tests/contract/test_qualification_admission.py
uv run --frozen pytest -q tests/e2e/test_gating_real_suite.py
uv run --frozen pytest -q tests/contract/test_kernel_unchanged.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
# Before implementation, add every new test ID to governance/suite_manifest.json
# and verify that the frozen landing manifest contains each collected ID.
```

## Controls most likely to become decoration

1. Satisfying `host-qualification` because its bound command exited zero while
   skipping the live durable-anchor re-read.
2. Sending qualification JSON through generic JUnit parsing, or setting
   `results_artifact`, instead of admitting it as the claim-specific signed
   carrier.
3. Comparing transient cgroup path/source fields as freshness anchors despite
   ADR-021:190 saying they are never anchors.
4. Letting `cmd_gate_evaluate` return `EXIT_USAGE` for a missing or malformed
   report instead of evaluating absence/rejection to gate FAIL.
5. Counting two disagreeing records as one admissible record or preferring the
   newer one.
6. Adding tests but omitting their IDs from `governance/suite_manifest.json`, so
   the landing suite does not make them gate-blocking.
7. Claiming full report binding without proving the existing exact signed fields,
   subject/producer binding and evidence-vs-approval domain separation.

## Not in this slice

- General `cmd_run` confinement binding (ADR-006 closure; a later slice).
- Cgroup/output lifecycle (SLICE-018).
- The launcher launch-time anchor re-read; it stays in
  `src/ranex/cli/host_confinement.py`, SLICE-017's file.
- ADR-019 verdict-read-channel and ADR-020 structured-cause work; those belong
  to their own kernel slice.
- Authentication of the CLI `--approver` string; this pre-existing risk is not
  repaired by qualification evidence.
