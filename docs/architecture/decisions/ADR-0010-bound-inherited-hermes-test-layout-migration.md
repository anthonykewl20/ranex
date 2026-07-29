# ADR-0010: Bind the Inherited Hermes Test Layout and Its Migration

| Field | Value |
|---|---|
| ADR ID | `ADR-0010` |
| Version | `2.0.1` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | The accepted upstream-derived baseline `0533e1eaf50ace0eb84435a5c3de05e939fd4daa`; migration and runtime evidence pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `compatibility`, `migration`, `process_assurance`, all test lanes, and every context whose behavior is exercised by inherited Hermes tests |
| Supersedes | No ADR; constrains coexistence between the inherited Hermes test tree and ADR-0008 |
| Review/expiry date | Review on every row trigger; authorization expires 2026-10-31T23:59:59Z unless the row closes sooner through migration/deletion and the complete cutover is accepted and landed by that instant |
| Compatibility/migration class | Time-bounded strangler exception; no test is claimed migrated |
| Security/data class | Public design and source-integrity metadata; test evidence inherits its subject classification |

## Decision

ADR-0008 remains the sole target test-layout policy. The accepted Hermes
upstream-derived source, however, contains inherited tests outside that target.
Deleting, moving, or relabeling them merely to make a topology check green
would destroy regression evidence and increase upstream-sync risk.

Ranex therefore accepts one bounded, immutable compatibility baseline:

- unchanged baseline files may continue to execute as inherited regression
  evidence;
- they do not establish Ranex TDD enactment, architecture conformance, gate
  `PASS`, or migration completion;
- no new Ranex test may be created in an inherited root or directly under
  `tests/`;
- any added file in a legacy or direct-top-level scope is a blocking
  recontamination finding; a change exception cannot enlarge the baseline;
- an in-place content change to an existing baseline path requires a
  registered, expiring change exception and migration review before landing;
- a move or rename is a migration: its new path must be canonical under
  ADR-0008 and it requires complete migration proof, never a change exception;
- intentional retirement is authorized only by ADR-0008's canonical
  `TestDeletionRecordV1`, for either the exact legacy source or a later stable
  canonical test; a migration record is not a parallel retirement authority;
- new Ranex tests may be created only below the 18 canonical ADR-0008 roots;
  and
- every inherited scope has one destination, accountable owners, trigger,
  expiry, and removal-proof profile.

This is an anti-recontamination contract, not a waiver of ADR-0008. All source,
test, runtime, and migration results begin `NOT_ASSESSED`.

## Immutable baseline

The complete baseline is machine-bound as follows:

```yaml
legacy_test_layout_policy_id: "RANEX-LEGACY-TEST-LAYOUT-2.0"
legacy_test_baseline:
  baseline_id: "HERMES-TEST-BASELINE-001"
  source_commit_sha1: "0533e1eaf50ace0eb84435a5c3de05e939fd4daa"
  tests_tree_oid_sha1: "e331f2ea8d5233ed74ca42d2380c1c6fd4e58c67"
  file_count: 2444
  mode_counts: {"100644": 2444}
  ls_tree_command: "git ls-tree -r --full-tree 0533e1eaf50ace0eb84435a5c3de05e939fd4daa -- tests"
  ls_tree_exact_stdout_sha256: "cab0556790b9ddcb7cabcd6c1d7ff6d8ca6a9065a391e06a17239cfb5f36a076"
  file_manifest_serialization: "<path>\\t<mode>\\t<git_blob_oid_sha1>\\t<content_sha256>\\n; UTF-8; LF; bytewise path order"
  file_manifest_sha256: "e550a598da0e226a94a7b15c9a0ace9c48a58e04df146bbe044a7cedcc41e463"
  directory_exception_file_count: 2294
  direct_top_level_file_count: 134
  inherited_canonical_file_count: 16
  partition_equation: "2294 + 134 + 16 = 2444"
  evidence_status: "BASELINE_BOUND_NOT_MIGRATED"
```

The executable projection
`architecture/contracts/legacy-test-layout-policy-v2.json` embeds all 2,444
bytewise path-sorted file rows with `path`, mode, Git blob OID, and SHA-256 of
the blob bytes. It validates against
`schemas/common/legacy-test-layout-policy-v2.schema.json`. A mutable branch
name, working-tree path, count alone, subtree name alone, or aggregate digest
alone is insufficient evidence.

The predecessor projection and empty record manifest are preserved byte-for-
byte at explicit `-v1.json` paths and at their historical unversioned paths.
Those unversioned files are frozen V1 compatibility aliases, not current
pointers. Contract-2 consumers must use only the explicit `-v2.json` paths;
an unversioned lookup or policy-major mismatch is blocking `UNKNOWN`.

The policy projection is definition-only and is never the mutable instance
store. Governed instances have these sole canonical source locations:

```text
architecture/records/legacy-test-layout/
├── direct-source-classifications/
│   └── <classification_id>.json
├── change-exceptions/
│   └── <change_exception_id>.json
├── migration-records/
│   └── <proof_id>.json
└── cutover-removal-records/
    └── <cutover_removal_record_id>.json

architecture/records/test-governance/
└── behavior-authorities/
    └── <behavior_id>@<behavior_version>.json
```

The contract compiler reads only canonical JSON files matching those patterns,
requires each filename to equal its record ID, sorts them bytewise by relative
path, and validates them respectively against:

- `schemas/common/direct-source-classification-authority-v1.schema.json` with
  record type `DIRECT_SOURCE_CLASSIFICATION_AUTHORITY`;
- `schemas/common/legacy-test-change-exception-v2.schema.json` with record type
  `LEGACY_TEST_CHANGE_EXCEPTION`;
- `schemas/common/legacy-test-migration-record-v2.schema.json` with record type
  `LEGACY_TEST_MIGRATION_RECORD` and proof type
  `LEGACY_TEST_MIGRATION_PROOF_V2`; and
- `schemas/common/legacy-test-cutover-removal-record-v2.schema.json` with record
  type `LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2`; and
- `schemas/common/test-behavior-authority-v1.schema.json` with record type
  `TEST_BEHAVIOR_AUTHORITY`.

It embeds validated active transition records in
`legacy-test-layout-policy-v2.json` and projects their exact source paths and
digests to
`architecture/contracts/legacy-test-layout-records-v2.json`
(`REG-LEGACY-TEST-LAYOUT-RECORDS-001`). Direct-source classification authority
sources instead project bijectively to the closed
`DirectSourceClassificationAuthorityRowV1` catalog
`architecture/contracts/legacy-test-direct-source-classifications.json`
(`REG-LEGACY-TEST-DIRECT-SOURCE-CLASSIFICATIONS-001`). The general legacy
record manifest may additionally reference those catalog row IDs/digests for
whole-tree completeness, but it cannot replace, override, or independently
derive classification authority. The classification catalog row's
`source_path` is derived from `classification_id`; `source_digest` is the
SHA-256 of the exact finalized source bytes and is never a field inside those
bytes. Exact catalog/source bijection is mandatory. The global registry
manifest content-binds all projections. The initial transition and
classification source sets are empty; that is valid only while the exact
inherited baseline is unchanged and does not imply classification, migration,
or cutover.

Behavior authority sources project separately and bijectively to
`architecture/contracts/test-behaviors.json`
(`REG-TEST-BEHAVIORS-001`). Every source has exactly one registry row, every
row has exactly one canonical source, and both exact source bytes and normalized
row digests are content-bound by the global registry manifest. The live initial
behavior-authority population is empty. That is a fail-closed current fact:
synthetic contract-satisfiability fixtures may prove the schema and resolver,
but they grant no current direct-top-level change or migration authority.

Intentional retirement records are not duplicated under this tree. ADR-0008's
sole source
`architecture/records/test-health/obsolete-test-deletions/<deletion_id>.json`,
schema `schemas/common/test-deletion-record-v1.schema.json`, and registry
`architecture/contracts/test-deletion-records.json`
(`REG-TEST-DELETION-RECORDS-001`) are authoritative. The legacy-layout
registry references accepted deletion IDs and digests; it never embeds or
rewrites their authority.

Lifecycle authority is exact:

- a test-behavior authority and a direct-source classification authority are
  each `PROPOSED -> ACTIVE | REJECTED`; only an independently landed `ACTIVE`
  source with an eligible owner `HumanDecisionRecord`, an unexpired
  non-superseded subject, and exact catalog/source bijection can authorize a
  direct-top-level transition;
- a change exception is `PROPOSED -> ACTIVE -> CLOSED | REVOKED | EXPIRED`;
  a proposal outside the canonical directory grants nothing, and only one
  schema-valid, nonexpired `ACTIVE` source record can authorize the in-place
  byte change it binds;
- a migration/removal proof is `PROPOSED -> ACCEPTED | REJECTED`; only an
  accepted `LEGACY_TEST_MIGRATION_RECORD` with `result: PASS` can dispose its
  exact missing
  baseline file as `MIGRATED`;
- a `TestDeletionRecordV1` is `PROPOSED -> ACCEPTED | REJECTED`; only an
  accepted `LEGACY_SOURCE` record can directly derive one baseline source as
  `RETIRED`, and only an accepted `CANONICAL_TEST` record can transition one
  stable migrated test lineage from `ACTIVE` to `RETIRED`; and
- a cutover/removal record is `PROPOSED -> ACCEPTED | REJECTED`; only
  `LEGACY-TEST-CUTOVER-001` as a schema-valid
  `LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2` with `result: PASS` can request a
  cutover claim.

Per-record subject binding must remain valid as later strangler slices land:

- every record binds `policy_id: RANEX-LEGACY-TEST-LAYOUT-2.0`,
  `policy_version: 2.0.0`, and `baseline_id: HERMES-TEST-BASELINE-001`;
- an active change exception binds `transition_sequence: 1`,
  `predecessor_transition_id: HERMES-TEST-BASELINE-001`, a nonempty
  `causation_ref`, `landing_record_ref`, `before_commit_sha1`,
  `after_commit_sha1`, `before_tests_snapshot_digest`, and
  `after_tests_snapshot_digest`; its `baseline_row` and `current_row` are the
  exact before/after rows for one unchanged baseline path;
- accepted migration records form atomic groups. Every member binds one exact
  `baseline_source_row` (old path/blob/content), one event-time
  `current_source_row` (path/mode/content), `source_state_kind` plus its
  nullable prior-change fields and `closes_change_exception_id`,
  `migration_group_id`,
  `group_member_index`, `group_member_count`, the group's globally unique contiguous
  `transition_sequence`, `predecessor_transition_id` (the baseline ID for
  sequence 1, otherwise the immediately prior `migration_group_id`), one
  shared nonempty `causation_ref`, `landing_record_ref`, before/after commit
  IDs, test-snapshot digests, inherited-disposition digests, and
  `destination_rows[{path, mode, content_sha256, test_id}]`. Every member also
  binds the same exact test-practice profile ID/version/digest, group transition
  subject ref/digest, group member-manifest digest, tests-delta-manifest digest,
  typed evidence/decision references, and `accepted_at`; and
- a cutover/removal record alone binds the complete resulting event-time test-tree
  event snapshot through causal before/after commits, tree OIDs and snapshot
  digests, a tests-delta-manifest digest, plus
  `migration_transition_count` and `ordered_migration_subset_digest` for the
  ordered accepted-migration subset, exact lineage digest, profile binding,
  typed evidence/decisions, `accepted_at`, and one successful
  `landing_record_ref`.

All subject-digest fields use `sha256:<64 lowercase hex>` over the declared
canonical-JSON subject, not over the record containing that digest.
`exact_subject_digest` binds the record-local transition payload.
`before_tests_snapshot_digest` and `after_tests_snapshot_digest` bind immutable
Git event subjects. Migration `before_disposition_digest` and
`after_disposition_digest` bind the **inherited-disposition state**: begin with
one `INHERITED` disposition row per baseline file, then apply complete accepted
migration groups in sequence by marking every named source exactly once as
`MIGRATED`; an accepted `LEGACY_SOURCE` deletion instead marks its named source
`RETIRED`. Destination rows are event-time evidence and are not
copied into the disposition state. Unrelated canonical tests, later migrations,
and legitimate later ADR-0008 edits to a migrated canonical destination
therefore do not mutate an earlier transition subject.

The validator must derive every Git event subject independently, never trust a
record's row assertions:

1. `before_commit_sha1` and `after_commit_sha1` are full 40-character lowercase
   commit IDs available in the declared repository object database. A shallow
   or missing object is `UNKNOWN`, never a pass.
2. The after commit has exactly one parent and that parent is the before commit.
   The validated landed subject is the after commit or has the after commit as
   an ancestor. Before applying the event, the complete baseline ledger is
   reproduced from Git: every still-`INHERITED` source exists with immutable
   baseline bytes or the one exact causally landed active-exception bytes, and
   every already `MIGRATED` or `RETIRED` source is absent. A missing, extra,
   reverted, reintroduced, or wrong-state source fails before the named event is
   considered.
3. `landing_record_ref` resolves to a schema-valid `LandingRecord` with
   `status: SUCCEEDED`. Its `target_head_before` equals the before commit, its
   candidate and landed commits contain the after commit as an ancestor, and
   the candidate contains the byte-exact instance record at its canonical
   source path. A nonresolving, self-asserted, wrong-subject, squash-only, or
   noncausal landing reference fails. For every migration group after sequence
   1, the predecessor group's successful landed commit is an ancestor of the
   current group's before commit; a record-only predecessor ID cannot substitute
   for causal Git history. The authoritative UTC chronology is
   `evidence/check finish <= review/decision issue <= LandingRecord.started_at
   <= LandingRecord.finished_at <= validation_observed_at`; every artifact and
   decision is current and unexpired at the decision and landing. A change
   landing finishes before both its exception expiry and policy expiry. Every
   migration landing, whether sourced from baseline or an authorized change,
   finishes on or before policy expiry. Commit author/committer timestamps and
   record `recorded_at` are metadata and cannot replace these times.
4. For each commit, recursively enumerate the exact `tests` tree from Git, not
   the checkout. Reject a non-UTF-8 path; bytewise path-sort blob rows shaped
   `{path, mode, git_blob_oid_sha1, content_sha256}`; then compute the RFC 8785
   SHA-256 of
   `{kind: LEGACY_TEST_GIT_SNAPSHOT_SUBJECT_V1, commit_sha1,
   tests_tree_oid_sha1, rows}`. The result must equal the corresponding
   `*_tests_snapshot_digest`.
5. For a change exception, the before-tree row equals `baseline_row` and the
   immutable baseline row, while the same path's after-tree row equals
   `current_row`. For a migration, every `current_source_row` equals its
   before-tree blob/mode/content, the old path is absent from the after tree,
   and every destination row's path/mode/content equals the after-tree blob.
   The validator recomputes blob SHA-1 and content SHA-256 from Git bytes.
   It also computes the complete after-minus-before `tests` delta. A change
   event may modify only its one unchanged baseline path. A migration event may
   remove only the complete group's named source paths and add/modify only the
   bytewise union of its named destination paths; an unchanged existing shared
   destination is allowed but contributes no delta. Every delta row is
   `{path, operation: ADD|MODIFY|DELETE, before_row, after_row}` with nullable
   rows containing mode, Git blob OID, and content SHA-256. The RFC 8785 digest
   of the bytewise path-sorted rows must equal
   `tests_delta_manifest_digest`. Any unrelated test addition, deletion,
   modification, disposed-path reintroduction, or omitted group operation
   fails even if a later commit restores the final tree.
6. A migration source has exactly one authorized predecessor state:
   `IMMUTABLE_BASELINE` requires `current_source_row` to equal the baseline
   path/mode/content, all three `source_change_exception_*` fields to be null,
   and `closes_change_exception_id` to be null; no active exception for that
   path may exist in the before commit.
   `AUTHORIZED_CHANGE_EXCEPTION` requires nonnull
   `source_change_exception_id`,
   `source_change_exception_source_digest`, and
   `source_change_exception_exact_subject_digest`, with
   `closes_change_exception_id` exactly equal to the source exception ID. The
   migration before commit
   must contain exactly one direct, canonical, schema-valid active
   change-exception JSON record for that baseline path, at the filename derived
   from the named ID. Its exact file-byte digest, exact-subject digest,
   baseline/current rows, policy, scope, and owners must equal the migration
   chain; its successful landing must be an ancestor of the migration before
   commit. The migration landing must finish before both that exception's
   expiry and the row-policy expiry. Missing, ambiguous, expired, stale,
   noncausal, or digest-mismatched prior state fails. The accepted migration
   atomically derives that one referenced exception as `CLOSED`; an exception
   can be closed exactly once and cannot authorize any later event. The proof
   candidate adds the immutable migration record and does not edit or delete the
   exception record. A governed follow-up commit removes the now-closed record
   from the active source directory only after the migration lands; immutable
   Git and landing evidence retain its original `ACTIVE` bytes and the closure
   chain. Before any subsequent validation, construction, landing, or release
   claim, that derived-closed source must be absent from the committed active
   source tree and `legacy-test-layout-records-v2.json`; retaining it is a dangling
   authority failure. The authoritative artifact/landing registry globally
   claims every change ID even after cleanup, so it can never be reused. A
   dangling active exception, wrong/multiple closure, reused ID/closure, or
   authorized-change migration without the exact closure fails.
7. Every migration record has `disposition: MIGRATED`, a nonempty destination
   set, and no independent retirement-rationale branch. A legacy behavior that
   is deliberately obsolete instead uses an accepted ADR-0008
   `TestDeletionRecordV1` with `target_kind: LEGACY_SOURCE`. That deletion
   independently binds the exact baseline/current authorized row, ledger state,
   causal removal delta, requirement/risk/no-gap disposition, cleanup, typed
   evidence and decisions, and its own successful landing. If the current row
   is authorized by a change exception, the deletion names and closes that
   exact exception under the same one-time digest/causality rules as migration;
   its active source is removed only in the governed follow-up cleanup before a
   later validation claim. It derives `RETIRED` without creating a temporary
   canonical test. A migration record cannot alias or substitute for this
   authority.
8. A migration destination is a regular `.py` file in an ADR-0008 canonical
   root. Its UTF-8 after-commit blob contains exactly one complete line
   `# ranex-test-id: <test_id>`, whose value byte-equals the row's `test_id`.
   Many-to-one members may share that identical destination row and marker.
   Each directory-exception source destination is below that row's exact
   `destination_root`. Each direct-top-level source additionally carries a
   governed behavior/context/capability/owner/lane classification whose
   resulting root is one of ADR-0008's 18 roots; a path-only guess or
   fixture-local label fails. Its closed `direct_source_classification` object
   is `{classification_id, classification_source_ref,
   classification_source_digest, behavior_id, context_id, capability_id,
   owner_id, test_lane, destination_root}`. The reference resolves exactly one
   canonical, byte-digested, separately landed
   `DirectSourceClassificationAuthorityV1` source. That authority binds the
   exact immutable top-level source row and scope, work item, versioned
   `TestBehaviorAuthorityV1`, six exact registry/catalog rows and digests,
   validity window, deterministic destination derivation, owner decision, and
   non-circular classification subject.

   The classification `HumanDecisionRecord` has `status: APPROVED`, outcome
   `ALLOW`, the exact `TEST_CLASSIFICATION_OWNER` role and
   `ALLOW_DIRECT_LEGACY_TEST_CLASSIFICATION` action, and its subject equals the
   derived classification-authority subject. Its `issued_at` is no earlier
   than the authority's `valid_from`; validation time is at or after
   `issued_at` and strictly before both authority and decision expiry;
   `revoked_at` is null; and no eligible conflicting or superseding behavior,
   classification, or decision exists. `destination_root` derives from the
   exact ADR-0008 taxonomy row: `CONTEXT` appends `context_id`,
   `CAPABILITY` appends `capability_id`, `OWNER` appends `owner_id`, and
   `EXACT_TEST_METADATA` appends the authority's nonnull
   `exact_test_metadata_segment`; that field is null for every other branch.
   The expanded root must satisfy one and only one declared taxonomy
   `mirror_pattern`, and every destination is strictly below it. The
   transition object and authority source mappings must byte-equal.

   The field is required and nonnull only for
   `LEGACY-TEST-TOPLEVEL-001`, and required null for every fixed
   directory/canonical scope. Both the real change-exception path and the real
   migration-member path must resolve the authority unconditionally before
   any destination or artifact check; an omitted resolver input is blocking
   `UNKNOWN`, never a fixture-only bypass.
   Later edits or canonical renames never rewrite the historical event row or
   commit.
