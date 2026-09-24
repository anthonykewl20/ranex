# SLICE-090 — Instrument self-test: no gauge is trusted until it has caught a known-bad

**Status:** done
**Issue:** #113

## Contract

`tools/dogfood/selftest.py` is the pre-flight harness. Every instrument —
`marker-scanner` (markers_probe.py), `release-audit` (release_audit.py),
`receiver-audit` (receiver_audit.py) — ships a **committed** good and bad
reference pair under `tools/dogfood/selftest/references/`, and the self-test
runs both **before any measurement and before any spend**. Exit contract:
`0` every instrument proved; `1` an instrument failed its own reference and no
measurement is attempted; `2` incomplete execution, never a silent green.

Classification rides the #95 machinery (`calibration.Control`/`_classify`), so
a self-test receipt can never be more lenient than a calibration one: statuses
are VERIFIED · GAP · FALSE-PASS · NON-DETERMINISTIC · UNVERIFIED, a bad
reference that is *accepted* is FALSE-PASS (not VERIFIED), and each side runs
3× on identical input with digest comparison. The receipt `selftest.json` is
timing-free so identical repeats are byte-identical; wall-clock and captured
output live in `selftest-commands.json`, where variation never changes a
status.

## Wiring

Each of the three drivers pre-flights its own instrument before measuring
(before kernel provisioning, before the external clone, before the pinned
subject, before the first listener). The #95 driver `calibration.py` gates its
measurement on **all three** passing in the same run: the self-test receipt is
written into `<out>/selftest/` before the first subject is built, and no
`calibration.json` can exist without it. `--skip-selftest` is refused outright
(exit 1, empty output directory) — ordering is enforced, not documented.
`--blunt <instrument>` is the negative control: it breaks one gauge on purpose
(marker-scanner becomes the neuter script that writes an empty SARIF; the
audit/receiver judgments approve whatever they observe) and the run must then
come back FALSE-PASS and refuse to measure.

## Boundaries

Marker references are `.txt` data copied into a scratch `.py` at run time —
committing the trigger-less bad reference plants no live violation in this
tree. The release-audit references build real governed scratch repositories
(real git, real Ed25519 key generated per run through the installed CLI,
discarded with the scratch); the receiver reference drives the real listener
over TCP with the local audit fixture. `verdict.py` untouched
(KERNEL_DIGEST unchanged); no new runtime dependency.

## Validation

Red-first: tests/contract/test_instrument_selftest.py (24 cases — reference
pairs, FALSE-PASS naming, GAP/NON-DETERMINISTIC classification, timing-free
byte-identical receipts, the skip refusal, and per-driver ordering), plus the
FT-16 BOM row and its extended contract test. Real-data proof:
tools/dogfood/audits/2026-09-24-selftest/ — all nine arms as-expected
(instruments VERIFIED ×3 byte-identical; blunted instrument stops the run with
no measurement receipt; cannot-fail reported FALSE-PASS; skip refused on an
empty directory; wired clean run produces the receipt only beside a passing
self-test; lane refusal, SIGKILL self-heal, all three spellings admitted
through the lane, forged boot-id staleness). Suite green on the final commit;
suite manifest refrozen on the committed tree.
