# SLICE-101 — Minimization ladder as handbook system layer

**Status:** done
**Issue:** #112
**ADR:** docs/adr/ADR-070-minimization-ladder-handbook.md

## Contract

`governance/handbook.json` carries the adapted ponytail minimization ladder
as a single `**/*` chapter (always on; no lite/full/off). Rung 5 is
already-approved deps; testing is red-first + suite manifest; no ask-user
stall. Vendored upstream at `docs/adr/prior-art/ADR-070/` (MIT). System-layer
install for foreign subjects uses the same bytes at
`$XDG_CONFIG_HOME/ranex/handbook.json`. Guidance only — ADR-062 sole-importer
unchanged. `verdict.py` untouched.

## Boundaries

Not #102. Not growing the runtime dependency graph. Not copying upstream's
testing clause or ask-user rule.

## Validation

Seeded-subject proof on `fastapi/full-stack-fastapi-template@cd83fc1` with
anti-flake ×3: `tools/dogfood/minimization_ladder_proof.py` →
`tools/dogfood/audits/2026-09-27-minimization-ladder/`.
