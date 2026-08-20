"""SLICE-058 — real e2e: the provisioning family (deps fetch/approve) on real
data.

Issue #38's exact ownership (file 1 of 2). The provisioning family rides the
ADR-032 frame (docs/adr/ADR-032-real-e2e-suite-framework.md), following the
SLICE-056/057 family patterns: real journeys — this repository cloned at HEAD
with its REAL committed ``governance/deps.yaml``, the real pinned resolver at
``/usr/local/bin/uv`` (digest-pinned), the real ``uv.lock``, and the real
wheel sources the pins declare — whose captured transcripts compare
byte-exactly against golden ``.out`` files through the ONE centralized
normalizer (``_prereqs.normalize_transcript``). No per-family masks exist and
none may be added (ADR-032 sad path 11).

The journeys (every command below was verified against the installed kernel
at 271344443 in a /tmp/opencode prototype before this file was frozen — the
prototype is the freeze-time evidence, not an assumption):

* **The real-index journey** — the clone keeps ``governance/deps.yaml`` (the
  first family that does: the verdict/execution families removed it to stay
  self-contained), so provisioning genuinely activates. A real ``deps
  fetch`` against the pinned inputs re-derives the committed lock from the
  committed manifest over the real index (byte-compare, never ``uv lock
  --check`` — ADR-007's fabricated-hash lesson) and downloads the real
  wheels the lock selects into a fresh content-addressed store; the FETCHED
  transcript freezes against ``expected/deps-fetch-lock.out`` (the depset
  digest is the one volatile class, ``<DIGEST>``-masked). Every store entry
  is then re-hashed by ``sha256sum`` — an external tool — and must hash to
  its own address (issue #38 AC2). A second fetch proves the store is
  reusable (``downloaded=0 reused=N``, same depset); ``deps approve``
  records the human delta; a third fetch after approval drops the
  ``not yet approved`` line.
* **The sabotage arms** — a wheel byte-flip in the store (issue #38
  deterministic gate 2, AC3, the approved-wheel-can-lie gate reused): the
  governed ``run`` refuses admission naming the wheel and quarantining the
  entry, writes no new evidence, and only ``deps fetch`` may repair it (one
  re-download). Lock drift (sad path 3) and the missing epoch block — the
  known ``--frozen`` hazard (sad path 7) — each refuse with the stable
  byte-compare reason. An unapproved depset refuses before spawn with the
  delta (sad path 4). Hostile ``UV_*``/``PIP_*`` env-var injection into
  provisioning is ignored (sad path 8 / AC4: declared-network discipline —
  the pins declare exactly one source and the derivation never leaves it).
* **The local-index sabotage fixture** (ADR-032 sad path 12's deferred
  ownership: the provisioning family owns the in-process stdlib server, the
  ephemeral port, and its transcripts) — a real clone whose pins declare a
  PEP 691 loopback index serving one honest wheel, whose committed lock the
  pinned resolver itself derived against that index. A lying server (wrong
  bytes at the wheel URL, advertised hash unchanged) makes ``deps fetch``
  refuse naming the wheel (sad path 2); a dead server refuses cleanly,
  never partial green (sad path 1). Loopback only — this fixture needs no
  external network.

Probe gating (the frame's two-grammar scheme): the real-index journey and
the drift/epoch arms consume ``prereq_pinned_resolver`` AND
``prereq_network_available`` (issue #38 deterministic gate 5: an offline
host gets the named ``ranex-prereq:network_available:`` skip, never green);
the local-index fixture consumes ``prereq_pinned_resolver`` only (loopback).
The golden-contract test runs ungated so the golden is held to its contract
on every host. git, python, sha256sum, and the pinned interpreter
(/usr/bin/python3.12, root-owned, per the committed pins) are hard tool
requirements — a host missing one fails honestly; it does not skip green.

The golden ``expected/deps-fetch-lock.out`` is the implementation lane's
artifact, captured from a real run of the fetch journey (stdout piped
through the normalizer exactly as the tests do it); its absence is this
file's honest frozen red. The sabotage control and the
normalizer-application contract refuse every hand-sanitized golden shape.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

#: The journey's producer, gate, claim, and bound command — the family
#: spine's pattern: a real command that really runs and attests something
#: true about the subject tree.
FAMILY_PRODUCER = "provisioning-family"
FAMILY_GATE = "provisioning-family"
FAMILY_CLAIM = "tree-clean"
FAMILY_COMMAND = ("git", "status", "--porcelain")

#: Environment keys stripped from every child: the signing variables, the
#: coverage switches (the frame's unwired-children rule), the trace
#: variables, and the resolver/interpreter selectors this family's
#: injection arm sets deliberately on its own children (sad path 8) — the
#: clean arms must start from a genuinely un-injected baseline.
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
    "UV_INDEX_URL",
    "UV_EXTRA_INDEX_URL",
    "UV_INDEX",
    "UV_PYTHON",
    "PIP_INDEX_URL",
    "PIP_CUSTOM_COMPILE_COMMAND",
    "UV_CUSTOM_COMPILE_COMMAND",
)

#: The hostile provisioning environment (sad path 8): a dead loopback index,
#: a decoy extra index, and a wrong pinned interpreter. If any of these
#: reached the derivation, the depset would change or the fetch would fail.
_INJECTED_ENV = {
    "UV_INDEX_URL": "http://127.0.0.1:9/simple/",
    "UV_EXTRA_INDEX_URL": "http://127.0.0.1:9/extra/",
    "UV_PYTHON": "/usr/bin/false",
    "PIP_INDEX_URL": "http://127.0.0.1:9/pip/",
    "UV_CUSTOM_COMPILE_COMMAND": "/bin/false",
}

_FETCHED_RE = re.compile(
    r"^FETCHED  packages=(\d+)  downloaded=(\d+)  reused=(\d+)$", re.MULTILINE
)
_DEPSET_RE = re.compile(r"^[ \t]+depset=(sha256:[0-9a-f]{64})$", re.MULTILINE)


def ranex(
    subject: Path,
    argv: list[str],
    key: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does: a real process, the
    subject's own source on PYTHONPATH (the clone judges the clone — the
    governed root is the CLI's own checkout), the key in the real
    environment variable."""

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
    )


