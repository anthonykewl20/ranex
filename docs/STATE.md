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

## Known limits

- **The materialised suite is not fully deterministic** — a SLICE-017
  cgroup-inotify test flaked once under load and remains unfixed.
- **Running the harness commits its tree on idle** (`plugin/ranex.ts`).
