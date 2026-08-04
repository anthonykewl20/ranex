# SLICE-006 — gate a real test suite

**Status:** done
**Opened:** 2026-08-03 — parked for SLICE-007, unparked 2026-08-04 by owner decision
**Closed:** 2026-08-04 — all fifteen criteria met, each proven by a test.
Stage 12 passed with the operator's own key: the self-gate is real, not
demonstrated on a clone only.
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

## What the real-world journeys found

Nine defects, every one caught by driving the CLI as a person does, and
**none by a unit test**. The first six came from
`tests/e2e/test_gating_real_suite.py`; seven and eight from
`tests/e2e/test_cold_start_journey.py`, which starts from zero state and is
the only test that sees what a new operator sees; the ninth from running the
suite inside the ADR-009 sample. MAP §4.6 records the
doctrine this evidence produced. Recorded because the ADR's sad-path table did not
predict any of them, and the next fork-facing slice will meet the same shapes.

1. **`uv run` rewrites the committed lock.** A plain `uv run pytest -q` after
   a clean re-lock silently dropped the `[options]` epoch block, after which
   the lock failed its own byte comparison. Fixed twice: the gated run carries
   `UV_FROZEN=1`, and the repository's own commands moved to `uv run --frozen`.
2. **A lock legitimately holds one package at several versions.** Split
   resolution puts `libcst` at 1.8.5 and 1.9.0 in one file; the parser treated
   any repeated name as corruption and refused most real locks. Packages are
   keyed by `(name, version)`, and edges resolve by explicit version or by the
   entries' own `resolution-markers`, where anything but exactly one match is
   a refusal.
3. **`uv lock --check` re-resolves when the epoch is omitted.** The stage
   proving uv accepts a fabricated hash was passing for the wrong reason until
   it passed `--exclude-newer` too.
4. **CI was rewriting the lock too.** Every `uv` call in the workflow ran
   unfrozen — the same defect in the one place a silently mutated trust root
   would be hardest to notice.
5. **A test that proved the wrong thing.** Tightening a bare `pytest.raises`
   showed that "an absent pin refuses" had been deleting a key line and
   leaving its children, so two cases proved malformed YAML refuses rather
   than that absence does.
6. **The committed lock itself, on the first production fetch.** It had been
   derived through the ambient warm uv cache, whose cffi metadata predated a
   2.1.1 release uploaded three hours before the pinned epoch. The byte
   comparison refused it naming the exact divergence. `derive_lock` already
   used an empty cache per derivation; the operator's re-lock procedure now
   does too, and the lock is regenerated from it.
7. **`keygen` told a first-time operator to write an invalid keyring.** This
   repository commits none, so a new person is creating the file; the bare
   entry that was printed parses as a document with no `producers` mapping,
   and the loader then refuses it for doing exactly what the product said.
   It now prints the complete shape and names the file.
8. **The README's walkthrough had silently rotted.** It omitted `deps fetch`
   and `deps approve`, never mentioned installing the pinned resolver, and
   explained a `gate evaluate` failure with a `contracts-validated`
   requirement SLICE-003 had removed. The cold-start journey now asserts the
   commands it runs appear in `README.md`, so the two cannot drift again.
9. **The cold-start journey re-entered itself inside the ADR-009 sample.**
   Its recursion guard travels by environment, and the sample's environment
   is built from empty, so the guard never arrives; before the sample had a
   repository, the recursion died accidentally at `git clone`. Stages 1 and 2
   ran against a clone whose HEAD was the outer journey's committed keyring
   and failed its zero-state claims. The guard now also recognises the
   sample by what does survive — its deterministic synthetic commit identity
   — and skips loudly.

## Criterion 14 — met

**Resolved 2026-08-04 by ADR-009, accepted the same day.** The five
git-dependent tests that failed inside the ADR-005 sample —
`test_docs_discipline::test_every_cited_implementation_is_vendored_and_matches_its_digest`,
`test_gate_evaluate_cli::test_foreign_repository_evaluation_is_refused_by_real_cli`,
and three in `test_keygen_key_confinement` reaching
`governed_repository_root()` — were never relaxed; the materialisation now
answers them truthfully. `materialise_subject` builds a fresh single-commit
repository around the verified tree: empty template, fixed identity and
epoch timestamp, no reflog, ignore rules bypassed on `add`, and a refusal
unless the sample's `HEAD^{tree}` equals the governed ref's tree. Measured
before deciding: the tree hash is unchanged, so the subject digest does not
move and prior evidence stays comparable.

All three strict `xfail` markers are removed and the stages pass:
`test_gating_real_suite.py` stage 08b and `test_cold_start_journey.py`
stage 9 are green against real PyPI (stage 12 skips by name on the
operator's signing key). Inside the sealed sample, 448 tests pass, the
recorded exit is 0, and `gate evaluate` answers PASS — Ranex gates a clone
of Ranex through the unchanged catalog command.
`tests/security/test_git_backed_materialisation.py` proves determinism (two
runs, one commit id), hygiene (no remote, hooks, reflog, stash, or second
commit), object-store containment, and every added refusal; the slice004
"no `.git`" control is amended to prove a clean filter planted in the
governed config cannot reach the sample's fresh one.

Criterion 13 is met: `tests/security/test_slice006_approved_wheel_can_lie.py`
demonstrates an approved, hash-correct wheel forcing a passing verdict with
every integrity control green, labelled **not caught**, with a control run
proving the suite genuinely executed.

## Verification actually run

- Full suite after criterion 14: **518 passed, 1 skipped** (stage 12, on the
  operator's signing key, which it names).
- Both real-world journeys with the resolver present: **23 passed, 1
  skipped**; stages 08b and cold-start 9 genuinely pass, no xfail remains.
- `diff-cover` on the criterion-14 change: **100%**, 17/17 lines; at
  close-out, **100%** over the whole slice range (747/747 changed lines) —
  which itself found one unreached refusal (the pins loader's YAMLError
  branch), closed with a test before closing the slice.
- Stage 12 with the operator's registered key and populated store: **passed**
  — `ranex run` executed `uv run pytest -q` against the real current commit
  and `gate evaluate` accepted the signed evidence.
- `mutmut` at close-out: 4771 mutants — 2980 killed, 841 timed out, 306
  without coverage, 644 survived (down from 1036). Sampled survivors in the
  new `_construct_repository` are equivalent or message-text mutants
  (redundant defensive `-c` flags, unasserted branch/message strings); every
  mutant of the new `.git`-path refusal was killed. Survivors remain weak
  evidence, per the recorded convention.
- `mutmut`: 4673 mutants — 2945 killed, 386 timed out, 306 without coverage,
  1036 survived. The provisioning survivors are dominated by error-message
  text and by equivalent mutants such as `"utf-8"` → `"UTF-8"`. Ten bare
  `pytest.raises` were tightened in response, and that tightening exposed a
  real defect: the "absent pin refuses" test had been removing a key line but
  leaving its children, so two cases proved that malformed YAML refuses
  rather than that absence does. Treat the remaining survivors as weak
  evidence, per the convention this repository already records.

## Operator setup

`governance/deps.yaml` pins the resolver at `/usr/local/bin/uv`, which is
root-owned on purpose. Installing it is the one step this slice cannot take
for itself:

```
sudo install -m 0755 ~/.local/bin/uv /usr/local/bin/uv
```

Until it exists, every real-world stage skips loudly by name rather than
passing vacuously.

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
