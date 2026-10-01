# ADR-071 — central settings layer

**Status:** accepted
**Date:** 2026-10-01
**Decision-makers:** repo owner
**Issue:** #224

## Context and Problem Statement

The owner law (issue #224): "never ever hardcode anything, make sure that this
project is agnostic driven with real centralized settings/config", while "code
is the only source of truth". No centralized typed settings layer exists today
(the `governance/*` catalogs do exist and are read as code constants). Order 012
swept every tracked `*.py` under `src/` and `tools/`, the native worker launcher,
and the GitHub workflows and inventoried 252 config-bearing rows: 120
CONFIG-CANDIDATE, 39 AGNOSTIC-VIOLATION, 35 TRUST-PIN, 18 STANDARD-CONSTANT,
14 ALREADY-CONFIGURED, 26 OTHER (hardcoding inventory, order 012).

Configuration today is the `governance/*.yaml|json` catalogs plus roughly 20
scattered `RANEX_*` environment reads. The inventory's top risks: product SARIF
output hardcodes `github.com/anthonykewl20/ranex`; one Ubuntu toolchain (gcc-13,
13.3.0/6.8, `x86_64-linux-gnu`) is frozen truth for host qualification; x86-64
syscall numbers sit in `src/ranex/cli/host_confinement.py`; `http_observer.py`
embeds a Postgres URI with a credential; launcher protocol limits are duplicated
between C and Python. The inventory proposes 13 settings sections: catalogs,
paths, github, witness, execution, supervisor/confinement/launcher,
journal/history/logs/redaction/observability,
subject/delegation/repair/qualification, acceptance/observer, toolchain, ci,
dogfood, build.

The kernel — `evaluate()` in
`src/ranex/governed_execution/domain/verdict.py` — is pure and digest-pinned.
It must never read settings (see D3, C1).

## Decision

**D1** One typed settings module src/ranex/foundation/settings.py (new module, created by PR-0) (frozen
dataclasses, one per section from report 012) is the only place code reads
configuration; no other module reads `os.environ` or a settings file directly.
Every key carries `scope = policy | mechanics` (C1).

**D2** Two file scopes plus overrides. Precedence, lowest to highest: built-in
defaults in `settings.py` < repository file `governance/settings.toml`
(committed in the governed repository) < host file
`<XDG_CONFIG_HOME>/ranex/settings.toml` (the `XDG_CONFIG_HOME` directory;
default `~/.config/ranex/settings.toml`) < `RANEX_<SECTION>_<KEY>` environment
variables < an explicit CLI flag (mechanics keys only; policy keys resolve only
from the repository file at the evaluated ref — C2). Unknown keys and wrong
types are refused at load with a named error.

**D3** Verdict safety: only repository-scope (policy) settings may influence
acceptance; their canonical digest is recorded in every evidence record and
checked at admission (C1). Mechanics keys — and only keys that cannot change
evidence or a verdict — may come from the host file, env or CLI; a host-file,
env or CLI value for a policy key is refused with a named error (C2). The
kernel never reads settings; values reach it only as explicit inputs, and
`verdict.py` stays byte-identical (C1).

**D4** Secrets never live in settings files: settings hold the NAME of an env
var or a key-file path, never the secret value. The `http_observer` credential
is replaced by generated per-run credentials or an env reference; per-run secret
transport, redaction and cleanup are specified in C3.

**D5** Not settings: trust pins stay code constants pinned by tests; standard
constants stay; platform facts (syscall numbers, loader paths, triples) come
from a built-in per-architecture table selected from the running machine
(src/ranex/foundation/platform.py (new module), C5), with unsupported architectures
refused, not configured.

**D6** Identity: product output (SARIF `informationUri`, release URLs, check
names) derives from repository/github settings, never a literal owner/repo.

**D7** Migration: one PR per settings section from report 012 plus the PR-0
settings foundation, each with its own issue in milestone #9, in C4's order
(catalogs, github, witness, execution, then the rest); a contract test forbids
new literals of the migrated kinds in `src/` outside `settings.py`, trust pins
and the platform table.

### Decisions C1–C6 (captain decisions resolving review 014 F1–F5; C1–C6 win over D1–D7 on conflict, and E1–E3 win over C1–C6 and D1–D7)

**C1 (F1) Scope per key.** Every key in `settings.py` carries
`scope = policy | mechanics`. Classification rule: any key read on an
evidence-producing, admitting or evaluating path is policy (this includes
timeouts, limits, endpoints and catalog paths used there); everything else is
mechanics. Policy values are loaded ONLY from `governance/settings.toml` as
committed at the evaluated ref (read the blob from git at that ref, never
working-tree bytes). Their canonical digest (`settings_digest`, over the
resolved policy subset including defaults, with a `settings_schema_version`) is
recorded in every evidence record produced under them and checked at admission:
evidence whose `settings_digest` is missing or differs from the digest computed
at the evaluated ref is refused (absence blocks). The check lives in admission
(`src/ranex/governed_execution/domain/admission.py`), NOT in `verdict.py`; the
kernel stays byte-identical. Refs with no settings file use the versioned
built-in defaults digest. Evidence produced before this ADR (no
`settings_digest`) is accepted only for gates whose catalog does not declare
`requires_settings_binding: true`; new gates declare it.

**C2 (F2) Resolution.** Precedence for mechanics keys: defaults < repository
file < host file (XDG config home `ranex/settings.toml`, default
`~/.config/ranex/settings.toml`) < env `RANEX_<SECTION>_<KEY>` < explicit CLI
flag. Policy keys: defaults < repository file at the evaluated ref ONLY; a
host-file, env or CLI value for a policy key is refused with a named error.
Merge is per key (deep), never section replacement. Env names: uppercase, `.`
to `_`; the schema test fails on any name collision. Types: TOML types from
files; env strings parsed by the key's declared type (bool only `true`/`false`;
ints base 10; durations as integer seconds/milliseconds named in the key, e.g.
`timeout_seconds`). Missing files = defaults. Each section may define
`validate()` for relational constraints (e.g. receiver deadlines), run at load.
Legacy `RANEX_*` env names keep working as aliases mapped in `settings.py` for
one release, logged as deprecated.

