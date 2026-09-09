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
materialised source precedes the controller import path.
Strict-local pytest observation refuses until its runtime carries this hook.

Real GitHub PRs #7, #8 and #9 in anthonykewl20/ranex-app-live-probe completed
missing-evidence refusal → fresh Six PASS → explicit XPASS and merge refusal
→ repair → fresh PASS and merge. PR #9 merged
842983261fadc3dbd0c9bb5a46540b9560f613ca. All three retained observations
(185 pass; 184 pass + 1 xpassed; 185 pass, each with 15 declared skips)
were independently signature-verified by OpenSSL. GitHub confirmed delivery GUIDs.
The driver invokes observation explicitly; unattended execution is not proven.
Receipts: tools/dogfood/audits/2026-09-09-xpass-observer/.
The 30-case real Six audit has 25 VERIFIED and 5 GAP outcomes, not an overall PASS.
Combined governed freeze: 1776 passed, 140 skipped; 1916 IDs, 168 declarations.
Release acceptance requires `uv run --frozen pytest -q` on the final commit;
the closing issue comment records that result. Focused changed-line coverage: 57/57.

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
