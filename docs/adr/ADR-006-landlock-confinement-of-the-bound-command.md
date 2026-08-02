# ADR-006 — confine the bound command with Landlock, so the clean room has a lock

**Status:** proposed
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-005-landlock-confinement.md`

## Context and Problem Statement

`cmd_run` builds the bound command's environment from empty and resolves `argv[0]`
on a pinned toolchain (`src/ranex/cli/main.py:1322`), and that is where
confinement stops. The command runs under Ranex's own uid, so every control above
it holds only while the command declines to reach around it.

It need not. Measured here, not argued: the child reads
`/proc/<ranex-pid>/environ`, finds `RANEX_SIGNING_KEY`, reads the 0600 key it
names, and then signs any record for any claim, subject digest and exit code. Two
file reads, no privilege, no race — defeating ADR-002's trust root and ADR-005's
materialisation together, because a forger that never invokes `run` is never
measured. Same uid also gives execution inside Ranex's own `git status` via a
mid-run `~/.gitconfig` `core.fsmonitor` (reproduced), and lets a `setsid`
grandchild outlive `subprocess.run`. ADR-005 s.p. 12 and 13 deferred this.

## Decision Drivers

- The measured party must not be able to read the key that signs the measurement.
- A control the observed party can switch off, or that switches itself off on an
  old kernel, is decoration — this repo refused that shape for `--journal`.
- Whatever is chosen must not put an unpinned external binary in the path that
  decides a verdict; ADR-005 pinned the toolchain precisely to stop that.
- It must work unprivileged. Ranex running as root to drop privileges would add
  the risk it is trying to remove.
- Kernel 7.0.0 here reports Landlock ABI 8; 8 rules apply in 0.18 ms.

## Prior art

**Searched:** `gh search repos` for "landlock sandbox", "landlock python",
"sandbox untrusted command linux landlock seccomp", "in-toto attestation",
"witness attestation supply chain", "slsa provenance"; then `gh api search/code`
inside the attestation projects for `landlock`, `seccomp`, `bubblewrap`, `sandbox`.

- **go-landlock derives the ruleset from the running kernel and refuses when it
  cannot honour what was asked.** `restrict()` reads the ABI, validates every rule
  against the config before creating anything, and returns "missing kernel
  Landlock support" rather than enforcing something weaker. It also prices ABI 8:
  `useTsync := abi.version >= 8`, below which `no_new_privs` and `restrict_self`
  must be issued on every thread by hand.
  <https://github.com/landlock-lsm/go-landlock/blob/v0.9.0/landlock/restrict.go>
  License: MIT (Copyright 2021 Günther Noack) — vendorable into MIT with notice.
  Weakness: best-effort is a foot-gun and the code says so. `downgrade()` returns
  `v0, nil` — "Use ABI V0 (do nothing)" — so a single rule it cannot downgrade
  disables the sandbox entirely while `restrict()` reports success; an empty
  config takes the same path, `return nil // Success: Nothing to restrict.` That
  is the absence-blocks inversion this kernel refuses. Not copied: best-effort.
  Vendored: docs/adr/prior-art/ADR-006/go-landlock-restrict.go blob:34755a18d12ba505bacd1cd8b58fceb629d9c5bf
- **py-landlock is the same mechanism in this repository's language, and defaults
  to strict.** `Landlock(strict=True)` raises `CompatibilityError` instead of
  dropping an unsupported feature, and `apply()` sets `handled_access_fs =
  get_supported_fs(abi)` — every right the kernel knows, so nothing is permitted
  by having been left out of the mask.
  <https://github.com/SebastienWae/py-landlock/blob/v0.1.1/py_landlock/landlock.py>
  License: MIT — same terms.
  Weakness: `apply()` calls `restrict_self(ruleset_fd, None)` with no TSYNC flag
  and its own docstring scopes it to "the current thread", so sibling threads stay
  unconfined — the case go-landlock goes to trouble over. `set_no_new_privs()`
  also runs before the ruleset exists, so a failure leaves `no_new_privs` set and
  no domain. v0.1.1, one author, six stars: too thin to *be* the boundary, which
  is why it is read rather than depended on.
  Vendored: docs/adr/prior-art/ADR-006/py-landlock-landlock.py blob:0a3e98c2cfab07eacdf9cfd4a10a5142a6516f76
