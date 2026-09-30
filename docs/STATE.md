# State

**Updated:** 2026-09-30
**Active slice:** none — #115 gate calibration certificates shipped;
#88 / SLICE-085 closed with retained live App evidence (no production
sign-off).

**#115 / MAP §8.4 closed for relied-on gates:** certificates under
`tools/dogfood/audits/2026-09-30-gate-calibration/` for the marker gate,
landing suite gate, and handbook-governed delegate path. Known-defect catch,
journal firing counts, Gauge R&R repeatability (×3 byte-identical), and recall
FALSE-PASS with a named suspect window are measured. `bom.yaml` carries
`calibrated` distinct from `built`, naming those receipts. BASE freeze cited:
`governance/calibration/base-freeze-v1.json`.

**Production use licensed only for what those certificates cover on this host.**
No general zero-bug or market claim.

**UNVERIFIED:** cross-host/operator Gauge R&R; AIAG % thresholds; full-repo
landing under the lab certificate; live App soak/rotation/backup (#88);
standing host-drift / E-C17 / fixture red family on main.

Recent closed: #107–#109, #112, #102, #88. Queue: #119, #105, #90.
