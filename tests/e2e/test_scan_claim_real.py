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
import os
import pwd
import shutil
import subprocess
import sys
from pathlib import Path

import _approver
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

# These reviewed inline bytes are part of the bound catalog command. Coverage
# comes from Ruff's real discovery, never from the frozen manifest. This is a
# producer coverage declaration; it does not claim controller-observed reads.
RUFF_DISCOVERY_ADAPTER = """\
import json, pathlib, resource, subprocess, sys, tempfile
LIMIT = 1024 * 1024
def bounded(argv):
    def limits():
        resource.setrlimit(resource.RLIMIT_FSIZE, (LIMIT, LIMIT))
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        result = subprocess.run(argv, stdout=out, stderr=err, timeout=30, preexec_fn=limits)
        out.seek(0); err.seek(0)
        stdout, stderr = out.read(LIMIT + 1), err.read(LIMIT + 1)
        if len(stdout) > LIMIT or len(stderr) > LIMIT:
            raise ValueError('Ruff output exceeds discovery adapter limit')
        if stderr:
            sys.stderr.buffer.write(stderr)
        return result.returncode, stdout
binary, target = sys.argv[1], sys.argv[-1]
status, version = bounded([binary, '--version'])
if status or version.strip() != b'ruff 0.16.2':
    raise ValueError('discovery adapter requires actual Ruff 0.16.2')
base = [binary, 'check', '--no-cache', '--isolated', '--select=F401']
status, discovered = bounded(base + ['--show-files', target])
if status:
    sys.exit(status)
root = pathlib.Path.cwd().resolve()
paths = sorted(set(pathlib.Path(line).resolve().relative_to(root).as_posix()
                   for line in discovered.decode('utf-8').splitlines()))
if any(not (root / path).is_file() for path in paths):
    raise ValueError('discovered Ruff path does not exist in the subject')
output = next(arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--output-file='))
args = base + (['--exit-zero'] if '--exit-zero' in sys.argv else [])
args += ['--output-format=sarif', '--output-file=' + output]
# Empty discovery remains an actual empty-target Ruff check, with artifacts [].
status, _ = bounded(args + (paths or [target]))
if status not in (0, 1):
    sys.exit(status)
artifact = pathlib.Path(output)
if not artifact.is_file() or artifact.stat().st_size > LIMIT:
    raise ValueError('Ruff did not produce a bounded SARIF report')
document = json.loads(artifact.read_bytes())
if len(document['runs']) != 1:
    raise ValueError('Ruff discovery adapter requires one report run')
document['runs'][0]['artifacts'] = [{'location': {'uri': path}} for path in paths]
document['runs'][0]['invocations'] = [{'executionSuccessful': status in (0, 1)}]
encoded = json.dumps(document).encode('utf-8')
if len(encoded) > LIMIT:
    raise ValueError('augmented Ruff report exceeds discovery adapter limit')
artifact.write_bytes(encoded)
sys.exit(status)
"""


