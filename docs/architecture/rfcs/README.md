# RFCs

Proposals. Not decisions.

This directory is the accepted home for governance proposals in the target tree
(`HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:954`, accepted by
[ADR-0003](../decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md)).

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

This directory is created; the RFC lifecycle axis, artifact type, and schema are not yet
enacted in `architecture/contracts/`. Until they are, an RFC here is a governed prose
artifact only — it carries no machine-checked state.
