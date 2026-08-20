"""SLICE-054 — kernel-trace emitter mechanics, frozen red before implementation.

Unit contract for src/ranex/observability/ per ADR-031 and issue #34: the
trace2-subset target grammar, target admission outside governed outputs,
open-once descriptors, SID chaining, positive-allowlist redaction, the
refusal-not-rotation byte cap, single-warning write-failure disable, the
one-env-read off state, independent two-target routing, and canonical
serialization.

Because the emitter reads each trace variable exactly once at import, every
behavioral test re-imports `ranex.observability` under a patched environment
(`_fresh_observability`). Public-surface note: the frozen signatures are the
names `parse_target`, `derive_session_id`, and `screen_event` plus the
`ranex.observability` constants/functions; everything here asserts behavior
through those surfaces rather than pinning private return shapes. This file
was written against the pre-implementation tree and must fail there.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import threading
from collections import Counter
from pathlib import Path

import pytest

import ranex.observability  # noqa: F401 — frozen surface
from ranex.observability import schema as trace_schema
from ranex.observability.emitter import parse_target  # noqa: F401 — frozen surface
from ranex.observability.redaction import screen_event  # noqa: F401 — frozen surface
from ranex.observability.sid import derive_session_id  # noqa: F401 — frozen surface

TRACE_VARIABLES = ("RANEX_TRACE", "RANEX_TRACE_EVENT", "RANEX_TRACE_PARENT_SID")
FIELDS = (
    "event", "sid", "time", "level", "module", "stage", "subject_digest",
    "duration_us", "hierarchy", "child_id", "code",
)
SID_COMPONENT = re.compile(r"^\d{8}T\d{6}\.\d+Z-[^/]+$")
SHAPE_DESCRIPTOR = re.compile(r"len=\d+,sha256_8=[0-9a-f]{8}")


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


def _note(observability, **extra) -> None:
    payload: dict[str, object] = {
        "event": "note",
        "level": "info",
        "module": "observability",
        "stage": "observability.note",
    }
    payload.update(extra)
    observability.emit_raw(payload)


def _refusals(path: Path) -> list[str]:
    return [event["code"] for event in _events(path) if event["event"] == "refusal"]


def _git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "file.txt").write_text("subject\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for key, value in (("user.email", "t@example.invalid"), ("user.name", "test")):
        subprocess.run(["git", "-C", str(path), "config", key, value], check=True)
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "initial"], check=True)
    return path


class _LowFd:
    """Pin a descriptor to a single-digit fd number, restoring what was there.

    The fd target grammar admits single digits 2-9 only, so tests that need a
    real fd target move their descriptor onto a fixed low number for the
    duration of one import+emission cycle.
    """

    def __init__(self, source_fd: int, number: int) -> None:
        self.source_fd = source_fd
        self.number = number
        self.saved: int | None = None

    def __enter__(self) -> int:
        try:
            fcntl.fcntl(self.number, fcntl.F_GETFD)
            self.saved = os.dup(self.number)
        except OSError:
            self.saved = None
        os.dup2(self.source_fd, self.number)
        return self.number

    def __exit__(self, *args: object) -> None:
        try:
            os.close(self.number)
        except OSError:
            pass  # the emitter may have closed the descriptor when disabling
        if self.saved is not None:
            os.dup2(self.saved, self.number)
            os.close(self.saved)


# --- the target grammar -------------------------------------------------------


@pytest.mark.parametrize("value", ["", "0", "false"])
def test_off_values_leave_tracing_disabled_with_zero_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str], value: str
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": value})
    assert observability.TRACING_ENABLED is False
    assert observability.emit_raw({"event": "note"}) is None
    _note(observability)
    observability.stage_begin("cli.keygen.start")
    observability.stage_end("cli.keygen.end", "exit:0")
    assert not target.exists()
    assert capfd.readouterr().out == ""
    assert capfd.readouterr().err == ""


def test_unset_leaves_tracing_disabled(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    observability = _fresh_observability(monkeypatch)
    assert observability.TRACING_ENABLED is False
    _note(observability)
    assert capfd.readouterr().err == ""


@pytest.mark.parametrize("value", ["1", "true"])
def test_stderr_target_writes_jsonl_to_stderr(
    monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str], value: str
) -> None:
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": value})
    assert observability.TRACING_ENABLED is True
    _note(observability)
    captured = capfd.readouterr()
    assert captured.out == ""
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert lines, "an admitted stderr target must receive the stream"
    first = json.loads(lines[0])
    assert first["event"] == "version"


def test_fd_target_writes_to_the_already_open_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "fd-trace.jsonl"
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with _LowFd(descriptor, number=4) as pinned:
            observability = _fresh_observability(
                monkeypatch, {"RANEX_TRACE": str(pinned)}
            )
            assert observability.TRACING_ENABLED is True
            _note(observability)
    finally:
        os.close(descriptor)

    events = _events(target)
    assert events[0]["event"] == "version"
    assert events[-1]["event"] == "note"


def test_file_target_appends_and_directory_target_gets_one_file_per_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file_target = tmp_path / "trace.jsonl"
    first = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(file_target)})
    _note(first)
    second = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(file_target)})
    _note(second)
    events = _events(file_target)
    assert [event["event"] for event in events].count("version") == 2, "append, never truncate"

    directory = tmp_path / "trace-dir"
    directory.mkdir()
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(directory)})
    _note(observability)
    files = sorted(path for path in directory.iterdir() if path.is_file())
    assert len(files) == 1, "one file per process, named by the last SID component"
    events = _events(files[0])
    assert events[0]["event"] == "version"
    assert files[0].name == events[0]["sid"].rsplit("/", 1)[-1]


@pytest.mark.parametrize(
    "value",
    [
        "relative.jsonl",
        "af_unix:/tmp/ranex-under-test.sock",
        "af_unix:dgram:/tmp/ranex-under-test.sock",
        "af_unix:stream:/tmp/ranex-under-test.sock",
        "10",
        "stdout",
    ],
)
def test_invalid_target_values_warn_with_shape_descriptors_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
    value: str,
) -> None:
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": value})
    _note(observability)
    captured = capfd.readouterr()
    lines = [line for line in captured.err.splitlines() if line.strip()]
    assert len(lines) == 1, f"exactly one warning line, got {lines!r}"
    warning = lines[0]
    assert "RANEX_TRACE" in warning
    assert SHAPE_DESCRIPTOR.search(warning)
    assert value not in warning, "case-(b) refusals never echo the raw value"


# --- target admission --------------------------------------------------------


def test_target_inside_the_governed_repository_is_refused_naming_the_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """The emitter discovers the governed root of its cwd and refuses targets
    under it — a trace inside the governed tree dirties the subject (ADR-031
    sad path 12). A well-formed absolute target failing admission is a case-(a)
    refusal: the full path is named."""

    repo = _git_repo(tmp_path / "governed")
    target = repo / "trace.jsonl"
    monkeypatch.chdir(repo)
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability)

    assert not target.exists()
    warning = capfd.readouterr().err
    assert str(target) in warning
    assert "RANEX_TRACE" in warning


def test_symlinked_target_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    destination = tmp_path / "real.jsonl"
    destination.write_text("", encoding="utf-8")
    link = tmp_path / "link.jsonl"
    link.symlink_to(destination)
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(link)})
    _note(observability)

    assert destination.read_text(encoding="utf-8") == ""
    warning = capfd.readouterr().err
    assert str(link) in warning


def test_target_hardlinked_to_a_governed_file_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """Device+inode aliasing: a second name outside the tree for a file inside
    it is the governed bytes by another route."""

    repo = _git_repo(tmp_path / "governed")
    governed = repo / "file.txt"
    alias = tmp_path / "alias.jsonl"
    os.link(governed, alias)
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(alias)})
    _note(observability)

    warning = capfd.readouterr().err
    assert str(alias) in warning
    assert governed.read_text(encoding="utf-8") == "subject\n"


def test_target_is_written_only_through_the_once_opened_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After admission the path is never re-resolved: a rename plus symlink
    swap at the target path cannot redirect later writes."""

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability)
    first_size = target.stat().st_size

    moved = tmp_path / "moved.jsonl"
    os.rename(target, moved)
    decoy = tmp_path / "decoy.jsonl"
    decoy.write_text("", encoding="utf-8")
    target.symlink_to(decoy)

    _note(observability)
    assert moved.stat().st_size > first_size, "writes continue into the held descriptor"
    assert decoy.read_text(encoding="utf-8") == ""
    assert target.is_symlink()


