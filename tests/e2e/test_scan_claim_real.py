"""#97 — a real scanner satisfies (and fails) a real gate, on real bytes.

The claim under test is the ecosystem one: a deterministic scanner emits SARIF
2.1.0, `ranex run` reduces it inside the materialisation, and `gate evaluate`
decides — with `verdict.py` untouched and no bespoke loader anywhere.

Every arm here runs the real CLI over a real Git repository with a real
producer key, and the scanner is really ruff. The negative controls are the
point: a clean tree that passes proves only that nothing objected, so each
expectation is paired with the failure it is supposed to catch — a real
violation, a stale subject, a widened manifest, a forged region, and a scanner
that declares its own failure while exiting 0.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_json_bytes

ARTIFACT = "governance/scan.sarif"
MANIFEST = "governance/scan-manifest.json"
SCOPE = "pkg/mod.py"
CLEAN = "def answer():\n    return 42\n"
VIOLATION = "import os\n\n\ndef answer():\n    return 42\n"

#: A producer that emits whatever SARIF a test hands it, under the same argv
#: shape the catalog demands of a scanner. It is how the hostile-report arms
#: are run without pretending a real scanner would cooperate.
FORGER = (
    "import json, sys\n"
    "out = [a for a in sys.argv if a.startswith('--output-file=')][0].split('=', 1)[1]\n"
    "open(out, 'w').write(open('forged.json').read())\n"
)


def ruff_binary() -> str:
    found = shutil.which("ruff")
    if found is None:
        pytest.skip("ranex-prereq:ruff: no ruff on PATH, so no real SARIF producer")
    return found


def catalog(command: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: SCAN_CLEAN\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(command)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n"
    )


def scan_command(binary: str, *, exit_zero: bool = False) -> list[str]:
    """ruff's real argv.

    `--exit-zero` is a policy choice, not a convenience. `Evidence.satisfies`
    requires the bound command to have exited 0, so a scanner that exits 1 on
    any finding decides the claim by its exit code before the manifest is ever
    consulted — and manifest-level acceptance is then unreachable. A claim that
    wants `accepted` to mean anything binds a scanner that reports through its
    artifact and exits 0; what blocks is then the frozen manifest, which is the
    whole point of the producer evidence plane.
    """

    return [binary, "check", "--no-cache", "--isolated", "--select=F401",
            *(["--exit-zero"] if exit_zero else []),
            "--output-format=sarif", f"--output-file={ARTIFACT}", "pkg"]


def commit(repo: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    repository = tmp_path / "scanned"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(repository), "config", key, value], check=True)
    (repository / "pkg").mkdir()
    (repository / SCOPE).write_text(CLEAN, encoding="utf-8")
    (repository / "governance").mkdir()
    (repository / "gates.yaml").write_text(catalog(scan_command(ruff_binary())), encoding="utf-8")
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


def freeze(repo: Path, *declarations: str, exit_zero: bool = False) -> int:
    return invoke(
        repo,
        [
            "suite", "freeze",
            "--repository", ".",
            "--artifact", ARTIFACT,
            "--output", MANIFEST,
            "--results-reporter", "sarif-2.1.0",
            "--scan-scope", SCOPE,
            "--scan-rule", "F401",
            *declarations,
            "--", *scan_command(ruff_binary(), exit_zero=exit_zero),
        ],
    )


def run(repo: Path, command: list[str] | None = None) -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", "scan",
            "--producer", "worker",
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--gate-catalog", "gates.yaml",
            "--", *(command if command is not None else scan_command(ruff_binary())),
        ],
        producer="worker",
    )


def evaluate(repo: Path) -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--approver", "reviewer",
        ],
    )


def records(repo: Path) -> list[dict]:
    return json.loads((repo / "evidence.json").read_text(encoding="utf-8"))


def frozen(repo: Path) -> Path:
    """A frozen scan manifest, committed, over the tree as it stands."""

    assert freeze(repo) == 0
    commit(repo, "freeze the scan manifest")
    return repo / MANIFEST


# --- the positive control and its negative twin -----------------------------


def test_a_clean_scan_satisfies_the_gate(repo: Path) -> None:
    frozen(repo)
    assert run(repo) == 0
    (record,) = records(repo)
    assert record["suite_results"]["non_passed"] == []
    assert record["suite_results"]["missing"] == []
    assert not (repo / ARTIFACT).exists(), "the artifact lives and dies inside the run"
    assert evaluate(repo) == 0


def test_a_real_violation_blocks_and_the_finding_is_named(repo: Path, capsys) -> None:
    """The negative control: one real unused import, and the gate must refuse."""

    frozen(repo)
    (repo / SCOPE).write_text(VIOLATION, encoding="utf-8")
    commit(repo, "introduce a real F401")
    assert run(repo) == 1, "ruff exits 1 on a finding, and `run` returns it verbatim"
    (record,) = records(repo)
    failed = dict(record["suite_results"]["non_passed"])
    assert failed[SCOPE] == "failed"
    identifier = next(key for key in failed if key != SCOPE)
    assert identifier.startswith(f"{SCOPE}::F401::")
    assert evaluate(repo) != 0
    assert "scan" in capsys.readouterr().out


def clear_run_state(repo: Path) -> None:
    """Drop what a run and an evaluation leave behind, so a freeze can follow.

    `suite freeze` refuses a dirty tree, and both the evidence file and the
    journal are untracked products of the arms above. Removing them is the
    operator's own sequence — freeze on a clean tree — not a workaround.
    """

    for name in ("evidence.json", "governance/journal.sqlite3"):
        (repo / name).unlink(missing_ok=True)


def observed_finding(repo: Path) -> str:
    return next(
        key for key, _ in records(repo)[-1]["suite_results"]["non_passed"] if "::" in key
    )


def rebind(repo: Path, *, exit_zero: bool) -> list[str]:
    command = scan_command(ruff_binary(), exit_zero=exit_zero)
    (repo / "gates.yaml").write_text(catalog(command), encoding="utf-8")
    return command


def test_an_accepted_finding_passes_only_when_the_scanner_exits_zero(repo: Path) -> None:
    """Acceptance is a reviewed declaration over a finding the run really saw."""

    command = rebind(repo, exit_zero=True)
    (repo / SCOPE).write_text(VIOLATION, encoding="utf-8")
    commit(repo, "a real F401, reported through the artifact")
    assert freeze(repo, exit_zero=True) == 0
    commit(repo, "freeze over the violating tree")
    assert json.loads((repo / MANIFEST).read_text(encoding="utf-8"))["accepted"] == {}
    assert run(repo, command) == 0
    observed = observed_finding(repo)
    assert evaluate(repo) != 0, "an unaccepted finding blocks even at exit 0"

    clear_run_state(repo)
    assert freeze(repo, "--accepted", f"{observed}=reviewed: the import is load-bearing",
                  exit_zero=True) == 0
    commit(repo, "accept the reviewed finding")
    assert run(repo, command) == 0
    (record,) = records(repo)
    assert record["suite_results"]["non_passed"] == [[observed, "skipped"]], (
        "acceptance is policy, not silence: the scanner still reports it"
    )
    assert evaluate(repo) == 0


def test_exit_zero_never_makes_a_finding_pass_by_itself(repo: Path, capsys) -> None:
    """The control the arm above depends on: the artifact decides, not the exit code."""

    command = rebind(repo, exit_zero=True)
    commit(repo, "bind an exit-zero scanner")
    assert freeze(repo, exit_zero=True) == 0
    commit(repo, "freeze a clean tree")
    (repo / SCOPE).write_text(VIOLATION, encoding="utf-8")
    commit(repo, "introduce a real F401")
    assert run(repo, command) == 0, "the scanner is happy; the gate must not be"
    assert dict(records(repo)[0]["suite_results"]["non_passed"])[SCOPE] == "failed"
    assert evaluate(repo) != 0
    assert "scan" in capsys.readouterr().out


def test_acceptance_cannot_rescue_a_scanner_that_exits_nonzero(repo: Path) -> None:
    """The constraint, pinned where it will be found.

    `evaluate()` requires exit 0 before it looks at a summary at all, so under
    ruff's default exit code an accepted finding is still a failed claim. That
    is not a defect to route around — it is why `--exit-zero` above is a
    reviewed part of the bound argv rather than a flag someone may add later.
    """

    (repo / SCOPE).write_text(VIOLATION, encoding="utf-8")
    commit(repo, "introduce a real F401")
    assert freeze(repo) == 0
    commit(repo, "freeze over the violating tree")
    assert run(repo) == 1
    observed = observed_finding(repo)
    clear_run_state(repo)
    assert freeze(repo, "--accepted", f"{observed}=reviewed") == 0
    commit(repo, "accept the reviewed finding")
    assert run(repo) == 1
    assert records(repo)[0]["suite_results"]["non_passed"] == [[observed, "skipped"]]
    assert evaluate(repo) != 0, "the exit code decided before the manifest was consulted"


def test_a_freeze_refuses_to_accept_what_the_run_did_not_observe(repo: Path, capsys) -> None:
    invented = f"{SCOPE}::F401::" + "0" * 64
    assert freeze(repo, "--accepted", f"{invented}=invented") == 2
    assert "must name findings the frozen run observed" in capsys.readouterr().err


# --- the artifact is not taken at its word ----------------------------------


def forging_repo(repo: Path, document: dict[str, object]) -> list[str]:
    """Bind a producer that writes `document` under a scanner's argv shape."""

    (repo / "forge.py").write_text(FORGER, encoding="utf-8")
    (repo / "forged.json").write_text(json.dumps(document), encoding="utf-8")
    command = ["/usr/bin/python3", "forge.py", "--output-format=sarif",
               f"--output-file={ARTIFACT}"]
    (repo / "gates.yaml").write_text(catalog(command), encoding="utf-8")
    return command


