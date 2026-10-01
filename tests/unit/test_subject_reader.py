"""Cache budgets cover keys, container overhead and all retained derived views."""
import os

import pytest

from ranex.foundation.subject_reader import SubjectReader


def test_bounded_lru_evicts_and_reacquires_updated_file(tmp_path):
    for name in ['a','b','c']:
        (tmp_path/name).write_bytes(name.encode()*16)
    reader = SubjectReader(tmp_path,max_entries=2,max_cache_bytes=4096)
    assert reader.read('a') == b'a'*16
    assert reader.read('b') == b'b'*16
    assert reader.read('a') == b'a'*16  # a is most recently used; b will be evicted.
    assert reader.read('c') == b'c'*16
    (tmp_path/'b').write_bytes(b'changed')
    assert reader.read('b') == b'changed'
    assert len(reader._entries) <= 2
    assert reader.retained_bytes <= 4096


def test_large_entry_bypasses_without_evicting_smaller_entry(tmp_path):
    (tmp_path/'small').write_bytes(b'ok')
    (tmp_path/'large').write_bytes(b'x'*4096)
    reader = SubjectReader(tmp_path,max_cache_bytes=2048)
    assert reader.read('small') == b'ok'
    assert reader.read('large') == b'x'*4096
    assert list(reader._entries) == ['small']
    (tmp_path/'large').write_bytes(b'y'*4096)
    assert reader.read('large') == b'y'*4096
    assert reader.retained_bytes <= 2048


def test_decoded_and_split_overhead_cannot_overrun_budget(tmp_path):
    raw = b'x\n'*1000
    (tmp_path/'many-lines').write_bytes(raw)
    reader = SubjectReader(tmp_path,max_cache_bytes=4096)
    assert reader.read('many-lines') == raw
    assert reader.lines('many-lines') == tuple(raw.splitlines(keepends=True))
    assert reader.text_lines('many-lines') == tuple(raw.decode().splitlines(keepends=True))
    assert reader.compact_lines('many-lines') == tuple((i,'x') for i in range(1000))
    # Auxiliary Python objects exceed the budget even though source bytes fit.
    assert reader._entries['many-lines'][0].lines is None
    assert reader._entries['many-lines'][0].text_lines is None
    assert reader._entries['many-lines'][0].compact is None
    assert reader.retained_bytes <= 4096


def test_unicode_and_crlf_line_views_preserve_each_existing_interpretation(tmp_path):
    raw = 'first\r\nsecond\u2028third\n'.encode()
    (tmp_path/'lines').write_bytes(raw)
    reader = SubjectReader(tmp_path)
    assert reader.lines('lines') == tuple(raw.splitlines(keepends=True))
    assert reader.text_lines('lines') == tuple(raw.decode().splitlines(keepends=True))
    assert reader.compact_lines('lines') == ((0,'first'),(1,'second'),(2,'third'))


@pytest.mark.parametrize('configuration',[{'max_cache_bytes':0},{'max_entries':0}])
def test_disabled_cache_observes_each_acquisition(tmp_path,configuration):
    (tmp_path/'file').write_bytes(b'before')
    reader = SubjectReader(tmp_path,**configuration)
    assert reader.read('file') == b'before'
    (tmp_path/'file').write_bytes(b'after')
    assert reader.read('file') == b'after'
    assert not reader._entries
    assert reader.retained_bytes == 0


@pytest.mark.parametrize('attack',['leaf-symlink','parent-symlink','fifo','oversized','escape'])
def test_first_acquisition_preserves_confined_regular_bounded_reader(tmp_path,attack):
    from ranex.foundation.suite_results import MAX_RESULTS_BYTES
    root = tmp_path/'subject'
    root.mkdir()
    outside = tmp_path/'outside'
    outside.write_bytes(b'outside')
    path = 'file'
    if attack == 'leaf-symlink':
        (root/path).symlink_to(outside)
    elif attack == 'parent-symlink':
        (root/'dir').symlink_to(tmp_path,target_is_directory=True)
        path = 'dir/outside'
    elif attack == 'fifo':
        os.mkfifo(root/path)
    elif attack == 'oversized':
        with (root/path).open('wb') as stream:
            stream.truncate(MAX_RESULTS_BYTES+1)
    else:
        path = '../outside'
    with pytest.raises(ValueError):
        SubjectReader(root).read(path)


def test_evicted_file_rechecks_confinement(tmp_path):
    (tmp_path/'a').write_bytes(b'first')
    (tmp_path/'b').write_bytes(b'second')
    reader = SubjectReader(tmp_path,max_entries=1)
    assert reader.read('a') == b'first'
    reader.read('b')
    (tmp_path/'a').unlink()
    (tmp_path/'a').symlink_to(tmp_path/'b')
    with pytest.raises(ValueError):
        reader.read('a')


def test_byte_budget_evicts_entries_even_below_entry_limit(tmp_path):
    reader = SubjectReader(tmp_path,max_cache_bytes=2048,max_entries=32)
    for number in range(20):
        path = f'file_{number}'
        (tmp_path/path).write_bytes(bytes([number])*256)
        assert reader.read(path) == bytes([number])*256
        assert reader.retained_bytes <= 2048
    assert len(reader._entries) < 20
    (tmp_path/'file_0').write_bytes(b'new content')
    assert reader.read('file_0') == b'new content'
