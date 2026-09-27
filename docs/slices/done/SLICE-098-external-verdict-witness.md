# SLICE-098 — External verdict witness (Rekor / DSSE)

**Status:** done
**Origin:** issue #108; ADR-067; MAP RISK-19 / RISK-03.

## Contract

Opt-in external witness for published verdicts:

- `src/ranex/foundation/dsse.py` — PAE + pure Ed25519 DSSE envelopes
- `src/ranex/foundation/merkle.py` — RFC 6962/9162 inclusion verifier
- `src/ranex/governed_execution/witness.py` — Rekor `dsse` submit + verify
- `governance/rekor_public_key.pem` — pinned log public key
- `gate evaluate --witness` — submit after publish; refuse (exit 2) and remove
  the verdict on failure; coalesce on HTTP 409
- `journal verify --against-verdict --witnessed` — digest + inclusion + checkpoint
- e2e: `tests/e2e/test_witness_rekor_real.py` (five real-log arms)

KERNEL_DIGEST unchanged. No new runtime deps.
