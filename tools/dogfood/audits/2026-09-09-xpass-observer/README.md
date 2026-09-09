# Explicit XPASS: real data and GitHub acceptance

The canonical controller reporter retains `xfail(strict=False)` unexpected
passes before JUnit loses the outcome. A required observer property prevents
missing reporting from being signed as passing evidence. This does not make a
hostile pytest plugin trustworthy. See ADR-059 for activation and confinement.

## Retained measurements

The final transport repair was measured at kernel
`e4ae64121ca454a93f01a9fb499df9db763801cd`, source tree
`d2de9068b41ab06d6dcdbc4815a3002aa35c3bdf`. `external-six-final/receipt.json`
again records 25 VERIFIED / 5 GAP cases. `installed-live/receipt.json` records
real GitHub PR #10 from a built and installed wheel, with source-path injection
disabled. It refused the explicit XPASS merge, then merged repaired source at
`5d108f53c58c34cff7e16a7d383d598703a2e774`. Its three signed observations
were independently verified with OpenSSL. `installed-wheel.json` binds the
wheel hash and confirms that every packaged Python source matches the checkout.

`installed-dependency-before.json` retains a real packaging regression: adding
the controller's site-packages replaced system pytest 7.4.4 with controller
pytest 9.1.1. The reporter now supplies only its private module; explicit
loading uses a namespace portion that preserves real materialised packages.
`installed-dependency-after.json` runs the identical probe successfully in
automatic, separate `-p`, and combined `-p` modes. The installed release checks
repeat all three modes for two package candidates. No dependency version or
controller site-packages path leaks into the subject. Latest focused changed-line
coverage is 63/63 (`focused-diff-coverage-final.log`).

- `external-six/receipt.json` (earlier checkpoint): kernel `b0f1cb6741e41a6fc5b7475d517c147094b37e9b`,
  source tree `bfe864e605bd5b9d6be10900469ad7552a3076f9`, real
  `benjaminp/six@c8e394065cd541a16c040515dc0afb85cf22a7c3`.
  30 cases: **25 VERIFIED, 5 GAP**. The audit exits 1 because gaps remain.
  Both strict and explicit non-strict XPASS block. The signed journal anchor
  accepts the true chain and refuses a truncation that plain verification accepts.
- `live/receipt.json`: real GitHub PR #9, App-owned checks, GitHub-origin
  delivery GUIDs, two merge refusals and repaired merge
  `842983261fadc3dbd0c9bb5a46540b9560f613ca`. The driver explicitly ran the
  observation CLI; this is not evidence of unattended contributor-code execution.
- `live/evidence-3.json`, `evidence-6.json`, `evidence-10.json`: the actual
  signed passing, XPASS and repaired observations. Each ran Six's 200-test
  collection: 185 pass / 184 pass + 1 xpassed / 185 pass, with 15 declared skips.
  `signature-verification.json` retains successful independent OpenSSL checks
  and commands; `.payload`, `.sig` and the public DER key permit replay.
- `earlier-pr7.json`, `earlier-pr8.json`: earlier successful real GitHub loops.
- `first-sealed-run.log`: the first run found seven regressions. Environment
  activation leaked into child pytest; fixture JUnit lacked the new marker;
  test doubles drifted; supervisor capture hid a child diagnostic. These were
  repaired and tested rather than counted as successes.
- `combined-sealed-run.log` and `freeze-summary.json`: actual committed-tree
  freeze at `d2f1ea9ea9dd0c62f672506b17e9d3db2e1ceb9e`, 1776 passed and 140
  skipped, run_exit=0. All 1916 IDs came from that run; 168 existing skip
  declarations were preserved. Later changes preserve the same ID set.
- `xdist_probe.py` / `xdist.log`: synthetic outcome controls executed through
  real pytest 9.1.1 and pytest-xdist 3.8.0 with two workers; exit 1, one xpassed.
  This is integration evidence, distinct from the real upstream Six dataset.
- `focused-diff-coverage.log`: 57/57 changed executable lines covered by actual
  subprocess and integration tests. The final full-suite result belongs to the
  closing validation comment on issue #94, not this checkpoint measurement.

Supplemental checks are retained under `supplemental/`: 41/41 receiver
fault-injection controls, 20,000 concurrent journal appends over five rounds,
19 storage controls, real Six collection-failure/recovery and executable-alias
journeys, six signed-anchor input checks, and installed-package release checks.
The initial receiver replay exposed a probe race: a journal entry was visible
before the pipeline lock was released. Bounded redelivery now handles the
specified 503 response and still requires the real recovered fetch/API result.
The failed and repaired receipts are both retained. These local fault-injection
checks are separate from the live GitHub App publication in PR #9.

The five GAP cases are same-subject evidence reuse, hostile result production,
and suffix truncation, whole-history deletion and rewriting under **unanchored**
verification. Signed anchoring is measured separately; an external witness,
isolated scheduling and production deployment/soak are not established here.
No private signing keys or GitHub tokens are retained.

## Replay

`uv run --frozen python tools/dogfood/release_audit.py --refs HEAD --out .local/xpass-replay`
repeats the real Six audit. A nonzero result must be inspected, not relabelled PASS.

`uv run --frozen --with pytest-xdist==3.8.0 python tools/dogfood/audits/2026-09-09-xpass-observer/xdist_probe.py`
repeats the distributed outcome control without changing the project lockfile.

`tools/dogfood/live_evidence_evaluation.py --help` describes the credentials and
prepared probe branch needed to repeat the GitHub journey with `--mutation
explicit-xpass`. `--installed-kernel` requires an installed wheel and disables
source-path injection. It creates and merges probe PRs after verifying the exact SHA.
