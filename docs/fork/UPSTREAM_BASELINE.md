# Ranex Upstream Runtime Baseline

| Field | Value |
|---|---|
| Captured | 2026-07-27 (Asia/Manila) |
| Phase result | `PARTIAL` |
| Upstream | `NousResearch/hermes-agent` |
| Upstream SHA | `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012` |
| Ranex adoption SHA | `9be6bd9443e447b205ad265d44238436910dfbce` |
| Baseline branch | `phase/2-runtime-bootstrap` |
| Runtime source changes | None; the only tracked worktree change during the run was the fork-only `.local/dev-env.sh.example` helper |
| Application home | Isolated through `HERMES_HOME=/home/soultransit/.local/share/ranex` |
| Model credentials used by baseline tests | None |

`PARTIAL` means the supported test entry point completed with three inherited,
host-sensitive test-isolation failures. It does not mean the Ranex runtime
bootstrap failed: the CLI, locked environment, JavaScript workspace, and
editable installation are operational. The failures are retained here so later
Ranex changes can be compared against an honest starting point.

## Host and toolchain

| Component | Observed value |
|---|---|
| OS | elementary OS 8.1 |
| Kernel | Linux 7.0.0-28-generic x86_64 |
| Python | CPython 3.11.15 in the external Ranex virtual environment |
| Hermes Agent | 0.19.0 (2026.7.20) |
| uv | 0.11.26 |
| Node.js | 24.18.0 |
| npm | 11.16.0 |
| Git | 2.43.0 |
| GitHub CLI | 2.96.0 |

The host's default Python 3.14 is outside upstream's supported
`>=3.11,<3.14` range. The baseline therefore uses the uv-managed Python 3.11
environment at `~/.local/share/ranex/venvs/dev`; it does not replace the
system Python.

## Environment and CLI checks

| Check | Result | Notes |
|---|---|---|
| `uv sync --locked --python 3.11 --extra all --extra dev` | `PASS` | Resolved the checked-in lockfile and installed Hermes editably from the Ranex development worktree |
| `uv lock --check` | `PASS` | Resolved 233 locked packages without changing `uv.lock` |
| `python -m compileall ...` | `PASS` | Covered `agent`, `hermes_cli`, `gateway`, `tools`, `providers`, and `plugins` |
| `hermes --version` | `PASS` | Executed from the external virtual environment |
| `hermes --help` | `PASS` | CLI entry point loaded |
| `hermes-acp --version` | `PASS` | Reported 0.19.0 |
| `hermes doctor` | `PASS_WITH_WARNINGS` | Exit code 0; optional integrations were absent and the doctor did not recognize the deliberately external entry-point location |
| `hermes config check` | `PASS` | Exit code 0 |

The initial doctor run also reported a missing `.env`, missing `config.yaml`,
and missing provider login. The isolated `.env` and `config.yaml` were then
created with mode `0600`; provider authentication and the live model smoke
test are recorded separately because they require a human device-code action.

## Python baseline

Canonical command:

```bash
HERMES_HOME=/home/soultransit/.local/share/ranex \
HERMES_PYTHON=/home/soultransit/.local/share/ranex/venvs/dev/bin/python \
scripts/run_tests.sh
```

| Measurement | Result |
|---|---|
| Test files | 2,342 |
| Passed | 48,519 |
| Failed | 3 |
| Skipped | 236 |
| Workers | 32 |
| Runner time | 562.9 seconds |
| Wall time | 567.12 seconds |

Failures and independent classification:

1. `tests/agent/test_copilot_acp_client.py::test_run_prompt_preserves_real_home_when_profile_home_available`
   expected the child process to preserve the real home. Upstream's container
   detector scans all mount information, sees host-mounted Docker/containerd
   paths, and falsely classifies this systemd host as a container. That causes
   the child home to be rewritten to the profile-scoped Hermes home.
2. `tests/agent/test_credential_pool_routing.py::TestFailureAttribution::test_auth_refresh_uses_stable_id_after_runtime_key_changes`
   expected no recovery, but the test's temporary one-entry pool auto-discovered
   the real user's Claude Code credential record and gained another entry.
3. `tests/agent/test_credential_pool_routing.py::TestFailureAttribution::test_unmatched_key_does_not_retry_only_pool_entry`
   made the same one-entry assumption and likewise rotated after real-home
   credential discovery.

The relevant source, tests, and test fixtures are byte-identical to upstream.
The repository wrapper reproduced the same three failures with only those two
test files and one worker: 30 passed and 3 failed in 5.8 seconds. Running the
credential-pool file through the same wrapper with an isolated nonexistent
`HOME` passed all 20 tests, confirming the real-home discovery cause. Per-file
subprocess isolation and the narrow reproduction rule out cross-file state and
parallelism. These failures are unrelated to the Ranex environment helper; no
production or test-source fix was mixed into baseline capture.

The parallel runner also marked
`tests/agent/test_context_compressor.py` flaky after its first attempt exceeded
300 seconds; the retry passed all 214 tests in 247.32 seconds.

## JavaScript baseline

| Check | Result |
|---|---|
| `npm ci --no-audit --no-fund` | `PASS` — 1,307 packages in 21.81 seconds |
| Checked-in `package-lock.json` digest | `UNCHANGED` |
| `npm run check` | `PASS` — 125.25 seconds |
| Vitest | 4,826 passed, 0 failed, 7 skipped |
| Workspace files | 516 passed, 1 skipped |
| TypeScript, ESLint, desktop build/package validation | `PASS` |

Nonblocking inherited warnings included 76 ESLint warnings with zero errors,
five deprecated npm-package notices, six install-script approval notices,
jsdom canvas and build-size/CSS notices, and one TUI subprocess that invoked
system `python` and could not import `yaml`. The TUI suite still passed all
1,394 of its tests.

## Worktree and credential boundaries

- The package lock and Python lock were unchanged.
- Generated `node_modules`, build, distribution, and release outputs are
  ignored.
- No model API key or OAuth credential was required or used by the baseline
  suites.
- GitHub authentication was used only for the separately audited Phase 1
  publication, not for these tests.
- The primary checkout remained on `bootstrap/pre-upstream` so its active
  Codex/VS Code documentation changes were not disturbed.

## Follow-up

1. Complete the separate OpenAI Codex device login and one-shot model smoke.
2. Track the three inherited Python failures as baseline defects; do not
   silently weaken their assertions.
3. Compare future Ranex changes against these exact counts and failure names.
