# Session handoff — 2026-07-31

For the next agent. Read this, then [`docs/README.md`](README.md).

Every claim below is labelled. **FACT** means measured in this repository or
verified against a cited external source. **INFERENCE** means concluded but not
directly proven. **UNVERIFIED** means neither. Do not promote a label without
doing the work.

## The two rules that matter most here

**1. Nobody holds true answers — verify everything.** Not the owner, not you, not
any model. Your training knowledge is stale. HY3, Codex, Grok, MiMo and DeepSeek
are all susceptible to assumption. Every claim needs proof at `path:line` or a
cited source. This is the owner's standing mandate, restated three times.

**2. Ranex is not novel — find the working piece before designing anything.**
Others have already built what you are about to invent, and their version is
public and maintained. Search first, adopt, then improve. See
[`architecture/rfcs/RFC-0003`](architecture/rfcs/RFC-0003-deterministic-session-continuity-and-drift-tripwires.md)
for what happens when you skip this: three of its four provisions were rewritten
as adoptions of `cog`, `AGENTS.md`, and `pre-commit` after a sweep found them.

**Corollary — a negative search result is evidence about your search, not about
the corpus.** Do not declare anything missing until you have searched every
location, including these:

```
docs/architecture/            docs/architecture/reviews/   docs/architecture/reviews/artifacts/
docs/architecture/rfcs/       docs/research/               architecture/contracts/   schemas/
.claude/worktrees/kernel-tracer/            ← the R&D tracer, untracked src/ and tests/
.claude/worktrees/phase-2-runtime-bootstrap/ ← inherited Hermes source
```

## What Ranex is

A governance harness that makes unreliable AI agents produce reliable enterprise
software. Deterministic contracts compiled from architecture documents into
checking code — not prompts. A **non-technical owner** describes intent; an
assistant translates it; a fleet of AI workers executes under enforced
constraints. Derived from Hermes Agent, stripped of its general-assistant and
commercial surface.

The owner is not technical. Explain in plain language, lead with the answer, keep
it short. Do not ask trivial questions that do not need their input.

## State at handoff — all FACT

