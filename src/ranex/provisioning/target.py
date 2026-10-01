"""Ask the pinned interpreter what it is, instead of assuming this process is it.

The resolver, the wheels and the assembled root all serve one interpreter:
the pinned one, which need not be the interpreter running Ranex. Marker
evaluation and wheel-tag selection therefore take their facts from a probe
executed BY the pinned interpreter, using stdlib and the installed pinned
packaging implementation. Target site packages never make this decision.
"""

from __future__ import annotations

import inspect
import json
import subprocess
from pathlib import Path

from packaging import _elffile, _manylinux, _musllinux, tags

from ranex.cli.toolchain import pinned_path_value
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.lockfile import TargetEnvironment


class TargetError(ProvisioningError):
    """The pinned interpreter cannot describe a usable target environment."""


# Everything PEP 508 markers can ask about, answered by the interpreter that
# will import the wheels. Extra contexts are supplied by the closure traversal.
_PROBE = """\
import json, os, platform, sys
print(json.dumps({
    "python_version": [sys.version_info[0], sys.version_info[1]],
    "implementation_name": sys.implementation.name,
    "machine": platform.machine(),
    "supported_tags": [str(tag) for tag in target_tags.sys_tags()],
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


def _probe_script() -> str:
    """Run our installed packaging implementation against the target runtime.

    The target need not have packaging installed. Load only these trusted
    installed sources, preserving their notices, rather than importing target
    site packages or recreating packaging's platform and ABI rules.
    """
    sources = [(module.__name__.rsplit(".", 1)[1], inspect.getsource(module))
               for module in (_elffile, _manylinux, _musllinux, tags)]
    return """import sys, types
package = types.ModuleType('_ranex_packaging')
package.__path__ = []
sys.modules[package.__name__] = package
for name, source in """ + repr(sources) + """:
    module = types.ModuleType(package.__name__ + '.' + name)
    module.__package__ = package.__name__
    sys.modules[module.__name__] = module
    setattr(package, name, module)
    exec(compile(source, '<pinned-packaging/' + name + '>', 'exec'), module.__dict__)
target_tags = package.tags
""" + _PROBE


def probe_target(python: Path) -> TargetEnvironment:
    """Run the pinned interpreter and return the environment it reports."""

    try:
        completed = subprocess.run(
            [str(python), "-I", "-S", "-c", _probe_script()],
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
        implementation = str(answer["implementation_name"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise TargetError(
            f"pinned interpreter {python} answered malformed probe output"
        ) from exc
    if len(version) != 2:
        raise TargetError(f"pinned interpreter {python} reported no version")
    if not all(isinstance(value, str) for value in markers.values()):
        raise TargetError(f"pinned interpreter {python} reported malformed markers")
    supported = answer.get("supported_tags")
    if not isinstance(supported, list) or not supported or any(
        not isinstance(tag, str) or len(tag.split("-")) != 3
        or any(not component for component in tag.split("-")) for tag in supported
    ):
        raise TargetError(f"pinned interpreter {python} reported malformed wheel tags")
    return TargetEnvironment(
        # packaging's tag names abbreviate CPython to "cp"; every other
        # implementation keeps the name the interpreter reports.
        implementation="cp" if implementation == "cpython" else implementation,
        python_version=(version[0], version[1]),
        platforms=tuple(dict.fromkeys(tag.rsplit("-", 1)[1] for tag in supported
                                      if not tag.endswith("-any"))),
        marker_environment=markers,
        supported_tags=tuple(supported),
    )
