"""Controller-supplied pytest hook: preserve explicit non-strict XPASS.

Copied into the observation's scratch root and loaded by pytest, never imported
by the controller. Uses the installed pytest 7.4.4/9.1.1 reporting hooks and
JUnit stash interface. It does not make a hostile pytest plugin trustworthy.
"""

import pytest
from _pytest.junitxml import xml_key


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if config.option.runxfail or not config.pluginmanager.hasplugin("skipping"):
        raise pytest.UsageError("E-PYTEST-XFAIL-DISABLED: xfail/skip reporting must remain enabled")
    reporter = config.stash.get(xml_key, None)
    if reporter is not None:
        reporter.add_global_property("ranex.pytest_observer", "1")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Outermost wrapper: observe the report after pytest's skipping hook has
    # applied marker-level strict=False. Match pytest's own strict-XPASS shape
    # so both its exit status and its existing JUnit writer retain the failure.
    outcome = yield
    report = outcome.get_result()
    if report.passed and hasattr(report, "wasxfail"):
        report.outcome = "failed"
        report.longrepr = "[XPASS(strict)] " + str(report.wasxfail)
        del report.wasxfail
