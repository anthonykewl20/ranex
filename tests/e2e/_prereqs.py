"""SLICE-055 / ADR-032 — the real-e2e frame's one library module.

Issue #35's exact ownership. Everything the family slices (SLICE-056+) and
the README-documented entrypoint compose lives here:

  - the six frozen probes, each returning exactly ``(ok, reason)`` with the
    machine-greppable reason grammar ``ranex-prereq:<name>:``, and
    ``prereq_or_skip`` for the consuming module-scoped fixtures
    (tests/e2e/conftest.py);
  - the declared-skip cross-check (both directions) against the committed
    suite manifest, plus the ``cross-check`` script exit contract the
    documented entrypoint composes;
  - the golden-transcript normalizer (one centralized, single-argument
    function with the frozen ordered grammar) and its byte-exact comparator;
  - the subprocess-coverage wiring (append-never-replace PYTHONPATH, absolute
    ``COVERAGE_PROCESS_START``, one shared absolute ``COVERAGE_FILE`` home)
    and the combine/report helpers.

This module imports nothing from ``ranex`` and nothing heavy at import time:
it is imported by bare child interpreters (the frozen cross-process probe
test runs it with only ``PATH`` and ``HOME`` in the environment) and it runs
as the ``cross-check`` script where ``ranex`` is not importable at all. Every
repository import is therefore lazy and inside the function that needs it,
mirroring the off-state laziness rule the ADR-031 substrate set
(src/ranex/observability/sid.py's socket precedent).

junitxml ID convention: mirrors the kernel's frozen ``_test_id``/``_outcome``
shapes from ranex/foundation/suite_results.py (classname
``tests.contract.<module>`` -> ``tests/contract/<module>.py::<name>``). The
convention is mirrored locally rather than imported because the cross-check
script must run without ``src`` on the path — the module is the convention's
consumer, never its second owner.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

E2E_DIR = Path(__file__).resolve().parent
REPO_ROOT = E2E_DIR.parents[1]

#: The subprocess hook's home directory. Appended LAST to a wired child's
#: PYTHONPATH (append-never-replace, ADR-032): last, so nothing on the path
#: can shadow the hook — and so the hook directory can never shadow a real
#: package (``coverage`` itself) that a child needs to import.
HOOK_DIR = E2E_DIR / "coverage"

#: The coverage config the wiring names: this repository's pyproject.toml
#: carries the frozen ``[tool.coverage]`` run/report block (source=src/ranex,
#: parallel=true, fail-under). Kept relative-to-``source`` deliberately — see
#: wire_child_environment.
COVERAGE_CONFIG = REPO_ROOT / "pyproject.toml"

#: One grammar, one place: every probe reason starts with this prefix, so a
#: skip ledger, a grep, and an entrypoint finding all name the precondition
#: the same way (tests/contract/test_prereq_gates.py freezes this constant).
REASON_PREFIX = "ranex-prereq:"

#: The default shared coverage home under the ignored ``.local/*`` territory
#: (ADR-032): every wired process's ``parallel=true`` suffix file
#: (``.coverage.<host>.<pid>.<rand>``) lands in this one directory, whose
#: names match no other ignore pattern — the ignored home is what keeps them
#: from dirtying a freeze tree, and the entrypoint's sweeps around each run
#: keep stale inputs out of later combines.
DEFAULT_COVERAGE_HOME = REPO_ROOT / ".local" / "ranex-e2e" / "coverage"


def default_coverage_home() -> Path:
    """The one shared coverage data home (``.local/ranex-e2e/coverage``)."""
    return DEFAULT_COVERAGE_HOME


# --- the six frozen probes -----------------------------------------------------
#
# A probe answers "is this precondition present on this host, right now" as
# exactly (ok, reason). It is lazy (nothing runs until a consuming fixture
# asks) and never caches: every call re-evaluates against the live
# environment, so no answer crosses a module boundary or a process (git's
# test_lazy_prereq weakness, refused — frozen by
# test_probes_hold_no_cross_process_cache). A probe that ERRORS raises loudly;
# only a genuinely absent precondition yields (False, reason).

PROBE_NAMES = (
    "pinned_resolver",
    "network_available",
    "signing_key",
    "harness_fork",
    "openrouter_key",
    "qualified_host",
)


def pinned_resolver() -> tuple[bool, str]:
    """The resolver the committed pins cite, present and matching its pin.

    Generalizes tests/e2e/test_gating_real_suite.py's probe: the committed
    governance/deps.yaml names the resolver by path and sha256, and the
    precondition is both the file's presence and its digest.
    """

    import yaml  # runtime dependency; lazy so bare children stay import-light

    pins_path = REPO_ROOT / "governance" / "deps.yaml"
    if not pins_path.is_file():
        return False, (
            f"{REASON_PREFIX}pinned_resolver: governance/deps.yaml is not "
            "committed; the pinned resolver cannot be probed"
        )
    pins = yaml.safe_load(pins_path.read_text(encoding="utf-8"))
    path = Path(pins["resolver"]["path"])
    if not path.is_file():
        return False, (
            f"{REASON_PREFIX}pinned_resolver: the pinned resolver is absent "
            f"at {path}"
        )
    if hashlib.sha256(path.read_bytes()).hexdigest() != pins["resolver"]["sha256"]:
        return False, (
            f"{REASON_PREFIX}pinned_resolver: the resolver at {path} does "
            "not match the sha256 pinned in governance/deps.yaml"
        )
    return True, f"{REASON_PREFIX}pinned_resolver: present ({path})"


def network_available() -> tuple[bool, str]:
    """An outbound TCP connection to the real package index succeeds.

    Generalizes the spine's network_available: the precondition for any
    journey that reaches the real index, probed the same way (pypi.org:443,
    3s timeout) so a wired suite and its probe cannot disagree.
    """

    import socket  # lazy: the off-state import cost rule (sid.py precedent)

    probe = socket.socket()
    probe.settimeout(3)
    try:
        probe.connect(("pypi.org", 443))
    except OSError as error:
        return False, (
            f"{REASON_PREFIX}network_available: pypi.org:443 unreachable "
            f"({type(error).__name__}: {error})"
        )
    finally:
        probe.close()
    return True, f"{REASON_PREFIX}network_available: present (pypi.org:443 reachable)"


def signing_key() -> tuple[bool, str]:
    """``RANEX_SIGNING_KEY`` names an existing key file.

    The kernel convention (keygen, `run`, the e2e Signing registry) is a path
    to a private key file held outside the repository; an empty or dangling
    variable is an absent precondition, never a half-present one.
    """

    raw = os.environ.get("RANEX_SIGNING_KEY", "")
    if not raw:
        return False, (
            f"{REASON_PREFIX}signing_key: RANEX_SIGNING_KEY is unset or empty; "
            "run keygen outside the repository and export its path"
        )
    path = Path(raw)
    if not path.is_file():
        return False, (
            f"{REASON_PREFIX}signing_key: RANEX_SIGNING_KEY does not name an "
            f"existing key file ({raw})"
        )
    return True, f"{REASON_PREFIX}signing_key: present ({raw})"


def harness_fork() -> tuple[bool, str]:
    """``RANEX_HARNESS_DIR`` names the sibling harness fork directory.

    The variable the frozen harness-fork skips cite (manifest expected-skip
    reasons, tests/e2e/test_first_delegation.py): a materialised sample does
    not carry the fork, so the precondition is the directory's presence.
    """

    raw = os.environ.get("RANEX_HARNESS_DIR", "")
    if not raw:
        return False, (
            f"{REASON_PREFIX}harness_fork: RANEX_HARNESS_DIR is unset or empty; "
            "the sibling harness fork is not named"
        )
    if not Path(raw).is_dir():
        return False, (
            f"{REASON_PREFIX}harness_fork: RANEX_HARNESS_DIR does not name an "
            f"existing fork directory ({raw})"
        )
    return True, f"{REASON_PREFIX}harness_fork: present ({raw})"


def openrouter_key() -> tuple[bool, str]:
    """``OPENROUTER_API_KEY`` is set to a non-empty value.

    Mirrors tests/e2e/test_first_delegation.py's credential gate. The value
    itself is never echoed — a reason that printed the credential would leak
    it into every skip ledger and artifact transcript.
    """

    raw = os.environ.get("OPENROUTER_API_KEY", "")
    if not raw.strip():
        return False, (
            f"{REASON_PREFIX}openrouter_key: OPENROUTER_API_KEY is absent or "
            "empty; the first-delegation journey needs a real credential"
        )
    return True, f"{REASON_PREFIX}openrouter_key: present (value not echoed)"


def qualified_host() -> tuple[bool, str]:
    """This host can run the confinement acceptance surfaces.

    Generalizes the host-qualification limitation probe frozen by
    tests/e2e/test_run_produces_evidence.py (SLICE-017/018 shapes): uid mapping,
    the pinned launcher build closure, delegated cgroup-v2 controllers, and
    unprivileged user namespaces. A limitation string is an absent
    precondition with that string as its explanation; ``None`` means
    qualified. An unreadable kernel fact is reported the same way the frozen
    spine reports it, never guessed into a present.
    """

    limitation = _qualification_host_limitation()
    if limitation is not None:
        return False, f"{REASON_PREFIX}qualified_host: {limitation}"
    return True, (
        f"{REASON_PREFIX}qualified_host: present (delegated cgroup-v2 root "
        "and the pinned launcher build closure available)"
    )


def _launcher_host():
    """The shared host-qualification guards (tests/launcher_host.py).

    tests/conftest.py's path hook makes ``tests`` importable under pytest;
    the explicit insert keeps the probe honest when the module is imported
    outside a pytest collection (a family slice's subprocess, say).
    """

    tests_dir = E2E_DIR.parent
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))
    import launcher_host

    return launcher_host


def _qualification_host_limitation() -> str | None:
    """Name the SLICE-017 host-only prerequisite unavailable here, if any.

    Mirrors tests/e2e/test_run_produces_evidence.py's frozen limitation
    probe verbatim in its checks and their order — the probe generalizes
    that shape; it must not diverge from it.
    """

    try:
        uid_map = Path("/proc/self/uid_map").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not any(line.strip() for line in uid_map):
        return "the current user namespace has no uid mapping, so no cgroup delegation is reachable"
    launcher_host = _launcher_host()
    build_limitation = launcher_host.build_closure_limitation()
    if build_limitation is not None:
        return build_limitation
    try:
        cgroup_lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
        unified = [line.split("::", 1)[1] for line in cgroup_lines if "::" in line]
        if len(unified) != 1 or not unified[0].startswith("/"):
            return None
        root = Path("/sys/fs/cgroup") / unified[0].lstrip("/")
        controllers = set((root / "cgroup.controllers").read_text(encoding="utf-8").split())
    except OSError:
        return None
    missing = sorted({"cpu", "memory", "pids"} - controllers)
    if missing:
        return "the delegated cgroup is missing required controllers: " + ", ".join(missing)
    userns = launcher_host.userns_limitation()
    if userns is not None:
        return userns
    return None


_PROBES = {
    "pinned_resolver": pinned_resolver,
    "network_available": network_available,
    "signing_key": signing_key,
    "harness_fork": harness_fork,
    "openrouter_key": openrouter_key,
    "qualified_host": qualified_host,
}


def prereq_or_skip(name: str) -> None:
    """The consuming-fixture helper: skip exactly when the probe says absent.

    Returns ``None`` quietly when the precondition is present — the frame's
    sanctioned skip path never skips when its probe says present (the
    stale-declaration refusal ADR-032 adds at the fixture seam). An unknown
    probe name is a loud failure, never a skip of everything.
    """

    probe = _PROBES.get(name)
    if probe is None:
        raise ValueError(
            f"unknown prereq probe {name!r}; the frozen probes are {PROBE_NAMES}"
        )
    ok, reason = probe()
    if not ok:
        import pytest  # lazy: the library stays importable without a test runner

        pytest.skip(reason)
    return None


# --- the declared-skip cross-check, both directions ----------------------------


def _junit_test_id(testcase: ElementTree.Element) -> str:
    """The manifest's frozen nodeid convention (kernel ``_test_id`` shape)."""

    classname = testcase.get("classname")
    name = testcase.get("name")
    if not classname or not name:
        raise ValueError("junitxml testcase must carry classname and name")
    parts = classname.split(".")
    if "tests" in parts:
        parts = parts[parts.index("tests") :]
    return f"{'/'.join(parts)}.py::{name}"


def _junit_outcomes(junitxml_path: Path) -> dict[str, tuple[str, str]]:
    """Observed ``(outcome, skip_reason)`` per test ID, kernel ``_outcome`` shape.

    The DTD/entity refusal mirrors ranex/foundation/suite_results.py: a
    crafted junitxml must not expand entities into the ledger.
    """

    text = junitxml_path.read_text(encoding="utf-8")
    if re.search(r"<!\s*(?:doctype|entity)\b", text, re.IGNORECASE):
        raise ValueError("junitxml DTD and entity declarations are refused")
    # Bytes, like the kernel's parse: a str carrying an XML encoding
    # declaration is refused by ElementTree on Python <3.14, and the
    # declared range (>=3.11) must not decide this by interpreter.
    root = ElementTree.fromstring(text.encode("utf-8"))

    outcomes: dict[str, tuple[str, str]] = {}
    for testcase in root.iter():
        if testcase.tag.rsplit("}", 1)[-1] != "testcase":
            continue
        test_id = _junit_test_id(testcase)
        if test_id in outcomes:
            raise ValueError(f"duplicate test ID in junitxml: {test_id}")
        children = [
            child
            for child in testcase
            if child.tag.rsplit("}", 1)[-1] in {"skipped", "failure", "error"}
        ]
        if len(children) > 1:
            raise ValueError(f"junitxml testcase carries multiple outcome children: {test_id}")
        if not children:
            outcomes[test_id] = ("passed", "")
            continue
        child = children[0]
        kind = child.tag.rsplit("}", 1)[-1]
        if kind == "skipped":
            reason = child.get("message") or (child.text or "").strip()
            outcomes[test_id] = ("skipped", reason)
        else:
            outcomes[test_id] = (kind, "")
    return outcomes


def cross_check_skips(manifest_path, junitxml_path) -> list[str]:
    """Both directions of the declared-skip ledger, at entrypoint time.

    Direction one — an observed skip with no declaration — names the test ID
    and the OBSERVED skip reason. Direction two — a declaration whose test
    ran and did not skip — names the ID and the DECLARED reason; it fires
    only for IDs the junitxml actually observed, because an ID absent from
    the junitxml is a suite-composition question, and full ID-set diffing is
    gate evaluate's frozen job (SLICE-009), not the skip ledger's — the two
    are never ambiguated here. Returns [] when the ledger is honest;
    otherwise one greppable line per finding.

    ``suite freeze`` itself stays outcome-blind by frozen design; this check
    is the entrypoint's composition, never a manifest edit.
    """

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    declared = manifest.get("expected_skips")
    if not isinstance(declared, dict):
        raise ValueError("suite manifest must carry an expected_skips object")
    outcomes = _junit_outcomes(Path(junitxml_path))

    findings: list[str] = []
    for test_id in sorted(outcomes):
        outcome, reason = outcomes[test_id]
        if outcome == "skipped" and test_id not in declared:
            findings.append(f"undeclared skip: {test_id}: {reason}")
    for test_id in sorted(declared):
        observed = outcomes.get(test_id)
        if observed is not None and observed[0] != "skipped":
            findings.append(f"declared skip not observed: {test_id}: {declared[test_id]}")
    return findings


# --- the golden-transcript normalizer and comparator ----------------------------
#
# One audited function, one ordered grammar (ADR-032, frozen by
# tests/contract/test_prereq_gates.py): digests, absolute paths, timestamps,
# durations, chained SIDs, PIDs, ephemeral ports, then relative paths — in
# exactly that order. Two different live values of one volatile class must
# normalize to the same bytes; meaningful values (verdict words, exit codes,
# test names) stay discriminating. The signature takes exactly `text` —
# per-test or per-family masks cannot be injected, and over-masking is a
# reviewed golden edit, never a comparator hack.

# Digests as the repo canonically renders them: "<algorithm>:<hex>".
_DIGEST_RE = re.compile(r"\b(?:sha(?:256|384|512|1)|blake2[bs]|md5):[0-9a-f]{32,128}\b")

# Absolute POSIX paths. The lookbehind refuses to start a match mid-token:
# the "/" that joins two SID components is preceded by a word character, so
# a chained SID survives this rule intact for its own (a "/" leading an
# absolute path is preceded by whitespace or punctuation instead).
_ABS_PATH_RE = re.compile(r"(?<![\w.-])/(?:[A-Za-z0-9._+@-]+/)*[A-Za-z0-9._+@-]+")

# ISO-8601 moments as the kernel prints them, Z or offset, fractional or not.
_TIMESTAMP_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})\b"
)

