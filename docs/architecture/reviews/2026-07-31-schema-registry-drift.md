# Schema-registry inventory drift investigation

Investigation date: 2026-07-31  
Repository root: `/tmp/claude-1000/-home-soultransit-devtony-ranex/2731e1a6-a08e-4bf9-ab2f-e08867548087/scratchpad/schema-probe`

## Scope and evidence convention

This is an investigation of the current working tree. No repository file was
modified except this report. The repository was already dirty before the
investigation; in particular, both tooling programs and the generated registry
and validation report were already modified:

```text
$ pwd && git status --short
/tmp/claude-1000/-home-soultransit-devtony-ranex/2731e1a6-a08e-4bf9-ab2f-e08867548087/scratchpad/schema-probe
 M architecture/contracts/registry-manifest.json
 M architecture/contracts/schema-registry.json
 M docs/architecture/assessments/validation-report.json
 M scripts/architecture/generate_contracts.py
 M scripts/architecture/validate_contracts.py
... other pre-existing modified and untracked paths omitted here ...
```

All commands in this report were run from the repository root shown above
unless a command says otherwise. Line references address the current working
tree.

## 1. Defect reproduced

The supplied inventory comparison reproduces exactly: the registry has 153
entries, the filesystem has 157 `*.schema.json` documents, and the set
difference contains exactly four paths.

```text
$ python3 -c "import json,glob; d=json.load(open('architecture/contracts/schema-registry.json')); reg={e['path'] for e in d['entries']}; disk=set(glob.glob('schemas/**/*.schema.json',recursive=True)); print(len(d['entries']),len(disk)); print(sorted(disk-reg))"
153 157
['schemas/common/legacy-test-change-exception-v1.schema.json', 'schemas/common/legacy-test-cutover-removal-record-v1.schema.json', 'schemas/common/legacy-test-layout-policy-v1.schema.json', 'schemas/common/legacy-test-migration-record-v1.schema.json']
```

## 2. Why exactly these four are excluded

### 2.1 The registry inclusion rule

The generator does **not** inventory the `schemas/` directory. It builds an
in-memory `schemas` mapping, writes all non-immutable members, and then creates
one registry row for every key in that mapping:

> `scripts/architecture/generate_contracts.py:19827-19843`
>
> ```python
>     for relative, schema in schemas.items():
>         if "schemas/" + relative in ADR10_IMMUTABLE_V1_INPUT_PATHS:
>             continue
>         write_json(SCHEMAS / relative, schema)
>
>     entries = []
>     for relative in sorted(schemas):
>         entries.append(
>             {
>                 "schema_id": schemas[relative]["$id"],
>                 "path": f"schemas/{relative}",
>                 "digest": "sha256:" + sha256_file(SCHEMAS / relative),
>                 "draft": "2020-12",
>                 "status": "ACTIVE_DOCUMENTATION_CONTRACT",
>             }
>         )
>     write_json(CONTRACTS / "schema-registry.json", registry("REG-SCHEMAS-001", "1.0.0", entries, schema_count=len(entries)))
> ```

Therefore the exact inclusion rule is: a schema is registered if and only if
the generator placed its relative path in the in-memory `schemas` mapping.
Filesystem presence is not part of the rule. Every produced row is unconditionally
classified `ACTIVE_DOCUMENTATION_CONTRACT`.

The immutable v1 set contains five schemas, including the four in the defect:

> `scripts/architecture/generate_contracts.py:168-188`
>
> ```python
> ADR10_IMMUTABLE_V1_INPUT_PATHS = frozenset(
>     {
>         ...
>         "schemas/common/legacy-test-change-exception-v1.schema.json",
>         "schemas/common/legacy-test-cutover-removal-record-v1.schema.json",
>         "schemas/common/legacy-test-layout-policy-v1.schema.json",
>         "schemas/common/legacy-test-migration-record-v1.schema.json",
>         "schemas/execution/landing-record-v1.schema.json",
>     }
> )
> ```

The generator only loads an immutable schema into `schemas` when that path is
also reached through `ARTIFACT_SCHEMAS`:

> `scripts/architecture/generate_contracts.py:19691-19700`
>
> ```python
>     for template_name, (relative_schema, producer) in ARTIFACT_SCHEMAS.items():
>         if (
>             "schemas/" + relative_schema
>             in ADR10_IMMUTABLE_V1_INPUT_PATHS
>         ):
>             historical_schema_path = SCHEMAS / relative_schema
>             schemas[relative_schema] = load_json_strict(
>                 historical_schema_path
>             )
>             continue
> ```

Of those five immutable schemas, only the shared landing schema has an
`ARTIFACT_SCHEMAS` entry:

> `scripts/architecture/generate_contracts.py:300-319`
>
> ```python
> ARTIFACT_SCHEMAS: dict[str, tuple[str, str]] = {
>     ...
>     "LANDING_RECORD.yaml": ("execution/landing-record-v1.schema.json", "workspace"),
> ```

That explains the exact cardinality: landing v1 enters `schemas` and is
registered; the other four historical v1 schemas never enter `schemas` and are
not registered. The v2 versions are separately constructed and inserted:

> `scripts/architecture/generate_contracts.py:19637-19650,19667-19690`
>
> ```python
>         "change_exceptions": legacy_test_record_schema(
>             "change_exceptions",
>             "legacy-test-change-exception-v2.schema.json",
>             ...
>         "migration_proofs": legacy_test_record_schema(
>             "migration_proofs",
>             "legacy-test-migration-record-v2.schema.json",
>             ...
>         "cutover_removal_records": legacy_test_record_schema(
>             "cutover_removal_records",
>             "legacy-test-cutover-removal-record-v2.schema.json",
>             ...
>     schemas["common/legacy-test-layout-policy-v2.schema.json"] = (
>         legacy_policy_schema
>     )
>     schemas["common/legacy-test-change-exception-v2.schema.json"] = ...
>     schemas["common/legacy-test-migration-record-v2.schema.json"] = ...
>     schemas["common/legacy-test-cutover-removal-record-v2.schema.json"] = ...
> ```

