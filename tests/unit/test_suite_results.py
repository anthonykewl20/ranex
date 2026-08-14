"""SLICE-009 — a skip is absence, not success.

Written before the implementation and required to fail first.

This file pins three surfaces:

1. `ranex.foundation.suite_results`, a new parser/manifest module:

       freeze_manifest(junitxml_bytes, *, expected_skips=None) -> dict
       load_manifest(path) -> dict
       manifest_digest(manifest) -> str
       parse_results_artifact(path, manifest) -> dict
       suite_results_from_junitxml(junitxml_bytes, manifest) -> dict

2. `ranex.foundation.signing` / admission v4:

        EVIDENCE_DOMAIN == b"ranex-evidence-v4\\n"
       SIGNED_FIELDS == the previous seven fields plus "suite_results"
       admit(...) refuses old v2 rows and malformed v3 `suite_results`

3. The verdict rule in `ranex.governed_execution.domain.verdict`:

       Claim(..., results_required=..., manifest_digest=..., expected_ids=...,
             expected_skips=...)
       Evidence(..., suite_results=...)

The imports of the new module are deferred on purpose. A missing
`ranex.foundation.suite_results` must fail these tests individually, not abort
collection for the whole suite.
"""

from __future__ import annotations

import base64
import hashlib
import importlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ranex.foundation.canonical import canonical_json_bytes, command_digest

SUBJECT = "sha256:" + "a" * 64
COMMAND = ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
COMMAND_DIGEST = command_digest(COMMAND)
EXECUTABLE = sys.executable
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def domain() -> SimpleNamespace:
    from ranex.foundation import signing
    from ranex.governed_execution.domain import admission, verdict
    from ranex.policy.adapters.configuration.yaml import slice_gate_loader

    return SimpleNamespace(
        admission=admission,
        loader=slice_gate_loader,
        signing=signing,
        verdict=verdict,
    )


@pytest.fixture()
def suite_api():
    return importlib.import_module("ranex.foundation.suite_results")


@pytest.fixture()
def keypair(domain) -> tuple[str, str]:
    return domain.signing.generate_keypair()


def manifest(ids: list[str], expected_skips: dict[str, str] | None = None) -> dict[str, object]:
    return {
        "suite": sorted(ids),
        "expected_skips": {} if expected_skips is None else dict(expected_skips),
    }


def manifest_digest_value(value: dict[str, object]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def suite_results(
    manifest_value: dict[str, object],
    outcomes: dict[str, str],
    *,
    missing: list[str] | None = None,
    extra_count: int = 0,
) -> dict[str, object]:
    ordered = dict(sorted(outcomes.items()))
    counts = {
        "passed": sum(kind == "passed" for kind in ordered.values()),
        "skipped": sum(kind == "skipped" for kind in ordered.values()),
        "failed": sum(kind == "failed" for kind in ordered.values()),
        "errors": sum(kind == "error" for kind in ordered.values()),
        "xfailed": sum(kind == "xfailed" for kind in ordered.values()),
        "xpassed": sum(kind == "xpassed" for kind in ordered.values()),
    }
    non_passed = [
        [test_id, kind]
        for test_id, kind in sorted(ordered.items())
        if kind != "passed"
    ]
    return {
        "manifest_digest": manifest_digest_value(manifest_value),
        "counts": counts,
        "non_passed": non_passed,
        "missing": [] if missing is None else list(missing),
        "extra_count": extra_count,
        "outcome_digest": "sha256:" + hashlib.sha256(
            canonical_json_bytes(ordered)
        ).hexdigest(),
    }


def claim(domain, **overrides: object):
    kwargs: dict[str, object] = {
        "claim_id": "tests-executed",
        "command_digest": COMMAND_DIGEST,
        "results_required": True,
        "manifest_digest": manifest_digest_value(
            manifest(["tests/unit/test_x.py::test_pass"])
        ),
        "expected_ids": ("tests/unit/test_x.py::test_pass",),
        "expected_skips": {},
    }
    kwargs.update(overrides)
    return domain.verdict.Claim(**kwargs)


def evidence(domain, *, suite_results_value: dict[str, object] | None, exit_code: int = 0):
    return domain.verdict.Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command=" ".join(COMMAND),
        command_digest=COMMAND_DIGEST,
        executable_path=EXECUTABLE,
        exit_code=exit_code,
        suite_results=suite_results_value,
    )


