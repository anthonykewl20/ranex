# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (multi-agent review round complete; all green)
**Active slice:** none

## Where we stopped

Two regimes, both green. (1) TRAINER clean pass: 104 VulcanBench tasks x
7 labelled variants + GitHub six@c8e39406 5/5 — 0 divergences; labels
sound by confinement-equivalent preflight; 183 exclusions classified;
passes digest-chained. (2) EXTERNAL PROOF
(`tools/dogfood/external_proof.py`): released v0.1.0 tag alone on clean
six (MIT) — vendored src tree-digest == `<tag>:src`, run -> gate PASS
-> journal verified; stale-evidence attack refused (edit after green,
no re-run: FAIL `evidence bound to a different subject digest`, exit
1; re-run -> PASS); reproduced twice. Pile 0010/0011; renderer/pile
contract carries agentless entries. Review round (three agents +
re-runs): ledger zero anomalies; docs reconciled to audited numbers
(683 graded/50 skips/0 diverge; F-004 23+5; 66-169x class range);
mutation battery v2 kills 12/18 (was 7/18); reproducibility 84/84; six
label-soundness fixes from adversarial review landed; preflight
unchanged at 104 ok; two pile-dependent invariants repaired.

## Next

More permissively-licensed external repos (non-Python once a toolchain
pins at /usr/bin); governed env-file design (the 10 env-unsupported
tasks are its acceptance test); close F-004 (owner decision); anchor
the journal head; promote audit survivors (M01/M04/M06/M08/M17/M18)
into scenario pins; keep claims interval-honest.

## Governance

ADR-038: deliberate re-locks pass `--exclude-newer
2026-08-04T00:00:00Z`; CLI stays checkout-anchored (ADR-009). ADR-039:
coverage floor 64 comes from the enforcing pipeline. The `anthony`
producer key is absent from this host; the freeze is the proof.

## Known limits

- Trainer labels are host-relative (gold-not-green excluded, not
  failed). Trainer trains the WORKING TREE kernel; external_proof
  trains the released tag (needs system pytest, F-003; network).
- Kernel-only, source-run (ADR-009); strict-local needs a delegated
  cgroup scope (ADR-044); cross-batch locking is journal discipline.
- `mutmut` UNVERIFIED; the 18-mutant battery is the control (survivors
  M01/M06/M09/M14/M17 need pins; M16 equivalent). No journal head
  anchor yet: full-chain rewrite or tail truncation undetectable.
