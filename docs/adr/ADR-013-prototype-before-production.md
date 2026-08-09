# ADR-013 — prototype before production

**Status:** accepted
**Date:** 2026-08-06
**Decision-makers:** repo owner
**Slice:** n/a — this decision precedes a future prototype slice; SLICE-010 is closed

## Context and Problem Statement

Two independent adversarial reviews, reviewer-hy3 and reviewer-deepseek, cross-verified against source, found authenticity gaps in the built system.
P0 RISK-06 remains deferred by [ADR-006](./ADR-006-landlock-confinement-of-the-bound-command.md): the measured command and the signing key share a uid — the child env is scrubbed (`src/ranex/cli/delegation.py:56-60`), but the same-uid child can read the signer's `/proc/<pid>/environ` (delegation.py:34-44; env name at `src/ranex/cli/main.py:124`), so signed evidence is forgeable.
The suite freezes test IDs, not bodies (`src/ranex/foundation/suite_results.py:186-198`), so a neutered body can pass.
P1 RISK-07 leaves `approver_id` an unauthenticated CLI string; `evidence.json` replaces a producer's prior record per claim instead of appending (`src/ranex/cli/main.py:697-722`), and network denial applies only to provisioned runs (`src/ranex/cli/main.py:1868`).
P2 has no external journal anchor, no negative-control fixtures, and stale documentation counts: README declares 737 manifest IDs while collection measures 809 tests (807 passed, 2 skipped, 2026-08-06) and 85 e2e functions.
Production changes made directly from these ideas would turn plausible sketches into trust-boundary code without evidence.

## Decision Drivers

- Prototype every authenticity idea before production code.
- Start each idea red-first, and retain a negative control.
- Keep the pure kernel and existing trust boundaries unchanged.
- Use real current artifacts without shipping scratch code.
- Make uid, filesystem, network, hashing, identity, and journal assumptions observable.
- Time-box exploration and record the decision at expiry.

## Prior art

- Searched: `gh api -X GET search/repositories -f q='signer key isolation CI attestation'`; no useful result was returned.
- Searched: `gh api -X GET search/repositories -f q='Landlock rootless sandbox untrusted command'`; no useful result was returned.
- Searched: `gh api -X GET search/repositories -f q='content hash frozen tests test identity'`; no useful result was returned.
- Searched: `gh api -X GET search/repositories -f q='append only evidence hash chain'`; returned small evidence-ledger projects, not a mature whole solution.
- **in-toto runlib**, commit `c82fe5d21aaa61c7f1a213db20a46f10bb3f411a`, records command materials, products, and byproducts: <https://github.com/in-toto/in-toto/blob/c82fe5d21aaa61c7f1a213db20a46f10bb3f411a/in_toto/runlib.py>
  License: Apache-2.0.
  Weakness: it records provenance but does not isolate a signing key from the command or authenticate Ranex approvers.
  Vendored: docs/adr/prior-art/ADR-013/in-toto-runlib.py blob:8207871046a6b0691c2689198d8d87a874520a38
- **sigstore/cosign remote**, commit `9a4cfe1aae777984c07ce373d97a65428bbff734`, separates signed artifact lookup from local policy: <https://github.com/sigstore/cosign/blob/9a4cfe1aae777984c07ce373d97a65428bbff734/pkg/oci/remote/remote.go>
  License: Apache-2.0.
  Weakness: registry signatures and transparency services do not make local command execution unable to read a parent environment.
  Vendored: docs/adr/prior-art/ADR-013/cosign-remote.go blob:eab4e1f9b012aff2710fafa75d1d04afebfee2bf
- **bubblewrap**, commit `8e51677abd7e3338e4952370bf7d902e37d8cbb6`, supplies a rootless sandbox boundary: <https://github.com/containers/bubblewrap/blob/8e51677abd7e3338e4952370bf7d902e37d8cbb6/bubblewrap.c>
  License: LGPL-2.1-or-later, research-only evidence.
  Weakness: kernel support, setup policy, and uid/user namespaces vary; a wrapper alone does not prove the exact Ranex key is inaccessible.
  Vendored: docs/adr/prior-art/ADR-013/bubblewrap.c blob:9b78a9ae30dd8f3361f95ae0132d1c32a4ac3329
- Rejected: https://github.com/aevryone/proofgate — self-advertised maturity with one commit and no evidence that its gate resists an adversarial producer.
- Rejected: https://github.com/UmutKorkmaz/quorate — no demonstrated production implementation or independent tests for authenticated approval and evidence integrity.

## Considered Options