| | |
|---|---|
| Working branch | `bootstrap/pre-upstream` |
| Accepted ADRs | **21** (ADR-0017 … ADR-0021 accepted 2026-07-31) |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`, generator idempotent |
| Runtime | `NOT_ASSESSED` — nothing runs |
| Readiness | Neither tier declared |
| Owner decisions | 20 rows; six have accepted ADRs. `ADR-0017` is now **implemented** (2026-07-31): status may be `ACCEPTED`, `owner_decision_ref` is a `TypedArtifactRefV1` paired with `owner_decision_digest`, `unresolved_owner_decision_count` is **derived**, and `architecture/records/owner-decisions/` exists and is empty. The count still reads 20 because nothing is resolved — correctly, not because the machinery is missing |
| Kernel | R&D tracer, branch `feature/kernel-tracer`. Audited by three models; §8.3 gate, journal replay and real crash tests added. 82 tests pass |
| Records freshness | Gate green: 21 ADRs, 10 RFCs, no stale claims (`ADR-0020`) |
| Type checker | `pyrefly` 1.1.1 pinned (`ADR-0018` v1.2.0); **243 strict errors** — measured by `cd scripts/architecture && uv run --group typecheck pyrefly check`. **The working directory is load-bearing:** from the repo root with `--project`, pyrefly loses `preset = "strict"` and reports 6. Both exit non-zero. `ADR-0018`'s gate has **no CI step** at `HEAD` |
| Unconstrained schema arrays | 329 → **173**, each marked `UNDECIDED` and counted by the validator |
| CI | Green (`30619852943`). **Four parallel checks plus an aggregating gate**, not one sequential job: `drift`, `freshness`, `validate`, `concurrency_regression`, then `all contract checks`. Wall clock 8m00s → 6m17–6m41s (17–22%), at **+62% billable minutes** (8 → 13; GitHub rounds each job up) |
| Branch protection | **`bootstrap/pre-upstream` PROTECTED** — all five checks required, force-push and deletion blocked. `develop` protected against force-push/deletion. `main` protected but legacy. `enforce_admins: false`, so the owner still pushes freely; the gate binds AI workers, not the owner |

## Corrections to the previous handoff — read before acting

The handoff you are replacing contained a **false** instruction. Both corrections
are FACT.

1. **Agent stalls were NOT provider concurrency.** The previous handoff said three
   concurrent runs on one provider produce zero output for 24–52 minutes, and told
   you to serialize. Measured today: the causes were (a) **unclosed stdin** —
   identical model, brief and provider gave 0 bytes in 2h47m with stdin open and
   3,275 bytes in 90 seconds with `< /dev/null`; and (b) an **exhausted
   opencode-go quota**. Cross-provider parallelism works fine. Always pass
   `< /dev/null` and a hard `timeout`.
2. **Check accumulated CPU time, not output size,** to tell working from hung. A
   real hang shows `00:00:00` CPU over hours; a working model can legitimately go
   quiet. The previous advice to watch file size produced a false alarm on a model
   that was simply slow.

## Immediate next steps, in order

**1. Clear the 243 strict type errors.** `LANG-TYPECHECK-001` cannot pass until
they are zero. `ADR-0018` `TYPECHECK-DEBT-001` forbids a baseline or any rule
demotion.

**Do not attempt this in bulk.** It was tried and reverted. A 42-annotation batch
reached 159 and looked safe; three further automated rounds were not
behaviour-neutral — `implicit-any` stuck at 40 while `bad-assignment` rose 3 → 18,
because annotating a variable later reassigned an incompatible value changes what
type-checks, and the generated tree changed.

The false confidence came from an **invalid proof**: neutrality was "shown" by
regenerating with the *same* script and comparing the tree to itself, which only
demonstrates idempotence. The valid check is to generate one tree with the OLD
script and one with the NEW, and diff those. Work one owner at a time — 33 owners,
largest are `build_worker_runtime_semantic_world` (28) and
`build_test_definition_profile` (26).

**2. ~~Implement `ADR-0017`~~ — DONE 2026-07-31.** The machinery exists and is
gated. `status` may be `ACCEPTED`; `owner_decision_ref` is a `TypedArtifactRefV1`
paired with `owner_decision_digest`; `unresolved_owner_decision_count` is
**derived** (`OWNER-RESOLVE-005`, the only deletion accepted);
`architecture/records/owner-decisions/` exists and is **empty, so it grants
nothing**; `runtime_validation_status` becomes `NOT_ASSESSED` on resolution,
never `PASS`. Eleven acceptance cases pass
(`scripts/architecture/test_adr17_owner_resolution.py`), including the
`OWNER-RESOLVE-007` case proving a bare-string reference still fails closed.

The feared cascade **did not occur**, because the population starts empty. The
generated diff is exactly: `owner_decision_digest` added to 20 rows, and those
20 rows' own digests moved. 98 rows in, 98 out; no other value changed. The
`ADR-0013` cascade belongs to an *actual resolution*, not to the machinery — see
`architecture/records/owner-decisions/README.md`.

**What remains for a real resolution:** mint a `HumanDecisionV1`, then write the
typed reference into `ADR-0013`'s YAML and accept the digest cascade there.
**No such record exists, and nothing in this repository can mint one** — the only
construction of `authentication_context_id`/`presentation_challenge_digest` is a
synthetic fixture at `validate_contracts.py:8436`. That is the true blocker on
`RFC-0010`.

**3. Decide the 121 undecided array element types.** 173 arrays remain
unconstrained across 121 field names (`limitations`, `scope`, `conflicts`,
`unknowns`, …). The owner chose: derive where the name determines it, never guess
the rest. These need per-field decisions, in batches.

**4. `RFC-0002`, `RFC-0003`, `RFC-0007`, `RFC-0009` await owner decision.**
`RFC-0007` matters most: `validation-report.json` content is
environment-dependent — this machine emits `practice_corpus_validation: PASS`
while CI emits `NOT_ASSESSED_LOCAL_ONLY`. The committed file should carry the
form a clean checkout can prove. Left untouched deliberately.

## What CI enforces, and what it does not — read before trusting a green tick

Established 2026-07-31 by two independent adversarial audits (HY3 and Grok-4.5,
each with terminal access in an isolated worktree, briefed to assume the work
was wrong). Both found real defects. All **FACT** unless marked.

**Binding:** `bootstrap/pre-upstream` requires all five checks. Force-push and
deletion are blocked there and on `develop`.

**`develop` is protected for a non-obvious reason.** Commit `0533e1eaf` is
reachable from **no other ref**, and both `drift` and `validate` read git
objects from it (`generate_contracts.py:4872, :4973, :5129`;
`validate_contracts.py:26620`). Deleting or force-pushing `develop` breaks CI
outright. This is why every job except `freshness` needs `fetch-depth: 0`.

**Not closed, by design or by pending decision:**

- **A required check is matched by NAME**, and the workflow defining that name
  is an editable repository file. A branch carrying a workflow whose
  `all contract checks` job is `exit 0` satisfies the requirement having proven
  nothing — a `pull_request` run executes the HEAD's workflow. Requiring the
  four leaf names as well as the aggregate raises the cost; it does not close
  it. GitHub's ruleset rule of type `workflows` pins a workflow by
  `repository_id + path + sha` and would close it. **Not enabled — owner
  decision.**
- **`app_id` proves nothing.** The requirement carries `app_id 15368`, which is
  the generic GitHub Actions app shared by every workflow in every repository —
  measured: four unrelated workflows on `9be6bd944` all report `app=15368`. An
  earlier claim that it prevented forgery was **false**.
- **`enforce_admins: false`** by owner decision, so an admin pushes past a red
  gate. Deliberate: it keeps an emergency path for a solo owner.
- **The merge commit is never gate-checked** — protection evaluates the PR head
  SHA, and `allow_merge_commit: true` creates a new SHA on the target.
- **No required reviews and no CODEOWNERS**, so any write-access actor
  self-merges.
- **A job in the workflow but absent from the gate's `needs:`** is invisible to
  the gate. Documented in the workflow; unavoidable with this pattern.
- **`validation-report.json` drift is invisible.** The validator writes this
  tracked file (`validate_contracts.py:31793`) and no job diffs afterwards. It
  cannot simply be added: a runner can never hold the gitignored practice
  corpus, so CI necessarily emits `NOT_ASSESSED_LOCAL_ONLY` while the committed
  file records `PASS`. **This is exactly what `RFC-0007` asks the owner to
  decide.**

**`main` is legacy.** Owner decision 2026-07-31: `bootstrap/pre-upstream` is the
real branch. The two share no usable ancestry — `main` holds **18,258 commits**
this branch does not, and `main` **fails its own validation**
(`PRACTICE_CORPUS_INDEX_PATH_SET` → `FAIL`), because the fix landed here and
never reached it. Do not try to merge them; it is a repository restructure, not
a merge.

## Open threads

- **Monetization**, still unfinished. New relevant FACT: FedRAMP requires
  machine-readable authorization packages by **2026-09-30**, and NIST OSCAL is the
  format. Ranex produces exactly that class of artifact. `LICENSE-RANEX.md` is
  personal-use, all rights reserved, so commercial optionality is preserved.
  ADR-0011 forecloses the Hermes inference-margin model.
- **Copyrighted PDFs remain reachable** in the git object database via
  `refs/codex/`. **Re-verified 2026-07-31: 15 refs still present**, two of which
  carry **11 PDF blobs** (`Clean.Code…pdf`, `Code.Complete…pdf` and others under
  `docs/research/`). The `origin` remote
  (`https://github.com/anthonykewl20/ranex.git`) is a **PUBLIC** GitHub
  repository. A normal `git push <remote> <branch>` does not carry them;
  **`git push --all` or `--mirror` would publish them**. Never use those flags on
  this repository. Unresolved by owner choice. **FACT**.

  Count them with `git for-each-ref 'refs/codex/**'` — **not** `refs/codex/*`,
  which matches one path level, returns zero, and reads as an all-clear. That
  exact mistake was made and caught on 2026-07-31.
