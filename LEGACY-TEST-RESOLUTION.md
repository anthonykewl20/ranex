# Legacy test governance resolution

> **Status:** non-authoritative executed-evidence record. It is the resolution
> that produced ADR-0021 and is cited by that accepted ADR. It is evidence, not
> a governing decision; see
> `docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md`.
> Kept at the repository root by design because ADR-0021 references it by path.

Date: 2026-07-31
Repository: `/home/soultransit/devtony/ranex`

## CONFIRMED — governing instructions and initial repository state

`AGENTS.md` was read first. Its applicable constraints are:

- product capability code is prohibited except for the bounded first walking
  skeleton;
- governance documents and architecture tooling may be changed;
- generated outputs must never be hand-edited;
- checks must not be weakened to make code pass;
- evidence that invalidates an accepted ADR must be handled by superseding the
  ADR, never by silently rewriting it;
- every numerical or checkable claim in this report must be tied to an executed
  command and working directory.

The initial worktree was already dirty. In particular, `tests/`,
`src/`, `scripts/architecture/generate_contracts.py`,
`scripts/architecture/validate_contracts.py`, and generated contract/report
files existed or were modified before this resolution was started. Those
pre-existing changes are preserved.

Command (working directory `/home/soultransit/devtony/ranex`):

```text
git status --short --branch
```

Output (exit 0):

```text
## bootstrap/pre-upstream...origin/bootstrap/pre-upstream
 M README.md
 M architecture/contracts/hermes-research-promotions.json
 M architecture/contracts/registry-manifest.json
 M architecture/contracts/schema-registry.json
 M docs/HANDOFF.md
 M docs/README.md
 M docs/architecture/README.md
 M docs/architecture/assessments/validation-report.json
 M docs/architecture/rfcs/README.md
 M docs/architecture/rfcs/RFC-0009-record-freshness-as-a-shipped-capability.md
 M schemas/common/hermes-research-provision-v1.schema.json
 M scripts/architecture/generate_contracts.py
 M scripts/architecture/pyproject.toml
 M scripts/architecture/validate_contracts.py
?? AGENTS.md
?? LUNA-ADR7-REPORT.md
?? architecture/records/bootstrap-authorizations/
?? architecture/records/owner-decisions/
?? docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md
?? docs/architecture/reviews/2026-07-31-delivery-model-restructure-assessment.md
?? docs/architecture/reviews/2026-07-31-slice-01-plan.md
?? docs/architecture/reviews/2026-07-31-spike-01-and-02-results.md
?? docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md
?? docs/architecture/rfcs/RFC-0010-authorize-bounded-vertical-product-slices.md
?? governance/
?? pyproject.toml
?? pyrefly.toml
?? scripts/architecture/test_adr17_owner_resolution.py
?? src/
?? tests/
?? uv.lock
```

## ASSUMED

No substantive conclusion is assumed at this stage. The binding scope of
ADR-0010, the ancestry facts, the baseline/disk comparison, the landing-record
resolver behavior, the fail-open behavior, and the stale validation report will
be established independently below.

## CONFIRMED — the governing text and the decision

### Outcome

**B) Rule is obsolete -> supersede it with evidence**

ADR-0010's 2,444-file baseline is not binding on the current orphan lineage.
This conclusion is not based on inconvenience. It follows from ADR-0010's own
subject:

> “Effective revision | The accepted upstream-derived baseline
> `0533e1eaf50ace0eb84435a5c3de05e939fd4daa`”

and:

> “The accepted Hermes upstream-derived source, however, contains inherited
> tests outside that target.”

The rule is a bounded compatibility exception for inherited files in that
specific source. It is not a universal requirement to introduce those files
into unrelated history. The ADR reinforces the exact-subject boundary:

> “A mutable branch name, working-tree path, count alone, subtree name alone, or
> aggregate digest alone is insufficient evidence.”

The current validation subject is not a descendant of the named effective
revision, has no common ancestor with `develop`, has no committed `tests/` path
anywhere in its own ancestry, and contains none of the baseline paths in its
working tree. Importing 2,444 foreign files merely to make the validator green
would manufacture the very “inherited” state the ADR was written to govern; it
would not preserve inherited regression evidence.

ADR-0008 remains fully binding. Its text says:

