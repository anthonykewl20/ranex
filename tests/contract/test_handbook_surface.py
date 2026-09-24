"""Contract tests for the kernel-handbook surface (issue #100, ADR-062).

The handbook is guidance, never authority (MAP §5.1, §17.6 knob 3). Two
structural facts make that true rather than aspirational, and both are
compiled here so a future change cannot quietly erode them:

1. only delegate packet construction consumes the engine — `run` and
   `gate evaluate` never read a handbook, so no chapter can influence a
   verdict path;
2. the digest record is the additive ADR-043 manifest field and nothing
   else — no evidence envelope or verdict field names a handbook.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import tempfile
from pathlib import Path

from ranex.execution.retained_logs import write_log_manifest
from ranex.foundation.canonical import canonical_json_bytes

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "src" / "ranex"

#: The only modules that may import the resolution engine. `delegation.py`
#: is the injection point; the engine imports itself.
_ENGINE = "src/ranex/policy/handbook.py"
_ENGINE_IMPORTERS = {_ENGINE, "src/ranex/cli/delegation.py"}

#: The only source files that may mention a handbook at all: the engine,
#: the injection point, and the additive manifest field.
_MENTION_ALLOWED = {
    "src/ranex/policy/handbook.py",
    "src/ranex/cli/delegation.py",
    "src/ranex/execution/retained_logs.py",
}

#: Authority surfaces a handbook may never touch, by name.
_AUTHORITY_SURFACES = (
    "src/ranex/governed_execution/domain/verdict.py",
    "src/ranex/governed_execution/domain/admission.py",
    "src/ranex/governed_execution/verdict_publication.py",
    "src/ranex/foundation/signing.py",
    "src/ranex/foundation/verdict_signing.py",
    "src/ranex/foundation/approval.py",
)


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def test_only_delegate_packet_construction_imports_the_engine() -> None:
    """`run` and `gate evaluate` cannot read what they never import."""

    offenders: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = _relative(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            offenders.append(f"{relative}: unparseable")
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name == "ranex.policy.handbook" or (
                    name == "handbook" and relative.startswith("ranex/policy/")
                ):
                    if relative not in _ENGINE_IMPORTERS:
                        offenders.append(f"{relative}: imports {name}")
    assert not offenders, (
        "the handbook engine may be consumed only by delegate packet "
        f"construction (ADR-062); other importers: {offenders}"
    )


def test_no_source_outside_the_allowed_surface_mentions_a_handbook() -> None:
    """SIGNED_FIELDS, EVIDENCE_DOMAIN and the kernel never name one."""

    offenders: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = _relative(path)
        if "handbook" in path.read_text(encoding="utf-8").lower() and (
            relative not in _MENTION_ALLOWED
        ):
            offenders.append(relative)
    assert not offenders, (
        f"handbook references outside the allowed surface {_MENTION_ALLOWED}: "
        f"{offenders}"
    )
    for surface in _AUTHORITY_SURFACES:
        assert (REPO_ROOT / surface).is_file(), surface


def test_verdict_module_is_byte_identical_to_the_pinned_digest() -> None:
    """The kernel digest pin is ADR-062's hard boundary; assert it directly.

    `tests/contract/test_kernel_unchanged.py` already refuses a moved or
    edited verdict.py; this test restates it from the handbook side so the
    two contracts fail together if anyone crosses the line.
    """

    pin = REPO_ROOT / "tests" / "contract" / "test_kernel_unchanged.py"
    match = re.search(r'KERNEL_DIGEST\s*=\s*"([0-9a-f]{64})"', pin.read_text("utf-8"))
    assert match is not None, "KERNEL_DIGEST pin not found"
    verdict = (
        REPO_ROOT / "src" / "ranex" / "governed_execution" / "domain" / "verdict.py"
    ).read_bytes()
    assert hashlib.sha256(verdict).hexdigest() == match.group(1)


def test_manifest_field_is_additive_and_absent_without_a_handbook() -> None:
    """No handbook → the manifest is exactly its pre-ADR-062 shape."""

    with tempfile.TemporaryDirectory() as scratch:
        directory = Path(scratch)
        streams = {"harness.stdout": {"file": "harness.stdout.log", "bytes": 0}}
        policy = {"max_bytes_per_stream": 1, "retention": "replace"}
        write_log_manifest(directory, streams, policy)
        without = json.loads((directory / "manifest.json").read_bytes())
        assert set(without) == {"version", "policy", "streams"}

        write_log_manifest(
            directory,
            streams,
            policy,
            handbook={
                "digest": "sha256:" + "0" * 64,
                "chapters": [],
                "matched": 0,
                "unmatched": 0,
            },
        )
        raw = (directory / "manifest.json").read_bytes()
        with_field = json.loads(raw)
        assert raw == canonical_json_bytes(with_field) + b"\n"
        assert set(with_field) == {"version", "policy", "streams", "handbook"}
        # The pre-existing keys are unchanged by the field's presence.
        assert with_field["streams"] == without["streams"]
        assert with_field["policy"] == without["policy"]
