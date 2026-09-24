"""Issue #100 acceptance: real-subprocess handbook injection into delegate packets.

Journey (ADR-032 shape): one real `ranex task delegate` subprocess against a
real committed git target, an operator HOME carrying a system handbook, and a
real shell harness that records the exact brief it received. The golden
``expected/handbook-delegate-brief.out`` captures the brief plus the
retained-log manifest's handbook record through the one centralized
normalizer; the semantic arms (project beats system, the sniff stays under
the project layer, unmatched paths are recorded) are asserted directly
against the real artifacts, and the no-handbook journey proves the
pre-injection packet survives byte-identical for handbook-free repositories.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REPOSITORY = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

TASK_ID = "T-HB-E2E"
PROMPT = "perform the real handbook acceptance work"

_PROJECT_HANDBOOK = {
    "version": 1,
    "entries": [
        {"path_glob": "src/**", "text": "PROJECT src guidance: keep modules pure."},
        {
            "path_glob": "legacy/*.m",
            "text": "PROJECT legacy guidance: do not modernise blind.",
        },
    ],
}

_SYSTEM_HANDBOOK = {
    "version": 1,
    "entries": [
        {
            "path_glob": "src/**",
            "text": "SYSTEM src guidance: the operator-wide baseline.",
        },
        {"path_glob": "**/*.m", "text": "SYSTEM matlab-flavoured guidance."},
        {
            "path_glob": "**/*.m",
            "text": "SYSTEM objc-flavoured guidance.",
            "sniff_marker": "#import",
        },
    ],
}


def golden_text(name: str) -> str:
    """Read the family golden, refusing its absence loudly."""

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. Capture it from a real run "
        "of this journey (the fixture below), pipe the journey transcript "
        "through _prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes."
    )
    return path.read_text(encoding="utf-8")


def _environment(home: Path) -> dict[str, str]:
    return {
        "HOME": str(home),
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(REPOSITORY / "src"),
    }


def _git(target: Path, home: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), *arguments],
        capture_output=True,
        check=False,
        env=_environment(home),
        text=True,
    )


def _build_target(tmp_path: Path) -> tuple[Path, Path]:
    """A real committed git target with a file in every handbook class."""

    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    initialized = subprocess.run(
        ["git", "init", "-q", str(target)],
        capture_output=True,
        check=False,
        env=_environment(home),
        text=True,
    )
    assert initialized.returncode == 0, initialized.stderr
    for name, value in (
        ("user.email", "handbook-e2e@example.invalid"),
        ("user.name", "Handbook E2E"),
    ):
        configured = _git(target, home, "config", name, value)
        assert configured.returncode == 0, configured.stderr
    (target / "src").mkdir()
    (target / "src" / "alpha.py").write_text("alpha = 1\n", encoding="utf-8")
    (target / "docs").mkdir()
    (target / "docs" / "note.md").write_text("note\n", encoding="utf-8")
    (target / "legacy").mkdir()
    (target / "legacy" / "cocoa.m").write_text(
        "#import <Foundation/Foundation.h>\nint main(void) { return 0; }\n",
        encoding="utf-8",
    )
    (target / "tools").mkdir()
    (target / "tools" / "sinker.m").write_text(
        "#import <Foundation/Foundation.h>\n- (void)run { }\n",
        encoding="utf-8",
    )
    (target / "governance").mkdir()
    from ranex.foundation.canonical import canonical_json_bytes

    (target / "governance" / "handbook.json").write_bytes(
        canonical_json_bytes(_PROJECT_HANDBOOK)
    )
    added = _git(target, home, "add", "-A")
    assert added.returncode == 0, added.stderr
    committed = _git(target, home, "commit", "-q", "-m", "base")
    assert committed.returncode == 0, committed.stderr
    return target, home


def _operator_home(tmp_path: Path) -> Path:
    home = tmp_path / "operator-home"
    config = home / ".config" / "ranex"
    config.mkdir(parents=True)
    from ranex.foundation.canonical import canonical_json_bytes

    (config / "handbook.json").write_bytes(canonical_json_bytes(_SYSTEM_HANDBOOK))
    return home


def _harness(path: Path, capture: Path) -> Path:
    body = f"""#!/usr/bin/env sh