# Durations: one or more number+unit segments ("0.042s", "1m02.500s").
_DURATION_RE = re.compile(
    r"\b\d+(?:\.\d+)?(?:ms|us|ns|h|m|s)(?:\d+(?:\.\d+)?(?:ms|us|ns|h|m|s))*"
)

# Chained SIDs: the frozen component shape from
# src/ranex/observability/sid.py —
# <yyyymmdd>T<hhmmss>.<frac>Z-<host>-<process> — one or more components
# joined by "/", masked as ONE token however deep the chain.
_SID_COMPONENT = r"\d{8}T\d{6}\.\d+Z-[A-Za-z0-9_-]{1,64}-\d{1,10}"
_SID_RE = re.compile(rf"\b{_SID_COMPONENT}(?:/{_SID_COMPONENT})*\b")

# PIDs and ephemeral ports as transcripts render them: "<key>=<number>".
_PID_RE = re.compile(r"\bpid(?P<sep>[=:]) ?\d{1,10}\b")
_PORT_RE = re.compile(r"\bport(?P<sep>[=:]) ?\d{1,5}\b")

# Relative paths: path-character runs joined by "/" that are not absolute
# (the absolute rule has already run). The lookbehind keeps the match from
# starting inside a longer token.
_REL_PATH_RE = re.compile(r"(?<![\w./-])(?:[A-Za-z0-9._+@-]+/)+[A-Za-z0-9._+@-]+")


