# State

**Updated:** 2026-09-30
**Active slice:** none — ADR-065 accepted; SLICE-096–101 closed;
#88 / SLICE-085 archived with retained live App evidence.

**#105 / OCR-as-subject closed (honest refusal):** pinned
`alibaba/open-code-review` `v1.12.9` linux-amd64
(`sha256:9105c708…`) is static `ET_EXEC` (no `PT_INTERP`). Runtime v3
entrypoint admission refuses honest null-interp binding (Arm 0
VERIFIED ×3). static-v2 admits the same bytes (contrast only). Arms
1–4 UNVERIFIED per issue protocol. Receipts:
`tools/dogfood/audits/2026-09-30-ocr-subject/`. Findings stay
ADVISORY / never `required_claims`. `KERNEL_DIGEST` unmoved.

**#88 closed (2026-09-30):** App product on main (slices 082–086).
Live: `ranex-gate` (4863198) auth + install + `ranex/acceptance` pin
on `ranex-app-live-probe`. Production soak/rotation/backup/restore
and full harness acceptance remain UNVERIFIED; merge-candidate/shard
aggregation remain UNIMPLEMENTED.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__`.
- `landing` gate carries claim `architecture`.

Recent closed: #107–#109, #112, #102, #88, #105. Queue: #115, #119, #90.

Suite: standing host-drift / fixture red family on main unchanged by
this ship; refreeze is IDs-only and outcome-blind.