- **Rejected:** <https://github.com/Zouuup/landrun> — 2.2k stars, MIT, and it does
  exactly this job. Not adopted because it is a separate binary: the boundary
  would then be decided by an executable the pinned-toolchain rule does not cover.
- **Rejected:** <https://github.com/containers/bubblewrap> — strictly stronger, a
  mount namespace makes the repository not exist rather than merely unreadable.
  LGPL, needs a helper binary, and needs unprivileged user namespaces that this
  host's AppArmor denies except through bwrap's own profile. The named follow-on.
- **Rejected:** <https://github.com/in-toto/witness> and
  <https://github.com/in-toto/in-toto> — mature, and they already implement
  Ranex's attestation half to a published standard. Neither confines the command
  it attests to: the code search above returns zero hits in both. That gap is why
  this ADR exists, and adopting their formats is a separate decision.

## Considered Options

1. **A dedicated worker uid.** The classic answer, and the strongest against
   same-uid reads. Rejected for now: provisioning needs root or a setuid helper,
   so Ranex gains a privilege in order to drop one.
2. **Mount namespace via bubblewrap.** Strictly stronger; rejected as the *first*
   step for the licence, binary-dependency and host-policy reasons above.
3. **Shell out to `landrun`.** Same objection as 2, minus the licence problem.
4. **Depend on `py-landlock`.** Rejected: a v0.1.x single-author package cannot be
   the thing a verdict rests on. Read it, copy what holds.
5. **Apply Landlock in the child before `execve`, from a module in this repo,
   written against go-landlock's and py-landlock's designs.** Chosen.

## Decision Outcome

In the context of a bound command sharing Ranex's uid, facing a two-read theft of
the signing key that forges any verdict, we chose **an unprivileged Landlock
domain applied in the forked child after `PR_SET_NO_NEW_PRIVS` and before
`execve`**, to make the clean room a kernel-enforced boundary rather than an
observed one, accepting that Ranex becomes Linux-only and refuses where it cannot.

- **Handle every right the running ABI knows**, then grant back: read+execute on
  the pinned system directories, read+write+execute on the materialised tree,
  read+write no-execute on scratch `HOME` and `TMPDIR`, file-only rights on the
  `/dev` nodes a toolchain needs. TCP is handled with no rules, denying all of it.
- **Refuse rather than degrade**: ABI below 6, or any failing step, refuses — no
  best-effort mode and no flag to ask for one. `scoped` covers signals and
  abstract unix sockets; a timeout bounds the run, and the process group is killed.

### Consequences

- Good: the signing key stops being reachable, and with it the forge-anything
  path. The repo, the operator's home, the journal and the evidence file all
  become unreadable and unwritable to the measured party.
- Good: confinement is inherited across `fork` and `execve`, so a surviving
  grandchild is confined too — the process-group kill is tidiness, not the
  control.
- Bad: Ranex becomes Linux-only in fact, not merely in practice, and refuses on
  kernels below Landlock ABI 6. That is a real loss of reach, taken deliberately.
- Bad: no `/dev/shm`, so tooling that uses POSIX shared memory (some Python
  multiprocessing) will fail inside the room. A cost of the room, not a bug.
- Bad, and stated rather than hidden: this closes reads and writes. It does not
  close metadata syscalls, pathname unix sockets, UDP, or Ranex itself.

### Confirmation

`tests/security/test_slice004_hermetic_observation.py` gains the reproductions,
each asserting the property positively: the child cannot read the governed
repository, cannot read the operator's home, cannot read `/proc/<ranex>/environ`
even where `/proc` is granted, and cannot signal Ranex — while a control proves
an honest command still runs, since a refusal that refuses everything satisfies
"the attack failed" and governs nothing.

The controls that must fail closed get their own tests: a simulated ABI below the
floor, and each syscall in the sequence failing in turn, must each refuse without
spawning. Mutation-checked, not trusted to a green suite: every control deleted
in turn and the covering test watched go red.

