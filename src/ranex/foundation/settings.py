"""Typed, scoped settings. Policy is repository-owned; mechanics is host-owned."""
from __future__ import annotations

import os
import re
import subprocess
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ranex.foundation.canonical import canonical_sha256

settings_schema_version = 1


class SettingsError(ValueError):
    """A named configuration or secret-reference failure."""


def setting(name: str, default: Any, scope: str, description: str) -> Any:
    metadata = {"name": name, "type": type(default), "default": default,
                "scope": scope, "description": description}
    if isinstance(default, dict):
        return field(default_factory=lambda: dict(default), metadata=metadata)
    return field(default=default, metadata=metadata)


@dataclass(frozen=True)
class Catalogs:
    journal: str = setting("journal", "governance/journal.sqlite3", "policy", "Governance journal")
    pins: str = setting("pins", "governance/deps.yaml", "policy", "Dependency pins")
    gates: str = setting("gates", "governance/gates.yaml", "policy", "Gate catalog")
    suite_manifest: str = setting("suite_manifest", "governance/suite_manifest.json", "policy", "Frozen suite")
    evidence: str = setting("evidence", "governance/evidence.json", "policy", "Evidence records")
    calibration_dir: str = setting("calibration_dir", "governance/calibration", "policy", "Calibration freezes")
    producers: str = setting("producers", "governance/producers.yaml", "policy", "Producer keyring")
    verdict_dir: str = setting("verdict_dir", "governance/verdicts", "policy", "Signed verdicts")


SCHEMA: Mapping[str, type] = MappingProxyType({"catalogs": Catalogs})


@dataclass(frozen=True)
class SecretReference:
    key: str
    env: str | None = None
    file: str | None = None


def _secret(key: str, value: Any, root: Path) -> SecretReference:
    if not isinstance(value, dict) or set(value) not in ({"env"}, {"file"}):
        raise SettingsError(f"{key}: expected exactly {{env = NAME}} or {{file = PATH}}")
    kind, text = next(iter(value.items()))
    if not isinstance(text, str):
        raise SettingsError(f"{key}: reference must be a string")
    if kind == "env":
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", text):
            raise SettingsError(f"{key}: invalid environment name")
        return SecretReference(key, env=text)
    if (not (Path(text).is_absolute() or text.startswith("~/"))
            or any(ord(c) < 32 or ord(c) == 127 for c in text)):
        raise SettingsError(f"{key}: invalid secret file path")
    path = Path(text).expanduser().resolve()
    if path.is_relative_to(root):
        raise SettingsError(f"{key}: secret file is inside repository")
    return SecretReference(key, file=str(path))


def resolve_secret(ref: SecretReference, *, environ: Mapping[str, str] | None = None) -> str:
    """Resolve only at use time; settings loading never reads secret contents."""
    env = os.environ if environ is None else environ
    if ref.env is not None:
        if ref.env not in env:
            raise SettingsError(f"{ref.key}: environment variable {ref.env} is not set")
        return env[ref.env]
    if ref.file is not None:
        try:
            return Path(ref.file).read_text()
        except (OSError, UnicodeError) as exc:
            raise SettingsError(f"{ref.key}: secret file {ref.file} is not readable") from exc
    raise SettingsError(f"{ref.key}: invalid secret reference")


@dataclass(frozen=True)
class Settings:
    sections: Mapping[str, Any]
    sources: Mapping[str, str]

    @property
    def catalogs(self) -> Catalogs:
        return self.sections["catalogs"]

    def show(self) -> dict[str, Any]:
        return {section: {f.name: {"value": _value(getattr(instance, f.name)),
                                  "scope": f.metadata["scope"],
                                  "source": self.sources[f"{section}.{f.name}"]}
                          for f in fields(instance)}
                for section, instance in self.sections.items()}

    def get(self, key: str) -> Any:
        section, sep, name = key.partition(".")
        if not sep or section not in self.sections or name not in {f.name for f in fields(self.sections[section])}:
            raise SettingsError(f"unknown setting {key}")
        return _value(getattr(self.sections[section], name))


def _value(value: Any) -> Any:
    if isinstance(value, SecretReference):
        return {"env": value.env} if value.env is not None else {"file": value.file}
    return value


def _read(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text())
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise SettingsError(f"{path}: {exc}") from exc


