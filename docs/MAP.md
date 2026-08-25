# Ranex Map

**The map. Not a decision, not a gate, not authority.**

This document shows the whole intended system while separating what is known
from what is hypothesis. It is the top of the delivery hierarchy: problem →
product requirements → **this map** → architecturally significant requirements →
bill of materials → current-slice ADRs → one small slice → evidence → back into
this map.

| | |
|---|---|
| Version | `3.5.9` |
| Created | 2026-07-31, as `MASTER_ARCHITECTURE_SPECIFICATION.md` in the pre-reset tree |
| Last revised | 2026-08-21 — A/B/C substrate maturity synchronized after SLICE-029–033 and SLICE-035; see §0.33 |
| Status | Working document. **Not digest-pinned**, deliberately — see §0.3 |
| Structure | [arc42](https://arc42.org/overview) §1–12, plus §13–§17. See §0.4 for licensing |
| Authority | **None.** This document grants nothing, gates nothing, and supersedes no ADR |

---

## §0 How to read this

### 0.1 Status vocabulary

Every section header and every material claim carries one label. A claim with
no label inherits its section's.

| Label | Means |
|---|---|
| `CONFIRMED` | Supported by executed implementation evidence |
| `PROVISIONAL` | Current direction. Written down, reasoned, **not validated by anything running** |
| `UNRESOLVED` | A real decision is still required. Names what would settle it |
| `OUT-OF-SCOPE` | Not needed for the current delivery horizon |

**An accepted ADR does not make a thing `CONFIRMED`.** Acceptance means the
decision was made, not that it was proven. Confusing the two is the failure this
document exists to prevent.

### 0.2 What this document is not

- Not a specification you can implement from. It is deliberately shallow in
  places, because depth without evidence is the thing being avoided.
- Not authority. The ADRs in `docs/adr/` govern what may be built.
- Not a work plan. §5.5 names the bill of materials that will carry that load.
- Not a log. `docs/STATE.md` says where work stopped; this says where it is going.
- **Not conformant to ISO/IEC/IEEE 42010**, the standard for architecture
  descriptions, and knowingly so. It has an entity of interest (§3.1), views
  (§5, §6, §7) and partial rationale (§0.5, §4.2, §4.3). Stakeholder, concerns,
  viewpoints and correspondences are declared; model kinds are absent and two
  viewpoints govern no view. Those gaps are recorded as `RISK-18`.
- **Not finished.** The owner's assessment as of 2026-08-03 is that this map is
  "still cloudy and needs much more refinement." Treat every §1 claim as a first
  articulation rather than a settled position. That refinement arrived as
  `2.5.0`–`3.0.0`, and at `3.0.1` the map is settled **as a director of the
  build** — the owner delegated the done-call, and it was made on executed
  checks (§0.8), not confidence. Absolutely it stays unfinished: `VP-05`/`VP-06`
  govern no view until the harness and SLICE-006 give them one.

### 0.3 Why it is not digest-pinned

A map must stay current cheaply. A decision should be expensive to change.
Pinning this document's digest into anything taxes every correction and produces
a map that is stale because updating it is costly. Keeping it outside the digest
chain is what makes it affordable to keep true.

### 0.4 On arc42

The twelve section headings follow arc42 (Starke & Hruschka), used here as a
**conformance checklist** to avoid omitting a section, not republished as an
adaptation. arc42 is licensed CC BY-SA 4.0; whether to adopt-and-attribute
instead is an open owner decision recorded in §11 as `RISK-16`.

### 0.5 What changed in `2.0.0`, and why — `PROVISIONAL` as a change of position

Version `1.1.0` stated the product thesis as:

> A governance harness that makes unreliable AI agents produce reliable software.
> Rules compiled into code change what an agent produces.

That is a claim about **output quality**. It was never tested, it is expensive to
test, and `1.1.0` recorded that the experiment which would settle it had not been
run.

The repository moved away from it independently. `CLAUDE.md` and `README.md` now
state the opposite in the strongest available language:

> **Ranex does not improve aim.** Not by one degree. It makes misses visible and
> cheap, and hits provable.

`2.0.0` resolves the contradiction in favour of the repository. Every product
requirement, ASR and risk in `1.1.0` was written against the discarded thesis and
has been re-derived. The change is not cosmetic: **the old thesis is a claim
about aim, the new one is a claim about scoring**, and they imply different
products, different proof burdens and different buyers.

The substantive additions in `2.0.0` — the problem statement (§1.1), the factory
doctrine (§4), calibration as a first-class concern (§8.4), and the measurement
problem (§11.3) — come from an owner working session on 2026-08-03. They are
recorded as `PROVISIONAL` because they are newly articulated and nothing has been
built against them.

### 0.6 What changed in `2.1.0` — bounded adoption of TOGAF

`2.1.0` adopts **four** parts of the TOGAF ADM and explicitly refuses the rest
(§4.5), and records the map's own non-conformance to ISO/IEC/IEEE 42010 (§0.2,
`RISK-18`).

Two standards, two different questions, and Ranex needs both:

- **ISO/IEC/IEEE 42010** — *architecture description*. Answers "is the map
  complete?" Completeness is not "every section is filled"; it is **every
  identified stakeholder concern is framed by a viewpoint and addressed by a
  view, with correspondences stated between them.** That is a checkable
  criterion; the one used to call `2.0.0` "fully written" was a formatting check.
- **TOGAF** — *architecture process*. Answers "how do we get from here to there,
  and how do we know the builders complied?"

**Source discipline:** the TOGAF material consulted was 9.1/9.2, which is
**superseded**. The current standard is the *TOGAF Standard, 10th Edition*
(The Open Group, April 2022, Technical Corrigendum 1 in 2025), free for
non-commercial use. Anything entering an ADR must cite the 10th Edition
directly — the 9.x copies read were an unlicensed third-party dump including
copyrighted commercial books, and ADR-003 would reject them on origin and
licence alone.

### 0.7 What changed in `2.2.0` — the stakeholder layer

`2.0.0` and `2.1.0` were written from reasoning. `2.2.0` is the first version
containing anything the **owner stated directly**, and it changes four things:

1. **§1.3 is new** — the stakeholder, his four concerns in his own words, and a
   measured coverage test of every requirement against them. This is the layer
   whose absence produced 561 files and zero product code last time.
2. **§1.4's requirements were re-tested.** `PR-01` was reframed (it had been
   written for an acquirer who is not a stakeholder here) and `PR-04` was made
   explicit as *agent produces, human approves*.
3. **§11.1 and §11.2 are deferred, not resolved.** There is no external audience
   and no deadline, so market questions stop being sequencing inputs. Dogfooding
   is the schedule.
4. **`RISK-15` is reclassified** — one implementer is the premise, not a defect —
   and `RISK-18` is partially closed.

What `2.2.0` still does **not** have: declared viewpoints and correspondences.
The map can still be wrong without anything noticing. That is the next gap.

### 0.8 What changed in `2.3.0` — the map becomes able to fail

§14 is new: six declared **viewpoints**, seven stated **correspondences**, and an
honest **conformance statement** that declines to claim conformance.

It earned its place immediately. Declaring the viewpoints exposed, on first
application, that **`C-02` and `C-03` are framed by viewpoints that govern no
view at all** — two of the operator's four worries have no view in this map,
which agrees with §1.3's independently-measured coverage table. That is the
completeness criterion doing the job a formatting check cannot.

Four correspondence rules were executed against the document on 2026-08-03 and
pass: no risk is referenced without being defined, no section cross-reference
dangles, and no requirement lacks a concern. `CR-02` **fails by design** and is
left failing, because a hole reported is worth more than a hole read over.
Re-executed at settlement (`3.0.1`): `CR-01`, `CR-04`, `CR-05` pass; `CR-07`
passes with one named exception — `SLICE-005` is referenced in §13 and §15.2
but has no file on disk, having been withdrawn before any implementation was
committed. A slice the ledger itself records as never committed is a named
exception, not a dangling reference.

### 0.9 What changed in `2.4.0` — the translator, and the chain's freeze line

Three owner clarifications, all in §11.6:

1. **Behaviour has two halves with a freeze line between them** — specify, then
   *freeze*, then execute. Without that line the target moves mid-work, and
   everything else in this document is decoration. It is the same rule `CLAUDE.md`
   already states as tests frozen before BUILD and read-only to implementers.
2. **The adobo illustration**, which states the hermetic principle better than
   this document did: recipe, ingredients and tools are all handed to the cook
   and none are chosen by him.
3. **The translator is a missing container** (§5.1). The map described a kernel
   that emits verdicts but no plain-language projection, then stopped — which is
   exactly why `C-04` is unserved. `ranex journal verify` can inspect chain
   integrity; it is not that projection. The role now exists as absent rather
   than being invisible.

And the trap the same illustration exposes: **an independent taster that is
another model is not independent.** `PR-02` with its reason made obvious.

### 0.10 What changed in `2.5.0` — filtered pre-reset dig

This is a merge of the retained findings from a filtered dig of the pre-reset
research, decisions and architecture corpus, not a restoration of its enterprise
architecture. It adds future packet/role/verdict/independence capabilities,
binding inherited constraints, and retained control details; it also records the
three current contradictions and the silently lost approval, measurement and
journal-effect requirements. The README correction replaces the prior false
assertion with the implemented `ranex journal verify`, and adds the still-open
rollback/truncation risk. Sources outside the repository:
`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:605-990`,
`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:20`,
`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md:279-398`,
`README.md` ("Known gaps — stated plainly").

### 0.11 What changed in `2.6.0` — adversarial pass

Two adversarial rounds by `tencent/hy3` retained kernel determinism, the
producer/approver separation, and Phase G positioning. They overturned three
overclaims: confinement makes the producer-unalterable scorer false today,
red-then-green proves discrimination rather than precedence, and a rich
fail-closed outcome taxonomy is not a graded pass scale. The corrections are in
§1.2, §1.3, §4.5 and §11.5–§11.6.

### 0.12 What changed in `2.7.0` — xhigh audit and second adversarial review

An xhigh code audit corrected repository contradictions and replaced 28 dead
scratchpad citations with primary sources outside the repository. A second
adversarial review found limits in the map's self-declared concern set,
mutation/coverage reasoning, and operator-selected first thread. Fifteen
`CONFIRMED` labels were demoted because policy, decisions, owner statements and
history are not executed implementation evidence; the limits are `RISK-21`–`24`.

### 0.13 What changed in `2.8.0` — the maturity ledger and per-problem diagrams

The owner's complaint against `2.7.0`: the labels are correct but the picture is
vague — a reader cannot say at a glance which mechanisms are proven and which
are not, nor see how each of the four concerns is actually defended. Two
additions, and nothing else changed:

1. **§15, the maturity ledger.** Every mechanism in one of two columns —
   MATURE/PROVEN (built and carrying executed evidence, or proven elsewhere by
   code the world already runs and available to adopt) or IMMATURE/UNPROVEN
   (decided, designed, or vague, with nothing running behind it). Each row names
   its evidence or its absence.
2. **§16, per-problem architecture.** One diagram per concern — `C-01` through
   `C-04` — drawing the defence chain step by step, each step marked built,
   open or absent, with the residual holes named.

The owner also stated the adoption rule as a standing instruction: where mature,
widely-used open source already solves a mechanism, Ranex grabs it rather than
generating fresh code — and adopts it by **copying it into Ranex's own
infrastructure to improve and maintain, never by adding a dependency** (§15.3).
`opensrc` is installed and caching sources locally for exactly this.

A re-audit of the map against the tree accompanied this revision: every line
reference, count and cross-reference was re-checked on 2026-08-03. One stale
number was found and corrected (§5.3, suite count); every other citation held.

### 0.14 What changed in `3.0.0` — the owner's restaurant; the harness decision

Owner working sessions on 2026-08-03 changed the product thesis. Recorded the
same way as `2.0.0` — as a change of position, with what it overturns named:

1. **Ranex becomes a full harness.** Overturned: *control plane, not an agent
   harness* and *never implements an agent loop*. The owner chose the full
   harness, agent loop included: **Ranex owns the restaurant.**
2. **The restaurant, in the owner's words.** Ranex owns the restaurant and is the
   owner's assistant for managing different restaurant chains. The kernel is the
   library of handbooks, manuals, rules and recipes that every employee works
   from. Each department has its own manager/supervisor and main worker.
3. **The harness is a trimmed fork of opencode** (MIT). Forked at a pinned
   commit, bloat stripped (desktop, web, console, infra), the lean agent core
   kept and molded to the kernel. The cost is recorded: upstream moves fast, so
   the diff must stay small enough to rebase — or the fork silently becomes a
   second codebase to maintain. **§17 is the trim spec**: what is kept, what is
   cut, what must be assessed against code, the named overheads and bottlenecks,
   and the customization policy — few knobs, deep customization blocked.
4. **The wall becomes a process boundary.** Harness (model-driven, TypeScript,
   forked) and kernel (code-only, Python, proven) run as separate processes.
   Hooks inside the harness collect; the kernel outside judges and stamps —
   reads disk, holds keys, writes the journal. Confinement (ADR-006) moves from
   scheduled hardening to load-bearing wall.
5. **Delegation, clean-room.** The orchestration patterns — foreman → department
   supervisors → workers, category→model routing, plan-before-execute — are
   studied from oh-my-openagent and reimplemented as original code. Its code is
   SUL-1.0 (internal use only; no commercial distribution; derivative works
   included) and never enters this tree, converted or not. hermes-agent and
   OpenClaw remain feature quarry under §15.3; hermes was audited and rejected
   as a base on 2026-08-01 (zero measured contribution), and that verdict stands.
6. **The kernel handbook.** `governance/` becomes the handbook library every
   agent reads — rules, manuals, recipes. Reading guides; only the kernel
   enforces. *A rule an agent can read is a suggestion* survives verbatim.
7. **The Web UI is parked.** Not designed, not built, not discussed until the
   harness works. When it comes, its features are sliced from the quarry under
   §15.3, one ADR-governed copy at a time.
8. **What does not change.** The kernel invariants (§5.2). *Does not improve
   aim.* The maturity ledger (§15) and per-problem diagrams (§16) — the evidence
   is the evidence.

`PROVISIONAL` throughout: nothing is built against any of this yet.

**The build order (owner, 2026-08-03):** this map → one researched ADR for the
fork (pinned commit, trim list, kernel-bridge design) → the trimmed fork talking
to the kernel → first delegation (one foreman, one worker, one task, judged by
the kernel) → the handbooks. SLICE-006 is parked behind the fork work and stays
recoverable in git history — it was unparked 2026-08-04 and is now done.

### 0.15 What changed in `3.1.0` — the background worktree agent manager — `PROVISIONAL`

The owner added a scheduled capability to the pipeline: a **background worktree
agent manager** — many agents running in one harness process, each in its own
worktree, tracked durably and supervised, with verification and kernel-governed
merge. It is the next phase after first delegation. Recorded the same way as
every earlier revision:

1. **ADR-014** (`proposed`, this repository) decides the kernel-side change the
   manager requires: the bridge becomes a **per-member protocol** — per-member
   emission binding task id, member id, worktree, commit and tree; per-member
   latch; per-member commit boundary. It is the only kernel decision; the
   harness-side mechanics are harness decisions, not this ADR.
2. **The manager is outside ADR-013's gate.** The owner recorded this on
   2026-08-06: the manager is new product behaviour, not the authenticity-hardening
   track. The credential scale-up it implies — one model credential shared by N
   members in one process — is `RISK-06`, standing, mitigated by scoped
   spend-limited keys.
3. **The pipeline shape.** Milestone "Background worktree agent manager" on this
   repository; slice issues #1-#9 carry the plan; SLICE-060 through SLICE-068
   (renumbered 2026-08-17) open after SLICE-010 and after the durability
   program, with SLICE-010 satisfied but durability still required before the
   manager starts — SLICE-010 closed `15614e6fc`, SLICE-011 closed `e0b9886d9`.
   One slice at a time; §0.16 owns the durability program. §9
   carries ADR-014; §15.2 carries the manager as designed-unbuilt; §16.3 names
   it as the first scheduled machinery for `C-02`.
4. **What does not change.** One git worktree per task survives per member; the
   kernel merges, the harness never does; the wall stands — hooks collect, the
   kernel judges.

`PROVISIONAL` throughout: ADR-014 is proposed, no manager slice is open (its
slice issues were renumbered SLICE-020-028 on 2026-08-07, and again to
SLICE-060-068 on 2026-08-17, after kernel SLICE-020 closed over the range),
nothing is built.

### 0.16 What changed in `3.2.0` — the durable execution program — `PROVISIONAL`

The owner directed a full audit of the harness's durability story after a
proposal claimed a durable-execution fix. The audit verdict (ADR-015) is that
the proposal's diagnosis was right and its fix misaimed:

1. **ADR-015** (`accepted 2026-08-07`, this repository; `proposed` when this
   section was written) decides the harness-side durability
   contract: **at-most-once with explicit interruption** — never
   at-least-once-plus-idempotent, because unsandboxed `bash` cannot be made
   idempotent and spec `session.md:50` forbids silent side-effect replay.
   First deliverable is a **provider watchdog** (inactivity + absolute timeout),
   then a reconciler reorder, then durable retry, then durable permission and
   question blockers, then Session-ID fencing via the harness's existing
   `effect-flock` and EventV2 `owner_id`. Explicitly **not** adopted: a
   `session_execution` lease/heartbeat table, a `tool_attempt` replay column,
   and subagent completion recovery (V2 has no `task` tool yet).
2. **The prototype gate.** SLICE-011 (closed 2026-08-07) is a disposable prototype in
   scratch harness worktrees (ADR-013 style): five claims red-to-green with
   negative controls and a digest-bound exit record before any production slice
   opens. **All five ran and are green (2026-08-07)** — one worktree per claim
   at an identical harness HEAD — and the five per-claim records are
   consolidated, embedded and hash-bound in
   `docs/slices/SLICE-011-durable-execution-prototype.exit-record.json`. The
   compiled gate, which extends `tests/contract/test_docs_discipline.py` to
   refuse production durability slices without that record, is **not built**;
   is now BUILT (criterion 8, red-then-green, 11 durability cases). SLICE-011
   closed 2026-08-07 with all nine criteria met; the record is archived at
   `docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`.
3. **Tracking.** Milestone #1 "Durable execution, failover, and recovery" and
   issues #1-#9 on `anthonykewl20/ranex-harness` carry the production plan;
   SLICE-012+ open one at a time after SLICE-011, each refused by the compiled
   gate unless the prototype record is present, GREEN and digest-bound.
4. **What does not change.** The wall stands; the kernel is never asked to
   judge liveness. SLICE-010 was parked, then re-opened and closed 2026-08-06
   with all fourteen criteria proven (`15614e6fc`).

`PROVISIONAL` at `3.2.0`: ADR-015 was proposed and **nothing was built in
production** — the prototype ran green and raised confidence in the *design*
without being a durability claim about the harness. ADR-015 was **accepted
2026-08-07** (`c106ec170`) and the production watchdog is now SLICE-012; see
§0.20 for what is built. The prototype itself still ships nothing.

One result is worth carrying forward because it is evidence about method, not
about durability: claim 5 was reported stable, approved by two reviewers, and
was not stable. Supervisor re-runs measured a ~12% failure rate whose cause was
a fixture pragma-ordering race, invisible because the fixture captured worker
stderr and discarded it. Reviewing a report cannot find what the report does
not contain; re-running the gate can.

### 0.17 What changed in `3.3.0` — evidence refresh

Evidence changed the claims, in bulk: SLICE-007 through SLICE-010 closed,
ADR-015 opened the durability track (SLICE-011 open), and the agent-manager
slice issues were renumbered SLICE-020-028 on 2026-08-07 to clear the collision
with that track (and again to SLICE-060-068 on 2026-08-17, after kernel
SLICE-020 closed over the range). Stale counts, tenses and risk standings are corrected
throughout; no position changes.

### 0.19 What changed in `3.3.2` — SLICE-011 closed

The compiled gate (criterion 8) is built, so SLICE-011 closed with all nine
criteria met, and the slice and its record are archived under
`docs/slices/done/`. All five claims now carry two-reviewer consensus; the two
that had only one reviewer said so before they were closed, which is the part
worth keeping. **No position changes**: ADR-015 stays `proposed`, nothing
durable is built in production, and the prototype still ships nothing.

