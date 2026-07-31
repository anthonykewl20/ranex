# RFCs

Proposals. Not decisions.

This directory is the accepted home for governance proposals in the target tree
(`HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:954`, accepted by
[ADR-0003](../decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md)).

## Current proposals

| RFC | Status | Standing |
|---|---|---|
| [RFC-0001: Fix the implementation language and its performance escape hatch](RFC-0001-fix-the-implementation-language-and-performance-escape-hatch.md) | `ACCEPTED` | Promoted to [ADR-0014](../decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md); retained as history |
| [RFC-0002: Selectively adapt Spec Kit interaction and artifact patterns](RFC-0002-selective-spec-kit-adaptation.md) | `DRAFT` | Prose proposal backed by an advisory review; no adaptation or authority. Awaits owner decision |
| [RFC-0003: Deterministic session continuity and drift tripwires](RFC-0003-deterministic-session-continuity-and-drift-tripwires.md) | `DRAFT` | Prose proposal; rewritten as adoption of `cog`, `AGENTS.md` and `pre-commit`. Awaits owner decision |
| [RFC-0004: Canonical workflow and event schema, and upcaster policy](RFC-0004-canonical-workflow-and-event-schema-and-upcaster-policy.md) | `ACCEPTED` | Accepted by the human owner 2026-07-30 and promoted to [ADR-0015](../decisions/ADR-0015-canonical-workflow-and-event-schema-and-upcaster-policy.md); retained as history |
| [RFC-0005: Resolve the five remaining implementation-start owner decisions](RFC-0005-resolve-five-remaining-implementation-start-owner-decisions.md) | `ACCEPTED` | Accepted by the human owner 2026-07-30 and promoted to [ADR-0016](../decisions/ADR-0016-resolve-five-implementation-start-owner-decisions.md); retained as history |
| [RFC-0006: Record a resolved owner decision](RFC-0006-record-resolved-owner-decisions.md) | `ACCEPTED` | Prose proposal; amends `ADR-0013` so its own stated resolution procedure becomes executable. Awaits owner acceptance |
| [RFC-0007: Validate without the local-only practice corpus](RFC-0007-validate-without-the-local-only-practice-corpus.md) | `DRAFT` | Prose proposal; corrects a validator contract that contradicted `ADR-0002`. Awaits owner acceptance |
| [RFC-0008: Select the static type checker](RFC-0008-select-the-static-type-checker.md) | `ACCEPTED` | Prose proposal; discharges the selection `ADR-0014` `LANG-TYPECHECK-001` deferred. Recommends `pyrefly` pinned at `1.1.1`. Awaits owner acceptance |
| [RFC-0009: Record freshness as a shipped Ranex capability](RFC-0009-record-freshness-as-a-shipped-capability.md) | `DEFERRED` | Prose proposal; specifies a capability Ranex ships to governed projects. **Deferred by owner decision 2026-07-31**: no implementation slice requires it. Reopens when the first external governed repository becomes a supported runtime target |
| [RFC-0010: Authorize bounded vertical product slices before `IMPLEMENTATION_START_READY`](RFC-0010-authorize-bounded-vertical-product-slices.md) | `DRAFT` | Prose proposal at `2.2.0`. Would add a second bounded pre-readiness lane permitting product capability on this repository only, producing **no** readiness evidence. `1.0.0` and `2.0.0` were both **rejected by independent adversarial review**. Blocked on one thing only: no authenticated `HumanDecisionV1` can be minted, because nothing in this repository issues authentication contexts. Not eligible for promotion |

The `Status` column records the value in each file's own header. An RFC promoted
into an accepted ADR carries `ACCEPTED`; `scripts/architecture/check_record_freshness.py`
fails closed if a promoted RFC still reads `DRAFT`.

## What belongs here

A change to architecture, machine contracts, or policy that is proposed but not yet
decided. The Core SDLC routes such changes "through RFC/ADR policy"
(`CORE_SDLC_OPERATING_MODEL.md:577`) and requires an RFC alongside threat, data and
operational analysis in the highest design column (`:229`).

A direct owner requirement may bypass the RFC. [ADR-0001](../decisions/ADR-0001-established-sdlc-governs-ai-work.md)
and [ADR-0002](../decisions/ADR-0002-retire-legacy-implementation-guide.md) both record
`RFC | Not required; direct owner requirement`.

## What does not belong here

Accepted decisions. Those live in [`../decisions/`](../decisions/), where every file must
carry `Status | ACCEPTED` — enforced by `scripts/architecture/validate_contracts.py`.

An RFC is not authority. Nothing in this directory grants a permit, satisfies a gate, or
authorizes a transition until it has been accepted as an ADR.

## Naming

`RFC-NNNN-kebab-case-title.md`, starting from `RFC-0001`. Author from
[`../templates/RFC.md`](../templates/RFC.md).

## Promotion

An accepted RFC becomes an ADR in `../decisions/`. The RFC record remains here as history;
it is not deleted or rewritten. The resulting ADR references the RFC it came from in its
`RFC` header field.

## Status

The RFC lifecycle axis, artifact type, and schema are not yet enacted in
`architecture/contracts/`. Until they are, every RFC here is a governed prose
artifact only — it carries no machine-checked state.
