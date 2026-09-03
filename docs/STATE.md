# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (multi-agent review round complete; all green)
**Active slice:** none

## Where we stopped

Two regimes, both green. (1) The TRAINER clean pass: 104 VulcanBench
tasks x 7 labelled variants + the GitHub source (six@c8e39406) 5/5 — 0
divergences; labels sound by preflight (confinement-equivalent
collection, gold green); exclusions classified (95 toolchain-unpinned,
28 preflight-failed, 15 gold-not-green, 10 governance-env-unsupported,
32 diff-graded, 3 cmd-unparseable); passes digest-chained. (2) EXTERNAL PROOF, sources now committed:
`tools/dogfood/external_proof.py` ran the released v0.1.0 tag alone on a
clean third-party repo (six, MIT) — tag checkout + `uv sync --frozen`,
vendored src tree-digest == `<tag>:src`, run -> gate PASS -> journal
verified — and refused the published stale-evidence attack (one edit
after green evidence, no re-run: FAIL `evidence bound to a different
subject digest`, exit 1; re-run -> PASS); reproduced identically twice.
Pile 0010/0011; renderer + pile contract carry the agentless entries.
Review round (2026-09-04, three independent agents + re-runs): ledger-data
audit zero anomalies; docs reconciled to audited numbers; mutation battery
v2 over the 43-scenario suite kills 12/18 (was 7/18 — the formal/grid
additions killed M04/M08/M10/M15); trainer reproducibility 84/84 rows
identical; adversarial review produced six label-soundness fixes, now
landed (pristine-red gate, no-gold class, manifest-covers-ids assertion
with the kernel's class-id spelling, exact governed-env mirror,
delete-by-manifest-id, byte-preserving patch slicing) — preflight set
unchanged at 104 ok; two pile-dependent scenario invariants repaired.

## Next

More permissively-licensed external repos (non-Python once a toolchain
pins at /usr/bin); design governed env-file support (the 10
governance-env-unsupported tasks are its acceptance test); close F-004
with an owner decision; anchor the journal head; promote audit survivors
(M01/M04/M06/M08/M17/M18) into scenario pins; keep claims interval-honest.

## Governance

ADR-038: deliberate re-locks and builds pass `--exclude-newer
2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per ADR-009.
ADR-039: coverage floor 64 comes from the enforcing pipeline. The
`anthony` producer key is absent from this host; the freeze is the proof.

## Known limits

- Trainer labels are host-relative: gold-not-green tasks are excluded,
  not failed. The trainer trains the WORKING TREE kernel;
  external_proof trains the released tag.
- External proof needs system pytest for /usr/bin/python3 (F-003,
  mitigated 2026-09-04: documented + scripted) and network for clone/sync.
- Kernel-only, source-run (ADR-009); strict-local needs a delegated cgroup
  scope (ADR-044); cross-batch locking is journal discipline (ADR-046).
- `mutmut` remains UNVERIFIED; the audit's 18-mutant battery is the
  negative control (12/18 killed by the 43-scenario suite; survivors
  M01/M06/M09/M14/M17 need pins, M16 is equivalent).
- No journal head anchor yet: full-chain rewrite or tail truncation stays
  undetectable (AUDIT A-01/A-02, RISK-19 adjacent).
