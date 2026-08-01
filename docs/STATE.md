# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-01
**Phase:** kernel — evidence loop
**Active slice:** `docs/slices/SLICE-003-claim-command-binding.md` — open, NOT done

## Where we stopped

**SLICE-003 is implemented, 214 green, and the green suite is false.** Four
independent audits (three subagents, plus `tencent/hy3` via direct OpenRouter)
reproduced **seven fraudulent gate PASSes**. Do not trust the suite here; read
`docs/adr/ADR-001-claim-command-binding.md` sad paths 18-24 first. Red tests for
every defect below are being written; `src/` is NOT yet fixed.

- **PATH shadowing (18, 21).** A fake `pytest` outside the tree, earlier on
  `$PATH`, PASSes: containment asks "outside the repo?", never "is this the bound
  binary?". ADR-001 claimed this closed; false, withdrawn in place.
- **Hard link (19).** `ln <repo>/x /tmp/pytest` — outside by path, in-repo by
  inode. Identity must be `(st_dev, st_ino)`. Same class as the Landlock spike.
- **TOCTOU (20).** Swap a directory component between check and spawn; won 9/9
  at 75-85ms. Fix: open once, spawn via `/proc/self/fd/N`.
- **`--journal` (23).** Out of scope and exploitable: exempts any untracked path
  from the dirty-tree check, so a record can describe a tree that is not HEAD —
  stronger than the hole `6e6a28005` closed. The HEAD check also misses staged files.
- **Contradictory records (22).** Honest exit-1 plus faked exit-0 for one claim
  PASSes via `any()`.
- **Reporting.** A digest mismatch reads as "no evidence" — the honest-absence
  wording SLICE-002 already fixed once.

## Next

1. **Fix the above, red-then-green, then re-audit.** SLICE-003 does not close
   until an adversarial audit fails to get a PASS.
2. **SLICE-002 IS REOPENED — critical.** `--gate-catalog` / `--producers`
   pointing at an uncommitted file bypasses `refuse_uncommitted_trust_root`,
   which returns early when HEAD lacks the path. A worker self-registers a
   producer and PASSes. The trust root must be the committed path itself.
3. **SLICE-004 — signer/runner separation.** The privileged side must run the
   command and observe the exit code; a broker that signs what it is handed
   leaves the oracle in reach. Landlock ABI 8 works unprivileged (~75 rules,
   ~1.7ms) but is inode-bound — assert `st_nlink == 1`.

## Known limits, stated not fixed

- A committed `conftest.py` neutering the suite yields a genuine run, exit 0 and
  a PASS, no trace. If the tree defines the check, the thrower controls the eyes.
- Approver identity is an unauthenticated string (SLICE-005). *Accelerate*
  constrains the fix: a peer in the flow, never a change-approval board.
