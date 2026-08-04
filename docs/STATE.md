# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** SLICE-008 open — first delegation. Nothing built yet.
**Active slice:** `docs/slices/SLICE-008-first-delegation.md` (ADR-010,
accepted today, fan-out included before it was frozen).

## Where we stopped

SLICE-006 closed: Ranex gates Ranex, proven with the operator's own key.
`cli/main.py` then shed its git-query mechanics into `cli/repository.py`
(byte-identical, ten new refusal tests, suite 529 green).

ADR-010 is researched, panelled and accepted. A REFUTE panel found — and the
artifact confirmed — that `main.py:1368` reads the signing key into kernel
memory before the bound command spawns, while `RISK-06` reproduces that
command taking it from `/proc/<pid>/environ`. Under delegation the executed
suite is AI-written code, so that standing risk becomes the feature's main
attack path. Measured here: `os.environ.pop()` does not alter
`/proc/self/environ`; a same-uid process reads another's environ; and
unprivileged `uid_map` writes fail under
`apparmor_restrict_unprivileged_userns=1`, so a second uid needs privilege.
Hence: execution and attestation never share a process lifetime, enforced by
refusal — what SLSA Build L3 requires. Eight citations vendored, hashes recorded.

## Next

1. **Build SLICE-008 in criterion order, red first.** Criteria 1–3 (the
   execute/attest separation and its refusals) are why the slice exists;
   everything after is plumbing. Criterion 2 must inspect the live process
   tree through `/proc`, never a dict the test built.
2. Criterion 7 needs a real provider credential — scoped and spend-limited,
   since the loop can exfiltrate it (recorded, not mitigated).
3. Backlog: MAP §4.6 as a gate rule (start with "a skip is absence, not
   success"). ADR-006/Landlock still proposed and deferred; its `SLICE-005`
   reference is dangling by design. Handbooks unstarted.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` and dropped the
  epoch, breaking derivation — measured, not theoretical.
- Dependencies are trusted computing base: an approved wheel chooses the exit
  code (ADR-007 s.p. 17-19), demonstrated executably.
- The sample repository is writable by the observed command (ADR-009 s.p. 6);
  the fingerprint check still refuses edits.
- `approver_id` unauthenticated (`RISK-07`); `RISK-06` stays open for
  `ranex run` even once SLICE-008 closes its delegated path.
- The journal detects an edited row but not a removed one.
