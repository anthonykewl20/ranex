"""Issue #107 field proof — the authenticated approver (RISK-07), real data.

Arms (status vocabulary: VERIFIED | GAP | FALSE-PASS | NON-DETERMINISTIC |
UNVERIFIED; repeats are three identical-input runs unless noted):

On the REAL repository, its committed catalog and the operator host's real
keys (`~/.config/ranex/approver.key`, registered as `release-approver`):

  R1 possession positive: the real approver key passes possession and the
     judgment runs (exit 0/1 — never the possession refusal's 2).
  R2 key absent: exit 2, E-APPROVER-KEY-ABSENT, journal row count unchanged.
  R3 worker's key as the approver: exit 2, E-APPROVER-ROLE.
  R4 unknown approver id: exit 2, E-APPROVER-UNKNOWN.
  R5 worker's key under the approver's id: exit 2, E-APPROVER-KEY-MISMATCH.
  R6 the kernel did not move: sha256(verdict.py) equals the BASE freeze's
     kernel_digest — the judgment code is byte-identical to the frozen one.

In a governed lab cloned from this repository (its own real keygen keys,
its catalog a committed diff, publication env configured):

  L1 two-signature publication: the verdict carries the verdict signer's
     and the approver's signatures over the same content; three
     identical-state repeats produce byte-identical verdict bytes.
  L2 openssl — a non-kernel tool — verifies BOTH signatures out of band.
  L3 stripped approver signature: `journal verify --against-verdict`
     refuses naming unapproved; altered: refuses naming bad-signature.
  L4 one key under two principals: the catalog refuses to load.
  L5 the approver principal as evidence producer: possession passes and
     the kernel's unchanged no-self-approval check FAILs the gate
     (self_approval=true in the published FAIL verdict).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
AUDIT = Path(__file__).resolve().parent
RANEX = str(REPO / ".venv" / "bin" / "ranex")
# The stage holds private keys, so it must live OUTSIDE the repository —
# `keygen` refuses to write a committable key, and the audit directory
# carries only the receipts.
STAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    tempfile.mkdtemp(prefix="ranex-107-receipt-")
)
APPROVER_KEY = Path.home() / ".config" / "ranex" / "approver.key"
WORKER_KEY = Path.home() / ".config" / "ranex" / "anthony.key"
REPEATS = 3
ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

records: list[dict[str, object]] = []


def run_cli(target: Path, argv: list[str], env: dict[str, str] | None = None,
            **kwargs: object) -> dict[str, object]:
    """Judge a target through ITS OWN source (the clone judges the clone),
    never through the checkout this receipt runs from (ADR-038)."""

    child = dict(env or {})
    child["PYTHONPATH"] = str(target / "src")
    return run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=target, env=child, **kwargs,  # type: ignore[arg-type]
    )


def run(argv: list[str], *, cwd: Path, env: dict[str, str] | None = None,
        timeout: float = 300.0) -> dict[str, object]:
    started = time.monotonic()
    child = {k: v for k, v in os.environ.items() if k not in {
        "RANEX_SIGNING_KEY", "RANEX_VERDICT_SIGNING_KEY", "RANEX_VERDICT_DIR",
        "RANEX_APPROVER_SIGNING_KEY",
    }}
    child.update(env or {})
    completed = subprocess.run(
        argv, cwd=str(cwd), capture_output=True, text=True, check=False,
        env=child, timeout=timeout,
    )
    return {
        "argv": [str(part) for part in argv],
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_tail": completed.stdout[-1500:],
        "stderr_tail": completed.stderr[-1500:],
    }


def journal_rows(repository: Path) -> int:
    journal = repository / "governance" / "journal.sqlite3"
    if not journal.is_file():
        return 0
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        return int(connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0])
    finally:
        connection.close()


def arm(name: str, status: str, detail: str, **evidence: object) -> None:
    records.append({"arm": name, "status": status, "detail": detail, **evidence})
    print(f"{status} {name}: {detail}")


def evaluate(repository: Path, approver: str, *, env: dict[str, str] | None = None,
             journal: str = "governance/journal.sqlite3") -> dict[str, object]:
    return run(
        [RANEX, "gate", "evaluate", "HEAD", "--approver", approver,
         "--journal", journal],
        cwd=repository, env=env,
    )


def real_repo_arms() -> None:
    before = journal_rows(REPO)
    # R1 — the real key passes possession; the judgment runs. The receipt
    # journal is a scratch path: the arm must not touch the operator's.
    outcomes = []
    for _ in range(REPEATS):
        possession = evaluate(
            REPO, "release-approver",
            env={"RANEX_APPROVER_SIGNING_KEY": str(APPROVER_KEY)},
            journal="governance/receipt-journal.sqlite3",
        )
        outcomes.append(possession["exit_code"])
    if all(code in (0, 1) for code in outcomes) and len(set(outcomes)) == 1:
        arm("R1-possession-positive", "VERIFIED",
            f"the real approver key reached judgment {REPEATS}x (exits {outcomes})",
            repeats=outcomes)
    else:
        arm("R1-possession-positive", "NON-DETERMINISTIC",
            f"identical inputs gave differing exits {outcomes}", repeats=outcomes)

    # R2..R5 — the refusals, each repeated on identical input.
    expectations = [
        ("R2-key-absent", "release-approver", {}, "E-APPROVER-KEY-ABSENT"),
        ("R3-worker-as-approver", "anthony",
         {"RANEX_APPROVER_SIGNING_KEY": str(WORKER_KEY)}, "E-APPROVER-ROLE"),
        ("R4-unknown-approver", "ghost",
         {"RANEX_APPROVER_SIGNING_KEY": str(APPROVER_KEY)}, "E-APPROVER-UNKNOWN"),
        ("R5-key-mismatch", "release-approver",
         {"RANEX_APPROVER_SIGNING_KEY": str(WORKER_KEY)}, "E-APPROVER-KEY-MISMATCH"),
    ]
    for name, approver, env, code in expectations:
        exits: list[int] = []
        named = True
        for _ in range(REPEATS):
            refusal = evaluate(REPO, approver, env=env,
                               journal="governance/receipt-journal.sqlite3")
            exits.append(int(refusal["exit_code"]))
            named = named and code in str(refusal["stderr_tail"])
        after = journal_rows(REPO)
        if all(exit_code == 2 for exit_code in exits) and named and after == before:
            arm(name, "VERIFIED",
                f"exit 2 naming {code} {REPEATS}x; journal rows {before}->{after}",
                repeats=exits, code=code)
        else:
            arm(name, "GAP",
                f"exits {exits}, named={named}, rows {before}->{after}",
                repeats=exits, code=code)

    # R6 — the kernel did not move.
    kernel = hashlib.sha256(
        (REPO / "src/ranex/governed_execution/domain/verdict.py").read_bytes()
    ).hexdigest()
    freeze = json.loads(
        (REPO / "governance/calibration/base-freeze-v1.json").read_text(encoding="utf-8")
    )
    frozen = freeze["kernel_digest"].removeprefix("sha256:")
    arm("R6-kernel-unchanged",
        "VERIFIED" if kernel == frozen else "FALSE-PASS",
        f"sha256(verdict.py)={'matches' if kernel == frozen else 'DRIFTS from'} "
        "the BASE freeze digest",
        kernel_digest=f"sha256:{kernel}", frozen_digest=f"sha256:{frozen}")
    (REPO / "governance/receipt-journal.sqlite3").unlink(missing_ok=True)


def published_verdicts(directory: Path) -> list[Path]:
    """The signed verdict publications, never the repair envelopes."""

    return sorted(
        path for path in directory.glob("*.json")
        if not path.name.endswith(".envelope.json")
    )


def git_commit(repository: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-qm", message],
        check=True, env={**os.environ, "GIT_AUTHOR_NAME": "receipt",
                         "GIT_AUTHOR_EMAIL": "receipt@ranex.local",
                         "GIT_COMMITTER_NAME": "receipt",
                         "GIT_COMMITTER_EMAIL": "receipt@ranex.local"},
    )


def keygen(lab: Path, name: str) -> tuple[Path, str]:
    path = STAGE / f"{name}.key"
    generated = run_cli(
        lab, ["keygen", "--producer", name], env={"RANEX_SIGNING_KEY": str(path)}
    )
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", str(generated["stdout_tail"]))
    assert generated["exit_code"] == 0 and match, generated
    return path, match.group(1)


def lab_arms() -> None:
    branch = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    lab = STAGE / "lab"
    cloned = subprocess.run(
        ["git", "clone", "-q", "--branch", branch, str(REPO), str(lab)],
        capture_output=True, text=True, check=False,
    )
    assert cloned.returncode == 0, cloned.stderr
    worker_key, worker_public = keygen(lab, "worker")
    approver_key, approver_public = keygen(lab, "approver")
    signer_key, signer_public = keygen(lab, "verdict-signer")

    catalog = lab / "governance" / "producers.yaml"
    catalog.write_text(
        "producers:\n"
        f"  worker: {worker_public}\n"
        "verdict_signer:\n"
        "  id: kernel-verdict-signer\n"
        f"  public_key: {signer_public}\n"
        "principals:\n"
        f"  worker:\n    role: worker\n    keys:\n"
        f"      - key: {worker_public}\n        status: active\n"
        f"  release-approver:\n    role: approver\n    keys:\n"
        f"      - key: {approver_public}\n        status: active\n"
        "  kernel-verdict-signer:\n    role: service\n    keys:\n"
        f"      - key: {signer_public}\n        status: active\n",
        encoding="utf-8",
    )
    (lab / "governance" / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: approver-lab\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: tree-clean\n"
        '        command: ["git", "status", "--porcelain"]\n',
        encoding="utf-8",
    )
    (lab / "governance" / "deps.yaml").unlink(missing_ok=True)
    git_commit(lab, "the lab's trust root")
    recorded = run_cli(
        lab,
        ["run", "--claim", "tree-clean", "--producer", "worker",
         "--gate", "approver-lab", "--", "git", "status", "--porcelain"],
        env={"RANEX_SIGNING_KEY": str(worker_key)},
    )
    assert recorded["exit_code"] == 0, recorded
    pristine = STAGE / "lab-identical"
    shutil.copytree(lab, pristine)

    publication = {
        "RANEX_VERDICT_SIGNING_KEY": str(signer_key),
        "RANEX_VERDICT_DIR": "governance/verdicts",
        "RANEX_APPROVER_SIGNING_KEY": str(approver_key),
    }

    # L1 — two signatures; identical-state repeats are byte-identical.
    judged = run_cli(
        lab,
        ["gate", "evaluate", "HEAD", "--gate", "approver-lab",
         "--approver", "release-approver"], env=publication,
    )
    verdicts = published_verdicts(lab / "governance/verdicts")
    assert judged["exit_code"] == 0 and len(verdicts) == 1, judged
    verdict_bytes = verdicts[0].read_bytes()
    verdict = json.loads(verdict_bytes)
    signers = [entry["signer_id"] for entry in verdict["signatures"]]
    repeat_bytes = {verdict_bytes}
    for attempt in range(REPEATS - 1):
        copy = STAGE / f"lab-repeat-{attempt}"
        shutil.copytree(pristine, copy)
        repeated = run_cli(
            copy,
            ["gate", "evaluate", "HEAD", "--gate", "approver-lab",
             "--approver", "release-approver"], env=publication,
        )
        assert repeated["exit_code"] == 0, repeated
        repeat_bytes.add(published_verdicts(copy / "governance/verdicts")[0].read_bytes())
    if signers == ["kernel-verdict-signer", "release-approver"] and len(repeat_bytes) == 1:
        arm("L1-two-signature-publication", "VERIFIED",
            f"signers={signers}; {REPEATS} identical-state runs -> "
            f"{len(repeat_bytes)} distinct verdict byte-sets",
            signers=signers,
            verdict_sha256=hashlib.sha256(verdict_bytes).hexdigest())
    else:
        arm("L1-two-signature-publication", "NON-DETERMINISTIC",
            f"signers={signers}, distinct={len(repeat_bytes)}")

    # L2 — openssl verifies BOTH signatures over the domain-bound payload.
    sys.path.insert(0, str(REPO / "src"))
    from ranex.foundation.verdict_signing import signed_payload  # noqa: E402

    content = dict(verdict["record"])
    content.pop("record_digest", None)
    payload = STAGE / "payload.bin"
    payload.write_bytes(signed_payload(content))
    verified = {}
    for name, entry, public in (
        ("signer", verdict["signatures"][0], signer_public),
        ("approver", verdict["signatures"][1], approver_public),
    ):
        sig = STAGE / f"{name}.sig"
        sig.write_bytes(base64.b64decode(entry["signature"].removeprefix("ed25519:")))
        der = STAGE / f"{name}.der"
        der.write_bytes(
            ED25519_SPKI_PREFIX + base64.b64decode(public.removeprefix("ed25519:"))
        )
        check = run(
            ["openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
             "-inkey", str(der), "-rawin", "-in", str(payload),
             "-sigfile", str(sig)],
            cwd=STAGE,
        )
        verified[name] = check["exit_code"] == 0
    arm("L2-openssl-both-signatures",
        "VERIFIED" if all(verified.values()) else "GAP",
        f"openssl out-of-band verification: {verified}")

    # L3 — stripped and altered approver signatures anchor nothing.
    refusal_states = {}
    for variant in ("stripped", "altered"):
        tampered = STAGE / f"lab-{variant}"
        shutil.copytree(lab, tampered)
        target = published_verdicts(tampered / "governance/verdicts")[0]
        document = json.loads(target.read_text(encoding="utf-8"))
        if variant == "stripped":
            document["signatures"] = document["signatures"][:1]
        else:
            document["signatures"][1]["signature"] = (
                document["signatures"][1]["signature"][:-1] + "B"
            )
        target.chmod(0o644)
        target.write_text(json.dumps(document), encoding="utf-8")
        anchor = run_cli(
            tampered,
            ["journal", "verify", "--journal", "governance/journal.sqlite3",
             "--against-verdict", str(target.relative_to(tampered))],
        )
        text = f"{anchor['stdout_tail']}{anchor['stderr_tail']}".lower()
        refusal_states[variant] = (
            anchor["exit_code"] != 0
            and ("unapproved" in text if variant == "stripped" else "bad-signature" in text)
        )
    arm("L3-tampered-verdict-anchors-nothing",
        "VERIFIED" if all(refusal_states.values()) else "GAP",
        f"journal verify --against-verdict refusals: {refusal_states}")

    # L4 — one key under two principals: the catalog refuses to load.
    collision = STAGE / "lab-collision"
    shutil.copytree(pristine, collision)
    colliding = (collision / "governance/producers.yaml").read_text(encoding="utf-8")
    (collision / "governance/producers.yaml").write_text(
        colliding.replace(approver_public, worker_public), encoding="utf-8"
    )
    git_commit(collision, "the colliding trust root")
    refused = run_cli(
        collision,
        ["gate", "evaluate", "HEAD", "--gate", "approver-lab",
         "--approver", "release-approver"],
        env={"RANEX_APPROVER_SIGNING_KEY": str(worker_key)},
    )
    text = f"{refused['stdout_tail']}{refused['stderr_tail']}"
    arm("L4-one-key-two-principals",
        "VERIFIED" if refused["exit_code"] == 2 and "share a public key" in text else "GAP",
        f"exit {refused['exit_code']}; refusal names the shared key")

    # L5 — the approver as producer: the kernel's own check refuses.
    self_approval = STAGE / "lab-selfapproval"
    shutil.copytree(pristine, self_approval)
    (self_approval / "governance/producers.yaml").write_text(
        (self_approval / "governance/producers.yaml").read_text(encoding="utf-8").replace(
            "producers:\n", f"producers:\n  release-approver: {approver_public}\n"
        ),
        encoding="utf-8",
    )
    git_commit(self_approval, "the approver produces")
    produced = run_cli(
        self_approval,
        ["run", "--claim", "tree-clean", "--producer", "release-approver",
         "--gate", "approver-lab", "--", "git", "status", "--porcelain"],
        env={"RANEX_SIGNING_KEY": str(approver_key)},
    )
    judged_self = run_cli(
        self_approval,
        ["gate", "evaluate", "HEAD", "--gate", "approver-lab",
         "--approver", "release-approver"], env=publication,
    )
    published = published_verdicts(self_approval / "governance/verdicts")
    record = (
        json.loads(published[0].read_text(encoding="utf-8"))["record"]
        if published else {}
    )
    arm("L5-kernel-self-approval-refuses",
        "VERIFIED" if (
            produced["exit_code"] == 0 and judged_self["exit_code"] == 1
            and record.get("self_approval") is True
        ) else "GAP",
        f"run exit {produced['exit_code']}, evaluate exit "
        f"{judged_self['exit_code']}, self_approval={record.get('self_approval')}",
        reason=record.get("reason"))


def main() -> None:
    STAGE.mkdir(parents=True, exist_ok=True)
    real_repo_arms()
    lab_arms()
    receipt = {
        "issue": "anthonykewl20/ranex#107",
        "risk": "RISK-07",
        "protocol": "#95 — real subprocesses, no mocked seams, "
                    "positive/negative controls, 3 identical-input repeats",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "kernel_commit": subprocess.run(
                ["git", "-C", str(REPO), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True,
            ).stdout.strip(),
        },
        "arms": records,
    }
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    statuses = [str(record["status"]) for record in records]
    (AUDIT / "summary.json").write_text(
        json.dumps(
            {"arms": len(statuses),
             "verified": statuses.count("VERIFIED"),
             "other": {status: statuses.count(status)
                       for status in set(statuses) if status != "VERIFIED"}},
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"arms": len(statuses), "verified": statuses.count("VERIFIED")}))


if __name__ == "__main__":
    main()
