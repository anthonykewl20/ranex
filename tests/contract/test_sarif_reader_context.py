"""Optional SARIF readers cannot substitute a different subject's cached bytes."""
from pathlib import Path

import pytest

from ranex.foundation.delegated_review import (
    build_packet,
    empty_handbook_digest,
    packet_bytes,
    packet_digest,
    rederive_findings,
    resolve_anchor,
    validated_review_findings,
)
from ranex.foundation.scan_results import _findings, _materialised_packet_digest, _region_bytes
from ranex.foundation.subject_reader import SubjectReader

ENDPOINTS = ['region','findings','packet','anchor','rederived','validated-review']


def _subject(root, name):
    root.mkdir()
    (root/'mod.py').write_text(f'{name} = 1\n')
    (root/'child').mkdir()
    packet = build_packet(subject_digest='sha256:'+('a' if name=='first' else 'b')*64,
                          range_base='c'*40,range_head='d'*40,
                          handbook_digest=empty_handbook_digest(),chapters=[])
    (root/'governance').mkdir()
    (root/'governance/review-packet.json').write_bytes(packet_bytes(packet))
    return packet_digest(packet)


def _invoke(endpoint, root, reader, excerpt, digest):
    document = {'version':'2.1.0','runs':[{'tool':{'driver':{'name':'context-contract'}},
                'properties':{'packet_digest':digest},
                'artifacts':[{'location':{'uri':'mod.py'}}],
                'results':[{'ruleId':'review','level':'error','message':{'text':'finding'},
                            'locations':[{'physicalLocation':{'artifactLocation':{'uri':'mod.py'},
                                          'region':{'startLine':1,'endLine':1,
                                                    'snippet':{'text':excerpt}}}}]}]}]}
    if endpoint=='region':
        return _region_bytes(root,'mod.py',1,1,None,reader=reader)
    if endpoint=='findings':
        return _findings(document,root,reader=reader)
    if endpoint=='packet':
        return _materialised_packet_digest(root,reader=reader)
    if endpoint=='anchor':
        return resolve_anchor(root,'mod.py',excerpt,reader=reader)
    if endpoint=='rederived':
        return rederive_findings(document,root,reader=reader)
    return validated_review_findings(document,root,digest,reader=reader)


@pytest.mark.parametrize('endpoint',ENDPOINTS)
def test_optional_reader_refuses_other_subject_context(tmp_path, endpoint):
    first,second=tmp_path/'first',tmp_path/'second'
    _subject(first,'first')
    digest=_subject(second,'second')
    reader=SubjectReader(second)
    reader.read('mod.py')  # Already trusted bytes, but for the other subject.
    with pytest.raises(ValueError,match='subject.*context'):
        _invoke(endpoint,first,reader,'second = 1',digest)


@pytest.mark.parametrize('endpoint',ENDPOINTS)
def test_optional_reader_accepts_same_normalized_absolute_context(tmp_path, endpoint):
    root=tmp_path/'subject'
    digest=_subject(root,'first')
    reader=SubjectReader(root/'child'/'..')
    assert _invoke(endpoint,root,reader,'first = 1',digest)==_invoke(endpoint,root,None,'first = 1',digest)


def test_reader_keeps_creation_context_when_cwd_changes(tmp_path, monkeypatch):
    first,second=tmp_path/'first',tmp_path/'second'
    _subject(first,'first')
    _subject(second,'second')
    monkeypatch.chdir(tmp_path)
    reader=SubjectReader(Path('first'))
    monkeypatch.chdir(second)
    assert reader.read('mod.py')==b'first = 1\n'
    assert resolve_anchor(first,'mod.py','first = 1',reader=reader)==(1,1)
    with pytest.raises(ValueError,match='subject.*context'):
        resolve_anchor(Path('first'),'mod.py','first = 1',reader=reader)