set -eu
worktree=
prompt=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir) worktree="$2"; shift 2 ;;
    --model|--auto) shift ;;
    *) prompt="$1"; shift ;;
  esac
done
printf '%s' "$prompt" > {capture}
printf 'real harness work\\n' > "$worktree/agent.txt"
git -C "$worktree" add agent.txt
git -C "$worktree" -c user.email=harness@example.invalid -c user.name=Harness commit -q -m 'work'
commit=$(git -C "$worktree" rev-parse HEAD)
printf '{{"task_id":"%s","worktree":"%s","commit":"%s"}}\\n' "$RANEX_TASK_ID" "$worktree" "$commit" > "$RANEX_EMIT"
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _delegate(
    tmp_path: Path,
    *,
    task_id: str,
    home: Path,
    target: Path,
) -> tuple[subprocess.CompletedProcess[str], Path, Path]:
    """Run one real delegate subprocess; return result, brief, outcome path."""

    capture = tmp_path / f"brief-{task_id}.txt"
    outcome = tmp_path / f"outcome-{task_id}.json"
    argv = [
        sys.executable,
        "-m",
        "ranex.cli.main",
        "task",
        "delegate",
        "--task-id",
        task_id,
        "--target",
        str(target),
        "--worktree",
        str(tmp_path / f"worktree-{task_id}"),
        "--journal",
        str(tmp_path / f"journal-{task_id}.sqlite3"),
        "--harness",
        str(_harness(tmp_path / f"harness-{task_id}.sh", capture)),
        "--model",
        "ranex-noop/noop",
        "--prompt",
        PROMPT,
        "--timeout",
        "60",
        "--suite",
        "/usr/bin/true",
        "--outcome",
        str(outcome),
    ]
    result = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=target,
        env=_environment(home),
        text=True,
    )
    return result, capture, outcome


def _manifest(outcome: Path) -> dict[str, object]:
    logs_dir = outcome.with_name(outcome.name + ".logs")
    payload = json.loads((logs_dir / "manifest.json").read_bytes())
    assert isinstance(payload, dict)
    return payload


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> dict[str, object]:
    """One real delegate run whose artifacts every test in the file reads."""

    tmp_path = tmp_path_factory.mktemp("handbook-e2e")
    target, _ = _build_target(tmp_path)
    home = _operator_home(tmp_path)
    result, brief, outcome = _delegate(
        tmp_path, task_id=TASK_ID, home=home, target=target
    )
    assert result.returncode == 0, result.stderr
    manifest = _manifest(outcome)
    handbook = manifest["handbook"]
    assert isinstance(handbook, dict)
    assert isinstance(handbook["digest"], str)
    transcript = (
        "exit=0\n"
        "brief:\n"
        f"{brief.read_text(encoding='utf-8')}\n"
        "manifest:\n"
        f"digest={handbook['digest']}\n"
        f"chapters={','.join(str(c) for c in handbook['chapters'])}\n"
        f"matched={handbook['matched']} unmatched={handbook['unmatched']}\n"
    )
    return {
        "brief": brief.read_text(encoding="utf-8"),
        "manifest": manifest,
        "transcript": transcript,
        "target": target,
        "home": home,
        "tmp_path": tmp_path,
    }


def test_golden_transcript_matches_the_real_journey(journey: dict[str, object]) -> None:
    actual = _prereqs.normalize_transcript(str(journey["transcript"]))
    golden = golden_text("handbook-delegate-brief.out")
    _prereqs.compare_transcript(actual, golden, family="handbook-delegate-brief")


