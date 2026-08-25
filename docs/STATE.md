# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-25 (SLICE-036 CCR v4 finalizer pre-OCR)
**Active slice:** `docs/slices/SLICE-036-approved-batch-qualification.md`
## Where we stopped
Milestone 4 is closed with partial delivery, not full-program completion.
Retained kernel/framework work: #34–#38 (SLICE-054–058). #39/SLICE-059
task-family proof and #43/SLICE-069 broker qualification are withdrawn, not
completed release gates. Harness development stopped; Ranex makes no claim of
full governed production-agent execution, real-provider task proof, or
production mutation fanout. The kernel code at origin/main remains the source
of truth for the initial release.
## Next
Framework closed: SLICE-055 closed 2026-08-19
Only planned delivery: #19 / SLICE-036, approved-batch qualification and
kernel continuity in disposable strict-local worktrees with publication
blocked. Its signed schema/descriptor/children, distinct protected oracle
artifacts, B-bound public-CLI negative controls, and one-repository/ref
qualification-through-publication-refusal proof are frozen RED for external
review. Staged development source remains outside the governed checkout and is
bound in the transcript by an independently recomputed manifest digest and
exact imported module path. The actual canonical qualification outcome is
evidence-v4-signed, bound to its exact `batch-qualified` journal row, and
refused by additive batch-aware judge/merge before any legacy publication
write. Implementation remains unauthorized until external review approves CCR
v4, the specification owner accepts it, and `status:ready` is applied.
No harness, broker, task-family proof, or production-exit slice gates it.
## Governance (owner, 2026-08-25)
Current release: kernel-only initial release; one open slice and one mutation
writer. The prior build order remains historical provenance only:
Build order: milestone 4 → milestone 3 → milestone 2
## Known limits
- The strict-local controller remains same-UID trusted infrastructure; hosted
  confinement may lack user namespaces or delegated cgroup controllers.
- The approver is an unauthenticated string; the journal does not detect a
  removed, internally consistent prefix; `evidence.json` is not append-only.
- About 125 legacy test IDs remain unregistered; trace fd targets retain
  O_NONBLOCK on the operator descriptor after exit (disclosed).
- `mutmut` statistics remain unavailable for subprocess-heavy surfaces; the
  default-deny clone and writable-tree EXECUTE residuals remain review-owned.
- Concurrent sessions in one delegated scope serialize; availability and
  teardown crash residuals remain documented kernel limits.
