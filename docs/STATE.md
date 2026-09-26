# State

**Updated:** 2026-09-26
**Active slice:** [SLICE-096 — the architecture-freeze claim](docs/slices/SLICE-096-architecture-freeze-claim.md) — ADP's first family.

ADR-065 (ADP authority split + freeze-origin rule) shipped **proposed**:
the operator's approval of it IS the freeze — until then no graph is
frozen and `governance/gates.yaml` carries no arch claim. Wiring ranex's
own ten-subpackage graph is the post-approval promote ship. Machinery,
contract/unit tests and real-kernel receipts
(`tools/dogfood/audits/2026-09-26-arch-freeze/`) are landed: pristine
PASS ×3 byte-identical, planted edge FAIL ×3 (fingerprint byte-identical
to the arch-maintain lab), accepted both directions, freeze-tamper,
absence.

The #134 renumber restored one-number-one-document (antislop slice/ADR
094/063; base-freeze 095/064); this ship renumbers its own slice/ADR to
096/065 on top of it. DIRECT 014: implementation-only — production waits
for `ranex-stress-arch-freeze` READY (the stress verdict is 2026-09-26
NOT-READY); the ADR names the D013 set (TS/JS, Python, PHP, Java, Go,
Rust + common web backends). Next after approval: the freeze wiring
promote ship; the stress fractures' repair; DIRECT 013 language feeds.

Suite: standing red on main, pre-existing at eeee52d30 and unchanged by
this branch: the DIRECT 003 host-drift family (6 failures + 13 errors,
verified failing on clean HEAD); the docs-collision pair was repaired by
#134.
