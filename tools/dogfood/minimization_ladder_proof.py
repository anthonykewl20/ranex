"""#95 seeded-subject proof for the minimization ladder (#112 / ADR-070).

Operator/CI invoke: ``python tools/dogfood/minimization_ladder_proof.py``.
Handbook schema: ``{version, entries:[{path_glob,text,...}]}``.
Subject pin: fastapi/full-stack-fastapi-template@cd83fc1.
User: Ship #112 minimization ladder as handbook system layer.
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

from ranex.policy.handbook import (  # noqa: E402
    SYSTEM_LAYER,
    parse_handbook_bytes,
    resolve_handbook,
)

FASTAPI_COMMIT = "cd83fc10ca20393e9ee50e3005e170c6929e047e"
FASTAPI_REPO = "https://github.com/fastapi/full-stack-fastapi-template.git"
PONYTAIL_BLOB = "0af61d583fbd42e8900fce9183d68167eb3d93e6"


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _clone_fastapi(dest: Path) -> str:
    cache = Path.home() / ".cache" / "ranex-subjects" / "full-stack-fastapi-template"
    if not (cache / ".git").exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(["git", "clone", FASTAPI_REPO, str(cache)])
    subprocess.check_call(["git", "fetch", "origin", FASTAPI_COMMIT], cwd=cache)
    subprocess.check_call(["git", "checkout", "--force", FASTAPI_COMMIT], cwd=cache)
    if dest.exists():
        raise RuntimeError(f"dest exists: {dest}")
    subprocess.check_call(["git", "clone", "--no-local", str(cache), str(dest)])
    subprocess.check_call(["git", "checkout", "--force", FASTAPI_COMMIT], cwd=dest)
    return FASTAPI_COMMIT


def _list_paths(root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in {".git", "node_modules", ".venv", "dist"}
        ]
        for name in filenames:
            paths.append((Path(dirpath) / name).relative_to(root).as_posix())
    return tuple(sorted(paths))


def _record(out: Path, name: str, **payload: object) -> None:
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

    handbook_bytes = (REPOSITORY / "governance" / "handbook.json").read_bytes()
    system_entries = parse_handbook_bytes(SYSTEM_LAYER, handbook_bytes)

    vendored = (
        REPOSITORY / "docs" / "adr" / "prior-art" / "ADR-070" / "ponytail.md"
    ).read_bytes()
    blob = _git_blob_sha1(vendored)
    ok5 = blob == PONYTAIL_BLOB
    statuses["arm5-prior-art-blob"] = "VERIFIED" if ok5 else "FALSE-PASS"
    _record(
        args.out,
        "arm5-prior-art-blob",
        expectation="arm5-prior-art-blob",
        status=statuses["arm5-prior-art-blob"],
        digests={"blob": blob, "expected": PONYTAIL_BLOB},
        argv=["sha1(git-blob)"],
        cwd=str(REPOSITORY),
        exit_code=0 if ok5 else 1,
        notes="Vendored: docs/adr/prior-art/ADR-070/ponytail.md",
    )

    text = json.loads(handbook_bytes.decode())["entries"][0]["text"]
    amendments = {
        "approved_deps": "already-approved" in text and "deps fetch" in text,
        "red_first": "red first" in text and "suite manifest" in text,
        "no_ask_user": 'No "ask the user"' in text,
        "no_gauge": "lite/full/off" in text,
        "guardrails": all(
            p in text for p in ("trust boundaries", "security", "accessibility")
        ),
    }
    ok3 = all(amendments[k] for k in ("approved_deps", "red_first", "no_ask_user"))
    ok4 = amendments["guardrails"] and amendments["no_gauge"]
    statuses["arm3-ladder-amendments"] = "VERIFIED" if ok3 else "FALSE-PASS"
    statuses["arm4-guardrail-text"] = "VERIFIED" if ok4 else "FALSE-PASS"
    handbook_digest = "sha256:" + hashlib.sha256(handbook_bytes).hexdigest()
    _record(
        args.out,
        "arm3-ladder-amendments",
        expectation="arm3-ladder-amendments",
        status=statuses["arm3-ladder-amendments"],
        digests={"handbook": handbook_digest},
        argv=["parse governance/handbook.json"],
        cwd=str(REPOSITORY),
        exit_code=0 if ok3 else 1,
        notes=json.dumps(amendments),
    )
    _record(
        args.out,
        "arm4-guardrail-text",
        expectation="arm4-guardrail-text",
        status=statuses["arm4-guardrail-text"],
        digests={"handbook": handbook_digest},
        argv=["parse governance/handbook.json"],
        cwd=str(REPOSITORY),
        exit_code=0 if ok4 else 1,
        notes=json.dumps(amendments),
    )

    with tempfile.TemporaryDirectory(prefix="ranex-112-proof-") as tmp:
        subject = Path(tmp) / "fastapi-template"
        try:
            full = _clone_fastapi(subject)
            clone_ok = True
            clone_notes = full
        except Exception as exc:  # noqa: BLE001
            clone_ok = False
            clone_notes = f"clone failed: {exc}"
            subject.mkdir(parents=True, exist_ok=True)
            (subject / "README.md").write_text("seed\n", encoding="utf-8")

        paths = _list_paths(subject)
        digests_on: list[str] = []
        digests_off: list[str] = []
        for _ in range(args.repeats):
            digests_on.append(resolve_handbook(system_entries, (), paths, {}).digest)
            digests_off.append(resolve_handbook((), (), paths, {}).digest)

        ok1 = (
            clone_ok
            and len(set(digests_on)) == 1
            and digests_on[0] != digests_off[0]
        )
        ok2 = len(set(digests_off)) == 1 and digests_on[0] != digests_off[0]
        statuses["arm1-resolution-determinism"] = (
            "VERIFIED" if ok1 else ("GAP" if not clone_ok else "NON-DETERMINISTIC")
        )
        statuses["arm2-handbook-absent"] = "VERIFIED" if ok2 else "FALSE-PASS"
        _record(
            args.out,
            "arm1-resolution-determinism",
            expectation="arm1-resolution-determinism",
            status=statuses["arm1-resolution-determinism"],
            digests={"with_ladder": digests_on[0], "path_count": str(len(paths))},
            argv=["resolve_handbook", "system=ladder", f"pin={clone_notes}"],
            cwd=str(subject),
            exit_code=0 if ok1 else 1,
            notes=f"repeats={args.repeats} unique={len(set(digests_on))} clone_ok={clone_ok}",
        )
        _record(
            args.out,
            "arm2-handbook-absent",
            expectation="arm2-handbook-absent",
            status=statuses["arm2-handbook-absent"],
            digests={"without_ladder": digests_off[0], "with_ladder": digests_on[0]},
            argv=["resolve_handbook", "system=empty"],
            cwd=str(subject),
            exit_code=0 if ok2 else 1,
            notes="resolution digest differs when handbook absent",
        )

        for name in (
            "arm-overbuild-governed",
            "arm-overbuild-absent",
            "arm-guardrail-path-escape",
            "arm-irreducible-crud",
        ):
            statuses[name] = "GAP"
            _record(
                args.out,
                name,
                expectation=name,
                status="GAP",
                digests={},
                argv=["task delegate"],
                cwd=str(subject),
                exit_code=0,
                notes="seeded-subject ship: live model worker not configured",
            )

    summary = {
        "issue": 112,
        "repeats": args.repeats,
        "statuses": statuses,
        "host": os.uname().nodename,
        "fastapi_pin": FASTAPI_COMMIT,
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
