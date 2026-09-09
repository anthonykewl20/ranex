"""Negative controls and calibration recall — MAP §8.4 consequence 3.

The map has said for months that this is "the smallest shippable piece of §8.4
and should be built first", and §8.4's recall rule says why:

    When a gauge is found out of calibration, **every part it passed** since
    its last good check is suspect and is recalled. Not the parts it rejected.
    The ones it approved — because a bad gauge does not produce visible errors,
    it produces confident approvals.

`release_audit.py` already records controls, but its vocabulary collapses to
VERIFIED or GAP. That cannot express the two outcomes that matter most: a check
which accepted the thing it exists to refuse, and a check whose answer changes
between identical runs. Both were observed on this repository on 2026-09-09,
and neither had a name.

An expectation here is a **pair**. A positive that must hold and a negative
that must be refused, each run `repeats` times on identical input. A control
with no negative is not a passing control; it is a GAP, because nobody knows
whether it could ever fail.

This module runs controls and classifies them. It decides nothing about the
kernel: it is a measuring instrument, and instruments measure.
"""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any

SCHEMA = "ranex-calibration-v1"
DEFAULT_REPEATS = 3


class Status(StrEnum):
    """Closed vocabulary. PASS is deliberately absent — that word belongs to a
    verdict, and a measurement that borrows it invites being read as one."""

    VERIFIED = "VERIFIED"
    GAP = "GAP"
    FALSE_PASS = "FALSE-PASS"
    NON_DETERMINISTIC = "NON-DETERMINISTIC"
    UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True, slots=True)
