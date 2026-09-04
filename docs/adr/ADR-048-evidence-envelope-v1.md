# ADR-048 — Evidence Envelope v1: evidence binds the policy it was produced under

**Status:** accepted
**Date:** 2026-09-04
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-081-evidence-envelope-v1.md`

## Context and Problem Statement

An evidence record binds what ran (`command`, `command_digest`,
`executable_path`), what it ran against (`subject_digest`), who ran it
(`producer_id`), how it was confined (`confinement_profile_digest`,
`confinement_result_digest`), and what happened (`exit_code`,
`suite_results`). Ten signed fields, `ranex-evidence-v4`.

It does not bind **the rules it was produced under**. Neither `gate_id` nor
`catalog_digest` is in the record, so nothing stops evidence produced for one
gate catalog from satisfying a gate evaluated under a different one.

The attack needs no forged signature and no changed subject. Run the suite
honestly, get green signed evidence, then edit `governance/gates.yaml` — drop
a required claim, point a claim's `command` at something weaker — and evaluate.
The old evidence still verifies, still matches the subject, and now satisfies
a rulebook it was never produced under. `catalog_digest` is already bound in
the *approval* envelope (`foundation/approval.py`) and in the *verdict* record
(`verdict_signing.py`); evidence is the one link in the chain that omits it.

The subject binding is not a substitute. It answers "was this evidence produced
for this code", which is what the published attack demonstration exercises. It
cannot answer "was this evidence produced under this rulebook", and those are
different questions with the same shape.

## Decision Drivers

- Evidence must carry the policy context it was produced under, signed.
- Changing the rulebook must invalidate evidence produced under the old one.
- A v4 record must be refused, never accepted as a downgrade.
- `evaluate()` must not move. Policy comparison is an admission-layer concern.
- Refusal must be reported as structured data, distinguishable from absence.

## Prior art

- Searched: in-toto link metadata and layout expectations, SLSA provenance
  `buildDefinition`, Sigstore bundle media types, and TUF targets metadata,
  for how each binds a produced artifact to the policy in force.
- SLSA provenance binds `buildDefinition.externalParameters` into the signed
  predicate, so a build's declared inputs travel inside the signature rather
  than beside it. That is the shape adopted here for `gate_id` and
  `catalog_digest`. Rejected as a format: the predicate is open-schema, and
  this repository's canonical-JSON and exact-field-set discipline (ADR-025)
  refuses open shapes at the signing boundary.
- in-toto's `expected_command` is advisory: a verifier may warn and proceed.
  Refused explicitly. `refuse_executables_inside` already exists because a
  field nothing re-checks is decoration, and the same reasoning governs the
  policy fields added here.
- Media types follow the local precedent in `verdict_signing.PAYLOAD_TYPE`
  rather than Sigstore's bundle types, because the record is self-describing
  in canonical JSON and carries no detached bundle.

## Considered Options

1. Additive optional fields, compared when present: rejected. An attacker
   omits them and the comparison never runs. Absence must block, so the
   fields must be inside the exact signed set.
2. Bind the catalog digest only, not the gate id: rejected. One catalog
   defines many gates; evidence for gate `landing` must not satisfy gate
   `release` merely because both were read from the same bytes.
3. Bump the domain to `v5`, extend the exact signed set, and compare at
   admission: chosen.
4. Move `gate_id`/`catalog_digest` onto the kernel `Evidence` dataclass so
   `evaluate()` compares them: rejected. It moves the kernel for a check that
   does not need it, and the executable-containment precedent already shows
   how a record-level policy refusal is taken outside the kernel and reported
   through the same structured `Rejection`.

## Decision Outcome

`EVIDENCE_DOMAIN` becomes `ranex-evidence-v5`. `SIGNED_FIELDS` gains three:

- `envelope_type` — the constant `ranex-evidence-envelope-v1`. The domain
  prefix already versions the bytes; this makes the record self-describing on
  disk, so a JSON consumer reads what it is holding without inferring it from
  a signature it cannot check. Same discipline as `policy-capabilities-v1`
  (ADR-030) and `verdict_signing.PAYLOAD_TYPE`.
- `gate_id` — the gate the run was performed for. `run` already takes
  `--gate`, so nothing new is plumbed.
- `catalog_digest` — `sha256:` over the exact gate-catalog bytes, computed by
  the existing `catalog_digest_for`, from the committed bytes `run` already
  reads. When no catalog is committed it is the sentinel `catalog-absent`,
  and `gate_id` on an attestation produced for no gate is `gate-absent`.

### Absence is recorded, not refused

The first implementation refused inside `run` when no committed catalog was
present. That was wrong twice over. `run` is not only the gating path — the
observability, trace and confinement suites exercise it with no catalog at all
— so refusing broke recording for reasons that have nothing to do with policy.
And it put the block in the wrong place: in this repository absence blocks at
the *verdict*, which is where ADR-011 put it.

So a record with no catalog says so. `catalog-absent` never equals a live
catalog digest, so such a record is refused at `gate evaluate` by the same
comparison that refuses a foreign one, naming what is missing. A placeholder
`sha256:` would have been worse than either: a well-formed digest that names
nothing is a lie no verifier can detect.

Comparison happens in `refuse_foreign_policy_context`, beside
`refuse_executables_inside` and for the same stated reason: the decision needs
a repository and a live gate, and the domain does not reach for either. It
reads the raw records rather than admitted `Evidence`, so no kernel field is
added and `KERNEL_DIGEST` does not move.

Two new refusals, both structured:

- `POLICY_CONTEXT_MISMATCH` — the record names a different gate or a different
  catalog than the one being evaluated.
- `UNSUPPORTED_ENVELOPE` — the record is v4-shaped: it carries the ten old
  fields and none of the three new ones. Reported distinctly rather than as
  `MALFORMED_RECORD`, because "this is evidence from before the envelope
  changed" and "this is not a record at all" are different events, and an
  operator investigating the first should not be told the second.

### Consequences

- Every existing signed record is invalid. `governance/evidence.json` is
  gitignored and regenerated by `run`, so nothing committed carries v4 bytes;
  test fixtures that build records by hand move with the field set. That churn
  is the point of an exact signed set and is not a reason to soften it.
- A v4 record and a v5 record never verify as each other: the domain differs,
  and `signed_payload` refuses a content mapping that is not exactly the
  signed set, so a downgrade cannot be spelled.
- Editing `governance/gates.yaml` after a green run now invalidates that run's
  evidence. This is intended and is the property the slice exists to add. It
  also means a catalog edit requires a re-run, which is the honest cost.
- The envelope still carries no anti-replay context: no nonce, no journal head
  anchor. SLICE-082 owns that, and the Week 2 objective is not met by this
  decision alone. Recorded here so the gap is not mistaken for closed.

### The frozen fixture this collided with, and the re-key

The approved-batch qualification artifact (SLICE-071) is signed with this
module's primitive and admitted through `admit`, so it moves with the envelope.
Its shape is pinned by `governance/schemas/specification/batch-qualification-v1.schema.json`,
whose digest is pinned by the descriptor, whose digest is pinned inside an
A/B/C triple signed under ADR-025 — **with a private key that is not in this
repository or anywhere in its history**. Those bytes could not be re-made, so
the frozen set hard-coded the v4 evidence shape and, as it stood, blocked any
future change to the envelope. That is a latent defect this slice uncovered
rather than created: it would have stopped the next such change too.

The fixture set is therefore re-keyed with a key the repository keeps, stored
beside the vectors as `fixture_private_key`. It is a test fixture and never a
trust root — `governance/producers.yaml` is untouched — and the whole digest
chain is recomputed from the files themselves and verified with
`validate_approval_envelope` before anything is written.

Two things that went wrong on the way, recorded because the second is the kind
of error a reviewer should look for. A first regeneration reconciled every
`{path, digest}` pair it could find, and so overwrote `published_v2_authority`
in the expected-values fixture — a record of digests **as of commit
6d8e690f**, which is meant to be historical and must not track current files.
It was reverted and redone naming each reference explicitly. The second: a
partial run left one file rewritten before a later guard refused, so the
regeneration now refuses to start unless every file it writes is clean.

### Confirmation

`tests/security/test_slice081_evidence_envelope.py` pins the attack: green
evidence, an edited gate catalog, and a refusal naming
`POLICY_CONTEXT_MISMATCH` rather than a PASS or a bare absence. It also pins
the downgrade refusal and that a v4 signature does not verify against v5
bytes. `tests/contract/test_kernel_unchanged.py` stays green with
`KERNEL_DIGEST` untouched, which is what proves the comparison stayed out of
the kernel.
