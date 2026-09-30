"""Test support for the catalogued approver every gate evaluation requires.

RISK-07 / issue #107: `gate evaluate --approver A` refuses before judgment
unless A is a catalogued `approver` principal and `RANEX_APPROVER_SIGNING_KEY`
holds that principal's private half. Real journeys mint a real keypair with
the real `keygen` CLI; the compact in-process suites mint one with the same
`generate_keypair` the kernel's own keygen uses. Either way the private half
lives outside every subject repository, exactly as the operator's does.

Importable everywhere through tests/conftest.py's path hook (`import _approver`).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from ranex.foundation.signing import generate_keypair
from ranex.policy.adapters.configuration.yaml.principal_catalog import load_principals_text
from ranex.policy.adapters.configuration.yaml.producer_keyring import _NoDuplicateKeys

APPROVER_ENV = "RANEX_APPROVER_SIGNING_KEY"


def mint_approver(directory: Path, name: str = "approver") -> tuple[Path, str]:
    """Mint an approver keypair; return (private-key path, public key).

    The private half lands in a 0600 file under the test's own tmp directory —
    never inside a subject repository, which `private_signing_key` refuses.
    """

    private, public = generate_keypair()
    path = Path(directory) / f"{name}.key"
    path.write_text(private + "\n", encoding="utf-8")
    path.chmod(0o600)
    return path, public


def register_approver(keyring: Path, approver_id: str, public: str) -> None:
    """Register an approver principal in a subject's producers.yaml.

    Creates the `principals:` block when the catalog predates it, adopting
    every existing producer as a `worker` principal so the two blocks agree
    the way `_require_blocks_agree` demands. The approver is a principal and
    never a producer: one principal, one role.
    """

    raw = keyring.read_text(encoding="utf-8")
    document = yaml.load(raw, Loader=_NoDuplicateKeys)
    if "principals" in document:
        # Validate before editing: fixture rotation cannot repair malformed
        # trust or reinterpret a worker/service identity as an approver.
        load_principals_text(raw, keyring)
    else:
        document["principals"] = {
            producer: {"role": "worker", "keys": [{"key": key, "status": "active"}]}
            for producer, key in document["producers"].items()
        }
        signer = document.get("verdict_signer")
        if signer is not None:
            document["principals"].setdefault(signer["id"], {
                "role": "service", "keys": [{"key": signer["public_key"], "status": "active"}]
            })
    principals = document["principals"]
    existing = principals.get(approver_id)
    if existing is None:
        principals[approver_id] = {"role": "approver", "keys": [{"key": public, "status": "active"}]}
    else:
        if existing["role"] != "approver":
            raise ValueError("fixture approver registration cannot change a principal's role")
        previous = next((key for key in existing["keys"] if key["key"] == public), None)
        if previous is not None:
            if previous["status"] != "active":
                raise ValueError("fixture approver rotation cannot reactivate a retired key")
            return
        existing["keys"].append({"key": public, "status": "active"})
    encoded = yaml.safe_dump(document, sort_keys=False)
    load_principals_text(encoded, keyring)
    keyring.write_text(encoded, encoding="utf-8")


def strip_approvers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Drop any host approver key from the environment, the way the suites
    already strip `RANEX_SIGNING_KEY` — a host credential must never decide a
    test's identity."""

    monkeypatch.delenv(APPROVER_ENV, raising=False)


def approver_env(path: Path) -> dict[str, str]:
    """The environment carrying one approver key, for subprocess helpers."""

    return {APPROVER_ENV: str(path)}


def host_approvers_present() -> bool:
    return bool(os.environ.get(APPROVER_ENV))


# History is a separate service identity. Fixtures register it before their
# initial commit and explicitly establish the empty history after that commit.
from dataclasses import dataclass, field  # noqa: E402

import _history  # noqa: E402

from ranex.governed_execution.adapters.persistence.sqlite.observations import (
    observations_path_for,  # noqa: E402
)


@dataclass
class HistoryService:
    repository: Path
    private: str
    public: str
    key_path: Path
    checkpoints: dict[str, Path] = field(default_factory=dict)

    def establish(self, name: str = "evidence.json") -> Path:
        identity = str(observations_path_for(self.repository / name).resolve())
        if identity not in self.checkpoints:
            checkpoint = self.key_path.parent / f"history-{len(self.checkpoints)}.json"
            _history.establish(self.repository, name, checkpoint, self.private, self.public)
            self.checkpoints[identity] = checkpoint
        return self.checkpoints[identity]

    def environment(self, name: str = "evidence.json") -> dict[str, str]:
        return {"RANEX_VERDICT_SIGNING_KEY": str(self.key_path),
                "RANEX_HISTORY_CHECKPOINT": str(self.establish(name))}

    def configure(self, monkeypatch, name: str = "evidence.json") -> None:
        for variable, value in self.environment(name).items():
            monkeypatch.setenv(variable, value)
        monkeypatch.delenv("RANEX_VERDICT_DIR", raising=False)

    def write(self, records, name: str = "evidence.json") -> None:
        _history.write_records(self.repository, name, records, self.establish(name), self.private, self.public)


_HISTORY_SERVICES: dict[Path, HistoryService] = {}


def register_history_service(repository: Path, keyring: Path, directory: Path) -> HistoryService:
    private, public, path = _history.mint_service(directory)
    _history.register_service(keyring, public)
    service = HistoryService(repository, private, public, path)
    _HISTORY_SERVICES[repository.resolve()] = service
    return service


def history_for(repository: Path) -> HistoryService:
    return _HISTORY_SERVICES[repository.resolve()]
