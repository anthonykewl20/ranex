"""SLICE-055 — prereq-gate honesty, declared-skip cross-check, normalizer freeze.

Frozen RED before any implementation exists (spec-prd stage 2, step 6;
ADR-032 docs/adr/ADR-032-real-e2e-suite-framework.md; issue #35). The frame
module named below does not exist yet — the import failure at collection
time IS the red. From the freeze commit on, this file is read-only to the
implementer.

The frozen interface this file pins (the frame's one library module,
`tests/e2e/_prereqs.py` — issue #35's exact ownership):

    PROBE_NAMES                        the six frozen probe names, exactly:
                                       pinned_resolver, network_available,
                                       signing_key, harness_fork,
                                       openrouter_key, qualified_host
    <probe>() -> (ok: bool, reason: str)   one callable per name
    REASON_PREFIX = "ranex-prereq:"    machine-greppable reason grammar: an
                                       absent probe's reason starts
                                       "ranex-prereq:<probe_name>:"
    prereq_or_skip(name) -> None       the consuming-fixture helper: returns
                                       when the probe says present, skips
                                       with the greppable reason when absent
                                       — it NEVER skips when its probe says
                                       present
    normalize_transcript(text) -> str  the ONE centralized normalizer; a
                                        single `text` argument and nothing
                                        else — per-test/per-family masks
                                        cannot be injected. A relative path
                                        immediately followed by `::` is a
                                        test nodeid — nodeids stay
                                        discriminating bytes (remediation
                                        R5b: two failures in different
                                        files never normalize equal).
    compare_transcript(actual, expected, family=None) -> None
                                        byte-exact compare; on mismatch the
                                        AssertionError carries the unified
                                        diff of the first differing hunk,
                                        untruncated, EXACTLY one hunk
                                        (remediation R5c) and names the
                                        golden's family label.
    cross_check_skips(manifest_path, junitxml_path) -> list[str]
                                        both directions at entrypoint time:
                                        "undeclared skip: <id>: <reason>" and
                                        "declared skip not observed: <id>:
                                        <reason>"; [] when honest. A declared
                                        skip that WAS observed but with a
                                        drifted reason is a finding of the
                                        HARD tier only (remediation R1d as
                                        scoped by the orchestrator ruling on
                                        Worker B's #35 blocker: a
                                        ``ranex-prereq:`` declaration
                                        compares reasons EXACTLY, both
                                        strings named; a ``ranex-context:``
                                        declaration is never byte-compared —
                                        its drift is reported by
                                        ``context_mismatches`` naming ID +
                                        observed message + declared context).
    `python tests/e2e/_prereqs.py cross-check <manifest> <junitxml>`
                                       exit 0 when honest, nonzero printing
                                       each finding — the step the README
                                       entrypoint composes for its
                                       nonzero-on-any-mismatch contract

Ordered normalizer grammar (ADR-032, applied in exactly this order by the
one audited function): digests -> <DIGEST>, absolute paths -> <ABS-PATH>,
timestamps -> <TIMESTAMP>, durations -> <DURATION>, chained SIDs -> <SID>
(sid.py's component shape, slashes included, one token), PIDs -> <PID>,
ephemeral ports -> <PORT>, then relative paths -> <REL-PATH>. Meaningful
values — verdict words, exit codes, test names — stay discriminating.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_DIR = REPO_ROOT / "tests" / "e2e"

# The frame's library module. Import through the e2e directory so this file
# does not depend on pytest's import mode; the missing module pre-
# implementation is the frozen red.
sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.observability.sid import mint_component  # noqa: E402

# --- the six frozen probes ----------------------------------------------------

# (probe name, env var, present value factory). Three probes are
# environment-file-driven, so absence and presence are simulated in tmp
# environments exactly as the ADR's honesty proof requires. The env var
# names come from the existing frozen usage this frame generalizes
# (RANEX_SIGNING_KEY everywhere, RANEX_HARNESS_DIR in the manifest's own
# expected-skip reasons and tests/e2e/test_first_delegation.py,
# OPENROUTER_API_KEY in tests/e2e/test_first_delegation.py).
ENV_PROBES = (
    ("signing_key", "RANEX_SIGNING_KEY", "key-file"),
    ("harness_fork", "RANEX_HARNESS_DIR", "dir"),
    ("openrouter_key", "OPENROUTER_API_KEY", "value"),
)
NON_ENV_PROBES = ("pinned_resolver", "network_available", "qualified_host")


def _make_present(kind: str, tmp_path: Path) -> str:
    if kind == "key-file":
        path = tmp_path / "worker.key"
        path.write_text("test-private-key-material\n", encoding="utf-8")
        return str(path)
    if kind == "dir":
        path = tmp_path / "harness-fork"
        path.mkdir()
        return str(path)
    return "sk-test-openrouter-key"


# --- 1. probe library contract ------------------------------------------------


def test_the_six_frozen_probe_names_exist_as_callables() -> None:
    """Exactly the six ADR-named probes, each a callable returning a pair."""

    assert _prereqs.PROBE_NAMES == (
        "pinned_resolver",
        "network_available",
        "signing_key",
        "harness_fork",
        "openrouter_key",
        "qualified_host",
    )
    for name in _prereqs.PROBE_NAMES:
        probe = getattr(_prereqs, name, None)
        assert callable(probe), f"probe {name} is missing from _prereqs"
        result = probe()
        assert isinstance(result, tuple) and len(result) == 2, (
            f"probe {name} returned {result!r}; the contract is (ok, reason)"
        )
        ok, reason = result
        assert isinstance(ok, bool), f"probe {name} ok={ok!r} is not a bool"
        assert isinstance(reason, str), (
            f"probe {name} reason={reason!r} is not a string"
        )


@pytest.mark.parametrize(
    ("probe_name", "env_var", "kind"),
    ENV_PROBES,
    ids=[name for name, _, _ in ENV_PROBES],
)
def test_probe_reason_grammar_fires_when_the_precondition_is_absent(
    probe_name: str, env_var: str, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An absent precondition yields (False, reason) whose stable prefix
    grammar is machine-greppable and names the precondition."""

    monkeypatch.delenv(env_var, raising=False)
    ok, reason = getattr(_prereqs, probe_name)()
    assert ok is False, (
        f"{probe_name}: precondition absent ({env_var} unset) but probe "
        f"reports present — the skip must fire exactly then"
    )
    prefix = f"ranex-prereq:{probe_name}:"
    assert reason.startswith(prefix), (
        f"{probe_name} reason {reason!r} does not start with the stable "
        f"prefix {prefix!r}; every skip reason must be machine-greppable"
    )
    assert len(reason) > len(prefix), (
        f"{probe_name} reason carries no explanation after the prefix"
    )


@pytest.mark.parametrize("probe_name", NON_ENV_PROBES)
def test_non_env_probe_grammar_holds_wherever_it_is_absent_here(
    probe_name: str,
) -> None:
    """Host-dependent probes keep the same grammar on any host where their
    precondition is absent; where it is present, the pair shape (frozen
    above) is all this test can demand without faking the host."""

    ok, reason = getattr(_prereqs, probe_name)()
    if not ok:
        assert reason.startswith(
            f"ranex-prereq:{probe_name}:"
        ), f"{probe_name} reason {reason!r} breaks the greppable grammar"


