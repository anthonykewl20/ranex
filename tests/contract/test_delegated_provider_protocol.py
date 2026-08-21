"""Freeze ADR-033's protocol artifact before SLICE-069 implementation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json"
EXPECTED_SHA256 = "c37e4fd270b78f1a0f6070cfe757a9f463ae68147081a0037425201de7ea7db4"
EXPECTED_VECTOR_IDS = (
    "handshake-ok",
    "handshake-replay",
    "chat-first-request",
    "chat-replay",
    "chat-distinct-second-request",
    "unsupported-version",
)
EXPECTED_PROTOCOL_KEYS = {
    "name",
    "version",
    "bind",
    "handshake",
    "chat",
    "stream",
    "ttlSeconds",
    "maxRequests",
    "maxConcurrency",
    "maxRequestBytes",
    "maxResponseBytes",
    "timeoutSeconds",
    "upstream",
    "redirects",
    "retry",
    "persistence",
    "handshakeAccounting",
    "handshakeUse",
    "chatReplayKey",
    "maxRequestsScope",
    "distinctRequestIds",
    "requestId",
    "ttlAccounting",
    "chatTimeout",
    "timeoutScope",
    "requestBytes",
    "responseBytes",
    "oversizeStream",
    "transport",
    "policy",
    "outcome",
    "logging",
    "fixture",
}
CAPABILITY_PATTERN = r"[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]"
ERRORS = {
    "invalid_protocol", "unsupported_version", "unauthorized", "handshake_required",
    "session_mismatch", "replay", "expired", "model_not_allowed", "provider_not_allowed",
    "invalid_request", "tool_not_allowed", "request_too_large", "response_too_large",
    "concurrency_limit", "request_limit", "upstream_timeout", "upstream_http",
    "redirect_refused", "upstream_protocol", "server_shutdown", "internal",
}


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def test_delegated_provider_protocol_freeze() -> None:
    raw = ARTIFACT.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    artifact = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)

    assert artifact["$id"] == "https://ranex.dev/governance/schemas/delegated-provider/ranex-delegated-provider-v1.json"
    protocol = artifact["protocol"]
    assert set(protocol) == EXPECTED_PROTOCOL_KEYS
    assert protocol["name"] == "ranex-delegated-provider"
    assert protocol["version"] == 1
    assert protocol["ttlSeconds"] == 300
    assert protocol["maxRequests"] == 8
    assert protocol["maxConcurrency"] == 1
    assert protocol["maxRequestBytes"] == 4 * 1024 * 1024
    assert protocol["maxResponseBytes"] == 16 * 1024 * 1024
    assert protocol["timeoutSeconds"] == 120
    assert protocol["upstream"] == "https://openrouter.ai/api/v1/chat/completions"
    assert protocol["redirects"] == "refuse"
    assert protocol["retry"] == "none"
    assert protocol["persistence"] == "none"
    assert protocol["handshakeAccounting"] == "uncounted"
    assert protocol["handshakeUse"] == "single-use-per-capability-session"
    assert protocol["chatReplayKey"] == ["session", "requestId"]
    assert protocol["requestId"] == {"encoding": "base64url", "randomBytes": 16, "length": 22, "finalCharacters": "AQgw"}
    assert protocol["ttlAccounting"] == "session-wall-clock"
    assert protocol["chatTimeout"] == "min(120s, remaining session TTL)"
    assert protocol["timeoutScope"] == "whole request/stream"
    assert protocol["maxRequestsScope"] == "chat only"
    assert protocol["distinctRequestIds"] == "up to 8 per session"
    assert protocol["requestBytes"] == "raw HTTP request body"
    assert protocol["responseBytes"] == "cumulative SSE bytes"
    assert protocol["oversizeStream"] == "close streams, record response_too_large, omit [DONE], harness reports upstream_protocol"
    assert protocol["transport"] == {
        "capability": "inherited FD/pipe at spawn only",
        "prohibited": ["argv", "environment", "files", "logs"],
        "harnessStorage": "bounded in-memory only",
        "brokerTransport": "direct TLS via stdlib",
        "proxyEnvironment": "ignored",
        "redirects": "refuse",
    }
    assert protocol["policy"]["modelSource"] == "kernel task grant"
    assert protocol["policy"]["handshakeModel"] == "binds session"
    assert protocol["policy"]["chatModel"] == "must equal handshake model"
    assert protocol["policy"]["handshakeTools"] == "allowed function names"
    assert protocol["policy"]["chatTools"] == "function.name set must be subset of handshake tools"
    assert protocol["policy"]["default"] == "deny"
    assert protocol["policy"]["hostedProviderTools"] == "refuse"
    assert protocol["outcome"] == "provider_attempt"
    assert protocol["fixture"] == {
        "path": "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json",
        "harness": "vendor exact JSON fixture",
        "sha256": "authoritative contract-test pin",
    }
    assert protocol["logging"] == {
        "events": ["cli.task.delegate.start", "cli.task.delegate.end"],
        "format": "JSONL",
        "time": "UTC",
        "fields": ["correlation", "outcome", "duration"],
        "broker": "no independent logs",
        "secrets": "no session/auth headers/raw prompts",
    }

    schemas = artifact["schemas"]
    assert "requestId" in schemas["chatRequest"]["required"]
    assert schemas["handshakeResponse"]["required"][-1] == "remainingRequests"
    assert set(schemas["error"]["properties"]["error"]["enum"]) == ERRORS
    assert artifact["$defs"]["capability"]["pattern"] == f"^{CAPABILITY_PATTERN}$"
    assert artifact["$defs"]["requestId"]["pattern"] == "^[A-Za-z0-9_-]{21}[AQgw]$"
    assert artifact["vectorSemantics"] == {
        "ordering": "explicit",
        "independence": "each vector is evaluated from its declared state; replay vectors reuse only their declared key",
    }

    vectors = artifact["vectors"]
    assert tuple(vector["id"] for vector in vectors) == EXPECTED_VECTOR_IDS
    assert vectors[0]["response"]["remainingRequests"] == 8
    assert vectors[2]["response"]["remainingRequests"] == 7
    assert vectors[4]["response"]["remainingRequests"] == 6
    assert vectors[1]["response"]["error"] == "replay"
    assert vectors[3]["response"]["error"] == "replay"
    assert vectors[2]["request"]["requestId"] == vectors[3]["request"]["requestId"]
    assert vectors[2]["request"]["requestId"] != vectors[4]["request"]["requestId"]
    assert all(re.fullmatch(CAPABILITY_PATTERN, vector["request"]["capability"]) for vector in vectors)
    assert re.fullmatch(r"[A-Za-z0-9_-]{21}[AQgw]", vectors[2]["request"]["requestId"])
    assert re.fullmatch(r"[A-Za-z0-9_-]{21}[AQgw]", vectors[4]["request"]["requestId"])
    assert set(vectors[2]["request"]["tools"][0]) == {"type", "function"}
    assert vectors[2]["request"]["tools"][0]["function"]["name"] == "weather"
    with pytest.raises(AssertionError, match="duplicate JSON key"):
        json.loads('{"protocol": "one", "protocol": "two"}', object_pairs_hook=_reject_duplicate_keys)
