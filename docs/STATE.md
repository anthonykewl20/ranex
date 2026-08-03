# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-03
**Phase:** map — the architecture description, not a slice
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`

## Where we stopped

**The owner's focus is the map. SLICE-006 is open and deliberately untouched.**
Stated plainly: *"we are not doing any slice, we are still writing the map."*
Do not start it, and do not offer to.

`docs/MAP.md` went `1.1.0` → `2.7.0` and moved into the capped docs set. It now
names one stakeholder — a solo operator running AI agents — with four concerns in
his own words, every requirement traced to one, six viewpoints, seven
correspondences, and the pre-reset corpus filtered rather than re-derived.
`governance/bom.yaml` holds 15 parts for one thread, with a checker.

Three adversarial passes ran: hy3 on the claims, DeepSeek on the structure, and a
`gpt-5.6-sol` xhigh audit of the map against the code. The audit found **15 wrong
`CONFIRMED` labels, 28 citations to files that do not exist, and 10 places the
map contradicted the code.** All corrected; the reasoning is in the commits.

## Next

1. **Finish the map.** `VP-05` and `VP-06` govern no view, so two of four
   concerns have nothing behind them and `CR-02` fails on purpose. Model kinds
   are absent. Only the first thread is enumerated in Baseline/Target/Gap.
2. **Audit `CLAUDE.md` against the code.** It has never been checked, and both
   `README.md` and `MAP.md` carried false claims when they finally were.
3. SLICE-006, then confinement — **only once the owner says the map is done.**

## Known limits

- **The BOM checker is structural, not semantic.** It calls `Path.is_file()`, so
  an empty test file passes. The map and its checker can drift together, green.
- **The concern set is self-declared** by the only stakeholder, who is also the
  architect, so coverage is internal consistency and not completeness. The owner
  named tool-server poisoning as a worry this session and it is **not** among the
  four. Nothing in the map can notice that.
- Mutation testing measures repeatability, not validity: it checks the gauge
  against the operator's own model of defects, never whether that model is right.
- **`mutmut` does report on `cli/main.py`** — 573 survivors, 65 unreached. The
  older claim that it "says nothing" there was false and is corrected everywhere.
- The journal detects an edited row but not a removed one; truncate the tail and
  the surviving prefix verifies clean.
- `approver_id` unauthenticated; same-uid signing-key theft reproduced and open;
  Ranex still does not gate its own repository.
