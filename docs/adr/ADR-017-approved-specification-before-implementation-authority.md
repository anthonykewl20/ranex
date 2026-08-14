# ADR-017 — approved specification before implementation authority

**Status:** accepted
**Accepted:** 2026-08-15 — confinement prerequisite closed (ADR-006 accepted, RISK-06 closed via SLICE-046); SLICE-029 may open. Accepted without broadening.
**Date:** 2026-08-09
**Decision-makers:** repo owner
**Slice:** `n/a — program decision; SLICE-017 is active; SLICE-018/019 and SLICE-029..044 are planned sequentially`

## Context and Problem Statement

Ranex can dispatch a prose prompt, but neither kernel nor harness can prove what
the human approved, which outcome is intended, or which tools the worker may use.
Source and runtime observation reveal what exists; they cannot turn a defect into
business intent. ADR-006 confines a bound command, but does not decide when a
command earns authority or what its arguments mean. The missing P0 capability is
a human-approved, machine-readable target that deterministically governs every
implementation action, generated test, verification claim, and merge.

## Decision Drivers

- Resolve blocking questions, observable outcomes, and non-goals before BUILD.
- Give the kernel a deterministic grant, not a prompt or model-selected mode.
- Bind intent, generated checks, policy, execution, evidence, and merge end to end.
- Let parallel agents work only inside intersected, least-authority child grants.
- Keep enforcement common across every harness tool and direct side-effect seam.
- Make a changed normative specification revoke outstanding implementation power.
- Distinguish acceptance oracles from observed characterization.
- Close only on real installed CLI-to-application evidence, not mock-only proof.

## Prior art

Searched: GitHub code and repository searches for specification gates, artifact
graphs, state machines, durable workflows, agent task envelopes, traceability,
code-edit protocols, and test-generation pipelines; immutable commits and root
licences were checked before copying.

