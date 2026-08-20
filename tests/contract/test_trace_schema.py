"""SLICE-054 — the kernel-trace schema contract, frozen red before implementation.

ADR-031 (docs/adr/ADR-031-kernel-observability-framework.md) freezes the field
set and delegates the value vocabularies to slice time: "value vocabularies
frozen by the schema contract test at slice freeze; their numeric values are
slice work". This file IS that test. It was written against the
pre-implementation tree and must fail there (the `ranex.observability` module
does not exist yet); any later drift in the frozen sets, constants, grammars,
or the version-event variant discipline turns it red again. Schema evolution is
a new decision (an `evt` bump), never a patch that sneaks past this file.

Behavioral checks that need a live emitter (code grammar screening, the
version variant, `time` rendering, `exe` resolution) re-import
`ranex.observability` under a patched environment because the emitter reads
each trace variable exactly once at import — that single read is itself part
of the frozen contract.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pytest

import ranex.observability  # noqa: F401 — the module's existence is the contract
from ranex.observability import schema as trace_schema

TRACE_VARIABLES = ("RANEX_TRACE", "RANEX_TRACE_EVENT", "RANEX_TRACE_PARENT_SID")

# The canonical field set, in the canonical serialization order. Git trace2's
# event target (vendored as docs/adr/prior-art/ADR-031/git-tr2_tgt_event.c)
# named `event`, `sid`, and `time`; issue #34 froze the full eleven.
EXPECTED_FIELDS = (
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

# The version event is a discriminated variant: the eleven plus exactly these
# two members, admitted on `version` events only.
EXPECTED_VERSION_ONLY_FIELDS = ("evt", "exe")

# The 12 CLI dispatch groups enumerated from src/ranex/cli/main.py's argparse
# subcommands (run; gate evaluate; journal verify; suite freeze; deps fetch;
# deps approve; keygen; task dispatch/judge/merge/delegate/fanout) — verified
# against main.py at freeze time and recorded as a literal, so adding or
# removing a CLI group is a deliberate edit here.
CLI_DISPATCH_GROUPS = (
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

EXPECTED_STAGES = (
    {f"cli.{group}.{phase}" for group in CLI_DISPATCH_GROUPS for phase in ("start", "end")}
    | {"observability.emission", "observability.note"}
)

SID_COMPONENT = re.compile(r"^\d{8}T\d{6}\.\d+Z-[^/]+$")


def _fresh_observability(monkeypatch: pytest.MonkeyPatch, env: dict[str, str] | None = None):
    """Import ranex.observability afresh so it reads the patched env exactly once."""

    for name in [
        name
        for name in sys.modules
        if name == "ranex.observability" or name.startswith("ranex.observability.")
    ]:
        del sys.modules[name]
    for variable in TRACE_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    import ranex.observability  # noqa: F811 — frozen surface

    return ranex.observability


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _emit_notes(observability, *codes: str) -> None:
    for code in codes:
        observability.emit_raw(
            {
                "event": "note",
                "level": "info",
                "module": "observability",
                "stage": "observability.note",
                "code": code,
            }
        )


# --- the frozen sets and constants -------------------------------------------


def test_fields_tuple_is_frozen_in_canonical_order() -> None:
    assert trace_schema.FIELDS == EXPECTED_FIELDS
    assert isinstance(trace_schema.FIELDS, tuple)


def test_version_only_fields_are_frozen() -> None:
    assert trace_schema.VERSION_ONLY_FIELDS == EXPECTED_VERSION_ONLY_FIELDS
    assert isinstance(trace_schema.VERSION_ONLY_FIELDS, tuple)


def test_schema_constants_are_frozen() -> None:
    assert trace_schema.SCHEMA_NUMBER == 1
    assert trace_schema.MAX_LINE_LENGTH == 16384
    assert trace_schema.TRACE_BYTE_CAP == 1_048_576
    assert trace_schema.IDENTIFIER_NAME_CAP == 256


def test_event_name_registry_is_frozen() -> None:
    assert trace_schema.EVENT_NAMES == {"version", "stage", "refusal", "note"}


def test_level_registry_is_frozen() -> None:
    assert trace_schema.LEVELS == {"debug", "info", "warn", "error"}


def test_module_registry_is_frozen() -> None:
    assert trace_schema.MODULES == {"cli", "observability"}


def test_stage_registry_is_frozen_over_the_cli_dispatch_groups() -> None:
    assert trace_schema.STAGES == EXPECTED_STAGES


def test_version_only_fields_are_not_part_of_the_eleven() -> None:
    assert not set(trace_schema.VERSION_ONLY_FIELDS) & set(trace_schema.FIELDS)


# --- pinned value semantics, through the live emitter ------------------------


def test_time_is_an_epoch_float_truncated_to_milliseconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """time = time.time(), UTC, millisecond-truncated: int(now*1000)/1000.0.

    ADR-031's text governs over issue #34's review-comment "RFC 3339" reading;
    git trace2's event target — the ADR's named precedent — also renders time
    as an epoch float.
    """

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(
        monkeypatch, {"RANEX_TRACE": str(target)}
    )
    before = time.time()
    _emit_notes(observability, "cap_exceeded")
    after = time.time()

    events = _events(target)
    assert events, "an admitted target must receive events"
    stamps = [event["time"] for event in events]
    assert all(isinstance(stamp, float) for stamp in stamps)
    # Millisecond truncation: the value sits exactly on the 1e-3 grid and is
    # reconstructible by the frozen helper int(now*1000)/1000.0.
    for stamp in stamps:
        assert stamp == round(stamp, 3)
        assert stamp == int(round(stamp * 1000)) / 1000.0
        assert before - 1 <= stamp <= after + 1


def test_code_grammar_accepts_the_frozen_examples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """code = kind[:arg], arg matching [A-Za-z0-9_.=+,:-]{1,200}."""

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    accepted = (
        "exit:0",
        "exit:-1",
        "undeclared_field:len=33,sha256_8=29a80d62",
        "malformed_parent_sid:af_unix",
        "cap_exceeded",
        "target_admission_failed",
        "oversized_event:len=16385",
        "emission_refused",
    )
    _emit_notes(observability, *accepted)

    notes = {
        event["code"]
        for event in _events(target)
        if event["event"] == "note"
    }
    assert set(accepted) <= notes


def test_code_grammar_refuses_oversized_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    oversized = "exit:" + "0" * 201
    _emit_notes(observability, oversized)

    text = target.read_text(encoding="utf-8")
    assert "0" * 201 not in text, "a refused argument must never reach the stream"
    refusals = [
        event["code"] for event in _events(target) if event["event"] == "refusal"
    ]
    assert any(code.startswith("out_of_form:code:") for code in refusals), refusals


def test_version_event_is_the_discriminated_variant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The internal first write is a literal-built version event; screened
    version emissions follow variant discipline (evt/exe only on version;
    non-null stage fields on version are out-of-form)."""

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    observability.emit_raw(
        {"event": "note", "level": "warn", "module": "observability",
         "stage": "observability.note"}
    )

    events = _events(target)
    first = events[0]
    assert first["event"] == "version"
    assert list(first) == list(EXPECTED_FIELDS) + list(EXPECTED_VERSION_ONLY_FIELDS)
    assert first["evt"] == trace_schema.SCHEMA_NUMBER
    assert first["stage"] is None and first["code"] is None

    # A well-formed version emission through the screened surface is admitted.
    observability.emit_raw(
        {"event": "version", "evt": trace_schema.SCHEMA_NUMBER, "exe": "0.0.0"}
    )
    screened = [event for event in _events(target) if event["event"] == "version"]
    assert len(screened) == 2

    # Non-null stage fields on a version event are out of form.
    observability.emit_raw(
        {"event": "version", "stage": "cli.run.start",
         "evt": trace_schema.SCHEMA_NUMBER, "exe": "0.0.0"}
    )
    # evt/exe on a non-version event are undeclared fields, named as drops.
    observability.emit_raw(
        {"event": "note", "level": "info", "module": "observability",
         "stage": "observability.note", "evt": 1}
    )
    observability.emit_raw(
        {"event": "note", "level": "info", "module": "observability",
         "stage": "observability.note", "exe": "0.0.0"}
    )

    refusals = [
        event["code"] for event in _events(target) if event["event"] == "refusal"
    ]
    assert any(code.startswith("out_of_form:stage:") for code in refusals), refusals
    assert "undeclared_field:evt" in refusals
    assert "undeclared_field:exe" in refusals


