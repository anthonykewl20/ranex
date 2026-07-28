# ADR-0004: Establish Initial Quality-Attribute Baselines

| Field | Value |
|---|---|
| ADR ID | `ADR-0004` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a758f70d39af6a21e73488c61db5f82f32` |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | Authority, storage, security, operations, backup/restore, artifacts, delivery, release, and service management |
| RFC | Not required; establishes the initial construction baseline |
| Supersedes | None |
| Review/expiry date | First two target-mode tracers and first restore drill, then quarterly |
| Compatibility/migration class | New target baseline; profiles may strengthen it |
| Security/data class | Public architecture decision; operational evidence follows its source classification |

## Decision

Ranex adopts the following initial quality-attribute objectives. They are
binding design and acceptance targets for the first qualified local release;
they are **not** measurements of the current repository or promises that a
runtime already meets them.

### Safety and integrity invariants

The permitted count for each of these events is zero:

- unauthorized work/run transition, authority grant, permit, or effect;
- successful use of a stale, expired, revoked, reused, or wrong-subject permit;
- a review observation, model output, missing result, or stale artifact being
  converted directly into a passing gate;
- an unjournaled canonical authority write or an effect without durable intent;
- silent acceptance of corrupt, incomplete, conflicting, or unavailable
  blocking evidence; and
- a compatibility, extension, route, or worker path writing authority state.

These are invariants rather than percentile SLOs. A known violation blocks
release or triggers incident containment and reconciliation.

### Initial service objectives

| Attribute | Initial target | Measurement boundary |
|---|---|---|
| Local control-plane availability | `>= 99.0%` per calendar month during owner-declared service windows | Excludes planned maintenance and periods when the owner intentionally powers off the local host; includes process faults and dependency faults inside the supported profile |
| Local read/query latency | `p95 <= 500 ms`, `p99 <= 1 s` | Warm local process, supported dataset, excludes explicitly identified external-provider work |
| Authority command commit latency | `p95 <= 2 s`, `p99 <= 5 s` | Receipt through durable SQLite commit/outbox record; excludes downstream effect completion |
| Crash restart and authority recovery | `RPO = 0` committed authority transactions; `RTO <= 15 min` | Supported single-host process/OS crash with intact durable storage |
| Host loss or unrecoverable store corruption | `RPO <= 24 h`; `RTO <= 4 h` | Restore from the qualified encrypted backup set on a supported replacement host |
| Reconciliation | `100%` of `OUTCOME_UNKNOWN` effects receive a durable reconciliation record; critical effects begin reconciliation within `15 min` of detection | Measured from durable detection, not from a model or UI observation |

`service_management` owns the SLI definitions and service-window policy.
`operations` owns measurement and incident evidence. `backup_restore` owns
recovery evidence. A release profile may set stricter values. A weaker value
requires an accepted risk decision and ADR and may never weaken the safety
invariants.

### Backup and restore baseline

- Authority SQLite data, journal/outbox state, schema/migration state,
  configuration baselines, release manifest, artifact catalog, and required
  interaction-retention metadata are in the protected backup set.
- The default cadence is one encrypted backup at least every 24 hours, with
  30 daily recovery points and 12 month-end recovery points.
- Encryption keys/credentials are stored separately from backup payloads.
- Every backup is content-manifested and integrity-checked. A backup is not
  called restorable until a clean-environment restore and reconciliation pass.
- Restore drills run before the first limited release, after a storage or
  migration-format change, and at least quarterly thereafter.
- Before live authority use, the authority journal head is anchored at least
  daily in a separately protected location so a local administrator/store
  compromise cannot silently rewrite both evidence and anchor.

### Security and privacy baseline

- Local authority files use owner-only operating-system access. Sensitive
  stores require supported volume or application-layer encryption at rest;
  backups are always encrypted.
- The web surface binds to loopback by default and requires authenticated,
  expiring sessions. Private-network publication is a separately qualified
  delivery profile; public binding is excluded.
- Worker processes start network-denied, home-directory-denied, authority-DB-
  denied, and secret-value-denied. Each allowed resource is explicit,
  subject-bound, time-bounded, and auditable.
- Secrets are referenced by opaque handles. They do not enter packets, prompts,
  logs, command lines, review artifacts, or model-visible exception text.
- External connections require allowlisted destinations, verified transport
  security, pinned route/provider identity, bounded time/output, and recorded
  egress classification.
- Logs and telemetry use structured allowlists and redaction; unclassified
  arbitrary payload logging is prohibited.
- High-risk changes require separation between maker, independent reviewer,
  qualified deterministic checker, and human authority.

### Retention and disposal baseline

| Data class | Default retention | Disposal/exception rule |
|---|---|---|
| Authority, policy decision, gate, permit, release, provenance, and security-audit records | Supported product lifetime plus 1 year | A legal/contractual hold or accepted compliance profile may extend; minimization forbids copying unrelated personal content into these records |
| Routine operational telemetry and redacted logs | 30 days | Security incident evidence is promoted to the governed incident/evidence class |
| Raw prompts, model responses, transient source bundles, and failed-attempt payloads | 30 days after run closure | Shorter for sensitive data; longer only through classified evidence/legal-hold policy |
| Isolated worker workspaces and temporary exports | 7 days after terminal handoff | Preserve only content-addressed artifacts named by an accepted evidence or release manifest |
| User interaction content | 30 days after owner deletion/expiry request | Product/legal profile may define a different disclosed period; tombstone and deletion evidence outlive content only as required |
| Backup recovery points | 30 daily and 12 month-end points | Legal hold may suspend expiry for named manifests only |

`artifact_management` enforces artifact retention/legal hold/purge;
`interaction_history` enforces conversation export/deletion;
`provenance_compliance` defines legal overlays; `backup_restore` expires backup
sets; the source context remains the data owner.

## Alternatives considered

1. **Leave all objectives to implementation teams.** Rejected because storage,
   security, recovery, and capacity decisions would be made without a common
   acceptance boundary.
2. **Claim enterprise-grade values now.** Rejected because no target runtime
   measurements or restore drill exist.
3. **Promise uninterrupted cloud-style availability.** Rejected because Ranex
   is local-first and owner-operated.
4. **Retain everything indefinitely.** Rejected because it increases privacy,
   breach, discovery, and operational risk.
5. **Keep all evidence only in the authority database.** Rejected because a
   compromised local store could rewrite both record and proof.

## Fitness functions and required evidence

| ID | Required result |
|---|---|
| `FF-SAFE-001` | Property and integration tests show zero legal path for each forbidden authority/evidence event. |
| `FF-PERF-001` | A versioned workload and dataset emit percentile distributions; summaries alone do not pass. |
| `FF-CRASH-001` | Fault injection before and after every authority commit/outbox/effect boundary preserves RPO and reconciliation invariants. |
| `FF-RESTORE-001` | A clean-host restore meets the stated RPO/RTO and reconciles external effects/artifact digests. |
| `FF-SEC-001` | Real subprocess and adapter tests prove file, process, network, secret, argument, output, and authority-DB denials. |
| `FF-RET-001` | Time-controlled tests prove expiry, purge, legal hold, backup expiry, and deletion tombstones without orphaned projections. |
| `FF-ANCHOR-001` | Tamper tests detect local journal/store rewriting against the separately protected anchor. |

Results bind the exact build, configuration, host profile, dataset, and
measurement method. Until those evidence records exist, each objective is
reported `NOT_MEASURED`, never `PASS`.

## Engineering-reference application

The quality-attribute questions and measurable fitness functions apply the
advisory guidance catalogued in the
[Engineering Reference Application Map](../ENGINEERING_REFERENCE_APPLICATION_MAP.md),
especially §3, §5.1, §5.3, §5.4, §8, and §10. The local works are advisory,
edition-specific, sometimes excerpted or opinionated, and do not prove these
numbers. The values above are Ranex owner decisions to be calibrated with
runtime evidence, not quotations or claims of standards certification.

## Consequences and change rule

The targets make capacity, recovery, retention, and security trade-offs visible
before code chooses them. They also create implementation and operating work.
Calibration may tighten a target through a release profile. Weakening a target
requires a recorded service/risk analysis, owner approval, an accepted
superseding ADR, migration/rollback impact, and updated tests.

## Human approval

The human owner requested an enterprise-build-ready architecture grounded in
mature engineering practice. This ADR records the initial paper baseline for
that construction. It is not runtime evidence, certification, a production
authorization, or a claim that the current branch meets the targets.

