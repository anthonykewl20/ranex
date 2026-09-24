# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061; #111 closed on PR #124; #113 is next.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the whole program, required exits and trust boundaries.
Do not stop at artifact integrity or describe it as product acceptance.

#111 shipped: `task delegate` now records what shaped the work. The outcome
and the ADR-043 log manifest carry `instruction_digest` (sha256 over the
canonical instruction bytes handed to the worker: prompt plus any injected
handbook chapters, composed so #100 extends it), and the resolved instruction
is retained as a redacted `instruction` stream under the unchanged ADR-043
bounded/truncating/redacting rules. Signed envelope untouched (EVIDENCE_DOMAIN
v6 is PR-07/ADR-016). Evidence:
tools/dogfood/audits/2026-09-24-issue111-instruction-digest/.

Suite status, measured 2026-09-23/24: the host glibc moved past the owner's
pinned native build inputs (libc, libm, libz, ld-linux, ld.so.cache, libc.a),
so the drift family (slice036 selectors, approved-batch contract,
specification-batch qualification) and every nested-green ceremony test
(gating stage_08b/slice009, suite-freeze golden's run_exit=0) are red on a
pristine base checkout too — the owner re-pin HEAD already records is still
needed. Refreezes stay mechanical (IDs only; outcome-blind by contract). The
treehouse pool path also sits deep enough that host_result_dir's
`../../../etc/passwd` probe resolves inside writable `$HOME`; those five pass
from `/tmp`-depth trees.

SLICE-087 / #116: external executable probe bundles stand as recorded in
MAP §6.4. Next: #113 (self-test wiring), #112, #114, #115, milestone 7
(#107, #108, #109), then #100 (handbook injection), #102, #105, #106.

Live journal experiment: three baseline matches, three named mutant
failures, live probe rejects the known-bad commit (2026-09-12-probe-bundles/).

#117: the host lane check/write race reproduced with real concurrent
processes; a persistent directory flock now serializes registry transactions
(two-slot fixed runs admitted 2/2/2, one-slot 1 each).

Parallel work and overlapping verification are owner-authorized (2026-09-12);
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, independent observer scheduling, merge-group checks and production
hosting/rotation/backup are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
