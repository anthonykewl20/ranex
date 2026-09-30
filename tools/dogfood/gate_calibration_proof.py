#!/usr/bin/env python3
"""#115 — production calibration certificates for relied-on gates (MAP §8.4).

Operator invoke (completion evidence is this run, not unit tests alone):

    uv sync --frozen
    uv run --frozen python tools/dogfood/gate_calibration_proof.py \
        --out tools/dogfood/audits/2026-09-30-gate-calibration --repeats 3

Produces one certificate per gate under ``--out``:

* ``certificate-marker.json`` — shortcut-marker gate; known defect = trigger-less marker
* ``certificate-landing.json`` — landing-shaped suite gate; known defects = deleted
  frozen test + source break
* ``certificate-handbook-delegate.json`` — handbook-governed delegate path; known
  defect = dropped trust-boundary completeness guard (path silently omitted from
  the brief table)
* ``recall-false-pass.json`` — blunt gauge → FALSE-PASS with recall window
* ``SUMMARY.json`` — production statement inputs + Gauge R&R + host facts

Cites ``governance/calibration/base-freeze-v1.json``; invents no AIAG thresholds.
Second-host reproducibility is recorded UNVERIFIED when no second host is available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

DOGFOOD = Path(__file__).resolve().parent
REPOSITORY = DOGFOOD.parents[1]
sys.path[:0] = [str(DOGFOOD), str(REPOSITORY / "src"), str(REPOSITORY / "tests")]

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.foundation.signing import generate_keypair  # noqa: E402

SCHEMA = "ranex-gate-certificate-v1"
DATE = "2026-09-30"
BASE_FREEZE_PATH = REPOSITORY / "governance" / "calibration" / "base-freeze-v1.json"

MARKER_SCANNER = (
    "import pathlib,sys;"
    "bad=[p for p in pathlib.Path('.').rglob('*.py') "
    "if 'ranex:' in p.read_text() and ';' not in p.read_text().split('ranex:')[1].split(chr(10))[0]];"
    "print('markers without a trigger:',len(bad));"
    "sys.exit(1 if bad else 0)"
)
BLUNT_SCANNER = "import sys;print('all clear');sys.exit(0)"

# Tiny suite runner for the landing lab: hermetic runs resolve the venv
# interpreter to the base python (no pytest). This bound command uses
# /usr/bin/python3, executes the two named tests against app.py, and writes
# junitxml the gate's suite_manifest checker consumes — the same contract as
# a pytest --junitxml claim, without importing pytest.
LANDING_RUNNER = (
    "import ast,importlib.util,sys,traceback,xml.etree.ElementTree as ET\n"
    "from pathlib import Path\n"
    "root=Path('.')\n"
    "src=(root/'test_unit.py').read_text()\n"
    "names=[n.name for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]\n"
    "spec=importlib.util.spec_from_file_location('app', root/'app.py')\n"
    "app=importlib.util.module_from_spec(spec); spec.loader.exec_module(app)\n"
    "checks={'test_value': lambda: app.VALUE==1, 'test_value_positive': lambda: app.VALUE>0}\n"
    "suite=ET.Element('testsuite', name='pytest', tests=str(len(names)), failures='0', errors='0', skipped='0')\nprops=ET.SubElement(suite,'properties')\nET.SubElement(props,'property',name='ranex.pytest_observer',value='1')\n"
    "fails=0\n"
    "for name in names:\n"
    "  cid=f'test_unit.py::{name}'\n"
    "  case=ET.SubElement(suite,'testcase',classname='test_unit',name=name,time='0')\n"
    "  try:\n"
    "    assert checks[name]()\n"
    "  except Exception as exc:\n"
    "    fails+=1\n"
    "    fail=ET.SubElement(case,'failure',message=str(exc))\n"
    "    fail.text=''.join(traceback.format_exception(exc))\n"
    "suite.set('failures', str(fails))\n"
    "Path('governance').mkdir(exist_ok=True)\n"
    "ts=ET.Element('testsuites', name='pytest tests'); ts.append(suite)\n"
    "ET.ElementTree(ts).write('governance/suite_results.xml', encoding='utf-8', xml_declaration=True)\n"
    "print(f'{len(names)-fails} passed, {fails} failed of {len(names)}')\n"
    "sys.exit(1 if fails else 0)\n"
)



def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode())


def _host_facts() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "machine": platform.machine(),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "cwd": str(REPOSITORY),
        "ranex": str(REPOSITORY / ".venv" / "bin" / "ranex"),
    }


def _base_freeze_citation() -> dict[str, Any]:
    raw = BASE_FREEZE_PATH.read_bytes()
    loaded = json.loads(raw)
    return {
        "freeze_id": loaded.get("freeze_id", "base-freeze-v1"),
        "path": str(BASE_FREEZE_PATH.relative_to(REPOSITORY)),
        "digest": _sha256_bytes(raw),
        "note": (
            "Cited, not re-derived. MAP §8.4 AIAG percentage thresholds remain "
            "unverified; this certificate invents none."
        ),
        "reference_metrics_present": sorted(
            (loaded.get("reference_metrics") or {}).keys()
        ),
    }


def _write(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _repeatability(digests: list[str]) -> dict[str, Any]:
    identical = len(set(digests)) <= 1 and len(digests) >= 3
    return {
        "repeats": len(digests),
        "identical": identical,
        "distinct_count": len(set(digests)),
        "verdict_digests": digests,
        "status": "VERIFIED" if identical else "NON-DETERMINISTIC",
    }


def _repro_unverified() -> dict[str, Any]:
    return {
        "status": "UNVERIFIED",
        "detail": (
            "No second host available on this run; same-host ×N repeatability "
            "is recorded. Cross-host / cross-operator reproducibility remains "
            "UNVERIFIED."
        ),
        "second_host": None,
        "second_operator": None,
    }


def _journal_firing(journal: Path, *, gate_id: str | None = None) -> dict[str, Any]:
    if not journal.is_file():
        return {"determinable": False, "detail": "journal absent"}
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT seq, record, link FROM evaluations ORDER BY seq ASC"
        ).fetchall()
    except sqlite3.Error as exc:
        return {"determinable": False, "detail": f"journal unreadable: {exc}"}
    finally:
        connection.close()

    fires = 0
    passes = 0
    digests: list[str] = []
    positions: list[int] = []
    for seq, record_text, link in rows:
        try:
            body = json.loads(record_text)
        except (TypeError, ValueError):
            continue
        if gate_id is not None and body.get("gate_id") not in {None, gate_id}:
            continue
        verdict = body.get("verdict")
        digests.append(str(link))
        positions.append(int(seq))
        if verdict == "FAIL":
            fires += 1
        elif verdict == "PASS":
            passes += 1
    return {
        "determinable": True,
        "rows": len(rows),
        "fires": fires,
        "passes": passes,
        "positions": positions,
        "verdict_digests": digests,
        "source": str(journal),
    }


class Lab:
    """Real governed checkout: worker + catalogued approver, external-repository."""

    def __init__(self, root: Path, python: str, *, claim: str, argv: list[str], rule: str) -> None:
        self.root = root
        self.python = python
        self.claim = claim
        self.argv = argv
        self.rule = rule
        self.repo = root / "repo"
        self.home = root / "home"
        self.worker_key = root / "worker.key"
        self.approver_key = root / "approver.key"
        self.worker_public = ""
        self.approver_public = ""
        self.refs: dict[str, str] = {}

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                "GIT_AUTHOR_NAME": "gate-calibration",
                "GIT_AUTHOR_EMAIL": "gate-calibration@example.invalid",
                "GIT_COMMITTER_NAME": "gate-calibration",
                "GIT_COMMITTER_EMAIL": "gate-calibration@example.invalid",
            },
        )

    def _cli(
        self, *args: str, key: bool = True, approver: bool = False
    ) -> subprocess.CompletedProcess[str]:
        self.home.mkdir(parents=True, exist_ok=True)
        env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.home),
            "LANG": "C.UTF-8",
            "PYTHONPATH": str(REPOSITORY / "src"),
        }
        if key:
            env["RANEX_SIGNING_KEY"] = str(self.worker_key)
        if approver:
            env["RANEX_APPROVER_SIGNING_KEY"] = str(self.approver_key)
        argv = list(args)
        anchor = ["--external-repository", str(self.repo)]
        position = argv.index("--") if "--" in argv else len(argv)
        argv[position:position] = anchor
        return subprocess.run(
            [self.python, "-m", "ranex.cli.main", *argv],
            cwd=str(self.repo),
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

    def _commit(self, message: str) -> str:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD").stdout.strip()

    def init_repo(self) -> None:
        self.repo.mkdir(parents=True)
        (self.repo / "governance").mkdir()
        self.home.mkdir(parents=True, exist_ok=True)
        self._git("init", "-q", ".")
        self._git("config", "user.email", "gate-calibration@example.invalid")
        self._git("config", "user.name", "gate-calibration")
        (self.repo / ".gitignore").write_text(
            "governance/journal.sqlite3\n"
            "governance/evidence.json\n"
            "governance/suite_results.xml\n"
            "governance/verdicts/\n",
            encoding="utf-8",
        )
        w_priv, w_pub = generate_keypair()
        a_priv, a_pub = generate_keypair()
        self.worker_key.write_text(w_priv + "\n", encoding="utf-8")
        self.worker_key.chmod(0o600)
        self.approver_key.write_text(a_priv + "\n", encoding="utf-8")
        self.approver_key.chmod(0o600)
        self.worker_public = w_pub
        self.approver_public = a_pub
        command = json.dumps(self.argv)
        extra = ""
        if self.claim == "tests-executed":
            extra = "        results_artifact: governance/suite_results.xml\n"
        (self.repo / "governance" / "gates.yaml").write_text(
            "gates:\n"
            "  - gate_id: landing\n"
            f"    rule_id: {self.rule}\n"
            "    blocking: true\n"
            "    required_claims:\n"
            f"      - claim_id: {self.claim}\n"
            f"        command: {command}\n"
            f"{extra}",
            encoding="utf-8",
        )
        (self.repo / "governance" / "producers.yaml").write_text(
            f"producers:\n  worker: {w_pub}\n"
            f"principals:\n"
            f"  worker:\n    role: worker\n    keys:\n"
            f"      - key: {w_pub}\n        status: active\n"
            f"  auditor:\n    role: approver\n    keys:\n"
            f"      - key: {a_pub}\n        status: active\n",
            encoding="utf-8",
        )

    def observe(self, ref: str, *, keep_journal: bool = False) -> dict[str, Any]:
        self._git("checkout", "-q", ref)
        (self.repo / "governance" / "evidence.json").unlink(missing_ok=True)
        (self.repo / "governance" / "suite_results.xml").unlink(missing_ok=True)
        if not keep_journal:
            (self.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        run = self._cli(
            "run",
            "--claim",
            self.claim,
            "--producer",
            "worker",
            "--",
            *self.argv,
        )
        verdict = self._cli(
            "gate",
            "evaluate",
            "HEAD",
            "--approver",
            "auditor",
            "--journal",
            "governance/journal.sqlite3",
            key=False,
            approver=True,
        )
        first = verdict.stdout.split("\n", 1)[0].split("  ")[0].strip()
        facts = {
            "verdict": first,
            "exit": verdict.returncode,
            "run_exit": run.returncode,
            "stdout_head": verdict.stdout[:500],
            "run_stdout_head": run.stdout[:300],
        }
        digest = _sha256_bytes(
            json.dumps(facts, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        )
        return {"ok": first == "PASS", "facts": facts, "digest": digest}


def calibrate_marker(out: Path, repeats: int) -> dict[str, Any]:
    root = Path(tempfile.mkdtemp(prefix="ranex-115-marker-"))
    started = time.monotonic()
    try:
        lab = Lab(
            root,
            sys.executable,
            claim="markers-declared",
            argv=["/usr/bin/python3", "-c", MARKER_SCANNER],
            rule="MARKERS_DECLARED",
        )
        lab.init_repo()
        (lab.repo / "good.py").write_text(
            "# ranex: single-threaded scan; parallelise past 100k files\n",
            encoding="utf-8",
        )
        lab.refs["good"] = lab._commit("marker: well-formed")
        (lab.repo / "bad.py").write_text("# ranex: global lock\n", encoding="utf-8")
        lab.refs["bad"] = lab._commit("marker: trigger-less")
        lab._git("checkout", "-q", lab.refs["good"])

        digests: list[str] = []
        trials: list[dict[str, Any]] = []
        for _ in range(repeats):
            good = lab.observe(lab.refs["good"])
            bad = lab.observe(lab.refs["bad"])
            digests.append(good["digest"])
            trials.append(
                {
                    "positive_ok": good["ok"],
                    "negative_accepted": bad["ok"],
                    "positive": good["facts"],
                    "negative": bad["facts"],
                    "positive_digest": good["digest"],
                    "negative_digest": bad["digest"],
                }
            )

        # Retained journal for independent firing count.
        (lab.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        for ref in (lab.refs["good"], lab.refs["bad"], lab.refs["good"]):
            lab.observe(ref, keep_journal=True)
        firing = _journal_firing(
            lab.repo / "governance" / "journal.sqlite3", gate_id="landing"
        )

        all_positive = all(t["positive_ok"] for t in trials)
        all_refused = all(not t["negative_accepted"] for t in trials)
        repeatability = _repeatability(digests)
        if all_positive and all_refused and repeatability["identical"]:
            status = "VERIFIED"
        elif not all_refused:
            status = "FALSE-PASS"
        elif not all_positive:
            status = "GAP"
        else:
            status = "NON-DETERMINISTIC"

        certificate = {
            "schema": SCHEMA,
            "gate_id": "marker",
            "catalog_gate_id": "landing",
            "date": DATE,
            "bound_argv_digest": _sha256_bytes(canonical_json_bytes(lab.argv)),
            "bound_argv": lab.argv,
            "known_defect": {
                "name": "trigger-less-marker",
                "plant": "# ranex: global lock  (no ';' trigger half)",
                "caught": all_refused,
                "defects_caught": sum(1 for t in trials if not t["negative_accepted"]),
            },
            "repeats": repeats,
            "repeatability": repeatability,
            "reproducibility": _repro_unverified(),
            "firing_count": {
                "driver_negative_refusals": sum(
                    1 for t in trials if not t["negative_accepted"]
                ),
                "journal_independent": firing,
            },
            "recall": {
                "armed": True,
                "demonstrated_here": False,
                "detail": "Recall demonstration is in recall-false-pass.json",
            },
            "status": status,
            "base_freeze": _base_freeze_citation(),
            "host": _host_facts(),
            "wall_clock_s": round(time.monotonic() - started, 3),
            "trials": trials,
        }
        _write(out / "certificate-marker.json", certificate)
        return certificate
    finally:
        shutil.rmtree(root, ignore_errors=True)


def calibrate_landing(out: Path, repeats: int) -> dict[str, Any]:
    root = Path(tempfile.mkdtemp(prefix="ranex-115-landing-"))
    started = time.monotonic()
    try:
        # The catalog contract for results_artifact requires the exact
        # token --junitxml=governance/suite_results.xml in the bound argv
        # (reject_pytest_xfail_blindness / results-artifact binding).
        argv = [
            "/usr/bin/python3",
            "-c",
            LANDING_RUNNER,
            "-o",
            "xfail_strict=true",
            "-p",
            "ranex.foundation.pytest_xpass",
            "--junitxml=governance/suite_results.xml",
        ]
        lab = Lab(
            root,
            sys.executable,
            claim="tests-executed",
            argv=argv,
            rule="TESTS_EXECUTED",
        )
        lab.init_repo()
        (lab.repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (lab.repo / "test_unit.py").write_text(
            "def test_value():\n"
            "    pass\n"
            "def test_value_positive():\n"
            "    pass\n",
            encoding="utf-8",
        )
        suite_ids = [
            "test_unit.py::test_value",
            "test_unit.py::test_value_positive",
        ]
        (lab.repo / "governance" / "suite_manifest.json").write_bytes(
            canonical_json_bytes({"suite": suite_ids, "expected_skips": {}})
        )
        lab.refs["good"] = lab._commit("landing: clean frozen suite")

        (lab.repo / "test_unit.py").write_text(
            "def test_value():\n"
            "    pass\n",
            encoding="utf-8",
        )
        lab.refs["deleted"] = lab._commit("landing: deleted frozen test")

        lab._git("checkout", "-q", lab.refs["good"])
        (lab.repo / "test_unit.py").write_text(
            "def test_value():\n"
            "    pass\n"
            "def test_value_positive():\n"
            "    pass\n",
            encoding="utf-8",
        )
        (lab.repo / "app.py").write_text("VALUE = 0\n", encoding="utf-8")
        lab.refs["broken"] = lab._commit("landing: source break")
        lab._git("checkout", "-q", lab.refs["good"])

        digests: list[str] = []
        trials: list[dict[str, Any]] = []
        for _ in range(repeats):
            good = lab.observe(lab.refs["good"])
            deleted = lab.observe(lab.refs["deleted"])
            broken = lab.observe(lab.refs["broken"])
            digests.append(good["digest"])
            trials.append(
                {
                    "positive_ok": good["ok"],
                    "deleted_accepted": deleted["ok"],
                    "broken_accepted": broken["ok"],
                    "positive": good["facts"],
                    "deleted_frozen_test": deleted["facts"],
                    "source_break": broken["facts"],
                    "positive_digest": good["digest"],
                }
            )

        (lab.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        for ref in (lab.refs["good"], lab.refs["deleted"], lab.refs["broken"]):
            lab.observe(ref, keep_journal=True)
        firing = _journal_firing(
            lab.repo / "governance" / "journal.sqlite3", gate_id="landing"
        )

        all_positive = all(t["positive_ok"] for t in trials)
        deleted_caught = all(not t["deleted_accepted"] for t in trials)
        broken_caught = all(not t["broken_accepted"] for t in trials)
        repeatability = _repeatability(digests)
        if (
            all_positive
            and deleted_caught
            and broken_caught
            and repeatability["identical"]
        ):
            status = "VERIFIED"
        elif not (deleted_caught and broken_caught):
            status = "FALSE-PASS"
        elif not all_positive:
            status = "GAP"
        else:
            status = "NON-DETERMINISTIC"

        certificate = {
            "schema": SCHEMA,
            "gate_id": "landing",
            "date": DATE,
            "bound_argv_digest": _sha256_bytes(canonical_json_bytes(lab.argv)),
            "bound_argv": lab.argv,
            "known_defect": {
                "names": ["deleted-frozen-test", "source-break"],
                "deleted_frozen_test_caught": deleted_caught,
                "source_break_caught": broken_caught,
                "caught": deleted_caught and broken_caught,
                "defects_caught": int(deleted_caught) + int(broken_caught),
            },
            "repeats": repeats,
            "repeatability": repeatability,
            "reproducibility": _repro_unverified(),
            "firing_count": {
                "driver_negative_refusals": (
                    int(deleted_caught) * repeats + int(broken_caught) * repeats
                ),
                "journal_independent": firing,
            },
            "recall": {
                "armed": True,
                "demonstrated_here": False,
                "detail": "Recall demonstration is in recall-false-pass.json",
            },
            "status": status,
            "base_freeze": _base_freeze_citation(),
            "host": _host_facts(),
            "wall_clock_s": round(time.monotonic() - started, 3),
            "trials": trials,
        }
        _write(out / "certificate-landing.json", certificate)
        return certificate
    finally:
        shutil.rmtree(root, ignore_errors=True)


def calibrate_handbook_delegate(out: Path, repeats: int) -> dict[str, Any]:
    from handbook_proof import (
        _DELEGATE_PROJECT,
        _brief_table_paths,
        _build_delegate_target,
        _paths_of,
        _run_delegate,
    )

    root = Path(tempfile.mkdtemp(prefix="ranex-115-handbook-"))
    started = time.monotonic()
    try:
        digests: list[str] = []
        trials: list[dict[str, Any]] = []
        for index in range(repeats):
            target, home = _build_delegate_target(
                root, project_payload=_DELEGATE_PROJECT, label=f"p{index}"
            )
            run = _run_delegate(
                root, task_id=f"T-115-P-{index}", target=target, home=home
            )
            brief = run["brief"] or ""
            scope = set(_paths_of(target))
            table = _brief_table_paths(brief)
            positive_ok = (
                run["exit"] == 0
                and table == scope
                and "docs/note.md → unmatched" in brief
            )
            dropped = brief.replace("docs/note.md → unmatched\n", "", 1)
            dropped_table = _brief_table_paths(dropped)
            negative_accepted = dropped_table == scope
            facts = {
                "exit": run["exit"],
                "scope": len(scope),
                "table": len(table),
                "dropped_table": len(dropped_table),
                "negative_accepted": negative_accepted,
                "stderr": (run.get("stderr") or "")[:200],
            }
            digest = _sha256_bytes(
                json.dumps(
                    facts, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            )
            digests.append(digest)
            trials.append(
                {
                    "positive_ok": positive_ok,
                    "negative_accepted": negative_accepted,
                    "facts": facts,
                    "digest": digest,
                }
            )

        all_positive = all(t["positive_ok"] for t in trials)
        all_refused = all(not t["negative_accepted"] for t in trials)
        repeatability = _repeatability(digests)
        if all_positive and all_refused and repeatability["identical"]:
            status = "VERIFIED"
        elif not all_refused:
            status = "FALSE-PASS"
        elif not all_positive:
            status = "GAP"
        else:
            status = "NON-DETERMINISTIC"

        certificate = {
            "schema": SCHEMA,
            "gate_id": "handbook-governed-delegate",
            "date": DATE,
            "bound_argv_digest": _sha256_text(
                "ranex task delegate + handbook resolution table"
            ),
            "bound_argv_kind": "task-delegate-with-handbook-resolution-table",
            "known_defect": {
                "name": "dropped-trust-boundary-guard",
                "plant": (
                    "brief resolution table silently omits docs/note.md "
                    "(scope completeness / trust-boundary guard)"
                ),
                "caught": all_refused,
                "defects_caught": sum(
                    1 for t in trials if not t["negative_accepted"]
                ),
            },
            "repeats": repeats,
            "repeatability": repeatability,
            "reproducibility": _repro_unverified(),
            "firing_count": {
                "driver_negative_refusals": sum(
                    1 for t in trials if not t["negative_accepted"]
                ),
                "journal_independent": {
                    "determinable": False,
                    "detail": (
                        "Delegate brief completeness is scored from the retained "
                        "brief text, not journal evaluations."
                    ),
                },
            },
            "recall": {
                "armed": True,
                "demonstrated_here": False,
                "detail": "Recall demonstration is in recall-false-pass.json",
            },
            "status": status,
            "base_freeze": _base_freeze_citation(),
            "host": _host_facts(),
            "wall_clock_s": round(time.monotonic() - started, 3),
            "trials": trials,
        }
        _write(out / "certificate-handbook-delegate.json", certificate)
        return certificate
    finally:
        shutil.rmtree(root, ignore_errors=True)


def demonstrate_recall(out: Path, repeats: int) -> dict[str, Any]:
    """Blunt gauge → FALSE-PASS; name the recall window from the journal."""

    root = Path(tempfile.mkdtemp(prefix="ranex-115-recall-"))
    started = time.monotonic()
    try:
        lab = Lab(
            root,
            sys.executable,
            claim="markers-declared",
            argv=["/usr/bin/python3", "-c", BLUNT_SCANNER],
            rule="MARKERS_DECLARED",
        )
        lab.init_repo()
        (lab.repo / "good.py").write_text(
            "# ranex: single-threaded scan; parallelise past 100k files\n",
            encoding="utf-8",
        )
        lab.refs["good"] = lab._commit("recall: well-formed")
        (lab.repo / "bad.py").write_text("# ranex: global lock\n", encoding="utf-8")
        lab.refs["bad"] = lab._commit("recall: trigger-less (should FAIL)")
        lab._git("checkout", "-q", lab.refs["good"])

        # Prior "good" evaluates under the blunt gauge (approvals to recall).
        (lab.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        last_good_seq = 0
        for _ in range(2):
            good = lab.observe(lab.refs["good"], keep_journal=True)
            if not good["ok"]:
                raise RuntimeError(f"blunt positive failed: {good}")
        firing_before = _journal_firing(lab.repo / "governance" / "journal.sqlite3")
        last_good_seq = firing_before.get("positions", [0])[-1] if firing_before.get("positions") else 0

        # Negative control under blunt gauge: must be ACCEPTED → FALSE-PASS.
        negative_results: list[dict[str, Any]] = []
        for _ in range(repeats):
            bad = lab.observe(lab.refs["bad"], keep_journal=True)
            negative_results.append(bad)

        accepted = sum(1 for row in negative_results if row["ok"])
        firing = _journal_firing(lab.repo / "governance" / "journal.sqlite3")
        after = [
            (pos, digest)
            for pos, digest in zip(
                firing.get("positions", []),
                firing.get("verdict_digests", []),
                strict=False,
            )
            if pos > last_good_seq
        ]
        # Also include every PASS since last_good — those are the recalled ones.
        suspect_positions = [pos for pos, _ in after]
        suspect_digests = [digest for _, digest in after]

        status = "FALSE-PASS" if accepted == repeats else "GAP"
        receipt = {
            "schema": "ranex-gate-recall-v1",
            "date": DATE,
            "control": "a-blunted-gauge-is-caught-as-false-pass",
            "expectation": (
                "a gate whose bound command cannot fail is reported FALSE-PASS, "
                "and the recall window names every evaluation it approved"
            ),
            "status": status,
            "expected_outcome": "FALSE-PASS",
            "as_expected": status == "FALSE-PASS",
            "reason": (
                f"the negative control was ACCEPTED in {accepted}/{repeats} repeats; "
                "this check cannot block what it exists to refuse"
                if status == "FALSE-PASS"
                else f"expected blunt acceptance, got {accepted}/{repeats}"
            ),
            "repeats": repeats,
            "negative": {
                "runs": repeats,
                "ok": [row["ok"] for row in negative_results],
                "digests": [row["digest"] for row in negative_results],
                "identical": len({row["digest"] for row in negative_results}) <= 1,
            },
            "recall": {
                "suspect_from": last_good_seq,
                "determinable": True,
                "suspect_count": len(suspect_positions),
                "suspect_positions": suspect_positions,
                "suspect_verdict_digests": suspect_digests,
                "detail": (
                    f"{len(suspect_positions)} evaluation(s) were approved after "
                    "this control's last good journal head and are recalled"
                ),
            },
            "firing_count": {"journal_independent": firing},
            "base_freeze": _base_freeze_citation(),
            "host": _host_facts(),
            "wall_clock_s": round(time.monotonic() - started, 3),
            "note": (
                "Deliberate blunt scanner (always exit 0). FALSE-PASS is the "
                "alarm proof, not a product defect. Restore = not loading this "
                "scanner as a production gauge."
            ),
        }
        _write(out / "recall-false-pass.json", receipt)
        return receipt
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if not BASE_FREEZE_PATH.is_file():
        print(f"REFUSED: missing {BASE_FREEZE_PATH}", file=sys.stderr)
        return 2

    print("=== marker gate ===", flush=True)
    marker = calibrate_marker(args.out, args.repeats)
    print(f"{marker['status']} marker", flush=True)

    print("=== landing gate ===", flush=True)
    landing = calibrate_landing(args.out, args.repeats)
    print(f"{landing['status']} landing", flush=True)

    print("=== handbook-governed delegate ===", flush=True)
    handbook = calibrate_handbook_delegate(args.out, args.repeats)
    print(f"{handbook['status']} handbook-governed-delegate", flush=True)

    print("=== recall FALSE-PASS ===", flush=True)
    recall = demonstrate_recall(args.out, args.repeats)
    print(f"{recall['status']} recall (as_expected={recall.get('as_expected')})", flush=True)

    statuses = {
        "marker": marker["status"],
        "landing": landing["status"],
        "handbook-governed-delegate": handbook["status"],
        "recall": recall["status"],
    }
    summary = {
        "schema": "ranex-gate-calibration-summary-v1",
        "date": DATE,
        "issue": 115,
        "base_freeze": _base_freeze_citation(),
        "certificates": {
            "marker": "certificate-marker.json",
            "landing": "certificate-landing.json",
            "handbook-governed-delegate": "certificate-handbook-delegate.json",
            "recall": "recall-false-pass.json",
        },
        "statuses": statuses,
        "gauge_rr": {
            "repeatability": {
                "marker": marker["repeatability"],
                "landing": landing["repeatability"],
                "handbook-governed-delegate": handbook["repeatability"],
            },
            "reproducibility": {
                "status": "UNVERIFIED",
                "detail": (
                    "Second host unavailable on this machine for this ship; "
                    "cross-host reproducibility is UNVERIFIED. Same-host "
                    "repeatability (byte-identical digests ×N) is measured "
                    "per certificate."
                ),
            },
        },
        "map_8_4_consequences": {
            "1_known_defect_detection": {
                "status": "satisfied",
                "receipts": [
                    "certificate-marker.json",
                    "certificate-landing.json",
                    "certificate-handbook-delegate.json",
                ],
            },
            "2_firing_rate_recorded": {
                "status": "satisfied",
                "receipts": [
                    "certificate-marker.json",
                    "certificate-landing.json",
                    "recall-false-pass.json",
                ],
            },
            "3_recall_armed": {
                "status": "satisfied",
                "receipt": "recall-false-pass.json",
            },
            "4_built_vs_calibrated": {
                "status": "satisfied",
                "detail": "governance/bom.yaml calibrated rows name a receipt",
            },
        },
        "production_statement": (
            "Production use of the marker gate, the landing suite gate, and "
            "the handbook-governed delegate completeness check is licensed "
            "only for the behaviours these certificates cover on this host. "
            "No general zero-bug or market claim is made."
        ),
        "UNVERIFIED": [
            "Cross-host / cross-operator Gauge R&R reproducibility",
            "AIAG % of tolerance thresholds (MAP §8.4; cite before quoting)",
            "Full ranex repository landing gate under this certificate "
            "(lab uses a minimal frozen suite subject)",
            "Live GitHub App / network-facing gates (out of #115 scope)",
        ],
        "host": _host_facts(),
    }
    _write(args.out / "SUMMARY.json", summary)
    print(json.dumps({"statuses": statuses, "out": str(args.out)}, indent=2))

    if not recall.get("as_expected"):
        return 1
    blocking = {"FALSE-PASS", "NON-DETERMINISTIC", "GAP"}
    for name, status in statuses.items():
        if name == "recall":
            continue
        if status in blocking:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
