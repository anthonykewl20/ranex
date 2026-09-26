"""The base-freeze promotion gate: improvement claims must cite their gauge.

SLICE-095 ships the oracle-science §5 result. The BASE freeze — a committed,
digest-bound record of kernel identity, pinned subjects, control banks and
reference metrics — is what makes a self-evolving policy claim falsifiable:
a treatment may promote only on paired MARGINAL deltas against the freeze's
own numbers, on axes the freeze itself names. This module is the deterministic
judge of that citation discipline. It refuses an improvement claim that names
no freeze, invents its own baseline, grades on axes the freeze does not carry,
reconciles no arithmetic, or stamps a calibration τ that is not the freeze's
own derived number (the exact failure that killed L3: a constant τ=0.80
against an honestly measured 0.60).

Three boundaries hold by construction:

- **Not the kernel.** This is not `evaluate()`: a promotion decision judges a
  *claim about* a treatment, never a subject tree. Nothing here signs,
  verifies, or admits; the module imports no signing, admission, or journal
  code, and its bytes have no path into a signed record's closed shapes.
- **The freeze is read, never written.** The gauge non-contamination rule
  (report §5): the freeze is committed like the catalog and read through the
  caller's committed-bytes discipline (seam C, ADR-060); a treatment that
  could regenerate the gauge favorably would grade itself.
- **Deterministic and total over claims.** Identical inputs yield identical
  canonical decision bytes; a structurally broken claim is REFUSED as data
  with a named cause, never crashed on. Absence blocks: a missing citation,
  a missing baseline, a missing receipts binding each refuse on their own.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256

FREEZE_SCHEMA = "ranex-base-freeze-v1"
CLAIM_SCHEMA = "ranex-promotion-claim-v1"
DECISION_SCHEMA = "ranex-promotion-decision-v1"

#: The freeze the report names `base-freeze-v1` and the claim cites by that
#: id. A citation is a name under the committed calibration directory, so it
#: is held to a filename-safe alphabet: no separators, no traversal, no
#: empty stem. Anything else is refused as a citation, not sanitized.
_SAFE_FREEZE_ID = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
_DIGEST64 = re.compile(r"^sha256:[0-9a-f]{64}$")
# The vendored tree digest is carried exactly as the scout recorded it
# (report §2.2 records a 40-hex tree marker); it is provenance, not a
# canonical content digest, so its width is not forced to 64.
_TREE_DIGEST = re.compile(r"^sha256:[0-9a-f]{40,64}$")
_GIT_HEX = re.compile(r"^[0-9a-f]{40}$")
_AXIS = re.compile(r"^[^.\s]+\.[^.\s]+$")

#: Closed key sets at every decode boundary, the house rule: a field this
#: version does not define is refused rather than ignored, because an ignored
#: field in a gauge or a claim is a silent rewrite of what either says.
_FREEZE_KEYS = frozenset(
    {
        "schema",
        "freeze_id",
        "minted",
        "kernel_commit",
        "kernel_digest",
        "vendored_src_tree",
        "subjects",
        "reference_metrics",
        "receipts_digest",
        "source_prereg_digest",
        "journal_head_at_freeze",
        "mint_receipts_digest",
        "provenance",
    }
)
_SUBJECT_KEYS = frozenset(
    {"commit", "suite_manifest_digest", "control_bank_digest", "suite", "cases"}
)
_PROVENANCE_KEYS = frozenset({"source", "report_digest"})
_CLAIM_KEYS = frozenset(
    {
        "schema",
        "claim_id",
        "treatment",
        "base_freeze",
        "marginal_deltas",
        "evidence_receipts_digest",
        "tau",
    }
)
_DELTA_KEYS = frozenset({"axis", "base", "treatment", "delta"})
_TAU_ENTRY_KEYS = frozenset({"axis", "value"})

#: Float equality tolerance for claim arithmetic only. Baselines are compared
#: exactly (they are the freeze's own literals); a delta is *reconciled*
#: against its base and treatment, which is arithmetic, so it tolerates
#: representation noise smaller than any honest measurement.
_ARITHMETIC_EPSILON = 1e-9


class PromotionVerdict(StrEnum):
    ADMITTED = "ADMITTED"
    REFUSED = "REFUSED"


@dataclass(frozen=True, slots=True)
class PromotionCause:
    """One named reason a promotion claim was refused, in the gate's words."""

    cause: str
    detail: str
    axis: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.cause, str) or not self.cause.strip():
            raise ValueError("cause must be a non-empty string")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("detail must be a non-empty string")


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    """The decision record. Ordered and typed so two runs are identical."""

    verdict: PromotionVerdict
    claim_id: str
    freeze_id: str | None
    freeze_digest: str | None
    axes: tuple[str, ...]
    causes: tuple[PromotionCause, ...]

    def as_record(self) -> dict[str, object]:
        return {
            "axes": list(self.axes),
            "causes": [
                {
                    "axis": cause.axis,
                    "cause": cause.cause,
                    "detail": cause.detail,
                }
                for cause in self.causes
            ],
            "claim_id": self.claim_id,
            "freeze_digest": self.freeze_digest,
            "freeze_id": self.freeze_id,
            "schema": DECISION_SCHEMA,
            "verdict": str(self.verdict),
        }

    @property
    def decision_digest(self) -> str:
        return "sha256:" + canonical_sha256(self.as_record())


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_safe_freeze_id(value: object) -> bool:
    """A citation that may name a file under the committed calibration dir.

    Filename-safe: no separators, no traversal, no empty stem. Anything else
    is refused as a citation rather than sanitized — cleaning it would hand
    the naming walk to the party being gated.
    """

    return (
        isinstance(value, str) and _SAFE_FREEZE_ID.fullmatch(value) is not None
    )