# --- session identifiers ------------------------------------------------------


def test_session_id_component_format(monkeypatch: pytest.MonkeyPatch) -> None:
    observability = _fresh_observability(monkeypatch)
    assert SID_COMPONENT.match(observability.SESSION_ID)


def test_well_formed_parent_sid_chains_with_a_slash_separator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    parent = "20260818T060601.512Z-ranex-box-4242"
    observability = _fresh_observability(
        monkeypatch, {"RANEX_TRACE": str(target), "RANEX_TRACE_PARENT_SID": parent}
    )
    _note(observability)

    for event in _events(target):
        assert event["sid"].startswith(parent + "/")
        component = event["sid"].rsplit("/", 1)[-1]
        assert SID_COMPONENT.match(component)


def test_malformed_parent_sid_mints_a_fresh_root_and_notes_the_shape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """Git blindly prefixes any non-empty parent (its recorded weakness);
    Ranex validates, mints a fresh root, and records the malformed shape."""

    target = tmp_path / "trace.jsonl"
    malformed = "not a sid ::: with hostile bytes rnxs-malformed-parent"
    observability = _fresh_observability(
        monkeypatch, {"RANEX_TRACE": str(target), "RANEX_TRACE_PARENT_SID": malformed}
    )
    _note(observability)

    events = _events(target)
    assert all(SID_COMPONENT.match(event["sid"]) for event in events)
    noted = [
        event["code"]
        for event in events
        if event["event"] in ("note", "refusal")
        and str(event["code"]).startswith("malformed_parent_sid:")
    ]
    assert noted, "the malformed parent must be recorded as an event"
    text = target.read_text(encoding="utf-8")
    assert malformed not in text
    assert malformed not in capfd.readouterr().err


# --- the positive allowlist ---------------------------------------------------


def test_undeclared_field_is_dropped_and_named_when_identifier_shaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability, bearer_token="tok-rnxs-plant-0001")
    events = _events(target)

    note = next(event for event in events if event["event"] == "note")
    assert "bearer_token" not in note
    assert list(note) == list(FIELDS)
    assert "undeclared_field:bearer_token" in _refusals(target)
    assert "tok-rnxs-plant-0001" not in target.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "name",
    [
        "Bearer Token!",  # not [a-z_][a-z0-9_]*-form
        "z" * 300,  # grammar-shaped but over the 200-char naming cap
    ],
    ids=["non-grammar", "oversized"],
)
def test_hostile_undeclared_field_names_are_reported_by_shape_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability, **{name: "value-rnxs-plant-0002"})

    text = target.read_text(encoding="utf-8")
    assert name not in text
    assert "value-rnxs-plant-0002" not in text
    refusals = _refusals(target)
    expected = (
        f"undeclared_field:len={len(name)},sha256_8="
        f"{hashlib.sha256(name.encode('utf-8')).hexdigest()[:8]}"
    )
    assert expected in refusals


def test_version_only_members_are_undeclared_on_non_version_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability, evt=1)
    _note(observability, exe="0.0.0")

    assert "undeclared_field:evt" in _refusals(target)
    assert "undeclared_field:exe" in _refusals(target)


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("level", "VERBOSE"),
        ("stage", "cli.run.middle"),
        ("module", "kernel"),
        ("subject_digest", "sha256:not-hex-at-all"),
        ("duration_us", "fast"),
        ("code", "exit:not a code, spaces; pipes"),
    ],
)
def test_out_of_form_values_are_refused_by_shape_and_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, bad: str
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability, **{field: bad})

    text = target.read_text(encoding="utf-8")
    assert bad not in text
    assert any(code.startswith(f"out_of_form:{field}:") for code in _refusals(target))


