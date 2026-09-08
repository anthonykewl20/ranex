# State

**Updated:** 2026-09-09
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open issues: #88 (production readiness, slice 085), #90
(dogfood publication).

Findings closed this pass — each pinned by a test that asserts the defect, so
regressions surface as a failing pin rather than a silent return:

- **F-010 (#92, ADR-056).** Non-strict XPASS is byte-identical to a pass in
  JUnit (pinned pytest drops `rep.wasxfail` in `append_pass`), so a
  `pytest-junit` claim must carry `-o xfail_strict=true`; `--runxfail` and
  `-p no:skipping` refuse by name. Refused where the **Gate is constructed** —
  all four `results_artifact` consumers, including `cmd_task_judge`'s duplicated
  `Gate(...)` — not at parse, so historical base commits still load.
- **F-005 item 1 (#93, ADR-057).** The verdict signs its journal head
  (`journal_head`, domain `ranex-verdict-v2`); `journal verify
  --against-verdict` refuses the complete rewrite `verify()` accepts. v1 stays
  verifiable (archived Leitir/Arxic receipts) but cannot anchor or gate — a
  first cut refusing v1 outright broke archive verification; pinned on real receipts.
- **F-002 (#91, parallel session).** Two session-dependent gating arms declared
  `ranex-context:host-capability:` (expected_skips 166 → 168).

Unchanged boundaries, not claimed closed: a hostile tree can forge the JUnit
artifact via `conftest.py`/approved `pytest11` plugin (ADR-007, ADR-011 c.10,
F-012); the xfail rule reads argv, not `PYTEST_ADDOPTS`. The journal anchor
has no external witness — an operator holding both keys can still rewrite.

App review (#88): nine receiver/App repairs (spool loss, allowlist refresh,
truncated lists, reconciliation, ruleset reuse, non-RSA keys, malformed
responses, fake receipts, delegation race). Stress 41/41; live recovery one
real check, no duplicate. Receipts: tools/dogfood/audits/2026-09-08-*.
App ranex-gate: 4863198, owner anthonykewl20, installation 159825611.

UNVERIFIED: multi-hour soak, supervised production traffic, secret rotation,
operational backup/restore, full Leitir/Arxic governed acceptance.
UNIMPLEMENTED: automatic evaluation, merge-candidate checks, shard aggregation,
Chock-equivalent policy compiler/catalog, compliance-framework coverage
reporting, a DSSE / in-toto `test-result` projection, a transparency-log
witness for the journal anchor. No production sign-off has been issued.

Host note: two agents cannot verify concurrently here — a 12.7 GB `uvicorn`
plus two full suites exhausts 62 GB and OOM-kills freezes. Serialise.

Dogfood publishing (#90): web hourly sync consumes benchmarks, proof pile and
committed audit sessions from one checkout; local sessions need commit + push.
