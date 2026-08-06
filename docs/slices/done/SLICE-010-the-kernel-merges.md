# SLICE-010 — the kernel merges

**Status:** done
**Opened:** 2026-08-06
**Parked:** 2026-08-06 — archived without implementation when the owner
redirected to the ADR-015 durability program (SLICE-011).
**Closed:** 2026-08-06 — re-opened and finished by the owner's direction. All
fourteen done criteria are proven by passing tests: the unsafe `update-ref`
control is reproduced before it is refused; the closed approval envelope is
bound to C, D, R, T, catalog digest, and CANDIDATE row hash with a real
domain-separated signature; ancestry, merge-range, digest/evidence, and CAS
each refuse red-first against the measured baseline; races journal exactly one
winner; crash recovery infers only after inspecting R; the clean fast-forward
e2e journey is entered in `governance/suite_manifest.json` as a NON-skip.
Verification actually run: full suite 827 passed / 2 skipped; `diff-cover`
100% on the change; `mutmut` kernel-scope run completed (1936 killed, 82
timeout, 559 survived — survivors are review input per policy; the new
`approval.py` survivors are error-text and redundant-length-check mutants).
One harness-side blocker was closed outside this tree: the sibling
`ranex-harness` typecheck failure in `test/plugin/trigger.test.ts` was fixed
and committed there as `f7f822ff5e`.
**ADR:** `docs/adr/ADR-012-the-kernel-merges.md` — accepted 2026-08-05.
**Closes:** ADR-012's confirmation, ADR-010's deferred sad paths 10 and 18,
and the publication boundary. The kernel, not a human or harness, becomes the
only governed publication path.

## The defect

ADR-010 leaves a kernel-journalled CANDIDATE whose evidence is digest-bound, but
promotion is manual and unvalidated. The measured unsafe control is concrete:
in a scratch repository, `git update-ref refs/heads/main <C> <T>` moved `main`
from T to a completely unrelated orphan C. The old-value argument proves only
value equality. It does not prove ancestry, that C was judged, or that approval
is current.

## Design

Per `docs/adr/ADR-012-the-kernel-merges.md`:

1. `ranex task merge` takes candidate C, subject D, target ref R, and observed
   tip T. It snapshots both trees, the CANDIDATE row, catalog, and keyring.
   Catalog and keyring are read by blob OID from C and T once and retained for
   the decision; mutable paths are never re-read between validation and CAS.
2. It verifies policy and approval before publication. Catalog and keyring blob
   OIDs at C and T must be equal. The approval envelope's domain-separated
   signature must bind C, D, R, T, the catalog digest, and the exact CANDIDATE
   row hash. The signer must be in the keyring at T, and the approver must differ
   from every evidence producer.
3. It runs `git merge-base --is-ancestor T C`.
4. It requires an empty `git rev-list --merges T..C`, so a merge commit cannot
   smuggle unreviewed second-parent history.
5. It requires `subject_digest_for(C) == D` with satisfying evidence.
6. Only after every preceding check succeeds does it run `git update-ref R C T`.
   The human supplies the stamp out-of-band and never pushes; the harness can
   do neither.
7. Merge-attempt intent `(task, C, D, T)` records the stamp before the checks
   run, spanning the checks, CAS, and outcome row. If a crash follows
   successful CAS but precedes the outcome, recovery inspects R and appends
   `INFERRED`. Recovery never invents a direct observation it did not make.

## Done criteria

Each criterion is met only when a test proves it. New coverage belongs in
`tests/security/test_slice010_the_kernel_merges.py`; the named existing files
extend where stated.

1. **The unsafe publication is measured before it is refused.**
   `tests/security/test_git_backed_materialisation.py` reproduces the measured
   `update-ref refs/heads/main <C> <T>` control moving main to an unrelated
   orphan when only T is supplied. The new composition then refuses missing or
   pruned C, a deleted target, C equal to T, or tree(C) equal to tree(T), before
   publication. (ADR-012 s.p. 4, 20, 21)
2. **The immutable policy and approval snapshot is closed.** The security tests
   refuse a pre-signed approval with no matching CANDIDATE row, a different row
   hash, any changed C, D, R, or T, changed catalog or keyring blobs, a signer
   absent from T's keyring, a forged or otherwise changed signature, and an
   approver who produced satisfying evidence. Each refusal is first observed
   red against the unsafe composition, then green. (ADR-012 s.p. 6, 7, 8, 9,
   10, 11, 12, 13, 14, 15, 16, 22)
3. **An unrelated candidate cannot reach CAS.** The real Git-backed security
   test refuses when T is not an ancestor of C, and leaves R unchanged. The
   test runs `git merge-base --is-ancestor T C`; it does not substitute a source
   inspection or a prose assertion. The refusal is red first against the unsafe
   composition and green after the kernel check. (ADR-012 s.p. 2)
4. **Merge-commit smuggling is refused.** A candidate containing a merge commit
   in `T..C` is rejected by the real `git rev-list --merges T..C` check even when
   its final tree matches the judged subject. The refusal is red first and green
   second. (ADR-012 s.p. 3)
5. **The published commit is exactly the judged subject.** The security tests
   refuse evidence naming a digest other than D, and refuse a same-tree,
   different-C substitution through the closed approval binding. No failing
   digest or evidence branch reaches CAS. Each refusal is observed red first
   against the unsafe composition, then green after the kernel check. (ADR-012
   s.p. 5, 6)
