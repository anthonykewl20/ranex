# Branding Strategy

Ranex begins from a functional Hermes Agent baseline and replaces product
identity in measured, reversible slices. The initial adoption commit layers
Ranex legal, architecture, research, environment-example, and fork-governance
records onto upstream history. Its only public product-surface change is the
README license-scope notice; it changes no runtime code and does not claim the
rebrand is complete.

## Principles

- Preserve upstream behavior while each public surface is inventoried.
- Separate user-facing identity from compatibility identifiers needed during
  migration.
- Do not reuse Nous Research trademarks or imply upstream endorsement.
- Keep the upstream MIT notice attached to upstream material.
- Apply the Ranex license only to original Ranex Material and modifications.
- Replace installers, services, environment names, paths, package metadata,
  telemetry tags, and remote URLs through reviewed migration contracts.
- Keep legacy `HERMES_HOME` compatibility until the Ranex home resolver and
  migration path are verified.

## Sequence

1. Capture an unmodified upstream runtime baseline.
2. Build a machine-readable brand and integration inventory.
3. Rebrand public documentation and UI surfaces without changing protocols.
4. Introduce Ranex-native package, command, path, service, and configuration
   identities with compatibility aliases.
5. Remove obsolete upstream commercial integrations only after replacement
   behavior and migrations pass.

The detailed sequence and acceptance criteria remain in
`RANEX_IMPLEMENTATION_GUIDE.md`.