def content(*, suite_results_value: dict[str, object] | None) -> dict[str, object]:
    return {
        "claim_id": "tests-executed",
        "command": " ".join(COMMAND),
        "command_digest": COMMAND_DIGEST,
        "executable_path": EXECUTABLE,
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": SUBJECT,
        "suite_results": suite_results_value,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }


def signed(domain, private_key: str, *, suite_results_value: dict[str, object] | None):
    body = content(suite_results_value=suite_results_value)
    return {
        **body,
        "signature": domain.signing.sign_evidence(body, private_key),
    }


def signed_v2(private_key: str, body: dict[str, object]) -> str:
    return signed_for_domain(private_key, b"ranex-evidence-v2\n", body)


def signed_for_domain(
    private_key: str,
    domain: bytes,
    body: dict[str, object],
) -> str:
    """Sign arbitrary record content without asking product validation first.

    Admission is the surface under test for malformed-but-authentic records.
    Going through ``sign_evidence`` would let producer-side validation prevent
    those records from ever reaching the refusal the tests need to pin.
    """

    raw = base64.b64decode(private_key.removeprefix("ed25519:"))
    payload = domain + canonical_json_bytes(body)
    return "ed25519:" + base64.b64encode(
        Ed25519PrivateKey.from_private_bytes(raw).sign(payload)
    ).decode("ascii")


def raw_signed_v4(private_key: str, body: dict[str, object]) -> dict[str, object]:
    return {
        **body,
        "signature": signed_for_domain(private_key, b"ranex-evidence-v4\n", body),
    }


def xml_case(path: str, name: str, body: str = "") -> str:
    classname = path.removesuffix(".py").replace("/", ".")
    return f'<testcase classname="{classname}" name="{name}" time="0.000">{body}</testcase>'


def junitxml(*cases: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites><testsuite name="pytest" tests="1">'
        + "".join(cases)
        + "</testsuite></testsuites>"
    ).encode("utf-8")


