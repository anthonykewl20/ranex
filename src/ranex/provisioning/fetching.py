"""Bring the selected wheels into the store — the only networked step.

Every artifact's address was fixed by the derivation-verified lock before
this module runs. A download either hashes to that address or is refused by
the store's own publish check; nothing here can admit bytes the lock did not
name. A store entry that fails its re-hash was already quarantined by the
read, and only this phase may fetch its replacement (ADR-007 sad path 9).
"""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass

from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.lockfile import WheelArtifact
from ranex.provisioning.store import StoreError, WheelStore


class FetchError(ProvisioningError):
    """A selected wheel cannot be brought verifiably into the store."""


@dataclass(frozen=True, slots=True)
class FetchReport:
    downloaded: tuple[str, ...]
    reused: tuple[str, ...]


def ensure_wheels(
    artifacts: Sequence[WheelArtifact],
    store: WheelStore,
    timeout: float = 60.0,
) -> FetchReport:
    """Verify or download every selected wheel; partial success is failure."""

    downloaded: list[str] = []
    reused: list[str] = []
    for artifact in artifacts:
        try:
            store.verified_path(artifact.sha256)
            reused.append(artifact.package)
            continue
        except StoreError:
            # Absent, or corrupt-and-now-quarantined. Either way the address
            # is empty and this phase is the one allowed to fill it.
            pass
        if not artifact.url.startswith(("https://", "http://")):
            raise FetchError(
                f"wheel for {artifact.package} {artifact.version} has an "
                f"unsupported url scheme: {artifact.url}"
            )
        try:
            with urllib.request.urlopen(artifact.url, timeout=timeout) as response:
                data = response.read()
        except (urllib.error.URLError, OSError) as exc:
            raise FetchError(
                f"cannot download {artifact.package} {artifact.version} "
                f"from {artifact.url}: {exc}"
            ) from exc
        try:
            store.publish(artifact.sha256, data)
        except StoreError as exc:
            # s.p. 8: the downloaded bytes miss their declared digest. The
            # store already refused them; name the package for the operator.
            raise FetchError(
                f"downloaded wheel for {artifact.package} {artifact.version} "
                f"does not match the lock's sha256: {exc}"
            ) from exc
        downloaded.append(artifact.package)
    return FetchReport(tuple(downloaded), tuple(reused))
