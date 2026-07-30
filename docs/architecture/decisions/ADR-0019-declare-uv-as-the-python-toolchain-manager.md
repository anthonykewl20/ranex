# ADR-0019: Declare uv as the Python Toolchain and Dependency Manager

| Field | Value |
|---|---|
| ADR ID | `ADR-0019` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-31 |
| Effective revision | Working tree based on `79d568914`; definition-only, no runtime or readiness claim |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `configuration_management`, `assurance`, `process_assurance`, `release_management` |
| RFC | Not required; direct owner requirement, as for `ADR-0001` and `ADR-0002` |
| Supersedes | Nothing. Declares a load-bearing tool that was in use without a decision record |
| Review/expiry date | On any change to the pinned version, the licence, or the invocation contract |
| Compatibility/migration class | Declaratory; records an existing dependency, introduces no new one |
| Security/data class | Public architecture decision |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.0.0` | 2026-07-31 | Initial accepted decision. Closes the same defect class `ADR-0014` closed for the implementation language: a load-bearing tool in use with no decision selecting it. |

## Context

`uv` is load-bearing and undeclared. **FACT**, verified 2026-07-31:

- Every executable verification path invokes it. `scripts/architecture/README.md:6`
  documents `uv run --project scripts/architecture` as the way to run the
  generator, validator and concurrency regression, and the architecture-contract
  CI gate calls it at five sites
  (`.github/workflows/architecture-contracts.yml:43, 55, 59, 81, 99`), including
  `astral-sh/setup-uv@v5` and `uv python install 3.12`.
- `scripts/architecture/uv.lock` is tracked and licence-classified at
  `legal/licensing-manifest.json` as `RANEX_ORIGINAL` /
  `GENERATED_DEPENDENCY_LOCK`. That entry classifies the **lock file**, not the
  **tool** that produces and consumes it.
- No accepted decision selects `uv`. `ADR-0014:116` mentions `uv.lock` only as
  "the only related record," explicitly as a classified artefact rather than a
  tool selection.

This is the same defect class `ADR-0014` closed for the implementation language:
a choice on which every verification path depends, made by convention rather than
by decision. `ADR-0013:1175-1176` states that an unresolved choice cannot be
activated "by configuration, convention, model output, or a generator default."
An undeclared toolchain manager is exactly activation by convention.

## Decision

### `TOOLCHAIN-MANAGER-001` — `uv` is the declared Python toolchain and dependency manager

`uv` is the selected tool for resolving dependencies, producing and consuming
`uv.lock`, provisioning the interpreter, and invoking every governed script. Its
selection is recorded here rather than inferred from usage.

### `TOOLCHAIN-PIN-001` — the tool and the interpreter floor are pinned

The interpreter floor remains `ADR-0014` `LANG-PRIMARY-001` (Python ≥ 3.12), and
CI provisions it explicitly via `uv python install 3.12`. `uv` itself is pinned
in CI by the action reference. A drift between the declared floor and the runner
is a finding, not a convenience.

**Recorded version evidence.** The locally exercised version is `0.11.26`; the
latest published version is `0.12.0`. A version pin is therefore a live
obligation, not a formality: the tool that produced the committed lock file and
the tool a fresh environment installs are not the same by default.

### `TOOLCHAIN-LICENCE-001` — licence recorded as declared upstream

`uv` is published by `astral-sh/uv` under the SPDX expression
**`MIT OR Apache-2.0`**, taken from the package's own `license_expression`
metadata. The repository carries both `LICENSE-APACHE` and `LICENSE-MIT`.

This value was corrected during verification: the GitHub repository API reports a
single licence, `Apache-2.0`, which is incomplete. Where a repository API and
package metadata disagree, the package metadata and the licence files shipped
with the distribution govern, because they describe the artefact actually
consumed. Recording the API's answer would have understated the grant.

### `TOOLCHAIN-SUBSTITUTABLE-001` — the dependency is kept replaceable

`uv` is consumed only through a narrow interface: resolve, lock, provision an
interpreter, and run a script. Nothing in the contract system depends on `uv`
internals. A permissive dual licence and a public source repository preserve the
owner's stated requirement that Ranex can continue a tool that is abandoned.

## Predeclared acceptance tests

1. An accepted decision names `uv` as the toolchain manager; validation resolves
   this ADR in the accepted-ADR registry.
2. The licensing manifest carries an entry for `uv` recording
   `MIT OR Apache-2.0`, distinct from the existing `uv.lock` file entry.
3. CI provisions the interpreter explicitly and reports both `uv --version` and
   the interpreter version, so a floor drift is visible rather than silent.
4. Replacing `uv` requires a superseding decision; no script acquires a second
   dependency-resolution path by convention.
5. A resolved dependency set that cannot be reproduced from the committed lock
   file is a finding.

## Consequences and evidence standing

- This decision records an existing dependency. It introduces no new dependency
  and changes no existing check's strictness.
- **Dependency licences remain unregistered.** `legal/licensing-manifest.json`
  has no entry for `jsonschema`, `PyYAML`, or the `rfc8785` package. The single
  textual occurrence of `rfc8785` in that file is the path
  `schemas/fixtures/canonical/rfc8785-golden.json`, a fixture, not a package
  entry. That gap is recorded in `ADR-0014` v1.1.0 and is **not** closed here.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`. This
  decision authorizes no product code and declares no readiness tier.

## Human approval

The human owner directed that `uv` be recorded as a declared tool choice, on the
ground that it is load-bearing and that the same defect class was already closed
for the implementation language by `ADR-0014`.
