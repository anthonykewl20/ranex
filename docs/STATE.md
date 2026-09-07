# State

**Updated:** 2026-09-07
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Issues: #88. Findings: F-033, F-034.
Issue #88 production assessment remains NO-GO for verified live operation.
SLICE-085 (ADR-055) makes App creation, credential storage and the
App-pinned `ranex/acceptance` ruleset operable from the CLI.

Local App-surface tests cover bind, publish, receive, register, status
and ruleset against a fake API. Live App authentication, installation,
HTTPS delivery, App-pinned merge refusal, deployment recovery and
production load stay UNVERIFIED until a real conversion is observed.
Automatic evaluation, merge-candidate checks and shard aggregation stay
unimplemented. No production-readiness sign-off has been issued.

Ordinary full baselines and governed Leitir/Arxic acceptance remain as
recorded in tools/dogfood/FINDINGS.md (issue #88, 2026-09-06/07).
