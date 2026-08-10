"""Focused refusal coverage for dependency provisioning."""

from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path
from urllib.error import URLError

import pytest

from ranex.provisioning.derivation import DerivationError, derive_lock, refuse_mismatch
from ranex.provisioning.fetching import FetchError, ensure_wheels
from ranex.provisioning.lockfile import (
    Dependency,
    Lock,
    LockError,
    Package,
    TargetEnvironment,
    WheelArtifact,
    _edge_enabled,
    _filename,
    _resolve_edge,
    parse_lock,
    select_wheels,
)
from ranex.provisioning.pins import (
    PinsError,
    ResolutionPins,
    load_pins_text,
    refuse_writable_interpreter,
    verified_pinned_binary,
)
from ranex.provisioning.root import RootError, _seal, verified_wheel_paths
from ranex.provisioning.store import StoreError, WheelStore
from ranex.provisioning.target import TargetError, _platforms, probe_target

TARGET = TargetEnvironment(
    implementation="cp", python_version=(3, 12),
    platforms=("manylinux_2_17_x86_64", "linux_x86_64"),
    marker_environment={"python_version": "3.12", "python_full_version": "3.12.1",
                        "implementation_name": "cpython", "platform_system": "Linux",
                        "platform_machine": "x86_64", "sys_platform": "linux",
                        "os_name": "posix", "platform_python_implementation": "CPython",
                        "extra": ""},
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lock_text(*, packages: str) -> bytes:
    return ("version = 1\n" + packages).encode()


def package(name: str, version: str = "1.0", *, extra: str = "") -> str:
    return f'''[[package]]
name = "{name}"
version = "{version}"
source = {{ registry = "https://example.test" }}
{extra}
'''


def wheel(name: str, data: bytes = b"wheel") -> str:
    return f'{{ url = "https://files.example/{name}-1.0-py3-none-any.whl", hash = "sha256:{digest(data)}" }}'


def root_and_dep(dep_extra: str = "", root_extra: str = "") -> Lock:
    dep_fields = dep_extra or f"wheels = [{wheel('dep')}]"
    return parse_lock(lock_text(packages=(
        package("dep", extra=dep_fields)
        + package("root", extra=f'dependencies = [{{ name = "dep" }}]\n{root_extra}')
    )))


def test_lock_by_key_returns_name_version_mapping() -> None:
    # Input: two distinct package records.
    lock = parse_lock(lock_text(packages=package("one") + package("two", "2.0")))
    assert lock.by_key[("one", "1.0")].name == "one"
    assert lock.by_key[("two", "2.0")].version == "2.0"


def test_parse_lock_refuses_no_package_records() -> None:
    # Input: no [[package]] record exists.
    with pytest.raises(LockError, match="no package records"):
        parse_lock(b"version = 1\n")


def test_parse_lock_refuses_non_table_package_record() -> None:
    # Input: package is a list of non-tables.
    with pytest.raises(LockError, match="malformed package record"):
        parse_lock(b"package = [1]\n")


def test_parse_lock_refuses_package_without_name_or_version() -> None:
    # Input: package record omits its version.
    with pytest.raises(LockError, match="no name or version"):
        parse_lock(lock_text(packages='[[package]]\nname = "x"\nsource = { registry = "x" }\n'))


def test_parse_lock_refuses_exact_duplicate() -> None:
    # Input: two records have the same name and version.
    with pytest.raises(LockError, match="more than once"):
        parse_lock(lock_text(packages=package("x") + package("x")))


def test_parse_lock_refuses_malformed_resolution_markers() -> None:
    # Input: resolution-markers contains an integer.
    with pytest.raises(LockError, match="malformed resolution-markers"):
        parse_lock(lock_text(packages=package("x", extra="resolution-markers = [1]")))


@pytest.mark.parametrize("source", ["source = 1", "source = {}"])
def test_parse_lock_refuses_malformed_source(source: str) -> None:
    # Input: source is not a populated mapping.
    with pytest.raises(LockError, match="malformed source"):
        parse_lock(lock_text(packages='[[package]]\nname = "x"\nversion = "1"\n' + source))


def test_parse_lock_refuses_non_mapping_dev_dependencies() -> None:
    # Input: dev-dependencies is an integer.
    with pytest.raises(LockError, match="malformed dev-dependencies"):
        parse_lock(lock_text(packages=package("x", extra="dev-dependencies = 1")))


def test_parse_lock_accepts_valid_dev_dependencies_defence_guard_unreachable() -> None:
    # Input: a valid TOML dev-dependencies table; non-string TOML keys cannot reach the defence-in-depth guard.
    lock = parse_lock(lock_text(packages=package("x", extra='[package.dev-dependencies]\ntest = []')))
    assert lock.packages[0].dev_dependencies == {"test": ()}


@pytest.mark.parametrize("wheels", ["wheels = 1", "wheels = [1]"])
def test_parse_lock_refuses_malformed_wheels(wheels: str) -> None:
    # Input: wheels is not a list of mappings.
    with pytest.raises(LockError, match="malformed wheels"):
        parse_lock(lock_text(packages=package("x", extra=wheels)))


def test_dependencies_refuses_non_list() -> None:
    # Input: dependencies is an integer.
    with pytest.raises(LockError, match="malformed dependencies"):
        parse_lock(lock_text(packages=package("x", extra="dependencies = 1")))


@pytest.mark.parametrize("dependencies", ["dependencies = [1]", "dependencies = [{}]"])
def test_dependencies_refuses_malformed_member(dependencies: str) -> None:
    # Input: dependencies contains a non-dependency member.
    with pytest.raises(LockError, match="malformed dependency"):
        parse_lock(lock_text(packages=package("x", extra=dependencies)))


@pytest.mark.parametrize("marker", ["1", '\"\"'])
def test_dependencies_refuses_malformed_marker(marker: str) -> None:
    # Input: dependency marker is non-string or empty.
    with pytest.raises(LockError, match="malformed dependency marker"):
        parse_lock(lock_text(packages=package("x", extra=f'dependencies = [{{ name = "y", marker = {marker} }}]')))


@pytest.mark.parametrize("version", ["1", '\"\"'])
def test_dependencies_refuses_malformed_version(version: str) -> None:
    # Input: dependency version is non-string or empty.
    with pytest.raises(LockError, match="malformed dependency version"):
        parse_lock(lock_text(packages=package("x", extra=f'dependencies = [{{ name = "y", version = {version} }}]')))


def test_edge_enabled_refuses_invalid_marker_with_owner() -> None:
    # Input: dependency marker is syntactically invalid.
    with pytest.raises(LockError, match="owner.*invalid marker"):
        _edge_enabled(Dependency("dep", "this is not a marker"), TARGET, "owner")


def test_filename_refuses_url_without_basename() -> None:
    # Input: wheel URL ends at a directory slash.
    with pytest.raises(LockError, match="wheel has no filename"):
        _filename("https://files.example/", "dep")


def test_resolve_edge_refuses_absent_package() -> None:
    # Input: edge names no package in the lock.
    with pytest.raises(LockError, match="absent from lockfile"):
        _resolve_edge(Lock(()), Dependency("missing", None), TARGET)


def test_resolve_edge_refuses_absent_explicit_version() -> None:
    # Input: edge names a version the lock does not carry.
    with pytest.raises(LockError, match="does not carry"):
        _resolve_edge(parse_lock(lock_text(packages=package("dep"))), Dependency("dep", None, "2"), TARGET)


def test_resolve_edge_selects_held_explicit_version() -> None:
    # Input: edge explicitly selects a held version.
    lock = parse_lock(lock_text(packages=package("dep", "1") + package("dep", "2")))
    assert _resolve_edge(lock, Dependency("dep", None, "2"), TARGET).version == "2"


def test_resolve_edge_refuses_zero_marker_matches() -> None:
    # Input: neither split-resolution marker matches the target.
    lock = parse_lock(lock_text(packages=package("dep", "1", extra='resolution-markers = ["python_version < \'3\'"]') + package("dep", "2", extra='resolution-markers = ["python_version < \'3\'"]')))
    with pytest.raises(LockError, match=r"1, 2.*0 of them"):
        _resolve_edge(lock, Dependency("dep", None), TARGET)


def test_resolve_edge_refuses_two_marker_matches() -> None:
    # Input: both split-resolution markers match the target.
    lock = parse_lock(lock_text(packages=package("dep", "1", extra='resolution-markers = ["python_version >= \'3\'"]') + package("dep", "2", extra='resolution-markers = ["python_version >= \'3\'"]')))
    with pytest.raises(LockError, match=r"1, 2.*2 of them"):
        _resolve_edge(lock, Dependency("dep", None), TARGET)


def test_select_wheels_skips_incompatible_wheel() -> None:
    # Input: dependency offers incompatible then compatible wheel.
    lock = root_and_dep(dep_extra=f'wheels = [{wheel("bad").replace("py3-none-any", "cp39-cp39-win_amd64")}, {wheel("good")}]')
    assert select_wheels(lock, "root", TARGET)[0].filename == "good-1.0-py3-none-any.whl"


@pytest.mark.parametrize("entry", ['{ hash = "sha256:' + "a" * 64 + '" }', '{ url = "https://x/a-1.0-py3-none-any.whl", hash = 1 }'])
def test_select_wheels_refuses_malformed_wheel(entry: str) -> None:
    # Input: selected wheel lacks a string URL or hash.
    with pytest.raises(LockError, match="dep.*malformed wheel"):
        select_wheels(root_and_dep(dep_extra=f"wheels = [{entry}]"), "root", TARGET)


def test_select_wheels_refuses_unparseable_wheel_filename() -> None:
    # Input: selected wheel filename is not a valid wheel name.
    lock = root_and_dep(dep_extra=f'wheels = [{{ url = "https://x/not-a-wheel.whl", hash = "sha256:{digest(b"x")}" }}]')
    with pytest.raises(LockError, match="invalid wheel"):
        select_wheels(lock, "root", TARGET)


def test_store_refuses_invalid_digest_for_publish_and_read(tmp_path: Path) -> None:
    # Input: digest is not 64 lowercase hexadecimal characters.
    store = WheelStore(tmp_path)
    with pytest.raises(StoreError, match="64 lowercase hex"):
        store.publish("BAD", b"x")
    with pytest.raises(StoreError, match="64 lowercase hex"):
        store.verified_path("BAD")


def test_store_publish_refuses_temp_write_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: mkstemp raises while publishing.
    monkeypatch.setattr("ranex.provisioning.store.tempfile.mkstemp", lambda **_: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(StoreError, match="cannot publish"):
        WheelStore(tmp_path).publish(digest(b"x"), b"x")


def test_store_publish_cleans_temp_after_replace_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: os.replace fails after the temporary wheel exists.
    monkeypatch.setattr("ranex.provisioning.store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("replace")))
    with pytest.raises(StoreError, match="cannot publish"):
        WheelStore(tmp_path).publish(digest(b"x"), b"x")
    assert list((tmp_path / "tmp").iterdir()) == []


def test_store_verified_path_refuses_non_file_oserror(tmp_path: Path) -> None:
    # Input: store entry is a directory, so read_bytes fails with OSError.
    address = "a" * 64
    (tmp_path / "sha256" / address).mkdir(parents=True)
    with pytest.raises(StoreError, match="cannot read wheel-store entry"):
        WheelStore(tmp_path).verified_path(address)


def test_store_quarantine_lost_race_still_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: quarantine rename loses a concurrent FileNotFoundError race.
    address = digest(b"expected")
    store = WheelStore(tmp_path)
    (tmp_path / "sha256").mkdir()
    (tmp_path / "sha256" / address).write_bytes(b"wrong")
    monkeypatch.setattr("ranex.provisioning.store.os.replace", lambda *_: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(StoreError, match="failed verification"):
        store.verified_path(address)


def test_store_quarantine_other_oserror_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: quarantine rename raises a non-race OSError.
    address = digest(b"expected")
    (tmp_path / "sha256").mkdir()
    (tmp_path / "sha256" / address).write_bytes(b"wrong")
    monkeypatch.setattr("ranex.provisioning.store.os.replace", lambda *_: (_ for _ in ()).throw(OSError("denied")))
    with pytest.raises(StoreError, match="cannot quarantine"):
        WheelStore(tmp_path).verified_path(address)


@pytest.mark.parametrize("glibc", ["glibc x.y", "musl 1.2"])
def test_platforms_fall_back_when_glibc_is_unusable(glibc: str) -> None:
    # Input: probe reports malformed or non-glibc libc data.
    assert _platforms("x86_64", glibc) == ("linux_x86_64",)


def unseal(root: Path) -> None:
    """Restore write bits under `root` so the fixture can be removed.

    Anything that calls the real `assemble_root` inherits its seal. Left in
    place, pytest cannot delete the directory and the debris breaks the NEXT
    run's cleanup — the same failure the `_seal` test above was written to
    avoid, met a second time from the other direction.
    """

    if not root.exists():
        return
    for parent, directories, files in os.walk(root, topdown=True):
        for name in (*directories, *files):
            path = Path(parent, name)
            if not path.is_symlink():
                path.chmod(stat.S_IMODE(path.lstat().st_mode) | 0o700)
    root.chmod(stat.S_IMODE(root.lstat().st_mode) | 0o700)


def script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "tool"
    path.write_text("#!/bin/sh\n" + body + "\n")
    path.chmod(0o755)
    return path


def test_probe_target_refuses_missing_interpreter(tmp_path: Path) -> None:
    # Input: pinned interpreter path does not exist.
    with pytest.raises(TargetError, match="cannot run pinned interpreter"):
        probe_target(tmp_path / "missing")


def test_probe_target_refuses_nonzero_interpreter(tmp_path: Path) -> None:
    # Input: interpreter script exits nonzero.
    with pytest.raises(TargetError, match="cannot describe itself"):
        probe_target(script(tmp_path, "exit 1"))


def test_probe_target_refuses_malformed_json(tmp_path: Path) -> None:
    # Input: interpreter script emits non-JSON output.
    with pytest.raises(TargetError, match="malformed probe output"):
        probe_target(script(tmp_path, "echo not-json"))


def test_probe_target_refuses_short_version(tmp_path: Path) -> None:
    # Input: probe JSON reports a one-element python_version.
    body = "echo '{\"python_version\":[3],\"markers\":{},\"machine\":\"x\",\"implementation_name\":\"cpython\"}'"
    with pytest.raises(TargetError, match="reported no version"):
        probe_target(script(tmp_path, body))


def test_probe_target_refuses_non_string_markers(tmp_path: Path) -> None:
    # Input: probe JSON includes an integer marker value.
    body = "echo '{\"python_version\":[3,12],\"markers\":{\"python_version\":3},\"machine\":\"x\",\"implementation_name\":\"cpython\"}'"
    with pytest.raises(TargetError, match="malformed markers"):
        probe_target(script(tmp_path, body))


class Response:
    def __init__(self, data: bytes) -> None: self.data = data
    def __enter__(self) -> Response: return self
    def __exit__(self, *_: object) -> None: return None
    def read(self) -> bytes: return self.data


def artifact(data: bytes = b"wheel", url: str = "https://files.example/a.whl") -> WheelArtifact:
    return WheelArtifact("pkg", "1", "a.whl", url, digest(data))


def test_ensure_wheels_reuses_verified_entry_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: matching wheel is already published in the store.
    item = artifact(); store = WheelStore(tmp_path); store.publish(item.sha256, b"wheel")
    monkeypatch.setattr("ranex.provisioning.fetching.urllib.request.urlopen", lambda *_1, **_2: (_ for _ in ()).throw(AssertionError()))
    assert ensure_wheels([item], store).downloaded == ()
    assert ensure_wheels([item], store).reused == ("pkg",)


def test_ensure_wheels_refuses_unsupported_scheme(tmp_path: Path) -> None:
    # Input: wheel URL uses file scheme.
    with pytest.raises(FetchError, match="pkg.*unsupported url scheme"):
        ensure_wheels([artifact(url="file:///x.whl")], WheelStore(tmp_path))


def test_ensure_wheels_refuses_download_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: urlopen raises URLError.
    item = artifact()
    monkeypatch.setattr("ranex.provisioning.fetching.urllib.request.urlopen", lambda *_1, **_2: (_ for _ in ()).throw(URLError("no")))
    with pytest.raises(FetchError, match="pkg.*files.example"):
        ensure_wheels([item], WheelStore(tmp_path))


def test_ensure_wheels_refuses_digest_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: download bytes differ from the declared digest.
    item = artifact(b"expected")
    monkeypatch.setattr("ranex.provisioning.fetching.urllib.request.urlopen", lambda *_1, **_2: Response(b"other"))
    with pytest.raises(FetchError, match="pkg.*sha256"):
        ensure_wheels([item], WheelStore(tmp_path))
    with pytest.raises(StoreError, match="absent"):
        WheelStore(tmp_path).verified_path(item.sha256)


def test_ensure_wheels_downloads_and_publishes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Input: download bytes match the declared digest.
    item = artifact(b"right"); store = WheelStore(tmp_path)
    monkeypatch.setattr("ranex.provisioning.fetching.urllib.request.urlopen", lambda *_1, **_2: Response(b"right"))
    assert ensure_wheels([item], store).downloaded == ("pkg",)
    assert store.verified_path(item.sha256).read_bytes() == b"right"


def test_load_pins_refuses_non_mapping_top_level_field() -> None:
    # Input: resolver top-level field is an integer.
    with pytest.raises(PinsError, match="resolver"):
        load_pins_text("resolver: 5")


def test_load_pins_refuses_unparseable_yaml() -> None:
    # Input: a document the YAML parser itself rejects.
    with pytest.raises(PinsError, match="cannot parse pins YAML"):
        load_pins_text("resolver: [unclosed")


def test_verified_binary_refuses_malformed_expected_digest(tmp_path: Path) -> None:
    # Input: expected resolver digest is malformed.
    with pytest.raises(PinsError, match="malformed expected sha256"):
        verified_pinned_binary(tmp_path / "x", "bad")


def test_verified_binary_refuses_directory(tmp_path: Path) -> None:
    # Input: pinned resolver path is a directory.
    with pytest.raises(PinsError, match="not a regular file"):
        verified_pinned_binary(tmp_path, "a" * 64, require_unwritable=False)


def test_refuse_writable_interpreter(tmp_path: Path) -> None:
    # Input: interpreter file is owned by this user and mode 0700.
    binary = tmp_path / "python"; binary.write_bytes(b"x"); binary.chmod(0o700)
    with pytest.raises(PinsError, match="writable"):
        refuse_writable_interpreter(binary)


def test_verified_wheel_paths_refuses_missing_store_entry(tmp_path: Path) -> None:
    # Input: selected package has no store entry.
    with pytest.raises(RootError, match="pkg 1.*not available"):
        verified_wheel_paths([artifact()], WheelStore(tmp_path))


def test_seal_removes_write_bits_and_skips_symlink(tmp_path: Path) -> None:
    # Input: tree contains writable directory/file and a symlink.
    root = tmp_path / "tree"
    nested = root / "nested"
    nested.mkdir(parents=True)
    file = nested / "file"
    file.write_text("x")
    link = root / "link"
    link.symlink_to(file)
    try:
        _seal(root)
        assert not stat.S_IMODE(root.stat().st_mode) & 0o222
        assert not stat.S_IMODE(nested.stat().st_mode) & 0o222
        assert not stat.S_IMODE(file.stat().st_mode) & 0o222
        # Skipped, not chmod'ed: on Linux a symlink is always 0777 to lstat
        # and chmod on one raises, so sealing it would refuse every real
        # environment while proving nothing.
        assert link.is_symlink()
    finally:
        # Unconditional. Left sealed, this fixture is unremovable by pytest,
        # and its leftovers then break the NEXT run's garbage collection —
        # which is how this test failed in-file while passing alone.
        for path, mode in ((root, 0o755), (nested, 0o755), (file, 0o644)):
            path.chmod(mode)


def test_refuse_mismatch_accepts_equal_bytes() -> None:
    # Input: committed and derived bytes are identical.
    assert refuse_mismatch(b"one\n", b"one\n") is None


def test_refuse_mismatch_names_first_divergent_line() -> None:
    # Input: second text line differs.
    with pytest.raises(DerivationError, match="first divergence at line 2"):
        refuse_mismatch(b"one\ntwo\n", b"one\nthree\n")


def test_refuse_mismatch_names_length_difference() -> None:
    # Input: line counts differ after an identical prefix.
    with pytest.raises(DerivationError, match="files differ in length"):
        refuse_mismatch(b"one\n", b"one\ntwo\n")


def pins_for(script_path: Path) -> ResolutionPins:
    return ResolutionPins(script_path, "a" * 64, Path("/usr/bin/python3"), ("https://example.test/simple",), "2026-01-01")


def test_derive_lock_refuses_nonzero_resolver(tmp_path: Path) -> None:
    # Input: pinned resolver script exits 1.
    resolver = script(tmp_path, "exit 1"); descriptor = os.open(resolver, os.O_RDONLY)
    try:
        with pytest.raises(DerivationError, match="clean resolution failed"):
            derive_lock(b"[project]\nname='x'\nversion='1'\n", pins_for(resolver), descriptor, tmp_path / "scratch")
    finally:
        os.close(descriptor)


def test_derive_lock_refuses_success_without_lock(tmp_path: Path) -> None:
    # Input: pinned resolver script exits 0 without writing uv.lock.
    resolver = script(tmp_path, "exit 0"); descriptor = os.open(resolver, os.O_RDONLY)
    try:
        with pytest.raises(DerivationError, match="wrote no lock"):
            derive_lock(b"[project]\nname='x'\nversion='1'\n", pins_for(resolver), descriptor, tmp_path / "scratch")
    finally:
        os.close(descriptor)


# --------------------------------------------------------------------------
# The branches the first pass left uncovered. Each is a real path, not a
# defensive one: a branch no input can reach is decoration, and the one such
# guard found here was deleted from lockfile.py rather than tested around.
# --------------------------------------------------------------------------


def test_resolve_edge_selects_the_single_marker_match() -> None:
    # Input: a name locked twice, an edge without a version, and exactly one
    # entry whose resolution-markers hold for this target. The happy half of
    # the ambiguity rule — the refusals for zero and two matches are above.
    old = Package(
        "dual", "1.0", {"registry": "https://example.test"}, (), {}, (), False,
        ("python_full_version >= '3.14'",),
    )
    new = Package(
        "dual", "2.0", {"registry": "https://example.test"}, (), {}, (), False,
        ("python_full_version < '3.14'",),
    )
    chosen = _resolve_edge(Lock((old, new)), Dependency("dual", None), TARGET)
    assert chosen.version == "2.0"


def test_select_wheels_visits_a_shared_dependency_once() -> None:
    # Input: a diamond — two packages depending on the same third. The shared
    # package must be selected once, not twice.
    body = (
        package("root", extra='dependencies = [{ name = "left" }, { name = "right" }]')
        + package("left", extra=f'dependencies = [{{ name = "shared" }}]\nwheels = [{wheel("left")}]')
        + package("right", extra=f'dependencies = [{{ name = "shared" }}]\nwheels = [{wheel("right")}]')
        + package("shared", extra=f"wheels = [{wheel('shared')}]")
    )
    selected = select_wheels(parse_lock(lock_text(packages=body)), "root", TARGET)
    names = [item.package for item in selected]
    assert names.count("shared") == 1
    assert sorted(names) == ["left", "right", "shared"]


def test_pins_refuse_an_empty_path_string() -> None:
    # Input: resolver.path present but empty — absence wearing a value.
    text = (
        "resolver:\n  path: ''\n  sha256: " + "a" * 64 + "\n"
        "python:\n  path: /usr/bin/python3\n"
        "indexes:\n  - https://example.test/simple\n"
        'exclude_newer: "2026-01-01"\n'
    )
    with pytest.raises(PinsError, match="absolute path"):
        load_pins_text(text)


def test_derive_lock_passes_every_extra_index(tmp_path: Path) -> None:
    # Input: pins naming two indexes. The second must reach the resolver as
    # --extra-index-url, or a package served only there silently disappears.
    # The log path is relative to the resolver's cwd, which derive_lock sets
    # to <scratch>/derive. It cannot come from the environment: derive_lock
    # hands the resolver a built-from-empty env on purpose, and a test that
    # smuggled a variable through it would be testing a different function.
    resolver = script(tmp_path, 'printf "%s\\n" "$@" > ../argv.log\ntouch uv.lock\nexit 0')
    scratch = tmp_path / "scratch"
    pins = ResolutionPins(
        resolver, "a" * 64, Path("/usr/bin/python3"),
        ("https://one.test/simple", "https://two.test/simple"), "2026-01-01",
    )
    descriptor = os.open(resolver, os.O_RDONLY)
    try:
        derive_lock(b"[project]\n", pins, descriptor, scratch)
    finally:
        os.close(descriptor)
    recorded = (scratch / "argv.log").read_text().split("\n")
    assert "--index-url" in recorded and "https://one.test/simple" in recorded
    assert "--extra-index-url" in recorded and "https://two.test/simple" in recorded


def test_derive_lock_refuses_an_unspawnable_resolver(tmp_path: Path) -> None:
    # Input: a descriptor for a file that is not executable, so the spawn
    # itself fails rather than the resolution.
    plain = tmp_path / "not-a-program"
    plain.write_text("data\n")
    plain.chmod(0o600)
    descriptor = os.open(plain, os.O_RDONLY)
    try:
        with pytest.raises(DerivationError, match="cannot run the pinned resolver"):
            derive_lock(b"[project]\n", pins_for(plain), descriptor, tmp_path / "scratch")
    finally:
        os.close(descriptor)


def test_store_publish_tolerates_a_vanished_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Input: the rename fails AND the temporary is already gone. Cleanup must
    # not replace the StoreError with a FileNotFoundError from its own tidy-up.
    store = WheelStore(tmp_path / "store")
    payload = b"wheel-bytes"

    def replace(source, _destination):
        os.unlink(source)
        raise OSError("rename refused")

    monkeypatch.setattr("ranex.provisioning.store.os.replace", replace)
    with pytest.raises(StoreError, match="cannot publish"):
        store.publish(digest(payload), payload)
    assert not list((tmp_path / "store" / "tmp").iterdir())


def test_assemble_root_refuses_a_failing_environment_builder(tmp_path: Path) -> None:
    # Input: the pinned resolver fails while creating the environment. The
    # refusal must carry the resolver's own stderr, or an operator is left
    # guessing which of two resolver calls broke.
    from ranex.provisioning.root import assemble_root

    resolver = script(tmp_path, 'echo "venv refused" >&2\nexit 1')
    descriptor = os.open(resolver, os.O_RDONLY)
    try:
        with pytest.raises(RootError, match="cannot create the dependency environment"):
            assemble_root((), WheelStore(tmp_path / "store"), pins_for(resolver),
                          descriptor, tmp_path / "root")
    finally:
        os.close(descriptor)


def test_assemble_root_refuses_a_failing_installer(tmp_path: Path) -> None:
    # Input: the environment is created but installing the verified wheels
    # fails. Reached only when there is at least one wheel, so the empty-set
    # shortcut cannot hide it.
    from ranex.provisioning.root import assemble_root

    store = WheelStore(tmp_path / "store")
    payload = b"wheel"
    store.publish(digest(payload), payload)
    item = WheelArtifact("pkg", "1", "pkg-1-py3-none-any.whl",
                         "https://files.example/pkg-1-py3-none-any.whl", digest(payload))
    resolver = script(tmp_path, 'case "$1" in venv) exit 0 ;; esac\necho "install refused" >&2\nexit 1')
    descriptor = os.open(resolver, os.O_RDONLY)
    try:
        with pytest.raises(RootError, match="cannot install the verified wheels"):
            assemble_root((item,), store, pins_for(resolver), descriptor, tmp_path / "root")
    finally:
        os.close(descriptor)


def test_assemble_root_copies_when_hard_linking_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Input: os.link fails, as it does across filesystems. The verified bytes
    # must still reach the staging name — by copy, never by skipping the wheel.
    from ranex.provisioning import root as root_module

    store = WheelStore(tmp_path / "store")
    payload = b"wheel"
    store.publish(digest(payload), payload)
    item = WheelArtifact("pkg", "1", "pkg-1-py3-none-any.whl",
                         "https://files.example/pkg-1-py3-none-any.whl", digest(payload))
    monkeypatch.setattr(
        root_module.os, "link",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("cross-device link")),
    )
    # Stands in for the resolver: `venv` creates the directory it is asked
    # for — the seal walks it afterwards — and `pip install` is a no-op,
    # because what this test asserts is the staged bytes, not the install.
    resolver = script(
        tmp_path,
        'if [ "$1" = "venv" ]; then\n'
        '  for last in "$@"; do :; done\n'
        '  mkdir -p "$last/bin"\n'
        "fi\n"
        "exit 0",
    )
    descriptor = os.open(resolver, os.O_RDONLY)
    destination = tmp_path / "root"
    try:
        root_module.assemble_root((item,), store, pins_for(resolver), descriptor, destination)
        staged = destination / "wheels" / item.filename
        assert staged.read_bytes() == payload
    finally:
        os.close(descriptor)
        # assemble_root SEALS what it builds, and a sealed tree is one pytest
        # cannot remove — its leftovers then break the next run's garbage
        # collection. Production does not need this: the whole materialisation
        # is torn down by `_remove_materialisation`, which restores write bits
        # for exactly this reason. A test calling the real thing has to do the
        # same job itself.
        unseal(destination)


def test_assemble_root_refuses_an_unspawnable_resolver(tmp_path: Path) -> None:
    # Input: a descriptor for a file that is not executable, so the resolver
    # spawn fails rather than the resolver.
    from ranex.provisioning.root import assemble_root

    plain = tmp_path / "not-a-program"
    plain.write_text("data\n")
    plain.chmod(0o600)
    descriptor = os.open(plain, os.O_RDONLY)
    try:
        with pytest.raises(RootError, match="cannot create the dependency environment"):
            assemble_root((), WheelStore(tmp_path / "store"), pins_for(plain),
                          descriptor, tmp_path / "root")
    finally:
        os.close(descriptor)


def test_deny_network_requests_a_fresh_user_and_network_namespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The flags are the whole control: CLONE_NEWNET is what leaves the child
    # with no interfaces, and CLONE_NEWUSER is what lets an unprivileged
    # process ask for it at all. Asserted against a fake because calling the
    # real one would unshare THIS process — the child actually being unable
    # to reach the network is proven separately, end to end, by
    # tests/security/test_slice006_dependency_provisioning.py.
    from ranex.cli import main as cli

    requested: list[int] = []
    monkeypatch.setattr(cli.os, "unshare", requested.append)
    cli._deny_network()
    assert requested == [os.CLONE_NEWUSER | os.CLONE_NEWNET]
