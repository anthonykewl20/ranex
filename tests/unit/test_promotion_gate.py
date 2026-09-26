"""The base-freeze promotion gate: citation discipline, made to block.

SLICE-095 / oracle-science §5. The BASE freeze is the durable measurement
instrument; a treatment may promote only on paired MARGINAL deltas against
the freeze's own numbers, on axes the freeze names. This module is a
deterministic judge of that citation discipline — it is not the kernel, it
signs nothing, admits nothing, and its decisions never enter evidence. A
REFUSED promotion claim is a refused *claim about* improvement, not a gate
verdict over a subject tree.
"""

from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.promotion_gate import (
    CLAIM_SCHEMA,
    FREEZE_SCHEMA,
    derived_tau,
    evaluate_promotion,
    validate_base_freeze,
    validate_promotion_claim,
)

DIGEST = "sha256:" + "0" * 64
OTHER_DIGEST = "sha256:" + "1" * 64
REPORT_DIGEST = "sha256:" + "2" * 64
PREREG_DIGEST = "sha256:" + "3" * 64
FREEZE_DIGEST = "sha256:" + "4" * 64


def base_freeze() -> dict[str, object]:
    return {
        "schema": FREEZE_SCHEMA,
        "freeze_id": "base-freeze-v1",
        "minted": "2026-09-25",
        "kernel_commit": "638f7d8613fe5cbdeed96b89c103d5185ce39866",
        "kernel_digest": DIGEST,
        "vendored_src_tree": "sha256:" + "7" * 40,
        "subjects": {
            "six@1.17.0": {
                "commit": "ebd9b3af90247b8858d415a05e96e9ee61e48d07",
                "suite_manifest_digest": OTHER_DIGEST,
                "control_bank_digest": "sha256:" + "8" * 64,
            },
            "ranex-handbook": {
                "commit": "638f7d8613fe5cbdeed96b89c103d5185ce39866",
                "suite": "tests/unit/test_handbook_resolution.py",
                "cases": 58,
            },
        },
        "reference_metrics": {
            "six": {
                "raw_false_pass": 0.625,
                "honest_false_pass": 0.025,
                "kg_false_fail": 0.0,
                "suite_kill_rate_behavior_changing": 0.875,
                "cycle_seconds": 1.5,
                "tau_max_honest_kill_rate": 0.6,
            },
            "ranex-handbook": {"false_pass": 0.25, "suite_kill_rate": 0.75},
        },
        "receipts_digest": REPORT_DIGEST,
        "source_prereg_digest": PREREG_DIGEST,
        "journal_head_at_freeze": DIGEST,
        "mint_receipts_digest": OTHER_DIGEST,
        "provenance": {"source": "oracle-science scout report", "report_digest": REPORT_DIGEST},
    }


def admitted_claim() -> dict[str, object]:
    """The report's own C4 composition result, stated as a promotion claim."""

    return {
        "schema": CLAIM_SCHEMA,
        "claim_id": "c4-differential-composed",
        "treatment": "differential coexistence oracle (composed)",
        "base_freeze": "base-freeze-v1",
        "marginal_deltas": [
            {"axis": "six.raw_false_pass", "base": 0.625,
             "treatment": 0.6, "delta": -0.025},
            {"axis": "ranex-handbook.false_pass", "base": 0.25,
             "treatment": 0.0, "delta": -0.25},
        ],
        "tau": [{"axis": "six.tau_max_honest_kill_rate", "value": 0.6}],
        "evidence_receipts_digest": REPORT_DIGEST,
    }


class TestFreezeValidation:
    def test_accepts_the_durable_format(self) -> None:
        assert validate_base_freeze(base_freeze())["freeze_id"] == "base-freeze-v1"

    def test_refuses_unknown_schema(self) -> None:
        freeze = base_freeze()
        freeze["schema"] = "ranex-base-freeze-v2"
        with pytest.raises(ValueError, match="schema"):
            validate_base_freeze(freeze)

    def test_refuses_unknown_top_level_key(self) -> None:
        freeze = base_freeze()
        freeze["extra"] = 1
        with pytest.raises(ValueError, match="unknown key"):
            validate_base_freeze(freeze)

    def test_refuses_malformed_kernel_digest(self) -> None:
        freeze = base_freeze()
        freeze["kernel_digest"] = "sha256:zz"
        with pytest.raises(ValueError, match="kernel_digest"):
            validate_base_freeze(freeze)

    def test_refuses_non_numeric_reference_metric(self) -> None:
        freeze = base_freeze()
        freeze["reference_metrics"]["six"]["raw_false_pass"] = "25/40"
        with pytest.raises(ValueError, match="numeric"):
            validate_base_freeze(freeze)

    def test_refuses_axis_name_collision(self) -> None:
        # "six@1.1" + "raw" and "six@1" + "1.raw" flatten to one axis name,
        # so a claim citing it could not name one baseline.
        freeze = base_freeze()
        freeze["reference_metrics"]["six@1"] = {"1.raw": 0.5}
        freeze["reference_metrics"]["six@1.1"] = {"raw": 0.5}
        with pytest.raises(ValueError, match="collision"):
            validate_base_freeze(freeze)

    def test_refuses_boolean_metric(self) -> None:
        freeze = base_freeze()
        freeze["reference_metrics"]["six"]["kg_false_fail"] = False
        with pytest.raises(ValueError, match="numeric"):
            validate_base_freeze(freeze)


class TestClaimValidation:
    def test_accepts_a_well_formed_claim(self) -> None:
        assert validate_promotion_claim(admitted_claim())["claim_id"]

    def test_refuses_unknown_claim_key(self) -> None:
        claim = admitted_claim()
        claim["confidence"] = 0.9
        with pytest.raises(ValueError, match="unknown key"):
            validate_promotion_claim(claim)


