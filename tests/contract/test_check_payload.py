"""Contract arms for the check-run payload: the shape GitHub is promised.

The name `ranex/acceptance` is the context a repository ruleset will
require (pinned again, with the ruleset recipe, in the README contract when
the receiver slice lands); this file freezes what the payload itself must
carry, so the publisher cannot drift from the documented check-run shape.
"""

from __future__ import annotations

import re

from ranex.github_app.acceptance import (
    ABSENT_CODE,
    ACCEPTED,
    REJECTED_PREFIX,
    Acceptance,
)
from ranex.github_app.binding import PrHeadBinding, subject_digest_for_tree
from ranex.github_app.publisher import (
    CHECK_NAME,
    check_run_body,
    decide_check,
)
from ranex.governed_execution.verdict_reader import ReadState

_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def binding() -> PrHeadBinding:
    tree = "e" * 40
    return PrHeadBinding(
        head_sha="9" * 40, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )


def test_the_check_name_is_the_context_a_ruleset_requires() -> None:
    assert CHECK_NAME == "ranex/acceptance"


def test_the_payload_names_the_head_and_closes_the_run() -> None:
    record = {
        "verdict": "PASS",
        "gate_id": "landing",
        "subject_digest": binding().subject_digest,
        "record_digest": "sha256:" + "0" * 64,
    }
    decision = decide_check(binding(), Acceptance(ACCEPTED, ReadState.VERIFIED, record))
    body = check_run_body(
        binding(), decision, started_at=1.0, completed_at=2.0
    )

    assert set(body) == {
        "name", "head_sha", "status", "conclusion", "output",
        "started_at", "completed_at",
    }
    assert body["name"] == CHECK_NAME
    assert body["head_sha"] == binding().head_sha
    # A conclusion implies completion; the payload says both, explicitly.
    assert body["status"] == "completed"
    assert body["conclusion"] == "success"
    assert _TIMESTAMP.fullmatch(body["started_at"])
    assert _TIMESTAMP.fullmatch(body["completed_at"])


def test_the_output_carries_the_binding_not_just_the_verdict() -> None:
    acceptance = Acceptance(ABSENT_CODE, ReadState.ABSENT)
    decision = decide_check(binding(), acceptance)
    combined = decision.summary + decision.text
    assert binding().subject_digest in combined
    assert binding().tree in combined
    assert binding().head_sha in combined


def test_every_conclusion_is_one_of_the_documented_vocabulary() -> None:
    vocabulary = {"success", "failure", "neutral", "cancelled", "skipped",
                  "timed_out", "action_required"}
    acceptances = [
        Acceptance(ACCEPTED, ReadState.VERIFIED, {"verdict": "PASS"}),
        Acceptance(ACCEPTED, ReadState.VERIFIED, {"verdict": "FAIL"}),
        Acceptance(ABSENT_CODE, ReadState.ABSENT),
        Acceptance(f"{REJECTED_PREFIX}bad-signature", ReadState.BAD_SIGNATURE),
    ]
    for acceptance in acceptances:
        assert decide_check(binding(), acceptance).conclusion in vocabulary
