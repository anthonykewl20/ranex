# Research inputs

Research informs the architecture but never overrides it
(`../architecture/README.md`, "Research inputs"). Files registered below as
immutable evidence are frozen in content-addressed manifests; **renaming or
moving one of those files breaks digest evidence.** A new draft remains
non-authoritative until it is explicitly reviewed, digest-bound, and promoted
through the architecture process. Files dated 2026-07-27 that cite the retired
`RANEX_IMPLEMENTATION_GUIDE.md` are historical under
[ADR-0002](../architecture/decisions/ADR-0002-retire-legacy-implementation-guide.md).

## Active proposals (not yet architecture decisions)

| File | ID / status | Standing |
|---|---|---|
| [deterministic-run-graph-visualization-research-2026-07-30.md](deterministic-run-graph-visualization-research-2026-07-30.md) | `RES-EXEC-GRAPH-001` v0.2.0 — reviewed draft research proposal | DeepSeek V4 Pro and HY3 both returned `FIT_WITH_CHANGES`; recommends a read-only deterministic run graph and requires an accepted RFC/ADR before any dependency or product implementation |

## Current inputs (accepted decisions or tooling depend on these)

| File | ID / status | Depended on by |
|---|---|---|
| [real-world-sdlc-operating-model-research-2026-07-27.md](real-world-sdlc-operating-model-research-2026-07-27.md) | `RES-SDLC-001` — adopted evidence basis, not normative | [Core SDLC Operating Model](../architecture/CORE_SDLC_OPERATING_MODEL.md) ("Research basis" header row); context for ADR-0001 |
| [ranex-architecture-practice-application-profile.json](ranex-architecture-practice-application-profile.json) | `ENGPROFILE-RANEX-ARCHITECTURE-DESIGN-001` v1.7.0 — design application defined, runtime `NOT_ASSESSED` | SHA-256-pinned inside `scripts/architecture/validate_contracts.py`; cited by `../architecture/README.md` ("Engineering-practice rule"). Do not edit without updating the validator constant |
| [engineering-reference-practice-registry.json](engineering-reference-practice-registry.json) | `ENGREF-PRACTICE-SOURCES-001` v1.1.0 — `SOURCE_RECONCILED_NOT_APPLIED` | Read by `scripts/architecture/generate_contracts.py`; digest-bound inside the profile above |
| [aposd-agent-rules-codebase-design-assessment-2026-07-28.md](aposd-agent-rules-codebase-design-assessment-2026-07-28.md) | `RESEARCH-APOSD-SKILLS-001` v1.2.0 — `RESEARCH_ONLY` | Advisory only; reconciled in [the APOSD review](../architecture/reviews/2026-07-28-aposd-agent-rules-skills-reconciliation.md); registered APOSD as the tenth source family |
| [hermes-core-architecture-research-2026-07-27.md](hermes-core-architecture-research-2026-07-27.md) | Historical study, **and now a promotion source** | [ADR-0013](../architecture/decisions/) promotes 65 provisions from it with per-row line citations and excerpt digests. Editing any promoted line breaks those bindings. The unpromoted material remains advisory — see the ADR for exactly which line ranges were deliberately left in research |

## Historical studies (immutable evidence; no accepted decision depends on their recommendations)

| File | Status | Note |
|---|---|---|
| [gemini-research.md](gemini-research.md) | UNKNOWN (no ID, date, or status header in file) | Added 2026-07-27; frozen in four `.sha256` manifests and `legal/licensing-manifest.json` — must not be renamed |
| [cookbook-alignment-research-2026-07-27.md](cookbook-alignment-research-2026-07-27.md) | Historical | Names the retired implementation guide as primary authority |
| [ocask-alignment-research-2026-07-27.md](ocask-alignment-research-2026-07-27.md) | Historical | Same retired-guide framing |
| [hermes-core-architecture-research-2026-07-27.md](hermes-core-architecture-research-2026-07-27.md) | **Moved to Current inputs above** — ADR-0013 promotes from it | Paired with the HY3 review below |
| [hermes-core-architecture-hy3-review-2026-07-27.md](hermes-core-architecture-hy3-review-2026-07-27.md) | Historical advisory review; no transition authority | Cross-family review of the file above |
| [ranex-sdlc-full-spec.svg](ranex-sdlc-full-spec.svg), [ranex-sdlc-visual-guide.html](ranex-sdlc-visual-guide.html) | Historical visuals | Whether they still match `POL-SDLC-001` v1.5.0 is UNKNOWN; reviewed by the file below |
| [ranex-sdlc-visual-hy3-review-2026-07-27.md](ranex-sdlc-visual-hy3-review-2026-07-27.md) | `REV-SDLC-VISUAL-HY3-001` — advisory | Review of the two visuals |

## Local-only (git-ignored; not in the repository you cloned)

- `books/` — full-text reference works; represented publicly by the
  [live-corpus manifest](../architecture/reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256).
- `kimi-research/` — raw Kimi corpus; represented publicly by the
  [Kimi manifest](../architecture/reviews/artifacts/2026-07-27/kimi-research-manifest.sha256).
