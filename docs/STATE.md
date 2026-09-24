# State

**Updated:** 2026-09-24
**Active slice:** none — milestone 8 continues with #113; task authority (#119)
is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge;
ADR-061 defines the whole program, required exits and trust boundaries. Do
not stop at artifact integrity or describe it as product acceptance.

SLICE-090 / #118: calibrated live HTTP observer. `ranex specification
observe-http` binds an independently pinned probe bundle, materialises the
exact Git candidate, starts real PostgreSQL/PostgREST containers by immutable
image ID, runs frozen HTTP journeys with process controls, and refuses
surviving, unrelated or failing known-bad calibration. Qualification
2026-09-23, re-qualified after lint hardening (receipts bind the delivered
observer bytes): 16/16 VERIFIED — good runs byte-identical, known-bad
rejected at tenant isolation, all three calibration refusals held. Receipts:
audits/2026-09-23-live-observer/. Transient 503 readiness probes retry
under the frozen deadline. Not a verdict.

SLICE-089 / #100: path-scoped kernel handbook injection (ADR-062). Two
layers — governance/handbook.json (project) over the XDG system layer —
resolve purely per path; task delegate injects chapters plus the table into
the brief and lands the additive ADR-043 manifest field. run/gate evaluate
never read a handbook; verdict.py unchanged. #95 proof: six control pairs
over six@1.17.0 and this repo, all VERIFIED ×3:
audits/2026-09-24-handbook-injection/.

SLICE-088 / #110: deliberate-shortcut markers as deterministic evidence —
`ranex markers` into SARIF via #97's reducer; malformed markers error; scan
claims never bind a script operand. All 8 arms VERIFIED on real subprocesses
over pinned `benjaminp/six`, 3x byte-identical: audits/2026-09-23-markers/.

Suite status, measured 2026-09-23: host glibc moved past the owner's pinned
native build inputs, so the drift family (slice036 selectors, approved-batch
contract, specification-batch qualification) and every nested-green ceremony
test (gating stage_08b/slice009, suite-freeze golden run_exit=0) are red on a
pristine base too — the owner re-pin already recorded in HEAD is still
needed; detail retained at audits/2026-09-23-live-observer/base-failures.log.
Refreezes stay mechanical (IDs only, outcome-blind, load_manifest-verified).
The treehouse pool path makes host_result_dir's `../../../etc/passwd` probe
resolve inside writable `$HOME`; those five pass from `/tmp`-depth trees.

SLICE-087 / #116 stands as recorded in MAP §6.4. Queue: #113, #111, #112,
#114, #115, then milestone 7 (#107-#109), then #102, #105, #106.

#117: lane check/write race fixed by a persistent directory flock (5/5/5 admitted, fixed 2/2/2).

Parallel work and overlapping verification are owner-authorized (2026-09-12);
use separate writer worktrees and pinned verification worktrees. Refreeze on
a committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Harness mediation, observer scheduling, merge-group checks
and production hosting are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
