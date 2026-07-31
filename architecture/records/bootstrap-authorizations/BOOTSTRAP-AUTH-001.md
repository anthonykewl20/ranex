# BOOTSTRAP-AUTH-001 — controlled bootstrap exception for the first walking skeleton

| Field | Value |
|---|---|
| Record ID | `BOOTSTRAP-AUTH-001` |
| Status | `ACTIVE` |
| Issued by | Human owner, in session, 2026-07-31 |
| Issued at | 2026-07-31 |
| Subject | The first walking skeleton, defined at [`docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md`](../../../docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md) |
| Expires | On completion **and verification** of that slice |
| Form | **Prose, not `HumanDecisionV1`.** See "Why this is an exception" |

---

## What the owner authorized, verbatim in substance

> Proceed with the first walking skeleton. Treat the missing authorization
> issuance as a **temporary bootstrap authorization**, not as a reason to block
> implementation.

With five explicit limits, recorded here as the terms of the exception:

1. This authorization applies **only to the first walking skeleton**.
2. It authorizes implementation of **the defined slice only**.
3. It does **not** authorize unrelated product work.
4. It **expires** when the slice is completed and verified.
5. The permanent authorization issuance mechanism is a **required prerequisite
   before the second implementation slice**.

And two prohibitions:

- **Do not weaken any fail-closed guarantee.**
- **Do not bypass governance checks.**

## Why this is an exception, stated plainly

`ADR-0012:72` and its machine contract at `:656-657` forbid implementing a
product capability before `IMPLEMENTATION_START_READY`. `RFC-0010` would
authorize a bounded lane and is **not promoted**, because `SLICE-LANE-011`
requires an authenticated `HumanDecisionV1` and **nothing in this repository can
mint one**.

Verified 2026-07-31:

- No populated `HumanDecisionV1` exists anywhere under `architecture/`.
- The only construction of `authentication_context_id` and
  `presentation_challenge_digest` is a **synthetic fixture** at
  `scripts/architecture/validate_contracts.py:8436`.
- `ADR-0017`'s machinery is implemented and gated, but **issuance** is not built.

The corpus therefore required an artifact it could not produce. That is a
bootstrap deadlock, not a governance failure, and it is exactly the class of
problem `ADR-0012`'s own tracer lane was created to solve for tooling.

## What this record is NOT

- **Not a `HumanDecisionV1`.** It has no `principal_id`, no
  `authentication_context_id`, no `presentation_challenge_digest`, no `nonce`,
  no cryptographic digest. It does not validate against
  `schemas/authority/human-decision-v1.schema.json` and **must never be counted
  as satisfying it**.
- **Not a resolution of any `HERMES-OWNER-DECISION-*` row.** All 20 remain
  `OWNER_DECISION_REQUIRED`. `unresolved_owner_decision_count` stays 20.
- **Not a promotion of `RFC-0010`.** That RFC remains `DRAFT`, rejected twice by
  independent review.
- **Not a readiness declaration.** Neither tier is declared.
- **Not a precedent.** Term 5 makes the permanent mechanism a prerequisite for
  the next slice, so this cannot be reused.

## Fail-closed guarantees that remain in force

None of the following is weakened, and each is verifiable by execution:

| Guarantee | Still enforced |
|---|---|
| Absence blocks — `NOT_ASSESSED` is never a pass | Yes; the slice's `BC-2` tests it directly |
| Generated output cannot be hand-edited | Yes; validator returns `EXIT=1` on tampering, tested 2026-07-31 |
| Records cannot go stale silently | Yes; freshness gate returns `EXIT=1` on a broken claim, tested 2026-07-31 |
| Owner-decision rows fail closed on a bare reference | Yes; `OWNER-RESOLVE-007` case passes in the 11-case suite |
| No model verdict is authority | Yes; the slice's `BC-5` requires that removing model access changes no verdict |
| Slice evidence is not readiness evidence | Yes; every record carries `subject_lane: PRE_READINESS_PRODUCT_SLICE` |

**No governance check is disabled, relaxed, skipped or reinterpreted by this
record.** The exception is to the *prohibition on writing product code*, and to
nothing else.

## Traceability

| Link | Target |
|---|---|
| Slice definition | `docs/architecture/reviews/2026-07-31-walking-skeleton-definition.md` |
| Governing prohibition | `ADR-0012:72`, machine contract `:656-657` |
| Blocked proposal | `docs/architecture/rfcs/RFC-0010-authorize-bounded-vertical-product-slices.md` (`2.2.0`, `DRAFT`) |
| Missing mechanism | `ADR-0017` implemented; issuance not built |
| Map | `docs/architecture/MASTER_ARCHITECTURE_SPECIFICATION.md` §11.1 |

## Discharge conditions

This record moves to `EXPIRED` when **all** hold:

1. Every behavioural contract `BC-1` … `BC-7` has an executed, passing test.
2. Every failure mode in the slice definition §9 has an executed test.
3. The command has **blocked a real change** in this repository, output recorded.
4. Verification evidence is recorded, separating executed from statically
   reviewed.
5. The Master Architecture Specification is updated with validated **and
   disproved** findings.

After discharge, **no further product slice may open** until the permanent
authorization issuance mechanism exists. That is term 5, and it is the single
most important line in this record.
