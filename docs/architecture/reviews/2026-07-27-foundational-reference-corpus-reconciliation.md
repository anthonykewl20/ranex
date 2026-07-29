# Foundational Software-Engineering Reference Corpus Reconciliation

| Field | Value |
|---|---|
| Review ID | `REVIEW-ENG-REF-001` |
| Version | `1.0.0` |
| Status | Complete read-only corpus audit and architecture reconciliation; public redistribution blocked |
| Date | 2026-07-27 |
| Owner | Human governor |
| Exact corpus | Six saved works represented by six PDFs and six Markdown derivatives |
| Corpus count/size | 12 files / 47,732,875 bytes |
| Manifest | [Foundational-reference corpus manifest](./artifacts/2026-07-27/foundational-reference-corpus-manifest.sha256) |
| Manifest SHA-256 | `e9bb449238bd0c8c326588cb7e6df2d82beb3796c09ced2d5b5b1da409326472` |
| Resulting map | [Ranex Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md) |
| Decision authority | Human owner inside applicable law/contract/license; this review is advisory evidence |
| Provenance class | `CURATED_RESEARCH`, `NOASSERTION` |
| Repository inclusion | `LOCAL_ONLY`; `PROHIBITED_PENDING_RIGHTS` |
| Release standing | Blocking for any public commit/package containing the full PDFs or full/near-full derivatives |

## 1. Verdict

The saved works are major Ranex engineering references. Together they close
important practice detail around lifecycle coverage, design, file structure,
construction, testing, professional commitments, operations, and improvement.
They do not replace the owner-accepted SDLC or create AI authority.

The corpus is not safe to publish as part of a public repository on the
evidence currently available. Multiple works carry restrictive or
all-rights-reserved notices, the acquisition/right-to-use chain is absent, and
one ebook is visibly personalized to a named third party. Full-text Markdown
conversion creates an additional derivative/reproduction concern.

The reconciled decision is:

> **Use the works locally as major practice references; publish original Ranex
> synthesis and lawful citations, not the full corpus, unless documented
> redistribution and privacy clearance are obtained.**

## 2. Method

Every file in the 12-entry manifest was inspected. The audit:

1. inventoried and hashed every PDF and Markdown file;
2. checked PDF container/page/metadata and visible rights/provenance signals;
3. read the Markdown structure, contents, relevant chapters, limitations, and
   rights notices;
4. compared each PDF/Markdown pair for derivation signals and extraction loss;
5. separated one intellectual work from its two stored representations;
6. mapped usable practices to the human Core SDLC and full architecture;
7. recorded overbroad, dated, corrupted, or context-incompatible advice;
8. checked current official lifecycle-standard status; and
9. classified public-repository and release risk.

The audit does not establish lawful acquisition, ownership, permission,
authenticity of the original distribution, completeness of extraction, or
standards conformity.

## 3. Exact artifact inventory

| Work/representation | SHA-256 | Observed scope and limitation |
|---|---|---|
| Clean Code PDF | `034292d5e0a2e27bc3444ff41216139537b4e0729661c79ee0a8ad3298db3857` | Full-book structure; restrictive Pearson rights notice; acquisition source absent |
| Clean Code Markdown | `f44a1ba7b8da08642c7ee4a557ba4e9aea7b9befedac4686c2d141d4a916377c` | 9,185 lines / 125,536 words; picture-text substitutions and no retained code-fence/image fidelity |
| Code Complete PDF | `018235406bd1a515e361b579382cce72fa0e773f1796dbf316d91947a0e3d252` | 120-page excerpt containing front matter, full Chapter 5, bibliography/index material—not the complete book |
| Code Complete Markdown | `081150569d686a3f38ec471e86cf61151ebc33eeaa19937c38d5940a0e6e28aa` | 3,274 lines / 54,769 words; broad table of contents/index must not be mistaken for retained chapter content |
| System Design Interview PDF | `d2bafdef03246a64e3c58049c5ae188d8be9d74c6b23f05045637b07ad7167df` | 269-page Second Edition ebook; explicit restrictive rights; Calibre-produced container |
| System Design Interview Markdown | `340ed9c4e03d88ea89f949cb1d038f15cea855a7e3004718992c588d5372f972` | 4,916 lines / 46,652 words; all 207 referenced figures absent, so diagrams and some claims cannot be reconstructed |
| The Clean Coder PDF | `73f64ac2e6f2bb18f0cbc2879b636c031ee3fe98eba0cc0a04ce8203d7aec90b` | 248-page ebook; Pearson restriction; ebook-origin metadata; no acquisition record |
| The Clean Coder Markdown | `b37771c0dc990b225bcbc5f0de1b5dbd6c496240e9fa47bacfce12bc7bf2f899` | 4,797 lines / 68,600 words; images absent and some estimation formulas materially corrupted |
| SWEBOK V4.0a PDF | `b3cb8028fecb9607f757504c861947fa3bf423087ea8bf08c58020f0ba3596dc` | IEEE Computer Society guide released September 2025; rights do not imply blanket public redistribution |
| SWEBOK V4.0a Markdown | `26a2eb8585c93cf77a60bed26e15695892941c14e38a2587054034904e291ce7` | 15,441 lines / 178,184 words; useful searchable projection, not authoritative layout or a complete lifecycle |
| The Pragmatic Programmer PDF | `7c8ad03780b2905e0cd47e3f5c60bd0474a718e7e7133ca226ef05828011ef20` | Original first-edition text / local 25th printing; 352-page personalized ebook marked “Prepared exclusively for Zach” |
| The Pragmatic Programmer Markdown | `fcd45290aa0d53e6468d5110caed549dbfcac1b8d3ad3183737447bbd05f0768` | 10,055 lines / 103,747 words; the third-party personalization is repeated throughout the derivative |

