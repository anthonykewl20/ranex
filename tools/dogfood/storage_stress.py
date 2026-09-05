"""Stress SQLite with actual gate records and verify attacked copies via the CLI.

Pass journals produced by real Ranex gate evaluations. Repeated appends measure
storage behavior only; they are not independent code correctness observations.
Output must be inside this checkout so the real journal CLI can resolve it.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import time
from contextlib import closing
from pathlib import Path

from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.verdict import ClaimCause, Evaluation, Verdict

ROOT = Path(__file__).resolve().parents[2]


def append_batch(args):
    path, raw = args
    value = json.loads(raw)
    value['verdict'] = Verdict(value['verdict'])
    value['causes'] = tuple(ClaimCause(**c) for c in value['causes'])
    for name in ('missing_claims', 'considered'):
        value[name] = tuple(value[name])
    evaluation = Evaluation(**value)
    journal = Journal(Path(path))
    before = len(os.listdir('/proc/self/fd'))
    started = time.monotonic()
    for _ in range(500):
        journal.append(evaluation)
    return dict(seconds=time.monotonic()-started, fd_before=before, fd_after=len(os.listdir('/proc/self/fd')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for source in args.journal:
        with closing(sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True)) as connection:
            records.append(connection.execute('select record from evaluations limit 1').fetchone()[0])
    receipt = dict(kernel=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
                   source_journals=[dict(path=str(p.resolve()), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in args.journal],
                   scope='Storage load replays actual CLI gate evaluations; repeated rows are not new correctness observations',
                   source_records=[json.loads(r) for r in records], rounds=[], controls=[])
    def save():
        (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    save()
    for index, executor in enumerate([concurrent.futures.ThreadPoolExecutor,
                                      concurrent.futures.ProcessPoolExecutor,
                                      concurrent.futures.ThreadPoolExecutor,
                                      concurrent.futures.ProcessPoolExecutor,
                                      concurrent.futures.ThreadPoolExecutor]):
        path = out / f'round-{index}.sqlite3'
        start = time.monotonic()
        with executor(max_workers=8) as pool:
            workers = list(pool.map(append_batch, [(str(path), records[i % len(records)]) for i in range(8)]))
        journal = Journal(path)
        count, verified = len(journal.entries()), journal.verify()
        relative = Journal(path.relative_to(Path.cwd()))
        relative_verified = relative.verify(expected_head=journal.head())
        row = dict(round=index, executor=executor.__name__, appends=count, verified=verified,
                   relative_path_verified=relative_verified, relative_head=relative.head(),
                   seconds=time.monotonic()-start, workers=workers, head=journal.head())
        receipt['rounds'].append(row)
        save()
        print(row, flush=True)
        if count != 4000 or not verified or not relative_verified or relative.head() != journal.head():
            raise RuntimeError('storage round failed')
    head = Journal(path).head()
    receipt['independent_head_before_mutation'] = head
    for mode in ('unchanged', 'nonjson', 'truncated', 'empty', 'rewritten'):
        attacked = out / f'{mode}.sqlite3'
        shutil.copyfile(path, attacked)
        if mode != 'unchanged':
            with closing(sqlite3.connect(attacked)) as c, c:
                c.execute('drop trigger evaluations_no_update')
                c.execute('drop trigger evaluations_no_delete')
                if mode == 'nonjson':
                    c.execute("update evaluations set record='not JSON' where seq=1")
                elif mode == 'truncated':
                    c.execute('delete from evaluations where seq=(select max(seq) from evaluations)')
                elif mode == 'empty':
                    c.execute('delete from evaluations')
                else:
                    previous = 'sha256:'+'0'*64
                    for seq, raw in c.execute('select seq,record from evaluations order by seq').fetchall():
                        value = json.loads(raw)
                        value['approver_id'] = 'altered-history'
                        link = 'sha256:'+canonical_sha256(dict(prev_link=previous,record=value))
                        c.execute('update evaluations set record=?,prev_link=?,link=? where seq=?',
                                  (canonical_json(value), previous, link, seq))
                        previous = link
        command = ['uv', 'run', '--frozen', 'ranex', 'journal', 'verify', '--journal', str(attacked.relative_to(ROOT)),
                   '--expected-head', head]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        row = dict(mode=mode, command=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
                   database_sha256=hashlib.sha256(attacked.read_bytes()).hexdigest())
        receipt['controls'].append(row)
        save()
        print(row, flush=True)
        if result.returncode != (0 if mode == 'unchanged' else 1):
            raise RuntimeError('anchor control failed: '+mode)
        if mode == 'nonjson' and Journal(attacked).verify() is not False:
            raise RuntimeError('non-JSON API must return false')
    # Reproduce an operator pasting an incomplete actual retained head.
    command = ['uv', 'run', '--frozen', 'ranex', 'journal', 'verify', '--journal',
               str(path.relative_to(ROOT)), '--expected-head', head[:-1]]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    receipt['controls'].append(dict(mode='incomplete-pasted-head', command=command,
                                    exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
    save()
    if result.returncode != 2:
        raise RuntimeError('an incomplete retained head must be a named usage refusal')


if __name__ == '__main__':
    main()
