# State

**Updated:** 2026-09-25
**Active slice:** none — #111 (instruction digest) is next; task authority
(#119) under ADR-061 follows the milestone-8 queue.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
SLICE-093 / #114: bare-arm purity. The two-arm adapter's bare arm now runs
from a DECLARED allowlist (BARE_ENV_PASSTHROUGH + an asserted venv-on-PATH
entry over BARE_SYSTEM_PATH — never dict(os.environ)); an in-child canary
measures the environment every command actually receives, and any RANEX_*
variable, kernel-naming PYTHONPATH, vendored kernel on PATH, or
constructed-vs-observed deviation fails the run loudly (exit 3, no ground
truth written). --contaminate {pythonpath,ranex-var,vendored-path} is the
caught negative control; prior two-arm numbers are re-labelled UNVERIFIED
(F-041). Five ceremony arms VERIFIED, outputs byte-identical ×3
(tools/dogfood/audits/2026-09-24-bare-purity/). verdict.py untouched.

SLICE-092 / P0 envelope stands as recorded (repair envelope at the read
channel; `task stop-hook` C6 attachment; audits/2026-09-25-p0-envelope/),
as do SLICE-091 / #118 (calibrated live HTTP observer), SLICE-090 / #113
(instrument self-test) and SLICE-088/089. SLICE-085 stays blocked. Queue:
#111 (instruction digest), #112 (minimization ladder = the C2 orchestrator
over SLICE-092's shipped rung pointers), #115, milestone 7 (#107-#109),
then #102, #105, #106, #119. No ranex prove exists yet.

Suite status, measured 2026-09-24/25: the standing host-glibc /
reproducible-build drift family (slice036 selectors, approved-batch
contract, specification-batch qualification, gating stage_08b/slice009,
suite-freeze goldens) is red on a pristine base checkout too — the owner
re-pin main already records is still needed. On the pre-merge #114 tree:
2074 passed / 90 skipped / 6 failed + 13 errors, every red inside that
documented family; the 13 new bare-purity tests pass. Suite manifest
refreeze to 2217+13 IDs on the merged committed tree follows in this pass,
load_manifest before commit.

Parallel work and overlapping verification are owner-authorized
(2026-09-12): use separate writer worktrees and pinned verification
worktrees. Refreeze on a committed tree; load_manifest must accept the
result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, observer scheduling, merge-group checks and production hosting
are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
