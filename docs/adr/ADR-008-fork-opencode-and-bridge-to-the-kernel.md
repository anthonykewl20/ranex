# ADR-008 — fork opencode at a pinned commit; bridge it to the kernel through hooks

**Status:** accepted
**Date:** 2026-08-03
**Decision-makers:** repo owner
**Slice:** none yet — the fork slice opens against this ADR

## Context and Problem Statement

The owner decided Ranex owns the harness (MAP §0.14): a trimmed fork of opencode
molded so every workflow step calls the proven kernel. The loop has never closed
around a real agent (`RISK-14`), so the kernel has never measured agent output.
Three things must be settled before any code is cut:
- opencode moves fast; a fork with no pinned point and no confirmed trim becomes a
  second codebase — the 561-files failure in code form.
- The harness is model-driven and untrusted; the kernel must judge bytes it
  materialises itself, never the harness's summary (accepted ADR-005).
- The wall between them is load-bearing; without it the restaurant grades its own
  dishes.

## Decision Drivers

- The wall is load-bearing: harness (model-driven, TypeScript) and kernel (code,
  Python) stay separate processes; hooks collect references, the kernel judges.
- The kernel observes a materialised commit, not the live tree (accepted ADR-005);
  the harness's summary is never evidence.
- The producer cannot approve its own work: approval is a human act, out-of-band.
- The trim must stay small enough to rebase, or the fork becomes a second codebase.
- Adoption rule: copy-and-own mature code; MIT only — a copyleft file changes what
  this repo may be distributed as.
- Deep customization is blocked; a gauge the user can recalibrate is no gauge.

## Prior art

Searched: code-host queries over clones of github.com/anomalyco/opencode and
github.com/pre-commit/pre-commit, plus GitHub searches for "agent harness plugin
hook", "git hook run external checker", "worktree per-task isolation"; tool: git
clone + local grep/read. Alternative harness bases surveyed at licence level only
(see Considered Options).

Rejected: git hooks — https://github.com/git/git. The hook-invokes-external-checker
pattern is the mature ancestor of the bridge, but a hook's verdict is a bare exit
code: not bound to a subject digest, not signed, not journaled, and the checker runs
unconfined in the caller's trust domain. git is also GPL-2.0, so its code cannot be
vendored into this MIT tree; the pattern is reimplemented, never copied.

Rejected: husky — https://github.com/typicode/husky. A git-hook manager: it sets
`core.hooksPath` and orchestrates hooks but produces no verdict of its own and adds
no wall between producer and judge; it inherits git's unbound exit-code semantics.
The fork inherits husky from the root `prepare` script and removes it.

- **opencode's hook contract** — the surface the kernel bridge collects through: a
  `Hooks` interface with an `event` hook plus `tool.execute.before/after`,
  `command.execute.before` and `shell.env` hooks.
  <https://github.com/anomalyco/opencode/blob/012c2f57f976489d88bd4598a056b4bdcdd428ee/packages/plugin/src/index.ts>
  License: MIT — vendorable without restriction.
  Weakness: hooks run in-process in the harness's trust domain and are a two-way
  channel — a loaded plugin can rewrite tool args, the system prompt and the shell
  env; the host can skip a hook, and events whose `location.directory` does not
  match are dropped before any hook sees them. `permission.ask` is declared but has
  no call site at this pin. Hook output is therefore untrusted reference, never
  evidence.
  Deliberately not copied: the mutable-output trigger dispatch. The npm plugin
  loader stays in kept code but is locked — no config-driven or npm-installed
  plugins (§17.6).
  Vendored: docs/adr/prior-art/ADR-008/opencode-plugin-hooks.ts blob:edfa0139dfcaf0e877ab906fabe8e0527afc3915

- **pre-commit's run loop** — the mature hook-drives-external-judging-of-a-diff
  pattern: collect the changed files, run each checker, OR the return codes.
  <https://github.com/pre-commit/pre-commit/blob/242ce8a25657be59f2770b50de41fe0fd508820d/pre_commit/commands/run.py>
  License: MIT — vendorable without restriction.
  Weakness: the verdict is `retval |= current_retval` — a bare return code not bound
  to any digest of the tree it measured, so it can be replayed against a different
  tree; checkers run unconfined and the result dies with the process (no journal).
  Deliberately not copied, but kept as ideas: `staged_files_only` measuring exactly
  the staged tree, and failing when a checker mutates the subject mid-measurement —
  the ancestors of commit-binding and the merge-time digest re-check.
  Vendored: docs/adr/prior-art/ADR-008/pre-commit-run.py blob:8ab505ffbeb79949dbf00d4606e4e0200c15f7b7

## Considered Options

1. **Fork opencode at a pinned commit and trim.** Chosen: MIT, and verified in-tree
   to have the hook surface and headless `run` the bridge needs.
2. **Build a harness from scratch.** Rejected: reinvents the agent loop, provider
   routing and tool surface — what the adoption rule forbids.
3. **Keep opencode as a dependency / control plane beside it.** Rejected: the owner
   overturned "control plane, not an agent harness" (MAP §0.14); a dependency cannot
   be trimmed or molded.
