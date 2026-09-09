# State

**Updated:** 2026-09-09
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open: #88 production readiness and #90 dogfood publication.
No production sign-off or zero-bug claim is issued.
Slice 086 supplies opt-in automatic judgment of signed PR evidence:
`github listen --evaluate-evidence` pins operator policy, evaluates the exact
PR SHA, verifies the signed verdict and publishes. It never runs contributor
code. Late evidence refreshes every 15 seconds; failed publication reconciles.

F-010 (#94, ADR-059): the controller supplies the canonical pytest reporter.
Explicit strict=False XPASS is retained as xpassed and blocks acceptance.
Missing/disabled reporting refuses observation. Nested pytest activation is
isolated; real pytest-xdist 3.8.0 workers preserve XPASS centrally.
Explicit -p loading remains supported, including separate applications;
a private module copy preserves materialised source and dependency versions.
Strict-local pytest observation refuses until its runtime carries this hook.

Real GitHub PRs #7, #8, #9 and #10 in anthonykewl20/ranex-app-live-probe completed
missing-evidence refusal → fresh Six PASS → explicit XPASS and merge refusal
→ repair → fresh PASS and merge. PR #10 merged
5d108f53c58c34cff7e16a7d383d598703a2e774. Its three retained observations
(185 pass; 184 pass + 1 xpassed; 185 pass, each with 15 declared skips)
were independently signature-verified by OpenSSL. GitHub confirmed delivery GUIDs.
PR #10 ran the rebuilt installed wheel without source-path injection.
The driver invokes observation explicitly; unattended execution is not proven.
Receipts: tools/dogfood/audits/2026-09-09-xpass-observer/.
The 30-case real Six audit has 25 VERIFIED and 5 GAP outcomes, not an overall PASS.
Supplemental checks: 41 receiver controls, 20,000 concurrent journal appends,
19 storage controls and real collection/executable recovery journeys.
Combined governed freeze: 1776 passed, 140 skipped; 1916 IDs, 168 declarations.
Release acceptance requires `uv run --frozen pytest -q` on the final commit;
the closing issue comment records that result. Focused changed-line coverage: 63/63.

Remaining audit boundaries: same-subject evidence reuse, hostile report
producers (F-012), and three attacks against unanchored journal verification.
F-005 (#93, ADR-057): signed v2 verdict anchors detect truncation; the external
Six audit verifies the true-chain/rewritten-chain differential. No independent
witness protects an operator controlling both signing keys.
UNIMPLEMENTED: isolated automatic observer scheduling, merge-candidate/group
checks, shard aggregation, policy compiler/catalog, standard DSSE/in-toto
attestations, compliance coverage and an external journal witness.
UNVERIFIED: production hosting, sustained traffic/soak, credential rotation,
backup/restore, foreign same-name check availability and external-harness acceptance.
Serialise full suites on this host; concurrent runs have exhausted its memory.
Dogfood publishing (#90) consumes committed/pushed audit sessions from a checkout.