### 2.2 Deliberate historical exclusion, accidental silent inventory gap

The four-file exclusion from the **active** registry is deliberate. ADR-0010
declares active consumers v2-only
(`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:481-490`),
individually classifies all four v1 schemas as `HISTORICAL_SCHEMA` and
`READ_ONLY_SUPERSEDED` with named v2 successors
(`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:531-540`),
and states that v2 registries consume only explicit v2 paths
(`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:541-548`):

> `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:529-540`
>
> ```yaml
> output_exclusion: "All nine paths are excluded from every generated-output writer/exact-output set and included in the immutable-input exact set. V2 schemas/projections/manifests use distinct paths and remain generator-owned outputs."
> ...
> - {path: "schemas/common/legacy-test-change-exception-v1.schema.json", ..., artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-change-exception-v2.schema.json"}
> - {path: "schemas/common/legacy-test-cutover-removal-record-v1.schema.json", ..., artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-cutover-removal-record-v2.schema.json"}
> - {path: "schemas/common/legacy-test-layout-policy-v1.schema.json", ..., artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-layout-policy-v2.schema.json"}
> - {path: "schemas/common/legacy-test-migration-record-v1.schema.json", ..., artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-migration-record-v2.schema.json"}
> ```

The committed registry history corroborates that intent. The v2 enactment
commit replaced the four v1 rows with the four v2 rows, rather than merely
dropping the v1 rows:

```text
$ git show 099ac438d -- architecture/contracts/schema-registry.json
- "path": "schemas/common/legacy-test-change-exception-v1.schema.json",
+ "path": "schemas/common/legacy-test-change-exception-v2.schema.json",
- "path": "schemas/common/legacy-test-cutover-removal-record-v1.schema.json",
+ "path": "schemas/common/legacy-test-cutover-removal-record-v2.schema.json",
- "path": "schemas/common/legacy-test-layout-policy-v1.schema.json",
+ "path": "schemas/common/legacy-test-layout-policy-v2.schema.json",
- "path": "schemas/common/legacy-test-migration-record-v1.schema.json",
+ "path": "schemas/common/legacy-test-migration-record-v2.schema.json",
```

Commit `099ac438d` describes that regeneration as “ADR-0010 v2 policy now
enacted”:

```text
$ git show -s --format=fuller 099ac438d
commit 099ac438d4350d744971b980046c70c225c89d8d
...
    chore: capture passing architecture contract validation

    Regenerated contract tree with ... ADR-0010 v2 policy now enacted.
```

What is accidental is the **silent inventory gap**: the active-registry
construction at `scripts/architecture/generate_contracts.py:19832-19843` never
compares its keys with the complete on-disk schema set, so its deliberate
historical exclusion is indistinguishable from any future accidental omission.
Section 4 establishes the corresponding validator gap.

## 3. Supersession and complete reference search

### 3.1 All four have v2 equivalents

The following command opened both versions, printed their `$id` values, and
looked up each v2 path in the current registry:

```text
$ python3 - <<'PY'
import json, pathlib
names = [
    'legacy-test-change-exception',
    'legacy-test-cutover-removal-record',
    'legacy-test-layout-policy',
    'legacy-test-migration-record',
]
reg=json.load(open('architecture/contracts/schema-registry.json'))
rows={e['path']:e for e in reg['entries']}
for stem in names:
    v1=pathlib.Path('schemas/common')/(stem+'-v1.schema.json')
    v2=pathlib.Path('schemas/common')/(stem+'-v2.schema.json')
    a=json.load(open(v1)); b=json.load(open(v2))
    p2=v2.as_posix()
    print(stem)
    print(' v1',v1.is_file(),a.get('$id'))
    print(' v2',v2.is_file(),b.get('$id'))
    print(' v2_registered',p2 in rows, rows.get(p2,{}).get('status'))
PY
legacy-test-change-exception
 v1 True https://schemas.ranex.dev/common/legacy-test-change-exception-v1.schema.json
 v2 True https://schemas.ranex.dev/common/legacy-test-change-exception-v2.schema.json
 v2_registered True ACTIVE_DOCUMENTATION_CONTRACT
legacy-test-cutover-removal-record
 v1 True https://schemas.ranex.dev/common/legacy-test-cutover-removal-record-v1.schema.json
 v2 True https://schemas.ranex.dev/common/legacy-test-cutover-removal-record-v2.schema.json
 v2_registered True ACTIVE_DOCUMENTATION_CONTRACT
legacy-test-layout-policy
 v1 True https://schemas.ranex.dev/common/legacy-test-layout-policy-v1.schema.json
 v2 True https://schemas.ranex.dev/common/legacy-test-layout-policy-v2.schema.json
 v2_registered True ACTIVE_DOCUMENTATION_CONTRACT
legacy-test-migration-record
 v1 True https://schemas.ranex.dev/common/legacy-test-migration-record-v1.schema.json
 v2 True https://schemas.ranex.dev/common/legacy-test-migration-record-v2.schema.json
 v2_registered True ACTIVE_DOCUMENTATION_CONTRACT
```

The supersession relation is normative, not inferred from filenames:
ADR-0010's breaking bindings explicitly map policy, change, migration, and
cutover v1 to v2 at
`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:498-510`,
and its historical rows repeat the four `superseded_by` mappings at
`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:536-539`.

