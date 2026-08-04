# ADR-009 — give the observation a repository, not just its files

**Status:** accepted
**Date:** 2026-08-04 (accepted same day, owner)
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md` — this
is SLICE-006's criterion 14, not a new slice; opening a second one is
the failure the working rule exists to prevent.
**Amends:** ADR-005, which materialises committed blobs and nothing else.
**Closes:** SLICE-006 criterion 14, recorded there as a strict `xfail`.

## Context and Problem Statement

ADR-005 built the observation from verified blobs alone. That was right about
*contents* and silent about *identity*: the sample has no `.git`, so a check
asking "what repository am I in, and what does it carry?" gets an error.

SLICE-006 made this concrete. With dependencies provisioned, 362 of this
repository's own tests pass inside the sealed environment and five fail, every
one for that single reason: three reach `governed_repository_root()`, one asks
whether a vendored file is tracked, one drives the CLI from a directory git
does not recognise. Ranex therefore cannot gate Ranex, which is the
confirmation ADR-007 named.

Relaxing them is refused. `_tracked_by_git` calls failing closed outside a
repository deliberate — "skipping this check would let an author manufacture
that escape hatch" — and weakening it to score a pass is the dart-and-bullseye
failure this project exists to catch. The defect is ours: the subject **is** a
commit, and we hand the command files that pretend otherwise.

## Decision Drivers

- A committed suite that legitimately asks git about itself must get a true
  answer, not an error.
- The subject digest must not change meaning; evidence already signed must
  remain comparable.
- Nothing the observed party wrote may enter the sample through this door —
  no history, no config, no hooks, no remotes, no ambient identity.
- Construction must be deterministic: the same subject builds the same tree.
- The command must not be able to use the repository to reach the network or
  the governed checkout.
- Cost must stay proportional to a test-suite run, not dominate it.

## Prior art

**Searched:** `gh api search/repositories` for "hermetic build sandbox",
"sandbox git worktree isolated build reproducible"; `gh api search/code` for
`leaveDotGit` within `NixOS/nixpkgs`, then the `pkgs/build-support/fetchgit`
tree; and `actions/checkout` for its checkout construction path.

- **nixpkgs solved this exact tension and its answer is a scrubbing pass.**
  `nix-prefetch-git` deletes `.git` by default and, under `--leave-dotGit`,
  calls `make_deterministic_repo`, which removes `logs/`, `hooks/`, `index`,
  `FETCH_HEAD`, `ORIG_HEAD`, `refs/remotes/origin/HEAD` and `config`, deletes
  every remote branch, and drops tags not reachable from HEAD. That list is
  the honest enumeration of what inside `.git` is non-deterministic or
  attacker-supplied, written by people who had to make it reproducible.
  <https://github.com/NixOS/nixpkgs/blob/ac62194c3917d5f474c1a844b6fd6da2db95077d/pkgs/build-support/fetchgit/nix-prefetch-git>
  License: MIT — compatible with this repository.
  Weakness: it *keeps history*, so the whole upstream past — every blob ever
  committed — remains reachable inside the sandbox, and it scrubs a
  pre-existing `.git` rather than building a fresh one, so anything the list
  forgets survives. Ranex creates the repository from nothing instead, which
  inverts the default: only what is deliberately added exists.
  Vendored: docs/adr/prior-art/ADR-009/nixpkgs-nix-prefetch-git.sh blob:7ba7fa568cd645086d64aed32facb06bd20dc240
- **actions/checkout is the mainstream "a job needs a real repository at
  exactly this commit" implementation**, and its git-directory helper is the
  decision procedure for reusing versus recreating one: it inspects the
  existing `.git`, tries `git clean -ffdx` and a reset, and recreates from
  scratch whenever anything is unexpected.
  <https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/src/git-directory-helper.ts>
  License: MIT — compatible with this repository.
  Weakness: every one of its choices optimises for *reuse* on a trusted
  runner — it prefers salvaging an existing checkout, keeps the remote and
  its credentials in the repository config, and fetches history by default.
  Reuse is the thing Ranex must not do: the sample is adversarial and
  disposable, so recreation is the only path, never the fallback.
  Vendored: docs/adr/prior-art/ADR-009/actions-checkout-git-directory-helper.ts blob:c73a1a404bb982601a8aa76b1f251f41efe5f23e
- **Rejected:** <https://github.com/git/git> — `git worktree add` is the
  obvious primitive, and wrong here. A linked worktree shares the governed repository's object store, so the
  observed command can write objects and refs into the tree that judges it;
  `committable_into` already treats a linked worktree as inside the
  repository for exactly this reason.
- **Rejected:** <https://github.com/util-linux/util-linux> — bind-mounting a
  read-only `.git` from the governed checkout. It gives the sample real history at near-zero cost and puts the object
  store the verdict depends on inside the blast radius of the command being
  measured. Cheaper, and it reopens what ADR-005 closed.

## Considered Options

1. **Leave it.** Honest but self-defeating: the checker that guards this
   project still cannot be run through this project, which is the SLICE-004
   failure one level up.
2. **Relax the five tests.** Rejected outright — their own comments call
   failing closed deliberate, and this would manufacture the escape hatch.
3. **Bind-mount or share the governed `.git`.** Rejected above.
4. **Build a fresh, single-commit repository around the verified tree,
   scrubbed of everything the observed party could have authored.** Chosen.

## Decision Outcome

In the context of a subject that is a commit and a sample that cannot say so,
we chose **to initialise a new repository inside the materialisation and
commit the verified tree as its only commit**, accepting that the sandbox
gains a repository with no history.

Measured here on 2026-08-04: re-initialising and committing the materialised
tree produced `1d8aa022265461852c42e554c01dfcdb4f977657`, **identical to the
governed checkout's `HEAD^{tree}`**, under a different commit id. That is the
crux — the subject digest is computed over the tree, so the identity binding
evidence does not move; only a question that had no answer now has one.

Fixed author, committer and timestamp make the construction deterministic. No
remote, no hooks, no ambient `~/.gitconfig`, and the `.git` is created empty
rather than scrubbed: the nixpkgs list is a record of what to *not add*.

### Consequences

- Good: a committed suite may ask git about itself and be told the truth.
- Good: Ranex can gate Ranex through the unchanged catalog command.
- Good: the subject digest is untouched, so prior evidence stays comparable.
- Good: creating from empty means an omission yields *less* in the sandbox,
  never more — the safe direction for a scrubbing mistake.
- Bad: the observed command gains a writable repository. It can commit, move
  HEAD, and rewrite that history; all of it dies with the materialisation,
  and the tracked-file fingerprint check still refuses a run that edited the
  observed files.
- Bad: `git log` in the sandbox shows one synthetic commit. A suite asserting
  real history will fail, and should — that history is not part of the
  subject.
- Bad: construction costs an `add` and a `commit` over the whole tree on
  every run.

### Confirmation

The slice must prove: the fresh tree hash equals the governed
`HEAD^{tree}`; the subject digest is unchanged from the pre-ADR value for the
same commit; the sample carries no remote, no hooks, no reflog, no stash and
no second commit; two runs of the same subject build byte-identical commit
ids; the sandbox's object store is not the governed one; and the five named
tests pass inside it. Then the end-to-end confirmation ADR-007 asked for —
`ranex run` executing `uv run pytest -q` against the real commit and
`gate evaluate` accepting the result — with the SLICE-006 `xfail` markers
removed rather than retained.

## Improvements on the prior art

1. **Created empty, not scrubbed.** nixpkgs deletes a list from an existing
   `.git`; anything the list forgets survives into the output. Ranex's `.git`
   starts with nothing in it, so the failure mode of an incomplete list is a
   missing convenience rather than a leaked attacker input.
2. **No history at all.** `--leave-dotGit` keeps every blob ever committed
   reachable inside the sandbox. One commit carrying one verified tree is the
   least that answers the question.
3. **Recreation is the only path.** actions/checkout treats "recreate" as the
   fallback after salvage fails; here it is the sole behaviour, because a
   reusable sample is a sample the previous run could have poisoned.
4. **No remote, therefore no credentials and no fetch.** checkout's helper
   configures the remote it will authenticate to. Ranex configures none, so
   there is nothing for the command to fetch from or steal.
5. **Deterministic by construction.** Fixed identity and timestamp make the
   commit id a function of the tree, so "same subject, same sample" is
   checkable rather than asserted.

## Architecture surface

`materialise_subject` gains the repository construction after the blobs are
written and before the sample is yielded. It stays in `cli/subject.py`
alongside the tree building it extends. Git is invoked through the pinned
toolchain with a `GIT_*`-free environment, as every other git call here is.
The verdict kernel is untouched: it is not taught that a repository exists,
and the subject digest keeps its current definition.

## Scope and threat delta

In scope: one commit, one branch, fixed identity, no remotes, no hooks, no
config beyond what the commit requires. Out: real history, tags, submodules,
signing of the synthetic commit, and any attempt to make `git log` in the
sandbox resemble upstream.

STRIDE movement: **I** narrows slightly — a suite that needed repository
identity no longer errors in a way that could be mistaken for a policy
refusal. Nothing else moves, because nothing crosses the boundary: no network
reachable, no governed object store shared, no credential present. The new
surface is a writable repository the command can vandalise, whose only
contents it already had, and which is deleted immediately afterwards.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Identity | fresh commit built from the verified tree | tree hash equals governed `HEAD^{tree}` |
| Determinism | same subject materialised twice | identical commit ids |
| Containment | command writes objects in the sandbox | governed object store unchanged |
| Isolation | command runs `git fetch` | no remote configured; nothing to fetch |
| Performance | full tree committed per run | small beside the suite it wraps |

## Reversibility

Door: two-way

The construction can be removed and the sample returns to a bare file tree.
What is not reversible is the *expectation*: once gates depend on suites that
query git, withdrawing this makes them unrunnable. The subject digest does
not move either way, so no evidence is invalidated by adding or removing it.

## Sad paths

| # | Input | Required behaviour |
|---|---|---|
| 1 | git absent from the pinned toolchain | refuse; never yield a sample that half-answers |
| 2 | `init` or `commit` fails | refuse and remove the materialisation |
| 3 | ambient `GIT_*` or `~/.gitconfig` names another repository or identity | ignored; construction uses explicit values only |
| 4 | a committed `.gitignore` would exclude tracked files from `add` | add with the ignore rules bypassed, or the sample's commit is not the subject |
| 5 | the subject legitimately carries a `.git`-named blob | refuse, as ADR-005 already refuses unrepresentable entries |
| 6 | command commits, resets, or deletes `.git` in the sandbox | permitted; the tracked-file fingerprint still refuses an edited observation |
| 7 | command configures a remote and fetches | denied by the run's network namespace, not by git |
| 8 | hooks planted in the sample's `.git` by the command | run in the sandbox only, and die with it |
| 9 | two runs of one subject | identical commit ids, or determinism is not established |
| 10 | a suite asserts real upstream history | **not caught** — it fails, and that is correct: the history is not the subject |
| 11 | a suite asserts its own commit id | **not caught** — the synthetic id is not the governed one |

## Test strategy

Levels: unit tests for the construction and each refusal below; security
tests that the governed object store is untouched when the command commits
inside the sample and that no remote, hook or reflog reaches it; a
determinism check over two materialisations. New files and exact test names
belong in the slice, not here.

`tests/security/test_slice004_hermetic_observation.py` remains the control
that ignored state never enters the subject, and is rerun with the sample's
`.git` present. `tests/integration/test_kernel_materialise_reference.py` is
the existing materialisation reference and gains the determinism case. The
end-to-end proof is the removal of both `xfail` markers in
`tests/e2e/test_gating_real_suite.py`. Red first: the five tests named above
fail inside the sample today, and that failure is the target.

## Code review checklist

- Is the sample's object store provably separate from the governed one?
- Can any ambient git variable or user config influence the construction?
- Is the commit's identity and timestamp fixed, and the id therefore stable?
- Does `add` see every tracked path, including ignored-but-committed ones?
- Is the subject digest computed exactly as before this change?
- Does a construction failure refuse rather than yield a partial sample?
- Do the docs still say the sandbox has no real history?

## More Information

Verified locally on 2026-08-04: cloning this repository, removing `.git`, and
re-initialising with a fixed identity and timestamp reproduced the tree
`1d8aa022265461852c42e554c01dfcdb4f977657`. The governed checkout reports the
same value for `HEAD^{tree}`, while the synthetic commit id was
`73ae7601c18c2284bbf5ca44f0e00507b7c4e7f4` — different commit, same tree. The five failing tests and their
single shared cause are recorded in
`docs/slices/SLICE-006-gating-a-real-test-suite.md` and pinned by the strict
`xfail` markers in `tests/e2e/test_gating_real_suite.py`.
