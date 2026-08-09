# ADR-012 — the kernel merges

**Status:** accepted
**Date:** 2026-08-05 (accepted same day, owner, after REFUTE panel)
**Decision-makers:** repo owner
**Slice:** `SLICE-010` — closed 2026-08-06, all fourteen criteria proven

## Context and Problem Statement

[ADR-010](./ADR-010-first-delegation.md) ends with a kernel-journalled CANDIDATE
whose satisfying evidence is bound to a subject digest, but promotion
is manual and unvalidated. It explicitly defers merge-time freshness, candidate
edits to the gate catalog or keyring (sad path 10), and collisions between
concurrent tasks (sad path 18). This ADR completes that boundary and supersedes nothing.

The subject is exactly `"sha256:" + hex_sha256(canonical JSON bytes({"tree": <hex Git tree OID>}))`,
implemented by `subject_digest_for` at `src/ranex/cli/main.py:153`. This
repository currently assumes Git's SHA-1 object format,
so commit and tree OIDs are 40 hex characters. An object-format migration changes
the signed bytes and requires an explicit migration.

Measured in a scratch repository on 2026-08-05, `git update-ref refs/heads/main
<C> <T>` moved `main` from T to a completely unrelated orphan C. The old-value
argument is value equality, not ancestry. CAS closes a race; it does not prove a
fast-forward, that the published tree was judged, or that approval is current.

## Decision Drivers

- The kernel merges; neither the harness nor a human push may publish governed work.
- What is published must be exactly the subject that was judged and approved.
- Fast-forward ancestry and an expected-old ref update are different checks.
- A same-tree commit with different parents is not the approved commit.
- Gate catalog and keyring are trust roots, not candidate-controlled inputs.
- Freshness must remain deterministic: causal state, never wall-clock time.
- `evaluate()` stays pure and unchanged; merge composes existing kernel results.
- Every crash and race must leave an append-only, honest journal explanation.

## Prior art

- Searched: `gh search repos` for `merge queue revalidate checks before merge`, `merge gate tested commit merge`, `speculative merge gating`, `merge train rebase verify`, and `tested candidate promotion`; all returned zero or no useful whole-problem result.
- Searched: corrected `gh api -X GET search/repositories` for `gating merge system revalidate promotion` returned zero; an earlier POST-shaped call returned 404 and is recorded in the research summary.
- Searched: component queries included `approval bound commit sha merge bot`, `protected policy files merge gate`, `atomic compare and swap git ref merge queue`, `git merge-tree write-tree`, and `in-toto final product verification`; targeted `gh api search/code`, GitLab REST, OpenDev, `git ls-remote`, Leitir, and opensrc located the implementations below.
- **Prow Tide** rechecks current base/head-bound jobs and head freshness before merge; copy the boundary, not its provider/controller surface: <https://github.com/kubernetes-sigs/prow/blob/7f8580d8da573bcb9e4fe716358d4c0ee1d24b38/pkg/tide/tide.go>
  License: Apache-2.0.
  Weakness: SHA/status freshness is not a canonical merged-tree proof; the final API guards head, not base, and a partial batch may leave untested state.
  Vendored: docs/adr/prior-art/ADR-012/prow-tide.go blob:6219e99f695dcae094c7ddeaee48d97bd5e530b3
- **Gerrit MergeOp** reloads NoteDb state and rechecks submit requirements, permissions, current patch set and mergeability at submit; copy re-evaluation, not NoteDb/JGit architecture: <https://github.com/GerritCodeReview/gerrit/blob/017823543c322cd1b3500bdc91d8b5a62baf5caf/java/com/google/gerrit/server/submit/MergeOp.java>
  License: Apache-2.0.
  Weakness: `MergeOp` has a submit-rule bypass and no Ranex digest, policy, approval-envelope, or journal-row binding.
  Vendored: docs/adr/prior-art/ADR-012/gerrit-merge-op.java blob:eddee821855e644c63bf3d1b82fe2f9613d87a2d
