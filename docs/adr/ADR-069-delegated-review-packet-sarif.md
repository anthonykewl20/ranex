# ADR-069 — delegated review as the bound command: packet in, SARIF out

**Status:** accepted
**Date:** 2026-09-27
**Decision-makers:** repo owner
**Issue:** #102

## Context and Problem Statement

Issue #97 admitted SARIF 2.1.0 for deterministic scanners. Issue #100 injected
path-scoped handbook chapters into delegate briefs. What was still missing:
a review worker's findings entering the same evidence plane as a bound
command of `ranex run`, without a second signing surface, without promoting
model prose to a verdict input, and without trusting producer-supplied line
numbers.

The OCR steal report (captain hold on #102) proposed three contract
additions. The captain adopted all three; reflection-as-PASS/FAIL and new
runtime deps were rejected.

## Decision Drivers

- ADR-060 rules 3–4, 6: delegated work is the bound argv; model findings are
  never default `required_claims`; unresolvable anchors are absence.
- #97 reporter family: one reduction into the closed suite-summary.
- Captain rulings (binding): anchor re-derive; prose-free fingerprints;
  findings advisory-only.
- No new runtime dependency; `verdict.py` / `KERNEL_DIGEST` unchanged.

## Prior art

- `alibaba/open-code-review` SARIF fingerprints and anchor re-derivation
  (`sarif.go`, `resolver.go`) at the pin named by the OCR steal report —
  behaviour adopted, nothing vendored (Apache-2.0; MAP §15.3).
- ADR-060 / ADR-062 already voucher the packet and handbook shapes.

## Decision

1. **Packet.** A review binds a canonical packet
   `{subject_digest, range:{base,head}, handbook_digest, chapters}` written
   at `governance/review-packet.json`. Digests are `sha256:` over canonical
   JSON. Range SHAs are frozen 40-hex commits, never mutable refs.
2. **Admission.** When a SARIF run carries `properties.packet_digest`, the
   #97 normaliser re-derives the digest from the materialised packet file,
   refuses substitution, re-derives line numbers from the verbatim excerpt
   (producer `startLine` ignored), and fingerprints
   `sha256(path|category|excerpt[+occurrence])` — never message prose.
   Unresolvable excerpts refuse the artifact (absence).
3. **Advisory.** Default gate catalogs do not list a review claim under
   `required_claims`. Findings appear in `considered` when the claim is run;
   removing every model credential leaves the verdict unchanged when the
   claim is absent both ways. An operator who requires the claim knowingly
   relaxes that invariant and needs a separate ADR.
4. **Worker.** `python -m ranex.foundation.delegated_review` is the
   deterministic bound command for proofs; a live model worker is optional
   field evidence, not a second signing surface.

## Consequences

- Ordinary scanner SARIF (no `packet_digest`) keeps the #97 path unchanged.
- #105's OCR-as-subject arms can bind the same packet/admission contract.
- Live-model content remains non-deterministic; the admission path, packet
  digest and statuses must not be.

## Evidence

Unit: `tests/unit/test_delegated_review.py`. Field proof:
`tools/dogfood/audits/2026-09-27-delegated-review/` via
`tools/dogfood/delegated_review_proof.py`.