def forged_sarif(line: int, snippet: str | None = None, **run_fields: object) -> dict:
    region: dict[str, object] = {"startLine": line, "endLine": line}
    if snippet is not None:
        region["snippet"] = {"text": snippet}
    return {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "forger"}},
            "results": [{
                "ruleId": "F401",
                "level": "error",
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": SCOPE}, "region": region,
                }}],
            }],
            **run_fields,
        }],
    }


def test_a_forged_region_is_refused_rather_than_relocated(repo: Path, capsys) -> None:
    frozen(repo)
    command = forging_repo(repo, forged_sarif(line=99))
    commit(repo, "bind a forging producer")
    assert run(repo, command) == 2
    assert "lies outside" in capsys.readouterr().err
    assert not (repo / "evidence.json").exists(), "a refused artifact records nothing"
    assert evaluate(repo) != 0, "absence blocks"


def test_a_snippet_the_subject_does_not_carry_is_refused(repo: Path, capsys) -> None:
    frozen(repo)
    command = forging_repo(repo, forged_sarif(line=1, snippet="import os"))
    commit(repo, "bind a forging producer")
    assert run(repo, command) == 2
    assert "does not match the subject" in capsys.readouterr().err


def test_a_scanner_that_declares_its_own_failure_never_reads_as_clean(
    repo: Path, capsys
) -> None:
    """The FALSE-PASS trap: zero findings, exit 0, and an unsuccessful run."""

    frozen(repo)
    document = forged_sarif(line=1)
    document["runs"][0]["results"] = []
    document["runs"][0]["invocations"] = [{"executionSuccessful": False}]
    command = forging_repo(repo, document)
    commit(repo, "bind a producer that reports its own failure")
    assert run(repo, command) == 2
    assert "executionSuccessful" in capsys.readouterr().err
    assert evaluate(repo) != 0


