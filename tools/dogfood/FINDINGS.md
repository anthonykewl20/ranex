# Dogfood findings

Output of the iteration loop (`dogfood.py iterate`). Every finding names the
verified behaviour, the file:line anchor, and the scenario that pins it. A
finding is only closed by a change in the KERNEL that makes its pinning
scenario drift (which the loop reports) — never by editing the scenario to
match the kernel silently.

## Open

### F-005 (CONFIRMED, partially closed) — journal detects only partial edits; interval-honest wording for small samples

- Source: the 2026-09-03 full adversarial audit of `tools/dogfood/**`
  (mutation testing, 18 mutants, 7 killed), committed as
  `tools/dogfood/AUDIT-2026-09-03.md` at 85ed1f1cf and removed from the tree
  the same day by the docs cap (`test_no_document_exists_outside_the_allowed_set`);
  the full analysis is preserved verbatim in git history at that commit.
- Still open, re-anchored against the tree:
  1. Journal chain: hash-linking detects partial edits only. A full rewrite
     that forges a self-consistent chain (or a truncation from a fresh head)
     verifies clean — nothing anchors the chain head to committed state.
     Every "tamper-evident" claim should read "partial-edit-evident" until
     the head is signed/anchored. Pinned partially by
     `journal-tamper-detected` (UPDATE refusal) and
     `proof-journal-tamper-propagation`; full-rewrite/truncation/splice
     scenarios are the missing pins.
  2. The "0 false verdicts" agreement claims are point estimates with no
     interval; at this sample size the honest wording is Clopper-Pearson
     upper bounds, not zeroes.
- Closed in the harness-audit fix:
  - Canonical-JSON disagreement (was item 2): dogfood's independent layer
    and `math_proofs._independent_canonical` now use `ensure_ascii=False`
    with the kernel; `proof-canonical-agreement` includes a non-ASCII
    sample (`café`).
  - `argv[3]` misparse (was item 3): oss_bench now uses `cmdparse.parse_cmd`
    (same node-id grammar as the trainer) and refuses a cmd with no node
    ids. Relative `--out` paths are resolved before the child cwd is set.
    Existing pile rows that judged the kernel journal or ran
    `pytest pytest pytest` are still in the append-only archive but are
    classified `harness_fault` by `proofs.summary()` and excluded from
    kernel false-block / false-pass counts.
- Audit items already closed by earlier commits: report-site numbers now all
  derived from the archive (corpus-driven page), admission taxonomy and
  boundary/pigeonhole/fixed-point scenarios landed with the blind-spot
  mathematics hardening.

### F-004 (CONFIRMED) — collection-error junit is refused; the gate journals an observed failure as ABSENCE