> “These are the only top-level `tests/` roots.”

It then lists the 18 roots `unit`, `contract`, `integration`, `architecture`,
`acceptance`, `system`, `e2e`, `security`, `performance`, `resilience`,
`migration`, `replay`, `operations`, `qualification`, `effectiveness`,
`evaluation`, `fixtures`, and `builders`. Supersession must therefore remove
only the inapplicable inherited-baseline comparison on the precisely bound
orphan lineage. It must not remove or weaken canonical layout enforcement.

### ADR-expansion freeze check

All four `AGENTS.md` §3.7 conditions are met:

1. The currently authorized first walking skeleton depends on tests under
   ADR-0008.
2. Delaying the decision blocks that implementation because merely creating
   `tests/` activates an impossible foreign-history comparison.
3. The scope and provenance of an accepted 2,444-file migration obligation is
   architecturally significant.
4. The exact Git ancestry, committed path history, baseline manifest, working
   tree, empty proof registries, and validator behavior have all been executed
   and recorded below.

The superseding ADR can therefore be drafted despite the freeze. It cannot
become authoritative until the human owner accepts it; a model verdict cannot
approve governance.

## CONFIRMED — ancestry, path population, and proof population

Command (working directory `/home/soultransit/devtony/ranex`):

```text
printf 'HEAD ancestry:\n'; git rev-list --parents -n 3 HEAD; printf 'source_is_ancestor_of_HEAD:\n'; git merge-base --is-ancestor 0533e1eaf50ace0eb84435a5c3de05e939fd4daa HEAD; printf 'exit=%s\n' "$?"; printf 'HEAD_develop_merge_base:\n'; git merge-base HEAD develop; printf 'exit=%s\n' "$?"; printf 'committed_tests_paths_in_HEAD:\n'; git ls-tree -r --name-only HEAD -- tests | wc -l; printf 'tests_history_in_HEAD_ancestry:\n'; git log --format='%H %s' HEAD -- tests; printf 'working_tree_test_files:\n'; rg --files tests | wc -l
```

Output (the command as a whole exits 0; individual Git results are printed):

```text
HEAD ancestry:
f2c04c1674282052e26648b756481da337b45458 0b23cc5374fe93b4d60b59acc037be72b82bd50f
0b23cc5374fe93b4d60b59acc037be72b82bd50f 1be0d5a6b4885fa158f49be4c704bda7f85b430e
1be0d5a6b4885fa158f49be4c704bda7f85b430e 5d14d4267466583c4e6062db7b4be6459d220c5a
source_is_ancestor_of_HEAD:
exit=1
HEAD_develop_merge_base:
exit=1
committed_tests_paths_in_HEAD:
0
tests_history_in_HEAD_ancestry:
working_tree_test_files:
11
```

The empty output after `tests_history_in_HEAD_ancestry:` is material: the
current lineage has no committed `tests/` history. The 11 current test files
are uncommitted working-tree files.

Command (working directory `/home/soultransit/devtony/ranex`):

```text
printf 'baseline_rows:\n'; jq '[.directory_exceptions[].baseline_files[], .direct_top_level_exception.baseline_files[], .inherited_canonical_scopes[].baseline_files[]] | length' architecture/contracts/legacy-test-layout-policy-v2.json; printf 'baseline_vs_worktree_intersection:\n'; comm -12 <(jq -r '.directory_exceptions[].baseline_files[].path, .direct_top_level_exception.baseline_files[].path, .inherited_canonical_scopes[].baseline_files[].path' architecture/contracts/legacy-test-layout-policy-v2.json | LC_ALL=C sort) <(rg --files tests | LC_ALL=C sort) | wc -l; printf 'baseline_paths_absent_from_worktree:\n'; comm -23 <(jq -r '.directory_exceptions[].baseline_files[].path, .direct_top_level_exception.baseline_files[].path, .inherited_canonical_scopes[].baseline_files[].path' architecture/contracts/legacy-test-layout-policy-v2.json | LC_ALL=C sort) <(rg --files tests | LC_ALL=C sort) | wc -l; printf 'worktree_paths_not_in_baseline:\n'; comm -13 <(jq -r '.directory_exceptions[].baseline_files[].path, .direct_top_level_exception.baseline_files[].path, .inherited_canonical_scopes[].baseline_files[].path' architecture/contracts/legacy-test-layout-policy-v2.json | LC_ALL=C sort) <(rg --files tests | LC_ALL=C sort) | wc -l
```

