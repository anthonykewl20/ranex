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
# ``code`` is a closed vocabulary, not an open grammar (D3): the kind must be
# one of CODE_KINDS below — the emitted set, frozen by
# tests/contract/test_trace_schema.py. Per-kind structural argument forms
# (remediation N1) replace the old bounded-charset argument: a registered
# kind's ARGUMENT is structural, so a grammar-shaped secret riding a
# legitimate kind (`out_of_form:code:rnxs-bearer-…`) is out of form exactly
# like an unknown kind. The admissible forms, per kind:
#
#   exit:<int>                            bounded integer (exit codes)
#   undeclared_field:<identifier>         the echoable-name form
#   undeclared_field:len=N,sha256_8=<hex> the shape form for hostile names
#   out_of_form:<field>:len=N,sha256_8=…  <field> one of the frozen eleven
#   malformed_parent_sid:len=N,sha256_8=… the shape form (plus the bounded
#                                         identifier argument the frozen
#                                         round-1 example ``af_unix`` pins)
#   oversized_event:len=<N>               the refused line's length
#   the five bare kinds                   NO argument whatsoever
#
# Anything else is refused whole-event and the value is represented by shape
# plus digest, never its bytes. Every internal emission site emits one of
# these forms literally.
CODE_KINDS: frozenset[str] = frozenset(
    {
        "exit",
        "undeclared_field",
        "out_of_form",
        "malformed_parent_sid",
        "cap_exceeded",
        "target_admission_failed",
        "oversized_event",
        "emission_refused",
        "emission_not_a_mapping",
        "refusal_code_overflow",
    }
)
# The five kinds that take no argument at all; ``kind:arg`` with one of them
# is out of form.
CODE_BARE_KINDS: frozenset[str] = frozenset(
    {
        "cap_exceeded",
        "target_admission_failed",
        "emission_refused",
        "emission_not_a_mapping",
        "refusal_code_overflow",
    }
)
# The ``out_of_form`` field names one of the frozen eleven; the version-only
# ``evt``/``exe`` members are not among them, so a refusal code naming them
# falls back to the bounded ``emission_refused`` literal in redaction's belt.
_CODE_OUT_OF_FORM_FIELDS: frozenset[str] = frozenset(FIELDS)
# ``len=`` plus digits and ``len=…,sha256_8=`` plus 8 hex: the two shape-form
# arguments, bounded so the argument alone cannot exceed the old 200-char
# argument cap. The type-bucket form ``type=object,sha256_8=…`` is part of
# the same closed vocabulary — ``shape_descriptor`` returns it for values
# with no JSON form (D5's fixed bucket), and refusal codes compose
# ``out_of_form:<field>:<shape_descriptor(value)>``, so the bucket must
# stay an admissible argument or those refusals would degrade to the belt.
_CODE_SHAPE_ARG_RE = re.compile(
    r"\A(?:len=[0-9]{1,196},sha256_8=[0-9a-f]{8}|type=object,sha256_8=[0-9a-f]{8})\Z"
)
_CODE_LEN_ARG_RE = re.compile(r"\Alen=[0-9]{1,196}\Z")
_CODE_EXIT_ARG_RE = re.compile(r"\A-?[0-9]{1,200}\Z")
# The bounded identifier argument — the same [a-z_][a-z0-9_]*-form, capped at
# 200 total, that redaction's echo path applies to echoed field names.
_CODE_IDENTIFIER_ARG_RE = re.compile(r"\A[a-z_][a-z0-9_]{0,199}\Z")
_HIERARCHY_RE = re.compile(r"\A[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*\Z")
# ``subject_digest`` is hex (slice decision 3): 64 lowercase hex characters.
_SUBJECT_DIGEST_RE = re.compile(r"\A[0-9a-f]{64}\Z")
# ``exe`` is a version string ("0.0.0" here); a closed charset keeps a rogue
# emission from smuggling arbitrary bytes through the version variant.
_EXE_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._+~-]{0,255}\Z")