- **`~/.codex/logs_2.sqlite` is 3,792,609,280 bytes (3.79 GB)** as of 2026-07-31
  — **FACT**, re-measured. The "88% dead space" figure and the claim that a
  compaction job is armed but has never fired remain **UNVERIFIED** inherited
  claims; only the file size was re-checked.

### Closed since the last handoff — do not re-report as open

- **Dependency licences are registered.** `legal/licensing-manifest.json`
  `dependencies.entries` carries all five: `jsonschema` (MIT), `PyYAML` (MIT),
  `rfc8785` (Apache-2.0), `pyrefly` (MIT), `uv` (MIT OR Apache-2.0). The previous
  handoff recorded zero entries. **FACT**, verified by parsing the manifest.
- **`uv` is declared.** `ADR-0019` selects it, `ACCEPTED`. The previous handoff
  listed it as an undeclared load-bearing tool choice. **FACT**.

## Operational notes — model routing

Verified prices, OpenRouter, 2026-07-30. **FACT.**

| Model | In | Out | Role |
|---|---|---|---|
| `tencent/hy3` (variant high) | $0.13/M | $0.53/M | **Workhorse.** Exhaustive reads, adversarial audits, full-corpus sweeps |
| `tencent/hy3-preview` | $0.06/M | $0.21/M | Cheaper still; untested here |
| `xiaomi/mimo-v2.5-pro` | $0.43/M | $0.87/M | Systematic full-row passes; verifies claims structurally |
| `x-ai/grok-4.5` | $2.00/M | $6.00/M | **Final validator and tiebreaker only** — owner decision |
| Codex `gpt-5.6-sol` | **free** | **free** | **Default for heavy research.** Owner has an x20 Pro account. Fastest measured, ~27 KB/min |

