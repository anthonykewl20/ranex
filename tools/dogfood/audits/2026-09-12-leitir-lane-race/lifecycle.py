"""Exercise actual lane CLI contention, cross-kind work, release, and crash recovery."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('module', type=Path)
parser.add_argument('output', type=Path)
a = parser.parse_args()
a.output.mkdir(parents=True)
records = []
for repeat in range(3):
    folder = a.output / str(repeat)
    folder.mkdir()
    env = dict(os.environ, RANEX_LANE_DIR=str(folder / 'lanes'))
    prefix = [sys.executable, str(a.module)]
    ready = folder / 'ready'
    stop = folder / 'stop'
    child = "from pathlib import Path; import sys,time; Path(sys.argv[1]).touch();\nwhile not Path(sys.argv[2]).exists(): time.sleep(.01)"
    hold_argv = prefix + ['run', '--kind', 'soak', '--', sys.executable, '-c', child, str(ready), str(stop)]
    def run(arguments):
        argv = prefix + arguments
        start = time.time()
        result = subprocess.run(argv, env=env, capture_output=True, text=True, check=False, timeout=10)
        records.append({'repeat': repeat, 'argv': argv, 'cwd': str(Path.cwd()), 'started': start,
                        'elapsed_seconds': time.time()-start, 'exit_code': result.returncode,
                        'stdout': result.stdout, 'stderr': result.stderr})
        return result
    for killed in (False, True):
        ready.unlink(missing_ok=True)
        stop.unlink(missing_ok=True)
        holder = subprocess.Popen(hold_argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, start_new_session=True)
        try:
            deadline = time.monotonic() + 10
            while not ready.exists():
                if time.monotonic() > deadline or holder.poll() is not None:
                    raise RuntimeError('holder failed to start')
                time.sleep(.005)
            status = run(['status', '--json'])
            assert status.returncode == 0 and len(json.loads(status.stdout)) == 1
            refused = run(['run', '--kind', 'soak', '--', sys.executable, '-c', "print('must-not-run')"])
            assert refused.returncode != 0 and 'REFUSED' in refused.stderr
            assert 'must-not-run' not in refused.stdout
            other = run(['run', '--kind', 'dogfood', '--', sys.executable, '-c', "print('parallel-kind-ran')"])
            assert other.returncode == 0 and 'parallel-kind-ran' in other.stdout
            if killed:
                os.killpg(holder.pid, signal.SIGKILL)
            else:
                stop.touch()
            stdout, stderr = holder.communicate(timeout=10)
            assert holder.returncode == (-signal.SIGKILL if killed else 0)
            records.append({'repeat': repeat, 'argv': hold_argv, 'killed': killed,
                            'exit_code': holder.returncode, 'stdout': stdout, 'stderr': stderr})
            recovered = run(['run', '--kind', 'soak', '--', sys.executable, '-c', "print('recovered')"])
            assert recovered.returncode == 0 and 'recovered' in recovered.stdout
            empty = run(['status', '--json'])
            assert empty.returncode == 0 and json.loads(empty.stdout) == []
        finally:
            if holder.poll() is None:
                os.killpg(holder.pid, signal.SIGKILL)
                holder.communicate(timeout=10)
    print(json.dumps({'repeat': repeat, 'same_kind_refused': True, 'different_kind_ran': True,
                      'release_recovered': True, 'killed_holder_recovered': True, 'final_holders': 0}))
(a.output / 'results.json').write_text(json.dumps({'module_sha256': hashlib.sha256(a.module.read_bytes()).hexdigest(),
                                                 'runs': records}, indent=2) + '\n')