# --- emitter discipline -------------------------------------------------------


def test_byte_cap_refuses_rather_than_rotates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})

    saw_cap_refusal = False
    for index in range(60_000):
        _note(observability)
        if index % 250 == 0 and index > 0:
            saw_cap_refusal = any(
                code == "cap_exceeded" for code in _refusals(target)
            )
            if saw_cap_refusal:
                break
    assert saw_cap_refusal, "the stream must reach the reserved cap refusal"

    events = _events(target)
    cap_at = max(
        index for index, event in enumerate(events) if event["code"] == "cap_exceeded"
    )
    assert cap_at == len(events) - 1, "nothing is written after the cap refusal"
    assert target.stat().st_size <= trace_schema.TRACE_BYTE_CAP

    size_after = target.stat().st_size
    for _ in range(50):
        _note(observability)
    assert target.stat().st_size == size_after, "a capped target stays stopped"


def test_target_with_no_remaining_capacity_is_refused_at_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """A target whose remaining capacity is below one max line is refused at
    admission — no bytes written, the full path named (ADR-031 sad path 9's
    setup-time refusal, instantiated against the frozen cap)."""

    target = tmp_path / "trace.jsonl"
    filler = b'{"prefill":1}\n'
    prefill = filler * (trace_schema.TRACE_BYTE_CAP // len(filler))
    target.write_bytes(prefill)
    assert target.stat().st_size > trace_schema.TRACE_BYTE_CAP - trace_schema.MAX_LINE_LENGTH
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability)

    assert target.stat().st_size == len(prefill), "nothing may be appended"
    warning = capfd.readouterr().err
    assert "RANEX_TRACE" in warning
    assert str(target) in warning, "a well-formed absolute target is named"


def test_near_cap_target_consumes_the_reserved_refusal_and_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refusal, not rotation: the next event that would exceed cap-minus-
    reserved consumes the one reserved refusal event and the target stops."""

    target = tmp_path / "trace.jsonl"
    filler = b'{"prefill":1}\n'
    budget = trace_schema.TRACE_BYTE_CAP - 300
    prefill = filler * (budget // len(filler))
    target.write_bytes(prefill)
    remaining = trace_schema.TRACE_BYTE_CAP - len(prefill)
    assert 300 <= remaining < trace_schema.MAX_LINE_LENGTH
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability)
    _note(observability)

    appended = target.read_bytes()[len(prefill):]
    events = [json.loads(line) for line in appended.splitlines() if line]
    assert events, "the reserved refusal event must be written"
    assert all(event["event"] == "refusal" for event in events), (
        "past the cap the answer is refusal, never more events"
    )
    assert events[-1]["code"] == "cap_exceeded"
    assert target.stat().st_size <= trace_schema.TRACE_BYTE_CAP

    frozen_size = target.stat().st_size
    for _ in range(20):
        _note(observability)
    assert target.stat().st_size == frozen_size, "a capped target stays stopped"


def test_write_failure_disables_the_target_with_one_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """A full, non-blocking pipe: one warning, target disabled, never a retry,
    never a crash of the emitting process."""

    read_end, write_end = os.pipe()
    os.set_blocking(write_end, False)
    try:
        # Fill the pipe first: an empty pipe would accept the first write and
        # prove nothing. Full and non-blocking, every write raises.
        while True:
            try:
                os.write(write_end, b"x" * 65536)
            except BlockingIOError:
                break
        with _LowFd(write_end, number=4) as pinned:
            observability = _fresh_observability(
                monkeypatch, {"RANEX_TRACE": str(pinned)}
            )
            assert observability.TRACING_ENABLED is True
            _note(observability)  # must not raise and must not block
            first = capfd.readouterr()
            warnings = [line for line in first.err.splitlines() if line.strip()]
            assert len(warnings) == 1
            assert "RANEX_TRACE" in warnings[0]

            _note(observability)
            _note(observability)
            again = capfd.readouterr()
            assert again.err == "", "a disabled target warns once, never again"
    finally:
        os.close(read_end)
        os.close(write_end)


class _CountingEnviron:
    """Delegate os.environ while counting reads of the trace variables."""

    def __init__(self, wrapped) -> None:
        self._wrapped = wrapped
        self.counts: Counter[str] = Counter()

    def _track(self, key) -> None:
        if isinstance(key, str) and key in TRACE_VARIABLES:
            self.counts[key] += 1

    def __getitem__(self, key):
        self._track(key)
        return self._wrapped[key]

    def get(self, key, default=None):
        self._track(key)
        return self._wrapped.get(key, default)

    def __contains__(self, key):
        self._track(key)
        return key in self._wrapped

    def __setitem__(self, key, value):
        self._wrapped[key] = value

    def __delitem__(self, key):
        del self._wrapped[key]

    def __iter__(self):
        return iter(self._wrapped)

    def __len__(self):
        return len(self._wrapped)

    def keys(self):
        return self._wrapped.keys()

    def items(self):
        return self._wrapped.items()

    def values(self):
        return self._wrapped.values()

    def copy(self):
        return self._wrapped.copy()


def test_off_state_reads_each_trace_variable_exactly_once_at_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One env read per variable at import, and never again: the disabled
    emission path touches nothing. MonkeyPatch's own env helpers read through
    the wrapper, so the removals go directly through the real environ."""

    for name in [
        name
        for name in sys.modules
        if name == "ranex.observability" or name.startswith("ranex.observability.")
    ]:
        del sys.modules[name]

    real_environ = os.environ
    prior = {variable: real_environ.get(variable) for variable in TRACE_VARIABLES}
    counter = _CountingEnviron(real_environ)
    monkeypatch.setattr(os, "environ", counter)
    for variable in TRACE_VARIABLES:
        real_environ.pop(variable, None)
    try:
        import ranex.observability as observability

        assert observability.TRACING_ENABLED is False
        assert counter.counts["RANEX_TRACE"] == 1
        assert counter.counts["RANEX_TRACE_EVENT"] == 1
        assert counter.counts["RANEX_TRACE_PARENT_SID"] == 1

        counter.counts.clear()
        assert observability.emit_raw({"event": "note"}) is None
        observability.stage_begin("cli.keygen.start")
        observability.stage_end("cli.keygen.end", "exit:0")
        assert not counter.counts, f"emission re-read env: {dict(counter.counts)}"
    finally:
        monkeypatch.undo()
        for variable, value in prior.items():
            if value is None:
                real_environ.pop(variable, None)
            else:
                real_environ[variable] = value


