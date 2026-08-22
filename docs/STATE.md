# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-23 (ADR-033 OCR remediation; pending re-review)
**Active slice:** none
## Where we stopped
ADR-033 is proposed and awaiting landing; this OCR remediation is pending
re-review, and it is not accepted, merged, or closed. The remediation freezes the
loopback/http/ephemeral-port bootstrap object, 65,536-byte bootstrap and
32-tool bounds, inherited-FD raw-key ingress plus FD3 replacement/close
semantics, stdlib HTTP/TLS plus the policy-specific bounded SSE validator,
pre-stream status mapping, reservation-state accounting, optional session-bound
chat-provider policy, and an additive
ADR-031 stage event owned by #43. Handshake/version vectors use `response` as
literal wire bodies; chat vectors use `expected` as broker state observations,
never SSE bodies. Vectors cover replay, ninth-request, concurrency, expiry,
response-too-large, invalid tool ordering, and invalid requestId terminal syntax.
SLICE-059 (#39, task family — milestone 4's last family slice) is done and
archived: dispatch→work→`run`→judge, tamper/self-approval/moved-base/digest
refusals, clean PUBLISHED merge, residue detection, and real delegated model
run; three journey goldens are captured (dbe923e7…/f7ff1f74…/cac49c48…). The
byte-exact blocker is Option 1 (DECISION issuecomment-5359345600), with zero
frozen-test changes. Ceremony 2bab8c9bee2ab93d4b84b2f5c4505944442405e: FROZEN
tests=1399 expected_skips=136 run_exit=0, round-trip 6/6,
cross-check 0 honest, fail_under 16.68 → 14; G-1 12/2/0, G-2 clean, G-3/G-5
 at final SHA.
## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-036
Implementation order: harness issue #106 first, then kernel issue #43 via
SLICE-069. Issues #39 and #33 remain blocked pending secure G-4; neither is
claimed merged, accepted, or closed by this specification work.
Milestone 4's family work remains subject to tracker #33's validator act;
milestone 3 resumes at SLICE-036 (#19, MAP §0.24). Follow-ups: argument-
filtered clone and writable-tree full-mask EXECUTE (security review), the
`_journal_first_broken_row` mirror-pin test (SLICE-056), and SLICE-060's
 review-named duplication pair (cross-claim-set and newline-bearing IDs).
## Governance (owner, 2026-08-17)
Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4
 is P0's proof substrate)
## Known limits
- CI's `test` job is green again on main after the CI-debt fixes (3f900d027, 9243bea41, eb1c1e413/8dc685cca), merged into issue/39 at 0344644ff; confinement suites still fail on hosted runners (ld.so.cache drift, userns EACCES).
- MAP §4.7 rows for SLICE-054..058/060 remain absent (tracker #33 Phase-2 cure applied to SLICE-059 only, via CCR-1; the others wait on their own owner acts).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest; trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed); the journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags); writable trees carry full-mask Landmark EXECUTE — SLICE-057's recorded residuals, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (E-C18-HOST-DRIFT next session); concurrent sessions in one delegated scope interfere (serialize).
- SLICE-059 residual (owner-accepted, DECISION issuecomment-5359345600): the free model's note-line content is nondeterministic — a credentialed re-run of the delegation journey gets a content coin-flip and the byte-exact golden fails on the content lines alone; canonical entrypoint and G-1 unaffected.
