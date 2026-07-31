# CLI boundary fixes

Status: both HIGH defects fixed; LOW documentation defect partially blocked by
an owner-accepted content pin.

## Scope and evidence classification

### CONFIRMED

- `2026-07-31-final-gate-adjudication.md` reproduces two adapter-boundary failures: omitted
  `subject_digest` is replaced with the evaluated subject, and no production
  caller invokes `resolve_within_repository`.
- `src/ranex/governed_execution/domain/verdict.py` already requires an exact
  subject digest. This repair therefore belongs in `src/ranex/cli/main.py`, not
  in the domain.
- `SLICE-LANE-007` says the entry point resolves every path against the governed
  repository root and refuses absolute paths, traversal, remotes, and a second
  repository. Accordingly, `--repository`, `--gate-catalog`, `--evidence`, and
  `--journal` are all confined inputs.
- The three incorrect documented invocations are in the review documents named
  by `2026-07-31-final-gate-adjudication.md` section 1.1.
- Before implementation,
  `uv run pytest -q tests/e2e/test_gate_evaluate_cli.py` from
  `/home/soultransit/devtony/ranex` produced `5 failed, 5 passed`. The omitted
  subject test printed `PASS`; the three absolute auxiliary-path cases were not
  rejected by confinement; and the real CLI subprocess evaluated the foreign
  tree and returned a policy `FAIL` instead of a boundary error.
- After the adapter change,
  `uv run pytest -q tests/e2e/test_gate_evaluate_cli.py tests/security/test_repository_confinement.py`
  from `/home/soultransit/devtony/ranex` produced `16 passed in 0.27s`.

## Implemented repairs

- Evidence loading now indexes `item["subject_digest"]`; omission raises the
  `KeyError` already mapped by the CLI to exit 2.
- The CLI discovers the governed Git root from the installed CLI module's path,
  independent of caller cwd, resolves all four path arguments through
  `resolve_within_repository`, and additionally requires the resolved
  `--repository` path to equal that root.
- E2e fixtures now invoke the CLI from the governed temporary repository and use
  relative catalog, evidence, and journal paths. New tests exercise omitted
  subject binding, all three auxiliary absolute-path inputs, and a real CLI
  subprocess aimed at a foreign Git repository.
- Two unpinned review documents identified in `2026-07-31-final-gate-adjudication.md` section 1.1 now
  show the complete explicit module form, including required `--approver`.
- The walking-skeleton definition is content-pinned by ADR-0021 and cannot be
  corrected without changing that owner-accepted ADR or its pin. It remains
  unchanged; see Remaining risk.

## Direct attack replays

### CONFIRMED: omitted subject digest is refused

Working directory: `/home/soultransit/devtony/ranex`

```text
$ PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --evidence governance/attack-no-subject.json --approver reviewer
ERROR  'subject_digest'
exit=2
```

The temporary evidence file contained the two records from the independent
attack, both without `subject_digest`; it was deleted after execution.

### CONFIRMED: foreign repository evaluation is refused

Working directory: `/home/soultransit/devtony/ranex`

```text
$ PYTHONPATH=src uv run python -m ranex.cli.main gate evaluate HEAD --repository /tmp/ranex-foreign-2CuLTW --gate-catalog /tmp/ranex-foreign-2CuLTW/attacker-gates.yaml --evidence /tmp/ranex-foreign-2CuLTW/attacker-evidence.json --journal /tmp/ranex-foreign-2CuLTW/attacker-journal.sqlite3 --approver reviewer
ERROR  absolute paths are refused: '/tmp/ranex-foreign-2CuLTW'
exit=2
```

`/tmp/ranex-foreign-2CuLTW` was an initialized foreign Git repository with its
own commit. It was moved to trash after execution.

## Required validation

### CONFIRMED: full product test suite

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run pytest -q
.........................................                                [100%]
41 passed in 0.38s
exit=0
```

### CONFIRMED: strict product type check

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --with pyrefly==1.1.1 pyrefly check
 INFO Checking project configured at `/home/soultransit/devtony/ranex/pyrefly.toml`
 INFO 0 errors (3 warnings not shown)
exit=0
```

### CONFIRMED: first contract-validation attempt failed closed

Working directory: `/home/soultransit/devtony/ranex`

The first attempt followed a direct textual correction in all three documents.
It returned exit 1 with:

