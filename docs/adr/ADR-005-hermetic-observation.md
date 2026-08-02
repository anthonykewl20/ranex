# ADR-005 — observe a materialised commit, not the tree the worker is standing in

**Status:** accepted
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** docs/slices/SLICE-004-hermetic-observation.md

## Context and Problem Statement

Six strict xfails in `tests/security/test_slice003_audit_defects.py` reproduce a
PASS, or an unrefused substitution, that no forgery was needed to obtain. They
look like six defects and are two:

1. **The tree observed is not the tree HEAD names.** An ignored file decides the
   bound command's outcome (D12); a `filter.<n>.clean` in `.git/config` makes
   `git status` report a modified tracked file as clean (D14).
2. **The toolchain and its inputs are chosen by the measured party.** A shadowed
   binary on `PATH` satisfies the claim (D1); `PYTHONPATH` rewrites what the
   bound interpreter does (D11); a `git` shim answers every question the verdict
   rests on (D17); an overwritten loose object substitutes the catalog (D15).

Each xfail reason arrives at the same two fixes: observe a pristine checkout of
the subject commit, and stop inheriting what the observed party owns. ADR-004
closed this for Ranex's *own* git queries and said the bound command's
environment was still inherited. This is that boundary.

## Decision Drivers

- Ranex is a measuring instrument; the measured party must not choose the
  instrument, its inputs, or the sample.
- `git status` cannot be made to answer honestly here. An untracked *empty
  directory* has no representation in git at all, so no flag reaches it.
- Verified locally, not taken on trust: git recomputes the hash when it parses a
  **tree** (`error: hash mismatch`, `fatal: not a tree object`) and never when it
  streams a **blob** — `cat-file` served substituted bytes while `ls-tree` still
  reported the honest object id. The disagreement is both the defect and its fix.
- A control that can be switched off from the command line is decoration; this
  repo already refused that shape for `--journal` and for `--ref`.

## Prior art

- **Bazel builds an exec root holding exactly the declared inputs, and deletes
  whatever else is in it.** `SymlinkedSandboxedSpawn.filterInputsAndDirsToCreate`
  hands a reused sandbox to `SandboxHelpers.cleanExisting` — "Delete anything
  unnecessary" — so an action can never see a file that was not declared. The
  action's environment is a constructor argument, not the client's.
  <https://github.com/bazelbuild/bazel/blob/c8217fdd2f20e4a061122c0af0417380d09e9480/src/main/java/com/google/devtools/build/lib/sandbox/SymlinkedSandboxedSpawn.java>
  License: Apache-2.0, declared in the file header — vendorable into MIT with the
  notice and attribution preserved.
  Weakness: `copyFile` is `target.createSymbolicLink(source)`. The sandbox's
  "copy" is a link into the real source tree, so an action can write through it,
  and a source file edited mid-action changes what the action sees. Sandboxes are
  also *stashed and reused* (`SandboxStash`), which makes correctness depend on
  `cleanExisting` being exhaustive. This is a hermeticity mechanism, not an
  adversarial boundary. Not copied: symlinking inputs, and reuse.
  Vendored: docs/adr/prior-art/ADR-005/bazel-SymlinkedSandboxedSpawn.java blob:770f3caf7197575ce49f6308d6efc0c9b100030f
- **containerd's content store refuses bytes that do not hash to the name they
  were asked for.** `writer.Commit` digests every byte as it is written and ends
  with `if expected != "" && expected != dgst` — the blob is admitted under a
  name only once the bytes have proved they own it, and the file is `Rename`d
  into place afterwards, never before.
  <https://github.com/containerd/containerd/blob/88bf19b2105c8b17560993bee28a01ddc2f97182/content/local/writer.go>
  License: Apache-2.0, declared in the file header — same terms as above.
  Weakness: both checks are skipped when nothing was declared. `expected != ""`
  makes an empty digest an acceptance, and `size > 0 && size != fi.Size()` does
  the same for a zero size, so an unstated expectation is satisfied by anything.
  That is precisely the "absence blocks" inversion this repository's kernel
  refuses. Not copied: making the check conditional on a declaration existing.
  Vendored: docs/adr/prior-art/ADR-005/containerd-content-writer.go blob:0cd8f2d04bbd9e3d2bfbac1973d25a9ccaafba5f

