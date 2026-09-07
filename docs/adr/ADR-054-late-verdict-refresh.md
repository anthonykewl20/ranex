# ADR-054 — Late-verdict refresh from the listener's periodic pass

**Status:** accepted
**Date:** 2026-09-07
**Issue:** #88

## Context and Problem Statement

A pull-request event usually arrives before the gate has run for its head.
The receiver publishes `action_required` and, until now, nothing further
happened unless GitHub redelivered the event or an operator ran
`ranex github check publish`. Issue #88 named this as an unimplemented
production behaviour: the verdict lands, the check stays red.

## Considered Options

1. Watch the verdict directory with inotify — rejected: a second
   long-running mechanism, host-limited (this workstation exhausts inotify
   instances), and the receiver already has a periodic pass (ADR-053).
2. Have `gate evaluate` call the App — rejected: the kernel's evaluation
   path must not depend on network or credentials (invariant: removing
   every model credential must not change a verdict; the App is a
   publisher, never part of the verdict).
3. Remember unresolved heads and re-read the verdict store on the periodic
   pass — chosen.

## Decision Outcome

When a delivery publishes `action_required` because the verdict is absent,
`_process_delivery` writes `<state>/awaiting/<head>.json` (delivery id,
installation, repository). `refresh_awaiting` runs after `drain_spool` on
each periodic pass, under the same pipeline lock a delivery holds, and per
head: asks GitHub for a run stamped `refresh:<head>` (an interrupted
earlier pass — journal `reconciled-refresh:<conclusion>`, forget the head);
otherwise binds the head from the local clone, resolves acceptance, and if
the verdict is still absent leaves the record; if present — verified or
rejected — revalidates the head, publishes with that stamp, journals
`refreshed:<conclusion>` and forgets the head. A fresh event that publishes
a verdict forgets the head too. Damaged or misnamed records are journaled
`awaiting-unreadable` and left. Nothing here evaluates: the pass reads the
same signed publications the delivery path reads.

## Consequences

- A head can carry two `ranex/acceptance` runs: the early `action_required`
  and the refresh. GitHub shows the latest; the ruleset gates on it.
- New state directory `awaiting/`, preserved on upgrade.
- Refresh latency is `SPOOL_RETRY_SECONDS` (300) at worst.