class Observation:
    """One execution of one side of a control.

    `ok` is what the caller observed, never what it hoped: for a positive it
    means the expectation held, for a negative it means the check *accepted*
    the bad input. A negative whose `ok` is True is the alarm.
    """

    ok: bool
    facts: dict[str, Any]

    @property
    def digest(self) -> str:
        """Canonical digest of the observed facts, for repeat comparison.

        Sorted, separator-fixed, and `allow_nan=False`: a value that cannot
        serialise deterministically was never evidence.
        """

        return sha256(
            json.dumps(self.facts, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class Control:
    """A positive that must hold and a negative that must be refused.

    `negative=None` is permitted and always classifies GAP. Refusing to accept
    such a control at construction would push authors to write a decorative
    negative to get past the constructor, which is worse than an honest GAP.
    """

    name: str
    expectation: str
    positive: Callable[[], Observation]
    negative: Callable[[], Observation] | None = None
    deterministic: bool = True


@dataclass
class Calibration:
    """Runs controls, classifies them, and writes one receipt."""

    out: Path
    repeats: int = DEFAULT_REPEATS
    journal: Path | None = None
    history: Path | None = None
    cases: list[dict[str, Any]] = field(default_factory=list)

    def run(self, control: Control) -> dict[str, Any]:
        started = time.time()
        positive = [control.positive() for _ in range(self.repeats)]
        negative = (
            [control.negative() for _ in range(self.repeats)]
            if control.negative is not None
            else []
        )
        status, reason = self._classify(control, positive, negative)

        case: dict[str, Any] = {
            "control": control.name,
            "expectation": control.expectation,
            "status": str(status),
            "reason": reason,
            "repeats": self.repeats,
            "positive": _side(positive),
            "negative": _side(negative) if control.negative is not None else None,
            "duration_s": round(time.time() - started, 3),
        }
        if status is Status.FALSE_PASS:
            case["recall"] = self.recall_window(control.name)
        self.cases.append(case)
        print(f"{status} {control.name}: {reason}", flush=True)
        self.save()
        return case

    def _classify(
        self,
        control: Control,
        positive: list[Observation],
        negative: list[Observation],
    ) -> tuple[Status, str]:
        if control.negative is None:
            return (
                Status.GAP,
                "no negative control: nobody knows whether this check can fail",
            )
        if control.deterministic:
            for label, side in (("positive", positive), ("negative", negative)):
                digests = {item.digest for item in side}
                if len(digests) > 1:
                    return (
                        Status.NON_DETERMINISTIC,
                        f"{label} produced {len(digests)} distinct results from identical "
                        f"input across {self.repeats} repeats",
                    )
        if any(item.ok for item in negative):
            accepted = sum(1 for item in negative if item.ok)
            return (
                Status.FALSE_PASS,
                f"the negative control was ACCEPTED in {accepted}/{len(negative)} repeats; "
                "this check cannot block what it exists to refuse",
            )
        if not all(item.ok for item in positive):
            failed = sum(1 for item in positive if not item.ok)
            return (
                Status.GAP,
                f"the positive control was refused in {failed}/{len(positive)} repeats "
                "(a known-good input was rejected)",
            )
        return (
            Status.VERIFIED,
            f"held in {self.repeats} repeats and refused its negative in {self.repeats}",
        )

    def recall_window(self, control: str) -> dict[str, Any]:
        """Which verdicts this gauge approved since it was last known good.

        §8.4's rule, made computable. The window opens at the journal head this
        control last recorded while VERIFIED, and closes at the current head;
        every evaluation appended between them was approved by an instrument
        now known to accept what it should refuse.

        Reports what it could not establish rather than guessing: with no prior
        VERIFIED receipt the window is the whole chain, and that is said out
        loud instead of being narrowed to look tidy.
        """

        previous = self._last_verified_head(control)
        rows = self._journal_rows()
        if rows is None:
            return {
                "suspect_from": previous,
                "determinable": False,
                "detail": "no journal was configured; the window cannot be computed here",
            }
        if previous is None:
            return {
                "suspect_from": None,
                "determinable": True,
                "suspect_count": len(rows),
                "suspect_positions": [row[0] for row in rows],
                "detail": (
                    "no prior VERIFIED run of this control is on record, so every "
                    "evaluation in the chain is suspect"
                ),
            }
        after = [row for row in rows if row[1] > previous]
        return {
            "suspect_from": previous,
            "determinable": True,
            "suspect_count": len(after),
            "suspect_positions": [row[0] for row in after],
            "detail": (
                f"{len(after)} evaluation(s) were approved after this control was last "
                "VERIFIED and are recalled"
            ),
        }

    def _journal_rows(self) -> list[tuple[int, int]] | None:
        if self.journal is None or not self.journal.is_file():
            return None
        connection = sqlite3.connect(f"{self.journal.as_uri()}?mode=ro", uri=True)
        try:
            return [
                (int(seq), int(seq))
                for (seq,) in connection.execute(
                    "SELECT seq FROM evaluations ORDER BY seq ASC"
                ).fetchall()
            ]
        except sqlite3.Error:
            return None
        finally:
            connection.close()

    def _last_verified_head(self, control: str) -> int | None:
        """The journal position this control last recorded while VERIFIED."""

        if self.history is None or not self.history.is_dir():
            return None
        best: int | None = None
        for receipt in sorted(self.history.rglob("calibration.json")):
            try:
                loaded = json.loads(receipt.read_bytes())
            except (OSError, ValueError):
                continue
            if loaded.get("schema") != SCHEMA:
                continue
            for case in loaded.get("cases", []):
                if case.get("control") == control and case.get("status") == Status.VERIFIED:
                    head = case.get("journal_head")
                    if isinstance(head, int) and (best is None or head > best):
                        best = head
        return best

    @property
    def worst(self) -> Status:
        """The receipt's own verdict-free summary, worst outcome first."""

        order = (
            Status.FALSE_PASS,
            Status.NON_DETERMINISTIC,
            Status.GAP,
            Status.UNVERIFIED,
            Status.VERIFIED,
        )
        seen = {case["status"] for case in self.cases}
        for status in order:
            if str(status) in seen:
                return status
        return Status.VERIFIED

    def save(self) -> None:
        self.out.mkdir(parents=True, exist_ok=True)
        rows = self._journal_rows()
        (self.out / "calibration.json").write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "repeats": self.repeats,
                    "journal_head": rows[-1][0] if rows else None,
                    "worst": str(self.worst),
                    "cases": self.cases,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def exit_code(self) -> int:
        """0 only when every control is VERIFIED or explicitly UNVERIFIED.

        A GAP is not a pass: it means the expectation has no executable
        negative, so its green says nothing.
        """

        blocking = {Status.FALSE_PASS, Status.NON_DETERMINISTIC, Status.GAP}
        return 1 if any(case["status"] in {str(s) for s in blocking} for case in self.cases) else 0


def _side(observations: list[Observation]) -> dict[str, Any]:
    return {
        "runs": len(observations),
        "ok": [item.ok for item in observations],
        "digests": [item.digest for item in observations],
        "identical": len({item.digest for item in observations}) <= 1,
        "facts": [item.facts for item in observations],
    }


# --------------------------------------------------------------------------
# The controls. Each is a real `ranex run` + `gate evaluate` on a real Git
# repository with real Ed25519 keys — no mocked seam, no constructed verdict.
# --------------------------------------------------------------------------

import os
import shlex
import subprocess
import tempfile

#: The scanner the gate binds. Held in argv rather than a committed script:
#: containment refuses an argv[0] inside the subject, and an in-tree script
#: reached by a system interpreter was measured escaping that check entirely
#: (ADR-060), so a control's own gauge must not live in the tree it judges.
_SCANNER = (
    "import pathlib,sys;"
    "bad=[p for p in pathlib.Path('.').rglob('*.py') "
    "if 'ranex:' in p.read_text() and ';' not in p.read_text().split('ranex:')[1].split(chr(10))[0]];"
    "print('markers without a trigger:',len(bad));"
    "sys.exit(1 if bad else 0)"
)


#: A gauge that cannot fail. Used only to prove the alarm fires: it is a real
#: bound command on a real gate, and it green-lights the violating tree.
_BLUNT_SCANNER = "import sys;print('all clear');sys.exit(0)"


class Subject:
    """A real governed repository with a good commit and a violating one."""

    def __init__(self, root: Path, python: str, scanner: str = "") -> None:
        self.root = root
        self.python = python
        self.scanner = scanner or _SCANNER
        self.repo = root / "subject"
        self.key = root / "worker.key"
        self.good = ""
        self.bad = ""

    def _git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                       capture_output=True, text=True)

    def _cli(self, *args: str, key: bool = True) -> subprocess.CompletedProcess[str]:
        """Always names the subject explicitly.

        A governed subcommand anchors to the checkout holding the CLI, never to
        the caller's cwd (ADR-038), so running from inside this scratch
        repository judges *Ranex* instead. `--external-repository` is the only
        thing that points it here (ADR-052); without it the first version of
        this driver read Ranex's own gates.yaml and reported every control GAP.
        """

        env = {"PATH": "/usr/bin:/bin", "HOME": str(self.root / "home"), "LANG": "C.UTF-8"}
        if key:
            env["RANEX_SIGNING_KEY"] = str(self.key)
        # Inserted BEFORE any `--`: `run` takes everything after the separator
        # as the command it must execute (argparse.REMAINDER), so a flag
        # appended at the end is swallowed into the observed argv instead of
        # being parsed. The first version of this driver did exactly that and
        # every control reported GAP.
        argv = list(args)
        anchor = ["--external-repository", str(self.repo)]
        position = argv.index("--") if "--" in argv else len(argv)
        argv[position:position] = anchor
        return subprocess.run(
            [self.python, "-m", "ranex.cli.main", *argv],
            cwd=str(self.repo), env=env, capture_output=True, text=True,
            timeout=300, check=False,
        )

    def build(self) -> None:
        (self.root / "home").mkdir(parents=True, exist_ok=True)
        self.repo.mkdir(parents=True)
        (self.repo / "governance").mkdir()
        self._git("init", "-q", ".")
        self._git("config", "user.email", "calibration@example.invalid")
        self._git("config", "user.name", "Calibration")
        (self.repo / ".gitignore").write_text(
            "governance/journal.sqlite3\ngovernance/evidence.json\n", encoding="utf-8"
        )
        command = json.dumps(["/usr/bin/python3", "-c", self.scanner])
        (self.repo / "governance" / "gates.yaml").write_text(
            "gates:\n"
            "  - gate_id: landing\n"
            "    rule_id: MARKERS_DECLARED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: markers-declared\n"
            f"        command: {command}\n",
            encoding="utf-8",
        )
        generated = self._cli("keygen", "--producer", "worker")
        public = ""
        for token in generated.stdout.split():
            if token.startswith("ed25519:"):
                public = token
                break
        if not public:
            raise RuntimeError(f"keygen printed no public key: {generated.stdout!r}")
        (self.repo / "governance" / "producers.yaml").write_text(
            f"producers:\n  worker: {public}\n"
            f"principals:\n  worker:\n    role: worker\n    keys:\n"
            f"      - key: {public}\n        status: active\n",
            encoding="utf-8",
        )
        (self.repo / "good.py").write_text(
            "# ranex: single-threaded scan; parallelise past 100k files\n", encoding="utf-8"
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "a marker that declares its trigger")
        self.good = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"],
                                   capture_output=True, text=True, check=True).stdout.strip()
        (self.repo / "bad.py").write_text("# ranex: global lock\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "a marker with no trigger")
        self.bad = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        self._git("checkout", "-q", self.good)

    def observe(self, ref: str, *, approver: str = "auditor",
                evidence: bool = True, producer: str = "worker") -> Observation:
        """Record evidence at `ref` and judge it. `ok` means the gate said PASS."""

        self._git("checkout", "-q", ref)
        store = self.repo / "governance" / "evidence.json"
        store.unlink(missing_ok=True)
        (self.repo / "governance" / "journal.sqlite3").unlink(missing_ok=True)
        if evidence:
            self._cli("run", "--claim", "markers-declared", "--producer", producer,
                      "--", "/usr/bin/python3", "-c", self.scanner)
        verdict = self._cli("gate", "evaluate", "HEAD", "--approver", approver, key=False)
        first = verdict.stdout.split("\n", 1)[0].split("  ")[0].strip()
        return Observation(
            ok=first == "PASS",
            facts={"verdict": first, "exit": verdict.returncode, "evidence": evidence},
        )


def _controls(subject: Subject) -> list[Control]:
    """Four properties of the kernel, each paired with what must refuse it."""

    return [
        Control(
            name="gate-blocks-a-failing-bound-command",
            expectation="the gate PASSes a clean subject and FAILs one the bound scanner refuses",
            positive=lambda: subject.observe(subject.good),
            negative=lambda: _inverted(subject.observe(subject.bad)),
        ),
        Control(
            name="absence-blocks",
            expectation="a required claim with no evidence FAILs; it is never a default or a skip",
            positive=lambda: subject.observe(subject.good),
            negative=lambda: _inverted(subject.observe(subject.good, evidence=False)),
        ),
        Control(
            name="self-approval-refused",
            expectation="a producer cannot approve its own evidence",
            positive=lambda: subject.observe(subject.good, approver="auditor"),
            negative=lambda: _inverted(subject.observe(subject.good, approver="worker")),
        ),
    ]


def _blunted_control(subject: Subject) -> Control:
    """The alarm, on real data: a gate whose gauge cannot fail.

    Everything here is real — a real catalog binding a real command, real
    signed evidence, a real verdict. The only difference is that the bound
    scanner always exits 0, so the violating tree earns a PASS. That is
    precisely the failure §8.4 exists for: not a visible error, a confident
    approval. The control must come back FALSE-PASS and name the window of
    verdicts the blunt gauge already approved.
    """

    return Control(
        name="a-blunted-gauge-is-caught-as-false-pass",
        expectation="a gate whose bound command cannot fail is reported FALSE-PASS, not VERIFIED",
        positive=lambda: subject.observe(subject.good),
        negative=lambda: _inverted(subject.observe(subject.bad)),
    )


def _inverted(observation: Observation) -> Observation:
    """A negative control's `ok` means the check ACCEPTED the bad input.

    Stated as its own function because the inversion is the whole subtlety of a
    negative control: `ok=True` here is the alarm, not the success.
    """

    return Observation(ok=observation.ok, facts=observation.facts)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="receipt directory")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS)
    parser.add_argument("--journal", type=Path, default=None,
                        help="journal whose head bounds a recall window")
    parser.add_argument("--history", type=Path, default=None,
                        help="directory of prior receipts, for the recall window")
    parser.add_argument("--prove-alarms", action="store_true",
                        help="add a deliberately blunted gauge; the run must report FALSE-PASS")
    args = parser.parse_args()

    root = Path(tempfile.mkdtemp(prefix="ranex-calibration-"))
    subject = Subject(root, os.environ.get("RANEX_PYTHON", "python3"))
    try:
        subject.build()
        calibration = Calibration(out=args.out, repeats=args.repeats,
                                  journal=args.journal, history=args.history)
        controls = _controls(subject)
        blunted: Subject | None = None
        if args.prove_alarms:
            blunted = Subject(root / "blunt", subject.python, scanner=_BLUNT_SCANNER)
            blunted.build()
            controls.append(_blunted_control(blunted))
        for control in controls:
            calibration.run(control)
        print(f"\nworst: {calibration.worst}  receipt: {args.out / 'calibration.json'}")
        return calibration.exit_code()
    finally:
        # Private keys are generated per run and never outlive it.
        subprocess.run(["rm", "-rf", str(root)], check=False)


if __name__ == "__main__":
    raise SystemExit(main())
