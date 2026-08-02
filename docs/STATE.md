# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** `docs/slices/SLICE-003-claim-command-binding.md` — criteria met,
close pending the decision below

## Where we stopped

250 green, 6 strict xfail, after six closing audits. Criteria 1–9 re-proven by
mutation — each control deleted from `src/` in turn, the covering test observed
going red.

- **The binding held.** No audit made a record satisfy a claim it does not name.
- **Five fixes, each mutation-verified.** `git replace` substituting the catalog,
  keyring or subject tree (all git queries now pass `--no-replace-objects`
  through one function); the dirty-tree exemption aimed by a symlink at Ranex's
  own bookkeeping name — D4 reopened, and needing no commit in the default
  layout; a malformed committed catalog exiting 1, the code meaning "gate not
  satisfied"; the trivial-command guard `/bin/true` walked past; a v1-downgrade
  test green for the wrong reason.

## Next

1. **Decide whether SLICE-003 closes.** Its own promise is met. Six reproduced
   fraudulent PASSes stand, all one root cause, all SLICE-004's — the
   disposition D1 got when SLICE-003 was opened on top of it.
2. **ADR-003, then SLICE-004 — isolate the runner *and its toolchain*.** Research
   first, and name all six sad paths: separating the signer does not by itself
   move `git` or the object store out of the worker's reach. Landlock ABI 8
   unprivileged (~75 rules, ~1.7 ms) but inode-bound — assert `st_nlink == 1`.
3. **Queued — Architecture Contract.** After the trust-boundary slices.

## Known limits, stated not fixed

- **Ranex trusts a repository, an environment and a toolchain the observed party
  owns.** Six PASSes, one cause: `PYTHONPATH` retargets the bound binary;
  `.git/info/exclude`, and an untracked *empty directory* that no git query can
  see at all, hide a file the command reads; `filter.<n>.clean` hides an edit to
  a **tracked** file; overwriting a loose object substitutes a trust-root blob,
  because `cat-file` never checks a blob against the name asked for; and a `git`
  shim on PATH deletes one argument to undo the fix above. ADR-001 sad path 30,
  ADR-002 sad paths 15–19. Strict xfails, each with a green control.
- **`evidence.json` is not append-only.** Deleting a contradicting record, or one
  producer re-running a flaky command, erases the disagreement. ADR-001 s.p. 27.
- Approver identity is unauthenticated; the keyring admits lookalikes. SLICE-005.
- **No committed `governance/producers.yaml`**, so this repo cannot evaluate its
  own gate. Bootstrap, not a defect — but the loop is unclosed here.