1. Patch each gap directly. Rejected: the reviews identify ideas, not proven designs.
2. Prototype only the highest-risk uid boundary. Rejected: the remaining gaps are independently reachable; leaving them unproven transfers the same gamble to later slices.
3. Prototype all scoped ideas in the production tree. Rejected: scratch experiments would become accidental runtime surface.
4. Reuse mature wrappers directly (bubblewrap/in-toto-style signer isolation). Rejected: wrapping mature mechanisms still leaves the exact Ranex boundary — key reachability, approver identity, evidence chain — unproven; adopting any wrapper remains a later slice decision.
5. Prototype each idea red-first in a scratch worktree, then open production slices only when all exit criteria are green. Chosen.

## Decision Outcome

In the context of authenticity gaps in the built system, facing unproven trust-boundary ideas, we chose a scratch prototype as the gate before production, to replace confidence with executable evidence, accepting bounded delay and possible abandonment.
The prototype lives in a scratch git worktree or scratch directory, never inside `src/ranex`; it may reuse the built Ranex module and `governance/` artifacts but ships nothing.
Each idea starts with a failing test, proves the unsafe baseline, then passes only with a negative control demonstrating refusal.
The prototype is time-boxed to two weeks of wall-clock from acceptance; expiry requires a recorded choice to polish-and-extend, drop the idea, or open a production slice.
Each idea's production slice may open independently once that idea's exit criteria are green; no slice opens with a missing or merely described criterion.
Future production slices, beginning at SLICE-011+, copy the prototype's proven design into their done-criteria.

### Consequences

- Good: uid separation, test-body hashing, authenticated approvers, evidence chaining, per-run network denial, anchors, and negative controls become testable.
- Good: the current kernel and strong controls remain the baseline, not experimental output.
- Good: a failed or impossible idea is visible before production scope is committed.
- Bad: no production fix lands while the prototype gate is incomplete.
- Bad: scratch harnesses cost time and can require privileged or kernel-specific facilities.
- Bad: passing a prototype does not prove production integration.
- The prototype may reuse artifacts but never changes them or becomes an import path.
- The parallel track is a research track, not a slice: it carries no done-criteria, owns no production surface, and cannot delay SLICE-010.
- Existing strengths retained: pure `evaluate()` (`verdict.py:338`), absence blocks, contradiction FAIL (`verdict.py:248-266`), signing, digest binding, committed trust roots, journal, and CAS merge.
- This decision does not close RISK-06, RISK-07, or any listed gap.

### Confirmation

The prototype's own scratch suite is the confirmation authority, not its author summary.
For each idea, the suite must show a red test against the current unsafe control, then green behavior and a deliberate negative control.
The exit record must enumerate each idea, command, fixture, observed refusal, artifact digest, and reviewer decision.
The exit record — each idea, command, fixture, observed refusal, artifact digest, and reviewer decision — lives in the scratch worktree until the decision point; the owner's decision is then recorded in `docs/STATE.md` and the opening slice.
The gate is compiled, not merely stated: the first hardening slice must extend `tests/contract/test_docs_discipline.py` to refuse hardening slices whose ADR-013 exit criteria lack a green, digest-bound record.
No production slice may open with a missing or merely described criterion.
The existing contract test confirms this ADR's structure only; it does not certify the prototype or any security property.

## Improvements on the prior art

1. The uid experiment proves both read access today and inability after confinement, rather than assuming a sandbox boundary.
2. Test freezing hashes each file body with SHA-256, not merely names or IDs, and mutating one character must refuse.
3. Approver identity is tested as a verified signature/envelope, not accepted as a CLI label.
4. Evidence append-only behavior is tested with hash chaining like the journal, rather than overwrite semantics.
5. Network denial is exercised per run, not only in provisioning.
6. An external journal anchor is treated as an explicit prototype idea, with offline and unavailable-anchor controls.
7. Negative-control fixtures deliberately demonstrate that a harness-level pass is insufficient.
8. Stale test counts are measured against collection output and become a visible documentation failure.
9. Each design must survive a red-first test and a negative control before production consideration.
10. A time-box decision prevents prototypes becoming silent permanent architecture.

## Architecture surface

No production port, adapter, or module changes in this ADR.
The prototype composes the existing Ranex module, committed governance artifacts, OS uid/sandbox facilities, temporary fixtures, and scratch journal/evidence stores.
It must not import scratch code into `src/ranex` or write `governance/`.
Future slices own production composition, migrations, and integration with the kernel and harness.

## Scope and threat delta

This ADR governs the transition from authenticity idea to production implementation; it changes no current verdict or trust boundary.
STRIDE delta now: none; the prototype produces evidence about future **Tampering**, **Elevation**, **Repudiation**, and **Information Disclosure** controls.
In scope are the seven prototype ideas and stale-count/negative-control checks named above.
Out of scope are unrelated product behavior, replacing the pure kernel, and shipping a scratch harness.
Non-goal: a green prototype is not proof that production integration is safe without slice review.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Security | command attempts key access | separated run refuses; control reads key |
| Integrity | one frozen test character changes | manifest digest mismatch refuses |
| Authenticity | CLI approver string is forged | envelope verification refuses |
| Reliability | evidence is written twice | chain preserves both records |
| Observability | prototype expires | decision and evidence record exist |

