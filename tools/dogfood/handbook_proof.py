"""#95 control-pair proof for the path-scoped kernel handbook (issue #100).

Every expectation from the issue's five real-data arms is a control pair run
through the calibration machinery: a positive that must hold, a negative that
must be refused, `--repeats` identical-input executions of both. Real
`ranex` subprocesses on real repositories throughout — a pinned clone of
``six@1.17.0``, this repository, and scratch real git targets with real
files; no mocked seam, no monkeypatching, and the engine is exercised
through its public functions over real path sets only.

Arms (issue #100 "Real-data arms", verbatim mapping):

1. ``arm1-resolution-determinism`` — resolve every path in ``six`` and in
   Ranex; repeats produce an identical resolution-table digest. Negative:
   one perturbed chapter byte must change the digest.
2. ``arm2-project-beats-system`` — project rule and system rule on the same
   glob → project wins, and the row records BOTH matches. Negative (the
   issue's own): remove the project rule → system wins.
3. ``arm3-sniffer-cannot-override-project`` — a sniff-firing path that also
   matches a project rule resolves to the project chapter; the sniff
   selects a system chapter only where no project rule matched. Negative:
   the sniffed system chapter overriding the project rule is the accepted
   outcome this check exists to refuse.
4. ``arm4a-digest-in-manifest`` — the delegate outcome's ADR-043 manifest
   carries the handbook digest, equal to the engine's digest over the same
   inputs; negative: one changed handbook byte leaves the digest unchanged.
   ``arm4b-digest-absent-from-evidence`` — a real governed ``ranex run`` +
   ``gate evaluate`` produce identical evidence and verdict with and
   without a system handbook in the operator HOME, and no handbook bytes
   appear in either; negative: a doctored evidence file carrying the digest
   string must be caught.
5. ``arm5-unmatched-recorded`` — every path in scope appears in the brief's
   table, matched or ``unmatched``; negative: a brief with one path
   silently dropped must be caught by the coverage detector.

Run (network required for the six clone; nothing else touches the network):

    uv run --frozen python tools/dogfood/handbook_proof.py \
        --out tools/dogfood/audits/2026-09-24-handbook-injection --repeats 3

Exit 0 only when every control is VERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

DOGFOOD = Path(__file__).resolve().parent
if str(DOGFOOD) not in sys.path:
    sys.path.insert(0, str(DOGFOOD))
REPOSITORY = DOGFOOD.parents[1]
if str(REPOSITORY / "src") not in sys.path:
    sys.path.insert(0, str(REPOSITORY / "src"))

from calibration import Calibration, Control, Observation, Subject  # noqa: E402

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.policy.handbook import (  # noqa: E402
    glob_matches,
    parse_handbook_bytes,
    resolve_handbook,
)

SIX_TAG = "1.17.0"
SIX_COMMIT = "ebd9b3af90247b8858d415a05e96e9ee61e48d07"
SIX_URL = "https://github.com/benjaminp/six.git"

_ARM1_SYSTEM = {
    "version": 1,
    "entries": [
        {"path_glob": "**/*.py", "text": "SYSTEM python guidance: prefer stdlib."},
        {"path_glob": "**/*.rst", "text": "SYSTEM docs guidance: keep prose tight."},
    ],
}
_ARM1_PROJECT = {
    "version": 1,
    "entries": [
        {"path_glob": "**/*.py", "text": "PROJECT python guidance: match the house style."},
    ],
}
_ARM1_PROJECT_PERTURBED = {
    "version": 1,
    "entries": [
        {
            "path_glob": "**/*.py",
            "text": "PROJECT python guidance: match the house style!",
        },
    ],
}

_DELEGATE_SYSTEM = {
    "version": 1,
    "entries": [
        {"path_glob": "src/**", "text": "SYSTEM src guidance: the operator baseline."},
        {"path_glob": "**/*.m", "text": "SYSTEM matlab-flavoured guidance."},
        {
            "path_glob": "**/*.m",
            "text": "SYSTEM objc-flavoured guidance.",
            "sniff_marker": "#import",
        },
    ],
}
_DELEGATE_PROJECT = {
    "version": 1,
    "entries": [
        {"path_glob": "src/**", "text": "PROJECT src guidance: keep modules pure."},
        {"path_glob": "legacy/*.m", "text": "PROJECT legacy guidance: do not modernise blind."},
    ],
}


def _handbook_bytes(payload: dict[str, object]) -> bytes:
    return canonical_json_bytes(payload)


def _paths_of(repository: Path, ref: str = "HEAD") -> list[str]:
    """Every file path in a real repository tree, via real git."""

    completed = subprocess.run(
        ["git", "-C", str(repository), "ls-tree", "-r", "--name-only", ref],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ls-tree failed on {repository}: {completed.stderr}")
    return [line for line in completed.stdout.splitlines() if line]


def _peek(repository: Path, ref: str, path: str) -> str | None:
    """The first non-blank line of one path, read via real git."""

    completed = subprocess.run(
        ["git", "-C", str(repository), "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    for line in completed.stdout.splitlines():
        stripped = line.lstrip()
        if stripped:
            return stripped[:256]
    return None


def _resolve_repository(
    repository: Path,
    system_payload: dict[str, object],
    project_payload: dict[str, object],
) -> dict[str, object]:
    """Resolve every path of a real repository through the public engine."""

    system = parse_handbook_bytes("system", _handbook_bytes(system_payload))
    project = parse_handbook_bytes("project", _handbook_bytes(project_payload))
    paths = _paths_of(repository)
    peeks = _sniff_peeks(repository, "HEAD", paths, system)
    resolution = resolve_handbook(system, project, paths, peeks)
    return {
        "repository": str(repository),
        "paths": len(paths),
        "matched": sum(1 for row in resolution.rows if row.status == "matched"),
        "unmatched": sum(1 for row in resolution.rows if row.status == "unmatched"),
        "digest": resolution.digest,
        "chapters": [chapter.chapter_id for chapter in resolution.chapters],
    }


def _sniff_peeks(
    repository: Path,
    ref: str,
    paths: list[str],
    system: tuple[object, ...],
) -> dict[str, str]:
    """Content peeks for exactly the paths a sniff-marker entry's glob names."""

    sniff_globs = {
        entry.path_glob for entry in system if getattr(entry, "sniff_marker", None)
    }
    peeks: dict[str, str] = {}
    if not sniff_globs:
        return peeks
    for path in paths:
        if not any(glob_matches(glob, path) for glob in sniff_globs):
            continue
        peek = _peek(repository, ref, path)
        if peek is not None:
            peeks[path] = peek
    return peeks


