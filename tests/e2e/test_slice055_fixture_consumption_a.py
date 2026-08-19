"""SLICE-055 remediation R6b (worker A) — fixture-consumption module A.

The first of two tiny consuming modules for the module-scope re-evaluation
arm in tests/contract/test_real_suite_entrypoint.py. It requests one of the
six module-scoped ``prereq_*`` fixtures from tests/e2e/conftest.py and adds
nothing else: its whole observable is the fixture's own verdict for THIS
module (a skip with the greppable reason when the precondition is absent,
a quiet pass when present). The contract arm drives this module and its
sibling B in one pytest session with the precondition flipped between the
two modules — a session-cached fixture would make B reuse A's verdict
instead of re-evaluating its own.

Consuming the fixture here is deliberate: before these modules existed no
test requested the conftest prereq fixtures (the family slices SLICE-056+
own that), which the arbitration flagged as a dead-fixture finding.
"""

from __future__ import annotations


def test_module_a_consumes_the_signing_key_prereq_fixture(
    prereq_signing_key: None,
) -> None:
    """Module A's own module-scoped evaluation of the signing-key probe.

    No assertion beyond the fixture's verdict: the fixture itself skips
    with the ``ranex-prereq:signing_key:`` reason when the precondition is
    absent here, and returns quietly when present.
    """
