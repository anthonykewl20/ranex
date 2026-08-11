# ADR-019 — the verdict read channel

**Status:** proposed
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** `not yet opened — SLICE-017 holds the one-slice budget. This ADR and the structured cause it depends on must both land before that slice opens; BOARD-01 and BOARD-05..BOARD-14 queue behind it`

## Context and Problem Statement

The board renders what the kernel decided, and today it cannot read a verdict at
all. `packages/ranex/src/plugin/ranex.ts` is 38 lines and one-directional: on
session idle it commits the worktree and appends `{"task_id", "worktree",
"commit"}` to the path in `RANEX_EMIT`. Nothing returns. The kernel's only
verdict-producing command, `gate evaluate`, prints to stdout and has no `--json`
flag; measured, its sole machine-readable output is the journal row.

So `feature-plugins/board/index.tsx` ships a `createMemo` hard-coded to
`undefined` and a screen that says so. ADR-018 waved at "reading durable state
through the existing SDK", which named no source for that state.

The reader is hostile-capable: it is the same process that runs the coding agent,
and `host_confinement.py` is imported nowhere in `src/`, so the harness is a
plain `Popen` with a five-variable environment and ordinary uid-level filesystem
access. It must not read the journal, hold a key, or forge a verdict on screen.

## Decision Drivers

- Absence blocks. "No verdict read" and "a verdict proving nothing" must never
  render alike, and neither may look like a pass.
- The kernel is a short-lived CLI that exits; the UI is long-lived and may attach
  long after the verdict was written.
- The kernel judges, the harness collects. No verdict logic crosses the wall.
- Verdict content must not vary with the destination (ADR-018, rule 1).
- Whatever is built must survive the harness being compromised without lying.
- The fork stays mergeable: no upstream file is rewritten to carry this.

## Prior art

Searched: GitHub **code** search (`gh search code`) and `gh api` tree enumeration
at pinned commits, over signed-statement verification, local producer/consumer
transport under asymmetric trust, and torn-write recovery. Tags were dereferenced
to 40-hex commits and every raw URL fetched and hashed. Specifications excluded.

