"""A real Ranex parent proves the delegated patch's suite is discriminating."""

from __future__ import annotations

from pathlib import Path

from _provider_neutral_subject import (
    BASE_COMMIT,
    PATCH_COMMIT,
    assert_nested_hermetic_boundary,
    git,
    materialize,
    nested_hermetic_boundary,
    run_focused,
)


def test_real_ranex_parent_is_red_before_delegation(tmp_path: Path) -> None:
    if nested_hermetic_boundary():
        assert_nested_hermetic_boundary()
        return
    subject = materialize(tmp_path, commit=BASE_COMMIT)
    assert git(subject, "rev-parse", "HEAD") == BASE_COMMIT
    assert git(subject, "rev-parse", f"{PATCH_COMMIT}^") == BASE_COMMIT

    completed = run_focused(subject)

    assert completed.returncode == 1
    assert "37 failed" in completed.stdout
    assert "11 passed" in completed.stdout


def test_real_ranex_patch_is_nonempty_and_reviewable(tmp_path: Path) -> None:
    if nested_hermetic_boundary():
        assert_nested_hermetic_boundary()
        return
    subject = materialize(tmp_path, commit=BASE_COMMIT)
    changed = git(
        subject,
        "diff",
        "--name-only",
        f"{BASE_COMMIT}..{PATCH_COMMIT}",
    ).splitlines()

    assert len(changed) == 53
    assert "src/ranex/foundation/dynamic_runtime.py" in changed
    assert "tests/integration/test_slice072_dynamic_runtime_contract.py" in changed