## Reversibility

Door: two-way

Delete the scratch worktree without touching production or governance.
A rejected idea leaves its failing and passing prototype history as review evidence.
An accepted idea still requires a new ADR or slice implementation decision.
No production format migration is authorized by this ADR.
Superseding this proposed ADR changes only the gate, not existing runtime behavior.

## Sad paths

Derived by threat modeling, equivalence partitions, and state-transition analysis.

| # | Failure | Required behavior |
|---|---|---|
| 1 | Landlock unavailable | record environment failure; do not claim the uid idea green |
| 2 | uid separation impossible on dev kernel | mark blocked and choose at time-box decision |
| 3 | prototype shares the parent's blind spot | add an independent observer (a second scratch harness reading `/proc` directly) or refuse the result |
| 4 | prototype proves the wrong idea | restate threat and restart red-first |
| 5 | time-box expires | record polish-and-extend, drop, or production-slice decision |
| 6 | harness bug makes a test pass | reproduce with a negative control and independent inspection |
| 7 | prototype cost exceeds benefit | record drop decision; do not silently expand scope |
| 8 | prototype validates but production drifts | future slice copies design and adds integration refusal tests |
| 9 | one-character test neuter is not detected | prototype remains red; no production slice opens |
| 10 | evidence append fails or chain forks | reject the design and preserve the failing artifact |
| 11 | approver envelope is malformed or self-authored | reject identity; never coerce CLI text into trust |
| 12 | per-run network denial is bypassed | negative control fails; no green exit criterion |
| 13 | anchor service unavailable | distinguish unavailable from anchored; never invent confirmation |
| 14 | stale counts differ from collection | record measured counts and correct the future slice/docs owner |

## Test strategy

The prototype suite lives in its scratch area, not under `tests/`; implementers must not edit frozen production tests to make it pass.
Each idea follows red-first: run the baseline failing test, make the smallest scratch change, then run the positive assertion and its negative control.
The uid case runs a command that can read the key, then a separated/constrained command that cannot.
The manifest case mutates one frozen test byte and requires digest refusal.
Identity, evidence, network, anchor, and negative-control cases each have positive and refusal fixtures.
The existing `tests/contract/test_docs_discipline.py` verifies this ADR's sections, budgets, citations, hashes, and notices.
Existing `tests/unit/test_gate_verdict.py` protects pure evaluation, absence, contradiction, and producer/approver behavior.
Existing `tests/security/test_git_backed_materialisation.py` protects committed materialisation boundaries.
Existing `tests/integration/test_journal.py` protects append-only journal behavior.
Existing `tests/e2e/test_first_delegation.py` protects the current governed journey.
The future production slice's tests under `tests/security/` belong to that slice, not this ADR.
No global coverage percentage is required; changed prototype branches and every refusal branch need assertions.
Exit is green only when every named idea has a passing test, a demonstrated negative control, and an immutable result record.

## Code review checklist

- Does every prototype begin with an observed red unsafe control?
- Is the negative control independent of the implementation under test?
- Does the uid test actually attempt `/proc/<pid>/environ` key access?
- Does the manifest hash the test body rather than just its identifier?
- Is approver identity verified cryptographically and bound to the envelope?
- Is evidence append-only and hash-chained without overwrite fallback?
- Is network denial applied on every run, not just provisioning?
- Are unavailable facilities recorded as blocked rather than green?
- Does the exit record state the time-box decision and all criteria?
- Does the future slice copy proven behavior without changing existing strengths?

## More Information

[ADR-006](./ADR-006-landlock-confinement-of-the-bound-command.md) defers confinement and records RISK-06.
[ADR-008](./ADR-008-fork-opencode-and-bridge-to-the-kernel.md) names delegated-loop credential exfiltration as sad path 13.
[ADR-011](./ADR-011-a-skip-is-absence.md) establishes that a skip is absence.
[ADR-012](./ADR-012-the-kernel-merges.md) keeps merge publication in the kernel.
The reviewed source locations are `src/ranex/cli/main.py:124`, `:697-722`, and `:1868`, plus `src/ranex/foundation/suite_results.py:186-198`.
The prototype must preserve signing at `src/ranex/foundation/signing.py:44,92-96` and digest binding at `src/ranex/governed_execution/domain/verdict.py:124-162`.
It must preserve committed-byte trust roots at `src/ranex/cli/main.py:186-255` and CAS merge at `src/ranex/cli/main.py:1272-1360`.
Reviewed 2026-08-06 by reviewer-hy3 and reviewer-deepseek (both approve-with-fixes); the stale-count claim, exit-record sink, and compiled gate were their consensus defects.
Open decision: at the time-box, record polish-and-extend, drop, or open a future production slice; silence is not an option.
