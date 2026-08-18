"""Kernel observability — env-gated, default-off trace emission (ADR-031, SLICE-054).

Public surface (frozen by the SLICE-054 contract tests):

    TRACING_ENABLED                    -- False unless a target variable is set
    SESSION_ID                         -- this process's SID, always minted
    stage_begin(stage)                 -- one stage start event at a CLI boundary
    stage_end(stage, code)             -- the matching end event with duration
    emit_raw(mapping)                  -- the screened emission surface

Off state: the environment is read exactly once at import — one ``get`` per
trace variable — and when no variable enables a target, every entry point is
bound once to ``_nop`` (structlog's disabled-cost pattern), so a disabled
emission is a single call returning None and never touches the environment
again. ``SESSION_ID`` stays a module attribute but is minted lazily on first
access, keeping the off-state import bounded to the env reads (the hostname
lookup's socket/idna import chain is paid only when the SID is actually
needed).

An invalid target value is refused loudly at import with one shape-descriptor
warning (never its bytes) and disables only that variable's target; caps,
refusals, and write-failure accounting are per-target (ADR-031 sad path 14).
"""

from __future__ import annotations

import os

import ranex.observability.schema as schema
from ranex.observability.emitter import Emitter, _warn, parse_target
from ranex.observability.sid import derive_session_id

TRACE_VARIABLE = "RANEX_TRACE"
EVENT_VARIABLE = "RANEX_TRACE_EVENT"
PARENT_SID_VARIABLE = "RANEX_TRACE_PARENT_SID"
TRACE_VARIABLES = (TRACE_VARIABLE, EVENT_VARIABLE, PARENT_SID_VARIABLE)
TARGET_VARIABLES = (TRACE_VARIABLE, EVENT_VARIABLE)


def _nop(*_args: object, **_kwargs: object) -> None:
    return None


# The one import-time env read per variable (ADR-031). Nothing below ever
# consults os.environ again.
_VALUES: dict[str, str | None] = {name: os.environ.get(name) for name in TRACE_VARIABLES}

# Classify the two target variables once. An invalid value warns exactly once
# here, whether or not an emission ever happens, and disables only that
# variable's target; tracing is enabled when at least one variable admits a
# target.
_ENABLED_TARGETS: dict[str, str] = {}
for _variable in TARGET_VARIABLES:
    _value = _VALUES[_variable]
    _kind, _operand = parse_target(_value)
    if _kind == "invalid":
        _warn(
            f"{_variable}: refusing trace target value "
            f"({schema.shape_descriptor(_value)}); tracing stays off for this variable"
        )
    elif _kind != "off":
        _ENABLED_TARGETS[_variable] = _value  # type: ignore[assignment]

TRACING_ENABLED = bool(_ENABLED_TARGETS)

# The SID is minted lazily (PEP 562 module __getattr__): deriving a component
# costs a hostname lookup whose import chain (socket, encodings.idna) is the
# single most expensive thing this package can do, and the off state — bound
# by ADR-031 to one env read — must not pay it. First access (an emission, or
# a reader of the SESSION_ID attribute) mints once; the process SID never
# changes afterwards.
_SESSION_ID: str | None = None
_MALFORMED_PARENT_NOTE: str | None = None


def _session_identity() -> tuple[str, str | None]:
    global _SESSION_ID, _MALFORMED_PARENT_NOTE
    if _SESSION_ID is None:
        _SESSION_ID, _MALFORMED_PARENT_NOTE = derive_session_id(
            _VALUES[PARENT_SID_VARIABLE]
        )
    return _SESSION_ID, _MALFORMED_PARENT_NOTE


def __getattr__(name: str) -> object:
    if name == "SESSION_ID":
        return _session_identity()[0]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TRACING_ENABLED:
    _EMITTER = Emitter(_ENABLED_TARGETS, *_session_identity())

    def stage_begin(stage: str) -> None:
        _EMITTER.stage_begin(stage)

    def stage_end(stage: str, code: str | None) -> None:
        _EMITTER.stage_end(stage, code)

    def emit_raw(mapping: object) -> None:
        _EMITTER.emit_raw(mapping)

else:
    stage_begin = _nop  # type: ignore[assignment]
    stage_end = _nop  # type: ignore[assignment]
    emit_raw = _nop  # type: ignore[assignment]


def controller_trace_environment() -> dict[str, str]:
    """ADR-031's one-child seam: the trace variables the confinement-session
    controller may receive, and nothing else.

    Tracing off — ``{}``, so the controller's environment stays byte-identical
    to today's fixed four-variable base. Tracing on — exactly the enabled
    trace target variable(s) plus ``RANEX_TRACE_PARENT_SID`` (the chain into
    the child), derived from the import-time snapshot; the environment is
    never re-read. No other child surface receives a trace variable.

    Only variables whose targets this process actually holds propagate
    (remediation D4): admission is forced here, and a target refused at
    admission in the current process — or since disabled by a write failure
    or the cap — is dropped, because the parent already warned and the child
    must never re-receive a variable the parent could not admit (re-handing
    it would let the child re-admit against a root where sad path 12 does
    not fire). fd targets never propagate at all: the emitter holds its
    descriptors non-inheritable (the CLOEXEC posture), so the child has no
    such fd and the number would name an unrelated descriptor. The parent
    SID still propagates whenever tracing is enabled, so the chain survives
    even when every target was refused.
    """

    if not TRACING_ENABLED:
        return {}
    environment: dict[str, str] = {}
    for variable, value in _ENABLED_TARGETS.items():
        if parse_target(value)[0] == "fd":
            continue
        if _EMITTER.variable_admitted(variable):
            environment[variable] = value
    environment[PARENT_SID_VARIABLE] = _session_identity()[0]
    return environment
