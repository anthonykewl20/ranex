# Slice 1 Phase 5 evidence — closure refused

| Field | Value |
|---|---|
| Date | 2026-07-31 |
| Subject | Git tree for `HEAD`; `sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e` |
| Repository | `/home/soultransit/devtony/ranex` |
| Phase 5 result | **NOT CLOSED** |
| Bootstrap authorization | `BOOTSTRAP-AUTH-001` remains **`ACTIVE`** |

The walking skeleton runs and its narrow gate proposition is confirmed. Slice 1
cannot be closed because its own discharge and size conditions are not all met.
This record reports the contradictions rather than converting them into a pass.

## 1. WHAT WAS BUILT

`src/ranex/` contains the walking-skeleton implementation. Its entry point is:

```text
PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner
```

The implementation path is:

```text
CLI -> composition root -> authored YAML slice-gate loader
    -> pure evidence verdict -> optional SQLite hash-chain journal
```

It does **not** load a generated contract-tree gate.

### Modules

| Module | Executed line count | What it does |
|---|---:|---|
| `bootstrap/composition.py` | 73 | Wires the slice YAML loader, verdict function, and optional SQLite journal. |
| `cli/main.py` | 127 | Parses `gate evaluate`, derives the exact Git-tree subject digest, loads JSON evidence, prints the verdict, and sets the exit code. |
| `cli/confinement.py` | 44 | Defines path/remote confinement checks. **It is not imported or called by `cli/main.py`.** |
| `foundation/canonical.py` | 26 | Stable sorted JSON and SHA-256 helpers used by subject and record digests. |
| `foundation/identity.py` | 53 | Canonical prefix plus UUIDv7 identity parsing for the richer policy model; not on the Slice 1 CLI path. |
| `governed_execution/domain/verdict.py` | 207 | Claim/evidence/gate types and pure `PASS`/`FAIL` evaluation. A record satisfies a claim only when claim ID and subject match and `exit_code == 0`. |
| `governed_execution/adapters/persistence/sqlite/journal.py` | 94 | SQLite append-only triggers, hash-chain append/read/replay verification. |
| `governed_execution/api/__init__.py` | 19 | Re-exports governed-execution public contracts. |
| `policy/adapters/configuration/yaml/slice_gate_loader.py` | 99 | Loads the one simple authored YAML action-gate format used by the CLI. |
| `policy/adapters/configuration/yaml/gate_catalog_loader.py` | 174 | Loads a richer R&D action-gate catalog; present but not used by the CLI. |
| `policy/domain/gates.py` | 101 | Rich policy catalog/domain types used by SPIKE-01 comparison, not by the CLI verdict path. |
| `policy/api/contracts.py` | 15 | Re-exports the rich policy-domain types. |
| 18 one-line package/namespace `__init__.py` files | 18 | Namespace markers, including empty `assurance` and application scaffolding; the 19-line governed-execution API initializer is listed separately. |
| **Total** | **1,050** | Physical lines; because `HEAD` tracks zero `src/ranex` files, all 1,050 are net-new on this working tree. |

Executed from `/home/soultransit/devtony/ranex`:

```text
$ git ls-tree -r --name-only HEAD -- src/ranex | wc -l
0
$ find src/ranex -type f -name '*.py' -print0 | sort -z | xargs -0 wc -l
    1 src/ranex/__init__.py
    1 src/ranex/assurance/__init__.py
    1 src/ranex/assurance/api/__init__.py
    1 src/ranex/assurance/domain/__init__.py
   73 src/ranex/bootstrap/composition.py
    1 src/ranex/cli/__init__.py
   44 src/ranex/cli/confinement.py
  127 src/ranex/cli/main.py
    1 src/ranex/foundation/__init__.py
   26 src/ranex/foundation/canonical.py
   53 src/ranex/foundation/identity.py
    1 src/ranex/governed_execution/__init__.py
    1 src/ranex/governed_execution/adapters/__init__.py
    1 src/ranex/governed_execution/adapters/persistence/__init__.py
    1 src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
   94 src/ranex/governed_execution/adapters/persistence/sqlite/journal.py
   19 src/ranex/governed_execution/api/__init__.py
    1 src/ranex/governed_execution/application/__init__.py
    1 src/ranex/governed_execution/domain/__init__.py
  207 src/ranex/governed_execution/domain/verdict.py
    1 src/ranex/policy/__init__.py
    1 src/ranex/policy/adapters/__init__.py
    1 src/ranex/policy/adapters/configuration/__init__.py
    1 src/ranex/policy/adapters/configuration/yaml/__init__.py
  174 src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py
   99 src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py
    1 src/ranex/policy/api/__init__.py
   15 src/ranex/policy/api/contracts.py
    1 src/ranex/policy/domain/__init__.py
  101 src/ranex/policy/domain/gates.py
 1050 total
```