They are not dead files. The accepted ADR requires their continued exact-byte
presence, and the validator enforces both the exact historical path set and
each digest:

> `scripts/architecture/validate_contracts.py:11267-11316,11327-11338`
>
> ```python
>     historical_rows = historical["rows"]
>     expected_historical_paths = {
>         ...
>         "schemas/common/legacy-test-change-exception-v1.schema.json",
>         "schemas/common/legacy-test-cutover-removal-record-v1.schema.json",
>         "schemas/common/legacy-test-layout-policy-v1.schema.json",
>         "schemas/common/legacy-test-migration-record-v1.schema.json",
>         ...
>     }
>     require(... {row["path"] for row in historical_rows}
>             == expected_historical_paths, "ADR10_HISTORICAL_MANIFEST", "")
>     ...
>     for row in historical_rows:
>         path = ROOT / row["path"]
>         require(
>             path.is_file()
>             and "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
>             == row["sha256"],
>             "ADR10_HISTORICAL_ARTIFACT_DIGEST",
>             row["path"],
>         )
> ```

### 3.2 Every literal reference found

This exhaustive literal-basename search included hidden and normally ignored
files, excluded only `.git/` and this report, and found the following
references:

```text
$ for name in legacy-test-change-exception-v1.schema.json legacy-test-cutover-removal-record-v1.schema.json legacy-test-layout-policy-v1.schema.json legacy-test-migration-record-v1.schema.json; do
    rg -n --hidden --no-ignore --fixed-strings -g '!.git/**' -g '!SCHEMA-DRIFT.md' "$name" .
  done
```

`legacy-test-change-exception-v1.schema.json`:

- `legal/licensing-manifest.json:3489`
- `architecture/contracts/generated-output-authority.json:2133`
- `scripts/architecture/validate_contracts.py:11274`
- `scripts/architecture/generate_contracts.py:176`
- `scripts/architecture/generate_contracts.py:4315`
- `schemas/common/legacy-test-change-exception-v1.schema.json:2` (its own `$id`)
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:501`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:536`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-C.md:1560`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:299`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:2432`

`legacy-test-cutover-removal-record-v1.schema.json`:

- `legal/licensing-manifest.json:3518`
- `architecture/contracts/generated-output-authority.json:2149`
- `scripts/architecture/validate_contracts.py:11277`
- `scripts/architecture/generate_contracts.py:180`
- `scripts/architecture/generate_contracts.py:4318`
- `schemas/common/legacy-test-cutover-removal-record-v1.schema.json:2` (its own `$id`)
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:510`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:537`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:301`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:2434`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-C.md:1558`

`legacy-test-layout-policy-v1.schema.json`:

- `legal/licensing-manifest.json:3547`
- `scripts/architecture/generate_contracts.py:182`
- `scripts/architecture/generate_contracts.py:4320`
- `scripts/architecture/validate_contracts.py:11279`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:303`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:2435`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-C.md:1545`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:498`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:538`
- `schemas/common/legacy-test-layout-policy-v1.schema.json:2` (its own `$id`)
- `architecture/contracts/generated-output-authority.json:2165`

`legacy-test-migration-record-v1.schema.json`:

- `legal/licensing-manifest.json:3576`
- `scripts/architecture/validate_contracts.py:11280`
- `scripts/architecture/generate_contracts.py:185`
- `scripts/architecture/generate_contracts.py:4321`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:502`
- `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:539`
- `schemas/common/legacy-test-migration-record-v1.schema.json:2` (its own `$id`)
- `architecture/contracts/generated-output-authority.json:2181`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-C.md:1552`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:305`
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:2437`

The generated-output authority rows are not claims that these are writable
outputs. They classify all four as `HISTORICAL_SCHEMA`,
`READ_ONLY_SUPERSEDED`, input class `ADR10_IMMUTABLE_V1_INPUT`, writer
`NONE_IMMUTABLE_COMMITTED_INPUT`, and bind each v2 successor at
`architecture/contracts/generated-output-authority.json:2124-2187`. The legal
manifest makes the same immutable-input classification and pins each digest at
`legal/licensing-manifest.json:3488-3591`.

There are **no schema-to-schema `$ref` consumers** of these four v1 files. Two
independent searches produced no output:

```text
$ rg -n --hidden '\\$ref.*legacy-test-(change-exception|cutover-removal-record|layout-policy|migration-record)-v1\\.schema\\.json' schemas -g '*.schema.json'
[no output]

$ python3 - <<'PY'
import json, pathlib
needles = (
    'legacy-test-change-exception-v1.schema.json',
    'legacy-test-cutover-removal-record-v1.schema.json',
    'legacy-test-layout-policy-v1.schema.json',
    'legacy-test-migration-record-v1.schema.json',
)
for path in sorted(pathlib.Path('schemas').rglob('*.schema.json')):
    value=json.load(open(path))
    stack=[value]
    while stack:
        item=stack.pop()
        if isinstance(item,dict):
            ref=item.get('$ref')
            if isinstance(ref,str) and any(n in ref for n in needles):
                print(f'{path}: $ref={ref}')
            stack.extend(item.values())
        elif isinstance(item,list):
            stack.extend(item)
