"""The conclusion mapping: exactly one road to `success`.

`ranex/acceptance` says `success` only when `read_verdict` verified a record
under the committed verdict signer and that record says PASS. A failing
verdict, a rejected verdict, and no verdict at all are three different loud
outcomes — `failure`, `failure` naming the reader state, `action_required` —
and a test reaches for `success` from every other direction to prove the
mapping is closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from ranex.github_app.acceptance import ABSENT_CODE, REJECTED_PREFIX, Acceptance
from ranex.github_app.binding import PrHeadBinding
from ranex.github_app.client import GitHubClient

CHECK_NAME = "ranex/acceptance"

CONCLUSION_SUCCESS = "success"
CONCLUSION_FAILURE = "failure"
CONCLUSION_ACTION_REQUIRED = "action_required"


def _timestamp(moment: float) -> str:
    return datetime.fromtimestamp(moment, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True, slots=True)
class CheckDecision:
    """What the check says, independent of how it reaches GitHub."""

    conclusion: str
    title: str
    summary: str
    text: str


def decide_check(binding: PrHeadBinding, acceptance: Acceptance) -> CheckDecision:
    digest_line = (
        f"subject={binding.subject_digest}  tree={binding.tree}"
    )
    if acceptance.publishable:
        record = acceptance.record or {}
        verdict = record.get("verdict")
        if verdict == "PASS":
            return CheckDecision(
                conclusion=CONCLUSION_SUCCESS,
                title="PASS",
                summary=f"PASS  gate={record.get('gate_id')}  {digest_line}",
                text=(
                    f"record_digest={record.get('record_digest')}\n"
                    f"head_sha={binding.head_sha}\n{digest_line}"
                ),
            )
        return CheckDecision(
            conclusion=CONCLUSION_FAILURE,
            title="FAIL",
            summary=f"FAIL  gate={record.get('gate_id')}  rule={record.get('failing_rule')}",
            text=(
                f"missing_claims={record.get('missing_claims')}\n"
                f"record_digest={record.get('record_digest')}\n{digest_line}"
            ),
        )
    if acceptance.code == ABSENT_CODE:
        return CheckDecision(
            conclusion=CONCLUSION_ACTION_REQUIRED,
            title="No verdict for this head",
            summary=(
                "No signed verdict publication exists for this pull-request "
                "head's tree. Run the gate; the App publishes what it verifies."
            ),
            text=f"head_sha={binding.head_sha}\n{digest_line}",
        )
    state = acceptance.code.removeprefix(REJECTED_PREFIX)
    return CheckDecision(
        conclusion=CONCLUSION_FAILURE,
        title=f"Verdict rejected: {state}",
        summary=f"The verdict publication was refused by the reader: {state}.",
        text=f"reader_state={state}\nhead_sha={binding.head_sha}\n{digest_line}",
    )


def check_run_body(
    binding: PrHeadBinding,
    decision: CheckDecision,
    *,
    started_at: float,
    completed_at: float,
) -> dict[str, Any]:
    """The exact payload `POST /repos/{owner}/{repo}/check-runs` receives."""

    return {
        "name": CHECK_NAME,
        "head_sha": binding.head_sha,
        "status": "completed",
        "conclusion": decision.conclusion,
        "output": {
            "title": decision.title,
            "summary": decision.summary,
            "text": decision.text,
        },
        "started_at": _timestamp(started_at),
        "completed_at": _timestamp(completed_at),
    }


def publish_check(
    client: GitHubClient,
    installation_id: int,
    repository: str,
    binding: PrHeadBinding,
    acceptance: Acceptance,
    *,
    started_at: float,
    completed_at: float,
) -> tuple[CheckDecision, Mapping[str, Any]]:
    """Publish one check and return the decision that produced it."""

    decision = decide_check(binding, acceptance)
    response = client.create_check_run(
        installation_id,
        repository,
        check_run_body(
            binding, decision, started_at=started_at, completed_at=completed_at
        ),
    )
    return decision, response
