# Live Foundational Software-Engineering Reference Corpus Reconciliation

| Field | Value |
|---|---|
| Review ID | `REVIEW-ENG-REF-002` |
| Version | `1.0.0` |
| Status | Complete live-corpus inventory and source reconciliation; practice conformance and public redistribution unproven |
| Date | 2026-07-28 |
| Owner | Human governor |
| Exact corpus | Nine conceptual works represented by eight PDF/Markdown pairs and one PDF-only work |
| Corpus count/size | 17 files / 86,856,268 bytes |
| Manifest | [Live corpus SHA-256 manifest](./artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256) |
| Manifest SHA-256 | `24517b0975ed5c4c601ac482f6403c28b3570719333c1f1f1c83bff7c59a8e18` |
| Work/representation index | [Live corpus index](./artifacts/foundational-reference-corpus/2026-07-28-live-corpus-index.json) |
| Practice-source dataset | [Engineering-reference practice registry](../../research/engineering-reference-practice-registry.json) |
| Resulting map | [Ranex Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md) |
| Superseded live baseline | [Six-work reconciliation](./2026-07-27-foundational-reference-corpus-reconciliation.md) remains an immutable historical snapshot |
| Decision authority | Human owner inside applicable law, contract, license, and policy; this review is advisory evidence |
| Provenance class | `CURATED_RESEARCH`, `NOASSERTION` |
| Repository inclusion | `LOCAL_ONLY`; `PROHIBITED_PENDING_RIGHTS` |
| Release standing | Blocking for any public commit, package, mirror, prompt bundle, or deployment input containing a full-text representation |

## 1. Verdict

The live directory now contains **17 stored artifacts representing nine
conceptual works**. Every current artifact is hashed, assigned to exactly one
source family, and classified in the licensing manifest. A PDF/Markdown pair is
one source lineage, not two independent corroborating sources.

The three works added after the six-work review are:

1. *Designing Data-Intensive Applications*, a PDF/Markdown pair derived from an
   explicitly unfinished Sixth Early Release;
2. *Fundamentals of Software Architecture*, a First Edition PDF/Markdown pair;
   and
3. *Clean Architecture*, a PDF-only Calibre representation.

They materially strengthen the architecture question set around data-system
failure semantics, time, fencing, event derivation, architecture
characteristics, fitness functions, decision records, dependency direction,
component boundaries, and enforceable encapsulation. They also expose
unresolved decisions. Their presence does **not** prove that the current Ranex
architecture follows them or that their recommendations fit every capability.

The corpus remains unsafe to publish on the available evidence. Every full-text
representation is therefore:

```text
classification: CURATED_RESEARCH
license: NOASSERTION
repository_inclusion: LOCAL_ONLY
redistribution: PROHIBITED_PENDING_RIGHTS
release_blocker: true
```

The reconciled decision is:

> Use the exact local bytes as non-authoritative research inputs; compile
> original Ranex syntheses and applicability rules from them; require
> subject-specific alternatives and verification; never publish the full text
> or claim implementation/conformance without separate evidence.

## 2. Method and counting rule

The audit dynamically enumerated every regular file below
`docs/research/books`, then:

1. captured path, byte size, SHA-256, media type, and available PDF metadata;
2. grouped representations by intellectual work and assigned a stable
   `ENGREF-*` source-family ID;
3. inspected front matter, edition signals, rights notices, retained scope, and
   extraction defects;
4. reconciled original, non-reconstructive practice summaries to exact
   section/page/line locators;
5. recorded accepted, adapted, rejected, and confirmation-required uses;
6. mapped the source families to lifecycle and architecture concerns;
7. classified every saved path for release and repository inclusion; and
8. generated a machine-readable practice-source dataset for the future
   contract compiler.

The audit does not establish lawful acquisition, authenticity of an official
distribution, permission, ownership, complete conversion provenance,
extraction accuracy, implementation, effectiveness, or standards conformity.

## 3. Exact live inventory

