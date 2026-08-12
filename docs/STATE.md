# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-12
**Active slice:** docs/slices/SLICE-019-host-qualification-as-gate-evidence.md.

## Where we stopped

SLICE-017 is closed. ADR-021 is accepted after consensus-luna and
consensus-terra returned APPROVE on the prior-art-corrected `69fd9db12f`.
SLICE-019 is open for ADR-021 integration only. QA-gate found the real `cmd_run`
operator path could not capture the qualification report and that admission's
closed schema checked keys but not confinement value content. Owner chose the
full fix: the revised frozen-red contract adds loader-bound
`qualification_report` capture, deep grammar/non-emptiness validation, reuses
`ranex-evidence-v3`, and keeps the verdict kernel byte-exact.

## Next

1. Implement the frozen-red SLICE-019 contract and close without changing
   `verdict.py` or `host_confinement.py`.
2. Open the ADR-019/020 kernel slice for judgment identity and the
   `self_approval` wire.
3. Then open SLICE-018/029; SLICE-029..044 open strictly one at a time.
   SLICE-036 only qualifies an approved batch in disposable child worktrees
   with publication blocked. SLICE-037..042 close the harness effect families;
   SLICE-043 serially integrates every leaf and CAS seam. SLICE-044 alone
   authorizes production mutation fanout, after two real repository/provider
   journeys plus a concurrent-attack exit. (ADR-017 Confirmation; MAP §0.26)

## Known limits

- **The materialised suite is not fully deterministic** — a SLICE-017
  cgroup-inotify test flaked once under load and remains unfixed.
- **Running the harness commits its tree on idle** (`plugin/ranex.ts`).
- **Parallel work today:** allowed now are bounded read-only research/review
  fanout (children read evidence, cannot mutate files/refs/external state, and
  receive no secret) and the kernel/harness lanes running in parallel (the
  harness is out-of-tree at `../ranex-harness`). Forbidden now is parallel
  mutation fanout (multiple concurrent writers / parallel open slices) until
  SLICE-044's exit; today's `task fanout` is free-prompt JSONL prototype
  mechanics, not authorization.
