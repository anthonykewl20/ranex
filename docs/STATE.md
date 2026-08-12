# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-13
**Active slice:** docs/slices/SLICE-019-host-qualification-as-gate-evidence.md.

## Where we stopped

SLICE-019 (ADR-021 host-qualification integration) is open and nearly done. The
owner landed `cmd_run` qualification-report capture, deep admission schema
validation, the `MAIN_PY_SHA256` pin refresh, and a host-only skip for journeys
needing a qualified host. Targeted admission + manifest tests pass; the
host-only-skip paths are the remaining loose end. ADR-019/020 stay `proposed`:
consensus-cleared, with owner decisions recorded — extend harness `verdict.ts`
for Record `self_approval` + Rejection `producer_id` (kernel-first), and a
dedicated `kernel-verdict-signer` under `ranex-verdict-v1`.

A premature close-SLICE-019/open-SLICE-020 merge was reverted (`3c7d97252`,
`05519567c`): the slice's done-criteria were not yet met. Do not merge a
spec-prd that closes a slice before its gates are green.

## Preserved for SLICE-020 (ready when SLICE-019 closes)

Branch `agent/slice020-impl` (worktree `ranex-wt-020`, tip `8e9fbcf46`) holds a
COMPLETE verified-green SLICE-020: spec-prd (slice + ADR-019/020 accepted) AND
implementation — `_diagnosis`→structured causes, `Evaluation.causes`/
`self_approval`, third signing domain, projection/publication/reader, atomic-
writer extracted from `host_confinement.py`, dedicated signer. Full suite 959
passed; KERNEL_DIGEST moved (aa753cae→6bde8574) with reason/stdout unchanged;
no `src/` import of `host_confinement.py`. Rebase onto main once SLICE-019
closes, re-run the full suite, then merge.

## Next

1. Finish SLICE-019's host-only-skip paths; close by done-criteria, not a merge.
2. Rebase + merge `agent/slice020-impl`; open SLICE-020 from the preserved branch.
3. Then SLICE-018/029; SLICE-029..044 strictly one at a time (ADR-017; MAP §0.26).

## Known limits

- The materialised suite is not fully deterministic — a SLICE-017 cgroup-inotify
  test flaked once under load and remains unfixed.
- Running the harness commits its tree on idle (`plugin/ranex.ts`).
- Owner-implemented work outpaces codex delegations; this session's parallel
  value was read-only gates (consensus panels + the SLICE-020 blueprint).
- Parallel mutation fanout stays forbidden until SLICE-044's exit; `task fanout`
  is free-prompt JSONL prototype mechanics, not authorization.
