"""The antislop claim surface: one more SARIF family, the same discipline.

An `antislop-sarif-2.1.0` claim is authored exactly like a scan claim — a
scanner bound as the kernel's own entry point, one canonical argv, a frozen
manifest the loader refuses to leave out — and its expectations answer the
same three questions every manifest kind answers at Gate construction, so
no construction site learns a third shape.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import claim_expectations
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate

ARTIFACT = "governance/antislop/scan.sarif"
MANIFEST = "governance/antislop/expectations.json"
ARGV = ["ranex", "antislop", "--output-format=sarif", f"--output-file={ARTIFACT}"]


def catalog(
    command: list[str] | None = None,
    *,
    reporter: str = "antislop-sarif-2.1.0",
    artifact: str = ARTIFACT,
    manifest: str | None = MANIFEST,
) -> str:
    entry = (
        "      - claim_id: antislop\n"
        f"        command: {json.dumps(command if command is not None else ARGV)}\n"
    )
    if artifact is not None:
        entry += f"        results_artifact: {artifact}\n"
    if reporter is not None:
        entry += f"        results_reporter: {reporter}\n"
    if manifest is not None:
        entry += f"        results_manifest: {manifest}\n"
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: ANTISLOP_SANE\n"
        "    blocking: true\n"
        "    required_claims:\n" + entry
    )


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_well_formed_antislop_claim_loads(tmp_path: Path) -> None:
    gate = load_gate(write(tmp_path, catalog()), "landing")
    (claim,) = gate.required_claims
    assert claim.claim_id == "antislop"
    assert claim.results_reporter == "antislop-sarif-2.1.0"
    assert claim.results_artifact == ARTIFACT
    assert claim.results_manifest == MANIFEST
    assert claim.command == tuple(ARGV)


def test_an_antislop_claim_without_a_manifest_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="without a results_manifest"):
        load_gate(write(tmp_path, catalog(manifest=None)), "landing")


def test_an_antislop_claim_binds_exactly_one_output_pair(tmp_path: Path) -> None:
    # A second output token — any spelling — is refused; `--root` is the
    # scanner's own reviewed narrowing knob and stays legal, as scan scope is.
    with pytest.raises(ValueError, match="exactly"):
        load_gate(
            write(
                tmp_path,
                catalog(command=[*ARGV, "--output-file=other.sarif"]),
            ),
            "landing",
        )
    with pytest.raises(ValueError, match="exactly"):
        load_gate(
            write(
                tmp_path,
                catalog(command=["ranex", "antislop", f"--output-file={ARTIFACT}"]),
            ),
            "landing",
        )


def test_an_antislop_claim_never_binds_a_script_operand(tmp_path: Path) -> None:
    """#110 Correction 2's rule, inherited by the new family: a script the
    observed tree carries chooses what the claim means."""

    with pytest.raises(ValueError, match="script operand"):
        load_gate(
            write(
                tmp_path,
                catalog(
                    command=[
                        "python3",
                        "neuter.py",
                        "--output-format=sarif",
                        f"--output-file={ARTIFACT}",
                    ]
                ),
            ),
            "landing",
        )


def test_an_antislop_manifest_is_not_a_scan_manifest() -> None:
    """The two SARIF families freeze different universes; the dispatch that
    resolves a reporter's expectations refuses the wrong vocabulary rather
    than silently reducing one shape as the other."""

    raw = canonical_json_bytes(
        {"scope": ["test_six.py"], "tests": {"test_six.py::test_add_doc": 1}}
    )
    with pytest.raises(ValueError, match="scan manifest must contain"):
        claim_expectations(raw, "sarif-2.1.0")
    scan_raw = canonical_json_bytes(
        {
            "scope": ["test_six.py"],
            "rules": ["ranex/marker-shortcut"],
            "blocking_levels": ["error"],
            "accepted": {},
        }
    )
    with pytest.raises(ValueError, match="antislop expectations must contain"):
        claim_expectations(scan_raw, "antislop-sarif-2.1.0")


def test_claim_expectations_answers_the_three_questions() -> None:
    raw = canonical_json_bytes(
        {
            "scope": ["test_six.py"],
            "tests": {"test_six.py::TestX::test_add_doc": 2},
        }
    )
    digest, expected_ids, expected_skips = claim_expectations(
        raw, "antislop-sarif-2.1.0"
    )
    assert digest.startswith("sha256:")
    assert expected_ids == ("test_six.py", "test_six.py::TestX::test_add_doc")
    # No acceptance vocabulary exists in this family: a slop shape or a
    # count shortfall is never review-waved, so there are no expected skips.
    assert expected_skips == {}


def test_claim_expectations_refuses_tampered_bytes() -> None:
    raw = canonical_json_bytes(
        {"scope": ["test_six.py"], "tests": {"test_six.py::test_add_doc": 1}}
    )
    padded = raw[:-1] + b" "
    with pytest.raises(ValueError):
        claim_expectations(padded, "antislop-sarif-2.1.0")
