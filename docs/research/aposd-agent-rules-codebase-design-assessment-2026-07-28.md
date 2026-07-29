# APOSD, Agent Rule Packs, and Codebase-Design Skills Assessment

| Field | Value |
|---|---|
| Document class | `Research` |
| Research ID | `RESEARCH-APOSD-SKILLS-001` |
| Version | `1.2.0` |
| Status | APOSD source reconciliation completed; third-party rule-pack/skill treatment and experiment remain `RESEARCH_ONLY` |
| Date | 2026-07-28 |
| Ranex base revision | `4baad4a67843b02d5970f442fb54aed8d6525dda` with a pre-existing dirty working tree |
| Owner | Human governor |
| Decision authority | None; this document cannot change architecture, policy, gates, permits, construction, merge, release, or runtime status |
| Runtime standing | `NOT_ASSESSED` |
| Definition-layer impact | APOSD is the tenth source family with four design-time practices in the 38-practice registry; generated definition contracts reflect that denominator |
| Runtime/practice standing | `SOURCE_RECONCILED_NOT_APPLIED` / `NOT_ASSESSED`; third-party rule packs, skills, and the seven-question treatment are not activated |
| Primary question | Which ideas, if any, should Ranex evaluate or later adapt from APOSD, `ciembor/agent-rules-books`, and Matt Pocock's architecture skills? |

## 1. Verdict

Ranex should evaluate a small qualitative design lens, not install or copy the
third-party rule packs and not create an APOSD policy engine.

The useful candidate ideas are:

- inspect caller knowledge, leaked decisions, change amplification, and
  scattered special cases;
- ask whether a public interface hides meaningful implementation complexity
  without hiding required authority, failure, data, or operational semantics;
- use current-code and frozen-history evidence to identify candidate
  architectural hotspots;
- compare materially different interfaces for consequential decisions; and
- use replacement/deletion thought experiments to expose mechanism coupling.

APOSD's primary-source ideas now have four explicit Ranex practice IDs for
complexity symptoms, deep modules, information hiding, and comparative design.
The third-party prompt/rule-pack treatment still overlaps substantially with
other Ranex complexity, alternatives, boundary, dependency, and fitness
practices. Its incremental value remains an empirical question: does the
additional treatment produce better decisions or merely more prose,
abstraction, interfaces, and review cost?

The following are not accepted:

- `# OBEY` or an instruction to follow a whole book;
- an aggregate APOSD-compliance or architecture-maturity score;
- a mandatory plugin, skill invocation, agent count, interface count, adapter
  count, or implementation-to-interface ratio;
- automatic edits to `CONTEXT.md`, ADRs, architecture, policy, or tests;
- automatic test deletion, mock-only proof, or a fake being sufficient
  justification for a production seam;
- mutable `main`, `@latest`, telemetry-bearing installation, CDN execution,
  Mermaid `securityLevel: "loose"`, or automatic browser opening;
- a fresh chat, model label, or alternative-design agent being treated as an
  independent reviewer;
- model review becoming a `GateOutcome`, merge authority, or release evidence;
  or
- evaluation results automatically promoting instructions or policy.

## 2. Authority and evidence boundary

This assessment follows the existing Ranex hierarchy:

1. accepted human decisions and ADRs;
2. the Core SDLC and applicable standards;
3. registered engineering-practice references;
4. exact upstream/runtime evidence;
5. advisory AI and third-party workflow research; and
6. local evaluation and operational evidence.

The local APOSD source is now reconciled at level 3 through exact-byte,
edition, rights, locator, limitation, and applicability records. The
third-party rule packs, skills, advisory analyses, and proposed experiment
remain at level 5. Neither level proves implementation, effectiveness,
maturity, or conformance.

Source observations, Ranex interpretations, owner decisions, runtime enactment,
and effectiveness results are separate claims. Terms such as `effective`,
`qualified`, `implemented`, `mature`, `best`, or `AI-G2 PASS` require their own
exact-subject evidence and are not used here.

