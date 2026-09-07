# State

**Updated:** 2026-09-08
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Issues: #88. Findings: F-033–F-037.
Live App verification COMPLETE for the App surface: App ranex-gate (4863112's
replacement, owner anthonykewl20, installation 159825611) authenticates,
receives real GitHub webhooks over HTTPS (smee), publishes ranex/acceptance,
refreshes late verdicts, enforces the App-pinned ruleset (HTTP 405), defeats
a same-named forged Actions check, merges only behind a signed verdict, and
redeliveries replay as no-ops. Evidence: tools/dogfood/audits/
2026-09-08-live-app/ (no mock GitHub).

F-035/F-037 fixes and pre-App live calibration: audits/2026-09-07-live-app/.

Remaining UNVERIFIED: multi-hour soak, supervised deploy under traffic,
secret rotation, full Leitir/Arxic governed acceptance. Automatic
evaluation, merge-candidate checks, shard aggregation: unimplemented.
No production sign-off has been issued.