def test_version_event_is_the_first_write_on_each_admitted_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_target = tmp_path / "one.jsonl"
    second_target = tmp_path / "two.jsonl"
    observability = _fresh_observability(
        monkeypatch,
        {"RANEX_TRACE": str(first_target), "RANEX_TRACE_EVENT": str(second_target)},
    )
    _note(observability)

    for target in (first_target, second_target):
        events = _events(target)
        assert events[0]["event"] == "version"
        assert events[0]["evt"] == trace_schema.SCHEMA_NUMBER
        assert events[-1]["event"] == "note"


def test_two_targets_route_independently_with_per_target_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    good = tmp_path / "good.jsonl"
    observability = _fresh_observability(
        monkeypatch,
        {"RANEX_TRACE": str(good), "RANEX_TRACE_EVENT": "af_unix:not-a-target"},
    )
    _note(observability)

    events = _events(good)
    assert events and events[-1]["event"] == "note"
    warnings = [line for line in capfd.readouterr().err.splitlines() if line.strip()]
    assert len(warnings) == 1
    assert "RANEX_TRACE_EVENT" in warnings[0]
    assert "af_unix" not in warnings[0], "case-(b) refusals never echo the raw value"


def test_events_serialize_canonically_with_all_eleven_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    observability.stage_begin("cli.keygen.start")
    observability.stage_end("cli.keygen.end", "exit:0")
    _note(observability, subject_digest="ab" * 32)

    raw = target.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    for line in raw.splitlines():
        event = json.loads(line)
        assert line == json.dumps(event, separators=(",", ":")), "no extra whitespace"
        expected = list(FIELDS)
        if event["event"] == "version":
            expected += ["evt", "exe"]
        assert list(event) == expected


def test_stage_begin_and_stage_end_emit_stage_events_with_duration_and_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    observability.stage_begin("cli.keygen.start")
    observability.stage_end("cli.keygen.end", "exit:0")

    stages = [event for event in _events(target) if event["event"] == "stage"]
    assert [event["stage"] for event in stages] == ["cli.keygen.start", "cli.keygen.end"]
    assert stages[0]["duration_us"] is None
    assert isinstance(stages[1]["duration_us"], int) and stages[1]["duration_us"] >= 0
    assert stages[1]["code"] == "exit:0"


# --- remediation arms (dual security + test-layer review, D1-D5 + S5) --------
#
# Authored red against the defective tree at 46c538c02 per test-debug
# discipline: every arm below fails there, before any fix is designed.


def _run_with_watchdog(action, seconds: float = 10.0):
    """Run `action` in a daemon thread, failing (never hanging) past the bound.

    The emitter must never block (ADR-031 sad path 3), so a hang is a test
    FAILURE, not a suite hang: the watchdog daemon thread is abandoned if the
    bound trips and dies with the process at exit.
    """

    outcome: dict[str, object] = {}

    def run() -> None:
        try:
            action()
            outcome["done"] = True
        except BaseException as exc:  # noqa: BLE001 - reported, never swallowed
            outcome["error"] = exc

    thread = threading.Thread(target=run, daemon=True, name="ranex-trace-watchdog")
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        pytest.fail(
            f"trace emission blocked for more than {seconds}s — the emitter must "
            "never block (ADR-031 sad path 3: full or blocking fd → one warning, "
            "target disabled, run proceeds)"
        )
    if "error" in outcome:
        raise outcome["error"]
    assert outcome.get("done") is True


def test_full_blocking_fd_target_never_blocks_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """D1 — a blocking pipe fd whose reader never drains must not hang.

    The pipe's write end is left in the default BLOCKING state after being
    filled to capacity, exactly the operator condition ADR-031 sad path 3
    names. The first emission (version write) must return promptly, disable
    the target with exactly one warning, and never retry.
    """

    read_end, write_end = os.pipe()
    try:
        # Fill the pipe without ever blocking: flip to non-blocking only for
        # the fill, then restore the default blocking state under test.
        os.set_blocking(write_end, False)
        while True:
            try:
                os.write(write_end, b"x" * 65536)
            except BlockingIOError:
                break
        os.set_blocking(write_end, True)

        with _LowFd(write_end, number=4) as pinned:
            observability = _fresh_observability(
                monkeypatch, {"RANEX_TRACE": str(pinned)}
            )
            assert observability.TRACING_ENABLED is True

            _run_with_watchdog(lambda: _note(observability))

            first = capfd.readouterr()
            warnings = [line for line in first.err.splitlines() if line.strip()]
            assert len(warnings) == 1, f"exactly one warning, got {warnings!r}"
            assert "RANEX_TRACE" in warnings[0]

            # Disabled: further emissions are silent no-ops, never retries.
            _run_with_watchdog(lambda: _note(observability))
            _run_with_watchdog(lambda: _note(observability))
            again = capfd.readouterr()
            assert again.err == "", "a disabled target warns once, never again"
    finally:
        os.close(read_end)
        try:
            os.close(write_end)
        except OSError:
            pass  # _LowFd already closed the dup'd number


