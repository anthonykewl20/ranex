"""Explicit isolated history service setup for CLI test repositories."""
from __future__ import annotations

from pathlib import Path

import yaml

from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.history import bootstrap_history, record_anchored


def mint_service(directory: Path) -> tuple[str, str, Path]:
    private, public = generate_keypair()
    path = directory / "history-service.key"
    path.write_text(private + "\n")
    path.chmod(0o600)
    return private, public, path


def register_service(keyring: Path, public: str) -> None:
    document = yaml.safe_load(keyring.read_bytes())
    document["verdict_signer"] = {"id": "kernel-verdict-signer", "public_key": public}
    principals = document.setdefault("principals", {})
    for producer, producer_key in document["producers"].items():
        principals.setdefault(producer, {"role": "worker", "keys": [
            {"key": producer_key, "status": "active"}]})
    principals["kernel-verdict-signer"] = {"role": "service", "keys": [
        {"key": public, "status": "active"}]}
    keyring.write_text(yaml.safe_dump(document, sort_keys=False))


def establish(repo: Path, name: str, checkpoint: Path, private: str, public: str) -> None:
    bootstrap_history(repo / name, checkpoint, private, public, repo)


def write_records(repo: Path, name: str, records, checkpoint: Path,
                  private: str, public: str) -> None:
    for record in records:
        record_anchored(repo / name, record, checkpoint, private, public, repo)
