# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-056 opened)
**Active slice:** docs/slices/SLICE-056-real-e2e-verdict-family.md

## Where we stopped

SLICE-056 (#36, verdict-family real e2e) is open, contracts frozen red
(Worker A). Both family files — tests/e2e/test_gate_evaluate_real.py,
tests/e2e/test_journal_verify_real.py — commit 8 red: 7 golden-missing
(the four `tests/e2e/expected/*.out` are the implementation lane's
artifacts, captured from the real journeys through the ADR-032
normalizer) plus 1 behavioral red (journal verify must name the
byte-edited row — issue #36 sad path 3; today's CLI prints only
`chain=invalid`). Every journey mechanic verified green against the
installed kernel at freeze time: the no-evidence landing FAIL, the
keygen→run→evaluate PASS over real signed evidence, openssl's
independent Ed25519 verification, clean/tampered/truncated journal
verifies, and the truncation blind spot (a rolled-back journal verifies
PASS — characterized, asserted as the documented outcome, sad path 4).
Implementation lane unblocked: goldens + row-naming presentation, then
the sabotage-control run and `suite freeze` at close.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-056
Active: SLICE-056 — Worker B implements (goldens + row-naming + close
per the slice file's done criteria); SLICE-055 follow-ups registered in
its done slice file stay queued behind it.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape
  (subprocess-heavy tests vs the in-process trampoline; observability
  mutants remain unchecked — mutation evidence not obtained, disclosed).
- SLICE-056 hermetic-freeze behavior of the family journeys is an honest
  UNKNOWN at open time (slice file records the sanctioned remedy).
