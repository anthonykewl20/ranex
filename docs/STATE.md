# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** `docs/slices/SLICE-003-claim-command-binding.md` — open, NOT done

## Where we stopped

238 green, 1 strict xfail, and **green has meant nothing twice here** — every
claim below was reproduced closed in a lab, not read off the suite. Red test
first, by a different agent than the implementer.

- **SLICE-002 reopened and re-closed** — `docs/adr/ADR-002-committed-trust-root.md`.
  The check returned early for a path the ref did not carry, so three attacks
  reached PASS: `--gate-catalog attacker-gates.yaml`, a `--producers` keyring
  under a committed `.gitignore` (invisible to `git status`), and a committed
  symlink at a reviewed name. Now such a path is refused, and git is asked about
  the name the operator typed. `run` applies it too.
- **Trust-root TOCTOU closed.** `committed_trust_root` returns the committed
  **bytes** and every loader parses those, so the second read has nowhere to
  happen. `strace`: `evaluate` opened `gates.yaml` 3× and `producers.yaml` 2×
  before, 1× each now.
- **D9, bind mount** — `same_file_inside` short-circuited on `st_nlink <= 1`, and
  a bind mount gives one inode a second name without touching the link count. The
  device pre-filter was unsound likewise. Both dropped; the scan is unconditional
  and reads inodes from the dirent — 5 ms, was 23 ms.
- **D10, unreadable directory** — found by this session's audit, not inherited.
  One `chmod 000` inside the worktree hid the twin, and git records no directory
  mode so the tree still read clean. A scan that cannot look now refuses.

## Next

1. **Re-audit the fixed code, then close SLICE-003.** No clean adversarial pass
   has run since D10 landed. It closes when an audit fails to get a PASS — not
   when the suite is green.
2. **SLICE-004 — signer/runner separation.** Owns D1 PATH-shadowing strict xfail
   (`tests/security/test_slice003_audit_defects.py`); Landlock ABI 8 unprivileged
   (~75 rules, ~1.7 ms) but inode-bound — assert `st_nlink == 1`.
3. **Queued — Architecture Contract.** After trust-boundary slices: research its ADR, then open one slice; turn global guidance into repo-specific artifact gates.

## Known limits, stated not fixed

- **`evidence.json` is not append-only**, so deleting a contradicting record
  defeats the contradiction check entirely. ADR-001 sad path 27.
- A committed `conftest.py` neutering the suite yields a genuine run, exit 0, a PASS and no trace — if the tree defines the check, the thrower owns the eyes.
- Approver identity is unauthenticated and the keyring admits visual lookalikes
  (`alice` beside `alice`+ZWSP), so no-self-approval is string equality over a
  pair the attacker picks. SLICE-005.
