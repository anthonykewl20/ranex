# State

**Updated:** 2026-10-02
**Active slice:** [SLICE-103-audit-findings-and-remediation](docs/slices/SLICE-103-audit-findings-and-remediation.md).

- Settings migration 3 part A: new `witness` section (url,
  log_public_key_path, request_timeout_seconds) is the single source of the
  witness defaults in `governed_execution/witness.py` (#268).

Audit remediation: SLICE-104 merged via PR #227; open follow-ups are tracked
in GitHub milestone #9 (umbrella #186). Static-worker closure tests skip on
foreign hosts (#194 part 1).

ADR-071 PR-0b settings binding enforcement on captain/binding-enforcement.
- Catalog gates opt into settings-bound evidence with a boolean flag.
- CLI admission compares signed envelope-v2 bindings with evaluated-commit settings.
- Binding evaluators refuse bypasses; missing claims remain journaled FAILs.
- Non-binding gates retain existing behavior; the verdict kernel is unchanged.
- Live acceptance remains explicitly non-binding pending #236.
- Next: PR-0c consumer migration for centralized settings.

Documentation is synchronised with the code (PRs #228-#232, #234): README,
OPERATIONS, STATE, MAP, dogfood docs, ADR/slice status lines.
Removed stray tool output (.playwright-mcp, .video_agent); ignored going forward.

Central settings (ADR-071, accepted; issue #226):
- C4 literal ratchet guards src configuration literals; migrations must lower its baseline.
- Platform table centralizes Linux x86-64 ABI facts and refuses unsupported platforms (C5).
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
OCR #221: v3 anchored-history receipts verify arms 0/1/2/3/5 and controls; arm 4 out of scope.
C1 pairing check hardened (#223): `_checked_record_pairs` refuses malformed pairing inputs without raising; two refusal cases pinned.
