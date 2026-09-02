"""Advanced-math proofs, mapped HONESTLY onto what ranex actually is.

Ranex is a governance kernel: hashing, signing, journals, lockfiles, canonical
JSON. There are no gradients or matrices here, and none of these proofs
pretend otherwise. The applicable advanced methods are:

  graph theory   -> the uv.lock dependency graph must be a DAG, and the
                    kernel's wheel selection must stay inside the independent
                    reachable-closure over-approximation;
  numerical
  analysis       -> floats never publish, integers are bounded by the exact
                    TypeScript-safe 2^53 - 1 boundary, and NaN/Inf are refused
                    by canonical JSON (non-deterministic bytes never enter a
                    digest);
  stability      -> the journal is deliberately unstable: one edited byte
                    diverges every later link (avalanche as a feature);
  asymptotics    -> append-only proven at the BYTE level: appending row N
                    never rewrites rows 1..N-1 (structural O(1) append), and
                    gate evaluation is invariant under evidence permutation.

Every fact returned is byte-deterministic (no timings — timing benchmarks
live in `dogfood.py bench` precisely because they are NOT deterministic).
"""

from __future__ import annotations

import itertools
import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from ranex.foundation.canonical import canonical_json
from ranex.foundation.publication_validation import validate_publication_value
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    evaluate,
)
from ranex.provisioning.lockfile import Lock, parse_lock, select_wheels
from ranex.provisioning.target import probe_target

REPO_ROOT = Path(__file__).resolve().parents[2]
SAFE = 2**53 - 1


def _load_real_lock(ctx) -> Lock:
    return parse_lock((REPO_ROOT / "uv.lock").read_bytes())


def _unmarked_graph(lock: Lock) -> dict[str, set[str]]:
    """Name -> dependency-name edges, ignoring markers: a SUPERSET of the true
    reachability graph, so any conclusion drawn over it is conservative."""
    graph: dict[str, set[str]] = {}
    for package in lock.packages:
        edges = {dep.name for dep in package.dependencies}
        for group in package.dev_dependencies.values():
            edges.update(dep.name for dep in group)
        graph.setdefault(package.name, set()).update(edges)
    return graph