- **Grok earns the validator role on evidence:** it found §8.3 that four other
  readers missed, and it **executed** an exploit (forged the SQLite snapshot, then
  called `load()`) rather than reasoning about one. It did this at **default**
  effort while HY3 ran at `high`.
- **Cost is dominated by what a model READS, not by output length or reasoning
  effort.** FACT: a 36 KB kernel audit cost $0.0868; four tiny single-file probes
  across all four effort levels cost $0.0798 combined; one whole-repo-plus-web
  sweep cost **$1.88**. Constrain the brief's reading scope to control cost.
  Reasoning effort is close to free on narrow questions — all four variants
  answered a targeted question correctly.
- **GLM 5.2 — verdict CONFOUNDED, not established.** It measured ~1.4 KB/min
  against Codex's ~27 KB/min, but it ran on opencode-go while that gateway's quota
  was exhausted. Out of the roster by owner decision; the slowness measurement is
  not trustworthy evidence about the model.
- **opencode-go quota is exhausted.** `hy3` and `grok-4.5` are listed there but
  will not respond. Use OpenRouter. **Probe any model with a one-token prompt
  before dispatching real work** — a model appearing in a list does not mean it
  answers.
- **Costs are queryable** at the provider's credits endpoint. Expect settlement lag
  of more than 20 seconds, so do not attribute per-run costs from a short window.
  Check the remaining balance before dispatching paid work.
- **Codex is drivable directly:** `codex exec --cd <dir> "<prompt>" < /dev/null`.
  Config is `danger-full-access` with `approval_policy = never`. Use an isolated
  worktree for anything that writes.

