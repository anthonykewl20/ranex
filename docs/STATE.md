# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-05
**Phase:** SLICE-009 closed, merged to main, pushed. CI green — the first
green run since 2026-08-03.
**Active slice:** none

## Where we stopped

SLICE-009 landed: the gauge measures test identity now; a skip is absence
unless ceremony-declared. Two hermeticity holes found by running the product
on itself were fixed the same day: an ancestor `.venv` capturing provisioned
runs (`VIRTUAL_ENV` now pinned to the verified deps environment), and
machine-level git config reaching the observed tree (the runner image's
git-lfs filters; `GIT_CONFIG_NOSYSTEM`/`GIT_ATTR_NOSYSTEM` now ride every
hermetic environment and materialisation git call — this was the whole of
the CI red). Mutation policy is now kernel-scoped, cached, advisory
(pyproject `[tool.mutmut]`; survivors are review input, never a blocker).

## Next

1. The merge ADR: kernel-side digest re-check at merge time (ADR-010 names
   it), deferred behind the gauge fix on purpose. Research before design.
2. The rest of MAP §4.6: entry-point-observed spawning, `tests-executed` vs
   `product-exercised` as distinct claims, assertion strength.

## Known limits

- The delegated loop can exfiltrate the model credential; use a scoped,
  spend-limited key (ADR-010 s.p. 13). RISK-06 remains open for `ranex run`.
- `approver_id` is unauthenticated (RISK-07).
- Same-task-id dispatch has a TOCTOU window; the earlier racer dies at the
  cross-check.
- Dependencies are trusted computing base (ADR-007).
- The journal detects an edited row, not a removed one.
- A hostile tree can forge the suite artifact (criterion 10's passing test
  states the boundary).
- The 67 declared expected-skips are permission, not obligation; the manifest
  holds 737 IDs and re-freezing is the only way in.
- The full suite takes about six minutes; mutation re-baselining ~15.
