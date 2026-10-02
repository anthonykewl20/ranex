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


def test_newline_dense_subject_refuses_each_derived_view(tmp_path):
    (tmp_path/'dense').write_bytes(b'\n'*200)
    reader = SubjectReader(tmp_path, max_view_lines=100)
    before = reader.retained_bytes
    raw_reader = SubjectReader(tmp_path, max_view_lines=100)
    raw_reader.read('dense')
    raw_cost = raw_reader.retained_bytes
    for method in (reader.lines, reader.text_lines, reader.compact_lines):
        with pytest.raises(ValueError, match='more than 100 lines'):
            method('dense')
    assert reader.retained_bytes <= before + raw_cost
    view = reader._entries['dense'][0]
    assert view.lines is view.text_lines is view.compact is None


def test_view_at_the_bound_is_built(tmp_path):
    (tmp_path/'bound').write_bytes(b'x\n'*99 + b'end')
    reader = SubjectReader(tmp_path, max_view_lines=100)
    default = SubjectReader(tmp_path)
    assert reader.lines('bound') == default.lines('bound')
    assert reader.text_lines('bound') == default.text_lines('bound')
    assert reader.compact_lines('bound') == default.compact_lines('bound')


def test_view_bound_rejects_bad_values(tmp_path):
    for value in (-1, True):
        with pytest.raises(ValueError):
            SubjectReader(tmp_path, max_view_lines=value)


def test_sparse_multiline_subject_unchanged(tmp_path):
    (tmp_path/'sparse').write_bytes(b'first\r\n\r\n+ second\r\n  \r\n-last')
    reader = SubjectReader(tmp_path)
    assert reader.lines('sparse') == (b'first\r\n', b'\r\n', b'+ second\r\n', b'  \r\n', b'-last')
    assert reader.text_lines('sparse') == ('first\r\n', '\r\n', '+ second\r\n', '  \r\n', '-last')
    assert reader.compact_lines('sparse') == ((0, 'first'), (2, 'second'), (4, 'last'))
