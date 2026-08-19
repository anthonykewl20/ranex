"""SLICE-057 — real e2e: the execution family (suite freeze) on real data.

Issue #37's exact ownership (file 3 of 3), riding the ADR-032 frame: the
real hermetic ``suite freeze`` cycle on the committed tree — the
standing ceremony's own shape, executed as a test: the committed
expected-skip declarations re-declared verbatim (derived mechanically
from the committed manifest, never hand-copied), the full suite run
inside the sealed materialisation, the canonical manifest bytes produced
at an ignored ``.local/`` output path so the committed manifest is never
clobbered, and the result compared byte-exactly against the committed
``governance/suite_manifest.json``.

What each frozen contract proves (every kernel behavior was verified
against the installed kernel at e84b5176a in a /tmp/opencode prototype
before this file was frozen):

* **The round-trip** (issue #37 deterministic gate 4, AC4) — an
  unchanged tree reproduces the committed manifest byte-for-byte (the
  prototype observed sha256 ``53931503…97139``, ``run_exit=0``); a tree
  whose suite has moved past the committed manifest is the named red —
  the freeze produced different bytes, the manifest is stale for this
  tree, and the standing ceremony must re-freeze. The normalized
  ``FROZEN`` line matches ``expected/suite-freeze-manifest.out``.
* **The recursion boundary** — inside a sealed materialisation (the
  ceremony running THIS suite), the freeze journey cannot provision and
  would recurse forever; the journey detects the frozen
  ``nested_hermetic_self_gate`` environment shape
  (tests/e2e/test_gating_real_suite.py) and the arms pass by proving
  the boundary instead of recursing — the established repo pattern.
* **Sad path 5** — a dirty tree refuses the freeze before anything
  runs, with the stable reason and no output file.
* **Sad path 6** — a hand-edited manifest is refused at load: the
  verify side (``gate evaluate``) exits 2 for non-canonical bytes and
  for an expected-skip naming an ID the suite does not carry.

The freeze journey's precondition is the frame's ``pinned_resolver``
probe (the committed pins name the resolver the sealed run needs; the
operator's wheel store and journal are live host state the probe's
condition depends on) — consumed through the module-scoped
``prereq_pinned_resolver`` fixture, so an absent pin is a named skip,
never a silent green. The sad-path arms need no probe: their refusals
fire before provisioning is ever consulted.

The golden ``expected/suite-freeze-manifest.out`` is the implementation
lane's artifact, captured from a real run of this journey (the FROZEN
line piped through ``_prereqs.normalize_transcript`` exactly as the
tests do it); its absence is this file's honest frozen red.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

ARTIFACT = "governance/suite_results.xml"
COMMITTED_MANIFEST = REAL_REPO / "governance" / "suite_manifest.json"

#: See test_run_real.py's _STRIPPED_ENV for the rationale.
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
    "RANEX_TRACE",
    "RANEX_TRACE_EVENT",
    "RANEX_TRACE_PARENT_SID",
)

_GOLDEN = "suite-freeze-manifest.out"


def ranex_real(argv: list[str], *, timeout: float = 240.0) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI in the real repository the way the operator's
    ceremony does: the real tree's own source on PYTHONPATH, the real
    HOME (the wheel store and journal are live operator state)."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(REAL_REPO / "src")
    env.setdefault("LC_ALL", "C")
    env.setdefault("TZ", "UTC")
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=REAL_REPO,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=timeout,
    )


def _nested_hermetic_freeze_boundary() -> bool:
    """The sealed-materialisation recursion boundary, in the frozen
    ``nested_hermetic_self_gate`` shape (test_gating_real_suite.py).

    Inside the ceremony's sealed environment this suite IS the frozen
    run; a nested freeze could neither provision (fresh HOME, no store,
    no journal) nor terminate. The arms detect the boundary and pass by
    proving it — never by silently skipping.
    """

    dependency_root = os.environ.get("UV_PROJECT_ENVIRONMENT")
    home = os.environ.get("HOME")
    temporary = os.environ.get("TMPDIR")
    if not dependency_root or not home or not temporary:
        return False
    repository = REAL_REPO.resolve()
    materialisation = repository.parent
    if (
        repository.name != "tree"
        or not materialisation.name.startswith("ranex-subject-")
        or Path.cwd().resolve() != repository
    ):
        return False
    if (
        Path(dependency_root) != materialisation / "deps" / "env"
        or Path(home) != materialisation / "home"
        or Path(temporary) != materialisation / "tmp"
    ):
        return False
    return True


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly (the frozen red)."""

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-057 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the FROZEN line of the freeze cycle's stdout, "
        "piped through _prereqs.normalize_transcript exactly as the "
        "tests do), and commit the bytes. A hand-written golden cannot "
        "pass the sabotage control or the normalizer-application "
        "contracts in this file."
    )
    return path.read_text(encoding="utf-8")


