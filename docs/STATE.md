# State

**Updated:** 2026-09-27
**Active slice:** [SLICE-096 — the architecture-freeze claim](docs/slices/SLICE-096-architecture-freeze-claim.md) — ADP's first family.

**ADR-065 accepted** (this commit): operator approval is the freeze-origin.
Promote wiring (freeze bytes + `gates.yaml` pin + scan manifesto) follows
immediately as the next commit on this branch.

**Experiments:**
- `ranex-stress-arch-freeze`: DIRECT 012 **READY** (PR #135). Receipt
  `tools/dogfood/audits/2026-09-27-arch-stress/` — 24 VERIFIED, 2 GAP,
  0 FALSE-PASS / 0 NON-DETERMINISTIC.
- `ranex-adp-python-fracture-remediation`: **NOT-READY** (PR #136). F-AD3
  and F-AD7 remain irreducible HOLDs. No new languages until Python READY.

(#107 / RISK-07 authenticated-approver lane: preserve that branch's
RISK-07 STATE lines on merge — append, do not claim #107 closed.)

Suite: standing DIRECT 003 host-drift red family on main unchanged
(documented at eeee52d30 / post-#133).
