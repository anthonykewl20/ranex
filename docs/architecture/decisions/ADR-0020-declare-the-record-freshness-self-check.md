# ADR-0020: Declare the Record-Freshness Self-Check

| Field | Value |
|---|---|
| ADR ID | `ADR-0020` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-31 |
| Effective revision | Working tree based on `79d568914`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `assurance`, `process_assurance`, `configuration_management` |
| RFC | Not required; direct owner requirement, as for `ADR-0001` and `ADR-0002` |
| Supersedes | Nothing. Declares a gate that was added to CI and would otherwise be load-bearing and unrecorded |
| Review/expiry date | On any change to the check set, or when `RFC-0009`'s shipped capability supersedes this repository-local control |
| Compatibility/migration class | Additive control; no existing check's strictness changes |
| Security/data class | Public architecture decision |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-31 | Initial accepted decision. Records a CI gate that was otherwise in the same undeclared, load-bearing position `ADR-0019` closed for `uv`. |

## Context

The contract tree fails closed when generated output drifts from its sources.
Prose records had no equivalent. An agent could complete work, pass every gate,
and leave the documents describing the corpus asserting an older state, because
nothing generated those documents and nothing checked them.

**FACT**, measured 2026-07-31 before the gate existed: `HANDOFF.md` claimed 16
accepted ADRs while 19 existed; `README.md` stated the range ended at `ADR-0014`
and named RFCs only to `RFC-0002`, while `ADR-0019` and `RFC-0008` existed; and
five RFCs carried `Status: DRAFT` while each was already promoted into an
accepted ADR. Eight false claims, all passing contract validation, in a corpus
whose purpose is that claims must be checkable.

`scripts/architecture/check_record_freshness.py` was written to close them and
wired into `.github/workflows/architecture-contracts.yml`. It is therefore
load-bearing and, until this decision, unrecorded — the same defect class
`ADR-0019` closed for `uv` and `ADR-0014` closed for the language.

## Decision

### `RECORD-SELFCHECK-001` — the self-check is a declared, required gate

`check_record_freshness.py` is a required step in the architecture-contract
workflow. A non-zero exit blocks. Its scope is **this repository only**; it is
not the shipped capability specified by `RFC-0009` and must not be presented as
one.

### `RECORD-SELFCHECK-002` — every check is mechanical and model-free

Each check compares a written claim against an observable fact. No model is
invoked, nothing is inferred from prose, and identical inputs yield identical
findings. A proposed check that cannot be expressed this way is not admitted.

### `RECORD-SELFCHECK-003` — the declared check set

Five checks, each closing a defect measured in this corpus:

| check | claim compared against fact |
|---|---|
| `promoted_rfc_still_draft` | an RFC cited by an accepted ADR must not read `DRAFT` |
| `index_status_mismatch` | the RFC index's status column must equal the record's own header |
| `record_not_indexed` | every RFC file must be reachable from its index |
| `stated_range_stale` | a stated ADR/RFC range must name the highest record on disk |
| `stated_count_stale` | a stated accepted-ADR count must equal the number on disk |

Adding or removing a check is a change to this decision, not a convenience.

### `RECORD-SELFCHECK-004` — freshness is computed, never asserted

An agent may not mark records fresh. Findings clear only when the observed fact
changes. This mirrors `ADR-0017` `OWNER-RESOLVE-003` and `ADR-0013:1175-1176`.

## Predeclared acceptance tests

1. Reverting a promoted RFC's status to `DRAFT` produces a finding and a
   non-zero exit. **Verified by execution 2026-07-31.**
2. Staling the accepted-ADR count in `HANDOFF.md` produces a finding and a
   non-zero exit. **Verified by execution 2026-07-31.**
3. Restoring both produces zero findings and a zero exit. **Verified.**
4. Adding a new RFC without indexing it produces a finding. **Verified — the
   gate caught `RFC-0009` within seconds of its creation.**
5. An index status column disagreeing with the record's own header produces a
   finding. **Verified — this check was added after the gate passed while five
   such disagreements existed.**
6. Two runs over identical inputs produce identical findings.
7. No check invokes a model; removing model access changes no verdict.

## Consequences and evidence standing

- The eight measured stale claims are closed and the gate is green: 19 ADRs,
  9 RFCs, no stale claims.
- A defect was found and fixed in the gate itself during construction: a header
  parser excluded backticks, so the promoted-RFC check silently reported zero
  findings while five existed. A gate that under-reports is worse than no gate,
  and it is recorded here because the failure mode matters more than the fix.
- This control is repository-local and expected to be superseded by the shipped
  capability once `RFC-0009` is accepted and `IMPLEMENTATION_START_READY` is
  declared.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`. This
  decision authorizes no product code and declares no readiness tier.

## Human approval

The human owner directed that Ranex's architectural documents must never be stale
after work is done, and that the mechanism be an enforced gate rather than a
reminder, on the ground that a control depending on anyone remembering is not a
control.