PY
[no output]
```

Thus the references are historical-governance, immutable-byte verification,
licensing, self-identification, and archived review evidence—not active `$ref`
use. Their lack of active use is intentional; their retained presence is still
required.

## 4. Why validation counts 157 and still passes

`schema_documents` is a filesystem count. `validate_schema_documents()` recursively
discovers every on-disk `*.schema.json`, validates each document and `$id`, and
increments the counter once per discovered file:

> `scripts/architecture/validate_contracts.py:20355-20372`
>
> ```python
> def validate_schema_documents(checks: Counter[str]) -> dict[str, dict[str, Any]]:
>     schema_files = sorted(SCHEMAS.rglob("*.schema.json"))
>     require(len(schema_files) >= 46, "SCHEMA_DENOMINATOR", str(len(schema_files)))
>     schemas: dict[str, dict[str, Any]] = {}
>     ids: list[str] = []
>     for path in schema_files:
>         schema = load_json(path)
>         jsonschema.Draft202012Validator.check_schema(schema)
>         require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "SCHEMA_DRAFT", str(path))
>         require("$id" in schema, "SCHEMA_ID_MISSING", str(path))
>         ids.append(schema["$id"])
>         schemas[str(path.relative_to(ROOT))] = schema
>         checks["schema_documents"] += 1
>         ...
>     require(len(ids) == len(set(ids)), "SCHEMA_ID_DUPLICATE", "duplicate $id")
>     return schemas
> ```

The only denominator check is `len(schema_files) >= 46`; 157 satisfies it.
There is no equality check against `schema-registry.json`.

The current saved report confirms both the filesystem count and `PASS`:

> `docs/architecture/assessments/validation-report.json:145,225,228`
>
> ```json
> "schema_documents": 157,
> "schema_registry_digest": "sha256:093be0f1d9b0007d9efa42148d029ce7d77130c65c49a0790abde1fd75ca831c",
> "status": "PASS"
> ```

The report's registry digest and the registry manifest's digest both match the
current 153-entry file exactly:

```text
$ python3 - <<'PY'
import json, hashlib
p='architecture/contracts/schema-registry.json'
b=open(p,'rb').read(); actual='sha256:'+hashlib.sha256(b).hexdigest()
r=json.load(open('docs/architecture/assessments/validation-report.json'))
m=json.load(open('architecture/contracts/registry-manifest.json'))
row=next(e for e in m['entries'] if e['path']==p)
print('actual',actual)
print('report',r['schema_registry_digest'],actual==r['schema_registry_digest'])
print('manifest',row['digest'],actual==row['digest'])
print('report_status',r['status'],'schema_documents',r['checks']['schema_documents'])
PY
actual sha256:093be0f1d9b0007d9efa42148d029ce7d77130c65c49a0790abde1fd75ca831c
report sha256:093be0f1d9b0007d9efa42148d029ce7d77130c65c49a0790abde1fd75ca831c True
manifest sha256:093be0f1d9b0007d9efa42148d029ce7d77130c65c49a0790abde1fd75ca831c True
report_status PASS schema_documents 157
```

The report also binds the current generator, validator, lock, and concurrency
script bytes; all four comparisons are true:

```text
$ python3 - <<'PY'
import hashlib,json
r=json.load(open('docs/architecture/assessments/validation-report.json'))
for key,pathkey in [('generator_digest','generator_path'),('validator_digest','validator_path'),('contract_tree_lock_digest','contract_tree_lock_path'),('concurrency_regression_digest','concurrency_regression_path')]:
    p=r[pathkey]
    actual='sha256:'+hashlib.sha256(open(p,'rb').read()).hexdigest()
    print(key,actual==r[key],actual,r[key])
