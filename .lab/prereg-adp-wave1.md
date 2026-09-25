# Preregistration — ADP steal wave 1 calibration (ranex-ide-oracle-steal-wave1)

Frozen before any scored measurement. Digest of this file is recorded in the
report; any post-hoc change is disclosed as an amendment with its own digest.
Calibration instrument: **base-freeze-v1** (governance/calibration/base-freeze-v1.json,
commit d4f63079118277ce71332ae0a934c1ae756844a6, branch fm/ranex-p1-base-freeze-ship;
not merged to main at scout time — re-cited in the final report).

## §0 Subjects and engines (pinned)

| Pin | Value |
|---|---|
| Subject A | six@1.17.0 @ git ebd9b3af90247b8858d415a05e96e9ee61e48d07 (matches base-freeze-v1 subjects) |
| Subject B | ranex checkout @ b7f039ba0 (worktree HEAD; verdict.py digest must equal base-freeze kernel_digest 2969aa74…) |
| Engine L (lint) | ruff 0.16.2 (matches CI pin `uvx ruff@0.16.2`) |
| Engine T (types) | pyrefly 1.2.0 (matches CI pin `pyrefly==1.2.0`) |
| Engine configs | Subject B: repo pyproject [tool.ruff]; pyrefly `--project-excludes '**/verdict.py'` over src/ranex. Subject A: no repo config → ruff defaults (E4,E7,E9,F); pyrefly defaults over six.py. |

## §1 Design (experimental-design skill: units, blocks, no pseudoreplication)

- **Unit of FP estimation** = one distinct known-good file/tree (S2 bank: 30 novel
  clean Python files authored before any engine run, idiomatic, no seeded defect).
- **Unit of catch estimation** = one distinct known-bad plant (12 defect classes,
  §3). The ×3 repeats of one plant are determinism checks, NOT replicates, and are
  never counted toward a rate.
- **Blocks** = subject (six / ranex) and engine (ruff / pyrefly); rates reported
  per engine; no pooling across engines for promotion decisions.
- **Round structure** (multiple calibration rounds authorized by DIRECT 010b):
  - Round 0 (characterization, unscored): run engines on pinned clean subjects;
    freeze the allowance list (rule, file, count) and the SARIF/JSON output shapes.
  - Round 1 (scored): KG bank, KB plants, determinism ×3, env-invariance,
    negative control. Thresholds below apply to Round 1 only.

## §2 Preregistered thresholds (frozen)

| ID | Quantity | Threshold for PROMOTE | Estimator |
|---|---|---|---|
| TH-KG | KG false-FAIL on S2 bank (n=30) and on S1 beyond frozen allowances | 0 observed; one-sided 95% Clopper-Pearson UB ≤ 10% (n=30 ⇒ UB=9.5% at 0/30) | exact binomial |
| TH-KB | KB catch across 12 distinct plants per engine-subject pair where the rule applies | 12/12 caught (any miss = FALSE-PASS, blocks promote); CP two-sided 95% LB disclosed (12/12 ⇒ LB=0.735) — honesty, not the bar | exact binomial |
| TH-DET | Determinism | every scored arm's primary output byte-identical across 3 repeats (sha256); any divergence blocks | exact comparison |
| TH-ENV | Credential-free invariance | verdict + output bytes identical under `env -i` (PATH/HOME only) vs normal env | exact comparison |
| TH-NEG | Negative control | attempt to admit a completion/preview artifact as evidence for a required claim MUST be refused by the claim surface | structural |
| TH-SCOPE | Zero-scope guard (prusik steal) | clean run over empty scope (exit 0, nothing checked) must yield executed-count 0 → NOT PROVEN | structural |

The DIRECT 010b bar "×3 stable" binds TH-DET. The bar "target 0 on pinned subjects"
binds TH-KG on S1. Thresholds are not moved mid-round; a moved threshold in a later
round is disclosed as an amendment (silent moves forbidden).

## §3 KB plant bank (12 classes, authored before Round 1)

Type plants (pyrefly must catch): t1 wrong-arg-type call; t2 undefined name;
t3 return-type violation; t4 attribute on incompatible union; t5 wrong arity;
t6 incompatible assignment.
Lint plants (ruff must catch, rule in the subject's frozen config/defaults):
l1 F401 unused import; l2 F821 undefined name; l3 F541 f-string no placeholder;
l4 E731 lambda assignment; l5 E722 bare except; l6 E711 `== None` comparison.
Plants are planted one at a time in the pinned subject trees (copies), run,
reverted; each plant ×3 repeats for TH-DET.

## §4 MARGINAL definition (Ranex baseline, per brief)

BASE arm = bare CI invocation (exit code only; no absence-blocking, no digest
binding, no envelope). TREATMENT arm = the same command wired as a governed
claim through the real kernel (`ranex run --claim … && ranex gate evaluate`) in
a real governed repo, plus (scratch, Seam-B prototype, kernel untouched) a
SARIF normaliser that puts rule id + severity + file:line into the repair
envelope. MARGINAL is judged on: absence-blocks, digest-binding, envelope
detail, determinism — never on agent self-report.

## §5 Analysis plan (frozen)

Exact binomial (Clopper-Pearson) intervals at 95% (one-sided for UB on FP,
two-sided disclosed for catch). No NHST beyond these intervals. Determinism and
env arms are pass/fail exact comparisons. Uncertainty discipline
(uncertainty-and-units skill): sampling uncertainty attaches ONLY to rates over
finite banks; digests/byte-identity are exact and carry no ±; "confidence"
fields of subject tools are reported as fabricated precision where they are
fixed tables, and never quoted as calibrated.

## §6 Deviations

Deviations from this prereg are reported in a dedicated amendments section with
cause; none may relax a threshold.
