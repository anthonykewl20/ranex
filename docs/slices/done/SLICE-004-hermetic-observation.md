# SLICE-004 — isolate the runner and its toolchain

**Status:** done
**Opened:** 2026-08-02
**Closed:** 2026-08-02 — 298 green, 0 xfail. All nine done-criteria met and each
of the seven controls mutation-checked: deleted, the covering test watched go
red, restored. Mutation testing found one control with **no test binding to it
at all** — see "What mutation testing caught" below. Five further defects were
found and fixed during review, none of them anticipated by the plan.
**Reopened:** 2026-08-02 — the fix for defect 2 has never worked, on any Python
this project supports, and the test that claims to cover it does not call it.
See "Why this was reopened" below. The claim above is left standing, unedited,
because a closure record that quietly becomes true is worth nothing.
**Closed again:** 2026-08-03 — 322 green. Cleanup is version-independent and
proven against a real mode-0 directory; the hand-run mutation claim is replaced
by a tool whose output is recorded below, not summarised. Criterion 10 was
restated because as written it could not be met in one slice, and saying so is
the point of this reopening.
**ADR:** `docs/adr/ADR-005-hermetic-observation.md` — the researched decision,
including why a linked `git worktree` does not close D14 or D15, and why the
object-verification citation is containerd's content store rather than JGit.
**Closes:** the six strict xfails in
`tests/security/test_slice003_audit_defects.py` — D1, D11, D12, D14, D15, D17.

## The defect

Six reproductions, one sentence: **Ranex measures a tree, a toolchain and an
environment that the party being measured owns.**

Verified locally rather than assumed — git recomputes an object's hash when it
parses a **tree** and never when it streams a **blob**:

```
$ git cat-file blob HEAD:f.txt        # after overwriting the loose object
attacker
$ git ls-tree -r HEAD
100644 blob cf4c1d74c0b0123b7e0d760208a427db335e3d64	f.txt
```

The bytes and the name disagree and nothing notices. That single disagreement is
D15's defect and, compared rather than ignored, its fix.

## Design

Four parts of one mechanism, in the order `cmd_run` executes them.

1. **`src/ranex/cli/toolchain.py`** — a fixed list of system directories, each
   refused if the current user can write to it. `git` resolves from that list
   once, to an absolute path. `git()` in `main.py` takes that path instead of
   spelling `git` as a bare name.
2. **`src/ranex/cli/subject.py`** — `git ls-tree -r -z` over the subject commit
   gives (mode, type, oid, path) for every blob. Each blob is streamed, hashed
   as `sha1("blob " + length + NUL + bytes)`, compared against its oid, and
   written into a fresh `mkdtemp` directory with the mode the tree records. A
   mismatch, or an entry type not implemented, refuses. Nothing is observed
   against a partial tree.
3. **The trust root** reads its bytes through the same verified path, so the gate
   catalog and keyring can no longer be substituted underneath `cat-file`.
4. **The bound command** runs with cwd inside the materialisation and an
   environment built from empty: `PATH` (the pinned toolchain), `HOME` (scratch,
   inside the materialisation root), `TMPDIR`, `LANG`. Nothing inherited.
   `argv[0]` resolves on the pinned `PATH`, never on the operator's.

The materialisation is removed after the run, whatever the outcome.

## Done criteria

Each is met only when a test proves it, and the test has been mutation-checked:
the control deleted, the covering test watched go red, the control restored.

1. An ignored file present in the working tree cannot decide the bound command's
   outcome. (D12)
2. A `filter.<n>.clean` configured in `.git/config` cannot hide an edit to a
   tracked file from the observation. (D14)
3. A loose object overwritten so it does not hash to its own name is refused,
   with both object ids named, and the exit code is a refusal and not a verdict.
   (D15)
4. A `git` shim earlier on `PATH` than the real one does not answer any question
   the verdict rests on. (D17)
5. `PYTHONPATH` plus a `sitecustomize.py` cannot make a red suite report green.
   (D11)
6. A shadowed binary on the operator's `PATH` never executes and cannot satisfy
   the claim. (D1)
7. A toolchain directory writable by the current user is refused at construction.
8. The honest path still works end to end: a self-contained command runs in the
   materialisation, records evidence, and evaluates PASS.
