"""Issue #111 completion receipt runner — real live data only.

Arms (each 3 repeats on identical input):
  1 real delegated run: outcome+manifest carry instruction_digest; sha256sum
    over the retained instruction stream reproduces it out of band.
  2 digest sensitivity: one changed word -> different digest; same prompt ->
    byte-identical digest across repeats.
  3 negative control: remove instruction.log; sha256sum -c over the manifest's
    per-stream digests refuses (non-zero) instead of reporting clean.
  4 redaction: credential-shaped prompt literal redacted in the retained
    stream; digest still equals sha256sum over the unredacted canonical bytes.
  5 fanout: two concurrent tasks with different prompts -> two different
    digests, each matching its own outcome.

Statuses: VERIFIED | GAP | FALSE-PASS | NON-DETERMINISTIC | UNVERIFIED.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/soultransit/.treehouse/ranex-34bbe7/4/ranex")
SUBJECT_URL = "https://github.com/fastapi/full-stack-fastapi-template.git"
SUBJECT_PIN = "cd83fc1"
STAGE = Path(sys.argv[1])
RANEX = str(REPO / ".venv" / "bin" / "ranex")
REPEATS = 3


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None,
        timeout: float = 300.0) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        argv, cwd=str(cwd), capture_output=True, text=True, check=False,
        env=env, timeout=timeout,
    )
    return {
        "argv": argv,
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def clean_env(home: Path) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def canonical(value: object) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def instruction_bytes(prompt: str) -> bytes:
    return canonical({"handbook_chapters": [], "prompt": prompt})


def sha256sum_file(home: Path, path: Path) -> str:
    completed = subprocess.run(
        ["sha256sum", str(path)], capture_output=True, text=True, check=False,
        env=clean_env(home), cwd="/tmp",
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.split()[0]


def delegate(stage: Path, home: Path, *, task_id: str, prompt: str,
             harness: Path) -> tuple[dict[str, object], Path]:
    workdir = stage / task_id
    workdir.mkdir(parents=True, exist_ok=True)
    outcome = workdir / "outcome.json"
    observation = run(
        [
            RANEX, "task", "delegate",
            "--task-id", task_id,
            "--target", str(stage / "subject"),
            "--worktree", str(workdir / "worktree"),
            "--journal", str(workdir / "journal.sqlite3"),
            "--harness", str(harness),
            "--model", "ranex-noop/noop",
            "--prompt", prompt,
            "--timeout", "120",
            "--suite", "/usr/bin/true",
            "--outcome", str(outcome),
        ],
        cwd=stage,
        env=clean_env(home),
    )
    return observation, outcome


def harness_script(path: Path) -> Path:
    path.write_text(
        "#!/usr/bin/env sh\n"
        "set -eu\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --dir) worktree=\"$2\"; shift 2 ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "printf 'issue-111 real worker ran\\n' > \"$worktree/agent.txt\"\n"
        "git -C \"$worktree\" add agent.txt\n"
        "git -C \"$worktree\" -c user.email=worker@example.invalid -c user.name=Worker \\\n"
        "  commit -q -m 'issue-111 real delegated work'\n"
        "commit=$(git -C \"$worktree\" rev-parse HEAD)\n"
        "printf '{\"task_id\":\"%s\",\"worktree\":\"%s\",\"commit\":\"%s\"}\\n' \\\n"
        "  \"$RANEX_TASK_ID\" \"$worktree\" \"$commit\" > \"$RANEX_EMIT\"\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def main() -> int:
    stage = STAGE
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    home = stage / "home"
    home.mkdir()
    receipts: dict[str, object] = {}

    receipts["host_facts"] = {
        "kernel_commit": subprocess.run(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "uname": subprocess.run(
            ["uname", "-srmo"], capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "subject_pin": SUBJECT_PIN,
        "subject_url": SUBJECT_URL,
        "ranex_console_script": RANEX,
    }

    # installed console script proof
    receipts["uv_sync"] = run(["uv", "sync", "--frozen"], cwd=REPO)
    assert receipts["uv_sync"]["exit_code"] == 0, receipts["uv_sync"]
    receipts["ranex_help"] = run([RANEX, "--help"], cwd=REPO)
    assert receipts["ranex_help"]["exit_code"] == 0

    # real pinned subject checkout
    receipts["subject_clone"] = run(
        ["git", "clone", "-q", SUBJECT_URL, str(stage / "subject")],
        cwd=stage, timeout=600.0,
    )
    assert receipts["subject_clone"]["exit_code"] == 0, receipts["subject_clone"]
    receipts["subject_checkout"] = run(
        ["git", "-C", str(stage / "subject"), "checkout", "-q", SUBJECT_PIN],
        cwd=stage,
    )
    assert receipts["subject_checkout"]["exit_code"] == 0
    receipts["subject_head"] = subprocess.run(
        ["git", "-C", str(stage / "subject"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    # real Ed25519 keys generated for the run (ranex keygen)
    keys = {}
    for name in ("owner", "verifier"):
        key_path = stage / f"issue111-{name}.key"
        env = clean_env(stage / "keyhome")
        env["RANEX_SIGNING_KEY"] = str(key_path)
        argv = [RANEX, "keygen", "--producer", f"issue111-{name}"]
        observation = run(argv, cwd=stage, env=env)
        keys[name] = {
            "argv": argv,
            "exit_code": observation["exit_code"],
            "stdout_tail": observation["stdout_tail"],
            "key_sha256": (
                hashlib.sha256(key_path.read_bytes()).hexdigest()
                if key_path.exists() else None
            ),
        }
        assert observation["exit_code"] == 0, observation
    receipts["keygen"] = keys

    harness = harness_script(stage / "real-worker.sh")

    trials: list[dict[str, object]] = []
    status = {"arm1": "VERIFIED", "arm2": "VERIFIED", "arm3": "VERIFIED",
              "arm4": "VERIFIED", "arm5": "VERIFIED"}

    prompt_arm1 = "add one short comment to the backend README and stop"

    # ---- arm 2 determinism inputs (shared with arm 1 repeats) ----
    digests_stable: dict[str, list[str]] = {}

    for repeat in range(REPEATS):
        # arm 1: real delegated run, digest reproduced out of band
        task_id = f"T111-A1-R{repeat}"
        observation, outcome = delegate(stage, home, task_id=task_id,
                                        prompt=prompt_arm1, harness=harness)
        record: dict[str, object] = {"arm": 1, "repeat": repeat,
                                     "delegate": observation}
        if observation["exit_code"] != 0:
            status["arm1"] = "GAP"
            trials.append(record)
            continue
        payload = json.loads(outcome.read_bytes())
        logs_dir = outcome.with_name(outcome.name + ".logs")
        manifest = json.loads((logs_dir / "manifest.json").read_bytes())
        measured = sha256sum_file(home, logs_dir / "instruction.log")
        record["instruction_digest"] = payload["instruction_digest"]
        record["manifest_instruction_digest"] = manifest.get("instruction_digest")
        record["sha256sum_instruction_log"] = measured
        record["verdict"] = (
            payload["instruction_digest"]
            == manifest.get("instruction_digest")
            == "sha256:" + measured
            == "sha256:" + hashlib.sha256(
                instruction_bytes(prompt_arm1)
            ).hexdigest()
        )
        if not record["verdict"]:
            status["arm1"] = "FALSE-PASS" if observation["exit_code"] == 0 else "GAP"
        digests_stable.setdefault("same", []).append(
            str(payload["instruction_digest"]))
        trials.append(record)

    # arm 2: changed word -> different digest (1 run), same prompt already 3x
    changed_prompt = "add one long comment to the backend README and stop"
    observation, outcome = delegate(stage, home, task_id="T111-A2-CHANGED",
                                    prompt=changed_prompt, harness=harness)
    payload = json.loads(outcome.read_bytes())
    changed_digest = str(payload["instruction_digest"])
    same_digests = digests_stable["same"]
    if len(set(same_digests)) != 1:
        status["arm2"] = "NON-DETERMINISTIC"
    if changed_digest == same_digests[0]:
        status["arm2"] = "GAP"
    trials.append({
        "arm": 2,
        "delegate": observation,
        "same_prompt_digests": same_digests,
        "changed_prompt_digest": changed_digest,
        "changed_differs": changed_digest != same_digests[0],
    })

    # arm 3: negative control — silent drop refused by manifest digest check
    for repeat in range(REPEATS):
        task_id = f"T111-A3-R{repeat}"
        observation, outcome = delegate(stage, home, task_id=task_id,
                                        prompt="do the auditable thing",
                                        harness=harness)
        logs_dir = outcome.with_name(outcome.name + ".logs")
        manifest = json.loads((logs_dir / "manifest.json").read_bytes())
        checklist = logs_dir / "manifest.sha256sums"
        checklist.write_text(
            "\n".join(
                f"{entry['sha256'].removeprefix('sha256:')}  {entry['file']}"
                for entry in manifest["streams"].values()
            ) + "\n",
            encoding="utf-8",
        )
        intact = subprocess.run(
            ["sha256sum", "-c", "--strict", str(checklist)],
            cwd=str(logs_dir), capture_output=True, text=True, check=False,
            env=clean_env(home),
        )
        (logs_dir / "instruction.log").unlink()
        dropped = subprocess.run(
            ["sha256sum", "-c", "--strict", str(checklist)],
            cwd=str(logs_dir), capture_output=True, text=True, check=False,
            env=clean_env(home),
        )
        verdict = (
            observation["exit_code"] == 0
            and intact.returncode == 0
            and dropped.returncode != 0
            and "instruction.log" in dropped.stdout
        )
        if not verdict:
            status["arm3"] = "GAP"
        trials.append({
            "arm": 3, "repeat": repeat, "delegate": observation,
            "intact_check_exit": intact.returncode,
            "dropped_check_exit": dropped.returncode,
            "dropped_stdout_tail": dropped.stdout[-500:],
            "verdict": verdict,
        })

    # arm 4: redaction holds; digest covers the unredacted bytes
    password = "RANEX111AUDITPW0123456789abcdef"
    redact_prompt = f"pull using https://ci:{password}@registry.invalid/wheels and stop"
    for repeat in range(REPEATS):
        task_id = f"T111-A4-R{repeat}"
        observation, outcome = delegate(stage, home, task_id=task_id,
                                        prompt=redact_prompt, harness=harness)
        payload = json.loads(outcome.read_bytes())
        logs_dir = outcome.with_name(outcome.name + ".logs")
        retained = (logs_dir / "instruction.log").read_text(encoding="utf-8")
        unredacted = stage / f"unredacted-{task_id}.json"
        unredacted.write_bytes(instruction_bytes(redact_prompt))
        measured = sha256sum_file(home, unredacted)
        verdict = (
            observation["exit_code"] == 0
            and password not in retained
            and "[REDACTED:credential]" in retained
            and payload["instruction_digest"] == "sha256:" + measured
        )
        if not verdict:
            status["arm4"] = "GAP"
        trials.append({
            "arm": 4, "repeat": repeat, "delegate": observation,
            "instruction_digest": payload["instruction_digest"],
            "sha256sum_unredacted_bytes": measured,
            "redaction_marker_present": "[REDACTED:credential]" in retained,
            "secret_absent": password not in retained,
            "verdict": verdict,
        })

    # arm 5: fanout — two concurrent different prompts, isolated digests
    for repeat in range(REPEATS):
        fanout_dir = stage / f"fanout-R{repeat}"
        fanout_dir.mkdir()
        tasks = fanout_dir / "tasks.jsonl"
        prompts = {
            "T111-A5-ONE": "describe the backend in one sentence",
            "T111-A5-TWO": "describe the frontend in one sentence",
        }
        tasks.write_text(
            "\n".join(
                json.dumps({
                    "task_id": task_id, "prompt": prompt,
                    "worktree": str(fanout_dir / f"worktree-{task_id}"),
                })
                for task_id, prompt in prompts.items()
            ) + "\n",
            encoding="utf-8",
        )
        argv = [
            RANEX, "task", "fanout",
            "--tasks", str(tasks),
            "--target", str(stage / "subject"),
            "--journal", str(fanout_dir / "journal.sqlite3"),
            "--harness", str(harness),
            "--model", "ranex-noop/noop",
            "--timeout", "120",
            "--suite", "/usr/bin/true",
            "--outcome-dir", str(fanout_dir / "outcomes"),
            "--pool", "2",
        ]
        observation = run(argv, cwd=fanout_dir, env=clean_env(home))
        observed_digests = {}
        matches_own = True
        for task_id, prompt in prompts.items():
            outcome = fanout_dir / "outcomes" / f"{task_id}.json"
            payload = json.loads(outcome.read_bytes())
            logs_dir = outcome.with_name(outcome.name + ".logs")
            measured = sha256sum_file(home, logs_dir / "instruction.log")
            observed_digests[task_id] = payload["instruction_digest"]
            if payload["instruction_digest"] != "sha256:" + measured:
                matches_own = False
            if payload["instruction_digest"] != "sha256:" + hashlib.sha256(
                instruction_bytes(prompt)
            ).hexdigest():
                matches_own = False
        verdict = (
            observation["exit_code"] == 0
            and matches_own
            and observed_digests["T111-A5-ONE"] != observed_digests["T111-A5-TWO"]
        )
        if not verdict:
            status["arm5"] = "GAP"
        trials.append({
            "arm": 5, "repeat": repeat, "fanout": observation,
            "digests": observed_digests, "verdict": verdict,
        })

    receipts["trials"] = trials
    receipts["status"] = status
    receipts["limitations"] = [
        "Worker harness is a real shell worker, not a live LLM: the kernel's "
        "child environment deliberately carries no model credential, so no "
        "live model was driven; the digest names exactly the bytes handed to "
        "the real worker process, which is the property under test.",
        "Suite bound to the delegate run is /usr/bin/true; the arms test the "
        "instruction record, not the subject's own test suite.",
        "Manifest digest check exercised through sha256sum(1) over the "
        "manifest's per-stream digests (the established ADR-043 checking "
        "discipline); no product logs-verify CLI exists or was added.",
    ]
    receipt_path = stage / "receipt.json"
    receipt_path.write_text(json.dumps(receipts, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=1))
    overall = "PASS" if all(v == "VERIFIED" for v in status.values()) else "FAIL"
    print("OVERALL:", overall)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