## Prompt discipline that produced results

- **State findings as attacks, not confirmations.** "Confirm X" returns the
  framing back as a finding.
- **Never put your own assumption in the brief.** Of three hypotheses withheld
  today, one was independently found, one was found in a more serious form, and
  one was not surfaced — which is itself information about that hypothesis.
- **Require `path:line` for every claim,** and verify before relaying. Today: one
  agent claim verified true, one overstated, one file-list grep that turned out to
  be a false positive matching `429` inside a SHA-256 hash. Relaying any unchecked
  would have misled the owner.
- **Require reporting of inferences.** An unreported inference is a defect
  regardless of correctness.
- **Ask a sweep what to DELETE**, not only what to add. That instruction is what
  demolished RFC-0003's first draft.

## Assistant errors, 2026-07-31 — do not repeat

1. **Proved a change safe with an invalid test.** Regenerated with the *same*
   script and compared the tree to itself, then declared 42 annotations
   behaviour-neutral. That shows idempotence, nothing more. Compare OLD-script
   output against NEW-script output.
2. **Rewrote a legal record with `sort_keys`,** churning 4,126 lines of
   `licensing-manifest.json` to add five entries. Reverted; redone surgically as
   50 insertions. Never reformat a file you are only adding to.
3. **Built a gate that under-reported.** The freshness check's header parser
   excluded backticks, so the promoted-RFC check found zero of five. Caught only
   by comparing against an independent count. A gate that silently passes is
   worse than no gate.
4. **Ran a research agent with `--cd` on the live repository** rather than an
   isolated worktree, contrary to this handoff's own instruction.
5. **Wrote a stale figure into an accepted ADR.** `ADR-0018` cited 256 errors
   measured against an uncommitted config; corrected in v1.1.0 to the figure the
   committed config produces. **v1.1.0's replacement figure was also wrong** —
   256 was measured mid-change, before the schema-array typing landed in the same
   commit. Corrected to **245** in v1.2.0, this time proven by
   `pyrefly check --output-format json` at a named commit. Two corrections of the
   same number, both because it was recorded without a reproducing command beside
   it.
6. **Counted with a regex that matched a code snippet.** A first per-rule
   breakdown grepped for lines ending `[rule-name]` and scored 246 — one of the
   "rules" was the source fragment `[value]` printed inside a quoted line of
   `generate_contracts.py`. Same class as the `429`-inside-a-SHA false positive.
   Never derive a count from prose output when the tool emits JSON.
7. **Declared a copyright exposure resolved on a bad glob.**
   `git for-each-ref 'refs/codex/*'` returned 0 and was briefly read as the refs
   being gone; `refs/codex/**` returns 15. A single-level glob against a
   deep ref namespace silently reports absence. The handoff's own corollary —
   a negative search result is evidence about the search — applies to glob
   patterns, not only to grep.
8. **Shipped a fix for audit findings without re-auditing the fix.** HY3 audited
   version 1 of the CI restructure; ten changes were made in response and
   version 2 was committed **unreviewed**, and Grok — the designated final gate
   — never saw it. The owner caught this, not self-review. The second audit then
   found that one of those "fixes" had introduced a **fail-open gate** (below).
   Fixing findings is not the end of the loop; re-auditing the fix is.
