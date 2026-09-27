# State

**Updated:** 2026-09-27
**Active slice:** [SLICE-096 — the architecture-freeze claim](docs/slices/SLICE-096-architecture-freeze-claim.md) — ADP's first family.

ADR-065 (ADP authority split + freeze-origin rule) remains **proposed**:
the operator's approval of it IS the freeze — until then no graph is
frozen and `governance/gates.yaml` carries no arch claim. Machinery,
contract/unit tests and real-kernel proofs
(`tools/dogfood/audits/2026-09-26-arch-freeze/`) are landed beside it.

**Experiment — `ranex-stress-arch-freeze`:** DIRECT 012 deep stress is
**READY**. Receipt `tools/dogfood/audits/2026-09-27-arch-stress/` —
24 VERIFIED, 2 GAP (A3 promote-ship shape; A6 dynamic-import static
limit), 0 FALSE-PASS / 0 NON-DETERMINISTIC. Fractures closed this ship:
symlink-dir refuse, dotted `import` attribution, scale plant isolation,
harness `kernel-verdict-signer` id. Runner:
`tools/dogfood/arch_stress.py` (recovered from prior FM treehouse
session). Captain word still required to **accept ADR-065**; post-approval
wiring (freeze bytes + `gates.yaml` pin) is a separate promote ship.
Python ADP stress remains NOT-READY (six named fractures); no new
languages until Python READY.

(#107 / RISK-07 authenticated-approver lane: do not overwrite that
branch's RISK-07 STATE lines on merge — append this experiment block.)

Suite: standing red on main, pre-existing at eeee52d30 and unchanged by
this branch: the DIRECT 003 host-drift family (6 failures + 13 errors,
verified failing on clean HEAD); docs-collision pair repaired by #134.
