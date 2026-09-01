# ADR-044 — delegated host workflow operator surface

**Status:** accepted
**Date:** 2026-09-01
**Decision-makers:** repo owner
**Issue:** #64

## Context and Problem Statement

Strict-local confinement (namespaces + Landlock + seccomp + delegated
cgroup-v2, native C launcher) works on qualified hosts, but the operator
workflow to reach one does not exist as a product. The launcher lifecycle
verbs (`launcher-build`, `launcher-install`, `qualify`) live in
`src/ranex/cli/host_confinement.py`, reachable only via
`python -m ranex.cli.host_confinement` or a hidden argv[0] intercept at
`main.py:4192` before argparse — invisible in `--help`; success is silent.
The kernel `confinement_session` re-reads the qualification's
`delegation_identity` against the live cgroup (`host_confinement.py:4134-4160`),
so qualify and session must share ONE delegated cgroup or `E-C18-HOST-DRIFT`
fires; a plain terminal sits in `session.slice/vte-spawn-*.scope` with only
memory+pids — unqualified. The 2026-08-29 acceptance (13/13 v2/v3 arms,
`docs/MAP.md:962`) passed only inside a manually created delegated scope;
direct v1 failed, and refusal paths retain no evidence.

## Decision Drivers

- Issue #64 is a P0 production blocker: no documented public path exists.
- The frozen claim command in `governance/gates.yaml:19` must not change.
- ADR-037 already refused systemd as the kernel's process-ownership model;
  this decision must not contradict that boundary.
- Refusal paths must keep retaining no suite-level artifacts
  (`tests/contract/test_real_suite_entrypoint.py:558-603`, frozen).
- v1/v2/v3 pairing rules (`main.py:3739-3772`) must be enforced before any
  scope is entered, not after.
- Operators need one command, not a manual systemd runbook.

## Prior art

Searched: GitHub code search and installed-source inspection for
systemd-run scope delegation wrappers, cgroup-v2 delegation preconditions,
and transient-unit operator CLIs.

- https://github.com/systemd/systemd/blob/v257/man/systemd-run.xml
  grounds: `--scope` runs the command as a direct child of `systemd-run`
  itself with synchronous execution and exit-code propagation; `--collect`
  unloads failed transient units; `--same-dir` and `--setenv=` carry the
  caller's cwd and a sentinel variable into the scope.
  License: LGPL-2.1-or-later.
  Weakness: documents scope/service semantics but says nothing about which
  controllers a `Delegate=yes` scope actually propagates to the cgroup
  subtree, which the kernel probes must enforce themselves.
  Vendored: docs/adr/prior-art/ADR-044/systemd-v257-systemd-run.xml blob:20c0a5af2ea84ef1760934f7128f21ed6a18c998

- https://github.com/torvalds/linux/blob/v6.12/Documentation/admin-guide/cgroup-v2.rst
  grounds: delegation is granting write access to a directory and its
  `cgroup.procs`/`cgroup.threads`/`cgroup.subtree_control`; resources flow
  top-down, so a delegatee can only further restrict, never escape.
  License: GPL-2.0.
  Weakness: describes delegation semantics generally, not systemd's
  user-scope `Delegate=yes` behavior, and not which controllers a delegate
  receives — that is host state the wrapper must probe.
  Vendored: docs/adr/prior-art/ADR-044/linux-v6.12-cgroup-v2-delegation-excerpt.rst blob:cc934a14c1c8e03a436ca72a611d4147c07bdae0

- Rejected: https://github.com/systemd/systemd a broker-shaped transient
  `--user --service` wrapper forks output plumbing and unit lifecycle onto
  an operator flow whose product is the exit code, while `--scope` is
  already a direct child that propagates exit code, tty, cwd, and signals
  without a broker.
- Rejected: https://github.com/systemd/systemd having the kernel create its
  own delegation internally — an unprivileged terminal cannot create
  delegated cgroups (delegation is a top-down grant), and it would contradict
  ADR-037's refusal of systemd as a kernel ownership dependency.
- Rejected: https://github.com/anthonykewl20/ranex a docs-only runbook —
  the status quo IS the blocker; silent verbs and manual systemd
  choreography would remain the only path to a qualified host.

In-repo anchors (ordinary citations, not vendored):
`docs/adr/ADR-037-kill-safe-command-ownership.md`;
`governance/gates.yaml`.

## Considered Options

1. New public `ranex host` command group with one `strict-local` workflow
   verb that prechecks, re-execs into a `systemd-run --user --scope` it
   owns, and runs launcher-build/install/qualify/run inside that one scope.
