# SLICE-009 — a skip is absence, not success

**Status:** done
**Opened:** 2026-08-05
**Closed:** 2026-08-05
**ADR:** `docs/adr/ADR-011-a-skip-is-absence.md` — accepted 2026-08-05.
**Closes:** ADR-011's confirmation; MAP §4.6's first control ("a skip is
absence, not success"). Leaves §4.6's other controls (entry-point observed
spawning, distinct claims, assertion strength) open.

## The defect

`Evidence.satisfies` accepts `exit_code == 0` (`verdict.py:105`) and nothing
else. Measured (MAP §4.6): a test asserting `False`, marked skip, reports
`1 skipped`, exits 0, and satisfies `tests-executed`. A suite that skips
itself into silence, or silently shrinks — two agents in one worktree once
destroyed 27 tests while the rest stayed green — is indistinguishable from a
healthy run. pytest refuses only total absence (exit 5); partial absence
passes.

## Design

Per ADR-011, all five parts:

1. **Structured results in the bound argv.** The catalog claim gains a key
   naming a junitxml artifact path; the argv carries `--junitxml=<that
   fixed relative untracked path>` inside the digest-bound command. A claim
   without the key keeps today's exit-code-only semantics.
2. **Observation signs the summary.** The hermetic run reads the artifact
   out of the materialised sample before teardown and signs outcome counts,
   sorted non-passed IDs with kinds, and a full-outcome digest into
   evidence. Domain bump `ranex-evidence-v2` → `v3`; admission refuses any
   other key set, old `v2` rows included.
3. **A freeze-time manifest.** Generated outcome-blind from a hermetic
   run's junitxml by a freeze command; committed beside `gates.yaml`;
   declares expected-skips by ID with a reason. Only the freeze ceremony
   writes it.
4. **The diff is the rule.** Every manifest ID must appear passed, except a
   declared expected-skip, which may skip or pass. Undeclared skip, xfail,
   xpass, error, missing ID, absent/unparseable/duplicate-ID artifact —
   each is absence and blocks, with a diagnosis clause naming the IDs and
   kind. Extra IDs satisfy nothing and block nothing.
5. **Base-tree trust for delegated judging.** Every trust root, manifest
   included, is read from the dispatch-time base commit, never the
   candidate.

## Done criteria

Each criterion is met only when a test proves it. New coverage belongs in
`tests/unit/test_suite_results.py` and
`tests/security/test_slice009_skip_is_absence.py`; existing contract and
e2e files extend where named.

1. **An undeclared skip blocks.** A manifest ID reported skipped without a
   declaration reads as absence; the verdict names the ID and the kind.
   (ADR-011 s.p. 1)
2. **A declared expected-skip is permission, not obligation.** Skipping
   satisfies; passing also satisfies. (s.p. 2, 3)
3. **xfail, xpass, and error each block.** (s.p. 4, 5, 6)
4. **A missing ID blocks**, proven both ways: an in-tree `addopts`/`-k`
   deselection that drops a manifest ID, and a deleted test file — the
   27-tests incident class. (s.p. 7, 13)
5. **Artifact discipline.** Absent, unparseable, oversized, and
   duplicate-ID junitxml each block as absence and never crash the judge.
   (s.p. 9, 10, 11)
6. **Evidence v3 is the only admissible shape.** The domain string moves to
   `ranex-evidence-v3`; admission refuses any other key set, and an old
   `v2` row is refused loudly, not skipped. Canonical JSON throughout.
7. **The catalog stays strict.** The new claim key parses, unknown keys
   still refuse, a claim without the key keeps exit-code semantics, and
   the argv digest binding is unchanged.
8. **The manifest is freeze-ceremony-only.** The freeze command generates
   it from a hermetic run's junitxml, outcome-blind; the gate parses the
   same artifact format through the same code path — proven by a test that
   freezes and judges one run, not by prose.
