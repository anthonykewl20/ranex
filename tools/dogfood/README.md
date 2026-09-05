# Ranex dogfood — training and benchmarking loop

## Release audit probes

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
