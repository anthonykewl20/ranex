# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** SLICE-006 unparked — Ranex learns to gate a real test suite.
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md` (ADR-007,
now accepted).

## Where we stopped

Owner decided 2026-08-04: unpark SLICE-006 over opening first-delegation. The
slice file is restored from `bbb74c015f` unchanged except the unpark note;
ADR-007 flipped to accepted. Work order inside the slice: red tests first
(prove the clean room cannot resolve `uv`/`pytest`, prove `uv lock --check`
accepts a fabricated hash), then provisioning service, store, root assembly,
approval delta, and the criterion-14 self-gate.

SLICE-007 remains closed: fork built on `ranex-trim` in sibling `ranex-harness`,
bridged, gear-mesh e2e green. Suite baseline: 355 passed.

## Next

1. Finish SLICE-006 — 15 criteria; criterion 14 (Ranex gates its own repo
   through the unchanged `uv run pytest -q`) is the one that matters.
2. The `§17.4` horsepower/fuel baseline is still unmeasured — carry it into the
   next fork-facing slice, not this one.
3. Handbooks unstarted. `RISK-06` and `RISK-07` remain open.

## Known limits

- `ranex-harness` is a local sibling clone; machines without it skip its 21
  fork tests loudly (CI prints the skips via `-rs`).
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`);
  confinement (`ADR-006`) unbuilt and deliberately deferred.
- The journal detects an edited row but not a removed one.
- Host `uv` is user-writable at `~/.local/bin/uv` — exactly what this slice
  refuses to trust; the resolver must be operator-pinned.
- The trim must stay rebaseable; every upstream release costs a measured rebase.