- **Zuul merger** constructs the speculative future commit and feeds that state to tests; copy future-state identity, not its scheduler/executor stack: <https://github.com/openstack-infra/zuul/blob/dc9347c1223e3c7eb0399889d03c5de9e854a836/zuul/merger/merger.py>
  License: Apache-2.0.
  Weakness: it has no Ranex approval/digest binding or demonstrated final tree-OID CAS, and its operational surface dwarfs this kernel.
  Vendored: docs/adr/prior-art/ADR-012/zuul-merger.py blob:798cc90a9f7a6362ffe44267d5ddce1a485e4684
- **Git merge-tree**, `v2.51.0`, computes an in-core result tree; copy the clean-result contract, never its GPL code into product code: <https://github.com/git/git/blob/c44beea485f0f2feaf460e2ac87fdd5608d63cf0/builtin/merge-tree.c>
  License: GPL-2.0-only — vendored research evidence, not MIT product code.
  Weakness: it prints a tree OID even when the merge is unclean; it supplies no evidence, approval, policy check, or publication guarantee.
  Vendored: docs/adr/prior-art/ADR-012/git-merge-tree.c blob:203f0e6456a751448f81efb59bf4e67ce2cb2425
- **Git files ref backend**, `v2.51.0`, checks the expected old OID while holding the update lock; copy explicit CAS semantics, not backend internals: <https://github.com/git/git/blob/c44beea485f0f2feaf460e2ac87fdd5608d63cf0/refs/files-backend.c>
  License: GPL-2.0-only — vendored research evidence, not MIT product code.
  Weakness: one internal backend; CAS prevents a lost update but proves neither ancestry nor evidence, approval, and policy freshness.
  Vendored: docs/adr/prior-art/ADR-012/git-refs-files-backend.c blob:088b52c740b9ff0587fe3935da33f69478ae1c5d
- **in-toto verifylib**, `3.1.0`, verifies owner policy, authorized signatures, thresholds and artifact agreement before final products; copy verifier ordering, not inspections/CLI: <https://github.com/in-toto/in-toto/blob/c82fe5d21aaa61c7f1a213db20a46f10bb3f411a/in_toto/verifylib.py>
  License: Apache-2.0.
  Weakness: command alignment is warning-only, revocation needs a new layout, and it supplies no Git CAS or producer-versus-approver rule.
  Vendored: docs/adr/prior-art/ADR-012/in-toto-verifylib.py blob:cae4498bb0636c68b814e8b4d8dba5c0cef29b76
- Rejected: GitLab merge trains <https://gitlab.com/gitlab-org/gitlab/-/tree/v18.3.1-ee/ee/app/services/merge_trains> test merged results, but the decisive orchestration is EE-restricted and the Rails platform is not a proportionate base.
- Rejected: marge-bot <https://github.com/smarkets/marge-bot> rebase-checks an exact SHA but is GitLab-bound and supplies no Ranex digest-bound evidence or approval.
- Rejected: plain `git merge` <https://github.com/git/git> creates state but proves nothing about the digest ultimately published and leaves an independent ref-update race.
- Rejected: `--force-with-lease` <https://github.com/git/git> can infer its lease from remote-tracking state; that is weaker than the exact observed T and still proves no digest or approval freshness.
- Provenance: all six files were independently re-fetched from the cited URLs on 2026-08-05 and matched their vendored bytes exactly. The offline suite checks local hashes but cannot repeat network provenance.

## Considered Options

1. **Leave promotion manual.** Rejected: a human push is an unvalidated second publication path and cannot prove that published bytes equal judged bytes.
2. **CAS alone.** Rejected by measurement: `update-ref <ref> C T` accepts unrelated C; old-value equality is not ancestry.
3. **Merge/rebase onto a moved tip and reuse the verdict.** Rejected: the result is generally a new subject; re-materialise, re-judge and re-approve instead.
4. **Kernel-owned, fast-forward-only checked promotion with digest and signed approval binding.** Chosen.

