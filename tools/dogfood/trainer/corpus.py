"""Corpus classification: every task gets an honest exercisability verdict.

Real corpora are heterogeneous (AUDIT finding C-01: the previous harness
assumed one cmd grammar and silently ran nonsense on the first task that
disagreed). Classification therefore PARSES each test command into
(env-assignments, argv, node-ids) and refuses to guess: a task whose commands
yield no node ids is 'cmd-unparseable', a task whose toolchain is not pinned
on this machine is 'toolchain-unavailable' — both are recorded as training
classes, never silently skipped.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# argv[0] tokens the pinned toolchain can provide on this class of machine.
PINNED_PYTHON = "/usr/bin/python3"
_NODE_ID = re.compile(r"^[^\s:]+::.+$")
_ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


@dataclass(frozen=True)
class TestEntry:
    name: str
    node_ids: tuple[str, ...]
    argv0: str          # after env-prefix stripping, before substitution
    grammar: str        # grammar family, for coverage bookkeeping
    env: tuple[str, ...] = ()   # ENV=value prefixes the task's own cmd carries

    @property
    def runnable(self) -> bool:
        return bool(self.node_ids) and self.argv0 == "python"


@dataclass(frozen=True)
class TaskRecord:
    suite: str
    task: str
    path: str
    language: str
    classification: str            # exercisable | toolchain-unavailable | cmd-unparseable | diff-graded
    entries: tuple[TestEntry, ...] = ()
    notes: tuple[str, ...] = field(default=())

    @property
    def id(self) -> str:
        return f"{self.suite}/{self.task}"

    def as_dict(self) -> dict:
        return {
            "suite": self.suite, "task": self.task, "path": self.path,
            "language": self.language, "classification": self.classification,
            "entries": [
                {"name": e.name, "node_ids": list(e.node_ids),
                 "argv0": e.argv0, "grammar": e.grammar, "runnable": e.runnable,
                 "env": list(e.env)}
                for e in self.entries
            ],
            "notes": list(self.notes),
        }


def _parse_cmd(cmd: str) -> tuple[list[str], list[str], list[str]]:
    """-> (env assignments, argv tokens, node ids). shlex, no guessing."""
    import shlex

    tokens = shlex.split(cmd)
    env: list[str] = []
    argv: list[str] = []
    for token in tokens:
        if _ENV_ASSIGN.match(token) and not argv:
            env.append(token)
        else:
            argv.append(token)
    node_ids = [t for t in argv if _NODE_ID.match(t)]
    return env, argv, node_ids


def _grammar_family(argv: list[str], node_ids: list[str]) -> str:
    head = " ".join(argv[:3])
    if argv[:1] == ["python"] and "-m" in argv[:2]:
        fam = "python -m pytest"
    elif argv[:1] == ["python"]:
        fam = "python <script>"
    else:
        fam = argv[0] if argv else "<empty>"
    flags = [t for t in argv if t.startswith("-") and not _NODE_ID.match(t)]
    fam += f" +{len(flags)}flags" if flags else ""
    fam += " +nodeids" if node_ids else " -nodeids"
    return fam


def classify_task(task_dir: Path) -> TaskRecord:
    meta_path = task_dir / "metadata.json"
    meta = json.loads(meta_path.read_text())
    languages = meta.get("languages") or ["?"]
    language = ",".join(sorted(languages))
    tests = meta.get("tests")
    entries: list[TestEntry] = []
    notes: list[str] = []
    f2p = tests.get("fail_to_pass", []) if isinstance(tests, dict) else []
    if not f2p and (task_dir / "grader_cases.json").is_file():
        return TaskRecord(task_dir.parent.name, task_dir.name, str(task_dir),
                          language, "diff-graded", (), ("grader_cases.json contract",))
    if not f2p:
        return TaskRecord(task_dir.parent.name, task_dir.name, str(task_dir),
                          language, "cmd-unparseable", (),
                          ("metadata carries no tests.fail_to_pass",))
    for entry in f2p:
        env, argv, node_ids = _parse_cmd(entry["cmd"])
        argv0 = argv[0] if argv else ""
        grammar = _grammar_family(argv, node_ids)
        entries.append(TestEntry(entry["name"], tuple(node_ids), argv0, grammar,
                                 tuple(env)))
    runnable = all(e.runnable for e in entries)
    if runnable:
        classification = "exercisable"
    elif any(e.argv0 == "python" for e in entries):
        classification = "cmd-unparseable"
        notes.append("python task with at least one command yielding no node ids")
    else:
        classification = "toolchain-unavailable"
        notes.append(f"argv0 set: {sorted({e.argv0 for e in entries})}")
    return TaskRecord(task_dir.parent.name, task_dir.name, str(task_dir),
                      language, classification, tuple(entries), tuple(sorted(set(notes))))


def classify_corpus(vulcan_root: Path, suites: list[str] | None = None) -> list[TaskRecord]:
    tasks_root = vulcan_root / "tasks"
    selected = sorted(
        p for p in tasks_root.iterdir()
        if p.is_dir() and (suites is None or p.name in suites)
    )
    records: list[TaskRecord] = []
    for suite in selected:
        for task_dir in sorted(suite.iterdir()):
            if (task_dir / "metadata.json").is_file():
                records.append(classify_task(task_dir))
    return records


def canonical_bytes(value) -> bytes:
    import json as _json

    return _json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8")
