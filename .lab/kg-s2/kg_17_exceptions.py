"""Domain error hierarchy."""
from __future__ import annotations


class AppError(Exception):
    """Base class for expected application failures."""

    def __init__(self, message: str, *, recoverable: bool = True) -> None:
        super().__init__(message)
        self.recoverable = recoverable


class ConfigError(AppError):
    pass


class UpstreamError(AppError):
    def __init__(self, message: str, service: str) -> None:
        super().__init__(message, recoverable=False)
        self.service = service


def classify(error: BaseException) -> str:
    match error:
        case ConfigError():
            return "config"
        case UpstreamError(service=s):
            return f"upstream:{s}"
        case AppError(recoverable=True):
            return "soft"
        case AppError():
            return "hard"
        case _:
            return "unknown"
