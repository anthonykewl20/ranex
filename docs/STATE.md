# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-03
**Phase:** ADR-008 accepted; fork slice open.
**Active slice:** `docs/slices/SLICE-007-trimmed-fork-to-the-kernel.md`

## Where we stopped

**ADR-008 is accepted** and named the fork work: pin `v1.18.11` (`012c2f57f9`),
trim the keep-set, and bridge the harness to the kernel through
commit-then-materialise. The bridge slice is open and `SLICE-006` is parked
behind it, recoverable from git history.

## Next

1. Build the trimmed fork and wire it to the kernel in `SLICE-007`
   (`§17.5` gear-mesh run: dispatch → loop → hooks → kernel judgement → journal,
   ending in evidence and `CANDIDATE`).
2. Then first delegation, then handbooks.
3. Keep `SLICE-006` parked until unblocked by owner; `RISK-06` and `RISK-07`
   remain open.

## Known limits

- The trim must stay rebaseable and continue to build at the pinned commit.
- Confinement (`ADR-006`) and approver authentication (`RISK-07`) are not in this
  slice.
- `approver_id` unauthenticated; same-uid key theft (`RISK-06`) stays open.
- The journal detects an edited row but not a removed one.
