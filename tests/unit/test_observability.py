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
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

import ranex.observability
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
    import ranex.observability

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