def git(subject: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(subject), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly.

    The two SLICE-058 goldens are the implementation lane's artifacts,
    captured from real runs of these exact journeys (transcripts piped
    through ``_prereqs.normalize_transcript``). A missing golden is this
    file's frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-058 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture above), pipe the CLI stdout through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


def _register_family_gate(subject: Path, producer: str, public: str) -> None:
    """Register the journey's producer and gate in the committed tree."""

    keyring = subject / "governance" / "producers.yaml"
    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == "producers:"), None)
    assert header is not None, "the committed keyring carries no producers: mapping"
    lines.insert(header + 1, f"  {producer}: {public}\n")
    keyring.write_text("".join(lines), encoding="utf-8")

    with (subject / "governance" / "gates.yaml").open("a", encoding="utf-8") as file:
        file.write(
            "  - gate_id: provisioning-family\n"
            "    rule_id: TESTS_EXECUTED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: tree-clean\n"
            '        command: ["git", "status", "--porcelain"]\n'
        )


def _keygen(subject: Path, producer: str, key: Path) -> str:
    """Generate the journey's real keypair through the real keygen CLI."""

    generated = ranex(subject, ["keygen", "--producer", producer], key=key)
    assert generated.returncode == 0, generated.stderr
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    return match.group(1)


def _depset_line(transcript: str) -> str:
    """The bare depset digest (``sha256:…``) of a provisioning transcript."""

    match = _DEPSET_RE.search(transcript)
    assert match, f"the transcript carries no depset line: {transcript!r}"
    return match.group(1)


def _fetch_counts(transcript: str) -> tuple[int, int, int]:
    match = _FETCHED_RE.search(transcript)
    assert match, f"the transcript carries no FETCHED line: {transcript!r}"
    return tuple(int(group) for group in match.groups())


@dataclass
class DepsJourney:
    """Everything the frozen tests consume from the real-index journey."""

    subject: Path
    key: Path
    store: Path
    first_fetch: subprocess.CompletedProcess[str]
    second_fetch: subprocess.CompletedProcess[str]
    unapproved_run: subprocess.CompletedProcess[str]
    approve_run: subprocess.CompletedProcess[str]
    third_fetch: subprocess.CompletedProcess[str]
    injection_fetch: subprocess.CompletedProcess[str]
    provisioned_run: subprocess.CompletedProcess[str]
    evidence_at_run: int
    flip_refusal: subprocess.CompletedProcess[str]
    flip_wheel: tuple[str, str]
    flip_digest: str
    repair_fetch: subprocess.CompletedProcess[str]