@dataclass
class FreezeJourney:
    """Everything the frozen tests consume from the one module journey."""

    boundary: bool
    frozen_line: str | None
    produced_bytes: bytes | None
    committed_bytes: bytes


@pytest.fixture(scope="module")
def journey(
    tmp_path_factory: pytest.TempPathFactory, prereq_pinned_resolver: None
) -> FreezeJourney:
    """The one real freeze cycle on the committed tree (or the boundary)."""

    if _nested_hermetic_freeze_boundary():
        # The recursion boundary: this suite is running INSIDE the sealed
        # materialisation of a freeze cycle. Proving the boundary is this
        # module's honest pass; provisioning a nested cycle is neither
        # possible nor meaningful here.
        return FreezeJourney(
            boundary=True, frozen_line=None, produced_bytes=None, committed_bytes=None
        )

    dirty = subprocess.run(
        ["git", "-C", str(REAL_REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert not dirty, (
        "the real-tree freeze journey needs a clean working tree — the "
        f"kernel's own freeze would refuse it: {dirty}. Commit or clean "
        "the tree and re-run; the refusal itself is frozen by "
        "test_dirty_tree_freeze_refuses_with_stable_reason below."
    )

    committed_bytes = COMMITTED_MANIFEST.read_bytes()
    committed = json.loads(committed_bytes)
    declarations = [
        f"{test_id}={reason}"
        for test_id, reason in committed["expected_skips"].items()
    ]

    output = f".local/ranex-e2e/suite-freeze-roundtrip-{os.getpid()}.json"
    argv = [
        "suite", "freeze",
        "--artifact", ARTIFACT,
        "--output", output,
    ]
    for declaration in declarations:
        argv += ["--expected-skip", declaration]
    argv += ["--", "uv", "run", "pytest", "-q", f"--junitxml={ARTIFACT}"]

    completed = ranex_real(argv, timeout=1500.0)
    produced = REAL_REPO / output
    try:
        assert completed.returncode == 0, (
            "the real-tree freeze cycle must succeed — the journey "
            "refused where the ceremony should have run:\n"
            f"{completed.stdout[-2000:]}{completed.stderr[-2000:]}"
        )
        lines = [
            line for line in completed.stdout.splitlines() if line.startswith("FROZEN")
        ]
        assert len(lines) == 1, (
            f"exactly one FROZEN line was expected: {lines!r}"
        )
        assert produced.is_file(), "the freeze wrote no manifest at its output path"
        return FreezeJourney(
            boundary=False,
            frozen_line=lines[0],
            produced_bytes=produced.read_bytes(),
            committed_bytes=committed_bytes,
        )
    finally:
        if produced.exists():
            produced.unlink()


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def _assert_not_nested(journey: FreezeJourney) -> None:
    """The recursion-boundary proof: when the journey reported the
    boundary, this suite IS the sealed run, and the sealed environment
    shape must really hold (passing by proving the boundary — the frozen
    gating-suite pattern — never by silently skipping)."""

    if journey.boundary:
        assert os.environ["UV_PROJECT_ENVIRONMENT"].endswith("/deps/env")
        assert os.environ["HOME"].endswith("/home")
        assert os.environ["TMPDIR"].endswith("/tmp")
        assert REAL_REPO.resolve().name == "tree"
        return
    assert journey.frozen_line is not None
    assert journey.produced_bytes is not None
    assert journey.committed_bytes is not None


# --- the sad-path arms (no probe, no journey; they refuse before it) -----------


def test_dirty_tree_freeze_refuses_with_stable_reason() -> None:
    """Issue #37 sad path 5: a dirty tree refuses the freeze before
    anything runs, with the stable reason, and writes no output."""

    probe = REAL_REPO / "slice057-freeze-dirty-probe.txt"
    assert not probe.exists()
    probe.write_text("transient dirt for the refusal arm\n", encoding="utf-8")
    output = f".local/ranex-e2e/slice057-dirty-arm-{os.getpid()}.json"
    try:
        refused = ranex_real([
            "suite", "freeze",
            "--artifact", ARTIFACT,
            "--output", output,
            "--", "sh", "-c", "exit 0",
        ])
        assert refused.returncode == 2, (
            f"the dirty tree must refuse (exit 2): {refused.stdout}{refused.stderr}"
        )
        assert "refusing to freeze against a dirty working tree" in refused.stderr
        assert probe.name in refused.stderr, (
            "the refusal must name the dirty path: " + refused.stderr
        )
        assert not (REAL_REPO / output).exists(), (
            "a refused freeze must write no manifest"
        )
    finally:
        probe.unlink(missing_ok=True)
        leftover = REAL_REPO / output
        leftover.unlink(missing_ok=True)


def test_manifest_hand_edit_is_refused_at_load(tmp_path: Path) -> None:
    """Issue #37 sad path 6: a hand-edited manifest is refused at load by
    the verify side — ``gate evaluate`` exits 2 for non-canonical bytes,
    and again for an expected-skip naming an ID the suite does not carry."""

    subject = tmp_path / "hand-edited"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, cloned.stderr
    subprocess.run(
        ["git", "-C", str(subject), "config", "user.email", "hand-edit@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(subject), "config", "user.name", "hand edit"],
        check=True,
    )
    manifest_path = subject / "governance" / "suite_manifest.json"
    value = json.loads(manifest_path.read_text(encoding="utf-8"))

    def commit_edit(new_text: str) -> None:
        manifest_path.write_text(new_text, encoding="utf-8")
        subprocess.run(["git", "-C", str(subject), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(subject), "commit", "-q", "-m", "hand-edited manifest"],
            check=True,
        )

    def evaluate() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "ranex.cli.main", "gate", "evaluate", "HEAD",
             "--repository", ".", "--approver", "reviewer"],
            cwd=subject,
            env={
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONPATH": str(subject / "src"),
                "LC_ALL": "C", "TZ": "UTC",
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=240,
        )

    # the classic hand edit: reformatting — honest JSON, wrong bytes
    commit_edit(json.dumps(value, indent=2) + "\n")
    reformatted = evaluate()
    assert reformatted.returncode == 2, (
        f"a non-canonical manifest must refuse (exit 2): "
        f"{reformatted.stdout}{reformatted.stderr}"
    )
    assert "suite manifest must contain exact canonical JSON bytes" in reformatted.stderr

    # the structural hand edit: an expected skip naming an absent ID
    shape_invalid = dict(value)
    shape_invalid["expected_skips"] = {
        "tests/does/not/exist.py::test_x": "ranex-context:x: prose"
    }
    commit_edit(
        json.dumps(shape_invalid, sort_keys=True, separators=(",", ":"))
    )
    invalid = evaluate()
    assert invalid.returncode == 2, (
        f"a shape-invalid manifest must refuse (exit 2): "
        f"{invalid.stdout}{invalid.stderr}"
    )
    assert "expected-skip IDs must name tests in suite" in invalid.stderr


# --- the journey arms ----------------------------------------------------------


def test_manifest_round_trip_is_byte_stable(journey: FreezeJourney) -> None:
    """Issue #37 deterministic gate 4 / AC4: the freeze round-trip
    reproduces the committed manifest exactly — or names its drift."""

    _assert_not_nested(journey)
    if journey.boundary:
        return
    assert journey.produced_bytes == journey.committed_bytes, (
        _drift_report(journey.produced_bytes, journey.committed_bytes)
    )


def _drift_report(produced: bytes, committed: bytes) -> str:
    """Name the drift honestly: what the freeze produced vs what the tree
    commits, so the red says 'the manifest is stale for this tree'."""

    try:
        produced_manifest = json.loads(produced)
        committed_manifest = json.loads(committed)
        added = sorted(
            set(produced_manifest["suite"]) - set(committed_manifest["suite"])
        )
        removed = sorted(
            set(committed_manifest["suite"]) - set(produced_manifest["suite"])
        )
        skips_added = sorted(
            set(produced_manifest["expected_skips"])
            - set(committed_manifest["expected_skips"])
        )
        return (
            "the freeze round-trip drifted from the committed manifest — "
            f"the committed manifest is stale for this tree (+{len(added)} "
            f"IDs, first: {added[:5]}; -{len(removed)} IDs; "
            f"+{len(skips_added)} expected skips). The standing ceremony "
            "must re-freeze; drift is never silently green."
        )
    except (ValueError, KeyError, TypeError):
        return "the freeze round-trip drifted from the committed manifest"


def test_frozen_transcript_matches_the_golden(journey: FreezeJourney) -> None:
    """The FROZEN line of the real cycle, byte-frozen against its golden."""

    _assert_not_nested(journey)
    if journey.boundary:
        return
    frozen_line = journey.frozen_line
    assert frozen_line is not None
    assert frozen_line.startswith("FROZEN"), frozen_line
    assert "run_exit=0" in frozen_line, (
        f"the ceremony's own suite run must be green sealed: {frozen_line}"
    )
    compare_golden(frozen_line, _GOLDEN)


def test_goldens_carry_real_volatile_material(journey: FreezeJourney) -> None:
    """The machine-normalized-capture contract on the freeze golden: it
    carries ``<ABS-PATH>`` where the journey emits the live output path,
    is a normalizer fixpoint, and a golden holding the live path bytes
    provably cannot match."""

    _assert_not_nested(journey)
    if journey.boundary:
        return
    golden = golden_text(_GOLDEN)
    assert "<ABS-PATH>" in golden, (
        f"{_GOLDEN} carries no <ABS-PATH> token: the freeze's output path "
        "is real volatile material the normalizer must have tamed — a "
        "golden without the token is hand-sanitized text"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        f"{_GOLDEN} is not a normalizer fixpoint: it still contains bytes "
        "the frozen grammar would mask, which no capture piped through "
        "normalize_transcript can"
    )
    live = re.search(r"output=(\S+)", journey.frozen_line or "")
    assert live is not None, journey.frozen_line
    doctored = golden.replace("<ABS-PATH>", live.group(1), 1)
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _normalized(journey.frozen_line or ""), doctored,
            family=_GOLDEN.removesuffix(".out"),
        )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: FreezeJourney) -> None:
    """ADR-032's red control on the freeze golden: a mutated meaningful
    byte diffs dirty, the family named, the first hunk untruncated."""

    _assert_not_nested(journey)
    if journey.boundary:
        return
    family = _GOLDEN.removesuffix(".out")
    golden = golden_text(_GOLDEN)
    verdict_word = "FROZEN"
    assert verdict_word in golden, golden
    mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(
            _normalized(journey.frozen_line or ""), mutated, family=family
        )
    message = str(raised.value)
    assert family in message, f"the mismatch must name the family {family!r}: {message}"
    assert "@@" in message, message
    assert "Q" + verdict_word[1:] in message, message
