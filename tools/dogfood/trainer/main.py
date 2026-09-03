"""Trainer CLI: classify, train, coverage.

  classify   survey the corpus; snapshot it to training/corpus.json
  train      run labelled exercises over exercisable tasks; append one pass
             to the chained ledger; divergences are printed and recorded
  coverage   print the class ledger and which required classes remain untrained
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

from trainer import corpus as corpus_mod
from trainer import ledger, variants

DEFAULT_VULCAN = Path("/home/soultransit/devtony/VulcanBench")


def cmd_classify(args: argparse.Namespace) -> int:
    suites = args.suites.split(",") if args.suites else None
    records = corpus_mod.classify_corpus(Path(args.vulcan_root), suites)
    counts = Counter(r.classification for r in records)
    by_suite: Counter[str] = Counter()
    for r in records:
        by_suite[f"{r.suite}:{r.classification}"] += 1
    snapshot = {
        "schema": "ranex-dogfood-training-corpus-v1",
        "vulcan_root": str(args.vulcan_root),
        "suites": suites or "all",
        "tasks": [r.as_dict() for r in records],
        "counts": dict(sorted(counts.items())),
    }
    ledger.TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    ledger.CORPUS_SNAPSHOT.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(f"corpus: {len(records)} tasks -> {ledger.CORPUS_SNAPSHOT}")
    for kind, n in sorted(counts.items()):
        print(f"  {n:4}  {kind}")
    for key, n in sorted(by_suite.items()):
        print(f"         {key}: {n}")
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    from trainer import preflight

    if not ledger.CORPUS_SNAPSHOT.is_file():
        print("no corpus snapshot; run `classify` first", file=sys.stderr)
        return 2
    print(f"preflighting exercisable tasks against the pinned interpreter "
          f"(probe timeout {preflight.PROBE_TIMEOUT_SECONDS}s) ...")
    result = preflight.run_preflights(ledger.CORPUS_SNAPSHOT,
                                      only_missing=not args.redo)
    print(f"checked {result['checked']}, failed {result['failed']} "
          f"(reasons cached in {ledger.CORPUS_SNAPSHOT})")
    return 0


def _select_tasks(args: argparse.Namespace) -> list[corpus_mod.TaskRecord]:
    snapshot = json.loads(ledger.CORPUS_SNAPSHOT.read_text())
    tasks = []
    for raw in snapshot["tasks"]:
        record = corpus_mod.TaskRecord(
            suite=raw["suite"], task=raw["task"], path=raw["path"],
            language=raw["language"], classification=raw["classification"],
            entries=tuple(corpus_mod.TestEntry(
                e["name"], tuple(e["node_ids"]), e["argv0"], e["grammar"],
                tuple(e.get("env", ())))
                for e in raw["entries"]),
            notes=tuple(raw["notes"]),
        )
        if record.classification != "exercisable":
            continue
        preflight = raw.get("preflight", {})
        if preflight.get("status") != "ok":
            continue
        if args.task and record.id != args.task:
            continue
        if not args.task and args.suites and record.suite not in args.suites.split(","):
            continue
        tasks.append(record)
    return tasks[: args.limit] if args.limit else tasks


def _corpus_stats() -> dict:
    snapshot = json.loads(ledger.CORPUS_SNAPSHOT.read_text())
    stats: dict[str, int] = {}
    preflight_reasons: dict[str, int] = {}
    for raw in snapshot["tasks"]:
        stats[raw["classification"]] = stats.get(raw["classification"], 0) + 1
        status = raw.get("preflight", {}).get("status")
        if status == "failed":
            key = raw["preflight"].get("reason", "?").split("(")[0][:60]
            preflight_reasons[key] = preflight_reasons.get(key, 0) + 1
        elif status == "gold-not-green":
            stats["gold-not-green"] = stats.get("gold-not-green", 0) + 1
        elif status == "ok":
            stats["preflight-ok"] = stats.get("preflight-ok", 0) + 1
    stats["preflight_failure_reasons"] = preflight_reasons  # type: ignore[assignment]
    return stats


def cmd_train(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "oss_bench"))
    from two_arm import pinned_python_has_pytest

    ok, detail = pinned_python_has_pytest()
    if not ok:
        print(f"PREREQUISITE-MISSING: {detail}")
        return 4
    if not ledger.CORPUS_SNAPSHOT.is_file():
        print("no corpus snapshot; run `classify` first", file=sys.stderr)
        return 2

    chosen = _select_tasks(args)
    wanted = [v for v in args.variants.split(",") if v] or list(variants.ALL_VARIANTS)
    unknown = [v for v in wanted if v not in variants.ALL_VARIANTS]
    if unknown:
        print(f"unknown variants: {unknown}; known: {list(variants.ALL_VARIANTS)}",
              file=sys.stderr)
        return 2
    print(f"training {len(chosen)} tasks x {len(wanted)} variants "
          f"(max {args.max_examples} examples), head {ledger.git_head()[:12]}")

    pass_record: dict = {
        "schema": "ranex-dogfood-training-pass-v1",
        "git_head": ledger.git_head(),
        "corpus": _corpus_stats(),
        "requested": {"suites": args.suites, "task": args.task,
                      "variants": wanted, "limit": args.limit},
        "examples": [],
    }
    divergences: list[dict] = []
    written = 0
    for record in chosen:
        task_dir = Path(record.path)
        gold = task_dir / "gold_patch.diff"
        node_ids = sorted({nid for e in record.entries for nid in e.node_ids})
        for variant in wanted:
            if written >= args.max_examples:
                break
            with tempfile.TemporaryDirectory(prefix="ranex-trainer-") as scratch:
                try:
                    example = variants.run_exercise(
                        variant, task_dir, Path(scratch), node_ids,
                        gold if gold.is_file() else None,
                        env_assignments=sorted(
                            {a for e in record.entries for a in e.env}))
                except Exception as exc:  # noqa: BLE001 — a failed build is data
                    example = {"variant": variant, "task": record.id,
                               "expected_gate": "?" if variant != "gold" else "PASS",
                               "actual_gate": "ERROR", "agree": False,
                               "error": f"{type(exc).__name__}: {exc}"[:300]}
            if not example.get("skipped"):
                example["classes"] = variants.classes_for(example)
                if example.get("agree") is False:
                    divergences.append(example)
            pass_record["examples"].append(example)
            written += 1
            mark = ("SKIP" if example.get("skipped")
                    else ("agree" if example.get("agree") else "DIVERGE"))
            extra = example.get("missing_diagnosis") or ""
            print(f"  {mark:<8} {record.id:<44} {variant:<14} {extra}", flush=True)
        # C-03 lesson: persist incrementally, never only at the end.
        pass_record["summary"] = _summary(pass_record["examples"])
        _rewrite_pending(pass_record)
    coverage_path = ledger.write_coverage()
    pass_record["summary"] = _summary(pass_record["examples"])
    pass_path = ledger.write_pass(pass_record)
    (ledger.PASSES_DIR / "pending.json").unlink(missing_ok=True)
    print(f"\nexamples: {written}  divergences: {len(divergences)}")
    print(f"pass -> {pass_path}")
    print(f"coverage -> {coverage_path}")
    uncovered = ledger.uncovered_required_classes()
    if uncovered:
        print(f"required classes still untrained: {uncovered}")
    return 1 if divergences else 0


def _summary(examples: list[dict]) -> dict:
    graded = [e for e in examples if not e.get("skipped")]
    return {
        "examples": len(graded),
        "agree": sum(1 for e in graded if e.get("agree")),
        "diverge": sum(1 for e in graded if e.get("agree") is False),
        "skipped": sum(1 for e in examples if e.get("skipped")),
    }


def _rewrite_pending(pass_record: dict) -> None:
    """Crash-safe in-progress persistence (pending-*.json, adopted on success)."""
    pending = ledger.PASSES_DIR / "pending.json"
    ledger.PASSES_DIR.mkdir(parents=True, exist_ok=True)
    body = dict(pass_record)
    body["summary"] = _summary(pass_record["examples"])
    pending.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")


def cmd_github(args: argparse.Namespace) -> int:
    from trainer import github

    wanted = [v for v in args.variants.split(",") if v] or list(github.GITHUB_VARIANTS)
    pass_record: dict = {
        "schema": "ranex-dogfood-training-pass-v1",
        "git_head": ledger.git_head(),
        "corpus": {"source": "github"},
        "requested": {"url": args.url, "rev": args.rev, "variants": wanted},
        "examples": [],
    }
    try:
        examples = github.train_github(args.url, args.rev, args.max_ids,
                                       wanted, pass_record)
    except Exception as exc:  # noqa: BLE001 — fetch/collect failure is data
        print(f"ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    pass_record["examples"] = examples
    pass_record["summary"] = _summary(examples)
    path = ledger.write_pass(pass_record)
    coverage_path = ledger.write_coverage()
    divergences = [e for e in examples if e.get("agree") is False]
    print(f"\nexamples: {len(examples)}  divergences: {len(divergences)}")
    print(f"pass -> {path}\ncoverage -> {coverage_path}")
    return 1 if divergences else 0


def cmd_coverage(_: argparse.Namespace) -> int:
    coverage = ledger.recompute_coverage()
    print(f"passes={coverage['passes']} examples={coverage['examples']} "
          f"agree={coverage['agree']} diverge={coverage['diverge']} "
          f"tasks={coverage['distinct_tasks']}")
    for cls, n in coverage["classes"].items():
        print(f"  {n:5}  {cls}")
    uncovered = ledger.uncovered_required_classes()
    if uncovered:
        print("\nrequired classes still untrained:")
        for cls in uncovered:
            print(f"         {cls}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trainer", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    classify = sub.add_parser("classify")
    classify.add_argument("--vulcan-root", type=Path, default=DEFAULT_VULCAN)
    classify.add_argument("--suites")
    classify.set_defaults(func=cmd_classify)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--redo", action="store_true",
                           help="re-probe tasks already cached as ok")
    preflight.set_defaults(func=cmd_preflight)

    train = sub.add_parser("train")
    train.add_argument("--vulcan-root", type=Path, default=DEFAULT_VULCAN)
    train.add_argument("--suites")
    train.add_argument("--task", help="single suite/task id")
    train.add_argument("--variants", default="")
    train.add_argument("--limit", type=int, default=0)
    train.add_argument("--max-examples", type=int, default=200)
    train.set_defaults(func=cmd_train)

    github = sub.add_parser("github")
    github.add_argument("--url", required=True,
                        help="e.g. https://github.com/benjaminp/six.git")
    github.add_argument("--rev", default="HEAD")
    github.add_argument("--max-ids", type=int, default=25)
    github.add_argument("--variants", default="")
    github.set_defaults(func=cmd_github)

    coverage = sub.add_parser("coverage")
    coverage.set_defaults(func=cmd_coverage)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
