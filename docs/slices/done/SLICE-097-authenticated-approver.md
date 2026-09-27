# SLICE-097 — Authenticated approver (possession before judgment)

**Status:** done
**Origin:** GitHub issue #107 / MAP RISK-07; ADR-066.

## Contract

`approver_id` stops being an unauthenticated string. A catalogued principal with
`role: approver` must prove key possession before `evaluate()` runs, and the
published verdict carries that principal's Ed25519 signature beside the verdict
signer's. `verdict.py` / `KERNEL_DIGEST` are unmoved.

## Delivered

- CLI possession gate (`E-APPROVER-*` codes) before judgment.
- Dual signature in `signatures[]`; reader `UNAPPROVED` when the approver
  signature is absent or bad.
- Receiver env pass-through for the approver key.
- Real e2e seven arms + dogfood receipt 11/11 VERIFIED
  (`tools/dogfood/audits/2026-09-26-approver-authentication/`).

## Out of scope

Witness / Rekor (RISK-19, #108); observation log (RISK-11, #109).
