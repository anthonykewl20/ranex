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
                                       cannot be injected
    compare_transcript(actual, expected) -> None
                                       byte-exact compare; on mismatch the
                                       AssertionError carries the unified
                                       diff of the first differing hunk,
                                       untruncated
    cross_check_skips(manifest_path, junitxml_path) -> list[str]
                                       both directions at entrypoint time:
                                       "undeclared skip: <id>: <reason>" and
                                       "declared skip not observed: <id>:
                                       <reason>"; [] when honest
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
    assert _prereqs.prereq_or_skip(probe_name) is None, (
        f"prereq_or_skip({probe_name!r}) skipped or signaled while its "
        "probe says present — the frame refuses probe-says-present-but-"
        "fixture-skipped"
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
    # Golden conventions: tests/e2e/expected/ holds plain <family>.out
    # transcripts only — no config file a family could add masks through.
    expected_dir = E2E_DIR / "expected"
    if expected_dir.is_dir():
        for path in sorted(expected_dir.rglob("*")):
            if path.is_file():
                assert path.suffix == ".out", (
                    f"{path} is not a plain <family>.out golden; no mask "
                    "config ships beside goldens"
                )


def test_reason_prefix_constant_is_the_one_grammar() -> None:
    """One grammar, one place: the prefix constant the probes emit is the
    one the cross-check and the entrypoint grep."""

    assert _prereqs.REASON_PREFIX == "ranex-prereq:"
    assert re.escape(_prereqs.REASON_PREFIX) in re.escape(
        "ranex-prereq:signing_key:"
    )
