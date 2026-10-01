import subprocess
from dataclasses import dataclass

import pytest

from ranex.foundation import settings as mod
from ranex.foundation.canonical import canonical_json


@pytest.fixture
def schema(monkeypatch):
    @dataclass(frozen=True)
    class Mechanics:
        count: int = mod.setting("count", 1, "mechanics", "Count")
        enabled: bool = mod.setting("enabled", False, "mechanics", "Enabled")
        access_token: object = mod.setting("access_token", {"env": "TEST_SECRET"}, "mechanics", "Secret")

    monkeypatch.setattr(mod, "SCHEMA", {"catalogs": mod.Catalogs, "test": Mechanics})


def write(root, text):
    path = root / "governance/settings.toml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text)
    return path


def load(root, **kwargs):
    return mod.load_settings(root, host_file=root / "absent-host", environ={}, **kwargs)


def test_defaults_missing_files(tmp_path):
    settings = load(tmp_path)
    assert settings.catalogs.gates == "governance/gates.yaml"
    assert len(settings.show()["catalogs"]) == 8
    assert settings.show()["catalogs"]["gates"]["source"] == "default"
    assert all(f["scope"] == "policy" for f in settings.show()["catalogs"].values())


def test_mechanics_precedence_and_merge(tmp_path, schema):
    write(tmp_path, '[test]\ncount = 2\nenabled = true\n[catalogs]\ngates = "repo"\n')
    host = tmp_path / "host.toml"
    host.write_text('[test]\ncount = 3\n')
    def resolve(env=None, cli=None):
        return mod.load_settings(tmp_path, host_file=host, environ=env or {}, cli_overrides=cli)
    assert load(tmp_path).get("test.count") == 2
    assert resolve().get("test.count") == 3
    assert resolve({"RANEX_TEST_COUNT": "4"}).get("test.count") == 4
    final = resolve({"RANEX_TEST_COUNT": "4"}, {"test.count": 5})
    assert final.get("test.count") == 5
    assert final.get("test.enabled") is True
    assert final.catalogs.gates == "repo"
    assert final.show()["test"]["count"]["source"] == "CLI"


@pytest.mark.parametrize("source", ["host", "env", "CLI"])
def test_policy_refusal(tmp_path, source):
    host = tmp_path / "host.toml"
    kwargs = {"host_file": host, "environ": {}}
    if source == "host":
        host.write_text('[catalogs]\ngates = "host"\n')
    elif source == "env":
        kwargs["environ"] = {"RANEX_CATALOGS_GATES": "env"}
    else:
        kwargs["cli_overrides"] = {"catalogs.gates": "cli"}
    with pytest.raises(mod.SettingsError, match="catalogs.gates") as error:
        mod.load_settings(tmp_path, **kwargs)
    assert {"host": str(host), "env": "RANEX_CATALOGS_GATES", "CLI": "CLI"}[source] in str(error.value)


@pytest.mark.parametrize("text,key", [('[catalogs]\nunknown = "x"', "catalogs.unknown"),
                                       ('[bogus]\nx = 1', "bogus"),
                                       ('[catalogs]\ngates = 1', "catalogs.gates")])
def test_file_errors(tmp_path, text, key):
    path = write(tmp_path, text)
    with pytest.raises(mod.SettingsError, match=key) as error:
        load(tmp_path)
    assert str(path) in str(error.value)


@pytest.mark.parametrize("value,expected", [("true", True), ("false", False)])
def test_bool_env(tmp_path, schema, value, expected):
    result = mod.load_settings(tmp_path, host_file=tmp_path / "missing", environ={"RANEX_TEST_ENABLED": value})
    assert result.get("test.enabled") is expected


@pytest.mark.parametrize("name,value", [("ENABLED", "True"), ("ENABLED", "1"), ("COUNT", "0x10"), ("COUNT", "1.0"), ("UNKNOWN", "x")])
def test_bad_env(tmp_path, schema, name, value):
    var = "RANEX_TEST_" + name
    with pytest.raises(mod.SettingsError, match=var):
        mod.load_settings(tmp_path, host_file=tmp_path / "missing", environ={var: value})


