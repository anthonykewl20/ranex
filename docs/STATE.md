# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-03 (#74 and #69 fixed)
**Active slice:** none

## Where we stopped

Issue #74 FIXED, closing evidence posting: the strict-local session's
cgroup mutations (worker-cgroup create at setup, controller-leaf
release at teardown) now acquire `_host_probe_lock()` at the call
sites — never inside the shared helpers, which the qualified probe
calls under the same lock (self-deadlock; ADR-046 addendum). Frozen
red 720aca208 (a real session completed both mutations under a held
lock, three consecutive reproductions), fix 9e9c0a701 (zero test-byte
edits between), suite re-frozen and sealed green at **1655 IDs / 166
expected skips** (run_exit=0). Earlier tonight: docs cap admitted the
dogfood interface docs; the libc-bin loader-cache drift re-pinned with
the host profile re-bound and the approved-batch vectors regenerated
(v19); the freeze golden's byte format restored.

## Next

#68 (recovery stale-worktree detection, detached mid-sync window);
then umbrella #66 (release gate, v0.1.0). #69 FIXED: suite_tail drops
designed-red canary lines so a nested red names its victim; stability
evidenced by consecutive full-suite greens at 1655 and 1656 IDs.

## Governance

ADR-038: preserve epoch discipline—deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per
ADR-009 and refuses governed subcommands outside its containing checkout.
ADR-039: coverage floor 64 comes from the enforcing pipeline; confinement-only
lines carry the pragma convention. Governed self-gate note: the `anthony`
producer key is absent from this host; the sealed freeze is the proof.

## Known limits

- Version stays 0.0.0 until the release-gate slice (#66).
- Strict-local requires a delegated cgroup scope; the `ranex host
  strict-local` wrapper establishes it, and the controller remains
  same-UID trusted infrastructure (ADR-044).
- Session cgroup mutations are serialized per-host-scope only against
  probes taking the same lock; cross-batch locking remains journal
  discipline (ADR-046 scope).
- `mutmut` remains an UNVERIFIED residual: no negative control or
  consuming gate (MAP §1.5).
- The concurrent-CAS journal race family is documented, not fixed;
  verification cannot detect snapshot replacement (RISK-19 adjacent).
