"""The repair envelope: advisory FAIL detail composed at the read channel.

SLICE-092 ships the oracle-science C1+C6 result. A FAIL verdict names the
claim; the closed suite summary beside it ends at counts and non-passed
IDs. An honest agent must therefore re-run the failing tests or ingest
raw junitxml — observer- and token-expensive — to learn *what* asserted
and *where*. This module renders that detail as one bounded, advisory
packet: failing IDs, assertion text, file:line, the repro argv, and the
C2 ladder's next-rung pointers (L0 compile → L1 targeted IDs → L2 full
suite). It says WHAT failed and WHERE. It never proposes a fix.

Three boundaries hold by construction:

- **Never evidence.** Nothing here signs, verifies, or admits; the module
  imports no signing, admission, or journal code, and its bytes have no
  path into a signed record's closed shapes. Offering envelope bytes as
  evidence is refused by the ordinary admission rules, unchanged.
- **One derivation.** Failure detail comes from
  `ranex.foundation.suite_results.failure_locations`, the same parser
  that owns test identity; causes are carried verbatim from the projected
  verdict record and are never recomputed here (ADR-020's rule: the same
  closed set derived twice diverges).
- **Bounded and deterministic.** Identical inputs render byte-identical
  canonical bytes; the carried detail is capped (16 entries, 200-char
  assertions, 8 targeted IDs, 4 compiled files) with the honest totals
  kept in `failure_count`, so a bounded packet never understates a break.
  The canonical JSON bytes are the machine contract (captain DIRECT 008);
  the text rendering is derived from the same structure and is never the
  only form.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.suite_results import failure_locations

ENVELOPE_SCHEMA = "ranex-repair-envelope-v1"

#: Bounded carried detail. The caps are policy, not parsing: the parser
#: returns everything, the envelope carries the head, and failure_count
#: always names the whole so a bounded packet cannot read as a small one.
MAX_CARRIED_FAILURES = 16
MAX_ASSERTION_CHARS = 200
MAX_TARGETED_IDS = 8
MAX_COMPILED_FILES = 4

_ENVELOPE_KEYS = {
    "schema",
    "verdict",
    "verdict_record_digest",
    "causes",
    "failures",
    "failure_count",
    "repro_argv",
    "next_rung",
    "junit_retained",
}
_CAUSE_KEYS = {"claim_id", "cause", "detail"}
_FAILURE_KEYS = {"id", "assertion", "at"}
_VERDICTS = {"PASS", "FAIL"}
_RUNG = re.compile(r"^L[012] ")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_WHITESPACE = re.compile(r"\s+")


def validate_repair_envelope(value: object) -> dict[str, object]:
    """Accept only the exact envelope shape; refuse at the decode boundary."""

    if not isinstance(value, Mapping) or set(value) != _ENVELOPE_KEYS:
        raise ValueError(
            f"repair envelope must contain exactly {sorted(_ENVELOPE_KEYS)}"
        )
    if value["schema"] != ENVELOPE_SCHEMA:
        raise ValueError(f"repair envelope schema must be {ENVELOPE_SCHEMA!r}")
    verdict = value["verdict"]
    if verdict is not None and verdict not in _VERDICTS:
        raise ValueError("repair envelope verdict must be PASS, FAIL, or null")
    digest = value["verdict_record_digest"]
    if digest is not None and (
        not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None
    ):
        raise ValueError(
            "repair envelope verdict_record_digest must be a canonical digest or null"
        )

    causes = value["causes"]
    if not isinstance(causes, list):
        raise ValueError("repair envelope causes must be a list")
    for cause in causes:
        if not isinstance(cause, Mapping) or not _CAUSE_KEYS >= set(cause):
            raise ValueError(
                "repair envelope cause entries must carry claim_id and cause"
            )
        claim_id = cause["claim_id"]
        if claim_id is not None and (not isinstance(claim_id, str) or not claim_id):
            raise ValueError(
                "repair envelope cause claim_id must be a non-empty string or null"
            )
        if not isinstance(cause["cause"], str) or not cause["cause"]:
            raise ValueError("repair envelope cause kind must be a non-empty string")

    failures = value["failures"]
    if not isinstance(failures, list):
        raise ValueError("repair envelope failures must be a list")
    for failure in failures:
        if not isinstance(failure, Mapping) or set(failure) != _FAILURE_KEYS:
            raise ValueError(
                f"repair envelope failure entries must contain exactly {sorted(_FAILURE_KEYS)}"
            )
        if any(not isinstance(failure[field], str) for field in _FAILURE_KEYS):
            raise ValueError("repair envelope failure fields must be strings")

    count = value["failure_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < len(failures):
        raise ValueError("repair envelope failure_count must cover every carried failure")

    if not isinstance(value["repro_argv"], str):
        raise ValueError("repair envelope repro_argv must be a string")
    rungs = value["next_rung"]
    if not isinstance(rungs, list) or any(
        not isinstance(rung, str) or _RUNG.match(rung) is None for rung in rungs
    ):
        raise ValueError("repair envelope rungs must be L0/L1/L2 command pointers")
    if not isinstance(value["junit_retained"], bool):
        raise ValueError("repair envelope junit_retained must be a boolean")
    return dict(value)


def _bounded_failures(detail: Mapping[str, object]) -> list[dict[str, str]]:
    failures = [
        {
            "id": str(failure["id"]),
            "assertion": _WHITESPACE.sub(" ", str(failure["assertion"])).strip()[
                :MAX_ASSERTION_CHARS
            ],
            "at": str(failure["at"]),
        }
        for failure in detail["failures"]  # type: ignore[index]
    ]
    return failures[:MAX_CARRIED_FAILURES]


def next_rung_lines(
    repro_argv: str, failures: Sequence[Mapping[str, str]]
) -> list[str]:
    """The C2 ladder as pointers: what to run next, never what to change.

    L0 compiles the files the failures named, L1 re-runs only the IDs this
    envelope carries, L2 is the full governed argv. L0 appears only when a
    located file exists and the repro argv names a python interpreter —
    the one command shape the ladder's first rung is known to hold for.
    The orchestrator that would *run* these is out of scope (C2); these
    are advisory pointers an agent or operator may follow.
    """

    if not repro_argv:
        return []
    rungs: list[str] = []
    tokens = repro_argv.split()
    located = sorted(
        {failure["at"].rsplit(":", 1)[0] for failure in failures if failure.get("at")}
    )
    if located and tokens and tokens[0].rsplit("/", 1)[-1].startswith("python"):
        rungs.append(
            f"L0 {tokens[0]} -m py_compile {' '.join(located[:MAX_COMPILED_FILES])}"
        )
    targeted = [failure["id"] for failure in failures if failure.get("id")]
    if targeted:
        rungs.append(f"L1 {repro_argv} {' '.join(targeted[:MAX_TARGETED_IDS])}")
    rungs.append(f"L2 {repro_argv}")
    return rungs


def _envelope(
    *,
    verdict: str | None,
    verdict_record_digest: str | None,
    causes: list[dict[str, str | None]],
    detail: Mapping[str, object] | None,
    repro_argv: str,
    failure_count: int,
) -> dict[str, object]:
    failures = [] if detail is None else _bounded_failures(detail)
    envelope: dict[str, object] = {
        "schema": ENVELOPE_SCHEMA,
        "verdict": verdict,
        "verdict_record_digest": verdict_record_digest,
        "causes": causes,
        "failures": failures,
        "failure_count": failure_count,
        "repro_argv": repro_argv,
        "next_rung": next_rung_lines(repro_argv, failures),
        "junit_retained": detail is not None,
    }
    return validate_repair_envelope(envelope)


def envelope_from_suite(
    *, repro_argv: str, junit_bytes: bytes | None, reporter: str = "pytest-junit"
) -> dict[str, object]:
    """Render the delegate capture: suite detail without a verdict.

    The delegate runs the suite but judges nothing, so the packet it
    retains says so: no verdict, no causes, no record binding — only the
    bounded failure detail, the repro argv, and the ladder.
    """

    detail = (
        None if junit_bytes is None else failure_locations(junit_bytes, reporter=reporter)
    )
    count = 0 if detail is None else int(detail["non_passed_count"])  # type: ignore[index]
    return _envelope(
        verdict=None,
        verdict_record_digest=None,
        causes=[],
        detail=detail,
        repro_argv=repro_argv,
        failure_count=count,
    )


def envelope_from_projection(
    *,
    projected: Mapping[str, Any],
    evidence: Sequence[Any],
    junit_bytes: bytes | None,
    reporter: str = "pytest-junit",
) -> dict[str, object]:
    """Render at the ADR-019/020 projection boundary, beside the verdict.

    Causes and the verdict travel verbatim from the projected record;
    `verdict_record_digest` binds this packet to exactly the signed
    verdict published beside it, so an honest reader can detect
    accidental divergence without a fourth signing domain. The repro argv
    and the no-junit failure count come from the freshest admitted suite
    record — the signed evidence the gate itself decided on.
    """

    causes = [
        {key: cause[key] for key in _CAUSE_KEYS if key in cause}
        for cause in projected["causes"]
    ]
    suite_records = [
        item for item in evidence if getattr(item, "suite_results", None) is not None
    ]
    repro_argv = str(suite_records[-1].command) if suite_records else ""
    summary_count = 0
    if suite_records:
        non_passed = suite_records[-1].suite_results["non_passed"]  # type: ignore[index]
        summary_count = len(non_passed)
    detail = (
        None
        if junit_bytes is None
        else failure_locations(junit_bytes, reporter=reporter)
    )
    count = (
        summary_count if detail is None else int(detail["non_passed_count"])  # type: ignore[index]
    )
    return _envelope(
        verdict=str(projected["verdict"]),
        verdict_record_digest=str(projected["record_digest"]),
        causes=causes,
        detail=detail,
        repro_argv=repro_argv,
        failure_count=count,
    )


def envelope_packet_bytes(envelope: Mapping[str, object]) -> bytes:
    """Canonical JSON plus newline: the bytes an agent ingests."""

    validate_repair_envelope(envelope)
    return canonical_json_bytes(dict(envelope)) + b"\n"


def render_packet_text(envelope: Mapping[str, object]) -> str:
    """The packet as one bounded text block, derived from the structure.

    Secondary form (captain DIRECT 008): harnesses that surface only a
    string still show the same facts the structured bytes carry, and any
    consumer that can read JSON should read `envelope_packet_bytes`.
    """

    validate_repair_envelope(envelope)
    lines: list[str] = []
    verdict = envelope["verdict"]
    lines.append(
        f"VERDICT {verdict}" if verdict else "VERDICT none (no evaluation composed)"
    )
    for cause in envelope["causes"]:  # type: ignore[index]
        detail = cause.get("detail")
        suffix = f" ({detail})" if detail else ""
        lines.append(f"CAUSE {cause['claim_id']}: {cause['cause']}{suffix}")
    lines.append(f"FAILURES {len(envelope['failures'])}/{envelope['failure_count']}")  # type: ignore[index]
    for failure in envelope["failures"]:  # type: ignore[index]
        parts = [failure["id"]]
        if failure["assertion"]:
            parts.append(failure["assertion"])
        if failure["at"]:
            parts.append(failure["at"])
        lines.append("- " + " | ".join(parts))
    if envelope["repro_argv"]:
        lines.append(f"REPRO {envelope['repro_argv']}")
    for rung in envelope["next_rung"]:  # type: ignore[index]
        lines.append(f"NEXT {rung}")
    if not envelope["junit_retained"]:
        lines.append("NOTE junit not retained; no assertion/file detail available")
    return "\n".join(lines)
