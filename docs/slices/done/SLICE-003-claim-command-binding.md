# SLICE-003 — claim↔command binding

**Status:** done
**Opened:** 2026-08-01
**Closed:** 2026-08-02 — 250 green, 6 strict xfail. Six independent audits failed
to break the binding itself; criteria 1–9 were re-proven by mutation. Closed on
its own promise, with six reproduced false-PASS paths recorded, frozen, and
assigned to SLICE-004 — the same disposition sad path 18 got when this slice was
opened on top of it. See "The closing audit" below for what that does not buy.
**ADR:** `docs/adr/ADR-001-claim-command-binding.md` — the researched decision,
including why in-toto's `expected_command` is prior art for the defect and not
for the fix.
**Closes:** a signed evidence record for `true` satisfying `tests-executed`.

## The defect

`Evidence.satisfies()` (`src/ranex/governed_execution/domain/verdict.py:64-75`)
decides satisfaction from three facts: claim name, subject digest, exit code 0.
It never looks at what ran. The catalog cannot help it — `required_claims` is a
list of bare strings, coerced with `str(claim)` at
`slice_gate_loader.py:95`, so there is nowhere to declare what a claim means.

Consequence, reproducible today:

```
ranex run --claim tests-executed --producer worker \
  --repository . --evidence governance/evidence.json \
  --producers governance/producers.yaml -- true
```

yields a correctly signed, subject-bound record that satisfies a gate requiring
`tests-executed`. Signature and subject digest prove *who* recorded *against
which tree*. Neither proves any work happened.

This is the dart-thrower painting the bullseye. It is the failure the project
exists to prevent, and it is currently asserted as intended behaviour by
`tests/e2e/test_signed_evidence_cli.py:128-139`.

## Design

A claim declares the command that satisfies it, in the committed catalog. The
catalog is already the trust root — `refuse_uncommitted_trust_root`
(`cli/main.py:94-128`) checks it against the committed blob before load — so the
binding inherits that protection for free.

`gates.yaml` claim entries become mappings, argv as a list:

```yaml
required_claims:
  - claim_id: tests-executed
    command: ["uv", "run", "pytest", "-q"]
```

argv, not a string, so comparison needs no shell parsing. The literal stays
readable in review; the digest is what the kernel compares.

- `Claim` gains `command_digest`, computed at load over
  `canonical_json_bytes(argv)`.
- `Evidence` gains `command_digest`, a **signed** field. The existing human
  readable `command` stays, also signed, so the legible field cannot be swapped
  under a matching digest.
- `satisfies()` gains `self.command_digest == claim.command_digest`.
- `Evidence` gains `executable_path`, also **signed**: the kernel resolves
  `argv[0]` once, refuses if the resolution lands inside the subject worktree,
  and executes the resolved absolute path. This closes the PATH-aliasing forgery
  the in-toto spec concedes defeats `expected_command` — a worker cannot drop
  `./pytest` in the repo and satisfy the claim. Symlinks are resolved before the
  containment check. Re-checked at evaluate, so it is verified at both ends
  rather than merely recorded.
- `SIGNED_FIELDS` 5 → 7; domain string `ranex-evidence-v1` → `v2`.

v1 records are refused, not migrated. `governance/evidence.json` is gitignored
and no signed evidence is committed, so there is nothing to migrate. A silent
v1 acceptance path would be a downgrade attack against this whole slice.

**Absence blocks, at construction.** A required claim with no `command` is a
claim whose satisfaction is undefined, and an undefined claim cannot block. The
loader raises; it does not default. Bare-string claim entries are refused with a
message naming the migration.

### Deliberately out of scope

- **Output digests.** Nothing in this slice would verify one, and an unchecked
  field that resembles a control is decoration. Recorded as a known limit
  instead: a command matching the bound digest is still trusted to have done what
  its name suggests.
