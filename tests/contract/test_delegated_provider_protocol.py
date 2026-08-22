"""Freeze ADR-033's protocol artifact before SLICE-069 implementation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from ranex.observability import schema as trace_schema

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json"
EXPECTED_SHA256 = "94bff0f1647382fd3f24c78176b5e6ab3b917173b3ae9627889489892cfdb48f"
ERRORS = {
    "invalid_protocol", "unsupported_version", "unauthorized", "handshake_required",
    "session_mismatch", "replay", "expired", "model_not_allowed", "provider_not_allowed",
    "invalid_request", "tool_not_allowed", "request_too_large", "response_too_large",
    "concurrency_limit", "request_limit", "upstream_timeout", "upstream_http",
    "redirect_refused", "upstream_protocol", "server_shutdown", "internal",
}
OUTCOMES = [
    "success", "response_too_large", "upstream_timeout", "upstream_http",
    "redirect_refused", "upstream_protocol", "server_shutdown", "internal",
]
EXPECTED_VECTOR_IDS = {
    "bootstrap-complete-example-non-normative-port",
    "handshake-ok",
    "handshake-replay",
    "chat-first-request",
    "chat-replay",
    "chat-distinct-second-request",
    "unsupported-version",
    "chat-upstream-failure-consumes-attempt",
    "chat-failed-request-replay-does-not-consume",
    "invalid-tool-order",
    "invalid-request-id-terminal-character",
    "concurrency-limit-before-reservation",
    "expired-before-reservation",
    "response-too-large-post-reservation",
    "ninth-distinct-request-limit-before-reservation",
}
EXPECTED_PROTOCOL_KEYS = {
    "bind", "bootstrap", "chat", "chatAccounting", "chatReplayKey", "chatTimeout",
    "distinctRequestIds", "fixture", "grant", "handshake", "handshakeAccounting",
    "handshakeReplayKey", "handshakeUse", "httpSse", "logging", "maxBootstrapBytes",
    "maxConcurrency", "maxRequestBytes", "maxRequests", "maxRequestsScope",
    "maxResponseBytes", "name", "persistence", "policy", "preStreamHttpStatus",
    "redirects", "requestBytes", "requestId", "responseBytes", "retry", "schemaValidation",
    "stream", "timeoutScope", "timeoutSeconds", "transport", "ttlAccounting", "ttlSeconds",
    "upstream", "validation", "version",
}
PRE_RESERVATION_ERRORS = [
    "invalid_protocol", "unsupported_version", "unauthorized", "handshake_required",
    "session_mismatch", "replay", "expired", "model_not_allowed", "provider_not_allowed",
    "invalid_request", "tool_not_allowed", "request_too_large", "concurrency_limit", "request_limit",
]
def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _artifact() -> dict[str, object]:
    raw = ARTIFACT.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    assert raw == (json.dumps(json.loads(raw), indent=2) + "\n").encode()
    return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)


def test_delegated_provider_protocol_freeze() -> None:
    artifact = _artifact()
    protocol = artifact["protocol"]
    assert set(protocol) == EXPECTED_PROTOCOL_KEYS
    assert protocol["name"] == "ranex-delegated-provider"
    assert protocol["version"] == 1
    assert (protocol["ttlSeconds"], protocol["maxRequests"], protocol["maxConcurrency"]) == (300, 8, 1)
    assert (protocol["maxRequestBytes"], protocol["maxResponseBytes"]) == (4 * 1024 * 1024, 16 * 1024 * 1024)
    assert protocol["maxBootstrapBytes"] == 65536
    assert protocol["timeoutSeconds"] == 120
    assert protocol["upstream"] == "https://openrouter.ai/api/v1/chat/completions"
    assert protocol["redirects"] == "refuse"
    assert protocol["retry"] == protocol["persistence"] == "none"
    assert protocol["chatReplayKey"] == ["session", "requestId"]
    assert protocol["handshakeReplayKey"] == ["capability"]
    assert protocol["requestId"] == {"encoding": "base64url", "randomBytes": 16, "length": 22, "finalCharacters": "AQgw"}
    assert protocol["maxRequestsScope"] == "chat only; provider attempts"
    assert protocol["distinctRequestIds"] == "at most 8 accepted reservations per session; every accepted requestId is unique within that session"
    assert protocol["policy"]["chatProvider"] == (
        "if omitted, use the authenticated session provider; if present, it must equal the session provider"
    )

    transport = protocol["transport"]
    assert transport["rawKeyIngress"] == "kernel receives the raw provider key only through an inherited FD/pipe owned by the kernel process"
    assert "environment" not in transport["rawKeyIngress"]
    assert "environment" not in " ".join(transport["rawKeyProhibited"])
    assert "FD 3" in transport["fd3CloseAll"] and "distinct child pipe" in transport["fd3CloseAll"]
    assert "never the bytes" in transport["fd3CloseAll"]
    assert "reads and closes" in transport["spawn"]

    status = protocol["preStreamHttpStatus"]
    assert {key for key in status if key not in {"preStream", "post200"}} == {
        "invalid_protocol", "unsupported_version", "unauthorized", "handshake_required",
        "session_mismatch", "replay", "expired", "model_not_allowed", "provider_not_allowed",
        "invalid_request", "tool_not_allowed", "request_too_large", "concurrency_limit", "request_limit",
    }
    assert {key: status[key] for key in status if key not in {"preStream", "post200"}} == {
        "invalid_protocol": 400, "unsupported_version": 426, "unauthorized": 401, "handshake_required": 401,
        "session_mismatch": 401, "replay": 409, "expired": 410, "model_not_allowed": 403,
        "provider_not_allowed": 403, "invalid_request": 400, "tool_not_allowed": 403,
        "request_too_large": 413, "concurrency_limit": 429, "request_limit": 429,
    }
    assert "response_too_large" not in status and "upstream_protocol" not in status

    assert set(artifact["schemas"]["error"]["properties"]["error"]["enum"]) == ERRORS
    assert len(ERRORS) == 21
    schemas = artifact["schemas"]
    assert {"handshakeRequest", "handshakeResponse", "chatRequest", "chatResponse"} <= set(schemas)
    for schema_name in ("handshakeRequest", "handshakeResponse", "chatRequest"):
        schema = schemas[schema_name]
        if "provider" in schema["properties"]:
            assert schema["properties"]["provider"]["type"] == "string"
        if "model" in schema["properties"]:
            assert "const" not in schema["properties"]["model"]
        if "provider" in schema["properties"]:
            assert "const" not in schema["properties"]["provider"]
    assert schemas["chatResponse"] == {
        "description": "Opaque raw SSE relay; each event is forwarded without constraining model-specific response structure.",
        "type": "object",
    }
    capability_pattern = r"^[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]$"
    assert schemas["bootstrap"]["properties"]["capability"]["pattern"] == capability_pattern
    expected_request_id_pattern = r"^[A-Za-z0-9_-]{21}[AQgw]$"
    assert schemas["chatRequest"]["properties"]["requestId"]["pattern"] == expected_request_id_pattern
    assert "provider" not in schemas["chatRequest"]["required"]
    request_id_regex = re.compile(schemas["chatRequest"]["properties"]["requestId"]["pattern"])
    assert schemas["handshakeResponse"]["properties"]["session"]["minLength"] == 16
    for schema_name in ("handshakeRequest", "chatRequest"):
        tools = schemas[schema_name]["properties"]["tools"]
        assert tools["maxItems"] == 32 and tools["uniqueItems"] is True
        tool_name = tools["items"] if schema_name == "handshakeRequest" else tools["items"]["properties"]["function"]["properties"]["name"]
        assert tool_name["pattern"] == r"^[A-Za-z0-9_-]{1,64}$"
    assert protocol["validation"]["reservationState"] == {
        "preReservation": {
            "consumes": 0,
            "emits": 0,
            "errors": PRE_RESERVATION_ERRORS,
        },
        "postReservation": {"consumes": 1, "emits": 1, "outcomes": OUTCOMES},
    }

    attempt = protocol["logging"]["providerAttempt"]
    assert attempt["event"] == "stage"
    assert attempt["module"] == "cli"
    assert attempt["stage"] == "cli.task.delegate.provider_attempt"
    assert attempt["code"] == {"form": "delegation_provider_attempt:<argument>", "argumentSet": OUTCOMES}
    assert attempt["fields"] == {
        "nonNull": ["event", "sid", "time", "level", "module", "stage", "duration_us", "code"],
        "null": ["subject_digest", "hierarchy", "child_id"],
    }
    assert set(attempt["fields"]["nonNull"]) | set(attempt["fields"]["null"]) == set(trace_schema.FIELDS)
    assert "stage" in trace_schema.EVENT_NAMES and "cli" in trace_schema.MODULES
    assert attempt["stage"] not in trace_schema.STAGES
    assert "#43" in protocol["logging"]["schemaEvolution"]

    vectors = artifact["vectors"]
    assert len(vectors) == len(EXPECTED_VECTOR_IDS)
    assert {vector["id"] for vector in vectors} == EXPECTED_VECTOR_IDS
    assert vectors[0]["id"] == "bootstrap-complete-example-non-normative-port"
    bootstrap = vectors[0]["bootstrap"]
    assert set(bootstrap) == set(artifact["schemas"]["bootstrap"]["required"])
    assert bootstrap["endpoint"]["scheme"] == "http" and bootstrap["endpoint"]["host"] == "127.0.0.1"
    assert 1 <= bootstrap["endpoint"]["port"] <= 65535
    assert "non-normative" in vectors[0]["id"]
    assert vectors[0]["portSemantics"].startswith("non-normative allocated-port example")
    vectors_by_id = {vector["id"]: vector for vector in vectors}
    assert vectors_by_id["handshake-ok"]["response"]["remainingRequests"] == 8
    assert vectors_by_id["chat-first-request"]["expected"]["remainingRequests"] == 7
    assert vectors_by_id["chat-distinct-second-request"]["expected"]["remainingRequests"] == 6
    assert vectors_by_id["chat-upstream-failure-consumes-attempt"]["expected"]["remainingRequests"] == 5
    assert vectors_by_id["chat-upstream-failure-consumes-attempt"]["expected"]["emissionCount"] == 1
    assert vectors_by_id["chat-failed-request-replay-does-not-consume"]["expected"]["remainingRequests"] == 5
    assert all(
        request_id_regex.fullmatch(vector["requestId"])
        for vector in vectors
        if "requestId" in vector and vector["id"] != "invalid-request-id-terminal-character"
    )
    invalid_request_id = next(vector for vector in vectors if vector["id"] == "invalid-request-id-terminal-character")
    assert len(invalid_request_id["requestId"]) == 22
    assert invalid_request_id["requestId"][-1] == "Z"
    assert not request_id_regex.fullmatch(invalid_request_id["requestId"])
    response_too_large = vectors_by_id["response-too-large-post-reservation"]
    assert response_too_large["expected"] == {"emissionCount": 1, "outcome": "response_too_large", "reserved": True}

    request_limit = vectors_by_id["ninth-distinct-request-limit-before-reservation"]
    accepted = request_limit["state"]["acceptedRequestIds"]
    assert len(accepted) == protocol["maxRequests"] == 8
    assert len(set(accepted)) == len(accepted)
    assert all(request_id_regex.fullmatch(request_id) for request_id in accepted)
    assert request_limit["requestId"] not in accepted
    assert request_limit["expected"] == {"error": "request_limit", "reserved": False}
    assert request_limit["expected"]["reserved"] is False
    assert protocol["validation"]["reservationState"]["preReservation"]["consumes"] == 0
    assert protocol["validation"]["reservationState"]["preReservation"]["emits"] == 0


def test_duplicate_key_rejection_is_independent() -> None:
    import pytest

    with pytest.raises(AssertionError, match="duplicate JSON key"):
        json.loads('{"protocol": "one", "protocol": "two"}', object_pairs_hook=_reject_duplicate_keys)
