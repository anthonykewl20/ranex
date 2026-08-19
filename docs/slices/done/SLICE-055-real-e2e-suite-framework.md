# SLICE-055 — real-e2e suite framework

**Status:** done
**ADR:** docs/adr/ADR-032-real-e2e-suite-framework.md
**Issue:** #35 (tracker #33, milestone 4 — PHASE 2 production; Phase-0 ADR
accepted, Phase-1 disposable prototype completed out-of-tree)

## Scope — issue #35's exact ownership, frame only

- `tests/e2e/_prereqs.py` — the frame's one library module: the six frozen
  probes, the golden-transcript normalizer and comparator, the declared-skip
  cross-check (both directions), child-environment wiring, and the coverage
  combine/report helpers. `python tests/e2e/_prereqs.py cross-check
  <manifest> <junitxml>` is the nonzero-on-mismatch step the documented
  entrypoint composes.
- `tests/e2e/conftest.py` — extensions only: module-scoped skip fixtures
  consuming the probes. The Signing registry above them is untouched.
- `tests/e2e/coverage/sitecustomize.py` — the subprocess hook
  (`coverage.process_startup()` under `COVERAGE_PROCESS_START`).
- `pyproject.toml` — `[tool.coverage]` run/report block
  (`source=src/ranex`, `parallel=true`, a fail-under threshold).
- `README.md` — one documented full-suite entrypoint section.
- `tests/contract/test_prereq_gates.py`,
  `tests/contract/test_real_suite_entrypoint.py` — the frozen contract
  tests, committed RED before any implementation (spec-prd step 6); from
  the freeze commit on they are read-only to the implementer.

No per-feature real tests land here — SLICE-056..053 own those. No server
fixture, no port binding, no service conftest abstraction (ADR-032 defers
the curl loopback model to the first service-journey family slice). No new
pytest markers (`--strict-markers` held). No kernel `src/` change.

## Frozen decisions carried as done-criteria contracts

Each criterion is provable by a named test in the two frozen files; the
ADR-032 decision each one compiles is named beside it.

1. **Probe library** — six frozen probes (`pinned_resolver`,
   `network_available`, `signing_key`, `harness_fork`, `openrouter_key`,
   `qualified_host`), each returning exactly an `(ok, reason)` pair with a
   machine-greppable reason grammar (`ranex-prereq:<name>:`), lazy per
   consuming module but never a cached lie across test boundaries or
   processes, and a skip that fires exactly when the precondition is
   absent — the frame helper never skips when its probe says present.
   Proven by the probe tests in `tests/contract/test_prereq_gates.py`.
