# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-29 (code-to-doc audit, issue #54)
**Active slice:** none

## Where we stopped

The repository is a pre-release, source-run Python kernel. Its public main CLI
is `gate evaluate`, `journal verify`, `run`, `suite freeze`, `deps
fetch|approve`, `keygen`, `task dispatch|judge|merge|delegate|fanout`, and
`task batch qualify`.

The code implements deterministic gate evaluation, signed subject/command-bound
evidence, committed-tree execution, a hash-chained SQLite append API, suite-ID
freezing, dependency provisioning, serial task publication, prototype external
delegation/fanout, internal A/B/C specification APIs, non-publishable approved
batch qualification, optional signed verdict publication, and host-qualified
strict-local confinement.

There is no installed agent harness, main-CLI specification lifecycle, owner
intake, task board, deployment command, built-in model provider, authenticated
ordinary gate approver, or end-to-end A/B/C-authorized mutation composition.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: none scheduled; the owner must choose any new product-code scope.

## Governance
Kernel-only initial release; no implementation slice is active.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
(superseded by the 2026-08-25 kernel-only scope reset).
Documentation capability claims must cite current source and executable tests;
archived slices and prior prose are history, not the source of truth.

## Known limits

- `task delegate` records a nonzero suite exit but returns orchestration success
  after a completed delegation; only a gate evaluation issues a verdict.
- Free-prompt fanout has no A/B/C child admission; batch qualification cannot
  publish.
- `evidence.json` replaces same-claim/same-producer rows; it is not append-only.
- The suite manifest freezes IDs and skip reasons, not test bodies.
- Journal verification cannot detect an internally consistent older snapshot.
- Strict-local requires a qualified Linux host and trusts a same-UID controller.
