# SLICE-059 — real e2e: task family (dispatch/judge/merge/delegate + fanout qualification)

**Status:** open
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
without the credential gets the named
`ranex-prereq:openrouter_key:` skip, never green; the harness fork names
its own probe) plus the bun toolchain as a local hard requirement
(first-delegation's skip shape). The task file's journeys and every
golden-contract arm declare no skips — they run wherever git and the
interpreter run. The fanout arm's skip is the two-grammar scheme's context
tier (`ranex-context:fanout-gated:` — a static, byte-stable reason citing
#19), declared in the suite manifest at the close-time ceremony and
enabled only in a follow-up governed change after #19 closes. The
close-time freeze ceremony declares the observed skips with the probe
grammar — context-independent conditions the frame verifies live, both
directions.

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
   delegation journey consumes `prereq_openrouter_key`; the skip carries
   the `ranex-prereq:openrouter_key:` grammar and is declared at the
   ceremony. The skip fires (not green) on any credential-less host,
   including the red freeze below. AC-3 evidence remains the real G-4 run
   alone — a named skip never counts.
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
  (`ranex-context:fanout-gated:` … #19) and the delegation journey
  (`ranex-prereq:openrouter_key:` — OPENROUTER_API_KEY absent on this
  host), both named, both the sanctioned shapes. (Corrected 2026-08-20
  from the freeze-time draft's "9 failed / 3 passed": the executed run —
  re-run at the capture, output in the capture record — is 8/4/2; the
  freeze-time STATUS comment 5354489393 already carried the correct
  counts.)
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
- `delegation-diff.out` is NOT captured: OPENROUTER_API_KEY is absent on
  this host, and the contract's own sequencing (C-4/G-4 + the Rollback
  commitment "the owner exports the scoped OpenRouter credential for
  G-4") puts that capture at key-availability time. Its digest is
  recorded here when that capture lands. Until then G-1 cannot exit 0
  (the delegation file's three ungated golden-contract arms are its
  honest red) and the close-time ceremony holds (every precedent
  ceremony sealed a green run, run_exit=0 — SLICE-056/057/058).

## Sanctioned amendments — none

The frame exists for this family; nothing in the frozen contracts needed
an ADR-032 amendment or an issue #39 change request at freeze time, and
no `src/` change is demanded: every refusal, transcript, and binding
asserted was observed against the installed kernel at 5e1ea681d. The
implementation lane's obligations — capturing the three goldens from the
real journeys, posting AC-2's refusal artifacts and AC-3's real G-4 run
on #39, the fail_under re-derivation (G-3), and the registration
ceremony — are the issue's own demands, not amendments.

NOTICED, NOT TOUCHING (outside this slice's denied surface, reported for
the owner): CI's `test` job is red on main at 5e1ea681d (pre-dating this
slice; `uvx ruff@0.16.2 check src tests` fails on nine findings in
src/ranex and other slices' frozen test files — src/ranex is denied
surface here, and the findings are not this family's). G-2/G-5 at the
final SHA will need this owned by the lane that owns those files.
