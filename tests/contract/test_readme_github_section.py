"""Contract arms for the README's GitHub acceptance loop documentation.

The docs set is closed (`test_docs_discipline.py`), so the App creation
recipe and the ruleset recipe live in README — and what an operator will
copy from them is pinned here: the check context name, the App pinning,
the permissions, the event subscription, and the listener command.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def readme() -> str:
    return (REPO_ROOT / "README.md").read_text(encoding="utf-8")


def test_the_readme_carries_the_acceptance_loop_section() -> None:
    assert "## The GitHub acceptance loop" in readme()


def test_the_check_context_name_is_pinned() -> None:
    text = readme()
    assert '`ranex/acceptance`' in text


def test_the_ruleset_recipe_pins_the_app_as_the_check_source() -> None:
    text = readme()
    assert '"type": "required_status_checks"' in text
    assert '"context": "ranex/acceptance"' in text
    assert "integration_id" in text


def test_the_app_recipe_names_the_documented_permissions_and_events() -> None:
    text = readme()
    assert "Checks: Read & write" in text
    assert "Contents: Read-only" in text
    assert "Pull requests: Read-only" in text
    assert "Pull request" in text


def test_the_listener_recipe_is_the_shipped_command() -> None:
    text = readme()
    assert "ranex github listen" in text
    assert "smee.io" in text
    assert "X-Hub-Signature-256" in text


def test_the_publisher_never_evaluates_is_stated() -> None:
    text = readme()
    assert "publisher, never a judge" in text
    assert "action_required" in text
