"""Labelled exercise variants: the trainer's automatically-graded curriculum.

Each variant builds a governed repo from corpus truth, drives it through the
real pipeline, and states — before anything runs — what the gate MUST print.
The label is derived from the task's own contract (gold patch, pristine test
set), never from observing ranex's answer first.

Diagnosis substrings are matched against the gate's own vocabulary
("missing test ID(s)", "different subject digest", ...) because those strings
are part of the kernel's published operator contract (cmd_gate_evaluate).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from trainer import governed

VARIANT_CLASSES = {
    "gold": "verdict/suite-satisfied",
    "empty": "verdict/tests-failing-pre-fix",
    "delete-tests": "verdict/missing-ids-gaming",
    "goalpost-move": "verdict/stale-subject-binding",
    "partial-gold": "verdict/partial-solution-failing",
    "manifest-swap": "verdict/manifest-mismatch-at-evidence-time",
    "manifest-crossbind": "verdict/manifest-mismatch-cross-bind",
}
ALL_VARIANTS = tuple(VARIANT_CLASSES)


def first_hunk_patch(patch: Path, out_dir: Path) -> Path | None:
    """The gold diff restricted to the first file's first hunk.

    None when the patch is single-hunk (partial == whole, no signal).
    BYTE-preserving: the diff is sliced as bytes — CR characters are diff
    CONTENT for CRLF files, and universal-newline decoding would corrupt
    the partial patch so `git apply` fails against the very files the gold
    patch handles fine.
    """
    raw = patch.read_bytes()
    marker = b"diff --git "
    blocks = raw.split(marker)
    if len(blocks) < 2:
        return None
    first = blocks[1]
    at = first.find(b"\n@@")
    if at == -1:
        return None
    header_end = at + 1
    next_hunk = first.find(b"\n@@", header_end)
    if next_hunk == -1:
        return None  # single hunk: withholding it would test the empty patch
    truncated = first[: next_hunk + 1]
    partial = out_dir / "partial-gold.diff"
    payload = blocks[0] + marker + truncated
    if payload == raw:
        return None
    partial.write_bytes(payload)
    return partial


def delete_test_functions(repo: governed.GovernedRepo, node_ids: list[str],
                          how_many: int = 2) -> list[str]:
    """Delete EXACTLY the functions the manifest ids name (not whatever
    test function happens to sit first in the file).

    Victims are chosen from ids of the plain top-level shape `file::name`
    (no class segment, no parametrize brackets) so the deletion provably
    removes manifest-bound tests; class-nested, parametrized and async
    shapes are left alone rather than approximated. Returns the deleted
    names — an empty list means "no deletable shape" and the caller must
    skip, never grade.
    """
    victims: dict[str, list[str]] = {}
    for nid in sorted(set(node_ids)):
        parts = nid.split("::")
        if len(parts) != 2:          # class-nested or deeper: skip the shape
            continue
        name = parts[1]
        if "[" in name or not name.startswith("test"):
            continue                 # parametrized or not a test function
        victims.setdefault(parts[0], []).append(name)
    chosen: dict[str, list[str]] = {}
    total = 0
    for filename, names in sorted(victims.items()):
        take = min(len(names), how_many - total)
        if take <= 0:
            break
        chosen[filename] = names[:take]
        total += take
    if total == 0:
        return []
    removed: list[str] = []
    for filename, names in chosen.items():
        victim = repo.root / filename
        if not victim.is_file():
            continue
        tree = ast.parse(victim.read_text())
        wanted = set(names)
        kept: list[ast.stmt] = []
        dropped: list[str] = []
        for node in tree.body:
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name in wanted):
                dropped.append(node.name)
                continue
            kept.append(node)
        if dropped:
            tree.body = kept
            victim.write_text(ast.unparse(tree) + "\n")
            removed.extend(dropped)
    return removed


def run_exercise(variant: str, task_dir: Path, out: Path,
                 node_ids: list[str], gold_patch: Path | None,
                 env_assignments: list[str] | None = None) -> dict[str, Any]:
    """Build the governed repo for `variant`, drive the cycle, grade it."""
    alt_suite = sorted(set(node_ids))[1:] if variant == "manifest-crossbind" else None
    if variant == "manifest-crossbind" and not alt_suite:
        return _skipped(variant, task_dir, "single test id; cross-bind needs two")
    repo = governed.GovernedRepo(
        task_dir, out, node_ids, alt_manifest_suite=alt_suite,
        env_extra=governed.env_extra_for(env_assignments or []))
    removed: list[str] = []
    expect_contains: tuple[str, ...] = ()

    if variant == "gold":
        repo.apply_patch(gold_patch, "gold solution")
    elif variant == "empty":
        pass
    elif variant == "delete-tests":
        repo.apply_patch(gold_patch, "gold solution")
        removed = delete_test_functions(repo, node_ids)
        if not removed:
            return _skipped(variant, task_dir,
                            "no plain top-level test functions in the "
                            "manifest ids (class-nested/parametrized only)")
        repo.commit_working_tree("agent solution (tests 'cleaned up')")
        expect_contains = ("missing test ID(s):",)
    elif variant == "goalpost-move":
        # Evidence is recorded against subject S1, then the tree moves: the
        # same signed proof must go stale against the new subject.
        repo.apply_patch(gold_patch, "gold solution")
        run = repo.run_claim()
        (repo.root / "TASK.md").write_text("the ground moved under the evidence\n")
        repo.commit_working_tree("post-evidence commit moves the subject")
        gate = repo.evaluate()
        journal = repo.verify_journal()
        return _result(variant, task_dir, "FAIL", ("different subject digest",),
                       run, gate, journal, extra={"moved_by": "post-evidence commit"})
    elif variant == "partial-gold":
        if gold_patch is None:
            return _skipped(variant, task_dir, "no gold patch")
        partial = first_hunk_patch(gold_patch, out)
        if partial is None:
            return _skipped(variant, task_dir, "gold patch is single-hunk")
        repo.apply_patch(partial, "partial solution")
    elif variant == "manifest-swap":
        # Goalpost move at EVIDENCE time: a fresh, correctly signed run whose
        # suite results were summarised against an uncommitted tampered
        # manifest. Subject binding cannot catch this (the evidence is fresh);
        # the claim's committed manifest binding must.
        repo.apply_patch(gold_patch, "gold solution")
        tampered = {"suite": sorted(set(node_ids))[1:] or sorted(set(node_ids)),
                    "expected_skips": {}}
        tampered_path = repo.root / "governance" / "tampered-manifest.json"
        tampered_path.write_bytes(
            json.dumps(tampered, sort_keys=True, separators=(",", ":")).encode())
        run = repo.run_claim("--suite-manifest",
                             "governance/tampered-manifest.json")
        gate = repo.evaluate()
        journal = repo.verify_journal()
        # Verified contract: an UNCOMMITTED governance input is refused at run
        # time ("A file no commit carries is a file review never saw"), so the
        # tampered summary never becomes evidence and the gate fails as
        # absence. Defense in depth — the mismatch never reaches a diagnosis.
        return _result(variant, task_dir, "FAIL", (),
                       run, gate, journal,
                       expect_run_contains=("carries no suite manifest",),
                       extra={"tampered_suite": tampered["suite"],
                              "refused_at": "run"})
    elif variant == "manifest-crossbind":
        # Both manifests are COMMITTED (review saw both), so the run-time
        # refusal for uncommitted governance cannot fire. Evidence is fresh
        # and addressed — but it was summarised against the alt manifest
        # while the claim binds the pristine one: the mismatch must surface
        # as a gate diagnosis, not a pass.
        repo.apply_patch(gold_patch, "gold solution")
        run = repo.run_claim("--suite-manifest", "governance/alt-manifest.json")
        gate = repo.evaluate()
        journal = repo.verify_journal()
        return _result(variant, task_dir, "FAIL", ("manifest digest did not match",),
                       run, gate, journal, extra={"alt_suite": alt_suite})
    else:
        raise ValueError(f"unknown variant {variant!r}")

    run = repo.run_claim()
    gate = repo.evaluate()
    journal = repo.verify_journal()
    expected_gate = "PASS" if variant == "gold" else "FAIL"
    extra = {"removed_tests": removed} if removed else {}
    result = _result(variant, task_dir, expected_gate, expect_contains,
                     run, gate, journal, extra=extra)
    if variant == "partial-gold" and result["actual_gate"] == "PASS":
        # The withheld hunks may simply not affect the contracted tests.
        # Bare arbitration: run the IDENTICAL command without ranex. Bare
        # green -> the gate is right and the label was wrong (skip, no
        # signal). Bare red -> the gate passed work that fails outside it —
        # the loudest divergence the trainer can produce.
        import os
        import subprocess as _sp

        env = dict(os.environ)
        env.update(repo.env_extra)
        bare = _sp.run(repo.junit_argv, cwd=str(repo.root), env=env,
                       capture_output=True, text=True, check=False, timeout=600)
        if bare.returncode == 0:
            result.update({"skipped": "partial patch is genuinely green "
                                      "(withheld hunks do not affect the tests)",
                           "agree": None, "bare_arbitration": "green"})
        else:
            result["bare_arbitration"] = "RED — gate passed work that fails bare"
    return result


def _skipped(variant: str, task_dir: Path, why: str) -> dict[str, Any]:
    return {"variant": variant, "task": task_dir.parent.name + "/" + task_dir.name,
            "skipped": why, "agree": None}


def _result(variant: str, task_dir: Path, expected_gate: str,
            expect_contains: tuple[str, ...], run: dict, gate: dict,
            journal: dict, extra: dict | None = None,
            expect_run_contains: tuple[str, ...] = ()) -> dict[str, Any]:
    actual = governed.verdict_of(gate)
    output = gate["stdout"] + "\n" + gate["stderr"]
    missing_substrings = [s for s in expect_contains if s not in output]
    missing_run = [s for s in expect_run_contains
                   if s not in (run["stdout"] + "\n" + run["stderr"])]
    record: dict[str, Any] = {
        "variant": variant,
        "task": task_dir.parent.name + "/" + task_dir.name,
        "expected_gate": expected_gate,
        "actual_gate": actual,
        "gate_exit": gate["exit"],
        "journal_verified": governed.journal_ok(journal),
        "agree": (
            actual == expected_gate
            and not missing_substrings
            and not missing_run
            and governed.journal_ok(journal)
        ),
        "run_exit": run["exit"],
        "run_error": run["stderr"][-250:] if run["exit"] != 0 else "",
        "gate_output": output.strip()[:1200],
    }
    if missing_substrings:
        record["missing_diagnosis"] = missing_substrings
    if missing_run:
        record["missing_run_refusal"] = missing_run
    if extra:
        record.update(extra)
    return record


def classes_for(record: dict[str, Any]) -> list[str]:
    """Input-space classes one exercise trained (audit taxonomy codes)."""
    classes = [VARIANT_CLASSES.get(record["variant"], record["variant"])]
    gate = record.get("gate_output", "")
    for marker, code in (
        ("missing test ID(s)", "diagnosis/missing-ids"),
        ("different subject digest", "diagnosis/stale-subject"),
        ("blocking suite outcome", "diagnosis/non-passed-tests"),
        ("manifest digest did not match", "diagnosis/manifest-mismatch"),
        ("no evidence for required claim", "diagnosis/absent-evidence"),
        ("contradictory evidence", "diagnosis/contradiction"),
        ("carries no suite manifest", "defense/uncommitted-governance-refused"),
    ):
        if marker in gate:
            classes.append(code)
    if record.get("run_exit") not in (0, None) and record.get("agree") is False:
        classes.append("sad-path/claim-run-nonzero")
    return classes
