# SLICE-090 — Calibrated live HTTP observer

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

Public CLI refusal tests are red before implementation. The real Docker journey
requires `RANEX_LIVE_HTTP_EXPERIMENT=1` and the two installed image IDs named in
the integration fixture; a skipped Docker journey in the regression suite is not
release evidence. The installed console script was qualified on 2026-09-23 by
`tools/dogfood/live_observer_proof.py` and re-qualified unchanged (16/16) on
2026-09-24 after lint hardening; the committed receipts are from that
re-qualification and bind the delivered observer bytes: three identical good-candidate runs
(observed match, six trials each, byte-identical observation rows), three
known-bad runs rejected at tenant isolation, and three runs each of the
surviving-control, compile-error and wrong-assertion calibration refusals.
Raw receipts: `tools/dogfood/audits/2026-09-23-live-observer/`. Full suite and
committed-tree manifest freeze remain mandatory for this slice.

## Boundaries

Linux controller and Docker daemon are trusted. The initial service profile is
PostgREST with SQL application code, fixed test roles and ephemeral credentials.
Startup readiness is a measured race: PostgREST can answer transient 503
connection-refused probes until its database pool is warm; the observer retries
under its frozen deadline and retains every probe as raw evidence, so probe
counts vary while frozen journey-step observations repeat byte-identically.
No general arbitrary-server, browser, hostile-host or production claim. The
result is OBSERVED-MATCH / OBSERVED-MISMATCH / execution or calibration error,
not C approval, evidence admission, product PASS or merge. Remaining ADR-061
exits (task authority, integration, release) retain their own implementation
and real-execution requirements.
