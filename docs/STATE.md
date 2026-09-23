# State

**Updated:** 2026-09-24
**Active slice:** none — live observer is next under ADR-061.

Owner pivot: idea → approved map → frozen executable probes → scoped AI build
→ independent live evidence → deterministic verdict → exact-candidate merge.
ADR-061 defines the whole program, required exits and trust boundaries.
Do not stop at artifact integrity or describe it as product acceptance.

#111 shipped: `task delegate` now records what shaped the work. The outcome
and the ADR-043 log manifest carry `instruction_digest` (sha256 over the
canonical instruction bytes handed to the worker: prompt plus any injected
handbook chapters, composed so #100 extends it), and the resolved instruction
is retained as a redacted `instruction` stream under the unchanged ADR-043
bounded/truncating/redacting rules. Timeout outcomes carry it too; the digest
covers unredacted bytes while the stream stays redacted. Signed envelope
untouched (EVIDENCE_DOMAIN v6 is PR-07/ADR-016). Evidence:
tools/dogfood/audits/2026-09-24-issue111-instruction-digest/.

SLICE-087 / #116: external executable probe bundles, reusing A/B identity,
canonical bytes and verified Git object readers. New CLI freeze-probes and
check-probes preserve artifact integrity, not product PASS. Closing full-suite
evidence is on #116; verdict.py is unchanged.
Live journal experiment: three baseline matches and three named mutant failures;
499 unit tests pass on that same known-bad commit; live probe rejects it.
Raw output: tools/dogfood/audits/2026-09-12-probe-bundles/.

SLICE-085 / #88 production registration is parked under the owner pivot.
Prior queue is retained: milestone 8 (#113, #110, #112, #114, #115),
then milestone 7 (#107, #108, #109), then #100, #102, #105, #106.
No production sign-off, zero-bug claim or universal deterministic-runtime claim.

#117: the host lane check/write race reproduced with real concurrent processes.
A persistent directory flock now serializes registry transactions, not workloads.
Fixed runs admitted 2/2/2 and refused 14 each; one-slot runs admitted 1 each.

Suite refreeze after #111's 21 tests: 2037 IDs, 168 unchanged skips, golden
recaptured. Sealed residual (2 failed + 9 errors) is the documented drift
class — identical on pristine main 3edad33af; owner re-pin pending (PR #121).

Parallel work and overlapping verification are owner-authorized (2026-09-12).
Use separate writer worktrees and pinned verification worktrees. Refreeze on a
committed tree; load_manifest must accept the result before committing it.

Remaining boundaries: same-subject evidence reuse; hostile report producers
(F-012); same-UID trusted controller; no external witness against an operator
holding both keys. Ordinary run is non-confined. Full installed harness
mediation, independent observer scheduling, merge-group checks and production
hosting/rotation/backup are UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
