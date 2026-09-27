# ADR-066 — authenticated approver: possession before judgment, second signature in the verdict

**Status:** accepted

Closes MAP `RISK-07` / GitHub issue #107. Rests on ADR-047 (authenticated
principals at the trust root) and ADR-030 (roles). `verdict.py` is unchanged;
`KERNEL_DIGEST` is unmoved.

## Context and Problem Statement

`evaluate()` has always taken an `approver_id` string. No-self-approval was a
string comparison: any caller could type a different name and pass. In a team
the approver key should sit with a different person (or an HSM); with one
operator it is at least a second key a compromised worker never holds.

## Decision Outcome

In the context of unauthenticated `approver_id` strings, we chose **a catalogued
`role: approver` principal, CLI key-possession checks before `evaluate()`, and a
second Ed25519 signature in `signatures[]` verified by the reader**, accepting
that archived single-signature verdicts remain readable as `UNAPPROVED` and never
gate.

### Principal

`governance/producers.yaml` names a principal with `role: approver`. One
principal, one role — `_INCOMPATIBLE_ROLES` already forbids approver+worker on
one key. Key material is minted with `ranex keygen` into
`~/.config/ranex/approver.key` (0600, outside every checkout).

### Possession at evaluation

`ranex gate evaluate --approver A` requires `RANEX_APPROVER_SIGNING_KEY`. Its
public half must equal principal A's active key and A's role must be `approver`.
Any other case is an operational refusal (exit 2) **before** `evaluate()`:
`E-APPROVER-KEY-ABSENT`, `E-APPROVER-UNKNOWN`, `E-APPROVER-KEY-MISMATCH`,
`E-APPROVER-ROLE`. No verdict, no journal row, no publication.

### Proof in the verdict

`publish_verdict` appends `{signer_id: A, signature: sign(content)}` to
`signatures[]` over the same signed fields and domain. `read_verdict` verifies
**every** signature; when `approver_id` names a catalogued approver, a missing
or bad signature yields closed state `UNAPPROVED`. Publication and
`journal verify --against-verdict` refuse `UNAPPROVED` like every non-VERIFIED
state.

### Receiver

`EvidenceEvaluator` passes the approver key path through its minimal environment
exactly as it passes the verdict key; both stay outside the repository.

## Consequences

- Positive: no-self-approval becomes a cryptographic control, not a string.
- Negative: operators must mint and place a second key; CI/receivers must carry
  `RANEX_APPROVER_SIGNING_KEY` where approval is required.
- Archived single-signature verdicts remain readable, never gating (ADR-057
  precedent).

## Confirmation

- Real e2e: `tests/e2e/test_approver_authentication_real.py` (seven arms).
- Field receipt: `tools/dogfood/audits/2026-09-26-approver-authentication/`
  (11/11 VERIFIED).
- Unit: `tests/unit/test_verdict_publication.py`,
  `tests/unit/test_verdict_reader.py`.
