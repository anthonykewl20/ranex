# ADR-057 — the signed verdict anchors the journal head

**Status:** accepted

**Date:** 2026-09-09
**Decision-makers:** repo owner
**Closes:** FINDINGS F-005 item 1 (the "independent history anchor"). Issue #93.

## Context

`Journal.verify()` recomputes the hash chain. Its own docstring states the
limit precisely: *"Without an external head this detects inconsistent edits,
not a complete replacement or truncation of a self-consistent chain."*

An attacker who rewrites the whole journal — deleting every row and reinserting
a new history with every link correctly recomputed from genesis — produces a
chain that verifies clean. So does truncation from a fresh head. Every
"tamper-evident" claim about the journal has therefore really meant
"partial-edit-evident". F-005 recorded this on 2026-09-03 and it stayed open.

`journal verify --expected-head` (2026-09-05) closed half of it: an operator
who retained a head out of band can compare. It relies on an operator having
done so, by hand, for every journal they might later need to trust.

## Decision

**The published verdict signs the journal chain link its own evaluation
created, as `journal_head`.** `Journal.append` already computed and returned
that link; `GateEvaluator.evaluate` was discarding it.

The anchor therefore lives *outside* the journal, in a record signed by the
**verdict signer** — a different key from the one that writes the journal — and
retained wherever verdicts are retained (`governance/verdicts/`, the GitHub
check publication). Rewriting history then means forging a head that a
separately signed, separately stored record already fixed.

`ranex journal verify --against-verdict <path>` performs the check. It reads
the head from a verdict it **verifies** — signature and record digest — never
from the file's raw bytes. An attacker who can rewrite the journal can also edit
an unsigned file beside it; reading the head out of that would anchor the chain
to itself, which is the exact circularity this ADR exists to remove.

### Versioning: v1 stays readable, and that is deliberate

`SIGNED_FIELDS` gains `journal_head`; the domain moves `ranex-verdict-v1` →
`v2` and the payload type with it. The domain string is inside the signed
bytes, so the two versions are cryptographically distinct — a v2 signature
cannot be replayed as v1 or the reverse.

The first implementation refused every older payload type outright, citing
ADR-011's evidence `v2 → v3` bump as precedent. **That precedent does not
transfer, and following it was a defect.** Evidence is produced fresh each run
and never re-read. Verdicts *are* re-read: `tools/dogfood/verify_repository_pilot.py`
exists to prove archived audits still verify, and the Leitir and Arxic pilot
receipts under `tools/dogfood/audits/2026-09-06-external/` are signed v1
history that cannot honestly be re-signed. A bump that made retained evidence
unverifiable would have destroyed the audit trail it was meant to protect. This
was measured against those real receipts, not predicted.

So the reader accepts every version in `VERSIONS`, verifying each against its
own domain and exact field set. What an old record may **not** do is decide
anything:

| path | v1 record | v2 record |
|---|---|---|
| archive verification (`verify_repository_pilot.py`) | verifies | verifies |
| `journal verify --against-verdict` | **refused — UNANCHORED** | head used |
| GitHub check publication | refused — anchorless | publishes |
| newly written verdicts | never | always |

Reading is permitted; deciding is not. A downgrade therefore buys an attacker
nothing, and the archive keeps its meaning.

A v1 record and a v2 record signed with **no journal configured** are
deliberately indistinguishable through `ReadResult.journal_head` — both `None`
— because the consequence is identical: there is no head to compare a chain
against. `payload_type` is carried on the result so the refusal can name which
case it was.

`journal_head` on `project_verdict` is keyword-only with **no default**. A
caller that forgets it fails loudly rather than publishing an unanchored
verdict that looks anchored. `None` is a value the record carries explicitly,
never a field it omits.

## What this does not establish

An operator holding **both** the journal and the verdict signing key can still
rewrite consistently. There is no external witness. That is the residual gap,
stated rather than glossed, and it is where a transparency-log anchor would
attach. It is not claimed closed.

## Confirmation

`tests/security/test_slice005_journal_anchor.py`:

- the finding itself, pinned: a complete rehashed rewrite and a truncation both
  pass `verify()`; if that ever fails, the chain gained a property it does not
  claim and the anchor may no longer be load-bearing;
- the same rewrite is refused against the head a verdict fixed;
- `journal_head` is inside the signed bytes — editing it in place breaks
  verification;
- the anchor is read only from a verifying verdict: a forged signature and an
  in-place edit both refuse;
- `read_verdict_unbound` drops the judgment-context match and nothing else,
  sharing one implementation with `read_verdict` so the two cannot drift;
- **the real committed Leitir and Arxic v1 receipts verify against their real
  signatures and report no anchor**;
- a v1 record cannot be used as an anchor.

## Prior art

- **sigstore-python 3.6.1** (Apache-2.0), read at source. Reference
  materialised from the PyPI sdist
  `sha256:ee60fdc9236fd6709271ad53b44027461360c3fde155d2af15482e4c451ff865`,
  recorded upstream identity
  `sigstore/sigstore-python@896cfe13105495e6dc6f8faf23e1007da35edeeb`; parity is
  *drift* (167 files only in git, 1 only in the sdist), so the checksum is the
  authority. `sigstore/_internal/rekor/checkpoint.py`: `LogCheckpoint(origin,
  log_size, log_hash)` wrapped in a `SignedNote`; `verify_checkpoint` runs the
  two stages this ADR needs — verify the signature on the checkpoint, then
  require `checkpoint_hash == inclusion_proof.root_hash`.
  **Weakness:** `verify_checkpoint` verifies against `rekor_keyring`, the
  **log's own key**. The party that could rewrite the log is the party that
  signs the head attesting it was not rewritten. Rekor's real defence is
  external witnesses and gossip, which that module does not implement.
  **Adopted:** the signed-head-plus-inclusion-comparison shape.
  **Improved:** the head is signed by a *different* key from the writer and
  retained *outside* the log. **Not improved:** no witness; see above.
- **Certificate Transparency (RFC 6962), Trillian `SignedLogRoot`, Go checksum
  database** — the same signed-tree-head pattern; cited as lineage, not read at
  source for this ADR.
- **ADR-011** — the evidence `v2 → v3` bump. Consulted, then correctly *not*
  followed for reading, for the reason above.

## Reversibility

Door: two-way, with a sharp edge that is the point. Removing `journal_head` from
`SIGNED_FIELDS` and reverting the domain restores the pre-2026-09-09 behaviour,
finding and all. Records already signed as v2 would then be the ones an old
reader refuses. Nothing in the append-only journal is invalidated either way;
the anchors simply stop being checked.