| Source family | Work | Stored representations and SHA-256 |
|---|---|---|
| `ENGREF-SWEBOK-V4A` | SWEBOK Guide V4.0a | PDF `b3cb8028fecb9607f757504c861947fa3bf423087ea8bf08c58020f0ba3596dc`; Markdown `26a2eb8585c93cf77a60bed26e15695892941c14e38a2587054034904e291ce7` |
| `ENGREF-CODE-COMPLETE-CH5` | Code Complete, Second Edition, retained Chapter 5 excerpt | PDF `018235406bd1a515e361b579382cce72fa0e773f1796dbf316d91947a0e3d252`; Markdown `081150569d686a3f38ec471e86cf61151ebc33eeaa19937c38d5940a0e6e28aa` |
| `ENGREF-CLEAN-CODE` | Clean Code | PDF `034292d5e0a2e27bc3444ff41216139537b4e0729661c79ee0a8ad3298db3857`; Markdown `f44a1ba7b8da08642c7ee4a557ba4e9aea7b9befedac4686c2d141d4a916377c` |
| `ENGREF-PRAGMATIC-PROGRAMMER-1E` | The Pragmatic Programmer, original first edition | PDF `7c8ad03780b2905e0cd47e3f5c60bd0474a718e7e7133ca226ef05828011ef20`; Markdown `fcd45290aa0d53e6468d5110caed549dbfcac1b8d3ad3183737447bbd05f0768` |
| `ENGREF-SYSTEM-DESIGN-INTERVIEW-2E` | System Design Interview, Second Edition | PDF `d2bafdef03246a64e3c58049c5ae188d8be9d74c6b23f05045637b07ad7167df`; Markdown `340ed9c4e03d88ea89f949cb1d038f15cea855a7e3004718992c588d5372f972` |
| `ENGREF-CLEAN-CODER` | The Clean Coder | PDF `73f64ac2e6f2bb18f0cbc2879b636c031ee3fe98eba0cc0a04ce8203d7aec90b`; Markdown `b37771c0dc990b225bcbc5f0de1b5dbd6c496240e9fa47bacfce12bc7bf2f899` |
| `ENGREF-DDIA-1E-ER6` | Designing Data-Intensive Applications, Sixth Early Release | PDF `905e1348c2b7955a3e799998ce9b45993b5c8cfa9ef6b93931af7a780b71ac02`; Markdown `5ffa700462ce50dc05067d052c3742fdc79809c840b4412805b70dee6acd204f` |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E` | Fundamentals of Software Architecture, First Edition | PDF `5008352574b214d08e4e831288a4e628355557fb73a927f91eda411c2ba1a546`; Markdown `3aa8f1351047d0900abe793c543b280fee188c7d93525d8455ec2050683873a1` |
| `ENGREF-CLEAN-ARCHITECTURE-1E` | Clean Architecture, First Edition | PDF `1973f36809f8bd696578e05a6975f5b96117a26359a51e1eb1b036f3c615ff07`; no Markdown representation |

The authoritative path, byte-size, representation, and grouping details are in
the machine-readable index. The manifest contains all 17 paths and no
directory-glob claim.

## 4. Provenance, edition, extraction, and rights

### 4.1 Shared gaps

No work has a complete local acquisition and custody record. The corpus lacks:

- purchase, loan, download, or other acquisition evidence;
- uploader identity and custody history;
- a grant covering each stored representation;
- PDF-to-Markdown conversion command, tool version, run ID, and log;
- page-to-line derivation maps; and
- human proofreading and extraction-validation records.

The hashes prove only which bytes were reviewed.

### 4.2 Per-work limitations

| Source family | Observed edition/provenance | Extraction/scope limit | Rights/privacy signal |
|---|---|---|---|
| `ENGREF-SWEBOK-V4A` | Version 4.0a, September 2025 | Markdown is a lossy searchable projection; guide is a knowledge map, not a complete lifecycle | IEEE copyright/use conditions; no blanket redistribution grant established |
| `ENGREF-CODE-COMPLETE-CH5` | Second Edition excerpt | PDF is 120 pages; only retained Chapter 5 content is evidence | Microsoft Press reproduction restrictions |
| `ENGREF-CLEAN-CODE` | Pearson first-edition, 2009-era practice context | Atypical 27-page PDF container; Markdown loses code/image fidelity | Pearson copyright and permission-required language |
| `ENGREF-PRAGMATIC-PROGRAMMER-1E` | Original first-edition text; local 25th printing dated 2010 | Dated tools; contextual practice, not current security guidance | Restrictive notice and repeated named-third-party personalization |
| `ENGREF-SYSTEM-DESIGN-INTERVIEW-2E` | Second Edition, 2020 interview context | Markdown omits all 207 referenced figures; examples are simplified interview exercises | Copyright/all-rights/no-reproduction language |
| `ENGREF-CLEAN-CODER` | 2011 first-edition context | Images absent and estimation formulas are corrupted in Markdown | Pearson restriction and ebook-origin metadata |
| `ENGREF-DDIA-1E-ER6` | Revision history ends at Sixth Early Release, 2016-07-11 | Front matter contains placeholders; several chapters are explicitly unwritten; security, deployment, operations, ethics, and management are excluded | Copyright 2016 Martin Kleppmann; all rights reserved |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E` | First Edition, February 2020; local front matter records fourth release 2021-02-12 | Qualitative tables/diagrams need PDF verification; generic style ratings are not Ranex measurements | Copyright 2020 Mark Richards and Neal Ford; all rights reserved |
| `ENGREF-CLEAN-ARCHITECTURE-1E` | XMP identifies Robert C. Martin, Pearson, 2017 date, ebook ISBN `9780134494326`; copyright page says 2018 and print ISBN `9780134494166` | PDF-only, Calibre 2.51, 364 sequence pages; no conversion/acquisition record | Copyright 2018 Pearson; all rights reserved and permission required for prohibited reproduction |

