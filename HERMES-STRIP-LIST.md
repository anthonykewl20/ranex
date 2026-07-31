# Hermes strip list

Extracted 2026-07-31 from `architecture/contracts/hermes-research-promotions.json` (catalog `1.4.0`, 98 entries) before the clean-slate reset.

Plain checklist. No generator, no ADR, no authority — these are notes on what Hermes does and what a fork has to decide about each one. Full originals in `legacy/`.

---

## 1. De-commercialization — remove from the fork (18 rows)

Everything here is monetization/commercial surface. Delete it.

- [ ] `HERMES-PROMOTION-011` **BLOCK** — Remove the Nous commercial model provider and all account, credit, subscription, payment, entitlement, Portal, and promotional infrastructure; retain only provider-neutral cost and budget measurement.
- [ ] `HERMES-PROMOTION-037` **BLOCK** — Any legacy migration reader must be standalone and time-bounded, may recognize old Nous provider/account fields only to warn, redact, or translate a user to an explicit BYOK provider, must not be imported by normal startup, and cannot refresh a token or contact a Portal.
- [ ] `HERMES-PROMOTION-038` **BLOCK** — Legacy `$HERMES_HOME/auth.json` entries (`providers.nous`, `credential_pool.nous`, `active_provider="nous"`), shared `nous_auth.json`, and model/recommendation caches remain quarantined metadata. The reader reports “unsupported legacy provider,” offers explicit secret deletion, requires a new provider selection, and never silently moves an OAuth token into Ranex.
- [ ] `HERMES-PROMOTION-039` **BLOCK** — Payment methods, subscriptions, balances, entitlements, and billing authorization data are never copied into Ranex.
- [ ] `HERMES-PROMOTION-041` **BLOCK** — Remove Hermes/Nous branding from all Ranex product surfaces and, as separately checkable items, from package metadata; remote endpoints; headers; telemetry tags; help text; screenshots; generated assets; and defaults. Historical research citations and legally required attribution are exceptions.
- [ ] `HERMES-PROMOTION-042` **BLOCK** — A clean-host Ranex run makes no DNS or HTTP request to a Nous, Portal, or Nous inference host.
- [ ] `HERMES-PROMOTION-043` **BLOCK** — nous, nous-portal, and nousresearch do not resolve as a runtime provider or model-catalog owner.
- [ ] `HERMES-PROMOTION-044` **BLOCK** — `/topup` and `/subscription` commands, billing and subscription RPCs, checkout, card, and auto-reload schemas, and Portal proxy routes are unregistered.
- [ ] `HERMES-PROMOTION-045` **BLOCK** — Runtime packages exclude `x-nous-credits-*`, `billing:manage`, `providers.nous`, Portal OAuth scopes, managed tool-pool entitlement, and `product=hermes-agent` request tags.
- [ ] `HERMES-PROMOTION-047` **BLOCK** — Sessions, canonical databases, exports, and backups contain no payment method, subscription, commercial balance, Portal entitlement, or Nous auth token.
- [ ] `HERMES-PROMOTION-048` **BLOCK** — The wheel, container, and SBOM exclude dedicated billing UI, purchase clients, Nous provider plugins, generated billing bundles, and monetization-only dependencies.
- [ ] `HERMES-PROMOTION-049` **BLOCK** — Static and runtime route-census tests find no hidden import, command, hook, RPC, environment variable, URL, or feature flag that can reactivate the commercial subsystem.
- [ ] `HERMES-PROMOTION-050` **BLOCK** — A configured tool without direct credentials becomes unavailable and never attempts a Nous managed gateway or checks a commercial subscription.
- [ ] `HERMES-PROMOTION-051` **BLOCK** — An auxiliary or model fallback never selects Nous when the configured provider is missing or fails; missing configuration fails closed.
- [ ] `HERMES-PROMOTION-053` **BLOCK** — Fuzzed `x-nous-*` headers cannot create state, notices, prompt content, tier selection, or tool gating.
- [ ] `HERMES-PROMOTION-054` **BLOCK** — Built wheel, npm bundle, and container scans find no dedicated commercial file, generated billing bundle, provider plugin, or `@nous-research/ui` package.
- [ ] `HERMES-PROMOTION-055` **BLOCK** — Provider-neutral token, cost, and budget telemetry continues to work after commercial deletion.
- [ ] `HERMES-PROMOTION-057` **BLOCK** — No product-facing package name, CLI command, config root, header, telemetry tag, help screen, screenshot, generated asset, or default presents Hermes/Nous branding outside an explicit migration warning or legally required attribution.