@pytest.mark.parametrize(
    ("probe_name", "env_var", "kind"),
    ENV_PROBES,
    ids=[name for name, _, _ in ENV_PROBES],
)
def test_probe_flips_to_present_when_the_environment_provides_it(
    probe_name: str,
    env_var: str,
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same probe, same process, environment changed: the answer must
    follow the environment — no in-process memoization."""

    monkeypatch.delenv(env_var, raising=False)
    absent_ok, _ = getattr(_prereqs, probe_name)()
    assert absent_ok is False

    monkeypatch.setenv(env_var, _make_present(kind, tmp_path))
    present_ok, _ = getattr(_prereqs, probe_name)()
    assert present_ok is True, (
        f"{probe_name}: precondition present ({env_var} set) but the probe "
        f"still reports absent — a cached answer is a cached lie"
    )


def test_probes_hold_no_cross_process_cache(tmp_path: Path) -> None:
    """A capability decision cached on disk would poison later processes —
    git's test_lazy_prereq weakness, refused here. Two fresh interpreters,
    absent then present environment, must disagree."""

    probe_code = (
        "import json, sys\n"
        f"sys.path.insert(0, {str(E2E_DIR)!r})\n"
        "import _prereqs\n"
        "ok, reason = _prereqs.signing_key()\n"
        "print(json.dumps({'ok': ok, 'reason': reason}))\n"
    )

    def _probe(env: dict[str, str]) -> dict[str, object]:
        completed = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout.strip().splitlines()[-1])

    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    absent = _probe({**base})  # no RANEX_SIGNING_KEY anywhere
    key = tmp_path / "worker.key"
    key.write_text("test-private-key-material\n", encoding="utf-8")
    present = _probe({**base, "RANEX_SIGNING_KEY": str(key)})

    assert absent["ok"] is False and present["ok"] is True, (
        "a fresh process must re-evaluate the probe against its own "
        f"environment; absent={absent!r} present={present!r}"
    )


@pytest.mark.parametrize(
    ("probe_name", "env_var", "kind"),
    ENV_PROBES,
    ids=[name for name, _, _ in ENV_PROBES],
)
def test_prereq_or_skip_fires_exactly_on_absence(
    probe_name: str,
    env_var: str,
    kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The consuming-fixture helper: absent -> pytest skip carrying the
    greppable reason; present -> returns quietly. The present case is the
    probe-says-present-but-fixture-skipped refusal — the frame's sanctioned
    skip path never skips when its probe says present."""

    monkeypatch.delenv(env_var, raising=False)
    with pytest.raises(pytest.skip.Exception, match=rf"ranex-prereq:{probe_name}:"):
        _prereqs.prereq_or_skip(probe_name)

    monkeypatch.setenv(env_var, _make_present(kind, tmp_path))
    # Remediation R4c (strengthening, recorded): the bare `assert ... is None`
    # could never FAIL a wrong skip — pytest.skip propagates as SKIPPED. The
    # refusal is now caught and converted to a loud failure.
    try:
        returned = _prereqs.prereq_or_skip(probe_name)
    except pytest.skip.Exception:
        pytest.fail(
            f"prereq_or_skip({probe_name!r}) skipped while its probe says "
            "present — the frame refuses probe-says-present-but-fixture-"
            "skipped"
        )
    assert returned is None, (
        f"prereq_or_skip({probe_name!r}) signaled {returned!r} while its "
        "probe says present — the frame refuses probe-says-present-but-"
        "fixture-skipped"
    )


# --- 1b. non-env probes under injected preconditions (remediation R4a/R4b) -----
#
# The arbitration finding: the three host-dependent probes had no present-case
# arms and no flip arms — their honesty was asserted only "wherever absent
# here". The drivers below inject the precondition at its real seam (a tmp
# governance/deps.yaml tree for pinned_resolver, a socket test double for
# network_available, a limitation return for qualified_host), so both verdicts
# are driven deterministically on any host.


def _drive_pinned_resolver(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, correct_pin: bool
) -> None:
    """Point the probe's repository root at a tmp tree with a real resolver
    file — its pinned digest correct or wrong."""

    root = tmp_path / "pin-root"
    (root / "governance").mkdir(parents=True, exist_ok=True)
    resolver = root / "resolver.bin"
    resolver.write_bytes(b"resolver-bytes-for-the-frozen-probe")
    digest = hashlib.sha256(resolver.read_bytes()).hexdigest()
    (root / "governance" / "deps.yaml").write_text(
        "resolver:\n"
        f"  path: {resolver}\n"
        f"  sha256: {digest if correct_pin else 'f' * 64}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_prereqs, "REPO_ROOT", root)


class _DoubleSocket:
    """A socket test double: connect() refuses or succeeds on demand."""

    def __init__(self, *, refuse: bool) -> None:
        self._refuse = refuse

    def settimeout(self, seconds: float) -> None:
        return None

    def connect(self, address: object) -> None:
        if self._refuse:
            raise ConnectionRefusedError(f"test double refusal for {address!r}")
        return None

    def close(self) -> None:
        return None


def _drive_network(monkeypatch: pytest.MonkeyPatch, *, refuse: bool) -> None:
    import socket

    monkeypatch.setattr(socket, "socket", lambda: _DoubleSocket(refuse=refuse))


def _drive_qualified_host(
    monkeypatch: pytest.MonkeyPatch, limitation: str | None
) -> None:
    monkeypatch.setattr(
        _prereqs, "_qualification_host_limitation", lambda: limitation
    )


def _inject_absent(
    probe_name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    if probe_name == "pinned_resolver":
        _drive_pinned_resolver(monkeypatch, tmp_path, correct_pin=False)
    elif probe_name == "network_available":
        _drive_network(monkeypatch, refuse=True)
    else:
        _drive_qualified_host(
            monkeypatch, "injected limitation: the test double denies this host"
        )


def _inject_present(
    probe_name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    if probe_name == "pinned_resolver":
        _drive_pinned_resolver(monkeypatch, tmp_path, correct_pin=True)
    elif probe_name == "network_available":
        _drive_network(monkeypatch, refuse=False)
    else:
        _drive_qualified_host(monkeypatch, None)


@pytest.mark.parametrize("probe_name", NON_ENV_PROBES)
def test_non_env_probe_absent_case_keeps_the_grammar_under_injection(
    probe_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R4a: the absent verdict under an injected precondition is a real
    (False, reason) pair carrying the greppable grammar — not a guess, an
    error, or a present."""

    _inject_absent(probe_name, monkeypatch, tmp_path)
    ok, reason = getattr(_prereqs, probe_name)()
    prefix = f"ranex-prereq:{probe_name}:"
    assert ok is False, (
        f"{probe_name}: injected precondition is absent but the probe "
        f"reports present — {reason!r}"
    )
    assert reason.startswith(prefix), (
        f"{probe_name} reason {reason!r} does not start with {prefix!r}; "
        "every skip reason must be machine-greppable"
    )
    assert len(reason) > len(prefix), (
        f"{probe_name} reason carries no explanation after the prefix"
    )


@pytest.mark.parametrize("probe_name", NON_ENV_PROBES)
def test_non_env_probe_re_evaluates_when_the_precondition_flips_in_process(
    probe_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R4a present-case + R4b no-cache: same process, precondition flipped
    between two calls — the second answer must follow the flipped
    precondition (mirrors the signing_key env-flip arm's construction).
    With pinned_resolver the present case is a REAL satisfied fixture: a
    tmp deps.yaml whose pin matches the digest of the file it names."""

    _inject_absent(probe_name, monkeypatch, tmp_path)
    absent_ok, _ = getattr(_prereqs, probe_name)()
    assert absent_ok is False, (
        f"{probe_name}: the absent injection did not take (probe reports "
        "present before the flip — the fixture is broken)"
    )

    _inject_present(probe_name, monkeypatch, tmp_path)
    present_ok, present_reason = getattr(_prereqs, probe_name)()
    assert present_ok is True, (
        f"{probe_name}: precondition flipped present but the probe still "
        f"reports absent ({present_reason!r}) — a cached answer is a "
        "cached lie"
    )


# --- 2. declared-skip cross-check, both directions ----------------------------

# One honest test, one undeclared skip, one stale declaration. IDs use the
# manifest's frozen nodeid convention (kernel _test_id: junitxml classname
# tests.contract.<module> -> tests/contract/<module>.py).
_CROSSED_ID = "tests/contract/test_prereq_gates.py::test_cross_check_honest_manifest_passes"
_UNDECLARED_ID = "tests/contract/test_prereq_gates.py::test_probe_undeclared_fixture"
_STALE_ID = "tests/contract/test_prereq_gates.py::test_probe_stale_declaration"
_CROSSED_REASON = "ranex-prereq:signing_key: fixture environment has no key"
_UNDECLARED_REASON = "ranex-prereq:openrouter_key: fixture environment has no key"
_STALE_REASON = "ranex-prereq:harness_fork: declared but the fork is present"

_JUNIT_SKIPPED = (
    '<testcase classname="tests.contract.test_prereq_gates" '
    'name="{name}" time="0.000"><skipped type="pytest.skip" '
    'message="{reason}">{reason}</skipped></testcase>'
)
_JUNIT_PASSED = (
    '<testcase classname="tests.contract.test_prereq_gates" '
    'name="{name}" time="0.000" />'
)


def _junitxml(tmp_path: Path, cases: str, *, skipped: int, tests: int) -> Path:
    path = tmp_path / "results.xml"
    path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites name="pytest tests"><testsuite name="pytest" '
        f'errors="0" failures="0" skipped="{skipped}" tests="{tests}" '
        f'time="0.011" hostname="host">{cases}</testsuite></testsuites>',
        encoding="utf-8",
    )
    return path


def _manifest(tmp_path: Path, expected_skips: dict[str, str]) -> Path:
    """A canonical manifest whose suite is EXACTLY the junitxml ID set: the
    cross-check contract frozen here is the skip ledger (both directions) —
    full ID-set diffing is gate evaluate's frozen job (SLICE-009), and this
    fixture refuses to ambiguates the two."""

    path = tmp_path / "suite_manifest.json"
    ids = sorted([_CROSSED_ID, _UNDECLARED_ID, _STALE_ID])
    path.write_bytes(
        canonical_json_bytes({"suite": ids, "expected_skips": expected_skips})
    )
    return path


def _cross(manifest: Path, junit: Path) -> list[str]:
    return _prereqs.cross_check_skips(manifest, junit)


def _cross_script(manifest: Path, junit: Path) -> subprocess.CompletedProcess[str]:
    """The entrypoint's nonzero-on-mismatch step, driven exactly as the
    README documents it."""

    return subprocess.run(
        [
            sys.executable,
            str(E2E_DIR / "_prereqs.py"),
            "cross-check",
            str(manifest),
            str(junit),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
        check=False,
    )


def test_cross_check_honest_manifest_passes(tmp_path: Path) -> None:
    """A skip both declared and observed, plus clean passes: no findings,
    and the script exits zero."""

    manifest = _manifest(tmp_path, {_CROSSED_ID: _CROSSED_REASON})
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(name=_CROSSED_ID.split("::")[1], reason=_CROSSED_REASON)
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=1,
        tests=3,
    )
    assert _cross(manifest, junit) == []

    completed = _cross_script(manifest, junit)
    assert completed.returncode == 0, (
        f"honest manifest must exit zero; stderr={completed.stderr!r}"
    )


def test_undeclared_observed_skip_fails_naming_id_and_reason(
    tmp_path: Path,
) -> None:
    """Sad path 5, direction one: an observed skip with no declaration."""

    manifest = _manifest(tmp_path, {_CROSSED_ID: _CROSSED_REASON})
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(name=_CROSSED_ID.split("::")[1], reason=_CROSSED_REASON)
        + _JUNIT_SKIPPED.format(
            name=_UNDECLARED_ID.split("::")[1], reason=_UNDECLARED_REASON
        )
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=2,
        tests=3,
    )
    findings = _cross(manifest, junit)
    assert findings, "an undeclared observed skip must produce a finding"
    line = findings[0]
    assert line.startswith("undeclared skip:"), (
        f"finding must start with the greppable grammar: {line!r}"
    )
    assert _UNDECLARED_ID in line and _UNDECLARED_REASON in line, (
        f"finding must name the test ID and its reason: {line!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode != 0, "undeclared skip must exit nonzero"
    assert _UNDECLARED_ID in completed.stdout, (
        f"the entrypoint step must print the finding: {completed.stdout!r}"
    )


def test_declared_skip_not_observed_fails_naming_id_and_reason(
    tmp_path: Path,
) -> None:
    """Sad path 5, direction two (and 10): the declaration is stale — the
    precondition turned out present, the test ran. The entrypoint catches
    what outcome-blind freeze time cannot."""

    manifest = _manifest(
        tmp_path,
        {_CROSSED_ID: _CROSSED_REASON, _STALE_ID: _STALE_REASON},
    )
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(name=_CROSSED_ID.split("::")[1], reason=_CROSSED_REASON)
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=1,
        tests=3,
    )
    findings = _cross(manifest, junit)
    assert findings, "a declared skip that did not occur must produce a finding"
    line = findings[0]
    assert line.startswith("declared skip not observed:"), (
        f"finding must start with the greppable grammar: {line!r}"
    )
    assert _STALE_ID in line and _STALE_REASON in line, (
        f"finding must name the test ID and its declared reason: {line!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode != 0, "declared-but-not-observed must exit nonzero"
    assert _STALE_ID in completed.stdout


# --- 2b. remediation arms: the scoped cross-check made contractual --------------
#
# Arbitration B1/M4: the two-tier scope (hard probe-backed tier +
# informational context tier, ruled on issue #35) had no frozen arms — only
# the mechanism tests for the unscoped directions. R1a/R1b pin the ruled
# scope permanently; R1c lints the manifest's own declarations into the
# ruled two grammars (amended per the orchestrator's R1c census ruling:
# prereq hard / context informational); R1d adds the missing direction (a)
# reason comparison — scoped, per the orchestrator ruling on Worker B's
# #35 blocker (comment 5343719923), to a HARD-tier obligation only: exact
# comparison for ranex-prereq: declarations, reported-not-compared for
# ranex-context: ones, and a prereq-tier declaration whose observed
# message cannot carry the marker is misclassified — a finding until it is
# reclassified context-tier through the freeze ceremony (classification
# honesty).


_CONTEXT_BOUND_REASON = (
    "needs operator uv on PATH and an unwritable system interpreter; the "
    "sealed hermetic environment provides neither"
)


def test_non_probe_backed_declared_not_observed_is_informational_only(
    tmp_path: Path,
) -> None:
    """R1a: a context-bound declaration whose test ran on this host is NOT a
    hard finding — the manifest is multi-context by design. The hard ledger
    stays empty, the informational tier names the ID with a count line, and
    the script path exits 0 with the ID in its output."""

    manifest = _manifest(tmp_path, {_CROSSED_ID: _CONTEXT_BOUND_REASON})
    junit = _junitxml(
        tmp_path,
        _JUNIT_PASSED.format(name=_CROSSED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=0,
        tests=3,
    )

    assert _cross(manifest, junit) == [], (
        "a non-probe-backed declared-not-observed skip must not enter the "
        "hard ledger — it is the informational context-mismatch tier"
    )
    mismatches = _prereqs.context_mismatches(manifest, junit)
    assert any(_CROSSED_ID in line for line in mismatches), (
        f"the informational tier must name the ID: {mismatches!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode == 0, (
        f"a context mismatch is informational, never an exit condition; "
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert _CROSSED_ID in completed.stdout, (
        f"the ID must appear in the mismatch list output: {completed.stdout!r}"
    )
    assert re.search(r"context-mismatch count: 1\b", completed.stdout), (
        f"the composed output must carry the count line: {completed.stdout!r}"
    )


def test_probe_backed_declared_not_observed_with_absent_probe_is_hard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R1b: the absent-verdict branch of the probe-backed tier. A grammar
    declaration whose probe is verifiably ABSENT on the running host, whose
    test ran anyway, is a HARD finding naming the live probe verdict — the
    distinguishing text is 'the declared context did not skip here'."""

    monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
    probe_ok, _ = _prereqs.signing_key()
    assert probe_ok is False, (
        "fixture precondition: the signing_key probe must be verifiably "
        "absent in this process for the absent-verdict branch to be driven"
    )

    manifest = _manifest(tmp_path, {_CROSSED_ID: _CROSSED_REASON})
    junit = _junitxml(
        tmp_path,
        _JUNIT_PASSED.format(name=_CROSSED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=0,
        tests=3,
    )
    findings = _cross(manifest, junit)
    assert findings, "a probe-backed declared-not-observed skip must be hard"
    line = findings[0]
    assert line.startswith("declared skip not observed:"), (
        f"finding must start with the greppable grammar: {line!r}"
    )
    assert "says absent" in line, (
        f"the finding must name the live ABSENT probe verdict: {line!r}"
    )
    assert "the declared context did not skip here" in line, (
        f"the finding must carry the absent-verdict branch's distinguishing "
        f"text: {line!r}"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(E2E_DIR / "_prereqs.py"),
            "cross-check",
            str(manifest),
            str(junit),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
        check=False,
        env={
            key: value
            for key, value in os.environ.items()
            if key != "RANEX_SIGNING_KEY"
        },
    )
    assert completed.returncode != 0, (
        "the probe-backed absent-verdict branch must exit nonzero"
    )
    assert "the declared context did not skip here" in completed.stdout


_DRIFTED_DECLARED = (
    "ranex-prereq:signing_key: declared at freeze time with this wording"
)
_DRIFTED_OBSERVED = (
    "ranex-prereq:signing_key: the live fixture skipped with different wording"
)


def test_declared_observed_skip_with_drifted_reason_is_a_finding_naming_both(
    tmp_path: Path,
) -> None:
    """R1d, hard tier: direction (a) reason comparison for a PREREQ-tier
    declaration, pinned to EXACT string equality (the arbitration's
    pick-one; scope confirmed by the orchestrator ruling on Worker B's #35
    blocker). A skip that IS declared with ``ranex-prereq:`` but whose
    observed reason drifted is a finding naming both strings — an
    outcome-blind freeze cannot be allowed to launder a reworded skip.
    Both fixtures carry the marker: this tier's tests are designed to emit
    marker-carrying skip messages."""

    manifest = _manifest(tmp_path, {_CROSSED_ID: _DRIFTED_DECLARED})
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(
            name=_CROSSED_ID.split("::")[1], reason=_DRIFTED_OBSERVED
        )
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=1,
        tests=3,
    )
    findings = _cross(manifest, junit)
    assert findings, (
        "a declared skip observed with a drifted reason must produce a "
        "finding — direction (a) compares reasons, not just IDs"
    )
    line = findings[0]
    assert line.startswith("skip reason mismatch:"), (
        f"finding must start with the greppable grammar: {line!r}"
    )
    assert _DRIFTED_DECLARED in line and _DRIFTED_OBSERVED in line, (
        f"finding must name BOTH the declared and the observed reason: {line!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode != 0, "a drifted skip reason must exit nonzero"
    assert "skip reason mismatch:" in completed.stdout
    assert _DRIFTED_OBSERVED in completed.stdout


#: The ruled case, verbatim from Worker B's blocker (#35 comment 5343719923):
#: a live skip message emitted by ANOTHER slice's frozen test file —
#: dynamically composed build-closure prose whose "(1 of 213 traced inputs
#: differ, e.g. /etc/ld.so.cache)" detail varies with host state, so it can
#: never byte-match a freeze-time declaration. Exactly the message class the
#: ruling holds out of the hard tier's exact comparison.
_FOREIGN_DYNAMIC_OBSERVED = (
    "SLICE-017 build host unavailable: the pinned launcher build closure "
    "does not match this host (1 of 213 traced inputs differ, e.g. "
    "/etc/ld.so.cache) — launcher-build refuses E-C17-BUILD-INPUT-DRIFT here"
)


def test_context_tier_declared_observed_drift_is_reported_not_compared(
    tmp_path: Path,
) -> None:
    """R1d, informational tier: a ``ranex-context:`` declaration observed
    skipping with a wildly different (here: dynamically composed, foreign)
    live message produces NO reason finding — ``cross_check_skips`` stays
    empty, the entrypoint exits zero — and the drift is REPORTED: the ID
    appears in ``context_mismatches`` output alongside its declared context
    and the observed message (the ruling's machine-greppable promise:
    reported, never byte-compared)."""

    declared = (
        "ranex-context:launcher-build-host: the sealed hermetic freeze never "
        "materialises the pinned launcher build closure this journey needs"
    )
    manifest = _manifest(tmp_path, {_CROSSED_ID: declared})
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(
            name=_CROSSED_ID.split("::")[1], reason=_FOREIGN_DYNAMIC_OBSERVED
        )
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=1,
        tests=3,
    )

    assert _cross(manifest, junit) == [], (
        "a context-tier declaration whose observed message drifted is "
        "reported, never a hard reason-mismatch finding — the informational "
        "tier is not byte-compared (orchestrator ruling, #35)"
    )

    mismatches = _prereqs.context_mismatches(manifest, junit)
    reported = [line for line in mismatches if _CROSSED_ID in line]
    assert reported, (
        "the drifted context-tier skip must be REPORTED with its ID: "
        f"{mismatches!r}"
    )
    line = reported[0]
    assert "launcher-build-host" in line, (
        "the report must name the declared context: "
        f"{line!r}"
    )
    assert _FOREIGN_DYNAMIC_OBSERVED in line, (
        "the report must name the observed message next to the declared "
        f"context (ID + observed + declared context): {line!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode == 0, (
        "a context-tier reason drift is informational, never an exit "
        f"condition; stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert _CROSSED_ID in completed.stdout, (
        f"the ID must appear in the mismatch list output: {completed.stdout!r}"
    )
    assert _FOREIGN_DYNAMIC_OBSERVED in completed.stdout, (
        "the artifact must carry the observed message next to the ID: "
        f"{completed.stdout!r}"
    )
    assert re.search(r"context-mismatch count: 1\b", completed.stdout), (
        f"the composed output must carry the count line: {completed.stdout!r}"
    )


def test_prereq_tier_declaration_with_unmarked_observed_message_is_a_finding(
    tmp_path: Path,
) -> None:
    """R1d, classification honesty (the hard tier restated with the marker
    check pinned): a ``ranex-prereq:`` declaration observed with a live
    message that does NOT carry the marker is a finding naming both
    strings. A prereq-tier declaration whose test's message cannot carry
    the marker is misclassified — the remedy is reclassifying it
    context-tier through the freeze ceremony, never silencing the
    finding."""

    declared = (
        "ranex-prereq:qualified_host: this host was declared at freeze time "
        "to lack the confinement qualification"
    )
    # The marker check, pinned explicitly: the declaration carries the
    # prereq marker, the observed message does not — the misclassification
    # the classification-honesty rule names.
    assert declared.startswith(f"{_prereqs.REASON_PREFIX}qualified_host:"), (
        "fixture precondition: the declaration must carry the prereq marker"
    )
    assert not _FOREIGN_DYNAMIC_OBSERVED.startswith(_prereqs.REASON_PREFIX), (
        "fixture precondition: the observed message must NOT carry the "
        "marker — this is the misclassified case"
    )

    manifest = _manifest(tmp_path, {_CROSSED_ID: declared})
    junit = _junitxml(
        tmp_path,
        _JUNIT_SKIPPED.format(
            name=_CROSSED_ID.split("::")[1], reason=_FOREIGN_DYNAMIC_OBSERVED
        )
        + _JUNIT_PASSED.format(name=_UNDECLARED_ID.split("::")[1])
        + _JUNIT_PASSED.format(name=_STALE_ID.split("::")[1]),
        skipped=1,
        tests=3,
    )
    findings = _cross(manifest, junit)
    assert findings, (
        "a prereq-tier declaration observed with an unmarked message is a "
        "finding — the classification-honesty rule"
    )
    line = findings[0]
    assert line.startswith("skip reason mismatch:"), (
        f"finding must start with the greppable grammar: {line!r}"
    )
    assert declared in line and _FOREIGN_DYNAMIC_OBSERVED in line, (
        f"finding must name BOTH the declared and the observed reason: {line!r}"
    )

    completed = _cross_script(manifest, junit)
    assert completed.returncode != 0, (
        "a prereq-tier reason mismatch must exit nonzero however foreign "
        "the observed message is"
    )
    assert "skip reason mismatch:" in completed.stdout
    assert _FOREIGN_DYNAMIC_OBSERVED in completed.stdout


#: R1c — the two-grammar declaration mandate (orchestrator ruling on issue
#: #35, replacing the single-grammar mandate ruled unsound): the manifest
#: legitimately serves multiple contexts — a hermetic freeze and a
#: documented entrypoint host — so a context-bound declaration is honest
#: when it NAMES its context. Two grammars, two tiers:
#:
#:     ``ranex-prereq:<probe>: <prose>`` — HARD tier. The declaration
#:     asserts a context-independent, probe-verifiable condition;
#:     ``<probe>`` must be one of the six frozen probes, exactly the
#:     mapping the cross-check's probe-backed tier verifies live in both
#:     directions.
#:
#:     ``ranex-context:<context>: <prose>`` — INFORMATIONAL tier. The
#:     declaration names the context it belongs to (e.g.
#:     ``hermetic-freeze``); ``context_mismatches`` reports it with its
#:     context named, never hard. The seven plugin_lock harness-fork
#:     declarations are the ruled example: absent in the hermetic freeze,
#:     present-and-running on the canonical entrypoint host, so forcing
#:     them into the probe-backed tier would hard-fail a green entrypoint.
#:
#: Every expected_skip reason must start with one of the two grammars —
#: unmarked prose is refused. A context marker without a non-empty
#: single-token ``<context>`` is refused too: the context slot names a
#: context, conditions belong in the prose.
_CONTEXT_MARKER = "ranex-context:"


def _declaration_defect(reason: str) -> str | None:
    """The two-grammar lint verdict for ONE declared reason: ``None`` when
    the declaration carries a valid grammar, the greppable defect line
    naming what is wrong when it does not."""

    if reason.startswith(_prereqs.REASON_PREFIX):
        rest = reason[len(_prereqs.REASON_PREFIX) :]
        probe, colon, prose = rest.partition(":")
        if not colon:
            return "carries the probe marker but no '<probe>:' slot"
        if probe not in _prereqs.PROBE_NAMES:
            return (
                f"names {probe!r} — not one of the six frozen probes — so "
                "the probe-backed tier cannot verify it and the declaration "
                "would silently fall informational"
            )
        if not prose.strip():
            return "carries no prose after the probe marker"
        return None

    if reason.startswith(_CONTEXT_MARKER):
        rest = reason[len(_CONTEXT_MARKER) :]
        context, colon, prose = rest.partition(":")
        if not colon or not context or any(char.isspace() for char in context):
            return (
                "carries the context marker but no non-empty single-token "
                "<context> — a context declaration must NAME the context it "
                "belongs to"
            )
        if not prose.strip():
            return "carries no prose after the context marker"
        return None

    return (
        "unmarked prose — the reason must start with "
        f"'{_prereqs.REASON_PREFIX}<probe>:' (hard tier, probe-verified) or "
        f"'{_CONTEXT_MARKER}<context>:' (informational tier, context-named)"
    )


#: The arm's sample declarations, one per ruled form, pinning the lint's
#: cross-tier consistency: (reason, the defect substring the refusal must
#: carry — None when the lint must ACCEPT — the ruled form's id).
_DECLARATION_SAMPLES: tuple[tuple[str, str | None, str], ...] = (
    (
        "ranex-prereq:signing_key: RANEX_SIGNING_KEY is unset or empty",
        None,
        "valid-prereq",
    ),
    (
        "ranex-context:hermetic-freeze: the sealed environment provides "
        "neither operator uv nor an unwritable system interpreter",
        None,
        "valid-context",
    ),
    (
        "needs the sibling harness fork (RANEX_HARNESS_DIR); a materialised "
        "sample does not carry it",
        "unmarked prose",
        "refuse-unmarked",
    ),
    (
        "ranex-context:: the context slot was left empty",
        "no non-empty single-token <context>",
        "refuse-contextless-context",
    ),
)


@pytest.mark.parametrize(
    ("reason", "expected_defect"),
    [(r, d) for r, d, _ in _DECLARATION_SAMPLES],
    ids=[form for _, _, form in _DECLARATION_SAMPLES],
)
def test_two_grammar_lint_classifies_the_ruled_sample_declarations(
    reason: str, expected_defect: str | None
) -> None:
    """R1c self-check: the lint accepts each ruled valid form — the prereq
    grammar the cross-check's probe-backed tier verifies live, and the
    context grammar the informational tier reports — and refuses each ruled
    invalid form: unmarked prose, and a context marker without a context."""

    defect = _declaration_defect(reason)
    if expected_defect is None:
        assert defect is None, (
            f"the two-grammar lint must accept {reason!r}; "
            f"defect={defect!r}"
        )
    else:
        assert defect is not None, (
            f"the two-grammar lint must refuse {reason!r} "
            f"({expected_defect!r})"
        )
        assert expected_defect in defect, (
            f"the refusal must name the defect {expected_defect!r}: "
            f"{defect!r}"
        )


def test_manifest_declarations_carry_one_of_the_two_grammars() -> None:
    """R1c: the two-grammar mandate, linted over the committed manifest.
    Every expected_skip reason must start with ``ranex-prereq:<probe>:``
    (hard tier — the probe-backed cross-check verifies it live both
    directions) or ``ranex-context:<context>:`` (informational tier — the
    declaration names its context; ``context_mismatches`` reports it,
    never hard). Unmarked prose is refused; a context marker without a
    non-empty ``<context>`` token is refused too — RED until the manifest
    is reworded through the freeze ceremony."""

    manifest = json.loads(
        (REPO_ROOT / "governance" / "suite_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    declared = manifest["expected_skips"]
    violators = [
        f"{test_id}: {defect}: {reason!r}"
        for test_id, reason in sorted(declared.items())
        if (defect := _declaration_defect(reason)) is not None
    ]
    assert not violators, (
        f"{len(violators)} expected_skip declaration(s) carry neither "
        "declaration grammar — reword them through the freeze ceremony "
        f"into '{_prereqs.REASON_PREFIX}<probe>:' (context-independent, "
        f"probe-verifiable) or '{_CONTEXT_MARKER}<context>:' "
        "(context-bound, the context named):\n" + "\n".join(violators)
    )


# --- 3. normalizer grammar freeze ---------------------------------------------

_DIGEST_A = "sha256:" + "a" * 64
_DIGEST_B = "sha256:" + "b" * 64
_SID_A = mint_component(now=1_000_000_000.0)
_SID_B = mint_component(now=1_000_000_100.5)

_VOLATILE_PAIRS = (
    # (class id, sample A, sample B, expected normalized bytes)
    (
        "digest",
        f"subject {_DIGEST_A} frozen",
        f"subject {_DIGEST_B} frozen",
        "subject <DIGEST> frozen",
    ),
    (
        "abs-path",
        "tee /tmp/pytest-abc123/enabled/transcript.txt done",
        "tee /home/ops/run-77/enabled/transcript.txt done",
        "tee <ABS-PATH> done",
    ),
    (
        "timestamp",
        "at 2026-08-19T07:31:04Z gate",
        "at 2026-08-19T07:31:04.915222+00:00 gate",
        "at <TIMESTAMP> gate",
    ),
    (
        "duration",
        "took 0.042s wall",
        "took 1m02.500s wall",
        "took <DURATION> wall",
    ),
    (
        "sid",
        f"sid {_SID_A} chain",
        f"sid {_SID_B} chain",
        "sid <SID> chain",
    ),
    (
        "sid-chain",
        f"sid {_SID_A}/{_SID_B} chain",
        f"sid {_SID_B}/{_SID_A} chain",
        "sid <SID> chain",
    ),
    (
        "pid",
        "child pid=4242 exited",
        "child pid=999999 exited",
        "child pid=<PID> exited",
    ),
    (
        "port",
        "listening port=34765 ready",
        "listening port=51003 ready",
        "listening port=<PORT> ready",
    ),
    (
        "rel-path",
        "golden tests/e2e/expected/provisioning.out differs",
        "golden tests/e2e/expected/observability.out differs",
        "golden <REL-PATH> differs",
    ),
)


@pytest.mark.parametrize(
    ("sample_a", "sample_b", "expected"),
    [(a, b, e) for _, a, b, e in _VOLATILE_PAIRS],
    ids=[name for name, _, _, _ in _VOLATILE_PAIRS],
)
def test_each_volatile_class_normalizes_two_live_values_identically(
    sample_a: str, sample_b: str, expected: str
) -> None:
    """Positive fixtures: two different live values of one volatile class
    normalize to the same bytes — the golden recorded from one run diffs
    clean against a run producing the other."""

    assert _prereqs.normalize_transcript(sample_a) == expected
    assert _prereqs.normalize_transcript(sample_b) == expected


def test_ordered_grammar_is_deterministic_on_a_full_transcript() -> None:
    """All classes interleaved: same input, same normalized bytes, byte for
    byte — and the ordered result is pinned exactly."""

    transcript = (
        f"run 2026-08-19T07:31:04Z subject {_DIGEST_A}\n"
        f"path /tmp/pytest-abc123/enabled/t.txt sid {_SID_A}/{_SID_B} "
        "pid=4242 port=34765\n"
        "duration 0.042s golden tests/e2e/expected/provisioning.out "
        "verdict PASS exit code 0\n"
    )
    expected = (
        "run <TIMESTAMP> subject <DIGEST>\n"
        "path <ABS-PATH> sid <SID> pid=<PID> port=<PORT>\n"
        "duration <DURATION> golden <REL-PATH> verdict PASS exit code 0\n"
    )
    assert _prereqs.normalize_transcript(transcript) == expected
    assert _prereqs.normalize_transcript(transcript) == (
        _prereqs.normalize_transcript(transcript)
    )


@pytest.mark.parametrize(
    ("meaningful_a", "meaningful_b"),
    [
        ("verdict PASS", "verdict FAIL"),
        ("exit code 0", "exit code 1"),
        ("failure in test_first_delegation", "failure in test_cold_start_journey"),
        ("gate landing CANDIDATE", "gate landing PASS"),
    ],
    ids=["verdict", "exit-code", "test-name", "gate-verdict"],
)
def test_meaningful_values_stay_discriminating(
    meaningful_a: str, meaningful_b: str
) -> None:
    """Negative fixtures: over-masking is refused — values that carry
    verdict meaning must survive normalization as different bytes."""

    assert (
        _prereqs.normalize_transcript(meaningful_a)
        != _prereqs.normalize_transcript(meaningful_b)
    ), (
        f"normalizer masked the difference between {meaningful_a!r} and "
        f"{meaningful_b!r}; meaningful values stay discriminating"
    )


def test_sabotaged_golden_diffs_dirty_with_untruncated_hunk() -> None:
    """The red control: mutate a golden's meaningful byte and the
    comparator must diff dirty, naming the first differing hunk."""

    run_a = (
        f"run 2026-08-19T07:31:04Z subject {_DIGEST_A} verdict PASS\n"
        f"sid {_SID_A} pid=4242 duration 0.042s\n"
    )
    run_b = (
        f"run 2026-08-19T09:15:44Z subject {_DIGEST_B} verdict PASS\n"
        f"sid {_SID_B} pid=999999 duration 1m02.500s\n"
    )
    golden = _prereqs.normalize_transcript(run_a)
    assert _prereqs.compare_transcript(
        _prereqs.normalize_transcript(run_b), golden
    ) is None, "same-class different live values must diff clean"

    sabotaged = golden.replace("verdict PASS", "verdict FAIL")
    assert sabotaged != golden, "sabotage fixture must change the golden"
    with pytest.raises(AssertionError) as refused:
        _prereqs.compare_transcript(_prereqs.normalize_transcript(run_b), sabotaged)
    message = str(refused.value)
    assert "@@" in message, (
        f"the failure must carry the unified diff hunk: {message!r}"
    )
    assert "FAIL" in message, (
        f"the first differing hunk must appear untruncated: {message!r}"
    )


def test_normalizer_is_one_centralized_function_without_mask_inputs() -> None:
    """Masks live in one audited function: a single `text` parameter and
    nothing else — per-test and per-family mask lists cannot be injected
    through the signature."""

    parameters = list(inspect.signature(_prereqs.normalize_transcript).parameters)
    assert parameters == ["text"], (
        f"normalize_transcript must take exactly one argument (text); got "
        f"{parameters}. Masking is centralized, never per-call-site."
    )
    # Remediation R5d (recorded transformation): the golden-directory sweep
    # that lived here was dead code — tests/e2e/expected/ does not exist on
    # this tree, so the `if` could never fire. It was made LIVE (not
    # removed) in test_exactly_one_normalizer_entry_point_under_tests_e2e
    # below, alongside the structural centralization sweeps.


def test_reason_prefix_constant_is_the_one_grammar() -> None:
    """One grammar, one place: the prefix constant the probes emit is the
    one the cross-check and the entrypoint grep."""

    assert _prereqs.REASON_PREFIX == "ranex-prereq:"
    assert re.escape(_prereqs.REASON_PREFIX) in re.escape(
        "ranex-prereq:signing_key:"
    )


# --- 3b. remediation arms: classifier, nodeid masking, comparator hunks --------


_JUNIT_XFAILED = (
    '<testcase classname="tests.contract.test_prereq_gates" '
    'name="test_xfailed_case" time="0.000"><skipped '
    'type="pytest.xfail" message="xfail condition: {reason}">'
    "xfail condition: {reason}</skipped></testcase>"
)
_JUNIT_XPASSED_STRICT = (
    '<testcase classname="tests.contract.test_prereq_gates" '
    'name="test_xpassed_strict_case" time="0.000"><failure '
    'type="pytest.xfail" message="XPASS(strict) {reason}">'
    "XPASS(strict) {reason}</failure></testcase>"
)
_JUNIT_XPASSED_SKIPPED = (
    '<testcase classname="tests.contract.test_prereq_gates" '
    'name="test_xpassed_skip_case" time="0.000"><skipped '
    'type="pytest.xpass" message="xpass {reason}">'
    "xpass {reason}</skipped></testcase>"
)


def test_junit_xfail_and_xpass_are_not_skip_ledger_entries(
    tmp_path: Path,
) -> None:
    """R5a: xfailed/xpassed entries are NOT skips — the frame's classifier
    must match the kernel's frozen semantics (suite_results.py:142-151:
    skipped+xfail marker -> xfailed; failure/skipped with an xpass marker ->
    xpassed). A ledger that counts them as skips would flag every strict
    xfail as an undeclared skip at entrypoint time."""

    junit = _junitxml(
        tmp_path,
        _JUNIT_XFAILED.format(reason="boundary-one")
        + _JUNIT_XPASSED_STRICT.format(reason="boundary-two")
        + _JUNIT_XPASSED_SKIPPED.format(reason="boundary-three"),
        skipped=2,
        tests=3,
    )
    outcomes = _prereqs._junit_outcomes(junit)
    by_name = {
        test_id.split("::")[1]: outcome
        for test_id, (outcome, _) in outcomes.items()
    }
    assert by_name.get("test_xfailed_case") == "xfailed", (
        f"a <skipped type=pytest.xfail> entry classifies xfailed, kernel "
        f"semantics: {by_name!r}"
    )
    assert by_name.get("test_xpassed_strict_case") == "xpassed", (
        f"a strict-XPASS <failure type=pytest.xfail> entry classifies "
        f"xpassed, kernel semantics: {by_name!r}"
    )
    assert by_name.get("test_xpassed_skip_case") == "xpassed", (
        f"a <skipped type=pytest.xpass> entry classifies xpassed, kernel "
        f"semantics: {by_name!r}"
    )

    # The ledger consequence: with zero declarations, none of the three is
    # an "undeclared skip" — the cross-check stays honest.
    manifest = _manifest(tmp_path, {})
    assert _cross(manifest, junit) == [], (
        "xfail/xpass entries must not raise undeclared-skip findings"
    )


def test_nodeid_paths_stay_discriminating_while_volatile_relative_paths_mask() -> (
    None
):
    """R5b, decision pinned: a relative path immediately followed by `::` is
    a test nodeid and is NEVER masked — two failures in different files
    remain different bytes — while genuine volatile relative paths (tmp
    artifact paths, golden paths) still mask to <REL-PATH>."""

    failed_delegation = "failed tests/e2e/test_first_delegation.py::test_journey"
    failed_cold_start = "failed tests/e2e/test_cold_start_journey.py::test_journey"
    assert (
        _prereqs.normalize_transcript(failed_delegation)
        != _prereqs.normalize_transcript(failed_cold_start)
    ), (
        "over-masking refused: the normalizer masked two different test "
        "nodeids into equal bytes — which file failed is verdict meaning"
    )
    assert "tests/e2e/test_first_delegation.py" in _prereqs.normalize_transcript(
        failed_delegation
    ), "the nodeid's file path must survive normalization byte-for-byte"

    tmp_artifact_a = (
        "wrote pytest-tmp-of-worker/pytest-123/wired-child/report.txt out"
    )
    tmp_artifact_b = (
        "wrote pytest-tmp-of-worker/pytest-456/wired-child/report.txt out"
    )
    assert (
        _prereqs.normalize_transcript(tmp_artifact_a)
        == _prereqs.normalize_transcript(tmp_artifact_b)
    ), (
        "volatile relative artifact paths must still mask — two runs with "
        "different tmp locations normalize equal"
    )


_FAMILY = "first-delegation-family"


def _first_hunk_lines(actual: str, expected: str) -> list[str]:
    import difflib

    diff = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected (golden)",
            tofile="actual (run)",
            lineterm="",
        )
    )
    hunk: list[str] = []
    seen_header = False
    for line in diff:
        if line.startswith("@@"):
            if seen_header:
                break
            seen_header = True
        hunk.append(line)
    return hunk


def test_multi_hunk_mismatch_carries_exactly_the_first_hunk_and_names_the_family() -> (
    None
):
    """R5c: compare_transcript gains a family label; on a >=2-hunk mismatch
    the failure carries EXACTLY the first hunk (every line present, the
    second hunk absent) and names the family. The trailing-newline-only
    case is covered with the family named too."""

    parameters = list(inspect.signature(_prereqs.compare_transcript).parameters)
    assert parameters == ["actual", "expected", "family"], (
        f"compare_transcript must take (actual, expected, family); got "
        f"{parameters}. The family label is how a failure names its golden."
    )

    filler = [f"common-line-{index}" for index in range(2, 9)]
    expected = "\n".join(
        ["start", "HUNK-ONE-EXPECTED", *filler, "HUNK-TWO-EXPECTED", "end"]
    )
    actual = "\n".join(
        ["start", "HUNK-ONE-ACTUAL", *filler, "HUNK-TWO-ACTUAL", "end"]
    )
    # sanity: the inputs really produce two diff hunks at default context
    hunk_lines = _first_hunk_lines(actual, expected)
    assert any("HUNK-TWO" in line for line in _all_hunks(actual, expected)), (
        "fixture precondition: the sabotage must produce >= 2 hunks"
    )

    with pytest.raises(AssertionError) as refused:
        _prereqs.compare_transcript(actual, expected, family=_FAMILY)
    message = str(refused.value)
    assert _FAMILY in message, (
        f"the failure must name the golden's family: {message!r}"
    )
    for line in hunk_lines:
        assert line in message, (
            f"every line of the FIRST hunk must appear untruncated "
            f"(missing {line!r}): {message!r}"
        )
    assert "HUNK-TWO-EXPECTED" not in message and "HUNK-TWO-ACTUAL" not in message, (
        f"the second hunk must be absent — exactly one hunk, never the "
        f"whole diff: {message!r}"
    )

    # the two-argument call still returns None on a clean diff (the frozen
    # mechanism arms call it exactly that way)
    assert _prereqs.compare_transcript(actual, actual, family=_FAMILY) is None
    assert _prereqs.compare_transcript(actual, actual) is None

    # trailing-newline-only difference: named exactly, family named
    with pytest.raises(AssertionError) as newline_only:
        _prereqs.compare_transcript("start\n", "start", family=_FAMILY)
    newline_message = str(newline_only.value)
    assert "trailing-newline" in newline_message, (
        f"a trailing-newline-only diff must be named exactly: "
        f"{newline_message!r}"
    )
    assert _FAMILY in newline_message


def _all_hunks(actual: str, expected: str) -> list[str]:
    import difflib

    return list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected (golden)",
            tofile="actual (run)",
            lineterm="",
        )
    )


_MASK_CONFIG_NAME = re.compile(
    r"^(?:masks?)\.(?:ya?ml|json|toml|txt|cfg|ini)$|\.masks\.", re.IGNORECASE
)


def test_exactly_one_normalizer_entry_point_under_tests_e2e() -> None:
    """R5d, structural: exactly one normalizer entry point lives under
    tests/e2e — no sibling ``normalize_*`` function a family slice could
    hand mask inputs to — no mask-config file ships anywhere under the e2e
    tree, and the golden convention (plain ``<family>.out`` transcripts
    only in tests/e2e/expected/, whenever it ships) is evaluated LIVE on
    every run (the dead conditional sweep from
    test_normalizer_is_one_centralized_function_without_mask_inputs was
    folded in here — recorded transformation)."""

    normalizers: set[tuple[str, str]] = set()
    for path in sorted(E2E_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("normalize"):
                normalizers.add((path.relative_to(E2E_DIR).as_posix(), node.name))
    assert normalizers == {("_prereqs.py", "normalize_transcript")}, (
        f"the ONE normalizer entry point is _prereqs.normalize_transcript; "
        f"siblings with their own normalize_* entry points are the "
        f"centralization hole: {sorted(normalizers)}"
    )

    mask_configs = sorted(
        path.relative_to(E2E_DIR).as_posix()
        for path in E2E_DIR.rglob("*")
        if path.is_file() and _MASK_CONFIG_NAME.match(path.name)
    )
    assert not mask_configs, (
        f"no mask config may ship under tests/e2e — masks live in one "
        f"audited function, never a config file: {mask_configs}"
    )

    expected_dir = E2E_DIR / "expected"
    non_out = sorted(
        path.relative_to(E2E_DIR).as_posix()
        for path in expected_dir.rglob("*")
        if path.is_file() and path.suffix != ".out"
    ) if expected_dir.is_dir() else []
    assert not non_out, (
        f"tests/e2e/expected/ holds plain <family>.out goldens only — no "
        f"config file a family could add masks through: {non_out}"
    )


_REAL_READ_TEXT = Path.read_text


def _bind_proc_facts(
    monkeypatch: pytest.MonkeyPatch,
    *,
    uid_map: str = "1000 1000 65536\n",
    cgroup: str = "0::/delegated\n",
    controllers: str = "cpu memory pids\n",
) -> None:
    """Inject identical /proc facts under both copies of the limitation
    probe (both read them through Path.read_text). Unknown paths fall
    through to the real filesystem."""

    def _read_text(self: Path, *args: object, **kwargs: object) -> str:
        posix = self.as_posix()
        if posix == "/proc/self/uid_map":
            return uid_map
        if posix == "/proc/self/cgroup":
            return cgroup
        if posix.endswith("/cgroup.controllers"):
            return controllers
        return _REAL_READ_TEXT(self, *args, **kwargs)  # type: ignore[return-value]

    monkeypatch.setattr(Path, "read_text", _read_text)


def _load_spine_evidence_module():
    """Load tests/e2e/test_run_produces_evidence.py as a module, with its
    ``from conftest import ...`` resolving to tests/e2e/conftest.py exactly
    as the e2e suite's own import mode resolves it."""

    e2e_conftest_spec = importlib.util.spec_from_file_location(
        "conftest", E2E_DIR / "conftest.py"
    )
    assert e2e_conftest_spec is not None and e2e_conftest_spec.loader is not None
    e2e_conftest = importlib.util.module_from_spec(e2e_conftest_spec)
    saved_conftest = sys.modules.get("conftest")
    sys.modules["conftest"] = e2e_conftest
    try:
        e2e_conftest_spec.loader.exec_module(e2e_conftest)
        spec = importlib.util.spec_from_file_location(
            "spine_evidence_module", E2E_DIR / "test_run_produces_evidence.py"
        )
        assert spec is not None and spec.loader is not None
        spine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spine)
    finally:
        if saved_conftest is not None:
            sys.modules["conftest"] = saved_conftest
        else:
            sys.modules.pop("conftest", None)
    return spine


def test_frame_qualification_limitation_matches_the_spine_copy_on_identical_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R5d, drift pin: _prereqs._qualification_host_limitation mirrors
    tests/e2e/test_run_produces_evidence.py's frozen copy — identical
    injected inputs (uid map, launcher build closure, cgroup controllers,
    user namespaces) must yield the same output from both: both None, or
    the identical limitation string. If either copy drifts, this reddens."""

    spine = _load_spine_evidence_module()

    import launcher_host

    scenarios: list[tuple[str, dict[str, str], str | None, str | None]] = [
        # name, /proc bindings, build limitation, userns limitation
        ("uid-map-blank", {"uid_map": "\n"}, "not-reached", "not-reached"),
        (
            "build-closure-limitation",
            {},
            "injected build closure drift",
            None,
        ),
        ("controllers-missing", {"controllers": "cpu io\n"}, None, None),
        ("userns-limitation", {}, None, "injected userns limitation"),
        ("all-clear", {}, None, None),
    ]
    for name, proc_facts, build, userns in scenarios:
        _bind_proc_facts(monkeypatch, **proc_facts)
        monkeypatch.setattr(
            launcher_host, "build_closure_limitation", lambda b=build: b
        )
        monkeypatch.setattr(
            launcher_host, "userns_limitation", lambda u=userns: u
        )
        monkeypatch.setattr(
            spine, "build_closure_limitation", lambda b=build: b
        )
        monkeypatch.setattr(spine, "userns_limitation", lambda u=userns: u)

        frame_verdict = _prereqs._qualification_host_limitation()
        spine_verdict = spine._qualification_host_limitation()
        assert frame_verdict == spine_verdict, (
            f"scenario {name!r}: the frame's qualification limitation "
            f"drifted from the spine's frozen copy on identical inputs — "
            f"frame={frame_verdict!r} spine={spine_verdict!r}"
        )
        assert frame_verdict is None or (
            isinstance(frame_verdict, str) and frame_verdict
        ), (
            f"scenario {name!r}: the limitation output shape is None or a "
            f"non-empty string, not {frame_verdict!r}"
        )