9. **Introduced a fail-open gate while following a documentation
   recommendation.** The aggregating gate was changed from `always()` to
   `if: !cancelled()`, citing GitHub's general advice. For an aggregating gate
   that is the wrong reading: *"Successful check statuses are success, skipped,
   and neutral"* and *"A job that is skipped will report its status as
   'Success'... even if it is a required check."* With `cancel-in-progress:
   true`, superseded runs are cancelled routinely, so the gate was **skipped,
   reported as success, and would have allowed a merge having proven nothing.**
   Reverted to `always()`, which fails closed. A docs recommendation is scoped
   to the case it was written for.
10. **Verified a config change by reading back my own write.** Branch protection
    was applied and then "verified" with a GET of the same endpoint. That
    confirms the API stored what was sent; it says nothing about whether what
    was sent is correct. It is not independent verification.
11. **Used `pgrep -f` to check whether my own background job was alive.** It
    matched *other Claude sessions'* processes on the same machine and would
    have reported my job running after it died. Match on something unique to
    the invocation — the `--dir` path — not on the program name.

### Model-routing evidence from this session

**Give both models a terminal.** Owner instruction, 2026-07-31: a read-only
brief wastes them. Run them through `opencode run --model <provider/model>
--dir <isolated worktree>` with `< /dev/null` and a hard `timeout`. With tools,
HY3 installed `actionlint` itself, pulled per-step timings from the Actions
API, executed the scripts, and **demonstrated** the drift-gate hole rather than
theorising it. A bare chat-completions call also truncates: HY3 is a reasoning
model and spent an entire 8,000-token budget on reasoning, returning empty.

**What the two audits caught that self-review did not** (2026-07-31):
`git diff --quiet` in the drift gate ignores **untracked** files, so a
regeneration emitting a brand-new output file reported CLEAN — demonstrated,
and a defect present since the original workflow. The Python floor assertion
covered 1 job of 4 after the split. Three published cost figures were
predictions stated as measurements, all wrong (+62% not ~50% billable; four
jobs check out, not three; wall clock a 17–22% range, not 21%).

**HY3 retracted its own finding, unprompted.** It drafted a claim that the
`validation-report.json` comment was false, then `git show HEAD:` proved it had
been misled by the validator's own side-effect write, and it reported the
retraction. That is the behaviour to select for.

**Grok-4.5 cannot be trusted to count.** Asked to derive the per-rule breakdown
from the 84 KB pyrefly log, it returned totals wrong on **6 of 11** rules
(`implicit-any` 118 vs 122, `missing-attribute` 48 vs 45, `bad-argument-type`
42 vs 40, `unsupported-operation` 15 vs 18, `bad-index` 8 vs 9, `bad-assignment`
4 vs 3). Cost $0.047.

Two things it did right, and they are why it stays the final gate: it reported
that its own table summed to 243 rather than adjusting a number to reach a
total, and it refused to accept 256 on the evidence offered. **Use it to
adjudicate reasoning and to attack a claim — never to tally.** Anything
countable must come from the tool's machine-readable output.

The common thread, again: **stating a checkable claim without checking it** — and
this time, checking it the wrong way, which is worse because it feels rigorous.

## Assistant errors, earlier sessions — do not repeat

Recorded because the pattern matters more than the individual mistakes. All were
caught by the owner or by another model, never by self-review.

1. Asserted from recall that the tooling dependencies were C-backed. **False** —
   `jsonschema` and `rfc8785` contain no compiled extensions.
2. Wrote "each dependency carries a licensing-manifest entry" into an **accepted
   ADR**. **False** — zero entries exist. Fixed in v1.1.0.
3. Diagnosed stalls as provider concurrency and serialized the whole queue on that
   basis, after having already disproved it.
4. Designed four mechanisms in RFC-0003 before searching; three already existed as
   maintained tools.
5. Queued two jobs on a model without probing it; the model never answered.
6. Ran a grep, reported five files as containing rate-limit evidence, and nearly
   confirmed the owner's hypothesis on a match that was `429` inside a hash.

The common thread: **stating a checkable claim without checking it.**

## Standing constraint

`IMPLEMENTATION_START_READY` is not declared. Product code is authorised only as
an R&D tracer in an isolated worktree, claiming no authority — the precedent is
`reviews/2026-07-28-gate-controller-mvp-user-level-audit.md`. Do not relax a check
to make code pass; if code cannot satisfy a provision, that is a finding.