9. Current marker state is derived, not frozen forever. A migrated test ID is
   `ACTIVE` when exactly one current regular canonical `.py` file carries its
   marker. Its marker may be absent only after an accepted canonical
   `TestDeletionRecordV1` with `target_kind: CANONICAL_TEST` transitions that
   exact ID to `RETIRED`. That record binds the complete introducing migration
   proof set where applicable, causal before/after Git snapshots and exact
   deletion/cleanup delta, requirement/risk disposition, typed artifacts and
   decisions, and either active successor IDs or a governed
   no-longer-required/applicable terminal. Retired IDs are globally nonreusable;
   successor edges are acyclic and recursively resolve to `ACTIVE` or a
   governed terminal. An absent/duplicate marker, direct unrecorded deletion,
   forged/missing disposition, cycle, or reused retired ID fails.
10. A sealing validation names one full `validation_commit_sha1`, loads
    `tests/`, all legacy-layout sources, all test-health retirement sources,
    and their projected registries from that commit's Git trees, and proves the
    validated commit descends every successful landing it relies on. Relevant
    staged, unstaged, or untracked checkout changes fail; a working-tree
    compiler run may produce a nonauthoritative candidate only. No `PASS`,
    landing, release, or cutover claim may mix committed test bytes with
    working-tree record bytes.

The event and its finalized record use one governed, commit-preserving landing
stack to avoid a self-referential commit hash: the event commit is the direct
child of the before commit; the next commit adds the finalized canonical record
that names the already-known event commits; and the preallocated
`landing_record_ref` binds the whole stack. Neither commit may land, verify, or
release independently. The record commit changes no `tests` bytes and adds only
the named canonical record set: one record for a change, every exact member for
a migration group, or the one cutover record. Squashing the stack or adding an
unmanifested record invalidates the event proof.

Cutover is a distinct zero-test-delta event after every inherited source has an
accepted `MIGRATED` or `RETIRED` disposition and every resulting test lineage
is valid. Its after commit is the direct child of its before commit and has the
identical complete `tests` tree; the following record commit adds only
`LEGACY-TEST-CUTOVER-001`. Its successful `LandingRecord` binds the canonical
cutover subject and candidate bytes. `accepted_at` is the latest required
authenticated owner-decision issue time, not `recorded_at`. Both
`accepted_at` and `LandingRecord.finished_at` must be on or before
2026-10-31T23:59:59Z.

The registry must reject an incomplete group, sequence gap, duplicate,
predecessor mismatch, replayed/unaccounted old path, incompatible shared
destination, forged row, wrong or missing commit, noncausal landing, test-ID
mismatch, or digest mismatch. Current validation requires the source
disposition/removal and destination lineage, not equality to historical
destination bytes. This makes sequential migrations and ordinary canonical TDD
evolution possible without rewriting earlier immutable proofs.

Many legacy sources may consolidate into one canonical test only inside one
atomic `migration_group_id`. Group members share sequence, predecessor,
causation, landing record, event commits, Git snapshots, disposition states, and
member count; member indexes are exactly contiguous
`1..group_member_count`. Identical destination rows are de-duplicated as the
group's canonical destination union. Reuse of one path with different `test_id`
values in the same group is a conflict. Every source is disposed exactly once;
a duplicate or omitted source blocks the group.

The following marked YAML is the sole field/type/cardinality/order catalog for
the legacy-test record family. A compiler must consume it rather than infer
fields from examples or prose. All declared fields are required as JSON keys;
nullable fields retain an explicit JSON `null`; all other scalar/object fields
have cardinality one. `additional_properties: false` is recursive.

ADR-0010 2.0 makes the authority change an explicit major boundary. Historical
v1 schemas remain immutable reference artifacts, but the active compiler and
validator accept only the V2 change, migration, and affected subject contracts.
The marked compatibility matrix is normative: it prohibits silent
reinterpretation, mixed-version groups, identity reuse, and partial generated
output on rejection.

<!-- BEGIN ADR10 LEGACY TEST RECORD CONTRACT -->