Output (exit 0):

```text
baseline_rows:
2444
baseline_vs_worktree_intersection:
0
baseline_paths_absent_from_worktree:
2444
worktree_paths_not_in_baseline:
11
```

Command (working directory `/home/soultransit/devtony/ranex`):

```text
jq '[(.migration_proofs | length), (.change_exceptions | length), (.cutover_removal_records | length)]' architecture/contracts/legacy-test-layout-policy-v2.json
```

Output (exit 0):

```text
[
  0,
  0,
  0
]
```

The baseline object is present in the shared object database, but that does not
make it an ancestor of this subject:

```text
HEAD=f2c04c1674282052e26648b756481da337b45458
HEAD_root_commits:
4ee007fcbe40b1afa7c362767005cf2f4508fc3d
HEAD_commit_count:
38
HEAD_contains_baseline_commit:
architecture/validated-baseline-20260728
develop
feature/deterministic-gate-controller-mvp
baseline_object_type:
commit
```

Those lines came from, in the same working directory:

```text
printf 'HEAD=%s\n' "$(git rev-parse HEAD)"; printf 'HEAD_root_commits:\n'; git rev-list --max-parents=0 HEAD; printf 'HEAD_commit_count:\n'; git rev-list --count HEAD; printf 'HEAD_contains_baseline_commit:\n'; git branch --contains 0533e1eaf50ace0eb84435a5c3de05e939fd4daa --format='%(refname:short)' | LC_ALL=C sort; printf 'baseline_object_type:\n'; git cat-file -t 0533e1eaf50ace0eb84435a5c3de05e939fd4daa
```

## CONFIRMED — migration records cannot repair the production path

The active V2 migration schema requires **59** top-level fields, not 58. The
prompt's 58-field figure is therefore disproved by the generated schema; this
does not change the contradiction.

Command (working directory `/home/soultransit/devtony/ranex`):

```text
jq '.. | objects | select(.properties?.proof_type?.const? == "LEGACY_TEST_MIGRATION_PROOF_V2") | (.required | length)' schemas/common/legacy-test-layout-policy-v2.schema.json
```

Output (exit 0):

```text
59
```

`validate_legacy_test_snapshot` defaults `landing_record_resolver` to `None` at
`scripts/architecture/validate_contracts.py:19873`. The production call at
`:20252-20255` supplies only the policy and snapshot rows. Any nonempty proof
then reaches `validate_legacy_landing_stack`; with no resolver, `landing` is
`None` and `LEGACY_TEST_LANDING_RECORD_UNRESOLVED` blocks at `:13043-13046`.
Synthetic fixtures do supply a resolver at `:28669-28673`, but that fixture-only
path cannot make production proofs resolvable.

## CONFIRMED — current validator failure and stale PASS report

Before validation, the on-disk report said `PASS` and had SHA-256
`ee574b0fde9fd17d68ee03cc6cce80794944f6034194123967da3ff5e5c9e836`.
The validator exited 1 with:

```json
{"error":"LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py","status":"FAIL"}
```

After the failure, the on-disk report still said `PASS` and had the identical
SHA-256.

Command (working directory `/home/soultransit/devtony/ranex`):

```text
printf 'report_status_before:\n'; jq -r '.status // .validation_status // "<missing>"' docs/architecture/assessments/validation-report.json; printf 'report_sha256_before:\n'; sha256sum docs/architecture/assessments/validation-report.json; printf 'validator_run:\n'; uv run --project scripts/architecture python scripts/architecture/validate_contracts.py; validator_exit=$?; printf 'validator_exit=%s\n' "$validator_exit"; printf 'report_status_after:\n'; jq -r '.status // .validation_status // "<missing>"' docs/architecture/assessments/validation-report.json; printf 'report_sha256_after:\n'; sha256sum docs/architecture/assessments/validation-report.json
```

Relevant output (the wrapper intentionally continued after the validator's
nonzero exit):

