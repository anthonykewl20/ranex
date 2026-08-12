# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-12
**Active slice:** docs/slices/SLICE-020-judgment-identity-and-verdict-read-channel.md.

## Where we stopped

SLICE-019 is closed. The full frozen suite was green at `028957002`: host
qualification now travels through ordinary signed evidence, is deeply validated
by shared admission, and blocks both judgment paths when absent or stale.
ADR-019 and ADR-020 are accepted after owner-locked consensus. SLICE-020 is open
for their single kernel-first result: structured judgment identity and a signed,
atomic verdict read channel whose wire contract the harness will consume later.

## Next

1. Implement SLICE-020 against its frozen-red tests without editing them.
2. Move `KERNEL_DIGEST` in the implementation commit and argue the deliberate
   one-way kernel and `ranex-verdict-v1` signing-domain boundaries.
3. Extend the harness `verdict.ts` only after the kernel contract lands.
4. Then open SLICE-018/029; SLICE-029..044 open strictly one at a time.
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
