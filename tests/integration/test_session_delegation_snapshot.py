"""Admission observes restored delegation, and still refuses real drift."""

from contextlib import contextmanager
from pathlib import Path

import pytest

from ranex.cli import host_confinement as host
from ranex.foundation.canonical import canonical_json_bytes


@pytest.mark.parametrize("permanent_drift", [False, True])
def test_session_waits_for_qualification_topology_before_comparing_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, permanent_drift: bool,
) -> None:
    qualification = {
        "schema": "ranex-strict-local-qualification-v1",
        "qualified": True,
        "host_state": {
            "boot_id": "fixture", "machine_id": "fixture",
            "lsm": {"securityfs_lsm": "fixture"},
            "unprivileged_userns_sysctls": {"fixture": 1},
            "delegation_identity": {
                "cgroup_root": "/sys/fs/cgroup/scope",
                "cgroup_relative_path": "/scope",
            },
        },
        "primitives": {
            "landlock": {"abi": 6, "available": True},
            "seccomp_filter": True, "no_new_privs": True, "openat2": True,
        },
    }
    (tmp_path / "qualification.json").write_bytes(canonical_json_bytes(qualification))
    (tmp_path / "runtime.json").write_bytes(canonical_json_bytes({"landlock_abi_minimum": 6}))
    probing = True

    @contextmanager
    def completed_probe():
        nonlocal probing
        # Acquiring the shared lock waits until qualification has restored
        # the scope. An unlocked read sees its temporary controller leaf.
        probing = False
        try:
            yield
        finally:
            probing = True

    def current_cgroup():
        relative = "/scope/controller" if probing else "/scope"
        if permanent_drift:
            relative = "/other-scope"
        return Path("/sys/fs/cgroup" + relative), relative

    class ReachedRuntimeValidation(Exception):
        pass

    def runtime_validation(*_args):
        raise ReachedRuntimeValidation

    def session_parent():
        assert not probing, "session parent read during qualification relocation"
        return Path("/sys/fs/cgroup/scope")

    monkeypatch.setattr(host, "_host_probe_lock", completed_probe)
    monkeypatch.setattr(host, "_current_cgroup_root", current_cgroup)
    monkeypatch.setattr(host, "_required_host_text", lambda *_: "fixture")
    monkeypatch.setattr(host, "_unprivileged_userns_sysctls", lambda: {"fixture": 1})
    monkeypatch.setattr(host, "_session_runtime_profile", lambda _: False)
    monkeypatch.setattr(host, "_probe_openat2", lambda: None)
    monkeypatch.setattr(host, "_session_cgroup_parent", session_parent)
    monkeypatch.setattr(host, "_validate_profile_and_objects", runtime_validation)
    expected = host.HostConfinementError if permanent_drift else ReachedRuntimeValidation
    with pytest.raises(expected) as failure:
        host.confinement_session(
            tmp_path, profile_arg="runtime.json", host_profile_arg="host.json",
            artifact_arg="launcher", manifest_arg="manifest.json",
            qualification_arg="qualification.json", descriptor={"_resolved": {}},
            result_arg="result.json",
        )
    if permanent_drift:
        assert failure.value.code == host.E_C18_HOST_DRIFT
    assert not (tmp_path / "result.json").exists()
