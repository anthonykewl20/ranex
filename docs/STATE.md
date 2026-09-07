# State

**Updated:** 2026-09-07
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Issues: #88. Findings: F-033–F-036.
Live calibration landed (F-035 fix): awaiting heads survive refused
action_required publications. Evidence: tools/dogfood/audits/
2026-09-07-live-app/ — real smee.io HTTPS deliveries, real api.github.com
refusals, real fetch/bind/verdict resolution, SIGKILL recovery, replay
no-op, connection bound. No mock GitHub in that pass.

Governed probe repo anthonykewl20/ranex-app-live-probe runs the real
ceremony (keys, freeze, run, PASS verdicts, journal verified).

Still blocked on the owner: GitHub App creation is web-only; no
anthonykewl20 browser session exists on this host. The manifest form is
staged at http://127.0.0.1:8081/ with the catcher armed; after that one
click: install, App-pinned ruleset, live PR journey, merge enforcement.

Live authentication, installation, HTTPS delivery from GitHub, App-pinned
merge refusal, deployment recovery and production load stay UNVERIFIED.
Automatic evaluation, merge-candidate checks and shard aggregation stay
unimplemented. No production sign-off has been issued.
