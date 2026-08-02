# ADR-004 — the environment must not choose the repository being judged

**Status:** accepted
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** none — corrects ADR-002 sad path 14 and records the control that closed it

## Context and Problem Statement

ADR-002 sad path 14 answers `git replace` substituting a trust-root blob or the
subject commit with: "refuse — every git query passes `--no-replace-objects`,
injected once in the function they all go through". That reads as a closed door.
It was not one.

`--no-replace-objects` constrains object lookup *inside* a repository. It says
nothing about *which* repository is being asked, and `git()` passed `env=None` at
nine of its ten call sites, so every query inherited the caller's `GIT_*`. A
relative `GIT_DIR` therefore aimed the subject digest, the trust-root reads and
the scratch-index status at a repository the observed party owns. Reproduced end
to end with no forgery: genuine, correctly signed evidence produced in a shadow
tree passed the governed repository's gate, whose own committed check exits 1.

The row is not merely incomplete. It is an overclaim, and an overclaim in a sad
path is worse than a silence, because a sad-path table is what a reader consults
to learn what has been thought about.

## Decision Drivers

- ADR-002's answer is load-bearing: `--no-replace-objects` was added in response
  to a reproduced attack, and nothing said what it did not cover.
- Ranex is a measuring instrument. The party being measured must not be able to
  choose what the instrument reads, and the environment is an input it owns.
- Absence of a stated limit reads as absence of the limit.
- ADRs here are append-only. A wrong answer is corrected by a new decision, not
  by editing the old one until it looks like it was never wrong.

## Prior art

- **OpenSSH sshd builds the child's environment instead of inheriting it.**
  `do_setup_env` opens with `env = xcalloc(envsize, sizeof(char *)); env[0] =
  NULL;` — an empty array — and every variable the session gets is then set
  explicitly. The daemon's own environment is never handed to the user's shell.
  <https://github.com/openssh/openssh-portable/blob/53a80baaebda180f46e6e8571f3ff800e1f5c496/session.c>
  License: BSD-2-Clause (Ylönen's grant plus Friedl's two-clause terms in the
  file header) — vendorable into an MIT repository with the notice.
  Weakness: what the client supplies is copied in *first*, and everything
  restraining it is a name-based policy — `AcceptEnv` patterns, and
  `PermitUserEnvironment` with `permit_user_env_allowlist`. Safety rests on an
  allowlist of names an administrator can widen; OpenSSH ships the feature off by
  default precisely because enabling it lets a user bypass restrictions through
  mechanisms such as `LD_PRELOAD`. Not copied: an allowlist anyone can widen.
  Vendored: docs/adr/prior-art/ADR-004/openssh-session.c blob:c9415114db94f2b7bd6ea483665f53d7b36a6d87
- **sudo resets the environment and re-admits by allowlist.** Under `env_reset`,
  the default, `rebuild_env` seeds a fresh environment from `/etc/environment`
  and login.conf and pulls back only what the keep tables name; a separate
  `initial_checkenv_table` sanitises the *values* of `TZ`, `LC_*` and `TERM`,
  rejecting `%` and `/`, because a kept variable's value is itself an attack.
  <https://github.com/sudo-project/sudo/blob/c1a6140608d591b6992c6f8674ee2ce684a0481a/plugins/sudoers/env.c>
  License: ISC, declared by SPDX identifier in the file header.
  Weakness: the security lives entirely in what is *kept*. `PATH` is on the
  default keep list, `env_keep` is configurable, and `env_reset` itself can be
  switched off in sudoers, falling back to the weaker `initial_badenv_table`
  blacklist of `LD_*`, `IFS` and `_RLD*` — a list that only ever grew by
  incident. Not copied: keeping anything by name.
  Vendored: docs/adr/prior-art/ADR-004/sudo-env.c blob:95558e9edfa457f5b3a8e5665f5d80e3d21f59ce

## Considered Options

1. **Leave ADR-002 sad path 14 as written.** Rejected: the row states a refusal
   that did not hold, and a sad-path table is read as the record of what has been
   considered.
