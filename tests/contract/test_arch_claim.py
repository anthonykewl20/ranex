"""The architecture-freeze claim surface: a scan claim like any other.

ADR-065's first claim family is authored exactly like a ruff scan claim —
the kernel's own console script as the scanner, the two canonical SARIF
tokens, its own frozen manifest — plus the one token this family adds: the
digest pin that binds the freeze's bytes to the catalog that names it. The
loader's existing guarantees (script-operand refusal, exact output tokens,
manifest required) are inherited, and these tests pin that inheritance plus
the digest pin's own refusal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate

ARTIFACT = "governance/arch/scan.sarif"
MANIFEST = "governance/arch/scan-manifest.json"
FREEZE = "governance/architecture-freeze.json"
DIGEST = "sha256:" + "0" * 64
ARGV = [
    "ranex-arch",
    "check",
    "--freeze",
    FREEZE,
    "--expected-freeze-digest",
    DIGEST,
    "--output-format=sarif",
    f"--output-file={ARTIFACT}",
]


def catalog(
    command: list[str] | None = None,
    *,
    reporter: str | None = "sarif-2.1.0",
    artifact: str | None = ARTIFACT,
    manifest: str | None = MANIFEST,
) -> str:
    entry = (
        "      - claim_id: architecture\n"
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
        "    rule_id: ARCHITECTURE_FROZEN\n"
        "    blocking: true\n"
        "    required_claims:\n" + entry
    )


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_well_formed_architecture_claim_loads(tmp_path: Path) -> None:
    gate = load_gate(write(tmp_path, catalog()), "landing")
    (claim,) = gate.required_claims
    assert claim.claim_id == "architecture"
    assert claim.results_reporter == "sarif-2.1.0"
    assert claim.results_artifact == ARTIFACT
    assert claim.results_manifest == MANIFEST
    assert claim.command == tuple(ARGV)


def test_the_scanner_is_the_kernel_never_a_script_operand(tmp_path: Path) -> None:
    """#110 Correction 2, as the micro-exercise met it live: a scripted
    interpreter bound to a script operand is refused (and a path-like `-m`
    value is still a script operand). The console script is the production
    shape; a module name also loads, though governed runs cannot use it —
    argv[0] resolution loses the venv, measured in the ADP proof."""

    with pytest.raises(ValueError, match="script operand"):
        load_gate(
            write(
                tmp_path,
                catalog(
                    command=[
                        "python",
                        "tools/arch_scan.py",
                        "--output-format=sarif",
                        f"--output-file={ARTIFACT}",
                    ]
                ),
            ),
            "landing",
        )
    with pytest.raises(ValueError, match="script operand"):
        load_gate(
            write(
                tmp_path,
                catalog(
                    command=[
                        "python",
                        "-m",
                        "tools/arch_scan.py",
                        "--output-format=sarif",
                        f"--output-file={ARTIFACT}",
                    ]
                ),
            ),
            "landing",
        )
    gate = load_gate(write(tmp_path, catalog()), "landing")
    assert gate.required_claims[0].command[0] == "ranex-arch"
    module_form = load_gate(
        write(
            tmp_path,
            catalog(
                command=[
                    "python",
                    "-m",
                    "ranex.foundation.arch_scan",
                    "check",
                    "--freeze",
                    FREEZE,
                    "--expected-freeze-digest",
                    DIGEST,
                    "--output-format=sarif",
                    f"--output-file={ARTIFACT}",
                ]
            ),
        ),
        "landing",
    )
    assert module_form.required_claims[0].command[1:3] == (
        "-m",
        "ranex.foundation.arch_scan",
    )


def test_the_claim_binds_exactly_one_output_pair(tmp_path: Path) -> None:
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
                catalog(
                    command=[
                        "python",
                        "-m",
                        "ranex.foundation.arch_scan",
                        "check",
                        "--freeze",
                        FREEZE,
                        "--expected-freeze-digest",
                        DIGEST,
                        f"--output-file={ARTIFACT}",
                    ]
                ),
            ),
            "landing",
        )


def test_a_claim_without_a_manifest_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="without a results_manifest"):
        load_gate(write(tmp_path, catalog(manifest=None)), "landing")


def test_the_digest_pin_rides_the_signed_argv(tmp_path: Path) -> None:
    """The pin is a plain argv token, so `command_digest` covers it: a
    record produced under a different pin cannot satisfy the claim, and
    moving the pin is a catalog edit review sees."""

    gate = load_gate(write(tmp_path, catalog()), "landing")
    pinned = gate.required_claims[0].command_digest
    other = load_gate(
        write(
            tmp_path,
            catalog(
                command=[
                    *ARGV[: ARGV.index(DIGEST)],
                    "sha256:" + "1" * 64,
                    *ARGV[ARGV.index(DIGEST) + 1 :],
                ]
            ),
        ),
        "landing",
    )
    assert pinned != other.required_claims[0].command_digest
    assert command_digest(tuple(ARGV)) == pinned