# --- the manifest is trust root ---------------------------------------------


def test_widening_the_manifest_moves_the_subject_the_evidence_addressed(
    repo: Path, capsys
) -> None:
    """The manifest is in the tree, so widening it is a change to the subject.

    There is no window in which policy is edited and the old evidence still
    addresses the tree: the accepted list is part of what the subject digest
    covers, so evidence signed before the edit stops addressing the commit
    after it. The digest binding is belt to that braces — a receiver comparing
    manifests across heads (`E-GITHUB-EVALUATION-POLICY-CHANGED`) is where it
    does the work on its own.
    """

    frozen(repo)
    (repo / SCOPE).write_text(VIOLATION, encoding="utf-8")
    commit(repo, "introduce a real F401")
    assert run(repo) == 1
    identifier = observed_finding(repo)
    manifest = json.loads((repo / MANIFEST).read_text(encoding="utf-8"))
    manifest["accepted"] = {identifier: "waved through after the fact"}
    (repo / MANIFEST).write_bytes(canonical_json_bytes(manifest))
    commit(repo, "widen accepted after the evidence was signed")
    assert evaluate(repo) != 0
    assert "different subject digest" in capsys.readouterr().out


def test_an_uncommitted_manifest_edit_never_decides(repo: Path, capsys) -> None:
    """Review is the control on the manifest, so an unstaged edit cannot count."""

    frozen(repo)
    assert run(repo) == 0
    manifest = json.loads((repo / MANIFEST).read_text(encoding="utf-8"))
    manifest["accepted"] = {f"{SCOPE}::F401::{'0' * 64}": "unreviewed"}
    (repo / MANIFEST).write_bytes(canonical_json_bytes(manifest))
    assert evaluate(repo) == 2
    assert "scan manifest" in capsys.readouterr().err


def test_evidence_from_another_subject_never_satisfies(repo: Path) -> None:
    frozen(repo)
    assert run(repo) == 0
    (repo / "unrelated.txt").write_text("moved on\n", encoding="utf-8")
    commit(repo, "change the subject")
    assert evaluate(repo) != 0


def test_absence_blocks(repo: Path) -> None:
    frozen(repo)
    assert evaluate(repo) != 0, "no run, no evidence, no pass"


# --- determinism ------------------------------------------------------------


def test_repeats_on_identical_input_reduce_identically(repo: Path) -> None:
    frozen(repo)
    digests = []
    for _ in range(3):
        assert run(repo) == 0
        digests.append(records(repo)[-1]["suite_results"]["outcome_digest"])
    assert len(set(digests)) == 1, digests