## Improvements on the prior art

1. **No best-effort, in any form.** go-landlock's `downgrade()` turning the
   sandbox off while reporting success is the exact inversion this kernel refuses
   elsewhere, and py-landlock's `strict=True` is the posture we want made
   mandatory rather than default. An old kernel refuses; it never quietly widens.
2. **Handle the full mask, always.** Both sources compute the handled set from the
   ABI, and it is worth stating why: a right left out of `handled_access_fs` is
   permitted everywhere, so a hand-picked list silently grants what it forgot.
3. **Single-threaded by construction rather than by TSYNC.** py-landlock restricts
   the calling thread only; go-landlock pays for the general case. We need
   neither, because the domain is applied in a freshly forked child that has one
   thread — and the slice asserts that Ranex itself is single-threaded, so the
   assumption is checked rather than believed.
4. **The failure path is the specified path.** Both libraries treat setup failure
   as an error to return; here it is a refusal to execute, which is a different
   requirement: `no_new_privs` set with no domain must never reach `execve`.
5. **Confinement and attestation in one tool.** in-toto and witness attest to a
   command they do not confine; landrun confines one it does not attest to. The
   contribution is the join, and it is worth saying plainly that neither half is
   novel.

## Architecture surface

A new `src/ranex/cli/confinement_policy.py` holds the ABI probe, the ruleset
construction and the `restrict_self` sequence, exposing one callable suitable for
`preexec_fn`. `cmd_run` passes it, plus the timeout and the process-group kill, to
the single `subprocess.run` it already makes. `src/ranex/cli/subject.py` gains the
assertion that materialised files carry `st_nlink == 1`, because Landlock is
inode-bound and a second name would re-grant access under an allowed path.

The kernel is untouched. `evaluate()` still neither knows nor asks where the
command ran.

## Scope and threat delta

In scope: what the bound command may read, write, execute and signal. Out of
scope and explicitly still open: metadata syscalls (`stat`, `chmod`, `utime`,
`access`) on denied paths; `connect()` to a pathname unix socket whose path the
command already knows, which needs ABI 9; UDP, which needs ABI 10; System V IPC,
which Landlock does not mediate; and Ranex's own process, which must stay
unconfined because it writes the evidence and the journal. STRIDE letters moved:
**E** and **I** — elevation via key theft and disclosure of the operator's home
both close. Non-goal: resource exhaustion, which the timeout bounds and nothing
else does.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Confidentiality | bound command reads the producer's signing key | denied by the kernel; test asserts EACCES |
| Integrity | bound command writes into the governed repository | denied; verdict unaffected |
| Performance | ruleset construction per run | 8 rules in 0.18 ms measured; under 5 ms budget |
| Reliability | kernel without Landlock ABI 6 | refuses, exit 2, names the ABI it needs |

## Reversibility

Door: one-way

Not because the code is hard to remove — it is one callable and one argument. It
is one-way because every gate authored afterwards is authored against a confined
run, and reverting would re-widen what those gates permit while they keep passing.
That is the failure this repository exists to prevent, so the direction is worth
arguing about now rather than later.

## Sad paths

Enumerated by walking the setup sequence, then every resource the command can
reach that the sandbox is supposed to remove.

