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

import copy
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from ranex.cli.main import record_evidence, subject_digest_for
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import sign_evidence
from ranex.governed_execution.domain import admission

REAL_REPO = Path(__file__).resolve().parents[2]
README = REAL_REPO / "README.md"
PINS = REAL_REPO / "governance" / "deps.yaml"

# A stage that spawns the governed command runs this suite again inside the
# observation. Without a guard the clone below would be made recursively.
GUARD = "RANEX_COLD_START_CHILD"


def _inside_materialised_sample() -> bool:
    """Is this suite running inside an ADR-009 sample rather than a checkout?

    The environment guard below cannot make this call: the observed command's
    environment is built from empty, so no variable survives into the sample.
    What does survive is the sample's own construction — exactly one synthetic
    commit with the fixed identity ADR-009 specifies — and that identity is
    deterministic on purpose, so it is checkable here. Stages 1 and 2 would
    otherwise re-enter against a clone whose HEAD is the outer journey's work
    (a committed keyring), a subject this journey makes claims about but did
    not start from.
    """

    result = subprocess.run(
        ["git", "-C", str(REAL_REPO), "log", "-1", "--format=%ae"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "subject@ranex.invalid"


pytestmark = [
    pytest.mark.skipif(
        os.environ.get(GUARD) == "1",
        reason="cold-start journey does not re-enter itself",
    ),
    pytest.mark.skipif(
        _inside_materialised_sample(),
        reason=(
            "cold-start journey does not re-enter a materialised sample: its "
            "history is one synthetic commit (ADR-009), not the zero state "
            "this journey is about"
        ),
    ),
]


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
    """Sanctioned spine edit (SLICE-055 M8 dedupe): the verdict is the frame
    probe's (tests/e2e/_prereqs.py); the path is re-derived from the same
    committed pins the probe just verified."""

    import yaml

    e2e_dir = str(Path(__file__).resolve().parent)
    if e2e_dir not in sys.path:
        sys.path.insert(0, e2e_dir)
    import _prereqs

    ok, _reason = _prereqs.pinned_resolver()
    if not ok:
        return None
    pins = yaml.safe_load(PINS.read_text())
    return Path(pins["resolver"]["path"])


class Operator:
    """One person, one machine, one afternoon.

    A stage is either **reached** (it ran and produced what its dependents
    consume), **blocked** (a precondition this machine cannot supply was found
    absent and named), or neither — it never ran. `require()` used to consult
    only `blocked`, so the third case passed the guard and the dependent stage
    then ran `git`/`ranex` against a clone directory that was never created,
    dying with a bare `FileNotFoundError` on a temporary path that named
    neither the stage nor the reason. A never-run stage now FAILS its
    dependents loudly. Deliberately not a skip: absence blocks here, and
    demoting a missing artifact to a skip would be a silent pass-by-absence.
    """

    def __init__(self) -> None:
        self.blocked: dict[str, str] = {}
        self.reached: set[str] = set()
        self.clone: Path | None = None
        self.key: Path | None = None
        self.store: Path | None = None

    def reach(self, stage: str) -> None:
        """Record that `stage` produced the artifact its dependents need."""

        self.reached.add(stage)

    def require(self, *stages: str) -> None:
        for stage in stages:
            if stage in self.blocked:
                pytest.skip(f"depends on {stage}: {self.blocked[stage]}")
            if stage not in self.reached:
                pytest.fail(
                    f"required stage {stage!r} never ran, so the artifact this "
                    "test consumes was never produced. Nothing declared its "
                    "preconditions absent either, so this is not a skip.\n"
                    "This journey is ordered and shares one module-scoped "
                    f"operator: {stage!r} must execute in this same process "
                    "first. Selecting a single test ID from this file is the "
                    "usual cause — run the whole file instead. An earlier "
                    "stage erroring out part-way is the other.\n"
                    f"  reached: {sorted(self.reached) or ['(none)']}\n"
                    f"  declared absent: {sorted(self.blocked) or ['(none)']}",
                    pytrace=False,
                )

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
    else:
        state.reach("resolver")
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
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def git(repo: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def qualification_report(host_state: dict[str, object]) -> dict[str, object]:
    open_objects = {
        name: {
            "path": path,
            "realpath": path,
            "sha256": "sha256:" + digit * 64,
            "device": 1,
            "inode": inode,
            "uid": 0,
            "gid": 0,
            "mode": 0o755,
            "mount_id": 1,
            "security_capability": False,
            "filesystem": {
                "device": "0:1",
                "filesystem": "ext4",
                "mount_id": 1,
                "mount_point": "/",
                "options": ["rw"],
                "source": "/dev/root",
            },
        }
        for name, path, digit, inode in (
            ("bubblewrap", "/usr/bin/bwrap", "4", 2),
            ("launcher", "/opt/ranex/ranex-worker-launcher", "3", 3),
        )
    }
    return {
        "schema": "ranex-strict-local-qualification-v1",
        "qualified": True,
        "refusal": None,
        "kernel": {"release": "6.12.0", "architecture": "x86_64"},
        "primitives": {
            "landlock": {"available": True, "abi": 6},
            "seccomp_filter": True,
            "no_new_privs": True,
            "namespaces": {
                "user": True, "mount": True, "pid": True, "ipc": True, "network": True,
            },
            "openat2": True,
        },
        "cgroup": {
            "cgroup_kill": True,
            "mount": {"path": "/sys/fs/cgroup", "filesystem": "cgroup2"},
            "root": "/sys/fs/cgroup",
            "relative_path": "/session.scope",
            "controllers": ["cpu", "memory", "pids"],
            "probe_transcript": {"created": True},
        },
        "open_objects": open_objects,
        "digests": {
            "profile": "sha256:" + "1" * 64,
            "build_manifest": "sha256:" + "2" * 64,
            "artifact": "sha256:" + "3" * 64,
        },
        "delegation": {"broker": None, "existing_root": None, "source": "direct"},
        "host_state": host_state,
    }


def record_live_host_qualification(repo: Path, key_path: Path) -> None:
    argv = (
        "python",
        "-m",
        "ranex.cli.host_confinement",
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report=.local/ranex/qualification/strict-local-v1.json",
    )
    host_state = copy.deepcopy(admission._read_live_durable_host_state())
    host_state["delegation_identity"].update(
        {
            "cgroup_root": "/sys/fs/cgroup",
            "cgroup_relative_path": "/session.scope",
            "source": "direct",
            "userns_state_source": "qualification-host-probe",
        }
    )
    report = qualification_report(host_state)
    content = {
        "claim_id": "host-qualification",
        "command": " ".join(argv),
        "command_digest": command_digest(argv),
        "executable_path": sys.executable,
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": subject_digest_for(repo, "HEAD"),
        "suite_results": report,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    private_key = key_path.read_text(encoding="utf-8").strip()
    record_evidence(
        repo / "governance" / "evidence.json",
        {**content, "signature": sign_evidence(content, private_key)},
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
        check=False,
    )
    if cloned.returncode != 0:
        operator.block("clone", f"cannot clone: {cloned.stderr}")
    operator.reach("clone")
    for key, value in (("user.email", "new@example.com"), ("user.name", "New")):
        git(operator.clone, "config", key, value)

    # The state a person starts from, asserted rather than assumed: no private
    # key anywhere in the tree, and no provisioned environment.
    assert not list(operator.clone.rglob("*.key"))
    assert not (operator.clone / ".venv").exists()
    assert not operator.store.exists()
    # The keyring IS committed: it is the trust root (ADR-002), and it ships
    # because the repository's own operator registered for the self-gate
    # (SLICE-006 stage 12). Zero state is the OPERATOR's — no private key, no
    # store — not the repository's. What must hold is that only public halves
    # are in the tree; the private keys those entries verify live outside it.
    keyring = yaml.safe_load(
        (operator.clone / "governance" / "producers.yaml").read_text(encoding="utf-8")
    )
    assert keyring["producers"], keyring
    assert all(
        str(value).startswith("ed25519:") for value in keyring["producers"].values()
    ), keyring


# --------------------------------------------------------------------------
# Stage 2 — the first command, and whether its refusal is usable.
# --------------------------------------------------------------------------


def test_stage_2_gate_evaluate_fails_closed_and_names_the_missing_claim(
    operator: Operator,
) -> None:
    """Absence blocks: with the keyring committed, the first evaluate reaches
    the kernel and the verdict is an honest FAIL for missing evidence — not a
    configuration error. A failure must also be actionable."""

    operator.require("resolver", "clone")
    documented(
        "python -m ranex.cli.main gate evaluate HEAD --approver reviewer_alice"
    )
    code, out, err = ranex(
        operator.clone, ["gate", "evaluate", "HEAD", "--approver", "reviewer_alice"]
    )
    assert code == 1, err
    assert out.startswith("FAIL"), out
    # Not merely nonzero: the verdict must name the missing claim, or the
    # operator is left guessing what evidence they are expected to produce.
    assert "tests-executed" in out, out
    assert "no evidence" in out, out


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
            "--junitxml=governance/suite_results.xml",
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
    operator.reach("fetch")
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
            "--junitxml=governance/suite_results.xml",
        ],
        key=operator.key,
    )
    evidence = operator.clone / "governance" / "evidence.json"
    assert evidence.exists(), f"no evidence recorded: {err}"
    # Recorded, whichever way the suite went — stage 9 judges it, this stage
    # only proves it exists and is honest about the exit code.
    operator.reach("evidence")
    import json

    records = json.loads(evidence.read_text())
    assert records[0]["command"] == (
        "uv run pytest -q --junitxml=governance/suite_results.xml"
    )
    assert records[0]["exit_code"] == code
    # It really ran: a recorded exit code with no suite behind it is the
    # "denial that passes because the command never ran" this project names.
    assert "passed" in out or "passed" in err, out + err


def test_stage_9_the_gate_accepts_the_evidence(operator: Operator) -> None:
    operator.require("resolver", "clone", "fetch", "evidence")
    record_live_host_qualification(operator.clone, operator.key)
    code, out, err = ranex(
        operator.clone,
        ["gate", "evaluate", "HEAD", "--approver", "reviewer_alice"],
    )
    assert code == 0, (
        "the gate did not accept the evidence stage 8 recorded; it exited "
        f"{code}. The verdict, verbatim:\n{(out + err).strip() or '(no output)'}"
    )
    assert out.startswith("PASS"), out