def ruff_binary() -> str:
    """The real scanner, found by absolute path and not by an inherited PATH.

    A hermetic run pins `PATH` to `/usr/bin:/bin`, which is the whole point of
    it — so `shutil.which` finds nothing there and every arm below would skip.
    A skipped arm inside a materialisation is an UNDECLARED skip against the
    frozen manifest, which `test_slice009_repository_gate_fails_when_a_manifest_
    test_is_deleted` refuses, and it should: a suite that quietly stops running
    where it is being trusted most is exactly what that journey guards.

    So the binary is resolved the way the bound argv resolves it — absolutely,
    against the real filesystem the materialisation still sees.
    """

    # `Path.home()` reads HOME, and a hermetic run redirects HOME into its own
    # scratch tree — so the first version of this fallback pointed at a home
    # that had never seen ruff, and the arms went on skipping exactly where
    # they were needed. The account's real home comes from the passwd database,
    # which the environment cannot move.
    account = pwd.getpwuid(os.getuid()).pw_dir
    candidates = [shutil.which("ruff")]
    candidates += [
        f"{account}/.local/bin/ruff",
        "/usr/local/bin/ruff",
        "/usr/bin/ruff",
    ]
    for candidate in candidates:
        if candidate and os.access(candidate, os.X_OK):
            return candidate
    pytest.skip("ranex-prereq:ruff: no ruff on this host, so no real SARIF producer")


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

    return [sys.executable, "-c", RUFF_DISCOVERY_ADAPTER, binary,
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
    (repository / ".gitignore").write_text("observations.sqlite3*\n", encoding="utf-8")
    signing.write_keyring(repository)
    attach(repository, signing)
    commit(repository, "initial")
    return repository


def invoke(
    repo: Path, argv: list[str], producer: str | None = None, *, approver: str | None = None
) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr("ranex.cli.main.governed_repository_root", lambda: repo.resolve())
        if producer is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv("RANEX_SIGNING_KEY", str(signing_for(repo).key_path(producer)))
        if approver is None:
            _approver.strip_approvers(monkeypatch)
        else:
            # RISK-07: prove possession of the catalogued approver's key.
            monkeypatch.setenv(
                _approver.APPROVER_ENV,
                str(signing_for(repo).approver_path(approver)),
            )
        signing_for(repo).configure_history(monkeypatch, repo)
        return main(argv)


def freeze(repo: Path, *declarations: str, exit_zero: bool = False) -> int:
    return invoke(
        repo,
        [
            "suite", "freeze",
            "--repository", ".",
            "--evidence", "evidence.json",
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
        approver="reviewer",
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
    """Bind a producer that writes `document` under a scanner's argv shape.

    #110 Correction 2 refuses a scan claim bound to an in-tree script, so the
    forger rides inline `-c` bytes: catalog-supplied, review-visible, exactly
    the hostile-report vehicle these tests need. The tree still supplies
    `forged.json` — a scanner reading planted data is the threat being tested,
    and the kernel's region validation is what must catch it.
    """

    (repo / "forged.json").write_text(json.dumps(document), encoding="utf-8")
    command = ["/usr/bin/python3", "-c", FORGER, "--output-format=sarif",
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
                "ruleId": "F401", "message": {"text": "forged region"},
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


@pytest.mark.parametrize("operation", ["run", "freeze"])
@pytest.mark.parametrize("reporter,metadata,expected", [
    ("delegated-review-sarif-2.1.0", False, 2),
    ("delegated-review-sarif-2.1.0", True, 0),
    ("sarif-2.1.0", False, 0),
])
def test_committed_review_reporter_governs_real_worker_dispatch(
    repo, capsys, operation, reporter, metadata, expected
):
    import sys

    from ranex.foundation.delegated_review import (
        build_packet,
        empty_handbook_digest,
        packet_bytes,
        packet_digest,
    )
    packet = build_packet(subject_digest="sha256:" + "a" * 64,
                          range_base="b" * 40, range_head="c" * 40,
                          handbook_digest=empty_handbook_digest(), chapters=[])
    (repo / "governance/review-packet.json").write_bytes(packet_bytes(packet))
    document = {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "review-worker"}},
        "artifacts": [{"location": {"uri": SCOPE}}], "results": [],
    }]}
    if metadata:
        document["runs"][0]["properties"] = {"packet_digest": packet_digest(packet)}
    # Real subprocess emits pinned bytes; it does not import a stale checkout.
    code = "import sys; open(sys.argv[-1].split('=',1)[1], 'w').write(" + repr(json.dumps(document)) + ")"
    command = [sys.executable, "-c", code, "--output-format=sarif", f"--output-file={ARTIFACT}"]
    (repo / "gates.yaml").write_text(catalog(command).replace("sarif-2.1.0", reporter))
    (repo / MANIFEST).write_bytes(canonical_json_bytes({
        "scope": [SCOPE], "rules": ["review"], "blocking_levels": ["error"], "accepted": {},
    }))
    commit(repo, "bind trusted review reporter and packet")
    if operation == "run":
        actual = run(repo, command)
    else:
        actual = invoke(repo, ["suite", "freeze", "--repository", ".",
                              "--evidence", "evidence.json", "--artifact", ARTIFACT,
                              "--output", MANIFEST, "--results-reporter", reporter,
                              "--scan-scope", SCOPE, "--scan-rule", "review", "--", *command])
    captured = capsys.readouterr()
    assert actual == expected, captured
    if expected:
        assert "packet_digest" in captured.err
    elif operation == "run":
        assert evaluate(repo) == 0


@pytest.mark.parametrize("operation", ["run", "freeze"])
@pytest.mark.parametrize("malformed", ["tool", "severity"])
def test_real_worker_malformed_sarif_core_refuses(repo, capsys, operation, malformed):
    import sys

    document = {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "worker", "rules": [{
            "id": "security", "defaultConfiguration": {"level": "error"},
        }]}}, "artifacts": [{"location": {"uri": SCOPE}}], "results": [],
    }]}
    if malformed == "tool":
        document["runs"][0].pop("tool")
    else:
        document["runs"][0]["tool"]["driver"]["rules"][0]["defaultConfiguration"] = [{"level": "error"}]
        document["runs"][0]["results"] = [{
            "ruleId": "security", "message": {"text": "danger"},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": SCOPE},
                                                  "region": {"startLine": 1}}}],
        }]
    code = "import sys; open(sys.argv[-1].split('=',1)[1], 'w').write(" + repr(json.dumps(document)) + ")"
    command = [sys.executable, "-c", code, "--output-format=sarif", f"--output-file={ARTIFACT}"]
    (repo / "gates.yaml").write_text(catalog(command))
    (repo / MANIFEST).write_bytes(canonical_json_bytes({
        "scope": [SCOPE], "rules": ["security"], "blocking_levels": ["error"], "accepted": {},
    }))
    commit(repo, "bind malformed-report negative control")
    if operation == "run":
        actual = run(repo, command)
    else:
        actual = invoke(repo, ["suite", "freeze", "--repository", ".",
                              "--evidence", "evidence.json", "--artifact", ARTIFACT,
                              "--output", MANIFEST, "--results-reporter", "sarif-2.1.0",
                              "--scan-scope", SCOPE, "--scan-rule", "security", "--", *command])
    assert actual == 2, capsys.readouterr()
    assert evaluate(repo) != 0