The gate was built wrong first, and that is recorded rather than tidied away.
It derived the record path from the open slice — on a mistaken supervisor
instruction — which meant a production slice was refused for lacking a record
production slices never carry, while the green prototype record sat
unconsulted. reviewer-hy3 caught it; the supervisor reproduced it on disk
before accepting the finding, because the same reviewer had been wrong about
something else in the same review. Being wrong about one thing is not evidence
about another. The gate now resolves the prototype record in both
`docs/slices/` and `docs/slices/done/`, which is the only state it will ever
actually run in.

### 0.18 What changed in `3.3.1` — the prototype ran

SLICE-011's five durability claims were prototyped in parallel on 2026-08-07,
one disposable harness worktree per claim at an identical HEAD, and all five
are green red-first with negative controls. The five per-claim exit records are
consolidated, embedded and hash-bound in
`docs/slices/SLICE-011-durable-execution-prototype.exit-record.json`
(`5bf20ac0c`), so the evidence outlives the worktrees, which are meant to be
deleted. §0.16 and the durability row are corrected from "the prototype has not
run" to what actually happened. **No position changes and no durability claim
about the harness**: the prototype ships nothing, ADR-015 stays `proposed`, and
SLICE-011 closed 2026-08-07 once its compiled gate was built.

Two results are recorded because they are evidence about method rather than
about durability. First: claim 5 was reported stable and approved by two
independent reviewers, and was not stable — supervisor re-runs measured ~12%
failures from a fixture pragma-ordering race that was invisible because the
fixture captured worker stderr and discarded it. Reviewing a report cannot find
what the report does not contain. Second: the record states plainly what a
kernel-repo gate can and cannot do — it can check the record is present,
well-formed, green and digest-bound; it can never re-verify the bytes, which
live in another repository built to be thrown away. That is the same limit
ADR-003 already accepts for vendored prior art, and it is written down rather
than left to be discovered.

### 0.22 What changed in `3.4.0` — the measurement flywheel is source-backed and prototype-gated

ADR-016 is **accepted** (owner, 2026-08-09). Six permissive pinned sources were vendored and refetched; the frozen-target/fixed-treatment conflation was corrected; and monitoring-only observations were separated from controlled paired grades. The parked measurement-local workflow is M0, then F1–F4, with no current slice change. Ranex composition remains **UNPROVEN**.

### 0.23 What changed in `3.3.5` — the reconciler ships, and adds a hazard

SLICE-013 closed: the runner no longer returns on its eligible-input guard
before reconciling, and a startup sweep wired into the application graph
recovers sessions nobody calls `run()` on — the half SLICE-011 left as a
capability with no caller. Two of ADR-015's five claims are now built; durable
retry is next.

Recorded because it cuts against the usual direction of these entries: this
slice **introduced** a hazard as well as removing one. The sweep is DB-global
over a process-wide shared database, so a second process booting marks tools a
first live process is actively running as interrupted. SLICE-011 claim 5 had
already reproduced that two-process case, so the precondition is demonstrated
rather than assumed. A reviewer raised it as a blocker and it was accepted as
scope — the harness runs one daemon (ADR-014) and closing it properly needs the
durable owner claim the fencing slice owns. Fencing must now gate the sweep
before this harness is ever multi-process; that is a dependency the durability
track did not have yesterday.

Two measurement notes worth more than the code. The concurrency test only
works because `Effect.all` defaults to sequential in this Effect beta — without
an explicit `concurrency: 2` it would have passed against the unfixed code. And
`turbo.json` had scoped its test task to the pre-rebrand package name, so CI
was running 1100 tests and silently skipping 2942; measured with a dry run,
not read.

### 0.21 What changed in `3.3.4` — the rebrand finishes

The 2026-08-06 rebrand had renamed a bin and stopped. The workspace scope,
the package directory, the config directory and the CLI's own program name
still said opencode, and two binaries were declared at once. That is closed
(`a4da8a8d28`..`3dfe9ee562`), and the harness rows below are unaffected: this
map's many references to *a trimmed fork of opencode* are provenance and MIT
attribution, not leftovers, and they stay.

Two findings are recorded because they outlive the rename. Ranex had been
reporting itself to third-party gateways as `opencode` through OpenRouter
attribution headers, so its traffic was credited to the upstream project; the
tests that appeared to protect that only asserted our own emission. And the
claim that this fork's CI workflows were inert was wrong — three are gated on
the upstream repository, twenty-two are not, and one of those pointed at a
directory the rename had just deleted. Four more still point at directories
this fork never had, so CI was already broken before any of this. `RISK` rows
are unchanged; none of it moves a position.

### 0.20 What changed in `3.3.3` — the watchdog goes to production

ADR-015 was **accepted 2026-08-07** (`c106ec170`), superseding the `stays
proposed` line this map carried since `3.3.1`/`3.3.2`. SLICE-012 is open: the
**production provider watchdog** — the first of ADR-015's five claims and the
only one needing no schema change. The slice was amended before any code was
written (`dc014d44a`, six holes from a pre-implementation review; see the slice's
"Amendments" section for the mapping to criteria 1–7 and control 5); the sharpest
is the one worth carrying forward here — both timeouts must fail as a
**non-retryable** `LLMError` reason, or the watchdog fires, is retried,
restarts the same stall and hangs anyway while every criterion still passes. It
is in progress, not built: four implementation terminals work the nine
done-criteria red-first in the harness (`anthonykewl20/ranex-harness`, issue
#2). On the kernel `slice-012-docs` branch this map's durability row and §0.16
move from "nothing built in production" to what the slice builds, with `[TODO]`
where production evidence does not exist yet; the harness
`specs/v2/session.md:153` deferral is rewritten the same way on the harness
`slice-012-docs` branch. This change does not modify `docs/STATE.md`; the owner
rewrites it in `main` each session, so it is finalised there, not here. The
disposable SLICE-011 prototype remains green and digest-bound but
reference-only — it ships nothing, and `proto/s011-watchdog` carries no
obligation to stay correct as the harness moves. **No position changes beyond
the ADR status**: the durability contract is still at-most-once with explicit
interruption; the other four claims (reconciler, retry, blockers, fencing) stay
`PROVISIONAL` and open one slice at a time; nothing here is `CONFIRMED` until
the production gate is green on disk.

This is a draft: where the production evidence does not exist yet, the map says
so and marks it `[TODO]`. The gate (`tests/contract/test_docs_discipline.py`)
still resolves the prototype record; it cannot re-verify harness bytes.

### 0.24 What changed in `3.5.0` — specification earns implementation authority

The owner made the missing Idea → Behaviour → Result thread the explicit P0 and
first product program. SLICE-017 is the single active prerequisite; ADR-017 is
the program decision and has no implementation slice open. Human and AI will
resolve blocking questions,
observable outcomes and non-goals; normative A is rendered into manifest B; a
human signs A+B in envelope C; then the
kernel issues a least-authority implementation grant which the harness enforces
at every effect path. A model, prompt, mode, comment or observed behavior grants
nothing.

This changes sequencing, not the truth of parked work. ADR-006 is a dependency:
it confines the admitted process, while ADR-017 decides when and why the process
may act. The 2026-08-17 milestone-4-first decision is historical provenance;
the owner superseded it on 2026-08-25 by closing milestone 4 with partial
delivery and stopping the harness lane. The initial release is kernel-only.
Harness effect admission, broker qualification, real-provider task proof,
concurrent production mutation and production fanout are not release scope.
Only #19 / SLICE-036 remains next: qualification-only approved-batch and kernel
continuity in disposable worktrees, with publication blocked. Logical
parallel-readiness in the historical DAG does not open another slice or writer.

**The TUI redesign (`ADR-018`) is outside this sequence.** The owner recorded on
2026-08-10 that it is a separate track: harness work packages BOARD-01..BOARD-22,
not slices. It neither consumes the single open slice nor waits for the P0 exit,
and it changes no kernel authority — the board renders verdicts and issues none.
Its one kernel dependency, a structured per-claim cause on `Evaluation`
(BOARD-02), is governed work and needs its own slice like anything else that
touches the kernel. Do not confuse it with the Web UI, which stays parked (§15.2).

The former milestone was deliberately composition-level. Its installed-harness,
real-provider and concurrent-production closure criteria are retained as
historical provenance only; owner scope reset 2026-08-25 withdrew that program.
The current release is kernel-only and #19 / SLICE-036 qualifies approved-batch
continuity in disposable worktrees with publication blocked.

### 0.25 What changed in `3.5.1` — confinement becomes session-sized

The prior SLICE-017 combined native build, host qualification, cgroup and output
lifecycle, `cmd_run`, evidence and fourteen attacks. That was not one-session
work. The decision remains ADR-006, but delivery is now active SLICE-017
(host/build/real launcher probe), planned issue #21 / SLICE-018 (cgroup,
namespace and bounded-output lifecycle), then planned issue #22 / SLICE-019
(`cmd_run`, evidence and installed-CLI attack closure). Only SLICE-019 may accept
ADR-006 or close RISK-06; SLICE-029 follows it.

The split adds no weaker intermediate production mode. SLICE-017 cannot execute
an untrusted subject; SLICE-018 exposes no `cmd_run` path and signs nothing;
SLICE-019 has no direct-execution fallback. Exact path ownership and frozen I/O
for every future package are recorded in §4.7 before its issue may open. GitHub
milestone #3 is mirrored by parent tracker issue #11; this map remains authority.

### 0.26 What changed in `3.5.2` — parallel jobs gain a closed authority boundary

Parallel work now has two explicit classes. Bounded read-only research and
independent review may fan out immediately: children may read local/source-host
evidence but cannot mutate repository files/refs or external state, receive a
secret, or turn their report into implementation authority. The supervisor
verifies their evidence and orders their findings canonically.

Mutation-capable fanout remains forbidden in production. Today's `task fanout`
accepts free prompts from JSONL and repeats `task delegate`; its bounded pool and
one-worktree-per-task behavior are useful prototype mechanics, not authorization.
The planned governed grammar is:

```text
PYTHONPATH=src uv run --frozen python -m ranex.cli.main task fanout \
  --spec-packet A.json --artifact-manifest B.json \
  --approval-envelope C.json --tasks child-requests.jsonl \
  --target <repo> --journal <external> --outcome-dir <dir> --pool N
```

B/C own harness, model, timeout and suite; caller flags cannot replace them.
Every child row names its approved `scope_id`, `capability_request_id`, task and
isolated worktree, never free-form prose as an oracle. The signed batch binds the
parent/C and base digests, dependency DAG, exact pairwise-disjoint path+action
scopes, per-child gates/evidence, retry limit and `max_pool`; `--pool` may only
narrow that maximum. A ready set is the canonical task-ID-sorted pending set
whose dependencies are VERIFIED and whose bound base/parent remain current.
Failure blocks dependants but not independent ready tasks; retries keep identical
authority and tests. Completion order never changes canonical result order.

Children get parent ∩ request and no secret, approval, integration, merge or
publication capability. One key-exclusive integrator consumes accepted results
in canonical dependency/task/attempt order; the kernel alone publishes with a
stale-base CAS. SLICE-036 remains the only retained qualification slice, in
disposable child worktrees with publication blocked. The SLICE-037..044
harness-effect and production-exit program is historical design provenance and
was withdrawn by the 2026-08-25 owner scope decision. There is one open slice
and one mutation writer; no production fanout authorization is claimed.

### 0.27 What changed in `3.5.3` — evidence refresh

SLICE-017, SLICE-019 and kernel SLICE-020 (judgment identity and the verdict
read channel, ADR-019/020) closed 2026-08-12..13: fifteen closed slices, one
withdrawn, none open. §1.3's coverage accounting is corrected to that count.
The verdict channel is UI/board-track work under ADR-018/022; the P0 critical
path remains SLICE-018, then SLICE-029..044. **No position changes** — this
revision records evidence, not decisions.

### 0.28 What changed in `3.5.4`

SLICE-018 closed 2026-08-14 and shipped with a post-closure fix (0caa1090f):
the session required Landlock ABI equality with the profile minimum and refused
every real session on ABI≠6 hosts; now a true minimum. Real sessions verified on
the qualified host via delegated systemd units (honest, output-writing,
alias-refusal, OOM-refusal). Sixteen closed slices, none open. §1.3 coverage
accounting now counts SLICE-018. No position changes — evidence, not decisions.

### 0.29 What changed in `3.5.5`

