from dataclasses import FrozenInstanceError

import pytest

from ranex.foundation import platform


def test_x86_64_facts(monkeypatch):
    monkeypatch.setattr(platform.sys, "platform", "linux")
    monkeypatch.setattr(platform.platform, "machine", lambda: "x86_64")
    facts = platform.current()
    assert (facts.execveat, facts.keyctl, facts.openat2, facts.landlock_create_ruleset) == (322, 250, 437, 444)
    assert facts.target_triple == "x86_64-linux-gnu"
    assert facts.loader_name == "ld-linux-x86-64.so.2"
    assert facts.loader_path == "/lib64/ld-linux-x86-64.so.2"


def test_unsupported_machine(monkeypatch):
    monkeypatch.setattr(platform.sys, "platform", "linux")
    monkeypatch.setattr(platform.platform, "machine", lambda: "riscv64")
    with pytest.raises(platform.PlatformUnsupported, match="linux.*riscv64"):
        platform.current()


def test_table_is_frozen():
    with pytest.raises(TypeError):
        platform.PLATFORMS[("linux", "riscv64")] = platform.current()
    with pytest.raises(FrozenInstanceError):
        platform.current().execveat = 0