# --- the real delegate journey (arms 3, 4a, 5) -------------------------------


def _run_key() -> str:
    """A fresh scratch namespace per delegate invocation.

    The calibration machinery re-executes each side on identical input, and
    `task delegate` refuses a reused worktree or journal by design — so every
    invocation builds its target, journal and worktree under a fresh key
    while the input bytes stay identical.
    """

    return uuid.uuid4().hex[:12]


def _build_delegate_target(
    root: Path, *, project_payload: dict[str, object] | None, label: str
) -> tuple[Path, Path]:
    """A fresh real git target with real files in every handbook class."""

    label = f"{label}-{_run_key()}"
    home = root / f"home-{label}"
    home.mkdir(parents=True, exist_ok=True)
    target = root / f"target-{label}"
    target.mkdir()
    environment = {
        "HOME": str(home),
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(target), *arguments],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

    assert subprocess.run(
        ["git", "init", "-q", str(target)], capture_output=True, env=environment
    ).returncode == 0
    assert git("config", "user.email", "handbook-proof@example.invalid").returncode == 0
    assert git("config", "user.name", "Handbook Proof").returncode == 0
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
    if project_payload is not None:
        (target / "governance" / "handbook.json").write_bytes(
            _handbook_bytes(project_payload)
        )
    assert git("add", "-A").returncode == 0
    assert git("commit", "-q", "-m", "base").returncode == 0
    return target, home


