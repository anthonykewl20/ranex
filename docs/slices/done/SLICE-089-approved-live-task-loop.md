# SLICE-089 — Approved live acceptance task loop

**Status:** done
**Issue:** #119
**ADR:** docs/adr/ADR-061-live-acceptance-before-completion.md

## Contract

An operator signs an independently pinned frozen A/B probe bundle and worker
profile. Existing C approval issuance, grants, journal CAS, the pure verdict
and signed v2 publication govern the task. The controller state is external,
private and locked per task; separate tasks may execute concurrently.

`specification approve-task` initializes authority. `build-task` launches the
pinned local Docker worker with a read-only verified Git subject and writable
approved product directories. Worker keys, controller state and the Docker
socket are not mounted. Output links, special files, Git controls and excessive
copy size are refused. Image-declared volumes are masked with bounded read-only
tmpfs after a real receipt exposed an inherited writable anonymous volume.
Only the controller creates the candidate commit.

`ranex prove --task PATH` runs fresh calibrated HTTP observations and evaluates
that exact commit. Only observed mismatches consume misses. Three persisted
misses revoke the grant; further attempts refuse before observing. Infrastructure
and calibration failures do not become PASS. `reapprove-task` requires the same
operator, a strictly newer map and fresh frozen bundle, preserves prior history
and issues a new C at the existing journal head. It does not erase old misses.

`land-task` requires the latest completed live PASS, matching receipt and
candidate, product scope, an unchanged target base and a clean target checkout.
An expected-old Git ref update integrates that exact candidate, followed by
checkout synchronization. Duplicate integration refuses. A synchronization or
interrupted journal/publication failure needs explicit operator recovery and
never silently reports success.

## Real qualification

`tools/dogfood/acceptance_task_proof.py --output NEW_EXTERNAL_DIR` runs public
CLI subprocesses, a pinned SQL-writing worker, real PostgreSQL and PostgREST.
It retains three tenant-isolation misses, fourth-attempt refusal, reapproval,
calibrated PASS, exact integration, repeated-integration refusal, stale-candidate
and moved-target refusal. The worker attempts frozen-file and out-of-scope
writes and a cross-mount hardlink. This is a deterministic harness fixture,
not qualification of a full AI harness. Optional integration tests must run
explicitly with RANEX_LIVE_TASK_EXPERIMENT=1; their default skip proves nothing.

## Boundaries

The host, Docker daemon and controller installation are trusted. This initial
profile supports Linux/PostgREST SQL applications and local immutable images.
It does not assert that arbitrary agents, browsers, production deployments or
unstated requirements have been qualified. Network-enabled workers receive
explicit broad network authority. Worker environment values are not passed to
the host Docker client's environment or retained in command/inspection logs.
No runtime dependency or verdict.py change. Final committed-tree manifest and
full-suite evidence remain required before this slice closes.

Combined committed-tree freeze at 31a63334: 1873 passed, 162 skipped; 2035 IDs
and 170 expected skips, run_exit=0. The later inherited-volume fix is separately
qualified by 7 live CLI tests in 49.72s. Final full-suite evidence is recorded
in the closing issue comment; no release claim precedes that result.

Four concurrent public prove processes also recorded exactly three misses and
one revocation refusal, followed by successful reapproval and exact integration.
The parallel-prove audit retains actual subprocess results and journal bytes.
