"""Pre-flight instrument self-test — no gauge is trusted until it has caught a
known-bad (issue #113).

Every dogfood instrument ships a **committed good reference** it must pass and
a **committed bad reference** it must catch. The self-test runs *before any
measurement and before any spend*, and the run refuses to proceed if either
expectation fails: a bad gauge does not produce visible errors, it produces
confident approvals, so the only time its betrayal is cheap to observe is
before it is trusted with a subject.

Exit contract, shared with the drivers that embed this pre-flight:

  0  every instrument proved (good passed, bad caught, deterministic)
  1  an instrument failed its own reference — NO measurement is attempted
  2  incomplete execution (a reference, interpreter or service was missing)

Statuses reuse the #95 vocabulary; `PASS` stays absent for the same reason it
is absent from `calibration.py`. The receipt written to `<out>/selftest.json`
is deliberately **timing-free** so that the anti-flake rule is checkable by
byte-comparing receipts across identical repeats; wall-clock and captured
output live beside it in `selftest-commands.json`, where variation is
permitted and never changes a status.

Run standalone:

    .venv/bin/python tools/dogfood/selftest.py --out /tmp/ranex-selftest

`--blunt NAME` is the negative control for the harness itself: it replaces one
instrument's gauge with a deliberately broken one (the marker scanner becomes
a script that writes an empty SARIF and exits 0; the audit and receiver
judgments approve whatever they observe). The blunted run must come back
FALSE-PASS — a self-test that cannot fail is the thing being hunted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import calibration

TOOL_DIR = Path(__file__).resolve().parent
KERNEL = TOOL_DIR.parents[1]
#: The installed console script (uv sync --frozen): a governed run resolves
#: argv[0] through its symlinks, and the script carries its own kernel.
RANEX = KERNEL / ".venv" / "bin" / "ranex"
REFERENCES = TOOL_DIR / "selftest" / "references"

SCHEMA = "ranex-selftest-v1"
DEFAULT_REPEATS = 3

#: Every instrument, with the driver whose gauge it proves. The #95 driver
#: (`calibration.py`) gates its measurement on ALL of these passing in the same
#: run; each driver also pre-flights its own instrument before measuring.
INSTRUMENTS: dict[str, str] = {
    "marker-scanner": "tools/dogfood/markers_probe.py",
    "release-audit": "tools/dogfood/release_audit.py",
    "receiver-audit": "tools/dogfood/receiver_audit.py",
}

#: The blunt marker scanner (issue arm 2): a real process that really exits 0
#: and really writes a clean SARIF — modelled on the neuter script of
#: markers_probe arm 8, because that shape already escaped one gate.
_NEUTER = (
    "import json, sys\n"
    "out = [a for a in sys.argv if a.startswith('--output-file=')][0].split('=', 1)[1]\n"
    "open(out, 'w').write(json.dumps({'version': '2.1.0', 'runs': [{'tool': "
    "{'driver': {'name': 'neuter'}}, 'invocations': [{'executionSuccessful': True}], "
    "'artifacts': [{'location': {'uri': 'reference.py'}}], 'results': []}]}))\n"
)

COMMANDS: list[dict[str, Any]] = []


def _run(argv: list[str], cwd: Path, *, env: dict[str, str] | None = None,
         timeout: int = 120) -> subprocess.CompletedProcess[str]:
    started = time.monotonic()
    completed = subprocess.run(
        [str(part) for part in argv], cwd=str(cwd), env=env,
        capture_output=True, text=True, check=False, timeout=timeout,
    )
    COMMANDS.append({
        "argv": [str(part) for part in argv],
        "cwd": str(cwd),
        "exit": completed.returncode,
        "wall_ms": round((time.monotonic() - started) * 1000.0, 1),
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    })
    return completed


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _reference(instrument: str, side: str) -> Path:
    """The committed reference for one side of one instrument.

    Marker references are `.txt` data on purpose: the bytes are copied into a
    scratch `.py` at run time, so committing the bad (trigger-less) reference
    never plants a live violating marker — or a well-formed one — in this tree.
    """

    group = {
        "marker-scanner": "markers",
        "release-audit": "release",
        "receiver-audit": "receiver",
    }[instrument]
    suffix = ".txt" if instrument == "marker-scanner" else ".json"
    return REFERENCES / group / f"{side}{suffix}"


# --- the instruments ---------------------------------------------------------


def _observe_markers(side: str, scratch: Path, *, blunt: bool) -> calibration.Observation:
    """Scan one committed marker reference with the installed scanner.

    Acceptance (the gauge's green) is a scan with no error-level finding: a
    well-formed marker may carry a note-level `marker-shortcut` result — that
    is the declaration working, not a defect — but `marker-no-trigger` and
    `marker-malformed` are errors the scanner exists to refuse.
    """

    reference = _reference("marker-scanner", side)
    tree = scratch / f"markers-{side}"
    tree.mkdir(exist_ok=True)
    (tree / "shortcut_probe.py").write_bytes(reference.read_bytes())
    artifact = scratch / f"markers-{side}.sarif"
    artifact.unlink(missing_ok=True)
    argv = (
        ["/usr/bin/python3", "-c", _NEUTER, f"--output-file={artifact}"]
        if blunt
        else [str(RANEX), "markers", "--output-format=sarif",
              f"--output-file={artifact}", f"--root={tree}"]
    )
    completed = _run(argv, tree)
    findings: list[dict[str, str]] = []
    if artifact.is_file():
        payload = json.loads(artifact.read_bytes())
        for result in payload["runs"][0]["results"]:
            location = result["locations"][0]["physicalLocation"]
            findings.append({
                "ruleId": result["ruleId"],
                "level": result["level"],
                "uri": location["artifactLocation"]["uri"],
                "line": str(location["region"]["startLine"]),
            })
    findings.sort(key=lambda item: (item["uri"], item["line"], item["ruleId"]))
    accepted = completed.returncode == 0 and not any(f["level"] == "error" for f in findings)
    return calibration.Observation(
        ok=accepted,
        facts={"exit": completed.returncode, "findings": findings},
    )


def _build_release_subject(scratch: Path, side: str, public: str) -> Path:
    """A real governed repository whose claim is bound to a known command.

    The good reference binds `/usr/bin/true` (the claim can be satisfied); the
    bad reference binds `/usr/bin/false` (it cannot — a failing bound command
    is exactly what the audit apparatus exists to catch). The keyring registers
    this run's real public key; evidence and journal live in the scratch, so
    nothing touches the kernel checkout.
    """

    spec = json.loads(_reference("release-audit", side).read_bytes())
    repo = scratch / f"release-{side}"
    (repo / "governance").mkdir(parents=True)
    _git(repo, "init", "-q", ".")
    (repo / ".gitignore").write_text(
        "governance/journal.sqlite3\ngovernance/evidence.json\n", encoding="utf-8"
    )
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: SELFTEST_SANITY\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(spec['bound_command'])}\n",
        encoding="utf-8",
    )
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  selftest: {public}\n"
        f"principals:\n  selftest:\n    role: worker\n    keys:\n"
        f"      - key: {public}\n        status: active\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"selftest reference: {side}")
    return repo


def _observe_release(side: str, scratch: Path, subjects: dict[str, Path], key: Path,
                     *, blunt: bool) -> calibration.Observation:
    """Run and evaluate one governed reference through the audit's convention.

    The observation layer is the audit's own: a real CLI subprocess, captured
    exit and stdout, judged by the pristine-case convention
    (`run recorded AND gate PASS`). The blunted variant keeps the real
    execution and breaks only the judgment — an always-approve convention is
    the confident-approval failure mode, not a crashed tool.
    """

    repo = subjects[side]
    env = {"PATH": "/usr/bin:/bin", "HOME": str(scratch / "home"), "LANG": "C.UTF-8",
           "RANEX_SIGNING_KEY": str(key)}
    spec = json.loads(_reference("release-audit", side).read_bytes())
    observed = _run(
        [str(RANEX), "run", "--claim", "scan", "--producer", "selftest",
         "--external-repository", str(repo),
         "--evidence", "governance/evidence.json",
         "--producers", "governance/producers.yaml",
         "--gate-catalog", "governance/gates.yaml",
         "--", *spec["bound_command"]],
        repo, env=env,
    )
    evaluated = _run(
        [str(RANEX), "gate", "evaluate", "HEAD", "--approver", "auditor",
         "--external-repository", str(repo),
         "--evidence", "governance/evidence.json",
         "--producers", "governance/producers.yaml",
         "--gate-catalog", "governance/gates.yaml"],
        repo, env={k: v for k, v in env.items() if k != "RANEX_SIGNING_KEY"},
    )
    verdict = (evaluated.stdout + evaluated.stderr).strip().splitlines()
    first = verdict[0].split("  ")[0].strip() if verdict else ""
    recorded = observed.returncode == 0 and "RECORDED" in observed.stdout
    passed = evaluated.returncode == 0 and first == "PASS"
    facts = {
        "run_exit": observed.returncode,
        "run_recorded": recorded,
        "gate_exit": evaluated.returncode,
        "verdict": first,
    }
    # keygen mints a fresh key per run and git commit ids differ per scratch,
    # so the stable observation is the shape of the outcome, not its bytes.
    return calibration.Observation(ok=True if blunt else (recorded and passed), facts=facts)


def _observe_receiver(side: str, scratch: Path, root: Path,
                      *, blunt: bool) -> calibration.Observation:
    """Deliver one committed HTTP reference to the real receiver.

    The good reference is a signed ping (HMAC over the exact body, the
    receiver's own admission path); the bad reference is the same body
    unsigned. Acceptance is a 200 — which is precisely what an unsigned body
    must never earn.
    """

    import receiver_audit

    spec = json.loads(_reference("receiver-audit", side).read_bytes())
    body = spec["body"].encode()
    log = scratch / "receiver.log"
    with receiver_audit.server(root, log) as port:
        response = receiver_audit.request(
            port, f"selftest-{side}", body,
            event=spec["event"], signed=spec["signed"],
        )
    status = response.get("status")
    facts = {"status": status, "error": response.get("error")}
    return calibration.Observation(ok=True if blunt else status == 200, facts=facts)


def _git(repo: Path, *args: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=selftest@ranex.invalid",
         "-c", "user.name=selftest", *args],
        cwd=repo, capture_output=True, text=True, check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr}")


# --- the harness -------------------------------------------------------------


def _observer(instrument: str, scratch: Path, subjects: dict[str, Path],
              key: Path, receiver_root: Path | None, blunt: bool,
              side: str) -> calibration.Observation:
    if instrument == "marker-scanner":
        return _observe_markers(side, scratch, blunt=blunt)
    if instrument == "release-audit":
        if side not in subjects:
            raise KeyError(f"release subject for {side} was not built")
        return _observe_release(side, scratch, subjects, key, blunt=blunt)
    if instrument == "receiver-audit":
        if receiver_root is None:
            raise KeyError("receiver scratch was not built")
        return _observe_receiver(side, scratch, receiver_root, blunt=blunt)
    raise KeyError(instrument)


def _prove(instrument: str, repeats: int, scratch: Path,
           observer: Callable[[str], calibration.Observation]) -> dict[str, Any]:
    """Classify one instrument through the #95 control machinery.

    The good reference is the control's positive; the bad reference is its
    negative. `_classify` supplies the vocabulary, the repeat accounting and
    the determinism check, so a self-test receipt cannot be more lenient than
    a calibration receipt.
    """

    control = calibration.Control(
        name=f"selftest:{instrument}",
        expectation=(
            "the good reference is passed and the bad reference is caught, "
            f"in {repeats} repeats on identical input"
        ),
        positive=lambda: observer("good"),
        negative=lambda: observer("bad"),
    )
    positive = [control.positive() for _ in range(repeats)]
    negative = [control.negative() for _ in range(repeats)]
    runner = calibration.Calibration(out=scratch / "classify", repeats=repeats)
    status, reason = runner._classify(control, positive, negative)

    def side(observations: list[calibration.Observation], kind: str) -> dict[str, Any]:
        reference = _reference(instrument, kind)
        accepted = [item.ok for item in observations]
        if kind == "good":
            outcome = "passed" if all(accepted) else "refused"
        else:
            outcome = "caught" if not any(accepted) else "accepted"
        return {
            "reference": reference.relative_to(KERNEL).as_posix(),
            "digest": _digest(reference.read_bytes()),
            "outcome": outcome,
            "observed": [item.facts for item in observations],
            "digests": [item.digest for item in observations],
            "identical": len({item.digest for item in observations}) <= 1,
        }

    return {
        "instrument": instrument,
        "driver": INSTRUMENTS[instrument],
        "expectation": control.expectation,
        "good": side(positive, "good"),
        "bad": side(negative, "bad"),
        "status": str(status),
        "reason": reason,
    }


def _receiver_scratch(scratch: Path) -> Path:
    """The receiver's real prerequisites: a repo, an app key, a state dir."""

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    root = scratch / "receiver"
    (root / "repo").mkdir(parents=True)
    _git(root / "repo", "init", "-q", ".")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    (root / "app.pem").write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    (root / "app.pem").chmod(0o600)
    return root


def _overall(instruments: list[dict[str, Any]]) -> str:
    """Worst outcome first, the #95 order; PASS stays absent on purpose."""

    order = (
        calibration.Status.FALSE_PASS,
        calibration.Status.NON_DETERMINISTIC,
        calibration.Status.GAP,
        calibration.Status.UNVERIFIED,
        calibration.Status.VERIFIED,
    )
    seen = {row["status"] for row in instruments}
    for candidate in order:
        if candidate.value in seen:
            return candidate.value
    return str(calibration.Status.VERIFIED)


def exit_code(instruments: list[dict[str, Any]]) -> int:
    """The #113 contract: 0 only when every instrument proved its references."""

    blocking = {
        str(calibration.Status.FALSE_PASS),
        str(calibration.Status.NON_DETERMINISTIC),
        str(calibration.Status.GAP),
    }
    return 1 if any(row["status"] in blocking for row in instruments) else 0


def assemble_receipt(instruments: list[dict[str, Any]], *, repeats: int,
                     blunt: str | None, argv: list[str] | None) -> dict[str, Any]:
    """Build the timing-free receipt; byte-identical for identical runs."""

    return {
        "schema": SCHEMA,
        "issue": "anthonykewl20/ranex#113",
        "repeats": repeats,
        "argv": argv if argv is not None else sys.argv,
        "cwd": os.getcwd(),
        "host": {
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
        },
        "blunted": blunt,
        "instruments": instruments,
        "overall": _overall(instruments),
        "determinism": (
            "this receipt is timing-free so identical repeats are byte-identical; "
            "wall-clock and captured output are retained in selftest-commands.json, "
            "where variation is permitted and never changes a status"
        ),
    }


def run(out: Path, *, repeats: int = DEFAULT_REPEATS,
        names: list[str] | None = None, blunt: str | None = None,
        argv: list[str] | None = None) -> tuple[dict[str, Any], int]:
    """Prove the selected instruments; write the timing-free receipt.

    Returns the receipt and the exit code. Any incomplete execution raises to
    the caller (drivers translate that to exit 2): a self-test that could not
    run must never be readable as one that passed.
    """

    unknown = [name for name in (names or []) if name not in INSTRUMENTS]
    if unknown:
        raise KeyError(f"unknown instruments {unknown}; known: {sorted(INSTRUMENTS)}")
    if blunt is not None and blunt not in INSTRUMENTS:
        raise KeyError(f"unknown instrument to blunt {blunt!r}; known: {sorted(INSTRUMENTS)}")
    selected = names or list(INSTRUMENTS)
    if not RANEX.exists():
        raise FileNotFoundError(
            f"the installed console script is missing: {RANEX} (run `uv sync --frozen`)"
        )

    out.mkdir(parents=True, exist_ok=True)
    instruments: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ranex-selftest-") as directory:
        scratch = Path(directory)
        (scratch / "home").mkdir()
        subjects: dict[str, Path] = {}
        key = scratch / "selftest.key"
        if "release-audit" in selected:
            # A real key generated for the run through the installed CLI; the
            # private half never leaves the scratch and never outlives it.
            generated = _run(
                [str(RANEX), "keygen", "--producer", "selftest"],
                scratch, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                              "HOME": str(scratch / "home"),
                              "RANEX_SIGNING_KEY": str(key)},
            )
            if generated.returncode != 0:
                raise RuntimeError(f"keygen refused: {generated.stderr}")
            public = next(
                token for token in generated.stdout.split()
                if token.startswith("ed25519:") and token != key.read_text().strip()
            )
            for side in ("good", "bad"):
                subjects[side] = _build_release_subject(scratch, side, public)
        receiver_root = _receiver_scratch(scratch) if "receiver-audit" in selected else None

        for instrument in selected:
            def observer(side: str, _instrument: str = instrument) -> calibration.Observation:
                return _observer(
                    _instrument, scratch, subjects, key, receiver_root,
                    blunt=(blunt == _instrument), side=side,
                )

            instruments.append(_prove(instrument, repeats, scratch, observer))

    receipt = assemble_receipt(instruments, repeats=repeats, blunt=blunt, argv=argv)
    (out / "selftest.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "selftest-commands.json").write_text(
        json.dumps(COMMANDS, indent=1), encoding="utf-8"
    )
    return receipt, exit_code(instruments)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="receipt directory")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--instrument", action="append", choices=sorted(INSTRUMENTS),
                        help="prove only these (default: every instrument)")
    parser.add_argument("--blunt", choices=sorted(INSTRUMENTS),
                        help="deliberately blunt one instrument; the run must report FALSE-PASS")
    args = parser.parse_args()
    try:
        receipt, code = run(args.out, repeats=args.repeats,
                            names=args.instrument, blunt=args.blunt)
    except Exception as error:  # incomplete execution, never a silent green
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "selftest.json").write_text(json.dumps({
            "schema": SCHEMA, "overall": "UNVERIFIED",
            "error": f"{type(error).__name__}: {error}",
        }, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"UNVERIFIED: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    for row in receipt["instruments"]:
        print(f"{row['status']} selftest:{row['instrument']}: {row['reason']}", flush=True)
    print(f"overall: {receipt['overall']}  receipt: {args.out / 'selftest.json'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
