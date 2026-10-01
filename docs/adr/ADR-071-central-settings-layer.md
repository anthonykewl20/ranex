# ADR-071 — central settings layer

**Status:** proposed
**Date:** 2026-10-01
**Decision-makers:** repo owner
**Issue:** #224

## Context and Problem Statement

The owner law (issue #224): "never ever hardcode anything, make sure that this
project is agnostic driven with real centralized settings/config", while "code
is the only source of truth". Nothing of that exists today. Order 012 swept
every tracked `*.py` under `src/` and `tools/`, the native worker launcher,
and the GitHub workflows and inventoried 252 config-bearing rows: 120
CONFIG-CANDIDATE, 39 AGNOSTIC-VIOLATION, 35 TRUST-PIN, 18 STANDARD-CONSTANT,
14 ALREADY-CONFIGURED, 26 OTHER (hardcoding inventory, order 012).

There is no settings module in `src/`. Configuration today is the
`governance/*.yaml|json` catalogs plus roughly 20 scattered `RANEX_*`
environment reads. The inventory's top risks: product SARIF output hardcodes
`github.com/anthonykewl20/ranex`; one Ubuntu toolchain (gcc-13, 13.3.0/6.8,
`x86_64-linux-gnu`) is frozen truth for host qualification; x86-64 syscall
numbers sit in `src/ranex/cli/host_confinement.py`; `http_observer.py` embeds
a Postgres URI with a credential; launcher protocol limits are duplicated
between C and Python. The inventory proposes 13 settings sections: catalogs,
paths, github, witness, execution, supervisor/confinement/launcher,
journal/history/logs/redaction/observability,
subject/delegation/repair/qualification, acceptance/observer, toolchain, ci,
dogfood, build.

The kernel — `evaluate()` in
`src/ranex/governed_execution/domain/verdict.py` — is pure and digest-pinned.
It must never read settings (see D3).

## Decision

**D1** One typed settings module `src/ranex/foundation/settings.py` (frozen
dataclasses, one per section from report 012) is the only place code reads
configuration; no other module reads `os.environ` or a settings file directly.

**D2** Two file scopes plus overrides. Precedence, lowest to highest: built-in
defaults in `settings.py` < repository file `governance/settings.toml`
(committed in the governed repository) < host file
`<XDG_CONFIG_HOME>/ranex/settings.toml` (the `XDG_CONFIG_HOME` directory;
default `~/.config/ranex/settings.toml`) < `RANEX_<SECTION>_<KEY>` environment
variables. Unknown keys and wrong types are refused at load with a named
error.

**D3** Verdict safety: only repository-scope settings may influence
acceptance; their canonical digest is bound into the evidence/verdict inputs.
Host-scope settings and env overrides may change execution mechanics (paths,
timeouts, endpoints) but never a verdict; a host setting that tries to set a
policy key is refused. The kernel never reads settings; values reach it only
as explicit inputs.

**D4** Secrets never live in settings files: settings hold the NAME of an env
var or a key-file path, never the secret value. The `http_observer` credential
is replaced by generated per-run credentials or an env reference.

**D5** Not settings: trust pins stay code constants pinned by tests; standard
constants stay; platform facts (syscall numbers, loader paths, triples) come
from a built-in per-architecture table selected from the running machine, with
unsupported architectures refused, not configured.

**D6** Identity: product output (SARIF `informationUri`, release URLs, check
names) derives from repository/github settings, never a literal owner/repo.

**D7** Migration: one PR per settings section from report 012, each with its
own issue in milestone #9; a contract test forbids new literals of the
migrated kinds in `src/` outside `settings.py` and the trust-pin list. Order
of migration: catalogs, github, execution, then the rest.

## Consequences

Good:

- Every configuration value has one typed home. Forks, renames, and host
  changes become settings edits, never code edits (D1, D6).
- Verdicts stay trustworthy: acceptance is influenced only by
  repository-scope settings whose canonical digest is bound into the
  evidence/verdict inputs, and the kernel stays pure (D3).
- Secrets leave product code: the embedded `http_observer` credential dies,
  and settings files stay safe to commit and review (D4).
- Platform facts become one auditable per-architecture table; a wrong
  architecture is a loud refusal, not a security bug (D5).
- The migration is mechanical and test-gated: one section per PR with its own
  issue, and a contract test refuses new literals of migrated kinds (D7).

Bad:

- A settings load failure is a startup failure: unknown keys and wrong types
  refuse to load, so a bad `settings.toml` blocks the run instead of degrading
  gracefully (D2).
- Binding the repository-scope digest into verdict inputs means any change to
  `governance/settings.toml` invalidates continuity with prior evidence —
  deliberate, but it makes settings edits weighty.
- Host operators can no longer tune policy from outside the repository: a
  host-scope attempt on a policy key is refused, which some deployments will
  call inflexible (D3).
- `settings.py` and its loader/validation become new code that must itself
  stay literal-free; only the D7 contract test guards against creep re-entering.
- Frozen dataclasses plus stdlib `tomllib` keep the runtime dependency graph
  unchanged, but the validation layer is hand-rolled where
  `pydantic-settings` would have given it for free (rejected, below).

## Alternatives considered

- **env-only configuration** — rejected. Environment variables are host
  scope: there is no repository scope to digest-bind into the verdict inputs
  (D3 becomes impossible), and the existing ~20 scattered `RANEX_*` reads
  would stay scattered rather than converge on one typed module (D1).
- **single file without scopes** — rejected. One flat namespace cannot
  separate verdict-influencing repository settings from host mechanics, so
  either the host could move a verdict or the file could not configure
  execution at all (D3).
- **pydantic-settings dependency** — rejected: no new runtime deps without
  owner word. Frozen dataclasses with stdlib `tomllib` cover the typed load
  and validation this layer needs.

## Migration plan

One PR per settings section (D7), each with its own issue in milestone #9.
Rows are the inventory's CONFIG-CANDIDATE rows carrying a proposed key in the
section (120 of the 252 rows). The 39 AGNOSTIC-VIOLATION rows are fixed by
the section that owns their family (identity literals via `github.*`, D6) or
by D5 platform facts and trust pins, and keep their own classification.

| section | rows | issue to open | order |
|---|---|---|---|
| catalogs.* | 5 | settings: migrate catalogs.* | 1 |
| github.* (with receiver.*) | 12 | settings: migrate github.* | 2 |
| execution.* | 8 | settings: migrate execution.* | 3 |
| paths.* (with provisioning.*) | 3 | settings: migrate paths.* | after 3 |
| supervisor.* / confinement.* / launcher.* | 17 | settings: migrate supervisor/confinement/launcher.* | after 3 |
| journal.* / history.* / logs.* / redaction.* / observability.* | 13 | settings: migrate journal/history/logs/redaction/observability.* | after 3 |
| subject.* / delegation.* / repair.* / qualification.* | 14 | settings: migrate subject/delegation/repair/qualification.* | after 3 |
| acceptance.* / observer.* | 7 | settings: migrate acceptance/observer.* | after 3 |
| toolchain.* | 1 | settings: migrate toolchain.* | after 3 |
| ci.* | 7 | settings: migrate ci.* | after 3 |
| dogfood.* | 21 | settings: migrate dogfood.* | after 3 |
| build.* | 2 | settings: migrate build.* | after 3 |
| residual keys (evidence, antislop, artifacts, cli, probes, site, oss_bench, trainer) | 8 | assign to the absorbing section at migration | with their section |

Only the first three positions are decided: catalogs, github, execution, then
the rest (D7). Every migration PR keeps current values as defaults, so each is
behaviour-identical before any operator opts into a settings file.
