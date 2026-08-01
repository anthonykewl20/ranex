# SLICE-002 — evidence authenticity

**Status:** open
**Opened:** 2026-08-01

## Why

A PASS is currently forgeable with a text editor. `governance/evidence.json` is a
plain array; appending a record with `exit_code: 0` and the right
`subject_digest` produces a PASS that no check can distinguish from a real one.

Subject binding already stops *stale* evidence — the same command run against a
different tree proves nothing about this one. Nothing stops *fabricated*
evidence. Until a record carries proof of who produced it, "the kernel judges by
evidence" is only true against honest inputs, which is not a governance claim.

## Goal

Every evidence record carries an Ed25519 signature over its own canonical bytes,
bound to a producer whose public key is registered in a committed keyring. A
record that does not verify is not evidence, and absence blocks.

```
ranex keygen --producer worker              # private key outside the repo
ranex run --claim tests-executed --producer worker -- uv run pytest -q
ranex gate evaluate HEAD --approver reviewer_alice
```

## Done criteria

Each must be met and proven by a test.

- [ ] `sign(record, private_key)` returns a detached Ed25519 signature over
      `canonical_json_bytes` of the record's content fields, with the
      `signature` field itself excluded from the signed bytes
- [ ] Signing the same record twice produces **identical** bytes — Ed25519 is
      deterministic per RFC 8032, and a nondeterministic signature would make
      evidence records differ run to run for no semantic reason
- [ ] `governance/producers.yaml` maps `producer_id` to an Ed25519 public key
      and is **committed**. It is the trust root; review is the control on it
- [ ] Verification uses the key registered for **that record's exact
      `producer_id`**. A record signed by `alice` but claiming
      `producer_id: worker` is rejected — otherwise an approver could produce
      evidence under another name and defeat no-self-approval
- [ ] A record whose `producer_id` is absent from the keyring is **rejected**,
      never trusted by default
- [ ] A record with a missing, malformed, or non-verifying signature is
      **rejected**
- [ ] Mutating any signed field — `claim_id`, `subject_digest`, `producer_id`,
      `command`, `exit_code` — invalidates the signature
- [ ] Loading returns admitted records **and** rejections. `evaluate()` receives
      only admitted records, so a forged record reaches the kernel as absence
      and absence blocks
- [ ] The CLI reports rejections distinctly: a forged record must not read as
      "no evidence for required claim". Same verdict, different stated reason
- [ ] `run` **refuses to write** when no signing key is available (nonzero exit,
      nothing written), rather than emit an unsigned record
- [ ] `keygen` writes the private key outside the repository at the path from
      `$RANEX_SIGNING_KEY`, with `0600` permissions, and prints the public key
      line for `producers.yaml`. It refuses to overwrite an existing key
- [ ] Existing unsigned records stop counting. They are unverifiable, so they
      are rejected — no migration, no grandfathering
- [ ] `evaluate()` is byte-for-byte unchanged
- [ ] e2e: `keygen` → `run` → `gate evaluate` → PASS, exit 0
- [ ] e2e: hand-edit a signed record's `exit_code` from 1 to 0 → FAIL, and the
      reason names signature rejection

## Out of scope

- **Key rotation, revocation, and expiry.** One active key per producer. A
  compromised key is handled by editing the committed keyring.
- Multiple simultaneous keys per producer.
- Signing the journal, the gate catalog, or the approval itself. Approver
  identity stays unauthenticated in this slice — only *production* is proven.
- OS keychain or external signer custody. Decided against for now; see below.
- **Command/claim binding.** This slice does not constrain which command may
  substantiate which claim. A signed record for a trivially passing command
  such as `true` remains valid evidence for `tests-executed`. Binding claims to
  approved commands or frozen test-plan digests is later work.
- Any change to `evaluate()`, to gate semantics, or to subject binding.

## Decisions taken

- **Ed25519 over HMAC.** HMAC's verifier holds the same secret that signs, so
  anyone who can check a record can forge one. That contradicts producer and
  approver separation at the crypto layer. Asymmetric keys make "the verifier
  cannot forge" true rather than assumed.
- **`cryptography` as a runtime dependency.** This doubles the runtime
  dependency surface, which was one package. Accepted: there is no asymmetric
  primitive in the standard library, and shelling out to `ssh-keygen -Y` would
  put a subprocess and an environment assumption in the verify path.
- **Public keyring committed, private key outside the repo.** The trust root is
  reviewable in git. Private keys live at `$RANEX_SIGNING_KEY` and never enter
  the tree.
- **Verification happens at load, not inside `evaluate()`.** The kernel stays a
  pure function of (gate, evidence, subject, approver); adding a keyring
  parameter would change its signature and its meaning. A record that does not
  verify is simply not admitted as evidence.
- **Rejections are reported, not swallowed.** Dropping a forged record silently
  would make forgery indistinguishable from absence in the output. Both FAIL,
  but they must not read the same.

## What this does not buy

Stated plainly, because the temptation is to oversell it.

This does **not** stop an attacker with local filesystem access. Whoever can
edit `governance/evidence.json` can usually also read `$RANEX_SIGNING_KEY` and
sign whatever they like. Signing raises forgery from "text editor" to "steal the
key first", and nothing more, on a single machine.

It also does not prove that the recorded command substantiates the named claim.
A valid signature over `command: "true"` still satisfies `tests-executed`.

What it does buy is the case Ranex actually needs: evidence produced on one
machine can be verified on another that holds only public keys. That is the
precondition for workers being remote and untrusted, which every later slice
assumes.

## Notes

`evaluate()` must not change. If this slice seems to require changing it, stop —
that is a signal the slice is wrong, not the kernel.

`governance/evidence.json` is gitignored and stays that way. Signing does not
make produced evidence a committed artifact.
