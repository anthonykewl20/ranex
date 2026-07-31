# Owner-decision records

Canonical source root for `HumanDecisionV1` records that resolve rows in the
`ADR-0013` owner-decision register. Governed by
[`ADR-0017`](../../../docs/architecture/decisions/ADR-0017-record-resolved-owner-decisions.md)
`OWNER-RESOLVE-006`, on the same terms as
`architecture/records/test-governance/behavior-authorities/`.

**This directory is deliberately empty. It therefore grants nothing.**

## Rules

- Only canonical JSON files are eligible.
- Each file validates against
  [`schemas/authority/human-decision-v1.schema.json`](../../../schemas/authority/human-decision-v1.schema.json)
  — 22 required fields, including `principal_id`, `authentication_context_id`,
  `presentation_challenge_digest`, `nonce`, `issued_at`, `expires_at` and
  `digest`.
- Each record has exactly one byte-bound row in the register.
- A record must be authenticated, unrevoked, unexpired, and authorized for the
  exact role, action and scope of the row it resolves (`OWNER-RESOLVE-003`).

## How a row is resolved

1. Mint a `HumanDecisionV1` record here.
2. In `ADR-0013`'s marked YAML, set that row's `status` to `ACCEPTED` and its
   `owner_decision_ref` to `{artifact_type: human_decision, artifact_ref, artifact_digest}`.
3. Regenerate. `unresolved_owner_decision_count` derives downward on its own
   (`OWNER-RESOLVE-005`); it is never edited by hand.

Step 2 changes `ADR-0013`, whose source digest is bound in four tracked files.
**That cascade belongs to the resolution and is expected.** It is the cost of a
decision being recorded, not a defect.

## What resolution does not do

A resolved row's `runtime_validation_status` becomes `NOT_ASSESSED`
(`OWNER-RESOLVE-004`) — never `PASS`. Resolving a decision executes nothing.
