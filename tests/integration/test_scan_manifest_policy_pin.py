"""A scan claim's manifest is trust root, so the receiver pins it too.

`accepted` decides as much as the gate catalog does: a head that quietly adds
a finding to it has changed the policy under which the verdict is published.
The receiver already refuses a rewritten catalog or keyring across heads; this
is that refusal extended to the file a scan claim actually reads.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.github_app.binding import bind_pr_head
from ranex.github_app.evaluation import EvidenceEvaluator

CATALOG = """
gates:
  - gate_id: landing
    rule_id: SCAN_CLEAN
    blocking: true
    required_claims:
      - claim_id: scan
        command: ["/usr/bin/ruff", "check", "--output-format=sarif", "--output-file=governance/scan.sarif", "pkg"]
        results_artifact: governance/scan.sarif
        results_reporter: sarif-2.1.0
        results_manifest: governance/scan-manifest.json
"""

MANIFEST = {
    "scope": ["pkg/mod.py"],
    "rules": ["F401"],
    "blocking_levels": ["error"],
    "accepted": {},
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repository = tmp_path / "scanned"
    (repository / "governance").mkdir(parents=True)
    (repository / "pkg").mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        git(repository, "config", key, value)
    (repository / "pkg/mod.py").write_text("x = 1\n", encoding="utf-8")
    (repository / "governance/gates.yaml").write_text(CATALOG, encoding="utf-8")
    (repository / "governance/producers.yaml").write_text(
        "producers: []\n", encoding="utf-8"
    )
    (repository / "governance/scan-manifest.json").write_bytes(
        canonical_json_bytes(MANIFEST)
    )
    git(repository, "add", "-A")
    git(repository, "commit", "-q", "-m", "governed by a scan claim")
    return repository


def evaluator_for(repo: Path) -> EvidenceEvaluator:
    return EvidenceEvaluator(
        repo,
        "governance/evidence.json",
        "landing",
        "governance/gates.yaml",
        "governance/producers.yaml",
        "governance/suite_manifest.json",
        "pilot",
        repo / "governance/verdicts",
        repo / "key.pem",
        repo / ".local/evaluation",
    )


def test_the_scan_manifest_is_pinned_and_the_absent_suite_manifest_is_not(repo: Path) -> None:
    """A repository judged only by a scan need not carry a suite manifest."""

    evaluator = evaluator_for(repo)
    assert "governance/scan-manifest.json" in evaluator._policy_names
    assert "governance/suite_manifest.json" not in evaluator._policy_names


def test_a_head_that_widens_accepted_is_refused(repo: Path) -> None:
    evaluator = evaluator_for(repo)
    widened = {**MANIFEST, "accepted": {f"pkg/mod.py::F401::{'0' * 64}": "unreviewed"}}
    (repo / "governance/scan-manifest.json").write_bytes(canonical_json_bytes(widened))
    git(repo, "commit", "-qam", "widen accepted on the head")
    binding = bind_pr_head(repo, git(repo, "rev-parse", "HEAD"))
    with pytest.raises(ValueError, match="E-GITHUB-EVALUATION-POLICY-CHANGED"):
        evaluator(binding)


def test_an_unchanged_head_is_not_refused(repo: Path) -> None:
    """The control: the refusal must be about the manifest, not about any commit."""

    evaluator = evaluator_for(repo)
    (repo / "pkg/other.py").write_text("y = 2\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "unrelated change")
    binding = bind_pr_head(repo, git(repo, "rev-parse", "HEAD"))
    evaluator(binding)  # no evidence file: returns quietly, having checked policy
