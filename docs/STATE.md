# State

**Updated:** 2026-10-01
**Active slice:** docs/slices/SLICE-103-audit-findings-and-remediation.md

**C1 done:** `f01d42a`, branch `captain/c1-policy-context-order`.
Deferred qualification checks now preserve evidence record order. Both policy
and executable filters verify lengths and signed-source identity, refusing
ambiguous duplicates, missing identity and mismatched adapter output safely.
No verdict.py changes, runtime dependencies, H1 or M1–M5 implementation.
`MAIN_PY_SHA256` updated in the implementation commit.

**Security evidence:** new production-chain regressions cover qualification
before/after foreign evidence, both filters' malformed/duplicate/missing/
unmatched/length-mismatched identity, and broken ordering. Origin/main
`c3ac86a85710dc615902e72d473d218d880e5af6`: 16 failed / 3 passed;
branch: 19 passed, 63 passed with existing policy/qualification/kernel contracts.
The foreign-first counterfactual already passed on main; retained, not hidden.

**Suite manifest:** production `ranex suite freeze` on committed `f01d42a`:
2469 tests / 157 expected skips; `load_manifest` accepted before commit.
Sealed freeze: 2268 passed / 146 skipped / 22 failed / 33 errors, NOT PASS.
Final direct-suite counts and every red ID's origin/main comparison accompany
the C1 review PR; documented suite drift is not silently repaired here.

**#105 shipped:** static OCR v3 subject, proof arms 0/1/2/3/5 VERIFIED;
arm 4 GAP by owner decision. Receipts:
`tools/dogfood/audits/2026-09-30-ocr-subject-v2/`.

**Remaining queue:** H1 observation-chain signed anchor, M1/M2 promotion,
M5 freeze/run conflict and honest red-suite repair, #112/SLICE-036 completion,
centralized logging, dead-code purge, manifest ID correction.

**Next:** SLICE-103 H1. C1 is ready for ordering-session review, not merged.
