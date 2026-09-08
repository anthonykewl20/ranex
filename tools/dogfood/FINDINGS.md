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

## Closed

### F-005 (CLOSED 2026-09-09, item 1; item 2 unchanged) — journal needs an independent history anchor

- **Item 1 closed by ADR-057 (#93).** `Journal.verify()` concedes in its own
  docstring that it detects inconsistent edits, not a complete replacement or
  truncation of a self-consistent chain. Pinned as an executable assertion:
  `test_a_complete_rewrite_still_passes_plain_chain_verification` — a fully
  rehashed replacement history and a truncated prefix both return
  `chain=verified`. That test must keep passing; if it fails, the chain gained
  a property it does not claim.
- The anchor: `Journal.append` already returned the chain link it created and
  `GateEvaluator.evaluate` discarded it. The published verdict now signs it as
  `journal_head`, so the anchor lives *outside* the journal in a record signed
  by the **verdict signer** — a different key from the journal writer.
  `journal verify --against-verdict <path>` reads the head from a verdict it
  **verifies**, never from raw bytes; an attacker who can rewrite the journal
  can edit an unsigned file beside it, and that would anchor the chain to
  itself. The rewrite the chain accepts is refused against the anchor.
- **A defect introduced and repaired inside this fix, on the record:** the
  first cut bumped the signing domain and refused every older payload type,
  citing ADR-011's evidence v2→v3 precedent. Measured against the real
  Leitir/Arxic pilot receipts under `audits/2026-09-06-external/`, that made
  `tools/dogfood/verify_repository_pilot.py` refuse signed archived verdicts
  that cannot honestly be re-signed — destroying the audit trail the anchor
  was meant to protect. Repaired with version-aware verification: v1 verifies
  against its own domain and field set and reports **no anchor**; it cannot be
  used by `--against-verdict` or check publication. Reading is allowed;
  deciding is not; a downgrade buys nothing. Regression pinned against the
  real committed receipts:
  `test_a_real_archived_v1_verdict_still_verifies_and_carries_no_anchor`.
- Residual, stated not glossed: an operator holding both the journal and the
  verdict signing key can still rewrite consistently. No external witness.
  That is where a transparency-log anchor attaches; it is not claimed closed.
- Prior art: sigstore-python 3.6.1 `_internal/rekor/checkpoint.py`
  (`LogCheckpoint`, `SignedNote`, `verify_checkpoint`) — the signed-tree-head
  shape, adopted. Its `verify_checkpoint` trusts `rekor_keyring`, the log's own
  key; Ranex signs the head with a different key and retains it outside the log.
- **Item 2 unchanged:** the "0 false verdicts" agreement claims remain point
  estimates; the honest wording is a Clopper-Pearson upper bound.
- Earlier history retained: 2026-09-05 `--expected-head` (operator-retained
  anchor), the 2026-09-03 audit source, the closed canonical-JSON and
  `argv[3]` items.

### F-002 (CLOSED 2026-09-08) — session/location-dependent skip arms are now explicitly declared

**Remediation 2026-09-08 (issue #91):** the disposition the findings review
named — making the skip list explicit — is delivered as two new context-tier
declarations plus the paired measurement that verified coverage. Full-suite
runs of the same commit from different launch contexts on one host split the
outcome set exactly as the 2026-09-03 observation recorded: a delegated
systemd scope (cpu/memory/pids controllers) ran the host-gated arms green
(retained operator logs: 1812 passed / 62 skipped, fresh clone and main
checkout), while a plain non-delegated shell skipped them — and two of those
skips were UNDECLARED:
`tests/e2e/test_gating_real_suite.py::test_stage_08b_criterion_14_the_suite_passes_and_the_gate_accepts`
and
`tests/e2e/test_gating_real_suite.py::test_slice009_repository_gate_fails_when_a_manifest_test_is_deleted`
skip mid-test at `record_host_qualification`'s `qualified_host` probe when
the session's delegated cgroup lacks a controller (observed live: "the
delegated cgroup is missing required controllers: cpu"). Both arms are now
declared `ranex-context:host-capability:` (166 → 168 declarations) — the
tier the cross-check reports but never byte-compares — so a plain shell, a
delegated scope, a fresh worktree and the sealed freeze all observe declared
skips only. The finding's open counting question is answered: `suite freeze`
never counts observed skips — `freeze_manifest` freezes the observed junitxml
ID set and carries the `--expected-skip` declarations verbatim — so the
manifest's total is the declaration count across contexts (host-capability
71, hermetic-freeze 87, delegated-scope 4, fanout-gated 1, operator-action 2,
probe-backed signing_key 3), never one run's skip count; the historical
166-vs-34/59 divergence was the manifest describing several contexts at
once, which is its design. Final-commit verification in both session shapes
is recorded in issue #91. No kernel file changed.

Historical observation retained (2026-09-03, commit edf1a98605):

- main checkout: 1657 collected, 1623 passed, 34 skipped, exit 0; fresh
  worktree: 1657 collected, 1598 passed, 59 skipped, exit 0 — 25 tests
  passed in the main checkout and skipped in the fresh worktree, attributed
  to untracked local state.
- Methodology note (binding): ADR-046 serialized cgroup probes; parallel
  full-suite runs on one repo remain invalid by construction. The 2026-09-08
  measurement additionally observed five confinement-journey setup ERRORS in
  a contended worktree run: a concurrent session's host-probe mutations
  moved shared session cgroup placement inside the journey's probe window
  (the frame probe said qualified; the session command then refused
  E-C18-GATE "delegated cgroup lacks controllers: cpu"). Those are
  contention artifacts of the unserialized window, not location semantics;
  the serialized session-shape runs are the evidence of record.

### F-010 (CLOSED 2026-09-08) — ordinary non-strict XPASS received gate PASS

- Original observation, unchanged: reproduced with released v0.1.0
  (`edf1a98605`) and HEAD (`48f3a98e48`) on the pinned external
  `benjaminp/six` repository — the actual pytest run reports **184 passed,
  1 xpassed**, then Ranex recorded exit 0 and gate PASS. Strict XPASS, XFAIL,
  undeclared skip and deselection controls all blocked.
- Re-measured 2026-09-08 against the installed pytest to find the cause in the
  bytes rather than in the parser. A non-strict XPASS is written as
  `<testcase classname="test_xp" name="test_nonstrict_xpass" time="0.001" />`
  — a bare element with no outcome child, byte-identical to an ordinary pass.
  The enclosing `<testsuite>` carries `failures="0" errors="0"` and does not
  count it in `skipped` either. `foundation/suite_results._outcome` reads
  `passed` because the outcome is absent from the artifact, not because the
  branch is wrong. No parser change could have closed this.
- Closed by ADR-056: the outcome has to be requested before the artifact is
  written, so it is required in the one thing the kernel already binds and
  digests — the claim's argv. A `pytest-junit` suite claim must carry the exact
  adjacent tokens `-o xfail_strict=true`, and the gate loader refuses at
  construction otherwise. The same XPASS is then written as
  `<failure message="[XPASS(strict)] ...">`, which the **unchanged** summariser
  already classifies as `xpassed`. `evaluate()` did not move; `KERNEL_DIGEST`
  did not move; no stdout heuristic and no fabricated outcome were added.
- Also refused by name, each measured rather than assumed, because each makes
  the reporter blind again with the override still set: `--runxfail`;
  `-p no:skipping` in any spelling, matched on the plugin name rather than an
  enumerated list (this one unloads xfail **and skip**, so a declared
  `@pytest.mark.skip` becomes a bare pass and "a skip is absence" fails
  outright); `-o xfail_strict=false`; a second,
  later override; a bare `xfail_strict=true` with no preceding `-o`; and the
  pair placed after a `--`.
- `governance/gates.yaml` now carries the binding, so the repository's own
  landing gate no longer has the finding.
- Pins: `tests/security/test_slice009_strict_xfail_binding.py` (the refusals)
  and `tests/unit/test_suite_results.py::test_a_non_strict_xpass_is_only_visible_when_the_argv_asks_for_it`
  (the reporter half, run against the installed pytest, not a hand-written XML
  fixture). `release_audit.py`'s `nonstrict-xpass` versus `strict-xpass`
  scenarios remain the external-subject arm.
- Boundary restated, not closed: a hostile tree can still forge the artifact via
  `conftest.py` or an approved `pytest11` plugin (ADR-007, ADR-011 criterion 10,
  F-012). This closes an honest-process blind spot; it moves no trust boundary.
- `vitest-junit` claims are unaffected and are not asked for an equivalent:
  Vitest's `test.fails` already fails a test that unexpectedly passes.

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

## Receiver retry storm after restart — F-037 (2026-09-08)

**Observed in hosted CI** on `45a842d80` (`receiver_stress.py`,
`restored-reviewed-catalog`: HTTP 503 on the first delivery after a restart;
passed locally on a faster host). Since F-035 every delivery without a
verdict leaves an awaiting head; the startup pass (ADR-053/054) re-bound and
re-published each of them, refused by the API each time, holding the
pipeline while the live delivery arrived. The same held for spool entries
that answer 5xx: each restart and each periodic pass re-ran a real Git
fetch per stuck entry.

**Fix, two parts.** (1) Priority: a live delivery that finds the pipeline
held by a startup/periodic pass waits for it, bounded by the acknowledgement
deadline, instead of answering 503; the pass yields after the entry in
flight (a waiting delivery, or its own 503 against a live holder) and
resumes 0.1 s after that delivery instead of resting the full interval. Two
live deliveries still never wait for each other. (2) Backoff: a failed
attempt writes a `.failed` marker beside the entry (spool or awaiting);
both passes skip entries whose marker is younger than `SPOOL_RETRY_SECONDS`,
restart or not. 503 writes no marker. Never-attempted entries still drain
at startup, so crash recovery is unchanged; markers leave with their entry.
Backoff alone did not fix the stress run: the first attempt after a restart
still blocked the 100 post-restart replays (`sigkill-restart-retains-100-
completions` 503). Contract-tested in the existing durability and refresh
arms (the race and the demand yield both pinned); `receiver_stress.py` rerun
locally, receipt retained in `audits/2026-09-08-receiver/`.

## Live App verification — issue #88 (2026-09-08)

**Evidence directory:** `tools/dogfood/audits/2026-09-08-live-app/`.
**App:** `ranex-gate` (4863198), owner `anthonykewl20`, installation 159825611,
created through `ranex github register`'s manifest handshake and installed by
the owner. All observations below are against **real GitHub** — no mock.

- **Authentication**: App JWT accepted by `GET /app` (live identity confirmed).
- **HTTPS delivery**: GitHub → smee.io (public HTTPS) → listener; HMAC
  verified on every delivery; real delivery ids journal and stamp `external_id`.
- **Live PR journey**: PR → `ranex/acceptance` `action_required` → gate run →
  signed PASS verdict → periodic pass `refreshed:success` → GitHub check
  `success` (stamped `refresh:<head>`).
- **App-pinned merge refusal**: ruleset (`required_status_checks`,
  `integration_id` 4863198, `refs/heads/main`) blocks the merge with HTTP 405
  while the required check is `action_required`.
- **Wrong-source attack defeated**: a GitHub Actions job literally named
  `ranex/acceptance` reporting `success` does NOT satisfy the rule — the pin
  requires the check from this App. Merge stayed 405 until the App's own
  check turned `success` behind a signed verdict, then the merge succeeded.
- **Redelivery replay**: GitHub's own `POST /app/hook/deliveries/{id}/attempts`
  → listener journaled `replayed`, no duplicate check published.
- Operational notes: the first App (4863112, slug `ranex-acceptance`) was
  created under TonyGarces because the browser profile used for the Create
  click was logged in as that account; it is unused and can be deleted.
  Rulesets require a public repo on a free plan — the probe repo was made
  public. A private-repo/Pro deployment keeps the same pin semantics.

Still UNVERIFIED: a multi-hour production soak (the 20-delivery live soak ran
at ~1.4 s/delivery), supervised-deploy restart under real traffic, secret
rotation, and full Leitir/Arxic governed acceptance. Automatic evaluation,
merge-candidate checks and shard aggregation remain unimplemented (the App
still publishes only what `gate evaluate` produced).

## Live App calibration — issue #88 (2026-09-07, pre-App)

**Evidence directory:** `tools/dogfood/audits/2026-09-07-live-app/`.
**Scope:** real network paths — the public smee.io HTTPS channel, real
`api.github.com` publication attempts, real `git fetch` from GitHub, the
real listener process — with pre-App credentials (App id 000000), so live
publication is refused by GitHub by design. **No mock GitHub anywhere in
this pass.** No live App identity existed on the host at observation time.

- **F-035 (fixed, live-reproduced):** a head whose `action_required`
  publication was refused (API outage at event time) was never written to
  `awaiting/`, silently losing ADR-054's refresh. Reproduced live as
  `live-absent-verdict-1` (journal `E-GITHUB-API-REFUSED`, no marker);
  fixed by remembering the head before `publish_check`
  (`src/ranex/github_app/receiver.py`), regression-tested red-first in
  `tests/integration/test_github_awaiting_survives_refusal.py`, and
  re-verified live (`live-absent-verdict-2-fixed`: marker present).
- **F-036 (operational):** the receiver's state dir lives inside the
  operator clone; once tracked, every `deliveries.jsonl` append dirties the
  governed tree and `ranex run` refuses to record evidence. Keep the state
  dir untracked and gitignored in any clone that runs the listener.
- The full pipeline ran live to the publication boundary: HMAC-verified
  delivery through smee → real head fetch → binding → verdict resolution →
  real `api.github.com` POST → refused (fake App id) → journaled refusal.
- Verified live: 401 unsigned/tampered, 404 wrong endpoint, 413 oversized,
  foreign-repo ignore + same-id replay no-op, SIGKILL crash recovery with
  startup spool drain, 16-connection bound with rejection and recovery,
  and the ADR-054 refresh loop (verdict lands → periodic pass fires →
  `refresh-failed` while the App is fake → marker kept for retry).
- Probe harness note: smee-client re-serializes JSON bodies; only compact
  (JSON.stringify-shaped) deliveries keep a valid HMAC. GitHub itself
  always posts compact JSON.
- **Still blocked on the owner:** GitHub App creation is web-only and no
  anthonykewl20 browser session exists on this host. The manifest form is
  staged at `http://127.0.0.1:8081/` with the conversion catcher armed;
  one owner click completes registration, after which installation, the
  App-pinned ruleset, the live PR journey and merge enforcement proceed.

## Production verification follow-up — issue #88 (2026-09-07)

**Decision unchanged: NO-GO for a claim of verified production operation.**
**Evidence directory:** `tools/dogfood/audits/2026-09-07-production/`.
**Design notes:** [ADR-053](../../docs/adr/ADR-053-receiver-durable-ack-and-reconciliation.md), [ADR-054](../../docs/adr/ADR-054-late-verdict-refresh.md).

Four of the 2026-09-06 blockers were local product gaps, reproducible without
credentials. They are repaired and re-probed with the same script against the
same fake API; the rest need the live App and stay UNVERIFIED or UNIMPLEMENTED.

| Blocker (2026-09-06) | Repair | Re-probe (`fault-probes.json`) |
|---|---|---|
| Webhook response deadline | Proven deliveries are spooled before work; the answer waits ≤8 s, then 202; the spool drains at start and every 5 min | Injected 11 s publication: HTTP 202 after 8.0 s; one check published; completion receipt written after acknowledgement |
| Retry after publication | Attempt record + `external_id` on the check; a retry asks GitHub for its own run and republishes nothing | Injected completion-write failure, then retry: 200, **one** check (was two); journal `reconciled:success` |
| App credential file permissions | `load_private_key` refuses group/other-readable or non-regular keys before parsing | Mode 0644 fixture key: `E-GITHUB-KEY-EXPOSED`, no JWT minted |
| JUnit collection skips | A `classname=""` testcase whose only child is `skipped` with message `collection skipped` is retained under its module name, outcome `skipped`; any other unnamed skip is still refused | Unit-tested against the retained Leitir record shape; the Leitir full suite was not rerun |
| Verdict arriving after event | Implemented (ADR-054): a head answered `action_required` is remembered; the periodic pass re-reads the verdict store and publishes once a verdict exists, stamped `refresh:<head>` and reconciled if interrupted | Verdict copied after the event: `refresh_awaiting` publishes `success`, the head is forgotten; same-delivery replay still publishes nothing |

Controls that passed on 2026-09-06 passed again: refusals 401/400/404/413,
lock busy 503 → 200, conflicting replay 409, restart replay 200 with one
publication, 16-connection bound recovered. `receiver_audit.py` reports 16/16
VERIFIED on the changed receiver. Contract tests: `tests/integration/
test_github_receiver_durability.py` (8), key exposure and collection-skip
tests in the security and unit suites.

Still UNVERIFIED (needs the live App, its credentials and a deployment):
authentication, installation, HTTPS delivery, App-pinned merge refusal,
deployment recovery, production load. SLICE-085 / ADR-055 made App
creation, 0600 credential storage and the App-pinned ruleset operable
from `ranex github register|status|ruleset`; those commands are tested
against the fake API only. Still UNIMPLEMENTED: automatic evaluation
(the App still publishes only what a gate run produced), merge-candidate
evaluation, distributed shard aggregation. Full Leitir/Arxic governed
acceptance remains unverified: the runtime/input provisioning gap is
unchanged by this follow-up.

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

## GitHub App audit — 2026-09-08

Issue: #88. Scope: the eight `src/ranex/github_app` modules, GitHub CLI
integration, existing security/durability tests, operator documentation,
real-PR receiver stress, and live App publication/recovery.
This is an evidence-backed review, not proof that all possible bugs are absent.

### Findings repaired

| Finding | Failure | Repair and regression evidence |
|---|---|---|
| Revoked refresh authorization | A queued late verdict could publish after its repository was removed from the allowlist | Recheck the current allowlist before any refresh API call; journal and forget revoked work; regression proves no network request |
| Durable retry loss | Fast HTTP 500/503 deleted the spool; GitHub does not automatically retry | Retain failed entries; back off failed attempts; HTTP outage/contention/restart regression in `test_github_receiver_durability.py` |
| Incomplete API listings | Installations/rulesets stopped at 30, checks at 100 | Numbered pagination, 100 per page; refuse beyond a bounded 1000 pages instead of silently returning partial results; 105-item HTTP tests |
| Reconciliation filter | Default `latest` can hide the delivery's earlier check | Request `filter=all` with App/name filters on every page |
| Ruleset false assurance | Same App ID credited disabled, evaluation-only, wrong-branch, excluded-branch, bypassable or non-strict rules | Reuse only matching active strict scope without bypasses; preserve custom rules and create the requested rule; status ignores disabled/non-branch rules; later foreign pins still refuse |
| Wrong signing key | Valid non-RSA PEM loaded, then signing raised an unclassified TypeError | Validate RSA key type with installed cryptography 50.0.0; named credential refusal |
| Malformed API response | Invalid/deep JSON and truncated HTTP bodies escaped the retryable-error boundary | Convert parser and HTTP protocol errors to named API refusals; bound error-body reads; real truncated-HTTP regression |
| False test evidence | Fake API listed failed POSTs as completed checks | Track successful publication separately from attempted requests |

The stress harness's old expectation that HTTP 500 deletes the spool was also
corrected. The first audit run stopped at that obsolete assertion; the rerun
passed all 41 cases. No runtime dependency was added.

### Fresh evidence

Retained receipts: `tools/dogfood/audits/2026-09-08-app-review/`.

- `receiver_stress.py`: 41/41 checks; actual PR #72 data, 1000 replay requests,
  restart, two-process state sharing, signature/framing attacks, resource
  saturation, paused Git fetch, and recovery. Local signing credentials and
  a real unavailable API endpoint; this alone does not prove live publication.
- `live_receiver_recovery.py`: current GitHub PR #1 in the dedicated
  `anthonykewl20/ranex-app-live-probe` repository, real App 4863198 and
  installation 159825611. HTTP 503 under actual lock contention; queued body
  survives server shutdown; fresh receiver state publishes one successful
  App check; a second drain produces no duplicate.
- Live ruleset GET and setup reuse: `live-ruleset.json`; verified `existing`
  with GitHub's actual added default fields, no mutation or merge attempt.
- Live check: https://github.com/anthonykewl20/ranex-app-live-probe/runs/102017776260.
  Uses an existing verified signed verdict. The replay is locally HMAC-signed
  from actual API data; it is not a fresh GitHub-originated webhook or a new
  governed test observation.
- These initial receipts identify the pre-change base commit; they exercised
  the working-tree patch. They must not be attributed to the base commit alone.
- Mandatory final-commit `uv run --frozen pytest -q` evidence belongs in the
  single issue closing comment. Skipped host/optional cases are UNVERIFIED.

### Chock comparison and remaining work

Compared with the [published Marketplace description](https://github.com/marketplace/actions/chock-governance-check),
not with an executed Chock installation. Chock advertises policy compilation
into agent/git/CI hooks, a policy catalog, lock/evaluation tooling and coverage
reporting. Ranex's implemented App publishes signed, tree-bound verdicts and
can pin the check's App identity in a ruleset. Those are different capabilities;
this audit does not establish overall superiority or feature parity.

Still UNIMPLEMENTED: automatic App-side evaluation, merge-group/candidate
checks, distributed shard aggregation, and a Chock-equivalent multi-agent
policy compiler/catalog. These require separately specified product work.
Still UNVERIFIED: supervised production deployment under traffic, multi-hour
soak, credential rotation, operational backup/restore, and full governed
Leitir/Arxic acceptance. Prior live HTTPS/merge-enforcement evidence remains in
`audits/2026-09-08-live-app/`; it was not repeated by this recovery probe.
No production sign-off is issued; slice 085 and issue #88 remain open.

### API and implementation references

- [Failed delivery behavior](https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries).
- [Checks API, 2026-03-10](https://docs.github.com/en/rest/checks/runs?apiVersion=2026-03-10#list-check-runs-for-a-git-reference): `filter`, `page`, `per_page`, `app_id`.
- [App installations API, 2026-03-10](https://docs.github.com/en/rest/apps/apps?apiVersion=2026-03-10#list-installations-for-the-authenticated-app).
- [Rulesets API, 2026-03-10](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10).
- Installed cryptography 50.0.0: `hazmat/primitives/asymmetric/rsa.py`,
  `RSAPrivateKey.sign`; existing serialization loader and RSA type reused.

The first final-revision full run exposed the frozen `main.py` integrity pin:
its governed child reported 1 failed, 1729 passed, 140 skipped. The sole failure
was `test_gate10_production_entrypoint_adr_and_risk_remain_frozen`. Review of
the CLI diff confirmed only the two-line inactive-ruleset status filter changed;
the recorded SHA-256 was refreshed using the established pin-update convention.
The integrity assertion and confinement implementation remain intact. The
focused gate9/gate10 checks then passed; final full-suite evidence remains in
the issue closing comment.

A later full run exposed an intermittent delegated-session admission failure:
`test_session_and_qualify_concurrently_in_one_fresh_delegated_scope_both_succeed`
refused `E-C18-HOST-DRIFT` while qualification succeeded. Session admission read
the current cgroup before taking the shared host-probe lock, allowing it to
observe qualification's temporary controller leaf. Both admission snapshots now
take the existing lock. A deterministic regression models temporary relocation
and verifies that actual delegation drift still refuses before launch. The
isolated pre-fix concurrency rerun passed, so that rerun alone was not credited
as a fix. This repair changes session admission synchronization; it does not
change the frozen evaluation kernel or weaken host identity validation.

The subsequent full run completed with 1835 passed, 37 skipped and two stale
freeze-artifact failures: the regression additions changed the inventory from
1861 to 1874 tests. The existing real sealed `suite freeze` journey regenerated
the canonical manifest and normalized transcript with `run_exit=0`; all 166
expected-skip declarations were preserved verbatim. No freeze assertion was
relaxed. Final-commit full-suite results supersede this intermediate run and
are recorded in the issue closing comment.

Concurrent validation also exposed a lifecycle-test attribution error: both
SIGKILL arms observed their own descendants gone, their exact materialisation
removed and no evidence published, but failed because a different run created
another `/tmp/ranex-subject-*` tree during the observation window. The test now
attributes cleanup to the exact materialisation obtained from its real pytest
descendant, retaining process, scratch and evidence assertions. A global
temporary-directory delta is not evidence that this invocation leaked a tree.
This repair changes only the test observer, not lifecycle cleanup behavior.
