# SLICE-002 — evidence authenticity

**Status:** done
**Opened:** 2026-08-01
**Closed:** 2026-08-01 — 134 tests green; target frozen at `0b0512c2f`

## Why

`governance/evidence.json` is a plain array of unsigned records. Nothing in a
record says who produced it, so nothing distinguishes an observation from an
assertion. Subject binding already stops *stale* evidence — the same command run
against a different tree proves nothing about this one. Nothing stops
*fabricated* evidence.

Be precise about which problem this fixes. On a single machine it fixes almost
nothing: whoever can edit `evidence.json` can usually read the signing key too.
What it fixes is the case Ranex actually depends on — evidence produced on one
machine, verified on another that holds only public keys. Until that works,
"workers are untrusted and replaceable" is not implementable.

## Goal

Every evidence record carries an Ed25519 signature over its own canonical bytes,
bound to a producer whose public key is registered in a committed keyring. A
record that does not verify is not evidence, and absence blocks.

```
ranex keygen --producer worker              # private key outside the repo
ranex run --claim tests-executed --producer worker -- uv run pytest -q
ranex gate evaluate HEAD --approver reviewer_alice
```

## Format — pinned, because run and load must agree exactly

Ambiguity here produces a signature that one side computes and the other cannot
reproduce, so none of it is left to the implementer.

- **Signed payload:** `b"ranex-evidence-v1\n" + canonical_json_bytes(content)`.
  The domain-separation prefix is mandatory. Without it a signature over these
  bytes stays valid if the same key is ever reused to sign a different structure.
- **`content` is exactly these five fields**, no more: `claim_id`,
  `subject_digest`, `producer_id`, `command`, `exit_code`. Not "every key except
  `signature`" — an on-disk record carrying an unexpected extra field must be
  rejected, never silently signed over or silently dropped.
- **Signature encoding:** `ed25519:<base64>`, stored in a `signature` field
  alongside the five. Base64 fixed, so a record written on one machine verifies
  on another.
- **Keyring:** `governance/producers.yaml`, committed, mapping `producer_id` to
  `ed25519:<base64>` public key. **One public key may appear at most once.** Two
  producer ids sharing a key would let the holder sign as either identity and
  walk past no-self-approval; the loader must refuse such a keyring outright.
- The `Evidence` dataclass does **not** gain a `signature` field. The loader
  verifies, discards the signature, and constructs `Evidence` from the five.

## The trust chain, stated

The verdict is not a pure function of the evidence file alone, and pretending
otherwise would hide a real input:

```
raw records + keyring  ──admission──▶  admitted evidence  ──evaluate()──▶  verdict
                                       + structured rejections
```

`evaluate()` stays a pure function of `(gate, evidence, subject, approver)` and
is unchanged. The keyring is an input to **admission only** — never to the
kernel. Keys are ambient machine state, and a kernel whose judgement depended on
them would violate the principle behind "removing every model credential from
the machine must not change a verdict."

The consequence must be handled rather than ignored: because `evaluate()` sees
only admitted records, an `Evaluation` **cannot** distinguish forged from absent.
So admission must return rejections as **structured data**, not CLI prose — a
programmatic consumer has to be able to escalate forgery as an incident rather
than read it as missing work.

## Done criteria

Each must be met and proven by a test.

**Signing and verification**

- [x] `sign()` produces a detached Ed25519 signature over the pinned payload
      above, including the domain prefix
- [x] Signing the same record twice produces **identical** bytes — Ed25519 is
      deterministic per RFC 8032
- [x] Verification uses the key registered for **that record's exact
      `producer_id`**; a record signed by `alice` claiming `producer_id: worker`
      is rejected
- [x] Mutating any of the five signed fields invalidates the signature
- [x] A record with a missing, malformed, or non-verifying signature is rejected
- [x] A record carrying an unexpected extra field is rejected
- [x] A record whose `producer_id` is absent from the keyring is rejected

**Keyring — fail closed, every path**

- [x] A keyring that is missing, unreadable, invalid YAML, or holds a malformed
      key is a **distinct, loud failure**. Never "no evidence"
- [x] A keyring mapping one public key to two producer ids is **refused**
- [x] Duplicate `producer_id` entries are refused rather than resolved by
      last-wins

**Admission and reporting**

- [x] Admission returns admitted records **and** structured rejections, each
      carrying a machine-readable reason
- [x] Forged signature, unknown producer, and corrupt evidence file each produce
      a **distinct** reason. None may read as "no evidence for required claim"
- [x] A truncated or unparseable `evidence.json` is reported as file corruption,
      not as absence
- [x] `evaluate()` receives only admitted records, so forgery reaches the kernel
      as absence and absence blocks

**Producing**

- [x] `run` refuses to write when no signing key is available — nonzero exit,
      nothing written — rather than emit an unsigned record
- [x] `run` derives the public key from the private key and **refuses before
      executing** if it does not match the keyring entry for `--producer`.
      Otherwise it burns a full test run to write a record guaranteed to be
      rejected at load
