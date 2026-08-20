# SLICE-059 — real e2e: task family (dispatch/judge/merge/delegate + fanout qualification)

**Status:** done
**Opened:** 2026-08-20
**Closed:** 2026-08-21 (ceremony 56c445a1f; the comparator ruling DECISION issuecomment-5359345600)
**ADR:** docs/adr/ADR-032-real-e2e-suite-framework.md
**Issue:** #39 (tracker #33, milestone 4 — the ADR-032 frame's fourth and
final family customer; SLICE-055 prerequisite closed 2026-08-19; the three
earlier families closed: SLICE-056/#36, SLICE-057/#37, SLICE-058/#38)
**Contract:** frozen at `status:ready` 2026-08-20 (issue #39's body;
baseline SHA `aa454bd1b0f3301a1e85f1fbf84a52707658f456`, claim-time main
`5e1ea681d50468912dfea30b2be45e731b907280`); the allowed change surface,
gates G-0..G-5, contracts C-1..C-5, and sad paths SP-1..SP-8 in it are
binding over this slice. A kernel fix forced from this slice is a CONTRACT
CHANGE REQUEST (the SLICE-036/#19 fanout gate rides as AC-4).

## Scope — issue #39's exact ownership, nothing else

- `tests/e2e/test_task_real.py` — the task family: the real
  dispatch→work→run→judge journey over a real disposable git worktree of a
  real governed target (the first-delegation construction the contract
  names), the kernel's own `run` producing the real evidence inside the
  worktree, the tampered-evidence refusal (SP-4), the merge refusal
  journey on real evidence (self-approval SP-5/C-2, moved base SP-6/C-3,
  digest mismatch C-3), the clean PUBLISHED merge through the ordered
  journalled checks, the worktree-residue detection (SP-7), and the fanout
  qualification arm authored and skipped-with-name until #19 closes
  (AC-4). Committed red at the freeze.
- `tests/e2e/test_delegation_real.py` — the delegation family: the
  red-at-base proof, the real delegated model run over OpenRouter
  (declared network, bounded ATTEMPTS=3 retry with a fresh task id per
  attempt — SP-2), the real diff read against the journal's dispatch-record
  base, the CANDIDATE judgement with no PASS anywhere, and the
  credential/harness gating through the frame's probes (SP-1/C-5).
  Committed red at the freeze.
- `tests/e2e/expected/task-dispatch-judge.out`,
  `tests/e2e/expected/task-merge-refusal.out`,
  `tests/e2e/expected/delegation-diff.out` — the three goldens, the
  implementation lane's artifacts, captured from real runs of the frozen
  journeys (transcripts piped through `_prereqs.normalize_transcript`
  exactly as the tests do) and committed green. Hand-written goldens
  cannot pass: the sabotage control and the normalizer-application
  contracts refuse them.

No new ADR, no frame change, no kernel semantics change, no new pytest
markers, no dependency. The task family rides ADR-032: the probes it needs
are `openrouter_key` and `harness_fork` (the delegation file's arms; the
task file's journeys are all-local and gate nothing, the keygen-family
precedent), the normalizer is the frame's one function, and the comparison
is the frame's comparator with the family label. The `run`/`merge` stages
drive the CLI in-process under a patched governed root — the frozen
kernel-merge convention from `tests/e2e/test_first_delegation.py` (`run`
refuses second-repository targets, and the disposable target is not the
CLI's own checkout).

## Determination — no new ADR at open time

Issue #39's header defers the ADR to open time; ADR-032 already carries
this family's frame — the per-family golden files, the sabotage red
control, the centralized normalizer, the declared-skip grammar, the
probes, and the entrypoint/ceremony composition — and names the family
slices as its customers, so no new ADR is written and this slice links
ADR-032 (docs-discipline's open-slice rule). Every kernel behavior the
frozen tests assert was verified against the installed kernel at
5e1ea681d before freezing, in /tmp/opencode prototypes: the dispatch
journey (`DISPATCHED` → real `git worktree add` → `RECORDED` → `CANDIDATE`
exit 0 with no missing claims over real run-produced evidence), the
tampered-evidence refusal (exit 1, the claim named missing), the
self-approval refusal (`sad-path-14 self-approval` on the approver's own
real run evidence), the moved-base refusal (`sad-path-9 tip-mismatch`),
the digest-mismatch refusal (`sad-path-5 subject-digest-mismatch`), the
clean PUBLISHED merge (all five ordered checks passed, journal chain
verifies), the tracked-evidence dirty-tree rule (evidence must be
gitignored for run's own exemption), and the merge-journal conventions
(domain-object appends, `candidate_row_hash`, `sign_approval`). No `src/`
change is demanded anywhere.

## Host-gating strategy — the frame's probe/skip grammar

The delegation file's journey consumes `prereq_openrouter_key` AND
`prereq_harness_fork` through module-scoped fixtures (SP-1/C-5: a host
without the credential skips on the probe's live
`ranex-prereq:openrouter_key:` message, never green; the harness fork
names its own probe) plus the bun toolchain as a local hard requirement
(first-delegation's skip shape). The task file's journeys and every
golden-contract arm declare no skips — they run wherever git and the
interpreter run. The fanout arm's skip is the two-grammar scheme's context
tier (`ranex-context:fanout-gated:` — a static, byte-stable reason citing
#19), declared in the suite manifest at the close-time ceremony and
enabled only in a follow-up governed change after #19 closes. The
delegation journey's ceremony declaration is the context tier too —
`ranex-context:operator-action:`, the first-delegation precedent: a
probe-backed `ranex-prereq:openrouter_key:` declaration would turn every
credentialed re-run into a hard stale-prune finding (the ceremony
record's rationale, below).

## Frozen decisions carried as done-criteria contracts

Every criterion is provable by a named test in the two frozen files; from
the freeze commit on they are read-only to the implementer (spec-prd
step 6).

1. **Dispatch→judge golden — the lifecycle over real produced evidence**
   (C-1, AC-1): a real task dispatched against a real disposable worktree
   of a governed target, judged by the kernel's judge over evidence the
   kernel's own `run` produced inside that worktree; the transcript
   (DISPATCHED + RECORDED + CANDIDATE) freezes against
   `expected/task-dispatch-judge.out` — the worktree path and subject
   digests are the volatile classes (`<ABS-PATH>`/`<DIGEST>`). Proven by
   `test_task_real.py::test_dispatch_run_judge_transcript_matches_the_golden`;
   the ungated `…::test_golden_contract_task_dispatch_judge` holds the
   golden to its existence/fixpoint/token contract on every host.
2. **Tampered judge evidence refuses** (SP-4): a byte-tampered evidence
   record is refused admission, the claim it forged is named missing, the
   judge exits 1 — discriminated against the clean journey's exit 0, so a
   default PASS is impossible. Proven by
   `…::test_tampered_judge_evidence_refuses_never_a_default_pass`.
3. **Self-approval refusal on real evidence** (C-2, SP-5, AC-2): the
   approver's own real run evidence at the candidate tree; the merge
   refuses `sad-path-14 self-approval`, the transcript freezes against
   `expected/task-merge-refusal.out`, and the refusal is byte-identical on
   replay. Proven by
   `…::test_self_approval_refusal_on_real_evidence`.
4. **Named merge refusals** (C-3, SP-6): the moved base refuses
   `sad-path-9 tip-mismatch` and the digest mismatch refuses
   `sad-path-5 subject-digest-mismatch` — stable named reasons, identical
   on replay, never a silent merge. Proven by
   `…::test_moved_base_and_digest_mismatch_refusals_name_the_reason`.
5. **The clean candidate publishes through the ordered checks** (the Real
   E2E journey's step 6): producer ≠ approver, real evidence, current
   base — PUBLISHED with all five journalled checks passed and the chain
   verifying; the kernel merges, the test never does. Proven by
   `…::test_clean_candidate_publishes_through_the_ordered_checks`.
6. **Worktree residue detection** (SP-7): the journey removes every
   disposable worktree; the detector is green on the cleaned journey and
   provably red on a planted survivor. Proven by
   `…::test_worktree_residue_detection_goes_red_on_a_survivor`.
7. **Delegation golden — a real model, a real diff** (C-4, AC-3, SP-2,
   SP-3): the note test is red at the dispatch base (observed up front),
   the delegated run is retried at most ATTEMPTS=3 with a fresh task id
   per attempt, the diff is read against the journal's dispatch-record
   base and freezes against `expected/delegation-diff.out`, the
   kernel-recorded suite output proves execution, and the judgement is a
   CANDIDATE naming its missing claims with no PASS anywhere. Proven by
   `test_delegation_real.py::test_delegated_diff_matches_the_golden_and_proves_execution`;
   the ungated `…::test_golden_contract_delegation_diff` holds the golden
   to its contract on every host.
8. **Credential absence is a named skip, never green** (C-5, SP-1): the
   delegation journey consumes `prereq_openrouter_key`; the skip is
   declared at the ceremony as `ranex-context:operator-action:` — a
   probe-backed declaration would turn credentialed re-runs into hard
   stale-prune findings (the ceremony record's rationale, below), while
   the live message on a credential-less host stays the probe's
   `ranex-prereq:openrouter_key:` one. The skip fires (not green) on any
   credential-less host, including the red freeze below. AC-3 evidence
   remains the real G-4 run alone — a named skip never counts.
9. **Golden integrity contracts** (AC-1; ADR-032's red control): each
   golden is a normalizer fixpoint carrying real volatile material, a
   live-byte-doctored golden provably cannot match, and a mutated golden
   byte diffs dirty with the family named and the first hunk untruncated.
   Proven by both files' `test_goldens_carry_real_volatile_material` and
   `test_sabotage_control_mutated_golden_diffs_dirty` (the delegation
   variants run ungated with the golden itself as the actual bytes, so
   G-1's unset-credential run still exercises the red control).
10. **Fanout qualification waits for #19** (AC-4): the assertions over
    `task fanout`'s tasks-file contract are authored and frozen, skipped
    with the `ranex-context:fanout-gated:` reason citing #19 — never
    green, never failed; enabled only in a follow-up governed change.
    Proven by
    `test_task_real.py::test_fanout_qualification_arms_wait_for_slice036`.
11. **Manifest registration at close** (the standing ceremony): both
    files' test IDs enter `governance/suite_manifest.json` through the
    existing `ranex suite freeze` ceremony at slice close, no hand edits;
    the observed skips are declared with the two-grammar scheme per the
    host-gating strategy above.

## Red-freeze record (2026-08-20)

The freeze commits the two family files red in the SLICE-056..058
pattern: the goldens are absent and every golden arm fails on the loud
missing-golden assertion — the honest red, never a silent pass.

- Command: `uv run --frozen pytest -q tests/e2e/test_task_real.py
  tests/e2e/test_delegation_real.py` (repo root, clean tree plus the two
  frozen files).
- Outcome: **exit 1 — 8 failed / 4 passed / 2 skipped**. The 8 failures
  are exactly the golden arms (5 task, 3 delegation), each naming its
  missing golden. The 4 passes are the non-golden arms whose journeys run
  green at the freeze (tampered-evidence refusal, moved-base/digest
  named-reason refusals with replay equality, clean PUBLISHED merge,
  worktree-residue detection). The 2 skips are the fanout arm
  (`ranex-context:fanout-gated:` … #19) and the delegation journey (the
  probe's live `ranex-prereq:openrouter_key:` message —
  OPENROUTER_API_KEY absent on this host; its ceremony declaration is
  `ranex-context:operator-action:` per the rationale in the ceremony
  record below), both named, both the sanctioned shapes. (Corrected
  2026-08-20 from the freeze-time draft's "9 failed / 3 passed": the
  executed run — re-run at the capture, output in the capture record —
  is 8/4/2; the freeze-time STATUS comment 5354489393 already carried
  the correct counts.)
- Suite collection with the frozen files present: 1397 IDs collect
  (1383 prior + 14 new), no import breakage.

## Golden-capture record (2026-08-20)

Beside the red-freeze commit `305938bf6` (per the contract's
deterministic-recording clause; re-stated in the close-time EVIDENCE at
the final tested SHA): the two LOCAL goldens are captured from real runs
of the frozen journeys
themselves — the SLICE-056 (2e6947e365) / SLICE-058 (8fb7d79597)
precedent: the committed `family` fixture driven verbatim (imported from
the frozen file, its original reached through pytest 9's `__wrapped__`)
against a real temp factory on this host, transcripts piped through
`_prereqs.normalize_transcript` exactly as `compare_golden` applies it.
No hand-sanitization; the frozen normalizer-application and sabotage
arms enforce that and run green against these bytes.

- `task-dispatch-judge.out`
  sha256 dbe923e77121c5a2c4836509354acd6239e815bfdeda8e277e363388f79f678e
  — DISPATCHED/RECORDED/CANDIDATE over the real journey; raw transcript
  sha256 897a006725929045fa1134fbf9d3c2b0a350959f9d909637ca549a4f3fb2161b.
- `task-merge-refusal.out`
  sha256 f7ff1f74c86c20c3a8165305e426f95a048552aad8f263e002a72bee31bf6b77
  — the C-2 self-approval REFUSED line on the approver's own real run
  evidence (its raw bytes are already mask-free: the digest equals the
  raw transcript's).
- Byte-stability (C-1's idempotency clause): two independent journeys in
  separate roots (`/tmp/opencode/slice059/run1`, `run2`) produced
  byte-identical normalized goldens (`diff` clean both files; digests
  equal).
- With these bytes committed, `uv run --frozen pytest -q
  tests/e2e/test_task_real.py tests/e2e/test_delegation_real.py` =
  3 failed / 9 passed / 2 skipped — the task family fully green (10
  passed / 1 fanout skip in its file), the 3 failures exactly the
  delegation file's ungated golden arms.
- Sabotage controls (throwaway copies; the real tree untouched):
  mutated golden bytes — `CANDIDATE`→`QANDIDATE` in
  task-dispatch-judge.out → 3 red (contract, transcript-match, sabotage
  arms), exit 1; `self-approval`→`self-approvaX` in
  task-merge-refusal.out → 2 red (refusal-match, volatile-material),
  exit 1. Mutated kernel behavior — `sad-path-14 self-approval`→`…X` at
  src/ranex/cli/main.py:1405 → red at the refusal arm's transcript
  assert; `DISPATCHED`→`DISPATCHXD` at main.py:1117 → red at the
  comparator. Every control diffs dirty; nothing passed vacuously.
- `delegation-diff.out` — captured 2026-08-21 from the real G-4 run
  (CCR-2/CCR-3 below): sha256
  `cac49c48a6283364ef90ef57d89fc459d8b66bad43aa16dd93b6296537afba9d`
  (raw diff sha256
  `95fc39873cdf5333b25e2f046923c3252a15161f2768b9c8a5ce6fd282fb8491`),
  task `T-TASK-FAMILY-DELEGATION-1`, emitted commit `c345c6e6…`,
  kernel-recorded suite `1 passed`, judgement CANDIDATE exit 1 with
  missing claims `tests-executed`, no PASS anywhere, journal verifies.
  With these bytes committed, G-1 at its contract shape (credential
  unset, SP-1 named skip) is green: **12 passed / 2 skipped, exit 0**.
  The note-line nondeterminism once blocked here (BLOCKER
  issuecomment-5359180442) is RULED — see the risk-acceptance record
  below.

## Sanctioned amendments — CCR-1, CCR-2, CCR-3 (records on #39)

* **CCR-1** (issuecomment-5354660541): docs/MAP.md §4.7 added to the
  surface — one SLICE-059 row (tracker #33 Phase-2 mandate).
* **CCR-2** (issuecomment-5358926531; DECISION 5358927994), 2026-08-21:
  (a) the delegation wrappers invoke the real bridge entry
  `packages/ranex/src/index.ts` — `packages/opencode` holds only
  node_modules at the provenance-pinned harness HEAD; (b) the G-4
  credential mechanism reads the owner's EXISTING OpenRouter credential
  from the owner's store into the run environment only (free model,
  value never printed/logged/committed, store never mutated) — the
  Rollback checkpoint's substance under the owner's standing
  instructions ("complete all"; key-export objection; "we have our own
  harness").
* **CCR-3** (issuecomment-5359078756), 2026-08-21: the harness's three
  GitHub tools (the only `Schema.Union` parameters in the tree) lower to
  a top-level `anyOf` without `type`, which the frozen free model's
  upstream (Cohere via OpenRouter) rejects on every turn —
  deterministic, all ATTEMPTS=3. The wrappers seed the harness-native
  agent config denying exactly that family into the kernel's scratch
  HOME; remedy proven by a real run end-to-end before application. G-4
  environment wiring only; no assertion semantics change.

## Owner risk-acceptance — C-4's byte-exact re-run clause (DECISION issuecomment-5359345600)

BLOCKER issuecomment-5359180442 stopped execution at the owner-decision
point: the frozen free model's note-line content is nondeterministic —
six real delegated runs, three distinct AGENT_NOTE.txt forms
(`delegated work happened.` / `delegated work happened. Do not do
anything else.` / `delegated work happened`), `temperature: 0` included —
so C-4's idempotency clause ("re-running the journey reproduces the
normalized transcript byte-exactly") is **unsatisfiable as frozen** with
the contract's own model: a with-credential re-run performs a real green
journey and then fails the byte-exact comparison on exactly the
content-derived lines (the note line and its blob index; every other
byte identical, OBSERVED over the six runs).

The ruling (DECISION issuecomment-5359345600, 2026-08-21, orchestrator
decision under the specification owner's standing completion
instructions, answering the BLOCKER): **Option 1 — bless the
contract-shaped close.** G-4's frozen pass condition (real non-empty
diff; kernel-recorded suite output green only via the model's real work;
outcome posted) is satisfied by the capture run's artifacts; the
byte-exact re-run clause becomes a written owner risk-acceptance under
the milestone's universal-alignment valve ("a real-data e2e assertion,
**or an explicit written owner risk-acceptance recorded on this issue**"
— correct to the extent provable). Zero frozen-test changes; no golden
byte, assertion, or red control weakened.

**Accepted residual R-SLICE-059-1:** on any host with
`OPENROUTER_API_KEY` exported, re-running
`tests/e2e/test_delegation_real.py::test_delegated_diff_matches_the_golden_and_proves_execution`
performs a REAL delegated run whose note-line content is a coin-flip
among the observed forms; the byte-exact golden comparison then fails on
the content-derived lines alone (exit 1) even though the journey itself
is green. The canonical entrypoint environment (credential absent,
README) and G-1's contract shape are unaffected. A shape-golden
amendment is drafted as CCR-4 in the DECISION for any future owner who
wants deterministic-shape credentialed runs; it is NOT applied.

## fail_under re-derivation (G-3, 2026-08-21)

Measured by a real wired entrypoint run at this tree's content-final
state (the suite + combine + report stages of the README block, artifact
home `.local/ranex-e2e/`, transcript + report
`transcript-derivation.txt` / `coverage-report-derivation.txt`):
**TOTAL 16.68%** — 75085 statements, 62558 missed (the pre-ceremony
tree; its seven reds are the two STATE-discipline failures the blocked
session left, their three sealed-clone cascades, and the two
manifest-drift arms the ceremony itself cures — none touches `src/`
coverage). Under the standing variance-margin convention (baseline
precedent, OBSERVED: measured 17.14 → `fail_under = 15` = floor − 2):
**floor(16.68) − 2 = 14**, recorded in `pyproject.toml`
(`[tool.coverage.report]`, 15 → 14). The official G-3 at the final SHA
runs the README block verbatim and verifies TOTAL ≥ 14; its report is
posted in the close-time EVIDENCE.

NOTICED, RESOLVED UPSTREAM (disclosed 2026-08-20, closed by the main
merge 0344644ff): CI's `test` job was red on main at 5e1ea681d
(pre-dating this slice; nine ruff findings in src/ranex and earlier
slices' frozen test files). The debt was owned and fixed on main
(isort 3f900d027, pyrefly 9243bea41, re-pins eb1c1e413/8dc685cca) and
merged forward into this branch; `uvx ruff@0.16.2 check src tests` is
exit 0 here (G-2).

## Close-out record (2026-08-21)

**The G-4 capture (5fe0d3849, the CCR-2/CCR-3-amended wrappers).** The
real delegated journey ran green end-to-end on the first attempt after
CCR-3: dispatch → the REAL model call over OpenRouter (owner's
credential via CCR-2's store-read; value never printed/logged/
committed, store never mutated) → bridge commit `c345c6e6…` → the
kernel-recorded suite `1 passed` (the red-at-base note test green only
through the model's work) → CANDIDATE judgement exit 1 naming
`tests-executed`, no PASS anywhere, journal chain verifies. Provenance:
harness HEAD `9b9b521c61cb` (branch `prototype-spec`, six known dirty
github-auth files, none touched by this work), bun 1.3.14. The golden
`delegation-diff.out` (sha256 `cac49c48…`, raw diff sha256
`95fc3987…`) is those bytes; with it committed, G-1 at its contract
shape (credential unset, SP-1 named skip) is 12 passed / 2 skipped /
exit 0.

**The blocker and the ruling.** C-4's byte-exact re-run clause is
unsatisfiable with the frozen free model (six runs, three note-line
forms, `temperature: 0` included — BLOCKER issuecomment-5359180442).
Ruled Option 1 — bless the contract-shaped close (DECISION
issuecomment-5359345600): residual R-SLICE-059-1 recorded above under
the universal-alignment valve; zero frozen-test changes; CCR-4
shape-golden text drafted in the DECISION for any future owner, not
applied.

**fail_under re-derived (d91c5ac7f).** Measured TOTAL 16.68%
(75085/62558) from a real wired entrypoint measurement at the
content-final tree; floor − 2 = 14 under the standing convention
(baseline precedent 17.14 → 15). pyproject 15 → 14; derivation quoted
in its comment and in this file.

**The ceremony (56c445a1f).** The standing close ceremony on the clean
tree at d91c5ac7f: the 134 committed declarations re-declared verbatim
plus two new — the fanout arm (`ranex-context:fanout-gated:`, the
byte-stable static reason citing #19; the faithful case — declared
bytes equal the live skip message) and the delegation journey
(`ranex-context:operator-action:`, the first-delegation precedent for
the same credential-gated shape; a probe-backed declaration would turn
every credentialed re-run — the DECISION-blessed residual path — into
a hard stale-prune finding at the entrypoint cross-check). Sealed run:
1262 passed / 135 skipped / 0 failed in 125.39s — run_exit=0. FROZEN
tests=1397 expected_skips=136. Sanctioned delta verified exact by set
difference: suite 1383 → 1397 (+14: task family 10, delegation family
4), expected_skips 134 → 136 (+2, nothing reworded, nothing removed);
manifest canonical (the kernel's own loader accepts; sha256
`dc4ecadd…`). Freeze golden re-captured from the ceremony's own FROZEN
line through the frame normalizer (`suite-freeze-manifest.out` sha256
`2886644c…` — the golden embeds the frozen counts, so every re-freeze
re-captures it).

**Final verification at the ceremony-sealed state (56c445a1f).**
Freeze round-trip file 6/6 on the clean tree (the nested sealed
re-ceremony, 129.71s, reproduces the committed manifest byte-exactly
and matches the re-captured golden). Entrypoint cross-check over the
derivation run's plain-session junitxml with the fresh manifest: exit
0, hard tier honest (every observed skip declared, every
`ranex-prereq:` declaration byte-matched, no probe-backed lie), 132
informational context mismatches — the multi-context manifest's
standing shape; the fanout declaration is the faithful case (absent
from the mismatch list), the delegation journey reports
observed-drift informationally exactly as first_delegation does.
G-1/G-2/G-3/G-5 at the final tested SHA run after this archive lands,
and their verbatim tails + exits are posted in the close-time EVIDENCE
comment on #39 (the contract's deterministic-recording clause).

**Commits this slice:** 305938bf6 (frozen red) → 7b134fbe9 (the two
local goldens) → bcc70b24b (CCR-1 MAP row + docs) → 0344644ff (main
merge: the CI-debt fixes) → 5fe0d3849 (CCR-2/CCR-3 wrappers + the
delegation golden) → bbc4e4d0d (blocked-state docs) → d91c5ac7f (the
ruling + fail_under 14 + discipline-valid STATE) → 56c445a1f (the
ceremony) → the docs close-out.