2. Keep the hidden module CLI and only document the manual `systemd-run`
   runbook. Rejected: leaves the silent/hidden surface and choreography.
3. Move qualify/run ownership into the kernel session. Rejected:
   contradicts ADR-037 and breaks the wrapper-free execution invariant.
4. Option 1, chosen.

## Decision Outcome

Chosen: a public `ranex host` group in `build_parser()` — verbs `launcher-build`, `launcher-install`,
`host-probe`, `qualify` (defaults = the four canonical paths frozen in `governance/gates.yaml:19`),
`launcher-identity` (ranex-launcher-v1 digest/protocol identity check; no launcher `--version`
exists), and the ONE workflow verb `host strict-local` with required `--version` choice `v1`, `v2`, or `v3`, validated version-paired runtime selectors, and
`[--result-dir DIR] [--skip-build] -- <command>`. Phases: (A) PRECHECK outside any scope — named
fail-closed checks (pid1-systemd, systemd-run-present, user-session-bus, user-manager-alive
accepting `degraded`, not-root, build-closure, already-delegated → in-place mode); (B) ENTER —
re-exec inside `systemd-run --user --scope --quiet --collect --same-dir --property=Delegate=yes`
+ accounting properties + `RANEX_STRICT_LOCAL_IN_SCOPE=1` sentinel (recursion guard; the wrapper
returns the child's exit code); (C) LIFECYCLE in that ONE cgroup (the E-C18 fix): build → install
→ qualify ALWAYS fresh → `ranex run --confinement strict-local`, with BUILT/INSTALLED/QUALIFIED/
ENTERED-style lifecycle lines on stdout, `ERROR {code}: {detail}` + `HINT {action}` on stderr,
and EXIT_USAGE on pairing misuse before any scope entry; (D) ARTIFACTS — canonical report (schema
`ranex-host-strict-local-run-v1`), #58-pattern logs, honest-null binding, no wrapper junitxml.

### Consequences

- Good: one documented command reaches a qualified host; nothing silent.
- Good: qualify and session share one cgroup by construction — the E-C18
  drift class this issue was opened for cannot occur via stale identity.
- Good: refusal paths now retain wrapper-side report/log artifacts while
  the frozen suite-home refusal contract stays untouched.
- Bad: hosts without a systemd user manager are refused (named check),
  not silently degraded.
- Bad: the wrapper adds a re-exec layer; its failure modes are new sad
  paths, enumerated below.

### Confirmation

ADR-037 NON-CONTRADICTION: ADR-037 rejected systemd transient services as
the kernel's process-ownership model ("user-manager availability is not the
kernel's current host contract"). This decision gives systemd the
ENVIRONMENT BOUNDARY only — the delegated cgroup the qualification binds
to — never the process tree. The kernel session code gains zero new systemd
references, and the invariant "the kernel session must remain executable
under ANY delegated cgroup root, with or without this wrapper" is proven by
the in-place (already-delegated) mode working under a manually created
delegation, exactly as the 2026-08-29 acceptance showed.

## Improvements on the prior art

- systemd-run.xml does not say which controllers a `Delegate=yes` scope
  exposes; the `already-delegated` precheck probes the live cgroup's
  controller set (`cpu`, `memory`, `pids`) instead of trusting the man page.
- cgroup-v2.rst describes delegation generally; this decision pins the
  specific controller subset the kernel probes require and treats a subset
  match as sufficient for in-place mode.
- Neither source addresses recursion guarding on self-re-exec; the
  `RANEX_STRICT_LOCAL_IN_SCOPE=1` sentinel is this decision's addition.
- Neither source addresses artifact retention across success and refusal;
  this decision reuses the #58 `persist_stream`/`write_log_manifest`
  pattern (bounded, redacted, digest-bound) instead of inventing a new one.
- The manual runbook being replaced had no fresh-qualify-per-run guarantee;
  qualify is now always fresh so the report's delegation identity can
  never lag the scope it was bound to.
- Corrective-action HINT text exists in neither source nor the runbook;
  it is enforced by a contract test so the catalog cannot rot.

## Architecture surface

- New: `src/ranex/cli/host_workflow.py` — phases A-D, `CORRECTIVE_ACTIONS`
  catalog, `host-run-report.json` writer.
- Changed: `src/ranex/cli/main.py` — registers the `ranex host` group in
  `build_parser()`; the hidden argv[0] intercept stays so old paths work.
- Unchanged: `src/ranex/cli/host_confinement.py` (verbs re-exposed, not
  reimplemented), `governance/gates.yaml`, kernel session code.

## Scope and threat delta

- No new privilege: `systemd-run --user --scope` runs as the invoking uid,
  same as the manual runbook it replaces.
- New surface is a re-exec of the same binary plus one sentinel env var;
  the sentinel prevents unbounded recursion.
- The kernel's qualification/session identity matching is unchanged; the
  wrapper only ensures both sides observe the same delegated cgroup.
- Same-UID host peers remain outside the strict-local boundary, as before.

## Quality attributes

| attribute | effect |
|---|---|
| Discoverability | all lifecycle verbs appear in `ranex host --help` |
| Fail-closed | every precheck failure exits 1 before scope entry or build |
| Determinism | qualify always fresh; no stale identity reuse |
| Auditability | every run — confined, refused, or prereq-failed — leaves a canonical report |
| Honesty | `result_binding` is null when unpublished, never fabricated |

## Reversibility

Door: two-way

The `ranex host` parser group is additive and removable without touching
`host_confinement.py` or the kernel session; the hidden argv[0] intercept
can retire independently once the public surface is proven. Removing the
wrapper leaves in-place execution under any manual delegation exactly as
today.

## Sad paths

- Plain terminal in a non-delegated scope → precheck refusal before any build step runs.
- User manager stopped mid-run → systemd-run/exec failure recorded as a refused step, exit 1.
- Controllers missing inside the entered scope → qualify/E-C17 refusal; the report retains the scope controllers actually observed.
- Degraded user manager with a failed desktop unit (IBus) is accepted for delegation — quirk pinned: this sad path must still PASS (verified on the dev host).
- Sentinel env lost on re-exec → recursion guard fires; the wrapper refuses rather than re-entering a scope.
- Scope loses delegation mid-flight → kernel session raises `E-C18-HOST-DRIFT`; report outcome `refused` with the refusal code retained.
- Session result never published → `result_binding` stays honest `null`, never fabricated from a partial run.
- Build-closure drift on a foreign toolchain → `build-closure` check fails before scope entry, not mid-build.
- A refusal path still retains wrapper report and log artifacts while never writing into the suite artifact home.
- The wrapper never writes junitxml — the documented recipe passes `--junitxml=<result-dir>/junit.xml` through to pytest.
- Wrong v1/v2/v3 flag pairing → `EXIT_USAGE` before any scope entry, per the existing `RanexArgumentParser` rules.
- Running as root → `not-root` precheck refuses before build or scope entry.

## Test strategy

- `tests/contract/test_host_operator_surface.py` — asserts `ranex host
  --help` enumerates all six verbs, the `governance/gates.yaml:19` claim
  command string is byte-identical to today's frozen value, and
  `CORRECTIVE_ACTIONS` covers every `E-C17-*`/`E-C18*` code and named
  precheck.
- `tests/contract/test_docs_discipline.py` — governs this ADR itself
  (budgets, citations, vendored digests, NOTICE, section order).
- `tests/contract/test_real_suite_entrypoint.py` — the frozen
  refusal-writes-nothing suite-home contract must keep passing with the
  new command group present.
- SLICE-077 additionally owns integration and real-host end-to-end
  companions (precheck branches without a real manager; real v1/v2/v3 runs
  asserting the report schema, the shared cgroup root between qualification
  and command, and the BUILT/INSTALLED/QUALIFIED/CONFINED/ENTERED order);
  those files land with the implementation tranche and the suite is
  re-frozen then.

## Code review checklist

- [ ] `governance/gates.yaml:19` command string is byte-identical to before.
- [ ] `host_confinement.py` verbs are re-exposed, not reimplemented.
- [ ] Kernel session code has zero new systemd references.
- [ ] The sentinel check runs before any re-exec, not after.
- [ ] Qualify runs fresh every invocation — no cached identity reuse.
- [ ] `CORRECTIVE_ACTIONS` covers every refusal code introduced.
- [ ] Refusal paths write no artifact into the suite home.
- [ ] `result_binding` is null, never fabricated, when unpublished.
- [ ] `--help` lists all six `ranex host` verbs; wrapper never invokes `--junitxml` itself.

## More Information

- Issue #64 — the production blocker this decision opens.
- `docs/adr/ADR-037-kill-safe-command-ownership.md` — the ownership boundary
  this decision deliberately does not cross.
- `docs/MAP.md:962` — the 2026-08-29 manual-delegation acceptance evidence.
- `docs/adr/prior-art/ADR-044/NOTICE.md` — vendored source provenance and
  fetch-method disclosure.
