# SLICE-088 — Calibrated live HTTP observer

**Status:** done
**Issue:** #118
**ADR:** docs/adr/ADR-061-live-acceptance-before-completion.md

## Contract

`ranex specification observe-http` consumes an independently pinned executable
bundle. Its frozen invocation selects a frozen declarative JSON profile. The
trusted controller materializes the exact Git candidate, starts local images
by immutable image ID, loads candidate SQL into real PostgreSQL, and sends HTTP
requests to its inspected PostgREST endpoint. Candidate scripts and reports
never execute in the observer. No runtime dependency is added.

Every HTTP step has explicit equality assertions and may capture scalar response
values for later requests. Process controls cover application restart, database
stop and database start. Bounds and repetition count are frozen. At least one
named product SQL mutation must fail its specified HTTP assertion. Surviving,
inapplicable and unrelated failures block calibration. Timeouts and cleanup
failures cannot become observed success. Receipts retain candidate, bundle,
observer, schema and container identities plus actual responses and commands.

## Exits and evidence

Public CLI refusal tests are red before implementation. Real Docker journey
requires `RANEX_LIVE_HTTP_EXPERIMENT=1` and the two installed image IDs named in
the integration fixture. Run it explicitly and retain receipts before release;
a skipped Docker journey in the general regression suite is not its evidence.

R&D retained startup-race and wrong-sequence-oracle failures before a revised
Git-bound experiment matched three baselines and rejected three committed
mutants at tenant isolation. The shipped CLI is qualified separately, including
calibration refusal controls. Full suite and committed-tree manifest freeze
remain mandatory for this slice.

## Boundaries

Linux controller and Docker daemon are trusted. The initial service profile is
PostgREST with SQL application code, fixed test roles and ephemeral credentials.
No general arbitrary-server, browser, hostile-host or production claim. The
result is OBSERVED-MATCH / OBSERVED-MISMATCH / execution or calibration error,
not C approval, evidence admission, product PASS or merge. Remaining ADR-061
exits retain their own implementation and real-execution requirements.

Source freeze at b903e53: 1865 passed, 161 skipped; 2026 IDs and 169 expected
skips, run_exit=0. Live CLI: 12 passed in 70.65s. Full final-commit evidence
is recorded in the closing issue comment; no release claim precedes that run.
