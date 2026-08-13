# ADR-020 — cause is structure, not prose

**Status:** accepted
**Date:** 2026-08-11
**Decision-makers:** repo owner
**Slice:** `not yet opened — shares the kernel slice with ADR-019 and waits on SLICE-017. BOARD-02 is this decision; BOARD-05's exhaustive cause renderer queues behind it`

## Context and Problem Statement

Seven distinct events reach a caller as "this claim is not satisfied", and only
one of them is work never done. `_diagnosis()` in `verdict.py` partitions
unsatisfied claims into five kinds — contradicted, failed, mismatched, stale,
absent — with suite detail prefixed onto the claim id; `cmd_gate_evaluate` adds
two more from the admission layer, refused and unattributable.

Both then throw the structure away. `_diagnosis()` joins its five buckets into
one English string with `"; "`, and that string is all that escapes: `Evaluation`
exposes `missing_claims` (ids, no cause) and `reason` (all causes, one sentence).
The CLI recomputes refused and unattributable and discards those too.

So a renderer wanting to show seven causes distinctly has two options: parse the
prose, or receive a field that does not exist. Parsing is the defect that
reopened SLICE-002 — reporting a forgery under the wording reserved for honest
absence lets an attacker choose the report by choosing which field to tamper
with. ADR-018 committed to closing this and deliberately left the shape open.

## Decision Drivers

- The seven causes are **unordered**. `absent` is not a worse `failed`.
- Only one of the seven means work never done; conflating any other with it is
  the failure this project exists to prevent.
- `evaluate()` is a pure function of (gate, evidence, subject, approver). That
  invariant decides what may and may not enter `Evaluation`.
- `reason` must stay byte-identical: humans read it and the journal records it.
- A renderer must be unable to receive a cause it has not handled.
- The kernel is digest-frozen; moving it is a decision, not a side effect.

## Prior art

Searched: GitHub **code** search (`gh search code`) over judged-result models that
cross a process boundary — condition/reason vocabularies, policy results, admission
decisions — enumerating consumers as well as producers. Tags were dereferenced to
40-hex commits and every raw URL fetched and hashed. SARIF was read as an
implementation, never as a schema document.