```yaml
legacy_test_record_contract:
  contract_id: "ADR10-LEGACY-TEST-RECORDS-2.0"
  contract_version: "2.0.0"
  canonicalization: "RFC8785"
  digest_algorithm: "SHA-256"
  digest_encoding: "sha256:<64 lowercase hex>"
  source_record_encoding: "UTF-8 canonical JSON with no BOM"
  additional_properties: false
  inherited_type_authority:
    source: "ADR-0008 canonical record catalog"
    types: ["TypedArtifactRefV1", "LegacyBaselineSourceRowV1", "LegacyCurrentSourceRowV1"]
  scalar_types:
    safe_id: "nonempty registered identifier with no path traversal"
    safe_id_or_registered_urn: "safe_id or registered urn:ranex identifier"
    safe_path: "normalized repository-relative UTF-8 path with no empty, dot, or dot-dot segment"
    sha1: "40 lowercase hexadecimal characters"
    sha256: "sha256:<64 lowercase hexadecimal characters>"
    hex_sha256: "64 lowercase hexadecimal characters with no algorithm prefix"
    semver: "SemVer 2.0.0"
    strict_utc: "RFC3339 UTC instant with Z and no leap second"
    git_mode: "100644"
    nonempty_string: "nonempty UTF-8 string"
    positive_integer: "integer >= 1"
    nonnegative_integer: "integer >= 0"
  cardinality_rule:
    undeclared_default: "FORBIDDEN"
    declared_nonnullable_scalar_or_object: "1"
    declared_nullable_scalar_or_object: "0..1 represented by an explicit value or JSON null"
    array: "the record-specific range; the JSON key is still required"
  set_order_rule: "Set-like arrays are duplicate-free and bytewise ordered by the declared key over UTF-8 bytes."

  compatibility_impact:
    predecessor_contract_id: "ADR10-LEGACY-TEST-RECORDS-1.0"
    predecessor_contract_version: "1.0.0"
    change_class: "BREAKING_MAJOR"
    admission_mode: "POLICY2_AND_V2_ONLY_FOR_ALL_ACTIVE_LEGACY_TRANSITIONS"
    active_projection_paths:
      policy: "architecture/contracts/legacy-test-layout-policy-v2.json"
      record_manifest: "architecture/contracts/legacy-test-layout-records-v2.json"
      policy_schema: "schemas/common/legacy-test-layout-policy-v2.schema.json"
      policy_schema_id: "legacy-test-layout-policy/v2"
      policy_id: "RANEX-LEGACY-TEST-LAYOUT-2.0"
      policy_version: "2.0.0"
      record_manifest_id_version: "REG-LEGACY-TEST-LAYOUT-RECORDS-001@2.0.0"
      rule: "Contract-2 consumers resolve only these explicit V2 paths. The unversioned policy/record-manifest paths are frozen byte-identical V1 compatibility aliases and are never current-authority pointers."
    live_v1_precondition:
      expected_active_change_record_count: 0
      expected_accepted_migration_record_count: 0
      expected_accepted_cutover_record_count: 0
      authority: "complete canonical source scan, immutable Git history, LandingRecord/artifact registries, and the byte-identical architecture/contracts/legacy-test-layout-records-v1.json plus frozen unversioned V1 alias"
      failure: "Any live or previously admitted v1 change, migration, or cutover record blocks the first v2 seal and requires a separately accepted migration ADR; it cannot be silently converted, ignored, or reauthored."
    breaking_bindings:
      - {old_id: "RANEX-LEGACY-TEST-LAYOUT-1.0@1.0.0", old_schema: "schemas/common/legacy-test-layout-policy-v1.schema.json", new_id: "RANEX-LEGACY-TEST-LAYOUT-2.0@2.0.0", new_schema: "schemas/common/legacy-test-layout-policy-v2.schema.json", impact: "The policy envelope embeds the changed record family, proof type, scope authority, and complete active ledgers; it is a breaking projection."}
      - {old_id: "REG-LEGACY-TEST-LAYOUT-RECORDS-001@1.0.0", old_schema: "architecture/contracts/legacy-test-layout-records-v1.json", new_id: "REG-LEGACY-TEST-LAYOUT-RECORDS-001@2.0.0", new_schema: "architecture/contracts/legacy-test-layout-records-v2.json", impact: "The manifest admits only policy2/V2 record identities and cannot be an unversioned current pointer."}
      - {old_id: "DirectSourceClassificationV1", old_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-1.0", new_id: "DirectSourceClassificationV2", new_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-2.0", impact: "The transition-local HumanDecision ref/digest shape is replaced by one separately landed canonical classification source ref/digest and repeated resolved mapping fields."}
      - {old_id: "LegacyTestChangeExceptionV1", old_schema: "schemas/common/legacy-test-change-exception-v1.schema.json", new_id: "LegacyTestChangeExceptionV2", new_schema: "schemas/common/legacy-test-change-exception-v2.schema.json", impact: "The embedded direct-source classification contract and its authority semantics are breaking."}
      - {old_id: "LegacyTestMigrationRecordV1", old_schema: "schemas/common/legacy-test-migration-record-v1.schema.json", new_id: "LegacyTestMigrationRecordV2", new_schema: "schemas/common/legacy-test-migration-record-v2.schema.json", impact: "The embedded classification contract, proof_type, member subject, and group-subject dependency are breaking."}
      - {old_id: "LegacyMemberManifestRowV1", old_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-1.0", new_id: "LegacyMemberManifestRowV2", new_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-2.0", impact: "exact_subject_digest now denotes only a V2 migration-member subject."}
      - {old_id: "LegacyOrderedMigrationSubsetRowV1", old_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-1.0", new_id: "LegacyOrderedMigrationSubsetRowV2", new_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-2.0", impact: "exact_subject_digest now denotes only a V2 member and drives the V2 cutover digest."}
      - {old_id: "LegacyTestScopeAuthorityRowV1", old_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-1.0", new_id: "LegacyTestScopeAuthorityRowV2", new_schema: "embedded closed nested type in ADR10-LEGACY-TEST-RECORDS-2.0", impact: "The exact policy identity and direct-top-level authority resolver are V2."}
      - {old_id: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V1", old_schema: "legacy-test-change-exception-subject/v1", new_id: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", new_schema: "legacy-test-change-exception-subject/v2", impact: "The projected direct_source_classification value has a different closed shape and authority meaning."}
      - {old_id: "LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V1", old_schema: "legacy-test-migration-member-subject/v1", new_id: "LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2", new_schema: "legacy-test-migration-member-subject/v2", impact: "The projected direct_source_classification value and member digest are breaking."}
      - {old_id: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V1", old_schema: "legacy-test-migration-transition-subject/v1", new_id: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", new_schema: "legacy-test-migration-transition-subject/v2", impact: "The group binds only V2 member subjects and a V2-derived member manifest."}
      - {old_id: "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-1.0", old_schema: "legacy-test-scope-authority-subject/v1", new_id: "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-2.0", new_schema: "legacy-test-scope-authority-subject/v2", impact: "Direct-top-level destination resolution now requires the separately landed DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0 chain instead of a transition-local decision."}
      - {old_id: "LegacyTestCutoverRemovalRecordV1", old_schema: "schemas/common/legacy-test-cutover-removal-record-v1.schema.json", new_id: "LegacyTestCutoverRemovalRecordV2", new_schema: "schemas/common/legacy-test-cutover-removal-record-v2.schema.json", impact: "The cutover exact subject binds policy2 and V2 migration member/subset semantics."}
      - {old_id: "LEGACY_TEST_CUTOVER_SUBJECT_V1", old_schema: "legacy-test-cutover-subject/v1", new_id: "LEGACY_TEST_CUTOVER_SUBJECT_V2", new_schema: "legacy-test-cutover-subject/v2", impact: "The whole-event subject binds policy2 and a pure-V2 closed transition ledger."}
    stable_v1_bindings:
      newly_introduced: ["ClassificationAuthorityBindingV1", "TestBehaviorAuthorityRowV1", "DirectSourceClassificationAuthorityRowV1", "TestBehaviorAuthorityV1", "DirectSourceClassificationAuthorityV1", "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1", "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1", "DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0"]
      version_neutral: ["TypedArtifactRefV1", "LegacyBaselineSourceRowV1", "LegacyCurrentSourceRowV1", "LegacyChangeRowV1", "LegacyDestinationRowV1", "LegacyRecordSourceManifestRowV1", "LegacyDispositionStateRowV1", "LegacyResultingTestRowV1", "LegacyTestLineageRowV1", "LegacyDeltaContentRowV1", "LegacyTestsDeltaRowV1", "LandingRecord", "TestDeletionRecordV1"]
      justification: "New authorities receive their first stable V1 identity but const-bind policy2 and can drive only V2 transitions. Version-neutral rows contain content/identity facts rather than a versioned subject meaning; every proof-like ID inside them is resolved contextually and exclusively to V2 under policy2. LandingRecord remains one read-only shared schema and binds the subject's exact schema/version."
    historical_artifact_authority:
      manifest_id: "ADR10-HISTORICAL-V1-ARTIFACTS-001"
      exact_artifact_count: 9
      owner_class: "ADR10_PREDECESSOR_CONTRACT_1_0"
      provenance_kind: "PROJECT_AUTHORED_ARCHITECTURE_TOOLING"
      licensing_classification: "RANEX_ORIGINAL"
      license_id: "LicenseRef-Ranex-Personal-Use-1.0"
      repository_inclusion: "PUBLIC_SAFE"
      manifest_digest_rule: "RFC8785 SHA-256 of manifest_id, the five shared ownership/provenance/licensing fields, and the nine rows in bytewise path order"
      writer_authority:
        canonical_writer: "NONE_IMMUTABLE_COMMITTED_INPUT"
        generator_role: "VERIFY_ONLY_NO_CREATE_UPDATE_DELETE_REFORMAT"
        tree_lock_class: "ADR10_IMMUTABLE_V1_INPUT"
        output_exclusion: "All nine paths are excluded from every generated-output writer/exact-output set and included in the immutable-input exact set. V2 schemas/projections/manifests use distinct paths and remain generator-owned outputs."
        change_rule: "No tool or human may modify these paths under contract 2.0. A change requires a new major contract and new path while retaining these exact bytes."
      rows:
        - {path: "architecture/contracts/legacy-test-layout-policy-v1.json", sha256: "sha256:e3aba0f4631f84c2a9baba9bbacfe7c29115b781cf1f45dc12c37e6f70fef421", artifact_class: "HISTORICAL_VERSIONED_PROJECTION", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "architecture/contracts/legacy-test-layout-policy-v2.json"}
        - {path: "architecture/contracts/legacy-test-layout-policy.json", sha256: "sha256:e3aba0f4631f84c2a9baba9bbacfe7c29115b781cf1f45dc12c37e6f70fef421", artifact_class: "HISTORICAL_UNVERSIONED_ALIAS", disposition: "READ_ONLY_V1_ALIAS", superseded_by: "architecture/contracts/legacy-test-layout-policy-v2.json"}
        - {path: "architecture/contracts/legacy-test-layout-records-v1.json", sha256: "sha256:9b94991b635995759dd8c8244f2d747701bc06c44d24de1e009bc137ad66b07b", artifact_class: "HISTORICAL_VERSIONED_MANIFEST", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "architecture/contracts/legacy-test-layout-records-v2.json"}
        - {path: "architecture/contracts/legacy-test-layout-records.json", sha256: "sha256:9b94991b635995759dd8c8244f2d747701bc06c44d24de1e009bc137ad66b07b", artifact_class: "HISTORICAL_UNVERSIONED_ALIAS", disposition: "READ_ONLY_V1_ALIAS", superseded_by: "architecture/contracts/legacy-test-layout-records-v2.json"}
        - {path: "schemas/common/legacy-test-change-exception-v1.schema.json", sha256: "sha256:3daadc7e930fa061e4cbf82f32e5aa5a7f2b8ca9a9b50b8b04cda446b813a0f9", artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-change-exception-v2.schema.json"}
        - {path: "schemas/common/legacy-test-cutover-removal-record-v1.schema.json", sha256: "sha256:1c93edb7478654660ff763bbc707ce13871c3c34b0beaebe14fe7730ead67a05", artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-cutover-removal-record-v2.schema.json"}
        - {path: "schemas/common/legacy-test-layout-policy-v1.schema.json", sha256: "sha256:11b6222ddcb8aef7b8958136876dd2f28cc8c1e487d4d2a67355c30a33f07be8", artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-layout-policy-v2.schema.json"}
        - {path: "schemas/common/legacy-test-migration-record-v1.schema.json", sha256: "sha256:d0c1fef4a913cf0877b8750fcf87a495d7f8feb919d8138daf0a8d32c186d61a", artifact_class: "HISTORICAL_SCHEMA", disposition: "READ_ONLY_SUPERSEDED", superseded_by: "schemas/common/legacy-test-migration-record-v2.schema.json"}
        - {path: "schemas/execution/landing-record-v1.schema.json", sha256: "sha256:9c0be4ac04542b9cd26561d06f4b3d401e84c4acbf3e855f628a67d3e58a070e", artifact_class: "SHARED_ACTIVE_SCHEMA", disposition: "READ_ONLY_SHARED_ACTIVE", superseded_by: null}
      verification_policy:
        - "All nine paths are committed repository inputs. A fresh checkout verifies the exact set, bytes, SHA-256, owner class, provenance, licensing, disposition, and superseded_by values without network or mutable-cache input."
        - "The generator never rewrites, deletes, reformats, or derives historical bytes from current V2 semantics. It builds V2 outputs in isolation and compares all historical bytes before and after atomic publication."
        - "The two unversioned paths remain byte-identical to their explicit V1 copies. V2 code, evidence, registries, and sealing consume only explicit V2 paths; an unversioned lookup is blocking UNKNOWN."
        - "Every row has an exact matching legal/licensing-manifest entry; a missing, duplicate, broader, wrong-owner, wrong-provenance, wrong-license, or release-unsafe classification blocks generation."
    v1_rejection_policy:
      migration_mode: "NO_AUTOMATIC_MIGRATION_FAIL_CLOSED"
      historical_schema_policy: "Only the exact historical_artifact_authority set is retained; it remains byte-bound to ADR10-LEGACY-TEST-RECORDS-1.0 and cannot be overwritten, deleted, silently regenerated, or interpreted as policy2."
      active_source_policy: "A policy1 projection, schema_version 1 change/cutover record, schema_version/proof_type v1 migration record, v1 changed-family subject, or any mixed-major ledger/group is ineligible before projection, artifact resolution, registry mutation, or authority evaluation."
      new_authority_policy: "The first-stable V1 behavior/classification authority records require policy_id RANEX-LEGACY-TEST-LAYOUT-2.0 and policy_version 2.0.0 wherever applicable and may authorize only policy2/V2 transition subjects."
      identity_policy: "No v1 policy, record, subject, decision, landing, proof, group, subset, or cutover ID may be relabeled or reused as V2. Because the live v1 population must be zero, work is authored as a fresh policy2/V2 event with fresh globally nonreusable IDs and the complete V2 authority/evidence stack."
      test_deletion_v1_policy: "TestDeletionRecordV1 remains version-neutral only at the outer record type. For target_kind LEGACY_SOURCE under ADR-0010 policy2, every source_migration_proof_ids value resolves exactly one accepted LegacyTestMigrationRecordV2 and LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2; a V1, mixed, dangling, reused, or policy1 proof ID fails."
      transactional_policy: "Compatibility detection is read-only and precedes generated-output publication. Compilation writes to an isolated candidate set and atomically publishes only after complete success; rejection leaves every prior artifact byte-identical and emits no registry, manifest, subject, or landing row."
      idempotency_policy: "Repeating validation of identical incompatible bytes returns the same stable rejection code and diagnostics digest and performs zero writes."
      rollback_policy: "No state rollback is needed for preflight rejection because no mutation occurred. Discovery after candidate generation discards the isolated candidate set; any already published incompatible state is a blocking incident requiring a separately governed rollback/migration event."
    fixture_requirements:
      positive:
        - {case_id: "ADR10-COMPAT-V2-POS-001", proves: "A pure LegacyTestChangeExceptionV2 with DirectSourceClassificationV2 and the complete new V1 authority chain is accepted."}
        - {case_id: "ADR10-COMPAT-V2-POS-002", proves: "A pure LegacyTestMigrationRecordV2 group derives only V2 member/group subjects and is accepted atomically."}
        - {case_id: "ADR10-COMPAT-V2-POS-003", proves: "LegacyTestCutoverRemovalRecordV2 and LEGACY_TEST_CUTOVER_SUBJECT_V2 close a pure-policy2/V2 transition ledger."}
        - {case_id: "ADR10-COMPAT-V2-POS-004", proves: "A TestDeletionRecordV1 LEGACY_SOURCE branch resolves every migration proof exclusively to accepted policy2/V2 members."}
        - {case_id: "ADR10-COMPAT-V2-POS-005", proves: "A fresh checkout verifies all nine retained V1 artifacts, emits explicit V2 outputs, and leaves every historical byte unchanged."}
      negative:
        - {case_id: "ADR10-COMPAT-V2-NEG-001", proves: "A v1 change source is rejected before projection and produces no V2 artifact."}
        - {case_id: "ADR10-COMPAT-V2-NEG-002", proves: "A v1 migration source/proof is rejected before member-manifest or group-subject derivation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-003", proves: "A mixed v1/v2 migration group is rejected atomically with no accepted member."}
        - {case_id: "ADR10-COMPAT-V2-NEG-004", proves: "The old transition-local DirectSourceClassificationV1 shape is rejected inside either V2 record."}
        - {case_id: "ADR10-COMPAT-V2-NEG-005", proves: "V2-shaped bytes labeled with schema_version 1, proof_type V1, or a v1 type/subject schema are rejected without reinterpretation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-006", proves: "A v1 transition subject cannot satisfy any V2 artifact, LandingRecord, manifest, or resolver role."}
        - {case_id: "ADR10-COMPAT-V2-NEG-007", proves: "Two runs over identical incompatible v1 bytes return one stable rejection code/diagnostics digest and identical zero-write state."}
        - {case_id: "ADR10-COMPAT-V2-NEG-008", proves: "Late incompatible-v1 discovery discards the isolated candidate output and leaves all prior schemas, registries, and manifests byte-identical."}
        - {case_id: "ADR10-COMPAT-V2-NEG-009", proves: "Relabeling or reusing a v1 record/subject/proof/group/landing identity as V2 is rejected."}
        - {case_id: "ADR10-COMPAT-V2-NEG-010", proves: "A policy1 projection or V1 record manifest cannot be consumed through an unversioned path as current policy2 authority."}
        - {case_id: "ADR10-COMPAT-V2-NEG-011", proves: "A V1 cutover record/subject cannot close a policy2/V2 ledger."}
        - {case_id: "ADR10-COMPAT-V2-NEG-012", proves: "Any policy1 identifier inside a V2 authority, transition, subset, cutover, resolver, LandingRecord, or sealing binding rejects the complete candidate."}
        - {case_id: "ADR10-COMPAT-V2-NEG-013", proves: "A TestDeletionRecordV1 LEGACY_SOURCE branch containing a V1, mixed, reused, dangling, or policy1 migration-proof ID is rejected."}
        - {case_id: "ADR10-COMPAT-V2-NEG-014", proves: "A missing retained-V1 artifact fails the exact historical set before V2 generation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-015", proves: "A byte-mutated retained-V1 artifact fails its bound SHA-256 before V2 generation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-016", proves: "An attempted overwrite, reformat, or deletion of retained V1 bytes aborts atomic publication and restores the unchanged prior tree."}
        - {case_id: "ADR10-COMPAT-V2-NEG-017", proves: "An orphan, duplicate, extra, or wrong-path historical artifact fails exact-set reconciliation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-018", proves: "A wrong or missing owner, provenance, license, disposition, or superseded_by legal-manifest binding blocks generation."}
        - {case_id: "ADR10-COMPAT-V2-NEG-019", proves: "Fresh generation with unavailable, mutable-cache-derived, or nondeterministic predecessor bytes fails rather than reconstructing approximate V1 artifacts."}
        - {case_id: "ADR10-COMPAT-V2-NEG-020", proves: "Any generated-writer claim or create/update/delete/reformat attempt against an immutable V1 input fails writer and tree-lock reconciliation."}
      exact_positive_case_count: 5
      exact_negative_case_count: 20

  nested_types:
    - type_id: "LegacyChangeRowV1"
      additional_properties: false
      fields: ["path", "mode", "content_sha256"]
      field_types: {path: "safe_path", mode: "git_mode", content_sha256: "hex_sha256"}
      nullable_fields: []
      array_cardinalities: {}
      order: "NOT_APPLICABLE"

    - type_id: "LegacyDestinationRowV1"
      additional_properties: false
      fields: ["path", "mode", "content_sha256", "test_id"]
      field_types: {path: "safe_path", mode: "git_mode", content_sha256: "hex_sha256", test_id: "safe_id"}
      nullable_fields: []
      array_cardinalities: {}
      order: "NOT_APPLICABLE"

    - type_id: "ClassificationAuthorityBindingV1"
      additional_properties: false
      fields: ["authority_role", "registry_id", "registry_version", "registry_ref", "registry_digest", "row_ref", "row_digest"]
      field_types:
        authority_role: {enum: ["BEHAVIOR", "CONTEXT", "CAPABILITY", "OWNERSHIP", "TEST_LANE", "DESTINATION_ROOT"]}
        registry_id: "safe_id"
        registry_version: "semver"
        registry_ref: "safe_path"
        registry_digest: "sha256"
        row_ref: "nonempty_string"
        row_digest: "sha256"
      nullable_fields: []
      array_cardinalities: {}
      row_order: "ENUM_ORDER_BEHAVIOR_CONTEXT_CAPABILITY_OWNERSHIP_TEST_LANE_DESTINATION_ROOT"
      invariants:
        - "registry_ref/version/digest bind one immutable accepted catalog snapshot at classification decision time; row_digest is the RFC8785 SHA-256 of the one resolved row."
        - "A mutable name, fixture-local map, missing row, duplicate role, unknown version, or whole-registry digest without the exact row digest is ineligible."

    - type_id: "DirectSourceClassificationV2"
      additional_properties: false
      fields: ["classification_id", "classification_source_ref", "classification_source_digest", "behavior_id", "context_id", "capability_id", "owner_id", "test_lane", "destination_root"]
      field_types:
        classification_id: "safe_id"
        classification_source_ref: "safe_path"
        classification_source_digest: "sha256"
        behavior_id: "safe_id"
        context_id: "safe_id"
        capability_id: "safe_id"
        owner_id: "safe_id"
        test_lane: "safe_id"
        destination_root: "safe_path"
      nullable_fields: []
      array_cardinalities: {}
      invariants:
        - "classification_source_ref is the canonical direct-source-classifications path derived from classification_id and classification_source_digest is the exact SHA-256 of those finalized source bytes."
        - "Every repeated mapping field byte-equals the resolved active DirectSourceClassificationAuthorityV1."

    - type_id: "TestBehaviorAuthorityRowV1"
      additional_properties: false
      fields: ["behavior_id", "behavior_version", "behavior_subject_schema", "behavior_subject_ref", "behavior_subject_digest", "owner_context_id", "capability_id", "definition_source_ref", "definition_source_digest", "valid_from", "expires_at", "supersedes_behavior_ref", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "status", "source_path", "source_digest"]
      field_types:
        behavior_id: "safe_id"
        behavior_version: "semver"
        behavior_subject_schema: "nonempty_string"
        behavior_subject_ref: "safe_id_or_registered_urn"
        behavior_subject_digest: "sha256"
        owner_context_id: "safe_id"
        capability_id: "safe_id"
        definition_source_ref: "safe_id_or_registered_urn"
        definition_source_digest: "sha256"
        valid_from: "strict_utc"
        expires_at: "strict_utc"
        supersedes_behavior_ref: "safe_id_or_registered_urn|null"
        landing_record_ref: "safe_id"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        status: {enum: ["PROPOSED", "ACTIVE", "REJECTED"]}
        source_path: "safe_path"
        source_digest: "sha256"
      nullable_fields: ["supersedes_behavior_ref", "accepted_at"]
      array_cardinalities: {}
      row_order: "BYTEWISE_BEHAVIOR_ID_THEN_SEMVER"
      invariants:
        - "ACTIVE requires an eligible owner decision and successful LandingRecord in its canonical source; valid_from < expires_at; behavior ID/version and subject identities are globally nonreusable."
        - "Exactly one current ACTIVE highest-version row may resolve per behavior_id; a superseded, expired, revoked, rejected, conflicting, source-drifted, or unlanded row is ineligible."
        - "source_path is derived from behavior_id/version and source_digest is SHA-256 of exact finalized source bytes; the catalog is a complete source bijection across PROPOSED, ACTIVE, and REJECTED rows, but only ACTIVE with nonnull accepted_at can authorize."

    - type_id: "DirectSourceClassificationAuthorityRowV1"
      additional_properties: false
      fields: ["classification_id", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "affected_scope_id", "baseline_source_row", "behavior_id", "behavior_version", "context_id", "capability_id", "owner_id", "test_lane", "exact_test_metadata_segment", "destination_root", "work_item_id", "authority_bindings", "valid_from", "expires_at", "supersedes_classification_id", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "status", "source_path", "source_digest"]
      field_types:
        classification_id: "safe_id"
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        affected_scope_id: {const: "LEGACY-TEST-TOPLEVEL-001"}
        baseline_source_row: "LegacyChangeRowV1"
        behavior_id: "safe_id"
        behavior_version: "semver"
        context_id: "safe_id"
        capability_id: "safe_id"
        owner_id: "safe_id"
        test_lane: "safe_id"
        exact_test_metadata_segment: "safe_id|null"
        destination_root: "safe_path"
        work_item_id: "safe_id"
        authority_bindings: "ClassificationAuthorityBindingV1[]"
        valid_from: "strict_utc"
        expires_at: "strict_utc"
        supersedes_classification_id: "safe_id|null"
        landing_record_ref: "safe_id"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        status: {enum: ["PROPOSED", "ACTIVE", "REJECTED"]}
        source_path: "safe_path"
        source_digest: "sha256"
      nullable_fields: ["exact_test_metadata_segment", "supersedes_classification_id", "accepted_at"]
      array_cardinalities: {authority_bindings: "exactly 6"}
      array_order: {authority_bindings: "ENUM_ORDER_BEHAVIOR_CONTEXT_CAPABILITY_OWNERSHIP_TEST_LANE_DESTINATION_ROOT"}
      row_order: "BYTEWISE_CLASSIFICATION_ID"
      invariants:
        - "source_path is the canonical path derived from classification_id and source_digest is SHA-256 of the exact finalized source bytes; neither field exists inside those source bytes."
        - "The catalog is a complete bijection over every canonical DirectSourceClassificationAuthorityV1 source in every lifecycle state; only an ACTIVE row with nonnull accepted_at can grant authority."

    - type_id: "LegacyMemberManifestRowV2"
      additional_properties: false
      fields: ["group_member_index", "proof_id", "exact_subject_ref", "exact_subject_digest", "source_path"]
      field_types: {group_member_index: "positive_integer", proof_id: "safe_id", exact_subject_ref: "safe_id_or_registered_urn", exact_subject_digest: "sha256", source_path: "safe_path"}
      nullable_fields: []
      array_cardinalities: {}
      order: "NUMERIC_GROUP_MEMBER_INDEX_THEN_BYTEWISE_PROOF_ID"
      invariants:
        - "The row contains stable V2 member-subject facts only; exact_subject_ref/digest resolve LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2 for proof_id and source_path resolves its LegacyTestMigrationRecordV2; finalized record source_digest is prohibited."

    - type_id: "LegacyTestScopeAuthorityRowV2"
      additional_properties: false
      fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "affected_scope_id", "scope_kind", "source_match_kind", "source_root", "source_population_digest", "destination_rule_kind", "destination_root", "compatibility_owner", "migration_owner", "test_governance_owner", "expires_at"]
      field_types:
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        affected_scope_id: "safe_id"
        scope_kind: {enum: ["DIRECTORY_EXCEPTION", "DIRECT_TOP_LEVEL", "INHERITED_CANONICAL"]}
        source_match_kind: {enum: ["EXACT_BASELINE_SUBTREE", "EXACT_DIRECT_BASELINE_FILE", "EXACT_INHERITED_CANONICAL_BASELINE"]}
        source_root: "safe_path"
        source_population_digest: "sha256"
        destination_rule_kind: {enum: ["FIXED_CANONICAL_ROOT", "CLASSIFICATION_DECISION"]}
        destination_root: "safe_path|null"
        compatibility_owner: {const: "compatibility"}
        migration_owner: {const: "migration"}
        test_governance_owner: {const: "process_assurance"}
        expires_at: "strict_utc"
      nullable_fields: ["destination_root"]
      array_cardinalities: {}
      invariants:
        - "DIRECT_TOP_LEVEL requires CLASSIFICATION_DECISION and null destination_root; every other scope requires FIXED_CANONICAL_ROOT and one ADR-0008 canonical destination_root."
        - "source_population_digest is the RFC8785 SHA-256 of every and only immutable baseline row selected by source_match_kind/source_root in bytewise path order."

    - type_id: "LegacyRecordSourceManifestRowV1"
      additional_properties: false
      fields: ["record_id", "source_path", "source_digest"]
      field_types: {record_id: "safe_id", source_path: "safe_path", source_digest: "sha256"}
      nullable_fields: []
      array_cardinalities: {}
      order: "BYTEWISE_SOURCE_PATH"
      purpose: "LandingRecord.subject_manifest_digest only; never an exact transition subject. record_id is version-neutral syntax whose containing policy2/V2 subject determines and verifies the exact V2 record type."

    - type_id: "LegacyDispositionStateRowV1"
      additional_properties: false
      fields: ["old_path", "old_content_sha256", "disposition", "migration_group_id", "proof_id", "deletion_id", "destination_test_ids"]
      field_types:
        old_path: "safe_path"
        old_content_sha256: "hex_sha256"
        disposition: {enum: ["INHERITED", "MIGRATED", "RETIRED"]}
        migration_group_id: "safe_id|null"
        proof_id: "safe_id|null"
        deletion_id: "safe_id|null"
        destination_test_ids: "safe_id[]"
      nullable_fields: ["migration_group_id", "proof_id", "deletion_id"]
      array_cardinalities: {destination_test_ids: "0..N"}
      array_order: {destination_test_ids: "BYTEWISE_SAFE_ID"}
      row_order: "BYTEWISE_OLD_PATH"
      invariants:
        - "proof_id is a version-neutral identifier slot; under policy2 every nonnull proof_id resolves exactly one accepted LegacyTestMigrationRecordV2 and LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2. V1, mixed-major, dangling, or reused proof IDs fail."

    - type_id: "LegacyResultingTestRowV1"
      additional_properties: false
      fields: ["path", "mode", "content_sha256"]
      field_types: {path: "safe_path", mode: "git_mode", content_sha256: "hex_sha256"}
      nullable_fields: []
      array_cardinalities: {}
      row_order: "BYTEWISE_PATH"

    - type_id: "LegacyOrderedMigrationSubsetRowV2"
      additional_properties: false
      fields: ["migration_group_id", "transition_sequence", "predecessor_transition_id", "group_member_index", "proof_id", "exact_subject_digest"]
      field_types: {migration_group_id: "safe_id", transition_sequence: "positive_integer", predecessor_transition_id: "safe_id", group_member_index: "positive_integer", proof_id: "safe_id", exact_subject_digest: "sha256"}
      nullable_fields: []
      array_cardinalities: {}
      row_order: "NUMERIC_TRANSITION_SEQUENCE_THEN_NUMERIC_GROUP_MEMBER_INDEX_THEN_BYTEWISE_PROOF_ID"
      invariants:
        - "proof_id and exact_subject_digest resolve one accepted LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2 whose group, transition sequence, predecessor, and member index equal this row; no V1 or mixed-major member is eligible."

    - type_id: "LegacyTestLineageRowV1"
      additional_properties: false
      fields: ["test_id", "state", "current_row", "introducing_migration_proof_ids", "retirement_deletion_id", "retirement_exact_subject_digest", "successor_test_ids", "terminal_kind"]
      field_types:
        test_id: "safe_id"
        state: {enum: ["ACTIVE", "RETIRED"]}
        current_row: "LegacyResultingTestRowV1|null"
        introducing_migration_proof_ids: "safe_id[]"
        retirement_deletion_id: "safe_id|null"
        retirement_exact_subject_digest: "sha256|null"
        successor_test_ids: "safe_id[]"
        terminal_kind: {enum: ["ACTIVE", "SUCCESSORS", "NO_LONGER_REQUIRED", "NO_LONGER_APPLICABLE"]}
      nullable_fields: ["current_row", "retirement_deletion_id", "retirement_exact_subject_digest"]
      array_cardinalities: {introducing_migration_proof_ids: "1..N", successor_test_ids: "0..N"}
      array_order: {introducing_migration_proof_ids: "BYTEWISE_PROOF_ID", successor_test_ids: "BYTEWISE_TEST_ID"}
      row_order: "BYTEWISE_TEST_ID"
      invariants:
        - "ACTIVE requires one event-time current_row with exactly one matching marker, null retirement fields, empty successor_test_ids, and terminal_kind ACTIVE."
        - "RETIRED requires null current_row, one accepted TestDeletionRecordV1 ID/exact-subject digest, and either nonempty successor_test_ids with terminal_kind SUCCESSORS or an empty successor set with a governed NO_LONGER_REQUIRED or NO_LONGER_APPLICABLE terminal."
        - "introducing_migration_proof_ids are version-neutral identifier slots; under policy2 each resolves only an accepted LegacyTestMigrationRecordV2/V2 member subject, while a V1, mixed-major, dangling, or reused proof ID fails."
        - "Every successor ID has exactly one row; edges are acyclic; every recursive path terminates ACTIVE or at a governed no-longer terminal; retired IDs are globally nonreusable."

    - type_id: "LegacyDeltaContentRowV1"
      additional_properties: false
      fields: ["mode", "git_blob_oid_sha1", "content_sha256"]
      field_types: {mode: "git_mode", git_blob_oid_sha1: "sha1", content_sha256: "hex_sha256"}
      nullable_fields: []
      array_cardinalities: {}

    - type_id: "LegacyTestsDeltaRowV1"
      additional_properties: false
      fields: ["path", "operation", "before_row", "after_row"]
      field_types:
        path: "safe_path"
        operation: {enum: ["ADD", "MODIFY", "DELETE"]}
        before_row: "LegacyDeltaContentRowV1|null"
        after_row: "LegacyDeltaContentRowV1|null"
      nullable_fields: ["before_row", "after_row"]
      array_cardinalities: {}
      row_order: "BYTEWISE_PATH"
      invariants:
        - "ADD has null before_row and nonnull after_row; MODIFY has both; DELETE has nonnull before_row and null after_row."

  record_catalog:
    - type_id: "TestBehaviorAuthorityV1"
      type_version: "1.0.0"
      source_pattern: "architecture/records/test-governance/behavior-authorities/<behavior_id>@<behavior_version>.json"
      schema_ref: "schemas/common/test-behavior-authority-v1.schema.json"
      registry_ref: "architecture/contracts/test-behaviors.json"
      registry_id: "REG-TEST-BEHAVIORS-001"
      additional_properties: false
      fields: ["schema_version", "record_type", "behavior_id", "behavior_version", "behavior_subject_schema", "behavior_subject_ref", "behavior_subject_digest", "owner_context_id", "capability_id", "definition_source_ref", "definition_source_digest", "work_item_id", "owner_decision_ref", "owner_decision_digest", "landing_record_ref", "valid_from", "expires_at", "supersedes_behavior_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]
      field_types:
        schema_version: {const: "1"}
        record_type: {const: "TEST_BEHAVIOR_AUTHORITY"}
        behavior_id: "safe_id"
        behavior_version: "semver"
        behavior_subject_schema: "nonempty_string"
        behavior_subject_ref: "safe_id_or_registered_urn"
        behavior_subject_digest: "sha256"
        owner_context_id: "safe_id"
        capability_id: "safe_id"
        definition_source_ref: "safe_id_or_registered_urn"
        definition_source_digest: "sha256"
        work_item_id: "safe_id"
        owner_decision_ref: "TypedArtifactRefV1|null"
        owner_decision_digest: "sha256|null"
        landing_record_ref: "safe_id"
        valid_from: "strict_utc"
        expires_at: "strict_utc"
        supersedes_behavior_ref: "safe_id_or_registered_urn|null"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        recorded_at: "strict_utc"
        status: {enum: ["PROPOSED", "ACTIVE", "REJECTED"]}
      nullable_fields: ["owner_decision_ref", "owner_decision_digest", "supersedes_behavior_ref", "accepted_at"]
      array_cardinalities: {}
      invariants:
        - "filename equals <behavior_id>@<behavior_version>.json; the catalog projection is a bijection over exact canonical sources and TestBehaviorAuthorityRowV1 source_digest is independently recomputed."
        - "exact subject is TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1; it excludes decision, landing, accepted_at, recorded_at, status, exact-subject fields, and finalized source digest."
        - "owner_decision_ref and owner_decision_digest are both null or both nonnull; when nonnull, owner_decision_ref.artifact_type is human_decision and owner_decision_digest exactly equals owner_decision_ref.artifact_digest."
        - "ACTIVE requires CURRENT exact definition/context/capability bindings, nonnull APPROVED/ALLOW TEST_BEHAVIOR_OWNER decision for REGISTER_TEST_BEHAVIOR, a successful separately sealed LandingRecord, nonnull accepted_at, valid_from <= decision.issued_at <= accepted_at < expires_at, null revocation, and no conflicting or superseding active behavior row."
        - "PROPOSED has null decision/digest and accepted_at; REJECTED grants no authority."

    - type_id: "DirectSourceClassificationAuthorityV1"
      type_version: "1.0.0"
      source_pattern: "architecture/records/legacy-test-layout/direct-source-classifications/<classification_id>.json"
      schema_ref: "schemas/common/direct-source-classification-authority-v1.schema.json"
      registry_ref: "architecture/contracts/legacy-test-direct-source-classifications.json"
      registry_id: "REG-LEGACY-TEST-DIRECT-SOURCE-CLASSIFICATIONS-001"
      additional_properties: false
      fields: ["schema_version", "record_type", "classification_id", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "affected_scope_id", "baseline_source_row", "behavior_id", "behavior_version", "context_id", "capability_id", "owner_id", "test_lane", "exact_test_metadata_segment", "destination_root", "work_item_id", "authority_bindings", "valid_from", "expires_at", "supersedes_classification_id", "classification_decision_ref", "classification_decision_digest", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]
      field_types:
        schema_version: {const: "1"}
        record_type: {const: "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY"}
        classification_id: "safe_id"
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        affected_scope_id: {const: "LEGACY-TEST-TOPLEVEL-001"}
        baseline_source_row: "LegacyChangeRowV1"
        behavior_id: "safe_id"
        behavior_version: "semver"
        context_id: "safe_id"
        capability_id: "safe_id"
        owner_id: "safe_id"
        test_lane: "safe_id"
        exact_test_metadata_segment: "safe_id|null"
        destination_root: "safe_path"
        work_item_id: "safe_id"
        authority_bindings: "ClassificationAuthorityBindingV1[]"
        valid_from: "strict_utc"
        expires_at: "strict_utc"
        supersedes_classification_id: "safe_id|null"
        classification_decision_ref: "TypedArtifactRefV1|null"
        classification_decision_digest: "sha256|null"
        landing_record_ref: "safe_id"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        recorded_at: "strict_utc"
        status: {enum: ["PROPOSED", "ACTIVE", "REJECTED"]}
      nullable_fields: ["exact_test_metadata_segment", "supersedes_classification_id", "classification_decision_ref", "classification_decision_digest", "accepted_at"]
      array_cardinalities: {authority_bindings: "exactly 6"}
      array_order: {authority_bindings: "ENUM_ORDER_BEHAVIOR_CONTEXT_CAPABILITY_OWNERSHIP_TEST_LANE_DESTINATION_ROOT"}
      invariants:
        - "filename equals classification_id; baseline_source_row is exactly one immutable direct-top-level baseline row and no classification source may bind a directory or inherited-canonical scope."
        - "authority_bindings contains exactly one current exact BEHAVIOR, CONTEXT, CAPABILITY, OWNERSHIP, TEST_LANE, and DESTINATION_ROOT row; every registry ID/version/ref/digest and row ref/digest independently resolves."
        - "behavior row version/subject/source is ACTIVE and current; context, capability, owner, lane, and root rows are mutually compatible; destination_root is derived by the exact ADR-0008 taxonomy branch and satisfies one expanded mirror pattern."
        - "valid_from < expires_at <= 2026-10-31T23:59:59Z and the selected behavior authority is valid for the classification's complete validity interval."
        - "exact subject is DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1; it excludes decision, landing, accepted_at, recorded_at, status, exact-subject fields, and finalized source digest."
        - "classification_decision_ref and classification_decision_digest are both null or both nonnull; when nonnull, classification_decision_ref.artifact_type is human_decision and classification_decision_digest exactly equals classification_decision_ref.artifact_digest."
        - "ACTIVE requires nonnull APPROVED/ALLOW TEST_CLASSIFICATION_OWNER decision for ALLOW_DIRECT_LEGACY_TEST_CLASSIFICATION, a successful separately sealed LandingRecord, nonnull accepted_at, valid_from <= decision.issued_at <= accepted_at < expires_at, evaluation before both authority and decision expiry, null revocation, and no conflicting or superseding active classification or decision."
        - "PROPOSED has null decision/digest and accepted_at; REJECTED grants no authority."

    - type_id: "LegacyTestChangeExceptionV2"
      type_version: "2.0.0"
      source_pattern: "architecture/records/legacy-test-layout/change-exceptions/<change_exception_id>.json"
      schema_ref: "schemas/common/legacy-test-change-exception-v2.schema.json"
      additional_properties: false
      fields: ["schema_version", "record_type", "change_exception_id", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_row", "current_row", "rationale", "compatibility_owner", "migration_owner", "test_governance_owner", "expires_at", "canonical_destination", "direct_source_classification", "replacement_plan_ref", "new_ranex_behavior_forbidden", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest", "maintenance_evidence_snapshot_ref", "maintenance_checker_result_refs", "change_gate_evaluation_ref", "change_owner_acceptance_ref", "independent_migration_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]
      field_types:
        schema_version: {const: "2"}
        record_type: {const: "LEGACY_TEST_CHANGE_EXCEPTION"}
        change_exception_id: "safe_id"
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        test_practice_profile_id: "safe_id"
        test_practice_profile_version: "semver"
        test_practice_profile_digest: "sha256"
        profile_freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
        transition_sequence: "positive_integer"
        predecessor_transition_id: "safe_id"
        causation_ref: "safe_id_or_registered_urn"
        landing_record_ref: "safe_id"
        affected_scope_id: "safe_id"
        baseline_row: "LegacyChangeRowV1"
        current_row: "LegacyChangeRowV1"
        rationale: "nonempty_string"
        compatibility_owner: {const: "compatibility"}
        migration_owner: {const: "migration"}
        test_governance_owner: {const: "process_assurance"}
        expires_at: "strict_utc"
        canonical_destination: "safe_path"
        direct_source_classification: "DirectSourceClassificationV2|null"
        replacement_plan_ref: "safe_id_or_registered_urn"
        new_ranex_behavior_forbidden: {const: true}
        before_commit_sha1: "sha1"
        after_commit_sha1: "sha1"
        before_tests_tree_oid_sha1: "sha1"
        after_tests_tree_oid_sha1: "sha1"
        before_tests_snapshot_digest: "sha256"
        after_tests_snapshot_digest: "sha256"
        tests_delta_manifest_digest: "sha256"
        maintenance_evidence_snapshot_ref: "TypedArtifactRefV1|null"
        maintenance_checker_result_refs: "TypedArtifactRefV1[]"
        change_gate_evaluation_ref: "TypedArtifactRefV1|null"
        change_owner_acceptance_ref: "TypedArtifactRefV1|null"
        independent_migration_review_ref: "TypedArtifactRefV1|null"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        recorded_at: "strict_utc"
        result: {enum: ["PASS", "FAIL", "UNKNOWN"]}
        status: {enum: ["PROPOSED", "ACTIVE", "REJECTED"]}
      nullable_fields: ["direct_source_classification", "maintenance_evidence_snapshot_ref", "change_gate_evaluation_ref", "change_owner_acceptance_ref", "independent_migration_review_ref", "accepted_at"]
      array_cardinalities: {maintenance_checker_result_refs: "0..N; ACTIVE requires 1..N"}
      array_order: {maintenance_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"}
      invariants:
        - "filename ID equals change_exception_id; source bytes and registry digest are exact"
        - "baseline_file_manifest_sha256 equals the immutable baseline manifest; the profile triple resolves CURRENT and profile_freshness_status is recomputed, never trusted"
        - "transition_sequence == 1 and predecessor_transition_id == HERMES-TEST-BASELINE-001"
        - "after_commit_sha1 has exactly before_commit_sha1 as its sole parent; both tests tree OIDs, complete snapshots, and exact one-path MODIFY delta independently recompute from Git"
        - "baseline_row equals the immutable row and before-tree row; current_row uses the identical path and equals the after-tree row"
        - "direct_source_classification is nonnull exactly for LEGACY-TEST-TOPLEVEL-001 and null for every fixed-root directory/canonical scope"
        - "ACTIVE requires result PASS, nonnull accepted_at and all five common noncompensating artifact roles plus the direct-scope classification role when applicable, but authority additionally requires the separate successful LandingRecord role"
        - "PROPOSED has null accepted_at; REJECTED grants no authority and cannot carry result PASS"

    - type_id: "LegacyTestMigrationRecordV2"
      type_version: "2.0.0"
      source_pattern: "architecture/records/legacy-test-layout/migration-records/<proof_id>.json"
      schema_ref: "schemas/common/legacy-test-migration-record-v2.schema.json"
      additional_properties: false
      prohibited_fields: ["retirement_rationale"]
      fields: ["schema_version", "record_type", "proof_type", "proof_id", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "migration_group_id", "group_member_index", "group_member_count", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_source_row", "current_source_row", "source_state_kind", "source_change_exception_id", "source_change_exception_source_digest", "source_change_exception_exact_subject_digest", "closes_change_exception_id", "disposition", "destination_rows", "direct_source_classification", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_disposition_digest", "after_disposition_digest", "tests_delta_manifest_digest", "member_manifest_digest", "migration_transition_subject_ref", "migration_transition_subject_digest", "behavior_evidence_snapshot_ref", "built_artifact_evidence_snapshot_ref", "adr0008_checker_result_refs", "architecture_checker_result_refs", "destination_marker_checker_result_refs", "residual_reference_checker_result_refs", "migration_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_migration_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]
      field_types:
        schema_version: {const: "2"}
        record_type: {const: "LEGACY_TEST_MIGRATION_RECORD"}
        proof_type: {const: "LEGACY_TEST_MIGRATION_PROOF_V2"}
        proof_id: "safe_id"
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        test_practice_profile_id: "safe_id"
        test_practice_profile_version: "semver"
        test_practice_profile_digest: "sha256"
        profile_freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
        migration_group_id: "safe_id"
        group_member_index: "positive_integer"
        group_member_count: "positive_integer"
        transition_sequence: "positive_integer"
        predecessor_transition_id: "safe_id"
        causation_ref: "safe_id_or_registered_urn"
        landing_record_ref: "safe_id"
        affected_scope_id: "safe_id"
        baseline_source_row: "LegacyBaselineSourceRowV1"
        current_source_row: "LegacyCurrentSourceRowV1"
        source_state_kind: {enum: ["IMMUTABLE_BASELINE", "AUTHORIZED_CHANGE_EXCEPTION"]}
        source_change_exception_id: "safe_id|null"
        source_change_exception_source_digest: "sha256|null"
        source_change_exception_exact_subject_digest: "sha256|null"
        closes_change_exception_id: "safe_id|null"
        disposition: {const: "MIGRATED"}
        destination_rows: "LegacyDestinationRowV1[]"
        direct_source_classification: "DirectSourceClassificationV2|null"
        before_commit_sha1: "sha1"
        after_commit_sha1: "sha1"
        before_tests_tree_oid_sha1: "sha1"
        after_tests_tree_oid_sha1: "sha1"
        before_tests_snapshot_digest: "sha256"
        after_tests_snapshot_digest: "sha256"
        before_disposition_digest: "sha256"
        after_disposition_digest: "sha256"
        tests_delta_manifest_digest: "sha256"
        member_manifest_digest: "sha256"
        migration_transition_subject_ref: "safe_id_or_registered_urn"
        migration_transition_subject_digest: "sha256"
        behavior_evidence_snapshot_ref: "TypedArtifactRefV1|null"
        built_artifact_evidence_snapshot_ref: "TypedArtifactRefV1|null"
        adr0008_checker_result_refs: "TypedArtifactRefV1[]"
        architecture_checker_result_refs: "TypedArtifactRefV1[]"
        destination_marker_checker_result_refs: "TypedArtifactRefV1[]"
        residual_reference_checker_result_refs: "TypedArtifactRefV1[]"
        migration_gate_evaluation_ref: "TypedArtifactRefV1|null"
        compatibility_owner_acceptance_ref: "TypedArtifactRefV1|null"
        migration_owner_acceptance_ref: "TypedArtifactRefV1|null"
        process_assurance_owner_acceptance_ref: "TypedArtifactRefV1|null"
        independent_migration_review_ref: "TypedArtifactRefV1|null"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        recorded_at: "strict_utc"
        result: {enum: ["PASS", "FAIL", "UNKNOWN"]}
        status: {enum: ["PROPOSED", "ACCEPTED", "REJECTED"]}
      nullable_fields: ["source_change_exception_id", "source_change_exception_source_digest", "source_change_exception_exact_subject_digest", "closes_change_exception_id", "direct_source_classification", "behavior_evidence_snapshot_ref", "built_artifact_evidence_snapshot_ref", "migration_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_migration_review_ref", "accepted_at"]
      array_cardinalities:
        destination_rows: "1..N"
        adr0008_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        architecture_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        destination_marker_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        residual_reference_checker_result_refs: "0..N; ACCEPTED requires 1..N"
      array_order:
        destination_rows: "BYTEWISE_PATH"
        adr0008_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        architecture_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        destination_marker_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        residual_reference_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
      invariants:
        - "filename ID equals proof_id; destination_rows is nonempty; disposition is MIGRATED; retirement_rationale and an empty destination are schema-invalid"
        - "all group members have byte-identical shared fields, contiguous indexes 1..group_member_count, one event, one member_manifest_digest, and one migration transition subject ref/digest"
        - "all group-level evidence, checker, gate, owner-decision, review, accepted_at, result, and status fields are byte-identical across members; only direct-source classification is member-local"
        - "the member manifest contains LegacyMemberManifestRowV2 rows only; each exact_subject_digest resolves a V2 member subject and including finalized source_digest would create a digest cycle and is forbidden"
        - "after_commit_sha1 has exactly before_commit_sha1 as its sole parent; event trees, snapshots, ledgers, and exact named-only delta independently recompute"
        - "IMMUTABLE_BASELINE and AUTHORIZED_CHANGE_EXCEPTION branches satisfy the exact nullability, digest, causality, expiry, and one-time closure predicates in this ADR"
        - "direct_source_classification is nonnull exactly for LEGACY-TEST-TOPLEVEL-001 and null otherwise"
        - "ACCEPTED requires result PASS, profile CURRENT, all group artifact roles, three distinct eligible owner principals, and nonnull accepted_at; authority additionally requires the separate successful group LandingRecord role"
        - "PROPOSED has null accepted_at; REJECTED grants no authority and cannot carry result PASS"

    - type_id: "LegacyTestCutoverRemovalRecordV2"
      type_version: "2.0.0"
      source_pattern: "architecture/records/legacy-test-layout/cutover-removal-records/<cutover_removal_record_id>.json"
      schema_ref: "schemas/common/legacy-test-cutover-removal-record-v2.schema.json"
      additional_properties: false
      fields: ["schema_version", "record_type", "cutover_removal_record_id", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "landing_record_ref", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest", "baseline_disposition_count", "remaining_inherited_file_count", "open_change_exception_count", "resulting_test_snapshot_digest", "migration_transition_count", "ordered_migration_subset_digest", "test_lineage_digest", "cutover_evidence_snapshot_ref", "runner_import_configuration_checker_result_refs", "destination_lineage_checker_result_refs", "adr0008_checker_result_refs", "architecture_checker_result_refs", "zero_legacy_checker_result_refs", "registry_closure_checker_result_refs", "cutover_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_cutover_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]
      field_types:
        schema_version: {const: "2"}
        record_type: {const: "LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2"}
        cutover_removal_record_id: {const: "LEGACY-TEST-CUTOVER-001"}
        policy_id: {const: "RANEX-LEGACY-TEST-LAYOUT-2.0"}
        policy_version: {const: "2.0.0"}
        baseline_id: {const: "HERMES-TEST-BASELINE-001"}
        baseline_file_manifest_sha256: "hex_sha256"
        test_practice_profile_id: "safe_id"
        test_practice_profile_version: "semver"
        test_practice_profile_digest: "sha256"
        profile_freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
        landing_record_ref: "safe_id"
        before_commit_sha1: "sha1"
        after_commit_sha1: "sha1"
        before_tests_tree_oid_sha1: "sha1"
        after_tests_tree_oid_sha1: "sha1"
        before_tests_snapshot_digest: "sha256"
        after_tests_snapshot_digest: "sha256"
        tests_delta_manifest_digest: "sha256"
        baseline_disposition_count: "nonnegative_integer"
        remaining_inherited_file_count: "nonnegative_integer"
        open_change_exception_count: "nonnegative_integer"
        resulting_test_snapshot_digest: "sha256"
        migration_transition_count: "nonnegative_integer"
        ordered_migration_subset_digest: "sha256"
        test_lineage_digest: "sha256"
        cutover_evidence_snapshot_ref: "TypedArtifactRefV1|null"
        runner_import_configuration_checker_result_refs: "TypedArtifactRefV1[]"
        destination_lineage_checker_result_refs: "TypedArtifactRefV1[]"
        adr0008_checker_result_refs: "TypedArtifactRefV1[]"
        architecture_checker_result_refs: "TypedArtifactRefV1[]"
        zero_legacy_checker_result_refs: "TypedArtifactRefV1[]"
        registry_closure_checker_result_refs: "TypedArtifactRefV1[]"
        cutover_gate_evaluation_ref: "TypedArtifactRefV1|null"
        compatibility_owner_acceptance_ref: "TypedArtifactRefV1|null"
        migration_owner_acceptance_ref: "TypedArtifactRefV1|null"
        process_assurance_owner_acceptance_ref: "TypedArtifactRefV1|null"
        independent_cutover_review_ref: "TypedArtifactRefV1|null"
        exact_subject_ref: "safe_id_or_registered_urn"
        exact_subject_digest: "sha256"
        accepted_at: "strict_utc|null"
        recorded_at: "strict_utc"
        result: {enum: ["PASS", "FAIL", "UNKNOWN"]}
        status: {enum: ["PROPOSED", "ACCEPTED", "REJECTED"]}
      nullable_fields: ["cutover_evidence_snapshot_ref", "cutover_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_cutover_review_ref", "accepted_at"]
      array_cardinalities:
        runner_import_configuration_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        destination_lineage_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        adr0008_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        architecture_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        zero_legacy_checker_result_refs: "0..N; ACCEPTED requires 1..N"
        registry_closure_checker_result_refs: "0..N; ACCEPTED requires 1..N"
      array_order:
        runner_import_configuration_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        destination_lineage_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        adr0008_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        architecture_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        zero_legacy_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
        registry_closure_checker_result_refs: "BYTEWISE_TYPED_ARTIFACT_IDENTITY"
      invariants:
        - "baseline_file_manifest_sha256 equals the immutable 2,444-row baseline manifest and baseline_disposition_count == 2444"
        - "after_commit_sha1 has exactly before_commit_sha1 as its sole parent; the tests tree is byte-identical, the two tree OIDs are equal, and tests_delta_manifest_digest is the RFC8785 digest of an empty LegacyTestsDeltaRowV1 array"
        - "remaining_inherited_file_count == 0 and open_change_exception_count == 0"
        - "resulting_test_snapshot_digest is the RFC8785 SHA-256 of complete bytewise-path LegacyResultingTestRowV1 rows; ordered_migration_subset_digest is the RFC8785 SHA-256 of complete LegacyOrderedMigrationSubsetRowV2 rows whose proof IDs/digests resolve only V2 members; test_lineage_digest is the RFC8785 SHA-256 of complete bytewise-test-ID LegacyTestLineageRowV1 rows"
        - "ACCEPTED requires result PASS, profile CURRENT, all twelve noncompensating artifact roles, three distinct eligible owner principals, and nonnull accepted_at; authority additionally requires the separate successful cutover LandingRecord role"
        - "PROPOSED has null accepted_at; REJECTED grants no authority and cannot carry result PASS"

  subject_projection_contract:
    projection_rule:
      - "Construct exactly output_fields; retain declared nulls; reject missing or extra output keys."
      - "RFC8785-canonicalize the projection, then SHA-256 those bytes."
      - "The record exact_subject_ref and exact_subject_digest equal the derived values."
      - "Every source field is classified exactly once as direct, transformed, or excluded."
      - "Artifact, decision, review, landing receipt, source-byte digest, and lifecycle/result fields are excluded to prevent circular authorization."
    projections:
      - projection_id: "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1"
        subject_schema: "test-behavior-authority-subject/v1"
        subject_ref_rule: "urn:ranex:test-behavior:<behavior_id>:<behavior_version>"
        source_record_type: "TestBehaviorAuthorityV1"
        output_fields: ["subject_schema", "subject_ref", "behavior_id", "behavior_version", "behavior_subject_schema", "behavior_subject_ref", "behavior_subject_digest", "owner_context_id", "capability_id", "definition_source_ref", "definition_source_digest", "work_item_id", "valid_from", "expires_at", "supersedes_behavior_ref"]
        direct_included_source_fields: ["behavior_id", "behavior_version", "behavior_subject_schema", "behavior_subject_ref", "behavior_subject_digest", "owner_context_id", "capability_id", "definition_source_ref", "definition_source_digest", "work_item_id", "valid_from", "expires_at", "supersedes_behavior_ref"]
        transformed_source_fields: {}
        excluded_source_fields: ["schema_version", "record_type", "owner_decision_ref", "owner_decision_digest", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]

      - projection_id: "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1"
        subject_schema: "direct-source-classification-authority-subject/v1"
        subject_ref_rule: "urn:ranex:legacy-test-direct-classification:<classification_id>"
        source_record_type: "DirectSourceClassificationAuthorityV1"
        output_fields: ["subject_schema", "subject_ref", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "classification_id", "affected_scope_id", "baseline_source_row", "behavior_id", "behavior_version", "context_id", "capability_id", "owner_id", "test_lane", "exact_test_metadata_segment", "destination_root", "work_item_id", "authority_bindings", "valid_from", "expires_at", "supersedes_classification_id"]
        direct_included_source_fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "classification_id", "affected_scope_id", "baseline_source_row", "behavior_id", "behavior_version", "context_id", "capability_id", "owner_id", "test_lane", "exact_test_metadata_segment", "destination_root", "work_item_id", "authority_bindings", "valid_from", "expires_at", "supersedes_classification_id"]
        transformed_source_fields: {}
        excluded_source_fields: ["schema_version", "record_type", "classification_decision_ref", "classification_decision_digest", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]

      - projection_id: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2"
        subject_schema: "legacy-test-change-exception-subject/v2"
        subject_ref_rule: "urn:ranex:legacy-test-change:v2:<change_exception_id>"
        source_record_type: "LegacyTestChangeExceptionV2"
        output_fields: ["subject_schema", "subject_ref", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "change_exception_id", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_row", "current_row", "rationale", "compatibility_owner", "migration_owner", "test_governance_owner", "expires_at", "canonical_destination", "direct_source_classification", "replacement_plan_ref", "new_ranex_behavior_forbidden", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest"]
        direct_included_source_fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "change_exception_id", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_row", "current_row", "rationale", "compatibility_owner", "migration_owner", "test_governance_owner", "expires_at", "canonical_destination", "direct_source_classification", "replacement_plan_ref", "new_ranex_behavior_forbidden", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest"]
        transformed_source_fields: {}
        excluded_source_fields: ["schema_version", "record_type", "profile_freshness_status", "maintenance_evidence_snapshot_ref", "maintenance_checker_result_refs", "change_gate_evaluation_ref", "change_owner_acceptance_ref", "independent_migration_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]

      - projection_id: "LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2"
        subject_schema: "legacy-test-migration-member-subject/v2"
        subject_ref_rule: "urn:ranex:legacy-test-migration-member:v2:<proof_id>"
        source_record_type: "LegacyTestMigrationRecordV2"
        output_fields: ["subject_schema", "subject_ref", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "proof_id", "migration_group_id", "group_member_index", "group_member_count", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_source_row", "current_source_row", "source_state_kind", "source_change_exception_id", "source_change_exception_source_digest", "source_change_exception_exact_subject_digest", "closes_change_exception_id", "disposition", "destination_rows", "direct_source_classification", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_disposition_digest", "after_disposition_digest", "tests_delta_manifest_digest"]
        direct_included_source_fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "proof_id", "migration_group_id", "group_member_index", "group_member_count", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "affected_scope_id", "baseline_source_row", "current_source_row", "source_state_kind", "source_change_exception_id", "source_change_exception_source_digest", "source_change_exception_exact_subject_digest", "closes_change_exception_id", "disposition", "destination_rows", "direct_source_classification", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_disposition_digest", "after_disposition_digest", "tests_delta_manifest_digest"]
        transformed_source_fields: {}
        excluded_source_fields: ["schema_version", "record_type", "proof_type", "profile_freshness_status", "member_manifest_digest", "migration_transition_subject_ref", "migration_transition_subject_digest", "behavior_evidence_snapshot_ref", "built_artifact_evidence_snapshot_ref", "adr0008_checker_result_refs", "architecture_checker_result_refs", "destination_marker_checker_result_refs", "residual_reference_checker_result_refs", "migration_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_migration_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]

      - projection_id: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2"
        subject_schema: "legacy-test-migration-transition-subject/v2"
        subject_ref_rule: "urn:ranex:legacy-test-migration-group:v2:<migration_group_id>"
        source_record_type: "complete LegacyTestMigrationRecordV2 group"
        output_fields: ["subject_schema", "subject_ref", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "migration_group_id", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_disposition_digest", "after_disposition_digest", "tests_delta_manifest_digest", "member_manifest_digest"]
        shared_member_source_fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "migration_group_id", "transition_sequence", "predecessor_transition_id", "causation_ref", "landing_record_ref", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_disposition_digest", "after_disposition_digest", "tests_delta_manifest_digest", "member_manifest_digest"]
        member_manifest_derivation:
          row_type: "LegacyMemberManifestRowV2"
          cardinality: "1..N equal to group_member_count"
          order: "NUMERIC_GROUP_MEMBER_INDEX_THEN_BYTEWISE_PROOF_ID"
          digest_rule: "RFC8785 SHA-256 of the complete ordered row array"
        invariants:
          - "Every shared field is byte-identical across all members and member_manifest_digest equals the independent derivation."
          - "The group subject depends on member subjects, but no member subject depends on the group subject or finalized source bytes."

      - projection_id: "LEGACY_TEST_CUTOVER_SUBJECT_V2"
        subject_schema: "legacy-test-cutover-subject/v2"
        subject_ref_rule: "urn:ranex:legacy-test-cutover:v2:LEGACY-TEST-CUTOVER-001"
        source_record_type: "LegacyTestCutoverRemovalRecordV2"
        output_field_count: 25
        output_fields: ["subject_schema", "subject_ref", "policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "cutover_removal_record_id", "landing_record_ref", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest", "baseline_disposition_count", "remaining_inherited_file_count", "open_change_exception_count", "resulting_test_snapshot_digest", "migration_transition_count", "ordered_migration_subset_digest", "test_lineage_digest"]
        direct_included_source_fields: ["policy_id", "policy_version", "baseline_id", "baseline_file_manifest_sha256", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "cutover_removal_record_id", "landing_record_ref", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "tests_delta_manifest_digest", "baseline_disposition_count", "remaining_inherited_file_count", "open_change_exception_count", "resulting_test_snapshot_digest", "migration_transition_count", "ordered_migration_subset_digest", "test_lineage_digest"]
        transformed_source_fields: {}
        excluded_source_fields: ["schema_version", "record_type", "profile_freshness_status", "cutover_evidence_snapshot_ref", "runner_import_configuration_checker_result_refs", "destination_lineage_checker_result_refs", "adr0008_checker_result_refs", "architecture_checker_result_refs", "zero_legacy_checker_result_refs", "registry_closure_checker_result_refs", "cutover_gate_evaluation_ref", "compatibility_owner_acceptance_ref", "migration_owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_cutover_review_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "result", "status"]

  artifact_role_resolvers:
    common_predicates:
      - "TypedArtifactRefV1 artifact_type, artifact_ref, and artifact_digest resolve through ADR-0008's closed artifact resolver to byte-exact schema-valid bytes."
      - "Resolved subject_schema/ref/digest exactly equals the named projection; dangling, wrong-type, wrong-subject, stale, unqualified, or forged refs fail."
      - "CheckerResult is COMPLETED/PASS with exact role coverage and no invalidating limitation; EvidenceSnapshot has the exact claim denominator with no missing/conflicting claim; GateEvaluation is PASS and binds the eligible snapshot/check set; ReviewVerdict is ACCEPTABLE and independently eligible; HumanDecision is authenticated APPROVED, unrevoked, unexpired, and exact-role/action/scope authorized."
      - "Every checker role resolves a source-bound profile row containing the required checker ID/version/code digest/fixture digest/qualification and exact required-claim denominator; the reference set equals the complete applicable role population, so a free-form role label or one convenient checker cannot substitute."
      - "ADR-0008 and architecture coverage roles reconcile the complete source-bound rule registries at the recorded profile version; every applicable rule has qualified PASS coverage and every not-applicable rule has its separately eligible typed proof."
      - "Built-artifact evidence and checker execution subjects use one identical nonnull artifact digest reproducibly built from the exact event after_commit_sha1 under the bound profile; a subject-matching snapshot cannot bless a different build."
    roles:
      - {record_type: "TestBehaviorAuthorityV1", reference_path: "/owner_decision_ref", artifact_type: "human_decision", expected_subject: "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1", role: "TEST_BEHAVIOR_OWNER", action: "REGISTER_TEST_BEHAVIOR", outcome: "ALLOW", active_cardinality: "1"}
      - {record_type: "DirectSourceClassificationAuthorityV1", reference_path: "/classification_decision_ref", artifact_type: "human_decision", expected_subject: "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1", role: "TEST_CLASSIFICATION_OWNER", action: "ALLOW_DIRECT_LEGACY_TEST_CLASSIFICATION", outcome: "ALLOW", active_cardinality: "1"}
      - {record_type: "LegacyTestChangeExceptionV2", reference_path: "/maintenance_evidence_snapshot_ref", artifact_type: "evidence_snapshot", expected_subject: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", role: "LEGACY_CHANGE_EVIDENCE", active_cardinality: "1"}
      - {record_type: "LegacyTestChangeExceptionV2", reference_path: "/maintenance_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", role: "LEGACY_CHANGE_MAINTENANCE_CHECKER", active_cardinality: "1..N"}
      - {record_type: "LegacyTestChangeExceptionV2", reference_path: "/change_gate_evaluation_ref", artifact_type: "gate_evaluation", expected_subject: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", role: "LEGACY_CHANGE_GATE", active_cardinality: "1"}
      - {record_type: "LegacyTestChangeExceptionV2", reference_path: "/change_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", role: "compatibility", action: "AUTHORIZE_LEGACY_IN_PLACE_CHANGE", scope_rule: "affected_scope_id plus exact baseline path", active_cardinality: "1"}
      - {record_type: "LegacyTestChangeExceptionV2", reference_path: "/independent_migration_review_ref", artifact_type: "review_verdict", expected_subject: "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2", role: "INDEPENDENT_LEGACY_CHANGE_REVIEW", active_cardinality: "1"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/behavior_evidence_snapshot_ref", artifact_type: "evidence_snapshot", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "MIGRATION_BEHAVIOR_EVIDENCE", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/built_artifact_evidence_snapshot_ref", artifact_type: "evidence_snapshot", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "MIGRATION_BUILT_ARTIFACT_EVIDENCE", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/adr0008_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "ADR0008_APPLICABLE_RULE_COVERAGE", active_cardinality: "1..N per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/architecture_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "ARCHITECTURE_APPLICABLE_RULE_COVERAGE", active_cardinality: "1..N per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/destination_marker_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "DESTINATION_MARKER_AND_LINEAGE", active_cardinality: "1..N per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/residual_reference_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "ZERO_RESIDUAL_SOURCE_REFERENCE", active_cardinality: "1..N per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/migration_gate_evaluation_ref", artifact_type: "gate_evaluation", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "LEGACY_MIGRATION_GATE", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/compatibility_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "compatibility", action: "ACCEPT_LEGACY_MIGRATION", scope_rule: "whole migration group", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/migration_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "migration", action: "ACCEPT_LEGACY_MIGRATION", scope_rule: "whole migration group", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/process_assurance_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "process_assurance", action: "ACCEPT_LEGACY_MIGRATION", scope_rule: "whole migration group", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestMigrationRecordV2", reference_path: "/independent_migration_review_ref", artifact_type: "review_verdict", expected_subject: "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2", role: "INDEPENDENT_LEGACY_MIGRATION_REVIEW", active_cardinality: "1 per group"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/cutover_evidence_snapshot_ref", artifact_type: "evidence_snapshot", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "CUTOVER_WHOLE_EVENT_EVIDENCE", active_cardinality: "1"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/runner_import_configuration_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "ZERO_RUNNER_IMPORT_CONFIGURATION_REFERENCE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/destination_lineage_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "DESTINATION_LINEAGE_CLOSURE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/adr0008_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "ADR0008_APPLICABLE_RULE_COVERAGE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/architecture_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "ARCHITECTURE_APPLICABLE_RULE_COVERAGE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/zero_legacy_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "ZERO_LEGACY_SOURCE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/registry_closure_checker_result_refs/*", artifact_type: "checker_result", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "REGISTRY_AND_DISPOSITION_CLOSURE", active_cardinality: "1..N"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/cutover_gate_evaluation_ref", artifact_type: "gate_evaluation", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "LEGACY_CUTOVER_GATE", active_cardinality: "1"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/compatibility_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "compatibility", action: "ACCEPT_LEGACY_CUTOVER", scope_rule: "complete baseline", active_cardinality: "1"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/migration_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "migration", action: "ACCEPT_LEGACY_CUTOVER", scope_rule: "complete baseline", active_cardinality: "1"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/process_assurance_owner_acceptance_ref", artifact_type: "human_decision", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "process_assurance", action: "ACCEPT_LEGACY_CUTOVER", scope_rule: "complete baseline", active_cardinality: "1"}
      - {record_type: "LegacyTestCutoverRemovalRecordV2", reference_path: "/independent_cutover_review_ref", artifact_type: "review_verdict", expected_subject: "LEGACY_TEST_CUTOVER_SUBJECT_V2", role: "INDEPENDENT_LEGACY_CUTOVER_REVIEW", active_cardinality: "1"}

  nonartifact_reference_resolvers:
    common_failure_rule: "Missing, duplicate, mutable-name-only, wrong-type, wrong-version, wrong-digest, wrong-scope, stale, or noncausal resolution is blocking UNKNOWN."
    direct_source_classification_authority:
      authority_id: "DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0"
      authority_record_type: "DirectSourceClassificationAuthorityV1"
      authority_subject_projection: "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1"
      authority_source_pattern: "architecture/records/legacy-test-layout/direct-source-classifications/<classification_id>.json"
      authority_registry: "architecture/contracts/legacy-test-direct-source-classifications.json#REG-LEGACY-TEST-DIRECT-SOURCE-CLASSIFICATIONS-001"
      authority_catalog_row_type: "DirectSourceClassificationAuthorityRowV1"
      behavior_record_type: "TestBehaviorAuthorityV1"
      behavior_subject_projection: "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1"
      behavior_source_pattern: "architecture/records/test-governance/behavior-authorities/<behavior_id>@<behavior_version>.json"
      behavior_registry: "architecture/contracts/test-behaviors.json#REG-TEST-BEHAVIORS-001"
      behavior_catalog_row_type: "TestBehaviorAuthorityRowV1"
      live_initial_behavior_population: "EMPTY_FAIL_CLOSED"
      authoring_templates:
        behavior: "docs/architecture/templates/TEST_BEHAVIOR_AUTHORITY.yaml"
        classification: "docs/architecture/templates/DIRECT_SOURCE_CLASSIFICATION_AUTHORITY.yaml"
      source_bijection:
        - "Every authority/behavior source has exactly one registry row with exact source path and source-byte digest, and every row has exactly one canonical source."
        - "README.md is the sole permitted non-source entry in each exact authority root and is excluded from source counts/digests; it grants no authority."
        - "Duplicate IDs/versions/paths, orphan rows/sources, unallowlisted ignored or nonmatching entries, symlinks, alternate roots, or source/registry/manifest drift are blocking."
      authority_bindings:
        exact_role_count: 6
        roles: ["BEHAVIOR", "CONTEXT", "CAPABILITY", "OWNERSHIP", "TEST_LANE", "DESTINATION_ROOT"]
        order: "ENUM_ORDER_BEHAVIOR_CONTEXT_CAPABILITY_OWNERSHIP_TEST_LANE_DESTINATION_ROOT"
        required_sources:
          BEHAVIOR: "REG-TEST-BEHAVIORS-001 exact active behavior row"
          CONTEXT: "REG-CONTEXTS-001 exact context row"
          CAPABILITY: "REG-ARCHITECTURE-ELEMENTS-001 exact CAPABILITY_ZONE row"
          OWNERSHIP: "REG-DATA-OWNERSHIP-001 exact owner-context row"
          TEST_LANE: "REG-TEST-PRACTICES-001 exact taxonomy row"
          DESTINATION_ROOT: "REG-ACCEPTED-ADRS-001 exact ADR-0008 row plus the same REG-TEST-PRACTICES-001 taxonomy row"
      subject_and_decision:
        subject_key: "classification_id plus affected_scope_id plus exact baseline_source_row plus work_item_id"
        subject_digest_rule: "RFC8785 SHA-256 of exactly DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1; decision, landing, lifecycle, exact-subject, and source-digest fields are excluded"
        decision_rule: "Exactly one byte-exact HumanDecision resolves APPROVED with outcome ALLOW, role TEST_CLASSIFICATION_OWNER, action ALLOW_DIRECT_LEGACY_TEST_CLASSIFICATION, and the exact classification subject; its canonical_argument_digest equals the RFC8785 SHA-256 of the classification mapping and six bindings."
        noncircularity: "The classification subject exists before its HumanDecision and source record; the separately landed finalized authority source exists before any transition subject that includes its source ref/digest."
      cardinality:
        behavior_row: "exactly 1 current ACTIVE behavior ID/version"
        authority_source: "exactly 1 byte-exact ACTIVE source per classification_id"
        authority_for_scope_source_at_observation: "exactly 1 current eligible nonsuperseded authority"
        decision: "exactly 1 eligible nonconflicting decision"
        landing_record: "exactly 1 eligible SUCCEEDED receipt for the authority subject/source"
        direct_change_resolution: "exactly 1 mandatory resolver invocation and result"
        direct_migration_member_resolution: "exactly 1 mandatory resolver invocation and result per direct member"
      lifecycle:
        - "Behavior and classification valid_from are at or before their owner decision issued_at; decision issued_at is at or before accepted_at and observation; observation is strictly before behavior, classification, and decision expires_at."
        - "Decision revoked_at is null; no eligible conflicting decision, higher active behavior version, or active classification naming the prior ID in supersedes_classification_id exists."
        - "Behavior/classification status is ACTIVE, accepted_at is nonnull, bound immutable catalog snapshots/rows remain byte-exact, the current catalog lineage proves those rows unrevoked and unsuperseded, and each separate LandingRecord is SUCCEEDED, causally landed, and sealing-valid."
        - "An unrelated additive row in a later catalog snapshot does not stale historical authority; changed/revoked/superseded bound rows, incompatible authority versions, or a current lineage that cannot prove continuity do."
        - "The live empty behavior registry grants no authority. Synthetic positive fixtures prove satisfiability only and cannot be loaded by a current repository validation or runtime authority resolver."
      compatibility:
        - "The behavior row's behavior ID/version, owner_context_id, and capability_id exactly equal the classification row; the behavior subject and definition source independently resolve by digest."
        - "context_id and owner_id equal the behavior owner context and exact current context/data-ownership rows; capability_id resolves exactly one current CAPABILITY_ZONE row compatible with that context."
        - "test_lane resolves exactly one current REG-TEST-PRACTICES-001 taxonomy row. Its semantic_leaf_owner_parameter selects exactly one normalized leaf: CONTEXT -> context_id, CAPABILITY -> capability_id, OWNER -> owner_id, EXACT_TEST_METADATA -> nonnull exact_test_metadata_segment; that field is null for every other branch."
        - "destination_root equals taxonomy.root + '/' + the selected leaf, and the expanded path satisfies exactly one taxonomy mirror_pattern. A wrong registry, profile-only category row, wrong semantic branch, ambiguous pattern, or root guessed from labels is ineligible."
        - "Every change canonical_destination and migration destination path is a regular .py path strictly below destination_root; no normalized alias, root equality, legacy path, retired ID, or conflicting binding is accepted."
      call_path_invariant:
        - "When affected_scope_id is LEGACY-TEST-TOPLEVEL-001, both validate_legacy_change_exception and every validate_legacy_migration_ledger member invoke this resolver with the exact record, baseline row, authority/behavior sources, six registries, artifact registry, LandingRecord registry, and observation time."
        - "Any missing resolver argument, optional/default authority world, fixture-only authority map, skipped branch, or truthy-label fallback is blocking UNKNOWN."
        - "Every fixed-root scope requires direct_source_classification null and never calls this resolver as a substitute for its fixed scope authority."
      positive_fixture_requirements:
        active_landed_behavior_and_direct_change_authority: 1
        active_landed_behavior_and_direct_migration_authority: 1
        active_superseding_authority_invalidates_predecessor_and_authorizes_successor: 1
        exact_positive_case_count: 3
      negative_fixture_requirements:
        missing_authority_source: 1
        duplicate_authority_source: 1
        wrong_authority_source_path_or_filename: 1
        authority_source_digest_mismatch: 1
        authority_registry_source_bijection_failure: 1
        wrong_baseline_scope_or_source: 1
        missing_behavior_row: 1
        wrong_or_stale_behavior_version: 1
        behavior_source_or_row_digest_mismatch: 1
        behavior_expired_revoked_or_superseded: 1
        missing_behavior_decision: 1
        behavior_decision_wrong_subject: 1
        behavior_decision_wrong_role_action_or_outcome: 1
        behavior_decision_digest_ref_mismatch: 1
        missing_binding_role: 1
        duplicate_binding_role: 1
        authority_binding_order_wrong: 1
        wrong_registry_id_version_or_ref: 1
        registry_digest_mismatch: 1
        row_ref_missing_or_wrong: 1
        row_digest_mismatch: 1
        context_behavior_mismatch: 1
        capability_behavior_mismatch: 1
        ownership_context_mismatch: 1
        lane_category_mismatch: 1
        test_lane_bound_to_profile_not_taxonomy_registry: 1
        taxonomy_mirror_pattern_mismatch: 1
        nondeterministic_destination_root: 1
        missing_classification_decision: 1
        decision_wrong_subject: 1
        decision_wrong_role_action_or_outcome: 1
        classification_decision_digest_ref_mismatch: 1
        decision_not_approved_revoked_or_superseded: 1
        decision_or_authority_expired_or_not_yet_valid: 1
        conflicting_or_superseding_classification: 1
        behavior_authority_landing_omitted: 1
        classification_authority_landing_omitted_or_failed: 1
        classification_authority_landing_wrong_subject: 1
        sealing_behavior_registry_digest_wrong_or_omitted: 1
        sealing_classification_registry_digest_wrong_or_omitted: 1
        transition_mapping_or_authority_digest_mismatch: 1
        direct_change_resolver_omitted: 1
        direct_migration_resolver_omitted: 1
        synthetic_fixture_claimed_as_live_authority: 1
        exact_negative_case_count: 44
    scope_destination_authority:
      authority_id: "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-2.0"
      source_authority: "architecture/contracts/legacy-test-layout-policy-v2.json exact exception/direct/canonical scope rows plus DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0 and exact ADR-0008 taxonomy authorities"
      normalized_row_type: "LegacyTestScopeAuthorityRowV2"
      subject_schema: "legacy-test-scope-authority-subject/v2"
      subject_ref_rule: "urn:ranex:legacy-test-scope:<affected_scope_id>"
      subject_digest_rule: "RFC8785 SHA-256 of the one complete normalized LegacyTestScopeAuthorityRowV2"
      cardinality:
        scope_row_per_affected_scope_id: "exactly 1"
        scope_match_per_baseline_source_path: "exactly 1"
        change_source_path: "exactly 1 baseline path, unchanged before/after"
        migration_source_path_per_member: "exactly 1 baseline path"
        fixed_destination_root: "exactly 1 for fixed-root scopes"
        classification_destination_root: "exactly 1 eligible separately landed DirectSourceClassificationAuthorityV1-derived root for direct-top-level scope"
        destination_rows: "1..N, bytewise path ordered and duplicate-free"
      freshness:
        - "The policy ID/version, baseline manifest, normalized row subject/digest, ADR-0008 taxonomy registries, and any behavior/classification authority stack are current and mutually consistent at accepted_at, LandingRecord.finished_at, and validation_observed_at."
        - "The scope row expires at its declared expires_at and the policy cutoff; a superseded policy, changed row/digest, expired row, or post-expiry unfinished event is ineligible."
      predicates:
        - "affected_scope_id resolves one normalized row and every baseline/current source path belongs to that row's exact source population; a syntactically valid arbitrary scope ID is invalid."
        - "baseline_row/current_row and baseline_source_row/current_source_row use one identical source path; that path is an immutable baseline member and cannot match two scopes."
        - "For FIXED_CANONICAL_ROOT, canonical_destination and every destination_rows path are regular .py paths strictly below the row's exact ADR-0008 destination_root."
        - "For CLASSIFICATION_DECISION, canonical_destination and every destination_rows path are regular .py paths strictly below the exact root derived by the mandatory DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0 resolver; no transition-local HumanDecision or label map may substitute."
        - "No destination is a legacy/direct-top-level path, escapes through path normalization, reuses a retired test ID, or conflicts with another member's path/test-ID binding."
      positive_fixture_requirements:
        direct_top_level_change_exact_landed_classification_authority: 1
        direct_top_level_migration_exact_landed_classification_authority: 1
        fixed_root_change_null_classification: 1
        fixed_root_migration_null_classification: 1
        exact_positive_case_count: 4
      negative_fixture_requirements:
        unknown_scope_id: 1
        missing_scope_row: 1
        duplicate_scope_row: 1
        wrong_scope_for_source_path: 1
        overlapping_scope_match: 1
        baseline_population_digest_mismatch: 1
        stale_or_wrong_policy_binding: 1
        expired_scope: 1
        fixed_destination_outside_root: 1
        migration_missing_or_wrong_classification_root: 1
        change_missing_classification: 1
        change_wrong_classification_root: 1
        change_stale_classification: 1
        change_cross_subject_classification: 1
        noncanonical_or_non_py_destination: 1
        path_traversal_or_legacy_recontamination: 1
        duplicate_or_conflicting_destination: 1
        exact_negative_case_count: 17
    roles:
      - {reference_paths: ["/policy_id", "/policy_version", "/baseline_id", "/baseline_file_manifest_sha256"], authority: "architecture/contracts/legacy-test-layout-policy-v2.json plus immutable baseline rows", predicate: "all values equal policy2 and the one source-bound policy/baseline projection"}
      - {reference_paths: ["/test_practice_profile_id", "/test_practice_profile_version", "/test_practice_profile_digest", "/profile_freshness_status"], authority: "test-practice-profiles registry", predicate: "one exact profile triple resolves and freshness recomputes CURRENT at acceptance and validation"}
      - {reference_paths: ["/affected_scope_id", "/baseline_row/path", "/current_row/path", "/baseline_source_row/path", "/current_source_row/path"], authority: "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-2.0", predicate: "one current scope subject/digest resolves and every applicable source path belongs to its exact baseline population"}
      - {reference_paths: ["/canonical_destination", "/destination_rows/*/path"], authority: "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-2.0 plus ADR-0008 canonical path/root registries", predicate: "every applicable destination is canonical and strictly below the fixed or authenticated-classification root for the resolved scope"}
      - {reference_paths: ["/causation_ref"], authority: "CoreSdlcTrace and governed work/event registries", predicate: "one immutable trace/event resolves for the exact event subject and after commit"}
      - {reference_paths: ["/replacement_plan_ref"], authority: "governed work-item/task-packet registries", predicate: "one current owned plan resolves the exact change path, destination, migration trigger, and deadline no later than exception expiry"}
      - {reference_paths: ["/predecessor_transition_id"], authority: "baseline identity or accepted migration-group registry", predicate: "sequence 1 names the baseline; later sequence names exactly the immediately prior complete group whose landed commit is an ancestor"}
      - {reference_paths: ["/source_change_exception_id", "/source_change_exception_source_digest", "/source_change_exception_exact_subject_digest", "/closes_change_exception_id"], authority: "immutable change-source history, source registry, artifact registry, and LandingRecord registry", predicate: "the authorized-change branch resolves exactly one prior active accepted change and its one-time closure"}
      - {reference_paths: ["/exact_subject_ref", "/exact_subject_digest", "/migration_transition_subject_ref", "/migration_transition_subject_digest", "/member_manifest_digest"], authority: "the subject projection contract in this catalog", predicate: "all stored values exactly equal independent projection/DAG derivation"}
      - {reference_paths: ["/direct_source_classification/classification_id", "/direct_source_classification/classification_source_ref", "/direct_source_classification/classification_source_digest", "/direct_source_classification/behavior_id", "/direct_source_classification/context_id", "/direct_source_classification/capability_id", "/direct_source_classification/owner_id", "/direct_source_classification/test_lane", "/direct_source_classification/destination_root"], authority: "DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0 plus its exact behavior and six catalog bindings", predicate: "one ACTIVE separately landed authority source resolves by exact bytes; repeated mapping, taxonomy branch/root, lifecycle, decision, catalog, and real-call-path predicates all pass"}
      - {reference_paths: ["/destination_rows/*/test_id"], authority: "global Ranex test-ID/marker and retirement-lineage registry", predicate: "IDs are globally unique or same-group shared, markers are exact, retired IDs are never reused, and current lineages close"}
      - {reference_paths: ["/landing_record_ref"], authority: "the closed landing_record_role below", predicate: "one preallocated ID resolves one eligible byte-exact receipt for this subject and stack"}

  landing_record_role:
    schema_ref: "schemas/execution/landing-record-v1.schema.json"
    status_authority_ref: "ADR-0008 LANDING-RECORD-STATUS-1.0"
    additional_properties: false
    fields: ["schema_version", "artifact_type", "landing_id", "subject_schema", "subject_ref", "subject_digest", "subject_manifest_digest", "core_sdlc_trace_ref", "candidate_commit", "target_branch", "target_head_before", "landed_commit", "landing_strategy", "permit_id", "actor_principal_id", "provider_receipt_ref", "started_at", "finished_at", "status", "evidence_refs", "digest"]
    field_types:
      schema_version: {const: "1"}
      artifact_type: {const: "landing_record"}
      landing_id: "safe_id"
      subject_schema: "nonempty_string"
      subject_ref: "safe_id_or_registered_urn"
      subject_digest: "sha256"
      subject_manifest_digest: "sha256"
      core_sdlc_trace_ref: "safe_id_or_registered_urn"
      candidate_commit: "sha1"
      target_branch: "nonempty_string"
      target_head_before: "sha1"
      landed_commit: "sha1"
      landing_strategy: "nonempty_string"
      permit_id: "safe_id"
      actor_principal_id: "safe_id"
      provider_receipt_ref: "safe_id_or_registered_urn"
      started_at: "strict_utc"
      finished_at: "strict_utc"
      status: {const: "SUCCEEDED"}
      evidence_refs: "safe_id_or_registered_urn[]"
      digest: "sha256"
    nullable_fields: []
    array_cardinalities: {evidence_refs: "1..N"}
    array_order: {evidence_refs: "BYTEWISE_IDENTITY"}
    role_predicates:
      - "landing_id equals the preallocated landing_record_ref; exactly one eligible LandingRecord resolves for it"
      - "subject schema/ref/digest equals the behavior-authority, direct-classification-authority, change, complete migration-group, or cutover subject as applicable; cross-kind substitution fails"
      - "For a change/migration/cutover transition, target_head_before and the candidate parent satisfy that event's declared Git relation. For a behavior/classification authority, target_head_before is the candidate's sole parent and already contains every exact catalog/source dependency."
      - "A transition candidate changes no event test byte and adds only its canonical finalized source record set. A behavior/classification candidate adds only its one canonical finalized authority source and required generated registry projection; it cannot create, rewrite, or hide an underlying definition/catalog row."
      - "subject_manifest_digest equals the RFC8785 SHA-256 of complete bytewise-source-path LegacyRecordSourceManifestRowV1 rows derived from candidate_commit; migration rows cover every and only group member, while a behavior/classification authority covers exactly its one canonical source"
      - "landed_commit contains candidate_commit as an ancestor; provider receipt, permit, actor, strategy, target branch, and target-head compare are authenticated and mutually consistent"
      - "evidence_refs is the duplicate-free exact set of required gate, owner-decision, classification/behavior decision, and independent-review artifact IDs for the subject"
      - "candidate_tree_oid_sha1 and landed_tree_oid_sha1 are derived from the Git object database and bound in the validation result; they are not source-record fields"

  sealing_validation_role:
    closed_binding_fields: ["validation_commit_sha1", "validation_tree_oid_sha1", "validation_observed_at", "candidate_commit_sha1", "candidate_tree_oid_sha1", "landed_commit_sha1", "landed_tree_oid_sha1", "landing_record_ref", "landing_record_digest", "legacy_test_layout_policy_v2_digest", "legacy_test_layout_records_v2_digest", "historical_v1_artifact_set_digest", "test_deletion_records_digest", "test_behavior_records_digest", "test_behavior_registry_digest", "direct_source_classification_records_digest", "direct_source_classification_registry_digest"]
    field_types: {validation_commit_sha1: "sha1", validation_tree_oid_sha1: "sha1", validation_observed_at: "strict_utc", candidate_commit_sha1: "sha1", candidate_tree_oid_sha1: "sha1", landed_commit_sha1: "sha1", landed_tree_oid_sha1: "sha1", landing_record_ref: "safe_id", landing_record_digest: "sha256", legacy_test_layout_policy_v2_digest: "sha256", legacy_test_layout_records_v2_digest: "sha256", historical_v1_artifact_set_digest: "sha256", test_deletion_records_digest: "sha256", test_behavior_records_digest: "sha256", test_behavior_registry_digest: "sha256", direct_source_classification_records_digest: "sha256", direct_source_classification_registry_digest: "sha256"}
    nullable_fields: []
    array_cardinalities: {}
    predicates:
      - "validation_commit_sha1 has landed_commit_sha1 as an ancestor and every named tree OID is independently resolved from its exact commit"
      - "landing_record_ref and landing_record_digest resolve one byte-exact eligible LandingRecord; the validation commit contains the explicit policy2 projection/schema, pure-V2 record manifest, byte-exact historical V1 set, canonical source registries, artifact registries, LandingRecord, tests tree, retirement records, behavior sources/registry, and direct-classification sources/registry used by the result"
      - "legacy_test_layout_policy_v2_digest and legacy_test_layout_records_v2_digest independently recompute from the explicit V2 paths; historical_v1_artifact_set_digest equals ADR10-HISTORICAL-V1-ARTIFACTS-001. An unversioned/policy1 alias, mixed-major row, missing historical row, or mutated historical byte fails."
      - "all four behavior/classification record/registry digests independently recompute from complete canonical source populations and exact registry bytes; omission, stale registry bytes, wrong order, wrong row/source cardinality, or mixed-commit digests fail"
      - "relevant staged, unstaged, or untracked checkout bytes make a sealing result nonauthoritative"

  self_reference_prohibition:
    prohibited_source_record_fields: ["candidate_commit_sha1", "candidate_tree_oid_sha1", "landed_commit_sha1", "landed_tree_oid_sha1", "validation_commit_sha1", "validation_tree_oid_sha1", "validation_observed_at", "source_digest"]
    reason: "A candidate commit that contains a finalized source record cannot also be named inside those bytes; landed and validation facts occur later. These values belong to the separate LandingRecord and sealing-validation binding."
    digest_dag:
      - "byte-exact historical V1 artifact manifest verification"
      - "immutable baseline, policy2 projection/schema, and empty-or-pure-V2 record manifest"
      - "behavior authority subject"
      - "behavior owner decision"
      - "finalized behavior authority source bytes and behavior catalog row"
      - "behavior authority source manifest and LandingRecord"
      - "direct-source classification authority subject with six preexisting catalog bindings"
      - "classification owner decision"
      - "finalized direct-source classification authority bytes and classification catalog row"
      - "classification authority source manifest and LandingRecord"
      - "member transition subjects"
      - "stable member manifest"
      - "migration group subject"
      - "typed evidence, checks, gate, review, and owner decisions"
      - "finalized canonical source record bytes"
      - "candidate record-source manifest"
      - "LandingRecord"
      - "sealing validation binding"

  chronology_freshness_and_authority:
    event_time_order:
      - "the historical V1 exact set is verified and the explicit policy2 projection/schema plus empty-or-pure-V2 record manifest exist before any policy2 authority, transition, or cutover subject"
      - "behavior subject precedes its owner decision and finalized source; behavior candidate/landing/sealing precede any classification subject that binds its source/catalog row"
      - "classification subject precedes its owner decision and finalized source; classification candidate/landing/sealing precede any change or migration transition subject that binds its source digest"
      - "event after commit is the sole-child event described by the exact subject; Git commit timestamps are never authority"
      - "max(required EvidenceSnapshot.created_at, required CheckerResult.finished_at, required GateEvaluation.evaluated_at, required ReviewVerdict.produced_at, required classification HumanDecision.issued_at when applicable) <= min(required owner HumanDecision.issued_at)"
      - "accepted_at equals the maximum required owner HumanDecision.issued_at"
      - "accepted_at <= recorded_at and accepted_at <= LandingRecord.started_at <= LandingRecord.finished_at <= validation_observed_at"
    freshness:
      - "the explicit policy2 projection/schema and V2 record manifest remain current and byte-exact, while all nine V1 artifacts and their legal bindings remain byte-identical to ADR10-HISTORICAL-V1-ARTIFACTS-001 at every acceptance, landing, and sealing observation"
      - "behavior and classification authority sources, decisions, LandingRecords, six catalog rows/digests, source/registry bijections, and supersession populations are recomputed at transition accepted_at, LandingRecord.finished_at, and validation_observed_at"
      - "profile_freshness_status is CURRENT and the profile ID/version/digest is registered and current at accepted_at and validation_observed_at"
      - "every artifact is eligible, unrevoked, unexpired, and within its profile TTL at accepted_at and LandingRecord.finished_at; the gate snapshot and checker denominators exactly match the subject"
      - "a later discovered revocation, forgery, subject drift, or invalidated evidence blocks current authority; stored CURRENT or PASS text cannot override recomputation"
    expiry:
      - "change accepted_at and LandingRecord.finished_at are strictly before the earlier of its expires_at and 2026-10-31T23:59:59Z; an expired, closed, or revoked change grants no current byte authority"
      - "migration and cutover accepted_at and LandingRecord.finished_at are on or before 2026-10-31T23:59:59Z"
      - "a migration or cutover completely accepted, landed, and sealed by expiry remains immutable event-time history afterward; current validation still rechecks recontamination and lineage"
      - "post-expiry work cannot backdate or cure an unfinished migration or cutover"
    failure_and_rollback:
      - "a policy1 or unversioned current lookup, mixed-major ledger, mutated/missing historical artifact, nonexact legal binding, or partial V2 publication grants no authority and is blocking UNKNOWN"
      - "a behavior/classification proposal, rejected/unlanded source, stale catalog row, expired/revoked decision, superseded authority, or live empty behavior catalog grants no direct-top-level authority"
      - "PROPOSED, REJECTED, FAIL, UNKNOWN, missing/failed/duplicate LandingRecord, or unsealed validation grants no transition authority"
      - "a failed pre-landing event must be abandoned or reverted by a separately attributable commit; its record cannot be relabeled accepted"
      - "post-landing rollback is a new governed event and record; it cannot edit, reuse, erase, or backdate an accepted record"
      - "restoring any disposed legacy path is recontamination and fails this policy; reversing an accepted cutover requires a human-approved superseding ADR and policy, not mutation of historical proof"

  sibling_bindings:
    TestDeletionRecordV1:
      authority: "ADR-0008 TestDeletionRecordV1 50-field catalog and 30-field TEST_DELETION_SUBJECT_V1 projection"
      version_neutrality: "The outer V1 record and safe_id[] source_migration_proof_ids syntax remain stable; for target_kind LEGACY_SOURCE, semantic proof resolution is delegated to the exact current ADR-0010 policy identity."
      legacy_source_predicates:
        - "target_kind is LEGACY_SOURCE; legacy branch fields, prior-change closure, event Git relation, snapshots, delta, typed roles, subject, landing, and lineage all satisfy ADR-0008 and this ADR"
        - "policy2 requires every source_migration_proof_ids value to resolve exactly one accepted LegacyTestMigrationRecordV2 and LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2 in the pure-V2 ledger; V1, policy1, mixed-major, dangling, duplicate, or reused proofs fail"
        - "the complete V1 live-proof population is proven zero before first policy2 seal; the array cannot serve as a migration or compatibility bridge"
        - "all TypedArtifactRefV1 paths bind TEST_DELETION_SUBJECT_V1; no legacy migration or cutover subject may substitute"
    LandingRecord:
      authority: "the closed 21-field landing_record_role above"
      noncircularity: "LandingRecord is a post-candidate receipt and is excluded from behavior/classification authority subjects; transition projections include only their own preallocated opaque landing ID. No subject contains its finalized source digest, candidate, landed, or validation commit."
```

