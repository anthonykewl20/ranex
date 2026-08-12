# SLICE-019 — host qualification as gate evidence

**Status:** open
**Opened:** 2026-08-12
**Priority:** P0 — closes ADR-021's absence gap: the landing gate requires only
`tests-executed` today, so an unqualified host can pass (`governance/gates.yaml:10-17`).
**ADR:** `docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md`
(accepted). By owner direction 2026-08-12, this slice narrows ADR-006's original
“SLICE-019 = `cmd_run` integration” grant to ADR-021 integration only. `cmd_run`
binding and cgroup/output lifecycle remain deferred.
**Next:** close this slice; then the ADR-019/020 kernel slice
(judgment-identity + `self_approval` wire); then SLICE-018/029.

## Session-sized result

The landing gate consumes one new required `host-qualification` claim as signed,
subject-bound evidence. Admission refuses absence, stale or mismatched live host
state, ambiguous reports and self-approval. A reader validates the existing
`ranex-strict-local-qualification-v1` closed report schema emitted at
`src/ranex/cli/host_confinement.py:2568-2617`; `cmd_run` stays unbound.

This is an admission integration, not a kernel extension: records that do not
verify already reach the kernel as absence
(`src/ranex/governed_execution/domain/admission.py:1-24`), and existing
`missing_claims` makes that absence fail
(`src/ranex/governed_execution/domain/verdict.py:390-397`).

## Exact owned paths

Only these paths may change in code-impl:

- `governance/gates.yaml` (add the `host-qualification` claim)
- `src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py` (extend
  the closed `_CLAIM_KEYS` for a report-bearing, non-JUnit claim, distinct from
  `results_artifact`; the current closed set and JUnit-only token rule are at
  `slice_gate_loader.py:75` and `slice_gate_loader.py:133-151`)
- `src/ranex/bootstrap/composition.py` (thread the new claim field into the
  kernel `Claim`; current construction is `composition.py:68-95`)
- `src/ranex/governed_execution/domain/admission.py` (add a
  `RejectionReason` for stale/mismatched host state and the qualification-report
  reader hook; current reasons are `admission.py:43-59`)
- `src/ranex/foundation/qualification.py` (**new** — closed-schema reader for
  `ranex-strict-local-qualification-v1` and the qualification signing envelope)
- `src/ranex/cli/main.py` (read the qualification report named by the claim from
  its working-tree path and thread it through admission/evaluate)
- `tests/contract/test_qualification_admission.py` (**new** — rows 1, 9, 11, 13)
- `tests/e2e/test_gating_real_suite.py` (append qualify→approve→gate PASS, then
  change-one-bound-fact→FAIL)
- `docs/slices/SLICE-019-host-qualification-as-gate-evidence.md`
- `docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md`
- `docs/STATE.md`
- `README.md`

Explicitly **NOT** owned (one-way doors / other slices):

- `src/ranex/governed_execution/domain/verdict.py` (kernel byte-exact —
  `KERNEL_DIGEST` unchanged; absence falls out of existing `missing_claims`)
- `src/ranex/cli/host_confinement.py` (SLICE-017-owned; the report writer and
  launch-time re-read stay there)
- `cmd_run` binding
- cgroup lifecycle
- SLICE-018/029 work

## Frozen qualification-evidence contract

### Envelope

`src/ranex/foundation/qualification.py` owns the third signing domain, exactly
`QUALIFICATION_DOMAIN = b"ranex-qualification-v1\n"`, separate from evidence v3
(`src/ranex/foundation/signing.py:44`) and approval v1
(`src/ranex/foundation/approval.py:28`). Its exact `SIGNED_FIELDS` tuple is:

```text
("schema", "qualified", "host_state", "profile_digest",
 "build_manifest_digest", "artifact_digest", "subject_digest",
 "producer_id", "approver_id")
```

`host_state` is itself closed to exactly `lsm`,
`unprivileged_userns_sysctls`, `boot_id`, `machine_id` and
`delegation_identity`; the source writer records those anchors at
`src/ranex/cli/host_confinement.py:1502-1521`. The three digest fields are read
from the report's `digests.profile`, `digests.build_manifest` and
`digests.artifact` (`host_confinement.py:2604-2608`). The envelope carries a
producer signature and a distinct approver signature over the same bytes.
`producer_id == approver_id` refuses as self-approval. Both identities and the
evaluated `subject_digest` are therefore bound, not supplied as unsigned labels.
The closed tuple follows the existing exact-field pattern
(`signing.py:52-61`; `approval.py:30-38`).

### Claim and evidence source

