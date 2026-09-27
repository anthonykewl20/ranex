# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097 / #107 (authenticated approver) closed.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__`.
- `landing` gate carries claim `architecture` (scan manifesto
  `governance/arch/scan-manifest.json`).

**#107 / RISK-07 closed:** catalogued `role: approver`, CLI possession
before `evaluate()`, second Ed25519 signature in the verdict; reader
`UNAPPROVED` without it. `verdict.py` / `KERNEL_DIGEST` unmoved. Receipt:
`tools/dogfood/audits/2026-09-26-approver-authentication/` (11/11 VERIFIED).
MAP RISK-07 struck; producer↔approver row CONFIRMED as a control.

**Experiments:** `ranex-stress-arch-freeze` DIRECT 012 READY (#135);
`ranex-adp-python-fracture-remediation` NOT-READY (#136). Queue: #108,
#109, #102, #112, #115, #119, #105, #90; #88 parked (SLICE-085).

Suite: standing host-drift red family on main unchanged by this ship
(documented at eeee52d30 / post-#133); refreeze is IDs-only and outcome-blind.