<!-- END ADR10 LEGACY TEST RECORD CONTRACT -->

## Behavior and direct-source authority creation

The canonical authoring forms are
`docs/architecture/templates/TEST_BEHAVIOR_AUTHORITY.yaml` and
`docs/architecture/templates/DIRECT_SOURCE_CLASSIFICATION_AUTHORITY.yaml`.
They are construction aids only; canonical authority is the closed JSON source,
its exact registry projection, eligible artifacts, successful LandingRecord,
and sealing validation.

The only permitted creation order is:

1. Verify all nine retained V1 artifacts and legal bindings, then generate and
   seal the explicit policy2 schema/projection and empty-or-pure-V2 record
   manifest. An unversioned alias is never an active input.
2. Start from an accepted, byte-digested behavior definition and exact current
   context/capability rows. Materialize one `TestBehaviorAuthorityV1` proposal,
   derive `TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1`, and obtain a separately
   authenticated `TEST_BEHAVIOR_OWNER` decision. The decision cannot edit or
   bless a subject after issuance.
3. Finalize the behavior source, land it in a commit that produces the exact
   `TestBehaviorAuthorityRowV1`, validate catalog/source bijection, seal the
   LandingRecord and catalog digest, and only then permit status `ACTIVE`.
4. For one immutable direct-top-level baseline row, resolve that active
   behavior and the exact context, capability, ownership, test-taxonomy, and
   ADR-0008 rows. Populate six `ClassificationAuthorityBindingV1` rows from
   independently recomputed registry and row digests. Derive the destination
   with the taxonomy's `semantic_leaf_owner_parameter` and prove exactly one
   expanded `mirror_pattern`.