- **Per-claim producer binding.** Separate concern, no bearing on `-- true`.
- **Key containment and approver authenticity.** SLICE-004 and SLICE-005. The
  binding is forgeable by a keyholder until SLICE-004 lands, because a worker
  holding the key can sign `command_digest` of the bound command while running
  something else. This slice makes the binding *stated*; SLICE-004 makes it
  *observed*. Neither is sufficient alone and this file should not pretend
  otherwise.

## Consequence for this repo's own gate

`landing` requires `contracts-validated`, and nothing produces it. Today that is
invisible because `-- true` satisfies it. After this slice the claim needs a real
command, and there is no contracts validator to name.

Per STATE.md's standing instruction — "write one or amend the gate; do not fake
the claim" — **the claim is dropped from `landing`** and the debt stays recorded.
Naming a placeholder command would be faking it; leaving it required would make
`landing` permanently unsatisfiable, which is not a control, just a broken gate.

## Done criteria

Every one needs a test that fails before the change and passes after.

1. `run --claim tests-executed -- true` produces evidence that does **not**
   satisfy `tests-executed`; `gate evaluate` exits FAIL.
2. `run` with the catalog-bound command produces evidence that **does** satisfy.
3. A `gates.yaml` claim given as a bare string is refused at load, with a message
   that names the required shape.
4. A `gates.yaml` claim mapping missing `command` is refused at load.
5. A v1-domain signature is refused at admission (downgrade attack).
6. `command_digest` is covered by the signature: flipping it in a stored record
   fails verification.
7. Flipping the readable `command` field alone, leaving `command_digest` intact,
   also fails verification.
8. Argv differing only in argument order produces a different digest and does not
   satisfy.
9. The three tests that currently bless `exit 0` are rewritten to assert refusal:
   `tests/e2e/test_signed_evidence_cli.py:128`,
   `tests/e2e/test_run_produces_evidence.py:127`,
   `tests/security/test_slice002_defects.py:144`.
10. Full suite green. No test asserts that a trivial command satisfies a
    substantive claim.

## The closing audit — 2026-08-02

Five independent audits, three with no context but the tree. Criteria 1–9 were
re-proven by mutation: each control was removed from `src/` one at a time and the
covering test observed going red. Criterion 10's second sentence was **false** as
first written and is now enforced.

The binding itself held. No audit made a record satisfy a claim it does not name,
and every tamper route — digest, readable command, executable path, v1 downgrade,
argv permutation — was refused. What the audits broke is the promise *around* the
binding: that a PASS means the bound command ran against the tree being judged.

**Closed by this session**

- [x] **`git replace` substitutes the trust root.** A local `refs/replace/*` ref
      made `git cat-file blob HEAD:gates.yaml` return bytes no commit carries and
      `HEAD^{tree}` peel to an abandoned tree, while `git status` stayed empty,
      `git log` showed one honest commit, and no clone carried any of it. The
      gate catalog, the keyring and the subject digest each fell to it
      separately. All ten git queries now pass `--no-replace-objects`, injected
      once in the one function they go through rather than remembered at ten call
      sites. ADR-002 sad path 14.
- [x] **The trivial-command guard was a denylist `/bin/true` walked past.** It
      compared raw argv against four tuples, so this repository's own `landing`
      gate could be bound to `/bin/true` with the contract file entirely green.
      argv[0] is now reduced to its basename, and the check says plainly that it
      is a tripwire and not a proof.
- [x] **The v1-downgrade test was green for the wrong reason.** A five-field
      record is refused by the field-set check before any signature is read, so
      the test passed with the domain rolled back to v1. It now asserts which
      control caught it; the domain prefix is proven by its sibling.
- [x] **The dirty-tree exemption could be aimed by a symlink — D4 reopened.**
      Removing `--journal` stopped the observed party *naming* the exempted
      path; it could still *point* it. The exemption was computed from a
      resolved path, so a symlink at Ranex's own constant name re-aimed it at
      any untracked file, and the file the bound command read went unmentioned
      while `git status` reported it plainly. Worse in the default layout, where
      `governance/` holds two gitignored paths, so the link needs no commit and
      leaves no reviewable artifact. The exemption is now decided on the path as
      **named**, through the helper the trust root already uses for exactly this
      distinction. ADR-002 sad path 20.
