# State

**Updated:** 2026-09-25
**Active slice:** none — #111 closed on PR #124 and #114 closes on PR #128;
#112/#115 then task authority (#119) follow.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
SLICE-093 / #114: bare-arm purity. The bare arm runs from a DECLARED
allowlist (never dict(os.environ)); an in-child canary measures what every
command actually received and any RANEX_* variable, kernel-naming
PYTHONPATH/PATH entry, or constructed-vs-observed deviation fails the run
loudly (exit 3, no ground truth). --contaminate is the caught negative
control; prior two-arm numbers re-labelled UNVERIFIED (F-041); five
ceremony arms VERIFIED ×3 (audits/2026-09-24-bare-purity/). verdict.py
untouched.

SLICE-092 / P0 envelope (DONE, first captain-ordered promotion, DIRECT
004+008): repair envelope at the read channel; `gate evaluate` publishes
the unsigned `<subject>.envelope.json` beside the signed verdict (never
evidence); `task stop-hook` is the C6 attachment.

#111 shipped on PR #124: `task delegate` records what shaped the work —
ADR-043 manifest and outcome carry `instruction_digest` (sha256 over the
canonical composed instruction) plus a redacted `instruction` stream
(2026-09-24-issue111-instruction-digest/).

SLICE-091 / #118 (live HTTP observer), SLICE-090 / #113 (instrument
self-test), SLICE-089 / #100 (handbook injection) and SLICE-088 / #110
(markers) stand as recorded; SLICE-085 stays blocked. Queue: #112
(minimization ladder = the C2 orchestrator over SLICE-092's rung
pointers), #115, milestone 7 (#107-#109), then #102, #105, #106, #119.

Suite status, measured 2026-09-25: red only in the five files of the
standing host-glibc / reproducible-build drift family (slice036 selectors,
approved-batch, specification-batch, gating stage_08b/slice009,
suite-freeze goldens) — same set as the pristine base checkout; the owner
re-pin main already records is still needed. #114 runs: plain 2074 passed
/ 6F+13E, hermetic freeze 2054 passed / 2F+9E — all red inside that
family; the 13 bare-purity tests pass in both. Suite manifest refreeze on
this merged committed tree follows in this pass, load_manifest first.

Parallel work and overlapping verification remain owner-authorized
(2026-09-12); separate writer worktrees, pinned verification worktrees;
refreeze on a committed tree and load_manifest before committing it.
Remaining boundaries unchanged: same-subject evidence reuse; hostile
report producers (F-012); same-UID trusted controller; no external witness
against an operator holding both keys. Harness mediation, observer
scheduling, merge-group checks and production hosting stay UNVERIFIED or
UNIMPLEMENTED as detailed in MAP.
