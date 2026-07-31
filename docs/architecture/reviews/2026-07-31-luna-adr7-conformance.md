# LUNA ADR-0007 conformance report

Date: 2026-07-31  
Working directory: `/home/soultransit/devtony/ranex`  
Outcome: **STOPPED — conformance was not claimed and product code was not changed.**

## Executive result

The current product tree is not conformant with ADR-0007. Twelve of the 18
`ORG-*` rules fail the static rule-by-rule audit. Six pass for the current
scope; two of those six are not exercised because the slice has no product
migrations or module-discovery mechanism.

The validator does not reach its production-topology scan. Its exact current
first failure is:

```text
LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/acp/__init__.py
```

The failure is enforced at
`scripts/architecture/validate_contracts.py:19990-20000`. ADR-0010 says the
2,444 inherited tests cannot be deleted, moved, or relabelled merely to make a
topology check green (`ADR-0010:20-23`), and a move requires complete migration
proof (`ADR-0010:37-38`). The generated policy contains 2,444 baseline rows,
zero migration proofs, and zero cutover-removal records. Creating fictional
proofs, hiding `tests/`, changing the validator, or restoring the inherited
tree only for validation would be a bypass, so none was done.

There is a second independent blocker. ADR-0007 requires every enacted context
to contain `README.md` and a generated/validated `contract.yaml`
(`ADR-0007:70-85`; `topology-rules.json:256-260`). The enacted `assurance`,
`governed_execution`, and `policy` contexts contain neither. A repository-wide
search found no context-contract projection writer in the generator; its only
`contract.yaml` occurrence is the required-metadata declaration at
`generate_contracts.py:18726`. Hand-authoring these projections would
contradict ADR-0007:84-85.

## Files changed and why

- `LUNA-ADR7-REPORT.md` — added this requested evidence report.

No product, test, governance-source, generator, validator, generated contract,
schema, or assessment file was edited. The required generator ran successfully;
SHA-256 inventories taken immediately before and after it were identical, so it
changed zero generated files.

The worktree was already dirty before this task. Those existing changes were
preserved. `pytest` created an ignored root test cache during execution; it was
moved to `/tmp/luna-adr7-tests-init.cpython-314.pyc`, and the now-empty cache
directory was removed.

## Rule-by-rule result

No row is presented as an executable topology-validator pass: ADR-0010 stops
the validator inside `validate_production_test_layout()` before the source scan
at `validate_contracts.py:20269`.

| Rule | Result | Evidence |
|---|---|---|
| `ORG-PATH-001` | **FAIL** | `src/ranex/cli/` is an unregistered top-level product package. The registry contains `delivery` and declares CLI as its public boundary at `contexts.json:913-924`; it contains no `cli` context. The path audit found no owner entry for `src/ranex/cli/**`. |
| `ORG-CONTEXT-001` | **FAIL** | `assurance`, `governed_execution`, and `policy` have no `README.md` or `contract.yaml`. `governed_execution` also has no required `api/` package. Required metadata is at `topology-rules.json:256-260`; context records are at `contexts.json:481-527`. |
| `ORG-LAYER-001` | **FAIL** | `policy/adapters/configuration/yaml/slice_gate_loader.py:20` imports another context's private domain. `cli/main.py:19-29` reaches private adapter/domain packages from an unregistered horizontal package. Empty optional layer packages also exist, contrary to `topology-rules.json:262-266`. |
| `ORG-PUBLIC-001` | **FAIL** | Cross-context imports target `ranex.governed_execution.domain...` and `ranex.governed_execution.adapters...`, not the target context's `api` package (`slice_gate_loader.py:20`; `cli/main.py:19-29`). ADR-0007's exact rule is at `ADR-0007:139-140`. |
| `ORG-DEPENDENCY-001` | **FAIL** | The executed import audit found `policy -> governed_execution`; the executed registry query returned `declared_policy_to_governed_execution=False`. |
| `ORG-CYCLE-001` | **PASS (static scope)** | The executed graph query topologically sorted all 34 declared nodes (`34/34`) and the actual registered source edge set is acyclic. This does not cure the unregistered packages or undeclared edge. |
| `ORG-IMPORT-001` | **FAIL** | Importing `slice_gate_loader.py` performs YAML constructor registration at lines 39-41. ADR-0007 forbids import-time registration at lines 145-146. |
| `ORG-COMPOSE-001` | **FAIL** | `bootstrap/composition.py` exists, but `cli/main.py:68-86` independently selects the YAML loader, evaluator, and concrete SQLite `Journal`, then writes through it. |
| `ORG-MESSAGE-001` | **FAIL** | Code belonging to the delivery boundary directly calls private evaluation code and directly instantiates another owner's persistence adapter (`cli/main.py:72-86`) instead of using a public API. |
| `ORG-PERSIST-001` | **FAIL** | The `evaluations` table is declared in `governed_execution/adapters/.../journal.py:19-35`, while `contexts.json:524-525` assigns GateEvaluation and sole gate-evaluation persistence ownership to `assurance`. |
| `ORG-TEST-MIRROR-001` | **FAIL** | Unit tests are at `tests/unit/test_gate_verdict.py`, not `tests/unit/<context>/domain/**` or `application/**`; contract and integration tests likewise omit their context owner. `tests/confinement/` is not one of the 18 registered roots. `tests/__init__.py` is a forbidden new direct-top-level test under ADR-0010:31-42. |
| `ORG-GENERATED-001` | **PASS for existing generated tree** | The generator exited 0 and before/after SHA-256 inventories were identical. The validator completed schema/registry/generated-output checks before failing in the later test-layout phase. Missing context projections remain an `ORG-CONTEXT-001` blocker. |
| `ORG-MIGRATION-001` | **PASS / not exercised** | The product tree contains no context-owned migration directories or `src/ranex/migration` implementation. |
| `ORG-LEGACY-001` | **PASS (static scope)** | The executed source search found no `legacy` or `hermes` import in `src/ranex`. |
| `ORG-OWNERSHIP-001` | **FAIL** | The executed path-registry resolution found no ownership row for `src/ranex/__init__.py`, any `src/ranex/cli/*.py`, or any `src/ranex/foundation/*.py`. |
| `ORG-DISCOVERY-001` | **PASS / not exercised** | This slice has no module/adapter discovery mechanism. Source packages use explicit `__init__.py` files below `src/ranex`; no tests/docs/tools/legacy package is imported as product code. Import-time YAML registration fails `ORG-IMPORT-001` but is not package discovery. |
| `ORG-NAV-001` | **FAIL** | The executed search found zero context `README.md` files, so the required owner, vocabulary, API, invariant, data, dependency, operations, and test navigation is absent. |
| `ORG-EXEMPTION-001` | **PASS** | Executed JSON inspection returned `topology_exceptions=0`; no exemption was added or relied upon. |

