# SLICE-081 — Evidence Envelope v1

**Status:** open
**Opened:** 2026-09-04
**Priority:** P1 — Week 2 objective, second of three slices
**ADR:** docs/adr/ADR-048-evidence-envelope-v1.md
**Follows:** SLICE-080 (authenticated principals)

## Contract

Evidence binds the policy it was produced under, so a changed gate
catalog can no longer be satisfied by evidence produced under the old
one.

Acceptance:

- `EVIDENCE_DOMAIN` is `ranex-evidence-v5`; `SIGNED_FIELDS` gains
  `envelope_type`, `gate_id`, `catalog_digest`.
- `run` populates all three from what it already reads: `--gate`, and
  `catalog_digest_for` over the committed gate-catalog bytes.
- `gate evaluate` refuses a record naming a different gate or catalog
  with `POLICY_CONTEXT_MISMATCH`, and a v4-shaped record with
  `UNSUPPORTED_ENVELOPE` — both structured, neither reported as absence.
- `evaluate()` does not move. `KERNEL_DIGEST` untouched.

Out of scope, deliberately: nonce, journal head anchor, and any
approver-side signature. Those are SLICE-082, and the Week 2 objective is
not met by this slice alone.

## Owned paths

- Modify: `src/ranex/foundation/signing.py` — domain, signed set.
- Modify: `src/ranex/cli/main.py` — `cmd_run` populates the three fields;
  new `refuse_foreign_policy_context` beside `refuse_executables_inside`.
- Modify: `src/ranex/governed_execution/domain/admission.py` — two new
  `RejectionReason` members only.
- Tests: `tests/security/test_slice081_evidence_envelope.py` (new), plus
  the field-set migration across the suites that build records by hand.
- Governance: `governance/suite_manifest.json` re-freeze; golden refresh.
- Docs close-out: this slice to `docs/slices/done/`, `docs/STATE.md`,
  README completed-slices row.

Not touched: `verdict.py`, `principal_catalog.py`, `producer_keyring.py`.

## Order of work

Two green commits, because the second is only reviewable once the first
has landed.

1. **The envelope moves.** Domain, signed set, `cmd_run`, and every
   fixture that builds a record by hand. Evidence now *carries* policy
   context; nothing compares it yet. Suite green.
2. **The comparison lands.** `refuse_foreign_policy_context`, the two
   rejection reasons, and the attack tests. Suite green.

## Done criteria

1. Full suite green on the final commit.
2. `tests/contract/test_kernel_unchanged.py` green, `KERNEL_DIGEST`
   unchanged — proof the comparison stayed out of the kernel.
3. The attack test fails on step 1's commit and passes on step 2's.
4. Manifest re-frozen; `expected_skips` accounted for.

## Sad paths pinned

1. Green evidence, then an edited `governance/gates.yaml`, then evaluate
   — refused as `POLICY_CONTEXT_MISMATCH`, not PASS and not absence.
2. Evidence produced for gate `landing` presented to a different gate id
   in the same catalog — refused.
3. A v4-shaped record (ten old fields, none of the three new) — refused
   as `UNSUPPORTED_ENVELOPE`, distinctly from `MALFORMED_RECORD`.
4. A v4 signature over v5 content, and a v5 signature over v4 content —
   neither verifies. The domain differs and the field set is exact, so a
   downgrade cannot be spelled.
5. `envelope_type` carrying anything but the constant — refused.
6. A record whose `catalog_digest` is well-formed but names bytes that
   are not the committed catalog — refused.
7. The refusal names the record index a human must open, like every
   other rejection.

## Notes

The subject binding already answers "was this evidence produced for this
code" — that is what the published attack demonstration exercises. It
cannot answer "was this evidence produced under this rulebook". This
slice adds the second question; ADR-048 records why they are different.
