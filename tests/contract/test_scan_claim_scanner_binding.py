"""#110 Correction 2 — a scan claim's scanner is never a script the tree carries.

The issue's measured hole: containment inspects `argv[0]` only, so a claim
bound to a system interpreter plus an in-tree script that always exits 0 was
admitted, and the observed tree chose what the claim meant. The binding is
authored in the gate catalog, so the catalog is where it is refused: a
`sarif-2.1.0` claim may resolve its scanner from `argv[0]` (ruff) or from an
interpreter's own module/inline options (`python -m ranex.…`), never from a
script operand — whose bytes the loader cannot see, wherever they live.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.policy.adapters.configuration.yaml.slice_gate_loader import (
    load_gate,
    scripted_interpreter_operand,
)

ARTIFACT = "governance/scan.sarif"
SARIF_ARGV = ["--output-format=sarif", f"--output-file={ARTIFACT}"]


def catalog(command: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: SCAN_CLEAN\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(command)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        "        results_manifest: governance/scan-manifest.json\n"
    )


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- the operand locator, without a catalog ---------------------------------


@pytest.mark.parametrize(
    ("command", "operand"),
    [
        (["/usr/bin/python3", "neuter.py"], "neuter.py"),
        (["python3", "neuter.py"], "neuter.py"),
        (["/usr/bin/python3.14", "-P", "neuter.py"], "neuter.py"),
        (["python", "-u", "tools/run_scan.py"], "tools/run_scan.py"),
        (["python3", "-m", "pkg/neuter"], "pkg/neuter"),
        (["sh", "check.sh"], "check.sh"),
        (["/bin/bash", "-e", "scan.sh", "--flag"], "scan.sh"),
        (["node", "--max-old-space-size", "4096", "server.js"], "server.js"),
        (["php", "-f", "scan.php"], "scan.php"),
        (["ruby", "-rset", "scan.rb", "arg"], "scan.rb"),
    ],
)
def test_a_scripted_interpreter_names_its_script_operand(
    command: list[str], operand: str
) -> None:
    assert scripted_interpreter_operand(command) == operand


@pytest.mark.parametrize(
    "command",
    [
        ["/home/op/.local/bin/ruff", "check", "--output-format=sarif", "--output-file=x"],
        ["python3", "-P", "-m", "ranex.foundation.markers"],
        ["python", "-c", "print(1)"],
        ["python3", "-m", "pytest", "-q", "tests/test_x.py"],
        ["sh", "-c", "exit 0"],
        ["node", "-e", "console.log(1)"],
        ["node", "--eval", "code()", "server.js"],
        ["perl", "-e", "print 1"],
        ["uv", "run", "pytest", "-q"],
        ["echo", "neuter.py"],
    ],
)
def test_commands_without_a_script_operand_name_none(command: list[str]) -> None:
    assert scripted_interpreter_operand(command) is None


# --- the catalog refusal -----------------------------------------------------


@pytest.mark.parametrize(
    "argv0_and_operand",
    [
        (["/usr/bin/python3", "neuter.py"], "neuter.py"),
        (["python3", "neuter.py"], "neuter.py"),
        (["/bin/bash", "-e", "neuter.sh"], "neuter.sh"),
        (["node", "neuter.js"], "neuter.js"),
    ],
)
def test_a_scan_claim_bound_to_an_interpreter_script_is_refused_at_load(
    tmp_path: Path, argv0_and_operand: tuple[list[str], str]
) -> None:
    prefix, operand = argv0_and_operand
    with pytest.raises(ValueError) as raised:
        load_gate(write(tmp_path, catalog([*prefix, *SARIF_ARGV])), "landing")
    message = str(raised.value)
    assert operand in message, message
    assert "script" in message, message


def test_the_refusal_names_the_claim_and_the_fix(tmp_path: Path) -> None:
    with pytest.raises(ValueError) as raised:
        load_gate(
            write(tmp_path, catalog(["/usr/bin/python3", "neuter.py", *SARIF_ARGV])),
            "landing",
        )
    message = str(raised.value)
    assert "scan" in message, message
    assert "-m" in message, message


def test_the_module_form_is_the_shape_that_loads(tmp_path: Path) -> None:
    """The blessed marker-scanner argv: the installed kernel's interpreter, a
    module name, no path operand."""

    gate = load_gate(
        write(
            tmp_path,
            catalog(["/venv/bin/python3.14", "-P", "-m", "ranex.foundation.markers", *SARIF_ARGV]),
        ),
        "landing",
    )
    (claim,) = gate.required_claims
    assert claim.command[-2:] == tuple(SARIF_ARGV)


def test_a_ruff_shaped_scan_claim_still_loads(tmp_path: Path) -> None:
    gate = load_gate(
        write(
            tmp_path,
            catalog(
                [
                    "/home/op/.local/bin/ruff", "check", "--no-cache", "--isolated",
                    "--select=F401", "--exit-zero", *SARIF_ARGV, "pkg",
                ]
            ),
        ),
        "landing",
    )
    assert gate.required_claims[0].results_reporter == "sarif-2.1.0"


def test_an_inline_scanner_is_reviewed_bytes_and_loads(tmp_path: Path) -> None:
    """`-c` code is catalog-supplied and review sees it; the tree supplies
    nothing. Whether it substantiates the claim remains review's judgement."""

    load_gate(
        write(tmp_path, catalog(["python3", "-c", "import ranex.foundation.markers", *SARIF_ARGV])),
        "landing",
    )


def test_a_junit_claim_may_still_bind_an_in_tree_check_script(
    tmp_path: Path,
) -> None:
    """The scanner rule is scoped to scan claims. A suite claim bound to a
    committed check script is a separately recorded stance (SLICE-003), and
    this slice does not reverse it by accident."""

    text = (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: tests-executed\n"
        '        command: ["sh", "check.sh", "--junitxml=governance/suite_results.xml"]\n'
        '        results_artifact: governance/suite_results.xml\n'
    )
    gate = load_gate(write(tmp_path, text), "landing")
    assert tuple(gate.required_claims[0].command)[:2] == ("sh", "check.sh")
