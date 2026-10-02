"""Version-dispatched signing and a base-generated deterministic v1 vector."""

from pathlib import Path

import pytest

from ranex.foundation import signing as sg
from ranex.foundation.settings import load_settings, settings_digest
from ranex.foundation.canonical import canonical_sha256

CONTENT = {
    "claim_id": "tests-executed",
    "command": "uv run pytest -q",
    "command_digest": "sha256:" + canonical_sha256(["uv", "run", "pytest", "-q"]),
    "executable_path": "/usr/bin/uv",
    "exit_code": 0,
    "producer_id": "worker",
    "subject_digest": "sha256:" + "a" * 64,
    "suite_results": None,
    "confinement_result_digest": "sha256:" + "c" * 64,
    "confinement_profile_digest": "sha256:" + "d" * 64,
    "envelope_type": "ranex-evidence-envelope-v1",
    "gate_id": "landing",
    "catalog_digest": "sha256:" + "e" * 64,
}

# Generated once with dbaab957a's signing.py and its generate_keypair setup.
PRIVATE = "ed25519:nc17XFvcmwPpau9n2j2bhSVv2VCKrW0SFxdlfQr2EgU="
PUBLIC = "ed25519:iDLi+/PBcxqyV/jQ0M3n1aPlWlpjmRlsR4b8vYML7+w="
V1_SIGNATURE = (
    "ed25519:d6/hulTn+hbslmpf7bceyz3tj3enWjSXjlny2JlquAWEZxjO11+gSJdrZvvMsAv3"
    "CU2ab6j5eZwKOmGZCFuxDw=="
)


@pytest.fixture()
def v2():
    settings = load_settings(Path(__file__).resolve().parents[2], environ={})
    return {**CONTENT, "envelope_type": "ranex-evidence-envelope-v2",
            "settings_digest": settings_digest(settings), "settings_schema_version": 1}


def test_v1_round_trip():
    private, public = sg.generate_keypair()
    assert sg.verify_evidence(CONTENT, sg.sign_evidence(CONTENT, private), public)


def test_pinned_v1_vector():
    assert CONTENT["envelope_type"] == sg.ENVELOPE_TYPE
    assert sg.sign_evidence(CONTENT, PRIVATE) == V1_SIGNATURE
    assert sg.verify_evidence(CONTENT, V1_SIGNATURE, PUBLIC)


def test_v2_round_trip(v2):
    assert sg.ENVELOPE_TYPE_V2 == v2["envelope_type"]
    assert sg.SIGNED_FIELDS_V2 == sg.SIGNED_FIELDS + ("settings_digest", "settings_schema_version")
    signature = sg.sign_evidence(v2, PRIVATE)
    assert sg.verify_evidence(v2, signature, PUBLIC)


def test_tampered_settings_digest(v2):
    signature = sg.sign_evidence(v2, PRIVATE)
    assert not sg.verify_evidence({**v2, "settings_digest": v2["settings_digest"] + "x"}, signature, PUBLIC)


@pytest.mark.parametrize("change", ["missing-schema", "bool-schema", "extra-v1", "unknown", "missing-type", "empty-digest", "nonstring-digest"])
def test_malformed_envelopes_refused(v2, change):
    content = dict(v2)
    if change == "missing-schema":
        del content["settings_schema_version"]
    elif change == "bool-schema":
        content["settings_schema_version"] = True
    elif change == "extra-v1":
        content["envelope_type"] = sg.ENVELOPE_TYPE
    elif change == "unknown":
        content = {**CONTENT, "envelope_type": "unknown"}
    elif change == "missing-type":
        content = dict(CONTENT)
        del content["envelope_type"]
    elif change == "empty-digest":
        content["settings_digest"] = ""
    else:
        content["settings_digest"] = None
    with pytest.raises(ValueError, match="envelope_type" if change in {"unknown", "missing-type"} else None):
        sg.sign_evidence(content, PRIVATE)
    assert not sg.verify_evidence(content, V1_SIGNATURE, PUBLIC)