**REFUTE panel (supervisor-run, 2026-08-05):** openai/gpt-5.6-terra and
google/gemini-3.6-flash reviewed through OpenRouter; the usual deepseek/hy3 pair,
kimi-k3, glm-5.2, qwen3.8-max, and grok-4.5 timed out, so the substitution is
recorded rather than hidden. Accepted: merge-commit smuggling, binding C and the
CANDIDATE row against pre-signing, equal-subject evidence reuse, inferred crash
recovery, and the unmoved-tip approval limit. Refuted: FF-only misses upstream semantic conflicts—base is exactly T, so
there is no drift—and stale-tip rollback replay, which requires an out-of-kernel
ref write in the operator's stated trust domain. Zuul speculation improves
pipeline throughput; it supplies no missing FF-only safety property here.

## Decision Outcome

In the context of a judged CANDIDATE awaiting publication, facing mutable refs
and immutable evidence bound to content, we chose **kernel-owned, fast-forward-only
promotion through `ranex task merge`**, to publish exactly the judged and approved
commit, accepting complete re-judgment whenever the target tip changes.

For candidate C, subject D, target R, and observed tip T, the kernel snapshots
both trees, CANDIDATE row, catalog and keyring, then verifies policy and approval.
The guarded publication checks in order: `git merge-base --is-ancestor T C`;
empty `git rev-list --merges T..C`; `subject_digest_for(C) == D` with satisfying
evidence; then, and only then, `git update-ref R C T`. The human supplies the
stamp out-of-band and never pushes; the harness can do neither.

The approval's dedicated domain binds C, D, R, T, catalog digest, and CANDIDATE
row hash. Because that row follows task intent, chain position proves intent
before judgment before approval; pre-signing has no row. Merge-attempt intent
records the stamp before publication. Keyring comes from T; approver differs from every producer; `evaluate()` is untouched.

### Consequences

- Good: a same-tree replacement commit dies because approval binds C and its parents/history identity, not D alone.
- Good: a merge commit in `T..C` cannot smuggle unreviewed second-parent history even when its final tree matches D.
- Good: every decision input except R is content-addressed and immutable; the whole TOCTOU surface collapses to one CAS.
- Good: ADR-010 sad paths 10 and 18 become explicit refusals at the merge boundary.
- Good: evidence bound to equal tree subject, catalog digest and command under ADR-005/ADR-007's pinned toolchain re-judges identically; reuse is journalled as reuse, never a fresh run.
- Good: several linear non-merge commits may exist above T; delegation emits one HEAD, not a one-commit range.
- Bad: approval is never reusable across tips, even if recomputation would produce the same tree.
- Bad: while R remains at T, approval never expires; revocation exists only by advancing the tip. This is accepted and not mitigated by a clock.
- Bad: there is no queue or train; under contention a slow candidate may starve.
- Limit: out-of-kernel ref writes and rollback are in the operator trust domain; the CAS detects only movement from observed T.

Merge-attempt intent `(task, C, D, T)` references the stamp, followed by checks, CAS, then an
outcome row. A crash after CAS but before outcome leaves an unmatched intent;
recovery inspects R and appends an `INFERRED` outcome, never inventing a direct
observation it did not make.

### Confirmation

The slice must prove the exact ordered checks and that no failing branch reaches
CAS. Red-first security cases: unrelated-history C (the measured reproduction),
a merge commit in `T..C`, approval signed before its CANDIDATE row, altered
catalog/keyring, same-tree/different-C substitution, forged signature, and a
target-tip race. Each must first demonstrate the unsafe baseline, then the new
refusal.

Integration must prove intent → checks → CAS → outcome, plus recovery of a
post-CAS crash as `INFERRED`. One scratch-repository e2e must publish a clean FF
through `ranex task merge`; direct human/harness publication is never part of
the fixture. `evaluate()`'s existing purity and no-self-approval tests remain
unchanged and green.

## Improvements on the prior art

