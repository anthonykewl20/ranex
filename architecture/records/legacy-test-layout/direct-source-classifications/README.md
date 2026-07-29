# Direct-source classification authority sources

This is the sole canonical source root for ADR-0010 direct legacy-test
classification authority records. The live initial population is intentionally
empty and therefore grants no direct-source classification authority.

Only canonical JSON files named `<classification_id>.json` are eligible. Each
file must validate against
`schemas/common/direct-source-classification-authority-v1.schema.json`, and
every file must have exactly one byte-bound row in
`architecture/contracts/legacy-test-direct-source-classifications.json`. The
source/catalog bijection, source path, and finalized source-byte digest are
mandatory.

This authority record is the first stable V1 of its own type, but every record
const-binds `RANEX-LEGACY-TEST-LAYOUT-2.0` at `2.0.0` and may authorize only
policy2/V2 transitions. Its V1 type label is never policy1 compatibility.

This README, YAML authoring templates, symlinks, ignored files, alternate
roots, and synthetic fixtures are never authority sources. Any unexpected
entry, duplicate, orphan, path mismatch, digest mismatch, or absent eligible
`ACTIVE` source fails closed.
