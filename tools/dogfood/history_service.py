"""Explicit service identity and retained checkpoints for isolated tool subjects."""
from __future__ import annotations

from pathlib import Path

import yaml

from ranex.foundation.signing import generate_keypair

SERVICE_ID = "kernel-verdict-signer"


def install_service(keyring: Path, key_path: Path, approver: str) -> None:
    """Register a separate service before the caller commits its trust root."""
    private, public = generate_keypair()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with key_path.open("x", encoding="utf-8") as stream:
        stream.write(private + "\n")
    key_path.chmod(0o600)
    approver_private, approver_public = generate_keypair()
    approver_path = key_path.parent / "approver.key"
    with approver_path.open("x", encoding="utf-8") as stream:
        stream.write(approver_private + "\n")
    approver_path.chmod(0o600)
    document = yaml.safe_load(keyring.read_bytes())
    document["verdict_signer"] = {"id": SERVICE_ID, "public_key": public}
    principals = document.setdefault("principals", {})
    for producer, producer_key in document["producers"].items():
        principals.setdefault(producer, {"role": "worker", "keys": [
            {"key": producer_key, "status": "active"}]})
    principals[SERVICE_ID] = {"role": "service", "keys": [
        {"key": public, "status": "active"}]}
    principals[approver] = {"role": "approver", "keys": [
        {"key": approver_public, "status": "active"}]}
    keyring.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


def history_environment(producer_key: Path) -> dict[str, str]:
    directory = producer_key.resolve().parent
    return {
        "RANEX_APPROVER_SIGNING_KEY": str(directory / "approver.key"),
        "RANEX_VERDICT_SIGNING_KEY": str(directory / "history-service.key"),
        "RANEX_HISTORY_CHECKPOINT": str(directory / "history.checkpoint.json"),
    }