## 3. Exact source lineages

### 3.1 Local APOSD representation

| Field | Observation |
|---|---|
| Logical source ID | `APOSD-LOCAL-PDF-2026-07-28` |
| Local path | `docs/research/books/PDFs/A.Philosophy.of.Software.Design.pdf` |
| Bytes | `1,659,085` |
| SHA-256 | `48cee0a4a0dfeeea6617b71252bf989df8a616ca389b9fc9e1bb5b1627441d61` |
| Container signal | PDF 1.4; 188 observed page objects; visible metadata names Calibre 3.14.0 |
| Embedded metadata claim | Title *A Philosophy of Software Design*; author John Ousterhout; Yaknyam Press; 2019-era creation/metadata timestamps |
| Edition/source identity | Observed First Edition v1.01, November 2018, from local front matter; official-file authenticity and acquisition chain remain unresolved |
| Rights | `NOASSERTION`, `LOCAL_ONLY`, `PROHIBITED_PENDING_RIGHTS` |
| Authority | Reconciled opinionated design reference under `ENGREF-APOSD-1E`; not lifecycle, decision, or runtime authority |

The file is now the PDF-only tenth lineage in the exact 18-artifact corpus.
Local front matter establishes the observed edition of these bytes, but local
presence, metadata, and a digest do not establish lawful acquisition,
official-file authenticity, conversion fidelity, permission to copy,
permission to use as model input, or public redistribution rights.

