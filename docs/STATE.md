# State

**Updated:** 2026-09-30
**Active slice:** docs/slices/SLICE-103-audit-findings-and-remediation.md

**SLICE-103 (open):** exhaustive code-only audit complete (six lanes,
every finding re-verified against source). Verdict: kernel real and well
tested; 8/11 recent features genuinely shipped; initial plans NOT finished.
Full findings and the prioritized remediation queue live in the slice.
Priority order: C1, H1, M1/M2, red-suite truth, #112/SLICE-036, centralized
logging, dead-code purge + manifest fix.

**Critical/High/Med:** C1 SLICE-081 policy-context binding fails open
(`admission.py:577` reorders qualification evidence; `cli/main.py:472/:560`
zips by position). H1 observation-log head unanchored — wholesale
self-consistent rewrite defeats RISK-11 (no signed chain head). M1/M2
promotion gate admits NaN/inf and crashes on malformed claims; M3
`record_evidence` non-atomic; M4 bwrap probe unbounded; M5 `suite freeze`
refuses the artifacts `run` itself wrote (freeze exemption list never
updated for #109's `observations.sqlite3`).

**Suite on settled tip f42f03fed:** `uv run --frozen pytest -q` produced
2330 passed / 65 skipped / 13 failed / 26 errors / exit 1. Root causes:
stale `MAIN_PY_SHA256` pin (test_slice017 gate10); pre-#109 contracts in
test_slice003 and the golden e2e family (observation-log restore semantics);
slice036 compiled-artifact digest drift; E-046 host gate. "Standing host
drift" is an incomplete label. Do not trust a closure that cites it without
per-test root causes.

**Unfinished:** #112 proof arms hard-coded GAP (receipts contradict the
closure; the firstmate brief demanded real receipts —
`third_party/firstmate/data/ranex-112/brief.md`); SLICE-036 batch issuance +
fanout qualification (`tests/e2e/test_task_real.py:957` dead under skip);
#115 reproducibility leg UNVERIFIED; zero code for merge-group governance,
shard aggregation, policy compiler. Logging FAIL: no logging module; emitter
default-OFF and CLI-only; 6/10 packages silent; no debug mode.

**Housekeeping:** ADR-065 accepted; `governance/architecture-freeze.json`
pins the ten-subpackage graph. Worktrees consolidated 2026-09-30: all
uncommitted/unpushed work rescued to pushed `rescue/` branches first; clean
slate, no work lost. Local `third_party/firstmate/` tree (git-excluded)
breaks `test_docs_discipline` working-tree scan on this host; clean CI
passes — move it out of the checkout when practical.

**Next:** remediation queue in SLICE-103, C1 first.
