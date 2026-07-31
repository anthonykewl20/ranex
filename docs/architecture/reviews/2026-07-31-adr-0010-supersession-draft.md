# Draft superseding record — limit ADR-0010 to inherited lineage

> **Historical status: SUPERSEDED BY PROMOTION.** The human owner accepted this
> draft on 2026-07-31. It was promoted, with its machine projection preserved,
> to
> [`ADR-0021`](../decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md).
> This review copy remains in place as architectural history and grants no
> separate authority.

| Field | Value |
|---|---|
| Intended ADR ID | `ADR-0021` |
| Intended version | `1.0.0` |
| Status | `SUPERSEDED_BY_PROMOTION` |
| Decision owner | Human owner |
| Draft date | 2026-07-31 |
| Effective subject | Descendants of bootstrap boundary `f2c04c1674282052e26648b756481da337b45458` whose root is `4ee007fcbe40b1afa7c362767005cf2f4508fc3d`; exact ancestry is resolved from Git, never from a branch name |
| Supersedes | ADR-0010 only where its named baseline is not inherited by the exact exception lineage; ADR-0010 remains fully binding on subjects descended from `0533e1eaf50ace0eb84435a5c3de05e939fd4daa` |
| Compatibility/migration class | Scope correction supported by executed provenance evidence; no baseline file is classified as migrated or retired |
| Authority | Promoted to accepted `ADR-0021`; this historical draft has no independent authority |

## Why this record exists

ADR-0010 is an anti-recontamination and migration contract for 2,444 tests in
the accepted Hermes upstream-derived source
`0533e1eaf50ace0eb84435a5c3de05e939fd4daa`. The current bootstrap lineage does
not inherit that source.

Executed evidence is recorded in the repository-root
`LEGACY-TEST-RESOLUTION.md`:

- `git merge-base --is-ancestor 0533e1... HEAD` exited 1;
- `git merge-base HEAD develop` exited 1;
- the exact bootstrap lineage root is
  `4ee007fcbe40b1afa7c362767005cf2f4508fc3d`;
- `git log HEAD -- tests` emitted no commits and `git ls-tree -r HEAD -- tests`
  counted zero committed paths at boundary
  `f2c04c1674282052e26648b756481da337b45458`;
- the generated ADR-0010 projection contains exactly 2,444 baseline paths;
- zero of those paths exists in the working tree;
- the migration, change-exception, and cutover registries each contain zero
  records; and
- production validation fails on the first nonexistent baseline path as soon
  as ADR-0008-compliant Ranex tests make `tests/` exist.

This is not a migration. No inherited source was moved, renamed, changed, or
retired on this lineage. Requiring 2,444 migration proofs for events that did
not occur would fabricate provenance and would still be unsatisfiable because
the production validator supplies no landing-record resolver.

## Proposed decision

### ADR21-LINEAGE-001 — inheritance is resolved from exact Git ancestry

ADR-0010 applies in full when its baseline source commit
`0533e1eaf50ace0eb84435a5c3de05e939fd4daa` is an ancestor of the exact
validation commit.

The mere presence of that object in a shared Git object database, a mutable
branch name, a remote-tracking reference, or another branch containing it does
not make the baseline inherited by the validation subject.

### ADR21-LINEAGE-002 — one exact bootstrap lineage has no inherited baseline

The ADR-0010 baseline is `NOT_APPLICABLE_NO_INHERITED_SUBJECT` only when all of
the following are independently true:

1. the validation commit is the exact boundary
   `f2c04c1674282052e26648b756481da337b45458` or its descendant;
2. that boundary descends from the one exact root
   `4ee007fcbe40b1afa7c362767005cf2f4508fc3d`;
3. the ADR-0010 source commit is not an ancestor of the validation commit;
4. the boundary's committed `tests` tree is absent;
5. the boundary's complete ancestry contains no committed `tests/` path;
6. the accepted baseline's 2,444 paths have zero intersection with the
   boundary tree; and
7. the separately bound bootstrap authorization and walking-skeleton
   definition match their accepted source digests.

This is an exact-subject exception, not a general “no common ancestor” rule.
Any other non-descendant lineage is `UNKNOWN` and blocks until a human-accepted
record binds its provenance. Creating, rebasing, or replacing history to escape
an applicable ADR-0010 baseline is a blocking governance violation.

If a later merge makes the ADR-0010 source commit an ancestor, rule
ADR21-LINEAGE-001 wins and the full inherited-baseline contract applies.

### ADR21-LINEAGE-003 — ADR-0008 remains fully binding

On the exact non-inherited lineage, validation skips only the comparison against
the foreign 2,444-file manifest. It still independently enforces every
ADR-0008 canonical root and path rule against all present tests.

Missing `tests/` is a blocking `PRODUCTION_TEST_ROOT_MISSING` result. It must
never become `NOT_ASSESSED`, `NOT_APPLICABLE`, or overall `PASS`.

An invalid canonical path, new legacy root, direct file under `tests/`, baseline
path reintroduction, symlink, malformed Python source, or test-only production
branch remains blocking. No check is relaxed or demoted.

### ADR21-LINEAGE-004 — no migration event may be invented

The exact non-inherited lineage requires zero ADR-0010 migration, change, and
cutover records because it contains zero inherited baseline subjects. A record
claiming migration or retirement of those absent subjects is invalid.

