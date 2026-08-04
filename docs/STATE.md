# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** between slices. SLICE-006 is closed and archived.
**Active slice:** none — the next slice needs its ADR first; that is the rule.

## Where we stopped

SLICE-006 closed with all fifteen criteria met. Ranex gates Ranex: stage 12
passed with the operator's registered key — `ranex run` executed the
unchanged catalog command against the real current commit and `gate
evaluate` accepted the signed evidence. ADR-009's materialisation (a fresh
single-commit repository carrying the verified tree) is what unblocked it.

Close-out verification: suite 519 green; diff-cover 100% over the whole
slice range (747/747 lines, which found and closed one unreached refusal);
mutmut 4771 mutants — 2980 killed, 841 timed out, 306 uncovered, 644
survived (down from 1036), sampled survivors equivalent or message-text,
every mutant of the new `.git`-path refusal killed. Nine defects found this
slice by driving the real thing; none by a unit test (MAP §4.6).

Operator state: `anthony` registered in `governance/producers.yaml`; the
private key is outside the tree at `~/.config/ranex/anthony.key`
(`RANEX_SIGNING_KEY` points at it); the default store is populated and the
depset approved by `reviewer`.

## Next

1. **Owner-requested: extract the git-query service from `cli/main.py`**
   (2206 lines, 42% of the codebase — the one god-module; mutation
   survivors concentrate there). Mechanical move, no behavior change, full
   gates. Decide whether it needs its own ADR/slice before starting.
2. Backlog: turn MAP §4.6 into a gate rule (start with "a skip is absence,
   not success" — a fully skipped suite exits 0 and the gate accepts it
   today). ADR-006/Landlock still proposed and deferred; its `SLICE-005`
   reference is dangling by design. Handbooks and first-delegation
   unstarted.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` and dropped the
  epoch, breaking derivation — measured, not theoretical.
- Dependencies are trusted computing base: an approved wheel chooses the exit
  code (ADR-007 s.p. 17-19), demonstrated executably.
- The sample repository is writable by the observed command (ADR-009 s.p. 6)
  — vandalism dies with it; the fingerprint check still refuses edits.
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`).
- The journal detects an edited row but not a removed one.
