# Implementation Worktree Subject-Binding Audit

| Field | Value |
|---|---|
| Audit ID | `RANEX-WORKTREE-SUBJECT-BINDING-2026-07-28` |
| Capture time | `2026-07-28T09:35:48Z` |
| Method | Read-only Git identity, porcelain-status, and exact-byte comparison |
| Live reference | `/home/soultransit/devtony/ranex` |
| Reference HEAD | `4baad4a67843b02d5970f442fb54aed8d6525dda` |
| Candidate subject | `sha256:cf45b83a0e849ea0272b821c58a63432fdc093b301ca32be8c69dbea5d7528cc` |
| Machine evidence | [worktree-subject-bindings.json](./artifacts/enterprise-build-readiness/worktree-subject-bindings.json) |
| Mutations | None to an existing document, branch, worktree, or implementation file; this report and its JSON evidence are new |

## Verdict

**No current linked worktree is safe to use as a Ranex construction base.**

ADR-0003 accepts the paper destination, not the current exact bytes. No
owner-accepted `ArchitectureSubject` instance or owner decision bound to the
candidate digest was found. None of the four implementation/phase worktrees
carries a machine-readable subject binding, and none matches the live root
candidate. The live root matches itself but is not a construction release:
all 127 selected subject paths are modified or untracked relative to its HEAD.

This is a deterministic subject-control blocker, not a recommendation to
discard local work. Every dirty path remains user-or-collaborator work unless
and until its provenance and disposition are explicitly decided.

## Exact result

`M`, `X`, and `D` below count selected candidate files that match, are missing,
or differ using working-tree bytes. Dirty counts use
`git status --porcelain=v1 --untracked-files=all` and exclude the two outputs of
this audit to avoid self-reference.

| Worktree / role | Branch | HEAD | Dirty entries | M / X / D | Subject-local change | Safe to build |
|---|---|---|---:|---:|---|---|
| Live root / architecture consolidation | `bootstrap/pre-upstream` | `4baad4a67843b02d5970f442fb54aed8d6525dda` | 226 | 127 / 0 / 0 | All 127 selected paths are dirty against HEAD | **No** |
| Gate-controller implementation | `feature/deterministic-gate-controller-mvp` | `0533e1eaf50ace0eb84435a5c3de05e939fd4daa` | 44 | 0 / 90 / 37 | Local `SOURCE_OF_TRUTH.md` edit | **No** |
| Phase-0 preflight/evidence | `phase/0-preflight` | `fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4` | 168 | 0 / 126 / 1 | None among selected paths | **No** |
| Upstream-adoption implementation | `phase/1-adopt-upstream` | `9be6bd9443e447b205ad265d44238436910dfbce` | 3 | 0 / 90 / 37 | Local `SOURCE_OF_TRUTH.md` edit | **No** |
| Runtime-bootstrap implementation | `develop` | `0533e1eaf50ace0eb84435a5c3de05e939fd4daa` | 26 | 0 / 90 / 37 | Local `SOURCE_OF_TRUTH.md` edit | **No** |

The gate-controller worktree also has three worktree-only candidate
architecture paths:

- `docs/architecture/DETERMINISTIC_GATE_CONTROLLER_MVP.md`
- `schemas/assurance/evidence-record.schema.json`
- `schemas/governed-execution/transition-request.schema.json`

They are not silently added to the live subject. They require explicit
reconciliation against the accepted architecture and current schema registry.

All five worktrees show the working-tree deletion of the retired
`RANEX_IMPLEMENTATION_GUIDE.md`. That deletion is outside this subject digest
and is consistent with ADR-0002; reconciliation must not restore the guide.

## What the candidate digest binds

The 127-file point-in-time candidate contains:

| Subject class | Files |
|---|---:|
| Normative architecture prose | 9 |
| Accepted architecture decisions | 6 |
| Machine contract registry | 17 |
| Executable schema projection and negative fixtures | 53 |
| Provisional contract templates | 38 |
| Engineering-reference registry and live corpus bindings | 3 |
| Licensing constraint | 1 |

The digest is SHA-256 over sorted manifest lines of the form
`<file-sha256><two spaces><repository-relative-path><LF>`. The JSON evidence
contains every path, byte count, digest, live-root Git state, exact missing and
differing path sets, worktree status hashes, and comparison digest.

Reviews and capability assessments are evidence, not normative construction
authority, so they are excluded except for the two exact live-corpus binding
files referenced by the book-practice registry. Full book texts, implementation
source, generator tooling, phase/run evidence, and this audit are also excluded.
This avoids a circular subject and does not waive their separate gates.

## Deterministic blocking rule

`BUILD-SUBJECT-BINDING-001` is:

> Allow construction only if an immutable owner-accepted architecture subject
> `A` exists, the implementation task/worktree carries a machine-readable
> binding `W`, `W.subject_digest == A.subject_digest`, every file in `A` is
> present with the accepted hash, no material `UNKNOWN` or `CONFLICT` remains,
> and the exact task packet authorizes the construction scope. Otherwise block.

Dirty implementation files are not automatically prohibited: they are the
normal result of authorized work. A dirty, missing, or nonmatching architecture
subject is prohibited unless an exact architecture-change task carries it
through review and owner acceptance.

Current evaluation: `BLOCK_ALL_LINKED_WORKTREES`.

## Drift and preservation

- A local porcelain entry proves a worktree change, not its human, agent, or
  generator author.
- A differing path with no local status entry is classified only as a
  nonmatching committed branch copy relative to the live candidate.
- Phase 0 has 163 paths under its run-evidence convention. “Generated or run
  evidence” is a path classification, not an authorship claim.
- Root contracts and schemas that are untracked are candidate projections.
  Generated provenance is not asserted without generator evidence.
- The local `SOURCE_OF_TRUTH.md` changes in three worktrees and all other dirty
  implementation/evidence paths must be preserved during reconciliation.

The next construction precondition is therefore not copying root files into the
worktrees. It is freezing the intended root bytes, resolving semantic and gate
findings, producing the immutable accepted `ArchitectureSubject` and manifest,
then rebasing or transplanting each preserved implementation change onto a
worktree whose exact binding and hashes match that accepted subject.

## Limits

This audit establishes Git identity, byte drift, binding absence, and the
resulting construction block. It does not claim semantic correctness,
book-practice effectiveness, schema validity, security, test passage,
fork-preflight passage, `AI-G2`, `MAP-*`, or runtime qualification.
