"""Webhook delivery validation: every delivery proves itself before it runs.

GitHub signs the raw request body with the webhook secret under HMAC-SHA256
and sends `X-Hub-Signature-256: sha256=<hex>`. The comparison is
constant-time, the body is read before any parsing, and a delivery that
cannot prove itself is refused before a single byte of it is interpreted
(ADR-051). The event grammar is closed: `pull_request` with action
`opened`, `synchronize` or `reopened`; everything else is acknowledged,
journaled, and never processed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

SIGNATURE_HEADER = "X-Hub-Signature-256"
DELIVERY_HEADER = "X-GitHub-Delivery"
EVENT_HEADER = "X-GitHub-Event"

_SIGNATURE_PREFIX = "sha256="
HANDLED_EVENT = "pull_request"
HANDLED_ACTIONS = frozenset({"opened", "synchronize", "reopened"})

# The docs' own published test vector (validating-webhook-deliveries), pinned
# so a refactor of the comparison cannot silently change the arithmetic.
DOCUMENTED_VECTOR_SECRET = "It's a Secret to Everybody"
DOCUMENTED_VECTOR_BODY = b"Hello, World!"
DOCUMENTED_VECTOR_SIGNATURE = (
    "sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17"
)


class WebhookRefusal(ValueError):
    """A delivery that did not prove itself, named for the operator."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code = code
        self.detail = detail


def delivery_signature(secret: str, body: bytes) -> str:
    """The exact signature GitHub documents for X-Hub-Signature-256."""

    return _SIGNATURE_PREFIX + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()


def validate_delivery(secret: str, body: bytes, signature_header: str | None) -> None:
    """Refuse unsigned and tampered deliveries before any parsing."""

    if not signature_header:
        raise WebhookRefusal(
            "E-GITHUB-UNSIGNED-DELIVERY", f"{SIGNATURE_HEADER} is absent"
        )
    if not hmac.compare_digest(
        delivery_signature(secret, body), signature_header.strip()
    ):
        raise WebhookRefusal("E-GITHUB-BAD-SIGNATURE", "signature does not match body")


@dataclass(frozen=True, slots=True)
class PullRequestEvent:
    """The one event shape this receiver processes, closed at parse time."""

    action: str
    head_sha: str
    repository: str
    installation_id: int
    number: int


def parse_pull_request_event(body: bytes) -> PullRequestEvent | None:
    """The event, or None when the delivery is acknowledged but not ours.

    Parse failures of a *signed* body are refusals, not ignores: GitHub signed
    this shape, so it came from the webhook, and an unexpected shape means the
    grammar moved — an operator must hear about it, not watch it scroll past.
    """

    value: Any = json.loads(body)
    if not isinstance(value, dict):
        raise WebhookRefusal("E-GITHUB-BAD-EVENT", "body is not an object")
    if value.get("action") not in HANDLED_ACTIONS:
        return None
    try:
        pull_request = value["pull_request"]
        head = pull_request["head"]["sha"]
        repository = value["repository"]["full_name"]
        installation = value["installation"]["id"]
        number = value["pull_request"]["number"]
    except (KeyError, TypeError) as exc:
        raise WebhookRefusal(
            "E-GITHUB-BAD-EVENT", f"pull_request event lacks {exc}"
        ) from exc
    return PullRequestEvent(
        action=str(value["action"]),
        head_sha=str(head),
        repository=str(repository),
        installation_id=int(installation),
        number=int(number),
    )
