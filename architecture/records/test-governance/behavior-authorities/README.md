# Test-behavior authority sources

This is the sole canonical source root for ADR-0010 test-behavior authority
records. The live initial population is intentionally empty and therefore
grants no behavior authority.

Only canonical JSON files named
`<behavior_id>@<behavior_version>.json` are eligible. Each file must validate
against `schemas/common/test-behavior-authority-v1.schema.json`, and every file
must have exactly one byte-bound row in
`architecture/contracts/test-behaviors.json`. The source/catalog bijection,
source path, and finalized source-byte digest are mandatory.

This README, YAML authoring templates, symlinks, ignored files, alternate
roots, and synthetic fixtures are never authority sources. Any unexpected
entry, duplicate, orphan, path mismatch, digest mismatch, or absent eligible
`ACTIVE` source fails closed.

