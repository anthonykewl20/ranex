# Legacy test-layout governed records

This is the sole active-source root for ADR-0010 instance records. The initial
record set is empty.

Only JSON files at these exact paths are accepted:

- `change-exceptions/<change_exception_id>.json`
- `migration-records/<proof_id>.json`
- `cutover-removal-records/<cutover_removal_record_id>.json`
- `direct-source-classifications/<classification_id>.json`

Each filename must equal the record ID. JSON at this root, in a nested
subdirectory, or in any other child directory is rejected. The contract
compiler embeds validated records in
`architecture/contracts/legacy-test-layout-policy-v2.json` and projects their
source paths and digests to
`architecture/contracts/legacy-test-layout-records-v2.json`.
Direct-source classifications instead project bijectively to
`architecture/contracts/legacy-test-direct-source-classifications.json` and
must satisfy their separately landed authority chain.

ADR-0010 contract 2.0 accepts only policy2/V2 change, migration, and cutover
sources. Historical v1 schemas remain reference artifacts, but a v1 or mixed
v1/v2 active source population fails closed and produces no generated output.

The corresponding unversioned contract paths are frozen V1 compatibility
aliases, not current pointers.

See
[`ADR-0010`](../../../docs/architecture/decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md)
for lifecycle, authority, expiry, migration, and cutover semantics.