def test_socket_fd_target_is_refused_at_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """D2 — a socket is an exfiltration channel and is refused outright.

    `af_unix:` target VALUES are refused by the grammar; an already-open
    socket fd must not slip past admission through the fd form (ADR-031:
    "a socket is an exfiltration channel out of a confined tree"). Refusal
    means: one warning naming the variable and the fd, the target disabled,
    and not one byte reaching the socket — never a crash.
    """

    peer, writer = socket.socketpair()
    try:
        with _LowFd(writer.fileno(), number=4) as pinned:
            observability = _fresh_observability(
                monkeypatch, {"RANEX_TRACE": str(pinned)}
            )
            assert observability.TRACING_ENABLED is True
            _run_with_watchdog(lambda: _note(observability))

            warnings = [line for line in capfd.readouterr().err.splitlines() if line.strip()]
            assert len(warnings) == 1, f"exactly one admission warning, got {warnings!r}"
            assert "RANEX_TRACE" in warnings[0]
            assert "fd" in warnings[0]

            peer.setblocking(False)
            try:
                leaked = peer.recv(65536)
            except BlockingIOError:
                leaked = b""
            assert leaked == b"", (
                f"a socket target received {leaked!r}; sockets are refused, "
                "never written"
            )

            _run_with_watchdog(lambda: _note(observability))
            after = capfd.readouterr()
            assert after.err == "", "a refused target warns once, never again"
    finally:
        peer.close()
        writer.close()


def test_code_values_outside_the_closed_vocabulary_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D3 — `code` is a closed registry, not an open grammar.

    ADR-031: "`code` from registries frozen in schema.py … any value outside
    its closed form is refused and represented by shape plus digest, never by
    its bytes." The bare-identifier kind and the 200-char arg charset admit
    grammar-shaped secrets today — a bare 64-hex token (bare kind), a bearer
    token behind a legitimate `exit:` kind, and unknown kinds (`zzz`) all
    serialize verbatim. Each must instead be refused with an
    `out_of_form:code:<shape>` refusal; the frozen admissible kinds are pinned
    separately in tests/contract/test_trace_schema.py.
    """

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    hex_token = "d" * 64
    bearer = "rnxs-bearer-4d1f0c2e"
    hostile_codes = [
        hex_token,                # bare 64-hex: matches the open kind grammar today
        f"exit:{bearer}",         # arg-carried bearer token behind a real kind
        "zzz",                    # unknown bare kind
        "zzz:arg",                # unknown kind with arg
    ]
    for code in hostile_codes:
        _note(observability, code=code)

    text = target.read_text(encoding="utf-8")
    assert hex_token not in text
    assert bearer not in text
    assert "zzz" not in text

    refusals = _refusals(target)
    code_refusals = [code for code in refusals if code.startswith("out_of_form:code:")]
    assert len(code_refusals) == 4, (
        f"all four hostile codes refused by shape+digest, got {refusals!r}"
    )
    assert all(SHAPE_DESCRIPTOR.search(code) for code in code_refusals)


def test_controller_environment_excludes_a_target_refused_at_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D4(a) — a target refused at admission must not be re-propagated.

    `controller_trace_environment()` snapshots the import-time enabled
    variables and never revisits them, so a target the CURRENT process has
    since refused (here: a well-formed absolute path inside the cwd's
    governed root) is still handed to the confinement controller child —
    which then re-admits it against a session cwd with no governed root,
    silently undoing ADR-031 sad path 12 on the confinement path. The child
    seam must only ever carry variables whose targets this process actually
    holds.
    """

    repo = _git_repo(tmp_path / "governed")
    target = repo / "trace.jsonl"
    monkeypatch.chdir(repo)
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    assert observability.TRACING_ENABLED is True

    observability.emit_raw(
        {
            "event": "note",
            "level": "info",
            "module": "observability",
            "stage": "observability.note",
        }
    )
    assert not target.exists(), "construction check: the in-repo target was refused here"

    environment = observability.controller_trace_environment()
    assert "RANEX_TRACE" not in environment, (
        f"the controller seam re-propagates a refused target: {environment!r}"
    )


def test_anchor_seam_refuses_a_target_inside_the_anchored_governed_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """D4(b) — admission must be anchorable to the session's governed root.

    The confinement controller child's cwd is a disposable session directory
    with no `.git` at or above it, so cwd-based root discovery finds nothing
    and ADR-031 sad path 12 (a target inside the governed repository root is
    refused before the first write) silently does not apply in the child. The
    child KNOWS the session's governed root, so the emitter must expose an
    explicit anchor seam — prescribed here as
    `ranex.observability.emitter.set_governed_root(path)`, called before the
    first emission. The mechanism behind the seam is implementer-free; the
    observable is frozen: with cwd outside any repository but the anchored
    root a governed repository, a target inside that repository is refused,
    naming the full path.
    """

    repo = _git_repo(tmp_path / "governed")
    target = repo / "trace.jsonl"
    outside = tmp_path  # cwd for this test: no .git at or above it
    monkeypatch.chdir(outside)

    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    assert observability.TRACING_ENABLED is True

    import ranex.observability.emitter as emitter_module

    assert hasattr(emitter_module, "set_governed_root"), (
        "the emitter must expose the governed-root anchor seam "
        "(ranex.observability.emitter.set_governed_root) for the confinement "
        "controller child, whose cwd resolves to no governed root"
    )
    emitter_module.set_governed_root(repo)

    _note(observability)

    assert not target.exists(), "the anchored-root refusal must fire before any write"
    warning = capfd.readouterr().err
    assert str(target) in warning
    assert "RANEX_TRACE" in warning


