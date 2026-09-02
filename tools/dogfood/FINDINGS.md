# Dogfood findings

Output of the iteration loop (`dogfood.py iterate`). Every finding names the
verified behaviour, the file:line anchor, and the scenario that pins it. A
finding is only closed by a change in the KERNEL that makes its pinning
scenario drift (which the loop reports) — never by editing the scenario to
match the kernel silently.

## Open

### F-002 (CANDIDATE, UNVERIFIED) — suite-freeze counts appear checkout-environment-sensitive

- Observed (2026-09-03 ~02:30): the full suite run on commit fbb052e8b in a
  CLEAN THROWAWAY WORKTREE (/tmp) collected 1653 tests (1561 passed, 86
  skipped, 6 failed incl. `test_frozen_transcript_matches_the_golden` and
  two gating tests), while the then-committed golden expected 1681 IDs /
  164 skips. Same commit, different working location → different collected
  counts and skip arms.
- Confounds (why this is a candidate, not a finding): concurrent sessions
  were actively repairing the freeze golden (3613e7e22, then a3660edf0
  gating a probe arm) during the run, so part of the mismatch may be their
  mid-flight state rather than environment sensitivity. Also only 3 of the
  6 failure names were captured (output truncation).
- Next step (needs a stable, clean main checkout): run the suite twice —
  once in the main checkout, once in a throwaway worktree at the SAME
  commit — and compare collected counts and skip sets. If they differ
  reproducibly, the frozen manifest is not location-independent and that is
  a real reproducibility weak point in the freeze discipline itself.
- Not pinned by a scenario yet; do not close without the paired run.

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