4. **Fork a different base.** Rejected: hermes-agent audited out 2026-08-01 (zero
   contribution, git `d9db059e98`); OpenClaw is quarry, never a base (MAP §2.1).
   External bases were surveyed at licence level only — OpenHands (MIT),
   continue/cline/goose (Apache-2.0) — and not read deeply this session; opencode is
   chosen on verified hook surface + headless run + MIT, recorded as a gap rather
   than pretended to be a wide bake-off.

## Decision Outcome

In the context of owning the harness, facing an upstream that moves fast and a
producer that must not be trusted, we chose to fork opencode at tag `v1.18.11`
(commit `012c2f57f976489d88bd4598a056b4bdcdd428ee`), trim it to the keep-set, and
bridge it to the kernel, accepting the standing cost of rebasing.
- Keep: `opencode`, `core`, `cli`, `llm`, `plugin`, `protocol`, `schema`, `tui`,
  `server`, `sdk`, `effect-drizzle-sqlite`, and top-level `patches/` (load-bearing
  for keep deps).
- Cut: the remaining packages and top-level `artifacts/`, `infra/`, `github/`,
  `sdks/`, `sst.config.ts`, `nix/`, `perf/`; `ui` keeps only `tui`'s audio assets;
  `effect-sqlite-node` is cut as unimported.
- Bridge: the dispatcher (Ranex) creates the worktree and records task→worktree
  before the harness runs. On task end the harness commits; the kernel derives the
  subject commit by reading that worktree's HEAD itself, cross-checks the emitted
  reference, materialises the commit (ADR-005) and judges. Approval is out-of-band.

### Consequences

- Good: fork point and trim recorded and checkable; the bridge reuses the proven
  verdict path; kept `sdk` is the internal client the CLI/TUI need, not the public
  extension SDK §17.6 blocks.
- Good: commit-then-materialise makes the judged subject immutable and ADR-005-
  consistent; the harness's live tree is never the evidence.
- Bad: every upstream release costs a rebase, and two runtimes plus a bridge between
  them; if the trim grows, second codebase.
- Bad, known at the pin: cutting `script`, `codemode`, `http-recorder`,
  `effect-sqlite-node`, `ui` costs manifest edits; `codemode` also source edits (four
  opencode files); `script` is the opencode+cli build (replacement needed);
  `http-recorder` drops the recorded-test suites.
- Not closed: confinement from keys and journal (ADR-006 unbuilt, `RISK-06` stands);
  approver auth (`RISK-07`) — approval is out-of-band but the approver stays an
  unauthenticated string until that is designed.

### Confirmation

`tests/contract/test_docs_discipline.py` enforces this ADR's pinned citations and
vendored bytes. The runtime confirmation is the gear-mesh run (MAP §17.5): one task
turning dispatch → loop → hooks → kernel judgement → journal, ending in evidence and
a verdict CANDIDATE — the PASS stamp is a human's, out-of-band. The fork slice adds
this as an e2e test; until it exists this ADR stays `proposed`.

## Improvements on the prior art

1. **The verdict is bound, not returned.** pre-commit's checker yields a bare exit
   code; the kernel binds the verdict to the subject commit's digest, so stale or
   replayed evidence stops counting.
2. **The judge is outside the producer and observes an immutable subject.** git
   hooks and husky run the checker in the caller's trust domain against the live
   tree; the kernel is a separate process that materialises the committed work
   (ADR-005), so the producer cannot swap the ingredients mid-measure.
3. **References, not summaries.** The bridge forwards session id, worktree, commit
   and tool calls; the kernel reconstructs from commit bytes.
4. **Approval is removed from the producer.** pre-commit's caller both runs and
   accepts; here the harness can produce evidence but never the stamp.
5. **A durable record.** pre-commit's result dies at exit; the kernel appends to the
   hash-chained journal.
6. **Subject-isolation, inherited honestly.** pre-commit's `staged_files_only` and
   its fail-if-the-checker-mutates-the-subject are the ancestors of commit-binding
   and the merge-time digest re-check; named, not reinvented.

## Architecture surface

No port in `src/ranex/` changes. The bridge is a plugin inside the harness (the
`Hooks` contract) plus the kernel CLI it invokes as a separate process over
stdio/HTTP; no shared runtime, no shared trust. The fork trims built-in
provider-auth plugins for providers Ranex does not route to, and locks the plugin
list — no config-driven or npm-installed plugins — so the bridge is the only
LOADED plugin. The kernel's `evaluate()` is untouched; the bridge produces
evidence, never a verdict, and never an approval.

## Scope and threat delta

