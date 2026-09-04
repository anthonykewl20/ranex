# ADR-047 — authenticated principals at the trust root

**Status:** accepted
**Date:** 2026-09-04
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-080-authenticated-principals.md`

## Context and Problem Statement

The committed trust root answers one question: *is this public key one of
ours?* `governance/producers.yaml` is a flat `producer_id -> public_key`
mapping plus a single hard-coded `verdict_signer` block
(`producer_keyring.py:159`). It cannot answer *what is this principal
permitted to be*, and nothing in the repository can.

That gap is load-bearing. `ranex gate evaluate --approver <name>` accepts
any string (`cli/main.py:3893`), and `evaluate()` refuses self-approval by
comparing that string to `producer_id` (`verdict.py:393`). The producer half
of that comparison is key-bound, because admission verifies a signature and
the keyring enforces one key per producer. The approver half is bound to
nothing at all. An operator types a second name and the control passes.

A role vocabulary already exists — `RoleAssignments` in
`specification_approval.py:193`, with roles `approver`, `worker`,
`evaluator`, `publisher` and an incompatibility matrix (ADR-030). It is
scoped per C-digest: it constrains what one signed approval envelope may
claim, not who this repository trusts. Two role vocabularies would be two
answers to the same question, and the drift between them would be a defect
nobody could see.

## Decision Drivers

- An approver must be provable from a signature, not from a typed name.
- One vocabulary of roles across the repository, not two.
- Key rotation must not force a new identity, and a retired key must not
  authorize new work.
- The existing trust root, its contract test, and roughly fifty test files
  that write `producers:` literally must stay green.
- A trust root that cannot be read, or that reads empty, must fail loudly.
  Absence of a control must never look like honest absence of work.

## Prior art

- Searched: SPIFFE/SPIRE workload identity registration entries, in-toto
  functionary key layouts, TUF role delegation, and OpenSSH certificate
  principals — for how each separates a stable identity from the key
  material that currently speaks for it.
- SPIFFE registration entries bind a stable SPIFFE ID to rotating SVIDs,
  which is exactly the many-keys-to-one-principal shape adopted here.
  Rejected as a dependency: SPIRE is a networked attestation daemon, and
  this trust root must stay a committed file that review is the control on.
- TUF role delegation carries per-role key sets with thresholds. The key-set
  shape is adopted; thresholds are refused for v1, because a threshold that
  is always one is a field that lies about what is enforced.
- Rejected: X.509 with an internal CA. It moves the trust root off disk and
  out of review, and revocation becomes a network question. ADR-002 already
  decided that the trust root is committed.

## Considered Options

1. Extend `producers.yaml` in place with roles: rejected. It changes the
   shape roughly fifty test files write literally, and the contract test
   pins `load_keyring` at `dict[str, str]`. A mass edit is not a decision.
2. A second file, `governance/principals.yaml`: rejected. Two trust-root
   files drift, and each is a place to look for the other's answer.
3. An additive `principals:` block in the same committed file, read by a
   new loader, with the old loader and the old block untouched: chosen.

## Decision Outcome

`governance/producers.yaml` gains an optional `principals:` block. A new
loader, `principal_catalog.py`, reads it and nothing else reads it yet.
`load_keyring`, `load_trust_keyring`, and the `producers:` block are
unchanged.

A principal is an identity, a role, and an ordered list of keys:

    principals:
      anthony:
        role: worker
        keys:
          - key: ed25519:...
            status: active

Rules, each of which is a refusal:

- The role vocabulary is ADR-030's, plus `service` for non-human actors
  (the verdict signer, and any future broker or operator identity). One
  principal carries exactly one role. Per-key role assignment is refused:
  it is the shape that lets one key be two things.
- One key belongs to exactly one principal. This is `producer_keyring.py`'s
  existing alias refusal, generalized. Because a principal has one role,
  it also subsumes ADR-030's incompatibility matrix within the catalog:
  a key cannot hold two roles, because it cannot hold two principals.
- A principal has at least one key. Keys are `active` or `retired`. A
  retired key still resolves to its principal, so historical evidence stays
  attributable; it may not sign new work. A principal whose keys are all
  retired is a decommissioned identity, which is a legitimate state and not
  an error.
- If the `producers:` block is also present, every producer entry must
  appear in `principals` under the same id with that key active. The two
  blocks may not disagree about who a key belongs to.
- A `principals:` block that is present and empty is refused, for the reason
  the empty `producers:` block is refused: every lookup would fail, every
  gate would FAIL, and a deleted trust root would read as work never done.

### The limit this does not close, stated plainly

The catalog binds keys to principals. It cannot bind principals to humans.
A single operator who wants both roles can add a second principal with a
second key and approve their own work, and no test can tell that the two
principals are one person. That is true of every key-based identity system
and it is not fixed by adding fields.

What changes is where the lie has to live. Today it lives in an unrecorded
command-line argument. After this, it lives in a committed diff to the
trust root, reviewable, attributable and permanent. That is the control:
review, backed by a file that cannot be quietly ambiguous.

### Consequences

- `evaluate()` does not move. The catalog is an admission-layer input, like
  the keyring, for the same reason: a kernel whose judgement depended on
  ambient key material would break the credential-removal invariant.
  `test_kernel_unchanged.py` stays green.
- SLICE-081 (Evidence Envelope v1) can name a verifier principal, and
  SLICE-082 can require the approver to sign, because there is now
  something to check a signature against.
- `ranex keygen` will need to emit a `principals:` entry rather than a
  `producers:` line before the approver signature is required. That belongs
  to the slice that requires it, not to this one.
- The repository's own catalog gains `anthony` (worker) and
  `kernel-verdict-signer` (service). It gains no approver principal: one
  cannot be added without generating key material, and this decision does
  not create key material on the owner's behalf.

### Confirmation

`tests/contract/test_principal_catalog.py` pins the loader API and every
refusal above. `tests/security/test_slice080_principal_trust_root.py` pins
the attacks: one key under two principals, a role claimed that the catalog
does not grant, a retired key presented as a signer, and a `principals:`
block that disagrees with the `producers:` block it sits beside. The
existing keyring contract and security suites are unchanged and must stay
green, which is what proves this landed alongside the old trust root rather
than on top of it.
