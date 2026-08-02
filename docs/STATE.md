# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** none. SLICE-003 is closed; SLICE-004 cannot open until
`docs/adr/ADR-003-*.md` is researched and written.

## Where we stopped

250 green, 6 strict xfail. SLICE-003 closed on its own promise: six independent
audits failed to make a record satisfy a claim it does not name, and criteria
1–9 were re-proven by mutation — each control deleted from `src/` in turn, the
covering test observed going red, not read off a green suite.

Five defects fixed on the way out, each mutation-verified: `git replace`
substituting the catalog, keyring or subject tree (all git queries now pass
`--no-replace-objects` through one function); the dirty-tree exemption aimed by
a symlink at Ranex's own bookkeeping name — D4 reopened, needing no commit in
the default layout; a malformed committed catalog exiting 1, the code meaning
"gate not satisfied"; the trivial-command guard `/bin/true` walked past; a
v1-downgrade test green for the wrong reason.

## Next

1. **ADR-003, then SLICE-004 — isolate the runner *and its toolchain*.** Research
   first, and name all six sad paths: separating the signer does not by itself
   move `git` or the object store out of the worker's reach. Landlock ABI 8
   unprivileged (~75 rules, ~1.7 ms) but inode-bound — assert `st_nlink == 1`.
2. **No CI exists.** The six alarms below only sound when a person runs
   `uv run pytest -q`. Verified that a strict xfail turning green does fail the
   suite; nothing verifies that anyone ran it.
3. **Queued — Architecture Contract.** After the trust-boundary slices.

## Known limits, stated not fixed

- **Ranex trusts a repository, an environment and a toolchain the observed party
  owns.** Six false PASSes, one cause: `PYTHONPATH` retargets the bound binary
  (this defeats our own `uv run pytest -q`); `.git/info/exclude`, and an
  untracked *empty directory* no git query can see, hide a file the command
  reads; `filter.<n>.clean` hides an edit to a **tracked** file; overwriting a
  loose object substitutes a trust-root blob, because `cat-file` never checks a
  blob against the name asked for; a `git` shim on PATH deletes one argument to
  undo the fix above. ADR-001 sad path 30, ADR-002 sad paths 15–19.
- **`evidence.json` is not append-only.** Deleting a contradicting record, or one
  producer re-running a flaky command, erases the disagreement. ADR-001 s.p. 27.
- Approver identity is unauthenticated; the keyring admits lookalikes. SLICE-005.
- **No committed `governance/producers.yaml`**, so this repo cannot evaluate its
  own gate. Bootstrap, not a defect — but the loop is unclosed here.
