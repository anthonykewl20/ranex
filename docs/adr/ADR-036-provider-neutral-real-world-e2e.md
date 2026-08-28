# ADR-036 — provider-neutral real-world e2e portability

**Status:** proposed
**Date:** 2026-08-28
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-073-provider-neutral-real-world-e2e.md`

## Context and Problem Statement

The kernel's prototype `task delegate` path names `OPENROUTER_API_KEY`, refuses
without it, and copies it into the harness child. That makes kernel correctness
depend on one provider and prevents the same executable boundary from being
driven by Claude, Codex, opencode, a desktop host, or a deterministic test
adapter. The canonical real-e2e run also exposed two ambient-host assumptions:
suite freeze consumes the operator checkout's mutable dependency journal, and
the historical approved-batch fixture tries to qualify host bytes captured on
another machine. A nested fanout control failed once under the sealed full run
but passed ten focused repetitions.

Real-e2e must execute real committed code and independently observe repository
state. It must not mistake provider availability, an old host fingerprint, or
mutable operator state for kernel accuracy.

## Decision Drivers

- Kernel code and admission contain no provider or provider-credential name.
- The harness executable is an opaque adapter; `model` is opaque adapter input.
- Signing/verdict keys remain forbidden at the harness execution boundary.
- No ambient API key crosses into the harness environment.
- Real-e2e subjects and patches are existing pinned Git commits, not toy apps.
- Host-specific qualification proves success only on a matching host and
  proves fail-closed refusal elsewhere.
- Real freeze creates its own disposable derivation/approval state.
- Absence never becomes PASS and frozen behavior tests are not weakened.

## Prior art

- Searched: GitHub code search for provider-neutral executable hooks, external
  command adapters, real-repository patch grading, pinned task instances, and
  host capability requirements; installed git, pytest, uv, and the current
  Ranex CLI were exercised against the retained failure evidence.
- https://github.com/pre-commit/pre-commit/blob/b74a22d96cca546b8e0bb9f68f1d7d8565205b65/pre_commit/languages/system.py delegates a hook to the common command runner without encoding the tool behind that executable.
  License: MIT.
  Weakness: pre-commit intentionally inherits a developer execution context and does not provide Ranex's signing-key exclusion, subject binding, or emitted-commit validation.
  Vendored: `docs/adr/prior-art/ADR-036/pre-commit-system.py` blob:f6ad688fad185b06ef05765aa5d7aaa20e359784
- https://github.com/SWE-bench/SWE-bench/blob/7a21e05772954cc81471ae19d56f436cecf43c54/swebench/harness/grading.py grades patches from real repositories by independently classifying test outcomes rather than trusting a model report.
  License: MIT.
  Weakness: SWE-bench measures issue resolution inside prepared environments; it does not bind evidence, approvals, capabilities, journal order, or publication authority.
  Vendored: `docs/adr/prior-art/ADR-036/swebench-grading.py` blob:39174d64aef5c3cc211b27124af5966349d1aa8c
- Rejected: https://github.com/langchain-ai/langchain/tree/master/libs/partners — placing provider SDK selection in the kernel would recreate the forbidden provider matrix and credential coupling instead of defining an executable boundary.
- Rejected: https://github.com/SWE-agent/SWE-agent/tree/main/sweagent/agent — embedding one agent loop would test that loop rather than Ranex and would exclude desktop or already-running outer agents that only need dispatch, emission, and judgement.

## Considered Options

1. Keep OpenRouter as the required default and add optional providers. Rejected:
   the kernel remains a credential router and every new runtime changes policy.
2. Detect Claude/Codex/opencode and construct their CLI flags. Rejected: desktop
   hosts are not child CLIs, flags drift, and detection is provider policy.
3. Forward every ambient credential and HOME. Rejected: it leaks unrelated
   authority into the worktree and breaks the existing signing-key boundary.
4. Treat the executable harness as the adapter, pass only bridge variables and
   opaque adapter arguments, and judge its emitted repository state. Chosen.

## Decision Outcome

`task delegate` defines, requires, and forwards no model credential. Its child
environment contains only pinned `PATH`, scratch `HOME`, `RANEX_TASK_ID`, and
`RANEX_EMIT`; existing signing-credential refusals remain unchanged.
`--harness` is the adapter boundary; `--model` is opaque adapter input. Ranex
does not parse providers, credentials, or promise that every host
uses it. Desktop/app agents may operate between dispatch and judge; authentication
belongs to an adapter-side broker or authenticated outer process.
Real provider e2e becomes a deterministic
adapter applying pinned Ranex commit `cebc06a33ba1f28fd21815bb21edbdc768b4a669`
to its real parent: focused tests are red before and green after, then the kernel
independently reads the diff, suite result, candidate, and journal. Freeze e2e
uses a disposable real clone with its own derived/test-approved dependency state.
Historical batch authority stays immutable: matching hosts qualify; foreign hosts
prove exact build-input refusal and no publication. Fanout assertions stay intact.

### Consequences

- Good: kernel verdict behavior is identical across provider and app hosts.
- Good: credentials unknown to Ranex cannot accidentally cross the boundary.
- Good: real-e2e uses real repository history and independently observed tests.
- Good: historical host authority remains immutable and fails closed elsewhere.
- Bad: `task delegate` does not itself authenticate a provider; adapters needing
  credentials require an external broker or authenticated outer process.
- Bad: deterministic adapter e2e proves integration, not model problem-solving.

### Confirmation

Focused tests prove no provider constant exists, no API-key-shaped ambient value
crosses the environment, delegation reaches an executable adapter without any
model credential, and signing keys still refuse. Real-e2e proves a pinned real
commit is red-then-green through the emitted worktree. Freeze proves disposable
derivation/approval; historical qualification proves either exact success or
exact refusal. The canonical entrypoint and skip ledger remain the final gate.

## Improvements on the prior art

1. Add signing-key exclusion and exact emitted-worktree/commit validation to
   pre-commit's provider-blind executable pattern.
2. Add evidence, journal, approval, and absence-blocking semantics around
   SWE-bench's independent real-repository outcome model.
3. Separate adapter integration accuracy from model issue-resolution accuracy.

## Architecture surface

`src/ranex/cli/delegation.py` owns the provider-neutral child environment and
opaque executable invocation. Parser flags and emitted JSONL remain unchanged.
The affected unit/integration/security tests freeze credential absence and
bridge behavior. Real task, freeze, qualification, manifest, README, and state
surfaces change only enough to remove ambient-provider and ambient-host claims.

## Scope and threat delta

The harness loses direct access to one previously injected model credential and
gains no replacement secret, HOME, network, signing key, or verdict key. The
adapter remains arbitrary executable code already authorized by `--harness`.
This slice does not implement a broker, model router, desktop plugin, provider
SDK, harness mutation authority, or claim that deterministic adapters solve
unseen issues.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Portability | provider variables absent or renamed | same kernel outcome |
| Security | ambient API/signing keys present | API keys dropped; signing keys refuse |
| Reality | adapter integration journey | pinned real commit and real tests |
| Determinism | same adapter/subject repeated | identical diff and verdict class |
| Honesty | historical host bytes differ | exact refusal, no qualified claim |

## Reversibility

Door: two-way

The removed credential injection can be restored only by a later approved
credential-broker contract. Real-subject pins can move through a new slice;
published historical authority bytes are never rewritten.

## Sad paths

- Ambient signing or verdict key exists → refuse before dispatch or adapter.
- Ambient provider keys exist → drop all; none appear in the child environment.
- Adapter requires an unavailable provider session → adapter fails; no emission
  and no candidate, never a kernel PASS.
- Harness path is absent, non-file, non-executable, or replaced → existing refusal.
- Adapter emits no/malformed/multiple-authority JSON, wrong task/worktree/commit,
  base commit, empty tree, or unreadable worktree → existing refusal.
- Adapter times out or leaves descendants → process-group kill and timeout outcome.
- Pinned real patch is unavailable, already applied, empty, or its real suite
  is not red-then-green → e2e fails, never substitutes generated code.
- Disposable dependency derivation differs from committed lock → freeze refuses.
- Test approval is absent or for another depset → disposable freeze refuses.
- Historical build bytes differ → exact build-input refusal with no artifact.
- Matching host qualification writes residue or permits publication → e2e fails.
- Fanout exceeds the pool, ticks queued timeout, emits empty commits, or corrupts
  journal order → focused stress test fails.
- Observed skip is undeclared or a hard reason drifts → entrypoint exits nonzero.

## Test strategy

`tests/unit/test_delegation.py` and
`tests/integration/test_delegation_command.py` freeze the credential-free adapter
environment and all existing signing/emission/timeout refusals.
`tests/e2e/test_delegation_real.py` and
`tests/e2e/test_first_delegation.py` exercise a pinned real repository commit.
`tests/e2e/test_suite_freeze_real.py` owns disposable real-subject provisioning.
`tests/e2e/test_specification_batch_qualification.py` owns matching-host success
and foreign-host exact refusal. The existing fanout security test runs repeated
under load; `tests/contract/test_docs_discipline.py` freezes lifecycle shape.

## Code review checklist

- Verify no provider or provider-credential name remains in kernel admission.
- Verify the child environment is exact and signing-key refusals are unchanged.
- Verify the real patch and base are 40-hex pins already present in Git history.
- Verify foreign-host behavior asserts refusal and absence, not a skip-as-pass.
- Verify freeze state is disposable and no operator approval is fabricated.
- Verify no test timeout, security assertion, or manifest check is weakened.

## More Information

Issue #52 carries the baseline transcript, focused 10/10 fanout rerun, and final
proof. ADR-032 remains the real-e2e frame; this ADR supersedes only its
OpenRouter-specific prerequisite and ambient-host assumptions.