Governs the fork point, the trim, and the harness→kernel bridge. STRIDE letters
moved: **T** (the harness is an untrusted producer; hook output and the emitted
worktree reference are untrusted, matched against the kernel's own task→worktree
record), **E** (evidence is never a summary — the diff is the materialised
commit, and execution output rides the signed-record path with known hole RISK-06),
and **S** (the kernel endpoint authenticates its caller; spoofing the judge is a
named sad path). Non-goal: confining the loop from keys and journal (ADR-006,
unbuilt). Attacker out of scope: a kernel already compromised; same-uid
reachability of keys and journal is `RISK-06` until ADR-006 lands, and is not
claimed away here.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Maintainability | upstream releases a new tag | trim diff rebases; keep-set re-confirmed against the package graph |
| Functional correctness | harness reports a task done | verdict derives from the materialised commit, not the report |
| Security | a hook payload or worktree reference is forged | kernel matches it against its own task→worktree record; mismatch blocks |
| Security | the judged tree changes after the digest | merge re-checks the commit digest; mismatch blocks |
| Portability | the kernel loses model access | verdict unchanged (`PR-10`) |
| Performance | trimmed engine vs bulky upstream | horsepower (governed tasks done) and fuel (tokens/cost/wall-time per task) measured on the same tasks at fork time |

## Reversibility

Door: two-way

The fork can be abandoned for upstream or re-trimmed; nothing here is irreversible.
The cost of reversing is the molding and bridge effort; the cost of not rebasing is
a silent second codebase. Both are labour, not locks.

## Sad paths

Derived by walking each assumption and asking how it fails.

| # | Input/failure | Required behaviour |
|---|---|---|
| 1 | upstream moves and the trim will not rebase | stop; measure rebase cost per release; re-decide the fork |
| 2 | a hook payload or the emitted worktree reference is forged | kernel matches it against its own task→worktree record; mismatch blocks |
| 3 | the judged tree mutates between digest and merge | merge re-checks the commit digest; mismatch blocks; the subject is a commit, immutable by construction |
| 4 | the bridge plugin fails to load | the harness refuses to start unbridged; a silent unjudged run is a defect, never a default |
| 5 | a cut package proves load-bearing at build time | build fails; restore to keep-set and record the correction here |
| 6 | the vendored Hooks contract no longer matches the pin | research check fails; pin and copy must agree |
| 7 | session/worktree state grows unbounded on disk | bounded and rotated; the durable record is the kernel's journal |
| 8 | the harness names the approver, the gate, or the subject ref | refuse — the harness produces evidence only; approver, gate and subject come from the operator/kernel, never the producer |
| 9 | a copyleft dependency enters via the fork's graph | refuse; MIT only, checked before the copy lands |
| 10 | the worktree or commit is gone before the kernel reads it | absence blocks — FAIL, not skip |
| 11 | the pinned tag is moved or deleted upstream | the 40-hex commit is the pin, not the tag |
| 12 | another plugin loads beside the bridge and mutates its report | cannot happen — the plugin list is locked; no config/npm plugins |
| 13 | a spoofer invokes the kernel endpoint | the endpoint authenticates its caller; unauthenticated calls refuse |
| 14 | a rebase renames or drops a bridged hook | the bridge collects nothing and the run is treated as unbridged, refusing to start |
| 15 | model credentials are present or absent | verdict unchanged (`PR-10`) |
| 16 | kernel endpoint or hook stream floods or stalls past bound | bound and refuse; refusal is recorded, never a silent wait |

## Test strategy

Contract level anchors the decision today; the fork slice adds the runtime proof.
`tests/contract/test_docs_discipline.py` enforces this ADR's pinned citations,
vendored bytes and NOTICE. `tests/unit/test_gate_verdict.py` is the control that the
kernel's `evaluate()` stays pure while the bridge feeds it. The hermetic subject is
anchored by `tests/security/test_slice004_hermetic_observation.py` — the bridge's
commit-then-materialise must satisfy the same property. `tests/e2e/test_run_produces_evidence.py`
and `tests/security/test_evidence_trust_root.py` remain the honest signed-record path
the harness's references are admitted through. Red-then-green at slice time: the
gear-mesh e2e is written to fail with no bridge, then pass with it, and ends in
evidence plus a verdict candidate, never an auto-approval. No global coverage
percentage; delta coverage on changed lines and full coverage of the bridge's error
branches.

## Code review checklist

- Is the fork point the 40-hex commit, not the tag or a branch?
- Does every keep-set package still build after the cut, and were the manifest edits
  for `script`/`codemode`/`http-recorder` made, not assumed?
- Does the harness commit before the kernel materialises, and does the kernel match
  the emitted worktree/commit against its own task record?
- Is any hook payload or emitted reference trusted as evidence or a verdict? Delete it.
- Does the harness approve, merge, stamp, or name the approver anywhere? It must not.
- Is the plugin list locked (no config/npm plugins)?
- Did the rebase grow the trim diff, or drop/rename a bridged hook? Record it.

## More Information

Supersedes nothing; it follows accepted ADR-005 (materialised commit) and realises
MAP §0.14's harness decision, carrying §17 to a pinned commit. The two mature
candidates not adopted as code are in `## Prior art` (git hooks, husky); the
rejected bases in `## Considered Options`. Delegation (foreman → supervisors →
workers, clean-room from oh-my-openagent) is a later ADR. Open items handed to the
fork slice: the §17.4 horsepower/fuel baseline, the cli package's daemon/service
surface (`lildax` + second entry point), the task→worktree record via trusted
dispatcher path, and the kernel-endpoint auth choice.
