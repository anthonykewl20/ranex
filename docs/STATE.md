# State

**Updated:** 2026-09-08
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Production-readiness issue: #88, still open.
[App review](../tools/dogfood/FINDINGS.md#github-app-audit--2026-09-08): repaired fast-failure spool
loss, revoked-allowlist refresh, truncated API lists, latest-only reconciliation,
weak-ruleset reuse,
non-RSA credential crashes, malformed API responses and false fake-API receipts.
Full-suite review also repaired unlocked session delegation snapshots racing qualification.
Freeze artifacts regenerated; lifecycle E2E cleanup checks attribute scratch to their own run.

Fresh real-PR receiver stress: 41/41 checks. Live App recovery: HTTP 503,
retained queue, fresh receiver state, one successful real App check, no duplicate.
Receipts: tools/dogfood/audits/2026-09-08-app-review/.
Live recovery reuses an existing signed verdict; it does not rerun its tests.
Final-commit frozen pytest evidence is recorded in the issue closing comment.

Prior live HTTPS delivery, App-pinned merge refusal, wrong-source check refusal,
late verdict refresh and successful merge: audits/2026-09-08-live-app/.
App ranex-gate: 4863198, owner anthonykewl20, installation 159825611.

UNVERIFIED: multi-hour soak, supervised production traffic, secret rotation,
operational backup/restore, full Leitir/Arxic governed acceptance.
UNIMPLEMENTED: automatic evaluation, merge-candidate checks, shard aggregation,
Chock-equivalent multi-agent policy compiler/catalog.
No production sign-off or general zero-bug claim has been issued.

Dogfood publishing (#90): web hourly sync now consumes benchmarks, proof pile,
and committed audit sessions from one kernel checkout. Production verification
checks the benchmark fingerprint, proof HTML bytes, and audit snapshot.
Local-only sessions require commit + push before publication.
