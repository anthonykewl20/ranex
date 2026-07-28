# Architecture contract tooling

Run from the repository root:

```sh
uv run --project scripts/architecture \
  python scripts/architecture/generate_contracts.py
uv run --project scripts/architecture \
  python scripts/architecture/validate_contracts.py
uv run --project scripts/architecture \
  python scripts/architecture/test_contract_concurrency.py
```

`generate_contracts.py` deterministically derives registries, JSON Schemas,
architecture-element inventory, capability-assessment baselines, domain
projections, fixtures, and completeness reports from the accepted normative
documents and authoring templates.

`validate_contracts.py` rejects duplicate YAML keys, schema drift, registry
referential-integrity defects, manifest drift, forged digests, permit reuse,
subject mismatches, stale subjects, incomplete VITAL profiles, arithmetic
capability aggregation, and dishonest runtime scoring.

Generation and validation both hold the same repository-scoped interprocess
lock from their first read through their final write. The lock is outside all
generator-owned trees, so a validator or second writer waits rather than
observing a partial cleanup/publication. `test_contract_concurrency.py` verifies
that behavior in a disposable repository copy by staging an empty assessment
denominator, contending with both a validator and second generator, and
requiring the post-release tree digest to equal its baseline.

The validation report binds the exact generator, validator, lock module, and
concurrency-regression script digests alongside the registry, schema, practice
profile, and assessment-subject digests.

The tooling validates executable documentation contracts. It does not claim
that runtime producers, storage, policy enforcement, or isolation controls
exist.
