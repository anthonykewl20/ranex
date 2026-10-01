"""A reducer invocation reads each bounded subject once, with no cross-run state."""
import copy
import json
import os

import pytest

from ranex.foundation.antislop import antislop_sarif_bytes
from ranex.foundation.antislop_results import (
    antislop_results_from_sarif,
    freeze_antislop_expectations,
)
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.delegated_review import (
    build_packet,
    empty_handbook_digest,
    packet_bytes,
    packet_digest,
)
from ranex.foundation.scan_results import observed_findings, scan_results_from_sarif


def _case(root, family):
    root.mkdir()
    body = ''.join(f'def test_{i:03d}():\n    assert operation() == {i}\n' for i in range(100)).encode()
    remaining = 1024 * 1024 - len(body)
    raw = body + b'#' + b'x' * (remaining - 2) + b'\n'
    compile(raw, 'test_mod.py', 'exec')
    file = root / 'test_mod.py'
    file.write_bytes(raw)
    anti = antislop_sarif_bytes(root)
    if family == 'antislop':
        return json.loads(anti), freeze_antislop_expectations(anti, subject_root=root), file
    packet = build_packet(subject_digest='sha256:'+'a'*64, range_base='b'*40, range_head='c'*40,
                          handbook_digest=empty_handbook_digest(), chapters=[])
    (root / 'governance').mkdir()
    (root / 'governance/review-packet.json').write_bytes(packet_bytes(packet))
    results = []
    for i in range(100):
        results.append({'ruleId':'review','level':'error','message':{'text':'real bounded finding'},
                        'locations':[{'physicalLocation':{'artifactLocation':{'uri':'test_mod.py'},
                                     'region':{'startLine':i*2+2,'endLine':i*2+2,
                                               'snippet':{'text':f'    assert operation() == {i}'}}}}]})
    run = {'tool':{'driver':{'name':'cache-contract'}},'artifacts':[{'location':{'uri':'test_mod.py'}}],
           'results':results}
    if family == 'review':
        run['properties'] = {'packet_digest':packet_digest(packet)}
    return {'version':'2.1.0','runs':[run]}, {'scope':['test_mod.py'],'rules':['review'],
            'blocking_levels':['error'],'accepted':{}}, file


def _consume(root, family, freeze, document, manifest):
    raw = canonical_json_bytes(document)
    if family == 'antislop':
        return (freeze_antislop_expectations(raw, subject_root=root) if freeze else
                antislop_results_from_sarif(raw, manifest, subject_root=root))
    return (observed_findings(raw, root, require_review=family=='review') if freeze else
            scan_results_from_sarif(raw, manifest, subject_root=root, require_review=family=='review'))


@pytest.mark.parametrize('family', ['generic','review','antislop'])
@pytest.mark.parametrize('freeze', [False,True])
def test_one_subject_content_read_per_parse(tmp_path, monkeypatch, family, freeze):
    root = tmp_path / 'subject'
    document, manifest, file = _case(root, family)
    baseline = _consume(root, family, freeze, document, manifest)
    identity = (file.stat().st_dev,file.stat().st_ino)
    actual_read = os.read
    reads = []
    anchors = []
    if family == 'review':
        from ranex.foundation import delegated_review
        actual_resolve = delegated_review.resolve_anchor

        def counted_anchor(*args,**kwargs):
            anchors.append(args[2])
            return actual_resolve(*args,**kwargs)

        monkeypatch.setattr(delegated_review,'resolve_anchor',counted_anchor)

    def counted(fd, limit):
        info = os.fstat(fd)
        result = actual_read(fd,limit)
        if (info.st_dev,info.st_ino) == identity:
            reads.append(len(result))
        return result

    monkeypatch.setattr(os,'read',counted)
    assert _consume(root,family,freeze,copy.deepcopy(document),manifest) == baseline
    if family == 'review':
        assert len(anchors) == 100  # Identity and rewrite share the same resolved anchor.
    assert sum(reads) == 1024*1024
    assert len(reads) == 2  # One 1MiB chunk plus EOF, regardless of the 100 findings.


@pytest.mark.parametrize('family', ['generic','review','antislop'])
def test_new_invocation_rechecks_changed_subject(tmp_path, family):
    root = tmp_path / 'subject'
    document, manifest, file = _case(root,family)
    _consume(root,family,False,document,manifest)
    file.write_bytes(b'# reported regions have been removed\n')
    with pytest.raises(ValueError):
        _consume(root,family,False,document,manifest)


@pytest.mark.parametrize('family', ['generic','review','antislop'])
@pytest.mark.parametrize('freeze', [False,True])
def test_bypassing_cache_preserves_canonical_output(tmp_path, monkeypatch, family, freeze):
    from ranex.foundation import antislop_results, delegated_review, scan_results
    from ranex.foundation.subject_reader import SubjectReader
    root = tmp_path/'subject'
    document,manifest,_ = _case(root,family)
    expected = _consume(root,family,freeze,document,manifest)

    def disabled(subject_root):
        return SubjectReader(subject_root,max_cache_bytes=0)

    for module in [scan_results,antislop_results,delegated_review]:
        monkeypatch.setattr(module,'SubjectReader',disabled)
    assert _consume(root,family,freeze,document,manifest) == expected
