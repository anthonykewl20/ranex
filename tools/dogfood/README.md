# Ranex dogfood — training and benchmarking loop

Dogfooding ranex with ranex's own deterministic outputs. The loop's only
inputs are the installed kernel, the committed artifacts (`uv.lock`,
`governance/deps.yaml`), and byte-stable facts — no assumptions, no
hallucinated behaviour, no timing data in correctness records. The source of
truth is the code; `capabilities.json` holds the verified inventory with
file:line anchors.

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

## The trainer — corpus-driven, automatically graded

The scenario curriculum below is an exam: 33 fixed behavioural points chosen
by hand. The trainer (`tools/dogfood/trainer/`) is the complementary regime:
it generates labelled exercises from a corpus of REAL tasks and grades ranex
against labels derived from each task's own ground truth — no model, no
network, no hand-typed expectations. On this machine the corpus is the
VulcanBench checkout (snapshotted to `training/corpus.json`): 287 tasks with
metadata — 157 exercisable Python tasks, 95 whose toolchain is not pinned on
this host (recorded as honest refusals, never silently skipped), 32
diff-graded, 3 whose command grammar yields no test ids (the class that
silently produced `pytest pytest pytest` in the old divergence harness — now
a detected classification).

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
`training/coverage.json` — the input-space class ledger from
AUDIT-2026-09-03. A disagreement between label and verdict is recorded as a
DIVERGENCE and fails the pass (exit 1); divergences are findings to review —
kernel bug, harness bug, or a corpus task whose contract differs — and each
kind is information.

Runner hardening inherited from the audit (the old harness's defects fixed
at the source): node ids parsed from any cmd grammar, never `argv[3]`;
verdicts read from exit codes, never prose substring; every scratch path
inside a per-example tempdir, no `/tmp` globals; test directories copied
with `copytree`; the pass file is rewritten after every task so a crash
never destroys completed results.

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

## Curriculum (32 scenarios)

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

One honest limit: a full end-to-end `ranex run` scenario would exercise the
real governed-execution CLI on a real clone, but it requires wheel
provisioning (`deps fetch`), which is networked — deferred rather than
faked. When it lands, it lands real or not at all.
- Exit codes: `run`/`iterate` exit 1 on failures or baseline drift, 0 when
  the loop is clean — usable as a gate.

## Findings so far

See `FINDINGS.md`. F-001 (open): `Journal.verify()` raises on non-JSON record
corruption instead of returning its documented `False`. F-000 (closed):
catalog-vs-parser drift caught at construction time.
