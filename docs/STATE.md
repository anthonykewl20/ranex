# State

**Updated:** 2026-09-27
**Active slice:** [SLICE-096 — the architecture-freeze claim](docs/slices/SLICE-096-architecture-freeze-claim.md) — ADP's first family.

ADR-065 (ADP authority split + freeze-origin rule) remains **proposed**:
the operator's approval of it IS the freeze — until then no graph is
frozen and `governance/gates.yaml` carries no arch claim. Machinery,
contract/unit tests and real-kernel proofs
(`tools/dogfood/audits/2026-09-26-arch-freeze/`) are landed beside it.

**Experiments:**
- `ranex-stress-arch-freeze`: DIRECT 012 deep stress **READY**. Receipt
  `tools/dogfood/audits/2026-09-27-arch-stress/` — 24 VERIFIED, 2 GAP
  (A3 promote-ship shape; A6 dynamic-import static limit), 0 FALSE-PASS /
  0 NON-DETERMINISTIC. Fractures closed: symlink-dir refuse, dotted
  `import` attribution, scale plant isolation, harness
  `kernel-verdict-signer` id. Runner: `tools/dogfood/arch_stress.py`.
  Captain word still required to **accept ADR-065**; post-approval
  wiring (freeze bytes + `gates.yaml` pin) is a separate promote ship.
- `ranex-adp-python-fracture-remediation`: **NOT-READY**. Re-stress receipt
  `tools/dogfood/audits/2026-09-27-adp-python-fracture-restress/`: F-AD1,
  F-AD5, F-AD4, F-ND1 READY under named remediations; **F-AD3** and
  **F-AD7** remain irreducible HOLDs (no pyrefly ignore-disregard flag /
  no kernel files-checked witness). No new languages until Python READY.

(#107 / RISK-07 authenticated-approver lane: do not overwrite that
branch's RISK-07 STATE lines on merge — append this experiment block.)

Suite: standing red on main, pre-existing at eeee52d30 and unchanged by
these ships: the DIRECT 003 host-drift family (6 failures + 13 errors,
verified failing on clean HEAD); docs-collision pair repaired by #134.