- [x] **A malformed committed catalog was reported as a failing gate.** The
      catalog loader let `yaml.YAMLError` escape; it reached `main()` as a
      traceback, and an uncaught exception exits 1 — `EXIT_FAIL`, the code
      meaning the gate was not satisfied. Nothing had been evaluated. The
      adapter now wraps it, as the keyring loader already did. ADR-002 sad
      path 21.

**Reproduced, not closed — all one root cause**

The observation is made from inside the state the observed party controls. Each
is frozen as a strict xfail with a green control beside it, so none can pass
vacuously and each fails loudly the day it closes.

- [ ] **The inherited environment retargets the bound binary.** `PYTHONPATH` and
      a `sitecustomize.py` outside the repository make the bound command exit 0
      without running. The argv, the digest, the absolute interpreter, the tree
      and the signature are all honest. It survives an absolute `command[0]`, so
      it is not sad path 18 in another costume — and it defeats this
      repository's own binding, `uv run pytest -q`. ADR-001 sad path 30.
- [ ] **A file git was told to exclude decides the outcome.** `.git/info/exclude`
      needs no commit, so there is no artifact for review to see, and the
      dirty-tree check reports clean while the bound command reads the file.
      ADR-002 sad path 15.
- [ ] **A `clean` filter hides a modified tracked file.** `filter.<n>.clean`
      pointed at `git cat-file blob HEAD:%f` makes every tracked file hash to
      what HEAD carries however it was edited, so the committed check can be
      rewritten to pass and `git status` still reports nothing. No git flag
      ignores repository-local config, so no better question exists to ask.
      Hardening only the environment spelling would read as a fix while an
      equivalent vector stayed open. ADR-002 sad path 16.

- [ ] **A trust-root blob substituted by overwriting its loose object.** This is
      what bounds the `git replace` fix above. `--no-replace-objects` removes one
      lookup indirection; it does not make git authenticate the bytes it
      streams, and `cat-file` never checks a blob against the name it was asked
      for. Loose objects are created read-only, which is a speed bump against
      their owner and not a control. `git fsck` sees it; nothing on the verdict
      path runs fsck. ADR-002 sad path 17.
- [ ] **`git` itself resolved on an editable PATH.** Every fact the verdict
      rests on comes from spawning `git` as a bare name. A shim that forwards
      everything except `--no-replace-objects` removes the fix above entirely.
      Its precondition is control of the PATH *Ranex* is launched with, which a
      child process cannot reach — the same signer/runner boundary as the
      environment defect, not the same thing as PATH-shadowing the observed
      command. ADR-002 sad path 18.
- [ ] **An untracked empty directory.** Git has no representation for one, so no
      `-u` level and not `--ignored` reports it. It is the case that proves the
      dirty-tree check cannot be repaired by asking git a better question.
      ADR-002 sad path 19.

These belong to SLICE-004. They are not deferred for convenience: each fix is
architectural — drop the inherited environment, resolve the tooling outside the
observed party's reach, or observe in a pristine worktree of the subject commit
— and attempting any of them here would be opening the next slice inside this one.

**Found and recorded, no fraudulent PASS**

- `sqlite3.DatabaseError` escapes `cmd_gate_evaluate`, so a `--journal` pointing
  at a non-database gives a traceback. Fail-closed: the verdict is decided before
  the journal is written.
- `--journal ""` is falsy and silently disables journalling, so a PASS can be
  issued with no entry — the trace-free probe the code refuses elsewhere.
- `Journal.verify()` has no caller in `src/` and there is no `ranex journal`
  subcommand, so the chain is tamper-evident only to the test suite.
- `record_evidence` replaces by `(claim_id, producer_id)`, so one producer
  re-running a flaky command erases its own red observation before the
  contradiction check can ever see it. Same family as ADR-001 sad path 27.
- `cmd_run`'s docstring says refusals "exit 2 having written nothing"; a bound
  command that itself exits 2 also exits 2, having written a record.