## Considered Options

1. **Ask git a better question.** Rejected, and the xfails already bound it:
   `--ignored` refuses every real repository, an untracked empty directory is
   invisible at every `-u` level, and no flag makes git ignore `.git/config`.
2. **`git worktree add` a second checkout.** Rejected. A linked worktree shares
   the object store and the config of the repository it came from, so D14 and
   D15 follow it across unchanged.
3. **Strip the dangerous environment variables by name.** Rejected — a denylist
   against an attacker who picks the name. ADR-004 refused this already.
4. **Materialise the subject commit from verified bytes, construct the
   environment from empty, and pin the toolchain.** Chosen.

## Decision Outcome

Chosen: option 4, as one mechanism in four parts.

- **Materialise.** `git ls-tree -r` over the subject commit yields object ids git
  verified when it parsed the tree. Every blob is streamed, hashed as
  `sha1("blob " + length + NUL + bytes)`, compared against that id, and written
  into a scratch directory outside the governed repository. A mismatch refuses.
  The result carries no `.git`, so no config, no `info/exclude`, no
  `info/attributes` and no object store, and nothing untracked can pre-exist.
- **Verify the trust root the same way.** The gate catalog and keyring bytes come
  from the verified tree, not from `cat-file` alone.
- **Construct the environment.** The bound command receives `PATH`, `HOME`,
  `TMPDIR` and `LANG` — built, not inherited. Nothing else crosses.
- **Pin the toolchain.** `PATH` is a fixed list of system directories, each
  refused if it is group- or world-writable, or writable by a non-root Ranex.
  Ranex resolves its own `git` from that list once, to an absolute path.

### Consequences

- Good: six reproduced attacks close on one mechanism rather than six patches,
  and the dirty-tree question stops being load-bearing — a clean tree is now an
  operator courtesy, not the guarantee the verdict rests on.
- Good: the subject digest finally describes what the command saw. That was
  asserted from SLICE-001 and was not true until now.
- **Bad, and the largest cost here: a hermetic tree has no installed
  dependencies.** `.venv`, `node_modules` and `__pycache__` are ignored, so they
  are not in the commit and not in the materialisation. Until a declared,
  digest-bound toolchain input exists, Ranex can only gate commands that are
  self-contained — which does not include this repository's own `uv run pytest`.
  Named as the next slice, not waved at.
- Bad: the bound command no longer sees the operator's `HOME`, so credentials,
  caches and tool settings configured there are gone. Intended, and surprising.
- Bad: materialising costs a full tree write per run, where before there was none.

### Confirmation

`tests/security/test_slice004_hermetic_observation.py` carries the six
reproductions, re-aimed. Each was a strict xfail asserting only that a PASS was
reachable; each now asserts the property positively — the honest red suite is
reported red, the substitution is refused, the shadowed binary never executes.

Each keeps a control alongside it, because a refusal that refuses everything
satisfies "not a PASS" and governs nothing.

Mutation-checked, not trusted to a green suite: each control deleted in turn, the
covering test watched go red, restored. Not a formality — it found the pinned
`git` had **no test binding to it at all**. Removing it left the suite green,
because D17 uses a replace ref that the blob verification refuses whichever `git`
answered: one control stood in front of another and hid it. Shimming `git status`
— a working-tree question with no object id to check — is what binds the pin.

## Improvements on the prior art

- Bazel symlinks declared inputs into the sandbox; we copy the bytes. A symlink
  leaves the observed party owning the file the observation reads, which is the
  exact defect D14 reproduces one layer up. Copying costs a tree write per run
  and is what makes the materialisation an *observation* rather than a view.
- Bazel reuses and stashes sandboxes, so hermeticity rests on the cleaner being
  exhaustive. We build a fresh directory per run and remove it, so there is no
  residue for a cleaner to miss and no cleaner to get wrong.