The PDF and Markdown in each row pair are one source lineage. The corpus
contains six major works, not twelve independent corroborating sources.

## 4. Provenance and derivation

The files do not record a sufficient acquisition/conversion chain:

- no acquisition URL, purchase/loan record, uploader identity, or permission
  grant;
- no conversion command, tool/version, model, prompt, run ID, or conversion
  log;
- no retained page-to-Markdown mapping;
- no generated-artifact declaration connecting each derivative to its PDF;
- no human proofreading/validation record; and
- no privacy review before repository placement.

Arrival timing and near-full textual correspondence strongly indicate that
each Markdown file derives from its paired PDF, but that inference is not a
documented provenance record. The manifest preserves observed bytes, not
authorship or rights.

## 5. Extraction-quality limitations

The Markdown files are navigation and local-analysis aids, not faithful
publication substitutes:

- figures and diagrams are absent or reduced to extracted picture text;
- code layout/fencing is unreliable;
- headers, footers, page numbers, tables, and reading order contain conversion
  noise;
- formulas may be corrupted, especially in The Clean Coder's estimation
  material;
- the System Design Interview extraction loses all referenced figures;
- broad contents/index text in the Code Complete excerpt can imply chapters
  that are not actually retained;
- watermarks and other page furniture are repeated as body content; and
- line numbers are stable only for the exact manifested bytes.

Quantitative/formula/diagram claims must be checked against a lawful,
authoritative copy before they become decision evidence.

## 6. Rights and privacy findings

`NOASSERTION` means rights are unresolved. It is not permission.

| Work | Observed rights/privacy signal | Repository disposition |
|---|---|---|
| Clean Code | Pearson copyright and permission-required language | Local-only; public distribution blocked |
| Code Complete excerpt | Microsoft Press copyright and no-reproduction language | Local-only; public distribution blocked |
| System Design Interview | Copyright/all-rights/no-reproduction language | Local-only; public distribution blocked |
| The Clean Coder | Pearson copyright/permission language and ebook-origin metadata | Local-only; public distribution blocked |
| SWEBOK | IEEE copyright; download/use conditions do not provide blanket collective-work redistribution | Local-only pending documented rights |
| The Pragmatic Programmer | Restrictive notice plus named third-party personalization across the ebook | Local-only; public distribution and privacy review blocked |

Safe public evidence is an original Ranex summary, bibliographic reference,
lawful source link, claim-level paraphrase, and non-reconstructive digest. A
human decision, ADR, model output, or manifest entry cannot create missing
rights.

## 7. Per-reference architecture disposition

### 7.1 SWEBOK V4.0a

Adopt as the consensus knowledge-area map and broad discipline-coverage check.
It strengthens requirements, architecture, design, construction, testing,
operations, maintenance, configuration, management, process, quality,
security, economics, and foundations.

Do not call it a complete prescriptive lifecycle. Its citations are
non-comprehensive and its knowledge areas do not directly cover every lifecycle
process.

SWEBOK V4.0a maps to ISO/IEC/IEEE 12207:2017 because that was current before
its September 2025 release. The current lifecycle standard is
[ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html). The old
crosswalk is historical until a versioned 2026 mapping is verified.

### 7.2 Code Complete, retained Chapter 5

Adopt the retained chapter's treatment of:

- design as explicit work connecting requirements and construction;
- design as iterative, heuristic, trade-off-bearing, and capable of revealing
  new facts;
- essential versus accidental complexity;
- decomposition, information hiding, interfaces/contracts, coupling/cohesion,
  testability, binding time, and maintainability;
- multiple design levels from system through routines/data; and
- proportionate design artifacts, alternatives, collaboration, and review.

