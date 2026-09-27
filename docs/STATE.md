# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097 / #107 (authenticated approver) closed.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__` (digest
  `sha256:e7325bdc592efb301cfca4d267984d2b9eea6f3b87887ba33a1f8693525515f8`).
- `landing` gate carries claim `architecture`; self-host argv is
  `python3 -m ranex.foundation.arch_scan`.

**#107 / RISK-07 closed:** catalogued `role: approver`, CLI possession
before `evaluate()`, second Ed25519 signature in the verdict; reader
`UNAPPROVED` without it. `verdict.py` / `KERNEL_DIGEST` unmoved. Receipt:
`tools/dogfood/audits/2026-09-26-approver-authentication/` (11/11 VERIFIED).

**Experiments:** DIRECT 012 READY (#135); Python ADP fracture remediation
NOT-READY (#136). Queue: #108, #109, #102, #112, #115, #119, #105, #90;
#88 parked (SLICE-085).

Suite: standing host-drift red family on main unchanged by this ship
(documented at eeee52d30 / post-#133); refreeze is IDs-only and outcome-blind.