The slice definition's bound is at most 1,000 net product-source lines. The
executed count is 1,050, so the bound is exceeded by 50. Section 13 says
exceeding the bound **ends the slice**; it does not redefine the count.

## 2. THE THESIS TEST — the reason this slice existed

The premise is:

> Rules compiled into code change what an agent produces. Rules in a prompt do
> not.

The exact sequence below confirms a narrower fact: the implemented gate checks
claim ID, a caller-supplied subject digest, and zero exit code; record existence
alone does not pass. A final integrity check found that the commands ran in a
dirty working tree while the digest names `HEAD^{tree}`, which contains none of
the Slice 1 files. The sequence therefore **does not prove that evidence
supports the claimed subject**. It proves only that the gate accepts records
whose fields say it does. It also does not confirm the whole premise: this gate
is loaded from authored YAML rather than the compiled tree, is advisory,
observed no changed agent output, and made no prompt comparison.

All commands in this section ran from
`/home/soultransit/devtony/ranex`.

### a. No evidence: refusal names both missing claims

The evidence path was first checked to be absent.

```text
$ test ! -e /tmp/ranex-slice01-no-evidence.json
$ PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner --evidence /tmp/ranex-slice01-no-evidence.json
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: contracts-validated, tests-executed
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
EXIT=1
```

### b. Real commands were run and their real exit codes recorded

Successful test evidence:

```text
$ uv run pytest -q
....................................                                     [100%]
36 passed in 0.19s
EXIT=0
```

Successful contract evidence was produced by the exact validator command in
§3. Its JSON reported `"status":"PASS"`,
`"scope":"EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY"`,
`"runtime_validation":"NOT_ASSESSED"`, and the process exited 0.

To exercise the nonzero branch with real rather than invented evidence, a
deliberately invalid test target was actually invoked:

```text
$ uv run pytest -q tests/does-not-exist.py
ERROR: file or directory not found: tests/does-not-exist.py


no tests ran in 0.00s
EXIT=4
```

The failed-evidence record used that exact command and exit 4; the contract
record used the executed validator command and exit 0. No exit code was edited
into success.

### c. Present but failed evidence: still refused

```text
$ PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner --evidence governance/.slice-01-failed-evidence.json
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: tests-executed
      subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
EXIT=1
```

The temporary failed-evidence file was removed after this execution.

### d. Both claimed commands passed: the same subject passed

`governance/evidence.json` now records the two commands executed in §3, both
with exit 0 and the exact subject digest above.

```text
$ PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --approver owner
PASS  gate=landing  subject=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
EXIT=0
```

That `PASS` is a real gate output but is **not valid exact-subject evidence**.
Executed after the sequence:

```text
$ git status --short -- src tests governance pyproject.toml pyrefly.toml uv.lock
?? governance/
?? pyproject.toml
?? pyrefly.toml
?? src/
?? tests/
?? uv.lock
$ git ls-tree -r --name-only HEAD -- src tests governance pyproject.toml pyrefly.toml uv.lock | wc -l
0
$ git rev-parse 'HEAD^{tree}'
0beb9bb4e29ac9fb1840169bb4164f578890500d
GATE_SUBJECT=sha256:9edd77be549282954b4a40a25d549c5923f4505f672a2bc4365f9f396793fe9e
```

The validator and pytest observed the untracked working-tree implementation;
the gate subject observed the committed tree with zero scoped files.

### Thesis-test conclusion

**CONFIRMED:** absence failed; a present nonzero record still failed; matching
zero-exit fields passed. The same inputs also produced identical stdout, stderr
and journal records in two executed runs, and the chain verified.

**DISPROVED for this run:** the JSON records do not establish support for the
claimed exact subject. The CLI trusts their fields, does not execute the named
command, does not require a clean worktree, does not authenticate
`producer_id`, and does not prove the exit code was produced from the named Git
tree. No agent output or prompt-only comparator was observed. The requested
thesis proof was not achieved; the broad product thesis remains `UNRESOLVED`.

## 3. EXECUTED VERIFICATION — every gate, with real output

The four required final commands were run from the repository root after the
documentation edits. The validator emits one long JSON line; the exact current
line is also materialized as
`docs/architecture/assessments/validation-report.json`. The fields and counts
quoted below are exact values from that output, not a runtime claim.