@pytest.mark.parametrize("target", ["empty", "other"])
@pytest.mark.parametrize("operation", ["run", "freeze"])
def test_real_ruff_target_outside_frozen_scope_never_satisfies(repo, target, operation, capsys):
    """A genuine zero-exit Ruff invocation cannot certify an unscanned file."""
    frozen(repo)
    (repo / target).mkdir()
    (repo / target / (".keep" if target == "empty" else "clean.py")).write_text(CLEAN)
    (repo / SCOPE).write_text(VIOLATION)
    command = scan_command(ruff_binary())
    command[-1] = target
    (repo / "gates.yaml").write_text(catalog(command))
    commit(repo, "bind genuine scanner to a target outside the frozen scope")
    if operation == "run":
        assert run(repo, command) == 0
        assert records(repo)[-1]["suite_results"]["missing"] == [SCOPE]
        assert evaluate(repo) != 0
    else:
        assert invoke(repo, ["suite", "freeze", "--repository", ".", "--evidence", "evidence.json",
                             "--artifact", ARTIFACT, "--output", "governance/uncovered.json",
                             "--results-reporter", "sarif-2.1.0", "--scan-scope", SCOPE,
                             "--scan-rule", "F401", "--", *command]) == 2
        assert "coverage missing frozen scope" in capsys.readouterr().err
        assert not (repo / "governance/uncovered.json").exists()


@pytest.mark.parametrize("reporter", ["sarif-2.1.0", "delegated-review-sarif-2.1.0"])
@pytest.mark.parametrize("coverage", ["absent", "empty", "other"])
@pytest.mark.parametrize("operation", ["run", "freeze"])
def test_reporter_without_frozen_scope_coverage_never_satisfies(repo, reporter, coverage, operation, capsys):
    """A packet binding or successful invocation does not witness file coverage."""
    import sys

    from ranex.foundation.delegated_review import (
        build_packet,
        empty_handbook_digest,
        packet_bytes,
        packet_digest,
    )
    document = {"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "coverage-probe"}}, "results": [],
        "invocations": [{"executionSuccessful": True}],
    }]}
    if reporter == "delegated-review-sarif-2.1.0":
        packet = build_packet(subject_digest="sha256:" + "a" * 64,
                              range_base="b" * 40, range_head="c" * 40,
                              handbook_digest=empty_handbook_digest(), chapters=[])
        (repo / "governance/review-packet.json").write_bytes(packet_bytes(packet))
        document["runs"][0]["properties"] = {"packet_digest": packet_digest(packet)}
    if coverage != "absent":
        document["runs"][0]["artifacts"] = (
            [] if coverage == "empty" else [{"location": {"uri": "other.py"}}]
        )
    code = "import sys; open(sys.argv[-1].split('=',1)[1], 'w').write(" + repr(json.dumps(document)) + ")"
    command = [sys.executable, "-c", code, "--output-format=sarif", f"--output-file={ARTIFACT}"]
    (repo / "gates.yaml").write_text(catalog(command).replace("sarif-2.1.0", reporter))
    (repo / MANIFEST).write_bytes(canonical_json_bytes({
        "scope": [SCOPE], "rules": ["review"], "blocking_levels": ["error"], "accepted": {},
    }))
    commit(repo, "bind uncovered report with authentic producer and trusted history")
    if operation == "run":
        assert run(repo, command) == 0
        assert records(repo)[-1]["suite_results"]["missing"] == [SCOPE]
        assert evaluate(repo) != 0
    else:
        assert invoke(repo, ["suite", "freeze", "--repository", ".", "--evidence", "evidence.json",
                             "--artifact", ARTIFACT, "--output", "governance/uncovered.json",
                             "--results-reporter", reporter, "--scan-scope", SCOPE,
                             "--scan-rule", "review", "--", *command]) == 2
        assert "coverage missing frozen scope" in capsys.readouterr().err
        assert not (repo / "governance/uncovered.json").exists()
