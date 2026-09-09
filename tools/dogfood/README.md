# Ranex dogfood — training and benchmarking loop

## Release audit probes

The first-party external-repository receipts in `audits/2026-09-06-external/`
retain the source patch, public policy/keyring, frozen manifest and signed
verdict. Verify an archive against an existing local source repository:

```sh
uv run --frozen python tools/dogfood/verify_repository_pilot.py \
  --receipt tools/dogfood/audits/2026-09-06-external/leitir.json \
  --repository /path/to/leitir
```

Use `arxic.json` and the local Arxic checkout for its archive. The verifier
reconstructs the exact tree using a temporary Git index, compares the archived
policy files with that tree and uses Ranex's verdict reader. It changes no
checkout or branch. Signature validity under an included key does not establish
independent trust in that identity, rerun the tests or prove GitHub enforcement.

The owner-requested 2026-09-05 audit adds real subprocess and socket probes.
The retained [audit summary](audits/2026-09-05/audit.json) links the measured
revisions, outcomes, scope limits, and artifact inventory; [FINDINGS.md](FINDINGS.md)
explains the reproduced gaps. Public signature material is retained; private
keys are discarded with the disposable repositories.
Run with a **new** output directory each time:

```sh
uv run --frozen python tools/dogfood/release_audit.py --out /tmp/ranex-release-audit
uv run --frozen python tools/dogfood/receiver_audit.py --out /tmp/ranex-receiver-audit
```

`release_audit.py` checks the released `v0.1.0` tag and current HEAD separately.
It reuses `external_proof.py` to install each frozen checkout, vendor its
byte-verified kernel into pinned `benjaminp/six`, and freeze that repository's
185 passing tests (the full bare run collects 200, with 15 genuine skips).
It then runs positive, broken-code, signature, command, policy, absence,
skip/xfail/xpass, hostile-reporter, and journal-tampering controls. OpenSSL
independently verifies the real observation's Ed25519 signature. These are
process executions on actual files and Git/SQLite state; no kernel seam is
mocked. The hostile hook is an explicit attack on real failed assertions.

`receiver_audit.py` starts the production receiver in another process, sends
real HTTP requests, restarts it, and probes a real unavailable Git remote.
It uses locally generated audit credentials and publishes no GitHub checks.
Live GitHub App authentication, ruleset enforcement, and PR delivery remain
UNVERIFIED by this probe.

Each program writes machine-readable receipts and exits 0 only when its
expectations all hold, 1 for reproduced gaps, or 2 for incomplete execution.
**GAP is not PASS.** Some expectations deliberately test documented residual
boundaries, including hostile reporters and unanchored history. The receipt
names these separately from claimed defenses. Neither program is evidence of
general software correctness, exhaustive input-space coverage, or strict-local
confinement; the separate real host suites own those checks. Private keys and
scratch repositories are removed after the run; public verification material
and captured commands/results remain in the output directory.

Run host-dependent suite comparisons sequentially, as F-002 requires. The
existing full frozen pytest suite is still mandatory in addition to these
probes. Findings and scope limits are recorded in [FINDINGS.md](FINDINGS.md).

Dogfooding ranex with ranex's own deterministic outputs. The loop's only
inputs are the installed kernel, the committed artifacts (`uv.lock`,
`governance/deps.yaml`), and byte-stable facts — no assumptions, no
hallucinated behaviour, no timing data in correctness records. The source of
truth is the code; `capabilities.json` holds the verified inventory with
file:line anchors.

The repeatable stress tools consume actual upstream pull requests and journals:

```sh
gh api repos/anthonykewl20/ranex/pulls/72 > /tmp/ranex-pr-72.json
uv run --frozen python tools/dogfood/receiver_stress.py --pull-request /tmp/ranex-pr-72.json --out .local/receiver-stress
uv run --frozen python tools/dogfood/storage_stress.py --journal /path/to/actual-gate.sqlite3 --out .local/storage-stress
uv run --frozen python tools/dogfood/release_check.py --out .local/release-check
uv run --frozen python tools/dogfood/collection_journey.py --out .local/collection-journey
```