def load_settings(repository_root: str | Path, *, evaluated_ref: str | None = None,
                  host_file: str | Path | None = None, environ: Mapping[str, str] | None = None,
                  cli_overrides: Mapping[str, Any] | None = None) -> Settings:
    root = Path(repository_root).resolve()
    env = os.environ if environ is None else environ
    schema = {f"{section}.{f.name}": f for section, cls in SCHEMA.items() for f in fields(cls)}
    names = {"RANEX_" + key.replace(".", "_").upper(): key for key in schema}
    if len(names) != len(schema):
        raise SettingsError("schema: environment name collision")
    values: dict[str, Any] = {}
    sources: dict[str, str] = {}

    def put(key: str, value: Any, source: str, *, host: bool = False, env_value: bool = False) -> None:
        if key not in schema:
            raise SettingsError(f"{source}: unknown key {key}")
        f = schema[key]
        if host and f.metadata["scope"] == "policy":
            raise SettingsError(f"{source}: policy key {key} cannot be overridden")
        secret = key.endswith(("_secret", "_password", "_token", "_key"))
        if secret:
            if env_value:
                try:
                    value = tomllib.loads("reference = " + value)["reference"]
                except (tomllib.TOMLDecodeError, KeyError) as exc:
                    raise SettingsError(f"{source}: {key}: invalid secret reference") from exc
            try:
                value = _secret(key, value, root)
            except SettingsError as exc:
                raise SettingsError(f"{source}: {exc}") from exc
        else:
            expected = f.metadata["type"]
            if env_value:
                if expected is bool:
                    if value not in ("true", "false"):
                        raise SettingsError(f"{source}: {key}: expected true/false")
                    value = value == "true"
                elif expected is int:
                    if not re.fullmatch(r"[+-]?[0-9]+", value):
                        raise SettingsError(f"{source}: {key}: expected base-10 integer")
                    value = int(value, 10)
            if type(value) is not expected:
                raise SettingsError(f"{source}: {key}: expected {expected.__name__}")
        values[key], sources[key] = value, source

    def merge(data: Mapping[str, Any], source: str, *, host: bool = False,
              scope: str | None = None) -> None:
        for section, entries in data.items():
            if section not in SCHEMA or not isinstance(entries, dict):
                raise SettingsError(f"{source}: unknown or invalid section {section}")
            for name, value in entries.items():
                key = f"{section}.{name}"
                if key not in schema:
                    raise SettingsError(f"{source}: unknown key {key}")
                if scope is None or schema[key].metadata["scope"] == scope:
                    put(key, value, source, host=host)

    for key, f in schema.items():
        put(key, f.metadata["default"], "default")
    repo_path = root / "governance/settings.toml"
    if evaluated_ref is None:
        merge(_read(repo_path), str(repo_path))
    else:
        merge(_read(repo_path), str(repo_path), scope="mechanics")
        if evaluated_ref.startswith("-"):
            raise SettingsError(f"invalid evaluated_ref {evaluated_ref!r}")
        # Probe the tree first: a missing blob is defaults, an invalid ref is not.
        try:
            tree = subprocess.run(["git", "-C", str(root), "ls-tree", evaluated_ref, "--", "governance/settings.toml"], capture_output=True, text=True, check=False)
        except UnicodeError:
            raise SettingsError(f"{evaluated_ref}:governance/settings.toml: not UTF-8") from None
        if tree.returncode:
            raise SettingsError(f"{evaluated_ref}: {tree.stderr.strip()}")
        if tree.stdout:
            try:
                blob = subprocess.run(["git", "-C", str(root), "show", f"{evaluated_ref}:governance/settings.toml"], capture_output=True, text=True, check=False)
            except UnicodeError:
                raise SettingsError(f"{evaluated_ref}:governance/settings.toml: not UTF-8") from None
            if blob.returncode:
                raise SettingsError(f"{evaluated_ref}: {blob.stderr.strip()}")
            try:
                merge(tomllib.loads(blob.stdout), f"{evaluated_ref}:governance/settings.toml", scope="policy")
            except tomllib.TOMLDecodeError as exc:
                raise SettingsError(f"{evaluated_ref}:governance/settings.toml: {exc}") from exc
    host_path = Path(host_file) if host_file is not None else Path(env.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "ranex/settings.toml"
    merge(_read(host_path), str(host_path), host=True)
    for name, value in env.items():
        if name in names:
            put(names[name], value, name, host=True, env_value=True)
        elif any(name.startswith("RANEX_" + section.upper() + "_") for section in SCHEMA):
            raise SettingsError(f"{name}: unknown key {name}")
    for key, value in (cli_overrides or {}).items():
        put(key, value, "CLI", host=True)
    sections = {}
    for section, cls in SCHEMA.items():
        instance = cls(**{f.name: values[f"{section}.{f.name}"] for f in fields(cls)})
        validator = getattr(instance, "validate", None)
        if validator is not None:
            validator()
        sections[section] = instance
    return Settings(MappingProxyType(sections), MappingProxyType(sources))


def settings_digest(settings: Settings) -> str:
    policy = {section: {f.name: _value(getattr(instance, f.name)) for f in fields(instance)
                        if f.metadata["scope"] == "policy"}
              for section, instance in settings.sections.items()
              if any(f.metadata["scope"] == "policy" for f in fields(instance))}
    return canonical_sha256({"settings_schema_version": settings_schema_version, "policy": policy})
