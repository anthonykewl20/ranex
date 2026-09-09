"""Install controller-owned pytest reporting into a disposable observation."""

from collections.abc import Sequence
from pathlib import Path

from ranex.foundation.atomic_writer import write_atomic

PLUGIN = "_ranex_pytest_observer_v1"
NAMED_PLUGIN = "ranex.foundation.pytest_xpass"


def pytest_observer_environment(root: Path, command: Sequence[str] = ()) -> dict[str, str]:
    directory = root / "pytest-observer"
    directory.mkdir()
    source = (Path(__file__).parents[1] / "foundation" / "pytest_xpass.py").read_bytes()
    write_atomic(directory / f"{PLUGIN}.py", source, root=root)
    options = command[:command.index("--")] if "--" in command else command
    if ("-p", NAMED_PLUGIN) in zip(options, options[1:], strict=False) or f"-p{NAMED_PLUGIN}" in options:
        # Supply only the explicitly requested module. A whole site-packages
        # path would replace the subject's dependencies with the controller's.
        # Namespace portions defer to a real materialised Ranex package.
        named = directory / "ranex" / "foundation"
        named.mkdir(parents=True)
        write_atomic(named / "pytest_xpass.py", source, root=root)
    return {"PYTHONPATH": str(directory), "PYTEST_PLUGINS": PLUGIN}