def write_manifest(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "suite_manifest.json"
    path.write_bytes(canonical_json_bytes(data))
    return path


def run_real_pytest_suite(
    tmp_path: Path,
    source: str,
    *,
    pytest_args: tuple[str, ...] = (),
) -> tuple[subprocess.CompletedProcess[str], bytes]:
    return run_real_pytest_tree(
        tmp_path,
        {"tests/unit/test_x.py": source},
        pytest_args=pytest_args,
    )


def run_real_pytest_tree(
    tmp_path: Path,
    sources: dict[str, str],
    *,
    pytest_args: tuple[str, ...] = (),
) -> tuple[subprocess.CompletedProcess[str], bytes]:
    root = tmp_path / f"real-{len(list(tmp_path.iterdir()))}"
    for relative, source in sources.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(textwrap.dedent(source), encoding="utf-8")
    report = root / "report.xml"

    env = dict(os.environ)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests",
            *pytest_args,
            f"--junitxml={report.name}",
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert report.is_file(), result.stdout + result.stderr
    return result, report.read_bytes()


def test_signing_moves_to_v3_and_adds_suite_results(domain) -> None:
    assert domain.signing.EVIDENCE_DOMAIN == b"ranex-evidence-v4\n"
    assert domain.signing.SIGNED_FIELDS == (
        "claim_id",
        "command",
        "command_digest",
        "executable_path",
        "exit_code",
        "producer_id",
        "subject_digest",
        "suite_results",
        "confinement_result_digest",
        "confinement_profile_digest",
    )


def test_a_v3_record_with_null_suite_results_is_admitted(domain, keypair) -> None:
    private, public = keypair
    admitted = domain.admission.admit(
        [signed(domain, private, suite_results_value=None)],
        {"worker": public},
    )

    assert admitted.rejections == ()
    assert len(admitted.evidence) == 1
    assert admitted.evidence[0].suite_results is None


def test_an_old_v2_seven_field_record_is_refused_loudly_as_malformed(
    domain,
    keypair,
) -> None:
    private, public = keypair
    old_body = {
        key: value
        for key, value in content(suite_results_value=None).items()
        if key not in {
            "suite_results",
            "confinement_result_digest",
            "confinement_profile_digest",
        }
    }
    record = {**old_body, "signature": signed_v2(private, old_body)}

    result = domain.admission.admit([record], {"worker": public})
    assert result.evidence == ()
    assert [rejection.reason for rejection in result.rejections] == [
        domain.admission.RejectionReason.MALFORMED_RECORD
    ]
    assert "suite_results" in result.rejections[0].detail


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_admission_refuses_any_content_key_set_other_than_the_eight(
    domain,
    keypair,
    mutation: str,
) -> None:
    assert "suite_results" in domain.signing.SIGNED_FIELDS
    private, public = keypair
    body = content(suite_results_value=None)
    if mutation == "missing":
        del body["executable_path"]
    else:
        body["timestamp"] = "2026-08-05T00:00:00Z"

    result = domain.admission.admit(
        [raw_signed_v4(private, body)],
        {"worker": public},
    )

    assert result.evidence == ()
    assert result.rejections[0].reason is domain.admission.RejectionReason.MALFORMED_RECORD


@pytest.mark.parametrize(
    "suite_results_value",
    [
        {
            "manifest_digest": "sha256:" + "a" * 64,
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [],
            "missing": [],
            "extra_count": 0,
        },
        {
            "manifest_digest": "sha256:" + "a" * 64,
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [],
            "missing": [],
            "extra_count": 0,
            "outcome_digest": "sha256:" + "b" * 64,
            "unexpected": True,
        },
    ],
)
def test_admission_refuses_suite_results_with_missing_or_extra_inner_keys(
    domain,
    keypair,
    suite_results_value: dict[str, object],
) -> None:
    assert "suite_results" in domain.signing.SIGNED_FIELDS
    private, public = keypair
    result = domain.admission.admit(
        [
            raw_signed_v4(
                private,
                content(suite_results_value=suite_results_value),
            )
        ],
        {"worker": public},
    )

    assert result.evidence == ()
    assert result.rejections[0].reason is domain.admission.RejectionReason.MALFORMED_RECORD


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_admission_refuses_counts_with_missing_or_extra_keys(
    domain,
    keypair,
    mutation: str,
) -> None:
    assert "suite_results" in domain.signing.SIGNED_FIELDS
    private, public = keypair
    result_value = suite_results(
        manifest(["tests/unit/test_x.py::test_pass"]),
        {"tests/unit/test_x.py::test_pass": "passed"},
    )
    counts = dict(result_value["counts"])
    if mutation == "missing":
        del counts["errors"]
    else:
        counts["warnings"] = 0
    result_value["counts"] = counts

    result = domain.admission.admit(
        [raw_signed_v4(private, content(suite_results_value=result_value))],
        {"worker": public},
    )

    assert result.evidence == ()
    assert result.rejections[0].reason is domain.admission.RejectionReason.MALFORMED_RECORD


@pytest.mark.parametrize(
    "mutation",
    [
        "non-canonical-manifest-digest",
        "boolean-count",
        "boolean-extra-count",
        "non-canonical-outcome-digest",
        "unknown-outcome-kind",
        "unsorted-non-passed",
        "unsorted-missing",
    ],
)
def test_admission_refuses_non_canonical_suite_results_content(
    domain,
    keypair,
    mutation: str,
) -> None:
    assert "suite_results" in domain.signing.SIGNED_FIELDS
    private, public = keypair
    pinned = manifest(
        ["tests/unit/test_a.py::test_a", "tests/unit/test_b.py::test_b"]
    )
    result_value = suite_results(
        pinned,
        {
            "tests/unit/test_a.py::test_a": "failed",
            "tests/unit/test_b.py::test_b": "skipped",
        },
    )
    if mutation == "non-canonical-manifest-digest":
        result_value["manifest_digest"] = "SHA256:" + "a" * 64
    elif mutation == "boolean-count":
        result_value["counts"]["passed"] = True
    elif mutation == "boolean-extra-count":
        result_value["extra_count"] = True
    elif mutation == "non-canonical-outcome-digest":
        result_value["outcome_digest"] = "sha256:not-a-digest"
    elif mutation == "unknown-outcome-kind":
        result_value["non_passed"][0][1] = "bogus"
    elif mutation == "unsorted-non-passed":
        result_value["non_passed"] = list(reversed(result_value["non_passed"]))
    else:
        result_value = suite_results(
            pinned,
            {},
            missing=list(reversed(pinned["suite"])),
        )

    result = domain.admission.admit(
        [raw_signed_v4(private, content(suite_results_value=result_value))],
        {"worker": public},
    )

    assert result.evidence == ()
    assert result.rejections[0].reason is domain.admission.RejectionReason.MALFORMED_RECORD


def test_non_canonical_suite_results_content_is_malformed_not_bad_signature(
    domain,
    keypair,
) -> None:
    assert "suite_results" in domain.signing.SIGNED_FIELDS
    _, public = keypair
    record = {
        **content(
            suite_results_value={
                "manifest_digest": "sha256:" + "a" * 64,
                "counts": {
                    "passed": float("nan"),
                    "skipped": 0,
                    "failed": 0,
                    "errors": 0,
                    "xfailed": 0,
                    "xpassed": 0,
                },
                "non_passed": [],
                "missing": [],
                "extra_count": 0,
                "outcome_digest": "sha256:" + "b" * 64,
            }
        ),
        "signature": "ed25519:" + "A" * 88,
    }

    result = domain.admission.admit([record], {"worker": public})
    assert result.evidence == ()
    assert result.rejections[0].reason is domain.admission.RejectionReason.MALFORMED_RECORD


def test_claim_accepts_the_slice009_suite_contract_fields(domain) -> None:
    pinned = manifest(
        [
            "tests/unit/test_x.py::test_pass",
            "tests/unit/test_x.py::test_skip",
        ],
        {"tests/unit/test_x.py::test_skip": "credential-gated"},
    )
    built = domain.verdict.Claim(
        claim_id="tests-executed",
        command_digest=COMMAND_DIGEST,
        results_required=True,
        manifest_digest=manifest_digest_value(pinned),
        expected_ids=tuple(pinned["suite"]),
        expected_skips=pinned["expected_skips"],
    )

    assert built.results_required is True
    assert built.manifest_digest == manifest_digest_value(pinned)
    assert built.expected_ids == tuple(pinned["suite"])
    assert built.expected_skips == pinned["expected_skips"]


def test_loader_accepts_results_artifact_only_when_the_exact_token_is_in_argv(
    domain,
    tmp_path: Path,
) -> None:
    text = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
        results_artifact: artifacts/junit.xml
"""
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")

    gate = domain.loader.load_gate(path, "landing")
    (loaded,) = gate.required_claims
    assert tuple(loaded.command) == tuple(COMMAND)
    assert loaded.results_artifact == "artifacts/junit.xml"


@pytest.mark.parametrize(
    "artifact",
    [
        "",
        "/artifacts/junit.xml",
        "../junit.xml",
        "artifacts/../junit.xml",
        None,
        1,
        ["artifacts/junit.xml"],
    ],
)
def test_loader_refuses_invalid_results_artifact_paths(
    domain,
    tmp_path: Path,
    artifact: object,
) -> None:
    assert "results_artifact" in domain.loader._CLAIM_KEYS
    text = f"""
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
        results_artifact: {json.dumps(artifact)}
"""
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="results_artifact"):
        domain.loader.load_gate(path, "landing")


@pytest.mark.parametrize(
    "command",
    [
        ["uv", "run", "pytest", "-q"],
        ["uv", "run", "pytest", "-q", "--junitxml", "artifacts/junit.xml"],
        ["uv", "run", "pytest", "-q", "--junitxml=other.xml"],
    ],
)
def test_loader_refuses_results_artifact_not_bound_as_the_exact_junitxml_token(
    domain,
    tmp_path: Path,
    command: list[str],
) -> None:
    assert "results_artifact" in domain.loader._CLAIM_KEYS
    text = f"""
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: {json.dumps(command)}
        results_artifact: "artifacts/junit.xml"
"""
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="--junitxml=artifacts/junit.xml"):
        domain.loader.load_gate(path, "landing")


def test_loader_without_results_artifact_keeps_exit_code_only_claims(
    domain,
    tmp_path: Path,
) -> None:
    text = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")

    gate = domain.loader.load_gate(path, "landing")
    (loaded,) = gate.required_claims
    assert loaded.command == ("uv", "run", "pytest", "-q")
    assert loaded.results_artifact is None


def test_loader_keeps_unknown_claim_keys_strict_after_adding_results_artifact(
    domain,
    tmp_path: Path,
) -> None:
    assert "results_artifact" in domain.loader._CLAIM_KEYS
    text = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
        results_artifact: artifacts/junit.xml
        waiver: yes
"""

    with pytest.raises(ValueError, match="unknown"):
        domain.loader.load_gate_text(text, "landing")


def test_freeze_manifest_is_outcome_blind_and_digest_is_canonical(suite_api) -> None:
    xml = junitxml(
        xml_case("tests/unit/test_x.py", "test_skip", "<skipped />"),
        xml_case("tests/unit/test_x.py", "test_pass"),
        xml_case("tests/unit/test_x.py", "test_fail", "<failure />"),
    )

    frozen = suite_api.freeze_manifest(
        xml,
        expected_skips={"tests/unit/test_x.py::test_skip": "credential-gated"},
    )

    assert frozen == {
        "suite": [
            "tests/unit/test_x.py::test_fail",
            "tests/unit/test_x.py::test_pass",
            "tests/unit/test_x.py::test_skip",
        ],
        "expected_skips": {
            "tests/unit/test_x.py::test_skip": "credential-gated",
        },
    }
    assert suite_api.manifest_digest(frozen) == manifest_digest_value(frozen)

    without_ceremony_declarations = suite_api.freeze_manifest(xml)
    assert without_ceremony_declarations["suite"] == frozen["suite"]
    assert without_ceremony_declarations["expected_skips"] == {}
    assert suite_api.freeze_manifest(xml) == without_ceremony_declarations


def test_load_manifest_accepts_only_the_exact_canonical_json_bytes(
    suite_api,
    tmp_path: Path,
) -> None:
    frozen = manifest(
        [
            "tests/unit/test_x.py::test_pass",
            "tests/unit/test_x.py::test_skip",
        ],
        {"tests/unit/test_x.py::test_skip": "credential-gated"},
    )
    canonical_path = write_manifest(tmp_path, frozen)

    assert suite_api.load_manifest(canonical_path) == frozen

    non_canonical = tmp_path / "non-canonical.json"
    non_canonical.write_text(json.dumps(frozen), encoding="utf-8")
    with pytest.raises(ValueError, match="canonical"):
        suite_api.load_manifest(non_canonical)


@pytest.mark.parametrize(
    "payload",
    [
        {"suite": ["tests/unit/test_x.py::test_pass"]},
        {
            "suite": ["tests/unit/test_x.py::test_pass"],
            "expected_skips": {},
            "note": "not part of the trust root",
        },
    ],
)
def test_load_manifest_refuses_missing_or_extra_top_level_keys(
    suite_api,
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        suite_api.load_manifest(write_manifest(tmp_path, payload))


@pytest.mark.parametrize(
    "payload",
    [
        {"suite": ["tests/unit/test_b.py::test_b", "tests/unit/test_a.py::test_a"], "expected_skips": {}},
        {"suite": ["tests/unit/test_a.py::test_a", "tests/unit/test_a.py::test_a"], "expected_skips": {}},
        {"suite": [""], "expected_skips": {}},
        {"suite": ["tests/unit/test_a.py::test_a"], "expected_skips": {"tests/unit/test_b.py::test_b": "not present"}},
    ],
)
def test_load_manifest_refuses_unsorted_duplicate_empty_and_out_of_suite_ids(
    suite_api,
    tmp_path: Path,
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        suite_api.load_manifest(write_manifest(tmp_path, payload))


def test_suite_results_from_junitxml_summarises_missing_extra_and_outcomes(
    suite_api,
) -> None:
    pinned = manifest(
        [
            "tests/unit/test_x.py::test_fail",
            "tests/unit/test_x.py::test_missing",
            "tests/unit/test_x.py::test_pass",
            "tests/unit/test_x.py::test_skip",
        ]
    )
    xml = junitxml(
        xml_case("tests/unit/test_x.py", "test_pass"),
        xml_case("tests/unit/test_x.py", "test_skip", "<skipped />"),
        xml_case("tests/unit/test_x.py", "test_fail", "<failure />"),
        xml_case("tests/unit/test_x.py", "test_extra"),
    )

    assert suite_api.suite_results_from_junitxml(xml, pinned) == suite_results(
        pinned,
        {
            "tests/unit/test_x.py::test_extra": "passed",
            "tests/unit/test_x.py::test_fail": "failed",
            "tests/unit/test_x.py::test_pass": "passed",
            "tests/unit/test_x.py::test_skip": "skipped",
        },
        missing=["tests/unit/test_x.py::test_missing"],
        extra_count=1,
    )


def test_parse_results_artifact_refuses_an_absent_file(
    suite_api,
    tmp_path: Path,
) -> None:
    with pytest.raises((FileNotFoundError, ValueError)):
        suite_api.parse_results_artifact(
            tmp_path / "missing.xml",
            manifest(["tests/unit/test_x.py::test_pass"]),
        )


def test_suite_results_from_junitxml_refuses_unparseable_xml(suite_api) -> None:
    with pytest.raises(ValueError):
        suite_api.suite_results_from_junitxml(
            b"<testsuite><broken",
            manifest(["tests/unit/test_x.py::test_pass"]),
        )


def test_suite_results_from_junitxml_refuses_duplicate_test_ids(suite_api) -> None:
    xml = junitxml(
        xml_case("tests/unit/test_x.py", "test_same"),
        xml_case("tests/unit/test_x.py", "test_same"),
    )

    with pytest.raises(ValueError, match="duplicate"):
        suite_api.suite_results_from_junitxml(
            xml,
            manifest(["tests/unit/test_x.py::test_same"]),
        )


def test_suite_results_from_junitxml_refuses_multiple_outcome_children(suite_api) -> None:
    xml = junitxml(
        xml_case(
            "tests/unit/test_x.py",
            "test_bad",
            "<skipped /><failure />",
        )
    )

    with pytest.raises(ValueError, match="outcome"):
        suite_api.suite_results_from_junitxml(
            xml,
            manifest(["tests/unit/test_x.py::test_bad"]),
        )


def test_real_deselection_and_a_deleted_test_file_are_both_missing(
    domain,
    suite_api,
    tmp_path: Path,
) -> None:
    sources = {
        "tests/unit/test_keep.py": """
            def test_keep():
                assert True
        """,
        "tests/unit/test_removed.py": """
            def test_removed():
                assert True
        """,
    }
    first_run, first_xml = run_real_pytest_tree(tmp_path, sources)
    assert first_run.returncode == 0
    frozen = suite_api.freeze_manifest(first_xml)
    missing_id = "tests/unit/test_removed.py::test_removed"
    expected = claim(
        domain,
        manifest_digest=suite_api.manifest_digest(frozen),
        expected_ids=tuple(frozen["suite"]),
        expected_skips=frozen["expected_skips"],
    )

    deselected_run, deselected_xml = run_real_pytest_tree(
        tmp_path,
        sources,
        pytest_args=("-k", "test_keep"),
    )
    deleted_run, deleted_xml = run_real_pytest_tree(
        tmp_path,
        {"tests/unit/test_keep.py": sources["tests/unit/test_keep.py"]},
    )
    assert deselected_run.returncode == 0
    assert deleted_run.returncode == 0

    for artifact in (deselected_xml, deleted_xml):
        parsed = suite_api.suite_results_from_junitxml(artifact, frozen)
        assert parsed["missing"] == [missing_id]
        assert evidence(
            domain,
            suite_results_value=parsed,
            exit_code=0,
        ).satisfies(expected, SUBJECT) is False


def test_this_repository_binds_its_catalog_to_the_canonical_suite_manifest(
    domain,
    suite_api,
) -> None:
    frozen = suite_api.load_manifest(REPO_ROOT / "governance" / "suite_manifest.json")
    gate = domain.loader.load_gate(REPO_ROOT / "governance" / "gates.yaml", "landing")
    loaded = next(
        claim for claim in gate.required_claims if claim.claim_id == "tests-executed"
    )

    assert loaded.results_artifact
    assert f"--junitxml={loaded.results_artifact}" in loaded.command
    assert loaded.command_digest == command_digest(loaded.command)
    assert frozen["suite"] == sorted(frozen["suite"])
    assert frozen["suite"]


def test_exit_code_only_claims_keep_todays_semantics(domain) -> None:
    plain = domain.verdict.Claim(
        claim_id="tests-executed",
        command_digest=command_digest(["uv", "run", "pytest", "-q"]),
        results_required=False,
        manifest_digest=None,
        expected_ids=None,
        expected_skips=None,
    )
    observed = domain.verdict.Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command="uv run pytest -q",
        command_digest=command_digest(["uv", "run", "pytest", "-q"]),
        executable_path=EXECUTABLE,
        exit_code=0,
        suite_results=None,
    )

    assert observed.satisfies(plain, SUBJECT) is True


def test_results_required_claim_requires_a_matching_manifest_digest(domain) -> None:
    pinned = manifest(["tests/unit/test_x.py::test_pass"])
    observed = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {"tests/unit/test_x.py::test_pass": "passed"},
        ),
    )

    assert observed.satisfies(
        claim(domain, manifest_digest="sha256:" + "f" * 64),
        SUBJECT,
    ) is False


