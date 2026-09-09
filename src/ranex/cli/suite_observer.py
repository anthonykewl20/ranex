"""Install controller-owned pytest reporting into a disposable observation."""

from pathlib import Path

from ranex.foundation.atomic_writer import write_atomic

PLUGIN = "_ranex_pytest_observer_v1"


def pytest_observer_environment(root: Path) -> dict[str, str]:
    directory = root / "pytest-observer"
    directory.mkdir()
    write_atomic(directory / f"{PLUGIN}.py",
                 (Path(__file__).parents[1] / "foundation" / "pytest_xpass.py").read_bytes(), root=root)
    return {"PYTHONPATH": str(directory), "PYTEST_PLUGINS": PLUGIN}
