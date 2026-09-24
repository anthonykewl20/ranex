# State

**Updated:** 2026-09-25
**Active slice:** SLICE-092 (repair envelope at the read channel, C1+C6).

Captain DIRECT 004: first captain-ordered promotion ship from the
oracle-science program (report §3.1/§3.6/§8 SLICE-A). Ships C1+C6 together,
harness-side; `verdict.py`/KERNEL_DIGEST untouched. DIRECT 008 lens: the
loop is fully autonomous across a 3-miss budget (deterministic stop), the
envelope is machine-consumable structured bytes, and freeze authoring
stays with promote ships — the graded run never mints its own freeze.

Landed in SLICE-092: `governed_execution/repair_envelope.py` renders the
bounded advisory packet (failing IDs, assertion text, file:line, repro
argv, L0/L1/L2 next-rung pointers; causes compose verbatim at the
projection, never recomputed). `ranex run` retains the junit one seam
longer into the gitignored verdict channel (`<subject>.junit.xml`);
`gate evaluate` publishes `<subject>.envelope.json` beside the signed
verdict, bound by `record_digest`, unsigned, never evidence. The ADR-043
retained-log manifest gains the `envelope` field for delegate captures.
`ranex task stop-hook [--mode stop|pretooluse]` is the C6 attachment:
runs the governed cycle observer-side in-process, reads verdict +
envelope from the read channel, answers the harness in JSON, and stops
deterministically at `--budget` (default 3) misses. Without a credential
it fabricates nothing — delegation.py:93, main.py:798 and keyring
admission remain the walls, re-proven live in the receipt.

SLICE-091 / #118 and SLICE-090 / #113 stand as recorded (live HTTP
observer; instrument self-test). SLICE-085 stays blocked. Queue after
this ship: #111 (instruction digest), #112 (minimization ladder = C2
orchestrator over the shipped pointers), #114, #115, milestone 7
(#107-#109), then #102, #105, #106, #119.

Suite status: the 2026-09-23/24 host-glibc drift note still stands — the
reproducible-build goldens are red on a pristine base checkout until the
owner re-pin lands; counts for this ship are quoted in its PR. Refreezes
stay mechanical (IDs only, outcome-blind) on a committed tree, verified
by load_manifest before committing.

Parallel work and overlapping verification remain owner-authorized
(2026-09-12); separate writer worktrees, pinned verification worktrees.
Remaining boundaries unchanged: same-subject evidence reuse; hostile
report producers (F-012); same-UID trusted controller; no external
witness against an operator holding both keys. Harness mediation,
observer scheduling, merge-group checks and production hosting stay
UNVERIFIED or UNIMPLEMENTED as detailed in MAP.