def normalize_transcript(text: str) -> str:
    """Apply the frozen ordered grammar — the ONE centralized normalizer."""

    text = _DIGEST_RE.sub("<DIGEST>", text)
    text = _ABS_PATH_RE.sub("<ABS-PATH>", text)
    text = _TIMESTAMP_RE.sub("<TIMESTAMP>", text)
    text = _DURATION_RE.sub("<DURATION>", text)
    text = _SID_RE.sub("<SID>", text)
    text = _PID_RE.sub(r"pid\g<sep><PID>", text)
    text = _PORT_RE.sub(r"port\g<sep><PORT>", text)
    text = _REL_PATH_RE.sub("<REL-PATH>", text)
    return text


def compare_transcript(actual: str, expected: str) -> None:
    """Byte-exact compare; on mismatch the AssertionError carries the diff.

    The failure emits the first differing hunk of the unified diff,
    untruncated — never a bare ``assert False`` (ADR-032 sad path 3). Returns
    None on a clean diff so same-class different live values provably pass.
    """

    if actual == expected:
        return None
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
    seen_hunk_header = False
    for line in diff:
        if line.startswith("@@"):
            if seen_hunk_header:
                break  # the second hunk header ends the first differing hunk
            seen_hunk_header = True
        hunk.append(line)
    if not diff:
        # Only reachable when the inputs differ in nothing splitlines() keeps —
        # a trailing-newline difference. Name it exactly instead of emitting a
        # hunk-less failure.
        raise AssertionError(
            "golden transcript mismatch — trailing-newline difference only: "
            f"actual={actual!r} expected={expected!r}"
        )
    raise AssertionError(
        "golden transcript mismatch — first differing hunk, untruncated:\n"
        + "\n".join(hunk)
    )