PY
generator_digest True sha256:144c6b7c87c6e7d0a568e2db486fa95afe04e644d349a9553af9d091d6fa4830 sha256:144c6b7c87c6e7d0a568e2db486fa95afe04e644d349a9553af9d091d6fa4830
validator_digest True sha256:660c02af79407273e72b57331bac6bf623c0b2055a9f95e793a5b7437b2cdb8e sha256:660c02af79407273e72b57331bac6bf623c0b2055a9f95e793a5b7437b2cdb8e
contract_tree_lock_digest True sha256:b91c53a1d51772ec4afcab5fd4d0f6cf7da002a0225bb2ca806d484b97618f92 sha256:b91c53a1d51772ec4afcab5fd4d0f6cf7da002a0225bb2ca806d484b97618f92
concurrency_regression_digest True sha256:29e984ef874d9eba7cc30d32e450c5ad111d5c0d0718b6bd8c9704b1e91703e5 sha256:29e984ef874d9eba7cc30d32e450c5ad111d5c0d0718b6bd8c9704b1e91703e5
```

The validator was not rerun in the repository root because its success path
writes `docs/architecture/assessments/validation-report.json` at
`scripts/architecture/validate_contracts.py:31851-31855`, which would violate
this investigation's no-modification constraint. The saved `PASS` claim above
is therefore reported as saved, digest-bound evidence—not as a newly executed
validation.

That digest validation cannot detect semantic incompleteness: it proves only
that the incomplete registry is the exact file the report and manifest pinned.
`validate_registry_manifest()` checks the set and digests of top-level
`architecture/contracts/*.json` files, not the entries inside the schema
registry:

> `scripts/architecture/validate_contracts.py:21388-21402`
>
> ```python
>     expected_files = sorted(
>         str(path.relative_to(ROOT))
>         for path in CONTRACTS.glob("*.json")
>         if path.name != "registry-manifest.json"
>     )
>     require(paths == expected_files, "MANIFEST_INCOMPLETE", ...)
>     for entry in manifest["entries"]:
>         require(file_digest(ROOT / entry["path"]) == entry["digest"],
>                 "MANIFEST_DIGEST_MISMATCH", entry["path"])
> ```

An exact search shows that `validate_contracts.py` never loads or inspects
`schema-registry.json`; its sole literal reference is the report digest:

```text
$ rg -n "schema-registry\\.json|schema_registry" scripts/architecture/validate_contracts.py
31844:        "schema_registry_digest": file_digest(CONTRACTS / "schema-registry.json"),
```

The call sequence validates all filesystem schemas first, validates the
top-level registry manifest later, and never reconciles those two sets:

> `scripts/architecture/validate_contracts.py:31780-31790`
>
> ```python
> schemas = validate_schema_documents(checks)
> ...
> validate_registry_manifest(checks)
> tuples, domains = validate_registries(schemas, checks)
> ...
> ```

This is why 157 valid schema documents and a 153-entry registry can produce a
passing report.

## 5. Remedy analysis

The current data already forms a closed two-class inventory: 153 active
registry paths plus exactly four historical-schema exceptions equals all 157
disk schemas, with no overlap or remainder.

```text
$ python3 - <<'PY'
import glob,json
reg=json.load(open('architecture/contracts/schema-registry.json'))
a={e['path'] for e in reg['entries']}
auth=json.load(open('architecture/contracts/generated-output-authority.json'))
h={
    e['path'] for e in auth['immutable_inputs']
    if e['artifact_class']=='HISTORICAL_SCHEMA'
    and e['disposition']=='READ_ONLY_SUPERSEDED'
}
d=set(glob.glob('schemas/**/*.schema.json',recursive=True))
print('active',len(a),'historical_exception',len(h),'disk',len(d))
print('overlap',sorted(a&h))
print('disk_minus_union',sorted(d-(a|h)))
print('union_minus_disk',sorted((a|h)-d))
print('historical_exception',sorted(h))
PY
active 153 historical_exception 4 disk 157
overlap []
disk_minus_union []
union_minus_disk []
historical_exception ['schemas/common/legacy-test-change-exception-v1.schema.json', 'schemas/common/legacy-test-cutover-removal-record-v1.schema.json', 'schemas/common/legacy-test-layout-policy-v1.schema.json', 'schemas/common/legacy-test-migration-record-v1.schema.json']
```

The missing control is an assertion that this partition remains exact.

### 5.1 Remedy (a): register the four

To do this without falsely reactivating v1, the schema registry would have to
become a complete inventory with at least two entry dispositions. Simply adding
the four to the existing `schemas` mapping is wrong because the generator gives
every row `status: "ACTIVE_DOCUMENTATION_CONTRACT"` at
`scripts/architecture/generate_contracts.py:19832-19841`, while ADR-0010 gives
the four `READ_ONLY_SUPERSEDED` status at
`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:536-539`.

Exact required source changes:

1. `scripts/architecture/generate_contracts.py`
   - Load the four immutable schema documents into the registry inventory
     without calling `write_json()` on them. `write_json()` deliberately rejects
     immutable paths at
     `scripts/architecture/generate_contracts.py:941-949`.
   - Emit their existing `$id` and digest but use an explicit historical status,
     while leaving the 153 current entries active.
   - Set `schema_count` from the complete 157-entry inventory.
2. `scripts/architecture/validate_contracts.py`
   - Load and validate `schema-registry.json`.
   - Require `schema_count == len(entries)`, unique paths and IDs, exact path-set
     equality with the 157 filesystem schemas, and per-row equality of `$id`,
     digest, draft, and status.
   - Require the only non-active rows to equal the ADR-0010 historical-schema
     set. This general equality check is essential: adding today's four rows
     alone would still allow a fifth unregistered file to pass.

Required generated content changes:

- `architecture/contracts/schema-registry.json`: four historical rows added;
  `schema_count` changes 153 → 157.
- `architecture/contracts/registry-manifest.json`: its
  `schema-registry.json` digest row changes. The generator derives every
  top-level contract digest at
  `scripts/architecture/generate_contracts.py:22554-22562`.
- `docs/architecture/assessments/validation-report.json`: regenerated by the
  validator. Its `generator_digest`, `validator_digest`,
  `schema_registry_digest`, and `registry_manifest_digest` all change, and the
  new registry-check counter(s) appear. Those four bindings are emitted at
  `scripts/architecture/validate_contracts.py:31827-31849`.

No v1 schema bytes or their ADR-0010 digest pins may move: they are immutable
inputs (`scripts/architecture/generate_contracts.py:22714-22748`) and the
generator compares their bytes before and after publication
(`scripts/architecture/generate_contracts.py:22798-22805,22884-22890`).
`architecture/contracts/generated-output-authority.json` has no content reason
to change because the writer/path partition is unchanged; its construction is
path-based at `scripts/architecture/generate_contracts.py:22455-22549`. The
assessment generator computes a schema registry digest at
`scripts/architecture/generate_contracts.py:22194-22198`, but a
whole-repository search finds no read
of `registry_digests["schema-registry.json"]`; therefore no control assessment
or domain projection is bound to that digest.

```text
$ rg -n 'registry_digests\\[\"schema-registry.json\"\\]' scripts/architecture/generate_contracts.py
22197:    registry_digests["schema-registry.json"] = "sha256:" + sha256_file(CONTRACTS / "schema-registry.json")
```

Registry versioning requirement: **UNCHECKED**. The repository contains no rule
for when `REG-SCHEMAS-001`'s logical version must change. The generator
hard-codes `1.0.0` at
`scripts/architecture/generate_contracts.py:19843`, and committed registry
history has changed its entry set while keeping that value:

```text
$ for c in 032adf3687 099ac438d HEAD; do git show "$c":architecture/contracts/schema-registry.json | python3 -c "import json,sys; d=json.load(sys.stdin); print('$c',d['version'],len(d['entries']))"; done
032adf3687 1.0.0 113
099ac438d 1.0.0 152
HEAD 1.0.0 153
```

ADR-0015 requires
workflow runs to pin schema-registry versions/digests
(`docs/architecture/decisions/ADR-0015-canonical-workflow-and-event-schema-and-upcaster-policy.md:43-56,106-107`),
so inventing a version-bump rule here would be unsafe.

What could break:

- Any consumer that treats every registry entry as active could admit four
  forbidden v1 contracts unless it is changed to filter the new historical
  status. All 153 current rows have the same active status:

  ```text
  $ python3 - <<'PY'
  import json, collections
  r=json.load(open('architecture/contracts/schema-registry.json'))
  print('statuses',collections.Counter(e['status'] for e in r['entries']))
  PY
  statuses Counter({'ACTIVE_DOCUMENTATION_CONTRACT': 153})
  ```

- No in-repository executable consumer was found: the exhaustive
  `schema-registry.json` reference search found the generator, validator's
  digest binding, manifests, documentation, and archived reports, but no
  runtime loader. External consumers are **UNCHECKED**.
- Any exact expected count of 153 outside the repository is **UNCHECKED**.

This remedy can be made fail-closed, but it expands the meaning of the active
registry and creates avoidable consumer ambiguity.

### 5.2 Remedy (b): delete the four as obsolete

This is not a valid remedy under the accepted architecture. The files are
superseded for active use but explicitly retained, not obsolete for deletion:

> `docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:526-530,541-548`
>
> ```yaml
> canonical_writer: "NONE_IMMUTABLE_COMMITTED_INPUT"
> generator_role: "VERIFY_ONLY_NO_CREATE_UPDATE_DELETE_REFORMAT"
> ...
> change_rule: "No tool or human may modify these paths under contract 2.0. A change requires a new major contract and new path while retaining these exact bytes."
> ...
> historical_schema_policy: "Only the exact historical_artifact_authority set is retained; it remains byte-bound ... and cannot be overwritten, deleted, silently regenerated, or interpreted as policy2."
> ```

Deleting any one today fails both tools before an inventory remedy matters.
The generator rejects a missing historical input at
`scripts/architecture/generate_contracts.py:22722-22747`; the validator rejects
the missing file/digest at
`scripts/architecture/validate_contracts.py:11327-11338`.

Making deletion lawful would require evidence that invalidates ADR-0010 and a
new accepted major/superseding architectural decision; silently rewriting the
accepted ADR would violate the repository's evidence rule. Until such an
authority exists, the exact new ADR path and its full generated decision
registry cascade are **UNCHECKED**.

At minimum, that separately authorized change would have to:

- delete the four v1 schema files;
- remove their four rows from `legal/licensing-manifest.json`
  (`legal/licensing-manifest.json:3488-3591`);
- add a new accepted contract that explicitly supersedes ADR-0010's historical
  set/count and retention rule; ADR-0010 itself and its existing digest pins
  remain historical evidence;
- add and verify the new contract's source/machine-block digest pins in both
  tools, and change their historical-authority resolution to use the
  superseding contract. The exact constant names and source path are
  **UNCHECKED** until that decision exists;
- remove the four paths from `ADR10_IMMUTABLE_V1_INPUT_PATHS` and from both
  tools' expected historical sets
  (`scripts/architecture/generate_contracts.py:168-188,4310-4323`;
  `scripts/architecture/validate_contracts.py:11267-11302`);
- regenerate `architecture/contracts/generated-output-authority.json`, whose
  immutable-input list/count would fall from 9 to 5
  (`scripts/architecture/generate_contracts.py:22469-22549`);
- regenerate
  `docs/architecture/assessments/completeness-report.json` and
  `COMPLETENESS_REPORT.md`, because `common_schemas` is a live glob count at
  `scripts/architecture/generate_contracts.py:22217-22223` and would fall from
  the current 42
  (`docs/architecture/assessments/completeness-report.json:14`) to 38;
- regenerate `architecture/contracts/registry-manifest.json`, because the
  generated-output-authority digest would change; and
- rerun validation, changing `schema_documents` 157 → 153 plus
  `generator_digest`, `validator_digest`, `registry_manifest_digest`, and the
  validation report itself. The `schema_registry_digest` need not change if its
  153 active rows remain byte-identical.

The legal-manifest edit also changes
`generated-output-authority.json`'s `licensing_policy_source_digest`, derived at
`scripts/architecture/generate_contracts.py:22526-22529`.

What could break is not hypothetical: generation and validation fail
immediately under current authority. It also destroys the exact bytes that
ADR-0010 requires for historical compatibility verification. This remedy
solves the numeric mismatch by discarding governed evidence and is rejected.

### 5.3 Remedy (c): enforce an explicit historical exception

This matches the current contract model: keep 153 active rows, keep four
separately governed immutable historical schemas, and make their union equal
the complete disk inventory.

Exact required source change:

- `scripts/architecture/validate_contracts.py`: add a schema-registry
  validation function and call it with the `schemas` mapping returned by
  `validate_schema_documents()`. It must:
  1. load `architecture/contracts/schema-registry.json`;
  2. validate registry identity/shape, declared count, row shape, ordering,
     unique paths, and unique IDs;
  3. validate every active row's path, `$id`, SHA-256, draft, and
     `ACTIVE_DOCUMENTATION_CONTRACT` status against the opened schema;
  4. derive the exception set from ADR-0010
     `historical_artifact_authority.rows` where
     `artifact_class == HISTORICAL_SCHEMA` and
     `disposition == READ_ONLY_SUPERSEDED`, rather than trusting an ad hoc
     filename list;
  5. require active paths and exception paths to be disjoint; and
  6. require
     `active_registry_paths | historical_exception_paths == set(schemas)`.

Those last two equalities make future silent drift impossible. A new disk
schema absent from both sources fails; a missing registered schema fails; an
extra registry row fails; and enlarging the exception requires changing the
digest-pinned accepted ADR contract, which both tools independently verify at
`scripts/architecture/generate_contracts.py:3675-3694` and
`scripts/architecture/validate_contracts.py:10981-11003`.

Required generated content change:

- `docs/architecture/assessments/validation-report.json` only. The validator
  writes it at `scripts/architecture/validate_contracts.py:31851-31855`; its
  `validator_digest` and newly recorded schema-registry check counter(s) change.

The following remain byte-identical under this remedy:

- all 157 schemas;
- `architecture/contracts/schema-registry.json` and its 153 count;
- `architecture/contracts/registry-manifest.json`;
- `architecture/contracts/generated-output-authority.json`;
- the ADR-0010 and legal-manifest pins; and
- `generator_digest`, `schema_registry_digest`, and
  `registry_manifest_digest` in the regenerated report. Only
  `validator_digest` and checks move because only the validator source changes.

What could break:

- Any currently hidden fifth mismatch would now fail. The measured partition
  above proves there is none in this working tree.
- A future legitimate historical schema cannot be added casually; the
  validator will block until its governing accepted contract classifies it.
  That is the intended fail-closed behavior.
- Existing active registry consumers see no data or status change.

No check is weakened: this adds exact-set, identity, and digest checks that do
not exist today.

## 6. Recommendation

Choose **(c): keep the four schemas as explicitly governed historical
exceptions and add an exact, fail-closed validator reconciliation**.

The deciding evidence is:

1. Deletion is prohibited. ADR-0010 names each file, pins each digest, requires
   exact-byte retention, and the existing validator enforces it
   (`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:526-548`;
   `scripts/architecture/validate_contracts.py:11267-11338`).
2. Active registration is the wrong semantic class. All current schema-registry
   rows are active, while these four are normatively
   `READ_ONLY_SUPERSEDED`; the v2 replacements are already present and active
   (`docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md:498-510,536-539`;
   `scripts/architecture/generate_contracts.py:19832-19841`).
3. The repository already has the required two complete inventories. The
   measured equality is:

   ```text
   active registry (153) ∪ historical exception (4) = disk schemas (157)
   active registry ∩ historical exception = ∅
   ```

4. Remedy (c) preserves every existing schema and registry byte while closing
   the actual control gap. Remedy (a) changes registry semantics and may expose
   v1 to active-only consumers; remedy (b) contradicts accepted architecture.

The implemented check should fail with stable diagnostics for at least these
four distinct defects:

- disk path in neither active registry nor governed historical set;
- active registry path absent from disk;
- path present in both active and historical sets; and
- registry row whose `$id`, digest, draft, status, count, uniqueness, or order
  does not match the opened files.

The post-fix acceptance evidence should include:

```text
# repository root
uv run --project scripts/architecture \
  python scripts/architecture/generate_contracts.py
