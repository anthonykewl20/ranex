# ADR-052 — Explicit external repository authority

**Status:** accepted
**Date:** 2026-09-06
**Issue:** #86

## Context and Problem Statement

Leitir has its own `src/`. The Six demonstration's kernel-vendoring recipe
refuses that layout, while `governed_repository_root()` intentionally selects
the checkout containing the CLI, independently of cwd. Changing cwd must not
silently change the repository whose policy, keys and evidence are trusted.

## Decision

Add `--external-repository PATH` to `run`, `suite freeze`, `gate evaluate`,
`journal verify`, `deps fetch`, `deps approve` and `keygen`. It is an explicit
operator authority selection, never an environment variable or cwd default.
The selected directory must resolve to the root of an existing Git checkout;
nested directories and conflicting `--repository` selections are refused.

The existing repository selection remains the default. The external root
becomes the root for committed policy, public keys, subject materialization,
private-key exclusion, evidence, journal, verdict publication and trace-target
admission. Existing implementations perform these checks; the selector does
not introduce another signing, digest or confinement implementation. Kernel
runtime profiles still come from the installed kernel checkout.

Arxic's actual Vitest 4.1.11 run exposed a second adoption boundary: the loader
required pytest's output flag even for valid JUnit from another runner. Add
explicit `results_reporter: vitest-junit`, with exactly one `--reporter=junit`
and one matching `--outputFile=PATH`, refusing overrides and `--` separators.
`suite freeze --results-reporter vitest-junit` preserves the report's real
`classname::name` identifiers. Existing pytest normalization is unchanged and
never selected by guessing from a filename extension. The catalog digest binds
the reporter choice; manifest and result schemas and signing remain unchanged.

## Alternatives

- Copy the kernel into every application's `src/`: rejected because it
  changes the governed application's source layout and creates collisions.
- Infer the target from cwd or an ambient environment variable: rejected
  because it silently changes trust-root selection for existing commands.
- Reinterpret existing `--repository`: rejected to preserve the existing
  second-repository refusal contract unless the operator explicitly opts in.

## Consequences and Limits

Observation and evaluation can use a separately installed kernel without
vendoring. The operator remains responsible for reviewing the target's policy,
keys and frozen test manifest; selecting a repository does not authorize its
PR author to change acceptance policy. This flag does not add a trusted PR
scheduler, automatic check refresh, remote signing, or merge-queue support.
The default hermetic observation profile retains its existing trust limits;
it is not upgraded to strict-local confinement by selecting an external repo.
Strict-local execution still requires the qualified host and kernel checkout.

## Confirmation

`tests/integration/test_external_repository.py` invokes actual CLI subprocesses
against a separate application with `src/`, freezes real pytest output, runs
the tests, verifies signed publication through the GitHub verdict reader,
rejects signature tampering and stale source, observes a failed assertion,
then verifies recovery and the journal. Its second arm exercises path escapes,
conflicting roots, key confinement and the unchanged implicit refusal.
The contract and suite-result tests reject conflicting Vitest output options,
unknown reporters and missing test IDs. Retained pilot receipts distinguish
bounded real repository checks from full application or live App acceptance.
