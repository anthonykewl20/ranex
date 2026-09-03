# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (trainer clean pass 733/733; v0.1.0 proven externally)
**Active slice:** tools/dogfood trainer — corpus-driven, automatically graded

## Where we stopped

Two regimes completed in parallel. (1) The TRAINER
(`tools/dogfood/trainer/`) reached a CLEAN PASS: 104 VulcanBench tasks x 7
labelled variants (gold/empty/delete-tests/goalpost-move/partial-gold/
manifest-swap/manifest-crossbind) = 728 examples, 0 divergences, plus the
GitHub source (six@c8e39406) at 5/5 — every automatically-derived label
matched the real gate verdict. Labels are sound by preflight: suite must
collect under a CONFINEMENT-equivalent env and gold must be green there;
exclusions are classified, never silent (95 toolchain-unpinned, 28
preflight-failed, 15 gold-not-green, 10 governance-env-unsupported — ranex
run strips the child env, so PYTHONPATH-importing tests cannot be governed
yet, 32 diff-graded, 3 cmd-unparseable). Passes chain by digest in
training/passes/; coverage.json maps the AUDIT-2026-09-03 input classes
(all former zero-coverage classes now trained 93-169x). (2) v0.1.0 (tag
edf1a98605) has external proof via `tools/dogfood/external_proof.py`: the
released tag alone governed a clean third-party repo (six, MIT) end to
end — run -> gate PASS -> journal verified — and refused the published
stale-evidence attack (exit 1); reproduced identically twice; pile 0010/0011.

## Next

More permissively-licensed external repos (non-Python once a toolchain
pins at /usr/bin); design governed env-file support (the 10
governance-env-unsupported tasks are its acceptance test); close F-004
with an owner decision; anchor the journal head and add
full-rewrite/truncation scenarios; promote audit survivors (M01/M04/M06/
M08/M17/M18) into scenario pins; keep claims interval-honest.

## Governance

ADR-038: deliberate re-locks and builds pass `--exclude-newer
2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per ADR-009.
ADR-039: coverage floor 64 comes from the enforcing pipeline. The
`anthony` producer key is absent from this host; the sealed freeze is
the proof.

## Known limits

- Trainer labels are host-relative: gold-not-green tasks are excluded,
  not failed — re-preflight after host changes. The trainer trains the
  WORKING TREE kernel; external_proof trains the released tag.
- External proof needs system pytest for /usr/bin/python3 (F-003,
  mitigated 2026-09-04: documented + scripted) and network for clone/sync.
- Kernel-only, source-run (ADR-009); strict-local needs a delegated cgroup
  scope (ADR-044); cross-batch locking remains journal discipline (ADR-046).
- `mutmut` remains UNVERIFIED as a gate; the audit's 18-mutant battery is
  the negative control (7/18 killed, survivors named in the audit).
- No journal head anchor yet: full-chain rewrite or tail truncation stays
  undetectable (AUDIT A-01/A-02, RISK-19 adjacent).