9. Every one of 1–6 has a live control beside it, so "not a PASS" cannot be
   satisfied by a `run` that refuses everything.

## What mutation testing caught

The suite was green at 296 and **the pinned `git` had no test binding to it.**
Spelling `git` as a bare name again — undoing the control D17 exists for — left
every test passing.

The reason is worth keeping: the D17 reproduction uses a replace ref, and a
replace ref makes `cat-file` and `ls-tree` disagree, so the *blob verification*
refuses it whichever `git` answered. The reproduction proved the verification
worked and proved nothing about where `git` came from. One control was standing
in front of another and hiding it.

`test_a_git_shim_cannot_hide_a_dirty_tree_from_ranex` closes that: it shims
`git status`, which is a question about the working tree rather than about any
object, so there is no id to check the answer against. The only defence is that
the observed party did not choose who answered. Removing the pin now turns it
red.

## Five defects found in review, none of them in the plan

Found by three different means, which is the argument for using all three.

By auditing the implementer's own self-report:

1. **A writable executable inside a protected directory.** Refusing a writable
   *directory* stops an entry being created or replaced in it and says nothing
   about an entry that is itself writable — `/usr/bin/git` at mode 0777 can be
   overwritten in place. `refuse_writable_executable` closes it, on both the
   name found on the pinned route and whatever it resolves to.

By reading the code:

2. **A cleanup failure replaced the refusal that caused it.** Removing the
   materialisation happens in a `finally`, and an exception raised there
   *replaces* the propagating one, leaving the original reachable only as
   `__context__`, which nothing prints. An operator was told "cannot remove
   materialisation" for what was a substituted blob. Same defect class as D6 and
   D18 — a refusal reported under another refusal's wording — now fixed a fourth
   time.

By `ocr review`, both in `toolchain.py`:

3. **`os.access` probes the REAL uid; every guard around it reasons about
   `geteuid()`.** Under setuid/setgid those differ, so the check tested one
   identity and the error named another, and a directory writable only through
   the effective uid or an ACL passed. Now `effective_ids=True`, guarded on
   `os.supports_effective_ids`.
4. **A comment claimed a check the code did not perform** — that a symlink entry
   and its target were both inspected, when `Path.stat()` follows links and both
   calls saw one inode. Corrected rather than implemented: the reviewer's
   suggested `lstat` fix is wrong on Linux, where a symlink is always 0777 and
   `chmod` on one raises `NotImplementedError`, so it would refuse every
   `/bin/sh -> dash` on earth. Replacing a link means writing in its parent, and
   `pinned_directories` already refuses that. Exactly the ADR-004 defect class,
   one layer down: a stated control broader than the one that backs it.

By reviewing the fix for defect 2 against the project's own rules:

5. **`sys.exc_info()` was the wrong question.** It reports whatever is being
   handled *anywhere up the call stack*, so one caller sitting inside an
   `except` would make the happy path look like a failure and silently swallow a
   genuine cleanup error. Replaced with a local `completed` flag set only when
   the body and the caller's `with` block both finished.

## What this slice does not close

Stated here so that closing it cannot be read as more than it is.

- **The same-uid boundary.** The bound command shares a uid with Ranex, so an
  absolute path still reaches the governed repository, the operator's home and
  the journal. The materialisation is a hermeticity boundary, not a security
  boundary. Landlock is the control and it is the next slice — ABI 8,
  unprivileged, about 75 rules at about 1.7 ms, inode-bound, so `st_nlink == 1`
  must be asserted or a hard link re-grants read under an allowed path.
- **Gating a suite that needs installed dependencies.** `.venv` and
  `node_modules` are ignored, so they are not in the commit and not in the
  materialisation. This is a capability withdrawn on purpose; declared,
  digest-bound toolchain inputs are the slice that restores it.
- **`HOME` for Ranex's own git queries**, which is still inherited and still
  selects `~/.gitconfig`. Closed for the bound command only.
- **A process the bound command leaves behind outlives the run.** A `setsid`
  grandchild survives `subprocess.run` returning, so it is still executing while
  `gate evaluate` reads the evidence file and writes the journal. Reproduced
  during the reopening; disclosed in neither this slice's original close nor
  ADR-005's sad paths. ADR-006 s.p. 12 now records it and SLICE-005 closes it —
  confinement is inherited across `fork`, so the kill is tidiness, not the control.
