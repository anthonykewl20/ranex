"""External signed history is mandatory on the real bootstrap/run/gate path."""
from __future__ import annotations

import json
import subprocess

import pytest

from ranex.cli.main import main
from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.sqlite.observations import (
    ObservationLog,
    observations_path_for,
)
from ranex.governed_execution.verdict_reader import read_verdict, read_verdict_unbound


@pytest.mark.parametrize("attack", ["delete", "truncate", "rewrite"])
def test_explicit_bootstrap_real_run_then_judgment_and_missing_log_refusal(tmp_path, monkeypatch, capsys, attack):
    repository = tmp_path / "candidate"
    repository.mkdir()
    governance = repository / "governance"
    governance.mkdir()
    keys = {}
    for name, role in (("worker", "worker"), ("owner", "approver"), ("service", "service")):
        private, public = generate_keypair()
        path = tmp_path / (name + ".key")
        path.write_text(private)
        path.chmod(0o600)
        keys[name] = (path, public, role)
    producers = [f"producers:\n  worker: {keys['worker'][1]}",
                 f"verdict_signer:\n  id: kernel-verdict-signer\n  public_key: {keys['service'][1]}",
                 "principals:"]
    for name, (_, public, role) in keys.items():
        principal = "kernel-verdict-signer" if name == "service" else name
        producers.append(f"  {principal}:\n    role: {role}\n    keys:\n      - key: {public}\n        status: active")
    (governance / "producers.yaml").write_text("\n".join(producers) + "\n")
    (governance / "gates.yaml").write_text(
        'gates:\n  - gate_id: landing\n    rule_id: TESTS_EXECUTED\n    blocking: true\n'
        '    required_claims:\n      - claim_id: tests\n        command: ["/usr/bin/true"]\n')
    (repository / ".gitignore").write_text("governance/evidence.json\ngovernance/*.sqlite3*\ngovernance/verdicts/\n")
    for arguments in (("init", "-q"), ("config", "user.name", "Fixture"),
                      ("config", "user.email", "fixture@example.test"),
                      ("add", "."), ("commit", "-qm", "fixture")):
        subprocess.run(["git", "-C", str(repository), *arguments], check=True, capture_output=True)
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(keys["worker"][0]))
    monkeypatch.setenv("RANEX_VERDICT_SIGNING_KEY", str(keys["service"][0]))
    monkeypatch.setenv("RANEX_APPROVER_SIGNING_KEY", str(keys["owner"][0]))
    monkeypatch.setenv("RANEX_VERDICT_DIR", "governance/verdicts")
    checkpoint = tmp_path / "retained" / "history.json"
    monkeypatch.setenv("RANEX_HISTORY_CHECKPOINT", str(checkpoint))
    target = ["--external-repository", str(repository)]
    assert main(["gate", "evaluate", "HEAD", *target, "--approver", "owner"]) == 2
    assert "E-OBSERVATION-ANCHOR" in capsys.readouterr().err
    assert main(["history", "bootstrap", *target]) == 0
    assert main(["run", "--claim", "tests", "--producer", "worker", *target,
                 "--", "/usr/bin/true"]) == 0
    assert main(["gate", "evaluate", "HEAD", *target, "--approver", "owner"]) == 0
    evidence = governance / "evidence.json"
    record = json.loads(evidence.read_bytes())[0]
    verdict = governance / "verdicts" / (record["subject_digest"].removeprefix("sha256:") + ".json")
    archived = verdict.read_bytes()
    read = read_verdict_unbound(verdict, {"kernel-verdict-signer": keys["service"][1]},
                               approvers={"owner": (keys["owner"][1],)})
    assert str(read.state) == "verified"
    assert read.record["history_verified"] is True
    assert read.observation_checkpoint["head"] == ObservationLog(observations_path_for(evidence)).head()
    bound = read_verdict(verdict, {"kernel-verdict-signer": keys["service"][1]},
                         subject_digest=record["subject_digest"], gate_id="landing",
                         catalog_digest=read.record["catalog_digest"], approver_id="owner",
                         approvers={"owner": (keys["owner"][1],)}, repository_root=repository)
    assert str(bound.state) == "verified"
    old_pass = tmp_path / "old-pass-verdict.json"
    old_pass.write_bytes(archived)
    assert main(["run", "--claim", "tests", "--producer", "worker", *target,
                 "--", "/usr/bin/false"]) == 1
    assert main(["gate", "evaluate", "HEAD", *target, "--approver", "owner"]) == 1
    archived = verdict.read_bytes()
    retained_fail = read_verdict_unbound(verdict, {"kernel-verdict-signer": keys["service"][1]},
                                        approvers={"owner": (keys["owner"][1],)})
    assert retained_fail.record["verdict"] == "FAIL"
    old_replayed = read_verdict(old_pass, {"kernel-verdict-signer": keys["service"][1]},
                               subject_digest=record["subject_digest"], gate_id="landing",
                               catalog_digest=read.record["catalog_digest"], approver_id="owner",
                               approvers={"owner": (keys["owner"][1],)}, repository_root=repository)
    assert str(old_replayed.state) == "unanchored"
    observations_path_for(evidence).unlink()
    if attack != "delete":
        rebuilt = ObservationLog(observations_path_for(evidence))
        rebuilt.append_record(record)
        if attack == "rewrite":
            rebuilt.append_record(record)
        assert rebuilt.verify()
    assert main(["gate", "evaluate", "HEAD", *target, "--approver", "owner"]) == 2
    assert "E-OBSERVATION-ANCHOR" in capsys.readouterr().err
    assert verdict.read_bytes() == archived
    rejected = read_verdict(verdict, {"kernel-verdict-signer": keys["service"][1]},
                            subject_digest=record["subject_digest"], gate_id="landing",
                            catalog_digest=read.record["catalog_digest"], approver_id="owner",
                            approvers={"owner": (keys["owner"][1],)}, repository_root=repository)
    assert str(rejected.state) == "unanchored"