**C3 (F3) Secrets.** Settings files may hold a key-file PATH or the NAME of an
env var, never a secret value. Per-run secrets (`http_observer` database
credential, JWT secret) are generated in memory per run, passed to the container
only via environment (`docker -e`) or a 0600 file on a per-run tmpfs/temp dir
removed in a `finally` block; they are registered with the redaction layer
before any logging; no generated config file containing a secret is written into
the repository or a persistent path.

**C4 (F4) Migration.** PR-0 "settings foundation" (own issue): `settings.py`
loader, schema with scope metadata, `settings_digest`, admission check behind
`requires_settings_binding`, `ranex settings show|get` CLI, and the contract
test that forbids new literals of migrated kinds in `src/` outside
`settings.py`, trust pins and the platform table (E1 adds the v6 envelope,
version dispatch, live-acceptance binding and gate-catalog flag to PR-0).
Then one PR per section, each
its own issue, in this order: catalogs, github, witness, execution,
supervisor/confinement/launcher, journal/history/logs/redaction/observability,
subject/delegation/repair/qualification, acceptance/observer, toolchain, ci,
dogfood, build. Every inventory row (incl. residual families) is assigned to
exactly one of these; the migration table states rows per section and the
counts reconcile to the inventory's 120 CONFIG-CANDIDATE + 39
AGNOSTIC-VIOLATION. Native launcher: its limits are generated into a C header
from the Python platform/settings table at build time, with a test that the
header matches. Committed CI workflows are generated from central settings by
`ranex settings render-ci` with drift validation; tools and workflow steps read
step-time values via `ranex settings get <key>` (E2). Migration starts after
the remediation integration (order 011) merges, so remediation-only files are
covered.

**C5 (F4/D5) Platform table.** src/ranex/foundation/platform.py (new module) maps (os,
arch) to syscall numbers, loader paths and triples; unsupported platforms are
refused, never configured.

**C6 (F5) Wording.** Say "no centralized typed settings layer exists" (catalogs
do exist); configurable defaults live only in `settings.py`; scattered new
literals of migrated kinds are forbidden.

### Decisions E1–E3 (captain decisions resolving re-review 016 N1–N3; E1–E3 win over C1–C6 and D1–D7 on conflict)

