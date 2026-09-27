# ADR-067 — external verdict witness in a Rekor transparency log

**Status:** accepted

**Date:** 2026-09-27
**Decision-makers:** repo owner
**Closes:** MAP RISK-19 residual (journal rewrite under dual-key control) and
RISK-03's outward-facing record gap, for the verdict publication path. Issue #108.

## Context

ADR-057 signed the journal head into the verdict. An operator who holds **both**
the journal and the verdict signing key can still rewrite consistently: truncate
the journal, re-evaluate, re-sign. The local `--against-verdict` check accepts
the new self-consistent pair. There is no external witness neither key controls.

MAP §15.3 already names the prior art (Sigstore Rekor, Trillian). Adoption form:
stdlib HTTP client, no new dependency, the log's public key pinned in
`governance/` as a trust root.

## Decision

1. **Witness step** after `publish_verdict`, behind opt-in `--witness`. Wrap the
   canonical verdict envelope bytes in a DSSE envelope (payload type
   `application/vnd.ranex.verdict.v2+json`, pure Ed25519 over the PAE bytes by
   the verdict signer) and submit it as a Rekor `dsse` entry to
   `https://rekor.sigstore.dev` (or `RANEX_WITNESS_URL`). Store the returned
   entry UUID, log index, integrated time, body and inclusion proof beside the
   verdict as `<subject>.witness.json`. A failed submission is operational
   refusal (exit 2) and the published verdict is removed — never silently
   unwitnessed. A Rekor 409 (equivalent entry exists) is success: fetch that
   entry and write the witness from it.
2. **Verification** `journal verify --against-verdict --witnessed`: recompute
   the payload digest of the local verdict, verify the inclusion proof against
   the pinned log public key (owned RFC 6962/9162 Merkle verifier in
   `src/ranex/foundation/merkle.py`), verify the checkpoint signature, and
   require the witnessed digest to equal the local verdict. An outsider can
   repeat this with the UUID alone.
3. **Why DSSE, not `hashedrekord`.** Rekor's `hashedrekord` verifies Ed25519
   only in the pre-hashed Ed25519ph form; Ranex signs pure Ed25519 with
   `cryptography`, which has no Ed25519ph. The `dsse` type carries the payload,
   so pure Ed25519 verifies. The DSSE envelope is also the interoperable form
   of a Ranex verdict for policy engines that speak in-toto.

## What this buys

A rewrite of the journal plus a re-signed verdict produces a different digest
with a later integrated time; the earlier entry remains in a log neither key
controls. That closes the residual ADR-057 left open. RISK-19 is restated
**closed-with-witness** for the witnessed publication path; an unwitnessed
verdict retains the prior residual.

## Prior art

- **sigstore/rekor@904bbccce4df5e63c30209d7b7a00d9dda5400d6** — the `dsse` entry
  type and inclusion-proof response shape.
  Vendored: `docs/adr/prior-art/ADR-067/rekor-dsse_v0_0_1_schema.json` blob:51ebe3990afb6a22019e31e53252a45c72e6e48f
  Vendored: `docs/adr/prior-art/ADR-067/rekor-dsse-entry.go` blob:c1798c9966aa022861423afdacb5e4c475947f83
- **transparency-dev/merkle@fbbcd741c3d1c69d8498487baa8edc9e5824847c** — RFC 6962
  leaf/node hashes and inclusion-proof walk.
  Vendored: `docs/adr/prior-art/ADR-067/merkle-verify.go` blob:7aa9e84e364cc54528cc9d540535b74023c3a826
  Vendored: `docs/adr/prior-art/ADR-067/merkle-rfc6962.go` blob:ab109c7acb3ac4019c8f12291968428f27f6cb84
- **google/trillian@0362d55869965067c9ffa276a78d18e95a596ca3** — hasher reference.
  Vendored: `docs/adr/prior-art/ADR-067/trillian-hasher.go` blob:6fb147699e08a55ad31d8cd2e9dd60c2e9bbb7b8
- **secure-systems-lab/dsse@440901313676fedd0e31f16125c302b0df81e006** — PAE and
  envelope shape (also under ADR-025).
  Vendored: `docs/adr/prior-art/ADR-067/dsse-signing_spec.py` blob:0e5fea3c59e8cd1a8eae8c5442355c5d401bd813

## Consequences

- `governance/rekor_public_key.pem` is a trust root. Rotating it is a deliberate
  promote ship.
- `--witness` requires verdict publication env (`RANEX_VERDICT_*`).
- KERNEL_DIGEST / `verdict.py` unchanged.
- No new runtime dependency.

## Confirmation

`tests/e2e/test_witness_rekor_real.py` — five real-network arms per issue #108 /
#95 protocol (positive, negative, repeats).
