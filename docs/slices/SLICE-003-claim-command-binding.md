# SLICE-003 — claim↔command binding

**Status:** open
**Opened:** 2026-08-01
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
