"""Parse lockfiles and refuse dependencies that cannot be served by pinned wheels."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import unquote, urlparse

from packaging.markers import Marker
from packaging.tags import compatible_tags, cpython_tags
from packaging.utils import parse_wheel_filename

from ranex.provisioning.errors import ProvisioningError


class LockError(ProvisioningError):
    """A lock cannot provide a safe, compatible wheel closure."""


_WHEEL_SHA256 = re.compile(r"sha256:([0-9a-fA-F]{64})\Z")


@dataclass(frozen=True, slots=True)
class TargetEnvironment:
    implementation: str
    python_version: tuple[int, int]
    platforms: tuple[str, ...]
    marker_environment: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class WheelArtifact:
    package: str
    version: str
    filename: str
    url: str
    sha256: str


@dataclass(frozen=True, slots=True)
class Dependency:
    name: str
    marker: str | None


@dataclass(frozen=True, slots=True)
class Package:
    name: str
    version: str
    source: Mapping[str, Any]
    dependencies: tuple[Dependency, ...]
    dev_dependencies: Mapping[str, tuple[Dependency, ...]]
    wheels: tuple[Mapping[str, Any], ...]
    has_sdist: bool


@dataclass(frozen=True, slots=True)
class Lock:
    packages: tuple[Package, ...]

    @property
    def by_name(self) -> dict[str, Package]:
        return {package.name: package for package in self.packages}


def _dependencies(value: Any, package: str) -> tuple[Dependency, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise LockError(f"package {package} has malformed dependencies")
    result: list[Dependency] = []
    for item in value:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            raise LockError(f"package {package} has malformed dependency")
        marker = item.get("marker")
        if marker is not None and (not isinstance(marker, str) or not marker):
            raise LockError(f"package {package} has malformed dependency marker")
        result.append(Dependency(item["name"], marker))
    return tuple(result)


def parse_lock(data: bytes) -> Lock:
    """Parse the lock shape used for resolution, refusing malformed records."""
    try:
        parsed = tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise LockError(f"cannot parse lockfile: {exc}") from exc
    records = parsed.get("package")
    if not isinstance(records, list):
        raise LockError("lockfile has no package records")
    packages: list[Package] = []
    names: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise LockError("lockfile has malformed package record")
        name, version, source = record.get("name"), record.get("version"), record.get("source")
        if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
            raise LockError("lockfile package has no name or version")
        if name in names:
            raise LockError(f"lockfile contains package {name!r} more than once")
        names.add(name)
        if not isinstance(source, dict) or not source:
            raise LockError(f"package {name} has malformed source")
        dev_value = record.get("dev-dependencies", {})
        if not isinstance(dev_value, dict):
            raise LockError(f"package {name} has malformed dev-dependencies")
        dev_dependencies = {
            group: _dependencies(dependencies, name)
            for group, dependencies in dev_value.items()
            if isinstance(group, str)
        }
        if len(dev_dependencies) != len(dev_value):
            raise LockError(f"package {name} has malformed dev-dependencies")
        wheels_value = record.get("wheels", [])
        if not isinstance(wheels_value, list) or any(not isinstance(wheel, dict) for wheel in wheels_value):
            raise LockError(f"package {name} has malformed wheels")
        packages.append(
            Package(
                name,
                version,
                source,
                _dependencies(record.get("dependencies"), name),
                dev_dependencies,
                tuple(wheels_value),
                "sdist" in record,
            )
        )
    return Lock(tuple(packages))


def _edge_enabled(edge: Dependency, target: TargetEnvironment, owner: str) -> bool:
    if edge.marker is None:
        return True
    try:
        return Marker(edge.marker).evaluate(environment=dict(target.marker_environment))
    except Exception as exc:
        raise LockError(f"package {owner} has invalid marker {edge.marker!r}: {exc}") from exc


def _filename(url: str, package: str) -> str:
    filename = unquote(PurePosixPath(urlparse(url).path).name)
    if not filename:
        raise LockError(f"package {package} wheel has no filename")
    return filename


def select_wheels(lock: Lock, root: str, target: TargetEnvironment) -> tuple[WheelArtifact, ...]:
    """Select one best compatible wheel for every reachable non-root package."""
    packages = lock.by_name
    root_package = packages.get(root)
    if root_package is None:
        available = ", ".join(sorted(packages))
        raise LockError(
            f"root package {root!r} is absent from lockfile (packages: {available})"
        )
    reachable: set[str] = set()
    root_edges = (
        *root_package.dependencies,
        *(edge for group in root_package.dev_dependencies.values() for edge in group),
    )
    work: list[tuple[str, Dependency]] = [(root, edge) for edge in root_edges]
    while work:
        owner, edge = work.pop()
        if not _edge_enabled(edge, target, owner):
            continue
        package = packages.get(edge.name)
        if package is None:
            raise LockError(f"package dependency {edge.name!r} is absent from lockfile")
        if package.name in reachable:
            continue
        reachable.add(package.name)
        for dependency in package.dependencies:
            work.append((package.name, dependency))
    supported = tuple(
        cpython_tags(
            python_version=target.python_version,
            abis=None,
            platforms=target.platforms,
        )
    ) + tuple(
        compatible_tags(
            python_version=target.python_version,
            interpreter=(
                f"{target.implementation}{target.python_version[0]}"
                f"{target.python_version[1]}"
            ),
            platforms=target.platforms,
        )
    )
    order = {tag: index for index, tag in enumerate(supported)}
    selected: list[WheelArtifact] = []
    for name in sorted(reachable):
        package = packages[name]
        if set(package.source) != {"registry"}:
            raise LockError(f"package {package.name} has non-registry source")
        if not package.wheels:
            raise LockError(f"package {package.name} has no wheels")
        candidates: list[tuple[int, WheelArtifact]] = []
        for wheel in package.wheels:
            url, hashed = wheel.get("url"), wheel.get("hash")
            if not isinstance(url, str) or not url or not isinstance(hashed, str):
                raise LockError(f"package {package.name} has malformed wheel")
            match = _WHEEL_SHA256.fullmatch(hashed)
            if match is None:
                raise LockError(f"package {package.name} has malformed sha256 wheel hash")
            filename = _filename(url, package.name)
            try:
                _, _, _, tags = parse_wheel_filename(filename)
            except Exception as exc:
                raise LockError(f"package {package.name} has invalid wheel {filename!r}") from exc
            ranks = [order[tag] for tag in tags if tag in order]
            if ranks:
                candidates.append((min(ranks), WheelArtifact(package.name, package.version, filename, url, match.group(1).lower())))
        if not candidates:
            raise LockError(
                f"package {package.name} {package.version} has no wheel for "
                f"target {target.platforms}"
            )
        selected.append(min(candidates, key=lambda candidate: candidate[0])[1])
    return tuple(selected)
