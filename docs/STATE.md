# State

**Updated:** 2026-09-30
**Active slice:** none — #90 dogfood→ranex.dev path verified; no open
slice.

**#90 closed (2026-09-30):** Live `https://ranex.dev/dogfood` still
publishes provenance (verify-dogfood.ts + Playwright desktop/mobile).
Repo contract `tools/dogfood/site/INTEGRATION.md` updated: sync is
workflow_dispatch / path-push (hourly cron paused for Actions billing).
Site redesign + sync landed earlier (ranex `460f002…`, ranex-web
`877ff1c…` ancestor).

**#88 closed (2026-09-30):** App product on main (slices 082–086). Live
re-check retained; production soak/rotation remain UNVERIFIED.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__`.
- `landing` gate carries claim `architecture`.

Recent closed: #107/#108/#109, #112, #102, #88, #90. Queue: #115, #119,
#105.

Suite (isolated `/tmp/ranex-90`): `uv run --frozen pytest -q` → 2285
passed / 88 skipped / 12 failed / 26 errors / exit 1 — standing DIRECT
003 / E-C17 (`/etc/ld.so.cache`) + host-bound ELF digest fixtures; same
shape as sibling main worktrees; not fixed here.