- [Spec Kit workflow](https://github.com/github/spec-kit/blob/684b3d8e05263a7c1948d3d0699ab1cb4f77c3d5/workflows/speckit/workflow.yml)
  demonstrates explicit specify/review/plan/review/task/implement gates.
  License: MIT.
  Weakness: approval gates govern workflow progress, not OS-level mutation or a
  digest-bound capability enforced at every tool path.
  Vendored: `docs/adr/prior-art/ADR-017/spec-kit-workflow.yml` blob:230675b327758783e20740430e40ba70e059b7f5
- [OpenSpec artifact state](https://github.com/Fission-AI/OpenSpec/blob/e50bd0983dc8dc48250e3181f36e28450542f2ab/src/core/artifact-graph/state.ts)
  demonstrates deterministic completion derived from declared outputs.
  License: MIT.
  Weakness: file existence is not provenance, semantic correctness, authorization,
  or proof that an output was produced by the approved task.
  Vendored: `docs/adr/prior-art/ADR-017/openspec-artifact-state.ts` blob:47c256ac91844b6ac7f037c703288fc2ab9eecb4
- [XState adjacency traversal](https://github.com/statelyai/xstate/blob/c25dba07a2b68565edbe83d83c5d679dd85e00b2/packages/core/src/graph/adjacency.ts)
  demonstrates bounded, serialized state/event graph traversal.
  License: MIT.
  Weakness: traversal discovers reachability; it neither supplies business intent nor authorization.
  Vendored: `docs/adr/prior-art/ADR-017/xstate-adjacency.ts` blob:fc9f4b077dfbc7bcdcf0a2e5d077bf3109616b82
- [Arxic evidence refs](https://github.com/anthonykewl20/arxic/blob/135991d9b1a07c2ffa08e38f8e261543ec5ab980/packages/contracts/src/evidence-ref.ts)
  demonstrates schema-validated source, runtime, and document evidence identities.
  License: MIT.
  Weakness: a valid reference proves shape and provenance fields, not semantic conformance.
  Vendored: `docs/adr/prior-art/ADR-017/arxic-evidence-ref.ts` blob:b8e28ab2d7b440b26e8a36db6c6d040b4e614a2f

Rejected: [AlphaCodium](https://github.com/codium-ai/alphacodium) at `eb7577d`
is AGPL-3.0; its iterative test workflow may inform discussion, but no code,
translation, or close derivative enters this MIT repository.

Rejected: [Doorstop](https://github.com/doorstop-dev/doorstop) supplies useful
requirements links, but document linkage alone neither mediates tool calls nor
revokes process authority when the approved target changes.

## Considered Options

- Let the model infer intent from source and act: rejected; it preserves defects
  and makes model self-judgment an authorization source.
- Approve prose, then rely on prompts and comments: rejected; neither is a
  complete machine-checkable boundary and both drift silently.
- Put authorization only in the kernel or only in the harness: rejected; the
  kernel must own policy and lifecycle while the harness must mediate effects.
- Adopt one canonical packet, digest-bound human approval, kernel capability,
  harness admission, generated projections, and continuous verification: chosen.

## Decision Outcome

Three domain-separated levels avoid self-reference. **A:** normative `SpecPacket` plus task scope contains human-approved semantics and semantic-oracle adapter inputs, but no generated digests.
**B:** `GeneratedArtifactManifest(A)` hashes exact pseudocode/flow, protected gauge bytes, fixtures, checker/config, invocation, expected values, baseline and controls.
**C:** versioned `ApprovalEnvelope` signs A+B plus base/policy/generator/harness profile, capability request and anti-replay; `CapabilityGrant` binds C's digest.

Mechanical tests compile only from a closed scenario/oracle DSL. Otherwise the
semantic adapter/test is human-approved input in A; labels/prose never infer tests.
Stable IDs cover rules, transitions, outcomes, errors, tests and mappings. By default every changed in-scope source hunk/symbol has a generated trace comment or approved sidecar binding exact rule/transition/outcome IDs and projection digest.
“Behavior-bearing” is not a worker-selected escape hatch. Only generated, vendor, docs, or explicitly nonbehavioral paths enumerated with exact reason in A/B and signed in C are exempt; changing an exemption revokes authority.
Kernel owns lifecycle, approval, grant/revocation, journal, evidence, verdict and merge; harness services enforce effects.
Missing/stale/duplicate/uncovered anchors or tool bypasses refuse; anchors never become semantic oracles.

### Consequences

- Lifecycle is `DRAFT → SPEC_VALIDATED → TESTS_MAPPED → APPROVAL_PENDING → APPROVED → IMPLEMENTABLE → IMPLEMENTED → VERIFIED → ACCEPTANCE_AUTHORIZED → MERGE_INTENT → PUBLISHED`; any guard may produce durable `REFUSED`.
- Crash reconciliation inspects the target and records observed/inferred terminal state; it never blindly replays an irreversible effect.
- Before approval, mutation is denied; prototypes are disposable/non-promotable findings only.
- Envelope binds version/domain/task/revision, subject/base, A+B, principal/key/role, nonce, journal predecessor, time window, capability request and profile digests.
- Approver may propose but cannot be worker/evaluator; worker has no approval key; evaluator and publisher are distinct/key-exclusive.
- Every child is parent ∩ request. An approved batch binds parent/C and base digests, exact disjoint path+action scopes, dependencies, frozen per-child checks/evidence and maximum pool; retries never widen.
- Governed `task fanout` accepts A/B/C plus child rows naming approved scope/capability IDs; B/C own harness/model/timeout/suite and `--pool` only narrows. Today's free-prompt JSONL grants no mutation authority.
- Any bound semantic/gauge/policy/generator/harness/base change revokes and requires reapproval.
- Comments/sidecars prove trace coverage/staleness only; outcomes prove conformance.
- ADR-006 remains the process-confinement dependency beneath this decision.

### Confirmation

The P0 milestone begins with active SLICE-017, planned SLICE-018/019 accepting
ADR-006 only at 019, then SLICE-029..044 open strictly one at a time. Bounded
read-only research/review fanout is allowed now; mutation remains single-writer.
SLICE-036 only qualifies an approved batch in disposable child worktrees with
publication blocked. SLICE-037..042 wire effect families, 043 serially integrates
them, and SLICE-044 alone authorizes production fanout after both real
repository/provider journeys, concurrent children, attacks and an immutable exit.
Mock/synthetic tests may support a slice but cannot close the milestone. Gates are
`tests/contract/test_docs_discipline.py`, `tests/e2e/test_first_delegation.py`,
and `tests/e2e/test_gating_real_suite.py`.

## Improvements on the prior art

Spec Kit's gates become digest-bound authorization below the model. OpenSpec's
file completion becomes manifest evidence over exact bytes. XState contributes
bounded graph traversal, never intent. Arxic contributes typed evidence refs,
never semantic truth. Only these four compatible vendored mechanics are adopted;
their Ranex composition stays **UNVERIFIED** until SLICE-044's real exit passes.

Generated tests record oracle provenance: `human`, `domain-rule`, or
`requirement` produces acceptance evidence; `observed-only` produces a
characterization test and cannot silently become intent. Each behavior-changing
slice has a pre-change baseline plus a deliberately broken negative control or
mutation. A signed exemption is legal only for already-satisfied, refactor-only,
or nonbehavioral work when A/B enumerate exact path/class/reason and C signs it;
it must state why no discriminating red is possible.

## Architecture surface

Kernel domain gains A/B/C contracts, lifecycle, grant, mapping, identity and
evidence-continuity ports. CLI specification commands stay outside `main.py`
until integration. Harness adds one admission service at all effect leaves.
Generators compile only the closed DSL and render trace comments/sidecars.
SLICE-033 validates exact IDs+projection digest, uniqueness, coverage/staleness;
SLICE-036 qualifies the batch command without publication; 037..042 close the
effect inventory; 043 refuses missing/bypassed anchors before CAS; 044 tampers
each form through both real journeys. Approved executable outcomes, not anchors,
supply semantic evidence. Judge and merge bind A/B/C.

## Scope and threat delta

This closes preapproval mutation, prompt authority, scope escalation, child
amplification, stale grants, test/oracle tampering, mapping drift, and evidence
substitution. It does not prove the human chose a good product, infer business
intent from source, guarantee model quality, solve provider nondeterminism, or
replace ADR-006 confinement. Secrets remain references, never packet contents.

## Quality attributes

Deterministic serialization and transition tables make equal input produce equal
admission and verdict. Least authority and fail-closed absence bound damage.
Append-only digest continuity makes approvals and effects auditable. Stable IDs
make generated code traceable while keeping source comments non-authoritative.
Pinned real E2E repetition measures composition without claiming universal proof.

## Reversibility

Door: two-way

Packets are versioned and adapters may be replaced. Existing approvals remain
historical evidence but never authorize a new normative digest. Removing this
feature means removing its grant issuer and admission hooks together; a partial
rollback that leaves an unguarded effect path is forbidden.

## Sad paths

- 1. A blocking question remains: stay `DRAFT`; issue no implementation grant.
- 2. An outcome is not observable: refuse approval with `E-OUTCOME-AMBIGUOUS`.
- 3. A worker writes before approval: deny, journal, and leave source unchanged.
- 4. A shell, MCP, plugin, hosted tool, or auto-commit bypasses admission: deny.
- 5. Executable, argv, cwd, root, environment, or network exceeds scope: deny.
- 6. A child asks for broader authority than its parent: issue only intersection.
- 7. Spec or protected test changes after approval: revoke all descendant grants.
- 8. A mapping/comment is missing, stale, duplicate or uncovered: refuse acceptance.
- 9. A worker changes an acceptance oracle: deny and mark evidence compromised.
- 10. Only runtime observation supports an outcome: label characterization.
- 11. A process times out but leaves survivors: kill/reconcile and refuse PASS.
- 12. Evidence subject, base, packet, harness, or policy digest differs: refuse.
- 13. A model reports success without required evidence: verdict remains absent.
- 14. Parallel agents overlap unauthorized roots: deny both conflicting effects.
- 15. A prototype attempts promotion or merge: refuse by construction.
- 16. A normative change races with an admitted call: generation check revokes it.
- 17. A negative control survives: calibration fails and the milestone stays open.
- 18. Real provider credentials are unavailable: report BLOCKED, never mock-close.
- 19. Envelope nonce, predecessor, time window, task or revision replays: refuse.
- 20. Approver is worker/evaluator or a key is shared: refuse identity separation.
- 21. Crash follows merge intent: inspect target; infer state without blind replay.
- 22. Trace claims coverage but outcome fails: executable outcome wins and refuses.
- 23. Pool, retry, task order or child row widens signed batch authority: refuse.
- 24. A direct effect leaf is absent from the inventory or bypasses admission: refuse.
- 25. A worker labels an unlisted change nonbehavioral: require reapproval, do not exempt.
- 26. The projection the approver read differs from the bytes hashed in B: refuse; the exact rendered view shown for approval must deterministically re-hash to the signed manifest digest at verification.
- 27. The implementing worker authored the semantic adapter/oracle that accepts its own work: deny; adapter authorship provenance is recorded and a worker may not author the acceptance oracle for its own change.

## Test strategy

Contract tests freeze A/B/C bytes, domains, anti-replay, IDs, schema closure,
transition/refusal tables, grant intersection and errors. Property tests assert a
child never gains authority and normative change changes the digest. Harness tests
attack every inventoried process, filesystem, Git/worktree, tool-output, PTY, MCP,
auth/OAuth, plugin/provider network and storage effect before approval and outside
scope. Batch tests freeze dependency-ready sets, canonical result order, exact
path+action disjointness, pool narrowing, same-authority retries and per-child
evidence. Integration carries one packet digest through dispatch, judge and CAS.

Both permanent scenarios install CLI+harness, use a real provider and clone real
MIT repos. Ranex dogfoods issue #10 at commit
`3d0924c9c8f8f0c5483c0dc62558fdd23c51e9ce` after SLICE-019 passes:
`uv sync --frozen`, then real focused and full pytest gates. Arxic issue #109 at
`135991d9b1a07c2ffa08e38f8e261543ec5ab980` is a maintainer test/measurement
gap, not a production defect. A controller-only nonpersisting broker resolves
`github:anthonykewl20/arxic-read` to a pre-existing controller OS-keyring profile.
Without `gh auth token` or global mutation, it runs `gh repo view anthonykewl20/arxic --json nameWithOwner,isPrivate`, then uses the same process-local
`git -c "credential.helper=!/usr/bin/gh auth git-credential"` for `ls-remote https://github.com/anthonykewl20/arxic.git HEAD` and `clone --no-checkout https://github.com/anthonykewl20/arxic.git <mode-0700-temp>/repo`. It validates the
commit/licence/lock and that clone config/URL/logs contain no new credential copy.
Only a credential-free object store leaves; doubt deletes it and reports BLOCKED.
No auth env/FD reaches a worker; records hold only ref ID/outcome. Then run pinned
`corepack pnpm@11.17.0 install --frozen-lockfile`, `corepack pnpm@11.17.0 test`,
`corepack pnpm@11.17.0 --filter reference-auth-app test`, `corepack pnpm@11.17.0 --filter vulnerable-auth-app build`,
`corepack pnpm@11.17.0 --filter vulnerable-auth-app start`, and `corepack pnpm@11.17.0 exec vitest run`.
Record issues, licences, lock hashes, exact argv/cwd, apps and fixture processes.

The fixture attacks every tool family, scope, child intersection, spec revocation,
missing/stale/duplicate anchors, protected oracles, survivors and continuity. A
baseline passes and a wrong outcome fails. Existing anchors are
`tests/integration/test_delegation_command.py`, `tests/integration/test_journal.py`,
`tests/security/test_slice004_hermetic_observation.py`, and Confirmation's three
paths. Both repo/provider journeys are required; live model runs are witnessed
evidence, not deterministic replay, and skips cannot close the milestone. The named e2e anchors (`tests/e2e/test_first_delegation.py`, `tests/e2e/test_gating_real_suite.py`) count only when their preconditions (model credential, harness directory, runtime) are satisfied; a skipped gate is BLOCKED, not green. The Arxic repository is first-party and private, so its journey is a real provider/repo run for this operator but not independently reproducible by a third party — a stated limit on the exit evidence.

## Code review checklist

- Verify one canonical packet and one deterministic serializer own all projections.
- Verify human approval binds the digest after all blocking questions resolve.
- Verify no source/commit mutation path exists before an implementation grant.
- Verify every harness effect leaf calls the shared admission service.
- Verify exact process and ambient authorities are bound and child-intersected.
- Verify approved ready sets, exact disjoint scopes, bounded pool, canonical order,
  retry invariance, keyless children and single-writer CAS integration.
- Verify normative changes revoke parent and descendant grants.
- Verify every changed in-scope source hunk has exact IDs+digest unless its exact
  path/reason/class is A/B-enumerated and C-signed; comments stay trace-only.
- Verify envelope anti-replay, expiry and worker/evaluator/publisher key separation.
- Verify only closed-DSL tests compile; other semantic oracles are approved in A.
- Verify judge and merge consume the original digest/evidence chain.
- Verify mock-only, skipped-provider, or model-reported success cannot close P0.

## More Information

Vendored pins are Spec Kit `684b3d8`, OpenSpec `e50bd09`, XState `c25dba0`, and
Arxic `135991d`, all MIT. AlphaCodium `eb7577d` is AGPL-3.0 discussion-only.
Temporal, Aider, SWE-agent and StrictDoc are not adopted evidence in this ADR.
Actual OpenRouter `tencent/hy3` review was unavailable, so composition consensus
is **UNVERIFIED**. ADR-017 remains separate from ADR-006; SLICE-017..019 make
confinement the serial prerequisite, then SLICE-029..044 implement this decision.
Three mechanism details are explicitly deferred to the SLICE-029 opening rather
than left implicit: a trusted time source for the anti-replay time window, key
revocation for a compromised approver/publisher/evaluator key, and cross-batch
scope intersection (at most one live approved batch per base/subject).