# --- subprocess coverage wiring (the coverage.py pattern, ADR-032) --------------


class CoverageDataMissing(RuntimeError):
    """A frame-wired child produced no parallel data file — loud, never a fake zero.

    coverage.py's hook silently no-ops when its environment is absent, which
    makes "measured zero" and "never measured" byte-identical upstream. The
    frame promised the hook to exactly the children it wired, so for those
    children — and only those — absence is this loud failure. Children the
    frame does not wire are reported unmeasured (report_unmeasured) and
    never alarm.
    """


def wire_child_environment(base: dict[str, str], *, coverage_home=None) -> dict[str, str]:
    """Wire a child environment for subprocess coverage — append, never replace.

    The hook directory (HOOK_DIR) is APPENDED LAST to the child's PYTHONPATH:
    the spine's own ``ranex()`` helper replaces PYTHONPATH outright, which is
    the recorded way a hook silently dies in a ``cwd=<clone>`` child
    (tests/e2e/test_gating_real_suite.py, ADR-032 sad path 14). ``last``
    also means the hook directory can never shadow a real package a child
    imports. ``COVERAGE_PROCESS_START`` names this repository's pyproject.toml
    by absolute path — its ``[tool.coverage.run]`` source is deliberately
    RELATIVE, because installed coverage 7.15.3 resolves relative source
    entries against the child's own working directory
    (inorout.py: ``os.path.isdir(src)``), which is exactly what lets a
    clone-judges-clone child measure its own vendored copy of the kernel.
    ``COVERAGE_FILE`` pins every process's ``parallel=true`` suffix file into
    one shared absolute home (default: the ignored
    ``.local/ranex-e2e/coverage/``), so no data file ever scatters across a
    clone's working directory.
    """

    wired = dict(base)
    entries = [entry for entry in wired.get("PYTHONPATH", "").split(os.pathsep) if entry]
    wired["PYTHONPATH"] = os.pathsep.join([*entries, str(HOOK_DIR)])

    home = Path(coverage_home) if coverage_home is not None else default_coverage_home()
    home.mkdir(parents=True, exist_ok=True)
    wired["COVERAGE_PROCESS_START"] = str(COVERAGE_CONFIG)
    wired["COVERAGE_FILE"] = str(home / ".coverage")
    return wired


