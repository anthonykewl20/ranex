# SLICE-102 — Approved live acceptance task loop

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
tmpfs. Only the controller creates the candidate commit.

`ranex prove --task PATH` runs fresh calibrated HTTP observations and evaluates
that exact commit. Only observed mismatches consume misses. Three persisted
misses revoke the grant; further attempts refuse before observing. Infrastructure
and calibration failures do not become PASS. `reapprove-task` requires the same
operator, a strictly newer map and fresh frozen bundle, preserves prior history
and issues a new C at the existing journal head. It does not erase old misses.

`land-task` requires the latest completed live PASS, matching receipt and
candidate, product scope, an unchanged target base and a clean target checkout.
An expected-old Git ref update integrates that exact candidate, followed by
checkout synchronization. Duplicate integration refuses.

## Real qualification

`tools/dogfood/acceptance_task_proof.py --output NEW_EXTERNAL_DIR` runs public
CLI subprocesses, a pinned SQL-writing worker, real PostgreSQL and PostgREST.
Receipts: `tools/dogfood/audits/2026-09-30-acceptance-task-loop/` with #95
vocabulary (VERIFIED · GAP · FALSE-PASS · NON-DETERMINISTIC · UNVERIFIED).
Positive and negative controls: three tenant-isolation misses, fourth-attempt
revocation, reapproval, calibrated PASS, exact integration, stale-candidate,
moved-target and duplicate-land refusals. Three deterministic repeats retained
identical product/controller/case digests. Optional suite arms require
`RANEX_LIVE_TASK_EXPERIMENT=1`; a default skip proves nothing.

## Boundaries

The host, Docker daemon and controller installation are trusted. This initial
profile supports Linux/PostgREST SQL applications and local immutable images.
It does not assert that arbitrary agents, browsers, production deployments or
unstated requirements have been qualified. No runtime dependency or verdict.py
change. Remaining ADR-061 exits (browser/release) keep their own requirements.
