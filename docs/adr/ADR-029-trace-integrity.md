# ADR-029 — trace-reference integrity and independent verifier ports

**Status:** accepted
**Date:** 2026-08-16
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-033-trace-integrity.md`

## Context and Problem Statement

Approved A/B/C bytes identify a task, but a worker can still place a plausible
trace marker beside an unrelated change, alter a protected oracle, or claim a
new exemption. Trace references must therefore be independently checked against
the candidate tree and the signed manifest; trace coverage is not semantic proof.

## Decision Drivers

- Parse exactly one generated comment and sidecar grammar, without wildcards.
- Bind every anchor to A IDs, a B projection, and C's signed A/B identities.
- Refuse protected artifact or invocation drift before observing outcomes.
- Keep executable outcome observations separate from trace coverage.

## Prior art

- Searched: GitHub code search for in-toto artifact-rule verification, coverage
  report source filtering, diff hunk anchoring, and traceability matrices.
- [in-toto rule parser](https://github.com/in-toto/in-toto/blob/v2.3.0/in_toto/rulelib.py)
  validates a closed artifact-rule grammar before applying it.
  License: Apache-2.0.
  Weakness: its patterns intentionally support globs, which are authority
  widening and therefore forbidden for Ranex trace references.
  Vendored: docs/adr/prior-art/ADR-029/in-toto-rulelib.py blob:40802390de59b5db37809e6301e372bad89de69c
- [coverage.py report core](https://github.com/coveragepy/coveragepy/blob/7.10.6/coverage/report_core.py)
  applies include/exclude selection before rendering independent report data.
  License: Apache-2.0.
  Weakness: report selection is diagnostic and does not bind identities,
  signatures, or approved executable outcomes.
  Vendored: docs/adr/prior-art/ADR-029/coverage-report_core.py blob:9405f33f479a34291a70ae9d0a52db895ae4dee2
- Rejected: https://github.com/google/diff-match-patch Its fuzzy matching can
  relocate text after edits, whereas an approval boundary requires exact current
  paths and projections rather than best-effort correspondence.
- Rejected: https://github.com/sonar-scanner-engine/sonar-scanner-engine Its
  issue and coverage analysis is valuable diagnostics, but it has no C-signed
  exemption authority or explicit approved outcome input boundary.

## Considered Options

1. Exact parser plus independent tree verifier and outcome port: chosen.
2. Let workers classify behavior-bearing changes: rejected; it is an escape hatch.
3. Use fuzzy diff anchoring: rejected; moved text must require reapproval.

## Decision Outcome

The domain accepts only the generated Python/TypeScript comment form and the
closed `trace-sidecar-v1` JSON form. It compares every changed source hunk to
exact anchors or exact B exemption rows after validating A/B/C binding. The
application verifies protected bytes and invocation before comparing explicit
gauge observations with approved expected-value bytes.

### Consequences

- Trace/exemption facts and outcome facts have canonical, stable identities.
- A valid marker cannot turn a wrong gauge observation into a pass.
- This slice adds ports only; lifecycle, persistence, judge, CLI, and generator
  remain outside its boundary.
- Comment anchors cover only in-place modifications of the candidate symbol
  they directly precede. A deletion or whole-symbol rename is attributed to the
  base-side symbol and requires a signed sidecar: the comment grammar carries
  no symbol name, so it cannot attest to a symbol absent from the candidate.
  Sidecars are therefore the stronger form for this asymmetric case.

### Confirmation

Unit and integration tests exercise comments, sidecars, refusals, protected
bytes, wrong outcomes, and byte-identical repeated facts.

## Improvements on the prior art

Closed token order removes the pattern flexibility appropriate to in-toto rules.
Coverage's separate reporting concern becomes a separate outcome-observation
port, with no inference from a marker to semantic correctness.

## Architecture surface

`specification_trace` is pure domain parsing, changed-hunk coverage, and fact
serialization. `specification_verification` composes A/B/C validation, artifact
checks, invocation equality, and explicit outcome observations.

## Scope and threat delta

This blocks stale or invented references, exemptions, projections, and protected
oracles. It does not execute tools, generate comments, persist facts, issue
grants, or make a verdict in the existing judge.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | changed protected fixture | refusal precedes outcome comparison |
| Determinism | equal input | byte-identical fact bytes and code |
| Auditability | missing anchor | stable code names path and hunk |

## Reversibility

Door: two-way

The port can be replaced in a later version, but v1 anchor grammar and signed
manifest identities remain immutable for already-issued approvals.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | missing anchor | refuse uncovered hunk |
| 2 | stale projection | refuse before coverage |
| 3 | duplicate anchor | refuse exact duplicate |
| 4 | unknown ID | refuse closed vocabulary violation |
| 5 | cross-task C | refuse bound identity mismatch |
| 6 | ambiguous anchors | refuse instead of choosing one |
| 7 | wildcard exemption | refuse authority widening |
| 8 | reasonless exemption | refuse incomplete exemption |
| 9 | unapproved sidecar | refuse digest/path mismatch |
| 10 | protected bytes or argv drift | refuse before outcomes |
| 11 | wrong gauge result | emit failed outcome fact and refuse |

## Test strategy

`tests/unit/test_specification_trace.py` freezes grammar and all individual
reference/exemption refusal partitions. `tests/integration/test_specification_verification.py`
uses candidate/base trees and proves protected-byte precedence, outcome failure,
and deterministic facts.

## Code review checklist

- Is comment parsing exact in order, spelling, and allowed language prefix?
- Are IDs checked only against A's closed vocabulary?
- Do B/C/projection and protected bytes fail before gauge evaluation?
- Does every exemption compare exact path, class, and non-empty reason?
- Are facts sorted and serialized canonically?

## More Information

Vendored bytes prove that source bytes were obtained, not that they came from
the cited URL. They do not prove semantic correctness or replace SLICE-044's
real repository/provider attack exit.