def combine_coverage(home) -> str:
    """``coverage combine --keep`` over the retained parallel inputs in ``home``.

    Inputs are retained (--keep) so the operation is idempotent the honest
    way: a second combine over the same retained immutable inputs reproduces
    identical combined data (installed coverage deletes inputs without
    --keep, so a "second combine is a no-op" claim would be false — ADR-032
    Consequences). Raises CoverageDataMissing loudly when no parallel data
    file exists — the frame-wired-child no-data detection. Returns the
    combined data file's absolute path.
    """

    home = Path(home)
    parallel = [p for p in home.glob(".coverage.*") if p.name != ".coverage"]
    if not parallel:
        raise CoverageDataMissing(
            f"no parallel coverage data files in {home} — a frame-wired child "
            "produced no data; was sitecustomize absent from its PYTHONPATH?"
        )
    # The combiner's own environment is stripped of the measurement switch:
    # under an entrypoint session the tool child would otherwise import the
    # hook off the inherited PYTHONPATH and race its own combine.
    tool_env = {
        key: value
        for key, value in os.environ.items()
        if key != "COVERAGE_PROCESS_START"
    }
    completed = subprocess.run(
        [sys.executable, "-m", "coverage", "combine", "--keep", str(home)],
        cwd=str(REPO_ROOT),
        env={**tool_env, "COVERAGE_FILE": str(home / ".coverage")},
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"coverage combine failed in {home}: {completed.stderr.strip()}"
        )
    combined = home / ".coverage"
    if not combined.is_file():
        raise CoverageDataMissing(
            f"coverage combine produced no combined data file in {home}"
        )
    return str(combined)


def report_unmeasured(label: str) -> str:
    """The non-alarming report for a child the frame did not wire.

    The frozen spine's hookless clone children are expected to produce no
    data; they are reported unmeasured and must not false-alarm — the loud
    no-data detection is scoped to frame-wired children only.
    """

    return (
        f"unmeasured: {label} — not frame-wired; no subprocess coverage "
        "expected or recorded"
    )


# --- the cross-check script (the entrypoint's nonzero-on-mismatch step) ---------


def _main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "cross-check":
        findings = cross_check_skips(Path(argv[2]), Path(argv[3]))
        for finding in findings:
            print(finding)
        if findings:
            return 1
        print(
            "skip cross-check: honest — every observed skip is declared and "
            "every declaration observed"
        )
        return 0
    print(
        "usage: _prereqs.py cross-check <suite_manifest.json> <junitxml>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
