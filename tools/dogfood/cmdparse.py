"""Parse task test commands without guessing a positional argv slot.

VulcanBench cmds are heterogeneous: env assignments, `python -m pytest`,
flag order, and node ids can sit anywhere. Taking argv[3] silently grades
the wrong token (F-005.3). Node ids are tokens matching `file::name`.
"""

from __future__ import annotations

import re
import shlex

PINNED_PYTHON = "/usr/bin/python3"
NODE_ID = re.compile(r"^[^\s:]+::.+$")
ENV_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def parse_cmd(cmd: str) -> tuple[list[str], list[str], list[str]]:
    """Return (env assignments, argv tokens, node ids). shlex, no guessing."""
    tokens = shlex.split(cmd)
    env: list[str] = []
    argv: list[str] = []
    for token in tokens:
        if ENV_ASSIGN.match(token) and not argv:
            env.append(token)
        else:
            argv.append(token)
    node_ids = [token for token in argv if NODE_ID.match(token)]
    return env, argv, node_ids


def node_ids_from_entries(entries: list[dict]) -> list[str]:
    """Collect node ids from metadata test entries. Refuses a cmd with none."""
    collected: list[str] = []
    for entry in entries:
        cmd = entry.get("cmd", "")
        _env, _argv, node_ids = parse_cmd(cmd)
        if not node_ids:
            raise AssertionError(
                f"cmd yields no test node ids (refusing argv[3] guess): {cmd!r}"
            )
        collected.extend(node_ids)
    return collected


def pinned_argv(argv: list[str], pinned_python: str = PINNED_PYTHON) -> list[str]:
    """Rewrite a leading `python`/`python3` to the pinned interpreter."""
    if not argv:
        return argv
    if argv[0] in ("python", "python3"):
        return [pinned_python, *argv[1:]]
    return list(argv)



def command_environment(assignments: list[str], base: dict[str, str]) -> dict[str, str]:
    """Apply leading assignments to one command; duplicate names use the last value."""

    environment = dict(base)
    for assignment in assignments:
        name, _, value = assignment.partition("=")
        environment[name] = value
    return environment


def governed_argv(cmd: str, pinned_python: str = PINNED_PYTHON) -> list[str]:
    """Bind assignment semantics in argv, so the hermetic runner need not inherit env."""

    assignments, argv, _ = parse_cmd(cmd)
    if not argv:
        raise ValueError("task command carries no executable")
    resolved = pinned_argv(argv, pinned_python)
    return ["/usr/bin/env", *assignments, *resolved] if assignments else resolved
