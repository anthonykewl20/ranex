# ADR-014 — one process, many tasks: the bridge becomes a per-member protocol

**Status:** proposed
**Date:** 2026-08-06
**Decision-makers:** repo owner
**Slice:** n/a — precedes the harness slices; SLICE-010 is closed

## Context and Problem Statement

The harness bridge is one-task-one-process. `delegation.py` spawns one harness per task with a single `RANEX_TASK_ID` and one `RANEX_EMIT` file (`src/ranex/cli/delegation.py:26-73`); the fork's bridge plugin commits once on the first idle session then latches `emitted = true` (`packages/ranex/src/plugin/ranex.ts:8-33`). The owner-approved background worktree agent manager runs N agents in one harness process, each in its own worktree. The bridge as written cannot express that: the first idle member swallows the rest, and no member identity exists to cross-check. The kernel's emission cross-check is the trust boundary; it must hold per member.

## Decision Drivers

- One git worktree per task is a decided invariant; the manager keeps it per member.
- The wall stands: hooks collect, the kernel judges; the harness never writes the journal.
- A member must not be able to emit for another member.
- Evidence binds to a subject digest; with N worktrees the digest is per member.
- The bridge change must not delay or disturb the in-flight SLICE-010.
- The owner records the manager as outside ADR-013's gate; the credential scale-up is RISK-06, standing.

## Prior art

Searched: GitHub code search for "agent worktree orchestrator", "durable execution heartbeat lease", and "job queue visibility timeout stalled job recovery", via `gh api` search/repositories and repository clones.

- **DBOS** (dbos-inc/dbos-transact), commit `dfd600cc48537a69f3d57d28108a781bfb82c988`, `src/system_database.ts`, durable workflow rows fenced by `executor_id`; startup recovery re-enqueues rows left PENDING under a dead executor, matching `application_version`; recovery attempts are counted: <https://github.com/dbos-inc/dbos-transact/blob/dfd600cc48537a69f3d57d28108a781bfb82c988/src/system_database.ts>
  License: MIT.
  Weakness: it fences by executor identity, not wall-clock lease; a stale executor can keep running and its completion is rejected, but its external side effects already happened — at-least-once unless the side effect is idempotent.
  Vendored: docs/adr/prior-art/ADR-014/dbos-system-database.ts blob:a52e272e14bab5d2694d3556842349e70c456501
- **OpenAI Codex** (openai/codex), commit `1151b23f01accb19e55c090a3349a32fdf2b4685`, `codex-rs/agent-graph-store/src/local.rs`, SQLite-backed agent graph store persisting `thread_spawn_edge` rows (parent/child thread ids, status), restoring agent identities from durable history on resume: <https://github.com/openai/codex/blob/1151b23f01accb19e55c090a3349a32fdf2b4685/codex-rs/agent-graph-store/src/local.rs>
  License: Apache-2.0.
  Weakness: agents are in-process threads, not worktrees or branches; the live runtime registry stays in-memory, so resume restores history, never a live process; there is no branch or merge model.
  Vendored: docs/adr/prior-art/ADR-014/codex-agent-graph-store-local.rs blob:a7c1fd4a3395e9070f65cf7cbeff45f402c0f255
- **aider** (Aider-AI/aider), commit `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`, `aider/repo.py`, commits every edit, commits pre-existing dirty changes first, and confines undo to the last aider commit under strict guards (no pushed commits, no merge commits, no dirty affected files): <https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/repo.py>
  License: Apache-2.0.
  Weakness: it operates in the user's live checkout with no worktree isolation for concurrent agents; commit hooks can be skipped; a dirty tree is committed under a generic message, so the commit boundary is not evidence-grade.
  Vendored: docs/adr/prior-art/ADR-014/aider-repo.py blob:92b5e3bf5b81ec1bcee62feaf64c9c09fc607f54
- Rejected: https://github.com/oh-my-openagent/oh-my-openagent — the architectural ancestor of the N-agent manager, but its code is SUL-1.0 and this tree excludes it forever, converted or not; behavioural reference only, never vendored.
- Rejected: https://github.com/celery/celery — worker-local reserved/active state with no durable ownership of a work item; two workers resurrected after a partition both run without fencing, which is the exact failure this protocol must refuse.

## Considered Options

1. Ship the manager on the existing bridge, one process per member. Rejected: N processes cannot share the durable run state machine the feature exists to keep.
2. Extend the bridge to a per-member protocol. Chosen.
3. Replace the bridge with a message broker. Rejected: a broker is a new dependency and a new trust boundary, and the hermetic suite runs with no network.
4. Let the harness write the journal directly. Rejected: this is the wall; ADR-008 exists because of it.

## Decision Outcome

In the context of N agents in one governed process, facing a one-task bridge that cannot express it, we chose a per-member emit protocol, to keep every kernel cross-check true per member, accepting a breaking change to the bridge contract. Concretely: delegation registers members with `(task_id, member_id, worktree, base_commit)`; the fork's bridge emits one line per member binding `task_id`, `member_id`, `worktree`, `commit` and `tree`; the process latch becomes per-member; the kernel cross-checks each emission against its own dispatch record and the emitted tree digest. The commit boundary is per member: the bridge commits the member's work in that member's worktree before emitting, and the emitted tree is the judged tree.

### Consequences

- Good: per-member evidence replaces first-member-wins; member A cannot emit for member B.
- Good: one-worktree-per-task survives; SLICE-010 is untouched.
- Good: the emit record keeps the shape the kernel already validates, one field richer.
- Bad: the bridge contract breaks; fork and kernel must land together or the suite goes red.
- Bad: the supervisor, leases, orchestrator and UI are not decided here.
- Not closed: merge contention across members, RISK-06, the durable whiteboard.