The DDIA edition defect is material. The local Markdown itself records the
early-release history and placeholder fields at lines 1–29, calls the copy
unfinished with unwritten chapters at lines 344–348, and limits its scope at
lines 320–342. It must not be described as the completed first edition.

## 5. Per-reference architecture disposition

### 5.1 `ENGREF-SWEBOK-V4A`

Adopt as the broad discipline-coverage map. It lists 18 knowledge areas in the
exact Markdown at lines 1568–1614. Use it to find omitted engineering
responsibilities, not to assert a Ranex lifecycle or ISO/IEC/IEEE 12207:2026
clause mapping.

### 5.2 `ENGREF-CODE-COMPLETE-CH5`

Adopt retained Chapter 5 for design during construction, essential versus
accidental complexity, information hiding, cohesive decomposition, interfaces,
testability, and proportionate iterative design. Exact local locators include
lines 831–982, 1002–1065, and 1273–1395.

Reject claims based on absent chapters. Emergent local design cannot be used to
defer authority, persistence, security, recovery, or public-contract decisions
until coding.

### 5.3 `ENGREF-CLEAN-CODE`

Adopt owned wrappers around third-party boundaries (lines 3128–3454),
construction/runtime separation (lines 4098–4158), and small regression-backed
refactoring (lines 5219–5429).

Reject code-only authority, universal TDD, language-specific size dogma, and
the idea that local object cleanliness proves system failure, security,
concurrency, or lifecycle behavior.

### 5.4 `ENGREF-PRAGMATIC-PROGRAMMER-1E`

Adopt DRY as one owner for knowledge (lines 1214–1229), orthogonality
(1393–1449), reversibility (1730–1762), and production-shaped tracer learning
(1792–1842).

Adapt DRY so it cannot create shared domain ownership or a god database. Adapt
tracer bullets as routes through a mapped destination; a tracer never defines
or shrinks product scope. Dated tool and team prescriptions require current
security and organizational evidence.

### 5.5 `ENGREF-SYSTEM-DESIGN-INTERVIEW-2E`

Adapt the four-step interview method at lines 593–729 into requirements/scope,
complete high-level decomposition, risk-selected deep dives, and tradeoff/
failure/operations reconciliation.

