"""SLICE-055 remediation R6b (worker A) — fixture-consumption module B.

The second of the two tiny consuming modules for the module-scope
re-evaluation arm (tests/contract/test_real_suite_entrypoint.py). When the
contract arm exports ``RANEX_SLICE055_FLIP=1`` for its subprocess session,
this module's autouse module-scoped fixture removes ``RANEX_SIGNING_KEY``
before this module's own ``prereq_signing_key`` fixture evaluates (autouse
fixtures of a scope run before other same-scope fixtures) and restores it
at module teardown — so the session's second consumer sees the flipped
verdict as ITS OWN evaluation: the test skips with the greppable
``ranex-prereq:signing_key:`` reason even though module A, earlier in the
same session, saw the precondition present. A session-cached fixture would
instead reuse A's verdict and run B's test — exactly what the arm refuses.

Without ``RANEX_SLICE055_FLIP`` the module is inert: the flip never fires
and the fixture evaluates the live environment like any consumer, so a
plain suite run is unaffected.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="module", autouse=True)
def _flip_signing_key_absent_for_this_module_only():
    """Remove RANEX_SIGNING_KEY for this module's evaluation, restore after.

    Fires only under the contract arm's dedicated RANEX_SLICE055_FLIP=1
    session; module scope + restore keeps the flip from leaking past this
    module's last test into later modules of a full-suite run.
    """

    if os.environ.get("RANEX_SLICE055_FLIP") != "1":
        yield
        return
    saved = os.environ.pop("RANEX_SIGNING_KEY", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["RANEX_SIGNING_KEY"] = saved


def test_module_b_re_evaluates_the_signing_key_prereq_for_this_module(
    prereq_signing_key: None,
) -> None:
    """Module B's own module-scoped evaluation — the flip's observation.

    Under the flip this skips with the ``ranex-prereq:signing_key:`` reason
    (the observation the contract arm asserts); without it, the fixture
    evaluates the live environment exactly like module A.
    """
