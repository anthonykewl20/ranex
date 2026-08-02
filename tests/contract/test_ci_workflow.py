"""The CI workflow is itself a governance boundary.

This test checks the fixed workflow path, both review-relevant triggers, its
single least-privilege test job, immutable action revisions, and the exact test
command.  The pytest step is deliberately an allowlist: any legitimate future
addition to it requires changing this test.  That friction is intentional,
because step-level settings can otherwise make a byte-identical command
non-blocking.  This test does not cover GitHub Actions behaviour outside this
workflow, such as repository rulesets, branch protection, runner availability,
or a compromised pinned action.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
_SHA = re.compile(r"^[0-9a-f]{40}$")

_ACTIONS = {
    "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
    "astral-sh/setup-uv": "c771a70e6277c0a99b617c7a806ffedaca235ff9",
}


def test_ci_workflow_runs_the_full_suite_on_every_push_and_pull_request() -> None:
    """CI must be a real, minimal gate rather than an aspirational YAML file."""

    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert isinstance(workflow, dict)
    # PyYAML follows YAML 1.1, under which the unquoted GitHub Actions key
    # ``on`` becomes True. Accept only that parser normalization or the literal.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    assert set(triggers) == {"push", "pull_request"}

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    assert set(jobs) == {"test"}
    job = jobs["test"]
    assert set(job) == {"runs-on", "timeout-minutes", "permissions", "steps"}
    assert job["timeout-minutes"] == 10
    assert job["permissions"] == {"contents": "read"}

    steps = job["steps"]
    assert len(steps) == 4
    action_steps = [step for step in steps if "uses" in step]
    assert len(action_steps) == 2
    for step in action_steps:
        action, revision = step["uses"].split("@", maxsplit=1)
        assert _SHA.fullmatch(revision), f"{action} must be pinned to a 40-hex SHA"
        assert _ACTIONS[action] == revision

    setup_uv = next(step for step in action_steps if step["uses"].startswith("astral-sh/setup-uv@"))
    assert setup_uv.get("with") == {"python-version": "3.14"}

    checkout = next(step for step in action_steps if step["uses"].startswith("actions/checkout@"))
    assert checkout.get("with") == {"fetch-depth": 0}

    assert steps[-2] == {"run": "uv run pytest -q -rs"}
    assert steps[-1] == {
        "name": "Require coverage for changed lines",
        "env": {
            "DIFF_COVER_COMPARE_BRANCH": (
                "${{ github.event_name == 'pull_request' && "
                "github.event.pull_request.base.sha || github.event.before != "
                "'0000000000000000000000000000000000000000' && "
                "github.event.before || format('origin/{0}', "
                "github.event.repository.default_branch) }}"
            )
        },
        "run": (
            "uv run python -m coverage run --source=src/ranex -m pytest -q\n"
            "uv run python -m coverage xml -o coverage.xml\n"
            "uv run diff-cover coverage.xml "
            '--compare-branch="$DIFF_COVER_COMPARE_BRANCH" --fail-under=100\n'
        ),
    }
