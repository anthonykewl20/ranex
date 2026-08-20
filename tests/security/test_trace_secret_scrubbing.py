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

import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

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

# S4 (remediation strengthening): genuinely exercise the ambient credential
# URL — read it out of the environment a wholesale ambient copy would hand an
# observed command, and attempt to emit it through both a declared field
# (`code`) and an undeclared one. This emission is hostile; it must leave only
# refusals. Emitted BEFORE the well-formed note so the note stays the last
# line of the stream.
url = os.environ.get("WHEELS_INDEX_URL", "absent")
if url != "absent":
    observability.emit_raw(
        {
            "event": "note",
            "level": "warn",
            "module": "observability",
            "stage": "observability.note",
            "code": url,
            "wheels_index_url": url,
        }
    )

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

CODE_TOKEN_ATTACK = """
import os
import sys

sys.path.insert(0, __SRC__)
import ranex.observability as observability

# D3: an otherwise well-formed event whose only violation is the `code` value.
# Both spellings below are grammar-valid against the open kind/arg grammar —
# the exact shape the closed code registry must refuse.
observability.emit_raw(
    {
        "event": "note",
        "level": "info",
        "module": "observability",
        "stage": "observability.note",
        "code": __CODE__,
    }
)
"""

CODE_ARGUMENT_ATTACK = """
import os
import sys

sys.path.insert(0, __SRC__)
import ranex.observability as observability

# N1 (round 2): the planted token rides the ARGUMENT of a REGISTERED kind in
# otherwise perfectly well-formed events — the exact leak the per-kind
# structural argument forms must close. No other violation exists in these
# payloads.
token = os.environ["ATTACK_TOKEN"]
for code in (
    "out_of_form:code:" + token,
    "out_of_form:" + token,
    "undeclared_field:" + token,
    "malformed_parent_sid:" + token,
    "oversized_event:" + token,
    "cap_exceeded:" + token,
):
    observability.emit_raw(
        {
            "event": "note",
            "level": "info",
            "module": "observability",
            "stage": "observability.note",
            "code": code,
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

    # S4: the ambient credential URL genuinely flowed through the emission
    # surface — the attempt is recorded as refusals, never as bytes.
    codes = [event["code"] for event in events if event["event"] == "refusal"]
    assert "undeclared_field:wheels_index_url" in codes, codes
    assert any(code.startswith("out_of_form:code:") for code in codes), codes

    _assert_zero_hits(_markers(planted), completed, target)
    warnings = [line for line in completed.stderr.splitlines() if "RANEX_TRACE" in line]
    assert len(warnings) == 1
    assert "len=" in warnings[0] and "sha256_8=" in warnings[0]


# --- remediation arms (D3: the `code` field leaks grammar-shaped secrets) ----
#
# The ROGUE_ATTACK payload hides its code token behind a subject_digest
# violation, so the code leak was masked. These arms carry NO other violation:
# the only hostile element is the `code` value, and it must still never reach
# any stream.


def _run_code_attack(
    tmp_path: Path, code_literal: str, planted: dict[str, str]
) -> tuple[subprocess.CompletedProcess[str], Path]:
    target = tmp_path / "trace.jsonl"
    script = (
        CODE_TOKEN_ATTACK.replace("__SRC__", repr(str(PROJECT / "src")))
        .replace("__CODE__", code_literal)
    )
    completed = _run_attack(
        tmp_path, script, planted, {"RANEX_TRACE": str(target)}
    )
    return completed, target


def test_bearer_token_behind_a_legitimate_code_kind_never_reaches_trace_output(
    tmp_path: Path,
) -> None:
    """D3 — `exit:<bearer token>` is grammar-valid today and serializes verbatim.

    The arg charset admits hyphens and hex, so a bearer token rides the
    `exit:` kind — a legitimate frozen kind — straight into the stream. The
    closed code registry must refuse it (shape+digest only); the payload is
    otherwise perfectly well-formed, so nothing but the refusal may flow.
    """

    planted = _planted_secrets(tmp_path)
    token = planted["ATTACK_TOKEN"]
    completed, target = _run_code_attack(tmp_path, f'"exit:" + {token!r}', planted)

    assert target.exists(), "the on-arm must actually be tracing"
    text = target.read_text(encoding="utf-8")
    events = [json.loads(line) for line in text.splitlines() if line]
    assert events[0]["event"] == "version"
    assert token not in text, "the bearer token reached the trace stream via code"
    codes = [event["code"] for event in events if event["event"] == "refusal"]
    assert any(code.startswith("out_of_form:code:") for code in codes), codes

    _assert_zero_hits(_markers(planted), completed, target)


def test_hex_token_as_a_bare_code_kind_never_reaches_trace_output(
    tmp_path: Path,
) -> None:
    """D3 — a bare 64-hex token matches the open kind grammar and serializes
    verbatim; the closed registry must refuse it (shape+digest only)."""

    planted = _planted_secrets(tmp_path)
    token = planted["ATTACK_TOKEN"]
    # 64 lowercase hex, deterministically letter-first so the bare-kind
    # grammar ([a-z_][a-z0-9_]*) always admits it — a digest starting with a
    # digit would be out-of-form today for accidental reasons.
    hex_token = "de" + hashlib.sha256(token.encode("utf-8")).hexdigest()[2:]
    assert len(hex_token) == 64 and hex_token[0] in "abcdef"
    completed, target = _run_code_attack(tmp_path, repr(hex_token), planted)

    assert target.exists(), "the on-arm must actually be tracing"
    text = target.read_text(encoding="utf-8")
    events = [json.loads(line) for line in text.splitlines() if line]
    assert events[0]["event"] == "version"
    assert hex_token not in text, "the hex token reached the trace stream via code"
    codes = [event["code"] for event in events if event["event"] == "refusal"]
    assert any(code.startswith("out_of_form:code:") for code in codes), codes

    _assert_zero_hits(_markers(planted), completed, target)


def test_registered_kind_arguments_never_leak_planted_tokens(
    tmp_path: Path,
) -> None:
    """N1 — the bearer token as the ARGUMENT of a registered kind, in
    otherwise well-formed events. The generic argument charset admits the
    token behind every registered kind today (`out_of_form:code:<token>`,
    `undeclared_field:<token>`, `malformed_parent_sid:<token>`,
    `oversized_event:<token>`, even `cap_exceeded:<token>`); each must be
    refused with the value represented by shape plus digest, and grep -F must
    find ZERO hits of the token in every captured stream."""

    planted = _planted_secrets(tmp_path)
    target = tmp_path / "trace.jsonl"
    script = CODE_ARGUMENT_ATTACK.replace("__SRC__", repr(str(PROJECT / "src")))
    completed = _run_attack(
        tmp_path, script, planted, {"RANEX_TRACE": str(target)}
    )

    assert target.exists(), "the on-arm must actually be tracing"
    text = target.read_text(encoding="utf-8")
    events = [json.loads(line) for line in text.splitlines() if line]
    assert events[0]["event"] == "version"
    assert planted["ATTACK_TOKEN"] not in text, (
        "the bearer token reached the trace stream as a code argument"
    )
    codes = [event["code"] for event in events if event["event"] == "refusal"]
    assert len(codes) >= 6, codes
    assert all(code.startswith("out_of_form:code:") for code in codes), codes
    assert all(re.search(r"sha256_8=[0-9a-f]{8}", code) for code in codes)

    _assert_zero_hits(_markers(planted), completed, target)
