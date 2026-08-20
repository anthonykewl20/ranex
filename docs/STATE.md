# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-058 opened; frozen tests + golden contracts committed red)
**Active slice:** docs/slices/SLICE-058-real-e2e-provisioning-family.md

## Where we stopped

SLICE-058 (#38, provisioning-family real e2e — deps fetch/approve +
keygen) is OPEN with its frozen tests committed red: tests/e2e/
test_deps_real.py (4 red / 7 green — the four golden-consuming arms red
on the missing golden; real-index journey on the real pins, sha256sum
store re-hash, wheel byte-flip quarantine + one-wheel repair, drift/
epoch refusals, env-injection ignored, and the ADR-032 sad-path-12
local-index fixture: liar names the wheel, dead refuses clean) and
tests/e2e/test_keygen_real.py (3 red / 1 green — kernel signs and
accepts the keygen key, openssl verifies both directions over PKCS#8/
SPKI DER, confinement gates). The two goldens (deps-fetch-lock.out,
keygen-verify.out) are the implementation lane's artifacts. Every
asserted behavior was prototyped against the kernel at 271344443 first.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-058
The implementation lane captures the two goldens from the real journeys,
posts AC3's sabotage red output on #38, and closes through the standing
freeze ceremony (probe-grammar declarations for the deps arms' skips).
Carried follow-ups: the argument-filtered clone decision and the
writable-tree full-mask EXECUTE residual (both security-review-owned),
the mirror-pin test for `_journal_first_broken_row` (SLICE-056), the
SLICE-055 items.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags) — SLICE-057's recorded residual; contained by the inheritance facts, review-owned.
- Writable trees carry full-mask Landlock EXECUTE — live since the execveat admission (321cb524d's first pinned filter admitted openat+execveat, so self-written binaries were executable by fd BEFORE e1e6dc8a7; e1e6dc8a7's execve widened the surface to plain pathname exec) — self-written binaries exec in-sandbox; contained by inheritance; SLICE-057 MINOR-4, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