Use the owner's active GitHub account for the read above. Each output directory
must be new. Receiver replay uses real CLI processes, TCP, Git and durable
receipts; its generated local App credentials do not prove live publication.
Storage load repeats actual gate records across threads/processes, then attacks
copies of the resulting databases and checks an independently retained head via
the CLI. Repeated records measure storage, not new code correctness observations.
Storage defaults to five rounds of 4000 appends; `--rounds 25` increases the
same alternating eight-thread/eight-process workload to 100,000 appends.
Its receipts record the actual Python/SQLite runtime and CPU affinity, missing
append-only trigger recovery, damaged-header descriptor use and CAS results.
Preserved remediation receipts are in `audits/2026-09-05-remediation/`; earlier
failed attempts remain there alongside successful reruns.

The release check builds and installs actual candidate wheels. The collection
journey onboards the pinned six repository, observes its real passing tests,
breaks the actual test module's import, requires a named collection failure and
all absent manifest IDs, then restores the module and requires gate recovery.
Run that governed journey sequentially with other confinement work. CI retains
coverage from its vendored kernel only after comparing every Python source file
with this checkout; historical or modified source cannot supply its line hits.

## Commands

    uv run --frozen python tools/dogfood/dogfood.py capabilities
    uv run --frozen python tools/dogfood/dogfood.py list
    uv run --frozen python tools/dogfood/dogfood.py run [--filter SUBSTR]
    uv run --frozen python tools/dogfood/dogfood.py baseline
    uv run --frozen python tools/dogfood/dogfood.py iterate
    uv run --frozen python tools/dogfood/dogfood.py drift
    uv run --frozen python tools/dogfood/dogfood.py bench [--repeat N] [--output FILE]
    uv run --frozen python tools/dogfood/dogfood.py train classify
    uv run --frozen python tools/dogfood/dogfood.py train train [--suites S] \
        [--task SUITE/TASK] [--variants a,b] [--limit N] [--max-examples N]
    uv run --frozen python tools/dogfood/dogfood.py train coverage
    uv run --frozen pytest -q tools/dogfood/test_harness_guards.py
    uv run --frozen python tools/dogfood/external_proof.py [--publish] \
        [--tag TAG] [--url URL] [--rev REV]

## The trainer — corpus-driven, automatically graded

The scenario curriculum below is an exam: 43 fixed behavioural points chosen
by hand. The trainer (`tools/dogfood/trainer/`) is the complementary regime:
it generates labelled exercises from a corpus of REAL tasks and grades ranex
against labels derived from each task's own ground truth — no model, no
hand-typed expectations. On this machine the corpus is the VulcanBench
checkout (snapshotted to `training/corpus.json`): 287 tasks with metadata.
`classify` sorts every task into an honest class; `train preflight` then
gates which of the 157 grammar-exercisable tasks may actually train, and
the CURRENT sound set is 104 (95 toolchain-unpinned, 28 preflight-failed,
15 gold-not-green here, 10 governance-env-unsupported, 32 diff-graded,
3 cmd-unparseable — the class that silently produced `pytest pytest pytest`
in the old divergence harness, now a detected classification).

Per exercisable task, seven variants run the REAL governed cycle (vendored
kernel, pristine frozen manifest, `ranex run` → signed evidence →
`gate evaluate` → `journal verify`):

| variant | label (stated before anything runs) |
|---|---|
| `gold` | gold patch applied → gate MUST PASS |
| `empty` | no patch → gate MUST FAIL (tests are red pre-fix) |
| `delete-tests` | gold + test functions deleted → FAIL naming `missing test ID(s)` |
| `goalpost-move` | evidence recorded, then the tree moves → FAIL: `different subject digest` |
| `partial-gold` | first hunk of gold only → MUST FAIL |
| `manifest-swap` | run against an UNCOMMITTED tampered manifest → run REFUSES (`carries no suite manifest`), gate FAIL |
| `manifest-crossbind` | run against a COMMITTED alt manifest → gate FAIL: `manifest digest did not match` |