- [Kyverno rule status](https://github.com/kyverno/kyverno/blob/945ac9ce8546ea6cd51370f24b615148c577da5e/pkg/engine/api/rulestatus.go)
  declares only a five-value closed set as typed string constants: `Pass`, `Fail`,
  `Warn`, `Error`, and `Skip`; it contains no accessor or outcome derivation.
  License: Apache-2.0.
  Weakness: the string-kinded type cannot make downstream switches exhaustive;
  the separate vendored CLI consumer demonstrates the resulting default branch.
  Vendored: docs/adr/prior-art/ADR-020/kyverno-rulestatus.go blob:42bac5a9f4ce62cf12480d6349a2d9e533d8ef67
- [Kyverno CLI result counter](https://github.com/kyverno/kyverno/blob/945ac9ce8546ea6cd51370f24b615148c577da5e/cmd/cli/kubectl-kyverno/processor/result.go)
  switches over that same five-value set five times in 197 lines: four switches
  drop an unrecognised status silently, one maps it to `Fail`; none reports it.
  License: Apache-2.0.
  Weakness: Go does not exhaustiveness-check a switch over a string-kinded type,
  so a closed set enforced by convention is handled two ways in one file.
  Vendored: docs/adr/prior-art/ADR-020/kyverno-cli-result.go blob:be8849cb6534f2a4286f5c0ed683e31f6a43756a
- [Kubernetes apimachinery errors](https://github.com/kubernetes/kubernetes/blob/0f29094e5b73085e3802ecc1298ecae13866bfe6/staging/src/k8s.io/apimachinery/pkg/api/errors/errors.go)
  guards its nearest-value fallback with a `knownReasons` registry, so an
  unrecognised reason is inferred from the HTTP code but a recognised one is
  never overridden — the strongest form of a fallback that must exist.
  License: Apache-2.0.
  Weakness: repeated at thirteen call sites, and `IsTooManyRequests` omits it —
  its comment concedes backward compatibility now freezes the bug in place.
  Vendored: docs/adr/prior-art/ADR-020/k8s-apimachinery-errors.go blob:7b57a9eb6cabe741dd5aead43cbc45f14646a686
- [Knative condition set](https://github.com/knative/pkg/blob/39ebae2ee2dc245299eb6a3b12034fb624b86156/apis/condition_set.go)
  ranks twice to roll many causes into one: it discards everything below `Error`
  severity, sorts by transition time, and propagates the winner to the top.
  License: Apache-2.0.
  Weakness: severity is derived from a static registration list rather than from
  what happened, and an unevaluated dependent surfaces as a blank cause.
  Vendored: docs/adr/prior-art/ADR-020/knative-condition-set.go blob:940d1b3ab32de2695ce21356952961c7b57cbeb8
  Vendored: docs/adr/prior-art/ADR-020/LICENSE-APACHE-2.0.txt blob:261eeb9e9f8b2b4b0d119366dda99c6fd7d35c64

Rejected: [microsoft/sarif-sdk](https://github.com/microsoft/sarif-sdk) is the only
implementation read that rejects the whole document on an unknown enum member, and it scopes its
one ranked axis by construction-time exception. GitHub resolves its licence as `NOASSERTION`, the
ground ADR-018 refused conftest on, so it informs this decision and is not copied.

Rejected: [OPA constraint framework](https://github.com/open-policy-agent/frameworks) carries the
cause as `Msg string` and nothing else, then orders violations by sorting those English messages —
deployed at scale, and the exact end state this ADR exists to avoid.

Rejected: [Tekton Dashboard status icon](https://github.com/tektoncd/dashboard) is where the
producer-to-pixel chain dies: a hand-written ladder branches on status rather than reason, so a
forged signature and an unresolved reference draw the same icon.

## Considered Options

1. **Parse `reason`** in the renderer to recover the cause.
2. **A structured per-claim cause on `Evaluation`**, with `reason` rendered from
   the same partition so the two cannot disagree.
3. **A structured cause computed a second time** at the projection boundary,
   leaving `_diagnosis()` alone.
4. **A severity rank** over the seven causes, coloured by rank.

## Decision Outcome

For seven unordered causes surviving only as English, we chose **option 2 — one
partition, computed once by `_diagnosis()`, returned as data, with the sentence
rendered from it** — so structure and prose cannot drift, accepting a change to
the digest-frozen kernel and `record_digest`.

Option 1 is forbidden: reworded prose would mislabel a forgery as absence.
Option 3 is the defect Kyverno demonstrates — the same closed set derived twice
diverges; the two derivations already disagree here. Option 4 is Knative's regret:
ranking erases six of seven causes.

Admission's `refused` and `unattributable` do **not** enter `Evaluation`.
Pure `evaluate()` cannot see rejections; the projection composes them once.

Self-approval is an evaluation-level refusal, not a claim cause: `Evaluation`
carries `self_approval` despite empty `missing_claims`; renderers consume the
marker and never parse `reason` to recover it.

Door: one-way

### Consequences

- Good: seven causes reach the screen as seven values, and `absent` can no longer
  be spent on a claim some record named.
- Good: `reason` is derived from the partition, so the sentence and the structure
  are one artifact and a test over every branch can prove they agree.
- Good: the projection composes kernel causes with admission rejections at one
  place, which is also where ADR-019's reader validates them.
- Bad: `Evaluation.as_record()` gains a field, so `record_digest` changes for
  every new evaluation. Old journal rows keep their digests; this is a boundary.
- Bad: `tests/contract/test_kernel_unchanged.py` goes red by design, and the
  implementer must set the new digest in the same commit and argue it.
- Neutral: the wire keeps `cause` as a string; the closed set is enforced on read.

### Confirmation

Frozen red-first tests, reviewed against the diff on disk. A test over every
branch of `_diagnosis()` — including contradiction, suite detail, and the
self-approval path that bypasses it — asserts the rendered sentence is
byte-identical to today's for the same inputs, and that the structure names the
same claims. A table test asserts the cause-to-presentation mapping is total,
with no default arm. Independent review, then a mutation gate over `verdict.py`.
As with ADR-019, **no outside-model panel ran**: the OpenRouter credential had
expired. The kernel-digest change must be argued in its commit message, which is
the one place this repository treats as the record for a deliberate kernel move.

## Improvements on the prior art

Kyverno names the distinction correctly and then loses exhaustiveness in its
unchecked CLI switches. Kubernetes guards its fallback
properly at thirteen call sites and then misses the guard at two
(`IsTooManyRequests`, `IsRequestEntityTooLargeError`), permanently.
Both failures are the same failure: **the closed set was enforced at every use
instead of once at the boundary.** So the validation happens at deserialisation,
and no renderer receives a value it could mishandle. There is no accessor that
merges kinds; if one is written, the review checklist below is where it dies.

Kubernetes' `StatusCause` is the shape worth adopting — a machine-readable tag, a
human-readable message, and a locus — but its tag is `+optional` with
`omitempty`, so a cause with no machine-readable type is legal. Here the tag is
required and non-empty, and a record missing it fails to decode rather than
defaulting, because absence blocks.

On unknown values this ADR deliberately diverges from the strictest thing read.
SARIF rejects the entire document when an enum member is unrecognised, which is
right for a file format and wrong for a screen: it would show the operator no
verdict at all, which is worse than one cause they cannot name. So an eighth
cause renders as `unclassified` and still blocks — never as the nearest known
cause, which is what Kyverno's `default: rc.Fail++` and Tekton's icon ladder do.

## Architecture surface

Changed: `_diagnosis()` returns the partition as data; the sentence becomes a
renderer over it. `Evaluation` gains a per-claim cause tuple plus an
evaluation-level `self_approval` refusal marker, and `as_record()` carries both.
`KERNEL_DIGEST` in `tests/contract/test_kernel_unchanged.py` moves.

Added: nothing outside the kernel. The two admission-derived causes are composed
at ADR-019's projection, from `admission.rejections`, which already carries
`index`, `reason`, `detail`, `producer_id` and a nullable `claim_id`.

Unchanged: `evaluate()`'s signature and purity, `reason`'s bytes, the journal
schema, and `Verdict`, which stays two-valued with no rank.

## Scope and threat delta

STRIDE. The threat this closes is Repudiation-adjacent and specific: an attacker
who tampers with one field of a record chooses which sentence the operator reads.
Structure removes that choice, because the cause is decided by which check failed
and not by which words the failure happened to produce. Spoofing, Tampering and
Information disclosure are unchanged — no new input is trusted, no new data
leaves, and `claim_id` stays nullable rather than being coerced to a claim, since
that coercion is precisely how a forgery gets filed as honest absence.

Non-goals: presentation, colour, glyph, and the board's layout. Out of scope: any
new cause. The seven are the seven the code already computes.

## Quality attributes

- Determinism: the same evidence produces the same partition and the same bytes.
- Honesty: an unclassifiable cause says so and blocks; it never borrows a name.
- Legibility: the sentence a human reads is generated from what a machine reads.
- Totality: the cause-to-presentation mapping is proven complete, not reviewed.
- Compatibility: readers widen; `reason` does not move.
- Latency is not a quality attribute here, and no cause is ever ranked.

## Reversibility

Door: one-way

The field is additive and append-only in the record, so readers widen rather than
break — but once a journal row carries a structured cause, the shape is in the
permanent record and can be superseded, never withdrawn. `record_digest` changes
at the same boundary and cannot change back without invalidating what was written
after it. That is why this is argued before the slice rather than during it.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 2 | A claim is both contradicted and missing | named once, under contradiction, as `_diagnosis()` already does; never counted twice |
| 3 | A claim has suite detail | carried as detail on the `failed` cause, not as a sixth kind, and never concatenated into the claim id |
| 4 | An admission rejection carries `claim_id: null` | the null survives to the screen; coercing it to a claim files a forgery as absence |
| 5 | A rejection names a claim the kernel called absent | the claim is `refused`, not `absent`; the absence wording is spent only on claims nothing named |
| 6 | The kernel gains an eighth cause | the wire accepts it, the reader renders `unclassified`, and it blocks; no renderer guesses |
| 10 | Self-approval refusal bypasses `_diagnosis()` | evaluation-level `self_approval` marker renders the refusal despite empty `missing_claims`; `reason` is not parsed |
| 11 | `record_digest` changes and something compares old to new | the boundary is declared; no code may compare digests across it |
| 13 | A cause tag arrives empty | fails to decode; an optional tag is the hole Kubernetes left and this closes it |
| 14 | A cause is duplicated for one claim | render it once under that claim; never count the claim twice |
| 15 | A cause names a non-required `claim_id` | refuse the unknown claim id rather than filing it under a required claim or counting it |

## Test strategy

Frozen before build, read-only to implementers, red then green. New filenames and
exact test names belong to the slice; the files below exist and are where the
behaviour being changed is currently pinned.

- `tests/unit/test_gate_verdict.py` — the partition is asserted over every branch
  of `_diagnosis()`: contradicted, failed, failed-with-suite-detail, mismatched,
  stale, absent, and the self-approval path that bypasses it. For each, the
  rendered sentence must be byte-identical to what the current code produces,
  and the structure must name the same claims in the same order.
- `tests/contract/test_kernel_unchanged.py` — expected red, and the digest is
  updated in the same commit that moves `verdict.py`. Nothing else in that file
  may be relaxed to accommodate the change.
- `tests/unit/test_evidence_admission.py` — the six rejection kinds stay a closed
  set, and a rejection with a null `claim_id` keeps the null.
- `tests/contract/test_verdict_presentation.py` — the CLI's stdout is unchanged
  by this refactor, byte for byte, under both a pipe and a pty.

Belonging to the slice: a table test asserting the cause-to-presentation mapping
is total over the closed set with no default arm; a test that an unknown tag
renders as unclassified and still blocks; and a property test that no ordering is
imposed, by asserting the rendered grouping is stable under input permutation.

## Code review checklist

- Is the sentence rendered from the partition, or computed beside it?
- Can structure and `reason` disagree, or does construction make that impossible?
- Does any renderer parse or regex-match `reason`? The wording is not an interface.
- Does any accessor merge two cause kinds for convenience?
- Is there a comparison, sort, or severity anywhere over the cause set?
- Is the tag required and non-empty at the decode boundary?
- Does `claim_id` stay nullable end to end, with no coercion?
- Did `reason` change by even one byte for any existing input?
- Was `KERNEL_DIGEST` updated in the same commit, with the reason in the message?
- Does the renderer's mapping have a default arm? It must not.

## More Information

Depends on ADR-018, which decided `Evaluation` would gain a structured cause
without deciding its shape, and pairs with ADR-019, which carries the result to
the harness. Both must land before the kernel slice opens.

The harness-side contract already exists as `packages/schema/src/verdict.ts` and
fixes the wire shape: `cause` a plain string, `claim_id` nullable, `detail`
optional, with `KNOWN_CAUSES` matched exhaustively and anything else shown as
unclassified. This ADR is the kernel half of that contract, and the divergence
from SARIF's reject-the-document behaviour is argued above rather than inherited.

ADR-011 governs the disclosure that no outside panel read this decision.