9. **A candidate cannot judge itself leniently.** A delegated candidate
   commit that edits the manifest is judged identically to one that does
   not: the manifest read comes from the dispatch-time base tree. Proven by
   editing it and observing the identical verdict. (s.p. 12)
10. **The forgery boundary is stated by a passing test.** A planted
    `conftest.py` that writes an all-pass junitxml is NOT caught: the test
    proves the forged artifact satisfies the new rule and documents the
    boundary, mirroring `test_slice006_approved_wheel_can_lie.py`.
    (s.p. 16)
11. **Ranex gates Ranex through the new rule.** Our own `gates.yaml` claim
    carries `--junitxml`; our own committed manifest declares the
    credential-gated e2e expected-skips; `ranex run` then `evaluate` reach
    a verdict on this repository through the manifest diff, and removing a
    manifest ID's test flips it to FAIL.
12. Every refusal added by this slice is reached by a test, `diff-cover`
    stays 100% on the change, and the full suite stays green.

## The controls most likely to become decoration

First: **the rule tested only against synthetic XML.** Hand-written junitxml
strings prove the parser, not the pipeline. At least one test must run real
pytest, produce the real artifact, and judge it end to end — criterion 8.

Second: **"same code path" claimed in prose.** Manifest generation and gate
parsing sharing one parser is a testable property: freeze a run, judge the
same run, assert the ID sets are byte-identical. A comment is not the test.

Third: **base-tree trust proven by reading source.** Criterion 9 must edit
the manifest in the candidate commit and observe the verdict unchanged —
asserting over which file the code opens proves intent, not behaviour.

Fourth: **criterion 11 passing because our manifest is empty.** The live
manifest must name the real suite (hundreds of IDs) and the real
expected-skips, and the flip-to-FAIL half of the criterion is what proves
the diff is actually consulted.

## What this slice does not close

- **Forgery.** A hostile tree fabricates the artifact freely (criterion 10
  states it; ADR-007's wheel demonstration stands). Same trust level as the
  exit code it replaces. Review's job until merge-time re-check and
  verifiable separation land.
- **The rest of MAP §4.6.** Entry-point-observed-spawning,
  `tests-executed` vs `product-exercised` as distinct claims, and assertion
  strength stay open.
- **Merge, promotion, approver authentication** — unchanged from SLICE-008's
  ledger, deferred behind this gauge fix on purpose.
- **Mutmut blindness to subprocess-driven tests** — unchanged; the live
  tests are the proof for the delegated path.

## Close-out

Every done criterion is met and test-proven. The 61 frozen tests are green
and byte-untouched since freeze commit `a844d56`. The full suite is 734
passed, 2 skipped, 0 failed, and diff-cover on the slice is 100%. Criterion
11 is live in both directions: the repository gate PASSes a governed
hermetic run with a 736-ID manifest, 67 declared expected-skips, and 669
passed in the sealed sample; the evidence is signed by anthony and approved
by reviewer. Deleting a frozen test's file flips the gate to FAIL and names
the missing ID.

The full mutmut sweep produced 6,964 mutants: 4,516 killed, 1,161 survived,
and 1,260 timed out. There are zero survivors in the slice's decision logic:
`satisfies`, Claim validation, `suite_diagnosis`, and admission key sets.
Survivors are refusal-message prose and subprocess-blind CLI layers.

Two fixes discovered during the slice also landed. Provisioned runs now pin
`VIRTUAL_ENV` to the verified deps environment, preventing ancestor-`.venv`
capture; its regression test plants a hostile `.venv`. Fanout e2e no longer
races on shared `.git/config`; identity is now command-scoped.

Two caveats remain. First, the sealed context truthfully cannot execute 67
of 736 tests: 25 harness-fork, 9 cold-start by ADR-009 design, 31
deps/provisioning tests needing operator uv plus an unwritable system
interpreter, 1 OpenRouter credential, and 1 mount namespace. Each was
declared with its reason at the freeze ceremony. Second, artifact forgery
stays open by design; criterion 10's passing test states that boundary.
