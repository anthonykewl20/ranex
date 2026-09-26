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

from ranex.foundation.signing import generate_keypair

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

    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    producers = [
        (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
        for line in lines
        if line.startswith("  ") and ": ed25519:" in line and not line.lstrip().startswith("role")
    ]
    approver_entry = (
        f"  {approver_id}:\n    role: approver\n    keys:\n"
        f"      - key: {public}\n        status: active\n"
    )
    for index, line in enumerate(lines):
        if line.rstrip() == "principals:":
            lines.insert(index + 1, approver_entry)
            keyring.write_text("".join(lines), encoding="utf-8")
            return
    # No principals block: adopt the principal catalog wholesale, every
    # existing producer becoming the worker principal of its own key.
    lines.append("principals:\n")
    for producer_id, public_key in producers:
        lines.append(
            f"  {producer_id}:\n    role: worker\n    keys:\n"
            f"      - key: {public_key}\n        status: active\n"
        )
    lines.append(approver_entry)
    keyring.write_text("".join(lines), encoding="utf-8")


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
