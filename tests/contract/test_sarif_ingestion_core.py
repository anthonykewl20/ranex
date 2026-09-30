"""Malformed interpreted SARIF structure refuses in every consumer and freeze."""
import json

import pytest

from ranex.foundation.antislop import antislop_sarif_bytes
from ranex.foundation.antislop_results import (
    antislop_results_from_sarif,
    freeze_antislop_expectations,
)
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.delegated_review import (
    build_packet,
    emit_worker_sarif,
    empty_handbook_digest,
    packet_bytes,
)
from ranex.foundation.scan_results import observed_findings, scan_results_from_sarif


@pytest.mark.parametrize('family', ['generic', 'review', 'antislop'])
@pytest.mark.parametrize('freeze', [False, True])
@pytest.mark.parametrize('mutation', [
    'tool', 'driver', 'name', 'name-type', 'rules-type', 'rule-type', 'rule-id',
    'configuration-type', 'level', 'level-type', 'rules-null', 'invocations-null', 'message', 'message-type',
    'message-markdown-only', 'duplicate-rule-id', 'duplicate-rule-id-conflicting-level',
])
def test_malformed_core_refuses_across_actual_artifacts(tmp_path, family, freeze, mutation):
    (tmp_path / 'test_mod.py').write_text('def test_value():\n    assert operation() == 2\n')
    raw = antislop_sarif_bytes(tmp_path)
    manifest = freeze_antislop_expectations(raw, subject_root=tmp_path)
    if family == 'review':
        (tmp_path / 'governance').mkdir()
        packet = build_packet(subject_digest='sha256:'+'a'*64, range_base='b'*40,
                              range_head='c'*40, handbook_digest=empty_handbook_digest(), chapters=[])
        (tmp_path / 'governance/review-packet.json').write_bytes(packet_bytes(packet))
        raw = emit_worker_sarif(root=tmp_path, path='test_mod.py', category='review',
                               excerpt='    assert operation() == 2', level='error')
    document = json.loads(raw)
    run = document['runs'][0]
    driver = run['tool']['driver']
    if mutation == 'tool':
        run.pop('tool')
    elif mutation == 'driver':
        run['tool'].pop('driver')
    elif mutation == 'name':
        driver.pop('name')
    elif mutation == 'name-type':
        driver['name'] = 42
    elif mutation == 'rules-type':
        driver['rules'] = {}
    elif mutation == 'rules-null':
        driver['rules'] = None
    elif mutation == 'rule-type':
        driver['rules'] = [None]
    elif mutation == 'rule-id':
        driver['rules'][0].pop('id')
    elif mutation == 'configuration-type':
        driver['rules'][0]['defaultConfiguration'] = [{'level': 'error'}]
    elif mutation == 'level':
        driver['rules'][0]['defaultConfiguration'] = {'level': 'fatal'}
    elif mutation == 'level-type':
        driver['rules'][0]['defaultConfiguration'] = {'level': []}
    elif mutation in {'duplicate-rule-id', 'duplicate-rule-id-conflicting-level'}:
        duplicate = dict(driver['rules'][0])
        if mutation == 'duplicate-rule-id-conflicting-level':
            driver['rules'][0]['defaultConfiguration'] = {'level': 'error'}
            duplicate['defaultConfiguration'] = {'level': 'none'}
        driver['rules'].append(duplicate)
    elif mutation == 'invocations-null':
        run['invocations'] = None
    elif mutation == 'message':
        run['results'][0].pop('message')
    elif mutation == 'message-type':
        run['results'][0]['message'] = 42
    else:
        run['results'][0]['message'] = {'markdown': '**error**'}
    malformed = canonical_json_bytes(document)
    with pytest.raises(ValueError):
        if family == 'antislop':
            if freeze:
                freeze_antislop_expectations(malformed, subject_root=tmp_path)
            else:
                antislop_results_from_sarif(malformed, manifest, subject_root=tmp_path)
        elif freeze:
            observed_findings(malformed, tmp_path, require_review=family == 'review')
        else:
            scan_results_from_sarif(malformed, {
                'scope': ['test_mod.py'], 'rules': ['review'], 'accepted': {},
                'blocking_levels': ['error'],
            }, subject_root=tmp_path, require_review=family == 'review')


@pytest.mark.parametrize('message', [
    {'text': ''}, {'text': 'plain', 'markdown': '**plain**'},
    {'id': 'danger', 'markdown': '**danger**', 'arguments': ['arg']},
])
def test_valid_message_forms_and_properties_extensions_preserve_severity(tmp_path, message):
    (tmp_path / 'mod.py').write_text('danger = True\n')
    raw = canonical_json_bytes({'version': '2.1.0', 'properties': {'custom': 1}, 'runs': [{
        'properties': {'custom': {'anything': True}},
        'tool': {'driver': {'name': 'worker', 'globalMessageStrings': {'danger': {'text': 'danger'}},
                            'rules': [{'id': 'security', 'defaultConfiguration': {'level': 'error'}}]}},
        'results': [{'ruleId': 'security', 'message': message,
                     'locations': [{'physicalLocation': {'artifactLocation': {'uri': 'mod.py'},
                                                         'region': {'startLine': 1}}}]}],
    }]})
    summary = scan_results_from_sarif(raw, {
        'scope': ['mod.py'], 'rules': ['security'], 'accepted': {}, 'blocking_levels': ['error'],
    }, subject_root=tmp_path)
    assert summary['counts']['failed'] == 2


@pytest.mark.parametrize('family,legacy_digest', [
    ('generic', 'sha256:c94d376a7184b1d8427310b4f8c582caf2b4bef1139dda818120aab4814decc3'),
    ('review', 'sha256:d5a9eee128e46c131eff2fa0f35376375011a0fb2b1085e6d2eab38cf4ace614'),
    ('antislop', 'sha256:cc81edbf605f24849664da356c46f6b15a690b0b7d984609d75394370469bcf1'),
])
def test_pre_unique_rule_validation_summary_cannot_satisfy_current_claim(family, legacy_digest):
    """Retained clean summaries from the ambiguous-rule profile must be rerun."""
    from ranex.foundation.antislop_results import (
        antislop_expectations_digest,
        antislop_expected_ids,
    )
    from ranex.foundation.scan_results import scan_expected_ids, scan_manifest_digest
    from ranex.governed_execution.domain.verdict import Claim, Evidence, Gate, evaluate

    if family == 'antislop':
        manifest = {'scope': ['mod.py'], 'tests': {'mod.py::test_value': 1}}
        digest = antislop_expectations_digest(manifest)
        expected = antislop_expected_ids(manifest)
    else:
        manifest = {'scope': ['mod.py'], 'rules': ['security'],
                    'blocking_levels': ['error'], 'accepted': {}}
        digest = scan_manifest_digest(manifest, require_review=family == 'review')
        expected = scan_expected_ids(manifest)
    summary = {'manifest_digest': legacy_digest,
               'counts': {'passed': len(expected), 'skipped': 0, 'failed': 0,
                          'errors': 0, 'xfailed': 0, 'xpassed': 0},
               'non_passed': [], 'missing': [], 'extra_count': 0,
               'outcome_digest': 'sha256:' + 'c' * 64}
    command, subject = 'sha256:' + 'b' * 64, 'sha256:' + 'a' * 64
    claim = Claim('scan', command, True, digest, expected, {})
    evidence = Evidence('scan', subject, 'producer', 'scanner', command, '/scanner', 0, summary)
    assert evaluate(Gate('g', 'r', (claim,), True), (evidence,),
                    subject_digest=subject, approver_id='owner').verdict == 'FAIL'
