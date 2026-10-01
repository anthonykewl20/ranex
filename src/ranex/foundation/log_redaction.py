"""Pure redaction of retained execution-log text.

Passes redact literals, paired PEM blocks, unterminated PEM blocks, and
credential URL passwords. Credential URL matching deliberately selects the
last compatible ``@`` delimiter and permits one extra ``@`` before the host,
so ``@``-bearing URL path data can be over-redacted rather than leave password
bytes in retained text.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

SENSITIVE_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|passwd|credential|private[_-]?key|"
    r"signing[_-]?key|bearer)"
)
MIN_REDACT_LITERAL: int = 16
MIN_FORCED_LITERAL: int = 16

_SIGNING_KEY_NAMES: frozenset[str] = frozenset(
    {"RANEX_SIGNING_KEY", "RANEX_VERDICT_SIGNING_KEY"}
)
_PEM_BLOCK_PATTERN: re.Pattern[str] = re.compile(
    r"-----BEGIN ((?:[A-Z0-9]+ )*)PRIVATE KEY-----.*?-----END \1PRIVATE KEY-----",
    re.DOTALL,
)
_UNPAIRED_PEM_BLOCK_PATTERN: re.Pattern[str] = re.compile(
    r"-----BEGIN ((?:[A-Z0-9]+ )*)PRIVATE KEY-----(?:(?!-----END \1PRIVATE KEY-----).)*\Z",
    re.DOTALL,
)
_CREDENTIAL_URL_PATTERN: re.Pattern[str] = re.compile(
    r"(?P<prefix>[A-Za-z0-9+.-]+://[^:@/]*:)(?:[^@\s]+@)*[^@\s]+"
    r"(?P<suffix>@(?=[@]?[^@/\s]+(?:[/?#]|\s|$)))"
)


def collect_redaction_literals(
    ambient: Mapping[str, str], *, forced: Sequence[str] = ()
) -> list[tuple[str, str]]:
    """Collect environment values eligible for literal redaction."""

    collected: dict[str, str] = {}
    for name, value in ambient.items():
        if SENSITIVE_NAME_PATTERN.search(name) is not None and len(value) >= MIN_REDACT_LITERAL:
            collected[f"env:{name}"] = value

    for name in _SIGNING_KEY_NAMES:
        value = ambient.get(name)
        if value is not None and len(value) >= MIN_REDACT_LITERAL:
            collected[f"env:{name}"] = value

    for name in forced:
        if name not in ambient:
            raise ValueError(f"refusing --redact-env {name}: not set in the environment")
        value = ambient[name]
        if len(value) < MIN_FORCED_LITERAL:
            raise ValueError(
                f"refusing --redact-env {name}: value shorter than the 16-byte redaction floor"
            )
        collected[f"env:{name}"] = value

    return sorted(collected.items(), key=lambda literal: (-len(literal[1]), literal[0]))


def redact_text(text: str, literals: Sequence[tuple[str, str]]) -> tuple[str, dict[str, int]]:
    """Redact literals, PEM blocks, and credential URL passwords from text."""

    redacted = text
    counts: dict[str, int] = {}
    for kind, value in literals:
        replacements = redacted.count(value)
        if replacements > 0:
            redacted = redacted.replace(value, f"[REDACTED:{kind}]")
            counts[kind] = counts.get(kind, 0) + replacements

    redacted, pem_replacements = _PEM_BLOCK_PATTERN.subn("[REDACTED:pem]", redacted)
    redacted, unpaired_pem_replacements = _UNPAIRED_PEM_BLOCK_PATTERN.subn(
        "[REDACTED:pem]", redacted
    )
    pem_replacements += unpaired_pem_replacements
    if pem_replacements > 0:
        counts["pem"] = counts.get("pem", 0) + pem_replacements

    redacted, credential_replacements = _CREDENTIAL_URL_PATTERN.subn(
        _redact_credential_url,
        redacted,
    )
    if credential_replacements > 0:
        counts["credential"] = credential_replacements

    return redacted, counts


def _redact_credential_url(match: re.Match[str]) -> str:
    """Keep a credential URL's scheme, user, and suffix while hiding its password."""

    return f"{match.group('prefix')}[REDACTED:credential]{match.group('suffix')}"
