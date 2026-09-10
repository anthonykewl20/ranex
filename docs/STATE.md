# State

**Updated:** 2026-09-10
**Active slice:** [docs/slices/SLICE-085-github-app-production-registration.md](slices/SLICE-085-github-app-production-registration.md)

Version v0.1.006. Open: #88 production readiness and #90 dogfood publication.
No production sign-off or zero-bug claim is issued. Slice 086's receiver pins
operator policy, judges the exact PR SHA and publishes a verified verdict,
never running contributor code.

Suite: 2001 tests, 168 expected skips, ceremony `run_exit=0` (2026-09-10).
A refreeze runs the freeze journey's own recipe — clone the committed tree,
fresh HOME, `deps fetch` + `deps approve`, then `suite freeze` over the pinned
pytest argv — and takes about ten minutes here, not the hour once budgeted.

Lanes — `tools/dogfood/lane.py`. The dogfood loop, verification suites and the
soak campaign run here at once, and the first two cannot share a checkout: the
loop writes `backlog.json` and `iterations/` by design, and both the freeze
journey and `ranex run` refuse a dirty tree. A `verify` lane leases a worktree
at a pinned commit; every lane takes a slot from a memory-sized host semaphore.
An acquire REFUSES rather than warning, and a holder is pid AND boot id, so an
OOM kill self-heals. Run every suite and ceremony through it —
`lane.py run --kind verify -- <cmd>`. It replaces pattern-matching on `ps`,
which failed three ways in one evening.

#97 landed — `sarif-2.1.0`, the evidence plane's first non-JUnit producer
(ADR-060 seams A/B/C; MAP §6.4). A scan claim names its own frozen manifest
(`scope`, `rules`, `blocking_levels`, `accepted`), pinned in `run`, `gate
evaluate` and the App receiver. A blocking finding fails the scope path
carrying it — an ID nobody could freeze is one `evaluate()` would skip — and
the finding ID rides beside it, signed. Regions are checked against the
materialised subject, so a forged region is refused and absence blocks. Two
boundaries recorded, not closed: ruff 0.16.2 emits no coverage witness, so a
scanner exiting 0 having read nothing is caught by its exit code alone; and
`Evidence.satisfies` wants exit 0 first, so `accepted` is reachable only under
a `--exit-zero` argv. Receipt: tools/dogfood/audits/2026-09-10-sarif-reporter/.

Next, in order — milestone 8 (#113, #110, #111, #112, #114, #115), milestone 7
(#107 approver auth, #108 witness, #109 observation log), then milestone 6's
remainder (#100, #102, #105, #106).

Remaining boundaries: same-subject evidence reuse, hostile report producers
(F-012 — narrowed for scanners by region validation, open elsewhere),
unanchored journal verification. F-005 (#93, ADR-057): signed v2 anchors detect
truncation; no witness protects an operator holding both keys.
UNIMPLEMENTED: isolated observer scheduling, merge-group checks, shard
aggregation, policy compiler/catalog, DSSE/in-toto attestations, external
journal witness. UNVERIFIED: production hosting, soak, credential rotation,
backup/restore, foreign same-name check availability, external-harness
acceptance. The 30-case Six audit stands at 25 VERIFIED and 5 GAP.
