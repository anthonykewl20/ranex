# Dogfood findings

Output of the iteration loop (`dogfood.py iterate`). Every finding names the
verified behaviour, the file:line anchor, and the scenario that pins it. A
finding is only closed by a change in the KERNEL that makes its pinning
scenario drift (which the loop reports) — never by editing the scenario to
match the kernel silently.

## Open

### F-028 — the paused-fetch driver raced its own ignored probe

The immutable v0.1.001 tag's hosted CI completed its instrumented regression,
then the receiver journey failed before observing its paused Git fetch. The
thread-pool submission and immediate ignored-delivery probe race for the real
receiver's one pipeline lock; a submitted future does not prove Git has begun.
The driver now observes the actual child `git ... fetch` process before probing
for 503. It preserves named failures and the production 30-second fetch deadline.
Two real-PR repeats at 7e559bfbc0e4852665ec3611d4dcdb4ac94119f7 passed
all 41 controls on Python 3.14.7, with two-CPU and one-CPU affinity. Both
observed actual fetch admission, 503 backpressure, the unchanged fetch timeout
and successful redelivery after recovery. Receipts: `receiver-f028-1/receipt.json`
and `receiver-f028-2/receipt.json` in the remediation archive. Original hosted
failure: `audits/2026-09-05-remediation/ci-release-tag-failed.log`. Fresh
hosted validation has since completed on every padded release: dispatched tag
CI runs 34024985822 (v0.1.004), 34035352146 (v0.1.005) and 34041099936
(v0.1.006) all passed, including the receiver journeys on the release commits.

### F-025 — a shared receiver stress pass did not complete every request

The expanded real PR replay at fd13edbc0 accepted 158/200 concurrent requests
across two receiver processes. That attempt retained the count but not each
status, so its attribution is UNVERIFIED. A diagnostic repeat retained all
responses and accepted 200/200 without production changes. The earlier failure
is not erased or called fixed; final stress must retain individual statuses.
The burst driver now records every status and explicitly redelivers 503s after
contention drains; unexpected statuses still fail. The subsequent 38-control
admission run passed, including 200/200 shared-state requests. The later
41-control run additionally observed a real 503 while Git held the pipeline,
then a successful redelivery after recovery (`receiver-final-6b/receipt.json`).
The earlier admission run needed
no post-burst retry, so the earlier incomplete run is not retrospectively PASS.
The paused-Git setup initially stopped only the waiting Git wrapper, leaving its
server child running. The corrected driver stops its own isolated process group
and uses a fresh transport clone; real fetches then time out at 30.04/30.05 seconds
and recover after the server resumes. These are harness corrections, not changed
production deadlines. All failed setup receipts remain in the archive.


### F-023 — shared Git identity writes race in the existing fanout harness

The complete qualified regression at af9f403 recorded a nested bounded-pool
failure; its abbreviated report did not retain the inner assertion details.
Inspection found each worker writing user.name/user.email to the linked
worktrees' shared Git config. On five real Ranex worktrees, those same concurrent
operations failed 48/100 times with a config-lock refusal. Per-command identity
then committed the actual Ranex source patch in all five worktrees and preserved
the shared config. The existing harness now uses that per-command Git identity;
pool bounds and timeouts are unchanged, and failures retain CLI diagnostics.
The exact attribution of the original nested failure remains UNVERIFIED pending
fresh complete regression. The first repair introduced an indentation error in
the generated worker script: the retained cold diagnostic shows all five workers
without emissions. The indentation is corrected and generated Python syntax
checked. The corrected cold-start journey at fd13edbc0 passed all 9 stages;
its actual governed suite reported 1657 passed and 138 skipped, then the gate
accepted freshly qualified host evidence. The clean complete regression at
701258fbc then passed 1786 tests with 9 named skips (2125.39 seconds).
This verifies the corrected harness; the original abbreviated failure still
does not establish a unique cause.
This is not a live-agent fanout correctness proof.
Receipt: `audits/2026-09-05-remediation/git-identity-race.json`.

### F-022 — live Kogg subject qualification is unavailable in the measured runtime

After fixing active-account selection, the actual controller reaches the pinned
Kogg clone. With its specified npm 11.6.0 on Node 24.18.0, `npm ci` fails loading
`lightningcss-linux-x64-gnu`. A retained diagnostic checkout with npm 11.16.0
builds from the unchanged lock, then `npm test` exits 1 with 17 failing tests
(UI navigation plus workspace/AST runtime tests). Kogg's own CI and `.nvmrc`
select Node 22. A fresh live controller run on checksum-verified Node 22.23.2
and pinned npm 11.6.0 also fails during `npm ci` in the lightningcss load path.
Receipts: `kogg-node22-2.json` and `node22-SHASUMS256.txt` in the remediation
archive. Node 22 with a changed npm pin remains unqualified. These observations
do not establish a current Ranex kernel failure or universal upstream failure.

