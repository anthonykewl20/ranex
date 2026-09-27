# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed.

ADR-065 **accepted**. Production freeze wired:
`governance/architecture-freeze.json` (`ranex-architecture-freeze-v1`,
approved_by ADR-065), digest pin
`sha256:d463e3c97475c1971758415b07d072469385e33700081656d9d632acc3a58f72`,
scan manifesto `governance/arch/scan-manifest.json`, and blocking landing
claim `architecture` via `ranex-arch check …`.

**Experiments:**
- `ranex-stress-arch-freeze`: DIRECT 012 deep stress **READY**. Receipt
  `tools/dogfood/audits/2026-09-27-arch-stress/` — 24 VERIFIED, 2 GAP
  (A3 promote-ship shape; A6 dynamic-import static limit).
- `ranex-adp-python-fracture-remediation`: **NOT-READY**. F-AD3 / F-AD7
  HOLDs. No new languages until Python READY. BASE
  `ranex promotion evaluate` unchanged (arch wiring ≠ BASE promotion).

(#107 / RISK-07 authenticated-approver lane: do not overwrite that
branch's RISK-07 STATE lines on merge — append this experiment block.)

Suite: standing DIRECT 003 host-drift family (6 failures + 13 errors) on
main, unchanged by this ship.
