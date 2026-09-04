# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (v0.1.0 release-documentation pass; suite green)
**Active slice:** none

## Where we stopped

Docs-only pass for the v0.1.0 tag: README restructured (what Ranex is,
who it is for, use cases) plus a Benchmarks-and-proofs section sourced
entirely from committed artifacts — proof board 43/43 (5 open findings
published), trainer 733 examples / 683 graded / 50 skips / 0 divergences,
external v0.1.0-on-six proof (PASS, stale attack refused exit 1, twice),
pile 19 entries / 0 false passes / 3-of-3 attacks caught, and the
six-id timing table. GitHub repo description updated to v0.1.0 wording.
No kernel, contract, or artifact numbers changed.

Both proof regimes remain green: TRAINER (104 VulcanBench tasks x 7
variants + six@c8e39406 5/5, 0 divergences; 183 exclusions classified;
passes digest-chained) and EXTERNAL PROOF (released tag on clean six,
tree-digest equality, run -> PASS -> journal verified; stale-evidence
attack refused, reproduced twice).

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
