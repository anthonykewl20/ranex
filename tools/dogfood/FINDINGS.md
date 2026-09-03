# Dogfood findings

Output of the iteration loop (`dogfood.py iterate`). Every finding names the
verified behaviour, the file:line anchor, and the scenario that pins it. A
finding is only closed by a change in the KERNEL that makes its pinning
scenario drift (which the loop reports) — never by editing the scenario to
match the kernel silently.

## Open

### F-003 (CONFIRMED, environmental prerequisite) — governing third-party repos needs a vendored CLI and root-installed test tooling

- Verified 2026-09-03 while building the OSS two-arm benchmark:
  1. `governed_repository_root()` (cli/repository.py:331) resolves the
     governed repo from the CLI's own location, NOT caller cwd — so the CLI
     governs the repo that contains it. Governing a third-party task repo
     requires vendoring `src/ranex` into that repo and running with
     `PYTHONPATH` pointing there (the kernel's own clone-judges-clone model;
     consistent with ADR-009, but undocumented for external integrators).
  2. `ranex run` resolves argv[0] only through the pinned toolchain
     (`/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`), refusing user-writable
     routes — by design. Consequence: task commands like `python -m pytest`
     cannot run under governance unless a pinned interpreter carries pytest,
     which on this machine requires root (`sudo apt install python3-pytest`).
- Not a security bug — the pin is correct. It is an integration/usability
  cost that any external adopter hits on day one. Candidate improvement:
  document the vendoring pattern + a supported way to author a task-local
  toolchain root that keeps the writability refusal.
- Blocked-on-owner: installing pytest for /usr/bin/python3 (or moving the
  study to a machine with system pytest / a Go toolchain at /usr/bin).

### F-002 (CONFIRMED) — suite outcome split is checkout-environment-dependent; expected_skips are not location-reproducible

- Verified 2026-09-03 (~04:30), paired sequential runs at commit edf1a98605:
  - main checkout:   1657 collected, 1623 passed,  34 skipped, exit 0 (green)
  - fresh worktree:  1657 collected, 1598 passed,  59 skipped, exit 0 (green)
- Same commit, identical collected ID set, both green — but 25 tests pass in
  the main checkout and skip in a fresh worktree. The outcome split depends
  on untracked local state (e.g. `.local/**` scratch, host qualification
  material), so a frozen `expected_skips` set cannot be reproduced from an
  arbitrary clone location.
- Also observed, NOT interpreted (the freeze accounting was not read):
  the committed golden (`governance/suite_manifest.json`) expects 166 skips
  while both runs produced 34 / 59 — how expected_skips are counted by the
  freeze tool vs pytest is UNVERIFIED here.
- Methodology note: two earlier PARALLEL runs of the same suites produced
  failures/errors in the confinement/cgroup tests in both locations; the
  repo's own ADR-046 requires serialized cgroup probes. Sequential runs are
  mandatory for any suite comparison on one machine — parallel full-suite
  runs on this repo are invalid by construction.
- Severity: LOW (green preserved everywhere; reproducibility of the frozen
  skip set across checkout locations is the weak point). Candidate fix
  direction (not attempted): make the location/state-dependent skip arms
  explicit expected-skip declarations the freeze already supports, or have
  the e2e prereqs materialize the missing state in any checkout.

### F-001 — `Journal.verify()` raises instead of returning False on non-JSON record corruption

- Anchor: `src/ranex/governed_execution/adapters/persistence/sqlite/journal.py:176`
  (`json.loads(row["record"])` inside `verify()`, unguarded).
- Behaviour (verified): corrupting a journal row's `record` to non-JSON text
  (after dropping the UPDATE trigger out-of-band) makes `verify()` raise
  `json.JSONDecodeError` (a `ValueError`), while the docstring contract says
  "False means a row changed outside `append`".
- Severity: LOW (API contract, not security). The failure is closed — the
  corruption is never accepted; but a caller written to the documented bool
  contract will crash instead of reporting tampering. `cmd_journal_verify`
  currently lets the exception surface as a traceback rather than naming the
  broken row, unlike the chain-mismatch path which names seq + ordinal.
- Pinned by: `journal-nonjson-corruption` scenario (facts record the raising
  behaviour; any kernel fix will surface as baseline drift).

## Closed

### F-000 — construction-time capability drift between the catalog and the parser (tool-side, closed same session)

While wiring the CLI scenarios, three catalog assumptions failed against the
real code and were corrected by reading the source, not by relaxing the check:
`Gate` requires an explicit `blocking=True` argument (a non-blocking gate is
refused at construction — `verdict.py:208`), `Journal.append` takes structured
records with `.as_record()` (not dicts), and junitxml test IDs are synthesised
as `classname.py::name` (`suite_results.py:129`). Recorded because it is the
loop working as designed: assumptions die when they meet the parser.
