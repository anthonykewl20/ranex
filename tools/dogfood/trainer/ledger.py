"""Training ledger: append-only passes, chained by digest, plus derived coverage.

A pass record is canonical JSON (sorted, compact-normalised on write) with no
clocks and no randomness, so re-running the trainer over the same corpus and
kernel must reproduce byte-identical agreement bits — anything else is drift
and a finding. Each pass carries the sha256 of the previous pass's canonical
record (digest excludes the chaining fields), so silent history edits break
the chain the same way the journal's links do.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from trainer.corpus import canonical_bytes

TRAINING_DIR = Path(__file__).resolve().parents[1] / "training"
PASSES_DIR = TRAINING_DIR / "passes"
CORPUS_SNAPSHOT = TRAINING_DIR / "corpus.json"
COVERAGE = TRAINING_DIR / "coverage.json"

_CHAIN_FIELDS = ("pass_digest", "prev_pass_digest")


def _digest_of(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k not in _CHAIN_FIELDS}
    return "sha256:" + hashlib.sha256(canonical_bytes(body)).hexdigest()


def git_head() -> str:
    repo = Path(__file__).resolve().parents[3]
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def load_passes() -> list[dict[str, Any]]:
    if not PASSES_DIR.is_dir():
        return []
    passes = []
    for path in sorted(PASSES_DIR.glob("pass-*.json")):
        record = json.loads(path.read_text())
        expected = _digest_of(record)
        if record.get("pass_digest") != expected:
            raise ValueError(f"training pass {path.name} fails its self-digest")
        passes.append(record)
    for previous, current in zip(passes, passes[1:]):
        if current.get("prev_pass_digest") != previous["pass_digest"]:
            raise ValueError(
                f"training pass chain broken at pass {current.get('pass')}")
    return passes


def write_pass(pass_record: dict[str, Any]) -> Path:
    PASSES_DIR.mkdir(parents=True, exist_ok=True)
    previous = load_passes()
    number = len(previous) + 1
    pass_record["pass"] = number
    pass_record["prev_pass_digest"] = previous[-1]["pass_digest"] if previous else None
    pass_record["pass_digest"] = _digest_of(pass_record)
    path = PASSES_DIR / f"pass-{number:03d}.json"
    # Exclusive create: two concurrent runs must never silently overwrite
    # the same pass number (both chains would stay "valid" while one pass
    # is lost). Atomic replace so a crash never leaves truncated JSON that
    # bricks load_passes().
    import os
    import tempfile

    fd, tmp_name = tempfile.mkstemp(dir=PASSES_DIR, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(json.dumps(pass_record, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp_name, path)      # fails with FileExistsError on collision
        except FileExistsError:
            raise ValueError(
                f"training pass {path.name} already exists — another trainer "
                "run is writing concurrently; re-run after it finishes")
        finally:
            os.unlink(tmp_name)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return path


def recompute_coverage() -> dict[str, Any]:
    """Aggregate class counts over every recorded pass (derived, idempotent)."""
    classes: dict[str, int] = {}
    tasks: set[str] = set()
    examples = agrees = diverges = skipped = 0
    for record in load_passes():
        for example in record["examples"]:
            if example.get("skipped"):
                skipped += 1
                continue
            examples += 1
            tasks.add(example["task"])
            if example["agree"]:
                agrees += 1
            else:
                diverges += 1
            for cls in example.get("classes", []):
                classes[cls] = classes.get(cls, 0) + 1
    return {
        "schema": "ranex-dogfood-training-coverage-v1",
        "passes": len(load_passes()),
        "examples": examples, "agree": agrees, "diverge": diverges,
        "skipped": skipped, "distinct_tasks": len(tasks),
        "classes": dict(sorted(classes.items())),
    }


def write_coverage() -> Path:
    coverage = recompute_coverage()
    COVERAGE.write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    return COVERAGE


def uncovered_required_classes() -> list[str]:
    """Classes the audit named as blind spots; the trainer exists to close them."""
    required = [
        "verdict/suite-satisfied",
        "verdict/tests-failing-pre-fix",
        "verdict/missing-ids-gaming",
        "verdict/stale-subject-binding",
        "verdict/partial-solution-failing",
        "diagnosis/missing-ids",
        "diagnosis/stale-subject",
        "diagnosis/non-passed-tests",
        "diagnosis/manifest-mismatch",
    ]
    coverage = recompute_coverage()
    seen = coverage["classes"]
    return [cls for cls in required if seen.get(cls, 0) == 0]
