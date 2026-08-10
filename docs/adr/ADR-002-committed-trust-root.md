# ADR-002 — the trust root is the committed path, and absence blocks

**Status:** accepted
**Date:** 2026-08-02
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-002-evidence-authenticity.md` — reopened

## Context and Problem Statement

`refuse_uncommitted_trust_root` (`src/ranex/cli/main.py`) compared the gate
catalog and the producer keyring against the bytes the evaluated ref records,
and returned having compared nothing when the ref carried no such path. The
branch was deliberate: "there is no reviewed version to prefer, and taking one
out of the history is itself a commit a reviewer sees."

That reasoning holds for a path the *operator* chose. The party being gated
chooses it too, and it is a flag. Reproduced, all three with no key theft and no
forged signature: `--gate-catalog attacker-gates.yaml` rewrites the gate after
the work; `--producers` at a gitignored path self-registers a producer while
`git status` reports a spotless tree; and a catalog committed as a *symlink* at
a reviewed name delivers bytes no commit carries, because resolution happened
before git was asked. Each one lands on the same `return`.

## Decision Drivers

- Absence blocks everywhere else in this kernel; the trust root was the
  exception, and it is the thing every other control hangs from.
- The attacker controls the one input that skipped the check: the path.
- Review is the only control on these two files. A file no commit carries was
  reviewed by nobody, whatever its contents say.
- A check that a `.gitignore` line makes invisible is not a check.
- The product must still land changes; refusing everything is an outage wearing
  responsible clothes.

## Prior art

Searched: GitHub code search for trusted-root and trusted-metadata loading
across python-tuf, go-tuf, cosign and in-toto.

Rejected: <https://github.com/sigstore/cosign> at tag v3.1.3,
`pkg/cosign/verify.go` — its keyless model anchors verification in Fulcio and
Rekor online services, not in a version-controlled trust-root file whose exact
bytes the verifier pins. The earlier link named `pkg/root`, a path cosign has
never carried; that is sigstore-go's.

Rejected: <https://github.com/in-toto/in-toto> at tag v3.1.0, `in_toto/` — its
key loading is a caller and CLI concern, not enforcement that a reviewed
repository path supplies the trust-root bytes used for a verdict.

The revision sits beside each link rather than inside its path: a `/tree/<tag>/`
URL is a pinned citation to this repo's own checker, and a citation must be
vendored with a licence and a weakness. These were weighed, not adopted.

TUF remains the conceptual anchor: trusted root metadata must be present and
valid, but bootstrap is explicitly out of band:
<https://theupdateframework.github.io/specification/latest/>. SLSA likewise puts
provenance generation outside the tenant while not judging source soundness:
<https://slsa.dev/spec/v1.0/requirements>.

- **python-tuf trusted metadata loading** — `TrustedMetadataSet` validates the
  ordered root, timestamp, snapshot and targets chain and raises when metadata
  cannot be admitted, making absence and invalidity explicit states.
  <https://github.com/theupdateframework/python-tuf/blob/v7.0.0/tuf/ngclient/_internal/trusted_metadata_set.py>
  License: MIT OR Apache-2.0 — both choices are permissive and compatible here.
  Weakness: `_load_trusted_root` verifies the initial root only against itself;
  whoever plants the bootstrap bytes controls the anchor, with no external
  threshold or notarization, and `bootstrap=None` permits cached disk bytes.
  Vendored: docs/adr/prior-art/ADR-002/python-tuf-trusted-metadata-set.py blob:689eef01de665280434e4c3d8ccdc63f4431b67b
- **go-tuf trusted metadata loading** — `New()` initializes a trusted metadata
  set from caller-provided root bytes before enforcing the update sequence and
  signature checks for later metadata.
  <https://github.com/theupdateframework/go-tuf/blob/v2.4.2/metadata/trustedmetadata/trustedmetadata.go>
  License: Apache-2.0 — permissive and compatible with this repository.
  Weakness: `loadTrustedRoot` deliberately performs no expiry check on the
  initial root, whose bytes arrive from the caller; repository anchoring is
  therefore the caller's property rather than one this implementation enforces.
  Vendored: docs/adr/prior-art/ADR-002/go-tuf-trustedmetadata.go blob:3ae32781cdf83d84bacdd4276ae868cc7b6ef0ed

Kubernetes' fail-closed admission default supplies the outage warning inherited
here, while gitignore explains why ignored trust roots evade habitual status
inspection. Saltzer and Schroeder's fail-safe defaults name the underlying rule.

## Considered Options

1. **Keep the early return, document the hazard.** Rejected: the hazard is a
   reproduced gate PASS, and this project refuses controls that only warn.
2. **Refuse a trust-root path the ref does not carry.** Chosen.
3. **Compare only the post-resolution path, as before.** Rejected: it asks git
   about a name the working tree chose. A committed symlink then rewrites policy
   forever without another commit.
4. **Require the catalog to sit at one hard-coded path.** Rejected: it closes
   substitution and breaks every repository whose layout differs, and the flag
   would come back for the same reason it exists.
5. **Refuse only when the tree is dirty.** Rejected: gitignored files never make
   a tree dirty, which is the whole of attack three.

## Decision Outcome

In the context of two committed files that decide every verdict, facing a party
that names them by flag, we chose to **refuse any trust-root path the evaluated
ref does not carry, and to compare the bytes git records for the path AS NAMED
against the bytes actually read after resolution**, to make review the control
it was always claimed to be, accepting that every deployment must now commit its
keyring and catalog before either command will run.

Concretely: `committed_trust_root` takes both the operator's spelling and the
resolved path and **returns the committed bytes**, which is what every loader
below it parses; `named_within_repository` collapses `.` and `..` and follows
nothing, because a ref carries names; a missing blob raises instead of
returning; and `run` applies the same refusal to `--producers`, which it
previously consulted with no check at all.

### Consequences

- A catalog or keyring the history does not carry can no longer reach a verdict
  by any of the four routes reproduced above.
- A **symlinked trust root is refused outright**, including an honest one: the
  ref yields link text and the disk yields the target's contents, never equal.
  A reviewed name whose bytes live elsewhere is two objects where the design
  assumes one.
- Every repository must commit `producers.yaml` before `run` will sign. This
  repo carries none, so this ADR breaks its own default invocation until one is
  committed — the correct direction of failure.
- **This does not make a committed catalog correct.** A reviewed gate that
  demands little is a weak gate, and no check here can tell.
- The check-then-reopen window is **closed**, not deferred: nothing hands back a
  path, so the second read has nowhere to happen. `strace` counted 3 and 2 opens
  before, 1 each after.

### Confirmation

`tests/security/test_slice002_trust_root_reopened.py` is the check. Five attacks
— uncarried catalog, uncarried keyring, gitignored keyring, committed symlink,
and a redundant path spelling — must each exit 2 with no verdict line printed,
and a sixth test asserts the ordinary committed pair still reaches `PASS`. That
sixth is not decoration: a fix that refuses every path satisfies the other five
and leaves nothing landable. If the refusal is removed and the suite stays
green, the check is wrong, not the code.

## Improvements on the prior art

1. **The anchor is the repository's own history, not an out-of-band file.** TUF
   must ship its root separately and concedes it cannot bootstrap trust; we
   inherit the anchor git already provides, so "reviewed" and "committed" are
   the same fact and there is no second artefact to distribute or lose.
2. **The name is the question, not the destination.** Neither TUF nor SLSA has
   to deal with a trust root reachable by a symlink the attacker commits once.
   Asking git about the operator's spelling and comparing against the bytes
   actually read is what makes the indirection visible instead of transparent.
3. **Fail-closed, with the outage case named and tested.** Kubernetes documents
   fail-closed as a default and leaves the wedging risk to operators. Here the
   "refuses everything" failure is a test that must pass, so the cheap wrong fix
   cannot ship green.
4. **The gitignored case is treated as worse, not equal.** An untracked file at
   least shows as `??`. `private_signing_key` already refuses a key inside the
   tree on exactly this reasoning; the keyring now gets the same suspicion.

## Architecture surface

Driving side, plus one inversion. `cli/main.py` is the driving adapter and owns
the refusal. The two driven config adapters grow text-taking cores
(`load_gate_text`, `load_keyring_text`) and keep their path wrappers for callers
that genuinely mean a file; the composition root now takes catalog **bytes**, so
"which bytes are the policy" is decided by the only layer that can decide it.
The domain is untouched — `evaluate()` never learns a trust root exists, which
is what keeps it pure in (gate, evidence, subject, approver).

## Scope and threat delta

Governs which bytes may decide a verdict. STRIDE letters moved: **T** (the
catalog and keyring can no longer be swapped for unreviewed bytes) and **E** (a
worker can no longer self-register as a producer).

Explicit non-goal: judging whether a committed gate is a *good* gate. Out of
scope deliberately: an attacker who can commit and get the commit reviewed — at
that point review is the control, as designed, and no code here helps.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Security (integrity) | trust-root path the ref does not carry | exit 2, no verdict printed |
| Security (integrity) | trust root reached via a committed symlink | refused, no PASS reachable |
| Functional correctness | committed catalog and keyring, unmodified | `PASS` still reachable |
| Security (integrity) | trust root swapped after the check, before the load | committed bytes decide; 1 open per file, was 3 and 2 |

## Reversibility

Door: two-way

Nothing is written in a new format and no on-disk artefact changes shape.
Reverting restores the early return and re-opens the four reproductions;
existing evidence and journals stay valid either way. The cost of the decision
is operational, not structural: repositories must commit two files they were
already expected to commit.

## Sad paths

Derived by equivalence partitioning over the flag's value space — carried,
uncarried, hidden, redirected, respelled — plus boundary analysis on the ref.

| # | Input | Required behaviour |
|---|---|---|
| 1 | `--gate-catalog` names a path the ref does not carry | refuse, exit 2, no verdict |
| 2 | `--producers` names a path the ref does not carry | refuse, exit 2, no verdict |
| 3 | keyring hidden by a committed `.gitignore` | refuse — invisibility is not innocence |
| 4 | reviewed name committed as a symlink to uncarried bytes | refuse — link text never equals target content |
| 5 | committed path spelled with `./x/../` components | still the trust root; tampering still caught |
| 6 | committed catalog edited in the working tree | refuse — unchanged from before |
| 7 | `run --producers` at an uncommitted path | refuse before the command runs |
| 8 | trust-root path is a directory or a submodule | refuse — `cat-file blob` yields no blob |
| 9 | path escaping the repository after normalisation | refuse at resolution, unchanged |
| 10 | catalog or keyring swapped between the comparison and the load | refuse — the committed bytes are returned and parsed; nothing re-opens a path |
| 11 | evidence file at an arbitrary path | **by design** — every record is signed and admitted individually |
| 12 | a reviewed commit that weakens the gate | **not caught** — review is the control, and this is what it is for |
| 13 | contradicting record deleted from the evidence file | **not caught** — the file is not append-only; SLICE-004 |
| 14 | `git replace` substituting a trust-root blob, or the subject commit | refuse — every git query passes `--no-replace-objects`, injected once in the function they all go through |
| 15 | working-tree file hidden from `git status` by `.gitignore` or `.git/info/exclude` | **not caught** — the exclude needs no commit, so review sees nothing; SLICE-004 |
| 16 | `filter.<n>.clean` in `.git/config` hashing a modified tracked file to its committed blob | **not caught** — no git flag ignores repository-local config, so no better question exists to ask; SLICE-004 |
| 17 | trust-root blob substituted by overwriting its loose object | **not caught** — `cat-file` never checks a blob against the name it was asked for; read-only mode is not a control against its owner; SLICE-004 |
| 18 | `git` itself resolved on an editable PATH, a shim dropping the flag | **not caught** — this bounds row 14; the oracle is chosen by whoever launched Ranex; SLICE-004 |
| 19 | untracked **empty directory** the bound command reads | **not caught** — git cannot represent one, so no `-u` level and not `--ignored` sees it; SLICE-004 |
| 20 | a symlink at Ranex's own bookkeeping name, aiming the dirty-tree exemption elsewhere | refuse — the exemption is decided on the path as named, never on where the name leads |
| 21 | committed gate catalog that is not valid YAML | refuse, exit 2 — an escaping `YAMLError` exits 1, which is the code meaning the gate was not satisfied |

## Test strategy

Red-then-green, tests frozen before the change and authored by a different agent
than the implementer. All five attacks were observed failing against the old
code and the control observed passing, before any `src/` edit.

Levels, security-heavy because every sad path here is an attack rather than a
unit boundary:

- `tests/security/test_slice002_trust_root_reopened.py` — sad paths 1–5 and 10,
  plus the control for the outage failure mode. The new file. Sad path 10 is
  driven deterministically, not raced: the swap is performed inside the window
  by a patched `load_records`, which runs after both checks and before either
  load. A third test runs the same harness swapping nothing, so a broken
  harness cannot be mistaken for a working fix.
- `tests/security/test_evidence_trust_root.py` — sad path 6, the edited-catalog
  and edited-keyring cases SLICE-002 closed the first time; kept so this change
  cannot regress them.
- `tests/e2e/test_gate_evaluate_cli.py` — the ordinary committed path through the
  real CLI. Its fixture previously wrote the catalog after the commit and now
  commits it, which is itself evidence the refusal bites.

Sad paths 11–13 are declared uncaught rather than tested. Writing a green test
for a hole is how a hole becomes invisible.

Sad paths 14–21 were found by the audits that closed SLICE-003 and live in
`tests/security/test_slice003_audit_defects.py`. 14, 20 and 21 are closed and
green. 15–19 are strict xfails, each with a green control beside it, so no hole
is invisible and the day one closes its marker comes off loudly. 17 and 18 bound
what 14 bought: `--no-replace-objects` removes one lookup indirection, and does
not make git authenticate the bytes it streams or the binary that streams them.

Coverage: no global percentage — assertion-free suites reach 100%. Each attack
above maps to a named test; the residual four are recorded in `docs/STATE.md`
so a future session finds them without reading this file.

## Code review checklist

- Does the check ask git about the path *as named*, or about the resolved one?
- Would removing the `committed is None` branch fail a test, or only this prose?
- Does `run` apply the same refusal as `gate evaluate`, or only look like it?
- Is the control test still capable of failing — does it assert a real `PASS`?
- Does any refusal message tell the operator which file and what to do?
- Is `named_within_repository` used anywhere it would be mistaken for a
  containment check? It follows nothing and must never be one.

## More Information

Format defined by `docs/adr/ADR-000-how-we-write-adrs.md`. Supersedes nothing;
amends the trust-root reasoning SLICE-002 shipped and ADR-001 relied on when it
said the binding "inherits that protection for free".

Sad path 10 was closed in the same session this ADR was written, once an audit
named it independently. The fix turned out to be smaller than the descriptor
this repo uses for executables: pass the bytes, not a handle, and the second
read stops existing rather than being made safe.
