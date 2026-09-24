"""Real-CLI coverage for path-scoped handbook injection into delegate packets.

Issue #100: `task delegate` resolves `governance/handbook.json` (project) and
the operator's system handbook against every file in the dispatched base
tree, injects the resolved chapters plus the full per-path table into the
worker's brief, and lands the resolution digest in the ADR-043 retained-log
manifest. These tests run the real `cmd_task_delegate` in-process against a
real git target and a real shell harness; no seam is faked. The journey-level
proof (golden transcript, five real-data arms) lives in
`tests/e2e/test_handbook_injection_real.py` and the dogfood receipt.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from ranex.cli.delegation import cmd_task_delegate
from ranex.foundation.canonical import canonical_json_bytes

REPOSITORY = Path(__file__).resolve().parents[2]

_PROJECT_HANDBOOK = {
    "version": 1,
    "entries": [
        {
            "path_glob": "src/**",
            "text": "PROJECT src guidance: keep modules pure.",
        },
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


def _environment(home: Path) -> dict[str, str]:
    return {
        "HOME": str(home),
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _git(target: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    home = target.parent / "home"
    return subprocess.run(
        ["git", "-C", str(target), *arguments],
        capture_output=True,
        check=False,
        env=_environment(home),
        text=True,
    )


@pytest.fixture
def real_target(tmp_path: Path) -> Path:
    """A committed real git target carrying files in every handbook class."""

    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    assert subprocess.run(
        ["git", "init", "-q", str(target)],
        capture_output=True,
        check=False,
        env=_environment(home),
    ).returncode == 0
    for name, value in (
        ("user.email", "handbook@example.invalid"),
        ("user.name", "Handbook Delegate"),
    ):
        assert _git(target, "config", name, value).returncode == 0
    (target / "src").mkdir()
    (target / "src" / "alpha.py").write_text("alpha = 1\n", encoding="utf-8")
    (target / "src" / "beta.py").write_text("beta = 2\n", encoding="utf-8")
    (target / "docs").mkdir()
    (target / "docs" / "note.md").write_text("note\n", encoding="utf-8")
    (target / "legacy").mkdir()
    (target / "legacy" / "cocoa.m").write_text(
        "#import <Foundation/Foundation.h>\nint main(void) { return 0; }\n",
        encoding="utf-8",
    )
    (target / "legacy" / "plain.m").write_text("x = ones(3, 1);\n", encoding="utf-8")
    (target / "tools").mkdir()
    # An Objective-C-smelling .m file no project rule covers: the only place
    # the system layer's content sniffer may select a chapter.
    (target / "tools" / "sinker.m").write_text(
        "#import <Foundation/Foundation.h>\n- (void)run { }\n",
        encoding="utf-8",
    )
    (target / "governance").mkdir()
    (target / "governance" / "handbook.json").write_bytes(
        canonical_json_bytes(_PROJECT_HANDBOOK)
    )
    assert _git(target, "add", "-A").returncode == 0
    assert _git(target, "commit", "-q", "-m", "base").returncode == 0
    return target


@pytest.fixture
def operator_home(tmp_path: Path) -> Path:
    """An operator HOME whose XDG config dir carries the system handbook."""

    home = tmp_path / "operator-home"
    config = home / ".config" / "ranex"
    config.mkdir(parents=True)
    (config / "handbook.json").write_bytes(canonical_json_bytes(_SYSTEM_HANDBOOK))
    return home


def _harness(path: Path, capture: Path) -> Path:
    """A real shell harness that records its brief, works, and emits."""

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
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    *,
    task_id: str,
    home: Path,
) -> tuple[int, Path, Path]:
    """Run the real delegate command in-process; return exit, brief, outcome."""

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(home))
    capture = tmp_path / f"brief-{task_id}.txt"
    outcome = tmp_path / f"outcome-{task_id}.json"
    args = argparse.Namespace(
        task_id=task_id,
        target=str(target),
        worktree=str(tmp_path / f"worktree-{task_id}"),
        journal=str(tmp_path / f"journal-{task_id}.sqlite3"),
        harness=str(_harness(tmp_path / f"harness-{task_id}.sh", capture)),
        model="ranex-noop/noop",
        prompt="perform the handbook acceptance work",
        timeout=60,
        suite="/usr/bin/true",
        gate="landing",
        claim="tests-executed",
        gate_catalog=None,
        suite_manifest="governance/suite_manifest.json",
        outcome=str(outcome),
        log_dir=None,
        log_max_bytes=262144,
        log_retention="replace",
        redact_env=None,
    )
    import io
    from contextlib import redirect_stderr, redirect_stdout

    stderr = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
        code = cmd_task_delegate(args)
    assert code == 0, stderr.getvalue()
    return code, capture, outcome


def _manifest(outcome: Path) -> dict[str, object]:
    logs_dir = outcome.with_name(outcome.name + ".logs")
    manifest_path = logs_dir / "manifest.json"
    assert manifest_path.exists(), "retained-log manifest missing"
    payload = json.loads(manifest_path.read_bytes())
    assert manifest_path.read_bytes() == canonical_json_bytes(payload) + b"\n"
    return payload


def test_delegate_injects_chapters_and_records_unmatched_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
    operator_home: Path,
) -> None:
    _, brief, outcome = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-1", home=operator_home
    )
    text = brief.read_text(encoding="utf-8")
    # The project chapter won on src/** (arm 2, positive side).
    assert "PROJECT src guidance" in text
    assert "SYSTEM src guidance" not in text
    # Every path in scope is recorded — matched paths name their chapter and
    # unmatched paths say unmatched (arm 5).
    assert "src/alpha.py → project:src/**" in text
    assert "src/beta.py → project:src/**" in text
    assert "docs/note.md → unmatched" in text
    assert "governance/handbook.json → unmatched" in text
    # Both legacy .m files are project-covered, so the sniff never reaches
    # them; the only sniff-selected chapter is tools/sinker.m.
    assert "legacy/cocoa.m → project:legacy/*.m" in text
    assert "tools/sinker.m → system:**/*.m" in text
    assert "SYSTEM objc-flavoured guidance" in text

    manifest = _manifest(outcome)
    handbook = manifest["handbook"]
    assert isinstance(handbook, dict)
    assert handbook["chapters"] == [
        "project:legacy/*.m",
        "project:src/**",
        "system:**/*.m",
    ]
    assert handbook["matched"] == 5
    assert handbook["unmatched"] == 2  # docs/note.md and governance/handbook.json
    assert isinstance(handbook["digest"], str)
    assert handbook["digest"].startswith("sha256:")


def test_sniffer_never_overrides_a_project_rule(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
    operator_home: Path,
) -> None:
    """Arm 3: cocoa.m smells like Objective-C AND matches a project rule."""

    _, brief, _ = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-3", home=operator_home
    )
    text = brief.read_text(encoding="utf-8")
    assert "legacy/cocoa.m → project:legacy/*.m" in text
    assert "PROJECT legacy guidance" in text


def test_removing_the_project_rule_lets_the_system_rule_win(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
    operator_home: Path,
) -> None:
    """Arm 2, negative side: delete the project rule, the system rule applies."""

    (real_target / "governance" / "handbook.json").unlink()
    assert _git(real_target, "add", "-A").returncode == 0
    assert _git(real_target, "commit", "-q", "-m", "drop project handbook").returncode == 0
    _, brief, _ = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-2N", home=operator_home
    )
    text = brief.read_text(encoding="utf-8")
    assert "src/alpha.py → system:src/**" in text
    assert "SYSTEM src guidance" in text
    assert "PROJECT src guidance" not in text


def test_one_byte_change_changes_the_manifest_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
    operator_home: Path,
) -> None:
    """Arm 4: identical runs share a digest; one handbook byte breaks it."""

    _, _, first = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-4A", home=operator_home
    )
    _, _, second = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-4B", home=operator_home
    )
    digest_a = _manifest(first)["handbook"]["digest"]
    digest_b = _manifest(second)["handbook"]["digest"]
    assert digest_a == digest_b

    changed = {
        "version": 1,
        "entries": [
            {
                "path_glob": "src/**",
                "text": "PROJECT src guidance: keep modules pure!",
            },
        ],
    }
    (real_target / "governance" / "handbook.json").write_bytes(
        canonical_json_bytes(changed)
    )
    assert _git(real_target, "add", "-A").returncode == 0
    assert _git(real_target, "commit", "-q", "-m", "one byte of chapter text").returncode == 0
    _, _, third = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-4C", home=operator_home
    )
    digest_c = _manifest(third)["handbook"]["digest"]
    assert digest_c != digest_a


def test_no_handbook_anywhere_preserves_the_pre_injection_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
) -> None:
    """No layer anywhere: the brief is the prompt, the manifest has no knob."""

    (real_target / "governance" / "handbook.json").unlink()
    assert _git(real_target, "add", "-A").returncode == 0
    assert _git(real_target, "commit", "-q", "-m", "drop handbook").returncode == 0
    bare_home = tmp_path / "bare-home"
    bare_home.mkdir()
    _, brief, outcome = _delegate(
        tmp_path, monkeypatch, real_target, task_id="T-HB-5", home=bare_home
    )
    assert brief.read_text(encoding="utf-8") == "perform the handbook acceptance work"
    assert "handbook" not in _manifest(outcome)


def test_malformed_project_handbook_refuses_the_delegate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    real_target: Path,
    operator_home: Path,
) -> None:
    (real_target / "governance" / "handbook.json").write_bytes(b"{ not json")
    assert _git(real_target, "add", "-A").returncode == 0
    assert _git(real_target, "commit", "-q", "-m", "break handbook").returncode == 0

    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(operator_home))
    capture = tmp_path / "brief-broken.txt"
    args = argparse.Namespace(
        task_id="T-HB-6",
        target=str(real_target),
        worktree=str(tmp_path / "worktree-broken"),
        journal=str(tmp_path / "journal-broken.sqlite3"),
        harness=str(_harness(tmp_path / "harness-broken.sh", capture)),
        model="ranex-noop/noop",
        prompt="work",
        timeout=60,
        suite="/usr/bin/true",
        gate="landing",
        claim="tests-executed",
        gate_catalog=None,
        suite_manifest="governance/suite_manifest.json",
        outcome=str(tmp_path / "outcome-broken.json"),
        log_dir=None,
        log_max_bytes=262144,
        log_retention="replace",
        redact_env=None,
    )
    import io
    from contextlib import redirect_stderr, redirect_stdout

    stderr = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
        code = cmd_task_delegate(args)
    assert code == 2
    assert "refusing handbook" in stderr.getvalue()
    assert not capture.exists(), "no harness may run when the handbook is malformed"
