"""Real-CLI attack coverage for retained delegated-execution log redaction."""

from __future__ import annotations

import json
import os
import secrets
import shlex
import shutil
import subprocess
import sys
from base64 import b64decode
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ranex.foundation.signing import generate_keypair

PROJECT = Path(__file__).resolve().parents[2]
CLI_SOURCE = PROJECT / "src" / "ranex"
SENTINEL = "RANEX_LOG_SCRUBBING_OPERATOR_SENTINEL"


def _planted_secrets() -> dict[str, str]:
    private, _public = generate_keypair()
    raw_private = b64decode(private.removeprefix("ed25519:"), validate=True)
    pem = Ed25519PrivateKey.from_private_bytes(raw_private).private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    nonce = secrets.token_hex(16)
    token = f"rnxs-bearer-{nonce}"
    return {
        "token": token,
        "url": f"https://ci:RANEXCREDURLPW{nonce}@registry.invalid/wheels",
        "pem": pem,
        "evidence": json.dumps(
            {"claim_id": "tests-executed", "bearer": token},
            separators=(",", ":"),
        ),
        "odd": f"rnxs-odd-redaction-{nonce}",
    }


def _markers(planted: dict[str, str]) -> list[str]:
    markers = [
        planted["token"],
        planted["url"],
        "RANEXCREDURLPW",
        "-----BEGIN PRIVATE KEY-----",
        planted["evidence"],
        planted["odd"],
    ]
    markers.extend(line for line in planted["pem"].splitlines() if line.strip())
    return markers


def _environment(*, home: Path, python_path: Path, planted: dict[str, str]) -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(python_path),
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if not planted:
        return environment
    environment.update(
        {
            # The delegate process collects this grammar-matching secret before it
            # constructs the harness's deliberately minimal child environment.
            "OPENROUTER_API_KEY": planted["token"],
            # This name deliberately does not match the automatic sensitive-name
            # grammar: the URL's password must therefore exercise structural URL
            # redaction, rather than a whole-value environment replacement.
            "PLANT_RNX_SUPPLY": planted["url"],
            "PLANT_ODD_NAME": planted["odd"],
        }
    )
    return environment


def _build_target(tmp_path: Path) -> Path:
    target = tmp_path / "target"
    home = tmp_path / "git-home"
    target.mkdir()
    home.mkdir()
    environment = _environment(home=home, python_path=home, planted={})
    subprocess.run(["git", "init", "-q", str(target)], check=True, env=environment)
    for key, value in (
        ("user.email", "delegate-log-scrubbing@example.invalid"),
        ("user.name", "Delegate log scrubbing"),
    ):
        subprocess.run(
            ["git", "-C", str(target), "config", key, value],
            check=True,
            env=environment,
        )
    shutil.copytree(CLI_SOURCE, target / "src" / "ranex")
    (target / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(target), "add", "-A"], check=True, env=environment)
    subprocess.run(
        ["git", "-C", str(target), "commit", "-q", "-m", "initial target"],
        check=True,
        env=environment,
    )
    return target


