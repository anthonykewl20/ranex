# ADR-045 — approval signing and batch verification CLI

**Status:** accepted
**Date:** 2026-09-02
**Decision-makers:** repo owner
**Issue:** #65 (operator-reachable authority creation and independent verification)

*Drafting note: authored by the documentation driver; the repo contract
(tests/contract/test_docs_discipline.py) imposes no external drafting step, and
the headless drafting assistant was unavailable this session (OAuth session
expired).*

## Context and Problem Statement

Issue #65: an owner must create fresh authority and qualify a batch through
supported workflows only. Two gaps block that. First, `sign_approval_payload`
(foundation/specification_abc.py) had no operator surface — approval envelope
C existed only when a test or fixture produced it, so no owner could mint one
from their own key. Second, `verify_qualification`
(governed_execution/application/specification_batch.py) was API-only: the
independent recheck of a completed qualification (A/B/C validation, protected
digests, subject binding, journal continuity, attestation admission) was
reachable from Python but from no installed command, leaving fixtures and
private helpers as the only witnesses.

## Decision Drivers

- Compose existing foundation/application functions; add no new crypto.
- Operator-reachable via the installed `ranex` entry point only.
- Preserve refusal discipline: E-BATCH-* codes exit 1, approve errors exit 2.
- No `SCHEMA_NUMBER` bump: stage pairs derive from the action enumeration.
- Judge/merge behavior must be byte-for-byte unchanged.
- Independent verification must not reuse publication-only controls.

## Prior art

Searched: GitHub code search 'attestation verification CLI exit code',
'sign approval payload private key CLI', 'in-toto verify command', and
installed-source inspection of pinned supply-chain verification tools.

- https://github.com/in-toto/in-toto/blob/v2.3.0/in_toto/in_toto_verify.py
  grounds: the verification half — a standalone operator command that loads
  layout plus public keys, re-runs the full verification, and returns 2 for
  argument errors, 1 for verification failure, 0 for pass; exactly the
  exit-code shape `task batch verify` adopts (0 PASS / 1 refusal).
  License: Apache-2.0 (in-toto contributors).
  Weakness: verification re-executes inspection subprocesses and trusts GPG
  keyring state, where this kernel verifies already-recorded evidence
  read-only against the committed keyring; and the copy passed through a
  text-converting fetch, so whitespace may differ from the raw upstream
  object (ADR-038 precedent).
  Vendored: `docs/adr/prior-art/ADR-045/in-toto-v2.3.0-in_toto_verify.py` blob:79ffe666fc562e8e2dfc05a5380e45883a92e209

- https://github.com/in-toto/in-toto/blob/v2.3.0/in_toto/in_toto_run.py
  grounds: the signing half — key loading happens in the CLI layer, not the
  library, so the private key is read exactly once at the operator boundary
  and the envelope is written only on success; `cmd_approve` composes the
  same way over `private_signing_key` + `sign_approval_payload`.
  License: Apache-2.0 (in-toto contributors).
  Weakness: it accepts a key at any path with any permissions and prompts for
  passwords interactively, where this kernel refuses group/other-readable
  keys (mode & 0o077), keys committable into the governed tree, and writes
  the envelope exclusively (`xb`); same text-fetch caveat.
  Vendored: `docs/adr/prior-art/ADR-045/in-toto-v2.3.0-in_toto_run.py` blob:c764f91f11c21108a6585e2bbe9a3b2299b633c0

- Rejected: https://github.com/testifysec/witness — its verification policy
  is fetched from an online archivist and gates on policy bundles, so the
  offline committed-keyring model here would depend on network state the
  kernel refuses to trust.
- Rejected: https://github.com/sigstore/sigstore-python — signing identities
  are bound to a transparency log and Fulcio certificates, an online trust
  root incompatible with the repository-local keyring and subject digest
  this approval envelope must bind.

## Considered Options

1. Register both commands in `build_parser()`, composing existing functions
   via `set_defaults(func=...)` — chosen.
2. Keep them API-only and document a Python recipe. Rejected: issue #65 is
   exactly that fixtures/private helpers must not remain the only path.
3. Fold verification into `task batch qualify`. Rejected: re-verification
   must be independent of the path that produced the artifact.
4. New standalone console scripts. Rejected: fragments the entry point
   ADR-040 unified.

## Decision Outcome

In the context of issue #65's fixture-authority gap, facing an API-only
verifier and an unsigned operator authority lifecycle, we chose registration
over existing foundation/application functions — no new crypto, no new
authority — accepting two more parser surfaces to document and test.

