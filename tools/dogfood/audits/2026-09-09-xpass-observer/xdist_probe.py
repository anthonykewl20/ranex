"""Integration probe using real pytest-xdist workers; synthetic outcome controls."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from importlib.metadata import version
from ranex.cli.suite_observer import pytest_observer_environment
from ranex.foundation.suite_results import freeze_manifest, suite_results_from_junitxml
with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    (root / 'test_dist.py').write_text('import pytest\ndef test_pass(): pass\n@pytest.mark.xfail(strict=False)\ndef test_xpass(): pass\n')
    argv = [sys.executable, '-m', 'pytest', '-q', '-n', '2', '-o', 'xfail_strict=true', '--junitxml=result.xml']
    result = subprocess.run(argv, cwd=root, env={**os.environ, **pytest_observer_environment(root)}, capture_output=True, text=True, check=False)
    print(result.stdout, result.stderr)
    raw = (root / 'result.xml').read_bytes()
    summary = suite_results_from_junitxml(raw, freeze_manifest(raw, require_pytest_observer=True), require_pytest_observer=True)
    assert result.returncode == 1 and summary['counts']['xpassed'] == 1 and summary['counts']['passed'] == 1
    print(json.dumps({'pytest': version('pytest'), 'pytest-xdist': version('pytest-xdist'), 'command': argv, 'exit': result.returncode, 'summary': summary}, indent=2))
