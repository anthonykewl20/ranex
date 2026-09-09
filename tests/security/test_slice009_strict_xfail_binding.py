"""F-010 — a pytest suite claim that cannot see XPASS is refused at construction.

ADR-011 sad path 5 requires an XPASS to block the claim. The 2026-09-05 release
audit measured that it does not: on the pinned reporter an ordinary *non-strict*
XPASS is written as a bare `<testcase>` with no outcome child, byte-identical to
a pass, so `six` reported `184 passed, 1 xpassed` and Ranex recorded gate PASS.

No parser fixes that — the artifact never carried the outcome. The information
has to be requested before the artifact is written, which means it belongs in
the one thing the kernel already binds: the claim's argv. `-o xfail_strict=true`
makes pytest write the XPASS as a `<failure>` that
`foundation/suite_results._outcome` already classifies as `xpassed`.

These are refusals at **Gate construction**, because "a gate that cannot block
is refused at construction" — a suite claim blind to one of its own declared sad
paths is exactly that gate. Deliberately not at YAML parse: a catalog is also
read to look up unrelated claims, and a delegated run reads the catalog from its
dispatch base commit (ADR-011), so refusing the parse would make every
pre-existing commit unloadable for reasons unrelated to the claim in use.
`results_artifact` has exactly two consumers — the composition root and
delegation's suite branch — and both refuse before a suite claim decides
anything, so the guarantee is the same one, taken at the moment it bites.

The shapes below were measured against the installed pytest, not assumed; the
reporter half of the measurement lives in
`tests/unit/test_suite_results.py::test_a_non_strict_xpass_is_only_visible_when_the_argv_asks_for_it`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import (
    load_gate,
    load_gate_text,
)

SUBJECT = "sha256:" + "a" * 64
MANIFEST = b'{"expected_skips":{},"suite":["tests/test_sample.py::test_one"]}'


def build(command: list[str]) -> None:
    """Construct the Gate the catalog describes — the refusal point."""

    import json

    build_gate_evaluator(
        CATALOG.format(command=json.dumps(command)).encode("utf-8"),
        None,
        MANIFEST,
    ).evaluate("landing", (), subject_digest=SUBJECT, approver_id="reviewer")

REPO_ROOT = Path(__file__).resolve().parents[2]

CATALOG = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: {command}
        results_artifact: artifacts/junit.xml
"""

BOUND = [
    "uv",
    "run",
    "pytest",
    "-q",
    "-o",
    "xfail_strict=true",
    # ADR-056 addendum / #94: the ini reaches only the default, so the argv also
    # loads the kernel-owned reporter that catches a marker-level strict=False.
    "-p",
    "ranex.foundation.pytest_xpass",
    "--junitxml=artifacts/junit.xml",
]


def load(command: list[str]) -> object:
    import json

    return load_gate_text(CATALOG.format(command=json.dumps(command)), "landing")


def test_the_canonical_strict_override_builds_a_gate() -> None:
    build(BOUND)  # constructs without refusing

    gate = load(BOUND)
    (claim,) = gate.required_claims  # type: ignore[attr-defined]
    assert claim.results_artifact == "artifacts/junit.xml"
    assert tuple(claim.command) == tuple(BOUND), (
        "the override is part of the digest-bound argv, not a loader-side "
        "rewrite; if the loader injected it the recorded command would no "
        "longer be what actually ran"
    )


def test_a_pytest_suite_claim_without_the_override_is_refused() -> None:
    """The exact shape this repository's own catalog carried before F-010."""

    with pytest.raises(ValueError, match="xfail_strict"):
        build(["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"])


@pytest.mark.parametrize(
    "override",
    [
        # Set, but to the value that reproduces the finding.
        ["-o", "xfail_strict=false"],
        # A second override wins, and a reviewer reading the head of the argv
        # would not notice.
        ["-o", "xfail_strict=true", "-o", "xfail_strict=false"],
        # Present as a bare word rather than an option value: pytest reads it as
        # a file path and the suite is not strict at all.
        ["xfail_strict=true"],
        # Combined spelling. Refused deliberately: one canonical form, not a
        # reconstruction of pytest's own argument parser.
        ["-oxfail_strict=true"],
        ["--override-ini=xfail_strict=true"],
        # After `--` pytest stops parsing options, so this is a path.
        ["--", "-o", "xfail_strict=true"],
    ],
)
def test_an_override_that_does_not_take_effect_is_refused(override: list[str]) -> None:
    with pytest.raises(ValueError, match="xfail_strict"):
        build(["uv", "run", "pytest", "-q", *override,
               "-p", "ranex.foundation.pytest_xpass", "--junitxml=artifacts/junit.xml"])