uv run --project scripts/architecture \
  python scripts/architecture/validate_contracts.py
```

and a disposable-copy negative test that adds one otherwise-valid
`schemas/**/*.schema.json` file without a registry or historical-authority row
and proves the validator exits nonzero with the new unclassified-schema
diagnostic. A second negative case should remove one active registry row in the
disposable copy and prove the same exact-set check fails. These tests add
strictness; they do not relax or replace any existing check.

After (c), the four-file difference is no longer silent drift: it is a
machine-enforced, exact exception set. Any fifth unregistered schema necessarily
falls outside both sides of the allowed partition and fails validation.

## 7. Implementation

Implementation date: 2026-07-31  
Repository root: `/home/soultransit/devtony/ranex`

### 7.1 CONFIRMED

Before editing, the decided remedy's key claims were checked again in this
working tree:

- ADR-0010 lines 526-548 classify the four v1 schemas as
  `HISTORICAL_SCHEMA` / `READ_ONLY_SUPERSEDED`, pin each SHA-256 digest, forbid
  modification or deletion, and require exact-byte retention.
- The existing validator at its then-current lines 11267-11338 required the
  exact nine-row ADR-0010 historical manifest and verified every retained
  artifact digest.
- All 153 rows in `schema-registry.json` had status
  `ACTIVE_DOCUMENTATION_CONTRACT`. The four v2 replacements were present in
  that active registry.
- The independently measured partition was still exact: 153 active paths,
  four ADR-governed historical schema paths, 157 disk schemas, no overlap, and
  no remainder.

The implementation is confined to
`scripts/architecture/validate_contracts.py`:

- `historical_schema_exception_paths()` at lines 20368-20379 derives the
  exception only from the digest-bound ADR-0010 machine contract, filtering on
  `HISTORICAL_SCHEMA` and `READ_ONLY_SUPERSEDED`. The validator contains no new
  four-path allowlist.
- `validate_schema_registry_inventory()` at lines 20382-20536 verifies the
  registry identity and exact shape, declared count, row shape, normalized and
  bytewise-sorted unique paths, unique schema IDs, each active row's `$id`,
  digest, draft, and active status, disjoint active/historical sets, and exact
  union equality with the disk inventory.
- `validate_contract_tree()` calls the reconciliation immediately after
  opening and validating all disk schemas, at lines 31956-31957.
- The new counters are `schema_registry_entries`,
  `schema_registry_historical_exceptions`, and `schema_inventory_paths`.

A targeted positive execution from the repository root produced:

```text
{'schema_documents': 157, 'schema_registry_entries': 153, 'schema_registry_historical_exceptions': 4, 'schema_inventory_paths': 157}
```

The required throwaway-file experiment temporarily added
`schemas/common/zzz-probe-v1.schema.json`, ran only schema validation and the
new reconciliation, and then deleted the probe. Real output:

```text
{"error": "SCHEMA_REGISTRY_UNCLASSIFIED_DISK_PATH:schemas/common/zzz-probe-v1.schema.json", "status": "FAIL"}
exit_code=1
```

The required historical-exception experiment derived the live exception set
from ADR-0010, removed its first entry in memory, ran the reconciliation, and
then exited; the repository therefore needed no restoration write. Real
output:

```text
removed_exception=schemas/common/legacy-test-change-exception-v1.schema.json
{"error": "SCHEMA_REGISTRY_UNCLASSIFIED_DISK_PATH:schemas/common/legacy-test-change-exception-v1.schema.json", "status": "FAIL"}
exit_code=1
```

Additional in-memory targeted executions confirmed the other exact-set
branches:

```text
missing_registered_schema:FAIL:SCHEMA_REGISTRY_ACTIVE_PATH_MISSING:schemas/architecture/proposal-v1.schema.json
extra_registry_row:FAIL:SCHEMA_REGISTRY_ACTIVE_PATH_MISSING:schemas/zzzz-extra-row-v1.schema.json
active_historical_overlap:FAIL:SCHEMA_REGISTRY_ACTIVE_HISTORICAL_OVERLAP:schemas/architecture/proposal-v1.schema.json
```

All commands below were executed from
`/home/soultransit/devtony/ranex`.

```text
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
{"assessments": 41, "projections": 10, "registries": 46, "schemas": 157}
```

```text
$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
status: FAIL
error: LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/__init__.py
schema_documents: 157
schema_registry_entries: 153
schema_registry_historical_exceptions: 4
schema_inventory_paths: 157
```

The validation values above are selected fields decoded from the command's
single JSON output line. The command reached and passed the new reconciliation;
it then failed at the separately owner-gated migration-proof check exactly as
expected. No attempt was made to repair or bypass that check.

```text
$ uv run pytest -q
....................................                                     [100%]
36 passed in 0.18s
```

```text
$ git diff --stat
 README.md                                          |   2 +-
 .../contracts/hermes-research-promotions.json      |  60 +++--
 architecture/contracts/registry-manifest.json      |   4 +-
 architecture/contracts/schema-registry.json        |   2 +-
 docs/HANDOFF.md                                    | 138 +++++++++--
 docs/README.md                                     |  46 +++-
 docs/architecture/README.md                        |  18 +-
 .../assessments/validation-report.json             |   8 +-
 docs/architecture/rfcs/README.md                   |   3 +-
 ...009-record-freshness-as-a-shipped-capability.md |  17 +-
 .../hermes-research-provision-v1.schema.json       |  45 +++-
 scripts/architecture/generate_contracts.py         | 120 ++++++++-
 scripts/architecture/pyproject.toml                |  15 +-
 scripts/architecture/validate_contracts.py         | 267 +++++++++++++++++++--
 14 files changed, 663 insertions(+), 82 deletions(-)
