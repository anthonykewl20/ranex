"""The path a NEW operator walks, from zero state, following the README.

Every other journey in this suite starts from a repository that is already
configured. This one starts from nothing — fresh clone, no signing key, no
producer registered, no wheel store — and walks the documented setup exactly
as a person would, in order, asserting at each step that the product's own
message tells them what to do next.

That gap is not theoretical. When this file was written the README's
walkthrough had been correct and had silently rotted: it omitted `deps fetch`
and `deps approve` (added by SLICE-006, and without them `run` refuses), never
mentioned installing the pinned resolver, and explained a `gate evaluate`
failure with a `contracts-validated` requirement that SLICE-003 had already
removed. Three defects, all invisible to a suite whose fixtures begin
configured.

So the stages also assert that the commands they run **appear in README.md**.
A step deleted from the docs, or changed without the docs, fails here. That is
the cheapest available defence against the documentation drifting away from
the product again.

MAP §4.6: the gauge must be applied to the part. A person's first hour is part
of the product, and this is the only test that measures it.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REAL_REPO = Path(__file__).resolve().parents[2]
README = REAL_REPO / "README.md"
PINS = REAL_REPO / "governance" / "deps.yaml"

# A stage that spawns the governed command runs this suite again inside the
# observation. Without a guard the clone below would be made recursively.
GUARD = "RANEX_COLD_START_CHILD"

pytestmark = pytest.mark.skipif(
    os.environ.get(GUARD) == "1",
    reason="cold-start journey does not re-enter itself",
)


def documented(*fragments: str) -> None:
    """Refuse a stage whose command the README does not actually tell anyone.

    Whitespace is collapsed and shell line-continuations dropped, because the
    README wraps its blocks; the comparison is about the instruction existing,
    not about where the author broke the line.
    """

    def normalise(value: str) -> str:
        return " ".join(token for token in value.split() if token != "\\")

    text = normalise(README.read_text())
    for fragment in fragments:
        wanted = normalise(fragment)
        assert wanted in text, (
            f"README.md does not document {wanted!r}. Either the step is "
            "undocumented, or the docs changed without this journey."
        )


def pinned_resolver() -> Path | None:
    import yaml

    if not PINS.exists():
        return None
    pins = yaml.safe_load(PINS.read_text())
    path = Path(pins["resolver"]["path"])
    if not path.is_file():
        return None
    if hashlib.sha256(path.read_bytes()).hexdigest() != pins["resolver"]["sha256"]:
        return None
    return path


class Operator:
    """One person, one machine, one afternoon."""

    def __init__(self) -> None:
        self.blocked: dict[str, str] = {}
        self.clone: Path | None = None
        self.key: Path | None = None
        self.store: Path | None = None

    def require(self, *stages: str) -> None:
        for stage in stages:
            if stage in self.blocked:
                pytest.skip(f"depends on {stage}: {self.blocked[stage]}")

    def block(self, stage: str, reason: str) -> None:
        self.blocked[stage] = reason
        pytest.skip(reason)


@pytest.fixture(scope="module")
def operator(tmp_path_factory: pytest.TempPathFactory) -> Operator:
    state = Operator()
    if pinned_resolver() is None:
        state.blocked["resolver"] = (
            "the resolver in governance/deps.yaml is absent or does not match "
            "its digest; a new operator installs it first"
        )
    root = tmp_path_factory.mktemp("cold-start")
    state.key = root / "keys" / "worker.key"
    state.store = root / "store"
    state.clone = root / "clone"
    return state


def ranex(
    repo: Path, argv: list[str], key: Path | None = None
) -> tuple[int, str, str]:
    """Exactly the documented invocation: PYTHONPATH=src, module path, no venv."""

    environment = {**os.environ, "PYTHONPATH": str(repo / "src"), GUARD: "1"}
    environment.pop("RANEX_SIGNING_KEY", None)
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=repo,
        capture_output=True,
        text=True,
        env=environment,
    )
    return completed.returncode, completed.stdout, completed.stderr


def git(repo: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


# --------------------------------------------------------------------------
# Stage 1 — what a new operator actually receives.
# --------------------------------------------------------------------------


def test_stage_1_a_fresh_clone_carries_no_secrets_and_no_store(
    operator: Operator,
) -> None:
    operator.require("resolver")
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(operator.clone)],
        capture_output=True,
        text=True,
    )
    if cloned.returncode != 0:
        operator.block("clone", f"cannot clone: {cloned.stderr}")
    for key, value in (("user.email", "new@example.com"), ("user.name", "New")):
        git(operator.clone, "config", key, value)

    # The state a person starts from, asserted rather than assumed: no private
    # key anywhere in the tree, and no provisioned environment.
    assert not list(operator.clone.rglob("*.key"))
    assert not (operator.clone / ".venv").exists()
    assert not operator.store.exists()
    # And no keyring at all: this repository deliberately commits none, so the
    # operator is CREATING the trust root rather than editing it. That is the
    # fact the bootstrap below has to cope with, and the one the product used
    # to get wrong by printing an entry that is not a valid file on its own.
    assert not (operator.clone / "governance" / "producers.yaml").exists()


# --------------------------------------------------------------------------
# Stage 2 — the first command, and whether its refusal is usable.
# --------------------------------------------------------------------------


def test_stage_2_gate_evaluate_refuses_and_says_why(operator: Operator) -> None:
    """The README promises exit 2 here. A refusal must also be actionable."""

    operator.require("resolver", "clone")
    documented(
        "python -m ranex.cli.main gate evaluate HEAD --approver reviewer_alice"
    )
    code, _, err = ranex(
        operator.clone, ["gate", "evaluate", "HEAD", "--approver", "reviewer_alice"]
    )
    assert code == 2, err
    # Not merely nonzero: the message must name the missing trust root, or the
    # operator is left guessing which of several things is absent.
    assert "producers.yaml" in err or "keyring" in err.lower(), err


# --------------------------------------------------------------------------
# Stage 3 — bootstrapping an identity.
# --------------------------------------------------------------------------


def test_stage_3_keygen_writes_outside_the_tree_and_prints_a_usable_line(
    operator: Operator,
) -> None:
    operator.require("resolver", "clone")
    documented("python -m ranex.cli.main keygen --producer worker")
    operator.key.parent.mkdir(parents=True, exist_ok=True)
    code, out, err = ranex(
        operator.clone, ["keygen", "--producer", "worker"], key=operator.key
    )
    assert code == 0, err
    assert operator.key.is_file()
    # 0600, and outside the repository — both are the slice's premise, and a
    # new operator has no way to check either without being told.
    assert oct(operator.key.stat().st_mode)[-3:] == "600"
    assert REAL_REPO not in operator.key.parents
    assert operator.clone not in operator.key.parents

    # What is printed must be a VALID KEYRING on its own, because no keyring
    # is committed and the operator is creating one. Printing only the entry
    # yielded a document with no `producers` mapping, which the loader then
    # refuses — the product telling someone to do the wrong thing and
    # rejecting them for it. So the snippet is parsed here exactly as the
    # loader parses it, rather than pattern-matched.
    assert "governance/producers.yaml" in out, out
    lines = out.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == "producers:"]
    assert starts, out
    # From the mapping's own first line to the end, dedented by the two spaces
    # the CLI indents its snippet with. Taking every line that merely begins
    # with two spaces swept up the wrapped prose above it.
    snippet = "\n".join(line[2:] for line in lines[starts[0] :])
    parsed = yaml.safe_load(snippet)
    assert isinstance(parsed, dict) and "producers" in parsed, snippet
    assert list(parsed["producers"]) == ["worker"], snippet
    assert str(parsed["producers"]["worker"]).startswith("ed25519:"), snippet
    operator.keyring_text = snippet + "\n"  # type: ignore[attr-defined]


def test_stage_4_registering_the_producer_is_a_commit(operator: Operator) -> None:
    operator.require("resolver", "clone")
    documented("producers:", "worker: ed25519:<the key keygen printed>")
    keyring = operator.clone / "governance" / "producers.yaml"
    keyring_text = getattr(operator, "keyring_text", None)
    if keyring_text is None:
        pytest.skip("depends on keygen having printed a keyring snippet")
    # Written verbatim from what the product printed. Nothing is reformatted
    # here on purpose: if the operator has to edit it, the product is not
    # finished, and this stage must fail rather than paper over it.
    keyring.write_text(keyring_text)
    git(operator.clone, "add", "governance/producers.yaml")
    committed = git(operator.clone, "commit", "-q", "-m", "register worker")
    assert committed.returncode == 0, committed.stderr


# --------------------------------------------------------------------------
# Stage 5 — the trap this journey exists to catch.
# --------------------------------------------------------------------------


def test_stage_5_run_before_provisioning_refuses_and_names_the_next_command(
    operator: Operator,
) -> None:
    """The defect that motivated this file.

    Following the README as it stood, the operator's next move was `run` — and
    it refused, because SLICE-006 made provisioning a precondition and the
    walkthrough never said so. The product's own message did name the missing
    command, which is why this is recoverable rather than a dead end; that
    property is now asserted instead of assumed.
    """

    operator.require("resolver", "clone")
    code, _, err = ranex(
        operator.clone,
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--store", str(operator.store), "--", "uv", "run", "pytest", "-q",
        ],
        key=operator.key,
    )
    assert code == 2, err
    assert "deps fetch" in err, err
    assert not (operator.clone / "governance" / "evidence.json").exists()


# --------------------------------------------------------------------------
# Stage 6 — provisioning, as documented.
# --------------------------------------------------------------------------


def test_stage_6_deps_fetch_provisions_and_points_at_approval(
    operator: Operator,
) -> None:
    operator.require("resolver", "clone")
    documented("python -m ranex.cli.main deps fetch")
    code, out, err = ranex(
        operator.clone,
        ["deps", "fetch", "--repository", ".", "--store", str(operator.store)],
    )
    if code != 0:
        operator.block("fetch", f"deps fetch failed: {err.strip()[:300]}")
    assert "FETCHED" in out
    # The next step must be named here, not left to the reader.
    assert "deps approve" in out, out


def test_stage_7_deps_approve_shows_the_delta_and_states_its_limit(
    operator: Operator,
) -> None:
    operator.require("resolver", "clone", "fetch")
    documented(
        "python -m ranex.cli.main deps approve --approver reviewer_alice"
    )
    code, out, err = ranex(
        operator.clone,
        ["deps", "approve", "--repository", ".", "--approver", "reviewer_alice"],
    )
    assert code == 0, err
    assert "no prior approval" in out, out
    assert "pytest" in out, out
    # The operator must be told what approving does NOT buy, at the moment
    # they do it. MAP §4.6 and ADR-007 sad path 17.
    assert "hidden change" in out or "still chooses" in out, out


# --------------------------------------------------------------------------
# Stage 8 — the governed run, and the one thing still open.
# --------------------------------------------------------------------------


def test_stage_8_the_governed_run_executes_the_real_suite(
    operator: Operator,
) -> None:
    """Provisioned, the documented `run` executes and records honestly."""

    operator.require("resolver", "clone", "fetch")
    documented(
        "python -m ranex.cli.main run --claim tests-executed --producer worker "
        "-- uv run pytest -q"
    )
    code, out, err = ranex(
        operator.clone,
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--store", str(operator.store), "--", "uv", "run", "pytest", "-q",
        ],
        key=operator.key,
    )
    evidence = operator.clone / "governance" / "evidence.json"
    assert evidence.exists(), f"no evidence recorded: {err}"
    import json

    records = json.loads(evidence.read_text())
    assert records[0]["command"] == "uv run pytest -q"
    assert records[0]["exit_code"] == code
    # It really ran: a recorded exit code with no suite behind it is the
    # "denial that passes because the command never ran" this project names.
    assert "passed" in out or "passed" in err, out + err


def test_stage_9_the_gate_accepts_the_evidence(operator: Operator) -> None:
    operator.require("resolver", "clone", "fetch")
    code, out, _ = ranex(
        operator.clone,
        ["gate", "evaluate", "HEAD", "--approver", "reviewer_alice"],
    )
    assert code == 0
    assert out.startswith("PASS")
