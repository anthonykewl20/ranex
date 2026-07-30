# RFC-0007: Validate Without the Local-Only Practice Corpus

| Field | Value |
|---|---|
| Status | DRAFT |
| Owner | Human owner |
| Authors | Assistant, from Codex and Grok diagnosis, at owner request 2026-07-30 |
| Created | 2026-07-30 |
| Review by | Owner decision; unblocks contract validation on any machine that does not hold the corpus |
| Affected contexts | `process_assurance`, `assurance`, `provenance_compliance`, `configuration_management` |
| Supersedes | Nothing. Corrects a validator contract that contradicted an accepted decision |
| Architecture subject digest | Not pinned; the RFC lifecycle axis is not yet enacted |
| Subject-manifest digest | Not pinned; same reason |
| Core SDLC trace ref/digest | `docs/architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md:137` |

## Decision question

Contract validation required all 18 full-text reference books to be present on
disk, or it failed. Those books are deliberately never distributed. Should
validation continue to require them, or report their absence explicitly?

## Context and evidence

### Facts

1. **Measured.** `validate_contracts.py` required set-equality between the paths
   listed in the committed practice-corpus index and every file discovered under
   `docs/research/books`, failing with `PRACTICE_CORPUS_INDEX_PATH_SET`
   otherwise. A second check compared each file's byte size and digest.
2. **Measured.** `.gitignore:18` excludes `docs/research/books/`. **0 of 18 files
   are tracked in git**, and none appears in any commit in the repository's
   history. The path returns 404 on the public remote.
3. **Measured.** `legal/licensing-manifest.json` classifies this material
   `LOCAL_ONLY` and `PROHIBITED_PENDING_RIGHTS` — 109 occurrences each.
4. **Accepted decision.** `ADR-0002:137` already directs: *"Keep full-text book
   artifacts local-only under `docs/research/books/`."*
5. **Measured.** The repository therefore could not validate on any machine that
   did not already hold the corpus. Every local run passed because the files were
   present; the defect was invisible to local validation by construction.
6. **Measured.** This was found by the architecture-contract CI gate on its first
   execution, run 30552710344.

### The contradiction

Facts 1 and 3–4 are individually correct and jointly impossible. Repository
policy forbids distributing the corpus; the validator required it. The result was
a governance harness that could only prove itself on one laptop.

### Diagnosis

Two independent models diagnosed this from the CI evidence, and their claims were
reproduced at `path:line` before being accepted. Both classified it the same way:
**a real defect the gate caught, not a workflow bug.** As one put it, *"the
repository does not validate from a clean checkout,"* and *"merely changing the
workflow's working directory or validation command would not fix this defect."*

A third reviewer failed mid-run with an upstream timeout and returned 647 bytes;
the runner recorded it `EXIT_1_FAILED` rather than reading a fragment as a result.

## Proposed design

### `CORPUS-LOCAL-001` — File-presence checks run only where the files exist

When `docs/research/books` is present, every existing check runs unchanged: path
set equality, byte size, and digest per artifact.

When it is absent, those two checks are skipped and the report records
`"practice_corpus_validation": "NOT_ASSESSED_LOCAL_ONLY"`.

### `CORPUS-PROVENANCE-001` — The provenance record is always verified

Absence of the files never skips the committed evidence. On every machine,
validation still verifies the corpus index against itself, the manifest rows and
their digest format, the index-to-manifest agreement, the artifact-count
denominator, and the byte totals. What is no longer required is the presence of
copyrighted material that policy forbids publishing.

The distinction is deliberate: **the provenance record travels; the source files
do not.** Which editions, at which digests, informed the engineering-practice map
remains machine-checked everywhere. If a book were swapped for a different
edition, the recorded digest would no longer match on the machine that holds it.

### `CORPUS-ABSENCE-001` — Absence is stated, never implied

`NOT_ASSESSED_LOCAL_ONLY` is written into the report as a distinct value. It is
never rendered as `PASS`, and never omitted. This follows the rule `ADR-0012`
already established for runtime evidence: absence must be explicit, cannot be
represented as a pass, and cannot be left out of the assessment.

## Accepted cost

**CI proves less than a local run, and that reduction is real.** File-presence
and digest-drift checking for the practice corpus can only ever happen on a
machine that holds the corpus. A book replaced on such a machine is caught there;
the same substitution is invisible to CI, which has no file to compare.

This is the price of not publishing copyrighted material. It is recorded here so
that no reader infers from a green CI run that the corpus files were verified.

## Predeclared acceptance tests

1. With the corpus present, validation returns `PASS` and
   `practice_corpus_validation: PASS`, with all 18 artifacts counted.
2. With the corpus absent, validation returns `PASS` and
   `practice_corpus_validation: NOT_ASSESSED_LOCAL_ONLY`.
3. With the corpus present but one file's bytes altered,
   `PRACTICE_CORPUS_ARTIFACT_DRIFT` still fires.
4. With the corpus present but an unindexed file added,
   `PRACTICE_CORPUS_INDEX_PATH_SET` still fires.
5. With the corpus absent, a corrupted committed index or manifest still fails —
   absence of the files does not weaken the checks on committed evidence.
6. No configuration key, flag, or environment variable can suppress the corpus
   checks on a machine where the corpus is present.

Tests 1 and 2 were executed before this RFC was written, by moving the corpus
aside and restoring it. Both behaved as specified.

## Human decision requested

> Accept that contract validation reports the practice corpus as
> `NOT_ASSESSED_LOCAL_ONLY` where the files are absent, rather than failing —
> keeping the provenance record machine-checked everywhere while the copyrighted
> source files remain undistributed, and accepting that CI can never verify those
> files' bytes?

The owner directed on 2026-07-30 that the books must not be uploaded, which
settles the alternative. Rejecting this RFC means either publishing the corpus,
which the licensing manifest prohibits, or leaving the repository unvalidatable
outside one machine.
