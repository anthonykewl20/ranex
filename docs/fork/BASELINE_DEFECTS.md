# Ranex inherited baseline defects

Last verified: 2026-07-27 (Asia/Manila)

These defects are the exact inherited, host-sensitive failures accepted in the
Ranex upstream baseline at
`d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`. They are not silent test
allowances: future Ranex verification must report them by name and must treat
every additional failure as a regression.

## Comparison rule

- The accepted set contains exactly `BL-001`, `BL-002`, and `BL-003`.
- The relevant production and test files must remain byte-identical to the
  upstream baseline while a defect is classified as inherited.
- A renamed, moved, or behaviorally changed failure requires reclassification.
- A future upstream fix closes the corresponding defect; Ranex must not preserve
  the failure deliberately.
- No test assertion may be weakened merely to match this baseline.

## Open defects

### BL-001 — host mount paths trigger false container detection

| Field | Value |
|---|---|
| Status | `OPEN_INHERITED` |
| Test | `tests/agent/test_copilot_acp_client.py::test_run_prompt_preserves_real_home_when_profile_home_available` |
| Observed impact | The child process receives the profile-scoped Hermes home instead of preserving the real home expected by the test |
| Host trigger | Docker/containerd paths elsewhere in mount information cause the inherited detector to classify a systemd host as a container |
| Reproduction | Reproduced in the narrow two-file, one-worker baseline run |
| Ranex runtime regression | No; relevant source and test are byte-identical to upstream |
| Closure check | Upstream detector no longer treats unrelated host mount paths as proof that the current process is containerized, and the exact test passes under the canonical wrapper |

### BL-002 — discovered Claude credential changes stable-ID recovery

| Field | Value |
|---|---|
| Status | `OPEN_INHERITED` |
| Test | `tests/agent/test_credential_pool_routing.py::TestFailureAttribution::test_auth_refresh_uses_stable_id_after_runtime_key_changes` |
| Observed impact | A temporary one-entry pool gains a real-home `claude_code` entry and performs recovery contrary to the test's assumption |
| Host trigger | Automatic discovery of the user's existing Claude Code credential record |
| Reproduction | Reproduced with one worker; the credential-pool file passes all 20 tests under an isolated nonexistent `HOME` |
| Ranex runtime regression | No; relevant source and test are byte-identical to upstream |
| Closure check | The exact test isolates ambient credential discovery or explicitly models the extra entry, then passes under the canonical wrapper without using the user's credential |

### BL-003 — discovered Claude credential changes unmatched-key retry

| Field | Value |
|---|---|
| Status | `OPEN_INHERITED` |
| Test | `tests/agent/test_credential_pool_routing.py::TestFailureAttribution::test_unmatched_key_does_not_retry_only_pool_entry` |
| Observed impact | The same ambient `claude_code` discovery invalidates the test's one-entry assumption and permits rotation |
| Host trigger | Automatic discovery of the user's existing Claude Code credential record |
| Reproduction | Reproduced with one worker; the credential-pool file passes all 20 tests under an isolated nonexistent `HOME` |
| Ranex runtime regression | No; relevant source and test are byte-identical to upstream |
| Closure check | The exact test isolates ambient credential discovery or explicitly models the extra entry, then passes under the canonical wrapper without using the user's credential |

## Baseline reference

The commands, counts, isolation evidence, and warning record remain in
[`UPSTREAM_BASELINE.md`](UPSTREAM_BASELINE.md). This tracker supplies stable
defect identities for comparison; it does not replace the raw test evidence or
claim that the failures are fixed.
