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

The kill/drain and timeout contracts (issue #37 sad paths 3 and 8):

* a backgrounded worker that outlives its parent cannot escape the
  session cgroup — the kernel validates the confinement result only
  over a DRAINED teardown (``populated=0``, cgroup killed and removed),
  so a surviving worker refuses the result and this file goes red on
  the survivor (the test asserts the run completed and recorded);
* a worker that exceeds its wall-time bound is killed and refused
  (``E-C18-LIMIT``, exit 2, no evidence) — distinct reporting — while a
  worker that exits 3 propagates exactly (``RECORDED exit=3``, run
  exits 3): no swallowed exit code, no hang dressed as a verdict.

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


def test_worker_kill_drain_leaves_no_survivor(journey: ConfinementJourney) -> None:
    """Issue #37 sad path 3 — a worker that outlives its parent cannot
    escape the session: the kernel validates the result only over a
    drained teardown, so a survivor refuses the result and this test is
    RED on the survivor (the run could not have completed and recorded).
    """

    evidence = ".local/ranex-e2e/confined-evidence-survivor.json"
    escaped = _confined_run(
        journey, evidence, "/bin/sh", "-c", "( /bin/sleep 30 & ) ; exit 0"
    )
    assert escaped.returncode == 0, (
        "the backgrounded worker escaped the session cgroup or survived "
        "the teardown kill — the kernel should have refused the "
        f"undrained result: {escaped.stdout}{escaped.stderr}"
    )
    assert escaped.stdout.startswith("RECORDED"), escaped.stdout
    assert (journey.subject / evidence).is_file(), (
        "a drained teardown must have admitted the confinement result "
        "and recorded it — no record means a survivor was detected"
    )


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