def _leaking_harness(path: Path, planted: dict[str, str]) -> Path:
    values = "\n".join(
        f"{name}={shlex.quote(value)}"
        for name, value in (
            ("TOKEN", planted["token"]),
            ("URL", planted["url"]),
            ("PEM", planted["pem"]),
            ("EVIDENCE", planted["evidence"]),
            ("ODD", planted["odd"]),
        )
    )
    path.write_text(
        f"""#!/usr/bin/env sh
set -eu

{values}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir)
      WORKTREE="$2"
      shift 2
      ;;
    --model|--auto)
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

for value in "$TOKEN" "$URL" "$PEM" "$EVIDENCE" "$ODD"; do
  printf '%s\\n' "$value"
  printf '%s\\n' "$value" >&2
done
printf '%s\\n' {shlex.quote(SENTINEL)}
printf '%s\\n' {shlex.quote(SENTINEL)} >&2

printf 'delegated work\\n' > "$WORKTREE/agent.txt"
git -C "$WORKTREE" -c user.email=harness@example.invalid \\
  -c user.name=Harness add -A
git -C "$WORKTREE" -c user.email=harness@example.invalid \\
  -c user.name=Harness commit -q -m "agent work"
commit=$(git -C "$WORKTREE" rev-parse HEAD)
printf '{{"task_id":"%s","worktree":"%s","commit":"%s"}}\\n' \\
  "$RANEX_TASK_ID" "$WORKTREE" "$commit" > "$RANEX_EMIT"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _run_attack(
    tmp_path: Path,
    target: Path,
    harness: Path,
    planted: dict[str, str],
    *,
    redact_env: str,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    outcome = tmp_path / "outcome.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ranex.cli.main",
            "task",
            "delegate",
            "--task-id",
            "T-058-REDACTION",
            "--target",
            str(target),
            "--worktree",
            str(tmp_path / "worktree"),
            "--journal",
            str(tmp_path / "task-journal.sqlite3"),
            "--harness",
            str(harness),
            "--model",
            "ranex-noop/noop",
            "--prompt",
            "run the leaking harness",
            "--timeout",
            "120",
            "--suite",
            "/usr/bin/true",
            "--outcome",
            str(outcome),
            "--redact-env",
            redact_env,
        ],
        cwd=target,
        env=_environment(
            home=tmp_path / "delegate-home",
            python_path=target / "src",
            planted=planted,
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return completed, outcome


def _assert_zero_hits(
    markers: list[str], completed: subprocess.CompletedProcess[str], *haystacks: bytes
) -> None:
    outputs = (completed.stdout.encode(), completed.stderr.encode(), *haystacks)
    for marker in markers:
        for haystack in outputs:
            assert marker.encode() not in haystack, (
                f"planted secret {marker!r} survived into delegate output"
            )


def test_delegate_retains_only_redacted_logs_from_a_worst_case_leaking_harness(
    tmp_path: Path,
) -> None:
    planted = _planted_secrets()
    target = _build_target(tmp_path)
    harness = _leaking_harness(tmp_path / "leaking-harness.sh", planted)

    completed, outcome = _run_attack(
        tmp_path,
        target,
        harness,
        planted,
        redact_env="PLANT_ODD_NAME",
    )

    log_dir = outcome.with_name(outcome.name + ".logs")
    harness_stdout = log_dir / "harness.stdout.log"
    harness_stderr = log_dir / "harness.stderr.log"
    suite_stdout = log_dir / "suite.stdout.log"
    suite_stderr = log_dir / "suite.stderr.log"
    manifest = log_dir / "manifest.json"
    assert outcome.exists(), "the real delegate must write its outcome"
    assert harness_stdout.exists(), "the real delegate must retain harness stdout"
    assert harness_stderr.exists(), "the real delegate must retain harness stderr"
    assert suite_stdout.exists(), "the real delegate must retain suite stdout"
    assert suite_stderr.exists(), "the real delegate must retain suite stderr"
    assert manifest.exists(), "the real delegate must retain the log manifest"
    assert completed.returncode == 0, completed.stderr

    sidecar = b"".join(path.read_bytes() for path in sorted(log_dir.iterdir()))
    _assert_zero_hits(_markers(planted), completed, outcome.read_bytes(), sidecar)

    retained_stdout = harness_stdout.read_text(encoding="utf-8")
    assert "[REDACTED:env:OPENROUTER_API_KEY]" in retained_stdout
    assert "[REDACTED:pem]" in retained_stdout
    assert "[REDACTED:credential]" in retained_stdout
    assert "[REDACTED:env:PLANT_ODD_NAME]" in retained_stdout
    assert SENTINEL in retained_stdout

    redactions = json.loads(manifest.read_text(encoding="utf-8"))["streams"]["harness.stdout"][
        "redactions"
    ]
    for kind in ("env:OPENROUTER_API_KEY", "pem", "credential", "env:PLANT_ODD_NAME"):
        assert redactions[kind] >= 1


def test_delegate_refuses_invalid_forced_redaction_environment_names(tmp_path: Path) -> None:
    target = _build_target(tmp_path)
    base = [
        sys.executable,
        "-m",
        "ranex.cli.main",
        "task",
        "delegate",
        "--task-id",
        "T-058-REFUSAL",
        "--target",
        str(target),
        "--worktree",
        str(tmp_path / "worktree"),
        "--journal",
        str(tmp_path / "task-journal.sqlite3"),
        "--harness",
        str(tmp_path / "not-needed.sh"),
        "--model",
        "ranex-noop/noop",
        "--prompt",
        "unused",
        "--timeout",
        "120",
        "--suite",
        "/usr/bin/true",
        "--outcome",
        str(tmp_path / "outcome.json"),
        "--redact-env",
    ]
    environment = _environment(
        home=tmp_path / "delegate-home",
        python_path=target / "src",
        planted={},
    )
    environment["PLANT_SHORT_NAME"] = "short"

    short = subprocess.run(
        [*base, "PLANT_SHORT_NAME"],
        cwd=target,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    missing = subprocess.run(
        [*base, "PLANT_MISSING_NAME"],
        cwd=target,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    assert short.returncode != 0
    assert short.stderr.strip() == (
        "ERROR  refusing --redact-env PLANT_SHORT_NAME: "
        "value shorter than the 16-byte redaction floor"
    )
    assert missing.returncode != 0
    assert missing.stderr.strip() == (
        "ERROR  refusing --redact-env PLANT_MISSING_NAME: not set in the environment"
    )
