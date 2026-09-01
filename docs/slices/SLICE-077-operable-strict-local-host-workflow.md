# SLICE-077 — operable strict-local host workflow

**Status:** open
**Opened:** 2026-09-01
**Priority:** P0 — production blocker (issue #64)
**Issue:** #64
**ADR:** docs/adr/ADR-044-delegated-host-workflow-operator-surface.md

## Contract

Issue #64 acceptance criteria (verbatim):

- One documented public command prepares or enters the required delegated
  cgroup and runs strict-local without manual systemd choreography.
- Launcher build, install, qualification, and version/identity checks are
  discoverable public operations.
- A real v1, v2, and v3 run succeeds on a freshly qualified
  production-like host.
- Host drift and prerequisite failures identify the failed check and
  corrective action, while preserving fail-closed behavior.
- JUnit/evidence/log artifacts are retained for success and refusal paths.
- Acceptance evidence records the real cgroup tree, launcher identity,
  commands, exit codes, stdout, and stderr.

## Owned paths

- New: `src/ranex/cli/host_workflow.py` — `ranex host strict-local`
  phases A-D (precheck, scope entry, one-cgroup lifecycle, artifacts),
  the `CORRECTIVE_ACTIONS` catalog, and the canonical
  `host-run-report.json` writer (schema `ranex-host-strict-local-run-v1`).
- Modify: `src/ranex/cli/main.py` — register the `ranex host` group in
  `build_parser()` (verbs `launcher-build`, `launcher-install`,
  `host-probe`, `qualify`, `launcher-identity`, `strict-local`); the
  hidden argv[0] intercept stays so existing invocation paths keep working.
- Tests: `tests/contract/test_host_operator_surface.py`,
  `tests/integration/test_host_workflow.py`,
  `tests/e2e/test_host_workflow_real.py`.
- Governance: `governance/suite_manifest.json` re-freeze after the new
  test IDs land; `governance/gates.yaml` command unchanged.
- Docs close-out: this slice file, `docs/STATE.md`, README, `docs/MAP.md`.

## Done criteria

1. `ranex host --help` lists all six verbs; the workflow needs no manual
   systemd choreography anywhere in the docs.
2. `launcher-build`, `launcher-install`, `qualify` (defaults = the four
   canonical paths frozen in `governance/gates.yaml:19`), and
   `launcher-identity` (ranex-launcher-v1 digest/protocol check) are
   reachable as public `ranex host` verbs.
3. A real v1, v2, and v3 `strict-local` run succeeds on a freshly
   qualified production-like host, inside the one delegated cgroup the
   wrapper entered (qualify always fresh per run — the E-C18 fix).
4. Every named precheck and every `E-C17-*`/`E-C18*` refusal code
   identifies the failed check and prints a HINT corrective action;
   fail-closed before any scope entry or build step; pairing misuse →
   EXIT_USAGE before scope entry.
5. Success and refusal runs both retain `host-run-report.json` plus
   bounded, redacted, digest-bound logs under the result dir; the suite
   artifact home is never touched by the wrapper (frozen
   refusal-writes-nothing contract intact); `result_binding` is an
   honest null when the session result is unpublished.
6. Acceptance evidence records the real cgroup tree, launcher identity,
   commands, exit codes, stdout, and stderr; the wrapper itself generates
   no junitxml (documented recipe passes `--junitxml` through to pytest).
7. All new/modified tests pass; the suite manifest is re-frozen to
   include their IDs; `tests/contract/test_docs_discipline.py` green.

## Tranche plan

- T0 (this tranche): governed docs — ADR-044 accepted with vendored
  prior art, this slice opened, STATE repointed.
- T1: implementation tranche — `src/ranex/cli/host_workflow.py`, CLI
  wiring, the three test files frozen red then proven green.
- T2: real-host acceptance evidence — real v1/v2/v3 `strict-local` runs
  on a freshly qualified host; acceptance transcript + artifacts
  (report, logs, cgroup tree, launcher identity) attached to issue #64.
- T3: docs close-out — slice moved to `docs/slices/done/`, STATE/README/
  MAP updated, suite manifest re-frozen.

## Evidence

- `tests/contract/test_host_operator_surface.py` — public surface,
  frozen-command non-regression, corrective-action catalog coverage.
- `tests/integration/test_host_workflow.py` — precheck branches,
  sentinel recursion guard, pairing misuse, report outcomes (T1).
- `tests/e2e/test_host_workflow_real.py` — real v1/v2/v3 end-to-end
  runs asserting the report schema and the shared cgroup root (T1/T2).
- Acceptance transcript + artifacts to be attached to issue #64 in T2 —
  not produced yet; nothing here is claimed as run.

## Non-goals

- No kernel session changes (`governed_execution/` untouched; zero new
  systemd references in the kernel).
- No junitxml generation by the wrapper itself.
- No change to the module CLI argv (`python -m ranex.cli.host_confinement`)
  or to the `governance/gates.yaml` frozen command.
- No `--version` flag on the launcher; identity is the
  `ranex-launcher-v1` protocol pipe surface only.