5. Materialize one `DirectSourceClassificationAuthorityV1` proposal, derive
   `DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1`, and obtain a separate
   authenticated `TEST_CLASSIFICATION_OWNER` decision with outcome `ALLOW`.
   Finalize, land, project, and seal that authority exactly as for behavior.
6. Only a later change or migration event may copy the authority's nine-field
   mapping and exact source ref/digest into `direct_source_classification`.
   The transition validator reloads all sources, catalogs, artifacts, receipts,
   supersession populations, and observation times. It never trusts the copied
   mapping or an in-memory fixture world.

No behavior or classification authority may be created and consumed by the same
candidate commit. Reclassification is a new ID that explicitly supersedes its
predecessor; historical source, decisions, receipts, and transition subjects
remain immutable. The empty live behavior catalog blocks all 134 direct
top-level baseline files until real governed authorities are created. Synthetic
positive fixtures are labeled `CONTRACT_SATISFIABILITY_ONLY`, live outside all
canonical source roots, and are rejected if presented as repository/runtime
authority.

Disposition-state arrays are bytewise `old_path`-sorted
`{old_path, old_content_sha256, disposition, migration_group_id, proof_id,
deletion_id, destination_test_ids}` rows; initial rows use `INHERITED` and null
record/group/deletion fields. A migration derives `MIGRATED`; an accepted
legacy-source deletion derives `RETIRED`. Resulting-snapshot arrays are bytewise path-sorted
`{path, mode, content_sha256}` rows. The ordered-migration subset is sorted by
group sequence/member index and contains
`{migration_group_id, transition_sequence, predecessor_transition_id,
group_member_index, proof_id, exact_subject_digest}`. Their canonical-JSON
SHA-256 values are the only derivations for the corresponding digest fields.
`migration_transition_count` counts complete groups, not member records.