def test_anchor_seam_admits_a_target_outside_every_governed_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D4(c) — the anchor must not over-refuse.

    With the anchor naming a governed repository and cwd outside any
    repository, a target under neither must still be admitted and written:
    anchoring exists to restore sad path 12 in the confinement child, not to
    refuse every target once any root is anchored.
    """

    repo = _git_repo(tmp_path / "governed")
    target = tmp_path / "outside" / "trace.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)  # no .git at or above: cwd resolves to no root

    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    import ranex.observability.emitter as emitter_module

    emitter_module.set_governed_root(repo)

    _note(observability)

    events = _events(target)
    assert events and events[0]["event"] == "version"
    assert events[-1]["event"] == "note"


def test_shape_descriptor_type_bucket_is_fixed_not_the_class_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """D5 — the non-JSON-type fallback must not echo `type(value).__name__`.

    A class name is attacker-choosable ascii; interpolating it into the
    refusal's shape descriptor lets hostile bytes ride a diagnostic that is
    otherwise shape+digest only (ADR-031: "represented by shape plus digest,
    never by its bytes"). Two instances of two differently-named hostile
    classes must produce the SAME fixed type bucket — a closed vocabulary
    independent of the class — with the planted tokens absent everywhere.
    """

    token_a = "rnxs-clsa-4242a"
    token_b = "rnxs-clsb-9090b"
    class_a = type(f"class-{token_a}-payload", (), {})
    class_b = type(f"zzhostile-{token_b}-obj", (), {})

    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    _note(observability, subject_digest=class_a())
    _note(observability, subject_digest=class_b())

    captured = capfd.readouterr()
    for stream in (target.read_text(encoding="utf-8"), captured.out, captured.err):
        assert token_a not in stream
        assert token_b not in stream

    refusals = [
        code
        for code in _refusals(target)
        if code.startswith("out_of_form:subject_digest:")
    ]
    assert len(refusals) == 2, _refusals(target)
    assert all(re.search(r"sha256_8=[0-9a-f]{8}", code) for code in refusals)
    prefixes = {code.rsplit(",sha256_8=", 1)[0] for code in refusals}
    assert len(prefixes) == 1, (
        f"the type bucket varies with the class name ({prefixes!r}); it must "
        "be a fixed closed-vocabulary bucket"
    )
    (prefix,) = prefixes
    assert len(prefix) <= 48, f"the bucket is not bounded: {prefix!r}"


def test_worker_descriptor_carrying_trace_variables_is_refused_at_validation(
    tmp_path: Path,
) -> None:
    """S5(a) — the descriptor-validation path refuses RANEX_TRACE* pre-spawn.

    The confinement controller validates its command descriptor before any
    spawn; a worker environment key beyond {LC_ALL, TZ} — here RANEX_TRACE —
    is an allowlist violation and must be refused at descriptor validation
    itself, with no confinement host required to observe it. This pins the
    in-process seam so the refusal does not depend on the host-gated e2e arm.
    """

    from ranex.cli.host_confinement import HostConfinementError, _session_descriptor
    from ranex.foundation.canonical import canonical_json_bytes

    root = tmp_path / "session"
    for name in ("subject", "toolchain", "output", "scratch"):
        (root / name).mkdir(parents=True)

    def descriptor(environment: dict[str, str]) -> bytes:
        return canonical_json_bytes(
            {
                "schema": "ranex-confinement-command-v1",
                "argv": ["/bin/true"],
                "environment": environment,
                "subject": "subject",
                "toolchain": "toolchain",
                "output": "output",
                "scratch": "scratch",
                "limits": {
                    "cpu_usage_usec": 1_000_000,
                    "memory_bytes": 134_217_728,
                    "output_bytes": 65_536,
                    "output_depth": 8,
                    "output_inodes": 32,
                    "pids": 16,
                    "wall_time_ms": 5_000,
                },
            }
        )

    (root / "hostile.json").write_bytes(
        descriptor({"LC_ALL": "C", "TZ": "UTC", "RANEX_TRACE": "1"})
    )
    with pytest.raises(HostConfinementError, match="allowlist"):
        _session_descriptor(root, "hostile.json")

    # The frozen base still validates: the same descriptor without the trace
    # variable loads (this is the construction control, not a new assertion
    # about the launcher — the session itself stays host-gated).
    (root / "clean.json").write_bytes(descriptor({"LC_ALL": "C", "TZ": "UTC"}))
    assert _session_descriptor(root, "clean.json")["environment"] == {
        "LC_ALL": "C",
        "TZ": "UTC",
    }


def test_parent_sid_attribute_chains_strictly_under_the_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S5(b) — the public SESSION_ID attribute itself chains under the parent.

    The event-level chain is pinned by test_well_formed_parent_sid_chains…;
    this arm pins the same property on the controller-facing attribute a
    controller-side emitter would read, so the host-gated e2e tree-stitch is
    de-risked in-process. (Pure coverage strengthening: green on the current
    tree, no new behavior demanded.)
    """

    parent = "20260818T060601.512Z-ranex-box-4242"
    observability = _fresh_observability(
        monkeypatch, {"RANEX_TRACE_PARENT_SID": parent}
    )
    session_id = observability.SESSION_ID
    assert session_id.startswith(parent + "/")
    assert SID_COMPONENT.match(session_id.rsplit("/", 1)[-1])


# --- round-2 remediation arms (final-gate cumulative review, N1-N5) ----------
#
# Authored red against the tree at 68335ad71, blind to the fixes, per
# test-debug discipline.


def test_code_arguments_are_pinned_per_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """N1 — a registered kind's ARGUMENT is structural, not an open charset.

    After the CODE_KINDS registry (D3), the argument of every non-`exit` kind
    is still validated only by the generic charset, so a registered kind with
    a grammar-shaped secret argument passes (`out_of_form:code:rnxs-bearer-…`
    serializes verbatim). The internal forms are structural per kind:
    `exit:<int>`; `undeclared_field:<identifier>` or its shape form;
    `out_of_form:<field>:len=N,sha256_8=<8hex>` with <field> one of the frozen
    eleven; `malformed_parent_sid:<shape>`; `oversized_event:len=<N>`; the
    five bare kinds take NO argument at all. Anything else is refused with
    the value represented by shape plus digest, never bytes.
    """

    accepted = (
        "exit:0",
        "exit:-1",
        "undeclared_field:bearer_token",
        "undeclared_field:len=33,sha256_8=29a80d62",
        "out_of_form:code:len=12,sha256_8=deadbeef",
        "out_of_form:subject_digest:len=8,sha256_8=0bad1dea",
        "malformed_parent_sid:len=17,sha256_8=29a80d62",
        "oversized_event:len=16385",
        "cap_exceeded",
        "target_admission_failed",
        "emission_refused",
        "emission_not_a_mapping",
        "refusal_code_overflow",
    )
    for code in accepted:
        assert trace_schema.code_is_well_formed(code), f"structural form refused: {code}"

    token = "rnxs-bearer-0badf00dcafe"
    refused = (
        # argument-bearing kinds with hostile grammar-valid arguments
        f"out_of_form:code:{token}",       # field is real; the arg is not a shape
        f"out_of_form:{token}",            # not <field>:<shape> at all
        "out_of_form:exit:len=8,sha256_8=0bad1dea",  # `exit` is not one of the eleven
        f"undeclared_field:{token}",       # neither identifier nor shape form
        f"malformed_parent_sid:{token}",   # must be a shape descriptor
        f"oversized_event:{token}",        # must be len=<N>
        # bare kinds admit no argument whatsoever
        "cap_exceeded:anything",
        "target_admission_failed:1",
        "emission_refused:x",
        "emission_not_a_mapping:y",
        "refusal_code_overflow:len=1",
    )
    for code in refused:
        assert not trace_schema.code_is_well_formed(code), f"hostile code admitted: {code}"

    # Emission-level: each hostile value is refused by shape+digest and its
    # bytes never reach the stream.
    target = tmp_path / "trace.jsonl"
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    for code in refused:
        _note(observability, code=code)

    text = target.read_text(encoding="utf-8")
    assert token not in text
    refusals = [
        code
        for code in _refusals(target)
        if code.startswith("out_of_form:code:")
    ]
    assert len(refusals) == len(refused), _refusals(target)
    assert all(SHAPE_DESCRIPTOR.search(code) for code in refusals)


def test_anchor_appearing_after_admission_drops_a_held_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """N2(a) — a late-arriving authoritative anchor must drop a held target.

    The emitter admits against the cwd's git root, so a CLI invoked from
    OUTSIDE its checkout with RANEX_TRACE pointing inside the checkout admits
    and writes into the governed tree before the command even runs. The CLI's
    authoritative governed root is knowable only at the boundary, after
    admission may already have happened — so when the anchor appears, the
    already-held targets must be re-checked and any target inside the
    anchored root DROPPED: no further writes, exactly one warning, fail
    closed.
    """

    repo = _git_repo(tmp_path / "governed")
    target = repo / "trace.jsonl"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)  # no .git at or above: no cwd root today

    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(target)})
    assert observability.TRACING_ENABLED is True
    _note(observability)
    assert target.exists(), "construction check: admitted today (cwd has no root)"
    capfd.readouterr()  # admission succeeded; nothing warned yet

    import ranex.observability.emitter as emitter_module

    emitter_module.set_governed_root(repo)

    size_at_anchor = target.stat().st_size
    _note(observability)

    assert target.stat().st_size == size_at_anchor, (
        "a target inside the late-anchored governed root kept receiving writes"
    )
    first = capfd.readouterr()
    warnings = [line for line in first.err.splitlines() if line.strip()]
    assert len(warnings) == 1, f"exactly one drop warning, got {warnings!r}"
    assert "RANEX_TRACE" in warnings[0]
    assert str(target) in warnings[0], "a case-(a) refusal names the full path"

    _note(observability)
    again = capfd.readouterr()
    assert again.err == "", "a dropped target warns once, never again"
    assert target.stat().st_size == size_at_anchor


