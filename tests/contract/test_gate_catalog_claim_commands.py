"""SLICE-003 — the catalog says what a claim means, or it is refused.

Written before the implementation and required to fail first.

`required_claims` was a list of bare strings, coerced with `str(claim)`, so there
was nowhere to declare what satisfying a claim requires. The entries become
mappings:

    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]

**Absence blocks, at construction.** A required claim with no `command` is a
claim whose satisfaction is undefined, and an undefined claim cannot block. The
loader raises; it does not default, and it does not accept the old shape.

Done criteria 3, 4 and 10 of docs/slices/SLICE-003-claim-command-binding.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate

REPO_ROOT = Path(__file__).resolve().parents[2]

BOUND_ARGV = ["uv", "run", "pytest", "-q"]

GOOD = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""

# The shape this slice replaces. Kept verbatim so the refusal is tested against
# the exact text every existing catalog carries.
BARE_STRING = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims: [tests-executed]
"""

NO_COMMAND = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
"""

# Trivially true against any tree. A claim bound to one of these is a claim that
# blocks nothing, whatever its name promises.
#
# Matched on the *basename* of argv[0], because the set below is a denylist and a
# denylist that also has to guess the spelling is two guesses. `("true",)` alone
# left `/bin/true` and `/usr/bin/true` passing this check — reproduced by an
# audit against a copy of this catalog, and the whole defect the slice exists to
# close was green. Normalising the path is what makes one entry cover every way
# of naming one program.
#
# Say plainly what this is: a tripwire, not a proof. No predicate decides whether
# a command substantiates a claim — `sh -c 'exit $((0))'` walks past this and so
# does a script that reads the answer out of a file. It catches the placeholder a
# hurried session reaches for, which is the failure that actually happened here,
# and it must never be read as establishing that the bound commands are
# substantive. That judgement is review's, and this check does not replace it.
TRIVIAL_COMMANDS = {("true",), (":",), ("sh", "-c", "exit 0"), ("sh", "-c", ":")}


def normalised(argv: tuple[str, ...]) -> tuple[str, ...]:
    """`argv` with argv[0] reduced to its basename. `/bin/true` is `true`."""

    return () if not argv else (Path(argv[0]).name, *argv[1:])


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- the new shape loads ----------------------------------------------------


def test_a_claim_mapping_carries_the_command_that_satisfies_it(tmp_path: Path) -> None:
    gate = load_gate(write(tmp_path, GOOD), "landing")

    (claim,) = gate.required_claims
    assert claim.claim_id == "tests-executed"
    assert tuple(claim.command) == tuple(BOUND_ARGV), (
        "argv must survive the load as a sequence of strings; joining it into a "
        "string would put shell parsing back in the comparison"
    )


# --- criterion 3: the old shape is refused, and the message says what to do --


def test_a_bare_string_claim_is_refused_and_the_message_names_the_shape(
    tmp_path: Path,
) -> None:
    """The old catalog must not load silently. A bare string is a claim whose
    satisfaction is undefined, and the loader is the only place that can say so
    before a verdict depends on it."""

    with pytest.raises(ValueError) as raised:
        load_gate(write(tmp_path, BARE_STRING), "landing")

    message = str(raised.value)
    assert "tests-executed" in message, message
    # Naming the migration, not just the failure: an operator reading this has
    # to be able to fix the file without reading the loader.
    assert "claim_id" in message, message
    assert "command" in message, message


# --- criterion 4: a mapping without a command is refused --------------------


def test_a_claim_mapping_without_a_command_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="command"):
        load_gate(write(tmp_path, NO_COMMAND), "landing")


@pytest.mark.parametrize(
    "command",
    ['command: "uv run pytest -q"', "command: []", "command: [1, 2]", "command: null"],
)
def test_a_command_that_is_not_a_non_empty_argv_list_is_refused(
    tmp_path: Path,
    command: str,
) -> None:
    """A string would need shell parsing; an empty list binds nothing; a list of
    non-strings is not an argv. None of the three may become a default."""

    text = GOOD.replace('command: ["uv", "run", "pytest", "-q"]', command)
    with pytest.raises(ValueError, match="command"):
        load_gate(write(tmp_path, text), "landing")


def test_a_claim_entry_that_is_neither_a_string_nor_a_mapping_is_refused(
    tmp_path: Path,
) -> None:
    text = GOOD.replace(
        "      - claim_id: tests-executed\n"
        '        command: ["uv", "run", "pytest", "-q"]\n',
        "      - [tests-executed]\n",
    )
    with pytest.raises(ValueError):
        load_gate(write(tmp_path, text), "landing")


def test_a_duplicate_claim_id_in_one_gate_is_refused(tmp_path: Path) -> None:
    """ADR-001 sad path 4.

    `Gate` already refuses duplicates at construction, but the loader is what
    the operator's file reaches first, and two entries for one claim have no
    defined meaning: one of the two commands silently decides the claim. Refused
    where the ambiguity is written, not two layers later.
    """

    text = GOOD.replace(
        '      - claim_id: tests-executed\n        command: ["uv", "run", "pytest", "-q"]\n',
        '      - claim_id: tests-executed\n        command: ["uv", "run", "pytest", "-q"]\n'
        '      - claim_id: tests-executed\n        command: ["true"]\n',
    )
    assert text != GOOD, "the duplicate entry must actually have been added"
    with pytest.raises(ValueError, match="tests-executed"):
        load_gate(write(tmp_path, text), "landing")


def test_unknown_keys_in_a_claim_entry_are_refused(tmp_path: Path) -> None:
    """The gate entry already refuses unknown keys; a claim entry is now part of
    the trust root too, and `waiver: yes` must not be silently ignored there."""

    text = GOOD.replace(
        '        command: ["uv", "run", "pytest", "-q"]\n',
        '        command: ["uv", "run", "pytest", "-q"]\n        waiver: yes\n',
    )
    with pytest.raises(ValueError, match="unknown"):
        load_gate(write(tmp_path, text), "landing")


# --- criterion 10: this repository's own gate is honest ---------------------


def test_this_repositorys_gate_catalog_loads_under_the_new_schema() -> None:
    """`governance/gates.yaml` is the committed trust root for this repo. It
    carries the old shape, so this slice has to migrate it or the CLI refuses
    every evaluation here."""

    gate = load_gate(REPO_ROOT / "governance" / "gates.yaml", "landing")
    assert gate.required_claims
    for claim in gate.required_claims:
        assert isinstance(claim.claim_id, str) and claim.claim_id.strip()
        argv = list(claim.command)
        assert argv, f"{claim.claim_id} declares an empty command"
        assert all(isinstance(part, str) for part in argv), (
            f"{claim.claim_id} declares a command that is not an argv: {argv}"
        )


def test_no_required_claim_is_bound_to_a_trivially_true_command() -> None:
    """The whole point of the slice, applied to our own catalog.

    A claim bound to `true` is the defect wearing the new schema: the loader
    accepts it, the digest matches, and the gate blocks nothing.
    """

    gate = load_gate(REPO_ROOT / "governance" / "gates.yaml", "landing")
    bound_to_nothing = [
        claim.claim_id
        for claim in gate.required_claims
        if normalised(tuple(claim.command)) in TRIVIAL_COMMANDS
    ]
    assert not bound_to_nothing, (
        f"{bound_to_nothing} are bound to a command that succeeds against any "
        "tree; naming a placeholder command is faking the claim"
    )


@pytest.mark.parametrize(
    "argv",
    [["/bin/true"], ["/usr/bin/true"], ["true"], ["sh", "-c", "exit 0"]],
)
def test_the_trivial_command_guard_is_not_defeated_by_spelling(
    tmp_path: Path,
    argv: list[str],
) -> None:
    """The guard above is a denylist, so its own blind spots need a test.

    An audit bound this repository's `landing` gate to `/bin/true` and the
    contract file stayed entirely green: the denylist held `("true",)` and
    compared the raw argv, so one absolute path walked past it. A check that a
    reviewer trusts and a path prefix defeats is worse than no check, because it
    is read as coverage.
    """

    assert normalised(tuple(argv)) in TRIVIAL_COMMANDS, (
        f"{argv} succeeds against any tree and the guard does not recognise it"
    )


def test_contracts_validated_is_no_longer_required_by_landing() -> None:
    """Nothing produces `contracts-validated`, and today that is invisible only
    because `-- true` satisfies it. After this slice it needs a real command and
    there is no contracts validator to name, so per STATE.md's standing
    instruction — write one or amend the gate, do not fake the claim — the claim
    is dropped and the debt stays recorded."""

    gate = load_gate(REPO_ROOT / "governance" / "gates.yaml", "landing")
    assert "contracts-validated" not in {
        claim.claim_id for claim in gate.required_claims
    }, (
        "`landing` still requires a claim nothing produces; with a real command "
        "bound to it the gate is permanently unsatisfiable, which is not a "
        "control but a broken gate"
    )


def test_the_wired_gate_compares_the_same_digest_run_records(tmp_path: Path) -> None:
    """One digest implementation, not two.

    Goes through the composition root rather than the loader alone: the value
    the kernel compares has to be the value `run` writes for the same argv, and
    a second encoding anywhere between the two makes the binding unsatisfiable
    while looking correct in both files.
    """

    from ranex.bootstrap.composition import build_gate_evaluator
    from ranex.governed_execution.api import Evidence, Verdict

    subject = "sha256:" + "a" * 64
    recorded = Evidence(
        claim_id="tests-executed",
        subject_digest=subject,
        producer_id="worker",
        command=" ".join(BOUND_ARGV),
        command_digest=command_digest(BOUND_ARGV),
        executable_path="/usr/bin/uv",
        exit_code=0,
    )

    # Catalog bytes, not a path: the composition root no longer re-reads the
    # working tree at evaluation time. No assertion below changes.
    result = build_gate_evaluator(GOOD.encode("utf-8"), None).evaluate(
        "landing",
        (recorded,),
        subject_digest=subject,
        approver_id="reviewer",
    )
    assert result.verdict is Verdict.PASS, result.reason


def test_the_wired_gate_refuses_a_suite_claim_without_a_manifest() -> None:
    from ranex.bootstrap.composition import build_gate_evaluator

    catalog = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
        results_artifact: artifacts/junit.xml
"""

    evaluator = build_gate_evaluator(catalog.encode("utf-8"))
    with pytest.raises(
        ValueError,
        match="suite-results claim requires a committed suite manifest",
    ):
        evaluator.evaluate(
            "landing",
            (),
            subject_digest="sha256:" + "a" * 64,
            approver_id="reviewer",
        )


def test_the_wired_gate_loads_a_present_suite_manifest() -> None:
    from ranex.bootstrap.composition import build_gate_evaluator
    from ranex.governed_execution.api import Verdict

    catalog = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
        results_artifact: artifacts/junit.xml
"""
    manifest = (
        b'{"expected_skips":{},"suite":["tests/test_sample.py::test_one"]}'
    )

    result = build_gate_evaluator(
        catalog.encode("utf-8"),
        suite_manifest=manifest,
    ).evaluate(
        "landing",
        (),
        subject_digest="sha256:" + "a" * 64,
        approver_id="reviewer",
    )

    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
