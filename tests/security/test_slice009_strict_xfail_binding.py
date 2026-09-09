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
