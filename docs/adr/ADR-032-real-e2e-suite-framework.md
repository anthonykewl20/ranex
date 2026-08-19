# ADR-032 — real-e2e suite framework: prereqs, goldens, subprocess coverage, one proof entrypoint

**Status:** proposed
**Date:** 2026-08-19
**Decision-makers:** repo owner
**Slice:** n/a — SLICE-055 opens after this ADR is accepted and governance selects it, per tracker #33 phase order; no slice is open now

## Context and Problem Statement

Milestone 4 (tracker #33; MAP §0.24/§0.30 record the owner's build order) binds every slice to a universal alignment rule: every e2e runs real toolchains over real subjects with independently re-checkable outputs, with traced runs where applicable on the ADR-031 substrate. Issue #35 (https://github.com/anthonykewl20/ranex/issues/35) freezes the input contract this ADR records: a prerequisite library, golden-transcript conventions, a subprocess coverage harness, and one documented full-suite entrypoint whose captured run is the milestone's proof artifact.

The real-e2e layer today is a set of hand-built spines, each sound and each alone. `tests/e2e/test_gating_real_suite.py` drives ordered stages over a real clone of this repository with a `Session` object whose `reach`/`block`/`require` discipline already treats absence as failure and skips as named declarations — the clone's own CLI code judges the clone, exactly the construction this frame generalizes. `tests/e2e/test_run_produces_evidence.py` freezes the suite-manifest mechanics. `tests/integration/test_slice017_native_launcher.py` probes host capability through limitation functions. But every one of those files re-implements prerequisite probing by hand — `pinned_resolver` and `network_available` in one place, the qualification limitation probe in another, `RANEX_SIGNING_KEY` checks in a third — and none of them has golden transcripts, subprocess coverage, or a single entrypoint.

SLICE-056 onward each need exactly this frame — declared prereqs, a golden to diff against, coverage that sees their subprocess spines, and one command a human can run — and the milestone's definition of done (coverage of `src/ranex` measured and reported, every gap closed or risk-accepted in writing, a captured green run at a pinned commit) cannot be assembled from per-file improvisation. This ADR is the frame. It ships no per-feature real tests: the family slices own those, and this slice builds the frame they slot into.

## Decision Drivers

- Real toolchains, real files, independently re-checkable outputs only; synthetic fixtures support, never close (issue #35 closure boundary).
- Every skip carries a machine-greppable named reason and is declared; an undeclared skip fails the entrypoint — absence blocks, never silently greens.
- No new pytest markers registered: `--strict-markers` is held; gating uses the fixture/skipif convention only.
- The manifest discipline stands: `suite freeze` owns test-ID registration; framework-added IDs round-trip without hand edits.
- Determinism: identical runs diff clean against goldens; a sabotaged output diffs dirty.
- Coverage of `src/ranex` measured across subprocess CLI runs; hard-killed (SIGKILL) children are a documented blind spot the threshold accounts for.
- Dependency policy: the runtime graph stays three packages; coverage.py is already a pinned dev dependency — the frame adds nothing.
- Traced runs ride the ADR-031 substrate, default off, inherit its verdict-neutrality proofs, and never reach a governed or observed command.

## Prior art

Research evidence for this decision; every file below was fetched at its pinned ref this session and its blob hash confirmed present in the cited repository's own git blob store.

- Searched: `gh api repos/git/git/contents/t` at ref v2.45.2 plus the two vendored files — lazy prereqs live in `test-lib-functions.sh`, trash directories in `test-lib.sh`, not in one file.
- Searched: `gh api repos/postgres/postgres/git/ref/tags/REL_16_2` and `repos/curl/curl/git/ref/tags/curl-8_8_0` to dereference the pinned tags to their commits — the docs-discipline pin check accepts dotted-numeric tags or 40-hex commits only, and the commit is the tag.
- Searched: `gh api repos/moby/moby/contents/integration/internal` at ref v26.1.4 — the issue's `integration-cli` no longer exists at that ref; the centralized probes moved to `integration/internal/requirement`.
- Searched: `gh api repos/curl/curl/contents/tests/server` at ref curl-8_8_0 to pick `sws.c` as the focused representative of the local-server model over the far larger driver script.
- [git's test harness core, v2.45.2](https://github.com/git/git/blob/v2.45.2/t/test-lib.sh): the trash-directory model — every test gets a fresh `trash directory.<test>` subject; `--verbose`/`--immediate`/`--debug` knobs; the whole per-test lifecycle (setup, run, teardown) is one auditable shell file.
  License: GPL-2.0 — pattern only, no code enters `src/` (ADR-012 git-file precedent).
  Weakness: prerequisites are computed into per-process global variables and a failed prereq is a silent skip — the run reports skip counts, not skip reasons, so a CI log cannot grep which capability was missing; and `--immediate` aborts on first failure, masking later independent failures.
  Vendored: docs/adr/prior-art/ADR-032/git-test-lib.sh blob:79d3e0e7d9b32dd2938e635dc94acc6b49000569
- [git's lazy prereqs and sabotage primitives, v2.45.2](https://github.com/git/git/blob/v2.45.2/t/test-lib-functions.sh): `test_lazy_prereq` evaluates a probe once and caches it for the process; `test_must_fail` refuses unexpected failure modes (a command dying under a signal is an error, not an expected failure); `test_when_finished` binds cleanup to its test.
  License: GPL-2.0 — pattern only, no code enters `src/`.
  Weakness: the lazily cached answer is process-global truth — if the capability flips mid-run (network drops, a daemon exits) every later test consumes the stale answer; and `test_must_fail`'s acceptability is a hardcoded exit/signal whitelist that cannot express content-level expectations.
  Vendored: docs/adr/prior-art/ADR-032/git-test-lib-functions.sh blob:862d80c9748c7f9d6234c6b47d68ed7854f3de03
- [PostgreSQL's regression driver, REL_16_2 (commit b78fa8547d02fc72ace679fb4d5289dccdbfc781)](https://github.com/postgres/postgres/blob/b78fa8547d02fc72ace679fb4d5289dccdbfc781/src/test/regress/pg_regress.c): the sql/out golden-transcript model — run a real query batch against a real server, push output through a normalization filter, diff byte-exactly against the committed expected `.out` file, and on mismatch write the diff where the failure names it.
  License: PostgreSQL Licence — permissive, BSD-style (repo `COPYRIGHT`); pattern only.
  Weakness: normalization is a per-test sed-filter list, so anything the filter author forgot (a new timestamp, a path, a PID) becomes golden churn; and the sanctioned repair workflow is copying actual output over the expected file — refresh-by-copy is exactly how an implementation regression gets baked into a golden, and nothing in the driver distinguishes a stale golden from a wrong one.
  Vendored: docs/adr/prior-art/ADR-032/postgres-pg_regress.c blob:57aa0de3b7adf6a41f8423cbcfd86a4bedeb3fd8
- [curl's deterministic loopback test server, curl-8_8_0 (commit fd567d4f06857f4fc8e2f64ea727b1318f76ad33)](https://github.com/curl/curl/blob/fd567d4f06857f4fc8e2f64ea727b1318f76ad33/tests/server/sws.c): the local-server model — one in-repo HTTP server serves test-number-derived responses on a dedicated port with fixed semantics, so a test's wire transcript is a stable golden rather than a function of some external service.
  License: curl licence — MIT-style derivative (repo `COPYING`); pattern only.
  Weakness: determinism is bought with a bespoke C server that drifts from any real web server it stands in for — the suite proves the client against this server, not against the world — and serving state still needs out-of-band checks to avoid races, machinery the server itself cannot guarantee.
  Vendored: docs/adr/prior-art/ADR-032/curl-sws.c blob:53add587d6c8b44d47140d1c3a0bc3db37f29564
- [moby's centralized requirement probes, v26.1.4](https://github.com/moby/moby/blob/v26.1.4/integration/internal/requirement/requirement.go): one import point answers "is this host capable" — `HasHubConnectivity(t)` returns a bool that call sites turn into skips; capability questions stop being scattered per-test heuristics.
  License: Apache-2.0.
  Weakness: a bare bool answers "reachable at the instant of the call" — the skip decision and its reason live at each call site with no registry, so a mid-run flip yields tests that skip after earlier ones already ran; and the probe itself calls `t.Fatalf` on one error shape, mixing probe failure with test failure.
  Vendored: docs/adr/prior-art/ADR-032/moby-requirement.go blob:0e4ee0c4cd6303810caa02dafc6986ab0ecc172b
- [coverage.py's subprocess hook, 7.6.1](https://github.com/nedbat/coveragepy/blob/7.6.1/coverage/control.py): `process_startup()` is the documented mechanism — a config named by `COVERAGE_PROCESS_START`, a `sitecustomize.py` injected through `PYTHONPATH` that calls it, `parallel=true` per-process data files, then one combine; measuring real subprocesses becomes a property of the environment, not of each test.
  License: Apache-2.0.
  Weakness: the hook silently no-ops — if the env var is unset or `sitecustomize` is shadowed by another on the path, the child reports nothing, which is byte-identical to a child that simply had no coverable lines; a fake zero-coverage run is indistinguishable from a real one without out-of-band checks.
  Vendored: docs/adr/prior-art/ADR-032/coveragepy-control.py blob:ca757e9e133b02b8010f7229b817662672b14eba
- Rejected: https://github.com/pytest-dev/pytest-testinfra — its units are host-state assertions over ssh and docker back-ends, not journey-shaped CLI spines over a real git subject; adopting it grows the dev graph for a lane the repo's own pytest tree already provides, and its skip model carries no reason ledger.
- Rejected: https://github.com/microsoft/playwright — the strongest golden and auto-wait machinery in the field, but browser-lane only: it would drag a pinned browser download into a suite whose journeys are CLI and toolchain subprocesses, and its goldens are DOM/snapshot-shaped where this program needs text and wire-shaped transcripts.
- Rejected: https://github.com/tox-dev/tox — it orchestrates environments rather than assertions: no prereq-reason registry, no golden comparison, no skip-declaration discipline, and it would interpose a dependency layer between the operator and the single entrypoint this program must document honestly.

## Considered Options

1. Keep per-file hand-built spines; each family re-implements probing and skipping exactly as the gating-real-suite file does today. Rejected: SLICE-056 onward would each clone the same boilerplate, and the milestone's assembled proof — one entrypoint, one coverage report over subprocesses, one artifact — cannot be glued together from ad-hoc per-file skips.
2. Adopt an external harness (pytest-testinfra, Playwright, tox). Rejected per the prior art: wrong lanes, dependency growth, and none carries a skip-reason ledger, golden comparator, or subprocess coverage in the shape this program freezes.
3. A pytest plugin with custom markers (a `real` marker registered in pyproject). Rejected: the frozen configuration holds `--strict-markers` with no new registrations, and plugin machinery hides the entrypoint's behaviour from the review surface the milestone depends on.
4. A thin in-repo framework on the existing pytest tree: a probe library consumed by module-scoped skip fixtures, committed `.out` goldens with one deterministic normalizer, a sitecustomize-based subprocess coverage harness wired through the existing coverage.py dev dependency, and one documented entrypoint that tees transcript plus coverage report and fails on undeclared skips. Chosen.

## Decision Outcome

In the context of milestone 4's universal real-toolchain rule and issue #35's frozen contract, facing a real-e2e layer of isolated spines, we chose a thin in-repo framework — probes, goldens, subprocess coverage, one entrypoint — that generalizes the existing clone-judges-clone construction rather than replacing it, accepting that the frame itself owns no per-feature tests and that goldens add a standing maintenance surface.

- Prereq library (`tests/e2e/_prereqs.py`): six frozen lazy probes — `pinned_resolver`, `network_available`, `signing_key`, `harness_fork`, `openrouter_key`, `qualified_host` — each returning exactly an (ok, reason) pair; module-scoped skip fixtures consume them, so every skip is machine-greppable by reason. A probe is lazy (evaluated when a consuming fixture first asks, git's `test_lazy_prereq` model) but never process-global truth: each consuming module-scoped fixture re-evaluates at its own setup, so a mid-run capability flip cannot serve a cached lie across test boundaries — git's weakness is refused, and a probe that errors is a loud failure, never a skip.
- Declared skips: the existing manifest is the ledger — every expected skip is declared in `governance/suite_manifest.json` through `suite freeze`'s TEST_ID=REASON form (mechanics already frozen by `tests/e2e/test_run_produces_evidence.py`); the entrypoint greps observed skips against it and exits nonzero naming any undeclared one; a declared skip whose precondition is actually present is a stale manifest surfaced at freeze time, not discovered at run time.
- Goldens (the PostgreSQL model): a family journey compares its normalized transcript against committed goldens under `tests/e2e/expected/<family>.out`; normalization is one centralized deterministic mask (digests, timestamps, durations, ephemeral ports) — never per-test filter lists; comparison is byte-exact, and on mismatch the failure emits the full unified diff of the first differing hunk with no truncation; the directory, naming, mask set, and comparator freeze with this slice's contract tests, the per-family golden files freeze at SPEC PRD with their family slices.
- Sabotage controls: every golden carries a red control — mutate the expected bytes and the comparator must diff dirty — this repo's red-first discipline applied to goldens; refresh-by-copy (PostgreSQL's sanctioned workflow) is never sufficient to merge, and a refreshed golden without a passing red control is a review refusal.
- Local deterministic services (the curl model): where a family needs a service, a stdlib loopback server bound to an ephemeral port on 127.0.0.1 serves deterministic responses as a conftest-extension fixture — in-process, inside the measured tree, no bespoke server binary; the golden records a masked port token, and declared network appears only where the family's issue names it.
- Subprocess coverage (the coverage.py pattern): `pyproject.toml` gains a `[tool.coverage]` run/report block — `source=src/ranex`, `parallel=true`, a fail-under threshold; `tests/e2e/coverage/sitecustomize.py` calls `coverage.process_startup()` when `COVERAGE_PROCESS_START` names a config; the entrypoint injects the hook through `PYTHONPATH`, runs the real suite, then combines; children hard-killed by SIGKILL are an accounted, reported blind spot the threshold absorbs — and the harness detects a child that produced no data file and says so loudly, never a fake zero, inverting coverage.py's silent no-op.
- Traced runs: the ADR-031 substrate rides every journey — the entrypoint optionally sets `RANEX_TRACE`/`RANEX_TRACE_EVENT` to a target outside every governed root; verdict-neutrality is inherited from the substrate's own invariance proof; trace variables never reach a governed or observed command, per that ADR's propagation boundary.
- Entrypoint and proof: one README-documented command (exact invocation, env vars, expected duration budget) runs the real suite with coverage wired, tees transcript plus coverage report to a gitignored artifact path whose writability is probed before the run starts, and exits nonzero on any undeclared skip; the entrypoint run is itself the milestone's proof artifact — a real invocation transcript and a real coverage report a human can read at a pinned commit.

### Consequences

- Good: SLICE-056 onward slot into one frame — declared prereqs, goldens, subprocess coverage, one proof entrypoint — instead of re-implementing the spine per file.
- Good: the milestone's definition of done becomes demonstrable — coverage measured and reported per file and line, skips named and declared, a captured green run posted as an artifact.
- Good: the existing spines keep their behaviour; the frame is extensions only, so their frozen contracts stay green untouched.
- Bad: goldens are a standing maintenance surface — every intentional output change is a deliberate golden edit plus a red control, slower than refresh-by-copy and the deliberate price of not baking regressions into goldens.
- Bad: the fail-under threshold is a moving number — it rises as real suites grow and must be re-derived, not guessed, whenever a family lands; too tight fails honest runs, too loose measures nothing.
- Bad: the entrypoint adds a real wall-time budget to every proof run; the README states it and the artifact shows it.
- Bad: parallel coverage data files demand cleanup discipline; combine idempotence is a tested property, not an assumption.
- Bad: the artifact transcript is operator-visible output — any future test that echoed key material would leak it into the artifact, so the transcript stays subject to the suite's no-secret-echo rules.

### Confirmation

Future frozen tests, named in prose only because they do not exist yet and freeze red at SPEC PRD before implementation: a prereq-gate contract test (probe honesty — each probe's skip reason fires exactly when its precondition is absent; no new pytest markers registered; module-scope re-evaluation across test boundaries) and a real-suite-entrypoint contract test (artifact teeing and pre-run writability probe; undeclared-skip nonzero exit naming the skip; sitecustomize-absence loud failure; combine idempotence under parallel suffixes; golden normalization determinism and the sabotage red control; manifest round-trip of the framework's own test IDs through `suite freeze` without hand edits). Both are named in issue #35's exact ownership. Existing suites already guard adjacent boundaries — the docs-discipline contract governs this ADR's own citations and vendored evidence, the gating-real-suite e2e holds the spine's skip discipline, and the run-produces-evidence suite freezes the manifest mechanics. Tracker #33 Phase 1 runs the disposable prototype (prereq library, one toy golden, coverage wiring, in a disposable tree) before the production slice, per ADR-013's prototype discipline.

## Improvements on the prior art

- A named skip ledger where git counts skips: every reason is machine-greppable and cross-checked against manifest-declared expected skips, and an undeclared skip fails the entrypoint — git reports how many, Ranex reports which and why, and absence blocks.
- No cached prereq lie: probes re-evaluate at each consuming module-scoped fixture, so a capability flip cannot serve a stale answer across test boundaries; git's process-global lazy cache is refused.
- Red controls on goldens where PostgreSQL refreshes by copy: mutate-the-expected must diff dirty before a golden is accepted, so an implementation regression cannot enter a golden through the sanctioned workflow.
- One centralized deterministic mask where PostgreSQL keeps per-test sed lists: the normalization set (digests, timestamps, durations, ephemeral ports) is a single audited function; the churn class a forgotten filter creates is designed out, and over-masking is a reviewed golden edit, never a comparator hack.
- A loopback service inside the measured tree where curl builds a bespoke C server: an in-process stdlib server is ordinary Python in the same suite — no second network stack drifting from the subject's world — and ephemeral-port binding with masked port tokens removes port races from goldens.
- Loud failure where coverage.py silently no-ops: a child producing no parallel data file is detected and reported — the harness distinguishes measured-zero from never-measured, which upstream cannot.
- (ok, reason) pairs in one library where moby returns bare bools to every call site: the reason travels with the decision, so the ledger, the skip message, and the entrypoint grep all name the same precondition; a probe error is a loud failure, not a skip.

## Architecture surface

No port, no adapter, no kernel code: the decision touches the test tree, the coverage dev-config block, and operator documentation only. Ownership is exactly issue #35's list — `tests/e2e/_prereqs.py`; `tests/e2e/conftest.py` (extensions only — the Signing registry above it is untouched); `tests/e2e/coverage/sitecustomize.py`; `pyproject.toml` (`[tool.coverage]` run/report: `source=src/ranex`, `parallel=true`, fail-under threshold); `README.md` (one documented full-suite entrypoint section); and the two contract tests named in Confirmation. Golden conventions live at `tests/e2e/expected/` with per-family files owned by their family slices; no per-feature real tests land in this slice.

## Scope and threat delta

The frame governs how real e2e tests declare journeys and how their proof is captured; it changes no verdict semantics, gate-catalog meaning, or journal trust rule, and adds no kernel code path. STRIDE: none moved — the disclosure surface it touches is the artifact (transcript plus coverage report), which carries suite output and line numbers only; the entrypoint never logs env values, keys, or tokens, and inherits ADR-031's rule that trace variables never reach governed or observed commands. Explicit non-goals: harness-lane effect admission (milestone 3) and CI hosting policy (tracker #33 Phase 2); an attacker controlling the artifact path is out of scope — the path is operator-supplied and probed for writability, not trusted for content.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Determinism | identical runs of one family journey | normalized transcript diffs clean against the golden, byte-exact, run over run |
| Discriminating power | any golden's expected bytes mutated | comparator diffs dirty and names the first differing hunk — red control frozen per golden |
| Skip honesty | a probe's precondition absent versus present | skip reason fires exactly on absence; declared-absent-but-present surfaces at freeze time |
| Coverage truth | a measured subprocess child versus a hookless child | per-file line/branch numbers reported; the latter fails loudly, never fake zero |
| Reproducibility | entrypoint rerun at the same commit | combine idempotent, artifact teed, duration within the README's stated budget |

## Reversibility

Door: two-way

The frame is test-tree tooling and documentation: removing the entrypoint section, the probes, the sitecustomize hook, and the coverage block leaves the kernel, the journal, and every existing frozen test byte-identical. Once family goldens exist under `tests/e2e/expected/` and a fail-under number is recorded, retiring the frame means retiring those goldens deliberately — a visible slice, never a silent patch.

## Sad paths

- 1. Entry run on an unqualified host → the `qualified_host` probe returns (False, named reason); the skip is recorded with its machine-greppable reason, the entrypoint exits nonzero if the skip is undeclared in the manifest — never a silent green.
- 2. Coverage data missing for a SIGKILLed child → reported as an accounted gap in the coverage annotation; never guessed, never imputed; the fail-under threshold absorbs the documented blind spot.
- 3. Golden mismatch → the exact unified diff of the first differing hunk in the failure output, no truncation, the family named — never a bare "assert False".
- 4. Artifact path unwritable → loud failure before the run starts (pre-run writability probe), no partial run, no swallowed tee error mid-run.
- 5. An undeclared skip appears → the entrypoint exits nonzero naming the skip's test ID and its reason; declared skips alone may pass.
- 6. A probe flips mid-run (network drops) → the next consuming module-scoped fixture re-evaluates the probe; no cached answer crosses a test boundary; a journey already in flight completes against its recorded precondition and the artifact notes the flip.
- 7. `sitecustomize` absent from `PYTHONPATH` → the harness detects the child produced no parallel data file and fails loudly; never reports a fake zero.
- 8. Parallel coverage files collide → `parallel=true` suffixing is verified by the frozen contract test; a second combine is a no-op (idempotent), and stale data files from a prior run are swept before a new one begins.
- 9. A golden goes stale after an intentional output change → refresh is a deliberate commit whose red control (mutate-the-expected diffs dirty) still passes; refresh-without-control is a review refusal.
- 10. A declared skip whose precondition is actually present → surfaced as a stale manifest at freeze time; probe honesty is a frozen contract, not a hope.
- 11. The mask over-masks (a digest in operator-visible output normalized away) → the mask set is frozen in one audited function; over-masking is a golden edit under review, never a comparator hack.
- 12. Local loopback server port collision → the fixture binds an ephemeral port and the golden records a masked port token; a collision cannot churn a golden.
- 13. A trace target set inside the working tree during an entrypoint run → refused by ADR-031's admission rules; the entrypoint names the refusal and proceeds without trace, never writes into the governed tree.

## Test strategy

Named real suites, each verified on disk: `tests/contract/test_docs_discipline.py` governs this ADR's own shape, citations, and vendored evidence — green at the commit that lands this ADR; `tests/e2e/test_gating_real_suite.py` is the canonical clone-judges-clone spine this frame generalizes — its Session reach/block/require discipline, its named block() skips, and its nested_hermetic_self_gate boundary are the behaviour the probe library must preserve unchanged, because conftest gains extensions only; `tests/e2e/test_run_produces_evidence.py` freezes the suite-freeze manifest mechanics (canonical blind manifest, TEST_ID=REASON expected skips) that the declared-skip ledger rides; `tests/integration/test_slice017_native_launcher.py` holds the host-qualification limitation-probe shapes (build closure, userns, cgroup delegation) the `qualified_host` probe generalizes; `tests/contract/test_trace_schema.py` freezes the ADR-031 event schema the traced runs emit. The future SLICE-055 tests are named in prose in Confirmation and exist nowhere on disk yet — they freeze red at SPEC PRD before implementation, per the repo's red-first rule, and the golden red control is part of their frozen shape. The Phase-1 vehicles (toy golden, toy real-subprocess coverage proof) are contract-test material, not new lanes: the entrypoint contract test proves subprocess measurement with a toy real-subprocess test whose target lines must be counted (acceptance criterion 2), and the probe contract test proves each probe honest (criterion 3). No unit level exists for a frame with no runtime code; the ordinal pyramid invariant does not apply to a suite whose subject is the harness itself.

## Code review checklist

- Verify the ownership surface is exactly issue #35's list — no new pytest markers, no kernel `src/` change, no new runtime dependency.
- Verify every skip reason is machine-greppable (one grammar, one place) and the entrypoint exits nonzero naming an undeclared skip.
- Verify probes return (ok, reason), stay lazy per fixture scope, never cache across test boundaries, and never conflate "absent" with "failed" — a probe error is a loud failure, not a skip.
- Verify normalization masks live in one audited function, with no per-test masking; over-masking is a golden edit.
- Verify every merged golden carries a passing red control; refresh-by-copy alone is refused.
- Verify sitecustomize absence fails loudly, combine is idempotent, parallel suffixes are verified, and the SIGKILL blind spot is reported and threshold-accounted.
- Verify the artifact path is probed for writability before the run, the tee never swallows errors, and no secret can reach the transcript or the coverage report.
- Verify trace handling inherits ADR-031's rules: targets outside every governed root, stripped from governed and observed commands, default off.

## More Information

Issue #35 freezes the binding contract (ownership, deterministic gates, acceptance criteria, sad paths); tracker #33 owns the phase order this ADR opens (PHASE 0 research, PHASE 1 disposable prototype, PHASE 2 production); ADR-031 is the observability substrate traced runs ride; ADR-013 governs the disposable prototype. Two corrections to the issue's research table are recorded here: moby's `integration-cli` no longer exists at v26.1.4 — the centralized probes live in `integration/internal/requirement` (vendored); and the citation URLs for PostgreSQL REL_16_2 and curl curl-8_8_0 carry those tags' 40-hex commits (b78fa8547d02fc72ace679fb4d5289dccdbfc781 and fd567d4f06857f4fc8e2f64ea727b1318f76ad33) because the docs-discipline pin check accepts dotted-numeric tags or commits only — identical bytes, spellable pin. The vendored files and `NOTICE.md` are fetched-byte evidence; their hashes were confirmed present in the cited repositories' blob stores this session, which is consistency, not provenance.
