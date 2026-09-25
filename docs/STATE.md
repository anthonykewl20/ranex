# State

**Updated:** 2026-09-25
**Active slice:** [SLICE-093 — the BASE freeze and the promotion gate](docs/slices/SLICE-093-base-freeze-promotion-gate.md) — P1 of the captain-ordered oracle-science program (DIRECT 004+009).

SLICE-093 / P1 (this branch): the durable measurement instrument from
oracle-science §5. `governance/calibration/base-freeze-v1.json` — a new
committed gauge class under ADR-063 — binds kernel identity (kernel_commit
638f7d8 plus kernel_digest 2969aa74 = verdict.py bytes, identical from the
measurement commit to HEAD), the pinned subjects (six@1.17.0 @ ebd9b3af
with its mint-re-derived 200-ID/15-skip manifest digest 74f4321b and
control bank b25e2f05; ranex-handbook @ 638f7d8), and the scout's measured
reference metrics (six raw false-PASS 0.625 / honest 0.025 / KG 0.0 /
kill 0.875 / cycle 1.5s / tau bound 0.60; handbook 0.25, 0.75),
evidence-bound: scout appendix 49cc25f0, prereg d8b5b327, mint receipt
8fa2efc5, journal head 3c68c470. `ranex promotion evaluate` refuses any
improvement claim that lacks a committed freeze citation, paired marginal
deltas on the freeze's named axes (baseline = the freeze's own number),
reconciled arithmetic, a tau derived from the freeze (L3's rejected 0.80
constant is a refused cause, not an option), or an evidence receipts
digest; the cited freeze is read committed at the ref (seam C:
uncommitted gauge edits are operational refusals). Receipt:
audits/2026-09-25-base-freeze/ — 11/11 arms VERIFIED (derivation ×3
byte-identical; uncited / constant-tau / invented-baseline /
tampered-gauge all refused; the report's own C4 marginal ADMITTED;
decision bytes identical ×3). Kernel untouched: verdict.py/KERNEL_DIGEST unmoved.

SLICE-092 / P0 envelope (DONE) stands as shipped
(audits/2026-09-25-p0-envelope), as do SLICE-091/090/088/089. Queue: #112 (minimization ladder = the C2 orchestrator
over SLICE-092's rung pointers), #111, #114, #115, milestone 7
(#107-#109), then #102, #105, #106, #119. P2 (C3 anti-slop) and P3 (C4
differential reporter) ship in parallel branches per DIRECT 009.

Suite status, measured 2026-09-25 on this branch (uv run --frozen pytest
-q, clean tree): 2151 passed / 91 skipped, red only in the standing
host-glibc / reproducible-build drift family (slice036 selectors,
approved-batch contract, specification-batch qualification, gating
stage_08b/slice009, suite-freeze goldens — 7 failed / 9 errors, the same
set and totals as the pristine base checkout,
audits/2026-09-23-live-observer/base-failures.log); the owner re-pin main
already records is needed. Suite manifest refrozen to 2258 IDs on
the committed tree, load_manifest verified.

Parallel work and overlapping verification remain owner-authorized
(2026-09-12); separate writer worktrees, pinned verification worktrees.
Remaining boundaries unchanged: same-subject evidence reuse; hostile
report producers (F-012); same-UID trusted controller; no external
witness against an operator holding both keys. Harness mediation,
observer scheduling, merge-group checks and production hosting stay
UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
