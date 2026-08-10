"""SLICE-006 — the pure core of dependency provisioning.

These tests are the frozen target for `ranex.provisioning`. They cover the
parts that need no subprocess and no network: operator pins, lock parsing and
wheel selection, the SHA-256 store, and the approval delta. ADR-007 sad paths
are cited per test.

Committed red before any implementation exists, per the working rule.
"""

from __future__ import annotations

import hashlib
import os
import stat
import threading
from pathlib import Path

import pytest

from ranex.provisioning.approval import DepsDelta, depset_digest, package_delta
from ranex.provisioning.lockfile import (
    LockError,
    TargetEnvironment,
    parse_lock,
    select_wheels,
)
from ranex.provisioning.pins import PinsError, load_pins_text, verified_pinned_binary
from ranex.provisioning.store import StoreError, WheelStore

# --------------------------------------------------------------------------
# Fixtures: a small, honest uv.lock and a target environment to select for.
# --------------------------------------------------------------------------

TARGET = TargetEnvironment(
    implementation="cp",
    python_version=(3, 12),
    platforms=("manylinux_2_17_x86_64", "linux_x86_64"),
    marker_environment={
        "python_version": "3.12",
        "python_full_version": "3.12.3",
        "implementation_name": "cpython",
        "platform_system": "Linux",
        "platform_machine": "x86_64",
        "sys_platform": "linux",
        "os_name": "posix",
        "platform_python_implementation": "CPython",
        "extra": "",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


WHEEL_ALPHA = b"alpha-wheel-bytes"
WHEEL_BETA = b"beta-wheel-bytes"


def lock_text(
    *,
    alpha_wheel: str = "alpha-1.0.0-py3-none-any.whl",
    alpha_hash: str | None = None,
    alpha_source: str = 'source = { registry = "https://pypi.org/simple" }',
    include_beta: bool = True,
    beta_marker: str = "",
) -> str:
    """A minimal uv.lock shape: virtual root `demo` -> alpha -> (beta)."""

    alpha_digest = alpha_hash if alpha_hash is not None else sha256(WHEEL_ALPHA)
    beta_digest = sha256(WHEEL_BETA)
    beta_dependency = (
        f'dependencies = [{{ name = "beta"{beta_marker} }}]' if include_beta else ""
    )
    beta_package = (
        f'''
[[package]]
name = "beta"
version = "2.0.0"
source = {{ registry = "https://pypi.org/simple" }}
wheels = [
    {{ url = "https://files.example/beta-2.0.0-py3-none-any.whl", hash = "sha256:{beta_digest}" }},
]
'''
        if include_beta
        else ""
    )
    return f'''version = 1
revision = 3
requires-python = ">=3.11, <3.15"

[options]
exclude-newer = "2026-08-04T00:00:00Z"

[[package]]
name = "alpha"
version = "1.0.0"
{alpha_source}
{beta_dependency}
wheels = [
    {{ url = "https://files.example/{alpha_wheel}", hash = "sha256:{alpha_digest}" }},
]
{beta_package}
[[package]]
name = "demo"
version = "0.0.0"
source = {{ virtual = "." }}
dependencies = [
    {{ name = "alpha" }},
]
'''


# --------------------------------------------------------------------------
# Operator pins. (ADR-007 sad path 4)
# --------------------------------------------------------------------------

PINS = """\
resolver:
  path: /opt/pinned/uv
  sha256: {resolver_digest}
python:
  path: /usr/bin/python3.12
indexes:
  - https://pypi.org/simple
exclude_newer: "2026-08-04T00:00:00Z"
"""


class TestPins:
    def test_complete_pins_parse(self) -> None:
        pins = load_pins_text(PINS.format(resolver_digest="a" * 64))
        assert pins.resolver == Path("/opt/pinned/uv")
        assert pins.resolver_sha256 == "a" * 64
        assert pins.python == Path("/usr/bin/python3.12")
        assert pins.indexes == ("https://pypi.org/simple",)
        assert pins.exclude_newer == "2026-08-04T00:00:00Z"

    @pytest.mark.parametrize(
        "field",
        ["resolver:", "python:", "indexes:", "exclude_newer:"],
    )
    def test_absent_field_refuses(self, field: str) -> None:
        # s.p. 4: an unpinned input refuses before any network access. Absence
        # blocks; nothing defaults.
        #
        # The field's indented children go with it. Dropping only the key line
        # left them orphaned, so YAML failed to parse and two of these cases
        # were proving that corruption refuses — not that absence does. The
        # document handed to the parser here is valid YAML that is simply
        # missing one pin.
        kept: list[str] = []
        skipping = False
        for line in PINS.format(resolver_digest="a" * 64).splitlines():
            if line.startswith(field):
                skipping = True
                continue
            if skipping and line[:1] in (" ", "\t"):
                continue
            skipping = False
            kept.append(line)
        text = "\n".join(kept)
        with pytest.raises(PinsError, match=r"must be"):
            load_pins_text(text)

    def test_resolver_without_digest_refuses(self) -> None:
        text = PINS.format(resolver_digest="a" * 64).replace(
            "  sha256: " + "a" * 64 + "\n", ""
        )
        with pytest.raises(PinsError, match="sha256"):
            load_pins_text(text)

    def test_malformed_digest_refuses(self) -> None:
        with pytest.raises(PinsError, match=r"malformed|hex"):
            load_pins_text(PINS.format(resolver_digest="zz"))

    def test_empty_indexes_refuse(self) -> None:
        text = PINS.format(resolver_digest="a" * 64).replace(
            "indexes:\n  - https://pypi.org/simple", "indexes: []"
        )
        with pytest.raises(PinsError, match=r"indexes"):
            load_pins_text(text)

    def test_relative_resolver_path_refuses(self) -> None:
        text = PINS.format(resolver_digest="a" * 64).replace(
            "/opt/pinned/uv", "bin/uv"
        )
        with pytest.raises(PinsError, match=r"absolute"):
            load_pins_text(text)

    def test_verified_binary_accepts_matching_bytes(self, tmp_path: Path) -> None:
        binary = tmp_path / "uv"
        binary.write_bytes(b"resolver-bytes")
        binary.chmod(0o500)
        # The writability rule is the toolchain's and is exercised in the
        # security tests; here the digest half is proven on its own by a
        # non-user-writable fixture.
        descriptor = verified_pinned_binary(
            binary, sha256(b"resolver-bytes"), require_unwritable=False
        )
        try:
            # The descriptor is the verified artifact: what it reads is what
            # was hashed, however the name is edited afterwards.
            with open(descriptor, "rb", closefd=False) as handle:
                assert handle.read() == b"resolver-bytes"
        finally:
            os.close(descriptor)

    def test_verified_binary_refuses_changed_bytes(self, tmp_path: Path) -> None:
        # The slice's third decoration risk: an exact path without a digest
        # check is still agent-selected. Replaced bytes must refuse.
        binary = tmp_path / "uv"
        binary.write_bytes(b"not-the-pinned-resolver")
        binary.chmod(0o500)
        with pytest.raises(PinsError, match="sha256"):
            verified_pinned_binary(
                binary, sha256(b"resolver-bytes"), require_unwritable=False
            )

    def test_verified_binary_refuses_absence(self, tmp_path: Path) -> None:
        with pytest.raises(PinsError, match=r"cannot open|absent|No such"):
            verified_pinned_binary(
                tmp_path / "missing", sha256(b"x"), require_unwritable=False
            )

    def test_verified_binary_refuses_user_writable(self, tmp_path: Path) -> None:
        # s.p. 4 / done criterion 3: a user-writable resolver refuses under
        # the default rule, exactly as the pinned toolchain refuses one.
        binary = tmp_path / "uv"
        binary.write_bytes(b"resolver-bytes")
        binary.chmod(0o700)
        with pytest.raises(PinsError, match="writable"):
            verified_pinned_binary(binary, sha256(b"resolver-bytes"))


# --------------------------------------------------------------------------
# Lock parsing and wheel selection. (ADR-007 sad paths 6, 7, 11)
# --------------------------------------------------------------------------


class TestWheelSelection:
    def test_honest_lock_selects_the_closure(self) -> None:
        lock = parse_lock(lock_text().encode())
        selected = select_wheels(lock, "demo", TARGET)
        names = {wheel.package for wheel in selected}
        assert names == {"alpha", "beta"}
        by_name = {wheel.package: wheel for wheel in selected}
        assert by_name["alpha"].sha256 == sha256(WHEEL_ALPHA)
        assert by_name["alpha"].filename == "alpha-1.0.0-py3-none-any.whl"
        assert by_name["beta"].version == "2.0.0"

    def test_selection_is_a_closure_not_a_listing(self) -> None:
        # A package the graph never reaches from the root must not be
        # provisioned: selection walks edges, it does not enumerate the file.
        orphan = (
            lock_text()
            + f'''
[[package]]
name = "orphan"
version = "9.9.9"
source = {{ registry = "https://pypi.org/simple" }}
wheels = [
    {{ url = "https://files.example/orphan-9.9.9-py3-none-any.whl", hash = "sha256:{sha256(b'orphan')}" }},
]
'''
        )
        selected = select_wheels(parse_lock(orphan.encode()), "demo", TARGET)
        assert {wheel.package for wheel in selected} == {"alpha", "beta"}

    def test_false_marker_prunes_the_edge(self) -> None:
        pruned = lock_text(beta_marker=', marker = "python_version < \'3.0\'"')
        selected = select_wheels(parse_lock(pruned.encode()), "demo", TARGET)
        assert {wheel.package for wheel in selected} == {"alpha"}

    def test_missing_sha256_refuses_naming_the_package(self) -> None:
        # s.p. 7: uv's absence-permits default is not inherited.
        text = lock_text().replace(
            f'hash = "sha256:{sha256(WHEEL_ALPHA)}"', 'hash = ""'
        )
        with pytest.raises(LockError, match="alpha"):
            select_wheels(parse_lock(text.encode()), "demo", TARGET)

    def test_vcs_source_refuses(self) -> None:
        # s.p. 6: nothing that would execute during provisioning may enter.
        text = lock_text(
            alpha_source='source = { git = "https://github.com/x/alpha?rev=abc123" }'
        )
        with pytest.raises(LockError, match="alpha"):
            select_wheels(parse_lock(text.encode()), "demo", TARGET)

    def test_local_path_source_refuses(self) -> None:
        text = lock_text(alpha_source='source = { path = "../alpha" }')
        with pytest.raises(LockError, match="alpha"):
            select_wheels(parse_lock(text.encode()), "demo", TARGET)

    def test_sdist_only_package_refuses(self) -> None:
        # s.p. 6: an sdist is code that runs at build time, and the lock
        # offering only one means the platform cannot be served by wheels.
        text = lock_text().replace(
            f'''wheels = [
    {{ url = "https://files.example/beta-2.0.0-py3-none-any.whl", hash = "sha256:{sha256(WHEEL_BETA)}" }},
]''',
            f'sdist = {{ url = "https://files.example/beta-2.0.0.tar.gz", hash = "sha256:{sha256(b"beta-sdist")}" }}',
        )
        with pytest.raises(LockError, match="beta"):
            select_wheels(parse_lock(text.encode()), "demo", TARGET)

    def test_incompatible_platform_refuses_naming_package_and_target(self) -> None:
        # s.p. 11: refusal names package, version and target.
        text = lock_text(alpha_wheel="alpha-1.0.0-cp312-cp312-win_amd64.whl")
        with pytest.raises(LockError) as caught:
            select_wheels(parse_lock(text.encode()), "demo", TARGET)
        message = str(caught.value)
        assert "alpha" in message
        assert "1.0.0" in message
        assert "manylinux_2_17_x86_64" in message

    def test_most_specific_compatible_wheel_wins(self) -> None:
        # Between a universal and a platform wheel, the platform wheel is the
        # one uv would install; provisioning must fetch the same bytes.
        platform_bytes = b"alpha-manylinux-bytes"
        text = lock_text().replace(
            f'wheels = [\n    {{ url = "https://files.example/alpha-1.0.0-py3-none-any.whl", hash = "sha256:{sha256(WHEEL_ALPHA)}" }},\n]',
            f'''wheels = [
    {{ url = "https://files.example/alpha-1.0.0-py3-none-any.whl", hash = "sha256:{sha256(WHEEL_ALPHA)}" }},
    {{ url = "https://files.example/alpha-1.0.0-cp312-cp312-manylinux_2_17_x86_64.whl", hash = "sha256:{sha256(platform_bytes)}" }},
]''',
        )
        selected = select_wheels(parse_lock(text.encode()), "demo", TARGET)
        by_name = {wheel.package: wheel for wheel in selected}
        assert by_name["alpha"].sha256 == sha256(platform_bytes)

    def test_absent_root_refuses(self) -> None:
        with pytest.raises(LockError, match="demo"):
            select_wheels(parse_lock(lock_text().encode()), "absent", TARGET)

    def test_unparseable_lock_refuses(self) -> None:
        with pytest.raises(LockError, match=r"cannot parse lockfile"):
            parse_lock(b"version = ???")


# --------------------------------------------------------------------------
# The SHA-256 store. (ADR-007 sad paths 8, 9, 10)
# --------------------------------------------------------------------------


class TestWheelStore:
    def test_publish_then_read_round_trips(self, tmp_path: Path) -> None:
        store = WheelStore(tmp_path / "store")
        digest = sha256(WHEEL_ALPHA)
        store.publish(digest, WHEEL_ALPHA)
        assert store.verified_path(digest).read_bytes() == WHEEL_ALPHA

    def test_publish_refuses_bytes_missing_their_digest(self, tmp_path: Path) -> None:
        # s.p. 8: a downloaded wheel that misses its declared digest is
        # refused, and nothing is published under that address.
        store = WheelStore(tmp_path / "store")
        digest = sha256(WHEEL_ALPHA)
        with pytest.raises(StoreError, match=r"do not match"):
            store.publish(digest, b"other-bytes")
        with pytest.raises(StoreError, match=r"absent"):
            store.verified_path(digest)

    def test_read_rehashes_and_quarantines_corruption(self, tmp_path: Path) -> None:
        # s.p. 9: every read re-hashes; corruption is contained, not returned.
        store = WheelStore(tmp_path / "store")
        digest = sha256(WHEEL_ALPHA)
        store.publish(digest, WHEEL_ALPHA)
        entry = store.verified_path(digest)
        entry.chmod(0o600)
        entry.write_bytes(b"corrupted")
        with pytest.raises(StoreError, match="quarantine"):
            store.verified_path(digest)
        # The corrupt bytes are out of the addressable namespace entirely: a
        # second read is a miss, not a second serving of the corruption.
        with pytest.raises(StoreError, match=r"absent"):
            store.verified_path(digest)

    def test_missing_entry_is_a_refusal_not_none(self, tmp_path: Path) -> None:
        store = WheelStore(tmp_path / "store")
        with pytest.raises(StoreError, match=r"is not 64|absent"):
            store.verified_path(sha256(b"never-published"))

    def test_concurrent_publishers_expose_one_complete_entry(
        self, tmp_path: Path
    ) -> None:
        # s.p. 10: two writers, one atomic outcome, never partial bytes.
        store = WheelStore(tmp_path / "store")
        digest = sha256(WHEEL_ALPHA)
        barrier = threading.Barrier(2)
        failures: list[Exception] = []

        def publish() -> None:
            barrier.wait()
            try:
                store.publish(digest, WHEEL_ALPHA)
            except Exception as exc:  # pragma: no cover - failure is the report
                failures.append(exc)

        threads = [threading.Thread(target=publish) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert not failures
        assert store.verified_path(digest).read_bytes() == WHEEL_ALPHA

    def test_entries_are_not_published_writable(self, tmp_path: Path) -> None:
        store = WheelStore(tmp_path / "store")
        digest = sha256(WHEEL_ALPHA)
        store.publish(digest, WHEEL_ALPHA)
        mode = stat.S_IMODE(store.verified_path(digest).stat().st_mode)
        assert not mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)


# --------------------------------------------------------------------------
# The approval delta. (ADR-007 sad path 15; done criterion 9)
# --------------------------------------------------------------------------


class TestApprovalDelta:
    def test_no_baseline_shows_the_full_set(self) -> None:
        # s.p. 15: absence of a prior approval is explicit, never empty.
        delta = package_delta(None, {"alpha": "1.0.0", "beta": "2.0.0"})
        assert delta.baseline_exists is False
        assert delta.added == (("alpha", "1.0.0"), ("beta", "2.0.0"))
        assert delta.removed == ()
        assert delta.changed == ()

    def test_delta_names_added_removed_and_changed(self) -> None:
        delta = package_delta(
            {"alpha": "1.0.0", "gone": "3.0.0"},
            {"alpha": "1.0.1", "new": "0.1.0"},
        )
        assert delta.baseline_exists is True
        assert delta.added == (("new", "0.1.0"),)
        assert delta.removed == (("gone", "3.0.0"),)
        assert delta.changed == (("alpha", "1.0.0", "1.0.1"),)

    def test_unchanged_set_is_an_empty_delta(self) -> None:
        delta = package_delta({"alpha": "1.0.0"}, {"alpha": "1.0.0"})
        assert delta == DepsDelta(
            baseline_exists=True, added=(), removed=(), changed=()
        )

    def test_depset_digest_binds_lock_and_target(self) -> None:
        # Done criterion 10: the identity covers the lock bytes and the
        # target; either changing changes the identity.
        lock = lock_text().encode()
        base = depset_digest(lock, TARGET)
        assert base == depset_digest(lock, TARGET)
        assert base != depset_digest(lock + b"\n", TARGET)
        other = TargetEnvironment(
            implementation="cp",
            python_version=(3, 13),
            platforms=TARGET.platforms,
            marker_environment=dict(TARGET.marker_environment),
        )
        assert base != depset_digest(lock, other)
        assert base.startswith("sha256:")
