# ADR-056 — a suite claim must ask for the outcome it judges

**Status:** accepted

**Date:** 2026-09-08
**Decision-makers:** repo owner
**Supersedes nothing.** Closes the gap ADR-011 recorded on 2026-09-05 in its
"Release audit correction" subsection; ADR-011's decision is unchanged.

## Context

ADR-011 sad path 5 requires an XPASS to block a suite claim. The 2026-09-05
release audit (FINDINGS F-010) measured that it does not.

Reproduced again on 2026-09-08 against the installed pytest. A test carrying an
ordinary, non-strict `@pytest.mark.xfail` that passes anyway is reported by
pytest as `1 xpassed`, and written to the JUnit artifact as:

```xml
<testcase classname="test_xp" name="test_nonstrict_xpass" time="0.001" />
```

A bare element with no outcome child — byte-for-byte the shape of an ordinary
pass. The `<testsuite>` attributes do not carry it either: `failures="0"`,
`errors="0"`, and the XPASS is not counted in `skipped`.

`foundation/suite_results._outcome` therefore reads `passed`, and the gate
records PASS. This is not a parser defect. The information the kernel is
required to judge was never written to the bytes it judges, and no amount of
parsing recovers it. A stdout heuristic would recover it and was refused: the
whole point of ADR-011 was to stop reading verdicts out of prose.

## Decision

**The information has to be requested before the artifact is written, so it
belongs in the one thing the kernel already binds and digests: the claim's
argv.** A `pytest-junit` suite claim must carry the exact adjacent tokens
`-o xfail_strict=true`, and must not carry an argv token that switches the
observation back off. A `Gate` built from such a claim is refused.

With the override set, the same XPASS is written as:

```xml
<failure message="[XPASS(strict)] known">[XPASS(strict)] known</failure>
```

which the *unchanged* summariser already classifies as `xpassed`. No evaluation
code moved; `evaluate()` did not move; `KERNEL_DIGEST` did not move.

### Where the refusal lives, and why not at the parse

Refused when the `Gate` is **constructed**, not when the catalog YAML is
parsed. The standing invariant names gate construction — "a gate that cannot
block is refused at construction" — and a suite claim blind to one of its own
declared sad paths is exactly that gate. The YAML loader is a parser, and the
distinction is load-bearing rather than pedantic:

A delegated run reads its catalog from the **dispatch base commit**, never from
the candidate (ADR-011's base-tree trust rule). A kernel that refused the parse
would therefore make every commit predating this change unloadable — including
for looking up claims that declare no suite at all. That was not hypothetical:
the first implementation refused at parse time and broke
`test_provider_neutral_adapter_real`, which materialises the repository at a
pinned historical commit and dispatches with `--claim
provider-neutral-real-e2e`. That claim does not exist in the historical
catalog, so the suite path was never taken; the journey died on the parse
alone.

The guarantee is unchanged because `results_artifact` has a small, enumerated
set of consumers, and every one refuses before a suite claim decides anything:

| consumer | what it decides |
|---|---|
| `bootstrap/composition.py` — `GateEvaluator.evaluate` | builds the `Gate` for `gate evaluate` |
| `cli/main.py` — `cmd_task_judge` | builds its **own** `Gate`, separately |
| `cli/delegation.py` — the suite branch | runs the dispatch-time suite |
| `cli/main.py` — `run` | signs suite evidence |

The second row was found by the test that enumerates them, not by review:
`task judge` duplicates the composition root's `Gate(...)` construction, so a
refusal placed only in the composition root left a second path to a verdict.
`test_every_consumer_of_results_artifact_refuses_a_blind_claim` scans
`src/ranex` for `.results_artifact` attribute access and fails on any reader
that does not carry the refusal, so a fifth consumer cannot be added silently.

The refusal refuses, it does not inject. An injected token would make the
recorded command differ from the argv that actually ran, and the digest binding
is the reason that comparison is worth anything.

### Also refused, and why — each measured, not assumed

| argv | Measured effect with the override set |
|---|---|
| `--runxfail` | the xfail marker is treated as absent; the XPASS is a bare passing testcase again |
| `-p no:skipping`, in any spelling | unloads the plugin implementing xfail **and skip**, so a declared `@pytest.mark.skip` also becomes a bare pass — this one defeats "a skip is absence" outright, not only the XPASS arm. pytest ships no long form for `-p`, but the value may be attached (`-pno:skipping`) or the flag repeated, so the guard matches the plugin name as a substring rather than enumerating spellings — the `/bin/true` denylist lesson from SLICE-003 |
| `-o xfail_strict=false`, or a second override after the first | the later override wins, and the head of the argv still reads correct to a reviewer |
| a bare `xfail_strict=true` with no preceding `-o` | pytest reads it as a file path; the suite is not strict at all |
| `-oxfail_strict=true`, `--override-ini=xfail_strict=true` | *would* work; refused deliberately — one canonical spelling, not a reimplementation of pytest's argument parser inside the trust root (the same reasoning the vitest binding already uses) |
| the pair after a `--` | option parsing has ended; it is a path |

### Scope

`vitest-junit` claims are unaffected and are not asked for an equivalent.
Vitest's `test.fails` already fails a test that unexpectedly passes, so there is
no non-strict spelling to close.

Qualification claims are unaffected: they report no test outcomes, and demanding
a pytest option there would be cargo cult.

## What this does NOT close — measured, not predicted

`-o xfail_strict=true` supplies the **ini default** for markers that state no
`strict`. A marker-level kwarg overrides it. Measured against the installed
pytest, one run, one command, both markers in the same file:

```
@pytest.mark.xfail(reason=...)                 -> <failure>   visible, blocks
@pytest.mark.xfail(strict=False, reason=...)   -> bare pass   invisible
```

So a suite that writes `strict=False` explicitly still receives gate PASS on an
XPASS. This is **not** the hostile-`conftest.py` boundary: `strict=False` is an
ordinary, legitimate pytest idiom, and an honest repository using it gets no
detection. Nothing in a digest-bound argv can override a kwarg written in the
tree under test.

This was found by `release_audit.py` against the real external subject, after
the change was already committed and its unit-level pin was green — the arm
injects an explicit `strict=False` marker and is **GAP at both v0.1.0 and
HEAD**, unmoved by this ADR. Recorded rather than quietly narrowed: the earlier
revision of this document claimed sad path 5 was now true of an ordinary suite
without stating which markers "ordinary" excludes.

Closing the remainder needs a kernel-owned reporter that reads
`report.wasxfail` — which pytest sets on exactly this case and `junitxml`'s
`append_pass` discards — and that is separate product work, not a tightening of
this rule.

## Consequences

- Good: ADR-011 sad path 5 holds for a marker that states no `strict`, which is
  the case F-010 originally measured on `benjaminp/six`'s own suite — no longer
  only for one whose author wrote `strict=True` everywhere.
- Good: the two ways of blinding the reporter that a hostile-but-committed argv
  could use are named refusals with the measured reason attached.
- Good: historical catalogs still parse, so delegated judging of a pre-existing
  base commit is not retroactively bricked for unrelated claims.
- Bad: every existing `pytest-junit` claim catalog can no longer produce a
  suite verdict until it carries the token. That is the intended blast radius —
  a catalog that does not carry it has the finding.
- Bad, unchanged: a hostile tree can still forge the artifact via `conftest.py`
  or an approved `pytest11` plugin (ADR-007, ADR-011 criterion 10). This ADR
  moves no trust boundary; it closes an *honest-process* blind spot, the same
  class ADR-011 exists to close.
- Bad, and stated rather than closed: the rule reads the *argv*, which is what
  the kernel binds and digests. `PYTEST_ADDOPTS` and `PYTEST_PLUGINS` are
  environment, not argv, and a tree that unloads the plugin from its own
  `conftest.py` is the forgery case above. Neither is claimed closed here.

## Confirmation

`tests/security/test_slice009_strict_xfail_binding.py` — the canonical argv
builds a Gate; the pre-fix shape is refused; each blinding argv above is
refused; a historical catalog still *parses* while refusing to build; vitest and
qualification claims are untouched; every consumer of `.results_artifact` in
`src/ranex` carries the refusal; and this repository's own committed
`governance/gates.yaml` carries the binding.

`tests/unit/test_suite_results.py::test_a_non_strict_xpass_is_only_visible_when_the_argv_asks_for_it`
— the reporter half, run against the installed pytest rather than a hand-written
XML fixture: the same source yields `passed: 1` without the override and
`non_passed: [[id, "xpassed"]]` with it.

## Prior art and the competing products

- **pytest 9.1.1** (the pinned version; MIT), read at source rather than only
  measured. Reference materialised from the PyPI sdist
  `sha256:1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313`,
  recorded upstream identity `pytest-dev/pytest@cf470ec0bf7eb89cd97dd56df4859eae5db46447`;
  parity against that commit is *drift* (9 files present only in the sdist), so
  the checksum above is the authority for these lines, not the git tree.
  - `src/_pytest/skipping.py`, `pytest_runtest_makereport`: on `call`, a strict
    xfail sets `rep.outcome = "failed"` and
    `rep.longrepr = "[XPASS(strict)] " + xfailed.reason`; a non-strict one sets
    `rep.outcome = "passed"` and records the fact only as the `rep.wasxfail`
    attribute.
  - `src/_pytest/junitxml.py`, `pytest_runtest_logreport`: `if report.passed:`
    calls `append_pass`, whose whole body is `self.add_stats("passed")`. It
    never reads `wasxfail`.
  So the XPASS *is* known to pytest and is dropped on the way into the artifact.
  That is the mechanism behind the measurement above, and it is why the fix has
  to change what is asked for rather than what is parsed.
- **jankatins/pytest-error-for-skips** (ADR-011 prior art, vendored) — turns
  skips into errors from inside pytest's process. Same weakness as before: the
  tree under test decides whether the plugin loads. Here the requirement lives
  in the committed, digest-bound argv instead, so removing it changes the
  command digest and the claim stops being satisfied.
- **Chock governance check** — compiles committed YAML policy into agent hooks,
  git hooks and CI gates, and grades coverage per policy × agent. Compared with
  its published Marketplace description, not an executed installation. It
  governs *what an agent may do*; this ADR governs *whether the evidence a
  verdict rests on can see the outcome it claims to judge*. Different layers;
  nothing here establishes parity or superiority in either direction.
- **microsoft/agent-governance-toolkit** — intercepts tool calls before
  execution with a Merkle-logged decision record. Also read from its published
  README only. Same distinction: pre-execution authorisation, not post-execution
  evidence sufficiency.
- Not adopted: parsing pytest's stdout summary line for `xpassed`, and
  inferring an XPASS from `<testsuite>` count arithmetic. The first reintroduces
  exactly what ADR-011 removed; the second is unsound — the attributes do not
  carry the outcome, as measured above.

## Reversibility

Door: two-way. Delete `_reject_pytest_xfail_blindness` and the tokens from the
catalog and the claim reverts to the pre-2026-09-08 behaviour, finding and all.
No evidence shape changed, no signing domain moved, and nothing already in the
append-only journal is invalidated — the recorded command digests simply differ
before and after, which is the correct reading of a changed bound command.
