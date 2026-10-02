"""Opt-in settings binding stays outside the verdict kernel."""
from dataclasses import replace

import pytest

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.cli.acceptance_task import live_acceptance_gate
from ranex.foundation.canonical import command_digest
from ranex.foundation.settings import settings_schema_version
from ranex.foundation.signing import (
    ENVELOPE_TYPE,
    ENVELOPE_TYPE_V2,
    generate_keypair,
    sign_evidence,
)
from ranex.governed_execution.domain.admission import (
    Admission,
    RejectionReason,
    admit,
    apply_settings_binding,
)
from ranex.governed_execution.domain.verdict import Evidence, Verdict
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate_text

CATALOG = '''gates:
  - gate_id: binding
    rule_id: observed
    required_claims:
      - claim_id: check
        command: [true]
'''.replace('[true]', '["true"]')
SUBJECT = 'sha256:' + 'a' * 64
DIGEST = 'sha256:' + 'b' * 64


def evidence():
    return Evidence('check', SUBJECT, 'worker', 'true', command_digest(['true']), '/bin/true', 0)


@pytest.mark.parametrize('flag', [True, False])
def test_catalog_boolean(flag):
    catalog = CATALOG + f'    requires_settings_binding: {str(flag).lower()}\n'
    assert load_gate_text(catalog, 'binding').requires_settings_binding is flag
    assert load_gate_text(CATALOG, 'binding').requires_settings_binding is False


@pytest.mark.parametrize('flag', ['1', 'null', '"true"', '[]'])
def test_catalog_wrong_type(flag):
    with pytest.raises(ValueError, match='requires_settings_binding.*boolean'):
        load_gate_text(CATALOG + f'    requires_settings_binding: {flag}\n', 'binding')


@pytest.mark.parametrize('changes,kept', [
    ({'envelope_type': ENVELOPE_TYPE}, False),
    ({'settings_digest': SUBJECT}, False),
    ({'settings_schema_version': settings_schema_version + 1}, False),
    ({'settings_schema_version': True}, False),
    ({}, True),
])
def test_binding_filter(changes, kept):
    record = {'envelope_type': ENVELOPE_TYPE_V2, 'settings_digest': DIGEST,
              'settings_schema_version': settings_schema_version, **changes}
    original = Admission((evidence(),), (), (0,))
    result = apply_settings_binding(original, [record], expected_digest=DIGEST,
                                    expected_schema_version=settings_schema_version)
    assert bool(result.evidence) is kept
    assert result.evidence_indices == ((0,) if kept else ())
    if not kept:
        assert result.rejections[0].reason == RejectionReason.SETTINGS_BINDING_MISMATCH
        assert result.rejections[0].index == 0
        assert 'record 0' in result.rejections[0].detail
    assert original.evidence_indices == (0,)


def test_partial_and_malformed_records():
    records = [None, {'envelope_type': ENVELOPE_TYPE_V2, 'settings_digest': DIGEST,
                      'settings_schema_version': settings_schema_version}, []]
    original = Admission((evidence(), evidence(), evidence()), (), (2, 1, 0), history_verified=True)
    result = apply_settings_binding(original, records, expected_digest=DIGEST,
                                    expected_schema_version=settings_schema_version)
    assert result.evidence == (evidence(),)
    assert result.evidence_indices == (1,)
    assert [item.index for item in result.rejections] == [2, 0]
    assert result.history_verified
    missing = apply_settings_binding(replace(original, evidence=(evidence(),), evidence_indices=(9,)),
                                     records, expected_digest=DIGEST,
                                     expected_schema_version=settings_schema_version)
    assert missing.rejections[0].index == 9


def test_evaluator_refuses_bypass_and_journals_absence(tmp_path):
    catalog = CATALOG + '    requires_settings_binding: true\n'
    journal = tmp_path / 'journal.sqlite3'
    evaluator = build_gate_evaluator(catalog.encode(), journal)
    for method in (evaluator.evaluate, evaluator.evaluate_anchored):
        with pytest.raises(ValueError, match='binding.*settings binding requires the CLI admission path'):
            method('binding', (), subject_digest=SUBJECT, approver_id='approver')
    assert not journal.exists()
    result, head = evaluator.evaluate_anchored('binding', (), subject_digest=SUBJECT,
                                             approver_id='approver', settings_binding_verified=True)
    assert result.verdict == Verdict.FAIL
    assert result.missing_claims == ('check',)
    assert head and journal.exists()
    assert evaluator.evaluate('binding', (evidence(),), subject_digest=SUBJECT,
                              approver_id='approver', settings_binding_verified=True).verdict == Verdict.PASS


def test_nonbinding_evaluator_unchanged():
    evaluator = build_gate_evaluator(CATALOG.encode())
    assert evaluator.evaluate('binding', (evidence(),), subject_digest=SUBJECT,
                              approver_id='approver').verdict == Verdict.PASS


@pytest.mark.parametrize('unknown', [False, True])
def test_admission_version_dispatch_nonbinding(unknown):
    private, public = generate_keypair()
    record = dict(claim_id='check', subject_digest=SUBJECT, producer_id='worker',
                  command='true', command_digest=command_digest(['true']),
                  executable_path='/bin/true', exit_code=0, suite_results=None,
                  confinement_result_digest=DIGEST, confinement_profile_digest=DIGEST,
                  envelope_type=ENVELOPE_TYPE_V2, gate_id='binding', catalog_digest=DIGEST,
                  settings_digest=DIGEST, settings_schema_version=settings_schema_version)
    record['signature'] = sign_evidence(record, private)
    if unknown:
        record['envelope_type'] = 'unknown'
    result = admit([record], {'worker': public})
    if unknown:
        assert result.rejections[0].reason == RejectionReason.MALFORMED_RECORD
    else:
        assert len(result.evidence) == 1
        assert not result.rejections


def test_live_acceptance_pin():
    assert live_acceptance_gate(DIGEST).gate_id == 'live-acceptance'
    with pytest.raises(ValueError, match='E-TASK-SETTINGS-BINDING.*#236'):
        live_acceptance_gate(DIGEST, requires_settings_binding=True)