Every member retains its immutable member subject, but all group-level
behavior, built-artifact, checker, gate, review, and owner-decision artifacts
bind the one canonical group `LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2`
ref/digest. That digest includes both complete Git snapshot digests and the
member manifest; `after_tests_snapshot_digest` is a field of the transition,
not an alternate evidence subject. Each member stores the identical group
subject ref/digest and member-manifest digest. The successful group's
`LandingRecord` also binds that same transition subject and verifies the exact
member-record candidate manifest.

The cutover's artifacts and `LandingRecord` similarly bind only the one
`LEGACY_TEST_CUTOVER_SUBJECT_V2` whole-event subject. Its
`resulting_test_snapshot_digest` is one field, not the subject digest itself.
An exact subject is computed before artifacts and decisions and excludes their
references, avoiding circular approval.

All evidence and acceptance fields use ADR-0008 `TypedArtifactRefV1` objects.
Bare strings are invalid. Minimum noncompensating classes are:

- change authorization: one exact-subject `EvidenceSnapshot`, qualified
  maintenance `CheckerResult` set, `PASS` `GateEvaluation`, authenticated
  change-approver `HumanDecisionRecord`, and `ACCEPTABLE` independent
  migration `ReviewVerdict`;
- migration: behavior and built-artifact `EvidenceSnapshot` records, qualified
  ADR-0008, architecture, destination-marker, and residual-reference
  `CheckerResult` records, one `PASS` migration `GateEvaluation`, distinct
  authenticated compatibility/migration/process-assurance owner decisions,
  and one eligible independent migration verdict;