**E1 (N1) Authenticated settings binding.** The settings binding is carried in
a versioned evidence envelope: version 6 = the v5 `SIGNED_FIELDS` of
`src/ranex/foundation/signing.py` plus `settings_digest` and
`settings_schema_version`, both signed. Producers emit v6 once PR-0 lands; the
verifier dispatches by envelope version; v5 evidence is accepted only for gates
whose catalog does not declare `requires_settings_binding: true`. PR-0 owns:
`signing.py` (v6 fields + version dispatch), `admission.py` (digest check vs
the evaluated ref), `src/ranex/cli/acceptance_task.py` and
`src/ranex/bootstrap/composition.py` (the live-acceptance path must apply the
same binding check before calling evaluate; it may not bypass admission), and
gate catalog support for `requires_settings_binding`. `verdict.py` stays
byte-identical.

**E2 (N2) CI consumption.** Committed workflow files are GENERATED from central
settings by a ranex command (`ranex settings render-ci`), and a contract test
fails when the committed workflows differ from the render (drift validation).
Static fields (triggers, schedules, branches, runner, setup-python version)
come from that generation; step-time values use `ranex settings get <key>`. The
ci section PR owns the generator and the drift test; the default-branch
projection is owned by the github section.

**E3 (N3) Digest-invalidation wording.** "Any change to
`governance/settings.toml`" is replaced by "any change to the resolved policy
subset or its settings schema version": mechanics-only edits, comments and
equivalent TOML representations do not change `settings_digest`.

## Consequences

Good:

- Every configuration value has one typed home. Forks, renames, and host
  changes become settings edits, never code edits (D1, D6).
- Verdicts stay trustworthy: acceptance is influenced only by policy settings
  whose canonical digest is recorded in every evidence record and checked at
  admission, and the kernel stays pure (D3, C1).
- Secrets leave product code: the embedded `http_observer` credential dies,
  settings files stay safe to commit and review, and per-run secrets never
  persist beyond the run (D4, C3).
- Platform facts become one auditable per-architecture table; a wrong
  architecture is a loud refusal, not a security bug (D5, C5).
- The migration is mechanical and test-gated: PR-0 then one section per PR with
  its own issue in C4's order, and a contract test refuses new literals of
  migrated kinds (D7, C4).

Bad:

- A settings load failure is a startup failure: unknown keys and wrong types
  refuse to load, so a bad `settings.toml` blocks the run instead of degrading
  gracefully (D2).
- Recording the policy digest in every evidence record means any change to
  the resolved policy subset or its settings schema version changes
  `settings_digest` and breaks continuity with prior evidence — deliberate,
  but it makes settings edits weighty (C1, E3).
- Host operators can no longer tune policy from outside the repository: a
  host-file, env or CLI attempt on a policy key is refused, which some
  deployments will call inflexible (D3, C2).
- `settings.py` and its loader/validation become new code whose configurable
  defaults live only in its central defaults; scattered new literals of
  migrated kinds are forbidden, and only the D7 contract test guards against
  creep re-entering (C6).
- Frozen dataclasses plus stdlib `tomllib` keep the runtime dependency graph
  unchanged, but the validation layer is hand-rolled where
  `pydantic-settings` would have given it for free (rejected, below).

## Alternatives considered

- **env-only configuration** — rejected. Environment variables are host
  scope: there is no repository scope to digest-bind into the evidence records
  (D3, C1 become impossible), and the existing ~20 scattered `RANEX_*` reads
  would stay scattered rather than converge on one typed module (D1).
- **single file without scopes** — rejected. One flat namespace cannot
  separate verdict-influencing policy settings from host mechanics, so
  either the host could move a verdict or the file could not configure
  execution at all (D3, C1).
- **pydantic-settings dependency** — rejected: no new runtime deps without
  owner word. Frozen dataclasses with stdlib `tomllib` cover the typed load
  and validation this layer needs.

## Migration plan

PR-0 first, then one PR per settings section (C4), each with its own issue in
milestone #9. Every inventory row — CONFIG-CANDIDATE, AGNOSTIC-VIOLATION and
residual families alike — is assigned to exactly one migration PR. The `rows`
counts reconcile to the inventory's 120 CONFIG-CANDIDATE + 39
AGNOSTIC-VIOLATION rows = 159 (inventory 012 front matter); the `source` note
states which `report-rows.md` rows each count draws on.

