# SLICE-002 — evidence authenticity

**Status:** done
**Opened:** 2026-08-01
**Reopened:** 2026-08-01 — closed prematurely on tests narrower than reality
**Closed:** 2026-08-01 — 156 tests green; 17 defects from four independent audits
**Reopened:** 2026-08-02 — the committed-trust-root criterion below was ticked
and false. The check was skipped entirely for a path the ref did not carry, so
the party being gated chose the file by choosing the flag.
**Closed:** 2026-08-02 — `docs/adr/ADR-002-committed-trust-root.md`; 238 green.

> **Superseded in part by SLICE-003.** The pinned format below says
> `ranex-evidence-v1` and five signed fields. It is now `ranex-evidence-v2` and
> seven — `command_digest` and `executable_path` were added and the domain
> string moved with them. Read `docs/adr/ADR-001-claim-command-binding.md` for
> the current format; the section below is kept as the record of what this slice
> decided, not as a description of the code.

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
      (false as first shipped — four base64 spellings of one key were four
      identities; now canonical-only, and tested)
- [x] Duplicate `producer_id` entries are refused rather than resolved by
      last-wins

**Admission and reporting**

- [x] Admission returns admitted records **and** structured rejections, each
      carrying a machine-readable reason
- [x] Forged signature, unknown producer, and corrupt evidence file each produce
      a **distinct** reason. None may read as "no evidence for required claim"
      (false as first shipped on any multi-claim gate; now partitioned per
      claim, including refusals that name no claim at all)
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

## Defects — why this slice reopened

Closed at `7f6cd3779` with 134 tests green. Two independent auditors then found
12 defects, and two of the ticked criteria above were provably false. They passed
only because the tests were narrower than reality: one compared the same string
to itself, the other used a single-claim gate while this repository's real gate
requires two.

A slice is finished when every criterion is met **and a test proves it**. These
tests proved less than they appeared to, so the slice was not finished.

**Blockers**

- [x] Non-canonical base64 is accepted, so one key has 4 valid encodings and the
      one-key-one-producer rule is one character away from defeat
- [~] The observed command inherits `$RANEX_SIGNING_KEY`. **Mitigated, not
      closed** — see the honesty section. The variable is stripped, which stops
      nothing determined: a same-uid child reads `/proc/$PPID/environ`
- [x] `keygen` writes a committable key into a linked worktree of the same
      repository, which shares the object store
- [x] A gate requiring several claims reports a forged claim as honest absence

**Should fix**

- [x] Rejections are invisible on the PASS path and absent from the journal
- [x] `producers: {}` returns an empty keyring instead of failing closed
- [x] An unreadable evidence file is reported as an absent one
- [x] `run` executes the command before discovering it cannot write the record
- [x] The refusal summary discards the kernel's own reason, losing the
      actionable "bound to a different subject digest" diagnosis

**Found auditing the fixes, then fixed**

- [x] `run` re-checked only HEAD after the command, so a command could edit a
      tracked file, run, revert and exit 0 — an unearned PASS needing no crypto
      bug, with the journal corroborating it
- [x] `skip-worktree` hid a modification from the dirty-tree check
- [x] The keyring and gate catalog were read from the working tree, so an
      uncommitted edit decided a verdict. "Review of the committed keyring is
      the control" was unenforced, so the control did not exist
- [x] `seen.add` sat outside the guard meant to catch unhashable YAML keys
- [x] A rejection carrying no `claim_id` printed under the wording reserved for
      honest absence, letting an attacker pick the phrasing
- [x] `--evidence` exempted any named tracked file from the dirty-tree check

**Minor**

- [x] `keygen`'s containment check is check-then-open; the parent-directory
      TOCTOU was won 22 times in 200 attempts

**Found on 2026-08-02, auditing SLICE-003 — the second reopen**

The trust-root criterion above was ticked because an *edit* to a committed file
was caught. Nobody asked what happened to a path no commit carried.

- [x] `--gate-catalog attacker-gates.yaml` — a file HEAD does not carry was read
      unchecked and decided the verdict. Reproduced to PASS
- [x] `--producers` under a committed `.gitignore` — same hole, and
      `git status --porcelain` stays completely empty, so the one signal an
      operator watches shows nothing at all
- [x] A committed **symlink** at a reviewed name: resolution followed it before
      git was asked, so git was asked about the target and the reviewed name was
      never consulted. Committing the indirection once rewrites policy forever
- [x] Trust-root TOCTOU — the bytes were compared and the loaders then reopened
      the same name, so checked bytes and deciding bytes were two reads of a file
      the worker can replace in between. Now the committed **bytes** are returned
      and parsed; `strace` confirms one open per file where there were three and
      two
- [x] `run` accepts a signing key stored inside the repository, which `keygen`
      refuses to create
- [x] Two error paths accuse the wrong thing: an unhashable YAML key escapes as
      `TypeError`, and an unencodable string is reported as a bad signature when
      no verification took place

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

**It does not keep the key from the worker.** The observed command no longer
inherits `$RANEX_SIGNING_KEY`, and that is worth doing, but it is a speed bump
and must not be described as more. A child running as the same user reads
`/proc/$PPID/environ`, and can read the key file whatever the environment says.
Verified, not assumed. While the signer runs as the same user as the work it
observes, a determined worker can sign its own verdict. Closing that needs the
signer out of the worker's reach — a different uid, or a separate process the
worker cannot address — which is architecture, not a patch, and is not in this
slice.

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
`command: "true"` still satisfies `tests-executed`. Closed by SLICE-003.

**The keyring refuses one key under two names, and not two names that look the
same.** The one-key-one-producer rule above holds — verified. But
`producer_id` is any non-empty string, so `alice` and `alice` followed by a
zero-width space are two producers to the loader and one to a reviewer, and
either can produce evidence the other appears to approve. No-self-approval is
string equality over a pair the attacker picks. Found 2026-08-02, not fixed;
it belongs with approver authentication in SLICE-005, and it is strictly smaller
than the hole below, which needs no trick at all.

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
