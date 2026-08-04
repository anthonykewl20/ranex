# ADR-010 — first delegation: one operator request becomes governed work

**Status:** accepted
**Date:** 2026-08-04 (accepted same day, owner, with fan-out added before freezing)
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-008-first-delegation.md` — opened against this
decision. The decision is written first, as the rule requires.

## Context and Problem Statement

Today a human is the wire between `ranex task dispatch`, the harness, the emission
file, and `ranex task judge`; there is no path from "operator states a task" to
"the kernel judges real agent work". The parts each work. The harness refuses to
start unbridged, runs headless, commits on session idle and appends one JSON line
`{task_id, worktree, commit}`; `cmd_task_judge` cross-checks that line against its
own dispatch record, reads the gate catalog and keyring from the commit, verifies
signed evidence, and journals a CANDIDATE with its missing claims — never a PASS.
Absent: a dispatcher, a suite run in the delegated worktree, promotion, merge.

A REFUTE panel then exposed the harder problem, verified on the artifact:
`src/ranex/cli/main.py:1368` reads the private signing key into kernel memory
*before* the bound command spawns, and `RISK-06` (`docs/MAP.md:1169`) already
reproduces that command taking it from `/proc/<ranex-pid>/environ`. Under
delegation the executed suite is code an AI wrote minutes earlier: a planted
`conftest.py` could sign any record while every invariant still looked intact.

## Decision Drivers

- The product has no front door; every judged result passes through a human's hands.
- The kernel must judge work it did not produce and whose summary it discards.
- The delegated suite is untrusted code, not this repository's reviewed code.
- Nothing that signs may share a process lifetime with what it measures.
- A non-interactive run must terminate on its own, right or wrong.
- Merge and promotion stay a human's, per standing doctrine.
- Scope stays one slice: one task, one worktree, one verdict — fanned out.

## Prior art

**Searched:** `gh api search/code` and `gh api search/repositories` for headless agent drivers, gating merge queues, `unsigned link in-toto repo:in-toto/in-toto`, `signing key isolation build attestation`,
`provenance generator sign after build`, and `obs-sign`; `leitir` corpus materialisation of `pypi:in-toto`, `github:slsa-framework/slsa-github-generator`, `github:tektoncd/chains`, `github:sigstore/cosign`;
`opensrc` caching of `All-Hands-AI/OpenHands`, `SWE-agent/SWE-agent`, `sst/opencode`, `bors-ng/bors-ng`; opendev.org's Gitea API for Zuul. Three of those repository searches returned **zero results** —
the phrase-level search for this pattern finds nothing, which is itself evidence of how thinly it is documented.

**A result of the search, not an assumption: no mature project solves the whole problem.** Each half is mature — headless agent drivers, gating merge bots, provenance signers that sign from outside the build — and nothing mature composes them behind a non-LLM verdict.

- **opencode headless `run`**, the harness's own upstream — <https://github.com/anomalyco/opencode/blob/v1.18.12/packages/opencode/src/cli/cmd/run.ts>
  License: MIT. Copied: subscribe to the event stream before prompting, end on an explicit session-idle transition, exit non-zero if any session error was seen. Read there too: a non-interactive run auto-rejects every permission unless an auto-approve flag is passed.
  Weakness: the JSON stream has no terminal event and no permission event, so a supervisor cannot separate clean completion from a kill — hence process exit plus a wall-clock bound as the terminal signal, never the stream.
  Vendored: docs/adr/prior-art/ADR-010/opencode-run-headless.ts blob:3927f615a08053a0c631e8baaa1cbd0337a37127
- **bors-ng's batcher**, the merge bot authors never push through — <https://github.com/bors-ng/bors-ng/blob/ca725797e53a88e954998de0bbb14a8a5acb13ab/lib/worker/batcher.ex>
  License: Apache-2.0. Copied: an immutable candidate SHA the *system* builds from base tip plus approved commit SHAs, promoted only by a non-force ref update whose 422 is the concurrency detector.
  Weakness: between "all checks green" and "push" it re-validates nothing — not the approval, not the PR head, not the base tree — so authorization is only as fresh as the batch is old.
  Vendored: docs/adr/prior-art/ADR-010/bors-ng-batcher.ex blob:f835eb883112b9b110d3e4d6eac4f6a841997ae5
- **SWE-agent's single run** — one agent, one instance, one artifact — <https://github.com/SWE-agent/SWE-agent/blob/v1.1.0/sweagent/run/run_single.py>
  License: MIT. Copied: a named exit-status taxonomy where every abnormal termination still yields a *typed* artifact, with a separate predicate deciding whether that artifact may touch anything real.
  Weakness: a single-shot in-process script with no cancellation channel and no `try`/`finally` — a fatal path skips cleanup and leaks the sandbox, which a kernel flow cannot inherit.
  Vendored: docs/adr/prior-art/ADR-010/swe-agent-run-single.py blob:8ba4f77bcb939748974f3dddf2bdb63d3a7abb26
- **Zuul's dependent pipeline**, the gate that merges — <https://opendev.org/zuul/zuul/src/commit/37b54283676b372740cd3f33b85171ac677da9de/zuul/manager/dependent.py>
  License: Apache-2.0. Copied: evidence bound to the *future* state being merged (speculative merge); the gate performs the merge; humans never push.
  Weakness: operationally enormous — Zookeeper, executors, drivers — and its checks are job exit codes, not claim-per-gate evidence. Copy the pattern, reject the code.
  Vendored: docs/adr/prior-art/ADR-010/zuul-dependent-pipeline-manager.py blob:2bb328c3be6b0632e09358ddef48a3c408e71b5d
- **OpenHands' headless driver** — <https://github.com/OpenHands/OpenHands/blob/0.59.0/openhands/core/main.py>
  License: MIT. Examined: an explicit agent state machine in which "needs a human" is a first-class state, and a fake-user-response function that turns a would-be hang into progress.
  Weakness: that same function makes "done" indistinguishable from "was pushed past a checkpoint it should have stopped at"; and this 0.x line is superseded by its own authors' V1 SDK, so building on it is building on a dead line.
  Vendored: docs/adr/prior-art/ADR-010/openhands-headless-main.py blob:43a07a02db1bd72ff1bcc9f4ce2641f291443120
- **SLSA's GitHub generator**, the strongest evidence that a builder can be structurally barred from the signer — <https://github.com/slsa-framework/slsa-github-generator/blob/4d014fae4dbd39eb09e8d40348b73db095e6ba9a/.github/workflows/builder_go_slsa3.yml>
  License: Apache-2.0. Copied: the untrusted `build` job runs with `permissions: contents: read` only, while a separate `provenance` job on a different ephemeral VM is the sole holder of `id-token: write` — the only path to a signing identity, there being no long-lived key at all — and the artifact crosses the boundary as a sha256-verified download. The part most worth copying: the separation is checkable *after the fact*, because the Fulcio certificate names the reusable workflow, so a signature minted from the build job carries the wrong identity and fails verification. Detectable violation beats trusted separation.
  Weakness: every bit of the enforcement is GitHub's platform — per-job VM isolation, per-job OIDC issuance, reusable-workflow identity — and none of it transfers to a single Linux host, which is where Ranex runs.
  Vendored: docs/adr/prior-art/ADR-010/slsa-builder-go-two-job-split.yml blob:c82b7fc7de2f53e57d672a3807ae2e8a259b6609
- **in-toto**, record-then-sign as separable operations — <https://github.com/in-toto/in-toto/blob/c82fe5d21aaa61c7f1a213db20a46f10bb3f411a/in_toto/in_toto_sign.py>
  License: Apache-2.0. Copied: link metadata is a first-class artifact that can be produced unsigned — `in_toto_mock` stores unsigned link metadata — and signed later by a separate CLI process that loads the file and applies a signature.
  Weakness: the split is advisory, not structural. The default documented flow (`in_toto_run` with a signer) puts the key in the very process that just executed the untrusted command, and nothing forbids it.
  Vendored: docs/adr/prior-art/ADR-010/in-toto-sign.py blob:fa1150ad7eb1dc1fca32444e01a9e73bb820f784
- **Tekton Chains**, observe-then-sign from outside the build — <https://github.com/tektoncd/chains/blob/01d9ebfdae7a02247b1b00f48e44dd63d8a611ec/pkg/reconciler/taskrun/taskrun.go>
  License: Apache-2.0. Copied: the controller ignores anything not finished (`if !tr.IsDone() { return }`), checks an idempotence marker so a subject is signed exactly once, then signs — and the key lives only in the controller pod, never in a build pod.
  Weakness: it signs over results such as `*_DIGEST` that the untrusted build pod itself wrote into the TaskRun status, so the subject is self-reported. Key custody is separated; subject binding is not.
  Vendored: docs/adr/prior-art/ADR-010/tekton-chains-taskrun-observe-then-sign.go blob:49bc00325fbbdfea44bf8bcbbcb56dd902c51f99
- **Rejected:** <https://github.com/OpenHands/OpenHands> as a base — a superseded line, no worktree isolation, no external merge authority, and completion and verification decided *inside* the agent loop: the self-scoring failure we remove.
- **Rejected:** <https://github.com/openstack-infra/zuul> (Zuul's archived mirror) as a base — its operational surface dwarfs the whole kernel, and its checks are job exit codes rather than evidence bound to a tree digest.
- **Rejected:** <https://github.com/openSUSE/obs-sign> — a signing daemon on a separate host, some twenty years in production signing openSUSE packages. Rejected twice over: GPL-2.0 cannot enter this MIT tree, and a signing
  service reachable from the build host still lets a compromised builder *request* a valid signature — that separates key custody, not signing authority.
- **Rejected:** Zuul's bubblewrap driver (<https://opendev.org/zuul/zuul>, tag `14.2.0`; the archived mirror is <https://github.com/openstack-infra/zuul>) — `--unshare-all` with a fresh `/proc` defeats exactly the same-uid
  `/proc/<pid>/environ` read measured here, and it probes user-namespace availability at runtime and adapts. Rejected as the answer because the secret-holding executor is the direct ancestor of the untrusted code —
  namespace confinement, not key absence — and its unprivileged path needs user namespaces, which this host's `apparmor_restrict_unprivileged_userns=1` blocks. Its runtime userns probe is still worth stealing as a diagnostic.

## Considered Options

1. **Leave the human as the wire.** Rejected: the product has no front door, and
   the loop has still never closed around a real agent.
2. **Let the harness call a kernel endpoint.** Rejected here: no endpoint
   exists, and authenticating its caller is an open ADR-008 item (`RISK-07`).
3. **Let the harness produce its own evidence.** Rejected: that is the bullseye
   painted around the dart — one actor doing the work and the scoring.
4. **Kernel-driven delegation, with execution and attestation separated.**
   Chosen.

## Decision Outcome

In the context of an operator request that must become judged work, facing a
loop whose output cannot be trusted and whose code must nonetheless be run, we
chose **a kernel-driven `ranex task delegate` in which execution and
attestation never share a process lifetime**, accepting that merge and
promotion stay manual and that the model credential stays exposed.

`delegate` dispatches the worktree; spawns the harness headless from an environment built from empty — pinned `PATH`, scratch `HOME` outside the worktree, the two bridge variables, one model-credential variable, an auto-approve flag, a wall-clock timeout; cross-checks the emission against the kernel's dispatch record; then the *kernel* runs the frozen suite against the emitted commit and `judge` journals a CANDIDATE. The execute phase holds no signing key and **refuses to start if the signing-key variable is present** — absence enforced by refusal. Signing is a separate, later invocation.

Delegations **fan out** over a bounded pool, one worktree each, because that isolation was always the point. Both shared resources are already safe: `append` opens `BEGIN IMMEDIATE` and reads the previous link inside that write transaction, so SQLite serialises writers and the chain cannot fork, and the store is content-addressed with concurrent-writer safety proven in SLICE-006. Ordering belongs to the journal, not the schedule; the pool is bounded because unbounded fan-out starves the machine doing the measuring.

### Consequences

- Good: an operator request reaches a kernel verdict without a human relaying it.
- Good: the delegated-evidence path of `RISK-06` closes without root, namespaces
  or a second uid — measured unavailable on this host.
- Good: a planted `conftest.py` can fail the suite, and cannot sign anything.
- Bad, and **not closed**: the model credential sits in the harness environment
  with the network open, so the loop can post it anywhere. Mitigated only by a
  scoped, spend-limited key; egress confinement is deferred, not solved.
- Bad: `RISK-06` stays open for `ranex run` as invoked today. This closes the
  delegated path, not the risk.
- Bad: the harness commits everything in the worktree, junk included.
- Bad: one emission per process, so a resumed session emits once.
- Bad: the auto-approve flag is required before a real model may edit a file at
  all, which widens what the loop may do inside the worktree.
- Bad: a wall-clock timeout is a blunt terminal signal and will cut good work.

### Confirmation

The slice must prove: the execute phase **refuses** when the signing-key
variable is present in its environment; no signing key is reachable from
anywhere in the execute process tree, checked through `/proc`, not by
inspection; a `conftest.py` planted in the delegated commit cannot produce a
signed record; the emitted worktree and commit are cross-checked against the
dispatch record and a mismatch blocks; a `commit == base` emission is refused
rather than judged; and a delegated run against a *real* model ends in a
journalled CANDIDATE naming its missing claims, with no PASS anywhere; and that
N concurrent delegations yield N independent verdicts over a journal that still
verifies — the check that would catch a forked chain. Absent any one of these
the ADR stays `proposed`.

## Improvements on the prior art

1. **Execution and attestation are different process lifetimes.** Every driver cited runs the checker and reports from one process; here the phase that runs
   attacker-authored code never holds the key that would make its output count.
2. **Absence is enforced by refusal.** SWE-agent decides *afterwards* whether an artifact may touch anything real; the execute phase refuses to start at all
   when the signing variable is present, so there is no window.
3. **The terminal signal is not the stream.** opencode's `run` trusts a session-idle transition; the kernel uses process exit plus a wall-clock bound, because
   the stream has no event that distinguishes a kill.
4. **Freshness is re-checked at the boundary.** bors-ng promotes a candidate it validated some time ago; here the emitted reference is matched against the
   kernel's dispatch record, and a merge-time digest re-check follows.
5. **Evidence is claims, not exit codes.** Zuul reduces a job to a status; the kernel requires a satisfying record per claim, bound to the subject digest, and
   names the ones it did not find.
6. **"Needs a human" is not converted into progress.** OpenHands fakes a user reply to keep going; here delegation's only outcome is a CANDIDATE, and the stamp
   stays out-of-band.
7. **The untrusted phase cannot name its own subject.** Tekton Chains signs `*_DIGEST` results that the untrusted build pod wrote into the TaskRun status, and
   the generic SLSA generator accepts `base64-subjects` "formatted the same as the output of sha256sum" from the caller's own build job. Ranex computes the
   subject digest from the tree itself, so a delegated run cannot choose what it is judged against — a genuine improvement over two mature systems.
8. **Separation is an invariant, not an option.** in-toto ships record-then-sign as one available flow; Ranex refuses to execute at all when the signing-key
   variable is present.
9. **Adopted from the prior art, not invented here:** hash-verified handoff at the phase boundary (SLSA's `secure-download-artifact` re-verifies a sha256
   before signing — the point of maximum risk); a sign-once idempotence marker (Chains' `Reconciled` annotation); and the ambition of *verifiable* separation,
   where a phase-2 signature carries something phase 1 provably could not produce, so a violated separation is detectable rather than merely trusted. Say it
   plainly: Ranex does **not** have that detectability property today. A later slice must earn it.

## Architecture surface

A new `ranex task delegate` command in `src/ranex/cli/`, reusing the existing
dispatch and judge paths and ADR-009's materialisation for the suite run. The
verdict kernel is **not** widened: `evaluate()` is untouched, and delegation
produces evidence and a candidate, never a verdict or an approval.

Rebranding lands in the same slice: the operator-facing command and product name
become `ranex` and `Ranex` in the harness fork, opencode's MIT attribution retained.
Operator-visible surfaces only, not a wholesale internal identifier rewrite.

## Scope and threat delta

In scope: one task, one worktree, one headless run, one suite execution, one
CANDIDATE. Out: merge, promotion from CANDIDATE, approver authentication,
egress confinement, and multi-task scheduling.

STRIDE movement: **E** narrows — the executed suite can no longer reach a
signing key, so it cannot elevate into signing a record. **I** widens — a model
credential now lives in a process the loop controls, with the network open.
**T** is unchanged: the harness was already an untrusted producer. Explicit
non-goal: this does not make the delegated code good, only its scoring honest.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Confidentiality | signing key present during execute | process refuses to start |
| Integrity | delegated commit plants a test-time hook | no signed record is produced |
| Functional correctness | run finishes with claims unmet | CANDIDATE naming each missing claim |
| Reliability | loop hangs | terminated at the wall-clock bound, typed outcome |
| Accountability | emitted reference disagrees with dispatch | blocked before materialisation |

## Reversibility

Door: two-way

The command can be deleted and the human returns to being the wire; the journal
format and the subject digest do not change, so no evidence is invalidated either
way. What is **not** reversible is the expectation: once an operator has a front
door, withdrawing it removes the only path anyone uses. The execute/attest split is
likewise cheap to add and expensive to retract — every later signing path assumes it.

## Sad paths

Derived by state transition over the delegation lifecycle, plus boundary values
on the terminal signal.

| # | Failure | Required behaviour |
|---|---|---|
| 1 | signing-key variable present at execute time | refuse to start; never execute holding a key |
| 2 | harness exits non-zero | typed outcome recorded; no candidate journalled |
| 3 | harness never emits | refuse; a missing emission is absence, and absence blocks |
| 4 | emitted worktree or commit disagrees with dispatch | block before materialisation |
| 5 | harness commits nothing (`commit == base`) | refuse; there is no subject to judge |
| 6 | wall-clock timeout expires mid-work | terminate, record the timeout, journal no candidate |
| 7 | model credential absent | refuse at start rather than run a loop that cannot act |
| 8 | auto-approve absent, so nothing is edited | falls out as sad path 5; the empty commit is the signal |
| 9 | delegated commit plants a test-time hook (`conftest.py`) | permitted to run and to fail the suite; execute and attest are separate process lifetimes, so the hook has no key in reach and cannot obtain a signature |
| 10 | delegated commit edits the gate catalog or keyring | judge reads both **from the commit**, so this is visible in the diff — **not blocked automatically**; review's job until merge-time re-check lands |
| 11 | two `delegate` runs for one task id | second refuses; one dispatch, one judgement |
| 12 | worktree deleted mid-run | refuse at cross-check; HEAD cannot be read |
| 13 | loop exfiltrates the model credential | **not caught** — no egress confinement; stated, not mitigated |
| 14 | loop writes plausible code that passes a weak gate | **not caught** — the gate's quality is the operator's burden (`PR-06`) |
| 15 | concurrent delegations append to the journal at once | serialised by `BEGIN IMMEDIATE`; the chain still verifies, or the run is a defect |
| 16 | two concurrent tasks are given the same worktree path | refuse at dispatch, which already rejects an existing path |
| 17 | fan-out exceeds the machine | bound the pool and queue the remainder; never let breadth decide a verdict by timing out honest work |
| 18 | concurrent tasks edit the same file | permitted here — they are separate subjects with separate verdicts; the collision is merge's problem, and merge is a later slice |

## Test strategy

Levels: security tests for the refusals that carry the decision — sad paths 1 and 9,
written red-first against a delegation that *does* hold the key; integration tests
for the environment construction and the cross-check; one end-to-end run against a
real model for the confirmation.

`tests/security/test_keygen_key_confinement.py` is the existing control on key
handling and gains the execute-phase refusal.
`tests/integration/test_fork_startup_bridge.py` pins the bridge's startup contract
and gains the constructed-environment cases.
`tests/e2e/test_gear_mesh_candidate_verdict.py` is the honest baseline to beat: it
hand-writes its evidence and drives a deterministic `ranex-noop/noop` model that does
no work, so it proves the wiring and nothing about agent output. The delegated e2e
replaces both props. `tests/e2e/test_cold_start_journey.py` extends to reach
`delegate` from zero state, and
`tests/security/test_slice004_hermetic_observation.py` is rerun under delegation as
the control that ignored state never enters the subject.

New files and exact test names belong in the slice. Sad paths 13 and 14 are declared
uncatchable rather than tested, which is the honest outcome. No global coverage
percentage: delta coverage on changed lines, full coverage of the refusal branches.

## Code review checklist

- Is there any path on which the execute phase runs with a signing key reachable
  from its process tree, including via an inherited or re-exported variable?
- Is the refusal a check on the environment as it will be *exec'd*, given that
  `os.environ.pop()` was measured not to change `/proc/self/environ`?
- Is the environment built from empty, or filtered from the ambient one?
- Is the emitted reference ever trusted before it is matched against dispatch?
- Does any failure path produce a candidate, or a PASS, by omission?
- Is the model credential named once, scoped, and nowhere else in the tree?
- Does the rebrand alter attribution, or only operator-visible strings?

## More Information

Measured on this host, 2026-08-04, and reported as measurement rather than theory: `os.environ.pop()` does not alter `/proc/self/environ` — the exec-time environment persists, so runtime scrubbing is impossible; a same-uid
process reads another's `/proc/<pid>/environ` successfully, and the key path it leaks names a 0600 file readable by its owner; `unshare -U` succeeds unprivileged but writing `/proc/self/uid_map` fails with `EPERM`, because
this host sets `kernel.apparmor_restrict_unprivileged_userns=1`. A different uid therefore needs a privileged setup step — which is why the split, not a sandbox, is the answer here.

Verified against official documentation. SLSA v1.0 Build L3 (<https://slsa.dev/spec/v1.0/requirements>): "Any secret material used for authenticating the provenance, for example the signing key used to generate a digital
signature, MUST be stored in a secure management system appropriate for such material and accessible only to the build service account. Such secret material MUST NOT be accessible to the environment running the user-defined
build steps." A published standard requires exactly the property adopted here, so this design is aligned with an existing specification rather than invented in this repo. sigstore
(<https://docs.sigstore.dev/cosign/signing/overview/>): "Fulcio issues short-lived certificates binding an ephemeral key to an OpenID Connect identity. Signing events are logged in Rekor, a signature transparency log,
providing an auditable record of when a signature was created." Ephemeral signing material is a stronger answer than a long-lived key and is **not** adopted now — it needs an OIDC identity provider and a CA — but
shortening key lifetime is the direction of travel.

Zuul has no GitHub presence: its mirror was archived in 2019 (`pushed_at 2019-07-31`), so it is cited at the dotted-numeric tag `14.2.0` on opendev.org rather than at a 40-hex commit. Stated plainly, not dressed as a pin.

Open: egress confinement for the credential; promotion from CANDIDATE; merge.