1. **FF is checked separately from CAS.** Git's old-OID lock is concurrency control, not ancestry; the measured orphan update makes the distinction executable.
2. **No merge commits in the candidate range.** Prow checks the head and Gerrit checks the current patch set, but neither rule alone excludes an arbitrary second parent hidden behind an approved final tree.
3. **Commit and tree are both bound.** Evidence proves canonical tree D; the approval also names C, killing same-tree parent/history substitution.
4. **Judgment is in the approval.** Binding the CANDIDATE row hash makes a pre-signed stamp structurally unverifiable rather than merely too early by convention.
5. **Policy cannot judge its own mutation.** Catalog and keyring blob OIDs at C must equal the immutable T snapshot; changes need a separate future authorization path.
6. **Causal freshness only.** Unlike leases with timeouts, exactly T defines freshness; a moved tip invalidates approval without clocks or scheduler state.
7. **Evidence reuse is explicit and narrow.** Equal subject/catalog/command under the pinned toolchain may reuse evidence, but the journal says reuse and approval never crosses T.
8. **Recovery tells the epistemic truth.** An outcome reconstructed from the ref is `INFERRED`, not rewritten as an observation the crashed process never journalled.
9. **One mutable cell.** Commits, trees, blobs, signatures and journal rows are immutable; the target ref alone is mutable, so one CAS closes the race that bors-ng left open around mutable PR state without revalidation.

## Architecture surface

No new verdict path. `ranex task merge` is CLI composition around repository
object reads, existing evidence admission and pure `evaluate()`, approval
signature verification, the append-only journal, and one Git ref transaction.
The composition root supplies Git and journal adapters; the harness gains no
capability. Catalog/keyring are read by blob OID from C and T once and retained
for the decision; mutable paths are never re-read between validation and CAS.

The approval envelope is a new signed foundation value with an explicit domain
and closed field set. Intent/outcome rows extend journal event types without
rewriting any CANDIDATE. Recovery is a command-path concern, not a verdict.

## Scope and threat delta

In scope: one local task, one candidate, one target ref, one fast-forward CAS.
STRIDE narrows **Tampering** and **Elevation**: stale or substituted content,
self-authored policy, and non-ancestor publication refuse before the only write.
**Repudiation** narrows through intent/outcome chronology and inferred recovery.

Out: merge queues/trains—starvation is acceptable for one operator; semantic or metadata policy beyond binding C;
approver authentication (RISK-07); ref writers outside the kernel; and
submodule/LFS boundaries, which remain ADR-009's materialisation contract.
Policy changes need a separate explicitly-authorized future path.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Functional correctness | unrelated C supplied with expected T | ancestry check refuses; ref unchanged |
| Integrity | C has judged tree but different identity | approval verification refuses |
| Integrity | catalog or keyring differs between C and T | blob comparison refuses |
| Reliability | target moves between check and publish | CAS refuses exactly once |
| Accountability | crash follows successful CAS | unmatched intent recovered as `INFERRED` |
| Maintainability | verdict kernel reviewed after slice | `evaluate()` has no diff |

## Reversibility

Door: two-way

Remove `ranex task merge` and publication returns to being unavailable; no old
journal row or evidence format is rewritten. Approval envelopes and merge event
rows remain readable history. A rollback must not restore manual push as a
governed path. Changing FF-only later requires a superseding ADR because it
changes the subject that must be judged, not merely the Git command used.

## Sad paths

Derived by a decision table over object/ref/envelope state, plus crash-state transitions.

| # | Failure | Refusing check |
|---|---|---|
| 1 | target tip moves before CAS | `update-ref R C T` fails; stale-tip outcome, re-materialise |
| 2 | C is unrelated to T | `merge-base --is-ancestor T C` fails; measured regression |
| 3 | merge commit occurs in `T..C` | non-empty `rev-list --merges T..C` refuses |
| 4 | `C == T` or `tree(C) == tree(T)` | delegation already refuses; merge repeats the no-subject refusal |
| 5 | evidence names a digest other than D | evidence admission/evaluation refuses |
| 6 | envelope C differs | closed-field signature verification refuses |
| 7 | envelope D differs | closed-field signature verification refuses |
| 8 | envelope target ref differs | closed-field signature verification refuses |
| 9 | envelope T differs | closed-field signature verification refuses |
| 10 | envelope catalog digest differs | closed-field signature verification refuses |
| 11 | no matching CANDIDATE row, including pre-signed stamp | journal-row hash cannot resolve; refuses |
| 12 | envelope names a different CANDIDATE row hash | row lookup/binding refuses |
| 13 | signer absent from keyring blob at T | signature admission refuses |
| 14 | approver equals any evidence producer | existing no-self-approval rule refuses |
| 15 | catalog blob differs between C and T | immutable snapshot comparison refuses |
| 16 | keyring blob differs between C and T | immutable snapshot comparison refuses |
| 17 | crash after CAS before outcome | unmatched intent recovery inspects R; appends `INFERRED` |
| 18 | two merges race for one task | first CAS may win; second CAS refuses and journals refusal |
| 19 | two tasks race for one target | loser CAS refuses; re-materialise, re-judge, re-approve |
| 20 | target ref was deleted | snapshot/ref-resolution refuses; no recreation |
| 21 | C is missing or pruned | commit/tree resolution refuses before intent can publish |
| 22 | signature forged or any envelope field changed | domain-separated verification refuses |

