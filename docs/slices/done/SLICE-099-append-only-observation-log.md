# SLICE-099 — Append-only observation log (RISK-11)

**Status:** done
**Origin:** issue #109; ADR-068; MAP RISK-11.

## Contract

- `src/ranex/governed_execution/adapters/persistence/sqlite/observations.py`
  — `ObservationLog`, `reconcile`, `REMOVED_OBSERVATION`
- `Journal` table-parameterised (`_table`) so the observation log shares schema
  discipline without duplicating the chain
- `record_evidence` appends every signed record to the paired log
- `gate evaluate` restores deleted FAILs and names `removed-observation`;
  refuses invented history with `E-OBSERVATION-CHAIN`
- `journal verify --observations`
- e2e: `tests/e2e/test_observation_log_real.py` (four real-CLI arms)

KERNEL_DIGEST unchanged. No new runtime deps.