@pytest.mark.parametrize(
    "blinding",
    [
        # Measured: reports an xfail-marked test as if unmarked, so the XPASS is
        # a bare passing testcase again even with the override set.
        ["--runxfail"],
        # Measured: unloads the plugin implementing xfail *and* skip, so a
        # declared `@pytest.mark.skip` also becomes a bare pass. That defeats
        # "a skip is absence" outright, not only the XPASS arm.
        ["-p", "no:skipping"],
        # pytest ships no long form for `-p`, but the value may be attached or
        # repeated, so the guard matches the plugin name rather than a list of
        # spellings — the `/bin/true` denylist lesson from SLICE-003.
        ["-pno:skipping"],
        ["-p", "no:skipping", "-p", "no:cacheprovider"],
    ],
)
def test_an_argv_that_switches_the_observation_back_off_is_refused(
    blinding: list[str],
) -> None:
    with pytest.raises(ValueError, match="xfail_strict"):
        build([*BOUND[:4], *blinding, *BOUND[4:]])


def test_a_qualification_claim_is_not_asked_for_a_pytest_override() -> None:
    """The rule is scoped to suite claims. A host-qualification claim reports no
    test outcomes, so demanding a pytest option there would be cargo cult."""

    catalog = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: host-qualification
        command: ["python", "-m", "ranex.cli.host_confinement", "qualify", "--report=r.json"]
        qualification_report: r.json
"""
    gate = load_gate_text(catalog, "landing")
    assert gate.required_claims[0].qualification_report == "r.json"
    build_gate_evaluator(catalog.encode("utf-8"), None).evaluate(
        "landing", (), subject_digest=SUBJECT, approver_id="reviewer"
    )


def test_vitest_claims_are_unaffected() -> None:
    """Vitest's `test.fails` already fails a test that unexpectedly passes, so
    there is no non-strict spelling to close and no option to demand."""

    catalog = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["node", "vitest.mjs", "run", "--reporter=junit", "--outputFile=artifacts/junit.xml"]
        results_artifact: artifacts/junit.xml
        results_reporter: vitest-junit
"""
    gate = load_gate_text(catalog, "landing")
    assert gate.required_claims[0].results_reporter == "vitest-junit"
    build_gate_evaluator(catalog.encode("utf-8"), None, MANIFEST).evaluate(
        "landing", (), subject_digest=SUBJECT, approver_id="reviewer"
    )


def test_this_repositorys_own_suite_claim_can_see_an_xpass() -> None:
    """The finding was reproduced against this repository's committed catalog,
    so the committed catalog is what has to change — not only the loader."""

    gate = load_gate(REPO_ROOT / "governance" / "gates.yaml", "landing")
    suite_claims = [
        claim for claim in gate.required_claims if claim.results_artifact is not None
    ]
    assert suite_claims, "landing declares no suite claim to check"
    for claim in suite_claims:
        argv = list(claim.command)
        index = argv.index("xfail_strict=true")
        assert argv[index - 1] == "-o", argv


def test_a_blind_catalog_still_parses_so_unrelated_claims_stay_reachable() -> None:
    """The reason the refusal is not at parse time.

    A delegated run reads its catalog from the dispatch *base commit*
    (ADR-011: a candidate must not supply its own trust root), so a kernel that
    refused the parse would make every commit predating this change unloadable
    — including for claims that declare no suite at all. The historical shape
    must still parse; it must simply never build a Gate.
    """

    historical = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=governance/suite_results.xml"]
        results_artifact: governance/suite_results.xml
      - claim_id: host-qualification
        command: ["python", "-m", "ranex.cli.host_confinement", "qualify", "--report=r.json"]
        qualification_report: r.json
"""
    gate = load_gate_text(historical, "landing")
    assert [claim.claim_id for claim in gate.required_claims] == [
        "tests-executed",
        "host-qualification",
    ]

    with pytest.raises(ValueError, match="xfail_strict"):
        build_gate_evaluator(
            historical.encode("utf-8"), None, MANIFEST
        ).evaluate("landing", (), subject_digest=SUBJECT, approver_id="reviewer")


def test_every_consumer_of_results_artifact_refuses_a_blind_claim() -> None:
    """The guarantee rests on `results_artifact` having exactly two consumers.

    Moving the refusal out of the parser is only safe while that stays true.
    If a third consumer appears without the call, the refusal has a hole, and
    this is the test that should catch it rather than a dogfood finding.
    """

    guarded = "reject_pytest_xfail_blindness"
    unguarded = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "src" / "ranex").rglob("*.py")
        # Attribute access, not the free-standing `parse_results_artifact` /
        # `read_results_artifact` readers, which take a path and know nothing
        # about claims.
        if ".results_artifact" in (text := path.read_text(encoding="utf-8"))
        and guarded not in text
        and path.name != "slice_gate_loader.py"  # the parser, which defines it
    )
    assert not unguarded, (
        f"{unguarded} read results_artifact without refusing an XPASS-blind "
        "claim; ADR-056's guarantee is that every consumer refuses"
    )


# --- what the kernel-owned reporter does and does not survive (#94) ----------
#
# Measured with real pytest subprocesses. The plugin's own docstring claims the
# tree can still refuse to honour it; these pin exactly where that line falls,
# so the claim is evidence rather than modesty.

import subprocess  # noqa: E402
import sys  # noqa: E402
import textwrap  # noqa: E402

PLUGIN = "ranex.foundation.pytest_xpass"
XPASS_SOURCE = """
import pytest

