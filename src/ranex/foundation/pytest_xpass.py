"""A kernel-owned pytest reporter: every XPASS reaches the artifact.

ADR-056 bound a `pytest-junit` suite claim to `-o xfail_strict=true`, which
closes the XPASS blind spot for a marker that states no `strict`. It cannot
close the rest: `-o` supplies the ini *default*, a marker-level `strict` kwarg
overrides it, and nothing in a digest-bound argv can reach a kwarg written in
the tree under test. `@pytest.mark.xfail(strict=False)` — an ordinary,
legitimate idiom, not a hostile edit — therefore still produced a bare passing
`<testcase/>` and satisfied the claim (FINDINGS F-010 remainder, issue #94).

pytest does not lose the information. `_pytest/skipping.py` records it on
`report.wasxfail`; `_pytest/junitxml.py`'s `append_pass` is
`self.add_stats("passed")` and never reads it. This module reads it and turns
the pass into a failure, so the outcome exists in the bytes the kernel judges.

Loaded by name from the claim's argv (`-p ranex.foundation.pytest_xpass`), so
removing it changes the command digest and the claim stops being satisfied.
The tree can still refuse to honour it — a planted `conftest.py` or an approved
`pytest11` plugin is the disclosed forgery boundary (ADR-007, ADR-011 criterion
10, F-012) and is not closed here. This closes the honest-process case.
"""

from __future__ import annotations

from typing import Any

import pytest

#: The marker the kernel's summariser already classifies as `xpassed`. Spelled
#: exactly as `_pytest/skipping.py` spells a strict XPASS so one shape reaches
#: `foundation/suite_results._outcome`, whichever way strictness was obtained.
XPASS_PREFIX = "[XPASS(strict)]"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: Any, call: Any) -> Any:
    """Turn any unexpectedly-passing xfail into a reported failure.

    `tryfirst`, not `trylast`: a hookwrapper's post-yield body runs in reverse
    registration order, so the *first*-registered wrapper resumes last — after
    `_pytest.skipping` has attached `wasxfail`. Registered `trylast` this hook
    observes a report the marker has not been applied to yet and does nothing,
    which was measured, not assumed.
    """

    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.outcome != "passed":
        return
    reason = getattr(report, "wasxfail", None)
    if reason is None:
        return

    # `del` is load-bearing. `_pytest/junitxml.py`'s `append_failure` begins
    # `if hasattr(report, "wasxfail")` and, when it is present, writes
    # `<skipped message="xfail-marked test passes unexpectedly"/>` instead of a
    # failure. Setting the outcome alone yields an `F` in the terminal and a
    # *skipped* element in the artifact — fixed everywhere except the one place
    # that decides the verdict, and read back as `xfailed` rather than
    # `xpassed`. Dropping the attribute is what makes the artifact honest.
    del report.wasxfail
    report.outcome = "failed"
    report.longrepr = f"{XPASS_PREFIX} {reason}"
