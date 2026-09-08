"""Verify retained live signed journal anchors and refuse invalid anchor inputs.

The positive inputs are archived GitHub App receipts, not newly signed fixtures.
Attacks modify private copies only. No signing key or network access is needed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from ranex.foundation.verdict_signing import signed_fields_for, signed_payload
from ranex.governed_execution.verdict_reader import ReadState, read_verdict_unbound

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'tools/dogfood/audits/2026-09-09-automatic-evidence'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.relative_to(ROOT)
    out.mkdir(parents=True, exist_ok=False)
    live = ARCHIVE / 'fifth-pass'
    verdict = live / 'verdicts/5d185f19fa7e67d063e4dd954f464aa7a01ab1ae64319ef49b2a20ad4560acb6.json'
    journal = live / 'journal.sqlite3'
    keyring = live / 'producers.yaml'
    v1 = ARCHIVE / 'verdicts/292b30a32162cee62c65ad5a3cd6737909abbee2e227646bdec6041bb577f8d7.json'
    tampered = out / 'tampered.json'
    record = json.loads(verdict.read_bytes())
    record['record']['journal_head'] = 'sha256:' + '0' * 64
    tampered.write_text(json.dumps(record))
    receipts = []
    for name, anchor, producers, extra, expected in (
        ('live-signed-anchor', verdict, keyring, [], 0),
        ('missing-verdict', out / 'absent.json', keyring, [], 2),
        ('missing-keyring', verdict, out / 'absent.yaml', [], 2),
        ('tampered-anchor', tampered, keyring, [], 2),
        ('archived-v1-unanchored', v1, ARCHIVE / 'producers.yaml', [], 2),
        ('ambiguous-anchor', verdict, keyring, ['--expected-head', 'sha256:' + '0' * 64], 2),
    ):
        command = ['uv', 'run', '--frozen', 'ranex', 'journal', 'verify',
                   '--journal', str(journal.relative_to(ROOT)),
                   '--against-verdict', str(anchor.relative_to(ROOT)),
                   '--producers', str(producers.relative_to(ROOT)), *extra]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
        receipts.append(dict(case=name, command=command, exit=result.returncode,
                             stdout=result.stdout, stderr=result.stderr))
        (out / 'receipt.json').write_text(json.dumps(receipts, indent=2) + '\n')
        assert result.returncode == expected, receipts[-1]
        if expected == 0:
            assert 'external-anchor=matched(signed-verdict)' in result.stdout
        print(name, result.returncode, flush=True)
    absent = read_verdict_unbound(out / 'absent.json', {})
    assert absent.state is ReadState.ABSENT and absent.journal_head is None
    # Public signing APIs must reject unsupported domains before serialization.
    for call in (lambda: signed_fields_for(None),
                 lambda: signed_payload({}, payload_type='unsupported')):
        try:
            call()
        except ValueError as error:
            assert 'unsupported verdict payload type' in str(error)
        else:
            raise AssertionError('unsupported signing domain was accepted')


if __name__ == '__main__':
    main()