`SliceClaimDefinition` gains optional `qualification_report`, distinct from
`results_artifact` (`slice_gate_loader.py:24-41`). The claim binds the existing
`qualify` argv and names
`.local/ranex/qualification/strict-local-v1.json`. `gate evaluate` reads that
gitignored working-tree report rather than the subject commit. This is a new
evidence-source pattern: unlike committed trust roots, a second machine cannot
re-verify the qualification from the commit alone; it needs the signed report
and a live re-read of the named host anchors.

The exact bound argv is:

```text
python -m ranex.cli.host_confinement qualify --profile governance/confinement/strict-local-host-v1.json --artifact .local/ranex/libexec/strict-local-v1/ranex-worker-launcher --manifest governance/confinement/native-launcher-build-v1.json --report .local/ranex/qualification/strict-local-v1.json
```

Its option names and ordering follow the existing parser
(`src/ranex/cli/host_confinement.py:2635-2660`); no `cmd_run` binding is added.

### Refusal rule

No admitted report means no `host-qualification` evidence, so existing kernel
absence handling returns it in `missing_claims`; `verdict.py` does not change.
Admission re-reads boot ID, machine ID, LSM and both available userns sysctls
live and compares them with the signed report. An unreadable, missing, stale or
mismatched live anchor gets the new structured stale/mismatched-host-state
`RejectionReason`; it is never defaulted. Two reports disagreeing on any bound
host fact refuse as ambiguity rather than selecting the newer. A bad producer or
approver signature, subject mismatch, or producer/approver identity equality is
also refused before evidence reaches `evaluate()`. Once admitted, the kernel
reaches the same verdict with every model credential absent because evaluation
remains pure (`verdict.py:1-10,338-347`).

## Deterministic acceptance gates

1. ADR-021 sad-path row 1: an absent qualification report leaves
   `host-qualification` unsatisfied; the gate FAILs, never skips.
   `tests/contract/test_qualification_admission.py`.
2. Rows 9 and 13: an unknown report schema version refuses, and a readable
   report missing any required host fact refuses.
   `tests/contract/test_qualification_admission.py`.
3. Row 11: two reports disagreeing on host state refuse ambiguity; the reader
   does not prefer the newer. `tests/contract/test_qualification_admission.py`.
4. A genuine report whose boot ID, machine ID, LSM or userns sysctl differs from
   the live host is refused by admission. The test masks the live re-read; it
   does not delete a report key. `tests/contract/test_qualification_admission.py`.
5. Producer and approver identity equality refuses as self-approval.
   `tests/contract/test_qualification_admission.py`.
6. Verdict `reason` bytes and `KERNEL_DIGEST` remain unchanged: the kernel is
   byte-exact and `tests/contract/test_kernel_unchanged.py` stays green without
   touching `verdict.py`.
7. Qualify→approve→gate PASS, then change one bound host fact→FAIL naming
   `host-qualification`. `tests/e2e/test_gating_real_suite.py`.
8. A qualification signature does not verify under `ranex-evidence-v3` or
   `ranex-approval-v1`; adding or removing any member of the exact
   `SIGNED_FIELDS` tuple refuses. `tests/contract/test_qualification_admission.py`.

ADR-021 sad-path rows 3–7 — real boot/machine-ID/LSM/sysctl/principal
transitions — require a disposable-VM harness. Per ADR-021's test strategy
(`docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md:202-210`),
they remain manual evidence, not automated PASS.

## Verification commands

```text
uv sync --frozen
uv run --frozen pytest -q tests/contract/test_qualification_admission.py
uv run --frozen pytest -q tests/e2e/test_gating_real_suite.py
uv run --frozen pytest -q tests/contract/test_kernel_unchanged.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

## Controls most likely to become decoration

1. Satisfying the claim because the report path exists without validating its
   closed schema, signatures and subject binding.
2. Skipping the live admission re-read whenever a signed report is present.
3. Checking self-approval only after rejected evidence has been reduced to
   absence, losing the structured refusal.
4. “Testing” stale-state refusal by deleting a report key instead of masking the
   live host fact and making a genuine signed report disagree.
5. Reusing generic evidence or approval payload bytes without testing all three
   signing domains against one another.

## Not in this slice

- `cmd_run` binding (ADR-006 closure; a later slice).
- Cgroup/output lifecycle (SLICE-018).
- The launcher launch-time anchor re-read; it stays in
  `src/ranex/cli/host_confinement.py`, SLICE-017's file.
- ADR-019 verdict-read-channel and ADR-020 structured-cause work; those belong
  to their own kernel slice.
