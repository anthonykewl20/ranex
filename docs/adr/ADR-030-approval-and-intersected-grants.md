# ADR-030 — approval, revocation and intersected child grants

**Status:** accepted
**Date:** 2026-08-16
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-032-approval-and-intersected-grants.md`

## Context and Problem Statement

ABC signatures bind a proposed approval, but do not yet decide whether it is
current, role-separated, policy-bounded, revocable, or safely delegated. A
child capability must not amplify its request, parent, or current policy.

## Decision Drivers

- Refuse absent, stale, replayed, or role-conflicted authority.
- Make capability intersection closed, deterministic, and least-authority.
- Make revocation observable before persistence exists.
- Preserve a pure interface for SLICE-036 atomic journal wiring.

## Prior art

- Searched: GitHub code search for macaroon caveat attenuation, SPIRE workload
  catalog identity, OAuth scope intersection, and authorization revocation.
- [go-macaroon `macaroon.go` at v2.1.0](https://github.com/go-macaroon/macaroon/blob/v2.1.0/macaroon.go)
  carries caveats as an ordered restriction on a bearer authority.
  License: BSD-3-Clause.
  Weakness: arbitrary caveat predicates require an external checker and cannot
  provide Ranex's closed, byte-identical capability grammar.
  Vendored: `docs/adr/prior-art/ADR-030/macaroon.go` blob:d730f8924baa287b8a40b4661ddd8ddbdb71c576
- [SPIRE `catalog.go` at v1.10.1](https://github.com/spiffe/spire/blob/v1.10.1/pkg/common/catalog/catalog.go)
  maps named workload components through a closed catalog boundary.
  License: Apache-2.0.
  Weakness: plugin catalog identity does not express delegated filesystem/action
  authority, journal ordering, or sibling-disjoint child scopes.
  Vendored: `docs/adr/prior-art/ADR-030/spire-catalog.go` blob:ddc8d76b6fb83696531a450ec6614054ab0d1d1b
- Rejected: https://github.com/ory/hydra OAuth scopes are strings with provider
  policy interpretation, so they cannot prove pairwise path+action disjointness
  or reject wildcard expansion under a closed local grammar.
- Rejected: https://github.com/cedar-policy/cedar Cedar permits expressive policy
  evaluation, but its open expression language is intentionally broader than a
  frozen v1 capability record and would move determinism into policy authoring.

## Considered Options

1. Closed policy record, pure issuance and event reducers: chosen.
2. Treat empty lists as inherited authority: rejected; absence must block.
3. Persist revocation here: rejected; journal ownership is SLICE-036.
4. Generic wildcard scope language: rejected; v1 has no safe grammar for it.

## Decision Outcome

`PolicyCapabilities` has the C capability fields and a canonical SHA-256
digest. Issuance requires that digest to equal C's policy profile. A child is
the exact intersection of request, parent, and policy: strings/argv/cwd are
equal; lists are set intersections; empty lists grant nothing; wildcard paths
are refused; network false clears hosts; children always lose secret, commit,
approval, integration, merge, and publication authority. Child roots/actions
must be pairwise disjoint from existing siblings by exact `(path, action)`.

### Consequences

- Role snapshots reject incompatible public-key role pairs.
- Approval nonces derive only from prior successful approval events.
- Sequence windows are inclusive at both ends and predecessor must be current.
- Events chain canonically in-domain and expose journal sequence/head fields.
- Batch issuance/liveness is a typed refusal until SLICE-036.
- `argv` is an ordered capability field: as `canonical.py`'s `command_digest`
  doctrine states, argument order is inside the digest, so reordered arguments
  are a different authority. Other capability collections remain sorted sets.
- Capability records carry `policy-capabilities-v1`; SLICE-032 digest vectors
  were regenerated for that additive self-description.
- A grant carries C's inclusive window at use time and projects
  `EXPIRY_RECORDED` at `not_after + 1`; revocation producers make the complete
  pure stream constructible before SLICE-036 persists it.

### Confirmation

The unit suites pin policy digest binding, exact intersections, wildcard and
type attacks, replay/window/predecessor controls, role conflicts, deterministic
facts and sibling non-overlap. Integration tests pin ancestor revocation and
the two deterministic use/revoke orderings.

## Improvements on the prior art

Macaroon attenuation becomes an explicit closed record rather than executable
caveats. SPIRE's component identity becomes digest-bound principal/key role
facts. Neither prior-art system supplies this event projection or CAS contract.

## Architecture surface

Domain owns records, validation, capability algebra, event chaining, and use
reduction. Application owns A/B/C verification and approval issuance. No
adapter, persistence, CLI, harness, or SLICE-030 session record is changed.

## Scope and threat delta

This closes child amplification, role/key sharing, replay, stale approvals,
wildcards, path escapes, and observed revocation races. It does not authenticate
keys, persist events, batch children, or wire SLICE-030 sessions.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| integrity | policy substitution | C profile digest refuses |
| authority | child expansion | output is an intersection |
| determinism | repeated input | identical canonical records |

## Reversibility

Door: two-way

The pure records and reducer can be replaced by a versioned successor. Historical
facts remain evidence but cannot authorize a different policy grammar; removing
the issuer without removing effect admission would be an invalid rollback.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | roots supplied as a string | typed refusal |
| 2 | wildcard root/action | stable wildcard refusal |
| 3 | empty list treated as all | no authority |
| 4 | boolean used as child count | typed refusal |
| 5 | revoke ordered before use | use refuses |
| 6 | use ordered before revoke | use fact stands |
| 7 | reused successful nonce | E-ABC-015 refusal |
| 8 | time before/after inclusive window | refuse |
| 9 | stale predecessor | refuse |
| 10 | one key has incompatible roles | refuse |
| 11 | executable/argv/cwd expansion | refuse/no grant |
| 12 | `..`, absolute, backslash, control path | refuse |
| 13 | siblings overlap path+action | refuse |

## Test strategy

`tests/unit/test_specification_approval.py` covers C binding, policy digest, role snapshot,
nonce, predecessor and all window bounds. `tests/unit/test_specification_child_grants.py`
covers closed capability parsing, exact/intersected fields, no secret/commit,
wildcards, paths and sibling pairs. `tests/integration/test_specification_revocation.py` covers
event-chain determinism, ancestor propagation, expiry, and serial order races.

## Code review checklist

- Is policy content, not only its label, digest-bound to C?
- Are booleans rejected where integer counts are required?
- Can empty authority or wildcard syntax widen a capability?
- Is a child structurally unable to receive secret/commit/publish authority?
- Does each event bind prior event digest plus journal position/head?
- Does use observe the prefix head/position and ancestor revocations?
- Is persistence absent and SLICE-036 named for CAS wiring?

## More Information

SLICE-030 binding is represented as a typed approval-pending context with its
semantic digest and actor because its public session record is not on main.
SLICE-036 must atomically append against the observed head: compare expected
head, append exactly one event, and return its position/head. A batch request is
refused as `E-APPROVAL-BATCH-UNSUPPORTED`; no liveness guarantee is implied.
Vendored bytes prove acquisition, not origin.