2. **Edit ADR-002 in place.** Rejected. ADRs are append-only, and its research
   exemption is pinned to its exact bytes, so an edit lapses the exemption and
   demands a research retrofit of an accepted decision.
3. **Copy git's `local_repo_env` list.** Rejected on licence and on merit —
   see below.
4. **Strip every `GIT_*` variable and take only explicit overrides, and record
   the correction in this ADR.** Chosen.

## Decision Outcome

Chosen: option 4. `git()` constructs the child environment — `os.environ` minus
every key beginning `GIT_`, then the caller's explicit overrides on top. The one
deliberate override, the scratch index in `uncommitted_paths`, passes
`GIT_INDEX_FILE` alone. The parameter was renamed `env` to `overrides` because
its meaning changed from "the whole environment" to "what the caller deliberately
sets", and a name that lied about that is how the next one of these arrives.

**ADR-002 sad path 14 is corrected to read:** *refuse the `git replace`
substitution specifically — every git query passes `--no-replace-objects`. That
flag bounds object lookup within a repository and does not decide which
repository is asked; the environment did, until ADR-004.*

### Consequences

- Good: the reproduced fraudulent PASS is closed, and a sad path now states what
  its control does not cover rather than implying it covers everything.
- Good: stripping a prefix needs no list to maintain, so a `GIT_*` variable added
  by a future git release is excluded the day it exists.
- Bad: a legitimate caller cannot influence Ranex's git queries through the
  environment any more. This is intended, and it would surprise someone using
  `GIT_CONFIG_GLOBAL` to point Ranex at a test configuration.
- Bad: the boundary is drawn at a *prefix*, which is a syntactic property. Git
  honours variables that do not carry it, and those still pass through.

### Confirmation

`tests/security/test_ambient_git_environment.py` holds the reproduction, the
honest-FAIL control and the honest-PASS control, and asserts the poisoned
evaluation returns *the same verdict* as the unpoisoned one — not merely "not a
PASS", which a crash would also satisfy. A separate test asserts `git()` passes
no `GIT_*` through while still delivering an explicit `GIT_INDEX_FILE`.

Mutation-checked rather than trusted to a green suite: restoring the inherited
environment turns the reproduction red again while both controls stay green.

## Improvements on the prior art

- Both cited implementations reset and then re-admit by name. We reset and
  re-admit **nothing**: the only variables that reach git are ones a call site
  passes explicitly, in code, in this repository. There is no configuration file
  that can widen it, which is the weakness both of them carry.
- sudo checks the *values* of variables it keeps, because a kept name is not a
  safe name. We keep no names, so that class does not arise here — and where we
  do accept a value, the scratch-index path, it is one this program computed.
- git solves this problem most directly of all: `local_repo_env` in
  `environment.c` enumerates the variables that bind a process to one repository,
  and `prepare_other_repo_env` clears them before running against another. It is
  **GPL-2.0-only**, so it is discussed and deliberately not vendored — copying it
  into this MIT repository would change what may be distributed. Reading it was
  still worth it, and its exception is the lesson: the loop skips
  `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` on purpose, so git's own
  scrubber lets configuration injection through to keep `-c` working across
  submodules. That is the exact vector this repository already carries as a
  strict xfail, left open upstream by design. A copied allowlist would have
  copied the hole.

## Architecture surface

`git()` in `src/ranex/cli/main.py` is the only place a git subprocess is
constructed; the sole other `subprocess.run` in `src/` is the bound command in
`cmd_run`, which is a different boundary with its own rules. No module gains a
dependency, no interface changes, and the kernel is untouched: `evaluate()`
neither knows nor asks about the environment.

## Scope and threat delta

In scope: the environment of the git queries **Ranex itself** makes. Out of
scope, and unchanged: the environment of the bound command, which is still
inherited minus the signing key and remains a strict xfail; repository-local
`.git/config`, which no git flag ignores; and every variable git honours that is
not `GIT_*`-prefixed, `HOME` above all, which still selects `~/.gitconfig`. The
delta is one reproduced false PASS closed and three named as still open.

## Quality attributes

- Determinism: the same tree now yields the same answer regardless of what the
  caller exported, which is the property the subject digest already claimed.
