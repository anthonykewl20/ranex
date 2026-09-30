# State

**Updated:** 2026-09-30
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097–101 closed on prior ships.

**#105 / OCR-as-subject closed (honest refusal):** pinned
`alibaba/open-code-review` `v1.12.9` linux-amd64
(`sha256:9105c708…`) is static `ET_EXEC` (no `PT_INTERP`). Runtime v3
entrypoint admission refuses honest null-interp binding (Arm 0
VERIFIED ×3). static-v2 admits the same bytes (contrast only). Arms
1–4 UNVERIFIED per issue protocol. Receipts:
`tools/dogfood/audits/2026-09-30-ocr-subject/`. Findings stay
ADVISORY / never `required_claims`. `KERNEL_DIGEST` unmoved.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__`.
- `landing` gate carries claim `architecture`.

Recent: #112 minimization ladder; #102 delegated review; #107–#109
approver / Rekor / observations. Queue remains #115, #119, #90; #88
parked.

Suite: standing host-drift / fixture red family on main unchanged by
this ship; refreeze is IDs-only and outcome-blind.