def test_exe_resolves_from_this_repositories_static_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """exe = importlib.metadata.version("ranex"), falling back to the pyproject
    [project] version, last resort "unknown" — "0.0.0" here (package = false)."""

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _emit_notes(observability, "emission_refused")

    first = _events(target)[0]
    assert first["exe"] == "0.0.0"


def test_refusal_shape_descriptor_is_length_plus_eight_hex(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Shape descriptors are len=N plus the first 8 hex of SHA-256 over UTF-8."""

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    hostile_name = "Bearer Token!"
    observability.emit_raw(
        {"event": "note", "level": "info", "module": "observability",
         "stage": "observability.note", hostile_name: "irrelevant"}
    )

    refusals = [
        event["code"] for event in _events(target) if event["event"] == "refusal"
    ]
    expected = (
        "undeclared_field:len="
        f"{len(hostile_name)},sha256_8="
        f"{hashlib.sha256(hostile_name.encode('utf-8')).hexdigest()[:8]}"
    )
    assert expected in refusals, refusals


def test_sid_on_every_event_and_identifier_shape_when_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _emit_notes(observability, "exit:0")

    events = _events(target)
    assert events and all(SID_COMPONENT.match(event["sid"]) for event in events)


# --- remediation arms (dual security + test-layer review, D3 + S2 + S3) ------


def test_code_kind_registry_is_frozen() -> None:
    """D3 — `code` kinds are a closed registry, not an open identifier grammar.

    ADR-031 freezes "`code` from registries frozen in schema.py"; the open
    `[a-z_][a-z0-9_]*` kind grammar admits any grammar-shaped secret as a bare
    kind. The admissible kind vocabulary is frozen here to the emitted set;
    unknown kinds are out-of-form (behavioral refusals pinned in
    tests/unit/test_observability.py and the scrubbing attack suite). Adding a
    kind is a deliberate edit to this file.
    """

    assert trace_schema.CODE_KINDS == frozenset(
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


def test_exe_fallback_chain_covers_the_pyproject_and_unknown_branches(
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S2 — the exe resolution chain, branch by branch.

    importlib.metadata → pyproject [project] version → "unknown". The first
    branch is exercised by test_exe_resolves_from_this_repositories_static_
    version; this arm pins the other two by pointing the walker at a
    controlled location. (Coverage strengthening: green on the current tree.)
    """

    import importlib.metadata

    def not_installed(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", not_installed)

    # Pyproject branch: a fake schema.py location whose parent chain carries a
    # pyproject.toml with a [project] version.
    vendored = tmp_path / "src" / "ranex" / "observability" / "schema.py"
    vendored.parent.mkdir(parents=True)
    vendored.write_text("# sentinel for the version walk\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "ranex"\nversion = "9.8.7-remediation"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(trace_schema, "__file__", str(vendored))
    assert trace_schema.ranex_version() == "9.8.7-remediation"

    # Final fallback: a location whose parent chain carries no pyproject at
    # all — a fresh factory root, so the first arm's manifest cannot be found.
    bare = tmp_path_factory.mktemp("no-manifest") / "schema.py"
    bare.write_text("# sentinel\n", encoding="utf-8")
    monkeypatch.setattr(trace_schema, "__file__", str(bare))
    assert trace_schema.ranex_version() == "unknown"


def test_cli_dispatch_groups_derived_from_the_parser_stay_inside_the_registry() -> None:
    """S3 — a new CLI group without a schema edit turns this red.

    Derives the dispatch groups from the real argparse tree (nesting spells
    `gate.evaluate`, `task.dispatch`, …) and requires them to be a subset of
    the group names the frozen STAGES registry carries. The registry already
    pins equality today; this arm additionally catches the drift direction
    "someone added a subcommand and forgot schema.py". (Coverage
    strengthening: green on the current tree.)
    """

    import argparse

    from ranex.cli.main import build_parser

    def dispatch_groups(parser: argparse.ArgumentParser) -> set[str]:
        groups: set[str] = set()
        for action in parser._actions:
            if not isinstance(action, argparse._SubParsersAction):
                continue
            for name, subparser in action.choices.items():
                nested = dispatch_groups(subparser)
                if nested:
                    groups.update(f"{name}.{group}" for group in nested)
                else:
                    groups.add(name)
        return groups

    registered = {
        stage.removeprefix("cli.").removesuffix(".start")
        for stage in trace_schema.STAGES
        if stage.startswith("cli.") and stage.endswith(".start")
    }
    derived = dispatch_groups(build_parser())
    assert derived <= registered, (
        f"CLI dispatch groups missing from the frozen STAGES registry: "
        f"{sorted(derived - registered)}"
    )