### Contract validator

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
status=PASS
scope=EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY
runtime_validation=NOT_ASSESSED
legacy_test_baseline_files=2444
production_test_layout_files_scanned=10
production_topology_files_scanned=30
topology_rules=18
source_topology_validation=PASS
test_layout_validation=CANONICAL_TOPOLOGY_PASS
test_layout_migration=NOT_APPLICABLE_NO_INHERITED_SUBJECT
EXIT=0
```

Those `name=value` lines are a faithful field extraction from the command's
single JSON output, performed only to make the record readable; the command
itself was also run unfiltered and exited 0.

### Record freshness

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --project scripts/architecture python scripts/architecture/check_record_freshness.py
records fresh: 21 ADRs, 10 RFCs, no stale claims
EXIT=0
```

### Product tests

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run pytest -q
....................................                                     [100%]
36 passed in 0.23s
EXIT=0
```

### Product type check

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --with pyrefly==1.1.1 pyrefly check
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
EXIT=0
```

The count is invocation-dependent because these are different configured
projects and scopes. The architecture-tooling invocation was also executed:

```text
working directory: /home/soultransit/devtony/ranex/scripts/architecture
$ uv run --group typecheck pyrefly check
 INFO Checking project configured at `/home/soultransit/devtony/ranex/scripts/architecture/pyproject.toml`
...
 INFO 243 errors (6 warnings not shown)
EXIT=1
```

Therefore **0** is the product-code result for the exact required root
invocation; **243** is the separate architecture-tooling debt from its own
working directory. Neither number is substituted for the other.

## 4. WHAT THE SLICE DISPROVED — more important than what it confirmed

### ADR-0008 and ADR-0010 were jointly unsatisfiable on this branch

Executed from `/home/soultransit/devtony/ranex`:

```text
$ git merge-base HEAD develop
EXIT=1
$ git rev-parse --verify HEAD
f2c04c1674282052e26648b756481da337b45458
$ git rev-parse --verify develop
0533e1eaf50ace0eb84435a5c3de05e939fd4daa
```

Before ADR-0021's exact-lineage resolution, ADR-0008 required canonical tests
while creating `tests/` activated ADR-0010's comparison to a 2,444-file foreign
baseline that this non-inherited history could not satisfy. ADR-0021 now makes
the baseline comparison not applicable only on its exact bound lineage; it does
not erase the contradiction that Slice 1 exposed.

### Two governance contracts were dormant while their subject trees were empty

The exact `HEAD` version of the old validator was executed in memory. With an
empty root it returned:

```text
ABSENT_TESTS_RESULT={'validation_status': 'NOT_ASSESSED', 'canonical_test_topology_status': 'NOT_ASSESSED', 'baseline_file_count': 2444, 'remaining_inherited_file_count': None, 'migrated_or_retired_file_count': None, 'changed_in_place_file_count': None, 'new_canonical_file_count': None}
ABSENT_TESTS_COUNTS={'observed_test_roots': 0, 'production_test_layout_files_scanned': 0}
```

The same old function against the current `tests/` tree activated the foreign
baseline comparison:

```text
PRESENT_TESTS_RESULT=ContractFailure:LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py
PRESENT_TESTS_COUNTS={'observed_test_roots': 5, 'production_test_layout_files_scanned': 10}
EXIT=0
```

The current source-topology function was then executed with an absent and a
present `src/ranex`:

```text
ABSENT_SRC_COUNTS={'production_topology_files_scanned': 0}
PRESENT_SRC_COUNTS={'observed_test_roots': 5, 'production_test_layout_files_scanned': 10, 'adr21_lineage_provenance_facts': 7, 'adr21_lineage_applicability_resolutions': 1, 'production_topology_files_scanned': 30}
TOPOLOGY_RULE_COUNT=18
EXIT=0
```

Creating `tests/` therefore exposed the dormant 2,444-file policy comparison;
creating `src/ranex` activated source scanning under the 18-rule ADR-0007
topology registry. The live validator now fails when `tests/` is absent and
scans the present source, so this particular dormancy is no longer hidden.

### A fail-open converted `NOT_ASSESSED` into overall `PASS`

**Executed:** the old validator function returned the `NOT_ASSESSED` object
quoted above when `tests/` was absent.

**Statically reviewed:** the old `validate_contract_tree` success path emitted
`"status": "PASS"` without rejecting that state. That was the conversion; this
part is source inspection, not a claim that the historical whole-program run
was repeated here.

**Executed current correction:** the focused empty-root call now returns the
blocking result:

