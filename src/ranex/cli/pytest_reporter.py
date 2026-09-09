"""Controller-supplied pytest hook: preserve explicit non-strict XPASS.

Copied into the observation's scratch root and loaded by pytest, never imported
by the controller. Uses the installed pytest 7.4.4/9.1.1 reporting hooks and
JUnit stash interface. It does not make a hostile pytest plugin trustworthy.
"""

import os

import pytest
from _pytest.junitxml import xml_key


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    # Activation belongs to this observation, not arbitrary subprocess tests.
    # Distributed worker reports are normalized centrally by logreport below.
    plugins = [name for name in os.environ.get("PYTEST_PLUGINS", "").split(",")
               if name and name != __name__]
    if plugins:
        os.environ["PYTEST_PLUGINS"] = ",".join(plugins)
    else:
        os.environ.pop("PYTEST_PLUGINS", None)
    if not config.pluginmanager.hasplugin("skipping") or config.option.runxfail:
        raise pytest.UsageError("E-PYTEST-XFAIL-DISABLED: xfail/skip reporting must remain enabled")
    reporter = config.stash.get(xml_key, None)
    if reporter is not None:
        reporter.add_global_property("ranex.pytest_observer", "1")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_logreport(report):
    # Normalize completed local or distributed reports before normal hooks
    # count failures and serialize JUnit. Match pytest's strict-XPASS shape.
    if report.passed and hasattr(report, "wasxfail"):
        report.outcome = "failed"
        report.longrepr = "[XPASS(strict)] " + str(report.wasxfail)
        del report.wasxfail
    yield