Reject interview time boxes and web-scale examples as policy. Caches, queues,
shards, replicas, and multi-region patterns require measured load, consistency,
failure, recovery, security, and operating evidence plus an accepted decision.

### 5.6 `ENGREF-CLEAN-CODER`

Adopt executable acceptance examples (lines 2652–2674), risk-layered
verification (2928–2998), transparent risk/lateness disclosure, and separation
of estimate from commitment (3390–3404).

Reject universal test-pyramid percentages, coverage targets, fixed hours,
staffing ratios, TDD as the sole professional method, heroic commitments, and
“QA should find nothing” as a process objective.

### 5.7 `ENGREF-DDIA-1E-ER6`

Adopt or adapt only with the edition warning attached:

| Claim family | Exact local locator | Ranex disposition |
|---|---|---|
| Reliability, scalability, maintainability | Markdown lines 435–823 | Adopt as quality-attribute questions; bind exact faults, load, distributions, operability, and evolvability |
| Wall clock versus monotonic time | 6970–7005 | Adopt for elapsed-time and timeout design; prohibit cross-host comparison of local monotonic values |
| Process pauses and fencing | 7120–7306 | Adopt resource-enforced monotonically increasing epochs; a client lease check alone is insufficient |
| Dual-write/change capture | 10420–10487 | Adapt to local atomic state/outbox ownership, ordered derivation, duplicate handling, lag, replay, and reconciliation |
| Commands, immutable events, and derived state | 10505–10609 | Adapt to selective journal/reducer use with explicit consistency, snapshots, replay, retention, correction, and erasure |
| Atomicity/idempotence and retry | 10915–10942 | Adopt exact operation identities and reconciliation; reject end-to-end “exactly once” overclaims |

The fencing discussion assumes unreliable but honest nodes at lines 7302–7306.
It cannot replace Ranex authentication, policy enforcement, sandboxing, or
hostile-worker controls.

Impact questions for the architecture owner:

- Does every write, tool, budget, mailbox, and external-effect sink enforce the
  current fencing epoch beyond the worker?
- Are canonical state and local outbox/journal records atomic under actual
  SQLite crash, journal, WAL, and durability settings?
- Are duplicate, out-of-order, lagging, and poison consumers specified?
- Can current state be reconstructed or proven consistent with the selective
  journal?
- How do immutable history, correction, retention, and actual erasure coexist?
- Which external effects are not naturally idempotent, and who reconciles them?

These questions are review obligations, not findings that a particular
implementation already fails.

### 5.8 `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E`

| Claim family | Exact local locator | Ranex disposition |
|---|---|---|
| Architecture = structure + characteristics + decisions + principles | Markdown lines 508–540 | Adopt; topology alone is incomplete |
| Fitness functions | 700–716 | Adopt per material characteristic with owner, subject, threshold/distribution, cadence, and failure response |
| Contextual tradeoffs / least-worst choice | 750–772 and 1575–1604 | Adopt; retain status quo, viable alternatives, consequences, and falsifiers |
| Component/quantum boundaries | 2608–2635 | Adapt; justify consistency and communication boundary rather than maximizing context count |
| Orchestration and bounded-context coupling | 4416–4508 | Adopt as a risk test for central authority and over-fragmentation |
| Contextual style selection and modular monolith | 4740–4872 | Adopt; choose from domain, characteristics, data, organization, and process |
| ADR context, alternatives, consequences, compliance | 5044–5128 and 5197–5211 | Adopt for every architecturally significant decision |

Do not import the book's generic star ratings as a universal or arithmetic
Ranex score. Use exact-subject quality attributes and fitness evidence.

Impact questions for the architecture owner:

- Is the central authority cell narrowly responsible for consistency, or has
  business and technical orchestration accumulated into a change-coupling hub?
- Does each proposed context boundary reduce coupling enough to justify
  transaction, event, failure, and cognitive overhead?
- Is synchronous interaction the local default, with asynchronous interaction
  chosen only for a named characteristic or failure-isolation need?