- **`ranex specification approve --payload <path> --output <path>`**: `cmd_approve` (cli/specification.py) composes `parse_canonical_payload` → `private_signing_key` (RANEX_SIGNING_KEY; refuses unset, missing, group/other-readable, or committable-into-repo keys) → `sign_approval_payload`; writes the canonical envelope exclusively (`xb`); prints `APPROVED  <output>  key_id=<key>`, exit 0; refusals print `ERROR  <exc>` on stderr, exit 2.
- **`ranex task batch verify --spec-packet A --artifact-manifest B --approval-envelope C --qualification <artifact> --target <repo> --journal <path>`**: `cmd_task_batch_verify` → `verify_qualification` — validate A/B/C bytes → `assert_abc_chain` → `_verify_protected` → subject binding → journal continuity → `_verify_qualification_facts` (journal-row binding, base/candidate/tip keyring equality, attestation admission); prints canonical facts JSON plus `PASS  qualification=<path>  VERIFIED`, exit 0; refusals exit 1 with `E-BATCH-*`; `trace_dispatch_group="task.batch.verify"`.
- **Schema**: `approve` appended to `_SPECIFICATION_ACTIONS` (schema.py:89) — the `cli.specification.approve.start/end` pair derives from the enumeration, so no `SCHEMA_NUMBER` bump.
- Judge/merge paths are untouched.

### Consequences

- The owner authority lifecycle (draft → advance → approve) and batch
  qualification verification are fully operator-reachable; no fixture or
  private helper is required to mint envelope C or to recheck a
  qualification.
- Independent verification reads only recorded evidence and the committed
  keyring; it cannot widen authority and cannot publish.
- The suite grows new coverage: approve arms in the specification CLI
  integration test, a new batch-verify contract file, in-journey verifier
  assertions, and the trace-schema action enumeration.
- The e2e journey retains a known skip where fixture ancestry is absent —
  documented, not smoothed over.
- Two more help-tree entries and two more documented commands to keep in
  sync with README/MAP/CLAUDE.md.

### Confirmation

`tests/contract/test_trace_schema.py` freezes the action enumeration —
`SPECIFICATION_ACTIONS` includes `approve`, so removing it turns the suite
red. `tests/integration/test_batch_verify_contract.py` runs the real
qualify→verify cycle and every refusal branch through the parser.
`tests/integration/test_specification_cli.py` freezes the approve success
and refusal arms. `tests/contract/test_docs_discipline.py` governs this
ADR's own shape, citations, and vendored digests.

## Improvements on the prior art

1. in-toto's exit codes conflate "argument error" with library exceptions;
   here 2 is reserved for approve refusals and 1 for E-BATCH verification
   refusals, each with a named code on stderr, not a traceback.
2. in-toto loads whatever key path it is given; `private_signing_key`
   refuses group/other-readable modes and keys committable into the
   governed tree before any signature exists.
3. in-toto-verify re-executes inspections; `task batch verify` is
   read-only over recorded evidence — verification cannot become a second
   execution authority.
4. Envelope output is exclusive-create (`xb`): an approve can never
   silently overwrite an earlier envelope.
5. Signing binds the committed keyring identity (key_id from the payload)
   rather than trusting key files alone, so a substituted key produces a
   verification failure downstream, not a forged approval.

## Architecture surface

- `src/ranex/cli/main.py` — `specification approve` action parser +
  `cmd_task_batch_verify` + `task batch verify` parser with
  `trace_dispatch_group`.
- `src/ranex/cli/specification.py` — `cmd_approve`, also bound in the
  standalone parser's action table.
- `src/ranex/governed_execution/application/specification_batch.py` —
  `verify_qualification` + extracted `_verify_qualification_facts` (the
  publication-refusal path now shares it).
- `src/ranex/observability/schema.py` — one tuple entry.

## Scope and threat delta

Registration and composition only: no new cryptographic primitive, no new
trust root, no change to confinement, journaling, judge, or merge. STRIDE
letters moved: none — the signing path reuses the existing key-discipline
refusals, and verification is read-only. Explicit non-goal: proving the
signed approval semantically correct (a well-signed envelope over a wrong
payload still verifies structurally); review of the payload is the control,
out of scope for the attacker model here.

## Quality attributes

