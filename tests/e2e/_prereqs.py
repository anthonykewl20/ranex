"""SLICE-055 / ADR-032 — the real-e2e frame's one library module.

Issue #35's exact ownership. Everything the family slices (SLICE-056+) and
the README-documented entrypoint compose lives here:

  - the six frozen probes, each returning exactly ``(ok, reason)`` with the
    machine-greppable reason grammar ``ranex-prereq:<name>:``, and
    ``prereq_or_skip`` for the consuming module-scoped fixtures
    (tests/e2e/conftest.py);
  - the declared-skip cross-check against the committed suite manifest —
    direction (a) hard everywhere for undeclared observed skips, its REASON
    comparison a hard-tier obligation only (the orchestrator's R1d ruling
    on issue #35: ``ranex-prereq:`` declarations compare declared-vs-
    observed reasons exactly; ``ranex-context:`` declarations are reported
    by ``context_mismatches``, never byte-compared), direction (b) hard
    for probe-backed declarations (reason grammar
    ``ranex-prereq:<name>:``, live probe verdict named) and informational
    for context-bound ones (``ranex-context:<context>:``,
    ``context_mismatches``, which also reports the context tier's
    observed-drift skips — a declared context skip observed with a
    differing live message is named ID + declared context + observed
    message) — plus the ``cross-check`` script exit contract the
    documented entrypoint composes;
  - the golden-transcript normalizer (one centralized, single-argument
    function with the frozen ordered grammar; test nodeids stay
    discriminating bytes) and its byte-exact comparator (family-labelled,
    exactly-the-first-hunk failure output);
  - the subprocess-coverage wiring (append-never-replace PYTHONPATH, absolute
    ``COVERAGE_PROCESS_START``, one shared absolute ``COVERAGE_FILE`` home),
    the child-ledger combine/report helpers (loud no-data naming the wired
    child; unwired children reported unmeasured, never alarming), and the
    pre-run artifact-home writability probe.

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
import tempfile
from collections.abc import Mapping
from pathlib import Path
from xml.etree import ElementTree

E2E_DIR = Path(__file__).resolve().parent
REPO_ROOT = E2E_DIR.parents[1]

#: The subprocess hook's home directory. Appended LAST to a wired child's
#: PYTHONPATH (append-never-replace, ADR-032). LAST is the direction that
#: protects the CHILD: this directory rides behind every real package root,
#: so it can never shadow a package the child imports. The mirror risk is
#: real and NOT prevented by ordering (remediation M9, corrected rationale):
#: Python imports the FIRST ``sitecustomize`` found on the path, so an
#: EARLIER PYTHONPATH entry carrying its own ``sitecustomize`` shadows the
#: hook and the child silently measures nothing — that residual silence is
#: exactly what the loud wired-child no-data detection
#: (``combine_coverage``'s children ledger) exists to catch.
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

#: The informational tier's declaration grammar (the two-grammar scheme
#: ruled on issue #35): a declared reason starting
#: ``ranex-context:<context>:`` names the context it belongs to —
#: hermetic-freeze-context conditions not reproducible in the entrypoint's
#: documented environment. The frame REPORTS this tier (ID + observed
#: message + declared context, via ``context_mismatches``) and never
#: byte-compares its reasons: the orchestrator's R1d ruling records that
#: 37 host-observed skips emit live messages from other slices' frozen
#: test files — 27 of them dynamically composed — so exact comparison is
#: unsatisfiable without prohibited mass frozen-test churn.
CONTEXT_MARKER = "ranex-context:"

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
#
# Scoped application (recorded in the slice file's done-criteria contracts and
# on issue #35, 2026-08-19): direction (a) is hard everywhere — every observed
# skip must be declared — while its REASON comparison is a hard-tier
# obligation only (the orchestrator's R1d ruling on the Worker B blocker):
# a ``ranex-prereq:`` declaration compares declared-vs-observed reasons
# exactly; a ``ranex-context:`` declaration is reported, never byte-compared.
# Direction (b) is the probe-backed lie detector, a two-tier outcome keyed
# on the declaration's own reason grammar:
#
#   - a declared reason that STARTS WITH ``ranex-prereq:<probe_name>:`` (the
#     one grammar this module freezes) has opted into frame verification: it
#     is probe-backed, and when its test runs instead of skipping the finding
#     is hard, naming the live probe verdict on the running host — a present
#     verdict locates the lie in the declaration (prune it); an absent verdict
#     names that the declared context did not hold and the fixture ran anyway.
#   - any other reason is non-probe-backed — a context-bound declaration
#     (hermetic-freeze-context conditions not reproducible in the entrypoint's
#     documented environment). The manifest is deliberately multi-context, so
#     these are reported as an informational context-mismatch list (names +
#     count, ``context_mismatches``), never as an exit condition: an unscoped
#     direction (b) would make AC1 unsatisfiable on any single host.
#
# The frozen mechanism tests stay green unchanged under this scope: their
# fixture declarations use the grammar, so both fixture directions keep the
# hard outcome wherever the tests run — the probe's live answer decorates the
# hard finding, it never demotes a probe-backed one.


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

    Remediation R5a: xfail/xpass classification mirrors the kernel's frozen
    semantics (ranex/foundation/suite_results.py:142-151) exactly — a
    ``<skipped>`` entry whose type/message marker carries ``xfail`` is
    ``xfailed``; a ``<failure>``/``<skipped>`` whose marker carries ``xpass``
    is ``xpassed``. Neither is a skip-ledger entry: a ledger that counted
    them as skips would flag every strict xfail as an undeclared skip at
    entrypoint time. The DTD/entity refusal mirrors the kernel too: a
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
        reason = child.get("message") or (child.text or "").strip()
        # The kernel's marker shape: type and message, lowercased, grepped
        # for the xfail/xpass words — the only x-axis the kernel's frozen
        # classifier reads (suite_results.py:142-151).
        marker = f"{child.get('type', '')} {child.get('message', '')}".lower()
        if kind == "error":
            outcomes[test_id] = ("error", "")
        elif kind == "failure":
            outcomes[test_id] = ("xpassed" if "xpass" in marker else "failed", "")
        elif "xfail" in marker:
            outcomes[test_id] = ("xfailed", reason)
        elif "xpass" in marker:
            outcomes[test_id] = ("xpassed", reason)
        else:
            outcomes[test_id] = ("skipped", reason)
    return outcomes


#: A declared reason starting ``ranex-prereq:<probe_name>:`` names the frame
#: probe that can verify its stated precondition — the mapping that makes a
#: declaration probe-backed. Built from PROBE_NAMES, so the grammar and the
#: probe library cannot drift apart.
_PROBE_DECLARATION_RE = re.compile(
    rf"{re.escape(REASON_PREFIX)}(?P<name>{'|'.join(PROBE_NAMES)}):"
)


def _probe_backed_declaration(reason: str) -> str | None:
    """The frame probe a declared reason names, or ``None`` when the reason
    does not use the grammar (a non-probe-backed, context-bound declaration)."""

    match = _PROBE_DECLARATION_RE.match(reason)
    return match.group("name") if match is not None else None


def _context_tier_declaration(reason: str) -> bool:
    """Is this declared reason a WELL-FORMED context-tier declaration?

    Mirrors the frozen R1c lint's acceptance exactly (marker, non-empty
    single-token ``<context>`` slot, colon, non-empty prose): the R1d
    exemption from direction (a)'s byte comparison belongs only to
    honestly classified context declarations. An unmarked, malformed, or
    otherwise unknown declaration can no longer exist (the lint refuses
    it at freeze time), but if one somehow reaches here it fails CLOSED —
    it does not get the exemption and falls into the exact comparison.
    """

    if not reason.startswith(CONTEXT_MARKER):
        return False
    rest = reason[len(CONTEXT_MARKER) :]
    context, colon, prose = rest.partition(":")
    return (
        bool(colon)
        and bool(context)
        and not any(char.isspace() for char in context)
        and bool(prose.strip())
    )


def _declared_not_observed(
    declared: dict[str, str], outcomes: dict[str, tuple[str, str]]
) -> list[tuple[str, str]]:
    """Declared ``(test_id, reason)`` pairs whose test was observed running.

    Only IDs the junitxml actually observed: an ID absent from the junitxml
    is a suite-composition question, and full ID-set diffing is gate
    evaluate's frozen job (SLICE-009), not the skip ledger's.
    """

    return [
        (test_id, declared[test_id])
        for test_id in sorted(declared)
        if (observed := outcomes.get(test_id)) is not None and observed[0] != "skipped"
    ]


def cross_check_skips(manifest_path, junitxml_path) -> list[str]:
    """The HARD tier of the declared-skip ledger, at entrypoint time.

    Direction one — an observed skip with no declaration — names the test ID
    and the OBSERVED skip reason; it is hard unconditionally. Direction one
    also compares REASONS (remediation R1d, pinned to EXACT string equality
    by the frozen arm) as a HARD-TIER obligation only, per the
    orchestrator's ruling on the Worker B blocker (#35, 2026-08-19): a skip
    declared ``ranex-prereq:`` whose observed reason drifted from the
    declaration is a ``skip reason mismatch:`` finding naming BOTH strings
    — an outcome-blind freeze cannot be allowed to launder a reworded
    skip, and a prereq-tier declaration whose observed message cannot
    carry the marker is misclassified (the classification honesty rule:
    reclassify it context-tier through the freeze ceremony, never silence
    the finding). A skip declared ``ranex-context:`` is EXEMPT from the
    byte comparison — reported by :func:`context_mismatches` (ID + observed
    message + declared context), never compared here; anything the
    two-grammar lint would refuse fails closed into the comparison.
    Direction two — a probe-backed declaration whose test ran and did not
    skip — names the ID, the DECLARED reason, and the live verdict of the
    frame probe the declaration's grammar named: a present verdict locates
    the lie in the declaration (prune it); an absent verdict names that
    the declared context did not hold on this host and the test ran
    anyway. Non-probe-backed declarations (``ranex-context:<context>:``,
    the two-grammar scheme's informational tier) whose tests ran are NOT
    hard findings — they are the multi-context manifest's honest shape and
    are reported by :func:`context_mismatches`.
    Returns [] when the hard ledger is honest; otherwise one greppable line
    per finding.

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
        if outcome != "skipped":
            continue
        declared_reason = declared.get(test_id)
        if declared_reason is None:
            findings.append(f"undeclared skip: {test_id}: {reason}")
        elif _context_tier_declaration(declared_reason):
            # The R1d ruling: ranex-context: declarations are reported
            # (context_mismatches names ID + declared context + observed
            # message), never byte-compared — their live messages come
            # from other slices' frozen files, often dynamically composed.
            continue
        elif declared_reason != reason:
            findings.append(
                f"skip reason mismatch: {test_id}: "
                f"declared={declared_reason!r} observed={reason!r} "
                "(direction (a)'s reason comparison is the hard tier — "
                "a ranex-prereq: declaration and its live skip message "
                "must be the same bytes; a declaration the two-grammar "
                "lint would refuse fails closed into this comparison)"
            )
    for test_id, declared_reason in _declared_not_observed(declared, outcomes):
        probe_name = _probe_backed_declaration(declared_reason)
        if probe_name is None:
            continue  # informational tier — context_mismatches reports it
        ok, probe_reason = _PROBES[probe_name]()
        if ok:
            findings.append(
                f"declared skip not observed: {test_id}: {declared_reason} "
                f"[frame probe {probe_name} says present on this host — "
                f"{probe_reason}; the declaration is stale: prune it]"
            )
        else:
            findings.append(
                f"declared skip not observed: {test_id}: {declared_reason} "
                f"[frame probe {probe_name} says absent on this host — "
                f"{probe_reason}; the declared context did not skip here and "
                f"the test ran anyway]"
            )
    return findings


def context_mismatches(manifest_path, junitxml_path) -> list[str]:
    """The informational tier: context-bound declarations, reported never compared.

    Two reported shapes, both informational (never an exit condition):

    - declared-but-not-observed skips whose reason is NOT probe-backed —
      hermetic-freeze-context conditions (sealed-env toolchain absence,
      the materialised sample's missing sibling fork, unshare-denied
      hosts, cold-start re-entry) not reproducible in the entrypoint's
      documented environment. The manifest is multi-context by design, so
      these are names plus a count in the artifact: this list being
      non-empty is the honest report of one host running another
      context's ledger, not a lie.
    - observed-drift skips (the R1d ruling's machine-greppable promise): a
      declared ``ranex-context:`` skip that WAS observed skipping with a
      differing live message — the report names the test ID, the declared
      context, and the observed message, because the context tier is
      reported, never byte-compared. The declared-and-observed-agree case
      is not a mismatch and never appears here.

    Probe-backed declarations never appear here in either shape — they are
    cross_check_skips' hard tier (exact reason comparison, live probe
    verdicts). Entries are ordered by test ID.
    """

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    declared = manifest.get("expected_skips")
    if not isinstance(declared, dict):
        raise ValueError("suite manifest must carry an expected_skips object")
    outcomes = _junit_outcomes(Path(junitxml_path))
    lines: dict[str, str] = {}
    for test_id, declared_reason in _declared_not_observed(declared, outcomes):
        if _probe_backed_declaration(declared_reason) is None:
            lines[test_id] = f"context-mismatch: {test_id}: {declared_reason}"
    for test_id in sorted(outcomes):
        outcome, observed = outcomes[test_id]
        if outcome != "skipped" or test_id not in declared:
            continue
        declared_reason = declared[test_id]
        if _probe_backed_declaration(declared_reason) is not None:
            continue  # the hard tier's exact comparison owns prereq declarations
        if not _context_tier_declaration(declared_reason):
            continue  # unmarked/malformed — cross_check_skips fails closed on it
        if declared_reason == observed:
            continue  # declared and observed agree — the faithful case
        lines[test_id] = (
            f"context-mismatch: {test_id}: {declared_reason} "
            f"[observed here with a different message: {observed}]"
        )
    return [lines[test_id] for test_id in sorted(lines)]


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
# starting inside a longer token. Remediation R5b: a relative path
# immediately followed by "::" is a test NODEID — which file failed is
# verdict meaning, so nodeids are NEVER masked ("two failures in different
# files never normalize equal"). The path body is atomic ((?>...), Python
# 3.11+) so the refusal cannot be backtracked around: without it the engine
# would retry a shorter final segment (masking "tests/e2e/test_x.py" down
# to "tests/e2e/test_x.p" and leaving a stray "y::..."), and the negative
# lookahead alone would not keep two different nodeids discriminating.
_REL_PATH_RE = re.compile(
    r"(?<![\w./-])(?>(?:[A-Za-z0-9._+@-]+/)+[A-Za-z0-9._+@-]+)(?!::)"
)


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


def compare_transcript(actual: str, expected: str, family: str | None = None) -> None:
    """Byte-exact compare; on mismatch the AssertionError carries the diff.

    Remediation R5c: ``family`` names the golden's family label, and the
    failure carries EXACTLY the first hunk of the unified diff — every line
    of it, untruncated, the second hunk absent (one hunk names the first
    divergence; the whole diff would bury it) — never a bare ``assert
    False`` (ADR-032 sad path 3). A difference that survives splitlines()
    (trailing newline only) is named exactly, family named too. Returns
    None on a clean diff so same-class different live values provably pass.
    """

    family_note = (
        f"golden family {family!r}" if family else "golden family (none named)"
    )
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
    if not diff:
        # Only reachable when the inputs differ in nothing splitlines() keeps —
        # a trailing-newline difference. Name it exactly instead of emitting a
        # hunk-less failure.
        raise AssertionError(
            f"golden transcript mismatch ({family_note}) — "
            "trailing-newline difference only: "
            f"actual={actual!r} expected={expected!r}"
        )
    hunk: list[str] = []
    seen_hunk_header = False
    for line in diff:
        if line.startswith("@@"):
            if seen_hunk_header:
                break  # the second hunk header ends the first differing hunk
            seen_hunk_header = True
        hunk.append(line)
    raise AssertionError(
        f"golden transcript mismatch ({family_note}) — first differing "
        "hunk, untruncated:\n" + "\n".join(hunk)
    )


# --- subprocess coverage wiring (the coverage.py pattern, ADR-032) --------------


class CoverageDataMissing(RuntimeError):
    """A frame-wired child produced no parallel data file — loud, never a fake zero.

    coverage.py's hook silently no-ops when its environment is absent, which
    makes "measured zero" and "never measured" byte-identical upstream. The
    frame promised the hook to exactly the children it wired, so for those
    children — and only those — absence is this loud failure. Children the
    frame does not wire are reported unmeasured (report_unmeasured, fed the
    run's child ledger) and never alarm.
    """


def wire_child_environment(base: dict[str, str], *, coverage_home=None) -> dict[str, str]:
    """Wire a child environment for subprocess coverage — append, never replace.

    The hook directory (HOOK_DIR) is APPENDED LAST to the child's PYTHONPATH:
    the spine's own ``ranex()`` helper replaces PYTHONPATH outright, which is
    the recorded way a hook silently dies in a ``cwd=<clone>`` child
    (tests/e2e/test_gating_real_suite.py, ADR-032 sad path 14). ``last`` is
    what keeps THIS directory from shadowing a real package a child imports
    (remediation M9): it rides behind every package root. What LAST cannot
    prevent — the corrected rationale — is the mirror case: an EARLIER
    PYTHONPATH entry carrying its own ``sitecustomize`` shadows the hook,
    because Python imports the first ``sitecustomize`` it finds; that
    residual silence is the wired-child no-data detection's job
    (combine_coverage's ``children`` ledger), not the ordering's.
    ``COVERAGE_PROCESS_START`` names this repository's pyproject.toml
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


def _coverage_wired(env: Mapping[str, str]) -> bool:
    """Did the frame promise this child a coverage measurement?

    Remediation R2's honest scope, accounting for the venv wrinkle
    discovered on the canonical host (a1_coverage.pth in site-packages
    starts coverage in ANY child carrying COVERAGE_PROCESS_START — the
    PYTHONPATH hook is not the only measurement path): a child is "wired"
    exactly when its environment carries a coverage start switch. A child
    with NO coverage environment at all is unwired — no promise, no data
    expected, never an alarm.
    """

    return bool(env.get("COVERAGE_PROCESS_START")) or bool(
        env.get("COVERAGE_PROCESS_CONFIG")
    )


def combine_coverage(home, children: Mapping[str, Mapping[str, str]] | None = None) -> str:
    """``coverage combine --keep`` over the retained parallel inputs in ``home``.

    Inputs are retained (--keep) so the operation is idempotent the honest
    way: a second combine over the same retained immutable inputs reproduces
    identical combined data (installed coverage deletes inputs without
    --keep, so a "second combine is a no-op" claim would be false — ADR-032
    Consequences).

    Remediation R2: ``children`` is the run's child ledger — a mapping of
    child ID to the environment that child ran with — and the loud no-data
    detection consumes it. A frame-WIRED child (its environment carries a
    coverage start switch, see :func:`_coverage_wired`) that produced no
    parallel data file fails loudly as CoverageDataMissing NAMING THE CHILD:
    the hook's silent no-op must never read as a measured zero. A run whose
    ledger holds only unwired children never alarms — nothing was promised
    — and combines nothing when there is nothing to combine (the returned
    path is then the home's combined-file location, which need not exist;
    no data is claimed). Without ``children`` the loud detection stays
    home-scoped as before: no parallel data files at all is a refusal.
    Parallel files carry no child identity, so when data exists the combine
    proceeds for the whole home; per-child attribution of a silent wired
    child beside measured siblings is the ledger's honest limit.
    """

    home = Path(home)
    parallel = [p for p in home.glob(".coverage.*") if p.name != ".coverage"]
    if not parallel and children is not None:
        wired = sorted(
            child_id
            for child_id, env in children.items()
            if _coverage_wired(env)
        )
        if wired:
            raise CoverageDataMissing(
                f"no parallel coverage data files in {home} — frame-wired "
                f"children produced no data: {', '.join(wired)}; was "
                "sitecustomize shadowed off their PYTHONPATH, or did they "
                "exit before any atexit save?"
            )
        # An unwired-only ledger that measured nothing never alarms — no
        # promise was made, so nothing is combined and nothing is claimed
        # (the returned location need not exist; the report of these
        # children belongs to report_unmeasured).
        return str(home / ".coverage")
    if not parallel:
        raise CoverageDataMissing(
            f"no parallel coverage data files in {home} — a frame-wired child "
            "produced no data; was sitecustomize absent from its PYTHONPATH?"
        )
    # The combiner's own environment is stripped of the measurement
    # switches — COVERAGE_PROCESS_START and, symmetrically,
    # COVERAGE_PROCESS_CONFIG (the combiner must never auto-start): under
    # an entrypoint session the tool child would otherwise import the
    # hook off the inherited PYTHONPATH and race its own combine.
    tool_env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("COVERAGE_PROCESS_START", "COVERAGE_PROCESS_CONFIG")
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


def report_unmeasured(children: Mapping[str, Mapping[str, str]]) -> str:
    """The non-alarming report for the children the frame did not wire.

    Remediation R2: consumes the run's real child ledger (child id -> the
    environment that child ran with) and REFUSES a bare label string — the
    report must be built from what actually ran, not from a hand-passed
    name. A child is unmeasured exactly when its environment carries no
    coverage start switch (:func:`_coverage_wired`): the frozen spine's
    hookless clone children are expected to produce no data; they are
    reported unmeasured and must not false-alarm — the loud no-data
    detection is scoped to frame-wired children only.
    """

    if not isinstance(children, Mapping):
        raise TypeError(
            "report_unmeasured consumes the run's child ledger — a mapping "
            "of child id to the environment that child ran with, never a "
            f"hand-passed label string; got {type(children).__name__}: "
            f"{children!r}"
        )
    unmeasured = sorted(
        child_id
        for child_id, env in children.items()
        if not _coverage_wired(env)
    )
    if not unmeasured:
        if not children:
            return "unmeasured: (none — the ledger holds no children)"
        return (
            "unmeasured: (none — every child in the ledger was frame-wired "
            "for subprocess coverage)"
        )
    return (
        "unmeasured: " + ", ".join(unmeasured)
        + " — not frame-wired (no coverage environment); no subprocess "
        "coverage expected or recorded"
    )


def probe_artifact_home_writable(home) -> None:
    """The entrypoint's pre-run artifact-home probe (remediation R3).

    An artifact home that cannot be written fails LOUDLY — a RuntimeError
    naming the home and "not writable" — BEFORE any suite run writes a
    single artifact into it: no junitxml, no transcript, no partial run
    discovered half a suite later. The probe writes and removes one
    throwaway file, so a writable home is left byte-identical, and a home
    that does not yet exist is created (parents included) exactly as the
    entrypoint would. Returns None quietly on the writable path.
    """

    home = Path(home)
    try:
        home.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix=".ranex-e2e-writable-probe-", dir=home
        ):
            pass  # created and removed: the home is left untouched
    except OSError as error:
        raise RuntimeError(
            f"artifact home {home} is not writable "
            f"({type(error).__name__}: {error}) — refusing before any suite "
            "run writes a single artifact"
        ) from error
    return None


# --- the cross-check script (the entrypoint's nonzero-on-mismatch step) ---------


def _main(argv: list[str]) -> int:
    if len(argv) == 4 and argv[1] == "cross-check":
        manifest, junitxml = Path(argv[2]), Path(argv[3])
        findings = cross_check_skips(manifest, junitxml)
        for finding in findings:
            print(finding)
        if findings:
            return 1
        mismatches = context_mismatches(manifest, junitxml)
        for mismatch in mismatches:
            print(mismatch)
        if mismatches:
            print(
                f"context-mismatch count: {len(mismatches)} (informational: "
                "declared context-tier skips that either did not skip in "
                "this entrypoint environment or were observed with a "
                "different live message — reported, never byte-compared; "
                "exit unaffected)"
            )
        print(
            "skip cross-check: honest — every observed skip is declared, "
            "every ranex-prereq: declaration carried the same reason "
            "bytes, and no probe-backed declaration failed to occur "
            "(ranex-context: declarations are listed above as "
            "informational mismatches, never byte-compared)"
        )
        return 0
    print(
        "usage: _prereqs.py cross-check <suite_manifest.json> <junitxml>",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
