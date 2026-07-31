# ADR-0021 Promotion Record

Promotion date: 2026-07-31

Authority: the human owner explicitly accepted
`docs/architecture/reviews/2026-07-31-adr-0010-supersession-draft.md`.
This record reports execution of that decision; it does not treat a model
verdict as approval.

This file is updated incrementally. Commands below were executed from
`/home/soultransit/devtony/ranex` unless a different working directory is
stated.

## CONFIRMED

### Pre-promotion lineage and immutable inputs

Command:

```sh
git rev-parse HEAD
git rev-list --max-parents=0 HEAD
git merge-base --is-ancestor f2c04c1674282052e26648b756481da337b45458 HEAD
printf 'boundary_is_ancestor_exit=%s\n' "$?"
git merge-base --is-ancestor 0533e1eaf50ace0eb84435a5c3de05e939fd4daa HEAD
printf 'adr10_source_is_ancestor_exit=%s\n' "$?"
git merge-base --is-ancestor 4ee007fcbe40b1afa7c362767005cf2f4508fc3d f2c04c1674282052e26648b756481da337b45458
printf 'root_is_boundary_ancestor_exit=%s\n' "$?"
git ls-tree -r --name-only f2c04c1674282052e26648b756481da337b45458 -- tests | wc -l
git rev-list f2c04c1674282052e26648b756481da337b45458 --objects -- tests | wc -l
```

Output:

```text
f2c04c1674282052e26648b756481da337b45458
4ee007fcbe40b1afa7c362767005cf2f4508fc3d
boundary_is_ancestor_exit=0
adr10_source_is_ancestor_exit=1
root_is_boundary_ancestor_exit=0
0
0
```

The exact validation commit is the bootstrap boundary; its repository root is
the accepted root, the ADR-0010 source is not its ancestor, and neither its tree
nor its complete ancestry contains a committed `tests/` path.

Command:

```sh
sha256sum architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md \
  docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md \
  docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
```

Output:

```text
f517be8da802aee6fe46dfa4293da294b618cb982bd836413b3663bff3ee51d8  architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md
368d5e415f76ebb5062f58a8692a61ea68df650016aab821c68d1e04dbdadc5a  docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md
45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb  docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
```

These bytes match the three draft pins.

### Promoted decision pins

Command:

```sh
sha256sum docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md
python - <<'PY'
from pathlib import Path
import hashlib, re
path = Path('docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md')
text = path.read_text()
match = re.findall(r'<!-- BEGIN ADR21 LEGACY TEST LINEAGE APPLICABILITY -->\s*```yaml\n(.*?)\n```\s*<!-- END ADR21 LEGACY TEST LINEAGE APPLICABILITY -->', text, re.S)
print(f'marked_block_count={len(match)}')
print(f'marked_block_sha256={hashlib.sha256(match[0].encode()).hexdigest()}')
PY
```

Output:

```text
1b6ca0051d3eb406b299f12b7d24a22b8d96990111bbca3fe922e6c17a5e45ee  docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md
marked_block_count=1
marked_block_sha256=80e195ec795e8702bc4fccf13916ae039e04600af99956e4b46f4ca307d05567
```

Those values are pinned as `ADR21_SOURCE_SHA256` and
`ADR21_MACHINE_BLOCK_SHA256` in both the generator and validator.

### Promotion and generated projection

Confirmed source changes:

- `ADR-0021-limit-adr-0010-to-inherited-lineage.md` has one canonical H1,
  exactly one `ADR ID`, `Version`, and `Status` header row, and status
  `ACCEPTED`.
- `SOURCE_OF_TRUTH.md` declares the exact 21-file accepted-ADR closed set.
- The retained review draft is marked `SUPERSEDED_BY_PROMOTION` and links to
  ADR-0021.
- The MAS §9 index, live README ranges/counts, AGENTS state, HANDOFF state, and
  pinned architecture-practice normative source set include ADR-0021.
- `docs/architecture/rfcs/README.md` states neither an accepted-ADR range nor
  an accepted-ADR count, so this promotion required no edit to that index.
