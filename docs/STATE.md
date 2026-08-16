# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-17 (session close)
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
Frozen manifest: 1179 IDs / 115 expected skips. The TypeScript mirror merged in
`ranex-harness` `ranex-trim` at `16bf036f` (vectors SHA-256 `9efa0baf…`,
byte-identical, 35/35), closing #12.

## Next

SLICE-036 (#19) is the next planned slice. Prerequisites #12–#16 are closed;
#18 is open but kernel-side done. Owner decision: re-pin Arxic after its
reference-auth-app suite is fixed upstream, or accept the recorded BLOCKED
evidence and proceed per tracker governance. SLICE-036 must implement the
journal CAS/atomic-append and event-wiring contract documented on
`SpecificationEvent` (`src/ranex/governed_execution/domain/specification_events.py`)
and close the duplicate-issuance/ancestry guarantees already enforced domain-side.

## Known limits

- SLICE-046/047 host-gated skips remain declared.
- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- Controller same-uid trust follow-ups remain.
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; it passes isolated and on `origin/main`.
- mutmut is advisory and was not run this session.
- SLICE-035 Arxic reference-auth-app process gate is BLOCKED at pinned `135991d9` (subject behavior; Arxic #109).
- About 125 legacy test IDs remain unregistered in the frozen manifest (pre-existing and deliberately not swept by slice registrations).
