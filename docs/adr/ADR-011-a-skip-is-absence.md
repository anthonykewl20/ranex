# ADR-011 — a skip is absence, not success: suite verdicts from structured results, not exit codes

**Status:** accepted
**Date:** 2026-08-05 (accepted same day, owner)
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-009-a-skip-is-absence.md` — opened on
acceptance. The decision was written first, as the rule requires.

## Context and Problem Statement

The `landing` gate binds `tests-executed` to `["uv", "run", "pytest", "-q"]`
(`governance/gates.yaml:16`), and `Evidence.satisfies` accepts it on
`exit_code == 0` alone (`src/ranex/governed_execution/domain/verdict.py:105`)
— nothing about counts, identity, or outcome kind.

Measured, MAP §4.6 (`docs/MAP.md:757-762`): a test asserting `False`, marked
skipped, reports `1 skipped`, exits `0`, and the claim is satisfied —
indistinguishable from a clean pass.

Partial absence is invisible here; total absence is not — pytest's own
`ExitCode.NO_TESTS_COLLECTED = 5` already refuses running zero tests. The gap
is specifically tests that were supposed to run and silently did not: a suite
that skips itself into silence, or one that shrinks — two delegated agents
sharing a worktree once destroyed 27 tests while the rest stayed green —
reads identical to a healthy run at this gate.

## Decision Drivers

- The kernel must tell a claim that was satisfied from one that never ran.
- A skip must be visible but not automatically fatal — some skips are declared, and a declaration is permission, not an obligation.
- The frozen suite is a trust root; only the freeze ceremony may define what "complete" means for it, never an implementer.
- Detection must read structured results, not stdout text or a bare exit code — the format must not be plugin- or version-dependent.
- `evaluate()` stays pure — no model judges whether a test is real or well-written.
- A delegated candidate's own trust roots, the manifest included, must be read from the base tree, never from the commit being judged.
- Absence blocks by construction — a required claim with no satisfying evidence is FAIL, never a default, never a skip.

## Prior art

- Searched: `gh search repos "pytest-error-for-skips"`
- Searched: `gh api "search/code?q=repo:python/cpython+is_all_good"`
- Searched: `gh api "search/code?q=repo:jenkinsci/xunit-plugin+skip+threshold"`
- Searched: `gh api "search/code?q=repo:microsoft/azure-pipelines-tasks+failTaskOnSkippedTests"`
- **python/cpython**, `Lib/test/libregrtest/results.py` — <https://github.com/python/cpython/blob/37e98da7c19a9e5892ee756d6dee08225422cd49/Lib/test/libregrtest/results.py>
  License: PSF-2.0.
  Weakness: `is_all_good()` treats any skip as not-good, but `get_exitcode()` never consults skips — the definition drives only the "All N tests OK." banner; CPython ships this ADR's exact gap (and its `EXITCODE_NO_TESTS_RAN` fails total absence while partial absence passes).
  Copied: expected-vs-unexpected skip accounting.
  Vendored: docs/adr/prior-art/ADR-011/cpython_results.py blob:a35934fc2c9ca82afd6a873f3a3ef484bfa6102b
- **jenkinsci/xunit-plugin**, `SkippedThreshold.java` — <https://github.com/jenkinsci/xunit-plugin/blob/5fbba4002e02a66032804c5cace4cf51b20491cf/src/main/java/org/jenkinsci/plugins/xunit/threshold/SkippedThreshold.java>
  License: MIT (pom.xml; no top-level LICENSE).
  Weakness: gates aggregate skip counts/percentages only, never test identity — a specific vanished test is invisible while totals hold.
  Copied: skip thresholds as first-class build-verdict inputs.
  Vendored: docs/adr/prior-art/ADR-011/SkippedThreshold.java blob:26bb7e2dfac885b8236926b61758473b58b2d7ef
- **mesonbuild/meson**, `mtest.py` — <https://github.com/mesonbuild/meson/blob/1.5.1/mesonbuild/mtest.py>
  License: Apache-2.0.
  Weakness: SKIP is first-class (GNU exit-77, TAP directives) yet excluded from `is_bad()` and `total_failure_count()` — an all-skipped suite exits 0.
  Copied: structured per-test outcomes over process exit codes.
  Vendored: docs/adr/prior-art/ADR-011/mtest.py blob:c0ddb30bacf75e5304bb5b97bc2ed5f62587d0c9
- **jankatins/pytest-error-for-skips**, the `--error-for-skips` plugin — <https://github.com/jankatins/pytest-error-for-skips/blob/4c3eaae64e09dc077a52e219c3cf375e3e5dbdc0/pytest_error_for_skips.py>
  License: MIT.
  Weakness: a binary opt-in flag rewriting skip→failure inside pytest's own process — no identity, blind to deselection, and the tree under test decides whether the plugin runs at all.
  Vendored: docs/adr/prior-art/ADR-011/pytest_error_for_skips.py blob:0b71c43b365e716dedd787d1879f1e48250ace9f
- Rejected: <https://github.com/numirias/pytest-json-report> — a structured JSON reporter of per-test outcomes; it never changes pytest's own exit code and ships no policy for what an acceptable skip count is, so the gating decision this ADR writes down would still be unwritten.
- Rejected: <https://github.com/weiwei/junitparser> — a JUnit-XML parsing data model (`Element`/`TestCase`/`TestSuite`) with no threshold and no gate semantics; adopting it leaves the entire enforcement rule to be written from scratch.
- Rejected: <https://github.com/microsoft/azure-pipelines-tasks> — the assumed `failTaskOnSkippedTests` option does not exist; `PublishTestResultsV2`'s `task.json` ships only `failTaskOnFailedTests`, `failTaskOnFailureToPublishResults`, and `failTaskOnMissingResultsFile`. A verified-false lead, recorded rather than dropped.

## Considered Options

1. **A count-based ratchet** — "collected count must be ≥ previous accepted run". Rejected: identity-blind; five real tests swapped for five trivial ones keeps the count, and it drags cross-run state into a per-subject verdict.
2. **Parse stdout `PASSED` lines by regex.** Rejected: skip-blind under `-q`, and the format is plugin- and version-dependent; junitxml already exists to be the structured form regex is trying to reinvent.
3. **Widen the exit-code check to fail on any "skipped" substring.** Rejected: cannot name which test skipped, so a declared expected-skip and an undeclared one are indistinguishable.
4. **Structured per-test outcomes, diffed against a committed, freeze-time manifest of expected test IDs.** Chosen.

## Decision Outcome

In the context of a gate that must tell "the frozen suite ran and passed"
from "the frozen suite skipped itself into silence", facing structured
results that already exist (junitxml) and go unread, we chose **structured
suite verdicts, diffed against a committed, freeze-time manifest of expected
test IDs**, to make partial absence as visible as total absence already is,
accepting that a hostile tree can still forge the artifact it produces.

Concretely: the claim's argv carries `--junitxml=<fixed relative path>`
inside the digest-bound command; hermetic observation parses that artifact
before teardown and signs outcome counts, non-passed test IDs, and a
full-outcome digest into evidence (`ranex-evidence-v2` → `v3`); a committed
suite manifest — generated outcome-blind from the freeze-time run, naming any
declared expected-skips — is the frozen list the kernel diffs against; every
manifest ID must appear passed, except a declared expected-skip, which may
still pass.

### Consequences

- Good: a skip cannot pass as a proxy for "ran and succeeded" — an undeclared skip, xfail, xpass, error, or missing ID all read as FAIL.
- Good: expected-skips (e.g. the credential-gated e2e) stay legitimate without letting an implementer invent new ones — the manifest is freeze-ceremony-only.
- Good: the manifest and the gate parser share one code path, so ID spelling cannot drift between what was frozen and what is checked.
- Bad, and not closed: a hostile tree can still forge the junitxml via a planted `conftest.py` or an approved wheel's `pytest11` plugin (ADR-007; tests/security/test_slice006_approved_wheel_can_lie.py) — same trust level as the exit code it replaces.
- Bad: a pytest or toolchain upgrade can shift test IDs; bounded because the lock is pinned — a pytest bump is a lock change, which is a re-freeze ceremony anyway — not eliminated.
- Bad: evidence changes shape — a `v3`-expecting loader refuses an old `v2` record outright, so nothing old silently keeps working.
- Bad: one more committed artifact, the manifest, must stay in sync at freeze time; drift there is a re-freeze bug, not a runtime one.

### Confirmation

The slice must prove: an undeclared skip against a manifest ID blocks the
claim; a declared expected-skip that instead reports pass still satisfies the
claim; an xfail, xpass, error, or missing manifest ID each blocks; a
`pytest -k` deselection that drops a manifest ID blocks; a manifest edited in
the candidate commit changes nothing about how a delegated run is judged
(read from the base tree); an absent, unparseable, or duplicate-ID junitxml
file blocks; and a `conftest.py` forging the artifact is **not** blocked —
stated, not silently accepted as closed. Absent any one of these the ADR
stays `proposed`.

## Improvements on the prior art

1. **Test identity, not counts.** xunit-plugin and CPython's `is_all_good()` stop at counts or an unwired predicate; every manifest ID is checked by name, so swapped-in trivial tests cannot stand in for real ones.
2. **Wired to the verdict.** CPython computes `is_all_good()` and never calls it from `get_exitcode()`. Meson tracks SKIP and still excludes it from `is_bad()`. Here the blocking rule reads the summary directly.
3. **A declared exception, not a blind opt-in.** `pytest-error-for-skips` is one flag: any skip anywhere fails. Here a manifest names specific expected-skips, so the credential-gated e2e stays legitimate elsewhere.
4. **Base-tree trust for delegated judging**, adopted from a REFUTE panel run (tencent/hy3): the manifest is read from the dispatch-time base commit, never the candidate — a worker commit cannot shrink it to fit its own evasion.
5. **Outcome-blind manifest generation at freeze**, adopted from the same panel (qwen/qwen3-max): the manifest is the freeze-time test *ID set*, taken before outcome is read — impossible to green-wash under red-then-green.
6. **Not adopted, on the record:** count/ratchet designs and manifest generation from a passing run — both rejected above, and both traps the panel flagged independently before this ADR was written.

## Architecture surface

No new port. `gates.yaml`'s claim schema (`slice_gate_loader.py`) gains one
optional key for a suite claim — the junitxml path — validated by the same
refuse-unknown-keys discipline (`_CLAIM_KEYS`) that already rejects
`waiver`. Hermetic observation (SLICE-004's materialisation path) reads that
file before teardown; `foundation/signing.py`'s domain prefix moves
`ranex-evidence-v2` → `v3`. In `governed_execution/domain/verdict.py`,
`Evidence.satisfies` — today the one-line `exit_code == 0` — extends to
consult the new fields, and diagnosis gains a clause naming this failure
distinctly; `evaluate()`'s signature and purity do not change.

## Scope and threat delta

Governs how a `tests-executed`-shaped claim is judged; no trust boundary
moves. STRIDE: narrows **Spoofing** and **Repudiation** of "the tests ran" by
an honest-but-lazy process — a suite that skips or shrinks can no longer
claim it ran clean. Does not touch **Tampering** — a hostile tree can still
forge the junitxml the same way it could forge the old exit code.

Non-goal, stated plainly: no model judges whether a test is "realistic" or
whether the frozen suite is any good — nothing here improves the thrower's
aim. Out of scope, deliberately: adversarial forgery via `conftest.py` or an
approved wheel's `pytest11` plugin — that stays review's job until
merge-time re-check and verifiable separation land.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Functional correctness | a manifest ID reports skipped, undeclared | claim blocked, ID named |
| Functional correctness | a declared expected-skip reports pass | claim still satisfied |
| Integrity | candidate commit edits the manifest | judged from base tree, unaffected |
| Reliability | junitxml absent or unparseable | claim blocked, treated as absence |
| Maintainability | manifest and parser share one code path | ID spelling cannot drift between them |

## Reversibility

Door: two-way

The catalog argv key and the manifest file are both revertible — delete the
key, delete the manifest, and the claim reverts to exit-code-only. The
evidence domain bump is the sharp edge: an old verifier refuses a `v3`
record outright (`EVIDENCE_DOMAIN` is inside the signed bytes), so rollback
is a version revert plus re-observation, not a silent read. The journal is
append-only; nothing already recorded is invalidated either way.

## Sad paths

Derived by a decision table over (outcome kind × declaration state), plus
boundary values on artifact presence and well-formedness.

| # | Failure | Required behaviour |
|---|---|---|
| 1 | undeclared skip | blocks — absence |
| 2 | declared expected-skip, actually skipped | satisfies — permission, not obligation |
| 3 | declared expected-skip, reports pass instead | satisfies — passing is acceptable; the declaration is permission to skip, not an obligation |
| 4 | xfail | blocks — not a pass |
| 5 | xpass | blocks — not the declared outcome |
| 6 | error | blocks — absence |
| 7 | manifest ID missing from the artifact | blocks — absence |
| 8 | extra test ID beyond the manifest | satisfies nothing, blocks nothing — enters by re-freezing |
| 9 | artifact absent | blocks — absence |
| 10 | artifact unparseable or oversized XML | blocks — stdlib parser, entity-expansion hardening noted |
| 11 | duplicate test ID in the artifact | blocks — malformed, treated as absence |
| 12 | candidate commit edits the manifest | judged from base tree — changes nothing |
| 13 | in-tree `pyproject` `addopts` deselection drops a manifest ID | blocks — missing ID reads as FAIL |
| 14 | test ID drift on toolchain change | bounded — lock pinned; a pytest bump is a re-freeze; manifest and parser share one code path |
| 15 | implementer declares their own expected-skip | cannot — manifest is freeze-ceremony-only, already read-only to implementers |
| 16 | artifact forged (`conftest.py`, an approved wheel's `pytest11` plugin) | **not caught** — same trust level as the exit code it replaces |

## Test strategy

Levels: contract (docs discipline governs this ADR's own shape); security
(the observation this extends, and the forgery boundary it does not close);
e2e (the credential-gated skip this ADR's manifest must declare, not
invent).

`tests/contract/test_docs_discipline.py` is the check for this document
itself — run mid-draft against an incomplete version of this file and
observed failing (missing sections, thin sad paths, no `Vendored:` lines),
then green once every section, budget, and citation line was in place;
red-then-green observed directly here, not assumed.

`tests/security/test_slice004_hermetic_observation.py` is the hermetic-read
path SLICE-009 extends: today it proves state outside the tree never enters
the subject; the new suite-summary read must pass under the same
discipline — parsed before teardown, from the materialised sample, nothing
ambient.

`tests/security/test_slice006_approved_wheel_can_lie.py` is the forgery
boundary named in Consequences and sad path 16: it already proves a
`pytest11` plugin can force `session.exitstatus = 0` while a test fails, and
this ADR does not claim to close that — the new suite gains the same hole
under a different name (a forged junitxml) unless that file's own scope
changes first.

`tests/e2e/test_first_delegation.py` exercises the credential-gated path
(`OPENROUTER_API_KEY`) that SLICE-009's manifest must declare as an expected
skip — an existing example of the shape the manifest has to name, not a new
test.

SLICE-009 owns new tests, not named here: a manifest-vs-artifact unit suite
for the ID diff itself; a security test planting a `conftest.py` that
reports a false pass in the junitxml, to prove the summary is read
structurally and not trusted at face value; a contract test for the new
gates.yaml claim key. No global coverage percentage: delta coverage on
changed lines, full coverage of every blocking branch in the new rule.

## Code review checklist

- Does the manifest's test-ID set match the freeze-time run byte-for-byte, or could it have been hand-edited after?
- Is the new claim's argv still fully digest-bound — nothing appended by the runner outside the catalog?
- Does the observation path parse the junitxml before teardown, from the materialised sample, and nowhere else?
- Is a declared expected-skip narrated with a reason, not a bare test ID?
- Does any code path let a candidate commit's edited manifest affect its own judging?
- Is the `v2` → `v3` domain bump the only shape change, or did an unrelated field ride along?
- Would a reviewer reading only the diff — never the author's summary — reach the same verdict as the kernel?

## More Information

`governance/bom.yaml` FT-07 ("Enforce that the specified check was red
before execution and green after it.", status: `specified`) is the adjacent
unbuilt slot this mechanism will later serve — the freeze-time artifact this
ADR introduces is exactly the red-state record FT-07 needs.

No mature system found in this research enforces declared-vs-executed test
identity — a manifest diffed against a frozen ID set. CPython's
`-f/--fromfile` selects what runs; it never verifies what ran against what
was named. Meson's build-file test declarations are an implicit manifest
with no cross-check. That property is novel here, stated as such rather
than credited to prior art.

Superseded ADRs: none. Open: the manifest-vs-artifact diff implementation
itself, owned by SLICE-009.
