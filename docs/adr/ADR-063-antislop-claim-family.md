# ADR-063 — the antislop claim: a test-integrity census, not a verdict path

**Status:** accepted

DIRECT 004/009 (P2), science report §3.3 and §8 proposal B, wave-1 ruling.
The kernel-oracle science run measured that the slop an agent reaches for
when it cannot make a test pass — delete the body, replace the check with a
constant truth, comment one assertion out — evades both the suite (it stays
green) and the scan family (nothing about a file's shape is wrong). The
wave-1 steal dig added two families nobody covered: blindly updating
snapshots, and narrowing generated-input ranges. This ADR records where that
gauge entered.

## Problem

ADR-060 settled where a new *kind of observation* may enter: a named seam,
the existing kernel, one trust chain. The scan family freezes a universe of
paths; the suite family freezes a universe of test IDs. The anti-slop
property is invisible in both — `test_integer_types` with three assertions
instead of four is a *count* regression against the approved tree, and no
file-level or outcome-level shape carries it.

## Decision

A third reporter family, `antislop-sarif-2.1.0`, on ADR-060's seams only:

- **The scanner** (`foundation/antislop.py`) is stdlib `ast`: per test, an
  effective-assert count (`assert` statements plus assertion-equivalent
  calls — `pytest.raises`, unittest `assert*` methods; counting the keyword
  alone false-failed real assertion-free tests in the science run); four
  structural rules at `error` (constant-truth asserts, pass-only bodies,
  snapshot-update flags/kwargs, narrowed generated inputs); one census
  entry per test at `none`. It exits 0 however many findings it reports,
  binds regions through the #97 fingerprint, and runs as the kernel's own
  entry point (`ranex antislop`), never an in-tree script (#110
  Correction 2 inherited).
- **The frozen universe** is the expectations manifest `{scope, tests}`:
  the test files and the per-test effective-assert counts of the approved
  tree. It is a seam-C trust root — read from the governing commit by
  `run`, `gate evaluate` and `task judge` (through `claim_expectations`,
  which dispatches on the reporter so no Gate-construction site learns a
  third shape), never from the subject tree, which may carry its own
  weakened copy unread.
- **The reduction** (`foundation/antislop_results.py`) emits the closed
  suite-summary `evaluate()` already decides on: a census count below the
  frozen count fails that test; a frozen test absent from the census — or a
  scope file the artifact never witnessed — is `missing`, and absence
  blocks. That last rule is what makes an empty artifact a full miss rather
  than a clean pass: the census cannot be quietly emptied. Structural
  findings fail their finding ID, file and named test whether or not the
  freeze names it — slop does not become legal by being new.
- **No acceptance vocabulary.** A scan finding can be `accepted` because
  review may answer for a real shortcut; a slop shape or a count shortfall
  is never something review waves through, so the family has no word for
  it and `antislop_expected_skips` is the empty map by construction.
- **The freeze** records exactly what a real run of the approved tree
  observed — every test file, every test, no narrowing flags (a freeze that
  could declare less than the tree carries would be the narrowing slop the
  claim exists to catch) — and refuses a tree that already carries
  violations: expectations recorded over slop would be expectations for it.

`evaluate()`, `verdict.py` and the evidence envelope are untouched; the
delegation surface refuses the family exactly as it refuses scan claims.

## Evidence

Audit `tools/dogfood/audits/2026-09-25-antislop/`: the science bank (three
slop plants, six known-good edits) plus the two wave-1 plants, replayed as
in-place edits of the pinned `benjaminp/six` tree against a freeze of the
pristine tree — real `ranex run`/`gate evaluate` cycles, 3× repeats, all
arms `as-expected`; the frozen bank is additionally replayed by the unit
suite (`tests/unit/test_antislop_scanner.py`,
`tests/unit/test_antislop_results.py`,
`tests/contract/test_antislop_claim.py`).

## Limits

- Census counts ride in SARIF message text, which the #97 fingerprint
  deliberately does not bind (a producer may reword messages between runs).
  A producer that forges counts has forged the artifact — the F-012
  standing boundary every producer-signed results file carries; a test
  quietly dropped from observation is a miss and blocks.
- The two wave-1 plants are caught in their named shapes only: the
  snapshot-update flag/kwarg spellings and `max_examples` below the floor
  or a point `integers()` range. Narrowing that keeps those shapes and its
  assert count is invisible here.
- Tests the freeze does not name are `extra`, recorded and never blocked:
  added tests are the suite's business.

## Prior art

- `Jott2121/oracle-gate` at `b09206ca3dfb0f2a0c3ca2813139ed791d533bf5`
  (tag `v0.1.1`, CC-BY-4.0), read for its Part 1.3 enumeration of
  agent test-weakening modes — the source of the two promoted plants.
  Behaviour adopted, nothing copied, no dependency added.
- The kernel-oracle science run (first-party, §3.3): the measured
  3/3-plant/0/6-known-good result, the detector bug that fixed
  assertion-equivalent counting, and the frozen control bank this claim
  replays.