---

## 2. Everything else — decide per row (80 rows)

Each is something Hermes does. Keep, replace, or drop — but decide.

- [ ] `HERMES-PROMOTION-001` **BLOCK** — Ranex defines its core domain as governed deterministic execution rather than the agent loop.
- [ ] `HERMES-PROMOTION-002` **BLOCK** — A new dependency-clean kernel is built beside Hermes.
- [ ] `HERMES-PROMOTION-003` **BLOCK** — Workflow semantics and the execution reducer are first-class kernel responsibilities.
- [ ] `HERMES-PROMOTION-004` **BLOCK** — Hermes is contained as a replaceable worker and evolves into a typed action-proposal driver.
- [ ] `HERMES-PROMOTION-005` **BLOCK** — One fail-closed capability bus mediates every effect.
- [ ] `HERMES-PROMOTION-006` **BLOCK** — Policy enforcement, evidence and gate semantics, permit authority, module governance, and atomic event/outbox state remain kernel-owned.
- [ ] `HERMES-PROMOTION-007` **BLOCK** — Required capabilities ship as qualified first-party modules in one product release.
- [ ] `HERMES-PROMOTION-008` **BLOCK** — Legacy Hermes plugins execute only behind a constrained compatibility boundary.
- [ ] `HERMES-PROMOTION-009` **BLOCK** — Ranex starts with a small SQLite-backed tracer and retains a workflow-runtime port.
- [ ] `HERMES-PROMOTION-010` **BLOCK** — Import and runtime fitness tests enforce the architecture.
- [ ] `HERMES-PROMOTION-012` **BLOCK** — `ranex.*.domain` cannot import Hermes, CLI, gateway, database, provider, filesystem, HTTP, or tool packages.
- [ ] `HERMES-PROMOTION-013` **BLOCK** — A bounded context imports another context only through its public API.
- [ ] `HERMES-PROMOTION-014` **BLOCK** — First-party modules may depend on application/kernel public APIs, but the kernel cannot depend on modules.
- [ ] `HERMES-PROMOTION-015` **BLOCK** — Domain and application code do not import adapters; the composition root alone constructs them.
- [ ] `HERMES-PROMOTION-016` **BLOCK** — The module dependency graph is acyclic and equals a checked-in manifest.
- [ ] `HERMES-PROMOTION-017` **BLOCK** — Importing any module is side-effect free.
- [ ] `HERMES-PROMOTION-018` **BLOCK** — No direct canonical-state writes occur outside the unit of work.
- [ ] `HERMES-PROMOTION-019` **BLOCK** — No external effect occurs without a capability grant and recorded activity identity.
- [ ] `HERMES-PROMOTION-020` **BLOCK** — The module catalog cannot override a permit issuer or policy enforcement point.
- [ ] `HERMES-PROMOTION-021` **BLOCK** — A disabled, incompatible, unqualified, or quarantined module cannot register, migrate, receive traffic, or perform an effect.
- [ ] `HERMES-PROMOTION-022` **BLOCK** — Only the execution kernel chooses a legal next canonical state.
- [ ] `HERMES-PROMOTION-023` **BLOCK** — Only nonreplaceable application control authorizes and dispatches capabilities and effects using domain authorization decisions.
- [ ] `HERMES-PROMOTION-024` **BLOCK** — Every target-mode effect is completely mediated and no special agent-tool bypass exists.
- [ ] `HERMES-PROMOTION-025` **BLOCK** — Policy or checker unavailability and error deny a blocking action.
- [ ] `HERMES-PROMOTION-026` **BLOCK** — A maker cannot approve its own subject.
- [ ] `HERMES-PROMOTION-027` **BLOCK** — Evidence and approval bind the exact project, run, packet, commits, workflow version, and policy activation.
- [ ] `HERMES-PROMOTION-028` **BLOCK** — An approval or permit is single-use, scoped, expiring, and invalidated by material change.
- [ ] `HERMES-PROMOTION-029` **BLOCK** — Canonical state and version, audit or domain record, permit consumption, and outbox intent commit atomically.
- [ ] `HERMES-PROMOTION-030` **BLOCK** — Every retry uses the same logical idempotency identity.
- [ ] `HERMES-PROMOTION-031` **BLOCK** — The reducer has no hidden nondeterministic dependency.
- [ ] `HERMES-PROMOTION-032` **BLOCK** — Replay of the same definition, version, and history yields the same state and commands.
- [ ] `HERMES-PROMOTION-033` **BLOCK** — Historical decisions remain explainable and new effects use fresh authority.
- [ ] `HERMES-PROMOTION-034` **BLOCK** — Module code cannot write canonical state or grant itself capability.
- [ ] `HERMES-PROMOTION-035` **BLOCK** — External plugin failure cannot weaken a gate.
- [ ] `HERMES-PROMOTION-036` **BLOCK** — A human waiver remains visible as a waiver and never becomes machine PASS.
- [ ] `HERMES-PROMOTION-040` **BLOCK** — Preserve license, copyright, provenance, and required upstream attribution. Rebranding does not authorize erasing legal notices or Git history.
- [ ] `HERMES-PROMOTION-046` **BLOCK** — A remote model catalog cannot introduce or activate a model outside the release-pinned Ranex catalog and qualification record.
- [ ] `HERMES-PROMOTION-052` **BLOCK** — Legacy auth and config loading remains quarantined and cannot load a token, refresh credentials, log in, mint a key, or send network traffic.
- [ ] `HERMES-PROMOTION-056` **BLOCK** — License and attribution verification passes.
- [ ] `HERMES-PROMOTION-058` **BLOCK** — The clean kernel contains a shared-identity facility that provides shared identity and a canonical-serialization facility that provides canonical serialization.
- [ ] `HERMES-PROMOTION-059` **BLOCK** — The clean kernel contains an Execution aggregate, and Execution state transitions are computed by its pure reducer.
- [ ] `HERMES-PROMOTION-060` **BLOCK** — The clean kernel persists canonical execution state and its associated version in relational storage.
- [ ] `HERMES-PROMOTION-061` **BLOCK** — The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work.
- [ ] `HERMES-PROMOTION-062` **BLOCK** — The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope.
- [ ] `HERMES-PROMOTION-063` **BLOCK** — The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter.
- [ ] `HERMES-PROMOTION-064` **BLOCK** — Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted.
- [ ] `HERMES-PROMOTION-065` **BLOCK** — The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import.
- [ ] `HERMES-OWNER-DECISION-001` — 
- [ ] `HERMES-OWNER-DECISION-002` — 
- [ ] `HERMES-OWNER-DECISION-003` — 
- [ ] `HERMES-OWNER-DECISION-004` — 
- [ ] `HERMES-OWNER-DECISION-005` — 
- [ ] `HERMES-OWNER-DECISION-006` — 
- [ ] `HERMES-OWNER-DECISION-007` — 
- [ ] `HERMES-OWNER-DECISION-008` — 
- [ ] `HERMES-OWNER-DECISION-009` — 
- [ ] `HERMES-OWNER-DECISION-010` — 
- [ ] `HERMES-OWNER-DECISION-011` — 
- [ ] `HERMES-OWNER-DECISION-012` — 
- [ ] `HERMES-OWNER-DECISION-013` — 
- [ ] `HERMES-OWNER-DECISION-014` — 
- [ ] `HERMES-OWNER-DECISION-015` — 
- [ ] `HERMES-OWNER-DECISION-016` — 
- [ ] `HERMES-OWNER-DECISION-017` — 
- [ ] `HERMES-OWNER-DECISION-018` — 
- [ ] `HERMES-OWNER-DECISION-019` — 
- [ ] `HERMES-OWNER-DECISION-020` — 
- [ ] `HERMES-RESEARCH-ONLY-001` — 
- [ ] `HERMES-RESEARCH-ONLY-002` — 
- [ ] `HERMES-RESEARCH-ONLY-003` — 
- [ ] `HERMES-RESEARCH-ONLY-004` — 
- [ ] `HERMES-RESEARCH-ONLY-005` — 
- [ ] `HERMES-RESEARCH-ONLY-006` — 
- [ ] `HERMES-RESEARCH-ONLY-007` — 
- [ ] `HERMES-RESEARCH-ONLY-008` — 
- [ ] `HERMES-RESEARCH-ONLY-009` — 
- [ ] `HERMES-RESEARCH-ONLY-010` — 
- [ ] `HERMES-RESEARCH-ONLY-011` — 
- [ ] `HERMES-RESEARCH-ONLY-012` — 
- [ ] `HERMES-RESEARCH-ONLY-013` — 

---

**Totals:** 98 rows · 65 originally BLOCK · 18 de-commercialization · 80 other
