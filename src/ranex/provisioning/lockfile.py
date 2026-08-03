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
    # Present only when the lock holds more than one version of `name`, which
    # is how uv disambiguates an edge under split resolution. Absent means
    # "the one version there is", and a name with several versions and no
    # version on the edge is resolved by resolution markers instead.
    version: str | None = None


@dataclass(frozen=True, slots=True)
class Package:
    name: str
    version: str
    source: Mapping[str, Any]
    dependencies: tuple[Dependency, ...]
    dev_dependencies: Mapping[str, tuple[Dependency, ...]]
    wheels: tuple[Mapping[str, Any], ...]
    has_sdist: bool
    # The marker expressions this entry is the answer for. uv writes these
    # only on a package it locked at several versions; one of them must hold
    # for the target, or this entry is not the one that target installs.
    resolution_markers: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str]:
        return (self.name, self.version)


@dataclass(frozen=True, slots=True)
class Lock:
    packages: tuple[Package, ...]

    @property
    def by_key(self) -> dict[tuple[str, str], Package]:
        return {package.key: package for package in self.packages}

    def versions_of(self, name: str) -> tuple[Package, ...]:
        return tuple(package for package in self.packages if package.name == name)


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
        version = item.get("version")
        if version is not None and (not isinstance(version, str) or not version):
            raise LockError(f"package {package} has malformed dependency version")
        result.append(Dependency(item["name"], marker, version))
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
    names: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            raise LockError("lockfile has malformed package record")
        name, version, source = record.get("name"), record.get("version"), record.get("source")
        if not isinstance(name, str) or not name or not isinstance(version, str) or not version:
            raise LockError("lockfile package has no name or version")
        # Keyed by name AND version: a lock legitimately holds one package at
        # several versions under split resolution, and refusing that refused
        # every real lock that resolves across interpreter versions. Only an
        # exact repeat is corruption, because then one key names two entries
        # and which one is selected would depend on file order.
        if (name, version) in names:
            raise LockError(
                f"lockfile contains package {name!r} {version} more than once"
            )
        names.add((name, version))
        markers = record.get("resolution-markers", [])
        if not isinstance(markers, list) or any(
            not isinstance(marker, str) for marker in markers
        ):
            raise LockError(f"package {name} has malformed resolution-markers")
        if not isinstance(source, dict) or not source:
            raise LockError(f"package {name} has malformed source")
        dev_value = record.get("dev-dependencies", {})
        if not isinstance(dev_value, dict):
            raise LockError(f"package {name} has malformed dev-dependencies")
        # No non-string-key guard: TOML table keys are always strings, so it
        # could never fire, and a branch no input can reach is decoration
        # rather than a control.
        dev_dependencies = {
            group: _dependencies(dependencies, name)
            for group, dependencies in dev_value.items()
        }
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
                tuple(markers),
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


def _resolve_edge(
    lock: Lock, edge: Dependency, target: TargetEnvironment
) -> Package:
    """The one package entry this edge selects for this target.

    Three shapes, in the order uv writes them. A name locked once is
    unambiguous. A name locked several times carries the version on the
    edge, and that exact entry is taken. An edge without a version against a
    multi-version name is decided by the entries' own resolution markers,
    and only a single match is an answer — several matches or none is a
    refusal, because guessing which version the target installs is choosing
    the bytes the verdict rests on.
    """

    candidates = lock.versions_of(edge.name)
    if not candidates:
        raise LockError(f"package dependency {edge.name!r} is absent from lockfile")
    if edge.version is not None:
        exact = [package for package in candidates if package.version == edge.version]
        if not exact:
            raise LockError(
                f"package dependency {edge.name!r} names version "
                f"{edge.version}, which the lockfile does not carry"
            )
        return exact[0]
    if len(candidates) == 1:
        return candidates[0]
    matched = [
        package
        for package in candidates
        if any(
            _edge_enabled(Dependency(package.name, marker), target, package.name)
            for marker in package.resolution_markers
        )
    ]
    if len(matched) != 1:
        versions = ", ".join(sorted(package.version for package in candidates))
        raise LockError(
            f"package {edge.name!r} is locked at several versions ({versions}) "
            f"and {len(matched)} of them match this target's resolution "
            "markers; the lock does not say which one this target installs"
        )
    return matched[0]


def select_wheels(lock: Lock, root: str, target: TargetEnvironment) -> tuple[WheelArtifact, ...]:
    """Select one best compatible wheel for every reachable non-root package."""
    roots = lock.versions_of(root)
    if not roots:
        available = ", ".join(sorted({package.name for package in lock.packages}))
        raise LockError(
            f"root package {root!r} is absent from lockfile (packages: {available})"
        )
    root_package = roots[0]
    reachable: dict[tuple[str, str], Package] = {}
    root_edges = (
        *root_package.dependencies,
        *(edge for group in root_package.dev_dependencies.values() for edge in group),
    )
    work: list[tuple[str, Dependency]] = [(root, edge) for edge in root_edges]
    while work:
        owner, edge = work.pop()
        if not _edge_enabled(edge, target, owner):
            continue
        package = _resolve_edge(lock, edge, target)
        if package.key in reachable:
            continue
        reachable[package.key] = package
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
    for key in sorted(reachable):
        package = reachable[key]
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