This does not change ADR-0010's 59-field V2 migration record, evidence,
authority, causal Git, landing-record, expiry, or cutover rules on any subject
where ADR-0010 applies.

### ADR21-LINEAGE-005 — validation report failure publication is separate

The observed stale `PASS` report after a validator failure is a separate defect.
This decision neither authorizes nor specifies its repair. Failure-report
publication needs its own bounded tooling change and regression evidence.

## Proposed machine projection

Acceptance would add one generated, versioned applicability contract rather
than reinterpret ADR-0010's V2 policy:

```yaml
legacy_test_lineage_applicability:
  schema_version: "legacy-test-lineage-applicability/v1"
  policy_id: "RANEX-LEGACY-TEST-LINEAGE-APPLICABILITY-1.0"
  version: "1.0.0"
  inherited_baseline:
    source_commit_sha1: "0533e1eaf50ace0eb84435a5c3de05e939fd4daa"
    baseline_id: "HERMES-TEST-BASELINE-001"
    file_count: 2444
    file_manifest_sha256: "e550a598da0e226a94a7b15c9a0ace9c48a58e04df146bbe044a7cedcc41e463"
  exact_noninherited_lineage:
    root_commit_sha1: "4ee007fcbe40b1afa7c362767005cf2f4508fc3d"
    boundary_commit_sha1: "f2c04c1674282052e26648b756481da337b45458"
    boundary_committed_test_path_count: 0
    boundary_ancestry_test_commit_count: 0
    boundary_baseline_path_intersection_count: 0
    bootstrap_authorization_ref: "architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md"
    bootstrap_authorization_sha256: "f517be8da802aee6fe46dfa4293da294b618cb982bd836413b3663bff3ee51d8"
    walking_skeleton_definition_ref: "docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md"
    walking_skeleton_definition_sha256: "368d5e415f76ebb5062f58a8692a61ea68df650016aab821c68d1e04dbdadc5a"
  outcomes:
    inherited_descendant: "ADR0010_APPLIES"
    exact_noninherited_descendant: "NOT_APPLICABLE_NO_INHERITED_SUBJECT"
    any_other_non_descendant: "UNKNOWN_BLOCKING"
  missing_tests_result: "FAIL"
```

The generator would emit and schema-bind that contract. The validator would
resolve the exact commit ancestry and boundary facts before choosing a branch,
then run either the unchanged ADR-0010 baseline comparison or the unchanged
ADR-0008 canonical-layout comparison.

## Digest-pin impact

ADR-0010 is retained byte-for-byte as historical authority. Therefore none of
its existing pins moves:

- `ADR10_SOURCE_SHA256` remains
  `45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb`;
- `ADR10_MACHINE_BLOCK_SHA256` remains
  `de5ed30d02ffac788574b319ac9afcc4c1246212b0b015251ac055bd7ef17472`;
- `ADR10_BEHAVIOR_TEMPLATE_SHA256` and
  `ADR10_CLASSIFICATION_TEMPLATE_SHA256` also remain unchanged.

Acceptance introduces, rather than moves, two pins:

- `ADR21_SOURCE_SHA256` for the accepted superseding ADR bytes; and
- `ADR21_MACHINE_BLOCK_SHA256` for the finalized marked
  `legacy_test_lineage_applicability` YAML block.

Their values cannot be truthfully recorded until the human-owned text is
accepted and finalized. Generated registry/schema/manifest digests will then
change through normal regeneration; they are outputs, not hand-edited pins.

## Predeclared acceptance tests

1. A descendant of `0533e1...` receives the unchanged ADR-0010 comparison.
2. The exact bootstrap boundary resolves
   `NOT_APPLICABLE_NO_INHERITED_SUBJECT` only after all seven provenance checks.
3. A descendant of the bootstrap boundary with valid ADR-0008 tests passes the
   canonical topology check without requiring foreign migration proofs.
4. Removing `tests/` fails `PRODUCTION_TEST_ROOT_MISSING`.
5. A different orphan lineage is `UNKNOWN` and blocks.
6. Making `0533e1...` an ancestor reactivates ADR-0010.
7. Adding one ADR-0010 baseline path to the non-inherited lineage blocks as
   recontamination.
8. A migration, change-exception, or cutover record on the non-inherited
   lineage blocks as invented provenance.
9. Mutating the root, boundary, authorization digest, definition digest,
   baseline ID, count, or manifest digest blocks.
10. ADR-0010's current positive and negative fixtures remain unchanged and pass.

## Consequences and unchanged obligations

- The walking skeleton may use the canonical ADR-0008 test roots after human
  acceptance and machine projection.
- No Hermes test is declared migrated, retired, missing, or waived.
- ADR-0010 continues to bind every subject that inherits its source commit.
- ADR-0008, TDD evidence, strict typing, generated-output integrity, record
  freshness, owner separation, and every readiness/production gate remain
  unchanged.
- Neither readiness tier is declared.
- This draft grants no authority and changes no active generated contract until
  accepted by the human owner.

## Human decision

The owner accepted this exact-subject supersession on 2026-07-31. The accepted
authority is `ADR-0021`; this retained draft must not be treated as a separate
bypass or authority source.