- Does every fixed architecture decision have an ADR-equivalent rationale,
  alternatives, consequences, and fitness/compliance test?

### 5.9 `ENGREF-CLEAN-ARCHITECTURE-1E`

The PDF has no Markdown derivative. Locators below are sequence pages in the
exact 364-page PDF, not claimed publisher print-page locators:

| Claim family | Exact PDF sequence locator | Ranex disposition |
|---|---|---|
| Use-case-visible architecture | Chapter 16, page 125; Chapter 21, pages 158–160 | Adopt so domain/product intent remains visible above delivery mechanisms |
| Preserve options and draw policy/detail boundaries | Chapter 16, page 127; Chapter 17, pages 133, 137, 140 | Adapt with a cost/quality justification for each boundary |
| Dependency rule and translated boundary data | Chapter 22, pages 161–162 | Adopt as an inward dependency constraint, subject to language/data/performance evidence |
| Process separation is not architecture by itself | Chapter 27, pages 185–191 | Adopt as a guardrail against cargo-cult services |
| Tests are components and require designed testability | Chapter 28, pages 192–193 | Adopt, but isolate any test-only bypass from production authority |
| Package by component and enforce encapsulation | Chapter 34, pages 230 and 235 | Adapt; a directory diagram without language-level dependency enforcement is insufficient |

Reject these overclaims:

- database, web, UI, or frameworks being “details” does not make their data,
  reliability, security, accessibility, performance, or operations irrelevant;
- the dependency rule does not prove one universal layer count or package tree;
- adding interfaces everywhere does not prove lower coupling;
- process or service boundaries do not inherently provide architecture,
  deployability, or independence; and
- a privileged testing API must never become a production authorization
  bypass.

## 6. Lifecycle and architecture use map

| Core stage | Added nine-family contribution |
|---|---|
| `GOVERN` | SWEBOK discipline coverage; Clean Coder responsibility; Fundamentals characteristics, ADRs, and fitness governance |
| `SHAPE` | Pragmatic responsibility; Clean Coder commitments; System Design clarification; Clean Architecture use-case visibility |
| `DISCOVER` | System Design scale questions; DDIA load/fault vocabulary; Pragmatic reversibility; Fundamentals characteristic discovery |
| `SPECIFY` | SWEBOK requirements; Pragmatic contracts; Clean Coder acceptance examples; DDIA reliability/performance scenarios |
| `DESIGN` | All nine families: discipline coverage, complexity, boundaries, dependency direction, data/failure semantics, topology tradeoffs, alternatives, and ADRs |
| `PLAN` | SWEBOK management/economics; Clean Coder estimate/commitment; Pragmatic reversible routes; Fundamentals tradeoffs |
| `BUILD` | Code Complete construction design; Clean Code and Clean Architecture boundaries; Pragmatic generation; DDIA exact state/effect semantics |
| `VERIFY` | Risk-layered falsification; architecture fitness functions; dependency/encapsulation tests; crash, replay, stale-worker, duplicate, and reconciliation tests |
| `RELEASE` | SWEBOK configuration/operations; Pragmatic reversibility; DDIA migration/encoding questions; immutable provenance and rollback evidence |
| `OPERATE` | DDIA reliability/lag/recovery; System Design monitoring prompts; SWEBOK operations; fitness distributions and response |
| `MAINTAIN_OR_RETIRE` | SWEBOK maintenance/configuration; Code Complete maintainability; Pragmatic reversibility; event/history retention and erasure |
| `IMPROVE` | SWEBOK process/measurement; Clean Coder learning; Fundamentals evolutionary fitness functions; evidence-bound experiments |

This is a source-attachment map. A task-specific profile still evaluates all
nine families as `APPLICABLE`, `NOT_APPLICABLE`, or `UNKNOWN`.

## 7. Conflict and cargo-cult controls

The combined corpus is intentionally not flattened into one doctrine.