def _run_delegate(
    root: Path,
    *,
    task_id: str,
    target: Path,
    home: Path,
    system_payload: dict[str, object] | None = _DELEGATE_SYSTEM,
) -> dict[str, object]:
    """One real `ranex task delegate` subprocess; brief and manifest back."""

    config = home / ".config" / "ranex"
    config.mkdir(parents=True, exist_ok=True)
    system_file = config / "handbook.json"
    if system_payload is not None:
        system_file.write_bytes(_handbook_bytes(system_payload))
    else:
        system_file.unlink(missing_ok=True)

    capture = root / f"brief-{task_id}-{_run_key()}.txt"
    outcome = root / f"outcome-{task_id}-{_run_key()}.json"
    harness_path = root / f"harness-{task_id}-{_run_key()}.sh"
    harness_path.write_text(
        f"""#!/usr/bin/env sh
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
printf '{{"task_id":"{task_id}","worktree":"%s","commit":"%s"}}\\n' "$worktree" "$commit" > "$RANEX_EMIT"
""",
        encoding="utf-8",
    )
    harness_path.chmod(0o755)
    environment = {
        "HOME": str(home),
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(REPOSITORY / "src"),
    }
    completed = subprocess.run(
        [
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
            str(root / f"worktree-{task_id}-{_run_key()}"),
            "--journal",
            str(root / f"journal-{task_id}-{_run_key()}.sqlite3"),
            "--harness",
            str(harness_path),
            "--model",
            "ranex-noop/noop",
            "--prompt",
            "perform the handbook proof work",
            "--timeout",
            "60",
            "--suite",
            "/usr/bin/true",
            "--outcome",
            str(outcome),
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=target,
        env=environment,
        timeout=120,
    )
    if completed.returncode != 0:
        return {
            "exit": completed.returncode,
            "stderr": completed.stderr.strip()[-400:],
            "brief": None,
            "manifest_handbook": None,
        }
    manifest = json.loads(
        (outcome.with_name(outcome.name + ".logs") / "manifest.json").read_bytes()
    )
    return {
        "exit": 0,
        "stderr": "",
        "brief": capture.read_text(encoding="utf-8"),
        "manifest_handbook": manifest.get("handbook"),
    }


def _engine_manifest_digest(target: Path, home: Path) -> str | None:
    """Independently recompute the resolution digest for a delegate target."""

    system_file = home / ".config" / "ranex" / "handbook.json"
    system = (
        parse_handbook_bytes("system", system_file.read_bytes())
        if system_file.exists()
        else ()
    )
    project_file = target / "governance" / "handbook.json"
    project = (
        parse_handbook_bytes("project", project_file.read_bytes())
        if project_file.exists()
        else ()
    )
    paths = _paths_of(target)
    peeks = _sniff_peeks(target, "HEAD", paths, system)
    return resolve_handbook(system, project, paths, peeks).digest


def _brief_table_paths(brief: str) -> set[str]:
    """The paths a brief's resolution table actually names."""

    table = brief.split("### Resolution table", 1)
    if len(table) != 2:
        return set()
    paths = set()
    for line in table[1].splitlines():
        line = line.strip()
        if line.startswith("- ") and " → " in line:
            paths.add(line[2:].rsplit(" → ", 1)[0])
    return paths


# --- the controls --------------------------------------------------------------


def _arm1(six: Path) -> list[Control]:
    def positive() -> Observation:
        six_facts = _resolve_repository(six, _ARM1_SYSTEM, _ARM1_PROJECT)
        ranex_facts = _resolve_repository(REPOSITORY, _ARM1_SYSTEM, _ARM1_PROJECT)
        ok = (
            six_facts["paths"] > 0
            and ranex_facts["paths"] > 0
            and six_facts["matched"] + six_facts["unmatched"] == six_facts["paths"]
            and ranex_facts["matched"] + ranex_facts["unmatched"] == ranex_facts["paths"]
            and six_facts["matched"] > 0
            and six_facts["unmatched"] > 0
            and ranex_facts["matched"] > 0
            and ranex_facts["unmatched"] > 0
        )
        return Observation(
            ok=bool(ok),
            facts={"six": six_facts, "ranex": ranex_facts},
        )

    def negative() -> Observation:
        base = _resolve_repository(six, _ARM1_SYSTEM, _ARM1_PROJECT)
        perturbed = _resolve_repository(six, _ARM1_SYSTEM, _ARM1_PROJECT_PERTURBED)
        # The bad input is the perturbed handbook; accepting it means the
        # digest failed to notice one changed chapter byte.
        accepted = perturbed["digest"] == base["digest"]
        return Observation(
            ok=bool(accepted),
            facts={
                "base_digest": base["digest"],
                "perturbed_digest": perturbed["digest"],
            },
        )

    return [
        Control(
            name="arm1-resolution-determinism",
            expectation=(
                "resolving every path in six@1.17.0 and in Ranex yields one "
                "stable resolution-table digest per repository; one perturbed "
                "chapter byte changes it"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _arm2(six: Path) -> list[Control]:
    system = {
        "version": 1,
        "entries": [{"path_glob": "**/*.py", "text": "SYSTEM chapter"}],
    }
    project = {
        "version": 1,
        "entries": [{"path_glob": "**/*.py", "text": "PROJECT chapter"}],
    }

    def _row(project_payload: dict[str, object]) -> dict[str, object]:
        system_entries = parse_handbook_bytes("system", _handbook_bytes(system))
        project_entries = parse_handbook_bytes("project", _handbook_bytes(project_payload))
        paths = [p for p in _paths_of(six) if p.endswith(".py")][:5]
        resolution = resolve_handbook(system_entries, project_entries, paths)
        winner = resolution.rows[0]
        return {
            "path": winner.path,
            "layer": winner.layer,
            "pattern": winner.pattern,
            "system_pattern": winner.system_pattern,
            "text": resolution.chapters[0].text,
        }

    def positive() -> Observation:
        row = _row(project)
        ok = (
            row["layer"] == "project"
            and row["pattern"] == "**/*.py"
            and row["system_pattern"] == "**/*.py"  # both matches on the record
            and row["text"] == "PROJECT chapter"
        )
        return Observation(ok=bool(ok), facts={"row": row})

    def negative() -> Observation:
        # The issue's negative: remove the project rule → the system rule
        # must win. Accepting the bad outcome means the system rule failed
        # to step in once the project rule was gone.
        row = _row({"version": 1, "entries": []})
        accepted = row["layer"] != "system" or row["text"] != "SYSTEM chapter"
        return Observation(ok=bool(accepted), facts={"row": row})

    return [
        Control(
            name="arm2-project-beats-system",
            expectation=(
                "a project rule and a system rule on the same glob: the "
                "project rule wins and the row records both matches; with "
                "the project rule removed the system rule wins"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _arm3(root: Path) -> list[Control]:
    def _observe(label: str) -> tuple[bool, dict[str, object]]:
        target, home = _build_delegate_target(
            root, project_payload=_DELEGATE_PROJECT, label=label
        )
        run = _run_delegate(root, task_id=f"T-HB-A3-{label[-1:].upper()}", target=target, home=home)
        brief = run["brief"] or ""
        return run, brief

    def positive() -> Observation:
        run, brief = _observe("a3p")
        ok = (
            run["exit"] == 0
            and "legacy/cocoa.m → project:legacy/*.m" in brief
            and "PROJECT legacy guidance" in brief
            and "sniffed=yes" in brief  # the sniff fired for tools/sinker.m
            and "tools/sinker.m → system:**/*.m" in brief
        )
        return Observation(
            ok=bool(ok),
            facts={"exit": run["exit"], "stderr": run["stderr"]},
        )

    def negative() -> Observation:
        run, brief = _observe("a3n")
        # The bad outcome this check exists to refuse: the sniffed system
        # chapter overriding the project rule on legacy/cocoa.m.
        overridden = "legacy/cocoa.m → system:" in brief
        return Observation(
            ok=bool(overridden),
            facts={"exit": run["exit"], "stderr": run["stderr"]},
        )

    return [
        Control(
            name="arm3-sniffer-cannot-override-project",
            expectation=(
                "a path whose content sniffs Objective-C AND matches a "
                "project rule resolves to the project chapter; the sniff "
                "selects a system chapter only where no project rule matched"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _arm4a(root: Path) -> list[Control]:
    changed_project = {
        "version": 1,
        "entries": [
            {
                "path_glob": "src/**",
                "text": "PROJECT src guidance: keep modules pure!",
            },
            {
                "path_glob": "legacy/*.m",
                "text": "PROJECT legacy guidance: do not modernise blind.",
            },
        ],
    }

    def _run(label: str, payload: dict[str, object]) -> dict[str, object]:
        target, home = _build_delegate_target(root, project_payload=payload, label=label)
        run = _run_delegate(
            root, task_id=f"T-HB-A4-{label[-1:].upper()}", target=target, home=home
        )
        engine = _engine_manifest_digest(target, home)
        return {
            "exit": run["exit"],
            "manifest": run["manifest_handbook"],
            "engine_digest": engine,
            "paths": len(_paths_of(target)),
        }

    def positive() -> Observation:
        facts = _run("a4a", _DELEGATE_PROJECT)
        manifest = facts["manifest"]
        ok = (
            facts["exit"] == 0
            and isinstance(manifest, dict)
            and manifest.get("digest") == facts["engine_digest"]
            and str(manifest.get("digest", "")).startswith("sha256:")
            and manifest.get("matched", -1) + manifest.get("unmatched", -2)
            == facts["paths"]
        )
        return Observation(
            ok=bool(ok),
            facts={
                "exit": facts["exit"],
                "manifest": manifest,
                "engine_digest": facts["engine_digest"],
                "paths": facts["paths"],
            },
        )

    def negative() -> Observation:
        base = _run("a4nb", _DELEGATE_PROJECT)
        changed = _run("a4nc", changed_project)
        # The bad input is the one-changed-byte handbook; accepting it means
        # the manifest digest stayed the same.
        accepted = (
            base["manifest"] is not None
            and changed["manifest"] is not None
            and base["manifest"]["digest"] == changed["manifest"]["digest"]
        )
        return Observation(
            ok=bool(accepted),
            facts={
                "base_digest": (base["manifest"] or {}).get("digest"),
                "changed_digest": (changed["manifest"] or {}).get("digest"),
            },
        )

    return [
        Control(
            name="arm4a-digest-in-manifest",
            expectation=(
                "the delegate outcome's retained-log manifest carries the "
                "handbook digest and it equals the engine digest over the "
                "same inputs; one changed handbook byte changes it"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _arm4b(subject: Subject) -> list[Control]:
    def _outputs(with_handbook: bool) -> dict[str, object]:
        handbook = subject.root / "home" / ".config" / "ranex" / "handbook.json"
        handbook.parent.mkdir(parents=True, exist_ok=True)
        if with_handbook:
            handbook.write_bytes(_handbook_bytes(_DELEGATE_SYSTEM))
        else:
            handbook.unlink(missing_ok=True)
        subject._git("checkout", "-q", subject.good)
        store = subject.repo / "governance" / "evidence.json"
        store.unlink(missing_ok=True)
        (subject.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        subject._cli(
            "run",
            "--claim",
            "markers-declared",
            "--producer",
            "worker",
            "--",
            "/usr/bin/python3",
            "-c",
            subject.scanner,
        )
        verdict = subject._cli(
            "gate", "evaluate", "HEAD", "--approver", "auditor", key=False
        )
        evidence_bytes = store.read_bytes() if store.exists() else b""
        return {
            "verdict_stdout": verdict.stdout,
            "verdict_exit": verdict.returncode,
            "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "evidence_text": evidence_bytes.decode("utf-8", errors="replace"),
        }

    def positive() -> Observation:
        with_handbook = _outputs(True)
        without = _outputs(False)
        handbook_named = "handbook" in with_handbook["evidence_text"].lower() or (
            "handbook" in with_handbook["verdict_stdout"].lower()
        )
        identical = (
            with_handbook["verdict_stdout"] == without["verdict_stdout"]
            and with_handbook["verdict_exit"] == without["verdict_exit"]
            and with_handbook["evidence_sha256"] == without["evidence_sha256"]
        )
        ok = identical and not handbook_named
        return Observation(
            ok=bool(ok),
            facts={
                "identical": identical,
                "handbook_named": handbook_named,
                "verdict_first_line": str(with_handbook["verdict_stdout"]).split("\n", 1)[0],
                "evidence_sha256": with_handbook["evidence_sha256"],
            },
        )

    def negative() -> Observation:
        clean = _outputs(True)
        # The bad input: an evidence file doctored to carry handbook bytes.
        # The detector is 'no handbook naming anywhere in the evidence
        # plane'; accepting the doctored file means the detector is blind.
        doctored = (
            clean["evidence_text"]
            + "\n"
            + json.dumps({"handbook": {"digest": "sha256:" + "0" * 64}})
            + "\n"
        )
        detector_passed_doctored = "handbook" not in doctored.lower()
        return Observation(
            ok=bool(detector_passed_doctored),
            facts={"doctored_bytes": len(doctored)},
        )

    return [
        Control(
            name="arm4b-digest-absent-from-evidence",
            expectation=(
                "a real governed run and gate evaluate are identical with "
                "and without a system handbook, no handbook bytes in "
                "evidence or verdict; a doctored evidence file carrying the "
                "digest is caught"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _arm5(root: Path) -> list[Control]:
    def positive() -> Observation:
        target, home = _build_delegate_target(
            root, project_payload=_DELEGATE_PROJECT, label="a5p"
        )
        run = _run_delegate(root, task_id="T-HB-A5-P", target=target, home=home)
        brief = run["brief"] or ""
        scope = set(_paths_of(target))
        table = _brief_table_paths(brief)
        ok = (
            run["exit"] == 0
            and table == scope
            and "docs/note.md → unmatched" in brief
            and "governance/handbook.json → unmatched" in brief
        )
        return Observation(
            ok=bool(ok),
            facts={
                "exit": run["exit"],
                "scope": len(scope),
                "table": len(table),
                "stderr": run["stderr"],
            },
        )

    def negative() -> Observation:
        target, home = _build_delegate_target(
            root, project_payload=_DELEGATE_PROJECT, label="a5n"
        )
        run = _run_delegate(root, task_id="T-HB-A5-N", target=target, home=home)
        brief = run["brief"] or ""
        scope = set(_paths_of(target))
        # The bad input: the same brief with one unmatched path silently
        # dropped — exactly what arm 5 exists to refuse. The detector is
        # 'the table covers the scope'; accepting the doctored brief means
        # a silent drop would go unnoticed.
        dropped = brief.replace("docs/note.md → unmatched\n", "", 1)
        table = _brief_table_paths(dropped)
        accepted = table == scope
        return Observation(
            ok=bool(accepted),
            facts={"scope": len(scope), "doctored_table": len(table)},
        )

    return [
        Control(
            name="arm5-unmatched-recorded",
            expectation=(
                "every path in scope appears in the brief's resolution "
                "table, matched or unmatched; a brief with a path silently "
                "dropped is caught"
            ),
            positive=positive,
            negative=negative,
        )
    ]


def _clone_six(root: Path) -> Path:
    six = root / "six"
    completed = subprocess.run(
        ["git", "clone", "-q", "--branch", SIX_TAG, SIX_URL, str(six)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"cannot clone {SIX_URL}@{SIX_TAG} (network required): "
            f"{completed.stderr.strip()}"
        )
    head = subprocess.run(
        ["git", "-C", str(six), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != SIX_COMMIT:
        raise RuntimeError(
            f"six tag {SIX_TAG} resolved to {head}, expected the pinned {SIX_COMMIT}"
        )
    return six


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--keep-scratch", action="store_true")
    args = parser.parse_args()

    root = Path(tempfile.mkdtemp(prefix="ranex-handbook-proof-"))
    try:
        six = _clone_six(root)
        python = os.environ.get("RANEX_PYTHON", sys.executable)
        subject = Subject(root / "governed", python)
        subject.build()

        ranex_head = subprocess.run(
            ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "environment.json").write_text(
            json.dumps(
                {
                    "six_tag": SIX_TAG,
                    "six_commit": SIX_COMMIT,
                    "ranex_head": ranex_head,
                    "python": python,
                    "repeats": args.repeats,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        calibration = Calibration(out=args.out, repeats=args.repeats)
        controls = [
            *_arm1(six),
            *_arm2(six),
            *_arm3(root),
            *_arm4a(root),
            *_arm4b(subject),
            *_arm5(root),
        ]
        for control in controls:
            calibration.run(control)
        print(f"\nworst: {calibration.worst}  receipt: {args.out / 'calibration.json'}")
        return calibration.exit_code()
    finally:
        if args.keep_scratch:
            print(f"scratch kept: {root}")
        else:
            subprocess.run(["rm", "-rf", str(root)], check=False)


if __name__ == "__main__":
    raise SystemExit(main())