### Confirmation

The contract suite guards this ADR's structure, licences and digests. `tests/unit/test_delegation.py` extends with per-member emission refusals; `tests/integration/test_fork_startup_bridge.py` drives the fork with N members and asserts N independent emissions; `tests/security/test_refusal_coverage.py` keeps every refusal reachable. New filenames and exact test names belong to the slice. The bridge integration test skips without bun and the trimmed harness; under ADR-011 a skip is absence, disclosed here.

## Improvements on the prior art

1. DBOS fences by executor identity; this protocol adds a member identity and a per-member emit line, so the fence is per work item, not per process.
2. Codex resumes from durable history but has no branch; this keeps one worktree and one branch per member, so diff and merge have a ref to bind to.
3. aider commits in the live checkout; this commits in the member's worktree and emits the tree digest, so the judged subject is the committed tree.
4. The per-member latch replaces the process latch, so N members cannot race a single emission.
5. The no-self-approval cross-check is preserved per member rather than per process.

## Architecture surface

Port: the delegation bridge. Files: `src/ranex/cli/delegation.py` (`execute_environment`, `_read_emission`) and the fork's `packages/ranex/src/plugin/ranex.ts` bridge plugin. Emission schema gains `member_id` and `tree`. No verdict, journal, or `evaluate()` change.

## Scope and threat delta

Governs the bridge contract only. STRIDE: Spoofing (member_id binding refuses one member emitting for another); Tampering (emitted tree cross-checked against the dispatch worktree). Non-goals: the supervisor, orchestration, verification semantics, UI. Out of scope: an attacker holding the model credential — that is RISK-06, standing, mitigated by scoped spend-limited keys.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Integrity | member A emits member B's id | kernel refuses before materialisation |
| Functional correctness | N members idle in one process | N validated emissions, no latch loss |
| Security | an emission names a foreign worktree | refuse; worktree must equal the dispatch record |
| Maintainability | a member field is added | one schema, both sides updated together |

## Reversibility

Door: two-way

The bridge contract is internal and lands on both sides in one change; reverting both repositories restores the old shape. No migrated data: the emission file is transient, per run.

## Sad paths

| # | Failure | Required behaviour |
|---|---|---|
| 1 | Two members idle simultaneously | both emit; each validated independently |
| 2 | Member A emits with member B's identity | refuse: member_id must match the emitting session |
| 3 | Emitted worktree differs from the dispatch record | refuse before materialisation |
| 4 | Emitted commit equals the member's base commit | refuse: no subject to judge |
| 5 | Emitted tree equals the base tree | refuse: no subject to judge |
| 6 | Crash after commit, before emit | absence blocks; reconcile marks interrupted |
| 7 | The same member emits twice | refuse the second: one dispatch, one judgement per member |
| 8 | A stale emission from an earlier run id | refuse: task_id and member_id must both match |
| 9 | Git user identity unset in the worktree | bridge surfaces the failure; never emits a false commit |
| 10 | A commit hook rewrites files | emitted tree is post-hook; the judged tree is the emitted tree |
| 11 | N members share one emit file | append-only lines keyed by member_id; no cross-member interference |
| 12 | The suite runs against a moved HEAD | materialisation binds the emitted commit; mismatch refuses |
| 13 | The old process latch is retained | test forces N sessions to idle and asserts N emissions |
| 14 | A reviewer re-opens the ADR-013 gate | the exemption is recorded in More Information and the checklist |

## Test strategy

Levels: unit, integration, security, contract. `tests/contract/test_docs_discipline.py` guards this ADR's form, prior art, licences and vendored digests. `tests/unit/test_delegation.py` extends with the refusal cases as a decision table over the emission parser (sad paths 1-8, 12). `tests/integration/test_fork_startup_bridge.py` extends to drive the fork with two members and assert two emissions with distinct member ids; it skips without bun and the trimmed harness, a disclosed skip-is-absence. `tests/integration/test_delegation_command.py` covers the CLI surface for the new member argument. `tests/security/test_refusal_coverage.py` keeps every refusal reachable. Each case is first observed red against the current one-task bridge, then green. No global coverage percentage; delta coverage on changed lines and every refusal branch.

## Code review checklist

- Does the decision answer the Context and not restate a decided line?
- Is each citation traceable to its pinned URL and its weakness honestly named?
- Does the emission schema change break the kernel's existing cross-checks?
- Can any member emit a line another member produced? A no must be a refusal, not a convention.
- Is the commit boundary explicit: who commits, when, and what tree is judged?
- Do the frozen tests assert behaviour (two members, two emissions) rather than internal shape?
- Is the ADR-013 exemption carried in the record, not just in chat?

## More Information

Parent decisions: ADR-008 (the bridge), ADR-009 (materialisation), ADR-010 (delegation). Related: SLICE-010 (kernel merges); ADR-013 (prototype gate — the owner records the manager as outside it on 2026-08-06). Tracked in GitHub milestone #2 "Background worktree agent manager" on this repository; slice issues #1-#9 of that milestone carry the plan. SLICE-011/012/013/014/017 are gated by this ADR's bridge contract; SLICE-015/016/018/019 are downstream harness slices that depend on those. The harness fork is upstream code and is never written to. The harness-side mechanics (worktree creation, durable schema, leases, verification, orchestrator, UI) are separate harness decisions, not this ADR.