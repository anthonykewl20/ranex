"""SLICE-054 — the trace secret-scrubbing attack suite, frozen red first.

ADR-031's disclosure guarantee: under hostile input no key byte, credential
URL, or evidence byte may appear in any trace line or operator diagnostic.
The allowlist plus the shape-descriptor refusal split is the control; this
suite is the attack that proves it. Secrets are planted for real — Ed25519 PEM
key material from the project's own keygen, bearer tokens, credential-URL env
vars — ambient, embedded in RANEX_TRACE values, and inside rogue emit_raw
payloads with hostile field names and values. Every planted marker (and each
bare token core) is then searched for, grep -F semantics, across every
captured trace file and both captured streams: zero hits.

The rogue emissions run in a real subprocess because the emitter reads its
environment exactly once at import; the subprocess also models the actual
threat — an emission site the attacker influenced. The trace-must-exist
assertions are the red lever: against the pre-implementation tree there is no
emitter, so this file fails rather than passing vacuously.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

import ranex.observability  # noqa: F401 — the module's existence is the contract

PROJECT = Path(__file__).resolve().parents[2]

ROGUE_ATTACK = """
import os
import sys

sys.path.insert(0, __SRC__)
import ranex.observability as observability

pem = os.environ["ATTACK_PEM"]
token = os.environ["ATTACK_TOKEN"]
url = os.environ["ATTACK_URL"]
evidence = os.environ["ATTACK_EVIDENCE"]

observability.emit_raw(
    {
        "event": "note",
        "level": "info",
        "module": "observability",
        "stage": "observability.note",
        pem: pem,
        "z" * 300: token,
        "subject_digest": url,
        "code": "exit:" + token,
        "exe": evidence,
        "duration_us": {"nested": token},
    }
)
observability.stage_begin("cli.keygen.start")
observability.stage_end("cli.keygen.end", "exit:0")
"""

AMBIENT_ATTACK = """
import os
import sys

sys.path.insert(0, __SRC__)
import ranex.observability as observability

observability.emit_raw(
    {
        "event": "note",
        "level": "warn",
        "module": "observability",
        "stage": "observability.note",
        "code": "emission_refused",
    }
)
"""


def _planted_secrets(tmp_path: Path) -> dict[str, str]:
    from ranex.foundation.signing import generate_keypair

    private, _public = generate_keypair()
    nonce = secrets.token_hex(16)
    return {
        "ATTACK_PEM": private,
        "ATTACK_TOKEN": f"rnxs-bearer-{nonce}",
        "ATTACK_URL": f"https://ci:RANEXCREDURLPW{nonce}@registry.invalid/wheels",
        "ATTACK_EVIDENCE": f'{{"claim_id": "tests-executed", "api_key": "rnxs-evidence-{nonce}"}}',
    }


def _markers(planted: dict[str, str]) -> list[str]:
    url = planted["ATTACK_URL"]
    evidence = planted["ATTACK_EVIDENCE"]
    markers = [
        planted["ATTACK_TOKEN"],
        url,
        "RANEXCREDURLPW",
        "rnxs-evidence-",
        evidence,
        "-----BEGIN PRIVATE KEY-----",
        "-----END PRIVATE KEY-----",
    ]
    markers.extend(line for line in planted["ATTACK_PEM"].splitlines() if line.strip())
    return markers


def _run_attack(
    tmp_path: Path, script: str, planted: dict[str, str], target_env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(PROJECT / "src"),
            **planted,
            **target_env,
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _assert_zero_hits(
    markers: list[str], completed: subprocess.CompletedProcess[str], *files: Path
) -> None:
    haystacks = [completed.stdout, completed.stderr]
    haystacks.extend(path.read_text(encoding="utf-8") for path in files if path.exists())
    for marker in markers:
        for haystack in haystacks:
            assert marker not in haystack, (
                f"planted secret {marker!r} survived into trace output"
            )


def test_planted_secrets_in_rogue_emissions_never_reach_trace_output(
    tmp_path: Path,
) -> None:
    planted = _planted_secrets(tmp_path)
    target = tmp_path / "trace.jsonl"
    script = ROGUE_ATTACK.replace("__SRC__", repr(str(PROJECT / "src")))
    completed = _run_attack(
        tmp_path,
        script,
        planted,
        {
            # One valid target so events exist, plus a hostile relative value
            # carrying secret bytes on the second variable.
            "RANEX_TRACE": str(target),
            "RANEX_TRACE_EVENT": f"relative-{planted['ATTACK_TOKEN']}/trace.jsonl",
        },
    )

    assert target.exists(), "the on-arm must actually be tracing"
    events = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert events[0]["event"] == "version"
    assert any(event["event"] == "refusal" for event in events), (
        "the rogue payload must be refused, not silently swallowed"
    )

    _assert_zero_hits(_markers(planted), completed, target)
    warnings = [line for line in completed.stderr.splitlines() if "RANEX_TRACE" in line]
    assert warnings, "the invalid second target must warn"
    assert all("len=" in line and "sha256_8=" in line for line in warnings)


def test_planted_secrets_in_ambient_target_values_never_reach_diagnostics(
    tmp_path: Path,
) -> None:
    planted = _planted_secrets(tmp_path)
    target = tmp_path / "trace.jsonl"
    script = AMBIENT_ATTACK.replace("__SRC__", repr(str(PROJECT / "src")))
    completed = _run_attack(
        tmp_path,
        script,
        planted,
        {
            # A socket-form target value embedding a credential URL: refused
            # outright, diagnosed by shape, never by bytes.
            "RANEX_TRACE": f"af_unix:[{planted['ATTACK_URL']}]",
            "RANEX_TRACE_EVENT": str(target),
            "WHEELS_INDEX_URL": planted["ATTACK_URL"],
        },
    )

    assert target.exists(), "the valid target must carry the stream"
    events = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert events[0]["event"] == "version"
    assert events[-1]["event"] == "note"

    _assert_zero_hits(_markers(planted), completed, target)
    warnings = [line for line in completed.stderr.splitlines() if "RANEX_TRACE" in line]
    assert len(warnings) == 1
    assert "len=" in warnings[0] and "sha256_8=" in warnings[0]