```

That stat is against `HEAD` and includes the substantial pre-existing dirty
worktree recorded before this implementation. In particular, the registry,
manifest, one schema, generator, validator, and saved validation report were
already modified. It must not be interpreted as this fix changing all listed
files.

Byte identity was instead checked against a pre-edit snapshot of this working
tree and again after generation and both probes. The sorted list of all 157
schema paths and per-file SHA-256 digests had the same aggregate digest before
and after:

```text
sha256:4680dc9ccddfdbc227a491e341713c1298ac72742f644c6b5d4c6688273d1a61
```

The other protected whole-file digests also matched the pre-edit baseline:

```text
architecture/contracts/schema-registry.json
sha256:093be0f1d9b0007d9efa42148d029ce7d77130c65c49a0790abde1fd75ca831c
architecture/contracts/registry-manifest.json
sha256:90994c9f644657162837b7dd3d818e7da43ec7726b653aafc3ea706e835c6223
architecture/contracts/generated-output-authority.json
sha256:ed05095c5859f1955f4eb91189c6d69b6381a1faa07134d3097ff2e0854332aa
docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
sha256:45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb
legal/licensing-manifest.json
sha256:013f89c72c71c4d939edaf73bd6228073f87d25105325ab1ffa1275cc5b1fc29
```

Thus all 157 schema bytes, both registry files, generated-output authority,
ADR-0010 and every digest pin within it, and the legal manifest and every pin
within it remained byte-identical to the working-tree baseline. The temporary
probe path is absent. `git diff --check` also completed with no output and exit
code 0.

Because full validation failed before its success-only write, the generated
`validation-report.json` was not updated with this validator's digest or the
three new counters. Its saved `PASS` report still carries validator digest
`sha256:660c02af79407273e72b57331bac6bf623c0b2055a9f95e793a5b7437b2cdb8e`;
the implemented validator digest is
`sha256:e8e0ba2a6c0de80b818eb6fa2472833024f4bd6c5ef271fa44cd59ff71b62765`.
The generated report was not hand-edited.

### 7.2 ASSUMED

- The dirty worktree present before this task is user-owned and must be
  preserved. Therefore “byte-identical” above means identical to the measured
  pre-edit working-tree bytes, not identical to `HEAD`.
- External consumers of `schema-registry.json` were not executed. Their input
  bytes and the registry's active-only semantics did not change.

No assumption was used to classify a schema or admit an exception; production
validation derives both inventories from repository evidence.

### 7.3 Remaining risk

Repository-wide contract validation remains failed because
`tests/__init__.py` lacks the separately owner-gated legacy-test migration
proof. Until that issue is authorized and resolved, a successful validator run
cannot regenerate `validation-report.json`, so the saved `PASS` report remains
stale and does not record the new validator digest or counters. The targeted
positive and negative executions demonstrate this reconciliation independently
of that later blocker, but they do not discharge it.