| migration PR | rows | source (inventory 012 `report-rows.md`) | issue to open | order |
|---|---|---|---|---|
| PR-0 settings foundation | 0 | loader/schema/`settings_digest`/admission/CLI/contract test; migrates no rows | settings: PR-0 settings foundation | 0 |
| catalogs.* | 5 | keys `catalogs.*` (5 CONFIG-CANDIDATE) | settings: migrate catalogs.* | 1 |
| github.* (with receiver.*) | 26 | keys `github.*`/`receiver.*` (12) + 13 identity AGNOSTIC-VIOLATION rows (D6: SARIF `informationUri` ×3, owner/repo/issue refs ×7, default branch ×2, `gh` account) + `site.benchmark_url` (1) | settings: migrate github.* | 2 |
| witness.* | 2 | keys `witness.*` (2 CONFIG-CANDIDATE: `witness.log_public_key` witness.py:38, `witness.request_timeout_seconds` witness.py:99,151) | settings: migrate witness.* | 3 |
| execution.* | 8 | keys `execution.*` (8 CONFIG-CANDIDATE) | settings: migrate execution.* | 4 |
| supervisor.* / confinement.* / launcher.* | 23 | keys (17) + `paths.max_link_hops` + `probes.host_probe_env` (2) + 4 C5 platform rows (2 loader paths, syscall numbers, triple) | settings: migrate supervisor/confinement/launcher.* | 5 |
| journal.* / history.* / logs.* / redaction.* / observability.* | 15 | keys (13) + `paths.journal` + `evidence.max_results_bytes` (2) | settings: migrate journal/history/logs/redaction/observability.* | 6 |
| subject.* / delegation.* / repair.* / qualification.* | 16 | keys (14) + `artifacts.read_max_bytes` + `cli.conflict_display_paths` (2) | settings: migrate subject/delegation/repair/qualification.* | 7 |
| acceptance.* / observer.* | 14 | keys (7) + 7 Docker/observer container AGNOSTIC-VIOLATION rows (docker socket/CLI ×4, DB host/user, DB URI credential, `/bin/postgrest`) | settings: migrate acceptance/observer.* | 8 |
| toolchain.* | 11 | `toolchain.search_paths` + `provisioning.store_root` (2) + 9 host-tool/interpreter AGNOSTIC-VIOLATION rows (systemd tool paths, gcc-13 ×2, strace, systemd/bwrap/python3.12 pins, toolchain versions 13.3.0/6.8, `/usr/bin/python3` ×2, CPython pin) | settings: migrate toolchain.* | 9 |
| ci.* | 12 | keys `ci.*` (7) + 5 workflow AGNOSTIC-VIOLATION rows (`ubuntu-latest` ×2, apt package names ×2, AppArmor sysctl) | settings: migrate ci.* | 10 |
| dogfood.* | 25 | keys `dogfood.*` (21) + `antislop.min_examples_floor`, `oss_bench.sandbox`, `trainer.probe_timeout_seconds`, OCR asset pin (4) | settings: migrate dogfood.* | 11 |
| build.* | 2 | keys `build.*` (2 CONFIG-CANDIDATE) | settings: migrate build.* | 12 |

Assignment rule behind the `source` notes: identity literals to `github.*`
(D6); platform facts to the supervisor/confinement/launcher PR that owns the C5
table's consumers and the generated C header (C4); host tool and interpreter
pins to `toolchain.*`; workflow vendor/distro assumptions to `ci.*`;
Docker/observer container assumptions to `acceptance/observer.*`; each residual
family to the section whose PR edits the code that reads it (`paths.journal` and
`evidence.max_results_bytes` to persistence, `artifacts.read_max_bytes` and
`cli.conflict_display_paths` to the run/subject flow, `probes.host_probe_env` to
confinement, `antislop.*`/`oss_bench.*`/`trainer.*` to `dogfood.*`,
`provisioning.store_root` to `toolchain.*`, `site.benchmark_url` to `github.*`).
The 10 `commit=rem` rows (9 CONFIG-CANDIDATE, 1 TRUST-PIN) are covered by the
sections above and are migrated only after the remediation integration (order
011) merges (C4). Committed CI workflows are generated by `ranex settings
render-ci` with drift validation, and step-time values are consumed via `ranex
settings get <key>` (C4, E2). Every migration PR keeps current values as
defaults, so each is behaviour-identical before any operator opts into a
settings file.