```text
ContractFailure:PRODUCTION_TEST_ROOT_MISSING:tests
EXIT=0
```

The harness exited 0 because it expected and caught the `ContractFailure`.

### SPIKE-01 disproved document -> registry -> runtime closure by wiring

The current compiled registry and current kernel types were compared and
constructed directly:

```text
REGISTRY_GATE_COUNT=21
REGISTRY_GATE_FIELDS=['bridge_rule_id', 'evidence_role', 'freshness_rule', 'gate_id', 'noncompensating', 'required_result', 'tier_id']
KERNEL_GATE_FIELDS=['gate_id', 'action', 'rules']
ATTEMPT_1=TypeError:GateDefinition.__init__() got an unexpected keyword argument 'bridge_rule_id'
ATTEMPT_2=ValueError:identity must be a lowercase prefix plus UUIDv7
DERIVABLE_RULE_FIELDS=[]
ATTEMPT_3=ValueError:required_claim_ids must not be empty
INVENTED_FIELDS=['action', 'rules[].enforcement', 'rules[].resolution', 'rules[].required_claim_ids', 'canonical gate identity']
EXIT=0
```

The compiled registry holds readiness gates (`evidence_role` -> tier). The
kernel needs action gates (`action` -> rules). Five fields would have to be
invented. The document -> registry -> runtime path is **not closed**, and Slice
1 did not close it; the live CLI loads `governance/gates.yaml`.

### Phase 5 also disproved Slice 1's own completion claims

- The 1,050-line source count exceeds the 1,000-line bound.
- The gate subject contains zero Slice 1/project files while the verification
  commands ran against their untracked working-tree versions. Passing evidence
  is therefore bound to the wrong execution state.
- No collected test names duplicate **rule** IDs, mid-append failure, or a real
  concurrent evaluation. The purported concurrency test performs two
  sequential appends.
- A focused duplicate-rule catalog was accepted:

  ```text
  DUPLICATE_RULE_IDS_RESULT=ACCEPTED:DUPLICATE
  ```

- The confinement helper is not called by the CLI. A real temporary second
  repository, with matching evidence, passed:

  ```text
  PASS  gate=landing  subject=sha256:fdd3141d35bab285981aab4c7ffaadfffe450af41a9689fa87a1cd90d003aacf
  SECOND_REPOSITORY_EXIT=0
  HARNESS_EXIT=0
  ```

- The evaluation record fields are
  `['approver_id', 'considered', 'failing_rule', 'gate_id', 'missing_claims',
  'reason', 'subject_digest', 'verdict']`; executed inspection printed
  `HAS_SUBJECT_LANE=False`.

## 5. WHAT IS STILL NOT TRUE

- The compiled contract tree still has **no runtime consumer**. A scoped
  `rg` over `src`, `tests`, and `governance` found only the loader docstring
  saying it deliberately does not load `architecture/contracts/`.
- The CLI is advisory only and is **not a required merge blocker**. The only
  repository workflow is `.github/workflows/architecture-contracts.yml`; an
  executed search found no `ranex.cli.main`, `ranex gate`, or `gate evaluate`
  invocation there. Remote branch-protection state was not independently
  assessed in this Phase 5 run.
- No readiness tier is declared. Executed inspection of
  `readiness-tiers.json` printed:

  ```text
  CURRENT_STANDING={'assessment_record_count': 0, 'capability_score': None, 'evidence_binding_count': 0, 'implementation_start_authorized': False, 'implementation_start_state': 'NOT_ASSESSED', 'production_authorized': False, 'production_state': 'NOT_ASSESSED', 'runtime_validation_status': 'NOT_ASSESSED', 'subject_manifest_count': 0, 'transition_fact_count': 0}
  CATALOG_STATUS='DEFINITION_ONLY_NOT_ASSESSED'
  ```

- The statement “slice evidence is quarantined from every `READY-*` gate” is
  **not executable truth**. `QUARANTINE-001` and
  `PRE_READINESS_PRODUCT_SLICE` occur in rejected draft `RFC-0010`, not in
  `src/`, tests, schemas, or generated contracts; the runtime record has no
  `subject_lane`. Slice evidence is currently unable to satisfy readiness
  because no runtime readiness consumer or bridge exists. That absence is not
  the promised quarantine mechanism and must not be reported as one.
- Evidence authenticity is not established. Any writer can place `exit_code: 0`
  and `producer_id: "worker"` in the JSON file; the gate does not reproduce or
  authenticate those observations.
