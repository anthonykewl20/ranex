# SLICE-093 — Bare-arm purity: the two-arm benchmark's bare arm is provably bare

**Status:** done
**Issue:** #114

## Contract

`tools/dogfood/oss_bench/two_arm.py`'s bare arm used to build its
environment as `dict(os.environ)` plus a venv-on-PATH prepend — defensible,
but unproven. An inherited `PYTHONPATH` naming a ranex source root, an
inherited `RANEX_*` variable, or a vendored kernel directory on PATH would
make the bare arm quietly governed and the comparison would report a
difference that is not there (upstream's ponytail benchmark nearly published
a false ~4% from exactly this shape). #114 makes bareness proven, not
asserted:

1. **Declared allowlist** — `bare_environment()` constructs the whole
   environment from `BARE_ENV_PASSTHROUGH` (HOME, LANG, LC_ALL, LC_CTYPE,
   TERM, TMPDIR) plus `PATH = <ranex venv bin>:<BARE_SYSTEM_PATH>`. The
   deliberate venv-on-PATH interpreter choice stays, as an explicit,
   asserted entry over a declared system path — never inherited ambient
   bytes.
2. **In-child canary** — `BARE_CANARY` runs inside the bare child before
   EVERY task command and reports the environment the child actually
   received; the receipt records the environment used, not intended.
3. **Detector** — `contamination_findings()` flags any `RANEX_*` variable
   (names only, never values), any `PYTHONPATH`/`PATH` entry naming a ranex
   source root, and any deviation between constructed and observed child
   environment. `assert_bare_environment()` raises `BareArmContaminated`;
   `mode_tasks` catches it, prints `BARE-ARM-CONTAMINATED` on stderr,
   writes NO ground truth, and exits 3.
4. **Negative controls** — `--contaminate {pythonpath,ranex-var,
   vendored-path}` injects exactly one channel and exists only to be
   caught; the run must fail.

## Wiring

`run_bare_arm()` carries the probe-first loop (18 canaries on the 9-test
pinned task) and returns ground truth with an `environment` block (child
env, its sha256, findings, probe count). `bare_ground_truth.json` gains
that block; `validation.json` is byte-unchanged so before/after comparison
is honest. `_governed_environment()` factors the governed arm's deliberate
ambient+key+PYTHONPATH construction, retained per arm as
`governed_environment.json` (names and shape only — no ambient values, so
no operator secret is committed; scratch-absolute paths recorded by shape
so repeats compare stably). Prior two-arm numbers are re-labelled
UNVERIFIED in `tools/dogfood/FINDINGS.md` (F-041).

## Boundaries

The governed arm's behaviour, the benchmark methodology, and the
venv-interpreter choice are unchanged (verified byte-identical, elapsed
zeroed). `verdict.py` untouched (KERNEL_DIGEST unchanged); no new runtime
dependency. Out of scope by the issue: #115 calibration, #113 self-test
wiring.

## Validation

Red-first: tests/contract/test_bare_arm_purity.py (13 cases — allowlist
construction, declared PATH, determinism, each contamination channel,
in-child canary equality and catch, loud refusal, mode_tasks exit 3 with no
results, governed environment shape). Real-data proof:
tools/dogfood/audits/2026-09-24-bare-purity/ — five arms VERIFIED
(in-child probe clean ×3 with identical digests; each contamination flavor
caught 3/3 with no ground truth written; governed arms byte-identical
before/after the change on py-txn-kvstore; real task both arms with
journals verified; environment digests stable across 3 repeats per arm).
Suite manifest refrozen on the committed tree.