6. **The target race and competing tasks are atomic and journalled.**
   `tests/integration/test_journal.py` and the slice security tests prove that
   a target-tip race makes `update-ref R C T` refuse exactly once, that competing
   same-task attempts and different-task attempts produce at most one winner;
   every loser refuses and is journalled, and no loser reuses approval. Each
   refusal is observed red first against the unsafe composition, then green after
   the kernel check. (ADR-012 s.p. 1, 18, 19)
7. **The journal tells the truth across publication and crash recovery.**
   `tests/integration/test_journal.py` proves intent -> checks -> CAS -> outcome,
   exactly one terminal outcome, and a crash after successful CAS but before the
   outcome row leaving an unmatched intent. Recovery inspects R and appends an
   `INFERRED` outcome only after inspecting R; it never records a direct
   observation it did not make. The journal stays append-only across a merge and
   across recovery: no CANDIDATE row is rewritten, and `ranex journal verify`
   stays green. (ADR-012 s.p. 17)
8. **One clean fast-forward publishes through the kernel.**
   A pure scratch-repository fixture runs one successful `ranex task merge`,
   asserting exact C/D/R/T, policy, journal approval binding, and final ref
   identity. The pure fixture does not request the gated model-credential,
   harness-fork, or bun fixtures; the merge fast-forward needs no model. It is
   entered in
   `governance/suite_manifest.json` as a NON-skip, and direct human or harness
   publication is never part of the fixture. (ADR-012 Confirmation / Test
   strategy)
9. **The verdict kernel remains untouched.**
   `tests/contract/test_kernel_unchanged.py` requires `KERNEL_DIGEST` to remain
   unchanged, the byte-exact kernel guard. `tests/unit/test_gate_verdict.py`
   remains unchanged and continues to prove pure `evaluate()` and
   producer/approver separation; it gains no merge knowledge. The change gives
   the harness and the human no publication path. (ADR-012 Quality attributes:
   Maintainability; Architecture surface; Code review checklist, last item)
10. **Every refusal added by this slice is reached by a test, `diff-cover` stays
     100% on the change, and the full suite stays green.** This includes every
     refusal branch above and the red-first unsafe-baseline proofs required by
     each security criterion above.
11. **A linear multi-commit range publishes.** A candidate C that is several
    linear non-merge commits above T publishes successfully through `ranex task
    merge`; an implementation requiring `parent(C) == T` is forbidden. (ADR-012
    Consequences: Good: several linear non-merge commits may exist above T;
    delegation emits one HEAD, not a one-commit range)
12. **Refusal order is observable.** A candidate failing several checks at once
    refuses at the first check in ADR order: policy/approval, ancestry,
    merge-range, digest/evidence, then CAS. Journalled check rows prove the
    order; an unrelated-history C that also has a forged envelope refuses at
    policy/approval, not ancestry. (ADR-012 Confirmation; Code review checklist,
    first item)
13. **Evidence reuse is journalled as reuse.** Evidence reused under equal
    subject/catalog/command, under ADR-005/ADR-007's pinned toolchain, is
    journalled as reuse and is distinguishable from a fresh execution. (ADR-012
    Improvement 7; Code review checklist, evidence reuse question)
14. **Validation reads are not repeated before CAS.** Mutating the on-disk
    catalog, keyring, or working tree after validation but before CAS changes
    neither the decision nor the published commit: catalog/keyring are read by
    blob OID from C and T once and retained, and mutable paths are never re-read
    between validation and CAS. (ADR-012 Architecture surface; Consequences:
    Good: the whole TOCTOU surface collapses to one CAS)

## The controls most likely to become decoration

1. **First: a refusal test that reads source instead of running Git.** The
   ancestry, merge-range, and CAS cases must execute the real commands in a
   scratch repository. A test that inspects command construction or asserts a
   helper's return value can pass while `update-ref` still publishes an orphan.
2. **Second: the unsafe-control baseline measured by reading prose instead of
   reproduced.** The security test must actually create unrelated T and C and
   observe the old composition move R before it asserts that the new path refuses.
3. **Third: approval binding tested with a stub signature.** The test must verify
   a real domain-separated signature against the exact six closed fields and
   CANDIDATE row, including changed catalog/keyring and pre-signing cases. A
   stub returning true proves no binding.
4. **Fourth: INFERRED recovery asserted without an actual post-CAS crash.** The
   integration test must leave intent unmatched after successful CAS, inspect R
   during recovery, and distinguish that inference from a directly observed
   outcome. A fabricated recovery row proves nothing.

## What this slice does not close

- **Approver authentication (RISK-07).** The signer must be in the keyring, but
  authenticating the approver remains open.
- **Artifact forgery.** Merge-time re-check does not close it: re-judgment
  consults the same producible artifact path; verifiable separation remains for
  a later slice.
- **Policy changes.** Catalog/keyring mutation between C and T is refused;
  changing policy needs a separate explicitly-authorized path and is not part of
  this slice. (ADR-012 Scope Out / More Information)
- **Submodule/LFS subject boundaries.** These remain ADR-009's materialisation
  contract and are out of scope here. (ADR-012 Scope Out)
- **Merge queue or train.** There is no queue; contention can starve a slow
  candidate.
- **Ref writers outside the kernel.** Rollback and other out-of-kernel writes
  remain in the operator trust domain and are not detected here.
- **The immortal-approval-until-tip-advances limit.** Approval does not expire
  while R remains at T; only advancing the tip revokes it. No clock is added.
- **MAP §4.6's remaining controls.** Entry-point observed spawning, distinct
  claims, and assertion strength remain open.