def lock_graph_is_dag(ctx) -> dict[str, Any]:
    """Kahn's algorithm over the REAL committed uv.lock: the dependency graph
    must be acyclic — a cycle would make wheel selection non-terminating."""
    lock = _load_real_lock(ctx)
    graph = _unmarked_graph(lock)
    known = set(graph)
    indegree = {name: 0 for name in known}
    for name, deps in graph.items():
        for dep in deps:
            if dep in known:
                indegree[dep] += 1
    queue = sorted(name for name, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for dep in sorted(graph[node]):
            if dep in indegree:
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    queue.append(dep)
    edges = sum(len(deps & known) for deps in graph.values())
    assert len(order) == len(known), (
        f"uv.lock dependency graph has a cycle outside topological order: "
        f"{sorted(set(known) - set(order))}"
    )
    return {"packages": len(known), "edges": edges, "topological_order_len": len(order)}


def lock_selection_closure(ctx) -> dict[str, Any]:
    """select_wheels over the REAL lock and pinned interpreter: deterministic
    on repeat, duplicate-free, every selected package reachable from the root
    in the conservative unmarked graph, and every wheel sha256-pinned with a
    registry URL."""
    lock = _load_real_lock(ctx)
    pins = yaml.safe_load((REPO_ROOT / "governance" / "deps.yaml").read_text())
    target = probe_target(Path(pins["python"]["path"]))
    first = select_wheels(lock, "ranex", target)
    second = select_wheels(lock, "ranex", target)
    assert first == second, "select_wheels is not deterministic on repeat"

    graph = _unmarked_graph(lock)
    reachable: set[str] = set()
    work = list(graph.get("ranex", set()))
    while work:
        node = work.pop()
        if node in reachable:
            continue
        reachable.add(node)
        work.extend(graph.get(node, ()))

    keys = [(wheel.package, wheel.version) for wheel in first]
    assert len(set(keys)) == len(keys), "duplicate wheels selected"
    for wheel in first:
        assert wheel.package in reachable, (
            f"selected wheel {wheel.package!r} is not reachable from the root"
        )
        assert len(wheel.sha256) == 64 and wheel.url.startswith("https://"), (
            f"wheel {wheel.filename!r} is not sha256-pinned registry URL"
        )
    return {"selected_wheels": len(first), "reachable_unmarked": len(reachable)}


def publication_value_boundaries(ctx) -> dict[str, Any]:
    """Exact numeric boundaries of the publication validator: 2^53 - 1 in,
    2^53 out, floats always out, booleans exempt, non-BMP Unicode out."""
    accepted = [-(SAFE), -1, 0, 1, SAFE, True, False, "café"]
    refused = [SAFE + 1, -(SAFE + 1), 2**53, 0.5, -0.0, float(SAFE), "𝕏"]
    for value in accepted:
        validate_publication_value(value)  # must not raise
    for value in refused:
        try:
            validate_publication_value(value)
        except ValueError:
            continue
        raise AssertionError(f"publication validator accepted {value!r}")
    return {"accepted_boundary": SAFE, "refused_first_int": SAFE + 1,
            "floats_refused": True, "non_bmp_refused": True}


def canonical_json_refuses_indeterminates(ctx) -> dict[str, Any]:
    """NaN and Infinity can serialise differently across platforms; the kernel
    refuses them, so non-deterministic bytes can never enter a digest."""
    for value in [float("nan"), float("inf"), float("-inf")]:
        try:
            canonical_json({"x": value})
        except ValueError:
            continue
        raise AssertionError(f"canonical_json accepted non-finite {value!r}")
    return {"nan_refused": True, "inf_refused": True}


def journal_append_is_nondestructive(ctx) -> dict[str, Any]:
    """Structural O(1) append, proven in bytes: after appending rows k+1..N,
    rows 1..k keep byte-identical records AND links."""
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
    from scenarios import _evaluation

    path = ctx.scratch / "nondestructive.sqlite3"
    journal = Journal(path)
    for _ in range(3):
        journal.append(_evaluation())

    def snapshot() -> list[tuple[int, str, str]]:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT seq, record, link FROM evaluations ORDER BY seq ASC"
        ).fetchall()
        conn.close()
        return [(row["seq"], row["record"], row["link"]) for row in rows]

    before = snapshot()
    for _ in range(2):
        journal.append(_evaluation())
    after = snapshot()
    assert after[:3] == before, "appending rewrote prior journal rows"
    assert len(after) == 5
    return {"prefix_rows_unchanged": 3, "total_rows": 5}


def evidence_permutation_invariance(ctx) -> dict[str, Any]:
    """Gate evaluation must not depend on the order records arrive in: all
    permutations of the same evidence yield byte-identical canonical records
    (the kernel canonicalises internally — `considered` is sorted)."""
    digest = "sha256:" + "c" * 64
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    subject = "sha256:" + "a" * 64

    def ev(producer: str, exit_code: int) -> Evidence:
        return Evidence(claim_id="tests-executed", subject_digest=subject,
                        producer_id=producer, command="pytest -q",
                        command_digest=digest, executable_path="/usr/bin/pytest",
                        exit_code=exit_code)

    records = (ev("alice", 0), ev("bob", 0), ev("carol", 1))
    serialised = set()
    for permutation in itertools.permutations(records):
        result = evaluate(gate, permutation, subject_digest=subject,
                          approver_id="dana")
        serialised.add(canonical_json(result.as_record()))
    assert len(serialised) == 1, (
        f"evaluation depended on evidence order: {len(serialised)} distinct records"
    )
    return {"permutations": 6, "distinct_records": len(serialised)}
