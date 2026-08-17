# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-17 (governance session)
**Active slice:** none.

## Where we stopped

All six kernel slices of the P0 spec-authority program landed on `main` at `ff3ab802`.
- SLICE-029 — A/B/C contracts, error registry, and vectors.
- SLICE-030 — lifecycle to `APPROVAL_PENDING`.
- SLICE-031 — closed-DSL generator and projections.
- SLICE-032 — approval, revocation, and intersected grants.
- SLICE-033 — trace integrity and verifier ports.
- SLICE-035 — real-subject bootstrap.

Full suite: 1117 passed / 62 skipped / 0 failed under the absent-harness config.
Frozen manifest: 1179 IDs / 115 expected skips. The `ranex-harness` TypeScript
mirror merged `ranex-trim` at `16bf036f` (vectors SHA-256 `9efa0baf…`, 35/35), closing #12.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: the milestone-4 real-world verification &
observability program is P0's proof substrate, built first — dependency
order, not a competing priority. Milestone-4 tracker #33 carries
SLICE-054..059 (#34-#39); M2/M3 issues are gated (`dependency-gated` labels
+ blocked-by edges). SLICE-048 stays reserved (ADR-024); P0 stays primary.

## Next

SLICE-054 (#34) is next; its Phase-0 ADR is the first work item. Then
SLICE-055 (#35), then SLICE-036 (#19) per ADR-017 — prerequisite SLICE-034
(#17) must close first, already true. #18 stays open pending the owner's
Arxic decision: re-pin after the upstream reference-auth-app suite is fixed,
or accept the recorded BLOCKED evidence per tracker governance. SLICE-036
must implement the journal CAS/atomic-append and event-wiring contract on
`SpecificationEvent` (`src/ranex/governed_execution/domain/specification_events.py`).

## Known limits

- SLICE-046/047 host-gated skips remain declared.
- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- Controller same-uid trust follow-ups remain.
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; it passes isolated and on `origin/main`.
- mutmut is advisory and was not run this session.
- SLICE-035 Arxic reference-auth-app process gate is BLOCKED at pinned `135991d9` (subject behavior; Arxic #109).
- About 125 legacy test IDs remain unregistered in the frozen manifest (pre-existing and deliberately not swept by slice registrations).
