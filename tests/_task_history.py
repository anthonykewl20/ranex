"""Explicit retained service history for task publication fixtures."""
import hashlib
from pathlib import Path

from _history import mint_service, register_service

from ranex.foundation.signing import public_key_for
from ranex.governed_execution.adapters.persistence.history import bootstrap_history, record_anchored


def register(repo):
    _, public, path = mint_service(repo.parent)
    register_service(repo / "governance/producers.yaml", public)
    return path

def checkpoint(repo, name="governance/evidence.json"):
    repo = Path(repo).resolve()
    return repo.parent.parent / ("task-history-" + hashlib.sha256(str(repo / Path(name).parent).encode()).hexdigest() + ".json")

def record(repo, records):
    repo = Path(repo).resolve()
    service = repo.parent / "history-service.key"
    if not service.exists():
        service = repo.parent.parent / "history-service.key"
    private = service.read_text().strip()
    public = public_key_for(private)
    anchor = checkpoint(repo)
    if not anchor.exists():
        bootstrap_history(repo / "governance/evidence.json", anchor, private, public, repo)
    for item in records:
        record_anchored(repo / "governance/evidence.json", item, anchor, private, public, repo)

def configure(monkeypatch, repo, argv):
    root = Path(repo)
    if argv[:2] == ["task", "judge"]:
        root = Path(argv[argv.index("--emitted-worktree") + 1])
    elif argv[:2] == ["task", "merge"] and "--evidence" not in argv:
        from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
        task_id = argv[argv.index("--task-id") + 1]
        journal = Path(argv[argv.index("--journal") + 1]) if "--journal" in argv else Path(repo) / "governance/journal.sqlite3"
        dispatches = [x for x in (Journal(journal).entries() if journal.exists() else []) if x.get("type") == "task-dispatch" and x.get("task_id") == task_id]
        if dispatches:
            root = Path(dispatches[-1]["worktree"])
    name = argv[argv.index("--evidence") + 1] if "--evidence" in argv else "governance/evidence.json"
    monkeypatch.setenv("RANEX_HISTORY_CHECKPOINT", str(checkpoint(root, name)))