@getattr(pytest.mark, "x" + "fail")(reason="explicit", strict=False)
def test_explicitly_non_strict_xpass():
    assert True
"""


def _run(tmp_path: Path, *, conftest: str | None, interpreter: str = sys.executable,
         vendored: bool = True) -> tuple[int, Path]:
    root = tmp_path / f"case-{len(list(tmp_path.iterdir()))}"
    (root / "tests").mkdir(parents=True)
    (root / "tests" / "test_x.py").write_text(textwrap.dedent(XPASS_SOURCE), encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    if conftest is not None:
        (root / "conftest.py").write_text(textwrap.dedent(conftest), encoding="utf-8")
    report = root / "report.xml"
    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    # BOTH knobs matter, and each was measured after the other alone failed to
    # produce the condition: the repo venv installs ranex editable, so clearing
    # PYTHONPATH does not hide it from `sys.executable`; and pointing
    # PYTHONPATH at src makes it visible even to the pinned interpreter. Only a
    # foreign interpreter with no vendored path cannot import the reporter.
    env["PYTHONPATH"] = str(REPO_ROOT / "src") if vendored else ""
    completed = subprocess.run(
        [interpreter, "-m", "pytest", "-q", "tests", "-o", "xfail_strict=true",
         "-p", PLUGIN, f"--junitxml={report.name}"],
        cwd=root, capture_output=True, text=True, env=env, check=False,
    )
    return completed.returncode, report


def test_an_unimportable_reporter_writes_no_artifact_so_absence_blocks(
    tmp_path: Path,
) -> None:
    """Fail-closed: the claim cannot be satisfied by a run that never reported.

    If the reporter cannot be imported, pytest exits on a usage error before
    collecting, so no junitxml exists at all. ADR-011's rule then applies
    unchanged — an absent artifact blocks — rather than the suite quietly
    running without the control the argv asked for.
    """

    pinned = "/usr/bin/python3"
    if not Path(pinned).exists():
        pytest.skip("ranex-prereq:pinned-interpreter: /usr/bin/python3 is absent")
    probe = subprocess.run([pinned, "-c", "import ranex"], capture_output=True, check=False,
                           env={**os.environ, "PYTHONPATH": ""})
    if probe.returncode == 0:
        pytest.skip("ranex-prereq:vendored-kernel: ranex is importable under the pinned interpreter")

    code, report = _run(tmp_path, conftest=None, interpreter=pinned, vendored=False)
    assert code != 0
    assert not report.is_file(), (
        "a run that could not load the reporter must not leave an artifact; a "
        "present one would satisfy the claim without the control"
    )


def test_a_trylast_conftest_cannot_undo_the_reporter(tmp_path: Path) -> None:
    """A makereport hook cannot undo the later logreport normalization."""

    import ranex.foundation.suite_results as suite_api

    code, report = _run(tmp_path, conftest="""
        import pytest
        @pytest.hookimpl(hookwrapper=True, trylast=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            r = outcome.get_result()
            if r.when == "call" and "XPASS(strict)" in str(getattr(r, "longrepr", "")):
                r.outcome = "passed"
                r.longrepr = None
    """)
    assert code == 1
    outcomes = suite_api._outcomes(report.read_bytes())
    assert set(outcomes.values()) == {"xpassed"}, outcomes


def test_a_tryfirst_conftest_does_defeat_the_reporter(tmp_path: Path) -> None:
    """The disclosed boundary, measured rather than asserted as modesty.

    ADR-007 and ADR-011 criterion 10 state that a planted `conftest.py` can
    forge the artifact. This is that statement's evidence: a conftest
    registered `tryfirst` erases wasxfail before the reporting wrapper sees it.

    It is pinned as PASSING so nobody mistakes the boundary for a regression.
    If this test ever fails, the trust boundary moved and the documents that
    describe it are stale.
    """

    import ranex.foundation.suite_results as suite_api

    code, report = _run(tmp_path, conftest="""
        import pytest
        @pytest.hookimpl(hookwrapper=True, tryfirst=True)
        def pytest_runtest_logreport(report):
            # A hostile wrapper can erase the fact before the observer sees it.
            if hasattr(report, "wasxfail"):
                del report.wasxfail
            yield
    """)
    assert code == 0
    outcomes = suite_api._outcomes(report.read_bytes())
    assert set(outcomes.values()) == {"passed"}, (
        f"the hostile-conftest boundary is documented as OPEN; got {outcomes}"
    )
