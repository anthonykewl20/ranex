# SLICE-020 — judgment identity and verdict read channel

**Status:** done
**Closed:** 2026-08-13
**Opened:** 2026-08-12
**Priority:** P0 — the harness cannot read a verdict, and prose is the only cause
interface today.
**ADR:** `docs/adr/ADR-019-the-verdict-read-channel.md` and
`docs/adr/ADR-020-cause-is-structure-not-prose.md` (accepted).

## Session-sized result

One kernel-first change makes judgment identity durable and readable. The kernel
returns one ordered tuple of structured five-kind claim causes while preserving
today's `reason` bytes, exposes self-approval as data, and moves its frozen digest
deliberately. A new projection composes the kernel result with admission's seven
Rejection reasons, carrying Record `self_approval` and Rejection `producer_id`.
It validates the cross-language publication subset, signs the exact projected
fields with a dedicated `kernel-verdict-signer` under `ranex-verdict-v1`, and
publishes through the one shared durable atomic writer. A reader classifies every
closed transport/trust/context state without a default arm. The harness
`packages/schema/src/verdict.ts` extension is a later harness-lane change.

## Exact owned paths

Product implementation may change only:

- `src/ranex/governed_execution/domain/verdict.py`
- `src/ranex/governed_execution/domain/admission.py` only if projection-safe
  Rejection serialization requires it; its seven-reason behavior may not widen
- `src/ranex/foundation/verdict_signing.py` (new)
- `src/ranex/foundation/atomic_writer.py` (new shared writer)
- `src/ranex/governed_execution/verdict_projection.py` (new)
- `src/ranex/governed_execution/verdict_publication.py` (new)
- `src/ranex/governed_execution/verdict_reader.py` (new)
- `src/ranex/cli/host_confinement.py` (migrate its existing caller to the shared
  writer; no source module may import this CLI module)
- `src/ranex/cli/main.py` (replace lines 830–855's duplicate cause recomputation
  with the projection and invoke publication; stdout stays byte-identical)
- `src/ranex/policy/adapters/configuration/yaml/producer_keyring.py`
- `governance/producers.yaml` and the gitignore rule for the publication directory
- `tests/contract/test_kernel_unchanged.py` (only `KERNEL_DIGEST` and its
  deliberate-boundary explanation in the implementation commit)
- the frozen test paths and `governance/suite_manifest.json` named below
- this slice, `docs/STATE.md`, and `README.md` only when closing

Explicitly not owned: journal schema, gate/evidence/approval signing domains,
evaluation signature/purity, harness files, board presentation, freshness via
journal sequence/link, approver authentication, or harness confinement.

## Frozen contract

### Kernel partition and projection

`ClaimCause` is immutable data with `claim_id: str`, `cause: str`, and optional
`detail`; construction rejects empty cause. `_diagnosis()` computes one ordered
tuple over exactly `contradicted`, `failed`, `mismatched`, `stale`, and `absent`.
Its sixth internal bucket, suite failure text, is `detail` on `failed`, never a
sixth kind and never concatenated into `claim_id`. `Evaluation` gains `causes`
and boolean `self_approval`. Every existing input produces byte-identical
`reason`; self-approval has empty causes and `self_approval=True`.

The projection, not `evaluate()`, composes admission. It emits the harness Record
fields `verdict`, `gate_id`, `subject_digest`, `subject_lane`, `catalog_digest`,
`approver_id`, `failing_rule`, `missing_claims`, `considered`, `causes`,
`rejections`, `self_approval`, `reason`, and `record_digest`. Rejections carry
exactly `index`, `reason`, `detail`, nullable `claim_id`, and nullable
`producer_id`. Refused named claims become `refused`; rejections without a usable
claim become `unattributable`; neither is recomputed in CLI presentation.
Duplicate causes and causes naming non-required claims refuse projection.

### Signing, validation, publication, and reading

`governance/producers.yaml` gains a separate `verdict_signer` object with exact
identity `kernel-verdict-signer` and one Ed25519 public key. That identity is
forbidden in `producers`; producers and approvers cannot sign verdicts. New
`verdict_signing.py` mirrors `approval.py`: exact field set is the Record above
minus `record_digest`, payload type is the asserted literal
`application/vnd.ranex.verdict.v1+json`, and domain bytes are exactly
`b"ranex-verdict-v1\n"`. Cross-domain signatures fail. Zero signatures refuse.

Before hashing or signing, publication recursively refuses every float (including
finite values), integer outside TypeScript's safe range `[-(2**53-1), 2**53-1]`,
and non-BMP Unicode scalar in keys or values. This is a publication validator,
not a change to `canonical_json`, which continues to refuse only NaN/Infinity.
`record_digest` is SHA-256 over the validated exact signed Record fields.

