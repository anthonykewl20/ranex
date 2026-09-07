# State

**Updated:** 2026-09-07
**Active slice:** none

Version v0.1.006 follows dogfood fix e3b2ccfadcb94fcbfdfe2921dfeffe2f0fc0e96a.
Issues: #89. Findings: F-033, F-034.
Integrated external-repository/Vitest onboarding (#86, PR #87) with v0.1.006.
Issue #88 production assessment: NO-GO for verified production operation.
Assessment: tools/dogfood/FINDINGS.md (issue #88, 2026-09-06 and 09-07).
Evidence: tools/dogfood/audits/2026-09-0{6,7}-production/.
2026-09-07 (ADR-053): receiver spools before work and answers ≤8 s (202 past
it), reconciles retries via attempt record + check external_id, refuses
group/other-readable App keys; JUnit collection skips keep their module ID.
ADR-054: heads answered action_required are refreshed from the same periodic
pass once their verdict lands (stamped refresh:<head>, reconciled).

Ordinary full baselines: Leitir 3,742 passed / 159 skipped; Arxic 1,974
passed across 234 files. Arxic lint and both typecheck commands passed.
These are not signed Ranex full-suite acceptance results.
Leitir's external-venv governed attempt had 22 failures and a collection-skip
JUnit refusal; its interpreter context changed. Arxic's governed attempt
could not resolve Vitest from the materialized repository. Reviewed complete
runtime/input provisioning and full governed acceptance remain UNVERIFIED.

67 App-surface tests passed locally. Real HTTP/state probes verified refusal,
replay conflict, restart dedupe, lock recovery and bounded connections.
Delayed acknowledgement, duplicate publication after completion-write failure
mode-0644 key acceptance and late-verdict refresh are repaired and re-probed.
CI's external-CLI subprocess coverage gap is repaired; the 100% changed-line
threshold remains intact. Final-commit regression evidence is recorded in #88.

Both pilot repositories lack required Ranex checks. Live App authentication,
installation, HTTPS delivery, App-pinned merge refusal, deployment recovery
and production load are UNVERIFIED; credentials and browser access are absent.
Automatic evaluation, merge-candidate and shard aggregation behavior
remain unimplemented. No production-readiness sign-off has been issued.