Every exercise appends to a chained pass ledger
(`training/passes/pass-NNN.json`; each pass digest-linked to the previous,
chaining fields excluded from the digest) and increments
`training/coverage.json` — the input-space class ledger from the 2026-09-03
audit (full text preserved at commit 85ed1f1cf). A disagreement between
label and verdict is recorded as a DIVERGENCE and fails the pass (exit 1);
divergences are findings to review — kernel bug, harness bug, or a corpus
task whose contract differs — and each kind is information. Inaugural
clean pass: 104 tasks x 7 variants = 728 examples, 0 divergences; every
class the audit measured at zero coverage is now trained 93-169x.

**Labels are only sound under governance conditions**, so `train preflight`
mirrors confinement on a throwaway copy before a task may train: the suite
must collect WITHOUT the task's env assignments (`ranex run` hermetically
strips the child env — verified: the confined child sees PYTHONPATH=None),
and the gold patch must be green under that same stripped env. That is
what the `governance-env-unsupported` and `gold-not-green` classes mean —
excluded with the reason, never trained with an unsound label.

**GitHub source** (`train github --url ... --rev ... --max-ids N`): clones
a real repository at a pinned rev, collects its OWN test ids under the
pinned interpreter, measures the pristine baseline honestly, and — only
when that baseline is green — trains pristine-HEAD-as-gold plus the
gaming/staleness/manifest variants. First subject: benjaminp/six@
c8e39406, 5/5 agree (pass-002).

Runner hardening inherited from the audit (the old harness's defects fixed
at the source): node ids parsed from any cmd grammar, never `argv[3]`;
verdicts read from exit codes, never prose substring; every scratch path
inside a per-example tempdir, no `/tmp` globals; test directories copied
with `copytree`; repo tarball snapshots (including LFS-materialized ones)
extracted with the safe tar filter; partial-gold labels arbitrated by a
bare run of the identical command (bare green -> honest skip; bare red
but gate PASS -> loudest possible divergence); the pass file is rewritten
after every task so a crash never destroys completed results.

## External-repository proof — the released tag on a repo that is not ranex

`tools/dogfood/external_proof.py` is the F-003 integration pattern made
scripted and documented: the published kernel tag (default `v0.1.0`),
installed the supported way, brought to a clean third-party repository
(default `benjaminp/six` at a pinned commit) and judging there:

    uv run --frozen python tools/dogfood/external_proof.py --publish

What it does, end to end, with no manual repair:

1. clean checkout of the tag + `uv sync --frozen` (ADR-038/009 install);
2. clones the external repo at the pinned commit (refuses
   symlink/submodule trees — the ADR-005 boundary — instead of failing
   mid-run) and requires its pristine suite green under the pinned
   interpreter;
3. vendors the kernel `src/` into the repo, committed, and proves the
   vendored tree digest equals `<tag>:src` — the CLI governs the repo
   that contains it (`governed_repository_root`, ADR-009);
4. keygen (key outside the repo), committed producer keyring, gate
   catalog binding the repo's own test command, and a suite manifest
   frozen by the RELEASED kernel's `freeze_manifest` in its own
   canonical form;
5. `ranex run` → signed evidence → `gate evaluate` PASS →
   `journal verify` chain=verified;
6. the attack: one comment line appended to the repo's own source after
   the green evidence, no re-run → `gate evaluate` refuses, exit 1,
   `evidence bound to a different subject digest`; the journal still
   verifies; re-running the work under governance → PASS again.

Prerequisites, checked before any work: git, uv, `/usr/bin/python3`
importing pytest (`ranex run` resolves argv[0] only through system
directories — F-003; e.g. `sudo apt install python3-pytest`), the tag in
this checkout, network for the clone and `uv sync`. Verdicts, exit codes
and refusal reasons are asserted, never eyeballed; keys are fresh each
run so digests differ while verdicts reproduce. `--publish` appends two
entries to the proof pile (`oss_bench/proofs/`, kind `run` + the
`stale-proof-external` attack) and regenerates the site page;
re-publishing is idempotent per kernel commit.

## The iteration protocol

