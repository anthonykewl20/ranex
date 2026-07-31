# SLICE-001 — evidence production

**Status:** open
**Opened:** 2026-08-01

## Why

Nothing in Ranex produces evidence. `governance/evidence.json` is hand-written,
currently cites a script that no longer exists, and is bound to a dead tree
digest. The kernel can judge evidence but cannot generate it, so the loop is
open at both ends. This closes one end.

## Goal

`ranex run` executes a command, observes it, and emits an evidence record that
`gate evaluate` will accept.

```
ranex run --claim tests-executed --producer worker -- uv run pytest -q
ranex gate evaluate HEAD --approver reviewer_alice     # -> PASS
```

## Done criteria

Each must be met and proven by a test.

- [ ] `run` executes the command and records its exit code verbatim
- [ ] The subject digest is computed by the **same function** `gate evaluate`
      uses — one implementation, not two
- [ ] `run` **refuses on a dirty working tree** (exit 2, nothing written).
      A digest of `HEAD` does not describe an uncommitted tree, and recording it
      as if it did would be a false claim
- [ ] The record is appended to `governance/evidence.json`, creating the file if
      absent and preserving unrelated records
- [ ] A record for the same `(claim_id, producer_id)` is **replaced**, not
      duplicated
- [ ] Emitted records round-trip through the existing `load_evidence`
- [ ] Path arguments go through `resolve_within_repository` like every other
      path in the CLI
- [ ] e2e: `run` then `gate evaluate` → PASS, exit 0
- [ ] e2e: `run --producer X` then `gate evaluate --approver X` → FAIL
      (self-approval still refused end to end)

## Out of scope

- Signing and authenticity — that is SLICE-002. After this slice a pass is still
  forgeable with a text editor. That is expected and must not be described as
  solved.
- Journal changes — SLICE-003.
- Any change to the evidence file format or to `evaluate()`.

## Decisions taken

- **Refuse on dirty tree** rather than digesting the working tree. Simplest
  honest behaviour. Digesting a dirty tree via `git write-tree` is a later
  option if it proves necessary.
- Evidence stays a plain JSON array. No schema migration in this slice.

## Notes

`evaluate()` must not change. If this slice seems to require changing it, stop —
that is a signal the slice is wrong, not the kernel.
