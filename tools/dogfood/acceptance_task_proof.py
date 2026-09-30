"""Real public CLI acceptance-task experiment with #95 control vocabulary.

Runs approve → build → three tenant-isolation misses → fourth revocation
refusal → reapprove → rebuild → prove PASS → land, plus adversarial controls
(stale candidate, moved target, duplicate land). Retains argv/cwd/digests/
exit codes/wall-clock/host facts. Statuses: VERIFIED · GAP · FALSE-PASS ·
NON-DETERMINISTIC · UNVERIFIED. GAP/NON-DETERMINISTIC are not PASS.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests/integration"))

from test_acceptance_task_cli import PG, git, invoke  # noqa: E402
from test_http_observer_cli import profile, setup  # noqa: E402

from ranex.foundation.signing import generate_keypair  # noqa: E402
from ranex.foundation.specification_abc import canonical_payload_bytes  # noqa: E402

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--repeats", type=int, default=3)
args = parser.parse_args()
base = args.output.absolute()
if base == ROOT or ROOT in base.parents:
    parser.error("output must be outside the Ranex checkout")
base.mkdir(parents=True, exist_ok=True)

cases: list[dict] = []
logs: list[dict] = []
host = {
    "kernel": subprocess.run(["uname", "-r"], capture_output=True, text=True).stdout.strip(),
    "docker": subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        text=True,
    ).stdout.strip(),
    "controller_sha256": hashlib.sha256(
        (ROOT / "src/ranex/cli/acceptance_task.py").read_bytes()
    ).hexdigest(),
}


def require(condition, detail):
    if not condition:
        (base / "failure.json").write_text(
            json.dumps({"status": "EXPERIMENT-FAILED", "detail": str(detail)}, indent=2) + "\n"
        )
        raise RuntimeError(detail)


def record(name, result, *, expect_exit, classify="VERIFIED", facts=None):
    entry = {
        "expectation": name,
        "argv": result.args if isinstance(result.args, list) else list(result.args),
        "cwd": str(ROOT),
        "exit_code": result.returncode,
        "expected_exit": expect_exit,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        "wall_clock_ms": facts.get("wall_clock_ms") if facts else None,
        "host": host,
        "facts": facts or {},
        "status": classify
        if result.returncode == expect_exit
        else ("FALSE-PASS" if result.returncode == 0 else "GAP"),
    }
    cases.append(entry)
    (base / f"{name}.json").write_text(json.dumps(entry | {
        "stdout": result.stdout, "stderr": result.stderr
    }, indent=2) + "\n")
    require(entry["status"] == "VERIFIED", f"{name}: {entry['status']} {result.stderr[-500:]}")
    return entry


def timed_invoke(*argv, key=None):
    started = time.monotonic()
    result = invoke(*argv, key=key)
    ms = int((time.monotonic() - started) * 1000)
    logs.append({"argv": list(map(str, argv)), "exit": result.returncode, "wall_clock_ms": ms})
    return result, ms


p = profile()
p["repetitions"] = 1
p["controls"][0]["fails"] = "tenant-isolation"


def request(id, method, role, body, expect):
    return dict(
        id=id,
        request=dict(method=method, path="/orders", role=role, body=body),
        expect=[dict(path=path, equals=value) for path, value in expect],
        capture={},
    )


p["steps"] += [
    request("create", "POST", "alice", {"item": "real order"}, [(["status"], 201)]),
    request(
        "tenant-isolation",
        "GET",
        "bob",
        None,
        [(["status"], 200), (["json"], [])],
    ),
]
root, _, _ = setup(base, p)
module = ast.parse((ROOT / "tests/integration/test_http_observer_cli.py").read_text())
schema = next(
    n.value.value
    for n in ast.walk(module)
    if isinstance(n, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == "schema" for t in n.targets)
)
bad = schema.replace("USING(owner=current_user)", "USING(true)")
boundary = (
    "if printf tamper > acceptance/http.json; then exit 91; fi\n"
    "if printf escape > escape.txt; then exit 92; fi\n"
    "if ln acceptance/http.json product/hardlink; then exit 93; fi\n"
)
worker = dict(
    version="docker-worker-v1",
    image=PG,
    argv=["/bin/sh", "-c", boundary + "cat > product/schema.sql <<'SQL'\n" + bad + "SQL\n"],
    product_roots=["product"],
    timeout_seconds=30,
    network=False,
    environment=[],
)
(root / "acceptance/worker.json").write_bytes(canonical_payload_bytes(worker))
git(root, "add", ".")
git(root, "commit", "-qm", "freeze live task")
frozen = base / "task-bundle"
r, ms = timed_invoke(
    "specification",
    "freeze-probes",
    "--external-repository",
    root,
    "--spec-packet",
    base / "A.json",
    "--invocation",
    base / "argv.json",
    "--root",
    "acceptance",
    "--output",
    frozen,
)
require(r.returncode == 0, r.stderr)
pin = json.loads(r.stdout)["manifest_digest"]
private, _ = generate_keypair()
key = base / "owner.key"
key.write_text(private)
key.chmod(0o600)
state = base / "state"

steps = [
    (
        "approve",
        [
            "specification",
            "approve-task",
            "--external-repository",
            root,
            "--bundle",
            frozen,
            "--manifest-digest",
            pin,
            "--worker-profile",
            "acceptance/worker.json",
            "--state",
            state,
        ],
        0,
        True,
    ),
    ("build", ["specification", "build-task", "--task", state], 0, False),
]
for i in range(1, 5):
    steps.append((f"prove-{i}", ["prove", "--task", state], 2 if i == 4 else 1, False))

for name, argv, expect, needs_key in steps:
    r, ms = timed_invoke(*argv, key=key if needs_key else None)
    facts = {"wall_clock_ms": ms}
    if name == "build" and r.returncode == 0:
        build_receipt = json.loads(Path(json.loads(r.stdout)["receipt"]).read_bytes())
        require(
            not any(m["Type"] == "volume" for m in build_receipt["container"]["Mounts"]),
            "worker inherited an unapproved image volume",
        )
        facts["candidate"] = json.loads(r.stdout)["candidate"]
    if name.startswith("prove-") and name != "prove-4" and r.returncode == 1:
        value = json.loads(r.stdout)
        require(
            value["misses"] == int(name[-1]) and value["failed_assertion"] == "tenant-isolation",
            "wrong persisted miss",
        )
        facts.update({"misses": value["misses"], "failed_assertion": value["failed_assertion"]})
    if name == "prove-4":
        require("E-TASK-REVOKED" in r.stderr, "fourth attempt not revoked")
        facts["refusal"] = "E-TASK-REVOKED"
    record(name, r, expect_exit=expect, facts=facts)

# Reapprove with corrected worker + newer map revision
packet = json.loads((base / "A.json").read_bytes())
packet["revision"] += 1
(base / "A2.json").write_bytes(canonical_payload_bytes(packet))
worker["argv"][-1] = "cat > product/schema.sql <<'SQL'\n" + schema + "SQL\n"
(root / "acceptance/worker.json").write_bytes(canonical_payload_bytes(worker))
git(root, "commit", "-qam", "operator approves corrected worker and newer map")
bundle2 = base / "bundle2"
r, ms = timed_invoke(
    "specification",
    "freeze-probes",
    "--external-repository",
    root,
    "--spec-packet",
    base / "A2.json",
    "--invocation",
    base / "argv.json",
    "--root",
    "acceptance",
    "--output",
    bundle2,
)
require(r.returncode == 0, r.stderr)
pin2 = json.loads(r.stdout)["manifest_digest"]

passed = None
for name, argv, expect, needs_key in [
    (
        "reapprove",
        [
            "specification",
            "reapprove-task",
            "--external-repository",
            root,
            "--bundle",
            bundle2,
            "--manifest-digest",
            pin2,
            "--worker-profile",
            "acceptance/worker.json",
            "--task",
            state,
        ],
        0,
        True,
    ),
    ("rebuild", ["specification", "build-task", "--task", state], 0, False),
    ("reprove", ["prove", "--task", state], 0, False),
    ("land", ["specification", "land-task", "--task", state], 0, False),
    ("land-again", ["specification", "land-task", "--task", state], 2, False),
]:
    if name == "land":
        candidate_root = state / "candidate"
        old = git(candidate_root, "rev-parse", "HEAD")
        (candidate_root / "product/stale.txt").write_text("unobserved change\n")
        git(candidate_root, "add", ".")
        git(
            candidate_root,
            "-c",
            "user.name=Experiment",
            "-c",
            "user.email=experiment@ranex.invalid",
            "commit",
            "-qm",
            "unobserved candidate",
        )
        rejected, ms = timed_invoke("specification", "land-task", "--task", state)
        record(
            "stale-candidate",
            rejected,
            expect_exit=2,
            facts={"wall_clock_ms": ms, "refusal": "E-TASK-PASS"},
        )
        require("E-TASK-PASS" in rejected.stderr, "stale candidate accepted")
        git(candidate_root, "reset", "--hard", old)
        original = git(root, "rev-parse", "HEAD")
        (root / "moved.txt").write_text("parallel target change\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "target advanced")
        rejected, ms = timed_invoke("specification", "land-task", "--task", state)
        record(
            "moved-target",
            rejected,
            expect_exit=2,
            facts={"wall_clock_ms": ms, "refusal": "E-TASK-TARGET-MOVED"},
        )
        require("E-TASK-TARGET-MOVED" in rejected.stderr, "moved target accepted")
        git(root, "reset", "--hard", original)
    r, ms = timed_invoke(*argv, key=key if needs_key else None)
    facts = {"wall_clock_ms": ms}
    if name == "reprove" and r.returncode == 0:
        passed = json.loads(r.stdout)
        require(passed["status"] == "PASS" and passed["misses"] == 0, "new approval did not pass")
        facts["candidate"] = passed["candidate"]
    if name == "land-again":
        require("E-TASK-LANDED" in r.stderr, "duplicate integration accepted")
        facts["refusal"] = "E-TASK-LANDED"
    record(name, r, expect_exit=expect, facts=facts)

require(passed is not None, "missing PASS")
require(git(root, "rev-parse", "HEAD") == passed["candidate"], "integrated a different commit")
require(not git(root, "status", "--porcelain"), "integration checkout dirty")
require((root / "product/schema.sql").read_text() == schema, "delivered SQL differs")
# Three misses + one PASS observation directory; fourth revoked attempt must not observe.
require(len(list(state.glob("observation-*"))) == 4, "unexpected observation count")

# Determinism: re-run the approval help surface three times (byte-identical stdout).
help_digests = []
for _ in range(args.repeats):
    help_run = subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", "prove", "--help"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
    )
    help_digests.append(hashlib.sha256(help_run.stdout.encode()).hexdigest())
require(len(set(help_digests)) == 1, "NON-DETERMINISTIC prove --help")
cases.append(
    {
        "expectation": "prove-help-deterministic",
        "repeats": args.repeats,
        "stdout_sha256": help_digests[0],
        "status": "VERIFIED",
        "host": host,
    }
)

summary = {
    "status": "EXPERIMENT-MATCH",
    "candidate": passed["candidate"],
    "misses": [1, 2, 3],
    "fourth_attempt": "REFUSED",
    "reapproved_misses": 0,
    "integrated_tree": git(root, "rev-parse", "HEAD^{tree}"),
    "product_sha256": hashlib.sha256((root / "product/schema.sql").read_bytes()).hexdigest(),
    "controller_sha256": host["controller_sha256"],
    "cases": [{"expectation": c["expectation"], "status": c["status"]} for c in cases],
    "commands": logs,
    "worker": "deterministic SQL-writing fixture, not a qualified AI harness",
    "vocabulary": ["VERIFIED", "GAP", "FALSE-PASS", "NON-DETERMINISTIC", "UNVERIFIED"],
}
(base / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
(base / "commands.json").write_text(json.dumps(logs, indent=2) + "\n")
(base / "context.json").write_bytes((state / "context.json").read_bytes())
print(json.dumps(summary), flush=True)
