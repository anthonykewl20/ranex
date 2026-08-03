"""Ask the pinned interpreter what it is, instead of assuming this process is it.

The resolver, the wheels and the assembled root all serve one interpreter:
the pinned one, which need not be the interpreter running Ranex. Marker
evaluation and wheel-tag selection therefore take their facts from a probe
executed BY the pinned interpreter, with a stdlib-only script — importing
anything else would put unpinned code in front of the selection decision.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ranex.cli.toolchain import pinned_path_value
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.lockfile import TargetEnvironment


class TargetError(ProvisioningError):
    """The pinned interpreter cannot describe a usable target environment."""


# Everything PEP 508 markers can ask about, answered by the interpreter that
# will import the wheels. `extra` is defined as empty: extras were resolved
# into the lock's edges already, and an undefined variable fails evaluation.
_PROBE = """\
import json, os, platform, sys
print(json.dumps({
    "python_version": [sys.version_info[0], sys.version_info[1]],
    "implementation_name": sys.implementation.name,
    "machine": platform.machine(),
    "glibc": os.confstr("CS_GNU_LIBC_VERSION") if hasattr(os, "confstr") else "",
    "markers": {
        "python_version": ".".join(map(str, sys.version_info[:2])),
        "python_full_version": platform.python_version(),
        "implementation_name": sys.implementation.name,
        "implementation_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "platform_python_implementation": platform.python_implementation(),
        "sys_platform": sys.platform,
        "os_name": os.name,
        "extra": "",
    },
}))
"""


def _platforms(machine: str, glibc: str) -> tuple[str, ...]:
    """Platform tags the probed host serves, most specific first.

    A glibc host accepts every manylinux tag up to its own minor version;
    the plain linux tag stays last as the least specific. A non-glibc or
    non-Linux answer keeps only what the probe literally reported — guessing
    a compatibility range that was not measured is how a wheel gets selected
    for a host that cannot load it.
    """

    parts = glibc.split()
    if len(parts) == 2 and parts[0] == "glibc":
        try:
            major, minor = (int(piece) for piece in parts[1].split(".")[:2])
        except ValueError:
            return (f"linux_{machine}",)
        if major == 2:
            return tuple(
                f"manylinux_2_{version}_{machine}" for version in range(minor, 4, -1)
            ) + (f"linux_{machine}",)
    return (f"linux_{machine}",)


def probe_target(python: Path) -> TargetEnvironment:
    """Run the pinned interpreter and return the environment it reports."""

    try:
        completed = subprocess.run(
            [str(python), "-I", "-c", _PROBE],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": pinned_path_value()},
        )
    except OSError as exc:
        raise TargetError(f"cannot run pinned interpreter {python}: {exc}") from exc
    if completed.returncode != 0:
        raise TargetError(
            f"pinned interpreter {python} cannot describe itself: "
            f"{completed.stderr.strip()}"
        )
    try:
        answer = json.loads(completed.stdout)
        version = tuple(int(part) for part in answer["python_version"])
        markers = dict(answer["markers"])
        machine = str(answer["machine"])
        implementation = str(answer["implementation_name"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise TargetError(
            f"pinned interpreter {python} answered malformed probe output"
        ) from exc
    if len(version) != 2:
        raise TargetError(f"pinned interpreter {python} reported no version")
    if not all(isinstance(value, str) for value in markers.values()):
        raise TargetError(f"pinned interpreter {python} reported malformed markers")
    return TargetEnvironment(
        # packaging's tag names abbreviate CPython to "cp"; every other
        # implementation keeps the name the interpreter reports.
        implementation="cp" if implementation == "cpython" else implementation,
        python_version=(version[0], version[1]),
        platforms=_platforms(machine, str(answer.get("glibc", ""))),
        marker_environment=markers,
    )