Summary: **6 pass/pass-not-exercised; 12 fail.**

## Confirmed findings

1. The bootstrap authorization is `ACTIVE` and covers only this first walking
   skeleton. ADR-0007 is explicitly listed as governing the slice.
2. The exact initial validator result was exit 1 with
   `LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/acp/__init__.py`.
3. `contexts.json` registers 34 contexts. It does not register `cli`; it does
   register `delivery` and names CLI as a delivery boundary.
4. The enacted context roots are `assurance`, `governed_execution`, and
   `policy`; none has `README.md` or `contract.yaml`.
5. The legacy-test policy binds 2,444 baseline files, zero migration proofs,
   and zero cutover-removal records.
6. The declared 34-node context graph is acyclic, but the actual
   `policy -> governed_execution` edge is not declared.
7. Existing behavior remains green: 36 tests passed and strict pyrefly reported
   0 errors.
8. Generated output was idempotent in this run: the before/after SHA-256 diff
   was empty.
9. The implemented source scan does not enforce all 18 rules. At
   `validate_contracts.py:20300`, an unknown top-level package becomes
   `current_context=None`; private cross-context checks then do not apply. The
   scan also does not check required metadata, navigation, ownership resolution,
   import effects, or test mirroring.

## Assumptions and inferences

No assumption was used to edit product or governance code.

- **Inference:** `src/ranex/cli` belongs to `delivery`, based on the registry's
  delivery boundary (`contexts.json:920-924`). No move was performed.
- **Inference:** `ORG-MIGRATION-001` and `ORG-DISCOVERY-001` pass only by
  non-applicability. Runtime evidence remains `NOT_ASSESSED`.
- **Inference:** a compliant `contract.yaml` solution requires a governed
  generator/validator projection change and generated-output ownership updates.
  The narrower confirmed fact is that the current generator has no writer while
  ADR-0007 forbids maintaining those files by hand.
- **Inference:** restoring all 2,444 inherited tests is outside this
  behavior-preserving topology task and could change the test command's behavior.
  The confirmed rule is that their absence requires accepted evidence that does
  not exist.

## Remaining risk

1. Source topology has not been executable-validated. The committed assessment
   can remain a stale `PASS` because validator failure returns before writing a
   replacement report.
2. Clearing ADR-0010 requires real causal migration/retirement and landing
   evidence, or an owner-authorized change to the accepted policy. Neither can
   be fabricated in this task.
3. Context contract projection issuance is missing. Adding it affects the
   generator, validator, generated-output authority, licensing inventory, and
   contract-tree completeness; it is more than a product-tree move.
