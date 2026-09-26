# State

**Updated:** 2026-09-26
**Active slice:** [SLICE-094 — the architecture-freeze claim](docs/slices/SLICE-094-architecture-freeze-claim.md) — ADP's first family.

ADR-064 (ADP authority split + freeze-origin rule) shipped **proposed**:
the operator's approval of it IS the freeze — until then no graph is
frozen and `governance/gates.yaml` carries no arch claim. Wiring ranex's
own ten-subpackage graph is the post-approval promote ship. Machinery,
contract/unit tests and real-kernel receipts
(`tools/dogfood/audits/2026-09-26-arch-freeze/`) are landed: pristine
PASS ×3 byte-identical, planted edge FAIL ×3 (fingerprint byte-identical
to the arch-maintain lab), accepted both directions, freeze-tamper,
absence.

#130 BASE freeze + promotion gate merged; SLICE-093-base-freeze archived.
DIRECT 014: this ship lands implementation-only — production waits for
`ranex-stress-arch-freeze` READY (DIRECT 012 stress before blocking-on);
the ADR names the D013 set (TS/JS, Python, PHP, Java, Go, Rust + common
web backends). Next after approval: the freeze wiring promote ship; the
stress ship; DIRECT 013 language feeds.

Suite: standing red on main, pre-existing at eeee52d30 and unchanged by
this branch: `test_no_two_adrs_share_a_number` / `test_no_two_slices_share_a_number`
(two ADR-063s, three SLICE-093s from the 09-25 parallel landings — a
captain-owned renumber, not a hand-merge); plus the standing host-drift
red only (DIRECT 003).