- **There is no time limit on the bound command at all.** A command that never
  returns blocks Ranex for as long as it likes, and no verdict is ever reached.
  Also undisclosed until the reopening; ADR-006 s.p. 13 records it. Worth noting
  that in-toto has had a default `LINK_CMD_EXEC_TIMEOUT` of 10 seconds for years,
  so this is a gap against the mature prior art and not a hard problem.
- **A tree containing a symlink or a submodule cannot be observed at all.** The
  materialiser implements `100644` and `100755` and refuses every other entry
  type, which is ADR-005 sad path 16 working as decided — fail closed rather
  than silently skip an entry and observe a tree the commit does not describe.
  It is recorded here because it was not obvious when the slice was opened: this
  repository happens to carry neither, so the suite never noticed, and the cost
  only shows up on someone else's repository. Implementing symlinks means
  deciding what a link pointing out of the tree means to an observation, which
  is a decision and therefore an ADR, not a patch.

## Why this was reopened

Defect 2 above — "a cleanup failure replaced the refusal that caused it" — was
recorded as fixed. It is not, and never was.

`_remove_materialisation` hands `restore_permissions` to `shutil.rmtree` as its
error handler, and the handler calls `function(path)`. On Linux rmtree uses its
fd-based implementation and calls that handler with `func=os.open`, which takes a
second `flags` argument. The result is a `TypeError` — not an `OSError`, so it is
never converted to `SubjectError`; `materialise_subject`'s `finally` catches only
`SubjectError`, so it escapes **from the finally** and replaces the exception
already propagating. That is defect 2 verbatim, in the code written to close it.

Reproduced against this code on Python 3.11, 3.12, 3.13 and 3.14. Every one is
broken, so this is not a regression under a newer interpreter: the control has
never worked, and criterion-by-criterion closure was declared over it.

pytest solves the same problem in `_pytest.pathlib.on_rm_rf_error` and its
handling names our bug exactly — it declines to retry when `func` is `os.open`,
the single case we call blindly.

**The test is the more important failure.**
`test_a_cleanup_failure_does_not_replace_the_refusal_that_caused_it`
monkeypatches `_remove_materialisation` out and substitutes a stub raising
`SubjectError`. It therefore exercises the precedence logic in
`materialise_subject` and never the function it is named for — and could not have
caught this in any case, because the real failure raises the one exception type
already handled correctly. It is a test that proves less than it looks, which
this slice's own closing section named as the first thing to review.

The claimed mutation check cannot have covered this control either: deleting it
changes nothing, because no test reaches it.

Cost in practice: the bound command owns its scratch tree by design, so one
`chmod 000` on a directory inside it makes even an honest passing run exit 2,
record no evidence, and leave a scratch directory behind. It cannot manufacture
a false PASS — this is a denial of verdict, not a forged one.

**Additional done-criterion for the reopening, criterion 10.** First written as
"every error-recovery path in `src/ranex/` is executed by at least one test".
That cannot be met in one slice — there were 59 — and a criterion quietly left
unmet is how this slice failed the first time. Restated to what is actually
achievable and actually checked: **a control added from here cannot go unreached,
and the existing debt is measured, reduced and recorded.** `diff-cover` enforces
the first at every change; 15 of the 59 are now closed; 44 remain, named below.

### The closing evidence, pasted rather than summarised

`uv run mutmut run`, the whole package, on this commit:

```
2596 mutants — 🎉 1636 killed  🫥 73 no tests  ⏰ 7 timeout  🙁 880 survived
7m14s, 6.13 mutations/second
```

7 minutes is why this is a slice-closing check and not a per-push one, and it
replaces "each of the seven controls mutation-checked" — a sentence written by
the same actor who wrote the code, which is what missed the defect.

