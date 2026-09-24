"""#110 — the deliberate-shortcut scanner satisfies (and fails) a real gate.

The claim under test is the kernel's own: `ranex markers` emits SARIF 2.1.0,
`ranex run` reduces it inside the materialisation, and `gate evaluate`
decides — with `evaluate()` and `verdict.py` untouched. The scanner is bound
as the installed console script, never a script the observed tree carries
(Correction 2); the last test refuses the catalog that tries otherwise.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main
from ranex.foundation.markers import scanned_files

ARTIFACT = "governance/markers.sarif"
MANIFEST = "governance/scan-manifest.json"
WELL_FORMED = "# ranex: global lock; per-account locks if throughput matters\n"
TRIGGERLESS = "# ranex: global lock\n"


def scanner() -> str:
    """The installed kernel's console script, by absolute path.

    The module form (`python -m ranex.foundation.markers`) resolves through
    the venv symlink to a base interpreter with no ranex in site-packages, so
    the console script — shebang and all — is the form a governed run binds.
    """

    candidate = Path(sys.executable).parent / "ranex"
    if not (candidate.is_file() and os.access(candidate, os.X_OK)):
        pytest.skip("ranex-markers: no installed console script on this host")
    return str(candidate)


def marker_command() -> list[str]:
    return [scanner(), "markers", "--output-format=sarif", f"--output-file={ARTIFACT}"]


def catalog(command: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: MARKERS_SANE\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(command)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n"
    )


def commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(repository), "config", key, value], check=True)
    (repository / "shortcut_probe.py").write_text(WELL_FORMED, encoding="utf-8")
    (repository / "governance").mkdir()
    (repository / "gates.yaml").write_text(catalog(marker_command()), encoding="utf-8")
    signing.write_keyring(repository)
    attach(repository, signing)
    commit(repository, "initial")
    return repository


def invoke(repo: Path, argv: list[str], producer: str | None = None) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("ranex.cli.main.governed_repository_root", lambda: repo.resolve())
        if producer is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv("RANEX_SIGNING_KEY", str(signing_for(repo).key_path(producer)))
        return main(argv)


def freeze(repo: Path, *declarations: str) -> int:
    argv = [
        "suite", "freeze",
        "--repository", ".",
        "--artifact", ARTIFACT,
        "--output", MANIFEST,
        "--results-reporter", "sarif-2.1.0",
    ]
    for path in scanned_files(repo):
        argv += ["--scan-scope", str(path)]
    for rule in ("ranex/marker-malformed", "ranex/marker-no-trigger",
                 "ranex/marker-shortcut"):
        argv += ["--scan-rule", rule]
    argv += list(declarations)
    argv += ["--", *marker_command()]
    return invoke(repo, argv)


def run(repo: Path, command: list[str] | None = None) -> int:
    return invoke(
        repo,
        [
            "run", "--claim", "scan", "--producer", "worker",
            "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--gate-catalog", "gates.yaml",
            "--", *(command if command is not None else marker_command()),
        ],
        producer="worker",
    )


def evaluate(repo: Path) -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD", "--repository", ".",
            "--gate-catalog", "gates.yaml", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--approver", "reviewer",
        ],
    )


def records(repo: Path) -> list[dict]:
    return json.loads((repo / "evidence.json").read_text(encoding="utf-8"))


def scan_identifier(repo: Path) -> str:
    return next(
        test_id
        for record in records(repo)
        for test_id, _ in (record.get("suite_results") or {}).get("non_passed", [])
        if "::" in test_id
    )


def clear_run_state(repo: Path) -> None:
    for name in ("evidence.json", "governance/journal.sqlite3"):
        (repo / name).unlink(missing_ok=True)


def test_a_well_formed_marker_is_a_note_and_the_gate_passes(repo: Path) -> None:
    assert freeze(repo) == 0
    commit(repo, "freeze the marker scan manifest")
    assert run(repo) == 0
    (record,) = records(repo)
    assert record["suite_results"]["non_passed"] == []
    assert not (repo / ARTIFACT).exists(), "the artifact lives and dies inside the run"
    assert evaluate(repo) == 0


def test_a_trigger_less_marker_fails_the_gate_naming_the_finding(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (repo / "shortcut_probe.py").write_text(TRIGGERLESS, encoding="utf-8")
    commit(repo, "a shortcut with no trigger rots silently")
    assert freeze(repo) == 0
    commit(repo, "freeze the marker scan manifest")
    assert run(repo) == 0, "the scanner reports through its artifact and exits 0"
    identifier = scan_identifier(repo)
    assert identifier.startswith("shortcut_probe.py::ranex/marker-no-trigger::")
    assert evaluate(repo) == 1
    assert "shortcut_probe.py" in capsys.readouterr().out


def test_an_accepted_error_finding_passes_and_the_declaration_is_the_difference(
    repo: Path,
) -> None:
    (repo / "shortcut_probe.py").write_text(TRIGGERLESS, encoding="utf-8")
    commit(repo, "a shortcut with no trigger")
    assert freeze(repo) == 0
    commit(repo, "freeze")
    assert run(repo) == 0
    identifier = scan_identifier(repo)
    clear_run_state(repo)
    subprocess.run(["git", "-C", str(repo), "rm", "-q", MANIFEST], check=True)
    commit(repo, "drop the manifest to refreeze with acceptance")
    assert freeze(repo, "--accepted", f"{identifier}=review answered for it") == 0
    commit(repo, "freeze with the accepted declaration")
    assert run(repo) == 0
    assert evaluate(repo) == 0, "acceptance is a committed, reviewable act"
    (last,) = [r for r in records(repo) if r["claim_id"] == "scan"][-1:]
    assert dict(last["suite_results"]["non_passed"]) == {identifier: "skipped"}


def test_a_catalog_binding_the_scanner_to_an_in_tree_script_is_refused(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Correction 2's arm 8, at the layer where the binding is authored."""

    (repo / "neuter.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    bound = ["/usr/bin/python3", "neuter.py",
             "--output-format=sarif", f"--output-file={ARTIFACT}"]
    (repo / "gates.yaml").write_text(catalog(bound), encoding="utf-8")
    commit(repo, "bind the scan claim to an in-tree script")
    assert run(repo, bound) == 2
    output = capsys.readouterr()
    assert "script operand" in output.err, output.err
    assert evaluate(repo) == 2, "a gate that cannot load cannot pass"