- containerd verifies against `expected` only when `expected` is non-empty. Here
  the object id is never optional: it comes from a tree git verified, and a blob
  with no id to check against cannot arise. Absence blocks, so there is no
  unstated-expectation branch to skip.
- git's `checkout-index` and `archive` materialise a tree properly and are what a
  mature implementation would reuse. git is **GPL-2.0-only**, so it was read and
  is deliberately not vendored into this MIT repository — the same call ADR-004
  made about `local_repo_env`. Reading it was still the most useful hour: it is
  why the materialiser writes modes from the tree rather than from the umask.
- JGit was fetched as the object-verification citation and dropped after reading
  it. `UnpackedObject` raises on a bad header, a negative size, trailing garbage
  and a short inflate, and never recomputes the object id — the same gap as git's
  C, not a fix for it. The negative result is recorded in the NOTICE.

## Architecture surface

A new `src/ranex/cli/subject.py` holds materialisation and blob verification; a
new `src/ranex/cli/toolchain.py` holds the pinned PATH, the writability refusal
and the resolved `git`. `git()` in `main.py` takes the resolved binary instead of
the bare name. `cmd_run` gains the materialise-run-remove sequence around the
spawn it already does.

The kernel is untouched. `evaluate()` still neither knows nor asks where the
command ran, which is the property that keeps this reviewable.

## Scope and threat delta

In scope: what the bound command can see and be told, and which binary answers
Ranex's questions. Out of scope and explicitly still open: the bound command
shares a uid with Ranex, so absolute paths still reach the governed repository,
the operator's home and the journal. **The materialisation is a hermeticity
boundary, not a security boundary** — Bazel's own caveat, and true here for the
same reason. Landlock (ABI 8, unprivileged, about 75 rules at about 1.7 ms, and
inode-bound so `st_nlink == 1` must be asserted) is what would make it one, and
it is the slice after next. The delta is six reproductions closed and one
long-standing capability — gating a suite that needs installed dependencies —
knowingly withdrawn until that toolchain input exists.

## Quality attributes

- Determinism: the observed tree is now a pure function of the subject commit.
  Two runs of one commit on two machines see byte-identical inputs.
- Cost: one tree write and one sha1 per tracked file per run. On this repository,
  about 40 ms — against a test suite, unmeasurable; against a trivial bound
  command, the dominant cost, and honest about it.
- Diagnosability: a verification refusal names the path and both object ids, so
  an operator can tell a poisoned object from a bug in the materialiser.

## Reversibility

Door: one-way

Not because the code is hard to revert — it is one sequence in `cmd_run`. It is
one-way because every gate authored after it is authored against a hermetic
tree: no ambient tools, no `HOME`, no ignored files. Reverting would silently
re-widen what those gates see while they keep passing, which is the failure this
repository exists to prevent. The direction is worth arguing about now.

## Sad paths

Enumerated by walking every input to the observation, then every way the
materialiser itself can be wrong.