def test_results_required_blocks_a_nonzero_exit_or_absent_suite_results(domain) -> None:
    pinned = manifest(["tests/unit/test_x.py::test_pass"])
    expected = claim(
        domain,
        manifest_digest=manifest_digest_value(pinned),
        expected_ids=tuple(pinned["suite"]),
        expected_skips={},
    )
    valid = suite_results(
        pinned,
        {"tests/unit/test_x.py::test_pass": "passed"},
    )

    assert evidence(
        domain,
        suite_results_value=valid,
        exit_code=1,
    ).satisfies(expected, SUBJECT) is False
    assert evidence(
        domain,
        suite_results_value=None,
        exit_code=0,
    ).satisfies(expected, SUBJECT) is False


def test_declared_expected_skip_may_skip_or_pass(domain) -> None:
    pinned = manifest(
        ["tests/unit/test_x.py::test_skip"],
        {"tests/unit/test_x.py::test_skip": "credential-gated"},
    )
    skipped = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {"tests/unit/test_x.py::test_skip": "skipped"},
        ),
    )
    passed = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {"tests/unit/test_x.py::test_skip": "passed"},
        ),
    )
    expected = claim(
        domain,
        manifest_digest=manifest_digest_value(pinned),
        expected_ids=tuple(pinned["suite"]),
        expected_skips=pinned["expected_skips"],
    )

    assert skipped.satisfies(expected, SUBJECT) is True
    assert passed.satisfies(expected, SUBJECT) is True


