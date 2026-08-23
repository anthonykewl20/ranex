"""Freeze ADR-033's protocol artifact before SLICE-069 implementation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from ranex.observability import schema as trace_schema

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "governance/schemas/delegated-provider/ranex-delegated-provider-v1.json"
EXPECTED_SHA256 = "1708771b32fd3420776b4923a8f14023aa50a5b3dfc022ae94bb157a1f8fb35c"
ERRORS = {
    "invalid_protocol", "unsupported_version", "unauthorized", "handshake_required",
    "session_mismatch", "replay", "expired", "model_not_allowed", "provider_not_allowed",
    "invalid_request", "tool_not_allowed", "request_too_large", "response_too_large",
    "concurrency_limit", "request_limit", "upstream_timeout", "upstream_http",
    "redirect_refused", "upstream_protocol", "server_shutdown", "internal",
    "upstream_dns", "upstream_connect", "upstream_tls", "client_cancelled",
}
OUTCOMES = [
    "success", "upstream_dns", "upstream_connect", "upstream_tls", "client_cancelled",
    "response_too_large", "upstream_timeout", "upstream_http", "redirect_refused",
    "upstream_protocol", "server_shutdown", "internal",
]
EXPECTED_VECTOR_IDS = {
    "bootstrap-complete-example-non-normative-port",
    "handshake-ok",
    "handshake-replay",
    "chat-first-request",
    "chat-replay",
    "chat-distinct-second-request",
    "unsupported-version",
    "fingerprint-mismatch", "fingerprint-mismatch-bootstrap", "fingerprint-mismatch-handshake-response",
    "fingerprint-mismatch-chat-request",
    "chat-upstream-failure-consumes-attempt",
    "chat-failed-request-replay-does-not-consume",
    "invalid-tool-order",
    "invalid-request-id-terminal-character",
    "concurrency-limit-before-reservation",
    "expired-before-reservation",
    "response-too-large-post-reservation",
    "upstream-dns-post-reservation", "upstream-connect-post-reservation",
    "upstream-tls-post-reservation", "upstream-non-200-status-post-reservation",
    "upstream-redirect-refused-post-reservation",
    "upstream-wrong-media-type-post-reservation", "client-cancelled-post-reservation",
    "sse-headers-then-immediate-eof-post-reservation", "client-cancel-during-upstream-failure",
    "ninth-distinct-request-limit-before-reservation",
}
EXPECTED_PROTOCOL_KEYS = {
    "bind", "bootstrap", "chat", "chatAccounting", "chatReplayKey", "chatTimeout",
    "distinctRequestIds", "fixture", "grant", "handshake", "handshakeAccounting",
    "handshakeReplayKey", "handshakeUse", "httpSse", "logging", "maxBootstrapBytes",
    "maxConcurrency", "maxRequestBytes", "maxRequests", "maxRequestsScope",
    "maxResponseBytes", "name", "persistence", "policy", "preDownstreamHttpStatus", "preDownstreamNormalization", "terminalPrecedence", "preStreamHttpStatus",
    "security",
    "httpAdmission",
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


def _protocol_fingerprint(artifact: dict[str, object]) -> str:
    payload = {"protocol": artifact["protocol"], "schemas": artifact["schemas"]}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def test_delegated_provider_protocol_freeze() -> None:
    artifact = _artifact()
    protocol = artifact["protocol"]
    assert artifact["protocolFingerprint"] == _protocol_fingerprint(artifact)
    schemas = artifact["schemas"]
    assert protocol["bootstrap"]["required"] == schemas["bootstrap"]["required"]
    assert set(protocol) == EXPECTED_PROTOCOL_KEYS
    assert protocol["name"] == "ranex-delegated-provider"
    assert protocol["version"] == 1
    assert (protocol["ttlSeconds"], protocol["maxRequests"], protocol["maxConcurrency"]) == (300, 8, 1)
    assert (protocol["maxRequestBytes"], protocol["maxResponseBytes"]) == (4 * 1024 * 1024, 16 * 1024 * 1024)
    assert protocol["maxBootstrapBytes"] == 65536
    assert protocol["timeoutSeconds"] == 120
    assert protocol["upstream"] == "https://openrouter.ai/api/v1/chat/completions"
    assert protocol["redirects"] == "refuse"
    assert protocol["retry"] == "none"
    assert protocol["persistence"] == "no prompts or outputs; exactly two secret-free hash-chained reservation ledger rows per reserved attempt"
    assert protocol["chatReplayKey"] == ["session", "requestId"]
    assert protocol["handshakeReplayKey"] == ["capability"]
    assert protocol["requestId"] == {"encoding": "base64url", "randomBytes": 16, "length": 22, "finalCharacters": "AQgw"}
    assert protocol["maxRequestsScope"] == "chat only; provider attempts"
    assert protocol["distinctRequestIds"] == "at most 8 accepted reservations per session; every accepted requestId is unique within that session"
    assert protocol["policy"]["chatProvider"] == (
        "if omitted, use the authenticated session provider; if present, it must equal the session provider"
    )
    assert protocol["transport"]["upstreamRequest"] == {
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "connection": "direct HTTPSConnection to openrouter.ai:443; no proxy, tunnel, or configurable endpoint",
        "authorization": "broker constructs Authorization internally from the kernel-only raw key",
        "forwarded": "harness cannot supply or forward Authorization, custom headers, proxy settings, endpoint, transport, TLS, or debug options",
        "debuglevel": 0,
        "redirects": "refuse",
    }
    assert protocol["logging"]["audit"] == {
        "durable": False,
        "emitter": "exactly one ADR-031 emitter invocation per reserved attempt",
        "materialization": "materialized only when tracing is enabled; tracing disabled is verdict-neutral and emits nothing",
        "authority": "observability event only; not an authoritative durable audit",
    }
    assert protocol["logging"]["reservationLedger"]["rows"] == 2
    assert protocol["logging"]["reservationLedger"]["sequence"] == [
        "reserved before any upstream I/O", "terminal after upstream attempt"
    ]
    assert protocol["logging"]["reservationLedger"]["identity"] == (
        "each row carries the secret-free correlation fields taskId, session, requestId (when applicable), provider, model, "
        "and attemptCorrelationId = sha256 over canonical JSON {taskId, session, requestId} with sorted keys and compact separators; "
        "no secret material"
    )
    assert protocol["logging"]["reservationLedger"]["stageEventLinkage"] == (
        "the single ADR-031 provider_attempt stage event carries attemptCorrelationId as its non-null subject_digest; ledger rows and "
        "the stage event join on attemptCorrelationId; no new trace-schema field is introduced"
    )
    assert protocol["logging"]["reservationLedger"]["crashRecovery"] == (
        "at broker start, a reserved row without a terminal row is reconciled by appending a terminal row with outcome internal and "
        "marker reconciled_after_restart before any new reservation is accepted; a reconciliation pass applies the same rule to "
        "reserved rows older than timeoutSeconds + 60 seconds without a terminal row"
    )
    assert "does not detect rollback or truncation" in protocol["logging"]["reservationLedger"]["residual"]
    assert protocol["security"]["scope"].startswith("accidental secret non-propagation")
    assert "not isolation against an adversarial same-UID harness" in protocol["security"]["scope"]
    assert protocol["httpAdmission"] == {
        "maxHeaderBytes": 16384,
        "maxHeaderCount": 100,
        "maxPendingUnauthenticatedConnections": 64,
        "maxRequestLineBytes": 8192,
        "oversizedContentLengthStatus": 413,
        "errorCodes": {
            "oversizedContentLength": "request_too_large",
            "chunked": "invalid_protocol",
            "contentLengthWithTransferEncoding": "invalid_protocol",
            "duplicateContentLength": "invalid_protocol",
            "conflictingContentLength": "invalid_protocol",
            "missingContentLength": "invalid_protocol",
            "duplicateJsonKey": "invalid_protocol",
        },
        "acceptLoop": "bounded non-blocking accept loop; refuse further accepts while 64 unauthenticated connections are pending",
        "unauthenticatedReadDeadlineSeconds": 5,
        "framing": "Content-Length is required for requests with a body; Transfer-Encoding/chunked, Content-Length plus Transfer-Encoding, duplicate Content-Length, and conflicting Content-Length values are rejected",
        "json": "strict duplicate-key rejection before authentication or body dispatch",
        "providerSlot": "unauthenticated header/body admission is completed before authentication, validation, and the single provider-attempt slot reservation; partial unauthenticated clients cannot consume that slot",
        "implementation": "bounded parser and socket deadlines; do not rely on undocumented http.server knobs",
        "rationale": "16 KiB headers, 100 fields, and 8 KiB request lines stay below common stdlib line limits while bounding unauthenticated memory and header abuse; five seconds matches the handshake deadline",
        "pendingRationale": "64 pending unauthenticated connections bound pre-auth resource use; a local process can still occupy the pending pool for up to the read deadline and deny the legitimate harness admission — a bounded local availability residual (the provider slot itself is never consumed)",
        "availabilityResidual": "bounded local admission DoS remains possible; owner-accepted availability trade-off, recorded with the other known limits",
        "contentLengthRationale": "rejecting a declared body above maxRequestBytes at admission avoids allocating or reading an oversized unauthenticated request",
    }

    transport = protocol["transport"]
    assert transport["rawKeyIngress"] == "kernel receives the raw provider key only through an inherited FD/pipe owned by the kernel process under non-adversarial broker dataflow (see protocol.security.sameUidResidual)"
    assert transport["harnessStorage"] == "bounded in-memory only under non-adversarial broker dataflow (see protocol.security.sameUidResidual)"
    assert transport["rawKeyProhibited"][-1] == "request bodies; under non-adversarial broker dataflow (see protocol.security.sameUidResidual)"
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
        "invalid_protocol": 400, "unsupported_version": 400, "unauthorized": 401, "handshake_required": 401,
        "session_mismatch": 401, "replay": 409, "expired": 410, "model_not_allowed": 403,
        "provider_not_allowed": 403, "invalid_request": 400, "tool_not_allowed": 403,
        "request_too_large": 413, "concurrency_limit": 429, "request_limit": 429,
    }
    assert "response_too_large" not in status and "upstream_protocol" not in status
    assert protocol["preDownstreamHttpStatus"] == {
        "upstream_dns": 502, "upstream_connect": 502, "upstream_tls": 502, "client_cancelled": None,
        "response_too_large": 502,
        "upstream_timeout": 504,
        "upstream_http": 502,
        "redirect_refused": 502,
        "upstream_protocol": 502,
        "server_shutdown": 503,
        "internal": 500,
    }
    assert "exactly one non-overlapping named code" in protocol["preDownstreamNormalization"]
    assert protocol["terminalPrecedence"] == (
        "the terminal outcome is the first terminal condition the broker observes; if a downstream client close and an upstream failure "
        "are observed in the same event-loop iteration, client_cancelled takes precedence"
    )

    assert set(artifact["schemas"]["error"]["properties"]["error"]["enum"]) == ERRORS
    assert len(ERRORS) == 25
    assert {"handshakeRequest", "handshakeResponse", "chatRequest", "chatResponse"} <= set(schemas)
    for schema_name in ("handshakeRequest", "handshakeResponse", "chatRequest", "bootstrap"):
        assert "protocolFingerprint" in schemas[schema_name]["required"]
        assert schemas[schema_name]["properties"]["protocolFingerprint"]["pattern"] == r"^[0-9a-f]{64}$"
        schema = schemas[schema_name]
        if schema_name != "bootstrap":
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
    assert attempt["subjectDigest"] == (
        "non-null; equals attemptCorrelationId = sha256 over canonical JSON {taskId, session, requestId} with sorted keys and compact separators"
    )
    assert attempt["stage"] not in trace_schema.STAGES
    assert attempt["code"] == {"form": "delegation_provider_attempt:<argument>", "argumentSet": OUTCOMES}
    assert attempt["fields"] == {
        "nonNull": ["event", "sid", "time", "level", "module", "stage", "subject_digest", "duration_us", "code"],
        "null": ["hierarchy", "child_id"],
    }
    assert set(attempt["fields"]["nonNull"]) | set(attempt["fields"]["null"]) == set(trace_schema.FIELDS)
    assert "stage" in trace_schema.EVENT_NAMES and "cli" in trace_schema.MODULES
    assert attempt["stage"] == "cli.task.delegate.provider_attempt"
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
    fingerprint = artifact["protocolFingerprint"]
    assert vectors_by_id["handshake-ok"]["request"]["protocolFingerprint"] == fingerprint
    assert vectors_by_id["handshake-ok"]["response"]["protocolFingerprint"] == fingerprint
    assert vectors[0]["bootstrap"]["protocolFingerprint"] == fingerprint
    fingerprint_mismatch = vectors_by_id["fingerprint-mismatch"]
    mismatched_value = fingerprint_mismatch["request"]["protocolFingerprint"]
    fingerprint_schema = schemas["handshakeRequest"]["properties"]["protocolFingerprint"]
    assert isinstance(mismatched_value, str)
    assert re.fullmatch(fingerprint_schema["pattern"], mismatched_value)
    assert len(mismatched_value) == 64
    assert mismatched_value != fingerprint
    assert fingerprint_mismatch["response"]["error"] == "unsupported_version"
    assert fingerprint_mismatch["expected"] == {
        "error": "unsupported_version",
        "reserved": False,
        "upstream": False,
    }
    assert vectors_by_id["fingerprint-mismatch-bootstrap"]["bootstrap"]["protocolFingerprint"] == "0" * 64
    assert vectors_by_id["fingerprint-mismatch-bootstrap"]["expected"] == fingerprint_mismatch["expected"]
    assert vectors_by_id["fingerprint-mismatch-handshake-response"]["response"]["protocolFingerprint"] == "0" * 64
    assert vectors_by_id["fingerprint-mismatch-handshake-response"]["expected"] == fingerprint_mismatch["expected"]
    chat_mismatch = vectors_by_id["fingerprint-mismatch-chat-request"]
    chat_mismatch_value = chat_mismatch["request"]["protocolFingerprint"]
    chat_fingerprint_schema = schemas["chatRequest"]["properties"]["protocolFingerprint"]
    assert re.fullmatch(chat_fingerprint_schema["pattern"], chat_mismatch_value)
    assert chat_mismatch_value != fingerprint
    assert chat_mismatch["expected"] == fingerprint_mismatch["expected"]
    assert chat_mismatch["response"] == {
        "error": "unsupported_version",
        "message": "protocol fingerprint is not supported",
    }
    assert protocol["validation"]["reservationState"]["preReservation"] == {
        "consumes": 0,
        "emits": 0,
        "errors": PRE_RESERVATION_ERRORS,
    }
    invalid_request_id = next(vector for vector in vectors if vector["id"] == "invalid-request-id-terminal-character")
    assert len(invalid_request_id["requestId"]) == 22
    assert invalid_request_id["requestId"][-1] == "Z"
    assert not request_id_regex.fullmatch(invalid_request_id["requestId"])
    response_too_large = vectors_by_id["response-too-large-post-reservation"]
    assert response_too_large["expected"] == {"emissionCount": 1, "outcome": "response_too_large", "reserved": True}
    for outcome in ("upstream_dns", "upstream_connect", "upstream_tls", "client_cancelled"):
        assert vectors_by_id[f"{outcome.replace('_', '-')}-post-reservation"]["expected"] == {
            "emissionCount": 1, "outcome": outcome, "reserved": True,
        }
    assert vectors_by_id["sse-headers-then-immediate-eof-post-reservation"]["expected"] == {
        "emissionCount": 1, "outcome": "upstream_protocol", "reserved": True,
    }
    assert vectors_by_id["upstream-non-200-status-post-reservation"]["expected"] == {
        "emissionCount": 1, "outcome": "upstream_http", "reserved": True,
    }
    assert vectors_by_id["upstream-redirect-refused-post-reservation"]["expected"] == {
        "emissionCount": 1, "outcome": "redirect_refused", "reserved": True,
    }
    assert vectors_by_id["upstream-wrong-media-type-post-reservation"]["expected"] == {
        "emissionCount": 1, "outcome": "upstream_protocol", "reserved": True,
    }
    assert vectors_by_id["client-cancel-during-upstream-failure"]["expected"] == {
        "emissionCount": 1, "outcome": "client_cancelled", "reserved": True,
    }

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
