# State

**Updated:** 2026-09-09
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open: #88 production readiness and #90 dogfood publication.
No production sign-off or zero-bug claim is issued.
Slice 086 supplies opt-in automatic judgment of signed PR evidence:
`github listen --evaluate-evidence` pins operator policy, evaluates the exact
PR SHA, verifies the signed verdict and publishes, never running contributor
code. Late evidence refreshes every 15s; failed publication reconciles.

F-010 (#94, ADR-059): the controller supplies the canonical pytest reporter.
Explicit strict=False XPASS is retained as xpassed and blocks acceptance.
Missing/disabled reporting refuses observation; nested activation is isolated;
real pytest-xdist 3.8.0 workers preserve XPASS centrally. Strict-local
observation refuses until its runtime carries the hook.

Real GitHub PRs #7-#10 in anthonykewl20/ranex-app-live-probe completed
missing-evidence refusal → fresh Six PASS → explicit XPASS and merge refusal →
repair → fresh PASS and merge (PR #10: 5d108f53c58c34cff7e16a7d383d598703a2e774).
Its three retained observations were independently OpenSSL signature-verified.
The driver invokes observation explicitly; unattended execution is not proven.
Receipts: tools/dogfood/audits/2026-09-09-xpass-observer/. The 30-case real Six
audit has 25 VERIFIED and 5 GAP, not an overall PASS. Supplemental: 41 receiver
controls, 20,000 concurrent journal appends, 19 storage controls.

ADR-060 (#96): the producer evidence plane — five seams on one chain,
`verdict.py` unmoved. Measured on a real governed repository: an exit-code-only
claim already blocks on an arbitrary program; advisory evidence is recorded in
`considered` and cannot decide; a missing manifest ID fails deterministically;
and **containment inspects argv[0] only** — a system interpreter running an
in-tree script reached PASS over a violating tree (F-012 family, now a design
constraint on every scanner). A delegated worker's instructions are retained in
NO artifact — not the outcome, the ADR-043 log manifest, nor the signed
envelope (#111). MAP is 3.8.0, §6.4.

MAP §16 BUILT steps and §8.1 CONFIRMED boundaries now cite a test or receipt
(tests/contract/test_map_cites_its_evidence.py; red at 10/10 and 4/4 uncited).
CLAUDE.md and AGENTS.md are re-synced with the tree; AGENTS.md gains the lane
rule (check for another writer before writing, committing, pushing or starting
a suite) and the refreeze rule (load a frozen manifest before committing it).
Three sessions wrote this host today; both collisions were lane failures.

Next, in order — milestone 8 (#113, #110, #111, #112, #114, #115), milestone 7
(#107 approver authentication, #108 external witness, #109 observation log),
then milestone 6's remainder (#95, #97, #100, #102, #105).

Remaining audit boundaries: same-subject evidence reuse, hostile report
producers (F-012), unanchored journal verification. F-005 (#93, ADR-057):
signed v2 verdict anchors detect truncation; no independent witness protects an
operator controlling both signing keys.
UNIMPLEMENTED: isolated observer scheduling, merge-candidate/group checks,
shard aggregation, policy compiler/catalog, DSSE/in-toto attestations,
compliance coverage, external journal witness.
UNVERIFIED: production hosting, soak, credential rotation, backup/restore,
foreign same-name check availability, external-harness acceptance.
Serialise full suites on this host; concurrent runs have exhausted its memory.
