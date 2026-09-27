# State

**Updated:** 2026-09-27
**Active slice:** none — ADR-065 accepted; SLICE-096 wiring landed;
SLICE-097 / #107 (authenticated approver) closed; SLICE-098 / #108
(external Rekor witness) closed; SLICE-099 / #109 (observation log)
closed on this branch.

**ADP / architecture freeze (promoted):**
- ADR-065 **accepted**; `governance/architecture-freeze.json` pins
  ranex's ten-subpackage graph + root `__init__`.
- `landing` gate carries claim `architecture`.

**#107 / RISK-07 closed:** catalogued `role: approver`, CLI possession
before `evaluate()`, second Ed25519 signature in the verdict.

**#108 / RISK-19+03 closed-with-witness:** DSSE-wrapped verdicts anchored
in Rekor (`gate evaluate --witness`; `journal verify --witnessed`);
pinned log key `governance/rekor_public_key.pem` (ADR-067 / SLICE-098).

**#109 / RISK-11 closed:** append-only hash-chained
`governance/observations.sqlite3`; `run` appends every signed record;
`gate evaluate` restores deleted FAILs as `removed-observation`;
`journal verify --observations` (ADR-068 / SLICE-099).

Recent: #112 minimization ladder; #102 delegated review. Queue remains
#115, #119, #105, #90; #88 parked.

Suite: standing host-drift / fixture red family on main unchanged by this
ship; refreeze is IDs-only and outcome-blind.
