# Ranex — agent conduct

Standing owner rules (2026-08-17) for every AI agent in this repository,
every harness. `CLAUDE.md` carries the project map; this file carries
conduct. Where they overlap, the stricter reading wins.

## GitHub identity

Operate as `anthonykewl20` on GitHub — always, no exceptions.

- Before any `gh` operation or `git push`, the gh active account must be
  `anthonykewl20`; if it is not, run
  `gh auth switch -h github.com -u anthonykewl20` and proceed.
- Never report account state as a residual, caveat, or handoff note — it is a
  rule to enforce, not a finding to disclose.
- The machine's gitconfig already pins
  `credential.https://github.com.username = anthonykewl20`.

## Completion is a full loop — never stop half-way

Work is done only when ALL of these hold:

1. Implementation verified on disk — diffs read, checks run; never a
   self-report.
2. Working tree clean — no stray files, scratch worktrees removed.
3. Docs synced — `docs/STATE.md` rewritten, active slice file current, README
   when public status changed.
4. Issues synced — in-progress label claimed at start, live comments during
   work, closing proof with commit SHA + executed command output (the tracker
   issues' standing rules).
5. Changes committed through the OCR gate (a block is work to fix, never a
   control to argue away or skip) and pushed fast-forward; remote tip
   verified.

Ending a session with uncommitted work, unsynced docs, or unposted issue
updates is a failure state, whatever the code says. Pipeline-gated slice work
waits for its gate (automatic GO LIVE) — but nothing else waits.

## No hand-waved or hand-rolled code

1. Never write code from model memory — verify every API, flag, SHA, version,
   price, and runtime behavior against the installed artifact or
   version-matched official docs before writing; a plausible-looking call is a
   defect until verified.
2. No stubs, placeholders, or "approximately this" implementations shipped as
   finished work.
3. No hand-rolled replacement for what the repo already provides (canonical
   JSON, digests, signing, confinement, journal) or for a mature, pinned,
   licence-compatible upstream implementation — any deviation needs an ADR
   recording why.
4. Never fabricate commands, test results, SHAs, URLs, or citations —
   anything not verified is reported UNVERIFIED, never PASS.
