# ADR-001 — bind a claim to the command that satisfies it

**Status:** accepted
**Date:** 2026-08-01
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-003-claim-command-binding.md`

## Context and Problem Statement

`Evidence.satisfies()` (`src/ranex/governed_execution/domain/verdict.py:64-75`)
decides satisfaction from three facts: claim name, subject digest, exit code 0.
It never looks at what ran. The catalog gives it nothing to look at — a gate's
`required_claims` is a list of bare strings coerced with `str(claim)`
(`policy/adapters/configuration/yaml/slice_gate_loader.py:95`).

So `run --claim tests-executed … -- true` yields a correctly signed,
subject-bound record that satisfies a gate requiring `tests-executed`. The
signature proves *who* recorded; the subject digest proves *against which tree*.
Neither proves work happened.

This is the thrower painting the bullseye around the dart — the failure this
project exists to prevent. It is currently asserted as intended behaviour by
`tests/e2e/test_signed_evidence_cli.py:128`.

## Decision Drivers

- Absence must block: an undefined claim cannot be allowed to pass by default.
- The binding must live somewhere already covered by a trust root.
- Comparison must be exact and shell-free — no parsing, no fuzzy matching.
- The prior art's known weakness must be closed, not inherited.
- No field may be recorded that nothing verifies.

## Prior art

Searched: GitHub code search for command-binding and expected-command
verification across in-toto, in-toto-golang, sigstore and SLSA.

Rejected: <https://github.com/sigstore/cosign> — its attestation path authenticates
the CI identity and statement, but does not bind the exact argv that produced a
claim, so adopting it would leave this defect intact.

Rejected: <https://github.com/in-toto/in-toto-golang> — its verifier reproduces
the Python implementation's warning-only command alignment; it is another
implementation of the defect, not a hard-failing remedy. Read and cited below
for exactly that reason.

- **in-toto layout verification** — `in_toto_verify()` calls
  `verify_command_alignment`, but that function only compares the recorded
  command with caller-supplied layout data and emits `LOG.warning` on mismatch.
  <https://github.com/in-toto/in-toto/blob/v2.3.0/in_toto/verifylib.py>
  License: Apache-2.0 — permissive and compatible with this repository.
  Weakness: the mismatch never fails, and neither the layout nor
  `layout_key_dict` is bound to a content digest or committed trust root; the
  shipped field remains advisory and forgeable.
  Vendored: docs/adr/prior-art/ADR-001/in-toto-verifylib.py blob:64f11fb8cb25f556732ead52cda300fde31aaf62
- **DSSE's pre-authentication encoding rationale** — it explains why signed
  bytes include `payloadType`, preventing one message shape from being verified
  as another and demonstrating that security-relevant context belongs inside
  the authenticated bytes.
  <https://github.com/secure-systems-lab/dsse/blob/v1.0.2/background.md>
  License: Apache-2.0 — permissive and compatible with this repository.
  Weakness: this is design rationale, not executable code; it assumes the
  verifier already has the correct public key and says nothing about binding
  that trust root, so by itself it enforces nothing.
  Vendored: docs/adr/prior-art/ADR-001/dsse-background.md blob:8a9cc46d7b7eaebd58f6e44296f419f429056285
- **in-toto-golang's step command alignment** — `VerifyStepCommandAlignment` is
  the same control implemented independently in Go, read to establish that the
  advisory behaviour is the design and not one project's bug.
  <https://github.com/in-toto/in-toto-golang/blob/v0.11.0/in_toto/verifylib.go>
  License: Apache-2.0 — permissive and compatible with this repository.
  Weakness: the function returns nothing (`verifylib.go:451`) and a mismatch only
  prints (`:472`); worse, both sides are joined into one space-separated string
  before comparison (`:467-470`), so a two-element argv and the same text split
  into four compare equal — the structure the check exists to pin is erased
  before it is checked. An invalid payload also `return`s (`:465`), abandoning
  every later step in silence.
  Vendored: docs/adr/prior-art/ADR-001/in-toto-golang-verifylib.go blob:de9dfa7e647b9022c406c807363a2ae0df0ec47b

SLSA locates the real control in a trusted control plane rather than the tenant:
<https://slsa.dev/spec/v1.0/requirements>. **in-toto is prior art for our defect,
not our fix**: adopting `expected_command` as specified would ship a control that
only warns.

## Considered Options

1. **Adopt `expected_command` as specified** — declare the command, warn on
   mismatch. Rejected: a non-blocking check is decoration, and this project
   refuses gates that cannot block.
2. **Pin a digest of the executable's contents in the catalog.** Rejected:
   brittle — every toolchain upgrade breaks every gate, and the catalog is
   committed and shared across machines.
3. **Declare argv in the catalog, compare by digest, hard-fail; resolve `argv[0]`
   in the kernel and refuse a resolution inside the worktree.** Chosen.
4. **Also record and gate on an output digest.** Rejected for this slice: nothing
   here would verify it, and stdout is not deterministic. Deferred.
5. **Absolute `command[0]` in the catalog.** Rejected: it appears to close PATH
   shadowing and does not — the toolchain sits in worker-writable paths
   (`~/.local/bin/uv`), so a worker sharing the uid rewrites the named binary.
   It also makes the trust root machine-specific. SLICE-004 owns this.

## Decision Outcome

In the context of a kernel that spawns the observed process itself, facing prior
art whose command binding is advisory and PATH-forgeable, we chose to declare
argv in the committed catalog and compare it by digest as a hard failure, plus
resolve `argv[0]` in the kernel and refuse a resolution inside the subject
worktree, to make a trivial command unable to satisfy a substantive claim,
accepting that argv equality is brittle against benign rewordings.

Concretely: `gates.yaml` claim entries become `{claim_id, command: [argv]}`;
`Claim` gains `command_digest`; `Evidence` gains `command_digest` and
`executable_path`, both signed; `satisfies()` requires digest equality;
`SIGNED_FIELDS` goes 5 → 7 and the domain string `ranex-evidence-v1` → `v2`.

### Consequences

- A trivial command no longer satisfies a substantive claim by an honest route.
- v1 records are refused, not migrated. `governance/evidence.json` is gitignored
  and no signed evidence is committed, so there is nothing to migrate; a silent
  v1 acceptance path would be a downgrade attack against this whole change.
- **`landing` loses `contracts-validated`.** Nothing produces it, and nothing
  now can without a real validator. STATE.md's standing instruction is "write one
  or amend the gate; do not fake the claim" — the claim is dropped and the debt
  stays recorded. A placeholder command would be faking it.
- **The binding is stated, not yet observed.** A keyholder can still sign a record
  naming the bound command while running something else. That is SLSA's L2/L3
  distinction, and it is SLICE-004's job. This ADR does not close it.
- `sh -c "…"` remains a hole by construction: binding argv exactly does not
  constrain what the argv *does*. Catalog review is a human control here.

### Confirmation

`Evidence.satisfies()` returns False when `command_digest` differs from the
claim's, asserted at the kernel boundary in
`tests/unit/test_claim_command_binding.py` and end-to-end in
`tests/e2e/test_claim_command_binding_cli.py`. `run` exits non-zero when
`argv[0]` resolves into the worktree — asserted in
`tests/security/test_executable_path_confinement.py`, which is where the
containment tests actually live. The `-- true` attack is asserted refused in
`tests/security/test_slice003_command_binding.py`. If any of those pass while
the binding is removed, the check is wrong, not the code.

## Improvements on the prior art

1. **Hard-fail instead of warn.** in-toto *cannot* enforce this — it does not
   control the functionary's machine, so a mismatch can only be advisory. Ranex
   spawns the process itself (`cli/main.py:690`), so refusal is available and we
   take it.
2. **In-tree executables are refused. PATH aliasing is NOT closed.** An earlier
   draft of this ADR claimed it was; audit reproduced a gate PASS with a fake
   `pytest` shadowed on `$PATH` from outside the worktree, so the claim was
   false and is withdrawn. What holds: the kernel resolves `argv[0]` once,
   refuses a resolution inside the subject worktree, executes the checked inode,
   and records the resolved path as a signed field re-checked at evaluation. The
   real guarantee is **"argv matched and the binary was not in the tree"** — an
   unbounded set. Closing it needs SLICE-004's observer or a pinned executable
   digest.
3. **No unverified byproducts.** in-toto records stdout/stderr and then does not
   check them. We record neither. A field nothing verifies is decoration, and
   this project refuses decoration in both directions.
4. **Replay across a changed binding dies for free.** Because the digest of the
   bound argv *is* the comparison, editing a claim's command invalidates evidence
   produced under the old one — no separate catalog-version field is needed.

## Architecture surface

Driven side. The gate catalog is a driven adapter
(`policy/adapters/configuration/yaml/slice_gate_loader.py`); the change adds a
field to the `Claim` it yields. The kernel change is in the domain
(`governed_execution/domain/verdict.py`) and stays a pure function. The CLI
(`cli/main.py`) is the driving adapter and gains argv resolution. No new port; no
new dependency direction. No diagram — one field crossing one existing boundary.

## Scope and threat delta

Governs which evidence satisfies which claim. STRIDE letters moved: **S** (a
trivial command spoofing a substantive one) and **T** (the readable command field
can no longer be swapped under a matching digest).

Explicit non-goal: constraining what a bound command *does* once it runs.
Deliberately out of scope: a worker holding the signing key — it can still forge
any record, and no part of this slice narrows that. SLICE-004 owns it.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Functional correctness | trivial command offered for a substantive claim | gate FAILs, exit non-zero |
| Security (integrity) | any signed field altered in a stored record | verification fails |
| Compatibility | v1 record presented to a v2 verifier | refused, never silently accepted |
| Performance efficiency | argv resolution added to each `run` | one `which` call, no measurable change |

## Reversibility

Door: one-way

The signed field set and domain string are on-disk format. Once v2 records exist,
reverting to v1 means every record produced under v2 fails verification. Rolling
back requires discarding evidence, not just reverting code. The catalog schema
change is two-way — old bare-string catalogs can be restored by hand.

## Sad paths

Derived by equivalence partitioning over the catalog schema, and boundary/
tamper analysis over the signed field set.

| # | Input | Required behaviour |
|---|---|---|
| 1 | claim entry is a bare string (old schema) | refuse at load, message names the new shape |
| 2 | claim mapping has no `command` | refuse at load — undefined satisfaction cannot block |
| 3 | `command` is `[]`, a bare string, or holds non-strings | refuse at load |
| 4 | duplicate `claim_id` in one gate's `required_claims` | refuse at load |
| 5 | `run` argv matches no bound claim | evidence recorded, satisfies nothing, gate FAILs |
| 6 | argv correct but permuted | different digest, does not satisfy |
| 7 | argv equivalent, spelled differently (`-q` vs `--quiet`) | does not satisfy — exactness over convenience |
| 8 | `command_digest` edited in a stored record | signature verification fails |
| 9 | readable `command` edited, digest left intact | signature verification fails |
| 10 | v1-domain signature presented | refused at admission — no silent downgrade |
| 11 | `argv[0]` resolves inside the subject worktree | `run` refuses to execute |
| 12 | `argv[0]` is a symlink outside the repo pointing into it | resolved first, then refused |
| 13 | `argv[0]` cannot be resolved at all | `run` refuses with a named error |
| 14 | `executable_path` edited in a record | signature fails; also re-checked at evaluate |
| 15 | two records for one claim, one bound and one not | the unbound one must not satisfy |
| 16 | claim required, zero evidence | FAIL — absence blocks, unchanged |
| 17 | keyholder signs a record naming the bound command, runs another | **not caught** — SLICE-004 |
| 18 | `argv[0]` shadowed on `$PATH` by a binary outside the tree | **not closed** — needs SLICE-004 or a pinned digest |
| 19 | hard link outside the tree to an in-repo file | refuse — identity is `(st_dev, st_ino)`, not path |
| 20 | resolved path swapped between check and spawn | execute the checked fd, never re-open by path |
| 21 | committed in-repo symlink selecting an outside binary | refuse — same root cause as 18 |
| 22 | two records for one claim disagreeing on exit code | FAIL and report the contradiction |
| 23 | a flag naming an arbitrary untracked path as exempt | must not exempt it from the dirty-tree check |
| 24 | committed `conftest.py` neutering the bound suite | **not caught** — the tree defines the check |
| 25 | bind mount giving an in-repo inode an outside name | refuse — `st_nlink` never counts a mount, so identity cannot be gated on it |
| 26 | a worktree directory unreadable during the identity scan | refuse — a scan that cannot answer must not answer "no" |
| 27 | contradicting record deleted from the evidence file | **not caught** — the file is not append-only; SLICE-004 |
| 28 | producer id a visual lookalike of the approver's | **not caught** — no-self-approval compares strings; SLICE-005 |
| 29 | worktree directory closed to force the refusal in 26 | availability only — every run FAILs, and an unrun gate already FAILs; the message names the directory so it reads as an attack and not as a bug |
| 30 | inherited environment retargets the bound binary (`PYTHONPATH`, `LD_PRELOAD`, `NODE_OPTIONS`) | **not caught** — survives an absolute `command[0]`, and a denylist of variable names is not a control; SLICE-004 |

## Test strategy

Red-then-green, tests frozen before implementation and authored by a different
agent than the implementer — the same separation in-toto's advisory prescribes.
Every check above was observed failing before any `src/` change.

Levels, unit-heavy as the pyramid prescribes:

- `tests/unit/test_claim_command_binding.py` — `satisfies()` and digest
  computation at the domain boundary. Sad paths 5–7, 15, 16.
- `tests/contract/test_gate_catalog_claim_commands.py` — catalog schema refusals
  at load. Sad paths 1–4.
- `tests/security/test_slice003_command_binding.py` — tamper and downgrade. Sad
  paths 8–10, 14.
- `tests/e2e/test_claim_command_binding_cli.py` — the `-- true` attack and the
  worktree-containment refusal through the real CLI. Sad paths 11–13.
- `tests/security/test_slice003_audit_defects.py` — the seven fraudulent PASSes
  five audits reproduced. Sad paths 18–23 and 30; 18 and 30 are strict xfails,
  not passes. 30 has a green control test beside it and 18 asserts its
  preconditions inline, so neither can xfail for the wrong reason.
- `tests/security/test_slice003_bind_mount_identity.py` — identity where the
  link count and the device both lie. Sad paths 25–26. The bind-mount
  reproduction runs the CLI inside a real unprivileged mount namespace via
  `bwrap`; it is skipped only where no such namespace can be had, and that skip
  is loud because a silently-skipped security test is worse than none.

E2E hermeticity: each test builds its own repo and keypair under `tmp_path`, no
shared mutable state, no sleeps, no ambient environment reads.

Coverage: no global percentage — assertion-free suites reach 100%. Every sad path
above except 17 maps to a named test; 17 is declared uncatchable in this slice
rather than tested, which is the honest outcome.

## Code review checklist

- Does `satisfies()` compare the digest, not the readable string?
- Is `command_digest` in `SIGNED_FIELDS`, and does removing it break a test?
- Is the worktree-containment check applied after symlink resolution?
- Does any test still assert that a trivial command satisfies a claim?
- Does the catalog loader *refuse* an unbound claim rather than defaulting it?
- Do the frozen tests assert behaviour rather than the exact constructor shape?
- Does any new field go unverified anywhere in the codebase?

## More Information

Format defined by `docs/adr/ADR-000-how-we-write-adrs.md`. Supersedes nothing.

Open question deferred to SLICE-004: once the signer observes execution, should
`executable_path` become an executable *digest*? That is only meaningful once the
worker cannot choose what gets hashed.
