# State

**Updated:** 2026-09-08
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open issues: #88 (production readiness, slice 085),
#90 (dogfood publication), #91 (F-002 explicit skip list).

F-010 is closed (#92, ADR-056). A non-strict XPASS was written to the JUnit
artifact as a bare `<testcase/>`, byte-identical to a pass, so ADR-011 sad path
5 did not hold. Read at source in pinned pytest 9.1.1: `skipping.py` sets
`outcome="passed"` and keeps the fact only on `rep.wasxfail`; `junitxml.py`'s
`append_pass` never reads it. No parser could recover it, so the outcome is now
*requested* — a `pytest-junit` suite claim must carry the adjacent tokens
`-o xfail_strict=true`, and the gate loader refuses at construction otherwise.
`--runxfail` and `-p no:skipping` (which also turns a declared skip into a bare
pass) are refused by name. `evaluate()` and `KERNEL_DIGEST` did not move; the
summariser is unchanged. Suite manifest re-frozen: tests 1874 → 1890,
expected_skips 166 preserved verbatim, `run_exit=0`.

Unchanged boundary, not claimed closed: a hostile tree can still forge the
artifact via `conftest.py` or an approved `pytest11` plugin (ADR-007, ADR-011
criterion 10, F-012). The rule reads argv, not `PYTEST_ADDOPTS`/`PYTEST_PLUGINS`.

Earlier App review (#88): repaired fast-failure spool loss, revoked-allowlist
refresh, truncated API lists, latest-only reconciliation, weak-ruleset reuse,
non-RSA credential crashes, malformed API responses, false fake-API receipts,
and unlocked session delegation snapshots racing qualification.
Fresh real-PR receiver stress: 41/41. Live App recovery: HTTP 503, retained
queue, one successful real App check, no duplicate.
Receipts: tools/dogfood/audits/2026-09-08-app-review/. Prior live HTTPS
delivery, App-pinned merge refusal and merge: audits/2026-09-08-live-app/.
App ranex-gate: 4863198, owner anthonykewl20, installation 159825611.

UNVERIFIED: multi-hour soak, supervised production traffic, secret rotation,
operational backup/restore, full Leitir/Arxic governed acceptance.
UNIMPLEMENTED: automatic evaluation, merge-candidate checks, shard aggregation,
Chock-equivalent multi-agent policy compiler/catalog, compliance-framework
coverage reporting, and a standard attestation envelope (DSSE / in-toto
`test-result`) — every surveyed competitor ships at least one of the last three.
No production sign-off or general zero-bug claim has been issued.

Findings ledger: F-002 closed (#91) — the gating journey's two session-dependent
qualified_host arms are declared host-capability skips (166 → 168), so plain
non-delegated shells and delegated scopes observe declared skips only.

Dogfood publishing (#90): web hourly sync consumes benchmarks, proof pile and
committed audit sessions from one kernel checkout. Local-only sessions require
commit + push before publication.