Do not claim the absent chapters as reviewed evidence. “Emergent” design means
controlled learning inside the full map; it does not authorize architecture by
accident.

### 7.3 Clean Code

Adopt:

- explicit boundaries around third-party and volatile APIs;
- construction/runtime separation;
- testability, clear intent, low coupling, cohesive responsibility, and
  incremental verified refactoring;
- tests as executable examples and regression evidence; and
- concurrency as a separate source of failure requiring deliberate design.

Reject as universal:

- “only code is truth” when it would erase requirements, decisions, contracts,
  authority, configuration, or evidence;
- language-specific class/function-size dogma;
- TDD or coverage as sufficient assurance; and
- local object heuristics as a replacement for distributed fencing,
  idempotency, recovery, security, or lifecycle controls.

### 7.4 The Pragmatic Programmer, original first edition

Adopt responsibility, DRY as single authoritative knowledge, orthogonality,
reversibility, design by contract, plain-text/source-control discipline,
debugging, automation, production-shaped tracer routes, testing, and
escaped-defect regression learning.

Guardrails:

- DRY cannot create shared ownership or a common database across contexts;
- a tracer is a route through the full architecture, never an MVP/prototype map;
- automation cannot self-approve;
- disposable experiments remain quarantined; and
- dated tooling advice does not override current security/provenance controls.

### 7.5 System Design Interview, Second Edition

Adopt the design-conversation method:

1. clarify problem, actors, requirements, quality attributes, scale, and scope;
2. draw the complete high-level decomposition and obtain accountable review;
3. deep-dive the highest-risk state/data/effect/failure seams; and
4. reconcile trade-offs, bottlenecks, monitoring, recovery, and remaining
   unknowns.

Use its patterns as prompts, not defaults. Ranex is not a web-scale
microservice product. Cache, queue, replication, sharding, rate-limit, or
multi-region patterns require measured need, current primary references,
security, RPO/RTO, consistency/fencing, failure/recovery, and an accepted ADR.

### 7.6 The Clean Coder

Adopt:

- personal and organizational responsibility;
- explicit commitments only for controlled actions;
- early, transparent risk/lateness disclosure;
- estimates as uncertainty distinct from commitments;
- executable acceptance criteria co-developed across accountable roles;
- layered unit/component/integration/system/exploratory testing;
- continuous integration and regression discipline;
- asking for/offering help, sustainable work, learning, mentoring, and stable
  cross-functional teams; and
- an evidence-defined organizational Definition of Done.

Reject as universal gates:

- fixed work/learning hours, overtime rules, coverage percentages, team
  size/ratios, pyramid percentages, velocity/PERT mechanics, or hierarchy;
- TDD as the sole marker of professionalism;
- “QA should find nothing” as a cultural or process objective;
- independent findings treated as shame;
- architects owning all integration evidence;
- parallel personal/open-source repositories that violate enterprise
  security, retention, or provenance; and
- 2011 tools/branching/security coverage as adequate for Ranex.

## 8. Resulting Ranex changes

The audit resulted in:

- [Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md);
- explicit reference hierarchy in the Core SDLC, architecture, README, and
  ADR-0001;
- a scope → complete high-level map → risk deep dive → evidence/decision
  architecture workflow;
- context/authority-first file-structure and inward-dependency rules;
- tracer-route language that cannot be confused with an MVP/prototype map;
- layered risk-based testing without percentage monoculture;
- estimate/commitment/accountability rules;
- current ISO/IEC/IEEE 12207:2026 correction and SWEBOK crosswalk warning; and
- public-repository rights blocking in the licensing manifest.

## 9. Highest-value falsification tests

1. Every manifested byte still verifies.
2. A later book addition cannot inherit this audit without a new manifest.
3. A PDF/Markdown pair is never counted as two independent sources.
4. A cited chapter/figure/formula exists in the retained representation and is
   not conversion-corrupted.
5. Code Complete claims never imply the absent full book was reviewed.
6. A System Design web-scale pattern cannot enter Ranex without measured need
   and current primary evidence.
7. A book heuristic cannot override authority, security, privacy, recovery, or
   an accepted Core-SDLC control.
8. A tracer cannot be used to shrink the full target map.
9. No model can transform the books into lifecycle or decision authority.
10. The public build/release gate fails if any local-only full-text artifact is
    included without documented rights and privacy clearance.

## 10. Current standing

The exact six-work corpus has been inventoried, read, reconciled, and mapped.
Its engineering use is accepted under the Core SDLC hierarchy. Its public
redistribution is not.

> **Major reference use accepted; exact bytes frozen; public inclusion blocked
> pending rights; runtime practice and standards-clause conformance unproven.**
