# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-02
**Phase:** kernel — evidence loop
**Active slice:** none. SLICE-004 waits on `docs/adr/ADR-005-*.md`.

## Where we stopped

273 green, 6 strict xfail, and CI now runs them. Each control below was
mutation-checked: deleted, the covering test watched go red, restored.
**A PASS was reachable through the environment.** `git()` inherited ambient
`GIT_*`, so a *relative* `GIT_DIR` aimed every query Ranex makes at a repository
the worker owns. Reproduced with no forgery: honest evidence from a shadow tree
passed the governed repository's gate. An absolute `GIT_DIR` was blocked only by
luck — `committable_into` asked git from `/usr/bin` and got the same answer —
which is not a control. `git()` now builds a `GIT_*`-free environment. Also closed: `--journal ""` silently disabled the journal; a non-SQLite journal
exited 1, the code meaning "gate not satisfied"; `journal verify` did not exist,
then reported `chain=verified` for a journal that was not there, creating it. In
the research rule, one URL cited twice counted as two, a branch URL with a 40-hex
string in its query counted as pinned, and vendored files went untracked.

## Next

1. **ADR-005, then SLICE-004 — isolate the runner *and its toolchain*.** Name all
   six sad paths: separating the signer does not move `git` or the object store
   out of the worker's reach. Landlock ABI 8 unprivileged (~75 rules, ~1.7 ms) but
   inode-bound — assert `st_nlink == 1`. Numbering moved twice: ADR-003 is the
   research rule, ADR-004 the environment boundary.
2. **Open: should `gate evaluate` verify the chain before appending?** It appends
   to a tampered journal without complaint.

## Known limits, stated not fixed

- **Ranex still trusts a repository, an environment and a toolchain the observed
  party owns.** `PYTHONPATH` retargets the bound binary; `.git/info/exclude` and an
  untracked *empty directory* hide a file the command reads; `filter.<n>.clean` in
  `.git/config` hides an edit to a **tracked** file, and no git flag ignores
  repository-local config; a poisoned loose object substitutes a trust-root blob; a
  `git` shim on PATH undoes the fix above. ADR-001 s.p. 30, ADR-004 s.p. 6–12.
- **Vendoring proves bytes were obtained, not that they came from the cited URL**
  (ADR-003 s.p. 13); **`evidence.json` is not append-only** (ADR-001 s.p. 27);
  approver identity is unauthenticated and the keyring admits lookalikes
  (SLICE-005); and with no committed `governance/producers.yaml` this repo cannot
  evaluate its own gate — bootstrap, not a defect.