- Cost: one dict comprehension per git invocation, unmeasurable against a fork.
- Diagnosability: unchanged. Nothing about this is visible in output, which is
  itself a small argument for the test suite being where it is stated.

## Reversibility

Door: two-way

The change is one function and its single override call site. Reverting restores
the reproduced defect, so the test is what makes this hard to undo by accident —
which is the intended asymmetry.

## Sad paths

Enumerated by walking every way the environment can reach git, then every way
the boundary itself can be wrong.

| # | Input | Required behaviour |
|---|---|---|
| 1 | `GIT_DIR` naming another repository, absolute | refuse — stripped before git is invoked |
| 2 | `GIT_DIR` naming another repository, relative | refuse — this is the spelling that was reproduced, and the one an absolute path only appeared to close |
| 3 | `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` | refuse — all `GIT_*`, all stripped, no list to keep current |
| 4 | `GIT_INDEX_FILE` set by the caller | ignored — the only index git sees is the scratch one `uncommitted_paths` computes |
| 5 | `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` / `GIT_CONFIG_VALUE_n` injecting `filter.<n>.clean` | refuse — closes the env-injected spelling only, see row 6 |
| 6 | the same filter configured in `.git/config` instead | **not caught** — no git flag ignores repository-local config, so there is no better question to ask git; strict xfail, SLICE-005 |
| 7 | `GIT_NO_REPLACE_OBJECTS` unset or contradicted by the caller | refuse — stripped, and the flag is passed on the command line where the environment cannot reach it |
| 8 | `HOME` pointing at an attacker's `~/.gitconfig` | **not caught** — not `GIT_*`-prefixed, so this boundary does not see it |
| 9 | `PATH` selecting a `git` shim that drops the flag | **not caught** — the oracle is chosen by whoever launched Ranex; ADR-002 s.p. 18, SLICE-005 |
| 10 | the bound command's own environment | **out of scope** — a separate boundary, still inherited, strict xfail D11 |
| 11 | a future git release adding a new `GIT_*` variable | refuse — the prefix covers it without an edit |
| 12 | a future git release honouring a variable without the prefix | **not caught** — the boundary is syntactic, and this is what that costs |
| 13 | a call site needing a deliberate `GIT_*` value | supported — passed as an explicit override, in code, never from ambient state |
| 14 | the checker in `tests/` asking git while `GIT_DIR` is exported | refuse — it strips the same way, for the same reason |

## Test strategy

`tests/security/test_ambient_git_environment.py` carries the reproduction and its
two controls, and keeps the *relative* `GIT_DIR` spelling deliberately. The
absolute spelling is blocked today only because `committable_into` asks
`git -C /usr/bin rev-parse --git-common-dir`, receives the same substituted
answer it receives for the repository root, and concludes every binary is inside
the tree under observation. That is fail-closed by accident, and a test resting
on it would be a test of an accident.

`tests/security/test_slice003_audit_defects.py` holds the strict xfails for rows
6, 9 and 10, so the day one of those is closed the suite says so loudly instead
of quietly passing.

`tests/contract/test_docs_discipline.py` strips `GIT_*` around its own git
queries for the same reason, and its self-tests failed under an exported
`GIT_DIR` until it did — row 14 is not hypothetical.

Not tested: rows 8 and 12, because both are statements that a control does not
extend somewhere, and a test asserting the absence of a guarantee would be
theatre.

## Code review checklist

- Does any new git invocation bypass `git()`? Only `cmd_run`'s bound command may.
- Does any call site pass an override that came from ambient state rather than
  from a value this program computed?
- Does a new sad-path row claim a refusal broader than the control that backs it?
  That is the defect this ADR exists to correct.
- If a control is added here, does the row it strengthens say what it still
  misses?

## More Information

Corrects ADR-002 sad path 14. ADR-002 itself is unchanged and stays accepted:
one row's answer was too broad, not the decision it records. It is append-only,
and its research exemption is pinned to its bytes, so editing it would lapse the
exemption as well as break the rule.

The reproduction, the accidental block on the absolute spelling, and the three
vectors left open are recorded in commit `18d42d2ed`.