@pytest.fixture(scope="module")
def journey(
    tmp_path_factory: pytest.TempPathFactory,
    prereq_pinned_resolver: None,
    prereq_network_available: None,
) -> DepsJourney:
    """The one real-index journey: real pins, real wheels, real sabotage.

    Ordered, spine-style: every stage's refusal is loud and names the stage,
    so a journey that cannot complete fails here with the CLI's own words
    instead of a dereference error in a test below.
    """

    sha256sum = shutil.which("sha256sum")
    assert sha256sum is not None, (
        "the sha256sum binary is a hard requirement of this family's "
        "external re-check (issue #38 names it): a host without it fails "
        "honestly rather than skipping green"
    )

    base = tmp_path_factory.mktemp("provisioning-family-deps")
    subject = base / "subject"
    key = base / f"{FAMILY_PRODUCER}.key"
    store = base / "store"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, f"cannot clone the real subject: {cloned.stderr}"
    for name, value in (
        ("user.email", "provisioning-family@example.com"),
        ("user.name", "provisioning-family journey"),
    ):
        assert git(subject, "config", name, value).returncode == 0

    # The subject KEEPS governance/deps.yaml — provisioning activates. The
    # journey's producer is registered so the governed run arms below have
    # their fully-valid setup (the flip arm's refusal must be the store's,
    # not a registration failure).
    public = _keygen(subject, FAMILY_PRODUCER, key)
    _register_family_gate(subject, FAMILY_PRODUCER, public)
    committed = git(
        subject, "commit", "-q", "-am", "register the provisioning-family producer and gate"
    )
    assert committed.returncode == 0, committed.stderr

    # --- fetch 1: fresh store, the golden journey -------------------------
    first = ranex(subject, ["deps", "fetch", "--repository", ".", "--store", str(store)])
    assert first.returncode == 0, (
        f"the pinned-inputs fetch must exit 0: {first.stdout}{first.stderr}"
    )
    packages, downloaded, _ = _fetch_counts(first.stdout)
    assert downloaded == packages, first.stdout

    # --- fetch 2: the store is reusable, the derivation identical ---------
    second = ranex(subject, ["deps", "fetch", "--repository", ".", "--store", str(store)])
    assert second.returncode == 0, second.stderr
    packages2, downloaded2, reused2 = _fetch_counts(second.stdout)
    assert (packages2, downloaded2, reused2) == (packages, 0, packages), second.stdout
    assert _depset_line(second.stdout) == _depset_line(first.stdout), (
        "two fetches of the same committed lock must record one depset"
    )

    # --- sad path 4: derivation recorded, approval missing -> refuse ------
    run_argv = [
        "run",
        "--claim",
        FAMILY_CLAIM,
        "--producer",
        FAMILY_PRODUCER,
        "--gate",
        FAMILY_GATE,
        "--repository",
        ".",
        "--store",
        str(store),
        "--",
        *FAMILY_COMMAND,
    ]
    unapproved = ranex(subject, run_argv, key=key)
    assert unapproved.returncode == 2, (
        f"the unapproved depset must refuse (exit 2): {unapproved.stdout}"
    )
    assert "this dependency set is not approved" in unapproved.stderr
    assert "The delta awaiting approval:" in unapproved.stderr

    # --- approve: the human delta over the derived set ---------------------
    approve = ranex(
        subject, ["deps", "approve", "--repository", ".", "--approver", "reviewer"]
    )
    assert approve.returncode == 0, approve.stderr
    assert "no prior approval; the full set is the delta:" in approve.stdout
    assert f"APPROVED  packages={packages}  approver=reviewer" in approve.stdout
    assert _depset_line(approve.stdout) == _depset_line(first.stdout)

    # --- fetch 3: approved — the not-yet-approved line is gone -------------
    third = ranex(subject, ["deps", "fetch", "--repository", ".", "--store", str(store)])
    assert third.returncode == 0, third.stderr
    assert _fetch_counts(third.stdout) == (packages, 0, packages), third.stdout
    assert "not yet approved" not in third.stdout

    # --- sad path 8 / AC4: hostile env injection is ignored ----------------
    injected = ranex(
        subject,
        ["deps", "fetch", "--repository", ".", "--store", str(store)],
        extra_env=_INJECTED_ENV,
    )
    assert injected.returncode == 0, (
        f"the derivation must ignore ambient resolver injection: {injected.stderr}"
    )
    assert _fetch_counts(injected.stdout) == (packages, 0, packages), injected.stdout
    assert _depset_line(injected.stdout) == _depset_line(first.stdout), (
        "an injected UV_INDEX_URL/UV_PYTHON that changed the derivation "
        "would change the depset — the pins' declared inputs are the only "
        "inputs (issue #38 AC4)"
    )

    # --- the approved set admits a real provisioned run --------------------
    provisioned = ranex(subject, run_argv, key=key)
    assert provisioned.returncode == 0, (
        f"the approved governed run must exit 0: {provisioned.stdout}"
        f"{provisioned.stderr}"
    )
    assert provisioned.stdout.startswith("RECORDED"), provisioned.stdout
    evidence = subject / "governance" / "evidence.json"
    evidence_at_run = len(json.loads(evidence.read_text(encoding="utf-8")))

    # --- deterministic gate 2: a wheel byte-flip refuses admission ---------
    entries = sorted((store / "sha256").iterdir())
    assert len(entries) == packages, (
        f"the store holds {len(entries)} entries, the transcript said {packages}"
    )
    lock = tomllib.loads((subject / "uv.lock").read_text(encoding="utf-8"))
    flip_digest = entries[0].name
    flip_wheel = ("", "")
    for record in lock["package"]:
        for wheel in record.get("wheels", ()):
            if wheel.get("hash", "").endswith(flip_digest):
                flip_wheel = (record["name"], record["version"])
        if flip_wheel != ("", ""):
            break
    assert flip_wheel != ("", ""), f"the flipped digest {flip_digest} is not in the lock"
    entry = store / "sha256" / flip_digest
    entry.chmod(stat.S_IMODE(entry.stat().st_mode) | 0o200)
    data = bytearray(entry.read_bytes())
    data[len(data) // 2] ^= 0x01
    entry.write_bytes(bytes(data))

    flip_refusal = ranex(subject, run_argv, key=key)
    assert flip_refusal.returncode == 2, (
        f"admission over a flipped wheel must refuse (exit 2): "
        f"{flip_refusal.stdout}{flip_refusal.stderr}"
    )
    wheel_name, wheel_version = flip_wheel
    assert f"wheel for {wheel_name} {wheel_version} is not available" in flip_refusal.stderr
    assert "failed verification and was quarantined" in flip_refusal.stderr
    assert not entry.exists(), "the corrupted entry must be quarantined away"
    assert any(
        path.name.startswith(flip_digest)
        for path in (store / "quarantine").iterdir()
    ), "the quarantined bytes must exist under quarantine/"
    assert (
        len(json.loads(evidence.read_text(encoding="utf-8"))) == evidence_at_run
    ), "the refused admission must write no new evidence record"

    # --- only deps fetch may repair: one re-download ------------------------
    repair = ranex(subject, ["deps", "fetch", "--repository", ".", "--store", str(store)])
    assert repair.returncode == 0, repair.stderr
    assert _fetch_counts(repair.stdout) == (packages, 1, packages - 1), repair.stdout

    return DepsJourney(
        subject=subject,
        key=key,
        store=store,
        first_fetch=first,
        second_fetch=second,
        unapproved_run=unapproved,
        approve_run=approve,
        third_fetch=third,
        injection_fetch=injected,
        provisioned_run=provisioned,
        evidence_at_run=evidence_at_run,
        flip_refusal=flip_refusal,
        flip_wheel=flip_wheel,
        flip_digest=flip_digest,
        repair_fetch=repair,
    )


@dataclass
class LocalIndexJourney:
    """The loopback-index sabotage fixture and its three fetch outcomes."""

    subject: Path
    port: int
    good_fetch: subprocess.CompletedProcess[str]
    liar_refusal: subprocess.CompletedProcess[str]
    dead_refusal: subprocess.CompletedProcess[str]


@pytest.fixture(scope="module")
def local_index_journey(
    tmp_path_factory: pytest.TempPathFactory, prereq_pinned_resolver: None
) -> LocalIndexJourney:
    """ADR-032 sad path 12's deferred fixture, owned by this family: an
    in-process stdlib PEP 691 index on an ephemeral loopback port, one
    honest wheel, and a real clone whose pins and committed lock both cite
    THAT server — the lock derived by the pinned resolver itself against
    it, so fetch's byte-compare is a genuine reproducibility question."""

    import fcntl
    import hashlib
    import io
    import json as jsonlib
    import socket
    import struct
    import threading
    import zipfile
    from http.server import BaseHTTPRequestHandler, HTTPServer

    def build_wheel(name: str, version: str, body: str) -> bytes:
        buffer = io.BytesIO()
        prefix = f"{name}-{version}"
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(f"{name}/__init__.py", body)
            archive.writestr(
                f"{prefix}.dist-info/METADATA",
                f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
            )
            archive.writestr(
                f"{prefix}.dist-info/WHEEL",
                "Wheel-Version: 1.0\nGenerator: ranex-tests\n"
                "Root-Is-Purelib: true\nTag: py3-none-any\n",
            )
            archive.writestr(f"{prefix}.dist-info/RECORD", "")
        return buffer.getvalue()

    good_wheel = build_wheel("provpkg", "1.0.0", "VALUE = 42\n")
    lying_wheel = good_wheel[:-1] + bytes([good_wheel[-1] ^ 0x01])
    served = {"bytes": good_wheel}

    class IndexHandler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *args: object) -> None:
            pass

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command == "GET":
                self.wfile.write(body)

        def _respond(self) -> None:
            if self.path == "/simple/provpkg/":
                port = self.server.server_port  # type: ignore[attr-defined]
                body = jsonlib.dumps(
                    {
                        "meta": {"api-version": "1.0"},
                        "name": "provpkg",
                        "files": [
                            {
                                "filename": "provpkg-1.0.0-py3-none-any.whl",
                                "url": f"http://127.0.0.1:{port}/wheels/provpkg-1.0.0-py3-none-any.whl",
                                "hashes": {"sha256": hashlib.sha256(good_wheel).hexdigest()},
                                "upload-time": "2026-08-01T00:00:00Z",
                            }
                        ],
                    }
                ).encode()
                self._send(200, "application/vnd.pypi.simple.v1+json", body)
                return
            if self.path == "/wheels/provpkg-1.0.0-py3-none-any.whl":
                self._send(200, "application/octet-stream", served["bytes"])
                return
            self._send(404, "text/plain", b"not found")

        def do_GET(self) -> None:
            self._respond()

        def do_HEAD(self) -> None:
            self._respond()

    # The hermetic-freeze seal runs this very suite inside the network
    # namespace _deny_network creates (src/ranex/cli/main.py: unshare
    # CLONE_NEWUSER|CLONE_NEWNET between fork and exec), and a fresh netns
    # starts with loopback DOWN: the server below binds, but nothing — the
    # resolver's lock derivation, a fetch — can connect to it (ENETUNREACH),
    # so the frozen construction errors inside every sealed ceremony run
    # (issue #38 blocker comment 5350181287). Owner ruling 2026-08-20,
    # option B: the fixture itself raises ``lo`` in the current netns
    # before binding — the pure-stdlib ``ip link set lo up`` (SIOCSIFFLAGS
    # over flags read by SIOCGIFFLAGS); loopback only, so the seal's
    # no-external-network intent is untouched. Best-effort and guarded:
    # outside the seal lo is already up (idempotent no-op), and where a
    # host refuses the ioctl the loopback probe below is the same ruling's
    # sanctioned fallback (option A): the two arms skip with a named
    # reason instead of erroring. On this host the sealed shape does
    # refuse it — the seal's exec after the unshare drops CAP_NET_ADMIN
    # (uid unmapped in the fresh userns, CapEff=0; EPERM observed) — so
    # the fallback is the path that holds here; a sealed netns whose
    # loopback can be raised runs the arms genuinely.
    SIOCGIFFLAGS = 0x8913  # <linux/sockios.h>: read a netdev's flags
    SIOCSIFFLAGS = 0x8914  # ...and write them back — `ip link set lo up`
    IFF_UP = 0x1  # <linux/if.h>: the UP bit SIOCSIFFLAGS sets

    def _raise_loopback() -> None:
        ifreq = struct.Struct("16sH22x")  # struct ifreq: ifr_name[16] + union
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as control:
                packed = fcntl.ioctl(control.fileno(), SIOCGIFFLAGS, ifreq.pack(b"lo", 0))
                flags = ifreq.unpack(packed)[1]
                if not flags & IFF_UP:
                    fcntl.ioctl(
                        control.fileno(), SIOCSIFFLAGS, ifreq.pack(b"lo", flags | IFF_UP)
                    )
        except OSError:
            pass  # the loopback probe below reports the outcome honestly

    def _loopback_available() -> bool:
        """The fixture's real dependency, probed exactly as consumed: a
        loopback TCP connect — the resolver and the fetches are child
        processes connecting to 127.0.0.1, this probe's client shape."""

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.bind(("127.0.0.1", 0))
                listener.listen(1)
                port = listener.getsockname()[1]
                listener.settimeout(5)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
                    client.settimeout(5)
                    client.connect(("127.0.0.1", port))
                    accepted, _peer = listener.accept()
                    accepted.close()
        except OSError:
            return False
        return True

    _raise_loopback()
    if not _loopback_available():
        pytest.skip(
            "loopback TCP is unavailable in this network namespace: the "
            "hermetic-freeze seal starts lo DOWN and this host refuses the "
            "ruled option-B lo-raise (EPERM: no CAP_NET_ADMIN after the "
            "seal's fork-unshare-exec), so the local-index journey cannot "
            "construct its loopback index here (issue #38 ruling 2026-08-20 "
            "on blocker comment 5350181287, option-A fallback)"
        )

    server = HTTPServer(("127.0.0.1", 0), IndexHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base = tmp_path_factory.mktemp("provisioning-family-localidx")
    subject = base / "subject"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, f"cannot clone the fixture subject: {cloned.stderr}"
    for name, value in (
        ("user.email", "provisioning-family@example.com"),
        ("user.name", "provisioning-family local index"),
    ):
        assert git(subject, "config", name, value).returncode == 0

    pins = REAL_REPO / "governance" / "deps.yaml"
    pinned = yaml.safe_load(pins.read_text(encoding="utf-8"))
    (subject / "pyproject.toml").write_text(
        "[project]\n"
        'name = "ranex"\n'
        'version = "0.0.0"\n'
        'requires-python = ">=3.11"\n'
        'dependencies = ["provpkg==1.0.0"]\n'
        "\n[tool.uv]\npackage = false\n",
        encoding="utf-8",
    )
    (subject / "governance" / "deps.yaml").write_text(
        f"resolver:\n"
        f"  path: {pinned['resolver']['path']}\n"
        f"  sha256: {pinned['resolver']['sha256']}\n"
        f"python:\n"
        f"  path: {pinned['python']['path']}\n"
        f"indexes:\n"
        f"  - http://127.0.0.1:{port}/simple/\n"
        f'exclude_newer: "{pinned["exclude_newer"]}"\n',
        encoding="utf-8",
    )
    # The committed lock is derived by the pinned resolver itself against
    # this exact server, exactly as the kernel's derive_lock invokes it:
    # empty scratch HOME and cache, no ambient uv configuration.
    scratch = base / "derive"
    for directory in ("ws", "home", "cache"):
        (scratch / directory).mkdir(parents=True, exist_ok=True)
    shutil.copy(subject / "pyproject.toml", scratch / "ws" / "pyproject.toml")
    derived = subprocess.run(
        [
            str(pinned["resolver"]["path"]),
            "lock",
            "--exclude-newer",
            str(pinned["exclude_newer"]),
            "--python",
            str(pinned["python"]["path"]),
            "--index-url",
            f"http://127.0.0.1:{port}/simple/",
        ],
        cwd=scratch / "ws",
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(scratch / "home"),
            "UV_NO_CONFIG": "1",
            "UV_CACHE_DIR": str(scratch / "cache"),
            "UV_PYTHON_DOWNLOADS": "never",
        },
    )
    assert derived.returncode == 0, f"fixture lock derivation failed: {derived.stderr}"
    shutil.copy(scratch / "ws" / "uv.lock", subject / "uv.lock")
    added = git(subject, "add", "pyproject.toml", "uv.lock", "governance/deps.yaml")
    assert added.returncode == 0, added.stderr
    committed = git(subject, "commit", "-q", "-m", "fixture subject on the local index")
    assert committed.returncode == 0, committed.stderr

    def fetch(store_name: str) -> subprocess.CompletedProcess[str]:
        return ranex(
            subject, ["deps", "fetch", "--repository", ".", "--store", str(base / store_name)]
        )

    good = fetch("good-store")
    assert good.returncode == 0, (
        f"the honest local-index fetch must exit 0: {good.stdout}{good.stderr}"
    )
    assert _fetch_counts(good.stdout) == (1, 1, 0), good.stdout

    served["bytes"] = lying_wheel
    liar = fetch("liar-store")
    assert liar.returncode == 2, (
        f"a lying wheel source must refuse (exit 2): {liar.stdout}{liar.stderr}"
    )
    assert "downloaded wheel for provpkg 1.0.0 does not match the lock's sha256" in (
        liar.stderr
    ), liar.stderr

    server.shutdown()
    thread.join()
    server.server_close()

    dead_store = base / "dead-store"
    dead = fetch("dead-store")
    assert dead.returncode == 2, (
        f"an unreachable wheel source must refuse (exit 2): {dead.stdout}{dead.stderr}"
    )
    assert "clean resolution failed" in dead.stderr, dead.stderr
    assert not dead_store.exists(), "a refused fetch must leave no store behind"

    return LocalIndexJourney(
        subject=subject,
        port=port,
        good_fetch=good,
        liar_refusal=liar,
        dead_refusal=dead,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def test_golden_contract_deps_fetch_lock() -> None:
    """The fetch golden's own contract, held on EVERY host (the confinement
    family's ungated precedent): it exists, it is a fixpoint of the one
    normalizer, and it carries ``<DIGEST>`` exactly where the journey emits
    live volatile material — the depset digest of the real committed lock.
    This is the file's ungated red at the freeze commit: the golden does not
    exist yet, and a host without the pinned resolver or the index still
    holds the golden to its contract once the implementation lane captures
    it."""

    golden = golden_text("deps-fetch-lock.out")
    assert "<DIGEST>" in golden, (
        "deps-fetch-lock.out carries no <DIGEST> token: the journey's "
        "depset digest is real volatile material the normalizer must have "
        "tamed — a golden without the token is hand-sanitized text, not a "
        "captured transcript"
    )
    assert "FETCHED" in golden, golden
    assert _prereqs.normalize_transcript(golden) == golden, (
        "deps-fetch-lock.out is not a normalizer fixpoint: it still "
        "contains bytes the frozen grammar would mask, which no capture "
        "piped through normalize_transcript can"
    )


def test_fetch_transcript_matches_the_golden(journey: DepsJourney) -> None:
    """The pinned-inputs FETCHED transcript, byte-frozen against its golden
    (issue #38 deterministic gate 1: the committed lock's derivation is
    reproduced byte-exactly, or this fetch would have refused).

    Independent re-check first (issue #38 AC2: an external tool re-hashes
    what the kernel admitted): every wheel-store entry is re-hashed by
    ``sha256sum`` — never the kernel's own WheelStore — and must hash to
    exactly its own content address, and the store's entry count must equal
    the packages count the transcript printed.
    """

    sha256sum = shutil.which("sha256sum")
    assert sha256sum is not None, (
        "the sha256sum binary is a hard requirement of this family's "
        "external re-check: a host without it fails honestly rather than "
        "skipping green"
    )
    entries = sorted((journey.store / "sha256").iterdir())
    assert len(entries) == _fetch_counts(journey.first_fetch.stdout)[0], (
        f"the store holds {len(entries)} entries; the first transcript "
        "named a different package count"
    )
    for entry in entries:
        rehashed = subprocess.run(
            [sha256sum, str(entry)], capture_output=True, text=True, check=False
        )
        assert rehashed.returncode == 0, rehashed.stderr
        digest = rehashed.stdout.split("  ", 1)[0]
        assert digest == entry.name, (
            f"sha256sum disagrees with the store address {entry.name}: "
            f"{digest} — the store's entries must be their own addresses"
        )

    compare_golden(journey.first_fetch.stdout, "deps-fetch-lock.out")


def test_second_fetch_approve_and_third_fetch_are_consistent(
    journey: DepsJourney,
) -> None:
    """The provisioning loop's honest bookkeeping, all asserted against the
    real transcripts the journey produced: the second fetch reuses every
    wheel (``downloaded=0``) at an identical depset; approval records the
    human delta over exactly the derived set; the third fetch drops the
    ``not yet approved`` line; and the hostile-injection fetch (sad path 8 /
    AC4) derives identically — the pins' declared sources are the only
    inputs provisioning can see.
    """

    packages = _fetch_counts(journey.first_fetch.stdout)[0]
    assert _fetch_counts(journey.second_fetch.stdout) == (packages, 0, packages)
    assert _fetch_counts(journey.third_fetch.stdout) == (packages, 0, packages)
    assert "not yet approved" not in journey.third_fetch.stdout
    assert _fetch_counts(journey.injection_fetch.stdout) == (packages, 0, packages)
    assert _depset_line(journey.injection_fetch.stdout) == _depset_line(
        journey.first_fetch.stdout
    ), (
        "the injected fetch's depset must be byte-identical to the clean "
        "one — declared-network discipline (issue #38 AC4, sad path 8)"
    )
    assert f"APPROVED  packages={packages}  approver=reviewer" in journey.approve_run.stdout
    assert "approval reduces hidden change" in journey.approve_run.stdout


def test_declared_network_is_exactly_the_pinned_sources(journey: DepsJourney) -> None:
    """Issue #38 AC4's configuration half: the committed provisioning pins
    declare exactly one index — the pinned wheel source — and the pinned,
    digest-verified resolver; nothing else is declared for provisioning to
    reach. Together with the injection arm (the behavioural half, above)
    this is the declared-network discipline.
    """

    pins = yaml.safe_load(
        (journey.subject / "governance" / "deps.yaml").read_text(encoding="utf-8")
    )
    indexes = pins["indexes"]
    assert indexes == ["https://pypi.org/simple"], (
        f"the committed pins must declare exactly the pinned index: {indexes}"
    )
    assert pins["resolver"]["path"] == "/usr/local/bin/uv", pins["resolver"]
    pinned_digest = pins["resolver"]["sha256"]
    assert (
        hashlib.sha256(Path("/usr/local/bin/uv").read_bytes()).hexdigest() == pinned_digest
    ), "the pinned resolver digest must match the binary the pins name"


def test_unapproved_depset_refuses_before_spawn(journey: DepsJourney) -> None:
    """Issue #38 sad path 4: with a derivation recorded but no approval,
    the governed run refuses — no silent admission — naming the delta that
    awaits a human. The refusal was produced against the real subject after
    a real fetch; it is part of the red output the implementation lane
    posts on issue #38 for AC3."""

    assert journey.unapproved_run.returncode == 2
    assert "refusing to run: this dependency set is not approved" in (
        journey.unapproved_run.stderr
    )
    assert "The delta awaiting approval:" in journey.unapproved_run.stderr


def test_wheel_byte_flip_refuses_admission_and_only_fetch_repairs(
    journey: DepsJourney,
) -> None:
    """Issue #38 deterministic gate 2 / AC3 / the approved-wheel-can-lie
    gate reused: one flipped byte in a stored wheel and the governed run's
    admission refuses, naming the wheel and quarantining the corrupted
    entry — an approved set is re-verified on the way out, never trusted.
    Only ``deps fetch`` may repair the address, and the repair fetch
    re-downloads exactly the one wheel."""

    wheel_name, wheel_version = journey.flip_wheel
    assert journey.flip_refusal.returncode == 2
    assert f"wheel for {wheel_name} {wheel_version} is not available" in (
        journey.flip_refusal.stderr
    ), journey.flip_refusal.stderr
    assert "quarantined" in journey.flip_refusal.stderr
    packages = _fetch_counts(journey.first_fetch.stdout)[0]
    assert _fetch_counts(journey.repair_fetch.stdout) == (packages, 1, packages - 1), (
        journey.repair_fetch.stdout
    )


def test_lock_drift_and_missing_epoch_block_refuse(
    journey: DepsJourney,
) -> None:
    """Issue #38 sad paths 3 and 7: a hand-edited lock and a lock whose
    epoch block was removed — the known ``--frozen`` hazard, which
    ``uv lock --check`` accepted (ADR-007) — each refuse under the
    byte-compare rule with the stable reason, leaving no store behind."""

    base = journey.subject.parent / "sad"
    base.mkdir(exist_ok=True)
    stable_reason = "the committed uv.lock differs from a clean derivation"

    drift = base / "drift"
    subprocess.run(
        ["git", "clone", "-q", str(journey.subject), str(drift)], check=True
    )
    with (drift / "uv.lock").open("a", encoding="utf-8") as file:
        file.write("\n# hand edit\n")
    added = git(drift, "add", "uv.lock")
    assert added.returncode == 0, added.stderr
    committed = git(drift, "commit", "-q", "-m", "hand edit the lock")
    assert committed.returncode == 0, committed.stderr
    drift_fetch = ranex(
        drift, ["deps", "fetch", "--repository", ".", "--store", str(base / "drift-store")]
    )
    assert drift_fetch.returncode == 2, (
        f"a drifted lock must refuse: {drift_fetch.stdout}{drift_fetch.stderr}"
    )
    assert stable_reason in drift_fetch.stderr
    assert not (base / "drift-store").exists(), "a refused fetch must leave no store"

    epoch = base / "epoch"
    subprocess.run(
        ["git", "clone", "-q", str(journey.subject), str(epoch)], check=True
    )
    pins = yaml.safe_load((epoch / "governance" / "deps.yaml").read_text(encoding="utf-8"))
    block = f'\n[options]\nexclude-newer = "{pins["exclude_newer"]}"\n'
    lock_text = (epoch / "uv.lock").read_text(encoding="utf-8")
    assert block in lock_text, "the committed lock carries no epoch block to remove"
    (epoch / "uv.lock").write_text(lock_text.replace(block, "", 1), encoding="utf-8")
    added = git(epoch, "add", "uv.lock")
    assert added.returncode == 0, added.stderr
    committed = git(epoch, "commit", "-q", "-m", "drop the epoch block")
    assert committed.returncode == 0, committed.stderr
    epoch_fetch = ranex(
        epoch, ["deps", "fetch", "--repository", ".", "--store", str(base / "epoch-store")]
    )
    assert epoch_fetch.returncode == 2, (
        f"a lock missing its epoch block must refuse: "
        f"{epoch_fetch.stdout}{epoch_fetch.stderr}"
    )
    assert stable_reason in epoch_fetch.stderr
    assert "'[options]'" in epoch_fetch.stderr or "first divergence" in epoch_fetch.stderr, (
        "the refusal must name the divergence the byte-compare found: "
        f"{epoch_fetch.stderr}"
    )
    assert not (base / "epoch-store").exists()


def test_lying_wheel_source_refuses_naming_the_wheel(
    local_index_journey: LocalIndexJourney,
) -> None:
    """Issue #38 sad path 2 (deterministic, loopback): a wheel source that
    serves bytes which do not hash to the lock's declared sha256 is refused
    naming the wheel and version, and nothing enters the store — the
    admission the byte-flip arm proves on the way out is the same refusal
    on the way in."""

    refusal = local_index_journey.liar_refusal
    assert refusal.returncode == 2
    assert "downloaded wheel for provpkg 1.0.0 does not match the lock's sha256" in (
        refusal.stderr
    ), refusal.stderr
    assert not (local_index_journey.subject.parent / "liar-store").exists()


def test_unreachable_wheel_source_refuses_never_partial_green(
    local_index_journey: LocalIndexJourney,
) -> None:
    """Issue #38 sad path 1 (deterministic, loopback): with the pinned
    wheel source down, ``deps fetch`` refuses with the stable
    clean-resolution failure and leaves no store — never a partial green.
    (On a host where the real index is unreachable entirely, the
    real-index arms carry the named ``ranex-prereq:network_available:``
    skip instead — deterministic gate 5 — which is the other honest half
    of this same sad path.)"""

    refusal = local_index_journey.dead_refusal
    assert refusal.returncode == 2
    assert "clean resolution failed" in refusal.stderr, refusal.stderr


def test_goldens_carry_real_volatile_material(journey: DepsJourney) -> None:
    """The golden is a machine-normalized capture, not hand-sanitized text:
    it carries the normalizer's own token where the journey emits live
    volatile material (the depset digest is real, derived from the real
    committed lock), it is a fixpoint of the normalizer, and a golden
    holding the LIVE volatile bytes provably cannot match — demonstrated by
    re-substituting one live depset digest into the real golden and proving
    the comparison fails."""

    name = "deps-fetch-lock.out"
    transcript = journey.first_fetch.stdout
    golden = golden_text(name)
    assert "<DIGEST>" in golden
    assert _prereqs.normalize_transcript(golden) == golden
    live = _depset_line(transcript)
    doctored = golden.replace("<DIGEST>", live, 1)
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _normalized(transcript), doctored, family=name.removesuffix(".out")
        )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: DepsJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte of
    the expected file and the comparator must diff dirty, naming the family
    and carrying exactly the first differing hunk — never a bare
    ``assert False``."""

    name = "deps-fetch-lock.out"
    transcript = journey.first_fetch.stdout
    verdict_word = "FETCHED"
    family = name.removesuffix(".out")
    golden = golden_text(name)
    assert verdict_word in golden, golden
    mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(_normalized(transcript), mutated, family=family)
    message = str(raised.value)
    assert family in message, f"the mismatch must name the golden family {family!r}: {message}"
    assert "@@" in message, (
        "the mismatch must carry the first differing hunk header: " + message
    )
    assert "Q" + verdict_word[1:] in message, (
        "the first hunk must show the mutated bytes untruncated: " + message
    )