```text
report_status_before:
PASS
report_sha256_before:
ee574b0fde9fd17d68ee03cc6cce80794944f6034194123967da3ff5e5c9e836  docs/architecture/assessments/validation-report.json
validator_run:
{"checks":{...,"legacy_test_baseline_files":2444,...,"production_test_layout_files_scanned":11,...},"error":"LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py","status":"FAIL"}
validator_exit=1
report_status_after:
PASS
report_sha256_after:
ee574b0fde9fd17d68ee03cc6cce80794944f6034194123967da3ff5e5c9e836  docs/architecture/assessments/validation-report.json
```

Cause is confirmed in `validate_contract_tree`: the exception handler at
`:31791-31793` prints the failure and returns 1. The report write occurs only on
the success path at `:31851-31854`. This separate stale-report defect is
reported here and is intentionally **not fixed in this task**, as directed.

## CONFIRMED — separate fail-open defect

At `validate_contracts.py:20209-20220`, absence of `tests/` returns
`validation_status: NOT_ASSESSED`. The success result at `:31794-31856` does not
reject that state and writes overall `status: PASS`.

That contradicts the active bootstrap authorization's guarantee:

> “Absence blocks — `NOT_ASSESSED` is never a pass”

and the Master Architecture Specification glossary:

> “`NOT_ASSESSED` | No attempt was made. Never a pass”

This is a real fail-open independent of whether ADR-0010 applies. Superseding
the foreign baseline must not preserve or recreate it.

The fail-open has been fixed without relaxing any rule. The early
`NOT_ASSESSED` return was replaced by an explicit blocking
`PRODUCTION_TEST_ROOT_MISSING` requirement. No status was demoted, no comparison
was skipped, and the still-applicable ADR-0010 comparison remains unchanged.

Focused verification command (working directory
`/home/soultransit/devtony/ranex`):

```text
uv run --project scripts/architecture python -c "import tempfile; from collections import Counter; from pathlib import Path; import sys; sys.path.insert(0, 'scripts/architecture'); import validate_contracts as v; d=tempfile.TemporaryDirectory(); v.ROOT=Path(d.name); c=Counter();
try: v.validate_production_test_layout(c)
except v.ContractFailure as exc: print(type(exc).__name__ + ':' + str(exc)); print(dict(c))
else: raise SystemExit('unexpected pass')"
```

Output (exit 0 because the harness expected and caught the blocking result):

```text
ContractFailure:PRODUCTION_TEST_ROOT_MISSING:tests
{}
```

## CONFIRMED — superseding record and pin impact

The non-authoritative draft is:

`docs/architecture/reviews/2026-07-31-adr-0010-supersession-draft.md`

It is deliberately outside `docs/architecture/decisions/`: the compiler treats
every `ADR-*.md` there as accepted, while repository rule §3.6 forbids a model
from approving a decision. The draft becomes intended `ADR-0021` only if the
human owner accepts it.

The draft is narrow and fail-closed:

- ADR-0010 remains fully active whenever its source commit is an ancestor.
- Only descendants of exact bootstrap boundary
  `f2c04c1674282052e26648b756481da337b45458` with root
  `4ee007fcbe40b1afa7c362767005cf2f4508fc3d` can establish the seven exact
  non-inheritance facts.
- Every other non-descendant lineage is `UNKNOWN` and blocks.
- A later merge that makes the source commit an ancestor reactivates ADR-0010.
- ADR-0008 is always enforced, and missing `tests/` always fails.

ADR-0010 itself was not edited. Therefore exactly **zero existing ADR-0010
pins move**:

- `ADR10_SOURCE_SHA256` remains
  `45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb`.
- `ADR10_MACHINE_BLOCK_SHA256` remains
  `de5ed30d02ffac788574b319ac9afcc4c1246212b0b015251ac055bd7ef17472`.
- `ADR10_BEHAVIOR_TEMPLATE_SHA256` and
  `ADR10_CLASSIFICATION_TEMPLATE_SHA256` remain unchanged.

Human acceptance would introduce `ADR21_SOURCE_SHA256` and
`ADR21_MACHINE_BLOCK_SHA256`; it would not move the ADR-0010 pins. Their values
cannot be computed until the owner finalizes and accepts the exact bytes.

## CONFIRMED — required validation

### Contract generation

Command (working directory `/home/soultransit/devtony/ranex`):