- legacy or canonical retirement: ADR-0008's required retirement snapshot,
  removal/cleanup/successor-or-N/A checkers, `PASS` retirement gate, owner and
  process-assurance decisions, and independent verdict; and
- cutover: one whole-subject evidence snapshot, qualified runner/import/config,
  destination-lineage, ADR-0008, architecture, zero-legacy, and registry
  closure checkers, one `PASS` cutover gate, the three owner decisions, and one
  independent cutover verdict.

The canonical artifact resolver enforces type, bytes/digest, subject
schema/ref/digest, producer, checker/evaluator/route qualification, complete
claims/coverage, required `PASS` or `ACCEPTABLE` outcome, independent-review
eligibility, authentication and exact owner role/scope, chronology, freshness,
expiry, revocation, and absence of missing/conflicting claims. Missing,
dangling, wrong-subject, stale, unauthorized, unqualified, self-asserted, or
forged references such as `["x"]` are blocking `UNKNOWN`, never `PASS`.
`landing_record_ref` remains a preallocated opaque `landing_<uuidv7>` ID and
resolves separately as `LandingRecord`; no evidence artifact can substitute
for it.

Once landed, active/accepted record bytes are immutable. Closing, revoking, or
expiring a change exception removes it from the active source directory in a
governed commit only after the bytes revert or the baseline file has an
accepted migration record; Git history and immutable landing evidence retain
the old record and digest. A correction uses a new record ID and governed
replacement commit rather than editing an accepted record. Migration and
cutover/removal records remain exact-subject evidence; a changed subject makes
them stale rather than silently current. A cutover record freezes its event-time
ledger, lineages, and `tests` snapshot, not all future canonical test bytes.
After it lands, ordinary ADR-0008-governed canonical edits, renames, successor
retirements, and additions may proceed without rewriting historical cutover
proof. Current validation still independently requires zero legacy paths or
active legacy exceptions, no retired-ID reuse, and valid current lineage
terminals; a later recontamination or broken lineage blocks without mutating
the historical record.

Every active/accepted record requires the exact transition/path subject, typed
owner decisions, typed independent review and qualified evidence, successful
landing, chronology, and source digest required by its schema and registry
entry. The validator loads
`legacy-test-layout-records-v2.json`, verifies it against the source records, and
then evaluates the current test snapshot. An unused/standing change exception,
a proof for a still-present old file, or a cutover/removal record whose
independently recomputed conditions do not pass is a blocking failure.

## Exact inherited directory exceptions

The common values repeated in every projected row are:

```yaml
row_policy:
  allowed_inherited_scope: "EXACT_BASELINE_FILES_ONLY"
  change_exception_scope: "IN_PLACE_CONTENT_ONLY_ON_EXISTING_BASELINE_PATH"
  legacy_addition_policy: "FAIL_REQUIRES_SUPERSEDING_ADR"
  move_rename_policy: "CANONICAL_DESTINATION_WITH_MIGRATION_PROOF_ONLY"
  compatibility_owner: "compatibility"
  migration_owner: "migration"
  test_governance_owner: "process_assurance"
  migration_trigger: "FIRST_PATH_OR_CONTENT_CHANGE_OR_RANEX_DEPENDENCY_TOUCH"
  expires_at: "2026-10-31T23:59:59Z"
  removal_proof_profile: "LEGACY_TEST_MIGRATION_PROOF_V2"
```

Every row below incorporates that policy by `row_policy_ref`; the executable
projection expands the common values into each row and rejects a missing or
different value.

