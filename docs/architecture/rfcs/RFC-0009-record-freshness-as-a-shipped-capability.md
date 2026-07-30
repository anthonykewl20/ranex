# RFC-0009: Record Freshness as a Shipped Ranex Capability

| Field | Value |
|---|---|
| Status | DRAFT |
| Owner | Human owner |
| Authors | Assistant, at owner direction 2026-07-31 |
| Created | 2026-07-31 |
| Review by | Owner decision; specifies a product capability, authorizes no product code |
| Affected contexts | `assurance`, `process_assurance`, `module_governance`, `work_management` |
| Supersedes | Nothing. Specifies a capability Ranex ships, distinct from the self-check already in this repository |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/SOURCE_OF_TRUTH.md` canonical status vocabulary |

## Decision question

Ranex makes unreliable agents produce reliable software by compiling architecture
documents into checking code. It already refuses to let *generated* output drift
from its sources. It has no equivalent protection for *prose records*.

An agent can therefore complete work, pass every gate, and leave the documents
that describe the system asserting an older state. Nothing detects it, because
nothing generated those documents.

Should Ranex ship a capability that refuses to let a governed project's records
go stale after work is done, and if so, on what terms?

## Evidence that the defect is real and silent

**FACT**, measured in this repository on 2026-07-31, before any such gate existed:

| stale claim | reality |
|---|---|
| `HANDOFF.md` stated **16** accepted ADRs | **19** existed on disk |
| `README.md` stated the range ended at **ADR-0014** | **ADR-0019** existed |
| `README.md` named RFCs up to **RFC-0002** | **RFC-0008** existed |
| Five RFCs carried `Status: DRAFT` | each was already promoted into an accepted ADR |

Eight false claims, in the corpus of a project whose entire purpose is that
claims must be checkable. Every one passed contract validation, because contract
validation never looked. This is the strongest available argument that the
capability is needed: the governance harness could not detect the defect in its
own governance documents.

A self-check closing these eight in this repository already exists
(`scripts/architecture/check_record_freshness.py`, wired into CI). It is
deliberately **not** the subject of this RFC: it is hardcoded to this
repository's paths and record types, and a capability customers run cannot be.

## What makes this hard, and why it is not an AI problem

The tempting implementation is to have a model read the documents and judge
whether they are current. That is rejected outright. A model's judgement is not
reproducible, cannot be pinned, and would place the governed agent in charge of
deciding whether it had updated its own records — the exact self-assertion
`ADR-0013:1175-1176` forbids and that `ADR-0017` was written to close.

The capability must be **mechanical**: every check compares a written claim to an
observable fact, and disagreement is a finding. This is only possible if claims
are *declared* rather than *inferred from prose*, which is the first open
question below.

## Open questions this RFC must settle

### 1. What counts as "work done" that obliges a record update?

Candidates, each with a different failure mode:

| trigger | catches | misses / cost |
|---|---|---|
| Any commit | everything | fires on typo fixes; trains people to ignore it |
| A landed change through the governed lifecycle | real work | needs the lifecycle enacted; not available pre-`IMPLEMENTATION_START` |
| A change to a declared *authority* artifact | decisions, schemas, catalogs | misses work that should have produced a record and did not |

**Recommendation:** the third, narrowed — an obligation arises when a declared
authority artifact changes. It is mechanical today, needs no runtime, and its
blind spot (work that produced no record at all) is a separate control, not this
one.

### 2. Which records are in scope?

**Recommendation:** only records the project explicitly declares. Ranex must not
guess which files are governed; a project that declares nothing gets no checks
and is told so, rather than being silently unprotected.

### 3. How does a project declare its records so the check stays mechanical?

This repository already answers this and the answer generalises:
`SOURCE_OF_TRUTH.md` carries a single canonical row listing every accepted
decision, and `generate_contracts.py:5563` parses it as a **closed set** —
filesystem and declaration must agree exactly or generation fails.

**Recommendation:** generalise that pattern. A governed project declares a record
manifest naming each governed document, its record type, and the claims it makes
that must remain true (a count, a range, a status derived from another record).
Ranex checks declared claims against observed facts. Anything not declared is not
checked, and the manifest itself is a governed record.

### 4. Does staleness block, or record a finding?

The strongest argument for blocking is the evidence above: findings that do not
block are what allowed eight false claims to persist. The strongest argument
against is that a documentation error would stop delivery.

**Recommendation:** blocking, but staged as `ADR-0012` already stages readiness —
staleness blocks at the readiness gate, not at every commit. A stale record
cannot reach a declared-ready state; it does not stop work in progress. This
preserves the fail-closed guarantee without making a typo a build break.

## Proposed provisions

### `RECORD-FRESH-001` — declared records, closed set

A governed project declares its records in a manifest. The declaration is a
closed set: a declared record that does not exist, and a record claiming
governance that is not declared, are both findings.

### `RECORD-FRESH-002` — claims are declared, never inferred from prose

A record declares the claims it makes that must remain true. Ranex checks
declared claims only. No model reads prose to decide whether a document is
current, and no check is added by convention.

### `RECORD-FRESH-003` — every check is mechanical and reproducible

Each check compares a declared claim to an observable fact and yields the same
verdict on identical inputs. No model is invoked. A check that cannot be
expressed this way is not admitted.

### `RECORD-FRESH-004` — staleness blocks at the readiness gate

A stale declared claim blocks a project from reaching a declared-ready state. It
does not block work in progress. The finding names the record, the claim, and the
observed fact.

### `RECORD-FRESH-005` — the obligation cannot be discharged by the party it constrains

An agent may not mark its own records fresh. Freshness is computed from observed
facts, never asserted. This mirrors `ADR-0017` `OWNER-RESOLVE-003`.

## Predeclared acceptance tests

1. A project declaring no records is reported as unprotected, not as passing.
2. A declared record absent from disk is a finding.
3. A governed record absent from the manifest is a finding.
4. A declared count that disagrees with the observed count is a finding naming
   both values.
5. A record whose status is derived from another record (a proposal promoted into
   a decision) is a finding while the two disagree.
6. Two runs over identical inputs produce identical findings.
7. No check invokes a model; removing model access changes no verdict.
8. An agent editing a record cannot clear a finding without changing the observed
   fact.
9. Findings block a readiness declaration and do not block ordinary work.

## Consequences and evidence standing

- This RFC **authorizes no product code**. `IMPLEMENTATION_START_READY` is not
  declared, and product code remains limited to an R&D tracer claiming no
  authority.
- The existing self-check is not this capability and is not promoted by this RFC.
  It remains a repository-specific control.
- Adopting a declared-manifest approach adds one governed artifact per project.
- The blind spot in question 1 — work that should have produced a record and
  produced none — is explicitly out of scope and needs its own control.
- `IMPLEMENTATION_START_READY` and `PRODUCTION_READY` remain `NOT_ASSESSED`.

## Human approval

The human owner directed that record freshness be specified as a capability
Ranex ships to governed projects, distinct from the self-check already protecting
this repository, and that the work be framed as the product's behaviour rather
than the assistant's workflow.