- The generator emits
  `architecture/contracts/legacy-test-lineage-applicability-v1.json` and
  `schemas/common/legacy-test-lineage-applicability-v1.schema.json`; normal
  regeneration adds both to the generated-output authority, schema registry,
  licensing projection, and registry manifest.

The generated applicability resolver has three closed outcomes:

1. `ADR0010_APPLIES` when the ADR-0010 source is an ancestor. This branch wins
   before evaluation of the bootstrap exception.
2. `NOT_APPLICABLE_NO_INHERITED_SUBJECT` only for the exact bootstrap lineage
   after all seven independently bound provenance conditions pass.
3. `UNKNOWN_BLOCKING` for every other non-descendant lineage.

The non-inherited branch independently requires `tests/`, enforces ADR-0008
canonical roots, rejects direct files, symlinks, malformed Python, baseline
recontamination, and invented migration/change/cutover records. No ADR-0010
record rule was changed.

### Findings encountered without weakening checks

The first generation attempt failed closed with:

```text
ValueError: Architecture practice profile normative accepted-ADR source set/order drift
```

ADR-0021 was added to that closed source set and its separate profile digest pin
was recomputed.

Validator iterations then exposed, in order:

```text
LEGACY_TEST_UNREGISTERED_ROOT:tests/__pycache__/__init__.cpython-314.pyc
TOPOLOGY_ADAPTER_WIRING_OUTSIDE_COMPOSITION:src/ranex/cli/main.py:ranex.governed_execution.adapters.persistence.sqlite.journal
TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT:src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py:ranex.governed_execution.domain.verdict
TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE:policy->governed_execution
```

Only generated bytecode caches were removed. The walking-skeleton confinement
test was moved to the canonical `tests/security/` root. Concrete adapter wiring
was routed through the existing composition root, and the policy loader now
returns policy-owned scalar definitions that composition translates to the
governed-execution public API. No topology or lineage check was relaxed.

The first product-test rerun then reported:

```text
2 failed, 34 passed in 0.25s
```

The policy-owned definition restored the pre-existing loader contract and its
non-blocking-gate refusal. The final rerun passed all 36.

### Ten predeclared acceptance tests

The validator executes all ten tests on every run. The final validation report
records:

```text
checks.adr21_acceptance_tests=10
checks.adr21_provenance_negative_cases=7
checks.adr21_invented_provenance_negative_cases=3
checks.adr21_contract_mutation_cases=7
```

Test 1 dispatches a complete 2,444-row baseline snapshot through the unchanged
`validate_legacy_test_snapshot` function. Test 10 requires the existing
ADR-0010 positive and negative fixture denominators before it can pass.

### ADR-0010 remains active on inherited lineage

Command:

```sh
uv run --project scripts/architecture python - <<'PY'
from pathlib import Path
import importlib.util
import sys

root = Path.cwd()
script_root = root / 'scripts/architecture'
sys.path.insert(0, str(script_root))
path = script_root / 'validate_contracts.py'
spec = importlib.util.spec_from_file_location(
    'ranex_contract_validator', path
)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
contract = validator.load_json(
    root / 'architecture/contracts/'
    'legacy-test-lineage-applicability-v1.json'
)
policy = validator.load_json(
    root / 'architecture/contracts/legacy-test-layout-policy-v2.json'
)
facts = {
    'validation_commit_sha1': 'constructed-descendant',
    'source_commit_is_ancestor': True,
    'boundary_commit_is_ancestor': False,
    'root_is_boundary_ancestor': False,
    'boundary_root_commit_sha1': '',
    'boundary_committed_test_path_count': 1,
    'boundary_ancestry_test_commit_count': 1,
    'boundary_baseline_path_intersection_count': 1,
    'bootstrap_authorization_digest_matches': False,
    'walking_skeleton_definition_digest_matches': False,
}
outcome = validator.resolve_legacy_test_lineage_outcome(contract, facts)
snapshot = [
    {
        'path': row['path'],
        'mode': row['mode'],
        'content_sha256': row['content_sha256'],
    }
    for row in validator.legacy_test_policy_rows(policy)
]
result = validator.validate_test_snapshot_for_lineage(
    contract, policy, snapshot, outcome
)
print(f"source_commit_is_ancestor={facts['source_commit_is_ancestor']}")
print(f"lineage_outcome={outcome}")
print(f"baseline_validation_status={result['validation_status']}")
print(f"baseline_file_count={result['baseline_file_count']}")
print(
    "remaining_inherited_file_count="
    f"{result['remaining_inherited_file_count']}"
)
PY
```

