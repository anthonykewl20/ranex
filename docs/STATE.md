# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097 / #107 (authenticated approver) closed; SLICE-098 / #108
(external Rekor witness) closed on this branch.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__` (digest
  `sha256:e7325bdc592efb301cfca4d267984d2b9eea6f3b87887ba33a1f8693525515f8`).
- `landing` gate carries claim `architecture`; self-host argv is
  `python3 -m ranex.foundation.arch_scan`.

**#107 / RISK-07 closed:** catalogued `role: approver`, CLI possession
before `evaluate()`, second Ed25519 signature in the verdict; reader
`UNAPPROVED` without it. `verdict.py` / `KERNEL_DIGEST` unmoved.

**#108 / RISK-19+03 closed-with-witness:** DSSE-wrapped verdicts anchored
in Rekor (`gate evaluate --witness`; `journal verify --witnessed`);
pinned log key `governance/rekor_public_key.pem` (ADR-067 / SLICE-098).
#109 takes ADR-068 / SLICE-099 next.

Suite: standing host-drift red family on main unchanged by this ship
(documented at eeee52d30 / post-#133); refreeze is IDs-only and outcome-blind.
