# ADR-068 — append-only hash-chained observation log

**Status:** accepted

**Date:** 2026-09-27
**Decision-makers:** repo owner
**Closes:** MAP RISK-11 (`evidence.json` is a current view, not history). Issue #109.

## Context

`record_evidence` replaces the previous record for the same claim+producer and
rewrites `governance/evidence.json`. A recorded FAIL that was never evaluated
can be deleted; evaluation then reads the gap as honest absence (denial,
unbounded). Signatures prevent forgery of a new PASS; they do not prevent
erasure of a FAIL.

ADR-043's journal already proves the schema discipline for an append-only,
hash-chained SQLite log. The same shape fits observation history without moving
`KERNEL_DIGEST` / `verdict.py`.

## Decision

1. **`governance/observations.sqlite3`** (gitignored), table `observations`,
   same `seq/record/prev_link/link` schema and UPDATE/DELETE triggers as the
   evaluation journal (`Journal` subclass with `_table = "observations"`).
   `ranex run` appends the exact signed record it also writes to
   `evidence.json`. The evidence file remains the projection the kernel judges.
2. **`gate evaluate` reconciliation.** When the log file exists, every evidence
   record must be in the chain (`E-OBSERVATION-CHAIN` otherwise). A
   chain-latest record the projection lacks is restored for judgment and named
   `removed-observation` in the projected diagnosis (and CLI presentation).
   When the log is absent, today's path is unchanged — protection activates
   once `run` has written the log.
3. **`journal verify --observations`** walks the observation chain the same way
   as the evaluation journal.
4. **Retention** is unbounded and operator-owned (ADR-043 stance). Records are
   already public-key-verifiable signed content; the log carries no secrets.

## Consequences

- KERNEL_DIGEST / `verdict.py` unchanged; naming is projection + reader known
  cause set only.
- No new runtime dependency.
- Hand-written evidence fixtures without a log keep working; production `run`
  paths gain the chain.

## Confirmation

`tests/e2e/test_observation_log_real.py` — four real-CLI arms per issue #109 /
#95 protocol (positive, negative, repeats).
