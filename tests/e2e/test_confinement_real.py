"""SLICE-057 — real e2e: the execution family (confinement) on real data.

Issue #37's exact ownership (file 2 of 3), riding the ADR-032 frame: the
launcher build contract and, where the host qualifies, real strict-local
journeys — real launcher builds, real install/qualification, real
confined spawns whose results the kernel validates over a drained
teardown — with a rendered confinement report transcript compared
byte-exactly against ``expected/confinement-report.out`` through the one
centralized normalizer.

Host gating (issue #37 deterministic gate 5, sad path 1): the
strict-local arms consume the frame's ``qualified_host`` probe through
the module-scoped ``prereq_qualified_host`` fixture — on a host whose
pinned launcher build closure drifts (this one: ``/etc/ld.so.cache``)
the probe returns the machine-greppable
``ranex-prereq:qualified_host: <limitation>`` reason, the arms skip with
that named reason — never a silent green — and the assertions run when
capable. The launcher-build contract itself is NOT host-gated: SLICE-017
gate 1 freezes both of its branches as honest outcomes, and this file
reuses exactly those shapes — a build-closure-matching host proves two
clean builds byte-equal (with manifest artifact-digest agreement), a
foreign host proves the controller's fail-closed ``E-C17-BUILD-INPUT-DRIFT``
refusal with no partial artifact. The drift branch was executed against
the installed kernel at e84b5176a in the freeze-time prototype (two
roots, identical refusals); the reproducibility branch is frozen from
tests/integration/test_slice017_native_launcher.py gate 1's verified
shape and first executes for real on a closure-matching host.

The qualified-host journeys (real build → install → qualify → confined
``run --confinement strict-local``) are frozen from shapes the existing
suites already prove on qualified hosts: the real-session signing and
refusal propagation of tests/security/test_slice046_cmd_run_confinement.py,
the E-C18-LIMIT kill-and-refuse lifecycle of
tests/security/test_slice018_cgroup_output_lifecycle.py, and the
confinement-repo construction of tests/contract/test_trace_invariance.py.
They first execute for real on a qualified host — an honest UNKNOWN
until then, disclosed in the slice file rather than assumed away.

The shell-descendant and timeout contracts (issue #37 sad paths 3 and
8; sad path 3 as reframed by the orchestrator's sanctioned amendment
on #37 — the frozen survivor arm was ruled vacuous, and the first
reframe's unconstructibility claim was itself ruled an overclaim by
the final gate and rescoped to what the arm proves):

* SHELL-constructed descendants die, and the three layers are pinned
  to their call sites — every dash-mediated construction goes through
  the shell's async-job machinery, and three independent layers (the
  empty MS_NODEV tmpfs on /dev kills dash's job children at their
  pre-exec /dev/null open, Landlock admits EXECUTE on exactly the
  pinned objects/trees, and the worker is PID 1 of a new PID namespace
  the kernel reaps at init exit) kill those constructions before any
  survivor exists; the arm proves it with real observations — an
  outside poller holds the worker leaf's visible membership at the
  direct pair through a deliberate shell fork-exec attempt — and pins
  all three layers against the launcher source that ran. NOT claimed:
  descendant unconstructibility — a NON-shell argv[0] can sustain
  descendants under the current policy, and their containment is the
  recorded inheritance residual (the slice file's seccomp entry);
* a worker that exceeds its wall-time bound is killed and refused
  (``E-C18-LIMIT``, exit 2, no evidence) — distinct reporting — while a
  worker that exits 3 propagates exactly (``RECORDED exit=3``, run
  exits 3): no swallowed exit code, no hang dressed as a verdict; this
  timeout arm is also where the REAL kill/drain-over-drained-teardown
  proof lives (a genuine wall overrun, killed and refused).

The golden ``expected/confinement-report.out`` is the implementation
lane's artifact, captured from a real qualified-host run of this journey
through the normalizer. Its absence is this file's honest frozen red on
EVERY host: ``test_golden_contract_confinement_report`` holds the golden
to its existence/fixpoint/token contract ungated, so the freeze commit
is red here and green only once the real capture lands.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402
import launcher_host  # noqa: E402

from ranex.foundation.signing import signed_payload  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

FAMILY_PRODUCER = "execution-family"
CONFINED_CLAIM = "confined-observed"
LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_OUTPUT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
QUALIFICATION_REPORT = ".local/ranex/qualification/strict-local-v1.json"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
CONTROLLER = (sys.executable, "-m", "ranex.cli.host_confinement")
BUILD_INPUT_DRIFT = "E-C17-BUILD-INPUT-DRIFT"

#: See test_run_real.py's _STRIPPED_ENV for the rationale.
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
    "RANEX_TRACE",
    "RANEX_TRACE_EVENT",
    "RANEX_TRACE_PARENT_SID",
)

_ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

_GOLDEN = "confinement-report.out"


def ranex(
    subject: Path, argv: list[str], key: Path | None = None, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does (the clone judges the clone)."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(subject / "src")
    if key is not None:
        env["RANEX_SIGNING_KEY"] = str(key)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=subject,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=240,
    )


def controller(
    subject: Path, arguments: list[str]
) -> subprocess.CompletedProcess[str]:
    """Run the confinement controller the way ``run`` does: a real child
    process in the subject, the subject's own source on PYTHONPATH."""

    return subprocess.run(
        [*CONTROLLER, *arguments],
        cwd=subject,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(subject / "src"),
            "LC_ALL": "C",
            "TZ": "UTC",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly (the frozen red)."""

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-057 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey on a confinement-qualified host (the fixture "
        "below), pipe the rendered report through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


def _refusal_of(completed: subprocess.CompletedProcess[str]) -> dict[str, str]:
    assert completed.returncode != 0, completed.stdout + completed.stderr
    refusal = json.loads(completed.stdout)
    assert set(refusal) == {"refusal", "detail"}, refusal
    return refusal


def _clone_real(destination: Path, identity: str) -> None:
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, f"cannot clone the real subject: {cloned.stderr}"
    subprocess.run(
        ["git", "-C", str(destination), "config", "user.email", f"{identity}@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(destination), "config", "user.name", identity],
        check=True,
    )


def _register_producer(subject: Path, public: str) -> None:
    keyring = subject / "governance" / "producers.yaml"
    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == "producers:"), None)
    assert header is not None, "the committed keyring carries no producers: mapping"
    lines.insert(header + 1, f"  {FAMILY_PRODUCER}: {public}\n")
    keyring.write_text("".join(lines), encoding="utf-8")
    subprocess.run(["git", "-C", str(subject), "rm", "-q", "governance/deps.yaml"], check=True)
    subprocess.run(["git", "-C", str(subject), "add", "governance/producers.yaml"], check=True)
    subprocess.run(
        ["git", "-C", str(subject), "commit", "-q", "-m", "register the execution-family producer"],
        check=True,
    )


@dataclass
class ConfinementJourney:
    """Everything the frozen tests consume from the one module journey."""

    subject: Path
    key: Path
    public: str
    record: dict[str, object]
    recorded_transcript: str
    qualification: dict[str, object]
    report_text: str


@pytest.fixture(scope="module")
def journey(
    tmp_path_factory: pytest.TempPathFactory, prereq_qualified_host: None
) -> ConfinementJourney:
    """The one real journey: build, install, qualify, confine — on a
    host the frame's ``qualified_host`` probe has declared capable."""

    base = tmp_path_factory.mktemp("execution-family-confinement")
    subject = base / "subject"
    key = base / f"{FAMILY_PRODUCER}.key"
    _clone_real(subject, "execution-family-confinement")

    generated = ranex(subject, ["keygen", "--producer", FAMILY_PRODUCER], key=key)
    assert generated.returncode == 0, generated.stderr
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    public = match.group(1)
    _register_producer(subject, public)

    # --- the subject's own build, then two clean builds in different ------
    # --- absolute roots: all three byte-equal (issue #37's "two clean ----
    # --- builds byte-equal check reused from SLICE-017 gates"; a ---------
    # --- differing pair is the frozen red of sad path 2) ------------------
    built = controller(
        subject,
        ["launcher-build", "--manifest", LAUNCHER_MANIFEST,
         "--source", LAUNCHER_SOURCE, "--output", BUILD_OUTPUT],
    )
    assert built.returncode == 0, built.stdout + built.stderr
    digests = [(subject / BUILD_OUTPUT).read_bytes()]
    for name in ("repro-first", "repro-second"):
        root = base / name / "repository"
        _clone_real(root, f"execution-family-{name}")
        repro = controller(
            root,
            ["launcher-build", "--manifest", LAUNCHER_MANIFEST,
             "--source", LAUNCHER_SOURCE, "--output", BUILD_OUTPUT],
        )
        assert repro.returncode == 0, repro.stdout + repro.stderr
        digests.append((root / BUILD_OUTPUT).read_bytes())
    assert digests[0] == digests[1] == digests[2], (
        "clean launcher builds in different absolute roots produced "
        "different bytes — the pinned build is not reproducible "
        "(issue #37 sad path 2)"
    )
    manifest = json.loads((subject / LAUNCHER_MANIFEST).read_text(encoding="utf-8"))
    assert hashlib.sha256(digests[0]).hexdigest() == manifest["artifact"]["sha256"], (
        "the reproducible builds disagree with the manifest's artifact pin"
    )

    # --- install + qualify in the subject --------------------------------
    for arguments in (
        ["launcher-install", "--manifest", LAUNCHER_MANIFEST,
         "--artifact", BUILD_OUTPUT, "--destination", INSTALLED_LAUNCHER],
        ["qualify", "--profile", HOST_PROFILE, "--artifact", INSTALLED_LAUNCHER,
         "--manifest", LAUNCHER_MANIFEST, "--report", QUALIFICATION_REPORT],
    ):
        step = controller(subject, arguments)
        assert step.returncode == 0, step.stdout + step.stderr
    qualification = json.loads(
        (subject / QUALIFICATION_REPORT).read_text(encoding="utf-8")
    )

    # --- the real confined run: spawn, kill/drain, signed evidence -------
    (subject / ".local" / "ranex-e2e").mkdir(parents=True, exist_ok=True)
    evidence = ".local/ranex-e2e/confined-evidence.json"
    confined = ranex(
        subject,
        [
            "run", "--claim", CONFINED_CLAIM, "--producer", FAMILY_PRODUCER,
            "--repository", ".", "--evidence", evidence,
            "--confinement", "strict-local", "--", "/bin/sleep", "2",
        ],
        key=key,
    )
    assert confined.returncode == 0, (
        f"the confined run must complete (exit 0): {confined.stdout}{confined.stderr}"
    )
    assert confined.stdout.startswith("RECORDED"), confined.stdout
    record = json.loads((subject / evidence).read_text(encoding="utf-8"))[0]
    assert record["exit_code"] == 0
    for field in ("confinement_result_digest", "confinement_profile_digest"):
        value = record[field]
        assert isinstance(value, str) and re.fullmatch(
            r"[0-9a-f]{64}", value
        ), f"the confined record must bind {field}: {value!r}"

    report_text = (
        confined.stdout
        + f"confinement_result_digest=sha256:{record['confinement_result_digest']}\n"
        + f"confinement_profile_digest=sha256:{record['confinement_profile_digest']}\n"
        + "launcher_builds_reproducible=true\n"
        + f"qualification_schema={qualification['schema']}\n"
        + f"qualification_qualified={str(qualification['qualified']).lower()}\n"
    )

    return ConfinementJourney(
        subject=subject,
        key=key,
        public=public,
        record=record,
        recorded_transcript=confined.stdout,
        qualification=qualification,
        report_text=report_text,
    )


def _confined_run(journey: ConfinementJourney, evidence: str, *command: str):
    return ranex(
        journey.subject,
        [
            "run", "--claim", CONFINED_CLAIM, "--producer", FAMILY_PRODUCER,
            "--repository", ".", "--evidence", evidence,
            "--confinement", "strict-local", "--", *command,
        ],
        key=journey.key,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


# --- the any-host arms ---------------------------------------------------------


def test_golden_contract_confinement_report() -> None:
    """The confinement golden's own contract, held on EVERY host.

    This is the file's ungated red at the freeze commit: the golden does
    not exist until the implementation lane captures it from a real
    qualified-host run. Once captured it must carry the normalizer's own
    ``<DIGEST>`` token (the confinement digests are real volatile
    material), be a fixpoint of the normalizer, and name the family's
    discriminating claim so it can never be confused with the run
    family's golden.
    """

    golden = golden_text(_GOLDEN)
    assert "<DIGEST>" in golden, (
        f"{_GOLDEN} carries no <DIGEST> token: the journey's confinement "
        "digests are real volatile material the normalizer must have "
        "tamed — a golden without the token is hand-sanitized text"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        f"{_GOLDEN} is not a normalizer fixpoint: it still contains bytes "
        "the frozen grammar would mask, which no capture piped through "
        "normalize_transcript can"
    )
    assert CONFINED_CLAIM in golden, (
        f"{_GOLDEN} must name the confinement family's own claim "
        f"({CONFINED_CLAIM!r}) so it stays discriminating against the "
        "run family's golden"
    )


def test_two_root_launcher_builds_drift_or_reproduce(
    tmp_path: Path,
) -> None:
    """Issue #37 gate 3 / sad path 2 — SLICE-017 gate 1's shapes, reused.

    A build-closure-matching host must prove two clean builds in two
    different absolute roots byte-equal, agreeing with the manifest's
    artifact pin (a differing pair is the frozen red: the build is not
    reproducible). A foreign host's honest contract is the controller's
    fail-closed refusal: both builds refuse ``E-C17-BUILD-INPUT-DRIFT``
    and neither leaves a partial artifact.
    """

    limitation = launcher_host.build_closure_limitation()
    builds = []
    for name in ("drift-first", "drift-second"):
        root = tmp_path / name / "repository"
        _clone_real(root, f"execution-family-{name}")
        completed = controller(
            root,
            ["launcher-build", "--manifest", LAUNCHER_MANIFEST,
             "--source", LAUNCHER_SOURCE, "--output", BUILD_OUTPUT],
        )
        if limitation is not None:
            refusal = _refusal_of(completed)
            assert refusal["refusal"] == BUILD_INPUT_DRIFT, refusal
            assert not (root / BUILD_OUTPUT).exists(), (
                "a refused build must leave no partial artifact"
            )
        else:
            assert completed.returncode == 0, completed.stdout + completed.stderr
            builds.append((root / BUILD_OUTPUT).read_bytes())
    if limitation is None:
        assert len(builds) == 2
        assert builds[0] == builds[1], (
            "two clean builds in different absolute roots differ — the "
            "pinned build is not reproducible (issue #37 sad path 2)"
        )


# --- the qualified-host arms (probe-gated; assertions run when capable) --------


def test_strict_local_journey_matches_the_golden(journey: ConfinementJourney) -> None:
    """Issue #37 deterministic gate 3: real build, real spawn, real
    kill/drain observed — the rendered confinement report frozen against
    its golden.

    The kill/drain observation rides the evidence itself: the kernel
    admits a confinement result only over a validated, drained teardown
    (SLICE-018's lifecycle), so a completed confined run with a bound
    ``confinement_result_digest`` IS the observation that the worker
    tree was killed and drained. openssl independently verifies the
    signature over the record including both confinement digests.
    """

    openssl = shutil.which("openssl")
    assert openssl is not None, (
        "the openssl binary is a hard requirement of this family's "
        "independent re-check: a host without it fails honestly rather "
        "than skipping green"
    )
    scratch = journey.subject.parent / "openssl-recheck"
    scratch.mkdir(exist_ok=True)
    record = journey.record
    content = {k: v for k, v in record.items() if k != "signature"}
    (scratch / "payload.bin").write_bytes(signed_payload(content))
    signature = record["signature"]
    assert isinstance(signature, str) and signature.startswith("ed25519:"), signature
    (scratch / "sig.bin").write_bytes(base64.b64decode(signature.removeprefix("ed25519:")))
    raw_public = journey.public.removeprefix("ed25519:")
    (scratch / "pub.der").write_bytes(_ED25519_SPKI_PREFIX + base64.b64decode(raw_public))
    verified = subprocess.run(
        [
            openssl, "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
            "-inkey", str(scratch / "pub.der"), "-rawin",
            "-in", str(scratch / "payload.bin"),
            "-sigfile", str(scratch / "sig.bin"),
        ],
        capture_output=True, text=True, check=False,
    )
    assert verified.returncode == 0, (
        "openssl (a non-kernel tool) refused the confined record's "
        f"signature — including its confinement digest bindings: "
        f"{verified.stdout}{verified.stderr}"
    )
    assert journey.qualification["qualified"] is True, journey.qualification

    compare_golden(journey.report_text, _GOLDEN)


# --- the shell-descendant contract (the sanctioned reframing of the frozen ---
# --- survivor arm, rescoped to the proven claim by the final gate; the -------
# --- arm's docstring carries the full ruling) --------------------------------


#: The direct pair the worker cgroup leaf's VISIBLE membership
#: (``cgroup.procs``, read from outside) holds at steady state: the
#: launcher process and the worker command itself. Live processes in the
#: worker's PID namespace list steadily there — the worker command itself
#: proves it in this very construction (it spins in dash's wait-poll for
#: the whole refusal window while listed) — so a live descendant would
#: list steadily too.
_DIRECT_PROCESS_COUNT = 2

#: A GENUINE descendant — a live ``/bin/sleep`` the shell is waiting on —
#: would be a visible third member of the leaf for the run's whole
#: refusal window (~1 s of cumulative CPU budget or ~5 s of wall bound;
#: the construction refuses at ~1018 ms on this host). The forked job
#: child that dies pre-exec appears in the visible listing for at most a
#: sub-millisecond flicker at its fork (its corpse then holds an extra
#: ``pids.current`` pid un-reaped until teardown — a reap-timing
#: artifact this arm RECORDS but never asserts on). 150 ms is far beyond
#: any observed flicker (the in-suite one was 0.04 ms) and a ~7x margin
#: below any genuine footprint.
_SUSTAINED_DESCENDANT_MS = 150.0

#: The outside observation must not be vacuous: fewer samples than this,
#: or a shorter window, means the poller never really watched the leaf
#: and the assertions below would be green over nothing.
_MIN_PROBE_SAMPLES = 30
_MIN_PROBE_WINDOW_MS = 5.0

# Layer-1 pins: /dev's ENTIRE authority is one empty MS_NODEV tmpfs — no host
# device, no node creation ("adding a host device would be a policy widen").
# Pinned as mount_minimal_dev's whole BODY; the call-site binding (the final
# gate's P1-2 remedy) is _assert_three_layers_pinned's assemble_mounts call
# count below — a defined-but-uncalled mount is the vacuity the first
# reframe's definition-only pins could not see.
_PIN_MINIMAL_DEV_BODY = (
    'return mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC | MS_NODEV, '
    '"mode=755") == 0;'
)
# Layer-2 pins: the exact Landlock grant block (six path grants plus the two
# runtime-loader grants; libc is read-only, no EXECUTE) and the subject and
# toolchain trees' read-only access shape — fragments of enforce_landlock's
# body, asserted inside that body with the enforcer itself call-bound in
# worker_exec.
_PIN_LANDLOCK_RULES = (
    'executable_access = LANDLOCK_ACCESS_FS_EXECUTE | '
    'LANDLOCK_ACCESS_FS_READ_FILE; '
    'if (add_path_rule(ruleset_fd, executable_fd, executable_access) != 0 || '
    'add_runtime_loader_rule(ruleset_fd, "/lib64/ld-linux-x86-64.so.2", '
    'executable_access) != 0 || '
    'add_runtime_loader_rule(ruleset_fd, "/lib/x86_64-linux-gnu/libc.so.6", '
    'LANDLOCK_ACCESS_FS_READ_FILE) != 0 || '
    'add_path_rule(ruleset_fd, subject_fd, readonly_access) != 0 || '
    'add_path_rule(ruleset_fd, toolchain_fd, readonly_access) != 0 || '
    'add_path_rule(ruleset_fd, output_fd, filesystem_mask) != 0 || '
    'add_path_rule(ruleset_fd, scratch_fd, filesystem_mask) != 0 || '
    'syscall(SYS_landlock_restrict_self, ruleset_fd, 0U) != 0 || '
    'close(ruleset_fd) != 0) {'
)
_PIN_READONLY_ACCESS = (
    'const __u64 readonly_access = LANDLOCK_ACCESS_FS_EXECUTE | '
    'LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR;'
)
# Layer-3 pins: the namespace flag set (CLONE_NEWPID among them) and the
# fresh proc overlay — WHOLE BODIES of enter_worker_namespaces and
# mount_fresh_proc, call-bound in worker_exec together with the exec itself;
# together they make the exec'd command PID 1 of a new PID namespace.
_PIN_NAMESPACE_BODY = (
    'const int namespaces = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | '
    'CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWCGROUP; '
    'return unshare(namespaces) == 0;'
)
_PIN_FRESH_PROC_BODY = (
    'return mount("proc", "/proc", "proc", MS_NOSUID | MS_NOEXEC | MS_NODEV, '
    'NULL) == 0;'
)
_PIN_EXECVEAT = (
    '(void)syscall(SYS_execveat, 3, "", argv + argument_offset + 4, '
    'environment, AT_EMPTY_PATH); (void)close(3);'
)


def _launcher_code(text: str) -> tuple[str, list[bool]]:
    """The launcher C source as comment-free text (string and character
    literals kept verbatim), with a parallel per-character flag marking
    which emitted characters are code rather than literal contents.

    One string-aware scanner feeds both the whole-file shape grammar and
    the function-body extractor below, so a ``//`` or ``/*`` inside a
    literal can never be mistaken for a comment, and a brace or paren
    inside a literal never opens a body — the structural judgment the
    call-site pins stand on.
    """

    out: list[str] = []
    structural: list[bool] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        following = text[index + 1] if index + 1 < length else ""
        if char == "/" and following == "*":
            end = text.find("*/", index + 2)
            end = length if end < 0 else end + 2
            out.append(" ")
            structural.append(True)
            index = end
        elif char == "/" and following == "/":
            end = text.find("\n", index)
            index = length if end < 0 else end
        elif char in ('"', "'"):
            out.append(char)
            structural.append(False)
            index += 1
            while index < length:
                current = text[index]
                out.append(current)
                structural.append(False)
                index += 1
                if current == "\\":
                    if index < length:
                        out.append(text[index])
                        structural.append(False)
                        index += 1
                    continue
                if current == char:
                    break
        else:
            out.append(char)
            structural.append(True)
            index += 1
    return "".join(out), structural


def _launcher_code_shape(path: Path) -> str:
    """The launcher C source as one comment-free, whitespace-collapsed
    shape — prose edits never redden the pins, any behavioral or policy
    change does. (Structural descendant of the first reframe's regex
    stripper: byte-equivalent on this source, and correct under
    string-borne comment markers too.)"""

    code, _structural = _launcher_code(path.read_text(encoding="utf-8"))
    return re.sub(r"\s+", " ", code).strip()


def _parameter_list_owner(code: str, structural: list[bool], close_paren: int) -> str:
    """The function name owning the parameter list that closes at
    ``close_paren``: walk back (paren-depth aware, structural characters
    only) to the list's opening paren, then over whitespace, and take
    the identifier ending there."""

    depth = 0
    index = close_paren
    while index >= 0:
        if structural[index]:
            if code[index] == ")":
                depth += 1
            elif code[index] == "(":
                depth -= 1
                if depth == 0:
                    break
        index -= 1
    else:
        raise ValueError("unbalanced parentheses in launcher source")
    index -= 1
    while index >= 0 and (not structural[index] or code[index].isspace()):
        index -= 1
    name_end = index + 1
    while index >= 0 and structural[index] and (
        code[index].isalnum() or code[index] == "_"
    ):
        index -= 1
    return code[index + 1 : name_end]


def _matching_brace(code: str, structural: list[bool], open_brace: int) -> int:
    """The structural ``}`` matching the structural ``{`` at ``open_brace``."""

    depth = 0
    for index in range(open_brace, len(code)):
        if not structural[index]:
            continue
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unbalanced braces in launcher source")


def _launcher_function_bodies(path: Path) -> dict[str, str]:
    """Every top-level function of the launcher source as name → its
    comment-free, whitespace-collapsed body — the C-side form of the
    repo's structural pin precedent
    (test_only_host_confinement_module_may_name_host_confinement walks
    Python's ast; C has no stdlib parser and the one installed C parser
    is an undeclared transitive of cryptography, so this scanner is the
    test file's own structure walk). A depth-0 brace opened by a
    parameter list is a function body; braces and parens inside string
    or character literals never count. Pins scoped to a body therefore
    bind CALL SITES: removing a call from the function redds while
    comment edits stay green — the mutation probes recorded with the
    arm's rescope verify both directions.
    """

    code, structural = _launcher_code(path.read_text(encoding="utf-8"))
    bodies: dict[str, str] = {}
    depth = 0
    index = 0
    last_significant = -1
    length = len(code)
    while index < length:
        if not structural[index]:
            index += 1
            continue
        char = code[index]
        if char == "{":
            if (
                depth == 0
                and last_significant >= 0
                and code[last_significant] == ")"
            ):
                name = _parameter_list_owner(code, structural, last_significant)
                end = _matching_brace(code, structural, index)
                if name in bodies:
                    raise ValueError(
                        f"duplicate function definition in launcher source: {name}"
                    )
                bodies[name] = re.sub(r"\s+", " ", code[index + 1 : end]).strip()
                last_significant = end
                index = end + 1
                continue
            depth += 1
        elif char == "}":
            depth -= 1
            last_significant = index
        elif not char.isspace():
            last_significant = index
        index += 1
    return bodies


def _assert_three_layers_pinned(source: Path) -> None:
    """The arm's part (b), the final gate's P1-2 remedy: the three layers,
    pinned against the launcher source that was actually built and run —
    the DEFINITIONS as whole bodies AND the CALL SITES that make those
    definitions the worker's live construction (the first reframe pinned
    definition text only, so a defined-but-uncalled layer stayed green).
    """

    bodies = _launcher_function_bodies(source)

    def body(name: str) -> str:
        assert name in bodies, (
            f"the launcher source no longer defines {name}() — the layer "
            "pins bind the call sites inside it"
        )
        return bodies[name]

    worker_exec = body("worker_exec")
    assemble_mounts = body("assemble_mounts")
    minimal_dev = body("mount_minimal_dev")
    namespaces = body("enter_worker_namespaces")
    fresh_proc = body("mount_fresh_proc")
    landlock = body("enforce_landlock")
    loader_rule = body("add_runtime_loader_rule")

    # Layer 1 — the definition is the whole pinned body, /dev's only
    # authority, and assemble_mounts (what worker_exec runs) CALLS it.
    assert minimal_dev == _PIN_MINIMAL_DEV_BODY, (
        "layer 1 is not the pinned construction: /dev's entire authority "
        "must be the one empty MS_NODEV tmpfs (mount_minimal_dev)"
    )
    assert assemble_mounts.count("mount_minimal_dev()") == 1, (
        "layer 1 call-site drift: assemble_mounts must CALL "
        "mount_minimal_dev exactly once — a definition without the call "
        "leaves the worker's /dev unpopulated by the pinned empty tmpfs, "
        "the vacuity the first reframe's definition-only pins could not "
        "see (final gate P1-2)"
    )
    shape = _launcher_code_shape(source)
    assert shape.count("/dev") == 1 and "mknod" not in shape.lower(), (
        "layer 1 policy widen: the launcher source names /dev or device "
        "creation beyond the one empty-tmpfs mount — a populated /dev "
        "would let dash's async-job children survive to their exec attempt"
    )

    # Layer 2 — the exact grant block inside enforce_landlock's own body,
    # the rule counts at their pinned sites, and worker_exec CALLS the
    # enforcer.
    assert _PIN_LANDLOCK_RULES in landlock and _PIN_READONLY_ACCESS in landlock, (
        "layer 2 is not the pinned construction: the Landlock grant block "
        "(six path grants — argv[0]'s descriptor with EXECUTE, the loader "
        "with EXECUTE, read-only libc, read-only subject/toolchain, the "
        "two writable trees with the full mask) must be exactly this shape"
    )
    assert (
        shape.count("add_path_rule(ruleset_fd") == 6
        and shape.count("add_runtime_loader_rule(ruleset_fd") == 2
    ), (
        "layer 2 policy widen: the Landlock ruleset carries rule "
        "invocations beyond the pinned set (five grants in "
        "enforce_landlock plus the loader helper's own, and exactly two "
        "runtime-loader grants) — any added grant reddens this pin"
    )
    assert (
        landlock.count("add_path_rule(ruleset_fd") == 5
        and loader_rule.count("add_path_rule(ruleset_fd") == 1
        and landlock.count("add_runtime_loader_rule(ruleset_fd") == 2
    ), (
        "layer 2 call-site drift: the six grants must live at their "
        "pinned sites — five add_path_rule calls inside enforce_landlock "
        "plus the loader helper's own, and exactly two runtime-loader "
        "grants inside enforce_landlock"
    )
    assert worker_exec.count("enforce_landlock(") == 1, (
        "layer 2 call-site drift: worker_exec must CALL enforce_landlock "
        "exactly once — a ruleset defined but never enforced by the worker "
        "path is the vacuity definition-only pins could not see"
    )

    # Layer 3 — the unshare set (CLONE_NEWPID among the flags) as the whole
    # body of the function worker_exec calls, proc overlaid in the forked
    # child, exec last, and the whole construction order pinned inside
    # worker_exec's own body (call sites, not file positions).
    assert namespaces == _PIN_NAMESPACE_BODY, (
        "layer 3 is not the pinned construction: the worker's namespace "
        "set must include CLONE_NEWPID exactly as pinned (the kernel "
        "reaps the whole namespace at PID-1 exit)"
    )
    assert fresh_proc == _PIN_FRESH_PROC_BODY, (
        "layer 3 is not the pinned construction: the forked child must "
        "overlay fresh proc (mount_fresh_proc)"
    )
    assert (
        worker_exec.count("enter_worker_namespaces(") == 1
        and worker_exec.count("assemble_mounts(") == 1
        and worker_exec.count("mount_fresh_proc(") == 1
    ), (
        "layer 3 call-site drift: worker_exec must call "
        "enter_worker_namespaces, assemble_mounts, and mount_fresh_proc "
        "exactly once each"
    )
    assert _PIN_EXECVEAT in worker_exec, (
        "layer 3 is not the pinned construction: the forked child must "
        "exec via AT_EMPTY_PATH on the pre-opened descriptor — the "
        "command itself is the namespace's PID 1"
    )
    assert (
        worker_exec.index("enter_worker_namespaces(")
        < worker_exec.index("assemble_mounts(")
        < worker_exec.index("worker = fork();")
        < worker_exec.index("mount_fresh_proc(")
        < worker_exec.index("enforce_landlock(")
        < worker_exec.index(_PIN_EXECVEAT)
    ), (
        "layer 3 construction order drifted: namespaces are entered and "
        "mounts assembled before the fork, proc overlay and landlock "
        "happen in the forked child, and exec is last — that order is "
        "what makes the exec'd command PID 1 of the new PID namespace"
    )


class _WorkerLeafPoller(threading.Thread):
    """Sample the confined run's worker cgroup leaf from OUTSIDE, while the
    run is in flight (the SLICE-057 vacuity experiment's proven poller,
    brought in-suite): the session's cgroup root grows one
    ``ranex-slice018-*-worker`` leaf per confined run, and this thread
    samples its visible membership (``cgroup.procs``) and ``pids.current``
    as fast as sysfs answers."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        unified = Path("/proc/self/cgroup").read_text(encoding="utf-8")
        relative = unified.splitlines()[0].split("::", 1)[1]
        self._root = Path("/sys/fs/cgroup") / relative.lstrip("/")
        self._known = {
            leaf.name for leaf in self._root.glob("ranex-slice018-*-worker")
        }
        #: ``_stop_event``, never ``_stop``: that name shadows
        #: ``threading.Thread._stop`` on Python <=3.13, where ``join()``
        #: calls it at thread exit — ``TypeError: 'Event' object is not
        #: callable`` (final gate P1-3, reproduced on 3.12.3; the
        #: installed 3.14 removed ``Thread._stop``, which is why the
        #: shadow stayed silent here). The helper's whole attribute
        #: surface (_root, _known, _stop_event, _lock, samples) is
        #: audited collision-free against Thread on both installed
        #: generations (3.12, 3.14).
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        #: ``(t_ms, visible_members, pids_current)`` per sample — visible
        #: membership is the asserted descendant detector; pids.current is
        #: the recorded secondary (an un-reaped zombie corpse can hold an
        #: extra pid in it until teardown).
        self.samples: list[tuple[float, int, int]] = []

    def run(self) -> None:
        origin = time.monotonic()
        leaf: Path | None = None
        while not self._stop_event.is_set():
            try:
                if leaf is None or not leaf.exists():
                    leaf = None
                    for candidate in self._root.glob("ranex-slice018-*-worker"):
                        if candidate.name not in self._known:
                            leaf = candidate
                            break
                if leaf is not None:
                    members = (leaf / "cgroup.procs").read_text(encoding="ascii")
                    pids = int(
                        (leaf / "pids.current").read_text(encoding="ascii").strip()
                    )
                    with self._lock:
                        self.samples.append(
                            (
                                (time.monotonic() - origin) * 1000.0,
                                len(members.split()),
                                pids,
                            )
                        )
            except (OSError, ValueError):
                pass  # the leaf's birth/death windows race the reads

    def finish(self) -> list[tuple[float, int, int]]:
        self._stop_event.set()
        self.join(timeout=5.0)
        with self._lock:
            return list(self.samples)


def _confined_run_observed(
    journey: ConfinementJourney, evidence: str, *command: str
) -> tuple[int, str, str, list[tuple[float, int, int]]]:
    """One confined run whose worker cgroup leaf is sampled from outside
    the whole time — the ``ranex`` helper's exact environment, but a
    Popen so the poller can watch concurrently."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(journey.subject / "src")
    env["RANEX_SIGNING_KEY"] = str(journey.key)
    poller = _WorkerLeafPoller()
    poller.start()
    process = subprocess.Popen(
        [
            sys.executable, "-m", "ranex.cli.main",
            "run", "--claim", CONFINED_CLAIM, "--producer", FAMILY_PRODUCER,
            "--repository", ".", "--evidence", evidence,
            "--confinement", "strict-local", "--", *command,
        ],
        cwd=journey.subject,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        stdout, stderr = process.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr, poller.finish()


def test_shell_constructed_descendants_die_and_the_layers_are_pinned(
    journey: ConfinementJourney,
) -> None:
    """Issue #37 sad path 3, scoped to exactly what this arm proves.

    Lineage: the frozen ``test_worker_kill_drain_leaves_no_survivor``
    was ruled VACUOUS by the orchestrator's sanctioned amendment (its
    "backgrounded worker" never existed); the first reframe then claimed
    descendants are UNCONSTRUCTIBLE and containment holds BY
    CONSTRUCTION — an overclaim the final gate struck down (codex P1-2,
    confirmed): every construction that reframe tried goes through
    dash's async-job machinery, and under the current policy a NON-shell
    argv[0] CAN sustain a descendant. This is the honest rescope of that
    arm to its proven claim.

    PROVEN — SHELL-constructed descendants die, by three independent
    layers, observed live. Every dash-mediated construction (subshells,
    explicit redirects, pipelines — /tmp/opencode/slice057-survivor/
    EVIDENCE.md) funnels through the shell job machinery's pre-exec
    ``open("/dev/null")``:

    1. the worker's /dev is one empty MS_NODEV tmpfs (the profile
       declares no device nodes), so dash's job child dies at that
       open — pre-exec, in under a millisecond (the operative first
       killer);
    2. Landlock admits EXECUTE on exactly the pinned objects/trees —
       argv[0]'s pre-opened descriptor, the pinned ELF loader, the
       subject, toolchain, output, and scratch trees (libc is
       read-only) — so a job child that survived layer 1 would still be
       EACCES-denied at its exec of any other host binary;
    3. the worker is PID 1 of a new PID namespace, and the kernel
       SIGKILLs every process in a namespace when its init exits —
       nothing can outlive it.

    The runtime observation, with the polling numbers of the verified
    construction: an outside poller (~7-10 kHz) watches the worker
    cgroup leaf while ``sh -c '/bin/sleep 30 & wait $!'`` runs confined
    — the leaf's VISIBLE membership (``cgroup.procs``) sits steadily at
    exactly the direct pair (launcher + worker command) with no
    SUSTAINED third member; the in-suite verification held ~20000
    samples over ~1020 ms, the longest observed third-member flicker
    was 0.04 ms (the dying job child's un-reaped corpse may hold an
    extra ``pids.current`` pid until teardown — recorded, never
    asserted, because reap timing is host-dependent), and the run
    refuses at ~1018 ms with ``E-C18-LIMIT cpu_usage_usec`` — the
    wait-spin's cumulative-CPU refusal, itself evidence no live sleeper
    existed. 150 ms is the sustained-descendant threshold: far beyond
    any flicker, ~7x below any genuine footprint.

    NOT CLAIMED — descendant unconstructibility. A NON-shell argv[0] —
    a fork-and-loop program exec'd directly as the observed command —
    CAN sustain live descendants under the current policy (the seccomp
    filter is nr-only, so clone is admitted with any flags; Landlock
    granted EXECUTE on argv[0] itself). Their containment rests on the
    inheritance facts, the slice file's RECORDED RESIDUAL (seccomp+NNP+
    Landlock inherit; descendants stay in the PID namespace and the
    confined cgroup; cgroup.kill reaches nested namespaces; pids bounds
    the count) — not on anything this arm observes. The REAL kill/drain
    proof — a genuine wall-time overrun killed and refused over a
    drained teardown — is for the worker itself and lives where it
    already lives: ``test_timeout_refusal_is_distinct_from_the_exit_
    code`` below.

    The three layers are pinned against the launcher source that was
    actually built and run, bound to their CALL SITES (the repo's
    structural pin precedent:
    test_only_host_confinement_module_may_name_host_confinement): the
    source is scanned comment- and string-aware into per-function
    bodies, so prose edits stay green, any policy change reddens, and
    REMOVING A CALL reddens even with its definition intact — the
    vacuity the first reframe's definition-only pins could not see.

    Supersedes the frozen ``test_worker_kill_drain_leaves_no_survivor``
    and its own first reframe, ``test_descendant_processes_are_
    unconstructible_and_containment_is_by_construction``; the freeze
    ceremony retires the previous IDs' declarations and declares this
    arm's in the same act.
    """

    # --- (a) the runtime observation: the worker leaf, watched from outside
    evidence = ".local/ranex-e2e/confined-evidence-descendant-probe.json"
    code, stdout, stderr, samples = _confined_run_observed(
        journey, evidence, "/bin/sh", "-c", "/bin/sleep 30 & wait $!"
    )
    window_ms = samples[-1][0] - samples[0][0] if samples else 0.0
    assert len(samples) >= _MIN_PROBE_SAMPLES and window_ms >= _MIN_PROBE_WINDOW_MS, (
        f"the descendant-probe observation is vacuous — {len(samples)} "
        f"samples over {window_ms:.1f} ms of the worker cgroup leaf; the "
        "outside poller must genuinely watch the run (the in-suite "
        "verification observed ~20000 samples over ~1020 ms on this very "
        "construction)"
    )
    steady = Counter(visible for _, visible, _ in samples).most_common(1)[0][0]
    longest_ms = 0.0
    run_start: float | None = None
    run_last = 0.0
    for t_ms, visible, _ in samples:
        if visible > _DIRECT_PROCESS_COUNT:
            if run_start is None:
                run_start = t_ms
            run_last = t_ms
        elif run_start is not None:
            longest_ms = max(longest_ms, run_last - run_start)
            run_start = None
    if run_start is not None:
        longest_ms = max(longest_ms, run_last - run_start)
    assert steady == _DIRECT_PROCESS_COUNT and longest_ms < _SUSTAINED_DESCENDANT_MS, (
        "a fork-exec attempt of another binary left the worker cgroup's "
        f"visible membership above its direct pair: steady visible "
        f"members={steady} (want {_DIRECT_PROCESS_COUNT}), longest "
        f"sustained third-member excursion {longest_ms:.1f} ms (threshold "
        f"{_SUSTAINED_DESCENDANT_MS} ms) — a genuine descendant was "
        f"constructed and containment is NOT holding by construction "
        f"({len(samples)} samples over {window_ms:.1f} ms, max visible="
        f"{max(visible for _, visible, _ in samples)}, max "
        f"pids.current={max(pids for *_, pids in samples)})"
    )

    # The run's own outcome — the secondary signal; both shapes honest.
    if code == 0:
        assert stdout.startswith("RECORDED"), stdout + stderr
        assert (journey.subject / evidence).is_file(), (
            "a recorded descendant-probe run must leave its evidence"
        )
    elif code == 2:
        assert "E-C18-LIMIT" in stderr, (
            f"the refused shape must be the limit refusal: {stderr}"
        )
        assert not (journey.subject / evidence).exists(), (
            "a refused (killed) descendant-probe run must leave no evidence"
        )
    else:
        raise AssertionError(
            "the descendant-probe run's outcome is outside its two honest "
            f"shapes (completion or limit refusal): rc={code} "
            f"stdout={stdout!r} stderr={stderr!r}"
        )

    # --- (b) the three layers, pinned to their call sites ------------------
    source = journey.subject / LAUNCHER_SOURCE
    assert source.is_file(), f"the built journey's launcher source is absent: {source}"
    _assert_three_layers_pinned(source)


def test_timeout_refusal_is_distinct_from_the_exit_code(
    journey: ConfinementJourney,
) -> None:
    """Issue #37 sad path 8 — a wall-time hang is refused with its own
    name and writes nothing; an observed exit code propagates exactly.

    The hang arm (``/bin/sleep 30`` against a 5000 ms wall bound) must
    be reported distinctly — the E-C18-LIMIT kill-and-refuse lifecycle,
    exit 2, no evidence — while the exit arm (``exit 3``) must come
    through the run verbatim: RECORDED exit=3, run exits 3. Neither
    code is swallowed into the other's shape.
    """

    hang_evidence = ".local/ranex-e2e/confined-evidence-hang.json"
    hang = _confined_run(journey, hang_evidence, "/bin/sleep", "30")
    assert hang.returncode == 2, (
        "a wall-time-exceeding worker must be refused (exit 2), not "
        f"recorded: {hang.stdout}{hang.stderr}"
    )
    assert "E-C18-LIMIT" in hang.stderr, (
        f"the timeout refusal must be distinctly named: {hang.stderr}"
    )
    assert not (journey.subject / hang_evidence).exists(), (
        "a refused (killed) worker must leave no evidence"
    )

    exit_evidence = ".local/ranex-e2e/confined-evidence-exit3.json"
    exited = _confined_run(journey, exit_evidence, "/bin/sh", "-c", "exit 3")
    assert exited.returncode == 3, (
        f"the observed command's exit code must propagate exactly: {exited.stdout}"
    )
    assert exited.stdout.startswith("RECORDED"), exited.stdout
    assert "exit=3" in exited.stdout, exited.stdout
    assert (journey.subject / exit_evidence).is_file()


def test_goldens_carry_real_volatile_material(journey: ConfinementJourney) -> None:
    """The machine-normalized-capture contract on the confinement golden
    (same three refusals as the run family's file, on this family's own
    volatile material — the confinement digests)."""

    golden = golden_text(_GOLDEN)
    assert "<DIGEST>" in golden
    assert _prereqs.normalize_transcript(golden) == golden
    live = f"sha256:{journey.record['confinement_result_digest']}"
    doctored = golden.replace("<DIGEST>", live, 1)
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _normalized(journey.report_text), doctored, family=_GOLDEN.removesuffix(".out")
        )


def test_sabotage_control_mutated_golden_diffs_dirty(
    journey: ConfinementJourney,
) -> None:
    """ADR-032's red control on the confinement golden: a mutated
    meaningful byte diffs dirty, the family named, the first differing
    hunk carried untruncated."""

    family = _GOLDEN.removesuffix(".out")
    golden = golden_text(_GOLDEN)
    marker = "launcher_builds_reproducible=true"
    assert marker in golden, golden
    mutated = golden.replace(marker, marker.replace("true", "trxe"), 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(
            _normalized(journey.report_text), mutated, family=family
        )
    message = str(raised.value)
    assert family in message, f"the mismatch must name the family {family!r}: {message}"
    assert "@@" in message, message
    assert "trxe" in message, message
