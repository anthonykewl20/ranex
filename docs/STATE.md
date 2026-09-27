# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097 / #107 (authenticated approver) closed.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**. Freeze `governance/architecture-freeze.json`
  (`approved_by: ADR-065`), digest pin
  `sha256:d463e3c97475c1971758415b07d072469385e33700081656d9d632acc3a58f72`,
  manifesto `governance/arch/scan-manifest.json` (file-level scopes under
  declared modules), landing claim `architecture` via `ranex-arch check …`.
- BASE `ranex promotion evaluate` unchanged (arch wiring ≠ BASE promotion).

**#107 / RISK-07 closed:** catalogued `role: approver`, CLI possession
before `evaluate()`, second Ed25519 signature in the verdict; reader
`UNAPPROVED` without it. `verdict.py` / `KERNEL_DIGEST` unmoved. Receipt:
`tools/dogfood/audits/2026-09-26-approver-authentication/` (11/11 VERIFIED).

**#102 / SLICE-100 / ADR-069 closed:** delegated review SARIF — packet at
`governance/review-packet.json`, #97 admission with captain rulings
(anchor re-derive, prose-free fingerprints, findings advisory-only).
Receipts: `tools/dogfood/audits/2026-09-27-delegated-review/` (six arms
VERIFIED ×3).

**Closed this lane (#112 / SLICE-101 / ADR-070):** minimization ladder as
handbook system layer — adapted ponytail ladder in
`governance/handbook.json` (foreign-subject install); prior-art under
`docs/adr/prior-art/ADR-070/`. Seeded-subject proof on fastapi template @
cd83fc1 — resolution determinism VERIFIED ×3; live-model over-build arms
GAP.

**Experiments:** DIRECT 012 READY (#135, 24 VERIFIED / 2 GAP); Python ADP
fracture remediation NOT-READY (#136, F-AD3/F-AD7 HOLDs). Queue: #108,
#109, #115, #119, #105, #90; #88 parked (SLICE-085).

Suite: standing DIRECT 003 host-drift family on main unchanged by this
ship (documented at eeee52d30 / post-#133).
