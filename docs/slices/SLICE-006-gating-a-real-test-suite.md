# SLICE-006 — gate a real test suite

**Status:** open
**Opened:** 2026-08-03 — parked for SLICE-007, unparked 2026-08-04 by owner decision
**ADR:** `docs/adr/ADR-007-dependency-provisioning-for-gated-suites.md` — the
researched decision, including why the lock is derived under fixed resolution
inputs and why dependencies remain trusted code after every hash matches.
**Closes:** ADR-005 sad path 14 and ADR-007 sad paths 1–16.

## The defect

Ranex materialises only committed blobs. That is the right subject and an
incomplete runtime: `.venv` and `node_modules` are ignored, so no committed tree
contains them. `governance/gates.yaml` binds `tests-executed` to `uv run pytest
-q`, but this host's `uv` is also user-writable and outside the pinned system
path. Ranex therefore cannot run its own bound command in its own clean room.

This is product-stopping, not ergonomic. The checker that guards Ranex cannot be
run through Ranex, which is how a broken cleanup control survived the suite that
was supposed to prove it. Restoring dependency-bearing commands is the active
work; ADR-006 remains proposed, but its Landlock slice is deliberately unopened.

## Design

One use case, with a hard boundary between preparation and measurement.

1. **Provision.** `ranex deps fetch` is the only networked phase. It resolves a
   clean copy of the committed manifest with no lock present, using an
   operator-pinned uv executable, Python target, index set and resolution epoch.
   Generated and committed locks must match byte-for-byte. Only SHA-256-addressed
   wheels enter the store; sdists, VCS and local sources refuse.
2. **Approve.** Compare the derived package set with the last approved subject.
   Render additions, removals and version changes, or the full set when there is
   no baseline. The approver explicitly accepts that exact delta before the run.
3. **Assemble.** Build a fresh environment from verified store entries, then
   make it read-only. The uv executable used by the unchanged gate command is
   itself selected by an operator-pinned digest, never from ambient `PATH`.
4. **Run.** Add the environment's `bin` only to the pinned route and set
   `UV_PROJECT_ENVIRONMENT`, `UV_NO_SYNC=1` and `UV_OFFLINE=1`. The subject argv
   remains exactly `uv run pytest -q`; the command cannot sync, build or fetch.

Policy lives in the provisioning and approval use cases. Resolver, store,
filesystem and process mechanics remain behind ports and services. The verdict
kernel is not widened into a package manager and still decides only from its
declared inputs.

## Done criteria

Each criterion is met only when a test proves it. New coverage belongs in
`tests/unit/test_dependency_provisioning.py`,
`tests/security/test_slice006_dependency_provisioning.py` (renamed from the
originally-planned basename, which collided with the unit file under pytest's
flat module namespace), and `tests/e2e/test_gating_real_suite.py` — the
latter written as the owner directed 2026-08-04: real-world operator stages
against a clone of this repository, no synthetic packages.

1. A subject without a supported committed manifest or committed lock refuses
   before resolution, download or execution. (ADR-007 s.p. 1, 2)
2. Resolution runs without the committed lock present. A hand edit to a package,
   graph edge, URL or hash makes byte equality fail and refuses. (s.p. 3)
3. The resolver executable, Python target, index set and resolution epoch are
   operator-pinned; absence or a user-writable executable refuses. (s.p. 4, 5)
4. Only wheels enter the store. An sdist, VCS source, local source, missing
   SHA-256 or incompatible platform refuses with the exact package named.
   (s.p. 6, 7, 11)
5. A downloaded wheel is hashed before atomic publication under its SHA-256;
   concurrent writers expose one complete entry and no partial file. (s.p. 8, 10)
6. Every store read re-hashes. A corrupt entry is quarantined; only `deps fetch`
   may refetch it, and a gated run with a missing entry refuses before spawn.
   (s.p. 9, 12)
7. The assembled root contains exactly the selected target's wheels and pinned
   runner, is read-only before spawn, and a write attempt cannot change it.
   (s.p. 13)
8. The run receives `UV_PROJECT_ENVIRONMENT`, `UV_NO_SYNC=1` and `UV_OFFLINE=1`;
   a network attempt is denied and produces no evidence. (s.p. 14)
9. The approval surface names every added, removed and version-changed package
   since the last approved subject; without a baseline it shows the full set.
   Rejecting the exact delta prevents execution. (s.p. 15, 16)
10. The dependency-set identity is derived from the subject lock and target, and
    evidence cannot be replayed for a subject selecting different bytes.
11. The existing executable-path, repository and ignored-state confinement tests
    remain green with the dependency `bin` directory present.
12. An honest dependency-bearing fixture provisions once, reuses the store with
    zero downloads, executes offline, signs evidence and evaluates PASS.
13. A malicious hash-correct wheel with a `pytest11` entry point demonstrates
    that approved dependency code can force exit 0; product text calls this
    **not caught**, and no test mistakes it for a closed path. (s.p. 17, 18)
14. **Ranex gates its own repository.** Against the real current commit, `ranex
    run` executes the unchanged catalog command `uv run pytest -q` in the
    materialised tree, and `gate evaluate` accepts the resulting signed evidence.
15. Every refusal added by this slice is reached by a test, `diff-cover` remains
    100% on the change, and the full repository suite remains green.

## The controls most likely to become decoration

First: resolving with `uv.lock` in place. uv documents that an existing lock is
used as a preference, and `uv lock --check` accepted a deliberately changed
wheel hash here. The reproduction must alter both graph and artifact fields; a
test that changes only a manifest constraint proves less than its name says.

Second: a dependency denial that passes because the command never ran. The
honest dependency-bearing path and the real self-gate are the controls. They
must assert collection happened and evidence was admitted, not merely “not a
false PASS.”

Third: calling a path pinned because its string is fixed. The installed uv here
is `/home/soultransit/.local/bin/uv`, owned and writable by the observed uid.
The test replaces its bytes or an equivalent fixture and watches provisioning
refuse; an exact path without an ownership/digest check is still agent-selected.

## What this slice does not close

- **Import-time execution is not caught.** A correctly hashed, explicitly
  approved malicious dependency still runs inside the measured command and can
  force its exit code. pytest makes the route concrete by auto-loading installed
  `pytest11` entry points, but direct imports make disabling that feature
  insufficient. Dependencies are trusted computing base for that run.
- **Approval is mitigation, not proof.** A readable package delta spends scarce
  human attention better than an opaque digest. It does not establish publisher
  identity, audit wheel code, detect malware, or make the dependency independent
  of the verdict it helps produce.
- **Index history is not retained.** A fixed epoch prevents newer releases from
  changing resolution; it cannot make a mutable registry keep old metadata.
  Store retention preserves fetched artifacts, not the ability to re-resolve an
  evicted subject forever.
- **Other ecosystems remain closed.** npm, Cargo and system packages need their
  own manifest, lock and artifact policies. No generic abstraction is added in
  anticipation.
- **Landlock remains deferred.** ADR-006 stays proposed, including the measured
  signing-key theft. This slice restores a runnable suite; it does not close that
  same-uid attack, approver authentication, journal truncation, or the remaining
  mutation survivors.