4. After those blockers, the twelve failed topology corrections remain: move
   CLI into `delivery`, move evaluation and its table to `assurance`, expose
   public APIs, remove private/undeclared edges and import-time registration,
   centralize wiring, mirror tests, add navigation, and close ownership gaps.
5. A green current validator would still not prove all 18 rules until its
   source scan enforces the rules it currently omits.

## Command execution record

All commands ran from `/home/soultransit/devtony/ranex`. File-display commands
(`sed`, `nl`, `rg`, `find`, and inline Python) produced the path:line evidence
quoted above. Large governance documents are not duplicated here; their exact
line counts and material outputs are recorded below.

### Governance reads and inspections

```text
$ pwd; rg --files for AGENTS.md, bootstrap authorization, slice definition,
  ADR-0007, scripts/architecture/README.md, and docs/HANDOFF.md
/home/soultransit/devtony/ranex
AGENTS.md
scripts/architecture/README.md
architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md
docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md
docs/HANDOFF.md
docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md

$ wc -l AGENTS.md scripts/architecture/README.md BOOTSTRAP-AUTH-001.md
  walking-skeleton-definition.md ADR-0007... docs/HANDOFF.md
148 AGENTS.md
53 scripts/architecture/README.md
111 architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md
207 docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md
387 docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md
392 docs/HANDOFF.md
1298 total

$ wc -l ADR-0010... ADR-0008...
1917 docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md
1798 docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md
3715 total
```

The executed registry/source audit printed:

```text
registered contexts: 34
cli_registered=False
unowned source paths:
  src/ranex/__init__.py
  src/ranex/cli/__init__.py
  src/ranex/cli/confinement.py
  src/ranex/cli/main.py
  src/ranex/foundation/__init__.py
  src/ranex/foundation/canonical.py
  src/ranex/foundation/identity.py
context metadata:
  assurance          __init__.py=True README.md=False contract.yaml=False
  governed_execution __init__.py=True README.md=False contract.yaml=False
  policy             __init__.py=True README.md=False contract.yaml=False
legacy_baseline_files=2444
migration_proofs=0
cutover_removal_records=0
topology_exceptions=0
declared_policy_to_governed_execution=False
declared_delivery_to_governed_execution=True
declared_graph_nodes=34 topologically_sorted=34 acyclic=True
actual_registered_edges=policy->governed_execution
actual_graph_acyclic=True
context README/contract search: no output
legacy/hermes product import search: no output
product migration path search: no output
```

The initial `git status --short`, before this task wrote any file, was:

```text
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

### Required validation commands and actual output

```text
$ uv run --project scripts/architecture python scripts/architecture/generate_contracts.py
{"assessments": 41, "projections": 10, "registries": 46, "schemas": 157}
EXIT=0

$ diff -u /tmp/luna-adr7-generated-before.sha256 /tmp/luna-adr7-generated-after.sha256
(no output)
EXIT=0

$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
{"checks": { ... "allowed_test_roots": 18, ...
"legacy_test_baseline_files": 2444, ... "observed_test_roots": 6, ...
"production_test_layout_files_scanned": 12, ... "topology_rules": 18, ... },
"error": "LEGACY_TEST_MIGRATION_PROOF_MISSING:tests/acp/__init__.py",
"status": "FAIL"}
EXIT=1

$ uv run pytest -q
....................................                                     [100%]
36 passed in 0.20s
EXIT=0

$ uv run --with pyrefly==1.1.1 pyrefly check
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
EXIT=0
```

The baseline test/type commands were also run before any attempted change:

```text
$ uv run pytest -q
....................................                                     [100%]
36 passed in 0.19s
EXIT=0

$ uv run --with pyrefly==1.1.1 pyrefly check
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
EXIT=0
```

The first complete validator capture, before pytest created the root cache,
reported `observed_test_roots: 5`, `production_test_layout_files_scanned: 11`,
the same exact error, and exit 1. Earlier validator attempts waiting for the
repository lock emitted:

```text
ranex-contract-tree-lock: waiting for exclusive lock
```

They were not used as pass/fail evidence.

### Other executed shell commands

The remaining shell invocations were read-only `sed`/`nl` excerpts of the files
cited above; `rg` searches for topology rules, imports, `contract.yaml`, and
source references; `find` inventories of `src/ranex` and `tests`; inline Python
parsing of JSON registries and Python AST imports; process/lock diagnostics;
SHA-256 inventory creation in `/tmp`; and `git status --short`. Their actual
material outputs are reproduced in the rule table and inspection output block.

The cache cleanup command output was:

```text
moved test-runner cache to /tmp/luna-adr7-tests-init.cpython-314.pyc
```