@pytest.mark.parametrize("kind", ["failed", "error", "xfailed", "xpassed"])
def test_failed_error_xfail_and_xpass_block_even_if_declared(
    domain,
    kind: str,
) -> None:
    pinned = manifest(
        ["tests/unit/test_x.py::test_bad"],
        {"tests/unit/test_x.py::test_bad": "declared-but-not-allowed"},
    )
    observed = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {"tests/unit/test_x.py::test_bad": kind},
        ),
    )

    assert observed.satisfies(
        claim(
            domain,
            manifest_digest=manifest_digest_value(pinned),
            expected_ids=tuple(pinned["suite"]),
            expected_skips=pinned["expected_skips"],
        ),
        SUBJECT,
    ) is False


def test_undeclared_skip_and_missing_id_block_but_extra_ids_do_not(domain) -> None:
    pinned = manifest(["tests/unit/test_x.py::test_a", "tests/unit/test_x.py::test_b"])
    skipped = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {
                "tests/unit/test_x.py::test_a": "skipped",
                "tests/unit/test_x.py::test_extra": "passed",
            },
            missing=["tests/unit/test_x.py::test_b"],
            extra_count=1,
        ),
    )
    only_extra = evidence(
        domain,
        suite_results_value=suite_results(
            manifest(["tests/unit/test_x.py::test_a"]),
            {
                "tests/unit/test_x.py::test_a": "passed",
                "tests/unit/test_x.py::test_extra": "passed",
            },
            extra_count=1,
        ),
    )

    assert skipped.satisfies(
        claim(
            domain,
            manifest_digest=manifest_digest_value(pinned),
            expected_ids=tuple(pinned["suite"]),
            expected_skips={},
        ),
        SUBJECT,
    ) is False
    assert only_extra.satisfies(
        claim(
            domain,
            manifest_digest=manifest_digest_value(manifest(["tests/unit/test_x.py::test_a"])),
            expected_ids=("tests/unit/test_x.py::test_a",),
            expected_skips={},
        ),
        SUBJECT,
    ) is True


