# ADR-061 — Live acceptance before completion

**Status:** accepted
**Date:** 2026-09-12
**Decision-makers:** repository owner

## Decision

Owner direction: implement the whole idea → approved map → frozen probes →
isolated implementation → independent evidence → deterministic verdict loop,
including three persisted acceptance misses and exact-candidate integration.
The product problem is an agent spending a day building code whose own tests
pass while the delivered program fails the user's workflow.

A PASS must establish that required approved journeys were observed against
the delivered candidate. A browser journey needs browser execution; internal
function assertions cannot stand in for it. Unit tests remain development
feedback and regression checks, never substitutes for required live acceptance.
Other required policy checks may still block. No model decides the verdict.

Deterministic means fixed, versioned rules evaluate digest-bound observations.
It does not mean an arbitrary distributed application always behaves identically,
that all bugs are discoverable, or that the kernel can infer unstated intent.
Freeze repetitions, deadlines and permitted nondeterminism explicitly. Missing
observations and infrastructure failures block completion without being silently
reclassified as successful acceptance.

## Existing substrate and measured gaps

Reuse A/B/C canonical identity and approval, capability intersection/revocation,
verified Git materialisation, process confinement, signatures, journal and the
existing pure evaluator. Do not introduce another approval or verdict engine.
Ordinary suite freeze records IDs, not executable bodies. SLICE-031 projections
include explicitly marked placeholder gauges, so they cannot be accepted as
live probes. Ordinary run remains non-confined; a same-UID controller is trusted.

The first slice adds an executable-artifact freeze path, independent of those
projections. It makes no execution, semantic adequacy or confinement claim.
An external directory alone does not prevent a same-UID worker modifying it.

## Implementation sequence and release exits

1. Complete probe bundle. Freeze actual committed files under exact selected
   roots, including helpers, fixtures, launch/configuration and runtime identity
   declarations. Preserve executable modes and literal argv. B binds the bundle
   descriptor and every copied file; C can bind that B using existing approval.
   Candidate integrity checks take an independently trusted B identity. Detect
   changed bytes, inserted helpers, deletions, mode changes and symlinks. Do not
   call artifact integrity a product PASS. This is issue #116 / SLICE-087.
2. Independent live observer. Materialise/build the exact candidate and start
   it under a qualified isolation profile. The trusted observer runs separately,
   cannot import candidate code, and owns outcomes/receipts/signing. Bind actual
   process/runtime identity, network endpoint and dependency instances. Refuse
   missing startup, wrong subjects, fabricated result artifacts, unexpected
   dependency substitution and attempts to modify the observer. Start with one
   Linux HTTP service and a real persistent database. Add the browser adapter
   before making UI acceptance claims.
3. Calibration. Require approved known-bad product controls to fail their named
   assertions and a known-good control to pass. A timeout, unrelated exception,
   compile error or nonzero exit is not evidence that the target defect was
   detected. Surviving required controls block acceptance. Store exact control
   identities and the scope of calibration; no universal anti-gaming claim.
4. Task authority. Connect map approval and C to implementation grants and the
   independently executed proof. Persist submitted acceptance misses by task
   and contract; stop authority after three. Development checks do not consume
   that budget. Infrastructure errors block separately. Restart cannot reset
   the count. Contract changes revoke old grants and evidence and require new
   human approval. Adapters explain policy; mediation enforces effects.
5. Integration. Only the tested integration candidate may land. Compare-and-swap
   against the approved target head; changed integration trees require proof.
   No copied verdict for an old PR tree. Crash/retry must not duplicate merges.
6. Real-world release. An independently retained frozen journey rejects an
   application whose own tests pass, then accepts the repair unchanged. Include
   fresh installation, normal use, persistence/restart and forbidden access;
   add a real browser flow. Repeat identical inputs under the frozen policy,
   retain raw evidence and distinguish VERIFIED, GAP and UNVERIFIED. External
   harness and production readiness claims require their own actual runs.

The owner prioritises this sequence over expanding GitHub publication and the
older minimisation program. Existing work is retained. One mutation issue is
completed and verified at a time. Each slice has real CLI positive/negative
journeys and the full frozen repository regression suite; the final product
release requires all six exits, not merely the first foundation slice.

## Research and rejected shortcuts

Read local ADR-017, ADR-025, ADR-045 and current implementation before designing.
Studied in-toto 2.3.0 `in_toto/verifylib.py` `verify_match_rule` and `runlib.py`
artifact recording via Leitir. Registry artifact checksum:
`sha256:69dce4b7df7177f3b84602edda526787570f3ce6db544ebb1d081a6a44fe1adb`.
Leitir reports Git/artifact parity drift and inconclusive licence routing.
This is study-only evidence, not a Git-parity claim; no code is copied and no
runtime dependency is added. Existing Ranex verified Git readers implement the
needed artifact identity mechanics. Exact root membership avoids treating a
matching subset as a complete unchanged acceptance directory.

Static mock bans are lint, not proof of live execution. Process stdout is a
claim, not authoritative process identity. A read-only file mode is not an
OS boundary against its owner. One mutation killed is not complete coverage.
Approval of prose alone does not approve arbitrarily generated executable
semantics. Known placeholder projections must never enter the executable freeze.

## Authority boundary

Owner approves normative outcomes and executable probes; implementation worker
cannot sign that approval or the observer's evidence. Trusted operator/controller
administration is outside the hostile-candidate boundary. Third-party trust in
an operator holding all keys still needs an external witness, independently of
the local acceptance pivot. No broad security claim closes on synthetic receipts.