The public-safe canonical starting points are John Ousterhout's
[official book page](https://web.stanford.edu/~ouster/cgi-bin/aposd.php) and
[Stanford course material](https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=complexity).
Those pages do not authenticate the local PDF.

### 3.2 `ciembor/agent-rules-books`

| Field | Observation |
|---|---|
| Logical source ID | `CIEMBOR-AGENT-RULES-BOOKS-2026-05-22` |
| Repository | `https://github.com/ciembor/agent-rules-books` |
| Inspected commit | [`9c8763613514e4047d75c089533e09bc4b493c28`](https://github.com/ciembor/agent-rules-books/tree/9c8763613514e4047d75c089533e09bc4b493c28) |
| Commit timestamp | `2026-05-22T13:00:36+02:00` |
| License | MIT; copyright 2026 Maciej Ciemborowicz |
| License SHA-256 | `c21def7bbce1900717a361a06af67399903d31bd3a695757fff534d6698d1bdb` |
| Inspected-subset manifest SHA-256 | `2c2f49d869eaae48802e792955cfb0cef3733688286f533875a936f6d46c4386` |
| Evidence class | Third-party derivative rule-pack research |
| Independence | One repository lineage; its full, mini, nano, workbench, and traceability files are representations, not independent corroboration |
| Ranex disposition | `RESEARCH_ONLY`; do not install globally or copy wholesale |

The repository provides compact rule representations and openly identifies
limitations. Its adding workflow asks a model to reconstruct a book outline,
extract explicit and strongly implied rules, and upgrade wording into
`MUST`/`SHOULD` form. Its traceability is primarily to generated rule material,
not a claim-level, primary-edition page map. That makes it useful for studying
instruction compression but insufficient as primary evidence of APOSD.

The repository reports one early qualitative helpdesk/refactoring exercise.
The reported GPT judge result favored the rules treatment (`74` versus `46`),
while the reported Reek totals were close (`1077` versus `1083`). The
repository itself does not present this as a general benchmark. The narrow
supported inference is that explicit rules affected one model/setup more than
merely naming a book; it does not establish faithfulness, general benefit, or
Ranex fit.

The repository's MIT license covers its repository material under its notice.
It does not independently settle rights in third-party books, reconstructed
expression, or other source material.

### 3.3 Matt Pocock architecture skills

| Field | Observation |
|---|---|
| Logical source ID | `MATTPOCOCK-ARCHITECTURE-SKILLS-2026-07-28` |
| Repository | `https://github.com/mattpocock/skills` |
| Inspected commit | [`2ab958093e83e0ec752e6c1c5932da465bf23e0c`](https://github.com/mattpocock/skills/tree/2ab958093e83e0ec752e6c1c5932da465bf23e0c) |
| Commit timestamp | `2026-07-28T10:18:17+01:00` |
| Release relation | Inspected commit; no release/tag relation was established for this assessment |
| License | MIT; copyright 2026 Matt Pocock |
| License SHA-256 | `0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5` |
| Inspected-subset manifest SHA-256 | `087287ad1faf0b4c304ee43aafe9fd7355322c9c6f087b1e2a1bb5833796d0fa` |
| Evidence class | Third-party workflow prior art |
| Independence | One repository lineage; the skills and helper files are not independent corroboration |
| Ranex disposition | Link and paraphrase; do not install, vendor, or activate |

At the pinned commit,
[`improve-codebase-architecture`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/improve-codebase-architecture/SKILL.md)
is a user-invoked discovery workflow. It prioritizes a supplied target or
recent-change hotspots, reads repository/domain/ADR context, creates candidate
reports, waits for user selection, and grills a selected candidate.
[`codebase-design`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/codebase-design/SKILL.md)
provides deep-module vocabulary and contextual design heuristics.
Alternative-interface generation is a separate, conditional workflow.

Useful characteristics are hotspot-first inspection, human candidate
selection, discovery before interface proposal, replacement/deletion
questions, and deliberate alternative design.

Direct-use blockers are:

- transitive dependencies on other skills, Git/history, temporary files,
  browser opening, Tailwind, Mermaid, and tool-bearing subagents;
- assumptions about `CONTEXT.md` and `docs/adr/` that conflict with Ranex's
  canonical registries and `docs/architecture/decisions/`;
- alternative designers acting as co-designers rather than independently
  qualified reviewers;
- vocabulary rules that prohibit canonical Ranex terms such as `service`,
  `API`, and `boundary`;
- contextual heuristics written as absolutes, including in-process
  deepening, adapter counts, result/effect preferences, test placement, mock
  usage, method/test-count implications, and deletion of prior unit tests;
- a report described as self-contained while loading remote Tailwind and
  Mermaid assets and selecting loose Mermaid security; and
- no checked-in evaluation harness or package test/eval command specific to
  this skill pair found in the inspected tree.

The final absence statement is deliberately scoped to the inspected public
tree. It is not a claim that no private or external evaluation exists.

### 3.4 User-provided GPT analyses

| Logical source ID | Bytes | SHA-256 | Disposition |
|---|---:|---|---|
| `GPT-ANALYSIS-BOOK-TO-CONTROLS-001` | 10,841 | `bac38eef449e8a250033b85ff680dd516da7644c6e69e4fc0a9c8e119eedb6c5` | Secondary analysis |
| `GPT-ANALYSIS-CONTROL-ARCHITECTURE-002` | 13,146 | `f08b54b0425fbead4a5017d5086017bebf1369edfb3f3c9fda21a18edc5f59cd` | Secondary analysis |
| `GPT-ANALYSIS-MATT-SKILLS-003` | 15,007 | `71c6b9ffd505aa5f8ca6fbd1cbd209194c9499536b3f786ee6cf843666282524` | Secondary analysis |

The supplied bytes are identified by logical IDs and digests; absolute
attachment paths are intentionally excluded. Provider, exact model snapshot,
system prompt, tool trace, source snapshot, run/session identity, and reuse
rights were not retained. They form one three-item advisory-attachment corpus,
not three qualified independent reviews or primary sources.

The analyses correctly emphasize scoped instructions, design records,
deterministic checks, qualitative review, and evaluation. Corrections required
before Ranex use include:

- replace claims that the integrated workflow is "proven" with the narrower
  statement that individual controls are documented while this exact
  combination remains unevaluated;
- replace "prevents" with "is intended to reduce the risk of";
- preserve `UNKNOWN`, conflict, checker-fault, timeout, stale-subject, retry,
  recovery, permit, landing, release, operation, and rollback paths;
- keep review separate from gate, human decision, grant, permit, landing, and
  release;
- reject fresh context alone as independence;
- keep learned instructions quarantined until exact human acceptance; and
- remove unsupported superlatives and undefined maturity labels.

## 4. Mapping to existing Ranex practices

| Candidate idea | Existing Ranex home | Proposed treatment |
|---|---|---|
| Caller knowledge and leaked decisions | `ENGREF-APOSD-1E-COMPLEXITY-SYMPTOMS` and `ENGREF-APOSD-1E-INFORMATION-HIDING` | Apply as qualitative, evidence-bound diagnostics, not new authority or a score |
| Change amplification/locality | APOSD complexity symptoms plus boundary, coupling, dependency, and feedback fitness | Apply the primary-source practice; separately evaluate whether the third-party treatment improves findings beyond existing checks |
| Scattered special cases | Cohesion, ownership, duplication, and state/effect rules | Require exact locations and affected owners; no generic style finding |
| Deep module/interface leverage | `ENGREF-APOSD-1E-DEEP-MODULES` and owned context public APIs/ports | Qualitative, consumer-relative inquiry only; no LOC/method/count ratio and no god-module exception |
| Hotspot discovery | Core `DISCOVER` evidence | Freeze target and history range; churn proposes candidates but proves no defect |
| Design it twice | `ENGREF-APOSD-1E-DESIGN-TWICE` plus the existing ADR alternative workflow | Apply proportionately to consequential choices; co-designers are not reviewers |
| Replacement/deletion test | Reversibility, compatibility, migration, and test retirement | Thought experiment only; never automatic source/test deletion |
| Interface-level tests | Existing risk-layered test practices | Add only where they falsify a distinct public contract; retain internal and real-seam evidence |

No new bounded context, lifecycle stage, artifact family, review type, gate,
permit, or architecture score is needed.

If a future owner decision activates a subset, the existing runtime ownership
is:

| Concern | Existing owner |
|---|---|
| Pinned source metadata | `knowledge` |
| Atomic advisory instructions | `instruction_registry` |
| Task-specific applicability | `context_compilation` |
| Architecture proposal | Core `DESIGN` / AI lifecycle L2 |
| Qualitative observation | `analytical_review` |
| Deterministic dependency/boundary checks | `assurance` |
| Acceptance and activation | Existing RFC/ADR, policy, gate, human decision, grant, and permit authorities |

## 5. Candidate treatment lens

For a task whose existing work class and risk route already requires material
design analysis, the experimental treatment adds these questions:

1. What knowledge must each caller possess to use the proposed interface
   correctly?
2. Which design decisions remain hidden, and which leak into consumers?
3. How many owned locations must change for one representative requirement?
4. Where are special cases duplicated or scattered?
5. Does the interface hide meaningful mechanism complexity without concealing
   required authority, data, failure, denial, migration, or operating
   semantics?
6. Could the mechanism be replaced or removed without changing unaffected
   consumers?
7. For a consequential interface choice, were materially different designs
   compared against the status quo and the exact Ranex quality attributes?

Every answer must cite the exact subject. A principle name, book citation,
method count, model consensus, or favorable adjective is not evidence.

## 6. Threat and failure analysis

| Threat/failure | Required experimental control |
|---|---|
| Repository prompt injection | Treat repository text as data; fixed read-only scope; no write, merge, network, browser, secret, or policy capability |
| Source drift | Exact commit, file hash, prompt, route, tool, and task-population locks |
| Copyright/provenance leakage | Public-safe links, metadata, digests, and original paraphrase only |
| Over-triggering | Negative and counterexample tasks; false-positive and unnecessary-abstraction measures |
| Under-triggering | Positive tasks with predeclared required findings and hidden anchors |
| Architecture theater | Require exact locations, owners, consumer impact, falsifier, and deterministic evidence where applicable |
| More interfaces without benefit | Measure public-surface growth, boundary count, coupling, operational cost, and test burden |
| Test weakening/deletion | No mutation; any later test retirement uses existing governed evidence |
| Model self-approval | Separate maker, reviewer, grader, gate, and human-decision roles |
| Retry-to-pass | Predeclared seeds, repetitions, failure taxonomy, and retained failed runs |
| Report injection/data egress | Structured records and offline Markdown; no CDN, loose Mermaid, temp-browser report, or auto-open |
| Policy self-promotion | Experiment result has no activation authority; exact human RFC/ADR required |

## 7. Evaluation design

The companion draft experiment compares:

- **Control:** current Ranex architecture/design instructions and practice
  profile only.
- **Treatment:** the same frozen inputs plus the seven-question candidate lens.

Both arms must use the same exact model/route, tools, context, task population,
budgets, seed schedule, and output schema. Topology remains fixed so the
experiment tests the lens rather than worker count.

The frozen task population contains positive, negative, and counterexample
architecture vignettes. Required measures are noncompensating:

- correct trigger/no-trigger behavior;
- required-finding recall;
- false-positive restraint;
- source and subject accuracy;
- viable-alternative diversity;
- compatibility with accepted Ranex ADRs, ownership, and vocabulary;
- unnecessary abstraction, public-surface, and boundary growth;
- deterministic architecture-check compatibility;
- task correctness, rework, and defect outcomes when implementation tasks are
  later authorized;
- authority/security/test-retirement violations;
- human review effort, latency, tokens, tool calls, and cost; and
- grader false-accept/false-reject calibration.

The acceptance margin and minimum detectable effect remain unset until a
non-decision pilot estimates variance and grader reliability. No arbitrary
percentage or aggregate score may fill that gap. Insufficient evidence remains
`UNKNOWN`.

## 8. Third-party treatment promotion path

The primary APOSD source is now registered at the definition layer as four
locator-backed, qualitative design practices. That registration does not
authenticate the local file's acquisition chain, settle its rights, activate
an instruction pack, prove task applicability, or establish runtime enactment
or effectiveness.

The separate seven-question treatment synthesized from the assessed
third-party material cannot enter an active instruction profile or affect
governed work until all of the following exist:

1. confirmation that the exact APOSD source, locators, limitations, and rights
   disposition remain current;
2. a registered experiment with qualified route/harness/verifier identities;
3. frozen task and verifier-only hidden-anchor populations;
4. predeclared uncertainty, acceptance margin, stop rule, and failure handling;
5. retained baseline/treatment raw evidence and analysis;
6. independent challenge, including HY3 and DeepSeek only if their exact routes
   are available and qualified;
7. an RFC identifying only the nonduplicative instruction changes, conflicts,
   compatibility impact, and rejected absolutes;
8. authenticated human acceptance through a new ADR; and
9. atomic instruction-registry, compiler, schema, profile, manifest, and
   generated-contract regeneration and validation.

Even after paper adoption, runtime enactment and effectiveness remain separate
`NOT_ASSESSED` claims until exact runtime evidence exists.

## 9. Current standing

| Question | Result |
|---|---|
| Were the requested sources inspected at immutable revisions or byte digests? | `YES` |
| Were multiple analytical roles used? | `YES`, as separately tasked advisory roles; formal independence is not retained or independently auditable |
| Did HY3 and DeepSeek advise on direct adoption? | The execution reports `YES` and a shared rejection of as-is activation; retained repository evidence cannot independently verify that result |
| Is their prior consultation a qualified runtime review artifact? | `NO` |
| Is APOSD now a tenth registered source family? | `YES`, at the definition/design layer with four practices; this is not runtime enactment |
| Were Matt's skills installed or vendored? | `NO` |
| Did the practice denominator or generated definition contracts change? | `YES`, from nine/34 to ten/38 as part of the live-corpus reconciliation |
| Did any lifecycle, gate, permit, runtime, conformance, or effectiveness status change? | `NO` |
| Is a controlled evaluation registered or executed? | Draft specified; not registered or executed |
| May the candidate affect construction, merge, or release? | `NO` |

The honest disposition is:

> **Source-audited and experiment-specified research candidate; no normative,
> executable, runtime, conformance, or effectiveness claim.**

## Appendix A — inspected `ciembor` subset

The commit already provides immutable Git identity. The SHA-256 values below
also bind the exact bytes inspected outside Git's hash algorithm.

| Path | Git blob | SHA-256 |
|---|---|---|
| `README.md` | `b3d0bc65e12f7bbd2fb0d0824f10982c3beb0779` | `eed1b39633c3ca898abfd3c45dc384d490dbcf5c6d93361727b674dae57f4a03` |
| `LICENSE` | `cd8d62d37497c0bd8d4124e895648850d4ca815a` | `c21def7bbce1900717a361a06af67399903d31bd3a695757fff534d6698d1bdb` |
| `a-philosophy-of-software-design/a-philosophy-of-software-design.md` | `02d9d5410165937d74c55cd17d9427175180343f` | `b521814b9d050d0d12594e13aa291029148a971b6f7d5a5ac3e74219de6c8563` |
| `a-philosophy-of-software-design/a-philosophy-of-software-design.mini.md` | `a7d88383dd909a97b423d5f54d308cb2049e9a5a` | `ad8d9bd764179c0d2fea95f2bee3e25d443589a12fec84bfead52bdd94b4645a` |
| `a-philosophy-of-software-design/a-philosophy-of-software-design.nano.md` | `866c3e0c2f49416e461aca74c013afd1e8123098` | `da780d76b862eb181554548f551493bcaa40ca25a550e2d02d3c67a7885ca6c7` |
| `docs/ADDING_THE_BOOK.md` | `c928642bc1a45b5570aada0542a7dd6f360b6918` | `470ee3ec821df2939231e25bfd347c24de6639270d6ca6485075863392e1d9a2` |
| `docs/COMPATIBILITY.md` | `486d606055809488c4754f53c1c36f6310baf1dc` | `d426409dd3152c1446ab07eac4d42adbafd60c261d4748591394c735dd39b605` |
| `docs/CRITICISM.md` | `e1d6bd73f4010f68ca69c00a01492ded6d5f2a9c` | `ba38e3d90671c35b2bc8f009b2be90f27e54f73f62d3e13e9ea5a0b3d8327050` |
| `docs/USAGE.md` | `bdb21fd2880a9e9ff4ed019bb3decc0c3b151d42` | `b71870bb131339d9a6a72e8c9d3f91538cb52da86c780c16871574b569613307` |
| `_rule-workbench/PROCESS.md` | `418b1fc4fba31f7e55e8b9111a336a96a6902f77` | `c02fb08e61f54c4551fce00b17af4d597eaff2028d3cdce04fc8d70387350ab7` |
| `_rule-workbench/RELEASE.md` | `82fd8aa82af32bfeda274478adab0275e560bf3e` | `cbe0551d19fd58fd38c2249ff1d8a80f52d61b23f723fe8f36ad456b647b13bd` |
| `_rule-workbench/a-philosophy-of-software-design/traceability.md` | `05ceb35a4a2902df371192396902f1db15f5c210` | `ec8c162ef0fab004437f9bf336fce6cf174f6e29d8082544c28b141fec14f66c` |

## Appendix B — inspected Matt subset

| Path | Git blob | SHA-256 |
|---|---|---|
| `README.md` | `eb26335f5ad16adc027ddac412c255f952099f08` | `6fab7e1acf0a5dede8691cb4dd50630677874f8284ad121a97097c36466b0f71` |
| `LICENSE` | `f1dd2c09108dde1a5f56097cee8461b3ea834499` | `0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5` |
| `package.json` | `ac2c8d2d39e47f25b09b3d891b4a8ac0c9807cf4` | `bce70fe1a4fe94109c78b4a51824bacd33898287a6e14df40376dc6ea2d8edc8` |
| `.claude-plugin/plugin.json` | `99d7c4c66f0ab8b6ffb41bdac26cd8675d33d5dd` | `e712cc026f5e78058067d17cd1fdf9665388d70db59dc50688286cb029e38eba` |
| `skills/engineering/codebase-design/SKILL.md` | `16620c24528b737408e78d95dd6a0e01a98d3d63` | `a8d50abac5a4018f60e1d911d4b6f4e36454ca14d6c390c0695a578c7de65dad` |
| `skills/engineering/codebase-design/DEEPENING.md` | `3938457b88ddf98262d5f461aac703dbd74f749a` | `125e6b77413ad2bc7cf7a772bc74336d580a50f9e797db2178ed133d62333d06` |
| `skills/engineering/codebase-design/DESIGN-IT-TWICE.md` | `49a7c42a2ccc6aff0ffc09efd28e6a4aa3c373d7` | `21c3264953bd30ee87b181a3ccaf0e70649f461e5ffd7dc654acee4ba1788b31` |
| `skills/engineering/codebase-design/agents/openai.yaml` | `3180715edb37f6e96bec42f92f00169faa8886ef` | `edebc9e4fcfe102114012575eaa9600b9b5fd08c311664f389c36e7bc717740f` |
| `skills/engineering/improve-codebase-architecture/SKILL.md` | `b56969e92f0705d70700f908b8ec929a1edfa782` | `4b4cb798c3863d5b6f5c0b4604af1ecb5beb6df82553c972898a91ba38bcf289` |
| `skills/engineering/improve-codebase-architecture/HTML-REPORT.md` | `17f6d2c7b8342ee7c4260d8d98024d462c7d3eaa` | `0b0936104158abeef7246ff6cbabefa4dc055f17589f2833f2d93001421910a1` |
| `skills/engineering/improve-codebase-architecture/agents/openai.yaml` | `706fdca096da5937fe57875a9154017d50668c42` | `c8cb20f68ebf0edb4e497bc11ae5fcaa196004e661cd189015b04f4109ced7f1` |
| `skills/productivity/grilling/SKILL.md` | `52d8eb3cadd2dca62634d5dccfa73ea6b725b117` | `44331dda57f461db4fec3f2efb6ddabe7aaaa0a57ae0f88a883bc61aed8a0587` |
| `skills/engineering/domain-modeling/SKILL.md` | `d0f7e1a5ccb06a7184056ff9af02b67bc77f9dda` | `152e2c97239affb12a60c5f4a7e74ab546a49ae169688c81f4e2ccc42dafa579` |
| `skills/engineering/implement/SKILL.md` | `7a0b11f5f4fe9505ea5c7983c3083ba1bf754f69` | `6d3fd9e83b8f36e5213854779db49b256a457a7ebb4a503e53fa7dcff696adc3` |
| `skills/engineering/code-review/SKILL.md` | `2a0b5240731b927caa9ac0bf43c3e2af9dc3f0a7` | `6a65cc61114f96db07ec41e3920e67c9c5bf70dd6e0901eb9460ebcb2bdc209f` |
| `skills/engineering/tdd/SKILL.md` | `9a2e1d2a1ad856b0d5903dd002209ff8c32c9a48` | `5363bb2775679fe9311fbb67947f95359169c6e7f1fac77c0f25e190bca6cf2f` |
