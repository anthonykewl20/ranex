# State

**Updated:** 2026-09-09
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open: #88 production readiness and #90 dogfood publication.
No production sign-off or zero-bug claim is issued.
Slice 086: `github listen --evaluate-evidence` pins operator policy, judges the
exact PR SHA, verifies the signed verdict and publishes, never running
contributor code. Late evidence refreshes every 15s; failures reconcile.

F-010 (#94, ADR-059): the controller supplies the canonical pytest reporter.
Explicit strict=False XPASS is retained as xpassed and blocks acceptance.
Missing/disabled reporting refuses observation; nested activation is isolated;
pytest-xdist 3.8.0 workers preserve XPASS centrally.

Real GitHub PRs #7-#10 in anthonykewl20/ranex-app-live-probe ran refusal → Six
PASS → XPASS refusal → repair → merge (PR #10: 5d108f53c); the three retained
observations were independently OpenSSL signature-verified. The driver invokes
observation explicitly; unattended execution is not proven. Receipts:
tools/dogfood/audits/2026-09-09-xpass-observer/. The 30-case Six audit has 25
VERIFIED and 5 GAP, not an overall PASS.

ADR-060 (#96): the producer evidence plane — five seams, one chain,
`verdict.py` unmoved. Measured on a real governed repository: an exit-code-only
claim already blocks on an arbitrary program; advisory evidence is recorded and
cannot decide; a missing manifest ID fails deterministically; and **containment
inspects argv[0] only** — a system interpreter running an in-tree script
reached PASS over a violating tree (F-012 family, now a constraint on every
scanner). A delegated worker's instructions are retained in NO artifact (#111).
MAP is 3.8.0, §6.4.
MAP §16 BUILT steps and §8.1 CONFIRMED boundaries now cite a test or receipt
(tests/contract/test_map_cites_its_evidence.py; red at 10/10 and 4/4 uncited).
CLAUDE.md and AGENTS.md are re-synced; AGENTS.md gains the lane rule (check for
another writer before writing, committing, pushing or starting a suite) and the
refreeze rule. Three sessions wrote this host today; both collisions were lane
failures — an uncommitted file collides exactly like a landed one.
Next, in order — milestone 8 (#113, #110, #111, #112, #114, #115), milestone 7
(#107 approver auth, #108 witness, #109 observation log), then milestone 6's
remainder (#95, #97, #100, #102, #105).

Remaining boundaries: same-subject evidence reuse, hostile report producers
(F-012), unanchored journal verification. F-005 (#93, ADR-057): signed v2
anchors detect truncation; no witness protects an operator holding both keys.
UNIMPLEMENTED: isolated observer scheduling, merge-group checks, shard
aggregation, policy compiler/catalog, DSSE/in-toto attestations, compliance
coverage, external journal witness.
UNVERIFIED: production hosting, soak, credential rotation, backup/restore,
foreign same-name check availability, external-harness acceptance. Serialise
full suites here; concurrent runs have exhausted this host's memory.
