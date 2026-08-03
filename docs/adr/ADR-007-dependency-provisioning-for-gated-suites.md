# ADR-007 — provision dependencies without pretending they are evidence

**Status:** accepted
**Date:** 2026-08-03 (accepted 2026-08-04)
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`

## Context and Problem Statement

ADR-005 made observation honest by materialising only committed blobs. That also
removed `.venv` and `node_modules`, because ignored state is not in the commit.
Only self-contained commands now run; this repository's bound command, `uv run
pytest -q`, cannot, so Ranex cannot gate Ranex and a real defect crossed a green
suite while that route was unavailable.

Copying hashed wheels into the room restores capability, not independence. A
wheel places importable code in the command's environment; pytest 9.1.1 here
calls `load_setuptools_entrypoints("pytest11")`, whose `EntryPoint.load()` imports
the named module. A dependency can therefore decide the exit code being signed.
The dependency set, resolver and environment builder are trusted computing base
for that run. Confinement does not turn their answer into an independent fact.

## Decision Drivers

- Ranex must run a committed suite whose dependencies are absent from its tree.
- Resolution and download may use the network; the measured run must not.
- A missing digest, unavailable wheel or unverifiable derivation must block.
- An authored lock must not be accepted as its own proof of the manifest.
- The approver must see dependency names and versions changed since approval.
- No design may call a dependency-selected exit code stronger than it is.
- Resolver, interpreter and runner identities must be pinned outside agent control.

## Prior art

**Searched:** `gh api search/repositories` for "hermetic build", "prefetch
dependencies hermetic", "cachi2", "offline install lockfile", "build sandbox";
then `gh api search/code` inside `astral-sh/uv` and `bazelbuild/bazel` for the
hash-checking and repository-cache paths.

- **uv exposes the policy distinction Ranex needs to make mandatory.** `Require`
  says every requirement must have a lock hash; `Verify`, the default, validates
  a hash only when present. `from_args` also returns `None` for either negative
  flag, meaning no hash checking.
  <https://github.com/astral-sh/uv/blob/0.12.1/crates/uv-configuration/src/hash.rs>
  License: MIT OR Apache-2.0 — taken under MIT, matching this repository.
  Weakness: `HashCheckingMode::Verify` is the default and absence permits; both
  `--no-verify-hashes` and `--no-require-hashes` can disable checking. Ranex has
  no permissive mode and no negative flag.
  Vendored: docs/adr/prior-art/ADR-007/uv-configuration-hash.rs blob:473a9588facbd46ae37ed2ba216789fccc1bb76f
- **Bazel's download cache is the storage shape worth copying.** It namespaces
  entries by hash function and digest, writes through a temporary name, renames
  atomically, and re-hashes a value before returning it.
  <https://github.com/bazelbuild/bazel/blob/9.2.0/src/main/java/com/google/devtools/build/lib/bazel/repository/cache/DownloadCache.java>
  License: Apache-2.0 — permissive; the header is retained in the copy.
  Weakness: `KeyType.SHA1` remains accepted, so integrity is as weak as the
  caller's choice; a failed read asks the operator to delete the directory by
  hand. Ranex fixes SHA-256 and quarantines a corrupt entry before refetch.
  Vendored: docs/adr/prior-art/ADR-007/bazel-DownloadCache.java blob:a780a4f88dd374b4ea9fa7b6bb87e055ec70537f
- **Rejected:** <https://github.com/hermetoproject/hermeto> — 62 stars, and it
  prefetches dependencies for hermetic builds, which is this whole problem.
  GPL-3.0 conflicts with this MIT repository, and its separate binary would sit
  in the path deciding a verdict, which the pinned-toolchain rule forbids.
- **Rejected:** <https://github.com/NixOS/nix> — fixed-output derivations are
  stronger than a lockfile and solve reproducibility properly. LGPL-2.1, a
  required daemon and store, and replacement of the deliberate toolchain design
  make adopting the whole system disproportionate here.

## Considered Options

1. **Keep self-contained gates only.** Honest and unusable for real suites;
   rejected because Ranex cannot gate its own repository.
2. **Trust the committed lock and verify its hashes.** Rejected: the agent can
   author its own lock, and a hash-correct wheel still executes in the verdict.
3. **Adopt Hermeto or Nix.** Both solve more of provisioning; rejected for the
   licence, process-boundary and installation costs recorded above.
4. **Resolve a clean manifest under fixed resolver inputs, compare the generated
   lock byte-for-byte, approve its readable delta, then provision hashed wheels
   into a content store for an offline run.** Chosen, with its limit explicit.

## Decision Outcome

In the context of a committed suite that cannot carry its ignored environment,
we chose **a separate, networked provisioning phase followed by a derived,
approved, read-only dependency root for the offline bound run**, accepting that
the dependencies remain inside the run's trusted computing base.

`ranex deps fetch` resolves the committed manifest in an empty input directory;
the committed lock is never a preference. Resolver executable, Python target,
index set and resolution epoch are operator-pinned, because a ranged manifest
against a moving index has no stable byte result. Generated and committed locks
must be byte-equal. Every selected wheel must carry SHA-256; sdists, local paths,
VCS sources and missing hashes refuse. Artifacts are stored by SHA-256, rehashed
on every read, and assembled read-only. The run has no network and sees only that
root. Its evidence remains bound to the subject whose lock names those bytes.

### Consequences

- Good: a committed suite can run without admitting ignored state into evidence.
- Good: a hand-edited lock, absent hash, sdist and corrupted cache entry refuse.
- Good: downloads are amortised and the measured command remains offline.
- Good: the approver sees added, removed and version-changed packages against
  the last approved subject, not only two opaque tree digests.
- Bad: resolver, target interpreter, root builder and dependency code are TCB.
- Bad: fixed resolution inputs and an artifact store are operator-managed state.
- Bad: platforms without a matching wheel cannot run a gate they previously ran
  from a local environment.
- Bad: approval reduces hidden change; it cannot make third-party code truthful.

### Confirmation

The control is proven in layers: derivation tests edit a committed hash and lock
edge and require refusal; store tests corrupt bytes and require quarantine;
execution tests make network and dependency-root writes fail while an honest
import succeeds. A malicious `pytest11` fixture is also run and shown capable of
forcing success after approval: that is a limit made executable, not a test the
system claims to defeat.

The end-to-end confirmation is this repository itself. `ranex run` must execute
the unchanged catalog command `uv run pytest -q` against the materialised commit,
then `gate evaluate` must accept its signed evidence for that same subject.

## Improvements on the prior art

1. **Absence blocks, unconditionally.** uv's default `Verify` mode permits a
   missing hash and its negative flags disable all checking. Ranex exposes
   neither: SHA-256 on every selected artifact or no dependency root.
2. **The lock is checked as output, not trusted as input.** `uv lock --check`
   returned success here after a wheel hash was edited. Ranex resolves without
   the committed lock and compares complete bytes, so graph and hashes both bind.
3. **Resolution state is named.** A clean resolution here already moved coverage
   7.15.2 to 7.15.3. Resolver version, target, indexes and epoch are explicit
   operator inputs; “manifest alone is reproducible” would be a false claim.
4. **One strong address.** Bazel lets the caller choose SHA-1 and verifies with
   that same choice. Ranex's store has one namespace and one algorithm: SHA-256.
5. **Corruption is contained.** A bad cache read is quarantined and can be
   refetched only in the networked phase; the run never repairs or downloads.
6. **Trust is surfaced rather than renamed.** A dependency delta is rendered and
   explicitly accepted, while the UI says the accepted code can still choose the
   command's exit. Hashes prove identity, not behaviour.

## Architecture surface

A dependency-provisioning service owns clean resolution, wheel admission, the
SHA-256 store and read-only root assembly. Ports separate the resolver and store
mechanics from the use case. `deps fetch` is the only networked command.

`cmd_run` selects the root derived for the subject and target, adds its `bin` to
the pinned executable search, and sets uv's documented offline, no-sync and
project-environment controls so the catalog argv stays unchanged. Dependency
delta rendering belongs in gate approval. The verdict kernel stays pure; it is
not taught that installed code is evidence.

## Scope and threat delta

In scope: Python wheel dependencies for a pinned Linux target, lock derivation,
artifact integrity, offline assembly, executable discovery, and a dependency
approval delta. Out: npm and other ecosystems, sdists, VCS/local dependencies,
package transparency, publisher identity and malware detection.

STRIDE movement: **T** narrows for lock and cache substitution; **I** narrows for
opaque dependency changes. Neither closes: an approved dependency executes in
the command and may decide its exit code. This restores a capability withdrawn
by ADR-005; it does not turn the sandbox into an independent test oracle.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | cache bytes differ from their SHA-256 address | refuse before root assembly |
| Auditability | subject changes one transitive package | delta names package and old/new version |
| Hermeticity | gated command attempts a download | network denied; no evidence recorded |
| Performance | second run uses an unchanged dependency set | zero downloads; store entries reused |
| Portability | target has no compatible wheel | explicit refusal naming package and target |

## Reversibility

Door: one-way

The store and service are removable. The trust claim is not safely reversible:
once gates are authored against provisioned imports, withdrawing the mechanism
makes them unrunnable, while retaining the capability without its derivation and
approval controls silently widens what a PASS means.

## Sad paths

Enumerated across declaration, resolution, fetch, assembly, approval and run.

| # | Input | Required behaviour |
|---|---|---|
| 1 | subject has no supported manifest | refuse; never guess dependencies |
| 2 | subject has no committed lock | refuse; absence cannot mean empty |
| 3 | clean generated lock differs by one byte | refuse and show the derivation mismatch |
| 4 | resolver, Python target, index set or epoch is unpinned | refuse before network access |
| 5 | newer registry release changes clean resolution | refuse; operator updates the fixed epoch deliberately |
| 6 | lock selects an sdist, VCS URL or local path | refuse; none may execute during provisioning |
| 7 | selected wheel has no SHA-256 | refuse; uv's absence-permits default is not inherited |
| 8 | downloaded wheel misses its declared digest | quarantine it and refuse |
| 9 | cached wheel misses its address on read | quarantine; only `deps fetch` may refetch |
| 10 | two writers fetch the same digest | publish one complete atomic entry, never partial bytes |
| 11 | target platform has no matching wheel | refuse and name package, version and target |
| 12 | gated run lacks a required store entry | refuse before spawning; never reach the network |
| 13 | command writes the dependency root | deny; root remains reusable and unchanged |
| 14 | command or uv attempts network access | deny and record no evidence |
| 15 | no prior approved subject exists | show the full set as the delta and require approval |
| 16 | approver rejects an added or changed package | refuse; do not execute the suite |
| 17 | correctly hashed, approved malicious wheel is imported | **not caught** — its code is in the run's TCB |
| 18 | approved wheel declares a `pytest11` plugin that forces exit 0 | **not caught** — pytest auto-loads it before collection |
| 19 | tests directly import an approved dependency that lies | **not caught** — disabling plugin auto-load cannot close this |
| 20 | mutable index removes metadata needed to rederive an old lock | **not caught** as availability — retained artifacts do not retain index history |

## Test strategy

Levels: unit tests for parsers, delta computation and refusal branches; security
tests for substitution, write and network attempts; e2e for a real provisioned
suite. New files and exact test names belong in the slice, not in this ADR.

`tests/security/test_slice004_hermetic_observation.py` remains the control that
ignored `.venv` state never enters the subject. `tests/security/test_executable_path_confinement.py`
and `tests/security/test_repository_confinement.py` are rerun with the dependency
bin directory present, so restoring imports does not reopen executable or tree
substitution. `tests/contract/test_gate_catalog_claim_commands.py` pins the
unchanged `uv run pytest -q` argv.

`tests/e2e/test_run_produces_evidence.py` remains the honest signed-record path.
The slice adds the provisioning and self-gating tests before implementation;
every new refusal is covered and `diff-cover` stays at 100%.

Red-then-green: first prove the current materialisation cannot resolve `uv` or
`pytest`; then prove a fabricated lock passes `uv lock --check`; then add the
clean regeneration, store and root. The malicious plugin demonstration stays
green both before and after because it proves the declared limit, not a defence.

## Code review checklist

- Does any path use the committed lock as a resolver preference?
- Can any missing hash, unsupported source or store miss become a skip?
- Are resolver, target, index set and epoch all outside agent-controlled choice?
- Can the run write the root, cache, resolver, interpreter or runner it uses?
- Can `uv run` sync, build, download or discover ambient configuration?
- Is the delta based on the actual last approved subject, with absence explicit?
- Does evidence still bind to the subject whose derived lock selected the root?
- Do messages say hashes prove identity and approval mitigates behaviour?
- Does the repository gate itself through the exact committed command?

## More Information

Verified locally on 2026-08-03: uv 0.11.26 is installed at the user-writable
`/home/soultransit/.local/bin/uv`, outside Ranex's pinned system directories; it
must be provisioned and pinned too. `uv lock --check` accepted a deliberately
changed wheel hash. A clean lock from the same manifest differed because coverage
7.15.3 had appeared after the committed 7.15.2 resolution.

pytest 9.1.1's installed source loads every `pytest11` entry point and
`importlib.metadata.EntryPoint.load()` imports its module. Official uv docs
confirm `UV_NO_SYNC`, `UV_OFFLINE` and `UV_PROJECT_ENVIRONMENT`; official pytest
docs confirm entry-point auto-loading. These checks support the limit, not a
claim that the approved dependency becomes trustworthy.
