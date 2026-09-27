# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__` (digest
  `sha256:e7325bdc592efb301cfca4d267984d2b9eea6f3b87887ba33a1f8693525515f8`).
- `landing` gate carries claim `architecture` (scan manifesto
  `governance/arch/scan-manifest.json`). Self-host argv is
  `python3 -m ranex.foundation.arch_scan` — console-script `ranex-arch`
  cannot live inside the governed tree (route-inside refusal).

**Experiments:**
- `ranex-stress-arch-freeze`: DIRECT 012 **READY** (#135).
- `ranex-adp-python-fracture-remediation`: **NOT-READY** (#136); F-AD3 /
  F-AD7 HOLDs. No new languages until Python READY. BASE
  `ranex promotion evaluate` unchanged (arch wiring ≠ BASE promotion).

(#107 / RISK-07 lane: preserve that branch's RISK-07 STATE on merge.)

Suite: standing DIRECT 003 host-drift red family on main unchanged.
