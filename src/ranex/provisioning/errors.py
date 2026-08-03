"""One base for every provisioning refusal, so the CLI catches one thing."""

from __future__ import annotations


class ProvisioningError(Exception):
    """A provisioning input, artifact or phase cannot be verified."""