- [x] `run` refuses a private key that is group- or world-readable

**keygen**

- [x] Writes to `$RANEX_SIGNING_KEY` with `0600`, prints the `producers.yaml`
      line, and refuses to overwrite an existing key
- [x] **Refuses to write inside the repository root or `.git`.** The whole
      premise is that private keys never enter the tree; an env var pointing
      inward must be rejected, not obeyed
- [x] Unset `$RANEX_SIGNING_KEY`, a relative path, or a path that is a directory
      each produce a clear error naming the variable

**Migration and end to end**

- [x] Existing unsigned records stop counting — rejected, not migrated
- [x] `evaluate()` is unchanged, proven by a digest assertion over
      `verdict.py`, so the criterion is checkable at test time rather than by
      reviewer memory
- [x] e2e: `keygen` → `run` → `gate evaluate` → PASS, exit 0
- [x] e2e: hand-edit a signed record's `exit_code` → FAIL, reason names
      signature rejection

## Out of scope

- **Approver authentication.** See the honesty section below — this is the
  largest hole left open and it is deliberate.
- **Key rotation, revocation, expiry.** One active key per producer.
- **Atomic evidence writes.** Non-atomic write and concurrent-run clobbering are
  pre-existing debts recorded in `STATE.md`. Signing verifies a complete file
  after the fact and does not touch the write path, so it does not make them
  worse. Absorbing an unrelated known debt because this slice happens to touch
  the same file is the scope creep the one-slice rule exists to prevent.
- **Command/claim binding.** This slice does not constrain which command may
  substantiate which claim. A signed record for a trivially passing command such
  as `true` remains valid evidence for `tests-executed`. Binding claims to
  approved commands or frozen test-plan digests is later work.
- Signing the journal or the gate catalog.
- OS keychain or external signer custody.
- Any change to `evaluate()`, gate semantics, or subject binding.

## Decisions taken

- **Ed25519 over HMAC.** HMAC's verifier holds the same secret that signs, so
  anyone who can check a record can forge one — that contradicts producer and
  approver separation at the crypto layer, which is the one property this slice
  exists to establish.
- **`cryptography` as a runtime dependency**, doubling a surface that was one
  package. There is no asymmetric primitive in the standard library, and
  `ssh-keygen -Y` would put a subprocess and an environment assumption in the
  verify path.
- **Public keyring committed, private key outside the repo.** The trust root is
  reviewable in git.
- **Verification at load, never inside `evaluate()`** — see the trust chain
  above.
- **Evidence is repository-agnostic by design.** A signed record binds a subject
  digest and a trusted producer, nothing else. Copying a record into another
  repository that trusts the same key and has a byte-identical tree is expected
  behaviour, not a vulnerability: the attestation is genuinely true of that
  tree. No repository identifier is added.

## What this does not buy

Stated plainly, because the temptation is to oversell it.

**It does not stop a local attacker.** Whoever can edit `governance/evidence.json`
can usually also read `$RANEX_SIGNING_KEY` and sign whatever they like. On one
machine this raises forgery from "text editor" to "steal the key first" and
nothing more. Agents here currently share the owner's credentials, so the local
machine is not a trust boundary at all.

**It does not make no-self-approval enforceable.** `--approver` is an
unauthenticated string. A producer can invoke `gate evaluate --approver
reviewer_alice` and the kernel, seeing `worker != reviewer_alice`, returns PASS.
Signing evidence proves *the worker ran the command*; it proves nothing about
who approved it or whether they were independent. This hole is pre-existing, not
introduced here, but after this slice it becomes the weakest link — and a signed
record makes a verdict *look* more trustworthy without making approval more
trustworthy. Until approvals are signed, treat no-self-approval as a convention,
not a control. This warning belongs at the `evaluate()` interface, not only here.

**It does not prove the command substantiates the claim.** A valid signature over
`command: "true"` still satisfies `tests-executed`.

**Key compromise invalidates history.** Removing or replacing a producer's key in
the keyring means every record that producer ever signed stops verifying. Gates
re-evaluated against that evidence will FAIL, and if the subject tree is gone
they can never PASS again. A keyring edit must be paired with re-running
production.

## Bootstrap

A fresh clone has no key, so every `ranex run` fails closed until `keygen` runs
and the resulting public key is committed to `producers.yaml` by review. A new
contributor's evidence is rejected until that lands. CI must inject the private
key as a secret. Failing closed is correct, but the wall is real and should
surprise nobody.

Rejected unsigned records stay in `evidence.json` and are re-reported on every
evaluation until removed by hand.

## If this slice will not finish in one session

Split here, do not carry it:

- **002a** — crypto, `producers.yaml`, admission, structured rejections. Tests
  sign with a fixture key.
- **002b** — `keygen`, `run` integration, the two e2e paths.

## Notes

`evaluate()` must not change. If this slice seems to require changing it, stop —
that is a signal the slice is wrong, not the kernel.

`governance/evidence.json` is gitignored and stays that way. Signing does not
make produced evidence a committed artifact.
