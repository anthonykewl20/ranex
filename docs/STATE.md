# State

**Updated:** 2026-09-09
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open: #88 production readiness, #90 dogfood publication,
No production sign-off is issued.
Completed slice 086: opt-in automatic judgment of signed PR evidence.
`github listen --evaluate-evidence` pins operator policy, evaluates the exact
PR SHA, verifies its signed verdict and publishes. It never runs contributor
code. Late evidence refreshes every 15 seconds; failed publication reconciles.

Real GitHub PR #6 in anthonykewl20/ranex-app-live-probe completed:
GitHub-origin webhook → missing-evidence merge refusal → upstream Six
observation (185 pass, 15 declared skips) → automatic signed PASS → source
break (5 failing tests) and merge refusal → repair, fresh observation, PASS
and merge ddfa81ae59f707d2ec8f8aca0f793e31f6183816.
The driver explicitly invokes observation; unattended execution is not proven.
Receipts: tools/dogfood/audits/2026-09-09-automatic-evidence/fifth-pass/.
The final signed v2 verdict matches the retained journal anchor.
ADR-058 records the boundary; foreign same-name check availability is UNVERIFIED.

F-010 CLOSED (#92 ADR-056, #94): `-o xfail_strict=true` sets only pytest's
default, so a claim also binds `-p ranex.foundation.pytest_xpass`, a
kernel-owned reporter reading `report.wasxfail` — the field junitxml's
`append_pass` discards. It catches an explicit `xfail(strict=False)` too. The
real Six audit now records **VERIFIED nonstrict-xpass** (GAP before). `ranex
run`'s hermetic env declares the materialisation's vendored `src`, without
which the governed child cannot import the reporter at all.
A hostile conftest/plugin can still forge JUnit (F-012, pinned as a passing
test); argv admission does not inspect PYTEST_ADDOPTS.
F-005 (#93, ADR-057): v2 verdicts sign journal_head; `journal verify
--against-verdict` checks it. Archived v1 stays readable but cannot anchor.
Measured on the external Six subject: the anchor accepts the true chain and
refuses a truncation that plain `journal verify` accepts.
There is no external witness against an operator controlling both keys.
F-002 (#91): 168 skip declarations retain the session/host prerequisites.

Earlier App repairs retained: durable delivery, allowlists, pagination,
check reconciliation, effective ruleset validation and API refusal handling.
UNIMPLEMENTED: isolated automatic observer scheduling, merge-candidate/group
checks, shard aggregation, multi-agent policy compiler/catalog, compliance
coverage, standard DSSE/in-toto attestations and an external journal witness.
UNVERIFIED: production hosting, sustained traffic/soak, credential rotation,
backup/restore and full external-harness governed acceptance.
Host note: concurrent full suites plus the large uvicorn service have exhausted
62 GB and OOM-killed freezes. Serialise full-suite verification on this host.
Dogfood publishing (#90) consumes committed/pushed audit sessions from a checkout.
No general zero-bug or market-leadership claim is made.