| # | Input | Required behaviour |
|---|---|---|
| 1 | kernel with no Landlock at all | refuse — never observe unconfined, and say which kernel feature is missing |
| 2 | Landlock present, ABI below the floor the policy needs | refuse — a domain missing signal scoping is not the domain this ADR claims |
| 3 | `landlock_create_ruleset`, `landlock_add_rule` or `landlock_restrict_self` fails | refuse — a partial domain must never reach `execve` |
| 4 | `PR_SET_NO_NEW_PRIVS` fails | refuse — and never leave it set with no domain behind it |
| 5 | a granted system directory does not exist on this host | skip that rule — `/lib64` is legitimately absent on some systems; the scratch root failing to open is a refusal |
| 6 | a rule on a device node carrying directory-only rights | refuse at construction — the kernel answers EINVAL and a silently dropped rule is a silently opened door |
| 7 | the command reads the governed repository by absolute path | denied |
| 8 | the command writes into the governed repository, the journal or the evidence file | denied |
| 9 | the command reads `/proc/<ranex-pid>/environ` for the signing-key path | denied, and still denied where `/proc` is granted for toolchain compatibility |
| 10 | the command reads the operator's home directly | denied |
| 11 | the command signals or ptraces Ranex | denied |
| 12 | the command leaves a background process behind | confined by inheritance; the process group is killed as well |
| 13 | the command never exits | refuse on the wall-clock timeout, record nothing |
| 14 | a materialised file with a second hard link | refuse — Landlock is inode-bound, so a second name re-grants access under an allowed path |
| 15 | Ranex running with more than one thread | refuse — `restrict_self` binds the calling thread, so a multithreaded parent makes the child's guarantee unprovable |
| 16 | the command connects to a pathname unix socket it already knows | **not caught** — ABI 9 adds the control; this kernel is 8, and the directory is unlistable but the path is guessable |
| 17 | the command calls `stat`, `chmod`, `utime` or `access` on a denied path | **not caught** — Landlock does not mediate these; names and sizes leak, contents do not |
| 18 | the command sends UDP, or uses System V IPC | **not caught** — UDP needs ABI 10 and Landlock never mediates SysV IPC |
| 19 | the command exhausts memory, disk or CPU | **not caught** — the timeout bounds wall clock and nothing bounds the rest |
| 20 | Ranex itself is compromised | **not caught** — it must write the journal, so it cannot be confined by the same domain |

## Test strategy

Levels: security tests for the reproductions, because each is an attack rather
than a unit; one e2e for the honest path; unit tests for the ABI floor and the
failure branches, which need no filesystem.

`tests/security/test_slice004_hermetic_observation.py` is extended rather than
duplicated: it already holds the same-uid reproductions this ADR closes, and
splitting them across two files would leave a reader unsure which one is current.
`tests/security/test_executable_path_confinement.py` and
`tests/security/test_repository_confinement.py` pin the containment rules that
remain load-bearing after confinement, so both are re-run against a confined
child to prove they did not quietly become vacuous.
`tests/e2e/test_run_produces_evidence.py` pins the honest path end to end: a
command that genuinely runs inside the domain, records, and evaluates PASS.

Sad paths 1–6 and 14–15 are unit-level and each maps to a named test in the
slice. Sad paths 7–13 are the security reproductions. Sad paths 16–20 are declared
uncatchable here and are deliberately **not** tested: a test asserting the absence
of a guarantee is theatre, and ADR-005 made the same call for its rows 12 and 13.

The new reproduction file is named in the slice, not here, because this
repository's checker resolves every `tests/` path an ADR mentions on disk — and a
path that does not exist yet is a promise, not a strategy.

Red-then-green: every reproduction must be observed failing against today's
unconfined `cmd_run` before the policy module exists.

## Code review checklist

- Does any failure in the setup sequence reach `execve`? That is the whole defect,
  and it is one missing `raise` away.
- Is `handled_access_fs` computed from the ABI, or hand-listed? A hand-listed mask
  permits everything it forgot.
- Is there any path — flag, environment variable, kernel version — by which the
  domain is applied more weakly rather than refused?
- Do the reproductions fail when the policy is removed? A test that passes both
  ways is what this slice is most likely to ship.
- Does the granted set still contain anything the command does not need? Every
  entry is a hole that was argued for once and then inherited.
- Is Ranex still single-threaded where it forks, and is that asserted rather than
  assumed?

## More Information

Closes ADR-005 sad paths 12 and 13, which named this boundary and deferred it.
ADR-004 s.p. 8 (`HOME` selecting a `~/.gitconfig` for Ranex's own queries) is
**not** closed by this and is made sharper by it: the `core.fsmonitor` execution
described above is that path, now reproduced.

Open, and each its own decision: bubblewrap or a worker uid to close rows 16–19;
adopting in-toto's attestation format in place of the bespoke evidence record;
and the journal's own tamper-evidence, which is the slice after this one.