def test_fifo_target_admission_never_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """N3 — an absolute FIFO path must not block admission.

    `RANEX_TRACE=<path to an existing FIFO with no reader>`: the file-target
    admission `os.open(O_WRONLY)` on a FIFO blocks until a reader appears, so
    the first stage emission hangs the governed run — the same violation as
    D1, on the admission path instead of the write path (ADR-031 sad path 3:
    never block). Admission must complete by REFUSING the target: one
    warning, tracing off for the variable, run proceeds — never a crash.
    """

    fifo = tmp_path / "trace.fifo"
    os.mkfifo(fifo)
    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(fifo)})
    assert observability.TRACING_ENABLED is True

    _run_with_watchdog(lambda: _note(observability))

    first = capfd.readouterr()
    warnings = [line for line in first.err.splitlines() if line.strip()]
    assert len(warnings) == 1, f"exactly one admission refusal, got {warnings!r}"
    assert "RANEX_TRACE" in warnings[0]

    _run_with_watchdog(lambda: _note(observability))
    again = capfd.readouterr()
    assert again.err == "", "a refused target warns once, never again"


def test_directory_target_admission_cannot_be_redirected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """N4 — the per-process file must land under the ADMITTED directory's identity.

    The dir target commits to a directory and then creates `name` under it;
    if the creation re-walks the admitted PATH (or pins the directory by an
    open that a later symlink swap can still divert), swapping the directory
    entry for a symlink in that window redirects the created trace file
    (e.g. into a governed root that admission had just checked the ORIGINAL
    path against). The race window is deterministic here: os.open is
    interposed so the swap lands between the emitter's commitment to the
    directory and the open that uses the path — the mechanism of the eventual
    fix is left entirely free; the OBSERVABLE is pinned instead: no byte may
    be created under a redirected location, and the emitter either refuses
    the target (fail closed, one warning) or creates the file under the
    original directory's filesystem identity (same dev+inode as the admitted
    directory — rename preserves identity, so a held-directory implementation
    still satisfies this).
    """

    repo = _git_repo(tmp_path / "governed")
    decoy = repo / "tracedecoy"  # inside the governed root
    decoy.mkdir()
    admit = tmp_path / "admitdir"  # outside every root at admission time
    admit.mkdir()
    real = tmp_path / "admitdir.real"  # where the original directory moves
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    observability = _fresh_observability(monkeypatch, {"RANEX_TRACE": str(admit)})
    import ranex.observability.emitter as emitter_module

    emitter_module.set_governed_root(repo)

    real_open = os.open
    swapped = []

    def swapping_open(path, flags, *args, **kwargs):
        # Separator-consistent geometry, matching the two real code shapes a
        # `_DirTarget` can open: the directory ITSELF (a dirfd-pinning
        # implementation opens `admit` exactly, then creates the per-process
        # file relative via dir_fd= — a bare name that matches neither arm)
        # and full-path CHILD opens (a path re-walking implementation opens
        # `admit/name`). The original `startswith(str(admit) + os.sep)` alone
        # could never fire against the dirfd shape, making the branch
        # bookkeeping unsatisfiable for any compliant fix (round-2 harness
        # amendment, ruled a construction defect).
        try:
            operand = os.fsdecode(path)
        except (TypeError, ValueError):
            operand = ""
        if (
            not swapped
            and (operand == str(admit) or operand.startswith(str(admit) + os.sep))
        ):
            # The deterministic race: the emitter has committed to the real
            # directory (lstat/pin); before its next open uses the path, the
            # directory entry becomes a symlink into the governed root.
            os.rename(admit, real)
            os.symlink(decoy, admit)
            swapped.append(True)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swapping_open)
    _note(observability)
    monkeypatch.undo()  # restore os.open before any assertions touch the fs

    assert not swapped or not any(decoy.iterdir())  # swap fired ⇒ redirect created nothing
    redirected = sorted(decoy.iterdir())
    assert not redirected, (
        f"admission followed the swapped symlink and created {redirected!r} "
        "inside the governed root"
    )

    if not real.exists() or not any(real.iterdir()):
        # Fail closed is an admissible outcome: the target was refused, once.
        warnings = [line for line in capfd.readouterr().err.splitlines() if line.strip()]
        assert warnings, "neither a safely-created file nor a refusal — silent loss"
        assert "RANEX_TRACE" in warnings[0]
    else:
        created = next(path for path in real.iterdir() if path.is_file())
        admitted_identity = (real.stat().st_dev, real.stat().st_ino)
        parent_identity = (
            created.parent.stat().st_dev,
            created.parent.stat().st_ino,
        )
        assert parent_identity == admitted_identity, (
            "the per-process file was created outside the admitted directory's "
            "filesystem identity"
        )