1. `iterate` runs every scenario TWICE in fresh scratch trees. If the two
   fact records are not byte-identical, the scenario itself is declared
   NON-DETERMINISTIC and fails — determinism is enforced, not assumed.
2. Each pass diffs every scenario's canonical facts digest against
   `baselines.json` (the golden record). Drift, failures, and new unbaselined
   scenarios are FINDINGS; findings are written to the append-only ledger
   `iterations/iteration-NNN.json` with the git head they were observed at.
3. Each pass diffs against the previous ledger iteration: NEW / CHANGED /
   DRIFT / GONE lines. Improvement and regression are both visible.
4. Real weak points go in `FINDINGS.md` with an anchor and a pinning
   scenario. A finding closes only when the kernel changes and the pinning
   scenario's drift is reviewed — never by silently editing the scenario.
5. Curriculum growth: a new capability check is added as a scenario whose
   lesson names the capability it trains; `capabilities.json` gains the
   anchor; then `baseline` is re-recorded deliberately. Growing the
   curriculum is itself an iteration with `unbaselined` findings.

`bench` is the capacity half of the loop: wall-clock timings per scenario
(median/min/max over `--repeat` runs). Timings are deliberately
NON-deterministic and never enter baselines or the ledger.

## Curriculum (43 scenarios)

- **CLI surface** (3): every catalogued command path parses; keygen
  round-trip, overwrite refusal, and refusal of repository-committable key
  paths.
- **Kernel behaviour** (11): journal chain + triggers + tamper detection;
  admission unknown-producer / bad-signature / good-record; verdict
  self-approval, contradiction, and absence blocking; suite freeze drift;
  command digest structure; keygen refusals.
- **Independent math proofs** (6): journal chain algebra recomputed with
  plain hashlib over raw SQLite rows; tamper propagation through the whole
  chain; canonical-JSON cross-implementation agreement; Ed25519 determinism
  stress (128 samples); digest avalanche/distinctness (8192 argvs);
  manifest digest recomputation.
- **Core logic methods** (5): exhaustive 8-row and 16-row truth tables for
  `addresses`/`satisfies`; De Morgan equivalence executed on the kernel's own
  predicates; precondition enforcement (7 malformed constructions must
  raise); evaluate postconditions + purity (byte-identical records).
- **Advanced methods, honestly mapped** (6): Kahn's DAG proof over the real
  `uv.lock` graph; `select_wheels` closure/determinism/pinning over the real
  lock and pinned interpreter; exact 2^53-1 publication boundary; NaN/Inf
  refusal in canonical JSON; byte-level O(1) append proof; permutation
  invariance of gate evaluation.

Ranex has no gradients or matrices, so none are pretended: finite domains are
proven exhaustively (truth tables), structural domains inductively (chain
walks, prefix-stability), infinite domains by deterministic stress (signing,
digests). Everything else is out of scope by evidence, not by omission.

## Guarantees

- No scenario mutates the working tree, committed governance state, or
  network; everything runs in `tempfile` scratch dirs.
- Facts are canonical JSON (sorted keys, compact, `allow_nan=False`); any
  value that cannot serialise deterministically was never evidence.
- Random material (keys) is behaviour-tested but never recorded in facts.

## Calibration — negative controls and recall (MAP §8.4, issue #95)

`calibration.py` runs **controls**, not checks. An expectation is a pair: a
positive that must hold and a negative that must be refused, each executed
`--repeats` times on identical input against a real governed repository — real
Git, real Ed25519 keys, real `ranex run`, real `gate evaluate`.

| Status | Means |
|---|---|
| `VERIFIED` | the positive held and the negative was refused, in every repeat |
| `GAP` | the positive was refused, or the control has no executable negative |
| `FALSE-PASS` | the negative was **accepted** — the check cannot block what it exists to refuse |
| `NON-DETERMINISTIC` | identical input produced different results across repeats |
| `UNVERIFIED` | not executable in this environment; named, never implied |

`PASS` is deliberately absent: that word belongs to a verdict, and a
measurement borrowing it invites being read as one. **GAP is not VERIFIED** —
a control with no negative has never been shown capable of failing, so its
green says nothing.

