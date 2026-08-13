# SLICE-019 — host qualification as gate evidence

**Status:** done
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
sidecar, foundation module or kernel field. The claim loader gains an optional
`qualification_report` carrier field. The earlier “no loader field” framing was
wrong: qa-gate proved that it left the real operator path unable to capture the
report, so `cmd_run` signed `suite_results=None` and admission could never admit
the resulting record. This slice supersedes that framing.

Before constructing kernel evidence, shared admission recognizes
`host-qualification`, validates the report deeply instead of interpreting it as
JUnit, re-reads every durable host anchor, and refuses malformed, shallow/empty,
stale, mismatched or ambiguous records. A rejected or absent record
reaches the kernel as absence (`src/ranex/governed_execution/domain/admission.py:1-24`),
and existing `missing_claims` blocks (`src/ranex/governed_execution/domain/verdict.py:390-397`).
The kernel remains byte-exact and pure (`verdict.py:1-10,338-347`).

## Exact owned paths

Only these paths may change in code-impl:

- `governance/gates.yaml`
- `src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py` (optional
  `qualification_report`, confined-path and exact-`--report=` binding rules)
- `src/ranex/bootstrap/composition.py` (surface `qualification_report` to
  `cmd_run` without changing the kernel `Claim`)
- `src/ranex/cli/main.py` (`cmd_run` canonical-JSON report capture into
  `suite_results`, plus shared admission wiring)
- `src/ranex/governed_execution/domain/admission.py` (deep closed-schema/value
  validation plus existing freshness and ambiguity handling)
- `governance/suite_manifest.json`
- `tests/contract/test_qualification_admission.py`
- `tests/e2e/test_run_produces_evidence.py`
- `tests/e2e/test_gating_real_suite.py`
- `tests/integration/test_slice017_native_launcher.py` (refresh only the frozen
  `main.py` digest after this slice's approved operator-path change)
- `docs/slices/SLICE-019-host-qualification-as-gate-evidence.md`
- `docs/adr/ADR-021-host-qualification-is-evidence-not-a-gated-test.md`
- `docs/STATE.md`
- `README.md`

This replaces the prior owned-path list in full; paths omitted here are not
implicitly retained.

Explicitly **NOT** owned (one-way doors / other slices):

- `src/ranex/foundation/qualification.py` (not created — no new domain)
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
`src/ranex/foundation/qualification.py`, and NO kernel `Claim` change.

The catalog claim binds this existing qualify argv and declares
`qualification_report: .local/ranex/qualification/strict-local-v1.json` while
omitting `results_artifact`:

```text
python -m ranex.cli.host_confinement qualify --profile governance/confinement/strict-local-host-v1.json --artifact .local/ranex/libexec/strict-local-v1/ranex-worker-launcher --manifest governance/confinement/native-launcher-build-v1.json --report=.local/ranex/qualification/strict-local-v1.json
```

Its option names and ordering are the existing parser's
(`src/ranex/cli/host_confinement.py:2635-2660`). Qualification is a HOST
operation: `cmd_run` executes it from the governed repository with the host
environment and this repository's `src/` on `PYTHONPATH`, without constructing
or observing a subject materialisation. The resulting Evidence remains bound to
the subject digest computed from the captured HEAD that `gate evaluate` judges.
`qualification_report` mirrors
`results_artifact`'s loader confinement rule
(`src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py:133-151`): it
is optional, a non-empty relative path with no `..`, and must occur in the claim
argv as the exact token `--report=<path>`. The two carrier fields are mutually
exclusive. Composition surfaces this adapter metadata to `cmd_run` without
adding it to the kernel `Claim` (`src/ranex/bootstrap/composition.py:68-95`).
No suite-manifest/JUnit validation may run for this claim: `cmd_run` reads the
named report from the host operation, parses it as JSON, normalizes it to
canonical JSON value bytes/structure, and places that value directly in the
raw record's `suite_results`; shared admission intercepts, extracts and
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
record and deeply validates the closed writer schema at
`src/ranex/cli/host_confinement.py:2568-2617`. In addition to exact top-level
and existing nested key sets, it enforces this value grammar and required
content:

- `digests.profile`, `digests.build_manifest`, and `digests.artifact` are each
  either the writer's bare 64 lowercase hexadecimal characters or
  `sha256:<64 lowercase hexadecimal characters>`; the same grammar applies to
  open-object `sha256` values;
- `primitives.landlock.available` is a boolean and `abi` is a non-boolean
  integer; `seccomp_filter`, `no_new_privs`, `openat2`, and every required
  namespace value are booleans;
- `primitives.namespaces` is non-empty and carries the writer's required
  `user`, `mount`, `pid`, `ipc`, and `network` keys;
- `cgroup` is non-empty and carries `cgroup_kill`, `mount`, `root`,
  `relative_path`, `controllers`, and `probe_transcript`, with the writer-level
  container/scalar types and non-empty content;
- each of `open_objects.bubblewrap` and `open_objects.launcher` is non-empty and
  carries the writer's `path`, `realpath`, `sha256`, `device`, `inode`, `uid`,
  `gid`, `mode`, `mount_id`, `security_capability`, and `filesystem` sub-keys,
  with their writer-level value types and SHA-256 grammar.

This is deliberately grammar plus presence-of-required-content, not full
SLICE-017 probe-value coupling: admission does not reproduce exact probe
transcripts or independently prove every value. A real writer report passes;
a producer-shaped forged report with the right outer shape but empty
confinement content MUST refuse. It then re-reads live `boot_id`,
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
2. Unknown schema, `qualified: false`, missing host fact, malformed digest, or
   empty/missing required confinement content → admission refusal (ADR-021 rows
   9, 13 plus the qa-gate deep-schema correction).
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
7. Real `cmd_run` capture: `ranex run --claim host-qualification --producer
   <id> -- <qualify argv>` captures the `--report` JSON in signed
   `suite_results`, shared admission accepts it, and `gate evaluate` PASSes;
   after one durable host-state fact moves, evaluation FAILs naming
   `host-qualification`. The capture test runs the actual catalog
   `python -m ranex.cli.host_confinement qualify ...` argv as a host operation,
   not a shell stand-in or subject-materialised observation.
   `tests/e2e/test_run_produces_evidence.py` and
   `tests/e2e/test_gating_real_suite.py`.
8. E2E qualify→approve→gate PASS, then change one bound durable fact → FAIL
   naming `host-qualification`. `tests/e2e/test_gating_real_suite.py`.
9. A `host-qualification` Evidence verifies only under `ranex-evidence-v3` (not
   under `ranex-approval-v1`); exact-`SIGNED_FIELDS` refusal holds and
    `subject_digest`/`producer_id` binding is proven.
    `tests/contract/test_qualification_admission.py`.
10. `cmd_task_judge` (the merge-candidate landing-gate path at
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
2. Sending qualification JSON through generic JUnit parsing, or using
   `results_artifact`, instead of capturing the loader-bound
   `qualification_report` as the claim-specific signed carrier.
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
8. Checking only closed key sets while accepting empty namespace, cgroup, or
   open-object mappings and malformed digest values.

## Not in this slice

- General `cmd_run` confinement binding (ADR-006 closure; a later slice).
- Cgroup/output lifecycle (SLICE-018).
- The launcher launch-time anchor re-read; it stays in
  `src/ranex/cli/host_confinement.py`, SLICE-017's file.
- ADR-019 verdict-read-channel and ADR-020 structured-cause work; those belong
  to their own kernel slice.
- Authentication of the CLI `--approver` string; this pre-existing risk is not
  repaired by qualification evidence.
