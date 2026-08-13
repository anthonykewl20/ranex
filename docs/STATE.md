# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-13
**Active slice:** `docs/slices/SLICE-018-confinement-session-lifecycle.md`.

## Where we stopped

SLICE-018 is open for the cgroup/namespace/bounded-output lifecycle under
ADR-006. Its contract is frozen in two new security/integration files and must
remain red until implementation. It depends on the shipped SLICE-017 qualified
artifact and exposes no `cmd_run` or signing path.

## Next

Implement only SLICE-018's exact owned paths against the frozen tests. Do not
change the frozen tests, bind `cmd_run`, sign a result, accept ADR-006, or close
RISK-06.

## Known limits

- The cgroup-observer test still flakes with `OSError(19)` under load; unfixed.
- Real qualification e2e skips on hosts without delegated cgroup `cpu`, as
  declared in the manifest.
- `mutmut` did not complete for this slice because the SLICE-017 copy-repo test
  environment crashed. This is advisory/non-blocking and remains unverified.