- Anchor: `src/ranex/foundation/suite_results.py:125` (`_test_id` refuses a
  testcase whose `classname` is empty) and the run's `ERROR  junitxml testcase
  must carry classname and name` (run exit 2).
- Verified 2026-09-03 by the dogfood trainer's preflight over the real
  VulcanBench corpus (23/157 exercisable tasks refuse with exactly this
  error; 5 more fail preflight with `cannot parse junitxml: no element
  found` — 28 preflight-failed in total) and by a direct governed-cycle
  probe on py-txn-kvstore with the
  test file broken at import: pytest 7.4.4 writes the collection error as
  `<testcase classname="" name="test_txnkv" ...><error/></testcase>`; ranex
  refuses the whole artifact; no evidence is recorded; the gate verdict is
  correctly FAIL but the journaled diagnosis is `no evidence for required
  claim: tests-executed` — the phrasing reserved for work never done. A
  genuine red-at-import suite is filed as an unfinished task, the exact
  misfiling the kernel elsewhere refuses to make (see `_diagnosis`,
  verdict.py:291-306, and the admission header's trust-chain note).
- Behaviour is fail-closed (verdict never wrong); the defect is diagnostic.
- Pinned by: trainer corpus class `corpus/preflight-failed` with reason
  `junitxml testcase must carry classname and name` (23 tasks, cached in
  `tools/dogfood/training/corpus.json`), plus the probe transcript above.
  Candidate kernel direction (owner decision — suite trust surface, not to
  be hand-fixed unattended): map a file-level collection error to a
  synthetic file outcome ("error") instead of refusing the artifact, so the
  claim records an observed collection failure rather than silence.

### F-003 (CONFIRMED, environmental prerequisite) — governing third-party repos needs a vendored CLI and root-installed test tooling

- Verified 2026-09-03 while building the OSS two-arm benchmark:
  1. `governed_repository_root()` (cli/repository.py:331) resolves the
     governed repo from the CLI's own location, NOT caller cwd — so the CLI
     governs the repo that contains it. Governing a third-party task repo
     requires vendoring `src/ranex` into that repo and running with
     `PYTHONPATH` pointing there (the kernel's own clone-judges-clone model;
     consistent with ADR-009, but undocumented for external integrators).
  2. `ranex run` resolves argv[0] only through the pinned toolchain
     (`/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`), refusing user-writable
     routes — by design. Consequence: task commands like `python -m pytest`
     cannot run under governance unless a pinned interpreter carries pytest,
     which on this machine requires root (`sudo apt install python3-pytest`).
- Not a security bug — the pin is correct. It is an integration/usability
  cost that any external adopter hits on day one.
- MITIGATED 2026-09-04: the candidate improvement is delivered — the
  vendoring pattern is now documented and scripted as
  `tools/dogfood/external_proof.py` (see `tools/dogfood/README.md`), which
  ran the released v0.1.0 tag end-to-end on a clean external repository
  (benjaminp/six @ c8e394065c): install from the tag, vendored tree digest
  == `<tag>:src`, governed PASS, journal verified, and the stale-evidence
  attack (`stale-proof-external`) refused with exit 1 — reproducible
  across runs (verdicts/exits/reasons identical; only fresh-key digests
  differ). Receipts: proof pile entries 0010/0011. The anchor cost itself
  is unchanged kernel behaviour, so the finding stays open as the recorded
  prerequisite, now with a supported path instead of folklore.

### F-002 (CONFIRMED) — suite outcome split is checkout-environment-dependent; expected_skips are not location-reproducible

- Verified 2026-09-03 (~04:30), paired sequential runs at commit edf1a98605:
  - main checkout:   1657 collected, 1623 passed,  34 skipped, exit 0 (green)
  - fresh worktree:  1657 collected, 1598 passed,  59 skipped, exit 0 (green)
- Same commit, identical collected ID set, both green — but 25 tests pass in
  the main checkout and skip in a fresh worktree. The outcome split depends
  on untracked local state (e.g. `.local/**` scratch, host qualification
  material), so a frozen `expected_skips` set cannot be reproduced from an
  arbitrary clone location.
- Also observed, NOT interpreted (the freeze accounting was not read):
  the committed golden (`governance/suite_manifest.json`) expects 166 skips
  while both runs produced 34 / 59 — how expected_skips are counted by the
  freeze tool vs pytest is UNVERIFIED here.
- Methodology note: two earlier PARALLEL runs of the same suites produced
  failures/errors in the confinement/cgroup tests in both locations; the
  repo's own ADR-046 requires serialized cgroup probes. Sequential runs are
  mandatory for any suite comparison on one machine — parallel full-suite
  runs on this repo are invalid by construction.
- Severity: LOW (green preserved everywhere; reproducibility of the frozen
  skip set across checkout locations is the weak point). Candidate fix
  direction (not attempted): make the location/state-dependent skip arms
  explicit expected-skip declarations the freeze already supports, or have
  the e2e prereqs materialize the missing state in any checkout.

### F-001 — `Journal.verify()` raises instead of returning False on non-JSON record corruption

- Anchor: `src/ranex/governed_execution/adapters/persistence/sqlite/journal.py:176`
  (`json.loads(row["record"])` inside `verify()`, unguarded).
- Behaviour (verified): corrupting a journal row's `record` to non-JSON text
  (after dropping the UPDATE trigger out-of-band) makes `verify()` raise
  `json.JSONDecodeError` (a `ValueError`), while the docstring contract says
  "False means a row changed outside `append`".
- Severity: LOW (API contract, not security). The failure is closed — the
  corruption is never accepted; but a caller written to the documented bool
  contract will crash instead of reporting tampering. `cmd_journal_verify`
  currently lets the exception surface as a traceback rather than naming the
  broken row, unlike the chain-mismatch path which names seq + ordinal.
- Pinned by: `journal-nonjson-corruption` scenario (facts record the raising
  behaviour; any kernel fix will surface as baseline drift).

## Closed

### F-006 — census baseline drift from the SLICE-084 receiver landing (closed same run, 2026-09-05)

- Anchor: `ranex/cli/main.py:cmd_run` (McCabe M 44 → 45) and the receiver
  module added by `14341b3f6` (SLICE-084); census `measured_functions`
  405 → 409, `never_touched_high_M` unchanged.
- Behaviour (verified): the 2026-09-05 unattended iterate flagged
  baseline-drift on `evolve-blind-spot-census` alone; the scenario's property
  assertions passed — the drift was the kernel-shape facts moving with the
  owner's landed, slice-closed feature, which post-dated the baseline
  re-record in the rewritten history line.
- How closed: drift reviewed against the intended change (backlog delta was
  exactly `cmd_run` M+1 and four newly-measured functions); baseline
  deliberately re-recorded — only the census digest changed
  (`a0c042dd…` → `602e986d…`); re-iterate 0 findings (iteration-012).
  No assertion weakened, no kernel file touched.

### F-000 — construction-time capability drift between the catalog and the parser (tool-side, closed same session)

While wiring the CLI scenarios, three catalog assumptions failed against the
real code and were corrected by reading the source, not by relaxing the check:
`Gate` requires an explicit `blocking=True` argument (a non-blocking gate is
refused at construction — `verdict.py:208`), `Journal.append` takes structured
records with `.as_record()` (not dicts), and junitxml test IDs are synthesised
as `classname.py::name` (`suite_results.py:129`). Recorded because it is the
loop working as designed: assumptions die when they meet the parser.
