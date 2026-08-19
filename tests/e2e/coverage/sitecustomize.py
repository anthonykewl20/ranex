"""The subprocess coverage hook (SLICE-055 / ADR-032, coverage.py pattern).

This directory is appended LAST to a frame-wired child's PYTHONPATH by
tests/e2e/_prereqs.py's ``wire_child_environment`` — never first, never
replacing what is already there. Python imports ``sitecustomize`` from the
path at interpreter startup, so the hook is a property of the child's
environment, not of any test: a real ``python -m ranex.cli.main`` subprocess
starts coverage before its first import and, with ``parallel=true`` in the
named config, leaves a suffixed data file in the one shared
``COVERAGE_FILE`` home for a later combine.

Inert by construction: without ``COVERAGE_PROCESS_START`` in the child's
environment the guard below does not even import coverage, so the hook dir
riding a PYTHONPATH it was never wired into (a pytest collection, a plain
child) measures nothing and costs nothing — the off-state rule. Verified
against the installed coverage 7.15.3: ``process_startup()`` reads
``COVERAGE_PROCESS_START``, builds ``Coverage(config_file=...)`` with
auto-save, and starts it — a silent no-op when the variable is unset, which
is precisely the upstream silence the frame's loud no-data detection
(tests/e2e/_prereqs.py ``CoverageDataMissing``) exists to correct for the
children it wired.
"""

import os

if os.environ.get("COVERAGE_PROCESS_START"):
    import coverage

    coverage.process_startup()
