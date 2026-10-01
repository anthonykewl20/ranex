"""Signing setup for the end-to-end tests.

SLICE-002 made signing mandatory: `run` refuses to write without a key, and
`gate evaluate` refuses to admit anything without a keyring. The SLICE-001 e2e
tests predate that. Every contract they assert is still true — exit codes are
still recorded verbatim, a dirty tree is still refused, subject binding still
holds — so they gain the setup a signed world requires rather than being
weakened or deleted.

The helpers live here, and the test bodies are left alone deliberately: the
SLICE-001 assertions are the record of what that slice proved, and a green suite
means more if they did not move to get there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import _history
import pytest

from ranex.foundation.signing import ENVELOPE_TYPE, generate_keypair, sign_evidence

# Every producer identity any e2e test uses. Registered up front so the keyring
# is committed with the rest of the tree and `run` sees a clean working tree.
KNOWN_PRODUCERS = (
    "worker",
    "worker-a",
    "worker-b",
    "alice",
    "auditor",
    "reviewer",
    "w",
    "someone",
)

# RISK-07 / issue #107: the names the e2e suites pass to `--approver`. Every
# keyring `write_keyring` writes now carries a `principals:` block, and each
# of these names is an `approver`-role principal there (every other registered
# name is a worker principal, which is what `_require_blocks_agree` demands).
# A name that also produces evidence keeps its `producers:` entry: admission
# does not consult roles, and the kernel's own no-self-approval comparison is
# what fires when the two meet — unchanged by this slice.
APPROVER_NAMES = (
    "owner",
    "reviewer",
    "reviewer_alice",
    "someone",
    "alice",
    "pilot",
    "slice036-observer-calibration",
)


@dataclass
class Signing:
    """Per-producer keys, kept outside the repository under test."""

    root: Path
    private: dict[str, str] = field(default_factory=dict)
    public: dict[str, str] = field(default_factory=dict)
    #: The repository these keys sign for, set by `attach`. Needed because a
    #: SLICE-081 record binds the gate catalog it was produced under, and a
    #: hand-built record must name the same catalog the gate will be judged by
    #: or it is refused as policy-context-mismatch — correctly, but for a
    #: reason the test did not intend to exercise.
    repo: Path | None = None
    service_private: str = field(init=False)
    service_public: str = field(init=False)
    service_path: Path = field(init=False)
    histories: dict[tuple[Path, str], Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.service_private, self.service_public, self.service_path = _history.mint_service(self.root)

    def establish_history(self, repo: Path, name: str = "evidence.json") -> Path:
        key = (repo.resolve(), name)
        if key not in self.histories:
            checkpoint = self.root / f"history-{len(self.histories)}.json"
            _history.establish(repo, name, checkpoint, self.service_private, self.service_public)
            self.histories[key] = checkpoint
        return self.histories[key]

    def configure_history(self, monkeypatch, repo: Path, name: str = "evidence.json") -> None:
        checkpoint = self.establish_history(repo, name)
        monkeypatch.setenv("RANEX_HISTORY_CHECKPOINT", str(checkpoint))
        monkeypatch.setenv("RANEX_VERDICT_SIGNING_KEY", str(self.service_path))
        monkeypatch.delenv("RANEX_VERDICT_DIR", raising=False)

    def write_records(self, repo: Path, records, name: str = "evidence.json") -> None:
        checkpoint = self.establish_history(repo, name)
        _history.write_records(repo, name, records, checkpoint, self.service_private, self.service_public)

    def register(self, *producers: str) -> Signing:
        for producer in producers:
            if producer in self.private:
                continue
            private_key, public_key = generate_keypair()
            self.private[producer] = private_key
            self.public[producer] = public_key
            path = self.root / f"{producer}.key"
            path.write_text(private_key + "\n", encoding="utf-8")
            path.chmod(0o600)
        return self

    def catalog_digest(self) -> str:
        """The digest of the catalog the attached repository actually carries.

        Falls back to `catalog-absent` when there is none, which is exactly what
        `run` records in that case — so a hand-built record and a real one agree
        about a repository with no rulebook.
        """

        from ranex.bootstrap.composition import catalog_digest_for
        from ranex.foundation.signing import CATALOG_ABSENT

        if self.repo is None:
            return CATALOG_ABSENT
        for name in ("gates.yaml", "governance/gates.yaml"):
            candidate = self.repo / name
            if candidate.is_file():
                return catalog_digest_for(candidate.read_bytes())
        return CATALOG_ABSENT

    def key_path(self, producer: str) -> Path:
        """The private key file for a producer, for $RANEX_SIGNING_KEY.

        Unknown producers get a key that is deliberately NOT in the keyring, so
        a test naming an unregistered producer fails the way production would.
        """

        self.register(producer)
        return self.root / f"{producer}.key"

    def approver_path(self, approver: str) -> Path:
        """The private key file for a catalogued approver, for
        $RANEX_APPROVER_SIGNING_KEY (RISK-07).

        The keyring `write_keyring` wrote carries this name as an
        `approver`-role principal bound to exactly this key, so an evaluation
        naming it passes possession and judges. A name no keyring wrote stays
        unregistered on purpose — a test naming an uncatalogued approver is
        exercising `E-APPROVER-UNKNOWN`, and minting a key for it here would
        silently move that refusal's goalposts.
        """

        if approver not in self.public:
            raise KeyError(
                f"{approver!r} was not registered when the keyring was written; "
                "an uncatalogued approver is a refusal, not a key to mint"
            )
        return self.root / f"{approver}.key"

    def write_keyring(self, repo: Path, name: str = "producers.yaml") -> None:
        lines = "\n".join(
            f"  {producer}: {key}" for producer, key in sorted(self.public.items())
        )
        principals = "\n".join(
            f"  {principal}:\n    role: "
            f"{'approver' if principal in APPROVER_NAMES else 'worker'}\n"
            f"    keys:\n      - key: {key}\n        status: active"
            for principal, key in sorted(self.public.items())
        )
        (repo / name).write_text(
            f"producers:\n{lines}\nprincipals:\n{principals}\n", encoding="utf-8"
        )
        _history.register_service(repo / name, self.service_public)

    def sign(self, content: dict[str, object], producer: str) -> dict[str, object]:
        """A record as `run` would have written it, for tests that hand-build
        evidence instead of producing it."""

        self.register(producer)
        body = {**content}
        body.setdefault("suite_results", None)
        body.setdefault("confinement_result_digest", "sha256:" + "c" * 64)
        body.setdefault("confinement_profile_digest", "sha256:" + "d" * 64)
        # SLICE-081: the policy context a record binds. Defaulted so hand-built
        # evidence stays terse, overridable by any test that must name the real
        # catalog its gate will be evaluated under.
        body.setdefault("envelope_type", ENVELOPE_TYPE)
        body.setdefault("gate_id", "landing")
        body.setdefault("catalog_digest", self.catalog_digest())
        return {**body, "signature": sign_evidence(body, self.private[producer])}


# Keyed by repository path so the helpers in each test module can reach the
# signing material without changing the signature of every test function.
_REGISTRY: dict[Path, Signing] = {}


def attach(repo: Path, signing: Signing) -> Signing:
    _REGISTRY[repo.resolve()] = signing
    signing.repo = repo
    return signing


def signing_for(repo: Path) -> Signing:
    return _REGISTRY[repo.resolve()]


@pytest.fixture()
def signing(tmp_path: Path) -> Signing:
    root = tmp_path / "keys"
    root.mkdir(parents=True, exist_ok=True)
    # The approver names ride along so `write_keyring` can catalogue them as
    # approver principals — possession needs their private halves on disk.
    return Signing(root=root).register(*KNOWN_PRODUCERS, *APPROVER_NAMES)


# --- SLICE-055 / ADR-032: the frame's module-scoped prereq fixtures -------------
#
# Extensions only — everything above (the Signing registry) is untouched.
# Each fixture consumes one frozen probe from tests/e2e/_prereqs.py through
# prereq_or_skip: a module re-evaluates its precondition at its own
# module-scoped setup, so no cached answer crosses a module boundary or a
# process, and every skip carries the machine-greppable reason grammar
# (ranex-prereq:<name>:) the declared-skip ledger greps. Nothing existing
# requests these fixtures; the family slices (SLICE-056+) do, so the default
# suite path is unchanged.

import sys as _sys  # noqa: E402

if str(Path(__file__).resolve().parent) not in _sys.path:
    _sys.path.insert(0, str(Path(__file__).resolve().parent))

import _prereqs  # noqa: E402


@pytest.fixture(scope="module")
def prereq_pinned_resolver() -> None:
    """Skip this module unless the pinned resolver is present and matches."""
    _prereqs.prereq_or_skip("pinned_resolver")


@pytest.fixture(scope="module")
def prereq_network_available() -> None:
    """Skip this module unless an outbound connection to the real index works."""
    _prereqs.prereq_or_skip("network_available")


@pytest.fixture(scope="module")
def prereq_signing_key() -> None:
    """Skip this module unless RANEX_SIGNING_KEY names an existing key file."""
    _prereqs.prereq_or_skip("signing_key")


@pytest.fixture(scope="module")
def prereq_harness_fork() -> None:
    """Skip this module unless RANEX_HARNESS_DIR names the sibling fork."""
    _prereqs.prereq_or_skip("harness_fork")


@pytest.fixture(scope="module")
def prereq_openrouter_key() -> None:
    """Skip this module unless a real OpenRouter credential is exported."""
    _prereqs.prereq_or_skip("openrouter_key")


@pytest.fixture(scope="module")
def prereq_qualified_host() -> None:
    """Skip this module unless this host passes the qualification limitation probe."""
    _prereqs.prereq_or_skip("qualified_host")