def test_int_env_and_wrong_bool_type(tmp_path, schema):
    result = mod.load_settings(tmp_path, host_file=tmp_path / "missing", environ={"RANEX_TEST_COUNT": "-012"})
    assert result.get("test.count") == -12
    write(tmp_path, '[test]\ncount = true\n')
    with pytest.raises(mod.SettingsError, match="test.count"):
        load(tmp_path)


def test_xdg_host(tmp_path, schema):
    path = tmp_path / "xdg/ranex/settings.toml"
    path.parent.mkdir(parents=True)
    path.write_text('[test]\ncount = 42\n')
    result = mod.load_settings(tmp_path, environ={"XDG_CONFIG_HOME": str(tmp_path / "xdg")})
    assert result.get("test.count") == 42


def test_evaluated_ref(tmp_path, schema):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True, text=True).stdout.strip()
    git("init")
    git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-m", "empty")
    empty = git("rev-parse", "HEAD")
    path = write(tmp_path, '[catalogs]\ngates = "committed"\n[test]\ncount = 2\n')
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-m", "settings")
    path.write_text('[catalogs]\ngates = "dirty"\n[test]\ncount = 3\n')
    assert load(tmp_path, evaluated_ref="HEAD").get("test.count") == 3
    assert load(tmp_path, evaluated_ref="HEAD").catalogs.gates == "committed"
    assert load(tmp_path, evaluated_ref=empty).catalogs.gates == "governance/gates.yaml"
    assert load(tmp_path).catalogs.gates == "dirty"
    with pytest.raises(mod.SettingsError, match="nonexistent"):
        load(tmp_path, evaluated_ref="nonexistent")


def test_digest(tmp_path, schema):
    first = mod.settings_digest(load(tmp_path))
    write(tmp_path, '[test]\ncount = 99\n')
    assert mod.settings_digest(load(tmp_path)) == first
    write(tmp_path, '[catalogs]\ngates = "changed"\n')
    changed = mod.settings_digest(load(tmp_path))
    assert changed != first
    write(tmp_path, '# comment\n[catalogs]\ngates = \'changed\'\n')
    assert mod.settings_digest(load(tmp_path)) == changed


@pytest.mark.parametrize("value", ['"literal"', '123', '{env="BAD-name"}', '{env="NAME",file="/tmp/key"}', '{other="NAME"}', '{file="relative"}', '{file="/tmp/line\\nkey"}'])
def test_secret_invalid(tmp_path, schema, value):
    write(tmp_path, '[test]\naccess_token = ' + value)
    with pytest.raises(mod.SettingsError, match="test.access_token"):
        load(tmp_path)


def test_secret_repo_refused(tmp_path, schema):
    write(tmp_path, '[test]\naccess_token = {file="' + str(tmp_path / "../" / tmp_path.name / "secret") + '"}')
    with pytest.raises(mod.SettingsError, match="inside repository"):
        load(tmp_path)


def test_secret_resolution(tmp_path, schema):
    result = load(tmp_path)
    ref = result.sections["test"].access_token
    with pytest.raises(mod.SettingsError, match="test.access_token"):
        mod.resolve_secret(ref, environ={})
    assert mod.resolve_secret(ref, environ={"TEST_SECRET": "actual"}) == "actual"
    assert result.get("test.access_token") == {"env": "TEST_SECRET"}
    secret = tmp_path.parent / (tmp_path.name + "-secret")
    write(tmp_path, '[test]\naccess_token = {file="' + str(secret) + '"}')
    ref = load(tmp_path).sections["test"].access_token
    with pytest.raises(mod.SettingsError, match="test.access_token"):
        mod.resolve_secret(ref)
    secret.write_text("file-secret")
    try:
        assert mod.resolve_secret(ref) == "file-secret"
    finally:
        secret.unlink()


def test_cli(tmp_path, capsys, monkeypatch):
    from ranex.cli.main import main
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert main(["settings", "show", "--repository", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == canonical_json(load(tmp_path).show())
    assert main(["settings", "get", "catalogs.gates", "--repository", str(tmp_path)]) == 0
    assert capsys.readouterr().out == "governance/gates.yaml\n"
    assert main(["settings", "get", "catalogs.unknown", "--repository", str(tmp_path)]) == 2
    assert "catalogs.unknown" in capsys.readouterr().err