The bootstrap now checks the actual npm version before execution and refuses
a mismatch; it does not call a real build failure credential-BLOCKED or PASS.
The historical subject pin and lock were not silently updated to conceal this.
Receipts: `audits/2026-09-05-remediation/kogg-current-2.xml` and
`kogg-diagnostic/receipt.json`, with compressed original diagnostic logs.
The matching optional-peer symptom is also documented in the
[npm issue tracker](https://github.com/npm/cli/issues/8489); attribution beyond
the measured install behavior remains unverified.

### F-018 (RECURRED after release) — journal schema initialization contends with writers

The v0.1.001 main CI instrumented run failed in `_connect` at
`conn.executescript(_SCHEMA)` during the existing eight-writer burst. Its bare
suite passed; the failed instrumented run reported 1665 passed and 129 skipped.
The separate tag run passed that regression but failed F-028 afterward. Both
failures are retained; the earlier successful stress runs are not a closure.

The follow-up reads the existing three schema objects instead of issuing DDL
on every connection, and creates missing objects inside BEGIN IMMEDIATE/COMMIT.
The 60-second budget, append transactions and compare-and-append semantics are
unchanged. The first 20,000-append diagnostic passed; its uncommitted source is
retained explicitly in `storage-after-release-fixed/`. Matching hosted-runtime
stress at committed 7e559bfbc0e4852665ec3611d4dcdb4ac94119f7 then passed
100,000 appends across 25 alternating eight-thread/eight-process rounds on
Python 3.14.7 and SQLite 3.53.1, restricted to one CPU. All 25 chains verified;
1000 failed damaged-header opens held the descriptor count at six. Both missing
append-only triggers were restored on copies of the original real journals,
then blocked actual SQL mutation without changing their anchored chains. Ten
CAS races produced exactly ten winners and 70 named stale refusals. Receipt:
`audits/2026-09-05-remediation/storage-100k-3147/receipt.json`. The existing
journal regression also passed 22 checks on that runtime. Repeated appends
measure storage contention, not independent code correctness observations.
Fresh hosted validation has since completed on the padded releases: dispatched
tag CI runs 34024985822 (v0.1.004), 34035352146 (v0.1.005) and 34041099936
(v0.1.006) all passed the frozen suites and the storage/journal journeys on
the release commits. SQLite documents
[write intent and lock upgrades](https://www.sqlite.org/lang_transaction.html)
and [busy-handler limits](https://www.sqlite.org/c3ref/busy_handler.html).
The exact scheduling cause of the old intermittent failure remains unverified.

#### Earlier evidence (retained)

**Remediation 2026-09-05:** SQLite connections now close deterministically.
Two real storage runs replayed original gate evaluations for 20,000 appends
apiece, alternating eight-thread and eight-process contention. Every chain
verified, and each process finished with the same descriptor count it started
with. The original intermittent timeout has not recurred; this does not prove
writer fairness or establish its original root cause. Evidence:
`audits/2026-09-05-remediation/storage-stress-1/receipt.json` and
`storage-stress-2/receipt.json`.

- The exploratory released full suite raised `sqlite3.OperationalError:
  database is locked` at `Journal.append`'s `BEGIN IMMEDIATE` during the
  eight-writer, 4000-append integration test. The implementation sets a
  finite 60-second SQLite lock timeout; it does not guarantee writer fairness.
- The unchanged journal implementation passed the same real contention test
  in isolation in 10.97 seconds. A repeatable standalone failure trigger and
  precise load attribution remain UNVERIFIED. No timeout or assertion was
  changed to conceal the observation.

### F-010 (CONFIRMED, specification mismatch) — ordinary non-strict XPASS receives gate PASS

- Reproduced with released v0.1.0 (`edf1a98605`) and HEAD (`48f3a98e48`)
  on the pinned external `benjaminp/six` repository: the actual pytest run
  reports **184 passed, 1 xpassed**, then Ranex records exit 0 and gate PASS.
  Strict XPASS, XFAIL, undeclared skip, and deselection controls all block.
- Anchor: `foundation/suite_results.py:_outcome` treats a testcase without
  outcome children as passed. Installed pytest 7.4.4's JUnit reporter emits
  this shape for non-strict XPASS; the kernel's pinned pytest 9.1.1 reporter
  has the same pass branch. No malicious XML writer is required.
- Contradicts ADR-011's unqualified XPASS-refusal claim and README's
  completed SLICE-009 description. This is a policy/diagnosis mismatch;
  the XPASS test did execute and its assertion passed.
- Pin: `release_audit.py`, `nonstrict-xpass` versus `strict-xpass`.

### F-012 (RECONFIRMED boundary) — authenticated test reports are not an independent correctness oracle

- With real `six.integer_types` broken, an independent Python assertion
  fails and the ordinary governed test run blocks. Add a committed pytest
  reporting hook that changes failed reports to passed: the same broken
  code receives signed evidence and gate PASS on both v0.1.0 and HEAD.
  The attack never constructs an evidence record or a signature itself.
- This is ADR-007/011's disclosed hostile-reporter limit, not a newly found
  cryptographic bypass. It prevents claiming that current general-purpose
  `run` independently proves arbitrary worker-controlled code/tests correct.
- Pin: `release_audit.py`, `broken-source`, `hostile-result-producer`, and
  the independent Python assertion captured in the receipt. The protected
  A/B/C qualification path is a different scope and is not disproved by it.

### F-005 (PARTIALLY CLOSED) — journal needs an independent history anchor

**Remediation 2026-09-05:** `journal verify --expected-head` compares the
verified chain with a separately retained head. Actual CLI controls reject
truncation, empty history, non-JSON corruption and a completely recomputed
rewrite; the unchanged database passes. Without the anchor, internal chain
consistency still cannot establish completeness. Ordinary reuse of unchanged
valid evidence remains allowed; fresh nonces are not implemented. Evidence:
`audits/2026-09-05-remediation/storage-stress-2/receipt.json`.

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
     **2026-09-05:** those missing pins now exist in `release_audit.py`:
     suffix truncation of a multi-row real gate journal, deletion of all
     rows, and a complete independently rehashed replacement history all
     return `chain=verified` on v0.1.0 and HEAD. An isolated partial edit
     refuses. The anti-replay probe also accepts old evidence unchanged.
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

## Closed

### F-030 — version tags did not create GitHub Release pages

The owner observed main at v0.1.003 while the GitHub Releases sidebar still
listed v0.1.0: the helper pushed Git refs and built packages but never created
a Release object. Closed with receipts: the repaired automation published
v0.1.004 (85037d1d9, issue #84 — wheel/sdist/SHA256SUMS uploaded, digests
matched GitHub's asset hashes, fresh public clone quickstart and the external
Six demo passed), then v0.1.005 (9b35392d4, 2026-09-06T13:11:47Z) and v0.1.006
(fae7ee94, 2026-09-06T15:03:33Z) without manual repair — each with a Latest
Release page, verified assets and an explicitly dispatched green tag CI
(34024985822, 34035352146, 34041099936). The manual v0.1.003 page remains at
its original tag 82cacd162adf022644ce3316783491153ac0bcf6.

### F-029 — dogfood releases required an unconfigured personal token

The eligible workflow run 33976105531 failed its owner-identity check because
`RANEX_RELEASE_TOKEN` was absent; later green runs skipped publication. Closed
by the owner-authorized built-in GITHUB_TOKEN workflow (2026-09-06): real
eligible hosted publication completed under issue #83 (source CI 34021796323,
release workflow 34022370140, dispatched tag CI 34022632883) and has repeated
for v0.1.004, v0.1.005 and v0.1.006 without any personal secret. The workflow
contract's first dispatch attempt (34021451447, 1 failed) is retained in
`audits/2026-09-06-builtin-release/source-ci-attempt-1.log`; the contract now
requires the explicit dispatch input and coverage comparison.

### F-034 — the two_arm gold arm silently shipped the empty stub inside a worktree

`build_governed_repo` applied the task's gold patch BEFORE `git init`. With
`--out` inside any git worktree, `git apply` from the repository-less directory
discovers the enclosing repository and — documented git behavior — silently
ignores patched paths outside the current directory, exiting 0 with nothing
applied. The "task base (+gold)" commit then carried the 3-line empty stub,
every governed run exited 1, and the gold arm's gate FAILed on bare-proven
6/6-green code: a harness-produced FALSE REJECTION at v0.1.005
(`.local/campaign/twoarm-v005-semver/validation.json`; kernel verdict honest on
its inputs). Prior studies ran with `--out` outside any worktree, where
no-index apply works — the fault only appears in the inside-checkout layout.
Closed by initializing the nested repository before any patch application.
Post-fix, the identical inside-checkout invocation reports bare gold 6/6 vs
empty 0/6, gold gate PASS (journal verified, 9.299s) and empty gate FAIL —
VALIDATION PASS. Receipts: `audits/2026-09-06-harness-faults/` (issue #89).

### F-033 — storage_stress crashed on the repository's own mixed journal

`tools/dogfood/storage_stress.py` selected `evaluations limit 1` and fed it to
`evaluation_for`; the governance journal's first row is a depset record, so the
replay KeyErrored on the missing `verdict` field and the tool exited 1 on the
most canonical "actual gate journal" there is — reproduced directly at
9b35392d4 and again from the campaign soak driver. Closed by selecting the
first row that actually carries a verdict and refusing honestly when a journal
has none. The fixed tool ran the full governance-journal load on this host:
4000 appends verified, relative-path verification PASS, and all four tamper
controls (nonjson/truncated/empty/rewritten) still refuse with exit 1.
Receipt: `audits/2026-09-06-harness-faults/` (issue #89).

### F-031 — the docs cap swept gitignored `.local` receipts and failed the frozen suite on the qualified host

At v0.1.004 (85037d1d9) the canonical `uv run --frozen pytest -q` failed on
the qualified operator host with 9 failures while release CI reported green:
`_tracked_markdown()` (tests/contract/test_docs_discipline.py:117) walks the
filesystem with `REPO_ROOT.rglob("*.md")`, and `_SKIP_DIRS` (line 24) omitted
`.local`. The documented workflow retains real receipts under gitignored
`.local/` — the #84 release-validation clones under
`.local/public-release/quickstart*/**` carry full documentation trees — so the
operator's own evidence failed the cap. CI has no `.local` and stayed green;
the cap's docstring scope is "every markdown file we are responsible for",
which gitignored operator scratch is not.

Closed by adding `.local` to `_SKIP_DIRS` with the scope comment naming this
finding. Controls on the fixed tree: a stray `CAMPAIGN-SCRATCH.md` at the
repository root still fails the cap (1 failed, 2026-09-06), and the same file
under `.local/` passes (1 passed). No repository document left the cap's
scope; no assertion was weakened. Evidence: issue #85 and the baseline run
receipt in `.local/campaign/baseline-pytest.log` (9 failed, 1750 passed,
36 skipped at 85037d1d9, 1559.86s).

### F-032 — the cold-start journey pinned the pre-rewrite README and failed on the qualified host

The same baseline run failed `tests/e2e/test_cold_start_journey.py` stages
2–9: `documented()` (test file line 84) asserted the setup steps appear in
README.md, but 3deb74459 (#84) deliberately moved the detailed operator
recipes to docs/OPERATIONS.md and shortened README. Every pinned fragment
(`python -m ranex.cli.main gate evaluate|keygen|deps fetch|deps approve|run …`,
the `producers:` keyring merge snippet) still exists in the guide's "Running
it" section — the documentation did not drift from the product; the journey
had not followed the restructure. CI skips this host-gated journey (129 named
skips), so the release shipped without seeing it.

Closed by reading README.md plus the linked operator guide as one body in
`documented()`, matching what a new operator follows. Controls on the fixed
tree: the full journey passes twice with real nested governed runs
(1655 passed / 140 skipped in 251.34s, evidence signed for the clone's tree
digest); removing the `gate evaluate` module-path line from
docs/OPERATIONS.md makes stage 2 fail naming both files (2026-09-06), and
restoring it is green. Stage 9 skips honestly on the missing delegated `cpu`
controller in that session's scope — a declared host limit, not a pass.
Evidence: issue #85.

### F-027 — the bind-mount regression could pass on an unrelated refusal

Hosted CI at 2b33dbc32 ran the real system pytest and returned 5 (no tests),
while the same regression locally returned 2 because its nested namespace
could not start. The test mounted an executable in ambient PATH but invoked
bare `pytest`; Ranex intentionally resolves bare commands on its pinned system
paths. Neither result established the claimed identity check. Installing system
pytest in CI exposed the old test's incorrect refusal expectation.

The regression now names the mounted executable explicitly and requires the
`same file as` refusal. No production identity check, assertion, timeout or
capability requirement was relaxed. The real upstream Six journey uses the
installed system pytest artifact: 185 required tests passed, ten actual bind
mounts were refused with equal device/inode and link count 1, and the 185 tests
passed again after unmounting. The corrected existing regression file passed
all 5 checks. The adjacent unreadable-directory regression had the same weak
selection and now requires its named unreadable-directory refusal. The expanded
real Six journey passed ten mounted and ten unreadable-directory refusals,
then all 185 required tests again (`executable-journey-2/`). CI runs this journey.
Receipts: `audits/2026-09-05-remediation/executable-journey-1/`,
`bind-fix.xml` and the original `ci-source-failed.log` in the same archive.


### F-024 — relative journal API paths failed during real receipt verification

Verification of the actual cold-start journal at fd13edbc0 raised
`ValueError: relative paths can't be expressed as file URIs` with its relative
archive path; the same database verified by absolute path and yielded head
`sha256:8fc91de7eaf7fb80d4b80a646e0777a2907f2fb6dfa8d5277094e6c6f259e5b4`.
The read-only SQLite URI now absolutizes the path before encoding it, preserving
read-only access and the append API's relative-path behavior. The actual database
then verified through both spellings. Storage stress now checks relative paths
and head equality on every completed 4,000-append round. All five rounds
(20,000 appends) passed at 15a5af5be; receipt: `storage-relative/receipt.json`.


### F-026 — failed journal initialization deferred connection cleanup to GC

Repeated reads of a damaged copy of the actual cold-start database reproduced
1,000 SQLite refusals. Open descriptors grew from 4 to 213 at attempt 500,
then varied as GC ran. `_connect` had not returned when `executescript(_SCHEMA)`
failed, so its caller's closing context never owned the connection. It now
closes initialization failures before re-raising. Repeating the identical
1,000 opens held the descriptor count at 4 at every sampled checkpoint.
Before/after receipts: `damaged-journal-open/receipt.json` and
`damaged-journal-open-fixed/receipt.json` in the remediation archive.
The full storage rerun held FDs at 7 for all 1,000 failed opens, verified another
20,000 appends, and admitted exactly one writer in each of ten eight-way
compare-and-append rounds (70 named stale refusals). Receipt: `storage-final-6b/receipt.json`.



### F-015 (historical subject) — the opt-in live Ranex bootstrap is red

**Remediation 2026-09-05:** The subject now pins the previously audited clean
`be228cacea5789adbfdac71ab34ea469f5504b44` revision and its actual lock digest.
After making the live opt-in controller-only (F-020), the real bootstrap passed:
`RANEX_SLICE035_REAL=1 uv run --frozen pytest -q tests/e2e/test_specification_subject_bootstrap.py::test_real_ranex_bootstrap_or_host_skip`
reported **1 passed in 2161.84 seconds**. Its controller really cloned GitHub,
validated commit/license/lock/issue, ran frozen installation, docs checks and
the full child suite. This compatibility journey does not substitute for the
current remediation's direct host and final regression runs. Evidence:
`audits/2026-09-05-remediation/bootstrap-current-2.xml` and `.log`.

Historical observation retained:

- `RANEX_SLICE035_REAL=1 uv run --frozen pytest -q
  tests/e2e/test_specification_subject_bootstrap.py::test_real_ranex_bootstrap_or_host_skip`
  really clones the configured upstream subject, installs its frozen lock,
  and runs its suite. The child produces 812 passed, 27 skipped, 1 failed;
  the outer bootstrap test fails instead of claiming availability.
- The configured subject is historical commit
  `3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce`. Its bind-mount identity
  security test observes an in-tree executable accepted through a second
  pathname (`RECORDED exit=5`, expected refusal exit 2).
- This does not establish a current or v0.1.0 identity bypass: current
  `main.py:same_file_inside` explicitly removes the faulty link-count
  shortcut, and the current real bind-mount control passes. The stale subject pin makes this claimed live bootstrap red on
  a host that can exercise the attack. No pin or frozen test was changed.


### F-020 — live bootstrap opt-in leaked into the subject environment

The controller's `RANEX_SLICE035_REAL=1` reached the full subject suite, where
it could opt into another bootstrap. The first updated historical run was
cancelled rather than counted as acceptance. The broker now removes that
controller-only flag. Reading the actual replacement subject process's
environment confirmed the flag was absent; no other environment values were
retained. Evidence: `audits/2026-09-05-remediation/bootstrap-current-cancelled.json`
and `bootstrap-current-2-environment.json`. This records a recursion risk and
its boundary fix, not a claim that an unbounded recursive run was observed.

### F-021 — GitHub check publication trusts the receiver host

**Documentation corrected 2026-09-05; live compromise test UNVERIFIED.**
ADR-051 and README claimed a compromised receiver could not forge a green
check. `GitHubClient.create_check_run` authenticates arbitrary check bodies
with the installation token; `check_run_body` sends a conclusion and record
digest, not a signature GitHub verifies. The receiver holds App credentials.
The [version-matched GitHub API](https://docs.github.com/en/rest/checks/runs?apiVersion=2026-03-10#create-a-check-run)
authorizes check creation with Checks write permission. Therefore host/App
credential integrity is required for the GitHub check's authenticity as a
Ranex decision. It is distinct from forging an independently verified signed
Ranex verdict. README now states this boundary and startup-only trust loading;
historical ADRs remain immutable. No live App compromise was attempted.

### F-004 — collection-error junit is refused; the gate journals an observed failure as ABSENCE

**Remediation 2026-09-05:** Actual pytest collection-error XML now retains
its module name and accepts repeated error children belonging to that one
failed collector. The kernel signs the observed failed execution; missing
expected IDs block. The repeated external audit verifies both collection
controls. Failures before pytest produces any report remain named missing
artifact refusals; no unobserved test outcomes are invented. Evidence:
`audits/2026-09-05-remediation/external-2/0/receipt.json`.

Historical observation retained:

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


### F-019 — positive host acceptance helpers fabricated qualification reports

**Remediation 2026-09-05:** Removed the positive cold-start and gating helpers
that assembled and signed successful host qualification reports. Their
replacement builds and installs the actual launcher and executes the catalog's
real host qualification command through `ranex run`. A host missing required
capabilities records the observed reason; it never creates positive evidence.
Cold start: nine passed. Direct capable-host checks: 29 passed, zero skipped.
Evidence: `audits/2026-09-05-remediation/cold-3.xml` and `qualified-2.xml`.
Negative forgery controls remain negative controls, not acceptance evidence.

### F-001 — `Journal.verify()` raises instead of returning False on non-JSON record corruption

**Remediation 2026-09-05:** Closed by deterministic connection cleanup and malformed-record handling in the journal, plus named CLI diagnostics. Two real storage runs replayed actual external gate records for 20,000 appends each; the non-JSON copy returned API False and CLI exit 1. Evidence: `audits/2026-09-05-remediation/storage-stress-2/receipt.json`.

Historical observation retained:

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
- **2026-09-05 correction:** the real CLI probe on v0.1.0 and HEAD exits
  2 with `ERROR  Expecting value: line 1 column 1 (char 0)`, without a
  traceback. The API still raises rather than returning False; the earlier
  CLI traceback claim above is superseded by this executed observation.

### F-007 — failed deliveries are deduped; restart forgets the spool

**Remediation 2026-09-05:** Closed by completion-only durable receipts, cross-process locking and retryable failures. The real public PR #72 replay recovered after a missing Git remote became available, retried an unavailable API, retained 100 completions across SIGKILL, rejected authenticated ID/body conflicts and handled 200 requests across two receiver processes. Evidence: `audits/2026-09-05-remediation/receiver-stress-4/receipt.json`. Live installed App publication remains UNVERIFIED; remote publication and local receipt completion cannot be one atomic transaction.

Historical observation retained:

- Reproduced at `48f3a98e48cf10bc0a4ce24fae7862726b82b1c7` over real TCP,
  a real failing `git fetch`, and a receiver process restart. The first fetch
  failure returns 500; the identical redelivery returns 200 without retrying.
  A previously handled delivery is processed again after restart.
- Anchor: `github_app/receiver.py:process_delivery` adds the ID to `seen`
  before processing; `serve` starts a new empty set without reading the spool.
  ADR-051 promises spooled delivery-ID deduplication. This is separate from
  the deliberately deferred cryptographic anti-replay feature.
- Pins: `tools/dogfood/receiver_audit.py`, cases
  `retry-after-real-fetch-failure` and `dedupe-after-restart`.
- Another incorrect premise in `process_delivery`: GitHub does **not**
  automatically redeliver failed webhooks. Explicit redelivery automation or
  an operator is needed ([GitHub documentation, checked 2026-09-05](https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries)).

### F-008 — an unauthenticated connection monopolizes the listener

**Remediation 2026-09-05:** Closed by bounded concurrent connections and a five-second request-read deadline. Real PR replay stress repeated five rounds of 32 held sockets: at most 33 threads including deadline timers, 22 descriptors, then HTTP 200 after recovery. A trickling socket disconnected after 5.107 seconds. Evidence: `audits/2026-09-05-remediation/receiver-stress-4/receipt.json`.

Historical observation retained:

- Real socket probes: idle connection, incomplete body, and negative
  `Content-Length` each make a second healthy client time out after two
  seconds; releasing the first socket restores successful delivery.
- Anchor: `github_app/receiver.py:build_handler` accepts negative lengths,
  reads the body before authentication without a deadline, and runs on a
  single-threaded `HTTPServer`. `read(-1)` waits for EOF; accepted sockets
  have no timeout. The two-second observation is bounded; the missing
  deadline is also established from source. No claim of a timed infinite run.
- Pin: `receiver_audit.py`, `negative-content-length`, `incomplete-body`,
  `idle-client`. Reachability depends on the operator's proxy configuration;
  the default endpoint is localhost. No internet attack was attempted.

### F-009 — malformed signed payloads escape named refusals

**Remediation 2026-09-05:** Closed by event shape validation and named refusals for malformed signed input, and validated durable receipt shapes. Both receiver boundary reruns verified all 16 controls. Actual PR replay also damaged and restored completion and legacy spool records: HTTP 500 while damaged and HTTP 200 after recovery. Evidence: `audits/2026-09-05-remediation/receiver-after-2/receipt.json` and `receiver-stress-4/receipt.json`.

Historical observation retained:

- A correctly HMAC-signed invalid JSON body and a PR number of `"oops"`
  both produce `RemoteDisconnected`; the receiver logs tracebacks instead
  of a named permanent refusal in the delivery journal.
- Anchors: `github_app/webhook.py:parse_pull_request_event` leaves
  `json.loads` and integer conversion exceptions unwrapped;
  `receiver.py:process_delivery` only catches `WebhookRefusal` there.
- Pin: `receiver_audit.py`, `malformed-json` and `malformed-number`.
  These probes use local audit credentials, not a GitHub installation.

### F-011 — principal retirement is not enforced by run/gate

Follow-through: real clone onboarding exposed producer-only registration
in the CLI instructions and existing journeys. Keygen now prints both current
trust-root entries, README describes merging them without replacing identities,
and the journey helpers attribute their generated keys consistently. The
original refusal is retained as `principal-onboarding-before.json`; the four
real execution/dependency/keygen/gate families then passed 26 checks.

**Remediation 2026-09-05:** Closed by invoking the existing principal catalog consistency and retirement checks during producer and verdict-signer admission. The real external six replay now refuses both run and gate with exit 2 after retiring its actual producer key. Real host onboarding registers matching active worker principals; the 29 direct host checks pass with zero skips. Evidence: `audits/2026-09-05-remediation/external-1/0/receipt.json` and `qualified-2.xml`.

Historical observation retained:

- On HEAD, mark the real producer key retired in the committed `principals`
  block while retaining it in `producers`. `ranex run` still signs a fresh
  successful 185-test external run; `gate evaluate` returns PASS.
- Anchors: `principal_catalog.py` implements retirement and cross-block
  validation, but `producer_keyring.py` does not invoke it and execution
  loads the legacy producer keyring. The new metadata is not enforcement.
- ADR-047 explicitly says the new loader is not yet wired. README's
  completed SLICE-080 wording nevertheless says a retired key authorizes
  none and the two blocks cannot disagree. Those properties currently hold
  only for direct callers of the standalone catalog loader.
- Pin: `release_audit.py`, `retired-principal-key`. Absent from v0.1.0;
  this is a HEAD integration gap, not a released cryptographic break.

### F-014 — an extra tooling test fails outside the default suite

**Remediation 2026-09-05:** Closed in the benchmark harness by fixing pytest rootdir for pristine collection, governed execution and bare execution. Both original agent-produced patches were rerun unchanged: bare GREEN, gate PASS and verified journals. The unchanged tooling guard now passes; historical receipts remain byte-identical and are classified by their observed harness fault. Evidence: `audits/2026-09-05-remediation/benchmark-rerun/divergence.json` and `tooling-check-2.log`.

Historical observation retained:

- `uv run --frozen pytest -q tools/dogfood/test_harness_guards.py` produces
  9 passed, 1 failed. `test_summary_excludes_committed_harness_faults`
  assumes the entire growing archive has zero false blocks; the current
  summary reports two. The default pytest testpaths exclude this module.
- The two archived 2026-09-05 runs (`py-config-parse-ba79feaa` and
  `py-semver-compare-bf46c069`) report green bare tests and governed exit 0,
  but the gate refuses manifest IDs prefixed with the enclosing Ranex
  checkout's `tools/dogfood/...` path. This is consistent with the existing
  F-005 output/root-directory problem; attribution as a kernel false block
  is not established by those receipts.
- No archived evidence or expectations were rewritten to obtain green.
  The failing tooling guard and archive-derived summary are retained as
  audit evidence; this is separate from the kernel's frozen full suite.

### F-016 — delegated-host cold start does not reach PASS

**Remediation 2026-09-05:** Closed in the real acceptance harness by probing the production namespace operation including UID mapping, checking missing build inputs, and executing actual host qualification. Cold start passes all nine stages; all 29 direct qualified-host checks pass without skips. The nested child reports real capability absence rather than claiming the outer host capabilities exist inside it. Evidence: `audits/2026-09-05-remediation/cold-3.xml`, `qualified-2.xml` and the preserved `nested-diagnosis` outputs. This is evidence for these execution contexts, not a portability proof for every host.

Historical observation retained:

- In a clean v0.1.0 checkout under a real systemd user scope with delegated
  `cpu`, `memory`, and `pids`, the cold-start walkthrough's stage 9 fails.
  Its real governed child records 1534 passed, 97 skipped, 11 failed, and
  15 errors; the gate correctly blocks those outcomes.
- The failing child IDs include native-launcher, host-workflow, strict-local
  I/O, and dynamic-runtime journeys. Running selected host journeys directly
  at the corrected HEAD produces 22 passed with no skips. These are distinct
  execution contexts, not contradictory verdicts about identical evidence.
- The released full-run aggregate (1616 passed, 34 skipped, 7 failed) is
  exploratory: its early phase overlapped the historical live bootstrap's
  nested suite. A subsequent **isolated, sequential** cold-start module run
  still produces 8 passed, 1 failed at stage 9. That rerun confirms the
  cold-start failure independently of the overlap.
- Two separate host-workflow failures were traced to test invocation routing
  and fixed as F-017; they must not be counted as established kernel bugs.
- This pins a self-hosting/environment integration failure, not a false
  acceptance. Its complete root cause and portability to other delegated
  hosts remain UNVERIFIED. The audit retains the released full-suite output
  and the gate's exact diagnosis; it does not weaken the prerequisite checks.


### F-017 — capable-host acceptance tests invoked the wrong checkout (fixed in release audit)

- Sequential execution of the current host-workflow, live qualification,
  and bind-mount checks: 5 passed, 2 failed. The v3 workflow and host-drift
  tests provisioned a disposable clone but set `PYTHONPATH` to the parent
  checkout. ADR-009 source-run anchoring then looked for the parent's
  launcher; the drift check reported that missing artifact instead of drift.
- `tests/e2e/test_host_workflow_real.py:_module` now selects the requested
  repository's `src` directory. The nested drift command likewise selects
  the provisioned clone. Explicit test environments remain explicit.
- The same seven real checks then produce **7 passed, no skips**, under a
  fresh delegated systemd scope. No acceptance assertion or manifest ID was
  changed. Receipts retain both the failing and corrected invocations.

### F-013 — Python 3.11 guardian startup contaminated JSON traces (fixed in release audit)

- Clean Python 3.11.15 install: the real execution-family journey produced
  five setup errors because stderr contained `Could not find platform
  dependent libraries <exec_prefix>` before the JSON trace events.
- A real fd-exec control reproduced the warning with argv[0] `python` and
  removed it with the resolved interpreter path, using the same opened
  executable and the supervisor's sealed environment in both cases.
- `process_supervisor.py` now uses the resolved interpreter as argv[0].
  The actual executable remains the already-verified `/proc/self/fd/...`;
  no environment inheritance, signature surface, or trust root is widened.
- Regression evidence is the existing `tests/e2e/test_run_real.py` journey
  run under Python 3.11; final audit receipts record the post-fix result.

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

## Production verification follow-up — issue #88 (2026-09-07)

**Decision unchanged: NO-GO for a claim of verified production operation.**
**Evidence directory:** `tools/dogfood/audits/2026-09-07-production/`.
**Design note:** [ADR-053](../../docs/adr/ADR-053-receiver-durable-ack-and-reconciliation.md).

Four of the 2026-09-06 blockers were local product gaps, reproducible without
credentials. They are repaired and re-probed with the same script against the
same fake API; the rest need the live App and stay UNVERIFIED or UNIMPLEMENTED.

| Blocker (2026-09-06) | Repair | Re-probe (`fault-probes.json`) |
|---|---|---|
| Webhook response deadline | Proven deliveries are spooled before work; the answer waits ≤8 s, then 202; the spool drains at start and every 5 min | Injected 11 s publication: HTTP 202 after 8.0 s; one check published; completion receipt written after acknowledgement |
| Retry after publication | Attempt record + `external_id` on the check; a retry asks GitHub for its own run and republishes nothing | Injected completion-write failure, then retry: 200, **one** check (was two); journal `reconciled:success` |
| App credential file permissions | `load_private_key` refuses group/other-readable or non-regular keys before parsing | Mode 0644 fixture key: `E-GITHUB-KEY-EXPOSED`, no JWT minted |
| JUnit collection skips | A `classname=""` testcase whose only child is `skipped` with message `collection skipped` is retained under its module name, outcome `skipped`; any other unnamed skip is still refused | Unit-tested against the retained Leitir record shape; the Leitir full suite was not rerun |
| Verdict arriving after event | Not implemented; documented as operator redelivery or `ranex github check publish` | Unchanged: fresh event publishes, same-delivery replay does not |

Controls that passed on 2026-09-06 passed again: refusals 401/400/404/413,
lock busy 503 → 200, conflicting replay 409, restart replay 200 with one
publication, 16-connection bound recovered. `receiver_audit.py` reports 16/16
VERIFIED on the changed receiver. Contract tests: `tests/integration/
test_github_receiver_durability.py` (8), key exposure and collection-skip
tests in the security and unit suites.

Still UNVERIFIED (needs the live App, its credentials and a deployment):
authentication, installation, HTTPS delivery, App-pinned merge refusal,
deployment recovery, production load. Still UNIMPLEMENTED: automatic
evaluation/refresh, merge-candidate evaluation, distributed shard
aggregation. Full Leitir/Arxic governed acceptance remains unverified: the
runtime/input provisioning gap is unchanged by this follow-up.

## Production verification — issue #88 (2026-09-06)

**Decision: NO-GO for a claim of verified production operation.**
**Evidence directory:** `tools/dogfood/audits/2026-09-06-production/`.
**Observed:** 2026-09-06. **Tracking:** [issue #88](https://github.com/anthonykewl20/ranex/issues/88).

The kernel has substantial passing evidence. The live App acceptance loop has
not been demonstrated, neither pilot repository requires Ranex's check, and
the tested full-repository workflows did not complete under Ranex. Passing
ordinary application suites or fake-GitHub tests does not close those gaps.

### What actually ran

| Check | Observed result | Scope |
|---|---|---|
| GitHub integration/refusal tests | 45 passed, 16.10s | Local fake API; real Git and HTTP |
| Acceptance mapping, payload, binding and external-repository tests | 22 passed, 7.90s | Local tests; no live App |
| External CLI coverage repair | 2 passed, 8.65s; all previously missing lines 865–873 measured | Same tests, CI-style subprocess coverage; not an additional 2 distinct tests |
| Leitir ordinary full suite | 3,742 passed, 159 skipped, 4 warnings, 930.67s | Python 3.12.3, pytest 9.0.3; offline/default suite |
| Arxic ordinary full suite | 1,974 passed, 234 files, 1434.31s | Node 24.18.0, pnpm 11.17.0, Vitest 4.1.11, Playwright 1.62.1; Docker available |
| Arxic lint and type checks | Lint, root typecheck and recursive package typechecks exited 0 | Same disposable checkout |
| Leitir full suite under Ranex | 22 failed, 3,735 passed, 144 skipped; freeze exit 2 | External-venv command; runtime changed and the JUnit reader refused a collection-skip record |
| Arxic full suite under Ranex | Startup refusal; freeze exit 2 | Committed Vitest config could not resolve `vitest` in the materialized tree; no results artifact |
| Final integrated Ranex regression/CI | Exact final SHA and result recorded in issue #88's closing evidence | The earlier PR's tests passed but its changed-line coverage gate failed; that failure is retained |

The ordinary repositories were copied **locally** into disposable checkouts.
The original working files were not changed. Source identities:

- Leitir: `bfcbcd83718ad1466ea9dd9d1d9ebb4915417517`.
- Arxic: `2395041598cf2aab14da8708ac2b21dc08f40731`.
- Runtime code observed by the probes: `7cc4ce7ae2daf0de8f062af59e87900d316119a3`,
  integrating the external-repository change with `v0.1.005`.

Arxic was tested on Node 24, not its CI-pinned Node 22.22.0. Its separate
packaging, worker-image build and all hosted CI jobs are not established by
the local Vitest result. Leitir's skipped optional parser/auth/MCP and live
provider cases are not counted as passes. These are application baselines,
not signed full-suite Ranex acceptance verdicts.

### Release blockers and operational limits

| Area | Evidence | Requirement before sign-off |
|---|---|---|
| Live App identity and installation | App ID/key/secret environment variables absent; browser discovery empty; OAuth installation discovery refused | Identify the actual App, authenticate as it, verify its permissions and installations on both repositories |
| Merge enforcement | Both repositories have no rulesets and no required `ranex/acceptance` check; no Ranex check at the tested heads | App-pinned rule; demonstrate blocked missing/failing/wrong-source checks and accepted valid evidence on an isolated test branch |
| Webhook response deadline | Injected 11s publication delay produced a real HTTP response after >11s | Acknowledge durably within GitHub's deadline and process independently of remote latency; verify crash recovery |
| Verdict arriving after event | Initial `action_required`; same-delivery replay remains unchanged; a fresh event publishes success | Demonstrate automatic evaluation/refresh or a documented, tested operator refresh contract |
| Retry after publication | Injected completion-write failure followed by retry created two successful checks | Document at-least-once behavior and demonstrate reconciliation/idempotent publication; no exactly-once claim |
| Python runtime preservation | Requested venv reports pytest 9.0.3 normally; governed probe reports `/usr/bin/python3.12`, `/usr`, pytest 7.4.4 | Reviewed dependency/runtime provisioning and a successful full-suite run; do not treat the two environments as equivalent |
| Full-repository execution inputs | Leitir failures include subprocess imports and history-dependent changelog checks; Arxic config cannot find installed Node dependencies | Declare/provision the necessary execution inputs without weakening source, command or result binding; rerun full acceptance |
| JUnit collection skips | Actual pytest output contains `classname=""`, `name="tests.test_query_probe_live"`, with a collection skip; Ranex rejects it | Define and test collection-skip identity semantics while preserving missing-test and undeclared-skip refusal |
| App credential file permissions | A temporary mode-0644 App key was accepted and minted a verifiable JWT | Verify production key ownership, directory access and permissions; no claim that App key loading enforces mode 0600 |
| Merge candidates and distributed evidence | PR-head publisher; no merge-group evaluation or shard aggregation demonstrated | Implement/test these before advertising them; head-only evidence cannot establish merge-candidate acceptance |
| Deployment operations | No accessible receiver deployment or live delivery history | Verify TLS, supervised restart, durable-state backup/restore, secret/token rotation, redelivery, monitoring and a representative soak |

GitHub requires webhook responses within 10 seconds and recommends asynchronous
processing when needed. Failed deliveries require redelivery; same-delivery
deduplication is not a late-verdict refresh mechanism.
[GitHub webhook guidance](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks).
App-pinned required-check fields are documented in the
[versioned rules API](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10).

The permission probe used only a disposable fixture key. Mode bits alone do
not establish effective exposure through restrictive parent directories or
ACLs. No production credential was read or emitted by these probes.

### Controls that passed in local fault injection

`fault-probes.json` records actual statuses and observations, with the fake API
and injected faults explicitly identified:

- Unsigned/tampered deliveries: 401; invalid delivery ID: 400; wrong endpoint:
  404; oversized declared body: 413. No check was published.
- Held receiver file lock: 503; retry after release: 200 and one publication.
- Conflicting body for a completed ID: 409. Restarted-state replay: 200,
  retaining one publication.
- Sixteen incomplete requests occupied the connection limit; overflow was
  rejected; all sixteen slots recovered after the read deadlines.

These controls prove the exercised local paths, not production uptime or
GitHub-origin delivery. A focused 45-test coverage measurement covered 83%
of the GitHub modules; it is not a claim of exhaustive branch coverage.

### Reproduction and retained material

From the Ranex checkout:

```sh
uv run --frozen python tools/dogfood/probe_github_production.py --output /tmp/ranex-production-probes.json
```

The probe uses the repository's existing fake-GitHub fixture and real local
Git/HTTP. Its successful exit means observations were collected, not that
production readiness passed. It requires no production credentials.

`github-preflight.json` retains read-only live configuration responses.
`repository-runs.json` retains exact commands, source and runtime identities,
exit codes and scope. `junit-compatibility.json` retains the actual refused
collection record. Compressed logs and JUnit documents retain the ordinary
full-suite results and governed failures. `archive-index.json` records raw
and compressed SHA-256 digests. The prior PR's failed CI log is retained;
the repair preserves the existing 100% changed-line coverage threshold.

**Investor-demo boundary:** the current defensible demonstration is the
bounded signed-evidence/refusal/recovery workflow already retained in the
external pilots. A live, automatically refreshed, enforced full-repository
GitHub App demonstration remains unverified. This assessment does not
authorize describing that workflow as production verified.
