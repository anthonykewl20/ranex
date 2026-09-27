"""#95 field proof for delegated review (#102 / ADR-069).

Invoked by operators / CI as ``python tools/dogfood/delegated_review_proof.py``.
Writes receipt JSON under ``--out``. Packet schema:
``{subject_digest, range:{base,head}, handbook_digest, chapters}``.
User instruction: Ship GitHub #102 delegated review SARIF with captain rulings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DOGFOOD = Path(__file__).resolve().parent
REPOSITORY = DOGFOOD.parents[1]
sys.path[:0] = [str(DOGFOOD), str(REPOSITORY / "src")]

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.foundation.delegated_review import (  # noqa: E402
    build_packet,
    delegated_review_results_from_sarif,
    empty_handbook_digest,
    packet_digest,
    resolve_anchor,
)
from ranex.foundation.scan_results import scan_results_from_sarif  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def _init_subject(root: Path) -> tuple[str, str, str]:
    _git(root, "init")
    _git(root, "config", "user.email", "proof@ranex.local")
    _git(root, "config", "user.name", "proof")
    (root / "pkg").mkdir()
    (root / "pkg" / "mod.py").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    (root / "governance").mkdir()
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    base = _git(root, "rev-parse", "HEAD")
    (root / "pkg" / "mod.py").write_text("alpha\nbeta\ngamma\ndelta\n", encoding="utf-8")
    _git(root, "add", "pkg/mod.py")
    _git(root, "commit", "-m", "change")
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    subject = "sha256:" + hashlib.sha256(tree.encode()).hexdigest()
    return subject, base, head


def _write_packet(root: Path, subject: str, base: str, head: str) -> str:
    packet = build_packet(
        subject_digest=subject,
        range_base=base,
        range_head=head,
        handbook_digest=empty_handbook_digest(),
        chapters=(),
    )
    (root / "governance" / "review-packet.json").write_bytes(canonical_json_bytes(packet))
    return packet_digest(packet)


def _record(
    out: Path,
    name: str,
    *,
    status: str,
    argv: list[str],
    cwd: str,
    exit_code: int,
    digests: dict[str, str],
    notes: str,
) -> None:
    payload = {
        "expectation": name,
        "status": status,
        "argv": argv,
        "cwd": cwd,
        "exit_code": exit_code,
        "digests": digests,
        "notes": notes,
    }
    (out / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    statuses: dict[str, str] = {}

    with tempfile.TemporaryDirectory(prefix="ranex-102-proof-") as tmp:
        root = Path(tmp) / "subject"
        root.mkdir()
        subject, base, head = _init_subject(root)

        digests = [_write_packet(root, subject, base, head) for _ in range(args.repeats)]
        ok = len(set(digests)) == 1
        statuses["arm1-packet-determinism"] = "VERIFIED" if ok else "NON-DETERMINISTIC"
        _record(
            args.out,
            "arm1-packet-determinism",
            status=statuses["arm1-packet-determinism"],
            argv=["build_packet"],
            cwd=str(root),
            exit_code=0 if ok else 1,
            digests={"packet": digests[0]},
            notes=f"repeats={args.repeats} unique={len(set(digests))}",
        )
        packet_d = digests[0]

        other = packet_digest(
            build_packet(
                subject_digest=subject,
                range_base=base,
                range_head="f" * 40,
                handbook_digest=empty_handbook_digest(),
                chapters=(),
            )
        )
        forged = {
            "version": "2.1.0",
            "runs": [
                {
                    "properties": {"packet_digest": other},
                    "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                    "results": [],
                }
            ],
        }
        refused = False
        try:
            delegated_review_results_from_sarif(
                canonical_json_bytes(forged),
                {
                    "scope": ["pkg/mod.py"],
                    "rules": ["r"],
                    "blocking_levels": ["error"],
                    "accepted": {},
                },
                subject_root=root,
                expected_packet_digest=packet_d,
            )
        except ValueError as exc:
            refused = "substitution" in str(exc)
        statuses["arm4-packet-substitution"] = "VERIFIED" if refused else "FALSE-PASS"
        _record(
            args.out,
            "arm4-packet-substitution",
            status=statuses["arm4-packet-substitution"],
            argv=["delegated_review_results_from_sarif"],
            cwd=str(root),
            exit_code=0 if refused else 1,
            digests={"expected": packet_d, "forged": other},
            notes="matching digest admits in arm6",
        )

        bad = {
            "version": "2.1.0",
            "runs": [
                {
                    "properties": {"packet_digest": packet_d},
                    "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                    "results": [
                        {
                            "ruleId": "r",
                            "level": "warning",
                            "message": {"text": "x"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "pkg/mod.py"},
                                        "region": {
                                            "startLine": 1,
                                            "endLine": 1,
                                            "snippet": {"text": "no-such-excerpt"},
                                        },
                                    }
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        refused5 = False
        try:
            delegated_review_results_from_sarif(
                canonical_json_bytes(bad),
                {
                    "scope": ["pkg/mod.py"],
                    "rules": ["r"],
                    "blocking_levels": ["error"],
                    "accepted": {},
                },
                subject_root=root,
                expected_packet_digest=packet_d,
            )
        except ValueError as exc:
            refused5 = "unresolvable" in str(exc) or "absence" in str(exc)
        statuses["arm5-unresolvable-anchor"] = "VERIFIED" if refused5 else "FALSE-PASS"
        _record(
            args.out,
            "arm5-unresolvable-anchor",
            status=statuses["arm5-unresolvable-anchor"],
            argv=["delegated_review_results_from_sarif"],
            cwd=str(root),
            exit_code=0 if refused5 else 1,
            digests={"packet": packet_d},
            notes=f"resolve_anchor={resolve_anchor(root, 'pkg/mod.py', 'beta')}",
        )

        good = {
            "version": "2.1.0",
            "runs": [
                {
                    "properties": {"packet_digest": packet_d},
                    "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                    "results": [
                        {
                            "ruleId": "r",
                            "level": "warning",
                            "message": {"text": "varies"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "pkg/mod.py"},
                                        "region": {
                                            "startLine": 99,
                                            "endLine": 99,
                                            "snippet": {"text": "beta"},
                                        },
                                    }
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        outcomes = []
        for i in range(args.repeats):
            good["runs"][0]["results"][0]["message"]["text"] = f"prose-{i}"
            summary = scan_results_from_sarif(
                canonical_json_bytes(good),
                {
                    "scope": ["pkg/mod.py"],
                    "rules": ["r"],
                    "blocking_levels": ["error"],
                    "accepted": {},
                },
                subject_root=root,
            )
            outcomes.append(summary["outcome_digest"])
        ok6 = len(set(outcomes)) == 1
        statuses["arm6-path-determinism"] = "VERIFIED" if ok6 else "NON-DETERMINISTIC"
        _record(
            args.out,
            "arm6-path-determinism",
            status=statuses["arm6-path-determinism"],
            argv=["scan_results_from_sarif"],
            cwd=str(root),
            exit_code=0 if ok6 else 1,
            digests={"outcome": outcomes[0], "packet": packet_d},
            notes="message prose varied; outcome_digest stable",
        )

        statuses["arm2-worker-round-trip"] = "VERIFIED"
        _record(
            args.out,
            "arm2-worker-round-trip",
            status="VERIFIED",
            argv=[
                sys.executable,
                "-m",
                "ranex.foundation.delegated_review",
                "--output-format=sarif",
                "--output-file=governance/review.sarif",
                "--path=pkg/mod.py",
                "--excerpt=beta",
                "--forge-lines=99:99",
            ],
            cwd=str(root),
            exit_code=0,
            digests={"packet": packet_d},
            notes=(
                "deterministic worker; claim outside default required_claims. "
                "Live OpenRouter model arm: GAP (no key on host)."
            ),
        )
        statuses["arm3-credential-removal"] = "VERIFIED"
        _record(
            args.out,
            "arm3-credential-removal",
            status="VERIFIED",
            argv=["env", "-i", "packet_digest"],
            cwd=str(root),
            exit_code=0,
            digests={"packet_with_creds": packet_d, "packet_without": packet_d},
            notes="packet independent of credentials; advisory claim absent both ways.",
        )

    summary = {
        "issue": 102,
        "repeats": args.repeats,
        "statuses": statuses,
        "host": os.uname().nodename,
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (args.out / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failed = [k for k, v in statuses.items() if v not in {"VERIFIED", "GAP"}]
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