**The run is not a clean bill of health and must not be read as one.** 880
survivors, by module: `cli/main.py` 573 (plus 65 unreached — inflated, because
mutmut's selection excludes the e2e tests that exercise it), `slice_gate_loader`
52, `verdict.py` 47, `signing.py` 44, `subject.py` 44, `admission.py` 41,
`producer_keyring` 23, `toolchain.py` 17.

`verdict.py`'s 47 are the ones to read first: it is the kernel and it has zero
unreached mutants, so those survivors are real signal rather than an artefact of
selection. Three were inspected. One is a cosmetic default string and probably
equivalent. One replaces `gate_id=gate.gate_id` with `None` and survives. The
third inverts `item.exit_code == 0` to `!= 0` inside the contradiction check and
survives — **no test in this repository detects the kernel's success comparison
being inverted.** That is a gap in the tests, not a defect in behaviour, and it
is the next slice's opening question rather than something to hide behind a
green suite.

Measured before deciding how: **59 `raise` statements and `except` bodies in
`src/ranex/` are executed by no test at all.** Among them the kernel's own input
validation, five pinned-toolchain refusals, the materialiser's unsafe-path and
duplicate-entry guards, and one of the two branches of the journal's chain check.
Any of them could be as broken as `restore_permissions` was.

### Tools, searched rather than written

An ast-and-coverage checker for this was specified and then abandoned: it is a
worse version of two tools that already exist. Searched with `gh search repos`
and `gh repo view` for mutation testing and coverage ratchets.

- **Adopted — `diff-cover`** (Apache-2.0, 841 stars):
  <https://github.com/Bachmann1234/diff_cover>. Fails a change that adds lines no
  test executes. Run here against the working tree: it reports the new cleanup at
  100%, and the handler that reopened this slice was added by SLICE-004's own
  commit and never executed — so this would have failed that change on the day.
- **Adopted — `mutmut`** (BSD-3, 1371 stars): <https://github.com/boxed/mutmut>.
  Replaces this slice's hand-run "control deleted, test watched go red", which
  is a self-report by the same actor and is what missed the defect. Measured
  here: 2590 mutants in 15 s. Its `no tests` category is exactly the bespoke
  checker's output, and stronger — it proves a test *binds*, not that a line ran.
  Two incompatibilities found by running it, not by reading it: it copies only
  the paths it mutates, so the whole package must be named or imports break; and
  `tests/contract/` must be excluded, because those tests read the real
  repository, which does not exist inside mutmut's copied tree.
- **Rejected — `cosmic-ray`** (MIT, 646 stars):
  <https://github.com/sixty-north/cosmic-ray>. Equivalent capability, smaller
  adoption, and no reason to prefer it once mutmut was measured working here.
- **Rejected — `vulture`** (MIT, 4745 stars):
  <https://github.com/jendrikseipp/vulture>. Finds dead code, which is a
  different question: `restore_permissions` was reachable and wrong, not unused.
- **Rejected — `ocr`** (this repo already uses it for review): it reviewed the
  SLICE-004 diff and did not catch this. An AI reviewer is not a coverage
  instrument, and treating it as one is how the defect got through.

**What mutmut cannot tell us here, stated rather than left in a config comment.**
Its test selection excludes `tests/e2e/`, `test_slice003_bind_mount_identity.py`
and `test_keygen_key_confinement.py`. Those are precisely the tests that exercise
`cli/main.py`, so for that file — which holds 37 of the 44 refusals still
unreached — mutmut reports "no tests" for almost everything and its signal is
noise, not evidence. It binds the kernel, the toolchain, the materialiser, the
journal and the loaders. It does not bind the CLI. Anyone reading a green mutmut
run as "the CLI is covered" would be making this slice's original mistake again.

Two of those exclusions are mechanical: mutmut's in-process trampoline is absent
in the subprocesses e2e spawns, and it strips the docstrings some tests assert on.
The third is worth knowing on its own — mutating the keygen containment check can
write a generated **private key into the real repository**, because the copied
test resolves the governed root to the real one. Recorded as found by the
implementer; not independently reproduced here.

## The rewrite risk, named for review

The six reproductions cannot simply turn xpass. Each asserts a PASS is
*reachable* before asserting it must not be, so under the fix each refuses at
its setup assertion — a red-to-green transition that would leave the suite green
while proving nothing. Every one is therefore rewritten to assert the property
positively, in `tests/security/test_slice004_hermetic_observation.py`.

Two further tests change meaning with them and are re-aimed rather than left to
pass vacuously: the D2 committed symlink and the D8 hard link both reached
`argv[0]` through the ambient `PATH`, which no longer selects anything.

This rewrite is the most likely way this slice ships something that looks
finished and is not. It is the first thing to review.
