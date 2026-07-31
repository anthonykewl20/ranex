# Slice 1 readiness assessment

**Date:** 2026-07-31 · **HEAD:** `f2c04c167` · **Branch:** `bootstrap/pre-upstream`

The critical decision this audit was commissioned to make. Answers the five
questions in the brief, in order.

Every claim is labelled. **FACT** = measured here by the command shown.
**INFERENCE** = concluded, not directly proven. Independent verification status
is recorded in §7.

---

## Verdict in one paragraph

**Slice 1 can continue on the current codebase, and the foundation question that
prompted this pause turned out not to be the blocking one.** The working tree
contains **zero** Hermes runtime code, the Hermes baseline is **not an ancestor**
of this lineage, and Slice 1's complete dependency path is the Python standard
library plus PyYAML plus git. **No extraction, adaptation, or removal is required
before Slice 1 resumes — zero commits.** What the audit did find is different in
kind: **six gaps between Slice 1's own written requirements and its current
implementation** — including two mitigations this document originally credited
that turn out not to be wired. The `ADR-0012` governance block is **already
lifted for this slice** by `BOOTSTRAP-AUTH-001` (`ACTIVE`), so building is
authorized; closing is not.

---

## 1. Can Slice 1 continue safely on the current codebase?

**Yes — the foundation is safe. Two conditions are unmet, and neither is a
foundation problem.**

### What makes it safe — FACT

| Property | Measurement |
|---|---|
| Hermes runtime code in tree | **0 files** across all 12 subsystem directories |
| Hermes baseline in ancestry | **Not an ancestor** — `git merge-base --is-ancestor 0533e1ea… HEAD` → exit `1` |
| Lineage | Root `4ee007fcbe…`, **38 commits**, unrelated to Hermes |
| Slice 1 third-party runtime deps | **1** — `PyYAML>=6.0.2,<7` |
| Hermes imports in `src/ranex/` | **0** |
| Test suite | **36 passed in 0.18 s** |
| Product source under strict pyrefly | **0 errors** (root `pyrefly.toml`, `project-includes = ["src","tests"]`) |
| Validator baseline | **243 errors**, per-rule breakdown sums to 243 — unchanged, so criterion 5 has a real baseline |
| Contract validation | `PASS`, scope `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |

### The core mechanism already executes — FACT

Run from the repository root, 2026-07-31:

```console
$ ranex gate evaluate HEAD --gate-catalog governance/gates.yaml \
    --evidence governance/evidence.json --approver owner
PASS  gate=landing  subject=sha256:9edd77be…                    exit 0

# BC-2 absence blocks
$ … --evidence <empty>
FAIL  gate=landing  rule=TESTS_EXECUTED
      no evidence for required claim: contracts-validated, tests-executed   exit 1

# BC-6 self-approval refused
$ … --approver worker
FAIL  self-approval refused: worker produced evidence and approved it       exit 1