- [securesystemslib DSSE envelope](https://github.com/secure-systems-lab/securesystemslib/blob/47b0f4512fe974d6df75dbd4ad62c2642d4e5806/securesystemslib/dsse.py)
  signs a length-prefixed pre-auth encoding over payload type and payload, so the
  verifier authenticates received bytes, never a structure it re-serialised.
  License: MIT.
  Weakness: `verify` never asserts `payload_type`, so a genuine signer's envelope
  for another purpose unwraps cleanly; zero signatures raise a forgery's error.
  Vendored: docs/adr/prior-art/ADR-019/securesystemslib-dsse.py blob:d41abec92618093ef6daba90a1f82fae087b8c40
- [kubelet file store](https://github.com/kubernetes/kubernetes/blob/a57b6f7709f6c2722b92f07b8b4c48210a51fc40/pkg/kubelet/util/store/filestore.go)
  writes one file per key through a `.`-prefixed temp and `Rename`, skips that
  prefix when listing, and returns `ErrKeyNotFound` for absence, not an empty value.
  License: Apache-2.0.
  Weakness: integrity is a 32-bit FNV over a reflected Go object, not the file
  bytes — accident-detecting, authorship-proving never — and orphans are unswept.
  Vendored: docs/adr/prior-art/ADR-019/kubelet-filestore.go blob:17c313602ad99ed23089496fedb86e391a3a625a
- [cosign exit-code lookup](https://github.com/sigstore/cosign/blob/11926fa5bbbbde47e88fc006b625a17769b743b2/cmd/cosign/errors/exit_code_lookup.go)
  maps typed errors to distinct exit codes — 10 no signature, 12 no matching
  signature — so a consumer reading no Go types still parts absence from invalid.
  License: Apache-2.0.
  Weakness: on the blob path a missing signature file is reinterpreted as the
  signature string, bypassing `ErrNoSignaturesFound` — absence reported as invalid.
  Vendored: docs/adr/prior-art/ADR-019/cosign-exit-code-lookup.go blob:7b038d5a9fa02575f2bbcd7173a847d22c310236
- [python-tuf trusted metadata set](https://github.com/theupdateframework/python-tuf/blob/353bdb767db56fd4667c9bcf56b710d50fdc2ac0/tuf/ngclient/_internal/trusted_metadata_set.py)
  refuses a genuine, correctly-signed document whose version is not greater than
  the trusted one (`BadVersionNumberError`): validity and freshness are separate.
  License: MIT OR Apache-2.0, per the file's SPDX header. Taken under MIT.
  Weakness: its loader skips verification when called without a delegator and
  returns an object indistinguishable from a verified one — default-open.
  Vendored: docs/adr/prior-art/ADR-019/tuf-trusted-metadata-set.py blob:689eef01de665280434e4c3d8ccdc63f4431b67b
  Vendored: docs/adr/prior-art/ADR-019/LICENSE-APACHE-2.0.txt blob:261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64

Rejected: [Tailscale LocalAPI](https://github.com/tailscale/tailscale) authenticates its peer with
kernel-attested `SO_PEERCRED`, the only unforgeable identity read here — but a socket is a
rendezvous, not a record, and this kernel has exited by the time the board opens.

Rejected: [systemd-journald](https://github.com/systemd/systemd) publishes a committed
`tail_object_offset` in the file header, the best cross-process torn-write defence in the survey.
LGPL-2.1-or-later, so it may not be copied into this MIT tree: mechanism only, no bytes.

Rejected: [in-toto](https://github.com/in-toto/in-toto) gives absence its own `LinkNotFoundError`,
the best absence handling found. GitHub resolves its licence as `NOASSERTION` — the ground ADR-018
refused conftest on — so it is not vendored, though its own SPDX headers say Apache-2.0.

## Considered Options

1. **Signed file per subject digest**, published by atomic rename, read by path.
2. **Append a signed record to a spool** named by an environment variable, the
   existing emit channel run backwards.
3. **A long-lived kernel daemon** on a unix socket, authenticated by `SO_PEERCRED`.
4. **The harness shells out** to `ranex gate evaluate` and parses stdout.
5. **A read-only SQLite projection** the kernel writes and the harness opens.

## Decision Outcome

In the context of a short-lived judging kernel and a long-lived untrusted reader,
facing a channel that runs only one way, we chose **option 1 — one signed file
per subject digest, published by atomic rename into a directory the harness may
read and not write** — so that an unfinished write is unnameable and absence is
`ENOENT`, accepting a third signing domain and a second place a verdict appears.

Option 2 keeps the torn record: `_read_emission` already refuses a truncated
final line rather than falling back, and that refusal is correct for a channel
the kernel controls but wrong for one the board must read at any moment. Option 3
cannot serve a reader that attaches after the writer exited. Option 4 hands the
untrusted process the choice of when judging happens and with which arguments.
Option 5 is option 1 with a database in the way.

Door: two-way

### Consequences

- Good: the three failures stay apart — no file, a file that will not verify, and
  a genuine verdict about a different tree are distinct states, not one blank.
- Good: verification needs a public key the keyring already publishes, and
  `verify_evidence` already returns `False` rather than raising.
- Good: signing the transmitted bytes removes the canonical-JSON problem whole;
  the reader never re-serialises, so Python and TypeScript cannot disagree.
- Bad: a third signing domain joins `ranex-evidence-v3` and `ranex-approval-v1`,
  and three domains is the point at which someone will reach for a generic one.
- Bad: a verdict now exists in two places — the journal and the published file —
  and they can disagree if publication is not bound to the append.
- Neutral: the board still cannot act. This channel is read-only by construction.

### Confirmation

Frozen red-first tests, reviewed against the diff on disk rather than a summary.
The publication path is asserted to reuse the atomic writer already in the tree
rather than a second one, the reader's state set is asserted total over its
closed cases, and a torn or truncated file is asserted unreadable by name rather
than caught by a parser. Independent review, then a mutation gate over the
touched kernel files. This ADR carries **no outside-model panel**: the OpenRouter
credential had expired when it was written and re-authorisation is the owner's,
so the design has had no adversarial reading beyond the author's own and the
prior art. That is a real gap in confirmation, recorded rather than papered over.

## Improvements on the prior art

Every signed-statement system read here collapses absence into invalidity
somewhere. securesystemslib raises one `VerificationError` for zero signatures
and for forged ones. python-tuf files "nobody signed" and "someone forged" in the
same `unsigned` dict, with the difference surviving only in an INFO log. in-toto
separates them at the file layer and re-merges them at the threshold. That is the
defect that reopened SLICE-002, found five more times in mature code, so the
distinction is carried in the reader's state instead of a counter.

cosign is the exception worth copying, and the improvement is where the table
lives. Its exit codes classify at the *process* boundary and one call site
bypasses them; here the classification happens once, at deserialisation, and the
renderer receives a value it cannot widen — the point Kyverno proves by handling
one five-value set four different ways in a single file.

containerd and kubelet both publish by rename and both omit the parent-directory
fsync, so the record is atomic and not durable. `_write_report_atomic` in
`host_confinement.py` opens a dot-prefixed temp with `O_EXCL` at mode `0o444`,
fsyncs it, replaces through a directory descriptor, then fsyncs the parent with
rollback — the stronger writer is already here, and reusing it is the improvement.

python-tuf is the only candidate that treats freshness as separate from validity.
Binding to a subject digest proves a verdict is *about* this tree; it does not
prove it is the *current* one, so a superseded PASS still verifies. The journal's
monotonic sequence closes that, and no other candidate addresses it at all.

## Architecture surface

Added: a publication step in the kernel writing one signed envelope per subject
digest under a gitignored directory, and a reader in the harness that verifies it
with a public key alone. Added: a third domain constant beside `EVIDENCE_DOMAIN`
and `APPROVAL_DOMAIN`, with its own exact `SIGNED_FIELDS` tuple.

Changed: `Evaluation` gains the structured per-claim cause ADR-018 committed to;
its shape is not decided here. Publication binds the journal append.

Unchanged: `evaluate()`, the journal schema, the emit channel, and every upstream
harness file. The board issues no verdict, holds no key, and writes nothing.

## Scope and threat delta

STRIDE. Spoofing: a process writing the directory cannot mint a verdict without
the private key, and the reader refuses an unknown producer. Tampering: an edited
envelope fails Ed25519; a replaced one fails the sequence check. Repudiation: the
published file is a projection, never the journal, and the journal still leads.
Information disclosure: no secret reaches the harness; the keyring is already
committed and world-readable. Denial of service: the reader refuses rather than
crashes, matching `verify_evidence`'s contract.

Non-goals: approval, merge, publication, and any action from the board. Out of
scope: confining the harness, which is RISK-06 and ADR-006's unbuilt sad path.

## Quality attributes

- Determinism: the same durable state publishes byte-identical bytes.
- Honesty: a state the reader cannot classify renders as unclassified and blocks.
- Legibility: the operator can verify the same file the board read, by hand.
- Mergeability: the harness change is confined to Ranex-owned files.
- Durability: a verdict survives the kernel exiting and the machine losing power.
- Latency is explicitly not a quality attribute; correctness outranks it.

## Reversibility

Door: two-way

Deleting the publication step and the reader returns the harness to the screen it
shows today, and the kernel to a CLI that prints. Nothing depends on the channel:
the journal remains the record, and `gate evaluate` remains the authority.

The one-way part is the third signing domain. Once a verdict has been signed
under `ranex-verdict-v1` and read by anything, the domain string is load-bearing
and may be superseded but not reused.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | No file for this subject digest | "no verdict read" as its own state; never an empty table, never a pass |
| 2 | Kernel crashes mid-write | the temp name is never the read name; the reader sees case 1, not a torn file |
| 3 | Envelope parses but the signature fails | render unverified and say so; never fall back to the nearest familiar state |
| 4 | Signature valid, producer not in the keyring | refuse: an unknown signer is not a verdict, and is distinct from a bad signature |
| 5 | Signature valid, `payload_type` is not the verdict type | refuse — the flaw securesystemslib leaves open |
| 6 | Envelope carries zero signatures | refuse as unsigned, not as below-threshold; these are different events |
| 7 | Genuine verdict, older journal sequence than one already read | refuse as superseded; a replayed PASS is not the current PASS |
| 8 | Verdict is genuine but names another subject digest | show both digests; never merge two reads into one row |
| 9 | Reader lacks a public key entirely | refuse; absence of trust material is not absence of a verdict |
| 10 | Keyring is empty | already refused by `load_keyring`; the reader must refuse too, not read zero keys as zero constraints |
| 11 | Two files exist for one subject digest | impossible by name; if the directory is manipulated, the digest mismatch in case 8 catches it |
| 12 | The harness is compromised | it can draw anything on screen, signature or not. The channel does not defend this and must not claim to; the operator's recourse is the CLI |
| 13 | The published file is deleted between list and read | case 1, not an error dialog; the state is recomputed, never cached as a pass |
| 14 | Payload carries a float, a big integer, or a non-BMP key | refuse at publication: those are the three measured places Python and TypeScript canonicalisation diverge |
| 15 | Directory is writable by the harness | a deployment defect, not a runtime one; the qualification check refuses to publish there |
| 16 | A cause arrives that the reader does not know | render as unclassified and block; never the nearest known cause |

## Test strategy

Frozen before build, read-only to implementers, red then green. New filenames and
exact test names belong to the slice; the files below already exist and are where
the existing behaviour is pinned.

- `tests/unit/test_evidence_signing.py` — extends to the third domain: a verdict
  envelope signed under `ranex-verdict-v1` must not verify under the evidence
  domain, and the exact-field-set refusal must hold for the new tuple.
- `tests/contract/test_producer_keyring.py` — the public key a reader needs is
  reachable from the committed keyring, and an empty keyring still refuses.
- `tests/unit/test_gate_verdict.py` — `Evaluation` gains its field without
  changing `reason` byte-for-byte, and `record_digest` stays stable.
- `tests/contract/test_verdict_presentation.py` — the published bytes and the
  bytes printed to stdout describe the same verdict, and neither varies with TTY.
- `tests/unit/test_delegation.py` — the reader's directory is not writable by the
  child environment, and no new variable leaks a key into it.

Additionally, and belonging to the slice: a publication test that kills the writer
between temp-write and rename and asserts the reader reports case 1; a table test
asserting the reader's state mapping is total, with no default arm; and a test
that a payload containing a float is refused at publication rather than at read.

## Code review checklist

- Does any renderer parse `reason` prose to recover a cause? It must not.
- Is the reader's state mapping total, or is there a default arm that can absorb
  a case nobody handled?
- Does publication reuse `_write_report_atomic`, or is there a second writer?
- Is `payload_type` asserted, not merely authenticated?
- Can absence, bad signature, unknown producer and superseded be told apart from
  the reader's return value alone, without reading a log line?
- Does anything in the harness compute a verdict, rather than display one?
- Is the published directory gitignored, so the dirty-tree check stays honest?

## More Information

Supersedes nothing. Depends on ADR-018, which decided the board exists and that
`Evaluation` would gain a structured cause without deciding its shape; that shape
needs its own decision and is not made here.

ADR-008 set the wall this channel crosses, and ADR-014 set the emit record it
mirrors. ADR-011 governs the disclosure above that no outside panel ran.

The harness-side contract already landed as `packages/schema/src/verdict.ts` in
the fork, and fixes the payload shape this envelope carries. RISK-06 stays open:
the harness is unconfined, which is why the channel is signed rather than trusted
to filesystem permissions alone.
