"""The release tag spelling; Python distribution metadata remains normalized."""

from __future__ import annotations

import re

from packaging.version import Version


def release_tag(version: str) -> str:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("release requires a three-part final package version")
    major, minor, patch = Version(version).release
    if patch > 999:
        raise ValueError("patch field exceeds three digits; choose a new minor release")
    return f"v{major}.{minor}.{patch:03d}"
