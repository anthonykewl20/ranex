import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('module', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--worker', type=int)
a = parser.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
if a.worker is not None:
    os.environ['RANEX_LANE_DIR'] = str(a.output / 'lanes')
    spec = importlib.util.spec_from_file_location('ranex_lane', a.module)
    lane = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = lane
    spec.loader.exec_module(lane)
    (a.output / f'ready-{a.worker}').touch()
    deadline = time.monotonic() + 20
    while not (a.output / 'start').exists():
        if time.monotonic() > deadline:
            raise TimeoutError('start')
        time.sleep(.001)
    held = None
    try:
        held = lane.acquire('soak', detail=f'lightweight race worker {a.worker}')
        result = {'worker': a.worker, 'status': 'ADMITTED'}
    except SystemExit as exc:
        result = {'worker': a.worker, 'status': 'REFUSED', 'reason': str(exc)}
    except Exception as exc:
        result = {'worker': a.worker, 'status': 'ERROR', 'reason': repr(exc)}
    pending = a.output / f'result-{a.worker}.tmp'
    pending.write_text(json.dumps(result))
    pending.replace(a.output / f'result-{a.worker}.json')
    try:
        while not (a.output / 'release').exists():
            if time.monotonic() > deadline:
                raise TimeoutError('release')
            time.sleep(.005)
    finally:
        if held is not None:
            lane.release(held)
    sys.exit(0)

reports = []
for repeat in range(3):
    run = a.output / str(repeat)
    run.mkdir()
    children = [subprocess.Popen([sys.executable, __file__, str(a.module), str(run), '--worker', str(i)], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(16)]
    def wait_for(pattern):
        deadline = time.monotonic() + 25
        while len(list(run.glob(pattern))) != len(children):
            if time.monotonic() > deadline:
                raise TimeoutError(pattern)
            time.sleep(.005)
    try:
        wait_for('ready-*')
        (run / 'start').touch()
        wait_for('result-*.json')
        rows = [json.loads(p.read_text()) for p in sorted(run.glob('result-*.json'))]
        counts = {status: sum(r['status'] == status for r in rows) for status in ('ADMITTED', 'REFUSED', 'ERROR')}
        reports.append({'repeat': repeat, **counts, 'rows': rows})
        print(json.dumps({'repeat': repeat, **counts}), flush=True)
    finally:
        (run / 'release').touch()
        for child in children:
            stdout, stderr = child.communicate(timeout=30)
            if child.returncode:
                print(stderr.decode(), file=sys.stderr)
                raise RuntimeError(child.returncode)
(a.output / 'summary.json').write_text(json.dumps(reports, indent=2) + '\n')
sys.exit(0 if all(r['ADMITTED'] == 1 and r['ERROR'] == 0 for r in reports) else 1)