def test_diagnosis_names_the_offending_ids_and_kinds_not_generic_absence(domain) -> None:
    pinned = manifest(["tests/unit/test_x.py::test_skip"])
    gate = domain.verdict.Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(
            claim(
                domain,
                manifest_digest=manifest_digest_value(pinned),
                expected_ids=tuple(pinned["suite"]),
                expected_skips={},
            ),
        ),
        blocking=True,
    )

    result = domain.verdict.evaluate(
        gate,
        (
            evidence(
                domain,
                suite_results_value=suite_results(
                    pinned,
                    {"tests/unit/test_x.py::test_skip": "skipped"},
                ),
            ),
        ),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert result.verdict is domain.verdict.Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
    assert result.reason is not None
    assert "tests/unit/test_x.py::test_skip" in result.reason
    assert "skipped" in result.reason
    assert "no evidence for required claim" not in result.reason


def test_diagnosis_names_a_missing_test_id_distinctly_from_generic_absence(domain) -> None:
    missing_id = "tests/unit/test_x.py::test_missing"
    pinned = manifest(["tests/unit/test_x.py::test_pass", missing_id])
    gate = domain.verdict.Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(
            claim(
                domain,
                manifest_digest=manifest_digest_value(pinned),
                expected_ids=tuple(pinned["suite"]),
                expected_skips={},
            ),
        ),
        blocking=True,
    )
    observed = evidence(
        domain,
        suite_results_value=suite_results(
            pinned,
            {"tests/unit/test_x.py::test_pass": "passed"},
            missing=[missing_id],
        ),
    )

    result = domain.verdict.evaluate(
        gate,
        (observed,),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert result.verdict is domain.verdict.Verdict.FAIL
    assert result.reason is not None
    assert missing_id in result.reason
    assert "missing" in result.reason.lower()
    assert "no evidence for required claim" not in result.reason


def test_real_pytest_artifact_freezes_and_judges_through_one_parser(
    domain,
    suite_api,
    tmp_path: Path,
) -> None:
    source = """
    import pytest
    import unittest

    @pytest.fixture
    def broken_fixture():
        raise RuntimeError("setup boom")

    def test_pass():
        assert True

    @unittest.skip("later")
    def test_skip():
        assert False

    @getattr(pytest.mark, "x" + "fail")(reason="known")
    def test_xfail():
        assert False

    @getattr(pytest.mark, "x" + "fail")(reason="bug", strict=True)
    def test_xpass():
        assert True

    def test_fail():
        assert False

    def test_error(broken_fixture):
        pass
    """
    first_run, first_xml = run_real_pytest_suite(tmp_path, source)
    assert first_run.returncode == 1

    frozen = suite_api.freeze_manifest(
        first_xml,
        expected_skips={"tests/unit/test_x.py::test_skip": "credential-gated"},
    )
    parsed = suite_api.suite_results_from_junitxml(first_xml, frozen)
    outcomes = {
        "tests/unit/test_x.py::test_error": "error",
        "tests/unit/test_x.py::test_fail": "failed",
        "tests/unit/test_x.py::test_pass": "passed",
        "tests/unit/test_x.py::test_skip": "skipped",
        "tests/unit/test_x.py::test_xfail": "xfailed",
        "tests/unit/test_x.py::test_xpass": "xpassed",
    }
    assert parsed == suite_results(frozen, outcomes)

    green_source = """
    import unittest

    def test_pass():
        assert True

    @unittest.skip("later")
    def test_skip():
        assert False

    def test_xfail():
        assert True

    def test_xpass():
        assert True

    def test_fail():
        assert True

    def test_error():
        assert True
    """
    second_run, second_xml = run_real_pytest_suite(tmp_path, green_source)
    assert second_run.returncode == 0
    judged = domain.verdict.evaluate(
        domain.verdict.Gate(
            gate_id="landing",
            rule_id="TESTS_EXECUTED",
            required_claims=(
                claim(
                    domain,
                    manifest_digest=suite_api.manifest_digest(frozen),
                    expected_ids=tuple(frozen["suite"]),
                    expected_skips=frozen["expected_skips"],
                ),
            ),
            blocking=True,
        ),
        (
            evidence(
                domain,
                suite_results_value=suite_api.suite_results_from_junitxml(
                    second_xml,
                    frozen,
                ),
                exit_code=second_run.returncode,
            ),
        ),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert judged.verdict is domain.verdict.Verdict.PASS
    assert judged.reason is None