| # | Input | Required behaviour |
|---|---|---|
| 1 | an ignored file that decides the bound command's outcome | refuse — it is not in the commit, so it is not in the materialisation (D12) |
| 2 | an untracked empty directory, invisible to every git question | refuse — same reason; nothing untracked is materialised |
| 3 | `filter.<n>.clean` in `.git/config` hiding a modified tracked file | refuse — the materialisation carries the committed bytes, and no `.git` follows it (D14) |
| 4 | a loose object overwritten so it does not hash to its own name | refuse — blob bytes are checked against the id the verified tree carries (D15) |
| 5 | a poisoned **tree** object | refuse — git already recomputes this on parse; confirmed locally, not assumed |
| 6 | `git replace` substituting a blob or the subject commit | refuse — `--no-replace-objects` still passed, now to a pinned binary (ADR-002 s.p. 14, ADR-004) |
| 7 | a `git` shim earlier on `PATH` than the real one | refuse — Ranex resolves `git` from the pinned toolchain, never from ambient `PATH` (D17) |
| 8 | `PYTHONPATH` plus a `sitecustomize.py` outside the tree | refuse — the child's environment is built from empty (D11) |
| 9 | `NODE_OPTIONS`, `RUBYOPT`, `PERL5OPT`, `LD_PRELOAD`, and the next one nobody has named | refuse — not a denylist; nothing is inherited, so a new name needs no edit |
| 10 | a shadowed `pytest` on the operator's `PATH` | refuse — `argv[0]` resolves on the pinned toolchain, and the shadow never executes (D1) |
| 11 | a toolchain directory the current user can write to | refuse at construction — a pinned path the observed party can edit is not pinned |
| 12 | the bound command reading the governed repository by absolute path | **not caught** — same uid; this is a hermeticity boundary, not a security one |
| 13 | the bound command writing into the governed repository | **not caught** — same reason; Landlock is the control, and it is not in this slice |
| 14 | a bound command needing `.venv` or `node_modules` | **refused, and this is a withdrawal of capability** — declared toolchain inputs are the next slice |
| 15 | `TMPDIR` chosen by the operator, pointing somewhere hostile | refuse — ambient `TMPDIR` is never consulted; the root is `mkdtemp` under `/tmp` then `/var/tmp`, resolved, and refused if it lands inside the governed repository |
| 16 | a commit carrying a symlink, a submodule, or a mode git records and we do not | refuse — an entry type the materialiser does not implement is a refusal, never a silent skip. **This makes such a repository unobservable**, which is a real cost and the right default |
| 17 | the materialiser failing part-way | refuse — nothing is observed against a partial tree, and the scratch directory is removed |
| 18 | `HOME` inside the materialisation being written by the command | allowed — it is scratch, discarded with the tree, and outside the subject |
| 19 | Ranex running as root, where every directory is writable | **not caught** — the pin cannot improve on a uid that owns the toolchain, and refusing would only stop legitimate root use. Row 11 is skipped under euid 0, deliberately |

## Test strategy

`tests/security/test_slice004_hermetic_observation.py` is the new file, and it
holds the six re-aimed reproductions plus a control for each. The controls are
load-bearing: without them "the attack did not PASS" is satisfied by a `run` that
refuses everything, which is a broken loop rather than a governed one.

The six previously lived as strict xfails in
`tests/security/test_slice003_audit_defects.py`. Their bodies asserted a PASS was
*reachable* before asserting it must not be, so none of them can simply turn
xpass — under the fix they refuse at the setup assertion instead, which would
leave a green suite proving nothing. Each is therefore rewritten to assert the
property positively and the markers removed. That rewrite is the risk in this
slice and is called out for review rather than buried.

Two existing tests change meaning and are re-aimed with them: the D2 committed
symlink and the D8 hard link both reached `argv[0]` through the ambient `PATH`,
which no longer selects anything. Left alone they would keep passing while
reproducing nothing — the "tests that prove less than they look" failure this
repository has shipped twice.

`tests/security/test_ambient_git_environment.py` keeps the ADR-004 reproduction
and gains one assertion: the pinned `git` is used even when `PATH` names another.

`tests/e2e/test_run_produces_evidence.py` pins the honest path end to end — a
command that genuinely runs in the materialisation, records, and evaluates PASS.

Not tested: sad paths 12 and 13, because each states that a control does not
extend somewhere. A test asserting the absence of a guarantee is theatre.

## Code review checklist

- Does anything reach the bound command's environment that was not built here?
  A single `os.environ` read in that path is the whole defect returning.
- Is every blob checked against the id the tree carries, or only the ones a test
  happened to name?
- Does a refusal in the materialiser leave a partial tree observable?
- Does any git invocation still spell `git` as a bare name?
- Do the rewritten reproductions still fail when the fix is removed? A test that
  passes both ways is the thing this slice is most likely to ship.

## More Information

Closes the six strict xfails ADR-001 s.p. 17, ADR-002 s.p. 18 and ADR-004 s.p. 6,
9 and 10 deferred to SLICE-004. ADR-004 s.p. 8 (`HOME` selecting a
`~/.gitconfig`) is closed for the bound command and remains open for Ranex's own
queries, which still inherit `HOME`.

Not closed, and deliberately: the same-uid boundary, and gating a suite that
needs installed dependencies. Both are named above with the slice that owns them.