A `FALSE-PASS` carries a **recall window**: §8.4's rule is that when a gauge is
found out of calibration, every part it *passed* since its last good check is
suspect. The receipt names those evaluations by journal position. With no prior
VERIFIED record the window is the whole chain, and the receipt says so rather
than narrowing to look tidy.

```sh
uv run --frozen python tools/dogfood/calibration.py --out /tmp/cal --repeats 3 \
  --journal governance/journal.sqlite3 --history tools/dogfood/audits
```

Retained receipts, `audits/2026-09-10-calibration/`:

* `calibration.json` — three kernel properties, each with its negative:
  a failing bound command blocks, absence blocks, self-approval is refused.
  All VERIFIED over three repeats.
* `alarm-proof/calibration.json` — **FALSE-PASS by construction, and that is
  the point.** A fourth control binds a real gate to a scanner that always
  exits 0, so the violating tree earns a PASS. It is the instrument proving its
  own alarm fires against the real kernel; it is not a defect in Ranex. Run it
  with `--prove-alarms`.

A deliberately red receipt must not be able to hide a real one, so the
distinction is machine-readable rather than a note someone remembers: a
selftest control declares `expected_outcome`, and `as_expected` records whether
it still produces it. **Scan for a FALSE-PASS with no `expected_outcome` and
what you find is genuine.** The declaration also inverts the check that matters
most — if the alarm ever stops firing, actual and expected disagree and the run
fails, because a selftest that quietly starts passing has stopped proving
anything. Only a genuine FALSE-PASS carries a recall window; nothing was
approved by a selftest's.

## Lanes — run in parallel, bounded, without taking turns

This host runs three legitimate kinds of heavy work at once. They are not rivals
and should not be serialised:

| lane | what it is | needs |
|---|---|---|
| `dogfood` | the iterate loop | a checkout it can WRITE to — `evolve_proofs.py` writes `backlog.json` and `dogfood.py` writes `iterations/`, both at repo-relative paths, by design |
| `verify` | a full suite or freeze ceremony | a checkout that stays CLEAN — `test_suite_freeze_real.py` and `ranex run` both refuse a dirty tree |
| `soak` | `.local/campaign/soak/soak.py` | memory and CPU; its scratch is campaign-owned and outside repo code |

In one checkout the first two cannot both be right, and that is the whole
collision: on 2026-09-09/10 it produced a freeze that returned `run_exit=1`
with no failure list, a 37-minute suite whose four freeze-journey tests errored
at setup, and two stashes holding nothing but the same regenerated metrics
file. Taking turns would fix it and waste the machine.

`lane.py` separates the two resources they actually contend for instead:

```sh
# a verification lane, isolated from whatever the loop is writing right now
uv run --frozen python tools/dogfood/lane.py run --kind verify --commit HEAD -- \
  uv run --frozen pytest -q

uv run --frozen python tools/dogfood/lane.py status
```

A `verify` lane leases a worktree at a pinned commit, so the loop — which
writes to the checkout it was started in — cannot dirty the tree being judged.
Every lane also takes a slot from a host semaphore sized by free memory,
because concurrent full suites have exhausted 62 GB here and been OOM-killed.

Two properties it keeps deliberately, both learned by losing runs to their
absence:

* **an acquire refuses**, it does not warn and continue. An advisory check a
  caller may ignore reproduces the failure it exists to prevent — which is how
  a second suite launched into a running freeze.
* **a holder is pid AND boot id.** Pids are reused across boots, and an OOM
  kill is this host's expected death, so a lock that cannot break itself would
  wedge the machine on the first kill.