2. **Declared-skip ledger, entrypoint time, both directions** — an
   observed-but-undeclared skip and a declared-but-not-observed skip each
   fail the cross-check nonzero naming the test ID and reason; an honest
   manifest passes. `suite freeze` itself stays outcome-blind and is not
   asked to check either. Proven by the cross-check tests in
   `tests/contract/test_prereq_gates.py`.

   *Application-scope ruling (orchestrator, 2026-08-19, recorded on issue
   #35):* direction (a) is hard everywhere — every observed skip must be
   declared, and its observed reason must be the declaration's same bytes
   (remediation R1d: exact string comparison, a drift is a finding naming
   both strings). Direction (b) is the probe-backed lie detector in two
   tiers: a declared-but-not-observed skip is a hard failure when its
   declared reason uses the frame grammar (`ranex-prereq:<probe>:`, the
   reason → probe mapping) — the finding names that probe's live verdict on
   the running host, and a present verdict locates the lie in the
   declaration (prune it at the next freeze) — while non-probe-backed,
   context-bound declarations (hermetic-freeze-context conditions not
   reproducible in the entrypoint's documented environment) are reported as
   an informational context-mismatch list, names plus count, exit 0. The
   manifest is deliberately multi-context; an unscoped direction (b)
   would make AC1 unsatisfiable on any single host. The frozen
   mechanism tests keep their fixture-driven hard outcomes unchanged —
   this scope governs application, not mechanism. Going forward,
   stage_12's operator-gate skip (`RANEX_SIGNING_KEY` not exported) is
   declared with the probe grammar.

   *Declaration-grammar ruling (orchestrator, 2026-08-19, DECISION
   [#35 #issuecomment-5343063550], extending the scope ruling above):* the
   manifest's expected_skips carry exactly two grammars —
   `ranex-prereq:<probe>: <prose>` (HARD tier: a context-independent
   condition one of the six frozen probes verifies live, both directions)
   and `ranex-context:<context>: <prose>` (INFORMATIONAL tier: the
   declaration names its context — hermetic-freeze, host-capability,
   operator-action; reported in the context-mismatch list, never hard).
   Unmarked prose is refused by the frozen lint; a context marker without
   a non-empty single-token context is refused too. Basis: the
   single-grammar mandate would hard-fail legitimately context-bound
   declarations (the plugin_lock harness-fork skips: absent in hermetic
   freeze, present-and-running on the canonical entrypoint host). ADR-032
   is revised in-place to match.
3. **Golden-transcript normalizer** — one centralized, single-argument
   function applying the ordered grammar (`<DIGEST>`, `<ABS-PATH>`,
   `<TIMESTAMP>`, `<DURATION>`, `<SID>`, `<PID>`, `<PORT>`, `<REL-PATH>`)
   deterministically; meaningful values (verdicts, exit codes, test names)
   stay discriminating; a sabotaged golden diffs dirty with the first
   differing hunk untruncated; per-test/per-family masking is refused.
   Proven by the normalizer tests in `tests/contract/test_prereq_gates.py`.
4. **Entrypoint documented** — README carries one section with the exact
   command, the coverage env vars, and the duration budget.
   Proven by `tests/contract/test_real_suite_entrypoint.py::test_readme_documents_the_real_suite_entrypoint`.
5. **Subprocess coverage harness** — wiring appends the hook dir to the
   child PYTHONPATH (last, never replacing), sets absolute
   `COVERAGE_PROCESS_START` and one absolute shared `COVERAGE_FILE` under
   `.local/ranex-e2e/coverage/`; a real `python -m ranex.cli.main`
   subprocess's target lines appear in the combined report with line
   numbers (AC2); repeated `coverage combine --keep` over retained inputs
   is idempotent by identical data hash; loud no-data detection fires for
   frame-wired children only, unwired children report unmeasured.
   Proven by the harness tests in
   `tests/contract/test_real_suite_entrypoint.py`.
6. **Joint trace+coverage case** — one real traced, coverage-measured CLI
   subprocess: out-of-governed-root trace artifact with version-first
   stream, governed outputs byte-identical to the untraced baseline,
   `RANEX_TRACE*` absent from the observed command's environment, target
   lines still counted in the combined report.
   Proven by `tests/contract/test_real_suite_entrypoint.py::test_joint_trace_and_coverage_case`.
7. **Coverage config block** — `[tool.coverage]` run/report freezes
   `source=src/ranex`, `parallel=true`, and a fail-under threshold.
   Proven by `tests/contract/test_real_suite_entrypoint.py::test_pyproject_freezes_the_coverage_block`.
8. **Manifest round-trip (AC5)** — the two frozen files' test IDs enter
   `governance/suite_manifest.json` through the existing `ranex suite
   freeze` ceremony, no hand edits. The frozen red form (IDs absent today
   → red) turns green only at the post-implementation ceremony.
   Proven by `tests/contract/test_real_suite_entrypoint.py::test_both_new_contract_files_are_in_the_frozen_manifest`.

## Frozen interface pinned by the red tests

`tests/e2e/_prereqs.py` public surface (spelled in both frozen test
docstrings, as amended by the sanctioned amendments below):
`PROBE_NAMES`; one `(ok, reason)` callable per name;
`REASON_PREFIX = "ranex-prereq:"`; `prereq_or_skip(name)`;
`normalize_transcript(text)`; `compare_transcript(actual, expected,
family=None)`; `cross_check_skips(manifest_path, junitxml_path)` returning
lines `"undeclared skip: <id>: <reason>"`, `"skip reason mismatch: <id>:
…"`, and `"declared skip not observed: <id>: <reason>"`;
`context_mismatches(manifest_path, junitxml_path)`;
`_junit_outcomes` classifying xfail/xpass per the kernel's frozen
semantics (suite_results.py:142-151 — xfailed/xpassed are not skip-ledger
entries); `wire_child_environment(base, *, coverage_home=None)`;
`HOOK_DIR`; `default_coverage_home()`; `CoverageDataMissing`;
`combine_coverage(home, children=None)` (the child-ledger seam — a wired
child that wrote nothing fails loudly naming the child; an unwired-only
ledger never alarms); `report_unmeasured(children)` (consumes the real
child ledger, refuses a label string); `probe_artifact_home_writable(home)`
(the pre-run loud failure); and the `cross-check` script exit contract.

## Sanctioned amendments to existing frozen tests

The docs-discipline gate's literal `Next slice: SLICE-054` mandate in
`docs/STATE.md` is compliance with `test_state_next_agrees_with_build_order`
(frozen-test-mandated wording, not ours to change), and the manifest
mechanics stay exactly as `tests/e2e/test_run_produces_evidence.py` froze
them. Beyond that baseline, the FULL amendment chain — B2's record, per
the 2026-08-19 remediation arbitration and its ruling trail on issue #35 —
enumerated one entry per sanctioned amendment:

1. **8cace47e6** — frozen-helper coverage-API construction fix in
   `tests/contract/test_real_suite_entrypoint.py`
   (`_coverage_data_hash`/`_cli_lines`: `CoverageData(basename=…)` +
   `.read()`, matching the installed coverage 7.15.3 API; `path=` does
   not exist there), assertions byte-identical; sanctioned in-session
   (BLOCKER anthonykewl20/ranex#35 #issuecomment-5340988152, disposition
   STATUS #issuecomment-5341197478; full diff posted as its record,
   #issuecomment-5343065062).
2. **b3426c3c3** — remediation arms red (Worker A): the
   arbitration-confirmed groups (B1/R1c+R1d cross-check, B4/R2 child
   ledger, M4/R3 artifact-home probe, R5 normalizer/comparator) plus the
   P2 gaps committed RED in the two frozen files — 10 red, 52 green at
   landing — the fixes being the implementer's next step.
3. **c0872e8fc** — the R1c two-grammar amendment to the frozen lint arm
   in `tests/contract/test_prereq_gates.py` (Worker A; the arm's
   `_declaration_defect` classifier accepts the ruled reworded forms);
   DECISION #issuecomment-5343063550.
4. **25bf6eac0** — the R1d hard-tier scoping amendment (Worker A, the
   R1d arm + its fixtures + its doc lines only): `ranex-prereq:`
   declarations compare declared-vs-observed reasons exactly,
   `ranex-context:` declarations reported-not-compared; ruling on Worker
   B's BLOCKER #issuecomment-5343719923, DECISION
   #issuecomment-5344433341.
5. **0b62c9287 (the spine edits)** — the three sanctioned spine changes,
   nothing else in the two spine files: `test_gating_real_suite.py::ranex()`
   strips `COVERAGE_PROCESS_START`/`COVERAGE_FILE` (its children are
   unwired by the frame, and this venv's `a1_coverage.pth` would measure
   them anyway — "unwired" must mean no coverage environment at all; the
   PYTHONPATH replacement stays as the recorded anti-pattern example);
   stage_12's skip message (~:937) byte-aligned to its
   `ranex-prereq:signing_key:` declaration (direction (a) compares
   reasons now); both spine files' local `pinned_resolver()` copies
   deduped into `_prereqs.pinned_resolver` (M8 — one owner of the digest
   verdict); sanctioned in the same ruling trail.

## Ceremony and proof

- Post-implementation: `ranex suite freeze` re-registers the two files' IDs
  (criterion 8), then the README entrypoint run is captured — transcript +
  coverage report teed under the ignored `.local/ranex-e2e/` home and posted
  on #35 as the milestone-4 proof artifact.
- Hard-killed (SIGKILL) children remain a documented, threshold-accounted
  coverage blind spot; the entrypoint's sweep of the shared coverage home
  is load-bearing freeze hygiene.

## Follow-ups register (accepted for the next test-author round)

Close-out verification review (2026-08-19), P3 lane — accepted, unarmed
today; each lands as a frozen arm first, then an implementation:

- Dodge-refusal sample arms for the declaration lint's refusal paths —
  the unknown-probe form and the prose-less-marker form, both refused in
  code at `_declaration_defect` with no frozen arm proving either refusal.
- `fail_under` derivation automation (the threshold re-derived from a
  real report as families land, never hand-guessed) plus the explicit
  `branch=true` decision.
- Hook-shadow decoy arm — an earlier PYTHONPATH entry carrying a
  competing `sitecustomize.py` (first-hit-wins) shadows the frame's hook;
  today only the loud wired-child no-data detection would catch it.
