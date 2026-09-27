# SLICE-100 — Delegated review as the bound command

**Status:** done
**Issue:** #102
**ADR:** docs/adr/ADR-069-delegated-review-packet-sarif.md

## Contract

A review claim binds an argv that consumes a deterministic packet
(`governance/review-packet.json`: subject digest, frozen range SHAs,
handbook digest + chapters) and writes SARIF 2.1.0 carrying
`properties.packet_digest`. Admission is the #97 path with captain
invariants: re-derive anchors from the verbatim excerpt; prose-free
fingerprints; packet substitution refused; unresolvable anchors = absence.
Findings are advisory — not in default `required_claims`. No worker key;
`verdict.py` unchanged.

## Boundaries

Not #105 (OCR as subject). Not making model findings required. Not LLM
reflection as PASS/FAIL. No new runtime deps.

## Validation

`tests/unit/test_delegated_review.py`; field proof
`tools/dogfood/delegated_review_proof.py` →
`tools/dogfood/audits/2026-09-27-delegated-review/`.