```text
uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
```

Output (exit 0):

```text
{"assessments": 41, "projections": 10, "registries": 46, "schemas": 157}
```

### Contract validation

Command (working directory `/home/soultransit/devtony/ranex`):

```text
uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
```

Output (exit 1; the validator emits one JSON object):

```text
{"checks": {"accepted_adrs": 20, "adr10_rules": 10, "allowed_test_roots": 18, "legacy_test_baseline_files": 2444, "legacy_test_directory_exceptions": 29, "observed_test_roots": 6, "production_test_layout_files_scanned": 11, "...": "all other completed check counters emitted by the validator"}, "error": "LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py", "status": "FAIL"}
```

The displayed `...` is report abbreviation, not validator output. The actual
one-line output included all check counters and ended exactly:

```text
"error": "LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py", "status": "FAIL"}
```

The nonzero result is expected and retained. The proposed superseding record
has no authority until human acceptance, so using it to skip the active
comparison now would itself be the forbidden bypass.

### Product tests

Command (working directory `/home/soultransit/devtony/ranex`):

```text
uv run pytest -q
```

Output (exit 0):

```text
....................................                                     [100%]
36 passed in 0.19s
```

### Strict product type check

Command (working directory `/home/soultransit/devtony/ranex`):

```text
uv run --with pyrefly==1.1.1 pyrefly check
```

Output (exit 0):

```text
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
```

### Post-validation stale-report confirmation

Command (working directory `/home/soultransit/devtony/ranex`):

```text
printf 'post_required_validation_report_status:\n'; jq -r '.status' docs/architecture/assessments/validation-report.json; printf 'post_required_validation_report_sha256:\n'; sha256sum docs/architecture/assessments/validation-report.json; printf 'report_bound_validator_digest:\n'; jq -r '.validator_digest' docs/architecture/assessments/validation-report.json; printf 'current_validator_digest:\n'; sha256sum scripts/architecture/validate_contracts.py
```

Output (exit 0):

```text
post_required_validation_report_status:
PASS
post_required_validation_report_sha256:
ee574b0fde9fd17d68ee03cc6cce80794944f6034194123967da3ff5e5c9e836  docs/architecture/assessments/validation-report.json
report_bound_validator_digest:
sha256:660c02af79407273e72b57331bac6bf623c0b2055a9f95e793a5b7437b2cdb8e
current_validator_digest:
2daaba7da4c27485267d556e62f9c238f4541043eb27ac4142085298dcc8680a  scripts/architecture/validate_contracts.py
```

The report is therefore stale in two independently visible ways: it says
`PASS` after an exit-1 validation, and it binds a validator digest different
from the current validator. It was not edited by hand and was not repaired.

### Patch hygiene

Command (working directory `/home/soultransit/devtony/ranex`):

```text
git diff --check
```

Output (exit 0):

```text
<no output>
```

## ASSUMED

No evidence claim in this resolution depends on an unexecuted assumption.

The only unresolved governance fact is human acceptance: this report does not
assume the owner will accept the draft. Until that happens, ADR-0010 remains the
active compiled rule and contract validation remains nonzero.

## Remaining risk and required next authority

1. **Owner acceptance is required.** The draft is evidence and a proposed
   decision, not authority.
2. **The applicability projection is not implemented.** After acceptance, the
   generator and validator must add the versioned, digest-pinned lineage
   contract and its ten predeclared acceptance tests. Doing that before
   acceptance would be a bypass.
3. **Production migration resolution remains incomplete.** On lineages where
   ADR-0010 applies, the production call still supplies no landing-record
   resolver. This does not justify weakening the record; it remains a separate
   blocking implementation defect.
4. **The validation report remains stale on failure.** It can advertise `PASS`
   after the validator exits 1. This was explicitly reported and not fixed.
5. **The worktree was already dirty.** Generated artifacts, product code,
   tests, and several documents contain pre-existing changes. This task did not
   attribute or discard them.

The present changes are limited to:

- this executed-evidence resolution;
- the proposed human-owned superseding record; and
- the independent fail-closed repair that makes a missing `tests/` directory
  fail `PRODUCTION_TEST_ROOT_MISSING`.

No ADR-0010 baseline check was relaxed, deleted, demoted, or bypassed.