| Attribute | Effect |
|---|---|
| Auditability | `specification approve` emits the `cli.specification.approve` stage pair; `task batch verify` deliberately emits no stage pair — it records no execution transition (ADR-040) |
| Compatibility | judge/merge and existing refusal vocabularies unchanged |
| Consistency | same registration shape and exit-code discipline as ADR-040 |
| Simplicity | zero new crypto, zero new glue beyond two cmd_ functions |
| Reversibility | delete the parsers and the tuple entry; both surfaces return |
| Testability | refusal branches frozen as expected-failure tests |

## Reversibility

Door: two-way

Removing the two parsers, `cmd_approve`/`cmd_task_batch_verify`, and the
`approve` tuple entry restores today's state exactly; no journal row,
golden, or schema number depends on either command existing. The extracted
`_verify_qualification_facts` stays useful to the publication-refusal path
either way.

## Sad paths

- RANEX_SIGNING_KEY unset, missing, group/other-readable, or inside the
  governed tree → `ERROR` on stderr, exit 2, no output file written.
- Malformed or non-canonical approval payload → `ERROR` from
  `parse_canonical_payload`, exit 2.
- `--output` already exists → the exclusive `xb` open raises, exit 2;
  an existing envelope is never overwritten.
- A/B/C inputs malformed or the chain disagrees → `E-BATCH-SCHEMA`,
  exit 1, no facts printed.
- Protected manifest digest mismatch → `E-BATCH-PROTECTED-ARTIFACT`,
  exit 1.
- Signed base, subject, HEAD, or refs/heads/main moved → 
  `E-BATCH-STALE-BASE`, exit 1.
- Qualification journal row absent, malformed, or unbound →
  `E-BATCH-PROTECTED-ARTIFACT`, exit 1.
- Attestation not admitted by base/candidate/tip keyrings →
  `E-BATCH-PROTECTED-ARTIFACT`, exit 1.
- `approve` removed from `_SPECIFICATION_ACTIONS` without the frozen test
  edit → trace-schema contract fails by design.
- README/CLAUDE.md/MAP drift from the parser surface → no test catches
  prose drift directly; review of this ADR's checklist is the control
  (declared uncaught, as in ADR-040).
- The e2e journey runs where fixture ancestry is absent → known declared
  skip, reported as skip, never as PASS.

## Test strategy

- `tests/integration/test_batch_verify_contract.py` (new) — full real
  qualify→verify cycle through the parser plus every refusal branch;
  expected-failure arms for each E-BATCH code above.
- `tests/integration/test_specification_cli.py` — approve success
  (keygen-path key, `APPROVED` line, canonical envelope) and refusal
  arms (missing key, malformed payload, overwrite) through both the
  standalone and registered surfaces.
- `tests/e2e/test_specification_batch_qualification.py` — in-journey
  verifier assertions; the journey's ancestry-absent fixture skip is a
  declared skip.
- `tests/contract/test_trace_schema.py` — action enumeration including
  `approve`.
- `tests/contract/test_docs_discipline.py` — governs this ADR: sections,
  budgets, citations, licences, weaknesses, vendored digests, NOTICE.
- Red-then-green: the contract and integration files were written against
  the unimplemented parser and observed red before the kernel tranche.

## Code review checklist

- [ ] Parser flags match this ADR verbatim; no flag added or renamed
      without editing this file in the same slice.
- [ ] `cmd_approve` composes only `parse_canonical_payload`,
      `private_signing_key`, `sign_approval_payload`; no new crypto.
- [ ] `verify_qualification` remains read-only; no publication-only
      control is reachable from `cmd_task_batch_verify`.
- [ ] Exit codes: 0 PASS, 1 E-BATCH refusal, 2 approve ERROR — verified
      through the installed parser, not by calling functions directly.
- [ ] Judge/merge diff is empty.
- [ ] Vendored digests recomputed on the review commit; NOTICE names both
      files with origin and licence.

## More Information

- Issue #65 — this decision; ADR-040 — the registration template and the
  specification group this extends; ADR-017/ADR-030 — the A/B/C authority
  and approval model the envelope belongs to.
- `docs/adr/prior-art/ADR-045/NOTICE.md` — provenance and licences for the
  vendored evidence.
- `src/ranex/cli/main.py` (`build_parser`, `cmd_task_batch_verify`),
  `src/ranex/cli/specification.py` (`cmd_approve`),
  `src/ranex/governed_execution/application/specification_batch.py`
  (`verify_qualification`, `_verify_qualification_facts`).
