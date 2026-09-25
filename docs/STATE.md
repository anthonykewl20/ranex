# State

**Updated:** 2026-09-25
**Active slice:** none — P2 antislop shipped; #112/#114/#115 then task
authority (#119) follow.

SLICE-093 / P2 antislop (DONE, DIRECT 004+009): the C3 test-integrity gauge
as the third SARIF family — `ranex antislop` (stdlib-AST scanner) censuses
per-test effective-assert counts and greps four structural slop shapes into
SARIF; `antislop-sarif-2.1.0` claims reduce the census at seam B against
frozen per-test expectations (ADR-063; seam-C trust root; census absence is
`missing` and blocks; the freeze refuses a violating tree). evaluate(),
verdict.py and the envelope untouched; no new dependencies. Receipt:
audits/2026-09-25-antislop/ (science bank 3+6 plus the two wave-1 plants,
all arms as-expected on pinned six@1.17.0, 3× identical). This repo's own
landing gate is deliberately unwired.

SLICE-092 / P0 envelope (DONE, DIRECT 004+008): the repair envelope at the
read channel — `repair_envelope.py` renders the bounded advisory packet;
`gate evaluate` publishes the unsigned `<subject>.envelope.json` beside the
signed verdict (never evidence); `ranex task stop-hook` is the C6
attachment. Receipt: audits/2026-09-25-p0-envelope/ (nine arms VERIFIED on
pinned six@1.17.0; verdict.py/KERNEL_DIGEST unmoved).

#111 shipped: `task delegate` records what shaped the work — outcome and
ADR-043 manifest carry `instruction_digest`, the instruction retained as a
redacted stream under unchanged rules. Evidence:
2026-09-24-issue111-instruction-digest/.

SLICE-091/#118, SLICE-090/#113, SLICE-089/#100 and SLICE-088/#110 stand as
recorded in their slices and audits; SLICE-085 stays blocked. Queue: #112
(minimization ladder over SLICE-092's rung pointers), #114, #115,
milestone 7 (#107-#109), then #102, #105, #106, #119.

Suite status, measured 2026-09-25: red only in the five files of the
standing host-glibc / reproducible-build drift family — the same set as the
pristine base checkout (audits/2026-09-23-live-observer/base-failures.log);
the owner re-pin main already records is still needed. Refreezes stay
mechanical (IDs only, outcome-blind). host_result_dir's traversal probe is
root-clamped (2026-09-24).

Parallel work and overlapping verification remain owner-authorized
(2026-09-12); separate writer worktrees, pinned verification worktrees;
refreeze on a committed tree and load_manifest before committing it.
Remaining boundaries unchanged: same-subject evidence reuse; hostile
report producers (F-012); same-UID trusted controller; no external
witness against an operator holding both keys. Harness mediation,
observer scheduling, merge-group checks and production hosting stay
UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
