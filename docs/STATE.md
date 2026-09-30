# State

**Updated:** 2026-09-30
**Active slice:** none — SLICE-102 / #119 (acceptance task loop) closed on
this branch; #115 gate-calibration and #88 / SLICE-085 closed on main.

**#119 / ADR-061 task authority closed:** `specification approve-task` /
`build-task` / `reapprove-task` / `land-task` and top-level `prove --task`
compose A/B/C grants, journal CAS, evaluate() and the #118 live observer.
Three persisted OBSERVED-MISMATCH misses revoke; land requires the exact
PASS candidate and unchanged target head. Receipts:
`tools/dogfood/audits/2026-09-30-acceptance-task-loop/` (#95 vocabulary,
3× deterministic repeats).

**#115 / MAP §8.4 gate certificates:** marker, landing, handbook-delegate
receipts under `tools/dogfood/audits/2026-09-30-gate-calibration/`;
`bom.yaml` `calibrated` distinct from `built`.

**ADP / architecture freeze (promoted):** ADR-065 accepted;
`landing` carries claim `architecture`.

**Still closed:** #107–#109, #112, #102, #118, #88 (live App observed;
production soak UNVERIFIED).

Queue: #105, #90 where still open.

Suite: standing host-drift / fixture red family on main unchanged by this
ship; refreeze is IDs-only and outcome-blind.
