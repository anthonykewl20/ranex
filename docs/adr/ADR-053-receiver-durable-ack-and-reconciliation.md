# ADR-053 — Durable acknowledgement and at-least-once reconciliation for the receiver

**Status:** accepted
**Date:** 2026-09-07
**Issue:** #88

## Context and Problem Statement

Issue #88's local fault probes reproduced three receiver gaps against the
real listener and a fake GitHub API: an 11-second check publication made the
HTTP answer arrive after GitHub's 10-second delivery deadline; a completion
receipt that failed to persist after a successful publication produced a
second identical check on redelivery; and a mode-0644 App private key minted
a verifiable JWT. ADR-051 chose a stdlib listener that processes one delivery
at a time and answers synchronously; its docstring conceded the duplicate.

## Considered Options

1. Answer 202 for every delivery and process from a queue — rejected: the
   fast path's real status (200/400/409/5xx) is what every existing stress
   and audit tool, and GitHub's redelivery UI, act on; hiding it behind 202
   costs the operator the signal for the common case.
2. A shorter API timeout so a slow publication answers 5xx in time —
   rejected: it turns a slow success into an operator redelivery and still
   duplicates on the retry.
3. Spool first, answer within a deadline, reconcile on retry — chosen.

## Decision Outcome

`spool_delivery` writes the proven delivery (body, event) atomically under
`<state>/spool/` before the pipeline touches it. The handler runs
`process_delivery` on a worker and joins it for `ACK_DEADLINE_SECONDS` (8):
a finished pipeline answers its real status and the spool entry is
released; an unfinished one answers 202 and the worker releases the entry
only if it completes (status < 500). `drain_spool` re-runs every remaining
entry through the same `process_delivery` at listener start and every
`SPOOL_RETRY_SECONDS` (300); damaged entries are journaled
(`spool-unreadable`) and left. The pipeline, its lock and its 503 are
unchanged.

Before the API call the pipeline writes `<state>/attempted/<id>.json`
naming the head, and the check-run body carries `external_id = <delivery
id>`. A retry that finds an attempt record for its own head asks GitHub for
this App's `ranex/acceptance` runs on that head and, if one bears the
delivery id, journals `reconciled:<conclusion>` and completes without
publishing. A record for another head is ignored. This is at-least-once
with reconciliation, not exactly-once: if the reconciliation call itself
fails the delivery answers 5xx and is retried; two checks stay possible
only when GitHub cannot be asked.

`load_private_key` refuses a key that is not a regular file, or whose mode
grants group or others any bit (`E-GITHUB-KEY-EXPOSED`), before parsing.

## Consequences

- HTTP 202 is a new answer on `/webhook`; tools that assert on the fast
  path's status are unaffected because the fast path still answers it.
- New state directories `spool/` and `attempted/` join `completed/`; all
  are preserved on upgrade.
- Fixture keys must be 0600; `tests/_github_fake.write_app_key` sets it.
- No automatic refresh when a verdict lands after the event was answered;
  that remains UNIMPLEMENTED and documented as an operator redelivery.
