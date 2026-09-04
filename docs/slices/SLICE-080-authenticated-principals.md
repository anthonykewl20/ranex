# SLICE-080 — authenticated principals at the trust root

**Status:** open
**Opened:** 2026-09-04
**Priority:** P1 — Week 2 objective, prerequisite for the evidence envelope
**ADR:** docs/adr/ADR-047-authenticated-principals-at-the-trust-root.md

## Contract

The committed trust root learns to say *what a principal is permitted to
be*, so that a later slice can require an approver to prove identity by
signature instead of by typing a name.

Acceptance:

- An additive `principals:` block in `governance/producers.yaml`, carrying
  identity, one role, and an ordered list of keys with `active` or
  `retired` status.
- A loader that fails closed on every malformed or ambiguous catalog, and
  that resolves a public key to its principal.
- The existing `producers:` block, `load_keyring`, `load_trust_keyring`,
  their contract test and every suite that writes `producers:` literally
  stay green and unedited.
- The repository's own catalog declares `anthony` and
  `kernel-verdict-signer`.

Out of scope, deliberately: any CLI change, any change to `evaluate()`,
any change to the evidence envelope, and any approver key material. Those
are SLICE-081 and SLICE-082.

## Owned paths

- Add: `src/ranex/policy/adapters/configuration/yaml/principal_catalog.py`
- Modify: `governance/producers.yaml` — additive `principals:` block only.
- Modify: `producer_keyring.py` — one line. `load_trust_keyring_text`
  pinned the document to exactly two blocks, so the block set had to admit
  `principals` before an additive block could exist at all. It is admitted
  and deliberately not parsed there; the catalog stays
  `principal_catalog`'s to read. Discovered by the live-trust-root test,
  not designed in.
- Tests: `tests/contract/test_principal_catalog.py` (new),
  `tests/security/test_slice080_principal_trust_root.py` (new).
- Docs close-out: this slice file to `docs/slices/done/`, `docs/STATE.md`,
  README completed-slices row.

Not touched: `verdict.py`, `admission.py`, `cli/main.py`,
`governance/gates.yaml`.

## Done criteria

1. Both new suites green; the full suite green on the final commit.
2. `tests/contract/test_producer_keyring.py` unchanged and green — proof
   the old trust root was extended, not replaced. The one edit to
   `producer_keyring.py` widens a closed set by exactly one admitted name;
   `test_the_trust_keyring_still_refuses_a_block_it_does_not_name` pins
   that the set is still closed.
3. `tests/contract/test_kernel_unchanged.py` green with `KERNEL_DIGEST`
   untouched — proof the kernel did not move.
4. Loading the repository's own `governance/producers.yaml` through the
   new loader yields both principals with their real committed keys, and
   the cross-block consistency check passes against the live file.

## Sad paths pinned

Each is a refusal test, not a comment.

1. `principals:` absent — the loader refuses; it does not return an empty
   catalog.
2. `principals: {}` present and empty — refused, for the reason an empty
   `producers:` block is refused.
3. One public key under two principals — refused (the alias attack that
   defeats no-self-approval by signing as either identity).
4. The same key listed twice inside one principal — refused.
5. An unknown role — refused. The vocabulary is closed.
6. A principal with no keys — refused.
7. An unknown key status — refused.
8. A key that is not a well-formed Ed25519 public key — refused.
9. An unexpected field on a principal entry — refused. The shape is closed.
10. A duplicate YAML key anywhere in the document — refused, reusing the
    existing no-duplicate loader; a trust-root replacement must never
    arrive disguised as an addition.
11. `producers:` and `principals:` disagreeing about who owns a key, or a
    producer absent from the catalog, or present with that key retired —
    refused. The two blocks may not give two answers.
12. A retired key is resolvable but may not sign: `resolve` returns its
    principal, `may_sign` is false.
13. An unreadable or non-YAML file — refused loudly, never an empty
    catalog.
14. A block the trust keyring does not name — still refused by
    `load_trust_keyring_text`. Admitting `principals` deliberately must
    not turn the document into an open one.

## Notes

The catalog binds keys to principals and cannot bind principals to
humans; ADR-047 records that limit and why review is the control on it.
The role vocabulary is ADR-030's, extended by `service`, so the
repository keeps one answer to what a role is.
