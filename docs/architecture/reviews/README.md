# Review and audit records

Reviews are evidence, not authority. Raw prompts, model outputs, metadata, and
digest manifests live under [`artifacts/`](artifacts/) and are immutable.

## Current

| Record | ID | Standing |
|---|---|---|
| [Live foundational-reference corpus reconciliation](2026-07-28-live-foundational-reference-corpus-reconciliation.md) | `REVIEW-ENG-REF-002` v1.1.0 | **Current corpus baseline** (ten works / 18 files). Supersedes `REVIEW-ENG-REF-001` as live baseline |
| [SDLC-FORK-000 preflight](2026-07-28-sdlc-fork-000-preflight.md) | `REVIEW-SDLC-FORK-000-20260728` | **`BLOCKED` — currently blocking** every runtime implementation commit (cited in the architecture header) |
| [Claude runtime / Hermes / OpenCode reconciliation](2026-07-29-claude-runtime-hermes-opencode-reconciliation.md) | `REVIEW-RUNTIME-RECONCILIATION-2026-07-29` | Current advisory; runtime and performance `NOT_ASSESSED` |
| [Spec Kit selective-adaptation reconciliation](2026-07-30-spec-kit-selective-adaptation-reconciliation.md) | `REVIEW-SPEC-KIT-SELECTIVE-ADAPTATION-2026-07-30` | Current advisory; recommends a measured Ranex-native experiment, adopts no feature or authority |
| [Modular-DDD and TDD adversarial review](2026-07-28-modular-ddd-tdd-adversarial-review.md) | `RANEX-DDD-TDD-ADVERSARIAL-2026-07-28-001-FINAL` | PASS at architecture-design/contract scope only; no runtime claim |
| [Kimi agent-fleet research reconciliation](2026-07-27-kimi-agent-fleet-research-reconciliation.md) | `REVIEW-KIMI-FLEET-001` | Current disposition record for the 89-file Kimi addendum |
| [APOSD / agent-rules / skills reconciliation](2026-07-28-aposd-agent-rules-skills-reconciliation.md) | `REVIEW-APOSD-SKILLS-001` | Current advisory; bound experiment remains `DRAFT`, unexecuted |

## Superseded

| Record | ID | Superseded by |
|---|---|---|
| [Foundational reference corpus reconciliation](2026-07-27-foundational-reference-corpus-reconciliation.md) | `REVIEW-ENG-REF-001` v1.0.0 | [`REVIEW-ENG-REF-002`](2026-07-28-live-foundational-reference-corpus-reconciliation.md) as live baseline; remains an immutable historical snapshot of the six-work corpus |

## Historical evidence (true records of past subjects; not current authority)

| Record | ID | Why historical |
|---|---|---|
| [DeepSeek V4 Pro / HY3 full-map review](2026-07-27-deepseek-v4-pro-hy3-full-map-review.md) | `REVIEW-ARCH-RANEX-001` | Advisory; consolidates three rounds — earlier rounds retained under [`artifacts/2026-07-27/`](artifacts/2026-07-27/) as historical advisory evidence |
| [Hermes initial runtime acceptance](2026-07-28-hermes-initial-runtime-acceptance.md) | `HERMES-INITIAL-RUNTIME-ACCEPTANCE-2026-07-28` | `ACCEPTED_FOR_BOUNDED_LOCAL_USE` of an exact past subject; not authority for a live Hermes/Nous inference route after ADR-0011 |
| [Gate-controller MVP user-level audit](2026-07-28-gate-controller-mvp-user-level-audit.md) | `REV-GATE-MVP-USER-001` | Audit of an uncommitted worktree prototype; `PASS_WITH_BLOCKERS` as R&D tracer, `REJECT` as live authority |
| [Implementation worktree subject-binding audit](2026-07-28-implementation-worktree-subject-binding-audit.md) | `RANEX-WORKTREE-SUBJECT-BINDING-2026-07-28` | Point-in-time verdict against HEAD `4baad4a…`; re-audit before relying on it |

## Session execution records (no formal review ID)

Dated records of agent execution sessions. These are evidence of work done,
not authority, and carry no formal `REVIEW-*` ID. Listed for discoverability.

| Record | Subject |
|---|---|
| [ADR-0021 promotion record](2026-07-31-adr-0021-promotion-record.md) | Executed evidence for promoting ADR-0021 (limiting ADR-0010 to inherited lineage) to `ACCEPTED` |
| [CLI boundary fixes](2026-07-31-cli-boundary-fixes.md) | Fix of the two HIGH CLI boundary defects (subject-digest omission, repository confinement) found by the final-gate audit |
| [Final-gate adjudication](2026-07-31-final-gate-adjudication.md) | Adversarial gate of the walking-skeleton slice by execution; found the two HIGH defects the CLI-boundary record fixes |
| [LUNA ADR-0007 conformance](2026-07-31-luna-adr7-conformance.md) | ADR-0007 topology conformance audit; 12 of 18 `ORG-*` rules fail, no product code changed |
| [Schema-registry drift](2026-07-31-schema-registry-drift.md) | Investigation of the 153-vs-157 schema-registry inventory gap (four deliberate historical v1 exclusions) |

## `artifacts/` layout

- `2026-07-27/` — full-map review rounds: prompts, raw HY3/DeepSeek outputs with
  provider metadata, review bundle, and eight `.sha256` source/bundle manifests
  that freeze exact bytes of architecture, research, and legal files.
- `2026-07-28/aposd-agent-rules-skills/` — APOSD addendum subject, packet,
  `DRAFT` experiment, and manifest.
- `2026-07-30/spec-kit-selective-adaptation/` — pinned Ranex/Spec Kit source
  manifest, common prompt, raw independent HY3/DeepSeek reviews, provider
  metadata, and artifact digest manifest.
- `enterprise-build-readiness/` — SDLC-FORK-000 evidence and worktree bindings.
- `foundational-reference-corpus/` — the current live-corpus manifest and index.

**Never edit or move anything under `artifacts/`.** The manifests are the
integrity anchor for documents across the whole repository.
