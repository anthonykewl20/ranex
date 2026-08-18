"""Frozen event schema for the kernel observability trace (ADR-031, SLICE-054).

Everything here is stdlib-only, per the ADR's dependency rule: the runtime
graph is three packages and an observer adds none. The numeric constants,
field order, registries, and grammars are frozen by
tests/contract/test_trace_schema.py; any drift turns that file red. Schema
evolution is a new decision (an ``evt`` bump), never a patch.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# The schema number carried by every ``version`` event as ``evt``.
SCHEMA_NUMBER = 1

# The frozen eleven-field set, in canonical serialization order. Every event
# carries all eleven; inapplicable members are null, never absent, because
# the set is the contract.
FIELDS: tuple[str, ...] = (
    "event",
    "sid",
    "time",
    "level",
    "module",
    "stage",
    "subject_digest",
    "duration_us",
    "hierarchy",
    "child_id",
    "code",
)

# ``version`` is a discriminated variant: the eleven plus exactly these two,
# admitted on ``version`` events only. Any other event carrying either is
# refused like any undeclared field.
VERSION_ONLY_FIELDS: tuple[str, ...] = ("evt", "exe")

# Bounded-size constants, frozen by the schema contract test. A line longer
# than MAX_LINE_LENGTH is refused, never truncated. A file/directory target
# that cannot fit one final refusal line inside TRACE_BYTE_CAP is refused at
# admission; past the cap the target stops — refusal, not rotation.
MAX_LINE_LENGTH = 16384
TRACE_BYTE_CAP = 1_048_576

# Bound for identifier-shaped strings that are not otherwise closed (``exe``).
# A dropped field name is echoed in a refusal event only when it also fits
# the ``code`` grammar's argument bound (see redaction.echoable_name), so an
# echoed name can never degrade into a truncated or grammar-invalid code.
IDENTIFIER_NAME_CAP = 256

# Closed value vocabularies.
EVENT_NAMES: frozenset[str] = frozenset({"version", "stage", "refusal", "note"})
LEVELS: frozenset[str] = frozenset({"debug", "info", "warn", "error"})
MODULES: frozenset[str] = frozenset({"cli", "observability"})

# The CLI dispatch groups enumerated from src/ranex/cli/main.py's argparse
# subcommands — verified against main.py at freeze time and recorded as a
# literal in tests/contract/test_trace_schema.py, so adding or removing a
# CLI group is a deliberate edit of that frozen test.
CLI_DISPATCH_NAMES: tuple[str, ...] = (
    "run",
    "gate.evaluate",
    "journal.verify",
    "suite.freeze",
    "deps.fetch",
    "deps.approve",
    "keygen",
    "task.dispatch",
    "task.judge",
    "task.merge",
    "task.delegate",
    "task.fanout",
)

STAGES: frozenset[str] = frozenset(
    {f"cli.{name}.{half}" for name in CLI_DISPATCH_NAMES for half in ("start", "end")}
) | {"observability.emission", "observability.note"}

# Value grammars.
_IDENTIFIER_RE = re.compile(r"\A[a-z_][a-z0-9_]*\Z")
# code = kind[:arg], arg matching [A-Za-z0-9_.=+,:-]{1,200} (slice decision 4;
# frozen by tests/contract/test_trace_schema.py). Colons are allowed in the
# argument so a refusal can name ``out_of_form:<field>:<shape>`` without
# overflowing its own grammar.
_CODE_RE = re.compile(r"\A[a-z_][a-z0-9_]*(?::[A-Za-z0-9_.=+,:-]{1,200})?\Z")
_HIERARCHY_RE = re.compile(r"\A[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*\Z")
# ``subject_digest`` is hex (slice decision 3): 64 lowercase hex characters.
_SUBJECT_DIGEST_RE = re.compile(r"\A[0-9a-f]{64}\Z")
# ``exe`` is a version string ("0.0.0" here); a closed charset keeps a rogue
# emission from smuggling arbitrary bytes through the version variant.
_EXE_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._+~-]{0,255}\Z")


def field_name_is_named(name: str) -> bool:
    """True when a dropped field name matches the bounded identifier grammar."""

    return bool(_IDENTIFIER_RE.match(name)) and len(name) <= IDENTIFIER_NAME_CAP


def code_is_well_formed(code: str) -> bool:
    return isinstance(code, str) and bool(_CODE_RE.match(code)) and len(code) <= MAX_LINE_LENGTH


def hierarchy_is_well_formed(hierarchy: str) -> bool:
    return (
        isinstance(hierarchy, str)
        and bool(_HIERARCHY_RE.match(hierarchy))
        and len(hierarchy) <= MAX_LINE_LENGTH
    )


def subject_digest_is_well_formed(digest: str) -> bool:
    return isinstance(digest, str) and bool(_SUBJECT_DIGEST_RE.match(digest))


def exe_is_well_formed(exe: str) -> bool:
    return isinstance(exe, str) and bool(_EXE_RE.match(exe))


def validate_field_value(field: str, value: object) -> str | None:
    """Return a short reason when ``value`` is outside the closed form for ``field``.

    The reason never contains the value's bytes — callers turn it into a
    refusal event carrying a shape descriptor only.
    """

    if field == "event":
        if not isinstance(value, str) or value not in EVENT_NAMES:
            return "event not in closed set"
    elif field == "level":
        if not isinstance(value, str) or value not in LEVELS:
            return "level not in closed set"
    elif field == "module":
        if not isinstance(value, str) or value not in MODULES:
            return "module not in closed set"
    elif field == "stage":
        if not isinstance(value, str) or value not in STAGES:
            return "stage not in registered set"
    elif field == "subject_digest":
        if value is not None and not subject_digest_is_well_formed(value):
            return "subject_digest outside hex-64 form"
    elif field == "duration_us":
        if value is not None and (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            or value > 2**53
        ):
            return "duration_us outside bounded integer form"
    elif field == "hierarchy":
        if value is not None and not hierarchy_is_well_formed(value):
            return "hierarchy outside bounded dot-chain form"
    elif field == "child_id":
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 1
        ):
            return "child_id outside bounded integer form"
    elif field == "code":
        if value is not None and not code_is_well_formed(value):
            return "code outside bounded registry form"
    elif field == "evt":
        # Version-only member: the allowlist already refused it on any event
        # other than ``version``; on the variant it must be the schema number.
        if not isinstance(value, int) or isinstance(value, bool) or value != SCHEMA_NUMBER:
            return "evt outside schema-number form"
    elif field == "exe":
        if not exe_is_well_formed(value):
            return "exe outside version-string form"
    else:  # pragma: no cover - the allowlist guards before this point
        return "undeclared field"
    return None


def shape_descriptor(value: object) -> str:
    """Length plus the first 8 hex of SHA-256, never the bytes. Never raises.

    Strings digest their UTF-8 bytes; bytes/bytearrays digest themselves;
    other JSON-shaped values digest their canonical JSON serialization. A
    value with no JSON form at all (a set, a custom object) is described by
    its type name only — no length is claimed, because none is well defined,
    and the digest input never includes the value's contents.
    Disclosed residual (ADR-031): a short digest is a weak offline-
    confirmation oracle for low-entropy refused values.
    """

    if isinstance(value, str):
        raw = value.encode("utf-8")
    elif isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        try:
            import json

            raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "utf-8"
            )
        except (TypeError, ValueError, RecursionError):
            digest = hashlib.sha256(type(value).__name__.encode("ascii")).hexdigest()[:8]
            return f"type={type(value).__name__},sha256_8={digest}"
    digest = hashlib.sha256(raw).hexdigest()[:8]
    return f"len={len(raw)},sha256_8={digest}"


def now_truncated_ms(now: float) -> float:
    """Wall clock, UTC, millisecond-truncated (slice decision 1).

    ``time`` = ``time.time()`` truncated to the millisecond grid as an epoch
    float: ``int(now*1000)/1000.0``. ADR-031's text governs over issue #34's
    review-comment "RFC 3339" reading, and the schema contract test freezes
    this helper's exact reconstruction.
    """

    return int(now * 1000) / 1000.0


def ranex_version() -> str:
    """The ``exe`` member of the version event: the ranex version string.

    importlib.metadata first (an installed context), then a walk up from this
    file for a ``pyproject.toml`` ``[project] version`` (this runtime is
    ``package = false`` and installs no dist metadata; today "0.0.0"), last
    resort "unknown". Both importlib.metadata and tomllib are imported lazily
    so the off-state import never pays for the version walker.
    """

    import importlib.metadata

    try:
        return importlib.metadata.version("ranex")
    except importlib.metadata.PackageNotFoundError:
        pass
    except ValueError:  # pragma: no cover - malformed metadata
        pass

    import tomllib

    here = Path(__file__).resolve()
    for candidate in here.parents:
        manifest = candidate / "pyproject.toml"
        if manifest.is_file():
            try:
                with manifest.open("rb") as handle:
                    data = tomllib.load(handle)
                version = data.get("project", {}).get("version")
                if isinstance(version, str) and version:
                    return version
            except (tomllib.TOMLDecodeError, OSError):
                continue
    return "unknown"
