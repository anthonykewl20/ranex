"""Positive-allowlist redaction for the kernel observability trace (ADR-031).

Inversion of pino's declared-path blocklist: only members of the frozen
eleven-field set (plus ``evt``/``exe`` on the ``version`` variant) may ever
be serialized.

Refusal semantics, fixed by the frozen tests:

- An undeclared *name* (any key outside the frozen set, including ``evt``/
  ``exe`` on a non-version event) is dropped from the payload and named in a
  refusal event — by name only when the name matches the bounded identifier
  grammar and the resulting ``undeclared_field:<name>`` code stays inside the
  frozen ``code`` grammar; any other name is represented by shape plus
  digest, never its bytes (ADR-031 sad path 11). The surviving declared
  fields are still emitted: the allowlist discarded the extra, the rest of
  the event stands (tests/unit/test_observability.py::
  test_undeclared_field_is_dropped_and_named_when_identifier_shaped).
- A declared field whose *value* is outside its closed form — including
  non-null stage fields on a ``version`` event, and any payload that is not
  a mapping or whose ``event`` is not classifiable — refuses the whole
  emission: nothing but refusal events is written. An out-of-form value
  means the event's own content is corrupt or hostile, and under hostile
  input no key byte, credential URL, or evidence byte may appear in any line
  (tests/security/test_trace_secret_scrubbing.py — a grammar-valid ``code``
  carrying a planted token reaches the stream only if the rest of a corrupt
  payload is still published).

Every string in a refusal payload is a bounded registry literal; refused
values are represented by variable plus shape plus digest, never bytes.
"""

from __future__ import annotations

import ranex.observability.schema as schema
from ranex.observability.schema import FIELDS, VERSION_ONLY_FIELDS

# A dropped field name is echoed in a refusal code only when the whole code
# stays inside the frozen code grammar — the argument bound is 200, so an
# echoable name is bounded by the same 200 rather than truncated.
_ECHO_CAP = 200

# The stage-lifecycle fields that must be null on a ``version`` event (the
# variant carries the eleven with every stage field null plus evt/exe).
_VERSION_NULL_FIELDS = (
    "module",
    "stage",
    "subject_digest",
    "duration_us",
    "hierarchy",
    "child_id",
    "code",
)


def echoable_name(name: str) -> str | None:
    """The echo form of a dropped field name, or None when it must not be named."""

    if not isinstance(name, str) or not schema.field_name_is_named(name):
        return None
    if len(name) > _ECHO_CAP:
        return None
    if not schema.code_is_well_formed(f"undeclared_field:{name}"):
        return None
    return name


def screen_event(raw: object) -> tuple[dict | None, list[dict]]:
    """Decide one emission attempt.

    Returns ``(accepted, refusals)``: ``accepted`` is the payload restricted
    to the frozen fields — None when the attempt is refused as a whole — and
    ``refusals`` is a list of ready-to-fill refusal payloads whose only
    variable content is a bounded, grammar-checked ``code`` string.
    ``sid`` and ``time`` are emitter-owned and never taken from the payload.
    """

    if not isinstance(raw, dict):
        return None, [_refusal_payload("emission_refused")]

    event_name = raw.get("event")
    if not isinstance(event_name, str) or event_name not in schema.EVENT_NAMES:
        return None, [_refusal_payload(f"out_of_form:event:{schema.shape_descriptor(event_name)}")]

    refusals: list[dict] = []
    accepted: dict = {}
    version_variant = event_name == "version"
    allowed = set(FIELDS) | (set(VERSION_ONLY_FIELDS) if version_variant else set())

    # Undeclared names: dropped and named; the surviving event still stands.
    for name in raw:
        if name in allowed:
            continue
        echoed = echoable_name(name) if isinstance(name, str) else None
        if echoed is not None:
            refusals.append(_refusal_payload(f"undeclared_field:{echoed}"))
        else:
            refusals.append(
                _refusal_payload(f"undeclared_field:{schema.shape_descriptor(name)}")
            )

    # Version-variant discipline: non-null stage fields are out of form.
    if version_variant:
        for field in _VERSION_NULL_FIELDS:
            if raw.get(field) is not None:
                refusals.append(
                    _refusal_payload(
                        f"out_of_form:{field}:{schema.shape_descriptor(raw.get(field))}"
                    )
                )

    # Copy declared fields, screening closed forms; any violation refuses the
    # whole emission — the payload's own content is not trustworthy.
    value_fields = [f for f in FIELDS if f not in ("sid", "time")]
    if version_variant:
        value_fields += list(VERSION_ONLY_FIELDS)
    for field in value_fields:
        if field not in raw:
            continue
        value = raw[field]
        if field in _VERSION_NULL_FIELDS and version_variant:
            continue  # already refused above; never copied onto the variant
        reason = schema.validate_field_value(field, value)
        if reason is not None:
            refusals.append(
                _refusal_payload(f"out_of_form:{field}:{schema.shape_descriptor(value)}")
            )
            return None, refusals
        accepted[field] = value

    if refusals and any(payload["code"].startswith("out_of_form:") for payload in refusals):
        # A value-form violation refuses the whole attempt: only refusals flow.
        return None, refusals
    return accepted, refusals


def _refusal_payload(code: str) -> dict:
    """A refusal event payload inside the frozen eleven (code carries the name)."""

    if not schema.code_is_well_formed(code):  # belt: the refusal itself stays bounded
        code = "emission_refused"
    return {
        "event": "refusal",
        "level": "warn",
        "module": "observability",
        "stage": "observability.emission",
        "code": code,
    }
