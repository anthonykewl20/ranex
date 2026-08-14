"""The CI workflow is itself a governance boundary.

This test checks the fixed workflow path, its review-relevant triggers, the
least-privilege test and scan jobs, immutable action revisions, and the exact
test command.  The pytest step is deliberately an allowlist: any legitimate
future addition to it requires changing this test.  That friction is
intentional, because step-level settings can otherwise make a byte-identical
command non-blocking.  This test does not cover GitHub Actions behaviour outside
this workflow, such as repository rulesets, branch protection, runner
availability, or a compromised pinned action.
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
    "github/codeql-action/upload-sarif": "ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd",
}


def test_ci_workflow_runs_the_full_suite_on_every_push_and_pull_request() -> None:
    """CI must be a real, minimal gate rather than an aspirational YAML file."""

    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)

    assert isinstance(workflow, dict)
    # PyYAML follows YAML 1.1, under which the unquoted GitHub Actions key
    # ``on`` becomes True. Accept only that parser normalization or the literal.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    assert set(triggers) == {"push", "pull_request", "schedule"}
    assert triggers["schedule"] == [{"cron": "0 9 * * 1"}]

    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict)
    assert set(jobs) == {"test", "osv-scan"}
    job = jobs["test"]
    assert set(job) == {"runs-on", "timeout-minutes", "permissions", "steps"}
    assert job["timeout-minutes"] == 10
    assert job["permissions"] == {"contents": "read"}

    steps = job["steps"]
    assert len(steps) == 6
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

    # Lint and type gates run before the suite so a style/type regression fails
    # fast. Both run via uvx with pinned versions; they do not touch uv.lock.
    assert steps[2] == {"name": "Lint (ruff)", "run": "uvx ruff@0.16.2 check src tests"}
    assert steps[3] == {
        "name": "Type check (pyrefly)",
        "run": (
            "uv run --frozen --with \"pyrefly==1.2.0\" pyrefly check src/ranex "
            "--project-excludes '**/verdict.py'"
        ),
    }
    assert steps[-2] == {"run": "uv run --frozen pytest -q -rs"}
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
            "uv run --frozen python -m coverage run --source=src/ranex -m pytest -q\n"
            "uv run --frozen python -m coverage xml -o coverage.xml\n"
            "uv run --frozen diff-cover coverage.xml "
            '--compare-branch="$DIFF_COVER_COMPARE_BRANCH" --fail-under=100\n'
        ),
    }

    osv_scan = jobs["osv-scan"]
    assert set(osv_scan) == {"runs-on", "timeout-minutes", "permissions", "steps"}
    assert osv_scan["runs-on"] == "ubuntu-latest"
    assert osv_scan["timeout-minutes"] == 10
    assert osv_scan["permissions"] == {"contents": "read", "security-events": "write"}

    all_osv_steps = osv_scan["steps"]
    osv_action_steps = [step for step in all_osv_steps if "uses" in step]
    assert len(osv_action_steps) == 2
    for step in osv_action_steps:
        action, revision = step["uses"].split("@", maxsplit=1)
        assert _SHA.fullmatch(revision), f"{action} must be pinned to a 40-hex SHA"
        assert _ACTIONS[action] == revision

    # The checkout action above is separately pinned. The scan-specific allowlist
    # below must not admit an unreviewed operational step.
    osv_steps = all_osv_steps[1:]
    assert len(osv_steps) == 4
    assert osv_steps[0] == {
        "name": "Install osv-scanner (pinned)",
        "run": (
            "curl -fsSL https://github.com/google/osv-scanner/releases/download/v2.5.0/"
            "osv-scanner_linux_amd64 -o /tmp/osv-scanner\n"
            'echo "edcfc41d257db36148f065055655fe3fcfc434b0b423ea67468a84c207524e0c  '
            '/tmp/osv-scanner" | sha256sum -c -\n'
            "chmod +x /tmp/osv-scanner\n"
        ),
    }
    assert osv_steps[1] == {
        "name": "Scan the committed lockfile",
        "id": "scan",
        "run": (
            "set +e\n"
            "/tmp/osv-scanner --lockfile=uv.lock --format=sarif --output=osv.sarif\n"
            "exit_code=$?\n"
            'echo "exit=$exit_code" >> "$GITHUB_OUTPUT"\n'
            "exit 0\n"
        ),
    }
    assert (
        "        # Upload only result-bearing scans: 0 = packages found and clean, 1 = "
        'findings. 128 means "no packages found" — a successful run that scanned nothing, '
        "whose empty SARIF must NOT be published as clean. Every other non-zero is a scanner "
        "failure. All fail closed below.\n"
        "        run: |\n"
    ) in workflow_text
    assert osv_steps[2] == {
        "name": "Upload SARIF",
        "if": (
            "!cancelled() && (steps.scan.outputs.exit == '0' || "
            "steps.scan.outputs.exit == '1') && (github.event_name != "
            "'pull_request' || github.event.pull_request.head.repo.full_name == "
            "github.repository)"
        ),
        "uses": "github/codeql-action/upload-sarif@ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd",
        "with": {
            "sarif_file": "osv.sarif",
            "category": ".github/workflows/ci.yml:osv-scan",
        },
    }
    assert (
        "        # Publish only result-bearing scans (0/1) — exit 128 is an empty scan that "
        "must not masquerade as clean — and only when this run can write to the Security tab "
        "(fork PRs get a read-only token and would 403).\n"
        "        uses: github/codeql-action/upload-sarif@"
        "ff2f1c621b7f889edc0d3c761ac2e6a3f8cdb0dd\n"
    ) in workflow_text

    assert osv_steps[-1] == {
        "name": "Findings block the scan",
        "if": "steps.scan.outputs.exit != '0'",
        "run": (
            'echo "::error::osv-scanner exit ${{ steps.scan.outputs.exit }} — '
            "vulnerabilities or scanner failure; see the Security tab\"\nexit 1\n"
        ),
    }