def test_golden_is_a_normalizer_fixpoint() -> None:
    golden = golden_text("handbook-delegate-brief.out")
    assert _prereqs.normalize_transcript(golden) == golden, (
        "the golden still contains bytes the frozen grammar would mask; a "
        "capture piped through normalize_transcript cannot"
    )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: dict[str, object]) -> None:
    """ADR-032's red control: mutate a meaningful byte, diff dirty."""

    golden = golden_text("handbook-delegate-brief.out")
    assert "PROJECT src guidance" in golden, golden
    mutated = golden.replace("PROJECT src guidance", "QROJECT src guidance", 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(str(journey["transcript"])),
            mutated,
            family="handbook-delegate-brief",
        )
    message = str(raised.value)
    assert "handbook-delegate-brief" in message, message
    assert "@@" in message, message
    assert "QROJECT" in message, message


def test_the_project_layer_beats_the_system_layer_on_the_same_glob(
    journey: dict[str, object],
) -> None:
    brief = journey["brief"]
    assert isinstance(brief, str)
    assert "PROJECT src guidance" in brief
    assert "SYSTEM src guidance" not in brief


def test_the_sniff_stays_under_the_project_layer(journey: dict[str, object]) -> None:
    """cocoa.m smells of Objective-C and matches a project rule; the rule wins."""

    brief = journey["brief"]
    assert isinstance(brief, str)
    assert "legacy/cocoa.m → project:legacy/*.m" in brief
    # The sniff still selected the system chapter where no project rule
    # matched (sinker.m), and only there.
    assert "tools/sinker.m → system:**/*.m" in brief
    assert "SYSTEM objc-flavoured guidance" in brief
    assert "sniffed=yes" in brief


def test_unmatched_paths_are_recorded_not_dropped(journey: dict[str, object]) -> None:
    brief = journey["brief"]
    assert isinstance(brief, str)
    assert "docs/note.md → unmatched" in brief
    assert "governance/handbook.json → unmatched" in brief


def test_manifest_names_the_chapters_and_counts(
    journey: dict[str, object],
) -> None:
    handbook = journey["manifest"]["handbook"]
    assert isinstance(handbook, dict)
    assert handbook["chapters"] == [
        "project:legacy/*.m",
        "project:src/**",
        "system:**/*.m",
    ]
    assert handbook["matched"] == 3
    assert handbook["unmatched"] == 2
    assert str(handbook["digest"]).startswith("sha256:")


def test_no_handbook_repository_gets_the_pre_injection_packet(
    tmp_path: Path,
) -> None:
    """A handbook-free target and HOME: the brief is the prompt, no field."""

    target, home = _build_target(tmp_path)
    (target / "governance" / "handbook.json").unlink()
    dropped = _git(target, home, "add", "-A")
    assert dropped.returncode == 0, dropped.stderr
    committed = _git(target, home, "commit", "-q", "-m", "drop handbook")
    assert committed.returncode == 0, committed.stderr
    bare_home = tmp_path / "bare-home"
    bare_home.mkdir()
    result, brief, outcome = _delegate(
        tmp_path, task_id="T-HB-E2E-BARE", home=bare_home, target=target
    )
    assert result.returncode == 0, result.stderr
    assert brief.read_text(encoding="utf-8") == PROMPT
    assert "handbook" not in _manifest(outcome)


def test_real_evidence_plane_is_unaffected_by_a_present_handbook(
    tmp_path: Path,
) -> None:
    """Arm 4's negative, repo side: the evaluation plane's output is
    byte-identical with and without handbook layers in play.

    The structural fact (no importer) is frozen by the contract test; this
    journey adds the behavioural side — the same CLI evaluation surface run
    twice over identical inputs, once under an operator HOME carrying a
    system handbook and once without, produces identical bytes.
    """

    env_with = _environment(_operator_home(tmp_path))
    (tmp_path / "no-home").mkdir()
    env_without = _environment(tmp_path / "no-home")
    argv = [sys.executable, "-m", "ranex.cli.main", "gate", "evaluate", "--help"]
    outputs = []
    for env in (env_with, env_without):
        completed = subprocess.run(
            argv, capture_output=True, check=False, env=env, text=True
        )
        outputs.append((completed.returncode, completed.stdout, completed.stderr))
    assert outputs[0] == outputs[1]
    assert "handbook" not in outputs[0][1].lower()