## Test strategy

Levels: contract, security, integration, and one scratch-repository e2e. Tests
are frozen red-first before SLICE-010 implementation; no product code belongs in
this ADR task.

`tests/contract/test_docs_discipline.py` guards this ADR's structure, research,
licences, hashes, sad paths, and line budgets. It is run now to turn the two
research-only prior-art failures green.

`tests/security/test_git_backed_materialisation.py` is extended with the
measured unsafe control: `git update-ref` successfully publishes an unrelated
orphan when only T is supplied. New merge security cases then require refusal
for unrelated history, merge-commit smuggling, pre-signed approval, changed
catalog/keyring, same-tree/different-C, forged signatures, and CAS races. Each
case is first observed red against the unsafe composition, then green.

`tests/integration/test_journal.py` is extended for intent/check/CAS/outcome
ordering, one terminal outcome, competing same-task and different-task
attempts, and crash recovery that writes `INFERRED` only after inspecting R.
Existing `tests/unit/test_gate_verdict.py` continues to prove pure evaluation
and producer/approver separation; it must not change to know about merging.

`tests/e2e/test_first_delegation.py` supplies the existing CANDIDATE journey;
SLICE-010 extends a scratch-repository journey through one successful FF
`ranex task merge`, exact C/D/R/T/policy/journal approval binding, and final ref
identity. New filenames and exact test names belong to the slice. No global
coverage percentage: delta coverage on changed lines and every refusal branch.

## Code review checklist

- Are policy/approval preliminary refusals complete, then ancestry, merge range, digest/evidence, and CAS ordered exactly?
- Can any exit-status, missing object, or malformed signature fall through to publication?
- Are C and T resolved once, with catalog/keyring read from their immutable trees only?
- Does approval bind all six fields and the exact CANDIDATE row under a distinct domain?
- Is producer identity compared against the approver for every satisfying evidence record?
- Can evidence reuse be mistaken in the journal for a fresh execution?
- Is any clock, TTL, mutable PR object, remote-tracking ref, or model consulted?
- Does a CAS loss restart from materialisation rather than reuse approval?
- Can recovery distinguish direct observation from inference after a crash?
- Did any change touch `evaluate()` or give the harness/human a publication path?

## More Information

[ADR-002](./ADR-002-committed-trust-root.md) fixes the trust root at committed
paths; [ADR-005](./ADR-005-hermetic-observation.md) and
[ADR-007](./ADR-007-dependency-provisioning-for-gated-suites.md) pin observation
and toolchain; [ADR-009](./ADR-009-git-backed-materialisation.md) owns the
submodule/LFS subject boundary; [ADR-010](./ADR-010-first-delegation.md) creates
the CANDIDATE and defers the merge boundary completed here.

Freshness limit, plainly: an approval at an unmoved T is immortal, and only a
tip advance revokes it. Trust-domain limit, plainly: rollback or other writes by
an actor bypassing the kernel are operator compromise, not detected here. There
is no queue; a slow candidate may starve under contention.

Superseded ADRs: none. Open: separately authorized policy changes, authenticated
approver identity (RISK-07), and the SLICE-010 implementation.
