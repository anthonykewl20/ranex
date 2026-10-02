# State

**Updated:** 2026-10-02
**Active slice:** docs/slices/SLICE-103-audit-findings-and-remediation.md

Audit remediation: SLICE-104 merged via PR #227; open follow-ups are tracked
in GitHub milestone #9 (umbrella #186).

Documentation is synchronised with the code (PRs #228-#232, #234): README,
OPERATIONS, STATE, MAP, dogfood docs, ADR/slice status lines.
Removed stray tool output (.playwright-mcp, .video_agent); ignored going forward.

Central settings (ADR-071, accepted; issue #226):
- PR-0a merged (#235): `ranex.foundation.settings` (catalogs section, scoped
  precedence, policy refusal, settings_digest, secret references) and
  `ranex settings show|get`. No consumer migrated yet.
- Envelope v2 (#237): signing dispatches on the signed `envelope_type`; v2
  adds `settings_digest` and `settings_schema_version`; v1 bytes unchanged
  (pinned vector). Nothing produces v2 yet.

Next: binding enforcement (catalog `requires_settings_binding`, admission
filter, CLI and evaluator wiring, producer emits v2 for binding gates), then
PR-0c (platform table and no-literal contract test), then section migrations.
Live-acceptance binding is tracked separately in #236.

Dogfood finding ids F-035..F-037 de-duplicated (#233).
