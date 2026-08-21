"""Freeze ADR-033's protocol artifact before SLICE-069 implementation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json"
EXPECTED_SHA256 = "8aa6cc646f7c4ca331c729b2a691bfde1ac5d506fdeab3b94c492bef27f162ea"
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
    "chatAccounting",
    "transport",
    "policy",
    "outcome",
    "schemaValidation",
    "validation",
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
    assert protocol["oversizeStream"] == "close streams, broker records response_too_large, omit [DONE], harness may report local upstream_protocol only"
    assert protocol["chatAccounting"] == {
        "remainingRequests": "broker session state returned by handshake only; never carried in relayed SSE",
        "decrement": "one successful distinct chat requestId consumes one request",
        "replay": "replayed requestId consumes no additional request",
    }
    assert protocol["transport"] == {
        "capability": "inherited file descriptor 3 (pipe) at spawn only",
        "prohibited": ["argv", "environment", "files", "logs"],
        "harnessStorage": "bounded in-memory only",
        "brokerTransport": "direct TLS through a verified HTTP stack",
        "httpStack": "stdlib HTTP stack with standard TLS verification; no custom TLS or SSE replacement",
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
    assert protocol["schemaValidation"] == (
        "schema block is structural validation only; authoritative provider/model/tool "
        "enforcement and error ordering are in validation+policy and MUST run before upstream"
    )
    assert protocol["validation"] == {
        "precedence": [
            "request_too_large", "invalid_protocol", "unsupported_version", "unauthorized",
            "handshake_required", "session_mismatch", "replay", "expired",
            "provider_not_allowed", "model_not_allowed", "tool_not_allowed", "invalid_request",
            "concurrency_limit", "request_limit", "upstream",
        ],
        "fieldErrors": {
            "capability": "unauthorized",
            "session": "unauthorized",
            "requestId": {
                "replay": "replay",
                "structural": "invalid_request",
            },
            "provider": "provider_not_allowed",
            "model": "model_not_allowed",
            "tools": "tool_not_allowed",
            "structuralFields": ["protocol", "messages", "stream", "requestId"],
        },
        "terminalOutcomes": {
            "response": ["response_too_large"],
            "upstream": ["upstream_timeout", "upstream_http", "redirect_refused", "upstream_protocol"],
            "broker": ["server_shutdown", "internal"],
        },
        "failBeforeUpstream": True,
    }
    assert protocol["fixture"] == {
        "path": "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json",
        "harness": "vendor exact JSON fixture",
        "sha256": "pinned in tests/contract/test_delegated_provider_protocol.py EXPECTED_SHA256",
    }
    assert protocol["logging"] == {
        "events": ["cli.task.delegate.start", "cli.task.delegate.end"],
        "authoritativeEmitter": "kernel broker",
        "harness": "must not emit provider_attempt or either delegation audit event",
        "format": "JSONL",
        "time": "UTC",
        "fields": ["sid", "code", "duration_us"],
        "broker": "no independent logs",
        "secrets": "no session/auth headers/raw prompts",
    }

    schemas = artifact["schemas"]
    assert "requestId" in schemas["chatRequest"]["required"]
    assert schemas["handshakeRequest"]["properties"]["provider"] == {
        "type": "string", "minLength": 1, "maxLength": 256
    }
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
    assert vectors[2]["expected"] == {
        "remainingRequests": 7,
        "sse": "opaque relay; not a literal vector body",
    }
    assert vectors[4]["expected"] == {
        "remainingRequests": 6,
        "sse": "opaque relay; not a literal vector body",
    }
    assert vectors[1]["response"]["error"] == "replay"
    assert vectors[3]["expected"]["error"] == "replay"
    assert "response" not in vectors[2] and "response" not in vectors[3] and "response" not in vectors[4]
    assert vectors[2]["request"]["requestId"] == vectors[3]["request"]["requestId"]
    assert vectors[2]["request"]["requestId"] != vectors[4]["request"]["requestId"]
    assert all(re.fullmatch(CAPABILITY_PATTERN, vector["request"]["capability"]) for vector in vectors)
    assert re.fullmatch(r"[A-Za-z0-9_-]{21}[AQgw]", vectors[2]["request"]["requestId"])
    assert re.fullmatch(r"[A-Za-z0-9_-]{21}[AQgw]", vectors[4]["request"]["requestId"])
    assert set(vectors[2]["request"]["tools"][0]) == {"type", "function"}
    assert vectors[2]["request"]["tools"][0]["function"]["name"] == "weather"
    with pytest.raises(AssertionError, match="duplicate JSON key"):
        json.loads('{"protocol": "one", "protocol": "two"}', object_pairs_hook=_reject_duplicate_keys)