```text
{"error": "ADR21_LEGACY_TEST_LINEAGE_UNKNOWN_BLOCKING:UNKNOWN_BLOCKING", "status": "FAIL"}
```

Inspection confirmed that ADR-0021 pins the exact walking-skeleton document
digest in its accepted machine block and that the generator and validator both
enforce it. The edit was restored; ADR-0021 and all of its pins remain unchanged.

### CONFIRMED: rejected packaging workaround

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run ranex gate evaluate HEAD --approver owner
   Building ranex @ file:///home/soultransit/devtony/ranex
      Built ranex @ file:///home/soultransit/devtony/ranex
Installed 1 package in 1ms
FAIL  gate=landing  rule=TESTS_EXECUTED
      evidence bound to a different subject digest: contracts-validated, tests-executed
      subject=sha256:16fa87aa23cc35649463caaeab502e5b14b8e42f062a61a2db13142e4ccc0dfe
exit=1
```

This proved `package = true` could install a console entry point under `uv run`,
but it did not make the pinned bare invocation complete: that line also omits
required `--approver`, and bare execution still depends on environment
activation. Defaulting an approver would weaken identity enforcement. The
packaging change was therefore reverted to avoid an incomplete workaround and
scope expansion.

### CONFIRMED: contract validation

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --project scripts/architecture python scripts/architecture/validate_contracts.py
... "production_test_construct_validation": "PASS",
    "scope": "EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY",
    "source_topology_validation": "PASS",
    "status": "PASS",
    "test_layout_migration": "NOT_APPLICABLE_NO_INHERITED_SUBJECT",
    "test_layout_validation": "CANONICAL_TOPOLOGY_PASS" ...
exit=0
```

The displayed fields are exact excerpts from the validator's one-line JSON
output; the complete output was retained in the execution record.

### CONFIRMED: record freshness

Working directory: `/home/soultransit/devtony/ranex`

```text
$ uv run --project scripts/architecture python scripts/architecture/check_record_freshness.py
records fresh: 21 ADRs, 10 RFCs, no stale claims
exit=0
```

## ADR-0021 section 3.2 assessment — report only

### CONFIRMED

I agree with the independent gate's MEDIUM rating. The resolver proves that
observed facts equal repository assertions, but it does not independently
require the three non-inheritance counts to equal literal zero. Coordinated edits
to the assertion, schema constraints, ADR machine block, and local digest pins
could therefore make a contaminated boundary satisfy the non-inheritance branch.
The existing multi-file pins make that visible and expensive, and unresolved
observations fail closed, so HIGH would overstate the current exploitability.

### Recommendation

Do not change ADR-0021 in this repair. Record the weakness and reopen it before
the non-inheritance outcome authorizes anything beyond the bounded bootstrap
slice. At that point, use an owner-approved superseding decision to make the
independent resolver require literal-zero contamination counts and externally
anchor which inherited baseline commit is authoritative. This recommendation
does not override the current ADR freeze or owner acceptance.

## ASSUMED

- The Git checkout containing the Ranex CLI module is the governed repository.
  A distribution installed outside that checkout will fail closed because the
  bounded first slice is not authorized to govern arbitrary repositories.

## Remaining risk

- Defect 3 is only partially repaired. Two documents are corrected. Correcting
  `docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md` changes
  the digest pinned by owner-accepted ADR-0021 and makes contract validation fail
  closed. The user's instruction not to change ADR-0021 prevents resolving that
  conflict in this change.
- The worktree was concurrently edited during validation. A transient literal
  `<replace>` marker appeared at the start of `bootstrap/composition.py`; only
  that marker was removed, preserving the concurrent logical changes. Final
  pytest, type, contract, and freshness results above are from the stable state.

## Final audit

### CONFIRMED

- `docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md` remains
  byte-identical to its ADR-0021 pin:
  `368d5e415f76ebb5062f58a8692a61ea68df650016aab821c68d1e04dbdadc5a`.
- No temporary `governance/attack-*` file remains, and the foreign repository
  used for the final replay was moved to trash.
- `git diff --check` passed from `/home/soultransit/devtony/ranex`.
- Concurrent repository activity advanced `HEAD` to
  `f46c4e5ade1216f7a4bc299fc3446bae116c1acd`; the final validation results in
  this report were measured after that change.