SLICE-046 (issue #21) closed 2026-08-15: `cmd_run` binds the qualified
strict-local session through a subprocess controller (ADR-023, `proposed`);
evidence is signed only after fail-closed confinement-result validation.
ADR-006 and ADR-017 are accepted (ADR-017 without broadening); `RISK-06`
closes in §11.5 with its standing limit recorded — the controller subprocess
remains same-uid trusted infrastructure. Seventeen closed slice documents,
none open; SLICE-029 (#12) is next. No position changes.

### 0.30 What changed in `3.5.6` — the owner's build order: milestone 4 first

The owner decided (2026-08-17) that the real-world verification &
observability program — GitHub milestone 4, SLICE-054..059 — is built
before milestone 3 (P0) continues and before milestone 2 (background
manager). This is dependency order, not a competing priority: P0's own
exit evidence strictly requires milestone 4's observability contract and
real-e2e conventions, so the framework slices (SLICE-054/#34 then
SLICE-055/#35) come first. The subordination sentence in §0.24 is revised
accordingly ("measurement flywheel" removed from the parked list), P0
remains the primary objective, and `tests/contract/test_docs_discipline.py`
now enforces that MAP carries the dated decision and STATE's Next points at
SLICE-054 until the framework closes. Enforced by
`test_map_records_owner_build_order` and
`test_state_next_agrees_with_build_order`. When the framework closes,
STATE.md records the literal marker line `Framework closed: SLICE-055 closed
<YYYY-MM-DD>` — the exact string the contract test requires.

### 0.31 What changed in `3.5.7` — manager slice issues renumbered; build-order tests hardened

The background-manager issues (#1-#9, GitHub milestone 2) carry SLICE-060..068,
renumbered 2026-08-17 from SLICE-020..028: the kernel lane's closed
SLICE-020 (judgment identity and verdict read channel) had consumed the head
of the old range. Precedent: the 2026-08-07 renumber recorded in §0.15. No
plan or scope change — the issues remain planned-not-active and
dependency-gated behind milestones 4 and 3. Two hardening fixes ride along:
STATE's `## Next` contract is now a literal mandated line — 'Next slice:
SLICE-054' — proximity or mention grants nothing, and the framework-closed
marker line tolerates CRLF. When the milestone-4 framework closes, STATE
records the literal marker line "Framework closed: SLICE-055 closed
<YYYY-MM-DD>" — the exact string `test_state_next_agrees_with_build_order`
requires to release the Next pointer.

### 0.32 What changed in `3.5.8` — the Next-pointer contract becomes a literal line

`test_state_next_agrees_with_build_order` now requires the literal line
`Next slice: SLICE-054` in STATE.md until the framework-closed marker line
appears. This retires the proximity-based probe (and its accepted
nearby-mention gap) in favour of the same mandated-line idiom as the
build-order line. When the framework closes, the session rewrites the line to
name the real next slice beside the marker line.

### 0.33 What changed in `3.5.9` — A/B/C substrate maturity synchronized

SLICE-029–033 and SLICE-035 are closed. The current capability, container, runtime, and
maturity views now record what their executed artifacts prove: canonical A/B/C
contracts and vectors, lifecycle, deterministic closed-DSL projections and
manifest B, approval/revocation/intersected grants, trace integrity, and
real-subject bootstrap are built kernel-side. This does **not** promote the
system-level composition: there is still no owner-facing intake product, common
harness effect admission, governed concurrent mutation, or real SLICE-044 exit.
SLICE-036 is next. No architecture decision changed; stale maturity labels were
corrected to match the repository and `docs/STATE.md`.

### 0.34 What changed in `3.6.0` — kernel-only initial release scope

Owner decision 2026-08-25: milestone 4 is closed with partial delivery. The
kernel observability, real-e2e framework, verdict, execution and provisioning
families (#34–#38 / SLICE-054–058) remain valid historical implementation
evidence. The task-family proof (#39 / SLICE-059) and protocol-v1 broker
qualification (#43 / SLICE-069) are withdrawn, not completed release gates.

Historical marker: Owner decision 2026-08-17: milestone 4 was P0's proof substrate.
Build order: milestone 4 → milestone 3 → milestone 2. This order
is superseded by the 2026-08-25 kernel-only scope reset.

Development requiring the ranex-harness lane is stopped. The initial release
is kernel-only: deterministic verdict/evidence/journal, provisioning,
confinement, A/B/C authority substrate, and serial task continuity. Harness
effect admission, credential-broker qualification, real-provider task proof,
concurrent production mutation and production fanout are out of scope and make
no closure claim. #19 / SLICE-036 is the only next delivery: approved-batch
qualification and kernel continuity in disposable worktrees, with publication
blocked. The older milestone-4-first build order remains historical provenance,
not a current dependency order.

---

## §1 Introduction and Goals

### 1.1 The problem — `PROVISIONAL`, newly articulated 2026-08-03

Stated at four depths, because the shallow versions are true but do not justify a
product.

**Level one — agents misreport.** An agent says the tests pass when they do not.
Real, and merely annoying.

**Level two — bad code ships.** Also real, also not new. Software has shipped
broken since it existed.

**Level three — no one has held the code in their head.** Every line of
production software was historically, at some moment, reasoned about by a human
who could later be asked. That is no longer true. Organisations now own, ship and
carry liability for code no living person has ever thought about. Not *the author
left* — **there was no author.**

**Level four — the load-bearing one.** Every artefact by which an organisation
demonstrates that it was careful — tests, documentation, decision records, review
comments, commit messages, changelogs, postmortems, compliance narratives — can
now be generated by the same system that did the work, more cheaply than the care
those artefacts are supposed to evidence.

> **AI has made the evidence of care cheaper than care itself, and every
> institution that governs software runs on that evidence.**

Any signal that costs less to produce than the thing it signals stops being a
signal. This requires no one to act in bad faith: an honest team using AI honestly
produces artefacts indistinguishable from a dishonest team's. The result is a
market for lemons — the careful organisation can no longer signal its care, and is
therefore priced as though it were careless.

**Two concrete failures this predicts** — `PROVISIONAL`, and the legal and
regulatory mechanics below require verification against primary sources before
either is repeated publicly:

- **Diligence.** An acquirer reviews 400,000 lines, 94% coverage, a complete test
  suite passing, thorough decision records. The question *what does passing prove?*
  has no answer, because no one at the company wrote any of it. The company is
  repriced or the deal dies — not because the software is bad, but because it is
  **unprovable**, and to a buyer those are the same condition.
- **Liability.** After a loss, discovery asks who approved a change. A name
  appears in the log. That person approved forty thousand lines that week and
  could not have read them. The organisation's defence is that it had a process,
  and the opposing exhibit is the organisation's own documentation of a process it
  demonstrably did not follow. **Thorough governance documentation becomes
  evidence against its author.**

**Why this worsens as models improve — `PROVISIONAL`, and strategically load-bearing.**
Confidence is the proxy humans use for knowledge. A more capable model is more
confident and more persuasive, so it degrades that proxy faster. An organisation's
certainty rises while its correctness does not. Most AI development tooling is a
bet that current models are weak and is obsoleted by the next release. **Ranex is
a bet that models get strong**, and becomes more necessary with each capability
increase. If a single claim in this document is worth defending, it is this one.

### 1.2 What Ranex is — `PROVISIONAL`, restated in `3.0.0`; the bounded mechanism `CONFIRMED`

Ranex is **the gauge — and as of `3.0.0`, the restaurant that owns it.**

In the owner's words: **Ranex owns the restaurant.** It is the owner's assistant
for managing different restaurant chains. The kernel is **the library of
handbooks, manuals, rules and recipes** that every employee works from. Each
department has its own manager/supervisor and main worker.

Concretely: Ranex builds **its own harness** — a trimmed fork of opencode (MIT),
molded so that every workflow step calls the existing kernel: specify, freeze,
execute, measure, record, approve. The proven part (§15.1) is not discarded; it
becomes the spine. Orchestration is written in-house, its patterns learned from
oh-my-openagent — never its SUL-licensed code (§0.14). The Web UI is parked.

**The wall, restated for a producer and a gauge under one roof:** the harness
loop is model-driven; the kernel is code; they run as separate processes. Hooks
collect; the kernel judges — reads disk, holds keys, writes the journal, is the
only thing that stamps. If that wall falls, the restaurant grades its own dishes
— exactly the failure below.

The age has an abundance of ways to produce software — models, harnesses, skills,
tool servers, frameworks, agents — multiplying weekly, each shipping with its own
self-assessment. What does not exist is any fixed external standard that says
whether the output is good and that the producer cannot reach. Self-assessment is
precisely what a gauge exists to replace.

> **The age has infinite ways to produce software and no way to gauge it.**

**The thesis, stated so it can be falsified:**

> A verdict produced by a fixed target, set before the work, and scored by
> something the producer cannot alter, is worth more than any quantity of evidence
> the producer generates about itself.

`PROVISIONAL` as a product thesis. The determinism half is constructive and
`CONFIRMED` for the kernel: `evaluate()` is pure and imports no model client
(`src/ranex/governed_execution/domain/verdict.py:3-18,238-324`), and the suite
passes with no model credential present. The producer-cannot-alter-the-scorer
half is **closed for the bound command**: SLICE-046 confines it in the
qualified strict-local session and evidence signs only after fail-closed
confinement-result validation (`RISK-06` closed; ADR-006 accepted 2026-08-15).
The thesis is still not true without limit: the controller subprocess is
same-uid trusted infrastructure (ADR-023 standing limit) and the approver
remains an unauthenticated string (`RISK-07`). "True" and "someone will pay"
remain distinct; see `RISK-01`.

**What Ranex explicitly does not claim — `PROVISIONAL` policy, `CLAUDE.md`:**
it does not improve the quality of generated code, by any margin. Program output,
documentation and sales material must never suggest otherwise.

### 1.3 Stakeholder and concerns — `PROVISIONAL` owner statement, 2026-08-03

ISO/IEC/IEEE 42010 requires an architecture description to identify its
stakeholders and their concerns, and to address every concern. `2.1.0` had
neither, and `RISK-18` recorded the gap. This closes it.

**The stakeholder — one human operator running a team of AI agents.**

In the owner's words: *"I am a solopreneur and I run AI agents. This is the proof
that Ranex is built solely for that setup."* And on what "enterprise" means here:
*"An enterprise can have dozens of humans, but with Ranex there will be just one
operator and the rest is AI agents."*

Which yields the sentence this entire design turns on:

> **Enterprise governance works because different people check each other. When
> there is only one human, that check has to be code.**

Separation of duties in an organisation comes from headcount. **Ranex substitutes
code for headcount.** That is why the producer is the *agent* and the approver is
the *human*, why the agent's summary is discarded, and why the gauge must be
unreachable by the thing it measures. `tencent/hy3` raised and withdrew the
objection that an AI has no legal or moral agency: agency is irrelevant to this
separation — a CNC machine has none and still does not certify its own output.
The surviving limit is unchanged: the operator writes the gauge and nothing
checks the gauge. It also inverts `RISK-15`: "one implementer" is the **premise
the product exists to serve**.

*Team use* is named by the owner as possible and is explicitly **not** designed
for. No part is built for it; none is precluded.

**The concerns** — all four confirmed by the stakeholder, in his words:

| ID | Concern | What it means |
|---|---|---|
| `C-01` | **"It says done, it isn't"** | The agent reports success and the work is incomplete, broken, or never ran |
| `C-02` | **"Money gone, nothing finished"** | Hours and tokens spent on a run that loops, stalls or gives up, leaving something that can be neither finished nor discarded |
| `C-03` | **"It broke something else"** | The new work is fine but quietly damaged something that already worked, and nothing caught it because the agent tested only what it just wrote |
| `C-04` | **"I can't tell what it did"** | The change is too large to read, the summary is unreliable, and there is no way to see what actually happened to the codebase |

**Coverage accounting.** Every requirement in §1.4 was mapped against these four:

| Concern | Requirements serving it | Built |
|---|---|---|
| `C-01` | `PR-02`, `PR-03`, `PR-04`, `PR-05`, `PR-06`, `PR-10` | **Yes, mostly.** Seventeen closed slice documents; one withdrawn; none open |
| `C-03` | `PR-05`, `PR-06` — partially | **Weak.** The self-gate runs the full suite (SLICE-006, SLICE-009); no regression view yet |
| `C-04` | `PR-07`, `PR-08` | **No.** `PR-07` has an accepted design in ADR-016 but remains unbuilt; the translator is absent and `ranex journal verify` only checks integrity (`RISK-12`) |
| `C-02` | `PR-09` — one requirement | **Almost nothing.** SLICE-008's `task delegate` bounds a worker's wall clock and kills the whole process group at the bound; no budget, no escalation, no three-miss stop |

**Seventeen closed slices of work have gone to one of four concerns; one was
withdrawn before implementation and none is open.** This is coverage accounting, not
validation of the concern set or the method. The owner chose to continue
hardening `C-01` — see §11.6.

**The honest limit of this configuration.** Code can prove the agent did not
approve its own work. It cannot prove the human's gate was a *good* gate. The
operator writes the ruler and nothing else checks it, which is why calibration
(§8.4) carries disproportionate weight here compared with a multi-person setup.

### 1.4 Product requirements — `PROVISIONAL`, re-derived 2026-08-03

Re-derived against §1.2. `1.1.0`'s `PR-01` and `PR-07` were claims about aim and
efficiency and do not survive the thesis change. `PR-06`, `PR-07` and `PR-09`
below are new and come directly from the 2026-08-03 session.

| ID | Requirement | Serves | Status |
|---|---|---|---|
| `PR-01` | **A verdict can be re-derived by the operator — who did not write the work — from the record alone** | `C-01` `C-04` | `PROVISIONAL` — the record exists; no re-derivation has been performed. **Reframed in `2.2.0`**: `2.1.0` said "by someone who did not produce the work, offline," which was written for an acquirer who is not a stakeholder in this design |
| `PR-02` | No model output is ever an authorization. A gate passes on evidence or does not pass | `C-01` | `CONFIRMED` for the kernel path: `evaluate()` imports no model client, and the suite passes with no model credential present |
| `PR-03` | Absence blocks. A required claim with no satisfying evidence is `FAIL`, never a default and never a skip | `C-01` | `CONFIRMED` for the kernel |
| `PR-04` | **The identity that produces evidence cannot approve it — the *agent* produces, the *human* approves** | `C-01` | `CONFIRMED` as a string comparison; `UNRESOLVED` as a control, because `approver_id` is unauthenticated (`RISK-07`). A prior typed, authenticated, unrevoked, scope-authorized human decision is only a future boundary (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0017-record-resolved-owner-decisions.md:65-76`). |
| `PR-05` | Every verdict binds the exact subject digest it was measured against, so stale evidence stops counting automatically | `C-01` `C-03` | `CONFIRMED` — SLICE-001 and SLICE-004 |
| `PR-06` | **Every gauge carries a calibration result. An uncalibrated gauge yields no information and must not be reported as though it did** | `C-01` `C-03` | `PROVISIONAL` — `mutmut` is a calibration procedure and runs; nothing consumes its result as a gate, and 880 mutants survive |
| `PR-07` | **The record binds the full production configuration — model, harness version, skill and tool manifest, prompt digest — not the code alone** | `C-04` `C-02` | `PROVISIONAL` — accepted design in ADR-016, unbuilt; no treatment record exists. §5.5 |
| `PR-08` | A governed project's written records cannot silently drift from observable fact | `C-04` | `PROVISIONAL` — the mechanism exists in `tests/contract/test_docs_discipline.py`; not generalised |
| `PR-09` | **A run that cannot succeed stops within a bounded budget and asks the operator a product question, rather than continuing to spend** | `C-02` | `UNRESOLVED` — designed in `README.md`, no budget, no escalation, no worker to bound. **The only requirement serving `C-02`** |
| `PR-10` | Removing every model credential from the machine must not change a verdict | `C-01` | `CONFIRMED` for the kernel path |

Every requirement serves at least one concern, and every concern is served by at
least one requirement — the 42010 completeness criterion, met at this layer.
**The distribution is badly uneven** and §1.3 records by how much.

### 1.5 Major system capabilities — status as of 2026-08-09

| Capability | What it does | Status |
|---|---|---|
| Deterministic verdict | Gate + distinct subject-bound evidence + approver → verdict, no model consulted | **`CONFIRMED`** — `evaluate()` is a pure function; the future distinct-evidence proposal is outside the repository (`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:610-628`) |
| Subject-bound evidence | Evidence binds the digest of the committed tree it was measured against | **`CONFIRMED`** — SLICE-001 |
| Evidence authenticity | Ed25519 signature verified against a committed keyring before admission | **`CONFIRMED`** — SLICE-002 |
| Claim↔command binding | The committed catalog declares the argv that satisfies a claim | **`CONFIRMED`** — SLICE-003; six independent audits failed to break it |
| Hermetic observation | The bound command runs against a materialisation of the subject commit, in an environment built from empty, with a pinned toolchain | **`CONFIRMED`** — SLICE-004, closed twice |
| Append-only journal | Hash-chained SQLite, serialised appends and operator chain verification | **`CONFIRMED`** for append and `ranex journal verify`; it does **not** detect a removed consistent prefix (`README.md`, "Known gaps — stated plainly"; `RISK-19`) |
| Confinement of the measured party | The bound command cannot reach the key that signs its own measurement | **`CONFIRMED`** — ADR-006 accepted 2026-08-15; built through SLICE-017/018/019 and closed by SLICE-046 (ADR-023): the bound command runs in the qualified strict-local session and evidence signs only after fail-closed confinement-result validation (`RISK-06` closed, §11.5). Standing limit: the controller subprocess remains same-uid trusted infrastructure. The retained isolation profile is outside the repository (`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:961-975`) |
| Isolation profile | Read-only base, task-only writes, no secrets, isolated temp, denied-by-default network/egress, bounded resources/output, fresh namespaces and immutable argv | `PROVISIONAL` acceptance-test shape for ADR-006; test every denial (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:961-975`) |
| Calibration of the gauges | Demonstrating that a gate detects a predeclared known defect; freeze controls and disclose sample limits | `PROVISIONAL` — `mutmut` and `diff-cover` run; no negative control or consuming gate (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:630-642) |
| Worker dispatch | Accept an immutable packet and handoff, grant only declared capabilities/configuration, then inspect disk rather than a summary | **`CONFIRMED`** for the retained serial kernel path — SLICE-008 and SLICE-010 built `ranex task dispatch/judge/merge`; the separate delegated first rung and bounded pool remain historical prototype mechanics. Current `fanout` is free-prompt JSONL convenience/prototype, not release authority; the approved-batch qualification is the only retained next delivery in #19/SLICE-036. |
| Background worktree agent manager | Durable supervisor + capability-gated orchestrator over N agents in one harness process, each in its own worktree: per-member bridge (`ADR-014`), durable run/task/member schema, leases and recovery, verification, kernel-governed merge handoff | `UNRESOLVED` — `ADR-014` `proposed` (the bridge); manager issues #1-#9 on this repository, renumbered SLICE-060-068 on 2026-08-17 (ADR-014 predates the renumbering and cites the old numbers); nothing built. SLICE-010 is satisfied, but the manager is parked until the ADR-015 durability production program closes. §0.15 |
| Durable execution and recovery | Provider watchdog, post-crash reconciler, durable retry, durable blockers, Session-ID fencing — the harness must not hang forever or strand running work | `ADR-015` **accepted 2026-08-07**. Two of five claims are in production: SLICE-012 provider watchdog and SLICE-013 reconciler hoist plus startup sweep, on harness default branch tip `9eeda0bf5d21...` (feature commits `23d6a5b4ee...` and `a8bc7bdf35...`). Durable retry is next; durable blockers and Session-ID fencing remain. The known fencing hazard is that the DB-global startup sweep can interrupt another process, so fencing must close it before multi-process use. The disposable prototype is green and digest-bound but ships nothing. §0.16, §0.20 |
| A/B/C specification authority | Normative A holds approved semantics without generated hashes; manifest B binds exact gauge artifacts/invocation; signed envelope C binds A+B, context, identities, anti-replay and capability request; grant binds C | **`CONFIRMED` kernel substrate** — SLICE-029–033 and SLICE-035 built canonical contracts/vectors, lifecycle, projections, approval/revocation/intersected grants, trace integrity and real-subject bootstrap. The installed harness-admission/concurrent-mutation composition is withdrawn from the kernel-only release, not completed by SLICE-044. |
| Canonical authority roles | Store only eight canonical role IDs; presentation aliases never carry authority | `UNRESOLVED` — only if authority or dispatch is added: `duty-orchestrator`, `project-supervisor`, `planner`, `implementation-worker`, `process-reviewer`, `outcome-reviewer`, `adversarial-reviewer`, `human-governor` (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:700-712`) |
| Rich verdict vocabulary | `PASS`, registered `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, `CHECKER_FAULT`; blocking work fails closed except proven inapplicability | `UNRESOLVED` — kernel has only `PASS`/`FAIL` (`src/ranex/governed_execution/domain/verdict.py:24-26`; outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:353-378`) |
| Independence record | Record distinct execution identity, no evaluator edit or maker rationale, exact commit/packet, and where needed model family plus locked test/hidden key | `UNRESOLVED` — fresh session is not independent evidence; only no-self-approval exists (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:736-756`) |
| Budget and escalation | Bounded spend, three misses, plain-language question to the owner; cancellation first denies new capability, records unknowns and cannot widen cleanup authority | `UNRESOLVED` — designed, never built; never silently downgrade a required gate (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/ocask-alignment-research-2026-07-27.md:1641-1654`; `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/AI_AGENT_FLEET_CONTROL_PLANE.md:426-438) |
| Intake, pseudocode, flow and tests | Human/AI clarification → canonical packet → generated pseudocode/flowchart → acceptance or characterization tests with oracle provenance | **`CONFIRMED` for kernel lifecycle and deterministic closed-DSL projections** — SLICE-030/031; no owner-facing clarification/intake product or installed end-to-end composition exists, and source/runtime observation cannot promote itself to intent |
| Configuration comparison | Which model, harness and skill set actually finishes work, measured | `PROVISIONAL` — ADR-016 accepted 2026-08-09; prototype not opened; composition UNPROVEN |

**Honest summary:** the verdict path and kernel-side A/B/C authority substrate
exist and are tested. Real delegation and kernel merge have happened, but the
full product loop has not closed: owner-facing intake, common harness effect
admission, governed concurrent mutation, and bounded escalation remain.

---

## §2 Constraints

### 2.1 Binding — `PROVISIONAL`

| Constraint | Source |
|---|---|
| Python is the implementation language | repository |
| `uv` is the toolchain manager; `[tool.uv] package = false`, so no console script is installed | `pyproject.toml` |
| One slice at a time; no slice without a researched ADR | `CLAUDE.md`, enforced by contract test |
| Research must vendor pinned third-party source with origin and licence | ADR-003, enforced by contract test |
| The docs layer is capped to a fixed set of allowed documents | `CLAUDE.md`, enforced by `tests/contract/test_docs_discipline.py` |
| `diff-cover` at 100% on changed lines; `mutmut` before a slice closes | SLICE-004 |
| Licence is MIT | `README.md` |
| Hermes is not a base; removed 2026-08-01 after an audit measured zero contribution. It and OpenClaw are feature quarry under §15.3, never a base | `CLAUDE.md`, git `d9db059e98` |
| The harness is a fork of opencode at a pinned commit; the fork point and trim list are recorded in its ADR; MIT attribution preserved | owner decision 2026-08-03 |
| oh-my-openagent is patterns-only: its code is SUL-1.0 (internal use only, no commercial distribution, derivative works included) and never enters this tree, converted or not | owner decision 2026-08-03 |
| **Inherited ADR-0008:** frozen tests, red-then-green, and no maker approval | Still binding; its cycle-record/tier machinery is not (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:20`) |
| **Inherited ADR-0014:** Python, with a measured rather than fashionable performance escape | Still binding (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md:91`) |
| **Inherited ADR-0019:** `uv` is the toolchain manager and command runner | Still binding (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0019-declare-uv-as-the-python-toolchain-manager.md:50`) |

### 2.2 Process constraints — `PROVISIONAL`

- **One slice open at a time.** Opening a second is the named failure mode.
- **No slice without an ADR**, written before the slice file exists.
- An ADR citing no working code is an opinion, and this is enforced by test.
- Never weaken a test, checker, baseline or policy to make work pass.

### 2.3 Environmental — `PROVISIONAL`

- Local-first. No hosted service exists and none is planned this horizon.
- Ranex becomes **Linux-only in fact** once confinement lands, and will refuse
  below Landlock ABI 6. Taken deliberately; ADR-006 records it as a cost.
- A hermetic tree has no installed dependencies, so only self-contained commands
  can be gated — in every language, not only Python.
- Single developer, no second implementer. See `RISK-15`.

---

## §3 Context and Scope

### 3.1 System context — `PROVISIONAL`

```
   ┌────────────┐        intent, decisions        ┌──────────────────┐
   │   Owner    │────────────────────────────────▶│                  │
   │(non-tech.) │◀────── plain-language state ────│                  │
   └────────────┘                                 │      RANEX       │
                                                  │   the gauge      │
   ┌────────────┐   diff on disk + evidence       │                  │
   │  Harnesses │────────────────────────────────▶│  freeze · run    │
   │ (bought,   │◀──── frozen target, bounded ────│  measure · record│
   │  not built)│      budget, no summary read    │  refuse          │
   └────────────┘                                 └────────┬─────────┘
                                                           │
   ┌────────────┐                                          │
   │  Outsiders │◀──── a record they can check without ────┘
   │ acquirer,  │      trusting the party that produced it
   │ insurer,   │
   │ regulator  │
   └────────────┘
```

The third box is new in `2.0.0` and follows from §1.1. A record only the producer
can read is a diary. See `RISK-03`.

### 3.2 Scope boundary — `PROVISIONAL` policy

**In scope:** fixing the target before the work; measuring the result with code;
binding the measurement to an exact subject; recording it so an outsider can check
it; calibrating the instruments that do the measuring; refusing when any of these
cannot be done honestly — **and, as of `3.0.0`, the harness itself**: a trimmed
opencode fork with the kernel as its operational spine, delegation from foreman
through department supervisors to workers, and the kernel handbook.

**Explicitly not:**

- **Model output as authority.** The harness uses models to work; nothing a model
  says is a verdict, an approval, or a control decision. The kernel never asks a
  model what to do next.
- **A harness built on code it cannot own.** opencode is forked under MIT and
  trimmed; hermes-agent was audited and rejected as a base; oh-my-openagent's
  code can never be copied in (§2.1).
- A general-purpose assistant, a prompt library, or a model-inference business.
- A claim about the quality of generated code (§1.2).

---

## §4 Solution Strategy

### 4.1 The doctrine — `PROVISIONAL`, articulated 2026-08-03

Ranex imports a solved discipline rather than inventing one. The industrial
factory's innovation was not mass production; it was **interchangeable parts**,
and interchangeable parts required something that had to exist before any part was
made: **the gauge**.

Before it, every musket was hand-fitted and a broken part meant finding a
gunsmith. The armory system stopped asking whether the craftsman was skilled and
started asking whether the part passes a fixed standard the maker cannot alter.

| Factory concept | Meaning | Ranex | Status |
|---|---|---|---|
| **Go/no-go gauge** | Fixed tolerance, mechanical check, precedes production | Frozen tests + gates | **specified** |
| **Interchangeable parts** | Any supplier's part fits | Model and harness swappable behind a port | designed |
| **Poka-yoke** | The defect is made impossible, not caught later | Tests read-only to implementers; no self-approval | **specified** |
| **Jidoka / andon** | The machine stops itself on a defect; anyone may halt the line, and halting is correct | Three misses → escalate a product question to the owner | designed |
| **The traveler** | The card that rides with the part, stamped at every station. **An unstamped part does not ship** | The journal plus signed evidence | **built** |
| **Incoming inspection** | Check what suppliers send before it enters the line | Digest the model, harness and skill manifest | **missing** — `PR-07` |
| **Calibration lab** | The gauges are themselves measured, on a schedule, against a reference | `mutmut` as calibration; negative controls | partial |
| **Statistical process control** | Measure the process, catch drift before it makes scrap | Cross-run comparison of configurations | **missing** |
| **Bill of materials** | Every part, its provenance, its spec | `governance/bom.yaml` | **built** |

The traveler is the most useful reframing available for the journal: it carries
its own rule, and a non-technical buyer understands *an unstamped part does not
ship* instantly, where *hash-chained append-only log* means nothing.

### 4.2 Why every prior software factory failed, and why that failure does not transfer — `PROVISIONAL`

"Software factory" is a burned term. It has been attempted publicly and failed —
CASE tooling, model-driven architecture, and the 2004 *Software Factories*
programme, among others. *(These specifics are recalled, not verified. They must
be checked against primary sources before use in any public material.)* To an
experienced engineer the phrase reads as a discredited idea, which is a real cost
of adopting it.

The argument that the failure does not transfer:

> Every previous attempt industrialised **production** — generating the
> implementation, assembling from components — but production was never the
> constraint. Knowing what to write, and knowing whether it was right, were.
> **AI has moved the constraint.** Writing code is now nearly free; specification
> and verification are what remain scarce. A factory is, at its core, a machine
> for verification at scale.

**Prior software factories industrialised the wrong step. Ranex industrialises
inspection, which is the step that just became scarce.** `PROVISIONAL`, but it
survives the obvious objection, which is more than the `1.1.0` thesis managed.

### 4.3 Ranex owns the factory; the inspection room stays locked inside it — `PROVISIONAL` policy, restated in `3.0.0`

`2.8.0` placed Ranex outside the factory: the quality system, never the machine
tools. `3.0.0` takes the owner's decision to own the whole restaurant — and keeps
the only part of that old framing that was load-bearing: **the inspection room
stays locked.**

**The machine tool is now owned, not bought — with one exception.** The harness
is Ranex's own fork of opencode: trimmed, molded, and maintained here, pinned to
an upstream commit for as long as rebasing stays cheaper than owning the diff.
**The models stay bought.** Providers are swappable behind the harness's routing;
the answer to *which model should I use* is still **measure it** (§11.3).

Three consequences, restated:

1. A quality system that also runs the machines is still a quality system **only
   while the two are walled**: harness and kernel are separate processes; the
   loop is confined from the keys and the journal; the verdict is produced by the
   kernel alone. Without the wall, this is the failure §1.1 describes, now
   in-house.
2. The harness produces the work; **the kernel produces the only stamp that ships
   a part.**
3. Forking the machine tool is a cost, recorded: upstream opencode moves fast,
   and the trim must stay small enough to rebase — or Ranex silently acquires a
   second codebase to maintain, which is the 561-files failure in code form.

### 4.4 Strategy decisions — `PROVISIONAL`, updated `3.0.0`

Deterministic over probabilistic enforcement; fail-closed, where `NOT_ASSESSED`
is never a pass; evidence bound to exact subject digests; separation of producer
and approver; containment over control — now applied inward: the harness loop is
confined from the keys and the journal, and is judged by what it leaves on disk.
Local-first before anything distributed.

**The phasing (owner, superseded 2026-08-09):** the trimmed fork, first
delegation and kernel merge exist. The next and first-priority feature is
the ADR-017 program: confinement (SLICE-017–019 plus SLICE-046's `cmd_run`
binding, closed 2026-08-12..15), then sequential SLICE-029..044 for
approved specification → governed implementation → deterministic real result.
ADR-006 confinement is accepted and closed. Durability,
background management, measurement, handbooks and Web UI stay parked or
background-only unless a bounded part is required for the P0 exit.

### 4.5 What we take from TOGAF, and what we refuse — `PROVISIONAL`, new in `2.1.0`

**The positioning claim: Ranex automates the conformance-checking part of ADM
Phase G, with code instead of a review board.**

TOGAF's Phase G — Implementation Governance — exists to ensure conformance with
the Target Architecture by the projects implementing it. Its instrument is the
**Architecture Contract (signed)**; its output is a **Compliance Assessment**.
The human still authors the target and approves; judgment about whether the
target is right never leaves the human. Enterprises legitimately use delegated
assurance and sampling; Ranex automates only the deterministic conformance check.

`tencent/hy3` withdrew its substantive objection to this positioning. TOGAF
named the loop and left the checking to humans; Ranex does the checking with code.
This is the most credible sentence available to an enterprise buyer, because it
names an acknowledged weak point rather than inventing a category. `UNRESOLVED`
as market positioning — never tested on a buyer (`RISK-04`).

**Adopted — four parts, and nothing else:**

| TOGAF part | What it gives Ranex |
|---|---|
| **Architecture Contract** | The frozen, signed task envelope. Half-built already: signed evidence and claim↔command binding are its mechanics |
| **Baseline / Target / Gap / Roadmap / Transition Architectures** | The vocabulary for §5.5. Where we are, the finish line, the parts, the order, and intermediate states that each deliver value |
| **ABB vs SBB** — Architecture Building Block (capability needed) vs Solution Building Block (what implements it) | The buy/build column, made rigorous. An ABB with no SBB is an unfilled part |
| **Requirements Management as the hub, not a phase** | It sits at the centre of the ADM and every phase touches it. This is the layer §0.2 records as missing |

**Refused, and one of them actively:**

Discarded as enterprise-scale overhead with no second consumer here: the four
architecture domains, the Enterprise Continuum, TRM and III-RM, the Skills
Framework, and the Architecture Board / Chief Architect / Domain Architect
hierarchy.

**Reject a graded pass scale; adopt a rich diagnostic outcome taxonomy.** A scale
where partial compliance passes is incompatible with absence-blocks: it turns
"mostly compliant" into a pass. But binary pass/fail is equally theatrical when
the gate is trivial — the calibration argument from the other direction. The
pre-reset corpus already proposed the correction that this map argued against:
`PASS`, registered `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, and
`CHECKER_FAULT`. Everything except proven `NOT_APPLICABLE` blocks: fail-closed
and diagnostic, not graded. The current kernel has only `PASS` and `FAIL`
(`src/ranex/governed_execution/domain/verdict.py:24-26`).

**Why the adoption is this narrow — evidence, not preference.** The pre-reset
tree already contained a faithful TOGAF-shaped apparatus: a core SDLC operating
model, a 2,172-line control catalog, 34 bounded contexts, 21 readiness gates in
two non-compensating tiers, 41 capabilities levelled 0–4 and every one
`NOT_ASSESSED`, compliance assessments and a governance log. It produced **561
files and zero product code.** The failure was structural, not a lapse of
discipline: **TOGAF's overhead is amortised across an enterprise, and there is
one implementer here.** Every ADM artifact assumes a different person consumes
it; when author and audience are the same person, the artifact is pure cost.
Tracked as `RISK-17`.

---

### 4.6 The gauge must be applied to the part — `PROVISIONAL`, owner, 2026-08-04

The gauge metaphor has a hole we walked into ourselves, and it is the one that
matters most now that generation is cheap.

**A gate that binds a claim to an argv measures that the command exited zero. It
does not measure that anything real was exercised.** Measured on 2026-08-04: a
test asserting `False` — a guaranteed failure — was marked skipped; pytest
reported `1 skipped` and exited `0`. A gate bound to `uv run pytest -q` accepts
that as satisfying evidence. This repository is currently exposed to it: on a
machine without the pinned resolver our own real-world journey skips every stage
and the suite still exits zero.

The dart metaphor names it exactly. We stopped the thrower painting the bullseye
around the dart *after* it lands. We did not stop it painting the bullseye around
a **drawing of the target** — a suite of mocks that never starts the product,
or a suite that skips itself into silence. The part was never offered to the
gauge, and the traveler got stamped anyway.

**The requirement, stated as product policy:** evidence must come from executing
the real product the way a person uses it, before a person does. Cheap
generation makes this sharper, not softer — code arrives faster than anyone can
read it, so the only affordable review is the one that runs it for real.

What the kernel can enforce **deterministically**, without any model judging
whether a test is "realistic":

| Control | What it refuses |
|---|---|
| A skip is absence, not success | a green suite where the real stages never ran |
| The product's own entry point must be observed spawning | a suite of mocks satisfying a claim about real use |
| Distinct claims for distinct things — `tests-executed` vs `product-exercised` | one command standing in for both |
| Assertion strength, already measured by `mutmut` | tests that run but cannot detect any change |

Empirical support, recorded because it is unusually clean. SLICE-006 found six
defects. **Every one came from running the real system; none came from unit
tests, and none appeared in ADR-007's twenty-row sad-path table** — a list
written specifically to anticipate failure. Unit tests confirmed what had already
been imagined; real runs found what had not. A seventh followed immediately: the
`README` walkthrough no longer works for a new operator, which no test starting
from a configured fixture can see.

**The boundary this must not cross.** None of it improves the model's aim, and no
document or program output may say otherwise. Fixing the contract before the
throw is ours to do; making the thrower better is not, and never was. What
changes here is only *where the target is nailed up*: on the real product, not on
a convincing picture of it.

### 4.7 P0: approved specification before implementation — `PROVISIONAL`, owner, 2026-08-09

The first feature now closes the whole missing thread:

```text
human idea → clarify → canonical TaskPacket → generated views/tests
               │                 │
               └─ blockers? stop └─ human approves exact digest
                                      │
                                      ▼
kernel grant → harness admission → parallel worktrees → verify → kernel merge
```

ADR-017 is the program authority; this map routes its sequential build. A is
normative SpecPacket/task scope with approved semantics
but no generated hashes. B hashes exact rendered and protected gauge bytes,
fixtures, checkers, invocation, expected values, baseline and controls. C signs
A+B plus context, identity, anti-replay and capability request; the grant binds
C. Mechanical tests compile only from a closed DSL; other semantic oracles are
approved in A. Pseudocode, flow and clause sidecars are derived views. Stable
question, rule, transition, outcome, error, test and mapping IDs make drift
machine-detectable. The deterministic default covers every changed in-scope
source hunk/symbol; “behavior-bearing” is not a worker-chosen category. Each has
a language-appropriate generated trace comment, or approved sidecar, naming
exact rule/transition/outcome IDs and the projection digest. Only generated,
vendor, docs or explicitly nonbehavioral classes enumerated in A/B with exact
paths/reasons and signed in C are exempt; changing that list revokes. Missing,
stale, duplicate or uncovered anchors refuse. Comments/sidecars prove only
coverage and staleness; executable approved outcomes remain the semantic oracle.

The kernel owns lifecycle, approval, revocation, capability issue, journal,
evidence continuity, verdict and merge. The harness owns a shared effect
admission service that enforces exact executable/argv/cwd, roots, actions,
environment, network, secret, commit and subagent bounds. An approved batch
binds the parent/C and base digests, dependency DAG, exact pairwise-disjoint
path+action scopes, isolated worktrees, frozen child tests/evidence, retries and
maximum pool. Each child receives only parent ∩ request and no secret/merge;
one integrator orders results canonically and the kernel publishes by CAS. A
changed normative, test, exemption, policy, generator, harness or base digest
revokes parent and descendants.

The future-slice DAG is logical; current execution stays sequential:

```text
017 host/build/launcher → 018 lifecycle → 019 host-qual evidence → 046 cmd_run/attacks ─┐
019 → 029 A/B/C contracts                                      │
       ├─ 030 lifecycle/clarification ──> 032 approval/grants   │
       ├─ 031 closed-DSL projections                           │
       ├─ 033 trace/verifier ports                             │
       ├─ 034 harness admission service                        │
       └─ 035 real subject/bootstrap lane                      │
019 + 030..033 + 035 ──> 036 qualification-only approved batch <───┘
034 + 036 ─┬─> 037 core process/fs/Git/output effects
            ├─> 038 Ranex tool/session/Git/worktree/PR effects
            ├─> 039 PTY/process-handler effects
            ├─> 040 MCP/auth/OAuth effects
            ├─> 041 plugin/provider network effects
            └─> 042 storage/database effects
019 + 029..042 ──> 043 serialized all-leaf/judge/merge/CAS integration
043 ──> 044 both real-provider journeys + concurrent attack exit
```

| Slice | Planned exact ownership | Frozen input → output | Deterministic gate | Real E2E contribution |
|---|---|---|---|---|
| `017` closed 2026-08-12 / issue #10 | `src/ranex/cli/host_confinement.py`<br>`native/ranex-worker-launcher/launcher.c`<br>`governance/confinement/native-launcher-build-v1.json`<br>`governance/confinement/strict-local-host-v1.json`<br>`tests/security/test_slice017_host_qualification.py`<br>`tests/integration/test_slice017_native_launcher.py` | ADR-006 host/build contract → installed real launcher + qualified/refused host report | two clean builds byte-equal; same-FD real probe; delegated-cgroup acquisition/readback; absence refuses | establishes no production execution path |
| `018` closed 2026-08-14 / issue #21 | `src/ranex/cli/host_confinement.py`<br>`native/ranex-worker-launcher/launcher.c`<br>`governance/confinement/native-launcher-build-v1.json`<br>`governance/confinement/strict-local-host-v1.json`<br>`governance/confinement/strict-local-v1.json`<br>`tests/security/test_slice018_cgroup_output_lifecycle.py`<br>`tests/integration/test_slice018_confinement_session.py` | qualifying 017 artifact/report + closed command descriptor → unsigned `ConfinementResult` | real namespaces/Landlock/seccomp; gate/readback/kill/drain/safe-output attacks | proves service with real processes, no `cmd_run` or signing |
| `019` closed 2026-08-13 / issue #22 | `src/ranex/cli/main.py`<br>`src/ranex/cli/host_confinement.py`<br>`tests/security/test_slice019_bound_command_confinement.py`<br>`tests/integration/test_slice019_confinement_cli.py`<br>`tests/security/test_slice004_hermetic_observation.py`<br>`tests/security/test_executable_path_confinement.py`<br>`tests/security/test_repository_confinement.py`<br>`tests/e2e/test_run_produces_evidence.py`<br>`tests/contract/test_kernel_unchanged.py` | existing `cmd_run` descriptor + 018 result → complete evidence or refusal | installed-CLI theft/survivor/layer/field mutations; honest repetition; byte guard | closed as host-qualification gate evidence (ADR-021); `cmd_run` binding and RISK-06 closure moved to SLICE-046 (ADR-023), closed 2026-08-15 |
| `029` / issue #12 | `governance/schemas/specification/spec-packet-v1.schema.json`<br>`governance/schemas/specification/generated-artifact-manifest-v1.schema.json`<br>`governance/schemas/specification/approval-envelope-v1.schema.json`<br>`tests/contract/fixtures/specification/abc-v1-vectors.json`<br>`packages/schema/src/specification.ts`<br>`packages/schema/test/specification.test.ts` | ADR-017 A/B/C → frozen cross-language vectors | byte-identical canonical digests/errors | identity/manifest vocabulary for exit |
| `030` / issue #13 | `src/ranex/governed_execution/domain/specification.py`<br>`src/ranex/governed_execution/application/specification.py`<br>`src/ranex/cli/specification.py`<br>`tests/unit/test_specification_lifecycle.py`<br>`tests/integration/test_specification_cli.py` | 029 ports → clarification/lifecycle results | every transition/refusal/identity guard | drives real human approval-pending |
| `031` / issue #14 | `src/ranex/specification_generation/__init__.py`<br>`src/ranex/specification_generation/scenario.py`<br>`src/ranex/specification_generation/projection.py`<br>`tests/unit/test_specification_generation.py`<br>`tests/contract/fixtures/specification/projection-v1-vectors.json` | A + 029 ports → pseudocode/flow/B or refusal | closed-DSL goldens; prose cannot invent tests | protected gauges/views for both repos |
| `032` / issue #15 | `src/ranex/governed_execution/domain/specification_approval.py`<br>`src/ranex/governed_execution/domain/specification_events.py`<br>`src/ranex/governed_execution/application/specification_approval.py`<br>`tests/unit/test_specification_approval.py`<br>`tests/unit/test_specification_child_grants.py`<br>`tests/integration/test_specification_revocation.py` | 029+030 → C/revocation/child-grant events | replay/expiry/key separation/intersection | exact grants used by concurrent agents in 044 |
| `033` / issue #16 | `src/ranex/governed_execution/domain/specification_trace.py`<br>`src/ranex/governed_execution/application/specification_verification.py`<br>`tests/unit/test_specification_trace.py`<br>`tests/integration/test_specification_verification.py` | A/B + candidate → structured trace/outcome facts | every changed in-scope source hunk/symbol has exact IDs+digest; only A/B-enumerated, C-signed generated/vendor/docs/nonbehavioral exact-path exemptions; missing/stale/duplicate/uncovered/refusal and executable outcome controls | trace facts for integration, never marker semantic proof |
| `034` / issue #17 | `packages/core/src/tool/specification-admission.ts`<br>`packages/core/test/tool/specification-admission.test.ts`<br>`packages/ranex/src/control-plane/specification-admission.ts`<br>`packages/ranex/test/control-plane/specification-admission.test.ts` | 029 request/grant fixtures → allow/deny/event port | request/revoke vectors and bypass baseline | shared service only; leaf wiring waits for 037..042 |
| `035` / issue #18 | `tests/e2e/specification/subjects.py`<br>`tests/e2e/specification/ranex-subject-v1.json`<br>`tests/e2e/specification/arxic-subject-v1.json`<br>`tests/e2e/test_specification_subject_bootstrap.py` | pinned repos/issues/locks/credential refs → credential-free bootstrap/process helpers | commit/licence/issue/lock/argv checks; credential broker failure blocks; no provider skip | real Ranex #10 and Arxic #109 subjects |
| `036` / issue #19 | `governance/schemas/specification/approved-batch-v1.schema.json`<br>`src/ranex/governed_execution/domain/specification_batch.py`<br>`src/ranex/governed_execution/application/specification_batch.py`<br>`src/ranex/cli/fanout.py`<br>`src/ranex/cli/main.py`<br>`tests/contract/fixtures/specification/approved-batch-v1-vectors.json`<br>`tests/integration/test_specification_batch_qualification.py` | A/B/C + approved child-request JSONL + base → canonical ready/result sets and child evidence in disposable worktrees | exact planned CLI grammar; ready-set dependencies; disjoint path+action scopes; parent ∩ child; pool only narrows; retries invariant; result order canonical; all merge/publish paths refuse | qualification only; cannot publish or authorize production fanout |
| `037` / issue #20 | `packages/core/src/tool/tool.ts`<br>`packages/core/src/tool/registry.ts`<br>`packages/core/src/tool/bash.ts`<br>`packages/core/src/process.ts`<br>`packages/core/src/cross-spawn-spawner.ts`<br>`packages/core/src/filesystem.ts`<br>`packages/core/src/filesystem/**`<br>`packages/core/src/fs-util.ts`<br>`packages/core/src/file-mutation.ts`<br>`packages/core/src/git.ts`<br>`packages/core/src/ripgrep.ts`<br>`packages/core/src/ripgrep/binary.ts`<br>`packages/core/src/tool-output-store.ts`<br>`packages/core/test/control-plane/specification-core-effects.test.ts` | 034 service + 036 grants → admitted core local effects | direct process/fs/mutation/Git/worktree/tool-output bypasses deny; omitted callers prove routing through these revalidated services | closes core effect family only |
| `038` / issue #23 | `packages/ranex/src/index.ts`<br>`packages/ranex/src/session/tools.ts`<br>`packages/ranex/src/session/processor.ts`<br>`packages/ranex/src/session/prompt.ts`<br>`packages/ranex/src/tool/**`<br>`packages/ranex/src/git/index.ts`<br>`packages/ranex/src/worktree/index.ts`<br>`packages/ranex/src/control-plane/adapters/worktree.ts`<br>`packages/ranex/src/cli/cmd/pr.ts`<br>`packages/ranex/src/format/index.ts`<br>`packages/ranex/src/installation/index.ts`<br>`packages/ranex/src/project/project.ts`<br>`packages/ranex/src/snapshot/index.ts`<br>`packages/ranex/test/control-plane/specification-local-effects.test.ts` | 034 service + 036 grants → admitted Ranex local effects | tool/gh/Git/worktree/CLI-PR and direct formatter/install/project/snapshot process attacks; no direct commit, branch, checkout or child-task bypass | closes local harness effects only |
| `039` / issue #24 | `packages/core/src/pty.ts`<br>`packages/core/src/pty/**`<br>`packages/server/src/handlers/pty.ts`<br>`packages/server/src/pty-environment.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/groups/pty.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/handlers/pty.ts`<br>`packages/ranex/src/server/shared/pty-ticket.ts`<br>`packages/ranex/src/plugin/pty-environment.ts`<br>`packages/ranex/test/control-plane/specification-pty-effects.test.ts` | 034 service + 036 grants → admitted PTY/process effects | create/write/resize/kill/env/ticket and direct-handler bypass attacks | closes PTY family only |
| `040` / issue #25 | `packages/core/src/oauth/page.ts`<br>`packages/core/src/credential.ts`<br>`packages/server/src/handlers/credential.ts`<br>`packages/ranex/src/auth/index.ts`<br>`packages/ranex/src/mcp/**`<br>`packages/ranex/src/cli/cmd/mcp.ts`<br>`packages/ranex/src/server/auth.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/groups/mcp.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/handlers/mcp.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/middleware/authorization.ts`<br>`packages/ranex/test/control-plane/specification-mcp-auth-effects.test.ts` | 034 service + reference-only secret IDs → admitted MCP/auth/OAuth calls | local/remote MCP spawn, browser/callback/OAuth and auth-read attacks; no token/env/FD reaches child | closes MCP/auth family only |
| `041` / issue #26 | `packages/core/src/plugin.ts`<br>`packages/core/src/plugin/**`<br>`packages/core/src/provider.ts`<br>`packages/core/src/models-dev.ts`<br>`packages/core/src/github-copilot/**`<br>`packages/ranex/src/plugin/**`<br>`packages/ranex/src/provider/**`<br>`packages/ranex/src/session/llm.ts`<br>`packages/ranex/src/session/llm/**`<br>`packages/ranex/src/session/message-v2.ts`<br>`packages/ranex/src/cli/network.ts`<br>`packages/ranex/src/cli/cmd/github.handler.ts`<br>`packages/ranex/src/cli/cmd/import.ts`<br>`packages/ranex/src/cli/cmd/providers.ts`<br>`packages/ranex/src/cli/cmd/run.ts`<br>`packages/ranex/src/cli/tui/worker.ts`<br>`packages/ranex/src/control-plane/dev/debug-workspace-plugin.ts`<br>`packages/ranex/src/lsp/server.ts`<br>`packages/ranex/src/server/server.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/groups/provider.ts`<br>`packages/ranex/src/server/routes/instance/httpapi/handlers/provider.ts`<br>`packages/ranex/test/control-plane/specification-network-effects.test.ts` | 034 service + 036 grants → admitted plugin/provider network calls | raw fetch/socket/dynamic-provider/plugin-hook/CLI/server bypass inventory and host/method/body/credential-scope attacks | closes direct network family only |
| `042` / issue #27 | `packages/core/src/database/**`<br>`packages/core/src/account/sql.ts`<br>`packages/core/src/credential/sql.ts`<br>`packages/core/src/event/sql.ts`<br>`packages/core/src/permission/sql.ts`<br>`packages/core/src/project/sql.ts`<br>`packages/core/src/session/sql.ts`<br>`packages/core/src/share/sql.ts`<br>`packages/core/src/control-plane/workspace.sql.ts`<br>`packages/core/src/data-migration.sql.ts`<br>`packages/ranex/src/storage/**`<br>`packages/ranex/test/control-plane/specification-storage-effects.test.ts` | 034 service + 036 grants → admitted storage transaction | create/update/delete/migrate/path/rollback attacks; omitted repositories prove routing through revalidated DB/storage services | closes storage family only |
| `043` / issue #28 | `src/ranex/cli/main.py`<br>`src/ranex/cli/delegation.py`<br>`src/ranex/cli/fanout.py`<br>`src/ranex/governed_execution/adapters/persistence/sqlite/journal.py`<br>`tests/integration/test_specification_continuity.py`<br>`packages/ranex/test/control-plane/specification-effect-inventory.test.ts`<br>`packages/ranex/test/control-plane/specification-integration.test.ts` | 030..042 ports/effects → serialized A/B/C/grant/evidence/judge/merge chain | every direct primitive classified; every omitted caller dynamically proves admitted service route; digest/identity/exemption/crash/bypass substitution refuses before single-writer stale-base CAS | sole serialized all-leaf integration owner |
| `044` / issue #29 — withdrawn 2026-08-25 | `tests/e2e/test_specification_program_exit.py`<br>`docs/slices/SLICE-044-approved-specification-program.md`<br>`docs/slices/done/SLICE-044-approved-specification-program.md`<br>`docs/slices/done/SLICE-044-approved-specification-program.exit-record.json`<br>`docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md`<br>`docs/adr/ADR-017-approved-specification-before-implementation-authority.md`<br>`docs/MAP.md`<br>`docs/STATE.md`<br>`README.md` | historical installed-composition/real-provider exit design | withdrawn from the kernel-only release; no production fanout authorization | not a current delivery gate |
| `059` historical implementation / issue #39 withdrawn 2026-08-25 | `tests/e2e/test_task_real.py`<br>`tests/e2e/test_delegation_real.py`<br>`tests/e2e/expected/task-dispatch-judge.out`<br>`tests/e2e/expected/task-merge-refusal.out`<br>`tests/e2e/expected/delegation-diff.out`<br>`docs/slices/done/SLICE-059-real-e2e-task-family.md` | retained as historical task-family test work, but withdrawn from the kernel-only release; its real-provider/production closure claim is not accepted | prior artifacts remain evidence records only; no G-4/G-5 release claim and no fanout authorization | not a current delivery gate; #19/SLICE-036 is the only retained next slice |

Rows 037–044 remain historical planned-contract records only; the owner
withdrew that harness-effect and production-exit program on 2026-08-25. No
slice document is open: 017, 018, 019, 020 and 046 are archived in
`docs/slices/done/`. A future slice document is created when it opens, after
its prerequisites and predecessor close. Slices 018/019 are serial;
030/031/033/034/035 are historical logically parallel-ready records; #19 /
SLICE-036 is the only retained next delivery and runs one slice at a time with
publication blocked. Issues #20 and #23..#29 mirror withdrawn work and are not
current release gates.
Mock/synthetic/unit tests support a slice but cannot close the milestone or
either real journey.

The effect inventory is closed, not illustrative: process spawn, filesystem
write/remove/rename, Git/gh/worktree/ref mutation, tool-output persistence, PTY,
MCP/auth/OAuth, plugin/provider HTTP/socket, database/storage and subagent spawn
must each be classified. Exact ownership above contains direct adapters. Any
caller elsewhere under `packages/core/src/**`, `packages/ranex/src/**` or
`packages/server/src/**` must route through a revalidated admitted service, and
043's static primitive inventory plus dynamic denial test must prove that route.
A new or unclassified primitive fails the gate; source inspection alone cannot
declare the bypass closed.

That inventory was read at harness commit
`9eeda0bf5d21bec10e3f526e5a1877d028872a2c`. Before any 037..043 issue opens,
its exact base inventory is regenerated. If a direct leaf falls outside the
assigned ownership above, opening blocks: the owner must amend this map and add
a new session-sized slice. SLICE-043 owns integration/tests only and cannot
quietly absorb newly discovered leaf wiring.

SLICE-035 uses real pinned repositories/issues and actual processes, though
Arxic itself contains a test fixture. A controller-only, nonpersisting broker
resolves `github:anthonykewl20/arxic-read` to a pre-existing controller OS-keyring
profile. It runs exact `gh repo view anthonykewl20/arxic --json nameWithOwner,isPrivate`, creates a mode-0700 temporary destination, then uses the same process-local `git -c "credential.helper=!/usr/bin/gh auth git-credential"` for exact `ls-remote https://github.com/anthonykewl20/arxic.git HEAD` and `clone --no-checkout https://github.com/anthonykewl20/arxic.git <temp>/repo`. It never runs `gh auth token`, mutates
global auth config or forwards auth environment/FDs to a worker. It validates
commit/licence/lock and that clone config/URL/logs contain no new credential copy,
then yields only a credential-free local object store. Any unresolved reference,
access, cleanup or nonpersistence doubt deletes the clone and reports BLOCKED; no
mock-close. Records contain only credential-ref ID and outcome. All pnpm commands
pin `corepack pnpm@11.17.0`. Issue #109 is a
maintainer test/measurement gap exercising actual Express/Playwright processes,
not a production-app defect.
The former SLICE-044 installed both products, invoked a real provider for both,
and covered clarification, digest approval, parallel children, effect-family
bypasses, scope/pool/retry widening, revocation, stale mapping, protected
oracles, timeout/survivors, evidence substitution and kernel PASS. That exit
is historical design provenance and was withdrawn; it does not authorize
production mutation in this release. `observed-only` oracles remain
characterization; kernel acceptance needs human, domain-rule or requirement
provenance.

Every behavior-changing WP carries a discriminating baseline and a negative
control or mutation. Only an authenticated exemption enumerated by exact
path/class/reason in A/B and signed in C for already-satisfied, refactor-only or
nonbehavioral work can replace red-first; any exemption change revokes.
Prototype exploration is separately rooted, disposable and non-promotable. The
milestone stays open on a credential skip, mock-only run, surviving negative
control, unverifiable evidence, or model-reported success.

## §5 Building Block View

### 5.1 Containers — status 2026-08-21

| Container | Responsibility | Status |
|---|---|---|
| `foundation/` | Canonical JSON, SHA-256 digests | **`CONFIRMED`** |
| `governed_execution/` | `verdict.py` — the kernel — and the SQLite hash-chained journal | **`CONFIRMED`** for evaluate, append and `ranex journal verify`; verification detects row edits, not rollback/truncation (`README.md`, "Known gaps — stated plainly") |
| `policy/` | Gate catalog loading from the committed tree | **`CONFIRMED`** |
| `cli/` | Operator entry point, path confinement, subject materialisation, toolchain pinning | **`CONFIRMED`**; mutmut recorded 573 survivors and 65 unreached in `cli/main.py`, but key e2e tests are excluded, so the signal is weak (`docs/slices/done/SLICE-004-hermetic-observation.md:239-257`) |
| `bootstrap/` | Composition root; the CLI also imports and constructs SQLite/YAML concretes directly | **`PROVISIONAL`** |
| `provisioning/` | Dependency provisioning behind `deps fetch`/`deps approve`: clean lock derivation under pinned inputs, the SHA-256-addressed wheel store, and approval recording | **`CONFIRMED`** — SLICE-006 |
| **Harness core** | Historical trimmed opencode fork and agent loop | **out of scope for the kernel-only initial release** — prior first-rung implementation is retained as provenance, not current release authority |
| **Kernel bridge** | Historical process boundary between harness collection and kernel judgment | **out of scope for the kernel-only initial release** — no current harness dependency gates #19 |
| **Delegation** | Historical first-rung worker delegation and bounded prototype pool | **prototype/history only** — broker qualification, real-provider task proof, and production fanout were withdrawn; no mutation authority |
| **Specification authority** | A normative SpecPacket/scope; B exact generated/protected gauge manifest; signed anti-replay ApprovalEnvelope C; role-separated grant/revocation, lifecycle and evidence continuity | **`CONFIRMED` kernel substrate** — SLICE-029–033 and SLICE-035 built canonical contracts/vectors, lifecycle, deterministic projections, approval/revocation/intersected grants, trace integrity and real-subject bootstrap; installed harness admission and concurrent mutation are withdrawn from the kernel-only release |
| **Harness admission** | Shared enforcement at every tool, plugin, MCP, process, Git, hosted and subagent effect leaf; exact child-intersected grant | **withdrawn from the kernel-only release** — no claim of production harness admission |
| **Agent-run manager** | Durable supervisor + capability-gated orchestrator over N worktrees/sessions | **withdrawn/out of scope** — no manager delivery follows #19 |
| **Kernel handbook** | `governance/` as the library every agent reads: rules, manuals, recipes. Reading guides; only the kernel enforces | **decided `3.0.0`**; the catalog exists, the injection does not |
| **TUI redesign — the board** | The harness front door: spec → gates → evidence → verdict, replacing the inherited opencode chat landing. Added as a new route plus feature-plugin slots, never a rewrite of `routes/session` | `PROVISIONAL` — decided, not built — `ADR-018` `accepted`. **A separate track, not a slice**: work packages BOARD-01..BOARD-22 live on the harness repository under milestone "TUI redesign — the board is the front door", design record in its `specs/tui-redesign/`. They do not contend for the one-open-slice rule and do not queue behind the P0 sequence (§0.17) |
| Web UI | Later surface; features sliced from the quarry (§15.3). **Distinct from the TUI redesign above** — that is the terminal front door and is active; this is the browser surface and is not | **parked `3.0.0`** |
| Budget / escalation | Bounded spend, three-miss escalation. The TUI redesign surfaces it (BOARD-13) but decides no threshold | **absent** |
| Intake / compile | Human/AI clarification, canonical rules/transitions/outcomes, pseudocode, flow, mapped protected gauges and oracle provenance | **`CONFIRMED` for kernel lifecycle and deterministic closed-DSL projections** — SLICE-030/031; no owner-facing clarification/intake product or installed end-to-end composition exists |
| **Translator** | Read-only projection of machine state and verdicts into plain language for the operator | **absent** — it may not evaluate, mutate, issue permits or treat worker prose as canonical (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:122-153`) |
| Outward record | Something an outsider can verify | **absent** — deferred with §11.1 |

`1.1.0` registered 34 bounded contexts. Six directories exist. The other 28 were
named and never built, and are removed from this map rather than carried as
aspiration. This is the single largest correction in `2.0.0`.

### 5.2 The kernel invariants — `CONFIRMED`, `CLAUDE.md`

Breaking one is a bug, not a tradeoff.

- The kernel is code. No model decides what happens next.
- Absence blocks.
- Evidence is bound to a subject digest.
- No self-approval.
- A gate that cannot block is refused at construction.
- The journal is append-only and hash-chained.
- Removing every model credential must not change a verdict.

### 5.3 What exists with executed evidence

The closed ledger lives under `docs/slices/done/`. SLICE-029–033, SLICE-035,
and milestone 4's retained observability/execution/provisioning work are closed;
the task-family artifact is historical but withdrawn from release scope. No
slice is active, and SLICE-036 is the only next delivery per `docs/STATE.md`.
Full-suite counts remain evidence records in the closed slices; this map does
not manufacture a new count.

### 5.4 Data ownership — `PROVISIONAL`

`governance/` holds `gates.yaml` (the committed catalog), `producers.yaml` (the
keyring and trust root), `evidence.json` (records, **not append-only**) and
`journal.sqlite3` (append-only, hash-chained, gitignored).

### 5.5 Bill of materials — `PROVISIONAL`

`governance/bom.yaml` enumerates the 15 parts, their ABB/SBB, gauge, status and
dependencies; `tests/contract/test_bom_is_honest.py` reads its structure. The
checker requires a non-null gauge, a `tests/` prefix and an existing file for a
`built` row. It does not run the named test, resolve the SBB, or show that the
gauge exercises it; an empty or unrelated test file would pass. This structural,
not semantic, check is a limitation: the map and checker can drift together while
the build stays green.

---

## §6 Runtime View

### 6.1 The intended flow — `PROVISIONAL`, shaped by ADR-017 (`accepted`) for P0

```
idea → clarify → normative SpecPacket A
                         ↓
       deterministic views + protected gauges + manifest B
                         ↓
      owner signs ApprovalEnvelope C, binding A+B+context
                         ↓
       kernel grant → isolated build → signed evidence
                         ↓
             admission → verdict → serial integration
```

Normative A carries approved semantics, deterministic manifest B binds its exact
generated artifacts and protected gauges, and signed envelope C approves A+B
plus execution context. Everything before C is conversation or deterministic
generation; everything after it requires a C-bound kernel grant. SLICE-029–033 and SLICE-035
built that kernel-side substrate. Owner-facing intake and the installed harness
admission/concurrent-mutation composition are not part of the kernel-only
initial release. SLICE-036 is the only retained next delivery and remains
qualification-only with publication blocked.

### 6.2 The build loop — `UNRESOLVED`, decided as own-built in `3.0.0`, not yet complete

```
  take the next ready task                          (foreman)
     → create an isolated git worktree
     → the harness loop executes the task           (Ranex's own, opencode fork)
     → hooks emit references, never summaries
     → read the DIFF ON DISK  (the loop's own summary is discarded)
     → THE KERNEL runs the checks                   (separate process; code, not a model)
     ├─ pass → THE KERNEL merges                    (the harness never merges)
     └─ fail → retry ×3 with the failure output
                 → still failing → escalate to the owner in plain language
```

The full loop has not run. Real delegation and kernel merge are proven by
SLICE-008 and SLICE-010, but an approved packet has never fed that path and the
harness has no common effect admission boundary. The confinement
prerequisite is closed (SLICE-017/018/019 plus SLICE-046's `cmd_run`
binding), and SLICE-029–033 plus SLICE-035 built the kernel-side A/B/C substrate.
SLICE-036 remains as the sole kernel-continuity delivery; the former
SLICE-037–044 installed composition path was withdrawn and cannot be treated as
a pending release gate (`RISK-14`, `RISK-25`).

### 6.3 The verdict path — **`CONFIRMED`**

```
ranex run --claim C --producer P -- <argv>
  → refuse if the worktree differs from HEAD
  → materialise the subject commit, each blob checked against the tree's object id
  → build the environment from empty, pin the toolchain
  → execute, record exit code + subject digest, sign Ed25519
ranex gate evaluate HEAD --approver A
  → verify signature against the committed keyring
  → compare the claim's declared argv digest
  → absence blocks; contradiction blocks; self-approval blocks
  → verdict + reason + journal append
```

---

## §7 Deployment View

### 7.1 Today — `PROVISIONAL`

There is no deployed Ranex. No service, no daemon, no installed package. The CLI
runs from the source tree through `uv` and is not an enforcement boundary for
anything but this repository — **and for this one it now is**: since SLICE-006
and SLICE-009 the self-gate runs `gates.yaml`'s bound command provisioned,
sealed and offline against the real commit, and judges the manifest diff
(`RISK-08`, closed).

### 7.2 Intended — `PROVISIONAL`

Local-first, single machine. A hosted surface is `OUT-OF-SCOPE` this horizon and
would be required by two things named later in this document — an outward-facing
record (`RISK-03`) and the fleet scale the measurement flywheel needs (§11.4).
Those are the two forces that would eventually overturn local-first.

---

## §8 Crosscutting Concepts

### 8.1 Trust boundaries

| Boundary | Rule | Status |
|---|---|---|
| Producer ↔ gauge | The gauge is external to the producer and unalterable by it | **`CONFIRMED` for the bound command** — ADR-006 (`accepted 2026-08-15`) confines it (SLICE-046; `RISK-06` closed); the controller subprocess remains same-uid trusted (ADR-023 standing limit) |
| Producer ↔ approver | The identity producing evidence cannot approve it | `CONFIRMED` as a comparison; `UNRESOLVED` as a control (`RISK-07`) |
| Model ↔ authority | A model verdict is evidence, never authority | `CONFIRMED` for the kernel |
| Enforcement ↔ inference | No enforcement check invokes a model. Removing model access changes no verdict | `CONFIRMED` for the kernel path |
| Ranex ↔ its own confinement | Ranex writes the journal, so it cannot be confined by the domain it applies to the worker | standing limit; ADR-006 is accepted and the worker is confined, but the signer/controller remains same-uid trusted infrastructure (ADR-023) |

### 8.2 Determinism — `CONFIRMED` for the kernel

Canonical JSON, SHA-256 digests, identical inputs to identical verdicts byte for
byte. **"Deterministic" describes the process and the verdict, never the generated
code.** Anyone claiming an LLM produces identical software twice is selling
something.

### 8.3 Observability

Recorded: every verdict with the rule that failed, the subject digest and the
approver; `Evaluation.as_record()` has no producer ID. `evidence.json` keeps only
the latest record for a claim+producer, so it is not durable evidence history.
Never recorded as fact: anything a model asserted about its own work.

Not recorded and required by `PR-07`: the production configuration — model,
harness version, skill and tool manifest, prompt digest.

`UNRESOLVED`: a future worker handoff is immutable references to its packet,
candidate, commands actually run, evidence, unknowns and deviations — never a
conversational summary (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md:377-398`). A future durable record may add rebuildable projections, content-addressed artefacts, idempotent external
effects and crash/recovery tests; if an external effect is introduced, its state,
journal and effect must be atomic. Neither end-to-end design is built (outside
repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/cookbook-alignment-research-2026-07-27.md:935-953`; `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0016-resolve-five-implementation-start-owner-decisions.md:34-45`).

### 8.4 Calibration — `PROVISIONAL`, new in `2.0.0`

The deepest part of the doctrine, and the part `1.1.0` had no concept of.

Every measured figure must record its exact invocation and working directory. The
lost rule produced a 245-vs-6 result for one pinned check, solely by changing the
directory/invocation; the pre-reset source, rather than the reported 245-vs-0,
is authoritative (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/reviews/2026-07-31-delivery-model-restructure-assessment.md:187-215`).

In a factory, **the gauges are themselves calibrated** against a reference, on a
schedule, with a certificate and a due date. The rule that gives it force:

> When a gauge is found out of calibration, **every part it passed** since its
> last good check is suspect and is recalled.

Not the parts it rejected. The ones it approved — because a bad gauge does not
produce visible errors, it produces confident approvals.

The surrounding discipline is **Measurement System Analysis**, whose core tool is
**Gauge R&R**: measuring the variance of *the measurement system* rather than the
part. Repeatability — same gauge, same part, same answer? Reproducibility —
different operators, same answer? Published guidance places roughly under 10% of
tolerance as good and over 30% as unusable. *(Thresholds recalled from AIAG
practice and not verified; check before quoting.)* Most shops never measure this,
and therefore do not know their pass/fail data is largely noise.

The same discipline exists in pharmaceutical work as **method validation** — an
assay must be validated for specificity, accuracy, precision and robustness
*before* any result from it is trusted. The test is tested before the drug is.

**Four consequences for Ranex, none of them currently satisfied:**

1. **`mutmut` is not a code-quality tool. It is a repeatability signal for the
   operator's defect model** — deliberately
   introducing known defects and checking whether the instrument notices. The 880
   surviving mutants are not a backlog; they are a **calibration report** stating
   that this instrument fails to detect 880 known defects, 47 of them in
   `verdict.py`, which is the master gauge every other measurement passes through.
2. **A gate that has never fired is unproven, not good.** It is either protecting
   against something that does not occur or it is broken, and from outside those
   are indistinguishable. Firing rate must be a recorded property of every gate.
   `gates.yaml` now touches the part (`RISK-08`, closed by SLICE-006/009), and
   SLICE-009 proved the gate fires — it flips to FAIL when a frozen test's file
   is deleted; firing rate is still not recorded.
3. **Negative controls.** Periodically inject a change known to be bad and confirm
   the gates block it. Every serious assay runs one. If it ever passes, every
   verdict since the last good control is suspect — calibration recall, applied.
   This is the smallest shippable piece of §8.4 and should be built first.
4. **Built and calibrated are different states**, which is why §5.5's bill of
   materials separates them.

---

## §9 Architectural Decisions

Eighteen ADRs exist. `1.1.0` indexed twenty-one belonging to an architecture that was
deleted; they are not carried forward.

| ADR | Decides |
|---|---|
| `ADR-000` | How ADRs are written — prior art must be fetched, pinned and vendored |
| `ADR-001` | Claim↔command binding |
| `ADR-002` | Committed trust root |
| `ADR-003` | Research is fetched evidence, not citation |
| `ADR-004` | Environment boundary for git queries |
| `ADR-005` | Hermetic observation |
| `ADR-006` | Landlock confinement of the bound command |
| `ADR-007` | Provision dependencies without pretending they are evidence |
| `ADR-008` | Fork opencode at a pinned commit; bridge to the kernel through hooks |
| `ADR-009` | Git-backed materialisation of the observed subject |
| `ADR-010` | First delegation: one operator request becomes governed work |
| `ADR-011` | A skip is absence, not success |
| `ADR-012` | The kernel merges |
| `ADR-013` | Prototype before production |
| `ADR-014` | The bridge becomes a per-member protocol — `proposed` |
| `ADR-015` | Durable execution, watchdog first — at-most-once with explicit interruption — `accepted 2026-08-07` |
| `ADR-016` | Measure before learning — source-backed, prototype-gated measurement |
| `ADR-017` | Human-approved canonical specification before implementation authority — `accepted 2026-08-15`, P0 |

**ADR-007 is not the journal ADR.** ADR-005 removed `.venv` and `node_modules`
from the materialisation because ignored state is not in the commit, so only
self-contained commands can run — and this repository's own `uv run pytest -q`
is not one. ADR-007 exists to reconnect the gauge to the part (`RISK-08`), which
is why it displaced confinement in the ordering (§13).

The journal ADR — verify before append, never auto-create, and a checkpoint
committing to log **size**, because size is what catches truncation and
rollback — is deferred and unnumbered.

### 9.1 Filtered historical contradictions — `PROVISIONAL` provenance, not authority

- Old ADR-0005's qualified Bubblewrap worker lane is contradicted by current
  ADR-006's Landlock confinement; neither authorises worker orchestration.
- Old ADRs 0011/0015's runtime is contradicted by the settled no-agent-loop/
  no-harness boundary.
- Old ADR-0012's two readiness tiers and 21 gates are contradicted by the current
  capability-status model and one-slice delivery rule.

These are recorded to prevent restoration, not to revive old authority (outside
repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md:34-42`,
`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md:19`, and
`/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/decisions/ADR-0012-separate-implementation-start-and-production-readiness.md:45`).

---

## §10 Quality Requirements

### 10.1 Architecturally significant requirements — `PROVISIONAL`, re-derived

| ID | ASR | Drives |
|---|---|---|
| `ASR-01` | A verdict must be reproducible: identical inputs, identical verdict, no model invoked | Rules out model-in-the-loop enforcement entirely |
| `ASR-02` | Absence of evidence must block, never default | Fail-closed; forbids permissive defaults |
| `ASR-03` | Evidence must bind an exact subject digest | Content addressing; stale evidence self-invalidates |
| `ASR-04` | **The gauge must be unreachable by the party it measures** | Confinement; forbids in-process trust. ADR-006, unbuilt |
| `ASR-05` | **Every gauge must be demonstrably able to detect a known defect** | Mutation testing and negative controls become gates, not habits (§8.4) |
| `ASR-06` | Records must be append-only and replayable | Journal + hash chain; forbids destructive update |
| `ASR-07` | **A verdict must be checkable by someone who distrusts its producer** | Signatures, public keyring, offline re-derivation. Currently unsatisfied (`RISK-03`) |
| `ASR-08` | **Configurations must be comparable: the same frozen target, scored identically across different producers** | This is what makes measurement possible at all (§11.3) |
| `ASR-09` | **Every run must be bounded in wall clock and spend, and exceeding the bound is a recorded refusal, never silent continuation** | `PR-09`, the wedge |
| `ASR-10` | A non-technical owner must be able to act without reading code | Plain-language escalation; the flow-graph gate |

### 10.2 Quality attributes — `UNRESOLVED`

**None measured.** No performance, latency or cost target has been observed. Any
number quoted today is a target, not an observation.

---

## §11 Risks and Open Questions

### 11.1 Product and market — **deferred in `2.2.0`, not resolved**

The owner settled the audience on 2026-08-03: *"Just needs to work for me."* No
external buyer, no deadline, no one reading this. Every risk in this section is
therefore **a not-now question rather than an open one**. They are kept because
they become live the moment anyone other than the operator is meant to read a
verdict — and deleting them would lose the reasoning.

| ID | Risk | Settled by |
|---|---|---|
| `RISK-01` | **Only the deterministic half of the thesis is true by construction.** The producer-unalterable scorer is built for the bound command (ADR-006 accepted; `RISK-06` closed with the same-uid controller standing limit) and `RISK-07` leaves approval unauthenticated, so `1.1.0`'s truth risk remains alongside the question of whether anyone will pay | Confinement landing, then a buyer paying for it |
| `RISK-02` | **Timing.** The provability nightmare (§1.1 level four) may be three to five years early. No one has been sued at scale over AI-written code. Founders do not buy diligence insurance in advance. Right and early is operationally identical to wrong | Evidence of present-tense pain, or a wedge that pays before the nightmare arrives |
| `RISK-03` | **Position.** A lemons market is fixed by a signal a hostile outsider can read. Ranex is a local CLI, and a certificate you issue to yourself is worth nothing. The cryptographic substrate for an outward record exists; the position does not | A decision about who the verifier is, which likely overturns local-first (§7.2) |
| `RISK-04` | **The buyer is post-disillusionment.** Someone who still believes a prompt produces an app does not want gates — they want the magic, and competitors sell it. The buyer is the person who already burned weeks and thousands and now distrusts the loop. Real, growing, and smaller than the believer market | Contact with actual buyers |
| `RISK-05` | **"Software factory" and "enterprise" both carry cost.** The first is a discredited term to experienced engineers (§4.2); the second quietly promises output quality, which §1.2 forbids claiming | An owner decision on naming |

### 11.2 The wedge and the moat — **deferred with §11.1**

Kept for the day there is an audience, and inert until then.

- **The wedge would be cost and completion** (`PR-09`, `C-02`) — *stop burning
  money on runs that never finish.* Felt today, easy to explain, and copyable in
  a quarter.
- **The moat would be provability** (`PR-01`, `ASR-07`) — *the record survives
  someone who wants it to be false.*

With no external audience, neither is a sequencing input. **Dogfooding is the
schedule**: the measure of progress is whether Ranex governs the operator's own
agents on his own repository. That promotes `RISK-14` from one risk among many to
the only scoreboard.

### 11.3 The measurement problem — `PROVISIONAL — source-backed design in ADR-016; unbuilt`

The owner's intent is that accumulated use should grade every component — skills,
gates, rules, reviews, models — and that grading should compound into improvement.

**The plan as stated does not work, for a structural reason.** Observational data
from real runs is confounded. Hard tasks get the expensive model; careful users
load better skills; complex repositories get more gates. Regressing outcome on
components across observed runs will produce a confident, tight-error-bar
conclusion that expensive models cause failure — because they were assigned to the
hard problems. This is not a data-hygiene issue that cleaning fixes; it is
structural, and it is the standard way measurement programmes generate confident
nonsense.

Both mature disciplines solved it the same way, and neither solved it with logs:

- Manufacturing uses **Design of Experiments** — deliberately varying factors on a
  schedule so effects are separable. Taguchi's orthogonal arrays exist to test many
  factors in few runs, which is precisely the constraint here.
- Pharmacology uses the **control arm**. No efficacy claim without a comparison
  group.

**So: run data gives monitoring; causal grades require deliberate experiments.**
Different machinery, and it has to be designed in rather than retrofitted.

**Why this is an opportunity rather than an obstacle.** An honest trial needs a
fixed treatment, isolated replicates, and an outcome measured by something with no
stake in it. Ranex has a mechanical outcome gauge and filesystem isolation, but not
fixed treatment or statistical independence by construction. The `TreatmentManifest`
is absent today; a complete experiment system does not exist. The frozen
`TargetCorpus` fixes the outcome instrument; it is not the treatment being compared.

ADR-016 bounds its parked measurement-local build path: M0 prototype, then F1 monitoring-only manifest/corpus
observations, F2 pure paired grader, F3 paired runner and fault capture, and F4
owner-authorized promotion/rollback. RISK-07/19 block F4; RISK-06 closed by
SLICE-046 (its standing controller limit is recorded in §11.5). Provider correlation,
generalization, exact power and the absent translator remain named limits or separate
work, not gates this feature pretends to close. The composition remains UNPROVEN:
this is a source-backed design, not a built feature or proof that any configuration
is best.

### 11.4 Limits of the grading idea — `PROVISIONAL`

| Limit | Consequence |
|---|---|
| **Not everything decomposes.** Skills, gates, rules and models are discrete and gradeable. Prompts, tasks and context are not. Some variance lives irreducibly in the whole | Do not attempt a grade for every input; the parts list must distinguish gradeable parts from unbounded ones |
| **Goodhart.** Publishing a component's grade causes components to be optimised for the grade. A frozen target prevents post-hoc movement, not optimisation against a visible corpus | Freeze the corpus before proposal, deny candidate mutation, record visibility, and claim only conformance to that corpus; generalisation remains unproven |
| **Sample size.** Separating signal from variance needs many runs on comparable tasks | Fix N before the trial, make no power claim, and return `INCONCLUSIVE` when evidence is insufficient; fleet scale may be needed for useful sensitivity |
| **First-scope bound.** One candidate and one binary primary endpoint; secondary metrics are descriptive only | Exact power remains unverified; fixed-N trials may yield `INCONCLUSIVE` |
| **Provider correlation and visible corpus.** Paired runs can share provider effects, and a visible corpus proves only conformance to that corpus | Disclose correlation and do not claim independence or generalization |

### 11.5 Engineering risks — current, `PROVISIONAL` unless noted

| ID | Risk |
|---|---|
| `RISK-06` | ~~**The measured party runs under the uid that signs the measurement.**~~ **Closed by SLICE-046 (ADR-023, ADR-006 accepted 2026-08-15)**: the bound command runs inside the qualified strict-local session (Landlock/seccomp/cgroup, env allowlisted to LC_ALL/TZ, no inherited fds), and evidence is signed only after fail-closed validation of the confinement result — the worker cannot reach the key or forge its measurement. Standing limit, recorded: the controller subprocess itself remains same-uid trusted infrastructure (sudo-monitor model, ADR-023); controller env narrowing is a named follow-up |
| `RISK-07` | **`approver_id` is an unauthenticated string.** No-self-approval is a comparison, so any caller can name an approver that is not themselves. The strongest remaining hole once confinement lands |
| `RISK-08` | **Ranex did not gate its own repository** — `gates.yaml` required a command a hermetic tree could not run; it is why the SLICE-004 defect got through, and it was §8.4's disconnected gauge. **Closed by SLICE-006 (ADR-007, accepted) and SLICE-009**: the self-gate runs the provisioned suite sealed and offline against the real commit, and judges the manifest diff, not the exit code |
| `RISK-09` | **880 surviving mutants**, 47 in `verdict.py`, and **44 refusals no test executes**. The gauge's own calibration report, unaddressed |
| `RISK-10` | Mutmut recorded **573 survivors and 65 unreached** in `cli/main.py`; the signal is weak because key e2e tests are excluded, not absent (`docs/slices/done/SLICE-004-hermetic-observation.md:239-257`) |
| `RISK-11` | **`evidence.json` is not append-only.** Signatures prevent forgery, but deletion turns a recorded failure into absence. Absence blocks, so this is denial rather than forgery — but it is unbounded |
| `RISK-12` | **The journal has no operator-facing projection.** `ranex journal verify` recomputes chain integrity, but it does not explain run state or proof in plain language; the translator remains absent (`README.md`, "Known gaps — stated plainly"; outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:122-153`) |
| `RISK-13` | **`HOME` is still inherited by Ranex's own git queries**; symlink and submodule trees cannot be observed at all |
| `RISK-14` | **The loop has closed around a real agent — once.** SLICE-008's `task delegate` dispatched, measured and judged a real model's work end to end, and SLICE-010 let the kernel publish it. What stays open is narrower: one operator-selected thread has run (`RISK-24`), and nothing upstream of dispatch — intake, graph, scenarios — has ever fed it |
| `RISK-15` | ~~**One implementer** is a weakness~~ — **reclassified in `2.2.0`.** One human operating a team of agents is the **premise**, not a defect (§1.3). What survives as a genuine risk is narrower: *the operator writes every gauge, and nothing checks the gauge.* Code proves the agent did not approve itself; nothing proves the human's gate was a good gate. That is `PR-06`'s burden and the reason §8.4 matters more here than in a multi-person shop |
| `RISK-16` | arc42 is CC BY-SA 4.0; adopting the template as an adaptation in a public repository carries ShareAlike |
| `RISK-17` | **Adopting more of TOGAF than §4.5's four parts recreates the 561-file failure.** This is not a hypothetical: the pre-reset tree was already TOGAF-shaped and produced zero product code. The ADM's overhead is amortised across an enterprise; there is one implementer here. Any proposal to add an ADM phase, a capability level, a maturity score or a compliance grade should be read as this risk materialising |
| `RISK-18` | **This map is not yet conformant to ISO/IEC/IEEE 42010.** It has stakeholder, concerns, viewpoints and correspondences; model kinds are absent and two viewpoints govern no view (§14.3) |
| `RISK-19` | **The journal does not detect rollback or truncation.** `ranex journal verify` recomputes an extant chain, but an internally consistent earlier prefix verifies after later rows are removed; the deferred size checkpoint is the named remedy (`README.md`, "Known gaps — stated plainly"; §9) |
| `RISK-20` | **Git ancestry establishes target-before-work only while history is not rewritten.** Signed commits would expose a rewrite, but Ranex verifies neither ancestry nor commit signatures today (`src/ranex/cli/main.py:976-1057`); apparent precedence remains forgeable |
| `RISK-21` | **Concern completeness is internal consistency, not completeness.** The sole stakeholder is also architect; a blind spot cannot break the concern↔requirement relation. The operator raised skill and tool-server poisoning earlier, but it is not among `C-01`–`C-04` |
| `RISK-22` | **Mutation testing validates the operator's model of defects, not that model's validity.** It measures repeatability and does not replace a reviewer who challenges the defect model |
| `RISK-23` | **The coverage table proves only the stated hole exists.** It does not validate the concern set, the mapping method, or the product reasoning |
| `RISK-24` | **One complete thread is operator-selected and likely the easiest available.** Passing it proves the mechanism runs, not that it handles the cases behind `C-02`, `C-03` or `C-04` |
| `RISK-25` | **Ranex's historical delegation path dispatched prose without common harness effect admission.** The harness admission and SLICE-044 production-exit program are withdrawn from the kernel-only release; the retained #19/SLICE-036 scope does not claim governed concurrent mutation |

### 11.6 Sequencing decisions — owner, 2026-08-03

**P0 supersession — owner, 2026-08-09.** SLICE-017..019 then ADR-017
SLICE-029..044 is the first program
and supersedes the earlier manual-thread exception below. The target is still
Idea → Behaviour → Result, but now intake, digest approval, actual Ranex dispatch,
harness enforcement, parallel child grants, deterministic verification and
kernel merge are the exit. ADR-006 is required underneath it. Other durability,
manager, measurement, handbook and UI tracks remain parked/background unless a
bounded dependency is necessary for that real composition test.

**Confinement lands first inside P0.** ADR-006 stands; its old slice was withdrawn
and replacement issue #10 / SLICE-017 is now the single active docs slice;
issues #21/#22 carry planned SLICE-018/019. The
reason for the earlier delay remains:
**the ruler was not
touching the part yet.** `gates.yaml` demanded a command a hermetic tree could not
run, so Ranex then gauged nothing — hardening an instrument that is measuring
nothing protects nothing. SLICE-006 has since closed and the ruler touches the
part: the precondition is met. Confinement has since landed: SLICE-017/018/
019 closed and SLICE-046 bound `cmd_run` to the qualified session; ADR-006 is
accepted and `RISK-06` closed (2026-08-15), leaving the same-uid controller
standing limit (§11.5).

**Hardening `C-01` continues.** The owner was shown §1.3's coverage table —
`C-02`, `C-03` and `C-04` are thin or empty, and four closed slices have gone to `C-01` —
and chose to keep hardening the foundation. Recorded as a decision with its cost
stated: **the other three concerns stay unserved for now**, and `C-02` in
particular has nothing at all.

**The first finish line — owner, `PROVISIONAL`, refined twice on 2026-08-03:**

> **One complete thread: Idea → Behaviour → Result.**
> **The numbers come after that thread exists, not before it.**

The path to this was: first a numeric target (zero surviving mutants, zero
unreached refusals) was offered and **rejected** — a mutation count measures the
instrument, not whether the design works. Then "Ranex governs one real task" was
chosen. Then the owner sharpened it again: *"the first viable finish line we
should have is the output. From Idea → Behaviour → Result, then from there we
will start the deterministic numbers."*

Both refinements moved the same direction, and the final one is the strongest
available, because it is **the gauge thesis stated as a workflow**:

**Behaviour has two halves and a freeze line between them** — the owner's
clarification, and the most load-bearing detail in the chain:

```
Idea  →  Behaviour [ specify │ FREEZE │ execute ]  →  Result
                               ↑                       ↑
                     target locked, read-only    checked against
                     to whoever executes it      the frozen target
```

| Step | What it is | Why it is the whole product in miniature |
|---|---|---|
| **Idea** | What the operator wants, in his own words | The only part that is a conversation |
| **Behaviour — specify** | What arriving looks like, written as something observable | This becomes the gauge |
| **FREEZE** | The specification is digested and made **read-only to whoever executes** | Without this line the target moves mid-work. Everything else is decoration if this fails |
| **Behaviour — execute** | The plan and the work | The throw. Ranex deliberately does not judge *how* |
| **Result** | What came out, **measured against the frozen specification** rather than reported | The verdict. The agent's account of itself is discarded |

**The owner's illustration**, recorded because it makes the freeze line obvious:
a human crossing a river from A to B. The idea is *get across*. The behaviour is
the raft and the crossing. The result is *standing at B*. Ranex does not care
whether he swam, rafted or bridged — only whether he is at B, **and only if
where B is was fixed before he stepped into the water.** The failure it prevents
is not a lie: it is a tired man turning back, calling the near bank "B," and
being right, because nobody planted the marker.

**Already decided, and this is the same thing:** `CLAUDE.md` requires tests
frozen before BUILD, read-only to implementers, with red-then-green enforced.
Red-then-green proves that a check **discriminates**: it fails without the work
and passes with it. It cannot prove temporal precedence; an author can write code
and its test, then check out an earlier commit and observe red. For SLICE-001,
Git ancestry supplies that evidence: `b495e3635` (the red target) is an ancestor
of `0762cf7428` (the implementation). That proves precedence only while history
is not rewritten; `RISK-20` records the unbuilt signature and ancestry controls.

**The owner's second illustration — cooking adobo** — recorded because it names
three things the river does not:

| Adobo | Ranex |
|---|---|
| The cook | The agent. Untrusted by design |
| The kitchen | Hermetic materialisation and confinement |
| **Recipe, ingredients, tools — all handed to the cook, none chosen by him** | The frozen behaviour, the materialised subject, the pinned toolchain. **This is the clearest available statement of why SLICE-004 exists**: a cook who brings his own ingredients can substitute them, and one who picks his own scale can pick a broken one |
| Another cook reviews the dish | A critic. Produces **findings**, never a verdict |
| **An independent taster** | The executable check. Produces **the verdict** |
| An assistant reports to the restaurant owner | **The translator** (§5.1) — absent, and the reason `C-04` is unserved |

**The trap the metaphor exposes: the taster must not be a cook.** Cooks share
blind spots and can be talked round. An "independent taster" that is another
model is not a taster — it is a third cook agreeing with the first two, which is
what most AI review arrangements actually are. The taster must be something that
cannot be persuaded. This is `PR-02` — model output is never an authorization —
with the reason made obvious rather than stipulated.

**What this reorders.** The owner had chosen to keep hardening `C-01`; this
supersedes that as the *goal* while keeping it as a *means*. Hardening now serves
the thread rather than preceding it. The 880 surviving mutants and 44 unreached
refusals become a **later phase** — real work, deferred, and not a precondition.
Recorded plainly because it reverses an answer given earlier in the same session.

**Historical exception, superseded 2026-08-09.** This paragraph formerly excluded
the flow interface, intake and Ranex dispatch, allowing the operator to author
behavior and run the agent manually. The owner replaced that shortcut with
ADR-017 SLICE-029..044: the first thread now includes canonical intake, dispatch and
harness enforcement. It remains here only to make the sequencing change visible.

This makes `RISK-14` the terminating condition rather than a standing risk, and
it is the first honest test of §1.2's thesis. It also means **`VP-05` and `VP-06`
(§14.1) stop being empty by neglect and become empty by schedule** — the thread
produces something for them to govern.

---

## §12 Glossary

| Term | Meaning |
|---|---|
| **Gauge** | A fixed, external, mechanical standard that decides whether a part passes. Set before the work and unalterable by the producer |
| **Calibration** | Demonstrating that a gauge detects a known defect. A gauge with no calibration result yields no information |
| **Gauge R&R** | Measuring the variance of the measurement system itself — repeatability and reproducibility — rather than of the part |
| **Negative control** | A deliberately bad input run through the system to confirm it is rejected. If it passes, everything since the last good control is suspect |
| **Traveler** | The record that accompanies work through every station, stamped at each. An unstamped part does not ship |
| **Jidoka / andon** | Stopping on a detected defect rather than continuing confidently. Stopping is correct behaviour |
| **Poka-yoke** | Making the defect impossible rather than catching it later |
| **Bill of materials** | Every part needed to build the whole, with its buy/build decision, its gauge and its status |
| **Routing** | The order of assembly, derived from the parts list's dependencies |
| **ABB / SBB** | TOGAF: Architecture Building Block — the capability required — versus Solution Building Block — what implements it. An ABB with no SBB is an unfilled part |
| **Baseline / Target / Gap** | TOGAF: what exists, the finish line, and the difference between them, which is the parts list |
| **Transition Architecture** | TOGAF: an intermediate state that must deliver value on its own, not merely be closer to done |
| **Architecture Contract** | TOGAF: the signed agreement an implementer must satisfy. Ranex's frozen task envelope, and Phase G is the checking of it (§4.5) |
| **Phase G** | TOGAF ADM Implementation Governance — conformance of built work to the agreed target. Ranex automates its conformance-checking part |
| **Viewpoint / view / concern / correspondence** | ISO 42010: a concern matters to a stakeholder; a viewpoint frames concerns; a view is governed by a viewpoint and addresses concerns; a correspondence is a checkable relation between description elements |
| **DOE** | Design of Experiments — deliberately varying factors so their effects are separable |
| **Worker envelope** | The full production configuration: model, harness version, skill and tool manifest, prompt digest |
| **Wedge / moat** | The problem that sells today versus the property that remains defensible after copying |
| **Subject digest** | The exact bytes a piece of evidence refers to |
| **Slice** | One small end-to-end capability, with an ADR behind it and a test proving each done-criterion |
| **`NOT_ASSESSED`** | No attempt was made. Never a pass |

---

## §13 Slice Ledger

Every slice, what it validated, and **what it disproved**. The second column is
the one that matters; a ledger recording only successes is a brochure.

| Slice | Delivered | Disproved |
|---|---|---|
| `SLICE-001` evidence production | `ranex run` executes a command, records exit code and tree digest, emits evidence the gate accepts. The red target at `b495e3635` is an ancestor of implementation `0762cf7428` | — |
| `SLICE-002` evidence authenticity | Ed25519 signatures verified against a committed keyring; keyring and catalog read from the commit, not the working tree | **Closed twice, reopened twice.** Audits found the tests narrower than reality (17 defects across four audits); then the trust-root check was skipped entirely for a path the commit did not carry, so an attacker-named catalog was read unchecked |
| `SLICE-003` claim↔command binding | The committed catalog declares the argv satisfying a claim; a signed record of `true` no longer satisfies `tests-executed`. Six audits failed to break the binding | The same audits reproduced **six ways to get a false PASS around it** — one root cause, all frozen as deliberately-failing tests |
| `SLICE-004` hermetic observation | The bound command runs against a materialisation of the subject commit, every blob checked against the tree's object id, environment built from empty, toolchain pinned | **Closed, reopened, closed again.** The first close rested on a cleanup control that had never worked on any supported Python, covered by a test that monkeypatched out the function it was named for, and on a mutation check **run by hand by the actor who wrote the code**. Measuring the general form found **59 refusals no test executed**. Two capabilities were deliberately withdrawn: trees needing installed dependencies, and trees carrying symlinks or submodules, can no longer be observed |
| `SLICE-005` confinement | **Withdrawn 2026-08-03 before any implementation**, never committed. ADR-006 stands; the slice was re-sequenced behind SLICE-006 | — |
| `SLICE-006` gate a real test suite | Closed 2026-08-04, all fifteen criteria proven. `deps fetch` derives the lock clean under pinned inputs, only SHA-256-addressed wheels enter the store, `deps approve` records the delta, and the self-gate ran sealed with the operator's own key. Closes `RISK-08` — the gauge touches the part | Nine defects found by driving the CLI as a person does; none by a unit test. An approved, hash-correct wheel still chooses its own exit code |
| `SLICE-007` trimmed fork to the kernel | Closed 2026-08-03, all five criteria proven. opencode forked at `v1.18.11` (`012c2f57`), trimmed, startup fails closed unbridged; `task dispatch`/`task judge` land the commit-then-materialise bridge, proven by the gear-mesh e2e on a deterministic in-fork model with zero credentials | — |
| `SLICE-008` first delegation | Closed 2026-08-05. `task delegate` runs a real agent headless in a dispatched worktree, in an environment that refuses to start holding the signing key; a separate keyless invocation judges — CANDIDATE, never PASS; prototype `task fanout` runs a bounded pool. Proven end to end against a real free model | `fanout` accepts free prompts and has no A/B/C, exact child scopes or capability admission, so it is not production mutation authority. The model credential sits in a network-open loop; `ranex run`'s bound command is now confined (SLICE-046) — the credential exposure remains recorded, not mitigated |
| `SLICE-009` a skip is absence | Closed 2026-08-05. Signed structured outcomes (evidence v3), an outcome-blind frozen manifest, and a diff that blocks undeclared skip, xfail, xpass, error or missing IDs; the self-gate PASSes honestly and flips to FAIL when a frozen test's file is deleted | Exit-code satisfaction let a skipped or vanished test read as success — measured by destroying 27 tests while the suite stayed green. A hostile tree can still forge the artifact; criterion 10 states that boundary |
| `SLICE-010` the kernel merges | Closed 2026-08-06 (parked and re-opened the same day), all fourteen criteria proven. `task merge` publishes a judged candidate only through ordered journalled checks: a domain-separated approval envelope bound to candidate, subject, target ref, observed tip, catalog digest and CANDIDATE row hash; ancestry, merge-range, digest/evidence and CAS each refuse red-first; races journal exactly one winner | The unsafe `update-ref` control is reproduced before it is refused |
| `SLICE-011` durable execution prototype | **Closed 2026-08-07**, all nine criteria met. Five durability claims proven red-to-green in disposable scratch-harness worktrees, one per claim at an identical HEAD (ADR-015): watchdog, reconciler reorder, durable retry, durable blockers, Session-ID fencing. Each carries two-reviewer consensus; the five per-claim records are consolidated, embedded and hash-bound in `docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`. Criterion 8's compiled gate refuses a production durability slice without it. Ships nothing; milestone #1 on `ranex-harness` carries the production plan | Every gate re-run against disk by the supervisor, never read from the session's own summary — which is how claim 5's suite was caught unstable (~12%) after being reported stable and approved by two reviewers, and how the gate itself was caught built wrong for the one case it exists to cover |
| `SLICE-012` provider watchdog | **Closed 2026-08-07**; provider watchdog in production, feature commit `23d6a5b4ee...`, with idle and absolute non-retryable timeouts | — |
| `SLICE-013` reconciler reorder | **Closed 2026-08-08**; reconciler hoist and startup sweep in production, feature commit `a8bc7bdf35...`; the DB-global sweep leaves the known fencing hazard | — |

**The pattern across seventeen closed slices, stated because it is the most reliable
information in this document:** every slice that was closed on the implementer's
own report was later reopened. Every reopening was caused by a measurement the
implementer did not run. The project's own history is the strongest available
evidence for §1.1 — and the substitution of `mutmut` and `diff-cover` for
self-report in SLICE-004 is the only structural change that has ever stopped it.

**SLICE-008 was the first slice to govern work produced by a real agent;
SLICE-010 let the kernel publish it.**

---

## §14 Architecture description conformance

arc42 has no slot for this. ISO/IEC/IEEE 42010 requires it, and without it the
map is prose that cannot be wrong.

### 14.1 Viewpoints — `PROVISIONAL`, new in `2.3.0`

A viewpoint frames one or more concerns and governs exactly one view. Declaring
them is what turns "the sections are full" into "the concerns are answered."

| Viewpoint | Frames | Governs | Convention |
|---|---|---|---|
| **VP-01 Verdict** | `C-01` | §6.3 the verdict path | The sequence from command to verdict, and every point at which it blocks. A step that cannot block does not belong in this view |
| **VP-02 Structure** | all four | §5 building blocks | One row per container, its responsibility, and its evidence status. Aspiration is excluded — a container that does not exist is marked absent, never described as though built |
| **VP-03 Calibration** | `C-01` `C-03` | §8.4 | Every gauge, its calibration procedure, and its most recent result. A gauge with no result is reported as yielding no information |
| **VP-04 Record** | `C-04` | §8.3 observability | What is recorded as fact, what is refused as fact, and what is not recorded at all |
| **VP-05 Cost** | `C-02` | **no view exists** | Would govern budget, timeout and escalation. Nothing to govern yet |
| **VP-06 Regression** | `C-03` | **no view exists** | Would govern what "still works" means and how it is measured across a change. SLICE-006, its precondition, has landed; the view itself remains unwritten |

**The finding this produces on its first application:** `VP-05` and `VP-06` frame
real concerns and govern nothing. **Two of the operator's four worries have no
view in this map at all** — not a thin one, none. The coverage accounting does not
validate the concern set or its method (`RISK-21`; `RISK-23`).

### 14.2 Correspondences and correspondence rules — `PROVISIONAL`

A correspondence is a stated relation between description elements. A
correspondence rule is one a check can enforce. These are the map's own gauges.

| # | Correspondence | Rule | Enforceable |
|---|---|---|---|
| `CR-01` | requirement → concern | Every `PR-*` names at least one `C-*` | **Yes** — trivially checkable |
| `CR-02` | concern → view | Every `C-*` is addressed by at least one view via a viewpoint | **Yes** — and it currently **fails** for `C-02` and `C-03` |
| `CR-03` | capability → evidence | Every §1.5 row marked `CONFIRMED` names a passing test | **No** — the rows name slices or prose, not tests |
| `CR-04` | risk reference → risk | Every `RISK-nn` mentioned in prose exists in a risk table | **Yes** |
| `CR-05` | section reference → section | Every `§n.n` cross-reference resolves | **Yes** |
| `CR-06` | BOM row → gauge | Every part in `governance/bom.yaml` names a gauge; `built` names a test; `calibrated` names a mutation or negative-control result | **Partly** — structural checks only (§5.5) |
| `CR-07` | map → repository | Slice and ADR names in §9 and §13 exist on disk | **Yes** |

`CR-01`, `CR-04`, `CR-05` and `CR-07` are mechanical and small. **`CR-02`
failing is a feature** — it is the map reporting a real hole rather than reading
smoothly over it.

### 14.3 Conformance statement — `PROVISIONAL`

This map **does not claim conformance** to ISO/IEC/IEEE 42010. It has an entity of
interest, one identified stakeholder, four concerns traced to him, six declared
viewpoints, views for four of them, partial rationale, and seven stated
correspondences. It lacks model kinds, and two viewpoints govern nothing.

The clause text of 42010 is behind a paywall and has not been read; the conceptual
model was taken from the working group's published material. **Conformance must
not be claimed publicly on that basis** — buy the standard first.

---

## §15 Maturity ledger

§0.1 labels claims; this ledger labels mechanisms, and collapses the scale to the
two columns the owner asked for. A mechanism is MATURE/PROVEN only if it is built
and carries executed evidence on disk, **or** it is proven elsewhere by code the
world already runs and is available to adopt under the research rule (§15.3).
Everything else — decided, designed, or merely named — is IMMATURE/UNPROVEN. A row
that cannot name its evidence or its absence is not in the ledger.

### 15.1 MATURE / PROVEN — `CONFIRMED`, executed evidence in this repository

| Mechanism | Executed evidence | Residual hole it does not cover |
|---|---|---|
| Deterministic verdict kernel | `evaluate()` is pure (`src/ranex/governed_execution/domain/verdict.py:238-324`); `tests/unit/test_gate_verdict.py`; the suite passes with no model credential present | `approver_id` is an unauthenticated string (`RISK-07`) |
| Subject-bound evidence | SLICE-001; stale evidence stops counting (`tests/unit/test_gate_verdict.py`) | — |
| Evidence authenticity | SLICE-002; Ed25519 verified against a committed keyring (`tests/security/test_evidence_trust_root.py`, `tests/security/test_slice002_trust_root_reopened.py`) | the controller subprocess remains same-uid trusted infrastructure (`RISK-06` standing limit, ADR-023) |
| Claim↔command binding | SLICE-003; `tests/security/test_slice003_command_binding.py`; six audits failed to break the binding itself | six false-PASS routes *around* it were one root cause, closed by SLICE-004 |
| Hermetic observation | SLICE-004; `tests/security/test_slice004_hermetic_observation.py` — materialised commit, environment from empty, pinned toolchain | trees needing installed dependencies, or carrying symlinks/submodules, cannot be observed (withdrawn capabilities) |
| Append-only hash-chained journal | `tests/integration/test_journal.py`, `tests/e2e/test_journal_verify_cli.py`; SQLite triggers forbid update and delete | rollback/truncation undetected (`RISK-19`); `evidence.json` is not append-only (`RISK-11`) |
| Path confinement, dirty-tree refusal | `tests/security/test_repository_confinement.py`, `tests/security/test_executable_path_confinement.py` | `HOME` inherited by Ranex's own git queries (`RISK-13`) |
| Refusal reporting | refused records are reported as refused, never as absence | 44 refusals no test executes (`RISK-09`) |
| Docs-discipline self-gauge | `tests/contract/test_docs_discipline.py` | the BOM checker is structural, not semantic (§5.5) |
| Red-then-green as git fact | `b495e3635` (red target) is an ancestor of `0762cf7428` (implementation) | ancestry is forgeable while history is unrewritten and unsigned (`RISK-20`) |
| Mutation census as calibration report | `mutmut` ran on the closing SLICE-004 commit: 880 survivors recorded (`docs/slices/done/SLICE-004-hermetic-observation.md:239-257`) | nothing consumes the result as a gate; no negative control (§8.4) |
| A/B/C canonical authority, lifecycle and grants | SLICE-029/030/032; canonical schemas/vectors, lifecycle transitions, signed approval, revocation reduction and intersected grants have executed contract, unit, integration and security gauges | owner-facing intake and installed harness composition remain outside the kernel-only release |
| Deterministic closed-DSL projections and manifest B | SLICE-031; generated flow/pseudocode/protected-gauge artifacts, mappings, controls and invocation metadata are digest-bound by manifest B | no owner-facing authoring product; today's suite freezes protected test IDs rather than complete test bodies |
| Trace integrity and real-subject bootstrap | SLICE-033/035; authority/evidence continuity and bootstrap against the real subject are exercised by repository gauges | common harness admission and the real concurrent mutation exit remain unproven |
| Landlock confinement of the bound command | ADR-006 accepted; SLICE-017/018/019/046 closed with qualification, lifecycle, host evidence and `cmd_run` attack gauges | the controller subprocess remains same-uid trusted infrastructure (§11.5 standing limit) |
| Dependency provisioning for gated suites | ADR-007 accepted; SLICE-006 closed; the self-gate runs from the approved SHA-256-addressed wheel store and `RISK-08` is closed | does not prove dependency consumption across the full installed harness composition |

### 15.2 IMMATURE / UNPROVEN — no complete composition running behind it

Two grades, worst last. The right column is the adoption question the owner's
rule asks of every unbuilt mechanism: is there code the world already runs that
solves this, or would building it be invention?

**Designed, unbuilt** — prose exists; never executed:

| Mechanism | State | Prior art to adopt |
|---|---|---|
| Harness core + delegation (own-built) | historical trimmed fork, bridge and first delegation landed (SLICE-007/008); the harness lane is stopped and no further production composition is planned in the kernel-only release | **Out of scope for this release.** Historical prior art and implementation remain provenance only |
| Owner-facing clarification and installed A/B/C/harness composition | kernel-side authority substrate built in SLICE-029–033 and SLICE-035; owner-facing intake, common admission and the real composed loop are not built | Out of scope for the kernel-only initial release; no completion claim |
| Budget, three-miss stop, escalation | designed; the only machinery serving `C-02`; nothing built | timeouts and circuit breakers are mature CI and distributed-systems patterns; the three-miss product question is a small, novel composition |
| Background worktree agent manager | `ADR-014` `proposed` (the bridge); milestone #2 and slice issues #1-#9 on this repository, renumbered SLICE-060-068 on 2026-08-17 — SLICE-010 is satisfied, but the manager is parked until the ADR-015 durability program closes; nothing built. The supervisor, durable run schema, leases, verification, orchestrator and UI are designed in those issues | **Split.** Temporal and DBOS prove the lease/fencing/recovery pattern (DBOS vendored under ADR-014); Codex's Apache-2.0 multi-agent protocol is read; vibe-kanban and Crystal prove the worktree-per-task manager form; the composition — a durable supervisor over N sessions in one governed process — is genuinely novel |
| Owner-facing intake and full harness compilation path | deterministic closed-DSL projection and manifest generation are built; interactive clarification and installed end-to-end consumption are not | **Split.** specification gates and artifact graphs are mature; the Ranex product composition is unproven |
| Harness common effect admission | historical ADR-017 design; shared service/family wiring/integration were withdrawn from this release | **Out of scope.** No harness leaf-admission or production-fanout claim |
| Rich verdict vocabulary | designed; the kernel has `PASS`/`FAIL` only | an enum and its refusal rules — small; the taxonomy decision is recorded in §4.5 |
| Independence record, canonical roles | designed in the pre-reset corpus only | no off-the-shelf equivalent; the composition is novel |
| End-to-end protected-gauge freeze line | approval, B-bound gauges, revocation and continuity components are built in SLICE-029–033 and SLICE-035; full harness enforcement remains unproven | read-only targets are mature; the installed composition remains unproven |

**Designed, unbuilt** — continued:

| Mechanism | State | Prior art to adopt |
|---|---|---|
| Production-configuration record (`PR-07`) | ADR-016 `accepted` 2026-08-09; measurement-local M0 not opened; no code | Six vendored source mechanisms under ADR-016; the Ranex composition is novel and UNPROVEN |
| Configuration comparison / measurement flywheel | ADR-016 `accepted` 2026-08-09; measurement-local M0 not opened; no treatment record or code | Six vendored source mechanisms under ADR-016; the Ranex composition is novel and UNPROVEN |

**Vague — not designed:**

| Mechanism | State | Prior art to adopt |
|---|---|---|
| The translator (§5.1) | absent; `C-04` unserved (`RISK-12`) | none — a read-only projection of *this* record is novel, and by §4.3 it may never be a model that decides anything |
| Outward-facing record | absent; deferred with §11.1 (`RISK-03`) | **Mature.** Certificate transparency is the solved form of this exact problem; see §15.3 |
| Approver authentication | no design; `RISK-07` | mature elsewhere (signature-bound approval); not yet designed here |
| Calibration consumption, negative controls | §8.4 names four consequences; none satisfied | negative controls are standard assay practice (§8.4); the machinery is small and unbuilt |

**The system-level verdict.** Every row in §15.1 is a component fact. The
kernel substrate and serial kernel path exist; the approved-specification
harness composition and production fanout are withdrawn, not pending release
gates (`RISK-14`, `RISK-25`). #19 / SLICE-036 is the sole retained next delivery
and remains qualification-only with publication blocked.

### 15.3 External maturity and the adoption rule — owner directive, 2026-08-03

The owner's standing instruction: mature, widely-used open source is itself
proven code, and where it solves a mechanism Ranex grabs and references it rather
than generating fresh code. This is the research rule of `CLAUDE.md` and ADR-003
stated as economics — invention is what needs justification, not adoption.

Compatibility is part of proof. Copy only the smallest exact implementation
whose licence can travel in this MIT tree, pin it, vendor it and preserve notice.
When a useful repository is incompatible, record only the behavior-level intent
and independently implement it from compatible sources or original requirements;
do not translate, port, or closely derive its code. ADR-017 applies this boundary
to AlphaCodium (`eb7577d`, AGPL-3.0): discussion reference only, never copied.

**The local shelf.** `opensrc` (vercel-labs, installed v0.7.3 at
`~/.local/bin/opensrc`) caches source under `~/.opensrc/repos/` so prior art is
read locally. Cached 2026-08-02/03, and each entry is prior art for a named gap:

| Cached source | What it is prior art for |
|---|---|
| `in-toto@3.1.0` (pinned release) | signed attestation layouts — the evidence-admission and independence-record rows |
| `github.com/google/trillian@master` | append-only Merkle trees — the journal's rollback/truncation gap (`RISK-19`) |
| `github.com/sigstore/rekor@main` | a transparency log in production — the outward-facing record (`RISK-03`) |

**The pinning caveat, stated because this repository's own rules state it:**
`trillian@master` and `rekor@main` are cached at *branch* refs, which ADR-003 and
`tests/contract/test_docs_discipline.py` reject as citations. They are readable
now; before either enters an ADR it must be re-fetched at a 40-hex commit or a
dotted-numeric release tag and vendored with origin and licence. `in-toto@3.1.0`
already satisfies the pin.

**The adoption form — copy, improve, own; never depend.** Owner directive,
2026-08-03: adopted code is copied into `src/ranex/`, improved, and maintained
as Ranex's own infrastructure. It is never added to the dependency graph. Two
reasons, both structural rather than stylistic: a growing dependency graph is a
maintenance liability no single implementer should carry, and Ranex's own gauge
cannot observe trees that need installed dependencies (§2.3) — accumulating
dependencies is precisely what would keep Ranex from ever gating itself
(`RISK-08`). The runtime graph today is two packages, each justified on its own
record (`pyproject.toml`); adopted code must not grow it. `docs/adr/prior-art/`
holds what was read as research evidence; adopted code lands in `src/` with its
attribution and licence preserved. Only licences compatible with MIT may be
copied in — a copyleft file changes what this repository can be distributed as,
and nothing else in the tree would catch it.

**The harness base and its quarry, recorded the same day.** opencode (MIT) is
the harness base: forked at a pinned commit, trimmed, molded to the kernel, its
attribution preserved. oh-my-openagent is the orchestration reference — studied
as a running tool and through its documentation; its code is SUL-1.0 (internal
use only, no commercial distribution, derivative works included) and never enters
this tree, converted or not. hermes-agent and OpenClaw remain quarry for later
surfaces (§2.1).

**What external maturity does not buy.** Proven elsewhere is not proven *here*:
adopted code still faces §15.1's standard — built, executed, and bound to this
tree — before it counts as part of Ranex. External maturity removes the need to
invent; it does not remove the need to verify.

---

## §16 Per-problem architecture — how each concern is defended

§1.3 names four concerns in the operator's words. This section draws the defence
of each, step by step. Every step is marked: **BUILT** carries executed evidence
(§15.1), **OPEN** is a scheduled gap with an ADR behind it, **ABSENT** has
nothing. These diagrams add no architecture; they project §5, §6 and §15 onto one
concern at a time, so the four pictures together are the whole system judged
concern by concern.

### 16.1 `C-01` — "It says done, it isn't" — mostly defended; holes named

```
 the agent reports "done"
        │
        ╳  the report is never read — the summary is discarded
        ▼
 [1] BUILT  the bound command is re-executed against a materialisation of
            the subject commit, every blob checked against the tree's
            object id (SLICE-004)
 [2] BUILT  exit code + subject digest signed Ed25519 (SLICE-001, SLICE-002)
 [3] BUILT  signature verified against the committed keyring; keyring and
            catalog read from the commit, never the worktree (SLICE-002)
 [4] BUILT  the record's argv digest is compared with the claim's bound
            command — a signed record of `true` cannot satisfy
            `tests-executed` (SLICE-003)
 [5] BUILT  absence, contradiction and self-approval each FAIL — never a
            default, never a skip (kernel)
 [6] BUILT  verdict + rule + subject + approver appended to the
            hash-chained journal
        │
        ▼
 PASS only if every required claim is satisfied by admitted evidence

 holes that remain: the approver is an unauthenticated string (RISK-07) ·
  the confinement controller is same-uid trusted infrastructure (RISK-06 standing limit, ADR-023) ·
 a consistent journal prefix survives row removal (RISK-19)
```

### 16.2 `C-03` — "It broke something else" — weak; the binding and the run exist, the regression view does not

```
 a change lands
        ▼
 [1] BUILT  evidence binds the post-change subject digest — a passing
            record for the OLD tree stops counting automatically (kernel)
 [2] BUILT  the gate's bound command IS the full suite
            (governance/gates.yaml: `uv run pytest -q`), provisioned and
            run sealed — SLICE-006 + ADR-007 landed, and SLICE-009 judges
            the manifest diff, not the exit code (RISK-08 closed)
 [3] ABSENT VP-06, the regression viewpoint, governs no view (§14.1) —
            "still works" has no definition and no measurement yet
        │
        ▼
 the full suite now runs under the gate; what "still works" means beyond
 the frozen manifest has no definition and no view yet (VP-06)

 holes: no regression view (VP-06) · no negative control (§8.4) ·
 880 surviving mutants are the calibration report on the checks themselves
 (RISK-09)
```

### 16.3 `C-02` — "Money gone, nothing finished" — nothing at all

```
 a run starts
        ▼
 [1] ABSENT wall-clock and spend bounds
 [2] ABSENT the three-miss stop
 [3] ABSENT plain-language escalation to the operator
        │
        ▼
 a run that cannot succeed spends until it is killed by hand

 PR-09 and ASR-09 name this; there is no design, no code, and VP-05
 governs no view (§14.1). The one concern with zero machinery — the wedge
 of §11.2, unbuilt.

 First scheduled machinery: the background worktree agent manager (§0.15).
Its supervisor owns wall-clock and spend bounds, cancellation, and
  escalation; none of it is built — ADR-014 covers only the bridge, the
  supervisor slice has no ADR yet, and everything here stays ABSENT until
  the durability program's SLICE-011 completes and the manager slices
  (SLICE-060-068, renumbered 2026-08-17) open — SLICE-010 is satisfied, but the manager remains parked
  until the durability program closes.
```

### 16.4 `C-04` — "I can't tell what it did" — the record exists; the reading does not

```
 what actually happened
        ▼
 [1] BUILT  every verdict recorded with its rule, subject digest and
            approver; model self-assertion is never recorded as fact (§8.3)
 [2] BUILT  `ranex journal verify` recomputes the chain for the operator
 [3] ABSENT the translator — no plain-language projection of run state or
            proof (RISK-12)
 [4] ABSENT the production-configuration record — model, harness version,
             skill and tool manifest, prompt digest (PR-07, ADR-016 accepted
             2026-08-09, unbuilt)
        │
        ▼
 the operator can verify integrity but cannot read the run — the record is
 a diary until the translator exists

 holes: RISK-12 · PR-07 · evidence.json keeps only the latest record per
 claim+producer, so it is not durable history (§8.3, RISK-11)
```

### 16.5 The whole board

| Concern | Built steps | What is missing | Defence today |
|---|---|---|---|
| `C-01` "done isn't" | all six of §16.1 | `RISK-07`, `RISK-19` (plus `RISK-06`'s standing controller limit) | mostly defended, holes named |
| `C-02` "money gone" | none | bounds, stop, escalation — all | **undefended**; nearest planned machinery is the agent manager (§0.15), parked behind P0 |
| `C-03` "broke other" | subject binding + the full-suite self-gate (SLICE-006, SLICE-009) | a regression view (VP-06) | weak — the suite runs; "still works" has no view yet |
| `C-04` "can't tell" | record + chain verify | translator, configuration record | record exists, unreadable |

One complete thread — Idea → Behaviour → Result — exists only for `C-01`, and
not yet around a real agent (`RISK-14`, `RISK-24`). The board is §1.3's coverage
table drawn as architecture; the two agree because both are read from the same
tree.

---

## §17 Trim spec — the compact engine

`PROVISIONAL` — the map-level spec the fork ADR will carry to pinned commits and
measured numbers. The classification below was read from opencode's package
structure on 2026-08-03, `dev` branch — a branch, not a pin. Every row is
confirmed against code at fork time or it moves to §17.3. **Done for the fork
point:** `ADR-008` re-confirmed these rows against `v1.18.11` and records the
corrections there (notably `server` and `sdk` are keep, `ui`/`client`/`codemode`
cut) — this section stays the provisional sketch, the ADR carries the pin.

**The owner's analogy is the doctrine.** We are not deleting parts from a bulky
V8. We are building a smaller, more compact engine that delivers **more
horsepower and better fuel economy** than the bulky one — each part trimmed down
but still as effective as it once was, and all parts interconnected like gears,
working as one full engine. Three consequences:

1. **Trim runs at two levels.** Cut what the engine does not need (§17.2), then
   lean out every part that remains (§17.1 is a keep-list, not a done-list).
2. **The claim is measured, not asserted.** Horsepower and fuel economy get
   definitions (§17.4), and the trimmed engine is proven against the bulky
   baseline on the same tasks. Smaller without more horsepower is not the goal —
   it is just smaller.
3. **The gears must mesh.** A pile of trimmed parts is not an engine. The fork
   ADR's closing proof is one task turning every gear in sequence: dispatch →
   loop → hooks → kernel judgement → journal, as one machine (§17.5).

**The criterion per package.** One question: *does a governed worker — dispatched
into a worktree, judged by an external kernel — need this to run?* The harness is
the most valuable asset that drives the AI agents (owner's words); everything
that does not serve that is bloat, overhead, or a surface someone will someday
customize into a hole.

### 17.1 KEEP — the lean core, each part itself to be leaned

| Package | Why it stays | Its trim |
|---|---|---|
| `opencode`, `core`, `cli` | The agent runtime and entry point: loop, tools, headless `run` | every feature the governed loop does not use is dead weight — named and cut at fork time |
| `llm` | Provider/model routing — the *recommended provider models* feature lives here | providers Ranex never routes to are configuration, not code |
| `plugin`, `protocol`, `schema` | The hook surface the kernel bridge collects through, and the contracts it speaks | hooks shrink to the handful the kernel needs (§17.4) |
| `tui` | The operator surface — the product is CLI-first (§7). Redesigned by `ADR-018` on its own track (§15.2): the board is the front door, added additively so the fork stays mergeable | minimal; the operator reads verdicts, not dashboards |
| `effect-drizzle-sqlite`, `effect-sqlite-node` | Session persistence, if `core` requires them | confirmed load-bearing or cut at fork time |

### 17.2 CUT — bloat for a governed harness

| Package | Why it goes |
|---|---|
| `desktop`, `web`, `console`, `session-ui`, `ui`, `storybook` | Desktop app, marketing lander, hosted console, web UI components — the Web UI is parked (§0.14), and parked means absent |
| `enterprise`, `identity` | Hosted identity and tenancy — Ranex is local-first, one operator (§7.2) |
| `slack` | A chat surface; quarry material for a later day, if ever (§15.3) |
| `sdk`, `sdk-next` | SDKs invite third-party extension — deep customization is blocked (§17.6) |
| `stats` | Usage statistics — a governance product does not phone home; verified inert or cut |
| `function`, `http-recorder`, `httpapi-codegen`, `script` | Serverless and development tooling, not product |
| `docs` | Upstream's documentation site; Ranex writes its own handbooks (§0.14) |
| Top level: `artifacts/`, `infra/`, `github/`, `sdks/vscode`, `sst.config.ts` | Marketing assets, deployment infrastructure, editor SDKs — no governed worker needs any of them |

### 17.3 ASSESS — read the code before deciding

`app`, `codemode`, `containers`, `client`, `server`, `nix`, `patches`, `perf`.
Each is either load-bearing for the core or irrelevant; the fork ADR decides per
package, against code, and records the verdict — including what `containers`
offers the confinement story, if anything.

### 17.4 Horsepower, fuel economy, and the things that waste both

The analogy's numbers, defined so they can be measured. **None are measured yet**;
the fork ADR takes the baseline (bulky upstream, same tasks) and must beat it.

| Measure | Meaning | Handling |
|---|---|---|
| **Horsepower** | Governed tasks completed: verdicts earned against frozen targets, per run | the kernel is the dynamometer — completion is what it already measures |
| **Fuel economy** | Tokens, cost and wall-time per completed task | budget layer turns this into a gate later (`C-02`); first it is simply recorded |
| Provider throttling | A stalled worker burns fuel standing still — `C-02` in miniature. This repo's own record: free-tier models stall after ~2 calls | a stall past bound is a recorded refusal, never a silent wait; model fallbacks per role |
| Context bloat | Every injected byte costs attention and tokens | handbooks are scoped per role — a worker reads its chapter, not the library |
| Hook overhead | Every lifecycle hook adds latency; the orchestration reference ships 54+ | the kernel bridge keeps a handful: exactly the ones that collect what the kernel judges |
| Per-task startup | Spawn and session init on every task | measured at fork time; worktree reuse decided by number, not taste |
| Session storage growth | Unbounded state on disk | bounded and rotated; the durable record is the kernel's journal, never the harness's sessions |
| Two runtimes | TypeScript harness, Python kernel — two toolchains, bridge latency | the wall is the point (§0.14): bridge over stdio/HTTP, no shared runtime, no shared trust |

### 17.5 The gears mesh — the closing proof

A trimmed engine is proven running, not listed. The fork ADR closes only when one
task turns every gear in sequence — foreman dispatches, the loop executes in an
isolated worktree, hooks emit references, the kernel materialises the committed
work,
judges, and journals the verdict — with no hand on any part. That run is also the
first delegation of §0.14's build order; the two are one milestone.

### 17.6 Customization policy — few knobs, deep customization blocked

Owner directive, 2026-08-03: *the AI harness is the most valuable asset that
drives the AI agent; the calibration is already made, so deep customization is
blocked; a few customizations, very easy, so users are not overwhelmed.*

The gauge argument makes this doctrine rather than taste: a gauge the user can
recalibrate is no gauge (§8.4). Deep customization of the harness is the user
editing the measurement process — after which a verdict states nothing. `RISK-15`
already names the hole: the operator writes the gauge and nothing checks it.
Users must not be able to widen it.

**Allowed — a short enumerated list, each easy, each recorded:**

1. Model/provider per role — the *recommended provider models* feature.
2. Budget caps — bounded choices for wall-clock and spend.
3. Handbook additions in a designated directory — read as guidance, never as
   authority; only the kernel enforces.

**Blocked — hard, and not by configuration:**

- Anything touching kernel authority: gates, claims, keyring, journal, verdict
  path. Not configurable, not overridable, not themed.
- Any plugin, hook, or tool surface that can intercept, weaken, or veto a
  verdict.
- Any extension mechanism that grows the surface — no marketplace, no SDK.

Adding a knob requires an ADR, and the default answer is no.

---

## Maintenance

Update when a slice closes, an ADR is accepted, or a `PROVISIONAL` claim gains or
loses evidence. Promote to `CONFIRMED` only on executed evidence; demote whatever
a slice contradicts. Record the command and its working directory beside every
number (outside repository: `/home/soultransit/devtony/ranex-FULL-BACKUP-2026-07-31/docs/architecture/reviews/2026-07-31-delivery-model-restructure-assessment.md:187-215`).

**The bill of materials is `governance/bom.yaml`; keep it aligned with executable
evidence rather than expanding this map.**