```yaml
directory_exceptions:
  - {exception_id: "LEGACY-TEST-ROOT-001", legacy_root: "tests/acp", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 15, subtree_oid_sha1: "4debc8c4754d4f835afbf18b1eea90abdf0f84d4", ls_tree_listing_sha256: "ff94065b1d8f24ac8d9198ed97cdb26015ca2db402a320522e152ebfa4f98b05", destination_root: "tests/contract/agent_collaboration/acp", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-002", legacy_root: "tests/acp_adapter", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 3, subtree_oid_sha1: "43091c091473f7d3bfdcb07134a1eda790e1df80", ls_tree_listing_sha256: "6a3aacb896580c8b2f00c9a38eccece250ae156e19ac5bcbeb645a420f14a90b", destination_root: "tests/integration/agent_collaboration/acp_adapter", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-003", legacy_root: "tests/agent", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 315, subtree_oid_sha1: "c17c4c0e1192bd1d640d3ee8fcd4883affa65139", ls_tree_listing_sha256: "7f4e0c1e814b66c1f2a94afff903dfb09afbbe91c8476cfe8caa23a88b865889", destination_root: "tests/system/agent_collaboration/agent", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-004", legacy_root: "tests/ci", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 8, subtree_oid_sha1: "1db247587d6bd6772c2d92c498d3737e90aefb20", ls_tree_listing_sha256: "871807a9eeb28b79e1e9bdbb67a428a508712f1e12704b65f3972cd4b9ae0aaf", destination_root: "tests/qualification/release_management/ci", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-005", legacy_root: "tests/cli", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 96, subtree_oid_sha1: "96ce43b104e7d98bc98fe3113b4471ae99ab759c", ls_tree_listing_sha256: "443162068aa1dbdace2ceb35627702b3fd99b48f1758edb0c26420ceee7c27a2", destination_root: "tests/acceptance/extension_host/cli", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-006", legacy_root: "tests/computer_use", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 8, subtree_oid_sha1: "74f904dd350592eef564d72fb2657e093c729e04", ls_tree_listing_sha256: "2aff6cdd836ce164557d0862a02b6d1b3605f47d2eeb9033f5bad5474bb931ca", destination_root: "tests/e2e/extension_host/computer_use", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-007", legacy_root: "tests/conformance", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 6, subtree_oid_sha1: "8351d5593874e55409a08008ddd3a51bcaddc442", ls_tree_listing_sha256: "db3d51fc6fb9a26c71fd878126d0514cf9e41fb509ef91fe3345b29cd001ae6d", destination_root: "tests/contract/assurance/conformance", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-008", legacy_root: "tests/cron", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 36, subtree_oid_sha1: "491e11d2530e8a33e824ea957ad64c09db258941", ls_tree_listing_sha256: "94f36e363cddc9abd85948cf966167a9519ae8c90db73b14faee31bcfb055731", destination_root: "tests/integration/scheduling/cron", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-009", legacy_root: "tests/dashboard", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 1, subtree_oid_sha1: "b26af98563b798fcc41da418d98d2778f13720d4", ls_tree_listing_sha256: "aca540a5bc545bf2140661b482e0a54ff147a50bd3db76fae039935045ba481f", destination_root: "tests/e2e/interaction_history/dashboard", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-010", legacy_root: "tests/docker", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 27, subtree_oid_sha1: "aa6bca1a5feec5a20d3638673714e7b3a0ce9cac", ls_tree_listing_sha256: "2928617cc88446f8c235ecb0e341edc05ba10bc255265b766d3aecaa4cb903a5", destination_root: "tests/system/operations/docker", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-011", legacy_root: "tests/fakes", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 2, subtree_oid_sha1: "955d34abc0ad269e9a409b2de64bc6c99b559fec", ls_tree_listing_sha256: "0662075f43c1629ac09ee4f05083713d870a1845c738c64ce9d30237116b7d45", destination_root: "tests/fixtures/compatibility/fakes", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-012", legacy_root: "tests/fixtures", exception_kind: "SEMANTIC_LAYOUT_ONLY", file_count: 2, subtree_oid_sha1: "aaaac398f04c07c7fd39f18620ec5552f36deb06", ls_tree_listing_sha256: "1160260a38ae1b6ac4d48e3bc21ce76fc4273dd928a2078e52ce8e36a92f5385", destination_root: "tests/fixtures/compatibility/inherited", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-013", legacy_root: "tests/gateway", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 557, subtree_oid_sha1: "0efcf8d04dad4a8386a75d411c4d545c315dfa11", ls_tree_listing_sha256: "4b4f356cb24b6933f9084de2ed2b20f7cef306b45786c63a3a5d91f9ba353c71", destination_root: "tests/integration/extension_host/gateway", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-014", legacy_root: "tests/hermes_cli", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 499, subtree_oid_sha1: "477f2fb0c8fb504133be29833b277a6534fd5bd6", ls_tree_listing_sha256: "ddf97954a83874b01acbfbdcfe1847f232ceb565fcd4f0d7b1215a21282486ac", destination_root: "tests/integration/extension_host/hermes_cli", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-015", legacy_root: "tests/hermes_state", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 8, subtree_oid_sha1: "ddd90b68b7e43cf5e347bfa5eaa68f2e938e8947", ls_tree_listing_sha256: "9ac8c6eeef19580ded5b9443cb924ab4cd05ba0301a0ff7aba6d87d630143dcb", destination_root: "tests/replay/compatibility/hermes_state", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-016", legacy_root: "tests/honcho_plugin", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 10, subtree_oid_sha1: "22953261708e839af65c1f26255ecc250c349e82", ls_tree_listing_sha256: "21b601f82530dafaa564e281abe0e2363885458e8772f598c16dbfa30d82dbda", destination_root: "tests/contract/extension_host/honcho_plugin", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-017", legacy_root: "tests/manual", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 2, subtree_oid_sha1: "c3838a5d3610fea85caa91e327bb409ee612072d", ls_tree_listing_sha256: "acccc78e0427de740b0689b95c827dfc824c12f896b3f8b9fb446a890de9dea4", destination_root: "tests/evaluation/compatibility/manual", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-018", legacy_root: "tests/openviking_plugin", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 1, subtree_oid_sha1: "5d6272eee28ae7e0d2d373662cccbbc53f1f9e36", ls_tree_listing_sha256: "f06101f4d62eebadd29ea2eabed26e8c56bbe16c6831ed6fd73c2d1bcfcdcfb5", destination_root: "tests/contract/extension_host/openviking_plugin", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-019", legacy_root: "tests/plugins", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 90, subtree_oid_sha1: "d4aec647eaf6056fd5105ae18540d26cf40ac100", ls_tree_listing_sha256: "64021258c16f0b9ff8027e972f3bb53e3c114b5366c3ecfc2db255778b3fdc6b", destination_root: "tests/contract/extension_host/plugins", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-020", legacy_root: "tests/providers", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 7, subtree_oid_sha1: "e378ca4bd7f855441bb26cf7c53cd48ac3bcb626", ls_tree_listing_sha256: "f8f8e7f07685898cb55d9a163163027d1020c5ecbd7d513a36dfd1f8f907a282", destination_root: "tests/contract/supplier_governance/providers", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-021", legacy_root: "tests/run_agent", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 159, subtree_oid_sha1: "51858d26b684c7bc7132c5150a0235db6c2ef79d", ls_tree_listing_sha256: "50b3abb2c02f8add9fd61d5fb8f33ab293890d9e51e67c80b98a2976bc197ec7", destination_root: "tests/system/agent_collaboration/run_agent", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-022", legacy_root: "tests/scripts", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 3, subtree_oid_sha1: "22f42650e7be22719b731fd56a50ae4b6396cbed", ls_tree_listing_sha256: "d246952d800c2a13e6972e7fe0acb31b266ab2e2f7b2f24e6ea4bd93b7b1459a", destination_root: "tests/operations/operations/scripts", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-023", legacy_root: "tests/secret_sources", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 5, subtree_oid_sha1: "debc97745b1fa0deac7bc88896d284630b93b324", ls_tree_listing_sha256: "5b956a40fccdf58275d4af38398b44f0a513daf4f66160aa656d0d57ee14914a", destination_root: "tests/security/identity_access/secret_sources", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-024", legacy_root: "tests/skills", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 19, subtree_oid_sha1: "13487bec9b1b6912cd8505cecb535314a4cc7075", ls_tree_listing_sha256: "32e503118419108d3e50a8455761846eaf44e81c6f06958013c67d4e0f9da769", destination_root: "tests/contract/instruction_registry/skills", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-025", legacy_root: "tests/state", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 2, subtree_oid_sha1: "878b4d385f95ef83f2984db462b96bc9da5818d9", ls_tree_listing_sha256: "e5f10bcfdfb2ab7d9ef47a5ef8754af4b3e547162399eb2c955d9aba88e6065f", destination_root: "tests/replay/compatibility/state", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-026", legacy_root: "tests/stress", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 11, subtree_oid_sha1: "cf5a9ea67f0e2d8da3299219ddc2f817e4e5a6e5", ls_tree_listing_sha256: "1cf809d312fa19c5cb9fa48e64237c8b40cd382c412e1aadba76906ab3a7c275", destination_root: "tests/performance/process_assurance/stress", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-027", legacy_root: "tests/tools", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 354, subtree_oid_sha1: "fefd09674ce53fefb54a6e3014f1c0d1c4a6850c", ls_tree_listing_sha256: "2d32b2d70debdab819154dc96e59b4d00b9a25959fdc2dbde040735475c9446d", destination_root: "tests/contract/extension_host/tools", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-028", legacy_root: "tests/tui_gateway", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 45, subtree_oid_sha1: "6921c4fbe35517c87b75706bfc99f47939d49c75", ls_tree_listing_sha256: "3b939602269ccfcd36d5b5e367860f6ee7b5b1b6c2ce407f3e8170441bd057cc", destination_root: "tests/integration/extension_host/tui_gateway", row_policy_ref: "row_policy"}
  - {exception_id: "LEGACY-TEST-ROOT-029", legacy_root: "tests/website", exception_kind: "PATH_AND_SEMANTIC_LAYOUT", file_count: 3, subtree_oid_sha1: "024427185d6c8b791369210d9cbc927fca69f980", ls_tree_listing_sha256: "79d86cc4ec561fe1c7c949995e08d00400b0cbd4200b3e8333a6b349fd36a6c0", destination_root: "tests/e2e/extension_host/website", row_policy_ref: "row_policy"}
```

`tests/fixtures` is included because its name is canonical but its two
inherited files lack the ADR-0008 owner and semantic placement contract. Its
exception is semantic only; the canonical root itself remains allowed.

## Direct top-level and inherited canonical scopes

```yaml
direct_top_level_exception:
  exception_id: "LEGACY-TEST-TOPLEVEL-001"
  legacy_root: "tests/"
  match: "direct files only"
  file_count: 134
  ls_tree_listing_sha256: "a2e6b50f2dc3deebc19d56911aa708a3b97be4de6c77e4943bcb7b1c9b3e2600"
  allowed_inherited_scope: "EXACT_BASELINE_FILES_ONLY"
  change_exception_scope: "IN_PLACE_CONTENT_ONLY_ON_EXISTING_BASELINE_PATH"
  legacy_addition_policy: "FAIL_REQUIRES_SUPERSEDING_ADR"
  move_rename_policy: "CANONICAL_DESTINATION_WITH_MIGRATION_PROOF_ONLY"
  destination_rule: "classify each file by behavior into one ADR-0008 root and owning context"
  compatibility_owner: "compatibility"
  migration_owner: "migration"
  test_governance_owner: "process_assurance"
  migration_trigger: "FIRST_PATH_OR_CONTENT_CHANGE_OR_RANEX_DEPENDENCY_TOUCH"
  expires_at: "2026-10-31T23:59:59Z"
  removal_proof_profile: "LEGACY_TEST_MIGRATION_PROOF_V2"

inherited_files_already_under_canonical_roots:
  - {scope_id: "LEGACY-TEST-CANONICAL-E2E-001", root: "tests/e2e", file_count: 7, subtree_oid_sha1: "894f4e84d1aa50196d2f3b5fdf3fbea4f4742011", ls_tree_listing_sha256: "4dedd8ace95440fb3293c3f27a978a4b5ac2c2a400ad409438d7dfb57324fbb4", evidence_status: "INHERITED_BASELINE_NOT_RANEX_PROOF"}
  - {scope_id: "LEGACY-TEST-CANONICAL-INTEGRATION-001", root: "tests/integration", file_count: 9, subtree_oid_sha1: "cdcd82d213be4e4d875f2f066b91927676aa5130", ls_tree_listing_sha256: "d03247de37b3f51d0f076c43f0ffa4395397ad115ad9622e3683f7d18915b512", evidence_status: "INHERITED_BASELINE_NOT_RANEX_PROOF"}
```

The 16 already-canonical files receive no path exception. They remain
byte-bound inherited files, so they cannot be counted as Ranex TDD or gate
evidence merely because their top-level root is allowed.

## Change, migration, expiry, and removal proof

A maintenance change to an existing exact baseline path is exceptional. Before
landing, it needs a
`LEGACY_TEST_CHANGE_EXCEPTION` containing the exact baseline file, before and
after content digests, defect/security rationale, affected exception/scope ID,
compatibility and migration owners, independent migration reviewer, expiry,
canonical destination, and replacement plan. It may preserve inherited
behavior while the strangler exists; it cannot add Ranex behavior or silently
increase the grandfathered set. It authorizes only different bytes at the same
one of the 2,444 baseline paths; it never authorizes an added, moved, or renamed
path. A newly added file in a legacy or direct
top-level scope is always a blocking violation: it needs a recorded finding
and migration review, but no exception record can authorize it. Changing the
immutable baseline itself requires a human-approved superseding ADR.

A move or rename must remove the old baseline path and land the replacement
only below an ADR-0008 canonical root under
`LEGACY_TEST_MIGRATION_PROOF_V2`. A temporary second legacy path is expansion
and fails even when the old path still exists.

An inherited file is migrated only when an immutable
`LEGACY_TEST_MIGRATION_PROOF_V2` record provides:

1. exact old path/blob/content digest and exception/scope ID;
2. exact nonempty new canonical test IDs and paths;
3. behavior-equivalence evidence;
4. proof that the destination tests exercise the built production artifact;
5. passing applicable ADR-0008 and architecture checks for the exact subject;
6. no remaining imports, runner configuration, fixture references, or
   documentation links to the old path;
7. deletion of the exact inherited file from the grandfathered set; and
8. independent migration review plus compatibility, migration, and
   process-assurance owner acceptance.

Direct intentional retirement instead requires one accepted
`TestDeletionRecordV1` with `target_kind: LEGACY_SOURCE`; later deletion of a
migrated canonical test requires `target_kind: CANONICAL_TEST`. Both use the
single ADR-0008 authority and its exact Git, trace, cleanup, lineage, typed
evidence, review, decision, and landing rules. A migration
`retirement_rationale`, empty destination, or prose approval has no authority.

Expiry is nonrenewable and cannot be laundered by post-expiry work. Every
change landing, migration landing, required cutover owner acceptance, and
cutover landing must complete on or before 2026-10-31T23:59:59Z, in addition
to any earlier per-record expiry. The validator first derives all dispositions,
active exceptions, lineages, and cutover result. After that instant, any
not-yet-complete migration, still-`INHERITED` row, active change exception, or
missing/failing/not-yet-landed cutover blocks construction verification until a
human-approved superseding ADR and policy version establish a new
evidence-bound decision. Post-expiry baseline migration followed by a
post-expiry full cutover cannot cure the lapse. Only a fully completed,
independently recomputed, owner-accepted and successfully landed
`LEGACY-TEST-CUTOVER-001` whose acceptance and landing occurred by expiry
remains valid historical proof afterward. An individually expired change
exception never authorizes its bytes, before or after cutover.

`LEGACY-TEST-CUTOVER-001` passes only when all 29 directory exceptions and the
direct-top-level exception are closed, every inherited canonical file is
migrated or intentionally retired through the one deletion authority, all
2,444 baseline rows have one complete
disposition, no runner/import/configuration reference depends on a legacy
layout, destination tests and applicable gates pass for the exact built
subject, every migrated destination lineage terminates in one current unique
active marker or a governed retirement terminal, the accepted cutover event
and landing bind that exact evidence by expiry, and the validator reports zero
legacy exceptions. A cutover record cannot override event-time or current
recomputation. A count decrease alone is not cutover proof.

## Noncompensating rules and fitness functions

| Rule ID | Blocking obligation |
|---|---|
| `LEGACYTEST-BASELINE-001` | Full tree, command output, 2,444 file rows, partition, modes, blob OIDs, and byte digests match the immutable baseline. |
| `LEGACYTEST-ROOTSET-001` | Exactly the 29 contiguous directory exception IDs and their complete row bindings exist. |
| `LEGACYTEST-TOPLEVEL-001` | Exactly the 134 direct baseline files are grandfathered; no new direct test file exists. |
| `LEGACYTEST-NOEXPAND-001` | No inherited root, file set, or semantic exception expands or recontaminates a closed scope. |
| `LEGACYTEST-CHANGE-001` | Every legacy/direct-scope addition fails as recontamination; only the exact active instance head can authorize in-place bytes at an existing baseline path; every move, rename, or deletion uses canonical migration proof. |
| `LEGACYTEST-CANONICAL-001` | New Ranex tests use only the 18 roots and inherited canonical files are not promoted into Ranex proof. |
| `LEGACYTEST-MIGRATION-001` | Each source is disposed once by either a complete accepted immutable MIGRATED-only atomic group with canonical destination lineage or the sole accepted `LEGACY_SOURCE` deletion authority; events have exact derived-before ledgers and named-only deltas with no residual reference. |
| `LEGACYTEST-EXPIRY-001` | Every change/migration/cutover acceptance and landing completes by policy expiry; post-expiry unfinished scope/cutover blocks, while only a by-expiry complete accepted cutover remains valid historical proof. |
| `LEGACYTEST-CUTOVER-001` | Cutover is claimed only when its immutable event-time subject, typed evidence/decisions, successful by-expiry landing, and independently recomputed event/current complete gate all pass. |
| `LEGACYTEST-NONCOMP-001` | A pass, score, count, or improvement elsewhere cannot offset any failed, unknown, conflict, or expired row. |

| Fitness ID | Required check |
|---|---|
| `FF-LEGACYTEST-001` | Reproduce the complete tree/listing/file-manifest bindings and reject any mismatched byte. |
| `FF-LEGACYTEST-002` | Prove the exception set is exactly `001..029`, with no duplicate, gap, missing field, or extra root. |
| `FF-LEGACYTEST-003` | Diff current paths/blobs/content against the baseline and fail unregistered expansion, drift, or recontamination. |
| `FF-LEGACYTEST-004` | Reject any new direct `tests/*` file and verify the exact top-level baseline scope. |
| `FF-LEGACYTEST-005` | Route every nonbaseline new test to one of the 18 canonical roots and keep inherited canonical evidence nonsealing. |
| `FF-LEGACYTEST-006` | Validate committed-tree source/digest/lifecycle, exact derived-before ledger and named-only delta, path-local change subject, baseline-or-latest-authorized source state and one-time cleaned closure, atomic ordered MIGRATED-only group, destination/classification, immutable Git event, current ACTIVE/RETIRED lineage, typed artifacts/roles, chronology, residual scan, and exact subject. Execute the exact behavior/direct-classification authority matrix (+3/-44) and scope matrix (+4/-17), including catalog/source bijection, taxonomy branch/mirror, six row/registry digests, decision/landing/sealing chronology, supersession, synthetic/live separation, and mandatory real change and migration call paths. Positives include authorized maintenance then closing migration, direct legacy-source retirement, migrate→retire, migrate→successor, two causal migrations, later canonical edit/rename, and one-group many-to-one consolidation. Negatives include unrelated event delta or disposed reintroduction; missing/ambiguous/expired prior state; dangling/wrong/multiple/reused closure or ID; forged `["x"]`, wrong-subject/stale/unqualified evidence; duplicate/unaccounted source; wrong destination; cross-group/retired test-ID reuse; wrong/missing commit; noncausal landing; resolver omission; catalog/row/source drift; and absent/duplicate/cyclic lineage. |
| `FF-LEGACYTEST-007` | Reject post-expiry baseline migration and post-expiry full cutover; prove only a cutover whose owner acceptance and landing completed by expiry remains valid historical proof afterward. |
| `FF-LEGACYTEST-008` | Exercise event-time and current cutover with exact valid resolver/landing positives and missing disposition, forged retirement, stale/dangling/wrong-subject/unqualified evidence, failing lineage/destination, dirty-checkout, later recontamination, and count-only negatives; prove ordinary later canonical evolution does not stale historical cutover. |
| `FF-LEGACYTEST-009` | Prove one failed/unknown/conflict/expired legacy-test rule keeps the aggregate nonsealing. |

The ten rule assessments are separate rows in
`architecture-rule-assessments.json`; all start `NOT_ASSESSED`. No aggregate
score has independent `PASS` authority.

## Engineering-reference application and limits

| Practice ID | Applied use and strict limit |
|---|---|
| `ENGREF-PRAGMATIC-PROGRAMMER-1E-TRACER-ROUTE` | Preserve a runnable inherited characterization path while replacing behavior in thin, observable slices; an inherited test is not proof that the new architecture works. |
| `ENGREF-CLEAN-ARCHITECTURE-1E-DEPENDENCY-RULE` | Move tests toward owning boundaries and public behavior; folder relocation alone cannot prove dependency direction. |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS` | Continuously detect expansion, drift, expiry, and incomplete cutover; a one-time green scan is not sustained conformance. |

## Alternatives considered

1. **Delete or bulk-move all inherited tests now.** Rejected because it would
   erase characterization evidence and create unmeasured sync and regression
   risk.
2. **Grandfather every current path indefinitely.** Rejected because it would
   nullify ADR-0008 and invite recontamination.
3. **Treat current test counts or passing executions as migration proof.**
   Rejected because counts and outcomes do not bind ownership, destination,
   dependency direction, subject identity, or residual references.
4. **Exclude canonical `e2e` and `integration` files from the baseline.**
   Rejected because path compliance does not transform inherited evidence into
   Ranex construction evidence.

## Consequences and approval standing

Construction may preserve and run the exact inherited baseline while the
strangler is active, but clean-base architecture validation remains blocked
until this ADR is projected and its fitness checks enforce the policy.
Migration then proceeds file by file without either a big-bang rewrite or an
unbounded waiver.

The human owner accepts this bounded coexistence decision. The decision does
not claim that any inherited test was migrated, any test passed, or any runtime
exists, and it does not declare either ADR-0012 readiness tier. This paper
decision is an input to `IMPLEMENTATION_START_READY`; inherited migration and
runtime evidence remain `NOT_ASSESSED` and block the applicable
`PRODUCTION_READY` gates.
