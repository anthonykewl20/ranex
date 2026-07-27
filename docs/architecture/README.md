# Ranex Architecture Documentation

This directory is the normative architecture base for rebuilding Hermes into
Ranex.

## Read in this order

1. [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md)  
   The core product-to-production process: governance, discovery,
   requirements, design, planning, implementation, verification, release,
   operation, improvement, risk lanes, decision rights, and measurable flow.
   Its executable stage contracts and stable controls are in the
   [SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md).
   The owner decision making this established SDLC primary and AI work
   subordinate is [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md).

2. [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)  
   The complete target map: product boundaries, bounded contexts, ownership,
   source tree, dependencies, state, effects, security, operations, migration,
   upstream sync, exclusions, and acceptance gates.

3. [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md)  
   Defines authority, evidence, machine contracts, conflicts, RFC/ADR changes,
   and how sliced delivery preserves the full map.

4. [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md)  
   Defines roles, packets, handoffs, independent review, verification, permits,
   landing, post-landing checks, and definition of done. It is the governed
   execution subprocess inside the core SDLC.

5. [DeepSeek V4 Pro and HY3 Full-Map Review](./reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md)  
   Records the model collaboration, evidence corpus, limitations, and material
   changes introduced through reconciliation.

6. [`templates/`](./templates/)  
   Initial document-level contracts for architecture reviews, tasks, handoffs,
   reviews, human decisions, RFCs, and ADRs.

## Scope rule

The architecture is a full-system specification, not an MVP or prototype map.
Implementation slices are routes through the architecture. They may leave mapped
capabilities inactive, but they may not leave their final owners and attachment
points undefined.

## Authority rule

The accepted Core SDLC governs how work moves from need to operated outcome.
The full-system architecture and ADRs govern what Ranex is and where authority
lives. Machine contracts are executable projections of both and cannot
semantically override either. AI agents are bounded workers; model output is
advisory. Runtime claims require runtime evidence.

## Research inputs

Every file under [`docs/research/`](../research/) is a required architecture
input. Research informs the architecture but does not silently override it.
The evidence basis for the core process is
[Real-world software-development operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md).