- Exact-subject execution is not established. The gate hashes the committed
  `HEAD` tree but does not isolate commands from dirty/untracked working-tree
  content; this Phase 5 run demonstrated the mismatch directly.
- Repository confinement is not an end-to-end property. The helper has passing
  tests, but the CLI bypasses it and accepted a second repository.

## 6. MAP UPDATE

`docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md` is updated to version
`1.1.0` on this evidence:

- **Promoted, narrowly:** the Slice 1 YAML gate's absent/nonzero/zero **field**
  behavior; its local CLI existence; and identical-output evaluation for the
  executed path. Exact-subject evidence support was not promoted.
- **Not promoted:** the broad product thesis, generated-tree enforcement,
  evidence authenticity, append-journal crash/concurrency behavior, readiness,
  or the full intent-to-landed flow.
- **Corrected/demoted:** “CLI does not exist,” “kernel exists only in the tracer,”
  “no runtime emits a verdict,” repository confinement, and the claimed
  executable slice-evidence quarantine.
- **Risk register:** `RISK-01` is narrowed, not closed; `RISK-10` records
  unauthenticated evidence; `RISK-11` records the failed discharge audit.
- **Slice Ledger:** the Slice 1 row records both the bounded validations and the
  ADR conflict, dormant contracts, fail-open, registry mismatch, size breach,
  missing failure-mode evidence, unwired confinement, and absent quarantine.

No section was promoted on the strength of a passing test alone.

## 7. DISCHARGE BOOTSTRAP-AUTH-001

The authorization's conditions were checked one by one.

| # | Condition | Result | Evidence |
|---:|---|---|---|
| 1 | Every `BC-1` ... `BC-7` has an executed, passing test | **MET** | `uv run pytest --collect-only -q` listed named BC tests; `uv run pytest -q` reported 36 passed. The live thesis sequence separately exercised BC-1/BC-2 behavior. |
| 2 | Every Slice definition §9 failure mode has an executed test | **NOT MET** | Duplicate rule IDs are accepted; no mid-append failure test exists; the “two journals” test is sequential, not concurrent; confinement tests exercise only an unwired helper; a second-repository evaluation actually passed. |
| 3 | The command blocked a real change in this repository, output recorded | **NOT MET** | §2(a) refused the old committed `HEAD` tree, but the Slice 1 change and its tests are untracked. `HEAD` contains zero scoped Slice 1/project files, so the command did not evaluate or block the actual Slice 1 change. |
| 4 | Verification separates executed from statically reviewed | **MET** | This record labels executed commands separately from static inspection, especially in the fail-open finding. |
| 5 | MAS updated with validated and disproved findings | **MET** | §6 and the MAS §13 Slice Ledger row. |

Not all discharge conditions are met. Independently, the slice is not complete
under its own size rule: 1,050 net-new source lines exceed the 1,000-line bound.
Therefore `architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md`
remains **`ACTIVE`** and was not edited to look tidy.

Term 5 is unchanged and controlling:

> The permanent authorization issuance mechanism is a **REQUIRED PREREQUISITE
> before any second implementation slice**.

No second slice is authorized. The active bootstrap exception permits work only
on bringing this already-defined first slice to its own discharge conditions;
it grants no unrelated product scope.

### CONFIRMED, ASSUMED, and remaining risk

**CONFIRMED by execution:** the four-part gate behavior; real command exits;
identical repeated output/records; 36 tests; root pyrefly 0; tooling pyrefly 243;
contract/freshness passes; ancestry failure; dormant old-validator behavior;
current fail-closed missing-test result; 21 readiness gates versus the kernel
shape; 1,050 source lines; duplicate-rule acceptance; second-repository pass;
absence of `subject_lane` in an evaluation record; and zero Slice 1/project
paths in the committed gate subject.

**Confirmed by static review, not execution:** the old whole-validator success
aggregation did not reject `NOT_ASSESSED`; the CLI has no confinement call site;
the collected test bodies do not create concurrent writers or inject a
mid-append failure; the workflow contains no Slice 1 CLI job.

**ASSUMED:** no claim needed for discharge is assumed. Remote GitHub
branch-protection configuration was not assessed. The honesty of future JSON
evidence producers is explicitly **not assumed**.

**Remaining risk:** a writer can fabricate passing evidence; the CLI can govern
another repository; optional journaling is not proven at the declared failure
boundaries; duplicate rule IDs pass; compiled readiness policy remains
disconnected; no executable readiness quarantine exists; verification can run
against dirty bytes absent from the subject digest; and the first slice remains
over its size bound. These are closure blockers, not deferred polish.
