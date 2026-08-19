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

import pytest

from ranex.foundation.signing import generate_keypair, sign_evidence

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


@dataclass
class Signing:
    """Per-producer keys, kept outside the repository under test."""

    root: Path
    private: dict[str, str] = field(default_factory=dict)
    public: dict[str, str] = field(default_factory=dict)

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

    def key_path(self, producer: str) -> Path:
        """The private key file for a producer, for $RANEX_SIGNING_KEY.

        Unknown producers get a key that is deliberately NOT in the keyring, so
        a test naming an unregistered producer fails the way production would.
        """

        self.register(producer)
        return self.root / f"{producer}.key"

    def write_keyring(self, repo: Path, name: str = "producers.yaml") -> None:
        lines = "\n".join(
            f"  {producer}: {key}" for producer, key in sorted(self.public.items())
        )
        (repo / name).write_text(f"producers:\n{lines}\n", encoding="utf-8")

    def sign(self, content: dict[str, object], producer: str) -> dict[str, object]:
        """A record as `run` would have written it, for tests that hand-build
        evidence instead of producing it."""

        self.register(producer)
        body = {**content}
        body.setdefault("suite_results", None)
        body.setdefault("confinement_result_digest", "sha256:" + "c" * 64)
        body.setdefault("confinement_profile_digest", "sha256:" + "d" * 64)
        return {**body, "signature": sign_evidence(body, self.private[producer])}


# Keyed by repository path so the helpers in each test module can reach the
# signing material without changing the signature of every test function.
_REGISTRY: dict[Path, Signing] = {}


def attach(repo: Path, signing: Signing) -> Signing:
    _REGISTRY[repo.resolve()] = signing
    return signing


def signing_for(repo: Path) -> Signing:
    return _REGISTRY[repo.resolve()]


@pytest.fixture()
def signing(tmp_path: Path) -> Signing:
    root = tmp_path / "keys"
    root.mkdir(parents=True, exist_ok=True)
    return Signing(root=root).register(*KNOWN_PRODUCERS)


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