def _require_digest64(value: object, field: str) -> None:
    if not isinstance(value, str) or _DIGEST64.fullmatch(value) is None:
        raise ValueError(f"{field} must be a canonical sha256 digest")


def _freeze_axes(freeze: Mapping[str, object]) -> dict[str, float]:
    """Flatten reference metrics to ``subject.metric`` axes.

    The flat name is the claim's vocabulary, so two (subject, metric) pairs
    that flatten to one string would make a citable axis ambiguous, and an
    ambiguous gauge is refused the same way a malformed one is.
    """

    axes: dict[str, float] = {}
    metrics_root = cast(
        "Mapping[str, Mapping[str, object]]", freeze["reference_metrics"]
    )
    for subject, metrics in metrics_root.items():
        for metric, value in metrics.items():
            axis = f"{subject}.{metric}"
            if axis in axes:
                raise ValueError(
                    f"reference_metrics axis name collision on '{axis}': "
                    "a claim citing it could not name one baseline"
                )
            axes[axis] = float(cast("float", value))
    return axes


def validate_base_freeze(value: object) -> dict[str, object]:
    """Validate the durable freeze format. Refuses anything v1 does not name.

    This is the gauge: a freeze that parses loosely is a gauge anyone can
    regenerate favorably, so the key set is closed, the digests are canonical,
    and every reference metric is a number. Future freeze versions get a new
    schema id and a new validator; they never widen this one.
    """

    if not isinstance(value, Mapping):
        raise ValueError("base freeze must be a JSON object")
    freeze = dict(value)
    unknown = sorted(set(freeze) - _FREEZE_KEYS)
    missing = sorted(_FREEZE_KEYS - set(freeze))
    if unknown:
        raise ValueError(f"unknown key(s) in base freeze: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"missing key(s) in base freeze: {', '.join(missing)}")
    if freeze["schema"] != FREEZE_SCHEMA:
        raise ValueError(f"base freeze schema must be {FREEZE_SCHEMA}")
    freeze_id = freeze["freeze_id"]
    if not isinstance(freeze_id, str) or _SAFE_FREEZE_ID.fullmatch(freeze_id) is None:
        raise ValueError("freeze_id must be a filename-safe freeze identifier")
    if not isinstance(freeze["minted"], str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", str(freeze["minted"])
    ):
        raise ValueError("minted must be an ISO date (YYYY-MM-DD)")
    if not isinstance(freeze["kernel_commit"], str) or _GIT_HEX.fullmatch(
        freeze["kernel_commit"]
    ) is None:
        raise ValueError("kernel_commit must be a 40-hex git commit")
    _require_digest64(freeze["kernel_digest"], "kernel_digest")
    if not isinstance(freeze["vendored_src_tree"], str) or _TREE_DIGEST.fullmatch(
        freeze["vendored_src_tree"]
    ) is None:
        raise ValueError("vendored_src_tree must be a recorded tree digest")
    subjects = freeze["subjects"]
    if not isinstance(subjects, Mapping) or not subjects:
        raise ValueError("subjects must be a non-empty mapping")
    for name, subject in subjects.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("subject names must be non-empty strings")
        if not isinstance(subject, Mapping):
            raise ValueError(f"subject '{name}' must be a JSON object")
        unknown_subject = sorted(set(subject) - _SUBJECT_KEYS)
        if unknown_subject:
            raise ValueError(
                f"unknown key(s) in subject '{name}': {', '.join(unknown_subject)}"
            )
        if not isinstance(subject.get("commit"), str) or _GIT_HEX.fullmatch(
            subject["commit"]
        ) is None:
            raise ValueError(f"subject '{name}' must carry a 40-hex commit")
        for digest_field in ("suite_manifest_digest", "control_bank_digest"):
            if digest_field in subject:
                _require_digest64(
                    subject[digest_field], f"subject '{name}' {digest_field}"
                )
        if "suite" in subject and not isinstance(subject["suite"], str):
            raise ValueError(f"subject '{name}' suite must be a string")
        if "cases" in subject and (
            not isinstance(subject["cases"], int) or isinstance(subject["cases"], bool)
        ):
            raise ValueError(f"subject '{name}' cases must be an integer")
    metrics = freeze["reference_metrics"]
    if not isinstance(metrics, Mapping) or not metrics:
        raise ValueError("reference_metrics must be a non-empty mapping")
    for subject, values in metrics.items():
        if not isinstance(values, Mapping) or not values:
            raise ValueError(f"reference_metrics['{subject}'] must be non-empty")
        for metric, number in values.items():
            if not _is_number(number):
                raise ValueError(
                    f"reference_metrics['{subject}']['{metric}'] must be numeric"
                )
    _freeze_axes(freeze)
    _require_digest64(freeze["receipts_digest"], "receipts_digest")
    _require_digest64(freeze["source_prereg_digest"], "source_prereg_digest")
    _require_digest64(freeze["mint_receipts_digest"], "mint_receipts_digest")
    if not isinstance(freeze["journal_head_at_freeze"], str) or not freeze[
        "journal_head_at_freeze"
    ].strip():
        raise ValueError("journal_head_at_freeze must be a non-empty string")
    provenance = freeze["provenance"]
    if not isinstance(provenance, Mapping):
        raise ValueError("provenance must be a JSON object")
    unknown_provenance = sorted(set(provenance) - _PROVENANCE_KEYS)
    if unknown_provenance:
        raise ValueError(
            f"unknown key(s) in provenance: {', '.join(unknown_provenance)}"
        )
    if not isinstance(provenance.get("source"), str) or not provenance[
        "source"
    ].strip():
        raise ValueError("provenance source must be a non-empty string")
    _require_digest64(provenance.get("report_digest"), "provenance report_digest")
    return freeze


def validate_promotion_claim(value: object) -> dict[str, object]:
    """Validate the claim shape. Structural refusal at the boundary; the
    citation/pairing rules are judged by :func:`evaluate_promotion`."""

    if not isinstance(value, Mapping):
        raise ValueError("promotion claim must be a JSON object")
    claim = dict(value)
    unknown = sorted(set(claim) - _CLAIM_KEYS)
    missing = sorted(_CLAIM_KEYS - set(claim) - {"tau"})
    if unknown:
        raise ValueError(f"unknown key(s) in promotion claim: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"missing key(s) in promotion claim: {', '.join(missing)}")
    if claim["schema"] != CLAIM_SCHEMA:
        raise ValueError(f"promotion claim schema must be {CLAIM_SCHEMA}")
    for field in ("claim_id", "treatment"):
        if not isinstance(claim[field], str) or not claim[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    if not isinstance(claim["marginal_deltas"], list):
        raise ValueError("marginal_deltas must be a list")
    for index, delta in enumerate(claim["marginal_deltas"]):
        _validate_delta(delta, index)
    tau = claim.get("tau")
    if tau is not None:
        if not isinstance(tau, list):
            raise ValueError("tau must be a list when present")
        for entry in tau:
            if not isinstance(entry, Mapping) or set(entry) != _TAU_ENTRY_KEYS:
                raise ValueError("each tau entry carries exactly axis and value")
            if not _is_number(entry["value"]):
                raise ValueError("tau value must be numeric")
    _require_digest64(claim["evidence_receipts_digest"], "evidence_receipts_digest")
    return claim


def _validate_delta(delta: object, index: int) -> None:
    if not isinstance(delta, Mapping) or set(delta) != _DELTA_KEYS:
        raise ValueError(
            f"marginal_deltas[{index}] carries exactly axis, base, treatment, delta"
        )
    if not isinstance(delta["axis"], str) or _AXIS.fullmatch(delta["axis"]) is None:
        raise ValueError(f"marginal_deltas[{index}].axis must name subject.metric")
    for field in ("base", "treatment", "delta"):
        if not _is_number(delta[field]):
            raise ValueError(f"marginal_deltas[{index}].{field} must be numeric")


def derived_tau(freeze: Mapping[str, object], axis: str) -> float:
    """The only τ this package will ever answer: the freeze's own number.

    Report §3.2: any future calibration τ must come from the BASE freeze,
    never from a constant. There is no default, no clamping, no fallback —
    an axis the freeze does not carry raises, because a τ guessed is the
    L3 failure wearing a helper's name.
    """

    validated = validate_base_freeze(freeze)
    axes = _freeze_axes(validated)
    if axis not in axes:
        raise KeyError(
            f"the freeze carries no '{axis}' reference metric; a calibration "
            "tau may only be derived from a freeze axis, never assumed"
        )
    return axes[axis]


def _claim_schema_causes(claim: object) -> list[PromotionCause]:
    """Structural claim problems as refusal data, mirroring the kernel's
    grammar: rejections reach the caller as structured causes, not crashes."""

    if not isinstance(claim, Mapping):
        return [
            PromotionCause(
                "claim-schema", "a promotion claim must be a JSON object"
            )
        ]
    causes: list[PromotionCause] = []
    unknown = sorted(set(claim) - _CLAIM_KEYS)
    if unknown:
        causes.append(
            PromotionCause(
                "claim-schema",
                "unknown claim key(s): " + ", ".join(unknown),
            )
        )
    if claim.get("schema") != CLAIM_SCHEMA:
        causes.append(
            PromotionCause(
                "claim-schema",
                f"claim schema must be {CLAIM_SCHEMA}",
            )
        )
    if not isinstance(claim.get("claim_id"), str) or not claim.get("claim_id"):
        causes.append(
            PromotionCause("claim-schema", "claim_id must be a non-empty string")
        )
    deltas = claim.get("marginal_deltas")
    if isinstance(deltas, list):
        for index, delta in enumerate(deltas):
            try:
                _validate_delta(delta, index)
            except ValueError as exc:
                causes.append(PromotionCause("malformed-delta", str(exc)))
    return causes


def evaluate_promotion(
    claim: object,
    freeze: Mapping[str, object] | None,
    *,
    freeze_digest: str | None,
) -> PromotionDecision:
    """Judge one improvement claim against one validated base freeze.

    Pure: same claim, same freeze, same digest — the same decision bytes.
    ``freeze`` is ``None`` exactly when no citation resolved to a committed
    gauge: the claim is then refused on citation grounds, and the
    freeze-dependent checks (axes, pairing, τ) are skipped because there is
    nothing to check against — an absent gauge is never a default gauge.
    When a freeze is given it must already be valid
    (:func:`validate_base_freeze`); a caller that cannot validate it must
    refuse before this point, because a broken gauge has no gradable claims.
    The claim is judged leniently on structure and strictly on discipline:
    every missing field is a named refusal, and every rule the freeze exists
    to enforce is checked against the freeze's own numbers.
    """

    if freeze_digest is not None:
        _require_digest64(freeze_digest, "freeze_digest")
    if freeze is None:
        axes: dict[str, float] = {}
        freeze_id: str | None = None
    else:
        axes = _freeze_axes(validate_base_freeze(freeze))
        freeze_id = str(freeze["freeze_id"])
    causes = _claim_schema_causes(claim)
    claim_id = ""
    citation: object = None
    deltas: object = []
    if isinstance(claim, Mapping):
        raw_id = claim.get("claim_id")
        claim_id = raw_id if isinstance(raw_id, str) else ""
        citation = claim.get("base_freeze")
        deltas = claim.get("marginal_deltas")

    # The citation: an improvement claim with no gauge to be marginal
    # against is an assertion. A citation that is not a safe freeze id is
    # refused unsanitized — cleaning it would hand the naming walk to the
    # party being gated.
    if not isinstance(citation, str) or not citation.strip():
        causes.append(
            PromotionCause(
                "no-freeze-citation",
                "the claim names no base freeze; an improvement claim is "
                "gradable only against a committed freeze",
            )
        )
    elif not is_safe_freeze_id(citation):
        causes.append(
            PromotionCause(
                "no-freeze-citation",
                f"base_freeze citation is not a safe freeze id: {citation!r}",
            )
        )
    elif freeze is None or citation != freeze_id:
        causes.append(
            PromotionCause(
                "freeze-mismatch",
                f"the claim cites {citation!r}; the freeze answers "
                f"{freeze_id!r}",
            )
        )

    # The marginals: paired deltas on named axes, reconciled arithmetic.
    # The axis checks compare against the freeze's own numbers, so with no
    # gauge resolved they are skipped — the arithmetic check stays, because
    # a claim's three numbers must reconcile whatever they are graded by.
    if not isinstance(deltas, list) or not deltas:
        causes.append(
            PromotionCause(
                "no-marginal-deltas",
                "no paired marginal deltas; a promotion without measured "
                "deltas against the freeze is an assertion, not a result",
            )
        )
    else:
        for delta in deltas:
            if not isinstance(delta, Mapping) or set(delta) != _DELTA_KEYS:
                continue  # already named as malformed-delta above
            axis = delta["axis"]
            if freeze is not None:
                if axis not in axes:
                    causes.append(
                        PromotionCause(
                            "unknown-axis",
                            f"axis {axis!r} is not a reference metric of the "
                            "cited freeze",
                            axis=axis,
                        )
                    )
                    continue
                frozen = axes[axis]
                if float(delta["base"]) != frozen:
                    causes.append(
                        PromotionCause(
                            "unpaired-baseline",
                            f"axis {axis!r}: claim baseline {delta['base']} != "
                            f"freeze {frozen}; the baseline is the freeze's, "
                            "never the claim's",
                            axis=axis,
                        )
                    )
            if abs(
                (float(delta["treatment"]) - float(delta["base"]))
                - float(delta["delta"])
            ) > _ARITHMETIC_EPSILON:
                causes.append(
                    PromotionCause(
                        "delta-arithmetic",
                        f"axis {axis!r}: treatment {delta['treatment']} − "
                        f"base {delta['base']} != delta {delta['delta']}",
                        axis=axis,
                    )
                )

    # The τ rule: a calibration threshold is the freeze's derived number or
    # the claim is refused. This is L3's headstone — a constant τ that
    # exceeded the honest measured rate would false-FAIL every honest suite.
    # Like the axis checks, τ is judged against a gauge; with none resolved
    # there is no number to derive from, and the citation cause already
    # refuses the claim.
    tau_entries = claim.get("tau", []) if isinstance(claim, Mapping) else []
    if freeze is not None and isinstance(tau_entries, list):
        for entry in tau_entries:
            if not isinstance(entry, Mapping) or set(entry) != _TAU_ENTRY_KEYS:
                causes.append(
                    PromotionCause(
                        "tau-not-derived-from-freeze",
                        "each tau entry carries exactly axis and value",
                    )
                )
                continue
            axis, value = entry["axis"], entry["value"]
            frozen = axes.get(axis)
            if frozen is None or float(value) != frozen:
                causes.append(
                    PromotionCause(
                        "tau-not-derived-from-freeze",
                        f"tau cites {axis!r} with {value}; the freeze's "
                        f"value is {axes.get(axis, 'absent')} — τ must be "
                        "derived from the freeze, never a constant",
                        axis=axis if isinstance(axis, str) else None,
                    )
                )

    # The evidence binding: measured deltas without receipts are unbound,
    # and an unbound number is exactly what a fabricated marginal is.
    binding = (
        claim.get("evidence_receipts_digest") if isinstance(claim, Mapping) else None
    )
    if not isinstance(binding, str) or _DIGEST64.fullmatch(binding) is None:
        causes.append(
            PromotionCause(
                "no-evidence-binding",
                "no evidence receipts digest; measured deltas without "
                "receipts are unbound",
            )
        )

    ordered = tuple(
        sorted(causes, key=lambda c: (c.cause, c.axis or "", c.detail))
    )
    claimed_axes = tuple(
        sorted(
            {
                delta["axis"]
                for delta in (deltas if isinstance(deltas, list) else [])
                if isinstance(delta, Mapping) and isinstance(delta.get("axis"), str)
            }
        )
    )
    verdict = PromotionVerdict.ADMITTED if not ordered else PromotionVerdict.REFUSED
    return PromotionDecision(
        verdict=verdict,
        claim_id=claim_id,
        freeze_id=freeze_id,
        freeze_digest=freeze_digest,
        axes=claimed_axes,
        causes=ordered,
    )


def refused_malformed_freeze(
    citation: object, freeze_digest: str | None, detail: str
) -> PromotionDecision:
    """The decision for a cited freeze that does not parse as a gauge.

    A broken gauge refuses every claim against it — loudly, as data, so the
    receipt names the gauge and not the claim as the problem.
    """

    cause = PromotionCause(
        "freeze-malformed",
        f"the cited freeze does not validate as {FREEZE_SCHEMA}: {detail}",
    )
    claim_citation = citation if isinstance(citation, str) else ""
    return PromotionDecision(
        verdict=PromotionVerdict.REFUSED,
        claim_id="",
        freeze_id=claim_citation or None,
        freeze_digest=freeze_digest,
        axes=(),
        causes=(cause,),
    )


def decision_bytes(decision: PromotionDecision) -> bytes:
    """Canonical decision bytes: the machine contract, the only durable form."""

    return canonical_json_bytes(decision.as_record())