class TestAdmission:
    def test_admits_a_paired_claim_with_named_axes(self) -> None:
        decision = evaluate_promotion(
            admitted_claim(), validate_base_freeze(base_freeze()),
            freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "ADMITTED"
        assert decision.causes == ()
        assert decision.axes == (
            "ranex-handbook.false_pass", "six.raw_false_pass",
        )
        record = decision.as_record()
        assert record["freeze_digest"] == FREEZE_DIGEST
        assert record["freeze_id"] == "base-freeze-v1"

    def test_decision_digest_is_canonical_and_stable(self) -> None:
        freeze = validate_base_freeze(base_freeze())
        digests = {
            evaluate_promotion(
                admitted_claim(), freeze, freeze_digest=FREEZE_DIGEST,
            ).decision_digest
            for _ in range(3)
        }
        assert len(digests) == 1
        assert digests == {"sha256:" + canonical_sha256(
            evaluate_promotion(
                admitted_claim(), freeze, freeze_digest=FREEZE_DIGEST,
            ).as_record()
        )}


class TestRefusal:
    def test_refuses_a_claim_without_freeze_citation(self) -> None:
        claim = admitted_claim()
        del claim["base_freeze"]
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["no-freeze-citation"]

    def test_refuses_an_uncited_claim_with_no_gauge_at_all(self) -> None:
        # The CLI's no-citation path: no freeze was resolved, so the claim
        # is refused on citation grounds and the freeze-dependent checks
        # (axes, pairing, τ) are skipped, not defaulted.
        claim = admitted_claim()
        del claim["base_freeze"]
        decision = evaluate_promotion(claim, None, freeze_digest=None)
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["no-freeze-citation"]
        assert decision.freeze_id is None
        assert decision.freeze_digest is None

    def test_refuses_an_unsafe_freeze_citation(self) -> None:
        claim = admitted_claim()
        claim["base_freeze"] = "../../etc/passwd"
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["no-freeze-citation"]

    def test_refuses_a_citation_the_freeze_does_not_answer(self) -> None:
        claim = admitted_claim()
        claim["base_freeze"] = "base-freeze-v9"
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["freeze-mismatch"]

    def test_refuses_a_claim_with_no_marginal_deltas(self) -> None:
        claim = admitted_claim()
        claim["marginal_deltas"] = []
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["no-marginal-deltas"]

    def test_refuses_an_axis_the_freeze_does_not_name(self) -> None:
        claim = admitted_claim()
        claim["marginal_deltas"][0]["axis"] = "six.token_cost"
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["unknown-axis"]

    def test_refuses_an_invented_baseline(self) -> None:
        # The L3 failure mode, inverted: a claim that grades itself against
        # a friendlier BASE than the freeze recorded. The fake arithmetic
        # reconciles — the only lie is the baseline.
        claim = admitted_claim()
        claim["marginal_deltas"][0]["base"] = 0.5
        claim["marginal_deltas"][0]["delta"] = 0.1  # 0.6 − 0.5, honestly stated
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["unpaired-baseline"]

    def test_refuses_delta_arithmetic_that_does_not_reconcile(self) -> None:
        claim = admitted_claim()
        claim["marginal_deltas"][0]["delta"] = -0.5
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert "delta-arithmetic" in [cause.cause for cause in decision.causes]

    def test_refuses_a_constant_tau(self) -> None:
        # Report §3.2: L3's preregistered τ=0.80 exceeded the honest measured
        # kill-rate and would have false-FAILed the honest suite. A τ that is
        # not the freeze's own number is refused, whatever its flavor.
        claim = admitted_claim()
        claim["tau"] = [{"axis": "six.tau_max_honest_kill_rate", "value": 0.8}]
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == [
            "tau-not-derived-from-freeze",
        ]

    def test_refuses_a_tau_citing_an_unknown_axis(self) -> None:
        claim = admitted_claim()
        claim["tau"] = [{"axis": "six.tau_max", "value": 0.6}]
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == [
            "tau-not-derived-from-freeze",
        ]

    def test_refuses_a_claim_without_evidence_binding(self) -> None:
        claim = admitted_claim()
        del claim["evidence_receipts_digest"]
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["no-evidence-binding"]

    def test_refuses_an_unknown_claim_schema(self) -> None:
        claim = admitted_claim()
        claim["schema"] = "ranex-promotion-claim-v2"
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert [cause.cause for cause in decision.causes] == ["claim-schema"]

    def test_reports_every_problem_at_once(self) -> None:
        claim = admitted_claim()
        del claim["base_freeze"]
        del claim["evidence_receipts_digest"]
        claim["marginal_deltas"][1]["base"] = 0.9
        claim["marginal_deltas"][1]["delta"] = -0.9  # reconciled to the lie
        decision = evaluate_promotion(
            claim, validate_base_freeze(base_freeze()), freeze_digest=FREEZE_DIGEST,
        )
        assert decision.verdict == "REFUSED"
        assert sorted(cause.cause for cause in decision.causes) == [
            "no-evidence-binding", "no-freeze-citation", "unpaired-baseline",
        ]


class TestTauDerivation:
    def test_tau_comes_from_the_freeze_and_nowhere_else(self) -> None:
        freeze = validate_base_freeze(base_freeze())
        assert derived_tau(freeze, "six.tau_max_honest_kill_rate") == 0.6

    def test_unknown_tau_axis_raises(self) -> None:
        with pytest.raises(KeyError):
            derived_tau(validate_base_freeze(base_freeze()), "six.tau_max")
