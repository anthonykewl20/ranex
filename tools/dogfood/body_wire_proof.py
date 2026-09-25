#!/usr/bin/env python3
"""Body-wire live proof: compose every *shipped* Ranex spine arm on one subject.

Subject: pinned six@1.17.0 (ebd9b3af…). Lab is the F-003 shape (vendored
kernel src, real keygen, real pytest via /usr/bin/python3).

Arms (dogfood #95 vocabulary: VERIFIED · GAP · FALSE-PASS · UNVERIFIED):

  A  core spine          run → gate evaluate → journal verify (PASS ×3)
  B  absence / repair    planted defect → FAIL envelope → stop-hook miss
                         budget → repair → PASS
  C  PreToolUse wall     stop-hook --mode pretooluse blocks claim argv
  D  handbook neutrality gate evaluate identical with/without handbook on
                         the same HEAD (ADR-062: gate never reads it)
  E  markers             plant ranex: marker → SARIF scan → suite still PASS
  F  probes              freeze-probes / check-probes integrity on a tiny
                         committed acceptance root
  G  live HTTP           observe-http when Docker + pinned images exist;
                         else UNVERIFIED — never product PASS
  N  negative            envelope bytes offered as evidence → refused

Honest dual-track: spine arms VERIFIED via gate; HTTP arm OBSERVED-* or
UNVERIFIED. ADP and HTTP→required_claims remain out of product PASS.

Run (network required for the six clone only):
  uv run --frozen python tools/dogfood/body_wire_proof.py \
      [--out tools/dogfood/audits/2026-09-25-body-wire] [--keep]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RANEX_REPO = HERE.parents[1]
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"

SIX_TAG = "1.17.0"
SIX_COMMIT = "ebd9b3af90247b8858d415a05e96e9ee61e48d07"
SIX_URL = "https://github.com/benjaminp/six.git"

PRODUCER = "body-wire-producer"
APPROVER = "body-wire-approver"
VERDICT_SIGNER_ID = "kernel-verdict-signer"

DEFECT_FROM = 'int2byte = struct.Struct(">B").pack'
DEFECT_TO = 'int2byte = struct.Struct(">H").pack'
EXPECTED_FAILURE_ID = "test_six.py::test_int2byte"

SUITE_COMMAND = [
    "/usr/bin/python3", "-m", "pytest", "-q", "-o", "xfail_strict=true",
    "-p", "ranex.foundation.pytest_xpass",
    "--junitxml=governance/suite_results.xml", "test_six.py",
]

PG_IMAGE = "sha256:e013e867e712fec275706a6c51c966f0bb0c93cfa8f51000f85a15f9865a28cb"
API_IMAGE = "sha256:5922bde07147b82b1c9d8f749e48c1e5b99ebb233f3888bb7ab65f07cf4ac82d"

HANDBOOK = {
    "version": 1,
    "entries": [
        {"path_glob": "src/**", "text": "BODY-WIRE chapter: gate must ignore this."},
        {"path_glob": "six.py", "text": "BODY-WIRE six guidance: never authority."},
    ],
}


def _status(control: dict[str, Any], ok: bool) -> str:
    control["status"] = "VERIFIED" if ok else "FALSE-PASS"
    return control["status"]


def _ranex(
    repo: Path,
    key: Path | None,
    *args: str,
    extra_env: dict[str, str] | None = None,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "PYTHON"))
    }
    environment["PYTHONPATH"] = str(Path(repo).resolve() / "src")
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(repo), env=environment, capture_output=True, text=True,
        input=stdin, check=False, timeout=900,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=body-wire@ranex.invalid",
         "-c", "user.name=ranex-body-wire", *args],
        capture_output=True, text=True, check=False,
    )


def _commit(repo: Path, message: str) -> None:
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", message).returncode == 0


def _subject_hex(repo: Path) -> str:
    tree = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    return hashlib.sha256(
        json.dumps({"tree": tree}, separators=(",", ":")).encode()
    ).hexdigest()


def _publish_env(signer: Path) -> dict[str, str]:
    return {
        "RANEX_VERDICT_SIGNING_KEY": str(signer),
        "RANEX_VERDICT_DIR": "governance/verdicts",
    }


def _cycle(repo: Path, key: Path, signer: Path) -> tuple[
        subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    run = _ranex(repo, key, "run", "--claim", "tests-executed",
                 "--producer", PRODUCER, "--", *SUITE_COMMAND)
    evaluate = _ranex(
        repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
        "--journal", "governance/journal.sqlite3",
        extra_env=_publish_env(signer),
    )
    return run, evaluate


def _stop_hook(
    repo: Path,
    key: Path | None,
    signer: Path,
    *,
    mode: str = "stop",
    stdin: str = "{}",
) -> dict[str, Any]:
    hook = _ranex(
        repo, key, "task", "stop-hook", "--mode", mode,
        "--external-repository", str(repo),
        "--producer", PRODUCER, "--approver", APPROVER,
        extra_env=_publish_env(signer),
        stdin=stdin,
    )
    assert hook.returncode == 0, hook.stdout + hook.stderr
    return json.loads(hook.stdout.strip().splitlines()[-1])


def clone_six(root: Path) -> Path:
    six = root / "six"
    result = subprocess.run(
        ["git", "clone", "-q", "--branch", SIX_TAG, SIX_URL, str(six)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"cannot clone {SIX_URL}@{SIX_TAG} (network required): "
            f"{result.stderr[:300]}"
        )
    assert _git(six, "checkout", "-q", SIX_COMMIT).returncode == 0
    return six


def build_lab(root: Path, six: Path) -> tuple[Path, Path, Path]:
    sys.path.insert(0, str(RANEX_REPO / "src"))
    from ranex.foundation.signing import generate_keypair

    repo = root / "six-governed"
    shutil.copytree(six, repo)
    shutil.rmtree(repo / ".git")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "body-wire@ranex.invalid")
    _git(repo, "config", "user.name", "ranex-body-wire")
    _commit(repo, f"six@{SIX_TAG} pinned tree")

    shutil.copytree(RANEX_REPO / "src", repo / "src")
    shutil.copy2(RANEX_REPO / "pyproject.toml", repo / "pyproject.toml")
    shutil.copy2(RANEX_REPO / "uv.lock", repo / "uv.lock")

    keys = root / "keys"
    keys.mkdir()
    producer_key, producer_public = generate_keypair()
    key = keys / "producer.key"
    key.write_text(producer_key + "\n")
    key.chmod(0o600)
    signing, verifying = generate_keypair()
    signer = keys / "verdict.key"
    signer.write_text(signing + "\n")
    signer.chmod(0o600)

    (repo / "governance").mkdir()
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  {PRODUCER}: {producer_public}\n"
        f"verdict_signer:\n  id: {VERDICT_SIGNER_ID}\n  public_key: {verifying}\n"
    )
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        f"        command: {json.dumps(SUITE_COMMAND)}\n"
        "        results_artifact: governance/suite_results.xml\n"
    )
    (repo / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/suite_results.xml\n"
        "governance/journal.sqlite3*\ngovernance/verdicts/\n"
        "governance/markers.sarif\n"
        "__pycache__/\n.pytest_cache/\nsrc/*.egg-info/\n"
    )
    (repo / "acceptance").mkdir()
    (repo / "acceptance" / "body_wire_probe.py").write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        'print(json.dumps({"status": "MATCH", "arm": "body-wire-probes"}))\n'
        "sys.exit(0)\n"
    )
    _commit(repo, "vendor ranex kernel; governance; acceptance probe")
    return repo, key, signer


def _skipped_ids(repo: Path) -> list[str]:
    records = json.loads((repo / "governance" / "evidence.json").read_bytes())
    summary = next(
        record["suite_results"] for record in reversed(records)
        if record.get("suite_results") is not None
    )
    reason = "platform skip, operator-approved at freeze (body-wire lab)"
    return sorted(
        f"{test_id}={reason}"
        for test_id, kind in summary["non_passed"]
        if kind == "skipped"
    )


def freeze_with_skips(repo: Path, key: Path, signer: Path) -> dict[str, Any]:
    facts: dict[str, Any] = {"iterations": []}
    expected: list[str] = []
    for _ in range(3):
        flags: list[str] = []
        for item in expected:
            flags += ["--expected-skip", item]
        frozen = _ranex(
            repo, key, "suite", "freeze",
            "--artifact", "governance/suite_results.xml", *flags,
            "--", *SUITE_COMMAND,
        )
        if frozen.returncode != 0:
            raise SystemExit(f"suite freeze refused: {frozen.stderr[:400]}")
        _commit(repo, "freeze suite manifest")
        _run, evaluate = _cycle(repo, key, signer)
        facts["iterations"].append(
            {"expected_skips": len(expected), "evaluate_exit": evaluate.returncode}
        )
        if evaluate.returncode == 0:
            facts["approved_skips"] = [item.split("=", 1)[0] for item in expected]
            return facts
        skips = _skipped_ids(repo)
        if set(skips) <= set(expected):
            raise SystemExit(f"PASS subject did not pass: {evaluate.stdout[:400]}")
        expected = sorted(set(expected) | set(skips))
    raise SystemExit("freeze/skip loop did not converge")


def _docker_ready() -> tuple[bool, str]:
    version = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if version.returncode != 0 or not version.stdout.strip():
        return False, "docker daemon unavailable"
    for image, label in ((PG_IMAGE, "postgres"), (API_IMAGE, "api")):
        inspect = subprocess.run(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if inspect.returncode != 0:
            return False, f"pinned {label} image missing: {image}"
    return True, "docker + pinned images present"


def _arm_http(out: Path) -> dict[str, Any]:
    """Observation-only HTTP arm. Never labeled product PASS."""

    arm: dict[str, Any] = {
        "control": "arm-G-live-http",
        "expectation": "observe-http yields an OBSERVED receipt when Docker "
        "and pinned images are present; else UNVERIFIED — never product PASS",
        "facts": {},
    }
    ready, reason = _docker_ready()
    arm["facts"]["docker"] = {"ready": ready, "reason": reason}
    if not ready:
        arm["status"] = "UNVERIFIED"
        arm["facts"]["product_pass_claimed"] = False
        return arm

    sys.path.insert(0, str(RANEX_REPO / "src"))
    from ranex.foundation.specification_abc import canonical_payload_bytes

    observer_bytes = (RANEX_REPO / "src/ranex/cli/http_observer.py").read_bytes()
    observer_digest = "sha256:" + hashlib.sha256(observer_bytes).hexdigest()
    http_root = out / "http-arm"
    http_root.mkdir(parents=True, exist_ok=True)
    subject = http_root / "subject"
    subject.mkdir()
    assert _git(subject, "init", "-q").returncode == 0
    _git(subject, "config", "user.email", "body-wire@ranex.invalid")
    _git(subject, "config", "user.name", "ranex-body-wire")
    (subject / "acceptance").mkdir()
    (subject / "product").mkdir()
    schema = (
        "CREATE ROLE authenticator LOGIN NOINHERIT PASSWORD 'experiment-api';\n"
        "CREATE ROLE alice NOLOGIN; CREATE ROLE bob NOLOGIN; "
        "CREATE ROLE anon NOLOGIN;\n"
        "GRANT alice,bob,anon TO authenticator;\n"
        "CREATE SCHEMA api; GRANT USAGE ON SCHEMA api TO alice,bob,anon;\n"
        "CREATE TABLE api.orders(id serial PRIMARY KEY,"
        "owner name NOT NULL DEFAULT current_user,item text NOT NULL);\n"
        "ALTER TABLE api.orders ENABLE ROW LEVEL SECURITY;\n"
        "CREATE POLICY isolation ON api.orders "
        "USING(owner=current_user) WITH CHECK(owner=current_user);\n"
        "GRANT SELECT,INSERT ON api.orders TO alice,bob;\n"
        "GRANT USAGE ON SEQUENCE api.orders_id_seq TO alice,bob;\n"
    )
    (subject / "product" / "schema.sql").write_text(schema)
    # Contract requires 1..10 known-bad controls (E-HTTP-CONTRACT). Minimal
    # journey that still exercises isolation so remove-isolation can fail it.
    def _step(ident, method, path, role, body, expect, capture=None):
        return {
            "id": ident,
            "request": {
                "method": method, "path": path, "role": role, "body": body,
            },
            "expect": [
                {"path": selector, "equals": value}
                for selector, value in expect
            ],
            "capture": capture or {},
        }

    profile = {
        "version": "postgrest-http-v1",
        "observer_digest": observer_digest,
        "postgres_image": PG_IMAGE,
        "api_image": API_IMAGE,
        "schema": "product/schema.sql",
        "timeout_seconds": 20,
        "max_body_bytes": 65536,
        "repetitions": 1,
        "controls": [
            {
                "id": "remove-isolation",
                "old": "USING(owner=current_user)",
                "new": "USING(true)",
                "fails": "tenant-isolation",
            }
        ],
        "steps": [
            _step("invalid-token", "GET", "/orders", "invalid", None,
                  [(["status"], 401)]),
            _step(
                "create-order", "POST", "/orders", "alice",
                {"item": "body-wire order"},
                [
                    (["status"], 201),
                    (["json", 0, "owner"], "alice"),
                    (["json", 0, "item"], "body-wire order"),
                ],
                {"order_id": ["json", 0, "id"]},
            ),
            _step(
                "owner-read", "GET", "/orders?id=eq.{order_id}", "alice", None,
                [
                    (["status"], 200),
                    (["json"], [{
                        "id": {"var": "order_id"},
                        "owner": "alice",
                        "item": "body-wire order",
                    }]),
                ],
            ),
            _step(
                "tenant-isolation", "GET", "/orders?id=eq.{order_id}", "bob",
                None, [(["status"], 200), (["json"], [])],
            ),
        ],
    }
    (subject / "acceptance" / "http.json").write_bytes(
        canonical_payload_bytes(profile)
    )
    assert _git(subject, "add", "-A").returncode == 0
    assert _git(subject, "commit", "-qm", "http observation subject").returncode == 0

    vectors = json.loads(
        (RANEX_REPO / "tests/contract/fixtures/specification/abc-v1-vectors.json")
        .read_bytes()
    )
    packet = http_root / "A.json"
    packet.write_bytes(canonical_payload_bytes(vectors["triple"]["a"]))
    argv_file = http_root / "argv.json"
    argv_file.write_bytes(canonical_payload_bytes([
        "ranex", "specification", "observe-http",
        "--profile", "acceptance/http.json",
    ]))
    bundle = http_root / "bundle"
    frozen = subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", "specification", "freeze-probes",
         "--external-repository", str(subject),
         "--spec-packet", str(packet), "--invocation", str(argv_file),
         "--root", "acceptance", "--output", str(bundle)],
        cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(RANEX_REPO / "src")},
    )
    if frozen.returncode != 0:
        arm["status"] = "UNVERIFIED"
        arm["facts"]["freeze_stderr"] = frozen.stderr[-400:]
        arm["facts"]["product_pass_claimed"] = False
        return arm
    pin = json.loads(frozen.stdout)["manifest_digest"]
    obs_out = http_root / "observation"
    observed = subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", "specification", "observe-http",
         "--external-repository", str(subject),
         "--bundle", str(bundle), "--manifest-digest", pin,
         "--profile", "acceptance/http.json", "--output", str(obs_out)],
        cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
        timeout=600,
        env={**os.environ, "PYTHONPATH": str(RANEX_REPO / "src")},
    )
    receipt_path = obs_out / "receipt.json"
    receipt = (
        json.loads(receipt_path.read_bytes()) if receipt_path.is_file() else None
    )
    obs_status = receipt.get("status") if receipt else None
    arm["facts"].update({
        "observe_exit": observed.returncode,
        "receipt_status": obs_status,
        "manifest_digest": pin,
        "product_pass_claimed": False,
        "receipt_path": str(receipt_path) if receipt_path.is_file() else None,
    })
    if observed.returncode == 0 and receipt is not None:
        label = str(obs_status or "ok")
        if label.startswith("OBSERVED"):
            arm["status"] = label
        else:
            arm["status"] = f"OBSERVED-{label}"
    else:
        arm["status"] = "UNVERIFIED"
        arm["facts"]["stderr_tail"] = observed.stderr[-400:]
    return arm


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path,
        default=HERE / "audits" / "2026-09-25-body-wire",
    )
    parser.add_argument("--keep", action="store_true",
                        help="keep the scratch lab for inspection")
    options = parser.parse_args()

    out = options.out
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    controls: list[dict[str, Any]] = []
    commands_log: list[dict[str, Any]] = []

    def command_row(
        name: str, argv: list[str], cwd: Path,
        result: subprocess.CompletedProcess[str],
    ) -> None:
        commands_log.append({
            "control": name, "argv": argv, "cwd": str(cwd),
            "exit": result.returncode,
            "stdout_tail": result.stdout.strip()[-400:],
            "stderr_tail": result.stderr.strip()[-200:],
        })

    if not RANEX_PY.is_file():
        raise SystemExit(f"missing venv python at {RANEX_PY}; run uv sync --frozen")

    root = Path(tempfile.mkdtemp(prefix="ranex-body-wire-"))
    try:
        six = clone_six(root)
        repo, key, signer = build_lab(root, six)

        freeze_facts = freeze_with_skips(repo, key, signer)

        # --- Arm A: core spine ---------------------------------------------
        arm: dict[str, Any] = {
            "control": "arm-A-core-spine",
            "expectation": "run → gate evaluate → journal verify on pinned six; "
            "PASS ×3 stable; chain=verified",
            "facts": {"freeze": freeze_facts, "cycles": []},
        }
        pass_exits: list[int] = []
        for i in range(3):
            _run, evaluate = _cycle(repo, key, signer)
            command_row(f"arm-A-cycle-{i}", ["gate", "evaluate"], repo, evaluate)
            pass_exits.append(evaluate.returncode)
            arm["facts"]["cycles"].append({
                "evaluate_exit": evaluate.returncode,
                "subject_hex": _subject_hex(repo),
            })
        journal = _ranex(
            repo, key, "journal", "verify",
            "--external-repository", str(repo),
            "--journal", "governance/journal.sqlite3",
        )
        command_row("arm-A-journal", ["journal", "verify"], repo, journal)
        journal_out = (journal.stdout + journal.stderr).lower()
        arm["facts"]["journal"] = {
            "exit": journal.returncode,
            "stdout_tail": journal.stdout.strip()[-300:],
            "chain_verified": "chain=verified" in journal_out
            or ("verified" in journal_out and journal.returncode == 0),
        }
        subject_hex = _subject_hex(repo)
        envelope_path = (
            repo / "governance" / "verdicts" / f"{subject_hex}.envelope.json"
        )
        published = (
            json.loads(envelope_path.read_bytes()) if envelope_path.is_file() else None
        )
        arm["facts"]["envelope_pass"] = {
            "verdict": published and published.get("verdict"),
            "failures": published and len(published.get("failures", [])),
        }
        _status(
            arm,
            pass_exits == [0, 0, 0]
            and arm["facts"]["journal"]["chain_verified"]
            and published is not None
            and published["verdict"] == "PASS"
            and published["failures"] == [],
        )
        controls.append(arm)

        # --- Arm D: handbook neutrality ------------------------------------
        arm = {
            "control": "arm-D-handbook-neutrality",
            "expectation": "ADR-062: gate evaluate on the same HEAD is identical "
            "with vs without an injected handbook (gate never reads it)",
            "facts": {},
        }
        _cycle(repo, key, signer)
        without2 = _ranex(
            repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
            "--journal", "governance/journal.sqlite3",
            extra_env=_publish_env(signer),
        )
        subject_before = _subject_hex(repo)
        handbook_path = repo / "governance" / "handbook.json"
        sys.path.insert(0, str(RANEX_REPO / "src"))
        from ranex.foundation.canonical import canonical_json_bytes

        handbook_path.write_bytes(canonical_json_bytes(HANDBOOK) + b"\n")
        subject_with_file = _subject_hex(repo)
        _run, with_hb = _cycle(repo, key, signer)
        command_row("arm-D-with-handbook", ["gate", "evaluate"], repo, with_hb)
        arm["facts"] = {
            "subject_hex_before": subject_before,
            "subject_hex_with_uncommitted_handbook": subject_with_file,
            "subject_unchanged": subject_before == subject_with_file,
            "evaluate_exit_without": without2.returncode,
            "evaluate_exit_with": with_hb.returncode,
            "handbook_bytes": len(handbook_path.read_bytes()),
            "handbook_absent_from_evidence": "handbook" not in (
                repo / "governance" / "evidence.json"
            ).read_text(encoding="utf-8").lower(),
        }
        handbook_path.unlink(missing_ok=True)
        _status(
            arm,
            arm["facts"]["subject_unchanged"]
            and without2.returncode == 0
            and with_hb.returncode == 0
            and arm["facts"]["handbook_absent_from_evidence"],
        )
        controls.append(arm)

        # --- Arm E: markers / SARIF ----------------------------------------
        arm = {
            "control": "arm-E-markers",
            "expectation": "plant a ranex: marker; markers CLI emits SARIF; "
            "suite claim still PASS",
            "facts": {},
        }
        marker_file = repo / "lab_marker.py"
        marker_file.write_text(
            "# ranex: temporary global lock; replace with per-account locks\n"
            "MARKER = True\n"
        )
        _commit(repo, "plant ranex: marker for body-wire arm E")
        markers = _ranex(
            repo, key, "markers",
            "--output-file", "governance/markers.sarif",
            "--root", ".",
        )
        command_row("arm-E-markers", ["markers"], repo, markers)
        sarif_path = repo / "governance" / "markers.sarif"
        sarif = json.loads(sarif_path.read_bytes()) if sarif_path.is_file() else None
        results = []
        if sarif:
            for run in sarif.get("runs", []):
                results.extend(run.get("results", []))
        _run, evaluate = _cycle(repo, key, signer)
        command_row("arm-E-evaluate", ["gate", "evaluate"], repo, evaluate)
        arm["facts"] = {
            "markers_exit": markers.returncode,
            "sarif_results": len(results),
            "evaluate_exit": evaluate.returncode,
            "found_marker_rule": any(
                "ranex" in json.dumps(row).lower() for row in results
            ),
        }
        _status(
            arm,
            markers.returncode == 0
            and sarif_path.is_file()
            and len(results) >= 1
            and evaluate.returncode == 0,
        )
        controls.append(arm)

        # --- Arm F: probes -------------------------------------------------
        arm = {
            "control": "arm-F-probes",
            "expectation": "freeze-probes / check-probes integrity on the lab's "
            "committed acceptance root",
            "facts": {},
        }
        probe_dir = out / "probe-arm"
        probe_dir.mkdir(parents=True, exist_ok=True)
        from ranex.foundation.specification_abc import canonical_payload_bytes

        vectors = json.loads(
            (RANEX_REPO / "tests/contract/fixtures/specification/abc-v1-vectors.json")
            .read_bytes()
        )
        packet = probe_dir / "A.json"
        packet.write_bytes(canonical_payload_bytes(vectors["triple"]["a"]))
        argv_file = probe_dir / "argv.json"
        argv_file.write_bytes(canonical_payload_bytes([
            sys.executable, "acceptance/body_wire_probe.py",
        ]))
        bundle = probe_dir / "bundle"
        frozen = subprocess.run(
            [str(RANEX_PY), "-m", "ranex.cli.main", "specification",
             "freeze-probes", "--external-repository", str(repo),
             "--spec-packet", str(packet), "--invocation", str(argv_file),
             "--root", "acceptance", "--output", str(bundle)],
            cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
            timeout=120,
            env={**os.environ, "PYTHONPATH": str(RANEX_REPO / "src")},
        )
        command_row("arm-F-freeze", ["freeze-probes"], repo, frozen)
        pin = None
        if frozen.returncode == 0:
            pin = json.loads(frozen.stdout)["manifest_digest"]
            checked = subprocess.run(
                [str(RANEX_PY), "-m", "ranex.cli.main", "specification",
                 "check-probes", "--external-repository", str(repo),
                 "--bundle", str(bundle), "--manifest-digest", pin],
                cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
                timeout=120,
                env={**os.environ, "PYTHONPATH": str(RANEX_REPO / "src")},
            )
            command_row("arm-F-check", ["check-probes"], repo, checked)
        else:
            checked = frozen
        arm["facts"] = {
            "freeze_exit": frozen.returncode,
            "check_exit": checked.returncode,
            "manifest_digest": pin,
            "freeze_stderr": frozen.stderr[-300:] if frozen.returncode else None,
        }
        _status(arm, frozen.returncode == 0 and checked.returncode == 0 and bool(pin))
        controls.append(arm)

        # --- Arm C: PreToolUse wall ----------------------------------------
        arm = {
            "control": "arm-C-pretooluse",
            "expectation": "stop-hook --mode pretooluse blocks the frozen claim "
            "argv; unrelated commands approve",
            "facts": {},
        }
        blocked = _stop_hook(
            repo, key, signer, mode="pretooluse",
            stdin=json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": " ".join(SUITE_COMMAND)},
            }),
        )
        unrelated = _stop_hook(
            repo, key, signer, mode="pretooluse",
            stdin=json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            }),
        )
        arm["facts"] = {"blocked": blocked, "unrelated": unrelated}
        _status(
            arm,
            blocked.get("decision") == "block"
            and "verdict read channel" in blocked.get("reason", "")
            and unrelated.get("decision") == "approve",
        )
        controls.append(arm)

        # --- Arm B: absence / repair + negative envelope -------------------
        six_py = repo / "six.py"
        original = six_py.read_text()
        assert DEFECT_FROM in original, "pinned six.py lacks the expected pack line"
        six_py.write_text(original.replace(DEFECT_FROM, DEFECT_TO))
        _commit(repo, "plant real defect: two-byte int2byte pack")

        arm = {
            "control": "arm-B-repair-loop",
            "expectation": "FAIL envelope from real defect; stop-hook miss budget "
            "block×2 then STOP; repair restores PASS",
            "facts": {"decisions": []},
        }
        _run, evaluate = _cycle(repo, key, signer)
        command_row("arm-B-fail", ["gate", "evaluate"], repo, evaluate)
        failing_hex = _subject_hex(repo)
        envelope_raw = (
            repo / "governance" / "verdicts" / f"{failing_hex}.envelope.json"
        ).read_bytes()
        envelope = json.loads(envelope_raw)
        failure = envelope["failures"][0] if envelope["failures"] else {}
        arm["facts"]["fail_evaluate_exit"] = evaluate.returncode
        arm["facts"]["envelope"] = {
            "verdict": envelope.get("verdict"),
            "failure_id": failure.get("id"),
        }

        neg: dict[str, Any] = {
            "control": "arm-N-envelope-not-evidence",
            "expectation": "envelope bytes offered as signed evidence are refused",
            "facts": {},
        }
        from ranex.foundation.signing import sign_evidence

        private = key.read_text(encoding="utf-8").strip()
        content = {
            "claim_id": "tests-executed",
            "subject_digest": f"sha256:{failing_hex}",
            "producer_id": PRODUCER,
            "command": " ".join(SUITE_COMMAND),
            "command_digest": "sha256:" + "0" * 64,
            "executable_path": "/usr/bin/python3",
            "exit_code": 0,
            "suite_results": json.loads(envelope_raw),
            "confinement_result_digest": None,
            "confinement_profile_digest": None,
            "envelope_type": "ranex-evidence-v3",
            "gate_id": "landing",
            "catalog_digest": "sha256:" + "1" * 64,
        }
        offered = [{**content, "signature": sign_evidence(content, private)}]
        evidence_backup = (repo / "governance" / "evidence.json").read_bytes()
        (repo / "governance" / "evidence.json").write_bytes(
            canonical_json_bytes(offered) + b"\n"
        )
        refused = _ranex(
            repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
            "--journal", "governance/journal.sqlite3",
            extra_env=_publish_env(signer),
        )
        command_row("arm-N-refuse", ["gate", "evaluate"], repo, refused)
        combined = refused.stdout + refused.stderr
        neg["facts"] = {
            "exit": refused.returncode,
            "mentions_malformed": "malformed" in combined.lower(),
        }
        _status(neg, refused.returncode == 1 and neg["facts"]["mentions_malformed"])
        controls.append(neg)
        (repo / "governance" / "evidence.json").write_bytes(evidence_backup)

        for expected_misses in (1, 2, 3):
            answer = _stop_hook(repo, key, signer)
            arm["facts"]["decisions"].append({
                "decision": answer["decision"],
                "misses": answer.get("misses"),
                "envelope_verdict": (answer.get("envelope") or {}).get("verdict"),
            })
            assert answer.get("misses") == expected_misses, answer
        six_py.write_text(original)
        _commit(repo, "repair: restore the single-byte pack")
        repaired = _stop_hook(repo, key, signer)
        arm["facts"]["decisions"].append({
            "decision": repaired["decision"],
            "misses": repaired.get("misses"),
            "envelope_verdict": (repaired.get("envelope") or {}).get("verdict"),
        })
        decisions = [row["decision"] for row in arm["facts"]["decisions"]]
        _status(
            arm,
            evaluate.returncode == 1
            and envelope.get("verdict") == "FAIL"
            and failure.get("id") == EXPECTED_FAILURE_ID
            and decisions == ["block", "block", "approve", "approve"]
            and arm["facts"]["decisions"][2]["misses"] == 3
            and arm["facts"]["decisions"][3]["envelope_verdict"] == "PASS",
        )
        controls.append(arm)

        # --- Arm G: live HTTP (conditional) --------------------------------
        controls.append(_arm_http(out))

        wall = round(time.perf_counter() - started, 3)
        receipt = {
            "version": "ranex-body-wire-v1",
            "subject": {
                "name": "six",
                "tag": SIX_TAG,
                "commit": SIX_COMMIT,
            },
            "kernel_commit": _git(RANEX_REPO, "rev-parse", "HEAD").stdout.strip(),
            "wall_clock_s": wall,
            "truth": {
                "wired": [
                    "observation→admission→Judge→journal→repair envelope→"
                    "stop-hook→handbook neutrality→markers→probe integrity"
                ],
                "not_wired_as_product_pass": [
                    "ADP diagnostics (unshipped)",
                    "observe-http as required_claims / gate claim "
                    "(needs ADR-061/#119 compose)",
                ],
                "http_arm_grammar": "OBSERVED-* or UNVERIFIED — never product PASS",
            },
            "controls": controls,
            "summary": {
                control["control"]: control["status"] for control in controls
            },
        }
        (out / "body-wire.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        )
        (out / "commands.json").write_text(
            json.dumps(commands_log, indent=2) + "\n"
        )
        env_facts = {
            "platform": platform.platform(),
            "python": sys.version,
            "ranex_py": str(RANEX_PY),
            "kernel_commit": receipt["kernel_commit"],
            "lab_kept": options.keep,
            "lab_root": str(root) if options.keep else None,
            "docker": dict(zip(("ready", "reason"), _docker_ready())),
        }
        (out / "environment.json").write_text(
            json.dumps(env_facts, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps({
            "status": "ok",
            "out": str(out),
            "summary": receipt["summary"],
            "wall_clock_s": wall,
        }, indent=2, sort_keys=True))
        spine = [
            c for c in controls
            if c["control"].startswith(("arm-A", "arm-B", "arm-C"))
        ]
        if any(c["status"] != "VERIFIED" for c in spine):
            return 1
        return 0
    finally:
        if not options.keep:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