It also replaces pattern-matching on `ps` output, which failed three ways in one
evening: too narrow (an anchored `pytest -q$` missed the freeze's inner run),
too broad (a bare `pytest` matched 13 dead watcher shells), and self-matching
(the checking shell's own command line contains the pattern). A pattern over
`ps` cannot distinguish the thing from a description of the thing; a lease can.

## Drivers read committed state — commit before you believe a re-run

Every governed and dogfood driver here reads the **committed** tree and anchors
to the **CLI's own checkout**, not to your working copy and not to your cwd.
That is correct — a governed observation must not be able to see uncommitted
edits — and it is also the single most expensive trap in this directory. Five
instances were hit in one evening (2026-09-09/10) by two sessions working in
parallel:

1. **`release_audit.py` provisions the kernel from the committed ref.** An
   uncommitted fix is invisible to it. Two full runs were spent re-verifying
   against an old kernel before anyone noticed.
2. **The argparse sweep clones the repository.** It verified `HEAD`, not the
   working tree, so a fix that existed only as an unstaged edit appeared to
   have failed — the same twelve defects reported back, identically.
3. **The freeze journey refuses a dirty tree.** Editing the very file the
   journey reads errored four tests for a reason unrelated to the change.
4. **A governed subcommand without `--external-repository` judges Ranex.**
   `governed_repository_root()` anchors to the checkout holding the CLI
   (ADR-038), so a driver running from inside a scratch subject still read
   *this* repository's `gates.yaml` and `producers.yaml`. Every control came
   back GAP with a refusal naming a producer the scratch repo had registered.
5. **That flag must precede `--`.** `run` takes everything after the separator
   as the command it executes (`argparse.REMAINDER`), so a flag appended at the
   end is swallowed into the observed argv instead of being parsed — and the
   symptom is identical to instance 4.

The shape is one property with five faces: **what a driver measures is the
committed tree of the repository it was explicitly pointed at.** So:

- commit before you believe a re-run, including a re-run that *fails*;
- name the subject explicitly with `--external-repository`, and put the flag
  before any `--`;
- when a driver's result contradicts an edit you are certain you made, check
  `git status` before you debug the code.

Instances 4 and 5 were hit by a session that had documented instance 4 in
`CLAUDE.md` the same morning. Knowing the rule is not the same as applying it,
which is why it is written here beside the drivers rather than only in
orientation.

## Realness policy — no mocks, no fakes, no synthetic data

A scenario that JUDGES kernel behaviour must exercise real artifacts:
- real CLI subprocesses (cli-surface, keygen scenarios);
- real SQLite journals with real out-of-band tampering (journal scenarios);
- real Ed25519 keys and signatures (signing, admission);
- real `uv.lock` and the real pinned interpreter (graph scenarios);
- real pytest runs producing real junitxml (suite-freeze-drift: the manifest
  is frozen from one real run and judged against a second real run of an
  edited test file);
- real git history (real-subject-digest-binding: evidence bound to the real
  HEAD tree digest, staleness proven against the real HEAD~1 tree).

Constructed inputs are permitted ONLY inside pure-algebra checks (truth
tables, De Morgan, determinism stress) where the input itself is the
variable under test — and the scenario's lesson must say so. A scenario
found faking the artifact it judges is a bug in the curriculum.

This is what makes fixes auditable: when the nightly loop fixes something,
the pinning scenario re-runs the REAL thing, so a fix that only satisfies a
mock cannot pass, and drift on the pinning scenario is proof the real
behavior changed.

The networked `release_audit.py` and `external_proof.py` now exercise real
`ranex run` and gate evaluation on pinned upstream clones, including actual
frozen dependency provisioning. They complement the deterministic curriculum.
- Exit codes: `run`/`iterate` exit 1 on failures or baseline drift, 0 when
  the loop is clean — usable as a gate.

## Findings so far

See [FINDINGS.md](FINDINGS.md) for current open and closed findings. The release
audit records receiver, principal-policy, suite-outcome, journal, bootstrap,
and host-integration gaps, plus the corrected Python 3.11 guardian startup.

The executable admission journey uses upstream Six and the installed system
pytest artifact, with 185-test passing runs surrounding ten real bind mounts
and ten unreadable-directory refusals:

```sh
uv run --frozen python tools/dogfood/executable_journey.py --out .local/executable-journey
```

Each refusal must name the shared identity or unreadable search. An unrelated
namespace/tooling failure is a failed check, never proof of identity enforcement.
