# State

**Active slice:** [SLICE-103-audit-findings-and-remediation](docs/slices/SLICE-103-audit-findings-and-remediation.md).

ADR-071 PR-0b settings binding enforcement on captain/binding-enforcement.

- Catalog gates opt into settings-bound evidence with a boolean flag.
- CLI admission compares signed envelope-v2 bindings with evaluated-commit settings.
- Binding evaluators refuse bypasses; missing claims remain journaled FAILs.
- Non-binding gates retain existing behavior; the verdict kernel is unchanged.
- Live acceptance remains explicitly non-binding pending #236.
- Next: PR-0c consumer migration for centralized settings.
