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

Suite: standing DIRECT 003 / E-C17 host-drift (`/etc/ld.so.cache`) and
host-bound ELF digest fixtures remain red on this host — quoted, not
fixed.
