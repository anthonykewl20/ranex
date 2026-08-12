# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-12
**Active slice:** none.

## Where we stopped

SLICE-017 is formally closed this session after its QA gate passed green ×3 on
`dc7f9fe8d`. The next step is to open SLICE-019 once ADR-021 clears the
ADR-019/020/021 consensus panel.

## Next

1. Complete the ADR-019/020/021 consensus panel now in flight.
2. Open SLICE-019 for ADR-021 integration: the qualification claim in
   `gates.yaml` and the kernel refusal rule.
3. Then open the ADR-019/020 kernel slice.
4. After SLICE-019 closes, SLICE-029..044 open strictly one at a time.
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