Output:

```text
source_commit_is_ancestor=True
lineage_outcome=ADR0010_APPLIES
baseline_validation_status=MIGRATION_EXCEPTION_ACTIVE
baseline_file_count=2444
remaining_inherited_file_count=2444
```

Quoted evidence: **`lineage_outcome=ADR0010_APPLIES`** and
**`remaining_inherited_file_count=2444`**. The deliberately invalid exception
facts do not bypass the inherited branch; the unchanged baseline comparison
still binds all 2,444 files.

### Final required verification

Command:

```sh
uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
```

Output:

```text
{"assessments": 41, "projections": 10, "registries": 47, "schemas": 158}
```

Command:

```sh
uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
```

The command exited 0 and emitted the full JSON report now stored at
`docs/architecture/assessments/validation-report.json`. Its decisive exact
fields are:

```text
status=PASS
test_layout_validation=CANONICAL_TOPOLOGY_PASS
test_layout_migration=NOT_APPLICABLE_NO_INHERITED_SUBJECT
checks.accepted_adrs=21
checks.adr21_acceptance_tests=10
checks.schema_documents=158
checks.schema_registry_entries=154
checks.schema_registry_historical_exceptions=4
```

The `158 / 154 / 4` schema counts confirm that the earlier schema-registry
reconciliation still distinguishes the active registry from four immutable
historical schemas and remains green.

Command:

```sh
uv run --project scripts/architecture python scripts/architecture/check_record_freshness.py
```

Output:

```text
records fresh: 21 ADRs, 10 RFCs, no stale claims
```

Command:

```sh
uv run pytest -q
```

Output:

```text
....................................                                     [100%]
36 passed in 0.19s
```

Command:

```sh
uv run --with pyrefly==1.1.1 pyrefly check
```

Output:

```text
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
```

### Final immutable-pin check

Command:

```sh
sha256sum \
  docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md \
  docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md
rg -n -A1 "ADR(10|21)_(SOURCE|MACHINE_BLOCK)_SHA256" \
  scripts/architecture/generate_contracts.py \
  scripts/architecture/validate_contracts.py
git diff --numstat -- \
  docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
```

Output:

```text
45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb  docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
1b6ca0051d3eb406b299f12b7d24a22b8d96990111bbca3fe922e6c17a5e45ee  docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md
ADR10_SOURCE_SHA256=45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb
ADR10_MACHINE_BLOCK_SHA256=de5ed30d02ffac788574b319ac9afcc4c1246212b0b015251ac055bd7ef17472
ADR21_SOURCE_SHA256=1b6ca0051d3eb406b299f12b7d24a22b8d96990111bbca3fe922e6c17a5e45ee
ADR21_MACHINE_BLOCK_SHA256=80e195ec795e8702bc4fccf13916ae039e04600af99956e4b46f4ca307d05567
```

`git diff --numstat` emitted no output for ADR-0010. Its bytes and both required
pins are unchanged.

## ASSUMED

- The owner acceptance in the task is authentic human authority. This agent
  cannot independently authenticate the human, but the task explicitly records
  the acceptance and directs promotion.
- The current dirty worktree contains earlier owner work that must be preserved.
  This promotion will not discard or rewrite unrelated changes.

## Remaining risk

- The worktree was already dirty and remains uncommitted. No commit or push was
  requested. The pins bind the final promoted ADR bytes present in this
  worktree.
- The current exact lineage is proven only for the named boundary/root and
  bound documents. A rebase, history replacement, bound-document mutation, or
  any other non-descendant lineage becomes `UNKNOWN_BLOCKING`; a later merge of
  the ADR-0010 source reactivates ADR-0010.
- Contract validation is `PASS` only for
  `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`. Runtime remains `NOT_ASSESSED`,
  and neither readiness tier is declared.
- No promotion blocker remains in the required command set.
