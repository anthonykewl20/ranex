"""Real external-repository audit, including controls that expose known limits.

Run sequentially with no other confinement suite on this host:
  uv run --frozen python tools/dogfood/release_audit.py --out /tmp/ranex-audit

Uses the existing external-proof onboarding, real six tests, CLI subprocesses,
Git commits, signed observations, and SQLite files. No product seam is mocked.
Every result carries the actual command/output; GAP is never called PASS.
Exit 1 means reproduced product/spec gaps; exit 2 means incomplete execution.
Scratch repositories and private keys are temporary and are never published.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import external_proof as proof
import yaml


class Audit:
    def __init__(self, root: Path, ref: str, out: Path) -> None:
        self.root, self.ref, self.out = root, ref, out
        self.commands: list[dict] = []
        self.cases: list[dict] = []
        self.kernel = root / "kernel"
        self.repo = root / "external"
        self.key = root / "external-proof.key"

    def command(self, name: str, argv: list[str], *, env: dict | None = None) -> dict:
        result = subprocess.run(
            [str(a) for a in argv], cwd=self.repo, env=env,
            capture_output=True, text=True, timeout=900, check=False,
        )
        row = {"name": name, "argv": [str(a) for a in argv],
               "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        self.commands.append(row)
        return row

    def cli(self, name: str, *args: str, credentials: bool = True) -> dict:
        # An allowlist avoids pretending that a list of provider names covers
        # every possible credential. The empty HOME carries no auth stores.
        (self.root / "home").mkdir(exist_ok=True)
        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root / "home"), "LANG": "C.UTF-8"}
        env["PYTHONPATH"] = str(self.repo / "src")
        if credentials:
            env["RANEX_SIGNING_KEY"] = str(self.key)
        return self.command(name, [str(self.kernel / ".venv/bin/python"),
                                  "-m", "ranex.cli.main", *args], env=env)

    def gate(self, name: str, approver: str = proof.APPROVER) -> dict:
        return self.cli(name, "gate", "evaluate", "HEAD", "--approver", approver,
                        "--journal", "governance/journal.sqlite3", credentials=False)

    def run(self, name: str, argv: list[str] | None = None) -> dict:
        return self.cli(name, "run", "--producer", proof.PRODUCER,
                        "--claim", "tests-executed", "--", *(argv or self.argv))

    def record(self, name: str, expected: str, verified: bool, *commands: dict,
               detail: str = "") -> None:
        row = {"case": name, "expected": expected,
               "status": "VERIFIED" if verified else "GAP",
               "commands": [c["name"] for c in commands], "detail": detail}
        self.cases.append(row)
        print(f"{self.ref}: {row['status']} {name}", flush=True)
        self.save()

    def save(self) -> None:
        self.out.mkdir(parents=True, exist_ok=True)
        (self.out / "receipt.json").write_text(json.dumps({
            "schema": "ranex-release-audit-v1", "requested_ref": self.ref,
            "kernel": getattr(self, "identity", None),
            "external": getattr(self, "external", None),
            "baseline": getattr(self, "baseline", None),
            "cases": self.cases, "commands": self.commands,
        }, indent=2, sort_keys=True) + "\n")

    def git(self, *args: str) -> str:
        result = proof._git(self.repo, *args)
        if result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def restore(self) -> None:
        # This reset is confined to the freshly created disposable clone.
        self.git("reset", "--hard", self.base)
        for name in ("evidence.json", "suite_results.xml", "journal.sqlite3"):
            (self.repo / "governance" / name).unlink(missing_ok=True)

    def plugin_variant(self, name: str, plugin: str, *, gap_detail: str = "") -> None:
        self.restore()
        if (self.repo / "conftest.py").exists():
            raise RuntimeError("fixture gained conftest.py; review before injecting a hook")
        (self.repo / "conftest.py").write_text(plugin)
        self.commit(name)
        observed = self.run(name + ":run")
        gate = self.gate(name + ":gate")
        reason = {"undeclared-skip": "(skipped)", "deselected-test": "missing test ID(s)",
                  "xfail": "(xfailed)", "strict-xpass": "(xpassed)",
                  "nonstrict-xpass": "(xpassed)"}.get(name)
        verified = gate["exit"] == 1
        if reason:
            verified = verified and "RECORDED" in observed["stdout"] and reason in gate["stdout"]
        self.record(name, "gate refuses with the expected suite diagnosis", verified,
                    observed, gate, detail=gap_detail)

    def execute(self) -> None:
        proof.check_prerequisites(proof.REPO_ROOT, self.ref)
        self.identity = proof.provision_kernel(self.root, proof.REPO_ROOT, self.ref)
        self.repo, self.external = proof.clone_external(
            self.root, proof.EXTERNAL_URL, proof.EXTERNAL_REV)
        self.baseline = proof.measure_baseline(self.repo, self.root)
        shutil.copyfile(self.root / "baseline.xml", self.out / "baseline.xml")
        setup = proof.onboard_governance(self.kernel, self.repo, self.root, self.ref,
                                         self.baseline["passing"], 0)
        self.argv = setup["argv"]
        self.base = self.git("rev-parse", "HEAD")
        self.external["selected_ids"] = setup["selected"]
        self.external["vendored_src_tree"] = setup["vendored_src_tree"]
        run = self.run("positive:run")
        gate = self.gate("positive:gate")
        journal = self.cli("positive:journal", "journal", "verify",
                           "--journal", "governance/journal.sqlite3", credentials=False)
        self.record("pristine-external-suite", "real suite recorded; gate PASS; chain verified",
                    run["exit"] == gate["exit"] == journal["exit"] == 0
                    and "RECORDED" in run["stdout"] and gate["stdout"].startswith("PASS"),
                    run, gate, journal)
        if self.cases[-1]["status"] != "VERIFIED":
            raise RuntimeError("positive control failed; sabotage results would be meaningless")
        evidence_path = self.repo / "governance/evidence.json"
        good_evidence = evidence_path.read_bytes()
        (self.out / "real-evidence.json").write_bytes(good_evidence)
        public = yaml.safe_load((self.repo / "governance/producers.yaml").read_text())["producers"][proof.PRODUCER]
        (self.out / "public-key.txt").write_text(public + "\n")
        (self.out / "public-key.der").write_bytes(bytes.fromhex("302a300506032b6570032100")
                                                  + base64.b64decode(public.removeprefix("ed25519:")))
        (self.out / "signature.bin").write_bytes(base64.b64decode(
            json.loads(good_evidence)[0]["signature"].removeprefix("ed25519:")))
        program = (
            "import json,sys; from pathlib import Path; "
            "from ranex.foundation.signing import signed_payload; "
            "record=json.loads(Path(sys.argv[1]).read_bytes())[0]; record.pop('signature'); "
            "Path(sys.argv[2]).write_bytes(signed_payload(record))"
        )
        payload = proof._kernel_python(self.kernel, self.repo, "-c", program,
                                       str(evidence_path), str(self.out / "payload.bin"))
        if payload.returncode:
            raise RuntimeError(payload.stderr)
        openssl = self.command("openssl:verify", ["openssl", "pkeyutl", "-verify", "-pubin",
                               "-keyform", "DER", "-inkey", str(self.out / "public-key.der"),
                               "-rawin", "-in", str(self.out / "payload.bin"),
                               "-sigfile", str(self.out / "signature.bin")])
        self.record("independent-signature-verification", "OpenSSL verifies the actual observation",
                    openssl["exit"] == 0, openssl,
                    detail="Payload framing uses the kernel's format; Ed25519 verification uses OpenSSL.")

        no_credentials = self.gate("no-model-credentials:gate")
        self.record("no-model-credentials", "same gate output without signing/model credentials",
                    no_credentials["exit"] == 0 and no_credentials["stdout"] == gate["stdout"],
                    no_credentials)
        self_approval = self.gate("self-approval:gate", proof.PRODUCER)
        self.record("self-approval", "same producer/approver refuses", self_approval["exit"] == 1,
                    self_approval)
        good_journal = (self.repo / "governance/journal.sqlite3").read_bytes()
        evidence_path.unlink()
        absent = self.gate("absent-evidence:gate")
        self.record("absent-evidence", "absence blocks", absent["exit"] == 1, absent)
        evidence_path.write_bytes(good_evidence)
        records = json.loads(good_evidence)
        records[0]["exit_code"] = 23
        evidence_path.write_text(json.dumps(records))
        tampered = self.gate("tampered-signature:gate")
        self.record("tampered-signature", "bad signature refuses", tampered["exit"] == 1
                    and "bad-signature" in tampered["stdout"], tampered)
        evidence_path.write_bytes(good_evidence)
        replay = self.gate("replayed-evidence:gate")
        self.record("evidence-replay", "freshness/replay detection", replay["exit"] != 0, replay,
                    detail="Deferred anti-replay: unchanged subject/policy accepts the same record again.")

        (self.repo / "six.py").write_text((self.repo / "six.py").read_text() + "\n# changed\n")
        dirty = self.run("dirty-subject:run")
        self.record("dirty-subject", "run refuses uncommitted source", dirty["exit"] != 0, dirty)
        self.commit("change subject after evidence")
        stale = self.gate("stale-subject:gate")
        self.record("stale-subject", "stale evidence refuses", stale["exit"] == 1
                    and proof.STALE_REASON in stale["stdout"], stale)
        evidence_path.unlink()
        recovery_run = self.run("recovery:run")
        recovery_gate = self.gate("recovery:gate")
        self.record("recovery", "rerun changed subject restores PASS",
                    recovery_run["exit"] == recovery_gate["exit"] == 0, recovery_run, recovery_gate)

        self.restore()
        wrong = self.run("wrong-command:run", ["true"])
        wrong_gate = self.gate("wrong-command:gate")
        self.record("wrong-command", "true cannot satisfy pytest claim", wrong_gate["exit"] == 1,
                    wrong, wrong_gate)

        self.restore()
        catalog = self.repo / "governance/gates.yaml"
        gates = yaml.safe_load(catalog.read_text())
        sibling = dict(gates["gates"][0], gate_id="sibling")
        gates["gates"].append(sibling)
        catalog.write_text(yaml.safe_dump(gates))
        self.commit("two gates with the same command but distinct identities")
        bound = self.run("cross-gate:run")
        foreign = self.cli("cross-gate:gate", "gate", "evaluate", "HEAD", "--gate", "sibling",
                           "--approver", proof.APPROVER, "--journal", "governance/journal.sqlite3",
                           credentials=False)
        self.record("cross-gate-replay", "landing evidence cannot authorize sibling gate",
                    foreign["exit"] == 1, bound, foreign,
                    detail="ADR-048 adds policy context after v0.1.0; older behavior is measured separately.")

        if (self.repo / "src/ranex/policy/adapters/configuration/yaml/principal_catalog.py").exists():
            self.restore()
            keyring = self.repo / "governance/producers.yaml"
            producers = yaml.safe_load(keyring.read_text())
            producers["principals"] = {proof.PRODUCER: {"role": "worker", "keys": [{
                "key": producers["producers"][proof.PRODUCER], "status": "retired"}]}}
            keyring.write_text(yaml.safe_dump(producers))
            self.commit("retire the producer key in the principal catalog")
            retired = self.run("retired-principal-key:run")
            retired_gate = self.gate("retired-principal-key:gate")
            self.record("retired-principal-key", "retired key cannot authorize new work",
                        retired["exit"] != 0 and retired_gate["exit"] != 0, retired, retired_gate,
                        detail="ADR-047's standalone principal loader is not wired into run/gate keyring admission.")

        self.restore()
        source = self.repo / "six.py"
        text = source.read_text()
        assert text.count("    integer_types = int,") == 1
        source.write_text(text.replace("    integer_types = int,", "    integer_types = str,"))
        self.commit("break real six integer type behavior")
        red = self.run("broken-source:run")
        red_gate = self.gate("broken-source:gate")
        self.record("broken-source", "real failed external assertions block",
                    red["exit"] == 1 and "RECORDED" in red["stdout"] and red_gate["exit"] == 1
                    and "test_six.py::test_integer_types (failed)" in red_gate["stdout"], red, red_gate)

        self.plugin_variant("undeclared-skip", "import pytest\ndef pytest_collection_modifyitems(items):\n"
                            "    items[0].add_marker(pytest.mark.skip(reason='audit'))\n")
        self.plugin_variant("deselected-test", "def pytest_collection_modifyitems(items):\n"
                            "    del items[0]\n")
        self.plugin_variant("xfail", "import pytest\ndef pytest_collection_modifyitems(items):\n"
                            "    items[0].add_marker(pytest.mark.xfail(run=False, reason='audit'))\n")
        self.plugin_variant("strict-xpass", "import pytest\ndef pytest_collection_modifyitems(items):\n"
                            "    items[0].add_marker(pytest.mark.xfail(strict=True, reason='audit'))\n")
        self.plugin_variant("nonstrict-xpass", "import pytest\ndef pytest_collection_modifyitems(items):\n"
                            "    items[0].add_marker(pytest.mark.xfail(strict=False, reason='audit'))\n",
                            gap_detail="ADR-011 promises XPASS refusal; pytest's real non-strict XPASS XML looks passed.")
        self.plugin_variant("collection-error", "raise RuntimeError('audit collection failure')\n",
                            gap_detail="Inspect run/error output: failed collection may leave no evidence (F-004).")
        self.restore()
        tests = self.repo / "test_six.py"
        tests.write_text("raise RuntimeError('audit file collection failure')\n" + tests.read_text())
        self.commit("break collection of an actual external test module")
        collection = self.run("file-collection-error:run")
        missing = self.gate("file-collection-error:gate")
        self.record("collection-error-diagnosis", "record executed collection failure, then gate FAIL",
                    "RECORDED" in collection["stdout"] and missing["exit"] == 1,
                    collection, missing,
                    detail="F-004: failed collection is reported as missing evidence, despite actual execution.")

        # The actual tests fail first; only their reporting hooks lie. Neither
        # evidence nor signatures are constructed by this attack program.
        self.restore()
        source.write_text(text.replace("    integer_types = int,", "    integer_types = str,"))
        (self.repo / "conftest.py").write_text(
            "import pytest\n"
            "@pytest.hookimpl(hookwrapper=True)\n"
            "def pytest_runtest_makereport(item, call):\n"
            "    result = yield\n"
            "    report = result.get_result()\n"
            "    if report.failed:\n"
            "        report.outcome = 'passed'\n"
            "        report.longrepr = None\n")
        self.commit("hostile reporting hook conceals real failed assertions")
        bare = self.command("forged-results:independent-oracle", [proof.PINNED_PY, "-c",
                            "import six; assert isinstance(1, six.integer_types)"])
        forged_run = self.run("forged-results:run")
        forged_gate = self.gate("forged-results:gate")
        if bare["exit"] != 1:
            raise RuntimeError("independent broken-code control did not fail")
        self.record("hostile-result-producer", "broken code must not receive correctness PASS",
                    forged_gate["exit"] == 1, bare, forged_run, forged_gate,
                    detail="ADR-007/011 disclosed boundary: signing authenticates a report, not its truth.")

        self.restore()
        journal_path = self.repo / "governance/journal.sqlite3"
        for name, sql in (
            ("partial-edit", "UPDATE evaluations SET record='{}' WHERE seq=1"),
            ("nonjson-edit", "UPDATE evaluations SET record='not-json' WHERE seq=1"),
            ("suffix-truncation", "DELETE FROM evaluations WHERE seq=(SELECT MAX(seq) FROM evaluations)"),
            ("whole-history-deletion", "DELETE FROM evaluations"),
        ):
            journal_path.write_bytes(good_journal)
            with sqlite3.connect(journal_path) as connection:
                connection.execute("DROP TRIGGER evaluations_no_update")
                connection.execute("DROP TRIGGER evaluations_no_delete")
                connection.execute(sql)
            checked = self.cli(name + ":journal", "journal", "verify", "--journal",
                               "governance/journal.sqlite3", credentials=False)
            self.record(name, "tampered history refused without traceback",
                        checked["exit"] != 0 and "Traceback" not in checked["stderr"], checked,
                        detail="F-001/F-005: unanchored chains cannot prove completeness.")
        journal_path.write_bytes(good_journal)
        with sqlite3.connect(journal_path) as connection:
            connection.execute("DROP TRIGGER evaluations_no_update")
            rows = connection.execute("SELECT seq,record FROM evaluations ORDER BY seq").fetchall()
            previous = "sha256:" + "0" * 64
            for seq, raw in rows:
                record = json.loads(raw)
                record["approver_id"] = "rewritten-history"
                # Independent attack arithmetic, deliberately not a production
                # reimplementation or an authority-generating helper.
                encoded = json.dumps({"prev_link": previous, "record": record},
                                     sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                link = "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()
                connection.execute("UPDATE evaluations SET record=?,prev_link=?,link=? WHERE seq=?",
                                   (json.dumps(record), previous, link, seq))
                previous = link
        checked = self.cli("full-rewrite:journal", "journal", "verify", "--journal",
                           "governance/journal.sqlite3", credentials=False)
        self.record("full-history-rewrite", "rewritten history refused", checked["exit"] != 0, checked,
                    detail="F-005: a self-consistent replacement chain has no external authenticity anchor.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--refs", nargs="+", default=["v0.1.0", "HEAD"])
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    gaps = 0
    for index, ref in enumerate(args.refs):
        destination = out / str(index)
        destination.mkdir()
        with tempfile.TemporaryDirectory(prefix="ranex-release-audit-") as directory:
            audit = Audit(Path(directory), ref, destination)
            try:
                audit.execute()
            except Exception as error:
                audit.save()
                (destination / "incomplete.json").write_text(json.dumps({
                    "status": "UNVERIFIED", "error": f"{type(error).__name__}: {error}"}) + "\n")
                print(f"UNVERIFIED {ref}: {error}", flush=True)
                return 2
            gaps += sum(c["status"] == "GAP" for c in audit.cases)
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
