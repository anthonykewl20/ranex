# State

**Updated:** 2026-09-12
**Active slice:** docs/slices/SLICE-089-approved-live-task-loop.md (#119).

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the program and trust boundaries. No universal bug-free claim.

SLICE-087 / #116 shipped external A/B-bound executable probe bundles. A known
bad journal verifier passes 499 unit tests but fails the frozen live probe;
three baseline matches and three named mutant failures are retained in
tools/dogfood/audits/2026-09-12-probe-bundles/.

SLICE-088 / #118 implements the trusted declarative PostgREST/PostgreSQL
observer. Real CLI qualification: 12 passed, including mutation calibration
and surviving/unrelated-control refusal. Final regression exposed a network
probe that checked one CDN address; it now tries all resolved addresses.
Full final verification is pending. No release claim precedes its result.

SLICE-089 composes existing signed C, grants, journal CAS and pure verdict.
Public commands: approve-task, build-task, ranex prove, reapprove-task,
land-task. Private per-task authority, scoped Docker worker, fresh observations,
three persisted misses, explicit new-revision approval and exact Git integration.
Real fixture produced misses 1/2/3, refusal on attempt 4, reapproval, calibrated
PASS and matching integration; stale candidates and moved targets refuse.
Worker is a deterministic SQL-writing fixture, not a qualified AI harness.
Manifest refreeze and final full suite remain required before closing #119.

SLICE-085 / #88 production registration remains parked under the owner pivot.
Next work: real AI harnesses, broader application/browser journeys, production
integration and fault/recovery qualification against retained real outputs.

Parallel work and overlapping verification are owner-authorized (2026-09-12).
Use separate writer and pinned verification worktrees. The lane helper admits
two verification runs with memory checks and persistent admission locking.
The parallel-lane race fixes from main are included. Refreeze on a committed tree and
load_manifest before committing the manifest. Do not claim skipped runs passed.

Trust boundaries: controller/host/Docker daemon trusted; PostgREST SQL profile
only. Interrupted publication or checkout synchronization fails closed and
needs operator recovery. Native host repinning was an external experiment,
not a tracked production-pin change. No zero-bug or universal-runtime claim.
