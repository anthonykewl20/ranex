"""SARIF interpretation reads bounded regular files inside the selected subject."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ranex
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
from ranex.foundation.suite_results import MAX_RESULTS_BYTES, read_results_artifact


def _setup(root, family, target):
    root.mkdir()
    (root / 'test_mod.py').write_text('def test_value():\n    assert operation() == 2\n')
    raw = antislop_sarif_bytes(root)
    if family == 'antislop':
        manifest = freeze_antislop_expectations(raw, subject_root=root)
    else:
        (root / 'governance').mkdir()
        packet = build_packet(subject_digest='sha256:' + 'a' * 64, range_base='b' * 40,
                              range_head='c' * 40, handbook_digest=empty_handbook_digest(), chapters=[])
        (root / 'governance/review-packet.json').write_bytes(packet_bytes(packet))
        raw = emit_worker_sarif(root=root, path='test_mod.py', category='review',
                               excerpt='    assert operation() == 2', level='error')
        manifest = {'scope': ['test_mod.py'], 'rules': ['review'],
                    'blocking_levels': ['error'], 'accepted': {}}
    document = json.loads(raw)
    if family == 'generic':
        document['runs'][0].pop('properties')
    document['runs'][0]['artifacts'] = [{'location': {'uri': 'test_mod.py'}}]
    if target == 'packet':
        victim = root / 'governance/review-packet.json'
    elif target == 'coverage':
        victim = root / 'covered/mod.py'
        victim.parent.mkdir()
        victim.write_text('covered = True\n')
        document['runs'][0]['artifacts'].append({'location': {'uri': 'covered/mod.py'}})
        manifest['scope'] = ['covered/mod.py', 'test_mod.py']
    else:
        # Nest the finding path so both leaf and parent symlinks are exercised.
        victim = root / 'subject/test_mod.py'
        victim.parent.mkdir()
        (root / 'test_mod.py').rename(victim)
        for result in document['runs'][0]['results']:
            result['locations'][0]['physicalLocation']['artifactLocation']['uri'] = 'subject/test_mod.py'
        document['runs'][0]['artifacts'] = [{'location': {'uri': 'subject/test_mod.py'}}]
        manifest['scope'] = ['subject/test_mod.py']
        if family == 'antislop':
            manifest['tests'] = {'subject/' + key: count for key, count in manifest['tests'].items()}
            for result in document['runs'][0]['results']:
                result['message']['text'] = result['message']['text'].replace('test_mod.py::', 'subject/test_mod.py::')
    return document, manifest, victim


def _consume(root, family, freeze, document, manifest):
    raw = canonical_json_bytes(document)
    if family == 'antislop':
        if freeze:
            return freeze_antislop_expectations(raw, subject_root=root)
        return antislop_results_from_sarif(raw, manifest, subject_root=root)
    if freeze:
        return observed_findings(raw, root, require_review=family == 'review')
    return scan_results_from_sarif(raw, manifest, subject_root=root, require_review=family == 'review')


def _mutate(victim, mutation, outside):
    raw = victim.read_bytes()
    if mutation == 'parent-symlink':
        outside.mkdir()
        (outside / victim.name).write_bytes(raw)
        victim.unlink()
        victim.parent.rmdir()
        victim.parent.symlink_to(outside, target_is_directory=True)
    else:
        victim.unlink()
        if mutation == 'fifo':
            os.mkfifo(victim)
        elif mutation == 'leaf-symlink':
            outside.write_bytes(raw)
            victim.symlink_to(outside)
        else:
            with victim.open('wb') as stream:
                stream.write(raw)
                # JSON packet remains syntactically valid with oversized whitespace.
                if victim.suffix in {'.json', '.sarif'}:
                    stream.write(b' ' * (MAX_RESULTS_BYTES + 1 - len(raw)))
                else:
                    stream.truncate(MAX_RESULTS_BYTES + 1)


@pytest.mark.parametrize('family', ['generic', 'review', 'antislop'])
@pytest.mark.parametrize('freeze', [False, True])
@pytest.mark.parametrize('target', ['region', 'coverage'])
@pytest.mark.parametrize('mutation', ['leaf-symlink', 'parent-symlink', 'oversized'])
def test_subject_read_refuses_unconfined_or_oversized_files(tmp_path, family, freeze, target, mutation):
    root = tmp_path / 'subject'
    document, manifest, victim = _setup(root, family, target)
    _consume(root, family, freeze, document, manifest)  # Actual regular-file control.
    _mutate(victim, mutation, tmp_path / 'outside')
    with pytest.raises(ValueError):
        _consume(root, family, freeze, document, manifest)


@pytest.mark.parametrize('freeze', [False, True])
@pytest.mark.parametrize('mutation', ['leaf-symlink', 'parent-symlink', 'oversized'])
def test_review_packet_read_refuses_unconfined_or_oversized_files(tmp_path, freeze, mutation):
    root = tmp_path / 'subject'
    document, manifest, victim = _setup(root, 'review', 'packet')
    _consume(root, 'review', freeze, document, manifest)
    _mutate(victim, mutation, tmp_path / 'outside')
    with pytest.raises(ValueError):
        _consume(root, 'review', freeze, document, manifest)


@pytest.mark.parametrize('family,target', [
    ('generic', 'region'), ('generic', 'coverage'), ('review', 'region'),
    ('review', 'coverage'), ('review', 'packet'), ('antislop', 'region'), ('antislop', 'coverage'),
])
@pytest.mark.parametrize('freeze', [False, True])
def test_fifo_refuses_before_subprocess_deadline(tmp_path, family, target, freeze):
    root = tmp_path / 'subject'
    document, manifest, victim = _setup(root, family, target)
    _consume(root, family, freeze, document, manifest)
    _mutate(victim, 'fifo', tmp_path / 'outside')
    request = tmp_path / 'request.json'
    request.write_text(json.dumps([str(root), family, freeze, document, manifest]))
    code = '''import json,runpy,sys
from pathlib import Path
helpers=runpy.run_path(sys.argv[1])
root,family,freeze,document,manifest=json.loads(Path(sys.argv[2]).read_text())
try: helpers['_consume'](Path(root),family,freeze,document,manifest)
except ValueError: sys.exit(0)
sys.exit(1)
'''
    environment = {key: value for key, value in os.environ.items() if key != 'PYTEST_ADDOPTS'}
    environment['PYTHONPATH'] = str(Path(ranex.__file__).parent.parent)
    completed = subprocess.run([sys.executable, '-c', code, __file__, str(request)],
                               env=environment, capture_output=True, timeout=2, check=False)
    assert completed.returncode == 0, completed.stderr.decode()


@pytest.mark.parametrize('family', ['generic', 'review', 'antislop'])
@pytest.mark.parametrize('freeze', [False, True])
@pytest.mark.parametrize('mutation', ['leaf-symlink', 'parent-symlink', 'oversized', 'fifo'])
def test_actual_cli_artifact_reader_confines_artifact_parents(tmp_path, family, freeze, mutation):
    from ranex.cli.main import (
        _antislop_artifact_reader,
        _antislop_freeze_reader,
        _scan_artifact_reader,
        _scan_freeze_reader,
    )
    root = tmp_path / 'subject'
    document, manifest, _ = _setup(root, family, 'coverage')
    relative = Path('output/scan.sarif')
    artifact = root / relative
    artifact.parent.mkdir()
    artifact.write_bytes(canonical_json_bytes(document))
    if family == 'antislop':
        reader = _antislop_freeze_reader(relative) if freeze else _antislop_artifact_reader(manifest, relative)
    else:
        reporter = 'delegated-review-sarif-2.1.0' if family == 'review' else 'sarif-2.1.0'
        reader = _scan_freeze_reader(relative, reporter=reporter) if freeze else _scan_artifact_reader(manifest, relative, reporter=reporter)
    reader(artifact)
    _mutate(artifact, mutation, tmp_path / 'outside')
    with pytest.raises(ValueError):
        reader(artifact)


def test_confined_reader_does_not_create_absent_directories(tmp_path):
    root = tmp_path / 'absent'
    with pytest.raises(ValueError, match='absent'):
        read_results_artifact('nested/missing.py', subject_root=root)
    assert not root.exists()


def test_confined_reader_holds_parent_descriptor_through_path_replacement(tmp_path, monkeypatch):
    root = tmp_path / 'subject'
    parent = root / 'nested'
    parent.mkdir(parents=True)
    (parent / 'mod.py').write_bytes(b'subject bytes')
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'mod.py').write_bytes(b'outside bytes')
    original_open = os.open
    replaced = False

    def replace_parent(path, flags, *args, **kwargs):
        nonlocal replaced
        if path == 'mod.py' and kwargs.get('dir_fd') is not None:
            parent.rename(root / 'original')
            parent.symlink_to(outside, target_is_directory=True)
            replaced = True
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, 'open', replace_parent)
    assert read_results_artifact('nested/mod.py', subject_root=root) == b'subject bytes'
    assert replaced
    with pytest.raises(ValueError):
        read_results_artifact('nested/mod.py', subject_root=root)


def test_large_scope_and_coverage_probes_read_metadata_only(tmp_path, monkeypatch):
    from ranex.foundation.scan_results import _region_bytes, _subject_file_present

    source = tmp_path / 'large.py'
    with source.open('wb') as stream:
        stream.write(b'subject bytes\n')
        stream.truncate(16 * 1024 * 1024)
    original_read = os.read
    read_count = 0

    def observed_read(descriptor, count):
        nonlocal read_count
        read_count += 1
        return original_read(descriptor, count)

    monkeypatch.setattr(os, 'read', observed_read)
    assert _subject_file_present(tmp_path, 'large.py')
    document = {'version': '2.1.0', 'runs': [{
        'tool': {'driver': {'name': 'scanner'}}, 'results': [],
        'artifacts': [{'location': {'uri': 'large.py'}}],
    }]}
    manifest = {'scope': ['large.py'], 'rules': [], 'blocking_levels': ['error'], 'accepted': {}}
    summary = scan_results_from_sarif(canonical_json_bytes(document), manifest, subject_root=tmp_path)
    assert summary['missing'] == []
    assert summary['counts']['passed'] == 1
    assert read_count == 0
    assert _region_bytes(tmp_path, 'large.py', 1, 1, 'subject bytes') == b'subject bytes\n'
    assert read_count > 0