# BC-4 determinism
$ cmp r1.txt r2.txt  →  IDENTICAL
```

Three of seven behavioural contracts are demonstrated **at the CLI boundary**,
not merely unit-tested. The product thesis — that a rule compiled into code can
refuse a change on evidence alone, with no model consulted — **works**.

### The two conditions that are unmet

**Condition A — already lifted for this slice, by owner authorization.**
`ADR-0012:72` forbids product capability before `IMPLEMENTATION_START_READY`,
and `RFC-0010` is not promoted because `SLICE-LANE-011` requires an
authenticated `HumanDecisionV1` that **nothing in this repository can mint** —
the only construction of `authentication_context_id` /
`presentation_challenge_digest` is a synthetic fixture in
`validate_contracts.py`.

**`BOOTSTRAP-AUTH-001` is `ACTIVE`**
(`architecture/records/bootstrap-authorizations/BOOTSTRAP-AUTH-001.md`, issued
by the human owner in session 2026-07-31). It treats the missing issuance
mechanism as a **temporary bootstrap authorization rather than a reason to
block**, on five limits — applies only to the first walking skeleton ·
authorizes the defined slice only · authorizes no unrelated product work ·
**expires when the slice is completed *and verified*** · the permanent issuance
mechanism is a required prerequisite before the second slice — and two
prohibitions: **do not weaken any fail-closed guarantee; do not bypass
governance checks.**

It is explicitly **not** a `HumanDecisionV1` — no `principal_id`, no
`authentication_context_id`, no nonce — and must never be counted as one. It is
a recorded, scoped, expiring exception to a bootstrap deadlock.

**Correction to an earlier draft of this document,** which said the block was
unresolved and untouched by this audit. That was true of the *corpus mechanism*
and false of the *authorization*. **Building is authorized. Closing is not.**

**Condition B — Slice 1 is working but not complete.** Six gaps against its own
written requirements, in §4. Note that limit 4 above makes this the operative
condition: the authorization expires on completion **and verification**, so the
gaps in §4 are what currently keep the slice open.

### Note on §5's premise

Question 5 of the brief asks what cleanup must be deferred. The honest answer is
that the premise of a "Hermes-to-Ranex extraction" did not survive measurement.
There is no inherited codebase under Slice 1 to extract from. That is the single
most consequential finding here, and it makes the readiness question much easier
than expected.

---

## 2. Which inherited Hermes components are required for Slice 1?

**None. Not one.**

Slice 1's complete dependency path, **FACT**
(`grep -rh '^import \|^from ' src/ranex` + `pyproject.toml`):

```
stdlib       argparse · dataclasses · enum · hashlib · json · pathlib
             re · sqlite3 · subprocess · sys · typing · uuid