def field_name_is_named(name: str) -> bool:
    """True when a dropped field name matches the bounded identifier grammar."""

    return bool(_IDENTIFIER_RE.match(name)) and len(name) <= IDENTIFIER_NAME_CAP


def code_is_well_formed(code: object) -> bool:
    """kind ∈ CODE_KINDS with its structural argument form, line-bounded.

    Per-kind forms (N1): ``exit`` an integer; ``undeclared_field`` an
    identifier or the shape form; ``out_of_form`` one of the frozen eleven
    fields plus a shape; ``malformed_parent_sid`` the shape form (plus the
    bounded identifier argument the frozen round-1 example ``af_unix`` pins);
    ``oversized_event`` ``len=<N>``; the five bare kinds no argument at all.
    """

    if not isinstance(code, str) or len(code) > MAX_LINE_LENGTH:
        return False
    kind, separator, argument = code.partition(":")
    if kind not in CODE_KINDS:
        return False
    if not separator:
        return kind in CODE_BARE_KINDS
    if len(argument) > 200:
        return False
    if kind == "exit":
        return bool(_CODE_EXIT_ARG_RE.match(argument))
    if kind == "undeclared_field":
        return bool(_CODE_IDENTIFIER_ARG_RE.match(argument)) or bool(
            _CODE_SHAPE_ARG_RE.match(argument)
        )
    if kind == "out_of_form":
        field, inner_separator, shape = argument.partition(":")
        return (
            bool(inner_separator)
            and field in _CODE_OUT_OF_FORM_FIELDS
            and bool(_CODE_SHAPE_ARG_RE.match(shape))
        )
    if kind == "malformed_parent_sid":
        return bool(_CODE_SHAPE_ARG_RE.match(argument)) or bool(
            _CODE_IDENTIFIER_ARG_RE.match(argument)
        )
    if kind == "oversized_event":
        return bool(_CODE_LEN_ARG_RE.match(argument))
    # The five bare kinds admit no argument whatsoever.
    return False


def hierarchy_is_well_formed(hierarchy: object) -> bool:
    return (
        isinstance(hierarchy, str)
        and bool(_HIERARCHY_RE.match(hierarchy))
        and len(hierarchy) <= MAX_LINE_LENGTH
    )


def subject_digest_is_well_formed(digest: object) -> bool:
    return isinstance(digest, str) and bool(_SUBJECT_DIGEST_RE.match(digest))


def exe_is_well_formed(exe: object) -> bool:
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

    Surrogate-safe (remediation N5): a hostile ``execve`` can put non-UTF-8
    bytes in the environment, which Python decodes with ``surrogateescape``;
    ``str.encode("utf-8")`` would raise ``UnicodeEncodeError`` on the lone
    surrogates and crash the import. Encoding with ``surrogatepass`` is
    total and deterministic over such values — the descriptor never echoes
    the raw bytes, only length and digest.
    """

    if isinstance(value, str):
        raw = value.encode("utf-8", "surrogatepass")
    elif isinstance(value, (bytes, bytearray)):
        raw = bytes(value)
    else:
        try:
            import json

            raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "utf-8"
            )
        except (TypeError, ValueError, RecursionError):
            # A value with no JSON form at all (a set, a custom object) is
            # described by a FIXED closed bucket, never the class name — a
            # class name is attacker-choosable ascii and would ride a
            # diagnostic that is otherwise shape+digest only. No length is
            # claimed (none is well defined for an unserializable value) and
            # the digest input is the bucket literal, so no content byte can
            # enter and the descriptor is identical for every such value.
            # Disclosed residual (ADR-031): a short digest is a weak offline-
            # confirmation oracle for low-entropy refused values.
            digest = hashlib.sha256(b"object").hexdigest()[:8]
            return f"type=object,sha256_8={digest}"
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
