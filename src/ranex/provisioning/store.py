"""Store wheel bytes by digest and quarantine any address that stops matching."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from ranex.provisioning.errors import ProvisioningError


class StoreError(ProvisioningError):
    """A wheel-store address is invalid, absent, or has become untrustworthy."""


_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class WheelStore:
    """A content-addressed wheel store whose reads always verify their bytes."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def _entry(self, digest: str) -> Path:
        return self.root / "sha256" / digest

    def _check_digest(self, digest: str) -> None:
        if not _DIGEST.fullmatch(digest):
            raise StoreError(f"wheel-store digest is not 64 lowercase hex: {digest!r}")

    def publish(self, digest: str, data: bytes) -> None:
        """Atomically publish bytes only at the address they actually hash to."""
        self._check_digest(digest)
        if hashlib.sha256(data).hexdigest() != digest:
            raise StoreError(f"wheel bytes do not match sha256 address {digest}")
        temporary_directory = self.root / "tmp"
        entry = self._entry(digest)
        temporary_directory.mkdir(parents=True, exist_ok=True)
        entry.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(dir=temporary_directory)
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
            os.chmod(temporary, 0o444)
            os.replace(temporary, entry)
            temporary = None
        except OSError as exc:
            raise StoreError(f"cannot publish wheel {digest}: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def verified_path(self, digest: str) -> Path:
        """Return an entry only after rehashing it, quarantining corruption."""
        self._check_digest(digest)
        entry = self._entry(digest)
        try:
            data = entry.read_bytes()
        except FileNotFoundError as exc:
            raise StoreError(f"wheel-store entry {digest} is absent") from exc
        except OSError as exc:
            raise StoreError(f"cannot read wheel-store entry {digest}: {exc}") from exc
        if hashlib.sha256(data).hexdigest() == digest:
            return entry
        quarantine = self.root / "quarantine"
        quarantine.mkdir(parents=True, exist_ok=True)
        destination = quarantine / f"{digest}-{os.urandom(8).hex()}"
        try:
            os.replace(entry, destination)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise StoreError(f"cannot quarantine corrupted wheel {digest}: {exc}") from exc
        raise StoreError(f"wheel-store entry {digest} failed verification and was quarantined")