third-party  yaml (PyYAML >=6.0.2,<7)
external     git, via one fixed-argv subprocess call (`git rev-parse <ref>^{tree}`)
first-party  ranex.*   (1,050 LOC)
```

Every capability Slice 1 needs is Ranex-original and already present:

| Need | Provided by | LOC |
|---|---|---:|
| Deterministic digest | `foundation/canonical.py` (RFC 8785 + SHA-256) | 26 |
| Verdict evaluation | `governed_execution/domain/verdict.py` | 207 |
| Append-only journal | `…/sqlite/journal.py`, hash-chained | 94 |
| Gate catalog loading | `…/yaml/slice_gate_loader.py` | 99 |
| Repository confinement | `cli/confinement.py` | 44 ⚠ **present but NOT wired — see G6** |
| Operator surface | `cli/main.py`, one subcommand | — |

**Deterministic validation — the one capability the product cannot exist without
— has no Hermes counterpart at all.** Searched `agent/`, `hermes_cli/`,
`tools/`, `gateway/` for canonicalisation, RFC 8785, content-addressed subject
binding and reproducible verdicts: none found. It could never have been
inherited. It exists only because it was written here.

---

## 3. Which inherited components would contaminate or distort Slice 1?

None can contaminate it today, because none is present. The list below is
therefore a **do-not-import** list, ordered by how plausible the mistake is.

### Tier 1 — would silently defeat the slice

**`agent/verification_evidence.py` — a passive evidence ledger.** Its own
docstring: *"deliberately passive: it never decides to run a suite, **never
blocks completion**."* Ranex requires the exact negation — `BC-2`, absence
blocks, *"Never a default, never a skip."*

The two share a name, a storage engine (SQLite), and a record shape (command,
exit code, output summary). A future agent looking for "the evidence ledger we
already have" would find something that imports cleanly, passes review, and
**cannot refuse anything**. Slice 1 would not break loudly. It would simply
always pass. **This is the single most dangerous artifact in the Hermes corpus
for this project.**

**Context and memory compression** (`context_compressor.py`,
`conversation_compression.py`, `trajectory_compressor.py`,
`memory_manager.py`, `learning_graph.py`). Lossy summarisation keyed on
accumulated history is a hidden input by construction, and `BC-4` requires
byte-identical output from identical inputs. **INFERENCE** — structural, not
measured against running Hermes.

### Tier 2 — would reopen a closed trust boundary

**In-process plugins** (`plugins/`, 190 files). `verify_hooks.py` resolves its
directive through `hermes_cli.plugins.get_pre_verify_continue_message` — a plugin
can steer the verification loop. **In-process extension of a gate is the gate's
own bypass.** `DEC-RANEX-019` already requires external extensions to be
out-of-process, capability-scoped, and *outside authority*.

**Ambient layered configuration** (`hermes_cli/config.py`,
`fallback_config.py`). Slice 1 takes only explicit CLI arguments. An ambient
input to a verdict breaks `BC-4` across machines. `ADR-0011` already forbids the
influence path: ambient user configuration "cannot broaden the effective set."
**This is the highest re-import risk on the list** — configuration arrives one
individually-defensible convenience default at a time.

**Model-provider abstraction and the agent loop.** Any of it makes `BC-5`
("removing model access changes no verdict") expensive to prove instead of free.

### Tier 3 — adverse to the slice's confinement property

**Remote-control surfaces** (`tui_gateway/`, `acp_adapter/`, `web/`,
`dashboard_auth/`, `api_server.py`) and the **28-platform gateway**. Each is an
authority path into the agent from outside the repository; `SLICE-LANE-007`
requires the opposite and enforces it with three tests.

**Model-initiated delegation** (`delegate_tool.py`, `moa_loop.py`). `ADR-0011`
already inverts every load-bearing property: the graph is compiled *before*
dispatch and model decomposition is an *untrusted proposal*.

### Contract-level residue — cannot contaminate a verdict

The 23 Hermes-referencing files under `architecture/contracts/` are **inert data
on no import path**. **65** `HERMES-PROMOTION` rows, **20** owner decisions, **13**
research-only, `catalog_status: DEFINITION_ONLY`. They block at `RELEASE` and
`PRODUCTION_READY`, stages this project has not reached. They cannot affect a
Slice 1 verdict. **FACT**, from the catalog's own counters.

---

## 4. What is the minimum required before Slice 1 resumes?

### Extraction, adaptation, removal: **zero commits**

There is nothing to extract (no inherited code), nothing to adapt (no inherited
interface is used), and nothing to remove (no inherited file is present).
Removal reasoning is in [`removal-sequence.md`](removal-sequence.md); the
retention triggers there are all future-dated or event-driven, and **none
precedes Slice 1**.

Actively recommended **against**: hand-editing `architecture/contracts/`. Those
47 files are generator output and the `drift` job compares them; a hand edit
either fails `drift` or is silently reverted on the next regeneration.

### What genuinely must be closed — Slice 1's own completion gaps

These are defects in Slice 1, not contamination from Hermes. Each is measured.

| # | Gap | Requirement it misses | Evidence |
|---|---|---|---|
| **G1** | **The journal is opt-in.** `--journal` defaults to `None`, so by default **no record is written**. Four evaluations were executed during this audit and the trail records none. | Walking skeleton §12: *"Each evaluation appends one record."* | `cli/main.py:69,115`; journal holds 2 pre-existing rows, mtime `17:42:37`, hours before those runs |
| **G2** | **`subject_lane` is absent from the record.** | §13: *"every record carries `subject_lane: PRE_READINESS_PRODUCT_SLICE`"*, and quarantine rule `QUARANTINE-001` depends on it | Record keys are exactly `approver_id, considered, failing_rule, gate_id, missing_claims, reason, subject_digest, verdict` |
| **G3** | **The policy is not digest-bound.** The record binds the subject but not the rules that judged it. Edit `gates.yaml` and the same subject yields a different verdict, with the journal showing `gate_id: landing` in both cases. | The reproducible-verdict claim. `BC-4` holds for "identical inputs" — which silently includes an unbound file | No catalog/gate/policy digest in the record or in `verdict.py` |
| **G4** | **`governance/` is entirely untracked.** The gate catalog and evidence defining what "landing" means are outside version control. | Implied by every integrity property the slice claims | `git ls-files governance/` → **0**; `git status --porcelain governance/` → `?? governance/` |

**G3 and G4 compound.** Together they mean the rules can be changed invisibly to
git, and the audit record cannot tell you which rules applied. For a product
whose entire premise is *"the verdict is reproducible and the reason is
recorded,"* that is the gap that matters most.

### G5 — `ADR-0021` and `RFC-0010` are not committed

**FACT**, measured 2026-07-31 and independently surfaced by the Codex Luna
sweep, which reported "20 ADRs, 9 RFCs" where this repository's own tooling
reports 21 and 10:

```console
$ git ls-tree -r HEAD --name-only -- docs/architecture/decisions | grep -c 'ADR-'
20
$ ls docs/architecture/decisions/ADR-*.md | wc -l
21
$ git status --porcelain docs/architecture/decisions/ docs/architecture/rfcs/
?? docs/architecture/decisions/ADR-0021-limit-adr-0010-to-inherited-lineage.md
?? docs/architecture/rfcs/RFC-0010-authorize-bounded-vertical-product-slices.md
```

The freshness gate agrees, and the split is the proof: run in the repository it
reports `21 ADRs, 10 RFCs`; run in a clean checkout of `HEAD` it reports
**`20 ADRs, 9 RFCs`**.

**Why this matters more than a missing commit.** `ADR-0021` is `ACCEPTED` and is
the decision that narrows `ADR-0010` to inherited lineage — the finding this
entire audit builds on and extends. `RFC-0010` is the authorisation path for
Slice 1 itself. **Both currently exist only in one working tree, on one
machine, unprotected by the branch rules and invisible to CI.** An `ACCEPTED`
decision that no clean checkout can see is not yet a decision anyone else can
rely on.

This is also a live example of the risk that `governance/` being untracked
(G4) creates: the repository's own reported state depends on which working
tree you ask.

**Cheapest fix in this list — commit them.** No code changes, and it should
precede the other four.

### G6 — repository confinement is dead code, and this document credited it twice

**FACT**, measured 2026-07-31:

```console
$ grep -rn "confinement" src/ tests/ --include=*.py | grep -v "^src/ranex/cli/confinement.py"
tests/security/test_repository_confinement.py:13:from ranex.cli.confinement import resolve_within_repository
```

**`src/ranex/cli/main.py` never imports it.** The module is exercised only by
its own test. `SLICE-LANE-007` — "governs only this repository" — is therefore
**unenforced at the CLI boundary**, and the three failure-mode tests prove a
helper that nothing calls. `docs/architecture/reviews/2026-07-31-slice-01-evidence.md`
records the consequence directly: *"a second-repository evaluation actually
passed."*

**This corrects two claims in this audit.** Earlier drafts cited
`cli/confinement.py` as the *mitigation* for filesystem-path risk in
[`dependency-risk-map.md`](dependency-risk-map.md) §2 row 5, and as an active
boundary in [`ranex-foundation-boundary.md`](ranex-foundation-boundary.md).
Both were wrong: the code exists, the tests pass, and the property is not in
force. A passing test suite was mistaken for a wired feature.

**Related precision fix.** Earlier drafts said the catalog loader "refuses
duplicate rule IDs." What it refuses is **duplicate YAML mapping keys**
(`slice_gate_loader.py:40-56`, a `BaseResolver.DEFAULT_MAPPING_TAG` override).
Duplicate `rule_id` *values* across separate list entries are a different check,
and the slice-01 evidence record reports them as **accepted**. Not re-tested
here — **INFERENCE** from that record plus the loader source.

**G6 is the most serious gap in this list**, because unlike G1–G5 it is a
security property the slice claims to have and does not.

All four are small and inside the slice's existing scope — they are fields and a
default, not new capability. **INFERENCE:** closing them is well under the
1,000-line budget (`SLICE-LANE-001`); current product source is 1,050 lines
total.

### Sequenced minimum

1. **Nothing to remove.** Proceed.
2. **Close G1–G6** as part of finishing Slice 1, under `ADR-0008` TDD — failing
   test first, as the slice requires.
3. **Track `governance/`** (G4) — the cheapest of the four and a precondition for
   G3 being meaningful.
4. **Then** acceptance criterion 2: block a **real** change, with output
   recorded. *A check only ever observed passing is not evidence* — and the
   PASS/FAIL pair demonstrated here was constructed by the audit, not encountered
   in anger.
5. **Condition A (`ADR-0012` / `RFC-0010`) remains open** and is the owner's to
   resolve. It gates *landing* the slice, not *building* it.

---

## 5. Which cleanup must be deferred until a later slice proves it necessary?

**All of it.** Full reasoning and triggers in
[`removal-sequence.md`](removal-sequence.md).

| Deferred item | Trigger | May never fire? |
|---|---|---|
| `ADR-0010` 2,444-path test projection | ADR expiry **2026-10-31T23:59:59Z** | No — dated |
| 65 `HERMES-PROMOTION` rows + schema | Per row, as implemented or superseded | No |
| 20 `HERMES-OWNER-DECISION` rows | Owner resolution via `ADR-0017` machinery | No |
| Hermes git refs + filesystem archive | Last promotion row closes | No |
| Hermes provenance tags in contracts (~2,400 matches) | — | **Yes — permanently. Provenance stays true.** |
| `ADR-0006` `DEC-RANEX-008` stale strangler premise | A slice actually collides with it | **Yes** |
| Import-surface CI assertion | A second dependency or an HTTP client appears | Possibly |
| `FF-DECOMM-001` execution | First release artifact exists | No |

**Deliberately not done, and why.** No new ADR is proposed. The one stale
architectural premise found — `DEC-RANEX-008`'s "strangler migration inside the
attributed fork," which presumes a legacy system in the tree that does not exist
— is recorded in [`hermes-retention-matrix.md`](hermes-retention-matrix.md) ADR
review ⚠ 2 and left un-superseded. Writing a decision record for a premise
nothing currently depends on would be the speculative-ADR and BDUF behaviour the
brief forbids. If a slice ever collides with it, supersede on the `ADR-0021`
pattern: narrow the scope on executed provenance evidence, without rewriting the
accepted decision.

---

## 6. Hermes monetization — owner-requested

**Nothing to remove. Already decided out, already contracted, trivially
satisfied — and never actually verified.**

- **Decided:** `DEC-RANEX-026` (`ADR-0006:234`, `ACCEPTED`) — Hermes/Nous is
  "provenance, compatibility, and reference only: no live inference,
  parent-agent model loop, Portal/model route, credential/entitlement, billing,
  credits, subscription, managed tool pool, purchase, promotion, or fallback."
  Rejected alternatives are the telling part: *"hide commercial UI"* and
  *"retain dormant commercial runtime"*. The decision is removal, not
  concealment.
- **Contracted:** **21 of 98** catalog entries carry de-commercialization
  content; **18 carry `failure_outcome: BLOCK`**. Fitness function
  `FF-DECOMM-001` (`ADR-0011:475`).
- **Satisfied:** every artifact those rows name — wheel, container, SBOM, npm
  bundle, `providers.nous`, `/topup`, billing RPCs, Portal OAuth scopes — does
  not exist here. There is no Hermes commercial code because there is no Hermes
  code.
- **But never run:** `catalog_status: DEFINITION_ONLY`. The checks bite at
  `RELEASE` and `PRODUCTION_READY`. The correct statement is *"Ranex carries no
  Hermes monetization surface"* — **not** *"`FF-DECOMM-001` passed."* It has
  never executed.

### Independent full-corpus sweep — Codex Luna, 2026-07-31

An independent sweep across `docs/`, `architecture/contracts/`, `schemas/` and
`legal/` classified **6,083 raw matching lines across 261 files** for 20+
commercial terms. Classified, not counted:

| Class | Lines | Meaning |
|---|---:|---|
| (a) Hermes commercial concept surviving as a **live enforced obligation** | **0 verified** | No contract retains a Hermes/Nous billing, credits, subscription-sale, Portal, purchase, managed-tool-pool or promotional path |
| (b) Hermes commercial concept **excluded by accepted decision** | 161 | The de-commercialization contract, working as designed |
| (c) **Ranex's own** future commercial/licensing optionality | 40 | A different question entirely; not a Hermes obligation |
| (d) **False positives** | 5,882 | `plan` 2,140 · `license` 1,733 · `tier` 802 · `promotion` 771 · state identifiers containing `PLAN`, readiness `tier` fields, ordinary licence metadata |

**No search term was found matching solely inside a SHA-256 digest** — the
specific false-positive class this project has been burned by twice.

**96.7% of raw matches are noise.** This is why the sweep had to classify rather
than count: a naive reading of 6,083 hits would have manufactured a
de-commercialization crisis that does not exist.

### Two refinements this sweep produced

**1. Provider-neutral cost accounting survives, and should.** *"Generic cost
accounting is not monetization. Ranex still needs provider cost, token, latency,
and budget evidence"* (`docs/research/hermes-core-architecture-research-2026-07-27.md:1592-1595`).
The canonical exclusion is scoped accordingly: *"retain only provider-neutral
cost and budget measurement."* Do not read "remove monetization" as "remove cost
measurement."

**2. Ranex retains non-Hermes subscription route classes.** `ADR-0011:149-157`
and `ADR-0006:228` keep "eligible local individual subscription or product
API/BYOK/cloud route classes" as **separate** vendor-neutral concepts. A future
sweep that greps `subscription` and reports a violation would be wrong.

Full detail: [`dependency-risk-map.md` §4](dependency-risk-map.md).

Ranex's *own* monetization is a separate open question and out of scope.

---

## 7. Verification status — what is proven and what is not

Rule: a claim is not established because this assessment states it.

**Independently executed by this audit (FACT):** the ancestry checks, the
zero-Hermes directory counts, the import surface, `36 passed`, the four CLI runs
including absence-blocks and self-approval-refused, byte-identical determinism,
`243` pyrefly errors with a per-rule breakdown summing to 243, `0` pyrefly errors
on product source, the catalog counters, and the six G1–G6 gaps.

**Adversarially reviewed by two independent agents**, each with a terminal in
its own isolated worktree, briefed **without** this audit's conclusions so they
could not simply confirm them:

- **HY3** (OpenRouter `tencent/hy3`) — attack brief: prove or disprove Hermes
  reachability, break the determinism claims, find what the repository's own
  documents get wrong. **Terminated early on a sandbox permission block**, with
  Q3, Q5, Q6 and Q8 unanswered. What it completed produced two corrections that
  survived re-verification here.
- **Codex Luna** (`gpt-5.6-luna`) — exhaustive enumeration of 20 ADRs, 9 RFCs,
  47 contract files and the full commercial-term corpus.

**Three of my claims they falsified, each re-verified by me before acceptance:**

| Claim | Status | Correction |
|---|---|---|
| `0533e1eaf` is "reachable from no other ref" — inherited from `docs/HANDOFF.md` and `.github/workflows/architecture-contracts.yml:75-76` | **FALSE** | **Four** refs reach it. Deleting `develop` alone would not break CI. Two stale claims sit in those same two workflow lines — it also calls `develop` `UNPROTECTED` |
| "All 47 contract files are generator output" | **FALSE** | **Four are immutable hand-authored inputs** (`immutable_input_count: 9`, four under `architecture/contracts/`). The `ADR-0010` projection cannot be retired by regenerating |
| "21 ADRs, 10 RFCs" | **True only in this working tree** | `HEAD` has **20 and 9**. `ADR-0021` and `RFC-0010` are uncommitted — now **G5** |

**One new defect they surfaced, reproduced by me:** the `drift` gate reports
CLEAN when the `ADR-0010` baseline object is absent. From a `--depth 1` clone
where `0533e1eaf` is absent, the generator exits 0 and emits a byte-identical
tree, because it falls back to reading its own prior committed output. **CI as a
whole still holds** — `validate` fails with
`LEGACY_FIXTURE_GIT_COMMAND: failed to unpack tree object`. The narrower finding
stands: a green `drift` is not evidence the baseline exists.

**One positive result from HY3, not re-run here (INFERENCE):** the generator
produced a byte-identical tree under `TZ=Pacific/Kiritimati`,
`LC_ALL=tr_TR.UTF-8` (the Turkish-`I` trap), a set `PYTHONHASHSEED`, a fake
`HOME`, `SOURCE_DATE_EPOCH=0` and `umask 077`.

**What they did not falsify.** Neither agent found any Hermes code in the tree,
any Hermes dependency of Slice 1, or any live Hermes commercial obligation. The
central finding survived an adversarial pass by two models that were briefed to
break it. That is the basis for the verdict above — **not** my own measurement
alone.

**Caveat on that corroboration.** HY3 died before answering Q3 (prove the
negative), Q5 (deletions), Q6 (attack the documents) and Q8 (commercial sweep).
Luna covered Q8 thoroughly and Q6 partially. **No agent completed a full
adversarial pass on the deletion recommendations or on this document's own
claims.** A third run would still have value.

**Corrected during the audit:** an earlier draft stated these runs appended
journal rows. **False** — `--journal` defaults to `None` and was not passed;
the journal's 2 rows predate the runs by hours. The correction is what exposed
**G1**. Recorded because *stating a checkable claim without checking it* is this
project's most repeated defect.

**Nearly reported as a finding, and wrong:** that pyrefly never covered
`src/ranex`, making acceptance criterion 5 vacuous. It **was** vacuous, and had
already been fixed by the root `pyrefly.toml`, whose own comment says so. Caught
by reading before reporting.

**Not established (INFERENCE or unverified):**

- All Hermes behavioural claims. Hermes was **never executed**; source was read
  at `phase/2-runtime-bootstrap`.
- `BC-4` determinism is shown across two runs **on one machine** (CPython 3.14),
  not across machines, Python versions, or PyYAML patch releases.
- `BC-1`, `BC-3`, `BC-5`, `BC-7` and the twelve failure modes are covered by the
  36 tests but were not re-executed at the CLI boundary here.
- Acceptance criterion 2 — blocking a **real** change, recorded — **not
  demonstrated**. The PASS/FAIL pair above was constructed by the audit.
- The 65 promotion rows were **counted, not re-adjudicated** against their
  research sources.
- `remotes/upstream/*` was **not swept**; only the fork point was inventoried.

**Slice 1 is working. It is not accepted.** Those are different claims and this
document asserts only the first.

---

## 7b. Independent re-verification — second pass, 2026-07-31

A second independent pass re-executed every load-bearing claim in this audit
rather than trusting the draft. All commands ran from
`/home/soultransit/devtony/ranex` unless noted. **Every claim below was
re-measured and held.**

| Claim | Re-measured result |
|---|---|
| Zero Hermes runtime dirs at `HEAD` | `git ls-tree -r HEAD --name-only -- agent hermes_cli tools gateway cron plugins skills apps web ui-tui acp_adapter tui_gateway providers` → **0 files** |
| Hermes baseline not an ancestor | `git merge-base --is-ancestor 0533e1ea… HEAD` → exit `1`; same for `phase/2-runtime-bootstrap` |
| Lineage | Root `4ee007fcbe…`, `git rev-list --count HEAD` → **38** |
| Product/test sizes | `find src tests … xargs wc -l` → 30 files / **1,050 LOC**, tests 5 files / **573 LOC** |
| Test suite | `.venv/bin/python -m pytest -q` → **36 passed** (0.23 s this pass; 0.18 s in the draft — machine variance, not material) |
| CLI behaviour | `PASS` exit 0 · empty evidence `FAIL` exit 1 · `--approver worker` self-approval `FAIL` exit 1 · two runs `cmp` → `IDENTICAL` |
| Journal state | 2 rows, both `FAIL`, mtime `17:42`; record keys exactly `approver_id, considered, failing_rule, gate_id, missing_claims, reason, subject_digest, verdict` — **no `subject_lane`** |
| `governance/` untracked | `git ls-files governance/` → **0** |
| Import surface | `grep -rh '^import \|^from ' src/ranex` → stdlib 12 modules + `yaml` only; `pyproject.toml` → single dependency `PyYAML>=6.0.2,<7` |
| ADR count / expiry | 21 ADRs **in this working tree — but only 20 at `HEAD`**; see **G5**. `ADR-0010` authorisation expires **2026-10-31T23:59:59Z**; `ADR-0012:72` and `:656-657` carry the prohibition |
| Catalog counters | `promoted_provision_count: 65`, `owner_decision_count: 20`, `research_only_count: 13`, `entries: 98`, `catalog_status: DEFINITION_ONLY`, `catalog_version: 1.4.0` |
| `ADR-0017` acceptance | `uv run --project scripts/architecture … test_adr17_owner_resolution.py` → **11 cases, 0 failed** |
| pyrefly totals | From `scripts/architecture`: **243 errors**. From repo root: **0 errors** (product source) |
| `refs/codex/**` | **15 refs**; **11 PDF blobs** reachable from exactly **2 refs** |
| `ADR-0010` projection | 2,444 test paths; **zero present** in the working tree; 545 `hermes` matches (case-insensitive) |
| Generator origin | `git log --diff-filter=A -- scripts/architecture/generate_contracts.py` → first added `032adf368` |
| `ADR-0011` / `DEC-RANEX-*` quotes | All spot-checked against the ADR text and hold |

**Corrections applied as a result of this pass.** Four line citations in the
draft had drifted from the code — the facts they cited all hold, the numbers did
not. Re-measured and fixed in all six foundation documents:

| Draft cited | Re-measured | Subject |
|---|---|---|
| `validate_contracts.py:8436` | `validate_contracts.py:8507` | Synthetic `HumanDecisionV1` construction (`"authentication_context_id": "auth_" + decision_id`) |
| `generate_contracts.py:4872,4973,5129` | `generate_contracts.py:4938,5140` | Commit `0533e1eaf` references |
| `validate_contracts.py:26620` | `validate_contracts.py:13841` | Same commit, validator |
| `validate_contracts.py:31793` | `validate_contracts.py:32846` | `validation-report.json` write |

The corresponding citations in `docs/HANDOFF.md` are equally stale and were
**left untouched** — the handoff is a tracked in-flight document owned by the
session that maintains it.

---

## 8. Standing hazards, unrelated to Hermes

Carried forward because they sit in the same repository and are easy to lose.

1. **`refs/codex/**` — 15 refs, 11 copyrighted PDF blobs, and `origin` is a
   **public** GitHub repository.** `git push --all` or `--mirror` publishes them.
   **Never use those flags here.** Count with `git for-each-ref 'refs/codex/**'`;
   the single-star form returns 0 and reads as a false all-clear. Unresolved by
   owner choice. **FACT**, re-measured 2026-07-31.
2. **`develop` is load-bearing for CI and looks like dead Hermes residue.**
   Commit `0533e1eaf` is reachable from **four refs**, not one — `architecture/validated-baseline-20260728`, `develop`, `feature/deterministic-gate-controller-mvp` and `origin/develop` (**measured 2026-07-31**; the handoff and the workflow comment at `.github/workflows/architecture-contracts.yml:75-76` both say "no other ref" and are **wrong**). Both the `drift` and `validate` jobs read git objects from it
    (`generate_contracts.py:4938,5140`; `validate_contracts.py:13841`).
   Deleting or force-pushing it breaks CI outright. This audit's original framing
   — "remove Hermes material" — would have encouraged exactly that mistake.
3. **`validation-report.json` drift is invisible to CI.** The validator writes
    this tracked file (`validate_contracts.py:32846`) and no job diffs afterwards.
   Reproduced during this audit: a clean checkout emits
   `practice_corpus_validation: NOT_ASSESSED_LOCAL_ONLY` while the committed file
   records `PASS`. **This is exactly what `RFC-0007` asks the owner to decide.**
4. **A required check is matched by name**, and the workflow defining that name
   is an editable repository file. GitHub's `workflows` ruleset rule would close
   it; **not enabled — owner decision.**
