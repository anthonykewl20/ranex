"""Session identifiers for the kernel observability trace (ADR-031, SLICE-054).

Component grammar, per ADR-031 / git trace2 prior art:

    <yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process>

A chained SID is components joined by ``/`` — ``RANEX_TRACE_PARENT_SID``
carries the parent's SID and the child appends ``/`` plus its own component.
Unlike git, a malformed parent is never blindly prefixed: a fresh root SID is
minted and the malformed parent is recorded by shape plus digest only.
"""

from __future__ import annotations

import os
import re
import time

from ranex.observability.schema import MAX_LINE_LENGTH, shape_descriptor

# Validation grammar: the frozen SID component shape is
# <yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process> with frac of one or more
# digits (tests pin `\d+`, so a parent minted with another frac width still
# chains). The host/process charset is kept strict — a validated parent is
# republished verbatim inside every child event's `sid`, so a permissive
# `[^/]+` host would let attacker bytes ride the chain into trace lines.
# Minting always uses 6-digit microseconds.
_COMPONENT_RE = re.compile(r"\A\d{8}T\d{6}\.\d+Z-[A-Za-z0-9_-]{1,64}-\d{1,10}\Z")

_HOST_KEEP_RE = re.compile(r"[^A-Za-z0-9_-]+")


def _host_component() -> str:
    """The hostname, sanitized to the component charset.

    ``socket`` is imported lazily: the off-state import cost must not pay for
    a name resolution module it will never use for emission.
    """

    import socket

    for candidate in (
        socket.gethostname() if hasattr(socket, "gethostname") else "",
        socket.getfqdn() if hasattr(socket, "getfqdn") else "",
    ):
        kept = _HOST_KEEP_RE.sub("-", candidate or "").strip("-")
        if kept:
            return kept[:64]
    return "unknown-host"


def mint_component(now: float | None = None) -> str:
    """A fresh root component ``<yyyymmdd>T<hhmmss>.<frac>Z-<host>-<pid>``."""

    moment = time.time() if now is None else now
    utc = time.gmtime(moment)
    microseconds = int(round((moment % 1) * 1_000_000))
    if microseconds >= 1_000_000:  # rounding carried into the next second
        utc = time.gmtime(int(moment) + 1)
        microseconds -= 1_000_000
    stamp = (
        f"{utc.tm_year:04d}{utc.tm_mon:02d}{utc.tm_mday:02d}"
        f"T{utc.tm_hour:02d}{utc.tm_min:02d}{utc.tm_sec:02d}"
    )
    return f"{stamp}.{microseconds:06d}Z-{_host_component()}-{os.getpid()}"


def component_is_well_formed(component: str) -> bool:
    return bool(_COMPONENT_RE.match(component))


def sid_chain_is_well_formed(sid: str) -> bool:
    """A full SID: one or more well-formed components joined by ``/``."""

    if not sid or len(sid) > MAX_LINE_LENGTH or "\x00" in sid:
        return False
    return all(component_is_well_formed(part) for part in sid.split("/"))


def derive_session_id(
    parent_raw: str | None, now: float | None = None
) -> tuple[str, str | None]:
    """The process SID plus, when the parent was malformed, a note code.

    Returns ``(sid, malformed_parent_note)``; ``malformed_parent_note`` is
    None when ``parent_raw`` is absent or well formed, and otherwise a
    bounded code-style string naming the parent by shape plus digest only —
    never its bytes, which may carry attacker material (ADR-031 sad path 8).
    """

    component = mint_component(now)
    if parent_raw is None or parent_raw == "":
        return component, None
    if (
        sid_chain_is_well_formed(parent_raw)
        and len(parent_raw) + 1 + len(component) <= MAX_LINE_LENGTH
    ):
        return f"{parent_raw}/{component}", None
    return component, f"malformed_parent_sid:{shape_descriptor(parent_raw)}"