def test_malformed_env_bytes_do_not_crash_the_import() -> None:
    """N5 — surrogate-escaped environment bytes must not crash the import.

    A RANEX_TRACE value carrying non-UTF-8 bytes (injected at the bytes-env
    level, as a hostile execve would) decodes with surrogates, and the
    invalid-value warning's shape descriptor raises UnicodeEncodeError during
    module import — violating "never crash the governed run for a trace
    problem". The import must succeed, warn once with a well-formed shape
    descriptor (length over the decoded value, digest over a surrogate-safe
    encoding), never echo the raw bytes, and disable that variable's target.

    Compatibility with the repo's advisory mutation tooling (mutmut): under
    `mutmut run` the child imports the trampolined mutants/ tree, whose
    trampoline reads MUTANT_UNDER_TEST unguarded — the parent's value is
    propagated (the stats-phase value normalised to mutmut's own
    no-mutant-active marker; see the env construction below) so the child
    still performs the real import of the (unmutated) module under the
    hostile env. The assertion under test is unchanged and still exercised
    in every normal run, where the parent carries no MUTANT_UNDER_TEST and
    the child env is exactly as before this amendment.
    """

    project_root = Path(__file__).resolve().parents[2]
    child_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "PYTHONPATH": str(project_root / "src"),
        "RANEX_TRACE": b"rel\xff\xfe.trace",  # non-UTF-8, not absolute
    }
    # mutmut 3.5.0 trampoline compatibility (SLICE-054 follow-up, sanctioned
    # amendment — construction class only). The generated trampoline reads
    # ``os.environ['MUTANT_UNDER_TEST']`` unguarded (trampoline_templates.py),
    # so a bare child importing the mutants/ tree dies with KeyError before
    # this test can prove anything. Propagate the parent's value when a
    # mutmut run is active: '' — mutmut's own "no mutant active" marker
    # (__main__.py sets it for unmutated executions) — and any value not
    # naming a mutant of this module fall through the trampoline to the
    # ORIGINAL code ('' matches neither the 'fail'/'stats' branches nor any
    # '<module>.<function>__mutmut_' prefix), while a real mutant name
    # executes that mutant, so a mutant that breaks the hostile-env import
    # still fails this test and is killed, as it must. One normalisation:
    # the stats-phase value 'stats' is propagated as '' — the 'stats'
    # trampoline branch calls record_trampoline_hit, which dereferences
    # mutmut.config (None in a fresh interpreter: AttributeError, verified
    # against the installed 3.5.0), and its in-memory stats set can never
    # cross the process boundary anyway, so no stats information is lost.
    parent_mutant = os.environ.get("MUTANT_UNDER_TEST")
    if parent_mutant is not None:
        child_env["MUTANT_UNDER_TEST"] = "" if parent_mutant == "stats" else parent_mutant
    completed = subprocess.run(
        [sys.executable, "-c", "import ranex.observability"],
        env=child_env,
        capture_output=True,
        text=False,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, (
        "the import crashed on malformed environment bytes:\n"
        + completed.stderr.decode("utf-8", "replace")
    )
    stderr = completed.stderr
    assert b"UnicodeEncodeError" not in stderr
    assert b"\xff\xfe" not in stderr, "the raw hostile bytes reached the warning"
    text = stderr.decode("utf-8", "replace")
    warnings = [line for line in text.splitlines() if "RANEX_TRACE" in line]
    assert len(warnings) == 1, f"exactly one invalid-value warning, got {text!r}"
    assert SHAPE_DESCRIPTOR.search(warnings[0]), (
        f"the warning carries no well-formed shape descriptor: {warnings[0]!r}"
    )