Extract `_write_report_atomic` mechanics to `foundation/atomic_writer.py` and
migrate host qualification to it. The shared writer retains dot-temp `O_EXCL`,
mode 0444, complete writes, file fsync, descriptor-relative replace, parent fsync,
rollback, and cleanup. Publication never imports `host_confinement.py`.

The reader returns a closed state for absent, unreadable/malformed, unsigned,
bad-signature, unknown-signer, wrong-payload-type, missing-key, context-mismatch,
unknown-cause, and verified records. Its mapping is total with no default arm.
A verified signature still refuses when subject, gate, catalog, or approver does
not match the requested context. Unknown causes remain visible as unclassified
and block; they never become a known cause. Freshness remains explicitly
unestablished across publication crash or reader restart.

## Deterministic acceptance gates

1. Every `_diagnosis()` branch yields the ordered structured cause and today's
   exact reason bytes; suite detail is failed detail, and self-approval is an
   evaluation marker. `tests/unit/test_gate_verdict.py`.
2. Empty cause, duplicate cause, and non-required claim cause refuse.
   `tests/unit/test_gate_verdict.py` and `tests/unit/test_verdict_projection.py`.
3. The projection exactly matches the extended harness wire, including Record
   `self_approval`, nullable Rejection `producer_id`, and all seven rejection
   reasons. `tests/unit/test_verdict_projection.py` and
   `tests/unit/test_evidence_admission.py`.
4. Evidence, approval, and verdict signatures are pairwise domain-separated;
   verdict payload type and exact signed fields are asserted.
   `tests/unit/test_evidence_signing.py` and `tests/unit/test_verdict_signing.py`.
5. The committed keyring exposes exactly one dedicated verdict signer, refuses
   missing/empty/aliased roles, and never admits it as a producer.
   `tests/contract/test_producer_keyring.py`.
6. The publication validator refuses floats, unsafe bigints, and non-BMP keys or
   values before signing. `tests/unit/test_verdict_publication.py`.
7. Both qualification and verdict publication use one shared atomic writer;
   torn publication is unnameable, rollback preserves the prior verdict, and no
   `src/` module imports `host_confinement.py`.
   `tests/unit/test_verdict_publication.py`.
8. Reader states cover bad signature, unknown signer, wrong payload type, zero
   signatures, missing key, subject/gate/catalog/approver mismatch, unknown
   cause, malformed, absent, and verified, with no default arm.
   `tests/unit/test_verdict_reader.py`.
9. CLI stdout remains byte-identical under pipe and pty after extracting its
   refused/unattributable partition. `tests/contract/test_verdict_presentation.py`.
10. Delegated child environments contain neither evidence nor verdict signing
    keys and cannot receive a writable publication path.
    `tests/unit/test_delegation.py`.
11. `KERNEL_DIGEST` moves in the implementation commit, with no relaxation of
    its check. `tests/contract/test_kernel_unchanged.py`.

## Sad-path mapping

| Failure | Required result | Gate |
|---|---|---|
| No published file | distinct absent state, never PASS | 8 |
| Bad signature / unknown signer / missing key | distinct closed states | 8 |
| Wrong payload type / zero signatures | refuse before decode | 4, 8 |
| Subject or judgment context differs | context mismatch, never display | 8 |
| Unknown cause | unclassified and blocking | 8 |
| Empty/duplicate/non-required cause | kernel/projection refusal | 2 |
| Float, unsafe bigint, or non-BMP scalar | publication refusal | 6 |
| Crash before rename | no new readable name | 7 |
| Crash after prior PASS | prior PASS may remain; freshness unestablished | 7, 8 |
| Harness is compromised at same uid | out of scope; no authenticity claim | 8 |
| Dedicated signer aliases a producer | keyring refusal | 5 |
| CLI extraction rewords output | byte comparison fails | 9 |

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q tests/unit/test_gate_verdict.py tests/unit/test_evidence_signing.py tests/unit/test_evidence_admission.py tests/unit/test_verdict_signing.py tests/unit/test_verdict_projection.py tests/unit/test_verdict_publication.py tests/unit/test_verdict_reader.py tests/contract/test_producer_keyring.py tests/contract/test_verdict_presentation.py tests/unit/test_delegation.py
uv run --frozen pytest -q tests/contract/test_kernel_unchanged.py
uv run --frozen pytest -q
uv run --frozen mutmut run
```

## One-way door and stop conditions

`KERNEL_DIGEST` and `record_digest` move deliberately, and
`ranex-verdict-v1` becomes permanent once any record is signed. The implementer
must stop rather than change `reason` bytes, add an eighth kernel cause, import
`host_confinement.py`, make the harness a signer, weaken exact-field validation,
or claim same-uid compromise/freshness is solved.

## Not in this slice

The harness `verdict.ts` extension and board reader/rendering, journal-bound
freshness, harness confinement, board actions, approval authentication, and any
new cause are follow-ups.
