# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-11
**Active slice:** SLICE-017 — QA gate passed (green ×3 on `dc7f9fe8d`); formal close (status → `done/`) pending. Next: SLICE-019.

## Where we stopped

SLICE-017's deterministic blocker is fixed and the gate is green. The 47 gates
failed under the materialised `_deny_network` suite; `5ddaaca94` adds a
`_confined_no_delegation()` guard (empty `/proc/self/uid_map`) that makes each
affected test assert the controller's actual `E-C17-EXEC-OBJECT-DRIFT` refusal
(launcher owned by uid 65534, refused before delegation) instead of a host-only
scenario it cannot build confined (counts 26/21, no bypass tokens, host journey
unchanged). ADR-019/020/021 were corrected per the consensus panel
(`ad86ac487`: kubelet prior-art weakness fabricated, Kyverno citation overclaimed,
ADR-021's `E-C17-CGROUP-DELEGATION` premise wrong).

## Decisions

- **`gate evaluate` does not confine** — it judges evidence; the operator
  produces it. The materialised `_deny_network` run is what confines; slice017
  was its sole deterministic blocker (slice006 skips uv-less, e2e bails via
  `nested_hermetic_self_gate`).
- **ADR-021 corrected:** the refusal is `E-C17-EXEC-OBJECT-DRIFT` at
  `_open_verified` (`host_confinement.py:331`), before `_current_cgroup_root`.
  The `E-C17-CGROUP-DELEGATION` framing and "nested-unshare EPERM / category
  error" narrative were wrong and are removed.
- **ADR-019/020 corrected per consensus** (kubelet weakness, Kyverno citation,
  crash-safety/freshness gap, self-approval cause). Signing = honest-reader
  transport, not screen defense. All three stay `proposed`; none paneled.

## Next

1. Formally close SLICE-017 (status → `done/`), then open SLICE-019: ADR-021's
   integration — the qualification claim in `gates.yaml` + the kernel refusal
   rule (absence/mismatch/stale/self-approval).
2. Then the ADR-019 + ADR-020 kernel slice (BOARD-01, BOARD-05..14).
3. Panel ADR-019/020/021 before any is accepted (consensus REQUEST_CHANGES;
   ADR-021 was REJECT, now corrected).

## Known limits

- **The materialised suite is not fully deterministic** — a slice017 cgroup-inotify
  test flaked once under load (3 greens since; unfixed); tensions the pure-function
  thesis and needs a dedicated stability effort.
- **Concurrent owner sessions commit to this tree** (governance/skills layer);
  six such commits landed this session and reached main via `dc7f9fe8d`.
- **Running the harness commits your working tree** (`plugin/ranex.ts`, on idle).