| Tension | Required resolution |
|---|---|
| Full destination map versus tracer learning | Keep destination ownership and invariants explicit; use tracers for reversible evidence, not scope authority |
| Clean Architecture boundaries versus Fundamentals boundary-cost warnings | Require change/failure/coupling benefit and fitness evidence for each boundary; more boundaries are not automatically cleaner |
| Clean Architecture mechanism-as-detail language versus DDIA data semantics | Keep policy independent of vendor mechanisms while treating transactions, clocks, consistency, retention, and recovery as first-class constraints |
| DDIA asynchronous derivations versus Fundamentals synchronous local default | Use a local transaction when it meets the need; add async only for named isolation, durability, integration, or throughput characteristics |
| DRY versus bounded ownership | Generate from one semantic owner; do not create shared mutable domain ownership or a god database |
| Central consistency authority versus orchestration coupling | Retain the smallest necessary consistency cell and measure responsibility, fan-in/fan-out, and change coupling |
| Test API power versus production security | Isolate privileged test support to qualified test builds/harnesses and prove production absence or denial |
| Generic book scores/percentages versus evidence | Reject arithmetic aggregation and universal star, coverage, pyramid, velocity, or team-size rules |
| Incomplete DDIA copy versus mature technical claim | Confirm high-consequence claims against a lawful final edition or the cited primary literature |

A pattern name, quotation, nine-family citation count, or model consensus is
never proof of applicability or implementation.

## 8. Machine-readable practice-source dataset

The public-safe
[`engineering-reference-practice-registry.json`](../../research/engineering-reference-practice-registry.json)
contains:

- all nine stable source-family IDs;
- 34 stable practice IDs;
- exact local section/page/line locators;
- original Ranex syntheses, never long copied passages;
- lifecycle and architecture concerns;
- required behavior and acceptable verification methods; and
- limitations and rejected overclaims.

It is input to, not a replacement for, the future executable practice contract.
Its status is `SOURCE_RECONCILED_NOT_APPLIED`. A compiler must still create an
immutable, subject-specific applicability profile and a verifier must still
test actual behavior.

## 9. Release and legal disposition

Every one of the 17 full-text paths is classified in
[`legal/licensing-manifest.json`](../../../legal/licensing-manifest.json).
Safe public substitutes are:

- bibliographic citations and lawful publisher/catalog links;
- original, non-reconstructive Ranex summaries;
- stable practice IDs and claim-level locators;
- non-reconstructive digests; and
- original applicability, decision, verification, and outcome evidence.

The release gate must fail if a `LOCAL_ONLY` or
`PROHIBITED_PENDING_RIGHTS` path enters the Git index, archive, package,
mirror, prompt bundle, deployment input, or public artifact.

## 10. Validation and acceptance tests

The reconciliation is falsified if:

1. live discovery produces a book path absent from the 17-entry manifest;
2. `sha256sum -c` fails for any entry;
3. the index does not contain nine unique families, 17 unique paths, and
   86,856,268 representation bytes;
4. a representation is assigned to zero or multiple conceptual works;
5. a PDF/Markdown pair is counted as independent corroboration;
6. a saved path lacks a matching licensing entry and release blocker;
7. a practice ID lacks an exact locator, limitation, required behavior, or
   verification method;
8. the unfinished DDIA copy is described as the completed first edition;
9. a diagram, formula, table, or page claim relies on a lossy extraction
   without authoritative-copy verification;
10. a book heuristic overrides policy, law, security, privacy, recovery, owner
    authority, or runtime evidence;
11. a nine-family mapping is reported as implementation or conformance; or
12. a full-text artifact is publicly included without documented rights and
    privacy clearance.

## 11. Current standing

Corpus inventory, conceptual-work grouping, source reconciliation, stable
practice-source IDs, and legal path coverage are complete for the exact
17-artifact live snapshot.

Architecture-element applicability, implementation, runtime effectiveness,
standards-clause conformity, and permission to redistribute remain separate
and unproven.

> **Nine works / seventeen representations frozen and source-reconciled;
> public full-text inclusion blocked; task-level applicability and runtime
> conformance not claimed.**
