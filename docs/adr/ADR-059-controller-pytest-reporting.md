# ADR-059 — Controller-supplied pytest outcome reporting

**Status:** accepted
**Date:** 2026-09-09
**Issue:** #94; F-010 remainder
**Related:** ADR-011, ADR-056, ADR-058

## Problem

Pytest's `xfail_strict` ini value is a default. A legitimate marker specifying
`strict=False` overrides it. An unexpected pass then has `report.wasxfail` but
JUnit records a bare passing testcase. The existing parser cannot recover the
lost information. The real Six release audit reproduced this on the prior
release despite the exact `-o xfail_strict=true` command binding.

## Decision

The controller copies its pytest reporting hook into each disposable
observation root, outside the materialised contributor tree, and selects it
through a fixed PYTEST_PLUGINS/PYTHONPATH environment. The canonical hook is
`ranex.foundation.pytest_xpass`; an explicitly bound `-p` uses the same source.
The controller copy also protects applications without an installed Ranex
package, so explicit `-p` is supported but not required by claim admission.
When both activation paths load, they emit one JUnit observer property.
An explicitly bound `-p ranex.foundation.pytest_xpass` receives a private
namespace portion containing only that module. Real materialised Ranex
packages retain import precedence. Automatic activation does not create a
Ranex namespace. The controller's source/site-packages directory is never
added to the subject's import path: an installed-wheel probe demonstrated
that doing so silently replaced system pytest 7.4.4 with controller pytest
9.1.1. The installed release check now exercises both activation modes and
asserts the subject's dependency version and import path remain intact.
It adds no target package,
does not change the digest-bound command, and does not inherit operator plugin
or Python startup settings. Existing command admission remains in place.

An outer pytest_runtest_logreport wrapper normalizes completed reports before
JUnit and failure-counting hooks. It consumes its environment activation so
nested pytest processes do not inherit an unavailable or unintended plugin.
Distributed worker reports are normalized in the controller as well.
A passed report carrying wasxfail becomes pytest's own strict-XPASS failure
shape: failed outcome, `[XPASS(strict)]` longrepr, and no wasxfail attribute.
The normal JUnit writer then records it as a failure, the process exits red,
and Ranex's existing outcome parser records xpassed. Ordinary failures, skips,
expected failures and passing tests keep their outcomes.

The hook records `ranex.pytest_observer=1` in JUnit suite properties. Live run,
freeze and delegated suite observation require exactly one supported marker
per suite. Missing/disabled reporting refuses observation instead of signing
a passing result. Configuration that disables xfail/skip handling through
runxfail or the skipping plugin also refuses. Historical raw JUnit parsing
remains available without changing retained evidence or verdict signatures.

The injected environment is supported in the standard observation path and
the delegated suite path. Strict-local runtime carriers do not yet contain
this hook; requesting a pytest suite in that path refuses before execution
with E-PYTEST-OBSERVER-CONFINEMENT. It must not silently fall back to lossy
JUnit. Vitest retains its own reporter and requires no pytest plugin.

## Trust boundary

This closes ordinary pytest outcome loss. The report marker is a presence and
compatibility check, not an attestation from a separate security principal.
A hostile conftest, pytest plugin or same-UID observer can still forge or alter
reports (F-012). No claim of hostile-code-proof reporting or isolated worker
security follows from this change. An external witness remains unimplemented.

## Version evidence

Inspected installed pytest 7.4.4 (`/usr/bin/python3`) and 9.1.1 (frozen Ranex
environment): `_pytest/skipping.py::pytest_runtest_makereport`,
`_pytest/junitxml.py::LogXML.pytest_runtest_logreport`,
`_NodeReporter.append_failure`, `LogXML.add_global_property`, and `xml_key`.
Both versions set wasxfail for a non-strict XPASS. append_failure treats a
remaining wasxfail as skipped, which is why the conversion removes it.
Real pytest-xdist 3.8.0 with two workers retained the failure centrally. Its
registry sdist was inspected via Leitir (SHA256
7e578125ec9bc6050861aa93f2d59f1d8d085595d6551c2c90b6f4fad8d3a9f1);
registry/Git parity reported drift, so no byte-identical Git claim is made.
The hook uses pytest's hookwrapper protocol and its version-matched JUnit
stash interface. No new project dependency or upstream code transplant.

## Validation

Real subprocess tests cover explicit XPASS, a mixed outcome suite, marker
absence/duplication, configuration disabling, signed gate refusal, repair,
and delegated observation before materialisation cleanup. The real external
Six audit and full final-commit regression remain release requirements.
